"""Registrar for scene tools."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated, Literal

from mcp.types import ToolAnnotations

from maya_mcp.registrars._progress import report_progress
from maya_mcp.tools.scene import (
    SCENE_UNSAVED_CHANGES_ERROR,
    SceneExportOutput,
    SceneImportOutput,
    SceneInfoOutput,
    SceneNewOutput,
    SceneOpenOutput,
    SceneRedoOutput,
    SceneSaveAsOutput,
    SceneSaveOutput,
    SceneUndoOutput,
    scene_export,
    scene_import,
    scene_info,
    scene_new,
    scene_open,
    scene_redo,
    scene_save,
    scene_save_as,
    scene_undo,
)

if TYPE_CHECKING:
    from fastmcp import Context, FastMCP
else:
    from importlib import import_module

    Context = import_module("fastmcp").Context


def _supports_form_elicitation(ctx: Context) -> bool:
    """Return whether the negotiated client capabilities allow form elicitation."""
    try:
        client_params = ctx.session.client_params
    except RuntimeError:
        return False

    if client_params is None:
        return False

    elicitation = client_params.capabilities.elicitation
    if elicitation is None:
        return False

    # Per the MCP spec, an empty elicitation capability object implies form support.
    return elicitation.form is not None or elicitation.url is None


def _is_unsaved_changes_refusal(
    result: SceneNewOutput | SceneOpenOutput,
) -> bool:
    """Return whether a scene tool result represents the standard unsaved-changes refusal."""
    return (
        result["success"] is False
        and result["was_modified"] is True
        and result["error"] == SCENE_UNSAVED_CHANGES_ERROR
    )


async def _confirm_discard_unsaved_changes(ctx: Context, operation: str) -> bool:
    """Prompt the user to discard unsaved changes when the client supports elicitation."""
    result = await ctx.session.elicit_form(
        message=(
            f"The current Maya scene has unsaved changes. "
            f"Discard those changes and continue with {operation}?"
        ),
        requestedSchema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["discard", "cancel"],
                    "title": "Action",
                    "description": "Choose whether to discard unsaved changes and continue.",
                }
            },
            "required": ["action"],
            "additionalProperties": False,
        },
        related_request_id=ctx.request_id,
    )
    return (
        result.action == "accept"
        and result.content is not None
        and result.content.get("action") == "discard"
    )


def tool_scene_info() -> SceneInfoOutput:
    """Get current scene information.

    Returns file path, modification status, FPS, frame range, and up axis.
    """
    return scene_info()


async def tool_scene_new(
    force: Annotated[
        bool,
        "If True, discard unsaved changes. If False (default), refuse when scene has unsaved changes.",
    ] = False,
    ctx: Context | None = None,
) -> SceneNewOutput:
    """Create a new empty Maya scene.

    Args:
        force: If True, discard unsaved changes and create new scene.
            If False (default), refuse when scene has unsaved changes.
        ctx: FastMCP request context, used for capability-gated elicitation.

    Returns:
        Dictionary with success, previous_file, was_modified, and error.
    """
    result = await asyncio.to_thread(scene_new, force=force)
    if force or ctx is None or not _is_unsaved_changes_refusal(result):
        return result
    if not _supports_form_elicitation(ctx):
        return result
    if not await _confirm_discard_unsaved_changes(ctx, "creating a new scene"):
        return result
    return await asyncio.to_thread(scene_new, force=True)


def tool_scene_save() -> SceneSaveOutput:
    """Save the current Maya scene.

    Returns:
        Dictionary with success, file_path, and error.
    """
    return scene_save()


def tool_scene_save_as(
    file_path: Annotated[
        str,
        "Absolute or relative path to save the scene to (.ma or .mb)",
    ],
) -> SceneSaveAsOutput:
    """Save the scene to a new file path.

    Args:
        file_path: Path to save the scene to.

    Returns:
        Dictionary with success, file_path, and error.
    """
    return scene_save_as(file_path=file_path)


async def tool_scene_open(
    file_path: Annotated[
        str,
        "Path to the Maya scene file to open (.ma or .mb)",
    ],
    force: Annotated[
        bool,
        "If True, discard unsaved changes. If False (default), refuse when scene has unsaved changes.",
    ] = False,
    ctx: Context | None = None,
) -> SceneOpenOutput:
    """Open a Maya scene file.

    Args:
        file_path: Path to the scene file (.ma or .mb).
        force: If True, discard unsaved changes and open the file.
            If False (default), refuse when scene has unsaved changes.
        ctx: FastMCP request context, used for capability-gated elicitation.

    Returns:
        Dictionary with success, file_path, previous_file, was_modified, and error.
    """
    result = await asyncio.to_thread(scene_open, file_path=file_path, force=force)
    if force or ctx is None or not _is_unsaved_changes_refusal(result):
        return result
    if not _supports_form_elicitation(ctx):
        return result
    if not await _confirm_discard_unsaved_changes(ctx, f"opening {file_path!r}"):
        return result
    return await asyncio.to_thread(scene_open, file_path=file_path, force=True)


def tool_scene_undo() -> SceneUndoOutput:
    """Undo the last Maya operation.

    Returns success status, description of undone action, and availability
    of further undo/redo operations.
    """
    return scene_undo()


def tool_scene_redo() -> SceneRedoOutput:
    """Redo the last undone Maya operation.

    Returns success status, description of redone action, and availability
    of further undo/redo operations.
    """
    return scene_redo()


def tool_scene_import(
    file_path: Annotated[
        str,
        "Path to the file to import (.ma, .mb, .obj, .fbx, .abc, .usd, .usda, .usdc, .usdz)",
    ],
    namespace: Annotated[
        str | None,
        "Namespace behavior: None = no namespace, '' = auto-generate, 'name' = use specified",
    ] = None,
    force: Annotated[
        bool,
        "If True, replace existing namespace contents. If False (default), merge.",
    ] = False,
) -> SceneImportOutput:
    """Import a file into the current Maya scene.

    Args:
        file_path: Path to the file to import.
        namespace: Namespace behavior:
            - None (default): Import without namespace
            - "": Auto-generate namespace from filename
            - "myNs": Use specified namespace
        force: If True, replace existing namespace contents.

    Returns:
        Dictionary with success, file_path, nodes (top-level parents),
        count, and error.
    """
    return scene_import(file_path=file_path, namespace=namespace, force=force)


async def tool_scene_export(
    file_path: Annotated[
        str,
        "Path for the exported file (.ma, .mb, .obj, .fbx, .abc, .usd, .usda, .usdc)",
    ],
    export_mode: Annotated[
        Literal["selected", "all"],
        "What to export: 'selected' (default) or 'all'",
    ] = "selected",
    animation: Annotated[
        bool,
        "If True, include animation data (FBX only). If False (default), export static.",
    ] = False,
    ctx: Context | None = None,
) -> SceneExportOutput:
    """Export scene content to a file.

    Args:
        file_path: Path for the exported file.
        export_mode: 'selected' to export selection, 'all' for entire scene.
        animation: Include animation data (FBX only).
        ctx: FastMCP request context, used for progress notifications.

    Returns:
        Dictionary with success, file_path, nodes_exported, and error.
    """
    await report_progress(ctx, 0, 100, "Preparing export request")
    await report_progress(ctx, 50, 100, "Executing export in Maya")
    result = await asyncio.to_thread(
        scene_export,
        file_path=file_path,
        export_mode=export_mode,
        animation=animation,
    )
    await report_progress(
        ctx,
        100,
        100,
        "Export complete" if result["success"] else "Export finished with an error",
    )
    return result


def register_scene_tools(mcp: FastMCP) -> None:
    """Register scene tools."""
    mcp.tool(
        name="scene.info",
        description="Get information about the current Maya scene",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_scene_info)

    mcp.tool(
        name="scene.new",
        description="Create a new empty Maya scene. "
        "Checks for unsaved changes first and refuses by default if the scene was modified. "
        "Use force=True to discard unsaved changes. "
        "When a client supports form elicitation, the server may ask for confirmation instead "
        "of requiring an immediate retry.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_scene_new)

    mcp.tool(
        name="scene.save",
        description="Save the current scene. "
        "Saves to the current file path. Fails if the scene is untitled.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_scene_save)

    mcp.tool(
        name="scene.save_as",
        description="Save the scene to a new file path. "
        "Validates the path and saves as Maya ASCII or Binary based on extension.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_scene_save_as)

    mcp.tool(
        name="scene.open",
        description="Open a Maya scene file. "
        "Validates the file path and checks for unsaved changes before proceeding. "
        "Use force=True to discard unsaved changes. "
        "When a client supports form elicitation, the server may ask for confirmation instead "
        "of requiring an immediate retry. "
        "Supported formats: .ma (Maya ASCII), .mb (Maya Binary).",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_scene_open)

    mcp.tool(
        name="scene.undo",
        description="Undo the last operation in Maya. Critical for LLM error recovery.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_scene_undo)

    mcp.tool(
        name="scene.redo",
        description="Redo the last undone operation in Maya.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_scene_redo)

    mcp.tool(
        name="scene.import",
        description="Import a file into the current Maya scene. "
        "Supports multiple formats (.ma, .mb, .obj, .fbx, .abc, .usd, .usda, .usdc, .usdz). "
        "Returns only top-level parent transforms to protect token budget.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_scene_import)

    mcp.tool(
        name="scene.export",
        description="Export scene content to a file. "
        "Export selected nodes or entire scene. "
        "Supports multiple formats (.ma, .mb, .obj, .fbx, .abc, .usd, .usda, .usdc).",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_scene_export)
