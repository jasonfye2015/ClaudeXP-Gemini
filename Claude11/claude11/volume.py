"""Volume: Windows 11's slider that pops up from the tray speaker, and the Volume Mixer (SndVol).

The master Volume is real: on Windows it sets Claude11's own volume in the Windows mixer, so every sound follows it.
'System Sounds' sets the level of the Windows 11 sounds. Mute is Claude11's own mute. Levels are kept in
data/volume.json. The same interface as ClaudeXP's volume module."""
import json
import os

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget

from . import sound
from .paths import DATA

FILE = DATA / "volume.json"
DEFAULTS = {"master": 1.0, "balance": 0.0, "wave": 1.0, "synth": 0.8, "cd": 0.8, "line": 0.6}
SLIDER_CSS = """
QSlider::groove:vertical { background: #C6C6C6; width: 4px; border-radius: 2px; }
QSlider::handle:vertical { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F6F6F6, stop:1 #D8D8D8);
                           border: 1px solid #707070; height: 11px; margin: 0 -8px; border-radius: 3px; }
QSlider::sub-page:vertical { background: #C6C6C6; }
QSlider::add-page:vertical { background: #3C8FD6; border-radius: 2px; }
"""


def _load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def levels():
    data = dict(DEFAULTS)
    saved = _load_json(FILE, {})
    if isinstance(saved, dict):
        data.update(saved)
    return data


def save(**changes):
    data = levels()
    data.update(changes)
    _save_json(FILE, data)
    apply(data)


def apply(data=None):
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


