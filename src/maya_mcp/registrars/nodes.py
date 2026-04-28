"""Registrar for node tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Literal

from mcp.types import ToolAnnotations

from maya_mcp.tools.nodes import (
    NodesCreateOutput,
    NodesDeleteOutput,
    NodesDuplicateOutput,
    NodesInfoOutput,
    NodesListOutput,
    NodesParentOutput,
    NodesRenameOutput,
    nodes_create,
    nodes_delete,
    nodes_duplicate,
    nodes_info,
    nodes_list,
    nodes_parent,
    nodes_rename,
)
from maya_mcp.utils.coercion import coerce_dict, coerce_list

if TYPE_CHECKING:
    from fastmcp import FastMCP


def tool_nodes_list(
    node_type: Annotated[
        str | None,
        "Filter by node type (e.g., 'transform', 'mesh')",
    ] = None,
    pattern: Annotated[str, "Name pattern filter (supports wildcards)"] = "*",
    long_names: Annotated[bool, "Return full DAG paths"] = False,
    limit: Annotated[
        int | None,
        "Max nodes to return (default 500, use 0 for unlimited)",
    ] = 500,
) -> NodesListOutput:
    """List Maya nodes.

    Args:
        node_type: Filter by node type (optional).
        pattern: Name pattern with wildcards.
        long_names: Return full DAG paths if True.
        limit: Max nodes to return. Default 500. Set to 0 for unlimited.

    Returns:
        Node list with nodes array, count. If truncated, includes
        'truncated' (True) and 'total_count' fields.
    """
    return nodes_list(node_type=node_type, pattern=pattern, long_names=long_names, limit=limit)


def tool_nodes_create(
    node_type: Annotated[str, "Type of node to create (e.g., 'transform', 'locator', 'joint')"],
    name: Annotated[str | None, "Desired node name (Maya may modify for uniqueness)"] = None,
    parent: Annotated[str | None, "Parent node to parent under"] = None,
    attributes: Annotated[
        dict[str, Any] | None,
        "Initial attribute values to set after creation",
    ] = None,
) -> NodesCreateOutput:
    """Create a new Maya node.

    Args:
        node_type: Type of node to create.
        name: Desired node name (optional).
        parent: Parent node to parent under (optional).
        attributes: Initial attribute values (optional).

    Returns:
        Dictionary with node name, type, parent, attributes_set list,
        and attribute_errors (if any).
    """
    return nodes_create(
        node_type=node_type, name=name, parent=parent, attributes=coerce_dict(attributes)
    )


def tool_nodes_delete(
    nodes: Annotated[list[str], "Node names to delete"],
    hierarchy: Annotated[bool, "Delete entire hierarchy below each node"] = False,
) -> NodesDeleteOutput:
    """Delete Maya nodes.

    Args:
        nodes: List of node names to delete.
        hierarchy: If True, delete entire hierarchy below each node.

    Returns:
        Dictionary with deleted list, count, and errors (if any nodes failed).
    """
    return nodes_delete(nodes=coerce_list(nodes), hierarchy=hierarchy)


def tool_nodes_rename(
    mapping: Annotated[dict[str, str], "Map of current node name to new name"],
) -> NodesRenameOutput:
    """Rename Maya nodes.

    Args:
        mapping: Dictionary mapping current node names to new names.

    Returns:
        Dictionary with renamed list and errors (if any nodes failed).
    """
    return nodes_rename(mapping=coerce_dict(mapping))


def tool_nodes_parent(
    nodes: Annotated[list[str], "Nodes to reparent"],
    parent: Annotated[str | None, "New parent node. If None, unparent (parent to world)."] = None,
    relative: Annotated[bool, "Preserve existing local transformations"] = False,
) -> NodesParentOutput:
    """Reparent Maya nodes.

    Args:
        nodes: List of nodes to reparent.
        parent: New parent node. If None, unparent.
        relative: Preserve local transformations.

    Returns:
        Dictionary with parented list and errors.
    """
    return nodes_parent(nodes=coerce_list(nodes), parent=parent, relative=relative)


def tool_nodes_duplicate(
    nodes: Annotated[list[str], "Nodes to duplicate"],
    name: Annotated[
        str | None, "Name for the new node (only valid when duplicating single node)"
    ] = None,
    input_connections: Annotated[bool, "Duplicate input connections"] = False,
    upstream_nodes: Annotated[bool, "Duplicate upstream nodes"] = False,
    parent_only: Annotated[bool, "Duplicate only the specified node, not its children"] = False,
) -> NodesDuplicateOutput:
    """Duplicate Maya nodes.

    Args:
        nodes: List of nodes to duplicate.
        name: Name for new node (single only).
        input_connections: Duplicate input connections.
        upstream_nodes: Duplicate upstream nodes.
        parent_only: Duplicate only the node.

    Returns:
        Dictionary with duplicated map and errors.
    """
    return nodes_duplicate(
        nodes=coerce_list(nodes),
        name=name,
        input_connections=input_connections,
        upstream_nodes=upstream_nodes,
        parent_only=parent_only,
    )


def tool_nodes_info(
    node: Annotated[str, "Node name to query"],
    info_category: Annotated[
        Literal["summary", "transform", "hierarchy", "attributes", "shape", "all"],
        "Category of information to retrieve",
    ] = "summary",
) -> NodesInfoOutput:
    """Get comprehensive information about a Maya node.

    Args:
        node: Name of the node to query.
        info_category: What information to return. Options:
            summary - node type, parent, children count
            transform - translate, rotate, scale, visibility
            hierarchy - parent, children list, full path
            attributes - all keyable/user-defined attributes with values
            shape - shape nodes, types, connection counts
            all - everything combined

    Returns:
        Dictionary with node information based on info_category.
    """
    return nodes_info(node=node, info_category=info_category)


def register_node_tools(mcp: FastMCP) -> None:
    """Register node tools."""
    mcp.tool(
        name="nodes.list",
        description="List nodes in the Maya scene, optionally filtered by type. "
        "Returns max 500 nodes by default to limit response size.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_nodes_list)

    mcp.tool(
        name="nodes.create",
        description="Create a new node in Maya with optional name, parent, and initial attributes.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_nodes_create)

    mcp.tool(
        name="nodes.delete",
        description="Delete one or more nodes from the Maya scene.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_nodes_delete)

    mcp.tool(
        name="nodes.rename",
        description="Rename one or more nodes in the Maya scene.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_nodes_rename)

    mcp.tool(
        name="nodes.parent",
        description="Reparent one or more nodes in the Maya hierarchy.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_nodes_parent)

    mcp.tool(
        name="nodes.duplicate",
        description="Duplicate one or more nodes.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_nodes_duplicate)

    mcp.tool(
        name="nodes.info",
        description="Get comprehensive information about a Maya node in a single call. "
        "Use info_category to choose: summary (default), transform, hierarchy, "
        "attributes, shape, or all. Reduces tool-call chaining.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_nodes_info)
