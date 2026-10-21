"""ClaudeTV: an over-the-air TV tuner card's viewer, the kind that came with a Hauppauge or ATI card in 2001.

Whatever is on is decided by the clock (see schedule.py): turning the TV on joins a program partway through, and
changing channels shows a burst of snow while the tuner locks on. Channels 2, 7 and 11 have nothing on them, just
static, and if a scheduled file has gone missing from the archive that channel shows static too.

Keys: Up/Down or PgUp/PgDn change channel, digits enter a channel, +/- volume, M mute, I info, G guide, C captions,
S second audio (SAP; the RiffTrax movies have the riff track there), double-click for full screen."""
import os
from pathlib import Path
import random
import re
from datetime import timedelta

from PySide6.QtCore import QLocale, QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import (QAction, QActionGroup, QColor, QFont, QIcon, QImage, QLinearGradient, QPainter,
                           QPainterPath, QPen, QPixmap)
from PySide6.QtMultimedia import QAudioOutput, QMediaMetaData, QMediaPlayer, QVideoSink
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QPushButton, QSlider, QVBoxLayout, QWidget
from shiboken6 import isValid

from claudecore.jsonfile import load_json, save_json
from . import lineup, schedule
from claudecore import host

STATE_FILE = host.data("claudetv") / "tv.json"
STATIC = [Path(__file__).resolve().parent / "assets" / f"static{n}.mp4" for n in (1, 2, 3, 4)]

def _clock_text(t):
    return t.strftime("%I:%M %p").lstrip("0")

DEAD_STATIC = {7: 0, 12: 1, 13: 3}          # which clip each empty channel shows (schedule.DEAD)
TUNE_MS = 450                                 # snow while the tuner locks on
OSD_MS = 4000
GREEN = QColor("#3CFF5A")


def tv_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#202020"), 1.4))
    p.drawLine(11, 2, 16, 8)
    p.drawLine(21, 2, 16, 8)
    g = QLinearGradient(0, 8, 0, 30)
    g.setColorAt(0, QColor("#8A8A92"))
    g.setColorAt(1, QColor("#3A3A40"))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(2, 8, 28, 21), 4, 4)
    s = QLinearGradient(0, 11, 0, 26)
    s.setColorAt(0, QColor("#7FC4FF"))
    s.setColorAt(1, QColor("#1A4C9A"))
    p.setBrush(s)
    p.setPen(QPen(QColor("#101010"), 1))
    p.drawRoundedRect(QRectF(5, 11, 18, 15), 3, 3)
    p.setBrush(QColor("#D0D0D0"))
    p.drawEllipse(QRectF(25, 13, 3, 3))
    p.drawEllipse(QRectF(25, 19, 3, 3))
    p.end()
    return QIcon(pm)


def _noise_frames(n=6, w=300, h=225):
    frames = []
    for _ in range(n):
        data = bytes(min(255, max(0, int(b * 0.85) + 20)) for b in os.urandom(w * h))
        img = QImage(data, w, h, w, QImage.Format_Grayscale8).copy()
        frames.append(img)
    return frames


def _time(dt):
    return f"{dt:%I:%M}".lstrip("0") + ("am" if dt.hour < 12 else "pm")


def now_secs():
    return (host.now() - schedule.EPOCH).total_seconds()


def _not_future(date_text):
    """Air dates and years after 2001 would give the game away on a PC where it's always 2001."""
    years = [int(y) for y in re.findall(r"(?:19|20)\d\d", date_text or "")]
    return not years or max(years) <= host.era()


def describe(slot):
    """(title, subtitle line, description) for a program slot."""
    m = slot.media
    when = f"{_time(slot.when())} - {_time(slot.until())}"
    if m.kind == "movie" or slot.text == "Paw Pictures Presents":
        bits = [b for b in (m.year if _not_future(m.year) else "", m.rating) if b]
        mins = round(m.secs / 60)
        bits.append(f"{mins // 60} hr {mins % 60} min" if mins >= 60 else f"{mins} min")
        return m.title, f"{when}  ·  {'  ·  '.join(bits)}", m.desc
    bits = []
    if m.season and m.episode:
        bits.append(f"Season {m.season}, Episode {m.episode}")
    if m.aired and _not_future(m.aired):
        bits.append(f"First aired {m.aired}")
    sub = f"{when}  ·  {'  ·  '.join(bits)}" if bits else when
    title = f'{m.show}: "{m.title}"' if m.show and m.title and m.title != m.show else m.label()
    desc = m.desc or (f"From the {m.show} DVD extras." if m.kind == "special" else "")
    return title, sub, desc


