#!/usr/bin/env python3
"""
RCON Test Script for Multiple Factorio Servers
Tests RCON connectivity to all running Factorio instances.
"""

import socket
import struct
import time
import sys
from typing import Optional, Dict, Any

class FactorioRCON:
    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password
        self.socket: Optional[socket.socket] = None
        self.request_id = 1

    def connect(self) -> bool:
        """Connect to the RCON server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            
            # Authenticate
            if not self._authenticate():
                return False
                
            print(f"✓ Connected to RCON at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to connect to RCON at {self.host}:{self.port}: {e}")
            return False

    def _authenticate(self) -> bool:
        """Authenticate with the RCON server."""
        auth_packet = self._create_packet(3, self.password)  # Type 3 = AUTH
        self.socket.send(auth_packet)
        
        response = self._read_packet()
        return response and response['id'] == self.request_id

    def _create_packet(self, packet_type: int, body: str) -> bytes:
        """Create an RCON packet."""
        body_bytes = body.encode('utf-8')
        packet_id = self.request_id
        self.request_id += 1
        
        # Packet structure: size (4) + id (4) + type (4) + body + null terminator (2)
        size = 4 + 4 + len(body_bytes) + 2
        packet = struct.pack('<iii', size, packet_id, packet_type)
        packet += body_bytes + b'\x00\x00'
        
        return packet

    def _read_packet(self) -> Optional[Dict[str, Any]]:
        """Read an RCON packet response."""
        try:
            # Read packet size
            size_data = self.socket.recv(4)
            if len(size_data) < 4:
                return None
                
            size = struct.unpack('<i', size_data)[0]
            
            # Read packet data
            data = b''
            while len(data) < size:
                chunk = self.socket.recv(size - len(data))
                if not chunk:
                    return None
                data += chunk
            
            # Parse packet
            packet_id, packet_type = struct.unpack('<ii', data[:8])
            body = data[8:-2].decode('utf-8', errors='ignore')
            
            return {
                'id': packet_id,
                'type': packet_type,
                'body': body
            }
            
        except Exception as e:
            print(f"Error reading packet: {e}")
            return None

    def execute_command(self, command: str) -> Optional[str]:
        """Execute a command via RCON."""
        if not self.socket:
            return None
            
        try:
            command_packet = self._create_packet(2, command)  # Type 2 = EXECCOMMAND
            self.socket.send(command_packet)
            
            response = self._read_packet()
            return response['body'] if response else None
            
        except Exception as e:
            print(f"Error executing command '{command}': {e}")
            return None

    def disconnect(self):
        """Disconnect from the RCON server."""
        if self.socket:
            self.socket.close()
            self.socket = None

def test_rcon_servers():
    """Test RCON connectivity to all servers."""
    servers = [
        {'name': 'Server 1', 'host': 'localhost', 'port': 27015, 'password': 'factorio'},
        {'name': 'Server 2', 'host': 'localhost', 'port': 27016, 'password': 'factorio'},
        {'name': 'Server 3', 'host': 'localhost', 'port': 27017, 'password': 'factorio'},
    ]
    
    print("Testing RCON connectivity to Factorio servers...\n")
    
    for server in servers:
        print(f"Testing {server['name']} at {server['host']}:{server['port']}")
        
        rcon = FactorioRCON(server['host'], server['port'], server['password'])
        
        if rcon.connect():
            # Test some basic commands
            commands = [
                '/version',
                '/time',
                '/players'
            ]
            
            for cmd in commands:
                result = rcon.execute_command(cmd)
                if result:
                    print(f"  {cmd}: {result.strip()}")
                else:
                    print(f"  {cmd}: No response")
            
            rcon.disconnect()
        
        print()

def main():
    """Main function."""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("Usage: python3 rcon_test.py [--help]")
            print("Tests RCON connectivity to all Factorio server instances.")
            return
    
    test_rcon_servers()

if __name__ == '__main__':
    main()
