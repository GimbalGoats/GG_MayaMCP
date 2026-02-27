"""Polygon modeling tools for Maya MCP.

This module provides tools for creating polygon primitives, extruding,
booleans, combining/separating meshes, beveling, bridging, edge loops,
component manipulation, and cleanup operations.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from maya_mcp.transport import get_client
from maya_mcp.utils.parsing import parse_json_response
from maya_mcp.utils.response_guard import guard_response_size
from maya_mcp.utils.validation import validate_component_name as _validate_component_name
from maya_mcp.utils.validation import validate_node_name as _validate_node_name

VALID_PRIMITIVES = {"cube", "sphere", "cylinder", "cone", "torus", "plane"}

VALID_AXES = {"x", "y", "z"}


def modeling_create_polygon_primitive(
    primitive_type: Literal["cube", "sphere", "cylinder", "cone", "torus", "plane"],
    name: str | None = None,
    width: float = 1.0,
    height: float = 1.0,
    depth: float = 1.0,
    radius: float = 0.5,
    subdivisions_width: int | None = None,
    subdivisions_height: int | None = None,
    subdivisions_depth: int | None = None,
    subdivisions_axis: int | None = None,
    axis: Literal["x", "y", "z"] = "y",
) -> dict[str, Any]:
    """Create a polygon primitive.

    Args:
        primitive_type: Type of primitive to create.
        name: Optional name for the transform node.
        width: Width of the primitive (cube/plane).
        height: Height of the primitive (cube/cylinder/cone).
        depth: Depth of the primitive (cube).
        radius: Radius of the primitive (sphere/cylinder/cone/torus).
        subdivisions_width: Width subdivisions.
        subdivisions_height: Height subdivisions.
        subdivisions_depth: Depth subdivisions.
        subdivisions_axis: Axis subdivisions (sphere/cylinder/cone/torus).
        axis: Up axis for the primitive.

    Returns:
        Dictionary with transform, shape, constructor, primitive_type,
        vertex_count, face_count, and errors.

    Raises:
        ValueError: If primitive_type or axis is invalid, or name contains
            invalid characters.
    """
    if primitive_type not in VALID_PRIMITIVES:
        raise ValueError(
            f"Invalid primitive_type: {primitive_type!r}. "
            f"Must be one of: {', '.join(sorted(VALID_PRIMITIVES))}"
        )
    if axis not in VALID_AXES:
        raise ValueError(f"Invalid axis: {axis!r}. Must be one of: {', '.join(sorted(VALID_AXES))}")
    if name is not None:
        _validate_node_name(name)

    client = get_client()
    name_escaped = json.dumps(name)
    ptype_escaped = json.dumps(primitive_type)
    axis_escaped = json.dumps(axis)

    # Build optional kwargs for subdivisions
    subdiv_parts: list[str] = []
    if subdivisions_width is not None:
        subdiv_parts.append(f"    kwargs['subdivisionsWidth'] = {int(subdivisions_width)}")
    if subdivisions_height is not None:
        subdiv_parts.append(f"    kwargs['subdivisionsHeight'] = {int(subdivisions_height)}")
    if subdivisions_depth is not None:
        subdiv_parts.append(f"    kwargs['subdivisionsDepth'] = {int(subdivisions_depth)}")
    if subdivisions_axis is not None:
        subdiv_parts.append(f"    kwargs['subdivisionsAxis'] = {int(subdivisions_axis)}")
    subdiv_block = "\n".join(subdiv_parts) if subdiv_parts else "    pass"

    command = f"""
import maya.cmds as cmds
import json

ptype = {ptype_escaped}
name = {name_escaped}
width = {float(width)}
height = {float(height)}
depth = {float(depth)}
radius = {float(radius)}
axis_str = {axis_escaped}

