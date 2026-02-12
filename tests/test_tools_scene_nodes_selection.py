"""Tests for scene, nodes, and selection tools.

These tests verify the MCP tools for scene information, node listing,
and selection management work correctly with mocked transport.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from maya_mcp.tools.nodes import (
    _build_info_command,
    nodes_create,
    nodes_delete,
    nodes_info,
    nodes_list,
)
from maya_mcp.tools.scene import scene_info, scene_redo, scene_undo
from maya_mcp.tools.selection import selection_clear, selection_get, selection_set


class TestSceneInfo:
    """Tests for the scene.info tool."""

    def test_scene_info_untitled(self) -> None:
        """Scene info returns None file_path for untitled scene."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "scene_name": None,
                "modified": False,
                "time_unit": "film",
                "min_time": 1.0,
                "max_time": 120.0,
                "up_axis": "y",
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            result = scene_info()

        assert result["file_path"] is None
        assert result["modified"] is False
        assert result["fps"] == 24.0
        assert result["frame_range"] == [1.0, 120.0]
        assert result["up_axis"] == "y"

    def test_scene_info_with_file(self) -> None:
        """Scene info returns correct file path when scene is saved."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "scene_name": "C:/Projects/test_scene.ma",
                "modified": True,
                "time_unit": "ntsc",
                "min_time": 0.0,
                "max_time": 100.0,
                "up_axis": "z",
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            result = scene_info()

        assert result["file_path"] == "C:/Projects/test_scene.ma"
        assert result["modified"] is True
        assert result["fps"] == 30.0  # ntsc = 30 fps
        assert result["frame_range"] == [0.0, 100.0]
        assert result["up_axis"] == "z"

    def test_scene_info_various_time_units(self) -> None:
        """Scene info correctly converts various time units to FPS."""
        test_cases = [
            ("film", 24.0),
            ("ntsc", 30.0),
            ("pal", 25.0),
            ("game", 15.0),
            ("show", 48.0),
        ]

        for time_unit, expected_fps in test_cases:
            mock_client = MagicMock()
            mock_response = json.dumps(
                {
                    "scene_name": None,
                    "modified": False,
                    "time_unit": time_unit,
                    "min_time": 1.0,
                    "max_time": 24.0,
                    "up_axis": "y",
                }
            )
            mock_client.execute.return_value = mock_response

            with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
                result = scene_info()

            assert result["fps"] == expected_fps, f"Failed for time_unit={time_unit}"


class TestSceneUndo:
    """Tests for the scene.undo tool."""

    def test_scene_undo_success(self) -> None:
        """Undo succeeds when undo queue is not empty."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": True,
                "undone": "setAttr pCube1.translateX",
                "can_undo": True,
                "can_redo": True,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            result = scene_undo()

        assert result["success"] is True
        assert result["undone"] == "setAttr pCube1.translateX"
        assert result["can_undo"] is True
        assert result["can_redo"] is True

    def test_scene_undo_nothing_to_undo(self) -> None:
        """Undo fails when undo queue is empty."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": False,
                "undone": None,
                "can_undo": False,
                "can_redo": False,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            result = scene_undo()

        assert result["success"] is False
        assert result["undone"] is None
        assert result["can_undo"] is False

    def test_scene_undo_result_shape(self) -> None:
        """Undo result includes all required fields."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": True,
                "undone": "createNode",
                "can_undo": False,
                "can_redo": True,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            result = scene_undo()

        assert "success" in result
        assert "undone" in result
        assert "can_undo" in result
        assert "can_redo" in result
        assert isinstance(result["success"], bool)
        assert isinstance(result["can_undo"], bool)
        assert isinstance(result["can_redo"], bool)


