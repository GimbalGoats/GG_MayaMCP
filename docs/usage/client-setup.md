---
summary: "Client configuration guide for Maya MCP with VS Code examples, generic stdio configs, and environment variable overrides."
read_when:
  - When wiring Maya MCP into an MCP client.
  - When you need a minimal working stdio configuration or want to pass environment overrides.
---

# Client Setup

Maya MCP is a local `stdio` server, but the config file shape depends on the client.

For Codex CLI and Claude Code on Windows, `py -m maya_mcp.server` is usually more reliable than depending on the `maya-mcp` console script being on the active `PATH`.

## Codex CLI / IDE Extension

Codex reads MCP server config from `~/.codex/config.toml`. The CLI and IDE extension share that config.

Installed package:

```toml
[mcp_servers.maya]
command = "maya-mcp"
```

Source checkout or Windows-friendly setup:

```toml
[mcp_servers.maya]
command = "py"
args = ["-m", "maya_mcp.server"]
env = { PYTHONPATH = "src" }
```

Use the `PYTHONPATH` line only when running from a source checkout.
Use `python` instead of `py` on platforms that do not provide the Windows launcher.

## Claude Code

Claude Code project-scoped MCP servers live in `.mcp.json`.

Installed package:

```json
{
  "mcpServers": {
    "maya-mcp": {
      "command": "maya-mcp",
      "args": []
    }
  }
}
```

Source checkout or Windows-friendly setup:

```json
{
  "mcpServers": {
    "maya-mcp": {
      "command": "py",
      "args": ["-m", "maya_mcp.server"],
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

## VS Code

Current VS Code docs support workspace-level MCP config in `.vscode/mcp.json`.

Minimal example:

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

With environment overrides:

```json
{
  "servers": {
    "maya": {
      "type": "stdio",
      "command": "maya-mcp",
      "env": {
        "MAYA_MCP_PORT": "7002",
        "MAYA_MCP_SCRIPT_DIRS": "C:/maya-scripts;D:/shared-maya-scripts"
      }
    }
  }
}
```

Use this when:

- Maya is listening on a non-default port
- you want to enable script discovery from approved folders

## Other MCP Clients

Some clients use a generic `mcpServers` object instead of VS Code's `servers` object. For those clients, the equivalent configuration usually looks like this:

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

If your client has its own config file shape, keep the launch command the same and adapt only the surrounding JSON.

## FastMCP Project Config

This repo includes `fastmcp.json`, which follows current FastMCP project-configuration guidance.

That matters if you want to:

- run the server with `fastmcp run`
- keep a portable server config checked into the repo
- use the same config across local tooling and IDEs

Example:

```bash
fastmcp run
```

## Recommended First Calls

After the client can start the server, test in this order:

1. `health.check`
2. `maya.connect`
3. `scene.info`

If `health.check` already reports `ok`, you usually do not need to call `maya.connect` manually.

## Common Mistakes

- The client starts a different Python environment than the one where `maya-mcp` is installed.
- Maya is using a different `commandPort` port than the server expects.
- `MAYA_MCP_SCRIPT_DIRS` uses relative paths instead of absolute directories.
- `script.run` is expected to work without setting `MAYA_MCP_ENABLE_RAW_EXECUTION=true`.

## Related Docs

- [Getting Started](getting-started.md)
- [Tool Guide](../spec/tools.md)
- [Security Specification](../spec/security.md)
