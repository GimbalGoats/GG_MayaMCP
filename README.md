# Maya MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP (Model Context Protocol) server for controlling Autodesk Maya via its commandPort socket interface.

## Overview

Maya MCP enables AI assistants to interact with a running Maya instance. It provides a typed, safe interface for:

- Querying scene information and managing files
- Manipulating nodes, attributes, and connections
- Polygon modeling (primitives, extrude, bevel, boolean, combine/separate)
- Material creation and assignment
- Skin binding and weight management
- Keyframe animation and timeline control
- NURBS curve inspection
- Component-level mesh selection and editing
- Python/MEL script execution
- Health monitoring and connection management

**Key Design Principles:**

- **No arbitrary code execution** - All operations are explicit, typed tools
- **Localhost-only** - Security-first design
- **Crash-resilient** - Detects Maya unavailability and recovers gracefully
- **Transport isolation** - MCP server never imports `maya.cmds`

---

## Quick Start

### 1. Enable Maya commandPort

In Maya's Script Editor (Python tab), run:

```python
import maya.cmds as cmds

# Close any existing port
try:
    cmds.commandPort(name=":7001", close=True)
except RuntimeError:
    pass

# Open Python commandPort on localhost:7001
cmds.commandPort(name=":7001", sourceType="python", echoOutput=True)
print("commandPort opened on :7001")
```

> **Tip:** Add this to your `userSetup.py` to auto-enable on Maya startup.

### 2. Install Maya MCP

**Option A: Using uvx (Recommended)**
```bash
uvx maya-mcp
```

**Option B: Using pip**
```bash
pip install maya-mcp
```

**Option C: From source**
```bash
git clone https://github.com/GimbalGoats/GG_MayaMCP.git
cd gg_mayamcp
pip install -e .
```

### 3. Configure Your AI Client

See [Client Configuration](#client-configuration) below for Claude Desktop, Cursor, VS Code, etc.

---

## Installation

### Prerequisites

- Python 3.10+
- Autodesk Maya 2022+ with commandPort enabled
- An MCP-compatible AI client

### Install Methods

| Method | Command | Best For |
|--------|---------|----------|
| **uvx** | `uvx maya-mcp` | Quick use, always latest |
| **pipx** | `pipx install maya-mcp` | Isolated install |
| **pip** | `pip install maya-mcp` | Traditional install |
| **Source** | `pip install -e .` | Development |

### Verify Installation

```bash
# Check the CLI is available
maya-mcp --help

# Or run directly
python -m maya_mcp.server
```

---

## Client Configuration

### Claude Desktop

**Config location:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "maya": {
      "command": "maya-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

**Alternative (using uvx):**
```json
{
  "mcpServers": {
    "maya": {
      "command": "uvx",
      "args": ["maya-mcp"],
      "env": {}
    }
  }
}
```

**Check status:** Settings → Developer → MCP Servers

---

### Cursor

**Config location:**
- Project: `.cursor/mcp.json`
- Global: `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "maya": {
      "command": "maya-mcp",
      "args": []
    }
  }
}
```

**Check status:** Output panel → "MCP Logs"

---

### VS Code (GitHub Copilot)

**Config location:** `.vscode/mcp.json`

```json
{
  "servers": {
    "maya": {
      "type": "stdio",
      "command": "maya-mcp",
      "args": []
    }
  }
}
```

**Check status:** Command Palette → "MCP: List Servers"

---

### OpenCode

**Config location:** `opencode.jsonc` (or `opencode.json`) in project root

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "maya": {
      "type": "local",
      "command": ["uvx", "maya-mcp"],
      "enabled": true
    }
  }
}
```

**Alternative (using pip install):**
```jsonc
{
  "mcp": {
    "maya": {
      "type": "local",
      "command": ["maya-mcp"],
      "enabled": true
    }
  }
}
```

**Important:** Restart OpenCode after editing config for changes to take effect.

---

### Using FastMCP CLI

If you have FastMCP installed, you can auto-configure clients:

```bash
# Auto-install into Claude Desktop
fastmcp install claude-desktop

# Auto-install into Cursor
fastmcp install cursor

