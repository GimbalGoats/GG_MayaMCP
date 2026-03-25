# Transport Layer Specification

This document specifies the transport layer that connects Maya MCP to Maya's commandPort.

## Overview

The transport layer provides a typed Python client for communicating with Maya via its `commandPort` socket interface. It handles:

- TCP socket connection management
- Command encoding (UTF-8)
- Response parsing
- Timeout enforcement
- Retry with exponential backoff
- Error translation to typed exceptions

## Maya commandPort Background

Maya's `commandPort` is a built-in feature that opens a TCP socket to receive commands from external processes.

### Opening a commandPort in Maya

```python
import maya.cmds as cmds

# Close existing port (if any)
try:
    cmds.commandPort(name=":7001", close=True)
except:
    pass

# Open Python commandPort
cmds.commandPort(
    name=":7001",           # Port number (: prefix = INET socket)
    sourceType="python",    # Command interpreter
    echoOutput=True,        # Send output back to client
)
```

### Port Naming Conventions

| Format | Type | Example |
|--------|------|---------|
| `:7001` | INET (TCP) | TCP socket on port 7001 |
| `/tmp/maya` | UNIX domain | Local socket file (Unix/macOS only) |

Maya MCP uses INET sockets for cross-platform compatibility.

## CommandPortClient

### Class Definition

```python
class CommandPortClient:
    """Client for communicating with Maya via commandPort.
    
    This client manages socket connections to Maya's commandPort,
    handles timeouts and retries, and translates errors to typed
    exceptions.
    
    The client is designed for Level 1 resilience:
    - Detects when Maya is unavailable
    - Returns typed errors
    - Automatically reconnects on next call when Maya restarts
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 7001,
        connect_timeout: float = 5.0,
        command_timeout: float = 30.0,
        max_retries: int = 3,
        retry_base_delay: float = 0.5,
    ) -> None: ...
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | `str` | `"localhost"` | Target host (localhost only in v0) |
| `port` | `int` | `7001` | Target port number |
| `connect_timeout` | `float` | `5.0` | Connection timeout in seconds |
| `command_timeout` | `float` | `30.0` | Command execution timeout in seconds |
| `max_retries` | `int` | `3` | Maximum retry attempts |
| `retry_base_delay` | `float` | `0.5` | Base delay for exponential backoff |

### Public Methods

#### `connect() -> bool`

Establish connection to Maya commandPort.

**Returns**: `True` if connected.

**Raises**: `MayaUnavailableError` after exhausting retries.

```python
client = CommandPortClient()
try:
    if client.connect():
        print("Connected to Maya")
except MayaUnavailableError as e:
    print(f"Cannot connect: {e}")
```

#### `disconnect() -> bool`

Close the connection to Maya.

**Returns**: `True` if disconnected, `False` if wasn't connected.

```python
client.disconnect()
```

#### `execute(command: str) -> str`

Execute a Python command in Maya and return the result.

**Parameters**:
- `command`: Python code to execute in Maya

**Returns**: Command output as string.

**Raises**:
- `MayaUnavailableError`: Cannot connect to Maya
- `MayaCommandError`: Command execution failed
- `MayaTimeoutError`: Command timed out

```python
result = client.execute("cmds.ls(selection=True)")
print(f"Selection: {result}")
```

#### `is_connected() -> bool`

Check if currently connected to Maya.

**Returns**: Connection status.

#### `get_status() -> ConnectionStatus`

Get detailed connection status.

**Returns**: `ConnectionStatus` enum value.

```python
from maya_mcp.types import ConnectionStatus

status = client.get_status()
if status == ConnectionStatus.OK:
    print("Connected and healthy")
elif status == ConnectionStatus.OFFLINE:
    print("Not connected")
elif status == ConnectionStatus.RECONNECTING:
    print("Attempting to reconnect")
```

## Connection Lifecycle

### State Machine

```
                    ┌──────────────┐
                    │              │
        ┌──────────►│   OFFLINE    │◄──────────┐
        │           │              │           │
        │           └──────┬───────┘           │
        │                  │                   │
        │           connect()                  │
        │                  │                   │
        │                  ▼                   │
        │           ┌──────────────┐           │
        │           │              │           │
