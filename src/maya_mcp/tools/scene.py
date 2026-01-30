"""Scene tools for Maya MCP.

This module provides tools for querying and manipulating Maya scenes.
"""

from __future__ import annotations

import ast
import json
from typing import Any

from maya_mcp.transport import get_client

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


def scene_info() -> dict[str, Any]:
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
    try:
        data = ast.literal_eval(response) if not response.startswith("{") else None
        if data is None:
            import json

            data = json.loads(response)
    except (ValueError, SyntaxError):
        # Try to parse as JSON directly
        import json

        data = json.loads(response)

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


def scene_undo() -> dict[str, Any]:
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
    try:
        data = json.loads(response)
    except (ValueError, json.JSONDecodeError):
        data = ast.literal_eval(response)

    return {
        "success": data.get("success", False),
        "undone": data.get("undone"),
        "can_undo": data.get("can_undo", False),
        "can_redo": data.get("can_redo", False),
    }


def scene_redo() -> dict[str, Any]:
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
    try:
        data = json.loads(response)
    except (ValueError, json.JSONDecodeError):
        data = ast.literal_eval(response)

    return {
        "success": data.get("success", False),
        "redone": data.get("redone"),
        "can_undo": data.get("can_undo", False),
        "can_redo": data.get("can_redo", False),
    }
