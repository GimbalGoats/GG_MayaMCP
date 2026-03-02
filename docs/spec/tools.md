# Tool Specifications

This document specifies all MCP tools provided by Maya MCP.

## Tool Naming Convention

Tools use a hierarchical naming scheme:

- `health.*` - Health and diagnostics
- `maya.*` - Connection management
- `scene.*` - Scene-level operations (info, new, open, undo, redo)
- `nodes.*` - Node operations (list, create, delete, info)
- `attributes.*` - Attribute operations (get, set)
- `selection.*` - Selection management
- `modeling.*` - Polygon modeling operations
- `shading.*` - Material creation and assignment
- `skin.*` - Skinning and weight management

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

### `scene.new`

Create a new, empty Maya scene.

Checks whether the current scene has unsaved changes before proceeding. When `force` is `false` (default) and the scene has been modified, the operation is refused with an actionable error message. When `force` is `true`, unsaved changes are discarded.

**Important:** This tool never triggers Maya's interactive "Save changes?" dialog, which would block the commandPort indefinitely.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `force` | `boolean` | No | `false` | If true, discard unsaved changes. If false, refuse when scene is modified. |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Whether the new scene was created |
| `previous_file` | `string \| null` | File path of the previous scene |
| `was_modified` | `boolean` | Whether the previous scene had unsaved changes |
| `error` | `string \| null` | Error message if refused, or null |

**Example Response (Success)**:

```json
{
  "success": true,
  "previous_file": "C:/projects/myScene.ma",
  "was_modified": false,
  "error": null
}
```

**Example Response (Refused — Unsaved Changes)**:

```json
{
  "success": false,
  "previous_file": "C:/projects/myScene.ma",
  "was_modified": true,
  "error": "Scene has unsaved changes. Use force=True to discard changes, or save first."
}
```

**Example Response (Forced — Discards Changes)**:

```json
{
  "success": true,
  "previous_file": "C:/projects/myScene.ma",
  "was_modified": true,
  "error": null
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

### `scene.open`

Open a Maya scene file.

Checks whether the current scene has unsaved changes before proceeding. When `force` is `false` (default) and the scene has been modified, the operation is refused with an actionable error message. When `force` is `true`, unsaved changes are discarded.

**Important:** This tool never triggers Maya's interactive "Save changes?" dialog, which would block the commandPort indefinitely.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file_path` | `string` | Yes | - | Path to the scene file to open |
| `force` | `boolean` | No | `false` | If true, discard unsaved changes. If false, refuse when scene is modified. |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Whether the scene was opened |
| `file_path` | `string \| null` | Path of the opened scene file |
| `previous_file` | `string \| null` | File path of the previous scene |
| `was_modified` | `boolean` | Whether the previous scene had unsaved changes |
| `error` | `string \| null` | Error message if refused, or null |

**Example Request**:

```json
{
  "file_path": "C:/projects/myScene.ma",
  "force": false
}
```

**Example Response (Success)**:

```json
{
  "success": true,
  "file_path": "C:/projects/myScene.ma",
  "previous_file": "C:/projects/oldScene.ma",
  "was_modified": false,
  "error": null
}
```

**Example Response (Refused — Unsaved Changes)**:

```json
{
  "success": false,
  "file_path": null,
  "previous_file": "C:/projects/oldScene.ma",
  "was_modified": true,
  "error": "Scene has unsaved changes. Use force=True to discard changes, or save first."
}
```

**Example Response (Forced — Discards Changes)**:

```json
{
  "success": true,
  "file_path": "C:/projects/myScene.ma",
  "previous_file": "C:/projects/oldScene.ma",
  "was_modified": true,
  "error": null
}
```

**Security**:
- File paths are validated for shell metacharacters and control characters
- Only supported scene extensions are accepted (`.ma`, `.mb`, `.obj`, `.fbx`, `.abc`, `.usd`, `.usda`, `.usdc`, `.usdz`)
- File existence is verified before sending to Maya

---

### `scene.save`

Save the current Maya scene.

Saves the currently open scene file. If the scene is untitled (never saved), the operation is rejected with an error instructing to use `scene.save_as`.

**Input**: None

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Whether the scene was saved |
| `file_path` | `string \| null` | The saved file path (or None if failed) |
| `error` | `string \| null` | Error message if the operation failed, or null |

**Example Response (Success)**:

```json
{
  "success": true,
  "file_path": "C:/projects/myScene.ma",
  "error": null
}
```

**Example Response (Untitled Error)**:

```json
{
  "success": false,
  "file_path": null,
  "error": "Scene is untitled. Use scene.save_as to save for the first time."
}
```

---

### `scene.save_as`

Save the current scene to a new file path.

