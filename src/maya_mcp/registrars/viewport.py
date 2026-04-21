"""Registrar for viewport tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastmcp.tools import ToolResult
from mcp.types import ToolAnnotations
from pydantic import TypeAdapter

from maya_mcp.tools.viewport import (
    ViewportCaptureOutput,
    ViewportFormat,
    _capture_viewport_image,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP


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
) -> ToolResult:
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
        Tool result containing inline image content plus structured capture metadata.
    """
    image, metadata = _capture_viewport_image(
        format=format,
        width=width,
        height=height,
        quality=quality,
        offscreen=offscreen,
        show_ornaments=show_ornaments,
        panel=panel,
        frame=frame,
    )
    return ToolResult(content=image, structured_content=metadata)


def register_viewport_tools(mcp: FastMCP) -> None:
    """Register viewport tools."""
    mcp.tool(
        name="viewport.capture",
        description="Capture a single viewport frame as inline image content using Maya playblast. "
        "Read-only: does not modify scene data.",
        output_schema=TypeAdapter(ViewportCaptureOutput).json_schema(mode="serialization"),
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_viewport_capture)
