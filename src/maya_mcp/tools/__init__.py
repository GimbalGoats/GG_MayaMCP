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
from maya_mcp.tools.curve import curve_cvs, curve_info
from maya_mcp.tools.health import health_check
from maya_mcp.tools.modeling import (
    modeling_bevel,
    modeling_boolean,
    modeling_bridge,
    modeling_center_pivot,
    modeling_combine,
    modeling_create_polygon_primitive,
    modeling_delete_faces,
    modeling_delete_history,
    modeling_extrude_faces,
    modeling_freeze_transforms,
    modeling_insert_edge_loop,
    modeling_merge_vertices,
    modeling_move_components,
    modeling_separate,
    modeling_set_pivot,
)
from maya_mcp.tools.nodes import nodes_create, nodes_delete, nodes_info, nodes_list
from maya_mcp.tools.scene import scene_info, scene_new, scene_redo, scene_undo
from maya_mcp.tools.scripts import script_execute, script_list, script_run
from maya_mcp.tools.selection import selection_clear, selection_get, selection_set
from maya_mcp.tools.shading import (
    shading_assign_material,
    shading_create_material,
    shading_set_material_color,
)
from maya_mcp.tools.viewport import viewport_capture

__all__ = [
    "attributes_get",
    "attributes_set",
    "connections_connect",
    "connections_disconnect",
    "connections_get",
    "connections_history",
    "connections_list",
    "curve_cvs",
    "curve_info",
    "health_check",
    "maya_connect",
    "maya_disconnect",
    "modeling_bevel",
    "modeling_boolean",
    "modeling_bridge",
    "modeling_center_pivot",
    "modeling_combine",
    "modeling_create_polygon_primitive",
    "modeling_delete_faces",
    "modeling_delete_history",
    "modeling_extrude_faces",
    "modeling_freeze_transforms",
    "modeling_insert_edge_loop",
    "modeling_merge_vertices",
    "modeling_move_components",
    "modeling_separate",
    "modeling_set_pivot",
    "nodes_create",
    "nodes_delete",
    "nodes_info",
    "nodes_list",
    "scene_info",
    "scene_new",
    "scene_redo",
    "scene_undo",
    "script_execute",
    "script_list",
    "script_run",
    "selection_clear",
    "selection_get",
    "selection_set",
    "shading_assign_material",
    "shading_create_material",
    "shading_set_material_color",
    "viewport_capture",
]
