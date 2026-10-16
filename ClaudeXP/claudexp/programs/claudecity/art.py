"""ClaudeCity's art, painted in code in the style of SimCity Classic: brown land, water, trees, roads, rail and power
lines that join up with their neighbours (bridges over water), parks, rubble, R/C/I zones from empty lots to
skyscrapers, and the big buildings. Everything is drawn for a tile size t (16, 24 or 32 pixels) and cached by
the screen.
"""
import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF

LAND_C, WATER_C = "#9C7A4E", "#2E62B8"
ZONE_C = {"res": "#4CB04C", "com": "#4C7CD8", "ind": "#D8C040"}
N, E, S, W = 1, 2, 4, 8


def _pm(w, h):
    pm = QPixmap(int(w), int(h))
    pm.fill(Qt.transparent)
    return pm


def land(t, variant, terrain):
    """A plain tile: dirt, water or trees."""
    pm = _pm(t, t)
    p = QPainter(pm)
    rnd = random.Random(variant * 31 + terrain)
    if terrain == 1:
        p.fillRect(0, 0, int(t), int(t), QColor(WATER_C))
        p.setPen(QPen(QColor("#5A8AD8"), max(1.0, t / 16)))
        for _ in range(2):
            x, y = rnd.uniform(0, t * 0.7), rnd.uniform(0, t)
            p.drawLine(QPointF(x, y), QPointF(x + t * 0.25, y))
    else:
        p.fillRect(0, 0, int(t), int(t), QColor(LAND_C))
        for _ in range(int(t * 0.8)):
            p.setPen(QColor(rnd.choice(["#8C6A40", "#AC8A5C", "#94744A"])))
            p.drawPoint(rnd.randrange(int(t)), rnd.randrange(int(t)))
        if terrain == 2:
            p.setRenderHint(QPainter.Antialiasing)
            for _ in range(3):
                cx, cy = rnd.uniform(t * 0.2, t * 0.8), rnd.uniform(t * 0.2, t * 0.8)
                r = rnd.uniform(t * 0.22, t * 0.34)
                p.setPen(QPen(QColor("#103A10"), 1))
                p.setBrush(QColor(rnd.choice(["#1E6A1E", "#2A7A26", "#185A18"])))
                p.drawEllipse(QPointF(cx, cy), r, r)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 255, 255, 40))
                p.drawEllipse(QPointF(cx - r * 0.3, cy - r * 0.3), r * 0.35, r * 0.35)
    p.end()
    return pm


