# Product Requirements Document (PRD)

## Overview

**Product**: Maya MCP Server  
**Version**: 0.1.0 (v0)  
**Status**: Active Development  
**Last Updated**: 2026-03-02

Maya MCP is an MCP (Model Context Protocol) server that enables AI assistants and other MCP-compatible clients to control a running instance of Autodesk Maya via its commandPort socket interface.

> **📋 Roadmap**: This document is the single source of truth for project scope, milestones, and roadmap. All future plans are documented in the [Milestones](#milestones) section below.

## Problem Statement

AI assistants need a standardized, safe way to interact with Maya for:

- Querying scene information
- Managing selections
- Manipulating nodes and attributes
- Automating repetitive tasks

Direct integration is problematic because:

1. Maya runs in a separate process with its own Python interpreter
2. Arbitrary code execution poses security risks
3. Maya can crash, requiring robust error handling
4. Different Maya versions may have API variations

## Goals (v0)

### Primary Goals

| ID | Goal | Success Criteria |
|----|------|------------------|
| G1 | **Safe Remote Control** | Execute predefined operations without arbitrary code execution |
| G2 | **Health Monitoring** | Detect Maya unavailability and report typed errors |
| G3 | **Graceful Recovery** | Reconnect automatically when Maya restarts |
| G4 | **Typed Interfaces** | All tool inputs/outputs have explicit types |
| G5 | **Transport Isolation** | MCP server never imports `maya.cmds` |

### Secondary Goals

| ID | Goal | Success Criteria |
|----|------|------------------|
| S1 | Developer Experience | Clear documentation and examples |
| S2 | Testability | Unit tests work without Maya running |
| S3 | Extensibility | Easy to add new tools |

## Non-Goals (Explicitly Out of Scope)

| ID | Non-Goal | Rationale |
|----|----------|-----------|
| N1 | **Arbitrary Code Execution** | Security risk; tools must be explicit |
| N2 | **Auto-restart Maya** | Complex; out of resilience Level 1 scope |
| N3 | **Remote Host Support** | Security; localhost-only |
| N4 | **Concurrent Request Handling** | Complexity; single-flight |
| N5 | **Full Maya API Coverage** | Scope; prioritize common workflows |
| N6 | **Plugin Management** | Scope; focus on scene operations |
| N7 | **Render Farm Integration** | Different use case |
| N8 | **Version-specific Adapters** | Defer until needed |

## Target Users

### Primary: AI-Assisted 3D Artists

- Use AI assistants to speed up Maya workflows
- Want natural language control of Maya
- Need reliable, predictable tool behavior

### Secondary: Pipeline Developers

- Build automation on top of Maya MCP
- Need typed APIs and clear error handling
- Want extensible architecture

## Functional Requirements

### FR1: Connection Management

- FR1.1: Connect to Maya commandPort on localhost
- FR1.2: Support configurable port (default: 7001)
- FR1.3: Detect connection failures with typed errors
- FR1.4: Support manual connect/disconnect via tools

### FR2: Health Monitoring

- FR2.1: `health.check` tool returns connection status
- FR2.2: Status includes: `ok | offline | reconnecting`
- FR2.3: Include last error message
- FR2.4: Include last successful contact timestamp

### FR3: Core Tools

- FR3.1: `scene.info` - Get current scene information
- FR3.2: `nodes.list` - List nodes by type
- FR3.3: `selection.get` - Get current selection
- FR3.4: `selection.set` - Set selection

### FR4: Error Handling

- FR4.1: All errors are typed (subclasses of `MayaMCPError`)
- FR4.2: `MayaUnavailableError` for connection issues
- FR4.3: `MayaCommandError` for command execution failures
- FR4.4: Errors include actionable context

## Non-Functional Requirements

### NFR1: Performance

- Connect timeout: 5 seconds (configurable)
- Command timeout: 30 seconds (configurable)
- Retry delay: exponential backoff (0.5s base, max 3 retries)

### NFR2: Security

- Localhost-only connections (no remote hosts)
- No arbitrary code execution
- No secrets in error messages

### NFR3: Reliability

- Level 1 resilience: detect, report, recover on restart
- Bounded retries prevent infinite loops
- Clear state machine for connection lifecycle

### NFR4: Maintainability

- 100% type-hinted (mypy strict)
- Google-style docstrings
- Ruff linting/formatting
- Pytest test coverage

## Success Metrics

| Metric | Target |
|--------|--------|
| Type coverage | 100% (mypy strict passes) |
| Lint issues | 0 (ruff clean) |
| Test coverage | >80% for transport layer |
| Documentation | All public APIs documented |

---

## Milestones

> **This is the single roadmap for Maya MCP.** All planned work is documented here.

### Milestone Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Complete |
| 🚧 | In Progress |
| 📋 | Planned |
| 💡 | Nice to Have |

---

### M0: Scaffold ✅

- [x] Project structure
- [x] pyproject.toml with all tooling
- [x] Transport layer with timeouts/retries
- [x] Health check tool
- [x] Connection management tools
- [x] Tool stubs for scene/nodes/selection
- [x] Test infrastructure with mocks
- [x] MkDocs documentation

---

### M1: Core Tools ✅

- [x] Implement scene.info
- [x] Implement nodes.list with type filtering
- [x] Implement selection.get/set
- [x] Integration tests with real Maya

---

### M2: Extended Tools ✅

**Design Principle**: Workflow-first, not API-first. Tools should consolidate
multiple Maya commands into single high-level operations that match how AI
agents actually work. See [Block's MCP Playbook](https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers).

- [x] `attributes.get` - Get attribute values (single or batch)
- [x] `attributes.set` - Set attribute values (single or batch)
- [x] `nodes.create` - Create nodes with optional name, parent, and initial attributes
- [x] `nodes.delete` - Delete nodes with optional hierarchy deletion
- [x] `scene.undo` - Undo last operation (critical for LLM error recovery)
- [x] `scene.redo` - Redo last undone operation

**Rationale for changes from original plan:**
- Transform operations (translate, rotate, scale) ARE attributes - covered by `attributes.set`
- Batch attribute operations reduce tool call chaining
- Node creation with initialization avoids create→set→parent call chains
- Undo/redo enables LLM self-correction without user intervention

---

### M3: Maya UI Panel + LLM Optimization 🚧

**Goal**: Provide in-Maya control panel and optimize tools for LLM efficiency.

#### M3-A: Maya Qt Panel ✅

A dockable Qt widget inside Maya for controlling the MCP server connection.

| ID | Feature | Description | Effort | Status |
|----|---------|-------------|--------|--------|
| M3.A1 | **Maya Qt Panel** | Dockable PySide2/PySide6 widget in Maya for MCP control | Medium | ✅ |
| M3.A2 | **Server status indicator** | Visual indicator (green/red/yellow) showing commandPort status | Low | ✅ |
| M3.A3 | **Start/Stop button** | Toggle commandPort open/close from Maya UI | Low | ✅ |
| M3.A4 | **Port configuration** | UI to set/change commandPort port number | Low | ✅ |
| M3.A5 | **Connection log** | Scrollable log showing recent MCP requests | Medium | ✅ |
| M3.A6 | **Auto-start option** | Preference to auto-open commandPort on Maya startup | Low | ✅ |

**Files created**:
- `src/maya_mcp/maya_panel/` - Panel package (runs inside Maya)
- `scripts/userSetup.py` - Example auto-start script
- `docs/usage/maya-panel.md` - Panel documentation

#### M3-B: LLM Optimization 🚧

Improvements based on [Block's MCP Playbook](https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers).

| ID | Feature | Description | Effort | Status |
|----|---------|-------------|--------|--------|
| M3.B1 | **Markdown output option** | Add `format: "markdown" \| "json"` parameter to read tools | Low | 📋 |
| M3.B2 | **Server instructions** | MCP `instructions` field with Maya-specific LLM guidance | Low | ✅ |
| M3.B3 | **Output size guards** | Check response size; truncate with actionable warning if too large | Medium | ✅ |
| M3.B4 | **Consolidated `nodes.info`** | Single tool with `info_category` param for all node queries | Medium | ✅ |

---

### M4: Scene Operations ✅

**Goal**: File and scene management workflows.

| ID | Feature | Description | Effort | Status |
|----|---------|-------------|--------|--------|
| M4.1 | `scene.new` | Create new scene (with save prompt option) | Low | ✅ |
| M4.2 | `scene.open` | Open scene file (path validated) | Medium | ✅ |
| M4.3 | `scene.save` | Save current scene | Low | ✅ |
| M4.4 | `scene.save_as` | Save scene to new path | Low | ✅ |
| M4.5 | `scene.import` | Import file into current scene | Medium | ✅ |
| M4.6 | `scene.export` | Export selection to file | Medium | ✅ |
| M4.7 | `nodes.rename` | Rename nodes (batch support) | Low | ✅ |
| M4.8 | `nodes.parent` | Reparent nodes in hierarchy | Low | ✅ |
| M4.9 | `nodes.duplicate` | Duplicate nodes with hierarchy | Medium | ✅ |

**Security considerations**:
- All file paths must be validated
- No shell metacharacters allowed
- Consider allowlist for file extensions

---

### M5: Animation & Rigging

**Goal**: Support animation workflows with template patterns for rigging.

#### M5-A: Core Animation Tools ✅

| ID | Feature | Description | Effort | Status |
|----|---------|-------------|--------|--------|
| M5.A1 | `animation.set_keyframe` | Set keyframe on attribute(s) at current/specified time | Medium | ✅ |
| M5.A2 | `animation.get_keyframes` | Query keyframes for attribute(s) in time range | Medium | ✅ |
| M5.A3 | `animation.delete_keyframes` | Delete keyframes in range | Low | ✅ |
| M5.A4 | `animation.set_time` | Set current time / go to frame | Low | ✅ |
| M5.A5 | `animation.get_time_range` | Get playback range | Low | ✅ |
| M5.A6 | `animation.set_time_range` | Set playback range | Low | ✅ |

#### M5-B: Rigging Workflow Patterns (Design Only)

Document common rigging workflows to inform future tool design. **No implementation** - design patterns only.

| Pattern | Tools Needed | Workflow Example |
|---------|-------------|------------------|
| **FK Chain** | `nodes.create`, `nodes.parent`, `attributes.set` | Create joint chain, set orient, parent hierarchy |
| **IK Setup** | `nodes.create` (ikHandle), constraints | Create IK handle, pole vector |
| **Control Rig** | `nodes.create` (curves), constraints | Create NURBS control, constraint to joint |
| **Blend Shapes** | `nodes.create` (blendShape), `attributes.set` | Connect blend shape targets |
| **Skin Binding** | `skin.bind`, `skin.weights.get/set` | Bind mesh to skeleton, adjust weights |

**Cross-reference**: M8 (Skinning) and M9 (Deformers & Blend Shapes) implement the tools documented in these patterns.

**Deliverable**: `docs/spec/rigging-patterns.md` documenting:
- What tools would be needed for each pattern
- Example LLM prompts
- Expected tool call sequences
- Input/output schemas

---

### M6: Production Hardening 💡

**Goal**: Studio deployment readiness. **Nice to have** - implement as needed.

| ID | Feature | Description | Effort |
|----|---------|-------------|--------|
| M6.1 | Structured logging | JSON logs with correlation IDs | Medium |
| M6.2 | Metrics endpoint | Tool call counts, latency stats | Medium |
| M6.3 | Rate limiting | Prevent runaway AI agents | Medium |
| M6.4 | Audit logging | Log all tool invocations | Low |
| M6.5 | Enhanced health check | Include Maya version, scene stats | Low |

---

### M7: Node Graph & Connections ✅

**Goal**: Expose node graph wiring — the most common operation in Maya pipeline scripts.

**Namespace**: `connections.*`

| ID | Feature | Description | Effort | Status |
|----|---------|-------------|--------|--------|
| M7.1 | `connections.list` | List connections on a node with direction/type filters | Low | ✅ |
| M7.2 | `connections.get` | Get connection details for specific plugs | Low | ✅ |
| M7.3 | `connections.connect` | Connect two attributes | Low | ✅ |
| M7.4 | `connections.disconnect` | Disconnect attributes with safe disconnect-before-reconnect pattern | Low | ✅ |
| M7.5 | `connections.history` | List construction/deformation history on a node | Medium | ✅ |

**Design note**: `connections.disconnect` implements the disconnect-before-reconnect safety pattern common in production rigs.

---

### M8: Skinning ✅

**Goal**: Skin binding and weight management for character rigging workflows.

**Namespace**: `skin.*`

| ID | Feature | Description | Effort |
|----|---------|-------------|--------|
| M8.1 | `skin.bind` | Bind mesh to skeleton with influence options | Medium |
| M8.2 | `skin.unbind` | Detach skin cluster from mesh | Low |
| M8.3 | `skin.influences` | List influences on a skin cluster | Low |
| M8.4 | `skin.weights.get` | Get skin weights with offset/limit pagination | High |
| M8.5 | `skin.weights.set` | Set skin weights with normalization | High |
| M8.6 | `skin.copy_weights` | Copy weights between meshes with association options | Medium |

**Token budget**: Skin weight data can reach 4–15MB for production meshes (100K vertices × ~4 influences). `skin.weights.get` MUST use offset/limit pagination and return summaries by default. The 50KB response guard applies.

---

### M9: Deformers & Blend Shapes 📋

**Goal**: Deformer management and blend shape workflows for modeling and rigging.

**Namespace**: `deformers.*`

| ID | Feature | Description | Effort |
|----|---------|-------------|--------|
| M9.1 | `deformers.list` | List deformers on a node with deformation order | Low |
| M9.2 | `deformers.create` | Create deformer (cluster, lattice, nonLinear, wire, deltaMush, wrap) | Medium |
| M9.3 | `deformers.reorder` | Change deformation order on a node | Low |
| M9.4 | `blendshape.create` | Create blend shape deformer with initial targets | Medium |
| M9.5 | `blendshape.targets` | List, add, or remove blend shape targets | Medium |
| M9.6 | `blendshape.weights` | Get or set blend shape target weights | Low |

**Cross-reference**: Implements the Blend Shapes rigging pattern from M5-B.

---

### M10: Constraints 📋

**Goal**: Constraint creation and management for rigging and animation workflows.

**Namespace**: `constraints.*`

| ID | Feature | Description | Effort |
|----|---------|-------------|--------|
| M10.1 | `constraints.create` | Create constraint (parent, point, orient, aim, scale, poleVector) | Medium |
| M10.2 | `constraints.list` | List constraints on a node with type filter | Low |
| M10.3 | `constraints.delete` | Delete constraints from a node | Low |
| M10.4 | `constraints.weights` | Get or set constraint target weights | Low |

**Design note**: Supports the common 'snap then delete constraint' pattern used in rig positioning workflows.

---

### M11: Mesh Operations & Component Selection ✅

**Goal**: Mesh queries, topology analysis, and component-level selection for targeted editing.

#### M11-A: Mesh Queries

**Namespace**: `mesh.*`

| ID | Feature | Description | Effort |
|----|---------|-------------|--------|
| M11.A1 | `mesh.info` | Get mesh statistics: vertex/face/edge counts, bounding box, UV status | Low |
| M11.A2 | `mesh.vertices` | Query vertex positions with offset/limit pagination | Medium |
| M11.A3 | `mesh.evaluate` | Topology analysis: non-manifold edges, lamina faces, holes, border edges | Medium |

**Token budget**: Vertex position data uses offset/limit pagination. `mesh.info` returns summary statistics by default.

#### M11-B: Component Selection

**Namespace**: extends `selection.*`

| ID | Feature | Description | Effort |
|----|---------|-------------|--------|
| M11.B1 | `selection.set_components` | Select vertices, edges, or faces by index ranges or criteria | Medium |
| M11.B2 | `selection.get_components` | Get selected components with type and indices | Low |
| M11.B3 | `selection.convert_components` | Convert selection between vertex/edge/face | Low |

**Security**: Component syntax uses `[`, `]`, `:`, and `.` characters (e.g., `pCube1.vtx[0:10]`). Input validation must be updated to allow these characters in component specifications while still blocking shell metacharacters.

---

### M12: Materials & Shading ✅

**Goal**: Basic material creation and assignment for shading workflows.

**Namespace**: `shading.*`

| ID | Feature | Description | Effort | Status |
|----|---------|-------------|--------|--------|
| M12.1 | `shading.create_material` | Create material with shading group (lambert, blinn, phong, standardSurface) | Medium | ✅ |
| M12.2 | `shading.assign_material` | Assign material to meshes or face components | Medium | ✅ |
| M12.3 | `shading.set_material_color` | Set color attribute on a material (color, baseColor, transparency, etc.) | Low | ✅ |

**Workflow-first**: `shading.create_material` consolidates 4 internal Maya steps (createNode material → createNode shadingGroup → connectAttr outColor → connectAttr dagSetMembers) into a single tool call.

**Implementation note**: The namespace was changed from the original `materials.*` plan to `shading.*` to better reflect the scope (material creation, assignment, and color setting rather than full material management). `materials.list` and `materials.get` were deferred — AI clients can use `nodes.list(node_type="lambert")` and `nodes.info` as alternatives.

---

### M13: Custom Script Execution ✅

**Goal**: Enable AI clients to discover and execute user-provided Python scripts inside Maya, with a three-tier trust model balancing usability and security.

**Design Principle**: Scripts are the escape hatch for workflows that don't have dedicated tools yet. Rather than blocking all code execution (too restrictive) or allowing arbitrary code (too dangerous), Maya MCP uses a layered trust model where each tier requires explicit opt-in.

#### Three-Tier Trust Model

| Tier | Tool | Risk Level | Config Required | Description |
|------|------|------------|-----------------|-------------|
| 1 | `script.list` | Read-only | `MAYA_MCP_SCRIPT_DIRS` | Catalog available scripts from allowlisted directories |
| 2 | `script.execute` | Medium | `MAYA_MCP_SCRIPT_DIRS` | Execute pre-approved `.py` files from allowlisted directories |
| 3 | `script.run` | High | `MAYA_MCP_ENABLE_RAW_EXECUTION=true` | Execute raw Python code (opt-in, disabled by default) |

#### Tools

**Namespace**: `script.*`

| ID | Feature | Description | Effort |
|----|---------|-------------|--------|
| M13.1 | `script.list` | List `.py` scripts recursively from `MAYA_MCP_SCRIPT_DIRS` directories. Returns name + path. Server-side only (no Maya needed). | Low |
| M13.2 | `script.execute` | Execute a script file inside Maya. Path validated against allowlisted dirs. Supports passing arguments via `__args__` dict. Returns success/output/error. | Medium |
| M13.3 | `script.run` | Execute raw Python code inside Maya. Disabled by default. Code validated for size limits. Returns success/output/error. | Medium |

#### Configuration (env vars only — no config files)

| Variable | Default | Description |
|----------|---------|-------------|
| `MAYA_MCP_SCRIPT_DIRS` | `""` (empty) | Semicolon-separated list of absolute directory paths to scan for scripts |
| `MAYA_MCP_ENABLE_RAW_EXECUTION` | `false` | Set to `true` or `1` to enable `script.run` |
| `MAYA_MCP_SCRIPT_TIMEOUT` | `60.0` | Timeout in seconds for script execution |

#### Security Requirements

- All script file paths validated against allowlisted directories (no traversal, no symlink escape)
- Forbidden shell metacharacters (`;|&$\``) rejected in paths
- Windows device names (`CON`, `NUL`, `COM1`, etc.) rejected
- UNC paths and alternate data streams rejected
- Script file size capped (1 MB max)
- Raw code size capped (100 KB max)
- `script.run` disabled by default — explicit opt-in via env var
- No command blocklists/allowlists for raw code — the config flag IS the guardrail
- Stdout captured and returned; errors surfaced as structured data
- Output subject to existing 50KB response size guard

#### Implementation Notes

- `ScriptConfig` dataclass loaded from env vars (frozen, validated)
- Script validation utilities in `utils/script_validation.py`
- Tool functions in `tools/scripts.py` following existing tool patterns
- Tools registered in `server.py` with proper MCP annotations
- All code must pass `mypy --strict`, `ruff`, and have full test coverage with mocked transport

---

### M14: Polygon Modeling ✅

**Goal**: Polygon modeling operations for geometry creation and editing workflows.

**Namespace**: `modeling.*`

| ID | Feature | Description | Effort | Status |
|----|---------|-------------|--------|--------|
| M14.1 | `modeling.create_polygon_primitive` | Create polygon primitives (cube, sphere, cylinder, cone, torus, plane) | Medium | ✅ |
| M14.2 | `modeling.extrude_faces` | Extrude polygon faces with local translation and offset | Medium | ✅ |
| M14.3 | `modeling.boolean` | Boolean operations (union, difference, intersection) on two meshes | Medium | ✅ |
| M14.4 | `modeling.combine` | Combine multiple meshes into one | Low | ✅ |
| M14.5 | `modeling.separate` | Separate a combined mesh into individual meshes | Low | ✅ |
| M14.6 | `modeling.merge_vertices` | Merge vertices within a distance threshold | Low | ✅ |
| M14.7 | `modeling.bevel` | Bevel edges or vertices with offset and segments | Medium | ✅ |
| M14.8 | `modeling.bridge` | Bridge between edge loops | Medium | ✅ |
| M14.9 | `modeling.insert_edge_loop` | Insert edge loop at an edge using polySplitRing | Low | ✅ |
| M14.10 | `modeling.delete_faces` | Delete polygon faces from a mesh | Low | ✅ |
| M14.11 | `modeling.move_components` | Move vertices, edges, or faces (relative or absolute) | Medium | ✅ |
| M14.12 | `modeling.freeze_transforms` | Freeze (reset) transforms to identity | Low | ✅ |
| M14.13 | `modeling.delete_history` | Delete construction history from nodes | Low | ✅ |
| M14.14 | `modeling.center_pivot` | Center pivot point on nodes | Low | ✅ |
| M14.15 | `modeling.set_pivot` | Set pivot point to an explicit position | Low | ✅ |

**Workflow-first**: Tools cover the full modeling workflow — create primitives, edit topology (extrude, bevel, bridge, insert edge loop), combine/separate meshes, boolean operations, and cleanup (freeze transforms, delete history, center pivot).

**Token budget**: `modeling.combine` and `modeling.separate` responses are guarded to prevent oversized results with many meshes.

---

## Milestone Priority

```
M0 ✅ ─► M1 ✅ ─► M2 ✅ ─► M3 🚧 ─► M4 ✅ ─► M5 📋 ─► M6 💡
                          │
                          ├─► M3-A ✅
                          └─► M3-B 🚧 (3/4)

M7 ✅ (Node Graph & Connections)

After M5:
M5 📋 ─► M8 ✅ ─► M9 📋 ─► M10 📋 ─► M11 ✅ ─► M12 ✅ ─► M13 ✅

M14 ✅ (Polygon Modeling)
```

| Priority | Milestone | Rationale |
|----------|-----------|-----------|
| 1 | ~~M3-A (Maya UI Panel)~~ | ✅ Complete |
| 2 | M3-B (LLM Optimization) | 1 remaining item: markdown output |
| 3 | ~~M4 (Scene Operations)~~ | ✅ Complete |
| 4 | ~~M7 (Node Graph & Connections)~~ | ✅ Complete |
| 5 | ~~M5-A (Core Animation)~~ | ✅ Complete |
| 6 | M5-B (Rigging Patterns) | Design documentation only |
| 7 | M6 (Production Hardening) | Nice to have |
| 8 | ~~M8 (Skinning)~~ | ✅ Complete |
| 9 | M9 (Deformers & Blend Shapes) | Essential for modeling and rigging; implements M5-B Blend Shapes pattern |
| 10 | M10 (Constraints) | Core rigging and animation workflow |
| 11 | ~~M11 (Mesh Operations & Component Selection)~~ | ✅ Complete |
| 12 | ~~M12 (Materials & Shading)~~ | ✅ Complete |
| 13 | M13 (Custom Script Execution) | Escape hatch for workflows without dedicated tools; three-tier trust model |
| 14 | ~~M14 (Polygon Modeling)~~ | ✅ Complete |

---

## Design Principles

Based on [Block's MCP Playbook](https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers):

### 1. Workflow-First Design

Design tools based on how AI clients will use them, not bottom-up from Maya commands.

| ❌ API-First | ✅ Workflow-First |
|-------------|-------------------|
| `cmds.ls()` wrapper | `nodes.list(type, pattern, limit)` |
| `cmds.setAttr()` per attr | `attributes.set(node, {attr: value, ...})` |
| `cmds.createNode()` then parent then setAttr | `nodes.create(type, name, parent, attributes)` |

### 2. Token Budget Awareness

Large Maya scenes can have 10,000+ nodes. Protect LLM context windows.

- Default limits on list operations (`limit=500`)
- Include `truncated` and `total_count` when limited
- Actionable error messages for oversized responses

### 3. Tool Annotations

Help AI clients make safe decisions with semantic hints:

| Annotation | Meaning |
|------------|---------|
| `readOnlyHint=True` | Safe to call without confirmation |
| `destructiveHint=True` | May cause irreversible changes |
| `idempotentHint=True` | Safe to retry on failure |

### 4. Single Risk Level Per Tool

Don't mix read-only and write operations in one tool.

| ❌ Mixed | ✅ Separated |
|----------|-------------|
| `selection.manage(action, nodes)` | `selection.get()` + `selection.set()` + `selection.clear()` |

### 5. Large Data: Summary + Pagination

Return summary data by default; paginate large datasets on request. Large responses (>50KB) consume LLM tokens without adding value.

| ❌ Naive | ✅ Summary + Paginate |
|---------|----------------------|
| Return all 100K vertex positions | Return vertex count + bounding box; paginate on request |
| Return all skin weights (4–15MB) | Return influence summary; paginate per-vertex weights |

---

## Appendix: Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| mayapy subprocess | No bidirectional communication |
| Maya Python API | Requires running inside Maya |
| Maya REST server | Non-standard, extra complexity |
| Unix domain sockets | Windows compatibility |

Selected: **commandPort with INET socket** - See [ADR-0001](adr/0001-commandport.md)

---

## Appendix: References

- [Block's MCP Playbook](https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers) - Design patterns from 60+ MCP servers
- [GitHub: Building Secure Remote MCP Servers](https://github.blog/ai-and-ml/generative-ai/how-to-build-secure-and-scalable-remote-mcp-servers/) - Security best practices
- [MCP Specification](https://modelcontextprotocol.io/specification) - Protocol specification
- [FastMCP Documentation](https://github.com/jlowin/fastmcp) - Python MCP framework
