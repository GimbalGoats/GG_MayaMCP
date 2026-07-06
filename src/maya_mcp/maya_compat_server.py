"""Maya-side compatibility server for broken commandPort response writers.

This module is designed to be executed inside Maya. The outside-Maya transport
can send this source through Maya's built-in commandPort when that port accepts
commands but returns empty responses because Autodesk's Python 3 response writer
is broken.
"""

import contextlib
import errno
import io
import pathlib
import socket
import socketserver
import sys
import tempfile
import threading
import time
import traceback

DEFAULT_PORT = 7001
BUFFER_SIZE = 65536
INITIAL_COMMAND_TIMEOUT = 30.0
COMMAND_IDLE_TIMEOUT = 0.05
BIND_RETRY_ATTEMPTS = 50
BIND_RETRY_DELAY_SECONDS = 0.1

# Auto-bootstrap can execute this module more than once in the same Maya
# session, each time as a fresh module instance. The running server handle is
# registered on ``sys`` so any instance can stop the previous server instead of
# colliding with it on the port bind.
_GLOBAL_HANDLE_NAME = "_maya_mcp_compat_server_handle"


def _registered_handle():
    handle = getattr(sys, _GLOBAL_HANDLE_NAME, None)
    if isinstance(handle, tuple) and len(handle) == 2:
        return handle
    return (None, None)


_server, _server_thread = _registered_handle()
_execution_globals = {
    "__name__": "__maya_mcp_compat_server__",
    "__builtins__": __builtins__,
}


class _ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class _CompatRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(INITIAL_COMMAND_TIMEOUT)

        while True:
            command = self._receive_command()
            if command is None:
                return

            output = _execute_in_maya(command)
            if not output:
                output = "\n"

            self.request.sendall(output.encode("utf-8", "replace"))

    def _receive_command(self):
        try:
            first_chunk = self.request.recv(BUFFER_SIZE)
        except OSError:
            return None

        if not first_chunk:
            return None

        chunks = [first_chunk]
        self.request.settimeout(COMMAND_IDLE_TIMEOUT)
        try:
            while True:
                try:
                    chunk = self.request.recv(BUFFER_SIZE)
                except socket.timeout:  # noqa: UP041 - Maya 2022 may not alias this to TimeoutError.
                    break
                if not chunk:
                    return None
                chunks.append(chunk)
        finally:
            self.request.settimeout(None)

        return b"".join(chunks).decode("utf-8", "replace").strip()


def _execute_in_maya(command):
    def run_command():
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                exec(command, _execution_globals)
            except Exception:
                traceback.print_exc()

        return stdout.getvalue() + stderr.getvalue()

    try:
        import maya.utils as maya_utils

        return maya_utils.executeInMainThreadWithResult(run_command)
    except ImportError:
        return run_command()


def _close_builtin_commandport(port):
    try:
        import maya.cmds as cmds

        port_suffix = f":{port}"
        existing_ports = cmds.commandPort(query=True, listPorts=True) or []
        for port_name in existing_ports:
            if str(port_name).strip().endswith(port_suffix):
                try:
                    cmds.commandPort(name=port_name, close=True)
                    print(f"Closed built-in commandPort on {port_name}")
                except RuntimeError as exc:
                    print(f"Could not close built-in commandPort {port_name}: {exc}")
    except RuntimeError as exc:
        print(f"Could not close built-in commandPort: {exc}")
    except ImportError:
        pass


def _is_address_in_use(exc):
    # Retry the bind while a prior socket on the same port is still tearing down.
    # Windows returns WSAEADDRINUSE (10048) while the old socket is still bound
    # and WSAEACCES (10013) during teardown even with SO_REUSEADDR set -- which is
    # exactly the window right after closing Maya's built-in commandPort. Python
    # may surface these as the raw WSA code in errno/winerror or as the mapped
    # POSIX errno (EADDRINUSE / EACCES), so check every form.
    err = getattr(exc, "errno", None)
    winerr = getattr(exc, "winerror", None)
    return err in {errno.EADDRINUSE, errno.EACCES, 10048, 10013} or winerr in {10048, 10013}


def _create_compat_server(port):
    last_error = None
    for attempt in range(BIND_RETRY_ATTEMPTS):
        try:
            return _ReusableThreadingTCPServer(("127.0.0.1", port), _CompatRequestHandler)
        except OSError as exc:
            last_error = exc
            if not _is_address_in_use(exc) or attempt == BIND_RETRY_ATTEMPTS - 1:
                raise
            time.sleep(BIND_RETRY_DELAY_SECONDS)

    raise last_error


def start_compat_server(port=DEFAULT_PORT):
    """Start the Maya MCP compatibility server.

    Args:
        port: Local TCP port to listen on.
    """
    global _server, _server_thread

    stop_compat_server()
    _close_builtin_commandport(port)

    _server = _create_compat_server(port)
    _server_thread = threading.Thread(target=_server.serve_forever)
    _server_thread.daemon = True
    _server_thread.start()
    setattr(sys, _GLOBAL_HANDLE_NAME, (_server, _server_thread))

    print(f"Maya MCP compatibility server opened on localhost:{port}")
    print("Leave Maya running, then start the MCP server normally.")


def _bootstrap_marker_path(port: int) -> str:
    """Path of the marker file proving Maya executed the bootstrap command."""
    return str(pathlib.Path(tempfile.gettempdir()) / f"maya_mcp_bootstrap_{port}.marker")


def _write_bootstrap_marker(port: int) -> None:
    with contextlib.suppress(OSError):
        pathlib.Path(_bootstrap_marker_path(port)).write_text(
            "maya-mcp compatibility bootstrap executed\n", encoding="utf-8"
        )


def bootstrap_compat_server(port=DEFAULT_PORT):
    """Start the compatibility server after the current Maya command returns."""
    # Written before anything can fail: its existence tells the MCP-side client
    # that Maya really executed this bootstrap (the transport cannot observe
    # that over the broken commandPort response path).
    _write_bootstrap_marker(port)

    def deferred_start():
        start_compat_server(port)

    try:
        import maya.utils as maya_utils

        maya_utils.executeDeferred(deferred_start)
        print(f"Maya MCP compatibility server scheduled on localhost:{port}")
    except ImportError:
        deferred_start()


def stop_compat_server():
    """Stop the compatibility server if it is running."""
    global _server, _server_thread

    server, _thread = _registered_handle()
    if server is None:
        server = _server
    if server is None:
        return

    server.shutdown()
    server.server_close()
    with contextlib.suppress(AttributeError):
        delattr(sys, _GLOBAL_HANDLE_NAME)
    _server = None
    _server_thread = None
    print("Maya MCP compatibility server stopped")


def compat_server_status():
    """Return and print whether the compatibility server is running."""
    server, _thread = _registered_handle()
    running = server is not None or _server is not None
    status = "running" if running else "stopped"
    print(f"Maya MCP compatibility server is {status}")
    return running


if __name__ == "__main__":
    try:
        start_compat_server()
    except OSError as exc:
        print(f"Failed to start Maya MCP compatibility server: {exc}", file=sys.stderr)
        raise
