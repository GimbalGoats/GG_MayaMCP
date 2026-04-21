"""Tool registration for the Maya MCP server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from maya_mcp.registrars.animation import register_animation_tools
from maya_mcp.registrars.attributes import register_attribute_tools
from maya_mcp.registrars.connections import register_connections_tools
from maya_mcp.registrars.core import register_core_tools
from maya_mcp.registrars.curve import register_curve_tools
from maya_mcp.registrars.mesh import register_mesh_tools
from maya_mcp.registrars.modeling import register_modeling_tools
from maya_mcp.registrars.nodes import register_node_tools
from maya_mcp.registrars.scene import register_scene_tools
from maya_mcp.registrars.scripts import register_script_tools
from maya_mcp.registrars.selection import register_selection_tools
from maya_mcp.registrars.shading import register_shading_tools
from maya_mcp.registrars.skin import register_skin_tools
from maya_mcp.registrars.viewport import register_viewport_tools

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register_all_tools(mcp: FastMCP) -> None:
    """Register the complete tool surface on a FastMCP server instance."""
    register_core_tools(mcp)
    register_scene_tools(mcp)
    register_node_tools(mcp)
    register_attribute_tools(mcp)
    register_connections_tools(mcp)
    register_selection_tools(mcp)
    register_mesh_tools(mcp)
    register_viewport_tools(mcp)
    register_curve_tools(mcp)
    register_modeling_tools(mcp)
    register_shading_tools(mcp)
    register_skin_tools(mcp)
    register_script_tools(mcp)
    register_animation_tools(mcp)
