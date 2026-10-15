"""RealPlayer 8 Basic and QuickTime Player 5 - two more ways to play your music and videos in 2001, each with the
nagging that came free with it.

RealPlayer: the dark RealPlayer window, Real.com Guide and Radio Tuner (whose stations buffer... and buffer), the
'make RealPlayer your default player?' question, Message Center offers for RealPlayer 8 Plus, and RealTray in the
notification area.

QuickTime: the brushed-metal player, QuickTime TV channels, 'Upgrade to QuickTime Pro' every single time you open it,
Pro-only menu items, and qttask in the notification area asking to take back your file associations.

Both really play files (mp3, wav, avi, mpg, mov, mp4, ...) through Qt Multimedia.
"""
import random
import time
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QMenuBar, QPushButton, QSlider, QStackedWidget,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from ..paths import DATA
from ..wm import XPWindow
from .people import load_json, save_json

STATE = DATA / "players.json"
MEDIA_EXTS = [".mp3", ".wav", ".wma", ".ogg", ".m4a", ".avi", ".mpg", ".mpeg", ".mp4", ".mov", ".qt", ".wmv", ".mkv",
              ".rm", ".ram", ".rmvb", ".webm"]
_open = {}
_trays = {}


def _state():
    return load_json(STATE, {})


def _set(**kw):
    s = _state()
    s.update(kw)
    save_json(STATE, s)


