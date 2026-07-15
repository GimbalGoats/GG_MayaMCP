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

import base64
import contextlib
import json
import logging
import socket
import threading
import time
from typing import Literal

from maya_mcp.commandport_protocol import (
    MAYA_2024_HANDLER_NAME,
    MAYA_2024_PORTS_NAME,
    MAYA_2024_REQUIRED_PROBE_SIZE,
)
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
_MAYA_COMPATIBILITY_PROBE_KEY = "__maya_mcp_compat__"
_MAYA_COMPATIBILITY_BUFFER_KEY = "__maya_mcp_buffer__"
_MAYA_COMPATIBILITY_RESPONSE_KEY = "__maya_mcp_response__"


class _MayaCompatibilityProbeError(TimeoutError):
    """A connected port did not complete the compatibility handshake."""


class _MayaCompatibilityProbeTimeout(_MayaCompatibilityProbeError):
    """A compatibility response did not arrive before the probe deadline."""


class _MayaCompatibilityProbeInvalid(_MayaCompatibilityProbeError):
    """A compatibility response arrived but did not match the protocol."""


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
            _client = CommandPortClient(auto_detect_maya_compatibility=True)
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
        auto_detect_maya_compatibility: bool = True,
        source_type: Literal["python", "mel"] = "python",
    ) -> None:
        """Initialize the CommandPortClient.

        Args:
            host: Target host. Only "localhost" or "127.0.0.1" are supported.
            port: Target port number (1-65535).
            connect_timeout: Connection timeout in seconds.
            command_timeout: Command execution timeout in seconds.
            max_retries: Maximum number of connection retry attempts.
            retry_base_delay: Base delay for exponential backoff (seconds).
            auto_detect_maya_compatibility: Detect the Maya 2024 response mode
                once per socket connection. Enabled by default for every public
                client; low-level legacy callers can explicitly opt out.
            source_type: Maya commandPort interpreter. Compatibility detection
                applies only to Python listeners.

        Raises:
            ValueError: If configuration is invalid.
        """
        if source_type not in {"python", "mel"}:
            raise ValueError(f"Unsupported commandPort source type: {source_type}")
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
        self._auto_detect_maya_compatibility = auto_detect_maya_compatibility
        self.source_type = source_type
        self._maya_2024_compatibility = False

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
            attempts_made = 0
            logger.info("Connecting to Maya at %s:%d", self.config.host, self.config.port)

            for attempt in range(self.config.max_retries):
                attempts_made = attempt + 1
                try:
                    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    self._socket.settimeout(self.config.connect_timeout)
                    self._socket.connect((self.config.host, self.config.port))
                    if self._auto_detect_maya_compatibility and self.source_type == "python":
                        self._detect_maya_compatibility()

                    # Connection successful
                    self.state.status = ConnectionStatus.OK
                    self.state.last_error = None
                    self.state.update_contact()
                    logger.info("Connected to Maya at %s:%d", self.config.host, self.config.port)
                    return True

                except _MayaCompatibilityProbeError as exc:
                    last_error = str(exc)
                    self._cleanup_socket()
                    break
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
                attempts_made,
                last_error,
            )

            raise MayaUnavailableError(
                message=f"Cannot connect to Maya commandPort at {self.config.host}:{self.config.port}",
                host=self.config.host,
                port=self.config.port,
                attempts=attempts_made,
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
            prepared_command = command.strip()
            logger.debug("Executing command (%d chars)", len(prepared_command))

            if self._maya_2024_compatibility:
                encoded = base64.b64encode(prepared_command.encode("utf-8")).decode("ascii")
                prepared_command = (
                    "__import__('json').dumps({"
                    f"'{_MAYA_COMPATIBILITY_RESPONSE_KEY}':"
                    f"getattr(__import__('builtins'),'{MAYA_2024_HANDLER_NAME}')("
                    f"__import__('base64').b64decode('{encoded}').decode('utf-8'))}})"
                )

            # Maya commandPort requires a newline to execute the command
            if not prepared_command.endswith("\n"):
                prepared_command += "\n"

            command_bytes = prepared_command.encode("utf-8")
            self._socket.sendall(command_bytes)
            send_completed = True

            response = self._receive_response()
            if self._maya_2024_compatibility:
                if not response:
                    self.state.last_error = (
                        f"Command timed out after {self.config.command_timeout}s"
                    )
                    self._handle_socket_error()
                    raise MayaTimeoutError(
                        message="Command execution timed out",
                        timeout_seconds=self.config.command_timeout,
                        operation="execute",
                    )
                try:
                    payload = json.loads(response)[_MAYA_COMPATIBILITY_RESPONSE_KEY]
                except (json.JSONDecodeError, KeyError, TypeError) as exc:
                    self.state.last_error = "Invalid Maya 2024 commandPort response envelope"
                    self._handle_socket_error()
                    raise MayaUnavailableError(
                        message="Invalid Maya 2024 commandPort response envelope",
                        host=self.config.host,
                        port=self.config.port,
                        attempts=0,
                    ) from exc
                if not isinstance(payload, dict) or not isinstance(payload.get("ok"), bool):
                    self._handle_socket_error()
                    raise MayaUnavailableError(
                        message="Invalid Maya 2024 commandPort response payload",
                        host=self.config.host,
                        port=self.config.port,
                        attempts=0,
                    )
                if not payload["ok"]:
                    maya_error = str(payload.get("error", "Unknown Maya command error"))
                    raise MayaCommandError(
                        message=f"Maya command failed: {maya_error}",
                        command=command,
                        maya_error=maya_error,
                    )
                response = str(payload.get("result", ""))

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
            phase = "receive" if send_completed else "send"
            error_msg = f"Connection lost during {phase}: {e}"
            self.state.last_error = error_msg
            self._handle_socket_error()

            # Only retry on send-phase errors — the command was never delivered
            if not send_completed and allow_retry:
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

    def _detect_maya_compatibility(self) -> None:
        """Detect the exact Maya 2024 response mode once on a new connection."""
        if self._socket is None:
            return
        probe = (
            "__import__('json').dumps({"
            f"'{_MAYA_COMPATIBILITY_PROBE_KEY}':"
            "str(__import__('maya.cmds',fromlist=['cmds']).about(majorVersion=True))"
            "+':' + str(int("
            f"{self.config.port} in getattr(__import__('builtins'),'{MAYA_2024_PORTS_NAME}',())"
            f" and callable(getattr(__import__('builtins'),'{MAYA_2024_HANDLER_NAME}',None))))}})\n"
        )
        # TCP is connected; this probe executes on Maya's main thread and gets
        # one full command deadline rather than multiplying it across retries.
        probe_timeout = self.config.command_timeout
        self._socket.settimeout(probe_timeout)
        self._send_compatibility_probe(
            probe,
            error="Maya compatibility probe timed out while sending",
        )
        response = self._receive_response(timeout=probe_timeout)
        if not response:
            raise _MayaCompatibilityProbeTimeout(
                "Maya compatibility probe returned no response"
            )
        try:
            mode = json.loads(response)[_MAYA_COMPATIBILITY_PROBE_KEY]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise _MayaCompatibilityProbeInvalid(
                "Maya compatibility probe returned an invalid response"
            ) from exc
        if mode == "2024:1":
            self._verify_maya_2024_buffer(probe_timeout)
            self._maya_2024_compatibility = True
        elif isinstance(mode, str) and mode.startswith("2024:"):
            raise _MayaCompatibilityProbeInvalid(
                "Maya 2024 commandPort lacks the compatibility handler; "
                "close and reopen it with the GG_MayaMCP helper"
            )

    def _verify_maya_2024_buffer(self, timeout: float) -> None:
        """Prove the active listener accepts commands beyond Maya's default buffer."""
        if self._socket is None:
            return
        payload_size = MAYA_2024_REQUIRED_PROBE_SIZE
        padding = "x" * payload_size
        probe = (
            "__import__('json').dumps({"
            f"'{_MAYA_COMPATIBILITY_BUFFER_KEY}':len('{padding}')"
            "})\n"
        )
        self._send_compatibility_probe(
            probe,
            error="Maya 2024 compatibility buffer probe timed out while sending",
        )
        response = self._receive_response(timeout=timeout)
        if not response:
            raise _MayaCompatibilityProbeTimeout(
                "Maya 2024 compatibility buffer probe returned no response"
            )
        try:
            accepted_size = json.loads(response)[_MAYA_COMPATIBILITY_BUFFER_KEY]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise _MayaCompatibilityProbeInvalid(
                "Maya 2024 compatibility buffer probe returned an invalid response"
            ) from exc
        if accepted_size != payload_size:
            raise _MayaCompatibilityProbeInvalid(
                "Maya 2024 compatibility buffer probe returned an unexpected size"
            )

    def _send_compatibility_probe(self, probe: str, *, error: str) -> None:
        if self._socket is None:
            return
        try:
            self._socket.sendall(probe.encode("utf-8"))
        except TimeoutError as exc:
            raise _MayaCompatibilityProbeTimeout(error) from exc

    def _receive_response(self, *, timeout: float | None = None) -> str:
        """Read and parse one commandPort response."""
        if self._socket is None:
            return ""
        response_parts: list[bytes] = []
        self._socket.settimeout(self.config.command_timeout if timeout is None else timeout)
        try:
            first_chunk = self._socket.recv(BUFFER_SIZE)
            if first_chunk:
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
        source_type: Literal["python", "mel"] | None = None,
    ) -> None:
        """Update connection configuration.

        Disconnects if currently connected and updates the configuration.

        Args:
            host: New target host (optional).
            port: New target port (optional).
            source_type: New command interpreter (optional).

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
            new_source_type = source_type if source_type is not None else self.source_type
            if new_source_type not in {"python", "mel"}:
                raise ValueError(f"Unsupported commandPort source type: {new_source_type}")

            self.config = ConnectionConfig(
                host=new_host,
                port=new_port,
                connect_timeout=self.config.connect_timeout,
                command_timeout=self.config.command_timeout,
                max_retries=self.config.max_retries,
                retry_base_delay=self.config.retry_base_delay,
            )
            self.state.config = self.config
            self.source_type = new_source_type

    def _cleanup_socket(self) -> None:
        """Clean up the socket connection."""
        if self._socket is not None:
            with contextlib.suppress(OSError):
                self._socket.close()
            self._socket = None
        self._maya_2024_compatibility = False

    def _handle_socket_error(self) -> None:
        """Handle a socket error by cleaning up and updating state."""
        self._cleanup_socket()
        self.state.status = ConnectionStatus.OFFLINE
