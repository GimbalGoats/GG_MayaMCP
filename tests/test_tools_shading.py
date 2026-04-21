"""Tests for shading tools.

These tests verify the MCP tools for material creation, assignment,
and color setting work correctly with mocked transport.
"""

from __future__ import annotations

import json
from typing import get_type_hints
from unittest.mock import MagicMock, patch

import pytest

from maya_mcp.tools.shading import (
    ShadingAssignMaterialOutput,
    ShadingCreateMaterialOutput,
    ShadingSetMaterialColorOutput,
    shading_assign_material,
    shading_create_material,
    shading_set_material_color,
)


class TestShadingOutputTypes:
    """Tests for public shading TypedDict return annotations."""

    def test_shading_tools_use_typed_outputs(self) -> None:
        """Shading tools expose typed output models."""
        assert get_type_hints(shading_create_material)["return"] is ShadingCreateMaterialOutput
        assert get_type_hints(shading_assign_material)["return"] is ShadingAssignMaterialOutput
        assert get_type_hints(shading_set_material_color)["return"] is ShadingSetMaterialColorOutput


class TestShadingCreateMaterial:
    """Tests for the shading.create_material tool."""

    def test_create_lambert_success(self) -> None:
        """Create lambert material returns material and shading group."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "material": "lambert2",
                "shading_group": "lambert2SG",
                "material_type": "lambert",
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.shading.get_client", return_value=mock_client):
            result = shading_create_material("lambert")

        assert result["material"] == "lambert2"
        assert result["shading_group"] == "lambert2SG"
        assert result["material_type"] == "lambert"
        assert result["errors"] is None

    def test_create_blinn_with_color(self) -> None:
        """Create blinn material with color."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "material": "blinn1",
                "shading_group": "blinn1SG",
                "material_type": "blinn",
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.shading.get_client", return_value=mock_client):
            result = shading_create_material("blinn", color=[1.0, 0.0, 0.0])

        assert result["material"] == "blinn1"
        assert result["errors"] is None

    def test_create_standard_surface(self) -> None:
        """Create standardSurface material."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "material": "standardSurface2",
                "shading_group": "standardSurface2SG",
                "material_type": "standardSurface",
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.shading.get_client", return_value=mock_client):
            result = shading_create_material("standardSurface", name="standardSurface2")

        assert result["material_type"] == "standardSurface"
        assert result["errors"] is None

    def test_create_with_name(self) -> None:
        """Create material with custom name."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "material": "redMat",
                "shading_group": "redMatSG",
                "material_type": "phong",
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.shading.get_client", return_value=mock_client):
            result = shading_create_material("phong", name="redMat", color=[1.0, 0.0, 0.0])

        assert result["material"] == "redMat"
        assert result["errors"] is None

    def test_create_invalid_type(self) -> None:
        """Create material raises ValueError for invalid type."""
        with pytest.raises(ValueError, match="Invalid material_type"):
            shading_create_material("metal")  # type: ignore[arg-type]

    def test_create_invalid_name(self) -> None:
        """Create material raises ValueError for invalid name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            shading_create_material("lambert", name="mat;bad")

    def test_create_invalid_color(self) -> None:
        """Create material raises ValueError for invalid color."""
        with pytest.raises(ValueError, match="color must be a list of 3 floats"):
            shading_create_material("lambert", color=[1.0, 0.0])


class TestShadingAssignMaterial:
    """Tests for the shading.assign_material tool."""

    def test_assign_success(self) -> None:
        """Assign material to mesh returns assigned list."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "assigned": ["pCube1"],
                "material": "lambert2",
                "shading_group": "lambert2SG",
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.shading.get_client", return_value=mock_client):
            result = shading_assign_material(["pCube1"], "lambert2")

        assert result["assigned"] == ["pCube1"]
        assert result["material"] == "lambert2"
        assert result["shading_group"] == "lambert2SG"
        assert result["errors"] is None

    def test_assign_to_faces(self) -> None:
        """Assign material to face components."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "assigned": ["pCube1.f[0]", "pCube1.f[1]"],
                "material": "redMat",
                "shading_group": "redMatSG",
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.shading.get_client", return_value=mock_client):
            result = shading_assign_material(["pCube1.f[0]", "pCube1.f[1]"], "redMat")

        assert len(result["assigned"]) == 2
        assert result["errors"] is None

    def test_assign_empty_targets(self) -> None:
        """Assign raises ValueError for empty targets."""
        with pytest.raises(ValueError, match="targets list cannot be empty"):
            shading_assign_material([], "lambert2")

    def test_assign_invalid_material_name(self) -> None:
        """Assign raises ValueError for invalid material name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            shading_assign_material(["pCube1"], "mat;bad")

    def test_assign_nonexistent_material(self) -> None:
        """Assign returns error for nonexistent material."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "assigned": [],
                "material": "nonexistent",
                "shading_group": None,
                "errors": {"_material": "Node 'nonexistent' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.shading.get_client", return_value=mock_client):
            result = shading_assign_material(["pCube1"], "nonexistent")

        assert len(result["assigned"]) == 0
        assert "_material" in result["errors"]

    def test_assign_multiple_meshes(self) -> None:
        """Assign material to multiple meshes."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "assigned": ["pCube1", "pSphere1"],
                "material": "blinn1",
                "shading_group": "blinn1SG",
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.shading.get_client", return_value=mock_client):
            result = shading_assign_material(["pCube1", "pSphere1"], "blinn1")

        assert len(result["assigned"]) == 2
        assert result["errors"] is None


