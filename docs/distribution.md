---
summary: "Maintainer runbook for publishing Maya MCP to registries, marketplaces, and connector directories."
read_when:
  - When preparing a Maya MCP release or updating public distribution metadata.
  - When submitting Maya MCP to the Official MCP Registry, Autodesk Marketplace, or Anthropic Connectors Directory.
---

# Distribution and Marketplace Publishing

Maya MCP uses the PyPI package and GitHub Release as the source of truth for
public versions. Keep `pyproject.toml`, `src/maya_mcp/__init__.py`,
`server.json`, and `packaging/claude-mcpb/manifest.json` on the same released
version.

## Official MCP Registry

The root `server.json` declares the PyPI-backed stdio package under
`io.github.GimbalGoats/maya-mcp`. The hidden `mcp-name` marker in `README.md`
proves package ownership after that README is published to PyPI.

For a GitHub Release, the Publish workflow:

1. publishes the Python distribution to PyPI
2. waits until PyPI exposes the matching version and ownership marker
3. authenticates to the Official MCP Registry through GitHub OIDC
4. publishes `server.json`

No registry token is required. The workflow pins and verifies the publisher
binary; update its version and SHA-256 together after reviewing a new upstream
release. Before releasing, validate locally with the same `mcp-publisher`
version:

```bash
mcp-publisher validate server.json
```

After the workflow succeeds, verify the exact record through the
[Official Registry API](https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.GimbalGoats/maya-mcp).

## Autodesk Design and Make Marketplace

The required MCP Tool Manifest lives at
`packaging/autodesk/mcp-tool-manifest.json`. It is generated from the live MCP
tool list so the 71 tool declarations cannot drift silently.

```bash
python packaging/autodesk/generate_manifest.py
python packaging/autodesk/generate_manifest.py --check
```

Follow `packaging/autodesk/README.md` to complete the Publisher Declaration and
email submission. The declaration requires publisher identity and security
attestations, so it is intentionally not automated.

## Anthropic Connectors Directory

Use the released `maya-mcp-<version>.mcpb` package. Before submission:

- run the release workflow's MCPB validation and 71-tool smoke test
- verify the bundled 512x512 icon
- provide the public [privacy policy](privacy.md) and GitHub support URL
- provide the reviewer setup and examples from the
  [Claude Desktop Extension guide](usage/claude-desktop-extension.md)

The submission form requires a responsible publisher to accept Anthropic's
directory terms, so it is intentionally not automated.

## Release Verification

After each release, confirm:

- PyPI, GitHub Release, MCPB, and Official MCP Registry versions agree
- the Official Registry record installs `maya-mcp` over stdio
- the Autodesk manifest check still passes
- claimed directory listings use the current install command, version, docs,
  privacy policy, and support URL
