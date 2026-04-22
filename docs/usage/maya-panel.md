---
summary: "Optional in-Maya panel for opening commandPort, changing the port, and storing local panel preferences."
read_when:
  - When you want a UI inside Maya instead of opening commandPort by hand.
  - When working on Maya panel UX, preferences, or startup behavior.
---

# Maya Control Panel

The Maya Control Panel is optional. It runs inside Maya and gives you a small UI for managing the Maya-side `commandPort`.

Use it if you want a button-driven setup instead of opening `commandPort` from the Script Editor.

## What It Does

- open or close `commandPort`
- change the port number
- remember local preferences
- optionally auto-start on Maya launch

It does not replace the external MCP server. The panel lives inside Maya; the MCP server still runs as a separate process.

## Compatibility

| Maya version | Qt binding |
|---|---|
| Maya 2022-2024 | `PySide2` |
| Maya 2025+ | `PySide6` |

## Open the Panel

Run this in Maya:

```python
from maya_mcp.maya_panel import show_panel

show_panel()
```

## Typical Workflow

1. Open the panel in Maya
2. Start `commandPort`
3. Confirm the port matches your client or server config
4. Start your MCP client and call `health.check`

## Auto-Start on Maya Launch

The repo includes an example `scripts/userSetup.py`.

Place it in Maya's scripts directory for your version:

| Platform | Example path |
|---|---|
| Windows | `Documents/maya/<version>/scripts/userSetup.py` |
| macOS | `~/Library/Preferences/Autodesk/maya/<version>/scripts/userSetup.py` |
| Linux | `~/maya/<version>/scripts/userSetup.py` |

If you already have a `userSetup.py`, merge only the parts you need.

## Preferences Helpers

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

Common use:

```python
set_port(7002)
set_auto_start(True)
print(get_all_preferences())
```

## Controller Helpers

```python
from maya_mcp.maya_panel.controller import (
    close_command_port,
    get_port_status,
    is_command_port_open,
    open_command_port,
    toggle_command_port,
)
```

Common use:

```python
open_command_port(7001)
print(is_command_port_open(7001))
print(get_port_status(7001))
close_command_port(7001)
```

## Troubleshooting

If the panel does not appear:

```python
import maya_mcp
print(maya_mcp.__file__)
```

If `commandPort` will not open:

```python
import maya.cmds as cmds
print(cmds.commandPort(query=True, listPorts=True))
```

If auto-start is not working:

```python
from maya_mcp.maya_panel.preferences import get_all_preferences

print(get_all_preferences())
```

## Related Docs

- [Getting Started](getting-started.md)
- [Client Setup](client-setup.md)
- [Architecture Overview](../spec/overview.md)
