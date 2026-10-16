"""ClaudeAmp: a Winamp 2 lookalike. It really whips the llama's ass.

The classic skinned main window (its own title bar, the green LCD time, a spectrum analyser / oscilloscope that
moves to the real audio, the scrolling song title, kbps / kHz / stereo read from the stream, volume, seek, the
transport buttons, shuffle and repeat), the playlist editor docked under it, and a video window that opens for
videos (AVI, MPEG, WMV, MOV, MP4, RealMedia...). On start-up it plays the Winamp intro, then whatever it was
asked to play. Keys are Winamp's: Z X C V B, L to open a file, arrows to seek and change the volume, Ctrl+D for
double size, Alt+E for the playlist, Alt+V for the video window."""
import math
import random
from collections import deque
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import (QAction, QActionGroup, QColor, QFont, QFontMetricsF, QIcon, QImage, QLinearGradient,
                           QPainter, QPainterPath, QPen, QPixmap, QPolygonF)
from PySide6.QtMultimedia import QAudioBufferOutput, QAudioOutput, QMediaPlayer, QVideoSink
from PySide6.QtWidgets import QMenu, QVBoxLayout, QWidget
from shiboken6 import isValid

from .. import sound
from ..paths import DATA, SOUNDS
from ..wm import XPWindow
from .people import load_json, save_json

STATE_FILE = DATA / "claudeamp.json"
INTRO = SOUNDS / "winamp_intro.mp3"
INTRO_TITLE = "DJ Mike Llama - Llama Whippin' Intro"
AUDIO_EXTS = {".mp3", ".wav", ".wma", ".m4a", ".ogg", ".flac", ".aac", ".mp2"}
VIDEO_EXTS = {".avi", ".mpg", ".mpeg", ".mp4", ".m4v", ".wmv", ".asf", ".mov", ".qt", ".mkv", ".rm", ".ram", ".rmvb",
              ".vob", ".flv", ".3gp", ".webm", ".divx"}
MEDIA_EXTS = AUDIO_EXTS | VIDEO_EXTS
MAIN = QSize(275, 116)
PL_H = 174
TB = 14                                         # the skinned title bars

GREEN = QColor("#00E200")
DIM_GREEN = QColor("#1C5A1C")
LCD = QColor("#000000")
MENU_STYLE = ("QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }"
              " QMenu::item { padding: 4px 24px 4px 20px; } QMenu::item:selected { background: #316AC5; color: white; }"
              " QMenu::item:disabled { color: #ACA899; } QMenu::separator { height: 1px; background: #ACA899;"
              " margin: 3px 2px; }")


def amp_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, 0, 32)
    g.setColorAt(0, QColor("#4A4A62"))
    g.setColorAt(1, QColor("#14141C"))
    p.setPen(QPen(QColor("#0A0A10"), 1))
    p.setBrush(g)
    p.drawEllipse(QRectF(1.5, 1.5, 29, 29))
    bolt = QPolygonF([QPointF(19, 3), QPointF(8, 18), QPointF(15, 18), QPointF(11, 29), QPointF(24, 12),
                      QPointF(17, 12), QPointF(21, 3)])
    bg = QLinearGradient(0, 3, 0, 29)
    bg.setColorAt(0, QColor("#FFF6A0"))
    bg.setColorAt(0.5, QColor("#FFC21A"))
    bg.setColorAt(1, QColor("#E05A00"))
    p.setPen(QPen(QColor("#7A3000"), 1))
    p.setBrush(bg)
    p.drawPolygon(bolt)
    p.end()
    return QIcon(pm)


def fmt(seconds):
    seconds = max(0, int(seconds or 0))
    return f"{seconds // 60}:{seconds % 60:02d}"


def _font(px, bold=False):
    f = QFont("Tahoma")
    f.setPixelSize(px)
    f.setBold(bold)
    f.setStyleStrategy(QFont.NoAntialias)
    return f


# ---- the playlist ----------------------------------------------------------------------------------------------------

class Entry:
    __slots__ = ("path", "title", "length", "video")

    def __init__(self, path, title=None, length=None):
        self.path = Path(path)
        self.video = self.path.suffix.lower() in VIDEO_EXTS
        self.title = title or self._title()
        self.length = self._length() if length is None else length

    def _title(self):
        if self.path.suffix.lower() == ".mp3":
            from .wmp import _id3
            tags = _id3(self.path)
            if tags.get("TIT2"):
                return f"{tags['TPE1']} - {tags['TIT2']}" if tags.get("TPE1") else tags["TIT2"]
        stem = self.path.stem.replace("_", " ").strip()
        return " ".join(stem.split()) or self.path.name

    def _length(self):
        try:
            if self.video:
                from claudetv.library import running_time
                return float(running_time(self.path) or 0)
            from .wmp import _length
            return float(_length(self.path) or 0)
        except Exception:
            return 0.0


# ---- the spectrum analyser -------------------------------------------------------------------------------------

class Analyser:
    """WMP's Goertzel bands, made Winamp-sized: 19 bars over 80 Hz .. 8 kHz, with falling peaks."""
    BARS = 19

    def __init__(self):
        self.samples = deque([0.0] * 1024, maxlen=1024)
        self.bands = [0.0] * self.BARS
        self.peaks = [0.0] * self.BARS
        self.rate = 44100
        self.channels = 2
        n, rate = 256, 11025
        self.coeffs = []
        for i in range(self.BARS):
            freq = 80 * (5000 / 80) ** (i / (self.BARS - 1))
            k = max(1, n * freq / rate)
            self.coeffs.append(2 * math.cos(2 * math.pi * k / n))

    def feed(self, buf):
        fmt_ = buf.format()
        ch = max(1, fmt_.channelCount())
        self.rate, self.channels = fmt_.sampleRate() or self.rate, ch
        try:
            data = buf.constData()
            name = fmt_.sampleFormat().name
            if name == "Float":
                vals = data.cast("f")
            elif name == "Int16":
                vals = [v / 32768 for v in data.cast("h")]
            else:
                return
        except (TypeError, ValueError):
            return
        mono = [sum(vals[i:i + ch]) / ch for i in range(0, len(vals) - ch + 1, ch)]
        step = max(1, round(self.rate / 22050))
        self.samples.extend(mono[::step])

    def tick(self, playing):
        if not playing:
            self.samples.extend([0.0] * 96)
        recent = list(self.samples)[-512:]
        for i, c in enumerate(self.coeffs):
            s1 = s2 = 0.0
            for x in recent[::2]:
                s1, s2 = x + c * s1 - s2, s1
            power = s1 * s1 + s2 * s2 - c * s1 * s2
            value = min(1.0, math.log10(1 + power) / 1.5)
            self.bands[i] = max(value, self.bands[i] - 0.09)
            self.peaks[i] = max(self.bands[i], self.peaks[i] - 0.025)


# ---- drawing helpers -------------------------------------------------------------------------------------------------

SEGMENTS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
            "7": "abc", "8": "abcdefg", "9": "abcdfg", "-": "g", " ": ""}


def draw_digit(p, x, y, ch, color, dim=None):
    """A 9x13 seven-segment digit, like the LCD numbers in Winamp's skin."""
    t = 1.6
    segs = {"a": QRectF(x + 1.8, y, 5.4, t), "g": QRectF(x + 1.8, y + 5.7, 5.4, t),
            "d": QRectF(x + 1.8, y + 11.4, 5.4, t),
            "f": QRectF(x + 0.2, y + 1.2, t, 4.8), "b": QRectF(x + 7.2, y + 1.2, t, 4.8),
            "e": QRectF(x + 0.2, y + 7, t, 4.8), "c": QRectF(x + 7.2, y + 7, t, 4.8)}
    on = SEGMENTS.get(ch, "")
    for name, r in segs.items():
        if name in on:
            p.fillRect(r, color)
        elif dim is not None:
            p.fillRect(r, dim)


