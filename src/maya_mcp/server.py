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

from maya_mcp import __version__
from maya_mcp.tools.animation import (
    TangentType,
    animation_delete_keyframes,
    animation_get_keyframes,
    animation_get_time_range,
    animation_set_keyframe,
    animation_set_time,
    animation_set_time_range,
)
from maya_mcp.tools.attributes import (
    AttributesGetOutput,
    AttributesSetOutput,
    attributes_get,
    attributes_set,
)
from maya_mcp.tools.connection import (
    MayaConnectOutput,
    MayaDisconnectOutput,
    maya_connect,
    maya_disconnect,
)
from maya_mcp.tools.connections import (
    connections_connect,
    connections_disconnect,
    connections_get,
    connections_history,
    connections_list,
)
from maya_mcp.tools.health import HealthCheckOutput, health_check
from maya_mcp.tools.mesh import mesh_evaluate, mesh_info, mesh_vertices
from maya_mcp.tools.modeling import (
    modeling_bevel,
    modeling_boolean,
    modeling_bridge,
    modeling_center_pivot,
    modeling_combine,
    modeling_create_polygon_primitive,
    modeling_delete_faces,
    modeling_delete_history,
    modeling_extrude_faces,
    modeling_freeze_transforms,
    modeling_insert_edge_loop,
    modeling_merge_vertices,
    modeling_move_components,
    modeling_separate,
    modeling_set_pivot,
)
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
from maya_mcp.tools.scene import (
    SceneInfoOutput,
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
from maya_mcp.tools.shading import (
    shading_assign_material,
    shading_create_material,
    shading_set_material_color,
)
from maya_mcp.tools.skin import (
    skin_bind,
    skin_copy_weights,
    skin_influences,
    skin_unbind,
    skin_weights_get,
    skin_weights_set,
)
from maya_mcp.tools.viewport import ViewportFormat, viewport_capture
from maya_mcp.utils.coercion import coerce_dict, coerce_list

SERVER_VERSION = __version__
SERVER_WEBSITE_URL = "https://github.com/GimbalGoats/GG_MayaMCP"
SERVER_INSTRUCTIONS = """Maya MCP exposes typed tools for controlling a local Autodesk Maya session through
localhost commandPort. Use the tool descriptions and schemas as the source of truth,
keep read-only inspection separate from mutating actions, and enable raw script
execution only with the explicit MAYA_MCP_ENABLE_RAW_EXECUTION opt-in."""

# Create the FastMCP server instance
mcp = FastMCP(
    name="Maya MCP",
    instructions=SERVER_INSTRUCTIONS,
    version=SERVER_VERSION,
    website_url=SERVER_WEBSITE_URL,
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
def tool_health_check() -> HealthCheckOutput:
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
) -> MayaConnectOutput:
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
def tool_maya_disconnect() -> MayaDisconnectOutput:
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
def tool_scene_info() -> SceneInfoOutput:
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
) -> NodesDeleteOutput:
    """Delete Maya nodes.

    Args:
        nodes: List of node names to delete.
        hierarchy: If True, delete entire hierarchy below each node.

    Returns:
        Dictionary with deleted list, count, and errors (if any nodes failed).
    """
    return nodes_delete(nodes=coerce_list(nodes), hierarchy=hierarchy)


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
) -> NodesRenameOutput:
    """Rename Maya nodes.

    Args:
        mapping: Dictionary mapping current node names to new names.

    Returns:
        Dictionary with renamed list and errors (if any nodes failed).
    """
    return nodes_rename(mapping=coerce_dict(mapping))


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
) -> AttributesGetOutput:
    """Get attribute values from a Maya node.

    Args:
        node: Node name to query.
        attributes: List of attribute names to retrieve.

    Returns:
        Dictionary with node, attributes (name→value map), count,
        and errors (if any attributes failed).
    """
    return attributes_get(node=node, attributes=coerce_list(attributes))


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
    return connections_get(node=node, attributes=coerce_list(attributes))


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
def tool_selection_get() -> SelectionOutput:
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
def tool_selection_clear() -> SelectionOutput:
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
    return mesh_evaluate(node=node, checks=coerce_list(checks), limit=limit)


