"""Maya MCP Control Panel - Qt dockable widget.

This module provides a dockable Qt widget for controlling Maya's commandPort
and monitoring MCP connections from within Maya.

Note:
    This module MUST be run inside Maya's Python interpreter.
    It supports both PySide2 (Maya 2022-2024) and PySide6 (Maya 2025+).

Features:
    - Status indicator (green/red/yellow)
    - Start/Stop commandPort button
    - Port configuration
    - Connection log showing recent MCP requests
    - Auto-start option

Example:
    Show the panel::

        from maya_mcp.maya_panel import show_panel
        show_panel()
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from maya_mcp.maya_panel.controller import (
    close_command_port,
    is_command_port_open,
    open_command_port,
)
from maya_mcp.maya_panel.preferences import (
    get_auto_start,
    get_port,
    set_auto_start,
    set_port,
)

logger = logging.getLogger(__name__)

# Panel object name for Maya workspace control
PANEL_OBJECT_NAME = "MCPControlPanel"
PANEL_WORKSPACE_NAME = PANEL_OBJECT_NAME + "WorkspaceControl"
PANEL_TITLE = "MCP Control"

# Status colors
STATUS_COLORS = {
    "running": "#4CAF50",  # Green
    "stopped": "#f44336",  # Red
    "unknown": "#FFC107",  # Yellow/Amber
}


def _get_qt_modules() -> tuple[Any, Any, Any]:
    """Get Qt modules, supporting both PySide2 (Maya 2022-2024) and PySide6 (Maya 2025+).

    Returns:
        Tuple of (QtCore, QtGui, QtWidgets) modules.

    Raises:
        ImportError: If neither PySide2 nor PySide6 is available.
    """
    try:
        # Maya 2025+ uses PySide6
        from PySide6 import QtCore, QtGui, QtWidgets

        return QtCore, QtGui, QtWidgets
    except ImportError:
        # Maya 2022-2024 uses PySide2
        from PySide2 import QtCore, QtGui, QtWidgets

        return QtCore, QtGui, QtWidgets


def _get_maya_mixin() -> Any:
    """Get Maya's dockable mixin class.

    Returns:
        MayaQWidgetDockableMixin class.
    """
    from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

    return MayaQWidgetDockableMixin


def _create_panel_class() -> type:
    """Dynamically create the panel class with proper Qt inheritance.

    This is necessary because we need to inherit from both MayaQWidgetDockableMixin
    and QWidget, but we don't know which Qt version is available until runtime.
    """
    QtCore, QtGui, QtWidgets = _get_qt_modules()
    MayaQWidgetDockableMixin = _get_maya_mixin()

    class MCPControlPanelWidget(MayaQWidgetDockableMixin, QtWidgets.QWidget):
        """Dockable Qt panel for controlling Maya MCP commandPort.

        This panel provides:
            - Visual status indicator (green/red)
            - Start/Stop button for commandPort
            - Port number configuration
            - Auto-start checkbox (persisted)
            - Connection log with timestamps
        """

        def __init__(self, parent: Any = None) -> None:
            """Initialize the MCP Control Panel."""
            super().__init__(parent=parent)

            self.setObjectName(PANEL_OBJECT_NAME)
            self.setWindowTitle(PANEL_TITLE)

            self._port: int = get_port()
            self._auto_start: bool = get_auto_start()
            self._log_entries: list[str] = []
            self._max_log_entries: int = 100

            # UI widgets
            self._status_label: Any = None
            self._status_indicator: Any = None
            self._start_stop_button: Any = None
            self._port_spinbox: Any = None
            self._auto_start_checkbox: Any = None
            self._log_text: Any = None
            self._timer: Any = None

            self._create_ui()
            self._start_status_timer()
            self._update_status()

        def _create_ui(self) -> None:
            """Create the panel UI widgets."""
            # Main layout
            main_layout = QtWidgets.QVBoxLayout(self)
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(10)

            # === Status Section ===
            status_group = QtWidgets.QGroupBox("Server Status")
            status_layout = QtWidgets.QHBoxLayout(status_group)

            # Status indicator (colored circle)
            self._status_indicator = QtWidgets.QLabel()
            self._status_indicator.setFixedSize(20, 20)
            self._update_status_indicator("unknown")
            status_layout.addWidget(self._status_indicator)

            # Status text
            self._status_label = QtWidgets.QLabel("Checking...")
            self._status_label.setStyleSheet("font-weight: bold;")
            status_layout.addWidget(self._status_label)

            status_layout.addStretch()
            main_layout.addWidget(status_group)

            # === Control Section ===
            control_group = QtWidgets.QGroupBox("Controls")
            control_layout = QtWidgets.QFormLayout(control_group)

            # Port configuration
            port_layout = QtWidgets.QHBoxLayout()
            self._port_spinbox = QtWidgets.QSpinBox()
            self._port_spinbox.setRange(1, 65535)
            self._port_spinbox.setValue(self._port)
            self._port_spinbox.valueChanged.connect(self._on_port_changed)
            port_layout.addWidget(self._port_spinbox)

            # Apply button for port change
            apply_port_btn = QtWidgets.QPushButton("Apply")
            apply_port_btn.setFixedWidth(60)
            apply_port_btn.clicked.connect(self._on_apply_port)
            port_layout.addWidget(apply_port_btn)

            control_layout.addRow("Port:", port_layout)

            # Start/Stop button
            self._start_stop_button = QtWidgets.QPushButton("Start Server")
            self._start_stop_button.setMinimumHeight(40)
            self._start_stop_button.clicked.connect(self._on_start_stop_clicked)
            control_layout.addRow("", self._start_stop_button)

            # Auto-start checkbox
            self._auto_start_checkbox = QtWidgets.QCheckBox("Auto-start on Maya launch")
            self._auto_start_checkbox.setChecked(self._auto_start)
            self._auto_start_checkbox.toggled.connect(self._on_auto_start_toggled)
            control_layout.addRow("", self._auto_start_checkbox)

            main_layout.addWidget(control_group)

            # === Log Section ===
            log_group = QtWidgets.QGroupBox("Connection Log")
            log_layout = QtWidgets.QVBoxLayout(log_group)

            self._log_text = QtWidgets.QTextEdit()
            self._log_text.setReadOnly(True)
            self._log_text.setFont(QtGui.QFont("Consolas", 9))
            self._log_text.setStyleSheet(
                "background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c;"
            )
            log_layout.addWidget(self._log_text)

            # Clear log button
            clear_log_btn = QtWidgets.QPushButton("Clear Log")
            clear_log_btn.clicked.connect(self._on_clear_log)
            log_layout.addWidget(clear_log_btn)

            main_layout.addWidget(log_group)

            # Add initial log entry
            self._add_log_entry("Panel initialized")

        def _start_status_timer(self) -> None:
            """Start a timer to periodically update the status."""
            if self._timer is not None:
                self._timer.stop()

            self._timer = QtCore.QTimer(self)
            self._timer.timeout.connect(self._update_status)
            self._timer.start(2000)  # Update every 2 seconds

        def _update_status(self) -> None:
            """Update the status indicator and label."""
            try:
                is_open = is_command_port_open(self._port)

                if is_open:
                    self._update_status_indicator("running")
                    self._status_label.setText(f"Running on port {self._port}")
                    self._start_stop_button.setText("Stop Server")
                    self._start_stop_button.setStyleSheet(
                        "background-color: #c62828; color: white;"
                    )
                else:
                    self._update_status_indicator("stopped")
                    self._status_label.setText("Stopped")
                    self._start_stop_button.setText("Start Server")
                    self._start_stop_button.setStyleSheet(
                        "background-color: #2e7d32; color: white;"
                    )
            except Exception as e:
                self._update_status_indicator("unknown")
                self._status_label.setText(f"Error: {e}")
                logger.exception("Error updating status")

        def _update_status_indicator(self, status: str) -> None:
            """Update the colored status indicator."""
            color = STATUS_COLORS.get(status, STATUS_COLORS["unknown"])
            self._status_indicator.setStyleSheet(
                f"background-color: {color}; border-radius: 10px; border: 1px solid #333;"
            )

        def _on_start_stop_clicked(self) -> None:
            """Handle start/stop button click."""
            try:
                if is_command_port_open(self._port):
                    close_command_port(self._port)
                    self._add_log_entry(f"Server stopped on port {self._port}")
                else:
                    open_command_port(self._port)
                    self._add_log_entry(f"Server started on port {self._port}")

                self._update_status()
            except Exception as e:
                self._add_log_entry(f"ERROR: {e}")
                logger.exception("Error toggling server")

        def _on_port_changed(self, value: int) -> None:
            """Handle port spinbox value change."""
            # Just update the internal value, don't apply yet
            pass

        def _on_apply_port(self) -> None:
            """Apply the port change."""
            new_port = self._port_spinbox.value()
            old_port = self._port

            if new_port == old_port:
                return

            try:
                # Close old port if open
                if is_command_port_open(old_port):
                    close_command_port(old_port)
                    self._add_log_entry(f"Closed port {old_port}")

                    # Open new port
                    open_command_port(new_port)
                    self._add_log_entry(f"Opened port {new_port}")

                # Save new port
                self._port = new_port
                set_port(new_port)
                self._add_log_entry(f"Port changed to {new_port}")

                self._update_status()
            except Exception as e:
                self._add_log_entry(f"ERROR changing port: {e}")
                # Try to restore old port
                self._port_spinbox.setValue(old_port)
                logger.exception("Error changing port")

        def _on_auto_start_toggled(self, checked: bool) -> None:
            """Handle auto-start checkbox toggle."""
            self._auto_start = checked
            set_auto_start(checked)
            status = "enabled" if checked else "disabled"
            self._add_log_entry(f"Auto-start {status}")

        def _on_clear_log(self) -> None:
            """Clear the connection log."""
            self._log_entries.clear()
            self._log_text.clear()
            self._add_log_entry("Log cleared")

        def _add_log_entry(self, message: str) -> None:
            """Add an entry to the connection log."""
            timestamp = datetime.now().strftime("%H:%M:%S")
            entry = f"[{timestamp}] {message}"

            self._log_entries.append(entry)

            # Trim if too many entries
            if len(self._log_entries) > self._max_log_entries:
                self._log_entries = self._log_entries[-self._max_log_entries :]

            # Update the text widget
            if self._log_text is not None:
                self._log_text.append(entry)
                # Scroll to bottom
                scrollbar = self._log_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

        def closeEvent(self, event: Any) -> None:
            """Handle panel close."""
            if self._timer is not None:
                self._timer.stop()
                self._timer = None
            super().closeEvent(event)

    return MCPControlPanelWidget


# Cache the panel class once created
_PanelClass: type | None = None
# Keep reference to the panel instance
_panel_instance: Any = None


def show_panel() -> Any:
    """Show the MCP Control Panel.

    Creates and shows the dockable panel. If the panel already exists,
    it will be deleted and recreated.

    Returns:
        The MCPControlPanel widget instance.

    Example:
        >>> from maya_mcp.maya_panel import show_panel
        >>> panel = show_panel()
    """
    import maya.cmds as cmds

    global _PanelClass, _panel_instance

    # Create panel class if needed
    if _PanelClass is None:
        _PanelClass = _create_panel_class()

    # Delete existing workspace control if it exists
    if cmds.workspaceControl(PANEL_WORKSPACE_NAME, exists=True):
        cmds.deleteUI(PANEL_WORKSPACE_NAME)

    # Create and show the panel
    _panel_instance = _PanelClass()
    _panel_instance.show(dockable=True, floating=True, width=300, height=400)

    return _panel_instance


def auto_start_if_enabled() -> None:
    """Auto-start commandPort if enabled in preferences.

    This function should be called from userSetup.py to automatically
    open the commandPort when Maya starts.

    Example:
        In userSetup.py::

            from maya_mcp.maya_panel import auto_start_if_enabled
            auto_start_if_enabled()
    """
    if get_auto_start():
        port = get_port()
        try:
            open_command_port(port)
            logger.info("Auto-started commandPort on port %d", port)
        except Exception:
            logger.exception("Failed to auto-start commandPort")


# For backwards compatibility
MCPControlPanel = None  # Will be set dynamically when show_panel is called
