# Maya MCP Claude Desktop Extension

Maya MCP is a local MCP server for controlling Autodesk Maya through Maya's
`commandPort`. This bundle runs on the user's workstation, communicates over
stdio with Claude Desktop, and connects only to Maya on `localhost`.

## Requirements

- Claude Desktop with desktop extensions enabled.
- Autodesk Maya running on the same machine.
- Maya `commandPort` open on the configured local port, usually `7001`.
- For building from source, Node/npm and the MCPB CLI.

## Build From Source

Install MCPB into a user-local npm prefix:

```powershell
npm install --prefix "$env:USERPROFILE\.tools\mcpb" @anthropic-ai/mcpb
```

From the repository root:

```powershell
.\packaging\claude-mcpb\build.ps1
```

The build script writes:

```text
dist/mcpb/maya-mcp/maya-mcp.mcpb
```

The script finds `mcpb` on `PATH` first, then falls back to the user-local
install at `%USERPROFILE%\.tools\mcpb`.

## Maya Setup

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

## First Calls

After installing the extension, verify the connection with:

1. `health.check`
2. `scene.info`
3. `nodes.list`

## Examples

### Inspect a scene

Ask Claude to check whether Maya is reachable, summarize the current scene, and
list the first nodes in the scene.

Expected tools: `health.check`, `scene.info`, `nodes.list`.

### Create simple geometry

Ask Claude to create a polygon cube, name it, and report its transform and shape
information.

Expected tools: `modeling.create_polygon_primitive`, `nodes.info`.

### Capture the viewport

Ask Claude to capture the active Maya viewport as an image.

Expected tool: `viewport.capture`.

## Security Notes

- The MCP server only connects to `localhost` or `127.0.0.1`.
- The server process does not import Maya modules.
- Maya communication happens only through Maya `commandPort`.
- Raw code execution through `script.run` is disabled unless the user explicitly
  enables it in extension settings.
- Approved script execution uses `MAYA_MCP_SCRIPT_DIRS` as an allowlist.

## Privacy Policy

Maya MCP runs locally on the user's machine. The extension does not operate a
hosted service, does not collect telemetry, and does not send Maya scene data to
Maya MCP contributors.

Claude receives tool inputs and outputs as part of normal MCP use in Claude
Desktop. Users should review Claude's own privacy and data-retention policies
for how conversation and tool data are handled by Claude.

Maya MCP may read or modify local Maya scene data only when the user allows
Claude to invoke its tools. Local logs and error messages are intended for
debugging and should not include secrets or raw tracebacks.

Support and privacy contact: use GitHub Issues at
https://github.com/GimbalGoats/GG_MayaMCP/issues.
