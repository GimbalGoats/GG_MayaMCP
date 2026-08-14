"""Maya commandPort compatibility policy tests."""

from __future__ import annotations

import base64
import builtins
import json
import runpy
import sys
import types
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import __main__

if TYPE_CHECKING:
    from collections.abc import Iterator

from maya_mcp.maya_panel import controller
from maya_mcp.maya_panel.commandport_compat import (
    MAYA_2024_COMMAND_PORT_BUFFER_SIZE,
    MAYA_2024_HANDLER_NAME,
    MAYA_2024_PORTS_NAME,
    MAYA_2024_STATE_NAME,
    command_port_open_kwargs,
    is_loopback_command_port_name,
    mark_maya_2024_compatible_port,
)


@pytest.fixture(autouse=True)
def _clear_maya_2024_builtins() -> Iterator[None]:
    names = (MAYA_2024_HANDLER_NAME, MAYA_2024_STATE_NAME, MAYA_2024_PORTS_NAME)
    main_namespace = vars(__main__)
    original_main = dict(main_namespace)
    for name in names:
        vars(builtins).pop(name, None)
    yield
    for name in names:
        vars(builtins).pop(name, None)
    for name in set(main_namespace) - set(original_main):
        main_namespace.pop(name, None)
    main_namespace.update(original_main)


class FakeCmds:
    def __init__(self, major_version: str) -> None:
        self.major_version = major_version

    def about(self, *, majorVersion: bool = False) -> str:
        assert majorVersion
        return self.major_version


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (":7002", True),
        ("localhost:7002", False),
        ("127.0.0.1:7002", False),
        ("[::1]:7002", False),
        ("7002", False),
        ("/tmp/maya:7002", False),
        ("maya-command-7002", False),
    ],
)
def test_loopback_tcp_port_names_do_not_match_unix_domain_names(
    name: str,
    expected: bool,
) -> None:
    assert is_loopback_command_port_name(name, 7002) is expected


@pytest.mark.parametrize("maya_version", ["2022", "2023", "2024"])
def test_maya_2022_through_2024_install_full_command_response_handler(
    maya_version: str,
) -> None:
    kwargs = command_port_open_kwargs(FakeCmds(maya_version), "python", True)

    assert kwargs == {
        "sourceType": "python",
        "echoOutput": False,
        "bufferSize": MAYA_2024_COMMAND_PORT_BUFFER_SIZE,
    }
    assert callable(getattr(builtins, MAYA_2024_HANDLER_NAME))


def test_maya_2024_buffer_covers_worst_case_approved_script_framing() -> None:
    json_escaped_script = json.dumps("\x00" * 1_048_576)
    framed_size = len(base64.b64encode(json_escaped_script.encode("utf-8"))) + 128

    assert framed_size < MAYA_2024_COMMAND_PORT_BUFFER_SIZE


def test_maya_2024_handler_executes_compound_multiline_python_once() -> None:
    command_port_open_kwargs(FakeCmds("2024"), "python", True)
    handler = getattr(builtins, MAYA_2024_HANDLER_NAME)
    command = """import json
values = []
if True:
    values.append("first")
    values.append("second")
else:
    values.append("wrong")
print(json.dumps(values))"""

    response = handler(command)

    assert json.loads(str(response["result"])) == ["first", "second"]


def test_maya_2024_handler_preserves_expression_results() -> None:
    command_port_open_kwargs(FakeCmds("2024"), "python", True)
    handler = getattr(builtins, MAYA_2024_HANDLER_NAME)

    assert handler("values = ['pCube1', 'pSphere1']\nvalues") == {
        "ok": True,
        "result": "['pCube1', 'pSphere1']",
    }


def test_maya_2024_handler_uses_maya_main_namespace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(__main__, "maya_mcp_existing_helper", lambda: "available", raising=False)
    command_port_open_kwargs(FakeCmds("2024"), "python", True)
    handler = getattr(builtins, MAYA_2024_HANDLER_NAME)

    assert handler("maya_mcp_existing_helper()") == {"ok": True, "result": "available"}


def test_maya_2024_handler_does_not_mutate_or_retain_main_namespace() -> None:
    command_port_open_kwargs(FakeCmds("2024"), "python", True)
    handler = getattr(builtins, MAYA_2024_HANDLER_NAME)

    assert handler("maya_mcp_temporary = ['large', 'result']\nmaya_mcp_temporary") == {
        "ok": True,
        "result": "['large', 'result']",
    }
    assert "maya_mcp_temporary" not in vars(__main__)
    assert handler("'maya_mcp_temporary' in globals()") == {"ok": True, "result": "False"}


def test_maya_2024_handler_does_not_inherit_helper_future_flags() -> None:
    command_port_open_kwargs(FakeCmds("2024"), "python", True)
    handler = getattr(builtins, MAYA_2024_HANDLER_NAME)

    response = handler("value: MissingAnnotation = 1")

    assert response["ok"] is False
    assert str(response["error"]).startswith("NameError:")


