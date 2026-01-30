"""Maya MCP Server.

A Model Context Protocol (MCP) server for controlling Autodesk Maya via
its commandPort socket interface.

This package provides:
    - MCP tools for interacting with Maya (scene, nodes, selection, etc.)
    - A transport layer for Maya commandPort communication
    - Typed error handling and resilience features

Example:
    Run the MCP server::

        python -m maya_mcp.server

    Or import and use programmatically::

        from maya_mcp.server import mcp
        mcp.run()

Note:
    This package does NOT import any Maya modules directly. All communication
    with Maya happens via TCP socket to Maya's commandPort.
"""

from maya_mcp.errors import (
    MayaCommandError,
    MayaMCPError,
    MayaTimeoutError,
    MayaUnavailableError,
)
from maya_mcp.types import ConnectionStatus

__all__ = [
    "ConnectionStatus",
    "MayaCommandError",
    "MayaMCPError",
    "MayaTimeoutError",
    "MayaUnavailableError",
]

__version__ = "0.1.0"
