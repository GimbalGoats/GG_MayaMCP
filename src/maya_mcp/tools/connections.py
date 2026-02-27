"""Connection tools for Maya MCP.

This module provides tools for querying and managing node connections
in Maya's dependency graph, including construction/deformation history.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from maya_mcp.transport import get_client
from maya_mcp.utils.parsing import parse_json_response
from maya_mcp.utils.response_guard import guard_response_size

FORBIDDEN_CHARS = frozenset([";", "|", "&", "$", "`", "\n", "\r"])

DEFAULT_CONNECTIONS_LIMIT = 500


def _validate_node_name(node: str) -> None:
    """Validate a node name for security.

    Args:
        node: The node name to validate.

    Raises:
        ValueError: If the node name is invalid or contains forbidden characters.
    """
    if not node or not isinstance(node, str):
        raise ValueError(f"Invalid node name: {node}")
    if any(c in node for c in FORBIDDEN_CHARS):
        raise ValueError(f"Invalid characters in node name: {node}")


def _validate_plug_name(plug: str) -> None:
    """Validate a plug name (node.attribute) for security.

    Args:
        plug: The plug name to validate.

    Raises:
        ValueError: If the plug name is invalid or contains forbidden characters.
    """
    if not plug or not isinstance(plug, str):
        raise ValueError(f"Invalid plug name: {plug}")
    if "." not in plug:
        raise ValueError(f"Invalid plug format: '{plug}'. Expected 'node.attribute'")
    if any(c in plug for c in FORBIDDEN_CHARS):
        raise ValueError(f"Invalid characters in plug name: {plug}")


def _validate_attribute_name(attr: str) -> None:
    """Validate an attribute name for security.

    Args:
        attr: The attribute name to validate.

    Raises:
        ValueError: If the attribute name is invalid or contains forbidden characters.
    """
    if not attr or not isinstance(attr, str):
        raise ValueError(f"Invalid attribute name: {attr}")
    if any(c in attr for c in FORBIDDEN_CHARS):
        raise ValueError(f"Invalid characters in attribute name: {attr}")


def connections_list(
    node: str,
    direction: Literal["incoming", "outgoing", "both"] = "both",
    connections_type: str | None = None,
    limit: int | None = DEFAULT_CONNECTIONS_LIMIT,
) -> dict[str, Any]:
    """List connections on a Maya node.

    Args:
        node: Node name to query connections for.
        direction: Filter by connection direction:
            - "incoming": Only connections where data flows INTO this node
            - "outgoing": Only connections where data flows FROM this node
            - "both" (default): All connections
        connections_type: Filter by connection type (e.g., "animCurve", "shader").
            If None, returns all connection types.
        limit: Maximum number of connections to return. Default 500.
            Set to 0 or None for unlimited.

    Returns:
        Dictionary with:
            - node: The queried node name
            - connections: List of connection info dicts
            - count: Number of connections returned
            - truncated: True if results were truncated (only if limit hit)
            - total_count: Total connections before limit (only if truncated)

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If node name is invalid.

    Example:
        >>> result = connections_list("pCube1", direction="incoming")
        >>> for conn in result["connections"]:
        ...     print(f"{conn['source']} -> {conn['destination']}")
    """
    _validate_node_name(node)

    client = get_client()

    node_escaped = json.dumps(node)
    direction_escaped = json.dumps(direction)
    type_escaped = json.dumps(connections_type) if connections_type else "None"
    limit_val = limit if limit and limit > 0 else 0

    command = f"""
import maya.cmds as cmds
import json

node = {node_escaped}
direction = {direction_escaped}
conn_type = {type_escaped}
limit = {limit_val}

result = {{"node": node, "connections": [], "errors": {{}}}}

if not cmds.objExists(node):
    result["errors"]["_node"] = f"Node '{{node}}' does not exist"
