"""Tests for the commandPort transport layer.

These tests verify the CommandPortClient's behavior including:
- Connection handling
- Retry logic with exponential backoff
- Timeout handling
- Error translation
- State management
"""

from __future__ import annotations

import builtins
import json
import subprocess
import sys
import threading
import types
from unittest.mock import MagicMock, call, patch

import pytest

import maya_mcp.transport.commandport as transport_module
from maya_mcp.commandport_protocol import MAYA_2024_HANDLER_NAME, MAYA_2024_PORTS_NAME
from maya_mcp.errors import MayaCommandError, MayaTimeoutError, MayaUnavailableError
from maya_mcp.transport.commandport import CommandPortClient, _parse_maya_response
from maya_mcp.types import ConnectionConfig, ConnectionStatus


def test_transport_import_does_not_load_maya_panel_package() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import maya_mcp.transport.commandport; "
            "assert 'maya_mcp.maya_panel' not in sys.modules",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


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


class TestGlobalClient:
    """Tests for module-level client singleton behavior."""

    def test_get_client_initializes_singleton_once_across_threads(self) -> None:
        """Concurrent first access creates only one shared client instance."""
        original_client = transport_module._client
        original_client_class = transport_module.CommandPortClient
        transport_module._client = None
        instances: list[object] = []
        constructor_kwargs: list[dict[str, object]] = []
        constructor_entered = threading.Event()
        release_constructor = threading.Event()

        class SlowClient:
            def __init__(self, **kwargs: object) -> None:
                instances.append(self)
                constructor_kwargs.append(kwargs)
                constructor_entered.set()
                assert release_constructor.wait(timeout=2.0)

        try:
            transport_module.CommandPortClient = SlowClient  # type: ignore[assignment]
            results: list[object] = []
            errors: list[BaseException] = []

            def get_shared_client() -> None:
                try:
                    results.append(transport_module.get_client())
                except BaseException as exc:  # pragma: no cover - asserted below
                    errors.append(exc)

            first_thread = threading.Thread(target=get_shared_client)
            second_thread = threading.Thread(target=get_shared_client)

            first_thread.start()
            assert constructor_entered.wait(timeout=1.0)
            second_thread.start()
            release_constructor.set()

            first_thread.join(timeout=1.0)
            second_thread.join(timeout=1.0)

            assert not first_thread.is_alive()
            assert not second_thread.is_alive()
            assert errors == []
            assert len(instances) == 1
            assert results == [instances[0], instances[0]]
            assert constructor_kwargs == [{"auto_detect_maya_compatibility": True}]
        finally:
            release_constructor.set()
            transport_module.CommandPortClient = original_client_class
            transport_module._client = original_client


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
        assert client._auto_detect_maya_compatibility is True

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
        client = CommandPortClient(auto_detect_maya_compatibility=False)

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
        client = CommandPortClient(auto_detect_maya_compatibility=False)

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
        client = CommandPortClient(
            max_retries=3,
            retry_base_delay=0.01,
            auto_detect_maya_compatibility=False,
        )

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
        client = CommandPortClient(
            max_retries=2,
            retry_base_delay=0.01,
            auto_detect_maya_compatibility=False,
        )

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.connect.side_effect = TimeoutError()
            mock_socket_class.return_value = mock_socket

            with pytest.raises(MayaUnavailableError) as exc_info:
                client.connect()

            assert exc_info.value.attempts == 2
            assert "timed out" in str(exc_info.value.last_error)

    def test_auto_detection_enables_single_line_framing_only_for_maya_2024(self) -> None:
        client = CommandPortClient(port=7002, auto_detect_maya_compatibility=True)

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.recv.side_effect = [
                b'plugin output\n{"__maya_mcp_compat__":"2024:1"}\n\x00',
                TimeoutError(),
                b'{"__maya_mcp_buffer__":4097}\n\x00',
                TimeoutError(),
                b'{"__maya_mcp_response__":{"ok":true,"result":"{\\"ok\\": true}"}}\n\x00',
                TimeoutError(),
            ]
            mock_socket_class.return_value = mock_socket

            client.connect()
            result = client.execute("if True:\n    print('ok')")

        assert result == '{"ok": true}'
        sent = [item.args[0].decode("utf-8") for item in mock_socket.sendall.call_args_list]
        assert "about(majorVersion=True)" in sent[0]
        assert "callable" in sent[0]
        assert "_maya_mcp_command_port_2024" in sent[0]
        assert "_maya_mcp_command_port_2024_ports" in sent[0]
        assert "7002" in sent[0]
        assert len(sent[1]) > 4096
        assert "__maya_mcp_buffer__" in sent[1]
        assert sent[2].count("\n") == 1
        assert "_maya_mcp_command_port_2024" in sent[2]
        assert "__maya_mcp_response__" in sent[2]

        fake_cmds = types.SimpleNamespace(about=lambda **_kwargs: "2024")
        fake_maya = types.ModuleType("maya")
        fake_maya.cmds = fake_cmds  # type: ignore[attr-defined]
        with (
            patch.dict(sys.modules, {"maya": fake_maya, "maya.cmds": fake_cmds}),
            patch.object(builtins, MAYA_2024_PORTS_NAME, {7002}, create=True),
            patch.object(
                builtins,
                MAYA_2024_HANDLER_NAME,
                lambda command: {"ok": True, "result": command},
                create=True,
            ),
        ):
            probe_result = json.loads(eval(compile(sent[0], "<probe>", "eval")))
            command_result = json.loads(eval(compile(sent[2], "<command>", "eval")))

        assert probe_result == {"__maya_mcp_compat__": "2024:1"}
        assert command_result["__maya_mcp_response__"]["ok"] is True

    def test_maya_2024_stale_marker_cannot_bypass_buffer_probe(self) -> None:
        client = CommandPortClient(max_retries=1, auto_detect_maya_compatibility=True)

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.recv.side_effect = [
                b'{"__maya_mcp_compat__":"2024:1"}\n\x00',
                TimeoutError(),
                TimeoutError(),
            ]
            mock_socket_class.return_value = mock_socket

            with pytest.raises(MayaUnavailableError):
                client.connect()

        sent = [item.args[0] for item in mock_socket.sendall.call_args_list]
        assert len(sent[1]) > 4096
        assert client._socket is None

    def test_maya_2024_response_envelope_preserves_repeated_output(self) -> None:
        client = CommandPortClient(auto_detect_maya_compatibility=False)
        client._maya_2024_compatibility = True
        client._socket = MagicMock()
        client._socket.recv.side_effect = [
            b'{"__maya_mcp_response__":{"ok":true,"result":"tick\\ntick\\n"}}\n\x00',
            TimeoutError(),
        ]

        result = client.execute("print('tick')\nprint('tick')")

        assert result == "tick\ntick\n"

    def test_maya_2024_response_envelope_preserves_command_failure(self) -> None:
        client = CommandPortClient(auto_detect_maya_compatibility=False)
        client._maya_2024_compatibility = True
        mock_socket = MagicMock()
        mock_socket.recv.side_effect = [
            b'{"__maya_mcp_response__":{"ok":false,"error":"ValueError: boom"}}\n\x00',
            TimeoutError(),
        ]
        client._socket = mock_socket

        with pytest.raises(MayaCommandError, match="ValueError: boom"):
            client.execute("raise ValueError('boom')")

        assert client._socket is mock_socket

    def test_maya_2024_invalid_response_envelope_discards_socket(self) -> None:
        client = CommandPortClient(auto_detect_maya_compatibility=False)
        client._maya_2024_compatibility = True
        client._socket = MagicMock()
        client._socket.recv.side_effect = [b"invalid\n\x00", TimeoutError()]

        with pytest.raises(MayaUnavailableError):
            client.execute("print('tick')")

        assert client._socket is None
        assert client.get_status() == ConnectionStatus.OFFLINE

    def test_maya_2024_empty_response_is_a_timeout_and_discards_socket(self) -> None:
        client = CommandPortClient(auto_detect_maya_compatibility=False)
        client._maya_2024_compatibility = True
        client._socket = MagicMock()
        client._socket.recv.side_effect = TimeoutError()

        with pytest.raises(MayaTimeoutError):
            client.execute("slow_command()")

        assert client._socket is None
        assert client.get_status() == ConnectionStatus.OFFLINE

    def test_auto_detection_keeps_maya_2025_command_bytes_unchanged(self) -> None:
        client = CommandPortClient(auto_detect_maya_compatibility=True)

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.recv.side_effect = [
                b'{"__maya_mcp_compat__":"2025:0"}\n\x00',
                TimeoutError(),
                b"ok\n\x00",
                TimeoutError(),
            ]
            mock_socket_class.return_value = mock_socket

            client.connect()
            result = client.execute("print('ok')")

        assert result == "ok"
        sent = [item.args[0].decode("utf-8") for item in mock_socket.sendall.call_args_list]
        assert sent[1] == "print('ok')\n"

    def test_auto_detection_does_not_frame_without_maya_side_handler(self) -> None:
        client = CommandPortClient(auto_detect_maya_compatibility=True)

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.recv.side_effect = [
                b'{"__maya_mcp_compat__":"2024:0"}\n\x00',
                TimeoutError(),
                b"legacy\n\x00",
                TimeoutError(),
            ]
            mock_socket_class.return_value = mock_socket

            client.connect()
            result = client.execute("print('legacy')")

        assert result == "legacy"
        sent = [item.args[0].decode("utf-8") for item in mock_socket.sendall.call_args_list]
        assert sent[1] == "print('legacy')\n"

    def test_auto_detection_discards_connection_after_inconclusive_probe(self) -> None:
        client = CommandPortClient(
            connect_timeout=2.0,
            command_timeout=30.0,
            max_retries=1,
            auto_detect_maya_compatibility=True,
        )

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.recv.side_effect = TimeoutError()
            mock_socket_class.return_value = mock_socket

            with pytest.raises(MayaUnavailableError) as exc_info:
                client.connect()

        mock_socket.close.assert_called_once()
        assert client._socket is None
        assert call(client.config.connect_timeout) in mock_socket.settimeout.call_args_list
        assert call(client.config.command_timeout) not in mock_socket.settimeout.call_args_list
        mock_socket_class.assert_called_once()
        assert exc_info.value.attempts == 1

    def test_auto_detection_discards_connection_after_invalid_probe(self) -> None:
        client = CommandPortClient(max_retries=1, auto_detect_maya_compatibility=True)

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.recv.side_effect = [b"plugin output only\n\x00", TimeoutError()]
            mock_socket_class.return_value = mock_socket

            with pytest.raises(MayaUnavailableError):
                client.connect()

        mock_socket.close.assert_called_once()

    def test_auto_detection_retries_transient_probe_timeout(self) -> None:
        client = CommandPortClient(
            max_retries=2,
            retry_base_delay=0.01,
            auto_detect_maya_compatibility=True,
        )
        first_socket = MagicMock()
        first_socket.recv.side_effect = TimeoutError()
        second_socket = MagicMock()
        second_socket.recv.side_effect = [
            b'{"__maya_mcp_compat__":"2025:0"}\n\x00',
            TimeoutError(),
        ]

        with patch("socket.socket", side_effect=[first_socket, second_socket]), patch(
            "time.sleep"
        ) as sleep_mock:
            assert client.connect()

        first_socket.close.assert_called_once()
        sleep_mock.assert_called_once_with(0.01)
        assert client._socket is second_socket


