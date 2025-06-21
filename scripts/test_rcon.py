#!/usr/bin/env python3
"""Simple RCON client for testing Factorio server commands."""

import argparse
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from factorio_mcp.rcon import FactorioRCON


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test Factorio RCON connection")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=34198, help="RCON port")
    parser.add_argument("--password", default="admin", help="RCON password")
    parser.add_argument("--command", help="Single command to execute")

    args = parser.parse_args()

    try:
        with FactorioRCON(args.host, args.port, args.password) as rcon:
            if args.command:
                response = rcon.send_command(args.command)
                print(f"Response: {response}")
            else:
                # Interactive mode
                print("Interactive RCON mode. Type 'quit' to exit.")
                while True:
                    try:
                        command = input("factorio> ").strip()
                        if command.lower() in ["quit", "exit"]:
                            break
                        if command:
                            response = rcon.send_command(command)
                            print(f"Response: {response}")
                    except KeyboardInterrupt:
                        print("\nExiting...")
                        break
                    except EOFError:
                        break

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
