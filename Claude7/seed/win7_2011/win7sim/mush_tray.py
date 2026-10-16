"""PawPrints MUCK notification-area icon and menu."""

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen
from PySide6.QtWidgets import QMenu, QToolButton

from .mush_world import MUSH_ASSETS


class MushTrayButton(QToolButton):
    openRequested = Signal()
    connectRequested = Signal()
    disconnectRequested = Signal()
    closeRequested = Signal()
    exitRequested = Signal()
    aboutRequested = Signal()
    visibilityChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mushTray")
        self.setAccessibleName("PawPrints MUCK tray menu")
        self.setFixedSize(32, 30)
        self.setIconSize(QSize(24, 24))
        self._active = False
        self._connected = False
        self._lit = False

        self._flash_timer = QTimer(self)
        self._flash_timer.setInterval(400)
        self._flash_timer.timeout.connect(self._toggle_led)
        self._quiet_timer = QTimer(self)
        self._quiet_timer.setSingleShot(True)
        self._quiet_timer.setInterval(1800)
        self._quiet_timer.timeout.connect(self._stop_activity)

        self._menu = QMenu(self)
        self.open_action = self._menu.addAction("Open MushClient")
        self.open_action.triggered.connect(self.openRequested)
        self.connect_action = self._menu.addAction("Connect to PawPrints MUCK")
        self.connect_action.triggered.connect(self.connectRequested)
        self.disconnect_action = self._menu.addAction("Disconnect from PawPrints MUCK")
        self.disconnect_action.triggered.connect(self.disconnectRequested)
        self._menu.addSeparator()
        self.close_action = self._menu.addAction("Close MushClient")
        self.close_action.triggered.connect(self.closeRequested)
        self.about_action = self._menu.addAction("About MushClient…")
        self.about_action.triggered.connect(self.aboutRequested)
        self._menu.addSeparator()
        self.exit_action = self._menu.addAction("Exit MushClient")
        self.exit_action.triggered.connect(self.exitRequested)
        self.setMenu(self._menu)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._refresh()
        self._apply_visibility()

    @property
    def connected(self):
        return self._connected

    def set_connected(self, connected):
        self._connected = bool(connected)
        self.connect_action.setEnabled(not self._connected)
        self.disconnect_action.setEnabled(self._connected)
        self._refresh()

    def activate(self):
        self._active = True
        self._apply_visibility()

    def deactivate(self):
        self._active = False
        self._stop_activity()
        self._apply_visibility()

    def _apply_visibility(self):
        self.setVisible(self._active)
        self.visibilityChanged.emit(self._active)

    def mark_activity(self):
        if not self._active:
            return
        self._lit = True
        if not self._flash_timer.isActive():
            self._flash_timer.start()
        self._quiet_timer.start()
        self._refresh()

    def _toggle_led(self):
        self._lit = not self._lit
        self._refresh()

    def _stop_activity(self):
        self._flash_timer.stop()
        self._lit = False
        self._refresh()

    def _refresh(self):
        pixmap = QIcon(str(MUSH_ASSETS / "mush_icon.png")).pixmap(24, 24)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#363022"), 1))
        painter.setBrush(QColor("#ffd429") if self._lit else QColor("#76692f"))
        painter.drawEllipse(16, 16, 7, 7)
        if self._lit:
            painter.setPen(QPen(QColor("#fff6b0"), 1))
            painter.drawPoint(18, 18)
        painter.end()
        self.setIcon(QIcon(pixmap))
        state = "Connected to PawPrints MUCK" if self._connected else "Disconnected"
        tip = f"MushClient — {state} (simulated local world)"
        if self._lit:
            tip += "\nRecent activity"
        self.setToolTip(tip)
        self.setAccessibleName(tip.replace("\n", "; "))
