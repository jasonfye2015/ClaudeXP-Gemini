"""Dial-up networking: 'Connect America Online', the modem, and the two-monitors tray icon.

Other programs ask for the Internet with network.connect(desktop, then=callback) and
hear about hang-ups through network.on_disconnect(callback).
"""
import json
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
                               QLabel, QLineEdit, QMenu, QPushButton, QVBoxLayout, QWidget)
from shiboken6 import isValid

from . import sound
from .paths import DATA, pixmap
from .tray import TrayIcon
from .user import user_name
from .wm import XPWindow

CONNECTION = "America Online"
SPEED = "53.3 Kbps"
SETTINGS_FILE = DATA / "network.json"
VERIFY_AT, REGISTER_AT = 0.45, 0.8    # fractions of the modem sound for each stage
NO_SOUND_MS = 8000                    # how long to pretend when the sound is off

DIALOG_STYLE = """
QWidget#dialog { background: #ECE9D8; }
QLabel, QCheckBox { background: transparent; }
QGroupBox { background: transparent; }
"""
MENU_STYLE = """
QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }
QMenu::item { padding: 4px 24px 4px 20px; }
QMenu::item:selected { background: #316AC5; color: white; }
QMenu::item:default { font-weight: bold; }
"""


# ---- icon ------------------------------------------------------------------------

def network_pixmap(size=16, lit=(False, False)):
    """XP's two overlapping monitors; lit screens show traffic."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 16.0
    for (x, y), on in (((0.5, 0.5), lit[0]), ((5.5, 5.5), lit[1])):
        body = QRectF(x * s, y * s, 10 * s, 8 * s)
        p.setPen(QPen(QColor("#2B2B2B"), max(1.0, s * 0.8)))
        p.setBrush(QColor("#D9D9D9"))
        p.drawRect(body)
        screen = body.adjusted(1.5 * s, 1.5 * s, -1.5 * s, -1.5 * s)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#A8E0FF") if on else QColor("#1E5BC6"))
        p.drawRect(screen)
        p.setBrush(QColor("#7A7A7A"))
        p.drawRect(QRectF(body.center().x() - 1.5 * s, body.bottom(), 3 * s, 1.5 * s))
    p.end()
    return pm


def network_icon():
    icon = QIcon()
    for size in (16, 32):
        icon.addPixmap(network_pixmap(size))
    return icon


# ---- settings ----------------------------------------------------------------------

def _load():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    data.setdefault("user", user_name().lower())
    data.setdefault("password", "")
    data.setdefault("save_password", True)
    data.setdefault("number", "555-0142")
    from . import user
    if user.linked():
        # one online identity: AOL signs on with the shared handle and (saved) online password
        data.update(user=user.online_handle(), password=user.online_password(), save_password=True)
    return data


def _save(data):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class DialogBody(QWidget):
    """Beige XP dialog background; on_close runs when the window's X is clicked."""

    def __init__(self):
        super().__init__()
        self.on_close = None
        self.setObjectName("dialog")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.restyle()

    def restyle(self):
        """The dialog face: XP's beige, or the Windows Classic colour scheme's."""
        from . import theme
        pal = theme.current().palette()
        self.setStyleSheet(DIALOG_STYLE if pal is None else
                           DIALOG_STYLE.replace("#ECE9D8", pal.window().color().name()))

    def closeEvent(self, event):
        event.accept()
        if self.on_close:
            self.on_close()


def _dialog_body():
    return DialogBody()


def _fixed_window(desktop, title, body, closer):
    """An XP dialog frame around body; closer() runs when the X is clicked."""
    body.setFixedSize(body.sizeHint().expandedTo(body.minimumSize()))
    body.on_close = closer
    win = XPWindow(desktop, title, body, network_icon(), buttons=("close",))
    win.fit_fixed_content()
    area = desktop.work_area()
    win.move(area.center() - win.rect().center())
    win.placed = True
    return win


# ---- the connection -----------------------------------------------------------------

