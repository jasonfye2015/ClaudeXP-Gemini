"""His satchel, opened (Tab) - and the little strip of it low on the left. Nothing stops for it: the night goes on while
he rummages (he can't walk while his hands are in it). Each thing lies on the cloth, drawn as itself - the ring catching
the light, the mouse twitching (or not), the moths beating about, the phial glowing - with what he's written beside it:
where it came from, and what she made of it, other times he gave it her.

    icon(p, item, rect, t, state)       a thing, drawn small
    strip(p, W, H, night, t, flying)    the four places low on the left: what's in each, his hand's outlined
    Satchel(view)                       .open / .toggle() / .draw(p, W, H, night, records) / .click(pos) -> item
"""
import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainterPath, QPen, QRadialGradient

from ..game import satchel as S
from ..game.offerings import ITEMS
from . import fonts

SERIF = "Georgia"


def _name(item):
    n = ITEMS[item][0]
    return n[:1].upper() + n[1:]


def icon(p, item, r, t, state=None):
    """A thing, drawn small inside rect r."""
    state = state or {}
    cx, cy, s = r.center().x(), r.center().y(), min(r.width(), r.height())
    p.save()
    p.setRenderHint(p.RenderHint.Antialiasing)
    if item == "ring":
        g = QLinearGradient(QPointF(cx - s * 0.3, cy - s * 0.3), QPointF(cx + s * 0.3, cy + s * 0.3))
        g.setColorAt(0, QColor(240, 240, 250))
        g.setColorAt(0.5, QColor(140, 140, 155))
        g.setColorAt(1, QColor(220, 222, 235))
        p.setPen(QPen(g, s * 0.09))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx, cy), s * 0.25, s * 0.2)
        a = (t * 0.9) % math.tau                                     # (a glint going round it)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 200))
        p.drawEllipse(QPointF(cx + math.cos(a) * s * 0.25, cy + math.sin(a) * s * 0.2), s * 0.035, s * 0.035)
    elif item == "mouse":
        still = state.get("still")
        k = 0.0 if still else math.sin(t * 15)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(110, 98, 92))
        p.save()
        p.translate(cx, cy)
        p.rotate(180 if still else 6 * k)
        p.drawEllipse(QPointF(0, 0), s * 0.26, s * 0.15)
        p.drawEllipse(QPointF(s * 0.24, -s * 0.03), s * 0.11, s * 0.09)
        p.setBrush(QColor(200, 150, 150))
        p.drawEllipse(QPointF(s * 0.22, -s * 0.12), s * 0.045, s * 0.05)
        p.setPen(QPen(QColor(200, 150, 140), s * 0.025))
        path = QPainterPath(QPointF(-s * 0.25, 0))
        path.cubicTo(QPointF(-s * 0.4, s * (0.15 + 0.08 * k)), QPointF(-s * 0.45, -s * 0.1), QPointF(-s * 0.48, s * 0.05))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
        for lx in (-0.12, 0.12):                                     # (legs, kicking)
            p.drawLine(QPointF(s * lx, s * 0.12), QPointF(s * (lx + 0.04 * k), s * (0.22 + 0.04 * k)))
        p.restore()
    elif item == "moths":
        left = state.get("moths", S.MOTHS)
        p.setPen(Qt.NoPen)
        for k in range(left):
            a = t * (1.4 + 0.2 * k) + k * 2.3
            mx, my = cx + math.cos(a) * s * 0.22, cy + math.sin(a * 1.3) * s * 0.18
            flap = abs(math.sin(t * 20 + k))
            p.setBrush(QColor(190, 180, 160, 230))
            p.drawEllipse(QPointF(mx - s * 0.05, my), s * 0.05, s * 0.07 * (0.3 + flap))
            p.drawEllipse(QPointF(mx + s * 0.05, my), s * 0.05, s * 0.07 * (0.3 + flap))
            p.setBrush(QColor(80, 70, 55))
            p.drawEllipse(QPointF(mx, my), s * 0.015, s * 0.04)
    elif item == "honey":
        p.setPen(QPen(QColor(120, 70, 10), s * 0.02))
        for i in range(-1, 2):
            for j in range(-1, 1):
                hx, hy = cx + i * s * 0.16 + (s * 0.08 if j else 0), cy + j * s * 0.14 + s * 0.07
                path = QPainterPath()
                for k in range(6):
                    a = k / 6 * math.tau + math.pi / 6
                    pt = QPointF(hx + math.cos(a) * s * 0.085, hy + math.sin(a) * s * 0.085)
                    path.lineTo(pt) if k else path.moveTo(pt)
                path.closeSubpath()
                g = QRadialGradient(QPointF(hx - s * 0.02, hy - s * 0.02), s * 0.1)
                g.setColorAt(0, QColor(255, 200, 80))
                g.setColorAt(1, QColor(190, 110, 15))
                p.setBrush(g)
                p.drawPath(path)
        drip = (t * 0.25) % 1.0                                       # (a drop, gathering and falling)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(230, 150, 30, int(220 * (1 - drip))))
        p.drawEllipse(QPointF(cx + s * 0.05, cy + s * 0.2 + drip * s * 0.2), s * 0.025, s * 0.035)
    elif item == "string":
        p.setPen(QPen(QColor(225, 210, 170), s * 0.025))
        p.setBrush(Qt.NoBrush)
        path = QPainterPath(QPointF(cx - s * 0.3, cy + s * 0.1))
        for k in range(1, 25):
            a = k / 24 * math.tau * 1.6
            path.lineTo(QPointF(cx - s * 0.3 + k * s * 0.022 + math.cos(a) * s * 0.1, cy + math.sin(a) * s * 0.12))
        p.drawPath(path)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(110, 60, 30))
        p.drawRoundedRect(QRectF(cx + s * 0.2, cy - s * 0.08, s * 0.08, s * 0.2), s * 0.02, s * 0.02)
    elif item == "journal":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(90, 46, 24))
        p.drawRoundedRect(QRectF(cx - s * 0.26, cy - s * 0.3, s * 0.52, s * 0.6), s * 0.03, s * 0.03)
        p.setBrush(QColor(236, 226, 200))
        p.drawRect(QRectF(cx - s * 0.2, cy - s * 0.27, s * 0.44, s * 0.54))
        p.setBrush(QColor(110, 56, 30))
        p.drawRoundedRect(QRectF(cx - s * 0.26, cy - s * 0.3, s * 0.48, s * 0.6), s * 0.03, s * 0.03)
        p.setPen(QPen(QColor(200, 170, 110), s * 0.012))
        p.drawLine(QPointF(cx - s * 0.18, cy - s * 0.2), QPointF(cx + s * 0.14, cy - s * 0.2))
    elif item == "antidote":
        glow = 0.6 + 0.4 * math.sin(t * 2.2)
        g = QRadialGradient(QPointF(cx, cy + s * 0.05), s * 0.45)
        g.setColorAt(0, QColor(120, 255, 140, int(110 * glow)))
        g.setColorAt(1, QColor(120, 255, 140, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(QPointF(cx, cy + s * 0.05), s * 0.45, s * 0.45)
        p.setBrush(QColor(70, 190, 90, 220))
        p.drawEllipse(QPointF(cx, cy + s * 0.08), s * 0.16, s * 0.2)
        p.drawRect(QRectF(cx - s * 0.05, cy - s * 0.2, s * 0.1, s * 0.12))
        p.setBrush(QColor(120, 75, 40))
        p.drawRect(QRectF(cx - s * 0.065, cy - s * 0.27, s * 0.13, s * 0.08))
    p.restore()


def strip(p, W, H, night, t, flying=None):
    """The satchel's four places, low on the left over the health orb - what's in his hand outlined."""
    size, gap = 34.0, 6.0
    r = max(34.0, H * 0.072)
    x0, y0 = 22.0 + 4, H - 22 - 44 - 2 * r - size - 18
    for k in range(S.SLOTS):
        rect = QRectF(x0 + k * (size + gap), y0, size, size)
        p.setPen(QPen(QColor(150, 120, 90, 130), 1))
        p.setBrush(QColor(20, 14, 10, 150))
        p.drawRoundedRect(rect, 5, 5)
        if k < len(night.pack):
            item = night.pack[k]
            if flying and flying[0] == item and t - flying[1] < 0.6:
                continue                                           # (still on its way in)
            icon(p, item, rect.adjusted(3, 3, -3, -3), t, night.items.get(item))
            if night.held == item:
                p.setPen(QPen(QColor(235, 200, 140, 230), 2))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(rect.adjusted(-2, -2, 2, 2), 6, 6)
    if flying and t - flying[1] < 0.6 and flying[0] in night.pack:  # (picked up: into its place)
        k = night.pack.index(flying[0])
        e = (t - flying[1]) / 0.6
        e = e * e * (3 - 2 * e)
        sx, sy = W / 2, H * 0.55
        tx, ty = x0 + k * (size + gap) + size / 2, y0 + size / 2
        x, y = sx + (tx - sx) * e, sy + (ty - sy) * e - math.sin(e * math.pi) * H * 0.08
        sz = 70 * (1 - e) + size * e
        icon(p, flying[0], QRectF(x - sz / 2, y - sz / 2, sz, sz), t, night.items.get(flying[0]))
    held = night.held
    if held:
        f = QFont(SERIF, 9)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(QColor(210, 190, 160, 170))
        p.drawText(QRectF(x0, y0 - 18, 620, 16), Qt.AlignLeft,
                   "In your hand: " + ITEMS[held][0] + "   (wheel to change, G puts it down, Tab the satchel)")


class Satchel:
    """The satchel, opened over the den - the night going on behind it."""

    def __init__(self):
        self.open = False
        self.at = 0.0
        self.rects = []

    def toggle(self):
        self.open = not self.open
        self.at = time.perf_counter()

    def rise(self):
        k = min(1.0, (time.perf_counter() - self.at) / 0.3)
        k = k * k * (3 - 2 * k)
        return k if self.open else 1.0 - k

    def draw(self, p, W, H, night, records):
        k = self.rise()
        if k <= 0.001:
            self.rects = []
            return
        t = time.perf_counter()
        p.save()
        p.fillRect(QRectF(0, 0, W, H), QColor(0, 0, 0, int(110 * k)))
        top = H * (1.0 - 0.62 * k)
        bag = QRectF(W * 0.08, top, W * 0.84, H * 0.6)
        path = QPainterPath()                                          # (the leather: worn, rounded, a flap thrown back)
        path.addRoundedRect(bag, 28, 28)
        g = QLinearGradient(bag.topLeft(), bag.bottomLeft())
        g.setColorAt(0, QColor(92, 58, 34))
        g.setColorAt(1, QColor(52, 30, 18))
        p.setPen(QPen(QColor(30, 16, 8), 3))
        p.setBrush(g)
        p.drawPath(path)
        p.setPen(QPen(QColor(150, 110, 70, 120), 1.5, Qt.DashLine))  # (its stitching)
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(bag.adjusted(10, 10, -10, -10), 20, 20)
        cloth = bag.adjusted(24, 52, -24, -22)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(54, 46, 40))
        p.drawRoundedRect(cloth, 10, 10)
        f = QFont(SERIF, 15)
        p.setFont(f)
        p.setPen(QColor(232, 214, 186))
        p.drawText(QRectF(bag.left(), bag.top() + 14, bag.width(), 30), Qt.AlignHCenter,
                   f"Your satchel  -  {len(night.pack)} of {S.SLOTS}")
        self.rects = []
        w = cloth.width() / S.SLOTS
        for i in range(S.SLOTS):
            cell = QRectF(cloth.left() + i * w + 8, cloth.top() + 10, w - 16, cloth.height() - 20)
            p.setPen(QPen(QColor(90, 76, 64), 1))
            p.setBrush(QColor(62, 52, 46))
            p.drawRoundedRect(cell, 8, 8)
            if i >= len(night.pack):
                f = QFont(SERIF, 10)
                f.setItalic(True)
                p.setFont(f)
                p.setPen(QColor(150, 130, 110, 150))
                p.drawText(cell, Qt.AlignCenter, "(empty)")
                continue
            item = night.pack[i]
            self.rects.append((cell, item))
            if night.held == item:
                p.setPen(QPen(QColor(240, 205, 140), 2.5))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(cell.adjusted(-3, -3, 3, 3), 10, 10)
            ic = QRectF(cell.center().x() - cell.width() * 0.32, cell.top() + 8, cell.width() * 0.64, cell.width() * 0.5)
            icon(p, item, ic, t, night.items.get(item))
            y = ic.bottom() + 6
            p.setFont(fonts.his(records, 12))
            p.setPen(QColor(236, 220, 196))
            p.drawText(QRectF(cell.left() + 8, y, cell.width() - 16, 22), Qt.AlignHCenter, _name(item))
            y += 24
            lines = [S.WHERE.get(item, "")] + self._now(item, night) + records.learned.get(item, [])
            f = QFont(SERIF, 9)
            f.setItalic(True)
            p.setFont(f)
            for j, line in enumerate(lines):
                if not line:
                    continue
                p.setPen(QColor(200, 186, 160) if j == 0 else QColor(222, 196, 140))
                box = p.boundingRect(QRectF(cell.left() + 10, y, cell.width() - 20, 400), Qt.TextWordWrap, line)
                if y + box.height() > cell.bottom() - 22:
                    break
                p.drawText(QRectF(cell.left() + 10, y, cell.width() - 20, box.height()), Qt.TextWordWrap, line)
                y += box.height() + 5
            p.setFont(QFont(SERIF, 8))
            p.setPen(QColor(200, 180, 150, 160))
            p.drawText(QRectF(cell.left(), cell.bottom() - 20, cell.width(), 16), Qt.AlignHCenter,
                       "in your hand" if night.held == item else "click to hold it")
        p.setFont(QFont(SERIF, 10))
        p.setPen(QColor(210, 190, 160, 200))
        p.drawText(QRectF(bag.left(), bag.bottom() - 20, bag.width(), 16), Qt.AlignHCenter,
                   "Tab closes it  -  G puts down what's in your hand  -  the night doesn't wait")
        p.restore()

    @staticmethod
    def _now(item, night):
        st = night.items.get(item, {})
        if item == "mouse":
            return ["Still now. It stopped kicking."] if st.get("still") else ["Kicking, in my fist."]
        if item == "moths":
            n = st.get("moths", S.MOTHS)
            return [f"{n} left - they keep getting out."]
        if item == "honey":
            return ["Sticky. Her small ones can smell it."]
        return []

    def click(self, pos):
        for rect, item in self.rects:
            if rect.contains(pos):
                return item
        return None
