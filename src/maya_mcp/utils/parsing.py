"""Response parsing utilities for Maya MCP.

This module provides shared helpers for parsing string responses returned by
Maya commandPort commands.
"""

from __future__ import annotations

import ast
import json
from typing import Any


def parse_json_response(response: str) -> Any:
    """Parse a Maya response string as JSON with a Python-literal fallback.

    Maya commandPort responses are expected to be JSON, but in some cases Maya
    may return Python literal syntax. This helper first attempts JSON parsing
    and falls back to ``ast.literal_eval`` for compatibility.

    Args:
        response: Raw response string returned by Maya commandPort.

    Returns:
        Parsed response object, commonly a dictionary or list.

    Raises:
        ValueError: If neither parser can parse the response.
        SyntaxError: If Python-literal fallback parsing fails due to syntax.
    """
    try:
        return json.loads(response)
    except (ValueError, json.JSONDecodeError):
        try:
            return ast.literal_eval(response)
        except (ValueError, SyntaxError):
            raise
