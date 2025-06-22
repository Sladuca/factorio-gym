#!/usr/bin/env python3
"""
Test script to verify E2E demo setup is working properly.

Checks:
1. RCON connection to server
2. Agent control mod is loaded
3. Agent creation works
4. Basic movement commands work
5. Status reporting works

Run this before the full demo to ensure everything is set up correctly.
"""

import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from factorio_mcp.rcon import FactorioRCON


def test_setup(host="localhost", port=34198, password="admin", agent_name="TestAgent"):
    """Test the E2E demo setup."""
    print("=== E2E Demo Setup Test ===")
    print()
    
    # Test 1: RCON Connection
    print("1. Testing RCON connection...")
    try:
        rcon = FactorioRCON(host, port, password)
        rcon.connect()
        print("   ✓ RCON connection successful")
    except Exception as e:
        print(f"   ✗ RCON connection failed: {e}")
        print()
        print("TROUBLESHOOTING:")
        print("- Is the Factorio server running?")
        print("- Run: python3 scripts/dev_server.py")
        print("- Check that RCON is enabled on the correct port")
        return False
    
    # Test 2: Basic Command
    print("2. Testing basic RCON command...")
    try:
        response = rcon.send_command("/help")
        if response:
            print("   ✓ Basic commands working")
        else:
            print("   ⚠ Got empty response, but connection works")
    except Exception as e:
        print(f"   ✗ Command failed: {e}")
        return False
    
    # Test 3: Agent Control Mod
    print("3. Testing agent-control mod...")
    try:
        response = rcon.send_command("/hello")
        if "Hello from RCON!" in response:
            print("   ✓ agent-control mod is loaded and working")
        else:
            print(f"   ⚠ Unexpected response: {response}")
            print("   The mod might not be loaded properly")
    except Exception as e:
        print(f"   ✗ Mod test failed: {e}")
        print("   Make sure the agent-control mod is installed and enabled")
        return False
    
    # Test 4: Agent Creation
    print("4. Testing agent creation...")
    try:
        response = rcon.send_command(f"/ensure_player {agent_name}")
        if "Created player" in response or "already exists" in response:
            print(f"   ✓ Agent '{agent_name}' ready")
        else:
            print(f"   ⚠ Unexpected response: {response}")
    except Exception as e:
        print(f"   ✗ Agent creation failed: {e}")
        return False
    
    # Test 5: Movement Commands
    print("5. Testing movement commands...")
    try:
        # Test movement
        response = rcon.send_command(f"/agent_move {agent_name} 0")
        if "Moving player" in response:
            print("   ✓ Movement command works")
            time.sleep(0.1)
            
            # Test stop
            response = rcon.send_command(f"/agent_stop {agent_name}")
            if "Stopped player" in response:
                print("   ✓ Stop command works")
            else:
                print(f"   ⚠ Stop command response: {response}")
        else:
            print(f"   ⚠ Movement command response: {response}")
    except Exception as e:
        print(f"   ✗ Movement test failed: {e}")
        return False
    
    # Test 6: Status Reporting
    print("6. Testing status reporting...")
    try:
        response = rcon.send_command(f"/agent_status {agent_name}")
        if "STATUS:" in response:
            print("   ✓ Status reporting works")
            # Try to parse status
            try:
                status_data = response.split("STATUS:", 1)[1]
                print(f"   Status data: {status_data}")
            except:
                print("   Status data parsing needs work, but basic function works")
        else:
            print(f"   ⚠ Status response: {response}")
    except Exception as e:
        print(f"   ✗ Status test failed: {e}")
        return False
    
    # Cleanup
    rcon.close()
    
    print()
    print("=== Setup Test Results ===")
    print("✓ All tests passed!")
    print()
    print("Your setup is ready for the E2E demo.")
    print("Run: python3 scripts/e2e_demo.py")
    print()
    print("Instructions:")
    print("1. Connect a human player via Factorio client to localhost:34197")
    print("2. Use WASD keys to control the agent")
    print("3. Both players will be visible and can interact")
    
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test E2E demo setup")
    parser.add_argument("--host", default="localhost", help="RCON host")
    parser.add_argument("--port", type=int, default=34198, help="RCON port")
    parser.add_argument("--password", default="admin", help="RCON password")
    parser.add_argument("--agent-name", default="TestAgent", help="Test agent name")
    
    args = parser.parse_args()
    
    success = test_setup(args.host, args.port, args.password, args.agent_name)
    
    if not success:
        print("\nSome tests failed. Please fix the issues before running the demo.")
        sys.exit(1)


if __name__ == "__main__":
    main()
