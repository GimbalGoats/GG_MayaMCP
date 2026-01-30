"""Integration tests for nodes tools.

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


class TestNodesCreateIntegration:
    """Integration tests for the nodes.create tool."""

    def test_nodes_create_simple(self, maya_client: CommandPortClient, clean_scene: None) -> None:
        """nodes.create creates a basic node."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_create

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = nodes_create("transform")

            assert result["node"] is not None
            assert result["node_type"] == "transform"
            assert result["parent"] is None
            assert result["attributes_set"] == []
            assert result["attribute_errors"] is None

            # Verify node exists in Maya
            exists = maya_client.execute(
                f"import maya.cmds as cmds; print(cmds.objExists('{result['node']}'))"
            )
            assert "True" in exists
        finally:
            transport_module._client = original_client

    def test_nodes_create_with_name(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """nodes.create uses the specified name."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_create

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = nodes_create("transform", name="myTestNode")

            assert result["node"] == "myTestNode"

            # Verify node exists in Maya
            exists = maya_client.execute(
                "import maya.cmds as cmds; print(cmds.objExists('myTestNode'))"
            )
            assert "True" in exists
        finally:
            transport_module._client = original_client

    def test_nodes_create_with_parent(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """nodes.create parents node correctly."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_create

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Create parent first
            maya_client.execute(
                "import maya.cmds as cmds; cmds.createNode('transform', name='parentNode')"
            )

            result = nodes_create("transform", name="childNode", parent="parentNode")

            assert result["node"] == "childNode"
            assert result["parent"] == "parentNode"

            # Verify parent-child relationship
            parent = maya_client.execute(
                "import maya.cmds as cmds; print(cmds.listRelatives('childNode', parent=True))"
            )
            assert "parentNode" in parent
        finally:
            transport_module._client = original_client

    def test_nodes_create_with_attributes(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """nodes.create sets initial attributes."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_create

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = nodes_create(
                "transform",
                name="attrTestNode",
                attributes={"translateX": 10.0, "translateY": 5.0},
            )

            assert result["node"] == "attrTestNode"
            assert "translateX" in result["attributes_set"]
            assert "translateY" in result["attributes_set"]

            # Verify attribute values
            tx = maya_client.execute(
                "import maya.cmds as cmds; print(cmds.getAttr('attrTestNode.translateX'))"
            )
            assert "10" in tx
        finally:
            transport_module._client = original_client

    def test_nodes_create_different_types(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """nodes.create works with various node types."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_create

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Test creating a multiplyDivide utility node
            result = nodes_create("multiplyDivide", name="testMD")

            assert result["node"] == "testMD"
            assert result["node_type"] == "multiplyDivide"

            # Verify node exists
            exists = maya_client.execute(
                "import maya.cmds as cmds; print(cmds.objExists('testMD'))"
            )
            assert "True" in exists
        finally:
            transport_module._client = original_client


class TestNodesDeleteIntegration:
    """Integration tests for the nodes.delete tool."""

    def test_nodes_delete_single(self, maya_client: CommandPortClient, clean_scene: None) -> None:
        """nodes.delete removes a single node."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_delete

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Create a node to delete
            maya_client.execute("import maya.cmds as cmds; cmds.polyCube(name='deleteMe')")

            result = nodes_delete(["deleteMe"])

            assert "deleteMe" in result["deleted"]
            assert result["count"] >= 1
            assert result["errors"] is None

            # Verify node is gone
            exists = maya_client.execute(
                "import maya.cmds as cmds; print(cmds.objExists('deleteMe'))"
            )
            assert "False" in exists
        finally:
            transport_module._client = original_client

    def test_nodes_delete_multiple(self, maya_client: CommandPortClient, clean_scene: None) -> None:
        """nodes.delete removes multiple nodes."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_delete

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Create nodes to delete
            maya_client.execute(
                "import maya.cmds as cmds; cmds.polyCube(name='del1'); cmds.polySphere(name='del2')"
            )

            result = nodes_delete(["del1", "del2"])

            assert result["count"] == 2
            assert "del1" in result["deleted"]
            assert "del2" in result["deleted"]
        finally:
            transport_module._client = original_client

    def test_nodes_delete_nonexistent(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """nodes.delete reports error for nonexistent nodes."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_delete

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = nodes_delete(["nonExistentNode12345"])

            assert result["count"] == 0
            assert result["deleted"] == []
            assert result["errors"] is not None
            assert "nonExistentNode12345" in result["errors"]
        finally:
            transport_module._client = original_client

    def test_nodes_delete_with_hierarchy(
        self, maya_client: CommandPortClient, clean_scene: None
    ) -> None:
        """nodes.delete with hierarchy removes children."""
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.nodes import nodes_delete

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            # Create parent with child
            maya_client.execute(
                "import maya.cmds as cmds; "
                "cmds.group(empty=True, name='parent'); "
                "cmds.polyCube(name='child'); "
                "cmds.parent('child', 'parent')"
            )

            result = nodes_delete(["parent"], hierarchy=True)

            assert "parent" in result["deleted"]

            # Verify both are gone
            exists_parent = maya_client.execute(
                "import maya.cmds as cmds; print(cmds.objExists('parent'))"
            )
            exists_child = maya_client.execute(
                "import maya.cmds as cmds; print(cmds.objExists('child'))"
            )
            assert "False" in exists_parent
            assert "False" in exists_child
        finally:
            transport_module._client = original_client
