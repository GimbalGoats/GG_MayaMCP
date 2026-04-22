---
summary: "Short architecture guide covering runtime flow, module boundaries, configuration, and the main design constraints."
read_when:
  - When changing module boundaries, server wiring, or tool layering.
  - When you need the mental model for how Maya MCP talks to Maya.
---

# Architecture Overview

This is the implementation-facing architecture summary for Maya MCP.

Use it as the first source of truth when changing server wiring, module boundaries, or the separation between MCP wrappers, tool logic, and transport.

## Core Invariants

These should remain true unless an ADR explicitly changes them:

- the MCP server process is separate from the Maya process
- the MCP server process does not import Maya modules
- Maya communication happens only through the transport layer
- transport remains localhost-only
- tools stay workflow-first and relatively thin

## Process Split

Maya MCP is intentionally split into two processes:

- the MCP server process
- the running Maya process

They communicate only through Maya's `commandPort` over `localhost`.

## Runtime Flow

The normal request path is:

1. An MCP client calls a tool on `maya_mcp.server`.
2. The registered wrapper in `src/maya_mcp/registrars/` receives the call.
3. The wrapper delegates to a function in `src/maya_mcp/tools/`.
4. The tool uses `src/maya_mcp/transport/commandport.py`.
5. The transport sends a Python or MEL payload to Maya.
6. Maya executes it and returns the result.

## Why This Split Exists

The separation is deliberate:

- the server can run in a normal Python environment
- tests can run without a live Maya session
- Maya crashes or restarts do not take down the MCP process
- the security boundary is easier to reason about

## Layer Responsibilities

| Layer | Path | Responsibility |
|---|---|---|
| Server | `src/maya_mcp/server.py` | Creates the FastMCP server and registers tools |
| Registrars | `src/maya_mcp/registrars/` | MCP-facing wrappers, descriptions, schemas, annotations |
| Tools | `src/maya_mcp/tools/` | Thin workflow functions and result shaping |
| Transport | `src/maya_mcp/transport/commandport.py` | Socket lifecycle, retries, timeouts, response parsing |
| Shared types/errors | `src/maya_mcp/types.py`, `src/maya_mcp/errors.py` | Stable typed contracts |
| Utilities | `src/maya_mcp/utils/` | Validation, coercion, script config, response guards |
| Maya panel | `src/maya_mcp/maya_panel/` | Optional UI running inside Maya |

## Change Boundaries

Use these rules when deciding where a change belongs:

- change `server.py` when server metadata, startup wiring, or the top-level server factory changes
- change `registrars/` when MCP-facing signatures, descriptions, annotations, progress wrappers, or schema-visible behavior changes
- change `tools/` when workflow behavior, result shaping, or tool-level validation changes
- change `transport/commandport.py` when socket lifecycle, retries, timeouts, response parsing, or host enforcement changes
- change `utils/` when logic is shared below the tool layer and is not specific to a single MCP wrapper

## Design Rules

### No Maya imports in the server

The server process must not import `maya.cmds` or other Maya modules.

### Thin tools

Tool modules should stay close to user-facing behavior and schemas. Socket policy, parsing, and lower-level validation belong below the tool layer.

### Localhost only

`commandPort` has no authentication, so remote-host support is intentionally out of scope.

### Workflow-first tool design

The tool surface is meant to support real workflows, not mirror every low-level Maya API call.

### Shared contract ownership

For implementation changes, the canonical companion docs are:

- `docs/spec/tools.md` for tool defaults, limits, annotations, and read/write behavior
- `docs/spec/transport.md` for connection behavior and typed transport failures
- `docs/spec/security.md` for security boundaries and trust model
- `docs/adr/0001-commandport.md` when reconsidering the transport choice itself

## Tool Families

The server currently registers 71 tools across:

- health and connection
- scene, nodes, attributes, selection
- connections, mesh, viewport, curves
- modeling, shading, skinning, animation
- scripts

See [Tool Guide](tools.md) for the practical overview.

## Configuration Surface

Core transport settings:

| Variable | Default |
|---|---:|
| `MAYA_MCP_HOST` | `localhost` |
| `MAYA_MCP_PORT` | `7001` |
| `MAYA_MCP_CONNECT_TIMEOUT` | `5.0` |
| `MAYA_MCP_COMMAND_TIMEOUT` | `30.0` |
| `MAYA_MCP_MAX_RETRIES` | `3` |

Script settings:

| Variable | Default |
|---|---:|
| `MAYA_MCP_SCRIPT_DIRS` | empty |
| `MAYA_MCP_ENABLE_RAW_EXECUTION` | `false` |
| `MAYA_MCP_SCRIPT_TIMEOUT` | `60` |

Experimental gate:

| Variable | Default | Notes |
|---|---:|---|
| `MAYA_MCP_CODE_MODE` | unset | Enables the prototype Code Mode only when set to `1` |

## Progress Support

Some longer-running tools can report progress when the client provides a progress token:

- `scene.export`
- `mesh.evaluate`
- `skin.weights.get`
- `skin.weights.set`

Progress support is registrar-level behavior. Do not move client-visible progress semantics into low-level transport code.

## Related Docs

- [Transport Specification](transport.md)
- [Security Specification](security.md)
- [Tool Guide](tools.md)
- [ADR-0001 CommandPort](../adr/0001-commandport.md)
