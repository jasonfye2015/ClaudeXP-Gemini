"""The hard-drive activity light in the tray: it flickers whenever the model is working."""
import random

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap

from . import broker
from .tray import TrayIcon

LED_ON = QColor("#3CFF3C")
LED_OFF = QColor("#1E4A1E")


def drive_pixmap(lit):
    pm = QPixmap(16, 16)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    body = QRectF(1.5, 4.5, 13, 8)
    g = QLinearGradient(0, body.top(), 0, body.bottom())
    g.setColorAt(0, QColor("#F2F2F2"))
    g.setColorAt(1, QColor("#A8A8A8"))
    p.setPen(QPen(QColor("#404040"), 1))
    p.setBrush(g)
    p.drawRoundedRect(body, 1.5, 1.5)
    p.setPen(QPen(QColor("#707070"), 1))
    p.drawLine(3, 7, 10, 7)
    p.setPen(Qt.NoPen)
    if lit:
        p.setBrush(QColor(60, 255, 60, 90))
        p.drawEllipse(QRectF(9.5, 7.5, 6, 6))   # glow
    p.setBrush(LED_ON if lit else LED_OFF)
    p.drawEllipse(QRectF(11, 9, 3, 3))
    p.end()
    return pm


class HddLight:
    def __init__(self, desktop):
        self.icons = (QIcon(drive_pixmap(False)), QIcon(drive_pixmap(True)))
        self.tray = TrayIcon(desktop, self.icons[0])
        self.tray.setToolTip("Hard disk: idle")
        self.tray.show()
        self.timer = QTimer()
        self.timer.timeout.connect(self._flicker)
        self.broker = broker.get()
        self.broker.busy_changed.connect(self._busy)

    def _busy(self, busy):
        if busy:
            self.timer.start(70)
        else:
            self.timer.stop()
            self.tray.setIcon(self.icons[0])
            self.tray.setToolTip("Hard disk: idle")

    def _flicker(self):
        # Real disk access is bursty: mostly on, with irregular short gaps.
        self.tray.setIcon(self.icons[random.random() < 0.65])
        n = self.broker.pending()
        self.tray.setToolTip(f"Hard disk: busy ({n} task{'s' if n != 1 else ''})")
