"""Response parsing utilities for Maya MCP.

This module provides shared helpers for parsing string responses returned by
Maya commandPort commands.
"""

from __future__ import annotations

import ast
import json
from typing import Any


def _response_candidates(response: str) -> list[str]:
    stripped = response.strip()
    if not stripped:
        return []

    candidates: list[str] = [stripped]
    parts = [part.strip() for part in stripped.replace("\x00", "\n").splitlines() if part.strip()]
    for part in parts:
        if part not in candidates:
            candidates.append(part)
    for part in reversed(parts):
        if part.startswith(("{", "[")) and part not in candidates:
            candidates.append(part)

    for open_char, close_char in (("{", "}"), ("[", "]")):
        start = stripped.find(open_char)
        end = stripped.rfind(close_char)
        if start != -1 and end != -1 and end > start:
            candidate = stripped[start : end + 1].strip()
            if candidate and candidate not in candidates:
                candidates.append(candidate)
    return candidates


def parse_json_response(response: str) -> Any:
    """Parse a Maya response string as JSON with a Python-literal fallback.

    Maya commandPort responses are expected to be JSON, but in some cases Maya
    may include extra log lines before the payload or return Python literal
    syntax. This helper tries the full response first, then JSON-like fragments,
    and finally falls back to ``ast.literal_eval`` for compatibility.

    Args:
        response: Raw response string returned by Maya commandPort.

    Returns:
        Parsed response object, commonly a dictionary or list.

    Raises:
        ValueError: If neither parser can parse the response.
        SyntaxError: If Python-literal fallback parsing fails due to syntax.
    """
    last_error: Exception | None = None
    for candidate in _response_candidates(response):
        try:
            return json.loads(candidate)
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
        try:
            return ast.literal_eval(candidate)
        except (ValueError, SyntaxError) as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise ValueError("Empty response")
