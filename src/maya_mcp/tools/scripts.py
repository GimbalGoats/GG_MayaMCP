"""Script execution tools for Maya MCP.

This module provides tools for listing, executing, and running scripts
in Maya with a three-tier trust model:
    - Tier 1 (script.list): Read-only listing of scripts from allowed dirs
    - Tier 2 (script.execute): Execute validated .py files from allowed dirs
    - Tier 3 (script.run): Execute raw Python/MEL code (requires opt-in)
"""

from __future__ import annotations

import contextlib
import json
from typing import TYPE_CHECKING, Any, Literal, cast

from typing_extensions import TypedDict

if TYPE_CHECKING:
    from collections.abc import Iterator

    from maya_mcp.transport.commandport import CommandPortClient

from maya_mcp.errors import ValidationError
from maya_mcp.transport import get_client
from maya_mcp.utils.parsing import parse_json_response
from maya_mcp.utils.response_guard import guard_response_size
from maya_mcp.utils.script_config import (
    MAX_RAW_CODE_BYTES,
    MAX_SCRIPT_FILE_BYTES,
    get_script_config,
)
from maya_mcp.utils.script_validation import validate_raw_code, validate_script_path

# Maximum number of scripts to enumerate before stopping.
_MAX_SCRIPT_SCAN = 500


class _GuardedOutput(TypedDict, total=False):
    """Metadata added when response size guards truncate a payload."""

    truncated: bool
    total_count: int
    _size_warning: str
    _original_size: int
    _truncated_size: int


class ScriptListEntry(TypedDict):
    """A discovered script file."""

    name: str
    path: str
    size_bytes: int
    relative_path: str


class ScriptListOutput(_GuardedOutput):
    """Return payload for the script.list tool."""

    scripts: list[ScriptListEntry]
    count: int
    directories: list[str]
    errors: dict[str, str] | None


class ScriptExecuteOutput(TypedDict):
    """Return payload for the script.execute tool."""

    success: bool
    script: str
    output: str
    errors: dict[str, str] | None


class ScriptRunOutput(TypedDict):
    """Return payload for the script.run tool."""

    success: bool
    output: str
    language: Literal["python", "mel"]
    errors: dict[str, str] | None


@contextlib.contextmanager
def _override_timeout(client: CommandPortClient, timeout: float) -> Iterator[CommandPortClient]:
    """Temporarily override a client's command timeout."""
    original = client.config.command_timeout
    if timeout != original:
        client.config.command_timeout = timeout
    try:
        yield client
    finally:
        if timeout != original:
            client.config.command_timeout = original


def script_list() -> ScriptListOutput:
    """List available Python scripts from configured directories.

    Scans MAYA_MCP_SCRIPT_DIRS for .py files, excluding underscore-prefixed
    files. This is a server-side operation that does not require a Maya
    connection.

    Returns:
        Dictionary with script listing:
            - scripts: List of script info dicts (name, path, size_bytes, relative_path)
            - count: Number of scripts found
            - directories: List of configured script directories
            - errors: Error details if any, or None
    """
    config = get_script_config()

    result: dict[str, Any] = {
        "scripts": [],
        "count": 0,
        "directories": [str(d) for d in config.script_dirs],
        "errors": None,
    }

    if not config.script_dirs:
        result["errors"] = {
            "_config": "No script directories configured (set MAYA_MCP_SCRIPT_DIRS)"
        }
        return cast("ScriptListOutput", result)

    scripts: list[dict[str, Any]] = []
    scan_errors: dict[str, str] = {}
    capped = False

    for script_dir in config.script_dirs:
        if capped:
            break
        try:
            resolved_dir = script_dir.resolve()
            for py_file in resolved_dir.rglob("*.py"):
                if len(scripts) >= _MAX_SCRIPT_SCAN:
                    capped = True
                    break
                # Skip underscore-prefixed files
                if py_file.name.startswith("_"):
                    continue
                try:
                    rel_path = py_file.relative_to(resolved_dir)
                    scripts.append(
                        {
                            "name": py_file.name,
                            "path": str(py_file),
                            "size_bytes": py_file.stat().st_size,
                            "relative_path": str(rel_path),
                        }
                    )
                except (OSError, ValueError):
                    continue
        except OSError as e:
            scan_errors[str(script_dir)] = str(e)

    result["scripts"] = scripts
    result["count"] = len(scripts)

    if scan_errors:
        result["errors"] = scan_errors

    return cast("ScriptListOutput", guard_response_size(result, list_key="scripts"))


