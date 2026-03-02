"""Animation tools for Maya MCP.

This module provides tools for keyframing, timeline control,
and playback range management for animation workflows.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from maya_mcp.tools.scene import TIME_UNIT_TO_FPS
from maya_mcp.transport import get_client
from maya_mcp.utils.parsing import parse_json_response
from maya_mcp.utils.response_guard import guard_response_size
from maya_mcp.utils.validation import validate_attribute_name as _validate_attribute_name
from maya_mcp.utils.validation import validate_node_name as _validate_node_name

TangentType = Literal[
    "auto",
    "linear",
    "flat",
    "step",
    "stepnext",
    "spline",
    "clamped",
    "plateau",
    "fast",
    "slow",
]

VALID_TANGENT_TYPES: frozenset[str] = frozenset(TangentType.__args__)  # type: ignore[attr-defined]


def animation_set_time(
    time: float,
    update: bool = True,
) -> dict[str, Any]:
    """Set the current time (go to a specific frame).

    Args:
        time: The frame number to set as current time.
        update: Whether to update the viewport (default True).

    Returns:
        Dictionary with time result:
            - time: The time that was set
            - errors: Error details if any, or None
    """
    client = get_client()
    update_val = "True" if update else "False"

    command = f"""
import maya.cmds as cmds
import json

t = {float(time)}
update = {update_val}

result = {{"time": None, "errors": {{}}}}

try:
    result["time"] = cmds.currentTime(t, update=update)
except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def animation_get_time_range() -> dict[str, Any]:
    """Get playback range, animation range, and current time.

    Returns:
        Dictionary with time range data:
            - current_time: Current frame
            - min_time: Playback start time
            - max_time: Playback end time
            - animation_start: Animation range start
            - animation_end: Animation range end
            - fps: Current FPS setting
            - errors: Error details if any, or None
    """
    client = get_client()

    command = """
import maya.cmds as cmds
import json

result = {
    "current_time": None,
    "min_time": None,
    "max_time": None,
    "animation_start": None,
    "animation_end": None,
    "fps": None,
    "errors": {}
}

try:
    result["current_time"] = cmds.currentTime(query=True)
    result["min_time"] = cmds.playbackOptions(query=True, minTime=True)
    result["max_time"] = cmds.playbackOptions(query=True, maxTime=True)
    result["animation_start"] = cmds.playbackOptions(query=True, animationStartTime=True)
    result["animation_end"] = cmds.playbackOptions(query=True, animationEndTime=True)
    result["fps"] = cmds.currentUnit(query=True, time=True)
except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    # Resolve FPS unit string to numeric value Python-side
    if parsed.get("fps") and isinstance(parsed["fps"], str):
        parsed["fps"] = TIME_UNIT_TO_FPS.get(parsed["fps"], parsed["fps"])

    return parsed


def animation_set_time_range(
    min_time: float,
    max_time: float,
    animation_start: float | None = None,
    animation_end: float | None = None,
) -> dict[str, Any]:
    """Set the playback and animation range.

    Args:
        min_time: Playback start time.
        max_time: Playback end time.
        animation_start: Animation range start (defaults to min_time).
        animation_end: Animation range end (defaults to max_time).

    Returns:
        Dictionary with range result:
            - min_time: The playback start time that was set
            - max_time: The playback end time that was set
            - animation_start: The animation start that was set
            - animation_end: The animation end that was set
            - errors: Error details if any, or None

    Raises:
        ValueError: If min_time >= max_time, animation_start > min_time,
            or animation_end < max_time.
    """
    if min_time >= max_time:
        raise ValueError(f"min_time ({min_time}) must be less than max_time ({max_time})")

    anim_start = animation_start if animation_start is not None else min_time
    anim_end = animation_end if animation_end is not None else max_time

    if anim_start > min_time:
        raise ValueError(f"animation_start ({anim_start}) must be <= min_time ({min_time})")
    if anim_end < max_time:
        raise ValueError(f"animation_end ({anim_end}) must be >= max_time ({max_time})")

    client = get_client()

    command = f"""
