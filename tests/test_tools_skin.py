"""Tests for skinning tools.

These tests verify the MCP tools for skin binding, weight management,
and weight transfer work correctly with mocked transport.
"""

from __future__ import annotations

import json
from typing import get_origin, get_type_hints
from unittest.mock import MagicMock, patch

import pytest
from typing_extensions import NotRequired

from maya_mcp.tools.skin import (
    SkinBindOutput,
    SkinCopyWeightsOutput,
    SkinInfluencesOutput,
    SkinUnbindOutput,
    SkinWeightsGetOutput,
    SkinWeightsSetOutput,
    skin_bind,
    skin_copy_weights,
    skin_influences,
    skin_unbind,
    skin_weights_get,
    skin_weights_set,
)


class TestSkinOutputTypes:
    """Tests for public skinning TypedDict return annotations."""

    def test_skin_tools_use_typed_outputs(self) -> None:
        """Skin tools expose typed output models."""
        assert get_type_hints(skin_bind)["return"] is SkinBindOutput
        assert get_type_hints(skin_unbind)["return"] is SkinUnbindOutput
        assert get_type_hints(skin_influences)["return"] is SkinInfluencesOutput
        assert get_type_hints(skin_weights_get)["return"] is SkinWeightsGetOutput
        assert get_type_hints(skin_weights_set)["return"] is SkinWeightsSetOutput
        assert get_type_hints(skin_copy_weights)["return"] is SkinCopyWeightsOutput

    def test_skin_weights_get_marks_truncation_and_geometry_type_optional(self) -> None:
        """Dense skin weight payloads model optional truncation metadata."""
        assert "truncated" in SkinWeightsGetOutput.__optional_keys__
        assert "total_count" in SkinWeightsGetOutput.__optional_keys__
        assert "_size_warning" in SkinWeightsGetOutput.__optional_keys__
        hints = get_type_hints(SkinWeightsGetOutput, include_extras=True)
        assert get_origin(hints["geometry_type"]) is NotRequired


class TestSkinBind:
    """Tests for the skin.bind tool."""

    def test_skin_bind_success(self) -> None:
        """Skin bind creates a skinCluster and returns influences."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "mesh": "pCube1",
                "skin_cluster": "skinCluster1",
                "influences": ["joint1", "joint2", "joint3"],
                "influence_count": 3,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_bind("pCube1", ["joint1", "joint2", "joint3"])

        assert result["mesh"] == "pCube1"
        assert result["skin_cluster"] == "skinCluster1"
        assert result["influence_count"] == 3
        assert len(result["influences"]) == 3
        assert result["errors"] is None

    def test_skin_bind_invalid_mesh_name(self) -> None:
        """Skin bind raises ValueError for invalid mesh name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            skin_bind("pCube1; rm -rf /", ["joint1"])

    def test_skin_bind_nonexistent_mesh(self) -> None:
        """Skin bind returns error for nonexistent mesh."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "mesh": "nonexistent",
                "skin_cluster": None,
                "influences": [],
                "influence_count": 0,
                "errors": {"_mesh": "Node 'nonexistent' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_bind("nonexistent", ["joint1"])

        assert result["skin_cluster"] is None
        assert result["errors"]["_mesh"] == "Node 'nonexistent' does not exist"

    def test_skin_bind_empty_joints_raises_error(self) -> None:
        """Skin bind raises ValueError for empty joints list."""
        with pytest.raises(ValueError, match="joints list cannot be empty"):
            skin_bind("pCube1", [])

    def test_skin_bind_invalid_joint_name(self) -> None:
        """Skin bind raises ValueError for invalid joint name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            skin_bind("pCube1", ["joint1", "joint2;bad"])

    def test_skin_bind_invalid_bind_method(self) -> None:
        """Skin bind raises ValueError for invalid bind method."""
        with pytest.raises(ValueError, match="Invalid bind_method"):
            skin_bind("pCube1", ["joint1"], bind_method="invalid")  # type: ignore[arg-type]

    def test_skin_bind_with_options(self) -> None:
        """Skin bind respects max_influences and bind_method."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "mesh": "pCube1",
                "skin_cluster": "skinCluster1",
                "influences": ["joint1"],
                "influence_count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_bind("pCube1", ["joint1"], max_influences=2, bind_method="heatMap")

        assert result["skin_cluster"] == "skinCluster1"
        assert result["errors"] is None
        # Verify the command was called
        mock_client.execute.assert_called_once()


class TestSkinUnbind:
    """Tests for the skin.unbind tool."""

    def test_skin_unbind_success(self) -> None:
        """Skin unbind removes the skinCluster."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "mesh": "pCube1",
                "unbound": True,
                "skin_cluster": "skinCluster1",
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_unbind("pCube1")

        assert result["unbound"] is True
        assert result["skin_cluster"] == "skinCluster1"
        assert result["errors"] is None

    def test_skin_unbind_no_skin_cluster(self) -> None:
        """Skin unbind returns error when mesh has no skinCluster."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "mesh": "pCube1",
                "unbound": False,
                "skin_cluster": None,
                "errors": {"_skin": "No skinCluster found on 'pCube1'"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_unbind("pCube1")

        assert result["unbound"] is False
        assert "No skinCluster" in result["errors"]["_skin"]

    def test_skin_unbind_invalid_name(self) -> None:
        """Skin unbind raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            skin_unbind("pCube1;bad")


