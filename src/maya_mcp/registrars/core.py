"""Registrar for core health and connection tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal

from mcp.types import ToolAnnotations

from maya_mcp.tools.connection import (
    MayaConnectOutput,
    MayaDisconnectOutput,
    maya_connect,
    maya_disconnect,
)
from maya_mcp.tools.health import HealthCheckOutput, health_check

if TYPE_CHECKING:
    from fastmcp import FastMCP


def tool_health_check() -> HealthCheckOutput:
    """Check Maya connection health.

    Returns status (ok/offline/reconnecting), last error, last contact
    timestamp, and connection configuration.
    """
    return health_check()


def tool_maya_connect(
    host: Annotated[str, "Target host (localhost only)"] = "localhost",
    port: Annotated[int, "Target port number"] = 7001,
    source_type: Annotated[
        Literal["python", "mel"],
        "Command interpreter type",
    ] = "python",
) -> MayaConnectOutput:
    """Connect to Maya commandPort.

    Args:
        host: Target host (localhost or 127.0.0.1 only).
        port: Target port number.
        source_type: Command interpreter (python or mel).

    Returns:
        Connection result with connected status, host, port, and error.
    """
    return maya_connect(host=host, port=port, source_type=source_type)


def tool_maya_disconnect() -> MayaDisconnectOutput:
    """Disconnect from Maya commandPort.

    Returns:
        Disconnect result with disconnected status and was_connected flag.
    """
    return maya_disconnect()


def register_core_tools(mcp: FastMCP) -> None:
    """Register core health and connection tools."""
    mcp.tool(
        name="health.check",
        description="Check the health status of the Maya connection",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_health_check)

    mcp.tool(
        name="maya.connect",
        description="Establish a connection to Maya's commandPort",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_maya_connect)

    mcp.tool(
        name="maya.disconnect",
        description="Close the connection to Maya",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_maya_disconnect)
