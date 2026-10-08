"""The MUSHclient-style window: black output screen, command line, toolbar and status bar."""
import random

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QMenuBar, QStyle, QTextBrowser, QToolBar,
                               QVBoxLayout, QWidget)

from ... import clock, network, sound
from .brain import WORLD_NAME

HOST, PORT = "muck.pawprints.net", 8888

COLORS = {
    "room": ("#FFFFFF", True), "desc": ("#C0C0C0", False), "contents": ("#FFFF55", False),
    "exits": ("#55FFFF", False), "say": ("#FFFFFF", False), "pose": ("#55FFFF", False),
    "page": ("#FF55FF", False), "arrive": ("#55FF55", False), "system": ("#C0C0C0", False),
    "who": ("#C0C0C0", False), "banner": ("#FFFF55", False), "error": ("#FF5555", False),
    "echo": ("#808000", False), "note": ("#00C0FF", False),
}

MENU_STYLE = """
QMenuBar { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
QMenuBar::item { padding: 3px 7px; background: transparent; }
QMenuBar::item:selected { background: #316AC5; color: white; }
QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }
QMenu::item { padding: 4px 24px 4px 20px; }
QMenu::item:selected { background: #316AC5; color: white; }
QToolBar { background: #ECE9D8; border: none; border-bottom: 1px solid #ACA899; spacing: 2px; padding: 2px; }
QLabel#status { background: #ECE9D8; border-top: 1px solid #ACA899; padding: 2px 6px; font-family: Tahoma; font-size: 11px; }
"""


def _mono(size=9):
    font = QFont("Lucida Console", size)
    font.setStyleHint(QFont.Monospace)
    return font


class CommandLine(QLineEdit):
    """MUSHclient's input box, with up/down command history."""

    def __init__(self, on_send):
        super().__init__()
        self.on_send = on_send
        self.history = []
        self.pos = 0
        self.returnPressed.connect(self._send)

    def _send(self):
        text = self.text()
        if text.strip() and (not self.history or self.history[-1] != text):
            self.history.append(text)
            del self.history[:-100]
        self.pos = len(self.history)
        self.clear()
        self.on_send(text)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up and self.history:
            self.pos = max(0, self.pos - 1)
            self.setText(self.history[self.pos])
        elif event.key() == Qt.Key_Down and self.history:
            self.pos = min(len(self.history), self.pos + 1)
            self.setText(self.history[self.pos] if self.pos < len(self.history) else "")
        else:
            super().keyPressEvent(event)


