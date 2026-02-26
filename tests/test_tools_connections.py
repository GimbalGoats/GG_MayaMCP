"""Tests for connections tools.

These tests verify the MCP tools for managing node connections
work correctly with mocked transport.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from maya_mcp.tools.connections import (
    connections_connect,
    connections_disconnect,
    connections_get,
    connections_history,
    connections_list,
)


class TestConnectionsList:
    """Tests for the connections.list tool."""

    def test_connections_list_incoming(self) -> None:
        """List incoming connections."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "connections": [
                    {
                        "source": "polyCube1.output",
                        "source_node": "polyCube1",
                        "source_type": "polyCube",
                        "destination": "pCubeShape1.inMesh",
                        "destination_node": "pCubeShape1",
                        "destination_type": "mesh",
                        "direction": "incoming",
                    }
                ],
                "count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_list("pCube1", direction="incoming")

        assert result["node"] == "pCube1"
        assert result["count"] == 1
        assert len(result["connections"]) == 1
        assert result["connections"][0]["direction"] == "incoming"
        assert result["errors"] is None

    def test_connections_list_outgoing(self) -> None:
        """List outgoing connections."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "ramp1",
                "connections": [
                    {
                        "source": "ramp1.outColor",
                        "source_node": "ramp1",
                        "source_type": "ramp",
                        "destination": "lambert1.color",
                        "destination_node": "lambert1",
                        "destination_type": "lambert",
                        "direction": "outgoing",
                    }
                ],
                "count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_list("ramp1", direction="outgoing")

        assert result["node"] == "ramp1"
        assert result["count"] == 1
        assert result["connections"][0]["direction"] == "outgoing"

    def test_connections_list_both_directions(self) -> None:
        """List both incoming and outgoing connections."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "connections": [
                    {
                        "source": "animCurveTL1.output",
                        "source_node": "animCurveTL1",
                        "source_type": "animCurveTL",
                        "destination": "pCube1.translateX",
                        "destination_node": "pCube1",
                        "destination_type": "transform",
                        "direction": "incoming",
                    },
                    {
                        "source": "pCube1.rotate",
                        "source_node": "pCube1",
                        "source_type": "transform",
                        "destination": "someConstraint.target",
                        "destination_node": "someConstraint",
                        "destination_type": "constraint",
                        "direction": "outgoing",
                    },
                ],
                "count": 2,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_list("pCube1", direction="both")

        assert result["count"] == 2

    def test_connections_list_with_type_filter(self) -> None:
        """List connections filtered by type."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "connections": [
                    {
                        "source": "animCurveTL1.output",
                        "source_node": "animCurveTL1",
                        "source_type": "animCurveTL",
                        "destination": "pCube1.translateX",
                        "destination_node": "pCube1",
                        "destination_type": "transform",
                        "direction": "incoming",
                    }
                ],
                "count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_list("pCube1", connections_type="animCurveTL")

        assert result["count"] == 1

    def test_connections_list_truncated(self) -> None:
        """List connections with truncation."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "connections": [
                    {"source": f"node{i}.out", "destination": "pCube1.in"} for i in range(500)
                ],
                "count": 500,
                "truncated": True,
                "total_count": 1000,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_list("pCube1", limit=500)

        assert result["truncated"] is True
        assert result["total_count"] == 1000

    def test_connections_list_node_not_exists(self) -> None:
        """List raises ValueError when node doesn't exist."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "nonExistent",
                "connections": [],
                "errors": {"_node": "Node 'nonExistent' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with (
            patch("maya_mcp.tools.connections.get_client", return_value=mock_client),
            pytest.raises(ValueError, match="does not exist"),
        ):
            connections_list("nonExistent")

    def test_connections_list_invalid_node_name(self) -> None:
        """List raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid"):
            connections_list("")

    def test_connections_list_forbidden_chars(self) -> None:
        """List raises ValueError for node names with forbidden characters."""
        with pytest.raises(ValueError, match="Invalid characters"):
            connections_list("node;rm -rf")


