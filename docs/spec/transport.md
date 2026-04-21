# Transport Layer Specification

This document defines the transport layer that connects Maya MCP to Autodesk Maya through `commandPort`.

## Purpose

The transport layer is responsible for all communication between the MCP server process and Maya.

It handles:

- socket connection management
- localhost-only host validation
- command submission and response retrieval
- timeout enforcement
- connection retry with exponential backoff
- translation of low-level failures into typed Maya MCP errors

## Why `commandPort`

Maya MCP uses Maya's built-in `commandPort` because it:

- is available without extra plugins
- works across Windows, macOS, and Linux
- executes inside Maya's process
- supports both Python and MEL

This decision is recorded in [ADR-0001](../adr/0001-commandport.md).

## Opening `commandPort` in Maya

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

Maya MCP uses INET sockets such as `:7001`, not Unix-domain sockets.

## Main Entry Point

The main transport class is `maya_mcp.transport.commandport.CommandPortClient`.

Its responsibilities are:

- maintain connection state
- connect and disconnect from Maya
- execute commands
- enforce retry and timeout policy
- expose health and status information

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| host | `localhost` | Maya host. Only `localhost` and `127.0.0.1` are allowed. |
| port | `7001` | Maya commandPort port |
| connect timeout | `5.0` seconds | Maximum wait while connecting |
| command timeout | `30.0` seconds | Maximum wait for command completion |
| max retries | `3` | Number of connection attempts before failing |
| retry base delay | `0.5` seconds | Base for exponential backoff |

## Connection Lifecycle

The transport tracks connection state through `ConnectionStatus`.

Expected states:

- `OFFLINE`: not connected
- `RECONNECTING`: currently retrying connection
- `OK`: connected and responsive

Typical lifecycle:

1. A tool requests a command.
2. The client connects if no healthy socket is available.
3. If connect succeeds, state becomes `OK`.
4. If the socket fails, state drops to `OFFLINE`.
5. The next command may trigger reconnect attempts and `RECONNECTING`.

## Timeout Behavior

### Connect timeout

Applied during socket connection establishment.

If exceeded, the transport treats Maya as unavailable.

### Command timeout

Applied while waiting for Maya to return a response after command submission.

If exceeded, the transport raises `MayaTimeoutError`.

## Retry Policy

Connection retries use exponential backoff.

With the default base delay of `0.5`, the delays are:

| Attempt | Delay |
|---------|-------|
| 1 | `0.5s` |
| 2 | `1.0s` |
| 3 | `2.0s` |

Retries are appropriate for transient connection failures such as:

- connection refused
- connection reset
- temporary network/socket errors on localhost

Retries are not used for command-level execution failures such as invalid Maya commands or structured command errors returned by Maya.

## Error Translation

The transport should translate low-level failures into typed errors from `maya_mcp.errors`.

| Situation | Error |
|-----------|-------|
| Maya cannot be reached | `MayaUnavailableError` |
| Maya command fails | `MayaCommandError` |
| Maya does not respond before timeout | `MayaTimeoutError` |
| Input/config validation fails | `ValidationError` |

These errors include structured `details` so clients can react programmatically.

## Protocol Notes

- Commands are encoded as UTF-8 strings.
- Responses are decoded from UTF-8.
- The transport owns response parsing boundaries before data is returned to tool modules.
- The tool layer should not implement its own socket policy.

## Threading

The current transport is not designed as a general-purpose concurrent client. Tool callers should assume single-client, request-at-a-time behavior unless the transport is explicitly redesigned.

## Security Constraints

The transport must enforce these constraints:

- no remote host support
- no secrets in error payloads
- no server-side Maya imports outside the command payload sent to Maya

For the wider threat model, see [Security Specification](security.md).
