"""Attribute tools for Maya MCP.

This module provides tools for getting and setting node attributes in Maya.
Supports batch operations to reduce tool call chaining.
"""

from __future__ import annotations

import json
from typing import Any

from maya_mcp.transport import get_client

# Characters that are not allowed in node/attribute names for security
FORBIDDEN_CHARS = frozenset([";", "|", "&", "$", "`", "\n", "\r"])


def _validate_node_name(node: str) -> None:
    """Validate a node name for security.

    Args:
        node: The node name to validate.

    Raises:
        ValueError: If the node name is invalid or contains forbidden characters.
    """
    if not node or not isinstance(node, str):
        raise ValueError(f"Invalid node name: {node}")
    if any(c in node for c in FORBIDDEN_CHARS):
        raise ValueError(f"Invalid characters in node name: {node}")


def _validate_attribute_name(attr: str) -> None:
    """Validate an attribute name for security.

    Args:
        attr: The attribute name to validate.

    Raises:
        ValueError: If the attribute name is invalid or contains forbidden characters.
    """
    if not attr or not isinstance(attr, str):
        raise ValueError(f"Invalid attribute name: {attr}")
    if any(c in attr for c in FORBIDDEN_CHARS):
        raise ValueError(f"Invalid characters in attribute name: {attr}")


def attributes_get(
    node: str,
    attributes: list[str],
) -> dict[str, Any]:
    """Get one or more attribute values from a Maya node.

    Supports batch attribute queries to reduce tool call chaining.
    Returns partial results if some attributes fail.

    Args:
        node: The node name to query.
        attributes: List of attribute names to get (e.g., ["translateX", "visibility"]).

    Returns:
        Dictionary with attribute values:
            - node: Node name queried
            - attributes: Map of attribute name to value
            - count: Number of attributes successfully retrieved
            - errors: Map of attribute name to error message (if any failed), or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails completely.
        ValueError: If node or attribute names are invalid.

    Example:
        >>> result = attributes_get("pCube1", ["translateX", "translateY", "visibility"])
        >>> print(f"translateX = {result['attributes']['translateX']}")
    """
    # Input validation
    _validate_node_name(node)
    if not attributes:
        raise ValueError("attributes list cannot be empty")
    for attr in attributes:
        _validate_attribute_name(attr)

    client = get_client()

    # Build the Maya command - get each attribute and collect results
    node_escaped = json.dumps(node)
    attrs_escaped = json.dumps(attributes)

    command = f"""
import maya.cmds as cmds
import json

node = {node_escaped}
attrs = {attrs_escaped}

result = {{"values": {{}}, "errors": {{}}}}

# Check if node exists
if not cmds.objExists(node):
    result["errors"]["_node"] = f"Node '{{node}}' does not exist"
else:
    for attr in attrs:
        try:
            full_attr = f"{{node}}.{{attr}}"
            if not cmds.attributeQuery(attr, node=node, exists=True):
                result["errors"][attr] = f"Attribute '{{attr}}' not found on node '{{node}}'"
            else:
                value = cmds.getAttr(full_attr)
                result["values"][attr] = value
        except Exception as e:
            result["errors"][attr] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)

    # Parse the JSON response
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError:
        import ast

        parsed = ast.literal_eval(response)

    values = parsed.get("values", {})
    errors = parsed.get("errors", {})

    # Check for node-level error
    if "_node" in errors:
        raise ValueError(errors["_node"])

    result: dict[str, Any] = {
        "node": node,
        "attributes": values,
        "count": len(values),
    }

    if errors:
        result["errors"] = errors
    else:
        result["errors"] = None

    return result


def attributes_set(
    node: str,
    attributes: dict[str, Any],
) -> dict[str, Any]:
    """Set one or more attribute values on a Maya node.

    Supports batch attribute setting to reduce tool call chaining.
    Returns partial results if some attributes fail.

    Args:
        node: The node name to modify.
        attributes: Map of attribute name to value.

    Returns:
        Dictionary with set results:
            - node: Node name modified
            - set: List of attributes successfully set
            - count: Number of attributes successfully set
            - errors: Map of attribute name to error message (if any failed), or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails completely.
        ValueError: If node or attribute names are invalid.

    Example:
        >>> result = attributes_set("pCube1", {"translateX": 10.0, "visibility": False})
        >>> print(f"Set {result['count']} attributes")
    """
    # Input validation
    _validate_node_name(node)
    if not attributes:
        raise ValueError("attributes dict cannot be empty")
    for attr in attributes:
        _validate_attribute_name(attr)

    client = get_client()

    # Build the Maya command - set each attribute and collect results
    node_escaped = json.dumps(node)
    attrs_escaped = json.dumps(attributes)

    command = f"""
import maya.cmds as cmds
import json

node = {node_escaped}
attrs = {attrs_escaped}

result = {{"set": [], "errors": {{}}}}

# Check if node exists
if not cmds.objExists(node):
    result["errors"]["_node"] = f"Node '{{node}}' does not exist"
else:
    for attr, value in attrs.items():
        try:
            full_attr = f"{{node}}.{{attr}}"
            if not cmds.attributeQuery(attr, node=node, exists=True):
                result["errors"][attr] = f"Attribute '{{attr}}' not found on node '{{node}}'"
            elif cmds.getAttr(full_attr, lock=True):
                result["errors"][attr] = f"Attribute '{{attr}}' is locked"
            else:
                # Handle different value types
                if isinstance(value, (list, tuple)) and len(value) == 3:
                    # Compound attribute like translate, rotate, scale
                    cmds.setAttr(full_attr, value[0], value[1], value[2], type="double3")
                elif isinstance(value, str):
                    cmds.setAttr(full_attr, value, type="string")
                else:
                    cmds.setAttr(full_attr, value)
                result["set"].append(attr)
        except Exception as e:
            result["errors"][attr] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)

    # Parse the JSON response
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError:
        import ast

        parsed = ast.literal_eval(response)

    set_attrs = parsed.get("set", [])
    errors = parsed.get("errors", {})

    # Check for node-level error
    if "_node" in errors:
        raise ValueError(errors["_node"])

    result: dict[str, Any] = {
        "node": node,
        "set": set_attrs,
        "count": len(set_attrs),
    }

    if errors:
        result["errors"] = errors
    else:
        result["errors"] = None

    return result
