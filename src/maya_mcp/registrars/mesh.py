"""Registrar for mesh tools."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated, Any, Literal, cast

from mcp.types import ToolAnnotations

from maya_mcp.registrars._progress import merge_error_dicts, report_progress
from maya_mcp.tools.mesh import (
    MeshEvaluateOutput,
    MeshInfoOutput,
    MeshVerticesOutput,
    mesh_evaluate,
    mesh_info,
    mesh_vertices,
)
from maya_mcp.utils.coercion import coerce_list
from maya_mcp.utils.response_guard import guard_response_size

if TYPE_CHECKING:
    from fastmcp import Context, FastMCP
else:
    from importlib import import_module

    Context = import_module("fastmcp").Context


MESH_EVALUATE_DEFAULT_CHECKS: tuple[
    Literal["non_manifold", "lamina", "holes", "border"],
    ...,
] = ("non_manifold", "lamina", "holes", "border")


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


async def tool_mesh_evaluate(
    node: Annotated[str, "Name of the mesh node (transform or shape)"],
    checks: Annotated[
        list[Literal["non_manifold", "lamina", "holes", "border"]] | None,
        "Checks to perform (default: all)",
    ] = None,
    limit: Annotated[
        int | None,
        "Max components per check (default 500)",
    ] = 500,
    ctx: Context | None = None,
) -> MeshEvaluateOutput:
    """Analyze mesh topology.

    Args:
        node: Name of the mesh node.
        checks: List of checks to perform. Options:
            non_manifold, lamina, holes, border. Default: all.
        limit: Maximum components to return per check.
        ctx: FastMCP request context, used for progress notifications.

    Returns:
        Dictionary with topology analysis results and is_clean flag.
    """
    selected_checks = cast(
        "list[Literal['non_manifold', 'lamina', 'holes', 'border']] | None",
        coerce_list(checks),
    )
    if selected_checks is None:
        selected_checks = list(MESH_EVALUATE_DEFAULT_CHECKS)

    if not selected_checks:
        await report_progress(ctx, 0, 1, "Starting mesh topology analysis")
        result = await asyncio.to_thread(mesh_evaluate, node=node, checks=[], limit=limit)
        await report_progress(ctx, 1, 1, "Mesh topology analysis complete")
        return result

    total_checks = len(selected_checks)
    await report_progress(ctx, 0, total_checks, "Starting mesh topology analysis")

    aggregated: dict[str, Any] | None = None
    errors: dict[str, Any] | None = None

    field_map: dict[str, tuple[str, str]] = {
        "non_manifold": ("non_manifold_edges", "non_manifold_count"),
        "lamina": ("lamina_faces", "lamina_count"),
        "holes": ("holes", "hole_count"),
        "border": ("border_edges", "border_count"),
    }

    for index, check in enumerate(selected_checks, start=1):
        partial = await asyncio.to_thread(mesh_evaluate, node=node, checks=[check], limit=limit)
        partial_data = cast("dict[str, Any]", partial)

        if aggregated is None:
            if not partial["exists"] or not partial["is_mesh"]:
                await report_progress(
                    ctx,
                    total_checks,
                    total_checks,
                    "Mesh topology analysis finished with an error",
                )
                return partial

            aggregated = {
                "node": partial["node"],
                "exists": partial["exists"],
                "is_mesh": partial["is_mesh"],
                "is_clean": True,
                "errors": None,
            }
            if "shape" in partial:
                aggregated["shape"] = partial["shape"]

        errors = merge_error_dicts(errors, partial.get("errors"))

        list_field, count_field = field_map[check]
        if list_field in partial_data:
            aggregated[list_field] = partial_data[list_field]
        if count_field in partial_data:
            aggregated[count_field] = partial_data[count_field]
            if partial_data[count_field] > 0:
                aggregated["is_clean"] = False

        if partial_data.get("truncated"):
            aggregated["truncated"] = True
        if "total_count" in partial_data:
            aggregated["total_count"] = partial_data["total_count"]
        if "_size_warning" in partial_data:
            aggregated["_size_warning"] = partial_data["_size_warning"]
        if "_original_size" in partial_data:
            aggregated["_original_size"] = partial_data["_original_size"]
        if "_truncated_size" in partial_data:
            aggregated["_truncated_size"] = partial_data["_truncated_size"]

        await report_progress(
            ctx,
            index,
            total_checks,
            f"Completed {check.replace('_', ' ')} topology check ({index}/{total_checks})",
        )

    assert aggregated is not None
    aggregated["errors"] = errors

    for list_key in ("non_manifold_edges", "lamina_faces", "holes", "border_edges"):
        if list_key in aggregated:
            aggregated = guard_response_size(aggregated, list_key=list_key)

    return cast("MeshEvaluateOutput", aggregated)


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
