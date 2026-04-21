"""Registrar for curve tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from mcp.types import ToolAnnotations

from maya_mcp.tools.curve import CurveCvsOutput, CurveInfoOutput  # noqa: TC001

if TYPE_CHECKING:
    from fastmcp import FastMCP


def tool_curve_info(
    node: Annotated[str, "Name of the curve node (transform or shape)"],
) -> CurveInfoOutput:
    """Get NURBS curve information.

    Args:
        node: Name of the curve node (transform or shape).

    Returns:
        Dictionary with degree, spans, form, cv_count, knots, length,
        bounding_box, and errors.
    """
    from maya_mcp.tools.curve import curve_info as _curve_info

    return _curve_info(node=node)


def tool_curve_cvs(
    node: Annotated[str, "Name of the curve node (transform or shape)"],
    offset: Annotated[int, "Starting CV index (0-based)"] = 0,
    limit: Annotated[
        int | None,
        "Maximum CVs to return (default 1000, use 0 for unlimited)",
    ] = 1000,
) -> CurveCvsOutput:
    """Query CV positions from a NURBS curve.

    Args:
        node: Name of the curve node.
        offset: Starting CV index.
        limit: Maximum CVs to return.

    Returns:
        Dictionary with cvs list, cv_count, offset, count, and errors.
    """
    from maya_mcp.tools.curve import curve_cvs as _curve_cvs

    return _curve_cvs(node=node, offset=offset, limit=limit)


def register_curve_tools(mcp: FastMCP) -> None:
    """Register curve tools."""
    mcp.tool(
        name="curve.info",
        description="Get NURBS curve information: degree, spans, form, CV count, knots, length, bounding box.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_curve_info)

    mcp.tool(
        name="curve.cvs",
        description="Query CV positions from a NURBS curve with offset/limit pagination. "
        "Returns CV positions as [x, y, z] arrays in world space.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_curve_cvs)
