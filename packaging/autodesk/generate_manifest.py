"""Generate the Autodesk Design and Make Marketplace MCP Tool Manifest."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from maya_mcp.server import mcp

MANIFEST_PATH = Path(__file__).with_name("mcp-tool-manifest.json")


def _plain_language_description(description: str) -> str:
    """Return the first descriptive sentence without implementation details."""
    paragraph = description.strip().split("\n\n", 1)[0]
    normalized = " ".join(paragraph.split())
    first_sentence = normalized.split(". ", 1)[0].rstrip(".")
    return f"{first_sentence}."


async def build_manifest() -> dict[str, object]:
    """Build a manifest from the server's public tool declarations."""
    tools = await mcp.list_tools()
    declarations = [
        {
            "name": tool.name,
            "description": _plain_language_description(tool.description or ""),
        }
        for tool in sorted(tools, key=lambda item: item.name)
    ]

    if any(declaration["description"] == "." for declaration in declarations):
        raise ValueError("Every MCP tool must have a description")

    return {
        "mcp_manifest_version": "1.0",
        "app_model": "A",
        "mcp_spec_version": "2025-11-25",
        "server": {"name": "maya-mcp", "transport": "stdio"},
        "tools": declarations,
        "resources": [],
        "prompts": [],
        "external_endpoints": [],
        "autodesk_apis_used": [
            "Autodesk Maya commandPort",
            "Autodesk Maya Python commands (maya.cmds)",
        ],
        "ai_llm_providers": [],
    }


def render_manifest() -> str:
    """Render the current manifest as deterministic JSON."""
    return f"{json.dumps(asyncio.run(build_manifest()), indent=2, ensure_ascii=False)}\n"


def main() -> int:
    """Write the manifest, or verify that the checked-in copy is current."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the checked-in manifest differs from the live MCP tool list",
    )
    args = parser.parse_args()
    expected = render_manifest()

    if args.check:
        actual = MANIFEST_PATH.read_text(encoding="utf-8") if MANIFEST_PATH.exists() else ""
        if actual != expected:
            print(
                "Autodesk manifest is stale; run packaging/autodesk/generate_manifest.py",
                file=sys.stderr,
            )
            return 1
        return 0

    MANIFEST_PATH.write_text(expected, encoding="utf-8")
    print(f"Wrote {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
