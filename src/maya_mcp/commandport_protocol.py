"""Maya-neutral constants shared by commandPort clients and openers."""

MAYA_2024_HANDLER_NAME = "_maya_mcp_command_port_2024"
MAYA_2024_STATE_NAME = "_maya_mcp_command_port_2024_state"
MAYA_2024_PORTS_NAME = "_maya_mcp_command_port_2024_ports"
# Covers the 1 MiB approved-script limit after worst-case JSON escaping and
# base64 framing, plus the compatibility wrapper.
MAYA_2024_COMMAND_PORT_BUFFER_SIZE = 9 * 1024 * 1024
