"""Tests for polygon modeling tools.

These tests verify the MCP tools for polygon modeling work correctly
with mocked transport. No running Maya instance is required.
"""

from __future__ import annotations

import json
from typing import get_origin, get_type_hints
from unittest.mock import MagicMock, patch

import pytest
from typing_extensions import NotRequired

from maya_mcp.tools.modeling import (
    ModelingBevelOutput,
    ModelingBooleanOutput,
    ModelingBridgeOutput,
    ModelingCenterPivotOutput,
    ModelingCombineOutput,
    ModelingCreatePolygonPrimitiveOutput,
    ModelingDeleteFacesOutput,
    ModelingDeleteHistoryOutput,
    ModelingExtrudeFacesOutput,
    ModelingFreezeTransformsOutput,
    ModelingInsertEdgeLoopOutput,
    ModelingMergeVerticesOutput,
    ModelingMoveComponentsOutput,
    ModelingSeparateOutput,
    ModelingSetPivotOutput,
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


class TestModelingOutputTypes:
    """Tests for public modeling TypedDict return annotations."""

    def test_modeling_tools_use_typed_outputs(self) -> None:
        """Modeling tools expose typed output models."""
        assert (
            get_type_hints(modeling_create_polygon_primitive)["return"]
            is ModelingCreatePolygonPrimitiveOutput
        )
        assert get_type_hints(modeling_extrude_faces)["return"] is ModelingExtrudeFacesOutput
        assert get_type_hints(modeling_boolean)["return"] is ModelingBooleanOutput
        assert get_type_hints(modeling_combine)["return"] is ModelingCombineOutput
        assert get_type_hints(modeling_separate)["return"] is ModelingSeparateOutput
        assert get_type_hints(modeling_merge_vertices)["return"] is ModelingMergeVerticesOutput
        assert get_type_hints(modeling_bevel)["return"] is ModelingBevelOutput
        assert get_type_hints(modeling_bridge)["return"] is ModelingBridgeOutput
        assert get_type_hints(modeling_insert_edge_loop)["return"] is ModelingInsertEdgeLoopOutput
        assert get_type_hints(modeling_delete_faces)["return"] is ModelingDeleteFacesOutput
        assert get_type_hints(modeling_move_components)["return"] is ModelingMoveComponentsOutput
        assert (
            get_type_hints(modeling_freeze_transforms)["return"] is ModelingFreezeTransformsOutput
        )
        assert get_type_hints(modeling_delete_history)["return"] is ModelingDeleteHistoryOutput
        assert get_type_hints(modeling_center_pivot)["return"] is ModelingCenterPivotOutput
        assert get_type_hints(modeling_set_pivot)["return"] is ModelingSetPivotOutput

    def test_modeling_outputs_mark_optional_and_guarded_fields(self) -> None:
        """Modeling payloads model conditional fields precisely."""
        hints = get_type_hints(ModelingMoveComponentsOutput, include_extras=True)
        assert get_origin(hints["translate"]) is NotRequired
        assert get_origin(hints["absolute"]) is NotRequired
        assert "truncated" in ModelingSeparateOutput.__optional_keys__
        assert "_size_warning" in ModelingDeleteHistoryOutput.__optional_keys__


class TestModelingCreatePolygonPrimitive:
    """Tests for the modeling.create_polygon_primitive tool."""

    def test_create_cube_success(self) -> None:
        """Create cube returns transform, shape, and constructor."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "transform": "pCube1",
                "shape": "pCubeShape1",
                "constructor_node": "polyCube1",
                "primitive_type": "cube",
                "vertex_count": 8,
                "face_count": 6,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_create_polygon_primitive("cube")

        assert result["transform"] == "pCube1"
        assert result["shape"] == "pCubeShape1"
        assert result["constructor_node"] == "polyCube1"
        assert result["primitive_type"] == "cube"
        assert result["vertex_count"] == 8
        assert result["face_count"] == 6
        assert result["errors"] is None

    def test_create_sphere_success(self) -> None:
        """Create sphere returns correct data."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "transform": "pSphere1",
                "shape": "pSphereShape1",
                "constructor_node": "polySphere1",
                "primitive_type": "sphere",
                "vertex_count": 382,
                "face_count": 400,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_create_polygon_primitive("sphere", radius=2.0)

        assert result["transform"] == "pSphere1"
        assert result["primitive_type"] == "sphere"
        assert result["errors"] is None
        mock_client.execute.assert_called_once()

    def test_create_with_name(self) -> None:
        """Create primitive with custom name."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "transform": "myBox",
                "shape": "myBoxShape",
                "constructor_node": "polyCube1",
                "primitive_type": "cube",
                "vertex_count": 8,
                "face_count": 6,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_create_polygon_primitive("cube", name="myBox")

        assert result["transform"] == "myBox"
        assert result["errors"] is None

    def test_invalid_primitive_type(self) -> None:
        """Invalid primitive type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid primitive_type"):
            modeling_create_polygon_primitive("hexagon")  # type: ignore[arg-type]

    def test_invalid_axis(self) -> None:
        """Invalid axis raises ValueError."""
        with pytest.raises(ValueError, match="Invalid axis"):
            modeling_create_polygon_primitive("cube", axis="w")  # type: ignore[arg-type]

    def test_invalid_name(self) -> None:
        """Invalid name with forbidden chars raises ValueError."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_create_polygon_primitive("cube", name="bad;name")

    def test_create_with_subdivisions(self) -> None:
        """Create primitive with subdivision parameters."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "transform": "pCube1",
                "shape": "pCubeShape1",
                "constructor_node": "polyCube1",
                "primitive_type": "cube",
                "vertex_count": 50,
                "face_count": 48,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_create_polygon_primitive(
                "cube",
                subdivisions_width=4,
                subdivisions_height=4,
                subdivisions_depth=4,
            )

        assert result["errors"] is None
        mock_client.execute.assert_called_once()


class TestModelingExtrudeFaces:
    """Tests for the modeling.extrude_faces tool."""

    def test_extrude_success(self) -> None:
        """Extrude faces returns node and new face count."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "polyExtrudeFace1",
                "faces_extruded": 1,
                "new_face_count": 10,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_extrude_faces(["pCube1.f[0]"], local_translate_z=0.5)

        assert result["node"] == "polyExtrudeFace1"
        assert result["faces_extruded"] == 1
        assert result["new_face_count"] == 10
        assert result["errors"] is None

    def test_extrude_empty_faces(self) -> None:
        """Extrude raises ValueError for empty faces list."""
        with pytest.raises(ValueError, match="faces list cannot be empty"):
            modeling_extrude_faces([])

    def test_extrude_invalid_component(self) -> None:
        """Extrude raises ValueError for invalid component."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_extrude_faces(["pCube1.f[0];bad"])

    def test_extrude_nonexistent_faces(self) -> None:
        """Extrude returns error for nonexistent faces."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": None,
                "faces_extruded": 1,
                "new_face_count": 0,
                "errors": {"_faces": "Components do not exist: pCube99.f[0]"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_extrude_faces(["pCube99.f[0]"])

        assert result["errors"]["_faces"] is not None


class TestModelingBoolean:
    """Tests for the modeling.boolean tool."""

    def test_boolean_union_success(self) -> None:
        """Boolean union returns result mesh."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "result_mesh": "polySurface1",
                "operation": "union",
                "vertex_count": 16,
                "face_count": 12,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_boolean("pCube1", "pCube2", "union")

        assert result["result_mesh"] == "polySurface1"
        assert result["operation"] == "union"
        assert result["errors"] is None

    def test_boolean_difference_success(self) -> None:
        """Boolean difference works correctly."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "result_mesh": "polySurface1",
                "operation": "difference",
                "vertex_count": 24,
                "face_count": 18,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_boolean("pCube1", "pSphere1", "difference")

        assert result["operation"] == "difference"
        assert result["errors"] is None

    def test_boolean_invalid_operation(self) -> None:
        """Boolean raises ValueError for invalid operation."""
        with pytest.raises(ValueError, match="Invalid operation"):
            modeling_boolean("pCube1", "pCube2", "xor")  # type: ignore[arg-type]

    def test_boolean_invalid_mesh_name(self) -> None:
        """Boolean raises ValueError for invalid mesh name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_boolean("pCube1;bad", "pCube2")

    def test_boolean_nonexistent_mesh(self) -> None:
        """Boolean returns error for nonexistent mesh."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "result_mesh": None,
                "operation": "union",
                "vertex_count": 0,
                "face_count": 0,
                "errors": {"_mesh_a": "Node 'nonexistent' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_boolean("nonexistent", "pCube2")

        assert result["result_mesh"] is None
        assert "_mesh_a" in result["errors"]


class TestModelingCombine:
    """Tests for the modeling.combine tool."""

    def test_combine_success(self) -> None:
        """Combine returns result mesh with vertex/face counts."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "result_mesh": "pCube3",
                "source_meshes": ["pCube1", "pCube2"],
                "vertex_count": 16,
                "face_count": 12,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_combine(["pCube1", "pCube2"])

        assert result["result_mesh"] == "pCube3"
        assert result["vertex_count"] == 16
        assert result["errors"] is None

    def test_combine_too_few_meshes(self) -> None:
        """Combine raises ValueError for less than 2 meshes."""
        with pytest.raises(ValueError, match="at least 2 meshes"):
            modeling_combine(["pCube1"])

    def test_combine_invalid_mesh_name(self) -> None:
        """Combine raises ValueError for invalid mesh name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_combine(["pCube1", "pCube2;bad"])

    def test_combine_with_name(self) -> None:
        """Combine respects the name parameter."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "result_mesh": "combined_mesh",
                "source_meshes": ["pCube1", "pCube2"],
                "vertex_count": 16,
                "face_count": 12,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_combine(["pCube1", "pCube2"], name="combined_mesh")

        assert result["result_mesh"] == "combined_mesh"
        assert result["errors"] is None


class TestModelingSeparate:
    """Tests for the modeling.separate tool."""

    def test_separate_success(self) -> None:
        """Separate returns result meshes list."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "source_mesh": "polySurface1",
                "result_meshes": ["polySurface2", "polySurface3"],
                "count": 2,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_separate("polySurface1")

        assert result["count"] == 2
        assert len(result["result_meshes"]) == 2
        assert result["errors"] is None

    def test_separate_invalid_name(self) -> None:
        """Separate raises ValueError for invalid name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_separate("mesh;bad")

    def test_separate_nonexistent_mesh(self) -> None:
        """Separate returns error for nonexistent mesh."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "source_mesh": "nonexistent",
                "result_meshes": [],
                "count": 0,
                "errors": {"_mesh": "Node 'nonexistent' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_separate("nonexistent")

        assert result["count"] == 0
        assert "_mesh" in result["errors"]


class TestModelingMergeVertices:
    """Tests for the modeling.merge_vertices tool."""

    def test_merge_vertices_success(self) -> None:
        """Merge vertices returns before/after counts."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "mesh": "polySurface1",
                "vertices_merged": 4,
                "vertex_count_before": 16,
                "vertex_count_after": 12,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_merge_vertices("polySurface1", threshold=0.01)

        assert result["vertices_merged"] == 4
        assert result["vertex_count_before"] == 16
        assert result["vertex_count_after"] == 12
        assert result["errors"] is None

    def test_merge_vertices_with_specific_verts(self) -> None:
        """Merge vertices works with specific vertex list."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "mesh": "pCube1",
                "vertices_merged": 2,
                "vertex_count_before": 8,
                "vertex_count_after": 6,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_merge_vertices("pCube1", vertices=["pCube1.vtx[0]", "pCube1.vtx[1]"])

        assert result["errors"] is None

    def test_merge_vertices_invalid_name(self) -> None:
        """Merge vertices raises ValueError for invalid mesh name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_merge_vertices("mesh;bad")

    def test_merge_vertices_invalid_component(self) -> None:
        """Merge vertices raises ValueError for invalid component."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_merge_vertices("pCube1", vertices=["pCube1.vtx[0];bad"])


class TestModelingDeleteHistory:
    """Tests for the modeling.delete_history tool."""

    def test_delete_history_success(self) -> None:
        """Delete history returns cleaned list."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "cleaned": ["pCube1", "pSphere1"],
                "count": 2,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_delete_history(nodes=["pCube1", "pSphere1"])

        assert result["count"] == 2
        assert result["errors"] is None

    def test_delete_history_all_nodes(self) -> None:
        """Delete history for all nodes in scene."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "cleaned": ["pCube1", "pSphere1", "pCylinder1"],
                "count": 3,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_delete_history(all_nodes=True)

        assert result["count"] == 3
        assert result["errors"] is None

    def test_delete_history_no_args(self) -> None:
        """Delete history raises ValueError when no args provided."""
        with pytest.raises(ValueError, match="Either nodes must be provided"):
            modeling_delete_history()

    def test_delete_history_invalid_name(self) -> None:
        """Delete history raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_delete_history(nodes=["pCube1;bad"])


class TestModelingFreezeTransforms:
    """Tests for the modeling.freeze_transforms tool."""

    def test_freeze_transforms_success(self) -> None:
        """Freeze transforms returns frozen list."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "frozen": ["pCube1", "pSphere1"],
                "count": 2,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_freeze_transforms(["pCube1", "pSphere1"])

        assert result["count"] == 2
        assert result["errors"] is None

    def test_freeze_transforms_empty_list(self) -> None:
        """Freeze transforms raises ValueError for empty list."""
        with pytest.raises(ValueError, match="nodes list cannot be empty"):
            modeling_freeze_transforms([])

    def test_freeze_transforms_invalid_name(self) -> None:
        """Freeze transforms raises ValueError for invalid name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_freeze_transforms(["pCube1;bad"])

    def test_freeze_transforms_selective(self) -> None:
        """Freeze transforms respects translate/rotate/scale flags."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "frozen": ["pCube1"],
                "count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_freeze_transforms(
                ["pCube1"], translate=True, rotate=False, scale=False
            )

        assert result["errors"] is None
        mock_client.execute.assert_called_once()


class TestModelingCenterPivot:
    """Tests for the modeling.center_pivot tool."""

    def test_center_pivot_success(self) -> None:
        """Center pivot returns centered nodes and positions."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "centered": ["pCube1"],
                "count": 1,
                "pivot_positions": {"pCube1": [0.0, 0.5, 0.0]},
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_center_pivot(["pCube1"])

        assert result["count"] == 1
        assert result["pivot_positions"]["pCube1"] == [0.0, 0.5, 0.0]
        assert result["errors"] is None

    def test_center_pivot_empty_list(self) -> None:
        """Center pivot raises ValueError for empty list."""
        with pytest.raises(ValueError, match="nodes list cannot be empty"):
            modeling_center_pivot([])

    def test_center_pivot_invalid_name(self) -> None:
        """Center pivot raises ValueError for invalid name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_center_pivot(["pCube1;bad"])


class TestModelingSetPivot:
    """Tests for the modeling.set_pivot tool."""

    def test_set_pivot_success(self) -> None:
        """Set pivot returns node and pivot position."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "pivot": [1.0, 2.0, 3.0],
                "world_space": True,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_set_pivot("pCube1", [1.0, 2.0, 3.0])

        assert result["pivot"] == [1.0, 2.0, 3.0]
        assert result["errors"] is None

    def test_set_pivot_invalid_position(self) -> None:
        """Set pivot raises ValueError for invalid position."""
        with pytest.raises(ValueError, match="position must be a list of 3 floats"):
            modeling_set_pivot("pCube1", [1.0, 2.0])

    def test_set_pivot_invalid_name(self) -> None:
        """Set pivot raises ValueError for invalid name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_set_pivot("pCube1;bad", [0.0, 0.0, 0.0])


class TestModelingMoveComponents:
    """Tests for the modeling.move_components tool."""

    def test_move_relative_success(self) -> None:
        """Move components with relative translation."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "components_moved": 4,
                "translate": [0.0, 1.0, 0.0],
                "world_space": True,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_move_components(["pCube1.vtx[0:3]"], translate=[0.0, 1.0, 0.0])

        assert result["components_moved"] == 4
        assert result["errors"] is None

    def test_move_absolute_success(self) -> None:
        """Move components with absolute position."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "components_moved": 1,
                "absolute": [5.0, 5.0, 5.0],
                "world_space": True,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_move_components(["pCube1.vtx[0]"], absolute=[5.0, 5.0, 5.0])

        assert result["errors"] is None

    def test_move_empty_components(self) -> None:
        """Move raises ValueError for empty components."""
        with pytest.raises(ValueError, match="components list cannot be empty"):
            modeling_move_components([], translate=[0.0, 1.0, 0.0])

    def test_move_both_translate_and_absolute(self) -> None:
        """Move raises ValueError when both translate and absolute are given."""
        with pytest.raises(ValueError, match="Only one of translate or absolute"):
            modeling_move_components(
                ["pCube1.vtx[0]"],
                translate=[1.0, 0.0, 0.0],
                absolute=[5.0, 5.0, 5.0],
            )

    def test_move_neither_translate_nor_absolute(self) -> None:
        """Move raises ValueError when neither translate nor absolute is given."""
        with pytest.raises(ValueError, match="Either translate or absolute must be provided"):
            modeling_move_components(["pCube1.vtx[0]"])

    def test_move_invalid_translate(self) -> None:
        """Move raises ValueError for invalid translate."""
        with pytest.raises(ValueError, match="translate must be a list of 3 floats"):
            modeling_move_components(["pCube1.vtx[0]"], translate=[1.0, 2.0])

    def test_move_invalid_component(self) -> None:
        """Move raises ValueError for invalid component."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_move_components(["pCube1.vtx[0];bad"], translate=[0.0, 0.0, 0.0])


class TestModelingBevel:
    """Tests for the modeling.bevel tool."""

    def test_bevel_success(self) -> None:
        """Bevel returns node and new counts."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "polyBevel1",
                "components_beveled": 4,
                "new_vertex_count": 24,
                "new_face_count": 14,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_bevel(["pCube1.e[0:3]"], offset=0.2, segments=2)

        assert result["node"] == "polyBevel1"
        assert result["errors"] is None

    def test_bevel_empty_components(self) -> None:
        """Bevel raises ValueError for empty components."""
        with pytest.raises(ValueError, match="components list cannot be empty"):
            modeling_bevel([])

    def test_bevel_invalid_component(self) -> None:
        """Bevel raises ValueError for invalid component."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_bevel(["pCube1.e[0];bad"])


class TestModelingBridge:
    """Tests for the modeling.bridge tool."""

    def test_bridge_success(self) -> None:
        """Bridge returns node and new face count."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "polyBridgeEdge1",
                "new_face_count": 10,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_bridge(["pCube1.e[4]", "pCube1.e[6]"])

        assert result["node"] == "polyBridgeEdge1"
        assert result["errors"] is None

    def test_bridge_empty_edges(self) -> None:
        """Bridge raises ValueError for empty edge loops."""
        with pytest.raises(ValueError, match="edge_loops list cannot be empty"):
            modeling_bridge([])

    def test_bridge_invalid_component(self) -> None:
        """Bridge raises ValueError for invalid component."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_bridge(["pCube1.e[0];bad"])


class TestModelingInsertEdgeLoop:
    """Tests for the modeling.insert_edge_loop tool."""

    def test_insert_edge_loop_success(self) -> None:
        """Insert edge loop returns node and new counts."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "polySplitRing1",
                "edge": "pCube1.e[4]",
                "new_edge_count": 16,
                "new_vertex_count": 12,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_insert_edge_loop("pCube1.e[4]")

        assert result["node"] == "polySplitRing1"
        assert result["edge"] == "pCube1.e[4]"
        assert result["errors"] is None

    def test_insert_edge_loop_invalid_component(self) -> None:
        """Insert edge loop raises ValueError for invalid component."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_insert_edge_loop("pCube1.e[4];bad")

    def test_insert_edge_loop_nonexistent(self) -> None:
        """Insert edge loop returns error for nonexistent edge."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": None,
                "edge": "pCube99.e[4]",
                "new_edge_count": 0,
                "new_vertex_count": 0,
                "errors": {"_edge": "Component 'pCube99.e[4]' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_insert_edge_loop("pCube99.e[4]")

        assert result["node"] is None
        assert "_edge" in result["errors"]


class TestModelingDeleteFaces:
    """Tests for the modeling.delete_faces tool."""

    def test_delete_faces_success(self) -> None:
        """Delete faces returns remaining face count."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "faces_deleted": 2,
                "mesh": "pCube1",
                "remaining_face_count": 4,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.modeling.get_client", return_value=mock_client):
            result = modeling_delete_faces(["pCube1.f[0]", "pCube1.f[1]"])

        assert result["faces_deleted"] == 2
        assert result["remaining_face_count"] == 4
        assert result["errors"] is None

    def test_delete_faces_empty_list(self) -> None:
        """Delete faces raises ValueError for empty list."""
        with pytest.raises(ValueError, match="faces list cannot be empty"):
            modeling_delete_faces([])

    def test_delete_faces_invalid_component(self) -> None:
        """Delete faces raises ValueError for invalid component."""
        with pytest.raises(ValueError, match="Invalid characters"):
            modeling_delete_faces(["pCube1.f[0];bad"])
