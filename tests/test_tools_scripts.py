"""Tests for script execution tools.

These tests verify the MCP tools for listing, executing, and running
scripts work correctly with mocked transport and filesystem.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import get_type_hints
from unittest.mock import MagicMock, patch

import pytest

from maya_mcp.errors import ValidationError
from maya_mcp.tools.scripts import (
    ScriptExecuteOutput,
    ScriptListOutput,
    ScriptRunOutput,
    script_execute,
    script_list,
    script_run,
)
from maya_mcp.utils.script_config import (
    ScriptConfig,
    load_script_config,
    reset_script_config,
)
from maya_mcp.utils.script_validation import validate_raw_code, validate_script_path


class TestScriptOutputTypes:
    """Tests for public script TypedDict return annotations."""

    def test_script_tools_use_typed_outputs(self) -> None:
        """Script tools expose typed output models."""
        assert get_type_hints(script_list)["return"] is ScriptListOutput
        assert get_type_hints(script_execute)["return"] is ScriptExecuteOutput
        assert get_type_hints(script_run)["return"] is ScriptRunOutput

    def test_script_list_marks_truncation_optional(self) -> None:
        """Script listing payloads preserve optional guard metadata."""
        assert "truncated" in ScriptListOutput.__optional_keys__
        assert "_size_warning" in ScriptListOutput.__optional_keys__


class TestScriptConfig:
    """Tests for script configuration loading."""

    def setup_method(self) -> None:
        reset_script_config()

    def teardown_method(self) -> None:
        reset_script_config()

    def test_default_config(self) -> None:
        """Default config has no dirs and raw execution disabled."""
        with patch.dict(os.environ, {}, clear=True):
            config = load_script_config()
        assert config.script_dirs == ()
        assert config.raw_execution_enabled is False
        assert config.script_timeout == 60

    def test_script_dirs_parsed(self, tmp_path: Path) -> None:
        """Script dirs are parsed from semicolon-separated env var."""
        dir1 = tmp_path / "scripts1"
        dir2 = tmp_path / "scripts2"
        dir1.mkdir()
        dir2.mkdir()

        with patch.dict(os.environ, {"MAYA_MCP_SCRIPT_DIRS": f"{dir1};{dir2}"}):
            config = load_script_config()

        assert len(config.script_dirs) == 2
        assert dir1 in config.script_dirs
        assert dir2 in config.script_dirs

    def test_nonexistent_dirs_skipped(self, tmp_path: Path) -> None:
        """Non-existent directories are silently skipped."""
        good_dir = tmp_path / "exists"
        good_dir.mkdir()
        bad_dir = tmp_path / "nope"

        with patch.dict(os.environ, {"MAYA_MCP_SCRIPT_DIRS": f"{good_dir};{bad_dir}"}):
            config = load_script_config()

        assert len(config.script_dirs) == 1
        assert good_dir in config.script_dirs

    def test_raw_execution_enabled(self) -> None:
        """Raw execution flag parsed correctly."""
        with patch.dict(os.environ, {"MAYA_MCP_ENABLE_RAW_EXECUTION": "true"}):
            config = load_script_config()
        assert config.raw_execution_enabled is True

        with patch.dict(os.environ, {"MAYA_MCP_ENABLE_RAW_EXECUTION": "1"}):
            config = load_script_config()
        assert config.raw_execution_enabled is True

        with patch.dict(os.environ, {"MAYA_MCP_ENABLE_RAW_EXECUTION": "false"}):
            config = load_script_config()
        assert config.raw_execution_enabled is False

    def test_custom_timeout(self) -> None:
        """Custom timeout parsed from env var."""
        with patch.dict(os.environ, {"MAYA_MCP_SCRIPT_TIMEOUT": "120"}):
            config = load_script_config()
        assert config.script_timeout == 120

    def test_invalid_timeout_defaults(self) -> None:
        """Invalid timeout values default to 60."""
        with patch.dict(os.environ, {"MAYA_MCP_SCRIPT_TIMEOUT": "abc"}):
            config = load_script_config()
        assert config.script_timeout == 60


class TestScriptPathValidation:
    """Tests for script path validation."""

    def test_valid_path(self, tmp_path: Path) -> None:
        """Valid path within allowed directory passes."""
        script = tmp_path / "test.py"
        script.write_text("print('hello')")

        result = validate_script_path(str(script), (tmp_path,))
        assert result == script.resolve()

    def test_empty_path_rejected(self) -> None:
        """Empty path is rejected."""
        with pytest.raises(ValidationError, match="non-empty string"):
            validate_script_path("", (Path("/tmp"),))

    def test_forbidden_chars_rejected(self, tmp_path: Path) -> None:
        """Forbidden characters in path are rejected."""
        with pytest.raises(ValidationError, match="forbidden characters"):
            validate_script_path(f"{tmp_path}/test;bad.py", (tmp_path,))

    def test_control_chars_rejected(self, tmp_path: Path) -> None:
        """Control characters in path are rejected."""
        with pytest.raises(ValidationError, match="control characters"):
            validate_script_path(f"{tmp_path}/test\x00.py", (tmp_path,))

    def test_unc_path_rejected(self) -> None:
        """UNC paths are rejected."""
        with pytest.raises(ValidationError, match="UNC"):
            validate_script_path("\\\\server\\share\\test.py", (Path("/tmp"),))

    def test_relative_path_rejected(self) -> None:
        """Relative paths are rejected."""
        with pytest.raises(ValidationError, match="absolute"):
            validate_script_path("scripts/test.py", (Path("/tmp"),))

    def test_wrong_extension_rejected(self, tmp_path: Path) -> None:
        """Non-.py extension is rejected."""
        script = tmp_path / "test.txt"
        script.write_text("hello")
        with pytest.raises(ValidationError, match=r"\.py extension"):
            validate_script_path(str(script), (tmp_path,))

    def test_device_name_rejected(self, tmp_path: Path) -> None:
        """Windows device names are rejected."""
        with pytest.raises(ValidationError, match="device names"):
            validate_script_path(str(tmp_path / "CON.py"), (tmp_path,))

    def test_path_outside_allowed_dirs(self, tmp_path: Path) -> None:
        """Path outside allowed directories is rejected."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        script = outside / "test.py"
        script.write_text("print('hello')")

        with pytest.raises(ValidationError, match="not within any allowed"):
            validate_script_path(str(script), (allowed,))

    def test_no_allowed_dirs(self, tmp_path: Path) -> None:
        """Empty allowed dirs raises error."""
        script = tmp_path / "test.py"
        script.write_text("print('hello')")

        with pytest.raises(ValidationError, match="No script directories"):
            validate_script_path(str(script), ())

    def test_nonexistent_file_rejected(self, tmp_path: Path) -> None:
        """Non-existent file is rejected."""
        with pytest.raises(ValidationError, match="cannot be resolved"):
            validate_script_path(str(tmp_path / "nope.py"), (tmp_path,))