def network(kind, mask, t, on_water=False):
    """Road / rail / wire / crossings, joined toward the neighbours in mask (N E S W bits)."""
    pm = _pm(t, t)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(0, 0, int(t), int(t), QColor(WATER_C if on_water else LAND_C))
    if not on_water:
        rnd = random.Random(mask)
        for _ in range(int(t * 0.5)):
            p.setPen(QColor(rnd.choice(["#8C6A40", "#AC8A5C"])))
            p.drawPoint(rnd.randrange(int(t)), rnd.randrange(int(t)))
    c = t / 2
    if mask == 0:
        mask = E | W
    arms = [(N, (c, 0)), (E, (t, c)), (S, (c, t)), (W, (0, c))]
    parts = kind.split("_")
    if "road" in parts:
        w = t * 0.7
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#5A5A5E"))
        p.drawRect(QRectF(c - w / 2, c - w / 2, w, w))
        for bit, (x, y) in arms:
            if mask & bit:
                if bit in (N, S):
                    p.drawRect(QRectF(c - w / 2, min(y, c), w, abs(y - c)))
                else:
                    p.drawRect(QRectF(min(x, c), c - w / 2, abs(x - c), w))
        p.setPen(QPen(QColor("#E8E8E8"), max(1.0, t / 18), Qt.DashLine))
        straight_ns = mask & (N | S) and not mask & (E | W)
        straight_ew = mask & (E | W) and not mask & (N | S)
        if straight_ns:
            p.drawLine(QPointF(c, 0), QPointF(c, t))
        elif straight_ew:
            p.drawLine(QPointF(0, c), QPointF(t, c))
        if on_water:                                    # bridge railings
            p.setPen(QPen(QColor("#C8C8CC"), max(1.0, t / 12)))
            if mask & (N | S):
                p.drawLine(QPointF(c - w / 2, 0), QPointF(c - w / 2, t))
                p.drawLine(QPointF(c + w / 2, 0), QPointF(c + w / 2, t))
            else:
                p.drawLine(QPointF(0, c - w / 2), QPointF(t, c - w / 2))
                p.drawLine(QPointF(0, c + w / 2), QPointF(t, c + w / 2))
    if "rail" in parts:
        rmask = mask if "road" not in parts else ((N | S) if not (mask & (N | S)) else (E | W))
        if "road" in parts:
            rmask = (E | W) if (mask & (N | S)) else (N | S)
        p.setPen(QPen(QColor("#6A4A2A"), max(1.5, t / 8)))
        for bit, (x, y) in arms:
            if rmask & bit:
                n = 3
                for i in range(n):
                    f = (i + 0.5) / n
                    px, py = c + (x - c) * f, c + (y - c) * f
                    if bit in (N, S):
                        p.drawLine(QPointF(c - t * 0.28, py), QPointF(c + t * 0.28, py))
                    else:
                        p.drawLine(QPointF(px, c - t * 0.28), QPointF(px, c + t * 0.28))
        p.setPen(QPen(QColor("#9A9AA4"), max(1.0, t / 14)))
        for bit, (x, y) in arms:
            if rmask & bit:
                if bit in (N, S):
                    for off in (-t * 0.16, t * 0.16):
                        p.drawLine(QPointF(c + off, c), QPointF(c + off, y))
                else:
                    for off in (-t * 0.16, t * 0.16):
                        p.drawLine(QPointF(c, c + off), QPointF(x, c + off))
    if "wire" in parts:
        wmask = mask
        if len(parts) > 1:
            wmask = (E | W) if (mask & (N | S)) else (N | S)
        p.setPen(QPen(QColor("#202020"), max(1.0, t / 20)))
        for bit, (x, y) in arms:
            if wmask & bit:
                for off in (-t * 0.12, t * 0.12):
                    if bit in (N, S):
                        p.drawLine(QPointF(c + off, c), QPointF(c + off, y))
                    else:
                        p.drawLine(QPointF(c, c + off), QPointF(x, c + off))
        p.setPen(QPen(QColor("#6A4A2A"), max(1.5, t / 9)))
        p.drawLine(QPointF(c - t * 0.18, c), QPointF(c + t * 0.18, c))
        p.setBrush(QColor("#4A3018"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(c, c), t * 0.08, t * 0.08)
    p.end()
    return pm


def misc(kind, t, variant=0):
    pm = _pm(t, t)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    rnd = random.Random(variant + hash(kind) % 1000)
    if kind == "park":
        p.fillRect(0, 0, int(t), int(t), QColor("#3E9A3A"))
        for _ in range(2):
            cx, cy = rnd.uniform(t * 0.25, t * 0.75), rnd.uniform(t * 0.25, t * 0.75)
            p.setPen(QPen(QColor("#184A18"), 1))
            p.setBrush(QColor("#1E6A1E"))
            p.drawEllipse(QPointF(cx, cy), t * 0.2, t * 0.2)
        if variant % 3 == 0:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#60A0E0"))
            p.drawEllipse(QPointF(t * 0.7, t * 0.7), t * 0.12, t * 0.12)
    elif kind == "rubble":
        p.fillRect(0, 0, int(t), int(t), QColor(LAND_C))
        for _ in range(int(t * 0.6)):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(rnd.choice(["#7A7A7E", "#9A9AA0", "#5A5A5E", "#8A6A4A"])))
            s = rnd.uniform(t * 0.06, t * 0.16)
            p.drawRect(QRectF(rnd.uniform(0, t - s), rnd.uniform(0, t - s), s, s))
    elif kind == "flood":
        p.fillRect(0, 0, int(t), int(t), QColor("#3A72C8"))
        p.setPen(QPen(QColor("#6A9AE0"), 1))
        p.drawLine(QPointF(t * 0.2, t * 0.4), QPointF(t * 0.6, t * 0.4))
    p.end()
    return pm


