"""Registrar for skinning tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Literal

from mcp.types import ToolAnnotations

from maya_mcp.tools.skin import (
    SkinBindOutput,
    SkinCopyWeightsOutput,
    SkinInfluencesOutput,
    SkinUnbindOutput,
    SkinWeightsGetOutput,
    SkinWeightsSetOutput,
    skin_bind,
    skin_copy_weights,
    skin_influences,
    skin_unbind,
    skin_weights_get,
    skin_weights_set,
)
from maya_mcp.utils.coercion import coerce_list

if TYPE_CHECKING:
    from fastmcp import FastMCP


def tool_skin_bind(
    mesh: Annotated[str, "Name of the mesh to bind"],
    joints: Annotated[list[str], "List of joint names to use as influences"],
    max_influences: Annotated[int, "Maximum influences per vertex (default 4)"] = 4,
    bind_method: Annotated[
        Literal["closestDistance", "heatMap", "geodesicVoxel"],
        "Binding algorithm: closestDistance (default), heatMap, or geodesicVoxel",
    ] = "closestDistance",
) -> SkinBindOutput:
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


def tool_skin_unbind(
    mesh: Annotated[str, "Name of the mesh to unbind"],
) -> SkinUnbindOutput:
    """Unbind skin cluster from mesh.

    Args:
        mesh: Name of the mesh to unbind.

    Returns:
        Dictionary with mesh, unbound, skin_cluster, and errors.
    """
    return skin_unbind(mesh=mesh)


def tool_skin_influences(
    skin_cluster: Annotated[str, "Name of the skinCluster node"],
) -> SkinInfluencesOutput:
    """List influences on a skin cluster.

    Args:
        skin_cluster: Name of the skinCluster to query.

    Returns:
        Dictionary with skin_cluster, influences (name and index), count, and errors.
    """
    return skin_influences(skin_cluster=skin_cluster)


def tool_skin_weights_get(
    skin_cluster: Annotated[str, "Name of the skinCluster node"],
    offset: Annotated[int, "Starting vertex index (0-based)"] = 0,
    limit: Annotated[
        int | None,
        "Maximum vertices to return (default 100, use 0 for unlimited)",
    ] = 100,
) -> SkinWeightsGetOutput:
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


def tool_skin_weights_set(
    skin_cluster: Annotated[str, "Name of the skinCluster node"],
    weights: Annotated[
        list[dict[str, Any]],
        "List of {vertex_id: int, weights: {joint: weight}} entries",
    ],
    normalize: Annotated[bool, "Normalize weights after setting (default True)"] = True,
) -> SkinWeightsSetOutput:
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
) -> SkinCopyWeightsOutput:
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


def register_skin_tools(mcp: FastMCP) -> None:
    """Register skinning tools."""
    mcp.tool(
        name="skin.bind",
        description="Bind a mesh to a skeleton with influence options. "
        "Creates a skinCluster with configurable bind method and max influences.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_skin_bind)

    mcp.tool(
        name="skin.unbind",
        description="Detach a skin cluster from a mesh, removing skin deformation.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_skin_unbind)

    mcp.tool(
        name="skin.influences",
        description="List influences (joints) on a skin cluster with index mapping.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_skin_influences)

    mcp.tool(
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
    )(tool_skin_weights_get)

    mcp.tool(
        name="skin.weights.set",
        description="Set per-vertex skin weights with optional normalization. "
        "Accepts up to 1000 vertex entries per call.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_skin_weights_set)

    mcp.tool(
        name="skin.copy_weights",
        description="Copy skin weights from one mesh to another using surface and "
        "influence association methods.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_skin_copy_weights)
