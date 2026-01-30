"""Integration tests for health and connection tools.

These tests require a running Maya instance with commandPort enabled.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from maya_mcp.transport.commandport import CommandPortClient


pytestmark = pytest.mark.integration


class TestHealthCheckIntegration:
    """Integration tests for the health.check tool."""

    def test_health_check_connected(self, maya_client: CommandPortClient) -> None:
        """Health check returns 'ok' when connected to Maya."""
        # Replace the global client with our test client
        import maya_mcp.transport.commandport as transport_module
        from maya_mcp.tools.health import health_check

        original_client = transport_module._client
        transport_module._client = maya_client

        try:
            result = health_check()

            assert result["status"] == "ok"
            assert result["host"] == "localhost"
            assert result["port"] == 7001
            assert result["last_error"] is None
        finally:
            transport_module._client = original_client

    def test_health_check_has_last_contact(self, maya_client: CommandPortClient) -> None:
        """Health check includes last contact timestamp when connected."""
        # Execute a command to ensure we have a last_contact timestamp
        maya_client.execute("print('test')")

        health = maya_client.get_health()

        assert health.status == "ok"
        assert health.last_contact is not None
        # Verify ISO8601 format (basic check)
        assert "T" in health.last_contact
        assert "Z" in health.last_contact


class TestMayaConnectIntegration:
    """Integration tests for the maya.connect tool."""

    def test_connect_success(self) -> None:
        """Connect tool successfully connects to Maya."""
        from maya_mcp.transport.commandport import CommandPortClient

        client = CommandPortClient(
            host="localhost",
            port=7001,
            connect_timeout=5.0,
            max_retries=1,
        )

        try:
            result = client.connect()
            assert result is True
            assert client.is_connected() is True
        finally:
            client.disconnect()

    def test_connect_executes_command_after(self) -> None:
        """Connection allows command execution."""
        from maya_mcp.transport.commandport import CommandPortClient

        client = CommandPortClient(
            host="localhost",
            port=7001,
            max_retries=1,
        )

        try:
            client.connect()

            # Execute a simple command
            result = client.execute("import maya.cmds as cmds; print(cmds.about(version=True))")

            # Should return Maya version string
            assert result != ""
            assert len(result) > 0
        finally:
            client.disconnect()


class TestMayaDisconnectIntegration:
    """Integration tests for the maya.disconnect tool."""

    def test_disconnect_closes_connection(self) -> None:
        """Disconnect tool properly closes the connection."""
        from maya_mcp.transport.commandport import CommandPortClient

        client = CommandPortClient(
            host="localhost",
            port=7001,
            max_retries=1,
        )

        client.connect()
        assert client.is_connected() is True

        result = client.disconnect()

        assert result is True
        assert client.is_connected() is False

    def test_disconnect_when_not_connected(self) -> None:
        """Disconnect returns False when not connected."""
        from maya_mcp.transport.commandport import CommandPortClient

        client = CommandPortClient(
            host="localhost",
            port=7001,
            max_retries=1,
        )

        # Don't connect
        result = client.disconnect()

        assert result is False


class TestConnectionRecovery:
    """Test connection recovery and state management."""

    def test_auto_reconnect_on_execute(self) -> None:
        """Client auto-connects when execute is called without connection."""
        from maya_mcp.transport.commandport import CommandPortClient

        client = CommandPortClient(
            host="localhost",
            port=7001,
            max_retries=1,
        )

        try:
            # Don't explicitly connect - execute should auto-connect
            client.execute("print('auto-connect test')")

            assert client.is_connected() is True
        finally:
            client.disconnect()

    def test_state_after_successful_command(self, maya_client: CommandPortClient) -> None:
        """Client state is updated after successful command."""
        # Clear any previous state
        initial_contact = maya_client.state.last_contact

        # Execute a command
        maya_client.execute("print('state test')")

        # State should be updated
        assert maya_client.state.last_error is None
        assert maya_client.state.last_contact is not None
        if initial_contact is not None:
            assert maya_client.state.last_contact >= initial_contact