else:
    all_conns = []

    # Get connections based on direction
    if direction in ("incoming", "both"):
        incoming = cmds.listConnections(node, source=True, destination=False,
                                        plugs=True, connections=True) or []
        # incoming is [dest_plug, src_plug, dest_plug, src_plug, ...]
        for i in range(0, len(incoming), 2):
            dest_plug = incoming[i]
            src_plug = incoming[i + 1]
            src_node = src_plug.split(".")[0]
            src_node_type = cmds.nodeType(src_node)

            # Type filter
            if conn_type and src_node_type != conn_type:
                continue

            all_conns.append({{
                "source": src_plug,
                "source_node": src_node,
                "source_type": src_node_type,
                "destination": dest_plug,
                "destination_node": node,
                "destination_type": cmds.nodeType(node),
                "direction": "incoming"
            }})

    if direction in ("outgoing", "both"):
        outgoing = cmds.listConnections(node, source=False, destination=True,
                                        plugs=True, connections=True) or []
        # outgoing is [src_plug, dest_plug, src_plug, dest_plug, ...]
        for i in range(0, len(outgoing), 2):
            src_plug = outgoing[i]
            dest_plug = outgoing[i + 1]
            dest_node = dest_plug.split(".")[0]
            dest_node_type = cmds.nodeType(dest_node)

            # Type filter
            if conn_type and dest_node_type != conn_type:
                continue

            all_conns.append({{
                "source": src_plug,
                "source_node": node,
                "source_type": cmds.nodeType(node),
                "destination": dest_plug,
                "destination_node": dest_node,
                "destination_type": dest_node_type,
                "direction": "outgoing"
            }})

    total_count = len(all_conns)
    truncated = False

    if limit > 0 and total_count > limit:
        all_conns = all_conns[:limit]
        truncated = True

    result["connections"] = all_conns
    result["count"] = len(all_conns)

    if truncated:
        result["truncated"] = True
        result["total_count"] = total_count

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    errors = parsed.get("errors") or {}
    if "_node" in errors:
        raise ValueError(errors["_node"])

    parsed["errors"] = errors if errors else None

    parsed = guard_response_size(parsed, list_key="connections")

    return parsed