Renames the current scene and saves it to the specified path. The file type (Maya ASCII or Maya Binary) is inferred from the file extension (`.ma` or `.mb`).

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file_path` | `string` | Yes | - | Absolute or relative path to save the scene to. Supported extensions: `.ma`, `.mb`. |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Whether the scene was saved |
| `file_path` | `string \| null` | The new file path (or None if failed) |
| `error` | `string \| null` | Error message if the operation failed, or null |

**Example Request**:

```json
{
  "file_path": "C:/projects/newScene.ma"
}
```

**Example Response**:

```json
{
  "success": true,
  "file_path": "C:/projects/newScene.ma",
  "error": null
}
```

**Security**:
- File paths are validated for shell metacharacters and control characters
- Only supported scene extensions are accepted (`.ma`, `.mb`)

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

### `nodes.info`

Get comprehensive information about a Maya node in a single call. Reduces tool-call chaining by consolidating what would otherwise require multiple `attributes.get` and `nodes.list` calls.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `node` | `string` | Yes | - | Node name to query |
| `info_category` | `string` | No | `"summary"` | Category of information: `"summary"`, `"transform"`, `"hierarchy"`, `"attributes"`, `"shape"`, or `"all"` |

**Output** (varies by `info_category`):

**Common fields (always present)**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | The queried node name |
| `info_category` | `string` | The category requested |
| `exists` | `boolean` | Whether the node exists |
| `node_type` | `string` | Maya node type (if exists) |
| `errors` | `object \| null` | Error details if any queries failed |

**Category: `summary`**:

| Field | Type | Description |
|-------|------|-------------|
| `parent` | `string \| null` | Parent node name |
| `children_count` | `integer` | Number of direct children |

**Category: `transform`**:

| Field | Type | Description |
|-------|------|-------------|
| `translateX`, `translateY`, `translateZ` | `number` | Position components |
| `rotateX`, `rotateY`, `rotateZ` | `number` | Rotation components (degrees) |
| `scaleX`, `scaleY`, `scaleZ` | `number` | Scale components |
| `visibility` | `boolean` | Node visibility |
| `translate` | `[number, number, number]` | Compound position |
| `rotate` | `[number, number, number]` | Compound rotation |
| `scale` | `[number, number, number]` | Compound scale |

**Category: `hierarchy`**:

| Field | Type | Description |
|-------|------|-------------|
| `parent` | `string \| null` | Parent full DAG path (in standalone `hierarchy` mode) |
| `children` | `string[]` | Direct children names |
| `full_path` | `string` | Full DAG path of the node |

**Category: `attributes`**:

| Field | Type | Description |
|-------|------|-------------|
| `keyable_attributes` | `object` | Map of keyable/user-defined attribute name to value |
| `keyable_count` | `integer` | Number of keyable attributes returned |
| `keyable_truncated` | `boolean` | Present and `true` if attributes were truncated (max 200) |
| `keyable_total_count` | `integer` | Total keyable attributes before truncation (only if truncated) |

**Category: `shape`**:

| Field | Type | Description |
|-------|------|-------------|
| `shapes` | `object[]` | Array of shape info objects |
| `shapes[].name` | `string` | Shape node name |
| `shapes[].type` | `string` | Shape node type (e.g., "mesh") |
| `shapes[].connections_count` | `integer` | Number of connections |
| `shape_count` | `integer` | Number of shape nodes |

**Category: `all`**: Returns all fields from all categories combined. Note: to avoid key collision, `parent` contains the short name (from summary) and `parent_full_path` contains the full DAG path (from hierarchy).

**Example Request (summary)**:

```json
{
  "node": "pCube1",
  "info_category": "summary"
}
```

**Example Response (summary)**:

```json
{
  "node": "pCube1",
  "info_category": "summary",
  "exists": true,
  "node_type": "transform",
  "parent": "group1",
  "children_count": 1,
  "errors": null
}
```

**Example Request (transform)**:

```json
{
  "node": "pCube1",
  "info_category": "transform"
}
```

**Example Response (transform)**:

```json
{
  "node": "pCube1",
  "info_category": "transform",
  "exists": true,
  "node_type": "transform",
  "translateX": 10.0,
  "translateY": 5.0,
  "translateZ": 0.0,
  "rotateX": 0.0,
  "rotateY": 45.0,
  "rotateZ": 0.0,
  "scaleX": 1.0,
  "scaleY": 1.0,
  "scaleZ": 1.0,
  "visibility": true,
  "translate": [10.0, 5.0, 0.0],
  "rotate": [0.0, 45.0, 0.0],
  "scale": [1.0, 1.0, 1.0],
  "errors": null
}
```

**Example Response (non-existent node)**:

```json
{
  "node": "nonexistent",
  "info_category": "summary",
  "exists": false,
  "errors": {
    "_node": "Node 'nonexistent' does not exist"
  }
}
```

**Notes**:
- Use `summary` for a quick overview before making changes
- Use `transform` instead of multiple `attributes.get` calls for position/rotation/scale
- Use `all` to get everything at once (response may be large for complex nodes)
- Response size guard applies to `attributes` and `all` categories

---

### `nodes.rename`

Rename one or more nodes in the Maya scene.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `mapping` | `object` | Yes | - | Map of current node name to new name |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `renamed` | `object` | Map of original name to actual new name |
| `errors` | `object \| null` | Map of original name to error message (for failures) |

**Example Request**:

```json
{
  "mapping": {
    "pCube1": "myCube",
    "pSphere1": "mySphere"
  }
}
```

**Example Response**:

```json
{
  "renamed": {
    "pCube1": "myCube",
    "pSphere1": "mySphere1"
  },
  "errors": null
}
```

**Example Response (Partial Failure)**:

```json
{
  "renamed": {
    "pCube1": "myCube"
  },
  "errors": {
    "pSphere1": "Node 'pSphere1' does not exist"
  }
}
```

---
### `nodes.parent`

Reparent one or more nodes in the Maya hierarchy.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `nodes` | `string[]` | Yes | - | Nodes to reparent |
| `parent` | `string \| null` | No | `null` | New parent node. If null, unparent (parent to world). |
| `relative` | `boolean` | No | `false` | Preserve existing local transformations |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `parented` | `string[]` | Nodes successfully reparented |
| `count` | `integer` | Number of nodes reparented |
| `errors` | `object \| null` | Map of node name to error message |

**Example Request (Parent to group)**:

```json
{
  "nodes": ["pCube1", "pSphere1"],
  "parent": "group1"
}
```

**Example Request (Unparent)**:

```json
{
  "nodes": ["pCube1"],
  "parent": null
}
```

**Example Response**:

```json
{
  "parented": ["pCube1", "pSphere1"],
  "count": 2,
  "errors": null
}
```

---

### `nodes.duplicate`

Duplicate one or more nodes.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `nodes` | `string[]` | Yes | - | Nodes to duplicate |
| `name` | `string` | No | `null` | Name for the new node (only valid when duplicating single node) |
| `input_connections` | `boolean` | No | `false` | Duplicate input connections |
| `upstream_nodes` | `boolean` | No | `false` | Duplicate upstream nodes |
| `parent_only` | `boolean` | No | `false` | Duplicate only the specified node, not its children |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `duplicated` | `object` | Map of original name to new name |
| `count` | `integer` | Number of nodes duplicated |
| `errors` | `object \| null` | Map of original name to error message |

**Example Request**:

```json
{
  "nodes": ["pCube1"],
  "input_connections": false
}
```

**Example Response**:

```json
{
  "duplicated": {
    "pCube1": "pCube2"
  },
  "count": 1,
  "errors": null
}
```

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

## Connection Tools

### `connections.list`

List connections on a Maya node with direction and type filters.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `node` | `string` | Yes | - | Node name to query connections for |
| `direction` | `string` | No | `"both"` | Filter by direction: `"incoming"`, `"outgoing"`, or `"both"` |
| `connections_type` | `string` | No | `null` | Filter by connection type (e.g., `"animCurve"`, `"shader"`) |
| `limit` | `integer` | No | `500` | Max connections to return. Use 0 for unlimited. |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | The queried node name |
| `connections` | `array` | List of connection info objects |
| `connections[].source` | `string` | Source plug (node.attribute) |
| `connections[].source_node` | `string` | Source node name |
| `connections[].source_type` | `string` | Source node type |
| `connections[].destination` | `string` | Destination plug (node.attribute) |
| `connections[].destination_node` | `string` | Destination node name |
| `connections[].destination_type` | `string` | Destination node type |
| `connections[].direction` | `string` | `"incoming"` or `"outgoing"` |
| `count` | `integer` | Number of connections returned |
| `truncated` | `boolean` | True if results were truncated (only if limit hit) |
| `total_count` | `integer` | Total connections before limit (only if truncated) |

**Example Request**:

```json
{
  "node": "pCube1",
  "direction": "incoming"
}
```

**Example Response**:

```json
{
  "node": "pCube1",
  "connections": [
    {
      "source": "polyCube1.output",
      "source_node": "polyCube1",
      "source_type": "polyCube",
      "destination": "pCubeShape1.inMesh",
      "destination_node": "pCubeShape1",
      "destination_type": "mesh",
      "direction": "incoming"
    }
  ],
  "count": 1,
  "errors": null
}
```

---

### `connections.get`

Get detailed connection information for specific attributes on a node.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `node` | `string` | Yes | - | Node name to query |
| `attributes` | `string[]` | No | `null` | Attribute names to check. If null, checks all connectable attributes. |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | The queried node name |
| `attributes` | `object` | Map of attribute name to connection info |
| `attributes[].attribute` | `string` | Attribute name |
| `attributes[].connected` | `boolean` | Whether the attribute has connections |
| `attributes[].connections` | `array` | List of connection details |
| `attributes[].locked` | `boolean` | Whether the attribute is locked |
| `attributes[].type` | `string` | Attribute type |
| `count` | `integer` | Number of attributes with connections |
| `errors` | `object \| null` | Map of attribute to error message |

**Example Request**:

```json
{
  "node": "pCube1",
  "attributes": ["translateX", "visibility"]
}
```

**Example Response**:

```json
{
  "node": "pCube1",
  "attributes": {
    "translateX": {
      "attribute": "translateX",
      "connected": true,
      "connections": [
        {
          "source": "animCurveTL1.output",
          "source_node": "animCurveTL1",
          "source_type": "animCurveTL",
          "destination": "pCube1.translateX",
          "direction": "incoming"
        }
      ],
      "locked": false,
      "type": "double"
    },
    "visibility": {
      "attribute": "visibility",
      "connected": false,
      "connections": [],
      "locked": false,
      "type": "bool"
    }
  },
  "count": 1,
  "errors": null
}
```

---

### `connections.connect`

Connect two attributes in Maya. Implements the disconnect-before-reconnect safety pattern.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `source` | `string` | Yes | - | Source plug in `"node.attribute"` format |
| `destination` | `string` | Yes | - | Destination plug in `"node.attribute"` format |
| `force` | `boolean` | No | `false` | If true, disconnect existing connections to destination first |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `connected` | `boolean` | Whether the connection was created |
| `source` | `string` | The source plug |
| `destination` | `string` | The destination plug |
| `disconnected` | `string[]` | Plugs that were disconnected (if force=true) |
| `error` | `string \| null` | Error message if failed |

**Example Request**:

```json
{
  "source": "ramp1.outColor",
  "destination": "lambert1.color",
  "force": true
}
```

**Example Response**:

```json
{
  "connected": true,
  "source": "ramp1.outColor",
  "destination": "lambert1.color",
  "disconnected": ["checker1.outColor"],
  "error": null
}
```

**Example Response (Already Connected)**:

```json
{
  "connected": false,
  "source": "ramp1.outColor",
  "destination": "lambert1.color",
  "disconnected": [],
  "error": "Destination 'lambert1.color' is already connected to 'checker1.outColor'. Use force=True to replace."
}
```

---

### `connections.disconnect`

Disconnect attributes in Maya. Can disconnect a specific connection, all outgoing from a source, or all incoming to a destination.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `source` | `string` | No | `null` | Source plug. If null, uses destination only. |
| `destination` | `string` | No | `null` | Destination plug. If null, uses source only. |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `disconnected` | `array` | List of disconnected connection objects |
| `disconnected[].source` | `string` | Source plug that was disconnected |
| `disconnected[].destination` | `string` | Destination plug that was disconnected |
| `count` | `integer` | Number of connections disconnected |
| `error` | `string \| null` | Error message if failed |

**Example Request (Specific Connection)**:

```json
{
  "source": "ramp1.outColor",
  "destination": "lambert1.color"
}
```

**Example Response**:

```json
{
  "disconnected": [
    {
      "source": "ramp1.outColor",
      "destination": "lambert1.color"
    }
  ],
  "count": 1,
  "error": null
}
```

**Example Request (All Incoming)**:

```json
{
  "destination": "pCube1.translateX"
}
```

**Example Response**:

```json
{
  "disconnected": [
    {
      "source": "animCurveTL1.output",
      "destination": "pCube1.translateX"
    }
  ],
  "count": 1,
  "error": null
}
```

---

### `connections.history`

List construction/deformation history on a node. Traverses upstream (input) or downstream (output) dependency graph.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `node` | `string` | Yes | - | Node name to query history for |
| `direction` | `string` | No | `"input"` | Direction: `"input"` (upstream), `"output"` (downstream), or `"both"` |
| `depth` | `integer` | No | `10` | Maximum traversal depth (max 50) |
| `limit` | `integer` | No | `500` | Max history nodes to return. Use 0 for unlimited. |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | The queried node name |
| `history` | `array` | List of history node info objects |
| `history[].name` | `string` | History node name |
| `history[].type` | `string` | History node type |
| `history[].depth` | `integer` | Depth from the queried node |
| `history[].direction` | `string` | `"input"` or `"output"` |
| `count` | `integer` | Number of history nodes returned |
| `truncated` | `boolean` | True if results were truncated |
| `total_count` | `integer` | Total history nodes before limit |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "node": "pCubeShape1",
  "direction": "input",
  "depth": 5
}
```

