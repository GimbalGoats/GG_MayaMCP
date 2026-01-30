# Tool Specifications

This document specifies all MCP tools provided by Maya MCP.

## Tool Naming Convention

Tools use a hierarchical naming scheme:

- `health.*` - Health and diagnostics
- `maya.*` - Connection management
- `scene.*` - Scene-level operations (info, undo, redo)
- `nodes.*` - Node operations (list, create, delete)
- `attributes.*` - Attribute operations (get, set)
- `selection.*` - Selection management

## Health Tools

### `health.check`

Check the health status of the Maya connection.

**Input**: None

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `status` | `"ok" \| "offline" \| "reconnecting"` | Current connection status |
| `last_error` | `string \| null` | Last error message, if any |
| `last_contact` | `string \| null` | ISO8601 timestamp of last successful contact |
| `host` | `string` | Current target host |
| `port` | `integer` | Current target port |

**Example Response**:

```json
{
  "status": "ok",
  "last_error": null,
  "last_contact": "2025-01-30T10:30:00Z",
  "host": "localhost",
  "port": 7001
}
```

**Status Values**:

| Status | Description |
|--------|-------------|
| `ok` | Connected and responsive |
| `offline` | Not connected, no active attempts |
| `reconnecting` | Attempting to reconnect |

---

## Connection Tools

### `maya.connect`

Establish a connection to Maya's commandPort.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `host` | `string` | No | `"localhost"` | Target host |
| `port` | `integer` | No | `7001` | Target port |
| `source_type` | `"python" \| "mel"` | No | `"python"` | Command interpreter |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `connected` | `boolean` | Whether connection succeeded |
| `host` | `string` | Connected host |
| `port` | `integer` | Connected port |
| `error` | `string \| null` | Error message if connection failed |

**Example Request**:

```json
{
  "host": "localhost",
  "port": 7001,
  "source_type": "python"
}
```

**Example Response (Success)**:

```json
{
  "connected": true,
  "host": "localhost",
  "port": 7001,
  "error": null
}
```

**Example Response (Failure)**:

```json
{
  "connected": false,
  "host": "localhost",
  "port": 7001,
  "error": "Connection refused - is Maya running with commandPort open?"
}
```

---

### `maya.disconnect`

Close the connection to Maya.

**Input**: None

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `disconnected` | `boolean` | Whether disconnect succeeded |
| `was_connected` | `boolean` | Whether was connected before |

**Example Response**:

```json
{
  "disconnected": true,
  "was_connected": true
}
```

---

## Scene Tools

### `scene.info`

Get information about the current Maya scene.

**Input**: None

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `file_path` | `string \| null` | Current scene file path |
| `modified` | `boolean` | Whether scene has unsaved changes |
| `fps` | `number` | Frames per second |
| `frame_range` | `[number, number]` | Start and end frame |
| `up_axis` | `"y" \| "z"` | Scene up axis |

**Example Response**:

```json
{
  "file_path": "C:/projects/myScene.ma",
  "modified": false,
  "fps": 24.0,
  "frame_range": [1, 100],
  "up_axis": "y"
}
```

---

### `scene.undo`

Undo the last operation in Maya. Critical for LLM error recovery.

**Input**: None

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Whether undo succeeded |
| `undone` | `string \| null` | Description of the undone action |
| `can_undo` | `boolean` | Whether more undo operations are available |
| `can_redo` | `boolean` | Whether redo is now available |

**Example Response**:

```json
{
  "success": true,
  "undone": "setAttr pCube1.translateX",
  "can_undo": true,
  "can_redo": true
}
```

**Example Response (Nothing to Undo)**:

```json
{
  "success": false,
  "undone": null,
  "can_undo": false,
  "can_redo": false
}
```

---

### `scene.redo`

Redo the last undone operation in Maya.

**Input**: None

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Whether redo succeeded |
| `redone` | `string \| null` | Description of the redone action |
| `can_undo` | `boolean` | Whether undo is now available |
| `can_redo` | `boolean` | Whether more redo operations are available |

**Example Response**:

```json
{
  "success": true,
  "redone": "setAttr pCube1.translateX",
  "can_undo": true,
  "can_redo": false
}
```

**Example Response (Nothing to Redo)**:

```json
{
  "success": false,
  "redone": null,
  "can_undo": true,
  "can_redo": false
}
```

---

## Node Tools

### `nodes.list`

List nodes in the scene, optionally filtered by type.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `node_type` | `string` | No | `null` | Filter by node type (e.g., "transform", "mesh") |
| `pattern` | `string` | No | `"*"` | Name pattern filter (supports wildcards) |
| `long_names` | `boolean` | No | `false` | Return full DAG paths |
| `limit` | `integer` | No | `500` | Max nodes to return. Use 0 for unlimited. |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `nodes` | `string[]` | List of node names |
| `count` | `integer` | Number of nodes returned |
| `truncated` | `boolean` | True if results were truncated (only present if limit hit) |
| `total_count` | `integer` | Total matching nodes before limit (only present if truncated) |

