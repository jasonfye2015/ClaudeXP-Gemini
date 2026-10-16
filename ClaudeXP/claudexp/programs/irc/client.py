"""The mIRC-style window: toolbar, switchbar, and Status / channel / private-message panes."""
import random

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap, QPolygonF, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (QCheckBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMenuBar,
                               QPushButton, QSplitter, QStackedWidget, QStyle, QTabBar, QTextBrowser, QToolBar,
                               QVBoxLayout, QWidget)

from ... import clock, network, sound
from ...user import user_name
from ..muck.client import CommandLine
from ..people import load_json, save_json
from .furnet import DATA_DIR

SETTINGS_FILE = DATA_DIR / "settings.json"

# mIRC's default colour scheme.
COLORS = {
    "own": ("#000000", False), "msg": ("#000000", False), "highlight": ("#000000", True),
    "action": ("#9C009C", False), "join": ("#009300", False), "part": ("#009300", False),
    "kick": ("#009300", False), "mode": ("#009300", False), "topic": ("#009300", False),
    "nick": ("#009300", False), "quit": ("#00007F", False), "notice": ("#7F0000", False),
    "ctcp": ("#FF0000", False), "info": ("#00007F", False), "server": ("#000000", False),
    "whois": ("#000000", False),
}
TAB_MESSAGE = QColor("#FF0000")     # switchbar button colours for unseen activity
TAB_EVENT = QColor("#00007F")

STYLE = """
QMenuBar { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
QMenuBar::item { padding: 3px 7px; background: transparent; }
QMenuBar::item:selected { background: #316AC5; color: white; }
QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }
QMenu::item { padding: 4px 24px 4px 20px; }
QMenu::item:selected { background: #316AC5; color: white; }
QToolBar { background: #ECE9D8; border: none; border-bottom: 1px solid #ACA899; spacing: 2px; padding: 2px; }
QTabBar { background: #ECE9D8; }
QTabBar::tab { background: #ECE9D8; border: 1px solid #ACA899; padding: 2px 10px; margin: 2px 1px;
               font-family: Tahoma; font-size: 11px; min-width: 40px; }
QTabBar::tab:selected { background: white; border: 1px solid #7F9DB9; }
QWidget#switchbar { background: #ECE9D8; border-bottom: 1px solid #ACA899; }
"""


def _mono():
    font = QFont("Lucida Console", 9)
    font.setStyleHint(QFont.Monospace)
    return font


def lightning_icon():
    """mIRC's yellow 'connect' lightning bolt."""
    pm = QPixmap(16, 16)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QColor("#7F5F00"))
    p.setBrush(QColor("#FFD800"))
    p.drawPolygon(QPolygonF([QPointF(9, 0.5), QPointF(3, 9), QPointF(7, 9), QPointF(5, 15.5),
                             QPointF(13, 6), QPointF(8.5, 6), QPointF(11, 0.5)]))
    p.end()
    return QIcon(pm)


