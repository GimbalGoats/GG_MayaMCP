"""Maya MCP Server entrypoint.

This module creates and configures the FastMCP server instance,
registers all tools, and provides the main entry point.

Example:
    Run the server::

        python -m maya_mcp.server

    Or use the CLI::

        maya-mcp

    Or import and use programmatically::

        from maya_mcp.server import mcp
        mcp.run()
"""

from __future__ import annotations

import os
import sys

if __name__ == "__main__" and (__package__ is None or __package__ == ""):
    _package_dir = os.path.dirname(os.path.abspath(__file__))  # noqa: PTH100,PTH120
    _src_dir = os.path.dirname(_package_dir)  # noqa: PTH120
    if sys.path and os.path.abspath(sys.path[0]) == _package_dir:  # noqa: PTH100
        sys.path.pop(0)
    if _src_dir not in sys.path:
        sys.path.insert(0, _src_dir)
    __package__ = "maya_mcp"

from fastmcp import FastMCP

from maya_mcp import __version__
from maya_mcp.registrars import register_all_tools
from maya_mcp.tool_metadata import build_tool_title_transform

SERVER_VERSION = __version__
SERVER_WEBSITE_URL = "https://github.com/GimbalGoats/GG_MayaMCP"
SERVER_INSTRUCTIONS = """Maya MCP exposes typed tools for controlling a local Autodesk Maya session through
localhost commandPort. Use the tool descriptions and schemas as the source of truth,
keep read-only inspection separate from mutating actions, and enable raw script
execution only with the explicit MAYA_MCP_ENABLE_RAW_EXECUTION opt-in."""


def create_server() -> FastMCP:
    """Create and configure the FastMCP server instance."""
    mcp = FastMCP(
        name="Maya MCP",
        instructions=SERVER_INSTRUCTIONS,
        version=SERVER_VERSION,
        website_url=SERVER_WEBSITE_URL,
    )
    register_all_tools(mcp)
    mcp.add_transform(build_tool_title_transform())
    return mcp


mcp = create_server()


def main() -> None:
    """Run the Maya MCP server.

    This is the main entry point for the server. It starts the FastMCP
    server with stdio transport (the default for MCP).
    """
    if os.environ.get("MAYA_MCP_SKIP_RUN") == "1":
        return
    mcp.run()


if __name__ == "__main__":
    main()
