"""Claude Shelter: run an underground vault, after Fallout Shelter.

Build rooms down into the rock, drag dwellers into the jobs that suit their S.P.E.C.I.A.L., keep the power, food and
water flowing, and tap a room's bubble to collect what it made (or rush it, and risk a fire). Put a man and a woman
in the Living Quarters and there'll be a baby; the radio brings in strangers. Fight off fires, radroaches and raiders,
send dwellers out into the wasteland for caps and gear, finish objectives for lunchboxes.

Drag the vault to look around, scroll to zoom. The vault saves itself, and the wasteland keeps going while you're
away. (The rules are in game.py.) No sound - it's a quiet vault."""
import json
import math
import time

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetrics, QIcon, QLinearGradient, QPainter, QPainterPath, QPen,
                           QPixmap, QPolygonF)
from PySide6.QtWidgets import QWidget
from shiboken6 import isValid

from claudecore import host

from .game import (BUILD_ORDER, CELLS, FLOORS, INCIDENTS, OUTFIT, RARITY, RESOURCES, ROOMS, SEG, STAT_NAMES, WEAPON,
                   Vault, width, xp_needed)

TITLE = "Claude Shelter"
EMOJI = "Segoe UI Emoji"
UI = "Segoe UI"
CW, FH = 34, 104                # a cell's width and a floor's height, in world pixels
SKY = 330                       # how much surface shows above the vault
TOP, BOTTOM, SIDE = 58, 66, 380
GREEN = "#7FE07A"               # the Pip-Boy green
AMBER = "#F2C230"
PANEL = "#16201A"
EDGE = "#3E5A44"
DIM = "#9AB59E"
RED = "#E0563A"
BLUE = "#4A90D9"
SUIT = "#2B5FAE"
SPEEDS = (0, 1, 2, 4)

_fonts = {}


def font(size, bold=True, family=UI):
    key = (int(size), bold, family)
    f = _fonts.get(key)
    if f is None:
        f = QFont(family)
        f.setPixelSize(max(1, int(size)))
        f.setBold(bold)
        _fonts[key] = f
    return f


def text(p, rect, s, size, colour="#FFFFFF", align=Qt.AlignCenter, bold=True, shadow=False, family=UI):
    p.setFont(font(size, bold, family))
    if shadow:
        p.setPen(QColor(0, 0, 0, 150))
        p.drawText(rect.translated(1, 1.5), align, s)
    p.setPen(QColor(colour))
    p.drawText(rect, align, s)


def emoji(p, rect, s, size):
    text(p, rect, s, size, "#000000", family=EMOJI)


def box(p, rect, fill=PANEL, border=EDGE, radius=8, width_=1.5):
    p.setPen(QPen(QColor(border), width_) if border else Qt.NoPen)
    p.setBrush(QColor(fill))
    p.drawRoundedRect(rect, radius, radius)


def bar(p, rect, frac, colour, back="#0B120D"):
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(back))
    p.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
    frac = max(0.0, min(1.0, frac))
    if frac > 0:
        p.setBrush(QColor(colour))
        p.drawRoundedRect(QRectF(rect.x(), rect.y(), max(rect.height(), rect.width() * frac), rect.height()),
                          rect.height() / 2, rect.height() / 2)


def mmss(sec):
    sec = int(sec)
    h, m, s = sec // 3600, sec // 60 % 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


# ---- the people -----------------------------------------------------------------------------------------------
def paint_dweller(p, x, y, d, t, moving=False, face=1, scale=1.0, colour=None, hair=None, skin=None, weapon=False,
                  glow=None):
    """A little vault dweller, feet at (x, y)."""
    p.save()
    p.translate(x, y)
    if glow:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(glow))
        p.drawEllipse(QPointF(0, -1), 11 * scale, 3.5 * scale)
    p.scale(face * scale, scale)
    suit = QColor(colour or (OUTFIT[d["outfit"]][3] if d and d.get("outfit") else SUIT))
    skin = QColor(skin or d["skin"])
    hair = QColor(hair or d["hair"])
    swing = math.sin(t * 11) * 0.45 if moving else 0.0
    p.setPen(Qt.NoPen)
    for k, a in ((-1, swing), (1, -swing)):          # legs
        p.save()
        p.translate(k * 2.5, -12)
        p.rotate(math.degrees(a))
        p.setBrush(suit.darker(125))
        p.drawRoundedRect(QRectF(-2, 0, 4, 12), 1.5, 1.5)
        p.setBrush(QColor("#2A2420"))
        p.drawRect(QRectF(-2, 10, 5, 2.5))
        p.restore()
    p.setBrush(suit)
    p.drawRoundedRect(QRectF(-6, -25, 12, 14), 3, 3)
    if not (d and d.get("outfit")) and not colour:
        p.setBrush(QColor(AMBER))
        p.drawRect(QRectF(-0.8, -25, 1.6, 14))
    if d and d.get("preg", 0) > 0:
        p.setBrush(suit.lighter(110))
        p.drawEllipse(QPointF(4.5, -16), 4, 4.5)
    p.save()                                         # an arm
    p.translate(0, -23)
    p.rotate(math.degrees(-swing * 0.8) + (-70 if weapon else 0))
    p.setBrush(suit.darker(110))
    p.drawRoundedRect(QRectF(-1.8, 0, 3.6, 11), 1.5, 1.5)
    p.setBrush(skin)
    p.drawEllipse(QPointF(0, 11.5), 1.9, 1.9)
    if weapon:
        p.setBrush(QColor("#3A3A3A"))
        p.drawRect(QRectF(-1, 11, 2, 7))
    p.restore()
    p.setBrush(skin)
    p.drawEllipse(QPointF(0, -30.5), 5.6, 5.8)
    p.setBrush(hair)
    style = d["style"] if d else 3
    if style == 0:
        p.drawChord(QRectF(-5.8, -36.6, 11.6, 11), 0, 180 * 16)
    elif style == 1:
        p.drawChord(QRectF(-5.8, -36.6, 11.6, 11), 0, 180 * 16)
        p.drawRoundedRect(QRectF(-6, -33, 4, 9), 2, 2)
    elif style == 2:
        p.drawChord(QRectF(-5.8, -36.6, 11.6, 11), 0, 180 * 16)
        p.drawEllipse(QPointF(-5, -34), 3, 3)
    else:
        for k in range(4):
            p.drawPolygon(QPolygonF([QPointF(-4 + k * 2.6, -34), QPointF(-2.7 + k * 2.6, -39.5),
                                     QPointF(-1.4 + k * 2.6, -34)]))
        p.drawChord(QRectF(-5.6, -36, 11.2, 9), 0, 180 * 16)
    p.setBrush(QColor("#1A1A1A"))
    p.drawEllipse(QPointF(2.6, -30.5), 0.9, 1.1)
    p.restore()


def paint_body(p, x, y, d):
    p.save()
    p.translate(x, y - 3)
    p.rotate(-90)
    paint_dweller(p, 0, 0, d, 0, colour="#5A6A78")
    p.restore()
    text(p, QRectF(x - 20, y - 26, 40, 16), "✝", 13, "#C8C8C8")


def paint_deathclaw(p, x, y, t, face=1):
    p.save()
    p.translate(x, y)
    p.scale(face, 1)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#3E4A2E"))
    p.drawEllipse(QRectF(-14, -44, 26, 32))
    p.drawEllipse(QRectF(4, -54, 16, 14))
    p.setBrush(QColor("#2E3822"))
    for k in (-1, 1):
        p.drawRoundedRect(QRectF(-6 + k * 5, -16, 6, 16), 2, 2)
    p.setBrush(QColor("#E8E0C8"))
    for k in range(3):
        p.drawPolygon(QPolygonF([QPointF(12 + k * 3, -30), QPointF(14 + k * 3, -22 + math.sin(t * 6) * 2),
                                 QPointF(16 + k * 3, -30)]))
    p.drawPolygon(QPolygonF([QPointF(8, -54), QPointF(4, -62), QPointF(11, -55)]))
    p.setBrush(QColor("#F2C230"))
    p.drawEllipse(QPointF(15, -49), 1.6, 1.6)
    p.restore()


# ---- the rooms --------------------------------------------------------------------------------------------------
_cache = {}