class Screen(QWidget):
    """The picture: video frames, snow, the Up Next card, captions and the green on-screen display."""

    def __init__(self, tuner):
        super().__init__(tuner)
        self.tuner = tuner
        self.setMinimumSize(320, 240)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.frame = QImage()
        self.mode = "off"                  # off | scanning | snow | video | card
        self.noise = _noise_frames()
        self.noise_i = 0
        self.card = None                   # (channel, slot)
        self.caption = ""
        self.osd_channel = ""
        self.osd_info = None               # (title, sub, desc) or None
        self.osd_long = False
        self.osd_message = ""
        self.osd_timer = QTimer(self, singleShot=True, timeout=self.clear_osd)
        self.snow_timer = QTimer(self, interval=33, timeout=self._next_noise)

    def set_frame(self, img):
        self.frame = img
        if self.mode == "video":
            self.update()

    def set_mode(self, mode):
        self.mode = mode
        if mode in ("snow", "scanning"):
            self.snow_timer.start()
        else:
            self.snow_timer.stop()
        self.update()

    def _next_noise(self):
        self.noise_i = (self.noise_i + 1) % len(self.noise)
        self.update()

    def show_osd(self, channel_text, info=None, long=False, message="", ms=OSD_MS):
        self.osd_channel, self.osd_info, self.osd_long, self.osd_message = channel_text, info, long, message
        self.osd_timer.start(ms)
        self.update()

    def clear_osd(self):
        self.osd_channel, self.osd_info, self.osd_message = "", None, ""
        self.update()

    def mouseDoubleClickEvent(self, event):
        self.tuner.toggle_full_screen()

    def contextMenuEvent(self, event):
        self.tuner.context_menu(event.globalPos())

    # ---- painting -----------------------------------------------------------
    def _picture_rect(self, img_w, img_h):
        """4:3 or widescreen video, letterboxed into the screen."""
        if img_w <= 0 or img_h <= 0:
            return QRectF(self.rect())
        scale = min(self.width() / img_w, self.height() / img_h)
        w, h = img_w * scale, img_h * scale
        return QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), Qt.black)
        if self.mode in ("snow", "scanning"):
            p.setRenderHint(QPainter.SmoothPixmapTransform, False)
            p.drawImage(QRectF(self.rect()), self.noise[self.noise_i])
            if self.mode == "scanning":
                self._text_box(p, "Scanning for channels...")
        elif self.mode == "video" and not self.frame.isNull():
            p.setRenderHint(QPainter.SmoothPixmapTransform, True)
            if self.tuner.showing_static():
                p.drawImage(QRectF(self.rect()), self.frame)       # snow fills the whole tube
            else:
                p.drawImage(self._picture_rect(self.frame.width(), self.frame.height()), self.frame)
        elif self.mode == "card" and self.card:
            self._paint_card(p)
        elif self.mode == "off":
            pass
        if self.caption and self.mode == "video":
            self._paint_caption(p)
        self._paint_osd(p)

    def _text_box(self, p, text):
        f = QFont("Courier New", max(10, self.height() // 22), QFont.Bold)
        p.setFont(f)
        r = p.fontMetrics().boundingRect(text).adjusted(-12, -8, 12, 8)
        r.moveCenter(self.rect().center())
        p.fillRect(r, QColor(0, 0, 0, 200))
        p.setPen(GREEN)
        p.drawText(r, Qt.AlignCenter, text)

    def _paint_card(self, p):
        channel, slot = self.card
        r = self.rect()
        g = QLinearGradient(0, 0, 0, r.height())
        g.setColorAt(0, QColor("#16307A"))
        g.setColorAt(1, QColor("#050C2A"))
        p.fillRect(r, g)
        h = r.height()
        p.setPen(QColor("#FFD43A"))
        p.setFont(QFont("Arial Black", max(14, h // 9)))
        p.drawText(QRectF(0, h * 0.2, r.width(), h * 0.18), Qt.AlignCenter, channel.call)
        p.setPen(QColor("#B8C8FF"))
        p.setFont(QFont("Arial", max(8, h // 30), QFont.Bold))
        p.drawText(QRectF(0, h * 0.37, r.width(), h * 0.07), Qt.AlignCenter, channel.slogan.upper())
        nxt = slot.next
        p.setPen(QColor("white"))
        p.setFont(QFont("Arial", max(10, h // 16), QFont.Bold))
        p.drawText(QRectF(0, h * 0.47, r.width(), h * 0.1), Qt.AlignCenter, "UP NEXT")
        if nxt is not None:
            title = nxt.media.label()
            p.setFont(QFont("Arial", max(9, h // 22), QFont.Bold))
            p.setPen(QColor("#FFD43A"))
            p.drawText(QRectF(r.width() * 0.05, h * 0.58, r.width() * 0.9, h * 0.2),
                       Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, title)
            p.setPen(QColor("white"))
            p.setFont(QFont("Arial", max(8, h // 26)))
            p.drawText(QRectF(0, h * 0.8, r.width(), h * 0.08), Qt.AlignCenter, f"at {_time(nxt.when())}")
        p.setPen(QColor("#8090C0"))
        p.setFont(QFont("Arial", max(7, h // 34)))
        p.drawText(QRectF(0, h * 0.9, r.width() - 10, h * 0.08), Qt.AlignRight | Qt.AlignVCenter,
                   _clock_text(host.now()))

    def _paint_caption(self, p):
        f = QFont("Courier New", max(9, self.height() // 24), QFont.Bold)
        p.setFont(f)
        fm = p.fontMetrics()
        lines = [ln for ln in self.caption.replace("\r", "").split("\n") if ln.strip()][-3:]
        y = self.height() - 18 - fm.height() * len(lines)
        for ln in lines:
            w = fm.horizontalAdvance(ln) + 12
            box = QRectF((self.width() - w) / 2, y, w, fm.height())
            p.fillRect(box, Qt.black)
            p.setPen(Qt.white)
            p.drawText(box, Qt.AlignCenter, ln)
            y += fm.height()

    def _outlined(self, p, rect, flags, text, color=GREEN):
        p.setPen(QColor(0, 0, 0, 220))
        for dx, dy in ((2, 2), (1, 1), (-1, 1), (1, -1)):
            p.drawText(rect.translated(dx, dy), flags, text)
        p.setPen(color)
        p.drawText(rect, flags, text)

    def _paint_osd(self, p):
        h = self.height()
        if self.osd_channel:
            p.setFont(QFont("Courier New", max(16, h // 9), QFont.Bold))
            self._outlined(p, QRectF(16, 10, self.width() - 32, h // 6), Qt.AlignRight | Qt.AlignTop,
                           self.osd_channel)
        if self.osd_message:
            p.setFont(QFont("Courier New", max(10, h // 20), QFont.Bold))
            self._outlined(p, QRectF(16, h * 0.22, self.width() - 32, h // 10), Qt.AlignRight | Qt.AlignTop,
                           self.osd_message)
        if self.osd_info:
            title, sub, desc = self.osd_info
            pad = 12
            lines = 3 if self.osd_long and desc else 2
            band_h = h * (0.36 if lines == 3 else 0.17)
            band = QRectF(0, h - band_h, self.width(), band_h)
            p.fillRect(band, QColor(0, 0, 0, 170))
            p.setFont(QFont("Arial", max(9, h // 24), QFont.Bold))
            fm = p.fontMetrics()
            p.setPen(Qt.white)
            p.drawText(band.adjusted(pad, 6, -pad, 0), Qt.AlignLeft | Qt.AlignTop,
                       fm.elidedText(title, Qt.ElideRight, int(band.width() - 2 * pad)))
            y = 6 + fm.height()
            p.setFont(QFont("Arial", max(8, h // 32)))
            p.setPen(GREEN)
            p.drawText(band.adjusted(pad, y, -pad, 0), Qt.AlignLeft | Qt.AlignTop, sub)
            if lines == 3:
                y += p.fontMetrics().height() + 4
                p.setPen(QColor("#E8E8E8"))
                p.drawText(band.adjusted(pad, y, -pad, -6), Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, desc)


class LedDisplay(QLabel):
    def __init__(self):
        super().__init__("--")
        self.setFixedSize(46, 26)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background:#061006; color:#3CFF5A; border:1px solid #303030; border-radius:2px;"
                           "font: bold 15px 'Courier New';")


PANEL_STYLE = """
QWidget#panel { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #D8D9DE, stop:0.5 #B4B6BE, stop:1 #8E9098); }
QPushButton { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #F4F4F6, stop:1 #BFC1C8);
              border: 1px solid #5A5C66; border-radius: 3px; padding: 2px 7px; font: bold 11px Tahoma; color:#202028; }
QPushButton:pressed { background: #A8AAB4; }
QPushButton:checked { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #9CF0A8, stop:1 #4FB862); }
QLabel { font: 11px Tahoma; color: #202028; }
"""


class Tuner(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.state = load_json(STATE_FILE, {})
        self.channels = []
        self.channel = None
        self.previous = None
        self.slot = None
        self.digits = ""
        self.full = False
        self.pending_seek = None
        self.source_path = None
        self.prefer_riff = True
        self.captions = bool(self.state.get("cc", False))
        self.volume = float(self.state.get("volume", 0.7))
        self.muted = False

        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.sink = QVideoSink(self)
        self.player.setVideoSink(self.sink)
        self.sink.videoFrameChanged.connect(self._frame)
        self.sink.subtitleTextChanged.connect(self._subtitle)
        self.player.mediaStatusChanged.connect(self._status)
        self.player.errorOccurred.connect(self._error)
        self.player.tracksChanged.connect(self._tracks)

        self.screen = Screen(self)
        self.panel = self._build_panel()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.screen, 1)
        lay.addWidget(self.panel)
        self.setFocusPolicy(Qt.StrongFocus)
        self._apply_volume()

        self.tick = QTimer(self, interval=500, timeout=self._tick)
        self.tune_timer = QTimer(self, singleShot=True, timeout=self._locked_on)
        self.digit_timer = QTimer(self, singleShot=True, timeout=self._enter_digits)
        self.screen.set_mode("scanning")
        lineup.get(self._lineup_ready)

    # ---- controls -------------------------------------------------------------------------------
    def _build_panel(self):
        panel = QWidget()
        panel.setObjectName("panel")
        panel.setAttribute(Qt.WA_StyledBackground)
        panel.setStyleSheet(PANEL_STYLE)
        row = QHBoxLayout(panel)
        row.setContentsMargins(8, 5, 8, 5)
        row.setSpacing(4)

        def button(text, tip, slot, checkable=False, width=None):
            b = QPushButton(text)
            b.setToolTip(tip)
            b.setFocusPolicy(Qt.NoFocus)
            b.setCheckable(checkable)
            if width:
                b.setFixedWidth(width)
            b.clicked.connect(slot)
            row.addWidget(b)
            return b

        self.led = LedDisplay()
        row.addWidget(self.led)
        button("▲", "Channel up", lambda: self.step(1), width=28)
        button("▼", "Channel down", lambda: self.step(-1), width=28)
        button("Last", "Previous channel", self.last_channel)
        row.addSpacing(8)
        row.addWidget(QLabel("Vol"))
        self.vol = QSlider(Qt.Horizontal)
        self.vol.setRange(0, 100)
        self.vol.setValue(int(self.volume * 100))
        self.vol.setFixedWidth(80)
        self.vol.setFocusPolicy(Qt.NoFocus)
        self.vol.valueChanged.connect(self._set_volume)
        row.addWidget(self.vol)
        self.mute_btn = button("Mute", "Mute (M)", self.toggle_mute, checkable=True)
        row.addStretch(1)
        self.sap_btn = button("SAP", "Second audio program (S)", self.next_audio)
        self.cc_btn = button("CC", "Closed captions (C)", self.toggle_captions, checkable=True)
        self.cc_btn.setChecked(self.captions)
        button("Info", "What's on (I)", lambda: self.show_info(long=True))
        button("Guide", "TV Guide (G)", self.open_guide)
        return panel

    def _set_volume(self, value):
        self.volume = value / 100
        self._apply_volume()
        self.screen.show_osd(self.channel_text(), message=f"VOLUME {'|' * (value // 5)}", ms=1500)

    def _apply_volume(self):
        self.audio.setVolume(0.0 if (self.muted or host.muted()) else self.volume)

    def toggle_mute(self):
        self.muted = not self.muted
        self.mute_btn.setChecked(self.muted)
        self._apply_volume()
        self.screen.show_osd(self.channel_text(), message="MUTE" if self.muted else "")

    def toggle_full_screen(self):
        if self.frame is not None:
            self.frame.toggle_maximize()

    def context_menu(self, pos):
        menu = QMenu(self)
        group = QActionGroup(menu)
        for ch in self.channels:
            a = QAction(f"Channel {ch.label()}" + ("" if not ch.dead else "  (no signal)"), menu, checkable=True)
            a.setChecked(ch is self.channel)
            a.triggered.connect(lambda _c=False, c=ch: self.tune(c))
            group.addAction(a)
            menu.addAction(a)
        menu.addSeparator()
        tracks = self.player.audioTracks()
        if len(tracks) > 1:
            audio = menu.addMenu("Audio")
            for i, md in enumerate(tracks):
                a = audio.addAction(self._track_name(md, i))
                a.setCheckable(True)
                a.setChecked(i == self.player.activeAudioTrack())
                a.triggered.connect(lambda _c=False, n=i: self._set_audio(n))
        menu.addAction("Closed Captions", self.toggle_captions).setCheckable(True)
        menu.actions()[-1].setChecked(self.captions)
        menu.addAction("TV Guide...", self.open_guide)
        menu.addAction("Full Screen", self.toggle_full_screen)
        menu.addSeparator()
        menu.addAction("Rescan Channels", self.rescan)
        menu.addAction("About ClaudeTV", self.about)
        menu.exec(pos)

    def about(self):
        host.message(self.desktop, "About ClaudeTV", "ClaudeTV for Windows\nVersion 2.1 (Build 2117)\n\n"
               "Analog TV tuner software. Channels found: "
               f"{sum(not c.dead for c in self.channels)}", "info")

    def rescan(self):
        self.player.stop()
        self.screen.set_mode("scanning")
        lineup.rescan(self._lineup_ready)

    # ---- keyboard -------------------------------------------------------------------------------
    def keyPressEvent(self, event):
        k, text = event.key(), event.text()
        if k in (Qt.Key_Up, Qt.Key_PageUp):
            self.step(1)
        elif k in (Qt.Key_Down, Qt.Key_PageDown):
            self.step(-1)
        elif text.isdigit():
            self.digits = (self.digits + text)[-2:]
            self.led.setText(self.digits.rjust(2, "-"))
            self.screen.show_osd(self.digits + "-" * (2 - len(self.digits)))
            self.digit_timer.start(1200 if len(self.digits) < 2 else 300)
        elif text in ("+", "="):
            self.vol.setValue(min(100, self.vol.value() + 5))
        elif text in ("-", "_"):
            self.vol.setValue(max(0, self.vol.value() - 5))
        elif text.lower() == "m":
            self.toggle_mute()
        elif text.lower() == "i":
            self.show_info(long=True)
        elif text.lower() == "g":
            self.open_guide()
        elif text.lower() == "c":
            self.toggle_captions()
        elif text.lower() == "s":
            self.next_audio()
        elif k == Qt.Key_Backspace:
            self.last_channel()
        elif k in (Qt.Key_Return, Qt.Key_Enter) and self.digits:
            self._enter_digits()
        else:
            super().keyPressEvent(event)

    def _enter_digits(self):
        self.digit_timer.stop()
        number, self.digits = int(self.digits or 0), ""
        ch = next((c for c in self.channels if c.number == number), None)
        if ch is not None:
            self.tune(ch)
        else:
            self.led.setText(f"{number:02d}")
            self.channel_snow(number)

    # ---- tuning ---------------------------------------------------------------------------------
    def _lineup_ready(self, channels):
        if not isValid(self):
            return
        self.channels = channels
        last = self.state.get("channel", 5)
        ch = next((c for c in channels if c.number == last), None) or next(
            (c for c in channels if not c.dead), channels[0] if channels else None)
        if ch is not None:
            self.tune(ch, remember=False)
        self.tick.start()

    def showing_static(self):
        return self.source_path is not None and any(self.source_path == str(c) for c in STATIC)

    def channel_text(self):
        return self.channel.label() if self.channel else ""

    def step(self, delta):
        if not self.channels:
            return
        i = self.channels.index(self.channel) if self.channel in self.channels else 0
        self.tune(self.channels[(i + delta) % len(self.channels)])

    def last_channel(self):
        if self.previous is not None:
            self.tune(self.previous)

    def channel_snow(self, number):
        """A channel number with no station at all: snow, and nothing else."""
        self.player.stop()
        self.source_path = None
        self.slot = None
        self.screen.set_mode("snow")
        self.screen.show_osd(f"{number}")

    def tune(self, channel, remember=True):
        if channel is not self.channel:
            self.previous = self.channel
        self.channel = channel
        self.led.setText(f"{channel.number:02d}")
        if remember:
            self.state["channel"] = channel.number
            save_json(STATE_FILE, self.state)
        if self.frame is not None:
            self.frame.set_title(f"ClaudeTV - Channel {channel.label()}")
        self.player.stop()
        self.source_path = None
        self.slot = None
        self.screen.caption = ""
        self.screen.set_mode("snow")
        self.screen.show_osd(channel.label())
        self.tune_timer.start(TUNE_MS)

    def _locked_on(self):
        self.sync(show_info=True)

    def _play(self, path, position_ms, loops=1):
        self.source_path = str(path)
        self.pending_seek = position_ms
        self.player.setLoops(loops)
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.player.play()

    def _static(self, which):
        clip = STATIC[which % len(STATIC)]
        if not clip.exists():
            self.player.stop()
            self.screen.set_mode("snow")
            return
        if self.source_path != str(clip):
            self._play(clip, random.randint(0, 4000), loops=QMediaPlayer.Infinite)
        self.screen.set_mode("video")

    def sync(self, show_info=False):
        """Make the picture match what the schedule says is on right now."""
        ch = self.channel
        if ch is None:
            return
        if ch.dead:
            self.slot = None
            self._static(DEAD_STATIC.get(ch.number, 0))
            return
        t = now_secs()
        slot = ch.at(t)
        if slot is None:
            self._static(2)
            return
        changed = slot is not self.slot
        self.slot = slot
        if slot.kind == "card":
            if changed:
                self.player.stop()
                self.source_path = None
                self.screen.caption = ""
                self.screen.card = (ch, slot)
                self.screen.set_mode("card")
            return
        path = slot.media.path
        if not path.exists():
            self._static(2)
            if changed:
                self.screen.show_osd(ch.label(), message="WEAK SIGNAL")
            return
        if changed or self.source_path != str(path):
            self.screen.caption = ""
            self._play(path, int((t - slot.start) * 1000))
            self.screen.set_mode("video")
            if slot.kind == "program" and (show_info or changed):
                self.show_info()

    def show_info(self, long=False):
        if self.channel is None:
            return
        if self.slot is not None and self.slot.kind == "program":
            self.screen.show_osd(self.channel.label(), describe(self.slot), long=long, ms=OSD_MS * (2 if long else 1))
        elif self.slot is not None and self.slot.kind in ("ad", "promo", "card"):
            nxt = self.slot.next or self.channel.next_program(self.channel.slots.index(self.slot))
            info = describe(nxt) if nxt else None
            if info:
                info = ("Up next: " + info[0], info[1], info[2])
            self.screen.show_osd(self.channel.label(), info, long=long)
        else:
            self.screen.show_osd(self.channel.label(), message="NO SIGNAL" if self.channel.dead else "")

    def _tick(self):
        if self.tune_timer.isActive() or self.channel is None or self.channel.dead:
            return
        slot = self.slot
        t = now_secs()
        if slot is None or t >= slot.end or t < slot.start:
            self.sync()
            return
        if slot.kind == "card":
            self.screen.update()            # the clock on the card
            return
        # stay in step with the clock (the window was dragged, the PC stalled, the file stuttered...)
        if self.pending_seek is None and self.player.isSeekable() and \
                self.player.playbackState() == QMediaPlayer.PlayingState:
            want = (t - slot.start) * 1000
            if abs(self.player.position() - want) > 4000:
                self.player.setPosition(int(want))

    # ---- player signals -------------------------------------------------------------------------
    def _frame(self, frame):
        if self.screen.mode == "video" and frame.isValid():
            self.screen.set_frame(frame.toImage())

    def _subtitle(self, text):
        self.screen.caption = text if self.captions else ""
        self.screen.update()

    def _status(self, status):
        if status in (QMediaPlayer.LoadedMedia, QMediaPlayer.BufferedMedia) and self.pending_seek is not None:
            pos, self.pending_seek = self.pending_seek, None
            if self.slot is not None and self.slot.kind != "card" and self.source_path == str(self.slot.media.path):
                pos = int((now_secs() - self.slot.start) * 1000)       # loading took a moment
            if pos > 500 and self.player.isSeekable():
                self.player.setPosition(pos)
            self.player.play()
        elif status == QMediaPlayer.EndOfMedia and self.player.loops() == 1:
            self.sync()
        elif status == QMediaPlayer.InvalidMedia:
            self._static(2)

    def _error(self, *_):
        if self.source_path and not any(self.source_path == str(s) for s in STATIC):
            self._static(2)
            if self.channel is not None:
                self.screen.show_osd(self.channel.label(), message="WEAK SIGNAL")

    def _tracks(self):
        tracks = self.player.audioTracks()
        if self.slot is not None and self.slot.media and "rifftrax" in self.slot.media.title.lower() and self.prefer_riff:
            for i, md in enumerate(tracks):
                if "riff" in self._track_name(md, i).lower():
                    self.player.setActiveAudioTrack(i)
                    break
        self.player.setActiveSubtitleTrack(0 if self.captions and self.player.subtitleTracks() else -1)
        self.sap_btn.setEnabled(len(tracks) > 1)

    @staticmethod
    def _track_name(md, i):
        title = md.value(QMediaMetaData.Title) or ""
        lang = md.value(QMediaMetaData.Language)
        try:
            lang = QLocale.languageToString(lang) if lang else ""
        except TypeError:
            lang = ""
        name = title or (lang if lang not in ("", "C", "Default") else "")
        return f"Track {i + 1}" + (f": {name}" if name else "")

    def next_audio(self):
        tracks = self.player.audioTracks()
        if len(tracks) < 2:
            self.screen.show_osd(self.channel_text(), message="MONO")
            return
        self._set_audio((self.player.activeAudioTrack() + 1) % len(tracks))

    def _set_audio(self, i):
        self.prefer_riff = False
        self.player.setActiveAudioTrack(i)
        tracks = self.player.audioTracks()
        self.screen.show_osd(self.channel_text(), message=("SAP  " if i else "STEREO  ") +
                             self._track_name(tracks[i], i).upper()[:28])

    def toggle_captions(self):
        self.captions = not self.captions
        self.cc_btn.setChecked(self.captions)
        self.state["cc"] = self.captions
        save_json(STATE_FILE, self.state)
        has = bool(self.player.subtitleTracks())
        self.player.setActiveSubtitleTrack(0 if self.captions and has else -1)
        if not self.captions:
            self.screen.caption = ""
        msg = "CC1" if self.captions else "CC OFF"
        if self.captions and not has and self.slot is not None and self.slot.kind == "program":
            msg = "CC1  (NOT AVAILABLE)"
        self.screen.show_osd(self.channel_text(), message=msg)

    def open_guide(self):
        from .guide import open_guide
        open_guide(self.desktop, self)

    def closeEvent(self, event):
        self.tick.stop()
        self.player.stop()
        self.state["volume"] = self.volume
        save_json(STATE_FILE, self.state)
        event.accept()


_open = {}


def open_tv(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = Tuner(desktop)
        win = host.window(desktop, "ClaudeTV", body, tv_icon(), (560, 500))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win


def current():
    win = _open.get("win")
    return win.content if win is not None and isValid(win) else None


def shutdown():
    t = current()
    if t is not None:
        t.player.stop()
