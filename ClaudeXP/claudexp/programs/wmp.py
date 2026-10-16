"""Windows Media Player 8 (the one XP shipped with): the Features taskbar (Now Playing, Media Guide, Copy from CD,
Media Library, Radio Tuner, Copy to CD or Device, Skin Chooser), visualizations that really move to the music
(Bars, Scope, Ambience), a Now Playing list, a Media Library built from My Music, Shared Music, C:\\WINDOWS\\Media
and the external drive (with ID3 tags), shuffle/repeat, and four colour skins."""
import json
import math
import random
import struct
import wave
from collections import deque
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import (QAction, QActionGroup, QBrush, QColor, QFont, QIcon, QKeySequence, QLinearGradient,
                           QPainter, QPainterPath, QPen, QPixmap, QRadialGradient)
from PySide6.QtMultimedia import QAudioBufferOutput, QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QListWidget, QListWidgetItem,
                               QMenuBar, QPushButton, QSlider, QStackedWidget, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import network, sound
from ..paths import DATA, SOUNDS
from ..wm import XPWindow
from .notepad import MENU_STYLE
from .people import load_json, save_json

AUDIO_EXTS = {".mp3", ".wav", ".wma", ".m4a", ".ogg", ".flac"}
STATE_FILE = DATA / "wmp.json"
FEATURES = ["Now Playing", "Media Guide", "Copy from CD", "Media Library", "Radio Tuner", "Copy to CD or Device",
            "Skin Chooser"]
VISUALIZATIONS = ["Bars and Waves : Bars", "Bars and Waves : Scope", "Ambience : Water"]
SKINS = {  # name: (top, bottom, accent, text)
    "Windows XP": ("#3A5FA8", "#0F2557", "#7FB2FF", "#FFFFFF"),
    "Silver": ("#E6E8EE", "#9EA3B0", "#3060C0", "#101820"),
    "Olive Green": ("#8DA35E", "#3E4F22", "#E0F0A0", "#FFFFFF"),
    "Midnight": ("#303040", "#08080C", "#FF9A30", "#E8E8F0"),
}
STATIONS = [("Classic Rock Café", "Rock", "128K"), ("Smooth Jazz 24/7", "Jazz", "56K"),
            ("Top 40 Now!", "Pop", "128K"), ("Club Beats Radio", "Electronica", "96K"),
            ("Country Roads FM", "Country", "56K"), ("Talk of the Town", "News/Talk", "32K")]


def wmp_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QRadialGradient(QPointF(12, 10), 20)
    g.setColorAt(0, QColor("#FFD27A"))
    g.setColorAt(1, QColor("#E06A00"))
    p.setPen(QPen(QColor("#A04000"), 1))
    p.setBrush(g)
    p.drawEllipse(QRectF(2, 2, 28, 28))
    tri = QPainterPath()
    tri.moveTo(12, 9)
    tri.lineTo(23, 16)
    tri.lineTo(12, 23)
    tri.closeSubpath()
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("white"))
    p.drawPath(tri)
    p.end()
    return QIcon(pm)


# ---- the library ---------------------------------------------------------------------------------------------------

def _id3(path):
    """Title / artist / album from ID3v2 (2.3/2.4) or ID3v1 tags; fallbacks from the file name."""
    tags = {}
    try:
        with open(path, "rb") as f:
            head = f.read(10)
            if head[:3] == b"ID3":
                size = (head[6] & 0x7F) << 21 | (head[7] & 0x7F) << 14 | (head[8] & 0x7F) << 7 | (head[9] & 0x7F)
                data = f.read(size)
                i = 0
                while i + 10 <= len(data):
                    fid = data[i:i + 4].decode("latin-1", "replace")
                    fsize = struct.unpack(">I", data[i + 4:i + 8])[0]
                    if head[3] == 4:
                        b = data[i + 4:i + 8]
                        fsize = (b[0] & 0x7F) << 21 | (b[1] & 0x7F) << 14 | (b[2] & 0x7F) << 7 | (b[3] & 0x7F)
                    if not fid.strip("\0") or fsize <= 0:
                        break
                    body = data[i + 10:i + 10 + fsize]
                    if fid in ("TIT2", "TPE1", "TALB", "TCON") and body:
                        enc, text = body[0], body[1:]
                        codec = {0: "latin-1", 1: "utf-16", 2: "utf-16-be", 3: "utf-8"}.get(enc, "latin-1")
                        tags[fid] = text.decode(codec, "replace").strip("\0 ").split("\0")[0]
                    i += 10 + fsize
            f.seek(-128, 2)
            tail = f.read(128)
            if tail[:3] == b"TAG":
                def field(a, b):
                    return tail[a:b].decode("latin-1", "replace").strip("\0 ")
                tags.setdefault("TIT2", field(3, 33))
                tags.setdefault("TPE1", field(33, 63))
                tags.setdefault("TALB", field(63, 93))
    except OSError:
        pass
    return tags