**Example Response**:

```json
{
  "node": "pCubeShape1",
  "history": [
    {
      "name": "polyCube1",
      "type": "polyCube",
      "depth": 1,
      "direction": "input"
    },
    {
      "name": "polyExtrudeFace1",
      "type": "polyExtrudeFace",
      "depth": 2,
      "direction": "input"
    },
    {
      "name": "tweak1",
      "type": "tweak",
      "depth": 3,
      "direction": "input"
    }
  ],
  "count": 3,
  "errors": null
}
```

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

## Mesh Tools

Mesh tools provide geometry queries and topology analysis for polygon meshes.

### `mesh.info`

Get mesh statistics: vertex/face/edge counts, bounding box, UV status.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `node` | `string` | Yes | - | Name of the mesh node (transform or shape) |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | The queried node name |
| `exists` | `boolean` | Whether the node exists |
| `is_mesh` | `boolean` | Whether the node is a mesh |
| `shape` | `string` | Shape node name (if mesh) |
| `vertex_count` | `integer` | Number of vertices |
| `face_count` | `integer` | Number of faces |
| `edge_count` | `integer` | Number of edges |
| `uv_count` | `integer` | Number of UV coordinates |
| `has_uvs` | `boolean` | Whether the mesh has UVs |
| `uv_sets` | `string[]` | List of UV set names |
| `bounding_box` | `[number, number, number, number, number, number]` | Bounding box as [min_x, min_y, min_z, max_x, max_y, max_z] |
| `errors` | `object \| null` | Error details if any queries failed |

