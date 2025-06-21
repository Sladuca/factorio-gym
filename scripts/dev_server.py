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
    def __init__(self, factorio_path: str = "factorio") -> None:
        self.factorio_path: str = factorio_path
        self.process: Optional[subprocess.Popen[bytes]] = None
        self.save_path: Path = Path("saves/test.zip")

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
        if self.process:
            print("Stopping server...")
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process.wait()
            print("Server stopped")

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
        default=os.environ.get("FACTORIO_PATH", "factorio"),
        help="Path to Factorio binary",
    )
    parser.add_argument(
        "command", nargs="?", choices=["create", "test"], help="Command to run"
    )

    args = parser.parse_args()

    # Setup signal handling
    def signal_handler(sig: int, frame: Any) -> None:
        print("\nShutting down...")
        server.stop_server()
        sys.exit(0)

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
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            server.stop_server()


if __name__ == "__main__":
    main()
