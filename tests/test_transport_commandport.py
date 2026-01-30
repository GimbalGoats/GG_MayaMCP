"""Tests for the commandPort transport layer.

These tests verify the CommandPortClient's behavior including:
- Connection handling
- Retry logic with exponential backoff
- Timeout handling
- Error translation
- State management
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from maya_mcp.errors import MayaTimeoutError, MayaUnavailableError
from maya_mcp.transport.commandport import CommandPortClient
from maya_mcp.types import ConnectionConfig, ConnectionStatus


class TestCommandPortClientInit:
    """Tests for CommandPortClient initialization."""

    def test_default_config(self) -> None:
        """Client uses correct default configuration."""
        client = CommandPortClient()

        assert client.config.host == "localhost"
        assert client.config.port == 7001
        assert client.config.connect_timeout == 5.0
        assert client.config.command_timeout == 30.0
        assert client.config.max_retries == 3

    def test_custom_config(self) -> None:
        """Client accepts custom configuration."""
        client = CommandPortClient(
            host="127.0.0.1",
            port=7002,
            connect_timeout=10.0,
            command_timeout=60.0,
            max_retries=5,
        )

        assert client.config.host == "127.0.0.1"
        assert client.config.port == 7002
        assert client.config.connect_timeout == 10.0
        assert client.config.command_timeout == 60.0
        assert client.config.max_retries == 5

    def test_rejects_remote_host(self) -> None:
        """Client rejects non-localhost hosts."""
        with pytest.raises(ValueError, match="Only localhost"):
            CommandPortClient(host="192.168.1.1")

    def test_rejects_invalid_port(self) -> None:
        """Client rejects invalid port numbers."""
        with pytest.raises(ValueError, match="Invalid port"):
            CommandPortClient(port=0)

        with pytest.raises(ValueError, match="Invalid port"):
            CommandPortClient(port=70000)

    def test_initial_state_offline(self) -> None:
        """Client starts in offline state."""
        client = CommandPortClient()
        assert client.get_status() == ConnectionStatus.OFFLINE
        assert not client.is_connected()


class TestCommandPortClientConnect:
    """Tests for CommandPortClient.connect()."""

    def test_connect_success(self) -> None:
        """Successful connection updates state correctly."""
        client = CommandPortClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            result = client.connect()

            assert result is True
            assert client.is_connected()
            assert client.get_status() == ConnectionStatus.OK
            mock_socket.connect.assert_called_once_with(("localhost", 7001))

    def test_connect_already_connected(self) -> None:
        """Connect returns True if already connected."""
        client = CommandPortClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()
            result = client.connect()  # Second call

            assert result is True
            # Socket should only be created once
            assert mock_socket_class.call_count == 1

    def test_connect_refused_retries(self) -> None:
        """Connection refused triggers retries with backoff."""
        client = CommandPortClient(max_retries=3, retry_base_delay=0.01)

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.connect.side_effect = ConnectionRefusedError()
            mock_socket_class.return_value = mock_socket

            with pytest.raises(MayaUnavailableError) as exc_info:
                client.connect()

            assert exc_info.value.attempts == 3
            assert "Connection refused" in str(exc_info.value.last_error)
            assert client.get_status() == ConnectionStatus.OFFLINE

    def test_connect_timeout_retries(self) -> None:
        """Connection timeout triggers retries."""
        client = CommandPortClient(max_retries=2, retry_base_delay=0.01)

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.connect.side_effect = TimeoutError()
            mock_socket_class.return_value = mock_socket

            with pytest.raises(MayaUnavailableError) as exc_info:
                client.connect()

            assert exc_info.value.attempts == 2
            assert "timed out" in str(exc_info.value.last_error)


class TestCommandPortClientDisconnect:
    """Tests for CommandPortClient.disconnect()."""

    def test_disconnect_when_connected(self) -> None:
        """Disconnect closes socket and updates state."""
        client = CommandPortClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()
            result = client.disconnect()

            assert result is True
            assert not client.is_connected()
            assert client.get_status() == ConnectionStatus.OFFLINE
            mock_socket.close.assert_called_once()

    def test_disconnect_when_not_connected(self) -> None:
        """Disconnect returns False if not connected."""
        client = CommandPortClient()
        result = client.disconnect()

        assert result is False
        assert client.get_status() == ConnectionStatus.OFFLINE


class TestCommandPortClientExecute:
    """Tests for CommandPortClient.execute()."""

    def test_execute_success(self) -> None:
        """Successful execution returns response."""
        client = CommandPortClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.recv.side_effect = [b"['pCube1', 'pSphere1']", TimeoutError()]
            mock_socket_class.return_value = mock_socket

            client.connect()
            result = client.execute("cmds.ls(selection=True)")

            assert result == "['pCube1', 'pSphere1']"
            mock_socket.sendall.assert_called_once()

    def test_execute_auto_connects(self) -> None:
        """Execute connects automatically if not connected."""
        client = CommandPortClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.recv.side_effect = [b"result", TimeoutError()]
            mock_socket_class.return_value = mock_socket

            result = client.execute("cmds.ls()")

            assert result == "result"
            assert client.is_connected()

    def test_execute_timeout(self) -> None:
        """Execute raises MayaTimeoutError on timeout."""
        client = CommandPortClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            # Simulate timeout during send
            mock_socket.sendall.side_effect = TimeoutError()

            with pytest.raises(MayaTimeoutError) as exc_info:
                client.execute("long_running_command()")

            assert exc_info.value.operation == "execute"

    def test_execute_connection_lost(self) -> None:
        """Execute raises MayaUnavailableError when connection is lost."""
        client = CommandPortClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            # Simulate connection reset
            mock_socket.sendall.side_effect = ConnectionResetError()

            with pytest.raises(MayaUnavailableError) as exc_info:
                client.execute("cmds.ls()")

            assert "Lost connection" in exc_info.value.message
            assert not client.is_connected()


class TestCommandPortClientHealth:
    """Tests for CommandPortClient.get_health()."""

    def test_health_offline(self) -> None:
        """Health check returns correct offline status."""
        client = CommandPortClient()
        health = client.get_health()

        assert health.status == "offline"
        assert health.last_contact is None
        assert health.host == "localhost"
        assert health.port == 7001

    def test_health_connected(self) -> None:
        """Health check returns correct connected status."""
        client = CommandPortClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()
            health = client.get_health()

            assert health.status == "ok"
            assert health.last_contact is not None
            assert health.last_error is None


class TestCommandPortClientReconfigure:
    """Tests for CommandPortClient.reconfigure()."""

    def test_reconfigure_disconnects(self) -> None:
        """Reconfigure disconnects existing connection."""
        client = CommandPortClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()
            assert client.is_connected()

            client.reconfigure(port=7002)

            assert not client.is_connected()
            assert client.config.port == 7002

    def test_reconfigure_partial(self) -> None:
        """Reconfigure updates only specified values."""
        client = CommandPortClient(host="localhost", port=7001)

        client.reconfigure(port=7002)

        assert client.config.host == "localhost"
        assert client.config.port == 7002


class TestConnectionConfig:
    """Tests for ConnectionConfig validation."""

    def test_valid_config(self) -> None:
        """Valid configuration is accepted."""
        config = ConnectionConfig(
            host="localhost",
            port=7001,
            connect_timeout=5.0,
            command_timeout=30.0,
        )
        assert config.host == "localhost"

    def test_invalid_host(self) -> None:
        """Non-localhost host is rejected."""
        with pytest.raises(ValueError, match="Only localhost"):
            ConnectionConfig(host="remote.server.com")

    def test_invalid_timeout(self) -> None:
        """Non-positive timeout is rejected."""
        with pytest.raises(ValueError, match="connect_timeout must be positive"):
            ConnectionConfig(connect_timeout=0)

        with pytest.raises(ValueError, match="command_timeout must be positive"):
            ConnectionConfig(command_timeout=-1)

    def test_invalid_retries(self) -> None:
        """Negative retries is rejected."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            ConnectionConfig(max_retries=-1)
