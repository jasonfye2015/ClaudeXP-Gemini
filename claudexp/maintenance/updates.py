"""Windows XP Automatic Updates: downloads in the tray, then 'Updates are ready for your computer'."""
import random

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QProgressBar, QPushButton,
                               QVBoxLayout)

from .. import network, sound
from ..paths import DATA
from ..programs.people import load_json, save_json
from . import CoverClock

STATE_FILE = DATA / "updates.json"

# Real updates from late 2001 / early 2002, in roughly the order Windows Update offered them.
CATALOG = [
    ("Critical Update for Windows XP (Q307869)", "Fixes a problem where Windows XP stops responding when you shut down.", True),
    ("Cumulative Patch for Internet Explorer 6 (Q313675)", "Security update for Internet Explorer.", False),
    ("Critical Update for Windows XP (Q309521)", "Universal Plug and Play security fix.", True),
    ("Windows Media Player for Windows XP Update (Q308567)", "Improves playback of DVDs and CDs.", False),
    ("Security Update for Windows XP (Q311967)", "Fixes a vulnerability in Remote Desktop.", True),
    ("Microsoft DirectX 8.1 Runtime", "Better graphics and sound for games.", True),
    ("Critical Update for Windows XP (Q315000)", "Unchecked buffer in Universal Plug and Play.", True),
    ("Windows Messenger 4.6", "The latest version of Windows Messenger.", False),
    ("Microsoft Java Virtual Machine Update (Q300845)", "Security update for the Microsoft VM.", False),
    ("Critical Update for Windows XP (Q312895)", "Fixes a problem with USB devices after standby.", True),
    ("Cumulative Patch for Internet Explorer 6 (Q316059)", "Security update for Internet Explorer.", False),
    ("Windows XP Home Edition Compatibility Update (Q319580)", "Helps older programs run on Windows XP.", True),
]


