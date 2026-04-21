"""Registrar for selection tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal

from mcp.types import ToolAnnotations

from maya_mcp.tools.selection import (
    SelectionComponentsOutput,
    SelectionConvertComponentsOutput,
    SelectionOutput,
    SelectionWithErrorsOutput,
    selection_clear,
    selection_convert_components,
    selection_get,
    selection_get_components,
    selection_set,
    selection_set_components,
)
from maya_mcp.utils.coercion import coerce_list

if TYPE_CHECKING:
    from fastmcp import FastMCP


def tool_selection_get() -> SelectionOutput:
    """Get current Maya selection.

    Returns:
        Selection list with selection array and count.
    """
    return selection_get()


def tool_selection_set(
    nodes: Annotated[list[str], "Node names to select"],
    add: Annotated[bool, "Add to existing selection"] = False,
    deselect: Annotated[bool, "Remove from selection"] = False,
) -> SelectionOutput:
    """Set Maya selection.

    Args:
        nodes: List of node names to operate on.
        add: Add to existing selection instead of replacing.
        deselect: Remove from selection instead of adding.

    Returns:
        New selection state with selection array and count.
    """
    return selection_set(nodes=coerce_list(nodes), add=add, deselect=deselect)


def tool_selection_clear() -> SelectionOutput:
    """Clear Maya selection.

    Deselects all currently selected nodes.

    Returns:
        Empty selection state with selection array and count of 0.
    """
    return selection_clear()


def tool_selection_set_components(
    components: Annotated[
        list[str],
        "Component specifications (e.g., ['pCube1.vtx[0:7]', 'pCube1.f[0]'])",
    ],
    add: Annotated[bool, "Add to existing selection"] = False,
    deselect: Annotated[bool, "Remove from selection"] = False,
) -> SelectionWithErrorsOutput:
    """Select mesh components.

    Args:
        components: List of component specifications in Maya notation.
        add: Add to existing selection.
        deselect: Remove from selection.

    Returns:
        Dictionary with selection list, count, and errors.
    """
    return selection_set_components(
        components=coerce_list(components),
        add=add,
        deselect=deselect,
    )


def tool_selection_get_components() -> SelectionComponentsOutput:
    """Get selected mesh components.

    Returns:
        Dictionary with selection, vertices, edges, faces lists and counts.
    """
    return selection_get_components()


def tool_selection_convert_components(
    to_type: Annotated[
        Literal["vertex", "edge", "face"],
        "Target component type",
    ],
    nodes: Annotated[
        list[str] | None,
        "Nodes to convert (None = use current selection)",
    ] = None,
) -> SelectionConvertComponentsOutput:
    """Convert selection to different component type.

    Args:
        to_type: Target component type (vertex, edge, face).
        nodes: Optional nodes to convert. If None, uses current selection.

    Returns:
        Dictionary with converted selection list and count.
    """
    return selection_convert_components(to_type=to_type, nodes=coerce_list(nodes))


def register_selection_tools(mcp: FastMCP) -> None:
    """Register object and component selection tools."""
    mcp.tool(
        name="selection.get",
        description="Get the current selection in Maya",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_selection_get)

    mcp.tool(
        name="selection.set",
        description="Set the Maya selection",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_selection_set)

    mcp.tool(
        name="selection.clear",
        description="Clear the Maya selection (deselect all)",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_selection_clear)

    mcp.tool(
        name="selection.set_components",
        description="Select mesh components (vertices, edges, or faces) using Maya notation "
        "(e.g., 'pCube1.vtx[0:10]', 'pSphere1.e[5]', 'pPlane1.f[0:99]').",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_selection_set_components)

    mcp.tool(
        name="selection.get_components",
        description="Get currently selected mesh components grouped by type (vertices, edges, faces).",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_selection_get_components)

    mcp.tool(
        name="selection.convert_components",
        description="Convert the current selection to a different component type "
        "(vertex, edge, or face).",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_selection_convert_components)