@mcp.tool(
    name="viewport.capture",
    description="Capture a single viewport frame as inline image content using Maya playblast. "
    "Read-only: does not modify scene data.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_viewport_capture(
    format: Annotated[
        ViewportFormat,
        "Image format: 'jpeg' (default) or 'png'",
    ] = "jpeg",
    width: Annotated[int, "Capture width in pixels (64-4096)"] = 1024,
    height: Annotated[int, "Capture height in pixels (64-4096)"] = 576,
    quality: Annotated[
        int,
        "JPEG quality 1-100 (used when format='jpeg')",
    ] = 85,
    offscreen: Annotated[bool, "Use offscreen capture when available (default False)"] = False,
    show_ornaments: Annotated[bool, "Show viewport ornaments/gizmos (default True)"] = True,
    panel: Annotated[str | None, "Optional preferred modelPanel name"] = None,
    frame: Annotated[
        float | None,
        "Optional frame to capture (defaults to current time)",
    ] = None,
) -> Any:
    """Capture viewport image via Maya playblast.

    Args:
        format: Output image format.
        width: Capture width.
        height: Capture height.
        quality: JPEG quality.
        offscreen: Offscreen capture flag.
        show_ornaments: Show viewport ornaments flag.
        panel: Optional preferred modelPanel.
        frame: Optional frame number.

    Returns:
        FastMCP Image helper object (auto-converted to MCP ImageContent).
    """
    return viewport_capture(
        format=format,
        width=width,
        height=height,
        quality=quality,
        offscreen=offscreen,
        show_ornaments=show_ornaments,
        panel=panel,
        frame=frame,
    )


# Register curve tools
@mcp.tool(
    name="curve.info",
    description="Get NURBS curve information: degree, spans, form, CV count, knots, length, bounding box.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_curve_info(
    node: Annotated[str, "Name of the curve node (transform or shape)"],
) -> dict[str, Any]:
    """Get NURBS curve information.

    Args:
        node: Name of the curve node (transform or shape).

    Returns:
        Dictionary with degree, spans, form, cv_count, knots, length,
        bounding_box, and errors.
    """
    from maya_mcp.tools.curve import curve_info as _curve_info

    return _curve_info(node=node)


@mcp.tool(
    name="curve.cvs",
    description="Query CV positions from a NURBS curve with offset/limit pagination. "
    "Returns CV positions as [x, y, z] arrays in world space.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_curve_cvs(
    node: Annotated[str, "Name of the curve node (transform or shape)"],
    offset: Annotated[int, "Starting CV index (0-based)"] = 0,
    limit: Annotated[
        int | None,
        "Maximum CVs to return (default 1000, use 0 for unlimited)",
    ] = 1000,
) -> dict[str, Any]:
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


@mcp.tool(
    name="selection.get_components",
    description="Get currently selected mesh components grouped by type (vertices, edges, faces).",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_selection_get_components() -> SelectionComponentsOutput:
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
) -> SelectionConvertComponentsOutput:
    """Convert selection to different component type.

    Args:
        to_type: Target component type (vertex, edge, face).
        nodes: Optional nodes to convert. If None, uses current selection.

    Returns:
        Dictionary with converted selection list and count.
    """
    return selection_convert_components(to_type=to_type, nodes=coerce_list(nodes))


