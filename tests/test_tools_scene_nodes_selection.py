"""Tests for scene, nodes, and selection tools.

These tests verify the MCP tools for scene information, node listing,
and selection management work correctly with mocked transport.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from maya_mcp.tools.nodes import nodes_list
from maya_mcp.tools.scene import scene_info
from maya_mcp.tools.selection import selection_get, selection_set


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
