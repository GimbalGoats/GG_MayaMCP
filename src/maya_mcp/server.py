"""Maya MCP Server entrypoint.

This module creates and configures the FastMCP server instance,
registers all tools, and provides the main entry point.

Example:
    Run the server::

        python -m maya_mcp.server

    Or use the CLI::

        maya-mcp

    Or import and use programmatically::

        from maya_mcp.server import mcp
        mcp.run()
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from maya_mcp.tools.attributes import attributes_get, attributes_set
from maya_mcp.tools.connection import maya_connect, maya_disconnect
from maya_mcp.tools.health import health_check
from maya_mcp.tools.nodes import (
    nodes_create,
    nodes_delete,
    nodes_duplicate,
    nodes_info,
    nodes_list,
    nodes_parent,
    nodes_rename,
)
from maya_mcp.tools.scene import scene_info, scene_new, scene_open, scene_redo, scene_undo
from maya_mcp.tools.selection import selection_clear, selection_get, selection_set

# Create the FastMCP server instance
mcp = FastMCP(
    name="Maya MCP",
    instructions="""Maya MCP provides tools for controlling Autodesk Maya.

Available tools:
- health.check: Check connection status to Maya
- maya.connect: Connect to Maya commandPort
- maya.disconnect: Disconnect from Maya
- scene.info: Get current scene information (file path, FPS, frame range, etc.)
- scene.new: Create a new empty scene (checks for unsaved changes first)
- scene.open: Open a scene file (validates path and checks for unsaved changes)
- scene.undo: Undo the last operation (critical for error recovery)
- scene.redo: Redo the last undone operation
- nodes.list: List nodes by type or pattern
- nodes.create: Create a new node with optional name, parent, and attributes
- nodes.delete: Delete one or more nodes (with optional hierarchy deletion)
- nodes.info: Get comprehensive node information in one call (summary, transform,
  hierarchy, attributes, shape, or all) - use this instead of multiple attribute queries
- attributes.get: Get attribute values from a node (batch supported)
- attributes.set: Set attribute values on a node (batch supported)
- selection.get: Get current selection
- selection.set: Set selection (replace, add, or deselect)
- selection.clear: Clear the selection (deselect all)

Workflow tips:
- Use nodes.info for a quick overview of any node before making changes
- Use nodes.info(info_category="transform") instead of multiple attributes.get calls
- Use nodes.info(info_category="all") to get everything about a node at once
- Use scene.new(force=True) to discard unsaved changes, or check the error message first

Before using Maya tools, ensure Maya is running with commandPort enabled:
    import maya.cmds as cmds
    cmds.commandPort(name=":7001", sourceType="python", echoOutput=True)