def fire(t, frame):
    pm = _pm(t, t)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(0, 0, int(t), int(t), QColor("#3A2A1A"))
    fl = [0.0, 0.15, 0.05, 0.2][frame % 4]
    for col, sc in (("#E03A10", 1.0), ("#F8A020", 0.7), ("#FFE070", 0.4)):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(col))
        h = t * (0.85 + fl) * sc
        p.drawPolygon(QPolygonF([QPointF(t * 0.15, t), QPointF(t * 0.3, t - h * 0.7), QPointF(t * 0.5, t - h),
                                 QPointF(t * 0.7, t - h * 0.65), QPointF(t * 0.85, t)]))
    p.end()
    return pm


# ---- buildings -------------------------------------------------------------------------------------------------

def _box(p, x, y, w, h, roof, wall, depth):
    """A little 3/4-view block: front wall below a roof."""
    p.setPen(QPen(QColor(0, 0, 0, 150), 1))
    p.setBrush(QColor(wall))
    p.drawRect(QRectF(x, y + h - depth, w, depth))
    p.setBrush(QColor(roof))
    p.drawRect(QRectF(x, y, w, h - depth))


def _windows(p, x, y, w, h, colour, step):
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(colour))
    yy = y + step * 0.4
    while yy < y + h - step * 0.6:
        xx = x + step * 0.35
        while xx < x + w - step * 0.5:
            p.drawRect(QRectF(xx, yy, step * 0.35, step * 0.35))
            xx += step * 0.7
        yy += step * 0.7


def zone(kind, level, variant, t, powered=True):
    """A 3x3 zone, from an empty lot (with its letter) to its densest building."""
    size = 3 * t
    pm = _pm(size, size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    rnd = random.Random(variant * 7 + level * 13 + hash(kind) % 97)
    zc = QColor(ZONE_C[kind])
    p.fillRect(0, 0, int(size), int(size), QColor(LAND_C))
    if level == 0:
        p.fillRect(QRectF(1, 1, size - 2, size - 2), zc.lighter(150))
        p.setPen(QPen(zc.darker(150), max(1.0, t / 10)))
        p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(1, 1, size - 2, size - 2))
        p.setFont(QFont("Arial", int(t * 1.3), QFont.Bold))
        p.setPen(zc.darker(170))
        p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, kind[0].upper())
    elif kind == "res":
        _res(p, level, t, size, rnd)
    elif kind == "com":
        _com(p, level, t, size, rnd)
    else:
        _ind(p, level, t, size, rnd)
    if not powered and level >= 0:
        _bolt(p, size / 2, size / 2, t)
    p.end()
    return pm


def _bolt(p, cx, cy, t):
    p.setPen(QPen(QColor("#202020"), 1))
    p.setBrush(QColor("#FFE020"))
    s = t * 0.5
    p.drawPolygon(QPolygonF([QPointF(cx + s * 0.2, cy - s * 1.2), QPointF(cx - s * 0.6, cy + s * 0.1),
                             QPointF(cx - s * 0.05, cy + s * 0.1), QPointF(cx - s * 0.3, cy + s * 1.2),
                             QPointF(cx + s * 0.6, cy - s * 0.2), QPointF(cx + s * 0.05, cy - s * 0.2)]))


