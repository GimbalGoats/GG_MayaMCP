"""Tests for environment-driven configuration of the shared transport client."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

import maya_mcp.transport.commandport as transport_module
from maya_mcp.tools.connection import maya_connect
from maya_mcp.transport.commandport import client_overrides_from_env

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def fresh_shared_client() -> Iterator[None]:
    """Reset the shared client singleton around a test."""
    original = transport_module._client
    transport_module._client = None
    try:
        yield
    finally:
        transport_module._client = original


class TestClientOverridesFromEnv:
    def test_empty_environment_returns_no_overrides(self) -> None:
        assert client_overrides_from_env({}) == {}

    def test_blank_values_are_ignored(self) -> None:
        env = {
            "MAYA_MCP_HOST": "",
            "MAYA_MCP_PORT": "  ",
            "MAYA_MCP_CONNECT_TIMEOUT": "",
            "MAYA_MCP_COMMAND_TIMEOUT": "",
        }
        assert client_overrides_from_env(env) == {}

    def test_reads_all_supported_variables(self) -> None:
        env = {
            "MAYA_MCP_HOST": "127.0.0.1",
            "MAYA_MCP_PORT": "7002",
            "MAYA_MCP_CONNECT_TIMEOUT": "2.5",
            "MAYA_MCP_COMMAND_TIMEOUT": "60",
        }
        assert client_overrides_from_env(env) == {
            "host": "127.0.0.1",
            "port": 7002,
            "connect_timeout": 2.5,
            "command_timeout": 60.0,
        }

    def test_invalid_port_raises_with_variable_name(self) -> None:
        with pytest.raises(ValueError, match="MAYA_MCP_PORT must be an integer"):
            client_overrides_from_env({"MAYA_MCP_PORT": "abc"})

    def test_fractional_port_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="MAYA_MCP_PORT"):
            client_overrides_from_env({"MAYA_MCP_PORT": "7002.5"})

    def test_invalid_timeout_raises_with_variable_name(self) -> None:
        with pytest.raises(ValueError, match="MAYA_MCP_COMMAND_TIMEOUT must be a number"):
            client_overrides_from_env({"MAYA_MCP_COMMAND_TIMEOUT": "soon"})


class TestGetClientUsesEnvironment:
    def test_defaults_without_environment(
        self, fresh_shared_client: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for name in (
            "MAYA_MCP_HOST",
            "MAYA_MCP_PORT",
            "MAYA_MCP_CONNECT_TIMEOUT",
            "MAYA_MCP_COMMAND_TIMEOUT",
        ):
            monkeypatch.delenv(name, raising=False)

        client = transport_module.get_client()

        assert client.config.host == "localhost"
        assert client.config.port == 7001

    def test_port_and_timeouts_from_environment(
        self, fresh_shared_client: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MAYA_MCP_PORT", "7002")
        monkeypatch.setenv("MAYA_MCP_CONNECT_TIMEOUT", "3")
        monkeypatch.setenv("MAYA_MCP_COMMAND_TIMEOUT", "45")

        client = transport_module.get_client()

        assert client.config.port == 7002
        assert client.config.connect_timeout == 3.0
        assert client.config.command_timeout == 45.0

    def test_non_local_host_is_still_rejected(
        self, fresh_shared_client: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MAYA_MCP_HOST", "192.168.1.10")

        with pytest.raises(ValueError, match="localhost"):
            transport_module.get_client()


class TestMayaConnectKeepsConfiguredPort:
    def _client_on(self, port: int) -> MagicMock:
        client = MagicMock()
        client.config.host = "localhost"
        client.config.port = port
        client.source_type = "python"
        return client

    def test_bare_connect_keeps_configured_port(self) -> None:
        client = self._client_on(7002)

        with patch("maya_mcp.tools.connection.get_client", return_value=client):
            result = maya_connect()

        client.reconfigure.assert_not_called()
        client.connect.assert_called_once()
        assert result["port"] == 7002
        assert result["host"] == "localhost"

    def test_explicit_port_still_reconfigures(self) -> None:
        client = self._client_on(7002)

        with patch("maya_mcp.tools.connection.get_client", return_value=client):
            result = maya_connect(port=7001)

        client.reconfigure.assert_called_once_with(
            host="localhost", port=7001, source_type="python"
        )
        assert result["port"] == 7001