import maya.cmds as cmds
import json

min_t = {float(min_time)}
max_t = {float(max_time)}
anim_start = {float(anim_start)}
anim_end = {float(anim_end)}

result = {{
    "min_time": None,
    "max_time": None,
    "animation_start": None,
    "animation_end": None,
    "errors": {{}}
}}

try:
    cmds.playbackOptions(
        minTime=min_t,
        maxTime=max_t,
        animationStartTime=anim_start,
        animationEndTime=anim_end,
    )
    result["min_time"] = cmds.playbackOptions(query=True, minTime=True)
    result["max_time"] = cmds.playbackOptions(query=True, maxTime=True)
    result["animation_start"] = cmds.playbackOptions(query=True, animationStartTime=True)
    result["animation_end"] = cmds.playbackOptions(query=True, animationEndTime=True)
except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def animation_set_keyframe(
    node: str,
    attributes: list[str] | None = None,
    time: float | None = None,
    value: float | None = None,
    in_tangent_type: TangentType = "auto",
    out_tangent_type: TangentType = "auto",
) -> dict[str, Any]:
    """Set keyframe on attribute(s) at current or specified time.

    Args:
        node: Name of the node to keyframe.
        attributes: List of attribute names to keyframe (None = all keyable).
        time: Time/frame to set the keyframe at (None = current time).
        value: Value to set (None = current value).
        in_tangent_type: In-tangent type. Options: auto, linear, flat,
            step, stepnext, spline, clamped, plateau, fast, slow.
        out_tangent_type: Out-tangent type. Same options as in_tangent_type.

    Returns:
        Dictionary with keyframe result:
            - node: The node that was keyed
            - attributes: List of attributes that were keyed
            - time: The time the keyframe was set at
            - keyframe_count: Number of keyframes set
            - errors: Error details if any, or None

    Raises:
        ValueError: If node name or attribute names contain invalid characters,
            or tangent types are invalid.
    """
    _validate_node_name(node)

    if attributes is not None:
        if not attributes:
            raise ValueError("attributes list cannot be empty")
        for attr in attributes:
            _validate_attribute_name(attr)

    if in_tangent_type not in VALID_TANGENT_TYPES:
        raise ValueError(
            f"Invalid in_tangent_type: {in_tangent_type!r}. "
            f"Must be one of: {', '.join(sorted(VALID_TANGENT_TYPES))}"
        )
    if out_tangent_type not in VALID_TANGENT_TYPES:
        raise ValueError(
            f"Invalid out_tangent_type: {out_tangent_type!r}. "
            f"Must be one of: {', '.join(sorted(VALID_TANGENT_TYPES))}"
        )

    client = get_client()
    node_escaped = json.dumps(node)
    attrs_escaped = json.dumps(attributes) if attributes is not None else "None"
    itt_escaped = json.dumps(in_tangent_type)
    ott_escaped = json.dumps(out_tangent_type)

    # Build conditional kwargs for time and value
    kwarg_lines: list[str] = []
    if time is not None:
        kwarg_lines.append(f"        kwargs['time'] = {float(time)}")
    if value is not None:
        kwarg_lines.append(f"        kwargs['value'] = {float(value)}")
    kwarg_block = "\n".join(kwarg_lines) if kwarg_lines else "        pass"

    command = f"""
import maya.cmds as cmds
import json

node = {node_escaped}
attrs = {attrs_escaped}
itt = {itt_escaped}
ott = {ott_escaped}

result = {{"node": node, "attributes": [], "time": None, "keyframe_count": 0, "errors": {{}}}}

try:
    if not cmds.objExists(node):
        result["errors"]["_node"] = "Node '" + node + "' does not exist"
    else:
        kwargs = {{"inTangentType": itt, "outTangentType": ott}}
{kwarg_block}

        if attrs is not None:
            kwargs["attribute"] = attrs
        count = cmds.setKeyframe(node, **kwargs)
        count = count if count else 0

        keyed_attrs = attrs if attrs is not None else (cmds.listAttr(node, keyable=True) or [])

        result["attributes"] = keyed_attrs
        result["keyframe_count"] = count
        result["time"] = cmds.currentTime(query=True)
except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def _build_time_range_code(
    time_range_start: float | None,
    time_range_end: float | None,
) -> str:
    """Build Maya-side time_range assignment code.

    Returns a Python code line that assigns a time_range variable
    for use with cmds.keyframe/cmds.cutKey time= parameter.

    Args:
        time_range_start: Start of range, or None.
        time_range_end: End of range, or None.

    Returns:
        A string of Python code to embed in the Maya command.
    """
    if time_range_start is not None and time_range_end is not None:
        return f"time_range = ({float(time_range_start)}, {float(time_range_end)})"
    return "time_range = None"


def animation_get_keyframes(
    node: str,
    attributes: list[str] | None = None,
    time_range_start: float | None = None,
    time_range_end: float | None = None,
) -> dict[str, Any]:
    """Query keyframes for attribute(s) on a node within optional time range.

    Args:
        node: Name of the node to query.
        attributes: List of attribute names to query (None = all animated).
        time_range_start: Start of time range to query (None = all time).
        time_range_end: End of time range to query (None = all time).

    Returns:
        Dictionary with keyframe data:
            - node: The queried node name
            - keyframes: Dict mapping attribute names to lists of
              {time, value} entries
            - attribute_count: Number of attributes with keyframes
            - total_keyframe_count: Total number of keyframes found
            - errors: Error details if any, or None

    Raises:
        ValueError: If node name or attribute names contain invalid characters.
    """
    _validate_node_name(node)

    if attributes is not None:
        if not attributes:
            raise ValueError("attributes list cannot be empty")
        for attr in attributes:
            _validate_attribute_name(attr)

    client = get_client()
    node_escaped = json.dumps(node)
    attrs_escaped = json.dumps(attributes) if attributes is not None else "None"
    time_range_init = _build_time_range_code(time_range_start, time_range_end)

    command = f"""
