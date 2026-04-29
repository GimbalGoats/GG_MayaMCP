---
summary: "Practical tool guide covering Maya MCP tool families, stable naming, defaults, limits, annotations, and error behavior."
read_when:
  - When adding, changing, or removing MCP tools, tool schemas, defaults, limits, risk annotations, or read/write behavior.
  - When validating tool output shapes, error responses, pagination, token-budget behavior, or scene safety prompts.
---

# Tool Guide

This page is the compact implementation-facing guide to the Maya MCP tool surface.

For exact argument and return shapes, the authoritative source is the MCP `tools/list` metadata exposed by the running server. That is the most stable place to inspect current `inputSchema`, `outputSchema`, descriptions, and annotations.

## Core Contract Rules

These should remain true unless a reviewed compatibility change intentionally breaks them:

- tool names stay stable and use dotted segments such as `namespace.action` or `namespace.subnamespace.action`
- every advertised tool has a title, description, `inputSchema`, `outputSchema`, and annotations
- read-only and mutating actions remain separate where practical
- defaults and limits are treated as part of the client-facing contract
- tool-visible behavior belongs in docs when it changes

## Tool Naming

Tool names follow dotted hierarchical segments such as `namespace.action` or `namespace.subnamespace.action`.

The Claude Desktop MCPB package is the compatibility exception. Claude Desktop
rejects dots in connector tool names, so that bundle advertises underscore
aliases such as `health_check`, `scene_info`, and
`modeling_create_polygon_primitive`. The underlying tool behavior and schemas
are otherwise the same as the standard dotted-name server.

Current namespaces:

- `health`
- `maya`
- `scene`
- `nodes`
- `attributes`
- `selection`
- `connections`
- `mesh`
- `viewport`
- `modeling`
- `shading`
- `skin`
- `animation`
- `curve`
- `script`

There are currently 71 tools.

## Source Of Truth

Use these sources in this order:

1. live MCP `tools/list` metadata for exact schemas and annotations
2. this page for stable defaults, limits, risk model, and scene-safety behavior
3. implementation code in `src/maya_mcp/registrars/` and `src/maya_mcp/tools/`

## Tool Families

| Family | Count | Use when you want to... | Core tools |
|---|---:|---|---|
| `health` | 1 | check whether Maya is reachable | `health.check` |
| `maya` | 2 | explicitly connect or disconnect transport | `maya.connect`, `maya.disconnect` |
| `scene` | 9 | inspect the scene, open/save files, import/export, undo/redo | `scene.info`, `scene.open`, `scene.save`, `scene.export` |
| `nodes` | 7 | create, rename, parent, duplicate, or inspect DAG/DG nodes | `nodes.list`, `nodes.create`, `nodes.info` |
| `attributes` | 2 | read or write attributes | `attributes.get`, `attributes.set` |
| `selection` | 6 | manage object and component selections | `selection.get`, `selection.set`, `selection.convert_components` |
| `connections` | 5 | inspect or edit DG connections and history | `connections.list`, `connections.get`, `connections.connect` |
| `mesh` | 3 | inspect mesh data and run topology checks | `mesh.info`, `mesh.vertices`, `mesh.evaluate` |
| `viewport` | 1 | capture an image from Maya | `viewport.capture` |
| `modeling` | 15 | perform common polygon modeling actions | `modeling.create_polygon_primitive`, `modeling.extrude_faces`, `modeling.boolean` |
| `shading` | 3 | create and assign materials | `shading.create_material`, `shading.assign_material` |
| `skin` | 6 | bind geometry and inspect or edit weights | `skin.bind`, `skin.weights.get`, `skin.weights.set` |
| `animation` | 6 | control time and keyframes | `animation.set_time`, `animation.get_keyframes`, `animation.delete_keyframes` |
| `curve` | 2 | inspect NURBS curve data | `curve.info`, `curve.cvs` |
| `script` | 3 | discover approved scripts or run opt-in execution paths | `script.list`, `script.execute`, `script.run` |

## Exact Tool List

### Health and connection

- `health.check`
- `maya.connect`
- `maya.disconnect`

### Scene

- `scene.info`
- `scene.new`
- `scene.open`
- `scene.save`
- `scene.save_as`
- `scene.import`
- `scene.export`
- `scene.undo`
- `scene.redo`

### Nodes and attributes

- `nodes.list`
- `nodes.create`
- `nodes.delete`
- `nodes.rename`
- `nodes.parent`
- `nodes.duplicate`
- `nodes.info`
- `attributes.get`
- `attributes.set`

### Selection and connections

- `selection.get`
- `selection.set`
- `selection.clear`
- `selection.set_components`
- `selection.get_components`
- `selection.convert_components`
- `connections.list`
- `connections.get`
- `connections.connect`
- `connections.disconnect`
- `connections.history`

### Mesh, viewport, curves

- `mesh.info`
- `mesh.vertices`
- `mesh.evaluate`
- `viewport.capture`
- `curve.info`
- `curve.cvs`

Mesh node inputs accept either short node names or Maya DAG paths such as
`|group1|mesh1`. The `|` character is accepted only as a hierarchy separator;
malformed paths and shell/control characters are rejected before commands are
sent to Maya.

### Modeling