# Register modeling tools
@mcp.tool(
    name="modeling.create_polygon_primitive",
    description="Create a polygon primitive (cube, sphere, cylinder, cone, torus, plane) "
    "with configurable dimensions, subdivisions, and axis.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_modeling_create_polygon_primitive(
    primitive_type: Annotated[
        Literal["cube", "sphere", "cylinder", "cone", "torus", "plane"],
        "Type of primitive to create",
    ],
    name: Annotated[str | None, "Optional name for the transform node"] = None,
    width: Annotated[float, "Width (cube/plane)"] = 1.0,
    height: Annotated[float, "Height (cube/cylinder/cone/plane)"] = 1.0,
    depth: Annotated[float, "Depth (cube)"] = 1.0,
    radius: Annotated[float, "Radius (sphere/cylinder/cone/torus)"] = 0.5,
    subdivisions_width: Annotated[int | None, "Width subdivisions"] = None,
    subdivisions_height: Annotated[int | None, "Height subdivisions"] = None,
    subdivisions_depth: Annotated[int | None, "Depth subdivisions"] = None,
    subdivisions_axis: Annotated[
        int | None, "Axis subdivisions (sphere/cylinder/cone/torus)"
    ] = None,
    axis: Annotated[Literal["x", "y", "z"], "Up axis for the primitive"] = "y",
) -> dict[str, Any]:
    """Create a polygon primitive.

    Args:
        primitive_type: Type of primitive to create.
        name: Optional name for the transform node.
        width: Width of the primitive.
        height: Height of the primitive.
        depth: Depth of the primitive.
        radius: Radius of the primitive.
        subdivisions_width: Width subdivisions.
        subdivisions_height: Height subdivisions.
        subdivisions_depth: Depth subdivisions.
        subdivisions_axis: Axis subdivisions.
        axis: Up axis.

    Returns:
        Dictionary with transform, shape, constructor, primitive_type,
        vertex_count, face_count, and errors.
    """
    return modeling_create_polygon_primitive(
        primitive_type=primitive_type,
        name=name,
        width=width,
        height=height,
        depth=depth,
        radius=radius,
        subdivisions_width=subdivisions_width,
        subdivisions_height=subdivisions_height,
        subdivisions_depth=subdivisions_depth,
        subdivisions_axis=subdivisions_axis,
        axis=axis,
    )


@mcp.tool(
    name="modeling.extrude_faces",
    description="Extrude polygon faces with local translation, offset, and division options.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_modeling_extrude_faces(
    faces: Annotated[
        list[str], "Face components to extrude (e.g., ['pCube1.f[0]', 'pCube1.f[2]'])"
    ],
    local_translate_z: Annotated[float | None, "Local Z translation (extrusion thickness)"] = None,
    local_translate_x: Annotated[float | None, "Local X translation"] = None,
    local_translate_y: Annotated[float | None, "Local Y translation"] = None,
    offset: Annotated[float | None, "Offset amount for the extrusion"] = None,
    divisions: Annotated[int, "Number of extrusion divisions"] = 1,
    keep_faces_together: Annotated[bool, "Keep faces together during extrusion"] = True,
) -> dict[str, Any]:
    """Extrude polygon faces.

    Args:
        faces: Face component strings to extrude.
        local_translate_z: Local Z translation.
        local_translate_x: Local X translation.
        local_translate_y: Local Y translation.
        offset: Offset amount.
        divisions: Number of divisions.
        keep_faces_together: Keep faces together.

    Returns:
        Dictionary with node, faces_extruded, new_face_count, and errors.
    """
    return modeling_extrude_faces(
        faces=coerce_list(faces),
        local_translate_z=local_translate_z,
        local_translate_x=local_translate_x,
        local_translate_y=local_translate_y,
        offset=offset,
        divisions=divisions,
        keep_faces_together=keep_faces_together,
    )


@mcp.tool(
    name="modeling.boolean",
    description="Perform a boolean operation (union, difference, intersection) on two meshes.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_modeling_boolean(
    mesh_a: Annotated[str, "First mesh (base)"],
    mesh_b: Annotated[str, "Second mesh (operand)"],
    operation: Annotated[
        Literal["union", "difference", "intersection"],
        "Boolean operation type",
    ] = "union",
) -> dict[str, Any]:
    """Perform a boolean operation on two meshes.

    Args:
        mesh_a: First mesh.
        mesh_b: Second mesh.
        operation: Boolean operation type.

    Returns:
        Dictionary with result_mesh, operation, vertex_count, face_count, and errors.
    """
    return modeling_boolean(mesh_a=mesh_a, mesh_b=mesh_b, operation=operation)


