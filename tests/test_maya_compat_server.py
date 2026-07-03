"""Tests for the Maya-side compatibility server module."""

from __future__ import annotations

import errno
import importlib
import socket
import sys
import threading
import types
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType


def _load_compat_server_module() -> ModuleType:
    import maya_mcp.maya_compat_server as compat_server

    return importlib.reload(compat_server)


def _read_compat_response(client: socket.socket) -> str:
    """Read one compatibility server response from a persistent socket."""
    chunks = [client.recv(1024)]

    client.settimeout(0.05)
    try:
        while True:
            try:
                chunk = client.recv(1024)
            except TimeoutError:
                break
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        client.settimeout(2.0)

    return b"".join(chunks).decode("utf-8").strip()


def test_compat_server_uses_socket_timeout_as_command_delimiter() -> None:
    """Legacy socket.timeout variants still mark the end of a command."""
    module = _load_compat_server_module()

    class LegacySocketTimeout(Exception):
        pass

    class FakeRequest:
        def __init__(self) -> None:
            self.timeouts: list[float | None] = []
            self.calls = 0

        def settimeout(self, timeout: float | None) -> None:
            self.timeouts.append(timeout)

        def recv(self, size: int) -> bytes:
            self.calls += 1
            if self.calls == 1:
                return b"print('ready')\n"
            raise LegacySocketTimeout

    handler = object.__new__(module._CompatRequestHandler)
    handler.request = FakeRequest()
    original_timeout = module.socket.timeout

    try:
        module.socket.timeout = LegacySocketTimeout
        assert handler._receive_command() == "print('ready')"
    finally:
        module.socket.timeout = original_timeout

    assert handler.request.timeouts == [module.COMMAND_IDLE_TIMEOUT, None]


