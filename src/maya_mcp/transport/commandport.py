"""Maya commandPort client.

This module provides the CommandPortClient class for communicating with
Maya via its commandPort socket interface.

The client handles:
    - TCP socket connection management
    - Command encoding (UTF-8)
    - Response parsing
    - Timeout enforcement
    - Retry with exponential backoff
    - Error translation to typed exceptions

The port must be opened with ``echoOutput=False``::

    cmds.commandPort(name=":7001", sourceType="python", echoOutput=False)

Commands do not travel over the wire as-is. Maya's commandPort only returns a
value when what it receives is a single bare expression, so each command is
base64-encoded and handed to a helper installed in Maya's ``__main__``, which
runs it, captures its stdout, and returns a JSON envelope. Callers see none of
this: ``execute()`` returns the command's stdout, so a command ending in
``print(json.dumps(result))`` still gets that JSON back. See
``_MAYA_HELPER_SOURCE`` for why this indirection is necessary.

Example:
    Basic usage::

        from maya_mcp.transport import CommandPortClient

        client = CommandPortClient()
        client.connect()
        result = client.execute("import json; print(json.dumps(cmds.ls()))")
        client.disconnect()

Note:
    This module does NOT import any Maya modules. All communication
    happens via TCP socket.
"""

from __future__ import annotations

import base64
import contextlib
import json
import logging
import socket
import threading
import time

from maya_mcp.errors import (
    MayaCommandError,
    MayaTimeoutError,
    MayaUnavailableError,
)
from maya_mcp.types import (
    ClientState,
    ConnectionConfig,
    ConnectionStatus,
    HealthCheckResult,
)

logger = logging.getLogger(__name__)

# Buffer size for socket receive
BUFFER_SIZE = 65536

# Module-level client instance for singleton pattern
_client: CommandPortClient | None = None
_client_lock = threading.Lock()

# Protocol version of the Maya-side helper. Bump when _MAYA_HELPER_SOURCE
# changes shape so a stale helper left in Maya by an older server is replaced.
HELPER_VERSION = 1

# Maya-side helper, installed into Maya's __main__ namespace once per connection.
#
# Why this exists: Maya's commandPort only returns a value when the payload it
# receives is a single bare expression it can eval. A multi-statement payload is
# exec'd and always answers "None", so a command ending in print(...) sends
# nothing back on a port opened with echoOutput=False. Commands also run in the
# maya.app.general.CommandPort namespace with a fresh locals dict each time, so
# nothing assigned at top level survives -- but __main__ does persist, and a
# function stashed there is reachable from a single expression.
#
# So: install this helper once, then send every command as one expression,
# _mcp_exec("<base64>"), which returns a JSON envelope as its value.
_MAYA_HELPER_SOURCE = f'''
import base64 as _mcp_base64
import contextlib as _mcp_contextlib
import io as _mcp_io
import json as _mcp_json
import traceback as _mcp_traceback

_MCP_HELPER_VERSION = {HELPER_VERSION}


def _mcp_envelope(ok, stdout, error=None, error_type=None, tb=""):
    return _mcp_json.dumps({{
        "v": _MCP_HELPER_VERSION,
        "ok": ok,
        "stdout": stdout,
        "error": error,
        "error_type": error_type,
        "traceback": tb,
    }})


def _mcp_exec(payload_b64):
    """Run a base64-encoded payload, return a JSON envelope. Never raises."""
    try:
        source = _mcp_base64.b64decode(payload_b64).decode("utf-8")
    except Exception as exc:
        return _mcp_envelope(
            False, "", "Could not decode payload: %s" % exc, type(exc).__name__
        )

    namespace = {{"__name__": "__maya_mcp__"}}
    buffer = _mcp_io.StringIO()
    try:
        with _mcp_contextlib.redirect_stdout(buffer):
            exec(source, namespace)
    except Exception as exc:
        return _mcp_envelope(
            False,
            buffer.getvalue(),
            str(exc),
            type(exc).__name__,
            _mcp_traceback.format_exc(),
        )
    return _mcp_envelope(True, buffer.getvalue())
'''


