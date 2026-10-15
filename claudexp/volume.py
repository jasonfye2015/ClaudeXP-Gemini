"""Volume: the little slider that pops up from the tray speaker, and the Volume Control mixer (sndvol32).

The master Volume and Balance are real: on Windows they set ClaudeXP's own volume in the Windows mixer
(waveOutSetVolume on the program's audio session), so every sound ClaudeXP makes follows them. 'Wave' sets the
level of the XP system sounds. Mute is ClaudeXP's own mute (the red circle on the speaker). The other columns are
there because XP had them. Levels are kept in data/volume.json.
"""
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QPolygonF
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import (QCheckBox, QFrame, QHBoxLayout, QLabel, QMenuBar, QPushButton, QSlider, QVBoxLayout,
                               QWidget)

from . import sound
from .paths import DATA
from .programs.people import load_json, save_json

FILE = DATA / "volume.json"
DEFAULTS = {"master": 1.0, "balance": 0.0, "wave": 1.0, "synth": 0.8, "cd": 0.8, "line": 0.6}


def levels():
    data = dict(DEFAULTS)
    saved = load_json(FILE, {})
    if isinstance(saved, dict):
        data.update(saved)
    return data


def save(**changes):
    data = levels()
    data.update(changes)
    save_json(FILE, data)
    apply(data)


def apply(data=None):
    """Push the master volume/balance to Windows and the Wave level to the system sounds."""
    data = data or levels()
    sound.set_wave_volume(float(data["wave"]))
    if os.name != "nt":
        return
    try:
        import ctypes
        v, b = max(0.0, min(1.0, float(data["master"]))), max(-1.0, min(1.0, float(data["balance"])))
        left = int(0xFFFF * v * (1.0 if b <= 0 else 1.0 - b))
        right = int(0xFFFF * v * (1.0 if b >= 0 else 1.0 + b))
        ctypes.WinDLL("winmm").waveOutSetVolume(None, ctypes.c_uint32((right << 16) | left))
    except Exception:
        pass


def speaker_pixmap(size=32, muted=False):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 16
    body = QPolygonF([QPointF(1 * s, 5 * s), QPointF(4 * s, 5 * s), QPointF(8 * s, 1 * s), QPointF(8 * s, 15 * s),
                      QPointF(4 * s, 11 * s), QPointF(1 * s, 11 * s)])
    p.setPen(QPen(QColor("#1A3E7A"), max(1.0, s * 0.8)))
    p.setBrush(QColor("#E8EEF8"))
    p.drawPolygon(body)
    p.setBrush(Qt.NoBrush)
    if muted:
        p.setPen(QPen(QColor("#E0302A"), 2 * s))
        p.drawEllipse(QRectF(8 * s, 7 * s, 8 * s, 8 * s))
    else:
        p.setPen(QPen(QColor("#1A3E7A"), 1.2 * s))
        p.drawArc(QRectF(6 * s, 5 * s, 5 * s, 6 * s), -60 * 16, 120 * 16)
        p.drawArc(QRectF(5 * s, 2 * s, 9 * s, 12 * s), -60 * 16, 120 * 16)
    p.end()
    return pm


def volume_icon():
    ic = QIcon()
    for sz in (16, 32):
        ic.addPixmap(speaker_pixmap(sz))
    return ic


def _vslider(value, on_change=None, height=110):
    s = QSlider(Qt.Vertical)
    s.setRange(0, 100)
    s.setValue(int(round(value * 100)))
    s.setTickPosition(QSlider.TicksBothSides)
    s.setTickInterval(10)
    s.setFixedHeight(height)
    if on_change:
        s.valueChanged.connect(lambda v: on_change(v / 100))
    return s


