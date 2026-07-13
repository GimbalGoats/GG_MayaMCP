# Autodesk Design and Make Marketplace Submission

This directory contains the MCP Tool Manifest required by Autodesk's
[MCP publisher guide](https://aps.autodesk.com/marketplace/mcp-publisher-guide).

## Validate the manifest

The checked-in manifest is generated from Maya MCP's public `tools/list`
metadata. Regenerate it after adding, removing, renaming, or redescribing a
tool:

```bash
python packaging/autodesk/generate_manifest.py
python packaging/autodesk/generate_manifest.py --check
```

The manifest declares:

- all 71 typed tools with plain-language descriptions
- no MCP resources or prompts
- no external endpoints; Maya communication uses local loopback only
- Autodesk Maya `commandPort` and `maya.cmds` usage
- no built-in AI or LLM provider

## Complete the manual submission

1. Run the full test suite and the manifest check.
2. Review `SECURITY.md`, `docs/spec/security.md`, and `docs/privacy.md` against
   the current server behavior.
3. Complete Autodesk's Publisher Declaration Form. This requires publisher
   identity and security attestations and must be completed by the publisher.
4. Email `mcp-tool-manifest.json` and the completed declaration to
   `appsubmissions@autodesk.com`.

Suggested listing details:

- name: `Maya MCP`
- category: `MCP / AI integrations`
- website: `https://gimbalgoats.github.io/GG_MayaMCP/`
- source: `https://github.com/GimbalGoats/GG_MayaMCP`
- support: `https://github.com/GimbalGoats/GG_MayaMCP/issues`
- privacy: `https://gimbalgoats.github.io/GG_MayaMCP/privacy/`

The manifest uses app model `A`, matching Autodesk's current MCP manifest
template for a stdio server. Confirm that classification while completing the
Publisher Declaration in case Autodesk changes its submission model.
