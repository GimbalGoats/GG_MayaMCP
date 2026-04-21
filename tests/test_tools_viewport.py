"""Tests for viewport capture tools."""

from __future__ import annotations

import asyncio
import base64
import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastmcp.utilities.types import Image

from maya_mcp.errors import MayaCommandError, ValidationError
from maya_mcp.tools.viewport import viewport_capture


def _extract_output_path(command: str) -> Path:
    """Extract the temporary output path from the generated Maya command."""
    match = re.search(r'output_path = "([^"]+)"', command)
    if match is None:
        raise AssertionError("output_path was not embedded in command")
    return Path(match.group(1))


class TestViewportCapture:
    """Tests for viewport.capture behavior."""

    def test_capture_jpeg_success(self) -> None:
        """Successful capture returns FastMCP Image with JPEG mime type."""
        mock_client = MagicMock()
        expected_bytes = b"fake-jpeg-bytes"

        def execute_side_effect(command: str) -> str:
            output_path = _extract_output_path(command)
            output_path.write_bytes(expected_bytes)
            return json.dumps(
                {
                    "success": True,
                    "path": output_path.as_posix(),
                    "metadata": {
                        "panel": "modelPanel4",
                        "frame": 12.0,
                        "width": 640,
                        "height": 360,
                        "compression": "jpg",
                        "size_bytes": len(expected_bytes),
                    },
                    "error": None,
                }
            )

        mock_client.execute.side_effect = execute_side_effect

        with patch("maya_mcp.tools.viewport.get_client", return_value=mock_client):
            result = viewport_capture(format="jpeg", width=640, height=360, quality=90, frame=12.0)

        assert isinstance(result, Image)
        image_content = result.to_image_content()
        assert image_content.mimeType == "image/jpeg"
        assert base64.b64decode(image_content.data) == expected_bytes

    def test_capture_png_success(self) -> None:
        """PNG capture uses image/png MIME type."""
        mock_client = MagicMock()
        expected_bytes = b"fake-png-bytes"

        def execute_side_effect(command: str) -> str:
            output_path = _extract_output_path(command)
            output_path.write_bytes(expected_bytes)
            return json.dumps(
                {
                    "success": True,
                    "path": output_path.as_posix(),
                    "metadata": {},
                    "error": None,
                }
            )

        mock_client.execute.side_effect = execute_side_effect

        with patch("maya_mcp.tools.viewport.get_client", return_value=mock_client):
            result = viewport_capture(format="png", width=800, height=450, quality=50)

        image_content = result.to_image_content()
        assert image_content.mimeType == "image/png"
        assert base64.b64decode(image_content.data) == expected_bytes

    def test_rejects_invalid_format(self) -> None:
        """Invalid format is rejected."""
        with pytest.raises(ValidationError, match="Unsupported format"):
            viewport_capture(format="bmp")  # type: ignore[arg-type]

    def test_rejects_invalid_dimensions(self) -> None:
        """Out-of-range dimensions are rejected."""
        with pytest.raises(ValidationError, match="Width must be between"):
            viewport_capture(width=16)
        with pytest.raises(ValidationError, match="Height must be between"):
            viewport_capture(height=99999)

    def test_rejects_invalid_quality(self) -> None:
        """Out-of-range quality is rejected."""
        with pytest.raises(ValidationError, match="Quality must be between 1 and 100"):
            viewport_capture(quality=0)

    def test_rejects_unsafe_panel_name(self) -> None:
        """Unsafe panel names are rejected."""
        with pytest.raises(ValidationError, match="forbidden characters"):
            viewport_capture(panel="modelPanel4;bad")

    def test_maya_failure_raises_command_error(self) -> None:
        """Maya-side capture failure raises MayaCommandError."""
        mock_client = MagicMock()
        mock_client.execute.return_value = json.dumps(
            {"success": False, "path": None, "metadata": {}, "error": "No model panel available"}
        )

        with (
            patch("maya_mcp.tools.viewport.get_client", return_value=mock_client),
            pytest.raises(MayaCommandError, match="No model panel available"),
        ):
            viewport_capture()

    def test_cleanup_runs_on_read_error(self) -> None:
        """Temporary directory is removed even when file read fails."""
        mock_client = MagicMock()
        created_path: Path | None = None

        def execute_side_effect(command: str) -> str:
            nonlocal created_path
            created_path = _extract_output_path(command)
            created_path.write_bytes(b"unreadable")
            return json.dumps(
                {
                    "success": True,
                    "path": created_path.as_posix(),
                    "metadata": {},
                    "error": None,
                }
            )

        def read_bytes_side_effect(self: Path) -> bytes:
            raise OSError("simulated read failure")

        mock_client.execute.side_effect = execute_side_effect

        with (
            patch("maya_mcp.tools.viewport.get_client", return_value=mock_client),
            patch(
                "maya_mcp.tools.viewport.Path.read_bytes",
                autospec=True,
                side_effect=read_bytes_side_effect,
            ),
            pytest.raises(MayaCommandError, match="Unable to read capture file"),
        ):
            viewport_capture()

        assert created_path is not None
        assert not created_path.parent.exists()

    def test_defaults_match_viewport_like_capture_settings(self) -> None:
        """Default command prefers viewport-like settings."""
        mock_client = MagicMock()

        def execute_side_effect(command: str) -> str:
            output_path = _extract_output_path(command)
            output_path.write_bytes(b"default-capture")
            assert '"offScreen": False' in command
            assert '"showOrnaments": True' in command
            return json.dumps(
                {
                    "success": True,
                    "path": output_path.as_posix(),
                    "metadata": {},
                    "error": None,
                }
            )

        mock_client.execute.side_effect = execute_side_effect

        with patch("maya_mcp.tools.viewport.get_client", return_value=mock_client):
            result = viewport_capture()

        assert isinstance(result, Image)


class TestViewportServerRegistration:
    """Smoke tests for viewport.capture server registration."""

    def test_viewport_capture_registered_with_read_only_annotations(self) -> None:
        """Tool exists with expected annotation hints."""
        from maya_mcp.server import mcp

        tool = asyncio.run(mcp.get_tool("viewport.capture"))
        assert tool is not None
        annotations = tool.annotations

        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False
        assert annotations.idempotentHint is True
        assert annotations.openWorldHint is False

    def test_viewport_capture_exposes_structured_output_schema(self) -> None:
        """Viewport capture publishes metadata schema alongside image content."""
        from maya_mcp.server import mcp

        tool = asyncio.run(mcp.get_tool("viewport.capture"))
        assert tool is not None

        schema = tool.to_mcp_tool().outputSchema
        assert schema is not None
        assert schema["type"] == "object"
        properties = schema["properties"]

        for field in ("format", "mime_type", "width", "height", "frame", "panel", "size_bytes"):
            assert field in properties
