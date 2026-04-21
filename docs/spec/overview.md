---
summary: "Architecture overview covering runtime flow, module responsibilities, constraints, and configuration surface."
read_when:
  - When changing architecture, module boundaries, tool layering, shared utilities, or server registration.
  - When orienting to how MCP clients, the server, transport, Maya, and the Maya panel interact.
---

# Architecture Overview

This document describes the runtime architecture of Maya MCP and the responsibilities of the main modules.

## System Context

Maya MCP runs as a separate Python process from Autodesk Maya.

The communication path is:

1. An MCP client talks to `maya_mcp.server` over MCP transport, usually stdio.
2. The server dispatches a typed tool function from `src/maya_mcp/tools/`.
3. The tool delegates to the transport layer in `src/maya_mcp/transport/commandport.py`.
4. The transport layer sends Python or MEL commands to Maya over `localhost`.
5. Maya executes the command inside its own process and returns the result.

## Architectural Layers

### MCP server layer

`src/maya_mcp/server.py`

- Creates the `FastMCP` server instance
- Registers all 71 tools
- Defines tool descriptions and annotations
- Exposes the `main()` CLI entrypoint
- Supports packaged CLI launch, module launch, and direct script launch for
  local source checkouts

### Tool layer

`src/maya_mcp/tools/`

- Implements the MCP-facing tool functions
- Validates and shapes tool input and output
- Keeps tool logic thin
- Delegates transport work to shared lower layers

Major tool namespaces:

- `health.*`
- `maya.*`
- `scene.*`
- `nodes.*`
- `attributes.*`
- `selection.*`
- `connections.*`
- `mesh.*`
- `viewport.*`
- `modeling.*`
- `shading.*`
- `skin.*`
- `animation.*`
- `curve.*`
- `script.*`

### Shared types and errors

`src/maya_mcp/types.py` and `src/maya_mcp/errors.py`

- Shared enums and result types
- Typed exception hierarchy
- Stable error payloads for callers

### Transport layer

`src/maya_mcp/transport/commandport.py`

- Owns socket lifecycle
- Enforces localhost-only communication
- Handles connect and command timeouts
- Retries connection attempts with backoff
- Translates socket and execution failures into typed errors

### Utilities

`src/maya_mcp/utils/`

- Input validation helpers
- Response parsing and coercion
- Response size guards
- Script-execution configuration and validation

### Maya panel

`src/maya_mcp/maya_panel/`

- Runs inside Maya, not in the MCP server process
- Provides a UI for opening and closing `commandPort`
- Stores local panel preferences such as port and auto-start

### Code Mode prototype

`src/maya_mcp/code_mode.py`

- Defines an experimental Code Mode gate for future server profiles
- Enables only when `MAYA_MCP_CODE_MODE=1`
- Keeps Code Mode factory selection separate from default server registration
- Applies fixed prototype sandbox limits before any code execution path uses it
- Does not change the default MCP server or make arbitrary code execution default

## Key Design Constraints

### Transport isolation

The MCP server process must not import `maya.cmds` or other Maya modules.

Why:

- The server must be able to run in a standard Python environment
- Maya crashes must not take down the server process
- Tool tests must run without a live Maya session

### Localhost-only communication

Maya `commandPort` has no built-in authentication, so the transport is intentionally restricted to `localhost` and `127.0.0.1`.

### Thin tools

Tool modules should stay close to MCP concerns:

- parameter handling
- result shaping
- annotations
- clear tool-level semantics

Transport, parsing, and validation should live below the tool layer.

### Recovery-oriented behavior

Maya is an external process and may be unavailable, restarted, or mid-crash-recovery. The server is designed to detect this state, surface typed errors, and retry connection when appropriate.

## Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `maya_mcp.server` | FastMCP entrypoint and tool registration |
| `maya_mcp.transport.commandport` | Socket transport to Maya |
| `maya_mcp.errors` | Typed error hierarchy |
| `maya_mcp.types` | Shared types and connection-state models |
| `maya_mcp.tools.*` | MCP tool implementations |
| `maya_mcp.utils.*` | Validation, parsing, coercion, response guards |
| `maya_mcp.maya_panel.*` | In-Maya UI for commandPort control |

## Request Flow

Typical successful call:

1. Client invokes a tool such as `scene.info`.
2. `maya_mcp.server` routes the call to the registered tool function.
3. The tool asks the transport client for execution.
4. The transport connects to Maya if needed.
5. Maya executes the request through `commandPort`.
6. The transport parses the response and returns typed data.
7. The tool returns the MCP result to the client.

Typical unavailable-Maya case:

1. A tool requests transport execution.
2. The transport cannot connect to `localhost:7001`.
3. Retry and backoff policy is applied.
4. A `MayaUnavailableError` is raised with context.
5. The next call can attempt reconnection again.

## Configuration Surface

Core transport settings are environment-driven:

| Variable | Default | Purpose |
|----------|---------|---------|
| `MAYA_MCP_HOST` | `localhost` | Maya host |
| `MAYA_MCP_PORT` | `7001` | Maya commandPort port |
| `MAYA_MCP_CONNECT_TIMEOUT` | `5.0` | Connect timeout in seconds |
| `MAYA_MCP_COMMAND_TIMEOUT` | `30.0` | Command timeout in seconds |
| `MAYA_MCP_MAX_RETRIES` | `3` | Max connection retries |

Script tools add:

| Variable | Default | Purpose |
|----------|---------|---------|
| `MAYA_MCP_SCRIPT_DIRS` | empty | Allowlisted script directories |
| `MAYA_MCP_ENABLE_RAW_EXECUTION` | `false` | Enables `script.run` |
| `MAYA_MCP_SCRIPT_TIMEOUT` | `60` | Script execution timeout |

Code Mode prototype adds:

| Variable | Default | Purpose |
|----------|---------|---------|
| `MAYA_MCP_CODE_MODE` | unset | Enables experimental Code Mode only when exactly `1` |

Current Code Mode sandbox limits are fixed in code:

| Limit | Value |
|-------|-------|
| Language | Python only |
| Code payload | 16 KB |
| Execution timeout | 10 seconds |
| Text output | 50 KB |

## Related Documents

- [Transport Specification](transport.md)
- [Security Specification](security.md)
- [Tool Specification](tools.md)
- [ADR-0001 CommandPort](../adr/0001-commandport.md)