def connections_get(
    node: str,
    attributes: list[str] | None = None,
) -> dict[str, Any]:
    """Get detailed connection information for specific attributes.

    Returns connection details for each specified attribute, including
    connected plugs, connection types, and lock status.

    Args:
        node: Node name to query.
        attributes: List of attribute names to check for connections.
            If None, checks all connectable attributes.

    Returns:
        Dictionary with:
            - node: The queried node name
            - attributes: Dict mapping attribute name to connection info
            - count: Number of attributes with connections
            - errors: Map of attribute to error message, or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If node name is invalid.

    Example:
        >>> result = connections_get("pCube1", ["translateX", "visibility"])
        >>> if result["attributes"]["translateX"]["connected"]:
        ...     print(f"translateX is connected to: {{result['attributes']['translateX']['connections']}}")
    """
    _validate_node_name(node)
    if attributes:
        for attr in attributes:
            _validate_attribute_name(attr)

    client = get_client()

    node_escaped = json.dumps(node)
    attrs_escaped = json.dumps(attributes) if attributes else "None"

    command = f"""
import maya.cmds as cmds
import json

node = {node_escaped}
attrs_to_check = {attrs_escaped}

result = {{"node": node, "attributes": {{}}, "count": 0, "errors": {{}}}}

if not cmds.objExists(node):
    result["errors"]["_node"] = f"Node '{{node}}' does not exist"
else:
    # If no specific attributes, get all connectable ones
    if attrs_to_check is None:
        attrs_to_check = cmds.listAttr(node, connectable=True) or []

    connected_count = 0

    for attr in attrs_to_check:
        try:
            full_attr = f"{{node}}.{{attr}}"

            if not cmds.attributeQuery(attr, node=node, exists=True):
                result["errors"][attr] = f"Attribute '{{attr}}' not found"
                continue

            attr_info = {{
                "attribute": attr,
                "connected": False,
                "connections": [],
                "locked": cmds.getAttr(full_attr, lock=True),
                "type": cmds.getAttr(full_attr, type=True)
            }}

            # Get incoming connections
            incoming = cmds.listConnections(full_attr, source=True, destination=False,
                                            plugs=True) or []
            for src_plug in incoming:
                src_node = src_plug.split(".")[0]
                attr_info["connections"].append({{
                    "source": src_plug,
                    "source_node": src_node,
                    "source_type": cmds.nodeType(src_node),
                    "destination": full_attr,
                    "direction": "incoming"
                }})

            # Get outgoing connections
            outgoing = cmds.listConnections(full_attr, source=False, destination=True,
                                            plugs=True) or []
            for dest_plug in outgoing:
                dest_node = dest_plug.split(".")[0]
                attr_info["connections"].append({{
                    "source": full_attr,
                    "destination": dest_plug,
                    "destination_node": dest_node,
                    "destination_type": cmds.nodeType(dest_node),
                    "direction": "outgoing"
                }})

            attr_info["connected"] = len(attr_info["connections"]) > 0
            if attr_info["connected"]:
                connected_count += 1

            result["attributes"][attr] = attr_info

        except Exception as e:
            result["errors"][attr] = str(e)

    result["count"] = connected_count

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    errors = parsed.get("errors") or {}
    if "_node" in errors:
        raise ValueError(errors["_node"])

    parsed["errors"] = errors if errors else None

    return parsed


def connections_connect(
    source: str,
    destination: str,
    force: bool = False,
) -> dict[str, Any]:
    """Connect two attributes in Maya.

    Creates a connection from the source attribute to the destination attribute.
    Implements the disconnect-before-reconnect safety pattern when force=True.

    Args:
        source: Source plug in "node.attribute" format.
        destination: Destination plug in "node.attribute" format.
        force: If True, disconnect any existing connection to the destination
            before creating the new connection. If False (default), the
            operation fails if destination is already connected.

    Returns:
        Dictionary with:
            - connected: True if connection was created
            - source: The source plug
            - destination: The destination plug
            - disconnected: List of plugs that were disconnected (if force=True)
            - error: Error message if failed, or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If plug names are invalid.

    Example:
        >>> result = connections_connect("ramp1.outColor", "lambert1.color", force=True)
        >>> print(f"Connected: {{result['connected']}}")
    """
    _validate_plug_name(source)
    _validate_plug_name(destination)

    client = get_client()

    source_escaped = json.dumps(source)
    dest_escaped = json.dumps(destination)
    force_str = "True" if force else "False"

    command = f"""
import maya.cmds as cmds
import json

source_plug = {source_escaped}
dest_plug = {dest_escaped}
force_disconnect = {force_str}

result = {{
    "connected": False,
    "source": source_plug,
    "destination": dest_plug,
    "disconnected": [],
    "error": None
}}

try:
    # Validate source exists
    src_parts = source_plug.split(".")
    if len(src_parts) < 2:
        result["error"] = f"Invalid source plug format: '{{source_plug}}'. Expected 'node.attribute'"
    elif not cmds.objExists(src_parts[0]):
        result["error"] = f"Source node '{{src_parts[0]}}' does not exist"
    elif not cmds.attributeQuery(src_parts[1], node=src_parts[0], exists=True):
        result["error"] = f"Source attribute '{{src_parts[1]}}' does not exist on '{{src_parts[0]}}'"

    # Validate destination exists
    dest_parts = dest_plug.split(".")
    if result["error"] is None:
        if len(dest_parts) < 2:
            result["error"] = f"Invalid destination plug format: '{{dest_plug}}'. Expected 'node.attribute'"
        elif not cmds.objExists(dest_parts[0]):
            result["error"] = f"Destination node '{{dest_parts[0]}}' does not exist"
        elif not cmds.attributeQuery(dest_parts[1], node=dest_parts[0], exists=True):
            result["error"] = f"Destination attribute '{{dest_parts[1]}}' does not exist on '{{dest_parts[0]}}'"

    # Check if destination is locked
    if result["error"] is None:
        if cmds.getAttr(dest_plug, lock=True):
            result["error"] = f"Destination attribute '{{dest_plug}}' is locked"

    # Check for existing connections and handle force disconnect
    if result["error"] is None:
        existing_src = cmds.listConnections(dest_plug, source=True, destination=False,
                                            plugs=True) or []
        if existing_src:
            if force_disconnect:
                # Disconnect existing connections
                for existing in existing_src:
                    cmds.disconnectAttr(existing, dest_plug)
                    result["disconnected"].append(existing)
            else:
                result["error"] = f"Destination '{{dest_plug}}' is already connected to '{{existing_src[0]}}'. Use force=True to replace."

    # Create the connection
    if result["error"] is None:
        cmds.connectAttr(source_plug, dest_plug, force=False)
        result["connected"] = True