class TestConnectionsGet:
    """Tests for the connections.get tool."""

    def test_connections_get_specific_attrs(self) -> None:
        """Get connections for specific attributes."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "attributes": {
                    "translateX": {
                        "attribute": "translateX",
                        "connected": True,
                        "connections": [
                            {
                                "source": "animCurveTL1.output",
                                "source_node": "animCurveTL1",
                                "source_type": "animCurveTL",
                                "destination": "pCube1.translateX",
                                "direction": "incoming",
                            }
                        ],
                        "locked": False,
                        "type": "double",
                    },
                    "visibility": {
                        "attribute": "visibility",
                        "connected": False,
                        "connections": [],
                        "locked": False,
                        "type": "bool",
                    },
                },
                "count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_get("pCube1", ["translateX", "visibility"])

        assert result["node"] == "pCube1"
        assert result["count"] == 1
        assert result["attributes"]["translateX"]["connected"] is True
        assert result["attributes"]["visibility"]["connected"] is False

    def test_connections_get_all_attrs(self) -> None:
        """Get connections for all attributes."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "attributes": {
                    "translateX": {
                        "attribute": "translateX",
                        "connected": False,
                        "connections": [],
                        "locked": False,
                        "type": "double",
                    }
                },
                "count": 0,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_get("pCube1")

        assert result["node"] == "pCube1"

    def test_connections_get_node_not_exists(self) -> None:
        """Get raises ValueError when node doesn't exist."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "nonExistent",
                "attributes": {},
                "errors": {"_node": "Node 'nonExistent' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with (
            patch("maya_mcp.tools.connections.get_client", return_value=mock_client),
            pytest.raises(ValueError, match="does not exist"),
        ):
            connections_get("nonExistent", ["translateX"])

    def test_connections_get_invalid_node_name(self) -> None:
        """Get raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid"):
            connections_get("", ["translateX"])


class TestConnectionsConnect:
    """Tests for the connections.connect tool."""

    def test_connections_connect_success(self) -> None:
        """Connect two attributes successfully."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "connected": True,
                "source": "ramp1.outColor",
                "destination": "lambert1.color",
                "disconnected": [],
                "error": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_connect("ramp1.outColor", "lambert1.color")

        assert result["connected"] is True
        assert result["source"] == "ramp1.outColor"
        assert result["destination"] == "lambert1.color"
        assert result["disconnected"] == []

    def test_connections_connect_force_disconnects_existing(self) -> None:
        """Connect with force=True disconnects existing connections."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "connected": True,
                "source": "ramp1.outColor",
                "destination": "lambert1.color",
                "disconnected": ["checker1.outColor"],
                "error": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_connect("ramp1.outColor", "lambert1.color", force=True)

        assert result["connected"] is True
        assert "checker1.outColor" in result["disconnected"]

    def test_connections_connect_already_connected_error(self) -> None:
        """Connect fails when destination already connected and force=False."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "connected": False,
                "source": "ramp1.outColor",
                "destination": "lambert1.color",
                "disconnected": [],
                "error": "Destination 'lambert1.color' is already connected. Use force=True to replace.",
            }
        )
        mock_client.execute.return_value = mock_response

        with (
            patch("maya_mcp.tools.connections.get_client", return_value=mock_client),
            pytest.raises(ValueError, match="already connected"),
        ):
            connections_connect("ramp1.outColor", "lambert1.color", force=False)

    def test_connections_connect_source_not_exists(self) -> None:
        """Connect fails when source doesn't exist."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "connected": False,
                "source": "nonExistent.outColor",
                "destination": "lambert1.color",
                "disconnected": [],
                "error": "Source node 'nonExistent' does not exist",
            }
        )
        mock_client.execute.return_value = mock_response

        with (
            patch("maya_mcp.tools.connections.get_client", return_value=mock_client),
            pytest.raises(ValueError, match="does not exist"),
        ):
            connections_connect("nonExistent.outColor", "lambert1.color")

    def test_connections_connect_invalid_plug_format(self) -> None:
        """Connect raises ValueError for invalid plug format."""
        with pytest.raises(ValueError, match="Invalid"):
            connections_connect("invalidplug", "lambert1.color")

    def test_connections_connect_forbidden_chars(self) -> None:
        """Connect raises ValueError for plug names with forbidden characters."""
        with pytest.raises(ValueError, match="Invalid characters"):
            connections_connect("node;rm.out", "lambert1.color")


