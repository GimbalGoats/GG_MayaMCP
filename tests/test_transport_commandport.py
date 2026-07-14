"""Tests for the commandPort transport layer.

These tests verify the CommandPortClient's behavior including:
- Connection handling
- Retry logic with exponential backoff
- Timeout handling
- Error translation
- State management
"""

from __future__ import annotations

import base64
import json
import re
import threading
from unittest.mock import MagicMock, patch

import pytest

import maya_mcp.transport.commandport as transport_module
from maya_mcp.errors import MayaCommandError, MayaTimeoutError, MayaUnavailableError
from maya_mcp.transport.commandport import (
    HELPER_VERSION,
    CommandPortClient,
    _bootstrap_expression,
    _call_expression,
    _find_envelopes,
)
from maya_mcp.types import ConnectionConfig, ConnectionStatus

_CALL_PATTERN = re.compile(r"_mcp_exec\('([A-Za-z0-9+/=]*)'\)")


def decode_call(data: bytes) -> str | None:
    """Recover the payload from a _mcp_exec(...) call, or None if not a call."""
    match = _CALL_PATTERN.search(data.decode("utf-8"))
    if match is None:
        return None
    return base64.b64decode(match.group(1)).decode("utf-8")


def envelope_bytes(
    stdout: str = "",
    *,
    ok: bool = True,
    error: str | None = None,
    error_type: str | None = None,
) -> bytes:
    """Build a wire-format response the way the Maya-side helper would."""
    payload = json.dumps(
        {
            "v": HELPER_VERSION,
            "ok": ok,
            "stdout": stdout,
            "error": error,
            "error_type": error_type,
            "traceback": "",
        }
    )
    return f"{payload}\n\x00".encode()


class BlockingCommandSocket:
    """Socket fake that can pause the first command while tests race callers.

    Speaks the helper protocol: it decodes the base64 payload out of the
    _mcp_exec(...) call expression and answers with a matching envelope.
    """

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
        payload = decode_call(data) or ""
        command_name = "second" if "second" in payload else "first"
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

        return envelope_bytes(f"{command_name}\n")

    def close(self) -> None:
        """Record close attempts."""
        self.close_started.set()


class ScriptedSocket:
    """Socket fake that replays a fixed list of raw responses, one per send."""

    def __init__(self, responses: list[bytes]) -> None:
        self.responses = list(responses)
        self.sent: list[str] = []
        self._pending: bytes | None = None

    def setsockopt(self, *_args: object) -> None:
        """Accept socket keepalive options."""

    def settimeout(self, _timeout: float) -> None:
        """Accept timeout changes."""

    def connect(self, _address: tuple[str, int]) -> None:
        """Pretend to connect successfully."""

    def sendall(self, data: bytes) -> None:
        """Record the sent expression and queue the next scripted response."""
        self.sent.append(data.decode("utf-8"))
        self._pending = self.responses.pop(0) if self.responses else b""

    def recv(self, _buffer_size: int) -> bytes:
        """Return the queued response once, then simulate read completion."""
        if self._pending is None:
            raise TimeoutError()
        chunk, self._pending = self._pending, None
        return chunk

    def close(self) -> None:
        """Accept close."""


class TestFindEnvelopes:
    """Tests for extracting helper envelopes from a raw commandPort response."""

    def test_extracts_single_envelope(self) -> None:
        """A normal echo-off response yields exactly one envelope."""
        raw = envelope_bytes('{"success": true}\n').decode("utf-8")

        envelopes = _find_envelopes(raw)

        assert len(envelopes) == 1
        assert envelopes[0]["ok"] is True
        assert envelopes[0]["stdout"] == '{"success": true}\n'

    def test_ignores_surrounding_maya_noise(self) -> None:
        """Plugin warnings sharing the stream do not hide the envelope."""
        raw = (
            "Arnold renderer not loaded.\n"
            "The MtoA plug-in needed for this scene is not loaded.\n"
            "\x00" + envelope_bytes("ok\n").decode("utf-8")
        )

        envelopes = _find_envelopes(raw)

        assert len(envelopes) == 1
        assert envelopes[0]["stdout"] == "ok\n"

    def test_reports_each_echoed_copy(self) -> None:
        """An echoOutput=True port duplicates the value; both copies are counted."""
        single = envelope_bytes("dup\n").decode("utf-8")

        envelopes = _find_envelopes(single + single)

        assert len(envelopes) == 2

    def test_ignores_unrelated_json(self) -> None:
        """JSON that is not an envelope is not mistaken for one."""
        raw = '{"success": true}\n\x00[1, 2, 3]\n\x00None\n\x00'

        assert _find_envelopes(raw) == []

    def test_handles_empty_response(self) -> None:
        """An empty response yields no envelopes rather than raising."""
        assert _find_envelopes("") == []


