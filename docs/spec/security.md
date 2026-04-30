---
summary: "Security model for Maya MCP covering localhost-only transport, script execution trust levels, and error-sanitization rules."
read_when:
  - When changing security-sensitive behavior, path validation, or script execution.
  - When deciding whether a new tool keeps the same risk boundaries.
---

# Security Specification

This is the implementation-facing security contract for Maya MCP.

Use it when deciding whether a new tool, input, or workflow preserves the current trust boundaries.

## Core Invariants

These should remain true unless an ADR explicitly changes them:

- transport is localhost-only
- the server process does not gain direct Maya imports
- arbitrary code execution stays opt-in, not default
- free-form inputs are validated before they reach Maya
- client-facing errors stay sanitized

## Security Posture

Maya MCP is a local-development server, not a remote multi-tenant service.

Its security model is built around a simple idea: keep the server local, keep the tool surface explicit, and make higher-risk execution paths opt-in.

## Main Assumptions

- Maya runs on the same machine as the MCP server
- communication stays on `localhost`
- clients are trusted enough to use local tools, but not trusted enough for unrestricted execution by default

## Core Rules

### Localhost only

Maya `commandPort` has no built-in authentication. Because of that, Maya MCP accepts only `localhost` and `127.0.0.1`.

Remote-host support is intentionally out of scope.

### No arbitrary code execution by default

Most tools expose specific workflows.

The raw execution path, `script.run`, is disabled unless:

```text
MAYA_MCP_ENABLE_RAW_EXECUTION=true
```

### Validate before sending anything to Maya

Inputs should be checked before they become Maya commands.

Common validation areas:

- node and attribute names
- file paths
- namespaces
- list sizes and pagination values
- raw code size
- script path allowlists

Existing-node references may use Maya DAG path separators such as
`|group1|mesh1`. Those separators are validated as path structure; malformed
paths and shell/control characters remain blocked.

Validation should happen as early as practical, but schema-visible tool semantics should remain easy to understand from the MCP layer.

### Sanitize errors

Client-facing errors should be useful, but they should not leak:

- secrets
- raw stack traces
- oversized command payloads
- avoidable local-path detail

## Script Trust Model

Script tooling is intentionally split into three levels:

| Tier | Tool | Default state | Purpose |
|---|---|---|---|
| 1 | `script.list` | enabled | Discover approved scripts |
| 2 | `script.execute` | enabled when directories are configured | Run `.py` files from allowlisted directories |
| 3 | `script.run` | disabled | Run raw Python or MEL only after explicit opt-in |

Relevant environment variables:

| Variable | Meaning |
|---|---|
| `MAYA_MCP_SCRIPT_DIRS` | Semicolon-separated absolute allowlist for script discovery and execution |
| `MAYA_MCP_ENABLE_RAW_EXECUTION` | Enables `script.run` when set to `true` or `1` |
| `MAYA_MCP_SCRIPT_TIMEOUT` | Default timeout for script tools |

Current implementation limits:

- approved script file size cap: 1 MB
- raw code size cap: 100 KB

If these limits change, update both this page and `docs/spec/tools.md`.

## Tool Risk Model

The tool surface is organized so clients can make safer decisions:

- read-only and write actions are separate where practical
- mutating tools carry different MCP annotations than inspection tools
- destructive or hard-to-recover operations are limited to a smaller set of tools

Examples:

- `attributes.get` vs `attributes.set`
- `selection.get` vs `selection.set`
- `skin.weights.get` vs `skin.weights.set`

This separation is part of the user and agent safety model, not only an API style choice.

## Human-In-The-Loop Expectation

The MCP specification and current VS Code guidance both assume users should be able to review and deny non-read-only tool invocations.

That matches Maya MCP's annotation strategy:

- read-only tools are marked for easier low-risk use
- mutating tools stay explicit
- destructive actions are easy to identify

Do not assume annotations alone are a sufficient security boundary. They are guidance metadata, not enforcement.

## Developer Checklist

When adding or changing tools:

- keep localhost-only behavior intact
- do not add unrestricted execution casually
- validate all free-form strings
- preserve read/write separation where practical
- update docs when defaults, limits, or schemas change

## When To Update This Doc

Update this page when changing:

- localhost-only enforcement
- script execution trust levels
- path validation or name validation rules
- raw execution enablement behavior
- error sanitization expectations
- risk classification assumptions for tools

## Release Checklist

Before shipping security-sensitive changes, confirm:

- remote hosts are still rejected
- `script.run` still requires explicit opt-in
- path validation still blocks unsafe traversal
- client-facing errors do not leak secrets or tracebacks
- tests cover malformed or adversarial inputs in the changed area

## Related Docs

- [Tool Guide](tools.md)
- [Transport Specification](transport.md)
- [ADR-0001 CommandPort](../adr/0001-commandport.md)