**Example Request**:

```json
{
  "node": "pCube1"
}
```

**Example Response**:

```json
{
  "node": "pCube1",
  "exists": true,
  "is_mesh": true,
  "shape": "pCubeShape1",
  "vertex_count": 8,
  "face_count": 6,
  "edge_count": 12,
  "uv_count": 8,
  "has_uvs": true,
  "uv_sets": ["map1"],
  "bounding_box": [-0.5, -0.5, -0.5, 0.5, 0.5, 0.5],
  "errors": null
}
```

---

### `mesh.vertices`

Query vertex positions from a mesh with offset/limit pagination.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `node` | `string` | Yes | - | Name of the mesh node (transform or shape) |
| `offset` | `integer` | No | `0` | Starting vertex index (0-based) |
| `limit` | `integer` | No | `1000` | Maximum vertices to return. Use 0 for unlimited. |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | The queried node name |
| `exists` | `boolean` | Whether the node exists |
| `is_mesh` | `boolean` | Whether the node is a mesh |
| `vertex_count` | `integer` | Total number of vertices in mesh |
| `vertices` | `array` | List of [x, y, z] position arrays |
| `offset` | `integer` | The offset used |
| `count` | `integer` | Number of vertices returned |
| `truncated` | `boolean` | True if results were truncated (only if limit hit) |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "node": "pCube1",
  "offset": 0,
  "limit": 100
}
```

**Example Response**:

```json
{
  "node": "pCube1",
  "exists": true,
  "is_mesh": true,
  "vertex_count": 8,
  "vertices": [
    [-0.5, -0.5, -0.5],
    [0.5, -0.5, -0.5],
    [0.5, 0.5, -0.5],
    [-0.5, 0.5, -0.5],
    [-0.5, 0.5, 0.5],
    [0.5, 0.5, 0.5],
    [0.5, -0.5, 0.5],
    [-0.5, -0.5, 0.5]
  ],
  "offset": 0,
  "count": 8,
  "errors": null
}
```

---

### `mesh.evaluate`

Analyze mesh topology for issues: non-manifold edges, lamina faces, holes, and border edges.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `node` | `string` | Yes | - | Name of the mesh node (transform or shape) |
| `checks` | `string[]` | No | `["non_manifold", "lamina", "holes", "border"]` | List of checks to perform |
| `limit` | `integer` | No | `500` | Max components to return per check. Use 0 for unlimited. |

**Valid Check Types**:

| Check | Description |
|-------|-------------|
| `non_manifold` | Find non-manifold edges (edges shared by more than 2 faces) |
| `lamina` | Find lamina faces (faces that share all edges with another face) |
| `holes` | Find edges bordering holes in the mesh |
| `border` | Find border edges (edges with only one adjacent face) |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | The queried node name |
| `exists` | `boolean` | Whether the node exists |
| `is_mesh` | `boolean` | Whether the node is a mesh |
| `is_clean` | `boolean` | True if mesh has no topology issues (excludes borders) |
| `non_manifold_edges` | `string[]` | List of non-manifold edge names (if checked) |
| `non_manifold_count` | `integer` | Count of non-manifold edges |
| `lamina_faces` | `string[]` | List of lamina face names (if checked) |
| `lamina_count` | `integer` | Count of lamina faces |
| `holes` | `string[]` | List of edges bordering holes (if checked) |
| `hole_count` | `integer` | Count of hole-bordering edges |
| `border_edges` | `string[]` | List of border edge names (if checked) |
| `border_count` | `integer` | Count of border edges |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "node": "pCube1",
  "checks": ["non_manifold", "holes"]
}
```

**Example Response (Clean Mesh)**:

```json
{
  "node": "pCube1",
  "exists": true,
  "is_mesh": true,
  "is_clean": true,
  "non_manifold_edges": [],
  "non_manifold_count": 0,
  "holes": [],
  "hole_count": 0,
  "errors": null
}
```

**Example Response (Mesh with Issues)**:

```json
{
  "node": "badMesh",
  "exists": true,
  "is_mesh": true,
  "is_clean": false,
  "non_manifold_edges": ["badMeshShape.e[5]", "badMeshShape.e[6]"],
  "non_manifold_count": 2,
  "lamina_faces": [],
  "lamina_count": 0,
  "holes": ["badMeshShape.e[10]"],
  "hole_count": 1,
  "border_edges": [],
  "border_count": 0,
  "errors": null
}
```

---

## Component Selection Tools

Component selection tools provide vertex, edge, and face selection operations.

### `selection.set_components`

Select mesh components (vertices, edges, or faces) using Maya notation.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `components` | `string[]` | Yes | - | Component specifications in Maya notation |
| `add` | `boolean` | No | `false` | Add to existing selection |
| `deselect` | `boolean` | No | `false` | Remove from selection |

**Component Notation Examples**:

| Notation | Description |
|----------|-------------|
| `pCube1.vtx[0]` | Single vertex |
| `pCube1.vtx[0:10]` | Vertex range (0 through 10) |
| `pCube1.vtx[0:10:2]` | Vertex range with step (0, 2, 4, 6, 8, 10) |
| `pCube1.e[5]` | Single edge |
| `pCube1.e[0:99]` | Edge range |
| `pCube1.f[0]` | Single face |
| `pCube1.f[0:99]` | Face range |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `selection` | `string[]` | List of currently selected components |
| `count` | `integer` | Number of selected components |
| `errors` | `object \| null` | Map of component to error message |

**Example Request**:

```json
{
  "components": ["pCube1.vtx[0:7]"]
}
```

**Example Response**:

```json
{
  "selection": [
    "pCube1.vtx[0]",
    "pCube1.vtx[1]",
    "pCube1.vtx[2]",
    "pCube1.vtx[3]",
    "pCube1.vtx[4]",
    "pCube1.vtx[5]",
    "pCube1.vtx[6]",
    "pCube1.vtx[7]"
  ],
  "count": 8,
  "errors": null
}
```

---

### `selection.get_components`

Get the currently selected mesh components grouped by type.

**Input**: None

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `selection` | `string[]` | List of all selected components (flattened) |
| `vertices` | `string[]` | List of selected vertex specifications |
| `edges` | `string[]` | List of selected edge specifications |
| `faces` | `string[]` | List of selected face specifications |
| `vertex_count` | `integer` | Number of selected vertices |
| `edge_count` | `integer` | Number of selected edges |
| `face_count` | `integer` | Number of selected faces |
| `total_count` | `integer` | Total number of selected components |
| `has_components` | `boolean` | True if any components are selected |

