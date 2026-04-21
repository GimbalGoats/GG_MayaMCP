"""Scene tools for Maya MCP.

This module provides tools for querying and manipulating Maya scenes.
"""

from __future__ import annotations

import json
from typing import Literal, cast

from typing_extensions import TypedDict

from maya_mcp.errors import ValidationError
from maya_mcp.transport import get_client
from maya_mcp.utils.parsing import parse_json_response
from maya_mcp.utils.response_guard import guard_response_size
from maya_mcp.utils.validation import FORBIDDEN_PATH_CHARS

# Mapping of Maya time units to FPS values
TIME_UNIT_TO_FPS: dict[str, float] = {
    "game": 15.0,
    "film": 24.0,
    "pal": 25.0,
    "ntsc": 30.0,
    "show": 48.0,
    "palf": 50.0,
    "ntscf": 60.0,
    "millisec": 1000.0,
    "sec": 1.0,
    "min": 1.0 / 60.0,
    "hour": 1.0 / 3600.0,
    # Additional common rates
    "2fps": 2.0,
    "3fps": 3.0,
    "4fps": 4.0,
    "5fps": 5.0,
    "6fps": 6.0,
    "8fps": 8.0,
    "10fps": 10.0,
    "12fps": 12.0,
    "16fps": 16.0,
    "20fps": 20.0,
    "40fps": 40.0,
    "75fps": 75.0,
    "80fps": 80.0,
    "100fps": 100.0,
    "120fps": 120.0,
    "125fps": 125.0,
    "150fps": 150.0,
    "200fps": 200.0,
    "240fps": 240.0,
    "250fps": 250.0,
    "300fps": 300.0,
    "375fps": 375.0,
    "400fps": 400.0,
    "500fps": 500.0,
    "600fps": 600.0,
    "750fps": 750.0,
    "1200fps": 1200.0,
    "1500fps": 1500.0,
    "2000fps": 2000.0,
    "3000fps": 3000.0,
    "6000fps": 6000.0,
    "23.976fps": 23.976,
    "29.97fps": 29.97,
    "29.97df": 29.97,
    "47.952fps": 47.952,
    "59.94fps": 59.94,
    "44100fps": 44100.0,
    "48000fps": 48000.0,
}

ALLOWED_SCENE_EXTENSIONS: tuple[str, ...] = (".ma", ".mb")
ALLOWED_IMPORT_EXTENSIONS: tuple[str, ...] = (
    ".ma",
    ".mb",
    ".obj",
    ".fbx",
    ".abc",
    ".usd",
    ".usda",
    ".usdc",
    ".usdz",
)
ALLOWED_EXPORT_EXTENSIONS: tuple[str, ...] = (
    ".ma",
    ".mb",
    ".obj",
    ".fbx",
    ".abc",
    ".usd",
    ".usda",
    ".usdc",
)
FORBIDDEN_PATH_CHARACTERS: str = FORBIDDEN_PATH_CHARS
SCENE_UNSAVED_CHANGES_ERROR = (
    "Scene has unsaved changes. Use force=True to discard changes, or save first."
)


class SceneInfoOutput(TypedDict):
    """Return payload for the scene.info tool."""

    file_path: str | None
    modified: bool
    fps: float
    frame_range: list[float]
    up_axis: Literal["y", "z"]


class _GuardedOutput(TypedDict, total=False):
    """Metadata added when response size guards truncate a payload."""

    truncated: bool
    total_count: int
    _size_warning: str
    _original_size: int
    _truncated_size: int


class SceneNewOutput(TypedDict):
    """Return payload for the scene.new tool."""

    success: bool
    previous_file: str | None
    was_modified: bool
    error: str | None


class SceneOpenOutput(TypedDict):
    """Return payload for the scene.open tool."""

    success: bool
    file_path: str | None
    previous_file: str | None
    was_modified: bool
    error: str | None


class SceneUndoOutput(TypedDict):
    """Return payload for the scene.undo tool."""

    success: bool
    undone: str | None
    can_undo: bool
    can_redo: bool


class SceneRedoOutput(TypedDict):
    """Return payload for the scene.redo tool."""

    success: bool
    redone: str | None
    can_undo: bool
    can_redo: bool


class SceneSaveOutput(TypedDict):
    """Return payload for the scene.save tool."""

    success: bool
    file_path: str | None
    error: str | None


class SceneSaveAsOutput(TypedDict):
    """Return payload for the scene.save_as tool."""

    success: bool
    file_path: str | None
    error: str | None