def _length(path):
    """Seconds, estimated without decoding (WAV header, or MP3 size / bitrate)."""
    try:
        if path.suffix.lower() == ".wav":
            with wave.open(str(path)) as w:
                return w.getnframes() / max(1, w.getframerate())
        if path.suffix.lower() == ".mp3":
            data = path.read_bytes()[:200_000]
            i = 0
            if data[:3] == b"ID3":
                i = 10 + ((data[6] & 0x7F) << 21 | (data[7] & 0x7F) << 14 | (data[8] & 0x7F) << 7 | (data[9] & 0x7F))
            while i + 4 < len(data):
                if data[i] == 0xFF and data[i + 1] & 0xE0 == 0xE0:
                    rates = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
                    br = rates[(data[i + 2] >> 4) & 15] if (data[i + 2] >> 4) & 15 < 15 else 128
                    if br:
                        return path.stat().st_size * 8 / (br * 1000)
                i += 1
    except (OSError, wave.Error, EOFError):
        pass
    return 0


def fmt_time(seconds, round_up=False):
    seconds = math.ceil(seconds or 0) if round_up else int(seconds or 0)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class Track:
    def __init__(self, path):
        self.path = Path(path)
        tags = _id3(self.path) if self.path.suffix.lower() == ".mp3" else {}
        self.title = tags.get("TIT2") or self.path.stem.replace("_", " ")
        self.artist = tags.get("TPE1") or "Unknown Artist"
        self.album = tags.get("TALB") or "Unknown Album"
        self.genre = tags.get("TCON") or ""
        self.length = _length(self.path)


def library_folders():
    from ..explorer import vfs
    return [("My Music", vfs.my_music()), ("Shared Music", vfs.shared_documents() / "Shared Music"),
            ("Windows Sounds", vfs.DRIVE_C / "WINDOWS" / "Media"), ("External Drive (E:)", vfs.local_storage())]


def ensure_sample_music():
    """Like XP's 'Sample Music' folder, once: the Welcome to Windows music, as a real track to play."""
    from ..explorer import vfs
    state = load_json(STATE_FILE, {})
    if state.get("sample_added"):
        return
    folder = vfs.shared_documents() / "Shared Music" / "Sample Music"
    folder.mkdir(parents=True, exist_ok=True)
    src = SOUNDS / "oobe_music.mp3"
    if src.exists():
        import shutil
        shutil.copy2(src, folder / "Welcome to Windows (Intro Music).mp3")
    state["sample_added"] = True
    save_json(STATE_FILE, state)


def scan_library():
    tracks = []
    for _label, folder in library_folders():
        if folder.exists():
            for p in sorted(folder.rglob("*")):
                if p.is_file() and p.suffix.lower() in AUDIO_EXTS:
                    tracks.append(Track(p))
    return tracks


# ---- visualizations -------------------------------------------------------------------------------------------------

