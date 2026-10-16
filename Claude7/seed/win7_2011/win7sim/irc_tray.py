"""mIRC notification icon with independent sending/receiving lights."""

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen
from PySide6.QtWidgets import QMenu, QToolButton

from .irc_world import IRC_ASSETS


class IRCTrayButton(QToolButton):
    openRequested = Signal()
    connectRequested = Signal()
    disconnectRequested = Signal()
    awayRequested = Signal()
    nicknameRequested = Signal()
    closeRequested = Signal()
    exitRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ircTray")
        self.setFixedSize(32, 30)
        self.setIconSize(QSize(24, 24))
        self._active = False
        self.connected = False
        self.away = False
        self.nick = ""
        self._remaining = {"outgoing": 0, "incoming": 0}
        self._lit = {"outgoing": False, "incoming": False}
        self.timer = QTimer(self)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self._blink)
        self._menu = QMenu(self)
        for attr, title, signal in (
            ("open_action", "Open mIRC", self.openRequested),
            ("connect_action", "Connect to FurNet", self.connectRequested),
            ("disconnect_action", "Disconnect", self.disconnectRequested),
            ("away_action", "Set Away", self.awayRequested),
            ("nickname_action", "Change Nickname…", self.nicknameRequested),
            ("close_action", "Close mIRC", self.closeRequested),
            ("exit_action", "Exit mIRC", self.exitRequested),
        ):
            action = self._menu.addAction(title)
            action.triggered.connect(signal)
            setattr(self, attr, action)
        self.setMenu(self._menu)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.hide()
        self._refresh()

    def activate(self):
        self._active = True
        self.show()

    def deactivate(self):
        self._active = False
        self.timer.stop()
        self._remaining = dict.fromkeys(self._remaining, 0)
        self._lit = dict.fromkeys(self._lit, False)
        self.hide()
        self._refresh()

    def set_state(self, connected, nick, away):
        self.connected, self.nick, self.away = bool(connected), nick, bool(away)
        self._refresh()

    def mark_transfer(self, direction, _size=0, _description=""):
        if not self._active or direction not in self._remaining:
            return
        self._remaining[direction] = 6
        self._lit[direction] = True
        self.timer.start()
        self._refresh()

    def _blink(self):
        for direction in self._remaining:
            self._remaining[direction] = max(0, self._remaining[direction] - 1)
            self._lit[direction] = (
                not self._lit[direction] if self._remaining[direction] else False
            )
        if not any(self._remaining.values()):
            self.timer.stop()
        self._refresh()

    def _refresh(self):
        pixmap = QIcon(str(IRC_ASSETS / "mirc_icon.png")).pixmap(24, 24)
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor("#303030"), 1))
        for x, direction, color in ((1, "outgoing", "#25e855"), (16, "incoming", "#ff3941")):
            painter.setBrush(QColor(color if self._lit[direction] else "#555555"))
            painter.drawEllipse(x, 16, 7, 7)
        painter.end()
        self.setIcon(QIcon(pixmap))
        self.connect_action.setEnabled(not self.connected)
        for action in (self.disconnect_action, self.away_action, self.nickname_action):
            action.setEnabled(self.connected)
        self.away_action.setText("Set Available" if self.away else "Set Away")
        state = ("Away" if self.away else "Connected") if self.connected else "Disconnected"
        tooltip = f"mIRC — FurNet — {self.nick or 'not signed in'} — {state}\nGreen = sending · Red = receiving"
        self.setToolTip(tooltip)
        self.setAccessibleName(tooltip.replace("\n", "; "))
