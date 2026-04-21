"""Registrar for dependency graph connection tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal

from mcp.types import ToolAnnotations

from maya_mcp.tools.connections import (
    ConnectionsConnectOutput,
    ConnectionsDisconnectOutput,
    ConnectionsGetOutput,
    ConnectionsHistoryOutput,
    ConnectionsListOutput,
    connections_connect,
    connections_disconnect,
    connections_get,
    connections_history,
    connections_list,
)
from maya_mcp.utils.coercion import coerce_list

if TYPE_CHECKING:
    from fastmcp import FastMCP


def tool_connections_list(
    node: Annotated[str, "Node name to query connections for"],
    direction: Annotated[
        Literal["incoming", "outgoing", "both"],
        "Filter by direction: incoming, outgoing, or both",
    ] = "both",
    connections_type: Annotated[
        str | None,
        "Filter by connection type (e.g., 'animCurve', 'shader')",
    ] = None,
    limit: Annotated[
        int | None,
        "Max connections to return (default 500, use 0 for unlimited)",
    ] = 500,
) -> ConnectionsListOutput:
    """List connections on a Maya node.

    Args:
        node: Node name to query.
        direction: Filter by connection direction.
        connections_type: Filter by connection type.
        limit: Max connections to return.

    Returns:
        Dictionary with connections list, count, and truncation info.
    """
    return connections_list(
        node=node,
        direction=direction,
        connections_type=connections_type,
        limit=limit,
    )


def tool_connections_get(
    node: Annotated[str, "Node name to query"],
    attributes: Annotated[
        list[str] | None,
        "Attribute names to check for connections (None = all connectable attrs)",
    ] = None,
) -> ConnectionsGetOutput:
    """Get connection details for specific attributes.

    Args:
        node: Node name to query.
        attributes: List of attribute names to check, or None for all.

    Returns:
        Dictionary with attribute connection details.
    """
    return connections_get(node=node, attributes=coerce_list(attributes))


def tool_connections_connect(
    source: Annotated[str, "Source plug in 'node.attribute' format"],
    destination: Annotated[str, "Destination plug in 'node.attribute' format"],
    force: Annotated[
        bool,
        "If True, disconnect existing connections to destination first",
    ] = False,
) -> ConnectionsConnectOutput:
    """Connect two attributes.

    Args:
        source: Source plug (node.attribute).
        destination: Destination plug (node.attribute).
        force: Disconnect existing connections first.

    Returns:
        Dictionary with connection result and any disconnected plugs.
    """
    return connections_connect(source=source, destination=destination, force=force)


def tool_connections_disconnect(
    source: Annotated[
        str | None,
        "Source plug to disconnect from (None = use destination only)",
    ] = None,
    destination: Annotated[
        str | None,
        "Destination plug to disconnect from (None = use source only)",
    ] = None,
) -> ConnectionsDisconnectOutput:
    """Disconnect attributes.

    Args:
        source: Source plug (optional).
        destination: Destination plug (optional).

    Returns:
        Dictionary with disconnected connections list.
    """
    return connections_disconnect(source=source, destination=destination)


def tool_connections_history(
    node: Annotated[str, "Node name to query history for"],
    direction: Annotated[
        Literal["input", "output", "both"],
        "Direction to traverse: input (upstream), output (downstream), or both",
    ] = "input",
    depth: Annotated[int, "Maximum depth to traverse (default 10, max 50)"] = 10,
    limit: Annotated[
        int | None,
        "Max history nodes to return (default 500)",
    ] = 500,
) -> ConnectionsHistoryOutput:
    """List construction/deformation history.

    Args:
        node: Node name to query.
        direction: Direction to traverse.
        depth: Maximum traversal depth.
        limit: Max history nodes to return.

    Returns:
        Dictionary with history nodes list.
    """
    return connections_history(node=node, direction=direction, depth=depth, limit=limit)


def register_connections_tools(mcp: FastMCP) -> None:
    """Register dependency graph connection tools."""
    mcp.tool(
        name="connections.list",
        description="List connections on a Maya node with direction and type filters. "
        "Returns max 500 connections by default to limit response size.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_connections_list)

    mcp.tool(
        name="connections.get",
        description="Get detailed connection information for specific attributes on a node.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_connections_get)

    mcp.tool(
        name="connections.connect",
        description="Connect two attributes in Maya. "
        "Use force=True to disconnect existing connections first.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_connections_connect)

    mcp.tool(
        name="connections.disconnect",
        description="Disconnect attributes in Maya. "
        "Can disconnect a specific connection, all outgoing from a source, "
        "or all incoming to a destination.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_connections_disconnect)

    mcp.tool(
        name="connections.history",
        description="List construction/deformation history on a node. "
        "Traverses upstream (input) or downstream (output) dependency graph.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_connections_history)
