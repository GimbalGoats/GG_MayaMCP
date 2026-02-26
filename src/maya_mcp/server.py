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
from maya_mcp.tools.connections import (
    connections_connect,
    connections_disconnect,
    connections_get,
    connections_history,
    connections_list,
)
from maya_mcp.tools.health import health_check
from maya_mcp.tools.mesh import mesh_evaluate, mesh_info, mesh_vertices
from maya_mcp.tools.nodes import (
    nodes_create,
    nodes_delete,
    nodes_duplicate,
    nodes_info,
    nodes_list,
    nodes_parent,
    nodes_rename,
)
from maya_mcp.tools.scene import (
    scene_export,
    scene_import,
    scene_info,
    scene_new,
    scene_open,
    scene_redo,
    scene_save,
    scene_save_as,
    scene_undo,
)
from maya_mcp.tools.selection import (
    selection_clear,
    selection_convert_components,
    selection_get,
    selection_get_components,
    selection_set,
    selection_set_components,
)

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
- scene.save: Save the current scene (fails if untitled)
- scene.save_as: Save scene to a new path (.ma or .mb)
- scene.import: Import a file into the current scene (.ma, .mb, .obj, .fbx, .abc, .usd)
- scene.export: Export selection or entire scene to a file
- scene.undo: Undo the last operation (critical for error recovery)
- scene.redo: Redo the last undone operation
- nodes.list: List nodes by type or pattern
- nodes.create: Create a new node with optional name, parent, and attributes
- nodes.delete: Delete one or more nodes (with optional hierarchy deletion)
- nodes.rename: Rename one or more nodes (batch supported)
- nodes.parent: Reparent nodes in hierarchy (or unparent to world)
- nodes.duplicate: Duplicate nodes with optional hierarchy and connections
- nodes.info: Get comprehensive node information in one call (summary, transform,
  hierarchy, attributes, shape, or all) - use this instead of multiple attribute queries
- attributes.get: Get attribute values from a node (batch supported)
- attributes.set: Set attribute values on a node (batch supported)
- connections.list: List connections on a node with direction/type filters
- connections.get: Get detailed connection info for specific attributes
- connections.connect: Connect two attributes (with optional force disconnect)
- connections.disconnect: Disconnect attributes (specific or all incoming/outgoing)
- connections.history: List construction/deformation history on a node
- mesh.info: Get mesh statistics (vertex/face/edge counts, bounding box, UV status)
- mesh.vertices: Query vertex positions with offset/limit pagination
- mesh.evaluate: Analyze mesh topology (non-manifold edges, lamina faces, holes, borders)
- selection.get: Get current selection
- selection.set: Set selection (replace, add, or deselect)
- selection.clear: Clear the selection (deselect all)
- selection.set_components: Select mesh components (vertices, edges, faces)
- selection.get_components: Get selected components grouped by type
- selection.convert_components: Convert selection between vertex/edge/face

Workflow tips:
- Use nodes.info for a quick overview of any node before making changes
- Use nodes.info(info_category="transform") instead of multiple attributes.get calls
- Use nodes.info(info_category="all") to get everything about a node at once
- Use connections.history(direction="input") to find upstream deformers
- Use connections.connect(force=True) for safe disconnect-before-reconnect pattern
- Use scene.new(force=True) to discard unsaved changes, or check the error message first
- Use scene.import with namespace to organize imported assets
- Use scene.export(export_mode="all") to export the entire scene
- Use mesh.evaluate() to check mesh topology before rigging or exporting
- Use selection.set_components() for precise vertex/edge/face selection

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
    name="scene.save",
    description="Save the current scene. "
    "Saves to the current file path. Fails if the scene is untitled.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_scene_save() -> dict[str, Any]:
    """Save the current Maya scene.

    Returns:
        Dictionary with success, file_path, and error.
    """
    return scene_save()


@mcp.tool(
    name="scene.save_as",
    description="Save the scene to a new file path. "
    "Validates the path and saves as Maya ASCII or Binary based on extension.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_scene_save_as(
    file_path: Annotated[
        str,
        "Absolute or relative path to save the scene to (.ma or .mb)",
    ],
) -> dict[str, Any]:
    """Save the scene to a new file path.

    Args:
        file_path: Path to save the scene to.

    Returns:
        Dictionary with success, file_path, and error.
    """
    return scene_save_as(file_path=file_path)


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


