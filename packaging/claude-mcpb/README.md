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

## Release Automation

The repository `Publish` workflow builds this package on `windows-latest` for
published GitHub Releases and manual dispatches. It verifies that the MCPB
manifest version matches `pyproject.toml` and the release tag, validates the
staged manifest, inspects the bundle, unpacks it for a stdio smoke test, and
uploads `maya-mcp-<version>.mcpb`.

On published GitHub Releases, that `.mcpb` file is attached to the release.
Manual dispatches build and upload the artifact without publishing to PyPI
unless `publish_pypi` is enabled.

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

1. `health_check`
2. `scene_info`
3. `nodes_list`

The Claude Desktop bundle uses underscore tool names because Claude Desktop
rejects dots in connector tool names. The normal `maya-mcp` server still uses
dotted names.

## Examples

### Inspect a scene

Ask Claude to check whether Maya is reachable, summarize the current scene, and
list the first nodes in the scene.

Expected Claude Desktop bundle tools: `health_check`, `scene_info`,
`nodes_list`.

### Create simple geometry

Ask Claude to create a polygon cube, name it, and report its transform and shape
information.

Expected Claude Desktop bundle tools: `modeling_create_polygon_primitive`,
`nodes_info`.

### Capture the viewport

Ask Claude to capture the active Maya viewport as an image.

Expected Claude Desktop bundle tool: `viewport_capture`.

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