**Example Request**:

```json
{
  "node_type": "mesh",
  "pattern": "pCube*"
}
```

**Example Response**:

```json
{
  "nodes": ["pCubeShape1", "pCubeShape2", "pCubeShape3"],
  "count": 3
}
```

**Example Response (Truncated)**:

```json
{
  "nodes": ["node1", "node2", "...500 total..."],
  "count": 500,
  "truncated": true,
  "total_count": 1234
}
```

---

### `nodes.create`

Create a new node in Maya with optional name, parent, and initial attributes.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `node_type` | `string` | Yes | - | Type of node to create (e.g., "transform", "locator", "joint") |
| `name` | `string` | No | `null` | Desired node name (Maya may modify for uniqueness) |
| `parent` | `string` | No | `null` | Parent node to parent under |
| `attributes` | `object` | No | `null` | Initial attribute values to set after creation |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | Name of the created node |
| `node_type` | `string` | Type of node created |
| `parent` | `string \| null` | Parent node (if parented) |
| `attributes_set` | `string[]` | Attributes successfully set (if any) |
| `attribute_errors` | `object \| null` | Errors for attributes that failed to set |

**Example Request**:

```json
{
  "node_type": "transform",
  "name": "myLocator",
  "parent": "group1",
  "attributes": {
    "translateX": 10.0,
    "translateY": 5.0
  }
}
```

**Example Response**:

```json
{
  "node": "myLocator",
  "node_type": "transform",
  "parent": "group1",
  "attributes_set": ["translateX", "translateY"],
  "attribute_errors": null
}
```

**Supported Node Types**:

| Category | Types |
|----------|-------|
| DAG nodes | `transform`, `joint`, `locator`, `camera`, `light` |
| Shape nodes | `mesh`, `nurbsCurve`, `nurbsSurface` |
| DG nodes | `multiplyDivide`, `blendColors`, `condition` |

---

### `nodes.delete`

Delete one or more nodes from the Maya scene.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `nodes` | `string[]` | Yes | - | Node names to delete |
| `hierarchy` | `boolean` | No | `false` | Delete entire hierarchy below each node |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `deleted` | `string[]` | Nodes successfully deleted |
| `count` | `integer` | Number of nodes deleted |
| `errors` | `object \| null` | Map of node name to error message (for nodes that failed) |

**Example Request**:

```json
{
  "nodes": ["pCube1", "pSphere1"],
  "hierarchy": false
}
```

**Example Response**:

```json
{
  "deleted": ["pCube1", "pSphere1"],
  "count": 2,
  "errors": null
}
```

**Example Response (Partial Failure)**:

```json
{
  "deleted": ["pCube1"],
  "count": 1,
  "errors": {
    "pSphere1": "Node 'pSphere1' does not exist"
  }
}
```

**Notes**:
- Deleting a transform also deletes its shape nodes
- With `hierarchy: true`, all descendant nodes are also deleted
- Use `scene.undo` to recover accidentally deleted nodes

---

## Attribute Tools

### `attributes.get`

Get one or more attribute values from a node.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `node` | `string` | Yes | - | Node name to query |
| `attributes` | `string[]` | Yes | - | Attribute names to get (e.g., `["translateX", "visibility"]`) |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | Node name queried |
| `attributes` | `object` | Map of attribute name to value |
| `count` | `integer` | Number of attributes returned |
| `errors` | `object \| null` | Map of attribute name to error message (for attrs that failed) |

**Example Request**:

```json
{
  "node": "pCube1",
  "attributes": ["translateX", "translateY", "translateZ", "visibility"]
}
```

**Example Response**:

```json
{
  "node": "pCube1",
  "attributes": {
    "translateX": 0.0,
    "translateY": 5.0,
    "translateZ": -2.5,
    "visibility": true
  },
  "count": 4,
  "errors": null
}
```

**Example Response (Partial Failure)**:

```json
{
  "node": "pCube1",
  "attributes": {
    "translateX": 0.0,
    "translateY": 5.0
  },
  "count": 2,
  "errors": {
    "nonExistentAttr": "Attribute 'nonExistentAttr' not found on node 'pCube1'"
  }
}
```

**Supported Value Types**:

| Maya Type | JSON Type | Example |
|-----------|-----------|---------|
| `double`, `float` | `number` | `5.0` |
| `int`, `long`, `short` | `integer` | `42` |
| `bool` | `boolean` | `true` |
| `string` | `string` | `"hello"` |
| `enum` | `integer` | `2` (enum index) |
| `double3` (compound) | `[number, number, number]` | `[1.0, 2.0, 3.0]` |

---

### `attributes.set`

Set one or more attribute values on a node.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `node` | `string` | Yes | - | Node name to modify |
| `attributes` | `object` | Yes | - | Map of attribute name to value |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | Node name modified |
| `set` | `string[]` | Attributes successfully set |
| `count` | `integer` | Number of attributes set |
| `errors` | `object \| null` | Map of attribute name to error message (for attrs that failed) |

**Example Request**:

