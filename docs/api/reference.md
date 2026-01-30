# API Reference

This page documents the Python API for Maya MCP.

## Server Module

::: maya_mcp.server
    options:
      show_root_heading: true
      members:
        - mcp
        - main

## Error Classes

::: maya_mcp.errors
    options:
      show_root_heading: true
      members:
        - MayaMCPError
        - MayaUnavailableError
        - MayaCommandError
        - MayaTimeoutError
        - ValidationError

## Type Definitions

::: maya_mcp.types
    options:
      show_root_heading: true
      members:
        - ConnectionStatus
        - HealthCheckResult
        - ConnectionConfig
        - ConnectResult
        - DisconnectResult

## Transport Layer

::: maya_mcp.transport.commandport
    options:
      show_root_heading: true
      members:
        - CommandPortClient

## Tools

### Health Tools

::: maya_mcp.tools.health
    options:
      show_root_heading: true

### Connection Tools

::: maya_mcp.tools.connection
    options:
      show_root_heading: true

### Scene Tools

::: maya_mcp.tools.scene
    options:
      show_root_heading: true

### Node Tools

::: maya_mcp.tools.nodes
    options:
      show_root_heading: true

### Selection Tools

::: maya_mcp.tools.selection
    options:
      show_root_heading: true
