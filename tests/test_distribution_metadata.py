"""Checks for public distribution and registry metadata."""

from __future__ import annotations

import json
from pathlib import Path

from maya_mcp import __version__

REPOSITORY_ROOT = Path(__file__).parents[1]
REGISTRY_NAME = "io.github.GimbalGoats/maya-mcp"


def test_official_registry_metadata_matches_package() -> None:
    """Keep the checked-in MCP Registry entry synchronized with the package."""
    metadata = json.loads((REPOSITORY_ROOT / "server.json").read_text(encoding="utf-8"))

    assert metadata["name"] == REGISTRY_NAME
    assert metadata["version"] == __version__
    assert len(metadata["description"]) <= 100
    assert metadata["repository"] == {
        "url": "https://github.com/GimbalGoats/GG_MayaMCP",
        "source": "github",
        "id": "1184183752",
    }

    assert len(metadata["packages"]) == 1
    package = metadata["packages"][0]
    assert package == {
        "registryType": "pypi",
        "identifier": "maya-mcp",
        "version": __version__,
        "runtimeHint": "uvx",
        "transport": {"type": "stdio"},
    }


def test_pypi_readme_contains_registry_ownership_marker() -> None:
    """Keep the ownership proof in the README shipped to PyPI."""
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")

    assert f"<!-- mcp-name: {REGISTRY_NAME} -->" in readme


def test_claude_mcpb_metadata_matches_release_and_publisher() -> None:
    """Keep the MCPB release and directory publisher identity synchronized."""
    metadata = json.loads(
        (REPOSITORY_ROOT / "packaging" / "claude-mcpb" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert metadata["version"] == __version__
    assert metadata["author"] == {
        "name": "Gimbal Goats",
        "url": "https://github.com/GimbalGoats",
    }


def test_registry_publish_waits_for_the_exact_pypi_release() -> None:
    """Keep registry publication independent of whichever release is latest."""
    workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "publish-pypi.yml").read_text(
        encoding="utf-8"
    )

    assert "f\"https://pypi.org/pypi/maya-mcp/{os.environ['VERSION']}/json\"" in workflow