class Pane(QWidget):
    """One mIRC window: Status, a #channel (with a nick list), or a private query."""

    def __init__(self, client, target):
        super().__init__()
        self.client = client
        self.target = target          # "" = Status
        self.is_channel = target.startswith("#")
        self.output = QTextBrowser()
        self.output.setFont(_mono())
        self.output.setStyleSheet("QTextBrowser { background: white; color: black; border: 1px solid #7F9DB9; }")
        self.output.document().setMaximumBlockCount(3000)
        self.output.setFocusPolicy(Qt.ClickFocus)
        self.input = CommandLine(lambda text: client.typed(self.target, text))
        self.input.setFont(_mono())
        self.input.setStyleSheet("QLineEdit { background: white; color: black; border: 1px solid #7F9DB9; padding: 1px; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        if self.is_channel:
            self.nicks = QListWidget()
            self.nicks.setFont(_mono())
            self.nicks.setStyleSheet("QListWidget { background: white; border: 1px solid #7F9DB9; }")
            self.nicks.itemDoubleClicked.connect(lambda item: client.open_query(item.text().lstrip("@+")))
            split = QSplitter(Qt.Horizontal)
            split.addWidget(self.output)
            split.addWidget(self.nicks)
            split.setStretchFactor(0, 1)
            split.setSizes([520, 130])
            layout.addWidget(split, 1)
        else:
            self.nicks = None
            layout.addWidget(self.output, 1)
        layout.addWidget(self.input)

    def add(self, kind, text):
        color, bold = COLORS.get(kind, COLORS["msg"])
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        fmt.setFontWeight(QFont.Bold if bold else QFont.Normal)
        bar = self.output.verticalScrollBar()
        at_bottom = bar.value() >= bar.maximum() - 4
        cursor = QTextCursor(self.output.document())
        cursor.movePosition(QTextCursor.End)
        if not self.output.document().isEmpty():
            cursor.insertBlock()
        cursor.insertText(f"[{clock.now():%H:%M}] {text}", fmt)
        if at_bottom:
            bar.setValue(bar.maximum())

    def set_names(self, entries):
        if self.nicks is not None:
            self.nicks.clear()
            self.nicks.addItems(entries)


class IrcClient(QWidget):
    def __init__(self, desktop, net):
        super().__init__()
        self.desktop = desktop
        self.net = net
        self.frame = None
        self.connecting = False
        self.options_win = None
        self.settings = load_json(SETTINGS_FILE, None)
        self.panes = {}
        self.setStyleSheet(STYLE)

        net.line.connect(self._line)
        net.joined.connect(self._joined)
        net.parted.connect(self._parted)
        net.names.connect(self._names)
        net.topic.connect(lambda _c: self._update_title())
        net.query_opened.connect(lambda nick: self.pane(nick))
        net.nick_changed.connect(lambda _n: self._update_title())
        net.closed.connect(self._closed)

        bar = QMenuBar()
        file_menu = bar.addMenu("&File")
        file_menu.addAction("&Connect", self.connect_server)
        file_menu.addAction("&Disconnect", lambda: self.typed("", "/quit Leaving"))
        file_menu.addSeparator()
        file_menu.addAction("&Options...", lambda: self.show_options())
        file_menu.addSeparator()
        file_menu.addAction("E&xit", lambda: self.frame.request_close() if self.frame else self.close())
        tools = bar.addMenu("&Tools")
        tools.addAction("&Channels List", lambda: self.typed("", "/list"))
        commands = bar.addMenu("&Commands")
        commands.addAction("&Join channel...", lambda: self._prefill("/join #"))
        commands.addAction("&Whois...", lambda: self._prefill("/whois "))
        commands.addAction("Set &Away...", lambda: self._prefill("/away "))
        commands.addAction("&Back", lambda: self.typed(self.current_target(), "/away"))
        window_menu = bar.addMenu("&Window")
        window_menu.addAction("&Status", lambda: self.show_pane(""))
        help_menu = bar.addMenu("&Help")
        help_menu.addAction("&Commands", lambda: self.typed(self.current_target(), "/help"))
        help_menu.addAction("&About ClaudeIRC", self._about)
        bar.triggered.connect(lambda _a: sound.play("menu"))

        toolbar = QToolBar()
        style = self.style()
        for icon, tip, slot in (
            (lightning_icon(), "Connect", self.connect_server),
            (style.standardIcon(QStyle.SP_BrowserStop), "Disconnect", lambda: self.typed("", "/quit Leaving")),
            (None, None, None),
            (style.standardIcon(QStyle.SP_FileDialogDetailedView), "Options", lambda: self.show_options()),
            (style.standardIcon(QStyle.SP_DirIcon), "Channels List", lambda: self.typed("", "/list")),
            (None, None, None),
            (style.standardIcon(QStyle.SP_MessageBoxQuestion), "Help", lambda: self.typed(self.current_target(), "/help")),
        ):
            if icon is None:
                toolbar.addSeparator()
                continue
            action = QAction(icon, tip, self)
            action.triggered.connect(slot)
            toolbar.addAction(action)

        self.switchbar = QTabBar()
        self.switchbar.setExpanding(False)
        self.switchbar.setDrawBase(False)
        self.switchbar.setTabsClosable(True)
        self.switchbar.currentChanged.connect(self._tab_changed)
        self.switchbar.tabCloseRequested.connect(self._tab_close)
        switch_row = QWidget()
        switch_row.setObjectName("switchbar")
        switch_row.setAttribute(Qt.WA_StyledBackground, True)
        row = QHBoxLayout(switch_row)
        row.setContentsMargins(2, 0, 2, 0)
        row.addWidget(self.switchbar)
        row.addStretch()

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background: #ECE9D8; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setMenuBar(bar)
        root.addWidget(toolbar)
        root.addWidget(switch_row)
        root.addWidget(self.stack, 1)

        self.pane("")
        self.switchbar.setTabButton(0, QTabBar.RightSide, None)

    # ---- windows ------------------------------------------------------------------
    def pane(self, target):
        key = target.lower()
        if key not in self.panes:
            pane = Pane(self, target)
            self.panes[key] = pane
            self.stack.addWidget(pane)
            label = "Status" if not target else target
            index = self.switchbar.addTab(label)
            self.switchbar.setTabData(index, key)
            if not target.startswith("#") and target:
                self.switchbar.setTabIcon(index, QIcon())
        return self.panes[key]

    def _tab_index(self, key):
        for i in range(self.switchbar.count()):
            if self.switchbar.tabData(i) == key:
                return i
        return -1

    def show_pane(self, target):
        index = self._tab_index(target.lower())
        if index >= 0:
            self.switchbar.setCurrentIndex(index)

    def current_target(self):
        index = self.switchbar.currentIndex()
        key = self.switchbar.tabData(index) if index >= 0 else ""
        pane = self.panes.get(key)
        return pane.target if pane else ""

    def _tab_changed(self, index):
        if index < 0:
            return
        key = self.switchbar.tabData(index)
        pane = self.panes.get(key)
        if pane is None:
            return
        self.stack.setCurrentWidget(pane)
        self.switchbar.setTabTextColor(index, QColor("black"))
        self.net.active_window = pane.target
        pane.input.setFocus()
        self._update_title()

    def _tab_close(self, index):
        key = self.switchbar.tabData(index)
        pane = self.panes.get(key)
        if pane is None or not pane.target:
            return
        if pane.is_channel and self.net.in_channel(pane.target):
            self.net.part(pane.target)
        else:
            self._remove_pane(key)

    def _remove_pane(self, key):
        pane = self.panes.pop(key, None)
        if pane is None:
            return
        index = self._tab_index(key)
        if index >= 0:
            self.switchbar.removeTab(index)
        self.stack.removeWidget(pane)
        pane.deleteLater()

    def _prefill(self, text):
        pane = self.panes.get(self.current_target().lower()) or self.panes[""]
        pane.input.setText(text)
        pane.input.setFocus()

    # ---- network events ------------------------------------------------------------------
    def _line(self, window, kind, text):
        pane = self.pane(window) if (not window or not window.startswith("#") or window.lower() in self.panes) \
            else self.panes[""]
        pane.add(kind, text)
        index = self._tab_index(pane.target.lower())
        current = self.switchbar.currentIndex()
        if index != current and index >= 0 and kind not in ("own", "server"):
            important = kind in ("msg", "action", "highlight", "notice") or not pane.is_channel
            colour = TAB_MESSAGE if important else TAB_EVENT
            if not (self.switchbar.tabTextColor(index) == TAB_MESSAGE and colour == TAB_EVENT):
                self.switchbar.setTabTextColor(index, colour)
        if kind == "highlight" or (pane.target and not pane.is_channel and kind in ("msg", "action")):
            if self.frame is not None and not self.desktop.is_active(self.frame):
                self.frame.flash()

    def _joined(self, name):
        self.pane(name)
        self.show_pane(name)
        self._names(name)

    def _parted(self, name):
        self._remove_pane(name.lower())
        self._remember_channels()

    def _names(self, name):
        pane = self.panes.get(name.lower())
        if pane is not None:
            pane.set_names(self.net.nicklist(name))
            if pane.target.lower() == self.current_target().lower():
                self._update_title()

    def _closed(self, reason):
        self._remember_channels(self.net.last_channels)
        for pane in self.panes.values():
            pane.add("info", "* Disconnected")
            pane.set_names([])
        self._update_title()

    def _remember_channels(self, channels=None):
        if self.settings is not None:
            self.settings["autojoin"] = list(channels if channels is not None else self.net.my_channels)
            save_json(SETTINGS_FILE, self.settings)

    def _update_title(self):
        if self.frame is None:
            return
        target = self.current_target()
        net = self.net
        if not target:
            caption = (f"Status: {net.nick} [+i] on {net.server} ({net.port})" if net.connected
                       else "Status: (not connected)")
        elif target.startswith("#"):
            chan = net.channel(target)
            count = len(net.member_nicks(target)) if net.in_channel(target) else 0
            caption = f"{target} [{count}] [{chan.modes if chan else '+nt'}]: {chan.topic if chan else ''}"
        else:
            p = net.person(target)
            caption = f"{target} ({p.host})" if p else target
        self.frame.set_title(f"ClaudeIRC - [{caption}]")

    # ---- typing ----------------------------------------------------------------------------
    def typed(self, target, text):
        if not text.strip():
            return
        if text.strip().lower() in ("/clear", "/cls"):
            pane = self.panes.get(target.lower())
            if pane:
                pane.output.clear()
            return
        if text.strip().lower().startswith(("/server", "/connect")):
            self.connect_server()
            return
        if not self.net.connected:
            (self.panes.get(target.lower()) or self.panes[""]).add("info", "* Not connected to server")
            return
        self.net.input(target, text)

    def open_query(self, nick):
        self.pane(nick)
        self.show_pane(nick)

    # ---- connecting ----------------------------------------------------------------------------
    def _apply_identity(self):
        """One online identity: the nickname follows the shared handle (no Options dialog needed)."""
        from ... import user
        if not user.linked():
            return
        from ... import fursonas
        s = dict(self.settings or {"realname": fursonas.irc_realname() or user.user_name(),
                                   "email": user.email_address(), "autojoin": []})
        s["nick"] = user.irc_nick()
        s["alt"] = user.irc_nick() + "_"
        if s != self.settings:
            self.settings = s
            save_json(SETTINGS_FILE, s)

    def start(self):
        status = self.panes[""]
        status.add("info", "* ClaudeIRC v6.02 - an IRC client for ClaudeXP")
        status.add("info", "* Type /help for a list of commands")
        self._apply_identity()
        if self.settings is None:
            self.show_options(connect_after=True)
        else:
            self.connect_server()

    def connect_server(self):
        if self.net.connected or self.connecting:
            return
        self._apply_identity()
        if self.settings is None:
            self.show_options(connect_after=True)
            return
        self.connecting = True
        self.show_pane("")
        self.panes[""].add("info", f"* Connecting to {self.net.server} ({self.net.port})")
        network.connect(self.desktop, then=self._online)
        QTimer.singleShot(200, self._check_dial_cancelled)

    def _check_dial_cancelled(self):
        dialer = network.get(self.desktop)
        if self.connecting and not dialer.connected and dialer.connect_win is None and dialer.progress_win is None:
            self.connecting = False
            self.panes[""].add("info", f"* Unable to connect to {self.net.server}: no Internet connection")
        elif self.connecting and not dialer.connected:
            QTimer.singleShot(500, self._check_dial_cancelled)

    def _online(self):
        QTimer.singleShot(random.randint(1000, 2500), self._register)

    def _register(self):
        if not self.connecting:
            return
        self.connecting = False
        s = self.settings
        self.net.connect_session(s["nick"], s.get("alt") or s["nick"] + "_", s.get("realname", ""))
        self._update_title()
        channels = s.get("autojoin") or self.net.default_autojoin
        QTimer.singleShot(1200, lambda: self.net.autojoin(channels) if self.net.connected else None)

    def network_lost(self):
        if self.net.connected:
            self.panes[""].add("quit", "* Connection lost: your modem hung up")
            self.net.disconnect_session("Connection reset by peer")
        self.connecting = False

    # ---- options ---------------------------------------------------------------------------------
    def show_options(self, connect_after=False):
        if self.options_win is not None:
            self.desktop.activate(self.options_win)
            return
        s = self.settings or {}
        from ... import user
        default_nick = user.irc_nick() if user.linked() else (self.net.aim_name or user_name())
        body = network.DialogBody()
        root = QVBoxLayout(body)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(8)
        title = QLabel("<b>Connect</b> - your IRC details")
        root.addWidget(title)
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        fields = {}
        for row, (key, label, default) in enumerate([
            ("realname", "&Full Name:", s.get("realname", user_name())),
            ("email", "&Email Address:", s.get("email", f"{user_name().lower()}@hotmail.com")),
            ("nick", "&Nickname:", s.get("nick", default_nick)),
            ("alt", "A&lternative:", s.get("alt", default_nick + "_")),
            ("autojoin", "&Join channels:", ", ".join(s.get("autojoin") or self.net.default_autojoin)),
        ]):
            edit = QLineEdit(default)
            lab = QLabel(label)
            lab.setBuddy(edit)
            grid.addWidget(lab, row, 0)
            grid.addWidget(edit, row, 1)
            fields[key] = edit
        root.addLayout(grid)
        invisible = QCheckBox("Invisible mode")
        invisible.setChecked(True)
        root.addWidget(invisible)
        buttons = QHBoxLayout()
        buttons.addStretch()
        ok = QPushButton("OK")
        ok.setDefault(True)
        cancel = QPushButton("Cancel")
        for b in (ok, cancel):
            b.setFixedSize(75, 23)
            buttons.addWidget(b)
        root.addLayout(buttons)
        body.setFixedWidth(330)

        def close():
            if self.options_win is not None:
                win, self.options_win = self.options_win, None
                self.desktop.close_window(win)

        def accept():
            nick = fields["nick"].text().strip() or default_nick
            self.settings = {
                "realname": fields["realname"].text().strip(),
                "email": fields["email"].text().strip(),
                "nick": nick,
                "alt": fields["alt"].text().strip() or nick + "_",
                "autojoin": [c.strip() if c.strip().startswith("#") else "#" + c.strip()
                             for c in fields["autojoin"].text().split(",") if c.strip()],
            }
            save_json(SETTINGS_FILE, self.settings)
            close()
            if connect_after:
                self.connect_server()

        ok.clicked.connect(accept)
        cancel.clicked.connect(close)
        for edit in fields.values():
            edit.returnPressed.connect(accept)
        self.options_win = network._fixed_window(self.desktop, "ClaudeIRC Options", body, close)
        self.options_win.icon = self.frame.icon if self.frame else QIcon()
        self.desktop.open_window(self.options_win)
        fields["nick"].setFocus()

    def _about(self):
        self.panes[""].add("info", "* ClaudeIRC v6.02 for ClaudeXP. Say hi to everyone on FurNet!")
        self.show_pane("")

    def shutdown(self):
        if self.net.connected:
            self.net.disconnect_session("Leaving")
        self.connecting = False

    def closeEvent(self, event):
        self.shutdown()
        if self.options_win is not None:
            self.desktop.close_window(self.options_win)
            self.options_win = None
        event.accept()