class TestRawCodeValidation:
    """Tests for raw code validation."""

    def test_valid_code(self) -> None:
        """Valid code passes validation."""
        result = validate_raw_code("print('hello')", 1000)
        assert result == "print('hello')"

    def test_empty_code_rejected(self) -> None:
        """Empty code is rejected."""
        with pytest.raises(ValidationError, match="non-empty"):
            validate_raw_code("", 1000)

    def test_oversized_code_rejected(self) -> None:
        """Code exceeding max bytes is rejected."""
        code = "x" * 1001
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_raw_code(code, 1000)


class TestScriptList:
    """Tests for the script.list tool."""

    def test_list_scripts(self, tmp_path: Path) -> None:
        """Script list finds .py files in configured dirs."""
        (tmp_path / "hello.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("x = 1")
        (tmp_path / "_private.py").write_text("# skip me")
        (tmp_path / "readme.txt").write_text("not a script")

        config = ScriptConfig(script_dirs=(tmp_path,))

        with patch("maya_mcp.tools.scripts.get_script_config", return_value=config):
            result = script_list()

        assert result["count"] == 2
        names = [s["name"] for s in result["scripts"]]
        assert "hello.py" in names
        assert "utils.py" in names
        assert "_private.py" not in names
        assert result["errors"] is None

    def test_list_no_dirs_configured(self) -> None:
        """Script list returns error when no dirs configured."""
        config = ScriptConfig()

        with patch("maya_mcp.tools.scripts.get_script_config", return_value=config):
            result = script_list()

        assert result["count"] == 0
        assert "_config" in result["errors"]

    def test_list_subdirectories(self, tmp_path: Path) -> None:
        """Script list finds scripts in subdirectories."""
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "nested.py").write_text("print('nested')")
        (tmp_path / "top.py").write_text("print('top')")

        config = ScriptConfig(script_dirs=(tmp_path,))

        with patch("maya_mcp.tools.scripts.get_script_config", return_value=config):
            result = script_list()

        assert result["count"] == 2


