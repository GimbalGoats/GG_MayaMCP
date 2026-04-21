"""Tests for curve tools.

These tests verify the MCP tools for querying NURBS curve geometry
work correctly with mocked transport.
"""

from __future__ import annotations

import json
from typing import get_origin, get_type_hints
from unittest.mock import MagicMock, patch

import pytest
from typing_extensions import NotRequired

from maya_mcp.tools.curve import CurveCvsOutput, CurveInfoOutput, curve_cvs, curve_info


class TestCurveOutputTypes:
    """Tests for public curve TypedDict return annotations."""

    def test_curve_tools_use_typed_outputs(self) -> None:
        """Curve tools expose typed output models."""
        assert get_type_hints(curve_info)["return"] is CurveInfoOutput
        assert get_type_hints(curve_cvs)["return"] is CurveCvsOutput

    def test_curve_outputs_mark_dense_and_truncated_fields_optional(self) -> None:
        """Curve payloads model fields that only appear on successful queries."""
        hints = get_type_hints(CurveInfoOutput, include_extras=True)
        assert get_origin(hints["shape"]) is NotRequired
        assert get_origin(hints["knots"]) is NotRequired
        assert "truncated" in CurveCvsOutput.__optional_keys__
        assert "_size_warning" in CurveCvsOutput.__optional_keys__


class TestCurveInfo:
    """Tests for the curve.info tool."""

    def test_curve_info_success(self) -> None:
        """Curve info returns degree, spans, form, cv_count, knots, length, bbox."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "curve1",
                "exists": True,
                "is_curve": True,
                "shape": "curveShape1",
                "degree": 3,
                "spans": 4,
                "form": "open",
                "cv_count": 7,
                "knots": [0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 4.0, 4.0],
                "length": 12.5,
                "bounding_box": [-1.0, 0.0, -1.0, 5.0, 3.0, 1.0],
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.curve.get_client", return_value=mock_client):
            result = curve_info("curve1")

        assert result["is_curve"] is True
        assert result["degree"] == 3
        assert result["spans"] == 4
        assert result["form"] == "open"
        assert result["cv_count"] == 7
        assert len(result["knots"]) == 9
        assert result["length"] == 12.5
        assert len(result["bounding_box"]) == 6
        assert result["errors"] is None

    def test_curve_info_nonexistent(self) -> None:
        """Curve info returns error for nonexistent node."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "doesNotExist",
                "exists": False,
                "is_curve": False,
                "errors": {"_node": "Node 'doesNotExist' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.curve.get_client", return_value=mock_client):
            result = curve_info("doesNotExist")

        assert result["exists"] is False
        assert result["errors"]["_node"] is not None

    def test_curve_info_not_a_curve(self) -> None:
        """Curve info returns error for non-curve node."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "exists": True,
                "is_curve": False,
                "errors": {"_curve": "Node is not a nurbsCurve (type: mesh)"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.curve.get_client", return_value=mock_client):
            result = curve_info("pCube1")

        assert result["is_curve"] is False
        assert "_curve" in result["errors"]

    def test_curve_info_closed_form(self) -> None:
        """Curve info correctly reports closed form."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "circle1",
                "exists": True,
                "is_curve": True,
                "shape": "circleShape1",
                "degree": 3,
                "spans": 8,
                "form": "periodic",
                "cv_count": 8,
                "knots": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "length": 6.28,
                "bounding_box": [-1.0, 0.0, -1.0, 1.0, 0.0, 1.0],
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.curve.get_client", return_value=mock_client):
            result = curve_info("circle1")

        assert result["form"] == "periodic"
        assert result["cv_count"] == 8

    def test_curve_info_invalid_name(self) -> None:
        """Curve info raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            curve_info("curve1;bad")


class TestCurveCvs:
    """Tests for the curve.cvs tool."""

    def test_curve_cvs_success(self) -> None:
        """Curve CVs returns paginated CV positions."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "curve1",
                "exists": True,
                "is_curve": True,
                "shape": "curveShape1",
                "cv_count": 7,
                "cvs": [
                    [0.0, 0.0, 0.0],
                    [1.0, 1.0, 0.0],
                    [2.0, 0.0, 0.0],
                ],
                "offset": 0,
                "count": 3,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.curve.get_client", return_value=mock_client):
            result = curve_cvs("curve1", offset=0, limit=3)

        assert result["cv_count"] == 7
        assert len(result["cvs"]) == 3
        assert result["cvs"][0] == [0.0, 0.0, 0.0]
        assert result["offset"] == 0
        assert result["count"] == 3
        assert result["errors"] is None

    def test_curve_cvs_with_offset(self) -> None:
        """Curve CVs respects offset parameter."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "curve1",
                "exists": True,
                "is_curve": True,
                "shape": "curveShape1",
                "cv_count": 7,
                "cvs": [
                    [3.0, 2.0, 0.0],
                    [4.0, 0.0, 0.0],
                ],
                "offset": 3,
                "count": 2,
                "truncated": True,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.curve.get_client", return_value=mock_client):
            result = curve_cvs("curve1", offset=3, limit=2)

        assert result["offset"] == 3
        assert result["count"] == 2
        assert result["truncated"] is True

    def test_curve_cvs_negative_offset(self) -> None:
        """Curve CVs raises ValueError for negative offset."""
        with pytest.raises(ValueError, match="offset must be non-negative"):
            curve_cvs("curve1", offset=-1)

    def test_curve_cvs_invalid_name(self) -> None:
        """Curve CVs raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            curve_cvs("curve1;bad")