class Visualizer(QWidget):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.mode = 0
        self.samples = deque([0.0] * 1024, maxlen=1024)
        self.bands = [0.0] * 20
        self.peaks = [0.0] * 20
        self.level = 0.0
        self.phase = 0.0
        self.setMinimumSize(260, 180)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)
        # Goertzel coefficients for 20 log-spaced bands, 80 Hz .. 5 kHz. The analysis runs on 256 samples at
        # ~11 kHz (the stored 22 kHz stream, every other sample).
        n, rate = 256, 11025
        self.coeffs = []
        for i in range(20):
            freq = 80 * (5000 / 80) ** (i / 19)
            k = max(1, n * freq / rate)
            self.coeffs.append(2 * math.cos(2 * math.pi * k / n))

    def feed(self, buf):
        fmt = buf.format()
        ch = max(1, fmt.channelCount())
        try:
            data = buf.constData()
            if fmt.sampleFormat().name == "Float":
                vals = data.cast("f")
            elif fmt.sampleFormat().name == "Int16":
                vals = [v / 32768 for v in data.cast("h")]
            else:
                return
        except (TypeError, ValueError):
            return
        mono = [sum(vals[i:i + ch]) / ch for i in range(0, len(vals) - ch + 1, ch)]
        self.samples.extend(mono[::2])          # ~22 kHz is plenty for drawing

    def tick(self):
        playing = self.player.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        if not playing:
            self.samples.extend([0.0] * 64)
        recent = list(self.samples)[-512:]
        self.level = self.level * 0.6 + 0.4 * min(1.0, math.sqrt(sum(v * v for v in recent) / len(recent)) * 3)
        for i, c in enumerate(self.coeffs):
            s1 = s2 = 0.0
            for x in recent[::2]:
                s1, s2 = x + c * s1 - s2, s1
            power = s1 * s1 + s2 * s2 - c * s1 * s2
            value = min(1.0, math.log10(1 + power) / 1.6)
            self.bands[i] = max(value, self.bands[i] * 0.82)
            self.peaks[i] = max(self.bands[i], self.peaks[i] - 0.015)
        self.phase += 0.02 + self.level * 0.08
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("black"))
        w, h = self.width(), self.height()
        if self.mode == 0:
            n = len(self.bands)
            bw = w / n
            for i, v in enumerate(self.bands):
                bh = v * (h - 10)
                r = QRectF(i * bw + 2, h - bh, bw - 4, bh)
                g = QLinearGradient(0, h, 0, 0)
                g.setColorAt(0, QColor("#00C000"))
                g.setColorAt(0.6, QColor("#E0E000"))
                g.setColorAt(1, QColor("#FF2000"))
                p.fillRect(r, g)
                py = h - self.peaks[i] * (h - 10)
                p.fillRect(QRectF(i * bw + 2, py - 3, bw - 4, 2), QColor("#FFFFFF"))
        elif self.mode == 1:
            pts = list(self.samples)[-w:] if w <= len(self.samples) else list(self.samples)
            path = QPainterPath()
            step = w / max(1, len(pts) - 1)
            for i, v in enumerate(pts):
                y = h / 2 - v * h * 0.45
                (path.moveTo if i == 0 else path.lineTo)(i * step, y)
            p.setPen(QPen(QColor("#40FF60"), 1.5))
            p.drawPath(path)
        else:
            cx, cy = w / 2, h / 2
            for ring in range(14):
                t = self.phase + ring * 0.45
                band = self.bands[ring % len(self.bands)]
                radius = (ring + 1) * min(w, h) / 30 * (1 + band * 0.8)
                hue = int((self.phase * 40 + ring * 18) % 360)
                color = QColor.fromHsv(hue, 200, 255, 180)
                p.setPen(QPen(color, 2 + band * 4))
                p.setBrush(Qt.NoBrush)
                ox, oy = math.cos(t) * band * 20, math.sin(t * 1.3) * band * 20
                p.drawEllipse(QPointF(cx + ox, cy + oy), radius * 1.4, radius)


# ---- the window ----------------------------------------------------------------------------------------------------------

class FeatureBar(QWidget):
    chosen = Signal(int)

    def __init__(self, player):
        super().__init__()
        self.player = player
        self.current = 0
        self.hover = -1
        self.setFixedWidth(118)
        self.setMouseTracking(True)

    def item_rect(self, i):
        return QRectF(4, 10 + i * 34, self.width() - 8, 30)

    def mouseMoveEvent(self, event):
        hit = next((i for i in range(len(FEATURES)) if self.item_rect(i).contains(event.position())), -1)
        if hit != self.hover:
            self.hover = hit
            self.update()

    def leaveEvent(self, event):
        self.hover = -1
        self.update()

    def mousePressEvent(self, event):
        for i in range(len(FEATURES)):
            if self.item_rect(i).contains(event.position()):
                self.chosen.emit(i)

    def paintEvent(self, event):
        top, bottom, accent, text = SKINS[self.player.skin]
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), 0)
        g.setColorAt(0, QColor(bottom))
        g.setColorAt(1, QColor(top))
        p.fillRect(self.rect(), g)
        f = QFont("Tahoma")
        f.setPixelSize(11)
        f.setBold(True)
        p.setFont(f)
        for i, name in enumerate(FEATURES):
            r = self.item_rect(i)
            if i == self.current or i == self.hover:
                c = QColor(accent)
                c.setAlpha(150 if i == self.current else 70)
                p.setPen(Qt.NoPen)
                p.setBrush(c)
                p.drawRoundedRect(r, 6, 6)
            p.setPen(QColor(text))
            p.drawText(r.adjusted(8, 0, -4, 0), Qt.AlignVCenter | Qt.AlignLeft | Qt.TextWordWrap, name)


