"""Client-compatibility tests for MCP ``tools/list`` metadata."""

from __future__ import annotations

import asyncio

from mcp.types import ListToolsResult, Tool

AnnotationExpectation = tuple[bool, bool, bool, bool]


def _build_expected_tool_annotations() -> dict[str, AnnotationExpectation]:
    """Return expected annotation hints for every advertised tool."""
    expectations: dict[str, AnnotationExpectation] = {}

    read_only_idempotent = (
        True,
        False,
        True,
        False,
    )
    write_idempotent = (
        False,
        False,
        True,
        False,
    )
    write_non_idempotent = (
        False,
        False,
        False,
        False,
    )
    destructive_non_idempotent = (
        False,
        True,
        False,
        False,
    )

    for name in (
        "health.check",
        "scene.info",
        "nodes.list",
        "nodes.info",
        "attributes.get",
        "connections.list",
        "connections.get",
        "connections.history",
        "selection.get",
        "selection.get_components",
        "mesh.info",
        "mesh.vertices",
        "mesh.evaluate",
        "viewport.capture",
        "curve.info",
        "curve.cvs",
        "skin.influences",
        "skin.weights.get",
        "script.list",
        "animation.get_time_range",
        "animation.get_keyframes",
    ):
        expectations[name] = read_only_idempotent

    for name in (
        "maya.connect",
        "maya.disconnect",
        "scene.new",
        "scene.open",
        "scene.save",
        "scene.save_as",
        "scene.export",
        "nodes.delete",
        "nodes.rename",
        "nodes.parent",
        "attributes.set",
        "connections.connect",
        "connections.disconnect",
        "selection.clear",
        "modeling.freeze_transforms",
        "modeling.delete_history",
        "modeling.center_pivot",
        "modeling.set_pivot",
        "shading.set_material_color",
        "animation.set_time",
        "animation.set_time_range",
    ):
        expectations[name] = write_idempotent

    for name in (
        "scene.undo",
        "scene.redo",
        "scene.import",
        "nodes.create",
        "nodes.duplicate",
        "selection.set",
        "selection.set_components",
        "selection.convert_components",
        "modeling.create_polygon_primitive",
        "modeling.extrude_faces",
        "modeling.boolean",
        "modeling.combine",
        "modeling.separate",
        "modeling.merge_vertices",
        "modeling.bevel",
        "modeling.bridge",
        "modeling.insert_edge_loop",
        "modeling.delete_faces",
        "modeling.move_components",
        "shading.create_material",
        "shading.assign_material",
        "skin.bind",
        "skin.unbind",
        "skin.weights.set",
        "skin.copy_weights",
        "animation.set_keyframe",
    ):
        expectations[name] = write_non_idempotent

    for name in ("script.execute", "script.run", "animation.delete_keyframes"):
        expectations[name] = destructive_non_idempotent

    return expectations


EXPECTED_TOOL_ANNOTATIONS = _build_expected_tool_annotations()
EXPECTED_TOOL_NAMES = frozenset(EXPECTED_TOOL_ANNOTATIONS)


def _list_tools() -> ListToolsResult:
    """Return the serialized MCP ``tools/list`` response."""
    from maya_mcp.server import mcp

    tools = [tool.to_mcp_tool() for tool in asyncio.run(mcp.list_tools())]
    return ListToolsResult(nextCursor=None, tools=tools)


def _tool_map() -> dict[str, Tool]:
    """Return the advertised tools keyed by name."""
    result = _list_tools()
    tool_map = {tool.name: tool for tool in result.tools}

    assert len(tool_map) == len(result.tools)
    return tool_map


def test_tools_list_returns_expected_names() -> None:
    """tools/list should advertise the full expected tool surface."""
    result = _list_tools()
    names = {tool.name for tool in result.tools}

    assert result.nextCursor is None
    assert len(result.tools) == len(names) == len(EXPECTED_TOOL_NAMES)
    assert names == EXPECTED_TOOL_NAMES


def test_tools_list_exposes_schemas_and_annotations_for_every_tool() -> None:
    """Every advertised tool should include client-usable schema metadata."""
    tool_map = _tool_map()

    for tool_name, expected_annotations in EXPECTED_TOOL_ANNOTATIONS.items():
        tool = tool_map[tool_name]

        assert tool.description, tool_name

        input_schema = tool.inputSchema
        assert isinstance(input_schema, dict), tool_name
        assert input_schema.get("type") == "object", tool_name
        assert isinstance(input_schema.get("properties", {}), dict), tool_name
        assert input_schema.get("additionalProperties") is False, tool_name

        output_schema = tool.outputSchema
        assert isinstance(output_schema, dict), tool_name
        assert output_schema.get("type") == "object", tool_name
        assert isinstance(output_schema.get("properties", {}), dict), tool_name

        annotations = tool.annotations
        assert annotations is not None, tool_name
        assert annotations.readOnlyHint == expected_annotations[0], tool_name
        assert annotations.destructiveHint == expected_annotations[1], tool_name
        assert annotations.idempotentHint == expected_annotations[2], tool_name
        assert annotations.openWorldHint == expected_annotations[3], tool_name


def test_tools_list_serializes_expected_metadata_for_representative_tools() -> None:
    """Representative tools should retain critical client-facing schema details."""
    tool_map = _tool_map()

    health_check = tool_map["health.check"]
    assert health_check.inputSchema == {
        "additionalProperties": False,
        "properties": {},
        "type": "object",
    }

    nodes_list = tool_map["nodes.list"]
    assert "max 500 nodes" in nodes_list.description
    assert nodes_list.inputSchema["properties"]["pattern"]["default"] == "*"
    assert nodes_list.inputSchema["properties"]["long_names"]["default"] is False
    assert nodes_list.inputSchema["properties"]["limit"]["default"] == 500
    assert nodes_list.inputSchema["properties"]["node_type"]["anyOf"] == [
        {"type": "string"},
        {"type": "null"},
    ]

    script_run = tool_map["script.run"]
    assert script_run.inputSchema["required"] == ["code"]
    assert script_run.inputSchema["properties"]["language"]["default"] == "python"
    assert script_run.inputSchema["properties"]["language"]["enum"] == ["python", "mel"]

    viewport_capture = tool_map["viewport.capture"]
    assert viewport_capture.inputSchema["properties"]["format"]["default"] == "jpeg"
    assert viewport_capture.inputSchema["properties"]["format"]["enum"] == ["jpeg", "png"]
    assert viewport_capture.inputSchema["properties"]["offscreen"]["default"] is False
    assert viewport_capture.inputSchema["properties"]["show_ornaments"]["default"] is True
    assert set(viewport_capture.outputSchema["required"]) == {
        "format",
        "mime_type",
        "width",
        "height",
        "frame",
        "panel",
        "size_bytes",
    }