class TestSkinInfluences:
    """Tests for the skin.influences tool."""

    def test_skin_influences_success(self) -> None:
        """Skin influences returns joint list with indices."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "skin_cluster": "skinCluster1",
                "influences": [
                    {"name": "joint1", "index": 0},
                    {"name": "joint2", "index": 1},
                    {"name": "joint3", "index": 2},
                ],
                "count": 3,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_influences("skinCluster1")

        assert result["count"] == 3
        assert len(result["influences"]) == 3
        assert result["influences"][0]["name"] == "joint1"
        assert result["influences"][0]["index"] == 0
        assert result["errors"] is None

    def test_skin_influences_nonexistent_cluster(self) -> None:
        """Skin influences returns error for nonexistent cluster."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "skin_cluster": "nonexistent",
                "influences": [],
                "count": 0,
                "errors": {"_node": "Node 'nonexistent' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_influences("nonexistent")

        assert result["count"] == 0
        assert result["errors"]["_node"] == "Node 'nonexistent' does not exist"

    def test_skin_influences_invalid_name(self) -> None:
        """Skin influences raises ValueError for invalid name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            skin_influences("skinCluster1;bad")


class TestSkinWeightsGet:
    """Tests for the skin.weights.get tool."""

    def test_skin_weights_get_success(self) -> None:
        """Skin weights get returns per-vertex weights."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "skin_cluster": "skinCluster1",
                "mesh": "pCube1",
                "vertex_count": 8,
                "influence_count": 3,
                "influences": ["joint1", "joint2", "joint3"],
                "vertices": [
                    {"vertex_id": 0, "weights": {"joint1": 0.8, "joint2": 0.2}},
                    {"vertex_id": 1, "weights": {"joint1": 0.5, "joint2": 0.3, "joint3": 0.2}},
                ],
                "offset": 0,
                "count": 2,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_weights_get("skinCluster1", offset=0, limit=2)

        assert result["mesh"] == "pCube1"
        assert result["vertex_count"] == 8
        assert result["influence_count"] == 3
        assert len(result["vertices"]) == 2
        assert result["vertices"][0]["weights"]["joint1"] == 0.8
        assert result["offset"] == 0
        assert result["count"] == 2
        assert result["errors"] is None

    def test_skin_weights_get_pagination(self) -> None:
        """Skin weights get respects offset and limit."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "skin_cluster": "skinCluster1",
                "mesh": "pCube1",
                "vertex_count": 100,
                "influence_count": 2,
                "influences": ["joint1", "joint2"],
                "vertices": [
                    {"vertex_id": 50, "weights": {"joint1": 0.6, "joint2": 0.4}},
                    {"vertex_id": 51, "weights": {"joint1": 0.7, "joint2": 0.3}},
                ],
                "offset": 50,
                "count": 2,
                "truncated": True,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_weights_get("skinCluster1", offset=50, limit=2)

        assert result["offset"] == 50
        assert result["count"] == 2
        assert result["truncated"] is True

    def test_skin_weights_get_truncation_flag(self) -> None:
        """Skin weights get sets truncated flag when more data available."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "skin_cluster": "skinCluster1",
                "mesh": "pCube1",
                "vertex_count": 1000,
                "influence_count": 4,
                "influences": ["j1", "j2", "j3", "j4"],
                "vertices": [{"vertex_id": i, "weights": {"j1": 1.0}} for i in range(100)],
                "offset": 0,
                "count": 100,
                "truncated": True,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_weights_get("skinCluster1")

        assert result["truncated"] is True
        assert result["vertex_count"] == 1000
        assert result["count"] == 100

    def test_skin_weights_get_negative_offset(self) -> None:
        """Skin weights get raises ValueError for negative offset."""
        with pytest.raises(ValueError, match="offset must be non-negative"):
            skin_weights_get("skinCluster1", offset=-1)

    def test_skin_weights_get_invalid_name(self) -> None:
        """Skin weights get raises ValueError for invalid name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            skin_weights_get("skinCluster1;bad")

    def test_skin_weights_get_response_guard(self) -> None:
        """Skin weights get applies response size guard on large data."""
        mock_client = MagicMock()
        # Create a large response that would exceed 50KB
        large_vertices = [
            {
                "vertex_id": i,
                "weights": {f"joint_{j}": round(1.0 / 10, 6) for j in range(10)},
            }
            for i in range(500)
        ]
        mock_response = json.dumps(
            {
                "skin_cluster": "skinCluster1",
                "mesh": "pCube1",
                "vertex_count": 10000,
                "influence_count": 10,
                "influences": [f"joint_{j}" for j in range(10)],
                "vertices": large_vertices,
                "offset": 0,
                "count": 500,
                "truncated": True,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_weights_get("skinCluster1", offset=0, limit=500)

        # Response guard should have truncated the vertices list
        # The exact count depends on the guard's binary search, but it should be less
        # than the original if the response exceeded 50KB
        response_size = len(json.dumps(result).encode("utf-8"))
        # Either the response fits within limits, or it was marked as truncated
        assert response_size <= 55000 or "_size_warning" in result


class TestSkinWeightsSet:
    """Tests for the skin.weights.set tool."""

    def test_skin_weights_set_success(self) -> None:
        """Skin weights set updates vertex weights."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "skin_cluster": "skinCluster1",
                "set_count": 2,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        weights = [
            {"vertex_id": 0, "weights": {"joint1": 0.8, "joint2": 0.2}},
            {"vertex_id": 1, "weights": {"joint1": 0.5, "joint2": 0.5}},
        ]

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_weights_set("skinCluster1", weights)

        assert result["set_count"] == 2
        assert result["errors"] is None

    def test_skin_weights_set_with_normalize(self) -> None:
        """Skin weights set respects normalize flag."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "skin_cluster": "skinCluster1",
                "set_count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        weights = [{"vertex_id": 0, "weights": {"joint1": 1.0}}]

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_weights_set("skinCluster1", weights, normalize=False)

        assert result["set_count"] == 1
        assert result["errors"] is None
        # Verify the command was called
        mock_client.execute.assert_called_once()

    def test_skin_weights_set_invalid_joint_name(self) -> None:
        """Skin weights set raises ValueError for invalid joint name."""
        weights = [{"vertex_id": 0, "weights": {"joint1;bad": 1.0}}]
        with pytest.raises(ValueError, match="Invalid characters"):
            skin_weights_set("skinCluster1", weights)

    def test_skin_weights_set_empty_weights(self) -> None:
        """Skin weights set raises ValueError for empty weights list."""
        with pytest.raises(ValueError, match="weights list cannot be empty"):
            skin_weights_set("skinCluster1", [])

    def test_skin_weights_set_too_many_entries(self) -> None:
        """Skin weights set raises ValueError for too many entries."""
        weights = [{"vertex_id": i, "weights": {"joint1": 1.0}} for i in range(1001)]
        with pytest.raises(ValueError, match="Too many weight entries"):
            skin_weights_set("skinCluster1", weights)

    def test_skin_weights_set_invalid_cluster_name(self) -> None:
        """Skin weights set raises ValueError for invalid cluster name."""
        weights = [{"vertex_id": 0, "weights": {"joint1": 1.0}}]
        with pytest.raises(ValueError, match="Invalid characters"):
            skin_weights_set("skinCluster1;bad", weights)

    def test_skin_weights_get_curve_success(self) -> None:
        """Skin weights get works on curves using cv[] components."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "skin_cluster": "skinCluster1",
                "mesh": "curve1",
                "vertex_count": 4,
                "influence_count": 2,
                "influences": ["joint1", "joint2"],
                "geometry_type": "nurbsCurve",
                "vertices": [
                    {"vertex_id": 0, "weights": {"joint1": 1.0}},
                    {"vertex_id": 1, "weights": {"joint1": 0.7, "joint2": 0.3}},
                ],
                "offset": 0,
                "count": 2,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_weights_get("skinCluster1", offset=0, limit=2)

        assert result["geometry_type"] == "nurbsCurve"
        assert result["vertex_count"] == 4
        assert len(result["vertices"]) == 2
        assert result["errors"] is None
        # Verify the command uses cv[] instead of vtx[]
        cmd = mock_client.execute.call_args[0][0]
        assert "nurbsCurve" in cmd or "comp_prefix" in cmd

    def test_skin_weights_set_curve_success(self) -> None:
        """Skin weights set works on curves using cv[] components."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "skin_cluster": "skinCluster1",
                "set_count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        weights = [{"vertex_id": 0, "weights": {"joint1": 1.0}}]

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_weights_set("skinCluster1", weights)

        assert result["set_count"] == 1
        assert result["errors"] is None
        # Verify the command contains geometry type detection
        cmd = mock_client.execute.call_args[0][0]
        assert "nurbsCurve" in cmd


class TestSkinCopyWeights:
    """Tests for the skin.copy_weights tool."""

    def test_skin_copy_weights_success(self) -> None:
        """Skin copy weights transfers weights between meshes."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "source_mesh": "pCube1",
                "target_mesh": "pCube2",
                "source_skin_cluster": "skinCluster1",
                "target_skin_cluster": "skinCluster2",
                "success": True,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_copy_weights("pCube1", "pCube2")

        assert result["success"] is True
        assert result["source_skin_cluster"] == "skinCluster1"
        assert result["target_skin_cluster"] == "skinCluster2"
        assert result["errors"] is None

    def test_skin_copy_weights_source_no_skin(self) -> None:
        """Skin copy weights returns error when source has no skin."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "source_mesh": "pCube1",
                "target_mesh": "pCube2",
                "source_skin_cluster": None,
                "target_skin_cluster": None,
                "success": False,
                "errors": {"_source_skin": "No skinCluster found on 'pCube1'"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_copy_weights("pCube1", "pCube2")

        assert result["success"] is False
        assert "No skinCluster" in result["errors"]["_source_skin"]

    def test_skin_copy_weights_target_no_skin(self) -> None:
        """Skin copy weights returns error when target has no skin."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "source_mesh": "pCube1",
                "target_mesh": "pCube2",
                "source_skin_cluster": "skinCluster1",
                "target_skin_cluster": None,
                "success": False,
                "errors": {"_target_skin": "No skinCluster found on 'pCube2'"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_copy_weights("pCube1", "pCube2")

        assert result["success"] is False
        assert "No skinCluster" in result["errors"]["_target_skin"]

    def test_skin_copy_weights_invalid_source_name(self) -> None:
        """Skin copy weights raises ValueError for invalid source name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            skin_copy_weights("pCube1;bad", "pCube2")

    def test_skin_copy_weights_invalid_target_name(self) -> None:
        """Skin copy weights raises ValueError for invalid target name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            skin_copy_weights("pCube1", "pCube2;bad")

    def test_skin_copy_weights_invalid_surface_association(self) -> None:
        """Skin copy weights raises ValueError for invalid surface_association."""
        with pytest.raises(ValueError, match="Invalid surface_association"):
            skin_copy_weights("pCube1", "pCube2", surface_association="invalid")  # type: ignore[arg-type]

    def test_skin_copy_weights_invalid_influence_association(self) -> None:
        """Skin copy weights raises ValueError for invalid influence_association."""
        with pytest.raises(ValueError, match="Invalid influence_association"):
            skin_copy_weights("pCube1", "pCube2", influence_association="invalid")  # type: ignore[arg-type]

    def test_skin_copy_weights_with_options(self) -> None:
        """Skin copy weights respects surface and influence association options."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "source_mesh": "pCube1",
                "target_mesh": "pCube2",
                "source_skin_cluster": "skinCluster1",
                "target_skin_cluster": "skinCluster2",
                "success": True,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.skin.get_client", return_value=mock_client):
            result = skin_copy_weights(
                "pCube1",
                "pCube2",
                surface_association="rayCast",
                influence_association="name",
            )

        assert result["success"] is True
        assert result["errors"] is None
