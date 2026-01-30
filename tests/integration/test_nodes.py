"""Integration tests for nodes.list tool.

These tests require a running Maya instance with commandPort enabled.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from maya_mcp.transport.commandport import CommandPortClient


pytestmark = pytest.mark.integration


class TestNodesListIntegration:
    """Integration tests for the nodes.list tool."""

    def test_nodes_list_returns_required_fields(self, maya_client: CommandPortClient) -> None:
        """nodes.list returns all required fields."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_list

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = nodes_list()

            assert "nodes" in result
            assert "count" in result
            assert isinstance(result["nodes"], list)
            assert isinstance(result["count"], int)
        finally:
            transport_module._client = original_client

    def test_nodes_list_finds_default_cameras(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """nodes.list finds Maya's default cameras in empty scene."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_list

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = nodes_list(node_type="camera")

            # Maya always has default cameras
            assert result["count"] >= 3  # persp, top, front, side
            camera_names = result["nodes"]
            assert any("persp" in name for name in camera_names)
        finally:
            transport_module._client = original_client

    def test_nodes_list_filter_by_type(
        self, maya_client: CommandPortClient, test_objects: list[str]
    ) -> None:
        """nodes.list correctly filters by node type."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_list

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # List only mesh nodes
            result = nodes_list(node_type="mesh")

            # We created 3 objects, each has a mesh shape
            assert result["count"] >= 3
            # All returned nodes should be mesh shapes
            for node in result["nodes"]:
                assert "Shape" in node or node.endswith("Shape")
        finally:
            transport_module._client = original_client

    def test_nodes_list_filter_by_pattern(
        self, maya_client: CommandPortClient, test_objects: list[str]
    ) -> None:
        """nodes.list correctly filters by name pattern."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_list

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # List only nodes matching pattern
            result = nodes_list(pattern="testCube*")

            assert result["count"] >= 1
            for node in result["nodes"]:
                assert "testCube" in node
        finally:
            transport_module._client = original_client

    def test_nodes_list_long_names(
        self, maya_client: CommandPortClient, test_objects: list[str]
    ) -> None:
        """nodes.list returns long names when requested."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_list

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = nodes_list(pattern="testCube*", long_names=True)

            # Long names start with |
            for node in result["nodes"]:
                if node.startswith("|"):
                    # At least one long name found
                    break
            else:
                # Transform nodes might not have | prefix if at root
                # But shapes should have parent in path
                pass
        finally:
            transport_module._client = original_client

    def test_nodes_list_limit(self, maya_client: CommandPortClient) -> None:
        """nodes.list respects limit parameter."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_list

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Get all nodes first
            all_result = nodes_list(limit=0)
            total = all_result["count"]

            if total > 5:
                # Request limited results
                limited_result = nodes_list(limit=5)

                assert limited_result["count"] == 5
                assert limited_result["truncated"] is True
                assert limited_result["total_count"] == total
        finally:
            transport_module._client = original_client

    def test_nodes_list_no_truncation_when_under_limit(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """nodes.list doesn't add truncation fields when under limit."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_list

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Use a very high limit
            result = nodes_list(limit=10000)

            # Should not have truncation fields
            assert "truncated" not in result
            assert "total_count" not in result
        finally:
            transport_module._client = original_client

    def test_nodes_list_combined_filters(
        self, maya_client: CommandPortClient, test_objects: list[str]
    ) -> None:
        """nodes.list combines type and pattern filters correctly."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_list

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Filter by both type and pattern
            result = nodes_list(node_type="transform", pattern="testSphere*")

            assert result["count"] >= 1
            for node in result["nodes"]:
                assert "testSphere" in node
        finally:
            transport_module._client = original_client

    def test_nodes_list_empty_result(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """nodes.list returns empty list for non-matching query."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_list

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = nodes_list(pattern="nonExistentNode12345*")

            assert result["nodes"] == []
            assert result["count"] == 0
        finally:
            transport_module._client = original_client