import maya.cmds as cmds
import json

node = {node_escaped}
attrs = {attrs_escaped}
{time_range_init}

result = {{
    "node": node,
    "keyframes": {{}},
    "attribute_count": 0,
    "total_keyframe_count": 0,
    "errors": {{}}
}}

try:
    if not cmds.objExists(node):
        result["errors"]["_node"] = "Node '" + node + "' does not exist"
    else:
        # Determine which attributes to query
        if attrs is not None:
            query_attrs = attrs
        else:
            # Find all animated attributes via anim curve connections
            anim_curves = cmds.keyframe(node, query=True, name=True) or []
            query_attrs = []
            seen = set()
            for curve in anim_curves:
                conns = cmds.listConnections(curve + ".output", plugs=True) or []
                for conn in conns:
                    parts = conn.split(".")
                    if len(parts) >= 2 and parts[0] == node:
                        attr = ".".join(parts[1:])
                        if attr not in seen:
                            seen.add(attr)
                            query_attrs.append(attr)

        keyframes = {{}}
        total_count = 0

        for attr in query_attrs:
            kw = {{"query": True, "attribute": attr}}
            if time_range is not None:
                kw["time"] = time_range

            times = cmds.keyframe(node, timeChange=True, **kw) or []
            values = cmds.keyframe(node, valueChange=True, **kw) or []

            if times:
                entries = []
                for t, v in zip(times, values):
                    entries.append({{"time": t, "value": v}})
                keyframes[attr] = entries
                total_count += len(entries)

        result["keyframes"] = keyframes
        result["attribute_count"] = len(keyframes)
        result["total_keyframe_count"] = total_count

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    # Guard against oversized keyframe data by flattening to a list
    if "keyframes" in parsed and isinstance(parsed["keyframes"], dict):
        flat_keyframes: list[dict[str, Any]] = []
        for attr_name, entries in parsed["keyframes"].items():
            if isinstance(entries, list):
                for entry in entries:
                    flat_keyframes.append({"attribute": attr_name, **entry})
        if flat_keyframes:
            guard_data: dict[str, Any] = {
                **parsed,
                "_flat_keyframes": flat_keyframes,
            }
            guarded = guard_response_size(guard_data, list_key="_flat_keyframes")
            if "_size_warning" in guarded:
                parsed["_size_warning"] = guarded["_size_warning"]
                parsed["_original_size"] = guarded.get("_original_size")
                # Rebuild keyframes dict from truncated flat list
                truncated: dict[str, list[dict[str, Any]]] = {}
                for entry in guarded["_flat_keyframes"]:
                    a = entry.pop("attribute")
                    truncated.setdefault(a, []).append(entry)
                parsed["keyframes"] = truncated
                parsed["attribute_count"] = len(truncated)
                parsed["total_keyframe_count"] = sum(len(v) for v in truncated.values())
                parsed["truncated"] = True

    return parsed


