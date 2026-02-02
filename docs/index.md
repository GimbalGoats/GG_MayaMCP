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
pip install maya-mcp
# Or from source:
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
maya-mcp
# Or:
python -m maya_mcp.server
```

### 4. Configure Your MCP Client

Add to your client's MCP configuration:

```json
{
  "mcpServers": {
    "maya": {
      "command": "maya-mcp"
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

| Document | Description |
|----------|-------------|
| [Product Requirements (PRD)](prd.md) | **Project goals, scope, and roadmap** |
| [Architecture Overview](spec/overview.md) | System design and components |
| [Tool Specifications](spec/tools.md) | Available MCP tools and their APIs |
| [Transport Layer](spec/transport.md) | commandPort client details |
| [Security Model](spec/security.md) | Security considerations |
| [API Reference](api/reference.md) | Python module documentation |

> **📋 Roadmap**: See the [Milestones section in the PRD](prd.md#milestones) for the complete project roadmap. The PRD is the single source of truth for all planned work.

## Current Status

### Completed (v0.1.0)

| Milestone | Status | Description |
|-----------|--------|-------------|
| M0: Scaffold | ✅ | Project structure, transport layer, test infrastructure |
| M1: Core Tools | ✅ | `scene.info`, `nodes.list`, `selection.get/set` |
| M2: Extended Tools | ✅ | `attributes.get/set`, `nodes.create/delete`, `scene.undo/redo` |

### Available Tools

| Category | Tools |
|----------|-------|
| **Health** | `health.check` |
| **Connection** | `maya.connect`, `maya.disconnect` |
| **Scene** | `scene.info`, `scene.undo`, `scene.redo` |
| **Nodes** | `nodes.list`, `nodes.create`, `nodes.delete` |
| **Attributes** | `attributes.get`, `attributes.set` |
| **Selection** | `selection.get`, `selection.set`, `selection.clear` |

### Planned

See [PRD Milestones](prd.md#milestones) for the complete roadmap:

- **M3**: Maya UI Panel + LLM Optimization
- **M4**: Scene Operations (file management)
- **M5**: Animation & Rigging
- **M6**: Production Hardening (nice to have)

## Design Principles

Maya MCP follows best practices from [Block's MCP Playbook](https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers):

1. **Workflow-first design** - Tools match how AI agents work, not Maya's API
2. **Token budget awareness** - Default limits on large responses
3. **Tool annotations** - Semantic hints for safe AI decision-making
4. **Single risk level per tool** - Read-only and write operations are separate

## License

MIT License - see [LICENSE](https://gitlab.pixel-nexus.com/rigging/gg_mayamcp/-/blob/main/LICENSE)
