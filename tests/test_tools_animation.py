"""Tests for animation tools.

These tests verify the MCP tools for keyframing, timeline control,
and playback range management work correctly with mocked transport.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from maya_mcp.tools.animation import (
    animation_delete_keyframes,
    animation_get_keyframes,
    animation_get_time_range,
    animation_set_keyframe,
    animation_set_time,
    animation_set_time_range,
)


class TestAnimationSetTime:
    """Tests for the animation.set_time tool."""

    def test_set_time_success(self) -> None:
        """Set time navigates to the specified frame."""
        mock_client = MagicMock()
        mock_response = json.dumps({"time": 24.0, "errors": None})
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_set_time(24.0)

        assert result["time"] == 24.0
        assert result["errors"] is None

    def test_set_time_no_update(self) -> None:
        """Set time with update=False does not update viewport."""
        mock_client = MagicMock()
        mock_response = json.dumps({"time": 10.0, "errors": None})
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_set_time(10.0, update=False)

        assert result["time"] == 10.0
        assert result["errors"] is None
        mock_client.execute.assert_called_once()

    def test_set_time_negative_frame(self) -> None:
        """Set time works with negative frame numbers."""
        mock_client = MagicMock()
        mock_response = json.dumps({"time": -5.0, "errors": None})
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_set_time(-5.0)

        assert result["time"] == -5.0
        assert result["errors"] is None

    def test_set_time_maya_error(self) -> None:
        """Set time returns error on Maya exception."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {"time": None, "errors": {"_exception": "Runtime error"}}
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_set_time(999.0)

        assert result["time"] is None
        assert result["errors"]["_exception"] == "Runtime error"


