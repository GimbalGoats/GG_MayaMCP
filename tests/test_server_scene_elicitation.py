"""Tests for scene elicitation behavior in MCP tool wrappers."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, call, patch


def _make_ctx(*, elicitation: object | None) -> SimpleNamespace:
    """Create a minimal FastMCP-like context for wrapper tests."""
    return SimpleNamespace(
        request_id="req-123",
        session=SimpleNamespace(
            client_params=SimpleNamespace(
                capabilities=SimpleNamespace(elicitation=elicitation),
            ),
            elicit_form=AsyncMock(),
        ),
    )


def test_scene_new_keeps_refusal_for_old_clients() -> None:
    """scene.new returns the current refusal unchanged when elicitation is unavailable."""
    from maya_mcp.registrars.scene import tool_scene_new
    from maya_mcp.tools.scene import SCENE_UNSAVED_CHANGES_ERROR

    ctx = _make_ctx(elicitation=None)
    refusal = {
        "success": False,
        "previous_file": "C:/projects/current.ma",
        "was_modified": True,
        "error": SCENE_UNSAVED_CHANGES_ERROR,
    }

    with patch("maya_mcp.registrars.scene.scene_new", return_value=refusal) as mock_scene_new:
        result = asyncio.run(tool_scene_new(force=False, ctx=ctx))

    assert result == refusal
    assert mock_scene_new.call_count == 1
    assert mock_scene_new.call_args_list[0].kwargs == {"force": False}
    ctx.session.elicit_form.assert_not_awaited()


def test_scene_new_retries_with_force_after_form_elicitation_accept() -> None:
    """scene.new retries with force=True after a supported client confirms discard."""
    from maya_mcp.registrars.scene import tool_scene_new
    from maya_mcp.tools.scene import SCENE_UNSAVED_CHANGES_ERROR

    ctx = _make_ctx(elicitation=SimpleNamespace(form=object(), url=None))
    ctx.session.elicit_form.return_value = SimpleNamespace(
        action="accept",
        content={"action": "discard"},
    )
    refusal = {
        "success": False,
        "previous_file": "C:/projects/current.ma",
        "was_modified": True,
        "error": SCENE_UNSAVED_CHANGES_ERROR,
    }
    success = {
        "success": True,
        "previous_file": "C:/projects/current.ma",
        "was_modified": True,
        "error": None,
    }

    with patch(
        "maya_mcp.registrars.scene.scene_new", side_effect=[refusal, success]
    ) as mock_scene_new:
        result = asyncio.run(tool_scene_new(force=False, ctx=ctx))

    assert result == success
    assert mock_scene_new.call_count == 2
    assert mock_scene_new.call_args_list[0].kwargs == {"force": False}
    assert mock_scene_new.call_args_list[1].kwargs == {"force": True}
    ctx.session.elicit_form.assert_awaited_once()


def test_scene_new_retries_with_force_via_worker_thread_after_elicitation_accept() -> None:
    """scene.new offloads both sync Maya calls when retrying after elicitation."""
    from maya_mcp.registrars import scene as scene_registrar
    from maya_mcp.tools.scene import SCENE_UNSAVED_CHANGES_ERROR

    ctx = _make_ctx(elicitation=SimpleNamespace(form=object(), url=None))
    ctx.session.elicit_form.return_value = SimpleNamespace(
        action="accept",
        content={"action": "discard"},
    )
    refusal = {
        "success": False,
        "previous_file": "C:/projects/current.ma",
        "was_modified": True,
        "error": SCENE_UNSAVED_CHANGES_ERROR,
    }
    success = {
        "success": True,
        "previous_file": "C:/projects/current.ma",
        "was_modified": True,
        "error": None,
    }
    async_to_thread = AsyncMock(side_effect=[refusal, success])

    with patch("maya_mcp.registrars.scene.asyncio.to_thread", async_to_thread):
        result = asyncio.run(scene_registrar.tool_scene_new(force=False, ctx=ctx))

    assert result == success
    assert async_to_thread.await_args_list == [
        call(scene_registrar.scene_new, force=False),
        call(scene_registrar.scene_new, force=True),
    ]
    ctx.session.elicit_form.assert_awaited_once()


def test_scene_new_empty_elicitation_capability_treated_as_form_support() -> None:
    """scene.new treats an empty elicitation capability object as form-capable."""
    from maya_mcp.registrars.scene import tool_scene_new
    from maya_mcp.tools.scene import SCENE_UNSAVED_CHANGES_ERROR

    ctx = _make_ctx(elicitation=SimpleNamespace(form=None, url=None))
    ctx.session.elicit_form.return_value = SimpleNamespace(
        action="accept",
        content={"action": "discard"},
    )
    refusal = {
        "success": False,
        "previous_file": None,
        "was_modified": True,
        "error": SCENE_UNSAVED_CHANGES_ERROR,
    }
    success = {
        "success": True,
        "previous_file": None,
        "was_modified": True,
        "error": None,
    }

    with patch(
        "maya_mcp.registrars.scene.scene_new", side_effect=[refusal, success]
    ) as mock_scene_new:
        result = asyncio.run(tool_scene_new(force=False, ctx=ctx))

    assert result == success
    assert mock_scene_new.call_count == 2
    ctx.session.elicit_form.assert_awaited_once()


def test_scene_open_keeps_refusal_for_url_only_clients() -> None:
    """scene.open does not use elicitation when the client only supports URL mode."""
    from maya_mcp.registrars.scene import tool_scene_open
    from maya_mcp.tools.scene import SCENE_UNSAVED_CHANGES_ERROR

    ctx = _make_ctx(elicitation=SimpleNamespace(form=None, url=object()))
    refusal = {
        "success": False,
        "file_path": None,
        "previous_file": "C:/projects/current.ma",
        "was_modified": True,
        "error": SCENE_UNSAVED_CHANGES_ERROR,
    }

    with patch("maya_mcp.registrars.scene.scene_open", return_value=refusal) as mock_scene_open:
        result = asyncio.run(tool_scene_open(file_path="C:/projects/next.ma", force=False, ctx=ctx))

    assert result == refusal
    assert mock_scene_open.call_count == 1
    assert mock_scene_open.call_args_list[0].kwargs == {
        "file_path": "C:/projects/next.ma",
        "force": False,
    }
    ctx.session.elicit_form.assert_not_awaited()


def test_scene_open_retries_with_force_after_form_elicitation_accept() -> None:
    """scene.open retries with force=True after a supported client confirms discard."""
    from maya_mcp.registrars.scene import tool_scene_open
    from maya_mcp.tools.scene import SCENE_UNSAVED_CHANGES_ERROR

    ctx = _make_ctx(elicitation=SimpleNamespace(form=object(), url=None))
    ctx.session.elicit_form.return_value = SimpleNamespace(
        action="accept",
        content={"action": "discard"},
    )
    refusal = {
        "success": False,
        "file_path": None,
        "previous_file": "C:/projects/current.ma",
        "was_modified": True,
        "error": SCENE_UNSAVED_CHANGES_ERROR,
    }
    success = {
        "success": True,
        "file_path": "C:/projects/next.ma",
        "previous_file": "C:/projects/current.ma",
        "was_modified": True,
        "error": None,
    }

    with patch(
        "maya_mcp.registrars.scene.scene_open", side_effect=[refusal, success]
    ) as mock_scene_open:
        result = asyncio.run(tool_scene_open(file_path="C:/projects/next.ma", force=False, ctx=ctx))

    assert result == success
    assert mock_scene_open.call_count == 2
    assert mock_scene_open.call_args_list[0].kwargs == {
        "file_path": "C:/projects/next.ma",
        "force": False,
    }
    assert mock_scene_open.call_args_list[1].kwargs == {
        "file_path": "C:/projects/next.ma",
        "force": True,
    }
    ctx.session.elicit_form.assert_awaited_once()


def test_scene_open_retries_with_force_via_worker_thread_after_elicitation_accept() -> None:
    """scene.open offloads both sync Maya calls when retrying after elicitation."""
    from maya_mcp.registrars import scene as scene_registrar
    from maya_mcp.tools.scene import SCENE_UNSAVED_CHANGES_ERROR

    ctx = _make_ctx(elicitation=SimpleNamespace(form=object(), url=None))
    ctx.session.elicit_form.return_value = SimpleNamespace(
        action="accept",
        content={"action": "discard"},
    )
    refusal = {
        "success": False,
        "file_path": None,
        "previous_file": "C:/projects/current.ma",
        "was_modified": True,
        "error": SCENE_UNSAVED_CHANGES_ERROR,
    }
    success = {
        "success": True,
        "file_path": "C:/projects/next.ma",
        "previous_file": "C:/projects/current.ma",
        "was_modified": True,
        "error": None,
    }
    async_to_thread = AsyncMock(side_effect=[refusal, success])

    with patch("maya_mcp.registrars.scene.asyncio.to_thread", async_to_thread):
        result = asyncio.run(
            scene_registrar.tool_scene_open(
                file_path="C:/projects/next.ma",
                force=False,
                ctx=ctx,
            )
        )

    assert result == success
    assert async_to_thread.await_args_list == [
        call(scene_registrar.scene_open, file_path="C:/projects/next.ma", force=False),
        call(scene_registrar.scene_open, file_path="C:/projects/next.ma", force=True),
    ]
    ctx.session.elicit_form.assert_awaited_once()


def test_scene_tools_list_schema_does_not_expose_context_argument() -> None:
    """Injected FastMCP context should not appear in scene tool input schemas."""
    from maya_mcp.server import mcp

    scene_new_tool = asyncio.run(mcp.get_tool("scene.new"))
    scene_open_tool = asyncio.run(mcp.get_tool("scene.open"))

    assert scene_new_tool is not None
    assert scene_open_tool is not None

    scene_new_schema = scene_new_tool.to_mcp_tool().inputSchema
    scene_open_schema = scene_open_tool.to_mcp_tool().inputSchema

    assert set(scene_new_schema["properties"]) == {"force"}
    assert set(scene_open_schema["properties"]) == {"file_path", "force"}
