"""MCP tools for Maya MCP.

This package contains all MCP tool implementations organized by domain.
"""

from maya_mcp.tools.connection import maya_connect, maya_disconnect
from maya_mcp.tools.health import health_check
from maya_mcp.tools.nodes import nodes_list
from maya_mcp.tools.scene import scene_info
from maya_mcp.tools.selection import selection_get, selection_set

__all__ = [
    "health_check",
    "maya_connect",
    "maya_disconnect",
    "nodes_list",
    "scene_info",
    "selection_get",
    "selection_set",
]