class TestAnimationGetTimeRange:
    """Tests for the animation.get_time_range tool."""

    def test_get_time_range_success(self) -> None:
        """Get time range returns all playback info."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "current_time": 1.0,
                "min_time": 1.0,
                "max_time": 120.0,
                "animation_start": 1.0,
                "animation_end": 200.0,
                "fps": 24,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_get_time_range()

        assert result["current_time"] == 1.0
        assert result["min_time"] == 1.0
        assert result["max_time"] == 120.0
        assert result["animation_start"] == 1.0
        assert result["animation_end"] == 200.0
        assert result["fps"] == 24
        assert result["errors"] is None

    def test_get_time_range_ntsc(self) -> None:
        """Get time range returns FPS for NTSC setting."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "current_time": 0.0,
                "min_time": 0.0,
                "max_time": 48.0,
                "animation_start": 0.0,
                "animation_end": 48.0,
                "fps": 30,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_get_time_range()

        assert result["fps"] == 30
        assert result["errors"] is None

    def test_get_time_range_maya_error(self) -> None:
        """Get time range returns error on Maya exception."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "current_time": None,
                "min_time": None,
                "max_time": None,
                "animation_start": None,
                "animation_end": None,
                "fps": None,
                "errors": {"_exception": "Not connected"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_get_time_range()

        assert result["errors"]["_exception"] == "Not connected"


class TestAnimationSetTimeRange:
    """Tests for the animation.set_time_range tool."""

    def test_set_time_range_success(self) -> None:
        """Set time range updates playback and animation range."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "min_time": 1.0,
                "max_time": 100.0,
                "animation_start": 1.0,
                "animation_end": 100.0,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_set_time_range(1.0, 100.0)

        assert result["min_time"] == 1.0
        assert result["max_time"] == 100.0
        assert result["animation_start"] == 1.0
        assert result["animation_end"] == 100.0
        assert result["errors"] is None

    def test_set_time_range_with_animation_range(self) -> None:
        """Set time range with explicit animation start/end."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "min_time": 10.0,
                "max_time": 50.0,
                "animation_start": 1.0,
                "animation_end": 100.0,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_set_time_range(
                10.0, 50.0, animation_start=1.0, animation_end=100.0
            )

        assert result["min_time"] == 10.0
        assert result["max_time"] == 50.0
        assert result["animation_start"] == 1.0
        assert result["animation_end"] == 100.0
        assert result["errors"] is None

    def test_set_time_range_min_ge_max_raises(self) -> None:
        """Set time range raises ValueError if min_time >= max_time."""
        with pytest.raises(ValueError, match=r"min_time.*must be less than.*max_time"):
            animation_set_time_range(100.0, 100.0)

    def test_set_time_range_min_gt_max_raises(self) -> None:
        """Set time range raises ValueError if min_time > max_time."""
        with pytest.raises(ValueError, match=r"min_time.*must be less than.*max_time"):
            animation_set_time_range(200.0, 100.0)

    def test_set_time_range_anim_start_gt_min_raises(self) -> None:
        """Set time range raises ValueError if animation_start > min_time."""
        with pytest.raises(ValueError, match=r"animation_start.*must be <= min_time"):
            animation_set_time_range(10.0, 100.0, animation_start=20.0)

    def test_set_time_range_anim_end_lt_max_raises(self) -> None:
        """Set time range raises ValueError if animation_end < max_time."""
        with pytest.raises(ValueError, match=r"animation_end.*must be >= max_time"):
            animation_set_time_range(1.0, 100.0, animation_end=50.0)

    def test_set_time_range_maya_error(self) -> None:
        """Set time range returns error on Maya exception."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "min_time": None,
                "max_time": None,
                "animation_start": None,
                "animation_end": None,
                "errors": {"_exception": "playbackOptions failed"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_set_time_range(1.0, 100.0)

        assert result["errors"]["_exception"] == "playbackOptions failed"


class TestAnimationSetKeyframe:
    """Tests for the animation.set_keyframe tool."""

    def test_set_keyframe_success(self) -> None:
        """Set keyframe creates keyframe on specified attributes."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "attributes": ["translateY"],
                "time": 10.0,
                "keyframe_count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_set_keyframe("pCube1", attributes=["translateY"], time=10.0)

        assert result["node"] == "pCube1"
        assert result["attributes"] == ["translateY"]
        assert result["time"] == 10.0
        assert result["keyframe_count"] == 1
        assert result["errors"] is None

    def test_set_keyframe_with_value(self) -> None:
        """Set keyframe with explicit value."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "attributes": ["translateY"],
                "time": 5.0,
                "keyframe_count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_set_keyframe(
                "pCube1", attributes=["translateY"], time=5.0, value=3.5
            )

        assert result["keyframe_count"] == 1
        assert result["errors"] is None

    def test_set_keyframe_all_keyable(self) -> None:
        """Set keyframe on all keyable attributes when attributes=None."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "attributes": ["translateX", "translateY", "translateZ"],
                "time": 1.0,
                "keyframe_count": 3,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_set_keyframe("pCube1")

        assert result["keyframe_count"] == 3
        assert len(result["attributes"]) == 3
        assert result["errors"] is None

    def test_set_keyframe_with_tangent_types(self) -> None:
        """Set keyframe with specific tangent types."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "attributes": ["translateY"],
                "time": 1.0,
                "keyframe_count": 1,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_set_keyframe(
                "pCube1",
                attributes=["translateY"],
                in_tangent_type="linear",
                out_tangent_type="flat",
            )

        assert result["keyframe_count"] == 1
        assert result["errors"] is None

    def test_set_keyframe_invalid_node_name(self) -> None:
        """Set keyframe raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            animation_set_keyframe("pCube1;bad")

    def test_set_keyframe_invalid_attribute_name(self) -> None:
        """Set keyframe raises ValueError for invalid attribute name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            animation_set_keyframe("pCube1", attributes=["translate;Y"])

    def test_set_keyframe_empty_attributes_raises(self) -> None:
        """Set keyframe raises ValueError for empty attributes list."""
        with pytest.raises(ValueError, match="attributes list cannot be empty"):
            animation_set_keyframe("pCube1", attributes=[])

    def test_set_keyframe_invalid_in_tangent_type(self) -> None:
        """Set keyframe raises ValueError for invalid in_tangent_type."""
        with pytest.raises(ValueError, match="Invalid in_tangent_type"):
            animation_set_keyframe("pCube1", in_tangent_type="invalid")

    def test_set_keyframe_invalid_out_tangent_type(self) -> None:
        """Set keyframe raises ValueError for invalid out_tangent_type."""
        with pytest.raises(ValueError, match="Invalid out_tangent_type"):
            animation_set_keyframe("pCube1", out_tangent_type="badtype")

    def test_set_keyframe_nonexistent_node(self) -> None:
        """Set keyframe returns error for nonexistent node."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "nonexistent",
                "attributes": [],
                "time": None,
                "keyframe_count": 0,
                "errors": {"_node": "Node 'nonexistent' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_set_keyframe("nonexistent", attributes=["translateY"])

        assert result["keyframe_count"] == 0
        assert result["errors"]["_node"] == "Node 'nonexistent' does not exist"

    def test_set_keyframe_maya_error(self) -> None:
        """Set keyframe returns error on Maya exception."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "attributes": [],
                "time": None,
                "keyframe_count": 0,
                "errors": {"_exception": "setKeyframe failed"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_set_keyframe("pCube1", attributes=["badAttr"])

        assert result["errors"]["_exception"] == "setKeyframe failed"


class TestAnimationGetKeyframes:
    """Tests for the animation.get_keyframes tool."""

    def test_get_keyframes_success(self) -> None:
        """Get keyframes returns keyframe data for animated attributes."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "keyframes": {
                    "translateY": [
                        {"time": 1.0, "value": 0.0},
                        {"time": 10.0, "value": 5.0},
                        {"time": 24.0, "value": 0.0},
                    ]
                },
                "attribute_count": 1,
                "total_keyframe_count": 3,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_get_keyframes("pCube1", attributes=["translateY"])

        assert result["node"] == "pCube1"
        assert result["attribute_count"] == 1
        assert result["total_keyframe_count"] == 3
        assert len(result["keyframes"]["translateY"]) == 3
        assert result["keyframes"]["translateY"][0]["time"] == 1.0
        assert result["keyframes"]["translateY"][1]["value"] == 5.0
        assert result["errors"] is None

    def test_get_keyframes_with_time_range(self) -> None:
        """Get keyframes filters by time range."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "keyframes": {
                    "translateY": [
                        {"time": 5.0, "value": 2.0},
                        {"time": 10.0, "value": 5.0},
                    ]
                },
                "attribute_count": 1,
                "total_keyframe_count": 2,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_get_keyframes(
                "pCube1",
                attributes=["translateY"],
                time_range_start=5.0,
                time_range_end=15.0,
            )

        assert result["total_keyframe_count"] == 2
        assert result["errors"] is None

    def test_get_keyframes_all_animated(self) -> None:
        """Get keyframes returns all animated attributes when attributes=None."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "keyframes": {
                    "translateX": [{"time": 1.0, "value": 0.0}],
                    "translateY": [{"time": 1.0, "value": 0.0}],
                    "rotateZ": [{"time": 1.0, "value": 0.0}],
                },
                "attribute_count": 3,
                "total_keyframe_count": 3,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_get_keyframes("pCube1")

        assert result["attribute_count"] == 3
        assert result["total_keyframe_count"] == 3
        assert result["errors"] is None

    def test_get_keyframes_no_animation(self) -> None:
        """Get keyframes returns empty data for non-animated node."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "keyframes": {},
                "attribute_count": 0,
                "total_keyframe_count": 0,
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_get_keyframes("pCube1")

        assert result["attribute_count"] == 0
        assert result["total_keyframe_count"] == 0
        assert result["keyframes"] == {}
        assert result["errors"] is None

    def test_get_keyframes_invalid_node_name(self) -> None:
        """Get keyframes raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            animation_get_keyframes("pCube1;bad")

    def test_get_keyframes_invalid_attribute_name(self) -> None:
        """Get keyframes raises ValueError for invalid attribute name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            animation_get_keyframes("pCube1", attributes=["translate;Y"])

    def test_get_keyframes_empty_attributes_raises(self) -> None:
        """Get keyframes raises ValueError for empty attributes list."""
        with pytest.raises(ValueError, match="attributes list cannot be empty"):
            animation_get_keyframes("pCube1", attributes=[])

    def test_get_keyframes_nonexistent_node(self) -> None:
        """Get keyframes returns error for nonexistent node."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "nonexistent",
                "keyframes": {},
                "attribute_count": 0,
                "total_keyframe_count": 0,
                "errors": {"_node": "Node 'nonexistent' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_get_keyframes("nonexistent")

        assert result["errors"]["_node"] == "Node 'nonexistent' does not exist"


class TestAnimationDeleteKeyframes:
    """Tests for the animation.delete_keyframes tool."""

    def test_delete_keyframes_success(self) -> None:
        """Delete keyframes removes keyframes and returns count."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "deleted_count": 3,
                "attributes": ["translateY"],
                "time_range": "all",
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_delete_keyframes("pCube1", attributes=["translateY"])

        assert result["node"] == "pCube1"
        assert result["deleted_count"] == 3
        assert result["attributes"] == ["translateY"]
        assert result["time_range"] == "all"
        assert result["errors"] is None

    def test_delete_keyframes_with_time_range(self) -> None:
        """Delete keyframes respects time range."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "deleted_count": 2,
                "attributes": ["translateY"],
                "time_range": [5.0, 15.0],
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_delete_keyframes(
                "pCube1",
                attributes=["translateY"],
                time_range_start=5.0,
                time_range_end=15.0,
            )

        assert result["deleted_count"] == 2
        assert result["time_range"] == [5.0, 15.0]
        assert result["errors"] is None

    def test_delete_keyframes_all_attributes(self) -> None:
        """Delete keyframes on all animated attributes when attributes=None."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "deleted_count": 9,
                "attributes": ["translateX", "translateY", "translateZ"],
                "time_range": "all",
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_delete_keyframes("pCube1")

        assert result["deleted_count"] == 9
        assert len(result["attributes"]) == 3
        assert result["errors"] is None

    def test_delete_keyframes_invalid_node_name(self) -> None:
        """Delete keyframes raises ValueError for invalid node name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            animation_delete_keyframes("pCube1;bad")

    def test_delete_keyframes_invalid_attribute_name(self) -> None:
        """Delete keyframes raises ValueError for invalid attribute name."""
        with pytest.raises(ValueError, match="Invalid characters"):
            animation_delete_keyframes("pCube1", attributes=["translate;Y"])

    def test_delete_keyframes_empty_attributes_raises(self) -> None:
        """Delete keyframes raises ValueError for empty attributes list."""
        with pytest.raises(ValueError, match="attributes list cannot be empty"):
            animation_delete_keyframes("pCube1", attributes=[])

    def test_delete_keyframes_nonexistent_node(self) -> None:
        """Delete keyframes returns error for nonexistent node."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "nonexistent",
                "deleted_count": 0,
                "attributes": [],
                "time_range": "all",
                "errors": {"_node": "Node 'nonexistent' does not exist"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_delete_keyframes("nonexistent")

        assert result["deleted_count"] == 0
        assert result["errors"]["_node"] == "Node 'nonexistent' does not exist"

    def test_delete_keyframes_maya_error(self) -> None:
        """Delete keyframes returns error on Maya exception."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "node": "pCube1",
                "deleted_count": 0,
                "attributes": [],
                "time_range": "all",
                "errors": {"_exception": "cutKey failed"},
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.animation.get_client", return_value=mock_client):
            result = animation_delete_keyframes("pCube1")

        assert result["errors"]["_exception"] == "cutKey failed"
