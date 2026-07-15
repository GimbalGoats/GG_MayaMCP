"""Version-scoped Maya commandPort compatibility policy."""

from __future__ import annotations

import ast
import builtins
import contextlib
import io
from typing import Protocol

MAYA_2024_HANDLER_NAME = "_maya_mcp_command_port_2024"
MAYA_2024_STATE_NAME = "_maya_mcp_command_port_2024_state"
MAYA_2024_PORTS_NAME = "_maya_mcp_command_port_2024_ports"
# Covers the 1 MiB approved-script limit after worst-case JSON escaping and
# base64 framing, plus the compatibility wrapper.
MAYA_2024_COMMAND_PORT_BUFFER_SIZE = 9 * 1024 * 1024


class MayaCommands(Protocol):
    """Subset of ``maya.cmds`` used by the compatibility policy."""

    def about(self, **kwargs: bool) -> object: ...


def requires_maya_2024_compatibility(
    cmds: MayaCommands,
    source_type: str,
    echo_output: bool,
) -> bool:
    """Return whether the exact Maya 2024 response policy is required."""
    return str(cmds.about(majorVersion=True)) == "2024" and source_type == "python" and echo_output


def is_loopback_command_port_name(name: object, port: int) -> bool:
    """Return whether Maya's port name is an accepted loopback TCP form."""
    value = str(name).lower()
    return value in {
        f":{port}",
        f"localhost:{port}",
        f"127.0.0.1:{port}",
        f"[::1]:{port}",
    }


def is_maya_2024_compatible_port(port: int) -> bool:
    """Return whether this Maya process opened ``port`` with the workaround."""
    return port in getattr(builtins, MAYA_2024_PORTS_NAME, set())


def mark_maya_2024_compatible_port(port: int) -> None:
    """Record a successfully opened Maya 2024 compatibility port."""
    ports = set(getattr(builtins, MAYA_2024_PORTS_NAME, set()))
    ports.add(port)
    setattr(builtins, MAYA_2024_PORTS_NAME, ports)


def unmark_maya_2024_compatible_port(port: int) -> None:
    """Clear a compatibility marker when its port is closed."""
    ports = set(getattr(builtins, MAYA_2024_PORTS_NAME, set()))
    ports.discard(port)
    setattr(builtins, MAYA_2024_PORTS_NAME, ports)


def _maya_2024_handler(command: str) -> dict[str, object]:
    """Execute one payload while keeping command errors inside the response."""
    try:
        return {"ok": True, "result": _execute_maya_2024_command(command)}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _execute_maya_2024_command(command: str) -> str:
    """Execute one complete Python payload and preserve stdout/result semantics."""
    # Preserve access to Maya's interactive globals without retaining command
    # temporaries or overwriting user variables between requests.
    namespace = dict(getattr(builtins, MAYA_2024_STATE_NAME))
    tree = ast.parse(command, filename="<maya-mcp-commandPort>", mode="exec")
    result: object = None
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
    cmds: MayaCommands,
    source_type: str,
    echo_output: bool,
) -> dict[str, object]:
    """Return commandPort kwargs, installing the exact Maya 2024 workaround."""
    if not requires_maya_2024_compatibility(cmds, source_type, echo_output):
        return {"sourceType": source_type, "echoOutput": echo_output}

    setattr(builtins, MAYA_2024_HANDLER_NAME, _maya_2024_handler)
    setattr(builtins, MAYA_2024_STATE_NAME, __import__("__main__").__dict__)
    return {
        "sourceType": "python",
        "echoOutput": False,
        "bufferSize": MAYA_2024_COMMAND_PORT_BUFFER_SIZE,
    }