def test_maya_2024_handler_serializes_command_errors() -> None:
    command_port_open_kwargs(FakeCmds("2024"), "python", True)
    handler = getattr(builtins, MAYA_2024_HANDLER_NAME)

    assert handler("raise ValueError('boom')") == {
        "ok": False,
        "error": "ValueError: boom",
    }


@pytest.mark.parametrize("major_version", ["2025", "2026", "2030"])
def test_maya_2025_and_later_keep_existing_command_port_path(major_version: str) -> None:
    kwargs = command_port_open_kwargs(FakeCmds(major_version), "python", True)

    assert kwargs == {"sourceType": "python", "echoOutput": True}


def test_explicit_mel_mode_is_preserved_on_maya_2024() -> None:
    assert command_port_open_kwargs(FakeCmds("2024"), "mel", True) == {
        "sourceType": "mel",
        "echoOutput": True,
    }


def _install_fake_maya(
    monkeypatch: pytest.MonkeyPatch,
    major_version: str,
    *,
    open_ports: list[str] | None = None,
) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    class FakeMayaCmds(FakeCmds):
        def commandPort(self, **kwargs: object) -> list[str]:
            if kwargs.get("query") and kwargs.get("listPorts"):
                return open_ports or []
            calls.append(kwargs)
            return []

        def evalDeferred(self, _callback: object) -> None:
            return None

    fake_cmds = FakeMayaCmds(major_version)
    maya_module = types.ModuleType("maya")
    maya_module.cmds = fake_cmds  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "maya", maya_module)
    monkeypatch.setitem(sys.modules, "maya.cmds", fake_cmds)
    return calls


def test_control_panel_applies_maya_2024_compatibility_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_maya(monkeypatch, "2024")

    assert controller.open_command_port(7002)

    assert calls[-1]["sourceType"] == "python"
    assert calls[-1]["echoOutput"] is False
    assert calls[-1]["bufferSize"] == MAYA_2024_COMMAND_PORT_BUFFER_SIZE


def test_control_panel_replaces_an_existing_broken_maya_2024_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_maya(monkeypatch, "2024", open_ports=[":7002"])

    assert controller.open_command_port(7002, replace_existing=True)

    assert calls[0] == {"name": ":7002", "close": True}
    assert calls[1]["echoOutput"] is False
    assert calls[1]["bufferSize"] == MAYA_2024_COMMAND_PORT_BUFFER_SIZE

    calls.clear()
    assert controller.open_command_port(7002)
    assert calls[0] == {"name": ":7002", "close": True}
    assert calls[1]["bufferSize"] == MAYA_2024_COMMAND_PORT_BUFFER_SIZE

    calls.clear()
    assert controller.open_command_port(7002, replace_existing=True)
    assert calls[0] == {"name": ":7002", "close": True}
    assert calls[1]["bufferSize"] == MAYA_2024_COMMAND_PORT_BUFFER_SIZE


def test_control_panel_reports_unmarked_maya_2024_inet_port_as_incompatible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_maya(monkeypatch, "2024", open_ports=[":7002"])

    assert controller.open_command_port(7002) is False
    assert calls == []


def test_control_panel_opens_inet_beside_named_socket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_maya(monkeypatch, "2024", open_ports=["localhost:7002"])

    assert controller.open_command_port(7002)

    assert calls[-1]["name"] == ":7002"
    assert {"name": "localhost:7002", "close": True} not in calls


def test_port_status_ignores_named_socket_with_port_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_maya(monkeypatch, "2024", open_ports=["127.0.0.1:7002"])

    status = controller.get_port_status(7002)

    assert status["is_open"] is False
    assert status["port_name"] == ":7002"


def test_control_panel_ignores_unix_domain_command_port_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_maya(
        monkeypatch,
        "2024",
        open_ports=["7002", "/tmp/maya:7002"],
    )

    assert controller.get_open_port_name(7002) is None
    assert controller.open_command_port(7002)
    assert calls[-1]["name"] == ":7002"


def test_manual_enable_script_applies_maya_2024_compatibility_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_maya(monkeypatch, "2024")

    namespace = runpy.run_path(str(Path("scripts/enable_commandport.py")))
    namespace["enable_commandport"](7002)

    assert calls[-1]["sourceType"] == "python"
    assert calls[-1]["echoOutput"] is False
    assert calls[-1]["bufferSize"] == MAYA_2024_COMMAND_PORT_BUFFER_SIZE


def test_user_setup_applies_maya_2024_compatibility_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_maya(monkeypatch, "2024")

    namespace = runpy.run_path(str(Path("scripts/userSetup.py")))
    namespace["_start_command_port"]()

    assert calls[-1]["sourceType"] == "python"
    assert calls[-1]["echoOutput"] is False
    assert calls[-1]["bufferSize"] == MAYA_2024_COMMAND_PORT_BUFFER_SIZE


