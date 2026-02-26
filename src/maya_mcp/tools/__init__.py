"""MCP tools for Maya MCP.

This package contains all MCP tool implementations organized by domain.
"""

from maya_mcp.tools.attributes import attributes_get, attributes_set
from maya_mcp.tools.connection import maya_connect, maya_disconnect
from maya_mcp.tools.connections import (
    connections_connect,
    connections_disconnect,
    connections_get,
    connections_history,
    connections_list,
)
from maya_mcp.tools.health import health_check
from maya_mcp.tools.nodes import nodes_create, nodes_delete, nodes_info, nodes_list
from maya_mcp.tools.scene import scene_info, scene_new, scene_redo, scene_undo
from maya_mcp.tools.selection import selection_clear, selection_get, selection_set

__all__ = [
    "attributes_get",
    "attributes_set",
    "connections_connect",
    "connections_disconnect",
    "connections_get",
    "connections_history",
    "connections_list",
    "health_check",
    "maya_connect",
    "maya_disconnect",
    "nodes_create",
    "nodes_delete",
    "nodes_info",
    "nodes_list",
    "scene_info",
    "scene_new",
    "scene_redo",
    "scene_undo",
    "selection_clear",
    "selection_get",
    "selection_set",
]
