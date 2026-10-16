"""MSN notification-area control inside the simulated Windows taskbar."""

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen
from PySide6.QtWidgets import QMenu, QToolButton

from .contacts import MSN_ASSETS


class MSNTrayButton(QToolButton):
    activated = Signal(str)
    closeRequested = Signal()
    visibilityChanged = Signal(bool)
    LABELS = {"Online": "Available", "Away": "Away",
              "Do not disturb": "Do not disturb", "Offline": "Offline"}
    COLORS = {"Online": "#48b64b", "Away": "#f2bd32",
              "Do not disturb": "#d64444", "Offline": "#969696"}

    def __init__(self, presence, parent=None):
        super().__init__(parent)
        self.presence = presence
        self._enabled = (
            presence.preferences.data.get("show_tray_icon", True)
            if presence.preferences else True
        )
        self._active = True
        self._unread = {}
        self._names = {}
        self._lit = False
        self.setObjectName("msnTray")
        self.setFixedSize(32, 30)
        self.setIconSize(QSize(24, 24))
        self.flash_timer = QTimer(self)
        self.flash_timer.setInterval(500)
        self.flash_timer.timeout.connect(self._flash)
        self.clicked.connect(
            lambda: self.activated.emit(next(iter(self._unread), ""))
        )
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._status_menu)
        presence.userChanged.connect(self._refresh)
        self._refresh()
        self._apply_visibility()

    @property
    def unread_count(self):
        return sum(self._unread.values())

    @property
    def unread_contacts(self):
        return tuple(self._unread)

    def notify_message(self, contact_id, name):
        self._unread[contact_id] = self._unread.get(contact_id, 0) + 1
        self._names[contact_id] = name
        self._lit = True
        self.flash_timer.start()
        self._refresh()

    def mark_read(self, contact_id):
        self._unread.pop(contact_id, None)
        self._names.pop(contact_id, None)
        if not self._unread:
            self.flash_timer.stop()
            self._lit = False
        self._refresh()

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)
        if self.presence.preferences:
            self.presence.preferences.data["show_tray_icon"] = self._enabled
            self.presence.preferences.save()
        self._apply_visibility()
        self.visibilityChanged.emit(self._enabled)

    def activate(self):
        self._active = True
        self._apply_visibility()

    def deactivate(self):
        self._active = False
        self._apply_visibility()

    def _apply_visibility(self):
        self.setVisible(self._enabled and self._active)

    def _flash(self):
        self._lit = not self._lit
        self._refresh()

    def _refresh(self):
        state = self.presence.user_status
        pixmap = QIcon(str(MSN_ASSETS / "MSN_Icon.ico")).pixmap(24, 24)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("white"), 1))
        painter.setBrush(QColor(self.COLORS[state]))
        painter.drawEllipse(14, 14, 9, 9)
        painter.setPen(QPen(QColor("white"), 1.2))
        if state == "Away":
            painter.drawLine(18, 16, 18, 19)
            painter.drawLine(18, 19, 20, 19)
        elif state == "Offline":
            painter.drawLine(16, 16, 21, 21)
            painter.drawLine(21, 16, 16, 21)
        elif state == "Do not disturb":
            painter.drawLine(16, 18, 21, 18)
        painter.end()
        self.setIcon(QIcon(pixmap))
        text = f"MSN Messenger — {self.LABELS[state]}"
        if self.unread_count:
            text += f"\n{self.unread_count} unread message(s): " + ", ".join(self._names.values())
        self.setToolTip(text)
        self.setAccessibleName(text.replace("\n", "; "))
        self.setStyleSheet(
            "QToolButton { border: 1px solid #ffd45b; border-radius: 3px; "
            "background: rgba(255,190,40,150); }" if self._lit else
            "QToolButton { border: 1px solid transparent; background: transparent; }"
            "QToolButton:hover { background: rgba(255,255,255,70); }"
        )

    def build_status_menu(self):
        menu = QMenu(self)
        for state, label in self.LABELS.items():
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(state == self.presence.user_status)
            action.triggered.connect(
                lambda _checked=False, selected=state: self.presence.set_user_status(
                    selected, self.presence.away_message if selected == "Away" else ""
                )
            )
        menu.addSeparator()
        show_icon = menu.addAction("Show Messenger icon in system tray")
        show_icon.setCheckable(True)
        show_icon.setChecked(self._enabled)
        show_icon.toggled.connect(self.set_enabled)
        close_action = menu.addAction("Close MSN Messenger")
        close_action.triggered.connect(
            lambda _checked=False: self.closeRequested.emit()
        )
        return menu

    def _status_menu(self, point):
        menu = self.build_status_menu()
        menu.exec(self.mapToGlobal(point))
        menu.deleteLater()

    def stop(self):
        self.flash_timer.stop()
        self._lit = False
        self._refresh()