def _fmt(ms):
    s = max(0, ms // 1000)
    return f"{s // 60}:{s % 60:02d}"


# ---- icons ---------------------------------------------------------------------------------------------------------

def real_pixmap(size=32):
    """RealPlayer's blue disc with the white 'real' swoosh."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#3E8EF0"))
    g.setColorAt(1, QColor("#0A3A9A"))
    p.setPen(QPen(QColor("#062A70"), max(1.0, s)))
    p.setBrush(g)
    p.drawEllipse(QRectF(1.5 * s, 1.5 * s, 29 * s, 29 * s))
    f = QFont("Arial Black")
    f.setPixelSize(max(6, int(11 * s)))
    f.setItalic(True)
    p.setFont(f)
    p.setPen(QColor("white"))
    p.drawText(QRectF(0, 7 * s, size, 14 * s), Qt.AlignCenter, "real")
    p.setPen(QPen(QColor("#FFC020"), max(1.0, 1.6 * s)))
    p.drawArc(QRectF(6 * s, 17 * s, 20 * s, 8 * s), 200 * 16, 140 * 16)
    p.end()
    return pm


def qt_pixmap(size=32):
    """QuickTime's blue 'Q' on a silver ball."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    g = QLinearGradient(0, 0, size, size)
    g.setColorAt(0, QColor("#FFFFFF"))
    g.setColorAt(1, QColor("#9AA4B0"))
    p.setPen(QPen(QColor("#5A6470"), max(1.0, s)))
    p.setBrush(g)
    p.drawEllipse(QRectF(1.5 * s, 1.5 * s, 29 * s, 29 * s))
    q = QLinearGradient(0, 6 * s, 0, 26 * s)
    q.setColorAt(0, QColor("#6AB8FF"))
    q.setColorAt(1, QColor("#0A4AB8"))
    p.setPen(QPen(q, max(2.0, 5 * s), Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QRectF(8 * s, 7 * s, 15 * s, 15 * s))
    p.drawLine(QPointF(19 * s, 19 * s), QPointF(25 * s, 26 * s))
    p.end()
    return pm


def real_icon():
    return QIcon(real_pixmap(32))


def qt_icon():
    return QIcon(qt_pixmap(32))


# ---- the shared player -----------------------------------------------------------------------------------------------

class Engine(QWidget):
    """A video area (or a logo while idle) plus a QMediaPlayer."""

    def __init__(self, idle_painter, parent=None):
        super().__init__(parent)
        self.idle_painter = idle_painter
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.audio.setVolume(0.8)
        self.stack = QStackedWidget()
        self.idle = _Idle(idle_painter)
        self.video = QVideoWidget()
        self.stack.addWidget(self.idle)
        self.stack.addWidget(self.video)
        self.player.setVideoOutput(self.video)
        self.player.hasVideoChanged.connect(lambda v: self.stack.setCurrentWidget(self.video if v else self.idle))
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.stack)
        self.path = None

    def open(self, path):
        self.path = Path(path)
        self.idle.caption = self.path.name
        self.idle.update()
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.player.play()

    def stop(self):
        self.player.stop()


class _Idle(QWidget):
    def __init__(self, painter):
        super().__init__()
        self.painter = painter
        self.caption = ""
        self.message = ""

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self.painter(p, self.rect(), self.caption, self.message)


def _pick_file(desktop, title, icon, on_open):
    from .opendialog import open_dialog
    open_dialog(desktop, title, MEDIA_EXTS, on_open, icon=icon)


def _transport(engine, accent):
    """Play/pause, stop, a position slider and a time readout."""
    row = QHBoxLayout()
    play, stop = QPushButton("▶"), QPushButton("■")
    for b in (play, stop):
        b.setFixedSize(32, 24)
        b.setStyleSheet(f"QPushButton {{ background: {accent}; color: white; border: 1px solid #202020; "
                        "border-radius: 3px; font-size: 12px; } QPushButton:hover { background: #5A80C8; }")
    pos = QSlider(Qt.Horizontal)
    readout = QLabel("0:00 / 0:00")
    vol = QSlider(Qt.Horizontal)
    vol.setRange(0, 100)
    vol.setValue(80)
    vol.setFixedWidth(70)
    row.addWidget(play)
    row.addWidget(stop)
    row.addWidget(pos, 1)
    row.addWidget(readout)
    row.addWidget(vol)
    p = engine.player

    def toggle():
        if p.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            p.pause()
        elif p.source().isEmpty():
            return
        else:
            p.play()
    play.clicked.connect(toggle)
    stop.clicked.connect(p.stop)
    p.durationChanged.connect(lambda d: pos.setRange(0, d))
    p.positionChanged.connect(lambda ms: (pos.blockSignals(True), pos.setValue(ms), pos.blockSignals(False),
                                          readout.setText(f"{_fmt(ms)} / {_fmt(p.duration())}")))
    p.playbackStateChanged.connect(lambda st: play.setText(
        "❚❚" if st == QMediaPlayer.PlaybackState.PlayingState else "▶"))
    pos.sliderMoved.connect(p.setPosition)
    vol.valueChanged.connect(lambda v: engine.audio.setVolume(v / 100))
    return row


# ---- RealPlayer 8 Basic ------------------------------------------------------------------------------------------------

REAL_CSS = """
QWidget#real { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3A3F4A, stop:1 #1C1F26); }
QLabel { color: #D8DDE8; font-family: Arial; font-size: 11px; }
QMenuBar { background: #2A2E36; color: #E0E4EC; font-family: Tahoma; font-size: 11px; }
QMenuBar::item:selected { background: #3A6EC8; }
QMenu { background: white; font-family: Tahoma; font-size: 11px; }
QMenu::item:selected { background: #316AC5; color: white; }
QPushButton#chan { background: #2A3A5A; color: #E8EEF8; border: 1px solid #4A5A7A; padding: 3px 8px;
                   font-family: Arial; font-size: 11px; font-weight: bold; }
QPushButton#chan:hover { background: #3A5A8A; }
QListWidget { background: #10141C; color: #C8D8F0; border: 1px solid #4A5A7A; font-family: Arial; font-size: 11px; }
"""
STATIONS = [("KROQ 106.7 Los Angeles", "Alternative"), ("Radio Margaritaville", "Tropical Rock"),
            ("Virgin Radio UK", "Pop / Rock"), ("Digitally Imported - Trance", "Electronic"),
            ("NPR News", "News / Talk"), ("Furry Radio Network", "Fandom / Variety"), ("BBC World Service", "News"),
            ("SomaFM Groove Salad", "Ambient / Downtempo")]
MESSAGES = [("Upgrade to RealPlayer 8 Plus!", "Get the best possible sound and video quality, a 10-band graphic "
             "equalizer, CD burning and much more - for only $29.99."),
            ("RealPlayer Message Center", "You have 3 new messages: Free Music Downloads, RealJukebox Plus, and the "
             "new RealOne Player beta. Click Read to view them."),
            ("Get RealJukebox Plus", "Organize your music collection and record CDs to MP3 at 'CD quality'. Upgrade "
             "now and save 30%!"),
            ("A new version of RealPlayer is available", "RealPlayer 8 Basic build 6.0.9.584 is ready to download. "
             "Upgrade now to get the latest features and security fixes.")]


def _real_idle(p, r, caption, message):
    g = QLinearGradient(0, 0, 0, r.height())
    g.setColorAt(0, QColor("#05070C"))
    g.setColorAt(1, QColor("#14203A"))
    p.fillRect(r, g)
    p.drawPixmap(int(r.center().x() - 32), int(r.center().y() - 50), real_pixmap(64))
    f = QFont("Arial", 18)
    f.setBold(True)
    f.setItalic(True)
    p.setFont(f)
    p.setPen(QColor("#E8EEF8"))
    p.drawText(QRectF(0, r.center().y() + 18, r.width(), 28), Qt.AlignCenter, "RealPlayer 8")
    p.setFont(QFont("Arial", 9))
    p.setPen(QColor("#8FA8D8"))
    p.drawText(QRectF(0, r.center().y() + 46, r.width(), 18), Qt.AlignCenter, message or caption or "Basic")


class RealPlayer(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setObjectName("real")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(REAL_CSS)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 6)
        bar = QMenuBar()
        f = bar.addMenu("&File")
        f.addAction("&Open File...", self.open_file)
        f.addAction("Open &Location...", lambda: self._buffer("http://www.real.com/live/"))
        f.addSeparator()
        f.addAction("E&xit", lambda: self.frame.request_close() if self.frame else None)
        view = bar.addMenu("&View")
        view.addAction("&Normal Mode")
        view.addAction("&Toolbar Mode")
        view.addAction("T&heater Mode", lambda: self._message("Theater Mode is available in RealPlayer 8 Plus."))
        bar.addMenu("&Play").addAction("&Play/Pause", lambda: self.engine.player.play())
        fav = bar.addMenu("F&avorites")
        for name, _g in STATIONS[:4]:
            fav.addAction(name, lambda n=name: self._buffer(n))
        tools = bar.addMenu("&Tools")
        tools.addAction("Check for &Update...", lambda: self._nag(3))
        tools.addAction("&Message Center...", lambda: self._nag(1))
        tools.addAction("&Preferences...", lambda: self._message("Preferences: Connection 56 Kbps Modem, "
                                                                 "Buffered Play 30 seconds."))
        bar.addMenu("&Help").addAction("&About RealPlayer...", lambda: self._message(
            "RealPlayer 8 Basic\nVersion 6.0.9.584\n\nCopyright (c) 1995-2001 RealNetworks, Inc."))
        v.setMenuBar(bar)
        top = QHBoxLayout()
        top.setContentsMargins(8, 6, 8, 0)
        for name, slot in (("Real.com Guide", self._guide), ("Radio Tuner", self._tuner),
                           ("Search", lambda: self._web("http://www.real.com/search/")),
                           ("Upgrade", lambda: self._nag(0))):
            b = QPushButton(name)
            b.setObjectName("chan")
            b.clicked.connect(slot)
            top.addWidget(b)
        top.addStretch()
        v.addLayout(top)
        self.pages = QStackedWidget()
        self.engine = Engine(_real_idle)
        self.pages.addWidget(self.engine)
        self.tuner = QListWidget()
        for name, genre in STATIONS:
            self.tuner.addItem(f"{name}    -    {genre}")
        self.tuner.itemActivated.connect(lambda it: self._buffer(it.text().split("    -")[0]))
        self.pages.addWidget(self.tuner)
        v.addWidget(self.pages, 1)
        controls = _transport(self.engine, "#2A4A8A")
        controls.setContentsMargins(8, 4, 8, 0)
        v.addLayout(controls)
        self.status = QLabel("  Ready")
        v.addWidget(self.status)
        self.engine.player.playbackStateChanged.connect(self._state)
        self.buffer_timer = None

    def _state(self, st):
        playing = st == QMediaPlayer.PlaybackState.PlayingState
        self.status.setText(f"  Playing: {self.engine.path.name}" if playing and self.engine.path else "  Ready")

    def open_file(self, path=None):
        if path is None:
            _pick_file(self.desktop, "Open", real_icon(), self.open_file)
            return
        self._stop_buffering()
        self.pages.setCurrentWidget(self.engine)
        self.engine.open(path)
        if self.frame is not None:
            self.frame.set_title(f"{Path(path).name} - RealPlayer")

    def _guide(self):
        self._web("http://www.real.com/guide/")

    def _tuner(self):
        self.pages.setCurrentWidget(self.tuner if self.pages.currentWidget() is not self.tuner else self.engine)

    def _web(self, url):
        from . import navigator
        navigator.open_url(self.desktop, url)

    def _buffer(self, name):
        """Streams in 2001, on a 56K modem: buffering... network congestion... buffering..."""
        from .. import network
        self.pages.setCurrentWidget(self.engine)
        self.engine.stop()
        self._stop_buffering()
        if not network.is_connected():
            network.connect(self.desktop, then=lambda: self._buffer(name))
            return
        state = {"pct": 0, "tries": 0}
        self.buffer_timer = QTimer(self)

        def step():
            state["pct"] += random.choice((0, 1, 2, 3, 5))
            if state["pct"] >= random.randint(40, 95):
                state["tries"] += 1
                state["pct"] = 0
                self.status.setText("  Network congestion... rebuffering")
                self.engine.idle.message = "Network congestion"
                if state["tries"] >= 3:
                    self._stop_buffering()
                    self.engine.idle.message = ""
                    self.status.setText("  Ready")
                    self._message(f"Unable to play '{name}'.\n\nGeneral error: the server is busy or the network "
                                  "connection was lost (error 0x80040fb3). Try again later.")
                    return
            else:
                self.status.setText(f"  Buffering {name}... {state['pct']}%")
                self.engine.idle.message = f"Buffering... {state['pct']}%"
            self.engine.idle.update()
        self.buffer_timer.timeout.connect(step)
        self.buffer_timer.start(400)

    def _stop_buffering(self):
        if self.buffer_timer is not None:
            self.buffer_timer.stop()
            self.buffer_timer = None

    def _message(self, text):
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, "RealPlayer", text, "info", window_icon=real_icon())

    def _nag(self, which=None):
        title, text = MESSAGES[which if which is not None else random.randrange(len(MESSAGES))]
        from ..explorer.dialogs import msgbox

        def answer(b):
            if b in ("Upgrade Now", "Read"):
                self._web("http://www.real.com/products/player/")
        msgbox(self.desktop, title, text, "info", ("Upgrade Now", "Later") if which != 1 else ("Read", "Later"),
               answer, window_icon=real_icon())

    def shutdown(self):
        self._stop_buffering()
        self.engine.stop()


