"""The screens around Windows itself: 'Starting Windows' with the four lights gathering into the flag, the shutdown
and log-off screens with their spinning ring, and the powered-off PC."""
import math
import zipfile

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from .paths import IMAGES

FRAMES_ZIP = IMAGES / "boot" / "windows7_boot_frames.zip"
FRAME_COUNT = 105
_frames = None


def frames():
    """The 105 frames of the Windows 7 boot animation (200 x 200), loaded once."""
    global _frames
    if _frames is None:
        out = []
        try:
            with zipfile.ZipFile(FRAMES_ZIP) as archive:
                for i in range(FRAME_COUNT):
                    pm = QPixmap()
                    if pm.loadFromData(archive.read(f"activity{i:03d}.bmp"), "BMP"):
                        out.append(pm)
        except (OSError, KeyError, zipfile.BadZipFile):
            out = []
        _frames = out
    return _frames


def sequence(loops=0):
    seq = list(range(FRAME_COUNT))
    for _ in range(loops):
        seq += list(range(103, 59, -1)) + list(range(61, 105))
    return seq


class BootScreen(QWidget):
    """Black, the animation, 'Starting Windows'. Click or press a key to skip."""
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.seq = sequence(0)
        self.pos = 0
        self._done = False
        self.noguiboot = False
        self.safe_mode = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def start(self, safe_mode=False):
        self._done = False
        self.pos = 0
        self.safe_mode = safe_mode
        try:
            from claudexp import startup
            self.noguiboot = startup.boot_flag("NOGUIBOOT")
        except Exception:
            self.noguiboot = False
        self.timer.start(50)

    def _tick(self):
        self.pos += 1
        if self.pos >= len(self.seq):
            self._finish()
            return
        self.update()

    def _finish(self):
        if self._done:
            return
        self._done = True
        self.timer.stop()
        self.finished.emit()

    def mousePressEvent(self, event):
        self._finish()

    def keyPressEvent(self, event):
        self._finish()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        if self.noguiboot:
            return
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        fr = frames()
        cx, cy = self.width() / 2, self.height() / 2 - 38
        if fr:
            pm = fr[self.seq[min(self.pos, len(self.seq) - 1)]]
            p.drawPixmap(QRectF(cx - 100, cy - 100, 200, 200), pm, QRectF(pm.rect()))
        f = QFont("Segoe UI")
        f.setPixelSize(26)
        f.setWeight(QFont.DemiBold)
        p.setFont(f)
        p.setPen(QColor("#F2F4F8"))
        p.drawText(QRectF(0, cy + 128, self.width(), 42), Qt.AlignCenter, "Starting Windows")
        f = QFont("Segoe UI")
        f.setPixelSize(13)
        p.setFont(f)
        p.setPen(QColor("#808080"))
        p.drawText(QRectF(0, self.height() - 44, self.width(), 24), Qt.AlignCenter, "© Microsoft Corporation")


class Ring(QWidget):
    """Windows 7's spinning ring of dots."""

    def __init__(self, parent=None, size=22):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(60)

    def _tick(self):
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.width() / 2
        for i in range(12):
            a = math.radians(self.angle + i * 30)
            alpha = int(255 * (i + 1) / 12)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, alpha))
            d = r * 0.26
            p.drawEllipse(QRectF(r + math.cos(a) * (r - d) - d / 2, r + math.sin(a) * (r - d) - d / 2, d, d))


class ShutdownScreen(QWidget):
    """'Shutting down...', 'Logging off...' or 'Restarting...' over the Windows 7 shutdown background."""
    text = "Shutting down..."

    def __init__(self, parent=None):
        super().__init__(parent)
        self.background = QPixmap(str(IMAGES / "shutdown" / "shutdown-screen.jpg"))
        self.ring = Ring(self)

    def resizeEvent(self, event):
        self._place()

    def showEvent(self, event):
        self._place()

    def _place(self):
        f = QFont("Segoe UI")
        f.setPixelSize(20)
        tw = QFontMetrics(f).horizontalAdvance(self.text)
        x = (self.width() - tw - 34) // 2
        self.ring.move(x, self.height() // 2 - 11)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        if self.background.isNull():
            p.fillRect(self.rect(), QColor("#1F5FA8"))
        else:
            scale = max(self.width() / self.background.width(), self.height() / self.background.height())
            w, h = self.background.width() * scale, self.background.height() * scale
            p.drawPixmap(QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h), self.background,
                         QRectF(self.background.rect()))
        p.fillRect(self.rect(), QColor(0, 0, 0, 60))
        f = QFont("Segoe UI")
        f.setPixelSize(20)
        p.setFont(f)
        p.setPen(QColor(0, 0, 0, 120))
        p.drawText(self.rect().translated(18, 1), Qt.AlignCenter, self.text)
        p.setPen(QColor("white"))
        p.drawText(self.rect().translated(17, 0), Qt.AlignCenter, self.text)


class PoweredOffScreen(QWidget):
    """The PC with the power off: 'It's now safe to turn off your computer' (the PC stays plugged in, so the
    world keeps moving), with the power button, a way out, and the installation DVD."""
    turn_on = Signal()
    exit_app = Signal()
    recovery = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = QPixmap(str(IMAGES / "shutdown" / "shutdown-safe.jpg"))
        style = ("QPushButton { background: black; color: #E8862A; border: 2px solid #E8862A; padding: 6px 18px;"
                 " font-family: 'Lucida Console'; font-size: 15px; }"
                 "QPushButton:hover { background: #2A1606; }"
                 "QPushButton:pressed { background: #E8862A; color: black; }")
        self.on_btn = QPushButton("Power on")
        self.exit_btn = QPushButton("Exit Claude7")
        self.recovery_btn = QPushButton("Reinstall Windows")
        self.recovery_btn.setToolTip("Boot from the Windows 7 DVD and install Windows again")
        for b in (self.on_btn, self.exit_btn, self.recovery_btn):
            b.setStyleSheet(style)
            b.setCursor(Qt.PointingHandCursor)
        self.on_btn.clicked.connect(self.turn_on)
        self.exit_btn.clicked.connect(self.exit_app)
        self.recovery_btn.clicked.connect(self.recovery)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.on_btn)
        row.addSpacing(30)
        row.addWidget(self.exit_btn)
        row.addSpacing(30)
        row.addWidget(self.recovery_btn)
        row.addStretch()
        root = QVBoxLayout(self)
        root.addStretch()
        root.addLayout(row)
        root.setContentsMargins(20, 20, 20, 40)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        if self.image.isNull():
            p.setPen(QColor("#E8862A"))
            f = QFont("Lucida Console")
            f.setPixelSize(28)
            p.setFont(f)
            p.drawText(self.rect(), Qt.AlignCenter, "It's now safe to turn off\nyour computer.")
            return
        scale = min(self.width() / self.image.width(), (self.height() - 80) / self.image.height())
        w, h = self.image.width() * scale, self.image.height() * scale
        p.drawPixmap(QRectF((self.width() - w) / 2, (self.height() - 80 - h) / 2, w, h), self.image,
                     QRectF(self.image.rect()))
