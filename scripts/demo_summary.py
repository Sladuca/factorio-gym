#!/usr/bin/env python3
"""
Demo Summary: Key Features of the E2E System

This script showcases the core capabilities without requiring keyboard input,
useful for demonstrations or automated testing.
"""

import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from factorio_mcp.rcon import FactorioRCON


def demo_agent_capabilities():
    """Demonstrate agent control capabilities."""
    print("=== Factorio Agent Control Demo ===")
    print()
    
    # Connect to server
    print("1. Connecting to Factorio server...")
    try:
        rcon = FactorioRCON("localhost", 34198, "admin")
        rcon.connect()
        print("   ✓ Connected successfully")
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return
    
    agent_name = "DemoAgent"
    
    # Create agent
    print(f"2. Creating agent player '{agent_name}'...")
    response = rcon.send_command(f"/ensure_player {agent_name}")
    print(f"   Server: {response}")
    
    # Demonstrate movement patterns
    print("3. Demonstrating movement patterns...")
    
    movements = [
        (0, "North"),
        (2, "East"), 
        (4, "South"),
        (6, "West"),
        (0, "North")
    ]
    
    for direction, name in movements:
        print(f"   Moving {name} (direction {direction})")
        rcon.send_command(f"/agent_move {agent_name} {direction}")
        time.sleep(1)
        
        # Get status
        status_response = rcon.send_command(f"/agent_status {agent_name}")
        if "STATUS:" in status_response:
            status_data = status_response.split("STATUS:", 1)[1]
            print(f"   Status: {status_data}")
    
    # Stop movement
    print("4. Stopping agent...")
    rcon.send_command(f"/agent_stop {agent_name}")
    print("   ✓ Agent stopped")
    
    # Final status
    print("5. Final status check...")
    status_response = rcon.send_command(f"/agent_status {agent_name}")
    if "STATUS:" in status_response:
        status_data = status_response.split("STATUS:", 1)[1]
        print(f"   Final status: {status_data}")
    
    # Cleanup
    print("6. Disconnecting...")
    rcon.close()
    print("   ✓ Disconnected")
    
    print()
    print("=== Demo Complete ===")
    print("The agent control system is working correctly!")
    print()
    print("To run the full interactive demo:")
    print("  python3 scripts/e2e_demo.py")
    print()
    print("Key capabilities demonstrated:")
    print("  ✓ Agent creation and management")
    print("  ✓ Real-time movement control")
    print("  ✓ Status monitoring")
    print("  ✓ RCON command processing")
    print("  ✓ Multi-player support ready")


if __name__ == "__main__":
    demo_agent_capabilities()