class TestSceneRedo:
    """Tests for the scene.redo tool."""

    def test_scene_redo_success(self) -> None:
        """Redo succeeds when redo queue is not empty."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": True,
                "redone": "setAttr pCube1.translateX",
                "can_undo": True,
                "can_redo": False,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            result = scene_redo()

        assert result["success"] is True
        assert result["redone"] == "setAttr pCube1.translateX"
        assert result["can_undo"] is True
        assert result["can_redo"] is False

    def test_scene_redo_nothing_to_redo(self) -> None:
        """Redo fails when redo queue is empty."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": False,
                "redone": None,
                "can_undo": True,
                "can_redo": False,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            result = scene_redo()

        assert result["success"] is False
        assert result["redone"] is None
        assert result["can_redo"] is False

    def test_scene_redo_result_shape(self) -> None:
        """Redo result includes all required fields."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": True,
                "redone": "delete",
                "can_undo": True,
                "can_redo": True,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            result = scene_redo()

        assert "success" in result
        assert "redone" in result
        assert "can_undo" in result
        assert "can_redo" in result
        assert isinstance(result["success"], bool)
        assert isinstance(result["can_undo"], bool)
        assert isinstance(result["can_redo"], bool)


class TestNodesList:
    """Tests for the nodes.list tool."""

    def test_nodes_list_all(self) -> None:
        """List all nodes without filters."""
        mock_client = MagicMock()
        mock_response = json.dumps(["pCube1", "pSphere1", "persp", "top", "front", "side"])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_list()

        assert result["count"] == 6
        assert "pCube1" in result["nodes"]
        assert "pSphere1" in result["nodes"]

    def test_nodes_list_by_type(self) -> None:
        """List nodes filtered by type."""
        mock_client = MagicMock()
        mock_response = json.dumps(["pCubeShape1", "pSphereShape1"])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_list(node_type="mesh")

        assert result["count"] == 2
        assert "pCubeShape1" in result["nodes"]
        mock_client.execute.assert_called_once()
        call_arg = mock_client.execute.call_args[0][0]
        assert "type=" in call_arg

    def test_nodes_list_by_pattern(self) -> None:
        """List nodes filtered by pattern."""
        mock_client = MagicMock()
        mock_response = json.dumps(["pCube1", "pCube2", "pCube3"])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_list(pattern="pCube*")

        assert result["count"] == 3
        assert all("pCube" in node for node in result["nodes"])

    def test_nodes_list_empty(self) -> None:
        """List returns empty when no nodes match."""
        mock_client = MagicMock()
        mock_response = json.dumps([])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_list(pattern="nonexistent*")

        assert result["count"] == 0
        assert result["nodes"] == []

    def test_nodes_list_invalid_pattern(self) -> None:
        """List rejects patterns with invalid characters."""
        with pytest.raises(ValueError, match="Invalid characters"):
            nodes_list(pattern="test; rm -rf /")

    def test_nodes_list_long_names(self) -> None:
        """List returns long names when requested."""
        mock_client = MagicMock()
        mock_response = json.dumps(["|pCube1", "|group1|pSphere1"])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_list(long_names=True)

        assert result["count"] == 2
        assert "|pCube1" in result["nodes"]
        mock_client.execute.assert_called_once()
        call_arg = mock_client.execute.call_args[0][0]
        assert "long=True" in call_arg


class TestNodesCreate:
    """Tests for the nodes.create tool."""

    def test_nodes_create_simple(self) -> None:
        """Create a simple node without options."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "transform1",
                "node_type": "transform",
                "parent": None,
                "attributes_set": [],
                "attribute_errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_create("transform")

        assert result["node"] == "transform1"
        assert result["node_type"] == "transform"
        assert result["parent"] is None
        assert result["attributes_set"] == []
        assert result["attribute_errors"] is None

    def test_nodes_create_with_name(self) -> None:
        """Create a node with a specific name."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "myLocator",
                "node_type": "transform",
                "parent": None,
                "attributes_set": [],
                "attribute_errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_create("transform", name="myLocator")

        assert result["node"] == "myLocator"

    def test_nodes_create_with_parent(self) -> None:
        """Create a node under a parent."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "child1",
                "node_type": "transform",
                "parent": "group1",
                "attributes_set": [],
                "attribute_errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_create("transform", name="child1", parent="group1")

        assert result["node"] == "child1"
        assert result["parent"] == "group1"

    def test_nodes_create_with_attributes(self) -> None:
        """Create a node with initial attributes."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "myNode",
                "node_type": "transform",
                "parent": None,
                "attributes_set": ["translateX", "translateY"],
                "attribute_errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_create(
                "transform",
                name="myNode",
                attributes={"translateX": 10.0, "translateY": 5.0},
            )

        assert result["node"] == "myNode"
        assert result["attributes_set"] == ["translateX", "translateY"]
        assert result["attribute_errors"] is None

    def test_nodes_create_with_attribute_errors(self) -> None:
        """Create a node with some attribute errors."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "myNode",
                "node_type": "transform",
                "parent": None,
                "attributes_set": ["translateX"],
                "attribute_errors": {"badAttr": "Attribute 'badAttr' not found"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_create(
                "transform",
                name="myNode",
                attributes={"translateX": 10.0, "badAttr": 5.0},
            )

        assert result["node"] == "myNode"
        assert result["attributes_set"] == ["translateX"]
        assert result["attribute_errors"] is not None
        assert "badAttr" in result["attribute_errors"]

    def test_nodes_create_invalid_node_type(self) -> None:
        """Create rejects invalid node type characters."""
        with pytest.raises(ValueError, match="Invalid characters"):
            nodes_create("transform; rm -rf /")

    def test_nodes_create_invalid_name(self) -> None:
        """Create rejects invalid node name characters."""
        with pytest.raises(ValueError, match="Invalid characters"):
            nodes_create("transform", name="node; bad")

    def test_nodes_create_result_shape(self) -> None:
        """Create result includes all required fields."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "node1",
                "node_type": "transform",
                "parent": None,
                "attributes_set": [],
                "attribute_errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_create("transform")

        assert "node" in result
        assert "node_type" in result
        assert "parent" in result
        assert "attributes_set" in result
        assert "attribute_errors" in result


class TestNodesInfo:
    """Tests for the nodes.info tool."""

    def test_nodes_info_summary(self) -> None:
        """Info with summary category returns node type, parent, children count."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "info_category": "summary",
                "exists": True,
                "node_type": "transform",
                "parent": "group1",
                "children_count": 1,
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_info("pCube1", info_category="summary")

        assert result["node"] == "pCube1"
        assert result["info_category"] == "summary"
        assert result["exists"] is True
        assert result["node_type"] == "transform"
        assert result["parent"] == "group1"
        assert result["children_count"] == 1
        assert result["errors"] is None

    def test_nodes_info_transform(self) -> None:
        """Info with transform category returns position, rotation, scale."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "info_category": "transform",
                "exists": True,
                "node_type": "transform",
                "translateX": 10.0,
                "translateY": 5.0,
                "translateZ": 0.0,
                "rotateX": 0.0,
                "rotateY": 45.0,
                "rotateZ": 0.0,
                "scaleX": 1.0,
                "scaleY": 1.0,
                "scaleZ": 1.0,
                "visibility": True,
                "translate": [10.0, 5.0, 0.0],
                "rotate": [0.0, 45.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_info("pCube1", info_category="transform")

        assert result["translate"] == [10.0, 5.0, 0.0]
        assert result["rotate"] == [0.0, 45.0, 0.0]
        assert result["scale"] == [1.0, 1.0, 1.0]
        assert result["visibility"] is True
        assert result["errors"] is None

    def test_nodes_info_hierarchy(self) -> None:
        """Info with hierarchy category returns parent, children, full path."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "info_category": "hierarchy",
                "exists": True,
                "node_type": "transform",
                "parent": "|group1",
                "children": ["pCubeShape1"],
                "full_path": "|group1|pCube1",
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_info("pCube1", info_category="hierarchy")

        assert result["parent"] == "|group1"
        assert result["children"] == ["pCubeShape1"]
        assert result["full_path"] == "|group1|pCube1"
        assert result["errors"] is None

    def test_nodes_info_attributes(self) -> None:
        """Info with attributes category returns keyable attributes."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "info_category": "attributes",
                "exists": True,
                "node_type": "transform",
                "keyable_attributes": {
                    "translateX": 0.0,
                    "translateY": 0.0,
                    "translateZ": 0.0,
                    "visibility": True,
                },
                "keyable_count": 4,
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_info("pCube1", info_category="attributes")

        assert result["keyable_count"] == 4
        assert "translateX" in result["keyable_attributes"]
        assert result["errors"] is None

    def test_nodes_info_shape(self) -> None:
        """Info with shape category returns shape nodes."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "info_category": "shape",
                "exists": True,
                "node_type": "transform",
                "shapes": [{"name": "pCubeShape1", "type": "mesh", "connections_count": 3}],
                "shape_count": 1,
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_info("pCube1", info_category="shape")

        assert result["shape_count"] == 1
        assert result["shapes"][0]["name"] == "pCubeShape1"
        assert result["shapes"][0]["type"] == "mesh"
        assert result["errors"] is None

    def test_nodes_info_all(self) -> None:
        """Info with 'all' category returns combined data with separate parent keys."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "info_category": "all",
                "exists": True,
                "node_type": "transform",
                # summary sets parent (short name)
                "parent": "group1",
                "children_count": 1,
                "translate": [0.0, 0.0, 0.0],
                "rotate": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "visibility": True,
                # hierarchy sets parent_full_path (full DAG path) in "all" mode
                "parent_full_path": "|group1",
                "children": ["pCubeShape1"],
                "full_path": "|group1|pCube1",
                "keyable_attributes": {"translateX": 0.0},
                "keyable_count": 1,
                "shapes": [{"name": "pCubeShape1", "type": "mesh", "connections_count": 2}],
                "shape_count": 1,
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_info("pCube1", info_category="all")

        assert result["info_category"] == "all"
        assert result["exists"] is True
        # Summary fields — parent is short name
        assert result["parent"] == "group1"
        assert "children_count" in result
        # Transform fields
        assert "translate" in result
        # Hierarchy fields — parent_full_path is full DAG path (no collision)
        assert result["parent_full_path"] == "|group1"
        assert "full_path" in result
        # Attribute fields
        assert "keyable_attributes" in result
        # Shape fields
        assert "shapes" in result
        assert result["errors"] is None

    def test_nodes_info_nonexistent_node(self) -> None:
        """Info for non-existent node returns exists=False with error."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "nonexistent",
                "info_category": "summary",
                "exists": False,
                "errors": {"_node": "Node 'nonexistent' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_info("nonexistent")

        assert result["exists"] is False
        assert result["errors"] is not None
        assert "_node" in result["errors"]

    def test_nodes_info_invalid_category(self) -> None:
        """Info rejects invalid info_category."""
        with pytest.raises(ValueError, match="Invalid info_category"):
            nodes_info("pCube1", info_category="invalid")

    def test_nodes_info_invalid_node_name(self) -> None:
        """Info rejects invalid node name characters."""
        with pytest.raises(ValueError, match="Invalid characters"):
            nodes_info("pCube1; rm -rf /")

    def test_nodes_info_default_category(self) -> None:
        """Info defaults to summary category."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "info_category": "summary",
                "exists": True,
                "node_type": "transform",
                "parent": None,
                "children_count": 0,
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_info("pCube1")

        assert result["info_category"] == "summary"

    def test_nodes_info_result_shape(self) -> None:
        """Info result always includes core fields."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "info_category": "summary",
                "exists": True,
                "node_type": "transform",
                "parent": None,
                "children_count": 0,
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_info("pCube1")

        assert "node" in result
        assert "info_category" in result
        assert "exists" in result
        assert "errors" in result


class TestNodesInfoCommand:
    """Tests for the generated Maya command string of nodes_info.

    These tests verify the static Maya script is correctly structured
    and includes/excludes the right conditional sections per category.
    """

    def test_command_has_top_level_try_except(self) -> None:
        """Generated command wraps everything in top-level try/except."""
        cmd = _build_info_command('"pCube1"', '"summary"')
        assert "except Exception as _top_err:" in cmd
        assert 'result["errors"]["_exception"]' in cmd

    def test_command_always_prints_json(self) -> None:
        """Generated command always ends with print(json.dumps(result))."""
        cmd = _build_info_command('"pCube1"', '"summary"')
        assert "print(json.dumps(result))" in cmd

    def test_command_summary_includes_parent_children(self) -> None:
        """Summary category command includes parent and children queries."""
        cmd = _build_info_command('"pCube1"', '"summary"')
        assert 'category in ("summary", "all")' in cmd
        assert 'result["parent"]' in cmd
        assert 'result["children_count"]' in cmd

    def test_command_transform_includes_attributes(self) -> None:
        """Transform category command includes translate/rotate/scale."""
        cmd = _build_info_command('"pCube1"', '"transform"')
        assert 'category in ("transform", "all")' in cmd
        assert '"translateX"' in cmd
        assert 'result["translate"]' in cmd
        assert 'result["rotate"]' in cmd
        assert 'result["scale"]' in cmd

    def test_command_hierarchy_uses_full_path(self) -> None:
        """Hierarchy category command uses fullPath=True for parent."""
        cmd = _build_info_command('"pCube1"', '"hierarchy"')
        assert 'category in ("hierarchy", "all")' in cmd
        assert "fullPath=True" in cmd
        assert 'result["full_path"]' in cmd

    def test_command_all_mode_separates_parent_keys(self) -> None:
        """In 'all' mode, hierarchy writes parent_full_path to avoid collision."""
        cmd = _build_info_command('"pCube1"', '"all"')
        assert 'result["parent_full_path"]' in cmd
        # summary still sets result["parent"] (short name)
        assert 'result["parent"]' in cmd

    def test_command_attributes_has_truncation_limit(self) -> None:
        """Attributes category command limits number of attributes returned."""
        cmd = _build_info_command('"pCube1"', '"attributes"')
        assert 'category in ("attributes", "all")' in cmd
        assert "_truncated" in cmd
        assert "keyable_truncated" in cmd
        assert "keyable_total_count" in cmd

    def test_command_shape_includes_connections(self) -> None:
        """Shape category command queries shape type and connections."""
        cmd = _build_info_command('"pCube1"', '"shape"')
        assert 'category in ("shape", "all")' in cmd
        assert "listRelatives(node, shapes=True)" in cmd
        assert "connections_count" in cmd

    def test_command_escapes_node_name(self) -> None:
        """Command properly embeds escaped node name."""
        cmd = _build_info_command('"my|node"', '"summary"')
        assert 'node = "my|node"' in cmd

    def test_command_normalizes_compound_attrs(self) -> None:
        """Attributes command unwraps [(x,y,z)] tuples to [x,y,z]."""
        cmd = _build_info_command('"pCube1"', '"attributes"')
        assert "isinstance(_val, list)" in cmd
        assert "isinstance(_val[0], tuple)" in cmd
        assert "list(_val[0])" in cmd


class TestNodesDelete:
    """Tests for the nodes.delete tool."""

    def test_nodes_delete_single(self) -> None:
        """Delete a single node."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "deleted": ["pCube1"],
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_delete(["pCube1"])

        assert result["deleted"] == ["pCube1"]
        assert result["count"] == 1
        assert result["errors"] is None

    def test_nodes_delete_multiple(self) -> None:
        """Delete multiple nodes."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "deleted": ["pCube1", "pSphere1"],
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_delete(["pCube1", "pSphere1"])

        assert result["deleted"] == ["pCube1", "pSphere1"]
        assert result["count"] == 2
        assert result["errors"] is None

    def test_nodes_delete_with_hierarchy(self) -> None:
        """Delete node with hierarchy flag."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "deleted": ["group1"],
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_delete(["group1"], hierarchy=True)

        assert result["deleted"] == ["group1"]
        mock_client.execute.assert_called_once()
        call_arg = mock_client.execute.call_args[0][0]
        assert "delete_hierarchy = True" in call_arg

    def test_nodes_delete_partial_failure(self) -> None:
        """Delete with some nodes failing."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "deleted": ["pCube1"],
                "errors": {"pSphere1": "Node 'pSphere1' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_delete(["pCube1", "pSphere1"])

        assert result["deleted"] == ["pCube1"]
        assert result["count"] == 1
        assert result["errors"] is not None
        assert "pSphere1" in result["errors"]

    def test_nodes_delete_empty_list(self) -> None:
        """Delete rejects empty nodes list."""
        with pytest.raises(ValueError, match="cannot be empty"):
            nodes_delete([])

    def test_nodes_delete_invalid_name(self) -> None:
        """Delete rejects invalid node name characters."""
        with pytest.raises(ValueError, match="Invalid characters"):
            nodes_delete(["node; bad"])

    def test_nodes_delete_result_shape(self) -> None:
        """Delete result includes all required fields."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "deleted": ["node1"],
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_delete(["node1"])

        assert "deleted" in result
        assert "count" in result
        assert "errors" in result
        assert isinstance(result["deleted"], list)
        assert isinstance(result["count"], int)


class TestSelectionGet:
    """Tests for the selection.get tool."""

    def test_selection_get_with_items(self) -> None:
        """Get selection returns selected nodes."""
        mock_client = MagicMock()
        mock_response = json.dumps(["pCube1", "pSphere1"])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_get()

        assert result["count"] == 2
        assert result["selection"] == ["pCube1", "pSphere1"]

    def test_selection_get_empty(self) -> None:
        """Get selection returns empty when nothing selected."""
        mock_client = MagicMock()
        mock_response = json.dumps([])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_get()

        assert result["count"] == 0
        assert result["selection"] == []


class TestSelectionSet:
    """Tests for the selection.set tool."""

    def test_selection_set_replace(self) -> None:
        """Set selection replaces current selection."""
        mock_client = MagicMock()
        mock_response = json.dumps(["pCube1", "pSphere1"])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_set(["pCube1", "pSphere1"])

        assert result["count"] == 2
        assert "pCube1" in result["selection"]
        mock_client.execute.assert_called_once()
        call_arg = mock_client.execute.call_args[0][0]
        assert "replace=True" in call_arg

    def test_selection_set_add(self) -> None:
        """Set selection adds to existing selection."""
        mock_client = MagicMock()
        mock_response = json.dumps(["pCube1", "pSphere1", "pCone1"])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_set(["pCone1"], add=True)

        assert result["count"] == 3
        mock_client.execute.assert_called_once()
        call_arg = mock_client.execute.call_args[0][0]
        assert "add=True" in call_arg

    def test_selection_set_deselect(self) -> None:
        """Set selection removes from current selection."""
        mock_client = MagicMock()
        mock_response = json.dumps(["pSphere1"])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_set(["pCube1"], deselect=True)

        assert result["count"] == 1
        assert "pSphere1" in result["selection"]
        mock_client.execute.assert_called_once()
        call_arg = mock_client.execute.call_args[0][0]
        assert "deselect=True" in call_arg

    def test_selection_set_empty_nodes(self) -> None:
        """Set selection rejects empty nodes list."""
        with pytest.raises(ValueError, match="cannot be empty"):
            selection_set([])

    def test_selection_set_invalid_node_name(self) -> None:
        """Set selection rejects invalid node names."""
        with pytest.raises(ValueError, match="Invalid"):
            selection_set(["valid_node", ""])

    def test_selection_set_malicious_node_name(self) -> None:
        """Set selection rejects node names with shell metacharacters."""
        with pytest.raises(ValueError, match="Invalid characters"):
            selection_set(["pCube1; rm -rf /"])

    def test_selection_set_both_add_and_deselect(self) -> None:
        """Set selection rejects both add and deselect flags."""
        with pytest.raises(ValueError, match="Cannot specify both"):
            selection_set(["pCube1"], add=True, deselect=True)


class TestSelectionClear:
    """Tests for the selection.clear tool."""

    def test_selection_clear_success(self) -> None:
        """Clear selection returns empty selection."""
        mock_client = MagicMock()
        mock_response = json.dumps([])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_clear()

        assert result["count"] == 0
        assert result["selection"] == []
        mock_client.execute.assert_called_once()
        call_arg = mock_client.execute.call_args[0][0]
        assert "clear=True" in call_arg

    def test_selection_clear_result_shape(self) -> None:
        """Clear selection result includes all required fields."""
        mock_client = MagicMock()
        mock_response = json.dumps([])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_clear()

        assert "selection" in result
        assert "count" in result
        assert isinstance(result["selection"], list)
        assert isinstance(result["count"], int)
        assert result["count"] == len(result["selection"])


class TestResultShapes:
    """Tests for result shape compliance."""

    def test_scene_info_result_shape(self) -> None:
        """Scene info result includes all required fields."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "scene_name": None,
                "modified": False,
                "time_unit": "film",
                "min_time": 1.0,
                "max_time": 24.0,
                "up_axis": "y",
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            result = scene_info()

        assert "file_path" in result
        assert "modified" in result
        assert "fps" in result
        assert "frame_range" in result
        assert "up_axis" in result
        assert isinstance(result["frame_range"], list)
        assert len(result["frame_range"]) == 2

    def test_nodes_list_result_shape(self) -> None:
        """Nodes list result includes all required fields."""
        mock_client = MagicMock()
        mock_response = json.dumps(["node1", "node2"])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_list()

        assert "nodes" in result
        assert "count" in result
        assert isinstance(result["nodes"], list)
        assert isinstance(result["count"], int)
        assert result["count"] == len(result["nodes"])

    def test_selection_get_result_shape(self) -> None:
        """Selection get result includes all required fields."""
        mock_client = MagicMock()
        mock_response = json.dumps(["node1"])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_get()

        assert "selection" in result
        assert "count" in result
        assert isinstance(result["selection"], list)
        assert isinstance(result["count"], int)
        assert result["count"] == len(result["selection"])

    def test_selection_set_result_shape(self) -> None:
        """Selection set result includes all required fields."""
        mock_client = MagicMock()
        mock_response = json.dumps(["pCube1"])
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_set(["pCube1"])

        assert "selection" in result
        assert "count" in result
        assert isinstance(result["selection"], list)
        assert isinstance(result["count"], int)
