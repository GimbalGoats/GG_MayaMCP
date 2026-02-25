"""Tests for nodes.duplicate tool."""
from unittest.mock import MagicMock, patch
import json
import pytest

from maya_mcp.tools.nodes import nodes_duplicate

@pytest.fixture
def mock_client():
    with patch("maya_mcp.tools.nodes.get_client") as mock_get_client:
        client = MagicMock()
        mock_get_client.return_value = client
        yield client

def test_nodes_duplicate_success(mock_client):
    """Test successful duplication of nodes."""
    # Mock Maya response
    mock_response = {
        "duplicated": {"pCube1": "pCube2"},
        "errors": {}
    }
    mock_client.execute.return_value = json.dumps(mock_response)

    result = nodes_duplicate(nodes=["pCube1"])

    assert result["duplicated"]["pCube1"] == "pCube2"
    assert result["count"] == 1
    assert result["errors"] is None

    # Verify command sent to Maya
    args, _ = mock_client.execute.call_args
    command = args[0]
    assert 'nodes = ["pCube1"]' in command
    assert 'desired_name = None' in command
    assert "ic_flag = False" in command
    assert "un_flag = False" in command
    assert "po_flag = False" in command
    assert "cmds.duplicate(node, **kwargs)" in command

def test_nodes_duplicate_single_with_name(mock_client):
    """Test duplicating a single node with a new name."""
    # Mock Maya response
    mock_response = {
        "duplicated": {"pCube1": "myCube"},
        "errors": {}
    }
    mock_client.execute.return_value = json.dumps(mock_response)

    result = nodes_duplicate(nodes=["pCube1"], name="myCube")

    assert result["duplicated"]["pCube1"] == "myCube"
    assert result["count"] == 1

    # Verify command sent to Maya
    args, _ = mock_client.execute.call_args
    command = args[0]
    assert 'desired_name = "myCube"' in command

def test_nodes_duplicate_name_multiple_error(mock_client):
    """Test validation error when providing name for multiple nodes."""
    with pytest.raises(ValueError, match="Cannot specify name when duplicating multiple nodes"):
        nodes_duplicate(nodes=["pCube1", "pSphere1"], name="myCube")

def test_nodes_duplicate_options(mock_client):
    """Test duplication options (input connections, upstream nodes, parent only)."""
    # Mock Maya response
    mock_response = {
        "duplicated": {"pCube1": "pCube2"},
        "errors": {}
    }
    mock_client.execute.return_value = json.dumps(mock_response)

    result = nodes_duplicate(nodes=["pCube1"], input_connections=True, upstream_nodes=True, parent_only=True)

    # Verify command sent to Maya
    args, _ = mock_client.execute.call_args
    command = args[0]
    assert "ic_flag = True" in command
    assert "un_flag = True" in command
    assert "po_flag = True" in command

def test_nodes_duplicate_partial_failure(mock_client):
    """Test partial failure when duplicating multiple nodes."""
    # Mock Maya response
    mock_response = {
        "duplicated": {"pCube1": "pCube2"},
        "errors": {
            "pSphere1": "Node 'pSphere1' does not exist"
        }
    }
    mock_client.execute.return_value = json.dumps(mock_response)

    result = nodes_duplicate(nodes=["pCube1", "pSphere1"])

    assert result["duplicated"] == {"pCube1": "pCube2"}
    assert result["count"] == 1
    assert result["errors"] == {"pSphere1": "Node 'pSphere1' does not exist"}

def test_nodes_duplicate_validation_error(mock_client):
    """Test validation error for empty nodes list."""
    with pytest.raises(ValueError, match="nodes list cannot be empty"):
        nodes_duplicate(nodes=[])

def test_nodes_duplicate_invalid_name(mock_client):
    """Test validation error for invalid node name."""
    with pytest.raises(ValueError, match="Invalid characters"):
        nodes_duplicate(nodes=["pCube1;"])
