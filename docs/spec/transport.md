---
summary: "Compact transport reference for Maya commandPort lifecycle, retries, timeouts, and typed error behavior."
read_when:
  - When changing commandPort behavior, host validation, retries, or timeout handling.
  - When debugging why the server can or cannot reach Maya.
---

# Transport Specification

This is the implementation-facing contract for the commandPort transport.

If a change affects connection lifecycle, host validation, timeout semantics, retry behavior, or response parsing, review this page before changing code.

## Core Invariants

These should remain true unless an ADR explicitly changes them:

- the transport is the only server-side code allowed to communicate with Maya
- the transport accepts only `localhost` and `127.0.0.1`
- transport policy is centralized here, not reimplemented in tool modules
- connection failures become typed Maya MCP errors

## Scope

The transport layer is the only part of Maya MCP that talks to Maya directly.

Its implementation lives in `src/maya_mcp/transport/commandport.py`.

## Purpose

The transport is responsible for:

- connecting to Maya's `commandPort`
- enforcing localhost-only host validation
- sending commands and receiving responses
- retrying connection attempts with backoff
- translating socket failures into typed Maya MCP errors

## Connection Defaults

| Setting | Default |
|---|---:|
| host | `localhost` |
| port | `7001` |
| connect timeout | `5.0` seconds |
| command timeout | `30.0` seconds |
| max retries | `3` |
| retry base delay | `0.5` seconds |

Only `localhost` and `127.0.0.1` are valid hosts.

The defaults above are code-level behavior and should stay aligned with `ConnectionConfig` and client initialization.

## Lifecycle

The transport tracks three states:

- `OFFLINE`
- `RECONNECTING`
- `OK`

Typical flow:

1. A tool needs Maya.
2. The transport connects if no healthy socket exists.
3. On success, state becomes `OK`.
4. If Maya is unavailable or the socket breaks, state drops to `OFFLINE`.
5. The next request can trigger reconnect attempts.

## Retry Behavior

Connection retries use exponential backoff:

| Attempt | Delay |
|---|---:|
| 1 | `0.5s` |
| 2 | `1.0s` |
| 3 | `2.0s` |

Retries are used for connection failures, not for tool-level validation or Maya-side command errors.

Send-phase reconnect-and-retry is allowed only when the command was not successfully delivered. Once send has completed, the transport must not blindly replay the command.

## Timeout Behavior

### Connect timeout

Used while opening the socket to Maya.

If it expires, Maya MCP treats Maya as unavailable.

### Command timeout

Used after the command is sent and the server is waiting for Maya to respond.

If it expires, Maya MCP raises `MayaTimeoutError`.

## Response Handling

Maya `commandPort` can echo output, include null bytes, or return duplicate JSON fragments when `echoOutput=True`.

The transport normalizes that noise before tool code sees the result:

- strips empty and `None` fragments
- drops known Maya startup/plugin warning lines that can arrive on the commandPort stream before command output
- prefers JSON-like payloads when present
- deduplicates repeated JSON echoes
- returns the last unique JSON block when Maya printed more than one
- preserves useful non-JSON output lines after cleanup when a command does not return JSON

That keeps parsing logic centralized instead of spreading it across tool modules.

Tool modules should not implement their own socket read loops or commandPort response cleanup.

## Typed Errors

Low-level failures are translated into the shared error types:

| Situation | Error |
|---|---|
| Maya cannot be reached | `MayaUnavailableError` |
| Maya stops responding before timeout | `MayaTimeoutError` |
| Invalid transport configuration | `ValidationError` |

Maya-side command failures are surfaced by higher layers as `MayaCommandError`.

Client-facing error payloads should stay structured enough for recovery logic and must not include secrets or raw tracebacks.

## Why `commandPort`

Maya MCP uses `commandPort` because it:

- ships with Maya
- works across supported desktop platforms
- executes inside the live Maya process
- supports Python and MEL

The decision is recorded in [ADR-0001 CommandPort](../adr/0001-commandport.md).

## Recommended Maya-Side Setup

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

## Operational Notes

- The transport serializes commandPort access per client. Concurrent server handlers can call the same client, but socket send/receive work still runs one request at a time.
- The module-level shared transport client is initialized under a singleton lock so concurrent first access still creates only one process-wide default client.
- `connect`, `disconnect`, and `reconfigure` share the same per-client serialization, so lifecycle changes cannot mutate socket state during an active command.
- The per-client lock does not coordinate separate `CommandPortClient` instances. Live tests and MCP server flows should route tool calls through the shared transport client instead of keeping multiple commandPort sockets open to the same Maya session.
- Restart the MCP server after local code changes when validating against a live Maya session.
- Restart Maya if `commandPort` state becomes confused or stale.

## When To Update This Doc

Update this page when changing:

- host validation rules
- retry or reconnect rules
- timeout defaults or semantics
- command send/receive behavior
- response parsing behavior
- typed transport error mapping

## Related Docs

- [Architecture Overview](overview.md)
- [Security Specification](security.md)
- [ADR-0001 CommandPort](../adr/0001-commandport.md)
