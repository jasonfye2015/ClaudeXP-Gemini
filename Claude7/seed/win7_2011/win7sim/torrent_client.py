"""Local-only simulation of a period-style desktop torrent client."""

from __future__ import annotations

from dataclasses import dataclass
import random
import time

from PySide6.QtCore import QObject, QPointF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPolygonF, QPixmap
from PySide6.QtWidgets import (
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


@dataclass
class SimulatedTorrent:
    name: str
    size_bytes: int
    progress: float
    seeders: int
    peers: int
    download_kib: float = 0.0
    upload_kib: float = 0.0


_STARTING_TORRENTS = (
    ("Ubuntu-11.04-desktop-amd64.iso", "ISO", 700, 8.4),
    ("OpenOffice.org-3.3.0-Win32.zip", "ZIP", 146, 14.9),
    ("Blender-2.58-win64.zip", "ZIP", 34, 22.1),
    ("FurCon-2011-Photos-Part-01.rar", "RAR", 825, 31.7),
    ("Public-Domain-Jazz-Collection-Vol-03.mp3", "MP3", 211, 42.6),
    ("Web-Design-Magazine-2011-07.pdf", "PDF", 78, 51.8),
    ("Linux-Mint-11-Katya-64bit.iso", "ISO", 900, 61.3),
    ("Indie-Game-Demo-Collection-Summer-2011.zip", "ZIP", 512, 68.5),
    ("Community-Radio-Summer-2011-Archive.mp3", "MP3", 348, 76.4),
    ("Public-Domain-Animation-Shorts-XviD.avi", "AVI", 603, 84.9),
    ("FurCon-2011-Video-Highlights-XviD.avi", "AVI", 1_100, 93.1),
    ("Blender-Open-Projects-2011-05.zip", "ZIP", 428, 97.4),
)


class TorrentClientService(QObject):
    """Fake peer transfers; no torrent files, trackers, peers, or files are used."""

    changed = Signal()
    activityChanged = Signal(bool, bool)
    networkTransferRequested = Signal(str, int, str)

    DOWNLOAD_LIMIT_KIB = 300.0
    UPLOAD_LIMIT_KIB = 44.0
    TICK_INTERVAL_MS = 1000

    def __init__(self, parent=None, *, seed: int | None = None):
        super().__init__(parent)
        self._rng = random.Random(seed if seed is not None else time.time_ns())
        self.torrents = [
            SimulatedTorrent(
                name=name,
                size_bytes=size_mib * 1024 * 1024,
                progress=progress,
                seeders=self._rng.randint(3, 24),
                peers=self._rng.randint(5, 48),
            )
            for name, _file_type, size_mib, progress in _STARTING_TORRENTS
        ]
        self.started = False
        self.paused = False
        self.network_available = True
        self._last_tick = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(self.TICK_INTERVAL_MS)
        self._timer.timeout.connect(self._tick)

    @property
    def downloading_count(self) -> int:
        return sum(torrent.progress < 100 for torrent in self.torrents)

    @property
    def seeding_count(self) -> int:
        return sum(torrent.progress >= 100 for torrent in self.torrents)

    @property
    def status_text(self) -> str:
        if not self.started:
            return "Torrent client is closed."
        if self.paused:
            return "All torrent transfers are paused."
        if not self.network_available:
            return "Waiting for the simulated broadband connection."
        return (
            f"Downloading {self.downloading_count} · "
            f"seeding {self.seeding_count} (simulation)"
        )

    def start(self) -> None:
        if self.started:
            return
        self.started = True
        self.paused = False
        self._last_tick = time.monotonic()
        if self.network_available:
            self._timer.start()
        self._update_speeds(0)
        self.changed.emit()

    def pause_all(self) -> None:
        if not self.started or self.paused:
            return
        self.paused = True
        self._timer.stop()
        self._zero_speeds()
        self.activityChanged.emit(False, False)
        self.changed.emit()

    def resume_all(self) -> None:
        if not self.started or not self.paused:
            return
        self.paused = False
        self._last_tick = time.monotonic()
        if self.network_available:
            self._timer.start()
            self._update_speeds(0)
        else:
            self._zero_speeds()
            self.activityChanged.emit(False, False)
        self.changed.emit()

    def set_network_available(self, available: bool) -> None:
        available = bool(available)
        if self.network_available == available:
            return
        self.network_available = available
        if not available:
            self._timer.stop()
            self._zero_speeds()
            self.activityChanged.emit(False, False)
        elif self.started and not self.paused:
            self._last_tick = time.monotonic()
            self._update_speeds(0)
            self._timer.start()
        self.changed.emit()

    def stop_session(self) -> None:
        """Stop all simulated network activity when the Windows session ends."""
        self._timer.stop()
        self.started = False
        self.paused = False
        self._zero_speeds()
        self.activityChanged.emit(False, False)
        self.changed.emit()

    def _tick(self) -> None:
        now = time.monotonic()
        elapsed = min(5.0, max(0.0, now - self._last_tick))
        self._last_tick = now
        self._update_speeds(elapsed)

    def _update_speeds(self, elapsed: float) -> None:
        if not self.started or self.paused or not self.network_available:
            self._zero_speeds()
            self.activityChanged.emit(False, False)
            self.changed.emit()
            return

        downloading = [torrent for torrent in self.torrents if torrent.progress < 100]
        for torrent in self.torrents:
            torrent.download_kib = 0.0
            torrent.upload_kib = 0.0

        if downloading:
            weights = [self._rng.uniform(0.45, 1.65) for _ in downloading]
            total_weight = sum(weights)
            for torrent, weight in zip(downloading, weights, strict=True):
                torrent.download_kib = self.DOWNLOAD_LIMIT_KIB * weight / total_weight

        upload_weights = [self._rng.uniform(0.45, 1.65) for _ in self.torrents]
        total_upload_weight = sum(upload_weights)
        for torrent, weight in zip(self.torrents, upload_weights, strict=True):
            torrent.upload_kib = self.UPLOAD_LIMIT_KIB * weight / total_upload_weight

        if elapsed > 0:
            for torrent in downloading:
                torrent.progress = min(
                    100.0,
                    torrent.progress
                    + torrent.download_kib * 1024 * elapsed * 100 / torrent.size_bytes,
                )
        total_down = sum(torrent.download_kib for torrent in self.torrents)
        total_up = sum(torrent.upload_kib for torrent in self.torrents)
        down_bytes = int(total_down * 1024 * elapsed)
        up_bytes = int(total_up * 1024 * elapsed)
        if down_bytes:
            self.networkTransferRequested.emit(
                "incoming", down_bytes, "Torrent client — simulated peer data"
            )
        if up_bytes:
            self.networkTransferRequested.emit(
                "outgoing", up_bytes, "Torrent client — simulated peer data"
            )
        self.activityChanged.emit(total_down > 0, total_up > 0)
        self.changed.emit()

    def _zero_speeds(self) -> None:
        for torrent in self.torrents:
            torrent.download_kib = 0.0
            torrent.upload_kib = 0.0


class TorrentClientApp(QWidget):
    closeWindowRequested = Signal()
    exitRequested = Signal()

    def __init__(self, service: TorrentClientService, parent=None):
        super().__init__(parent)
        self.service = service
        self.setObjectName("torrentClient")
        self.setMinimumSize(760, 410)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        title = QLabel("Torrent Client — Transfers")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #285476;")
        layout.addWidget(title)

        self.torrent_table = QTableWidget(0, 8)
        self.torrent_table.setObjectName("torrentList")
        self.torrent_table.setHorizontalHeaderLabels(
            ["Name", "Type", "Size", "Done", "Status", "Seeds", "Down", "Up"]
        )
        self.torrent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.torrent_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.torrent_table.setAlternatingRowColors(True)
        self.torrent_table.horizontalHeader().setStretchLastSection(False)
        self.torrent_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for column in range(1, 8):
            self.torrent_table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        layout.addWidget(self.torrent_table, 1)

        self.status_label = QLabel()
        self.status_label.setObjectName("torrentStatus")
        layout.addWidget(self.status_label)
        note = QLabel(
            "Simulation only: these are fictional or open-source-style 2011 entries. "
            "No torrent protocol, tracker, peer, or local file is contacted or changed."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #526576;")
        layout.addWidget(note)

        controls = QHBoxLayout()
        self.pause_button = QPushButton("Pause all")
        self.resume_button = QPushButton("Resume all")
        self.close_button = QPushButton("Close to tray")
        self.exit_button = QPushButton("Exit client")
        controls.addWidget(self.pause_button)
        controls.addWidget(self.resume_button)
        controls.addStretch(1)
        controls.addWidget(self.close_button)
        controls.addWidget(self.exit_button)
        layout.addLayout(controls)

        self.pause_button.clicked.connect(lambda: service.pause_all())
        self.resume_button.clicked.connect(lambda: service.resume_all())
        self.close_button.clicked.connect(lambda: self.closeWindowRequested.emit())
        self.exit_button.clicked.connect(lambda: self.exitRequested.emit())
        service.changed.connect(self._refresh)
        self._refresh()

    def _refresh(self) -> None:
        service = self.service
        self.status_label.setText(service.status_text)
        self.pause_button.setEnabled(service.started and not service.paused)
        self.resume_button.setEnabled(service.started and service.paused)
        self.torrent_table.setRowCount(len(service.torrents))
        for row, torrent in enumerate(service.torrents):
            file_type = torrent.name.rsplit(".", 1)[-1].upper()
            if service.paused:
                state = "Paused"
            elif not service.network_available:
                state = "Waiting for connection"
            elif torrent.progress >= 100:
                state = "Seeding"
            else:
                state = "Downloading"
            values = (
                torrent.name,
                file_type,
                _format_size(torrent.size_bytes),
                f"{torrent.progress:.1f}%",
                state,
                f"{torrent.seeders} / {torrent.peers}",
                f"{torrent.download_kib:.1f} KiB/s",
                f"{torrent.upload_kib:.1f} KiB/s",
            )
            for column, value in enumerate(values):
                cell = self.torrent_table.item(row, column)
                if cell is None:
                    cell = QTableWidgetItem()
                    self.torrent_table.setItem(row, column, cell)
                if cell.text() != value:
                    cell.setText(value)


class TorrentTrayButton(QToolButton):
    """Taskbar button with separate blinking download and upload indicators."""

    openRequested = Signal()
    pauseAllRequested = Signal()
    resumeAllRequested = Signal()
    closeWindowRequested = Signal()
    exitRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("torrentClientTray")
        self.setAccessibleName("Torrent Client activity and menu")
        self.setFixedSize(32, 30)
        self.setIconSize(QSize(26, 26))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._active = False
        self._window_open = False
        self._down_active = False
        self._up_active = False
        self._blink_on = True
        self._service: TorrentClientService | None = None

        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(180)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._menu = QMenu(self)
        self.open_action = self._menu.addAction("Open Torrent Client")
        self.pause_action = self._menu.addAction("Pause all transfers")
        self.resume_action = self._menu.addAction("Resume all transfers")
        self._menu.addSeparator()
        self.close_window_action = self._menu.addAction("Close window to tray")
        self.exit_action = self._menu.addAction("Exit Torrent Client")
        self.open_action.triggered.connect(lambda: self.openRequested.emit())
        self.pause_action.triggered.connect(lambda: self.pauseAllRequested.emit())
        self.resume_action.triggered.connect(lambda: self.resumeAllRequested.emit())
        self.close_window_action.triggered.connect(
            lambda: self.closeWindowRequested.emit()
        )
        self.exit_action.triggered.connect(lambda: self.exitRequested.emit())
        self.setMenu(self._menu)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._refresh()
        self.hide()

    def bind_service(self, service: TorrentClientService) -> None:
        self._service = service
        service.changed.connect(self._refresh)
        service.activityChanged.connect(self.set_activity)
        self._refresh()

    def activate(self) -> None:
        self._active = True
        self.show()
        self._refresh()

    def deactivate(self) -> None:
        self._active = False
        self._down_active = False
        self._up_active = False
        self._blink_timer.stop()
        self.hide()
        self._refresh()

    def set_window_open(self, is_open: bool) -> None:
        self._window_open = bool(is_open)
        self._refresh()

    def set_activity(self, downloading: bool, uploading: bool) -> None:
        self._down_active = bool(downloading)
        self._up_active = bool(uploading)
        if self._active and (self._down_active or self._up_active):
            self._blink_on = True
            self._blink_timer.start()
        else:
            self._blink_timer.stop()
            self._blink_on = False
        self._refresh()

    def _toggle_blink(self) -> None:
        self._blink_on = not self._blink_on
        self._refresh()

    def _refresh(self) -> None:
        if self._service is None:
            down = up = False
            tooltip = "Torrent Client"
        else:
            down = self._down_active
            up = self._up_active
            tooltip = self._service.status_text
        if self._active and (down or up) and self._blink_on:
            tooltip += "\nRed: downloading    Green: uploading"
        self.setIcon(_torrent_icon(
            down and self._blink_on,
            up and self._blink_on,
        ))
        self.setToolTip(tooltip)
        self.pause_action.setEnabled(
            bool(self._service and self._service.started and not self._service.paused)
        )
        self.resume_action.setEnabled(
            bool(self._service and self._service.started and self._service.paused)
        )
        self.close_window_action.setEnabled(self._window_open)
        self.exit_action.setEnabled(self._active)


def _format_size(byte_count: int) -> str:
    size_mib = byte_count / (1024 * 1024)
    if size_mib >= 1024:
        return f"{size_mib / 1024:.2f} GiB"
    return f"{size_mib:.0f} MiB"


def _torrent_icon(download_on: bool, upload_on: bool) -> QIcon:
    pixmap = QPixmap(26, 26)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("#40596c"), 1.2))
    painter.setBrush(QColor("#dceaf4"))
    painter.drawRoundedRect(2, 1, 22, 22, 4, 4)

    painter.setPen(QPen(QColor("#2872a2"), 2.3, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawLine(9, 4, 9, 13)
    painter.drawPolyline(QPolygonF([QPointF(6, 10), QPointF(9, 13), QPointF(12, 10)]))
    painter.drawLine(17, 13, 17, 4)
    painter.drawPolyline(QPolygonF([QPointF(14, 7), QPointF(17, 4), QPointF(20, 7)]))

    painter.setPen(QPen(QColor("#263947"), 0.8))
    painter.setBrush(QColor("#f04444") if download_on else QColor("#734747"))
    painter.drawEllipse(3, 18, 7, 7)
    painter.setBrush(QColor("#39d178") if upload_on else QColor("#466f57"))
    painter.drawEllipse(16, 18, 7, 7)
    painter.end()
    return QIcon(pixmap)