@mcp.tool(
    name="modeling.combine",
    description="Combine multiple meshes into a single mesh.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_modeling_combine(
    meshes: Annotated[list[str], "List of mesh names to combine (minimum 2)"],
    name: Annotated[str | None, "Optional name for the combined mesh"] = None,
) -> dict[str, Any]:
    """Combine multiple meshes into one.

    Args:
        meshes: List of mesh names to combine.
        name: Optional name for the result.

    Returns:
        Dictionary with result_mesh, source_meshes, vertex_count, face_count, and errors.
    """
    return modeling_combine(meshes=coerce_list(meshes), name=name)


@mcp.tool(
    name="modeling.separate",
    description="Separate a combined mesh into individual meshes.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_modeling_separate(
    mesh: Annotated[str, "Name of the mesh to separate"],
) -> dict[str, Any]:
    """Separate a combined mesh into individual meshes.

    Args:
        mesh: Name of the mesh to separate.

    Returns:
        Dictionary with source_mesh, result_meshes, count, and errors.
    """
    return modeling_separate(mesh=mesh)


@mcp.tool(
    name="modeling.merge_vertices",
    description="Merge vertices on a mesh within a distance threshold.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_modeling_merge_vertices(
    mesh: Annotated[str, "Name of the mesh"],
    threshold: Annotated[float, "Distance threshold for merging (default 0.001)"] = 0.001,
    vertices: Annotated[
        list[str] | None,
        "Optional specific vertex components to merge (None = all vertices)",
    ] = None,
) -> dict[str, Any]:
    """Merge vertices within a distance threshold.

    Args:
        mesh: Name of the mesh.
        threshold: Distance threshold.
        vertices: Optional specific vertices.

    Returns:
        Dictionary with mesh, vertices_merged, vertex_count_before,
        vertex_count_after, and errors.
    """
    return modeling_merge_vertices(mesh=mesh, threshold=threshold, vertices=coerce_list(vertices))


@mcp.tool(
    name="modeling.bevel",
    description="Bevel edges or vertices with offset, segments, and fraction options.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_modeling_bevel(
    components: Annotated[
        list[str], "Edge or vertex components to bevel (e.g., ['pCube1.e[0:3]'])"
    ],
    offset: Annotated[float, "Bevel offset distance (default 0.5)"] = 0.5,
    segments: Annotated[int, "Number of bevel segments (default 1)"] = 1,
    fraction: Annotated[float, "Bevel fraction (default 0.5)"] = 0.5,
) -> dict[str, Any]:
    """Bevel edges or vertices.

    Args:
        components: Edge or vertex components to bevel.
        offset: Bevel offset distance.
        segments: Number of segments.
        fraction: Bevel fraction.

    Returns:
        Dictionary with node, components_beveled, new_vertex_count,
        new_face_count, and errors.
    """
    return modeling_bevel(
        components=coerce_list(components),
        offset=offset,
        segments=segments,
        fraction=fraction,
    )


@mcp.tool(
    name="modeling.bridge",
    description="Bridge between edge loops to create connecting faces.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_modeling_bridge(
    edge_loops: Annotated[list[str], "Edge components for the edge loops to bridge"],
    divisions: Annotated[int, "Number of divisions in the bridge (default 0)"] = 0,
    twist: Annotated[int, "Twist amount (default 0)"] = 0,
    taper: Annotated[float, "Taper amount (default 1.0)"] = 1.0,
) -> dict[str, Any]:
    """Bridge between edge loops.

    Args:
        edge_loops: Edge components to bridge.
        divisions: Number of divisions.
        twist: Twist amount.
        taper: Taper amount.

    Returns:
        Dictionary with node, new_face_count, and errors.
    """
    return modeling_bridge(
        edge_loops=coerce_list(edge_loops),
        divisions=divisions,
        twist=twist,
        taper=taper,
    )


@mcp.tool(
    name="modeling.insert_edge_loop",
    description="Insert an edge loop at the specified edge using polySplitRing.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_modeling_insert_edge_loop(
    edge: Annotated[str, "Single edge component (e.g., 'pCube1.e[4]')"],
    divisions: Annotated[int, "Number of edge loops to insert (default 1)"] = 1,
    weight: Annotated[float, "Position weight along the edge (0-1, default 0.5)"] = 0.5,
) -> dict[str, Any]:
    """Insert an edge loop.

    Args:
        edge: Single edge component.
        divisions: Number of edge loops.
        weight: Position weight.

    Returns:
        Dictionary with node, edge, new_edge_count, new_vertex_count, and errors.
    """
    return modeling_insert_edge_loop(edge=edge, divisions=divisions, weight=weight)