def _lamp(p, x, y, w):
    g = QLinearGradient(QPointF(x, y), QPointF(x, y + 70))
    g.setColorAt(0, QColor(255, 236, 170, 70))
    g.setColorAt(1, QColor(255, 236, 170, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawPolygon(QPolygonF([QPointF(x - 5, y), QPointF(x + 5, y), QPointF(x + w / 2, y + 70),
                             QPointF(x - w / 2, y + 70)]))
    p.setBrush(QColor("#FFE9A0"))
    p.drawRoundedRect(QRectF(x - 6, y - 2, 12, 4), 2, 2)


def _furniture(p, kind, r, level):
    """One segment's worth of things in a room (r is the segment; its floor is at r.bottom())."""
    x, fy = r.x(), r.bottom()
    pen = QPen(QColor(0, 0, 0, 120), 1)
    p.setPen(pen)

    def rect(rx, ry, rw, rh, col, rad=2):
        p.setBrush(QColor(col))
        p.drawRoundedRect(QRectF(x + rx, fy - ry - rh, rw, rh), rad, rad)

    def circ(cx, cy, rad, col):
        p.setBrush(QColor(col))
        p.drawEllipse(QPointF(x + cx, fy - cy), rad, rad)

    if kind == "living":
        rect(6, 0, 42, 14, "#D8D0B8")
        rect(6, 6, 42, 8, "#4A6EA8")
        rect(8, 10, 10, 6, "#F0EAD8")
        rect(56, 0, 34, 24, "#7A5A3A")
        rect(60, 14, 10, 6, "#9A7A5A")
        rect(74, 24, 3, 14, "#5A5A5A", 1)
        rect(68, 38, 15, 8, "#E8C870", 3)
    elif kind == "power":
        for cx in (10, 54):
            g = QLinearGradient(QPointF(x + cx, 0), QPointF(x + cx + 34, 0))
            g.setColorAt(0, QColor("#6A6A60"))
            g.setColorAt(0.5, QColor("#B8B8A8"))
            g.setColorAt(1, QColor("#5A5A50"))
            p.setBrush(g)
            p.drawRoundedRect(QRectF(x + cx, fy - 58, 34, 58), 5, 5)
            rect(cx, 26, 34, 7, AMBER, 1)
            text(p, QRectF(x + cx, fy - 52, 34, 20), "⚡", 14, AMBER)
        rect(0, 62, r.width(), 5, "#5A5A5A", 1)
    elif kind == "diner":
        rect(4, 0, 68, 22, "#C8C0B0")
        rect(2, 22, 72, 5, "#C0392B", 1)
        for cx in (14, 36, 58):
            rect(cx - 2, 0, 4, 12, "#6A6A6A", 1)
            circ(cx, 14, 5, "#B03A2E")
        rect(76, 0, 20, 48, "#E8E8E0", 4)
        rect(18, 50, 44, 18, "#2A2A26", 2)
        p.setPen(QPen(QColor(GREEN), 1))
        for k in range(3):
            p.drawLine(QPointF(x + 22, fy - 64 + k * 5), QPointF(x + 56, fy - 64 + k * 5))
    elif kind == "water":
        for cx in (8, 52):
            g = QLinearGradient(QPointF(x + cx, 0), QPointF(x + cx + 36, 0))
            g.setColorAt(0, QColor("#2A5A8A"))
            g.setColorAt(0.5, QColor("#7AB8E8"))
            g.setColorAt(1, QColor("#244E78"))
            p.setBrush(g)
            p.drawRoundedRect(QRectF(x + cx, fy - 54, 36, 54), 12, 12)
            circ(cx + 18, 34, 6, "#E8E8E0")
        rect(0, 58, r.width(), 5, "#4A6A7A", 1)
    elif kind == "storage":
        rect(4, 0, 90, 60, "#5A4A36", 1)
        for row in range(3):
            for k in range(4):
                if (row * 4 + k + level) % 5 != 0:
                    rect(8 + k * 21, 2 + row * 20, 17, 15, "#A8824E" if (row + k) % 2 else "#8E6C3E", 1)
    elif kind == "medbay":
        rect(6, 0, 46, 14, "#E8E8E8")
        rect(8, 10, 12, 6, "#FFFFFF")
        rect(62, 0, 28, 44, "#F0F0F0", 3)
        rect(70, 26, 12, 4, "#D23A3A", 1)
        rect(74, 22, 4, 12, "#D23A3A", 1)
        rect(18, 40, 20, 20, "#FFFFFF", 3)
        rect(26, 44, 4, 12, "#D23A3A", 0)
        rect(22, 48, 12, 4, "#D23A3A", 0)
    elif kind == "science":
        rect(4, 0, 62, 24, "#8A8A80")
        for k, col in enumerate(("#7CFC5A", "#5AD8FC", "#FC5AD8")):
            circ(14 + k * 18, 30, 6, col)
            rect(12 + k * 18, 34, 4, 8, "#D0D0D0", 0)
        rect(70, 0, 24, 46, "#3A4A3A", 2)
        rect(72, 26, 20, 16, "#0A1A0A", 1)
        p.setPen(QPen(QColor(GREEN), 1))
        p.drawLine(QPointF(x + 74, fy - 34), QPointF(x + 90, fy - 34))
    elif kind == "radio":
        rect(4, 0, 54, 22, "#6A4A30")
        rect(24, 22, 3, 14, "#3A3A3A", 1)
        circ(26, 40, 5, "#2A2A2A")
        rect(64, 0, 30, 62, "#3A3A44", 2)
        for k in range(4):
            circ(72 + (k % 2) * 14, 14 + (k // 2) * 18, 5, "#8A8A9A")
        rect(68, 50, 22, 6, AMBER, 1)
    elif kind == "weight":
        rect(10, 0, 4, 40, "#5A5A5A", 1)
        rect(80, 0, 4, 40, "#5A5A5A", 1)
        rect(4, 32, 86, 3, "#C8C8C8", 1)
        for cx in (18, 76):
            rect(cx - 3, 24, 6, 20, "#2A2A2A", 2)
        rect(30, 0, 34, 10, "#7A3A3A", 2)
    elif kind == "athletics":
        for cx in (6, 52):
            rect(cx, 0, 40, 8, "#3A3A3A", 2)
            rect(cx + 32, 0, 4, 36, "#5A5A5A", 1)
            rect(cx + 26, 34, 14, 6, "#6A6A6A", 1)
    elif kind == "armory":
        for k, (cx, cy) in enumerate(((24, 42), (70, 42))):
            circ(cx, cy, 15, "#E8E8E0")
            circ(cx, cy, 10, "#D23A3A")
            circ(cx, cy, 5, "#E8E8E0")
            circ(cx, cy, 2, "#D23A3A")
        rect(4, 0, 86, 10, "#5A4A3A", 1)
    elif kind == "classroom":
        rect(8, 30, 70, 32, "#2E4A34", 2)
        p.setPen(QPen(QColor("#E8E8E8"), 1))
        p.drawLine(QPointF(x + 14, fy - 50), QPointF(x + 44, fy - 50))
        p.drawLine(QPointF(x + 14, fy - 42), QPointF(x + 60, fy - 42))
        rect(10, 0, 26, 14, "#8A6A4A")
        rect(52, 0, 26, 14, "#8A6A4A")
    elif kind == "fitness":
        rect(20, 52, 2, 14, "#5A5A5A", 0)
        rect(13, 18, 16, 36, "#C0392B", 7)
        rect(56, 0, 34, 6, "#3A6A9A", 2)
        rect(60, 6, 4, 20, "#5A5A5A", 1)
    elif kind == "lounge":
        rect(4, 0, 50, 22, "#7A4A8A", 6)
        rect(4, 18, 50, 12, "#6A3A7A", 5)
        rect(62, 0, 30, 30, "#6A4A2A")
        for k in range(4):
            rect(64 + k * 7, 30, 4, 12, ("#5A9A5A", "#C8A040", "#9A3A3A", "#4A6A9A")[k], 1)
    elif kind == "game":
        rect(8, 0, 6, 16, "#4A3A2A", 1)
        rect(64, 0, 6, 16, "#4A3A2A", 1)
        rect(4, 16, 72, 10, "#2E7A3A", 3)
        circ(86, 46, 9, "#E8E0C8")
        circ(86, 46, 4, "#C0392B")
    elif kind == "nuka":
        rect(6, 0, 30, 58, "#B03040", 8)
        text(p, QRectF(x + 6, fy - 46, 30, 20), "N", 16, "#FFFFFF")
        rect(40, 18, 54, 6, "#5A5A5A", 1)
        for k in range(5):
            rect(42 + k * 10, 24, 6, 14, "#C8303E", 2)
    elif kind == "door":
        cx, cy = x + 46, fy - 44
        p.setBrush(QColor("#8A8A80"))
        teeth = QPainterPath()
        for k in range(18):
            a = k * math.pi * 2 / 18
            for da, rad in ((-0.08, 44), (0.08, 44), (0.1, 38), (0.25, 38)):
                pt = QPointF(cx + math.cos(a + da) * rad, cy + math.sin(a + da) * rad)
                if k == 0 and da == -0.08:
                    teeth.moveTo(pt)
                else:
                    teeth.lineTo(pt)
        teeth.closeSubpath()
        p.drawPath(teeth)
        p.setBrush(QColor("#A8A898"))
        p.drawEllipse(QPointF(cx, cy), 34, 34)
        p.setBrush(QColor("#C8C0A0"))
        p.drawEllipse(QPointF(cx, cy), 14, 14)
        for k in range(8):
            rect(k * 13, 0, 7, 4, AMBER if k % 2 else "#2A2A2A", 0)


def paint_room(p, r, kind, segs, level):
    """A room (or an elevator shaft), drawn into r."""
    info = ROOMS[kind]
    path = QPainterPath()
    path.addRoundedRect(r, 3, 3)
    if kind == "elevator":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2A2E32"))
        p.drawRect(r)
        p.setBrush(QColor("#4A5058"))
        p.drawRect(QRectF(r.x() + 2, r.y(), 3, r.height()))
        p.drawRect(QRectF(r.right() - 5, r.y(), 3, r.height()))
        p.setPen(QPen(QColor("#6A6A6A"), 1))
        p.drawLine(QPointF(r.center().x(), r.y()), QPointF(r.center().x(), r.y() + 20))
        return
    wall = QColor(info["colour"])
    g = QLinearGradient(r.topLeft(), r.bottomLeft())
    g.setColorAt(0, wall.darker(150))
    g.setColorAt(0.75, wall.darker(115))
    g.setColorAt(1, wall.darker(170))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawPath(path)
    p.setPen(QPen(QColor(0, 0, 0, 40), 1))                  # wall panels
    for k in range(1, int(r.width() // 17)):
        p.drawLine(QPointF(r.x() + k * 17, r.y() + 8), QPointF(r.x() + k * 17, r.bottom() - 10))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#2A2A2A"))
    p.drawRect(QRectF(r.x(), r.bottom() - 8, r.width(), 8))     # the floor
    p.setBrush(QColor("#3A3A3A"))
    p.drawRect(QRectF(r.x(), r.y(), r.width(), 6))              # the ceiling
    seg_w = r.width() / max(1, segs) if kind != "door" else r.width()
    n = 1 if kind == "door" else segs
    for k in range(n):
        sr = QRectF(r.x() + k * seg_w, r.y() + 6, seg_w, r.height() - 14)
        _furniture(p, kind, sr, level)
        _lamp(p, sr.center().x(), r.y() + 7, seg_w * 0.8)
    stars = "★" * level
    text(p, QRectF(r.x() + 5, r.y() + 7, r.width() - 10, 14), f"{info['name']}  {stars}", 9,
         "#F4EED8", Qt.AlignLeft | Qt.AlignVCenter, shadow=True)
    p.setPen(QPen(QColor("#1A1A1A"), 2))
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)


def cached_room(p, r, kind, segs, level):
    key = (kind, segs, level, int(r.width()), int(r.height()))
    pm = _cache.get(key)
    if pm is None:
        pm = QPixmap(int(r.width() * 2), int(r.height() * 2))
        pm.setDevicePixelRatio(2)
        pm.fill(Qt.transparent)
        q = QPainter(pm)
        q.setRenderHint(QPainter.Antialiasing)
        q.setRenderHint(QPainter.TextAntialiasing)
        paint_room(q, QRectF(0, 0, r.width(), r.height()), kind, segs, level)
        q.end()
        _cache[key] = pm
    p.drawPixmap(r.topLeft(), pm)


def dirt_tile():
    pm = _cache.get("dirt")
    if pm is None:
        pm = QPixmap(160, 160)
        pm.fill(QColor("#5A4330"))
        q = QPainter(pm)
        q.setRenderHint(QPainter.Antialiasing)
        q.setPen(Qt.NoPen)
        seed = 7
        for k in range(70):
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            x = seed % 160
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            y = seed % 160
            rad = 1.5 + (seed >> 8) % 6
            q.setBrush(QColor("#4A3626") if k % 3 else QColor("#6E5640"))
            q.drawEllipse(QPointF(x, y), rad, rad * 0.7)
        q.end()
        _cache["dirt"] = pm
    return pm


# ---- the window -------------------------------------------------------------------------------------------------
class Shelter(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setMouseTracking(True)
        self.setMinimumSize(1100, 700)
        self.vault = None
        data = self._load("vault.json")
        if data:
            try:
                self.vault = Vault.from_json(data)
            except (KeyError, TypeError, ValueError, IndexError, StopIteration):
                self.vault = None
        if self.vault is None:
            self.vault = Vault()
        self.speed = 1
        self.zoom = 1.0
        self.cam = QPointF(-90, -150)
        self.panel = None               # room / dweller / build / list / waste / storage / goals / help
        self.sel_room = None
        self.sel_dweller = None
        self.build_kind = None
        self.drag = None
        self.mouse = QPointF(-1, -1)
        self.hits, self.tips = [], []
        self.scroll = {}
        self.toasts = []
        self.seen_msg = max([m.get("n", 0) for m in self.vault.msgs] or [0])
        self.lunch = None               # an open lunchbox's cards
        self.explore_pick = None        # [stimpaks, radaway] while choosing what to take
        self.confirm = None
        self.t = 0.0
        self.last = time.perf_counter()
        self.saved = time.perf_counter()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    # ---- saving ----
    def _load(self, name):
        try:
            return json.loads((host.saves(TITLE) / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def _save(self):
        try:
            (host.saves(TITLE) / "vault.json").write_text(json.dumps(self.vault.to_json()), encoding="utf-8")
        except OSError:
            pass
        self.saved = time.perf_counter()

    # ---- the clock ----
    def _tick(self):
        now = time.perf_counter()
        dt = min(0.25, now - self.last)
        self.last = now
        self.t += dt
        sim = dt * self.speed
        while sim > 0:
            step = min(0.25, sim)
            self.vault.update(step)
            sim -= step
        for m in self.vault.msgs:
            if m.get("n", 0) > self.seen_msg:
                self.seen_msg = m["n"]
                self.toasts.append([m["text"], m["kind"], self.t + (7 if m["kind"] in ("alert", "death") else 5)])
        self.toasts = [x for x in self.toasts if x[2] > self.t][-5:]
        if now - self.saved > 20:
            self._save()
        if self.drag and self.drag.get("pan") and self.drag["moved"]:
            pass
        self.update()

    # ---- geometry ----
    def view(self):
        return QRectF(0, TOP, self.width(), self.height() - TOP - BOTTOM)

    def to_world(self, pt):
        v = self.view()
        return QPointF((pt.x() - v.x()) / self.zoom + self.cam.x(), (pt.y() - v.y()) / self.zoom + self.cam.y())

    def room_rect(self, r):
        return QRectF(r["cell"] * CW + 1, r["floor"] * FH + 5, width(r) * CW - 2, FH - 10)

    def dweller_pos(self, d):
        return QPointF(d["x"] * CW, d["y"] * FH + FH - 13)

    def _clamp(self):
        v = self.view()
        w, h = v.width() / self.zoom, v.height() / self.zoom
        deepest = max(r["floor"] for r in self.vault.rooms) + 2
        x0, x1 = -260, CELLS * CW + 260
        y0, y1 = -SKY, max(deepest * FH + 60, 0)
        x = min(max(self.cam.x(), x0), max(x0, x1 - w))
        y = min(max(self.cam.y(), y0), max(y0, y1 - h + 120))
        self.cam = QPointF(x, y)

    def _room_under(self, wp):
        f = math.floor(wp.y() / FH)
        c = math.floor(wp.x() / CW)
        return self.vault.room_at(f, c)

    def _dweller_under(self, wp):
        best = None
        for d in self.vault.dwellers:
            if d["state"] in ("exploring", "returning", "dead_out"):
                continue
            pos = self.dweller_pos(d)
            s = 0.65 if d["child"] > 0 else 1.0
            if QRectF(pos.x() - 8, pos.y() - 40 * s, 16, 40 * s).contains(wp):
                best = d
        return best

    def _bubble(self, r):
        rr = self.room_rect(r)
        return QPointF(rr.center().x(), rr.y() + 30 + math.sin(self.t * 3 + r["id"]) * 2)

    # ---- painting ----
    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        self.hits, self.tips = [], []
        self._clamp()
        v = self.view()
        p.save()
        p.setClipRect(v)
        p.translate(v.x(), v.y())
        p.scale(self.zoom, self.zoom)
        p.translate(-self.cam.x(), -self.cam.y())
        self._draw_world(p)
        p.restore()
        self._draw_top(p)
        self._draw_bottom(p)
        self._draw_toasts(p)
        if self.panel:
            self._draw_panel(p)
        if self.lunch is not None:
            self.hits = []
            self._draw_lunchbox(p)
        if self.drag and self.drag.get("dweller") and self.drag["moved"]:
            d = self.vault.dweller(self.drag["dweller"])
            if d:
                paint_dweller(p, self.mouse.x(), self.mouse.y() + 18, d, self.t, scale=1.4 * self.zoom ** 0.5,
                              glow="#7FE07A80")
        self._draw_tip(p)
        p.end()

    def _visible(self):
        v = self.view()
        return QRectF(self.cam.x(), self.cam.y(), v.width() / self.zoom, v.height() / self.zoom)

    def _draw_world(self, p):
        vault = self.vault
        vis = self._visible()
        # the surface
        sky = QLinearGradient(QPointF(0, -SKY), QPointF(0, 0))
        sky.setColorAt(0, QColor("#E8A860"))
        sky.setColorAt(0.6, QColor("#F2D29A"))
        sky.setColorAt(1, QColor("#E8C88A"))
        p.fillRect(QRectF(vis.x(), -SKY - 400, vis.width(), SKY + 400), sky)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#FFF0C0"))
        p.drawEllipse(QPointF(CELLS * CW * 0.75, -SKY + 70), 34, 34)
        p.setBrush(QColor("#B88A5A"))
        hills = QPolygonF([QPointF(vis.x() - 50, -40)] + [QPointF(x, -70 - 40 * math.sin(x / 140) - 20 * math.sin(x / 47))
                                                          for x in range(int(vis.x()) - 50, int(vis.right()) + 60, 30)]
                          + [QPointF(vis.right() + 60, -40)])
        p.drawPolygon(hills)
        p.setBrush(QColor("#8A6440"))
        cliff = QPolygonF([QPointF(-260, -10), QPointF(-260, -260), QPointF(-140, -300), QPointF(-30, -250),
                           QPointF(60, -170), QPointF(150, -90), QPointF(200, -10)])
        p.drawPolygon(cliff)
        p.setBrush(QColor("#A07A50"))
        p.drawRect(QRectF(vis.x() - 10, -22, vis.width() + 20, 22))
        p.setBrush(QColor("#3A2E22"))                           # the cave mouth over the door
        p.drawRoundedRect(QRectF(4, -54, 92, 56), 30, 30)
        # dead trees and a sign
        p.setPen(QPen(QColor("#4A3626"), 3))
        for tx in (260, 520, 700):
            p.drawLine(QPointF(tx, -22), QPointF(tx, -70))
            p.drawLine(QPointF(tx, -55), QPointF(tx + 14, -68))
            p.drawLine(QPointF(tx, -48), QPointF(tx - 12, -60))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2E4E8A"))
        p.drawRoundedRect(QRectF(150, -64, 70, 26), 4, 4)
        text(p, QRectF(150, -64, 70, 26), f"VAULT {vault.number}", 10, AMBER)
        # the rock
        rock = QRectF(vis.x() - 20, 0, vis.width() + 40, max(0.0, vis.bottom() + 20))
        brush = QBrush(dirt_tile())
        p.fillRect(rock, brush)
        deep = QLinearGradient(QPointF(0, 0), QPointF(0, FLOORS * FH))
        deep.setColorAt(0, QColor(0, 0, 0, 0))
        deep.setColorAt(1, QColor(0, 0, 0, 150))
        p.fillRect(rock, deep)
        # where you could build
        if self.build_kind:
            for f, c in vault.placements(self.build_kind):
                w = 1 if self.build_kind == "elevator" else SEG
                r = QRectF(c * CW + 2, f * FH + 6, w * CW - 4, FH - 12)
                hover = r.contains(self.to_world(self.mouse))
                p.setPen(QPen(QColor(GREEN), 2, Qt.DashLine))
                p.setBrush(QColor(127, 224, 122, 90 if hover else 35))
                p.drawRoundedRect(r, 4, 4)
                if hover:
                    emoji(p, r, ROOMS[self.build_kind]["emoji"], 20)
        # the rooms
        powered = vault.res["power"] > 0
        target = None
        if self.drag and self.drag.get("dweller") and self.drag["moved"]:
            target = self._room_under(self.to_world(self.mouse))
        for r in vault.rooms:
            rr = self.room_rect(r)
            if not rr.intersects(vis):
                continue
            cached_room(p, rr, r["type"], r["segs"], r["level"])
            if not powered and r["type"] not in ("power", "door", "elevator"):
                p.fillRect(rr, QColor(0, 0, 0, 150))
            if r["inc"]:
                self._draw_incident(p, r, rr)
            info = ROOMS[r["type"]]
            if info["kind"] == "produce" and not r["ready"] and r["prog"] > 0:
                bar(p, QRectF(rr.x() + 6, rr.bottom() - 14, rr.width() - 12, 4), r["prog"], GREEN, "#00000080")
            if r["id"] == self.sel_room:
                p.setPen(QPen(QColor(GREEN), 3))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(rr.adjusted(-1, -1, 1, 1), 4, 4)
            if target is r:
                d = vault.dweller(self.drag["dweller"])
                ok = d is not None and r["type"] != "elevator" and (
                    d["room"] == r["id"] or len(vault.assigned(r)) < vault.room_cap(r))
                p.setPen(QPen(QColor(GREEN if ok else RED), 3))
                p.setBrush(QColor(127, 224, 122, 40) if ok else QColor(224, 86, 58, 40))
                p.drawRoundedRect(rr, 4, 4)
                if ok and d and vault.ideal(d, r):
                    text(p, QRectF(rr.x(), rr.y() + 22, rr.width(), 20), "★ Ideal job", 12, AMBER, shadow=True)
        # the dwellers
        for d in vault.dwellers:
            st = d["state"]
            if st in ("exploring", "returning", "dead_out"):
                continue
            if self.drag and self.drag.get("dweller") == d["id"] and self.drag["moved"]:
                continue
            pos = self.dweller_pos(d)
            if not vis.adjusted(-20, -40, 20, 40).contains(pos):
                continue
            if st == "dead":
                paint_body(p, pos.x(), pos.y(), d)
                continue
            here = vault.located(d)
            fighting = bool(here and here["inc"] and d["fight"] > 0)
            moving = st == "walking" or d["wx"] is not None
            glow = "#F2C230A0" if d["id"] == self.sel_dweller else None
            paint_dweller(p, pos.x(), pos.y(), d, self.t + d["id"], moving=moving, face=d["face"],
                          scale=0.65 if d["child"] > 0 else 1.0, weapon=fighting, glow=glow)
            if d["hp"] < vault.hp_cap(d) * 0.98 or fighting or d["rad"] > 0:
                frac = d["hp"] / vault.max_hp(d)
                hb = QRectF(pos.x() - 10, pos.y() - 46, 20, 3.5)
                bar(p, hb, frac, GREEN if frac > 0.5 else AMBER if frac > 0.25 else RED)
                if d["rad"] > 0:
                    rf = d["rad"] / vault.max_hp(d)
                    p.setBrush(QColor(RED))
                    p.drawRect(QRectF(hb.right() - hb.width() * rf, hb.y(), hb.width() * rf, hb.height()))
            if d["id"] == self.sel_dweller:
                text(p, QRectF(pos.x() - 60, pos.y() - 64, 120, 16), d["name"], 11, "#FFFFFF", shadow=True)
        # bubbles of things ready to collect
        for r in vault.rooms:
            if r["ready"]:
                c = self._bubble(r)
                p.setPen(QPen(QColor("#FFFFFF"), 2))
                p.setBrush(QColor(20, 30, 22, 220))
                p.drawEllipse(c, 15, 15)
                emoji(p, QRectF(c.x() - 15, c.y() - 15, 30, 30), RESOURCES[ROOMS[r["type"]]["produce"]][0], 16)

    def _draw_incident(self, p, r, rr):
        inc = r["inc"]
        kind = inc["kind"]
        t = self.t
        p.fillRect(rr, QColor(200, 40, 20, 50))
        if kind == "fire":
            p.setPen(Qt.NoPen)
            for k in range(int(rr.width() // 12)):
                fx = rr.x() + 6 + k * 12
                h = 18 + 10 * math.sin(t * 9 + k * 1.7) + 6 * math.sin(t * 13 + k)
                for col, s in (("#E8501A", 1.0), ("#F2A030", 0.65), ("#FFE070", 0.35)):
                    p.setBrush(QColor(col))
                    p.drawPolygon(QPolygonF([QPointF(fx - 6 * s, rr.bottom() - 8), QPointF(fx, rr.bottom() - 8 - h * s),
                                             QPointF(fx + 6 * s, rr.bottom() - 8)]))
        elif kind in ("roaches", "molerats"):
            n = max(2, int(rr.width() // 30))
            for k in range(n):
                ph = t * (1.2 + k * 0.17) + k * 2.1
                fx = rr.x() + 10 + (rr.width() - 20) * (0.5 + 0.5 * math.sin(ph))
                big = kind == "molerats"
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#6A4A2A" if not big else "#B8907A"))
                p.drawEllipse(QPointF(fx, rr.bottom() - 12), 7 if big else 5, 4 if big else 2.6)
                p.setBrush(QColor("#3A2A1A"))
                p.drawEllipse(QPointF(fx + (6 if math.cos(ph) > 0 else -6), rr.bottom() - 13), 2.4, 2)
        elif kind == "raiders":
            n = 3
            for k in range(n):
                fx = rr.x() + rr.width() * (0.55 + 0.12 * k) + math.sin(t * 2 + k) * 6
                paint_dweller(p, fx, rr.bottom() - 8, None, t + k, moving=True, face=-1, colour="#6A4030",
                              hair="#C0392B", skin=("#E8BE98", "#B07C55", "#D4A27A")[k], weapon=True)
        elif kind == "deathclaws":
            paint_deathclaw(p, rr.x() + rr.width() * 0.7 + math.sin(t * 2) * 8, rr.bottom() - 8, t, face=-1)
        info = INCIDENTS[kind]
        hb = QRectF(rr.x() + 30, rr.y() + 24, rr.width() - 60, 6)
        bar(p, hb, inc["hp"] / inc["max"], RED)
        text(p, QRectF(rr.x(), rr.y() + 30, rr.width(), 18), f"{info['emoji']} {info['name']}", 11, "#FFFFFF",
             shadow=True)
        if r["type"] == "door" and info.get("moves") and self.vault.door_hp > 0:
            text(p, QRectF(rr.x(), rr.y() + 46, rr.width(), 16),
                 f"Door {int(self.vault.door_hp)}/{self.vault.door_max()}", 10, AMBER, shadow=True)

    # ---- the bars ----
    def _btn(self, p, rect, label, action, colour=EDGE, enabled=True, size=13, fill=None):
        hover = enabled and rect.contains(self.mouse)
        p.setPen(QPen(QColor(colour if enabled else "#2E3A30"), 1.5))
        p.setBrush(QColor(fill or ("#24382A" if hover else "#18241B")) if enabled else QColor("#121812"))
        p.drawRoundedRect(rect, 6, 6)
        text(p, rect, label, size, ("#FFFFFF" if hover else GREEN) if enabled else "#4A5A4C",
             Qt.AlignCenter | Qt.TextWordWrap)
        if enabled and action:
            self.hits.append((rect, action))

    def _tip(self, rect, title, lines):
        self.tips.append((rect, title, [ln for ln in lines if ln]))

    def _draw_top(self, p):
        v = self.vault
        w = self.width()
        r = QRectF(0, 0, w, TOP)
        p.fillRect(r, QColor("#0E1510"))
        p.setPen(QPen(QColor(EDGE), 2))
        p.drawLine(QPointF(0, TOP - 1), QPointF(w, TOP - 1))
        text(p, QRectF(14, 6, 150, 24), f"VAULT {v.number}", 18, AMBER, Qt.AlignLeft | Qt.AlignVCenter)
        text(p, QRectF(14, 30, 160, 20), f"Day {int(v.time // 1440) + 1}  {mmss(v.time % 1440)}", 11, DIM,
             Qt.AlignLeft | Qt.AlignVCenter, bold=False)
        x = 180
        for key, col in (("power", AMBER), ("food", "#E8904A"), ("water", BLUE)):
            cap = v.res_cap(key)
            emoji(p, QRectF(x, 10, 26, 36), RESOURCES[key][0], 18)
            bar(p, QRectF(x + 30, 20, 96, 14), v.res[key] / cap, col if v.res[key] > cap * 0.15 else RED)
            text(p, QRectF(x + 30, 34, 96, 18), f"{int(v.res[key])}/{int(cap)}", 10, DIM, bold=False)
            self._tip(QRectF(x, 6, 130, 46), RESOURCES[key][1],
                      [f"{int(v.res[key])} of {int(cap)}", "Runs out: " + {
                          "power": "rooms go dark and stop working",
                          "food": "dwellers slowly lose health",
                          "water": "dwellers pick up radiation"}[key]])
            x += 140
        items = [("👥", f"{v.population()}/{v.capacity()}", "Dwellers", "Living Quarters raise the limit"),
                 ("😊", f"{int(v.happiness())}%", "Happiness", "Ideal jobs, full stores and the radio help"),
                 ("🪙", f"{v.caps}", "Caps", "From collecting, rushing, the wasteland and objectives"),
                 ("💊", f"{v.stimpaks}", "Stimpaks", "Heal a dweller (from the Medbay)"),
                 ("☢️", f"{v.radaway}", "RadAway", "Cure radiation (from the Science Lab)")]
        for icon, val, name, why in items:
            emoji(p, QRectF(x, 12, 26, 32), icon, 17)
            text(p, QRectF(x + 28, 12, 70, 32), val, 15, "#FFFFFF", Qt.AlignLeft | Qt.AlignVCenter)
            self._tip(QRectF(x, 8, 96, 42), name, [why])
            x += 26 + max(46, QFontMetrics(font(15)).horizontalAdvance(val) + 14)
        bx = w - 4 * 46 - 12
        for k, sp in enumerate(SPEEDS):
            rr = QRectF(bx + k * 46, 12, 42, 32)
            self._btn(p, rr, "⏸" if sp == 0 else f"{sp}×", lambda sp=sp: self._set_speed(sp),
                      colour=GREEN if self.speed == sp else EDGE, fill="#2E4A34" if self.speed == sp else None)

    def _draw_bottom(self, p):
        w, h = self.width(), self.height()
        r = QRectF(0, h - BOTTOM, w, BOTTOM)
        p.fillRect(r, QColor("#0E1510"))
        p.setPen(QPen(QColor(EDGE), 2))
        p.drawLine(QPointF(0, h - BOTTOM + 1), QPointF(w, h - BOTTOM + 1))
        v = self.vault
        claim = sum(1 for o in v.objectives if v.progress(o) >= o["target"]) + v.lunchboxes
        out = sum(1 for d in v.dwellers if d["state"] in ("exploring", "returning", "dead_out"))
        buttons = [("🔨", "Build", "build"), ("📋", "Dwellers", "list"), ("🗺️", f"Wasteland ({out})", "waste"),
                   ("🎒", f"Storage {len(v.items)}/{v.storage_cap()}", "storage"),
                   ("🍱", "Objectives" + (f" ({claim})" if claim else ""), "goals"), ("❓", "Help", "help")]
        bw = min(190, (w - 40) / len(buttons) - 8)
        x = (w - len(buttons) * (bw + 8)) / 2
        for icon, label, key in buttons:
            rr = QRectF(x, h - BOTTOM + 11, bw, 44)
            on = self.panel == key
            hover = rr.contains(self.mouse)
            p.setPen(QPen(QColor(GREEN if on else EDGE), 2 if on else 1.5))
            p.setBrush(QColor("#2E4A34" if on else "#24382A" if hover else "#18241B"))
            p.drawRoundedRect(rr, 8, 8)
            emoji(p, QRectF(rr.x() + 6, rr.y(), 34, rr.height()), icon, 18)
            text(p, QRectF(rr.x() + 40, rr.y(), rr.width() - 44, rr.height()), label, 13,
                 "#FFFFFF" if on or hover else GREEN, Qt.AlignLeft | Qt.AlignVCenter)
            self.hits.append((rr, lambda key=key: self._toggle_panel(key)))
            x += bw + 8
        if self.build_kind:
            info = ROOMS[self.build_kind]
            msg = f"Building: {info['name']} ({v.cost(self.build_kind)} caps) - click a green space; right-click to stop"
            right = self._panel_rect().x() - 10 if self.panel else w
            rr = QRectF(max(10, right / 2 - 330), h - BOTTOM - 40, min(660, right - 20), 32)
            box(p, rr, "#16201ADD", GREEN)
            text(p, rr, msg, 13, GREEN)

    def _draw_toasts(self, p):
        y = self.height() - BOTTOM - 48 - (40 if self.build_kind else 0)
        for msg, kind, until in reversed(self.toasts):
            fm = QFontMetrics(font(13))
            w = min(self.width() - 40, fm.horizontalAdvance(msg) + 30)
            rr = QRectF(16, y - 34, w, 30)
            col = {"alert": RED, "death": RED, "good": GREEN, "level": AMBER}.get(kind, EDGE)
            alpha = max(0.0, min(1.0, until - self.t))
            p.setOpacity(alpha)
            box(p, rr, "#101812E8", col)
            text(p, rr.adjusted(12, 0, -8, 0), msg, 13, "#FFFFFF", Qt.AlignLeft | Qt.AlignVCenter)
            p.setOpacity(1.0)
            y -= 36

    def _draw_tip(self, p):
        if self.drag and self.drag.get("moved"):
            return
        tip = None
        for t in self.tips:
            if t[0].contains(self.mouse):
                tip = t
        if tip is None:
            return
        rect, title, lines = tip
        w = 250
        fm = QFontMetrics(font(12, False))
        body = "\n".join(lines)
        bh = fm.boundingRect(QRect(0, 0, w - 20, 1000), Qt.TextWordWrap, body).height() if body else 0
        h = 32 + bh + (8 if body else 0)
        x = min(max(6, self.mouse.x() + 14), self.width() - w - 6)
        y = min(max(6, self.mouse.y() + 18), self.height() - h - 6)
        r = QRectF(x, y, w, h)
        box(p, r, "#101812F4", GREEN)
        text(p, QRectF(x + 10, y + 6, w - 20, 20), title, 13, GREEN, Qt.AlignLeft | Qt.AlignVCenter)
        if body:
            text(p, QRectF(x + 10, y + 28, w - 20, bh + 4), body, 12, "#E8F0E8",
                 Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, bold=False)

    # ---- the side panel ----
    def _panel_rect(self):
        return QRectF(self.width() - SIDE - 10, TOP + 10, SIDE, self.height() - TOP - BOTTOM - 20)

    def _draw_panel(self, p):
        r = self._panel_rect()
        box(p, r, "#0F1712", GREEN, 10, 2)
        self._btn(p, QRectF(r.right() - 36, r.y() + 8, 28, 26), "✕", self._close_panel, size=13)
        inner = r.adjusted(14, 10, -14, -12)
        p.save()
        p.setClipRect(r.adjusted(2, 2, -2, -2))
        {"room": self._p_room, "dweller": self._p_dweller, "build": self._p_build, "list": self._p_list,
         "waste": self._p_waste, "storage": self._p_storage, "goals": self._p_goals,
         "help": self._p_help}[self.panel](p, inner)
        p.restore()

    def _title(self, p, r, s, sub=None):
        text(p, QRectF(r.x(), r.y(), r.width() - 40, 28), s, 18, GREEN, Qt.AlignLeft | Qt.AlignVCenter)
        if sub:
            text(p, QRectF(r.x(), r.y() + 26, r.width(), 18), sub, 12, DIM, Qt.AlignLeft | Qt.AlignVCenter,
                 bold=False)
        return r.y() + (50 if sub else 36)

    def _line(self, p, r, y, label, value="", colour="#FFFFFF", size=13):
        text(p, QRectF(r.x(), y, r.width(), 20), label, size, DIM, Qt.AlignLeft | Qt.AlignVCenter, bold=False)
        if value:
            text(p, QRectF(r.x(), y, r.width(), 20), value, size, colour, Qt.AlignRight | Qt.AlignVCenter)
        return y + 22

    def _p_room(self, p, r):
        v = self.vault
        room = v.room(self.sel_room)
        if room is None:
            self._close_panel()
            return
        info = ROOMS[room["type"]]
        stat = info["stat"]
        y = self._title(p, r, f"{info['emoji']} {info['name']}",
                        f"Level {room['level']}  ·  {room['segs']} wide" if room["type"] not in ("door", "elevator")
                        else (f"Level {room['level']}" if room["type"] == "door" else ""))
        if room["inc"]:
            inc = room["inc"]
            ii = INCIDENTS[inc["kind"]]
            rr = QRectF(r.x(), y, r.width(), 56)
            box(p, rr, "#3A1410", RED)
            text(p, QRectF(rr.x() + 10, rr.y() + 4, rr.width() - 20, 22), f"{ii['emoji']} {ii['name']}!", 15, RED,
                 Qt.AlignLeft | Qt.AlignVCenter)
            bar(p, QRectF(rr.x() + 10, rr.y() + 30, rr.width() - 20, 8), inc["hp"] / inc["max"], RED)
            text(p, QRectF(rr.x() + 10, rr.y() + 38, rr.width() - 20, 16), "Drag dwellers in to fight it", 11,
                 "#F0D0C8", Qt.AlignLeft, bold=False)
            y += 64
        if stat is not None:
            y = self._line(p, r, y, "Needs", STAT_NAMES[stat], AMBER)
        kind = info["kind"]
        if kind == "produce":
            prod = info["produce"]
            c = v.cycle(room)
            amt = v.amount(room)
            label = (f"+{amt:g} {RESOURCES[prod][1]}" if prod != "nuka" else f"+{amt:g} Food and Water")
            y = self._line(p, r, y, "Makes", label)
            y = self._line(p, r, y, "Every", f"{int(c)}s" if c else "nobody's working", "#FFFFFF" if c else RED)
            bar(p, QRectF(r.x(), y + 4, r.width(), 10), room["prog"], GREEN)
            y += 22
            if not v.powered(room):
                y = self._line(p, r, y, "No power!", "", RED)
            bw = (r.width() - 8) / 2
            if room["ready"]:
                self._btn(p, QRectF(r.x(), y, bw, 34), f"Collect {RESOURCES[prod][0]}",
                          lambda: self._collect(prod if prod != "nuka" else "food"))
            else:
                risk = int(v.rush_risk(room) * 100)
                self._btn(p, QRectF(r.x(), y, bw, 34), f"Rush ({risk}% risk)", lambda: self._rush(room),
                          enabled=bool(v.present(room)) and not room["inc"])
            y += 40
        elif kind == "living":
            mult = (8, 10, 12)[room["level"] - 1]
            y = self._line(p, r, y, "Room for", f"{mult * room['segs']} dwellers")
            y = self._line(p, r, y, "Vault", f"{v.population()}/{v.capacity()}")
            if room["rom"] > 0:
                bar(p, QRectF(r.x(), y + 4, r.width(), 8), room["rom"] / 40, "#E87AA8")
                text(p, QRectF(r.x(), y + 12, r.width(), 18), "Romance is in the air...", 11, "#E87AA8",
                     Qt.AlignLeft, bold=False)
                y += 34
            else:
                text(p, QRectF(r.x(), y, r.width(), 36), "A man and a woman here (and room in the vault) "
                     "means a baby on the way.", 11, DIM, Qt.AlignLeft | Qt.TextWordWrap, bold=False)
                y += 40
        elif kind == "training":
            text(p, QRectF(r.x(), y, r.width(), 20), f"Trains {STAT_NAMES[stat]} (up to 10)", 12, DIM,
                 Qt.AlignLeft | Qt.AlignVCenter, bold=False)
            y += 24
        elif kind == "radio":
            bar(p, QRectF(r.x(), y + 4, r.width(), 10), v.radio, "#B08AE0")
            text(p, QRectF(r.x(), y + 14, r.width(), 18), "Broadcasting for new dwellers (and cheering the vault up)",
                 11, DIM, Qt.AlignLeft, bold=False)
            y += 36
        elif kind == "storage":
            y = self._line(p, r, y, "Storage", f"{len(v.items)}/{v.storage_cap()} items")
        elif kind == "door":
            y = self._line(p, r, y, "Door strength", f"{int(v.door_hp)}/{v.door_max()}")
            text(p, QRectF(r.x(), y, r.width(), 36), "Put armed dwellers here to meet raiders at the door.", 11, DIM,
                 Qt.AlignLeft | Qt.TextWordWrap, bold=False)
            y += 38
        elif kind == "elevator":
            text(p, QRectF(r.x(), y, r.width(), 36), "Elevators join the floors. Build one beside a room, or above or "
                 "below another elevator.", 12, DIM, Qt.AlignLeft | Qt.TextWordWrap, bold=False)
            y += 44
        # the people in it
        if kind != "elevator":
            ds = v.assigned(room)
            text(p, QRectF(r.x(), y + 4, r.width(), 20), f"Dwellers ({len(ds)}/{v.room_cap(room)})", 14, GREEN,
                 Qt.AlignLeft | Qt.AlignVCenter)
            y += 28
            for d in ds:
                rr = QRectF(r.x(), y, r.width(), 30)
                self._dweller_row(p, rr, d, stat)
                y += 34
            if not ds:
                text(p, QRectF(r.x(), y, r.width(), 20), "Drag a dweller onto the room to put them to work.", 11,
                     DIM, Qt.AlignLeft, bold=False)
                y += 26
        y += 6
        up = v.upgrade_cost(room)
        if up is not None:
            self._btn(p, QRectF(r.x(), y, r.width(), 34), f"Upgrade to level {room['level'] + 1}  ({up} caps)",
                      lambda: self._upgrade(room), enabled=v.caps >= up)
            y += 40
        if room["type"] != "door":
            sure = self.confirm == ("destroy", room["id"])
            self._btn(p, QRectF(r.x(), y, r.width(), 30), "Really destroy it?" if sure else "Destroy",
                      lambda: self._destroy(room), colour=RED)

    def _dweller_row(self, p, rr, d, stat=None):
        v = self.vault
        hover = rr.contains(self.mouse)
        box(p, rr, "#1E2E22" if hover else "#141E17", None, 6)
        paint_dweller(p, rr.x() + 14, rr.bottom() - 1, d, 0, scale=0.7)
        name = d["name"] + (" ♥" if d["preg"] > 0 else "") + (" (child)" if d["child"] > 0 else "")
        text(p, QRectF(rr.x() + 30, rr.y(), rr.width() - 120, rr.height()), name, 12, "#FFFFFF",
             Qt.AlignLeft | Qt.AlignVCenter)
        right = f"Lv {d['level']}"
        if stat is not None:
            right = f"{STAT_NAMES[stat][0]} {v.stat(d, stat)}  ·  " + right
        text(p, QRectF(rr.x(), rr.y(), rr.width() - 8, rr.height()), right, 12,
             AMBER if stat is not None and v.stat(d, stat) >= max(v.stat(d, i) for i in range(7)) else DIM,
             Qt.AlignRight | Qt.AlignVCenter)
        self.hits.append((rr, lambda d=d: self._select_dweller(d, center=True)))

    def _p_dweller(self, p, r):
        v = self.vault
        d = v.dweller(self.sel_dweller)
        if d is None:
            self._close_panel()
            return
        st = d["state"]
        room = v.room(d["room"]) if d["room"] else None
        status = {"exploring": "Exploring the wasteland", "returning": "On the way home", "dead": "Dead",
                  "dead_out": "Dead in the wasteland"}.get(st)
        if status is None:
            status = (f"In the {ROOMS[room['type']]['name']}" if room else "Waiting for a job")
            if d["child"] > 0:
                status = f"A child (grown up in {mmss(d['child'])})"
            elif d["preg"] > 0:
                status += f"  ·  expecting ({mmss(d['preg'])})"
        y = self._title(p, r, d["name"] + (" ★" if d.get("legend") else ""), status)
        portrait = QRectF(r.x(), y, 70, 84)
        box(p, portrait, "#18241B", EDGE)
        paint_dweller(p, portrait.center().x(), portrait.bottom() - 6, d, self.t, scale=1.8)
        x2 = r.x() + 82
        w2 = r.width() - 82
        lvl = f"Level {d['level']}"
        text(p, QRectF(x2, y, w2, 18), lvl, 13, "#FFFFFF", Qt.AlignLeft)
        bar(p, QRectF(x2, y + 20, w2, 7), d["xp"] / xp_needed(d["level"]) if d["level"] < 50 else 1, AMBER)
        cap = v.max_hp(d)
        text(p, QRectF(x2, y + 30, w2, 18), f"Health {int(max(0, d['hp']))}/{int(cap)}", 12, DIM, Qt.AlignLeft,
             bold=False)
        hb = QRectF(x2, y + 48, w2, 8)
        bar(p, hb, d["hp"] / cap, GREEN)
        if d["rad"] > 0:
            p.setBrush(QColor(RED))
            p.setPen(Qt.NoPen)
            p.drawRect(QRectF(hb.right() - w2 * d["rad"] / cap, hb.y(), w2 * d["rad"] / cap, hb.height()))
        text(p, QRectF(x2, y + 60, w2, 18), f"Happiness {int(d['happy'])}%", 12, DIM, Qt.AlignLeft, bold=False)
        bar(p, QRectF(x2, y + 78, w2, 6), d["happy"] / 100, "#E8D27A")
        y += 96
        best = v.best_stat(d)
        for i, name in enumerate(STAT_NAMES):
            base = d["special"][i]
            eff = v.stat(d, i)
            text(p, QRectF(r.x(), y, 18, 20), "SPECIAL"[i], 14, AMBER if i == best else GREEN, Qt.AlignLeft)
            text(p, QRectF(r.x() + 18, y, 100, 20), name, 12, DIM, Qt.AlignLeft | Qt.AlignVCenter, bold=False)
            bar(p, QRectF(r.x() + 118, y + 6, r.width() - 170, 8), base / 10, GREEN)
            text(p, QRectF(r.right() - 50, y, 50, 20), f"{eff}" + (f" (+{eff - base})" if eff > base else ""), 12,
                 "#FFFFFF", Qt.AlignRight | Qt.AlignVCenter)
            if d["room"] and room and ROOMS[room["type"]]["kind"] == "training" and ROOMS[room["type"]]["stat"] == i:
                need = 25 * base / (1 + 0.25 * (room["level"] - 1))
                bar(p, QRectF(r.x() + 118, y + 16, r.width() - 170, 3), d["train"] / need, AMBER)
            y += 22
        jobs = [ROOMS[k]["name"] for k in BUILD_ORDER if ROOMS[k]["stat"] == best and ROOMS[k]["kind"] in
                ("produce", "living", "radio", "storage")]
        text(p, QRectF(r.x(), y, r.width(), 20), "Best at: " + (", ".join(jobs[:2]) or "-"), 12, AMBER,
             Qt.AlignLeft | Qt.AlignVCenter)
        y += 26
        for slot, label in (("outfit", "Outfit"), ("weapon", "Weapon")):
            have = d[slot]
            desc = "Vault Suit" if slot == "outfit" and not have else "Fists" if not have else have
            if slot == "weapon" and have:
                w = WEAPON[have]
                desc += f"  ({w[1]}-{w[2]})"
            if slot == "outfit" and have:
                desc += "  " + " ".join(f"+{b}{'SPECIAL'[i]}" for i, b in OUTFIT[have][1].items())
            text(p, QRectF(r.x(), y, 60, 24), label, 12, DIM, Qt.AlignLeft | Qt.AlignVCenter, bold=False)
            text(p, QRectF(r.x() + 60, y, r.width() - 140, 24), desc, 12, "#FFFFFF", Qt.AlignLeft | Qt.AlignVCenter)
            if st in ("idle", "walking"):
                if have:
                    self._btn(p, QRectF(r.right() - 76, y, 76, 24), "Unequip",
                              lambda slot=slot: self._unequip(d, slot), size=11)
                else:
                    self._btn(p, QRectF(r.right() - 76, y, 76, 24), "Choose...",
                              lambda: self._toggle_panel("storage"), size=11)
            y += 28
        y += 6
        bw = (r.width() - 8) / 2
        if st in ("dead", "dead_out"):
            cost = v.revive_cost(d)
            self._btn(p, QRectF(r.x(), y, bw, 34), f"Revive ({cost} caps)", lambda: self._act(v.revive(d)),
                      enabled=v.caps >= cost)
            self._btn(p, QRectF(r.x() + bw + 8, y, bw, 34), "Bury", lambda: self._bury(d), colour=RED)
            return
        if st in ("exploring", "returning"):
            self._btn(p, QRectF(r.x(), y, r.width(), 34), "See them in the wasteland",
                      lambda: self._toggle_panel("waste"))
            return
        self._btn(p, QRectF(r.x(), y, bw, 30), f"Stimpak ({v.stimpaks})", lambda: self._act(v.heal(d)),
                  enabled=v.stimpaks > 0 and d["hp"] < v.hp_cap(d))
        self._btn(p, QRectF(r.x() + bw + 8, y, bw, 30), f"RadAway ({v.radaway})", lambda: self._act(v.cure(d)),
                  enabled=v.radaway > 0 and d["rad"] > 0)
        y += 36
        if self.explore_pick is None:
            self._btn(p, QRectF(r.x(), y, r.width(), 34), "🗺️  Send to the Wasteland", self._pick_explore,
                      enabled=d["child"] <= 0 and d["preg"] <= 0)
        else:
            sp, rp = self.explore_pick
            box(p, QRectF(r.x(), y, r.width(), 104), "#18241B", EDGE)
            for k, (label, have, n) in enumerate((("Stimpaks", v.stimpaks, sp), ("RadAway", v.radaway, rp))):
                yy = y + 8 + k * 30
                text(p, QRectF(r.x() + 10, yy, 120, 24), f"Take {label}", 12, DIM, Qt.AlignLeft | Qt.AlignVCenter,
                     bold=False)
                self._btn(p, QRectF(r.right() - 120, yy, 28, 24), "−", lambda k=k: self._pick_adjust(k, -1), size=13)
                text(p, QRectF(r.right() - 90, yy, 50, 24), str(n), 14, "#FFFFFF")
                self._btn(p, QRectF(r.right() - 40, yy, 28, 24), "+", lambda k=k, have=have: self._pick_adjust(k, 1,
                                                                                                           have),
                          size=13)
            self._btn(p, QRectF(r.x() + 10, y + 68, bw - 14, 28), "Go!", lambda: self._explore(d))
            self._btn(p, QRectF(r.x() + bw + 4, y + 68, bw - 14, 28), "Cancel", self._cancel_explore)

    def _p_build(self, p, r):
        v = self.vault
        y = self._title(p, r, "🔨 Build", f"{v.caps} caps  ·  {v.population()} dwellers")
        y0 = y
        sc = self.scroll.get("build", 0)
        y -= sc
        for kind in BUILD_ORDER:
            info = ROOMS[kind]
            ok = v.unlocked(kind)
            cost = v.cost(kind)
            rr = QRectF(r.x(), y, r.width(), 50)
            if rr.bottom() > y0 and rr.y() < r.bottom():
                on = self.build_kind == kind
                hover = rr.contains(self.mouse)
                box(p, rr, "#2E4A34" if on else "#1E2E22" if hover and ok else "#141E17", GREEN if on else None, 6)
                if not ok:
                    p.setOpacity(0.45)
                emoji(p, QRectF(rr.x() + 4, rr.y(), 40, 50), info["emoji"], 22)
                text(p, QRectF(rr.x() + 48, rr.y() + 4, rr.width() - 140, 22), info["name"], 14, "#FFFFFF",
                     Qt.AlignLeft | Qt.AlignVCenter)
                sub = (f"Uses {STAT_NAMES[info['stat']]}" if info["stat"] is not None else "Joins the floors")
                text(p, QRectF(rr.x() + 48, rr.y() + 24, rr.width() - 140, 20),
                     sub if ok else f"Needs {info['unlock']} dwellers", 11, DIM, Qt.AlignLeft | Qt.AlignVCenter,
                     bold=False)
                text(p, QRectF(rr.x(), rr.y(), rr.width() - 10, 50), f"{cost} 🪙", 13,
                     AMBER if v.caps >= cost else RED, Qt.AlignRight | Qt.AlignVCenter)
                p.setOpacity(1.0)
                if ok:
                    self.hits.append((rr, lambda kind=kind: self._pick_build(kind)))
            y += 56
        self.scroll_max = max(0, y + sc - r.bottom())

    def _p_list(self, p, r):
        v = self.vault
        y = self._title(p, r, "📋 Dwellers", f"{v.population()} of {v.capacity()}  ·  click one to find them")
        sort = self.scroll.get("sort", "name")
        keys = [("name", "Name"), ("level", "Level"), ("happy", "Happy")] + [(str(i), "SPECIAL"[i]) for i in range(7)]
        x = r.x()
        bw = (r.width() - 9 * 3) / 10
        for k, label in keys:
            self._btn(p, QRectF(x, y, bw if len(label) == 1 else bw * 1, 24), label[:5] if len(label) > 1 else label,
                      lambda k=k: self._sort(k), colour=GREEN if sort == k else EDGE, size=10)
            x += bw + 3
        y += 32
        ds = [d for d in v.dwellers]
        if sort == "name":
            ds.sort(key=lambda d: d["name"])
        elif sort == "level":
            ds.sort(key=lambda d: -d["level"])
        elif sort == "happy":
            ds.sort(key=lambda d: -d["happy"])
        else:
            i = int(sort)
            ds.sort(key=lambda d: -v.stat(d, i))
        y0 = y
        sc = self.scroll.get("list", 0)
        y -= sc
        stat = int(sort) if sort.isdigit() else None
        for d in ds:
            rr = QRectF(r.x(), y, r.width(), 30)
            if rr.bottom() > y0 and rr.y() < r.bottom():
                self._dweller_row(p, rr, d, stat)
                where = {"exploring": "🗺️", "returning": "🗺️", "dead": "✝", "dead_out": "✝"}.get(d["state"])
                if where:
                    text(p, QRectF(rr.right() - 110, rr.y(), 30, 30), where, 12, RED if "✝" in where else DIM,
                         family=EMOJI if where == "🗺️" else UI)
            y += 34
        self.scroll_max = max(0, y + sc - r.bottom())

    def _p_waste(self, p, r):
        v = self.vault
        out = [d for d in v.dwellers if d["state"] in ("exploring", "returning", "dead_out")]
        y = self._title(p, r, "🗺️ The Wasteland", f"{len(out)} out there")
        if not out:
            text(p, QRectF(r.x(), y, r.width(), 80), "Nobody's out exploring. Pick a dweller and send them to the "
                 "Wasteland: they'll find caps and gear (and trouble). Recall them when you like - the trip home "
                 "takes half as long as they've been out.", 13, DIM, Qt.AlignLeft | Qt.TextWordWrap, bold=False)
            return
        for d in out:
            ex = d["ex"]
            sel = d["id"] == self.sel_dweller
            rr = QRectF(r.x(), y, r.width(), 76)
            box(p, rr, "#1E2E22" if sel else "#141E17", GREEN if sel else None, 6)
            paint_dweller(p, rr.x() + 18, rr.y() + 50, d, self.t, moving=d["state"] != "dead_out", scale=0.9)
            text(p, QRectF(rr.x() + 38, rr.y() + 4, rr.width() - 140, 20), d["name"], 13, "#FFFFFF", Qt.AlignLeft)
            state = {"exploring": f"Out {mmss(ex['t'])}", "returning": f"Home in {mmss(ex['ret'])}",
                     "dead_out": "Dead"}[d["state"]]
            text(p, QRectF(rr.x(), rr.y() + 4, rr.width() - 8, 20), state, 12,
                 RED if d["state"] == "dead_out" else AMBER, Qt.AlignRight)
            bar(p, QRectF(rr.x() + 38, rr.y() + 28, rr.width() - 50, 7), d["hp"] / v.max_hp(d), GREEN)
            text(p, QRectF(rr.x() + 38, rr.y() + 36, rr.width() - 50, 18),
                 f"🪙 {ex['caps']}   🎒 {len(ex['items'])}   💊 {d['stim']}   ☢️ {d['radaway']}", 11, DIM,
                 Qt.AlignLeft, bold=False)
            bw = 96
            if d["state"] == "exploring":
                self._btn(p, QRectF(rr.right() - bw - 6, rr.y() + 52, bw, 20), "Recall",
                          lambda d=d: self._act(v.recall(d)), size=11)
            elif d["state"] == "dead_out":
                cost = v.revive_cost(d)
                self._btn(p, QRectF(rr.right() - bw - 6, rr.y() + 52, bw, 20), f"Revive {cost}",
                          lambda d=d: self._act(v.revive(d)), size=11, enabled=v.caps >= cost)
            self.hits.append((QRectF(rr.x(), rr.y(), rr.width() - bw - 10, rr.height()),
                              lambda d=d: self._pick_explorer(d)))
            y += 82
        d = v.dweller(self.sel_dweller)
        if d and d.get("ex"):
            text(p, QRectF(r.x(), y + 4, r.width(), 20), f"{d['name']}'s journal", 13, GREEN, Qt.AlignLeft)
            y += 28
            fm = QFontMetrics(font(11, False))
            for line in reversed(d["ex"]["log"][-12:]):
                h = fm.boundingRect(QRect(0, 0, int(r.width()), 200), Qt.TextWordWrap, line).height()
                text(p, QRectF(r.x(), y, r.width(), h), line, 11, "#D8E8D8", Qt.AlignLeft | Qt.TextWordWrap,
                     bold=False)
                y += h + 2

    def _p_storage(self, p, r):
        v = self.vault
        d = v.dweller(self.sel_dweller)
        can_equip = d is not None and d["state"] in ("idle", "walking")
        y = self._title(p, r, "🎒 Storage", f"{len(v.items)}/{v.storage_cap()} items" +
                        (f"  ·  equipping {d['name']}" if can_equip else "  ·  select a dweller to equip them"))
        if not v.items:
            text(p, QRectF(r.x(), y, r.width(), 60), "Nothing in storage yet. Explorers bring weapons and outfits "
                 "home; lunchboxes have them too.", 13, DIM, Qt.AlignLeft | Qt.TextWordWrap, bold=False)
            return
        y0 = y
        sc = self.scroll.get("storage", 0)
        y -= sc
        for it in sorted(v.items, key=lambda i: (i["kind"], i["name"])):
            rr = QRectF(r.x(), y, r.width(), 46)
            if rr.bottom() > y0 and rr.y() < r.bottom():
                if it["kind"] == "weapon":
                    w = WEAPON[it["name"]]
                    rarity, desc, icon = w[3], f"Damage {w[1]}-{w[2]}", "🔫"
                else:
                    o = OUTFIT[it["name"]]
                    rarity, icon = o[2], "👕"
                    desc = " ".join(f"+{b} {STAT_NAMES[i]}" for i, b in o[1].items())
                box(p, rr, "#141E17", (EDGE, BLUE, AMBER)[rarity], 6)
                emoji(p, QRectF(rr.x() + 2, rr.y(), 36, 46), icon, 18)
                text(p, QRectF(rr.x() + 40, rr.y() + 4, rr.width() - 160, 20), it["name"], 13, "#FFFFFF",
                     Qt.AlignLeft | Qt.AlignVCenter)
                text(p, QRectF(rr.x() + 40, rr.y() + 24, rr.width() - 160, 18), f"{RARITY[rarity]} · {desc}", 10,
                     DIM, Qt.AlignLeft | Qt.AlignVCenter, bold=False)
                self._btn(p, QRectF(rr.right() - 112, rr.y() + 10, 54, 26), "Equip",
                          lambda it=it: self._equip(it), enabled=can_equip, size=11)
                self._btn(p, QRectF(rr.right() - 54, rr.y() + 10, 50, 26), f"${v.item_value(it)}",
                          lambda it=it: self._sell(it), size=11)
            y += 52
        self.scroll_max = max(0, y + sc - r.bottom())

    def _p_goals(self, p, r):
        v = self.vault
        y = self._title(p, r, "🍱 Objectives", "Finish them for caps and lunchboxes")
        for o in v.objectives:
            rr = QRectF(r.x(), y, r.width(), 74)
            prog = v.progress(o)
            done = prog >= o["target"]
            box(p, rr, "#1E2E22" if done else "#141E17", GREEN if done else EDGE, 6)
            text(p, QRectF(rr.x() + 10, rr.y() + 6, rr.width() - 20, 20), o["text"], 13, "#FFFFFF", Qt.AlignLeft)
            bar(p, QRectF(rr.x() + 10, rr.y() + 32, rr.width() - 20, 8), prog / o["target"], GREEN)
            kind, n = o["reward"]
            reward = f"🪙 {n} caps" if kind == "caps" else "🍱 a lunchbox"
            text(p, QRectF(rr.x() + 10, rr.y() + 44, 200, 24), f"{prog}/{o['target']}   ·   {reward}", 11, DIM,
                 Qt.AlignLeft | Qt.AlignVCenter, bold=False)
            if done:
                self._btn(p, QRectF(rr.right() - 90, rr.y() + 44, 80, 24), "Claim", lambda o=o: self._claim(o),
                          size=12, fill="#2E4A34")
            y += 82
        y += 10
        rr = QRectF(r.x(), y, r.width(), 90)
        box(p, rr, "#2A2414", AMBER, 8)
        emoji(p, QRectF(rr.x() + 6, rr.y(), 70, 90), "🍱", 40)
        text(p, QRectF(rr.x() + 84, rr.y() + 10, rr.width() - 90, 24), f"Lunchboxes: {v.lunchboxes}", 16, AMBER,
             Qt.AlignLeft)
        text(p, QRectF(rr.x() + 84, rr.y() + 34, rr.width() - 90, 20), "Four cards: caps, supplies, gear... "
             "or a legend", 11, DIM, Qt.AlignLeft, bold=False)
        self._btn(p, QRectF(rr.x() + 84, rr.y() + 56, 120, 26), "Open one", self._open_lunchbox,
                  enabled=v.lunchboxes > 0, size=12)

    def _p_help(self, p, r):
        y = self._title(p, r, "❓ Overseer's Handbook")
        lines = [("Rooms", "Build with 🔨. Rooms must touch the vault; elevators join floors. Three of the same "
                  "kind and level side by side merge into one big room."),
                 ("Dwellers", "Drag a dweller onto a room to put them to work. They're happiest - and best - in "
                  "the room that uses their highest S.P.E.C.I.A.L. (it glows ★ Ideal job)."),
                 ("Resources", "Power, Food and Water rooms fill a bar; tap the bubble to collect (it collects "
                  "every room of that kind). Rush for an instant batch, at the risk of a fire."),
                 ("Babies", "A man and a woman in the Living Quarters, with room to spare, will start a family. "
                  "Children grow up in three minutes."),
                 ("Trouble", "Fires, radroaches and raiders strike now and then. Drag dwellers in to fight; give "
                  "them weapons; heal them with Stimpaks."),
                 ("Wasteland", "Send a dweller out with Stimpaks and RadAway to find caps and gear. Recall them "
                  "any time; the trip home takes half as long."),
                 ("Camera", "Drag the vault to look around; scroll to zoom. ⏸ 1× 2× 4× change the speed.")]
        for head, body in lines:
            text(p, QRectF(r.x(), y, r.width(), 18), head, 13, AMBER, Qt.AlignLeft)
            h = QFontMetrics(font(12, False)).boundingRect(QRect(0, 0, int(r.width()), 400), Qt.TextWordWrap,
                                                           body).height()
            text(p, QRectF(r.x(), y + 18, r.width(), h + 4), body, 12, "#E0EAE0",
                 Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, bold=False)
            y += h + 28
        sure = self.confirm == ("new", 0)
        self._btn(p, QRectF(r.x(), min(y + 6, r.bottom() - 40), r.width(), 34),
                  "Really start over? Click again" if sure else "Start a new vault", self._new_vault, colour=RED)

    # ---- the lunchbox ----
    def _draw_lunchbox(self, p):
        p.fillRect(self.rect(), QColor(0, 0, 0, 170))
        w, h = self.width(), self.height()
        text(p, QRectF(0, h * 0.14, w, 50), "🍱", 40, "#000000", family=EMOJI)
        text(p, QRectF(0, h * 0.22, w, 40), "Lunchbox!", 30, AMBER)
        cards = self.lunch
        cw, chh = 170, 230
        x0 = w / 2 - (len(cards) * (cw + 20) - 20) / 2
        for k, c in enumerate(cards):
            age = self.t - self.lunch_t - k * 0.45
            flip = max(0.0, min(1.0, age / 0.35))
            rr = QRectF(x0 + k * (cw + 20), h * 0.32, cw, chh)
            p.save()
            p.translate(rr.center())
            p.scale(max(0.05, abs(math.cos(flip * math.pi))) if flip < 1 else 1.0, 1.0)
            local = QRectF(-cw / 2, -chh / 2, cw, chh)
            if flip < 0.5:
                box(p, local, "#2E4E8A", AMBER, 12, 3)
                text(p, local, "?", 60, AMBER)
            else:
                col = ("#9AA0A0", BLUE, AMBER)[c["rarity"]]
                box(p, local, "#F4EED8", col, 12, 4)
                icon = {"caps": "🪙", "power": "⚡", "food": "🍔", "water": "💧", "stimpak": "💊",
                        "radaway": "☢️", "weapon": "🔫", "outfit": "👕", "dweller": "🧑"}[c["kind"]]
                emoji(p, QRectF(local.x(), local.y() + 30, cw, 80), icon, 48)
                text(p, QRectF(local.x() + 10, local.y() + 120, cw - 20, 60), c["label"], 16, "#2A2A2A",
                     Qt.AlignCenter | Qt.TextWordWrap)
                text(p, QRectF(local.x(), local.bottom() - 36, cw, 24), RARITY[c["rarity"]], 13, col)
            p.restore()
        self._btn(p, QRectF(w / 2 - 80, h * 0.32 + chh + 30, 160, 40), "Great!", self._close_lunchbox, size=15)

    # ---- actions ----
    def _set_speed(self, sp):
        self.speed = sp

    def _toggle_panel(self, key):
        if self.panel == key:
            self._close_panel()
            return
        self.panel = key
        self.confirm = None
        if key != "build":
            self.build_kind = None

    def _close_panel(self):
        self.panel = None
        self.sel_room = None
        self.build_kind = None
        self.explore_pick = None
        self.confirm = None

    def _act(self, err):
        if err:
            self.toasts.append([err, "alert", self.t + 3])

    def _select_dweller(self, d, center=False):
        self.sel_dweller = d["id"]
        self.sel_room = None
        self.explore_pick = None
        self.panel = "dweller"
        if center and d["state"] not in ("exploring", "returning", "dead_out"):
            pos = self.dweller_pos(d)
            v = self.view()
            self.cam = QPointF(pos.x() - v.width() / self.zoom / 2 + SIDE / self.zoom / 2,
                               pos.y() - v.height() / self.zoom / 2)

    def _select_room(self, r):
        self.sel_room = r["id"]
        self.panel = "room"
        self.confirm = None

    def _collect(self, kind):
        got, caps = self.vault.collect(kind)
        if got:
            self.toasts.append([f"+{int(got)} {RESOURCES[kind][1]}" + (f"  ·  +{caps} caps" if caps else ""), "good",
                                self.t + 2.5])

    def _rush(self, room):
        err = self.vault.rush(room)
        self._act(err)

    def _upgrade(self, room):
        self._act(self.vault.upgrade(room))

    def _destroy(self, room):
        if self.confirm != ("destroy", room["id"]):
            self.confirm = ("destroy", room["id"])
            return
        self.confirm = None
        err = self.vault.destroy(room)
        self._act(err)
        if not err:
            self._close_panel()

    def _pick_build(self, kind):
        self.build_kind = None if self.build_kind == kind else kind

    def _sort(self, key):
        self.scroll["sort"] = key
        self.scroll["list"] = 0

    def _unequip(self, d, slot):
        self._act(self.vault.unequip(d, slot))

    def _equip(self, it):
        d = self.vault.dweller(self.sel_dweller)
        if d:
            self._act(self.vault.equip(d, it))

    def _sell(self, it):
        v = self.vault.sell(it)
        if v:
            self.toasts.append([f"Sold the {it['name']} for {v} caps", "good", self.t + 2.5])

    def _bury(self, d):
        self.vault.bury(d)
        self.sel_dweller = None
        self.panel = None

    def _pick_explore(self):
        v = self.vault
        self.explore_pick = [min(5, v.stimpaks), min(3, v.radaway)]

    def _pick_adjust(self, k, n, have=0):
        cur = self.explore_pick[k] + n
        limit = (self.vault.stimpaks, self.vault.radaway)[k]
        self.explore_pick[k] = max(0, min(limit, 25, cur))

    def _cancel_explore(self):
        self.explore_pick = None

    def _explore(self, d):
        sp, rp = self.explore_pick
        self.explore_pick = None
        self._act(self.vault.explore(d, sp, rp))

    def _pick_explorer(self, d):
        self.sel_dweller = d["id"]

    def _claim(self, o):
        self._act(self.vault.claim(o))

    def _open_lunchbox(self):
        cards = self.vault.open_lunchbox()
        if cards:
            self.lunch = cards
            self.lunch_t = self.t

    def _close_lunchbox(self):
        self.lunch = None

    def _new_vault(self):
        if self.confirm != ("new", 0):
            self.confirm = ("new", 0)
            return
        self.vault = Vault()
        self.seen_msg = 0
        self.toasts = []
        self.cam = QPointF(-90, -150)
        self._close_panel()
        self.sel_dweller = None
        self._save()

    # ---- input ----
    def wheelEvent(self, e):
        if self.panel and self._panel_rect().contains(e.position()):
            key = {"build": "build", "list": "list", "storage": "storage"}.get(self.panel)
            if key:
                cur = self.scroll.get(key, 0) - e.angleDelta().y() / 2
                self.scroll[key] = max(0, min(getattr(self, "scroll_max", 0) + self.scroll.get(key, 0), cur))
            return
        before = self.to_world(e.position())
        f = 1.15 if e.angleDelta().y() > 0 else 1 / 1.15
        self.zoom = max(0.45, min(2.2, self.zoom * f))
        v = self.view()
        self.cam = QPointF(before.x() - (e.position().x() - v.x()) / self.zoom,
                           before.y() - (e.position().y() - v.y()) / self.zoom)

    def mouseMoveEvent(self, e):
        old = self.mouse
        self.mouse = e.position()
        d = self.drag
        if not d:
            return
        if not d["moved"] and (e.position() - d["start"]).manhattanLength() > 6:
            d["moved"] = True
        if d["moved"] and d.get("pan"):
            delta = (self.mouse - old) / self.zoom
            self.cam = QPointF(self.cam.x() - delta.x(), self.cam.y() - delta.y())

    def mousePressEvent(self, e):
        self.mouse = e.position()
        if e.button() == Qt.RightButton:
            self.build_kind = None
            self.drag = None
            return
        if e.button() != Qt.LeftButton:
            return
        pos = e.position()
        for rect, action in reversed(self.hits):
            if rect.contains(pos):
                action()
                return
        if self.lunch is not None:
            return
        if self.panel and self._panel_rect().contains(pos):
            return
        if not self.view().contains(pos):
            return
        wp = self.to_world(pos)
        d = None if self.build_kind else self._dweller_under(wp)
        if d is not None and d["state"] != "dead":
            self.drag = {"start": pos, "moved": False, "dweller": d["id"]}
        else:
            self.drag = {"start": pos, "moved": False, "pan": True, "dead": d["id"] if d else None}

    def mouseReleaseEvent(self, e):
        d = self.drag
        self.drag = None
        if not d or e.button() != Qt.LeftButton:
            return
        v = self.vault
        wp = self.to_world(e.position())
        if d.get("dweller"):
            dw = v.dweller(d["dweller"])
            if dw is None:
                return
            if d["moved"]:
                room = self._room_under(wp)
                if room is not None:
                    err = v.assign(dw, room)
                    self._act(err)
                    if not err and self.panel == "room":
                        self.sel_room = room["id"]
            else:
                self._select_dweller(dw)
            return
        if d["moved"]:
            return
        if d.get("dead"):
            self._select_dweller(v.dweller(d["dead"]))
            return
        if self.build_kind:
            kind = self.build_kind
            w = 1 if kind == "elevator" else SEG
            f = math.floor(wp.y() / FH)
            for c in range(math.floor(wp.x() / CW) - w + 1, math.floor(wp.x() / CW) + 1):
                if v.can_place(kind, f, c) and QRectF(c * CW, f * FH, w * CW, FH).contains(wp):
                    err = v.build(kind, f, c)
                    self._act(err)
                    return
            return
        for r in v.rooms:
            if r["ready"]:
                c = self._bubble(r)
                if (wp - c).manhattanLength() < 20:
                    self._collect(ROOMS[r["type"]]["produce"] if ROOMS[r["type"]]["produce"] != "nuka" else "food")
                    return
        room = self._room_under(wp)
        if room is not None:
            self._select_room(room)
        elif self.panel in ("room", "dweller"):
            self._close_panel()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            if self.lunch is not None:
                self.lunch = None
            elif self.build_kind:
                self.build_kind = None
            else:
                self._close_panel()
        elif e.key() == Qt.Key_Space:
            self.speed = 1 if self.speed == 0 else 0

    def closeEvent(self, event):
        self._save()
        self.timer.stop()
        event.accept()


def shelter_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#1A1A1A"), 1))
    p.setBrush(QColor("#9A9A8A"))
    teeth = QPainterPath()
    for k in range(12):
        a = k * math.pi * 2 / 12
        for da, rad in ((-0.12, 15), (0.12, 15), (0.16, 12.5), (0.36, 12.5)):
            pt = QPointF(16 + math.cos(a + da) * rad, 16 + math.sin(a + da) * rad)
            if k == 0 and da == -0.12:
                teeth.moveTo(pt)
            else:
                teeth.lineTo(pt)
    teeth.closeSubpath()
    p.drawPath(teeth)
    p.setBrush(QColor(SUIT))
    p.drawEllipse(QPointF(16, 16), 10, 10)
    p.setBrush(QColor(AMBER))
    p.setPen(Qt.NoPen)
    f = QFont(UI)
    f.setPixelSize(11)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor(AMBER))
    p.drawText(QRectF(6, 6, 20, 20), Qt.AlignCenter, "CS")
    p.end()
    return QIcon(pm)


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = Shelter(desktop)
        win = host.window(desktop, TITLE, body, shelter_icon(), (1300, 820))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.close()
