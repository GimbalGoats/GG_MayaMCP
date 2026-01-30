"""Tests for attributes tools.

These tests verify the MCP tools for getting and setting node attributes
work correctly with mocked transport.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from maya_mcp.tools.attributes import attributes_get, attributes_set


class TestAttributesGet:
    """Tests for the attributes.get tool."""

    def test_attributes_get_single(self) -> None:
        """Get a single attribute value."""
        mock_client = MagicMock()
        mock_response = json.dumps({"values": {"translateX": 5.0}, "errors": {}})
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.attributes.get_client", return_value=mock_client):
            result = attributes_get("pCube1", ["translateX"])

        assert result["node"] == "pCube1"
        assert result["attributes"] == {"translateX": 5.0}
        assert result["count"] == 1
        assert result["errors"] is None

    def test_attributes_get_multiple(self) -> None:
        """Get multiple attribute values in batch."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "values": {
                    "translateX": 0.0,
                    "translateY": 10.5,
                    "visibility": True,
                },
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.attributes.get_client", return_value=mock_client):
            result = attributes_get("pCube1", ["translateX", "translateY", "visibility"])

        assert result["node"] == "pCube1"
        assert result["attributes"]["translateX"] == 0.0
        assert result["attributes"]["translateY"] == 10.5
        assert result["attributes"]["visibility"] is True
        assert result["count"] == 3
        assert result["errors"] is None

    def test_attributes_get_partial_failure(self) -> None:
        """Get returns partial results when some attributes fail."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "values": {"translateX": 5.0},
                "errors": {"nonExistent": "Attribute 'nonExistent' not found on node 'pCube1'"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.attributes.get_client", return_value=mock_client):
            result = attributes_get("pCube1", ["translateX", "nonExistent"])

        assert result["node"] == "pCube1"
        assert result["attributes"] == {"translateX": 5.0}
        assert result["count"] == 1
        assert result["errors"] is not None
        assert "nonExistent" in result["errors"]

    def test_attributes_get_node_not_exists(self) -> None:
        """Get raises ValueError when node doesn't exist."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {"values": {}, "errors": {"_node": "Node 'nonExistentNode' does not exist"}}
        )
        mock_client.execute.return_value = mock_response

        with (
            patch("maya_mcp.tools.attributes.get_client", return_value=mock_client),
            pytest.raises(ValueError, match="does not exist"),
        ):
            attributes_get("nonExistentNode", ["translateX"])

    def test_attributes_get_empty_list_raises(self) -> None:
        """Get raises ValueError for empty attributes list."""
        with pytest.raises(ValueError, match="cannot be empty"):
            attributes_get("pCube1", [])

    def test_attributes_get_invalid_node_name_raises(self) -> None:
        """Get raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid"):
            attributes_get("", ["translateX"])

    def test_attributes_get_invalid_attr_name_raises(self) -> None:
        """Get raises ValueError for invalid attribute name."""
        with pytest.raises(ValueError, match="Invalid"):
            attributes_get("pCube1", ["valid", ""])

    def test_attributes_get_forbidden_chars_raises(self) -> None:
        """Get raises ValueError for node names with forbidden characters."""
        with pytest.raises(ValueError, match="Invalid characters"):
            attributes_get("pCube1;rm -rf", ["translateX"])


class TestAttributesSet:
    """Tests for the attributes.set tool."""

    def test_attributes_set_single(self) -> None:
        """Set a single attribute value."""
        mock_client = MagicMock()
        mock_response = json.dumps({"set": ["translateX"], "errors": {}})
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.attributes.get_client", return_value=mock_client):
            result = attributes_set("pCube1", {"translateX": 10.0})

        assert result["node"] == "pCube1"
        assert result["set"] == ["translateX"]
        assert result["count"] == 1
        assert result["errors"] is None

    def test_attributes_set_multiple(self) -> None:
        """Set multiple attribute values in batch."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {"set": ["translateX", "translateY", "visibility"], "errors": {}}
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.attributes.get_client", return_value=mock_client):
            result = attributes_set(
                "pCube1",
                {"translateX": 5.0, "translateY": 10.0, "visibility": False},
            )

        assert result["node"] == "pCube1"
        assert set(result["set"]) == {"translateX", "translateY", "visibility"}
        assert result["count"] == 3
        assert result["errors"] is None

    def test_attributes_set_partial_failure(self) -> None:
        """Set returns partial results when some attributes fail."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "set": ["translateX"],
                "errors": {"lockedAttr": "Attribute 'lockedAttr' is locked"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.attributes.get_client", return_value=mock_client):
            result = attributes_set("pCube1", {"translateX": 5.0, "lockedAttr": 10.0})

        assert result["node"] == "pCube1"
        assert result["set"] == ["translateX"]
        assert result["count"] == 1
        assert result["errors"] is not None
        assert "lockedAttr" in result["errors"]

    def test_attributes_set_node_not_exists(self) -> None:
        """Set raises ValueError when node doesn't exist."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {"set": [], "errors": {"_node": "Node 'nonExistentNode' does not exist"}}
        )
        mock_client.execute.return_value = mock_response

        with (
            patch("maya_mcp.tools.attributes.get_client", return_value=mock_client),
            pytest.raises(ValueError, match="does not exist"),
        ):
            attributes_set("nonExistentNode", {"translateX": 5.0})

    def test_attributes_set_empty_dict_raises(self) -> None:
        """Set raises ValueError for empty attributes dict."""
        with pytest.raises(ValueError, match="cannot be empty"):
            attributes_set("pCube1", {})

    def test_attributes_set_invalid_node_name_raises(self) -> None:
        """Set raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid"):
            attributes_set("", {"translateX": 5.0})

    def test_attributes_set_invalid_attr_name_raises(self) -> None:
        """Set raises ValueError for invalid attribute name."""
        with pytest.raises(ValueError, match="Invalid"):
            attributes_set("pCube1", {"valid": 1.0, "": 2.0})

    def test_attributes_set_forbidden_chars_raises(self) -> None:
        """Set raises ValueError for attribute names with forbidden characters."""
        with pytest.raises(ValueError, match="Invalid characters"):
            attributes_set("pCube1", {"tx;rm -rf": 5.0})

    def test_attributes_set_compound_value(self) -> None:
        """Set handles compound (double3) attribute values."""
        mock_client = MagicMock()
        mock_response = json.dumps({"set": ["translate"], "errors": {}})
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.attributes.get_client", return_value=mock_client):
            result = attributes_set("pCube1", {"translate": [1.0, 2.0, 3.0]})

        assert result["node"] == "pCube1"
        assert result["set"] == ["translate"]
        assert result["count"] == 1
        assert result["errors"] is None