def open_realplayer(desktop, path=None):
    win = _open.get("real")
    if win is not None and isValid(win):
        desktop.open_window(win)
        if path:
            win.content.open_file(path)
        return win
    body = RealPlayer(desktop)
    win = XPWindow(desktop, "RealPlayer", body, real_icon(), size=(470, 420))
    body.frame = win
    _open["real"] = win
    desktop.open_window(win)
    st = _state()
    if not st.get("real_asked"):                         # the very first time: 'make me your default player?'
        _set(real_asked=True)
        QTimer.singleShot(700, lambda: _real_default(desktop))
    elif random.random() < 0.5:
        QTimer.singleShot(1500, lambda: isValid(body) and body._nag())
    if path:
        body.open_file(path)
    return win


def _real_default(desktop):
    from ..explorer.dialogs import msgbox
    from .. import defaults

    def answer(b):
        if b == "Yes":
            defaults.set("media", "realplayer")
    msgbox(desktop, "RealPlayer - Universal Player", "RealPlayer can play almost any media type, including MP3, WAV, "
           "AVI, MPEG and QuickTime.\n\nWould you like RealPlayer to be your default player for these media types?",
           "question", ("Yes", "No"), answer, window_icon=real_icon())


def shutdown_realplayer():
    win = _open.get("real")
    if win is not None and isValid(win):
        win.content.shutdown()


