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

import ast
import builtins
import contextlib
import io

try:
    from maya_mcp.maya_panel.commandport_compat import (
        MAYA_2024_COMMAND_PORT_BUFFER_SIZE,
        command_port_open_kwargs,
        is_loopback_command_port_name,
        is_maya_2024_compatible_port,
        mark_maya_2024_compatible_port,
        requires_maya_2024_compatibility,
        unmark_maya_2024_compatible_port,
    )
except ImportError:
    _HANDLER_NAME = "_maya_mcp_command_port_2024"
    _STATE_NAME = "_maya_mcp_command_port_2024_state"
    _PORTS_NAME = "_maya_mcp_command_port_2024_ports"
    MAYA_2024_COMMAND_PORT_BUFFER_SIZE = 9 * 1024 * 1024

    def is_loopback_command_port_name(name: object, port: int) -> bool:
        return str(name) == f":{port}"

    def _maya_2024_handler(command: str) -> dict[str, object]:
        try:
            return {"ok": True, "result": _execute_maya_2024_command(command)}
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    def _execute_maya_2024_command(command: str) -> str:
        namespace = dict(getattr(builtins, _STATE_NAME))
        tree = ast.parse(command, filename="<maya-mcp-commandPort>", mode="exec")
        result = None
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            if tree.body and isinstance(tree.body[-1], ast.Expr):
                statements = ast.Module(body=tree.body[:-1], type_ignores=[])
                if statements.body:
                    exec(
                        compile(
                            statements,
                            "<maya-mcp-commandPort>",
                            "exec",
                            dont_inherit=True,
                        ),
                        namespace,
                        namespace,
                    )
                expression = ast.Expression(body=tree.body[-1].value)
                result = eval(
                    compile(
                        expression,
                        "<maya-mcp-commandPort>",
                        "eval",
                        dont_inherit=True,
                    ),
                    namespace,
                    namespace,
                )
            else:
                exec(
                    compile(
                        tree,
                        "<maya-mcp-commandPort>",
                        "exec",
                        dont_inherit=True,
                    ),
                    namespace,
                    namespace,
                )
        captured = output.getvalue()
        if result is None:
            return captured
        rendered = str(result)
        return f"{captured}{rendered}" if captured else rendered

    def command_port_open_kwargs(
        maya_cmds: object,
        source_type: str,
        echo_output: bool,
    ) -> dict[str, object]:
        if not requires_maya_2024_compatibility(maya_cmds, source_type, echo_output):
            return {"sourceType": source_type, "echoOutput": echo_output}
        setattr(builtins, _HANDLER_NAME, _maya_2024_handler)
        setattr(builtins, _STATE_NAME, __import__("__main__").__dict__)
        return {
            "sourceType": "python",
            "echoOutput": False,
            "bufferSize": MAYA_2024_COMMAND_PORT_BUFFER_SIZE,
        }

    def requires_maya_2024_compatibility(
        maya_cmds: object,
        source_type: str,
        echo_output: bool,
    ) -> bool:
        return (
            str(maya_cmds.about(majorVersion=True)) == "2024"
            and source_type == "python"
            and echo_output
        )

    def is_maya_2024_compatible_port(port: int) -> bool:
        return port in getattr(builtins, _PORTS_NAME, set())

    def mark_maya_2024_compatible_port(port: int) -> None:
        ports = set(getattr(builtins, _PORTS_NAME, set()))
        ports.add(port)
        setattr(builtins, _PORTS_NAME, ports)

    def unmark_maya_2024_compatible_port(port: int) -> None:
        ports = set(getattr(builtins, _PORTS_NAME, set()))
        ports.discard(port)
        setattr(builtins, _PORTS_NAME, ports)

# ============================================================================
# Configuration
# ============================================================================

# Set to True to automatically start commandPort when Maya launches
AUTO_START_ENABLED = True

# Default port for the MCP server
DEFAULT_PORT = 7001

# Set to True to show the MCP Control Panel on startup
SHOW_PANEL_ON_STARTUP = False

# Set to True only when this script owns the configured port and may replace an
# unknown existing Maya 2024 listener.
REPLACE_EXISTING_COMMAND_PORT = False

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

    # Replace legacy Maya 2024 ports so the installed response handler and port
    # configuration always agree. Later Maya versions keep the no-op behavior.
    open_ports = cmds.commandPort(query=True, listPorts=True) or []
    existing_port_name = next(
        (name for name in open_ports if is_loopback_command_port_name(name, DEFAULT_PORT)),
        None,
    )
    if existing_port_name is not None:
        already_compatible = is_maya_2024_compatible_port(DEFAULT_PORT)
        needs_compatibility = requires_maya_2024_compatibility(cmds, "python", True)
        if not needs_compatibility:
            print(f"[MCP] commandPort already open on {existing_port_name}")
            return
        if not already_compatible and not REPLACE_EXISTING_COMMAND_PORT:
            print(
                f"[MCP] Warning: commandPort {existing_port_name} is not owned by this "
                "startup script; leaving it unchanged"
            )
            return

    port_kwargs = command_port_open_kwargs(cmds, "python", True)
    is_maya_2024_compatibility = port_kwargs.get("bufferSize") == MAYA_2024_COMMAND_PORT_BUFFER_SIZE

    if existing_port_name is not None:
        if not is_maya_2024_compatibility:
            print(f"[MCP] commandPort already open on {port_name}")
            return
        cmds.commandPort(name=existing_port_name, close=True)
        unmark_maya_2024_compatible_port(DEFAULT_PORT)
        print(f"[MCP] Refreshing Maya 2024 commandPort on {port_name}")

    # Open the port
    try:
        cmds.commandPort(
            name=port_name,
            **port_kwargs,
        )
        if is_maya_2024_compatibility:
            mark_maya_2024_compatible_port(DEFAULT_PORT)
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