def speaker_pixmap(size=32, muted=False, level=None):
    """Windows 11's white speaker with its sound waves (fewer at lower volume, a red mark when muted)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    white = QColor("#FFFFFF") if size <= 20 else QColor("#4A4A4A")
    p.setPen(QPen(white.darker(130), max(1.0, s)))
    p.setBrush(white)
    p.drawPolygon(QPolygonF([QPointF(4 * s, 12 * s), QPointF(10 * s, 12 * s), QPointF(17 * s, 5 * s),
                             QPointF(17 * s, 27 * s), QPointF(10 * s, 20 * s), QPointF(4 * s, 20 * s)]))
    if muted:
        p.setPen(QPen(QColor("#E03030"), 2.5 * s))
        p.drawLine(QPointF(20 * s, 11 * s), QPointF(28 * s, 21 * s))
        p.drawLine(QPointF(28 * s, 11 * s), QPointF(20 * s, 21 * s))
    else:
        lv = levels()["master"] if level is None else level
        waves = 3 if lv > 0.66 else 2 if lv > 0.33 else 1 if lv > 0 else 0
        p.setPen(QPen(white, 2 * s))
        p.setBrush(Qt.NoBrush)
        for i in range(waves):
            r = (6 + i * 4) * s
            p.drawArc(QRectF(16 * s - r, 16 * s - r, 2 * r, 2 * r), -45 * 16, 90 * 16)
    p.end()
    return pm


def volume_icon(muted=None):
    muted = sound.is_muted() if muted is None else muted
    ic = QIcon()
    for sz in (16, 32):
        ic.addPixmap(speaker_pixmap(sz, muted))
    return ic


def _vslider(value, on_change=None, height=110):
    s = QSlider(Qt.Vertical)
    s.setRange(0, 100)
    s.setValue(int(round(value * 100)))
    s.setFixedHeight(height)
    s.setStyleSheet(SLIDER_CSS)
    if on_change:
        s.valueChanged.connect(lambda v: on_change(v / 100))
    return s


class VolumePopup(QFrame):
    """The little volume slider above the tray speaker; it closes when you click elsewhere."""

    def __init__(self, taskbar):
        super().__init__(None, Qt.Popup)
        self.taskbar = taskbar
        self.setStyleSheet("QFrame { background: #F0F0F0; border: 1px solid #7E7E7E; } QLabel { border: none; "
                           "font-family: 'Segoe UI'; font-size: 11px; color: #3A3A3A; } QPushButton { border: none; "
                           "background: transparent; }")
        v = QVBoxLayout(self)
        v.setContentsMargins(10, 8, 10, 8)
        self.level = QLabel(f"{int(levels()['master'] * 100)}")
        self.level.setAlignment(Qt.AlignHCenter)
        v.addWidget(self.level)
        row = QHBoxLayout()
        row.addStretch()
        self.slider = _vslider(levels()["master"], self._changed, 120)
        row.addWidget(self.slider)
        row.addStretch()
        v.addLayout(row)
        self.mute = QPushButton()
        self.mute.setFixedSize(24, 24)
        self.mute.setToolTip("Mute Speakers")
        self.mute.clicked.connect(self._mute)
        self._refresh_icon()
        v.addWidget(self.mute, 0, Qt.AlignHCenter)
        link = QLabel("Mixer")
        link.setStyleSheet("color: #0066CC; text-decoration: underline;")
        link.setAlignment(Qt.AlignHCenter)
        link.setCursor(Qt.PointingHandCursor)
        link.mousePressEvent = lambda e: (self.close(), open_volume_control(self.taskbar.desktop))
        v.addWidget(link)
        self.slider.sliderReleased.connect(lambda: sound.play("default"))
        self.adjustSize()

    def _changed(self, x):
        save(master=x)
        self.level.setText(f"{int(x * 100)}")
        self.taskbar.update()

    def _refresh_icon(self):
        self.mute.setIcon(QIcon(speaker_pixmap(24, sound.is_muted())))

    def _mute(self):
        sound.set_muted(not sound.is_muted())
        self._refresh_icon()
        self.taskbar.update()

    def show_at(self, global_pos):
        self.adjustSize()
        self.move(global_pos.x() - self.width() // 2, global_pos.y() - self.height() - 6)
        self.show()


class VolumeControl(QWidget):
    """The Volume Mixer: Speakers, System Sounds and a column per program making sound."""

    def __init__(self, taskbar):
        super().__init__()
        self.taskbar = taskbar
        self.frame = None
        self.setStyleSheet("QWidget { background: #F0F0F0; font-family: 'Segoe UI'; font-size: 12px; } "
                           "QLabel#head { color: #1E3B5A; font-size: 13px; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        head = QLabel("Device:  Speakers (High Definition Audio Device)")
        head.setObjectName("head")
        root.addWidget(head)
        cols = QHBoxLayout()
        cols.setSpacing(24)
        data = levels()
        for label, key in (("Speakers", "master"), ("System Sounds", "wave"), ("Windows Media Player", "cd"),
                           ("ClaudeAmp", "synth"), ("Internet Explorer", "line")):
            col = QVBoxLayout()
            title = QLabel(label)
            title.setAlignment(Qt.AlignHCenter)
            title.setWordWrap(True)
            title.setFixedWidth(84)
            col.addWidget(title)
            slider = _vslider(data[key], (lambda k: lambda v: save(**{k: v}))(key), 150)
            col.addWidget(slider, 0, Qt.AlignHCenter)
            btn = QPushButton()
            btn.setFixedSize(26, 26)
            btn.setIcon(QIcon(speaker_pixmap(22, sound.is_muted())))
            btn.setStyleSheet("border: 1px solid #ADADAD; background: #FAFAFA; border-radius: 3px;")
            if key == "master":
                btn.clicked.connect(self._toggle_mute)
                self.master_btn = btn
            col.addWidget(btn, 0, Qt.AlignHCenter)
            cols.addLayout(col)
        root.addLayout(cols)
        root.addStretch()

    def _toggle_mute(self):
        sound.set_muted(not sound.is_muted())
        self.master_btn.setIcon(QIcon(speaker_pixmap(22, sound.is_muted())))
        self.taskbar.update()


_open = {}


def open_volume_control(desktop):
    from shiboken6 import isValid
    from .wm import MicaWindow
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = VolumeControl(desktop.taskbar)
    win = MicaWindow(desktop, "Volume Mixer", body, volume_icon(), size=(560, 300))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    return win
