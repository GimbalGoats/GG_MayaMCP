"""Tests for parameter coercion utilities."""

from __future__ import annotations

import pytest

from maya_mcp.utils.coercion import coerce_dict, coerce_list


class TestCoerceList:
    """Tests for coerce_list."""

    def test_passthrough_list(self) -> None:
        assert coerce_list(["a", "b"]) == ["a", "b"]

    def test_passthrough_empty_list(self) -> None:
        assert coerce_list([]) == []

    def test_none_returns_none(self) -> None:
        assert coerce_list(None) is None

    def test_json_string_parsed(self) -> None:
        assert coerce_list('["a", "b"]') == ["a", "b"]

    def test_json_string_floats(self) -> None:
        assert coerce_list("[1.0, 2.0, 3.0]") == [1.0, 2.0, 3.0]

    def test_json_string_nested(self) -> None:
        result = coerce_list('[{"vertex_id": 0, "weights": {"joint1": 0.5}}]')
        assert result == [{"vertex_id": 0, "weights": {"joint1": 0.5}}]

    def test_json_string_empty_list(self) -> None:
        assert coerce_list("[]") == []

    def test_json_string_dict_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="Expected list"):
            coerce_list('{"key": "value"}')

    def test_json_string_scalar_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="Expected list"):
            coerce_list('"just a string"')

    def test_invalid_json_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid JSON"):
            coerce_list("not valid json")

    def test_non_string_non_list_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="Expected list or JSON string"):
            coerce_list(42)  # type: ignore[arg-type]


class TestCoerceDict:
    """Tests for coerce_dict."""

    def test_passthrough_dict(self) -> None:
        assert coerce_dict({"a": 1}) == {"a": 1}

    def test_passthrough_empty_dict(self) -> None:
        assert coerce_dict({}) == {}

    def test_none_returns_none(self) -> None:
        assert coerce_dict(None) is None

    def test_json_string_parsed(self) -> None:
        assert coerce_dict('{"a": 1, "b": 2}') == {"a": 1, "b": 2}

    def test_json_string_nested(self) -> None:
        result = coerce_dict('{"translateX": 1.0, "visibility": true}')
        assert result == {"translateX": 1.0, "visibility": True}

    def test_json_string_empty_dict(self) -> None:
        assert coerce_dict("{}") == {}

    def test_json_string_list_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="Expected dict"):
            coerce_dict("[1, 2, 3]")

    def test_json_string_scalar_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="Expected dict"):
            coerce_dict("42")

    def test_invalid_json_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid JSON"):
            coerce_dict("not valid json")

    def test_non_string_non_dict_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="Expected dict or JSON string"):
            coerce_dict([1, 2])  # type: ignore[arg-type]