class SceneImportOutput(_GuardedOutput):
    """Return payload for the scene.import tool."""

    success: bool
    file_path: str | None
    nodes: list[str]
    count: int
    error: str | None


class SceneExportOutput(TypedDict):
    """Return payload for the scene.export tool."""

    success: bool
    file_path: str | None
    nodes_exported: int
    error: str | None


def scene_info() -> SceneInfoOutput:
    """Get information about the current Maya scene.

    Returns information about the currently open scene including
    file path, modification status, frame rate, and frame range.

    Returns:
        Dictionary with scene information:
            - file_path: Current scene file path, or None if untitled
            - modified: Whether scene has unsaved changes
            - fps: Frames per second
            - frame_range: [start_frame, end_frame]
            - up_axis: "y" or "z"

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.

    Example:
        >>> info = scene_info()
        >>> print(f"Scene: {info['file_path']}")
    """
    client = get_client()

    # Build a compound command that returns all info in one call
    # This is more efficient than multiple round-trips
    command = """
import maya.cmds as cmds
import json

scene_name = cmds.file(query=True, sceneName=True)
modified = cmds.file(query=True, modified=True)
time_unit = cmds.currentUnit(query=True, time=True)
min_time = cmds.playbackOptions(query=True, minTime=True)
max_time = cmds.playbackOptions(query=True, maxTime=True)
up_axis = cmds.upAxis(query=True, axis=True)

result = {
    "scene_name": scene_name if scene_name else None,
    "modified": modified,
    "time_unit": time_unit,
    "min_time": min_time,
    "max_time": max_time,
    "up_axis": up_axis
}
print(json.dumps(result))
"""

    response = client.execute(command)

    # Parse the JSON response
    data = parse_json_response(response)

    # Convert time unit to FPS
    time_unit = data.get("time_unit", "film")
    fps = TIME_UNIT_TO_FPS.get(time_unit, 24.0)

    return {
        "file_path": data.get("scene_name"),
        "modified": data.get("modified", False),
        "fps": fps,
        "frame_range": [data.get("min_time", 1.0), data.get("max_time", 24.0)],
        "up_axis": data.get("up_axis", "y"),
    }


def scene_undo() -> SceneUndoOutput:
    """Undo the last operation in Maya.

    Critical for LLM error recovery - allows reverting mistakes made
    during automated operations.

    Returns:
        Dictionary with undo result:
            - success: Whether undo succeeded
            - undone: Description of the undone action, or None
            - can_undo: Whether more undo operations are available
            - can_redo: Whether redo is now available

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.

    Example:
        >>> result = scene_undo()
        >>> if result['success']:
        ...     print(f"Undone: {result['undone']}")
    """
    client = get_client()

    command = """
import maya.cmds as cmds
import json

result = {"success": False, "undone": None, "can_undo": False, "can_redo": False}

# Check if undo is available
can_undo = cmds.undoInfo(query=True, undoQueueEmpty=True) == False
result["can_undo"] = can_undo

if can_undo:
    # Get the name of the operation that will be undone
    undone_name = cmds.undoInfo(query=True, undoName=True)
    # Perform the undo
    cmds.undo()
    result["success"] = True
    result["undone"] = undone_name if undone_name else None

# Check states after undo
result["can_undo"] = cmds.undoInfo(query=True, undoQueueEmpty=True) == False
result["can_redo"] = cmds.undoInfo(query=True, redoQueueEmpty=True) == False

print(json.dumps(result))
"""

    response = client.execute(command)

    # Parse the JSON response
    data = parse_json_response(response)

    return {
        "success": data.get("success", False),
        "undone": data.get("undone"),
        "can_undo": data.get("can_undo", False),
        "can_redo": data.get("can_redo", False),
    }


