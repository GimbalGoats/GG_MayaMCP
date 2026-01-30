"""Connection management tools for Maya MCP.

This module provides tools for manually controlling the connection
to Maya's commandPort. These are optional debugging controls.
"""

from __future__ import annotations

from typing import Any, Literal

from maya_mcp.errors import MayaUnavailableError
from maya_mcp.transport import get_client


def maya_connect(
    host: str = "localhost",
    port: int = 7001,
    source_type: Literal["python", "mel"] = "python",  # noqa: ARG001
) -> dict[str, Any]:
    """Establish a connection to Maya's commandPort.

    Attempts to connect to Maya at the specified host and port.
    This is primarily for debugging and explicit connection control.

    Args:
        host: Target host. Only "localhost" or "127.0.0.1" are supported.
        port: Target port number (1-65535).
        source_type: Command interpreter type. Currently only "python" is
            actually used; "mel" is accepted for compatibility.

    Returns:
        Dictionary with connection result:
            - connected: Whether connection succeeded
            - host: Target host
            - port: Target port
            - error: Error message if connection failed, else None

    Example:
        >>> result = maya_connect(port=7001)
        >>> if result["connected"]:
        ...     print("Connected!")
    """
    client = get_client()

    # Reconfigure if host/port differ
    if client.config.host != host or client.config.port != port:
        client.reconfigure(host=host, port=port)

    try:
        client.connect()
        return {
            "connected": True,
            "host": host,
            "port": port,
            "error": None,
        }
    except MayaUnavailableError as e:
        return {
            "connected": False,
            "host": host,
            "port": port,
            "error": e.message,
        }


def maya_disconnect() -> dict[str, Any]:
    """Close the connection to Maya.

    Disconnects from Maya's commandPort and moves the client state
    to offline.

    Returns:
        Dictionary with disconnect result:
            - disconnected: Whether disconnect was performed
            - was_connected: Whether was connected before

    Example:
        >>> result = maya_disconnect()
        >>> print(f"Was connected: {result['was_connected']}")
    """
    client = get_client()
    was_connected = client.is_connected()
    client.disconnect()

    return {
        "disconnected": True,
        "was_connected": was_connected,
    }