@mcp.tool(
    name="scene.import",
    description="Import a file into the current Maya scene. "
    "Supports multiple formats (.ma, .mb, .obj, .fbx, .abc, .usd, .usda, .usdc, .usdz). "
    "Returns only top-level parent transforms to protect token budget.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_scene_import(
    file_path: Annotated[
        str,
        "Path to the file to import (.ma, .mb, .obj, .fbx, .abc, .usd, .usda, .usdc, .usdz)",
    ],
    namespace: Annotated[
        str | None,
        "Namespace behavior: None = no namespace, '' = auto-generate, 'name' = use specified",
    ] = None,
    force: Annotated[
        bool,
        "If True, replace existing namespace contents. If False (default), merge.",
    ] = False,
) -> dict[str, Any]:
    """Import a file into the current Maya scene.

    Args:
        file_path: Path to the file to import.
        namespace: Namespace behavior:
            - None (default): Import without namespace
            - "": Auto-generate namespace from filename
            - "myNs": Use specified namespace
        force: If True, replace existing namespace contents.

    Returns:
        Dictionary with success, file_path, nodes (top-level parents),
        count, and error.
    """
    return scene_import(file_path=file_path, namespace=namespace, force=force)


@mcp.tool(
    name="scene.export",
    description="Export scene content to a file. "
    "Export selected nodes or entire scene. "
    "Supports multiple formats (.ma, .mb, .obj, .fbx, .abc, .usd, .usda, .usdc).",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_scene_export(
    file_path: Annotated[
        str,
        "Path for the exported file (.ma, .mb, .obj, .fbx, .abc, .usd, .usda, .usdc)",
    ],
    export_mode: Annotated[
        Literal["selected", "all"],
        "What to export: 'selected' (default) or 'all'",
    ] = "selected",
    animation: Annotated[
        bool,
        "If True, include animation data (FBX only). If False (default), export static.",
    ] = False,
) -> dict[str, Any]:
    """Export scene content to a file.

    Args:
        file_path: Path for the exported file.
        export_mode: 'selected' to export selection, 'all' for entire scene.
        animation: Include animation data (FBX only).

    Returns:
        Dictionary with success, file_path, nodes_exported, and error.
    """
    return scene_export(file_path=file_path, export_mode=export_mode, animation=animation)


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


# Register connection tools
@mcp.tool(
    name="connections.list",
    description="List connections on a Maya node with direction and type filters. "
    "Returns max 500 connections by default to limit response size.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
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
) -> dict[str, Any]:
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


@mcp.tool(
    name="connections.get",
    description="Get detailed connection information for specific attributes on a node.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_connections_get(
    node: Annotated[str, "Node name to query"],
    attributes: Annotated[
        list[str] | None,
        "Attribute names to check for connections (None = all connectable attrs)",
    ] = None,
) -> dict[str, Any]:
    """Get connection details for specific attributes.

    Args:
        node: Node name to query.
        attributes: List of attribute names to check, or None for all.

    Returns:
        Dictionary with attribute connection details.
    """
    return connections_get(node=node, attributes=attributes)


@mcp.tool(
    name="connections.connect",
    description="Connect two attributes in Maya. "
    "Use force=True to disconnect existing connections first.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_connections_connect(
    source: Annotated[str, "Source plug in 'node.attribute' format"],
    destination: Annotated[str, "Destination plug in 'node.attribute' format"],
    force: Annotated[
        bool,
        "If True, disconnect existing connections to destination first",
    ] = False,
) -> dict[str, Any]:
    """Connect two attributes.

    Args:
        source: Source plug (node.attribute).
        destination: Destination plug (node.attribute).
        force: Disconnect existing connections first.

    Returns:
        Dictionary with connection result and any disconnected plugs.
    """
    return connections_connect(source=source, destination=destination, force=force)


@mcp.tool(
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
)
def tool_connections_disconnect(
    source: Annotated[
        str | None,
        "Source plug to disconnect from (None = use destination only)",
    ] = None,
    destination: Annotated[
        str | None,
        "Destination plug to disconnect from (None = use source only)",
    ] = None,
) -> dict[str, Any]:
    """Disconnect attributes.

    Args:
        source: Source plug (optional).
        destination: Destination plug (optional).

    Returns:
        Dictionary with disconnected connections list.
    """
    return connections_disconnect(source=source, destination=destination)


@mcp.tool(
    name="connections.history",
    description="List construction/deformation history on a node. "
    "Traverses upstream (input) or downstream (output) dependency graph.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
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
) -> dict[str, Any]:
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


# Register mesh tools
@mcp.tool(
    name="mesh.info",
    description="Get mesh statistics: vertex/face/edge counts, bounding box, UV status",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_mesh_info(
    node: Annotated[str, "Name of the mesh node (transform or shape)"],
) -> dict[str, Any]:
    """Get mesh statistics.

    Args:
        node: Name of the mesh node (transform or shape).

    Returns:
        Dictionary with vertex_count, face_count, edge_count, bounding_box,
        uv_sets, has_uvs, and errors.
    """
    return mesh_info(node=node)


@mcp.tool(
    name="mesh.vertices",
    description="Query vertex positions from a mesh with offset/limit pagination. "
    "Returns vertex positions as [x, y, z] arrays.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_mesh_vertices(
    node: Annotated[str, "Name of the mesh node (transform or shape)"],
    offset: Annotated[int, "Starting vertex index (0-based)"] = 0,
    limit: Annotated[
        int | None,
        "Maximum vertices to return (default 1000, use 0 for unlimited)",
    ] = 1000,
) -> dict[str, Any]:
    """Query vertex positions from a mesh.

    Args:
        node: Name of the mesh node.
        offset: Starting vertex index.
        limit: Maximum vertices to return.

    Returns:
        Dictionary with vertices list, vertex_count, offset, count, and errors.
    """
    return mesh_vertices(node=node, offset=offset, limit=limit)


@mcp.tool(
    name="mesh.evaluate",
    description="Analyze mesh topology for issues: non-manifold edges, lamina faces, "
    "holes, and border edges.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_mesh_evaluate(
    node: Annotated[str, "Name of the mesh node (transform or shape)"],
    checks: Annotated[
        list[Literal["non_manifold", "lamina", "holes", "border"]] | None,
        "Checks to perform (default: all)",
    ] = None,
    limit: Annotated[
        int | None,
        "Max components per check (default 500)",
    ] = 500,
) -> dict[str, Any]:
    """Analyze mesh topology.

    Args:
        node: Name of the mesh node.
        checks: List of checks to perform. Options:
            non_manifold, lamina, holes, border. Default: all.
        limit: Maximum components to return per check.

    Returns:
        Dictionary with topology analysis results and is_clean flag.
    """
    return mesh_evaluate(node=node, checks=checks, limit=limit)


# Register component selection tools
@mcp.tool(
    name="selection.set_components",
    description="Select mesh components (vertices, edges, or faces) using Maya notation "
    "(e.g., 'pCube1.vtx[0:10]', 'pSphere1.e[5]', 'pPlane1.f[0:99]').",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_selection_set_components(
    components: Annotated[
        list[str],
        "Component specifications (e.g., ['pCube1.vtx[0:7]', 'pCube1.f[0]'])",
    ],
    add: Annotated[bool, "Add to existing selection"] = False,
    deselect: Annotated[bool, "Remove from selection"] = False,
) -> dict[str, Any]:
    """Select mesh components.

    Args:
        components: List of component specifications in Maya notation.
        add: Add to existing selection.
        deselect: Remove from selection.

    Returns:
        Dictionary with selection list, count, and errors.
    """
    return selection_set_components(components=components, add=add, deselect=deselect)


@mcp.tool(
    name="selection.get_components",
    description="Get currently selected mesh components grouped by type "
    "(vertices, edges, faces).",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_selection_get_components() -> dict[str, Any]:
    """Get selected mesh components.

    Returns:
        Dictionary with selection, vertices, edges, faces lists and counts.
    """
    return selection_get_components()


@mcp.tool(
    name="selection.convert_components",
    description="Convert the current selection to a different component type "
    "(vertex, edge, or face).",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_selection_convert_components(
    to_type: Annotated[
        Literal["vertex", "edge", "face"],
        "Target component type",
    ],
    nodes: Annotated[
        list[str] | None,
        "Nodes to convert (None = use current selection)",
    ] = None,
) -> dict[str, Any]:
    """Convert selection to different component type.

    Args:
        to_type: Target component type (vertex, edge, face).
        nodes: Optional nodes to convert. If None, uses current selection.

    Returns:
        Dictionary with converted selection list and count.
    """
    return selection_convert_components(to_type=to_type, nodes=nodes)


def main() -> None:
    """Run the Maya MCP server.

    This is the main entry point for the server. It starts the FastMCP
    server with stdio transport (the default for MCP).
    """
    mcp.run()


if __name__ == "__main__":
    main()
