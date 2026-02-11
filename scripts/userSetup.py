"""Example userSetup.py for Maya MCP.

This script demonstrates how to configure Maya to automatically start
the MCP commandPort when Maya launches.

Installation:
    Copy this file (or its contents) to your Maya scripts directory:
        - Windows: Documents/maya/<version>/scripts/userSetup.py
        - macOS: ~/Library/Preferences/Autodesk/maya/<version>/scripts/userSetup.py
        - Linux: ~/maya/<version>/scripts/userSetup.py

    If userSetup.py already exists, add the relevant lines to it.

Configuration:
    You can customize the behavior by modifying the constants below:
        - AUTO_START_ENABLED: Set to True to auto-start commandPort
        - DEFAULT_PORT: Change the default port number

Note:
    This script runs during Maya's startup. Keep it lightweight to avoid
    slowing down Maya's launch time.

See Also:
    - docs/usage/maya-panel.md for full documentation
    - src/maya_mcp/maya_panel/ for the panel source code
"""

from __future__ import annotations

# ============================================================================
# Configuration
# ============================================================================

# Set to True to automatically start commandPort when Maya launches
AUTO_START_ENABLED = True

# Default port for the MCP server
DEFAULT_PORT = 7001

# Set to True to show the MCP Control Panel on startup
SHOW_PANEL_ON_STARTUP = False

# ============================================================================
# Implementation
# ============================================================================


def _setup_mcp() -> None:
    """Set up Maya MCP on startup.

    This function is called during Maya's initialization to:
    1. Auto-start the commandPort (if enabled)
    2. Show the MCP Control Panel (if enabled)

    All operations are wrapped in try/except to prevent startup failures.
    """
    import maya.cmds as cmds

    # Use executeDeferred to run after Maya is fully initialized
    cmds.evalDeferred(_deferred_setup)


def _deferred_setup() -> None:
    """Deferred setup that runs after Maya is fully initialized."""
    try:
        _start_command_port()
    except Exception as e:
        print(f"[MCP] Warning: Failed to start commandPort: {e}")

    try:
        _show_panel()
    except Exception as e:
        print(f"[MCP] Warning: Failed to show panel: {e}")


def _start_command_port() -> None:
    """Start the commandPort if auto-start is enabled."""
    if not AUTO_START_ENABLED:
        return

    import maya.cmds as cmds

    port_name = f":{DEFAULT_PORT}"

    # Check if already open
    open_ports = cmds.commandPort(query=True, listPorts=True) or []
    if port_name in open_ports:
        print(f"[MCP] commandPort already open on {port_name}")
        return

    # Open the port
    try:
        cmds.commandPort(
            name=port_name,
            sourceType="python",
            echoOutput=True,
        )
        print(f"[MCP] commandPort opened on {port_name}")
    except RuntimeError as e:
        print(f"[MCP] Failed to open commandPort: {e}")


def _show_panel() -> None:
    """Show the MCP Control Panel if enabled."""
    if not SHOW_PANEL_ON_STARTUP:
        return

    try:
        # Import panel module (only available if maya_mcp is installed)
        from maya_mcp.maya_panel import show_panel

        show_panel()
        print("[MCP] Control Panel shown")
    except ImportError:
        # maya_mcp not installed, skip panel
        print("[MCP] maya_mcp package not found, skipping panel")
    except Exception as e:
        print(f"[MCP] Failed to show panel: {e}")


# ============================================================================
# Entry Point
# ============================================================================

# Run setup on module load (during Maya startup)
_setup_mcp()
