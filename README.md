# Maya MCP

[![Python 3.10.1+](https://img.shields.io/badge/python-3.10.1%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Maya MCP is a Model Context Protocol (MCP) server for controlling Autodesk Maya through Maya's `commandPort` socket interface.

It gives MCP-compatible clients a typed tool surface for scene inspection, editing, modeling, animation, shading, skinning, scripting, and viewport capture without importing Maya modules in the server process.

## Highlights

- Transport isolation: the MCP server talks to Maya only over `commandPort`
- Localhost-only design: no remote-host support
- Typed tools: explicit schemas and predictable results
- Recovery-oriented workflow: health checks plus undo/redo support
- Broad Maya coverage: 71 tools across scene, nodes, mesh, modeling, shading, skinning, animation, curves, scripts, and viewport capture

## Quick Start

### 1. Enable Maya `commandPort`

Run this in Maya's Script Editor, Python tab:

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

### 2. Install Maya MCP

```bash
pip install maya-mcp
```

Use Python 3.10.1 or newer. Python 3.10.0 is excluded because its stdlib
`dataclasses.make_dataclass()` implementation lacks the `kw_only` support
expected by current FastMCP structured-output parsing.

From source:

```bash
git clone https://github.com/GimbalGoats/GG_MayaMCP.git
cd GG_MayaMCP
pip install -e ".[dev]"
```

### 3. Start the server

```bash
maya-mcp
```

Or:

```bash
python -m maya_mcp.server
```

From a local source checkout, direct script launch also works:

```bash
python src/maya_mcp/server.py
```

### 4. Configure your MCP client

Example stdio configuration:

```json
{
  "mcpServers": {
    "maya": {
      "command": "maya-mcp"
    }
  }
}
```

## Client Examples

### Claude Desktop

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

### Cursor

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

### VS Code MCP

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

## Tool Surface

Maya MCP currently exposes 71 tools:

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

`script.run` is disabled by default and requires `MAYA_MCP_ENABLE_RAW_EXECUTION=true`.

## Architecture

The runtime split is:

1. An MCP client communicates with `maya_mcp.server` over stdio.
2. The server dispatches typed tools implemented in `src/maya_mcp/tools/`.
3. The transport layer in `src/maya_mcp/transport/commandport.py` sends commands to Maya over `localhost`.
4. Maya executes the request inside its own process through `commandPort`.

The server process never imports `maya.cmds`.

## Documentation

- [Docs Home](docs/index.md)
- [Architecture Overview](docs/spec/overview.md)
- [Transport Specification](docs/spec/transport.md)
- [Security Specification](docs/spec/security.md)
- [Tool Specification](docs/spec/tools.md)
- [API Reference](docs/api/reference.md)
- [Maya Control Panel](docs/usage/maya-panel.md)

## Development

Repository commands on this machine use `py`:

```bash
py -m ruff check .
py -m ruff format .
py -m mypy src/
py -m pytest
```

If tests resolve `maya_mcp` from `site-packages` instead of this repo:

```powershell
$env:PYTHONPATH='src'
py -m pytest
```

## Security Notes

- Localhost only
- No direct Maya imports in the MCP server process
- No remote-host support
- No arbitrary code execution by default
- No secrets or raw tracebacks in client-facing errors

## License

MIT. See [LICENSE](LICENSE).
