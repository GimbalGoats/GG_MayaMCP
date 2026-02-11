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
    port_name = f":{port}"
    return port_name in get_open_ports()


def open_command_port(
    port: int = DEFAULT_PORT,
    source_type: str = "python",
    echo_output: bool = True,
) -> bool:
    """Open Maya's commandPort on the specified port.

    If the port is already open, this function returns True without reopening.

    Args:
        port: Port number to open (1-65535).
        source_type: Command interpreter ("python" or "mel").
        echo_output: If True, send command output back to client.

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

    # Check if already open
    if is_command_port_open(port):
        logger.info("CommandPort already open on %s", port_name)
        return True

    # Open the port
    try:
        cmds.commandPort(
            name=port_name,
            sourceType=source_type,
            echoOutput=echo_output,
        )
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
    if not is_command_port_open(port):
        logger.info("CommandPort already closed on %s", port_name)
        return True

    # Close the port
    try:
        cmds.commandPort(name=port_name, close=True)
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
    port_name = f":{port}"

    return {
        "is_open": port_name in all_ports,
        "port": port,
        "port_name": port_name,
        "all_ports": all_ports,
    }