""",
)


# Register health tool
@mcp.tool(
    name="health.check",
    description="Check the health status of the Maya connection",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_health_check() -> dict[str, Any]:
    """Check Maya connection health.

    Returns status (ok/offline/reconnecting), last error, last contact
    timestamp, and connection configuration.
    """
    return health_check()


# Register connection tools
@mcp.tool(
    name="maya.connect",
    description="Establish a connection to Maya's commandPort",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_maya_connect(
    host: Annotated[str, "Target host (localhost only)"] = "localhost",
    port: Annotated[int, "Target port number"] = 7001,
    source_type: Annotated[
        Literal["python", "mel"],
        "Command interpreter type",
    ] = "python",
) -> dict[str, Any]:
    """Connect to Maya commandPort.

    Args:
        host: Target host (localhost or 127.0.0.1 only).
        port: Target port number.
        source_type: Command interpreter (python or mel).

    Returns:
        Connection result with connected status, host, port, and error.
    """
    return maya_connect(host=host, port=port, source_type=source_type)


@mcp.tool(
    name="maya.disconnect",
    description="Close the connection to Maya",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_maya_disconnect() -> dict[str, Any]:
    """Disconnect from Maya commandPort.

    Returns:
        Disconnect result with disconnected status and was_connected flag.
    """
    return maya_disconnect()


# Register scene tools
@mcp.tool(
    name="scene.info",
    description="Get information about the current Maya scene",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_scene_info() -> dict[str, Any]:
    """Get current scene information.

    Returns file path, modification status, FPS, frame range, and up axis.
    """
    return scene_info()


@mcp.tool(
    name="scene.new",
    description="Create a new empty Maya scene. "
    "Checks for unsaved changes first and refuses by default if the scene was modified. "
    "Use force=True to discard unsaved changes.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_scene_new(
    force: Annotated[
        bool,
        "If True, discard unsaved changes. If False (default), refuse when scene has unsaved changes.",
    ] = False,
) -> dict[str, Any]:
    """Create a new empty Maya scene.

    Args:
        force: If True, discard unsaved changes and create new scene.
            If False (default), refuse when scene has unsaved changes.

    Returns:
        Dictionary with success, previous_file, was_modified, and error.
    """
    return scene_new(force=force)


@mcp.tool(
    name="scene.open",
    description="Open a Maya scene file. "
    "Validates the file path and checks for unsaved changes before proceeding. "
    "Use force=True to discard unsaved changes. "
    "Supported formats: .ma (Maya ASCII), .mb (Maya Binary).",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_scene_open(
    file_path: Annotated[
        str,
        "Path to the Maya scene file to open (.ma or .mb)",
    ],
    force: Annotated[
        bool,
        "If True, discard unsaved changes. If False (default), refuse when scene has unsaved changes.",
    ] = False,
) -> dict[str, Any]:
    """Open a Maya scene file.

    Args:
        file_path: Path to the scene file (.ma or .mb).
        force: If True, discard unsaved changes and open the file.
            If False (default), refuse when scene has unsaved changes.

    Returns:
        Dictionary with success, file_path, previous_file, was_modified, and error.
    """
    return scene_open(file_path=file_path, force=force)


@mcp.tool(
    name="scene.undo",
    description="Undo the last operation in Maya. Critical for LLM error recovery.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_scene_undo() -> dict[str, Any]:
    """Undo the last Maya operation.

    Returns success status, description of undone action, and availability
    of further undo/redo operations.
    """
    return scene_undo()


@mcp.tool(
    name="scene.redo",
    description="Redo the last undone operation in Maya.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_scene_redo() -> dict[str, Any]:
    """Redo the last undone Maya operation.

    Returns success status, description of redone action, and availability
    of further undo/redo operations.
    """
    return scene_redo()


# Register node tools
@mcp.tool(
    name="nodes.list",
    description="List nodes in the Maya scene, optionally filtered by type. "
    "Returns max 500 nodes by default to limit response size.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
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
) -> dict[str, Any]:
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


@mcp.tool(
    name="nodes.create",
    description="Create a new node in Maya with optional name, parent, and initial attributes.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_nodes_create(
    node_type: Annotated[str, "Type of node to create (e.g., 'transform', 'locator', 'joint')"],
    name: Annotated[str | None, "Desired node name (Maya may modify for uniqueness)"] = None,
    parent: Annotated[str | None, "Parent node to parent under"] = None,
    attributes: Annotated[
        dict[str, Any] | None,
        "Initial attribute values to set after creation",
    ] = None,
) -> dict[str, Any]:
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
    return nodes_create(node_type=node_type, name=name, parent=parent, attributes=attributes)


@mcp.tool(
    name="nodes.delete",
    description="Delete one or more nodes from the Maya scene.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_nodes_delete(
    nodes: Annotated[list[str], "Node names to delete"],
    hierarchy: Annotated[bool, "Delete entire hierarchy below each node"] = False,
) -> dict[str, Any]:
    """Delete Maya nodes.

    Args:
        nodes: List of node names to delete.
        hierarchy: If True, delete entire hierarchy below each node.

    Returns:
        Dictionary with deleted list, count, and errors (if any nodes failed).
    """
    return nodes_delete(nodes=nodes, hierarchy=hierarchy)


@mcp.tool(
    name="nodes.rename",
    description="Rename one or more nodes in the Maya scene.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_nodes_rename(
    mapping: Annotated[dict[str, str], "Map of current node name to new name"],
) -> dict[str, Any]:
    """Rename Maya nodes.

    Args:
        mapping: Dictionary mapping current node names to new names.

    Returns:
        Dictionary with renamed list and errors (if any nodes failed).
    """
    return nodes_rename(mapping=mapping)


@mcp.tool(
    name="nodes.parent",
    description="Reparent one or more nodes in the Maya hierarchy.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_nodes_parent(
    nodes: Annotated[list[str], "Nodes to reparent"],
    parent: Annotated[str | None, "New parent node. If None, unparent (parent to world)."] = None,
    relative: Annotated[bool, "Preserve existing local transformations"] = False,
) -> dict[str, Any]:
    """Reparent Maya nodes.

    Args:
        nodes: List of nodes to reparent.
        parent: New parent node. If None, unparent.
        relative: Preserve local transformations.

    Returns:
        Dictionary with parented list and errors.
    """
    return nodes_parent(nodes=nodes, parent=parent, relative=relative)


@mcp.tool(
    name="nodes.duplicate",
    description="Duplicate one or more nodes.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_nodes_duplicate(
    nodes: Annotated[list[str], "Nodes to duplicate"],
    name: Annotated[
        str | None, "Name for the new node (only valid when duplicating single node)"
    ] = None,
    input_connections: Annotated[bool, "Duplicate input connections"] = False,
    upstream_nodes: Annotated[bool, "Duplicate upstream nodes"] = False,
    parent_only: Annotated[bool, "Duplicate only the specified node, not its children"] = False,
) -> dict[str, Any]:
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
        nodes=nodes,
        name=name,
        input_connections=input_connections,
        upstream_nodes=upstream_nodes,
        parent_only=parent_only,
    )


@mcp.tool(
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
)
def tool_nodes_info(
    node: Annotated[str, "Node name to query"],
    info_category: Annotated[
        Literal["summary", "transform", "hierarchy", "attributes", "shape", "all"],
        "Category of information to retrieve",
    ] = "summary",
) -> dict[str, Any]:
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


# Register attribute tools
@mcp.tool(
    name="attributes.get",
    description="Get one or more attribute values from a Maya node. "
    "Supports batch queries to reduce tool call chaining.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_attributes_get(
    node: Annotated[str, "Node name to query"],
    attributes: Annotated[list[str], "Attribute names to get (e.g., ['translateX', 'visibility'])"],
) -> dict[str, Any]:
    """Get attribute values from a Maya node.

    Args:
        node: Node name to query.
        attributes: List of attribute names to retrieve.

    Returns:
        Dictionary with node, attributes (name→value map), count,
        and errors (if any attributes failed).
    """
    return attributes_get(node=node, attributes=attributes)


@mcp.tool(
    name="attributes.set",
    description="Set one or more attribute values on a Maya node. "
    "Supports batch operations to reduce tool call chaining.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_attributes_set(
    node: Annotated[str, "Node name to modify"],
    attributes: Annotated[dict[str, Any], "Map of attribute name to value"],
) -> dict[str, Any]:
    """Set attribute values on a Maya node.

    Args:
        node: Node name to modify.
        attributes: Dictionary mapping attribute names to values.

    Returns:
        Dictionary with node, set (list of attrs set), count,
        and errors (if any attributes failed).
    """
    return attributes_set(node=node, attributes=attributes)


# Register selection tools
@mcp.tool(
    name="selection.get",
    description="Get the current selection in Maya",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_selection_get() -> dict[str, Any]:
    """Get current Maya selection.

    Returns:
        Selection list with selection array and count.
    """
    return selection_get()


@mcp.tool(
    name="selection.set",
    description="Set the Maya selection",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_selection_set(
    nodes: Annotated[list[str], "Node names to select"],
    add: Annotated[bool, "Add to existing selection"] = False,
    deselect: Annotated[bool, "Remove from selection"] = False,
) -> dict[str, Any]:
    """Set Maya selection.

    Args:
        nodes: List of node names to operate on.
        add: Add to existing selection instead of replacing.
        deselect: Remove from selection instead of adding.

    Returns:
        New selection state with selection array and count.
    """
    return selection_set(nodes=nodes, add=add, deselect=deselect)


@mcp.tool(
    name="selection.clear",
    description="Clear the Maya selection (deselect all)",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_selection_clear() -> dict[str, Any]:
    """Clear Maya selection.

    Deselects all currently selected nodes.

    Returns:
        Empty selection state with selection array and count of 0.
    """
    return selection_clear()


def main() -> None:
    """Run the Maya MCP server.

    This is the main entry point for the server. It starts the FastMCP
    server with stdio transport (the default for MCP).
    """
    mcp.run()


if __name__ == "__main__":
    main()