def animation_delete_keyframes(
    node: str,
    attributes: list[str] | None = None,
    time_range_start: float | None = None,
    time_range_end: float | None = None,
) -> dict[str, Any]:
    """Delete keyframes in a time range for attribute(s).

    Args:
        node: Name of the node to delete keyframes from.
        attributes: List of attribute names (None = all animated attributes).
        time_range_start: Start of time range (None = all time).
        time_range_end: End of time range (None = all time).

    Returns:
        Dictionary with delete result:
            - node: The node that was modified
            - deleted_count: Number of keyframes deleted
            - attributes: Attributes that were affected
            - time_range: The time range used (or "all")
            - errors: Error details if any, or None

    Raises:
        ValueError: If node name or attribute names contain invalid characters.
    """
    _validate_node_name(node)

    if attributes is not None:
        if not attributes:
            raise ValueError("attributes list cannot be empty")
        for attr in attributes:
            _validate_attribute_name(attr)

    client = get_client()
    node_escaped = json.dumps(node)
    attrs_escaped = json.dumps(attributes) if attributes is not None else "None"
    time_range_code = _build_time_range_code(time_range_start, time_range_end)

    command = f"""
import maya.cmds as cmds
import json

node = {node_escaped}
attrs = {attrs_escaped}
{time_range_code}

result = {{
    "node": node,
    "deleted_count": 0,
    "attributes": [],
    "time_range": "all",
    "errors": {{}}
}}

try:
    if not cmds.objExists(node):
        result["errors"]["_node"] = "Node '" + node + "' does not exist"
    else:
        # Determine which attributes to process
        if attrs is not None:
            target_attrs = attrs
        else:
            # Find all animated attributes via anim curve connections
            anim_curves = cmds.keyframe(node, query=True, name=True) or []
            target_attrs = []
            seen = set()
            for curve in anim_curves:
                conns = cmds.listConnections(curve + ".output", plugs=True) or []
                for conn in conns:
                    parts = conn.split(".")
                    if len(parts) >= 2 and parts[0] == node:
                        attr = ".".join(parts[1:])
                        if attr not in seen:
                            seen.add(attr)
                            target_attrs.append(attr)

        total_deleted = 0
        affected_attrs = []

        for attr in target_attrs:
            # Count keyframes before deleting (cutKey return value unreliable)
            count_kw = {{"query": True, "keyframeCount": True, "attribute": attr}}
            if time_range is not None:
                count_kw["time"] = time_range
            pre_count = cmds.keyframe(node, **count_kw) or 0

            cut_kw = {{"attribute": attr, "clear": True}}
            if time_range is not None:
                cut_kw["time"] = time_range
            cmds.cutKey(node, **cut_kw)

            if pre_count > 0:
                total_deleted += pre_count
                affected_attrs.append(attr)

        result["deleted_count"] = total_deleted
        result["attributes"] = affected_attrs
        if time_range is not None:
            result["time_range"] = list(time_range)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed
