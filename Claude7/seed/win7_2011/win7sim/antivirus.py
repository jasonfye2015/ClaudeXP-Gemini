"""Simulated Windows Defender status, tray menu, and scan window."""

from __future__ import annotations

from datetime import datetime
import time

from PySide6.QtCore import QObject, QPointF, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QMenu,
)


class WindowsDefenderService(QObject):
    """Session-only protection simulation; it never inspects local files."""

    changed = Signal()
    maintenanceModeChanged = Signal(bool)
    scanFinished = Signal(str, int)

    SCAN_DURATIONS_MS = {"quick": 8_000, "full": 24_000}
    SIMULATED_ITEMS = {"quick": 6_200, "full": 48_000}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scan_running = False
        self.scan_kind = ""
        self.progress = 0
        self.items_checked = 0
        self.status_message = "Ready. No scan has been run this session."
        self.last_scan = "Never"
        self.last_result = ""
        self._started_at = 0.0
        self._duration_ms = 0
        self._priority_active = False

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._update_scan)

    def start_scan(self, kind: str = "quick", *, duration_ms: int | None = None) -> bool:
        if kind not in self.SCAN_DURATIONS_MS:
            raise ValueError("Scan type must be quick or full.")
        if self.scan_running:
            return False
        if duration_ms is not None and (
            type(duration_ms) is not int or not 1 <= duration_ms <= 3_600_000
        ):
            raise ValueError("Scan duration must be a whole number from 1 to 3600000 ms.")

        self.scan_kind = kind
        self._duration_ms = duration_ms or self.SCAN_DURATIONS_MS[kind]
        self._started_at = time.monotonic()
        self.progress = 0
        self.items_checked = 0
        self.last_result = ""
        self.scan_running = True
        self.status_message = (
            f"{kind.title()} scan is running. This is a simulation; no files are read."
        )
        self._set_maintenance_mode(True)
        self._timer.start()
        self.changed.emit()
        return True

    def cancel_scan(self) -> None:
        if not self.scan_running:
            return
        kind = self.scan_kind
        self._timer.stop()
        self.scan_running = False
        self.status_message = f"{kind.title()} scan canceled."
        self._set_maintenance_mode(False)
        self.changed.emit()

    def check_for_updates(self) -> None:
        self.status_message = "Security definitions are up to date (simulation)."
        self.changed.emit()

    def stop(self) -> None:
        self._timer.stop()
        was_running = self.scan_running
        self.scan_running = False
        if was_running or self._priority_active:
            self._set_maintenance_mode(False)

    def _set_maintenance_mode(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if self._priority_active == enabled:
            return
        self._priority_active = enabled
        self.maintenanceModeChanged.emit(enabled)

    def _update_scan(self) -> None:
        if not self.scan_running:
            return
        elapsed_ms = (time.monotonic() - self._started_at) * 1000
        self.progress = min(100, int(elapsed_ms * 100 / self._duration_ms))
        item_count = self.SIMULATED_ITEMS[self.scan_kind]
        self.items_checked = item_count * self.progress // 100
        if self.progress >= 100:
            self._finish_scan()
        else:
            self.changed.emit()

    def _finish_scan(self) -> None:
        kind = self.scan_kind
        self._timer.stop()
        self.scan_running = False
        self.progress = 100
        self.items_checked = self.SIMULATED_ITEMS[kind]
        self.last_scan = f"{kind.title()} scan at {datetime.now().astimezone():%I:%M %p}".lstrip("0")
        self.last_result = (
            f"{kind.title()} scan complete: {self.items_checked:,} simulated items checked; "
            "no threats found (simulation)."
        )
        self.status_message = self.last_result
        self._set_maintenance_mode(False)
        self.scanFinished.emit(kind, self.items_checked)
        self.changed.emit()


class WindowsDefenderTrayButton(QToolButton):
    """The Defender shield placed in the simulated Windows notification area."""

    openRequested = Signal()
    aboutRequested = Signal()

    def __init__(self, service: WindowsDefenderService, parent=None):
        super().__init__(parent)
        self.service = service
        self.setObjectName("windowsDefenderTray")
        self.setAccessibleName("Windows Defender")
        self.setFixedSize(32, 30)
        self.setIconSize(QSize(26, 26))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        self.context_menu = QMenu(self)
        self.open_action = self.context_menu.addAction("Open Windows Defender")
        self.context_menu.addSeparator()
        self.quick_scan_action = self.context_menu.addAction("Quick scan")
        self.full_scan_action = self.context_menu.addAction("Full scan")
        self.cancel_scan_action = self.context_menu.addAction("Cancel scan")
        self.context_menu.addSeparator()
        self.update_action = self.context_menu.addAction("Check for updates")
        self.about_action = self.context_menu.addAction("About Windows Defender")
        self.setMenu(self.context_menu)

        self.open_action.triggered.connect(self.openRequested.emit)
        self.quick_scan_action.triggered.connect(
            lambda: service.start_scan("quick")
        )
        self.full_scan_action.triggered.connect(
            lambda: service.start_scan("full")
        )
        self.cancel_scan_action.triggered.connect(service.cancel_scan)
        self.update_action.triggered.connect(service.check_for_updates)
        self.about_action.triggered.connect(self.aboutRequested.emit)
        service.changed.connect(self._refresh)
        self._refresh()

    def _refresh(self) -> None:
        self.cancel_scan_action.setEnabled(self.service.scan_running)
        self.quick_scan_action.setEnabled(not self.service.scan_running)
        self.full_scan_action.setEnabled(not self.service.scan_running)
        self.setToolTip(
            "Windows Defender — "
            + ("Simulated scan in progress" if self.service.scan_running
               else "Protection active (simulation)")
        )
        self.setIcon(_shield_icon(self.service.scan_running))


class WindowsDefenderApp(QWidget):
    """Simple control panel for the simulated Windows Defender service."""

    def __init__(self, service: WindowsDefenderService, parent=None):
        super().__init__(parent)
        self.service = service
        self.setObjectName("windowsDefender")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header_icon = QLabel()
        header_icon.setPixmap(_shield_icon(False).pixmap(42, 42))
        header.addWidget(header_icon)
        title = QLabel("Windows Defender")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #244d72;")
        header.addWidget(title, 1)
        layout.addLayout(header)

        self.protection_panel = QFrame()
        self.protection_panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel_layout = QVBoxLayout(self.protection_panel)
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.detail_label = QLabel()
        self.detail_label.setWordWrap(True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.last_scan_label = QLabel()
        panel_layout.addWidget(self.status_label)
        panel_layout.addWidget(self.detail_label)
        panel_layout.addWidget(self.progress_bar)
        panel_layout.addWidget(self.last_scan_label)
        layout.addWidget(self.protection_panel)

        note = QLabel(
            "Simulation only: scans do not inspect, modify, or quarantine real files. "
            "During a scan, queued background AI work gets priority; an active generation "
            "is never interrupted."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #4a5e70;")
        layout.addWidget(note)

        buttons = QHBoxLayout()
        self.quick_scan_button = QPushButton("Quick scan")
        self.full_scan_button = QPushButton("Full scan")
        self.cancel_scan_button = QPushButton("Stop scan")
        self.update_button = QPushButton("Check for updates")
        self.about_button = QPushButton("About")
        for button in (
            self.quick_scan_button, self.full_scan_button,
            self.cancel_scan_button, self.update_button, self.about_button,
        ):
            buttons.addWidget(button)
        layout.addLayout(buttons)

        self.quick_scan_button.clicked.connect(
            lambda: service.start_scan("quick")
        )
        self.full_scan_button.clicked.connect(
            lambda: service.start_scan("full")
        )
        self.cancel_scan_button.clicked.connect(service.cancel_scan)
        self.update_button.clicked.connect(service.check_for_updates)
        self.about_button.clicked.connect(self.show_about)
        service.changed.connect(self._refresh)
        self._refresh()

    def _refresh(self) -> None:
        scanning = self.service.scan_running
        if scanning:
            self.status_label.setText(
                f"Protection status: simulated {self.service.scan_kind} scan"
            )
            self.detail_label.setText(
                f"Checking simulated items… {self.service.items_checked:,} checked."
            )
            self.progress_bar.setValue(self.service.progress)
        else:
            self.status_label.setText("Protection status: active (simulation)")
            self.detail_label.setText(self.service.status_message)
            self.progress_bar.setValue(self.service.progress)
        self.last_scan_label.setText(f"Last completed scan: {self.service.last_scan}")
        self.progress_bar.setVisible(scanning or self.service.progress > 0)
        self.quick_scan_button.setEnabled(not scanning)
        self.full_scan_button.setEnabled(not scanning)
        self.cancel_scan_button.setEnabled(scanning)

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "About Windows Defender",
            "Windows Defender is represented here as a local simulation. "
            "It does not provide real antivirus protection or inspect local files.",
        )


def _shield_icon(scanning: bool) -> QIcon:
    pixmap = QPixmap(26, 26)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    shield = QPainterPath()
    shield.moveTo(13, 1.5)
    shield.lineTo(23, 5)
    shield.lineTo(22, 14)
    shield.cubicTo(21, 19, 17, 22.5, 13, 25)
    shield.cubicTo(9, 22.5, 5, 19, 4, 14)
    shield.lineTo(3, 5)
    shield.closeSubpath()
    gradient = QLinearGradient(QPointF(6, 3), QPointF(20, 23))
    if scanning:
        gradient.setColorAt(0, QColor("#f5d04c"))
        gradient.setColorAt(1, QColor("#d48a16"))
    else:
        gradient.setColorAt(0, QColor("#64c2ed"))
        gradient.setColorAt(1, QColor("#17874e"))
    painter.setBrush(gradient)
    painter.setPen(QPen(QColor("#f4f8fb"), 1.2))
    painter.drawPath(shield)

    check = QPainterPath()
    check.moveTo(8, 13)
    check.lineTo(11.5, 16.5)
    check.lineTo(18.5, 9)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor("white"), 2.2, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawPath(check)
    painter.end()
    return QIcon(pixmap)
