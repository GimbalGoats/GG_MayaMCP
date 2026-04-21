"""Curve tools for Maya MCP.

This module provides tools for querying NURBS curve geometry.
"""

from __future__ import annotations

import json
from typing import Any, Literal, cast

from typing_extensions import NotRequired, TypedDict

from maya_mcp.transport import get_client
from maya_mcp.utils.parsing import parse_json_response
from maya_mcp.utils.response_guard import guard_response_size
from maya_mcp.utils.validation import validate_node_name as _validate_node_name

DEFAULT_CV_LIMIT = 1000


class _GuardedOutput(TypedDict, total=False):
    """Metadata added when response size guards truncate a payload."""

    truncated: bool
    total_count: int
    _size_warning: str
    _original_size: int
    _truncated_size: int


class CurveInfoOutput(TypedDict):
    """Return payload for the curve.info tool."""

    node: str
    exists: bool
    is_curve: bool
    errors: dict[str, Any] | None
    shape: NotRequired[str]
    degree: NotRequired[int]
    spans: NotRequired[int]
    form: NotRequired[Literal["open", "closed", "periodic", "unknown"]]
    cv_count: NotRequired[int]
    knots: NotRequired[list[float]]
    length: NotRequired[float]
    bounding_box: NotRequired[list[float]]


class CurveCvsOutput(_GuardedOutput):
    """Return payload for the curve.cvs tool."""

    node: str
    exists: bool
    is_curve: bool
    errors: dict[str, Any] | None
    shape: NotRequired[str]
    cv_count: NotRequired[int]
    cvs: NotRequired[list[list[float]]]
    offset: NotRequired[int]
    count: NotRequired[int]


def curve_info(node: str) -> CurveInfoOutput:
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
from maya.api import OpenMaya as om2
node = {node_escaped}
result = {{"node": node, "exists": False, "is_curve": False, "errors": {{}}}}
try:
    if not cmds.objExists(node):
        result["errors"]["_node"] = "Node '" + node + "' does not exist"
    else:
        result["exists"] = True
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
            result["degree"] = cmds.getAttr(shape + ".degree")
            result["spans"] = cmds.getAttr(shape + ".spans")
            form_val = cmds.getAttr(shape + ".form")
            form_map = {{0: "open", 1: "closed", 2: "periodic"}}
            result["form"] = form_map.get(form_val, "unknown")
            cvs = cmds.ls(shape + ".cv[*]", flatten=True)
            result["cv_count"] = len(cvs)
            sel = om2.MSelectionList()
            sel.add(shape)
            fn_curve = om2.MFnNurbsCurve(sel.getDagPath(0))
            result["knots"] = [float(k) for k in fn_curve.knots()]
            result["length"] = fn_curve.length()
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

    return cast("CurveInfoOutput", parsed)


def curve_cvs(
    node: str,
    offset: int = 0,
    limit: int | None = DEFAULT_CV_LIMIT,
) -> CurveCvsOutput:
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

    # Maya's commandPort has scoping issues with deeply nested f-string
    # templates (variables become undefined mid-execution). Building the
    # code as an explicit string and running it via exec() with a clean
    # namespace avoids this. curve_info doesn't need this because its
    # command is shorter and doesn't hit the problematic threshold.
    inner_code = (
        "import maya.cmds as cmds\n"
        "import json\n"
        f"node = {node_escaped}\n"
        f"offset = {offset}\n"
        f"limit = {limit}\n"
        'result = {"node": node, "exists": False, "is_curve": False, "errors": {}}\n'
        "try:\n"
        "    if not cmds.objExists(node):\n"
        """        result["errors"]["_node"] = "Node '" + node + "' does not exist"\n"""
        "    else:\n"
        '        result["exists"] = True\n'
        "        shapes = cmds.listRelatives(node, shapes=True, fullPath=False) or []\n"
        "        shape = shapes[0] if shapes else node\n"
        "        node_type = cmds.nodeType(shape)\n"
        '        if node_type != "nurbsCurve":\n'
        '            result["errors"]["_curve"] = '
        '"Node is not a nurbsCurve (type: " + node_type + ")"\n'
        "        else:\n"
        '            result["is_curve"] = True\n'
        '            result["shape"] = shape\n'
        '            all_cvs = cmds.ls(shape + ".cv[*]", flatten=True)\n'
        "            total_count = len(all_cvs)\n"
        '            result["cv_count"] = total_count\n'
        "            end_idx = min(offset + limit, total_count) "
        "if limit and limit > 0 else total_count\n"
        '            cv_range = shape + ".cv[" + str(offset) '
        '+ ":" + str(end_idx - 1) + "]"\n'
        "            pos_data = cmds.xform(cv_range, query=True, "
        "worldSpace=True, translation=True) or []\n"
        "            cvs = [[pos_data[i], pos_data[i+1], pos_data[i+2]] "
        "for i in range(0, len(pos_data), 3)]\n"
        '            result["cvs"] = cvs\n'
        '            result["offset"] = offset\n'
        '            result["count"] = len(cvs)\n'
        "            if limit and limit > 0 and total_count > offset + limit:\n"
        '                result["truncated"] = True\n'
        "except Exception as e:\n"
        '    result["errors"]["_exception"] = str(e)\n'
        "print(json.dumps(result))\n"
    )
    code_escaped = json.dumps(inner_code)
    command = f'_c = {code_escaped}\nexec(_c, {{"__name__": "__main__"}})\n'

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    if "cvs" in parsed:
        parsed = guard_response_size(parsed, list_key="cvs")

    return cast("CurveCvsOutput", parsed)
