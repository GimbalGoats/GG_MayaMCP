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

import maya.cmds as cmds


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
        if port_name in existing_ports:
            cmds.commandPort(name=port_name, close=True)
            print(f"Closed existing commandPort on {port_name}")
    except RuntimeError:
        pass

    # Open new commandPort
    cmds.commandPort(
        name=port_name,
        sourceType=source_type,
        echoOutput=True,
        noreturn=False,
        bufferSize=16384,
    )

    print(f"commandPort opened on localhost{port_name}")
    print(f"  Source type: {source_type}")
    print("  Echo output: enabled")
    print()
    print("Maya MCP server can now connect to Maya.")
    print(f"To disable: cmds.commandPort(name=':{port}', close=True)")


def disable_commandport(port: int = 7001) -> None:
    """Disable Maya commandPort.

    Args:
        port: Port number to close (default: 7001)
    """
    port_name = f":{port}"

    try:
        cmds.commandPort(name=port_name, close=True)
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
    is_open = port_name in existing_ports

    if is_open:
        print(f"commandPort {port_name} is OPEN")
    else:
        print(f"commandPort {port_name} is CLOSED")
        print(f"Open ports: {existing_ports}")

    return is_open


# Run when executed directly in Maya
if __name__ == "__main__":
    enable_commandport()
