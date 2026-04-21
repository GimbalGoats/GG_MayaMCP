"""Tests for FastMCP tool output schemas."""

from __future__ import annotations

import asyncio


def test_remaining_tools_expose_specific_output_schemas() -> None:
    """Recently typed tool families should not regress to generic object schemas."""
    from maya_mcp.server import mcp

    expected_fields = {
        "connections.list": {"node", "connections", "count", "errors"},
        "connections.get": {"node", "attributes", "count", "errors"},
        "connections.connect": {"connected", "source", "destination", "disconnected", "error"},
        "connections.disconnect": {"disconnected", "count", "error"},
        "connections.history": {"node", "history", "count", "errors"},
        "animation.set_time": {"time", "errors"},
        "animation.get_time_range": {
            "current_time",
            "min_time",
            "max_time",
            "animation_start",
            "animation_end",
            "fps",
            "errors",
        },
        "animation.set_time_range": {
            "min_time",
            "max_time",
            "animation_start",
            "animation_end",
            "errors",
        },
        "animation.set_keyframe": {"node", "attributes", "time", "keyframe_count", "errors"},
        "animation.get_keyframes": {
            "node",
            "keyframes",
            "attribute_count",
            "total_keyframe_count",
            "errors",
        },
        "animation.delete_keyframes": {
            "node",
            "deleted_count",
            "attributes",
            "time_range",
            "errors",
        },
        "modeling.create_polygon_primitive": {
            "transform",
            "shape",
            "constructor_node",
            "primitive_type",
            "vertex_count",
            "face_count",
            "errors",
        },
        "modeling.extrude_faces": {"node", "faces_extruded", "new_face_count", "errors"},
        "modeling.boolean": {"result_mesh", "operation", "vertex_count", "face_count", "errors"},
        "modeling.combine": {
            "result_mesh",
            "source_meshes",
            "vertex_count",
            "face_count",
            "errors",
        },
        "modeling.separate": {"source_mesh", "result_meshes", "count", "errors"},
        "modeling.merge_vertices": {
            "mesh",
            "vertices_merged",
            "vertex_count_before",
            "vertex_count_after",
            "errors",
        },
        "modeling.bevel": {
            "node",
            "components_beveled",
            "new_vertex_count",
            "new_face_count",
            "errors",
        },
        "modeling.bridge": {"node", "new_face_count", "errors"},
        "modeling.insert_edge_loop": {
            "node",
            "edge",
            "new_edge_count",
            "new_vertex_count",
            "errors",
        },
        "modeling.delete_faces": {"faces_deleted", "mesh", "remaining_face_count", "errors"},
        "modeling.move_components": {"components_moved", "world_space", "errors"},
        "modeling.freeze_transforms": {"frozen", "count", "errors"},
        "modeling.delete_history": {"cleaned", "count", "errors"},
        "modeling.center_pivot": {"centered", "count", "pivot_positions", "errors"},
        "modeling.set_pivot": {"node", "pivot", "world_space", "errors"},
        "shading.create_material": {"material", "shading_group", "material_type", "errors"},
        "shading.assign_material": {"assigned", "material", "shading_group", "errors"},
        "shading.set_material_color": {"material", "attribute", "color", "errors"},
        "script.list": {"scripts", "count", "directories", "errors"},
        "script.execute": {"success", "script", "output", "errors"},
        "script.run": {"success", "output", "language", "errors"},
        "viewport.capture": {
            "format",
            "mime_type",
            "width",
            "height",
            "frame",
            "panel",
            "size_bytes",
        },
    }

    for tool_name, required_fields in expected_fields.items():
        tool = asyncio.run(mcp.get_tool(tool_name))
        assert tool is not None, tool_name

        schema = tool.to_mcp_tool().outputSchema
        assert schema is not None, tool_name
        assert schema.get("type") == "object", tool_name

        properties = schema.get("properties", {})
        assert required_fields.issubset(properties.keys()), tool_name

        if tool_name != "viewport.capture":
            assert not (schema.get("additionalProperties") is True and not properties), tool_name
