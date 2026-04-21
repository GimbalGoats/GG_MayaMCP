"""Tests for server entrypoint behavior."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_server_script_executes_without_shadowing_stdlib_types() -> None:
    """Running the server file directly should not shadow stdlib ``types``."""
    repo_root = Path(__file__).resolve().parents[1]
    server_path = repo_root / "src" / "maya_mcp" / "server.py"
    env = os.environ.copy()
    env["MAYA_MCP_SKIP_RUN"] = "1"

    result = subprocess.run(
        [sys.executable, str(server_path)],
        cwd=repo_root,
        capture_output=True,
        check=False,
        env=env,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
