"""Skinning tools for Maya MCP.

This module provides tools for skin binding, weight management,
and weight transfer for character rigging workflows.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from maya_mcp.transport import get_client
from maya_mcp.utils.parsing import parse_json_response
from maya_mcp.utils.response_guard import guard_response_size
from maya_mcp.utils.validation import validate_node_name as _validate_node_name

DEFAULT_WEIGHT_LIMIT = 100

MAX_WEIGHT_SET_ENTRIES = 1000

BIND_METHOD_MAP = {
    "closestDistance": 0,
    "heatMap": 1,
    "geodesicVoxel": 3,
}


def skin_bind(
    mesh: str,
    joints: list[str],
    max_influences: int = 4,
    bind_method: Literal["closestDistance", "heatMap", "geodesicVoxel"] = "closestDistance",
) -> dict[str, Any]:
    """Bind a mesh to a skeleton using a skin cluster.

    Creates a skinCluster binding the mesh to the specified joints
    with the given binding options.

    Args:
        mesh: Name of the mesh to bind.
        joints: List of joint names to use as influences.
        max_influences: Maximum number of influences per vertex (default 4).
        bind_method: Binding algorithm to use. Options:
            - "closestDistance": Closest distance (default)
            - "heatMap": Heat map based
            - "geodesicVoxel": Geodesic voxel

    Returns:
        Dictionary with binding result:
            - mesh: The mesh that was bound
            - skin_cluster: Name of the created skinCluster
            - influences: List of influence joint names
            - influence_count: Number of influences
            - errors: Error details if any, or None

    Raises:
        ValueError: If mesh or joint names contain invalid characters,
            or if joints list is empty.
    """
    _validate_node_name(mesh)
    if not joints:
        raise ValueError("joints list cannot be empty")
    for joint in joints:
        _validate_node_name(joint)

    if bind_method not in BIND_METHOD_MAP:
        raise ValueError(
            f"Invalid bind_method: {bind_method!r}. "
            f"Must be one of: {', '.join(sorted(BIND_METHOD_MAP))}"
        )

    client = get_client()
    mesh_escaped = json.dumps(mesh)
    joints_escaped = json.dumps(joints)
    bind_method_int = BIND_METHOD_MAP[bind_method]

    command = f"""
import maya.cmds as cmds
import json

mesh = {mesh_escaped}
joints = {joints_escaped}
max_influences = {max_influences}
bind_method = {bind_method_int}

result = {{"mesh": mesh, "skin_cluster": None, "influences": [], "influence_count": 0, "errors": {{}}}}

try:
    if not cmds.objExists(mesh):
        result["errors"]["_mesh"] = "Node '" + mesh + "' does not exist"
    else:
        # Validate all joints exist
        missing = [j for j in joints if not cmds.objExists(j)]
        if missing:
            result["errors"]["_joints"] = "Joints do not exist: " + ", ".join(missing)
        else:
            # Create skin cluster
            sc = cmds.skinCluster(
                joints + [mesh],
                toSelectedBones=False,
                maximumInfluences=max_influences,
                bindMethod=bind_method,
            )
            skin_cluster = sc[0] if isinstance(sc, list) else sc

            result["skin_cluster"] = skin_cluster

            # Query influences
            influences = cmds.skinCluster(skin_cluster, query=True, influence=True) or []
            result["influences"] = influences
            result["influence_count"] = len(influences)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def skin_unbind(mesh: str) -> dict[str, Any]:
    """Unbind (detach) a skin cluster from a mesh.

    Finds the skinCluster on the mesh and unbinds it, removing
    the skin deformation.

    Args:
        mesh: Name of the mesh to unbind.

    Returns:
        Dictionary with unbind result:
            - mesh: The mesh that was unbound
            - unbound: Whether unbinding succeeded
            - skin_cluster: Name of the removed skinCluster
            - errors: Error details if any, or None

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

result = {{"mesh": mesh, "unbound": False, "skin_cluster": None, "errors": {{}}}}

try:
    if not cmds.objExists(mesh):
        result["errors"]["_mesh"] = "Node '" + mesh + "' does not exist"
    else:
        # Find skin cluster in history
        history = cmds.ls(cmds.listHistory(mesh) or [], type="skinCluster") or []
        if not history:
            result["errors"]["_skin"] = "No skinCluster found on '" + mesh + "'"
        else:
            skin_cluster = history[0]
            result["skin_cluster"] = skin_cluster

            # Unbind the skin
            cmds.skinCluster(skin_cluster, edit=True, unbind=True)
            result["unbound"] = True

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def skin_influences(skin_cluster: str) -> dict[str, Any]:
    """List influences on a skin cluster.

    Returns the list of joints/transforms influencing the skin cluster,
    along with their index mapping.

    Args:
        skin_cluster: Name of the skinCluster node.

    Returns:
        Dictionary with influence data:
            - skin_cluster: The queried skinCluster name
            - influences: List of dicts with name and index
            - count: Number of influences
            - errors: Error details if any, or None

    Raises:
        ValueError: If skin_cluster name contains invalid characters.
    """
    _validate_node_name(skin_cluster)

    client = get_client()
    sc_escaped = json.dumps(skin_cluster)

    command = f"""