# ---- QuickTime Player 5 -------------------------------------------------------------------------------------------------

QT_CSS = """
QWidget#qt { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E6E8EC, stop:0.5 #C4C8D0, stop:1 #A8ADB6); }
QLabel { color: #1A1A1A; font-family: 'Lucida Grande', Tahoma; font-size: 11px; }
QMenuBar { background: #DCDEE2; font-family: Tahoma; font-size: 11px; }
QMenuBar::item:selected { background: #3A6EC8; color: white; }
QMenu { background: white; font-family: Tahoma; font-size: 11px; }
QMenu::item:selected { background: #316AC5; color: white; }
QMenu::item:disabled { color: #A0A0A0; }
QPushButton#tv { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #C8CCD4);
                 border: 1px solid #8A9098; border-radius: 6px; padding: 4px; font-family: Tahoma; font-size: 10px; }
QPushButton#tv:hover { border: 1px solid #3A6EC8; }
"""
CHANNELS = ["BBC World", "Fox Movies", "NPR", "Rolling Stone", "WGBH", "Disney", "ESPN", "Weather Channel",
            "Bloomberg", "VH1", "HBO", "Nickelodeon"]


def _qt_idle(p, r, caption, message):
    p.fillRect(r, QColor("#000000"))
    p.drawPixmap(int(r.center().x() - 32), int(r.center().y() - 44), qt_pixmap(64))
    f = QFont("Tahoma", 14)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#E8E8E8"))
    p.drawText(QRectF(0, r.center().y() + 26, r.width(), 26), Qt.AlignCenter, "QuickTime")
    p.setFont(QFont("Tahoma", 9))
    p.setPen(QColor("#9AA0A8"))
    p.drawText(QRectF(0, r.center().y() + 50, r.width(), 18), Qt.AlignCenter, message or caption)