class TestConnectionsDisconnect:
    """Tests for the connections.disconnect tool."""

    def test_connections_disconnect_specific(self) -> None:
        """Disconnect a specific connection."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "disconnected": [{"source": "ramp1.outColor", "destination": "lambert1.color"}],
                "count": 1,
                "error": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_disconnect("ramp1.outColor", "lambert1.color")

        assert result["count"] == 1
        assert len(result["disconnected"]) == 1

    def test_connections_disconnect_all_incoming(self) -> None:
        """Disconnect all incoming connections to a destination."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "disconnected": [
                    {"source": "animCurveTL1.output", "destination": "pCube1.translateX"}
                ],
                "count": 1,
                "error": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_disconnect(destination="pCube1.translateX")

        assert result["count"] == 1

    def test_connections_disconnect_all_outgoing(self) -> None:
        """Disconnect all outgoing connections from a source."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "disconnected": [
                    {"source": "ramp1.outColor", "destination": "lambert1.color"},
                    {"source": "ramp1.outColor", "destination": "lambert2.color"},
                ],
                "count": 2,
                "error": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_disconnect(source="ramp1.outColor")

        assert result["count"] == 2

    def test_connections_disconnect_no_connection_exists(self) -> None:
        """Disconnect fails when no connection exists."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "disconnected": [],
                "count": 0,
                "error": "No connection exists between 'ramp1.outColor' and 'lambert1.color'",
            }
        )
        mock_client.execute.return_value = mock_response

        with (
            patch("maya_mcp.tools.connections.get_client", return_value=mock_client),
            pytest.raises(ValueError, match="No connection exists"),
        ):
            connections_disconnect("ramp1.outColor", "lambert1.color")

    def test_connections_disconnect_neither_provided(self) -> None:
        """Disconnect raises ValueError when neither source nor destination provided."""
        with pytest.raises(ValueError, match="At least one"):
            connections_disconnect()


class TestConnectionsHistory:
    """Tests for the connections.history tool."""

    def test_connections_history_input(self) -> None:
        """Get upstream (input) history."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCubeShape1",
                "history": [
                    {"name": "polyCube1", "type": "polyCube", "depth": 1, "direction": "input"},
                    {
                        "name": "polyExtrudeFace1",
                        "type": "polyExtrudeFace",
                        "depth": 2,
                        "direction": "input",
                    },
                ],
                "count": 2,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_history("pCubeShape1", direction="input")

        assert result["node"] == "pCubeShape1"
        assert result["count"] == 2
        assert all(h["direction"] == "input" for h in result["history"])

    def test_connections_history_output(self) -> None:
        """Get downstream (output) history."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "history": [
                    {
                        "name": "skinCluster1",
                        "type": "skinCluster",
                        "depth": 1,
                        "direction": "output",
                    },
                ],
                "count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_history("pCube1", direction="output")

        assert result["count"] == 1

    def test_connections_history_both(self) -> None:
        """Get both input and output history."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCubeShape1",
                "history": [
                    {"name": "polyCube1", "type": "polyCube", "depth": 1, "direction": "input"},
                    {
                        "name": "skinCluster1",
                        "type": "skinCluster",
                        "depth": 1,
                        "direction": "output",
                    },
                ],
                "count": 2,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_history("pCubeShape1", direction="both")

        assert result["count"] == 2

    def test_connections_history_with_depth_limit(self) -> None:
        """Get history with depth limit."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCubeShape1",
                "history": [
                    {"name": "polyCube1", "type": "polyCube", "depth": 1, "direction": "input"},
                ],
                "count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_history("pCubeShape1", direction="input", depth=1)

        assert result["count"] == 1

    def test_connections_history_truncated(self) -> None:
        """Get history with truncation."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCubeShape1",
                "history": [
                    {"name": f"node{i}", "type": "deformer", "depth": i, "direction": "input"}
                    for i in range(500)
                ],
                "count": 500,
                "truncated": True,
                "total_count": 1000,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.connections.get_client", return_value=mock_client):
            result = connections_history("pCubeShape1", limit=500)

        assert result["truncated"] is True
        assert result["total_count"] == 1000

    def test_connections_history_node_not_exists(self) -> None:
        """History raises ValueError when node doesn't exist."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "nonExistent",
                "history": [],
                "errors": {"_node": "Node 'nonExistent' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with (
            patch("maya_mcp.tools.connections.get_client", return_value=mock_client),
            pytest.raises(ValueError, match="does not exist"),
        ):
            connections_history("nonExistent")

    def test_connections_history_invalid_node_name(self) -> None:
        """History raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid"):
            connections_history("")