class TestScriptExecute:
    """Tests for the script.execute tool."""

    def test_execute_success(self, tmp_path: Path) -> None:
        """Script execute runs a valid script file."""
        script = tmp_path / "test.py"
        script.write_text("print('hello from script')")

        config = ScriptConfig(script_dirs=(tmp_path,))
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": True,
                "script": str(script),
                "output": "hello from script\n",
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with (
            patch("maya_mcp.tools.scripts.get_script_config", return_value=config),
            patch("maya_mcp.tools.scripts.get_client", return_value=mock_client),
        ):
            result = script_execute(str(script))

        assert result["success"] is True
        assert result["output"] == "hello from script\n"
        assert result["errors"] is None

    def test_execute_with_args(self, tmp_path: Path) -> None:
        """Script execute injects __args__ into script namespace."""
        script = tmp_path / "test.py"
        script.write_text("print(__args__['msg'])")

        config = ScriptConfig(script_dirs=(tmp_path,))
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": True,
                "script": str(script),
                "output": "hello\n",
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with (
            patch("maya_mcp.tools.scripts.get_script_config", return_value=config),
            patch("maya_mcp.tools.scripts.get_client", return_value=mock_client),
        ):
            result = script_execute(str(script), args={"msg": "hello"})

        assert result["success"] is True
        # Verify args were injected into the command
        cmd = mock_client.execute.call_args[0][0]
        assert '"msg"' in cmd

    def test_execute_invalid_path(self) -> None:
        """Script execute rejects paths outside allowed dirs."""
        config = ScriptConfig(script_dirs=())

        with (
            patch("maya_mcp.tools.scripts.get_script_config", return_value=config),
            pytest.raises(ValidationError),
        ):
            script_execute("/some/bad/path.py")

    def test_execute_file_too_large(self, tmp_path: Path) -> None:
        """Script execute rejects files exceeding size limit."""
        script = tmp_path / "big.py"
        script.write_bytes(b"x" * 1_048_577)

        config = ScriptConfig(script_dirs=(tmp_path,))

        with (
            patch("maya_mcp.tools.scripts.get_script_config", return_value=config),
            pytest.raises(ValidationError, match="too large"),
        ):
            script_execute(str(script))


class TestScriptRun:
    """Tests for the script.run tool."""

    def test_run_python_success(self) -> None:
        """Script run executes Python code."""
        config = ScriptConfig(raw_execution_enabled=True)
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": True,
                "output": "hello\n",
                "language": "python",
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with (
            patch("maya_mcp.tools.scripts.get_script_config", return_value=config),
            patch("maya_mcp.tools.scripts.get_client", return_value=mock_client),
        ):
            result = script_run("print('hello')")

        assert result["success"] is True
        assert result["output"] == "hello\n"
        assert result["language"] == "python"

    def test_run_mel_success(self) -> None:
        """Script run executes MEL code."""
        config = ScriptConfig(raw_execution_enabled=True)
        mock_client = MagicMock()
        mock_response = json.dumps(
            {
                "success": True,
                "output": "42",
                "language": "mel",
                "errors": None,
            }
        )
        mock_client.execute.return_value = mock_response

        with (
            patch("maya_mcp.tools.scripts.get_script_config", return_value=config),
            patch("maya_mcp.tools.scripts.get_client", return_value=mock_client),
        ):
            result = script_run("int $x = 42;", language="mel")

        assert result["success"] is True
        assert result["language"] == "mel"

    def test_run_disabled_raises(self) -> None:
        """Script run raises when raw execution is disabled."""
        config = ScriptConfig(raw_execution_enabled=False)

        with (
            patch("maya_mcp.tools.scripts.get_script_config", return_value=config),
            pytest.raises(ValidationError, match="disabled"),
        ):
            script_run("print('hello')")

    def test_run_empty_code_raises(self) -> None:
        """Script run raises for empty code."""
        config = ScriptConfig(raw_execution_enabled=True)

        with (
            patch("maya_mcp.tools.scripts.get_script_config", return_value=config),
            pytest.raises(ValidationError, match="non-empty"),
        ):
            script_run("")

    def test_run_oversized_code_raises(self) -> None:
        """Script run raises for oversized code."""
        config = ScriptConfig(raw_execution_enabled=True)

        with (
            patch("maya_mcp.tools.scripts.get_script_config", return_value=config),
            pytest.raises(ValidationError, match="exceeds maximum"),
        ):
            script_run("x" * 102_401)
