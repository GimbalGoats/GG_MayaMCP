"""Shading and material tools for Maya MCP.

This module provides tools for creating materials, assigning them
to meshes or face components, and setting material attributes.
"""

from __future__ import annotations

import json
from typing import Any, Literal, cast

from typing_extensions import TypedDict

from maya_mcp.transport import get_client
from maya_mcp.utils.parsing import parse_json_response
from maya_mcp.utils.validation import validate_node_name as _validate_node_name

VALID_MATERIAL_TYPES = {"lambert", "blinn", "phong", "standardSurface"}


class ShadingCreateMaterialOutput(TypedDict):
    """Return payload for the shading.create_material tool."""

    material: str | None
    shading_group: str | None
    material_type: Literal["lambert", "blinn", "phong", "standardSurface"]
    errors: dict[str, str] | None


class ShadingAssignMaterialOutput(TypedDict):
    """Return payload for the shading.assign_material tool."""

    assigned: list[str]
    material: str
    shading_group: str | None
    errors: dict[str, str] | None


class ShadingSetMaterialColorOutput(TypedDict):
    """Return payload for the shading.set_material_color tool."""

    material: str
    attribute: str
    color: list[float]
    errors: dict[str, str] | None


def shading_create_material(
    material_type: Literal["lambert", "blinn", "phong", "standardSurface"] = "lambert",
    name: str | None = None,
    color: list[float] | None = None,
) -> ShadingCreateMaterialOutput:
    """Create a new material with an associated shading group.

    Args:
        material_type: Type of material shader to create.
        name: Optional name for the material node.
        color: Optional [r, g, b] color values (0-1 range).

    Returns:
        Dictionary with material, shading_group, material_type, and errors.

    Raises:
        ValueError: If material_type is invalid, name contains invalid
            characters, or color is not a list of 3 floats.
    """
    if material_type not in VALID_MATERIAL_TYPES:
        raise ValueError(
            f"Invalid material_type: {material_type!r}. "
            f"Must be one of: {', '.join(sorted(VALID_MATERIAL_TYPES))}"
        )
    if name is not None:
        _validate_node_name(name)
    if color is not None and (not isinstance(color, list) or len(color) != 3):
        raise ValueError("color must be a list of 3 floats [r, g, b]")

    client = get_client()
    mtype_escaped = json.dumps(material_type)
    name_escaped = json.dumps(name) if name is not None else "None"
    color_escaped = json.dumps([float(c) for c in color]) if color is not None else "None"

    command = f"""
import maya.cmds as cmds
import json

mtype = {mtype_escaped}
name = {name_escaped}
color = {color_escaped}

result = {{"material": None, "shading_group": None, "material_type": mtype, "errors": {{}}}}

try:
    kwargs = {{"asShader": True}}
    if name:
        kwargs["name"] = name

    mat = cmds.shadingNode(mtype, **kwargs)
    result["material"] = mat

    # Create shading group
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=mat + "SG")
    result["shading_group"] = sg

    # Connect material to shading group
    cmds.connectAttr(mat + ".outColor", sg + ".surfaceShader", force=True)

    # Set color if provided
    if color:
        if mtype == "standardSurface":
            cmds.setAttr(mat + ".baseColor", color[0], color[1], color[2], type="double3")
        else:
            cmds.setAttr(mat + ".color", color[0], color[1], color[2], type="double3")

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return cast("ShadingCreateMaterialOutput", parsed)


def shading_assign_material(
    targets: list[str],
    material: str,
) -> ShadingAssignMaterialOutput:
    """Assign a material to meshes or face components.

    Resolves the material's shading group automatically. Accepts
    both material names and shading group names.

    Args:
        targets: List of mesh names or face component strings to assign to.
        material: Name of the material (or shading group) to assign.

    Returns:
        Dictionary with assigned list, material, shading_group, and errors.

    Raises:
        ValueError: If targets list is empty or material name contains
            invalid characters.
    """
    if not targets:
        raise ValueError("targets list cannot be empty")
    _validate_node_name(material)

    client = get_client()
    targets_escaped = json.dumps(targets)
    material_escaped = json.dumps(material)

    command = f"""
import maya.cmds as cmds
import json

targets = {targets_escaped}
material = {material_escaped}

result = {{"assigned": [], "material": material, "shading_group": None, "errors": {{}}}}

try:
    if not cmds.objExists(material):
        result["errors"]["_material"] = "Node '" + material + "' does not exist"
    else:
        node_type = cmds.nodeType(material)

        # Determine the shading group
        sg = None
        if node_type == "shadingEngine":
            sg = material
        else:
            # Find connected shading group
            connections = cmds.listConnections(material + ".outColor", type="shadingEngine") or []
            if connections:
                sg = connections[0]
            else:
                result["errors"]["_sg"] = "No shading group found for material '" + material + "'"

        if sg:
            result["shading_group"] = sg
            assigned = []
            for target in targets:
                if not cmds.objExists(target):
                    result["errors"][target] = "Target does not exist: " + target
                else:
                    cmds.sets(target, forceElement=sg)
                    assigned.append(target)
            result["assigned"] = assigned

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return cast("ShadingAssignMaterialOutput", parsed)


def shading_set_material_color(
    material: str,
    color: list[float],
    attribute: str = "color",
) -> ShadingSetMaterialColorOutput:
    """Set a color attribute on a material.

    Args:
        material: Name of the material node.
        color: [r, g, b] color values (0-1 range).
        attribute: Color attribute name (default "color"). Common values:
            - "color": Diffuse color (lambert/blinn/phong)
            - "baseColor": Base color (standardSurface)
            - "transparency": Transparency color
            - "incandescence": Incandescence color

    Returns:
        Dictionary with material, attribute, color, and errors.

    Raises:
        ValueError: If material name contains invalid characters or
            color is not a list of 3 floats.
    """
    _validate_node_name(material)
    if not isinstance(color, list) or len(color) != 3:
        raise ValueError("color must be a list of 3 floats [r, g, b]")

    client = get_client()
    material_escaped = json.dumps(material)
    color_escaped = json.dumps([float(c) for c in color])
    attr_escaped = json.dumps(attribute)

    command = f"""
import maya.cmds as cmds
import json

material = {material_escaped}
color = {color_escaped}
attr = {attr_escaped}

result = {{"material": material, "attribute": attr, "color": color, "errors": {{}}}}

try:
    if not cmds.objExists(material):
        result["errors"]["_material"] = "Node '" + material + "' does not exist"
    else:
        full_attr = material + "." + attr
        if not cmds.attributeQuery(attr, node=material, exists=True):
            result["errors"]["_attribute"] = "Attribute '" + attr + "' does not exist on '" + material + "'"
        else:
            cmds.setAttr(full_attr, color[0], color[1], color[2], type="double3")

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return cast("ShadingSetMaterialColorOutput", parsed)