class TransportButton(QPushButton):
    def __init__(self, kind, size=28):
        super().__init__()
        self.kind = kind
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.setStyleSheet("QPushButton { border: none; background: transparent; }")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        g = QRadialGradient(r.center() - QPointF(r.width() * 0.15, r.height() * 0.2), r.width())
        hot = self.underMouse()
        g.setColorAt(0, QColor("#FFFFFF" if hot else "#E8F0FF"))
        g.setColorAt(1, QColor("#5A7EC0" if hot else "#3A5590"))
        p.setPen(QPen(QColor("#1A2A50"), 1))
        p.setBrush(g)
        p.drawEllipse(r)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#102040"))
        c = r.center()
        s = r.width() * 0.22
        k = self.kind
        if k == "play":
            path = QPainterPath()
            path.moveTo(c.x() - s * 0.7, c.y() - s)
            path.lineTo(c.x() + s, c.y())
            path.lineTo(c.x() - s * 0.7, c.y() + s)
            path.closeSubpath()
            p.drawPath(path)
        elif k == "pause":
            p.drawRect(QRectF(c.x() - s * 0.8, c.y() - s, s * 0.6, s * 2))
            p.drawRect(QRectF(c.x() + s * 0.2, c.y() - s, s * 0.6, s * 2))
        elif k == "stop":
            p.drawRect(QRectF(c.x() - s * 0.8, c.y() - s * 0.8, s * 1.6, s * 1.6))
        elif k in ("prev", "next"):
            d = 1 if k == "next" else -1
            for off in (-0.5, 0.4):
                path = QPainterPath()
                path.moveTo(c.x() + (off - 0.4) * s * 1.6 * d, c.y() - s * 0.8)
                path.lineTo(c.x() + (off + 0.4) * s * 1.6 * d, c.y())
                path.lineTo(c.x() + (off - 0.4) * s * 1.6 * d, c.y() + s * 0.8)
                path.closeSubpath()
                p.drawPath(path)
        elif k in ("mute", "unmute"):
            path = QPainterPath()
            path.moveTo(c.x() - s, c.y() - s * 0.4)
            path.lineTo(c.x() - s * 0.4, c.y() - s * 0.4)
            path.lineTo(c.x() + s * 0.3, c.y() - s)
            path.lineTo(c.x() + s * 0.3, c.y() + s)
            path.lineTo(c.x() - s * 0.4, c.y() + s * 0.4)
            path.lineTo(c.x() - s, c.y() + s * 0.4)
            path.closeSubpath()
            p.drawPath(path)
            if k == "mute":
                p.setPen(QPen(QColor("#C00000"), 2))
                p.drawLine(QPointF(c.x() + s * 0.5, c.y() - s * 0.6), QPointF(c.x() + s * 1.1, c.y() + s * 0.6))


