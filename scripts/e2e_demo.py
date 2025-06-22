#!/usr/bin/env python3
"""
End-to-End Demo: Human Player + WASD-Controlled Agent

This script creates a live demo where:
1. A human player can join the Factorio server normally
2. An external agent connects via RCON as a separate player
3. WASD keyboard input controls the agent's movement in real-time
4. Both human and agent operate simultaneously

Usage:
    python3 scripts/e2e_demo.py [--agent-name <name>] [--host <host>] [--port <port>]

Requirements:
    - Factorio server running with RCON enabled
    - agent-control mod installed and loaded
    - Terminal that supports keyboard input capture
"""

import asyncio
import sys
import threading
import time
from typing import Dict, Optional, Set

try:
    import keyboard  # For WASD input capture
except ImportError:
    print("Error: 'keyboard' library not found. Install with: pip install keyboard")
    print("Note: On some systems you may need to run with sudo for keyboard capture")
    sys.exit(1)

from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from factorio_mcp.rcon import FactorioRCON


class AgentController:
    """Controls an agent player via RCON with WASD keyboard input."""
    
    # Direction mapping: WASD -> Factorio direction (0=North, 2=East, 4=South, 6=West)
    DIRECTION_MAP = {
        'w': 0,  # North
        'd': 2,  # East  
        's': 4,  # South
        'a': 6,  # West
    }
    
    def __init__(self, host: str = "localhost", port: int = 34198, 
                 password: str = "admin", agent_name: str = "Agent"):
        self.host = host
        self.port = port
        self.password = password
        self.agent_name = agent_name
        self.rcon: Optional[FactorioRCON] = None
        
        # Movement state
        self.current_direction: Optional[int] = None
        self.pressed_keys: Set[str] = set()
        self.movement_active = False
        
        # Control flags
        self.running = True
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to Factorio server and ensure agent player exists."""
        try:
            print(f"Connecting to Factorio server at {self.host}:{self.port}...")
            self.rcon = FactorioRCON(self.host, self.port, self.password)
            self.rcon.connect()
            
            # Test connection
            response = self.rcon.send_command("/hello")
            if "Hello from RCON!" not in response:
                print("Warning: agent-control mod may not be loaded properly")
                
            # Ensure agent player exists
            print(f"Creating/ensuring agent player: {self.agent_name}")
            response = self.rcon.send_command(f"/ensure_player {self.agent_name}")
            print(f"Server response: {response}")
            
            self.connected = True
            print("✓ Connected successfully!")
            return True
            
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from server."""
        if self.rcon:
            try:
                # Stop agent movement before disconnecting
                if self.movement_active:
                    self.rcon.send_command(f"/agent_stop {self.agent_name}")
                self.rcon.close()
            except:
                pass
            finally:
                self.rcon = None
                self.connected = False
    
    def move_agent(self, direction: int):
        """Send movement command to agent."""
        if not self.connected or not self.rcon:
            return
            
        try:
            response = self.rcon.send_command(f"/agent_move {self.agent_name} {direction}")
            # Only print response if there's an error
            if "not found" in response.lower() or "failed" in response.lower():
                print(f"Movement error: {response}")
                
        except Exception as e:
            print(f"Failed to send movement command: {e}")
    
    def stop_agent(self):
        """Stop agent movement."""
        if not self.connected or not self.rcon:
            return
            
        try:
            self.rcon.send_command(f"/agent_stop {self.agent_name}")
            self.movement_active = False
        except Exception as e:
            print(f"Failed to stop agent: {e}")
    
    def get_agent_status(self) -> str:
        """Get current agent status."""
        if not self.connected or not self.rcon:
            return "Disconnected"
            
        try:
            response = self.rcon.send_command(f"/agent_status {self.agent_name}")
            return response
        except Exception as e:
            return f"Error getting status: {e}"
    
    def on_key_press(self, key_event):
        """Handle key press events."""
        key = key_event.name.lower()
        
        if key in ['w', 'a', 's', 'd']:
            if key not in self.pressed_keys:
                self.pressed_keys.add(key)
                self.update_movement()
        
        elif key == 'q':
            print("\nQuitting...")
            self.running = False
            
        elif key == 'space':
            # Status check
            status = self.get_agent_status()
            print(f"\nAgent Status: {status}")
    
    def on_key_release(self, key_event):
        """Handle key release events."""
        key = key_event.name.lower()
        
        if key in ['w', 'a', 's', 'd']:
            if key in self.pressed_keys:
                self.pressed_keys.remove(key)
                self.update_movement()
    
    def update_movement(self):
        """Update agent movement based on currently pressed keys."""
        if not self.pressed_keys:
            # No keys pressed - stop movement
            if self.movement_active:
                self.stop_agent()
            return
        
        # Determine direction based on pressed keys
        # Priority: W > S > D > A (if multiple keys pressed)
        direction = None
        
        if 'w' in self.pressed_keys:
            direction = self.DIRECTION_MAP['w']  # North
        elif 's' in self.pressed_keys:
            direction = self.DIRECTION_MAP['s']  # South
        elif 'd' in self.pressed_keys:
            direction = self.DIRECTION_MAP['d']  # East
        elif 'a' in self.pressed_keys:
            direction = self.DIRECTION_MAP['a']  # West
        
        # Only send command if direction changed
        if direction != self.current_direction:
            self.current_direction = direction
            self.move_agent(direction)
            self.movement_active = True
    
    def start_keyboard_listener(self):
        """Start listening for keyboard events."""
        print("Starting keyboard listener...")
        print("Controls:")
        print("  W/A/S/D - Move agent (North/West/South/East)")
        print("  SPACE   - Show agent status")
        print("  Q       - Quit demo")
        print()
        
        # Hook keyboard events
        keyboard.on_press(self.on_key_press)
        keyboard.on_release(self.on_key_release)
    
    def run(self):
        """Main demo loop."""
        if not self.connect():
            return
        
        try:
            self.start_keyboard_listener()
            
            print(f"✓ Agent '{self.agent_name}' ready for control!")
            print("✓ Keyboard controls active")
            print("✓ Human players can now join the server normally")
            print("\nDemo running - press Q to quit")
            
            # Main loop - just keep the program alive
            last_status_time = time.time()
            
            while self.running:
                time.sleep(0.1)
                
                # Periodic status update (every 5 seconds)
                if time.time() - last_status_time > 5:
                    if self.connected:
                        status = self.get_agent_status()
                        if "STATUS:" in status:
                            # Parse and display clean status
                            try:
                                status_data = status.split("STATUS:", 1)[1]
                                print(f"Agent Status: {status_data}")
                            except:
                                pass
                    last_status_time = time.time()
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            # Cleanup
            try:
                keyboard.unhook_all()
            except:
                pass
            self.disconnect()
            print("Demo ended")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Factorio E2E Demo: Human + Agent")
    parser.add_argument("--host", default="localhost", help="RCON host")
    parser.add_argument("--port", type=int, default=34198, help="RCON port")
    parser.add_argument("--password", default="admin", help="RCON password")
    parser.add_argument("--agent-name", default="Agent", help="Agent player name")
    
    args = parser.parse_args()
    
    print("=== Factorio End-to-End Demo ===")
    print()
    print("This demo shows simultaneous human and agent play:")
    print("1. Human player connects to server via Factorio client")
    print("2. Agent player controlled via WASD keys in this terminal")
    print("3. Both players operate simultaneously in the same world")
    print()
    print(f"Connecting agent '{args.agent_name}' to {args.host}:{args.port}")
    print()
    
    # Check if running with proper permissions
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        import os
        if os.geteuid() != 0:
            print("Note: If keyboard capture doesn't work, you may need to run with sudo")
            print("      sudo python3 scripts/e2e_demo.py")
            print()
    
    controller = AgentController(
        host=args.host,
        port=args.port, 
        password=args.password,
        agent_name=args.agent_name
    )
    
    controller.run()


if __name__ == "__main__":
    main()