# Generate MCP JSON config
fastmcp install mcp-json
```

---

## Available Tools

### Connection & Scene

| Tool | Description |
|------|-------------|
| `health.check` | Check Maya connection status |
| `maya.connect` | Connect to Maya commandPort |
| `maya.disconnect` | Close Maya connection |
| `scene.info` | Get current scene information |
| `scene.new` | Create new scene (with unsaved changes safety check) |
| `scene.open` | Open scene file (with path validation) |
| `scene.save` | Save current scene |
| `scene.save_as` | Save scene to a new file path |
| `scene.import` | Import file into current scene |
| `scene.export` | Export selection or entire scene |
| `scene.undo` | Undo last operation (LLM error recovery) |
| `scene.redo` | Redo last undone operation |

### Nodes & Attributes

| Tool | Description |
|------|-------------|
| `nodes.list` | List nodes by type/pattern (default limit: 500) |
| `nodes.create` | Create node with optional name, parent, and attributes |
| `nodes.delete` | Delete nodes with optional hierarchy |
| `nodes.rename` | Rename nodes (batch support) |
| `nodes.parent` | Reparent nodes in hierarchy |
| `nodes.duplicate` | Duplicate nodes with hierarchy |
| `nodes.info` | Get comprehensive node info (summary, transform, hierarchy, attributes, shape, or all) |
| `attributes.get` | Get attribute values (batch support) |
| `attributes.set` | Set attribute values (batch support) |

### Selection

| Tool | Description |
|------|-------------|
| `selection.get` | Get current selection |
| `selection.set` | Set/add/remove selection |
| `selection.clear` | Clear selection |
| `selection.set_components` | Select mesh components (vertices, edges, faces) |
| `selection.get_components` | Get selected components grouped by type |
| `selection.convert_components` | Convert selection between vertex/edge/face |

### Connections

| Tool | Description |
|------|-------------|
| `connections.list` | List connections on a node with direction/type filters |
| `connections.get` | Get connection details for specific attributes |
| `connections.connect` | Connect two attributes |
| `connections.disconnect` | Disconnect attributes |
| `connections.history` | List construction/deformation history |

### Mesh

| Tool | Description |
|------|-------------|
| `mesh.info` | Get mesh statistics (vertex/face/edge counts, bounding box, UVs) |
| `mesh.vertices` | Query vertex positions with pagination |
| `mesh.evaluate` | Analyze mesh topology (non-manifold, lamina, holes, borders) |

### Modeling

| Tool | Description |
|------|-------------|
| `modeling.create_polygon_primitive` | Create cube, sphere, cylinder, cone, torus, or plane |
| `modeling.extrude_faces` | Extrude polygon faces with translation and offset |
| `modeling.boolean` | Boolean union, difference, or intersection |
| `modeling.combine` | Combine multiple meshes into one |
| `modeling.separate` | Separate a combined mesh |
| `modeling.merge_vertices` | Merge vertices within a distance threshold |
| `modeling.bevel` | Bevel edges or vertices |
| `modeling.bridge` | Bridge between edge loops |
| `modeling.insert_edge_loop` | Insert edge loop at an edge |
| `modeling.delete_faces` | Delete polygon faces |
| `modeling.move_components` | Move vertices, edges, or faces |
| `modeling.freeze_transforms` | Freeze transforms to identity |
| `modeling.delete_history` | Delete construction history |
| `modeling.center_pivot` | Center pivot point |
| `modeling.set_pivot` | Set pivot to explicit position |

### Shading

| Tool | Description |
|------|-------------|
| `shading.create_material` | Create material (lambert, blinn, phong, standardSurface) with shading group |
| `shading.assign_material` | Assign material to meshes or face components |
| `shading.set_material_color` | Set color attribute on a material |

### Skinning

| Tool | Description |
|------|-------------|
| `skin.bind` | Bind mesh to skeleton with influence options |
| `skin.unbind` | Detach skin cluster from mesh |
| `skin.influences` | List influences on a skin cluster |
| `skin.weights.get` | Get per-vertex skin weights with pagination |
| `skin.weights.set` | Set per-vertex skin weights with normalization |
| `skin.copy_weights` | Copy weights between meshes |

### Animation

| Tool | Description |
|------|-------------|
| `animation.set_time` | Set the current time (go to a specific frame) |
| `animation.get_time_range` | Get playback range, animation range, and current time |
| `animation.set_time_range` | Set the playback and animation range |
| `animation.set_keyframe` | Set keyframe on attribute(s) at current or specified time |
| `animation.get_keyframes` | Query keyframes for attribute(s) in a time range |
| `animation.delete_keyframes` | Delete keyframes in range for attribute(s) |

### Curves

| Tool | Description |
|------|-------------|
| `curve.info` | Get NURBS curve information (degree, spans, form, CV count, length) |
| `curve.cvs` | Query CV positions from a NURBS curve with pagination |

### Scripts

| Tool | Description |
|------|-------------|
| `script.list` | List available Python scripts from configured directories |
| `script.execute` | Execute a Python script file from an allowed directory in Maya |
| `script.run` | Execute raw Python or MEL code in Maya (requires opt-in env var) |

---

## Troubleshooting

### Server won't start

1. **Check Python version:** `python --version` (need 3.10+)
2. **Check installation:** `pip show maya-mcp`
3. **Run directly:** `python -m maya_mcp.server`

### Can't connect to Maya

1. **Verify commandPort is open in Maya:**
   ```python
   import maya.cmds as cmds
   print(cmds.commandPort(query=True, listPorts=True))
   ```

2. **Check port 7001 is listening:**
   ```bash
   # Windows
   netstat -an | findstr 7001
   
   # macOS/Linux
   lsof -i :7001
   ```

3. **Test connection manually:**
   ```python
   import socket
   s = socket.socket()
   s.connect(("localhost", 7001))
   s.send(b"print('hello')\n")
   print(s.recv(1024))
   s.close()
   ```

### Client can't find server

1. **Verify config path is correct** (see Client Configuration above)
2. **Restart the AI client** after editing config
3. **Check client logs:**
   - Claude Desktop: `%APPDATA%\Claude\logs\` (Windows) or `~/Library/Logs/Claude/` (macOS)
   - Cursor: Output panel → "MCP Logs"
   - VS Code: "MCP: List Servers" command

### Windows-specific issues

Add these environment variables to your config if needed:

```json
{
  "mcpServers": {
    "maya": {
      "command": "maya-mcp",
      "args": [],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

---

## Updating

```bash
# Using uvx (always runs latest)
uvx maya-mcp

# Using pipx
pipx upgrade maya-mcp

# Using pip
pip install --upgrade maya-mcp

# From source
git pull
pip install -e .
```

---

## Development

```bash
# Clone and install with dev dependencies
git clone https://github.com/GimbalGoats/GG_MayaMCP.git
cd gg_mayamcp
pip install -e ".[dev]"

# Run linting
ruff check . && ruff format .

# Run type checking
mypy src/

# Run tests
pytest

# Build documentation
mkdocs serve
```

---

## Architecture

```
maya-mcp/
├── src/maya_mcp/
│   ├── server.py          # FastMCP server entrypoint
│   ├── errors.py          # Typed error hierarchy
│   ├── types.py           # Shared type definitions
│   ├── tools/             # MCP tool implementations
│   │   ├── health.py
│   │   ├── connection.py
│   │   ├── scene.py
│   │   ├── nodes.py
│   │   ├── attributes.py
│   │   ├── selection.py
│   │   ├── connections.py
│   │   ├── mesh.py
│   │   ├── modeling.py
│   │   ├── shading.py
│   │   ├── skin.py
│   │   ├── animation.py
│   │   ├── curve.py
│   │   └── scripts.py
│   ├── utils/             # Shared utilities
│   │   ├── validation.py
│   │   ├── parsing.py
│   │   └── response_guard.py
│   └── transport/
│       └── commandport.py # Maya commandPort TCP client
├── tests/                 # Pytest test suite
├── docs/                  # MkDocs documentation
└── fastmcp.json           # FastMCP configuration
```

---

## Documentation

- [Tool Specifications](docs/spec/tools.md)
- [Transport Layer](docs/spec/transport.md)
- [Security Model](docs/spec/security.md)
- [Architecture Overview](docs/spec/overview.md)

---

## License

MIT License - see [LICENSE](LICENSE) for details.