def test_compat_server_executes_multiline_commands_on_persistent_socket() -> None:
    """Compatibility server accepts multiline commands and keeps the socket open."""
    module = _load_compat_server_module()
    server = module._ReusableThreadingTCPServer(("127.0.0.1", 0), module._CompatRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        host, port = server.server_address
        with socket.create_connection((host, port), timeout=2.0) as client:
            client.settimeout(2.0)

            client.sendall(b"value = 40 + 2\nprint(value)\n")
            assert _read_compat_response(client) == "42"

            client.sendall(b"print(value)\n")
            assert _read_compat_response(client) == "42"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def test_compat_server_reexecution_preserves_running_server_handle() -> None:
    """Re-executing the module can still stop the previously started server."""
    module = _load_compat_server_module()

    module.start_compat_server(0)
    host, port = module._server.server_address

    try:
        importlib.reload(module)
        assert module._server is not None
        module.stop_compat_server()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind((host, port))
    finally:
        if module._server is not None:
            module.stop_compat_server()


def _load_fresh_compat_module_instance(name: str) -> ModuleType:
    import importlib.util

    import maya_mcp.maya_compat_server as compat_server

    spec = importlib.util.spec_from_file_location(name, compat_server.__file__)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_start_compat_server_replaces_server_from_another_module_instance() -> None:
    """Auto-bootstrap re-runs load fresh module instances; they must not collide."""
    module_a = _load_fresh_compat_module_instance("_compat_instance_a")
    module_b = _load_fresh_compat_module_instance("_compat_instance_b")

    module_a.start_compat_server(0)
    port = module_a._server.server_address[1]

    try:
        module_b.start_compat_server(port)
        assert module_b._server.server_address[1] == port
    finally:
        module_b.stop_compat_server()
        module_a.stop_compat_server()


def test_bootstrap_compat_server_defers_start_until_current_command_returns(monkeypatch) -> None:
    """Auto-bootstrap avoids binding while Maya's built-in commandPort is active."""
    module = _load_compat_server_module()
    deferred_calls = []
    start_calls = []

    maya_module = types.ModuleType("maya")
    maya_utils_module = types.ModuleType("maya.utils")

    def execute_deferred(callback):
        deferred_calls.append(callback)

    maya_utils_module.executeDeferred = execute_deferred
    maya_module.utils = maya_utils_module
    monkeypatch.setitem(sys.modules, "maya", maya_module)
    monkeypatch.setitem(sys.modules, "maya.utils", maya_utils_module)
    monkeypatch.setattr(module, "start_compat_server", lambda port: start_calls.append(port))

    module.bootstrap_compat_server(7001)

    assert start_calls == []
    assert len(deferred_calls) == 1
    deferred_calls[0]()
    assert start_calls == [7001]


def test_close_builtin_commandport_closes_host_prefixed_port(monkeypatch: Any) -> None:
    """Maya may list commandPorts as localhost:port instead of :port."""
    module = _load_compat_server_module()
    closed_ports: list[object] = []

    class FakeMayaModule(types.ModuleType):
        cmds: FakeMayaCmdsModule

    class FakeMayaCmdsModule(types.ModuleType):
        commandPort: Callable[..., list[str] | None]

    maya_module = FakeMayaModule("maya")
    maya_cmds_module = FakeMayaCmdsModule("maya.cmds")

    def command_port(**kwargs: object) -> list[str] | None:
        if kwargs.get("query") and kwargs.get("listPorts"):
            return ["localhost:7001", ":7002"]
        if kwargs.get("close"):
            closed_ports.append(kwargs["name"])
        return None

    maya_cmds_module.commandPort = command_port
    maya_module.cmds = maya_cmds_module
    monkeypatch.setitem(sys.modules, "maya", maya_module)
    monkeypatch.setitem(sys.modules, "maya.cmds", maya_cmds_module)

    module._close_builtin_commandport(7001)

    assert closed_ports == ["localhost:7001"]


def test_close_builtin_commandport_continues_after_close_failure(monkeypatch: Any) -> None:
    """One failing close does not prevent closing another matching port name."""
    module = _load_compat_server_module()
    close_attempts: list[object] = []

    class FakeMayaModule(types.ModuleType):
        cmds: FakeMayaCmdsModule

    class FakeMayaCmdsModule(types.ModuleType):
        commandPort: Callable[..., list[str] | None]

    maya_module = FakeMayaModule("maya")
    maya_cmds_module = FakeMayaCmdsModule("maya.cmds")

    def command_port(**kwargs: object) -> list[str] | None:
        if kwargs.get("query") and kwargs.get("listPorts"):
            return ["localhost:7001", "127.0.0.1:7001"]
        if kwargs.get("close"):
            close_attempts.append(kwargs["name"])
            if kwargs["name"] == "localhost:7001":
                raise RuntimeError("already closing")
        return None

    maya_cmds_module.commandPort = command_port
    maya_module.cmds = maya_cmds_module
    monkeypatch.setitem(sys.modules, "maya", maya_module)
    monkeypatch.setitem(sys.modules, "maya.cmds", maya_cmds_module)

    module._close_builtin_commandport(7001)

    assert close_attempts == ["localhost:7001", "127.0.0.1:7001"]


def test_create_compat_server_retries_while_commandport_releases_port(monkeypatch) -> None:
    """Port handoff tolerates transient address-in-use errors."""
    module = _load_compat_server_module()
    attempts = []
    sleep_calls = []
    fake_server = object()

    def server_factory(*_args):
        attempts.append(None)
        if len(attempts) < 3:
            raise OSError(errno.EADDRINUSE, "Address already in use")
        return fake_server

    monkeypatch.setattr(module, "_ReusableThreadingTCPServer", server_factory)
    monkeypatch.setattr(module.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    assert module._create_compat_server(7001) is fake_server
    assert len(attempts) == 3
    assert sleep_calls == [
        module.BIND_RETRY_DELAY_SECONDS,
        module.BIND_RETRY_DELAY_SECONDS,
    ]


def test_compat_server_returns_tracebacks() -> None:
    """Execution failures are returned to the client instead of killing the handler."""
    module = _load_compat_server_module()

    output = module._execute_in_maya("raise RuntimeError('boom')")

    assert "RuntimeError: boom" in output