class MuckClient(QWidget):
    def __init__(self, desktop, world):
        super().__init__()
        self.desktop = desktop
        self.world = world
        self.frame = None            # the XPWindow, set by the launcher
        self.connected = False
        self.connecting = False
        self.connected_at = None
        self.setStyleSheet(MENU_STYLE)
        world.line.connect(self.show_line)
        world.closed.connect(lambda: self._closed("Connection closed by the world."))

        bar = QMenuBar()
        file_menu = bar.addMenu("&File")
        file_menu.addAction("&Connect", self.connect_world)
        file_menu.addAction("&Disconnect", self.disconnect_world)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", lambda: self.frame.request_close() if self.frame else self.close())
        edit_menu = bar.addMenu("&Edit")
        edit_menu.addAction("&Copy", lambda: self.output.copy())
        edit_menu.addAction("Select &All", lambda: self.output.selectAll())
        edit_menu.addAction("C&lear Output", lambda: self.output.clear())
        game_menu = bar.addMenu("&Game")
        for label, cmd in (("&Look", "look"), ("&WHO", "WHO"), ("&Home", "home"), ("&Help", "help")):
            game_menu.addAction(label, lambda c=cmd: self.send(c))
        help_menu = bar.addMenu("&Help")
        help_menu.addAction("&About ClaudeMUCK", self._about)
        bar.triggered.connect(lambda _a: sound.play("menu"))

        tools = QToolBar()
        tools.setIconSize(tools.iconSize().scaled(16, 16, Qt.KeepAspectRatio))
        style = self.style()
        for icon, tip, slot in (
            (network.network_icon(), "Connect", self.connect_world),
            (style.standardIcon(QStyle.SP_BrowserStop), "Disconnect", self.disconnect_world),
            (None, None, None),
            (style.standardIcon(QStyle.SP_FileDialogContentsView), "Look", lambda: self.send("look")),
            (style.standardIcon(QStyle.SP_FileDialogDetailedView), "WHO", lambda: self.send("WHO")),
            (style.standardIcon(QStyle.SP_DirHomeIcon), "Home", lambda: self.send("home")),
            (None, None, None),
            (style.standardIcon(QStyle.SP_DialogResetButton), "Clear output", lambda: self.output.clear()),
            (style.standardIcon(QStyle.SP_MessageBoxQuestion), "Help", lambda: self.send("help")),
        ):
            if icon is None:
                tools.addSeparator()
                continue
            action = QAction(icon, tip, self)
            action.triggered.connect(slot)
            tools.addAction(action)

        self.output = QTextBrowser()
        self.output.setFont(_mono())
        self.output.setStyleSheet("QTextBrowser { background: black; color: #C0C0C0; border: none; }")
        self.output.document().setMaximumBlockCount(5000)
        self.output.setFocusPolicy(Qt.ClickFocus)

        self.input = CommandLine(self.send)
        self.input.setFont(_mono())
        self.input.setStyleSheet("QLineEdit { background: white; color: black; border: 1px solid #7F9DB9; padding: 2px; }")

        self.status = QLabel()
        self.status.setObjectName("status")
        self.clock_label = QLabel()
        self.clock_label.setObjectName("status")
        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(0)
        status_row.addWidget(self.status, 1)
        status_row.addWidget(self.clock_label)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setMenuBar(bar)
        root.addWidget(tools)
        root.addWidget(self.output, 1)
        root.addWidget(self.input)
        root.addLayout(status_row)

        self.ticker = QTimer(self)
        self.ticker.timeout.connect(self._update_status)
        self.ticker.start(1000)
        self._update_status()

    # ---- output -----------------------------------------------------------------
    def show_line(self, kind, text):
        color, bold = COLORS.get(kind, COLORS["system"])
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        fmt.setFontWeight(QFont.Bold if bold else QFont.Normal)
        bar = self.output.verticalScrollBar()
        at_bottom = bar.value() >= bar.maximum() - 4
        cursor = QTextCursor(self.output.document())
        cursor.movePosition(QTextCursor.End)
        if not self.output.document().isEmpty():
            cursor.insertBlock()
        cursor.insertText(text, fmt)
        if at_bottom:
            bar.setValue(bar.maximum())
        if kind in ("say", "pose", "page", "arrive") and self.frame is not None:
            if not self.desktop.is_active(self.frame):
                self.frame.flash()

    def note(self, text):
        self.show_line("note", text)

    # ---- connection -----------------------------------------------------------------
    def start(self):
        self.note(f"Welcome to ClaudeMUCK, the friendly MUCK client!")
        self.connect_world()

    def connect_world(self):
        if self.connected or self.connecting:
            return
        self.connecting = True
        self.note(f"Connecting to {WORLD_NAME} ({HOST}, port {PORT})...")
        if not network.is_connected():
            self.note("Waiting for your Internet connection...")
        network.connect(self.desktop, then=self._online)
        QTimer.singleShot(200, self._check_dial_cancelled)

    def _check_dial_cancelled(self):
        net = network.get(self.desktop)
        if self.connecting and not net.connected and net.connect_win is None and net.progress_win is None:
            self.connecting = False
            self.note(f'Unable to connect to "{HOST}": no Internet connection.')
            self._update_status()
        elif self.connecting and not net.connected:
            QTimer.singleShot(500, self._check_dial_cancelled)

    def _online(self):
        QTimer.singleShot(random.randint(800, 2000), self._socket_open)

    def _socket_open(self):
        if not self.connecting:
            return
        self.connecting = False
        self.connected = True
        self.connected_at = clock.now()
        self.note(f"--- Connected on {self.connected_at:%A, %B} {self.connected_at.day}, "
                  f"{self.connected_at.year}, {clock.time_text(self.connected_at)} ---")
        self.world.connect_session()
        self._update_status()
        self.input.setFocus()

    def disconnect_world(self):
        if self.connecting:
            self.connecting = False
            self.note("Connection attempt cancelled.")
        if self.connected:
            self.world.disconnect_session()
            self._closed()

    def _closed(self, why=""):
        if not self.connected:
            return
        self.connected = False
        if why:
            self.note(why)
        now = clock.now()
        self.note(f"--- Disconnected on {now:%A, %B} {now.day}, {now.year}, {clock.time_text(now)} ---")
        self._update_status()

    def network_lost(self):
        if self.connected:
            self.world.disconnect_session()
            self._closed("Connection lost: your modem hung up.")
        elif self.connecting:
            self.connecting = False

    def send(self, text):
        if not self.connected:
            if text.strip():
                self.note("You are not connected to the world. (File > Connect)")
            return
        shown = text
        parts = text.split()
        if len(parts) >= 3 and parts[0].lower() in ("connect", "co", "create"):
            shown = f"{parts[0]} {parts[1]} " + "*" * len(parts[2])
        self.show_line("echo", shown)
        self.world.command(text)

    def _update_status(self):
        if self.connected:
            self.status.setText(f"Connected to {WORLD_NAME}  ({HOST} {PORT})")
            secs = int((clock.now() - self.connected_at).total_seconds())
            self.clock_label.setText(f"{secs // 3600}:{secs // 60 % 60:02d}:{secs % 60:02d}")
        elif self.connecting:
            self.status.setText("Connecting...")
            self.clock_label.setText("")
        else:
            self.status.setText("Closed")
            self.clock_label.setText("")

    def _about(self):
        self.note("ClaudeMUCK 3.17 - a MUCK client for ClaudeXP. Type 'help' once connected.")

    def shutdown(self):
        self.ticker.stop()
        if self.connected:
            self.world.disconnect_session()
        self.connected = self.connecting = False

    def closeEvent(self, event):
        self.shutdown()
        event.accept()
