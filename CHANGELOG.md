# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-04-22

### Added

- `scene.new` tool - create new empty Maya scene with `force` parameter safety gate
  - Refuses when scene has unsaved changes (default `force=False`), preventing
    Maya's interactive "Save changes?" dialog from blocking commandPort
  - `force=True` discards unsaved changes without prompting
- Shared `parse_json_response()` utility in `maya_mcp.utils.parsing`
- Typed output models and explicit `outputSchema` coverage across the tool
  surface, including core read-only tools, `attributes`, `selection`, heavy
  data tools, and the remaining `connections`, `animation`, `modeling`,
  `shading`, `scripts`, and `viewport` families
- Env-gated Code Mode prototype in `maya_mcp.code_mode`
  - Disabled by default
  - Requires `MAYA_MCP_CODE_MODE=1` to enable
  - Uses fixed sandbox limits
- **M14: Polygon Modeling Tools**
  - `modeling.create_polygon_primitive` - create cube, sphere, cylinder, cone, torus, plane
  - `modeling.extrude_faces` - extrude polygon faces with local translation and offset
  - `modeling.boolean` - boolean union, difference, and intersection on two meshes
  - `modeling.combine` - combine multiple meshes into one
  - `modeling.separate` - separate a combined mesh into individual meshes
  - `modeling.merge_vertices` - merge vertices within a distance threshold
  - `modeling.bevel` - bevel edges or vertices with offset and segments
  - `modeling.bridge` - bridge between edge loops
  - `modeling.insert_edge_loop` - insert edge loop at an edge using polySplitRing
  - `modeling.delete_faces` - delete polygon faces from a mesh
  - `modeling.move_components` - move vertices, edges, or faces (relative or absolute)
  - `modeling.freeze_transforms` - freeze (reset) transforms to identity
  - `modeling.delete_history` - delete construction history from nodes
  - `modeling.center_pivot` - center pivot point on nodes
  - `modeling.set_pivot` - set pivot point to an explicit position
- **M12: Shading Tools**
  - `shading.create_material` - create material (lambert, blinn, phong, standardSurface) with shading group
  - `shading.assign_material` - assign material to meshes or face components
  - `shading.set_material_color` - set color attribute on a material
- **M8: Skinning Tools**
  - `skin.bind` - bind mesh to skeleton with influence options
  - `skin.unbind` - detach skin cluster from mesh
  - `skin.influences` - list influences on a skin cluster
  - `skin.weights.get` - get per-vertex skin weights with pagination
  - `skin.weights.set` - set per-vertex skin weights with normalization
  - `skin.copy_weights` - copy weights between meshes

### Fixed

- Reserved JavaScript property name `constructor` in MCP responses replaced with
  `constructor_node` to avoid `Object.prototype.constructor` collision causing
  Zod validation failures
- Direct `src/maya_mcp/server.py` launch no longer fails because the local
  `src/maya_mcp/types.py` module shadows Python's standard-library `types`
  module when the server is started as a script
- `json.dumps(None)` producing `"null"` instead of Python `None` in Maya commands
  sent via commandPort, causing `NameError` on the Maya side
- Dynamic code block indentation mismatch in f-string Maya command builders
- Noisy commandPort JSON responses are now cleaned before FastMCP tool wrappers
  consume them

### Changed

- `scene.new` and `scene.open` now support MCP form elicitation as a
  compatibility-preserving fallback for unsaved changes
  - Clients that advertise form elicitation can confirm discarding changes
    in-band and the server retries internally with `force=True`
  - Clients without elicitation support keep the existing `force=False`
    refusal behavior and must retry explicitly with `force=True`
- FastMCP integration updated to v3-compatible wiring
- Supported Python runtime is now effectively 3.10.1+; Python 3.10.0 is
  excluded because its stdlib `dataclasses.make_dataclass()` implementation
  lacks the `kw_only` support expected by current FastMCP structured-output
  parsing
- Consolidated all 13 response-parsing blocks across 4 tool files into shared
  `parse_json_response()` helper, eliminating 3 inconsistent patterns
- Transport parser (`_parse_maya_response`) now prefers last JSON-like part in
  multi-line responses, fixing a latent bug with commands that produce output
  before the JSON result
- Updated `tools/__init__.py` to export all 16+ tool functions (was stale, only
  exported M0 tools)

## [0.3.0] - 2025-02-02

### Added

- **M3-A: Maya Qt Control Panel** - dockable PySide2/PySide6 widget inside Maya
  - Server status indicator (green/red/yellow)
  - Start/stop button for commandPort
  - Port configuration UI
  - Scrollable connection log
  - Auto-start option via `userSetup.py`
- **M3-B2: Server instructions** - MCP `instructions` field with Maya-specific
  LLM guidance for tool usage
- **M3-B3: Output size guards** - response size checking with truncation and
  actionable warnings for oversized results
- **M3-B4: Consolidated `nodes.info`** - single tool with `info_category`
  parameter (`summary`, `transform`, `hierarchy`, `attributes`, `shape`, `all`)
  replacing multiple `attributes.get` / `nodes.list` call chains
- Editor integration guide

### Fixed

- OpenCode MCP config and `nodes.create` for primitive types

## [0.2.0] - 2025-02-01

### Added

- **M2: Extended Tools**
  - `attributes.get` - get attribute values (single or batch)
  - `attributes.set` - set attribute values (single or batch)
  - `nodes.create` - create nodes with optional name, parent, and initial attributes
  - `nodes.delete` - delete nodes with optional hierarchy deletion
  - `scene.undo` - undo last operation (critical for LLM error recovery)
  - `scene.redo` - redo last undone operation
- MCP tool annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`,
  `openWorldHint`) for AI client safety reasoning
- Token budget limits - `nodes.list` defaults to 500 nodes with `truncated` /
  `total_count` fields when limited
- Integration test suite against live Maya instance
- M2-M6 roadmap in PRD

### Changed

- Revised M2 roadmap to follow workflow-first design principles (Block MCP Playbook)
- `scene.info`, `nodes.list`, `selection.get`, `selection.set` upgraded from stubs
  to full implementations (M1 Core Tools)

## [0.1.0] - 2025-01-30

### Added

- Initial project scaffold
- FastMCP server with tool registration
- Maya commandPort transport layer with:
  - Connect/request timeouts
  - Bounded retry with exponential backoff
  - Automatic reconnection on next call
- Core tools:
  - `health.check` - connection health monitoring
  - `maya.connect` - manual connection establishment
  - `maya.disconnect` - manual connection teardown
  - `scene.info` - scene information retrieval (stub)
  - `nodes.list` - node listing by type (stub)
  - `selection.get` - selection query (stub)
  - `selection.set` - selection modification (stub)
  - `selection.clear` - clear selection
- Typed error hierarchy with `MayaMCPError` base class
- Level 1 resilience (detect unavailable, return error, recover on restart)
- MkDocs documentation with mkdocstrings
- Comprehensive test suite with mocked transport
- GitLab CI pipeline (mypy, ruff, pytest)
- Git workflow documentation with branch protection rules

### Security

- Localhost-only commandPort connection by default
- No arbitrary code execution - all operations are explicit tools
- No raw Python/MEL string evaluation exposed to clients

[Unreleased]: https://github.com/GimbalGoats/GG_MayaMCP/compare/v0.4.0...main
[0.4.0]: https://github.com/GimbalGoats/GG_MayaMCP/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/GimbalGoats/GG_MayaMCP/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/GimbalGoats/GG_MayaMCP/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/GimbalGoats/GG_MayaMCP/releases/tag/v0.1.0