def shield_pixmap(size=16, progress=None):
    """XP's yellow Automatic Updates shield (with a progress sliver while downloading)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 16
    path = QPainterPath()
    path.moveTo(8 * s, 0.8 * s)
    path.lineTo(14.5 * s, 3 * s)
    path.cubicTo(14.5 * s, 9 * s, 12 * s, 13 * s, 8 * s, 15.3 * s)
    path.cubicTo(4 * s, 13 * s, 1.5 * s, 9 * s, 1.5 * s, 3 * s)
    path.closeSubpath()
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#FFE680"))
    g.setColorAt(1, QColor("#E0A000"))
    p.setPen(QPen(QColor("#8A6000"), 1))
    p.setBrush(g)
    p.drawPath(path)
    p.setPen(QPen(QColor("#1C4FBF"), 1.6 * s))
    p.setBrush(QColor("#5FA0FF"))
    p.drawEllipse(QPointF(8 * s, 7.6 * s), 3.4 * s, 3.4 * s)
    p.drawLine(QPointF(4.6 * s, 7.6 * s), QPointF(11.4 * s, 7.6 * s))
    if progress is not None:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2DBE2D"))
        p.drawRect(QRectF(2 * s, 13.2 * s, 12 * s * progress, 2 * s))
    p.end()
    return pm


class AutoUpdates:
    def __init__(self, desktop):
        self.desktop = desktop
        self.tray = None
        self.clock = None
        self.ready = []           # updates downloaded and waiting to install
        self.dialog = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._download_tick)
        self.installed = set(load_json(STATE_FILE, {}).get("installed", []))

    def busy(self):
        return self.clock is not None or self.dialog is not None

    def _pending(self):
        return [u for u in CATALOG if u[0] not in self.installed and u[0] not in [r[0] for r in self.ready]]

    def _show_tray(self, progress=None):
        from ..tray import TrayIcon
        if self.tray is None:
            self.tray = TrayIcon(self.desktop, QIcon(shield_pixmap(16, progress)))
            self.tray.activated.connect(lambda _r: self.show_dialog())
            self.tray.messageClicked.connect(self.show_dialog)
            self.tray.show()
        else:
            self.tray.setIcon(QIcon(shield_pixmap(16, progress)))

    def _hide_tray(self):
        if self.tray is not None:
            self.tray.hide()
            self.tray.deleteLater()
            self.tray = None

    # ---- downloading in the background --------------------------------------------------
    def start_download(self):
        todo = self._pending()
        if not todo or self.busy():
            return False
        self.ready = todo[:random.randint(2, 4)]
        self.clock = CoverClock(random.uniform(60, 150))
        self._show_tray(0.0)
        self.tray.showMessage("Automatic Updates", "Windows is downloading updates in the background.", None, 5000)
        self.timer.start(1000)
        return True

    def _download_tick(self):
        if self.clock is None:
            return
        if not network.is_connected():
            self.tray.setToolTip("Automatic Updates: Waiting for an Internet connection")
            return
        f = self.clock.fraction()
        self.tray.setIcon(QIcon(shield_pixmap(16, f)))
        self.tray.setToolTip(f"Automatic Updates\nDownloading updates: {int(f * 100)}% complete")
        if f >= 1.0:
            self.timer.stop()
            self.clock = None
            self._show_tray()
            self.tray.setToolTip("Automatic Updates\nUpdates are ready to install")
            self.tray.showMessage("Updates are ready for your computer",
                                  "Click here to install these updates.", None, 15000)

    # ---- installing -----------------------------------------------------------------------
    def show_dialog(self):
        if self.dialog is not None:
            self.desktop.activate(self.dialog)
            return
        if not self.ready:
            if self.clock is not None:
                self.desktop.balloon.dismiss()
            return
        if self.clock is not None:
            return   # still downloading
        from ..network import DialogBody, _fixed_window
        body = DialogBody()
        root = QVBoxLayout(body)
        root.setContentsMargins(14, 12, 14, 12)
        head = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(shield_pixmap(32))
        head.addWidget(icon)
        title = QLabel("<b>Updates are ready to install</b><br>Microsoft recommends that you install these "
                       "updates to keep your computer secure and running smoothly.")
        title.setWordWrap(True)
        head.addWidget(title, 1)
        root.addLayout(head)
        items = QListWidget()
        items.setStyleSheet("QListWidget { background: white; }")
        for name, desc, restart in self.ready:
            item = QListWidgetItem(f"{name}\n    {desc}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            items.addItem(item)
        items.setFixedHeight(150)
        root.addWidget(items)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.hide()
        self.status = QLabel("")
        root.addWidget(self.status)
        root.addWidget(self.progress)
        row = QHBoxLayout()
        row.addStretch()
        self.install_btn = QPushButton("Install")
        self.later_btn = QPushButton("Remind Me Later")
        for b in (self.install_btn, self.later_btn):
            b.setFixedHeight(23)
            row.addWidget(b)
        root.addLayout(row)
        body.setFixedWidth(430)
        self.items = items
        self.install_btn.clicked.connect(self._install)
        self.later_btn.clicked.connect(self._close_dialog)
        self.dialog = _fixed_window(self.desktop, "Automatic Updates", body, self._close_dialog)
        self.dialog.icon = QIcon(shield_pixmap(16))
        self.desktop.open_window(self.dialog)

    def _close_dialog(self):
        if self.dialog is not None:
            win, self.dialog = self.dialog, None
            self.desktop.close_window(win)

    def _install(self):
        chosen = [self.ready[i] for i in range(self.items.count())
                  if self.items.item(i).checkState() == Qt.Checked]
        if not chosen:
            self._close_dialog()
            return
        from ..programs import sysrestore
        sysrestore.create_point("Installed Windows Update", "update")      # XP made one before updating
        self.install_btn.setEnabled(False)
        self.later_btn.setEnabled(False)
        self.items.setEnabled(False)
        self.progress.show()
        clock = CoverClock(random.uniform(20, 45) * len(chosen) / 2)
        timer = QTimer(self.dialog)

        def tick():
            f = clock.fraction()
            self.progress.setValue(int(f * 100))
            current = chosen[min(len(chosen) - 1, int(f * len(chosen)))]
            self.status.setText(f"Installing: {current[0]}")
            if f >= 1.0:
                timer.stop()
                self._installed(chosen)

        timer.timeout.connect(tick)
        timer.start(500)
        tick()

    def _installed(self, chosen):
        self.installed.update(name for name, _d, _r in chosen)
        save_json(STATE_FILE, {"installed": sorted(self.installed)})
        self.ready = [u for u in self.ready if u not in chosen]
        needs_restart = any(r for _n, _d, r in chosen)
        self.progress.hide()
        self.items.hide()
        self.status.setText("Installation complete." + (
            "\n\nYou must restart your computer for the updates to take effect." if needs_restart else ""))
        self.install_btn.setText("Restart Now" if needs_restart else "OK")
        self.later_btn.setText("Restart Later")
        self.later_btn.setVisible(needs_restart)
        for b in (self.install_btn, self.later_btn):
            b.setEnabled(True)
            b.clicked.disconnect()
        self.later_btn.clicked.connect(self._close_dialog)
        if needs_restart:
            self.install_btn.clicked.connect(self._restart)
        else:
            self.install_btn.clicked.connect(self._close_dialog)
        if not self.ready:
            self._hide_tray()
        sound.play("info")

    def _restart(self):
        self._close_dialog()
        self.desktop.restart_requested.emit()