class QuickTime(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setObjectName("qt")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(QT_CSS)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 6)
        bar = QMenuBar()
        f = bar.addMenu("&File")
        f.addAction("&New Player")
        f.addAction("&Open Movie in New Player...", self.open_file)
        f.addAction("Open &URL in New Player...", lambda: self._channel("URL"))
        f.addSeparator()
        for pro in ("Save", "Save As...", "Export...", "Present Movie..."):
            f.addAction(f"{pro}  (Pro)", self.pro_nag)
        f.addSeparator()
        f.addAction("E&xit", lambda: self.frame.request_close() if self.frame else None)
        e = bar.addMenu("&Edit")
        for pro in ("Undo", "Cut", "Copy", "Paste", "Clear", "Add", "Trim"):
            e.addAction(f"{pro}  (Pro)", self.pro_nag)
        m = bar.addMenu("&Movie")
        m.addAction("&Half Size")
        m.addAction("&Normal Size")
        m.addAction("&Double Size")
        m.addAction("&Full Screen  (Pro)", self.pro_nag)
        m.addSeparator()
        m.addAction("Show Movie &Info", self._info)
        fav = bar.addMenu("F&avorites")
        fav.addAction("Add Movie As Favorite  (Pro)", self.pro_nag)
        hp = bar.addMenu("&Help")
        hp.addAction("&QuickTime Player Help")
        hp.addAction("&Update Existing Software...", lambda: self._message("Connecting to the QuickTime Update "
                                                                           "Server...\n\nQuickTime 5.0.5 is up to "
                                                                           "date."))
        hp.addAction("&About QuickTime Player...", lambda: self._message(
            "QuickTime Player 5.0.5\n\nCopyright (c) 1991-2001 Apple Computer, Inc.\nAll Rights Reserved."))
        v.setMenuBar(bar)
        self.engine = Engine(_qt_idle)
        self.engine.setMinimumHeight(180)
        v.addWidget(self.engine, 1)
        controls = _transport(self.engine, "#5A6A80")
        controls.setContentsMargins(8, 4, 8, 0)
        v.addLayout(controls)
        drawer = QWidget()
        dv = QHBoxLayout(drawer)
        dv.setContentsMargins(8, 4, 8, 0)
        tv = QLabel("<b>QuickTime TV</b>")
        dv.addWidget(tv)
        for name in CHANNELS[:6]:
            b = QPushButton(name)
            b.setObjectName("tv")
            b.clicked.connect(lambda _c=False, n=name: self._channel(n))
            dv.addWidget(b)
        v.addWidget(drawer)
        self.timer = None

    def open_file(self, path=None):
        if path is None:
            _pick_file(self.desktop, "Open Movie", qt_icon(), self.open_file)
            return
        self.engine.open(path)
        if self.frame is not None:
            self.frame.set_title(Path(path).name)

    def _channel(self, name):
        from .. import network
        if not network.is_connected():
            network.connect(self.desktop, then=lambda: self._channel(name))
            return
        self.engine.stop()
        steps = ["Connecting...", "Negotiating...", "Requested data...", "Buffering... (streaming over 56K)"]
        state = {"i": 0}
        t = self.timer = QTimer(self)

        def step():
            if state["i"] < len(steps):
                self.engine.idle.message = f"{name}: {steps[state['i']]}"
                state["i"] += 1
            else:
                t.stop()
                self.engine.idle.message = ""
                self._message(f"The QuickTime TV channel '{name}' couldn't be reached.\n\nThe server may be busy, "
                              "or your connection is too slow for this stream. Try again later.")
            self.engine.idle.update()
        t.timeout.connect(step)
        t.start(1300)

    def _info(self):
        p = self.engine.path
        self._message(f"Movie Info\n\nSource: {p.name if p else '(none)'}\nDuration: "
                      f"{_fmt(self.engine.player.duration())}\nData Rate: 128 kbits/sec")

    def _message(self, text):
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, "QuickTime Player", text, "info", window_icon=qt_icon())

    def pro_nag(self):
        pro_nag(self.desktop)

    def shutdown(self):
        if self.timer is not None:
            self.timer.stop()
        self.engine.stop()


