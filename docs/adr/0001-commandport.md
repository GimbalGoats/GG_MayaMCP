# ADR-0001: Use Maya commandPort for Communication

**Status**: Accepted  
**Date**: 2025-01-30  
**Decision Makers**: Maya MCP Core Team

## Context

Maya MCP needs to communicate with a running Maya instance to execute commands and retrieve results. We need to choose a communication mechanism that is:

1. Cross-platform (Windows, macOS, Linux)
2. Reliable and well-documented
3. Supports bidirectional communication
4. Works with Maya's main thread for UI operations
5. Secure enough for localhost development use

## Decision

We will use Maya's built-in `commandPort` with INET (TCP) sockets for communication between the MCP server and Maya.

## Options Considered

### Option 1: Maya commandPort (INET Socket) ✓ Selected

Maya's native command port feature opens a TCP socket that accepts commands.

**Pros**:
- Built into Maya - no plugins required
- Cross-platform (Windows, macOS, Linux)
- Well-documented by Autodesk
- Supports both Python and MEL
- Commands execute on Maya's main thread (safe for UI)
- Simple text protocol

**Cons**:
- No built-in authentication
- Plaintext communication
- Limited to localhost for security
- Buffer size limitations (4KB default)

### Option 2: mayapy Subprocess

Spawn mayapy as subprocess and communicate via stdin/stdout.

**Pros**:
- Complete isolation
- No Maya GUI required

**Cons**:
- Not suitable for interactive Maya sessions
- No access to current scene in running Maya
- High latency for each command
- Resource intensive

### Option 3: Maya REST Server (Custom)

Build a custom HTTP server plugin for Maya.

**Pros**:
- Modern REST API
- Easy authentication
- JSON payloads

**Cons**:
- Requires Maya plugin development
- Must handle Maya's single-threaded model
- Significant development effort
- Plugin distribution complexity

### Option 4: Unix Domain Sockets

Use filesystem-based sockets for IPC.

**Pros**:
- Slightly faster than TCP
- More secure (filesystem permissions)

**Cons**:
- Not available on Windows
- Cross-platform complexity
- Maya commandPort supports this, but we lose Windows support

### Option 5: Shared Memory / Memory-Mapped Files

Direct memory sharing between processes.

**Pros**:
- Very fast
- Efficient for large data

**Cons**:
- Complex implementation
- Platform-specific APIs
- Difficult to handle Maya's main thread requirement
- Not suitable for command-response patterns

## Rationale

Maya commandPort (INET) was selected because:

1. **Zero deployment friction**: Works with any Maya installation
2. **Cross-platform**: Same code works on Windows, macOS, Linux
3. **Main thread safety**: Commands execute safely on Maya's main thread
4. **Proven reliability**: Used by many tools (VSCode extensions, IDE plugins)
5. **Sufficient security**: Localhost-only binding with no arbitrary code exposure addresses main risks

The limitations are acceptable:
- **No auth**: Localhost-only negates network attack vectors
- **Plaintext**: Same-machine communication, encryption adds complexity
- **Buffer size**: Can be configured; most commands are small

## Implementation Details

### Maya-Side Setup

```python
import maya.cmds as cmds

cmds.commandPort(
    name=":7001",           # TCP port
    sourceType="python",    # Python interpreter
    echoOutput=True,        # Return results
)
```

### MCP Server Client

```python
import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(5.0)
client.connect(("localhost", 7001))
client.sendall(b"cmds.ls()")
result = client.recv(4096)
```

### Security Mitigations

1. Only localhost connections accepted
2. MCP tools are explicit, no arbitrary code
3. Input validation on all parameters
4. Error sanitization

## Consequences

### Positive

- Users don't need to install Maya plugins
- Same approach works for Maya 2020+
- Well-understood failure modes
- Easy to debug (telnet testing possible)

### Negative

- Maya must be running before MCP server connects
- User must manually open commandPort in Maya
- Large responses may require multiple recv() calls

### Neutral

- Performance is adequate for interactive use (~10ms round-trip)
- Buffer handling adds code complexity

## Related Decisions

- [ADR-0002]: Error handling strategy (future)
- [ADR-0003]: Resilience levels (future)

## References

- [Maya commandPort Documentation](https://help.autodesk.com/cloudhelp/2020/ENU/Maya-Tech-Docs/CommandsPython/commandPort.html)
- [MayaSublime implementation](https://github.com/justinfx/MayaSublime)
- [NCCA mayaport extension](https://github.com/NCCA/mayaport)
