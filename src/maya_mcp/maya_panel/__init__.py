"""Maya MCP Control Panel.

This package provides a dockable Qt widget inside Maya for controlling
the MCP server connection via commandPort.

Note:
    This module is designed to run INSIDE Maya's Python interpreter.
    It imports maya.cmds and uses PySide2 (Maya's Qt binding).

Example:
    Show the panel in Maya::

        from maya_mcp.maya_panel import show_panel
        show_panel()

    Or from Maya's script editor::

        import maya_mcp.maya_panel
        maya_mcp.maya_panel.show_panel()
"""

from __future__ import annotations

from maya_mcp.maya_panel.panel import MCPControlPanel, auto_start_if_enabled, show_panel

__all__ = ["MCPControlPanel", "auto_start_if_enabled", "show_panel"]
