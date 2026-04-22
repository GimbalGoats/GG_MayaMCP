---
summary: "Documentation entrypoint with quick start, tool coverage, and links to canonical project docs."
read_when:
  - When first orienting to Maya MCP or deciding which project doc to read next.
  - When updating quick-start setup, client configuration, or the high-level tool coverage table.
---

# Maya MCP

Maya MCP is an MCP server for controlling Autodesk Maya through `commandPort`.

This documentation set is the canonical reference for repository behavior, architecture, and tool contracts.

## What Maya MCP Provides

- Typed MCP tools for common Maya workflows
- A transport layer isolated from Maya imports
- Localhost-only communication with Maya
- Capability-gated scene safety prompts for unsaved-change confirmations on
  `scene.new` and `scene.open`
- Recovery-oriented behavior for Maya restarts and failed operations
- A dockable in-Maya control panel for managing `commandPort`

## Quick Start

### Install

```bash
pip install maya-mcp
```

From source:

```bash
pip install -e ".[dev]"
```

The server targets the current FastMCP 3 line: `fastmcp>=3.2.4,<4`.
Use Python 3.10.1 or newer. Python 3.10.0 is excluded because its stdlib
`dataclasses.make_dataclass()` implementation is not compatible with current
FastMCP structured-output parsing.

### Enable Maya `commandPort`

Run this in Maya:

```python
import maya.cmds as cmds

try:
    cmds.commandPort(name=":7001", close=True)
except RuntimeError:
    pass

cmds.commandPort(
    name=":7001",
    sourceType="python",
    echoOutput=True,
)
```

### Start the MCP server

```bash
maya-mcp
```

Or:

```bash
python -m maya_mcp.server
```

For local development from a source checkout, direct script launch is also
supported:

```bash
python src/maya_mcp/server.py
```

### Configure a client

```json
{
  "mcpServers": {
    "maya": {
      "command": "maya-mcp"
    }
  }
}
```

## Tool Coverage

Maya MCP currently exposes 71 tools across these areas:

| Category | Tools |
|----------|-------|
| Health | `health.check` |
| Connection | `maya.connect`, `maya.disconnect` |
| Scene | `scene.info`, `scene.new`, `scene.open`, `scene.save`, `scene.save_as`, `scene.import`, `scene.export`, `scene.undo`, `scene.redo` |
| Nodes | `nodes.list`, `nodes.create`, `nodes.delete`, `nodes.rename`, `nodes.parent`, `nodes.duplicate`, `nodes.info` |
| Attributes | `attributes.get`, `attributes.set` |
| Selection | `selection.get`, `selection.set`, `selection.clear`, `selection.set_components`, `selection.get_components`, `selection.convert_components` |
| Connections | `connections.list`, `connections.get`, `connections.connect`, `connections.disconnect`, `connections.history` |
| Mesh | `mesh.info`, `mesh.vertices`, `mesh.evaluate` |
| Viewport | `viewport.capture` |
| Modeling | `modeling.create_polygon_primitive`, `modeling.extrude_faces`, `modeling.boolean`, `modeling.combine`, `modeling.separate`, `modeling.merge_vertices`, `modeling.bevel`, `modeling.bridge`, `modeling.insert_edge_loop`, `modeling.delete_faces`, `modeling.move_components`, `modeling.freeze_transforms`, `modeling.delete_history`, `modeling.center_pivot`, `modeling.set_pivot` |
| Shading | `shading.create_material`, `shading.assign_material`, `shading.set_material_color` |
| Skinning | `skin.bind`, `skin.unbind`, `skin.influences`, `skin.weights.get`, `skin.weights.set`, `skin.copy_weights` |
| Animation | `animation.set_time`, `animation.get_time_range`, `animation.set_time_range`, `animation.set_keyframe`, `animation.get_keyframes`, `animation.delete_keyframes` |
| Curves | `curve.info`, `curve.cvs` |
| Scripts | `script.list`, `script.execute`, `script.run` |

For scene replacement operations, `scene.new` and `scene.open` still refuse by
default when the current scene has unsaved changes. Clients that advertise MCP
form elicitation can receive an in-band discard-changes confirmation instead of
having to retry explicitly with `force=true`.

## Read Next

- [Architecture Overview](spec/overview.md)
- [Transport Specification](spec/transport.md)
- [Security Specification](spec/security.md)
- [Tool Specification](spec/tools.md)
- [API Reference](api/reference.md)
- [Maya Control Panel](usage/maya-panel.md)
- [ADR-0001 CommandPort](adr/0001-commandport.md)
- [PRD](prd.md)