def _bootstrap_expression() -> str:
    """Build the single expression that installs the helper into Maya's __main__."""
    encoded = base64.b64encode(_MAYA_HELPER_SOURCE.encode("utf-8")).decode("ascii")
    return (
        f"exec(__import__('base64').b64decode('{encoded}').decode('utf-8'),"
        " __import__('__main__').__dict__)"
    )


def _call_expression(command: str) -> str:
    """Build the single expression that runs ``command`` through the helper."""
    encoded = base64.b64encode(command.encode("utf-8")).decode("ascii")
    return f"__import__('__main__')._mcp_exec('{encoded}')"


def _response_parts(raw_response: str) -> list[str]:
    """Split a raw commandPort response into stripped, non-empty parts."""
    parts = raw_response.replace("\x00", "\n").split("\n")
    return [part.strip() for part in parts if part.strip()]


def _find_envelopes(raw_response: str) -> list[dict[str, object]]:
    """Extract every helper envelope present in a raw commandPort response.

    A port opened with echoOutput=True echoes the value back more than once, so
    the count matters: it is how an echo-enabled port is detected.

    Args:
        raw_response: Raw response string from Maya commandPort.

    Returns:
        Every decoded envelope found, in wire order.
    """
    envelopes = []
    for part in _response_parts(raw_response):
        if not part.startswith("{"):
            continue
        try:
            decoded = json.loads(part)
        except ValueError:
            continue
        if isinstance(decoded, dict) and "ok" in decoded and "stdout" in decoded:
            envelopes.append(decoded)
    return envelopes


def get_client() -> CommandPortClient:
    """Get the global CommandPortClient instance.

    Returns a singleton CommandPortClient instance, creating it if necessary.
    This is the recommended way to get a client for use in MCP tools.

    Returns:
        The global CommandPortClient instance.

    Example:
        >>> client = get_client()
        >>> client.execute("cmds.ls()")
    """
    global _client
    with _client_lock:
        if _client is None:
            _client = CommandPortClient()
        return _client


