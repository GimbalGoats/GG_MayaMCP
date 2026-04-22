---
summary: "Product requirements, scope, goals, non-goals, current milestone status, and planned direction."
read_when:
  - When evaluating feature scope, product goals, non-goals, or roadmap fit.
  - When changing workflow coverage or documenting why a capability is in or out of scope.
---

# Product Requirements Document

**Product**: Maya MCP  
**Version**: 0.4.0  
**Status**: Active development  
**Last Updated**: 2026-04-22

## Overview

Maya MCP is a Model Context Protocol server that lets MCP-compatible clients control a running Autodesk Maya instance through Maya's `commandPort`.

The project is designed for local, AI-assisted workflows where an external MCP client needs a safe, typed, and resilient bridge into Maya.

## Problem

AI clients need a predictable way to work with Maya scenes, selections, nodes, geometry, shading, skinning, animation, and scripts.

Direct in-process integration is a poor fit because:

1. Maya runs in a separate process with its own runtime
2. Maya may be unavailable or restarted during a session
3. unrestricted execution is too risky as a default model
4. clients need stable tool contracts rather than raw Maya APIs

## Primary Goals

| ID | Goal | Success Criteria |
|----|------|------------------|
| G1 | Safe remote control | Expose explicit tools instead of default arbitrary code execution |
| G2 | Typed interfaces | All tool inputs and outputs are well-defined |
| G3 | Transport isolation | The MCP server never imports Maya modules directly |
| G4 | Recovery-oriented behavior | Maya disconnects surface as typed errors and reconnect attempts |
| G5 | Useful workflow coverage | Support real Maya workflows beyond minimal scene inspection |

## Non-Goals

| ID | Non-Goal | Rationale |
|----|----------|-----------|
| N1 | Remote host support | Security model is localhost-only |
| N2 | Full Maya API parity | The project is workflow-first, not API-complete |
| N3 | Automatic Maya process management | Out of scope for current resilience level |
| N4 | Multi-tenant remote auth model | This is a local development/server workflow |
| N5 | Arbitrary execution by default | Security risk |

## Target Users

### AI-assisted Maya users

- want natural-language or agent-driven control
- need repeatable tool behavior
- benefit from undo/redo and bounded responses

### Pipeline and tools developers

- want a typed integration surface
- need testable logic outside Maya
- need a documented transport and security model

## Functional Scope

The implemented scope currently includes:

- health and connection management
- scene open, save, import, export, undo, redo
- node creation, deletion, rename, parenting, duplication, inspection
- attribute get/set
- selection and component selection workflows
- connection and history inspection
- mesh inspection and topology checks
- viewport capture
- polygon modeling workflows
- shading workflows
- skin binding and skin-weight workflows
- animation timeline and keyframe workflows
- curve inspection
- script discovery and controlled execution
- an in-Maya control panel for `commandPort`

## Non-Functional Requirements

| Area | Requirement |
|------|-------------|
| Security | Localhost-only transport, explicit opt-in for raw execution |
| Reliability | Typed errors, retries, reconnect behavior |
| Maintainability | Strict typing, linting, tests, repo docs |
| Usability | Bounded outputs and workflow-first tool design |

## Design Principles

### Workflow first

Tools should map to practical user workflows rather than mirror every low-level Maya call.

### Transport isolation

The MCP server process must stay independent from Maya imports and communicate only through `commandPort`.

### Clear risk boundaries

Read-only and mutating operations should be separated where practical, and high-risk behavior should require explicit opt-in.

### Token-budget awareness

Large scene outputs should use limits, summaries, and pagination instead of flooding MCP clients.

## Current Milestone Summary

| Area | Status |
|------|--------|
| Core transport and health | Complete |
| Scene, node, attribute, selection workflows | Complete |
| Connections, mesh, viewport | Complete |
| Modeling, shading, skinning, animation, curves | Complete |
| Script tool trust model | Complete |
| Maya control panel | Complete |
| Further rigging/deformer/constraint expansion | Planned |

## Planned Direction

Likely next areas:

- rigging-oriented higher-level workflows
- deformer and blend shape tooling
- constraint tooling
- additional LLM-optimized output formats where justified
- production hardening features such as structured logging and auditability

## Related Documents

- [Docs Home](index.md)
- [Architecture Overview](spec/overview.md)
- [Transport Specification](spec/transport.md)
- [Security Specification](spec/security.md)
- [Tool Guide](spec/tools.md)
