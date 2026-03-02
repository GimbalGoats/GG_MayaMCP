"""Curve tools for Maya MCP.

This module provides tools for querying NURBS curve geometry.
"""

from __future__ import annotations

import json
from typing import Any

from maya_mcp.transport import get_client
from maya_mcp.utils.parsing import parse_json_response
from maya_mcp.utils.response_guard import guard_response_size
from maya_mcp.utils.validation import validate_node_name as _validate_node_name

DEFAULT_CV_LIMIT = 1000


def curve_info(node: str) -> dict[str, Any]:
    """Get information about a NURBS curve.

    Returns degree, spans, form, CV count, knots, length, and bounding box.

    Args:
        node: Name of the curve node (transform or shape).

    Returns:
        Dictionary with curve information:
            - node: The queried node name
            - exists: Whether the node exists
            - is_curve: Whether the node is a nurbsCurve
            - degree: Curve degree
            - spans: Number of spans
            - form: Curve form (open, closed, periodic)
            - cv_count: Number of CVs
            - knots: List of knot values
            - length: Arc length of the curve
            - bounding_box: [min_x, min_y, min_z, max_x, max_y, max_z]
            - errors: Error details if any, or None

    Raises:
        ValueError: If node name contains invalid characters.
    """
    _validate_node_name(node)

    client = get_client()
    node_escaped = json.dumps(node)

    command = f"""
import maya.cmds as cmds
import json

node = {node_escaped}
result = {{"node": node, "exists": False, "is_curve": False, "errors": {{}}}}

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
        if node_type != "nurbsCurve":
            result["errors"]["_curve"] = "Node is not a nurbsCurve (type: " + node_type + ")"
        else:
            result["is_curve"] = True
            result["shape"] = shape

            # Query curve info
            result["degree"] = cmds.getAttr(shape + ".degree")
            result["spans"] = cmds.getAttr(shape + ".spans")

            form_val = cmds.getAttr(shape + ".form")
            form_map = {{0: "open", 1: "closed", 2: "periodic"}}
            result["form"] = form_map.get(form_val, "unknown")

            # CV count
            cvs = cmds.ls(shape + ".cv[*]", flatten=True)
            result["cv_count"] = len(cvs)

            # Knots
            knots = cmds.getAttr(shape + ".knots[*]") or []
            result["knots"] = list(knots)

            # Arc length
            result["length"] = cmds.arclen(shape)

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


def curve_cvs(
    node: str,
    offset: int = 0,
    limit: int | None = DEFAULT_CV_LIMIT,
) -> dict[str, Any]:
    """Query CV positions from a NURBS curve with pagination.

    Returns CV positions as [x, y, z] arrays in world space.

    Args:
        node: Name of the curve node (transform or shape).
        offset: Starting CV index (0-based).
        limit: Maximum number of CVs to return. Default 1000.
            Use 0 for unlimited.

    Returns:
        Dictionary with CV data:
            - node: The queried node name
            - exists: Whether the node exists
            - is_curve: Whether the node is a nurbsCurve
            - cv_count: Total number of CVs
            - cvs: List of [x, y, z] position arrays
            - offset: The offset used
            - count: Number of CVs returned
            - truncated: True if more CVs remain
            - errors: Error details if any, or None

    Raises:
        ValueError: If node name contains invalid characters or offset is negative.
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

result = {{"node": node, "exists": False, "is_curve": False, "errors": {{}}}}

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
        if node_type != "nurbsCurve":
            result["errors"]["_curve"] = "Node is not a nurbsCurve (type: " + node_type + ")"
        else:
            result["is_curve"] = True
            result["shape"] = shape

            # Get total CV count
            all_cvs = cmds.ls(shape + ".cv[*]", flatten=True)
            total_count = len(all_cvs)
            result["cv_count"] = total_count

            # Calculate range
            start_idx = offset
            end_idx = total_count
            if limit and limit > 0:
                end_idx = min(offset + limit, total_count)

            # Get CV positions in world space
            cvs = []
            for i in range(start_idx, end_idx):
                pos = cmds.pointPosition(shape + ".cv[" + str(i) + "]", world=True)
                cvs.append([pos[0], pos[1], pos[2]])

            result["cvs"] = cvs
            result["offset"] = offset
            result["count"] = len(cvs)

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

    if "cvs" in parsed:
        parsed = guard_response_size(parsed, list_key="cvs")

    return parsed