```json
{
  "node": "pCube1",
  "attributes": {
    "translateX": 10.0,
    "translateY": 5.0,
    "visibility": false
  }
}
```

**Example Response**:

```json
{
  "node": "pCube1",
  "set": ["translateX", "translateY", "visibility"],
  "count": 3,
  "errors": null
}
```

**Example Response (Partial Failure)**:

```json
{
  "node": "pCube1",
  "set": ["translateX", "translateY"],
  "count": 2,
  "errors": {
    "lockedAttr": "Attribute 'lockedAttr' is locked"
  }
}
```

**Common Transform Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `translateX`, `translateY`, `translateZ` | `number` | Position |
| `rotateX`, `rotateY`, `rotateZ` | `number` | Rotation (degrees) |
| `scaleX`, `scaleY`, `scaleZ` | `number` | Scale |
| `visibility` | `boolean` | Node visibility |
| `translate` | `[x, y, z]` | Compound position |
| `rotate` | `[x, y, z]` | Compound rotation |
| `scale` | `[x, y, z]` | Compound scale |

---

## Selection Tools

### `selection.get`

Get the current selection in Maya.

**Input**: None

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `selection` | `string[]` | List of selected node names |
| `count` | `integer` | Number of selected items |

**Example Response**:

```json
{
  "selection": ["pCube1", "pSphere1"],
  "count": 2
}
```

---

### `selection.set`

Set the Maya selection.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `nodes` | `string[]` | Yes | - | Node names to select |
| `add` | `boolean` | No | `false` | Add to existing selection |
| `deselect` | `boolean` | No | `false` | Remove from selection |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `selection` | `string[]` | New selection state |
| `count` | `integer` | Number of selected items |

**Example Request**:

```json
{
  "nodes": ["pCube1", "pCube2"],
  "add": false
}
```

**Example Response**:

```json
{
  "selection": ["pCube1", "pCube2"],
  "count": 2
}
```

---

### `selection.clear`

Clear the Maya selection (deselect all).

**Input**: None

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `selection` | `string[]` | Empty array |
| `count` | `integer` | 0 |

**Example Response**:

```json
{
  "selection": [],
  "count": 0
}
```

---

## Error Responses

All tools may return errors in a consistent format:

| Field | Type | Description |
|-------|------|-------------|
| `error` | `string` | Error type (e.g., "MayaUnavailableError") |
| `message` | `string` | Human-readable error message |
| `details` | `object \| null` | Additional error context |

**Example Error Response**:

```json
{
  "error": "MayaUnavailableError",
  "message": "Cannot connect to Maya commandPort at localhost:7001",
  "details": {
    "host": "localhost",
    "port": 7001,
    "attempts": 3
  }
}
```

## Tool Annotations

All tools include MCP annotations to help AI clients understand their behavior and make safe decisions.

### Annotation Types

| Annotation | Description |
|------------|-------------|
| `readOnlyHint` | Tool only reads data, doesn't modify Maya state |
| `destructiveHint` | Tool may make irreversible changes |
| `idempotentHint` | Calling multiple times has same effect as calling once |
| `openWorldHint` | Tool interacts with external systems (always `false` for Maya MCP) |

### Why Annotations Matter

**For AI Clients:**
- Read-only tools can be called without user confirmation
- Destructive tools should prompt for confirmation
- Idempotent tools can be safely retried on failure

**For Maya MCP:**
- All tools are `openWorldHint: false` (localhost-only, no external systems)
- Selection tools are not idempotent (state depends on prior state)
- No tools are destructive (Maya has undo for scene changes)

### Tool Annotation Table

| Tool | readOnlyHint | destructiveHint | idempotentHint |
|------|--------------|-----------------|----------------|
| `health.check` | true | false | true |
| `maya.connect` | false | false | true |
| `maya.disconnect` | false | false | true |
| `scene.info` | true | false | true |
| `scene.undo` | false | false | false |
| `scene.redo` | false | false | false |
| `nodes.list` | true | false | true |
| `nodes.create` | false | false | false |
| `nodes.delete` | false | false | true |
| `attributes.get` | true | false | true |
| `attributes.set` | false | false | true |
| `selection.get` | true | false | true |
| `selection.set` | false | false | false |
| `selection.clear` | false | false | true |

---

## Token Budget Considerations

Large Maya scenes can contain thousands of nodes. To prevent token budget explosion in AI clients, Maya MCP implements output limits.

### Default Limits

| Tool | Default Limit | Configurable |
|------|---------------|--------------|
| `nodes.list` | 500 nodes | Yes (`limit` param) |

### Handling Truncated Results

When results are truncated, the response includes additional fields:

```json
{
  "nodes": ["node1", "node2", "..."],
  "count": 500,
  "truncated": true,
  "total_count": 12345
}
```

**Best Practices for AI Clients:**
1. Check for `truncated: true` in responses
2. Use `pattern` or `node_type` filters to narrow results
3. Increase `limit` only when necessary (e.g., `limit: 1000`)
4. Use `limit: 0` with caution (unlimited results)
