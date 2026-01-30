# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial project scaffold
- FastMCP server with tool registration
- Maya commandPort transport layer with:
  - Connect/request timeouts
  - Bounded retry with exponential backoff
  - Automatic reconnection on next call
- Core tools:
  - `health.check` - Connection health monitoring
  - `maya.connect` - Manual connection establishment
  - `maya.disconnect` - Manual connection teardown
  - `scene.info` - Scene information retrieval (stub)
  - `nodes.list` - Node listing by type (stub)
  - `selection.get` - Selection query (stub)
  - `selection.set` - Selection modification (stub)
- Typed error hierarchy with `MayaMCPError` base class
- Level 1 resilience (detect unavailable, return error, recover on restart)
- MkDocs documentation with mkdocstrings
- Comprehensive test suite with mocked transport

### Security

- Localhost-only commandPort connection by default
- No arbitrary code execution - all operations are explicit tools
- No raw Python/MEL string evaluation exposed to clients

## [0.1.0] - TBD

Initial release.

[Unreleased]: https://github.com/your-org/maya-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/maya-mcp/releases/tag/v0.1.0
