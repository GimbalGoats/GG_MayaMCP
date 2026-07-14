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

## Command Protocol

There are two protocols. The transport reads Maya's version once per connection
and picks one; tool modules never see the difference, because `execute()` returns
the command's output either way.

| Maya version | `echoOutput` | Protocol |
|---|---|---|
| 2024 | `False` | Helper protocol (below) |
| everything else | `True` | Standard: command sent verbatim, echoed output parsed |

Anything that is not Maya 2024 — including a version Maya declines to report —
takes the standard path, which is the one every version other than 2024 has
always used and is unchanged by the 2024 work.

The version is read with a bare expression (`cmds.about(version=True)`) that
produces no stdout, so the probe is safe even on a 2024 port whose echo is
already broken.

### Standard protocol (all versions except 2024)

Commands are sent as-is. Maya echoes their output back, and the transport
normalizes that stream before tool code sees it:

- strips empty and `None` fragments
- drops known Maya startup/plugin warning lines that can arrive before output
- prefers JSON-like payloads when present
- deduplicates repeated JSON echoes
- returns the last unique JSON block when Maya printed more than one
- preserves useful non-JSON output lines when a command does not return JSON

### Maya 2024 protocol

Maya 2024 cannot echo command output at all. Its `CommandPort.py` writes the
output to the socket as `str` rather than `bytes`, so the first command that
prints anything raises inside Maya's echo writer, and the port stops responding
to every command afterwards. The port must therefore be opened with
`echoOutput=False`, which leaves only the value channel — and that channel
returns a value **only for a single bare expression**. A payload containing any
statement is executed and always answers `None`, so a command ending in
`print(json.dumps(result))` sends nothing back.

Commands also execute in the `maya.app.general.CommandPort` namespace with a
fresh locals mapping each time, so nothing assigned at top level survives to the
next command. Maya's `__main__` does persist, and a function stored there can be
reached from a single expression.

The 2024 path builds on those two facts:

1. A helper is installed into Maya's `__main__`, as one expression.
2. Every command is sent as one expression, `_mcp_exec("<base64>")`.
3. The helper executes the payload with stdout redirected, and returns a JSON
   envelope as its value: `{"v", "ok", "stdout", "error", "error_type", "traceback"}`.
4. `execute()` unwraps the envelope and returns the captured stdout.

The command is base64-encoded rather than embedded as source: the payload
survives byte-for-byte, including multi-line string literals that textual
re-indentation would silently corrupt.

Because output rides the helper's return value instead of an echoed stream, Maya
startup and plugin warnings never share the response, so the 2024 path needs no
noise filtering or echo-deduplication.

The helper is version-stamped (`HELPER_VERSION`) and installed on demand: the
transport sends the command first and only bootstraps when Maya reports the
helper missing or returns an envelope stamped with a different version. A command
against a ready Maya therefore costs one round trip, and a Maya restart or a
stale helper heals on the next command with no user action.

On this path an exception inside Maya is reported as `MayaCommandError` carrying
Maya's traceback, rather than arriving as unparseable output.

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

# Maya 2024 cannot echo command output, so the port must not try; every other
# version echoes normally. This picks the right setting automatically.
echo_output = cmds.about(version=True) != "2024"

cmds.commandPort(
    name=":7001",
    sourceType="python",
    echoOutput=echo_output,
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