class VolumePopup(QFrame):
    """XP's small 'Volume' box from a single click on the tray speaker; it closes when you click elsewhere."""

    def __init__(self, taskbar):
        super().__init__(None, Qt.Popup)
        self.taskbar = taskbar
        self.setStyleSheet("QFrame { background: #ECE9D8; border: 1px solid #808080; } QLabel, QCheckBox "
                           "{ font-family: Tahoma; font-size: 11px; border: none; }")
        v = QVBoxLayout(self)
        v.setContentsMargins(10, 8, 10, 8)
        title = QLabel("Volume")
        title.setAlignment(Qt.AlignHCenter)
        v.addWidget(title)
        row = QHBoxLayout()
        row.addStretch()
        self.slider = _vslider(levels()["master"], lambda x: save(master=x))
        row.addWidget(self.slider)
        row.addStretch()
        v.addLayout(row)
        self.mute = QCheckBox("Mute")
        self.mute.setChecked(sound.is_muted())
        self.mute.toggled.connect(self._mute)
        v.addWidget(self.mute)
        self.slider.sliderReleased.connect(lambda: sound.play("default"))
        self.adjustSize()

    def _mute(self, on):
        sound.set_muted(on)
        self.taskbar.update()

    def show_at(self, global_pos):
        self.adjustSize()
        self.move(global_pos.x() - self.width() // 2, global_pos.y() - self.height() - 4)
        self.show()


class VolumeControl(QWidget):
    """The Volume Control mixer: one column per line, each with Balance, a Volume slider and Mute."""

    LINES = [("master", "Volume Control", "Mute all"), ("wave", "Wave", "Mute"), ("synth", "SW Synth", "Mute"),
             ("cd", "CD Player", "Mute"), ("line", "Line In", "Mute")]

    def __init__(self, taskbar):
        super().__init__()
        self.taskbar = taskbar
        self.setStyleSheet("QWidget { font-family: Tahoma; font-size: 11px; } QFrame#col { border-right: 1px solid "
                           "#ACA899; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        bar = QMenuBar()
        bar.setStyleSheet("QMenuBar { background: #ECE9D8; }")
        opts = bar.addMenu("&Options")
        opts.addAction("&Properties").setEnabled(False)
        opts.addAction("&Advanced Controls").setEnabled(False)
        opts.addSeparator()
        opts.addAction("E&xit", lambda: self.frame.request_close() if getattr(self, "frame", None) else None)
        bar.addMenu("&Help").addAction("&About Volume Control").setEnabled(False)
        root.setMenuBar(bar)
        cols = QHBoxLayout()
        cols.setContentsMargins(8, 8, 8, 4)
        lv = levels()
        for key, label, mute_text in self.LINES:
            col = QFrame()
            col.setObjectName("col")
            cv = QVBoxLayout(col)
            name = QLabel(f"<b>{label}</b>" if key == "master" else label)
            name.setAlignment(Qt.AlignHCenter)
            cv.addWidget(name)
            cv.addWidget(QLabel("Balance:"), 0, Qt.AlignHCenter)
            bal = QSlider(Qt.Horizontal)
            bal.setRange(-50, 50)
            bal.setFixedWidth(70)
            bal.setValue(int(lv["balance"] * 50) if key == "master" else 0)
            bal.setEnabled(key == "master")
            if key == "master":
                bal.valueChanged.connect(lambda v: save(balance=v / 50))
            cv.addWidget(bal, 0, Qt.AlignHCenter)
            cv.addWidget(QLabel("Volume:"), 0, Qt.AlignHCenter)
            vol = _vslider(lv[key], lambda x, key=key: save(**{key: x}), height=120)
            if key in ("master", "wave"):
                vol.sliderReleased.connect(lambda: sound.play("default"))
            cv.addWidget(vol, 0, Qt.AlignHCenter)
            mute = QCheckBox(mute_text)
            if key == "master":
                mute.setChecked(sound.is_muted())
                mute.toggled.connect(self._mute_all)
                self.mute_all = mute
            cv.addWidget(mute, 0, Qt.AlignHCenter)
            if key == "master":
                adv = QPushButton("Advanced")
                adv.setEnabled(False)
                cv.addWidget(adv, 0, Qt.AlignHCenter)
            else:
                cv.addSpacing(26)
            cols.addWidget(col)
        root.addLayout(cols)
        status = QLabel("  SoundMAX Digital Audio")
        status.setStyleSheet("border-top: 1px solid #ACA899; padding: 2px;")
        root.addWidget(status)

    def _mute_all(self, on):
        sound.set_muted(on)
        self.taskbar.update()


_open = {}


def open_volume_control(desktop):
    from shiboken6 import isValid
    from .wm import XPWindow
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = VolumeControl(desktop.taskbar)
    win = XPWindow(desktop, "Volume Control", body, volume_icon(), size=(470, 330))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    return win
