"""Integration tests for scene tools.

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


class TestSceneUndoIntegration:
    """Integration tests for the scene.undo tool."""

    def test_scene_undo_after_operation(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """scene.undo reverts the last operation."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_undo

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Create a node (undoable operation)
            maya_client.execute("import maya.cmds as cmds; cmds.polyCube(name='undoTestCube')")

            # Verify it exists
            exists_before = maya_client.execute(
                "import maya.cmds as cmds; print(cmds.objExists('undoTestCube'))"
            )
            assert "True" in exists_before

            # Undo
            result = scene_undo()

            assert result["success"] is True
            assert result["undone"] is not None

            # Verify it's gone
            exists_after = maya_client.execute(
                "import maya.cmds as cmds; print(cmds.objExists('undoTestCube'))"
            )
            assert "False" in exists_after
        finally:
            transport_module._client = original_client

    def test_scene_undo_returns_required_fields(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """scene.undo returns all required fields."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_undo

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Create something to undo
            maya_client.execute("import maya.cmds as cmds; cmds.polyCube()")

            result = scene_undo()

            assert "success" in result
            assert "undone" in result
            assert "can_undo" in result
            assert "can_redo" in result
            assert isinstance(result["success"], bool)
            assert isinstance(result["can_undo"], bool)
            assert isinstance(result["can_redo"], bool)
        finally:
            transport_module._client = original_client

    def test_scene_undo_sets_can_redo(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """scene.undo sets can_redo to True after successful undo."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_undo

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Create something to undo
            maya_client.execute("import maya.cmds as cmds; cmds.polyCube()")

            result = scene_undo()

            assert result["success"] is True
            assert result["can_redo"] is True
        finally:
            transport_module._client = original_client


class TestSceneRedoIntegration:
    """Integration tests for the scene.redo tool."""

    def test_scene_redo_after_undo(self, maya_client: CommandPortClient, clean_scene: None) -> None:
        """scene.redo re-applies an undone operation."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_redo, scene_undo

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Create a node
            maya_client.execute("import maya.cmds as cmds; cmds.polyCube(name='redoTestCube')")

            # Undo it
            scene_undo()

            # Verify it's gone
            exists_after_undo = maya_client.execute(
                "import maya.cmds as cmds; print(cmds.objExists('redoTestCube'))"
            )
            assert "False" in exists_after_undo

            # Redo it
            result = scene_redo()

            assert result["success"] is True
            assert result["redone"] is not None

            # Verify it's back
            exists_after_redo = maya_client.execute(
                "import maya.cmds as cmds; print(cmds.objExists('redoTestCube'))"
            )
            assert "True" in exists_after_redo
        finally:
            transport_module._client = original_client

    def test_scene_redo_returns_required_fields(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """scene.redo returns all required fields."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_redo, scene_undo

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Create and undo to enable redo
            maya_client.execute("import maya.cmds as cmds; cmds.polyCube()")
            scene_undo()

            result = scene_redo()

            assert "success" in result
            assert "redone" in result
            assert "can_undo" in result
            assert "can_redo" in result
            assert isinstance(result["success"], bool)
            assert isinstance(result["can_undo"], bool)
            assert isinstance(result["can_redo"], bool)
        finally:
            transport_module._client = original_client

    def test_scene_redo_nothing_to_redo(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """scene.redo fails when nothing to redo."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_redo

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Perform an action to clear redo queue
            maya_client.execute("import maya.cmds as cmds; cmds.polyCube()")

            result = scene_redo()

            assert result["success"] is False
            assert result["redone"] is None
        finally:
            transport_module._client = original_client


class TestSceneNewIntegration:
    """Integration tests for the scene.new tool."""

    def test_scene_new_unmodified(self, maya_client: CommandPortClient, clean_scene: None) -> None:
        """scene.new succeeds on an unmodified scene."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_new

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = scene_new()

            assert result["success"] is True
            assert result["was_modified"] is False
            assert result["error"] is None
        finally:
            transport_module._client = original_client

    def test_scene_new_modified_refused(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """scene.new refuses when scene is modified and force=False."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_new

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Modify the scene
            maya_client.execute("import maya.cmds as cmds; cmds.polyCube()")

            result = scene_new(force=False)

            assert result["success"] is False
            assert result["was_modified"] is True
            assert result["error"] is not None
            assert "unsaved changes" in result["error"]
        finally:
            transport_module._client = original_client

    def test_scene_new_modified_force(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """scene.new succeeds when scene is modified and force=True."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_new

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Modify the scene
            maya_client.execute("import maya.cmds as cmds; cmds.polyCube(name='forceTestCube')")

            result = scene_new(force=True)

            assert result["success"] is True
            assert result["was_modified"] is True
            assert result["error"] is None

            # Verify the cube is gone (new scene)
            exists_after = maya_client.execute(
                "import maya.cmds as cmds; print(cmds.objExists('forceTestCube'))"
            )
            assert "False" in exists_after
        finally:
            transport_module._client = original_client

    def test_scene_new_returns_required_fields(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """scene.new returns all required fields."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_new

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = scene_new()

            assert "success" in result
            assert "previous_file" in result
            assert "was_modified" in result
            assert "error" in result
            assert isinstance(result["success"], bool)
            assert isinstance(result["was_modified"], bool)
        finally:
            transport_module._client = original_client

    def test_scene_new_clears_scene(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """scene.new actually creates a fresh scene with no user objects."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.scene import scene_new

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Create some objects
            maya_client.execute("import maya.cmds as cmds; cmds.polyCube(name='clearTestA')")
            maya_client.execute("import maya.cmds as cmds; cmds.polySphere(name='clearTestB')")

            scene_new(force=True)

            # Verify objects are gone
            exists_a = maya_client.execute(
                "import maya.cmds as cmds; print(cmds.objExists('clearTestA'))"
            )
            exists_b = maya_client.execute(
                "import maya.cmds as cmds; print(cmds.objExists('clearTestB'))"
            )
            assert "False" in exists_a
            assert "False" in exists_b
        finally:
            transport_module._client = original_client
