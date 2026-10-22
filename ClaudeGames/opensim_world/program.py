"""The Furry Hollow program: a small window that starts the world (the OpenSim server, the bridge, the Hollow Keeper),
opens the viewer logged in as you, shows what's happening, and stops everything when it's closed."""
import subprocess

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget
from shiboken6 import isValid

import opensim_world as world
from claudecore import host

_state = {"frame": None, "server": None, "bridge": None, "viewer": None}


def hollow_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#7FD3F7"))
    g.setColorAt(1, QColor("#2E8B57"))
    p.setPen(QPen(QColor("#1F5E3A"), 1))
    p.setBrush(g)
    p.drawEllipse(QRectF(2 * s, 2 * s, 28 * s, 28 * s))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#3FA35B"))
    p.drawEllipse(QRectF(4 * s, 17 * s, 24 * s, 14 * s))
    p.setBrush(QColor("#FFFFFF"))
    for x, y in ((11, 18), (16, 16), (21, 18)):                 # three little paw pads
        p.drawEllipse(QRectF((x - 1.6) * s, (y - 1.6) * s, 3.2 * s, 3.2 * s))
    p.drawEllipse(QRectF(13 * s, 20 * s, 6 * s, 5 * s))
    p.end()
    return QIcon(pm)


class HollowBody(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.setStyleSheet("QWidget { font-family: 'Segoe UI'; font-size: 12px; } QListWidget { border: 1px solid #C8C8C8; }")
        v = QVBoxLayout(self)
        title = QLabel("<b style='font-size:16px'>The Furry Hollow</b><br>Second Life on your own computer: your own "
                       "region, with the residents walking around in it.")
        title.setWordWrap(True)
        v.addWidget(title)
        self.log = QListWidget()
        v.addWidget(self.log, 1)
        row = QHBoxLayout()
        self.enter = QPushButton("Enter the Hollow")
        self.enter.setEnabled(False)
        self.enter.clicked.connect(self.open_viewer)
        self.stop_btn = QPushButton("Close the world")
        self.stop_btn.clicked.connect(lambda: self.frame.request_close() if getattr(self, "frame", None) else None)
        row.addWidget(self.enter)
        row.addStretch()
        row.addWidget(self.stop_btn)
        v.addLayout(row)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._check)
        QTimer.singleShot(100, self.start)

    def say(self, text):
        if isValid(self.log):
            self.log.addItem(text)
            self.log.scrollToBottom()

    def start(self):
        if not world.installed():
            self.say("The world isn't set up on this drive yet: it needs Local Storage\\SecondLife with dotnet\\, "
                     "opensim\\ and viewer\\ in it.")
            return
        me = world.configure()
        self.say(f"Starting the {world.REGION} (OpenSimulator)...")
        server = world.Server()
        server.start()
        _state["server"] = server
        self.started = 0
        self.timer.start(1000)
        self.me = me

    def _check(self):
        server = _state["server"]
        self.started += 1
        if server is None or not server.running():
            self.timer.stop()
            self.say("The server stopped. See Local Storage\\SecondLife\\opensim\\bin\\console.log.")
            return
        if not server.ready():
            if self.started % 15 == 0:
                self.say("Still starting...")
            return
        self.timer.stop()
        self.say("The region is up. Placing the Hollow Keeper...")
        if not world.place_keeper(server):
            self.say("Couldn't find your avatar's account on the server.")
            return
        from opensim_world.bridge import Bridge
        try:
            era = int(host.era())
        except Exception:
            era = 2025
        bridge = Bridge(self.me["first"], era=era, on_status=self.say)
        try:
            bridge.start()
        except OSError as exc:
            self.say(f"The residents' bridge couldn't start: {exc}")
        _state["bridge"] = bridge
        self.say(f"Residents in this era: {len(bridge.cast)}. They appear when you arrive.")
        self.enter.setEnabled(True)
        self.open_viewer()

    def open_viewer(self):
        viewer = _state.get("viewer")
        if viewer is not None and viewer.poll() is None:
            self.say("The viewer is already open.")
            return
        try:
            _state["viewer"] = world.launch_viewer()
            self.say(f"Opening the viewer as {self.me['first']} {self.me['last']}...")
        except OSError as exc:
            self.say(f"The viewer couldn't start: {exc}")

    def closeEvent(self, event):
        shutdown()
        event.accept()


def open_world(desktop):
    frame = _state.get("frame")
    if frame is not None and isValid(frame):
        desktop.open_window(frame)
        return frame
    body = HollowBody(desktop)
    frame = host.window(desktop, "Furry Hollow", body, hollow_icon(), (460, 340))
    body.frame = frame
    _state["frame"] = frame
    desktop.open_window(frame)
    return frame


def shutdown():
    bridge, server, viewer = _state.get("bridge"), _state.get("server"), _state.get("viewer")
    _state.update(bridge=None, server=None, viewer=None, frame=None)
    if bridge is not None:
        bridge.stop()
    if viewer is not None and viewer.poll() is None:
        try:
            viewer.terminate()
        except OSError:
            pass
    if server is not None:
        server.stop()
