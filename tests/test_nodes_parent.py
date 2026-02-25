"""Tests for nodes.parent tool."""

import json
from unittest.mock import MagicMock, patch

import pytest

from maya_mcp.tools.nodes import nodes_parent


@pytest.fixture
def mock_client():
    with patch("maya_mcp.tools.nodes.get_client") as mock_get_client:
        client = MagicMock()
        mock_get_client.return_value = client
        yield client


def test_nodes_parent_success(mock_client):
    """Test successful parenting of nodes."""
    # Mock Maya response
    mock_response = {"parented": ["pCube1", "pSphere1"], "errors": {}}
    mock_client.execute.return_value = json.dumps(mock_response)

    result = nodes_parent(nodes=["pCube1", "pSphere1"], parent="group1")

    assert result["parented"] == ["pCube1", "pSphere1"]
    assert result["count"] == 2
    assert result["errors"] is None

    # Verify command sent to Maya
    args, _ = mock_client.execute.call_args
    command = args[0]
    assert 'nodes = ["pCube1", "pSphere1"]' in command
    assert 'parent_node = "group1"' in command
    assert "relative_flag = False" in command
    assert "cmds.parent(node, parent_node, relative=relative_flag)" in command


def test_nodes_unparent_success(mock_client):
    """Test successful unparenting (parent to world)."""
    # Mock Maya response
    mock_response = {"parented": ["pCube1"], "errors": {}}
    mock_client.execute.return_value = json.dumps(mock_response)

    result = nodes_parent(nodes=["pCube1"], parent=None)

    assert result["parented"] == ["pCube1"]
    assert result["count"] == 1
    assert result["errors"] is None

    # Verify command sent to Maya
    args, _ = mock_client.execute.call_args
    command = args[0]
    assert "parent_node = None" in command
    assert "cmds.parent(node, world=True, relative=relative_flag)" in command


def test_nodes_parent_relative(mock_client):
    """Test parenting with relative flag."""
    # Mock Maya response
    mock_response = {"parented": ["pCube1"], "errors": {}}
    mock_client.execute.return_value = json.dumps(mock_response)

    result = nodes_parent(nodes=["pCube1"], parent="group1", relative=True)

    assert result["parented"] == ["pCube1"]

    # Verify command sent to Maya
    args, _ = mock_client.execute.call_args
    command = args[0]
    assert "relative_flag = True" in command


def test_nodes_parent_validation_error(mock_client):
    """Test validation error for empty nodes list."""
    with pytest.raises(ValueError, match="nodes list cannot be empty"):
        nodes_parent(nodes=[], parent="group1")


def test_nodes_parent_invalid_name(mock_client):
    """Test validation error for invalid node name."""
    with pytest.raises(ValueError, match="Invalid characters"):
        nodes_parent(nodes=["pCube1;"], parent="group1")


def test_nodes_parent_partial_failure(mock_client):
    """Test partial failure when parenting multiple nodes."""
    # Mock Maya response
    mock_response = {
        "parented": ["pCube1"],
        "errors": {"pSphere1": "Node 'pSphere1' does not exist"},
    }
    mock_client.execute.return_value = json.dumps(mock_response)

    result = nodes_parent(nodes=["pCube1", "pSphere1"], parent="group1")

    assert result["parented"] == ["pCube1"]
    assert result["count"] == 1
    assert result["errors"] == {"pSphere1": "Node 'pSphere1' does not exist"}


def test_nodes_parent_target_missing(mock_client):
    """Test failure when parent node does not exist."""
    # Mock Maya response
    mock_response = {"parented": [], "errors": {"_parent": "Parent node 'group1' does not exist"}}
    mock_client.execute.return_value = json.dumps(mock_response)

    result = nodes_parent(nodes=["pCube1"], parent="group1")

    assert result["parented"] == []
    assert result["count"] == 0
    assert result["errors"]["_parent"] == "Parent node 'group1' does not exist"
