"""Start a Maya MCP compatibility server inside Maya.

Run this script in Maya's Script Editor (Python tab) on Maya versions where
Autodesk's built-in commandPort returns empty responses or logs:

    TypeError: a bytes-like object is required, not 'str'

The compatibility server listens on localhost:7001 by default and executes
incoming Python commands on Maya's main thread. It is intended as a workaround
for Maya 2022/2024 commandPort response encoding failures.
"""

import contextlib
import io
import socketserver
import sys
import threading
import traceback

DEFAULT_PORT = 7001
BUFFER_SIZE = 65536
INITIAL_COMMAND_TIMEOUT = 30.0
COMMAND_IDLE_TIMEOUT = 0.05

_server = None
_server_thread = None
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
                except TimeoutError:
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
            except BaseException:
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

        port_name = f":{port}"
        existing_ports = cmds.commandPort(query=True, listPorts=True) or []
        if port_name in existing_ports:
            cmds.commandPort(name=port_name, close=True)
            print(f"Closed built-in commandPort on {port_name}")
    except RuntimeError as exc:
        print(f"Could not close built-in commandPort: {exc}")
    except ImportError:
        pass


def start_compat_server(port=DEFAULT_PORT):
    """Start the Maya MCP compatibility server.

    Args:
        port: Local TCP port to listen on.
    """
    global _server, _server_thread

    stop_compat_server()
    _close_builtin_commandport(port)

    _server = _ReusableThreadingTCPServer(("127.0.0.1", port), _CompatRequestHandler)
    _server_thread = threading.Thread(target=_server.serve_forever)
    _server_thread.daemon = True
    _server_thread.start()

    print(f"Maya MCP compatibility server opened on localhost:{port}")
    print("Leave Maya running, then start the MCP server normally.")


def stop_compat_server():
    """Stop the compatibility server if it is running."""
    global _server, _server_thread

    if _server is None:
        return

    _server.shutdown()
    _server.server_close()
    _server = None
    _server_thread = None
    print("Maya MCP compatibility server stopped")


def compat_server_status():
    """Return and print whether the compatibility server is running."""
    running = _server is not None
    status = "running" if running else "stopped"
    print(f"Maya MCP compatibility server is {status}")
    return running


if __name__ == "__main__":
    try:
        start_compat_server()
    except OSError as exc:
        print(f"Failed to start Maya MCP compatibility server: {exc}", file=sys.stderr)
        raise
