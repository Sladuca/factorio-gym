"""Integration tests for agent control functionality."""

import subprocess
import sys
import time
from pathlib import Path
from typing import Generator

import pytest

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from factorio_mcp.rcon import FactorioRCON
from dev_server import FactorioDevServer


@pytest.fixture(scope="module")
def test_server() -> Generator[FactorioDevServer, None, None]:
    """Start a test Factorio server for integration tests."""
    server = FactorioDevServer(test_mode=True)
    
    # Check if Factorio is available
    if not server._check_factorio_binary():
        pytest.skip("Factorio binary not available for integration tests")
    
    # Start the server
    if not server.start_server():
        pytest.skip("Failed to start Factorio server")
    
    # Wait a bit more for server to be fully ready
    time.sleep(5)
    
    try:
        yield server
    finally:
        server.stop_server()


@pytest.fixture
def rcon_client(test_server: FactorioDevServer) -> Generator[FactorioRCON, None, None]:
    """RCON client connected to test server."""
    client = FactorioRCON("localhost", test_server.rcon_port, "admin")
    client.connect()
    try:
        yield client
    finally:
        client.close()


@pytest.mark.integration
class TestAgentControl:
    """Integration tests for agent control commands."""

    def test_player_login_and_walk_left(self, rcon_client: FactorioRCON) -> None:
        """Test that a player can log in and walk left."""
        test_player = "testbot"
        
        print("Testing player creation and movement...")
        
        # Create the test player first
        create_response = rcon_client.send_command(f"ensure_player {test_player}")
        print(f"Create player response: {create_response}")
        assert ("created" in create_response.lower() or "already exists" in create_response.lower())
        
        # Get initial status
        status_response = rcon_client.send_command(f"agent_status {test_player}")
        print(f"Initial status: {status_response}")
        assert "STATUS:" in status_response
        assert test_player in status_response
        
        # Test movement - Direction 6 = West (left)
        print(f"Moving {test_player} left...")
        move_response = rcon_client.send_command(f"agent_move {test_player} 6")
        print(f"Move response: {move_response}")
        assert "Moving player" in move_response
        assert test_player in move_response
        assert "direction 6" in move_response
        
        # Check final status shows walking
        final_status = rcon_client.send_command(f"agent_status {test_player}")
        print(f"Final status: {final_status}")
        assert "STATUS:" in final_status
        assert "walking" in final_status.lower()
        
        # Stop the player
        stop_response = rcon_client.send_command(f"agent_stop {test_player}")
        print(f"Stop response: {stop_response}")
        assert "Stopped player" in stop_response
        assert test_player in stop_response

    def test_agent_commands_available(self, rcon_client: FactorioRCON) -> None:
        """Test that our agent control commands are available."""
        # Test help shows our commands
        help_response = rcon_client.send_command("/help")
        print(f"Help response: {help_response}")
        
        # Test agent_move with no parameters shows usage
        move_usage = rcon_client.send_command("agent_move")
        print(f"Move usage: {move_usage}")
        assert "Usage:" in move_usage
        assert "agent_move" in move_usage
        
        # Test agent_status with no parameters shows usage  
        status_usage = rcon_client.send_command("agent_status")
        print(f"Status usage: {status_usage}")
        assert "Usage:" in status_usage
        assert "agent_status" in status_usage
        
        # Test ensure_player with no parameters shows usage
        ensure_usage = rcon_client.send_command("ensure_player")
        print(f"Ensure usage: {ensure_usage}")
        assert "Usage:" in ensure_usage
        assert "ensure_player" in ensure_usage

    def test_rcon_basic_commands(self, rcon_client: FactorioRCON) -> None:
        """Test basic RCON functionality works."""
        # Test server info
        response = rcon_client.send_command("/time")
        assert response  # Should get some time response
        
        # Test version info  
        response = rcon_client.send_command("/version")
        assert response is not None  # Should get some response


@pytest.mark.integration
def test_server_startup_and_mod_loading(test_server: FactorioDevServer) -> None:
    """Test that server starts and our mod loads correctly."""
    # Server should be running (fixture ensures this)
    assert test_server.process is not None
    assert test_server.process.poll() is None
    
    # Connect via RCON and verify mod commands exist
    with FactorioRCON("localhost", 34198, "admin") as rcon:
        # Test that our custom commands exist by checking usage messages
        move_response = rcon.send_command("agent_move")
        assert "Usage:" in move_response  # Our mod's usage message
        
        # Test ensure_player command exists
        ensure_response = rcon.send_command("ensure_player")
        assert "Usage:" in ensure_response  # Our mod's usage message
        
        # Test agent_status command exists  
        status_response = rcon.send_command("agent_status")
        assert "Usage:" in status_response  # Our mod's usage message


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
