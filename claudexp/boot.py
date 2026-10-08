"""The black Windows XP boot screen with the sliding progress chunk."""
from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PySide6.QtWidgets import QWidget

from .paths import pixmap

# Inside of the empty progress bar, in winXP_boot.jpg pixel coordinates.
BAR = QRectF(88, 539, 364, 26)


class BootScreen(QWidget):
    finished = Signal()

    def __init__(self, duration_ms=5000, parent=None):
        super().__init__(parent)
        self.logo = pixmap("winXP_boot.jpg")
        self.chunk = pixmap("windowsxp_progress.jpg")
        self.duration_ms = duration_ms
        self.chunk_h = BAR.height() - 4
        self.chunk_w = self.chunk.width() * self.chunk_h / max(1, self.chunk.height())
        self.offset = -self.chunk_w
        self._done = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def start(self):
        self._done = False
        self.offset = -self.chunk_w
        self.timer.start(30)
        QTimer.singleShot(self.duration_ms, self._finish)

    def _tick(self):
        self.offset += 4
        if self.offset > BAR.width():
            self.offset = -self.chunk_w
        self.update()

    def _finish(self):
        if self._done:
            return
        self._done = True
        self.timer.stop()
        self.finished.emit()

    def mousePressEvent(self, event):
        self._finish()  # click to skip

    def keyPressEvent(self, event):
        self._finish()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        if self.logo.isNull():
            return
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        s = min(self.width() / self.logo.width(), self.height() / self.logo.height()) * 0.85
        w, h = self.logo.width() * s, self.logo.height() * s
        x, y = (self.width() - w) / 2, (self.height() - h) / 2
        p.drawPixmap(QRectF(x, y, w, h), self.logo, QRectF(self.logo.rect()))

        bar = QRectF(x + BAR.x() * s, y + BAR.y() * s, BAR.width() * s, BAR.height() * s)
        p.setClipRect(bar)
        chunk = QRectF(bar.x() + self.offset * s, bar.y() + 2 * s,
                       self.chunk_w * s, self.chunk_h * s)
        p.drawPixmap(chunk, self.chunk, QRectF(self.chunk.rect()))


class ShutdownScreen(QWidget):
    """The plain blue 'Windows is shutting down...' screen."""

    def paintEvent(self, event):
        p = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor("#5A7EDC"))
        grad.setColorAt(1, QColor("#3557C4"))
        p.fillRect(self.rect(), grad)
        font = QFont("Trebuchet MS", 16)
        font.setBold(True)
        p.setFont(font)
        p.setPen(QColor("#1E3A8A"))
        p.drawText(self.rect().translated(1, 1), Qt.AlignCenter, "Windows is shutting down...")
        p.setPen(QColor("white"))
        p.drawText(self.rect(), Qt.AlignCenter, "Windows is shutting down...")
