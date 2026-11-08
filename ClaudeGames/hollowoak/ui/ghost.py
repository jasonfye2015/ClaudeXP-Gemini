"""The letter's hand: while it leads him, a ghost of a cursor - large, brown, dripping her venom - glides to what it's
chosen, rests on it a moment, and presses it. So the player sees what was picked, and has time to read it.

    ghost = Ghost(parent)
    ghost.go(point, then)       glide to point (parent's coordinates), rest, press: then()
    ghost.busy
"""
import math
import random
import time

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget

GLIDE, REST = 0.9, 0.55
SIZE = 3.0                        # (how much larger than a cursor)


class Ghost(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(parent.rect())
        self.pos = QPointF(parent.width() * 0.72, parent.height() * 0.62)
        self.start, self.target, self.then = self.pos, None, None
        self.t0 = 0.0
        self.pressed = 0.0
        self.drips = []
        self.next_drip = 0.0
        self.rng = random.Random(7)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)
        self.show()
        self.raise_()

    @property
    def busy(self):
        return self.target is not None

    def go(self, point, then):
        self.setGeometry(self.parent().rect())
        self.start, self.target, self.then = QPointF(self.pos), QPointF(point), then
        self.t0 = time.perf_counter()
        self.raise_()

    def _tick(self):
        now = time.perf_counter()
        if self.target is not None:
            k = min(1.0, (now - self.t0) / GLIDE)
            e = k * k * (3 - 2 * k)
            arc = math.sin(e * math.pi) * 40.0                             # (a little arc, not a straight line)
            self.pos = QPointF(self.start.x() + (self.target.x() - self.start.x()) * e,
                               self.start.y() + (self.target.y() - self.start.y()) * e - arc)
            if now - self.t0 >= GLIDE + REST:
                self.pressed = now
                then, self.target, self.then = self.then, None, None
                if then is not None:
                    then()
        if now >= self.next_drip:                                          # (her venom, gathering at its tip)
            self.next_drip = now + self.rng.uniform(0.35, 0.9)
            self.drips.append([self.pos.x() + self.rng.uniform(-3, 5), self.pos.y() + 6, 0.0, now,
                               self.rng.uniform(2.2, 3.6)])
        for d in self.drips:
            d[2] += 260 * 0.016
            d[1] += d[2] * 0.016
        self.drips = [d for d in self.drips if now - d[3] < 1.4]
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        now = time.perf_counter()
        x, y = self.pos.x(), self.pos.y()
        press = max(0.0, 1.0 - (now - self.pressed) / 0.25)
        if press > 0:                                                      # (pressed: a ring of venom)
            r = 14 + 30 * (1 - press)
            p.setPen(QPen(QColor(110, 220, 90, int(200 * press)), 3))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(x, y), r, r)
        for dx, dy, _v, born, rad in self.drips:                           # (drops, falling)
            a = max(0.0, 1.0 - (now - born) / 1.4)
            g = QRadialGradient(QPointF(dx - rad * 0.3, dy - rad * 0.3), rad * 1.4)
            g.setColorAt(0, QColor(190, 255, 150, int(240 * a)))
            g.setColorAt(1, QColor(50, 150, 40, int(200 * a)))
            p.setPen(Qt.NoPen)
            p.setBrush(g)
            p.drawEllipse(QPointF(dx, dy), rad * 0.85, rad * 1.15)
        s = SIZE * (1.0 - 0.12 * press)
        arrow = [(0, 0), (0, 17), (4.2, 13.2), (7.2, 20), (10, 18.8), (7.1, 12.3), (12.5, 12.3)]
        path = QPainterPath(QPointF(x, y))
        for ax, ay in arrow[1:]:
            path.lineTo(QPointF(x + ax * s, y + ay * s))
        path.closeSubpath()
        g = QLinearGradient(QPointF(x, y), QPointF(x + 10 * s, y + 20 * s))
        g.setColorAt(0, QColor(150, 98, 56, 235))
        g.setColorAt(1, QColor(84, 50, 26, 235))
        p.setPen(QPen(QColor(30, 16, 8, 230), 2.2))
        p.setBrush(g)
        p.drawPath(path)
        wet = QPainterPath(QPointF(x + 1.5 * s, y + 3 * s))                # (venom running down its edge)
        wet.cubicTo(QPointF(x + 1.2 * s, y + 7 * s), QPointF(x + 2.6 * s, y + 9 * s),
                    QPointF(x + 1.8 * s, y + (12 + 1.5 * math.sin(now * 2.3)) * s))
        p.setPen(QPen(QColor(120, 230, 90, 210), 2.6, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawPath(wet)
        g = QRadialGradient(QPointF(x, y + 2), 7)                          # (a bead of it, at the tip)
        g.setColorAt(0, QColor(200, 255, 160, 240))
        g.setColorAt(1, QColor(60, 160, 40, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(QPointF(x, y + 2), 7, 7)
        p.end()