def pro_nag(desktop):
    """The legendary one."""
    from ..explorer.dialogs import msgbox

    def answer(b):
        if b == "Upgrade Now":
            from . import navigator
            navigator.open_url(desktop, "http://www.apple.com/quicktime/upgrade/")
    msgbox(desktop, "Upgrade to QuickTime Pro", "Upgrade to QuickTime Pro and get:\n\n   * Full-screen video\n"
           "   * Create, edit and save movies\n   * Export to dozens of formats\n   * Create slideshows\n\nUpgrade "
           "today for just $29.99.", "info", ("Upgrade Now", "Later"), answer, window_icon=qt_icon())


def open_quicktime(desktop, path=None):
    win = _open.get("qt")
    if win is not None and isValid(win):
        desktop.open_window(win)
        if path:
            win.content.open_file(path)
        return win
    body = QuickTime(desktop)
    win = XPWindow(desktop, "QuickTime Player", body, qt_icon(), size=(500, 400))
    body.frame = win
    _open["qt"] = win
    desktop.open_window(win)
    QTimer.singleShot(600, lambda: pro_nag(desktop))           # every time. Every. Time.
    if path:
        body.open_file(path)
    return win


def shutdown_quicktime():
    win = _open.get("qt")
    if win is not None and isValid(win):
        win.content.shutdown()


# ---- the tray helpers they install ------------------------------------------------------------------------------

def at_logon(desktop, real=True, qt=True):
    """RealTray and qttask: both start with Windows and sit in the notification area (unless msconfig says no)."""
    from . import installed
    from ..tray import TrayIcon
    from PySide6.QtWidgets import QMenu, QSystemTrayIcon
    from .. import defaults
    if real and not installed.is_removed("realplayer") and "real" not in _trays:
        t = _trays["real"] = TrayIcon(desktop, QIcon(real_pixmap(16)), desktop)
        t.setToolTip("RealPlayer")
        m = QMenu(desktop)
        m.addAction("Start RealPlayer", lambda: open_realplayer(desktop))
        m.addAction("Check for Update...", lambda: open_realplayer(desktop).content._nag(3))
        m.addSeparator()
        m.addAction("Exit", lambda: (t.hide(), _trays.pop("real", None)))
        t.setContextMenu(m)
        t.activated.connect(lambda r: open_realplayer(desktop) if r == QSystemTrayIcon.DoubleClick else None)
        t.messageClicked.connect(lambda: open_realplayer(desktop))
        t.show()
        if random.random() < 0.3:
            QTimer.singleShot(45000, lambda: t.showMessage("RealPlayer", "The new RealOne Player is here! Click to "
                                                           "find out more.", None, 8000))
    if qt and not installed.is_removed("quicktime") and "qt" not in _trays:
        t2 = _trays["qt"] = TrayIcon(desktop, QIcon(qt_pixmap(16)), desktop)
        t2.setToolTip("QuickTime")
        m2 = QMenu(desktop)
        m2.addAction("Open QuickTime Player", lambda: open_quicktime(desktop))
        m2.addAction("QuickTime Settings...", lambda: _qt_associations(desktop))
        m2.addSeparator()
        m2.addAction("Exit", lambda: (t2.hide(), _trays.pop("qt", None)))
        t2.setContextMenu(m2)
        t2.activated.connect(lambda r: open_quicktime(desktop) if r == QSystemTrayIcon.DoubleClick else None)
        t2.show()
        st = _state()
        if defaults.get("media") != "quicktime" and time.time() - st.get("qt_assoc_nag", 0) > 3 * 86400:
            _set(qt_assoc_nag=time.time())
            QTimer.singleShot(60000, lambda: desktop.isVisible() and _qt_associations(desktop))


def _qt_associations(desktop):
    from ..explorer.dialogs import msgbox
    from .. import defaults

    def answer(b):
        if b == "Yes":
            defaults.set("media", "quicktime")
    msgbox(desktop, "QuickTime", "QuickTime has detected that some of its file associations have been changed by "
           "another application.\n\nWould you like QuickTime to restore its file associations (.mov, .mp3, .mpg, "
           ".avi and others)?", "question", ("Yes", "No"), answer, window_icon=qt_icon())

