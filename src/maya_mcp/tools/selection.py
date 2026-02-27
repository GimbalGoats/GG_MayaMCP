"""Selection tools for Maya MCP.

This module provides tools for querying and modifying the Maya selection,
including component-level selection (vertices, edges, faces).
"""

from __future__ import annotations

import json
from typing import Any, Literal

from maya_mcp.transport import get_client
from maya_mcp.utils.parsing import parse_json_response
from maya_mcp.utils.response_guard import guard_response_size

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


def _validate_component_name(component: str) -> None:
    """Validate a component specification for security.

    Component syntax uses `[`, `]`, `:`, and `.` characters
    (e.g., `pCube1.vtx[0:10]`). These are allowed but shell
    metacharacters are still blocked.

    Args:
        component: The component specification to validate.

    Raises:
        ValueError: If the component contains forbidden characters.
    """
    if not component or not isinstance(component, str):
        raise ValueError(f"Invalid component specification: {component}")
    if any(c in component for c in FORBIDDEN_NODE_CHARS):
        raise ValueError(f"Invalid characters in component specification: {component}")


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
    selection = parse_json_response(response)

    if not isinstance(selection, list):
        selection = []

    return {
        "selection": selection,
        "count": len(selection),
    }


def selection_set_components(
    components: list[str],
    add: bool = False,
    deselect: bool = False,
) -> dict[str, Any]:
    """Select mesh components (vertices, edges, or faces).

    Selects components specified by Maya component notation
    (e.g., "pCube1.vtx[0:10]", "pSphere1.e[5]", "pPlane1.f[0:99]").

    Args:
        components: List of component specifications in Maya notation.
            Examples:
            - "pCube1.vtx[0]" - single vertex
            - "pCube1.vtx[0:10]" - vertex range
            - "pCube1.e[5]" - single edge
            - "pCube1.f[0:99]" - face range
        add: If True, add to existing selection instead of replacing.
        deselect: If True, remove from selection instead of adding.

    Returns:
        Dictionary with selection result:
            - selection: List of currently selected components
            - count: Number of selected components
            - errors: Map of component to error message, or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If components list is empty or contains invalid specifications.

    Example:
        >>> result = selection_set_components(["pCube1.vtx[0:7]"])
        >>> print(f"Selected {result['count']} vertices")
    """
    if not components:
        raise ValueError("components list cannot be empty")

    for comp in components:
        _validate_component_name(comp)

    if add and deselect:
        raise ValueError("Cannot specify both add=True and deselect=True")

    client = get_client()
    components_escaped = json.dumps(components)

    if deselect:
        mode = "deselect=True"
    elif add:
        mode = "add=True"
    else:
        mode = "replace=True"

    command = f"""
import maya.cmds as cmds
import json

components = {components_escaped}
result = {{"selection": [], "errors": {{}}}}

valid_components = []
for comp in components:
    try:
        if cmds.objExists(comp):
            valid_components.append(comp)
        else:
            result["errors"][comp] = "Component '" + comp + "' does not exist"
    except Exception as e:
        result["errors"][comp] = str(e)

if valid_components:
    try:
        cmds.select(valid_components, {mode})
        result["selection"] = cmds.ls(selection=True, flatten=True) or []
    except Exception as e:
        result["errors"]["_select"] = str(e)

result["count"] = len(result["selection"])
print(json.dumps(result))
"""

    response = client.execute(command)
    parsed = parse_json_response(response)

    selection = parsed.get("selection", [])
    errors = parsed.get("errors", {})

    result: dict[str, Any] = {
        "selection": selection,
        "count": len(selection),
    }

    if errors:
        result["errors"] = errors
    else:
        result["errors"] = None

    result = guard_response_size(result, list_key="selection")

    return result


