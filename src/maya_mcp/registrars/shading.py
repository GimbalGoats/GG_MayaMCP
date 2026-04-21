"""Registrar for shading tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal

from mcp.types import ToolAnnotations

from maya_mcp.tools.shading import (
    ShadingAssignMaterialOutput,
    ShadingCreateMaterialOutput,
    ShadingSetMaterialColorOutput,
    shading_assign_material,
    shading_create_material,
    shading_set_material_color,
)
from maya_mcp.utils.coercion import coerce_list

if TYPE_CHECKING:
    from fastmcp import FastMCP


def tool_shading_create_material(
    material_type: Annotated[
        Literal["lambert", "blinn", "phong", "standardSurface"],
        "Type of material shader to create",
    ] = "lambert",
    name: Annotated[str | None, "Optional name for the material node"] = None,
    color: Annotated[list[float] | None, "Optional [r, g, b] color (0-1 range)"] = None,
) -> ShadingCreateMaterialOutput:
    """Create a new material with shading group.

    Args:
        material_type: Type of material shader.
        name: Optional name.
        color: Optional [r, g, b] color.

    Returns:
        Dictionary with material, shading_group, material_type, and errors.
    """
    return shading_create_material(material_type=material_type, name=name, color=coerce_list(color))


def tool_shading_assign_material(
    targets: Annotated[list[str], "Meshes or face components to assign the material to"],
    material: Annotated[str, "Name of the material (or shading group) to assign"],
) -> ShadingAssignMaterialOutput:
    """Assign a material to targets.

    Args:
        targets: Meshes or face components.
        material: Material or shading group name.

    Returns:
        Dictionary with assigned list, material, shading_group, and errors.
    """
    return shading_assign_material(
        targets=coerce_list(targets),
        material=material,
    )


def tool_shading_set_material_color(
    material: Annotated[str, "Name of the material node"],
    color: Annotated[list[float], "[r, g, b] color values (0-1 range)"],
    attribute: Annotated[
        str,
        "Color attribute name (e.g., 'color', 'baseColor', 'transparency', 'incandescence')",
    ] = "color",
) -> ShadingSetMaterialColorOutput:
    """Set a color attribute on a material.

    Args:
        material: Material node name.
        color: [r, g, b] color values.
        attribute: Color attribute name.

    Returns:
        Dictionary with material, attribute, color, and errors.
    """
    return shading_set_material_color(
        material=material,
        color=coerce_list(color),
        attribute=attribute,
    )


def register_shading_tools(mcp: FastMCP) -> None:
    """Register shading tools."""
    mcp.tool(
        name="shading.create_material",
        description="Create a material (lambert, blinn, phong, standardSurface) "
        "with an associated shading group and optional color.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_shading_create_material)

    mcp.tool(
        name="shading.assign_material",
        description="Assign a material to meshes or face components. "
        "Resolves the shading group from the material automatically.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_shading_assign_material)

    mcp.tool(
        name="shading.set_material_color",
        description="Set a color attribute on a material (e.g., color, baseColor, transparency).",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_shading_set_material_color)
