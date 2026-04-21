---
summary: "User guide for the dockable Maya control panel, commandPort management, preferences, auto-start, and troubleshooting."
read_when:
  - When working on Maya panel UX, commandPort panel workflows, preferences, auto-start, or panel troubleshooting.
  - When changing Maya-side setup instructions or the relationship between the panel and external MCP server.
---

# Maya MCP Control Panel

The Maya control panel is a dockable widget that runs inside Maya and manages the Maya-side `commandPort` used by Maya MCP.

It is separate from the external MCP server process.

## Compatibility

| Maya Version | Qt Binding |
|--------------|------------|
| Maya 2022-2024 | PySide2 |
| Maya 2025+ | PySide6 |

The panel detects the available Qt binding at runtime.

## Features

- Start and stop `commandPort`
- Configure the port number
- Store auto-start preferences
- Show connection and activity log entries

## Open the Panel

Run this in Maya's Script Editor:

```python
from maya_mcp.maya_panel import show_panel

show_panel()
```

## Auto-Start on Maya Launch

The repository includes an example `scripts/userSetup.py`.

Place it in Maya's scripts directory for your version:

| Platform | Example Path |
|----------|--------------|
| Windows | `Documents\maya\<version>\scripts\userSetup.py` |
| macOS | `~/Library/Preferences/Autodesk/maya/<version>/scripts/userSetup.py` |
| Linux | `~/maya/<version>/scripts/userSetup.py` |

## Preferences API

```python
from maya_mcp.maya_panel.preferences import (
    get_all_preferences,
    get_auto_start,
    get_port,
    reset_preferences,
    set_auto_start,
    set_port,
)
```

Examples:

```python
port = get_port()
set_port(7002)

auto_start = get_auto_start()
set_auto_start(True)

prefs = get_all_preferences()
reset_preferences()
```

## Controller API

```python
from maya_mcp.maya_panel.controller import (
    close_command_port,
    get_port_status,
    is_command_port_open,
    open_command_port,
    toggle_command_port,
)
```

Examples:

```python
open_command_port(7001)

if is_command_port_open(7001):
    print("commandPort is running")

status = get_port_status(7001)
toggle_command_port(7001)
close_command_port(7001)
```

## Runtime Relationship

The panel and the MCP server have different roles:

1. The panel runs inside Maya.
2. The panel opens or closes Maya's native `commandPort`.
3. The external `maya_mcp.server` process connects to that port over `localhost`.
4. MCP clients talk to the external server, not directly to the panel.

## Troubleshooting

### Panel does not appear

```python
import maya_mcp
print(maya_mcp.__file__)
```

If import works, try creating the widget directly:

```python
from maya_mcp.maya_panel.panel import MCPControlPanel

panel = MCPControlPanel()
panel.show()
```

### `commandPort` will not start

Check which ports Maya currently has open:

```python
import maya.cmds as cmds
print(cmds.commandPort(query=True, listPorts=True))
```

### Auto-start is not working

Verify `userSetup.py` is in the correct Maya scripts directory, then inspect stored preferences:

```python
from maya_mcp.maya_panel.preferences import get_all_preferences

print(get_all_preferences())
```

## See Also

- [Docs Home](../index.md)
- [Architecture Overview](../spec/overview.md)
- [Transport Specification](../spec/transport.md)
