"""Viewport capture tools for Maya MCP.

This module provides a read-only viewport capture tool that uses Maya playblast
to write a temporary image file and returns it as inline MCP image content.
"""

from __future__ import annotations

import contextlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Literal

from fastmcp.utilities.types import Image

from maya_mcp.errors import MayaCommandError, ValidationError
from maya_mcp.transport import get_client
from maya_mcp.utils.parsing import parse_json_response
from maya_mcp.utils.validation import FORBIDDEN_NODE_CHARS

ViewportFormat = Literal["jpeg", "png"]

_MIN_CAPTURE_DIMENSION = 64
_MAX_CAPTURE_DIMENSION = 4096
_MAX_CAPTURE_BYTES = 10 * 1024 * 1024  # 10 MB safety cap for inline images
_FORMAT_TO_CAPTURE_SETTINGS: dict[ViewportFormat, tuple[str, Literal["jpg", "png"]]] = {
    "jpeg": ("jpg", "jpg"),
    "png": ("png", "png"),
}


def viewport_capture(
    format: ViewportFormat = "jpeg",
    width: int = 1024,
    height: int = 576,
    quality: int = 85,
    offscreen: bool = False,
    show_ornaments: bool = True,
    panel: str | None = None,
    frame: float | None = None,
) -> Image:
    """Capture the Maya viewport as an inline MCP image.

    The Maya command executes playblast server-side and returns only a compact
    JSON payload over commandPort. The image file is then read in the MCP
    server process and returned as ``fastmcp.utilities.types.Image``.

    Args:
        format: Image format, either ``"jpeg"`` or ``"png"``.
        width: Capture width in pixels.
        height: Capture height in pixels.
        quality: JPEG quality in the range 1-100. Ignored for PNG.
        offscreen: Whether to request offscreen capture.
        show_ornaments: Whether to show viewport ornaments/gizmos.
        panel: Optional preferred model panel name.
        frame: Optional frame to capture. Defaults to current time when omitted.

    Returns:
        ``Image`` instance with inline bytes for FastMCP conversion to
        ``ImageContent``.

    Raises:
        ValidationError: If tool inputs are invalid.
        MayaCommandError: If capture or file read fails.
    """
    _validate_capture_inputs(
        format=format,
        width=width,
        height=height,
        quality=quality,
        panel=panel,
    )

    client = get_client()
    extension, compression = _FORMAT_TO_CAPTURE_SETTINGS[format]

    temp_dir = Path(tempfile.mkdtemp(prefix="maya_mcp_viewport_"))
    output_path = temp_dir / f"capture.{extension}"

    try:
        command = _build_capture_command(
            output_path=output_path,
            compression=compression,
            width=width,
            height=height,
            quality=quality,
            offscreen=offscreen,
            show_ornaments=show_ornaments,
            panel=panel,
            frame=frame,
        )

        response = client.execute(command)
        payload = parse_json_response(response)

        success = bool(payload.get("success"))
        if not success:
            error_message = str(payload.get("error") or "Viewport capture failed in Maya.")
            _raise_capture_error(error_message=error_message)

        maya_path = str(payload.get("path") or "")
        if not maya_path:
            _raise_capture_error(
                error_message="Maya did not return an output path.",
                maya_error="missing output path",
            )

        expected_path = output_path.resolve()
        actual_path = Path(maya_path).resolve()
        if actual_path != expected_path:
            _raise_capture_error(
                error_message="Unexpected output path from Maya.",
                maya_error="unexpected output path",
            )

        if not expected_path.is_file():
            _raise_capture_error(
                error_message="Capture file was not created.",
                maya_error="missing capture file",
            )

        try:
            image_bytes = expected_path.read_bytes()
        except OSError as exc:
            _raise_capture_error(
                error_message="Unable to read capture file.",
                maya_error=str(exc),
                cause=exc,
            )

        if not image_bytes:
            _raise_capture_error(
                error_message="Capture file is empty.",
                maya_error="empty capture file",
            )

        if len(image_bytes) > _MAX_CAPTURE_BYTES:
            raise ValidationError(
                message=(
                    f"Captured image exceeds maximum allowed size ({_MAX_CAPTURE_BYTES} bytes)."
                ),
                field_name="capture_bytes",
                value=str(len(image_bytes)),
                constraint=f"<= {_MAX_CAPTURE_BYTES}",
            )

        return Image(data=image_bytes, format=format)
    finally:
        with contextlib.suppress(OSError):
            shutil.rmtree(temp_dir, ignore_errors=True)


def _raise_capture_error(
    *,
    error_message: str,
    maya_error: str | None = None,
    cause: Exception | None = None,
) -> None:
    """Raise a standardized viewport capture command error."""
    error = MayaCommandError(
        message=f"Viewport capture failed: {error_message}",
        maya_error=maya_error or error_message,
    )
    if cause is not None:
        raise error from cause
    raise error


