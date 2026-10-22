"""The screens around Windows itself: the ASUS splash with Windows 11's spinning dots under the logo while it boots,
the black 'Restarting' / 'Shutting down' / 'Signing out' screens with the same spinner, and the powered-off PC."""
import math

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from . import bios

BOOT_MS = 5200


def spinner_dots(progress, n=6):
    """Windows 11's progress ring: n dots chasing round the circle, bunching and spreading. Returns the angle of
    each dot (degrees, clockwise from the top) for a cycle position 0..1."""
    angles = []
    for i in range(n):
        t = (progress - i * 0.1) % 1.0
        # ease: fast across the bottom, slow at the top
        eased = t - math.sin(2 * math.pi * t) / (2 * math.pi) * 0.9
        angles.append(eased * 360)
    return angles


def draw_spinner(p, cx, cy, radius, progress, colour=QColor("#FFFFFF"), dot=None):
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    d = dot or max(2.0, radius * 0.17)
    for a in spinner_dots(progress):
        rad = math.radians(a - 90)
        p.setBrush(colour)
        p.drawEllipse(QPointF(cx + math.cos(rad) * radius, cy + math.sin(rad) * radius), d / 2, d / 2)


class BootScreen(QWidget):
    """The splash stays up and the dots start spinning under the Windows logo. Click or press a key to skip."""
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0.0
        self.elapsed = 0
        self._done = False
        self.noguiboot = False
        self.safe_mode = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def start(self, safe_mode=False):
        self._done = False
        self.progress = 0.0
        self.elapsed = 0
        self.safe_mode = safe_mode
        try:
            from claudexp import startup
            self.noguiboot = startup.boot_flag("NOGUIBOOT")
        except Exception:
            self.noguiboot = False
        self.timer.start(33)

    def _tick(self):
        self.elapsed += 33
        self.progress = (self.progress + 33 / 1800) % 1.0
        if self.elapsed >= BOOT_MS:
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
        if self.noguiboot:
            p.fillRect(self.rect(), QColor("black"))
            return
        bios.draw_splash(p, self, with_text=False)
        cx, cy, half = bios.logo_rect(self)
        draw_spinner(p, cx, cy + half * 3.2, half * 0.7, self.progress)
        if self.safe_mode:
            f = QFont("Segoe UI")
            f.setPixelSize(14)
            p.setFont(f)
            p.setPen(QColor("white"))
            for x, y in ((12, 12), (self.width() - 100, 12), (12, self.height() - 30), (self.width() - 100,
                                                                                         self.height() - 30)):
                p.drawText(QRectF(x, y, 90, 20), Qt.AlignLeft, "Safe Mode")


class Ring(QWidget):
    """Windows 11's spinning dots as a small widget."""

    def __init__(self, parent=None, size=28, colour="#FFFFFF"):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.progress = 0.0
        self.colour = QColor(colour)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)

    def _tick(self):
        self.progress = (self.progress + 33 / 1800) % 1.0
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        r = self.width() / 2
        draw_spinner(p, r, r, r * 0.78, self.progress, self.colour, dot=max(2.0, r * 0.22))


class ShutdownScreen(QWidget):
    """Black, the spinner, and 'Shutting down', 'Restarting', 'Signing out' or 'Welcome' under it."""
    text = "Shutting down"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ring = Ring(self, 40)

    def resizeEvent(self, event):
        self._place()

    def showEvent(self, event):
        self._place()

    def _place(self):
        self.ring.move((self.width() - self.ring.width()) // 2, self.height() // 2 - 50)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        f = QFont("Segoe UI")
        f.setPixelSize(17)
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(QRectF(0, self.height() // 2 + 4, self.width(), 30), Qt.AlignCenter, self.text.rstrip("."))


class PoweredOffScreen(QWidget):
    """The PC with the power off: a dark screen, the power button, a way out, and the recovery drive."""
    turn_on = Signal()
    exit_app = Signal()
    recovery = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        style = ("QPushButton { background: #1B1F26; color: #CFD6E0; border: 1px solid #3A4250; border-radius: 6px;"
                 " padding: 8px 20px; font-family: 'Segoe UI'; font-size: 14px; }"
                 "QPushButton:hover { background: #2A313B; border-color: #2D8CEB; }"
                 "QPushButton:pressed { background: #2D8CEB; color: white; }")
        self.on_btn = QPushButton("Power on")
        self.exit_btn = QPushButton("Exit Claude11")
        self.recovery_btn = QPushButton("Reinstall Windows")
        self.recovery_btn.setToolTip("Boot from the Windows 11 installation USB drive and install Windows again")
        for b in (self.on_btn, self.exit_btn, self.recovery_btn):
            b.setStyleSheet(style)
            b.setCursor(Qt.PointingHandCursor)
        self.on_btn.clicked.connect(self.turn_on)
        self.exit_btn.clicked.connect(self.exit_app)
        self.recovery_btn.clicked.connect(self.recovery)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.on_btn)
        row.addSpacing(24)
        row.addWidget(self.exit_btn)
        row.addSpacing(24)
        row.addWidget(self.recovery_btn)
        row.addStretch()
        root = QVBoxLayout(self)
        root.addStretch()
        root.addLayout(row)
        root.setContentsMargins(20, 20, 20, 48)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#07090C"))
        cx, cy = self.width() / 2, self.height() * 0.42
        # a dim power symbol, the standby light of the case
        p.setPen(QColor(45, 140, 235, 90))
        from PySide6.QtGui import QPen
        pen = QPen(QColor(45, 140, 235, 110), 6)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(cx - 60, cy - 60, 120, 120), 60 * 16, 300 * 16)
        p.drawLine(QPointF(cx, cy - 72), QPointF(cx, cy - 10))
        f = QFont("Segoe UI")
        f.setPixelSize(16)
        p.setFont(f)
        p.setPen(QColor("#6B7686"))
        p.drawText(QRectF(0, cy + 90, self.width(), 30), Qt.AlignCenter, "The PC is off. The world keeps going.")
