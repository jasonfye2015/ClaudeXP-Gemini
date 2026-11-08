"""Before the night: between the title and the oak. Begin the night; the endings found (named only once found); the
records of the nights so far; saved nights; unlocks; the options. Old branches reach in from the corners, leaves on
them, webs strung between - and now and then one of her babies runs across it all."""
import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel, QPushButton, QSlider, QStackedWidget, QVBoxLayout,
                               QWidget)

from ..game.records import ENDINGS

SERIF = "Georgia"
STYLE = """
QPushButton#nav { color: #D9C9B0; background: transparent; border: none; border-left: 2px solid transparent;
    padding: 8px 14px; font-family: Georgia; font-size: 16px; text-align: left; }
QPushButton#nav:hover { color: #FFF0DA; border-left: 2px solid #8C6A48; background: rgba(60, 36, 26, 90); }
QPushButton#nav:checked { color: #FFE9C8; border-left: 2px solid #C49A6C; background: rgba(70, 42, 28, 120); }
QPushButton#begin { color: #FFF0DA; background: rgba(70, 30, 22, 200); border: 1px solid #A07A54; border-radius: 4px;
    padding: 11px 26px; font-family: Georgia; font-size: 17px; }
QPushButton#begin:hover { background: rgba(110, 44, 30, 230); }
QLabel { color: #D8CAB4; font-family: Georgia; font-size: 14px; background: transparent; }
QLabel#head { color: #EADCC4; font-size: 22px; }
QCheckBox { color: #D8CAB4; font-family: Georgia; font-size: 14px; spacing: 10px; background: transparent; }
QSlider::groove:horizontal { height: 4px; background: #3A2A20; border-radius: 2px; }
QSlider::handle:horizontal { width: 14px; margin: -6px 0; border-radius: 7px; background: #B08860; }
QSlider::sub-page:horizontal { background: #7A4A30; border-radius: 2px; }
"""


