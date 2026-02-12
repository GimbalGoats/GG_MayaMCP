"""Node tools for Maya MCP.

This module provides tools for listing, creating, deleting, and querying
comprehensive information about Maya nodes.
"""

from __future__ import annotations

import json
from typing import Any

from maya_mcp.transport import get_client
from maya_mcp.utils.response_guard import guard_response_size

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

    # Apply response size guard to prevent token budget explosion
    result = guard_response_size(result, list_key="nodes")

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


_VALID_INFO_CATEGORIES = frozenset(
    ["summary", "transform", "hierarchy", "attributes", "shape", "all"]
)

# Maximum number of keyable attributes to return before truncating.
# Prevents token budget explosion for nodes with many custom attributes.
_MAX_KEYABLE_ATTRIBUTES = 200


def _build_info_command(node_escaped: str, category_escaped: str) -> str:
    """Build the Maya Python command string for nodes_info.

    Uses a single static script with conditional sections based on category,
    wrapped in a top-level try/except to guarantee JSON output even if
    unexpected exceptions occur.

    Args:
        node_escaped: JSON-escaped node name string (e.g. '"pCube1"').
        category_escaped: JSON-escaped category string (e.g. '"summary"').

    Returns:
        Complete Python command string to execute in Maya.
    """
    return f"""import maya.cmds as cmds
import json

node = {node_escaped}
category = {category_escaped}
result = {{"node": node, "info_category": category, "exists": False, "errors": {{}}}}

try:
    if not cmds.objExists(node):
        result["errors"]["_node"] = "Node '" + node + "' does not exist"
    else:
        result["exists"] = True
        result["node_type"] = cmds.nodeType(node)

        # --- summary ---
        if category in ("summary", "all"):
            try:
                _parent = cmds.listRelatives(node, parent=True) or []
                _children = cmds.listRelatives(node, children=True) or []
                result["parent"] = _parent[0] if _parent else None
                result["children_count"] = len(_children)
            except Exception as _e:
                result["errors"]["summary"] = str(_e)

        # --- transform ---
        if category in ("transform", "all"):
            try:
                for _attr in ["translateX", "translateY", "translateZ",
                               "rotateX", "rotateY", "rotateZ",
                               "scaleX", "scaleY", "scaleZ", "visibility"]:
                    if cmds.attributeQuery(_attr, node=node, exists=True):
                        result[_attr] = cmds.getAttr(node + "." + _attr)
                if cmds.attributeQuery("translate", node=node, exists=True):
                    _t = cmds.getAttr(node + ".translate")[0]
                    result["translate"] = list(_t)
                if cmds.attributeQuery("rotate", node=node, exists=True):
                    _r = cmds.getAttr(node + ".rotate")[0]
                    result["rotate"] = list(_r)
                if cmds.attributeQuery("scale", node=node, exists=True):
                    _s = cmds.getAttr(node + ".scale")[0]
                    result["scale"] = list(_s)
            except Exception as _e:
                result["errors"]["transform"] = str(_e)

        # --- hierarchy ---
        if category in ("hierarchy", "all"):
            try:
                _hp = cmds.listRelatives(node, parent=True, fullPath=True) or []
                _hc = cmds.listRelatives(node, children=True) or []
                _full_path = cmds.ls(node, long=True) or [node]
                if category == "all":
                    result["parent_full_path"] = _hp[0] if _hp else None
                else:
                    result["parent"] = _hp[0] if _hp else None
                result["children"] = _hc
                result["full_path"] = _full_path[0]
            except Exception as _e:
                result["errors"]["hierarchy"] = str(_e)

        # --- attributes ---
        if category in ("attributes", "all"):
            try:
                _keyable = cmds.listAttr(node, keyable=True) or []
                _user_defined = cmds.listAttr(node, userDefined=True) or []
                _all_attrs = list(dict.fromkeys(_keyable + _user_defined))
                _total_attr_count = len(_all_attrs)
                _truncated = False
                if _total_attr_count > {_MAX_KEYABLE_ATTRIBUTES}:
                    _all_attrs = _all_attrs[:{_MAX_KEYABLE_ATTRIBUTES}]
                    _truncated = True
                _attr_values = {{}}
                _attr_errors = {{}}
                for _a in _all_attrs:
                    try:
                        _val = cmds.getAttr(node + "." + _a)
                        if isinstance(_val, list) and len(_val) == 1 and isinstance(_val[0], tuple):
                            _val = list(_val[0])
                        _attr_values[_a] = _val
                    except Exception as _ae:
                        _attr_errors[_a] = str(_ae)
                result["keyable_attributes"] = _attr_values
                result["keyable_count"] = len(_attr_values)
                if _truncated:
                    result["keyable_truncated"] = True
                    result["keyable_total_count"] = _total_attr_count
                if _attr_errors:
                    result["errors"]["attributes"] = _attr_errors
            except Exception as _e:
                result["errors"]["attributes"] = str(_e)

        # --- shape ---
        if category in ("shape", "all"):
            try:
                _shapes = cmds.listRelatives(node, shapes=True) or []
                _shape_info = []
                for _s in _shapes:
                    _s_type = cmds.nodeType(_s)
                    _conns = cmds.listConnections(_s) or []
                    _shape_info.append({{"name": _s, "type": _s_type, "connections_count": len(_conns)}})
                result["shapes"] = _shape_info
                result["shape_count"] = len(_shape_info)
            except Exception as _e:
                result["errors"]["shape"] = str(_e)

except Exception as _top_err:
    result["errors"]["_exception"] = str(_top_err)

print(json.dumps(result))
"""


