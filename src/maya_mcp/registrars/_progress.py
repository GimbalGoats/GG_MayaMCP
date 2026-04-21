"""Shared progress helpers for registrar-level async tool wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastmcp import Context
else:
    from importlib import import_module

    Context = import_module("fastmcp").Context


async def report_progress(
    ctx: Context | None,
    progress: float,
    total: float | None,
    message: str,
) -> None:
    """Send a progress update when a FastMCP context is available."""
    if ctx is None:
        return
    await ctx.report_progress(progress=progress, total=total, message=message)


def merge_error_dicts(
    existing: dict[str, Any] | None,
    incoming: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Merge tool error dictionaries while preserving ``None`` for no errors."""
    if not existing and not incoming:
        return None

    merged: dict[str, Any] = {}
    if existing:
        merged.update(existing)
    if incoming:
        merged.update(incoming)
    return merged


def requested_skin_vertex_count(
    vertex_count: int,
    offset: int,
    limit: int | None,
) -> int:
    """Return how many vertices a skin weight query is expected to fetch."""
    remaining = max(vertex_count - offset, 0)
    if limit is None or limit == 0:
        return remaining
    return min(limit, remaining)