import maya.cmds as cmds
import json

sc = {sc_escaped}

result = {{"skin_cluster": sc, "influences": [], "count": 0, "errors": {{}}}}

try:
    if not cmds.objExists(sc):
        result["errors"]["_node"] = "Node '" + sc + "' does not exist"
    elif cmds.nodeType(sc) != "skinCluster":
        result["errors"]["_type"] = "Node '" + sc + "' is not a skinCluster (type: " + cmds.nodeType(sc) + ")"
    else:
        influences = cmds.skinCluster(sc, query=True, influence=True) or []
        inf_list = []
        for i, inf in enumerate(influences):
            inf_list.append({{"name": inf, "index": i}})
        result["influences"] = inf_list
        result["count"] = len(inf_list)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def skin_weights_get(
    skin_cluster: str,
    offset: int = 0,
    limit: int | None = DEFAULT_WEIGHT_LIMIT,
) -> dict[str, Any]:
    """Get skin weights with pagination.

    Returns per-vertex weight data for the specified range of vertices.
    Uses offset/limit pagination because skin weight data can be very
    large (4-15MB for production meshes).

    Args:
        skin_cluster: Name of the skinCluster node.
        offset: Starting vertex index (0-based).
        limit: Maximum number of vertices to return. Default 100.
            Use 0 for unlimited (use with caution on large meshes).

    Returns:
        Dictionary with weight data:
            - skin_cluster: The queried skinCluster name
            - mesh: The bound mesh name
            - vertex_count: Total number of vertices
            - influence_count: Number of influences
            - influences: List of influence names
            - vertices: List of vertex weight entries
            - offset: The offset used
            - count: Number of vertices returned
            - truncated: True if more vertices remain
            - errors: Error details if any, or None

    Raises:
        ValueError: If skin_cluster name contains invalid characters
            or offset is negative.
    """
    _validate_node_name(skin_cluster)
    if offset < 0:
        raise ValueError(f"offset must be non-negative, got {offset}")

    client = get_client()
    sc_escaped = json.dumps(skin_cluster)

    command = f"""
import maya.cmds as cmds
import json

sc = {sc_escaped}
offset = {offset}
limit = {limit}

result = {{
    "skin_cluster": sc,
    "mesh": None,
    "vertex_count": 0,
    "influence_count": 0,
    "influences": [],
    "vertices": [],
    "offset": offset,
    "count": 0,
    "errors": {{}}
}}

try:
    if not cmds.objExists(sc):
        result["errors"]["_node"] = "Node '" + sc + "' does not exist"
    elif cmds.nodeType(sc) != "skinCluster":
        result["errors"]["_type"] = "Node '" + sc + "' is not a skinCluster (type: " + cmds.nodeType(sc) + ")"
    else:
        # Get the mesh connected to this skin cluster
        geometry = cmds.skinCluster(sc, query=True, geometry=True) or []
        if not geometry:
            result["errors"]["_geometry"] = "No geometry connected to skinCluster '" + sc + "'"
        else:
            mesh = geometry[0]
            result["mesh"] = mesh

            # Get influence list
            influences = cmds.skinCluster(sc, query=True, influence=True) or []
            result["influences"] = influences
            result["influence_count"] = len(influences)

            # Get vertex count
            vtx_count = cmds.polyEvaluate(mesh, vertex=True)
            result["vertex_count"] = vtx_count

            # Calculate range
            start_idx = offset
            end_idx = vtx_count
            if limit and limit > 0:
                end_idx = min(offset + limit, vtx_count)

            # Get weights per vertex
            vertices = []
            for i in range(start_idx, end_idx):
                vtx = mesh + ".vtx[" + str(i) + "]"
                weights = {{}}
                for inf in influences:
                    w = cmds.skinPercent(sc, vtx, query=True, transform=inf, value=True)
                    if w is not None and w > 0.001:
                        weights[inf] = round(w, 6)
                vertices.append({{"vertex_id": i, "weights": weights}})

            result["vertices"] = vertices
            result["count"] = len(vertices)

            # Check truncation
            if limit and limit > 0 and vtx_count > offset + limit:
                result["truncated"] = True

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    # Apply response size guard
    if "vertices" in parsed:
        parsed = guard_response_size(parsed, list_key="vertices")

    return parsed


def skin_weights_set(
    skin_cluster: str,
    weights: list[dict[str, Any]],
    normalize: bool = True,
) -> dict[str, Any]:
    """Set skin weights on vertices.

    Sets per-vertex skin weights on the specified skin cluster.
    Each entry in the weights list specifies a vertex_id and
    a weights dict mapping joint names to weight values.

    Args:
        skin_cluster: Name of the skinCluster node.
        weights: List of weight entries, each a dict with:
            - vertex_id (int): Vertex index
            - weights (dict): Map of joint name to weight value
        normalize: Whether to normalize weights after setting (default True).

    Returns:
        Dictionary with set result:
            - skin_cluster: The skinCluster name
            - set_count: Number of vertices updated
            - errors: Error details if any, or None

    Raises:
        ValueError: If skin_cluster name contains invalid characters,
            weights list is empty, or too many entries.
    """
    _validate_node_name(skin_cluster)
    if not weights:
        raise ValueError("weights list cannot be empty")
    if len(weights) > MAX_WEIGHT_SET_ENTRIES:
        raise ValueError(
            f"Too many weight entries: {len(weights)}. "
            f"Maximum is {MAX_WEIGHT_SET_ENTRIES} per call."
        )

    # Validate joint names in all weight entries
    for entry in weights:
        if "weights" in entry and isinstance(entry["weights"], dict):
            for joint_name in entry["weights"]:
                _validate_node_name(joint_name)

    client = get_client()
    sc_escaped = json.dumps(skin_cluster)
    weights_escaped = json.dumps(weights)
    normalize_val = "True" if normalize else "False"

    command = f"""
