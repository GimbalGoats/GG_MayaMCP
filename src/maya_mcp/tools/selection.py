"""Selection tools for Maya MCP.

This module provides tools for querying and modifying the Maya selection.
"""

from __future__ import annotations

import json
from typing import Any

from maya_mcp.transport import get_client

# Characters that are not allowed in node names for security
FORBIDDEN_NODE_CHARS = frozenset([";", "|", "&", "$", "`", "\n", "\r"])


def _validate_node_name(node: str) -> None:
    """Validate a node name for security.

    Args:
        node: The node name to validate.

    Raises:
        ValueError: If the node name is invalid or contains forbidden characters.
    """
    if not node or not isinstance(node, str):
        raise ValueError(f"Invalid node name: {node}")
    if any(c in node for c in FORBIDDEN_NODE_CHARS):
        raise ValueError(f"Invalid characters in node name: {node}")


def selection_get() -> dict[str, Any]:
    """Get the current selection in Maya.

    Returns the list of currently selected nodes.

    Returns:
        Dictionary with selection:
            - selection: List of selected node names
            - count: Number of selected items

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.

    Example:
        >>> result = selection_get()
        >>> if result['count'] > 0:
        ...     print(f"Selected: {result['selection']}")
    """
    client = get_client()

    command = """
import maya.cmds as cmds
import json

selection = cmds.ls(selection=True) or []
print(json.dumps(selection))
"""

    response = client.execute(command)

    # Parse the JSON response
    try:
        selection = json.loads(response)
    except json.JSONDecodeError:
        # Try to handle Maya's Python list output format
        import ast

        selection = ast.literal_eval(response)

    if not isinstance(selection, list):
        selection = []

    return {
        "selection": selection,
        "count": len(selection),
    }


def selection_clear() -> dict[str, Any]:
    """Clear the Maya selection.

    Deselects all currently selected nodes.

    Returns:
        Dictionary with empty selection state:
            - selection: Empty list
            - count: 0

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.

    Example:
        >>> result = selection_clear()
        >>> print(f"Selection cleared: {result['count']} items")
    """
    client = get_client()

    command = """
import maya.cmds as cmds
import json

cmds.select(clear=True)
selection = cmds.ls(selection=True) or []
print(json.dumps(selection))
"""

    response = client.execute(command)

    # Parse the JSON response
    try:
        selection = json.loads(response)
    except json.JSONDecodeError:
        selection = []

    if not isinstance(selection, list):
        selection = []

    return {
        "selection": selection,
        "count": len(selection),
    }


def selection_set(
    nodes: list[str],
    add: bool = False,
    deselect: bool = False,
) -> dict[str, Any]:
    """Set the Maya selection.

    Modifies the current selection by selecting, adding to, or
    removing from the selection.

    Args:
        nodes: List of node names to operate on.
        add: If True, add to existing selection instead of replacing.
        deselect: If True, remove from selection instead of adding.

    Returns:
        Dictionary with new selection state:
            - selection: List of selected node names after operation
            - count: Number of selected items

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If nodes list is empty or contains invalid names.

    Example:
        >>> # Replace selection
        >>> result = selection_set(["pCube1", "pSphere1"])
        >>>
        >>> # Add to selection
        >>> result = selection_set(["pCone1"], add=True)
        >>>
        >>> # Remove from selection
        >>> result = selection_set(["pCube1"], deselect=True)
    """
    # Input validation
    if not nodes:
        raise ValueError("nodes list cannot be empty")

    for node in nodes:
        _validate_node_name(node)

    if add and deselect:
        raise ValueError("Cannot specify both add=True and deselect=True")

    client = get_client()

    # Build the Maya command
    # We use json.dumps to safely escape the node names
    nodes_escaped = json.dumps(nodes)

    if deselect:
        command = f"""
import maya.cmds as cmds
import json

nodes = {nodes_escaped}
cmds.select(nodes, deselect=True)
selection = cmds.ls(selection=True) or []
print(json.dumps(selection))
"""
    elif add:
        command = f"""
import maya.cmds as cmds
import json

nodes = {nodes_escaped}
cmds.select(nodes, add=True)
selection = cmds.ls(selection=True) or []
print(json.dumps(selection))
"""
    else:
        command = f"""
import maya.cmds as cmds
import json

nodes = {nodes_escaped}
cmds.select(nodes, replace=True)
selection = cmds.ls(selection=True) or []
print(json.dumps(selection))
"""

    response = client.execute(command)

    # Parse the JSON response
    try:
        selection = json.loads(response)
    except json.JSONDecodeError:
        # Try to handle Maya's Python list output format
        import ast

        selection = ast.literal_eval(response)

    if not isinstance(selection, list):
        selection = []

    return {
        "selection": selection,
        "count": len(selection),
    }
