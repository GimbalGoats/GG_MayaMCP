"""Tests for the Maya-side compatibility server helper script."""

from __future__ import annotations

import importlib.util
import socket
import threading
from pathlib import Path
from typing import Any


def _load_compat_server_script() -> Any:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "enable_compat_server.py"
    spec = importlib.util.spec_from_file_location("enable_compat_server", script_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_compat_server_executes_multiline_commands_on_persistent_socket() -> None:
    """Compatibility server accepts multiline commands and keeps the socket open."""
    module = _load_compat_server_script()
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


def test_compat_server_returns_tracebacks() -> None:
    """Execution failures are returned to the client instead of killing the handler."""
    module = _load_compat_server_script()

    output = module._execute_in_maya("raise RuntimeError('boom')")

    assert "RuntimeError: boom" in output