- `modeling.create_polygon_primitive`
- `modeling.extrude_faces`
- `modeling.boolean`
- `modeling.combine`
- `modeling.separate`
- `modeling.merge_vertices`
- `modeling.bevel`
- `modeling.bridge`
- `modeling.insert_edge_loop`
- `modeling.delete_faces`
- `modeling.move_components`
- `modeling.freeze_transforms`
- `modeling.delete_history`
- `modeling.center_pivot`
- `modeling.set_pivot`

### Shading, skinning, animation, scripts

- `shading.create_material`
- `shading.assign_material`
- `shading.set_material_color`
- `skin.bind`
- `skin.unbind`
- `skin.influences`
- `skin.weights.get`
- `skin.weights.set`
- `skin.copy_weights`
- `animation.set_time`
- `animation.get_time_range`
- `animation.set_time_range`
- `animation.set_keyframe`
- `animation.get_keyframes`
- `animation.delete_keyframes`
- `script.list`
- `script.execute`
- `script.run`

## Defaults and Limits That Matter

These are the defaults most likely to affect user experience or token usage:

| Tool or area | Default / limit | Why it exists |
|---|---|---|
| `nodes.list` | `limit=500` | Prevents large-scene dumps by default |
| `connections.list` | `limit=500` | Keeps graph inspection bounded |
| `connections.history` | `limit=500` | Avoids oversized history chains |
| `mesh.vertices` | `limit=1000` | Keeps mesh queries practical |
| `mesh.evaluate` | `limit=500` per check | Bounds topology analysis payload size |
| `curve.cvs` | `limit=1000` | Supports pagination on large curves |
| `skin.weights.get` | `limit=100` vertices | Prevents weight-data explosions |
| `viewport.capture` | inline image cap around 10 MB | Avoids huge inline responses |
| script file size | 1 MB | Limits approved-script payload size |
| raw script code | 100 KB | Limits opt-in raw execution payload size |
| `MAYA_MCP_SCRIPT_TIMEOUT` | `60s` | Bounded script execution by default |

Some modeling responses also pass through shared response guards so large Maya outputs do not flood the client.

If any default, limit, truncation flag, or paging behavior changes, update this page in the same change.

## Scene Safety Behavior

`scene.new` and `scene.open` still refuse by default when the current scene has unsaved changes.

Current contract:

- `force=false` keeps the safe default and does not discard changes silently
- `force=true` allows discard-and-proceed behavior
- clients that advertise MCP form elicitation can receive an in-band discard-changes confirmation
- clients without elicitation support keep the refusal flow and must retry explicitly

This behavior is client-visible and should be treated as part of the tool contract.

## Safe Usage Patterns

### Best first calls

For a new session:

1. `health.check`
2. `scene.info`
3. `nodes.list`

### Use read tools before write tools

Examples:

- `attributes.get` before `attributes.set`
- `selection.get` before `selection.set`
- `skin.weights.get` before `skin.weights.set`

### Prefer workflow tools over raw script execution

If a dedicated tool exists for the action, use it instead of `script.run`.

## Progress-Aware Tools

These tools can emit coarse progress updates when the client provides a progress token:

- `scene.export`
- `mesh.evaluate`
- `skin.weights.get`
- `skin.weights.set`

The JSON result shape stays the same; progress is reported separately through MCP progress notifications.

Progress support is part of client-visible behavior. If progress-enabled coverage changes, update this page and the relevant tests.

## Annotation Model

Maya MCP relies on MCP tool annotations so clients can make safer choices.

Risk classes in practice:

| Class | Meaning | Typical tools |
|---|---|---|
| read-only | safe inspection; no Maya state changes | `health.check`, `scene.info`, `nodes.list`, `mesh.info` |
| write but idempotent | changes Maya state, but repeating the same call should settle to the same result | `maya.connect`, `attributes.set`, `selection.clear`, `scene.export` |
| write and non-idempotent | changes Maya state and repeating it may stack or diverge | `nodes.create`, `scene.import`, `modeling.extrude_faces`, `animation.set_keyframe` |
| destructive or high-risk | removes data, replaces scene state, changes harder-to-recover state, or is intentionally powerful | `scene.new`, `scene.open`, `scene.save`, `nodes.delete`, `modeling.delete_history`, `script.run` |

All advertised tools include:

- a stable tool `name`
- a human-readable `title`
- a non-empty `description`
- an object `inputSchema`
- an object `outputSchema`
- populated annotations

Annotation changes should be treated as compatibility changes because clients may use them for confirmation and execution behavior.

## Error Shape

Client-facing failures use the shared error model:

| Field | Meaning |
|---|---|
| `error` | typed error name |
| `message` | human-readable explanation |
| `details` | structured recovery context when useful |

Representative error types:

- `MayaUnavailableError`
- `MayaCommandError`
- `MayaTimeoutError`
- `ValidationError`

## Change Triggers

Update this page when any of these change:

- tool names
- tool schemas
- defaults
- limits
- annotations
- read/write separation
- trust model for script or execution tools
- progress support
- scene safety prompting behavior
- truncation or pagination behavior

If exact schemas change, also treat the serialized MCP `tools/list` metadata as part of the public contract.

## Related Docs

- [Architecture Overview](overview.md)
- [Security Specification](security.md)
- [API Reference](../api/reference.md)
