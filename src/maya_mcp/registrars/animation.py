"""Registrar for animation tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from mcp.types import ToolAnnotations

from maya_mcp.tools.animation import (
    AnimationDeleteKeyframesOutput,
    AnimationGetKeyframesOutput,
    AnimationGetTimeRangeOutput,
    AnimationSetKeyframeOutput,
    AnimationSetTimeOutput,
    AnimationSetTimeRangeOutput,
    TangentType,
    animation_delete_keyframes,
    animation_get_keyframes,
    animation_get_time_range,
    animation_set_keyframe,
    animation_set_time,
    animation_set_time_range,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP


def tool_animation_set_time(
    time: Annotated[float, "The frame number to set as current time"],
    update: Annotated[bool, "Whether to update the viewport (default True)"] = True,
) -> AnimationSetTimeOutput:
    """Set the current time.

    Args:
        time: The frame number to navigate to.
        update: Whether to update the viewport.

    Returns:
        Dictionary with time and errors.
    """
    return animation_set_time(time=time, update=update)


def tool_animation_get_time_range() -> AnimationGetTimeRangeOutput:
    """Get playback range, animation range, and current time.

    Returns:
        Dictionary with current_time, min_time, max_time,
        animation_start, animation_end, fps, and errors.
    """
    return animation_get_time_range()


def tool_animation_set_time_range(
    min_time: Annotated[float, "Playback start time"],
    max_time: Annotated[float, "Playback end time"],
    animation_start: Annotated[
        float | None,
        "Animation range start (defaults to min_time)",
    ] = None,
    animation_end: Annotated[
        float | None,
        "Animation range end (defaults to max_time)",
    ] = None,
) -> AnimationSetTimeRangeOutput:
    """Set the playback and animation range.

    Args:
        min_time: Playback start time.
        max_time: Playback end time.
        animation_start: Animation range start.
        animation_end: Animation range end.

    Returns:
        Dictionary with min_time, max_time, animation_start,
        animation_end, and errors.
    """
    return animation_set_time_range(
        min_time=min_time,
        max_time=max_time,
        animation_start=animation_start,
        animation_end=animation_end,
    )


def tool_animation_set_keyframe(
    node: Annotated[str, "Name of the node to keyframe"],
    attributes: Annotated[
        list[str] | None,
        "Attribute names to keyframe (None = all keyable)",
    ] = None,
    time: Annotated[
        float | None,
        "Time/frame to set keyframe at (None = current time)",
    ] = None,
    value: Annotated[
        float | None,
        "Value to set (None = current value)",
    ] = None,
    in_tangent_type: Annotated[
        TangentType,
        "In-tangent type: auto, linear, flat, step, stepnext, spline, clamped, plateau, fast, slow",
    ] = "auto",
    out_tangent_type: Annotated[
        TangentType,
        "Out-tangent type: auto, linear, flat, step, stepnext, spline, clamped, plateau, fast, slow",
    ] = "auto",
) -> AnimationSetKeyframeOutput:
    """Set keyframe on attribute(s).

    Args:
        node: Name of the node to keyframe.
        attributes: Attribute names to keyframe.
        time: Time to set keyframe at.
        value: Value to set.
        in_tangent_type: In-tangent type.
        out_tangent_type: Out-tangent type.

    Returns:
        Dictionary with node, attributes, time, keyframe_count, and errors.
    """
    return animation_set_keyframe(
        node=node,
        attributes=attributes,
        time=time,
        value=value,
        in_tangent_type=in_tangent_type,
        out_tangent_type=out_tangent_type,
    )


def tool_animation_get_keyframes(
    node: Annotated[str, "Name of the node to query"],
    attributes: Annotated[
        list[str] | None,
        "Attribute names to query (None = all animated attributes)",
    ] = None,
    time_range_start: Annotated[
        float | None,
        "Start of time range to query (None = all time)",
    ] = None,
    time_range_end: Annotated[
        float | None,
        "End of time range to query (None = all time)",
    ] = None,
) -> AnimationGetKeyframesOutput:
    """Query keyframes for attribute(s).

    Args:
        node: Name of the node to query.
        attributes: Attribute names to query.
        time_range_start: Start of time range.
        time_range_end: End of time range.

    Returns:
        Dictionary with node, keyframes, attribute_count,
        total_keyframe_count, and errors.
    """
    return animation_get_keyframes(
        node=node,
        attributes=attributes,
        time_range_start=time_range_start,
        time_range_end=time_range_end,
    )


def tool_animation_delete_keyframes(
    node: Annotated[str, "Name of the node to delete keyframes from"],
    attributes: Annotated[
        list[str] | None,
        "Attribute names (None = all animated attributes)",
    ] = None,
    time_range_start: Annotated[
        float | None,
        "Start of time range (None = all time)",
    ] = None,
    time_range_end: Annotated[
        float | None,
        "End of time range (None = all time)",
    ] = None,
) -> AnimationDeleteKeyframesOutput:
    """Delete keyframes in a time range.

    Args:
        node: Name of the node.
        attributes: Attribute names.
        time_range_start: Start of time range.
        time_range_end: End of time range.

    Returns:
        Dictionary with node, deleted_count, attributes, time_range, and errors.
    """
    return animation_delete_keyframes(
        node=node,
        attributes=attributes,
        time_range_start=time_range_start,
        time_range_end=time_range_end,
    )


def register_animation_tools(mcp: FastMCP) -> None:
    """Register animation tools."""
    mcp.tool(
        name="animation.set_time",
        description="Set the current time (go to a specific frame).",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_animation_set_time)

    mcp.tool(
        name="animation.get_time_range",
        description="Get playback range, animation range, and current time.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_animation_get_time_range)

    mcp.tool(
        name="animation.set_time_range",
        description="Set the playback and animation range.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_animation_set_time_range)

    mcp.tool(
        name="animation.set_keyframe",
        description="Set keyframe on attribute(s) at current or specified time.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_animation_set_keyframe)

    mcp.tool(
        name="animation.get_keyframes",
        description="Query keyframes for attribute(s) on a node within optional time range.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_animation_get_keyframes)

    mcp.tool(
        name="animation.delete_keyframes",
        description="Delete keyframes in a time range for attribute(s).",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_animation_delete_keyframes)
