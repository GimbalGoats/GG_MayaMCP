"""Node tools for Maya MCP.

This module provides tools for listing, creating, and deleting Maya nodes.
"""

from __future__ import annotations

import json
from typing import Any

from maya_mcp.transport import get_client

# Characters that are not allowed in patterns for security
FORBIDDEN_PATTERN_CHARS = frozenset([";", "|", "&", "$", "`", "\n", "\r", '"', "'"])

# Characters that are not allowed in node names for security
FORBIDDEN_NAME_CHARS = frozenset([";", "&", "$", "`", "\n", "\r"])

# Default limit for node listing to prevent token budget explosion
DEFAULT_NODE_LIMIT = 500


def _validate_pattern(pattern: str) -> None:
    """Validate a node name pattern for security.

    Args:
        pattern: The pattern to validate.

    Raises:
        ValueError: If the pattern contains forbidden characters.
    """
    if any(c in pattern for c in FORBIDDEN_PATTERN_CHARS):
        raise ValueError(f"Invalid characters in pattern: {pattern}")


def _validate_node_name(name: str) -> None:
    """Validate a node name for security.

    Args:
        name: The node name to validate.

    Raises:
        ValueError: If the name is invalid or contains forbidden characters.
    """
    if not name or not isinstance(name, str):
        raise ValueError(f"Invalid node name: {name}")
    if any(c in name for c in FORBIDDEN_NAME_CHARS):
        raise ValueError(f"Invalid characters in node name: {name}")


def nodes_list(
    node_type: str | None = None,
    pattern: str = "*",
    long_names: bool = False,
    limit: int | None = DEFAULT_NODE_LIMIT,
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
        limit: Maximum number of nodes to return. Default is 500.
            Set to None or 0 for unlimited (use with caution in large scenes).
            When truncated, response includes 'truncated' and 'total_count'.

    Returns:
        Dictionary with node list:
            - nodes: List of node names
            - count: Number of nodes returned
            - truncated: True if results were truncated (only if limit hit)
            - total_count: Total nodes matching before limit (only if truncated)

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

    # Apply limit to prevent token budget explosion
    total_count = len(nodes)
    truncated = False
    if limit and limit > 0 and total_count > limit:
        nodes = nodes[:limit]
        truncated = True

    result: dict[str, Any] = {
        "nodes": nodes,
        "count": len(nodes),
    }

    if truncated:
        result["truncated"] = True
        result["total_count"] = total_count

    return result


def nodes_create(
    node_type: str,
    name: str | None = None,
    parent: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new node in Maya.

    Creates a node of the specified type with optional name, parent, and
    initial attribute values.

    Args:
        node_type: Type of node to create (e.g., "transform", "locator", "joint").
        name: Desired node name. Maya may modify for uniqueness.
        parent: Parent node to parent under.
        attributes: Initial attribute values to set after creation.

    Returns:
        Dictionary with creation result:
            - node: Name of the created node
            - node_type: Type of node created
            - parent: Parent node (if parented), or None
            - attributes_set: List of attributes successfully set
            - attribute_errors: Map of attribute to error message, or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If node_type, name, or parent contains invalid characters.

    Example:
        >>> result = nodes_create("transform", name="myGroup")
        >>> print(f"Created: {result['node']}")
    """
    # Input validation
    _validate_pattern(node_type)
    if name is not None:
        _validate_node_name(name)
    if parent is not None:
        _validate_node_name(parent)

    client = get_client()

    # Build the Maya command
    type_escaped = json.dumps(node_type)
    name_escaped = json.dumps(name) if name else "None"
    parent_escaped = json.dumps(parent) if parent else "None"
    attrs_escaped = json.dumps(attributes) if attributes else "{}"

    command = f"""
import maya.cmds as cmds
import json

node_type = {type_escaped}
desired_name = {name_escaped}
parent_node = {parent_escaped}
attrs = {attrs_escaped}

result = {{"node": None, "node_type": node_type, "parent": None, "attributes_set": [], "attribute_errors": {{}}}}

# Mapping of primitive types to their creation functions
# These return [transform, shape/history] instead of just the node
PRIMITIVE_CREATORS = {{
    "polyCube": lambda n: cmds.polyCube(name=n)[0] if n else cmds.polyCube()[0],
    "polySphere": lambda n: cmds.polySphere(name=n)[0] if n else cmds.polySphere()[0],
    "polyCylinder": lambda n: cmds.polyCylinder(name=n)[0] if n else cmds.polyCylinder()[0],
    "polyCone": lambda n: cmds.polyCone(name=n)[0] if n else cmds.polyCone()[0],
    "polyPlane": lambda n: cmds.polyPlane(name=n)[0] if n else cmds.polyPlane()[0],
    "polyTorus": lambda n: cmds.polyTorus(name=n)[0] if n else cmds.polyTorus()[0],
    "nurbsCircle": lambda n: cmds.circle(name=n)[0] if n else cmds.circle()[0],
    "nurbsCurve": lambda n: cmds.curve(d=1, p=[(0,0,0), (1,0,0)], name=n) if n else cmds.curve(d=1, p=[(0,0,0), (1,0,0)]),
    "locator": lambda n: cmds.spaceLocator(name=n)[0] if n else cmds.spaceLocator()[0],
    "camera": lambda n: cmds.camera(name=n)[0] if n else cmds.camera()[0],
}}

try:
    # Create the node using appropriate method
    if node_type in PRIMITIVE_CREATORS:
        created = PRIMITIVE_CREATORS[node_type](desired_name)
    elif desired_name:
        created = cmds.createNode(node_type, name=desired_name)
    else:
        created = cmds.createNode(node_type)
    result["node"] = created
    # Parent if requested
    if parent_node:
        if cmds.objExists(parent_node):
            cmds.parent(created, parent_node)
            result["parent"] = parent_node
        else:
            result["attribute_errors"]["_parent"] = f"Parent node '{{parent_node}}' does not exist"
    # Set initial attributes
    for attr, value in attrs.items():
        try:
            full_attr = f"{{created}}.{{attr}}"
            if not cmds.attributeQuery(attr, node=created, exists=True):
                result["attribute_errors"][attr] = f"Attribute '{{attr}}' not found"
            elif cmds.getAttr(full_attr, lock=True):
                result["attribute_errors"][attr] = f"Attribute '{{attr}}' is locked"
            else:
                if isinstance(value, (list, tuple)) and len(value) == 3:
                    cmds.setAttr(full_attr, value[0], value[1], value[2], type="double3")
                elif isinstance(value, str):
                    cmds.setAttr(full_attr, value, type="string")
                else:
                    cmds.setAttr(full_attr, value)
                result["attributes_set"].append(attr)
        except Exception as e:
            result["attribute_errors"][attr] = str(e)

except Exception as e:
    result["attribute_errors"]["_create"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)

    # Parse the JSON response
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError:
        import ast

        parsed = ast.literal_eval(response)

    # Check for creation error
    if "_create" in parsed.get("attribute_errors", {}):
        raise ValueError(parsed["attribute_errors"]["_create"])

    result: dict[str, Any] = {
        "node": parsed.get("node"),
        "node_type": parsed.get("node_type"),
        "parent": parsed.get("parent"),
        "attributes_set": parsed.get("attributes_set", []),
    }

    errors = parsed.get("attribute_errors", {})
    if errors:
        result["attribute_errors"] = errors
    else:
        result["attribute_errors"] = None

    return result


def nodes_delete(
    nodes: list[str],
    hierarchy: bool = False,
) -> dict[str, Any]:
    """Delete one or more nodes from the Maya scene.

    Args:
        nodes: List of node names to delete.
        hierarchy: If True, delete entire hierarchy below each node.

    Returns:
        Dictionary with deletion result:
            - deleted: List of nodes successfully deleted
            - count: Number of nodes deleted
            - errors: Map of node name to error message, or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If node names contain invalid characters.

    Example:
        >>> result = nodes_delete(["pCube1", "pSphere1"])
        >>> print(f"Deleted {result['count']} nodes")
    """
    # Input validation
    if not nodes:
        raise ValueError("nodes list cannot be empty")
    for node in nodes:
        _validate_node_name(node)

    client = get_client()

    # Build the Maya command
    nodes_escaped = json.dumps(nodes)
    hierarchy_flag = "True" if hierarchy else "False"

    command = f"""
import maya.cmds as cmds
import json

nodes_to_delete = {nodes_escaped}
delete_hierarchy = {hierarchy_flag}

result = {{"deleted": [], "errors": {{}}}}

for node in nodes_to_delete:
    try:
        if not cmds.objExists(node):
            result["errors"][node] = f"Node '{{node}}' does not exist"
        else:
            if delete_hierarchy:
                # Get all descendants and delete
                descendants = cmds.listRelatives(node, allDescendents=True, fullPath=True) or []
                cmds.delete(node)
            else:
                cmds.delete(node)
            result["deleted"].append(node)
    except Exception as e:
        result["errors"][node] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)

    # Parse the JSON response
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError:
        import ast

        parsed = ast.literal_eval(response)

    deleted = parsed.get("deleted", [])
    errors = parsed.get("errors", {})

    result: dict[str, Any] = {
        "deleted": deleted,
        "count": len(deleted),
    }

    if errors:
        result["errors"] = errors
    else:
        result["errors"] = None

    return result