**Example Response**:

```json
{
  "selection": ["pCube1.vtx[0]", "pCube1.vtx[1]", "pCube1.e[5]"],
  "vertices": ["pCube1.vtx[0]", "pCube1.vtx[1]"],
  "edges": ["pCube1.e[5]"],
  "faces": [],
  "vertex_count": 2,
  "edge_count": 1,
  "face_count": 0,
  "total_count": 3,
  "has_components": true
}
```

---

### `selection.convert_components`

Convert the current selection to a different component type.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `to_type` | `string` | Yes | - | Target component type: `"vertex"`, `"edge"`, or `"face"` |
| `nodes` | `string[]` | No | `null` | Nodes to convert. If null, uses current selection. |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `selection` | `string[]` | List of converted components |
| `to_type` | `string` | The target component type |
| `count` | `integer` | Number of converted components |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "to_type": "face"
}
```

**Example Response**:

```json
{
  "selection": ["pCube1.f[0]", "pCube1.f[1]", "pCube1.f[2]", "pCube1.f[3]"],
  "to_type": "face",
  "count": 4,
  "errors": null
}
```

---

## Modeling Tools

Polygon modeling tools provide geometry creation, topology editing, and cleanup operations.

### `modeling.create_polygon_primitive`

Create a polygon primitive (cube, sphere, cylinder, cone, torus, plane) with configurable dimensions, subdivisions, and axis.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `primitive_type` | `"cube" \| "sphere" \| "cylinder" \| "cone" \| "torus" \| "plane"` | Yes | - | Type of primitive to create |
| `name` | `string` | No | `null` | Optional name for the transform node |
| `width` | `number` | No | `1.0` | Width (cube, plane) |
| `height` | `number` | No | `1.0` | Height (cube, cylinder, cone, plane) |
| `depth` | `number` | No | `1.0` | Depth (cube) |
| `radius` | `number` | No | `0.5` | Radius (sphere, cylinder, cone, torus) |
| `subdivisions_width` | `integer` | No | `null` | Width subdivisions |
| `subdivisions_height` | `integer` | No | `null` | Height subdivisions |
| `subdivisions_depth` | `integer` | No | `null` | Depth subdivisions |
| `subdivisions_axis` | `integer` | No | `null` | Axis subdivisions (sphere, cylinder, cone, torus) |
| `axis` | `"x" \| "y" \| "z"` | No | `"y"` | Up axis for the primitive |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `transform` | `string` | Name of the created transform node |
| `shape` | `string` | Name of the mesh shape node |
| `constructor_node` | `string` | Name of the constructor/history node |
| `primitive_type` | `string` | The primitive type that was created |
| `vertex_count` | `integer` | Number of vertices |
| `face_count` | `integer` | Number of faces |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "primitive_type": "cube",
  "name": "myCube",
  "width": 2.0,
  "height": 3.0,
  "depth": 1.5
}
```

**Example Response**:

```json
{
  "transform": "myCube",
  "shape": "myCubeShape",
  "constructor_node": "polyCube1",
  "primitive_type": "cube",
  "vertex_count": 8,
  "face_count": 6,
  "errors": null
}
```

---

### `modeling.extrude_faces`

Extrude polygon faces with local translation, offset, and division options.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `faces` | `string[]` | Yes | - | Face components to extrude (e.g., `["pCube1.f[0]", "pCube1.f[2]"]`) |
| `local_translate_z` | `number` | No | `null` | Local Z translation (extrusion thickness) |
| `local_translate_x` | `number` | No | `null` | Local X translation |
| `local_translate_y` | `number` | No | `null` | Local Y translation |
| `offset` | `number` | No | `null` | Offset amount for the extrusion |
| `divisions` | `integer` | No | `1` | Number of extrusion divisions |
| `keep_faces_together` | `boolean` | No | `true` | Keep faces together during extrusion |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | Result node name |
| `faces_extruded` | `integer` | Number of faces that were extruded |
| `new_face_count` | `integer` | Total face count after extrusion |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "faces": ["pCube1.f[0]"],
  "local_translate_z": 1.5,
  "divisions": 2
}
```

**Example Response**:

```json
{
  "node": "polyExtrudeFace1",
  "faces_extruded": 1,
  "new_face_count": 13,
  "errors": null
}
```

---

### `modeling.boolean`

Perform a boolean operation (union, difference, intersection) on two meshes.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `mesh_a` | `string` | Yes | - | First mesh (the base) |
| `mesh_b` | `string` | Yes | - | Second mesh (the operand) |
| `operation` | `"union" \| "difference" \| "intersection"` | No | `"union"` | Boolean operation type |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `result_mesh` | `string` | Name of the resulting mesh |
| `operation` | `string` | The operation that was performed |
| `vertex_count` | `integer` | Vertex count of result |
| `face_count` | `integer` | Face count of result |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "mesh_a": "pCube1",
  "mesh_b": "pSphere1",
  "operation": "difference"
}
```

**Example Response**:

```json
{
  "result_mesh": "pCube1",
  "operation": "difference",
  "vertex_count": 142,
  "face_count": 280,
  "errors": null
}
```

---

### `modeling.combine`

Combine multiple meshes into a single mesh.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `meshes` | `string[]` | Yes | - | List of mesh names to combine (minimum 2) |
| `name` | `string` | No | `null` | Optional name for the combined mesh |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `result_mesh` | `string` | Name of the combined mesh |
| `source_meshes` | `string[]` | List of source mesh names |
| `vertex_count` | `integer` | Total vertex count |
| `face_count` | `integer` | Total face count |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "meshes": ["pCube1", "pSphere1", "pCylinder1"],
  "name": "combinedMesh"
}
```

**Example Response**:

```json
{
  "result_mesh": "combinedMesh",
  "source_meshes": ["pCube1", "pSphere1", "pCylinder1"],
  "vertex_count": 450,
  "face_count": 448,
  "errors": null
}
```

---

### `modeling.separate`

Separate a combined mesh into individual meshes.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `mesh` | `string` | Yes | - | Name of the mesh to separate |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `source_mesh` | `string` | Original mesh name |
| `result_meshes` | `string[]` | List of separated mesh names |
| `count` | `integer` | Number of resulting meshes |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "mesh": "combinedMesh"
}
```

**Example Response**:

```json
{
  "source_mesh": "combinedMesh",
  "result_meshes": ["combinedMesh", "polySurface2", "polySurface3"],
  "count": 3,
  "errors": null
}
```

---

### `modeling.merge_vertices`

