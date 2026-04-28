---
summary: "Step-by-step setup guide for installing Maya MCP, opening Maya commandPort, starting the server, and verifying the connection."
read_when:
  - When setting up Maya MCP for the first time.
  - When you need the shortest path from install to a working client connection.
---

# Getting Started

This page is the fastest reliable setup path.

## Before You Start

You need:

- Autodesk Maya running on the same machine as the MCP server
- Python 3.10.1 or newer
- an MCP client that can start a local `stdio` server

Python 3.10.0 is intentionally excluded because current FastMCP structured-output parsing depends on a newer `dataclasses` implementation.

## 1. Install Maya MCP

From PyPI:

```bash
pip install maya-mcp
```

On Windows:

```powershell
py -m pip install maya-mcp
```

From a source checkout:

```bash
pip install -e ".[dev]"
```

On Windows, the repo examples use `py`:

```powershell
py -m pip install -e ".[dev]"
```

## 2. Open Maya `commandPort`

Open Maya, then run this in the Script Editor on the Python tab:

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

This opens the default port that Maya MCP expects: `localhost:7001`.

If you prefer using the helper script from this repo, use `scripts/enable_commandport.py`.

## 3. Start the MCP Server

Installed package:

```bash
maya-mcp
```

Module entrypoint:

```bash
python -m maya_mcp.server
```

On Windows:

```powershell
py -m maya_mcp.server
```

Direct script launch from a source checkout:

```bash
python src/maya_mcp/server.py
```

If you are working from this repo and want to use the FastMCP CLI, the checked-in `fastmcp.json` also works:

```bash
fastmcp run
```

That follows current FastMCP guidance for portable project configuration.

## 4. Add the Server to Your Client

Use [Client Setup](client-setup.md).

Most users should pick the client-specific examples there:

- Codex CLI / IDE extension: `~/.codex/config.toml`
- Claude Code: `.mcp.json`
- Claude Desktop extension: packaged MCPB, see [Claude Desktop Extension](claude-desktop-extension.md)
- VS Code: `.vscode/mcp.json`

For Codex CLI and Claude Code on Windows, `py -m maya_mcp.server` is usually more reliable than depending on the `maya-mcp` console script being on `PATH`.

## 5. Verify It Works

Use your client to call these in order:

1. `health.check`
2. `scene.info`
3. `nodes.list`

What to expect:

- `health.check` should report `ok` when Maya is reachable
- `scene.info` should return scene metadata even in a new empty scene
- `nodes.list` should return a bounded list, not a huge scene dump

## Useful Environment Variables

You usually do not need these at first, but they are the main knobs:

| Variable | Default | Use |
|---|---:|---|
| `MAYA_MCP_HOST` | `localhost` | Leave as default; remote hosts are not supported |
| `MAYA_MCP_PORT` | `7001` | Change if Maya listens on another port |
| `MAYA_MCP_CONNECT_TIMEOUT` | `5.0` | Longer wait for initial connection |
| `MAYA_MCP_COMMAND_TIMEOUT` | `30.0` | Longer wait for slow Maya operations |
| `MAYA_MCP_MAX_RETRIES` | `3` | More reconnect attempts |
| `MAYA_MCP_SCRIPT_DIRS` | empty | Allowlisted directories for `script.list` and `script.execute` |
| `MAYA_MCP_ENABLE_RAW_EXECUTION` | `false` | Enables `script.run` |
| `MAYA_MCP_SCRIPT_TIMEOUT` | `60` | Default timeout for script tools |

## First Troubleshooting Checks

If `health.check` is failing:

- confirm Maya is running on the same machine
- confirm `commandPort` is open on `:7001`
- confirm your client is launching the same Python environment where `maya-mcp` is installed
- if you changed the port in Maya, also set `MAYA_MCP_PORT`

If the server starts but tools cannot connect:

- call `maya.connect` explicitly once
- restart Maya after changing `commandPort` setup
- restart the MCP server after changing local code in a source checkout

## Where To Go Next

- [Client Setup](client-setup.md)
- [Tool Guide](../spec/tools.md)
- [Maya Control Panel](maya-panel.md)
