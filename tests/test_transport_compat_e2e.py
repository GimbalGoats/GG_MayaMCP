"""End-to-end auto-bootstrap test against a simulated broken Maya commandPort.

Maya 2022/2024 executes commandPort commands but crashes with a ``TypeError``
when writing the response, so every command kills its connection without any
reply (see issue #26). The fake commandPort below reproduces that behavior with
a real TCP listener that executes received Python source and then closes the
connection without responding.

The fake ``maya`` package delays ``executeDeferred`` callbacks to mimic a busy
Maya main loop, which is the timing the auto-bootstrap must survive: the
compatibility server only takes over the port once Maya goes idle, well after
the bootstrap command itself returned.
"""

from __future__ import annotations

import contextlib
import socketserver
import sys
import threading
import time
import types
from typing import Any

import pytest

from maya_mcp.maya_compat_server import _GLOBAL_HANDLE_NAME
from maya_mcp.transport.commandport import CommandPortClient

# How long the fake Maya waits before running executeDeferred callbacks. Long
# enough that a single post-bootstrap probe would hit the still-broken port.
DEFERRED_IDLE_DELAY_SECONDS = 1.2


class _BrokenCommandPortHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        self.request.settimeout(5.0)
        try:
            first_chunk = self.request.recv(65536)
        except OSError:
            return
        if not first_chunk:
            return

        chunks = [first_chunk]
        self.request.settimeout(0.05)
        while True:
            try:
                chunk = self.request.recv(65536)
            except OSError:
                break
            if not chunk:
                break
            chunks.append(chunk)

        command = b"".join(chunks).decode("utf-8", "replace")
        # Errors only reach Maya's Script Editor; the client never sees them
        # because the response writer is broken either way.
        with contextlib.suppress(Exception):
            exec(command, self.server.execution_globals)  # type: ignore[attr-defined]
        # No response is ever written: Autodesk's Python 3 writer raises
        # TypeError before sendall, and the handler dies closing the socket.


class BrokenMayaCommandPort(socketserver.ThreadingTCPServer):
    """Executes each received command, then drops the connection silently."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _BrokenCommandPortHandler)
        self.execution_globals: dict[str, Any] = {"__name__": "__main__"}


@pytest.fixture
def broken_maya(monkeypatch: pytest.MonkeyPatch) -> Any:
    """A broken commandPort plus a fake maya package wired to it."""
    broken_server = BrokenMayaCommandPort()
    port = broken_server.server_address[1]
    serve_thread = threading.Thread(target=broken_server.serve_forever, daemon=True)
    serve_thread.start()
    builtin_port_open = threading.Event()
    builtin_port_open.set()

    def execute_deferred(callback: Any) -> None:
        timer = threading.Timer(DEFERRED_IDLE_DELAY_SECONDS, callback)
        timer.daemon = True
        timer.start()

    def execute_in_main_thread_with_result(callback: Any, *args: Any) -> Any:
        return callback(*args)

    def command_port(**kwargs: Any) -> list[str] | None:
        if kwargs.get("query") and kwargs.get("listPorts"):
            return [f":{port}"] if builtin_port_open.is_set() else []
        if kwargs.get("close") and str(kwargs.get("name", "")).endswith(f":{port}"):
            builtin_port_open.clear()
            broken_server.shutdown()
            broken_server.server_close()
        return None

    maya_module = types.ModuleType("maya")
    maya_utils_module = types.ModuleType("maya.utils")
    maya_cmds_module = types.ModuleType("maya.cmds")
    maya_utils_module.executeDeferred = execute_deferred  # type: ignore[attr-defined]
    maya_utils_module.executeInMainThreadWithResult = (  # type: ignore[attr-defined]
        execute_in_main_thread_with_result
    )
    maya_cmds_module.commandPort = command_port  # type: ignore[attr-defined]
    maya_module.utils = maya_utils_module  # type: ignore[attr-defined]
    maya_module.cmds = maya_cmds_module  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "maya", maya_module)
    monkeypatch.setitem(sys.modules, "maya.utils", maya_utils_module)
    monkeypatch.setitem(sys.modules, "maya.cmds", maya_cmds_module)

    try:
        yield types.SimpleNamespace(port=port, builtin_port_open=builtin_port_open)
    finally:
        handle = getattr(sys, _GLOBAL_HANDLE_NAME, None)
        if handle is not None:
            compat_server, _compat_thread = handle
            compat_server.shutdown()
            compat_server.server_close()
            delattr(sys, _GLOBAL_HANDLE_NAME)
        if builtin_port_open.is_set():
            broken_server.shutdown()
            broken_server.server_close()
        serve_thread.join(timeout=2.0)


def test_execute_recovers_from_broken_commandport_with_slow_deferred(broken_maya: Any) -> None:
    """The auto-bootstrap survives a compat takeover slower than one probe."""
    client = CommandPortClient(
        port=broken_maya.port,
        connect_timeout=2.0,
        command_timeout=5.0,
        retry_base_delay=0.1,
    )
    started = time.monotonic()

    try:
        result = client.execute("print('recovered-' + 'output')")

        assert result == "recovered-output"
        # The built-in port was replaced, not worked around on another port.
        assert not broken_maya.builtin_port_open.is_set()

        # The replacement listener keeps serving follow-up commands.
        assert client.execute("value = 40 + 2\nprint(value)") == "42"
    finally:
        client.disconnect()

    # Sanity: the takeover really happened after the deferred idle delay.
    assert time.monotonic() - started >= DEFERRED_IDLE_DELAY_SECONDS


def test_compat_server_survives_repeat_bootstrap(broken_maya: Any) -> None:
    """A second bootstrap replaces the running compat server without a bind clash."""
    client = CommandPortClient(
        port=broken_maya.port,
        connect_timeout=2.0,
        command_timeout=5.0,
        retry_base_delay=0.1,
    )

    try:
        assert client.execute("print('first-' + 'run')") == "first-run"

        first_handle = getattr(sys, _GLOBAL_HANDLE_NAME)
        from maya_mcp.transport.commandport import _build_compat_server_python_bootstrap

        # A stale client (or a Maya-side re-run of the bootstrap snippet) must
        # not collide with the already-running compatibility server.
        rebootstrap = _build_compat_server_python_bootstrap(broken_maya.port)
        client.execute(rebootstrap)
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            if getattr(sys, _GLOBAL_HANDLE_NAME, first_handle) is not first_handle:
                break
            time.sleep(0.1)

        second_handle = getattr(sys, _GLOBAL_HANDLE_NAME)
        assert second_handle is not first_handle

        client.disconnect()
        assert client.execute("print('second-' + 'run')") == "second-run"
    finally:
        client.disconnect()
