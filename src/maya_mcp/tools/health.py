"""Health check tool for Maya MCP.

This module provides the health.check tool for monitoring the connection
status between Maya MCP and Maya.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from maya_mcp.transport import get_client

if TYPE_CHECKING:
    from maya_mcp.types import HealthCheckResult


def health_check() -> dict[str, Any]:
    """Check the health status of the Maya connection.

    Returns current connection status, last error (if any), last successful
    contact timestamp, and connection configuration.

    Returns:
        Dictionary with health check results:
            - status: "ok" | "offline" | "reconnecting"
            - last_error: Last error message or None
            - last_contact: ISO8601 timestamp or None
            - host: Current target host
            - port: Current target port

    Example:
        >>> result = health_check()
        >>> print(result["status"])
        'ok'
    """
    client = get_client()
    health: HealthCheckResult = client.get_health()

    return {
        "status": health.status,
        "last_error": health.last_error,
        "last_contact": health.last_contact,
        "host": health.host,
        "port": health.port,
    }
