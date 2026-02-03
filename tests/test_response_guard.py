"""Tests for response guard utility."""

from __future__ import annotations

from maya_mcp.utils.response_guard import (
    DEFAULT_MAX_RESPONSE_BYTES,
    estimate_json_size,
    guard_response_size,
)


class TestEstimateJsonSize:
    """Tests for estimate_json_size function."""

    def test_estimate_empty_dict(self) -> None:
        """Empty dict should have minimal size."""
        size = estimate_json_size({})
        assert size == 2  # {}

    def test_estimate_simple_dict(self) -> None:
        """Simple dict should estimate correctly."""
        data = {"key": "value"}
        size = estimate_json_size(data)
        assert size > 0
        assert size < 100  # Reasonable upper bound

    def test_estimate_list(self) -> None:
        """List should estimate correctly."""
        data = ["a", "b", "c"]
        size = estimate_json_size(data)
        assert size > 0

    def test_estimate_nested_structure(self) -> None:
        """Nested structure should estimate correctly."""
        data = {"nodes": ["node1", "node2"], "count": 2}
        size = estimate_json_size(data)
        assert size > 10

    def test_estimate_large_list(self) -> None:
        """Large list should have larger size."""
        small = {"nodes": ["a"] * 10}
        large = {"nodes": ["a"] * 1000}
        small_size = estimate_json_size(small)
        large_size = estimate_json_size(large)
        assert large_size > small_size


class TestGuardResponseSize:
    """Tests for guard_response_size function."""

    def test_small_response_unchanged(self) -> None:
        """Small responses should pass through unchanged."""
        response = {"nodes": ["a", "b", "c"], "count": 3}
        result = guard_response_size(response)
        assert result == response
        assert "_size_warning" not in result

    def test_large_response_truncated(self) -> None:
        """Large responses should be truncated."""
        # Create a response that exceeds the limit
        response = {
            "nodes": [f"very_long_node_name_{i:010d}" for i in range(5000)],
            "count": 5000,
        }
        result = guard_response_size(response, max_bytes=1000, list_key="nodes")

        assert "_size_warning" in result
        assert result["truncated"] is True
        assert result["count"] < 5000
        assert len(result["nodes"]) < 5000

    def test_truncation_adds_metadata(self) -> None:
        """Truncated responses should have metadata."""
        response = {
            "nodes": [f"node_{i}" for i in range(1000)],
            "count": 1000,
        }
        result = guard_response_size(response, max_bytes=500, list_key="nodes")

        assert "_size_warning" in result
        assert "_original_size" in result
        assert result["total_count"] == 1000

    def test_no_list_key_adds_warning_only(self) -> None:
        """Without list_key, should only add warning, not truncate."""
        response = {"data": "x" * 10000}
        result = guard_response_size(response, max_bytes=100)

        assert "_size_warning" in result
        assert result["data"] == response["data"]  # Not truncated

    def test_default_max_bytes_is_reasonable(self) -> None:
        """Default max bytes should be reasonable (50KB)."""
        assert DEFAULT_MAX_RESPONSE_BYTES == 50_000

    def test_respects_existing_truncated_flag(self) -> None:
        """Should respect and update existing truncated flag."""
        response = {
            "nodes": [f"node_{i}" for i in range(1000)],
            "count": 1000,
            "truncated": True,
            "total_count": 5000,
        }
        result = guard_response_size(response, max_bytes=500, list_key="nodes")

        # Should still be marked as truncated
        assert result["truncated"] is True
        # total_count should still reflect original
        assert result["total_count"] == 5000

    def test_non_list_value_with_list_key(self) -> None:
        """Non-list value with list_key should just add warning."""
        response = {"nodes": "not a list", "count": 1}
        result = guard_response_size(response, max_bytes=10, list_key="nodes")

        assert "_size_warning" in result
        assert result["nodes"] == "not a list"  # Unchanged


class TestGuardResponseSizeEdgeCases:
    """Edge case tests for guard_response_size."""

    def test_empty_list(self) -> None:
        """Empty list should pass through."""
        response = {"nodes": [], "count": 0}
        result = guard_response_size(response, max_bytes=10, list_key="nodes")
        assert result == response

    def test_exact_limit(self) -> None:
        """Response at exact limit should pass through."""
        response = {"a": "b"}
        size = estimate_json_size(response)
        result = guard_response_size(response, max_bytes=size)
        assert "_size_warning" not in result

    def test_unicode_content(self) -> None:
        """Unicode content should be handled correctly."""
        # Use explicit unicode escape to avoid linter warnings about ambiguous chars
        response = {"nodes": ["\u8282\u70b91", "\u0443\u0437\u0435\u043b2", "\u30ce\u30fc\u30c93"]}
        result = guard_response_size(response, max_bytes=1000, list_key="nodes")
        # Should handle without error
        assert "nodes" in result
