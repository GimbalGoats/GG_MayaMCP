"""Registrar for mesh tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal

from mcp.types import ToolAnnotations

from maya_mcp.tools.mesh import (
    MeshEvaluateOutput,
    MeshInfoOutput,
    MeshVerticesOutput,
    mesh_evaluate,
    mesh_info,
    mesh_vertices,
)
from maya_mcp.utils.coercion import coerce_list

if TYPE_CHECKING:
    from fastmcp import FastMCP


def tool_mesh_info(
    node: Annotated[str, "Name of the mesh node (transform or shape)"],
) -> MeshInfoOutput:
    """Get mesh statistics.

    Args:
        node: Name of the mesh node (transform or shape).

    Returns:
        Dictionary with vertex_count, face_count, edge_count, bounding_box,
        uv_sets, has_uvs, and errors.
    """
    return mesh_info(node=node)


def tool_mesh_vertices(
    node: Annotated[str, "Name of the mesh node (transform or shape)"],
    offset: Annotated[int, "Starting vertex index (0-based)"] = 0,
    limit: Annotated[
        int | None,
        "Maximum vertices to return (default 1000, use 0 for unlimited)",
    ] = 1000,
) -> MeshVerticesOutput:
    """Query vertex positions from a mesh.

    Args:
        node: Name of the mesh node.
        offset: Starting vertex index.
        limit: Maximum vertices to return.

    Returns:
        Dictionary with vertices list, vertex_count, offset, count, and errors.
    """
    return mesh_vertices(node=node, offset=offset, limit=limit)


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
) -> MeshEvaluateOutput:
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


def register_mesh_tools(mcp: FastMCP) -> None:
    """Register mesh tools."""
    mcp.tool(
        name="mesh.info",
        description="Get mesh statistics: vertex/face/edge counts, bounding box, UV status",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_mesh_info)

    mcp.tool(
        name="mesh.vertices",
        description="Query vertex positions from a mesh with offset/limit pagination. "
        "Returns vertex positions as [x, y, z] arrays.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_mesh_vertices)

    mcp.tool(
        name="mesh.evaluate",
        description="Analyze mesh topology for issues: non-manifold edges, lamina faces, "
        "holes, and border edges.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_mesh_evaluate)
