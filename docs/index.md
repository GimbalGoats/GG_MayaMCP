---
summary: "Friendly docs home for installing Maya MCP, connecting a client, and finding the right reference page."
read_when:
  - When first orienting to Maya MCP.
  - When you want the fastest path to install, connect, and use the server.
---

# Maya MCP

Maya MCP is a local MCP server for controlling Autodesk Maya through Maya's `commandPort`.

It is designed for practical AI-assisted Maya work:

- run the MCP server outside Maya
- keep Maya communication on `localhost`
- expose typed tools instead of raw Maya APIs
- keep read-only and mutating actions easy to reason about

## Start Here

If you just want it working:

1. Read [Getting Started](usage/getting-started.md)
2. Add it to your client with [Client Setup](usage/client-setup.md)
3. Skim [Tool Guide](spec/tools.md) so you know what is available

If you are changing the project:

- [Architecture Overview](spec/overview.md)
- [Transport Specification](spec/transport.md)
- [Security Specification](spec/security.md)
- [ADR-0001 CommandPort](adr/0001-commandport.md)

## What You Get

Maya MCP currently exposes 71 tools across these families:

| Family | Count | Typical use |
|---|---:|---|
| `health` | 1 | Check whether Maya is reachable |
| `maya` | 2 | Manually connect or disconnect the transport |
| `scene` | 9 | Open, save, import, export, undo, redo |
| `nodes` | 7 | List, create, rename, parent, duplicate, inspect |
| `attributes` | 2 | Read and write attributes |
| `selection` | 6 | Manage object and component selections |
| `connections` | 5 | Inspect and edit DG connections |
| `mesh` | 3 | Inspect topology and vertex data |
| `viewport` | 1 | Capture screenshots from Maya |
| `modeling` | 15 | Common polygon modeling actions |
| `shading` | 3 | Create and assign materials |
| `skin` | 6 | Bind, inspect, and edit skin weights |
| `animation` | 6 | Timeline and keyframe workflows |
| `curve` | 2 | Inspect NURBS curves |
| `script` | 3 | Discover and run approved scripts, with opt-in raw execution |

## Five-Minute Setup

1. Install `maya-mcp`

```bash
pip install maya-mcp
```

2. Open Maya `commandPort`

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
    noreturn=False,
    bufferSize=16384,
)
```

3. Start the server

```bash
maya-mcp
```

4. Add it to your MCP client

Use the examples in [Client Setup](usage/client-setup.md).

5. Call `health.check`

If that succeeds, try `scene.info` or `nodes.list`.

## Guardrails

These are the rules that shape the whole project:

- The MCP server process does not import `maya.cmds`.
- Maya communication stays on `localhost` only.
- `script.run` is disabled unless `MAYA_MCP_ENABLE_RAW_EXECUTION=true`.
- Large results use limits, truncation, or pagination where needed.
- Exact tool schemas are exposed through MCP `tools/list` metadata.

## Documentation Map

- [Getting Started](usage/getting-started.md): install, run, verify
- [Client Setup](usage/client-setup.md): VS Code and generic stdio examples
- [Maya Control Panel](usage/maya-panel.md): optional in-Maya UI for managing `commandPort`
- [Tool Guide](spec/tools.md): tool families, defaults, limits, and risk model
- [Architecture Overview](spec/overview.md): runtime shape and module layout
- [Transport Specification](spec/transport.md): connection lifecycle, retries, errors
- [Security Specification](spec/security.md): localhost-only and script-execution trust model
- [API Reference](api/reference.md): generated Python API docs
- [PRD](prd.md): scope and planned direction