disconnect()        │ RECONNECTING │           │ max retries
        │           │              │           │ exceeded
        │           └──────┬───────┘           │
        │                  │                   │
        │           success│                   │
        │                  │                   │
        │                  ▼                   │
        │           ┌──────────────┐           │
        │           │              │           │
        └───────────│      OK      ├───────────┘
                    │              │  socket error
                    └──────────────┘
```

### Level 1 Resilience Behavior

1. **Detection**: Socket errors trigger state transition to `OFFLINE`
2. **Error Reporting**: `MayaUnavailableError` returned to caller with context
3. **Recovery**: Next call attempts reconnection (state: `RECONNECTING`)
4. **Backoff**: Retries use exponential backoff to avoid overwhelming Maya

## Timeout Behavior

### Connect Timeout

Applied when establishing the TCP connection:

```python
socket.settimeout(connect_timeout)
socket.connect((host, port))  # Raises socket.timeout
```

### Command Timeout

Applied when waiting for command response:

```python
socket.settimeout(command_timeout)
response = socket.recv(BUFFER_SIZE)  # Raises socket.timeout
```

### Timeout Translation

| Socket Exception | Maya MCP Exception |
|------------------|-------------------|
| `socket.timeout` on connect | `MayaUnavailableError` |
| `socket.timeout` on recv | `MayaTimeoutError` |

## Retry Strategy

### Exponential Backoff

Delays between retry attempts:

| Attempt | Delay (with base=0.5s) |
|---------|------------------------|
| 1 | 0.5s |
| 2 | 1.0s |
| 3 | 2.0s |

Formula: `delay = retry_base_delay * (2 ** attempt)`

### Retry Triggers

Retries are attempted for:
- Connection refused
- Connection reset
- Network unreachable

Retries are NOT attempted for:
- Command execution errors (bug in command)
- Timeout after connection established
- Invalid responses

## Protocol Details

### Command Encoding

Commands are sent as UTF-8 encoded strings:

```python
command_bytes = command.encode("utf-8")
socket.sendall(command_bytes)
```

### Response Handling

Maya's commandPort with `echoOutput=True` sends back command results:

```python
BUFFER_SIZE = 4096
response = socket.recv(BUFFER_SIZE)
result = response.decode("utf-8")
```

### Multi-line Commands

For multi-line Python code, wrap in exec():

```python
code = '''
import maya.cmds as cmds
result = cmds.ls(type="mesh")
print(result)
'''
client.execute(code)
```

## Error Handling

### Exception Hierarchy

```
MayaMCPError
├── MayaUnavailableError
│   └── Raised when Maya cannot be reached
├── MayaCommandError
│   └── Raised when command execution fails
└── MayaTimeoutError
    └── Raised when command times out
```

### Error Context

All exceptions include context for debugging:

```python
class MayaUnavailableError(MayaMCPError):
    def __init__(
        self,
        message: str,
        host: str,
        port: int,
        attempts: int,
        last_error: str | None = None,
    ) -> None: ...
```

## Thread Safety

The current implementation is NOT thread-safe. For concurrent access:

1. Use a single client per thread
2. Or implement external synchronization
3. Concurrent request handling is out of scope for v0

## Example Usage

```python
from maya_mcp.transport import CommandPortClient
from maya_mcp.errors import MayaUnavailableError, MayaCommandError

# Create client with custom config
client = CommandPortClient(
    host="localhost",
    port=7001,
    connect_timeout=5.0,
    command_timeout=30.0,
)

try:
    # Connect (optional - execute() auto-connects)
    client.connect()
    
    # Execute commands
    selection = client.execute("cmds.ls(selection=True)")
    print(f"Current selection: {selection}")
    
    # Scene info
    scene_name = client.execute("cmds.file(query=True, sceneName=True)")
    print(f"Scene: {scene_name}")
    
except MayaUnavailableError as e:
    print(f"Maya not available: {e.message}")
    print(f"Tried {e.attempts} times to connect to {e.host}:{e.port}")
    
except MayaCommandError as e:
    print(f"Command failed: {e.message}")
    
finally:
    client.disconnect()
```
