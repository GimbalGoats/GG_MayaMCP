# Product Requirements Document (PRD)

## Overview

**Product**: Maya MCP Server  
**Version**: 0.1.0 (v0)  
**Status**: Initial Development

Maya MCP is an MCP (Model Context Protocol) server that enables AI assistants and other MCP-compatible clients to control a running instance of Autodesk Maya via its commandPort socket interface.

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

## Non-Goals (Explicitly Out of Scope for v0)

| ID | Non-Goal | Rationale |
|----|----------|-----------|
| N1 | **Arbitrary Code Execution** | Security risk; tools must be explicit |
| N2 | **Auto-restart Maya** | Complex; out of resilience Level 1 scope |
| N3 | **Remote Host Support** | Security; localhost-only for v0 |
| N4 | **Concurrent Request Handling** | Complexity; single-flight for v0 |
| N5 | **Full Maya API Coverage** | Scope; start with core operations |
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

### FR3: Core Tools (Stubs for v0)

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

## Milestones

### M0: Scaffold (This PR)

- [x] Project structure
- [x] pyproject.toml with all tooling
- [x] Transport layer with timeouts/retries
- [x] Health check tool
- [x] Connection management tools
- [x] Tool stubs for scene/nodes/selection
- [x] Test infrastructure with mocks
- [x] MkDocs documentation

### M1: Core Tools ✅

- [x] Implement scene.info
- [x] Implement nodes.list with type filtering
- [x] Implement selection.get/set
- [x] Integration tests with real Maya

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

## Appendix: Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| mayapy subprocess | No bidirectional communication |
| Maya Python API | Requires running inside Maya |
| Maya REST server | Non-standard, extra complexity |
| Unix domain sockets | Windows compatibility |

Selected: **commandPort with INET socket** - See [ADR-0001](adr/0001-commandport.md)
