"""RCON client for Factorio server communication."""

import socket
import struct
from typing import Optional


class FactorioRCON:
    """RCON client for communicating with Factorio servers."""

    def __init__(self, host: str, port: int, password: str) -> None:
        self.host = host
        self.port = port
        self.password = password
        self.socket: Optional[socket.socket] = None
        self.request_id = 1

    def connect(self) -> None:
        """Connect to the server and authenticate."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

        # Authenticate
        self._send_packet(3, self.password)  # SERVERDATA_AUTH
        response = self._receive_packet()

        if response[2] != self.request_id:
            raise ConnectionError("Authentication failed")

    def send_command(self, command: str) -> str:
        """Send a command and return the response."""
        if not self.socket:
            raise RuntimeError("Not connected to server")

        self._send_packet(2, command)  # SERVERDATA_EXECCOMMAND
        response = self._receive_packet()
        return response[3]  # Response body

    def close(self) -> None:
        """Close the connection."""
        if self.socket:
            self.socket.close()
            self.socket = None

    def _send_packet(self, packet_type: int, body: str) -> None:
        """Send an RCON packet."""
        if not self.socket:
            raise RuntimeError("Not connected to server")

        body_bytes = body.encode("utf-8")
        packet_size = 10 + len(body_bytes)

        packet = struct.pack("<iii", packet_size, self.request_id, packet_type)
        packet += body_bytes
        packet += b"\x00\x00"

        self.socket.send(packet)
        self.request_id += 1

    def _receive_packet(self) -> tuple[int, int, int, str]:
        """Receive an RCON packet."""
        if not self.socket:
            raise RuntimeError("Not connected to server")

        # Read packet size
        size_data = self.socket.recv(4)
        packet_size = struct.unpack("<i", size_data)[0]

        # Read rest of packet
        data = self.socket.recv(packet_size)
        request_id, packet_type = struct.unpack("<ii", data[:8])
        body = data[8:-2].decode("utf-8")

        return (packet_size, request_id, packet_type, body)

    def __enter__(self) -> "FactorioRCON":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