class TestProtocolEncoding:
    """Tests for the expressions sent over the wire."""

    def test_call_expression_is_a_single_expression(self) -> None:
        """The call carries the command as base64, with no newlines to split on."""
        expression = _call_expression("print('hi')\nprint('there')\n")

        assert "\n" not in expression
        assert decode_call(expression.encode("utf-8")) == "print('hi')\nprint('there')\n"

    def test_call_expression_survives_quotes_and_unicode(self) -> None:
        """Base64 keeps quote-heavy and non-ASCII commands intact."""
        command = "result = {'name': \"café 'x' \\\"y\\\"\", 'emoji': '\U0001f3ac'}"

        assert decode_call(_call_expression(command).encode("utf-8")) == command

    def test_bootstrap_expression_is_a_single_expression(self) -> None:
        """The bootstrap must also be one line, or commandPort would exec it."""
        assert "\n" not in _bootstrap_expression()


class TestGlobalClient:
    """Tests for module-level client singleton behavior."""

    def test_get_client_initializes_singleton_once_across_threads(self) -> None:
        """Concurrent first access creates only one shared client instance."""
        original_client = transport_module._client
        original_client_class = transport_module.CommandPortClient
        transport_module._client = None
        instances: list[object] = []
        constructor_entered = threading.Event()
        release_constructor = threading.Event()

        class SlowClient:
            def __init__(self) -> None:
                instances.append(self)
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

    def test_execute_returns_captured_stdout(self) -> None:
        """Execute returns what the command printed, unwrapped from the envelope."""
        client = CommandPortClient()
        fake_socket = ScriptedSocket(
            [
                f"{HELPER_VERSION}\n\x00".encode(),
                envelope_bytes("['pCube1', 'pSphere1']\n"),
            ]
        )

        with patch("socket.socket", return_value=fake_socket):
            client.connect()
            result = client.execute("print(cmds.ls(selection=True))")

        assert result == "['pCube1', 'pSphere1']"

    def test_execute_sends_command_as_single_expression(self) -> None:
        """The command reaches Maya base64-wrapped, never as raw multi-line code."""
        client = CommandPortClient()
        command = "import json\nprint(json.dumps({'a': 1}))\n"
        fake_socket = ScriptedSocket(
            [
                f"{HELPER_VERSION}\n\x00".encode(),
                envelope_bytes('{"a": 1}\n'),
            ]
        )

        with patch("socket.socket", return_value=fake_socket):
            client.connect()
            client.execute(command)

        call = fake_socket.sent[-1]
        assert command not in call
        assert "\n" not in call.strip()
        assert decode_call(call.encode("utf-8")) == command

    def test_execute_auto_connects(self) -> None:
        """Execute connects automatically if not connected."""
        client = CommandPortClient()
        fake_socket = ScriptedSocket(
            [
                f"{HELPER_VERSION}\n\x00".encode(),
                envelope_bytes("result\n"),
            ]
        )

        with patch("socket.socket", return_value=fake_socket):
            result = client.execute("print('result')")

            assert result == "result"
            assert client.is_connected()

    def test_execute_installs_helper_when_missing(self) -> None:
        """A Maya without the helper gets it installed before the command runs."""
        client = CommandPortClient()
        fake_socket = ScriptedSocket(
            [
                b"None\n\x00",  # probe: helper absent
                b"None\n\x00",  # bootstrap acknowledged
                envelope_bytes("done\n"),
            ]
        )

        with patch("socket.socket", return_value=fake_socket):
            client.connect()
            result = client.execute("print('done')")

        assert result == "done"
        assert len(fake_socket.sent) == 3
        assert fake_socket.sent[1].strip() == _bootstrap_expression()

    def test_execute_skips_bootstrap_when_helper_present(self) -> None:
        """A helper already in Maya is not reinstalled."""
        client = CommandPortClient()
        fake_socket = ScriptedSocket(
            [
                f"{HELPER_VERSION}\n\x00".encode(),
                envelope_bytes("done\n"),
            ]
        )

        with patch("socket.socket", return_value=fake_socket):
            client.connect()
            client.execute("print('done')")

        assert len(fake_socket.sent) == 2
        assert all(not sent.strip().startswith("exec(") for sent in fake_socket.sent)

    def test_execute_probes_helper_only_once_per_connection(self) -> None:
        """The version probe is not repeated for every command."""
        client = CommandPortClient()
        fake_socket = ScriptedSocket(
            [
                f"{HELPER_VERSION}\n\x00".encode(),
                envelope_bytes("one\n"),
                envelope_bytes("two\n"),
            ]
        )

        with patch("socket.socket", return_value=fake_socket):
            client.connect()
            assert client.execute("print('one')") == "one"
            assert client.execute("print('two')") == "two"

        assert len(fake_socket.sent) == 3

    def test_execute_reinstalls_helper_after_reconnect(self) -> None:
        """A dropped socket forces a fresh probe, in case Maya restarted."""
        client = CommandPortClient()
        fake_socket = ScriptedSocket(
            [
                f"{HELPER_VERSION}\n\x00".encode(),
                envelope_bytes("one\n"),
                f"{HELPER_VERSION}\n\x00".encode(),
                envelope_bytes("two\n"),
            ]
        )

        with patch("socket.socket", return_value=fake_socket):
            client.connect()
            client.execute("print('one')")
            client.disconnect()
            client.connect()
            client.execute("print('two')")

        assert len(fake_socket.sent) == 4

    def test_execute_raises_when_command_raises_in_maya(self) -> None:
        """An exception inside Maya surfaces as MayaCommandError, not empty output."""
        client = CommandPortClient()
        fake_socket = ScriptedSocket(
            [
                f"{HELPER_VERSION}\n\x00".encode(),
                envelope_bytes(
                    "",
                    ok=False,
                    error="division by zero",
                    error_type="ZeroDivisionError",
                ),
            ]
        )

        with patch("socket.socket", return_value=fake_socket):
            client.connect()

            with pytest.raises(MayaCommandError) as exc_info:
                client.execute("print(1 / 0)")

        assert exc_info.value.maya_error == "division by zero"
        assert "ZeroDivisionError" in exc_info.value.message

    def test_execute_detects_echo_output_port(self) -> None:
        """A duplicated envelope means echoOutput=True; say so explicitly."""
        client = CommandPortClient()
        duplicated = envelope_bytes("dup\n") + envelope_bytes("dup\n")
        fake_socket = ScriptedSocket([f"{HELPER_VERSION}\n\x00".encode(), duplicated])

        with patch("socket.socket", return_value=fake_socket):
            client.connect()

            with pytest.raises(MayaCommandError) as exc_info:
                client.execute("print('dup')")

        assert "echoOutput=True" in exc_info.value.message
        assert "echoOutput=False" in exc_info.value.message

    def test_execute_raises_on_unparseable_response(self) -> None:
        """A response with no envelope is reported rather than returned as empty."""
        client = CommandPortClient()
        fake_socket = ScriptedSocket([f"{HELPER_VERSION}\n\x00".encode(), b"None\n\x00"])

        with patch("socket.socket", return_value=fake_socket):
            client.connect()

            with pytest.raises(MayaCommandError) as exc_info:
                client.execute("print('x')")

        assert "no usable response" in exc_info.value.message

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
            mock_socket_retry = ScriptedSocket(
                [
                    f"{HELPER_VERSION}\n\x00".encode(),
                    envelope_bytes('{"ok": true}\n'),
                ]
            )
            mock_socket_class.side_effect = [
                mock_socket_first,
                mock_socket_retry,
            ]

            client.connect()

            # First send fails (connection dropped)
            mock_socket_first.sendall.side_effect = BrokenPipeError("Broken pipe")

            result = client.execute("print('{\"ok\": true}')")

            assert result == '{"ok": true}'
            # First socket sendall was called, then failed
            mock_socket_first.sendall.assert_called_once()
            # Retry socket carried the probe and then the command
            assert len(mock_socket_retry.sent) == 2

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
            # Skip the helper probe so this exercises serialization only.
            client._bootstrapped = True

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
            # Skip the helper probe so this exercises locking only.
            client._bootstrapped = True

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
