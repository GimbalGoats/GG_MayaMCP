"""Checks for the Autodesk Design and Make Marketplace manifest."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

from maya_mcp.server import mcp

REPOSITORY_ROOT = Path(__file__).parents[1]
MANIFEST_PATH = REPOSITORY_ROOT / "packaging" / "autodesk" / "mcp-tool-manifest.json"


def test_autodesk_manifest_matches_live_tool_list() -> None:
    """Prevent marketplace declarations from drifting from MCP tools/list."""
    result = subprocess.run(
        [sys.executable, "packaging/autodesk/generate_manifest.py", "--check"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    live_tools = asyncio.run(mcp.list_tools())

    assert {tool["name"] for tool in manifest["tools"]} == {tool.name for tool in live_tools}
    assert len(manifest["tools"]) == 71
    assert all(tool["description"].endswith(".") for tool in manifest["tools"])
    assert manifest["resources"] == []
    assert manifest["prompts"] == []
    assert manifest["external_endpoints"] == []
    assert manifest["ai_llm_providers"] == []
