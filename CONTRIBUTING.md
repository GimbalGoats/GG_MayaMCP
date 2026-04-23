# Contributing to Maya MCP

Thank you for your interest in contributing to Maya MCP! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- Autodesk Maya (for integration testing)

### Setting Up Your Environment

1. **Fork and clone the repository:**

   ```bash
   git clone https://github.com/YOUR_USERNAME/GG_MayaMCP.git
   cd GG_MayaMCP
   ```

   Or clone the upstream repository directly if you are contributing without a fork:

   ```bash
   git clone https://github.com/GimbalGoats/GG_MayaMCP.git
   cd GG_MayaMCP
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # Unix/macOS
   source .venv/bin/activate
   ```

3. **Install in development mode:**

   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify your setup:**

   The examples below use `python -m ...`; on Windows, `py -m ...` is equivalent.

   ```bash
   python -m ruff check .
   python -m mypy src/
   python -m pytest
   ```

## Code Style

### Type Hints

All code must be fully type-hinted and pass `mypy --strict`:

```python
# Good
def process_node(node_name: str, attributes: list[str]) -> dict[str, Any]:
    ...

# Bad - missing type hints
def process_node(node_name, attributes):
    ...
```

### Docstrings

Use Google-style docstrings for all public modules, classes, and functions:

```python
def get_node_attributes(node_name: str, attributes: list[str] | None = None) -> dict[str, Any]:
    """Retrieve attribute values from a Maya node.

    Args:
        node_name: The full DAG path or short name of the node.
        attributes: List of attribute names to query. If None, returns all
            queryable attributes.

    Returns:
        Dictionary mapping attribute names to their current values.

    Raises:
        NodeNotFoundError: If the specified node does not exist.
        MayaUnavailableError: If Maya is not connected.

    Example:
        >>> get_node_attributes("pCube1", ["translateX", "translateY"])
        {"translateX": 0.0, "translateY": 5.0}
    """
```

### Formatting

We use `ruff` for both linting and formatting:

```bash
# Check for issues
python -m ruff check .

# Auto-fix issues
python -m ruff check --fix .

# Format code
python -m ruff format .
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=maya_mcp --cov-report=html

# Run specific test file
python -m pytest tests/test_transport_commandport.py

# Run tests matching a pattern
python -m pytest -k "test_health"
```

### Writing Tests

- All new features must have tests
- Use mocks for Maya transport layer (no real Maya required for unit tests)
- Use `pytest-asyncio` for async tests
- Follow existing test patterns

```python
import pytest
from unittest.mock import MagicMock, patch

from maya_mcp.transport.commandport import CommandPortClient

def test_client_handles_connection_refused():
    """Client should raise MayaUnavailableError when connection is refused."""
    client = CommandPortClient(host="localhost", port=7001)
    
    with patch("socket.socket") as mock_socket:
        mock_socket.return_value.connect.side_effect = ConnectionRefusedError()
        
        with pytest.raises(MayaUnavailableError):
            client.execute("print('test')")
```

## Pull Request Process

1. **Create a feature branch:**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clean, typed, documented code
   - Add/update tests as needed
   - Update documentation if applicable

3. **Verify your changes:**

   ```bash
   python -m ruff check .
   python -m ruff format --check .
   python -m mypy src/
   python -m pytest
   python -m mkdocs build
   ```

4. **Commit with a clear message:**

   ```bash
   git commit -m "feat: add node attribute querying tool"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation changes
   - `test:` adding/updating tests
   - `refactor:` code refactoring
   - `chore:` maintenance tasks

5. **Push and create a PR:**

   ```bash
   git push origin feature/your-feature-name
   ```

6. **PR Requirements:**
   - Clear description of changes
   - All checks passing (lint, typecheck, tests)
   - Documentation updated if needed
   - Tests added for new functionality

## Architecture Guidelines

### Tool Design

MCP tools should be thin wrappers around core functions:

```python
# Good - tool delegates to core function
@mcp.tool
def list_nodes(node_type: str) -> list[str]:
    """List Maya nodes of a specific type."""
    return core.list_nodes_by_type(node_type)

# Bad - tool contains business logic
@mcp.tool
def list_nodes(node_type: str) -> list[str]:
    """List Maya nodes of a specific type."""
    result = transport.execute(f"cmds.ls(type='{node_type}')")
    return [n.strip() for n in result.split(",") if n]
```

### Transport Isolation

Never import `maya.cmds` in the MCP server process:

```python
# Good - use transport layer
from maya_mcp.transport import get_client

def get_selection() -> list[str]:
    client = get_client()
    return client.execute("cmds.ls(selection=True)")

# Bad - direct Maya import
import maya.cmds as cmds  # This will fail!

def get_selection() -> list[str]:
    return cmds.ls(selection=True)
```

### Error Handling

Use typed errors from `maya_mcp.errors`:

```python
from maya_mcp.errors import MayaUnavailableError, NodeNotFoundError

def get_node(name: str) -> dict[str, Any]:
    if not client.is_connected():
        raise MayaUnavailableError("Not connected to Maya")
    
    result = client.execute(f"cmds.objExists('{name}')")
    if not result:
        raise NodeNotFoundError(f"Node not found: {name}")
    
    return {...}
```

## Documentation

### Building Docs

```bash
# Serve locally with hot reload
python -m mkdocs serve

# Build static site
python -m mkdocs build
```

### Documentation Standards

- Update relevant docs when changing functionality
- Add docstrings to all public APIs
- Include examples in docstrings
- Keep specs in sync with implementation

## Publishing Releases

PyPI publishing uses Trusted Publishing through GitHub Actions instead of a
long-lived API token.

Not every merge needs a new package release.
In general, cut a new PyPI version only when shipped package behavior,
dependencies, entrypoints, or package metadata need to change for installers.
Docs-only, README-only, CI-only, and contributor-workflow changes usually do
not require a new package version unless you intentionally want to refresh the
PyPI project page content.

Release workflow:

1. Merge the release prep into `main`
2. Create and push a version tag such as `v0.4.0`
3. Publish a GitHub Release for that tag
4. Ensure PyPI Trusted Publishing is configured for this repository

The checked-in publish workflow is:

- file: `.github/workflows/publish-pypi.yml`
- GitHub environment: `pypi`

For PyPI Trusted Publisher configuration on the `maya-mcp` project, use:

- owner: `GimbalGoats`
- repository: `GG_MayaMCP`
- workflow filename: `publish-pypi.yml`
- environment: `pypi`

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas

Thank you for contributing!
