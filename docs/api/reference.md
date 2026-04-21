---
summary: "Generated API reference index for public Python modules, errors, types, transport, tool modules, and Maya panel APIs."
read_when:
  - When changing public Python API symbols, API-facing docstrings, exported modules, or generated API documentation.
  - When adding or removing public tool modules, transport APIs, errors, types, or Maya panel APIs.
---

# API Reference

This page documents the public Python surface and the tool modules that back the MCP server.

## Typed Result Models

Tool functions return plain dictionaries at runtime, but high-use tools expose
`TypedDict` result models in their public Python annotations. These models
describe the same keys documented in the tool contracts; they do not change
MCP JSON response shapes or error conventions.

### Nodes

| Model | Backing tools |
|-------|---------------|
| `maya_mcp.tools.nodes.NodesListOutput` | `nodes.list` |
| `maya_mcp.tools.nodes.NodesCreateOutput` | `nodes.create` |
| `maya_mcp.tools.nodes.NodesInfoOutput` | `nodes.info` |
| `maya_mcp.tools.nodes.NodesDeleteOutput` | `nodes.delete` |
| `maya_mcp.tools.nodes.NodesRenameOutput` | `nodes.rename` |
| `maya_mcp.tools.nodes.NodesParentOutput` | `nodes.parent` |
| `maya_mcp.tools.nodes.NodesDuplicateOutput` | `nodes.duplicate` |

### Attributes

| Model | Backing tools |
|-------|---------------|
| `maya_mcp.tools.attributes.AttributesGetOutput` | `attributes.get` |
| `maya_mcp.tools.attributes.AttributesSetOutput` | `attributes.set` |

### Selection

| Model | Backing tools |
|-------|---------------|
| `maya_mcp.tools.selection.SelectionOutput` | `selection.get`, `selection.set`, `selection.clear` |
| `maya_mcp.tools.selection.SelectionWithErrorsOutput` | `selection.set_components` |
| `maya_mcp.tools.selection.SelectionComponentsOutput` | `selection.get_components` |
| `maya_mcp.tools.selection.SelectionConvertComponentsOutput` | `selection.convert_components` |

### Mesh

| Model | Backing tools |
|-------|---------------|
| `maya_mcp.tools.mesh.MeshInfoOutput` | `mesh.info` |
| `maya_mcp.tools.mesh.MeshVerticesOutput` | `mesh.vertices` |
| `maya_mcp.tools.mesh.MeshEvaluateOutput` | `mesh.evaluate` |

### Curves

| Model | Backing tools |
|-------|---------------|
| `maya_mcp.tools.curve.CurveInfoOutput` | `curve.info` |
| `maya_mcp.tools.curve.CurveCvsOutput` | `curve.cvs` |

### Skinning

| Model | Backing tools |
|-------|---------------|
| `maya_mcp.tools.skin.SkinBindOutput` | `skin.bind` |
| `maya_mcp.tools.skin.SkinUnbindOutput` | `skin.unbind` |
| `maya_mcp.tools.skin.SkinInfluenceEntry` | `skin.influences` |
| `maya_mcp.tools.skin.SkinInfluencesOutput` | `skin.influences` |
| `maya_mcp.tools.skin.SkinWeightEntry` | `skin.weights.get` |
| `maya_mcp.tools.skin.SkinWeightsGetOutput` | `skin.weights.get` |
| `maya_mcp.tools.skin.SkinWeightsSetOutput` | `skin.weights.set` |
| `maya_mcp.tools.skin.SkinCopyWeightsOutput` | `skin.copy_weights` |

## Package

::: maya_mcp
    options:
      show_root_heading: true

## Server

::: maya_mcp.server
    options:
      show_root_heading: true
      members:
        - mcp
        - main

## Errors

::: maya_mcp.errors
    options:
      show_root_heading: true
      members:
        - MayaMCPError
        - MayaUnavailableError
        - MayaCommandError
        - MayaTimeoutError
        - ValidationError

## Types

::: maya_mcp.types
    options:
      show_root_heading: true

## Transport

::: maya_mcp.transport
    options:
      show_root_heading: true

::: maya_mcp.transport.commandport
    options:
      show_root_heading: true

## Tool Modules

### Health

::: maya_mcp.tools.health
    options:
      show_root_heading: true

### Connection

::: maya_mcp.tools.connection
    options:
      show_root_heading: true

### Scene

::: maya_mcp.tools.scene
    options:
      show_root_heading: true

### Nodes

::: maya_mcp.tools.nodes
    options:
      show_root_heading: true

### Attributes

::: maya_mcp.tools.attributes
    options:
      show_root_heading: true

### Selection

::: maya_mcp.tools.selection
    options:
      show_root_heading: true

### Connections

::: maya_mcp.tools.connections
    options:
      show_root_heading: true

### Mesh

::: maya_mcp.tools.mesh
    options:
      show_root_heading: true

### Viewport

::: maya_mcp.tools.viewport
    options:
      show_root_heading: true

### Modeling

::: maya_mcp.tools.modeling
    options:
      show_root_heading: true

### Shading

::: maya_mcp.tools.shading
    options:
      show_root_heading: true

### Skinning

::: maya_mcp.tools.skin
    options:
      show_root_heading: true

### Animation

::: maya_mcp.tools.animation
    options:
      show_root_heading: true

### Curves

::: maya_mcp.tools.curve
    options:
      show_root_heading: true

### Scripts

::: maya_mcp.tools.scripts
    options:
      show_root_heading: true

## Maya Panel

::: maya_mcp.maya_panel
    options:
      show_root_heading: true

::: maya_mcp.maya_panel.controller
    options:
      show_root_heading: true

::: maya_mcp.maya_panel.preferences
    options:
      show_root_heading: true