@mcp.tool(
    name="modeling.delete_faces",
    description="Delete polygon faces from a mesh.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_modeling_delete_faces(
    faces: Annotated[list[str], "Face components to delete (e.g., ['pCube1.f[0]', 'pCube1.f[3]'])"],
) -> dict[str, Any]:
    """Delete polygon faces.

    Args:
        faces: Face component strings to delete.

    Returns:
        Dictionary with faces_deleted, mesh, remaining_face_count, and errors.
    """
    return modeling_delete_faces(faces=coerce_list(faces))


@mcp.tool(
    name="modeling.move_components",
    description="Move mesh components (vertices, edges, faces) by relative translation or to an absolute position.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_modeling_move_components(
    components: Annotated[list[str], "Component strings to move (e.g., ['pCube1.vtx[0:3]'])"],
    translate: Annotated[
        list[float] | None,
        "Relative [x, y, z] translation (mutually exclusive with absolute)",
    ] = None,
    absolute: Annotated[
        list[float] | None,
        "Absolute [x, y, z] position (mutually exclusive with translate)",
    ] = None,
    world_space: Annotated[bool, "Use world space coordinates (default True)"] = True,
) -> dict[str, Any]:
    """Move mesh components.

    Exactly one of translate or absolute must be provided.

    Args:
        components: Component strings to move.
        translate: Relative translation.
        absolute: Absolute position.
        world_space: Use world space.

    Returns:
        Dictionary with components_moved, translate/absolute, world_space, and errors.
    """
    return modeling_move_components(
        components=coerce_list(components),
        translate=coerce_list(translate),
        absolute=coerce_list(absolute),
        world_space=world_space,
    )


@mcp.tool(
    name="modeling.freeze_transforms",
    description="Freeze (reset) transforms on nodes, applying current values as identity.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_modeling_freeze_transforms(
    nodes: Annotated[list[str], "Node names to freeze transforms on"],
    translate: Annotated[bool, "Freeze translation (default True)"] = True,
    rotate: Annotated[bool, "Freeze rotation (default True)"] = True,
    scale: Annotated[bool, "Freeze scale (default True)"] = True,
) -> dict[str, Any]:
    """Freeze transforms on nodes.

    Args:
        nodes: Node names to freeze.
        translate: Freeze translation.
        rotate: Freeze rotation.
        scale: Freeze scale.

    Returns:
        Dictionary with frozen list, count, and errors.
    """
    return modeling_freeze_transforms(
        nodes=coerce_list(nodes),
        translate=translate,
        rotate=rotate,
        scale=scale,
    )


@mcp.tool(
    name="modeling.delete_history",
    description="Delete construction history from nodes or the entire scene.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_modeling_delete_history(
    nodes: Annotated[list[str] | None, "Node names to delete history from"] = None,
    all_nodes: Annotated[bool, "If True, delete history from all nodes in the scene"] = False,
) -> dict[str, Any]:
    """Delete construction history.

    Args:
        nodes: Node names to clean, or None if all_nodes is True.
        all_nodes: Delete history from all scene nodes.

    Returns:
        Dictionary with cleaned list, count, and errors.
    """
    return modeling_delete_history(nodes=coerce_list(nodes), all_nodes=all_nodes)


@mcp.tool(
    name="modeling.center_pivot",
    description="Center the pivot point on nodes.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_modeling_center_pivot(
    nodes: Annotated[list[str], "Node names to center pivots on"],
) -> dict[str, Any]:
    """Center pivot on nodes.

    Args:
        nodes: Node names to center pivots on.

    Returns:
        Dictionary with centered list, count, pivot_positions, and errors.
    """
    return modeling_center_pivot(nodes=coerce_list(nodes))


