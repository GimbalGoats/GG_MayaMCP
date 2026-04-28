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

## Build The Package

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
user-local install at `$env:USERPROFILE\.tools\mcpb`.

The generated package path is:

```text
dist/mcpb/maya-mcp/maya-mcp.mcpb
```

To inspect the package:

```powershell
& "$env:USERPROFILE\.tools\mcpb\node_modules\.bin\mcpb.cmd" info dist\mcpb\maya-mcp\maya-mcp.mcpb
```

## Release Automation

The `Publish` GitHub Actions workflow builds the MCPB package on
`windows-latest` for every published GitHub Release and manual dispatch. The
workflow installs `@anthropic-ai/mcpb`, runs the same
`packaging/claude-mcpb/build.ps1` script, validates the manifest, inspects the
bundle, unpacks the generated archive for a stdio server smoke test, and uploads
a `maya-mcp-<version>.mcpb` artifact.

For release events, the workflow also attaches that `.mcpb` file to the GitHub
Release alongside the PyPI publishing path.

## Install In Claude Desktop

Install the generated `.mcpb` file by using one of Claude Desktop's extension
flows:

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

## Verify

Open Maya, enable `commandPort`, then ask Claude Desktop to call:

1. `health_check`
2. `scene_info`
3. `nodes_list`

For a write-path smoke test, use a disposable scene and ask Claude to create a
polygon cube with `modeling_create_polygon_primitive`.

If Claude Desktop still shows the server as failed after reinstalling a rebuilt
`.mcpb`, fully quit and reopen Claude Desktop, then toggle Maya MCP off and on
under Settings -> Developer -> Local MCP servers. On the Windows Store build,
the useful server log is usually:

```text
C:\Users\<you>\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\logs\mcp-server-Maya MCP.log
```

## Submission Notes

For Anthropic review, prepare:

- the generated `.mcpb` package
- public setup docs
- a public privacy policy
- a support URL
- a 512x512 PNG logo
- three or more documented examples that exercise real tools
- a test Maya scene or clear reviewer setup steps

Use the Desktop extension submission form from Anthropic's Connectors Directory
submission page.

## Related Docs

- [Getting Started](getting-started.md)
- [Client Setup](client-setup.md)
- [Privacy Policy](../privacy.md)
- [Security Specification](../spec/security.md)
