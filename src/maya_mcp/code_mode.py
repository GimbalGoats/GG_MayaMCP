"""Opt-in Code Mode helpers for Maya MCP.

Code Mode is an experimental profile for future server wiring. It is not
enabled by default and must be explicitly selected with ``MAYA_MCP_CODE_MODE=1``.
The helpers in this module keep the gate and prototype sandbox limits separate
from the default MCP server registration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, TypeVar

from maya_mcp.errors import ValidationError
from maya_mcp.utils.script_validation import validate_raw_code

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

CODE_MODE_ENV_VAR = "MAYA_MCP_CODE_MODE"
CODE_MODE_ENABLED_VALUE = "1"
CODE_MODE_MAX_CODE_BYTES = 16_384
CODE_MODE_MAX_TIMEOUT_SECONDS = 10
CODE_MODE_MAX_OUTPUT_BYTES = 50_000

CodeModeLanguage = Literal["python"]
ServerT = TypeVar("ServerT")


@dataclass(frozen=True)
class CodeModeSandboxLimits:
    """Sandbox limits for the Code Mode prototype.

    Attributes:
        max_code_bytes: Maximum UTF-8 size of a single submitted code payload.
        max_timeout_seconds: Maximum execution timeout for a single request.
        max_output_bytes: Maximum UTF-8 size of returned text output.
        allowed_languages: Languages allowed by the prototype.
    """

    max_code_bytes: int = CODE_MODE_MAX_CODE_BYTES
    max_timeout_seconds: int = CODE_MODE_MAX_TIMEOUT_SECONDS
    max_output_bytes: int = CODE_MODE_MAX_OUTPUT_BYTES
    allowed_languages: tuple[CodeModeLanguage, ...] = ("python",)


@dataclass(frozen=True)
class CodeModeConfig:
    """Configuration resolved from the process environment.

    Attributes:
        enabled: Whether Code Mode is explicitly enabled.
        sandbox: Fixed prototype sandbox limits.
    """

    enabled: bool
    sandbox: CodeModeSandboxLimits = field(default_factory=CodeModeSandboxLimits)


@dataclass(frozen=True)
class CodeModeExecutionRequest:
    """Validated Code Mode execution request.

    Attributes:
        code: Validated Python code payload.
        language: Validated execution language.
        timeout: Effective timeout in seconds.
    """

    code: str
    language: CodeModeLanguage
    timeout: int


def is_code_mode_enabled(environ: Mapping[str, str] | None = None) -> bool:
    """Return whether Code Mode is explicitly enabled.

    Args:
        environ: Optional environment mapping. Defaults to ``os.environ``.

    Returns:
        ``True`` only when ``MAYA_MCP_CODE_MODE`` is exactly ``1`` after
        surrounding whitespace is stripped.
    """

    env = os.environ if environ is None else environ
    return env.get(CODE_MODE_ENV_VAR, "").strip() == CODE_MODE_ENABLED_VALUE


def load_code_mode_config(environ: Mapping[str, str] | None = None) -> CodeModeConfig:
    """Load Code Mode configuration from an environment mapping.

    Args:
        environ: Optional environment mapping. Defaults to ``os.environ``.

    Returns:
        Code Mode configuration with fixed sandbox limits.
    """

    return CodeModeConfig(enabled=is_code_mode_enabled(environ))


def require_code_mode(environ: Mapping[str, str] | None = None) -> CodeModeConfig:
    """Require Code Mode to be explicitly enabled.

    Args:
        environ: Optional environment mapping. Defaults to ``os.environ``.

    Returns:
        The enabled configuration.

    Raises:
        ValidationError: If Code Mode is not enabled.
    """

    active_config = load_code_mode_config(environ)
    if not active_config.enabled:
        raise ValidationError(
            message=f"Code Mode is disabled. Set {CODE_MODE_ENV_VAR}=1 to enable.",
            field_name=CODE_MODE_ENV_VAR,
            value="",
            constraint=f"{CODE_MODE_ENV_VAR}=1",
        )
    return active_config


def create_env_gated_server(
    default_factory: Callable[[], ServerT],
    code_mode_factory: Callable[[CodeModeConfig], ServerT],
    environ: Mapping[str, str] | None = None,
) -> ServerT:
    """Create the default server or the opt-in Code Mode server.

    This helper is intentionally independent from ``maya_mcp.server`` so future
    wiring can opt into Code Mode without changing default tool registration.

    Args:
        default_factory: Factory for the normal Maya MCP server.
        code_mode_factory: Factory for the Code Mode server profile.
        environ: Optional environment mapping. Defaults to ``os.environ``.

    Returns:
        A server instance from ``code_mode_factory`` only when
        ``MAYA_MCP_CODE_MODE=1``; otherwise a normal server instance.
    """

    config = load_code_mode_config(environ)
    if config.enabled:
        return code_mode_factory(config)
    return default_factory()


def validate_code_mode_execution(
    code: str,
    language: str = "python",
    timeout: int | None = None,
    environ: Mapping[str, str] | None = None,
) -> CodeModeExecutionRequest:
    """Validate a Code Mode execution request against the prototype limits.

    Args:
        code: Python code payload.
        language: Requested execution language.
        timeout: Optional timeout in seconds.
        environ: Optional environment mapping. Defaults to ``os.environ``.

    Returns:
        A validated execution request.

    Raises:
        ValidationError: If Code Mode is disabled or any sandbox limit is
            exceeded.
    """

    active_config = require_code_mode(environ)
    limits = active_config.sandbox

    if language not in limits.allowed_languages:
        raise ValidationError(
            message="Code Mode currently supports Python execution only",
            field_name="language",
            value=language,
            constraint="python",
        )

    validated_code = validate_raw_code(code, limits.max_code_bytes)
    effective_timeout = limits.max_timeout_seconds if timeout is None else timeout
    if effective_timeout <= 0 or effective_timeout > limits.max_timeout_seconds:
        raise ValidationError(
            message=(
                "Code Mode timeout must be greater than 0 and no more than "
                f"{limits.max_timeout_seconds} seconds"
            ),
            field_name="timeout",
            value=str(effective_timeout),
            constraint=f"1..{limits.max_timeout_seconds}",
        )

    return CodeModeExecutionRequest(
        code=validated_code,
        language="python",
        timeout=effective_timeout,
    )


def truncate_code_mode_output(output: str) -> str:
    """Truncate text output to the Code Mode output budget.

    Args:
        output: Text output returned by execution.

    Returns:
        The original output if it fits, otherwise a UTF-8-safe truncated string
        with a short truncation marker.
    """

    limits = CodeModeSandboxLimits()
    output_bytes = output.encode("utf-8")
    if len(output_bytes) <= limits.max_output_bytes:
        return output

    marker = "\n[Code Mode output truncated]"
    marker_bytes = marker.encode("utf-8")
    budget = max(0, limits.max_output_bytes - len(marker_bytes))
    truncated = output_bytes[:budget].decode("utf-8", errors="ignore")
    return f"{truncated}{marker}"