class CommandPortClient:
    """Client for communicating with Maya via commandPort.

    This client manages socket connections to Maya's commandPort,
    handles timeouts and retries, and translates errors to typed
    exceptions.

    The client is designed for Level 1 resilience:
        - Detects when Maya is unavailable
        - Returns typed errors
        - Automatically reconnects on next call when Maya restarts

    Attributes:
        config: Connection configuration.
        state: Current client state.

    Example:
        Basic usage::

            client = CommandPortClient(host="localhost", port=7001)
            try:
                client.connect()
                result = client.execute("cmds.ls()")
                print(result)
            finally:
                client.disconnect()

        With custom timeouts::

            client = CommandPortClient(
                connect_timeout=10.0,
                command_timeout=60.0,
                max_retries=5,
            )
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 7001,
        connect_timeout: float = 5.0,
        command_timeout: float = 30.0,
        max_retries: int = 3,
        retry_base_delay: float = 0.5,
    ) -> None:
        """Initialize the CommandPortClient.

        Args:
            host: Target host. Only "localhost" or "127.0.0.1" are supported.
            port: Target port number (1-65535).
            connect_timeout: Connection timeout in seconds.
            command_timeout: Command execution timeout in seconds.
            max_retries: Maximum number of connection retry attempts.
            retry_base_delay: Base delay for exponential backoff (seconds).

        Raises:
            ValueError: If configuration is invalid.
        """
        self.config = ConnectionConfig(
            host=host,
            port=port,
            connect_timeout=connect_timeout,
            command_timeout=command_timeout,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
        )
        self.state = ClientState(config=self.config)
        self._socket: socket.socket | None = None
        self._lock = threading.RLock()
        self._bootstrapped = False

    def connect(self) -> bool:
        """Establish connection to Maya commandPort.

        Attempts to connect to Maya's commandPort with retry logic.
        Uses exponential backoff between retry attempts.

        Returns:
            True if connection was successful.

        Raises:
            MayaUnavailableError: If connection fails after all retries.

        Example:
            >>> client = CommandPortClient()
            >>> if client.connect():
            ...     print("Connected to Maya")
        """
        with self._lock:
            if self._socket is not None:
                # Already connected
                return True

            self.state.status = ConnectionStatus.RECONNECTING
            last_error: str | None = None
            logger.info("Connecting to Maya at %s:%d", self.config.host, self.config.port)

            for attempt in range(self.config.max_retries):
                try:
                    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    self._socket.settimeout(self.config.connect_timeout)
                    self._socket.connect((self.config.host, self.config.port))

                    # Connection successful
                    self.state.status = ConnectionStatus.OK
                    self.state.last_error = None
                    self.state.update_contact()
                    logger.info("Connected to Maya at %s:%d", self.config.host, self.config.port)
                    return True

                except TimeoutError:
                    last_error = f"Connection timed out after {self.config.connect_timeout}s"
                    self._cleanup_socket()
                except ConnectionRefusedError:
                    last_error = "Connection refused - is Maya running with commandPort open?"
                    self._cleanup_socket()
                except OSError as e:
                    last_error = f"Socket error: {e}"
                    self._cleanup_socket()

                # Exponential backoff before retry
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_base_delay * (2**attempt)
                    logger.debug(
                        "Connection attempt %d/%d failed: %s. Retrying in %.1fs",
                        attempt + 1,
                        self.config.max_retries,
                        last_error,
                        delay,
                    )
                    time.sleep(delay)

            # All retries exhausted
            self.state.status = ConnectionStatus.OFFLINE
            self.state.last_error = last_error
            logger.warning(
                "Failed to connect to Maya after %d attempts: %s",
                self.config.max_retries,
                last_error,
            )

            raise MayaUnavailableError(
                message=f"Cannot connect to Maya commandPort at {self.config.host}:{self.config.port}",
                host=self.config.host,
                port=self.config.port,
                attempts=self.config.max_retries,
                last_error=last_error,
            )

    def disconnect(self) -> bool:
        """Close the connection to Maya.

        Returns:
            True if disconnection was successful, False if wasn't connected.

        Example:
            >>> client.disconnect()
            True
        """
        with self._lock:
            was_connected = self._socket is not None
            self._cleanup_socket()
            self.state.status = ConnectionStatus.OFFLINE
            if was_connected:
                logger.info("Disconnected from Maya")
            return was_connected

    def execute(self, command: str) -> str:
        """Execute a Python command in Maya and return whatever it printed.

        The command is run through the Maya-side helper (installed on first use)
        and its stdout is captured and returned, so a command ending in
        ``print(json.dumps(result))`` gets that JSON back exactly as before.

        Args:
            command: Python code to execute in Maya.

        Returns:
            Whatever the command wrote to stdout, stripped.

        Raises:
            MayaUnavailableError: Cannot connect to Maya.
            MayaCommandError: Command raised inside Maya, or the port speaks a
                protocol this client cannot use (e.g. opened with echoOutput=True).
            MayaTimeoutError: Command timed out.

        Example:
            >>> result = client.execute("import json; print(json.dumps(cmds.ls()))")
            >>> print(result)
            ["pCube1", "pSphere1"]
        """
        with self._lock:
            self._ensure_bootstrapped()
            return self._run_command(command)

    def _run_command(self, command: str) -> str:
        """Send one command through the helper and unwrap its envelope."""
        raw = self._send_expression(_call_expression(command), allow_retry=True)
        envelope = self._require_envelope(raw, command=command)

        if not envelope.get("ok"):
            maya_error = str(envelope.get("error") or "Unknown Maya error")
            error_type = str(envelope.get("error_type") or "Exception")
            logger.error("Command raised in Maya: %s: %s", error_type, maya_error)
            logger.debug("Maya traceback:\n%s", envelope.get("traceback") or "")
            raise MayaCommandError(
                message=f"Command failed in Maya: {error_type}: {maya_error}",
                command=command,
                maya_error=maya_error,
            )

        response = str(envelope.get("stdout") or "").strip()
        self.state.update_contact()
        self.state.last_error = None
        logger.debug("Command completed (%d chars response)", len(response))
        return response

    def _require_envelope(self, raw_response: str, *, command: str) -> dict[str, object]:
        """Pull exactly one helper envelope out of a raw response.

        More than one envelope means the port was opened with echoOutput=True:
        Maya echoes the value back alongside the return value. This client speaks
        the echo-off protocol only, so say that plainly rather than failing later
        with an unhelpful parse error.
        """
        envelopes = _find_envelopes(raw_response)

        if len(envelopes) == 1:
            return envelopes[0]

        if len(envelopes) > 1:
            port = self.config.port
            raise MayaCommandError(
                message=(
                    "Maya's commandPort appears to be open with echoOutput=True, "
                    "which this client does not support. Reopen it with "
                    "echoOutput=False:\n"
                    f"    cmds.commandPort(name=':{port}', close=True)\n"
                    f"    cmds.commandPort(name=':{port}', sourceType='python', "
                    "echoOutput=False)"
                ),
                command=command,
                maya_error=f"received {len(envelopes)} echoed responses",
            )

        preview = raw_response[:200] or "<empty>"
        raise MayaCommandError(
            message=(
                "Maya returned no usable response. The commandPort may be open "
                "with sourceType='mel' instead of 'python'."
            ),
            command=command,
            maya_error=f"unparseable response: {preview!r}",
        )

    def _ensure_bootstrapped(self) -> None:
        """Install the Maya-side helper if this connection has not verified it yet.

        The helper lives in Maya's ``__main__`` so it survives across sockets, but
        Maya may have restarted, so verify rather than assume.
        """
        if self._bootstrapped:
            return

        probe = self._send_expression(
            "__import__('__main__').__dict__.get('_MCP_HELPER_VERSION')",
            allow_retry=True,
        )
        installed = str(HELPER_VERSION) in _response_parts(probe)

        if not installed:
            logger.info("Installing Maya-side helper (v%d)", HELPER_VERSION)
            self._send_expression(_bootstrap_expression(), allow_retry=True)

        self._bootstrapped = True

    def _send_expression(self, expression: str, *, allow_retry: bool) -> str:
        """Send one expression and return the raw response, retrying on send failure.

        Args:
            expression: A single Python expression for Maya to eval.
            allow_retry: If True, reconnect and retry once on send-phase errors.

        Returns:
            Raw response string from Maya.
        """
        command = expression
        # Ensure connected
        if self._socket is None:
            self.connect()

        if self._socket is None:
            raise MayaUnavailableError(
                message="Not connected to Maya",
                host=self.config.host,
                port=self.config.port,
                attempts=0,
            )

        send_completed = False
        try:
            # Set command timeout
            self._socket.settimeout(self.config.command_timeout)

            # Prepare command
            command = command.strip()
            logger.debug("Executing command (%d chars)", len(command))

            # Maya commandPort requires a newline to execute the command
            if not command.endswith("\n"):
                command += "\n"

            command_bytes = command.encode("utf-8")
            self._socket.sendall(command_bytes)
            send_completed = True

            # Receive response — use command_timeout for the first chunk (Maya
            # may take a while to process) and a short follow-up timeout for
            # subsequent chunks once data starts flowing.
            response_parts: list[bytes] = []
            self._socket.settimeout(self.config.command_timeout)
            try:
                first_chunk = self._socket.recv(BUFFER_SIZE)
                if first_chunk:
                    response_parts.append(first_chunk)
                    # Data started flowing — switch to a short timeout to
                    # collect any remaining fragments without a long wait.
                    self._socket.settimeout(0.05)
                    while True:
                        try:
                            chunk = self._socket.recv(BUFFER_SIZE)
                            if not chunk:
                                break
                            response_parts.append(chunk)
                        except TimeoutError:
                            break
            except TimeoutError:
                # No response at all within command_timeout
                pass

            raw_response = b"".join(response_parts).decode("utf-8").strip()

            self.state.update_contact()
            self.state.last_error = None
            return raw_response

        except TimeoutError as exc:
            self.state.last_error = f"Command timed out after {self.config.command_timeout}s"
            self._handle_socket_error()
            logger.error("Command timed out after %.1fs", self.config.command_timeout)
            raise MayaTimeoutError(
                message="Command execution timed out",
                timeout_seconds=self.config.command_timeout,
                operation="execute",
            ) from exc

        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            phase = "receive" if send_completed else "send"
            error_msg = f"Connection lost during {phase}: {e}"
            self.state.last_error = error_msg
            self._handle_socket_error()

            # Only retry on send-phase errors — the command was never delivered
            if not send_completed and allow_retry:
                logger.warning("Connection lost during send, reconnecting: %s", e)
                try:
                    self.connect()
                    return self._send_expression(expression, allow_retry=False)
                except (MayaUnavailableError, OSError):
                    pass  # Fall through to raise original error

            logger.error("Connection lost during %s: %s", phase, e)
            raise MayaUnavailableError(
                message=f"Lost connection to Maya during {phase}",
                host=self.config.host,
                port=self.config.port,
                attempts=0,
                last_error=error_msg,
            ) from e

    def is_connected(self) -> bool:
        """Check if currently connected to Maya.

        Returns:
            True if socket is connected.

        Example:
            >>> if client.is_connected():
            ...     print("Connected")
        """
        with self._lock:
            return self._socket is not None and self.state.status == ConnectionStatus.OK

    def get_status(self) -> ConnectionStatus:
        """Get the current connection status.

        Returns:
            Current ConnectionStatus enum value.

        Example:
            >>> status = client.get_status()
            >>> if status == ConnectionStatus.OK:
            ...     print("Connected and healthy")
        """
        with self._lock:
            return self.state.status

    def get_health(self) -> HealthCheckResult:
        """Get detailed health information.

        Returns:
            HealthCheckResult with current connection health details.

        Example:
            >>> health = client.get_health()
            >>> print(f"Status: {health.status}")
        """
        with self._lock:
            return HealthCheckResult(
                status=self.state.status.value,
                last_error=self.state.last_error,
                last_contact=self.state.get_last_contact_iso(),
                host=self.config.host,
                port=self.config.port,
            )

    def reconfigure(
        self,
        host: str | None = None,
        port: int | None = None,
    ) -> None:
        """Update connection configuration.

        Disconnects if currently connected and updates the configuration.

        Args:
            host: New target host (optional).
            port: New target port (optional).

        Raises:
            ValueError: If new configuration is invalid.

        Example:
            >>> client.reconfigure(port=7002)
        """
        with self._lock:
            # Disconnect first
            self.disconnect()

            # Update config
            new_host = host if host is not None else self.config.host
            new_port = port if port is not None else self.config.port

            self.config = ConnectionConfig(
                host=new_host,
                port=new_port,
                connect_timeout=self.config.connect_timeout,
                command_timeout=self.config.command_timeout,
                max_retries=self.config.max_retries,
                retry_base_delay=self.config.retry_base_delay,
            )
            self.state.config = self.config

    def _cleanup_socket(self) -> None:
        """Clean up the socket connection."""
        if self._socket is not None:
            with contextlib.suppress(OSError):
                self._socket.close()
            self._socket = None
        # The helper lives in Maya's __main__, which outlives a dropped socket,
        # but Maya may have restarted underneath us. Re-verify on next connect.
        self._bootstrapped = False

    def _handle_socket_error(self) -> None:
        """Handle a socket error by cleaning up and updating state."""
        self._cleanup_socket()
        self.state.status = ConnectionStatus.OFFLINE