Merge vertices on a mesh within a distance threshold.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `mesh` | `string` | Yes | - | Name of the mesh |
| `threshold` | `number` | No | `0.001` | Distance threshold for merging |
| `vertices` | `string[]` | No | `null` | Specific vertex components to merge. If null, merges all. |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `mesh` | `string` | The mesh name |
| `vertices_merged` | `integer` | Number of vertices merged |
| `vertex_count_before` | `integer` | Vertex count before merge |
| `vertex_count_after` | `integer` | Vertex count after merge |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "mesh": "combinedMesh",
  "threshold": 0.01
}
```

**Example Response**:

```json
{
  "mesh": "combinedMesh",
  "vertices_merged": 8,
  "vertex_count_before": 16,
  "vertex_count_after": 8,
  "errors": null
}
```

---

### `modeling.bevel`

Bevel edges or vertices with offset, segments, and fraction options.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `components` | `string[]` | Yes | - | Edge or vertex components to bevel (e.g., `["pCube1.e[0:3]"]`) |
| `offset` | `number` | No | `0.5` | Bevel offset distance |
| `segments` | `integer` | No | `1` | Number of bevel segments |
| `fraction` | `number` | No | `0.5` | Bevel fraction |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | Result node name |
| `components_beveled` | `integer` | Number of components that were beveled |
| `new_vertex_count` | `integer` | Vertex count after bevel |
| `new_face_count` | `integer` | Face count after bevel |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "components": ["pCube1.e[0:3]"],
  "offset": 0.2,
  "segments": 2
}
```

**Example Response**:

```json
{
  "node": "polyBevel1",
  "components_beveled": 4,
  "new_vertex_count": 24,
  "new_face_count": 14,
  "errors": null
}
```

---

### `modeling.bridge`

Bridge between edge loops to create connecting faces.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `edge_loops` | `string[]` | Yes | - | Edge components for the edge loops to bridge |
| `divisions` | `integer` | No | `0` | Number of divisions in the bridge |
| `twist` | `integer` | No | `0` | Twist amount |
| `taper` | `number` | No | `1.0` | Taper amount |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | Result node name |
| `new_face_count` | `integer` | Face count after bridge |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "edge_loops": ["pCube1.e[4:7]", "pCube1.e[8:11]"],
  "divisions": 2
}
```

**Example Response**:

```json
{
  "node": "polyBridgeEdge1",
  "new_face_count": 18,
  "errors": null
}
```

---

### `modeling.insert_edge_loop`

Insert an edge loop at the specified edge using polySplitRing.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `edge` | `string` | Yes | - | Single edge component (e.g., `"pCube1.e[4]"`) |
| `divisions` | `integer` | No | `1` | Number of edge loops to insert |
| `weight` | `number` | No | `0.5` | Position weight along the edge (0-1) |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | Result node name |
| `edge` | `string` | The edge component that was used |
| `new_edge_count` | `integer` | Total edge count after insert |
| `new_vertex_count` | `integer` | Total vertex count after insert |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "edge": "pCube1.e[4]",
  "weight": 0.3
}
```

**Example Response**:

```json
{
  "node": "polySplitRing1",
  "edge": "pCube1.e[4]",
  "new_edge_count": 16,
  "new_vertex_count": 12,
  "errors": null
}
```

---

### `modeling.delete_faces`

Delete polygon faces from a mesh.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `faces` | `string[]` | Yes | - | Face components to delete (e.g., `["pCube1.f[0]", "pCube1.f[3]"]`) |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `faces_deleted` | `integer` | Number of faces deleted |
| `mesh` | `string` | The mesh node name |
| `remaining_face_count` | `integer` | Face count after deletion |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "faces": ["pCube1.f[0]", "pCube1.f[5]"]
}
```

**Example Response**:

```json
{
  "faces_deleted": 2,
  "mesh": "pCube1",
  "remaining_face_count": 4,
  "errors": null
}
```

---

### `modeling.move_components`

Move mesh components (vertices, edges, faces) by relative translation or to an absolute position.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `components` | `string[]` | Yes | - | Component strings to move (e.g., `["pCube1.vtx[0:3]"]`) |
| `translate` | `[number, number, number]` | No | `null` | Relative [x, y, z] translation (mutually exclusive with `absolute`) |
| `absolute` | `[number, number, number]` | No | `null` | Absolute [x, y, z] position (mutually exclusive with `translate`) |
| `world_space` | `boolean` | No | `true` | Use world space coordinates |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `components_moved` | `integer` | Number of components moved |
| `translate` or `absolute` | `[number, number, number]` | The translation/position values used |
| `world_space` | `boolean` | Whether world space was used |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "components": ["pCube1.vtx[0:3]"],
  "translate": [0, 1.5, 0]
}
```

**Example Response**:

```json
{
  "components_moved": 4,
  "translate": [0, 1.5, 0],
  "world_space": true,
  "errors": null
}
```

---

### `modeling.freeze_transforms`

Freeze (reset) transforms on nodes, applying current values as identity.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `nodes` | `string[]` | Yes | - | Node names to freeze transforms on |
| `translate` | `boolean` | No | `true` | Freeze translation |
| `rotate` | `boolean` | No | `true` | Freeze rotation |
| `scale` | `boolean` | No | `true` | Freeze scale |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `frozen` | `string[]` | List of nodes that were frozen |
| `count` | `integer` | Number of nodes frozen |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "nodes": ["pCube1", "pSphere1"]
}
```

**Example Response**:

```json
{
  "frozen": ["pCube1", "pSphere1"],
  "count": 2,
  "errors": null
}
```

---

### `modeling.delete_history`

Delete construction history from nodes or the entire scene.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `nodes` | `string[]` | No | `null` | Node names to delete history from |
| `all_nodes` | `boolean` | No | `false` | If true, delete history from all nodes in the scene |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `cleaned` | `string[]` | List of nodes that were cleaned |
| `count` | `integer` | Number of nodes cleaned |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "nodes": ["pCube1"]
}
```

**Example Response**:

```json
{
  "cleaned": ["pCube1"],
  "count": 1,
  "errors": null
}
```

**Example Request (All Nodes)**:

```json
{
  "all_nodes": true
}
```

---

### `modeling.center_pivot`

Center the pivot point on nodes.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `nodes` | `string[]` | Yes | - | Node names to center pivots on |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `centered` | `string[]` | List of nodes where pivots were centered |
| `count` | `integer` | Number of nodes processed |
| `pivot_positions` | `object` | Map of node name to pivot position [x, y, z] |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "nodes": ["pCube1"]
}
```

**Example Response**:

```json
{
  "centered": ["pCube1"],
  "count": 1,
  "pivot_positions": {
    "pCube1": [0.0, 0.5, 0.0]
  },
  "errors": null
}
```

---

### `modeling.set_pivot`

Set the pivot point of a node to an explicit position.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `node` | `string` | Yes | - | Node name to set pivot on |
| `position` | `[number, number, number]` | Yes | - | [x, y, z] position for the pivot |
| `world_space` | `boolean` | No | `true` | Position is in world space |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `node` | `string` | The node name |
| `pivot` | `[number, number, number]` | The actual pivot position set |
| `world_space` | `boolean` | Whether world space was used |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "node": "pCube1",
  "position": [0, 0, 0],
  "world_space": true
}
```