class Network:
    def __init__(self, desktop):
        self.desktop = desktop
        self.connected = False
        self.connected_at = None
        self.sent = self.received = 0
        self.waiting = []          # callbacks for when we're online
        self.disconnect_listeners = []
        self.connect_win = None
        self.progress_win = None
        self.status_win = None
        self.player = None
        self.stage = 0
        self.tray = None
        self.traffic = QTimer()
        self.traffic.timeout.connect(self._traffic_tick)

    # ---- public ------------------------------------------------------------
    def connect(self, then=None):
        if then:
            self.waiting.append(then)
        if self.connected:
            self._run_waiting()
        elif self.progress_win is not None:
            self.desktop.activate(self.progress_win)
        elif self.connect_win is not None:
            self.desktop.activate(self.connect_win)
        else:
            self._show_connect()

    def disconnect(self, quiet=False):
        self.waiting.clear()
        self._cancel_dialing()
        if self.connect_win is not None:
            self.desktop.close_window(self.connect_win)
            self.connect_win = None
        if self.status_win is not None:
            self.desktop.close_window(self.status_win)
            self.status_win = None
        if not self.connected:
            return
        self.connected = False
        self.traffic.stop()
        if self.tray is not None:
            self.tray.hide()
            self.tray.deleteLater()
            self.tray = None
        for listener in list(self.disconnect_listeners):
            listener(quiet)

    # ---- Connect dialog -------------------------------------------------------
    def _show_connect(self):
        settings = _load()
        body = _dialog_body()
        root = QVBoxLayout(body)
        root.setContentsMargins(0, 0, 0, 10)
        root.setSpacing(8)

        banner = QLabel()
        banner.setAlignment(Qt.AlignCenter)
        banner.setStyleSheet("background: white; border-bottom: 1px solid #ACA899;")
        logo = pixmap("aol_logo.png")
        if not logo.isNull():
            banner.setPixmap(logo.scaledToHeight(84, Qt.SmoothTransformation))
        banner.setFixedHeight(100)
        root.addWidget(banner)

        form = QGridLayout()
        form.setContentsMargins(14, 4, 14, 0)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)
        user = QLineEdit(settings["user"])
        password = QLineEdit(settings["password"] if settings["save_password"] else "")
        password.setEchoMode(QLineEdit.Password)
        save = QCheckBox("Save this user name and password")
        save.setChecked(settings["save_password"])
        number = QComboBox()
        number.setEditable(True)
        number.addItem(settings["number"])
        for row, (text, field) in enumerate([("&User name:", user), ("&Password:", password),
                                             (None, save), ("D&ial:", number)]):
            if text is None:
                form.addWidget(field, row, 0, 1, 2)
                continue
            label = QLabel(text)
            label.setBuddy(field)  # makes the & an Alt+key shortcut, like XP
            form.addWidget(label, row, 0)
            form.addWidget(field, row, 1)
        root.addLayout(form)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(14, 6, 14, 0)
        dial = QPushButton("&Dial")
        dial.setDefault(True)
        cancel = QPushButton("Cancel")
        props = QPushButton("Pr&operties")
        help_btn = QPushButton("&Help")
        for b in (dial, cancel, props, help_btn):
            b.setFixedSize(72, 23)
            buttons.addWidget(b)
        root.addLayout(buttons)
        body.setFixedWidth(340)

        def do_dial():
            settings.update(user=user.text().strip(), save_password=save.isChecked(),
                            password=password.text() if save.isChecked() else "",
                            number=number.currentText().strip() or settings["number"])
            _save(settings)
            self._close_connect()
            self._start_dialing(settings["number"])

        dial.clicked.connect(do_dial)
        user.returnPressed.connect(do_dial)
        password.returnPressed.connect(do_dial)
        cancel.clicked.connect(self._cancel_connect)
        props.clicked.connect(lambda: sound.play("default"))
        help_btn.clicked.connect(lambda: sound.play("default"))

        self.connect_win = _fixed_window(self.desktop, f"Connect {CONNECTION}", body, self._cancel_connect)
        self.desktop.open_window(self.connect_win)
        (password if not password.text() else dial).setFocus()

    def _close_connect(self):
        if self.connect_win is not None:
            win, self.connect_win = self.connect_win, None
            self.desktop.close_window(win)

    def _cancel_connect(self):
        self.waiting.clear()
        self._close_connect()

    # ---- dialing ----------------------------------------------------------------
    def _start_dialing(self, number):
        body = _dialog_body()
        layout = QHBoxLayout(body)
        layout.setContentsMargins(14, 14, 14, 12)
        layout.setSpacing(12)
        pic = QLabel()
        pic.setPixmap(network_pixmap(32))
        pic.setAlignment(Qt.AlignTop)
        layout.addWidget(pic)
        col = QVBoxLayout()
        self.status_label = QLabel(f"Dialing {number}...")
        self.status_label.setMinimumWidth(260)
        col.addWidget(self.status_label)
        col.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setFixedSize(72, 23)
        cancel.clicked.connect(self._user_cancelled_dial)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(cancel)
        col.addLayout(row)
        layout.addLayout(col)
        body.setFixedHeight(96)

        self.progress_win = _fixed_window(self.desktop, f"Connecting {CONNECTION}...", body,
                                          self._user_cancelled_dial)
        self.desktop.open_window(self.progress_win)
        self.stage = 0
        self.player = sound.play_file("modem.mp3", on_finished=self._dial_finished)
        if self.player is None:
            QTimer.singleShot(int(NO_SOUND_MS * VERIFY_AT), lambda: self._set_stage(1))
            QTimer.singleShot(int(NO_SOUND_MS * REGISTER_AT), lambda: self._set_stage(2))
            QTimer.singleShot(NO_SOUND_MS, self._dial_finished)
        else:
            self.player.positionChanged.connect(self._modem_progress)

    def _modem_progress(self, pos):
        dur = self.player.duration() if self.player is not None else 0
        if dur <= 0:
            return
        if pos >= dur * REGISTER_AT:
            self._set_stage(2)
        elif pos >= dur * VERIFY_AT:
            self._set_stage(1)

    def _set_stage(self, stage):
        if self.progress_win is None or stage <= self.stage:
            return
        self.stage = stage
        self.status_label.setText(["", "Verifying user name and password...",
                                   "Registering your computer on the network..."][stage])

    def _dial_finished(self):
        if self.progress_win is None:
            return  # cancelled
        self.player = None
        win, self.progress_win = self.progress_win, None
        self.desktop.close_window(win)
        self._went_online()

    def _cancel_dialing(self):
        if self.player is not None:
            player, self.player = self.player, None
            if isValid(player):
                player.stop()
                player.deleteLater()
        if self.progress_win is not None:
            win, self.progress_win = self.progress_win, None
            self.desktop.close_window(win)

    def _user_cancelled_dial(self):
        self.waiting.clear()
        self._cancel_dialing()

    # ---- online -------------------------------------------------------------------
    def _went_online(self):
        self.connected = True
        self.connected_at = time.monotonic()
        self.sent, self.received = random.randint(400, 900), random.randint(1200, 2600)
        self.tray = TrayIcon(self.desktop, QIcon(network_pixmap(16)))
        menu = QMenu()
        menu.setStyleSheet(MENU_STYLE)
        status = menu.addAction("Status", self._show_status)
        menu.setDefaultAction(status)
        menu.addAction("Disconnect", lambda: self.disconnect())
        self.tray_menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self._update_tooltip()
        self.tray.show()
        self.tray.showMessage(f"{CONNECTION} is now connected", f"Speed: {SPEED}", None, 6000)
        self.traffic.start(350)
        from . import life
        if life.get() is not None:
            life.get().connected()
        self._run_waiting()

    def _run_waiting(self):
        waiting, self.waiting = self.waiting, []
        for callback in waiting:
            callback()

    def _tray_activated(self, reason):
        from PySide6.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_status()

    def _traffic_tick(self):
        if self.tray is None:
            return
        busy = random.random() < 0.35
        if busy:
            self.sent += random.randint(40, 400)
            self.received += random.randint(80, 1500)
        lit = (busy and random.random() < 0.6, busy and random.random() < 0.8)
        self.tray.setIcon(QIcon(network_pixmap(16, lit)))
        self._update_tooltip()

    def _update_tooltip(self):
        self.tray.setToolTip(f"{CONNECTION}\nSpeed: {SPEED}\nSent: {self.sent:,} bytes\n"
                             f"Received: {self.received:,} bytes")

    def _duration_text(self):
        secs = int(time.monotonic() - self.connected_at)
        return f"{secs // 3600:02d}:{secs // 60 % 60:02d}:{secs % 60:02d}"

    # ---- Status window ---------------------------------------------------------------
    def _show_status(self):
        if self.status_win is not None:
            self.desktop.activate(self.status_win)
            return
        body = _dialog_body()
        root = QVBoxLayout(body)
        root.setContentsMargins(12, 12, 12, 12)
        conn = QGroupBox("Connection")
        cform = QFormLayout(conn)
        status, duration, speed = QLabel("Connected"), QLabel(), QLabel(SPEED)
        cform.addRow("Status:", status)
        cform.addRow("Duration:", duration)
        cform.addRow("Speed:", speed)
        activity = QGroupBox("Activity")
        aform = QFormLayout(activity)
        sent, received = QLabel(), QLabel()
        aform.addRow("Bytes sent:", sent)
        aform.addRow("Bytes received:", received)
        root.addWidget(conn)
        root.addWidget(activity)
        row = QHBoxLayout()
        props = QPushButton("Properties")
        props.setEnabled(False)
        hang_up = QPushButton("Disconnect")
        close = QPushButton("Close")
        for b in (props, hang_up, close):
            b.setFixedSize(75, 23)
        row.addWidget(props)
        row.addWidget(hang_up)
        row.addStretch()
        row.addWidget(close)
        root.addLayout(row)
        body.setFixedWidth(300)

        def refresh():
            if not self.connected:
                return
            duration.setText(self._duration_text())
            sent.setText(f"{self.sent:,}")
            received.setText(f"{self.received:,}")

        refresh()
        timer = QTimer(body)
        timer.timeout.connect(refresh)
        timer.start(1000)

        def close_status():
            if self.status_win is not None:
                win, self.status_win = self.status_win, None
                self.desktop.close_window(win)

        hang_up.clicked.connect(lambda: self.disconnect())
        close.clicked.connect(close_status)
        self.status_win = _fixed_window(self.desktop, f"{CONNECTION} Status", body, close_status)
        self.desktop.open_window(self.status_win)


# ---- module-level access ------------------------------------------------------------------

_network = None


def get(desktop):
    global _network
    if _network is None:
        _network = Network(desktop)
    return _network


def connect(desktop, then=None):
    get(desktop).connect(then)


def is_connected():
    return _network is not None and _network.connected


def disconnect(quiet=False):
    if _network is not None:
        _network.disconnect(quiet)


def on_disconnect(desktop, callback):
    get(desktop).disconnect_listeners.append(callback)
