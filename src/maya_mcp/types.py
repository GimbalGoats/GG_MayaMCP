"""Type definitions for Maya MCP.

This module contains all shared type definitions used throughout Maya MCP,
including enums, dataclasses, and type aliases.

These types are designed to be stable and form the public API contract
that MCP clients can rely on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal


class ConnectionStatus(Enum):
    """Connection status for Maya commandPort.

    Attributes:
        OK: Connected and responsive.
        OFFLINE: Not connected, no active connection attempts.
        RECONNECTING: Attempting to establish/re-establish connection.
    """

    OK = "ok"
    OFFLINE = "offline"
    RECONNECTING = "reconnecting"


@dataclass
class ConnectionConfig:
    """Configuration for Maya commandPort connection.

    Attributes:
        host: Target host (localhost only in v0).
        port: Target port number.
        connect_timeout: Connection timeout in seconds.
        command_timeout: Command execution timeout in seconds.
        max_retries: Maximum number of connection retry attempts.
        retry_base_delay: Base delay for exponential backoff (seconds).
    """

    host: str = "localhost"
    port: int = 7001
    connect_timeout: float = 5.0
    command_timeout: float = 30.0
    max_retries: int = 3
    retry_base_delay: float = 0.5

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.host not in ("localhost", "127.0.0.1"):
            raise ValueError("Only localhost connections are supported in v0")
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Invalid port number: {self.port}")
        if self.connect_timeout <= 0:
            raise ValueError("connect_timeout must be positive")
        if self.command_timeout <= 0:
            raise ValueError("command_timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.retry_base_delay <= 0:
            raise ValueError("retry_base_delay must be positive")


@dataclass
class HealthCheckResult:
    """Result of a health check operation.

    Attributes:
        status: Current connection status.
        last_error: Last error message, if any.
        last_contact: Timestamp of last successful contact with Maya.
        host: Current target host.
        port: Current target port.
    """

    status: Literal["ok", "offline", "reconnecting"]
    last_error: str | None
    last_contact: str | None  # ISO8601 timestamp
    host: str
    port: int


@dataclass
class ConnectResult:
    """Result of a connection attempt.

    Attributes:
        connected: Whether connection was successful.
        host: Target host.
        port: Target port.
        error: Error message if connection failed.
    """

    connected: bool
    host: str
    port: int
    error: str | None = None


@dataclass
class DisconnectResult:
    """Result of a disconnect operation.

    Attributes:
        disconnected: Whether disconnect was successful.
        was_connected: Whether was connected before disconnect.
    """

    disconnected: bool
    was_connected: bool


@dataclass
class SceneInfo:
    """Information about the current Maya scene.

    Attributes:
        file_path: Path to the current scene file, or None if untitled.
        modified: Whether the scene has unsaved changes.
        fps: Frames per second.
        frame_range: Tuple of (start_frame, end_frame).
        up_axis: Scene up axis ('y' or 'z').
    """

    file_path: str | None
    modified: bool
    fps: float
    frame_range: tuple[float, float]
    up_axis: Literal["y", "z"]


@dataclass
class NodeListResult:
    """Result of a node listing operation.

    Attributes:
        nodes: List of node names.
        count: Number of nodes in the list.
    """

    nodes: list[str] = field(default_factory=list)
    count: int = 0

    def __post_init__(self) -> None:
        """Update count from nodes list."""
        self.count = len(self.nodes)


@dataclass
class SelectionResult:
    """Result of a selection query or modification.

    Attributes:
        selection: List of selected node names.
        count: Number of selected items.
    """

    selection: list[str] = field(default_factory=list)
    count: int = 0

    def __post_init__(self) -> None:
        """Update count from selection list."""
        self.count = len(self.selection)


@dataclass
class ClientState:
    """Internal state of the CommandPort client.

    Attributes:
        status: Current connection status.
        last_error: Last error encountered.
        last_contact: Timestamp of last successful Maya contact.
        config: Current connection configuration.
    """

    status: ConnectionStatus = ConnectionStatus.OFFLINE
    last_error: str | None = None
    last_contact: datetime | None = None
    config: ConnectionConfig = field(default_factory=ConnectionConfig)

    def update_contact(self) -> None:
        """Update last_contact to current time."""
        self.last_contact = datetime.utcnow()

    def get_last_contact_iso(self) -> str | None:
        """Get last_contact as ISO8601 string."""
        if self.last_contact is None:
            return None
        return self.last_contact.isoformat() + "Z"