def nodes_info(
    node: str,
    info_category: str = "summary",
) -> dict[str, Any]:
    """Get comprehensive information about a Maya node in a single call.

    Consolidates what would otherwise require multiple attributes.get and
    nodes.list calls into one tool invocation, reducing LLM tool-call chaining.

    Args:
        node: Name of the node to query.
        info_category: Category of information to retrieve:
            - "summary" (default): node type, parent, children count, exists
            - "transform": translate, rotate, scale, visibility
            - "hierarchy": parent (full path), children list, full path
            - "attributes": all keyable attributes with current values
            - "shape": shape node(s) under transform, shape type, connections
            - "all": everything combined (parent = short name from summary,
              parent_full_path = full DAG path from hierarchy)

    Returns:
        Dictionary with node information. Contents depend on info_category:
            - node: The queried node name
            - info_category: The category requested
            - exists: Whether the node exists
            - (category-specific fields)
            - errors: Error details if any queries failed, or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If node name or info_category is invalid.

    Example:
        >>> result = nodes_info("pCube1", info_category="transform")
        >>> print(f"Position: {result['translate']}")
    """
    # Input validation
    _validate_node_name(node)
    if info_category not in _VALID_INFO_CATEGORIES:
        raise ValueError(
            f"Invalid info_category: {info_category!r}. "
            f"Must be one of: {', '.join(sorted(_VALID_INFO_CATEGORIES))}"
        )

    client = get_client()

    node_escaped = json.dumps(node)
    category_escaped = json.dumps(info_category)

    command = _build_info_command(node_escaped, category_escaped)
    response = client.execute(command)

    # Parse the JSON response
    try:
        parsed: dict[str, Any] = json.loads(response)
    except json.JSONDecodeError:
        import ast

        parsed = ast.literal_eval(response)

    # Clean up errors field
    errors = parsed.get("errors", {})
    if not errors:
        parsed["errors"] = None

    # Apply response size guard for categories that may produce large output.
    # The guard truncates list fields; for keyable_attributes (a dict), truncation
    # is handled in Maya code via _MAX_KEYABLE_ATTRIBUTES. The guard here catches
    # any remaining oversized list fields (e.g. children, shapes).
    if info_category in ("attributes", "all", "hierarchy", "shape"):
        for key in ("children", "shapes"):
            if key in parsed:
                parsed = guard_response_size(parsed, list_key=key)

    return parsed


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
