---
summary: "Client configuration guide for Maya MCP with VS Code examples, generic stdio configs, and environment variable overrides."
read_when:
  - When wiring Maya MCP into an MCP client.
  - When you need a minimal working stdio configuration or want to pass environment overrides.
---

# Client Setup

Maya MCP is a local `stdio` server. In practice, most clients only need a command and optional environment variables.

## Minimal Setup

If your client accepts a plain command-based MCP server definition, this is the smallest useful config:

```json
{
  "command": "maya-mcp"
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

## Generic `mcpServers` Example

Some clients use an `mcpServers` object instead of VS Code's `servers` object. For those clients, the equivalent configuration usually looks like this:

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

## Source Checkout Workflow

If you are developing from this repo and do not want to rely on the installed CLI entrypoint, you can point the client at Python directly:

```json
{
  "servers": {
    "maya": {
      "type": "stdio",
      "command": "py",
      "args": ["-m", "maya_mcp.server"],
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

Use `python` instead of `py` on platforms that do not provide the Windows launcher.

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