class TestCommandPortClientDisconnect:
    """Tests for CommandPortClient.disconnect()."""

    def test_disconnect_when_connected(self) -> None:
        """Disconnect closes socket and updates state."""
        client = CommandPortClient(auto_detect_maya_compatibility=False)

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
        client = CommandPortClient(auto_detect_maya_compatibility=False)

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
        client = CommandPortClient(auto_detect_maya_compatibility=False)

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.recv.side_effect = [b"result", TimeoutError()]
            mock_socket_class.return_value = mock_socket

            result = client.execute("cmds.ls()")

            assert result == "result"
            assert client.is_connected()

    def test_execute_timeout(self) -> None:
        """Execute raises MayaTimeoutError on timeout."""
        client = CommandPortClient(auto_detect_maya_compatibility=False)

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
        client = CommandPortClient(auto_detect_maya_compatibility=False)

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
        client = CommandPortClient(auto_detect_maya_compatibility=False)

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
        client = CommandPortClient(auto_detect_maya_compatibility=False)

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
        client = CommandPortClient(auto_detect_maya_compatibility=False)

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            mock_socket.sendall.side_effect = TimeoutError()

            with pytest.raises(MayaTimeoutError):
                client.execute("cmds.ls()")

    def test_execute_reconnect_fails_raises_original(self) -> None:
        """When reconnect also fails, raises MayaUnavailableError."""
        client = CommandPortClient(
            max_retries=1,
            retry_base_delay=0.01,
            auto_detect_maya_compatibility=False,
        )

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
        client = CommandPortClient(
            command_timeout=1.0,
            auto_detect_maya_compatibility=False,
        )
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
        client = CommandPortClient(
            command_timeout=1.0,
            auto_detect_maya_compatibility=False,
        )
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
        client = CommandPortClient(auto_detect_maya_compatibility=False)

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
        client = CommandPortClient(auto_detect_maya_compatibility=False)

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
