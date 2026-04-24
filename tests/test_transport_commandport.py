"""Tests for the commandPort transport layer.

These tests verify the CommandPortClient's behavior including:
- Connection handling
- Retry logic with exponential backoff
- Timeout handling
- Error translation
- State management
"""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from maya_mcp.errors import MayaTimeoutError, MayaUnavailableError
from maya_mcp.transport.commandport import CommandPortClient, _parse_maya_response
from maya_mcp.types import ConnectionConfig, ConnectionStatus


class BlockingCommandSocket:
    """Socket fake that can pause the first command while tests race callers."""

    def __init__(self) -> None:
        self.first_recv_started = threading.Event()
        self.release_first_recv = threading.Event()
        self.second_send_started = threading.Event()
        self.close_started = threading.Event()
        self.send_order: list[str] = []
        self._lock = threading.Lock()
        self._active_command = ""
        self._recv_counts: dict[str, int] = {}

    def setsockopt(self, *_args: object) -> None:
        """Accept socket keepalive options."""

    def settimeout(self, _timeout: float) -> None:
        """Accept timeout changes."""

    def connect(self, _address: tuple[str, int]) -> None:
        """Pretend to connect successfully."""

    def sendall(self, data: bytes) -> None:
        """Record which command was sent."""
        command = data.decode("utf-8")
        command_name = "second" if "second" in command else "first"
        with self._lock:
            self._active_command = command_name
            self.send_order.append(command_name)
        if command_name == "second":
            self.second_send_started.set()

    def recv(self, _buffer_size: int) -> bytes:
        """Return one response chunk per command, then simulate read completion."""
        with self._lock:
            command_name = self._active_command
            count = self._recv_counts.get(command_name, 0)
            self._recv_counts[command_name] = count + 1

        if count > 0:
            raise TimeoutError()

        if command_name == "first":
            self.first_recv_started.set()
            if not self.release_first_recv.wait(timeout=2.0):
                raise TimeoutError()

        return command_name.encode("utf-8")

    def close(self) -> None:
        """Record close attempts."""
        self.close_started.set()


