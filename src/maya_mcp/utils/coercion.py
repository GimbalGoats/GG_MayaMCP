"""Parameter coercion utilities for MCP tool inputs.

MCP clients may send list/dict parameters as JSON strings instead of
native Python objects. These utilities handle transparent deserialization
so tool implementations receive the correct types.
"""

from __future__ import annotations

import json
from typing import Any, overload


@overload
def coerce_list(value: None) -> None: ...


@overload
def coerce_list(value: list[Any] | str) -> list[Any]: ...


def coerce_list(value: list[Any] | str | None) -> list[Any] | None:
    """Coerce a value to a list, parsing JSON strings if needed.

    Args:
        value: A list (passthrough), JSON string to parse, or None.

    Returns:
        The parsed list, or None if value is None.

    Raises:
        TypeError: If the parsed JSON is not a list.
        ValueError: If the string is not valid JSON.
    """
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON string for list parameter: {exc}") from exc
        if not isinstance(parsed, list):
            raise TypeError(f"Expected list, got {type(parsed).__name__}")
        return parsed
    raise TypeError(f"Expected list or JSON string, got {type(value).__name__}")


@overload
def coerce_dict(value: None) -> None: ...


@overload
def coerce_dict(value: dict[str, Any] | str) -> dict[str, Any]: ...


def coerce_dict(value: dict[str, Any] | str | None) -> dict[str, Any] | None:
    """Coerce a value to a dict, parsing JSON strings if needed.

    Args:
        value: A dict (passthrough), JSON string to parse, or None.

    Returns:
        The parsed dict, or None if value is None.

    Raises:
        TypeError: If the parsed JSON is not a dict.
        ValueError: If the string is not valid JSON.
    """
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON string for dict parameter: {exc}") from exc
        if not isinstance(parsed, dict):
            raise TypeError(f"Expected dict, got {type(parsed).__name__}")
        return parsed
    raise TypeError(f"Expected dict or JSON string, got {type(value).__name__}")