except Exception as e:
    result["error"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    return parsed


def connections_disconnect(
    source: str | None = None,
    destination: str | None = None,
) -> dict[str, Any]:
    """Disconnect attributes in Maya.

    If both source and destination are provided, disconnects that specific connection.
    If only source is provided, disconnects all outgoing connections from that plug.
    If only destination is provided, disconnects all incoming connections to that plug.

    Args:
        source: Source plug in "node.attribute" format. If None, uses destination only.
        destination: Destination plug in "node.attribute" format. If None, uses source only.

    Returns:
        Dictionary with:
            - disconnected: List of disconnected connection pairs [source, destination]
            - count: Number of connections disconnected
            - error: Error message if failed, or None

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If plug names are invalid or neither source nor destination provided.

    Example:
        >>> # Disconnect specific connection
        >>> result = connections_disconnect("ramp1.outColor", "lambert1.color")
        >>> # Disconnect all incoming connections to an attribute
        >>> result = connections_disconnect(destination="pCube1.translateX")
    """
    if source is None and destination is None:
        raise ValueError("At least one of source or destination must be provided")

    if source:
        _validate_plug_name(source)
    if destination:
        _validate_plug_name(destination)

    client = get_client()

    source_escaped = json.dumps(source) if source else "None"
    dest_escaped = json.dumps(destination) if destination else "None"

    command = f"""
import maya.cmds as cmds
import json

source_plug = {source_escaped}
dest_plug = {dest_escaped}

result = {{
    "disconnected": [],
    "count": 0,
    "error": None
}}

try:
    if source_plug and dest_plug:
        # Disconnect specific connection
        src_parts = source_plug.split(".")
        dest_parts = dest_plug.split(".")

        # Validate both plugs exist
        if not cmds.objExists(src_parts[0]):
            result["error"] = f"Source node '{{src_parts[0]}}' does not exist"
        elif not cmds.attributeQuery(src_parts[1], node=src_parts[0], exists=True):
            result["error"] = f"Source attribute '{{src_parts[1]}}' does not exist"
        elif not cmds.objExists(dest_parts[0]):
            result["error"] = f"Destination node '{{dest_parts[0]}}' does not exist"
        elif not cmds.attributeQuery(dest_parts[1], node=dest_parts[0], exists=True):
            result["error"] = f"Destination attribute '{{dest_parts[1]}}' does not exist"
        else:
            # Check if connection exists
            connected = cmds.isConnected(source_plug, dest_plug)
            if connected:
                cmds.disconnectAttr(source_plug, dest_plug)
                result["disconnected"].append({{"source": source_plug, "destination": dest_plug}})
                result["count"] = 1
            else:
                result["error"] = f"No connection exists between '{{source_plug}}' and '{{dest_plug}}'"

    elif source_plug:
        # Disconnect all outgoing from source
        src_parts = source_plug.split(".")

        if not cmds.objExists(src_parts[0]):
            result["error"] = f"Source node '{{src_parts[0]}}' does not exist"
        elif not cmds.attributeQuery(src_parts[1], node=src_parts[0], exists=True):
            result["error"] = f"Source attribute '{{src_parts[1]}}' does not exist"
        else:
            destinations = cmds.listConnections(source_plug, source=False, destination=True,
                                                plugs=True) or []
            for dest in destinations:
                cmds.disconnectAttr(source_plug, dest)
                result["disconnected"].append({{"source": source_plug, "destination": dest}})
            result["count"] = len(result["disconnected"])

    elif dest_plug:
        # Disconnect all incoming to destination
        dest_parts = dest_plug.split(".")

        if not cmds.objExists(dest_parts[0]):
            result["error"] = f"Destination node '{{dest_parts[0]}}' does not exist"
        elif not cmds.attributeQuery(dest_parts[1], node=dest_parts[0], exists=True):
            result["error"] = f"Destination attribute '{{dest_parts[1]}}' does not exist"
        else:
            sources = cmds.listConnections(dest_plug, source=True, destination=False,
                                           plugs=True) or []
            for src in sources:
                cmds.disconnectAttr(src, dest_plug)
                result["disconnected"].append({{"source": src, "destination": dest_plug}})
            result["count"] = len(result["disconnected"])

except Exception as e:
    result["error"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    return parsed


def connections_history(
    node: str,
    direction: Literal["input", "output", "both"] = "input",
    depth: int = 10,
    limit: int | None = DEFAULT_CONNECTIONS_LIMIT,
) -> dict[str, Any]:
    """List construction/deformation history on a node.

    Traverses the dependency graph to find upstream (input) or downstream (output)
    history nodes such as deformers, construction history, shaders, etc.

    Args:
        node: Node name to query history for.
        direction: Direction to traverse:
            - "input" (default): Upstream history (construction/deformation inputs)
            - "output": Downstream history (what this node affects)
            - "both": Both directions
        depth: Maximum depth to traverse. Default 10.
        limit: Maximum number of history nodes to return. Default 500.

    Returns:
        Dictionary with:
            - node: The queried node name
            - history: List of history node info dicts with name, type, depth, direction
            - count: Number of history nodes returned
            - truncated: True if results were truncated
            - total_count: Total history nodes before limit

    Raises:
        MayaUnavailableError: If not connected to Maya.
        MayaCommandError: If Maya command execution fails.
        ValueError: If node name is invalid.

    Example:
        >>> result = connections_history("pCubeShape1", direction="input")
        >>> for hist in result["history"]:
        ...     print(f"{{hist['type']}}: {{hist['name']}} (depth {{hist['depth']}})")
    """
    _validate_node_name(node)

    client = get_client()

    node_escaped = json.dumps(node)
    direction_escaped = json.dumps(direction)
    depth_val = max(1, min(depth, 50))
    limit_val = limit if limit and limit > 0 else 0

    command = f"""
import maya.cmds as cmds
import json

node = {node_escaped}
direction = {direction_escaped}
max_depth = {depth_val}
limit = {limit_val}

result = {{"node": node, "history": [], "errors": {{}}}}

if not cmds.objExists(node):
    result["errors"]["_node"] = f"Node '{{node}}' does not exist"
else:
    all_history = []

    # Get upstream (input) history
    if direction in ("input", "both"):
        upstream = cmds.listHistory(node, future=False, levels=max_depth, pruneDagObjects=True) or []
        for i, hist_node in enumerate(upstream):
            if hist_node != node:
                all_history.append({{
                    "name": hist_node,
                    "type": cmds.nodeType(hist_node),
                    "depth": i + 1,
                    "direction": "input"
                }})

    # Get downstream (output) history
    if direction in ("output", "both"):
        downstream = cmds.listHistory(node, future=True, levels=max_depth, pruneDagObjects=True) or []
        for i, hist_node in enumerate(downstream):
            if hist_node != node:
                all_history.append({{
                    "name": hist_node,
                    "type": cmds.nodeType(hist_node),
                    "depth": i + 1,
                    "direction": "output"
                }})

    # Sort by depth, then by name
    all_history.sort(key=lambda x: (x["depth"], x["name"]))

    total_count = len(all_history)
    truncated = False

    if limit > 0 and total_count > limit:
        all_history = all_history[:limit]
        truncated = True

    result["history"] = all_history
    result["count"] = len(all_history)

    if truncated:
        result["truncated"] = True
        result["total_count"] = total_count

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    errors = parsed.get("errors") or {}
    if "_node" in errors:
        raise ValueError(errors["_node"])

    parsed["errors"] = errors if errors else None

    parsed = guard_response_size(parsed, list_key="history")

    return parsed
