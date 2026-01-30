# Security Specification

This document describes the security model and considerations for Maya MCP.

## Threat Model

### Assets to Protect

| Asset | Sensitivity | Protection Goal |
|-------|-------------|-----------------|
| Maya scene data | Medium | Prevent unauthorized access |
| System access | High | Prevent arbitrary code execution |
| User credentials | High | Never expose or transmit |
| File system | High | Prevent unauthorized file access |

### Trust Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                    User's Machine (Trusted)                      │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │  MCP Client  │◄──►│  MCP Server  │◄──►│      Maya        │   │
│  │  (trusted)   │    │  (trusted)   │    │   (trusted)      │   │
│  └──────────────┘    └──────────────┘    └──────────────────┘   │
│         │                   │                     │              │
│         └───────────────────┼─────────────────────┘              │
│                             │                                    │
│              Trust boundary: All on localhost                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Network boundary
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Network (Untrusted)                  │
└─────────────────────────────────────────────────────────────────┘
```

### Threat Actors

| Actor | Capability | Mitigation |
|-------|------------|------------|
| Remote attacker | Network access | Localhost-only binding |
| Malicious MCP client | Local access, MCP protocol | Tool allowlist, no arbitrary code |
| Compromised plugin | Maya process access | Out of scope (Maya's responsibility) |

## Security Controls

### 1. Localhost-Only Connections

**Control**: The MCP server only connects to Maya on `localhost`/`127.0.0.1`.

**Implementation**:

```python
DEFAULT_HOST = "localhost"

def __init__(self, host: str = DEFAULT_HOST, ...):
    if host not in ("localhost", "127.0.0.1"):
        raise ValueError("Only localhost connections are supported")
```

**Rationale**: Prevents network-based attacks. Maya commandPort has no authentication, so network exposure would allow any process to execute commands.

### 2. No Arbitrary Code Execution

**Control**: MCP tools execute predefined operations, not arbitrary Python/MEL strings.

**Implementation**:

```python
# GOOD: Predefined operation with validated parameters
@mcp.tool
def list_nodes(node_type: str) -> list[str]:
    validated_type = validate_node_type(node_type)
    return client.execute(f"cmds.ls(type='{validated_type}')")

# BAD: Never expose arbitrary code execution
@mcp.tool
def execute_code(code: str) -> str:  # DO NOT DO THIS
    return client.execute(code)
```

**Rationale**: Arbitrary code execution would allow:
- System commands via `os.system()`, `subprocess`
- File system access
- Network exfiltration
- Maya crash/corruption

### 3. Input Validation

**Control**: All tool inputs are validated before use.

**Implementation**:

```python
from pydantic import BaseModel, Field, validator

class NodeListInput(BaseModel):
    node_type: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9]*$")
    pattern: str = Field(max_length=256)
    
    @validator("pattern")
    def validate_pattern(cls, v):
        # Disallow shell-like patterns
        if any(c in v for c in [";", "|", "&", "$", "`"]):
            raise ValueError("Invalid characters in pattern")
        return v
```

**Rationale**: Prevents injection attacks through tool parameters.

### 4. Error Sanitization

**Control**: Error messages never expose sensitive information.

**Implementation**:

```python
class MayaMCPError(Exception):
    def __init__(self, message: str, ...):
        # Sanitize paths - replace user home with ~
        sanitized = message.replace(os.path.expanduser("~"), "~")
        # Never include raw tracebacks in client-facing errors
        self.message = sanitized
```

**Rationale**: Prevents information disclosure through error messages.

## Maya commandPort Security

### Native Security Features

Maya's commandPort has limited security features:

| Feature | Description | Our Usage |
|---------|-------------|-----------|
| `prefix` | Require command prefix | Not used (tools are explicit) |
| `securityWarning` | Log security warnings | Recommended for development |

### Recommended Maya Configuration

```python
import maya.cmds as cmds

# Development: enable warnings
cmds.commandPort(
    name=":7001",
    sourceType="python",
    echoOutput=True,
    securityWarning=True,  # Log when commands are received
)

# Production: consider prefix for defense-in-depth
cmds.commandPort(
    name=":7001",
    sourceType="python",
    echoOutput=True,
    prefix="mayamcp_",  # All commands must start with this
)
```

### Maya commandPort Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| No authentication | High | Localhost-only |
| Any command can be executed | High | MCP tools are explicit |
| `system()` calls possible | Critical | No arbitrary code exposure |
| File access possible | High | Tools don't expose file paths as inputs |

## Security Best Practices

### For Users

1. **Only run Maya MCP locally** - Never expose ports to network
2. **Trust your MCP clients** - They can invoke any exposed tool
3. **Keep Maya updated** - Security patches apply to commandPort
4. **Monitor commandPort activity** - Enable `securityWarning` in dev

### For Developers

1. **Never add arbitrary code execution tools**
2. **Validate all string inputs** - Assume injection attempts
3. **Use allowlists, not blocklists** - For node types, commands, etc.
4. **Sanitize error messages** - No paths, no stack traces
5. **Test with malicious inputs** - Fuzz testing recommended

## Security Checklist

Before deploying:

- [ ] Confirm localhost-only binding
- [ ] Verify no arbitrary code execution tools
- [ ] Review all string inputs for injection
- [ ] Check error messages for info disclosure
- [ ] Test with malformed/malicious inputs
- [ ] Document any security assumptions

## Future Considerations

### v1+ Security Enhancements

| Feature | Description | Priority |
|---------|-------------|----------|
| Command allowlist | Only permit specific Maya commands | Medium |
| Rate limiting | Prevent DoS via rapid requests | Low |
| Audit logging | Log all tool invocations | Medium |
| Auth token | Require token for connection | Low (localhost negates need) |

## Incident Response

### If Security Issue Found

1. **Do not expose details publicly**
2. Contact maintainers via security email
3. Provide:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Known Limitations (Not Vulnerabilities)

| Limitation | Status | Rationale |
|------------|--------|-----------|
| No encryption (plaintext TCP) | Accepted | Localhost-only, same-machine |
| No authentication | Accepted | Localhost-only, process isolation |
| Maya can execute system commands | Accepted | Maya's design, not MCP's exposure |
