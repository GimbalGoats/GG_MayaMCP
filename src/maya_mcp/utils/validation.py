"""Shared input validation utilities for Maya MCP.

This module provides centralized validation functions and constants
used across all tool modules to prevent code duplication.
"""

from __future__ import annotations

# Characters forbidden in node names (shell metacharacters + control chars)
FORBIDDEN_NODE_CHARS = frozenset([";", "|", "&", "$", "`", "\n", "\r"])

# Characters forbidden in patterns (superset of node chars + quotes)
FORBIDDEN_PATTERN_CHARS = frozenset([";", "|", "&", "$", "`", "\n", "\r", '"', "'"])

# Characters forbidden in file paths
FORBIDDEN_PATH_CHARS = ";|&$`"


def validate_node_name(node: str) -> None:
    """Validate a node name for security.

    Args:
        node: The node name to validate.

    Raises:
        ValueError: If the node name is invalid or contains forbidden characters.
    """
    if not node or not isinstance(node, str):
        raise ValueError(f"Invalid node name: {node}")
    if any(c in node for c in FORBIDDEN_NODE_CHARS):
        raise ValueError(f"Invalid characters in node name: {node}")


def validate_attribute_name(attr: str) -> None:
    """Validate an attribute name for security.

    Args:
        attr: The attribute name to validate.

    Raises:
        ValueError: If the attribute name is invalid or contains forbidden characters.
    """
    if not attr or not isinstance(attr, str):
        raise ValueError(f"Invalid attribute name: {attr}")
    if any(c in attr for c in FORBIDDEN_NODE_CHARS):
        raise ValueError(f"Invalid characters in attribute name: {attr}")


def validate_plug_name(plug: str) -> None:
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
    if any(c in plug for c in FORBIDDEN_NODE_CHARS):
        raise ValueError(f"Invalid characters in plug name: {plug}")


def validate_pattern(pattern: str) -> None:
    """Validate a node name pattern for security.

    Args:
        pattern: The pattern to validate.

    Raises:
        ValueError: If the pattern contains forbidden characters.
    """
    if any(c in pattern for c in FORBIDDEN_PATTERN_CHARS):
        raise ValueError(f"Invalid characters in pattern: {pattern}")


def validate_component_name(component: str) -> None:
    """Validate a component specification for security.

    Component syntax uses ``[``, ``]``, ``:``, and ``.`` characters
    (e.g., ``pCube1.vtx[0:10]``). These are allowed but shell
    metacharacters are still blocked.

    Args:
        component: The component specification to validate.

    Raises:
        ValueError: If the component contains forbidden characters.
    """
    if not component or not isinstance(component, str):
        raise ValueError(f"Invalid component specification: {component}")
    if any(c in component for c in FORBIDDEN_NODE_CHARS):
        raise ValueError(f"Invalid characters in component specification: {component}")