def bevel(p, r, down=False, face="#B8B8C8", light="#E8E8F4", dark="#4A4A5E"):
    p.fillRect(r, QColor(face if not down else "#8C8CA0"))
    p.setPen(QPen(QColor(dark if down else light), 1))
    p.drawLine(QPointF(r.left(), r.top() + 0.5), QPointF(r.right(), r.top() + 0.5))
    p.drawLine(QPointF(r.left() + 0.5, r.top()), QPointF(r.left() + 0.5, r.bottom()))
    p.setPen(QPen(QColor(light if down else dark), 1))
    p.drawLine(QPointF(r.left(), r.bottom() - 0.5), QPointF(r.right(), r.bottom() - 0.5))
    p.drawLine(QPointF(r.right() - 0.5, r.top()), QPointF(r.right() - 0.5, r.bottom()))


def title_bar(p, width, text, active, buttons=("min", "close")):
    """Winamp's ribbed title bar: grooves either side of the name, brighter when the window is active."""
    g = QLinearGradient(0, 0, 0, TB)
    g.setColorAt(0, QColor("#4E4E6A" if active else "#3A3A4C"))
    g.setColorAt(1, QColor("#26263A" if active else "#202030"))
    p.fillRect(QRectF(0, 0, width, TB), g)
    p.setFont(_font(8, True))
    fm = QFontMetricsF(p.font())
    tw = fm.horizontalAdvance(text) + 10
    left, right = (width - tw) / 2, (width + tw) / 2
    groove = QColor("#D8C27A" if active else "#7A7A8C")
    shade = QColor("#5A4A1A" if active else "#2A2A36")
    for y in (4, 7, 10):
        for x0, x1 in ((20, left), (right, width - 34)):
            if x1 > x0:
                p.fillRect(QRectF(x0, y, x1 - x0, 1), groove)
                p.fillRect(QRectF(x0, y + 1, x1 - x0, 1), shade)
    p.setPen(QColor("#F0F0F8" if active else "#A0A0B0"))
    p.drawText(QRectF(left, 0, tw, TB), Qt.AlignCenter, text)
    # the menu icon (left) and the window buttons (right)
    bevel(p, QRectF(6, 3, 9, 9))
    p.fillRect(QRectF(8, 6, 5, 1), QColor("#202030"))
    p.fillRect(QRectF(8, 8, 5, 1), QColor("#202030"))
    rects = {}
    x = width - 11
    for kind in reversed(buttons):
        r = QRectF(x, 3, 9, 9)
        bevel(p, r)
        p.setPen(QPen(QColor("#202030"), 1.2))
        if kind == "close":
            p.drawLine(QPointF(r.left() + 2, r.top() + 2), QPointF(r.right() - 2, r.bottom() - 2))
            p.drawLine(QPointF(r.right() - 2, r.top() + 2), QPointF(r.left() + 2, r.bottom() - 2))
        elif kind == "min":
            p.fillRect(QRectF(r.left() + 2, r.bottom() - 3, 5, 1.4), QColor("#202030"))
        rects[kind] = r
        x -= 10
    return rects


# ---- the skinned window frame --------------------------------------------------------------------------------------

class AmpFrame(XPWindow):
    """An XPWindow without the Luna frame: the content draws its own Winamp title bar, and dragging it moves us."""
    skinned = True

    def __init__(self, desktop, title, content, icon, resizable=False):
        super().__init__(desktop, title, content, icon, (content.width(), content.height()), buttons=())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.resizable = resizable
        self.setMinimumSize(MAIN.width(), 80)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#202030"))

    def drag_height(self):
        return TB * getattr(self.content, "scale", 1)

    def mousePressEvent(self, event):
        self.desktop.activate(self)
        if event.button() != Qt.LeftButton:
            return
        pos = event.position().toPoint()
        edges = self._edges_at(pos)
        if edges:
            self._resize = (edges, event.globalPosition().toPoint(), self.geometry())
        elif not self.maximized:
            self._drag = pos

    def mouseDoubleClickEvent(self, event):
        if self.resizable:
            self.toggle_maximize()


# ---- the main window ---------------------------------------------------------------------------------------------

R = {"menu": QRectF(6, 3, 9, 9), "min": QRectF(254, 3, 9, 9), "close": QRectF(264, 3, 9, 9),
     "clutter": QRectF(10, 22, 8, 40), "display": QRectF(20, 21, 86, 42), "time": QRectF(36, 25, 66, 15),
     "vis": QRectF(24, 43, 76, 16), "title": QRectF(111, 24, 155, 11),
     "vol": QRectF(107, 57, 68, 13), "bal": QRectF(177, 57, 38, 13), "eq": QRectF(219, 58, 23, 12),
     "pl": QRectF(242, 58, 23, 12), "seek": QRectF(16, 72, 248, 10),
     "prev": QRectF(16, 88, 23, 18), "play": QRectF(39, 88, 23, 18), "pause": QRectF(62, 88, 23, 18),
     "stop": QRectF(85, 88, 23, 18), "next": QRectF(108, 88, 22, 18), "eject": QRectF(136, 89, 22, 16),
     "shuffle": QRectF(164, 89, 46, 15), "repeat": QRectF(211, 89, 28, 15), "logo": QRectF(250, 89, 17, 17)}
BUTTONS = ("menu", "min", "close", "eq", "pl", "prev", "play", "pause", "stop", "next", "eject", "shuffle",
           "repeat", "logo")


