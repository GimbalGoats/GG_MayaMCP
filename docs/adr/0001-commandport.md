# ADR-0001: Use Maya `commandPort` for Communication

**Status**: Accepted  
**Date**: 2025-01-30

## Context

Maya MCP needs a reliable way to communicate with a running Maya instance.

The chosen mechanism must:

1. work across Windows, macOS, and Linux
2. support interactive use against a live Maya session
3. allow request/response communication
4. keep the MCP server outside the Maya process
5. fit a localhost-only security model

## Decision

Maya MCP uses Maya's built-in `commandPort` with an INET TCP socket.

## Why This Option Won

- built into Maya, so there is no plugin deployment requirement
- works across supported desktop platforms
- supports Python and MEL execution inside Maya
- keeps the MCP server process independent from Maya
- matches the project's localhost-only security posture

## Alternatives Considered

### `mayapy` subprocess

Rejected because it does not target a live interactive Maya session well and would split state away from the running DCC process.

### Custom HTTP or REST plugin

Rejected because it adds plugin-development, deployment, threading, and maintenance cost without solving the core problem better than `commandPort`.

### Unix-domain sockets

Rejected because they are not a practical cross-platform default for Windows support.

### Shared-memory IPC

Rejected because it is significantly more complex than the command/response pattern needed here.

## Consequences

### Positive

- zero additional Maya-side plugin requirement
- easy local setup
- clear process isolation
- practical for AI-assisted interactive workflows

### Negative

- users must open `commandPort` in Maya
- transport must remain localhost-only because `commandPort` has no authentication
- large responses require careful buffering and response-guard behavior

## Security Implications

Because `commandPort` itself is not authenticated, Maya MCP adds controls at the system design level:

- localhost-only transport
- explicit tool surface
- no unrestricted code execution by default
- input validation
- typed, sanitized errors

## Example Maya Setup

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
)
```

## Related Documents

- [Architecture Overview](../spec/overview.md)
- [Transport Specification](../spec/transport.md)
- [Security Specification](../spec/security.md)