def scene_new(force: bool = False) -> SceneNewOutput:
    """Create a new, empty Maya scene.

    Checks whether the current scene has unsaved changes before proceeding.
    When ``force`` is False (default) and the scene has been modified, the
    operation is rejected with an actionable error message instead of
    discarding work.  When ``force`` is True, unsaved changes are discarded
    and a new scene is created unconditionally.

    **Important:** This tool never triggers Maya's interactive "Save changes?"
    dialog, which would block the commandPort indefinitely.  Instead it
    pre-checks the modification state and always passes ``force=True`` to the
    underlying ``cmds.file(new=True, force=True)`` call.

    Args:
        force: If True, discard unsaved changes and create a new scene.
            If False (default), refuse when the scene has unsaved changes.

    Returns:
        Dictionary with scene_new result:
            - success: Whether the new scene was created
            - previous_file: File path of the previous scene (or None)
            - was_modified: Whether the previous scene had unsaved changes
            - error: Error message if the operation was refused, or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.

    Example:
        >>> result = scene_new()
        >>> if not result['success']:
        ...     print(result['error'])  # "Scene has unsaved changes..."
        >>> result = scene_new(force=True)
        >>> assert result['success']
    """
    client = get_client()

    force_py = str(force)
    command = f"""
import maya.cmds as cmds
import json

force = {force_py}
result = {{"success": False, "previous_file": None, "was_modified": False, "error": None}}

scene_name = cmds.file(query=True, sceneName=True)
result["previous_file"] = scene_name if scene_name else None
modified = cmds.file(query=True, modified=True)
result["was_modified"] = modified

if modified and not force:
    result["error"] = {json.dumps(SCENE_UNSAVED_CHANGES_ERROR)}
else:
    _ = cmds.file(new=True, force=True)
    result["success"] = True

print(json.dumps(result))
"""

    response = client.execute(command)

    data = parse_json_response(response)

    return {
        "success": data.get("success", False),
        "previous_file": data.get("previous_file"),
        "was_modified": data.get("was_modified", False),
        "error": data.get("error"),
    }


def scene_open(file_path: str, force: bool = False) -> SceneOpenOutput:
    """Open a Maya scene file.

    Loads the specified scene file into Maya.  Checks whether the current scene
    has unsaved changes before proceeding.  When ``force`` is False (default)
    and the scene has been modified, the operation is rejected with an
    actionable error message.  When ``force`` is True, unsaved changes are
    discarded and the file is opened unconditionally.

    **Important:** This tool never triggers Maya's interactive "Save changes?"
    dialog, which would block the commandPort indefinitely.  Instead it
    pre-checks the modification state and always passes ``force=True`` to the
    underlying ``cmds.file(path, open=True, force=True)`` call.

    The file path is validated before being sent to Maya:

    - Must not be empty
    - Must not contain shell metacharacters (``;|&$``` etc.)
    - Must end with a supported Maya file extension (``.ma``, ``.mb``)
    - The file must exist on disk (verified inside Maya)

    Args:
        file_path: Absolute or relative path to the Maya scene file to open.
            Supported extensions: ``.ma`` (Maya ASCII), ``.mb`` (Maya Binary).
        force: If True, discard unsaved changes and open the file.
            If False (default), refuse when the current scene has unsaved
            changes.

    Returns:
        Dictionary with scene_open result:
            - success: Whether the file was opened
            - file_path: The opened file path (as reported by Maya), or None
            - previous_file: File path of the previous scene, or None
            - was_modified: Whether the previous scene had unsaved changes
            - error: Error message if the operation was refused, or None

    Raises:
        ValidationError: If the file path is invalid or contains dangerous
            characters.
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.

    Example:
        >>> result = scene_open("/path/to/scene.ma")
        >>> if not result['success']:
        ...     print(result['error'])  # "Scene has unsaved changes..."
        >>> result = scene_open("/path/to/scene.ma", force=True)
        >>> assert result['success']
    """
    normalized_file_path = _validate_file_path(file_path, ALLOWED_SCENE_EXTENSIONS)

    client = get_client()

    # Normalize slashes for Maya and embed safely via JSON string literal
    safe_path = normalized_file_path.replace("\\", "/")
    path_literal = json.dumps(safe_path)

    force_py = str(force)
    command = f"""
import maya.cmds as cmds
import json
import os

force = {force_py}
file_path = {path_literal}

result = {{"success": False, "file_path": None, "previous_file": None, "was_modified": False, "error": None}}

# Capture previous scene info
scene_name = cmds.file(query=True, sceneName=True)
result["previous_file"] = scene_name if scene_name else None
modified = cmds.file(query=True, modified=True)
result["was_modified"] = modified

# Check unsaved changes
if modified and not force:
    result["error"] = {json.dumps(SCENE_UNSAVED_CHANGES_ERROR)}
elif not os.path.isfile(file_path):
    result["error"] = "File not found: " + file_path
else:
    _ = cmds.file(file_path, open=True, force=True)
    result["success"] = True
    result["file_path"] = cmds.file(query=True, sceneName=True) or None

print(json.dumps(result))
"""

    response = client.execute(command)

    data = parse_json_response(response)

    return {
        "success": data.get("success", False),
        "file_path": data.get("file_path"),
        "previous_file": data.get("previous_file"),
        "was_modified": data.get("was_modified", False),
        "error": data.get("error"),
    }


