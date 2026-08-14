"""Maya-neutral constants shared by commandPort clients and openers."""

# The marker names keep their original Maya 2024 spelling for wire
# compatibility with already-released Sessiond and MayaMCP builds.
MAYA_2024_HANDLER_NAME = "_maya_mcp_command_port_2024"
MAYA_2024_STATE_NAME = "_maya_mcp_command_port_2024_state"
MAYA_2024_PORTS_NAME = "_maya_mcp_command_port_2024_ports"
# Covers the 1 MiB approved-script limit after worst-case JSON escaping and
# base64 framing, plus the compatibility wrapper.
MAYA_2024_COMMAND_PORT_BUFFER_SIZE = 9 * 1024 * 1024
# Slightly exceeds worst-case JSON escaping plus base64 framing for the
# approved 1 MiB script limit while remaining below the configured buffer.
MAYA_2024_REQUIRED_PROBE_SIZE = 8 * 1024 * 1024 + 1024
MAYA_LEGACY_COMPATIBILITY_VERSIONS = frozenset({"2022", "2023", "2024"})
