"""Tests for scene saving tools (scene.save and scene.save_as)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from maya_mcp.errors import ValidationError
from maya_mcp.tools.scene import scene_save, scene_save_as


class TestSceneSave:
    """Tests for the scene.save tool."""

    def test_scene_save_success(self) -> None:
        """Save succeeds when scene has a name."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": True,
                "file_path": "C:/projects/test.ma",
                "error": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            result = scene_save()

        assert result["success"] is True
        assert result["file_path"] == "C:/projects/test.ma"
        assert result["error"] is None

    def test_scene_save_untitled(self) -> None:
        """Save fails when scene is untitled."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": False,
                "file_path": None,
                "error": "Scene is untitled. Use scene.save_as to save for the first time.",
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            result = scene_save()

        assert result["success"] is False
        assert result["file_path"] is None
        assert "Scene is untitled" in result["error"]

    def test_scene_save_error(self) -> None:
        """Save handles Maya errors gracefully."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": False,
                "file_path": None,
                "error": "Some Maya error occurred",
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            result = scene_save()

        assert result["success"] is False
        assert result["error"] == "Some Maya error occurred"


class TestSceneSaveAs:
    """Tests for the scene.save_as tool."""

    def test_scene_save_as_success_ascii(self) -> None:
        """Save as succeeds for .ma files."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": True,
                "file_path": "C:/projects/new_scene.ma",
                "error": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            result = scene_save_as("C:/projects/new_scene.ma")

        assert result["success"] is True
        assert result["file_path"] == "C:/projects/new_scene.ma"
        assert result["error"] is None

        # Verify command used correct type
        # Verify command contains logic for mayaAscii
        call_arg = mock_client.execute.call_args[0][0]
        assert 'file_type = "mayaAscii"' in call_arg
        assert 'if file_path.lower().endswith(".ma")' in call_arg
        # Our implementation uses python logic to determine type, so check if it's in the command
        # Actually, the command string is constructed with logic inside.
        # Let's check if the logic is correct in the test or implementation.
        # The tool builds a python script.

    def test_scene_save_as_success_binary(self) -> None:
        """Save as succeeds for .mb files."""
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": True,
                "file_path": "C:/projects/new_scene.mb",
                "error": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            result = scene_save_as("C:/projects/new_scene.mb")

        assert result["success"] is True

    def test_scene_save_as_validation_empty(self) -> None:
        """Save as rejects empty path."""
        with pytest.raises(ValidationError, match="must not be empty"):
            scene_save_as("")

    def test_scene_save_as_validation_extension(self) -> None:
        """Save as rejects unsupported extension."""
        with pytest.raises(ValidationError, match="Unsupported file extension"):
            scene_save_as("test.fbx")

    def test_scene_save_as_validation_chars(self) -> None:
        """Save as rejects forbidden characters."""
        with pytest.raises(ValidationError, match="forbidden character"):
            scene_save_as("test;rm.ma")

    def test_scene_save_as_command_structure(self) -> None:
        """Verify the generated Maya command structure."""
        mock_client = MagicMock()
        mock_client.execute.return_value = json.dumps({"success": True})

        with patch("maya_mcp.tools.scene.get_client", return_value=mock_client):
            scene_save_as("C:/test.ma")

        cmd = mock_client.execute.call_args[0][0]
        assert "cmds.file(rename=file_path)" in cmd
        assert "cmds.file(save=True, type=file_type)" in cmd
        assert 'file_type = "mayaAscii"' in cmd or 'file_path.lower().endswith(".ma")' in cmd
