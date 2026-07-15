"""CommandPort controller for Maya.

This module provides functions for managing Maya's commandPort from within Maya.
It handles opening, closing, and querying the status of the commandPort.

Note:
    This module MUST be run inside Maya's Python interpreter as it imports maya.cmds.

Example:
    Open commandPort on default port::

        from maya_mcp.maya_panel.controller import open_command_port
        open_command_port()

    Check if commandPort is open::

        from maya_mcp.maya_panel.controller import is_command_port_open
        if is_command_port_open():
            print("CommandPort is running")
"""

from __future__ import annotations

import logging

from maya_mcp.maya_panel.commandport_compat import (
    MAYA_2024_COMMAND_PORT_BUFFER_SIZE,
    command_port_open_kwargs,
    is_maya_2024_compatible_port,
    mark_maya_2024_compatible_port,
    unmark_maya_2024_compatible_port,
)

# Set up logging
logger = logging.getLogger(__name__)

# Default port for Maya MCP
DEFAULT_PORT = 7001


def get_open_ports() -> list[str]:
    """Get a list of currently open commandPorts.

    Returns:
        List of port names (e.g., [":7001", ":7002"]).

    Example:
        >>> ports = get_open_ports()
        >>> print(ports)
        [':7001']
    """
    import maya.cmds as cmds

    ports = cmds.commandPort(query=True, listPorts=True)
    return ports if ports else []


def is_command_port_open(port: int = DEFAULT_PORT) -> bool:
    """Check if commandPort is open on the specified port.

    Args:
        port: Port number to check.

    Returns:
        True if the commandPort is open on the specified port.

    Example:
        >>> is_command_port_open(7001)
        True
    """
    return get_open_port_name(port) is not None


def get_open_port_name(port: int = DEFAULT_PORT) -> str | None:
    """Return Maya's reported name for an open TCP commandPort number."""
    port_number = str(port)
    return next(
        (name for name in get_open_ports() if str(name).rsplit(":", 1)[-1] == port_number),
        None,
    )


def open_command_port(
    port: int = DEFAULT_PORT,
    source_type: str = "python",
    echo_output: bool = True,
    *,
    replace_existing: bool = False,
) -> bool:
    """Open Maya's commandPort on the specified port.

    If the port is already open, this function returns True without reopening.

    Args:
        port: Port number to open (1-65535).
        source_type: Command interpreter ("python" or "mel").
        echo_output: If True, send command output back to client.
        replace_existing: Replace an unknown existing Maya 2024 listener.
            Leave False for automatic startup; set True only after explicit
            user confirmation that this helper owns the port.

    Returns:
        True if the port is now open (either opened or was already open).

    Raises:
        ValueError: If port is out of valid range.
        RuntimeError: If commandPort could not be opened.

    Example:
        >>> open_command_port(7001)
        True
    """
    import maya.cmds as cmds

    if not 1 <= port <= 65535:
        msg = f"Port must be between 1 and 65535, got {port}"
        raise ValueError(msg)

    port_name = f":{port}"

    # Maya 2024 ports opened without the compatibility policy accept sockets but
    # cannot return responses. Replace an existing Python/echo port in that one
    # release; all other versions retain the established early-return path.
    existing_port_name = get_open_port_name(port)
    if existing_port_name is not None and is_maya_2024_compatible_port(port):
        logger.info("CommandPort already open on %s", port_name)
        return True

    port_kwargs = command_port_open_kwargs(cmds, source_type, echo_output)
    is_maya_2024_compatibility = port_kwargs.get("bufferSize") == MAYA_2024_COMMAND_PORT_BUFFER_SIZE

    if existing_port_name is not None:
        if not is_maya_2024_compatibility or not replace_existing:
            logger.info("CommandPort already open on %s", port_name)
            return True
        cmds.commandPort(name=existing_port_name, close=True)
        unmark_maya_2024_compatible_port(port)
        logger.info("Replacing incompatible Maya 2024 commandPort on %s", port_name)

    # Open the port
    try:
        cmds.commandPort(
            name=port_name,
            **port_kwargs,
        )
        if is_maya_2024_compatibility:
            mark_maya_2024_compatible_port(port)
        logger.info("CommandPort opened on %s", port_name)
        return True
    except RuntimeError as e:
        logger.exception("Failed to open commandPort on %s", port_name)
        msg = f"Failed to open commandPort on {port_name}: {e}"
        raise RuntimeError(msg) from e


def close_command_port(port: int = DEFAULT_PORT) -> bool:
    """Close Maya's commandPort on the specified port.

    If the port is not open, this function returns True.

    Args:
        port: Port number to close.

    Returns:
        True if the port is now closed (either closed or was already closed).

    Example:
        >>> close_command_port(7001)
        True
    """
    import maya.cmds as cmds

    port_name = f":{port}"

    # Check if open
    existing_port_name = get_open_port_name(port)
    if existing_port_name is None:
        logger.info("CommandPort already closed on %s", port_name)
        return True

    # Close the port
    try:
        cmds.commandPort(name=existing_port_name, close=True)
        unmark_maya_2024_compatible_port(port)
        logger.info("CommandPort closed on %s", port_name)
        return True
    except RuntimeError as e:
        logger.exception("Failed to close commandPort on %s", port_name)
        # Port might have been closed by something else
        if not is_command_port_open(port):
            return True
        msg = f"Failed to close commandPort on {port_name}: {e}"
        raise RuntimeError(msg) from e


def toggle_command_port(port: int = DEFAULT_PORT) -> bool:
    """Toggle commandPort on/off.

    Args:
        port: Port number to toggle.

    Returns:
        True if the port is now open, False if closed.

    Example:
        >>> toggle_command_port(7001)
        True  # Port was closed, now open
        >>> toggle_command_port(7001)
        False  # Port was open, now closed
    """
    if is_command_port_open(port):
        close_command_port(port)
        return False
    else:
        open_command_port(port)
        return True


def get_port_status(port: int = DEFAULT_PORT) -> dict[str, object]:
    """Get detailed status of the commandPort.

    Args:
        port: Port number to check.

    Returns:
        Dictionary with status information:
            - is_open: Whether the port is open
            - port: Port number
            - port_name: Port name string (e.g., ":7001")
            - all_ports: List of all open ports

    Example:
        >>> get_port_status(7001)
        {'is_open': True, 'port': 7001, 'port_name': ':7001', 'all_ports': [':7001']}
    """
    all_ports = get_open_ports()
    open_port_name = get_open_port_name(port)

    return {
        "is_open": open_port_name is not None,
        "port": port,
        "port_name": open_port_name or f":{port}",
        "all_ports": all_ports,
    }
