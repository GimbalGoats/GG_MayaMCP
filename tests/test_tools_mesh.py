"""Tests for mesh and component selection tools.

These tests verify the MCP tools for mesh queries, topology analysis,
and component-level selection work correctly with mocked transport.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from maya_mcp.tools.mesh import (
    mesh_evaluate,
    mesh_info,
    mesh_vertices,
)
from maya_mcp.tools.selection import (
    selection_convert_components,
    selection_get_components,
    selection_set_components,
)


class TestMeshInfo:
    """Tests for the mesh.info tool."""

    def test_mesh_info_success(self) -> None:
        """Mesh info returns correct statistics for a mesh."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "exists": True,
                "is_mesh": True,
                "shape": "pCubeShape1",
                "vertex_count": 8,
                "face_count": 6,
                "edge_count": 12,
                "uv_count": 8,
                "uv_sets": ["map1"],
                "has_uvs": True,
                "bounding_box": [-0.5, -0.5, -0.5, 0.5, 0.5, 0.5],
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.mesh.get_client", return_value=mock_client):
            result = mesh_info("pCube1")

        assert result["exists"] is True
        assert result["is_mesh"] is True
        assert result["vertex_count"] == 8
        assert result["face_count"] == 6
        assert result["edge_count"] == 12
        assert result["has_uvs"] is True
        assert result["bounding_box"] == [-0.5, -0.5, -0.5, 0.5, 0.5, 0.5]
        assert result["errors"] is None

    def test_mesh_info_nonexistent_node(self) -> None:
        """Mesh info returns error for nonexistent node."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "nonexistent",
                "exists": False,
                "is_mesh": False,
                "errors": {"_node": "Node 'nonexistent' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.mesh.get_client", return_value=mock_client):
            result = mesh_info("nonexistent")

        assert result["exists"] is False
        assert result["is_mesh"] is False
        assert result["errors"]["_node"] == "Node 'nonexistent' does not exist"

    def test_mesh_info_not_a_mesh(self) -> None:
        """Mesh info returns error for non-mesh node."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "camera1",
                "exists": True,
                "is_mesh": False,
                "errors": {"_mesh": "Node is not a mesh (type: camera)"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.mesh.get_client", return_value=mock_client):
            result = mesh_info("camera1")

        assert result["exists"] is True
        assert result["is_mesh"] is False
        assert "not a mesh" in result["errors"]["_mesh"]

    def test_mesh_info_invalid_node_name(self) -> None:
        """Mesh info raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            mesh_info("pCube1; rm -rf /")


class TestMeshVertices:
    """Tests for the mesh.vertices tool."""

    def test_mesh_vertices_success(self) -> None:
        """Mesh vertices returns correct positions."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "exists": True,
                "is_mesh": True,
                "shape": "pCubeShape1",
                "vertex_count": 8,
                "vertices": [
                    [-0.5, -0.5, -0.5],
                    [0.5, -0.5, -0.5],
                    [0.5, 0.5, -0.5],
                    [-0.5, 0.5, -0.5],
                ],
                "offset": 0,
                "count": 4,
                "truncated": True,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.mesh.get_client", return_value=mock_client):
            result = mesh_vertices("pCube1", offset=0, limit=4)

        assert result["exists"] is True
        assert result["vertex_count"] == 8
        assert len(result["vertices"]) == 4
        assert result["offset"] == 0
        assert result["count"] == 4
        assert result["truncated"] is True

    def test_mesh_vertices_with_offset(self) -> None:
        """Mesh vertices respects offset parameter."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "exists": True,
                "is_mesh": True,
                "vertex_count": 8,
                "vertices": [
                    [-0.5, 0.5, -0.5],
                    [0.5, 0.5, -0.5],
                ],
                "offset": 4,
                "count": 2,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.mesh.get_client", return_value=mock_client):
            result = mesh_vertices("pCube1", offset=4, limit=2)

        assert result["offset"] == 4
        assert result["count"] == 2

    def test_mesh_vertices_negative_offset_raises_error(self) -> None:
        """Mesh vertices raises ValueError for negative offset."""
        with pytest.raises(ValueError, match="offset must be non-negative"):
            mesh_vertices("pCube1", offset=-1)

    def test_mesh_vertices_invalid_node_name(self) -> None:
        """Mesh vertices raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            mesh_vertices("pCube1|bad", offset=0)


class TestMeshEvaluate:
    """Tests for the mesh.evaluate tool."""

    def test_mesh_evaluate_clean_mesh(self) -> None:
        """Mesh evaluate returns clean for valid mesh."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "exists": True,
                "is_mesh": True,
                "is_clean": True,
                "non_manifold_edges": [],
                "non_manifold_count": 0,
                "lamina_faces": [],
                "lamina_count": 0,
                "holes": [],
                "hole_count": 0,
                "border_edges": ["pCubeShape1.e[0]", "pCubeShape1.e[1]"],
                "border_count": 2,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.mesh.get_client", return_value=mock_client):
            result = mesh_evaluate("pCube1")

        assert result["is_clean"] is True
        assert result["non_manifold_count"] == 0
        assert result["lamina_count"] == 0
        assert result["hole_count"] == 0

    def test_mesh_evaluate_with_issues(self) -> None:
        """Mesh evaluate detects topology issues."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "badMesh",
                "exists": True,
                "is_mesh": True,
                "is_clean": False,
                "non_manifold_edges": ["badMeshShape.e[5]", "badMeshShape.e[6]"],
                "non_manifold_count": 2,
                "lamina_faces": [],
                "lamina_count": 0,
                "holes": ["badMeshShape.e[10]"],
                "hole_count": 1,
                "border_edges": [],
                "border_count": 0,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.mesh.get_client", return_value=mock_client):
            result = mesh_evaluate("badMesh", checks=["non_manifold", "holes"])

        assert result["is_clean"] is False
        assert result["non_manifold_count"] == 2
        assert result["hole_count"] == 1

    def test_mesh_evaluate_specific_checks(self) -> None:
        """Mesh evaluate respects specific checks parameter."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "exists": True,
                "is_mesh": True,
                "is_clean": True,
                "border_edges": ["pCubeShape1.e[0]"],
                "border_count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.mesh.get_client", return_value=mock_client):
            result = mesh_evaluate("pCube1", checks=["border"])

        assert "border_edges" in result
        assert "non_manifold_edges" not in result

    def test_mesh_evaluate_invalid_check_raises_error(self) -> None:
        """Mesh evaluate raises ValueError for invalid check."""
        with pytest.raises(ValueError, match="Invalid check"):
            mesh_evaluate("pCube1", checks=["invalid_check"])

    def test_mesh_evaluate_invalid_node_name(self) -> None:
        """Mesh evaluate raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            mesh_evaluate("pCube1;bad")


class TestSelectionSetComponents:
    """Tests for the selection.set_components tool."""

    def test_selection_set_components_success(self) -> None:
        """Set components selects vertices correctly."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "selection": [
                    "pCube1.vtx[0]",
                    "pCube1.vtx[1]",
                    "pCube1.vtx[2]",
                ],
                "count": 3,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_set_components(["pCube1.vtx[0:2]"])

        assert result["count"] == 3
        assert len(result["selection"]) == 3
        assert result["errors"] is None

    def test_selection_set_components_add(self) -> None:
        """Set components with add=True adds to selection."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "selection": ["pCube1.vtx[0]", "pCube1.vtx[1]"],
                "count": 2,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_set_components(["pCube1.vtx[1]"], add=True)

        assert result["count"] == 2

    def test_selection_set_components_deselect(self) -> None:
        """Set components with deselect=True removes from selection."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "selection": ["pCube1.vtx[0]"],
                "count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_set_components(["pCube1.vtx[1]"], deselect=True)

        assert result["count"] == 1

    def test_selection_set_components_empty_list_raises_error(self) -> None:
        """Set components raises ValueError for empty list."""
        with pytest.raises(ValueError, match="components list cannot be empty"):
            selection_set_components([])

    def test_selection_set_components_add_and_deselect_raises_error(self) -> None:
        """Set components raises ValueError when both add and deselect are True."""
        with pytest.raises(ValueError, match="Cannot specify both"):
            selection_set_components(["pCube1.vtx[0]"], add=True, deselect=True)

    def test_selection_set_components_invalid_spec_raises_error(self) -> None:
        """Set components raises ValueError for invalid component spec."""
        with pytest.raises(ValueError, match="Invalid characters"):
            selection_set_components(["pCube1.vtx[0];rm -rf /"])

    def test_selection_set_components_nonexistent(self) -> None:
        """Set components handles nonexistent components."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "selection": [],
                "count": 0,
                "errors": {"pCube999.vtx[0]": "Component 'pCube999.vtx[0]' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_set_components(["pCube999.vtx[0]"])

        assert result["count"] == 0
        assert "pCube999.vtx[0]" in result["errors"]


class TestSelectionGetComponents:
    """Tests for the selection.get_components tool."""

    def test_selection_get_components_empty(self) -> None:
        """Get components returns empty when nothing selected."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "selection": [],
                "vertices": [],
                "edges": [],
                "faces": [],
                "vertex_count": 0,
                "edge_count": 0,
                "face_count": 0,
                "total_count": 0,
                "has_components": False,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_get_components()

        assert result["has_components"] is False
        assert result["total_count"] == 0

    def test_selection_get_components_with_vertices(self) -> None:
        """Get components returns vertices correctly."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "selection": ["pCube1.vtx[0]", "pCube1.vtx[1]", "pCube1.vtx[2]"],
                "vertices": ["pCube1.vtx[0]", "pCube1.vtx[1]", "pCube1.vtx[2]"],
                "edges": [],
                "faces": [],
                "vertex_count": 3,
                "edge_count": 0,
                "face_count": 0,
                "total_count": 3,
                "has_components": True,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_get_components()

        assert result["has_components"] is True
        assert result["vertex_count"] == 3
        assert result["edge_count"] == 0
        assert result["face_count"] == 0

    def test_selection_get_components_mixed(self) -> None:
        """Get components returns mixed selection correctly."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "selection": ["pCube1.vtx[0]", "pCube1.e[1]", "pCube1.f[0]"],
                "vertices": ["pCube1.vtx[0]"],
                "edges": ["pCube1.e[1]"],
                "faces": ["pCube1.f[0]"],
                "vertex_count": 1,
                "edge_count": 1,
                "face_count": 1,
                "total_count": 3,
                "has_components": True,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_get_components()

        assert result["vertex_count"] == 1
        assert result["edge_count"] == 1
        assert result["face_count"] == 1


class TestSelectionConvertComponents:
    """Tests for the selection.convert_components tool."""

    def test_selection_convert_to_vertex(self) -> None:
        """Convert components to vertices."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "selection": ["pCube1.vtx[0]", "pCube1.vtx[1]", "pCube1.vtx[2]", "pCube1.vtx[3]"],
                "to_type": "vertex",
                "count": 4,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_convert_components("vertex")

        assert result["to_type"] == "vertex"
        assert result["count"] == 4

    def test_selection_convert_to_edge(self) -> None:
        """Convert components to edges."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "selection": ["pCube1.e[0]", "pCube1.e[1]", "pCube1.e[2]", "pCube1.e[3]"],
                "to_type": "edge",
                "count": 4,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_convert_components("edge")

        assert result["to_type"] == "edge"
        assert result["count"] == 4

    def test_selection_convert_to_face(self) -> None:
        """Convert components to faces."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "selection": ["pCube1.f[0]", "pCube1.f[1]"],
                "to_type": "face",
                "count": 2,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_convert_components("face")

        assert result["to_type"] == "face"
        assert result["count"] == 2

    def test_selection_convert_with_nodes(self) -> None:
        """Convert components with specified nodes."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "selection": ["pCube1.f[0]", "pCube1.f[1]", "pCube1.f[2]", "pCube1.f[3]"],
                "to_type": "face",
                "count": 4,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.selection.get_client", return_value=mock_client):
            result = selection_convert_components("face", nodes=["pCube1"])

        assert result["count"] == 4

    def test_selection_convert_invalid_type_raises_error(self) -> None:
        """Convert components raises ValueError for invalid type."""
        with pytest.raises(ValueError, match="Invalid to_type"):
            selection_convert_components("invalid")

    def test_selection_convert_invalid_node_raises_error(self) -> None:
        """Convert components raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            selection_convert_components("vertex", nodes=["pCube1;bad"])
