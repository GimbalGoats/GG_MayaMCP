# Maya MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP (Model Context Protocol) server for controlling Autodesk Maya via its commandPort socket interface.

## Overview

Maya MCP enables AI assistants to interact with a running Maya instance. It provides a typed, safe interface for:

- Querying scene information
- Managing selections
- Manipulating nodes
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
git clone https://gitlab.pixel-nexus.com/rigging/gg_mayamcp.git
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

| Tool | Description |
|------|-------------|
| `health.check` | Check Maya connection status |
| `maya.connect` | Connect to Maya commandPort |
| `maya.disconnect` | Close Maya connection |
| `scene.info` | Get current scene information |
| `nodes.list` | List nodes by type/pattern |
| `selection.get` | Get current selection |
| `selection.set` | Set selection |

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
git clone https://gitlab.pixel-nexus.com/rigging/gg_mayamcp.git
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
│   │   └── selection.py
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