@mcp.tool(
    name="modeling.set_pivot",
    description="Set the pivot point of a node to an explicit position.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_modeling_set_pivot(
    node: Annotated[str, "Node name to set pivot on"],
    position: Annotated[list[float], "[x, y, z] position for the pivot"],
    world_space: Annotated[bool, "Position is in world space (default True)"] = True,
) -> dict[str, Any]:
    """Set the pivot point of a node.

    Args:
        node: Node name.
        position: [x, y, z] position.
        world_space: Use world space.

    Returns:
        Dictionary with node, pivot, world_space, and errors.
    """
    return modeling_set_pivot(
        node=node,
        position=coerce_list(position),
        world_space=world_space,
    )


# Register shading tools
@mcp.tool(
    name="shading.create_material",
    description="Create a material (lambert, blinn, phong, standardSurface) "
    "with an associated shading group and optional color.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_shading_create_material(
    material_type: Annotated[
        Literal["lambert", "blinn", "phong", "standardSurface"],
        "Type of material shader to create",
    ] = "lambert",
    name: Annotated[str | None, "Optional name for the material node"] = None,
    color: Annotated[list[float] | None, "Optional [r, g, b] color (0-1 range)"] = None,
) -> dict[str, Any]:
    """Create a new material with shading group.

    Args:
        material_type: Type of material shader.
        name: Optional name.
        color: Optional [r, g, b] color.

    Returns:
        Dictionary with material, shading_group, material_type, and errors.
    """
    return shading_create_material(material_type=material_type, name=name, color=coerce_list(color))


@mcp.tool(
    name="shading.assign_material",
    description="Assign a material to meshes or face components. "
    "Resolves the shading group from the material automatically.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_shading_assign_material(
    targets: Annotated[list[str], "Meshes or face components to assign the material to"],
    material: Annotated[str, "Name of the material (or shading group) to assign"],
) -> dict[str, Any]:
    """Assign a material to targets.

    Args:
        targets: Meshes or face components.
        material: Material or shading group name.

    Returns:
        Dictionary with assigned list, material, shading_group, and errors.
    """
    return shading_assign_material(
        targets=coerce_list(targets),
        material=material,
    )


