"""Tests for env-gated Code Mode helpers."""

from __future__ import annotations

import pytest

from maya_mcp.code_mode import (
    CODE_MODE_ENV_VAR,
    CodeModeConfig,
    create_env_gated_server,
    is_code_mode_enabled,
    load_code_mode_config,
    require_code_mode,
    truncate_code_mode_output,
    validate_code_mode_execution,
)
from maya_mcp.errors import ValidationError


def test_code_mode_disabled_by_default() -> None:
    """Code Mode is off unless explicitly enabled."""

    config = load_code_mode_config({})

    assert config.enabled is False


def test_code_mode_requires_exact_one() -> None:
    """Only MAYA_MCP_CODE_MODE=1 enables Code Mode."""

    assert is_code_mode_enabled({CODE_MODE_ENV_VAR: "1"}) is True
    assert is_code_mode_enabled({CODE_MODE_ENV_VAR: " true "}) is False
    assert is_code_mode_enabled({CODE_MODE_ENV_VAR: "0"}) is False


def test_require_code_mode_rejects_disabled_config() -> None:
    """The explicit gate raises before Code Mode validation proceeds."""

    with pytest.raises(ValidationError, match="Code Mode is disabled"):
        require_code_mode(CodeModeConfig(enabled=False))


def test_create_env_gated_server_uses_default_factory_when_disabled() -> None:
    """Default server creation remains the fallback."""

    result = create_env_gated_server(
        default_factory=lambda: "default",
        code_mode_factory=lambda config: f"code:{config.enabled}",
        environ={},
    )

    assert result == "default"


def test_create_env_gated_server_uses_code_mode_factory_when_enabled() -> None:
    """Code Mode server creation requires the env flag."""

    result = create_env_gated_server(
        default_factory=lambda: "default",
        code_mode_factory=lambda config: f"code:{config.enabled}",
        environ={CODE_MODE_ENV_VAR: "1"},
    )

    assert result == "code:True"


def test_validate_code_mode_execution_accepts_python_with_defaults() -> None:
    """A small Python request gets the bounded default timeout."""

    request = validate_code_mode_execution(
        "print('ok')",
        config=CodeModeConfig(enabled=True),
    )

    assert request.code == "print('ok')"
    assert request.language == "python"
    assert request.timeout == 10


def test_validate_code_mode_execution_rejects_mel() -> None:
    """The prototype is Python-only."""

    with pytest.raises(ValidationError, match="Python execution only"):
        validate_code_mode_execution(
            "print `sphere`",
            language="mel",
            config=CodeModeConfig(enabled=True),
        )


def test_validate_code_mode_execution_rejects_oversized_code() -> None:
    """The code payload byte cap is enforced."""

    oversized_code = "x" * 16_385

    with pytest.raises(ValidationError, match="Code exceeds maximum size"):
        validate_code_mode_execution(oversized_code, config=CodeModeConfig(enabled=True))


def test_validate_code_mode_execution_rejects_timeout_over_limit() -> None:
    """Timeouts cannot exceed the Code Mode sandbox limit."""

    with pytest.raises(ValidationError, match="no more than 10 seconds"):
        validate_code_mode_execution(
            "print('ok')",
            timeout=11,
            config=CodeModeConfig(enabled=True),
        )


def test_truncate_code_mode_output_keeps_output_within_budget() -> None:
    """Oversized output is truncated with a clear marker."""

    output = truncate_code_mode_output("x" * 50_100)

    assert len(output.encode("utf-8")) <= 50_000
    assert output.endswith("[Code Mode output truncated]")
