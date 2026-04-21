"""Registrar for script tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Literal

from mcp.types import ToolAnnotations

from maya_mcp.tools.scripts import (  # noqa: TC001
    ScriptExecuteOutput,
    ScriptListOutput,
    ScriptRunOutput,
)
from maya_mcp.utils.coercion import coerce_dict

if TYPE_CHECKING:
    from fastmcp import FastMCP


def tool_script_list() -> ScriptListOutput:
    """List available scripts.

    Returns:
        Dictionary with scripts list, count, directories, and errors.
    """
    from maya_mcp.tools.scripts import script_list as _script_list

    return _script_list()


def tool_script_execute(
    file_path: Annotated[str, "Absolute path to the .py script file"],
    args: Annotated[
        dict[str, Any] | None,
        "Optional arguments dict injected as __args__ in the script namespace",
    ] = None,
    timeout: Annotated[
        int | None,
        "Optional timeout override in seconds (default from MAYA_MCP_SCRIPT_TIMEOUT)",
    ] = None,
) -> ScriptExecuteOutput:
    """Execute a Python script file in Maya.

    Args:
        file_path: Absolute path to the .py script.
        args: Optional arguments dict.
        timeout: Optional timeout override.

    Returns:
        Dictionary with success, script, output, and errors.
    """
    from maya_mcp.tools.scripts import script_execute as _script_execute

    return _script_execute(file_path=file_path, args=coerce_dict(args), timeout=timeout)


def tool_script_run(
    code: Annotated[str, "Python or MEL code to execute"],
    language: Annotated[
        Literal["python", "mel"],
        "Code language (default: python)",
    ] = "python",
    timeout: Annotated[
        int | None,
        "Optional timeout override in seconds (default from MAYA_MCP_SCRIPT_TIMEOUT)",
    ] = None,
) -> ScriptRunOutput:
    """Execute raw Python or MEL code in Maya.

    Args:
        code: Code to execute.
        language: Code language (python or mel).
        timeout: Optional timeout override.

    Returns:
        Dictionary with success, output, language, and errors.
    """
    from maya_mcp.tools.scripts import script_run as _script_run

    return _script_run(code=code, language=language, timeout=timeout)


def register_script_tools(mcp: FastMCP) -> None:
    """Register script tools."""
    mcp.tool(
        name="script.list",
        description="List available Python scripts from configured MAYA_MCP_SCRIPT_DIRS directories. "
        "Read-only, does not require Maya connection.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_script_list)

    mcp.tool(
        name="script.execute",
        description="Execute a Python script file in Maya from an allowed MAYA_MCP_SCRIPT_DIRS directory. "
        "The script is read server-side and sent to Maya. "
        "Optional args dict is injected as __args__ in the script namespace.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_script_execute)

    mcp.tool(
        name="script.run",
        description="Execute raw Python or MEL code in Maya. "
        "REQUIRES MAYA_MCP_ENABLE_RAW_EXECUTION=true environment variable. "
        "Disabled by default for security.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_script_run)
