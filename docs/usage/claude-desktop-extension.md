---
summary: "Build, install, and submit the Maya MCP Claude Desktop MCPB extension."
read_when:
  - When packaging Maya MCP as a Claude Desktop extension.
  - When preparing an Anthropic Connectors Directory submission for local MCPB distribution.
---

# Claude Desktop Extension

Maya MCP can be packaged as a Claude Desktop extension using Anthropic's MCPB
format.

This is the recommended Claude distribution path for Maya MCP because Maya runs
on the user's workstation and the server communicates only with Maya's local
`commandPort`.

## Quick Start

1. Download `maya-mcp-<version>.mcpb` from the latest GitHub Release.
2. Install it in Claude Desktop by double-clicking the `.mcpb` file, dragging
   it into Claude Desktop, or using Settings -> Extensions -> Advanced settings
   -> Install Extension.
3. Leave the Maya commandPort setting at `7001` unless your Maya setup uses a
   different port.
4. Open Maya and enable `commandPort`.
5. Ask Claude Desktop to call `health_check`, then `scene_info`, then
   `nodes_list`.

## What This Package Does

The MCPB package:

- runs the existing `maya-mcp` stdio server
- keeps Maya communication on `localhost`
- exposes the same MCP tools as normal `maya-mcp`
- advertises Claude Desktop-safe tool names with underscores, such as
  `health_check`, because Claude Desktop rejects dots in connector tool names
- lets Claude Desktop collect local settings such as the Maya commandPort
- keeps `script.run` disabled unless the user explicitly enables it

The normal MCP server behavior does not change. Existing clients can still run
`maya-mcp`, `py -m maya_mcp.server`, or `fastmcp run`.

## Requirements

You need:

- Claude Desktop with local extensions enabled
- Autodesk Maya running on the same machine
- Maya `commandPort` open on the configured local port, usually `7001`
- the `.mcpb` package from a GitHub Release, or Node/npm and the MCPB CLI when
  building from source

## Install From A Release

Published GitHub Releases attach the package as:

```text
maya-mcp-<version>.mcpb
```

Install it with any Claude Desktop extension flow:

- double-click the `.mcpb` file
- drag the `.mcpb` file into Claude Desktop
- use Settings -> Extensions -> Advanced settings -> Install Extension

During installation, configure:

| Setting | Default | Notes |
|---|---:|---|
| Maya commandPort | `7001` | Must match the open Maya commandPort |
| Connect timeout | `5` | Seconds to wait while connecting |
| Command timeout | `30` | Seconds to wait for Maya command responses |
| Approved script directories | empty | Optional semicolon-separated absolute paths |
| Enable raw `script.run` | disabled | Leave disabled unless raw execution is required |

Claude Desktop installs the extension before it enables the MCP server. If the
required settings above are not saved, Developer settings may show Maya MCP as
installed but failed or disabled.

## Enable Maya CommandPort

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

The port number must match the Claude Desktop extension setting.

## Verify In Claude Desktop

After Maya is running and `commandPort` is open, ask Claude Desktop to call:

1. `health_check`
2. `scene_info`
3. `nodes_list`

For a write-path smoke test, use a disposable scene and ask Claude to create a
polygon cube with `modeling_create_polygon_primitive`.

## Example Prompts

Inspect the open scene:

```text
Check whether Maya is reachable, summarize the current scene, and list the first
20 nodes.
```

Create simple geometry:

```text
Create a polygon cube, name it mcp_test_cube, assign a simple material, and
report its transform and shape information.
```

Capture the viewport:

```text
Capture the active Maya viewport and tell me where the image was written.
```

## FAQ

### Does this work in Claude web?

No. Maya MCP needs Claude Desktop because the MCP server and Maya both run on
your local workstation.

### Does Claude edit my Maya files directly?

Claude works through the open Maya session. Changes affect the current scene and
are written to disk only when a save/export tool is used or when you save in
Maya.

### Do I need to enable raw script execution?

No. Leave raw `script.run` disabled unless you explicitly need arbitrary Python
or MEL execution. Most workflows use the typed Maya MCP tools.

### Why are Claude Desktop tool names different?

