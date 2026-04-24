"""Pytest configuration for integration tests.

Integration tests require a running Maya instance with commandPort enabled.
These tests are skipped in CI and must be run manually.

To enable Maya commandPort, run in Maya's Script Editor:

    import maya.cmds as cmds
    try:
        cmds.commandPort(name=":7001", close=True)
    except RuntimeError:
        pass
    cmds.commandPort(name=":7001", sourceType="python", echoOutput=True)
"""

from __future__ import annotations

import socket
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

    from maya_mcp.transport.commandport import CommandPortClient


def is_maya_available(host: str = "localhost", port: int = 7001) -> bool:
    """Check if Maya commandPort is available.

    Args:
        host: The host to check.
        port: The port to check.

    Returns:
        True if Maya commandPort is listening.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except OSError:
        return False


# Skip all integration tests if Maya is not available
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip integration tests if Maya is not running."""
    if not is_maya_available():
        skip_maya = pytest.mark.skip(reason="Maya commandPort not available at localhost:7001")
        for item in items:
            if "integration" in str(item.fspath):
                item.add_marker(skip_maya)


@pytest.fixture(scope="session")
def maya_available() -> bool:
    """Fixture indicating if Maya is available.

    Returns:
        True if Maya commandPort is reachable.
    """
    return is_maya_available()


@pytest.fixture(scope="function")
def maya_client() -> Generator[CommandPortClient, None, None]:
    """Provide a connected CommandPortClient for testing.

    This fixture creates a fresh client for each test and ensures
    cleanup after the test completes. It also installs the client as the
    transport singleton so tool calls and fixture setup share one commandPort
    socket.

    Yields:
        A connected CommandPortClient instance.
    """
    import maya_mcp.transport.commandport as transport_module
    from maya_mcp.transport.commandport import CommandPortClient

    original_client = transport_module._client
    client = CommandPortClient(
        host="localhost",
        port=7001,
        connect_timeout=5.0,
        command_timeout=30.0,
        max_retries=1,  # Don't retry too much in tests
    )
    client.connect()
    transport_module._client = client

    try:
        yield client
    finally:
        transport_module._client = original_client
        client.disconnect()


@pytest.fixture(scope="function")
def clean_scene(maya_client: CommandPortClient) -> Generator[None, None, None]:
    """Ensure a clean Maya scene for testing.

    Creates a new empty scene before the test and clears selection
    after the test.

    Args:
        maya_client: The Maya client fixture.

    Yields:
        None (provides clean scene state).
    """
    # Create new empty scene
    maya_client.execute("import maya.cmds as cmds; cmds.file(new=True, force=True)")
    # Flush after the new-scene command completes so Maya startup/plugin callbacks
    # do not become the first undo item in live tests.
    maya_client.execute("import maya.cmds as cmds; cmds.flushUndo()")

    yield

    # Clear selection after test
    maya_client.execute("import maya.cmds as cmds; cmds.select(clear=True)")


@pytest.fixture(scope="function")
def test_cube(maya_client: CommandPortClient, clean_scene: None) -> Generator[str, None, None]:
    """Create a test cube for testing.

    Creates a polyCube named 'testCube1' for use in tests.

    Args:
        maya_client: The Maya client fixture.
        clean_scene: Ensures clean scene first.

    Yields:
        The name of the created cube transform.
    """
    # Create a test cube
    maya_client.execute("import maya.cmds as cmds; cmds.polyCube(name='testCube1')")

    yield "testCube1"

    # Cleanup handled by clean_scene


@pytest.fixture(scope="function")
def test_objects(
    maya_client: CommandPortClient, clean_scene: None
) -> Generator[list[str], None, None]:
    """Create multiple test objects for testing.

    Creates a cube, sphere, and cone for use in tests.

    Args:
        maya_client: The Maya client fixture.
        clean_scene: Ensures clean scene first.

    Yields:
        List of created object names.
    """
    command = """
import maya.cmds as cmds
cmds.polyCube(name='testCube1')
cmds.polySphere(name='testSphere1')
cmds.polyCone(name='testCone1')
"""
    maya_client.execute(command)

    yield ["testCube1", "testSphere1", "testCone1"]

    # Cleanup handled by clean_scene