class TestShadingSetMaterialColor:
    """Tests for the shading.set_material_color tool."""

    def test_set_color_success(self) -> None:
        """Set material color returns attribute and color."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "material": "lambert2",
                "attribute": "color",
                "color": [1.0, 0.0, 0.0],
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.shading.get_client", return_value=mock_client):
            result = shading_set_material_color("lambert2", [1.0, 0.0, 0.0])

        assert result["color"] == [1.0, 0.0, 0.0]
        assert result["attribute"] == "color"
        assert result["errors"] is None

    def test_set_base_color(self) -> None:
        """Set baseColor on standardSurface material."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "material": "standardSurface1",
                "attribute": "baseColor",
                "color": [0.0, 1.0, 0.0],
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.shading.get_client", return_value=mock_client):
            result = shading_set_material_color(
                "standardSurface1", [0.0, 1.0, 0.0], attribute="baseColor"
            )

        assert result["attribute"] == "baseColor"
        assert result["errors"] is None

    def test_set_color_invalid_material(self) -> None:
        """Set color raises ValueError for invalid material name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            shading_set_material_color("mat;bad", [1.0, 0.0, 0.0])

    def test_set_color_invalid_color(self) -> None:
        """Set color raises ValueError for invalid color."""
        with pytest.raises(ValueError, match="color must be a list of 3 floats"):
            shading_set_material_color("lambert2", [1.0, 0.0])

    def test_set_color_nonexistent_material(self) -> None:
        """Set color returns error for nonexistent material."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "material": "nonexistent",
                "attribute": "color",
                "color": [1.0, 0.0, 0.0],
                "errors": {"_material": "Node 'nonexistent' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.shading.get_client", return_value=mock_client):
            result = shading_set_material_color("nonexistent", [1.0, 0.0, 0.0])

        assert "_material" in result["errors"]

    def test_set_color_nonexistent_attribute(self) -> None:
        """Set color returns error for nonexistent attribute."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "material": "lambert2",
                "attribute": "fakeAttr",
                "color": [1.0, 0.0, 0.0],
                "errors": {"_attribute": "Attribute 'fakeAttr' does not exist on 'lambert2'"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.shading.get_client", return_value=mock_client):
            result = shading_set_material_color("lambert2", [1.0, 0.0, 0.0], attribute="fakeAttr")

        assert "_attribute" in result["errors"]
