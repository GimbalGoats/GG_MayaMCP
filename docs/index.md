# Maya MCP

Welcome to the Maya MCP documentation. This project provides an MCP (Model Context Protocol) server for controlling Autodesk Maya via its commandPort socket interface.

## What is Maya MCP?

Maya MCP is a bridge between AI assistants (and other MCP-compatible clients) and Autodesk Maya. It enables:

- **Safe Remote Control** - Execute predefined operations in Maya without arbitrary code execution
- **Health Monitoring** - Track connection status and recover from Maya crashes
- **Typed Interfaces** - All tool inputs and outputs are strongly typed
- **Transport Isolation** - The MCP server never imports Maya modules directly

## Quick Start

### 1. Install Maya MCP

```bash
pip install -e ".[dev]"
```

### 2. Enable Maya commandPort

In Maya's Script Editor (Python tab):

```python
import maya.cmds as cmds

# Open Python commandPort
cmds.commandPort(name=":7001", sourceType="python", echoOutput=True)
```

### 3. Start the MCP Server

```bash
python -m maya_mcp.server
```

### 4. Configure Your MCP Client

Add to your client's MCP configuration:

```json
{
  "mcpServers": {
    "maya": {
      "command": "python",
      "args": ["-m", "maya_mcp.server"]
    }
  }
}
```

## Architecture Overview

```
┌─────────────────┐     MCP Protocol      ┌──────────────────┐
│   MCP Client    │◄────────────────────►│  Maya MCP Server │
│  (AI Assistant) │     (stdio/http)      │   (FastMCP)      │
└─────────────────┘                       └────────┬─────────┘
                                                   │
                                          TCP Socket (localhost:7001)
                                                   │
                                          ┌────────▼─────────┐
                                          │      Maya        │
                                          │  (commandPort)   │
                                          └──────────────────┘
```

## Documentation

- [Product Requirements (PRD)](prd.md) - Project goals and scope
- [Architecture Overview](spec/overview.md) - System design
- [Tool Specifications](spec/tools.md) - Available MCP tools
- [Transport Layer](spec/transport.md) - commandPort client details
- [Security Model](spec/security.md) - Security considerations
- [API Reference](api/reference.md) - Python module documentation

## Features

### v0.1.0 (Current)

- [x] FastMCP server with tool registration
- [x] Maya commandPort transport layer
- [x] Health check and connection management tools
- [x] Level 1 resilience (detect unavailable, typed errors, recover on restart)
- [x] Stub implementations for scene, nodes, and selection tools

### Planned

- [ ] Full scene query tools
- [ ] Node manipulation tools
- [ ] Selection management
- [ ] Undo/redo support
- [ ] Batch operations

## License

MIT License - see [LICENSE](https://github.com/your-org/maya-mcp/blob/main/LICENSE)
