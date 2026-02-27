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
import socket
import time

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

# Buffer size for socket receive
BUFFER_SIZE = 65536

# Module-level client instance for singleton pattern
_client: CommandPortClient | None = None


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
        4. Prefer the **last** unique JSON part, because our ``print(json.dumps(...))``
           is always the final statement.
        5. Fall back to the first non-empty part for non-JSON responses.

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
    filtered = [p.strip() for p in parts if p.strip() and p.strip() != "None"]

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

    # Fall back to the first non-empty part for non-JSON responses
    return filtered[0]


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
        if self._socket is not None:
            # Already connected
            return True

        self.state.status = ConnectionStatus.RECONNECTING
        last_error: str | None = None

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
                time.sleep(delay)

        # All retries exhausted
        self.state.status = ConnectionStatus.OFFLINE
        self.state.last_error = last_error

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
        was_connected = self._socket is not None
        self._cleanup_socket()
        self.state.status = ConnectionStatus.OFFLINE
        return was_connected

    def execute(self, command: str) -> str:
        """Execute a Python command in Maya and return the result.

        Sends a command to Maya via commandPort and waits for the response.
        Automatically connects if not already connected.

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

        try:
            # Set command timeout
            self._socket.settimeout(self.config.command_timeout)

            # Prepare command
            command = command.strip()

            # Maya commandPort requires a newline to execute the command
            if not command.endswith("\n"):
                command += "\n"

            command_bytes = command.encode("utf-8")
            self._socket.sendall(command_bytes)

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

            # Parse Maya's response format to extract actual output
            response = _parse_maya_response(raw_response)

            # Update state on success
            self.state.update_contact()
            self.state.last_error = None

            return response

        except TimeoutError as exc:
            self.state.last_error = f"Command timed out after {self.config.command_timeout}s"
            self._handle_socket_error()
            raise MayaTimeoutError(
                message="Command execution timed out",
                timeout_seconds=self.config.command_timeout,
                operation="execute",
            ) from exc

        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            error_msg = f"Connection lost: {e}"
            self.state.last_error = error_msg
            self._handle_socket_error()
            raise MayaUnavailableError(
                message="Lost connection to Maya during command execution",
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
        return self.state.status

    def get_health(self) -> HealthCheckResult:
        """Get detailed health information.

        Returns:
            HealthCheckResult with current connection health details.

        Example:
            >>> health = client.get_health()
            >>> print(f"Status: {health.status}")
        """
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

    def _handle_socket_error(self) -> None:
        """Handle a socket error by cleaning up and updating state."""
        self._cleanup_socket()
        self.state.status = ConnectionStatus.OFFLINE
