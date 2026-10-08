"""Sound Recorder, like Windows XP's: record up to 60 seconds from the microphone, the green waveform, Position and
Length, seek to start/end, play, stop, save .wav (in My Music by default), open .wav files, Edit > Delete Before /
After Current Position, and the Effects menu (Increase/Decrease Volume, Increase/Decrease Speed, Add Echo, Reverse)."""
import wave
from array import array
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QKeySequence, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtMultimedia import QAudio, QAudioFormat, QAudioSink, QAudioSource, QMediaDevices
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenuBar, QPushButton, QSlider, QVBoxLayout, QWidget

from .. import sound
from ..wm import XPWindow
from .notepad import MENU_STYLE

RATE = 22050
MAX_SECONDS = 60


def sndrec_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#404040"), 1))
    p.setBrush(QColor("#C0C0C0"))
    p.drawRoundedRect(QRectF(11.5, 3.5, 9, 15), 4, 4)
    p.setPen(QPen(QColor("#404040"), 2))
    p.drawArc(QRectF(8, 8, 16, 14), 180 * 16, 180 * 16)
    p.drawLine(16, 22, 16, 27)
    p.drawLine(11, 27, 21, 27)
    p.end()
    return QIcon(pm)


def fmt():
    f = QAudioFormat()
    f.setSampleRate(RATE)
    f.setChannelCount(1)
    f.setSampleFormat(QAudioFormat.Int16)
    return f


