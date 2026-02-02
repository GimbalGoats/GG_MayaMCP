# Product Requirements Document (PRD)

## Overview

**Product**: Maya MCP Server  
**Version**: 0.1.0 (v0)  
**Status**: Active Development  
**Last Updated**: 2025-02-02

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

### M3: Maya UI Panel + LLM Optimization 📋

**Goal**: Provide in-Maya control panel and optimize tools for LLM efficiency.

#### M3-A: Maya Qt Panel

A dockable Qt widget inside Maya for controlling the MCP server connection.

| ID | Feature | Description | Effort |
|----|---------|-------------|--------|
| M3.A1 | **Maya Qt Panel** | Dockable PySide2 widget in Maya for MCP control | Medium |
| M3.A2 | **Server status indicator** | Visual indicator (green/red/yellow) showing commandPort status | Low |
| M3.A3 | **Start/Stop button** | Toggle commandPort open/close from Maya UI | Low |
| M3.A4 | **Port configuration** | UI to set/change commandPort port number | Low |
| M3.A5 | **Connection log** | Scrollable log showing recent MCP requests | Medium |
| M3.A6 | **Auto-start option** | Preference to auto-open commandPort on Maya startup | Low |

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                        Maya Process                          │
│                                                              │
│  ┌──────────────────────┐     ┌─────────────────────────┐   │
│  │   Maya Qt Panel      │     │    commandPort          │   │
│  │   (PySide2)          │────►│    (TCP :7001)          │   │
│  │                      │     └───────────▲─────────────┘   │
│  │  [●] Server: Running │                 │                 │
│  │  [Start] [Stop]      │                 │                 │
│  │  Port: [7001    ]    │                 │                 │
│  │  ☑ Auto-start        │                 │                 │
│  │                      │                 │                 │
│  │  Connection Log:     │                 │                 │
│  │  ├─ 10:30 nodes.list │                 │                 │
│  │  └─ 10:31 attrs.get  │                 │                 │
│  └──────────────────────┘                 │                 │
└───────────────────────────────────────────┼─────────────────┘
                                            │
                              TCP localhost:7001
                                            │
┌───────────────────────────────────────────▼─────────────────┐
│              Maya MCP Server (External Process)              │
│              python -m maya_mcp.server                       │
└─────────────────────────────────────────────────────────────┘
```

**Files to create**:
- `src/maya_mcp/maya_panel/` - Panel package (runs inside Maya)
- `scripts/userSetup.py` - Example auto-start script
- `docs/usage/maya-panel.md` - Panel documentation

#### M3-B: LLM Optimization

Improvements based on [Block's MCP Playbook](https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers).

| ID | Feature | Description | Effort |
|----|---------|-------------|--------|
| M3.B1 | **Markdown output option** | Add `format: "markdown" \| "json"` parameter to read tools | Low |
| M3.B2 | **Server instructions** | MCP `instructions` field with Maya-specific LLM guidance | Low |
| M3.B3 | **Output size guards** | Check response size; truncate with actionable warning if too large | Medium |
| M3.B4 | **Consolidated `nodes.info`** | Single tool with `info_category` param for all node queries | Medium |

---

### M4: Scene Operations 📋

**Goal**: File and scene management workflows.

| ID | Feature | Description | Effort |
|----|---------|-------------|--------|
| M4.1 | `scene.new` | Create new scene (with save prompt option) | Low |
| M4.2 | `scene.open` | Open scene file (path validated) | Medium |
| M4.3 | `scene.save` | Save current scene | Low |
| M4.4 | `scene.save_as` | Save scene to new path | Low |
| M4.5 | `scene.import` | Import file into current scene | Medium |
| M4.6 | `scene.export` | Export selection to file | Medium |
| M4.7 | `nodes.rename` | Rename nodes (batch support) | Low |
| M4.8 | `nodes.parent` | Reparent nodes in hierarchy | Low |
| M4.9 | `nodes.duplicate` | Duplicate nodes with hierarchy | Medium |

**Security considerations**:
- All file paths must be validated
- No shell metacharacters allowed
- Consider allowlist for file extensions

---

### M5: Animation & Rigging 📋

**Goal**: Support animation workflows with template patterns for rigging.

#### M5-A: Core Animation Tools

| ID | Feature | Description | Effort |
|----|---------|-------------|--------|
| M5.A1 | `animation.set_keyframe` | Set keyframe on attribute(s) at current/specified time | Medium |
| M5.A2 | `animation.get_keyframes` | Query keyframes for attribute(s) in time range | Medium |
| M5.A3 | `animation.delete_keyframes` | Delete keyframes in range | Low |
| M5.A4 | `animation.set_time` | Set current time / go to frame | Low |
| M5.A5 | `animation.get_time_range` | Get playback range | Low |
| M5.A6 | `animation.set_time_range` | Set playback range | Low |

#### M5-B: Rigging Workflow Patterns (Design Only)

Document common rigging workflows to inform future tool design. **No implementation** - design patterns only.

| Pattern | Tools Needed | Workflow Example |
|---------|-------------|------------------|
| **FK Chain** | `nodes.create`, `nodes.parent`, `attributes.set` | Create joint chain, set orient, parent hierarchy |
| **IK Setup** | `nodes.create` (ikHandle), constraints | Create IK handle, pole vector |
| **Control Rig** | `nodes.create` (curves), constraints | Create NURBS control, constraint to joint |
| **Blend Shapes** | `nodes.create` (blendShape), `attributes.set` | Connect blend shape targets |
| **Skin Binding** | `skin.bind`, `skin.weights.get/set` | Bind mesh to skeleton, adjust weights |

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

## Milestone Priority

```
M0 ✅ ─► M1 ✅ ─► M2 ✅ ─► M3 📋 ─► M4 📋 ─► M5 📋 ─► M6 💡
                          │
                          ├─► M3-A: Maya UI Panel (high priority)
                          └─► M3-B: LLM Optimization (high priority)
```

| Priority | Milestone | Rationale |
|----------|-----------|-----------|
| 1 | M3-A (Maya UI Panel) | User-facing control, high visibility |
| 2 | M3-B (LLM Optimization) | Efficiency improvements |
| 3 | M4 (Scene Operations) | Common file workflows |
| 4 | M5-A (Core Animation) | Essential animation tools |
| 5 | M5-B (Rigging Patterns) | Design documentation only |
| 6 | M6 (Production Hardening) | Nice to have |

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
