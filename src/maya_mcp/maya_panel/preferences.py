"""Preferences management for Maya MCP Panel.

This module handles saving and loading user preferences for the MCP panel,
including auto-start settings and port configuration.

Preferences are stored using Maya's optionVar system, which persists
across Maya sessions.

Example:
    Get and set port::

        from maya_mcp.maya_panel.preferences import get_port, set_port
        port = get_port()  # Returns 7001 by default
        set_port(7002)

    Get and set auto-start::

        from maya_mcp.maya_panel.preferences import get_auto_start, set_auto_start
        set_auto_start(True)
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Option variable names (prefixed with mayaMCP_ to avoid conflicts)
OPTION_PORT = "mayaMCP_port"
OPTION_AUTO_START = "mayaMCP_autoStart"

# Default values
DEFAULT_PORT = 7001
DEFAULT_AUTO_START = False


def get_port() -> int:
    """Get the configured commandPort port number.

    Returns:
        Port number from preferences, or DEFAULT_PORT if not set.

    Example:
        >>> get_port()
        7001
    """
    import maya.cmds as cmds

    if cmds.optionVar(exists=OPTION_PORT):
        return int(cmds.optionVar(query=OPTION_PORT))
    return DEFAULT_PORT


def set_port(port: int) -> None:
    """Set the commandPort port number in preferences.

    Args:
        port: Port number to save (1-65535).

    Raises:
        ValueError: If port is out of valid range.

    Example:
        >>> set_port(7002)
    """
    import maya.cmds as cmds

    if not 1 <= port <= 65535:
        msg = f"Port must be between 1 and 65535, got {port}"
        raise ValueError(msg)

    cmds.optionVar(intValue=(OPTION_PORT, port))
    logger.debug("Saved port preference: %d", port)


def get_auto_start() -> bool:
    """Get the auto-start preference.

    Returns:
        True if commandPort should auto-start on Maya launch.

    Example:
        >>> get_auto_start()
        False
    """
    import maya.cmds as cmds

    if cmds.optionVar(exists=OPTION_AUTO_START):
        return bool(cmds.optionVar(query=OPTION_AUTO_START))
    return DEFAULT_AUTO_START


def set_auto_start(enabled: bool) -> None:
    """Set the auto-start preference.

    Args:
        enabled: Whether to auto-start commandPort on Maya launch.

    Example:
        >>> set_auto_start(True)
    """
    import maya.cmds as cmds

    cmds.optionVar(intValue=(OPTION_AUTO_START, int(enabled)))
    logger.debug("Saved auto-start preference: %s", enabled)


def reset_preferences() -> None:
    """Reset all MCP preferences to defaults.

    Example:
        >>> reset_preferences()
    """
    import maya.cmds as cmds

    if cmds.optionVar(exists=OPTION_PORT):
        cmds.optionVar(remove=OPTION_PORT)

    if cmds.optionVar(exists=OPTION_AUTO_START):
        cmds.optionVar(remove=OPTION_AUTO_START)

    logger.info("Reset all MCP preferences to defaults")


def get_all_preferences() -> dict[str, object]:
    """Get all MCP preferences as a dictionary.

    Returns:
        Dictionary with all preference values.

    Example:
        >>> get_all_preferences()
        {'port': 7001, 'auto_start': False}
    """
    return {
        "port": get_port(),
        "auto_start": get_auto_start(),
    }