def _res(p, level, t, size, rnd):
    p.fillRect(QRectF(1, 1, size - 2, size - 2), QColor("#5A9A3A"))
    roofs = ["#B03A2A", "#8A4A2A", "#5A5A6A", "#A06A3A", "#3A5A8A"]
    if level <= 2:
        n = 4 if level == 1 else 8
        spots = [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)][:n]
        if level == 1:
            spots = [(0, 0), (2, 0), (0, 2), (2, 2)]
        for gx, gy in spots:
            x, y = gx * t + t * 0.15, gy * t + t * 0.15
            _box(p, x, y, t * 0.7, t * 0.7, rnd.choice(roofs), "#E8DCC0", t * 0.22)
            p.setPen(QPen(QColor(0, 0, 0, 90), 1))
            p.drawLine(QPointF(x, y + t * 0.24), QPointF(x + t * 0.7, y + t * 0.24))
        if level == 1:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#2A6A26"))
            p.drawEllipse(QPointF(size / 2, size / 2), t * 0.3, t * 0.3)
    elif level <= 4:
        blocks = 2 if level == 3 else 1
        if blocks == 2:
            for i in range(2):
                x = t * 0.2 + i * size / 2
                _box(p, x, t * 0.3, size / 2 - t * 0.4, size - t * 0.6, "#8A7A6A", "#C8B8A0", t * 0.5)
                _windows(p, x, t * 0.3 + size - t * 0.6 - t * 0.5, size / 2 - t * 0.4, t * 0.5, "#F0E890", t * 0.5)
        else:
            _box(p, t * 0.2, t * 0.2, size - t * 0.4, size - t * 0.4, "#9A8A7A", "#D0C0A8", t * 0.8)
            _windows(p, t * 0.2, size - t * 0.2 - t * 0.8, size - t * 0.4, t * 0.8, "#F0E890", t * 0.45)
    else:
        _box(p, t * 0.3, t * 0.15, size - t * 0.6, size - t * 0.3, "#6A6A7A", "#B8B8C8", t * 1.3)
        _windows(p, t * 0.3, size - t * 0.15 - t * 1.3, size - t * 0.6, t * 1.3, "#F8F0A0", t * 0.4)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#4A4A5A"))
        p.drawRect(QRectF(size / 2 - t * 0.3, t * 0.4, t * 0.6, t * 0.4))


def _com(p, level, t, size, rnd):
    p.fillRect(QRectF(1, 1, size - 2, size - 2), QColor("#7A7A7E"))
    if level <= 2:
        n = 3 if level == 1 else 5
        for i in range(n):
            gx, gy = [(0, 0), (1.5, 0), (0, 1.5), (1.5, 1.5), (0.75, 0.75)][i]
            x, y = gx * t + t * 0.15, gy * t + t * 0.15
            _box(p, x, y, t * 1.2, t * 1.2, rnd.choice(["#5A7AB8", "#7A5A9A", "#A85A3A", "#3A8A8A"]), "#E0E0E8",
                 t * 0.35)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(rnd.choice(["#F04040", "#40C040", "#F0C030"])))
            p.drawRect(QRectF(x, y + t * 1.2 - t * 0.35, t * 1.2, t * 0.1))
    elif level <= 4:
        _box(p, t * 0.25, t * 0.25, size - t * 0.5, size - t * 0.5, "#4A6AA8", "#A8B8D8", t * (0.7 + 0.3 * level / 4))
        _windows(p, t * 0.25, size - t * 0.25 - t, size - t * 0.5, t, "#C8E0FF", t * 0.4)
    else:
        _box(p, t * 0.5, t * 0.1, size - t, size - t * 0.2, "#3A5A98", "#98B0D8", t * 1.5)
        _windows(p, t * 0.5, size - t * 0.1 - t * 1.5, size - t, t * 1.5, "#D8ECFF", t * 0.35)
        p.setPen(QPen(QColor("#E0E0E0"), max(1.0, t / 12)))
        p.drawLine(QPointF(size / 2, t * 0.1), QPointF(size / 2, -t * 0.0))


def _ind(p, level, t, size, rnd):
    p.fillRect(QRectF(1, 1, size - 2, size - 2), QColor("#8A7A5A"))
    if level == 1:
        _box(p, t * 0.3, t * 0.6, size - t * 0.6, size - t * 1.2, "#8A8A90", "#B0A890", t * 0.4)
    elif level == 2:
        _box(p, t * 0.2, t * 0.3, size - t * 0.4, size - t * 0.6, "#7A7A80", "#A89880", t * 0.5)
        p.setPen(QPen(QColor(0, 0, 0, 80), 1))
        for i in range(1, 4):
            x = t * 0.2 + i * (size - t * 0.4) / 4
            p.drawLine(QPointF(x, t * 0.3), QPointF(x, size - t * 0.3 - t * 0.5))
    else:
        _box(p, t * 0.15, t * 0.5, size - t * 0.3, size - t * 0.7, "#6A6A70", "#9A8A70", t * 0.6)
        for i in range(level - 1):
            x = t * 0.5 + i * t * 0.9
            p.setPen(QPen(QColor(0, 0, 0, 150), 1))
            p.setBrush(QColor("#A04030"))
            p.drawRect(QRectF(x, t * 0.05, t * 0.35, t * 0.9))
            p.setBrush(QColor("#E8E8E8"))
            p.drawRect(QRectF(x, t * 0.25, t * 0.35, t * 0.12))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#C8A020"))
    p.drawRect(QRectF(size - t * 0.7, size - t * 0.5, t * 0.4, t * 0.3))