axis_map = {{"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}}
ax = axis_map[axis_str]

result = {{"transform": None, "shape": None, "constructor": None, "primitive_type": ptype, "vertex_count": 0, "face_count": 0, "errors": {{}}}}

try:
    kwargs = {{}}
    if name:
        kwargs["name"] = name
{subdiv_block}

    if ptype == "cube":
        kwargs["width"] = width
        kwargs["height"] = height
        kwargs["depth"] = depth
        kwargs["axis"] = ax
        created = cmds.polyCube(**kwargs)
    elif ptype == "sphere":
        kwargs["radius"] = radius
        kwargs["axis"] = ax
        if "subdivisionsAxis" not in kwargs and "subdivisionsWidth" not in kwargs:
            pass
        created = cmds.polySphere(**kwargs)
    elif ptype == "cylinder":
        kwargs["radius"] = radius
        kwargs["height"] = height
        kwargs["axis"] = ax
        created = cmds.polyCylinder(**kwargs)
    elif ptype == "cone":
        kwargs["radius"] = radius
        kwargs["height"] = height
        kwargs["axis"] = ax
        created = cmds.polyCone(**kwargs)
    elif ptype == "torus":
        kwargs["radius"] = radius
        kwargs["axis"] = ax
        created = cmds.polyTorus(**kwargs)
    elif ptype == "plane":
        kwargs["width"] = width
        kwargs["height"] = height
        kwargs["axis"] = ax
        created = cmds.polyPlane(**kwargs)
    else:
        result["errors"]["_type"] = "Unknown primitive type: " + ptype
        created = None

    if created:
        transform = created[0]
        constructor = created[1] if len(created) > 1 else None
        result["transform"] = transform
        result["constructor"] = constructor

        shapes = cmds.listRelatives(transform, shapes=True, fullPath=False) or []
        if shapes:
            result["shape"] = shapes[0]

        result["vertex_count"] = cmds.polyEvaluate(transform, vertex=True)
        result["face_count"] = cmds.polyEvaluate(transform, face=True)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def modeling_extrude_faces(
    faces: list[str],
    local_translate_z: float | None = None,
    local_translate_x: float | None = None,
    local_translate_y: float | None = None,
    offset: float | None = None,
    divisions: int = 1,
    keep_faces_together: bool = True,
) -> dict[str, Any]:
    """Extrude polygon faces.

    Args:
        faces: Component strings for faces to extrude (e.g., ['pCube1.f[0]']).
        local_translate_z: Local Z translation (thickness/extrusion amount).
        local_translate_x: Local X translation.
        local_translate_y: Local Y translation.
        offset: Offset amount for the extrusion.
        divisions: Number of divisions for the extrusion.
        keep_faces_together: Keep faces together during extrusion.

    Returns:
        Dictionary with node, faces_extruded, new_face_count, and errors.

    Raises:
        ValueError: If faces list is empty or contains invalid characters.
    """
    if not faces:
        raise ValueError("faces list cannot be empty")
    for face in faces:
        _validate_component_name(face)

    client = get_client()
    faces_escaped = json.dumps(faces)

    # Build optional kwargs
    kwarg_lines: list[str] = []
    if local_translate_z is not None:
        kwarg_lines.append(f"    kwargs['localTranslateZ'] = {float(local_translate_z)}")
    if local_translate_x is not None:
        kwarg_lines.append(f"    kwargs['localTranslateX'] = {float(local_translate_x)}")
    if local_translate_y is not None:
        kwarg_lines.append(f"    kwargs['localTranslateY'] = {float(local_translate_y)}")
    if offset is not None:
        kwarg_lines.append(f"    kwargs['offset'] = {float(offset)}")
    kwarg_block = "\n".join(kwarg_lines) if kwarg_lines else "    pass"

    kft_val = "True" if keep_faces_together else "False"

    command = f"""
import maya.cmds as cmds
import json

faces = {faces_escaped}
divisions = {int(divisions)}
keep_together = {kft_val}

result = {{"node": None, "faces_extruded": len(faces), "new_face_count": 0, "errors": {{}}}}

try:
    # Validate faces exist
    missing = [f for f in faces if not cmds.objExists(f)]
    if missing:
        result["errors"]["_faces"] = "Components do not exist: " + ", ".join(missing)
    else:
        kwargs = {{"divisions": divisions, "keepFacesTogether": keep_together}}
{kwarg_block}

        extrude_result = cmds.polyExtrudeFacet(faces, **kwargs)
        if extrude_result:
            result["node"] = extrude_result[0] if isinstance(extrude_result, list) else extrude_result

        # Get the mesh from the first face component
        mesh = faces[0].split(".")[0]
        result["new_face_count"] = cmds.polyEvaluate(mesh, face=True)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def modeling_boolean(
    mesh_a: str,
    mesh_b: str,
    operation: Literal["union", "difference", "intersection"] = "union",
) -> dict[str, Any]:
    """Perform a boolean operation on two meshes.

    Args:
        mesh_a: First mesh (the base mesh).
        mesh_b: Second mesh (the operand).
        operation: Boolean operation type.

    Returns:
        Dictionary with result_mesh, operation, vertex_count,
        face_count, and errors.

    Raises:
        ValueError: If mesh names contain invalid characters or
            operation is invalid.
    """
    _validate_node_name(mesh_a)
    _validate_node_name(mesh_b)

    valid_ops = {"union", "difference", "intersection"}
    if operation not in valid_ops:
        raise ValueError(
            f"Invalid operation: {operation!r}. Must be one of: {', '.join(sorted(valid_ops))}"
        )

    op_map = {"union": 1, "difference": 2, "intersection": 3}

    client = get_client()
    mesh_a_escaped = json.dumps(mesh_a)
    mesh_b_escaped = json.dumps(mesh_b)
    op_int = op_map[operation]
    op_escaped = json.dumps(operation)

    command = f"""
import maya.cmds as cmds
import json

mesh_a = {mesh_a_escaped}
mesh_b = {mesh_b_escaped}
op_int = {op_int}
op_name = {op_escaped}

result = {{"result_mesh": None, "operation": op_name, "vertex_count": 0, "face_count": 0, "errors": {{}}}}

try:
    if not cmds.objExists(mesh_a):
        result["errors"]["_mesh_a"] = "Node '" + mesh_a + "' does not exist"
    elif not cmds.objExists(mesh_b):
        result["errors"]["_mesh_b"] = "Node '" + mesh_b + "' does not exist"
    else:
        bool_result = cmds.polyCBoolOp(mesh_a, mesh_b, operation=op_int, constructionHistory=True)
        if bool_result:
            result_mesh = bool_result[0]
            result["result_mesh"] = result_mesh
            result["vertex_count"] = cmds.polyEvaluate(result_mesh, vertex=True)
            result["face_count"] = cmds.polyEvaluate(result_mesh, face=True)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def modeling_combine(
    meshes: list[str],
    name: str | None = None,
) -> dict[str, Any]:
    """Combine multiple meshes into one.

    Args:
        meshes: List of mesh names to combine (minimum 2).
        name: Optional name for the combined mesh.

    Returns:
        Dictionary with result_mesh, source_meshes, vertex_count,
        face_count, and errors.

    Raises:
        ValueError: If meshes list has fewer than 2 entries or names
            contain invalid characters.
    """
    if len(meshes) < 2:
        raise ValueError("meshes list must contain at least 2 meshes")
    for mesh in meshes:
        _validate_node_name(mesh)
    if name is not None:
        _validate_node_name(name)

    client = get_client()
    meshes_escaped = json.dumps(meshes)
    name_escaped = json.dumps(name)

    command = f"""
import maya.cmds as cmds
import json

meshes = {meshes_escaped}
name = {name_escaped}

result = {{"result_mesh": None, "source_meshes": meshes, "vertex_count": 0, "face_count": 0, "errors": {{}}}}

try:
    missing = [m for m in meshes if not cmds.objExists(m)]
    if missing:
        result["errors"]["_meshes"] = "Nodes do not exist: " + ", ".join(missing)
    else:
        combine_result = cmds.polyUnite(meshes, constructionHistory=True)
        if combine_result:
            result_mesh = combine_result[0]
            if name:
                result_mesh = cmds.rename(result_mesh, name)
            result["result_mesh"] = result_mesh
            result["vertex_count"] = cmds.polyEvaluate(result_mesh, vertex=True)
            result["face_count"] = cmds.polyEvaluate(result_mesh, face=True)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def modeling_separate(
    mesh: str,
) -> dict[str, Any]:
    """Separate a combined mesh into individual meshes.

    Args:
        mesh: Name of the mesh to separate.

    Returns:
        Dictionary with source_mesh, result_meshes, count, and errors.

    Raises:
        ValueError: If mesh name contains invalid characters.
    """
    _validate_node_name(mesh)

    client = get_client()
    mesh_escaped = json.dumps(mesh)

    command = f"""
import maya.cmds as cmds
import json

mesh = {mesh_escaped}

result = {{"source_mesh": mesh, "result_meshes": [], "count": 0, "errors": {{}}}}

try:
    if not cmds.objExists(mesh):
        result["errors"]["_mesh"] = "Node '" + mesh + "' does not exist"
    else:
        sep_result = cmds.polySeparate(mesh, constructionHistory=False)
        if sep_result:
            # polySeparate returns transforms under a new group
            result["result_meshes"] = sep_result
            result["count"] = len(sep_result)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    if "result_meshes" in parsed:
        parsed = guard_response_size(parsed, list_key="result_meshes")

    return parsed


def modeling_merge_vertices(
    mesh: str,
    threshold: float = 0.001,
    vertices: list[str] | None = None,
) -> dict[str, Any]:
    """Merge vertices on a mesh within a distance threshold.

    Args:
        mesh: Name of the mesh.
        threshold: Distance threshold for merging (default 0.001).
        vertices: Optional list of specific vertex components to merge.
            If None, merges all vertices on the mesh within threshold.

    Returns:
        Dictionary with mesh, vertices_merged, vertex_count_before,
        vertex_count_after, and errors.

    Raises:
        ValueError: If mesh name or vertex components contain invalid characters.
    """
    _validate_node_name(mesh)
    if vertices is not None:
        for vtx in vertices:
            _validate_component_name(vtx)

    client = get_client()
    mesh_escaped = json.dumps(mesh)
    vertices_escaped = json.dumps(vertices)

    command = f"""
import maya.cmds as cmds
import json

mesh = {mesh_escaped}
threshold = {float(threshold)}
vertices = {vertices_escaped}

result = {{"mesh": mesh, "vertices_merged": 0, "vertex_count_before": 0, "vertex_count_after": 0, "errors": {{}}}}

try:
    if not cmds.objExists(mesh):
        result["errors"]["_mesh"] = "Node '" + mesh + "' does not exist"
    else:
        result["vertex_count_before"] = cmds.polyEvaluate(mesh, vertex=True)

        if vertices:
            cmds.polyMergeVertex(vertices, distance=threshold, constructionHistory=True)
        else:
            cmds.polyMergeVertex(mesh, distance=threshold, constructionHistory=True)

        result["vertex_count_after"] = cmds.polyEvaluate(mesh, vertex=True)
        result["vertices_merged"] = result["vertex_count_before"] - result["vertex_count_after"]

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def modeling_delete_history(
    nodes: list[str] | None = None,
    all_nodes: bool = False,
) -> dict[str, Any]:
    """Delete construction history from nodes.

    Args:
        nodes: List of node names to delete history from.
        all_nodes: If True, delete history from all nodes in the scene.
            If True, the nodes parameter is ignored.

    Returns:
        Dictionary with cleaned list, count, and errors.

    Raises:
        ValueError: If neither nodes nor all_nodes is specified, or
            node names contain invalid characters.
    """
    if not all_nodes and not nodes:
        raise ValueError("Either nodes must be provided or all_nodes must be True")
    if nodes is not None:
        for node in nodes:
            _validate_node_name(node)

    client = get_client()
    nodes_escaped = json.dumps(nodes)
    all_val = "True" if all_nodes else "False"

    command = f"""
import maya.cmds as cmds
import json

nodes = {nodes_escaped}
all_nodes = {all_val}

result = {{"cleaned": [], "count": 0, "errors": {{}}}}

try:
    if all_nodes:
        all_transforms = cmds.ls(type="transform") or []
        # Filter to only DAG transforms with shapes (meshes, etc.)
        targets = []
        for t in all_transforms:
            shapes = cmds.listRelatives(t, shapes=True) or []
            if shapes:
                targets.append(t)
        if targets:
            cmds.delete(targets, constructionHistory=True)
        result["cleaned"] = targets
        result["count"] = len(targets)
    else:
        missing = [n for n in nodes if not cmds.objExists(n)]
        if missing:
            result["errors"]["_nodes"] = "Nodes do not exist: " + ", ".join(missing)
        else:
            cmds.delete(nodes, constructionHistory=True)
            result["cleaned"] = nodes
            result["count"] = len(nodes)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    if "cleaned" in parsed:
        parsed = guard_response_size(parsed, list_key="cleaned")

    return parsed


def modeling_freeze_transforms(
    nodes: list[str],
    translate: bool = True,
    rotate: bool = True,
    scale: bool = True,
) -> dict[str, Any]:
    """Freeze (reset) transforms on nodes.

    Applies the current transform values as the identity and resets
    the transform channels to zero/one.

    Args:
        nodes: List of node names to freeze.
        translate: Freeze translation (default True).
        rotate: Freeze rotation (default True).
        scale: Freeze scale (default True).

    Returns:
        Dictionary with frozen list, count, and errors.

    Raises:
        ValueError: If nodes list is empty or names contain invalid characters.
    """
    if not nodes:
        raise ValueError("nodes list cannot be empty")
    for node in nodes:
        _validate_node_name(node)

    client = get_client()
    nodes_escaped = json.dumps(nodes)
    t_val = "True" if translate else "False"
    r_val = "True" if rotate else "False"
    s_val = "True" if scale else "False"

    command = f"""
import maya.cmds as cmds
import json

nodes = {nodes_escaped}
do_translate = {t_val}
do_rotate = {r_val}
do_scale = {s_val}

result = {{"frozen": [], "count": 0, "errors": {{}}}}

try:
    missing = [n for n in nodes if not cmds.objExists(n)]
    if missing:
        result["errors"]["_nodes"] = "Nodes do not exist: " + ", ".join(missing)
    else:
        cmds.makeIdentity(nodes, apply=True, translate=do_translate, rotate=do_rotate, scale=do_scale)
        result["frozen"] = nodes
        result["count"] = len(nodes)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def modeling_center_pivot(
    nodes: list[str],
) -> dict[str, Any]:
    """Center the pivot point on nodes.

    Args:
        nodes: List of node names to center pivots on.

    Returns:
        Dictionary with centered list, count, pivot_positions, and errors.

    Raises:
        ValueError: If nodes list is empty or names contain invalid characters.
    """
    if not nodes:
        raise ValueError("nodes list cannot be empty")
    for node in nodes:
        _validate_node_name(node)

    client = get_client()
    nodes_escaped = json.dumps(nodes)

    command = f"""
import maya.cmds as cmds
import json

nodes = {nodes_escaped}

result = {{"centered": [], "count": 0, "pivot_positions": {{}}, "errors": {{}}}}

try:
    missing = [n for n in nodes if not cmds.objExists(n)]
    if missing:
        result["errors"]["_nodes"] = "Nodes do not exist: " + ", ".join(missing)
    else:
        for node in nodes:
            cmds.xform(node, centerPivots=True)
            piv = cmds.xform(node, query=True, pivots=True, worldSpace=True)
            result["pivot_positions"][node] = piv[:3] if piv else [0, 0, 0]
        result["centered"] = nodes
        result["count"] = len(nodes)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def modeling_set_pivot(
    node: str,
    position: list[float],
    world_space: bool = True,
) -> dict[str, Any]:
    """Set the pivot point of a node to an explicit position.

    Args:
        node: Node name to set pivot on.
        position: [x, y, z] position for the pivot.
        world_space: If True, position is in world space (default True).

    Returns:
        Dictionary with node, pivot, world_space, and errors.

    Raises:
        ValueError: If node name contains invalid characters or position
            is not a list of 3 floats.
    """
    _validate_node_name(node)
    if not isinstance(position, list) or len(position) != 3:
        raise ValueError("position must be a list of 3 floats [x, y, z]")

    client = get_client()
    node_escaped = json.dumps(node)
    pos_escaped = json.dumps([float(p) for p in position])
    ws_val = "True" if world_space else "False"

    command = f"""
import maya.cmds as cmds
import json

node = {node_escaped}
position = {pos_escaped}
world_space = {ws_val}

result = {{"node": node, "pivot": position, "world_space": world_space, "errors": {{}}}}

try:
    if not cmds.objExists(node):
        result["errors"]["_node"] = "Node '" + node + "' does not exist"
    else:
        cmds.xform(node, pivots=position, worldSpace=world_space)
        # Read back the actual pivot
        piv = cmds.xform(node, query=True, pivots=True, worldSpace=world_space)
        result["pivot"] = piv[:3] if piv else position

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def modeling_move_components(
    components: list[str],
    translate: list[float] | None = None,
    absolute: list[float] | None = None,
    world_space: bool = True,
) -> dict[str, Any]:
    """Move mesh components (vertices, edges, faces).

    Exactly one of translate (relative) or absolute must be provided.

    Args:
        components: Component strings (e.g., ['pCube1.vtx[0:3]']).
        translate: Relative [x, y, z] translation.
        absolute: Absolute [x, y, z] position.
        world_space: Use world space coordinates (default True).

    Returns:
        Dictionary with components_moved, translate or absolute,
        world_space, and errors.

    Raises:
        ValueError: If components are empty, both or neither of
            translate/absolute provided, or values are invalid.
    """
    if not components:
        raise ValueError("components list cannot be empty")
    for comp in components:
        _validate_component_name(comp)

    if translate is not None and absolute is not None:
        raise ValueError("Only one of translate or absolute can be provided, not both")
    if translate is None and absolute is None:
        raise ValueError("Either translate or absolute must be provided")

    if translate is not None and (not isinstance(translate, list) or len(translate) != 3):
        raise ValueError("translate must be a list of 3 floats [x, y, z]")
    if absolute is not None and (not isinstance(absolute, list) or len(absolute) != 3):
        raise ValueError("absolute must be a list of 3 floats [x, y, z]")

    client = get_client()
    components_escaped = json.dumps(components)
    ws_val = "True" if world_space else "False"

    if translate is not None:
        move_vals = json.dumps([float(v) for v in translate])
        mode = "relative"
    else:
        assert absolute is not None
        move_vals = json.dumps([float(v) for v in absolute])
        mode = "absolute"

    mode_escaped = json.dumps(mode)

    command = f"""
import maya.cmds as cmds
import json

components = {components_escaped}
move_vals = {move_vals}
mode = {mode_escaped}
world_space = {ws_val}

result = {{"components_moved": len(components), "world_space": world_space, "errors": {{}}}}

try:
    missing = [c for c in components if not cmds.objExists(c)]
    if missing:
        result["errors"]["_components"] = "Components do not exist: " + ", ".join(missing)
    else:
        if mode == "relative":
            result["translate"] = move_vals
            cmds.move(move_vals[0], move_vals[1], move_vals[2], components, relative=True, worldSpace=world_space)
        else:
            result["absolute"] = move_vals
            cmds.move(move_vals[0], move_vals[1], move_vals[2], components, absolute=True, worldSpace=world_space)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def modeling_bevel(
    components: list[str],
    offset: float = 0.5,
    segments: int = 1,
    fraction: float = 0.5,
) -> dict[str, Any]:
    """Bevel edges or vertices.

    Args:
        components: Edge or vertex component strings to bevel.
        offset: Bevel offset distance (default 0.5).
        segments: Number of bevel segments (default 1).
        fraction: Bevel fraction (default 0.5).

    Returns:
        Dictionary with node, components_beveled, new_vertex_count,
        new_face_count, and errors.

    Raises:
        ValueError: If components list is empty or contains invalid characters.
    """
    if not components:
        raise ValueError("components list cannot be empty")
    for comp in components:
        _validate_component_name(comp)

    client = get_client()
    components_escaped = json.dumps(components)

    command = f"""
import maya.cmds as cmds
import json

components = {components_escaped}
offset_val = {float(offset)}
segments = {int(segments)}
fraction = {float(fraction)}

result = {{"node": None, "components_beveled": len(components), "new_vertex_count": 0, "new_face_count": 0, "errors": {{}}}}

try:
    missing = [c for c in components if not cmds.objExists(c)]
    if missing:
        result["errors"]["_components"] = "Components do not exist: " + ", ".join(missing)
    else:
        bevel_result = cmds.polyBevel3(components, offset=offset_val, segments=segments, fraction=fraction)
        if bevel_result:
            result["node"] = bevel_result[0] if isinstance(bevel_result, list) else bevel_result

        # Get mesh name from component
        mesh = components[0].split(".")[0]
        result["new_vertex_count"] = cmds.polyEvaluate(mesh, vertex=True)
        result["new_face_count"] = cmds.polyEvaluate(mesh, face=True)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def modeling_bridge(
    edge_loops: list[str],
    divisions: int = 0,
    twist: int = 0,
    taper: float = 1.0,
) -> dict[str, Any]:
    """Bridge between edge loops.

    Args:
        edge_loops: Edge component strings for the edge loops to bridge.
        divisions: Number of divisions in the bridge (default 0).
        twist: Twist amount (default 0).
        taper: Taper amount (default 1.0).

    Returns:
        Dictionary with node, new_face_count, and errors.

    Raises:
        ValueError: If edge_loops list is empty or contains invalid characters.
    """
    if not edge_loops:
        raise ValueError("edge_loops list cannot be empty")
    for edge in edge_loops:
        _validate_component_name(edge)

    client = get_client()
    edges_escaped = json.dumps(edge_loops)

    command = f"""
import maya.cmds as cmds
import json

edges = {edges_escaped}
divisions = {int(divisions)}
twist = {int(twist)}
taper = {float(taper)}

result = {{"node": None, "new_face_count": 0, "errors": {{}}}}

try:
    missing = [e for e in edges if not cmds.objExists(e)]
    if missing:
        result["errors"]["_edges"] = "Components do not exist: " + ", ".join(missing)
    else:
        cmds.select(edges, replace=True)
        bridge_result = cmds.polyBridgeEdge(divisions=divisions, twist=twist, taper=taper)
        if bridge_result:
            result["node"] = bridge_result[0] if isinstance(bridge_result, list) else bridge_result

        mesh = edges[0].split(".")[0]
        result["new_face_count"] = cmds.polyEvaluate(mesh, face=True)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def modeling_insert_edge_loop(
    edge: str,
    divisions: int = 1,
    weight: float = 0.5,
) -> dict[str, Any]:
    """Insert an edge loop at the specified edge.

    Args:
        edge: Single edge component (e.g., 'pCube1.e[4]').
        divisions: Number of edge loops to insert (default 1).
        weight: Position weight along the edge (0-1, default 0.5).

    Returns:
        Dictionary with node, edge, new_edge_count,
        new_vertex_count, and errors.

    Raises:
        ValueError: If edge contains invalid characters.
    """
    _validate_component_name(edge)

    client = get_client()
    edge_escaped = json.dumps(edge)

    command = f"""
import maya.cmds as cmds
import json

edge = {edge_escaped}
divisions = {int(divisions)}
weight = {float(weight)}

result = {{"node": None, "edge": edge, "new_edge_count": 0, "new_vertex_count": 0, "errors": {{}}}}

try:
    if not cmds.objExists(edge):
        result["errors"]["_edge"] = "Component '" + edge + "' does not exist"
    else:
        split_result = cmds.polySplitRing(edge, divisions=divisions, weight=weight)
        if split_result:
            result["node"] = split_result[0] if isinstance(split_result, list) else split_result

        mesh = edge.split(".")[0]
        result["new_edge_count"] = cmds.polyEvaluate(mesh, edge=True)
        result["new_vertex_count"] = cmds.polyEvaluate(mesh, vertex=True)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def modeling_delete_faces(
    faces: list[str],
) -> dict[str, Any]:
    """Delete polygon faces from a mesh.

    Args:
        faces: Component strings for faces to delete (e.g., ['pCube1.f[0]']).

    Returns:
        Dictionary with faces_deleted, mesh, remaining_face_count, and errors.

    Raises:
        ValueError: If faces list is empty or contains invalid characters.
    """
    if not faces:
        raise ValueError("faces list cannot be empty")
    for face in faces:
        _validate_component_name(face)

    client = get_client()
    faces_escaped = json.dumps(faces)

    command = f"""
import maya.cmds as cmds
import json

faces = {faces_escaped}

result = {{"faces_deleted": len(faces), "mesh": None, "remaining_face_count": 0, "errors": {{}}}}

try:
    missing = [f for f in faces if not cmds.objExists(f)]
    if missing:
        result["errors"]["_faces"] = "Components do not exist: " + ", ".join(missing)
    else:
        mesh = faces[0].split(".")[0]
        result["mesh"] = mesh
        cmds.delete(faces)
        result["remaining_face_count"] = cmds.polyEvaluate(mesh, face=True)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed
