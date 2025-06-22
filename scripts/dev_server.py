#!/usr/bin/env python3
"""
Development server launcher and test harness for Factorio agent control
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, List, Optional


class FactorioDevServer:
    def __init__(self, factorio_path: Optional[str] = None) -> None:
        self.factorio_path: str = factorio_path or self._find_factorio_binary()
        self.process: Optional[subprocess.Popen[bytes]] = None
        self.save_path: Path = Path("saves/test.zip")

    def _find_factorio_binary(self) -> str:
        """Find Factorio binary in common installation locations"""
        import platform
        
        # Check PATH first
        try:
            result = subprocess.run(["factorio", "--version"], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                return "factorio"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Platform-specific common locations
        system = platform.system()
        home = Path.home()
        
        candidates: List[Path] = []
        
        if system == "Darwin":  # macOS
            candidates.extend([
                home / "Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/MacOS/factorio",
                Path("/Applications/factorio.app/Contents/MacOS/factorio"),
                home / "Applications/factorio.app/Contents/MacOS/factorio",
            ])
        elif system == "Linux":
            candidates.extend([
                home / ".steam/steam/steamapps/common/Factorio/bin/x64/factorio",
                home / ".local/share/Steam/steamapps/common/Factorio/bin/x64/factorio",
                Path("/opt/factorio/bin/x64/factorio"),
                home / "factorio/bin/x64/factorio",
            ])
        elif system == "Windows":
            candidates.extend([
                Path("C:/Program Files (x86)/Steam/steamapps/common/Factorio/bin/x64/factorio.exe"),
                Path("C:/Program Files/Steam/steamapps/common/Factorio/bin/x64/factorio.exe"),
                home / "AppData/Local/Steam/steamapps/common/Factorio/bin/x64/factorio.exe",
            ])
        
        # Test each candidate
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                try:
                    result = subprocess.run([str(candidate), "--version"], 
                                          capture_output=True, timeout=5)
                    if result.returncode == 0:
                        return str(candidate)
                except (subprocess.TimeoutExpired, PermissionError):
                    continue
        
        # Fallback to "factorio" if nothing found
        return "factorio"

    def _check_factorio_binary(self) -> bool:
        """Check if Factorio binary is available"""
        try:
            result = subprocess.run(
                [self.factorio_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def create_save(self) -> bool:
        """Create a new test save file"""
        if self.save_path.exists():
            print(f"Save file {self.save_path} already exists, skipping creation")
            return True

        print("Creating new save file...")
        cmd: List[str] = [
            self.factorio_path,
            "--create",
            str(self.save_path),
            "--map-gen-settings",
            "config/map-gen-settings.json",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to create save: {result.stderr}")
            return False

        print(f"Save created at {self.save_path}")
        return True

    def start_server(self) -> bool:
        """Start the headless Factorio server"""
        if not self._check_factorio_binary():
            print(
                f"Error: Factorio binary '{self.factorio_path}' not found or not "
                f"working"
            )
            print("Please install Factorio or provide the correct path:")
            print("  python3 scripts/dev_server.py --factorio-path /path/to/factorio")
            print("  OR set FACTORIO_PATH environment variable")
            return False

        if not self.save_path.exists():
            if not self.create_save():
                return False

        print("Starting Factorio server...")
        cmd: List[str] = [
            self.factorio_path,
            "--start-server",
            str(self.save_path),
            "--port",
            "34197",
            "--rcon-port",
            "34198",
            "--rcon-password",
            "admin",
            "--server-settings",
            "config/server-settings.json",
            "--mod-directory",
            "mods",
        ]

        # Redirect output to log file
        log_file = open("logs/server.log", "w")
        self.process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,  # Create new process group
        )

        # Wait a bit for server to start
        time.sleep(3)

        if self.process.poll() is None:
            print("Server started successfully!")
            print("RCON available on localhost:34198 (password: admin)")
            print("Game server on localhost:34197")
            return True
        else:
            print("Server failed to start, check logs/server.log")
            return False

    def stop_server(self) -> None:
        """Stop the server"""
        if self.process and self.process.poll() is None:
            print("Stopping server...")
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait()
                print("Server stopped")
            except ProcessLookupError:
                print("Server already stopped")
            finally:
                self.process = None

    def test_connection(self) -> None:
        """Test RCON connection"""
        print("\nTesting RCON connection...")
        result = subprocess.run(
            ["python3", "scripts/test_rcon.py", "--command", "/help"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("RCON connection successful!")
            print("Response:", result.stdout)
        else:
            print("RCON connection failed:", result.stderr)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Factorio development server")
    parser.add_argument(
        "--factorio-path",
        default=os.environ.get("FACTORIO_PATH"),
        help="Path to Factorio binary (auto-detected if not specified)",
    )
    parser.add_argument(
        "command", nargs="?", choices=["create", "test"], help="Command to run"
    )

    args = parser.parse_args()

    # Setup signal handling
    shutdown_requested = False
    
    def signal_handler(sig: int, frame: Any) -> None:
        nonlocal shutdown_requested
        print("\nShutting down...")
        shutdown_requested = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create logs directory
    os.makedirs("logs", exist_ok=True)

    server = FactorioDevServer(args.factorio_path)

    if args.command == "create":
        server.create_save()
        return
    elif args.command == "test":
        server.test_connection()
        return

    # Start server and keep running
    if server.start_server():
        server.test_connection()

        print("\nDevelopment server running...")
        print("Press Ctrl+C to stop")
        print("\nUseful commands:")
        print("  python3 scripts/test_rcon.py --command '/help'")
        print("  python3 scripts/test_rcon.py  # Interactive mode")

        try:
            while not shutdown_requested:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            server.stop_server()


if __name__ == "__main__":
    main()
