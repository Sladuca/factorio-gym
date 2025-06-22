"""Tests for development server functionality."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from dev_server import FactorioDevServer


class TestFactorioDevServer:
    """Test cases for FactorioDevServer."""

    def test_stop_server_idempotent(self) -> None:
        """Test that stop_server can be called multiple times without error."""
        server = FactorioDevServer()
        
        # Mock a running process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.pid = 12345
        server.process = mock_process
        
        with patch('os.killpg') as mock_killpg, \
             patch('os.getpgid', return_value=12345) as mock_getpgid:
            
            # First call should work normally
            server.stop_server()
            mock_killpg.assert_called_once_with(12345, signal.SIGTERM)
            mock_process.wait.assert_called_once()
            
            # Process should be set to None after stopping
            assert server.process is None
            
            # Second call should be safe (no-op)
            mock_killpg.reset_mock()
            mock_process.wait.reset_mock()
            
            server.stop_server()
            mock_killpg.assert_not_called()
            mock_process.wait.assert_not_called()

    def test_stop_server_handles_dead_process(self) -> None:
        """Test that stop_server handles ProcessLookupError gracefully."""
        server = FactorioDevServer()
        
        # Mock a process that appears running but is actually dead
        mock_process = Mock()
        mock_process.poll.return_value = None  # Appears running
        mock_process.pid = 12345
        server.process = mock_process
        
        with patch('os.killpg', side_effect=ProcessLookupError()) as mock_killpg, \
             patch('os.getpgid', return_value=12345):
            
            # Should handle ProcessLookupError gracefully
            server.stop_server()
            mock_killpg.assert_called_once_with(12345, signal.SIGTERM)
            # Process should still be set to None
            assert server.process is None

    def test_stop_server_already_stopped_process(self) -> None:
        """Test that stop_server skips already stopped processes."""
        server = FactorioDevServer()
        
        # Mock a process that has already exited
        mock_process = Mock()
        mock_process.poll.return_value = 0  # Process has exited
        server.process = mock_process
        
        with patch('os.killpg') as mock_killpg:
            server.stop_server()
            # Should not try to kill an already dead process
            mock_killpg.assert_not_called()

    def test_find_factorio_binary_checks_path_first(self) -> None:
        """Test that _find_factorio_binary checks PATH first."""
        server = FactorioDevServer()
        
        with patch('subprocess.run') as mock_run:
            # Mock successful factorio in PATH
            mock_result = Mock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = server._find_factorio_binary()
            assert result == "factorio"
            mock_run.assert_called_once()

    def test_find_factorio_binary_fallback_to_platform_specific(self) -> None:
        """Test that _find_factorio_binary falls back to platform-specific paths."""
        server = FactorioDevServer()
        
        with patch('subprocess.run', side_effect=FileNotFoundError()) as mock_run, \
             patch('platform.system', return_value='Darwin'), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=True):
            
            # First call fails (PATH check), second succeeds (platform check)
            mock_run.side_effect = [
                FileNotFoundError(),  # PATH check fails
                Mock(returncode=0)     # Platform-specific path succeeds
            ]
            
            result = server._find_factorio_binary()
            # Should return the platform-specific path
            assert "factorio.app/Contents/MacOS/factorio" in result

    def test_check_factorio_binary_timeout_handling(self) -> None:
        """Test that _check_factorio_binary handles timeouts gracefully."""
        server = FactorioDevServer("some-path")
        
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("cmd", 10)):
            result = server._check_factorio_binary()
            assert result is False

    def test_create_save_skips_existing(self) -> None:
        """Test that create_save skips creation if save already exists."""
        server = FactorioDevServer()
        
        with patch('pathlib.Path.exists', return_value=True):
            result = server.create_save()
            assert result is True

    def test_start_server_fails_without_binary(self) -> None:
        """Test that start_server fails gracefully when binary is not available."""
        server = FactorioDevServer("nonexistent-factorio")
        
        result = server.start_server()
        assert result is False


@pytest.mark.integration
class TestFactorioDevServerIntegration:
    """Integration tests that require actual Factorio binary."""

    def test_factorio_version_check(self) -> None:
        """Test that we can check Factorio version if binary exists."""
        server = FactorioDevServer()
        
        # This will either find a real Factorio or return False
        # We don't require Factorio for unit tests, but if present, it should work
        binary_found = server._check_factorio_binary()
        
        if binary_found:
            # If we found a binary, it should be callable
            result = subprocess.run([server.factorio_path, "--version"], 
                                  capture_output=True, timeout=10)
            assert result.returncode == 0
            assert b"Version:" in result.stdout
        else:
            # If no binary found, that's fine for CI/testing environments
            pytest.skip("Factorio binary not available for integration test")


if __name__ == "__main__":
    pytest.main([__file__])
