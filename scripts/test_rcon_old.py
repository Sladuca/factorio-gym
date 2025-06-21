#!/usr/bin/env python3
"""Simple RCON client for testing Factorio server commands."""

import argparse
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from factorio_mcp.rcon import FactorioRCON


def main() -> None:
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.socket = None
        self.request_id = 1
        
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        
        # Authenticate
        self._send_packet(3, self.password)  # SERVERDATA_AUTH
        response = self._receive_packet()
        
        if response[2] != self.request_id:
            raise Exception("Authentication failed")
        print("Connected and authenticated")
    
    def send_command(self, command):
        self._send_packet(2, command)  # SERVERDATA_EXECCOMMAND
        response = self._receive_packet()
        return response[3]  # Response body
    
    def _send_packet(self, packet_type, body):
        body_bytes = body.encode('utf-8')
        packet_size = 10 + len(body_bytes)
        
        packet = struct.pack('<iii', packet_size, self.request_id, packet_type)
        packet += body_bytes
        packet += b'\x00\x00'
        
        self.socket.send(packet)
        self.request_id += 1
    
    def _receive_packet(self):
        # Read packet size
        size_data = self.socket.recv(4)
        packet_size = struct.unpack('<i', size_data)[0]
        
        # Read rest of packet
        data = self.socket.recv(packet_size)
        request_id, packet_type = struct.unpack('<ii', data[:8])
        body = data[8:-2].decode('utf-8')
        
        return (packet_size, request_id, packet_type, body)
    
    def close(self):
        if self.socket:
            self.socket.close()

def main():
    parser = argparse.ArgumentParser(description='Test Factorio RCON connection')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=34198, help='RCON port')
    parser.add_argument('--password', default='admin', help='RCON password')
    parser.add_argument('--command', help='Single command to execute')
    
    args = parser.parse_args()
    
    rcon = FactorioRCON(args.host, args.port, args.password)
    
    try:
        rcon.connect()
        
        if args.command:
            response = rcon.send_command(args.command)
            print(f"Response: {response}")
        else:
            # Interactive mode
            print("Interactive RCON mode. Type 'quit' to exit.")
            while True:
                command = input("factorio> ").strip()
                if command.lower() in ['quit', 'exit']:
                    break
                if command:
                    response = rcon.send_command(command)
                    print(f"Response: {response}")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        rcon.close()

if __name__ == "__main__":
    main()
