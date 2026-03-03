"""Script execution configuration for Maya MCP.

Configuration is loaded from environment variables:
    - MAYA_MCP_SCRIPT_DIRS: Semicolon-separated list of absolute directory paths
    - MAYA_MCP_ENABLE_RAW_EXECUTION: Set to "true" or "1" to enable raw code execution
    - MAYA_MCP_SCRIPT_TIMEOUT: Timeout in seconds for script execution (default 60)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

MAX_SCRIPT_FILE_BYTES = 1_048_576  # 1 MB
MAX_RAW_CODE_BYTES = 102_400  # 100 KB


@dataclass(frozen=True)
class ScriptConfig:
    """Configuration for script execution tools.

    Attributes:
        script_dirs: List of allowed directories for script execution.
        raw_execution_enabled: Whether raw code execution (Tier 3) is enabled.
        script_timeout: Timeout in seconds for script execution.
    """

    script_dirs: tuple[Path, ...] = field(default_factory=tuple)
    raw_execution_enabled: bool = False
    script_timeout: int = 60


def load_script_config() -> ScriptConfig:
    """Load script configuration from environment variables.

    Returns:
        ScriptConfig populated from environment variables.
    """
    # Parse script directories
    dirs_str = os.environ.get("MAYA_MCP_SCRIPT_DIRS", "")
    script_dirs: list[Path] = []
    if dirs_str:
        for d in dirs_str.split(";"):
            d = d.strip()
            if not d:
                continue
            path = Path(d)
            if path.is_absolute() and path.is_dir():
                script_dirs.append(path)

    # Parse raw execution flag
    raw_str = os.environ.get("MAYA_MCP_ENABLE_RAW_EXECUTION", "").lower()
    raw_execution_enabled = raw_str in ("true", "1")

    # Parse timeout
    timeout_str = os.environ.get("MAYA_MCP_SCRIPT_TIMEOUT", "60")
    try:
        script_timeout = int(timeout_str)
        if script_timeout <= 0:
            script_timeout = 60
    except ValueError:
        script_timeout = 60

    return ScriptConfig(
        script_dirs=tuple(script_dirs),
        raw_execution_enabled=raw_execution_enabled,
        script_timeout=script_timeout,
    )


# Singleton
_config: ScriptConfig | None = None


def get_script_config() -> ScriptConfig:
    """Get the cached script configuration singleton.

    Returns:
        The global ScriptConfig instance.
    """
    global _config
    if _config is None:
        _config = load_script_config()
    return _config


def reset_script_config() -> None:
    """Reset the cached configuration. Used for testing."""
    global _config
    _config = None