def scene_redo() -> SceneRedoOutput:
    """Redo the last undone operation in Maya.

    Allows re-applying an operation that was previously undone.

    Returns:
        Dictionary with redo result:
            - success: Whether redo succeeded
            - redone: Description of the redone action, or None
            - can_undo: Whether undo is now available
            - can_redo: Whether more redo operations are available

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.

    Example:
        >>> result = scene_redo()
        >>> if result['success']:
        ...     print(f"Redone: {result['redone']}")
    """
    client = get_client()

    command = """
import maya.cmds as cmds
import json

result = {"success": False, "redone": None, "can_undo": False, "can_redo": False}

# Check if redo is available
can_redo = cmds.undoInfo(query=True, redoQueueEmpty=True) == False
result["can_redo"] = can_redo

if can_redo:
    # Get the name of the operation that will be redone
    redone_name = cmds.undoInfo(query=True, redoName=True)
    # Perform the redo
    cmds.redo()
    result["success"] = True
    result["redone"] = redone_name if redone_name else None

# Check states after redo
result["can_undo"] = cmds.undoInfo(query=True, undoQueueEmpty=True) == False
result["can_redo"] = cmds.undoInfo(query=True, redoQueueEmpty=True) == False

print(json.dumps(result))
"""

    response = client.execute(command)

    # Parse the JSON response
    data = parse_json_response(response)

    return {
        "success": data.get("success", False),
        "redone": data.get("redone"),
        "can_undo": data.get("can_undo", False),
        "can_redo": data.get("can_redo", False),
    }


def scene_save() -> SceneSaveOutput:
    """Save the current Maya scene.

    Saves the currently open scene file. If the scene is untitled (never saved),
    the operation is rejected with an error instructing to use ``scene.save_as``.

    Returns:
        Dictionary with save result:
            - success: Whether the scene was saved
            - file_path: The saved file path (or None if failed)
            - error: Error message if the operation failed, or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.

    Example:
        >>> result = scene_save()
        >>> if result['success']:
        ...     print(f"Saved: {result['file_path']}")
    """
    client = get_client()

    command = """
import maya.cmds as cmds
import json

result = {"success": False, "file_path": None, "error": None}

scene_name = cmds.file(query=True, sceneName=True)

if not scene_name:
    result["error"] = "Scene is untitled. Use scene.save_as to save for the first time."
else:
    try:
        # Save the file
        new_name = cmds.file(save=True)
        result["success"] = True
        result["file_path"] = new_name
    except Exception as e:
        result["error"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)

    data = parse_json_response(response)

    return {
        "success": data.get("success", False),
        "file_path": data.get("file_path"),
        "error": data.get("error"),
    }


def scene_save_as(file_path: str) -> SceneSaveAsOutput:
    """Save the current scene to a new file path.

    Renames the current scene and saves it to the specified path.
    If the file extension is ``.ma``, it saves as Maya ASCII.
    If the file extension is ``.mb``, it saves as Maya Binary.

    The file path is validated before being sent to Maya:
    - Must not be empty
    - Must not contain shell metacharacters
    - Must end with a supported Maya file extension (``.ma``, ``.mb``)

    Args:
        file_path: Absolute or relative path to save the scene to.

    Returns:
        Dictionary with save result:
            - success: Whether the scene was saved
            - file_path: The new file path (or None if failed)
            - error: Error message if the operation failed, or None

    Raises:
        ValidationError: If the file path is invalid.
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.

    Example:
        >>> result = scene_save_as("/path/to/new_scene.ma")
        >>> if result['success']:
        ...     print(f"Saved as: {result['file_path']}")
    """
    normalized_file_path = _validate_file_path(file_path, ALLOWED_SCENE_EXTENSIONS)

    client = get_client()

    # Normalize slashes and embed safely
    safe_path = normalized_file_path.replace("\\", "/")
    path_literal = json.dumps(safe_path)

    command = f"""
import maya.cmds as cmds
import json

file_path = {path_literal}
result = {{"success": False, "file_path": None, "error": None}}

# Determine file type based on extension
file_type = "mayaAscii" if file_path.lower().endswith(".ma") else "mayaBinary"

try:
    # Rename and save
    cmds.file(rename=file_path)
    new_name = cmds.file(save=True, type=file_type)
    result["success"] = True
    result["file_path"] = new_name