Claude Desktop rejects dots in connector tool names, so the MCPB package
advertises underscore names such as `scene_info`. Other MCP clients can use the
normal dotted names such as `scene.info`.

## Build From Source

Install the MCPB CLI.

User-local install, recommended when you do not want to modify global npm
packages:

```powershell
npm install --prefix "$env:USERPROFILE\.tools\mcpb" @anthropic-ai/mcpb
```

Global install, if you prefer `mcpb` to be on `PATH`:

```bash
npm install -g @anthropic-ai/mcpb
```

From the repository root on Windows:

```powershell
.\packaging\claude-mcpb\build.ps1
```

The script stages a clean extension tree under `dist/mcpb/maya-mcp` and runs
`mcpb pack` there. It first looks for `mcpb` on `PATH`, then falls back to the
user-local install at `$env:USERPROFILE\.tools\mcpb`. The staged extension
includes the connector logo from `packaging/claude-mcpb/icon.png`.

The generated package path is:

```text
dist/mcpb/maya-mcp/maya-mcp.mcpb
```

To inspect the package:

```powershell
& "$env:USERPROFILE\.tools\mcpb\node_modules\.bin\mcpb.cmd" info dist\mcpb\maya-mcp\maya-mcp.mcpb
```

To smoke-test the unpacked package:

```powershell
& "$env:USERPROFILE\.tools\mcpb\node_modules\.bin\mcpb.cmd" unpack dist\mcpb\maya-mcp\maya-mcp.mcpb dist\mcpb-smoke
py packaging\claude-mcpb\smoke_test.py dist\mcpb-smoke --expected-tools 71
```

## Release Automation

The `Publish` GitHub Actions workflow builds the MCPB package on
`windows-latest` for every published GitHub Release and manual dispatch. The
workflow installs `@anthropic-ai/mcpb`, verifies that `pyproject.toml`, the MCPB
manifest, and the release tag version agree, runs the same
`packaging/claude-mcpb/build.ps1` script, validates the staged manifest,
inspects the bundle, unpacks the generated archive for a stdio server smoke
test, and uploads a `maya-mcp-<version>.mcpb` artifact.

For release events, the workflow also attaches that `.mcpb` file to the GitHub
Release alongside the PyPI publishing path. Manual dispatch builds and uploads
the MCPB artifact without publishing to PyPI unless the `publish_pypi` input is
explicitly enabled.

## Troubleshooting

If Claude Desktop still shows the server as failed after reinstalling a rebuilt
`.mcpb`, fully quit and reopen Claude Desktop, then toggle Maya MCP off and on
under Settings -> Developer -> Local MCP servers.

If `health_check` fails:

- confirm Maya is running on the same machine
- confirm Maya `commandPort` is open on the configured port
- confirm the extension setting uses the same port
- restart Claude Desktop after reinstalling or changing extension settings
- restart Maya if the commandPort state becomes stale

To find the local MCP server log on Windows, check both the regular Claude
Desktop profile and the Microsoft Store package profile:

```powershell
$logName = "mcp-server-Maya MCP.log"
$regularLog = Join-Path $env:APPDATA "Claude\logs\$logName"

if (Test-Path $regularLog) {
    $regularLog
}

Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA "Packages") -Directory -Filter "Claude_*" |
    ForEach-Object { Join-Path $_.FullName "LocalCache\Roaming\Claude\logs\$logName" } |
    Where-Object { Test-Path $_ }
```

Common path patterns are:

```text
%APPDATA%\Claude\logs\mcp-server-Maya MCP.log
%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Roaming\Claude\logs\mcp-server-Maya MCP.log
```

## Submission Notes

For Anthropic review, prepare:

- the generated `.mcpb` package
- public setup docs
- a public privacy policy
- a support URL
- the bundled 512x512 PNG logo at `packaging/claude-mcpb/icon.png`
- three or more documented examples that exercise real tools
- a test Maya scene or clear reviewer setup steps

Use the Desktop extension submission form from Anthropic's Connectors Directory
submission page.

## Related Docs

- [Getting Started](getting-started.md)
- [Client Setup](client-setup.md)
- [Privacy Policy](../privacy.md)
- [Security Specification](../spec/security.md)