class MediaPlayerWindow(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        state = load_json(STATE_FILE, {})
        self.skin = state.get("skin", "Windows XP") if state.get("skin") in SKINS else "Windows XP"
        self.volume = float(state.get("volume", 0.8))
        self.muted = False
        self.shuffle = bool(state.get("shuffle", False))
        self.repeat = bool(state.get("repeat", False))
        self.playlist = []
        self.index = -1
        self.library = []
        self.player = QMediaPlayer(self)
        self.output = QAudioOutput(self)
        self.player.setAudioOutput(self.output)
        self.buffers = QAudioBufferOutput(self)
        self.player.setAudioBufferOutput(self.buffers)
        self._apply_volume()
        self.setObjectName("wmp")
        self.setAttribute(Qt.WA_StyledBackground, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.menu = QMenuBar()
        self.menu.triggered.connect(lambda _a: sound.play("menu"))
        root.addWidget(self.menu)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.features = FeatureBar(self)
        self.features.chosen.connect(self.show_feature)
        body.addWidget(self.features)
        self.pages = QStackedWidget()
        body.addWidget(self.pages, 1)
        root.addLayout(body, 1)
        root.addWidget(self._transport())
        self._now_playing_page()
        self._message_page("Media Guide", self._guide_text)
        self._message_page("Copy from CD", lambda: "No audio CD was found in drive D:.\n\nInsert an audio CD, "
                                                   "and then click Copy from CD.")
        self._library_page()
        self._radio_page()
        self._message_page("Copy to CD or Device", lambda: "No CD recorder or portable device was found.\n\n"
                                                           "Connect a portable device to copy music to it.")
        self._skin_page()
        self._menus()
        self.buffers.audioBufferReceived.connect(self.vis.feed)
        self.player.positionChanged.connect(self._position)
        self.player.durationChanged.connect(lambda d: self.seek.setRange(0, max(0, d)))
        self.player.mediaStatusChanged.connect(self._status_changed)
        self.player.playbackStateChanged.connect(self._state_changed)
        self.player.errorOccurred.connect(lambda _e, msg: self.status.setText("Ready" if not msg else
                                                                              "Windows Media Player cannot play the file."))
        ensure_sample_music()
        self.refresh_library()
        self.restyle()
        self.show_feature(0)

    # ---- layout pieces ---------------------------------------------------------------------------------------------
    def _transport(self):
        bar = QWidget()
        bar.setObjectName("transport")
        v = QVBoxLayout(bar)
        v.setContentsMargins(10, 4, 10, 6)
        v.setSpacing(3)
        top = QHBoxLayout()
        self.status = QLabel("Ready")
        self.status.setObjectName("wmptext")
        self.clock = QLabel("00:00")
        self.clock.setObjectName("wmptext")
        top.addWidget(self.status, 1)
        top.addWidget(self.clock)
        v.addLayout(top)
        self.seek = QSlider(Qt.Horizontal)
        self.seek.sliderMoved.connect(self.player.setPosition)
        v.addWidget(self.seek)
        row = QHBoxLayout()
        row.setSpacing(4)
        self.play_btn = TransportButton("play", 36)
        self.play_btn.clicked.connect(self.toggle_play)
        stop = TransportButton("stop")
        stop.clicked.connect(self.stop)
        prev, nxt = TransportButton("prev"), TransportButton("next")
        prev.clicked.connect(self.previous)
        nxt.clicked.connect(self.next)
        self.mute_btn = TransportButton("unmute", 24)
        self.mute_btn.clicked.connect(self.toggle_mute)
        self.vol = QSlider(Qt.Horizontal)
        self.vol.setRange(0, 100)
        self.vol.setValue(int(self.volume * 100))
        self.vol.setFixedWidth(90)
        self.vol.valueChanged.connect(self._set_volume)
        for wdg in (self.play_btn, stop, prev, nxt):
            row.addWidget(wdg)
        row.addSpacing(10)
        row.addWidget(self.mute_btn)
        row.addWidget(self.vol)
        row.addStretch()
        self.mode_label = QLabel("")
        self.mode_label.setObjectName("wmptext")
        row.addWidget(self.mode_label)
        v.addLayout(row)
        return bar

    def _now_playing_page(self):
        page = QWidget()
        h = QHBoxLayout(page)
        h.setContentsMargins(8, 8, 8, 8)
        left = QVBoxLayout()
        head = QHBoxLayout()
        self.vis_name = QLabel(VISUALIZATIONS[0])
        self.vis_name.setObjectName("wmptext")
        pv, nv = QPushButton("<"), QPushButton(">")
        for b, d in ((pv, -1), (nv, 1)):
            b.setFixedSize(22, 18)
            b.clicked.connect(lambda _c=False, d=d: self.set_visualization(self.vis.mode + d))
        head.addWidget(pv)
        head.addWidget(nv)
        head.addWidget(self.vis_name, 1)
        left.addLayout(head)
        self.vis = Visualizer(self)
        left.addWidget(self.vis, 1)
        self.now_title = QLabel("")
        self.now_title.setObjectName("wmptitle")
        left.addWidget(self.now_title)
        h.addLayout(left, 1)
        right = QVBoxLayout()
        lab = QLabel("Now Playing")
        lab.setObjectName("wmptext")
        right.addWidget(lab)
        self.queue = QListWidget()
        self.queue.setFixedWidth(190)
        self.queue.itemDoubleClicked.connect(lambda item: self.play_index(self.queue.row(item)))
        right.addWidget(self.queue, 1)
        h.addLayout(right)
        self.pages.addWidget(page)

    def _message_page(self, title, text_fn):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(24, 20, 24, 20)
        head = QLabel(title)
        head.setObjectName("wmphead")
        v.addWidget(head)
        body = QLabel()
        body.setObjectName("wmptext")
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        body.setTextFormat(Qt.RichText)
        v.addWidget(body, 1)
        page.refresh = lambda: body.setText(text_fn().replace("\n", "<br>"))
        self.pages.addWidget(page)

    def _guide_text(self):
        if not network.is_connected():
            return ("<b>The page cannot be displayed.</b>\n\nThe Media Guide needs an Internet connection. "
                    "Connect to the Internet, and then try again.")
        return ("<b>WindowsMedia.com</b>  —  Your guide to music, movies and more\n\n"
                "<b>New this week:</b> Download the latest music videos and movie trailers, in crisp "
                "Windows Media Video 8.\n\n"
                "<b>Radio:</b> Over 3,000 Internet radio stations are a click away in the Radio Tuner.\n\n"
                "<b>Tip:</b> Turn your CDs into a digital music library with Copy from CD. Windows Media Audio "
                "gives you CD quality in half the space of an MP3.")

    def _library_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(8, 8, 8, 8)
        head = QHBoxLayout()
        lab = QLabel("Media Library")
        lab.setObjectName("wmphead")
        head.addWidget(lab, 1)
        add = QPushButton("Search for media files")
        add.clicked.connect(self.refresh_library)
        play_all = QPushButton("Play all")
        play_all.clicked.connect(lambda: self.set_playlist(self._visible_tracks(), 0))
        head.addWidget(play_all)
        head.addWidget(add)
        v.addLayout(head)
        split = QHBoxLayout()
        self.lib_tree = QTreeWidget()
        self.lib_tree.setHeaderHidden(True)
        self.lib_tree.setFixedWidth(170)
        self.lib_tree.currentItemChanged.connect(lambda *_: self._fill_tracks())
        split.addWidget(self.lib_tree)
        self.tracks = QTreeWidget()
        self.tracks.setHeaderLabels(["Title", "Artist", "Album", "Length"])
        self.tracks.setRootIsDecorated(False)
        self.tracks.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tracks.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tracks.itemDoubleClicked.connect(self._library_play)
        split.addWidget(self.tracks, 1)
        v.addLayout(split, 1)
        self.pages.addWidget(page)

    def _radio_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(16, 12, 16, 12)
        head = QLabel("Radio Tuner  —  Featured Stations")
        head.setObjectName("wmphead")
        v.addWidget(head)
        self.stations = QTreeWidget()
        self.stations.setHeaderLabels(["Station", "Genre", "Speed"])
        self.stations.setRootIsDecorated(False)
        self.stations.header().setSectionResizeMode(0, QHeaderView.Stretch)
        for st in STATIONS:
            self.stations.addTopLevelItem(QTreeWidgetItem(list(st)))
        self.stations.itemDoubleClicked.connect(self._tune)
        v.addWidget(self.stations, 1)
        self.radio_note = QLabel("Double-click a station to listen.")
        self.radio_note.setObjectName("wmptext")
        v.addWidget(self.radio_note)
        self.pages.addWidget(page)

    def _tune(self, item):
        name = item.text(0)
        if not network.is_connected():
            self.radio_note.setText("You must be connected to the Internet to listen to radio stations.")
            return
        self.radio_note.setText(f"Connecting to {name}...")
        self.status.setText("Connecting to media...")

        def busy():
            if isValid(self):
                self.radio_note.setText(f"{name} is not available right now. The server is too busy "
                                        "(over 2,000 listeners). Please try another station.")
                self.status.setText("Ready")
        QTimer.singleShot(3500, busy)

    def _skin_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(16, 12, 16, 12)
        head = QLabel("Skin Chooser")
        head.setObjectName("wmphead")
        v.addWidget(head)
        self.skin_list = QListWidget()
        for name in SKINS:
            self.skin_list.addItem(name)
        self.skin_list.setFixedWidth(180)
        row = QHBoxLayout()
        row.addWidget(self.skin_list)
        self.skin_preview = QLabel()
        self.skin_preview.setFixedSize(220, 140)
        row.addWidget(self.skin_preview)
        row.addStretch()
        v.addLayout(row)
        apply = QPushButton("Apply Skin")
        apply.setFixedWidth(100)
        apply.clicked.connect(lambda: self.set_skin(self.skin_list.currentItem().text())
                              if self.skin_list.currentItem() else None)
        v.addWidget(apply)
        v.addStretch()
        self.skin_list.currentTextChanged.connect(self._preview_skin)
        self.pages.addWidget(page)

    def _preview_skin(self, name):
        if name not in SKINS:
            return
        top, bottom, accent, text = SKINS[name]
        pm = QPixmap(220, 140)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 0, 140)
        g.setColorAt(0, QColor(top))
        g.setColorAt(1, QColor(bottom))
        p.fillRect(pm.rect(), g)
        p.fillRect(QRectF(50, 12, 158, 90), QColor("black"))
        for i in range(10):
            hgt = random.Random(i).uniform(10, 80)
            p.fillRect(QRectF(56 + i * 15, 100 - hgt, 10, hgt), QColor(accent))
        p.setBrush(QColor(accent))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(12, 108, 26, 26))
        p.end()
        self.skin_preview.setPixmap(pm)

    def _menus(self):
        m = self.menu
        f = m.addMenu("&File")
        f.addAction("&Open...", self.open_dialog, QKeySequence("Ctrl+O"))
        f.addAction("Add to Media &Library", self.refresh_library)
        f.addSeparator()
        f.addAction("E&xit", lambda: self.frame.request_close())
        v = m.addMenu("&View")
        v.addAction("&Now Playing", lambda: self.show_feature(0))
        v.addAction("Media &Library", lambda: self.show_feature(3))
        vis = v.addMenu("&Visualizations")
        group = QActionGroup(self)
        self.vis_actions = []
        for i, name in enumerate(VISUALIZATIONS):
            act = QAction(name, self, checkable=True, checked=i == 0)
            act.triggered.connect(lambda _c=False, i=i: self.set_visualization(i))
            group.addAction(act)
            vis.addAction(act)
            self.vis_actions.append(act)
        play = m.addMenu("&Play")
        play.addAction("&Play/Pause", self.toggle_play, QKeySequence("Ctrl+P"))
        play.addAction("&Stop", self.stop, QKeySequence("Ctrl+S"))
        play.addSeparator()
        play.addAction("Pre&vious", self.previous, QKeySequence("Ctrl+B"))
        play.addAction("&Next", self.next, QKeySequence("Ctrl+F"))
        play.addSeparator()
        self.shuffle_act = QAction("S&huffle", self, checkable=True, checked=self.shuffle)
        self.shuffle_act.setShortcut(QKeySequence("Ctrl+H"))
        self.shuffle_act.toggled.connect(lambda on: self._set_mode(shuffle=on))
        self.repeat_act = QAction("&Repeat", self, checkable=True, checked=self.repeat)
        self.repeat_act.setShortcut(QKeySequence("Ctrl+T"))
        self.repeat_act.toggled.connect(lambda on: self._set_mode(repeat=on))
        play.addAction(self.shuffle_act)
        play.addAction(self.repeat_act)
        play.addSeparator()
        play.addAction("&Mute", self.toggle_mute, QKeySequence("F8"))
        tools = m.addMenu("&Tools")
        tools.addAction("&Search for Media Files...", self.refresh_library, QKeySequence("F3"))
        tools.addAction("&Skin Chooser", lambda: self.show_feature(6))
        m.addMenu("&Help").addAction("&About Windows Media Player", self.about)
        self._update_mode_label()

    # ---- look ------------------------------------------------------------------------------------------------------
    def restyle(self):
        top, bottom, accent, text = SKINS[self.skin]
        self.setStyleSheet(MENU_STYLE + f"""
            QWidget#wmp {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {top}, stop:1 {bottom}); }}
            QStackedWidget > QWidget {{ background: transparent; }}
            QWidget#transport {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {bottom}, stop:1 {top});
                                 border-top: 1px solid {accent}; }}
            QLabel#wmptext {{ color: {text}; font-family: Tahoma; font-size: 11px; }}
            QLabel#wmptitle {{ color: {text}; font-family: Tahoma; font-size: 13px; font-weight: bold; }}
            QLabel#wmphead {{ color: {text}; font-family: Trebuchet MS; font-size: 17px; font-weight: bold; }}
            QListWidget, QTreeWidget {{ background: #0B1530; color: #E0E8FF; border: 1px solid {accent};
                                        font-family: Tahoma; font-size: 11px; }}
            QListWidget::item:selected, QTreeWidget::item:selected {{ background: {accent}; color: black; }}
            QHeaderView::section {{ background: {bottom}; color: {text}; border: none; padding: 2px 4px;
                                    font-family: Tahoma; font-size: 11px; }}
            QPushButton {{ font-family: Tahoma; font-size: 11px; }}
            QSlider::groove:horizontal {{ height: 4px; background: #0A1430; border: 1px solid {accent}; }}
            QSlider::handle:horizontal {{ background: {accent}; width: 10px; margin: -5px 0; border-radius: 5px; }}
        """)
        self.features.update()
        self._preview_skin(self.skin)

    def set_skin(self, name):
        self.skin = name
        self._save_state()
        self.restyle()

    def show_feature(self, index):
        self.features.current = index
        self.features.update()
        self.pages.setCurrentIndex(index)
        page = self.pages.currentWidget()
        if hasattr(page, "refresh"):
            page.refresh()

    def set_visualization(self, i):
        i %= len(VISUALIZATIONS)
        self.vis.mode = i
        self.vis_name.setText(VISUALIZATIONS[i])
        self.vis_actions[i].setChecked(True)

    # ---- library ----------------------------------------------------------------------------------------------------
    def refresh_library(self):
        self.library = scan_library()
        self.lib_tree.clear()
        all_item = QTreeWidgetItem(["All Audio"])
        all_item.setData(0, Qt.UserRole, ("all", None))
        self.lib_tree.addTopLevelItem(all_item)
        for key, label in (("artist", "Artist"), ("album", "Album")):
            parent = QTreeWidgetItem([label])
            parent.setData(0, Qt.UserRole, (key, None))
            for value in sorted({getattr(t, key) for t in self.library}, key=str.lower):
                child = QTreeWidgetItem([value])
                child.setData(0, Qt.UserRole, (key, value))
                parent.addChild(child)
            self.lib_tree.addTopLevelItem(parent)
        self.lib_tree.setCurrentItem(all_item)
        self._fill_tracks()

    def _visible_tracks(self):
        item = self.lib_tree.currentItem()
        key, value = item.data(0, Qt.UserRole) if item else ("all", None)
        if key == "all" or value is None:
            return list(self.library)
        return [t for t in self.library if getattr(t, key) == value]

    def _fill_tracks(self):
        self.tracks.clear()
        for t in self._visible_tracks():
            item = QTreeWidgetItem([t.title, t.artist, t.album, fmt_time(t.length, True)])
            item.setData(0, Qt.UserRole, t)
            self.tracks.addTopLevelItem(item)

    def _library_play(self, item):
        visible = self._visible_tracks()
        t = item.data(0, Qt.UserRole)
        self.set_playlist(visible, visible.index(t) if t in visible else 0)

    # ---- playing ---------------------------------------------------------------------------------------------------
    def set_playlist(self, tracks, start=0):
        self.playlist = list(tracks)
        self.queue.clear()
        for t in self.playlist:
            self.queue.addItem(QListWidgetItem(f"{t.title}  ({fmt_time(t.length, True)})"))
        if self.playlist:
            self.play_index(start)
            self.show_feature(0)

    def add_and_play(self, path):
        path = Path(path)
        existing = next((i for i, t in enumerate(self.playlist) if t.path == path), None)
        if existing is None:
            self.playlist.append(Track(path))
            t = self.playlist[-1]
            self.queue.addItem(QListWidgetItem(f"{t.title}  ({fmt_time(t.length, True)})"))
            existing = len(self.playlist) - 1
        self.play_index(existing)
        self.show_feature(0)

    def play_index(self, i):
        if not (0 <= i < len(self.playlist)):
            return
        self.index = i
        t = self.playlist[i]
        self.queue.setCurrentRow(i)
        self.player.setSource(QUrl.fromLocalFile(str(t.path)))
        self._apply_volume()
        self.player.play()
        self.now_title.setText(f"{t.title}  —  {t.artist}" if t.artist != "Unknown Artist" else t.title)
        if self.frame is not None:
            self.frame.set_title(f"{t.title} - Windows Media Player")

    def toggle_play(self):
        state = self.player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif self.index < 0:
            if not self.playlist and self.library:
                self.set_playlist(self.library, 0)
            elif self.playlist:
                self.play_index(0)
        else:
            self._apply_volume()
            self.player.play()

    def stop(self):
        self.player.stop()

    def next(self):
        if not self.playlist:
            return
        if self.shuffle and len(self.playlist) > 1:
            choices = [i for i in range(len(self.playlist)) if i != self.index]
            self.play_index(random.choice(choices))
        elif self.index + 1 < len(self.playlist):
            self.play_index(self.index + 1)
        elif self.repeat:
            self.play_index(0)
        else:
            self.stop()

    def previous(self):
        if self.player.position() > 3000:
            self.player.setPosition(0)
        elif self.playlist:
            self.play_index(max(0, self.index - 1))

    def _status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.next()

    def _state_changed(self, state):
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.play_btn.kind = "pause" if playing else "play"
        self.play_btn.update()
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.status.setText("Stopped" if self.index >= 0 else "Ready")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.status.setText("Paused")
        elif 0 <= self.index < len(self.playlist):
            self.status.setText(f"Playing: {self.playlist[self.index].title}")

    def _position(self, ms):
        if not self.seek.isSliderDown():
            self.seek.setValue(ms)
        self.clock.setText(fmt_time(ms / 1000))

    def _apply_volume(self):
        self.output.setVolume(0.0 if (self.muted or sound.is_muted()) else self.volume)

    def _set_volume(self, value):
        self.volume = value / 100
        self._apply_volume()
        self._save_state()

    def toggle_mute(self):
        self.muted = not self.muted
        self.mute_btn.kind = "mute" if self.muted else "unmute"
        self.mute_btn.update()
        self._apply_volume()

    def _set_mode(self, shuffle=None, repeat=None):
        if shuffle is not None:
            self.shuffle = shuffle
        if repeat is not None:
            self.repeat = repeat
        self._update_mode_label()
        self._save_state()

    def _update_mode_label(self):
        bits = [name for name, on in (("Shuffle", self.shuffle), ("Repeat", self.repeat)) if on]
        self.mode_label.setText("  ".join(bits))

    def _save_state(self):
        state = load_json(STATE_FILE, {})
        state.update(skin=self.skin, volume=round(self.volume, 2), shuffle=self.shuffle, repeat=self.repeat)
        save_json(STATE_FILE, state)

    def open_dialog(self):
        from .paint import _dialog
        from PySide6.QtWidgets import QComboBox, QGridLayout
        from PySide6.QtWidgets import QApplication, QStyle
        body = QWidget()
        g = QGridLayout(body)
        g.addWidget(QLabel("Look in:"), 0, 0)
        where = QComboBox()
        for label, folder in library_folders():
            where.addItem(QApplication.style().standardIcon(QStyle.SP_DirIcon), label, str(folder))
        g.addWidget(where, 0, 1)
        files = QListWidget()
        files.setStyleSheet("background: white; color: black;")
        files.setMinimumSize(340, 200)
        g.addWidget(files, 1, 0, 1, 2)

        def fill():
            files.clear()
            folder = Path(where.currentData())
            if folder.is_dir():
                for p in sorted(folder.rglob("*")):
                    if p.suffix.lower() in AUDIO_EXTS:
                        item = QListWidgetItem(str(p.relative_to(folder)))
                        item.setData(Qt.UserRole, str(p))
                        files.addItem(item)
        where.currentIndexChanged.connect(fill)
        fill()

        def accept():
            item = files.currentItem()
            if item is None:
                return False
            self.add_and_play(item.data(Qt.UserRole))
        win = _dialog(self.desktop, "Open", body, accept)
        win.icon = wmp_icon()
        files.itemDoubleClicked.connect(lambda _i: accept() is not False and self.desktop.close_window(win))

    def about(self):
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, "About Windows Media Player", "Windows Media Player\nVersion 8.00.00.4477", "info")

    def closeEvent(self, event):
        self.player.stop()
        self.vis.timer.stop()
        event.accept()


_open = {}


def open_wmp(desktop, path=None):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = MediaPlayerWindow(desktop)
        win = XPWindow(desktop, "Windows Media Player", body, wmp_icon(), (700, 500))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    if path is not None:
        win.content.add_and_play(path)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.player.stop()