class TestParseMayaResponse:
    """Tests for commandPort response cleanup."""

    def test_ignores_known_maya_noise_before_plain_output(self) -> None:
        """Known Maya startup/plugin warning lines do not replace command output."""
        raw_response = (
            "Arnold renderer not loaded.\n"
            "The MtoA plug-in needed for this scene is not loaded.\n"
            "Make sure Autoload is on in the Plug-in Manager.\n"
            "See this article for more detail.\n"
            "https://www.autodesk.com/maya-arnold-not-available-error\n"
            "\x00False\n\x00False\n\x00"
        )

        assert _parse_maya_response(raw_response) == "False"

    def test_preserves_multiple_non_json_output_lines(self) -> None:
        """Non-JSON multi-line command output is preserved after cleanup."""
        raw_response = "None\n\x00first\n\x00second\n\x00first\n\x00"

        assert _parse_maya_response(raw_response) == "first\nsecond"


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
        """Execute raises MayaUnavailableError when connection is lost during receive."""
        client = CommandPortClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            # Simulate connection reset during receive (after send succeeds)
            mock_socket.recv.side_effect = ConnectionResetError()

            with pytest.raises(MayaUnavailableError) as exc_info:
                client.execute("cmds.ls()")

            assert "during receive" in exc_info.value.message
            assert not client.is_connected()

    def test_execute_reconnect_on_send_failure(self) -> None:
        """Execute reconnects and retries on send-phase failure."""
        client = CommandPortClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket_first = MagicMock()
            mock_socket_retry = MagicMock()
            mock_socket_class.side_effect = [
                mock_socket_first,
                mock_socket_retry,
            ]

            client.connect()

            # First send fails (connection dropped)
            mock_socket_first.sendall.side_effect = BrokenPipeError("Broken pipe")
            # Retry socket works
            mock_socket_retry.recv.side_effect = [b'{"ok": true}', TimeoutError()]

            result = client.execute("cmds.ls()")

            assert result == '{"ok": true}'
            # First socket sendall was called, then failed
            mock_socket_first.sendall.assert_called_once()
            # Retry socket sendall was called successfully
            mock_socket_retry.sendall.assert_called_once()

    def test_execute_no_retry_on_receive_failure(self) -> None:
        """Execute does NOT retry on receive-phase failure."""
        client = CommandPortClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            # Send succeeds but receive fails
            mock_socket.recv.side_effect = ConnectionResetError("Connection reset")

            with pytest.raises(MayaUnavailableError) as exc_info:
                client.execute("cmds.ls()")

            assert "during receive" in exc_info.value.message

    def test_execute_no_retry_on_timeout(self) -> None:
        """Execute does NOT retry on timeout."""
        client = CommandPortClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            mock_socket.sendall.side_effect = TimeoutError()

            with pytest.raises(MayaTimeoutError):
                client.execute("cmds.ls()")

    def test_execute_reconnect_fails_raises_original(self) -> None:
        """When reconnect also fails, raises MayaUnavailableError."""
        client = CommandPortClient(max_retries=1, retry_base_delay=0.01)

        with patch("socket.socket") as mock_socket_class:
            mock_socket_first = MagicMock()
            mock_socket_retry = MagicMock()
            mock_socket_retry.connect.side_effect = ConnectionRefusedError()
            mock_socket_class.side_effect = [
                mock_socket_first,
                mock_socket_retry,
            ]

            client.connect()

            # Send fails
            mock_socket_first.sendall.side_effect = BrokenPipeError("Broken pipe")

            with pytest.raises(MayaUnavailableError) as exc_info:
                client.execute("cmds.ls()")

            assert "during send" in exc_info.value.message

    def test_concurrent_execute_serializes_send_recv(self) -> None:
        """Concurrent execute calls do not interleave socket send/recv."""
        client = CommandPortClient(command_timeout=1.0)
        fake_socket = BlockingCommandSocket()
        results: dict[str, str] = {}
        errors: list[BaseException] = []

        def execute(name: str) -> None:
            try:
                results[name] = client.execute(f"print('{name}')")
            except BaseException as exc:  # pragma: no cover - asserted below
                errors.append(exc)

        with patch("socket.socket", return_value=fake_socket):
            client.connect()

            first_thread = threading.Thread(target=execute, args=("first",))
            second_thread = threading.Thread(target=execute, args=("second",))

            first_thread.start()
            assert fake_socket.first_recv_started.wait(timeout=1.0)

            second_thread.start()
            assert not fake_socket.second_send_started.wait(timeout=0.1)

            fake_socket.release_first_recv.set()
            first_thread.join(timeout=1.0)
            second_thread.join(timeout=1.0)

        assert not first_thread.is_alive()
        assert not second_thread.is_alive()
        assert errors == []
        assert results == {"first": "first", "second": "second"}
        assert fake_socket.send_order == ["first", "second"]

    @pytest.mark.parametrize("operation", ["disconnect", "reconfigure"])
    def test_lifecycle_mutation_waits_for_execute(self, operation: str) -> None:
        """Disconnect and reconfigure cannot mutate socket state mid-execute."""
        client = CommandPortClient(command_timeout=1.0)
        fake_socket = BlockingCommandSocket()
        results: dict[str, str | bool | None] = {}
        errors: list[BaseException] = []
        mutation_started = threading.Event()

        def execute() -> None:
            try:
                results["execute"] = client.execute("print('first')")
            except BaseException as exc:  # pragma: no cover - asserted below
                errors.append(exc)

        def mutate_lifecycle() -> None:
            mutation_started.set()
            try:
                if operation == "disconnect":
                    results["mutation"] = client.disconnect()
                else:
                    client.reconfigure(port=7002)
                    results["mutation"] = None
            except BaseException as exc:  # pragma: no cover - asserted below
                errors.append(exc)

        with patch("socket.socket", return_value=fake_socket):
            client.connect()

            execute_thread = threading.Thread(target=execute)
            mutation_thread = threading.Thread(target=mutate_lifecycle)

            execute_thread.start()
            assert fake_socket.first_recv_started.wait(timeout=1.0)

            mutation_thread.start()
            assert mutation_started.wait(timeout=1.0)
            assert not fake_socket.close_started.wait(timeout=0.1)
            assert client.config.port == 7001

            fake_socket.release_first_recv.set()
            execute_thread.join(timeout=1.0)
            mutation_thread.join(timeout=1.0)

        assert not execute_thread.is_alive()
        assert not mutation_thread.is_alive()
        assert errors == []
        assert results["execute"] == "first"
        assert fake_socket.close_started.is_set()
        if operation == "disconnect":
            assert results["mutation"] is True
        else:
            assert results["mutation"] is None
            assert client.config.port == 7002


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
