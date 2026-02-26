"""Tests for the nodes.rename tool."""

import json
from unittest.mock import MagicMock, patch

import pytest

from maya_mcp.tools.nodes import nodes_rename


class TestNodesRename:
    """Tests for the nodes.rename tool."""

    def test_nodes_rename_simple(self) -> None:
        """Rename a single node successfully."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "renamed": {"pCube1": "myCube"},
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_rename({"pCube1": "myCube"})

        assert result["renamed"] == {"pCube1": "myCube"}
        assert result["errors"] is None

    def test_nodes_rename_collision(self) -> None:
        """Rename reflects actual name assigned by Maya (collision)."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "renamed": {"pCube1": "myCube1"},
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            # Requested "myCube", but got "myCube1"
            result = nodes_rename({"pCube1": "myCube"})

        assert result["renamed"] == {"pCube1": "myCube1"}
        assert result["errors"] is None

    def test_nodes_rename_multiple(self) -> None:
        """Rename multiple nodes."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "renamed": {
                    "pCube1": "myCube",
                    "pSphere1": "mySphere",
                },
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_rename(
                {
                    "pCube1": "myCube",
                    "pSphere1": "mySphere",
                }
            )

        assert result["renamed"]["pCube1"] == "myCube"
        assert result["renamed"]["pSphere1"] == "mySphere"
        assert result["errors"] is None

    def test_nodes_rename_partial_failure(self) -> None:
        """Rename with some nodes failing."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "renamed": {"pCube1": "myCube"},
                "errors": {"pSphere1": "Node 'pSphere1' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_rename(
                {
                    "pCube1": "myCube",
                    "pSphere1": "mySphere",
                }
            )

        assert result["renamed"] == {"pCube1": "myCube"}
        assert result["errors"] == {"pSphere1": "Node 'pSphere1' does not exist"}

    def test_nodes_rename_empty_mapping(self) -> None:
        """Rename rejects empty mapping."""
        with pytest.raises(ValueError, match="cannot be empty"):
            nodes_rename({})

    def test_nodes_rename_invalid_old_name(self) -> None:
        """Rename rejects invalid old node name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            nodes_rename({"node; bad": "newNode"})

    def test_nodes_rename_invalid_new_name(self) -> None:
        """Rename rejects invalid new node name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            nodes_rename({"oldNode": "new; bad"})

    def test_nodes_rename_result_shape(self) -> None:
        """Rename result includes all required fields."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "renamed": {"node1": "newNode1"},
                "errors": {},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.nodes.get_client", return_value=mock_client):
            result = nodes_rename({"node1": "newNode1"})

        assert "renamed" in result
        assert "errors" in result
        assert isinstance(result["renamed"], dict)
