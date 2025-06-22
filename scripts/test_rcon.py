#!/usr/bin/env python3
"""
RCON client for testing Factorio server connections
"""

import argparse
import socket
import struct
import sys
import time
from typing import Optional, Tuple


class RCONClient:
    def __init__(self, host: str = "localhost", port: int = 34198, password: str = "admin"):
        self.host = host
        self.port = port
        self.password = password
        self.socket: Optional[socket.socket] = None
        self.request_id = 1
        
    def connect(self) -> bool:
        """Connect to RCON server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            
            # Authenticate
            return self._authenticate()
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
            
    def _authenticate(self) -> bool:
        """Authenticate with RCON server"""
        if not self.socket:
            return False
            
        # Send auth packet
        auth_packet = self._create_packet(3, self.password)  # Type 3 = AUTH
        self.socket.send(auth_packet)
        
        # Read response
        response = self._read_packet()
        if response is None:
            return False
            
        request_id, packet_type, data = response
        return request_id != -1  # -1 indicates auth failure
        
    def _create_packet(self, packet_type: int, body: str) -> bytes:
        """Create RCON packet"""
        body_bytes = body.encode('utf-8') + b'\x00'
        length = 4 + 4 + len(body_bytes) + 1  # id + type + body + null terminator
        
        packet = struct.pack('<i', length)  # Length
        packet += struct.pack('<i', self.request_id)  # Request ID
        packet += struct.pack('<i', packet_type)  # Type
        packet += body_bytes  # Body
        packet += b'\x00'  # Null terminator
        
        self.request_id += 1
        return packet
        
    def _read_packet(self) -> Optional[Tuple[int, int, str]]:
        """Read RCON packet"""
        if not self.socket:
            return None
            
        try:
            # Read length
            length_data = self.socket.recv(4)
            if len(length_data) != 4:
                return None
                
            length = struct.unpack('<i', length_data)[0]
            
            # Read rest of packet
            packet_data = b''
            while len(packet_data) < length:
                chunk = self.socket.recv(length - len(packet_data))
                if not chunk:
                    return None
                packet_data += chunk
                
            # Parse packet
            request_id = struct.unpack('<i', packet_data[0:4])[0]
            packet_type = struct.unpack('<i', packet_data[4:8])[0]
            body = packet_data[8:-2].decode('utf-8')  # Remove null terminators
            
            return request_id, packet_type, body
            
        except Exception as e:
            print(f"Read error: {e}")
            return None
            
    def send_command(self, command: str) -> Optional[str]:
        """Send command and get response"""
        if not self.socket:
            if not self.connect():
                return None
                
        # Send command packet
        cmd_packet = self._create_packet(2, command)  # Type 2 = COMMAND
        self.socket.send(cmd_packet)
        
        # Read response
        response = self._read_packet()
        if response is None:
            return None
            
        request_id, packet_type, data = response
        return data
        
    def close(self):
        """Close connection"""
        if self.socket:
            self.socket.close()
            self.socket = None


def main():
    parser = argparse.ArgumentParser(description="RCON client for Factorio")
    parser.add_argument("--host", default="localhost", help="RCON host")
    parser.add_argument("--port", type=int, default=34198, help="RCON port")
    parser.add_argument("--password", default="admin", help="RCON password")
    parser.add_argument("--command", help="Single command to execute")
    parser.add_argument("--timeout", type=int, default=5, help="Connection timeout")
    
    args = parser.parse_args()
    
    client = RCONClient(args.host, args.port, args.password)
    
    if args.command:
        # Single command mode
        print(f"Connecting to {args.host}:{args.port}...")
        if not client.connect():
            print("Failed to connect")
            sys.exit(1)
            
        print(f"Sending command: {args.command}")
        response = client.send_command(args.command)
        
        if response is not None:
            print("Response:")
            print(response)
        else:
            print("No response received")
            
        client.close()
    else:
        # Interactive mode
        print(f"RCON Interactive Mode - {args.host}:{args.port}")
        print("Type 'quit' to exit")
        
        while True:
            try:
                command = input("rcon> ").strip()
                if command.lower() in ['quit', 'exit']:
                    break
                    
                if not command:
                    continue
                    
                if not client.socket and not client.connect():
                    print("Failed to connect")
                    continue
                    
                response = client.send_command(command)
                if response is not None:
                    print(response)
                else:
                    print("No response received")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
                
        client.close()
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
