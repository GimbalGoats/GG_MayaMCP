"""Smoke-test a staged or unpacked Maya MCP Claude Desktop bundle."""

from __future__ import annotations

import argparse
import asyncio
import os
import struct
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
REQUIRED_ICON_SIZE = (512, 512)
REQUIRED_TOOLS = ("health_check", "scene_info", "nodes_list")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_dir", type=Path, help="Staged or unpacked MCPB directory.")
    parser.add_argument("--expected-tools", type=int, default=None)
    return parser.parse_args(argv)


def read_png_size(path: Path) -> tuple[int, int]:
    """Read PNG dimensions from the IHDR chunk."""
    with path.open("rb") as file:
        signature = file.read(len(PNG_SIGNATURE))
        if signature != PNG_SIGNATURE:
            raise RuntimeError(f"Expected PNG signature in {path}")

        header = file.read(8)
        if len(header) != 8:
            raise RuntimeError(f"Missing PNG IHDR header in {path}")

        chunk_length, chunk_type = struct.unpack(">I4s", header)
        if chunk_type != b"IHDR" or chunk_length < 8:
            raise RuntimeError(f"Missing PNG IHDR chunk in {path}")

        size_bytes = file.read(8)
        if len(size_bytes) != 8:
            raise RuntimeError(f"Missing PNG size data in {path}")

    return struct.unpack(">II", size_bytes)


async def smoke_test(bundle_dir: Path, expected_tools: int | None) -> None:
    """Launch the bundled stdio server and verify its tool surface."""
    server_module = bundle_dir / "src" / "maya_mcp" / "server.py"
    if not server_module.exists():
        raise RuntimeError(f"Missing bundled server module: {server_module}")

    icon_path = bundle_dir / "icon.png"
    if not icon_path.exists():
        raise RuntimeError(f"Missing bundled connector icon: {icon_path}")

    icon_size = read_png_size(icon_path)
    if icon_size != REQUIRED_ICON_SIZE:
        raise RuntimeError(f"Expected icon size {REQUIRED_ICON_SIZE}, got {icon_size}")

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

    errlog_handle, errlog_name = tempfile.mkstemp(text=True)
    os.close(errlog_handle)
    errlog_path = Path(errlog_name)
    try:
        with errlog_path.open("w+", encoding="utf-8") as errlog:
            try:
                async with (
                    stdio_client(params, errlog=errlog) as (read, write),
                    ClientSession(read, write) as session,
                ):
                    init = await session.initialize()
                    tools_result = await session.list_tools()
            except Exception as exc:
                errlog.flush()
                errlog.seek(0)
                server_stderr = errlog.read().strip()
                if not server_stderr:
                    server_stderr = "<empty>"
                raise RuntimeError(
                    f"MCPB smoke test failed. Server stderr:\n{server_stderr}"
                ) from exc
    finally:
        errlog_path.unlink(missing_ok=True)

    tool_names = {tool.name for tool in tools_result.tools}
    missing_tools = sorted(set(REQUIRED_TOOLS) - tool_names)
    if missing_tools:
        raise RuntimeError(f"Missing required tools: {', '.join(missing_tools)}")

    if expected_tools is not None and len(tool_names) != expected_tools:
        raise RuntimeError(f"Expected {expected_tools} tools, got {len(tool_names)}")

    print(f"server={init.serverInfo.name} version={init.serverInfo.version}")
    print(f"icon={icon_size[0]}x{icon_size[1]}")
    print(f"tools={len(tool_names)}")
    print(f"required={','.join(REQUIRED_TOOLS)}")


def main(argv: list[str] | None = None) -> None:
    """Run the smoke test."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    asyncio.run(smoke_test(args.bundle_dir.resolve(), args.expected_tools))


if __name__ == "__main__":
    main()
