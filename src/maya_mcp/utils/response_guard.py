"""Response size guard utilities for Maya MCP.

This module provides utilities to guard against oversized responses that could
exceed LLM token budgets. It implements the output size guard pattern from
Block's MCP Playbook.

References:
    https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers
"""

from __future__ import annotations

import json
from typing import Any, TypeVar

# Default maximum response size in bytes (50KB - reasonable for most LLM contexts)
DEFAULT_MAX_RESPONSE_BYTES = 50_000

# Warning message template for truncated responses
TRUNCATION_WARNING = (
    "Response truncated: {original_size:,} bytes exceeded limit of "
    "{max_size:,} bytes. Use filters (pattern, node_type) or lower limit "
    "to reduce response size."
)

T = TypeVar("T")


def estimate_json_size(data: Any) -> int:
    """Estimate the JSON-serialized size of data in bytes.

    This is a fast estimate that avoids full serialization for simple cases.

    Args:
        data: Any JSON-serializable data.

    Returns:
        Estimated size in bytes.
    """
    # For accurate size, we need to serialize
    # This is called after the response is built, so the cost is acceptable
    try:
        return len(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    except (TypeError, ValueError):
        # Fallback for non-serializable data
        return len(str(data).encode("utf-8"))


def guard_response_size(
    response: dict[str, Any],
    max_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    list_key: str | None = None,
) -> dict[str, Any]:
    """Guard a response against excessive size.

    Checks if the response exceeds the maximum byte size. If so, and if a
    list_key is provided, truncates the list to fit within the limit and
    adds warning metadata.

    Args:
        response: The response dictionary to guard.
        max_bytes: Maximum allowed response size in bytes.
        list_key: Key of the list field to truncate if oversized.
            If None, only adds warning without truncation.

    Returns:
        The response, possibly truncated with added warning metadata:
            - _size_warning: Warning message about truncation
            - _original_size: Original size in bytes
            - _truncated_size: Size after truncation

    Example:
        >>> result = {"nodes": ["node1", "node2", ...], "count": 1000}
        >>> guarded = guard_response_size(result, max_bytes=1000, list_key="nodes")
        >>> if "_size_warning" in guarded:
        ...     print("Response was truncated!")
    """
    original_size = estimate_json_size(response)

    if original_size <= max_bytes:
        return response

    # Response is too large - need to truncate
    if list_key is None or list_key not in response:
        # Can't truncate, just add warning
        response["_size_warning"] = TRUNCATION_WARNING.format(
            original_size=original_size,
            max_size=max_bytes,
        )
        response["_original_size"] = original_size
        return response

    # Truncate the list to fit
    original_list = response[list_key]
    if not isinstance(original_list, list):
        response["_size_warning"] = TRUNCATION_WARNING.format(
            original_size=original_size,
            max_size=max_bytes,
        )
        response["_original_size"] = original_size
        return response

    # Binary search to find the right truncation point
    low, high = 0, len(original_list)
    best_fit = 0

    while low <= high:
        mid = (low + high) // 2
        test_response = response.copy()
        test_response[list_key] = original_list[:mid]

        if list_key == "nodes" or "count" in response:
            test_response["count"] = mid

        test_size = estimate_json_size(test_response)

        if test_size <= max_bytes:
            best_fit = mid
            low = mid + 1
        else:
            high = mid - 1

    # Apply truncation
    truncated_list = original_list[:best_fit]
    response[list_key] = truncated_list

    # Update count if present
    if "count" in response:
        response["count"] = len(truncated_list)

    # Mark as truncated if not already
    if "truncated" not in response or not response["truncated"]:
        response["truncated"] = True
        response["total_count"] = len(original_list)

    truncated_size = estimate_json_size(response)

    response["_size_warning"] = TRUNCATION_WARNING.format(
        original_size=original_size,
        max_size=max_bytes,
    )
    response["_original_size"] = original_size
    response["_truncated_size"] = truncated_size

    return response
