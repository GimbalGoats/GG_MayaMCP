"""Registrar for modeling tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal

from mcp.types import ToolAnnotations

from maya_mcp.tools.modeling import (
    ModelingBevelOutput,
    ModelingBooleanOutput,
    ModelingBridgeOutput,
    ModelingCenterPivotOutput,
    ModelingCombineOutput,
    ModelingCreatePolygonPrimitiveOutput,
    ModelingDeleteFacesOutput,
    ModelingDeleteHistoryOutput,
    ModelingExtrudeFacesOutput,
    ModelingFreezeTransformsOutput,
    ModelingInsertEdgeLoopOutput,
    ModelingMergeVerticesOutput,
    ModelingMoveComponentsOutput,
    ModelingSeparateOutput,
    ModelingSetPivotOutput,
    modeling_bevel,
    modeling_boolean,
    modeling_bridge,
    modeling_center_pivot,
    modeling_combine,
    modeling_create_polygon_primitive,
    modeling_delete_faces,
    modeling_delete_history,
    modeling_extrude_faces,
    modeling_freeze_transforms,
    modeling_insert_edge_loop,
    modeling_merge_vertices,
    modeling_move_components,
    modeling_separate,
    modeling_set_pivot,
)
from maya_mcp.utils.coercion import coerce_list

if TYPE_CHECKING:
    from fastmcp import FastMCP


def tool_modeling_create_polygon_primitive(
    primitive_type: Annotated[
        Literal["cube", "sphere", "cylinder", "cone", "torus", "plane"],
        "Type of primitive to create",
    ],
    name: Annotated[str | None, "Optional name for the transform node"] = None,
    width: Annotated[float, "Width (cube/plane)"] = 1.0,
    height: Annotated[float, "Height (cube/cylinder/cone/plane)"] = 1.0,
    depth: Annotated[float, "Depth (cube)"] = 1.0,
    radius: Annotated[float, "Radius (sphere/cylinder/cone/torus)"] = 0.5,
    subdivisions_width: Annotated[int | None, "Width subdivisions"] = None,
    subdivisions_height: Annotated[int | None, "Height subdivisions"] = None,
    subdivisions_depth: Annotated[int | None, "Depth subdivisions"] = None,
    subdivisions_axis: Annotated[
        int | None, "Axis subdivisions (sphere/cylinder/cone/torus)"
    ] = None,
    axis: Annotated[Literal["x", "y", "z"], "Up axis for the primitive"] = "y",
) -> ModelingCreatePolygonPrimitiveOutput:
    """Create a polygon primitive.

    Args:
        primitive_type: Type of primitive to create.
        name: Optional name for the transform node.
        width: Width of the primitive.
        height: Height of the primitive.
        depth: Depth of the primitive.
        radius: Radius of the primitive.
        subdivisions_width: Width subdivisions.
        subdivisions_height: Height subdivisions.
        subdivisions_depth: Depth subdivisions.
        subdivisions_axis: Axis subdivisions.
        axis: Up axis.

    Returns:
        Dictionary with transform, shape, constructor, primitive_type,
        vertex_count, face_count, and errors.
    """
    return modeling_create_polygon_primitive(
        primitive_type=primitive_type,
        name=name,
        width=width,
        height=height,
        depth=depth,
        radius=radius,
        subdivisions_width=subdivisions_width,
        subdivisions_height=subdivisions_height,
        subdivisions_depth=subdivisions_depth,
        subdivisions_axis=subdivisions_axis,
        axis=axis,
    )


def tool_modeling_extrude_faces(
    faces: Annotated[
        list[str], "Face components to extrude (e.g., ['pCube1.f[0]', 'pCube1.f[2]'])"
    ],
    local_translate_z: Annotated[float | None, "Local Z translation (extrusion thickness)"] = None,
    local_translate_x: Annotated[float | None, "Local X translation"] = None,
    local_translate_y: Annotated[float | None, "Local Y translation"] = None,
    offset: Annotated[float | None, "Offset amount for the extrusion"] = None,
    divisions: Annotated[int, "Number of extrusion divisions"] = 1,
    keep_faces_together: Annotated[bool, "Keep faces together during extrusion"] = True,
) -> ModelingExtrudeFacesOutput:
    """Extrude polygon faces.

    Args:
        faces: Face component strings to extrude.
        local_translate_z: Local Z translation.
        local_translate_x: Local X translation.
        local_translate_y: Local Y translation.
        offset: Offset amount.
        divisions: Number of divisions.
        keep_faces_together: Keep faces together.

    Returns:
        Dictionary with node, faces_extruded, new_face_count, and errors.
    """
    return modeling_extrude_faces(
        faces=coerce_list(faces),
        local_translate_z=local_translate_z,
        local_translate_x=local_translate_x,
        local_translate_y=local_translate_y,
        offset=offset,
        divisions=divisions,
        keep_faces_together=keep_faces_together,
    )


def tool_modeling_boolean(
    mesh_a: Annotated[str, "First mesh (base)"],
    mesh_b: Annotated[str, "Second mesh (operand)"],
    operation: Annotated[
        Literal["union", "difference", "intersection"],
        "Boolean operation type",
    ] = "union",
) -> ModelingBooleanOutput:
    """Perform a boolean operation on two meshes.

    Args:
        mesh_a: First mesh.
        mesh_b: Second mesh.
        operation: Boolean operation type.

    Returns:
        Dictionary with result_mesh, operation, vertex_count, face_count, and errors.
    """
    return modeling_boolean(mesh_a=mesh_a, mesh_b=mesh_b, operation=operation)


def tool_modeling_combine(
    meshes: Annotated[list[str], "List of mesh names to combine (minimum 2)"],
    name: Annotated[str | None, "Optional name for the combined mesh"] = None,
) -> ModelingCombineOutput:
    """Combine multiple meshes into one.

    Args:
        meshes: List of mesh names to combine.
        name: Optional name for the result.

    Returns:
        Dictionary with result_mesh, source_meshes, vertex_count, face_count, and errors.
    """
    return modeling_combine(meshes=coerce_list(meshes), name=name)


def tool_modeling_separate(
    mesh: Annotated[str, "Name of the mesh to separate"],
) -> ModelingSeparateOutput:
    """Separate a combined mesh into individual meshes.

    Args:
        mesh: Name of the mesh to separate.

    Returns:
        Dictionary with source_mesh, result_meshes, count, and errors.
    """
    return modeling_separate(mesh=mesh)


def tool_modeling_merge_vertices(
    mesh: Annotated[str, "Name of the mesh"],
    threshold: Annotated[float, "Distance threshold for merging (default 0.001)"] = 0.001,
    vertices: Annotated[
        list[str] | None,
        "Optional specific vertex components to merge (None = all vertices)",
    ] = None,
) -> ModelingMergeVerticesOutput:
    """Merge vertices within a distance threshold.

    Args:
        mesh: Name of the mesh.
        threshold: Distance threshold.
        vertices: Optional specific vertices.

    Returns:
        Dictionary with mesh, vertices_merged, vertex_count_before,
        vertex_count_after, and errors.
    """
    return modeling_merge_vertices(mesh=mesh, threshold=threshold, vertices=coerce_list(vertices))


def tool_modeling_bevel(
    components: Annotated[
        list[str], "Edge or vertex components to bevel (e.g., ['pCube1.e[0:3]'])"
    ],
    offset: Annotated[float, "Bevel offset distance (default 0.5)"] = 0.5,
    segments: Annotated[int, "Number of bevel segments (default 1)"] = 1,
    fraction: Annotated[float, "Bevel fraction (default 0.5)"] = 0.5,
) -> ModelingBevelOutput:
    """Bevel edges or vertices.

    Args:
        components: Edge or vertex components to bevel.
        offset: Bevel offset distance.
        segments: Number of segments.
        fraction: Bevel fraction.

    Returns:
        Dictionary with node, components_beveled, new_vertex_count,
        new_face_count, and errors.
    """
    return modeling_bevel(
        components=coerce_list(components),
        offset=offset,
        segments=segments,
        fraction=fraction,
    )


def tool_modeling_bridge(
    edge_loops: Annotated[list[str], "Edge components for the edge loops to bridge"],
    divisions: Annotated[int, "Number of divisions in the bridge (default 0)"] = 0,
    twist: Annotated[int, "Twist amount (default 0)"] = 0,
    taper: Annotated[float, "Taper amount (default 1.0)"] = 1.0,
) -> ModelingBridgeOutput:
    """Bridge between edge loops.

    Args:
        edge_loops: Edge components to bridge.
        divisions: Number of divisions.
        twist: Twist amount.
        taper: Taper amount.

    Returns:
        Dictionary with node, new_face_count, and errors.
    """
    return modeling_bridge(
        edge_loops=coerce_list(edge_loops),
        divisions=divisions,
        twist=twist,
        taper=taper,
    )


def tool_modeling_insert_edge_loop(
    edge: Annotated[str, "Single edge component (e.g., 'pCube1.e[4]')"],
    divisions: Annotated[int, "Number of edge loops to insert (default 1)"] = 1,
    weight: Annotated[float, "Position weight along the edge (0-1, default 0.5)"] = 0.5,
) -> ModelingInsertEdgeLoopOutput:
    """Insert an edge loop.

    Args:
        edge: Single edge component.
        divisions: Number of edge loops.
        weight: Position weight.

    Returns:
        Dictionary with node, edge, new_edge_count, new_vertex_count, and errors.
    """
    return modeling_insert_edge_loop(edge=edge, divisions=divisions, weight=weight)


def tool_modeling_delete_faces(
    faces: Annotated[list[str], "Face components to delete (e.g., ['pCube1.f[0]', 'pCube1.f[3]'])"],
) -> ModelingDeleteFacesOutput:
    """Delete polygon faces.

    Args:
        faces: Face component strings to delete.

    Returns:
        Dictionary with faces_deleted, mesh, remaining_face_count, and errors.
    """
    return modeling_delete_faces(faces=coerce_list(faces))


def tool_modeling_move_components(
    components: Annotated[list[str], "Component strings to move (e.g., ['pCube1.vtx[0:3]'])"],
    translate: Annotated[
        list[float] | None,
        "Relative [x, y, z] translation (mutually exclusive with absolute)",
    ] = None,
    absolute: Annotated[
        list[float] | None,
        "Absolute [x, y, z] position (mutually exclusive with translate)",
    ] = None,
    world_space: Annotated[bool, "Use world space coordinates (default True)"] = True,
) -> ModelingMoveComponentsOutput:
    """Move mesh components.

    Exactly one of translate or absolute must be provided.

    Args:
        components: Component strings to move.
        translate: Relative translation.
        absolute: Absolute position.
        world_space: Use world space.

    Returns:
        Dictionary with components_moved, translate/absolute, world_space, and errors.
    """
    return modeling_move_components(
        components=coerce_list(components),
        translate=coerce_list(translate),
        absolute=coerce_list(absolute),
        world_space=world_space,
    )


def tool_modeling_freeze_transforms(
    nodes: Annotated[list[str], "Node names to freeze transforms on"],
    translate: Annotated[bool, "Freeze translation (default True)"] = True,
    rotate: Annotated[bool, "Freeze rotation (default True)"] = True,
    scale: Annotated[bool, "Freeze scale (default True)"] = True,
) -> ModelingFreezeTransformsOutput:
    """Freeze transforms on nodes.

    Args:
        nodes: Node names to freeze.
        translate: Freeze translation.
        rotate: Freeze rotation.
        scale: Freeze scale.

    Returns:
        Dictionary with frozen list, count, and errors.
    """
    return modeling_freeze_transforms(
        nodes=coerce_list(nodes),
        translate=translate,
        rotate=rotate,
        scale=scale,
    )


def tool_modeling_delete_history(
    nodes: Annotated[list[str] | None, "Node names to delete history from"] = None,
    all_nodes: Annotated[bool, "If True, delete history from all nodes in the scene"] = False,
) -> ModelingDeleteHistoryOutput:
    """Delete construction history.

    Args:
        nodes: Node names to clean, or None if all_nodes is True.
        all_nodes: Delete history from all scene nodes.

    Returns:
        Dictionary with cleaned list, count, and errors.
    """
    return modeling_delete_history(nodes=coerce_list(nodes), all_nodes=all_nodes)


def tool_modeling_center_pivot(
    nodes: Annotated[list[str], "Node names to center pivots on"],
) -> ModelingCenterPivotOutput:
    """Center pivot on nodes.

    Args:
        nodes: Node names to center pivots on.

    Returns:
        Dictionary with centered list, count, pivot_positions, and errors.
    """
    return modeling_center_pivot(nodes=coerce_list(nodes))


def tool_modeling_set_pivot(
    node: Annotated[str, "Node name to set pivot on"],
    position: Annotated[list[float], "[x, y, z] position for the pivot"],
    world_space: Annotated[bool, "Position is in world space (default True)"] = True,
) -> ModelingSetPivotOutput:
    """Set the pivot point of a node.

    Args:
        node: Node name.
        position: [x, y, z] position.
        world_space: Use world space.

    Returns:
        Dictionary with node, pivot, world_space, and errors.
    """
    return modeling_set_pivot(
        node=node,
        position=coerce_list(position),
        world_space=world_space,
    )


def register_modeling_tools(mcp: FastMCP) -> None:
    """Register modeling tools."""
    mcp.tool(
        name="modeling.create_polygon_primitive",
        description="Create a polygon primitive (cube, sphere, cylinder, cone, torus, plane) "
        "with configurable dimensions, subdivisions, and axis.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_modeling_create_polygon_primitive)

    mcp.tool(
        name="modeling.extrude_faces",
        description="Extrude polygon faces with local translation, offset, and division options.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_modeling_extrude_faces)

    mcp.tool(
        name="modeling.boolean",
        description="Perform a boolean operation (union, difference, intersection) on two meshes.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_modeling_boolean)

    mcp.tool(
        name="modeling.combine",
        description="Combine multiple meshes into a single mesh.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_modeling_combine)

    mcp.tool(
        name="modeling.separate",
        description="Separate a combined mesh into individual meshes.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_modeling_separate)

    mcp.tool(
        name="modeling.merge_vertices",
        description="Merge vertices on a mesh within a distance threshold.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_modeling_merge_vertices)

    mcp.tool(
        name="modeling.bevel",
        description="Bevel edges or vertices with offset, segments, and fraction options.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_modeling_bevel)

    mcp.tool(
        name="modeling.bridge",
        description="Bridge between edge loops to create connecting faces.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_modeling_bridge)

    mcp.tool(
        name="modeling.insert_edge_loop",
        description="Insert an edge loop at the specified edge using polySplitRing.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_modeling_insert_edge_loop)

    mcp.tool(
        name="modeling.delete_faces",
        description="Delete polygon faces from a mesh.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_modeling_delete_faces)

    mcp.tool(
        name="modeling.move_components",
        description="Move mesh components (vertices, edges, faces) by relative translation or to an absolute position.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )(tool_modeling_move_components)

    mcp.tool(
        name="modeling.freeze_transforms",
        description="Freeze (reset) transforms on nodes, applying current values as identity.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_modeling_freeze_transforms)

    mcp.tool(
        name="modeling.delete_history",
        description="Delete construction history from nodes or the entire scene.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_modeling_delete_history)

    mcp.tool(
        name="modeling.center_pivot",
        description="Center the pivot point on nodes.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_modeling_center_pivot)

    mcp.tool(
        name="modeling.set_pivot",
        description="Set the pivot point of a node to an explicit position.",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )(tool_modeling_set_pivot)
