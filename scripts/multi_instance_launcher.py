#!/usr/bin/env python3
"""
Multi-instance Factorio launcher for testing parallel execution
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional


class FactorioInstance:
    def __init__(self, instance_id: str, base_port: int = 34197):
        self.instance_id = instance_id
        self.game_port = base_port + (int(instance_id) * 10)
        self.rcon_port = self.game_port + 1
        self.process: Optional[subprocess.Popen] = None
        
        # Separate directories for each instance
        self.instance_dir = Path(f"instances/instance_{instance_id}")
        self.config_dir = self.instance_dir / "config"
        self.saves_dir = self.instance_dir / "saves"
        self.mods_dir = self.instance_dir / "mods"
        self.logs_dir = self.instance_dir / "logs"
        self.user_data_dir = self.instance_dir / "user-data"
        
        self.save_file = self.saves_dir / f"test_{instance_id}.zip"
        
    def setup_directories(self):
        """Create separate directory structure for this instance"""
        print(f"Setting up directories for instance {self.instance_id}")
        
        # Create all directories
        for dir_path in [self.config_dir, self.saves_dir, self.mods_dir, 
                        self.logs_dir, self.user_data_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Copy base config files if they exist
        base_config = Path("config")
        if base_config.exists():
            for config_file in base_config.glob("*.json"):
                shutil.copy2(config_file, self.config_dir / config_file.name)
                
        # Copy base mods if they exist
        base_mods = Path("mods")
        if base_mods.exists():
            for mod_file in base_mods.iterdir():
                if mod_file.is_file():
                    shutil.copy2(mod_file, self.mods_dir / mod_file.name)
                    
        # Create instance-specific config.ini
        self.create_config_ini()
        
    def create_config_ini(self):
        """Create instance-specific config.ini to isolate user data"""
        config_ini = self.config_dir / "config.ini"
        config_content = f"""[path]
read-data=__PATH__executable__
write-data={self.user_data_dir.absolute()}
use-system-read-write-data-directories=false