class Wave(QWidget):
    def __init__(self, rec):
        super().__init__()
        self.rec = rec
        self.setFixedHeight(56)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("black"))
        w, h = self.width(), self.height()
        p.setPen(QPen(QColor("#00A000"), 1))
        p.drawLine(0, h // 2, w, h // 2)
        data = self.rec.samples
        if not data:
            return
        pos = self.rec.position_samples()
        start = max(0, pos - w * 4)
        window = data[start:pos] if pos > 0 else data[:w * 4]
        if not window:
            return
        path = QPainterPath()
        step = max(1, len(window) // w)
        for i in range(0, len(window), step):
            x = i / max(1, len(window) - 1) * w
            y = h / 2 - window[i] / 32768 * (h / 2 - 2)
            (path.moveTo if i == 0 else path.lineTo)(x, y)
        p.setPen(QPen(QColor("#00FF40"), 1.2))
        p.drawPath(path)


class TransportButton(QPushButton):
    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        self.setFixedSize(40, 28)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QPointF(self.width() / 2, self.height() / 2)
        ink = QColor("#202020") if self.isEnabled() else QColor("#A0A0A0")
        p.setPen(Qt.NoPen)
        p.setBrush(ink)
        if self.kind == "record":
            p.setBrush(QColor("#D01010") if self.isEnabled() else QColor("#C0A0A0"))
            p.drawEllipse(c, 6, 6)
        elif self.kind == "stop":
            p.drawRect(QRectF(c.x() - 5, c.y() - 5, 10, 10))
        elif self.kind == "play":
            path = QPainterPath()
            path.moveTo(c.x() - 4, c.y() - 6)
            path.lineTo(c.x() + 6, c.y())
            path.lineTo(c.x() - 4, c.y() + 6)
            path.closeSubpath()
            p.drawPath(path)
        else:
            d = -1 if self.kind == "start" else 1
            for off in (0, 6):
                path = QPainterPath()
                path.moveTo(c.x() + d * (off - 6), c.y() - 5)
                path.lineTo(c.x() + d * off, c.y())
                path.lineTo(c.x() + d * (off - 6), c.y() + 5)
                path.closeSubpath()
                p.drawPath(path)
            p.drawRect(QRectF(c.x() + d * 7 - 1, c.y() - 5, 2, 10))


class SoundRecorder(QWidget):
    def __init__(self, desktop, path=None):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.path = None
        self.modified = False
        self.closing = False
        self.samples = array("h")
        self.pos = 0                    # current position in samples
        self.mode = "idle"              # idle / recording / playing
        self.source = self.sink = self.io = self.buffer = None
        self.play_start = 0
        self.setObjectName("sr")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(MENU_STYLE + "QWidget#sr { background: #ECE9D8; } QLabel { font-family: Tahoma; "
                                        "font-size: 11px; }")
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 8)
        menu = QMenuBar()
        menu.triggered.connect(lambda _a: sound.play("menu"))
        f = menu.addMenu("&File")
        f.addAction("&New", lambda: self._maybe_save(self.new), QKeySequence("Ctrl+N"))
        f.addAction("&Open...", lambda: self._maybe_save(self.open_dialog), QKeySequence("Ctrl+O"))
        f.addAction("&Save", self.save, QKeySequence("Ctrl+S"))
        f.addAction("Save &As...", self.save_as)
        f.addSeparator()
        f.addAction("P&roperties", self.properties)
        f.addSeparator()
        f.addAction("E&xit", lambda: self.frame.request_close())
        e = menu.addMenu("&Edit")
        e.addAction("Delete &Before Current Position", lambda: self._edit("before"))
        e.addAction("Delete &After Current Position", lambda: self._edit("after"))
        fx = menu.addMenu("Effect&s")
        for label, key in (("&Increase Volume (by 25%)", "louder"), ("&Decrease Volume", "quieter"),
                           ("Increase &Speed (by 100%)", "faster"), ("Decrease S&peed", "slower"),
                           ("&Add Echo", "echo"), ("&Reverse", "reverse")):
            fx.addAction(label, lambda k=key: self.effect(k))
        menu.addMenu("&Help").addAction("&About Sound Recorder", lambda: self._message(
            "About Sound Recorder", "Sound Recorder\nVersion 5.1 (Build 2600)"))
        v.addWidget(menu)
        body = QVBoxLayout()
        body.setContentsMargins(10, 6, 10, 0)
        labels = QHBoxLayout()
        self.position = QLabel("Position:\n0.00 sec.")
        self.wave = Wave(self)
        self.length = QLabel("Length:\n0.00 sec.")
        self.length.setAlignment(Qt.AlignRight)
        labels.addWidget(self.position)
        labels.addWidget(self.wave, 1)
        labels.addWidget(self.length)
        body.addLayout(labels)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self._seek)
        body.addWidget(self.slider)
        row = QHBoxLayout()
        self.btn = {}
        for kind, slot in (("start", self.seek_start), ("end", self.seek_end), ("play", self.play),
                           ("stop", self.stop), ("record", self.record)):
            b = TransportButton(kind)
            b.clicked.connect(slot)
            self.btn[kind] = b
            row.addWidget(b)
        body.addLayout(row)
        v.addLayout(body)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(50)
        self.setFixedSize(380, 170)
        if path is not None:
            self.load(Path(path))
        self._refresh()

    # ---- helpers --------------------------------------------------------------------------------------------
    def name(self):
        return self.path.name if self.path else "Sound"

    def seconds(self, n):
        return n / RATE

    def position_samples(self):
        return min(self.pos, len(self.samples))

    def _refresh(self):
        self.position.setText(f"Position:\n{self.seconds(self.position_samples()):.2f} sec.")
        self.length.setText(f"Length:\n{self.seconds(len(self.samples)):.2f} sec.")
        self.slider.blockSignals(True)
        self.slider.setRange(0, max(0, len(self.samples)))
        self.slider.setValue(self.position_samples())
        self.slider.blockSignals(False)
        busy = self.mode != "idle"
        self.btn["play"].setEnabled(not busy and bool(self.samples) and self.pos < len(self.samples))
        self.btn["record"].setEnabled(not busy and len(self.samples) < RATE * MAX_SECONDS)
        self.btn["stop"].setEnabled(busy)
        self.btn["start"].setEnabled(not busy and self.pos > 0)
        self.btn["end"].setEnabled(not busy and self.pos < len(self.samples))
        self.wave.update()
        if self.frame is not None:
            self.frame.set_title(f"{self.name()} - Sound Recorder")

    def _seek(self, value):
        self.pos = value
        self._refresh()

    def seek_start(self):
        self.pos = 0
        self._refresh()

    def seek_end(self):
        self.pos = len(self.samples)
        self._refresh()

    # ---- recording and playing ------------------------------------------------------------------------------------
    def record(self):
        device = QMediaDevices.defaultAudioInput()
        if device.isNull():
            return self._message("Sound Recorder", "There is no recording device. Plug in a microphone, and then "
                                 "try again.", "error")
        self.source = QAudioSource(device, fmt(), self)
        self.io = self.source.start()
        if self.io is None:
            return self._message("Sound Recorder", "The microphone could not be opened. It may be in use by "
                                 "another program, or blocked by your privacy settings.", "error")
        self.rec_start_len = len(self.samples)
        self.rec_insert = self.pos
        self.rec_buffer = array("h")
        self.io.readyRead.connect(self._read)
        self.mode = "recording"
        self._refresh()

    def _read(self):
        if self.io is None:
            return
        data = bytes(self.io.readAll().data())
        chunk = array("h")
        chunk.frombytes(data[: len(data) // 2 * 2])
        room = RATE * MAX_SECONDS - len(self.samples)
        chunk = chunk[:max(0, room)]
        self.samples[self.pos:self.pos + len(chunk)] = chunk     # record over / extend from the position
        self.pos += len(chunk)
        self.modified = True
        if len(self.samples) >= RATE * MAX_SECONDS:
            self.stop()

    def play(self):
        if not self.samples:
            return
        if self.pos >= len(self.samples):
            self.pos = 0
        data = self.samples[self.pos:].tobytes()
        self.buffer = QBuffer(self)
        self.buffer.setData(QByteArray(data))
        self.buffer.open(QIODevice.ReadOnly)
        self.sink = QAudioSink(QMediaDevices.defaultAudioOutput(), fmt(), self)
        self.sink.setVolume(0.0 if sound.is_muted() else 1.0)
        self.sink.stateChanged.connect(self._sink_state)
        self.play_start = self.pos
        self.sink.start(self.buffer)
        self.mode = "playing"
        self._refresh()

    def _sink_state(self, state):
        if state == QAudio.State.IdleState and self.mode == "playing":
            self.pos = len(self.samples)
            self.stop()

    def stop(self):
        if self.mode == "recording" and self.source is not None:
            self._read()
            self.source.stop()
            self.source = self.io = None
        elif self.mode == "playing" and self.sink is not None:
            self.sink.stop()
            self.sink = None
        self.mode = "idle"
        self._refresh()

    def _tick(self):
        if self.mode == "playing" and self.sink is not None:
            self.pos = min(len(self.samples), self.play_start + int(self.sink.processedUSecs() / 1e6 * RATE))
        if self.mode != "idle":
            self._refresh()

    # ---- editing ---------------------------------------------------------------------------------------------------
    def _edit(self, which):
        if not self.samples:
            return
        if which == "before":
            del self.samples[:self.pos]
            self.pos = 0
        else:
            del self.samples[self.pos:]
        self.modified = True
        self._refresh()

    def effect(self, key):
        s = self.samples
        if not s or self.mode != "idle":
            return
        clamp = lambda x: max(-32768, min(32767, int(x)))
        if key == "louder":
            out = array("h", (clamp(x * 1.25) for x in s))
        elif key == "quieter":
            out = array("h", (clamp(x * 0.8) for x in s))
        elif key == "faster":
            out = s[::2]
        elif key == "slower":
            out = array("h")
            for a, b in zip(s, s[1:] + array("h", [s[-1]])):
                out.append(a)
                out.append((a + b) // 2)
        elif key == "echo":
            delay = int(RATE * 0.18)
            out = array("h", s)
            for i in range(delay, len(out)):
                out[i] = clamp(out[i] + s[i - delay] * 0.5)
        elif key == "reverse":
            out = array("h", reversed(s))
        else:
            return
        self.samples = out[: RATE * MAX_SECONDS]
        self.pos = min(self.pos, len(self.samples))
        self.modified = True
        self._refresh()

    # ---- files -----------------------------------------------------------------------------------------------------
    def new(self):
        self.samples, self.pos, self.path, self.modified = array("h"), 0, None, False
        self._refresh()

    def load(self, path):
        try:
            with wave.open(str(path)) as w:
                ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
                raw = w.readframes(n)
        except (wave.Error, OSError, EOFError):
            return self._message("Sound Recorder", f"{Path(path).name} is not a valid wave file.", "error")
        if width == 1:
            vals = [(b - 128) << 8 for b in raw]
        elif width == 2:
            vals = array("h")
            vals.frombytes(raw[: len(raw) // 2 * 2])
        else:
            return self._message("Sound Recorder", "This wave format isn't supported.", "error")
        mono = [sum(vals[i:i + ch]) // ch for i in range(0, len(vals) - ch + 1, ch)] if ch > 1 else list(vals)
        if rate != RATE:
            ratio = rate / RATE
            mono = [mono[int(i * ratio)] for i in range(int(len(mono) / ratio))]
        self.samples = array("h", mono[: RATE * MAX_SECONDS])
        self.pos, self.path, self.modified = 0, Path(path), False
        self._refresh()

    def save(self, then=None):
        if self.path is None:
            return self.save_as(then)
        try:
            with wave.open(str(self.path), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(RATE)
                w.writeframes(self.samples.tobytes())
        except OSError as e:
            return self._message("Sound Recorder", f"Cannot save {self.path.name}.\n{e.strerror}", "error")
        self.modified = False
        self._refresh()
        if callable(then):
            then()

    def save_as(self, then=None):
        from ..explorer import vfs
        from .notepad import SaveAsDialog
        vfs.my_music().mkdir(parents=True, exist_ok=True)

        def saved(path):
            self.path = path if path.suffix.lower() == ".wav" else path.with_suffix(".wav")
            self.save(then)
        SaveAsDialog(self.desktop, self.path.name if self.path else "Sound.wav",
                     self.path.parent if self.path else vfs.my_music(), saved)

    def open_dialog(self):
        from .wmp import library_folders
        from .paint import _dialog
        from PySide6.QtWidgets import QApplication, QComboBox, QGridLayout, QListWidget, QListWidgetItem, QStyle
        body = QWidget()
        g = QGridLayout(body)
        where = QComboBox()
        for label, folder in library_folders():
            where.addItem(QApplication.style().standardIcon(QStyle.SP_DirIcon), label, str(folder))
        g.addWidget(QLabel("Look in:"), 0, 0)
        g.addWidget(where, 0, 1)
        files = QListWidget()
        files.setMinimumSize(320, 180)
        g.addWidget(files, 1, 0, 1, 2)

        def fill():
            files.clear()
            folder = Path(where.currentData())
            if folder.is_dir():
                for p in sorted(folder.rglob("*.wav")):
                    item = QListWidgetItem(str(p.relative_to(folder)))
                    item.setData(Qt.UserRole, str(p))
                    files.addItem(item)
        where.currentIndexChanged.connect(fill)
        fill()

        def accept():
            item = files.currentItem()
            if item is None:
                return False
            self.load(item.data(Qt.UserRole))
        win = _dialog(self.desktop, "Open", body, accept)
        win.icon = sndrec_icon()
        files.itemDoubleClicked.connect(lambda _i: accept() is not False and self.desktop.close_window(win))

    def properties(self):
        self._message(f"Properties for {self.name()}", f"Length: {self.seconds(len(self.samples)):.2f} sec.\n"
                      f"Data size: {len(self.samples) * 2:,} bytes\nAudio format: PCM 22.050 kHz, 16 Bit, Mono")

    def _maybe_save(self, proceed):
        if not self.modified:
            return proceed()

        def answer(button):
            if button == "Yes":
                self.save(proceed)
            elif button == "No":
                proceed()
        self._message("Sound Recorder", f"Do you want to save changes to {self.name()}?", "warning",
                      ("Yes", "No", "Cancel"), answer)

    def closeEvent(self, event):
        if self.mode != "idle":
            self.stop()
        if self.closing or not self.modified:
            self.timer.stop()
            event.accept()
            return
        event.ignore()

        def really_close():
            self.closing = True
            if self.frame is not None:
                self.desktop.close_window(self.frame)
        self._maybe_save(really_close)

    def _message(self, title, text, icon="info", buttons=("OK",), on_button=None):
        from ..explorer.dialogs import msgbox
        return msgbox(self.desktop, title, text, icon, buttons, on_button)


def open_sndrec(desktop, path=None):
    body = SoundRecorder(desktop, path)
    win = XPWindow(desktop, f"{body.name()} - Sound Recorder", body, sndrec_icon(), (380, 200), buttons=("min", "close"))
    body.frame = win
    win.fit_fixed_content()
    desktop.open_window(win)
    return win
