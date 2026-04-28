"""Client-facing MCP tool metadata.

This module contains metadata that is not part of the Python call signature but
is still visible through MCP ``tools/list``.
"""

from __future__ import annotations

from fastmcp.server.transforms import ToolTransform
from fastmcp.tools.tool_transform import ToolTransformConfig

TOOL_TITLES: dict[str, str] = {
    "health.check": "Check Maya Connection Health",
    "maya.connect": "Connect To Maya",
    "maya.disconnect": "Disconnect From Maya",
    "scene.info": "Get Scene Information",
    "scene.new": "Create New Scene",
    "scene.open": "Open Scene",
    "scene.save": "Save Scene",
    "scene.save_as": "Save Scene As",
    "scene.import": "Import Scene File",
    "scene.export": "Export Scene File",
    "scene.undo": "Undo Scene Operation",
    "scene.redo": "Redo Scene Operation",
    "nodes.list": "List Nodes",
    "nodes.create": "Create Node",
    "nodes.delete": "Delete Nodes",
    "nodes.rename": "Rename Nodes",
    "nodes.parent": "Parent Nodes",
    "nodes.duplicate": "Duplicate Nodes",
    "nodes.info": "Get Node Information",
    "attributes.get": "Get Attributes",
    "attributes.set": "Set Attributes",
    "connections.list": "List Connections",
    "connections.get": "Get Connection Details",
    "connections.connect": "Connect Attributes",
    "connections.disconnect": "Disconnect Attributes",
    "connections.history": "List Node History",
    "selection.get": "Get Selection",
    "selection.set": "Set Selection",
    "selection.clear": "Clear Selection",
    "selection.set_components": "Set Component Selection",
    "selection.get_components": "Get Component Selection",
    "selection.convert_components": "Convert Component Selection",
    "mesh.info": "Get Mesh Information",
    "mesh.vertices": "Get Mesh Vertices",
    "mesh.evaluate": "Evaluate Mesh Topology",
    "viewport.capture": "Capture Viewport",
    "modeling.create_polygon_primitive": "Create Polygon Primitive",
    "modeling.extrude_faces": "Extrude Faces",
    "modeling.boolean": "Run Mesh Boolean",
    "modeling.combine": "Combine Meshes",
    "modeling.separate": "Separate Mesh",
    "modeling.merge_vertices": "Merge Vertices",
    "modeling.bevel": "Bevel Components",
    "modeling.bridge": "Bridge Edge Loops",
    "modeling.insert_edge_loop": "Insert Edge Loop",
    "modeling.delete_faces": "Delete Faces",
    "modeling.move_components": "Move Components",
    "modeling.freeze_transforms": "Freeze Transforms",
    "modeling.delete_history": "Delete Construction History",
    "modeling.center_pivot": "Center Pivot",
    "modeling.set_pivot": "Set Pivot",
    "shading.create_material": "Create Material",
    "shading.assign_material": "Assign Material",
    "shading.set_material_color": "Set Material Color",
    "skin.bind": "Bind Skin",
    "skin.unbind": "Unbind Skin",
    "skin.influences": "List Skin Influences",
    "skin.weights.get": "Get Skin Weights",
    "skin.weights.set": "Set Skin Weights",
    "skin.copy_weights": "Copy Skin Weights",
    "animation.set_time": "Set Current Time",
    "animation.get_time_range": "Get Time Range",
    "animation.set_time_range": "Set Time Range",
    "animation.set_keyframe": "Set Keyframe",
    "animation.get_keyframes": "Get Keyframes",
    "animation.delete_keyframes": "Delete Keyframes",
    "curve.info": "Get Curve Information",
    "curve.cvs": "Get Curve CVs",
    "script.list": "List Approved Scripts",
    "script.execute": "Execute Approved Script",
    "script.run": "Run Raw Script Code",
}


def build_tool_title_transform() -> ToolTransform:
    """Return a FastMCP transform that adds display titles to all tools."""
    return ToolTransform(
        {name: ToolTransformConfig(title=title) for name, title in TOOL_TITLES.items()}
    )
