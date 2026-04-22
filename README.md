# Maya MCP

[![Python 3.10.1+](https://img.shields.io/badge/python-3.10.1%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Maya MCP is a local Model Context Protocol server for controlling Autodesk Maya through Maya's `commandPort`.

It gives MCP clients a typed tool surface for scene work, nodes, selection, modeling, shading, skinning, animation, curves, scripts, and viewport capture without importing Maya modules in the server process.

This project is unofficial and is not affiliated with or endorsed by Autodesk. Autodesk Maya is a trademark of Autodesk, Inc.

## Why Use It

- runs outside Maya, so the server stays isolated from Maya imports
- talks to Maya over `localhost` only
- exposes 71 typed tools instead of raw API calls
- supports safer scene replacement flows for unsaved changes
- leaves raw code execution disabled unless you opt in

## Quick Start

### 1. Install

```bash
pip install maya-mcp
```

From source:

```bash
pip install -e ".[dev]"
```

### 2. Open Maya `commandPort`

Run this in Maya's Script Editor on the Python tab:

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

### 3. Start the server

```bash
maya-mcp
```

Other supported launch styles:

```bash
python -m maya_mcp.server
python src/maya_mcp/server.py
fastmcp run
```

`fastmcp run` works from this repo because it includes `fastmcp.json`.

### 4. Add it to your client

Minimal generic config:

```json
{
  "command": "maya-mcp"
}
```

VS Code workspace example in `.vscode/mcp.json`:

```json
{
  "servers": {
    "maya": {
      "type": "stdio",
      "command": "maya-mcp"
    }
  }
}
```

### 5. Verify

Call these tools in order:

1. `health.check`
2. `scene.info`
3. `nodes.list`

## Tool Coverage

| Family | Count |
|---|---:|
| `health` | 1 |
| `maya` | 2 |
| `scene` | 9 |
| `nodes` | 7 |
| `attributes` | 2 |
| `selection` | 6 |
| `connections` | 5 |
| `mesh` | 3 |
| `viewport` | 1 |
| `modeling` | 15 |
| `shading` | 3 |
| `skin` | 6 |
| `animation` | 6 |
| `curve` | 2 |
| `script` | 3 |

`script.run` is disabled by default and requires `MAYA_MCP_ENABLE_RAW_EXECUTION=true`.

`scene.new` and `scene.open` still refuse by default when the current scene has unsaved changes. Clients that advertise MCP form elicitation can receive an in-band discard-changes confirmation instead of having to retry with `force=True`.

## Main Docs

- [Docs Home](docs/index.md)
- [Getting Started](docs/usage/getting-started.md)
- [Client Setup](docs/usage/client-setup.md)
- [Tool Guide](docs/spec/tools.md)
- [Architecture Overview](docs/spec/overview.md)
- [Transport Specification](docs/spec/transport.md)
- [Security Specification](docs/spec/security.md)
- [API Reference](docs/api/reference.md)

Published docs: <https://gimbalgoats.github.io/GG_MayaMCP/>

## Development

This repo uses `py` for Python commands on Windows:

```powershell
py -m ruff check .
py -m ruff format .
py -m mypy src/
py -m pytest
```

If tests import `maya_mcp` from `site-packages` instead of this repo:

```powershell
$env:PYTHONPATH='src'
py -m pytest
```

## Security Notes

- localhost only
- no remote-host support
- no Maya imports in the MCP server process
- no arbitrary code execution by default
- no secrets or raw tracebacks in client-facing errors

## License

MIT. See [LICENSE](LICENSE).