**Example Response**:

```json
{
  "node": "pCube1",
  "pivot": [0.0, 0.0, 0.0],
  "world_space": true,
  "errors": null
}
```

---

## Shading Tools

Shading tools provide material creation, assignment, and color management for shading workflows.

**Workflow-first**: `shading.create_material` consolidates 4 internal Maya steps (createNode material, createNode shadingGroup, connectAttr outColor, connectAttr dagSetMembers) into a single tool call.

### `shading.create_material`

Create a material (lambert, blinn, phong, standardSurface) with an associated shading group and optional color.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `material_type` | `"lambert" \| "blinn" \| "phong" \| "standardSurface"` | No | `"lambert"` | Type of material shader to create |
| `name` | `string` | No | `null` | Optional name for the material node |
| `color` | `[number, number, number]` | No | `null` | Optional [r, g, b] color values (0-1 range) |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `material` | `string` | Name of the created material node |
| `shading_group` | `string` | Name of the created shading group |
| `material_type` | `string` | The material type that was created |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "material_type": "blinn",
  "name": "redMetal",
  "color": [0.8, 0.1, 0.1]
}
```

**Example Response**:

```json
{
  "material": "redMetal",
  "shading_group": "redMetalSG",
  "material_type": "blinn",
  "errors": null
}
```

---

### `shading.assign_material`

Assign a material to meshes or face components. Resolves the shading group from the material automatically.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `targets` | `string[]` | Yes | - | Mesh names or face component strings to assign material to |
| `material` | `string` | Yes | - | Name of the material (or shading group) to assign |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `assigned` | `string[]` | List of targets that were successfully assigned |
| `material` | `string` | The material node name |
| `shading_group` | `string` | The shading group that was assigned |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "targets": ["pCube1", "pSphere1"],
  "material": "redMetal"
}
```

**Example Response**:

```json
{
  "assigned": ["pCube1", "pSphere1"],
  "material": "redMetal",
  "shading_group": "redMetalSG",
  "errors": null
}
```

**Example Request (Per-Face Assignment)**:

```json
{
  "targets": ["pCube1.f[0:2]"],
  "material": "redMetal"
}
```

---

### `shading.set_material_color`

Set a color attribute on a material (e.g., color, baseColor, transparency).

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `material` | `string` | Yes | - | Name of the material node |
| `color` | `[number, number, number]` | Yes | - | [r, g, b] color values (0-1 range) |
| `attribute` | `string` | No | `"color"` | Color attribute name (e.g., `"color"`, `"baseColor"`, `"transparency"`, `"incandescence"`) |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `material` | `string` | The material node name |
| `attribute` | `string` | The attribute that was set |
| `color` | `[number, number, number]` | The color values that were set |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "material": "redMetal",
  "color": [0.2, 0.4, 0.8],
  "attribute": "color"
}
```

**Example Response**:

```json
{
  "material": "redMetal",
  "attribute": "color",
  "color": [0.2, 0.4, 0.8],
  "errors": null
}
```

---

## Skinning Tools

Skinning tools provide skin binding, weight management, and weight transfer for character rigging workflows.

**Token budget**: Skin weight data can reach 4-15MB for production meshes (100K vertices x ~4 influences). `skin.weights.get` uses offset/limit pagination with a default limit of 100 vertices. The 50KB response guard applies.

### `skin.bind`

Bind a mesh to a skeleton with influence options. Creates a skinCluster.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `mesh` | `string` | Yes | - | Name of the mesh to bind |
| `joints` | `string[]` | Yes | - | List of joint names to use as influences |
| `max_influences` | `integer` | No | `4` | Maximum influences per vertex |
| `bind_method` | `string` | No | `"closestDistance"` | Binding algorithm: `"closestDistance"`, `"heatMap"`, or `"geodesicVoxel"` |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `mesh` | `string` | The mesh that was bound |
| `skin_cluster` | `string \| null` | Name of the created skinCluster |
| `influences` | `string[]` | List of influence joint names |
| `influence_count` | `integer` | Number of influences |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "mesh": "pCube1",
  "joints": ["joint1", "joint2", "joint3"],
  "max_influences": 4,
  "bind_method": "closestDistance"
}
```

**Example Response**:

```json
{
  "mesh": "pCube1",
  "skin_cluster": "skinCluster1",
  "influences": ["joint1", "joint2", "joint3"],
  "influence_count": 3,
  "errors": null
}
```

---

### `skin.unbind`

Detach a skin cluster from a mesh, removing skin deformation.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `mesh` | `string` | Yes | - | Name of the mesh to unbind |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `mesh` | `string` | The mesh that was unbound |
| `unbound` | `boolean` | Whether unbinding succeeded |
| `skin_cluster` | `string \| null` | Name of the removed skinCluster |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "mesh": "pCube1"
}
```

**Example Response**:

```json
{
  "mesh": "pCube1",
  "unbound": true,
  "skin_cluster": "skinCluster1",
  "errors": null
}
```

---

### `skin.influences`

List influences (joints) on a skin cluster with index mapping.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `skin_cluster` | `string` | Yes | - | Name of the skinCluster node |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `skin_cluster` | `string` | The queried skinCluster name |
| `influences` | `array` | List of influence objects |
| `influences[].name` | `string` | Influence joint name |
| `influences[].index` | `integer` | Influence index |
| `count` | `integer` | Number of influences |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "skin_cluster": "skinCluster1"
}
```

**Example Response**:

```json
{
  "skin_cluster": "skinCluster1",
  "influences": [
    {"name": "joint1", "index": 0},
    {"name": "joint2", "index": 1},
    {"name": "joint3", "index": 2}
  ],
  "count": 3,
  "errors": null
}
```

---

### `skin.weights.get`

