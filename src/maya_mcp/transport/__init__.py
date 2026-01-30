"""Transport layer for Maya MCP.

This package provides the communication layer between Maya MCP and Maya's
commandPort socket interface.
"""

from maya_mcp.transport.commandport import CommandPortClient, get_client

__all__ = ["CommandPortClient", "get_client"]
