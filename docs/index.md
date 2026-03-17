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

## Available Tools (70 total)

| Category | Tools |
|----------|-------|
| **Health** | `health.check` |
| **Connection** | `maya.connect`, `maya.disconnect` |
| **Scene** | `scene.info`, `scene.new`, `scene.open`, `scene.save`, `scene.save_as`, `scene.import`, `scene.export`, `scene.undo`, `scene.redo` |
| **Nodes** | `nodes.list`, `nodes.create`, `nodes.delete`, `nodes.rename`, `nodes.parent`, `nodes.duplicate`, `nodes.info` |
| **Attributes** | `attributes.get`, `attributes.set` |
| **Selection** | `selection.get`, `selection.set`, `selection.clear`, `selection.set_components`, `selection.get_components`, `selection.convert_components` |
| **Connections** | `connections.list`, `connections.get`, `connections.connect`, `connections.disconnect`, `connections.history` |
| **Mesh** | `mesh.info`, `mesh.vertices`, `mesh.evaluate` |
| **Modeling** | `modeling.create_polygon_primitive`, `modeling.extrude_faces`, `modeling.boolean`, `modeling.combine`, `modeling.separate`, `modeling.merge_vertices`, `modeling.bevel`, `modeling.bridge`, `modeling.insert_edge_loop`, `modeling.delete_faces`, `modeling.move_components`, `modeling.freeze_transforms`, `modeling.delete_history`, `modeling.center_pivot`, `modeling.set_pivot` |
| **Shading** | `shading.create_material`, `shading.assign_material`, `shading.set_material_color` |
| **Skinning** | `skin.bind`, `skin.unbind`, `skin.influences`, `skin.weights.get`, `skin.weights.set`, `skin.copy_weights` |
| **Animation** | `animation.set_time`, `animation.get_time_range`, `animation.set_time_range`, `animation.set_keyframe`, `animation.get_keyframes`, `animation.delete_keyframes` |
| **Curves** | `curve.info`, `curve.cvs` |
| **Scripts** | `script.list`, `script.execute`, `script.run` |

## Design Principles

Maya MCP follows best practices from [Block's MCP Playbook](https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers):

1. **Workflow-first design** - Tools match how AI agents work, not Maya's API
2. **Token budget awareness** - Default limits on large responses
3. **Tool annotations** - Semantic hints for safe AI decision-making
4. **Single risk level per tool** - Read-only and write operations are separate

## License

MIT License - see [LICENSE](https://github.com/GimbalGoats/GG_MayaMCP/blob/main/LICENSE)
