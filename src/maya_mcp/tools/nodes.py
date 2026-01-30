"""Node tools for Maya MCP.

This module provides tools for listing and querying Maya nodes.
"""

from __future__ import annotations

import json
from typing import Any

from maya_mcp.transport import get_client

# Characters that are not allowed in patterns for security
FORBIDDEN_PATTERN_CHARS = frozenset([";", "|", "&", "$", "`", "\n", "\r", '"', "'"])


def _validate_pattern(pattern: str) -> None:
    """Validate a node name pattern for security.

    Args:
        pattern: The pattern to validate.

    Raises:
        ValueError: If the pattern contains forbidden characters.
    """
    if any(c in pattern for c in FORBIDDEN_PATTERN_CHARS):
        raise ValueError(f"Invalid characters in pattern: {pattern}")


def nodes_list(
    node_type: str | None = None,
    pattern: str = "*",
    long_names: bool = False,
) -> dict[str, Any]:
    """List nodes in the Maya scene.

    Returns a list of nodes, optionally filtered by type and/or name pattern.

    Args:
        node_type: Filter by node type (e.g., "transform", "mesh", "camera").
            If None, returns all nodes.
        pattern: Name pattern filter. Supports wildcards (* and ?).
            Default is "*" (all names).
        long_names: If True, return full DAG paths. If False, return
            short names.

    Returns:
        Dictionary with node list:
            - nodes: List of node names
            - count: Number of nodes in the list

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If pattern contains invalid characters.

    Example:
        >>> result = nodes_list(node_type="mesh")
        >>> print(f"Found {result['count']} meshes")
        >>> for node in result['nodes']:
        ...     print(node)
    """
    # Input validation
    _validate_pattern(pattern)
    if node_type is not None:
        _validate_pattern(node_type)

    client = get_client()

    # Build the Maya command
    # We use json.dumps to safely escape the pattern string
    pattern_escaped = json.dumps(pattern)
    long_flag = "True" if long_names else "False"

    if node_type is not None:
        type_escaped = json.dumps(node_type)
        command = f"""
import maya.cmds as cmds
import json

nodes = cmds.ls({pattern_escaped}, type={type_escaped}, long={long_flag}) or []
print(json.dumps(nodes))
"""
    else:
        command = f"""
import maya.cmds as cmds
import json

nodes = cmds.ls({pattern_escaped}, long={long_flag}) or []
print(json.dumps(nodes))
"""

    response = client.execute(command)

    # Parse the JSON response
    try:
        nodes = json.loads(response)
    except json.JSONDecodeError:
        # Try to handle Maya's Python list output format
        import ast

        nodes = ast.literal_eval(response)

    if not isinstance(nodes, list):
        nodes = []

    return {
        "nodes": nodes,
        "count": len(nodes),
    }