Get per-vertex skin weights with offset/limit pagination.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `skin_cluster` | `string` | Yes | - | Name of the skinCluster node |
| `offset` | `integer` | No | `0` | Starting vertex index (0-based) |
| `limit` | `integer` | No | `100` | Maximum vertices to return. Use 0 for unlimited. |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `skin_cluster` | `string` | The queried skinCluster name |
| `mesh` | `string` | The bound mesh name |
| `vertex_count` | `integer` | Total number of vertices in the mesh |
| `influence_count` | `integer` | Number of influences |
| `influences` | `string[]` | List of influence joint names |
| `vertices` | `array` | List of vertex weight entries |
| `vertices[].vertex_id` | `integer` | Vertex index |
| `vertices[].weights` | `object` | Map of joint name to weight value (only > 0.001) |
| `offset` | `integer` | The offset used |
| `count` | `integer` | Number of vertices returned |
| `truncated` | `boolean` | True if more vertices remain |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "skin_cluster": "skinCluster1",
  "offset": 0,
  "limit": 100
}
```

**Example Response**:

```json
{
  "skin_cluster": "skinCluster1",
  "mesh": "pCube1",
  "vertex_count": 8,
  "influence_count": 3,
  "influences": ["joint1", "joint2", "joint3"],
  "vertices": [
    {"vertex_id": 0, "weights": {"joint1": 0.8, "joint2": 0.2}},
    {"vertex_id": 1, "weights": {"joint1": 0.5, "joint2": 0.3, "joint3": 0.2}},
    {"vertex_id": 2, "weights": {"joint2": 0.9, "joint3": 0.1}}
  ],
  "offset": 0,
  "count": 3,
  "errors": null
}
```

---

### `skin.weights.set`

Set per-vertex skin weights with optional normalization.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `skin_cluster` | `string` | Yes | - | Name of the skinCluster node |
| `weights` | `array` | Yes | - | List of `{vertex_id, weights}` entries (max 1000 per call) |
| `weights[].vertex_id` | `integer` | Yes | - | Vertex index |
| `weights[].weights` | `object` | Yes | - | Map of joint name to weight value |
| `normalize` | `boolean` | No | `true` | Normalize weights after setting |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `skin_cluster` | `string` | The skinCluster name |
| `set_count` | `integer` | Number of vertices updated |
| `errors` | `object \| null` | Error details if any (keyed by vertex_id) |

**Example Request**:

```json
{
  "skin_cluster": "skinCluster1",
  "weights": [
    {"vertex_id": 0, "weights": {"joint1": 0.8, "joint2": 0.2}},
    {"vertex_id": 1, "weights": {"joint1": 0.5, "joint2": 0.5}}
  ],
  "normalize": true
}
```

**Example Response**:

```json
{
  "skin_cluster": "skinCluster1",
  "set_count": 2,
  "errors": null
}
```

---

### `skin.copy_weights`

Copy skin weights from one mesh to another using surface and influence association methods.

**Input**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `source_mesh` | `string` | Yes | - | Source mesh (must have a skinCluster) |
| `target_mesh` | `string` | Yes | - | Target mesh (must have a skinCluster) |
| `surface_association` | `string` | No | `"closestPoint"` | Surface matching: `"closestPoint"`, `"closestComponent"`, or `"rayCast"` |
| `influence_association` | `string` | No | `"closestJoint"` | Influence matching: `"closestJoint"`, `"closestBone"`, `"oneToOne"`, `"name"`, or `"label"` |

**Output**:

| Field | Type | Description |
|-------|------|-------------|
| `source_mesh` | `string` | The source mesh name |
| `target_mesh` | `string` | The target mesh name |
| `source_skin_cluster` | `string \| null` | Source skinCluster name |
| `target_skin_cluster` | `string \| null` | Target skinCluster name |
| `success` | `boolean` | Whether the copy succeeded |
| `errors` | `object \| null` | Error details if any |

**Example Request**:

```json
{
  "source_mesh": "pCube1",
  "target_mesh": "pCube2",
  "surface_association": "closestPoint",
  "influence_association": "closestJoint"
}
```

**Example Response**:

```json
{
  "source_mesh": "pCube1",
  "target_mesh": "pCube2",
  "source_skin_cluster": "skinCluster1",
  "target_skin_cluster": "skinCluster2",
  "success": true,
  "errors": null
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
| `scene.new` | false | false | true |
| `scene.open` | false | false | false |
| `scene.save` | false | false | false |
| `scene.save_as` | false | false | false |
| `scene.undo` | false | false | false |
| `scene.redo` | false | false | false |
| `nodes.list` | true | false | true |
| `nodes.create` | false | false | false |
| `nodes.delete` | false | false | true |
| `nodes.rename` | false | false | true |
| `nodes.parent` | false | false | true |
| `nodes.duplicate` | false | false | false |
| `nodes.info` | true | false | true |
| `attributes.get` | true | false | true |
| `attributes.set` | false | false | true |
| `connections.list` | true | false | true |
| `connections.get` | true | false | true |
| `connections.connect` | false | false | true |
| `connections.disconnect` | false | false | true |
| `connections.history` | true | false | true |
| `mesh.info` | true | false | true |
| `mesh.vertices` | true | false | true |
| `mesh.evaluate` | true | false | true |
| `selection.get` | true | false | true |
| `selection.set` | false | false | false |
| `selection.clear` | false | false | true |
| `selection.set_components` | false | false | false |
| `selection.get_components` | true | false | true |
| `selection.convert_components` | false | false | false |
| `modeling.create_polygon_primitive` | false | false | false |
| `modeling.extrude_faces` | false | false | false |
| `modeling.boolean` | false | false | false |
| `modeling.combine` | false | false | false |
| `modeling.separate` | false | false | false |
| `modeling.merge_vertices` | false | false | false |
| `modeling.bevel` | false | false | false |
| `modeling.bridge` | false | false | false |
| `modeling.insert_edge_loop` | false | false | false |
| `modeling.delete_faces` | false | false | false |
| `modeling.move_components` | false | false | false |
| `modeling.freeze_transforms` | false | false | true |
| `modeling.delete_history` | false | false | true |
| `modeling.center_pivot` | false | false | true |
| `modeling.set_pivot` | false | false | true |
| `shading.create_material` | false | false | false |
| `shading.assign_material` | false | false | false |
| `shading.set_material_color` | false | false | true |
| `skin.bind` | false | false | false |
| `skin.unbind` | false | false | false |
| `skin.influences` | true | false | true |
| `skin.weights.get` | true | false | true |
| `skin.weights.set` | false | false | false |
| `skin.copy_weights` | false | false | false |

---

## Token Budget Considerations

Large Maya scenes can contain thousands of nodes. To prevent token budget explosion in AI clients, Maya MCP implements output limits.

### Default Limits

| Tool | Default Limit | Configurable |
|------|---------------|--------------|
| `nodes.list` | 500 nodes | Yes (`limit` param) |
| `connections.list` | 500 connections | Yes (`limit` param) |
| `connections.history` | 500 history nodes | Yes (`limit` param) |
| `mesh.vertices` | 1000 vertices | Yes (`limit` param) |
| `mesh.evaluate` | 500 components per check | Yes (`limit` param) |
| `modeling.combine` | 50KB response guard | No |
| `modeling.separate` | 50KB response guard | No |
| `modeling.delete_history` | 50KB response guard | No |
| `skin.weights.get` | 100 vertices | Yes (`limit` param) |

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