def test_user_setup_explicitly_replaces_an_owned_broken_maya_2024_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_maya(monkeypatch, "2024", open_ports=[":7001"])

    namespace = runpy.run_path(str(Path("scripts/userSetup.py")))
    namespace["_start_command_port"].__globals__["REPLACE_EXISTING_COMMAND_PORT"] = True
    namespace["_start_command_port"]()

    assert calls[0] == {"name": ":7001", "close": True}
    assert calls[1]["echoOutput"] is False


def test_user_setup_refreshes_a_marked_maya_2024_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_maya(monkeypatch, "2024", open_ports=[":7001"])
    mark_maya_2024_compatible_port(7001)

    namespace = runpy.run_path(str(Path("scripts/userSetup.py")))
    namespace["_start_command_port"]()

    assert calls[0] == {"name": ":7001", "close": True}
    assert calls[1]["bufferSize"] == MAYA_2024_COMMAND_PORT_BUFFER_SIZE


def test_user_setup_opens_inet_beside_named_socket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_maya(monkeypatch, "2024", open_ports=["localhost:7001"])

    namespace = runpy.run_path(str(Path("scripts/userSetup.py")))
    namespace["_start_command_port"]()

    assert calls[-1]["name"] == ":7001"
    assert {"name": "localhost:7001", "close": True} not in calls


def test_existing_maya_2025_port_is_left_untouched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_maya(monkeypatch, "2025", open_ports=[":7001"])

    namespace = runpy.run_path(str(Path("scripts/userSetup.py")))
    namespace["_start_command_port"]()

    assert calls == []


def test_manual_script_replaces_inet_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_maya(monkeypatch, "2024", open_ports=[":7002"])

    namespace = runpy.run_path(str(Path("scripts/enable_commandport.py")))
    namespace["enable_commandport"](7002)

    assert calls[0] == {"name": ":7002", "close": True}
    assert calls[1]["name"] == ":7002"


def test_maya_2024_port_compatibility_marker_is_port_specific() -> None:
    mark_maya_2024_compatible_port(7001)

    ports = vars(builtins)["_maya_mcp_command_port_2024_ports"]

    assert 7001 in ports
    assert 7002 not in ports


def test_standalone_paths_leave_maya_2025_on_existing_behavior(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_maya(monkeypatch, "2025")

    manual = runpy.run_path(str(Path("scripts/enable_commandport.py")))
    manual["enable_commandport"](7002)
    startup = runpy.run_path(str(Path("scripts/userSetup.py")))
    startup["_start_command_port"]()

    assert all(call["sourceType"] == "python" for call in calls)
    assert all(call["echoOutput"] is True for call in calls)
    assert calls[0]["bufferSize"] == 16384
    assert "bufferSize" not in calls[1]


@pytest.mark.parametrize("script", ["scripts/enable_commandport.py", "scripts/userSetup.py"])
def test_packaged_helpers_skip_standalone_fallback_imports(
    monkeypatch: pytest.MonkeyPatch,
    script: str,
) -> None:
    _install_fake_maya(monkeypatch, "2025")
    imported_modules: list[str] = []
    real_import = builtins.__import__

    def track_import(name: str, *args: object, **kwargs: object) -> object:
        imported_modules.append(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", track_import)
    runpy.run_path(str(Path(script)))

    assert {"ast", "builtins", "contextlib", "io"}.isdisjoint(imported_modules)


@pytest.mark.parametrize("script", ["scripts/enable_commandport.py", "scripts/userSetup.py"])
def test_standalone_fallback_works_without_installed_package(
    monkeypatch: pytest.MonkeyPatch,
    script: str,
) -> None:
    calls = _install_fake_maya(monkeypatch, "2024")
    real_import = builtins.__import__

    def import_without_package(name: str, *args: object, **kwargs: object) -> object:
        if name == "maya_mcp.maya_panel.commandport_compat":
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_package)
    namespace = runpy.run_path(str(Path(script)))
    assert namespace["is_loopback_command_port_name"]("/tmp/maya:7002", 7002) is False
    if script.endswith("userSetup.py"):
        namespace["_start_command_port"]()
    else:
        namespace["enable_commandport"](7002)
    handler = vars(builtins)[MAYA_2024_HANDLER_NAME]

    assert calls[-1]["echoOutput"] is False
    assert calls[-1]["bufferSize"] == MAYA_2024_COMMAND_PORT_BUFFER_SIZE
    assert handler("if True:\n    print('first')\n    print('second')") == {
        "ok": True,
        "result": "first\nsecond\n",
    }
    assert handler("print('tick')\nprint('tick')") == {
        "ok": True,
        "result": "tick\ntick\n",
    }
    assert handler("False") == {"ok": True, "result": "False"}
    assert str(handler("value: MissingAnnotation = 1")["error"]).startswith("NameError:")
    assert handler("raise ValueError('boom')") == {
        "ok": False,
        "error": "ValueError: boom",
    }
