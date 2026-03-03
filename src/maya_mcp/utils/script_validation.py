"""Script path and code validation for Maya MCP.

Security-focused validation for script file paths and raw code inputs.
"""

from __future__ import annotations

import re
from pathlib import Path

from maya_mcp.errors import ValidationError
from maya_mcp.utils.validation import FORBIDDEN_PATH_CHARS

# Windows device names that must be rejected
_WINDOWS_DEVICE_NAMES = frozenset(
    [
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    ]
)


def validate_script_path(file_path: str, allowed_dirs: tuple[Path, ...]) -> Path:
    """Validate a script file path against allowed directories.

    Performs security checks including:
    - Forbidden characters and control characters
    - UNC path rejection
    - NTFS alternate data stream rejection
    - Windows device name rejection
    - Must be absolute path with .py extension
    - Must resolve to within an allowed directory (handles symlinks)

    Args:
        file_path: The script file path to validate.
        allowed_dirs: Tuple of allowed parent directories.

    Returns:
        The resolved Path object.

    Raises:
        ValidationError: If the path fails any security check.
    """
    if not file_path or not isinstance(file_path, str):
        raise ValidationError(
            message="Script path must be a non-empty string",
            field_name="file_path",
            value=str(file_path)[:50] if file_path else "",
            constraint="non-empty string",
        )

    # Check for forbidden characters
    if any(c in file_path for c in FORBIDDEN_PATH_CHARS):
        raise ValidationError(
            message="Script path contains forbidden characters",
            field_name="file_path",
            value=file_path[:50],
            constraint="no shell metacharacters",
        )

    # Check for control characters
    if any(ord(c) < 32 for c in file_path):
        raise ValidationError(
            message="Script path contains control characters",
            field_name="file_path",
            value=repr(file_path[:50]),
            constraint="no control characters",
        )

    # Reject UNC paths
    if file_path.startswith("\\\\") or file_path.startswith("//"):
        raise ValidationError(
            message="UNC paths are not allowed",
            field_name="file_path",
            value=file_path[:50],
            constraint="no UNC paths",
        )

    # Reject NTFS alternate data streams
    if re.search(r":[^/\\]", file_path[2:]):  # Skip drive letter colon
        raise ValidationError(
            message="NTFS alternate data streams are not allowed",
            field_name="file_path",
            value=file_path[:50],
            constraint="no ADS",
        )

    path = Path(file_path)

    # Must be absolute
    if not path.is_absolute():
        raise ValidationError(
            message="Script path must be absolute",
            field_name="file_path",
            value=file_path[:50],
            constraint="absolute path",
        )

    # Must be .py extension
    if path.suffix.lower() != ".py":
        raise ValidationError(
            message="Script must have .py extension",
            field_name="file_path",
            value=file_path[:50],
            constraint=".py extension",
        )

    # Reject Windows device names
    stem = path.stem.upper()
    if stem in _WINDOWS_DEVICE_NAMES:
        raise ValidationError(
            message="Windows device names are not allowed",
            field_name="file_path",
            value=file_path[:50],
            constraint="no device names",
        )

    # Resolve and check containment (handles symlinks via strict=True)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ValidationError(
            message=f"Script path cannot be resolved: {exc}",
            field_name="file_path",
            value=file_path[:50],
            constraint="resolvable path",
        ) from exc

    # Check that resolved path is within an allowed directory
    if not allowed_dirs:
        raise ValidationError(
            message="No script directories configured (set MAYA_MCP_SCRIPT_DIRS)",
            field_name="file_path",
            value=file_path[:50],
            constraint="allowed directory",
        )

    for allowed_dir in allowed_dirs:
        try:
            resolved.relative_to(allowed_dir)
            return resolved
        except ValueError:
            continue

    raise ValidationError(
        message="Script path is not within any allowed directory",
        field_name="file_path",
        value=file_path[:50],
        constraint="allowed directory containment",
    )


def validate_raw_code(code: str, max_bytes: int) -> str:
    """Validate raw code for execution.

    Args:
        code: The code string to validate.
        max_bytes: Maximum allowed size in bytes.

    Returns:
        The validated code string.

    Raises:
        ValidationError: If the code fails validation.
    """
    if not code or not isinstance(code, str):
        raise ValidationError(
            message="Code must be a non-empty string",
            field_name="code",
            value="",
            constraint="non-empty string",
        )

    code_bytes = len(code.encode("utf-8"))
    if code_bytes > max_bytes:
        raise ValidationError(
            message=f"Code exceeds maximum size ({code_bytes} bytes > {max_bytes} bytes)",
            field_name="code",
            value=f"{code_bytes} bytes",
            constraint=f"max {max_bytes} bytes",
        )

    return code