[other]
# Instance {self.instance_id} configuration
"""
        config_ini.write_text(config_content)
        
    def create_save_file(self, factorio_path: str) -> bool:
        """Create save file for this instance"""
        if self.save_file.exists():
            print(f"Save file for instance {self.instance_id} already exists")
            return True
            
        print(f"Creating save file for instance {self.instance_id}")
        cmd = [
            factorio_path,
            "--create", str(self.save_file),
            "--config", str(self.config_dir / "config.ini")
        ]
        
        # Add map gen settings if available
        map_gen_file = self.config_dir / "map-gen-settings.json"
        if map_gen_file.exists():
            cmd.extend(["--map-gen-settings", str(map_gen_file)])
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to create save for instance {self.instance_id}: {result.stderr}")
            return False
            
        print(f"Save created for instance {self.instance_id}")
        return True
        
    def start_server(self, factorio_path: str) -> bool:
        """Start this Factorio instance"""
        if not self.save_file.exists():
            if not self.create_save_file(factorio_path):
                return False
                
        print(f"Starting Factorio instance {self.instance_id} on ports {self.game_port}/{self.rcon_port}")
        
        cmd = [
            factorio_path,
            "--start-server", str(self.save_file),
            "--port", str(self.game_port),
            "--rcon-port", str(self.rcon_port),
            "--rcon-password", "admin",
            "--config", str(self.config_dir / "config.ini"),
            "--mod-directory", str(self.mods_dir),
        ]
        
        # Add server settings if available
        server_settings = self.config_dir / "server-settings.json"
        if server_settings.exists():
            cmd.extend(["--server-settings", str(server_settings)])
            
        # Start with separate log file
        log_file = open(self.logs_dir / "server.log", "w")
        self.process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
        
        # Wait for startup
        time.sleep(3)
        
        if self.process.poll() is None:
            print(f"Instance {self.instance_id} started successfully!")
            print(f"  Game port: {self.game_port}")
            print(f"  RCON port: {self.rcon_port}")
            return True
        else:
            print(f"Instance {self.instance_id} failed to start")
            return False
            
    def stop_server(self):
        """Stop this instance"""
        if self.process and self.process.poll() is None:
            print(f"Stopping instance {self.instance_id}")
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait()
            except ProcessLookupError:
                pass
            finally:
                self.process = None
                
    def test_connection(self) -> bool:
        """Test RCON connection to this instance"""
        print(f"Testing RCON connection to instance {self.instance_id}")
        cmd = [
            "python3", "scripts/test_rcon.py",
            "--host", "localhost",
            "--port", str(self.rcon_port),
            "--password", "admin",
            "--command", "/help"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        success = result.returncode == 0
        
        if success:
            print(f"  Instance {self.instance_id}: RCON OK")
        else:
            print(f"  Instance {self.instance_id}: RCON FAILED - {result.stderr}")
            
        return success


class MultiInstanceManager:
    def __init__(self, factorio_path: Optional[str] = None):
        self.factorio_path = factorio_path or self._find_factorio_binary()
        self.instances: Dict[str, FactorioInstance] = {}
        
    def _find_factorio_binary(self) -> str:
        """Find Factorio binary - reuse logic from dev_server.py"""
        # Check PATH first
        try:
            result = subprocess.run(["factorio", "--version"], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                return "factorio"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
            
        # Platform-specific locations
        import platform
        system = platform.system()
        home = Path.home()
        
        candidates = []
        if system == "Darwin":
            candidates.extend([
                home / "Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/MacOS/factorio",
                Path("/Applications/factorio.app/Contents/MacOS/factorio"),
            ])
        elif system == "Linux":
            candidates.extend([
                home / ".steam/steam/steamapps/common/Factorio/bin/x64/factorio",
                home / ".local/share/Steam/steamapps/common/Factorio/bin/x64/factorio",
            ])
            
        for candidate in candidates:
            if candidate.exists():
                try:
                    result = subprocess.run([str(candidate), "--version"], 
                                          capture_output=True, timeout=5)
                    if result.returncode == 0:
                        return str(candidate)
                except subprocess.TimeoutExpired:
                    continue
                    
        return "factorio"
        
    def create_instance(self, instance_id: str) -> FactorioInstance:
        """Create and setup a new instance"""
        instance = FactorioInstance(instance_id)
        instance.setup_directories()
        self.instances[instance_id] = instance
        return instance
        
    def start_all_instances(self, instance_ids: List[str]) -> Dict[str, bool]:
        """Start multiple instances and return success status"""
        results = {}
        
        for instance_id in instance_ids:
            if instance_id not in self.instances:
                self.create_instance(instance_id)
                
            instance = self.instances[instance_id]
            results[instance_id] = instance.start_server(self.factorio_path)
            
            # Small delay between starts
            time.sleep(2)
            
        return results
        
    def test_all_connections(self) -> Dict[str, bool]:
        """Test RCON connections to all running instances"""
        results = {}
        for instance_id, instance in self.instances.items():
            if instance.process and instance.process.poll() is None:
                results[instance_id] = instance.test_connection()
            else:
                results[instance_id] = False
        return results
        
    def stop_all_instances(self):
        """Stop all running instances"""
        for instance in self.instances.values():
            instance.stop_server()
            
    def get_status_report(self) -> str:
        """Generate status report of all instances"""
        report = ["=== Multi-Instance Status Report ==="]
        
        for instance_id, instance in self.instances.items():
            status = "RUNNING" if instance.process and instance.process.poll() is None else "STOPPED"
            report.append(f"Instance {instance_id}: {status}")
            if status == "RUNNING":
                report.append(f"  Game port: {instance.game_port}")
                report.append(f"  RCON port: {instance.rcon_port}")
                report.append(f"  Directory: {instance.instance_dir}")
                
        return "\n".join(report)


def main():
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description="Multi-instance Factorio launcher")
    parser.add_argument("--factorio-path", help="Path to Factorio binary")
    parser.add_argument("--instances", nargs="+", default=["1", "2"], 
                       help="Instance IDs to create (default: 1 2)")
    parser.add_argument("--test-only", action="store_true", 
                       help="Only test connections, don't start new instances")
    
    args = parser.parse_args()
    
    manager = MultiInstanceManager(args.factorio_path)
    
    # Signal handling
    def signal_handler(sig, frame):
        print("\nShutting down all instances...")
        manager.stop_all_instances()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.test_only:
        # Test existing instances
        results = manager.test_all_connections()
        print("Connection test results:")
        for instance_id, success in results.items():
            print(f"  Instance {instance_id}: {'OK' if success else 'FAILED'}")
        return
        
    print("Starting multi-instance Factorio setup...")
    print(f"Instances to start: {args.instances}")
    
    # Start all instances
    results = manager.start_all_instances(args.instances)
    
    # Report startup results
    print("\nStartup results:")
    for instance_id, success in results.items():
        print(f"  Instance {instance_id}: {'SUCCESS' if success else 'FAILED'}")
        
    # Test connections
    print("\nTesting connections...")
    time.sleep(5)  # Give servers time to fully start
    connection_results = manager.test_all_connections()
    
    for instance_id, success in connection_results.items():
        print(f"  Instance {instance_id}: {'CONNECTED' if success else 'CONNECTION FAILED'}")
        
    # Status report
    print(f"\n{manager.get_status_report()}")
    
    # Keep running
    if any(results.values()):
        print("\nInstances running. Press Ctrl+C to stop all.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            manager.stop_all_instances()
    else:
        print("No instances started successfully.")


if __name__ == "__main__":
    main()
