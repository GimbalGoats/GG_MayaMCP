"""Registrar for attribute tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from mcp.types import ToolAnnotations

from maya_mcp.tools.attributes import (
    AttributesGetOutput,
    AttributesSetOutput,
    attributes_get,
    attributes_set,
)
from maya_mcp.utils.coercion import coerce_dict, coerce_list

if TYPE_CHECKING:
    from fastmcp import FastMCP


def tool_attributes_get(
    node: Annotated[str, "Node name to query"],
    attributes: Annotated[list[str], "Attribute names to get (e.g., ['translateX', 'visibility'])"],
) -> AttributesGetOutput:
    """Get attribute values from a Maya node.

    Args:
        node: Node name to query.
        attributes: List of attribute names to retrieve.

    Returns:
        Dictionary with node, attributes (name-to-value map), count,
        and errors (if any attributes failed).
    """
    return attributes_get(node=node, attributes=coerce_list(attributes))


def tool_attributes_set(
    node: Annotated[str, "Node name to modify"],
    attributes: Annotated[dict[str, Any], "Map of attribute name to value"],
) -> AttributesSetOutput:
    """Set attribute values on a Maya node.

    Args:
        node: Node name to modify.
        attributes: Dictionary mapping attribute names to values.

    Returns:
        Dictionary with node, set (list of attrs set), count,
        and errors (if any attributes failed).
    """
    return attributes_set(node=node, attributes=coerce_dict(attributes))


def register_attribute_tools(mcp: FastMCP) -> None:
    """Register attribute tools."""
    mcp.tool(
        name="attributes.get",
        description="Get one or more attribute values from a Maya node. "
        "Supports batch queries to reduce tool call chaining.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_attributes_get)

    mcp.tool(
        name="attributes.set",
        description="Set one or more attribute values on a Maya node. "
        "Supports batch operations to reduce tool call chaining.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_attributes_set)