def _validate_capture_inputs(
    *,
    format: str,
    width: int,
    height: int,
    quality: int,
    panel: str | None,
) -> None:
    """Validate viewport capture inputs."""
    if format not in ("jpeg", "png"):
        raise ValidationError(
            message="Unsupported format. Allowed: 'jpeg', 'png'.",
            field_name="format",
            value=format,
            constraint="jpeg|png",
        )

    if not (_MIN_CAPTURE_DIMENSION <= width <= _MAX_CAPTURE_DIMENSION):
        raise ValidationError(
            message=(
                f"Width must be between {_MIN_CAPTURE_DIMENSION} and {_MAX_CAPTURE_DIMENSION}."
            ),
            field_name="width",
            value=str(width),
            constraint=f"{_MIN_CAPTURE_DIMENSION}..{_MAX_CAPTURE_DIMENSION}",
        )

    if not (_MIN_CAPTURE_DIMENSION <= height <= _MAX_CAPTURE_DIMENSION):
        raise ValidationError(
            message=(
                f"Height must be between {_MIN_CAPTURE_DIMENSION} and {_MAX_CAPTURE_DIMENSION}."
            ),
            field_name="height",
            value=str(height),
            constraint=f"{_MIN_CAPTURE_DIMENSION}..{_MAX_CAPTURE_DIMENSION}",
        )

    if not (1 <= quality <= 100):
        raise ValidationError(
            message="Quality must be between 1 and 100.",
            field_name="quality",
            value=str(quality),
            constraint="1..100",
        )

    if panel is None:
        return

    panel_name = panel.strip()
    if not panel_name:
        raise ValidationError(
            message="Panel name must not be empty.",
            field_name="panel",
            value=panel,
            constraint="non-empty string",
        )

    if any(char in panel_name for char in FORBIDDEN_NODE_CHARS):
        raise ValidationError(
            message="Panel name contains forbidden characters.",
            field_name="panel",
            value=panel_name,
            constraint="safe panel identifier",
        )

    if not panel_name.replace("_", "").isalnum():
        raise ValidationError(
            message="Panel name must be alphanumeric (underscores allowed).",
            field_name="panel",
            value=panel_name,
            constraint="^[A-Za-z0-9_]+$",
        )


def _build_capture_command(
    *,
    output_path: Path,
    compression: Literal["jpg", "png"],
    width: int,
    height: int,
    quality: int,
    offscreen: bool,
    show_ornaments: bool,
    panel: str | None,
    frame: float | None,
) -> str:
    """Build the Maya Python command used for viewport capture."""
    safe_path = output_path.as_posix()
    panel_literal = "None" if panel is None else json.dumps(panel)
    frame_literal = "None" if frame is None else repr(frame)

    return f"""
import json
import os
import maya.cmds as cmds

output_path = {json.dumps(safe_path)}
preferred_panel = {panel_literal}
requested_frame = {frame_literal}
result = {{"success": False, "path": None, "metadata": {{}}, "error": None}}

def _pick_model_panel(preferred):
    panel_types = set(cmds.getPanel(type="modelPanel") or [])
    if preferred and preferred in panel_types:
        return preferred

    focused = cmds.getPanel(withFocus=True)
    if focused and focused in panel_types:
        return focused

    visible = cmds.getPanel(visiblePanels=True) or []
    for panel_name in visible:
        if panel_name in panel_types:
            return panel_name

    if panel_types:
        return sorted(panel_types)[0]
    return None

try:
    panel_name = _pick_model_panel(preferred_panel)
    if not panel_name:
        raise RuntimeError("No modelPanel available for viewport capture.")

    capture_frame = float(cmds.currentTime(query=True)) if requested_frame is None else float(requested_frame)

    blast_kwargs = {{
        "format": "image",
        "completeFilename": output_path,
        "forceOverwrite": True,
        "viewer": False,
        "offScreen": {offscreen!r},
        "showOrnaments": {show_ornaments!r},
        "compression": {json.dumps(compression)},
        "widthHeight": [{width}, {height}],
        "percent": 100,
        "frame": [capture_frame],
        "editorPanelName": panel_name,
    }}

    if {compression == "jpg"}:
        blast_kwargs["quality"] = {quality}

    _ = cmds.playblast(**blast_kwargs)

    if not os.path.isfile(output_path):
        raise RuntimeError("Playblast did not produce an output file.")

    result["success"] = True
    result["path"] = output_path
    result["metadata"] = {{
        "panel": panel_name,
        "frame": capture_frame,
        "width": {width},
        "height": {height},
        "compression": {json.dumps(compression)},
        "size_bytes": os.path.getsize(output_path),
    }}
except Exception as exc:
    result["error"] = str(exc)

print(json.dumps(result))
"""