class MainPanel(QWidget):
    def __init__(self, amp):
        super().__init__(amp)
        self.amp = amp
        self.pressed = None
        self.dragging = None                    # "vol" | "bal" | "seek"
        self.seek_preview = None
        self.message = None                     # (text, until tick) shown in the title box while dragging
        self.scroll = 0.0
        self.title_pm = None
        self.title_text = None
        self.setMouseTracking(True)

    @property
    def s(self):
        return self.amp.scale

    def logical(self, event):
        pos = event.position()
        return QPointF(pos.x() / self.s, pos.y() / self.s)

    def hit(self, pt):
        for name in BUTTONS + ("vol", "bal", "seek", "time", "vis", "clutter", "title"):
            if R[name].contains(pt):
                return name
        return None

    # ---- mouse -------------------------------------------------------------------------------------------------
    def mousePressEvent(self, event):
        pt = self.logical(event)
        name = self.hit(pt)
        if event.button() == Qt.RightButton:
            self.amp.main_menu(event.globalPosition().toPoint())
            return
        if event.button() != Qt.LeftButton:
            return
        if name == "menu":
            self.amp.main_menu(self.mapToGlobal(QPointF(R["menu"].left() * self.s,
                                                        R["menu"].bottom() * self.s).toPoint()))
            return
        if name in BUTTONS:
            self.pressed = name
            self.update()
            return
        if name in ("vol", "bal", "seek"):
            self.dragging = name
            self._drag_to(pt)
            return
        if name == "time":
            self.amp.remaining = not self.amp.remaining
            self.amp.save_state()
            return
        if name == "vis":
            self.amp.set_vis((self.amp.vis_mode + 1) % 3)
            return
        if name == "clutter":
            letter = "OAIDV"[min(4, int((pt.y() - R["clutter"].top()) / 8))]
            if letter == "D":
                self.amp.set_double(not self.amp.double)
            elif letter == "I":
                self.amp.file_info()
            elif letter == "O":
                self.amp.main_menu(event.globalPosition().toPoint())
            return
        event.ignore()                                   # the title bar and the body move the window

    def mouseMoveEvent(self, event):
        if self.dragging:
            self._drag_to(self.logical(event))
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        pt = self.logical(event)
        if self.pressed:
            name, self.pressed = self.pressed, None
            self.update()
            if R[name].contains(pt):
                self.amp.button(name)
            return
        if self.dragging == "seek" and self.seek_preview is not None:
            self.amp.player.setPosition(int(self.seek_preview))
        if self.dragging:
            self.dragging = None
            self.seek_preview = None
            self.message = None
            return
        event.ignore()

    def mouseDoubleClickEvent(self, event):
        if self.hit(self.logical(event)) is None and self.logical(event).y() < TB:
            self.amp.set_double(not self.amp.double)       # Winamp: double-click the title bar
            return
        event.ignore()

    def wheelEvent(self, event):
        self.amp.set_volume(self.amp.volume + (0.04 if event.angleDelta().y() > 0 else -0.04))

    def _drag_to(self, pt):
        r = R[self.dragging]
        frac = max(0.0, min(1.0, (pt.x() - r.left() - 7) / (r.width() - 14)))
        if self.dragging == "vol":
            self.amp.set_volume(frac)
            self.message = f"VOLUME: {round(frac * 100)}%"
        elif self.dragging == "bal":
            v = round((frac - 0.5) * 200)
            if abs(v) < 12:
                v = 0
            self.amp.balance = v
            self.message = "BALANCE: CENTER" if v == 0 else f"BALANCE: {abs(v)}% {'LEFT' if v < 0 else 'RIGHT'}"
        elif self.dragging == "seek":
            dur = self.amp.player.duration()
            if dur > 0:
                frac = max(0.0, min(1.0, (pt.x() - r.left() - 14) / (r.width() - 29)))
                self.seek_preview = frac * dur
                self.message = f"SEEK TO: {fmt(self.seek_preview / 1000)}/{fmt(dur / 1000)} ({round(frac * 100)}%)"
        self.update()

    # ---- painting ----------------------------------------------------------------------------------------------
    def paintEvent(self, event):
        amp = self.amp
        p = QPainter(self)
        p.scale(self.s, self.s)
        w, h = MAIN.width(), MAIN.height()
        g = QLinearGradient(0, 0, 0, h)
        g.setColorAt(0, QColor("#3A3A50"))
        g.setColorAt(1, QColor("#1C1C28"))
        p.fillRect(QRectF(0, 0, w, h), g)
        p.setPen(QColor(255, 255, 255, 10))
        for y in range(TB + 2, h, 3):                                     # brushed-metal texture
            p.drawLine(0, y, w, y)
        p.setPen(QPen(QColor("#6A6A84"), 1))
        p.drawRect(QRectF(0.5, 0.5, w - 1, h - 1))
        active = amp.frame is not None and amp.desktop.active is amp.frame
        title_bar(p, w, "CLAUDEAMP", active, ("min", "close"))
        self._display(p)
        self._info(p)
        self._sliders(p)
        self._transport(p)

    def _display(self, p):
        amp = self.amp
        d = R["display"]
        p.fillRect(d, LCD)
        p.setPen(QPen(QColor("#5A5A70"), 1))
        p.drawRect(d.adjusted(-0.5, -0.5, 0.5, 0.5))
        # clutterbar
        c = R["clutter"]
        p.fillRect(c, QColor("#2A2A3A"))
        p.setFont(_font(7, True))
        for i, letter in enumerate("OAIDV"):
            lit = (letter == "D" and amp.double)
            p.setPen(QColor("#F0E070" if lit else "#9A9AB0"))
            p.drawText(QRectF(c.left(), c.top() + i * 8, c.width(), 8), Qt.AlignCenter, letter)
        # play / pause / stop indicator
        st = amp.player.playbackState()
        ix, iy = 25, 28
        p.setPen(Qt.NoPen)
        if st == QMediaPlayer.PlayingState or amp.intro_playing:
            tri = QPolygonF([QPointF(ix, iy), QPointF(ix + 7, iy + 4), QPointF(ix, iy + 8)])
            p.setBrush(GREEN)
            p.drawPolygon(tri)
        elif st == QMediaPlayer.PausedState:
            p.fillRect(QRectF(ix, iy, 2.5, 8), QColor("#E8C020"))
            p.fillRect(QRectF(ix + 4.5, iy, 2.5, 8), QColor("#E8C020"))
        else:
            p.fillRect(QRectF(ix, iy + 1, 7, 7), QColor("#C02020"))
        # the time
        if st != QMediaPlayer.StoppedState or amp.intro_playing:
            pos = amp.player.position() / 1000
            dur = amp.player.duration() / 1000
            secs = (dur - pos) if (amp.remaining and dur > 0) else pos
            blink = st == QMediaPlayer.PausedState and (amp.ticks // 15) % 2
            if not blink:
                m, s = int(secs) // 60, int(secs) % 60
                text = f"{m:02d}" if m < 100 else f"{m % 100:02d}"
                if amp.remaining and dur > 0:
                    p.fillRect(QRectF(39, 31.7, 6, 1.6), GREEN)
                draw_digit(p, 48, 26, text[0], GREEN)
                draw_digit(p, 60, 26, text[1], GREEN)
                p.fillRect(QRectF(72.5, 29, 1.6, 1.6), GREEN)
                p.fillRect(QRectF(72.5, 35, 1.6, 1.6), GREEN)
                draw_digit(p, 78, 26, str(s // 10), GREEN)
                draw_digit(p, 90, 26, str(s % 10), GREEN)
        # the visualisation
        v = R["vis"]
        a = amp.analyser
        if amp.vis_mode == 0:
            grad = QLinearGradient(0, v.top(), 0, v.bottom())
            grad.setColorAt(0, QColor("#EF3110"))
            grad.setColorAt(0.35, QColor("#D6B521"))
            grad.setColorAt(0.7, QColor("#29CE10"))
            grad.setColorAt(1, QColor("#18840F"))
            for i in range(a.BARS):
                x = v.left() + i * 4
                bh = round(a.bands[i] * v.height())
                if bh > 0:
                    p.fillRect(QRectF(x, v.bottom() - bh, 3, bh), grad)
                py = v.bottom() - max(1, round(a.peaks[i] * v.height()))
                if a.peaks[i] > 0.02:
                    p.fillRect(QRectF(x, py, 3, 1), QColor("#9C9CB0"))
        elif amp.vis_mode == 1:
            pts = list(a.samples)[-152:][::2]
            p.setPen(QPen(QColor("#F0C020"), 1))
            path = QPainterPath()
            for i, val in enumerate(pts):
                y = v.center().y() - max(-1.0, min(1.0, val * 2.2)) * (v.height() / 2 - 1)
                (path.moveTo if i == 0 else path.lineTo)(v.left() + i, y)
            p.drawPath(path)

    def _info(self, p):
        amp = self.amp
        t = R["title"]
        p.fillRect(t, LCD)
        text = self.message or amp.scroll_text()
        p.setFont(_font(8, True))
        p.setPen(GREEN)
        if self.message:
            p.drawText(t.adjusted(2, 0, -2, 0), Qt.AlignVCenter | Qt.AlignLeft, text)
        else:
            if text != self.title_text:
                self.title_text = text
                self.scroll = 0.0
            fm = QFontMetricsF(p.font())
            tw = fm.horizontalAdvance(text)
            p.save()
            p.setClipRect(t)
            if tw <= t.width() - 4:
                p.drawText(t.adjusted(2, 0, -2, 0), Qt.AlignVCenter | Qt.AlignLeft, text)
            else:
                loop = tw + 24
                x = t.left() + 2 - (self.scroll % loop)
                for dx in (0, loop):
                    p.drawText(QRectF(x + dx, t.top(), tw + 4, t.height()), Qt.AlignVCenter | Qt.AlignLeft,
                               text + "  ***")
            p.restore()
        # kbps / kHz / mono-stereo
        p.setFont(_font(7, True))
        kbps, khz = amp.stream_info()
        for box, val, label, lx in ((QRectF(111, 41, 16, 9), kbps, "kbps", 129), (QRectF(156, 41, 11, 9), khz,
                                                                                    "khz", 169)):
            p.fillRect(box, LCD)
            p.setPen(GREEN)
            p.drawText(box, Qt.AlignCenter, val)
            p.setPen(QColor("#C8C8D8"))
            p.drawText(QRectF(lx, 41, 24, 9), Qt.AlignVCenter | Qt.AlignLeft, label)
        playing = amp.player.playbackState() != QMediaPlayer.StoppedState or amp.intro_playing
        for x, label, lit in ((212, "mono", playing and amp.analyser.channels == 1),
                              (239, "stereo", playing and amp.analyser.channels >= 2)):
            p.setPen(GREEN if lit else QColor("#4A4A5A"))
            p.drawText(QRectF(x, 41, 28, 9), Qt.AlignVCenter | Qt.AlignLeft, label)

    def _sliders(self, p):
        amp = self.amp
        # volume: the groove goes from green to red as it's turned up
        r = R["vol"]
        col = QColor.fromHsvF(max(0.0, 0.33 - amp.volume * 0.33), 0.85, 0.75)
        p.fillRect(QRectF(r.left(), r.top() + 4, r.width(), 5), QColor("#101018"))
        p.fillRect(QRectF(r.left() + 1, r.top() + 5, (r.width() - 2) * amp.volume, 3), col)
        knob = QRectF(r.left() + (r.width() - 14) * amp.volume, r.top() + 1, 14, 11)
        bevel(p, knob, self.dragging == "vol")
        # balance
        r = R["bal"]
        p.fillRect(QRectF(r.left(), r.top() + 4, r.width(), 5), QColor("#101018"))
        p.fillRect(QRectF(r.center().x() - 0.5, r.top() + 5, 1, 3), QColor("#3C8C3C"))
        knob = QRectF(r.left() + (r.width() - 14) * (amp.balance + 100) / 200, r.top() + 1, 14, 11)
        bevel(p, knob, self.dragging == "bal")
        # EQ / PL toggles
        p.setFont(_font(7, True))
        for name, on in (("eq", False), ("pl", amp.show_playlist)):
            r = R[name]
            bevel(p, r, self.pressed == name)
            p.fillRect(QRectF(r.left() + 3, r.top() + 4, 3, 4), QColor("#30E030" if on else "#2A3A2A"))
            p.setPen(QColor("#202030"))
            p.drawText(r.adjusted(6, 0, 0, 0), Qt.AlignCenter, name.upper())
        # the position bar
        r = R["seek"]
        p.fillRect(r, QColor("#121220"))
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor("#4A4A60"), 1))
        p.drawRect(r.adjusted(0.5, 0.5, -0.5, -0.5))
        dur = amp.player.duration()
        if dur > 0 and not amp.intro_playing:
            pos = self.seek_preview if self.seek_preview is not None else amp.player.position()
            knob = QRectF(r.left() + (r.width() - 29) * min(1.0, pos / dur), r.top(), 29, 10)
            bevel(p, knob, self.dragging == "seek", face="#C8C8A0", light="#F8F8D8", dark="#5A5A40")

    def _transport(self, p):
        amp = self.amp
        ink = QColor("#1A1A28")
        for name in ("prev", "play", "pause", "stop", "next", "eject"):
            r = R[name]
            bevel(p, r, self.pressed == name)
            c = r.center() + (QPointF(0.5, 0.5) if self.pressed == name else QPointF(0, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(ink)
            if name == "play":
                p.drawPolygon(QPolygonF([c + QPointF(-3, -4), c + QPointF(4, 0), c + QPointF(-3, 4)]))
            elif name == "pause":
                p.drawRect(QRectF(c.x() - 3.5, c.y() - 4, 2.5, 8))
                p.drawRect(QRectF(c.x() + 1, c.y() - 4, 2.5, 8))
            elif name == "stop":
                p.drawRect(QRectF(c.x() - 3.5, c.y() - 3.5, 7, 7))
            elif name in ("prev", "next"):
                d = 1 if name == "next" else -1
                p.drawPolygon(QPolygonF([c + QPointF(-4 * d, -4), c + QPointF(2 * d, 0), c + QPointF(-4 * d, 4)]))
                p.drawRect(QRectF(c.x() + (2.2 if d > 0 else -4) , c.y() - 4, 1.8, 8))
            else:                                                            # eject
                p.drawPolygon(QPolygonF([c + QPointF(-4, 1), c + QPointF(0, -4), c + QPointF(4, 1)]))
                p.drawRect(QRectF(c.x() - 4, c.y() + 2, 8, 2))
        p.setFont(_font(7, True))
        for name, on, label in (("shuffle", amp.shuffle, "SHUFFLE"), ("repeat", amp.repeat, "REP")):
            r = R[name]
            bevel(p, r, self.pressed == name)
            p.fillRect(QRectF(r.left() + 3, r.top() + 5, 3, 4), QColor("#30E030" if on else "#2A3A2A"))
            p.setPen(ink)
            p.drawText(r.adjusted(6, 0, 0, 0), Qt.AlignCenter, label)
        # the logo: a lightning bolt in a coin
        r = R["logo"]
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, QColor("#5A5A78"))
        g.setColorAt(1, QColor("#1A1A26"))
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#8A8AA0"), 0.8))
        p.setBrush(g)
        p.drawEllipse(r.adjusted(0.5, 0.5, -0.5, -0.5))
        x, y = r.left(), r.top()
        bolt = QPolygonF([QPointF(x + 10, y + 2), QPointF(x + 4.5, y + 9.5), QPointF(x + 8, y + 9.5),
                          QPointF(x + 6, y + 15), QPointF(x + 12.5, y + 6.5), QPointF(x + 9, y + 6.5),
                          QPointF(x + 11, y + 2)])
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#FFC21A"))
        p.drawPolygon(bolt)
        p.setRenderHint(QPainter.Antialiasing, False)


# ---- the playlist editor -------------------------------------------------------------------------------------------

PL = {"close": QRectF(264, 3, 9, 9), "list": QRectF(12, 20, 240, PL_H - 20 - 38), "scroll": QRectF(254, 20, 9, PL_H - 58),
      "add": QRectF(12, PL_H - 30, 25, 18), "rem": QRectF(41, PL_H - 30, 25, 18), "sel": QRectF(70, PL_H - 30, 25, 18),
      "misc": QRectF(99, PL_H - 30, 25, 18), "list_opts": QRectF(236, PL_H - 30, 25, 18),
      "mini": QRectF(130, PL_H - 31, 100, 20)}
ROW = 10


class PlaylistPanel(QWidget):
    def __init__(self, amp):
        super().__init__(amp)
        self.amp = amp
        self.top = 0
        self.selected = set()
        self.anchor = None
        self.pressed = None
        self.scrolling = False

    @property
    def s(self):
        return self.amp.scale

    def rows(self):
        return int(PL["list"].height() // ROW)

    def logical(self, event):
        pos = event.position()
        return QPointF(pos.x() / self.s, pos.y() / self.s)

    def row_at(self, pt):
        r = PL["list"]
        if not r.contains(pt):
            return None
        i = self.top + int((pt.y() - r.top()) // ROW)
        return i if i < len(self.amp.playlist) else None

    def ensure_visible(self, i):
        if i is None:
            return
        if i < self.top:
            self.top = i
        elif i >= self.top + self.rows():
            self.top = i - self.rows() + 1
        self.update()

    def mousePressEvent(self, event):
        pt = self.logical(event)
        if event.button() == Qt.RightButton and PL["list"].contains(pt):
            self.amp.playlist_menu(event.globalPosition().toPoint())
            return
        if event.button() != Qt.LeftButton:
            return
        for name in ("close", "add", "rem", "sel", "misc", "list_opts"):
            if PL[name].contains(pt):
                self.pressed = name
                self.update()
                return
        if PL["scroll"].contains(pt):
            self.scrolling = True
            self._scroll_to(pt)
            return
        i = self.row_at(pt)
        if i is not None:
            mods = event.modifiers()
            if mods & Qt.ControlModifier:
                self.selected ^= {i}
            elif mods & Qt.ShiftModifier and self.anchor is not None:
                lo, hi = sorted((self.anchor, i))
                self.selected = set(range(lo, hi + 1))
            else:
                self.selected = {i}
            if not mods & Qt.ShiftModifier:
                self.anchor = i
            self.update()
            return
        if PL["list"].contains(pt):
            self.selected.clear()
            self.update()
            return
        event.ignore()

    def mouseMoveEvent(self, event):
        if self.scrolling:
            self._scroll_to(self.logical(event))
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        self.scrolling = False
        if self.pressed:
            name, self.pressed = self.pressed, None
            self.update()
            if PL[name].contains(self.logical(event)):
                gp = self.mapToGlobal(QPointF(PL[name].left() * self.s, PL[name].top() * self.s).toPoint())
                self.amp.playlist_button(name, gp)
            return
        event.ignore()

    def mouseDoubleClickEvent(self, event):
        i = self.row_at(self.logical(event))
        if i is not None:
            self.amp.play_index(i)
        else:
            event.ignore()

    def wheelEvent(self, event):
        self.top = max(0, min(max(0, len(self.amp.playlist) - self.rows()),
                              self.top + (-3 if event.angleDelta().y() > 0 else 3)))
        self.update()

    def _scroll_to(self, pt):
        r = PL["scroll"]
        span = max(0, len(self.amp.playlist) - self.rows())
        frac = max(0.0, min(1.0, (pt.y() - r.top() - 9) / max(1, r.height() - 18)))
        self.top = round(frac * span)
        self.update()

    def paintEvent(self, event):
        amp = self.amp
        p = QPainter(self)
        p.scale(self.s, self.s)
        w, h = MAIN.width(), PL_H
        g = QLinearGradient(0, 0, 0, h)
        g.setColorAt(0, QColor("#30304A"))
        g.setColorAt(1, QColor("#1A1A26"))
        p.fillRect(QRectF(0, 0, w, h), g)
        p.setPen(QPen(QColor("#6A6A84"), 1))
        p.drawRect(QRectF(0.5, 0.5, w - 1, h - 1))
        active = amp.frame is not None and amp.desktop.active is amp.frame
        title_bar(p, w, "CLAUDEAMP PLAYLIST", active, ("close",))
        p.fillRect(QRectF(0, TB, w, 6), QColor("#24243A"))
        # the list
        lr = PL["list"]
        p.fillRect(lr, LCD)
        p.setFont(_font(8, True))
        fm = QFontMetricsF(p.font())
        for row in range(self.rows()):
            i = self.top + row
            if i >= len(amp.playlist):
                break
            e = amp.playlist[i]
            y = lr.top() + row * ROW
            rr = QRectF(lr.left(), y, lr.width(), ROW)
            if i in self.selected:
                p.fillRect(rr, QColor("#0000C6"))
            p.setPen(QColor("#FFFFFF") if i == amp.index else GREEN)
            length = fmt(e.length) if e.length else ""
            lw = fm.horizontalAdvance(length) + 4
            text = fm.elidedText(f"{i + 1}. {e.title}", Qt.ElideRight, lr.width() - lw - 6)
            p.drawText(rr.adjusted(2, 0, -lw, 0), Qt.AlignVCenter | Qt.AlignLeft, text)
            p.drawText(rr.adjusted(0, 0, -2, 0), Qt.AlignVCenter | Qt.AlignRight, length)
        # scroll bar
        sr = PL["scroll"]
        p.fillRect(sr, QColor("#14141E"))
        span = max(0, len(amp.playlist) - self.rows())
        thumb_y = sr.top() + (sr.height() - 18) * (self.top / span if span else 0)
        bevel(p, QRectF(sr.left(), thumb_y, sr.width(), 18), self.scrolling)
        # bottom buttons
        p.setFont(_font(7, True))
        for name, label in (("add", "ADD"), ("rem", "REM"), ("sel", "SEL"), ("misc", "MISC"), ("list_opts", "LIST")):
            r = PL[name]
            bevel(p, r, self.pressed == name)
            p.setPen(QColor("#1A1A28"))
            p.drawText(r, Qt.AlignCenter, label)
        # the mini display: selected / total time
        m = PL["mini"]
        p.fillRect(m, LCD)
        total = sum(e.length for e in amp.playlist)
        sel = sum(amp.playlist[i].length for i in self.selected if i < len(amp.playlist))
        p.setPen(GREEN)
        p.drawText(m.adjusted(3, 1, -3, -10), Qt.AlignLeft | Qt.AlignVCenter, f"{fmt(sel)}/{fmt(total)}")
        pos = amp.player.position() / 1000 if amp.player.playbackState() != QMediaPlayer.StoppedState else 0
        p.drawText(m.adjusted(3, 10, -3, 0), Qt.AlignLeft | Qt.AlignVCenter,
                   f"{len(amp.playlist)} item{'s' if len(amp.playlist) != 1 else ''}")
        p.drawText(m.adjusted(3, 10, -3, 0), Qt.AlignRight | Qt.AlignVCenter, fmt(pos) if pos else "")


# ---- the video window ----------------------------------------------------------------------------------------------

class VideoWindow(QWidget):
    BOTTOM = 14

    def __init__(self, amp):
        super().__init__()
        self.amp = amp
        self.frame = None
        self.image = QImage()
        self.native = None
        self.pressed = None
        self.resize(352 + 0, 288 + TB + self.BOTTOM)

    def set_frame(self, frame):
        if frame.isValid():
            self.image = frame.toImage()
            if self.native is None and not self.image.isNull():
                self.native = self.image.size()
                self.fit(1)
            self.update()

    def clear(self):
        self.image = QImage()
        self.native = None
        self.update()

    def fit(self, zoom):
        if self.frame is None or self.native is None or self.frame.maximized:
            return
        area = self.amp.desktop.work_area()
        w = max(MAIN.width(), int(self.native.width() * zoom))
        h = int(self.native.height() * zoom) + TB + self.BOTTOM
        scale = min(1.0, (area.width() - 20) / w, (area.height() - 20) / h)
        self.frame.resize(int(w * scale), int((h - TB - self.BOTTOM) * scale) + TB + self.BOTTOM)
        g = self.frame.geometry()
        if not area.contains(g):
            self.frame.move(max(0, min(g.left(), area.right() - g.width())), max(0, min(g.top(), area.bottom() - g.height())))
        self.amp.dock_video()

    def _buttons(self):
        y = self.height() - self.BOTTOM + 2
        return {"1x": QRectF(6, y, 18, 10), "2x": QRectF(26, y, 18, 10), "fs": QRectF(46, y, 18, 10),
                "close": QRectF(self.width() - 11, 3, 9, 9)}

    def mousePressEvent(self, event):
        pt = event.position()
        for name, r in self._buttons().items():
            if r.contains(pt):
                self.pressed = name
                return
        if TB <= pt.y() < self.height() - self.BOTTOM and event.button() == Qt.LeftButton:
            self.amp.toggle_pause()
            return
        if event.button() == Qt.RightButton:
            self.amp.main_menu(event.globalPosition().toPoint())
            return
        event.ignore()

    def mouseReleaseEvent(self, event):
        if self.pressed:
            name, self.pressed = self.pressed, None
            if self._buttons()[name].contains(event.position()):
                if name == "close":
                    self.amp.show_video(False)
                elif name == "fs":
                    self.frame.toggle_maximize()
                else:
                    if self.frame.maximized:
                        self.frame.toggle_maximize()
                    self.fit(1 if name == "1x" else 2)
            return
        event.ignore()

    def mouseDoubleClickEvent(self, event):
        if TB <= event.position().y() < self.height() - self.BOTTOM:
            self.amp.toggle_pause()                     # undo the single click's pause
            self.frame.toggle_maximize()
        else:
            event.ignore()

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()
        active = self.frame is not None and self.amp.desktop.active is self.frame
        title_bar(p, w, "CLAUDEAMP VIDEO", active, ("close",))
        screen = QRectF(0, TB, w, h - TB - self.BOTTOM)
        p.fillRect(screen, Qt.black)
        if not self.image.isNull():
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            img = self.image
            s = min(screen.width() / img.width(), screen.height() / img.height())
            iw, ih = img.width() * s, img.height() * s
            p.drawImage(QRectF(screen.left() + (screen.width() - iw) / 2, screen.top() + (screen.height() - ih) / 2,
                               iw, ih), img)
        else:
            p.setPen(QColor("#2A2A40"))
            p.setFont(QFont("Arial Black", 18))
            p.drawText(screen, Qt.AlignCenter, "ClaudeAmp")
        bar = QRectF(0, h - self.BOTTOM, w, self.BOTTOM)
        g = QLinearGradient(0, bar.top(), 0, bar.bottom())
        g.setColorAt(0, QColor("#3A3A50"))
        g.setColorAt(1, QColor("#1C1C28"))
        p.fillRect(bar, g)
        p.setFont(_font(7, True))
        for name, r in self._buttons().items():
            if name == "close":
                continue
            bevel(p, r, self.pressed == name)
            p.setPen(QColor("#1A1A28"))
            p.drawText(r, Qt.AlignCenter, name.upper())
        p.setPen(GREEN)
        e = self.amp.current()
        if e is not None:
            p.drawText(QRectF(72, bar.top(), w - 80, bar.height()), Qt.AlignVCenter | Qt.AlignRight,
                       QFontMetricsF(p.font()).elidedText(e.title, Qt.ElideRight, w - 80))


# ---- the program -------------------------------------------------------------------------------------------------

class ClaudeAmp(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.video_frame = None
        st = load_json(STATE_FILE, {})
        self.volume = float(st.get("volume", 0.8))
        self.balance = 0
        self.shuffle = bool(st.get("shuffle", False))
        self.repeat = bool(st.get("repeat", False))
        self.double = bool(st.get("double", False))
        self.vis_mode = int(st.get("vis", 0)) % 3
        self.remaining = bool(st.get("remaining", False))
        self.show_playlist = bool(st.get("playlist_shown", True))
        self.intro = bool(st.get("intro", True))
        self.playlist = [Entry(p, t, l) for p, t, l in st.get("playlist", []) if Path(p).exists()]
        self.index = min(int(st.get("index", -1)), len(self.playlist) - 1)
        self.intro_playing = False
        self.intro_entry = None
        self.after_intro = None
        self.ticks = 0
        self.history = []
        self.analyser = Analyser()
        self.player = QMediaPlayer(self)
        self.output = QAudioOutput(self)
        self.player.setAudioOutput(self.output)
        self.buffers = QAudioBufferOutput(self)
        self.player.setAudioBufferOutput(self.buffers)
        self.buffers.audioBufferReceived.connect(self.analyser.feed)
        self.sink = QVideoSink(self)
        self.player.setVideoSink(self.sink)
        self.player.mediaStatusChanged.connect(self._status)
        self.player.durationChanged.connect(self._duration)
        self.player.errorOccurred.connect(self._error)
        self.player.playbackStateChanged.connect(lambda _s: self.update_all())
        self.video = VideoWindow(self)
        self.sink.videoFrameChanged.connect(self.video.set_frame)
        self.setFocusPolicy(Qt.StrongFocus)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.main = MainPanel(self)
        self.pl = PlaylistPanel(self)
        lay.addWidget(self.main)
        lay.addWidget(self.pl)
        for panel in (self.main, self.pl):
            panel.setFocusPolicy(Qt.ClickFocus)
            panel.setFocusProxy(self)
        self.apply_size()
        self._apply_volume()
        self.timer = QTimer(self, interval=33, timeout=self._tick)
        self.timer.start()

    # ---- size -------------------------------------------------------------------------------------------------
    @property
    def scale(self):
        return 2 if self.double else 1

    def apply_size(self):
        s = self.scale
        self.main.setFixedSize(MAIN.width() * s, MAIN.height() * s)
        self.pl.setFixedSize(MAIN.width() * s, PL_H * s)
        self.pl.setVisible(self.show_playlist)
        h = MAIN.height() * s + (PL_H * s if self.show_playlist else 0)
        self.setFixedSize(MAIN.width() * s, h)
        if self.frame is not None:
            self.frame.setFixedSize(self.size())
            area = self.desktop.work_area()
            g = self.frame.geometry()
            if not area.contains(g):
                self.frame.move(max(0, min(g.left(), area.right() - g.width())),
                                max(0, min(g.top(), area.bottom() - g.height())))
            self.dock_video()

    def set_double(self, on):
        self.double = on
        self.apply_size()
        self.save_state()

    def toggle_playlist(self):
        self.show_playlist = not self.show_playlist
        self.apply_size()
        self.save_state()

    # ---- state ------------------------------------------------------------------------------------------------
    def save_state(self):
        save_json(STATE_FILE, {"volume": round(self.volume, 2), "shuffle": self.shuffle, "repeat": self.repeat,
                               "double": self.double, "vis": self.vis_mode, "remaining": self.remaining,
                               "playlist_shown": self.show_playlist, "intro": self.intro, "index": self.index,
                               "playlist": [[str(e.path), e.title, e.length] for e in self.playlist]})

    def current(self):
        if self.intro_playing:
            if self.intro_entry is None:
                self.intro_entry = Entry(INTRO, INTRO_TITLE)
            return self.intro_entry
        return self.playlist[self.index] if 0 <= self.index < len(self.playlist) else None

    def scroll_text(self):
        e = self.current()
        if e is None:
            return "CLAUDEAMP 2.81"
        n = 1 if self.intro_playing else self.index + 1
        return f"{n}. {e.title} ({fmt(e.length)})" if e.length else f"{n}. {e.title}"

    def stream_info(self):
        if self.player.playbackState() == QMediaPlayer.StoppedState and not self.intro_playing:
            return "", ""
        e = self.current()
        kbps = ""
        dur = self.player.duration() / 1000
        if e is not None and dur > 0:
            try:
                kbps = str(min(999, round(e.path.stat().st_size * 8 / dur / 1000)))
            except OSError:
                pass
        return kbps, str(round(self.analyser.rate / 1000))

    def update_all(self):
        self.main.update()
        self.pl.update()
        if self.video_frame is not None and isValid(self.video_frame) and self.video_frame.isVisible():
            self.video.update()

    def _tick(self):
        self.ticks += 1
        playing = self.player.playbackState() == QMediaPlayer.PlayingState
        self.analyser.tick(playing)
        if self.ticks % 2 == 0:
            self.main.scroll += 1
        if self.main.message and not self.main.dragging:
            self.main.message = None
        self.main.update()
        if self.ticks % 15 == 0:
            self.pl.update()

    # ---- playing ----------------------------------------------------------------------------------------------
    def start(self, paths=None):
        """A fresh start: the llama intro (if wanted), then the files asked for (or nothing)."""
        if paths:
            self.after_intro = paths
        if self.intro and INTRO.exists():
            self.intro_playing = True
            self.player.setSource(QUrl.fromLocalFile(str(INTRO)))
            self._apply_volume()
            self.player.play()
        else:
            self._after_intro()

    def _after_intro(self):
        self.intro_playing = False
        paths, self.after_intro = self.after_intro, None
        if paths:
            self.play_files(paths)
        else:
            self.player.stop()
            self.player.setSource(QUrl())
        self.update_all()

    def play_files(self, paths, replace=False):
        """Winamp's 'Play': add the files to the playlist and start the first of them."""
        if self.intro_playing:
            self.after_intro = list(paths)
            return
        paths = [Path(p) for p in paths if Path(p).suffix.lower() in MEDIA_EXTS]
        if not paths:
            return
        if replace:
            self.playlist = []
        first = None
        for path in paths:
            i = next((n for n, e in enumerate(self.playlist) if e.path == path), None)
            if i is None:
                self.playlist.append(Entry(path))
                i = len(self.playlist) - 1
            if first is None:
                first = i
        self.play_index(first)

    def add_files(self, paths):
        for path in paths:
            path = Path(path)
            if path.suffix.lower() in MEDIA_EXTS and not any(e.path == path for e in self.playlist):
                self.playlist.append(Entry(path))
        self.save_state()
        self.pl.update()

    def play_index(self, i):
        if not (0 <= i < len(self.playlist)):
            return
        if self.intro_playing:
            self.intro_playing = False
            self.after_intro = None
        self.index = i
        e = self.playlist[i]
        self.history.append(i)
        self.video.clear()
        self.player.setSource(QUrl.fromLocalFile(str(e.path)))
        self._apply_volume()
        self.player.play()
        if e.video:
            self.show_video(True)
        self.pl.ensure_visible(i)
        if self.frame is not None:
            self.frame.set_title(f"{i + 1}. {e.title} - ClaudeAmp")
        self.save_state()
        self.update_all()

    def button(self, name):
        if name == "close":
            self.frame.request_close()
        elif name == "min":
            self.desktop.minimize(self.frame)
        elif name == "prev":
            self.previous()
        elif name == "play":
            self.play()
        elif name == "pause":
            self.toggle_pause()
        elif name == "stop":
            self.stop()
        elif name == "next":
            self.next()
        elif name == "eject":
            self.open_dialog()
        elif name == "shuffle":
            self.shuffle = not self.shuffle
            self.save_state()
        elif name == "repeat":
            self.repeat = not self.repeat
            self.save_state()
        elif name == "pl":
            self.toggle_playlist()
        elif name == "eq":
            self.main.message = "EQUALIZER: NOT INSTALLED"
        elif name == "logo":
            self.about()
        elif name == "menu":
            pass
        self.update_all()

    def play(self):
        if self.intro_playing:
            return
        st = self.player.playbackState()
        if st == QMediaPlayer.PausedState:
            self.player.play()
        elif st == QMediaPlayer.PlayingState:
            self.player.setPosition(0)                       # Winamp: Play while playing restarts the song
        elif self.playlist:
            self.play_index(max(0, self.index))
        else:
            self.open_dialog()

    def toggle_pause(self):
        st = self.player.playbackState()
        if st == QMediaPlayer.PlayingState:
            self.player.pause()
        elif st == QMediaPlayer.PausedState:
            self.player.play()

    def stop(self):
        if self.intro_playing:
            self.intro_playing = False
            self.after_intro = None
        self.player.stop()
        self.video.clear()
        self.update_all()

    def next(self):
        if not self.playlist:
            return
        if self.shuffle and len(self.playlist) > 1:
            self.play_index(random.choice([i for i in range(len(self.playlist)) if i != self.index]))
        elif self.index + 1 < len(self.playlist):
            self.play_index(self.index + 1)
        elif self.repeat:
            self.play_index(0)
        else:
            self.stop()

    def previous(self):
        if not self.playlist:
            return
        if self.shuffle and len(self.history) > 1:
            self.history.pop()
            self.play_index(self.history.pop())
        else:
            self.play_index(max(0, self.index - 1) if self.index > 0 else (len(self.playlist) - 1 if self.repeat
                                                                              else 0))

    def seek_by(self, ms):
        if self.player.duration() > 0:
            self.player.setPosition(max(0, min(self.player.duration(), self.player.position() + ms)))

    def _status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            if self.intro_playing:
                QTimer.singleShot(0, self._after_intro)
            elif self.repeat and len(self.playlist) == 1:
                QTimer.singleShot(0, lambda: self.play_index(self.index))
            else:
                QTimer.singleShot(0, self.next)

    def _duration(self, ms):
        e = self.current()
        if e is not None and not self.intro_playing and ms > 0 and abs(e.length - ms / 1000) > 1:
            e.length = ms / 1000
            self.save_state()
        self.update_all()

    def _error(self, _err, msg):
        if self.intro_playing:
            QTimer.singleShot(0, self._after_intro)
            return
        self.main.message = "ERROR: CAN'T PLAY THIS FILE"
        QTimer.singleShot(1500, lambda: setattr(self.main, "message", None) if isValid(self) else None)

    def set_volume(self, v):
        self.volume = max(0.0, min(1.0, v))
        self._apply_volume()
        self.save_state()
        self.main.update()

    def _apply_volume(self):
        self.output.setVolume(0.0 if sound.is_muted() else self.volume ** 2)

    def set_vis(self, mode):
        self.vis_mode = mode % 3
        self.save_state()

    # ---- windows ----------------------------------------------------------------------------------------------
    def show_video(self, on):
        if on:
            if self.video_frame is None or not isValid(self.video_frame):
                self.video_frame = AmpFrame(self.desktop, "ClaudeAmp Video", self.video, amp_icon(), resizable=True)
                self.video.frame = self.video_frame
                self.video_frame.setMinimumSize(MAIN.width(), 120)
                self.video_frame.placed = True
                self.dock_video(force=True)
            self.desktop.open_window(self.video_frame)
            if self.frame is not None:
                self.desktop.activate(self.frame)
        elif self.video_frame is not None and isValid(self.video_frame):
            self.desktop.withdraw(self.video_frame)

    def dock_video(self, force=False):
        """Keep the video window beside the main window (to its right, or its left if there's no room)."""
        vf = self.video_frame
        if self.frame is None or vf is None or not isValid(vf) or vf.maximized:
            return
        g, v = self.frame.geometry(), vf.geometry()
        if not force and not g.intersects(v):
            return
        area = self.desktop.work_area()
        x = g.right() + 4 if g.right() + 4 + v.width() <= area.right() else max(0, g.left() - 4 - v.width())
        vf.move(x, max(0, min(g.top(), area.bottom() - v.height())))

    def main_menu(self, at):
        m = QMenu(self)
        m.setStyleSheet(MENU_STYLE)
        m.addAction("&About ClaudeAmp...", self.about)
        m.addSeparator()
        m.addAction("Play &file...\tL", self.open_dialog)
        m.addSeparator()
        pl = QAction("Playlist &Editor\tAlt+E", m, checkable=True, checked=self.show_playlist)
        pl.triggered.connect(lambda _c: self.toggle_playlist())
        m.addAction(pl)
        vid = QAction("&Video\tAlt+V", m, checkable=True,
                      checked=bool(self.video_frame and isValid(self.video_frame) and self.video_frame.isVisible()))
        vid.triggered.connect(lambda on: self.show_video(on))
        m.addAction(vid)
        m.addSeparator()
        opts = m.addMenu("&Options")
        ds = QAction("&Double Size\tCtrl+D", opts, checkable=True, checked=self.double)
        ds.triggered.connect(lambda on: self.set_double(on))
        opts.addAction(ds)
        tr = QAction("Time &remaining", opts, checkable=True, checked=self.remaining)
        tr.triggered.connect(lambda on: (setattr(self, "remaining", on), self.save_state()))
        opts.addAction(tr)
        intro = QAction("Play the &llama intro at start-up", opts, checkable=True, checked=self.intro)
        intro.triggered.connect(lambda on: (setattr(self, "intro", on), self.save_state()))
        opts.addAction(intro)
        vis = m.addMenu("&Visualization")
        group = QActionGroup(vis)
        for i, label in enumerate(("&Spectrum analyzer", "&Oscilloscope", "O&ff")):
            act = QAction(label, vis, checkable=True, checked=i == self.vis_mode)
            act.triggered.connect(lambda _c=False, i=i: self.set_vis(i))
            group.addAction(act)
            vis.addAction(act)
        play = m.addMenu("&Playback")
        for label, fn in (("&Previous\tZ", self.previous), ("Pla&y\tX", self.play), ("P&ause\tC", self.toggle_pause),
                          ("&Stop\tV", self.stop), ("&Next\tB", self.next)):
            play.addAction(label, fn)
        play.addSeparator()
        play.addAction("Back 5 seconds\tLeft", lambda: self.seek_by(-5000))
        play.addAction("Fwd 5 seconds\tRight", lambda: self.seek_by(5000))
        play.addSeparator()
        for label, attr in (("S&huffle\tS", "shuffle"), ("&Repeat\tR", "repeat")):
            act = QAction(label, play, checkable=True, checked=getattr(self, attr))
            act.triggered.connect(lambda on, attr=attr: (setattr(self, attr, on), self.save_state()))
            play.addAction(act)
        m.addSeparator()
        m.addAction("E&xit", lambda: self.frame.request_close())
        m.triggered.connect(lambda _a: sound.play("menu"))
        m.exec(at)

    def playlist_button(self, name, at):
        if name == "close":
            self.toggle_playlist()
            return
        m = QMenu(self)
        m.setStyleSheet(MENU_STYLE)
        sel = self.pl.selected
        if name == "add":
            m.addAction("Add &file...", lambda: self.open_dialog(add=True))
            e = self.current()
            if e is not None and not self.intro_playing:
                m.addAction("Add the rest of this &folder", lambda: self.add_files(
                    sorted(p for p in e.path.parent.iterdir() if p.suffix.lower() in MEDIA_EXTS)))
        elif name == "rem":
            m.addAction("Remove &selected\tDel", self.remove_selected).setEnabled(bool(sel))
            m.addAction("Remove &missing files", lambda: self._keep([e for e in self.playlist if e.path.exists()]))
            m.addAction("&Clear playlist", lambda: self._keep([]))
        elif name == "sel":
            m.addAction("Select &all\tCtrl+A", lambda: (self.pl.selected.update(range(len(self.playlist))),
                                                         self.pl.update()))
            m.addAction("Select &none", lambda: (self.pl.selected.clear(), self.pl.update()))
            m.addAction("&Invert selection", lambda: (setattr(self.pl, "selected", set(range(len(self.playlist)))
                                                              - self.pl.selected), self.pl.update()))
        elif name == "misc":
            m.addAction("Sort by &title", lambda: self._keep(sorted(self.playlist, key=lambda e: e.title.lower())))
            m.addAction("Sort by &file name", lambda: self._keep(sorted(self.playlist, key=lambda e: e.path.name.lower())))
            m.addAction("&Randomize list", lambda: self._keep(random.sample(self.playlist, len(self.playlist))))
            m.addAction("Re&verse list", lambda: self._keep(list(reversed(self.playlist))))
            m.addSeparator()
            m.addAction("File &info...", self.file_info)
        else:
            m.addAction("&New list", lambda: self._keep([]))
        m.triggered.connect(lambda _a: sound.play("menu"))
        m.exec(at)

    def playlist_menu(self, at):
        m = QMenu(self)
        m.setStyleSheet(MENU_STYLE)
        i = next(iter(sorted(self.pl.selected)), None)
        m.addAction("&Play item", lambda: self.play_index(i)).setEnabled(i is not None)
        m.addAction("&Remove item(s)\tDel", self.remove_selected).setEnabled(i is not None)
        m.addSeparator()
        m.addAction("File &info...", self.file_info)
        m.exec(at)

    def _keep(self, entries):
        cur = self.playlist[self.index] if 0 <= self.index < len(self.playlist) else None
        self.playlist = list(entries)
        self.index = self.playlist.index(cur) if cur in self.playlist else -1
        self.pl.selected.clear()
        self.pl.top = 0
        self.save_state()
        self.update_all()

    def remove_selected(self):
        self._keep([e for i, e in enumerate(self.playlist) if i not in self.pl.selected])

    def open_dialog(self, add=False):
        from .opendialog import open_dialog
        e = self.current()
        start = e.path.parent if (e is not None and not self.intro_playing) else None
        open_dialog(self.desktop, "Add file(s) to playlist" if add else "Open file(s)", MEDIA_EXTS,
                    (lambda p: self.add_files([p])) if add else (lambda p: self.play_files([p])), amp_icon(), start)

    def file_info(self):
        from ..explorer.dialogs import msgbox
        i = next(iter(sorted(self.pl.selected)), None)
        e = self.playlist[i] if i is not None else self.current()
        if e is None:
            return
        try:
            size = e.path.stat().st_size
        except OSError:
            size = 0
        msgbox(self.desktop, "File Info", f"{e.title}\n\n{e.path.name}\nSize: {size:,} bytes\n"
                                         f"Length: {fmt(e.length) if e.length else 'unknown'}\n"
                                         f"Type: {'Video' if e.video else 'Audio'}", "info")

    def about(self):
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, "About ClaudeAmp", "ClaudeAmp 2.81\n\nIt really whips the llama's ass!\n\n"
               "A Winamp 2 tribute for ClaudeXP.\nThe intro is DJ Mike Llama's.", "info")

    # ---- keys -------------------------------------------------------------------------------------------------
    def keyPressEvent(self, event):
        k, mods = event.key(), event.modifiers()
        if mods & Qt.ControlModifier and k == Qt.Key_D:
            self.set_double(not self.double)
        elif mods & Qt.ControlModifier and k == Qt.Key_A:
            self.pl.selected = set(range(len(self.playlist)))
            self.pl.update()
        elif mods & Qt.AltModifier and k == Qt.Key_E:
            self.toggle_playlist()
        elif mods & Qt.AltModifier and k == Qt.Key_V:
            self.show_video(not (self.video_frame and isValid(self.video_frame) and self.video_frame.isVisible()))
        elif k == Qt.Key_Z:
            self.previous()
        elif k == Qt.Key_X:
            self.play()
        elif k == Qt.Key_C:
            self.toggle_pause()
        elif k == Qt.Key_V:
            self.stop()
        elif k == Qt.Key_B:
            self.next()
        elif k == Qt.Key_L:
            self.open_dialog()
        elif k == Qt.Key_S:
            self.shuffle = not self.shuffle
            self.save_state()
        elif k == Qt.Key_R:
            self.repeat = not self.repeat
            self.save_state()
        elif k == Qt.Key_Left:
            self.seek_by(-5000)
        elif k == Qt.Key_Right:
            self.seek_by(5000)
        elif k == Qt.Key_Up:
            self.set_volume(self.volume + 0.02)
        elif k == Qt.Key_Down:
            self.set_volume(self.volume - 0.02)
        elif k == Qt.Key_Delete:
            self.remove_selected()
        elif k in (Qt.Key_Return, Qt.Key_Enter) and self.pl.selected:
            self.play_index(min(self.pl.selected))
        else:
            super().keyPressEvent(event)
            return
        self.update_all()

    def closeEvent(self, event):
        self.timer.stop()
        self.player.stop()
        self.save_state()
        if self.video_frame is not None and isValid(self.video_frame):
            self.desktop.close_window(self.video_frame)
        event.accept()


_open = {}


def open_amp(desktop, path=None):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = ClaudeAmp(desktop)
        win = AmpFrame(desktop, "ClaudeAmp", body, amp_icon())
        body.frame = win
        win.setFixedSize(body.size())
        _open["win"] = win
        desktop.open_window(win)
        body.start([path] if path is not None else None)
        body.setFocus()
        return win
    desktop.open_window(win)
    if path is not None:
        win.content.play_files([path])
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.player.stop()
        win.content.save_state()
