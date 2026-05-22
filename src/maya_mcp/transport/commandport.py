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

Example:
    Basic usage::

        from maya_mcp.transport import CommandPortClient

        client = CommandPortClient()
        client.connect()
        result = client.execute("cmds.ls(selection=True)")
        client.disconnect()

Note:
    This module does NOT import any Maya modules. All communication
    happens via TCP socket.
"""

from __future__ import annotations

import contextlib
import inspect
import logging
import os
import socket
import threading
import time

from maya_mcp import maya_compat_server
from maya_mcp.errors import (
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
_COMPAT_PROBE_TOKEN = "__maya_mcp_response_probe__"
_COMPAT_PROBE_COMMAND = f"print({_COMPAT_PROBE_TOKEN!r})"
_COMPAT_BOOTSTRAP_DELAY_SECONDS = 0.2
_COMPAT_BOOTSTRAP_RESPONSE_TIMEOUT_SECONDS = 2.0
_COMPAT_BOOTSTRAP_DISABLE_ENV = "MAYA_MCP_DISABLE_COMPAT_BOOTSTRAP"


class _CommandSocketError(OSError):
    """Socket error annotated with whether the command was already sent."""

    def __init__(self, original: OSError, *, send_completed: bool) -> None:
        super().__init__(str(original))
        self.send_completed = send_completed


# Module-level client instance for singleton pattern
_client: CommandPortClient | None = None
_client_lock = threading.Lock()

_MAYA_COMMANDPORT_NOISE_LINES = {
    "Arnold renderer not loaded.",
    "The MtoA plug-in needed for this scene is not loaded.",
    "Make sure Autoload is on in the Plug-in Manager.",
    "See this article for more detail.",
    "https://www.autodesk.com/maya-arnold-not-available-error",
}


def _is_noise_line(part: str) -> bool:
    """Return True for known Maya commandPort noise lines."""
    return part in _MAYA_COMMANDPORT_NOISE_LINES


def _parse_maya_response(raw_response: str) -> str:
    """Parse Maya commandPort response to extract the actual output.

    Maya's commandPort with echoOutput=True returns responses in a format like::

        'None\\n\\x00<actual_output>\\n\\x00\\n\\n\\x00'

    With echoOutput=True, Maya may echo the output twice, resulting in::

        '{"success": true}\\n{"success": true}'

    Some Maya commands (e.g. ``cmds.file()``) produce their own output before
    our ``print(json.dumps(result))`` statement.  In those cases the response
    contains multiple non-empty parts and the JSON payload may not be the first
    one.

    Strategy:
        1. Split by null bytes / newlines, strip whitespace, drop empty / "None".
        2. Find all JSON-like parts (start with ``{`` or ``[``).
        3. If multiple identical JSON parts exist (echoOutput duplication), return one.
        4. Drop known Maya startup/plugin warning lines that can arrive on the
           commandPort stream before command output.
        5. Prefer the **last** unique JSON part, because our ``print(json.dumps(...))``
           is always the final statement.
        6. Fall back to the unique non-empty non-JSON parts joined by newline.

    Args:
        raw_response: Raw response string from Maya commandPort.

    Returns:
        The extracted output string, or empty string if no output found.

    Example:
        >>> _parse_maya_response('None\\n\\x00{"test": 1}\\n\\x00\\n\\n\\x00')
        '{"test": 1}'
        >>> _parse_maya_response('None\\n\\x00\\n\\x00{"ok": true}\\n\\x00')
        '{"ok": true}'
        >>> _parse_maya_response('{"success": true}\\n{"success": true}')
        '{"success": true}'
    """
    if not raw_response:
        return ""

    # Remove null bytes and split into parts
    parts = raw_response.replace("\x00", "\n").split("\n")

    # Filter out empty strings and 'None' (from print() return)
    filtered = [
        p.strip()
        for p in parts
        if p.strip() and p.strip() != "None" and not _is_noise_line(p.strip())
    ]

    if not filtered:
        return ""

    # Find all JSON-like parts
    json_parts = [p for p in filtered if p.startswith(("{", "["))]

    if json_parts:
        # Deduplicate: if all JSON parts are identical, return just one
        # This handles echoOutput duplication
        unique_json = list(dict.fromkeys(json_parts))  # Preserve order, remove dups
        if len(unique_json) == 1:
            return unique_json[0]
        # If different, return the last one (our print is always last)
        return unique_json[-1]

    # Fall back to unique non-empty parts for non-JSON responses. Returning all
    # useful lines preserves command output when Maya logs unrelated text on the
    # same commandPort stream.
    return "\n".join(dict.fromkeys(filtered))


def _escape_mel_string(value: str) -> str:
    """Escape text for a double-quoted MEL string literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _build_compat_server_python_bootstrap(port: int) -> str:
    """Build Python code that starts the packaged compat server inside Maya."""
    compat_source = inspect.getsource(maya_compat_server)
    return (
        "import types\n"
        "_maya_mcp_compat_server = types.ModuleType('_maya_mcp_compat_server')\n"
        f"exec({compat_source!r}, _maya_mcp_compat_server.__dict__)\n"
        f"_maya_mcp_compat_server.start_compat_server(port={port!r})\n"
    )


def _build_compat_server_bootstrap_commands(port: int) -> tuple[str, ...]:
    """Build bootstrap commands for MEL-default and Python commandPorts."""
    python_bootstrap = _build_compat_server_python_bootstrap(port)
    escaped_python_bootstrap = _escape_mel_string(repr(python_bootstrap))
    mel_bootstrap = f'python("exec({escaped_python_bootstrap})")'
    return (mel_bootstrap, python_bootstrap)


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
        self._compat_bootstrap_attempted = False
        self._response_compatibility_checked = False

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
        """Execute a Python command in Maya and return the result.

        Sends a command to Maya via commandPort and waits for the response.
        Automatically connects if not already connected. If the connection
        drops during the send phase, reconnects and retries once.

        Args:
            command: Python code to execute in Maya.

        Returns:
            Command output as string.

        Raises:
            MayaUnavailableError: Cannot connect to Maya.
            MayaCommandError: Command execution failed.
            MayaTimeoutError: Command timed out.

        Example:
            >>> result = client.execute("cmds.ls(selection=True)")
            >>> print(result)
            ['pCube1', 'pSphere1']
        """
        with self._lock:
            return self._execute_with_retry(command, allow_retry=True)

    def ensure_response_compatible(self) -> bool:
        """Ensure Maya's commandPort response path can return command output.

        Returns:
            True if command responses are usable after the check.
        """
        with self._lock:
            if self._compat_bootstrap_disabled() or self._response_compatibility_checked:
                return True

            if self._socket is None:
                self.connect()

            try:
                probe_response = self._send_command(
                    _COMPAT_PROBE_COMMAND,
                    response_timeout=self.config.command_timeout,
                )
            except _CommandSocketError as exc:
                self._handle_socket_error()
                if exc.send_completed:
                    self.connect()
                    return self._bootstrap_compat_server()
                self.connect()
                try:
                    probe_response = self._send_command(
                        _COMPAT_PROBE_COMMAND,
                        response_timeout=self.config.command_timeout,
                    )
                except TimeoutError as retry_exc:
                    self._handle_socket_error()
                    raise MayaTimeoutError(
                        message="Maya commandPort response probe timed out",
                        timeout_seconds=self.config.command_timeout,
                        operation="compatibility probe",
                    ) from retry_exc
                except _CommandSocketError as retry_exc:
                    self._handle_socket_error()
                    if retry_exc.send_completed:
                        self.connect()
                        return self._bootstrap_compat_server()
                    raise MayaUnavailableError(
                        message="Lost connection to Maya during commandPort response probe",
                        host=self.config.host,
                        port=self.config.port,
                        attempts=0,
                        last_error=str(retry_exc),
                    ) from retry_exc
                except OSError as retry_exc:
                    self._handle_socket_error()
                    raise MayaUnavailableError(
                        message="Lost connection to Maya during commandPort response probe",
                        host=self.config.host,
                        port=self.config.port,
                        attempts=0,
                        last_error=str(retry_exc),
                    ) from retry_exc
            except TimeoutError as exc:
                self._handle_socket_error()
                raise MayaTimeoutError(
                    message="Maya commandPort response probe timed out",
                    timeout_seconds=self.config.command_timeout,
                    operation="compatibility probe",
                ) from exc
            except OSError as exc:
                self._handle_socket_error()
                raise MayaUnavailableError(
                    message="Lost connection to Maya during commandPort response probe",
                    host=self.config.host,
                    port=self.config.port,
                    attempts=0,
                    last_error=str(exc),
                ) from exc
            if _COMPAT_PROBE_TOKEN in probe_response:
                self._response_compatibility_checked = True
                return True

            if probe_response:
                logger.debug(
                    "Maya commandPort probe returned unexpected output: %s", probe_response
                )

            return self._bootstrap_compat_server()

    def _execute_with_retry(self, command: str, *, allow_retry: bool) -> str:
        """Execute a command with optional reconnect-and-retry on send failure.

        Args:
            command: Python code to execute in Maya.
            allow_retry: If True, reconnect and retry once on send-phase errors.

        Returns:
            Command output as string.
        """
        # Ensure connected
        if self._socket is None:
            self.connect()

        self.ensure_response_compatible()

        if self._socket is None:
            raise MayaUnavailableError(
                message="Not connected to Maya",
                host=self.config.host,
                port=self.config.port,
                attempts=0,
            )

        try:
            response = self._send_command(command)
            # Update state on success
            self.state.update_contact()
            self.state.last_error = None
            logger.debug("Command completed (%d chars response)", len(response))

            return response

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
            phase = "receive" if isinstance(e, _CommandSocketError) and e.send_completed else "send"
            error_msg = f"Connection lost during {phase}: {e}"
            self.state.last_error = error_msg
            self._handle_socket_error()

            # Only retry on send-phase errors — the command was never delivered
            if phase == "send" and allow_retry:
                logger.warning("Connection lost during send, reconnecting: %s", e)
                try:
                    self.connect()
                    return self._execute_with_retry(command, allow_retry=False)
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

    def _send_command(self, command: str, *, response_timeout: float | None = None) -> str:
        """Send one command over an already connected socket and parse its response."""
        if self._socket is None:
            raise MayaUnavailableError(
                message="Not connected to Maya",
                host=self.config.host,
                port=self.config.port,
                attempts=0,
            )

        send_completed = False
        try:
            self._socket.settimeout(self.config.command_timeout)

            command = command.strip()
            logger.debug("Executing command (%d chars)", len(command))

            if not command.endswith("\n"):
                command += "\n"

            self._socket.sendall(command.encode("utf-8"))
            send_completed = True

            response_parts: list[bytes] = []
            self._socket.settimeout(response_timeout or self.config.command_timeout)
            try:
                first_chunk = self._socket.recv(BUFFER_SIZE)
                if not first_chunk:
                    raise _CommandSocketError(
                        ConnectionResetError("Connection closed before response"),
                        send_completed=True,
                    )
                response_parts.append(first_chunk)
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
                pass

            raw_response = b"".join(response_parts).decode("utf-8").strip()
            return _parse_maya_response(raw_response)
        except TimeoutError:
            raise
        except _CommandSocketError:
            raise
        except OSError as exc:
            raise _CommandSocketError(exc, send_completed=send_completed) from exc

    def _bootstrap_compat_server(self) -> bool:
        """Start the Maya-side compatibility server through the current commandPort."""
        if self._compat_bootstrap_disabled():
            return False
        if self._compat_bootstrap_attempted:
            raise MayaUnavailableError(
                message="Maya compatibility server bootstrap was already attempted",
                host=self.config.host,
                port=self.config.port,
                attempts=0,
                last_error="Compatibility bootstrap did not produce usable command responses",
            )

        self._compat_bootstrap_attempted = True
        logger.warning(
            "Maya commandPort returned empty responses; attempting compatibility server bootstrap"
        )

        last_probe_error = "Compatibility bootstrap did not produce command responses"
        bootstrap_commands = _build_compat_server_bootstrap_commands(self.config.port)

        for bootstrap_command in bootstrap_commands:
            try:
                self._send_command(
                    bootstrap_command,
                    response_timeout=_COMPAT_BOOTSTRAP_RESPONSE_TIMEOUT_SECONDS,
                )
            except _CommandSocketError as exc:
                if not exc.send_completed:
                    self._handle_socket_error()
                    raise MayaUnavailableError(
                        message="Lost connection to Maya while sending compatibility server bootstrap",
                        host=self.config.host,
                        port=self.config.port,
                        attempts=0,
                        last_error=str(exc),
                    ) from exc
            except TimeoutError:
                pass

            self._cleanup_socket()
            time.sleep(_COMPAT_BOOTSTRAP_DELAY_SECONDS)
            self.connect()

            try:
                probe_response = self._send_command(
                    _COMPAT_PROBE_COMMAND,
                    response_timeout=self.config.command_timeout,
                )
            except TimeoutError as exc:
                self._handle_socket_error()
                last_probe_error = "Maya compatibility server response probe timed out"
                if bootstrap_command == bootstrap_commands[-1]:
                    raise MayaTimeoutError(
                        message="Maya compatibility server response probe timed out",
                        timeout_seconds=self.config.command_timeout,
                        operation="compatibility bootstrap",
                    ) from exc
                self.connect()
                continue
            except OSError as exc:
                self._handle_socket_error()
                last_probe_error = str(exc)
                if bootstrap_command == bootstrap_commands[-1]:
                    raise MayaUnavailableError(
                        message="Lost connection to Maya compatibility server after bootstrap",
                        host=self.config.host,
                        port=self.config.port,
                        attempts=0,
                        last_error=str(exc),
                    ) from exc
                self.connect()
                continue

            if probe_response == _COMPAT_PROBE_TOKEN:
                self._response_compatibility_checked = True
                return True

            self._handle_socket_error()
            last_probe_error = (
                probe_response or "Empty response after compatibility server bootstrap"
            )
            if bootstrap_command != bootstrap_commands[-1]:
                self.connect()
                continue

        unexpected_probe = not last_probe_error.startswith(
            ("Compatibility bootstrap", "Empty response", "Maya compatibility server")
        )
        raise MayaUnavailableError(
            message=(
                "Maya compatibility server bootstrap returned unexpected probe output"
                if unexpected_probe
                else "Maya compatibility server bootstrap did not produce command responses"
            ),
            host=self.config.host,
            port=self.config.port,
            attempts=0,
            last_error=last_probe_error,
        )

    def _compat_bootstrap_disabled(self) -> bool:
        value = os.environ.get(_COMPAT_BOOTSTRAP_DISABLE_ENV, "")
        return value.lower() in {"1", "true", "yes", "on"}

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
            self._compat_bootstrap_attempted = False
            self._response_compatibility_checked = False

    def _cleanup_socket(self) -> None:
        """Clean up the socket connection."""
        if self._socket is not None:
            with contextlib.suppress(OSError):
                self._socket.close()
            self._socket = None
            self._response_compatibility_checked = False
            self._compat_bootstrap_attempted = False

    def _handle_socket_error(self) -> None:
        """Handle a socket error by cleaning up and updating state."""
        self._cleanup_socket()
        self.state.status = ConnectionStatus.OFFLINE
