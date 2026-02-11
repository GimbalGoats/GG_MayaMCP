# Maya MCP Control Panel

The MCP Control Panel is a dockable widget inside Maya that provides visual control over the commandPort server connection.

## Compatibility

| Maya Version | Qt/PySide | Supported |
|--------------|-----------|-----------|
| Maya 2022-2024 | PySide2 (Qt5) | ✅ |
| Maya 2025+ | PySide6 (Qt6) | ✅ |

The panel automatically detects which PySide version is available and uses it.

## Features

| Feature | Description |
|---------|-------------|
| **Status Indicator** | Green/red indicator showing if commandPort is running |
| **Start/Stop Button** | Toggle commandPort on/off with one click |
| **Port Configuration** | Change the port number (default: 7001) |
| **Auto-start Option** | Automatically start commandPort when Maya launches |
| **Connection Log** | Timestamped log of server events |

## Quick Start

### Option 1: Show Panel Manually

In Maya's Script Editor (Python tab):

```python
from maya_mcp.maya_panel import show_panel
show_panel()
```

### Option 2: Auto-start on Maya Launch

Copy the example `userSetup.py` to your Maya scripts directory:

**Windows:**
```
Documents\maya\<version>\scripts\userSetup.py
```

**macOS:**
```
~/Library/Preferences/Autodesk/maya/<version>/scripts/userSetup.py
```

**Linux:**
```
~/maya/<version>/scripts/userSetup.py
```

The example script is located at `scripts/userSetup.py` in the maya-mcp repository.

## Panel Interface

```
┌─────────────────────────────────────┐
│       MCP Control Panel             │
├─────────────────────────────────────┤
│ Server Status                       │
│ [●] Running on port 7001            │
├─────────────────────────────────────┤
│ Controls                            │
│ Port: [7001      ] [Apply]          │
│ [      Stop Server      ]           │
│ ☑ Auto-start on Maya launch         │
├─────────────────────────────────────┤
│ Connection Log                      │
│ ┌─────────────────────────────────┐ │
│ │ [10:30:15] Server started       │ │
│ │ [10:30:20] Panel initialized    │ │
│ │ [10:31:05] nodes.list called    │ │
│ └─────────────────────────────────┘ │
│ [Clear Log]                         │
└─────────────────────────────────────┘
```

## Configuration Options

### Port Number

Default: `7001`

Change the port in the panel UI or programmatically:

```python
from maya_mcp.maya_panel.preferences import set_port
set_port(7002)
```

### Auto-start

When enabled, the commandPort will automatically open when Maya starts.

Enable via the checkbox in the panel, or programmatically:

```python
from maya_mcp.maya_panel.preferences import set_auto_start
set_auto_start(True)
```

### userSetup.py Configuration

The example `userSetup.py` supports these configuration options:

```python
# Set to True to automatically start commandPort
AUTO_START_ENABLED = True

# Default port for the MCP server  
DEFAULT_PORT = 7001

# Set to True to show the Control Panel on startup
SHOW_PANEL_ON_STARTUP = False
```

## API Reference

### Panel Functions

```python
from maya_mcp.maya_panel import show_panel, auto_start_if_enabled

# Show the dockable panel
panel = show_panel()

# Auto-start commandPort if enabled in preferences
# (typically called from userSetup.py)
auto_start_if_enabled()
```

### Controller Functions

```python
from maya_mcp.maya_panel.controller import (
    open_command_port,
    close_command_port,
    is_command_port_open,
    get_port_status,
    toggle_command_port,
)

# Open commandPort on port 7001
open_command_port(7001)

# Check if port is open
if is_command_port_open(7001):
    print("CommandPort is running")

# Get detailed status
status = get_port_status(7001)
# {'is_open': True, 'port': 7001, 'port_name': ':7001', 'all_ports': [':7001']}

# Toggle on/off
is_now_open = toggle_command_port(7001)

# Close the port
close_command_port(7001)
```

### Preferences Functions

```python
from maya_mcp.maya_panel.preferences import (
    get_port,
    set_port,
    get_auto_start,
    set_auto_start,
    get_all_preferences,
    reset_preferences,
)

# Get current port setting
port = get_port()  # Default: 7001

# Set port
set_port(7002)

# Get auto-start setting
auto_start = get_auto_start()  # Default: False

# Enable auto-start
set_auto_start(True)

# Get all preferences
prefs = get_all_preferences()
# {'port': 7001, 'auto_start': True}

# Reset to defaults
reset_preferences()
```

## Troubleshooting

### Panel doesn't appear

1. Ensure `maya_mcp` is installed and importable:
   ```python
   import maya_mcp
   print(maya_mcp.__file__)
   ```

2. Check Maya's Script Editor for errors

3. Try running the panel creation directly:
   ```python
   from maya_mcp.maya_panel.panel import MCPControlPanel
   panel = MCPControlPanel()
   panel.show()
   ```

### CommandPort won't start

1. Check if the port is already in use:
   ```python
   import maya.cmds as cmds
   print(cmds.commandPort(query=True, listPorts=True))
   ```

2. Try a different port number

3. Restart Maya and try again

### Auto-start not working

1. Verify `userSetup.py` is in the correct location

2. Check Maya's Script Editor Output on startup for errors

3. Manually check preferences:
   ```python
   from maya_mcp.maya_panel.preferences import get_all_preferences
   print(get_all_preferences())
   ```

## Architecture

The Maya Panel runs **inside** Maya's Python interpreter, while the MCP Server runs **outside** as a separate process:

```
┌─────────────────────────────────────────────────────┐
│                    Maya Process                      │
│                                                      │
│  ┌──────────────────┐     ┌──────────────────────┐  │
│  │   MCP Control    │     │    commandPort       │  │
│  │   Panel (Qt)     │────►│    (TCP :7001)       │  │
│  └──────────────────┘     └───────────▲──────────┘  │
│                                       │             │
└───────────────────────────────────────┼─────────────┘
                                        │
                          TCP localhost:7001
                                        │
┌───────────────────────────────────────▼─────────────┐
│           Maya MCP Server (External Process)         │
│           python -m maya_mcp.server                  │
└─────────────────────────────────────────────────────┘
```

The panel controls Maya's native `commandPort` feature. The external MCP server connects to this port to send commands.

## See Also

- [Quick Start Guide](../index.md) - Getting started with Maya MCP
- [Tool Specifications](../spec/tools.md) - Available MCP tools
- [Transport Layer](../spec/transport.md) - How communication works
