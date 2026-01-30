"""Tests for health and connection tools.

These tests verify the MCP tools for health checking and
connection management work correctly with mocked transport.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from maya_mcp.tools.connection import maya_connect, maya_disconnect
from maya_mcp.tools.health import health_check
from maya_mcp.types import HealthCheckResult


class TestHealthCheck:
    """Tests for the health.check tool."""

    def test_health_check_offline(self) -> None:
        """Health check returns offline status when not connected."""
        mock_client = MagicMock()
        mock_client.get_health.return_value = HealthCheckResult(
            status="offline",
            last_error=None,
            last_contact=None,
            host="localhost",
            port=7001,
        )

        with patch("maya_mcp.tools.health.get_client", return_value=mock_client):
            result = health_check()

        assert result["status"] == "offline"
        assert result["last_error"] is None
        assert result["last_contact"] is None
        assert result["host"] == "localhost"
        assert result["port"] == 7001

    def test_health_check_connected(self) -> None:
        """Health check returns ok status when connected."""
        mock_client = MagicMock()
        mock_client.get_health.return_value = HealthCheckResult(
            status="ok",
            last_error=None,
            last_contact="2025-01-30T10:00:00Z",
            host="localhost",
            port=7001,
        )

        with patch("maya_mcp.tools.health.get_client", return_value=mock_client):
            result = health_check()

        assert result["status"] == "ok"
        assert result["last_contact"] == "2025-01-30T10:00:00Z"

    def test_health_check_with_error(self) -> None:
        """Health check includes last error when present."""
        mock_client = MagicMock()
        mock_client.get_health.return_value = HealthCheckResult(
            status="offline",
            last_error="Connection refused",
            last_contact=None,
            host="localhost",
            port=7001,
        )

        with patch("maya_mcp.tools.health.get_client", return_value=mock_client):
            result = health_check()

        assert result["status"] == "offline"
        assert result["last_error"] == "Connection refused"


class TestMayaConnect:
    """Tests for the maya.connect tool."""

    def test_connect_success(self) -> None:
        """Connect returns success when connection succeeds."""
        mock_client = MagicMock()
        mock_client.config.host = "localhost"
        mock_client.config.port = 7001

        with patch("maya_mcp.tools.connection.get_client", return_value=mock_client):
            result = maya_connect()

        assert result["connected"] is True
        assert result["host"] == "localhost"
        assert result["port"] == 7001
        assert result["error"] is None
        mock_client.connect.assert_called_once()

    def test_connect_failure(self) -> None:
        """Connect returns error when connection fails."""
        from maya_mcp.errors import MayaUnavailableError

        mock_client = MagicMock()
        mock_client.config.host = "localhost"
        mock_client.config.port = 7001
        mock_client.connect.side_effect = MayaUnavailableError(
            message="Connection refused",
            host="localhost",
            port=7001,
            attempts=3,
        )

        with patch("maya_mcp.tools.connection.get_client", return_value=mock_client):
            result = maya_connect()

        assert result["connected"] is False
        assert result["error"] == "Connection refused"

    def test_connect_with_custom_port(self) -> None:
        """Connect reconfigures when port differs."""
        mock_client = MagicMock()
        mock_client.config.host = "localhost"
        mock_client.config.port = 7001

        with patch("maya_mcp.tools.connection.get_client", return_value=mock_client):
            result = maya_connect(port=7002)

        mock_client.reconfigure.assert_called_once_with(host="localhost", port=7002)
        assert result["port"] == 7002


class TestMayaDisconnect:
    """Tests for the maya.disconnect tool."""

    def test_disconnect_when_connected(self) -> None:
        """Disconnect returns was_connected=True when connected."""
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True

        with patch("maya_mcp.tools.connection.get_client", return_value=mock_client):
            result = maya_disconnect()

        assert result["disconnected"] is True
        assert result["was_connected"] is True
        mock_client.disconnect.assert_called_once()

    def test_disconnect_when_not_connected(self) -> None:
        """Disconnect returns was_connected=False when not connected."""
        mock_client = MagicMock()
        mock_client.is_connected.return_value = False

        with patch("maya_mcp.tools.connection.get_client", return_value=mock_client):
            result = maya_disconnect()

        assert result["disconnected"] is True
        assert result["was_connected"] is False


class TestConnectionStateTransitions:
    """Tests for connection state transitions."""

    def test_offline_to_connected(self) -> None:
        """State transitions from offline to connected on successful connect."""
        mock_client = MagicMock()
        mock_client.config.host = "localhost"
        mock_client.config.port = 7001
        mock_client.get_health.return_value = HealthCheckResult(
            status="offline",
            last_error=None,
            last_contact=None,
            host="localhost",
            port=7001,
        )

        with patch("maya_mcp.tools.health.get_client", return_value=mock_client):
            # Check initial state
            result = health_check()
            assert result["status"] == "offline"

        # Simulate successful connection
        mock_client.get_health.return_value = HealthCheckResult(
            status="ok",
            last_error=None,
            last_contact="2025-01-30T10:00:00Z",
            host="localhost",
            port=7001,
        )

        with (
            patch("maya_mcp.tools.health.get_client", return_value=mock_client),
            patch("maya_mcp.tools.connection.get_client", return_value=mock_client),
        ):
            maya_connect()
            result = health_check()
            assert result["status"] == "ok"

    def test_connected_to_offline_on_disconnect(self) -> None:
        """State transitions from connected to offline on disconnect."""
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True

        mock_client.get_health.return_value = HealthCheckResult(
            status="ok",
            last_error=None,
            last_contact="2025-01-30T10:00:00Z",
            host="localhost",
            port=7001,
        )

        with patch("maya_mcp.tools.health.get_client", return_value=mock_client):
            result = health_check()
            assert result["status"] == "ok"

        with patch("maya_mcp.tools.connection.get_client", return_value=mock_client):
            maya_disconnect()

        # Simulate post-disconnect state
        mock_client.get_health.return_value = HealthCheckResult(
            status="offline",
            last_error=None,
            last_contact="2025-01-30T10:00:00Z",
            host="localhost",
            port=7001,
        )

        with patch("maya_mcp.tools.health.get_client", return_value=mock_client):
            result = health_check()
            assert result["status"] == "offline"


class TestHealthCheckResultShape:
    """Tests for health check result shape compliance."""

    def test_result_has_required_fields(self) -> None:
        """Health check result includes all required fields."""
        mock_client = MagicMock()
        mock_client.get_health.return_value = HealthCheckResult(
            status="ok",
            last_error=None,
            last_contact="2025-01-30T10:00:00Z",
            host="localhost",
            port=7001,
        )

        with patch("maya_mcp.tools.health.get_client", return_value=mock_client):
            result = health_check()

        # Verify all required fields exist
        assert "status" in result
        assert "last_error" in result
        assert "last_contact" in result
        assert "host" in result
        assert "port" in result

    def test_status_is_valid_enum(self) -> None:
        """Health check status is one of valid enum values."""
        valid_statuses = {"ok", "offline", "reconnecting"}

        mock_client = MagicMock()
        mock_client.get_health.return_value = HealthCheckResult(
            status="offline",
            last_error=None,
            last_contact=None,
            host="localhost",
            port=7001,
        )

        with patch("maya_mcp.tools.health.get_client", return_value=mock_client):
            result = health_check()

        assert result["status"] in valid_statuses


class TestConnectResultShape:
    """Tests for connect result shape compliance."""

    def test_success_result_shape(self) -> None:
        """Successful connect has correct result shape."""
        mock_client = MagicMock()
        mock_client.config.host = "localhost"
        mock_client.config.port = 7001

        with patch("maya_mcp.tools.connection.get_client", return_value=mock_client):
            result = maya_connect()

        assert "connected" in result
        assert "host" in result
        assert "port" in result
        assert "error" in result
        assert isinstance(result["connected"], bool)
        assert isinstance(result["host"], str)
        assert isinstance(result["port"], int)

    def test_failure_result_shape(self) -> None:
        """Failed connect has correct result shape."""
        from maya_mcp.errors import MayaUnavailableError

        mock_client = MagicMock()
        mock_client.config.host = "localhost"
        mock_client.config.port = 7001
        mock_client.connect.side_effect = MayaUnavailableError(
            message="Connection refused",
            host="localhost",
            port=7001,
            attempts=3,
        )

        with patch("maya_mcp.tools.connection.get_client", return_value=mock_client):
            result = maya_connect()

        assert result["connected"] is False
        assert result["error"] is not None
        assert isinstance(result["error"], str)


class TestDisconnectResultShape:
    """Tests for disconnect result shape compliance."""

    def test_result_shape(self) -> None:
        """Disconnect has correct result shape."""
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True

        with patch("maya_mcp.tools.connection.get_client", return_value=mock_client):
            result = maya_disconnect()

        assert "disconnected" in result
        assert "was_connected" in result
        assert isinstance(result["disconnected"], bool)
        assert isinstance(result["was_connected"], bool)