def special(kind, t, powered=True):
    size = {"police": 3, "fire": 3, "stadium": 4, "seaport": 4, "coal": 4, "nuclear": 4, "airport": 6}[kind] * t
    pm = _pm(size, size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(0, 0, int(size), int(size), QColor(LAND_C))
    if kind in ("police", "fire"):
        p.fillRect(QRectF(1, 1, size - 2, size - 2), QColor("#9A9AA0"))
        roof = "#3A5AB8" if kind == "police" else "#C83A2A"
        _box(p, t * 0.3, t * 0.3, size - t * 0.6, size - t * 1.0, roof, "#E8E4D8", t * 0.6)
        if kind == "fire":
            p.setPen(QPen(QColor("#3A2A1A"), 1))
            p.setBrush(QColor("#8A2A1A"))
            for i in range(2):
                p.drawRect(QRectF(t * 0.6 + i * t * 1.0, size - t * 0.7 - t * 0.55, t * 0.8, t * 0.55))
            p.setBrush(QColor("#E03020"))
            p.drawRect(QRectF(t * 0.6, size - t * 0.55, t * 1.3, t * 0.4))
        else:
            p.setPen(QPen(QColor("#202040"), 1))
            p.setBrush(QColor("#F0D040"))
            c = QPointF(size / 2, t * 1.1)
            pts = [QPointF(c.x() + math.cos(a) * t * (0.55 if i % 2 == 0 else 0.25),
                           c.y() + math.sin(a) * t * (0.55 if i % 2 == 0 else 0.25))
                   for i, a in enumerate([j * math.pi / 5 - math.pi / 2 for j in range(10)])]
            p.drawPolygon(QPolygonF(pts))
            p.setBrush(QColor("#202020"))
            p.drawRect(QRectF(t * 0.8, size - t * 0.3, t * 1.4, t * 0.25))
    elif kind == "coal":
        p.fillRect(QRectF(1, 1, size - 2, size - 2), QColor("#5A5A5E"))
        _box(p, t * 0.3, t * 1.5, size - t * 0.6, size - t * 1.8, "#4A4A50", "#7A7A80", t * 0.8)
        for i in range(2):
            x = t * 0.8 + i * t * 1.6
            p.setPen(QPen(QColor(0, 0, 0, 150), 1))
            p.setBrush(QColor("#8A6A5A"))
            p.drawRect(QRectF(x, t * 0.1, t * 0.5, t * 1.6))
        p.setBrush(QColor("#202020"))
        p.drawEllipse(QPointF(size - t * 0.8, size - t * 0.6), t * 0.5, t * 0.35)
    elif kind == "nuclear":
        p.fillRect(QRectF(1, 1, size - 2, size - 2), QColor("#8A8A90"))
        p.setPen(QPen(QColor(0, 0, 0, 150), 1))
        g = QLinearGradient(t * 0.3, 0, t * 2.1, 0)
        g.setColorAt(0, QColor("#B0B0B8"))
        g.setColorAt(0.5, QColor("#E8E8F0"))
        g.setColorAt(1, QColor("#9898A0"))
        p.setBrush(QBrush(g))
        p.drawPolygon(QPolygonF([QPointF(t * 0.4, size - t * 0.3), QPointF(t * 0.7, t * 0.8), QPointF(t * 0.55, t * 0.3),
                                 QPointF(t * 1.95, t * 0.3), QPointF(t * 1.8, t * 0.8), QPointF(t * 2.1, size - t * 0.3)]))
        p.setBrush(QColor("#D0D0D8"))
        p.drawEllipse(QRectF(t * 2.3, t * 1.4, t * 1.4, t * 1.4))
        p.setBrush(QColor("#E8C020"))
        p.drawEllipse(QPointF(t * 3.0, t * 2.1), t * 0.25, t * 0.25)
    elif kind == "stadium":
        p.fillRect(QRectF(1, 1, size - 2, size - 2), QColor("#7A7A7E"))
        p.setPen(QPen(QColor(0, 0, 0, 150), 1))
        p.setBrush(QColor("#C8C0B0"))
        p.drawEllipse(QRectF(t * 0.2, t * 0.3, size - t * 0.4, size - t * 0.6))
        p.setBrush(QColor("#3A9A3A"))
        p.drawEllipse(QRectF(t * 0.8, t * 0.9, size - t * 1.6, size - t * 1.8))
        p.setPen(QPen(QColor("#FFFFFF"), 1))
        p.drawLine(QPointF(size / 2, t * 0.9), QPointF(size / 2, size - t * 0.9))
    elif kind == "seaport":
        p.fillRect(QRectF(1, 1, size - 2, size - 2), QColor("#7A7A7E"))
        for i in range(5):
            p.setPen(QPen(QColor(0, 0, 0, 120), 1))
            p.setBrush(QColor(["#C83A2A", "#3A6AC8", "#E8B020", "#3A9A4A", "#8A4AA8"][i]))
            p.drawRect(QRectF(t * 0.3 + (i % 3) * t * 0.9, t * 2.0 + (i // 3) * t * 0.6, t * 0.8, t * 0.45))
        p.setPen(QPen(QColor("#E0A020"), max(1.5, t / 8)))
        p.drawLine(QPointF(t * 2.8, size - t * 0.3), QPointF(t * 2.8, t * 0.4))
        p.drawLine(QPointF(t * 2.8, t * 0.4), QPointF(t * 3.8, t * 0.4))
        p.setPen(QPen(QColor(0, 0, 0, 160), 1))
        p.setBrush(QColor("#5A3A2A"))
        p.drawRect(QRectF(t * 0.3, t * 0.3, t * 2.0, t * 1.2))
    elif kind == "airport":
        p.fillRect(QRectF(1, 1, size - 2, size - 2), QColor("#7A9A5A"))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#4A4A4E"))
        p.drawRect(QRectF(t * 0.3, t * 1.0, size - t * 0.6, t * 1.1))
        p.drawRect(QRectF(t * 3.6, t * 0.3, t * 1.1, size - t * 0.6))
        p.setPen(QPen(QColor("#E8E8E8"), max(1.0, t / 10), Qt.DashLine))
        p.drawLine(QPointF(t * 0.5, t * 1.55), QPointF(size - t * 0.5, t * 1.55))
        p.drawLine(QPointF(t * 4.15, t * 0.5), QPointF(t * 4.15, size - t * 0.5))
        _box(p, t * 0.4, t * 3.0, t * 2.6, t * 1.6, "#9A9AA0", "#C8C8D0", t * 0.5)
        p.setPen(QPen(QColor(0, 0, 0, 150), 1))
        p.setBrush(QColor("#E8E8E8"))
        p.drawRect(QRectF(t * 1.0, t * 4.8, t * 0.5, t * 0.9))
        p.setBrush(QColor("#80C0E0"))
        p.drawRect(QRectF(t * 0.9, t * 4.6, t * 0.7, t * 0.35))
        _plane(p, t * 2.0, t * 1.55, t)
    if not powered and kind not in ("coal", "nuclear"):
        _bolt(p, size / 2, size / 2, t)
    p.end()
    return pm


def _plane(p, x, y, t):
    p.setPen(QPen(QColor(0, 0, 0, 160), 1))
    p.setBrush(QColor("#F0F0F4"))
    p.drawRect(QRectF(x - t * 0.6, y - t * 0.1, t * 1.2, t * 0.2))
    p.drawPolygon(QPolygonF([QPointF(x, y - t * 0.55), QPointF(x + t * 0.15, y), QPointF(x, y + t * 0.55),
                             QPointF(x - t * 0.15, y)]))


def monster(p, x, y, t, frame):
    """Claudezilla, from above-ish: a green reptile stomping across town."""
    p.save()
    p.translate(x, y)
    s = t / 16
    p.scale(s, s)
    step = math.sin(frame * 0.6) * 3
    p.setPen(QPen(QColor("#103A10"), 1.5))
    p.setBrush(QColor("#3A8A3A"))
    p.drawEllipse(QPointF(0, 0), 14, 20)
    p.drawEllipse(QPointF(-12, 8 + step), 6, 8)
    p.drawEllipse(QPointF(12, 8 - step), 6, 8)
    p.drawPolygon(QPolygonF([QPointF(-6, 16), QPointF(6, 16), QPointF(0, 40)]))
    p.drawEllipse(QPointF(0, -22), 9, 10)
    p.setBrush(QColor("#E8E040"))
    p.setPen(Qt.NoPen)
    for i in range(4):
        p.drawPolygon(QPolygonF([QPointF(-3, -10 + i * 7), QPointF(3, -10 + i * 7), QPointF(0, -16 + i * 7)]))
    p.setBrush(QColor("#FF3020"))
    p.drawEllipse(QPointF(-3.5, -25), 1.8, 1.8)
    p.drawEllipse(QPointF(3.5, -25), 1.8, 1.8)
    p.restore()


def tornado(p, x, y, t, frame):
    p.save()
    p.translate(x, y)
    s = t / 16
    p.scale(s, s)
    for i in range(7):
        r = 4 + i * 3.5
        wob = math.sin(frame * 0.8 + i) * 3
        p.setPen(QPen(QColor(90, 80, 70, 200), 2))
        p.setBrush(QColor(140, 130, 120, 120))
        p.drawEllipse(QPointF(wob, -i * 7), r, r * 0.35)
    p.restore()


# ---- tool icons for the Edit palette -----------------------------------------------------------------------------

def tool_icon(tool, size=26):
    pm = _pm(size, size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    t = size
    if tool == "bulldozer":
        p.setPen(QPen(QColor("#3A2A10"), 1))
        p.setBrush(QColor("#E8B020"))
        p.drawRect(QRectF(t * 0.25, t * 0.35, t * 0.5, t * 0.3))
        p.setBrush(QColor("#5A5A5E"))
        p.drawRect(QRectF(t * 0.2, t * 0.62, t * 0.6, t * 0.15))
        p.setBrush(QColor("#9A9AA0"))
        p.drawRect(QRectF(t * 0.08, t * 0.35, t * 0.1, t * 0.4))
    elif tool in ("road", "rail", "wire"):
        p.drawPixmap(0, 0, network(tool, E | W, t))
    elif tool == "park":
        p.drawPixmap(0, 0, misc("park", t, 0))
    elif tool in ("res", "com", "ind"):
        p.fillRect(QRectF(1, 1, t - 2, t - 2), QColor(ZONE_C[tool]).lighter(130))
        p.setPen(QPen(QColor(ZONE_C[tool]).darker(160), 1.5))
        p.drawRect(QRectF(1, 1, t - 2, t - 2))
        p.setFont(QFont("Arial", int(t * 0.5), QFont.Bold))
        p.drawText(QRectF(0, 0, t, t), Qt.AlignCenter, tool[0].upper())
    elif tool == "query":
        p.setPen(QPen(QColor("#202020"), 2))
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QPointF(t / 2, t / 2), t * 0.38, t * 0.38)
        p.setFont(QFont("Arial", int(t * 0.5), QFont.Bold))
        p.drawText(QRectF(0, 0, t, t), Qt.AlignCenter, "?")
    else:
        big = special(tool, t / ({"police": 3, "fire": 3, "stadium": 4, "seaport": 4, "coal": 4, "nuclear": 4,
                                  "airport": 6}[tool]))
        p.drawPixmap(QRectF(0, 0, t, t), big, QRectF(big.rect()))
    p.end()
    return pm


def icon_pixmap(size=32):
    """The program icon: a little skyline on a green road sign."""
    pm = _pm(size, size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    p.setPen(QPen(QColor("#FFFFFF"), 1.5 * s))
    p.setBrush(QColor("#1E7A2E"))
    p.drawRoundedRect(QRectF(1 * s, 3 * s, 30 * s, 24 * s), 3 * s, 3 * s)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#E8E8F0"))
    for x, h in ((5, 10), (9, 16), (14, 12), (18, 19), (23, 9)):
        p.drawRect(QRectF(x * s, (24 - h) * s, 4 * s, h * s))
    p.setBrush(QColor("#9A9AA4"))
    p.drawRect(QRectF(14 * s, 27 * s, 3 * s, 4 * s))
    p.end()
    return pm


def icon():
    ic = QIcon()
    for sz in (16, 32, 48):
        ic.addPixmap(icon_pixmap(sz))
    return ic
