# Maya MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP (Model Context Protocol) server for controlling Autodesk Maya via its commandPort socket interface.

## Overview

Maya MCP enables AI assistants and other MCP clients to interact with a running Maya instance. It provides a typed, safe interface for:

- Querying scene information
- Managing selections
- Manipulating nodes
- Health monitoring and connection management

**Key Design Principles:**

- **No arbitrary code execution** - All operations are explicit, typed tools
- **Localhost-only by default** - Security-first design
- **Crash-resilient** - Detects Maya unavailability and recovers gracefully
- **Transport isolation** - MCP server never imports `maya.cmds`

## Quick Start

### Prerequisites

- Python 3.10+
- Autodesk Maya with commandPort enabled
- An MCP-compatible client

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/maya-mcp.git
cd maya-mcp

# Install in development mode
pip install -e ".[dev]"
```

### Enable Maya commandPort

In Maya's Script Editor (Python), run:

```python
import maya.cmds as cmds

# Close any existing ports
try:
    cmds.commandPort(name=":7001", close=True)
except:
    pass

# Open Python commandPort on localhost:7001
cmds.commandPort(name=":7001", sourceType="python", echoOutput=True)
print("commandPort opened on :7001")
```

### Run the MCP Server

```bash
# Run with stdio transport (default for MCP)
python -m maya_mcp.server

# Or using the CLI
maya-mcp
```

### Configure Your MCP Client

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "maya": {
      "command": "python",
      "args": ["-m", "maya_mcp.server"],
      "env": {}
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `health.check` | Check Maya connection status |
| `maya.connect` | Establish connection to Maya commandPort |
| `maya.disconnect` | Close Maya connection |
| `scene.info` | Get current scene information |
| `nodes.list` | List nodes by type |
| `selection.get` | Get current selection |
| `selection.set` | Set selection |

See [docs/spec/tools.md](docs/spec/tools.md) for detailed API documentation.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linting
ruff check .
ruff format .

# Run type checking
mypy src/

# Run tests
pytest

# Build documentation
mkdocs serve
```

## Architecture

```
maya-mcp/
├── src/maya_mcp/
│   ├── server.py          # FastMCP server entrypoint
│   ├── errors.py          # Typed error hierarchy
│   ├── types.py           # Shared type definitions
│   ├── tools/             # MCP tool implementations
│   │   ├── health.py      # Health check tool
│   │   ├── connection.py  # Connect/disconnect tools
│   │   ├── scene.py       # Scene operations
│   │   ├── nodes.py       # Node operations
│   │   └── selection.py   # Selection operations
│   └── transport/
│       └── commandport.py # Maya commandPort client
├── tests/                 # Pytest test suite
└── docs/                  # MkDocs documentation
```

## Documentation

- [Product Requirements](docs/prd.md)
- [Architecture Overview](docs/spec/overview.md)
- [Tool Specifications](docs/spec/tools.md)
- [Transport Layer](docs/spec/transport.md)
- [Security Model](docs/spec/security.md)
- [API Reference](docs/api/reference.md)

## License

MIT License - see [LICENSE](LICENSE) for details.
