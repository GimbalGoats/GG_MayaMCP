"""Tests for progress-enabled MCP tool wrappers."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


def _make_progress_ctx() -> SimpleNamespace:
    """Create a minimal FastMCP-like context for progress wrapper tests."""
    return SimpleNamespace(report_progress=AsyncMock())


def _make_weight_vertices(start: int, count: int) -> list[dict[str, object]]:
    """Build compact per-vertex weight payloads for chunking tests."""
    return [
        {"vertex_id": vertex_id, "weights": {"joint1": 1.0}}
        for vertex_id in range(start, start + count)
    ]


def test_scene_export_reports_progress() -> None:
    """scene.export emits coarse progress updates around the Maya export call."""
    from maya_mcp.registrars.scene import tool_scene_export

    ctx = _make_progress_ctx()
    expected = {
        "success": True,
        "file_path": "C:/exports/test.fbx",
        "nodes_exported": 3,
        "error": None,
    }

    with patch("maya_mcp.registrars.scene.scene_export", return_value=expected) as mock_export:
        result = asyncio.run(
            tool_scene_export(
                file_path="C:/exports/test.fbx",
                export_mode="selected",
                animation=False,
                ctx=ctx,
            )
        )

    assert result == expected
    assert mock_export.call_args.kwargs == {
        "file_path": "C:/exports/test.fbx",
        "export_mode": "selected",
        "animation": False,
    }
    assert [call.kwargs for call in ctx.report_progress.await_args_list] == [
        {"progress": 0, "total": 100, "message": "Preparing export request"},
        {"progress": 50, "total": 100, "message": "Executing export in Maya"},
        {"progress": 100, "total": 100, "message": "Export complete"},
    ]


def test_mesh_evaluate_reports_progress_per_check() -> None:
    """mesh.evaluate emits progress as each requested check completes."""
    from maya_mcp.registrars.mesh import tool_mesh_evaluate

    ctx = _make_progress_ctx()
    border_result = {
        "node": "pCube1",
        "exists": True,
        "is_mesh": True,
        "is_clean": True,
        "shape": "pCubeShape1",
        "border_edges": ["pCubeShape1.e[0]"],
        "border_count": 1,
        "errors": None,
    }
    lamina_result = {
        "node": "pCube1",
        "exists": True,
        "is_mesh": True,
        "is_clean": False,
        "shape": "pCubeShape1",
        "lamina_faces": ["pCubeShape1.f[3]"],
        "lamina_count": 1,
        "errors": None,
    }

    with patch(
        "maya_mcp.registrars.mesh.mesh_evaluate",
        side_effect=[border_result, lamina_result],
    ) as mock_mesh_evaluate:
        result = asyncio.run(
            tool_mesh_evaluate(
                node="pCube1",
                checks=["border", "lamina"],
                limit=500,
                ctx=ctx,
            )
        )

    assert result["node"] == "pCube1"
    assert result["shape"] == "pCubeShape1"
    assert result["border_count"] == 1
    assert result["lamina_count"] == 1
    assert result["is_clean"] is False
    assert result["errors"] is None
    assert [call.kwargs for call in mock_mesh_evaluate.call_args_list] == [
        {"node": "pCube1", "checks": ["border"], "limit": 500},
        {"node": "pCube1", "checks": ["lamina"], "limit": 500},
    ]
    assert [call.kwargs for call in ctx.report_progress.await_args_list] == [
        {"progress": 0, "total": 2, "message": "Starting mesh topology analysis"},
        {
            "progress": 1,
            "total": 2,
            "message": "Completed border topology check (1/2)",
        },
        {
            "progress": 2,
            "total": 2,
            "message": "Completed lamina topology check (2/2)",
        },
    ]


def test_skin_weights_get_reports_progress_while_chunking() -> None:
    """skin.weights.get emits progress while aggregating chunked vertex ranges."""
    from maya_mcp.registrars.skin import tool_skin_weights_get

    ctx = _make_progress_ctx()
    first = {
        "skin_cluster": "skinCluster1",
        "mesh": "pCube1",
        "vertex_count": 200,
        "influence_count": 1,
        "influences": ["joint1"],
        "vertices": _make_weight_vertices(0, 50),
        "offset": 0,
        "count": 50,
        "errors": None,
    }
    second = {
        "skin_cluster": "skinCluster1",
        "mesh": "pCube1",
        "vertex_count": 200,
        "influence_count": 1,
        "influences": ["joint1"],
        "vertices": _make_weight_vertices(50, 50),
        "offset": 50,
        "count": 50,
        "errors": None,
    }
    third = {
        "skin_cluster": "skinCluster1",
        "mesh": "pCube1",
        "vertex_count": 200,
        "influence_count": 1,
        "influences": ["joint1"],
        "vertices": _make_weight_vertices(100, 20),
        "offset": 100,
        "count": 20,
        "errors": None,
    }

    with patch(
        "maya_mcp.registrars.skin.skin_weights_get",
        side_effect=[first, second, third],
    ) as mock_skin_weights_get:
        result = asyncio.run(
            tool_skin_weights_get(
                skin_cluster="skinCluster1",
                offset=0,
                limit=120,
                ctx=ctx,
            )
        )

    assert result["skin_cluster"] == "skinCluster1"
    assert result["vertex_count"] == 200
    assert result["count"] == 120
    assert len(result["vertices"]) == 120
    assert result["truncated"] is True
    assert result["errors"] is None
    assert [call.kwargs for call in mock_skin_weights_get.call_args_list] == [
        {"skin_cluster": "skinCluster1", "offset": 0, "limit": 50},
        {"skin_cluster": "skinCluster1", "offset": 50, "limit": 50},
        {"skin_cluster": "skinCluster1", "offset": 100, "limit": 20},
    ]
    assert [call.kwargs for call in ctx.report_progress.await_args_list] == [
        {"progress": 0, "total": None, "message": "Fetching skin weight data"},
        {
            "progress": 50,
            "total": 120,
            "message": "Fetched 50/120 skin weight vertices",
        },
        {
            "progress": 100,
            "total": 120,
            "message": "Fetched 100/120 skin weight vertices",
        },
        {
            "progress": 120,
            "total": 120,
            "message": "Fetched 120/120 skin weight vertices",
        },
    ]


def test_skin_weights_get_unlimited_uses_single_fetch() -> None:
    """skin.weights.get avoids chunk aggregation for unlimited requests."""
    from maya_mcp.registrars.skin import tool_skin_weights_get

    ctx = _make_progress_ctx()
    unlimited = {
        "skin_cluster": "skinCluster1",
        "mesh": "pCube1",
        "vertex_count": 5000,
        "influence_count": 1,
        "influences": ["joint1"],
        "vertices": _make_weight_vertices(0, 5000),
        "offset": 0,
        "count": 5000,
        "errors": None,
    }

    with patch(
        "maya_mcp.registrars.skin.skin_weights_get",
        return_value=unlimited,
    ) as mock_skin_weights_get:
        result = asyncio.run(
            tool_skin_weights_get(
                skin_cluster="skinCluster1",
                offset=0,
                limit=0,
                ctx=ctx,
            )
        )

    assert result == unlimited
    assert [call.kwargs for call in mock_skin_weights_get.call_args_list] == [
        {"skin_cluster": "skinCluster1", "offset": 0, "limit": 0},
    ]
    assert [call.kwargs for call in ctx.report_progress.await_args_list] == [
        {"progress": 0, "total": None, "message": "Fetching skin weight data"},
        {"progress": 1, "total": 1, "message": "Fetched skin weight data"},
    ]


def test_skin_weights_set_reports_progress_while_batching() -> None:
    """skin.weights.set emits progress while applying batched writes."""
    from maya_mcp.registrars.skin import tool_skin_weights_set

    ctx = _make_progress_ctx()
    weights = _make_weight_vertices(0, 240)

    with patch(
        "maya_mcp.registrars.skin.skin_weights_set",
        side_effect=[
            {"skin_cluster": "skinCluster1", "set_count": 100, "errors": None},
            {"skin_cluster": "skinCluster1", "set_count": 98, "errors": {"150": "locked"}},
            {"skin_cluster": "skinCluster1", "set_count": 40, "errors": None},
        ],
    ) as mock_skin_weights_set:
        result = asyncio.run(
            tool_skin_weights_set(
                skin_cluster="skinCluster1",
                weights=weights,
                normalize=True,
                ctx=ctx,
            )
        )

    assert result == {
        "skin_cluster": "skinCluster1",
        "set_count": 238,
        "errors": {"150": "locked"},
    }
    assert [len(call.kwargs["weights"]) for call in mock_skin_weights_set.call_args_list] == [
        100,
        100,
        40,
    ]
    assert [call.kwargs for call in ctx.report_progress.await_args_list] == [
        {"progress": 0, "total": 240, "message": "Applying skin weight edits"},
        {"progress": 100, "total": 240, "message": "Applied 100/240 skin weight entries"},
        {"progress": 200, "total": 240, "message": "Applied 200/240 skin weight entries"},
        {"progress": 240, "total": 240, "message": "Applied 240/240 skin weight entries"},
    ]


def test_progress_enabled_wrappers_do_not_expose_context_argument() -> None:
    """Injected FastMCP context should stay out of client-visible schemas."""
    from maya_mcp.server import mcp

    scene_export_tool = asyncio.run(mcp.get_tool("scene.export"))
    mesh_evaluate_tool = asyncio.run(mcp.get_tool("mesh.evaluate"))
    skin_get_tool = asyncio.run(mcp.get_tool("skin.weights.get"))
    skin_set_tool = asyncio.run(mcp.get_tool("skin.weights.set"))

    assert scene_export_tool is not None
    assert mesh_evaluate_tool is not None
    assert skin_get_tool is not None
    assert skin_set_tool is not None

    assert set(scene_export_tool.to_mcp_tool().inputSchema["properties"]) == {
        "file_path",
        "export_mode",
        "animation",
    }
    assert set(mesh_evaluate_tool.to_mcp_tool().inputSchema["properties"]) == {
        "node",
        "checks",
        "limit",
    }
    assert set(skin_get_tool.to_mcp_tool().inputSchema["properties"]) == {
        "skin_cluster",
        "offset",
        "limit",
    }
    assert set(skin_set_tool.to_mcp_tool().inputSchema["properties"]) == {
        "skin_cluster",
        "weights",
        "normalize",
    }