except Exception as e:
    result["error"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)

    data = parse_json_response(response)

    return {
        "success": data.get("success", False),
        "file_path": data.get("file_path"),
        "error": data.get("error"),
    }


def _validate_file_path(file_path: str, allowed_extensions: tuple[str, ...]) -> str:
    """Validate a file path for security and extension.

    Args:
        file_path: The file path to validate.
        allowed_extensions: Tuple of allowed file extensions (lowercase, with dot).

    Returns:
        The normalized file path.

    Raises:
        ValidationError: If the file path is invalid.
    """
    normalized_file_path = file_path.strip()

    if not normalized_file_path:
        raise ValidationError(
            message="File path must not be empty.",
            field_name="file_path",
            value="",
            constraint="non-empty string",
        )

    for ch in FORBIDDEN_PATH_CHARACTERS:
        if ch in normalized_file_path:
            raise ValidationError(
                message=f"File path contains forbidden character: {ch!r}",
                field_name="file_path",
                value=normalized_file_path,
                constraint="no shell metacharacters",
            )

    if any(ord(ch) < 32 for ch in normalized_file_path):
        raise ValidationError(
            message="File path contains forbidden control characters.",
            field_name="file_path",
            value=normalized_file_path,
            constraint="printable path string",
        )

    lower_path = normalized_file_path.lower()
    if not lower_path.endswith(allowed_extensions):
        raise ValidationError(
            message=f"Unsupported file extension. Allowed: {', '.join(allowed_extensions)}",
            field_name="file_path",
            value=normalized_file_path,
            constraint="supported file extension",
        )

    return normalized_file_path


def scene_import(
    file_path: str,
    namespace: str | None = None,
    force: bool = False,
) -> SceneImportOutput:
    """Import a file into the current Maya scene.

    Imports geometry, animation, or other scene data from an external file.
    Supports multiple formats including Maya scenes, OBJ, FBX, Alembic, and USD.

    The file path is validated before being sent to Maya:
    - Must not be empty
    - Must not contain shell metacharacters (``;|&$``` etc.)
    - Must end with a supported extension
    - The file must exist on disk (verified inside Maya)

    **Token Protection**: Returns only top-level parent transforms of imported
    nodes, not all descendants. This prevents token budget explosion when
    importing complex assets.

    Args:
        file_path: Absolute or relative path to the file to import.
            Supported extensions: ``.ma``, ``.mb``, ``.obj``, ``.fbx``, ``.abc``,
            ``.usd``, ``.usda``, ``.usdc``, ``.usdz``.
        namespace: Namespace behavior:
            - ``None`` (default): Import without namespace
            - ``""`` (empty string): Auto-generate namespace from filename
            - ``"myNs"``: Use specified namespace
        force: If True, replace existing namespace contents. If False (default),
            merge with existing namespace.

    Returns:
        Dictionary with import result:
            - success: Whether the file was imported
            - file_path: The imported file path
            - nodes: List of top-level parent transforms created by import
            - count: Number of top-level nodes returned
            - error: Error message if the operation failed, or None

    Raises:
        ValidationError: If the file path is invalid or contains dangerous
            characters.
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.

    Example:
        >>> result = scene_import("/assets/character.fbx", namespace="char")
        >>> if result['success']:
        ...     print(f"Imported {result['count']} top-level nodes")
    """
    normalized_file_path = _validate_file_path(file_path, ALLOWED_IMPORT_EXTENSIONS)

    client = get_client()

    safe_path = normalized_file_path.replace("\\", "/")
    path_literal = json.dumps(safe_path)

    namespace_literal = "None" if namespace is None else json.dumps(namespace)
    force_py = str(force)

    command = f"""
import maya.cmds as cmds
import json
import os

file_path = {path_literal}
namespace = {namespace_literal}
force = {force_py}

result = {{"success": False, "file_path": None, "nodes": [], "count": 0, "error": None}}

if not os.path.isfile(file_path):
    result["error"] = "File not found: " + file_path
    print(json.dumps(result))
else:
    try:
        before_nodes = set(cmds.ls(long=True, transforms=True) or [])

        import_kwargs = {{"i": True, "returnNewNodes": True}}

        if namespace is None:
            import_kwargs["namespace"] = ":"
        elif namespace == "":
            pass
        else:
            import_kwargs["namespace"] = namespace
            if force:
                import_kwargs["ra"] = True

        new_nodes = cmds.file(file_path, **import_kwargs) or []

        after_nodes = set(cmds.ls(long=True, transforms=True) or [])
        created_transforms = after_nodes - before_nodes

        top_level = []
        for node in created_transforms:
            parent = cmds.listRelatives(node, parent=True, fullPath=True)
            if not parent or parent[0] not in created_transforms:
                short_name = node.split("|")[-1]
                top_level.append(short_name)

        result["success"] = True
        result["file_path"] = file_path
        result["nodes"] = top_level
        result["count"] = len(top_level)

    except Exception as e:
        result["error"] = str(e)

    print(json.dumps(result))
"""

    response = client.execute(command)
    data = parse_json_response(response)

    result = {
        "success": data.get("success", False),
        "file_path": data.get("file_path"),
        "nodes": data.get("nodes", []),
        "count": data.get("count", 0),
        "error": data.get("error"),
    }

    result = guard_response_size(result, list_key="nodes")

    return cast("SceneImportOutput", result)