def spider(p, x, y, heading, size, phase):
    """One of her babies, seen from above, legs going: at (x, y), facing `heading` (radians, screen), `size` px long."""
    p.save()
    p.translate(x, y)
    p.rotate(math.degrees(heading) + 90)
    s = size / 2.0
    p.setPen(QPen(QColor(18, 14, 14), max(1.0, s * 0.09), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    for side in (-1, 1):                                         # (eight legs, in two alternating fours)
        for k in range(4):
            gait = math.sin(phase + (k % 2) * math.pi + (0 if side > 0 else math.pi)) * 0.35
            a = math.radians(-60 + k * 38) + gait
            hip = QPointF(side * s * 0.12, -s * 0.18 + k * s * 0.1)
            knee = QPointF(hip.x() + side * math.cos(a) * s * 0.55, hip.y() + math.sin(a) * s * 0.55 - s * 0.12)
            foot = QPointF(knee.x() + side * math.cos(a + 0.5 * side * 0) * s * 0.5,
                           knee.y() + math.sin(a) * s * 0.55 + s * 0.15)
            p.drawPolyline([hip, knee, foot])
    p.setPen(Qt.NoPen)
    g = QRadialGradient(QPointF(-s * 0.06, s * 0.28), s * 0.4)
    g.setColorAt(0, QColor(70, 48, 40))
    g.setColorAt(1, QColor(14, 10, 10))
    p.setBrush(g)
    p.drawEllipse(QPointF(0, s * 0.35), s * 0.3, s * 0.4)          # (the abdomen)
    p.setBrush(QColor(24, 18, 16))
    p.drawEllipse(QPointF(0, -s * 0.12), s * 0.19, s * 0.22)       # (the head and body before it)
    p.setBrush(QColor(230, 40, 25))
    for ex in (-0.07, 0.07):
        p.drawEllipse(QPointF(ex * s, -s * 0.3), s * 0.04, s * 0.04)
    p.restore()


class _Runners(QWidget):
    """Over everything on the screen: the babies running across, now and then."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.rng = random.Random()
        self.runs = []
        self.next = self.rng.uniform(1.5, 4.0)
        self.t = 0.0

    def tick(self, dt):
        self.t += dt
        W, H = self.width(), self.height()
        if self.t >= self.next:
            self.next = self.t + self.rng.uniform(5.0, 12.0)
            for _ in range(2 if self.rng.random() < 0.3 else 1):
                a, b = self.rng.sample(range(4), 2)

                def edge(e):
                    k = self.rng.uniform(0.1, 0.9)
                    return ((-30, k * H), (W + 30, k * H), (k * W, -30), (k * W, H + 30))[e]
                p0, p1 = edge(a), edge(b)
                self.runs.append({"p": list(p0), "to": p1, "speed": self.rng.uniform(140, 300),
                                  "size": self.rng.uniform(14, 30), "phase": 0.0, "rest": 0.0,
                                  "wob": self.rng.uniform(0, 6)})
        keep = []
        for r in self.runs:
            dx, dy = r["to"][0] - r["p"][0], r["to"][1] - r["p"][1]
            d = math.hypot(dx, dy)
            if d < 8:
                continue
            if r["rest"] > 0:
                r["rest"] -= dt
            else:
                h = math.atan2(dy, dx) + 0.35 * math.sin(self.t * 3 + r["wob"])
                r["head"] = h
                step = r["speed"] * dt
                r["p"][0] += math.cos(h) * step
                r["p"][1] += math.sin(h) * step
                r["phase"] += step / r["size"] * 2.6
                if self.rng.random() < dt * 0.5:
                    r["rest"] = self.rng.uniform(0.2, 0.9)                # (a stop: still, and off again)
            keep.append(r)
        self.runs = keep
        self.update()

    def paintEvent(self, _e):
        if not self.runs:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        for r in self.runs:
            spider(p, r["p"][0], r["p"][1], r.get("head", 0.0), r["size"], r["phase"])
        p.end()


class NightMenu(QWidget):
    def __init__(self, shell):
        super().__init__(shell)
        self.shell = shell
        self.rec = shell.records
        self.setStyleSheet(STYLE)
        self.rng = random.Random(7)
        self.leaves = [(self.rng.random(), self.rng.uniform(0.15, 0.95), self.rng.uniform(0, 6.28),
                        self.rng.uniform(0.8, 1.4),
                        self.rng.choice(((122, 78, 34), (140, 92, 40), (96, 84, 38), (150, 64, 30), (84, 70, 34))))
                       for _ in range(46)]
        self.t = 0.0
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(2)
        nav = QVBoxLayout()
        nav.addStretch(3)
        self.pages = QStackedWidget()
        self.pages.setFixedWidth(470)
        self.pages.setStyleSheet("QStackedWidget { background: rgba(10, 7, 8, 190); border: 1px solid #4A3626;"
                                 " border-radius: 6px; }")
        self.buttons = []
        begin = QPushButton("Begin the night")
        begin.setObjectName("begin")
        begin.setCursor(Qt.PointingHandCursor)
        begin.clicked.connect(shell.begin)
        nav.addWidget(begin)
        nav.addSpacing(18)
        for name, page in (("Endings", self._endings()), ("Records", self._records()), ("Saved nights", self._saved()),
                           ("Unlocks", self._unlocks()), ("Options", self._options())):
            b = QPushButton(name)
            b.setObjectName("nav")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            k = self.pages.addWidget(page)
            b.clicked.connect(lambda _c=False, k=k: self._show(k))
            nav.addWidget(b)
            self.buttons.append(b)
        nav.addSpacing(18)
        back = QPushButton("Back to the title")
        back.setObjectName("nav")
        back.setCursor(Qt.PointingHandCursor)
        back.clicked.connect(shell.show_title)
        nav.addWidget(back)
        nav.addStretch(2)
        outer.addLayout(nav)
        outer.addSpacing(36)
        col = QVBoxLayout()
        col.addStretch(3)
        col.addWidget(self.pages)
        col.addStretch(2)
        outer.addLayout(col)
        outer.addStretch(2)
        self._show(0)
        self.runners = _Runners(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)

    def _tick(self):
        self.t += 0.033
        self.runners.tick(0.033)
        if int(self.t * 30) % 3 == 0:
            self.update()

    def resizeEvent(self, e):
        self.runners.setGeometry(self.rect())
        self.runners.raise_()
        super().resizeEvent(e)

    def _show(self, k):
        self.pages.setCurrentIndex(k)
        for i, b in enumerate(self.buttons):
            b.setChecked(i == k)

    # ---- the pages -----------------------------------------------------------------------------------------------
    def _page(self, head, body_html=None):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(28, 22, 28, 22)
        h = QLabel(head)
        h.setObjectName("head")
        lay.addWidget(h)
        lay.addSpacing(8)
        if body_html is not None:
            lab = QLabel(body_html)
            lab.setWordWrap(True)
            lab.setTextFormat(Qt.RichText)
            lay.addWidget(lab)
            lay.addStretch(1)
        return w, lay

    def _endings(self):
        found = self.rec.found
        rows = []
        for k in range(ENDINGS):
            names = sorted(found)
            if k < len(names):
                rows.append(f"<tr><td style='color:#C9A27A; padding:4px 14px 4px 0'>Ending</td><td>{names[k]}</td>"
                            f"<td style='color:#8E7E6C; padding-left:18px'>found {found[names[k]]}</td></tr>")
            else:
                rows.append("<tr><td style='color:#5E5048; padding:4px 14px 4px 0'>Ending</td>"
                            "<td style='color:#5E5048'>? ? ?</td><td></td></tr>")
        html = (f"<p>{len(found)} of {ENDINGS} found.</p><table>{''.join(rows)}</table>"
                "<p style='color:#8E7E6C'><i>Each night ends one way or another. Some ways are easier to come by than"
                " others.</i></p>")
        return self._page("Endings", html)[0]

    def _records(self):
        t = self.rec.totals

        def hm(s):
            return f"{s // 3600}h {s % 3600 // 60:02d}m" if s >= 3600 else f"{s // 60}m {s % 60:02d}s"
        rows = (("Nights begun and ended", t["nights"]), ("Endings reached", t["endings"]),
                ("Time in the oak", hm(t["seconds"])), ("The longest night", hm(t["longest"])),
                ("Bitten", t["bites"]), ("Slipped from the silk", t["slips"]), ("Hard falls", t["falls"]),
                ("Swiped from your face", t["swipes"]), ("The lantern shaken", t["shakes"]))
        html = "<table>" + "".join(f"<tr><td style='padding:3px 30px 3px 0'>{a}</td><td style='color:#E8C9A0'>{b}</td></tr>"
                                   for a, b in rows) + "</table>"
        return self._page("Records", html)[0]

    def _saved(self):
        return self._page("Saved nights", "<p>No saved nights.</p><p style='color:#8E7E6C'><i>For now a night is played"
                                          " through in one sitting. Saving part-way will come.</i></p>")[0]

    def _unlocks(self):
        have = self.rec.unlocks
        html = ("".join(f"<p>{u}</p>" for u in have) if have else
                "<p>Nothing yet.</p><p style='color:#8E7E6C'><i>Some things are only found at the end of a night.</i></p>")
        return self._page("Unlocks", html)[0]

    def _options(self):
        w, lay = self._page("Options")
        o = self.rec.options

        def slider(label, key):
            lay.addWidget(QLabel(label))
            s = QSlider(Qt.Horizontal)
            s.setRange(0, 100)
            s.setValue(int(o[key]))
            s.valueChanged.connect(lambda v, key=key: self._set(key, v))
            lay.addWidget(s)
            lay.addSpacing(10)
        slider("Volume", "volume")
        slider("Looking about (mouse speed)", "look")
        for label, key in (("The heart monitor", "heart"), ("The heartbeat, heard", "heartbeat"),
                           ("The orbs", "orbs")):
            c = QCheckBox(label)
            c.setChecked(bool(o[key]))
            c.toggled.connect(lambda v, key=key: self._set(key, bool(v)))
            lay.addWidget(c)
        lay.addStretch(1)
        return w

    def _set(self, key, value):
        self.rec.options[key] = value
        self.rec.save()

    # ---- the dressing: branches, leaves, webs ---------------------------------------------------------------------
    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        g = QLinearGradient(0, 0, 0, H)
        g.setColorAt(0, QColor(4, 3, 5, 205))
        g.setColorAt(1, QColor(2, 1, 2, 235))
        p.fillRect(self.rect(), g)
        sway = math.sin(self.t * 0.6) * 2.0
        branches = (((0, 0.05), (0.18, 0.12), (0.3, 0.02), (0.42, 0.08), 26),
                    ((1, 0.0), (0.85, 0.16), (0.74, 0.05), (0.6, 0.12), 30),
                    ((0, 0.92), (0.12, 0.78), (0.22, 0.9), (0.33, 0.83), 22),
                    ((1, 0.95), (0.9, 0.8), (0.82, 0.92), (0.7, 0.86), 24),
                    ((0.18, 0.12), (0.2, 0.25), (0.14, 0.3), (0.16, 0.4), 9),
                    ((0.85, 0.16), (0.84, 0.3), (0.9, 0.36), (0.88, 0.46), 10))
        tips = []
        for (a, b, c, d, thick) in branches:                       # (old branches reaching in, tapering)
            pts = [QPointF(x * W, y * H + sway * (0.2 + x)) for x, y in (a, b, c, d)]
            for width, col in ((thick, QColor(16, 11, 8)), (thick * 0.62, QColor(42, 29, 20)), (thick * 0.22, QColor(64, 46, 32))):
                path = QPainterPath(pts[0])
                path.cubicTo(pts[1], pts[2], pts[3])
                p.setPen(QPen(col, width, Qt.SolidLine, Qt.RoundCap))
                p.drawPath(path)
            tips.append(pts)
        for u, v, turn, sc, col in self.leaves:                   # (leaves along them, a few turning)
            pts = tips[int(u * len(tips)) % len(tips)]
            k = v
            x = ((1 - k) ** 3 * pts[0].x() + 3 * (1 - k) ** 2 * k * pts[1].x() + 3 * (1 - k) * k * k * pts[2].x()
                 + k ** 3 * pts[3].x())
            y = ((1 - k) ** 3 * pts[0].y() + 3 * (1 - k) ** 2 * k * pts[1].y() + 3 * (1 - k) * k * k * pts[2].y()
                 + k ** 3 * pts[3].y())
            self._leaf(p, x, y, turn + 0.15 * math.sin(self.t * 0.9 + turn * 3), 22 * sc, QColor(*col))
        for cx, cy, r, turn in ((0.3 * W, 0.06 * H, 0.15 * H, 0.3), (0.75 * W, 0.1 * H, 0.17 * H, 1.1),
                                (0.2 * W, 0.86 * H, 0.12 * H, 2.0), (0.86 * W, 0.86 * H, 0.13 * H, 0.7)):
            self._web(p, cx, cy, r, turn)
        f = QFont(SERIF, 34)
        f.setLetterSpacing(QFont.PercentageSpacing, 110)
        p.setFont(f)
        p.setPen(QColor(232, 220, 200))
        p.drawText(QRectF(0, H * 0.1, W, 60), Qt.AlignHCenter, "Before the night")
        f2 = QFont(SERIF, 13)
        f2.setItalic(True)
        p.setFont(f2)
        p.setPen(QColor(180, 166, 148))
        p.drawText(QRectF(0, H * 0.1 + 58, W, 30), Qt.AlignHCenter, "The invitation is in your hand. The oak is waiting.")
        p.end()

    def _leaf(self, p, x, y, turn, size, col):
        """An oak leaf on its stalk: lobed edges along a rib."""
        p.save()
        p.translate(x, y)
        p.rotate(math.degrees(turn))
        path = QPainterPath(QPointF(0, 0))
        lobes = 4
        top = [QPointF(size * (0.2 + 0.8 * k / lobes), -size * (0.18 + 0.12 * math.sin(k * math.pi / lobes)))
               for k in range(lobes + 1)]
        path.moveTo(size * 0.15, 0)
        for k in range(lobes):                                   # (one side: rounded lobes)
            a, b = top[k], top[k + 1]
            path.quadTo(QPointF((a.x() + b.x()) / 2, a.y() - size * 0.16), b)
            if k < lobes - 1:
                path.lineTo(b.x() - size * 0.03, b.y() * 0.45)
        path.lineTo(size * 1.08, 0)
        for k in range(lobes, 0, -1):                            # (and back along the other)
            a, b = QPointF(top[k].x(), -top[k].y()), QPointF(top[k - 1].x(), -top[k - 1].y())
            path.quadTo(QPointF((a.x() + b.x()) / 2, a.y() + size * 0.16), b)
            if k > 1:
                path.lineTo(b.x() + size * 0.03, b.y() * 0.45)
        path.closeSubpath()
        p.setPen(QPen(col.darker(170), 0.8))
        p.setBrush(QBrush(col))
        p.drawPath(path)
        p.setPen(QPen(col.lighter(135), 0.9))
        p.drawLine(QPointF(-size * 0.12, 0), QPointF(size * 0.95, 0))
        p.restore()

    def _web(self, p, cx, cy, r, turn):
        p.setBrush(Qt.NoBrush)
        spokes = 13
        jag = [0.7 + 0.3 * abs(math.sin(turn * 5 + i * 1.7)) for i in range(spokes)]
        p.setPen(QPen(QColor(220, 225, 235, 60), 1.0))
        for i in range(spokes):
            a = turn + i / spokes * math.tau
            p.drawLine(QPointF(cx, cy), QPointF(cx + math.cos(a) * r * jag[i], cy + math.sin(a) * r * jag[i]))
        path = QPainterPath()
        for i in range(spokes * 7):
            a = turn + i / spokes * math.tau
            f = (0.12 + 0.86 * i / (spokes * 7)) * jag[i % spokes]
            pt = QPointF(cx + math.cos(a) * r * f, cy + math.sin(a) * r * f + 1.5 * math.sin(self.t * 0.8 + i * 0.05))
            path.lineTo(pt) if i else path.moveTo(pt)
        p.setPen(QPen(QColor(220, 225, 235, 45), 0.9))
        p.drawPath(path)
