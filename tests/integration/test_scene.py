"""Integration tests for scene.info tool.

These tests require a running Maya instance with commandPort enabled.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from maya_mcp.transport.commandport import CommandPortClient


pytestmark = pytest.mark.integration


class TestSceneInfoIntegration:
    """Integration tests for the scene.info tool."""

    def test_scene_info_returns_required_fields(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """scene.info returns all required fields."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_info

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = scene_info()

            # Check all required fields are present
            assert "file_path" in result
            assert "modified" in result
            assert "fps" in result
            assert "frame_range" in result
            assert "up_axis" in result
        finally:
            transport_module._client = original_client

    def test_scene_info_untitled_scene(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """scene.info returns None file_path for untitled scene."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_info

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = scene_info()

            # New scene should be untitled (empty path)
            assert result["file_path"] is None or result["file_path"] == ""
        finally:
            transport_module._client = original_client

    def test_scene_info_modified_flag(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """scene.info modified flag reflects scene state."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_info

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Clean scene should not be modified
            result = scene_info()
            assert result["modified"] is False

            # Create an object to modify the scene
            maya_client.execute("import maya.cmds as cmds; cmds.polyCube()")

            result = scene_info()
            assert result["modified"] is True
        finally:
            transport_module._client = original_client

    def test_scene_info_fps_is_positive(self, maya_client: CommandPortClient) -> None:
        """scene.info fps is a positive number."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_info

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = scene_info()

            assert isinstance(result["fps"], float | int)
            assert result["fps"] > 0
        finally:
            transport_module._client = original_client

    def test_scene_info_frame_range_format(self, maya_client: CommandPortClient) -> None:
        """scene.info frame_range is [start, end] tuple."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_info

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = scene_info()

            assert isinstance(result["frame_range"], list)
            assert len(result["frame_range"]) == 2
            assert isinstance(result["frame_range"][0], float | int)
            assert isinstance(result["frame_range"][1], float | int)
            # End should be >= start
            assert result["frame_range"][1] >= result["frame_range"][0]
        finally:
            transport_module._client = original_client

    def test_scene_info_up_axis_valid(self, maya_client: CommandPortClient) -> None:
        """scene.info up_axis is 'y' or 'z'."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_info

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = scene_info()

            assert result["up_axis"] in ("y", "z")
        finally:
            transport_module._client = original_client

    def test_scene_info_custom_frame_range(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """scene.info returns correct custom frame range."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_info

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Set custom frame range
            maya_client.execute(
                "import maya.cmds as cmds; cmds.playbackOptions(minTime=10, maxTime=100)"
            )

            result = scene_info()

            assert result["frame_range"][0] == 10.0
            assert result["frame_range"][1] == 100.0
        finally:
            transport_module._client = original_client
