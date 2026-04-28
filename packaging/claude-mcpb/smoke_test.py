"""Smoke-test a staged or unpacked Maya MCP Claude Desktop bundle."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REQUIRED_TOOLS = ("health_check", "scene_info", "nodes_list")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_dir", type=Path, help="Staged or unpacked MCPB directory.")
    parser.add_argument("--expected-tools", type=int, default=None)
    return parser.parse_args(argv)


async def smoke_test(bundle_dir: Path, expected_tools: int | None) -> None:
    """Launch the bundled stdio server and verify its tool surface."""
    server_module = bundle_dir / "src" / "maya_mcp" / "server.py"
    if not server_module.exists():
        raise RuntimeError(f"Missing bundled server module: {server_module}")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(bundle_dir / "src")
    env.setdefault("MAYA_MCP_HOST", "localhost")
    env.setdefault("MAYA_MCP_PORT", "7001")
    env.setdefault("MAYA_MCP_CLAUDE_DESKTOP_COMPAT", "true")

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "maya_mcp.server"],
        cwd=str(bundle_dir),
        env=env,
    )

    with Path(os.devnull).open("w", encoding="utf-8") as errlog:
        async with stdio_client(params, errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                tools_result = await session.list_tools()

    tool_names = {tool.name for tool in tools_result.tools}
    missing_tools = sorted(set(REQUIRED_TOOLS) - tool_names)
    if missing_tools:
        raise RuntimeError(f"Missing required tools: {', '.join(missing_tools)}")

    if expected_tools is not None and len(tool_names) != expected_tools:
        raise RuntimeError(f"Expected {expected_tools} tools, got {len(tool_names)}")

    print(f"server={init.serverInfo.name} version={init.serverInfo.version}")
    print(f"tools={len(tool_names)}")
    print(f"required={','.join(REQUIRED_TOOLS)}")


def main(argv: list[str] | None = None) -> None:
    """Run the smoke test."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    asyncio.run(smoke_test(args.bundle_dir.resolve(), args.expected_tools))


if __name__ == "__main__":
    main()
