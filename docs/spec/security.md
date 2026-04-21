---
summary: "Security model for localhost-only Maya control, script execution trust levels, validation, and error sanitization."
read_when:
  - When changing security-sensitive behavior, validation, path handling, script execution, logging, or error payloads.
  - When assessing whether a new tool or workflow preserves localhost-only and explicit-risk boundaries.
---

# Security Specification

This document defines the security model for Maya MCP.

## Security Posture

Maya MCP is a local-development MCP server intended to communicate with a Maya instance on the same machine.

The main security assumptions are:

- the MCP server runs locally
- Maya runs locally
- communication stays on `localhost`
- exposed tools are explicit and intentionally scoped

This is not a remote multi-tenant service.

## Assets to Protect

| Asset | Goal |
|-------|------|
| Maya scene data | Prevent unintended reads or destructive writes |
| Host system access | Prevent arbitrary code execution by default |
| User credentials and secrets | Never expose them through logs or error messages |
| Local filesystem | Avoid unintended file access and unsafe path handling |

## Threat Model

Relevant threats:

- remote access if `commandPort` were exposed beyond localhost
- malicious or careless MCP clients calling powerful tools
- parameter injection through unsafe string inputs
- information disclosure through raw errors, file paths, or tracebacks

Out of scope:

- compromise of Maya itself
- compromise of the local operating system
- security guarantees for user-authored scripts intentionally executed in Maya

## Core Controls

### Localhost only

The transport only supports `localhost` and `127.0.0.1`.

Why:

- Maya `commandPort` does not provide authentication
- remote exposure would turn local tooling into a network-exposed execution path

### No arbitrary code execution by default

Most tools expose predefined workflows only.

The one explicit raw-execution path is `script.run`, and it is disabled unless:

```text
MAYA_MCP_ENABLE_RAW_EXECUTION=true
```

`script.execute` is also constrained:

- file must be inside an allowlisted directory
- file type must be valid
- file size is capped
- execution timeout is bounded

### Input validation

Tool inputs must be validated before they reach Maya.

This includes:

- node names
- attribute names
- file paths
- namespace values
- script paths
- raw code size limits
- list and pagination limits

Validation should prefer allowlists and explicit bounds over permissive free-form input.

### Error sanitization

Client-facing errors must not leak:

- secrets
- raw stack traces
- oversized command payloads
- sensitive local paths when avoidable

Typed errors should include structured context, but only the context needed to explain and recover from the failure.

## Tool-Level Risk Model

Maya MCP separates read and write behavior into different tools whenever practical.

Examples:

- `attributes.get` vs `attributes.set`
- `selection.get` vs `selection.set`
- `skin.weights.get` vs `skin.weights.set`

This supports clearer annotations and safer client behavior.

## Script Tool Trust Model

Script tooling uses a three-tier model:

| Tier | Tool | Default State | Purpose |
|------|------|---------------|---------|
| 1 | `script.list` | enabled | Discover scripts from configured directories |
| 2 | `script.execute` | enabled when directories are configured | Execute approved `.py` files from allowlisted directories |
| 3 | `script.run` | disabled | Execute raw Python or MEL only after explicit opt-in |

Related configuration:

| Variable | Meaning |
|----------|---------|
| `MAYA_MCP_SCRIPT_DIRS` | Semicolon-separated allowlist of absolute directories |
| `MAYA_MCP_ENABLE_RAW_EXECUTION` | Enables `script.run` when set to `true` or `1` |
| `MAYA_MCP_SCRIPT_TIMEOUT` | Timeout for script execution |

## Maya `commandPort` Considerations

`commandPort` itself has limited security features. Maya MCP relies primarily on locality and explicit tool design rather than on strong transport authentication.

Recommended Maya-side setup during development:

```python
import maya.cmds as cmds

cmds.commandPort(
    name=":7001",
    sourceType="python",
    echoOutput=True,
    securityWarning=True,
)
```

`securityWarning=True` is useful for visibility during local development.

## Alignment With MCP Security Guidance

MCP guidance for remote servers often recommends OAuth and stronger session controls. Maya MCP does not implement those patterns because:

- it is localhost-only
- it does not operate as a remote shared service
- it does not broker external credentials

The main security boundary is the local machine, not an internet-facing deployment edge.

## Developer Requirements

When adding or changing tools:

- do not add unrestricted execution paths casually
- validate every free-form string input
- keep read-only and mutating tools separate where possible
- preserve localhost-only transport behavior
- do not suppress type or validation failures in ways that hide unsafe states

## Release Checklist

Before shipping security-sensitive doc or tool changes, confirm:

- localhost-only behavior is still enforced
- `script.run` remains explicit opt-in
- path validation still blocks traversal and unsafe inputs
- errors do not leak secrets or tracebacks
- tests cover malformed and adversarial inputs for the changed area
