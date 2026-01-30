"""Integration tests for selection tools.

These tests require a running Maya instance with commandPort enabled.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from maya_mcp.transport.commandport import CommandPortClient


pytestmark = pytest.mark.integration


class TestSelectionGetIntegration:
    """Integration tests for the selection.get tool."""

    def test_selection_get_empty(self, maya_client: CommandPortClient, clean_scene: None) -> None:
        """selection.get returns empty list when nothing selected."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.selection import selection_get

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = selection_get()

            assert result["selection"] == []
            assert result["count"] == 0
        finally:
            transport_module._client = original_client

    def test_selection_get_with_selection(
        self, maya_client: CommandPortClient, test_cube: str
    ) -> None:
        """selection.get returns selected objects."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.selection import selection_get

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Select the test cube
            maya_client.execute(f"import maya.cmds as cmds; cmds.select('{test_cube}')")

            result = selection_get()

            assert result["count"] == 1
            assert test_cube in result["selection"]
        finally:
            transport_module._client = original_client

    def test_selection_get_multiple_objects(
        self, maya_client: CommandPortClient, test_objects: list[str]
    ) -> None:
        """selection.get returns multiple selected objects."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.selection import selection_get

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Select all test objects
            maya_client.execute(
                "import maya.cmds as cmds; cmds.select(['testCube1', 'testSphere1', 'testCone1'])"
            )

            result = selection_get()

            assert result["count"] == 3
            for obj in test_objects:
                assert obj in result["selection"]
        finally:
            transport_module._client = original_client


class TestSelectionSetIntegration:
    """Integration tests for the selection.set tool."""

    def test_selection_set_single_object(
        self, maya_client: CommandPortClient, test_cube: str
    ) -> None:
        """selection.set selects a single object."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.selection import selection_set

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = selection_set([test_cube])

            assert result["count"] == 1
            assert test_cube in result["selection"]
        finally:
            transport_module._client = original_client

    def test_selection_set_multiple_objects(
        self, maya_client: CommandPortClient, test_objects: list[str]
    ) -> None:
        """selection.set selects multiple objects."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.selection import selection_set

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = selection_set(test_objects)

            assert result["count"] == 3
            for obj in test_objects:
                assert obj in result["selection"]
        finally:
            transport_module._client = original_client

    def test_selection_set_replaces_selection(
        self, maya_client: CommandPortClient, test_objects: list[str]
    ) -> None:
        """selection.set replaces existing selection by default."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.selection import selection_set

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Select first object
            selection_set(["testCube1"])

            # Replace with second object
            result = selection_set(["testSphere1"])

            assert result["count"] == 1
            assert "testSphere1" in result["selection"]
            assert "testCube1" not in result["selection"]
        finally:
            transport_module._client = original_client

    def test_selection_set_add_mode(
        self, maya_client: CommandPortClient, test_objects: list[str]
    ) -> None:
        """selection.set with add=True adds to selection."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.selection import selection_set

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Select first object
            selection_set(["testCube1"])

            # Add second object
            result = selection_set(["testSphere1"], add=True)

            assert result["count"] == 2
            assert "testCube1" in result["selection"]
            assert "testSphere1" in result["selection"]
        finally:
            transport_module._client = original_client

    def test_selection_set_deselect_mode(
        self, maya_client: CommandPortClient, test_objects: list[str]
    ) -> None:
        """selection.set with deselect=True removes from selection."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.selection import selection_set

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Select all objects
            selection_set(test_objects)

            # Deselect one
            result = selection_set(["testCube1"], deselect=True)

            assert result["count"] == 2
            assert "testCube1" not in result["selection"]
            assert "testSphere1" in result["selection"]
            assert "testCone1" in result["selection"]
        finally:
            transport_module._client = original_client


class TestSelectionClearIntegration:
    """Integration tests for the selection.clear tool."""

    def test_selection_clear_from_empty(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """selection.clear works on empty selection."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.selection import selection_clear

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = selection_clear()

            assert result["selection"] == []
            assert result["count"] == 0
        finally:
            transport_module._client = original_client

    def test_selection_clear_clears_selection(
        self, maya_client: CommandPortClient, test_objects: list[str]
    ) -> None:
        """selection.clear clears existing selection."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.selection import selection_clear, selection_set

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Select objects first
            selection_set(test_objects)

            # Clear selection
            result = selection_clear()

            assert result["selection"] == []
            assert result["count"] == 0
        finally:
            transport_module._client = original_client


class TestSelectionValidation:
    """Integration tests for selection input validation."""

    def test_selection_set_empty_list_raises(self, maya_client: CommandPortClient) -> None:
        """selection.set raises ValueError for empty list."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.selection import selection_set

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            with pytest.raises(ValueError, match="empty"):
                selection_set([])
        finally:
            transport_module._client = original_client

    def test_selection_set_add_and_deselect_raises(
        self, maya_client: CommandPortClient, test_cube: str
    ) -> None:
        """selection.set raises ValueError when both add and deselect are True."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.selection import selection_set

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            with pytest.raises(ValueError, match=r"add.*deselect"):
                selection_set([test_cube], add=True, deselect=True)
        finally:
            transport_module._client = original_client

    def test_selection_set_invalid_node_name(self, maya_client: CommandPortClient) -> None:
        """selection.set validates node names for security."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.selection import selection_set

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Node names with forbidden characters should raise
            with pytest.raises(ValueError, match="Invalid"):
                selection_set(["test;node"])  # semicolon forbidden
        finally:
            transport_module._client = original_client
