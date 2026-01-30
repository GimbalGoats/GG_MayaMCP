"""Integration tests for attributes tools.

These tests run against a real Maya instance with commandPort enabled.
They are automatically skipped if Maya is not available.
"""

from __future__ import annotations

import pytest

from maya_mcp.tools.attributes import attributes_get, attributes_set


@pytest.mark.integration
class TestAttributesGetIntegration:
    """Integration tests for attributes.get tool."""

    def test_get_required_fields(self, test_cube: str) -> None:
        """Response contains all required fields."""
        result = attributes_get(test_cube, ["translateX"])

        assert "node" in result
        assert "attributes" in result
        assert "count" in result
        assert "errors" in result

    def test_get_single_attribute(self, test_cube: str) -> None:
        """Get a single numeric attribute."""
        result = attributes_get(test_cube, ["translateX"])

        assert result["node"] == test_cube
        assert "translateX" in result["attributes"]
        assert isinstance(result["attributes"]["translateX"], (int, float))
        assert result["count"] == 1
        assert result["errors"] is None

    def test_get_multiple_attributes(self, test_cube: str) -> None:
        """Get multiple attributes in batch."""
        result = attributes_get(
            test_cube, ["translateX", "translateY", "translateZ", "visibility"]
        )

        assert result["node"] == test_cube
        assert result["count"] == 4
        assert "translateX" in result["attributes"]
        assert "translateY" in result["attributes"]
        assert "translateZ" in result["attributes"]
        assert "visibility" in result["attributes"]
        assert result["errors"] is None

    def test_get_boolean_attribute(self, test_cube: str) -> None:
        """Get a boolean attribute (visibility)."""
        result = attributes_get(test_cube, ["visibility"])

        assert result["attributes"]["visibility"] in (True, False, 0, 1)

    def test_get_nonexistent_attribute(self, test_cube: str) -> None:
        """Get returns error for nonexistent attribute."""
        result = attributes_get(test_cube, ["translateX", "nonExistentAttr"])

        assert result["count"] == 1
        assert "translateX" in result["attributes"]
        assert result["errors"] is not None
        assert "nonExistentAttr" in result["errors"]

    def test_get_nonexistent_node_raises(self, clean_scene: None) -> None:
        """Get raises ValueError for nonexistent node."""
        with pytest.raises(ValueError, match="does not exist"):
            attributes_get("definitelyDoesNotExist12345", ["translateX"])


@pytest.mark.integration
class TestAttributesSetIntegration:
    """Integration tests for attributes.set tool."""

    def test_set_required_fields(self, test_cube: str) -> None:
        """Response contains all required fields."""
        result = attributes_set(test_cube, {"translateX": 5.0})

        assert "node" in result
        assert "set" in result
        assert "count" in result
        assert "errors" in result

    def test_set_single_attribute(self, test_cube: str) -> None:
        """Set a single numeric attribute."""
        # Set a value
        set_result = attributes_set(test_cube, {"translateX": 42.5})

        assert set_result["node"] == test_cube
        assert "translateX" in set_result["set"]
        assert set_result["count"] == 1
        assert set_result["errors"] is None

        # Verify it was set
        get_result = attributes_get(test_cube, ["translateX"])
        assert abs(get_result["attributes"]["translateX"] - 42.5) < 0.001

    def test_set_multiple_attributes(self, test_cube: str) -> None:
        """Set multiple attributes in batch."""
        result = attributes_set(
            test_cube,
            {"translateX": 10.0, "translateY": 20.0, "translateZ": 30.0},
        )

        assert result["node"] == test_cube
        assert result["count"] == 3
        assert set(result["set"]) == {"translateX", "translateY", "translateZ"}
        assert result["errors"] is None

        # Verify values
        get_result = attributes_get(
            test_cube, ["translateX", "translateY", "translateZ"]
        )
        assert abs(get_result["attributes"]["translateX"] - 10.0) < 0.001
        assert abs(get_result["attributes"]["translateY"] - 20.0) < 0.001
        assert abs(get_result["attributes"]["translateZ"] - 30.0) < 0.001

    def test_set_boolean_attribute(self, test_cube: str) -> None:
        """Set a boolean attribute (visibility)."""
        # Set to False
        result = attributes_set(test_cube, {"visibility": False})
        assert result["count"] == 1
        assert result["errors"] is None

        # Verify
        get_result = attributes_get(test_cube, ["visibility"])
        assert get_result["attributes"]["visibility"] in (False, 0)

        # Set back to True
        result = attributes_set(test_cube, {"visibility": True})
        assert result["count"] == 1

    def test_set_nonexistent_attribute(self, test_cube: str) -> None:
        """Set returns error for nonexistent attribute."""
        result = attributes_set(
            test_cube, {"translateX": 5.0, "nonExistentAttr": 10.0}
        )

        assert result["count"] == 1
        assert "translateX" in result["set"]
        assert result["errors"] is not None
        assert "nonExistentAttr" in result["errors"]

    def test_set_nonexistent_node_raises(self, clean_scene: None) -> None:
        """Set raises ValueError for nonexistent node."""
        with pytest.raises(ValueError, match="does not exist"):
            attributes_set("definitelyDoesNotExist12345", {"translateX": 5.0})

    def test_set_rotation_attributes(self, test_cube: str) -> None:
        """Set rotation attributes (commonly used transform)."""
        result = attributes_set(
            test_cube, {"rotateX": 45.0, "rotateY": 90.0, "rotateZ": 180.0}
        )

        assert result["count"] == 3
        assert result["errors"] is None

        # Verify
        get_result = attributes_get(test_cube, ["rotateX", "rotateY", "rotateZ"])
        assert abs(get_result["attributes"]["rotateX"] - 45.0) < 0.001
        assert abs(get_result["attributes"]["rotateY"] - 90.0) < 0.001
        assert abs(get_result["attributes"]["rotateZ"] - 180.0) < 0.001

    def test_set_scale_attributes(self, test_cube: str) -> None:
        """Set scale attributes (commonly used transform)."""
        result = attributes_set(
            test_cube, {"scaleX": 2.0, "scaleY": 3.0, "scaleZ": 0.5}
        )

        assert result["count"] == 3
        assert result["errors"] is None

        # Verify
        get_result = attributes_get(test_cube, ["scaleX", "scaleY", "scaleZ"])
        assert abs(get_result["attributes"]["scaleX"] - 2.0) < 0.001
        assert abs(get_result["attributes"]["scaleY"] - 3.0) < 0.001
        assert abs(get_result["attributes"]["scaleZ"] - 0.5) < 0.001


@pytest.mark.integration
class TestAttributesRoundTrip:
    """Integration tests verifying get/set roundtrip behavior."""

    def test_get_set_get_roundtrip(self, test_cube: str) -> None:
        """Values survive a get→set→get roundtrip."""
        # Get original values
        original = attributes_get(
            test_cube, ["translateX", "translateY", "translateZ"]
        )

        # Set new values
        new_values = {"translateX": 100.0, "translateY": 200.0, "translateZ": 300.0}
        attributes_set(test_cube, new_values)

        # Get and verify new values
        updated = attributes_get(
            test_cube, ["translateX", "translateY", "translateZ"]
        )

        for attr, expected in new_values.items():
            assert abs(updated["attributes"][attr] - expected) < 0.001

        # Restore original values
        restore_values = {
            "translateX": original["attributes"]["translateX"],
            "translateY": original["attributes"]["translateY"],
            "translateZ": original["attributes"]["translateZ"],
        }
        attributes_set(test_cube, restore_values)