import maya.cmds as cmds
import json

sc = {sc_escaped}
weight_data = {weights_escaped}
normalize = {normalize_val}

result = {{"skin_cluster": sc, "set_count": 0, "errors": {{}}}}

try:
    if not cmds.objExists(sc):
        result["errors"]["_node"] = "Node '" + sc + "' does not exist"
    elif cmds.nodeType(sc) != "skinCluster":
        result["errors"]["_type"] = "Node '" + sc + "' is not a skinCluster (type: " + cmds.nodeType(sc) + ")"
    else:
        geometry = cmds.skinCluster(sc, query=True, geometry=True) or []
        if not geometry:
            result["errors"]["_geometry"] = "No geometry connected to skinCluster '" + sc + "'"
        else:
            mesh = geometry[0]
            set_count = 0
            vertex_errors = {{}}

            for entry in weight_data:
                vid = entry.get("vertex_id")
                w = entry.get("weights", {{}})
                vtx = mesh + ".vtx[" + str(vid) + "]"

                try:
                    tv_list = [(joint, weight) for joint, weight in w.items()]
                    cmds.skinPercent(sc, vtx, transformValue=tv_list, normalize=normalize)
                    set_count += 1
                except Exception as e:
                    vertex_errors[str(vid)] = str(e)

            result["set_count"] = set_count
            if vertex_errors:
                result["errors"].update(vertex_errors)

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed


def skin_copy_weights(
    source_mesh: str,
    target_mesh: str,
    surface_association: Literal[
        "closestPoint", "closestComponent", "rayCast"
    ] = "closestPoint",
    influence_association: Literal[
        "closestJoint", "closestBone", "oneToOne", "name", "label"
    ] = "closestJoint",
) -> dict[str, Any]:
    """Copy skin weights from one mesh to another.

    Transfers skin weights between two meshes using surface
    and influence association methods.

    Args:
        source_mesh: Name of the source mesh (must have a skinCluster).
        target_mesh: Name of the target mesh (must have a skinCluster).
        surface_association: Method for matching surface points. Options:
            - "closestPoint": Closest point on surface (default)
            - "closestComponent": Closest component
            - "rayCast": Ray casting
        influence_association: Method for matching influences. Options:
            - "closestJoint": Closest joint (default)
            - "closestBone": Closest bone
            - "oneToOne": One to one mapping
            - "name": Match by name
            - "label": Match by label

    Returns:
        Dictionary with copy result:
            - source_mesh: The source mesh name
            - target_mesh: The target mesh name
            - source_skin_cluster: Source skinCluster name
            - target_skin_cluster: Target skinCluster name
            - success: Whether the copy succeeded
            - errors: Error details if any, or None

    Raises:
        ValueError: If mesh names contain invalid characters.
    """
    _validate_node_name(source_mesh)
    _validate_node_name(target_mesh)

    valid_surface = {"closestPoint", "closestComponent", "rayCast"}
    if surface_association not in valid_surface:
        raise ValueError(
            f"Invalid surface_association: {surface_association!r}. "
            f"Must be one of: {', '.join(sorted(valid_surface))}"
        )

    valid_influence = {"closestJoint", "closestBone", "oneToOne", "name", "label"}
    if influence_association not in valid_influence:
        raise ValueError(
            f"Invalid influence_association: {influence_association!r}. "
            f"Must be one of: {', '.join(sorted(valid_influence))}"
        )

    client = get_client()
    src_escaped = json.dumps(source_mesh)
    tgt_escaped = json.dumps(target_mesh)
    sa_escaped = json.dumps(surface_association)
    ia_escaped = json.dumps(influence_association)

    command = f"""
import maya.cmds as cmds
import json

source_mesh = {src_escaped}
target_mesh = {tgt_escaped}
surface_assoc = {sa_escaped}
influence_assoc = {ia_escaped}

result = {{
    "source_mesh": source_mesh,
    "target_mesh": target_mesh,
    "source_skin_cluster": None,
    "target_skin_cluster": None,
    "success": False,
    "errors": {{}}
}}

try:
    # Validate meshes exist
    if not cmds.objExists(source_mesh):
        result["errors"]["_source"] = "Node '" + source_mesh + "' does not exist"
    elif not cmds.objExists(target_mesh):
        result["errors"]["_target"] = "Node '" + target_mesh + "' does not exist"
    else:
        # Find skin clusters
        src_history = cmds.ls(cmds.listHistory(source_mesh) or [], type="skinCluster") or []
        if not src_history:
            result["errors"]["_source_skin"] = "No skinCluster found on '" + source_mesh + "'"
        else:
            src_sc = src_history[0]
            result["source_skin_cluster"] = src_sc

            tgt_history = cmds.ls(cmds.listHistory(target_mesh) or [], type="skinCluster") or []
            if not tgt_history:
                result["errors"]["_target_skin"] = "No skinCluster found on '" + target_mesh + "'"
            else:
                tgt_sc = tgt_history[0]
                result["target_skin_cluster"] = tgt_sc

                # Copy weights
                cmds.copySkinWeights(
                    sourceSkin=src_sc,
                    destinationSkin=tgt_sc,
                    surfaceAssociation=surface_assoc,
                    influenceAssociation=[influence_assoc],
                    noMirror=True,
                )
                result["success"] = True

except Exception as e:
    result["errors"]["_exception"] = str(e)

print(json.dumps(result))
"""

    response = client.execute(command)
    parsed: dict[str, Any] = parse_json_response(response)

    if not parsed.get("errors"):
        parsed["errors"] = None

    return parsed
