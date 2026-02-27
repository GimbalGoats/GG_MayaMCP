"""Mesh tools for Maya MCP.

This module provides tools for querying mesh geometry and topology analysis.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from maya_mcp.transport import get_client
from maya_mcp.utils.parsing import parse_json_response
from maya_mcp.utils.response_guard import guard_response_size

FORBIDDEN_NODE_CHARS = frozenset([";", "|", "&", "$", "`", "\n", "\r"])

DEFAULT_VERTEX_LIMIT = 1000

DEFAULT_TOPOLOGY_LIMIT = 500


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


def mesh_info(node: str) -> dict[str, Any]:
    """Get mesh statistics for a polygon mesh.

    Returns vertex count, face count, edge count, bounding box,
    and UV set information.

    Args:
        node: Name of the mesh node (transform or shape).

    Returns:
        Dictionary with mesh statistics:
            - node: The queried node name
            - exists: Whether the node exists
            - is_mesh: Whether the node is a mesh
            - vertex_count: Number of vertices
            - face_count: Number of faces
            - edge_count: Number of edges
            - uv_count: Number of UVs
            - has_uvs: Whether the mesh has UVs
            - uv_sets: List of UV set names
            - bounding_box: [min_x, min_y, min_z, max_x, max_y, max_z]
            - errors: Error details if any queries failed, or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If node name contains invalid characters.

    Example:
        >>> result = mesh_info("pCube1")
        >>> print(f"Vertices: {result['vertex_count']}, Faces: {result['face_count']}")
    """
    _validate_node_name(node)

    client = get_client()
    node_escaped = json.dumps(node)

    command = f"""
import maya.cmds as cmds
import json

node = {node_escaped}
result = {{"node": node, "exists": False, "is_mesh": False, "errors": {{}}}}

try:
    if not cmds.objExists(node):
        result["errors"]["_node"] = "Node '" + node + "' does not exist"
    else:
        result["exists"] = True

        # Get shape node if transform was passed
        shapes = cmds.listRelatives(node, shapes=True, fullPath=False) or []
        if shapes:
            shape = shapes[0]
        else:
            shape = node

        node_type = cmds.nodeType(shape)
        if node_type != "mesh":
            result["errors"]["_mesh"] = "Node is not a mesh (type: " + node_type + ")"
        else:
            result["is_mesh"] = True
            result["shape"] = shape

            # Get counts
            result["vertex_count"] = cmds.polyEvaluate(shape, vertex=True)
            result["face_count"] = cmds.polyEvaluate(shape, face=True)
            result["edge_count"] = cmds.polyEvaluate(shape, edge=True)
            result["uv_count"] = cmds.polyEvaluate(shape, uvcoord=True)

            # UV sets
            uv_sets = cmds.polyUVSet(shape, query=True, allUVSets=True) or []
            result["uv_sets"] = uv_sets
            result["has_uvs"] = len(uv_sets) > 0 and result["uv_count"] > 0

            # Bounding box
            bbox = cmds.exactWorldBoundingBox(shape)
            result["bounding_box"] = bbox

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def mesh_vertices(
    node: str,
    offset: int = 0,
    limit: int | None = DEFAULT_VERTEX_LIMIT,
) -> dict[str, Any]:
    """Query vertex positions from a mesh with pagination.

    Returns vertex positions as [x, y, z] tuples. Use offset/limit
    pagination for large meshes to avoid token budget issues.

    Args:
        node: Name of the mesh node (transform or shape).
        offset: Starting vertex index (0-based).
        limit: Maximum number of vertices to return. Default 1000.
            Use 0 for unlimited (use with caution).

    Returns:
        Dictionary with vertex data:
            - node: The queried node name
            - exists: Whether the node exists
            - is_mesh: Whether the node is a mesh
            - vertex_count: Total number of vertices in mesh
            - vertices: List of [x, y, z] position arrays
            - offset: The offset used
            - count: Number of vertices returned
            - truncated: True if results were truncated (only if limit hit)
            - errors: Error details if any, or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If node name contains invalid characters or offset is negative.

    Example:
        >>> result = mesh_vertices("pCube1", offset=0, limit=100)
        >>> for i, v in enumerate(result['vertices']):
        ...     print(f"v{result['offset'] + i}: {v}")
    """
    _validate_node_name(node)
    if offset < 0:
        raise ValueError(f"offset must be non-negative, got {offset}")

    client = get_client()
    node_escaped = json.dumps(node)

    command = f"""
import maya.cmds as cmds
import json

node = {node_escaped}
offset = {offset}
limit = {limit}

result = {{"node": node, "exists": False, "is_mesh": False, "errors": {{}}}}

try:
    if not cmds.objExists(node):
        result["errors"]["_node"] = "Node '" + node + "' does not exist"
    else:
        result["exists"] = True

        # Get shape node if transform was passed
        shapes = cmds.listRelatives(node, shapes=True, fullPath=False) or []
        if shapes:
            shape = shapes[0]
        else:
            shape = node

        node_type = cmds.nodeType(shape)
        if node_type != "mesh":
            result["errors"]["_mesh"] = "Node is not a mesh (type: " + node_type + ")"
        else:
            result["is_mesh"] = True
            result["shape"] = shape

            # Get total vertex count
            total_count = cmds.polyEvaluate(shape, vertex=True)
            result["vertex_count"] = total_count

            # Calculate range
            start_idx = offset
            end_idx = total_count

            if limit and limit > 0:
                end_idx = min(offset + limit, total_count)

            # Get vertex positions
            vertices = []
            for i in range(start_idx, end_idx):
                pos = cmds.xform(shape + ".vtx[" + str(i) + "]", query=True, translation=True, worldSpace=True)
                vertices.append(pos)

            result["vertices"] = vertices
            result["offset"] = offset
            result["count"] = len(vertices)

            # Check truncation
            if limit and limit > 0 and total_count > offset + limit:
                result["truncated"] = True

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    # Apply response size guard
    if "vertices" in parsed:
        parsed = guard_response_size(parsed, list_key="vertices")

    return parsed


def mesh_evaluate(
    node: str,
    checks: list[Literal["non_manifold", "lamina", "holes", "border"]] | None = None,
    limit: int | None = DEFAULT_TOPOLOGY_LIMIT,
) -> dict[str, Any]:
    """Analyze mesh topology for issues.

    Performs topology analysis to find non-manifold edges, lamina faces,
    holes, and border edges. Returns lists of problematic components.

    Args:
        node: Name of the mesh node (transform or shape).
        checks: List of checks to perform. Options:
            - "non_manifold": Find non-manifold edges
            - "lamina": Find lamina faces (faces sharing all edges)
            - "holes": Find faces with holes
            - "border": Find border edges
            If None, performs all checks.
        limit: Maximum number of components to return per check. Default 500.
            Use 0 for unlimited.

    Returns:
        Dictionary with topology analysis:
            - node: The queried node name
            - exists: Whether the node exists
            - is_mesh: Whether the node is a mesh
            - non_manifold_edges: List of non-manifold edge names (if checked)
            - non_manifold_count: Count of non-manifold edges
            - lamina_faces: List of lamina face names (if checked)
            - lamina_count: Count of lamina faces
            - holes: List of faces with holes (if checked)
            - hole_count: Count of faces with holes
            - border_edges: List of border edge names (if checked)
            - border_count: Count of border edges
            - is_clean: True if mesh has no topology issues
            - errors: Error details if any, or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If node name contains invalid characters.

    Example:
        >>> result = mesh_evaluate("pCube1", checks=["non_manifold", "holes"])
        >>> if not result['is_clean']:
        ...     print(f"Found {result['non_manifold_count']} non-manifold edges")
    """
    _validate_node_name(node)

    if checks is None:
        checks = ["non_manifold", "lamina", "holes", "border"]

    valid_checks = {"non_manifold", "lamina", "holes", "border"}
    for check in checks:
        if check not in valid_checks:
            raise ValueError(
                f"Invalid check: {check!r}. Must be one of: {', '.join(sorted(valid_checks))}"
            )

    client = get_client()
    node_escaped = json.dumps(node)
    checks_escaped = json.dumps(checks)

    command = f"""
import maya.cmds as cmds
import json

node = {node_escaped}
checks = {checks_escaped}
limit = {limit}

result = {{
    "node": node,
    "exists": False,
    "is_mesh": False,
    "is_clean": True,
    "errors": {{}}
}}

try:
    if not cmds.objExists(node):
        result["errors"]["_node"] = "Node '" + node + "' does not exist"
    else:
        result["exists"] = True

        # Get shape node if transform was passed
        shapes = cmds.listRelatives(node, shapes=True, fullPath=False) or []
        if shapes:
            shape = shapes[0]
        else:
            shape = node

        node_type = cmds.nodeType(shape)
        if node_type != "mesh":
            result["errors"]["_mesh"] = "Node is not a mesh (type: " + node_type + ")"
        else:
            result["is_mesh"] = True
            result["shape"] = shape

            # Non-manifold edges
            if "non_manifold" in checks:
                try:
                    nm_edges = cmds.polyInfo(shape, nonManifoldEdges=True) or []
                    # polyInfo returns strings like "EDGE 0 1 2\\n"
                    # Parse to get edge names
                    edge_list = []
                    for line in nm_edges:
                        parts = line.split()
                        for idx in parts[1:]:
                            edge_name = shape + ".e[" + idx + "]"
                            edge_list.append(edge_name)
                            if limit and limit > 0 and len(edge_list) >= limit:
                                break
                        if limit and limit > 0 and len(edge_list) >= limit:
                            break
                    result["non_manifold_edges"] = edge_list
                    result["non_manifold_count"] = len(edge_list)
                    if len(edge_list) > 0:
                        result["is_clean"] = False
                except Exception as e:
                    result["errors"]["non_manifold"] = str(e)

            # Lamina faces
            if "lamina" in checks:
                try:
                    lam_faces = cmds.polyInfo(shape, laminaFaces=True) or []
                    face_list = []
                    for line in lam_faces:
                        parts = line.split()
                        for idx in parts[1:]:
                            face_name = shape + ".f[" + idx + "]"
                            face_list.append(face_name)
                            if limit and limit > 0 and len(face_list) >= limit:
                                break
                        if limit and limit > 0 and len(face_list) >= limit:
                            break
                    result["lamina_faces"] = face_list
                    result["lamina_count"] = len(face_list)
                    if len(face_list) > 0:
                        result["is_clean"] = False
                except Exception as e:
                    result["errors"]["lamina"] = str(e)

            # Holes (using polySelectConstraint to find faces with holes)
            if "holes" in checks:
                try:
                    # Store current selection
                    orig_sel = cmds.ls(selection=True, flatten=True) or []

                    # Select faces with holes using polySelectConstraint
                    cmds.select(shape, replace=True)
                    cmds.polySelectConstraint(mode=3, type=8, holes=1)
                    holed_faces = cmds.ls(selection=True, flatten=True) or []

                    # Reset constraint and restore selection
                    cmds.polySelectConstraint(holes=0)
                    cmds.polySelectConstraint(disable=True)
                    if orig_sel:
                        cmds.select(orig_sel, replace=True)
                    else:
                        cmds.select(clear=True)

                    # Filter to only include faces from this shape
                    face_list = []
                    for face in holed_faces:
                        if shape in face and ".f[" in face:
                            face_list.append(face)
                            if limit and limit > 0 and len(face_list) >= limit:
                                break

                    result["holes"] = face_list
                    result["hole_count"] = len(face_list)
                    if len(face_list) > 0:
                        result["is_clean"] = False
                except Exception as e:
                    result["errors"]["holes"] = str(e)

            # Border edges (using polySelectConstraint)
            if "border" in checks:
                try:
                    # Store current selection
                    orig_sel = cmds.ls(selection=True, flatten=True) or []

                    # Select border edges using polySelectConstraint
                    cmds.select(shape, replace=True)
                    cmds.polySelectConstraint(mode=3, type=0x8000, where=1)
                    border_edges = cmds.ls(selection=True, flatten=True) or []

                    # Reset constraint and restore selection
                    cmds.polySelectConstraint(where=0)
                    cmds.polySelectConstraint(disable=True)
                    if orig_sel:
                        cmds.select(orig_sel, replace=True)
                    else:
                        cmds.select(clear=True)

                    # Filter to only include edges from this shape
                    edge_list = []
                    for edge in border_edges:
                        if shape in edge and ".e[" in edge:
                            edge_list.append(edge)
                            if limit and limit > 0 and len(edge_list) >= limit:
                                break

                    result["border_edges"] = edge_list
                    result["border_count"] = len(edge_list)
                except Exception as e:
                    result["errors"]["border"] = str(e)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    # Apply response size guard for each list field
    for key in ["non_manifold_edges", "lamina_faces", "holes", "border_edges"]:
        if key in parsed:
            parsed = guard_response_size(parsed, list_key=key)

    return parsed
