"""Integration tests for Maya MCP.

These tests require a running Maya instance with commandPort enabled.
They are skipped in CI and must be run manually with:

    pytest tests/integration -v

To run with Maya, first paste and run the complete repository
``scripts/enable_commandport.py`` file in Maya's Python Script Editor.

All tests in this directory are marked with @pytest.mark.integration.
"""
