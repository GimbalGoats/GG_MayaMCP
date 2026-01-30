"""Integration tests for Maya MCP.

These tests require a running Maya instance with commandPort enabled.
They are skipped in CI and must be run manually with:

    pytest tests/integration -v

To run with Maya, first enable the commandPort in Maya:

    import maya.cmds as cmds
    cmds.commandPort(name=":7001", sourceType="python", echoOutput=True)

All tests in this directory are marked with @pytest.mark.integration.
"""