def script_execute(
    file_path: str,
    args: dict[str, Any] | None = None,
    timeout: int | None = None,
) -> ScriptExecuteOutput:
    """Execute a Python script file in Maya.

    The script must be within a configured MAYA_MCP_SCRIPT_DIRS directory.
    The script is read server-side and sent to Maya for execution. An
    ``__args__`` dict is injected into the script namespace.

    Args:
        file_path: Absolute path to the .py script file.
        args: Optional arguments dict injected as ``__args__`` in the script.
        timeout: Optional timeout override in seconds.

    Returns:
        Dictionary with execution result:
            - success: Whether execution completed without error
            - script: Path of the executed script
            - output: Captured stdout from the script
            - errors: Error details if any, or None

    Raises:
        ValidationError: If the path fails security validation.
    """
    config = get_script_config()
    resolved = validate_script_path(file_path, config.script_dirs)

    # Read script content server-side (single read avoids stat+read TOCTOU)
    raw_bytes = resolved.read_bytes()
    if len(raw_bytes) > MAX_SCRIPT_FILE_BYTES:
        raise ValidationError(
            message=f"Script file too large ({len(raw_bytes)} bytes > {MAX_SCRIPT_FILE_BYTES} bytes)",
            field_name="file_path",
            value=str(resolved)[:50],
            constraint=f"max {MAX_SCRIPT_FILE_BYTES} bytes",
        )

    script_content = raw_bytes.decode("utf-8")
    effective_timeout = timeout if timeout is not None else config.script_timeout

    client = get_client()
    code_escaped = json.dumps(script_content)
    args_escaped = json.dumps(args) if args is not None else "None"
    path_escaped = json.dumps(str(resolved))

    command = f"""
import sys
import json
from io import StringIO

_code = {code_escaped}
_args = {args_escaped}
_script_path = {path_escaped}

result = {{"success": False, "script": _script_path, "output": "", "errors": {{}}}}

try:
    _old_stdout = sys.stdout
    _capture = StringIO()
    sys.stdout = _capture

    try:
        _globals = {{"__args__": _args if _args is not None else {{}}, "__name__": "__main__"}}
        exec(_code, _globals)
        result["success"] = True
    except Exception as e:
        result["errors"]["_exception"] = type(e).__name__ + ": " + str(e)
    finally:
        sys.stdout = _old_stdout
        result["output"] = _capture.getvalue()

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    with _override_timeout(client, float(effective_timeout)):
        response = client.execute(command)

    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return cast("ScriptExecuteOutput", parsed)


def script_run(
    code: str,
    language: Literal["python", "mel"] = "python",
    timeout: int | None = None,
) -> ScriptRunOutput:
    """Execute raw Python or MEL code in Maya.

    This tool requires MAYA_MCP_ENABLE_RAW_EXECUTION=true to be set.
    Use with caution — raw execution has no sandboxing.

    Args:
        code: The code to execute.
        language: Code language ("python" or "mel").
        timeout: Optional timeout override in seconds.

    Returns:
        Dictionary with execution result:
            - success: Whether execution completed without error
            - output: Captured stdout from execution
            - language: The language used
            - errors: Error details if any, or None

    Raises:
        ValidationError: If raw execution is disabled or code exceeds size limit.
    """
    config = get_script_config()

    if not config.raw_execution_enabled:
        raise ValidationError(
            message="Raw code execution is disabled. "
            "Set MAYA_MCP_ENABLE_RAW_EXECUTION=true to enable.",
            field_name="code",
            value="",
            constraint="raw execution enabled",
        )

    validate_raw_code(code, MAX_RAW_CODE_BYTES)

    effective_timeout = timeout if timeout is not None else config.script_timeout
    client = get_client()
    code_escaped = json.dumps(code)

    if language == "mel":
        # Wrap MEL execution in Python
        command = f"""
import sys
import json
import maya.mel
from io import StringIO

_code = {code_escaped}

result = {{"success": False, "output": "", "language": "mel", "errors": {{}}}}

try:
    _old_stdout = sys.stdout
    _capture = StringIO()
    sys.stdout = _capture

    try:
        mel_result = maya.mel.eval(_code)
        if mel_result is not None:
            _capture.write(str(mel_result))
        result["success"] = True
    except Exception as e:
        result["errors"]["_exception"] = type(e).__name__ + ": " + str(e)
    finally:
        sys.stdout = _old_stdout
        result["output"] = _capture.getvalue()

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""
    else:
        command = f"""
import sys
import json
from io import StringIO

_code = {code_escaped}

result = {{"success": False, "output": "", "language": "python", "errors": {{}}}}

try:
    _old_stdout = sys.stdout
    _capture = StringIO()
    sys.stdout = _capture

    try:
        exec(_code, {{"__name__": "__main__"}})
        result["success"] = True
    except Exception as e:
        result["errors"]["_exception"] = type(e).__name__ + ": " + str(e)
    finally:
        sys.stdout = _old_stdout
        result["output"] = _capture.getvalue()

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    with _override_timeout(client, float(effective_timeout)):
        response = client.execute(command)

    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return cast("ScriptRunOutput", parsed)
