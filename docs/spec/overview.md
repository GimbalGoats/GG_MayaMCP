# Architecture Overview

This document describes the high-level architecture of Maya MCP.

## System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Development Environment                       │
│                                                                      │
│  ┌─────────────────┐                      ┌──────────────────────┐  │
│  │   MCP Client    │                      │    Autodesk Maya     │  │
│  │  (AI Assistant, │     MCP Protocol     │                      │  │
│  │   IDE Plugin,   │◄───────────────────►│  ┌────────────────┐  │  │
│  │   CLI tool)     │                      │  │  commandPort   │  │  │
│  └────────┬────────┘                      │  │  (TCP :7001)   │  │  │
│           │                               │  └───────▲────────┘  │  │
│           │ stdio/http                    │          │           │  │
│           │                               │          │           │  │
│  ┌────────▼────────┐                      │          │           │  │
│  │  Maya MCP       │   TCP localhost:7001 │          │           │  │
│  │  Server         │◄─────────────────────┼──────────┘           │  │
│  │  (FastMCP)      │                      │                      │  │
│  └─────────────────┘                      └──────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Layer Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     MCP Protocol Layer                   │
│  (FastMCP handles MCP protocol, tool dispatch, etc.)     │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│                      Tools Layer                         │
│  maya_mcp/tools/                                         │
│  ┌──────────┐ ┌────────────┐ ┌─────────┐ ┌───────────┐  │
│  │ health   │ │ connection │ │  scene  │ │   nodes   │  │
│  └──────────┘ └────────────┘ └─────────┘ └───────────┘  │
│  ┌───────────┐                                           │
│  │ selection │                                           │
│  └───────────┘                                           │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│                    Core Types Layer                      │
│  maya_mcp/types.py, maya_mcp/errors.py                  │
│  - Pydantic models for tool inputs/outputs              │
│  - Typed error hierarchy                                 │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│                   Transport Layer                        │
│  maya_mcp/transport/commandport.py                      │
│  - Socket connection to Maya                             │
│  - Retry logic, timeouts, backoff                        │
│  - Error translation                                     │
└─────────────────────────────────────────────────────────┘
```

## Module Responsibilities

### `maya_mcp/server.py`

The FastMCP server entrypoint:

- Creates FastMCP server instance
- Registers all tools from `maya_mcp.tools`
- Provides `main()` entry point
- Handles server lifecycle

### `maya_mcp/errors.py`

Typed error hierarchy:

```python
MayaMCPError              # Base class for all errors
├── MayaUnavailableError  # Maya not connected/reachable
├── MayaCommandError      # Command execution failed
├── MayaTimeoutError      # Operation timed out
└── ValidationError       # Invalid input parameters
```

### `maya_mcp/types.py`

Shared type definitions:

- `ConnectionStatus`: Enum for connection states
- `HealthCheckResult`: Response model for health.check
- `ConnectionConfig`: Settings for commandPort client
- Tool-specific input/output models

### `maya_mcp/transport/commandport.py`

Maya commandPort client:

- Socket connection management
- Connect/request timeouts
- Exponential backoff retry
- UTF-8 command encoding
- Error translation to typed exceptions

### `maya_mcp/tools/`

MCP tool implementations:

| Module | Tools | Description |
|--------|-------|-------------|
| `health.py` | `health.check` | Connection health status |
| `connection.py` | `maya.connect`, `maya.disconnect` | Manual connection control |
| `scene.py` | `scene.info` | Scene information queries |
| `nodes.py` | `nodes.list` | Node listing/filtering |
| `selection.py` | `selection.get`, `selection.set` | Selection management |

## Design Decisions

### 1. Transport Isolation

The MCP server process never imports `maya.cmds` or any Maya modules. All communication happens via TCP socket to Maya's commandPort.

**Rationale**:
- MCP server can run in any Python environment
- Maya crashes don't crash the MCP server
- Clear separation of concerns
- Easier testing with mocks

### 2. Typed Error Model

All errors are subclasses of `MayaMCPError` with structured context.

**Rationale**:
- Clients can handle errors programmatically
- Error messages are consistent
- No silent failures
- Easy to extend for new error types

### 3. Thin Tool Wrappers

MCP tools are thin wrappers around core functions. Business logic lives in the transport layer or dedicated modules.

**Rationale**:
- Tools focus on MCP interface
- Core logic is reusable
- Easier to test core functions
- Consistent tool patterns

### 4. Level 1 Resilience

The server detects Maya unavailability, returns typed errors, and can recover when Maya restarts.

**Rationale**:
- Maya crashes are common during development
- Users can restart Maya without restarting MCP server
- Clear error messages guide recovery
- Higher resilience levels can be added later

## Data Flow

### Successful Command

```
Client                MCP Server              CommandPort              Maya
   │                      │                        │                     │
   │  call_tool("scene.info")                      │                     │
   │─────────────────────►│                        │                     │
   │                      │                        │                     │
   │                      │  connect (if needed)   │                     │
   │                      │───────────────────────►│                     │
   │                      │◄───────────────────────│                     │
   │                      │                        │                     │
   │                      │  send command          │                     │
   │                      │───────────────────────►│                     │
   │                      │                        │  execute in Maya    │
   │                      │                        │────────────────────►│
   │                      │                        │◄────────────────────│
   │                      │  receive result        │                     │
   │                      │◄───────────────────────│                     │
   │                      │                        │                     │
   │  tool result         │                        │                     │
   │◄─────────────────────│                        │                     │
```

### Maya Unavailable

```
Client                MCP Server              CommandPort
   │                      │                        │
   │  call_tool("scene.info")                      │
   │─────────────────────►│                        │
   │                      │                        │
   │                      │  connect (retry 1)     │
   │                      │───────────────────────►│ Connection refused
   │                      │                        │
   │                      │  backoff (0.5s)        │
   │                      │  connect (retry 2)     │
   │                      │───────────────────────►│ Connection refused
   │                      │                        │
   │                      │  backoff (1.0s)        │
   │                      │  connect (retry 3)     │
   │                      │───────────────────────►│ Connection refused
   │                      │                        │
   │  MayaUnavailableError│                        │
   │◄─────────────────────│                        │
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAYA_MCP_HOST` | `localhost` | Maya commandPort host |
| `MAYA_MCP_PORT` | `7001` | Maya commandPort port |
| `MAYA_MCP_CONNECT_TIMEOUT` | `5.0` | Connection timeout (seconds) |
| `MAYA_MCP_COMMAND_TIMEOUT` | `30.0` | Command timeout (seconds) |
| `MAYA_MCP_MAX_RETRIES` | `3` | Maximum connection retries |

### Programmatic Configuration

```python
from maya_mcp.transport import CommandPortClient
from maya_mcp.types import ConnectionConfig

config = ConnectionConfig(
    host="localhost",
    port=7001,
    connect_timeout=5.0,
    command_timeout=30.0,
    max_retries=3,
)

client = CommandPortClient(config)
```

## Security Boundaries

See [Security Specification](security.md) for details.

Key boundaries:
- All connections are localhost-only
- No arbitrary code execution
- All tool parameters are validated
- Errors never expose system paths or secrets
