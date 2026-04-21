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

### Connections

| Model | Backing tools |
|-------|---------------|
| `maya_mcp.tools.connections.ConnectionEntry` | `connections.list` |
| `maya_mcp.tools.connections.ConnectionsListOutput` | `connections.list` |
| `maya_mcp.tools.connections.ConnectionAttributeInfo` | `connections.get` |
| `maya_mcp.tools.connections.ConnectionsGetOutput` | `connections.get` |
| `maya_mcp.tools.connections.ConnectionsConnectOutput` | `connections.connect` |
| `maya_mcp.tools.connections.ConnectionPair` | `connections.disconnect` |
| `maya_mcp.tools.connections.ConnectionsDisconnectOutput` | `connections.disconnect` |
| `maya_mcp.tools.connections.ConnectionHistoryEntry` | `connections.history` |
| `maya_mcp.tools.connections.ConnectionsHistoryOutput` | `connections.history` |

### Viewport

| Model | Backing tools |
|-------|---------------|
| `maya_mcp.tools.viewport.ViewportCaptureOutput` | `viewport.capture` |

### Modeling

| Model | Backing tools |
|-------|---------------|
| `maya_mcp.tools.modeling.ModelingCreatePolygonPrimitiveOutput` | `modeling.create_polygon_primitive` |
| `maya_mcp.tools.modeling.ModelingExtrudeFacesOutput` | `modeling.extrude_faces` |
| `maya_mcp.tools.modeling.ModelingBooleanOutput` | `modeling.boolean` |
| `maya_mcp.tools.modeling.ModelingCombineOutput` | `modeling.combine` |
| `maya_mcp.tools.modeling.ModelingSeparateOutput` | `modeling.separate` |
| `maya_mcp.tools.modeling.ModelingMergeVerticesOutput` | `modeling.merge_vertices` |
| `maya_mcp.tools.modeling.ModelingBevelOutput` | `modeling.bevel` |
| `maya_mcp.tools.modeling.ModelingBridgeOutput` | `modeling.bridge` |
| `maya_mcp.tools.modeling.ModelingInsertEdgeLoopOutput` | `modeling.insert_edge_loop` |
| `maya_mcp.tools.modeling.ModelingDeleteFacesOutput` | `modeling.delete_faces` |
| `maya_mcp.tools.modeling.ModelingMoveComponentsOutput` | `modeling.move_components` |
| `maya_mcp.tools.modeling.ModelingFreezeTransformsOutput` | `modeling.freeze_transforms` |
| `maya_mcp.tools.modeling.ModelingDeleteHistoryOutput` | `modeling.delete_history` |
| `maya_mcp.tools.modeling.ModelingCenterPivotOutput` | `modeling.center_pivot` |
| `maya_mcp.tools.modeling.ModelingSetPivotOutput` | `modeling.set_pivot` |

### Shading

| Model | Backing tools |
|-------|---------------|
| `maya_mcp.tools.shading.ShadingCreateMaterialOutput` | `shading.create_material` |
| `maya_mcp.tools.shading.ShadingAssignMaterialOutput` | `shading.assign_material` |
| `maya_mcp.tools.shading.ShadingSetMaterialColorOutput` | `shading.set_material_color` |

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

### Animation

| Model | Backing tools |
|-------|---------------|
| `maya_mcp.tools.animation.AnimationSetTimeOutput` | `animation.set_time` |
| `maya_mcp.tools.animation.AnimationGetTimeRangeOutput` | `animation.get_time_range` |
| `maya_mcp.tools.animation.AnimationSetTimeRangeOutput` | `animation.set_time_range` |
| `maya_mcp.tools.animation.AnimationSetKeyframeOutput` | `animation.set_keyframe` |
| `maya_mcp.tools.animation.KeyframeEntry` | `animation.get_keyframes` |
| `maya_mcp.tools.animation.AnimationGetKeyframesOutput` | `animation.get_keyframes` |
| `maya_mcp.tools.animation.AnimationDeleteKeyframesOutput` | `animation.delete_keyframes` |

### Scripts

| Model | Backing tools |
|-------|---------------|
| `maya_mcp.tools.scripts.ScriptListEntry` | `script.list` |
| `maya_mcp.tools.scripts.ScriptListOutput` | `script.list` |
| `maya_mcp.tools.scripts.ScriptExecuteOutput` | `script.execute` |
| `maya_mcp.tools.scripts.ScriptRunOutput` | `script.run` |

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