def selection_get_components() -> dict[str, Any]:
    """Get the currently selected mesh components.

    Returns the selected components grouped by type (vertex, edge, face)
    with their indices.

    Returns:
        Dictionary with component selection:
            - selection: List of all selected components (flattened)
            - vertices: List of selected vertex specifications
            - edges: List of selected edge specifications
            - faces: List of selected face specifications
            - vertex_count: Number of selected vertices
            - edge_count: Number of selected edges
            - face_count: Number of selected faces
            - total_count: Total number of selected components
            - has_components: True if any components are selected

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.

    Example:
        >>> result = selection_get_components()
        >>> print(f"Selected {result['vertex_count']} vertices")
        >>> for v in result['vertices']:
        ...     print(v)
    """
    client = get_client()

    command = """
import maya.cmds as cmds
import json

result = {
    "selection": [],
    "vertices": [],
    "edges": [],
    "faces": [],
    "vertex_count": 0,
    "edge_count": 0,
    "face_count": 0,
    "total_count": 0,
    "has_components": False
}

try:
    all_sel = cmds.ls(selection=True, flatten=True) or []
    result["selection"] = all_sel
    result["total_count"] = len(all_sel)

    for item in all_sel:
        if ".vtx[" in item or ".vtxs[" in item:
            result["vertices"].append(item)
        elif ".e[" in item or ".edge[" in item:
            result["edges"].append(item)
        elif ".f[" in item or ".face[" in item:
            result["faces"].append(item)

    result["vertex_count"] = len(result["vertices"])
    result["edge_count"] = len(result["edges"])
    result["face_count"] = len(result["faces"])
    result["has_components"] = result["total_count"] > 0

except Exception as e:
    result["error"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    parsed = guard_response_size(parsed, list_key="selection")

    return parsed


def selection_convert_components(
    to_type: Literal["vertex", "edge", "face"],
    nodes: list[str] | None = None,
) -> dict[str, Any]:
    """Convert the current selection to a different component type.

    Converts selected components (or specified nodes) to vertices,
    edges, or faces.

    Args:
        to_type: Target component type: "vertex", "edge", or "face".
        nodes: Optional list of nodes to convert selection on.
            If None, uses current selection.

    Returns:
        Dictionary with converted selection:
            - selection: List of converted components
            - to_type: The target component type
            - count: Number of converted components
            - errors: Error details if any, or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If to_type is invalid or nodes contain invalid names.

    Example:
        >>> # Convert edge selection to faces
        >>> result = selection_convert_components("face")
        >>> print(f"Now have {result['count']} faces selected")
    """
    valid_types = {"vertex", "edge", "face"}
    if to_type not in valid_types:
        raise ValueError(
            f"Invalid to_type: {to_type!r}. Must be one of: {', '.join(sorted(valid_types))}"
        )

    if nodes is not None:
        for node in nodes:
            _validate_node_name(node)

    client = get_client()

    nodes_escaped = json.dumps(nodes) if nodes else "None"

    command = f"""
import maya.cmds as cmds
import json

to_type = {json.dumps(to_type)}
nodes = {nodes_escaped}
result = {{"selection": [], "to_type": to_type, "count": 0, "errors": {{}}}}

try:
    current_sel = cmds.ls(selection=True, flatten=True) or []

    if not current_sel and nodes:
        cmds.select(nodes, replace=True)

    sel = cmds.ls(selection=True) or []
    if sel:
        if to_type == "vertex":
            converted = cmds.polyListComponentConversion(sel, toVertex=True)
        elif to_type == "edge":
            converted = cmds.polyListComponentConversion(sel, toEdge=True)
        elif to_type == "face":
            converted = cmds.polyListComponentConversion(sel, toFace=True)

        if converted:
            cmds.select(converted, replace=True)
            result["selection"] = cmds.ls(selection=True, flatten=True) or []
        else:
            result["selection"] = []
    else:
        result["selection"] = []

    result["count"] = len(result["selection"])

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed = parse_json_response(response)

    selection = parsed.get("selection", [])
    errors = parsed.get("errors", {})

    result: dict[str, Any] = {
        "selection": selection,
        "to_type": to_type,
        "count": len(selection),
    }

    if errors:
        result["errors"] = errors
    else:
        result["errors"] = None

    result = guard_response_size(result, list_key="selection")

    return result


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
    selection = parse_json_response(response)

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
    selection = parse_json_response(response)

    if not isinstance(selection, list):
        selection = []

    return {
        "selection": selection,
        "count": len(selection),
    }
