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

from maya_mcp.tools.connection import maya_connect, maya_disconnect
from maya_mcp.tools.health import health_check
from maya_mcp.tools.nodes import nodes_list
from maya_mcp.tools.scene import scene_info
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
- nodes.list: List nodes by type or pattern
- selection.get: Get current selection
- selection.set: Set selection (replace, add, or deselect)
- selection.clear: Clear the selection (deselect all)

Before using Maya tools, ensure Maya is running with commandPort enabled:
    import maya.cmds as cmds
    cmds.commandPort(name=":7001", sourceType="python", echoOutput=True)
""",
)


# Register health tool
@mcp.tool(
    name="health.check",
    description="Check the health status of the Maya connection",
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
)
def tool_scene_info() -> dict[str, Any]:
    """Get current scene information.

    Returns file path, modification status, FPS, frame range, and up axis.
    """
    return scene_info()


# Register node tools
@mcp.tool(
    name="nodes.list",
    description="List nodes in the Maya scene, optionally filtered by type",
)
def tool_nodes_list(
    node_type: Annotated[
        str | None,
        "Filter by node type (e.g., 'transform', 'mesh')",
    ] = None,
    pattern: Annotated[str, "Name pattern filter (supports wildcards)"] = "*",
    long_names: Annotated[bool, "Return full DAG paths"] = False,
) -> dict[str, Any]:
    """List Maya nodes.

    Args:
        node_type: Filter by node type (optional).
        pattern: Name pattern with wildcards.
        long_names: Return full DAG paths if True.

    Returns:
        Node list with nodes array and count.
    """
    return nodes_list(node_type=node_type, pattern=pattern, long_names=long_names)


# Register selection tools
@mcp.tool(
    name="selection.get",
    description="Get the current selection in Maya",
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
