"""Typed error classes for Maya MCP.

This module defines the error hierarchy used throughout Maya MCP.
All errors inherit from MayaMCPError, making it easy to catch all
Maya MCP-related exceptions.

Example:
    Handling Maya errors::

        from maya_mcp.errors import MayaUnavailableError, MayaCommandError

        try:
            result = client.execute("cmds.ls()")
        except MayaUnavailableError as e:
            print(f"Maya not available: {e.message}")
        except MayaCommandError as e:
            print(f"Command failed: {e.message}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MayaMCPError(Exception):
    """Base exception for all Maya MCP errors.

    All errors raised by Maya MCP inherit from this class, making it
    easy to catch all Maya MCP-related exceptions with a single handler.

    Attributes:
        message: Human-readable error description.
        details: Additional context as key-value pairs.
    """

    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Return the error message."""
        return self.message


@dataclass
class MayaUnavailableError(MayaMCPError):
    """Raised when Maya cannot be reached via commandPort.

    This error indicates that the MCP server cannot establish a connection
    to Maya's commandPort. This typically happens when:

    - Maya is not running
    - commandPort is not open in Maya
    - Network/socket issues

    Attributes:
        message: Human-readable error description.
        host: Target host that was attempted.
        port: Target port that was attempted.
        attempts: Number of connection attempts made.
        last_error: The last underlying error message, if any.
    """

    host: str = "localhost"
    port: int = 7001
    attempts: int = 0
    last_error: str | None = None

    def __post_init__(self) -> None:
        """Populate details from attributes."""
        self.details = {
            "host": self.host,
            "port": self.port,
            "attempts": self.attempts,
            "last_error": self.last_error,
        }


@dataclass
class MayaCommandError(MayaMCPError):
    """Raised when a Maya command fails to execute.

    This error indicates that the command was sent to Maya but
    failed during execution. The command syntax may be invalid,
    or the operation may have failed for other reasons.

    Attributes:
        message: Human-readable error description.
        command: The command that failed (may be truncated for security).
        maya_error: The error message returned by Maya.
    """

    command: str = ""
    maya_error: str = ""

    def __post_init__(self) -> None:
        """Populate details from attributes."""
        # Truncate command for security (no full code in logs)
        truncated_cmd = self.command[:100] + "..." if len(self.command) > 100 else self.command
        self.details = {
            "command": truncated_cmd,
            "maya_error": self.maya_error,
        }


@dataclass
class MayaTimeoutError(MayaMCPError):
    """Raised when a Maya operation times out.

    This error indicates that a command was sent to Maya but
    no response was received within the configured timeout period.

    Attributes:
        message: Human-readable error description.
        timeout_seconds: The timeout value that was exceeded.
        operation: Description of the operation that timed out.
    """

    timeout_seconds: float = 0.0
    operation: str = ""

    def __post_init__(self) -> None:
        """Populate details from attributes."""
        self.details = {
            "timeout_seconds": self.timeout_seconds,
            "operation": self.operation,
        }


@dataclass
class ValidationError(MayaMCPError):
    """Raised when input validation fails.

    This error indicates that the input parameters to a tool
    or function did not pass validation.

    Attributes:
        message: Human-readable error description.
        field: The name of the field that failed validation.
        value: The invalid value (sanitized for security).
        constraint: Description of the violated constraint.
    """

    field_name: str = ""
    value: str = ""
    constraint: str = ""

    def __post_init__(self) -> None:
        """Populate details from attributes."""
        # Sanitize value for security
        sanitized_value = str(self.value)[:50] if self.value else ""
        self.details = {
            "field": self.field_name,
            "value": sanitized_value,
            "constraint": self.constraint,
        }
