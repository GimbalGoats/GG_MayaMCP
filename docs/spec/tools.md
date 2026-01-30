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
| `nodes.list` | true | false | true |
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
