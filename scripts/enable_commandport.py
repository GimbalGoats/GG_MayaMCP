"""Enable Maya commandPort for MCP server communication.

Run this script in Maya's Script Editor (Python tab) to open the commandPort
that allows the Maya MCP server to communicate with Maya.

Usage:
    1. Open Maya
    2. Open Script Editor (Windows > General Editors > Script Editor)
    3. Switch to the Python tab
    4. Paste this entire script
    5. Press Ctrl+Enter (or click Execute)

The commandPort will be opened on localhost:7001 by default.
"""

from __future__ import annotations

import ast
import builtins
import contextlib
import io

import maya.cmds as cmds

try:
    from maya_mcp.maya_panel.commandport_compat import (
        MAYA_2024_COMMAND_PORT_BUFFER_SIZE,
        command_port_open_kwargs,
        mark_maya_2024_compatible_port,
        requires_maya_2024_compatibility,
        unmark_maya_2024_compatible_port,
    )
except ImportError:
    _HANDLER_NAME = "_maya_mcp_command_port_2024"
    _STATE_NAME = "_maya_mcp_command_port_2024_state"
    _PORTS_NAME = "_maya_mcp_command_port_2024_ports"
    MAYA_2024_COMMAND_PORT_BUFFER_SIZE = 9 * 1024 * 1024

    def _maya_2024_handler(command: str) -> dict[str, object]:
        try:
            return {"ok": True, "result": _execute_maya_2024_command(command)}
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    def _execute_maya_2024_command(command: str) -> str:
        namespace = getattr(builtins, _STATE_NAME)
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

    def mark_maya_2024_compatible_port(port: int) -> None:
        ports = set(getattr(builtins, _PORTS_NAME, set()))
        ports.add(port)
        setattr(builtins, _PORTS_NAME, ports)

    def unmark_maya_2024_compatible_port(port: int) -> None:
        ports = set(getattr(builtins, _PORTS_NAME, set()))
        ports.discard(port)
        setattr(builtins, _PORTS_NAME, ports)


def enable_commandport(port: int = 7001, source_type: str = "python") -> None:
    """Enable Maya commandPort for external communication.

    Args:
        port: Port number to listen on (default: 7001)
        source_type: Command interpreter type, "python" or "mel" (default: "python")
    """
    port_name = f":{port}"

    # Close existing port if open
    try:
        existing_ports = cmds.commandPort(query=True, listPorts=True) or []
        existing_port_name = next(
            (name for name in existing_ports if str(name).rsplit(":", 1)[-1] == str(port)),
            None,
        )
        if existing_port_name is not None:
            cmds.commandPort(name=existing_port_name, close=True)
            unmark_maya_2024_compatible_port(port)
            print(f"Closed existing commandPort on {port_name}")
    except RuntimeError:
        pass

    # Open new commandPort
    port_kwargs = command_port_open_kwargs(cmds, source_type, True)
    port_kwargs.setdefault("bufferSize", 16384)
    cmds.commandPort(
        name=port_name,
        noreturn=False,
        **port_kwargs,
    )
    if port_kwargs.get("bufferSize") == MAYA_2024_COMMAND_PORT_BUFFER_SIZE:
        mark_maya_2024_compatible_port(port)

    print(f"commandPort opened on localhost{port_name}")
    print(f"  Source type: {source_type}")
    if port_kwargs.get("bufferSize") == MAYA_2024_COMMAND_PORT_BUFFER_SIZE:
        print("  Echo output: Maya 2024 compatibility handler")
    else:
        print("  Echo output: enabled")
    print()
    print("Maya MCP server can now connect to Maya.")
    print(f"To disable: disable_commandport({port})")


def disable_commandport(port: int = 7001) -> None:
    """Disable Maya commandPort.

    Args:
        port: Port number to close (default: 7001)
    """
    port_name = f":{port}"

    try:
        existing_ports = cmds.commandPort(query=True, listPorts=True) or []
        existing_port_name = next(
            (name for name in existing_ports if str(name).rsplit(":", 1)[-1] == str(port)),
            port_name,
        )
        cmds.commandPort(name=existing_port_name, close=True)
        unmark_maya_2024_compatible_port(port)
        print(f"commandPort closed on {port_name}")
    except RuntimeError as e:
        print(f"Could not close commandPort: {e}")


def check_commandport(port: int = 7001) -> bool:
    """Check if commandPort is open.

    Args:
        port: Port number to check (default: 7001)

    Returns:
        True if port is open, False otherwise
    """
    port_name = f":{port}"
    existing_ports = cmds.commandPort(query=True, listPorts=True) or []
    is_open = any(str(name).rsplit(":", 1)[-1] == str(port) for name in existing_ports)

    if is_open:
        print(f"commandPort {port_name} is OPEN")
    else:
        print(f"commandPort {port_name} is CLOSED")
        print(f"Open ports: {existing_ports}")

    return is_open


# Run when executed directly in Maya
if __name__ == "__main__":
    enable_commandport()