def scene_export(
    file_path: str,
    export_mode: str = "selected",
    animation: bool = False,
) -> SceneExportOutput:
    """Export scene content to a file.

    Exports the current selection or the entire scene to an external file format.
    Supports multiple formats including Maya scenes, OBJ, FBX, Alembic, and USD.

    The file path is validated before being sent to Maya:
    - Must not be empty
    - Must not contain shell metacharacters (``;|&$``` etc.)
    - Must end with a supported extension

    Args:
        file_path: Absolute or relative path for the exported file.
            Supported extensions: ``.ma``, ``.mb``, ``.obj``, ``.fbx``, ``.abc``,
            ``.usd``, ``.usda``, ``.usdc``.
        export_mode: What to export:
            - ``"selected"`` (default): Export currently selected nodes
            - ``"all"``: Export entire scene
        animation: If True, include animation data in export (FBX only).
            If False (default), export static geometry only.

    Returns:
        Dictionary with export result:
            - success: Whether the file was exported
            - file_path: The exported file path
            - nodes_exported: Number of nodes exported (approximate)
            - error: Error message if the operation failed, or None

    Raises:
        ValidationError: If the file path is invalid or contains dangerous
            characters, or if export_mode is invalid.
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.

    Example:
        >>> result = scene_export("/output/asset.fbx", animation=True)
        >>> if result['success']:
        ...     print(f"Exported to: {result['file_path']}")
    """
    if export_mode not in ("selected", "all"):
        raise ValidationError(
            message=f"Invalid export_mode: {export_mode!r}. Must be 'selected' or 'all'.",
            field_name="export_mode",
            value=export_mode,
            constraint="'selected' or 'all'",
        )

    normalized_file_path = _validate_file_path(file_path, ALLOWED_EXPORT_EXTENSIONS)

    client = get_client()

    safe_path = normalized_file_path.replace("\\", "/")
    path_literal = json.dumps(safe_path)

    animation_py = str(animation)

    command = f"""
import maya.cmds as cmds
import json
import os

file_path = {path_literal}
export_mode = {json.dumps(export_mode)}
animation = {animation_py}

result = {{"success": False, "file_path": None, "nodes_exported": 0, "error": None}}

try:
    ext = os.path.splitext(file_path)[1].lower()

    export_all = (export_mode == "all")
    export_selected = (export_mode == "selected")

    if export_selected:
        selection = cmds.ls(selection=True, long=True) or []
        if not selection:
            result["error"] = "Nothing selected. Select nodes to export, or use export_mode='all'."
        else:
            result["nodes_exported"] = len(selection)

    if result["error"] is None:
        export_kwargs = {{}}

        if ext == ".ma":
            export_kwargs["type"] = "mayaAscii"
        elif ext == ".mb":
            export_kwargs["type"] = "mayaBinary"
        elif ext == ".obj":
            export_kwargs["type"] = "OBJexport"
        elif ext == ".fbx":
            export_kwargs["type"] = "FBX export"
            if animation:
                cmds.bakeResults(simulation=True)
        elif ext == ".abc":
            export_kwargs["type"] = "Alembic"
        elif ext in (".usd", ".usda", ".usdc"):
            export_kwargs["type"] = "USD Export"

        if export_all:
            exported = cmds.file(file_path, exportAll=True, force=True, **export_kwargs)
        else:
            exported = cmds.file(file_path, exportSelected=True, force=True, **export_kwargs)

        result["success"] = True
        result["file_path"] = file_path

except Exception as e:
    result["error"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    data = parse_json_response(response)

    return {
        "success": data.get("success", False),
        "file_path": data.get("file_path"),
        "nodes_exported": data.get("nodes_exported", 0),
        "error": data.get("error"),
    }