@mcp.tool(
    name="shading.set_material_color",
    description="Set a color attribute on a material (e.g., color, baseColor, transparency).",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_shading_set_material_color(
    material: Annotated[str, "Name of the material node"],
    color: Annotated[list[float], "[r, g, b] color values (0-1 range)"],
    attribute: Annotated[
        str,
        "Color attribute name (e.g., 'color', 'baseColor', 'transparency', 'incandescence')",
    ] = "color",
) -> dict[str, Any]:
    """Set a color attribute on a material.

    Args:
        material: Material node name.
        color: [r, g, b] color values.
        attribute: Color attribute name.

    Returns:
        Dictionary with material, attribute, color, and errors.
    """
    return shading_set_material_color(
        material=material,
        color=coerce_list(color),
        attribute=attribute,
    )


# Register skin tools
@mcp.tool(
    name="skin.bind",
    description="Bind a mesh to a skeleton with influence options. "
    "Creates a skinCluster with configurable bind method and max influences.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_skin_bind(
    mesh: Annotated[str, "Name of the mesh to bind"],
    joints: Annotated[list[str], "List of joint names to use as influences"],
    max_influences: Annotated[int, "Maximum influences per vertex (default 4)"] = 4,
    bind_method: Annotated[
        Literal["closestDistance", "heatMap", "geodesicVoxel"],
        "Binding algorithm: closestDistance (default), heatMap, or geodesicVoxel",
    ] = "closestDistance",
) -> dict[str, Any]:
    """Bind mesh to skeleton.

    Args:
        mesh: Name of the mesh to bind.
        joints: List of joint names to use as influences.
        max_influences: Maximum influences per vertex.
        bind_method: Binding algorithm to use.

    Returns:
        Dictionary with mesh, skin_cluster, influences, influence_count, and errors.
    """
    return skin_bind(
        mesh=mesh,
        joints=coerce_list(joints),
        max_influences=max_influences,
        bind_method=bind_method,
    )


@mcp.tool(
    name="skin.unbind",
    description="Detach a skin cluster from a mesh, removing skin deformation.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_skin_unbind(
    mesh: Annotated[str, "Name of the mesh to unbind"],
) -> dict[str, Any]:
    """Unbind skin cluster from mesh.

    Args:
        mesh: Name of the mesh to unbind.

    Returns:
        Dictionary with mesh, unbound, skin_cluster, and errors.
    """
    return skin_unbind(mesh=mesh)


@mcp.tool(
    name="skin.influences",
    description="List influences (joints) on a skin cluster with index mapping.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_skin_influences(
    skin_cluster: Annotated[str, "Name of the skinCluster node"],
) -> dict[str, Any]:
    """List influences on a skin cluster.

    Args:
        skin_cluster: Name of the skinCluster to query.

    Returns:
        Dictionary with skin_cluster, influences (name and index), count, and errors.
    """
    return skin_influences(skin_cluster=skin_cluster)


@mcp.tool(
    name="skin.weights.get",
    description="Get per-vertex skin weights with offset/limit pagination. "
    "Default limit is 100 vertices (skin weight data is dense). "
    "Use offset to paginate through large meshes.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_skin_weights_get(
    skin_cluster: Annotated[str, "Name of the skinCluster node"],
    offset: Annotated[int, "Starting vertex index (0-based)"] = 0,
    limit: Annotated[
        int | None,
        "Maximum vertices to return (default 100, use 0 for unlimited)",
    ] = 100,
) -> dict[str, Any]:
    """Get skin weights with pagination.

    Args:
        skin_cluster: Name of the skinCluster to query.
        offset: Starting vertex index.
        limit: Maximum vertices to return.

    Returns:
        Dictionary with skin_cluster, mesh, vertex_count, influences,
        vertices (with per-vertex weight maps), offset, count, and errors.
    """
    return skin_weights_get(skin_cluster=skin_cluster, offset=offset, limit=limit)


@mcp.tool(
    name="skin.weights.set",
    description="Set per-vertex skin weights with optional normalization. "
    "Accepts up to 1000 vertex entries per call.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_skin_weights_set(
    skin_cluster: Annotated[str, "Name of the skinCluster node"],
    weights: Annotated[
        list[dict[str, Any]],
        "List of {vertex_id: int, weights: {joint: weight}} entries",
    ],
    normalize: Annotated[bool, "Normalize weights after setting (default True)"] = True,
) -> dict[str, Any]:
    """Set skin weights on vertices.

    Args:
        skin_cluster: Name of the skinCluster to modify.
        weights: List of vertex weight entries.
        normalize: Whether to normalize weights.

    Returns:
        Dictionary with skin_cluster, set_count, and errors.
    """
    return skin_weights_set(
        skin_cluster=skin_cluster,
        weights=coerce_list(weights),
        normalize=normalize,
    )


@mcp.tool(
    name="skin.copy_weights",
    description="Copy skin weights from one mesh to another using surface and "
    "influence association methods.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_skin_copy_weights(
    source_mesh: Annotated[str, "Source mesh (must have a skinCluster)"],
    target_mesh: Annotated[str, "Target mesh (must have a skinCluster)"],
    surface_association: Annotated[
        Literal["closestPoint", "closestComponent", "rayCast"],
        "Surface matching method (default: closestPoint)",
    ] = "closestPoint",
    influence_association: Annotated[
        Literal["closestJoint", "closestBone", "oneToOne", "name", "label"],
        "Influence matching method (default: closestJoint)",
    ] = "closestJoint",
) -> dict[str, Any]:
    """Copy skin weights between meshes.

    Args:
        source_mesh: Source mesh with skin weights.
        target_mesh: Target mesh to receive weights.
        surface_association: Method for matching surface points.
        influence_association: Method for matching influences.

    Returns:
        Dictionary with source_mesh, target_mesh, skin cluster names,
        success, and errors.
    """
    return skin_copy_weights(
        source_mesh=source_mesh,
        target_mesh=target_mesh,
        surface_association=surface_association,
        influence_association=influence_association,
    )


# Register script tools
@mcp.tool(
    name="script.list",
    description="List available Python scripts from configured MAYA_MCP_SCRIPT_DIRS directories. "
    "Read-only, does not require Maya connection.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_script_list() -> dict[str, Any]:
    """List available scripts.

    Returns:
        Dictionary with scripts list, count, directories, and errors.
    """
    from maya_mcp.tools.scripts import script_list as _script_list

    return _script_list()


@mcp.tool(
    name="script.execute",
    description="Execute a Python script file in Maya from an allowed MAYA_MCP_SCRIPT_DIRS directory. "
    "The script is read server-side and sent to Maya. "
    "Optional args dict is injected as __args__ in the script namespace.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_script_execute(
    file_path: Annotated[str, "Absolute path to the .py script file"],
    args: Annotated[
        dict[str, Any] | None,
        "Optional arguments dict injected as __args__ in the script namespace",
    ] = None,
    timeout: Annotated[
        int | None,
        "Optional timeout override in seconds (default from MAYA_MCP_SCRIPT_TIMEOUT)",
    ] = None,
) -> dict[str, Any]:
    """Execute a Python script file in Maya.

    Args:
        file_path: Absolute path to the .py script.
        args: Optional arguments dict.
        timeout: Optional timeout override.

    Returns:
        Dictionary with success, script, output, and errors.
    """
    from maya_mcp.tools.scripts import script_execute as _script_execute

    return _script_execute(file_path=file_path, args=coerce_dict(args), timeout=timeout)


@mcp.tool(
    name="script.run",
    description="Execute raw Python or MEL code in Maya. "
    "REQUIRES MAYA_MCP_ENABLE_RAW_EXECUTION=true environment variable. "
    "Disabled by default for security.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def tool_script_run(
    code: Annotated[str, "Python or MEL code to execute"],
    language: Annotated[
        Literal["python", "mel"],
        "Code language (default: python)",
    ] = "python",
    timeout: Annotated[
        int | None,
        "Optional timeout override in seconds (default from MAYA_MCP_SCRIPT_TIMEOUT)",
    ] = None,
) -> dict[str, Any]:
    """Execute raw Python or MEL code in Maya.

    Args:
        code: Code to execute.
        language: Code language (python or mel).
        timeout: Optional timeout override.

    Returns:
        Dictionary with success, output, language, and errors.
    """
    from maya_mcp.tools.scripts import script_run as _script_run

    return _script_run(code=code, language=language, timeout=timeout)


# Register animation tools
@mcp.tool(
    name="animation.set_time",
    description="Set the current time (go to a specific frame).",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_animation_set_time(
    time: Annotated[float, "The frame number to set as current time"],
    update: Annotated[bool, "Whether to update the viewport (default True)"] = True,
) -> dict[str, Any]:
    """Set the current time.

    Args:
        time: The frame number to navigate to.
        update: Whether to update the viewport.

    Returns:
        Dictionary with time and errors.
    """
    return animation_set_time(time=time, update=update)


@mcp.tool(
    name="animation.get_time_range",
    description="Get playback range, animation range, and current time.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def tool_animation_get_time_range() -> dict[str, Any]:
    """Get playback range, animation range, and current time.

    Returns:
        Dictionary with current_time, min_time, max_time,
        animation_start, animation_end, fps, and errors.
    """
    return animation_get_time_range()


@mcp.tool(
    name="animation.set_time_range",
    description="Set the playback and animation range.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
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
) -> dict[str, Any]:
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


@mcp.tool(
    name="animation.set_keyframe",
    description="Set keyframe on attribute(s) at current or specified time.",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
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
) -> dict[str, Any]:
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


@mcp.tool(
    name="animation.get_keyframes",
    description="Query keyframes for attribute(s) on a node within optional time range.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
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
) -> dict[str, Any]:
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


@mcp.tool(
    name="animation.delete_keyframes",
    description="Delete keyframes in a time range for attribute(s).",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=False,
    ),
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
) -> dict[str, Any]:
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


def main() -> None:
    """Run the Maya MCP server.

    This is the main entry point for the server. It starts the FastMCP
    server with stdio transport (the default for MCP).
    """
    mcp.run()


if __name__ == "__main__":
    main()
