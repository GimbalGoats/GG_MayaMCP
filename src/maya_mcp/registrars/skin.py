"""Registrar for skinning tools."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated, Any, Literal, cast

from mcp.types import ToolAnnotations

from maya_mcp.registrars._progress import (
    merge_error_dicts,
    report_progress,
    requested_skin_vertex_count,
)
from maya_mcp.tools.skin import (
    MAX_WEIGHT_SET_ENTRIES,
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
from maya_mcp.utils.response_guard import guard_response_size

if TYPE_CHECKING:
    from fastmcp import Context, FastMCP
else:
    from importlib import import_module

    Context = import_module("fastmcp").Context


SKIN_WEIGHTS_GET_PROGRESS_CHUNK_SIZE = 50
SKIN_WEIGHTS_SET_PROGRESS_BATCH_SIZE = 100


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


async def tool_skin_weights_get(
    skin_cluster: Annotated[str, "Name of the skinCluster node"],
    offset: Annotated[int, "Starting vertex index (0-based)"] = 0,
    limit: Annotated[
        int | None,
        "Maximum vertices to return (default 100, use 0 for unlimited)",
    ] = 100,
    ctx: Context | None = None,
) -> SkinWeightsGetOutput:
    """Get skin weights with pagination.

    Args:
        skin_cluster: Name of the skinCluster to query.
        offset: Starting vertex index.
        limit: Maximum vertices to return.
        ctx: FastMCP request context, used for progress notifications.

    Returns:
        Dictionary with skin_cluster, mesh, vertex_count, influences,
        vertices (with per-vertex weight maps), offset, count, and errors.
    """
    await report_progress(ctx, 0, None, "Fetching skin weight data")

    if limit is None or limit == 0:
        result = await asyncio.to_thread(
            skin_weights_get,
            skin_cluster=skin_cluster,
            offset=offset,
            limit=limit,
        )
        await report_progress(ctx, 1, 1, "Fetched skin weight data")
        return result

    first_limit = SKIN_WEIGHTS_GET_PROGRESS_CHUNK_SIZE
    if limit is not None and limit > 0:
        first_limit = min(first_limit, limit)

    first_chunk = await asyncio.to_thread(
        skin_weights_get,
        skin_cluster=skin_cluster,
        offset=offset,
        limit=first_limit,
    )
    if first_chunk.get("errors"):
        return first_chunk

    requested_total = requested_skin_vertex_count(first_chunk["vertex_count"], offset, limit)
    vertices = list(first_chunk["vertices"])
    errors = merge_error_dicts(None, first_chunk.get("errors"))

    aggregated: dict[str, Any] = {
        "skin_cluster": first_chunk["skin_cluster"],
        "mesh": first_chunk["mesh"],
        "vertex_count": first_chunk["vertex_count"],
        "influence_count": first_chunk["influence_count"],
        "influences": first_chunk["influences"],
        "vertices": vertices,
        "offset": offset,
        "count": len(vertices),
        "errors": errors,
    }
    if "geometry_type" in first_chunk:
        aggregated["geometry_type"] = first_chunk["geometry_type"]

    await report_progress(
        ctx,
        len(vertices),
        requested_total if requested_total > 0 else None,
        (
            f"Fetched {len(vertices)}/{requested_total} skin weight vertices"
            if requested_total > 0
            else "Fetched skin weight data"
        ),
    )

    while len(vertices) < requested_total:
        remaining = requested_total - len(vertices)
        chunk_limit = min(SKIN_WEIGHTS_GET_PROGRESS_CHUNK_SIZE, remaining)
        chunk_offset = offset + len(vertices)

        chunk = await asyncio.to_thread(
            skin_weights_get,
            skin_cluster=skin_cluster,
            offset=chunk_offset,
            limit=chunk_limit,
        )

        errors = merge_error_dicts(errors, chunk.get("errors"))
        if chunk.get("errors"):
            break

        chunk_vertices = chunk.get("vertices", [])
        vertices.extend(chunk_vertices)
        aggregated["count"] = len(vertices)

        await report_progress(
            ctx,
            len(vertices),
            requested_total,
            f"Fetched {len(vertices)}/{requested_total} skin weight vertices",
        )

        if chunk.get("count", len(chunk_vertices)) == 0:
            break

    aggregated["vertices"] = vertices
    aggregated["count"] = len(vertices)
    aggregated["errors"] = errors

    if limit is not None and limit > 0 and first_chunk["vertex_count"] > offset + limit:
        aggregated["truncated"] = True

    aggregated = guard_response_size(aggregated, list_key="vertices")
    return cast("SkinWeightsGetOutput", aggregated)


async def tool_skin_weights_set(
    skin_cluster: Annotated[str, "Name of the skinCluster node"],
    weights: Annotated[
        list[dict[str, Any]],
        "List of {vertex_id: int, weights: {joint: weight}} entries",
    ],
    normalize: Annotated[bool, "Normalize weights after setting (default True)"] = True,
    ctx: Context | None = None,
) -> SkinWeightsSetOutput:
    """Set skin weights on vertices.

    Args:
        skin_cluster: Name of the skinCluster to modify.
        weights: List of vertex weight entries.
        normalize: Whether to normalize weights.
        ctx: FastMCP request context, used for progress notifications.

    Returns:
        Dictionary with skin_cluster, set_count, and errors.
    """
    weight_entries = cast("list[dict[str, Any]]", coerce_list(weights))
    if len(weight_entries) > MAX_WEIGHT_SET_ENTRIES:
        raise ValueError(
            f"Too many weight entries: {len(weight_entries)}. "
            f"Maximum is {MAX_WEIGHT_SET_ENTRIES} per call."
        )

    if len(weight_entries) <= SKIN_WEIGHTS_SET_PROGRESS_BATCH_SIZE:
        await report_progress(ctx, 0, len(weight_entries), "Applying skin weight edits")
        result = await asyncio.to_thread(
            skin_weights_set,
            skin_cluster=skin_cluster,
            weights=weight_entries,
            normalize=normalize,
        )
        await report_progress(
            ctx,
            len(weight_entries),
            len(weight_entries),
            "Applied skin weight edits",
        )
        return result

    total_entries = len(weight_entries)
    await report_progress(ctx, 0, total_entries, "Applying skin weight edits")

    set_count = 0
    errors: dict[str, Any] | None = None

    for start in range(0, total_entries, SKIN_WEIGHTS_SET_PROGRESS_BATCH_SIZE):
        batch = weight_entries[start : start + SKIN_WEIGHTS_SET_PROGRESS_BATCH_SIZE]
        partial = await asyncio.to_thread(
            skin_weights_set,
            skin_cluster=skin_cluster,
            weights=batch,
            normalize=normalize,
        )

        if start == 0 and partial.get("errors") and partial["set_count"] == 0:
            return partial

        set_count += partial["set_count"]
        errors = merge_error_dicts(errors, partial.get("errors"))

        processed = min(start + len(batch), total_entries)
        await report_progress(
            ctx,
            processed,
            total_entries,
            f"Applied {processed}/{total_entries} skin weight entries",
        )

        if partial.get("errors") and partial["set_count"] == 0:
            break

    return {
        "skin_cluster": skin_cluster,
        "set_count": set_count,
        "errors": errors,
    }


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
