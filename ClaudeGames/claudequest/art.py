"""ClaudeQuest's art, painted in code: wolves and the animals of the valley in side view (the world is seen from a
three-quarter angle above), trees and rocks for each season, and terrain tiles.

Every animal is drawn standing on (0, 0) facing right; the caller translates, and mirrors for facing left.
"""
import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, \
    QRadialGradient

from pathlib import Path

TITLE = Path(__file__).resolve().parent / "assets" / "title.jpg"
TILE = 40

# coat: (base, saddle/back, belly/light, legs)
COATS = {
    "gray": ("#8E8A84", "#4E4A46", "#DCD6CC", "#7A746C"),
    "tan": ("#C09A6A", "#7A5A3A", "#EADAC0", "#A88458"),
    "black": ("#3A3634", "#1E1C1B", "#6A6460", "#2E2B29"),
    "white": ("#E8E4DC", "#BEB8AE", "#FAF8F2", "#D4CEC4"),
    "red": ("#B06A3C", "#6A3A20", "#E8C8A4", "#8E5430"),
    "silver": ("#A8ACB0", "#5E6266", "#E4E6E8", "#8E9296"),
}
RIVAL_COATS = ["black", "gray", "red", "silver"]


def _c(h, a=255):
    c = QColor(h)
    c.setAlpha(a)
    return c


def shadow(p, w, h=None):
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 70))
    p.drawEllipse(QPointF(0, 0), w, h if h is not None else w * 0.22)


# ---- wolves ------------------------------------------------------------------------------------------------------

def draw_wolf(p, coat="gray", s=1.0, pose="stand", phase=0.0, hurt=False, glow=None):
    """A wolf facing right, feet on (0, 0). s=1.0 is an adult (about 70 px nose to tail). pose: stand, trot, run,
    sneak, lie, sleep, eat, howl, attack, dead."""
    base, saddle, belly, legs = (QColor(x) for x in COATS.get(coat, COATS["gray"]))
    line = QPen(base.darker(190), 0.9 * s)
    p.save()
    p.scale(s, s)
    if pose == "dead":
        _wolf_dead(p, base, saddle, belly, legs, line)
        p.restore()
        return
    lying = pose in ("lie", "sleep")
    shadow(p, 30 if not lying else 32, 6)
    if glow is not None:
        g = QRadialGradient(QPointF(0, -24), 46)
        g.setColorAt(0, _c(glow, 90))
        g.setColorAt(1, _c(glow, 0))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(0, -24), 46, 34)
    if lying:
        _wolf_lying(p, base, saddle, belly, legs, line, pose == "sleep", phase)
        p.restore()
        return
    run = pose == "run"
    moving = pose in ("trot", "run", "sneak", "attack")
    amp = 0.0 if not moving else (0.9 if run else 0.5)
    low = 6 if pose == "sneak" else 0
    bob = abs(math.sin(phase * 2)) * (2.5 if run else 1.2) if moving else 0
    body_y = -28 + low - bob
    stretch = 1.12 if run else 1.0

    def leg(x, ang, near):
        hip = QPointF(x, body_y + 6)
        knee = QPointF(x + math.sin(ang) * 9, body_y + 15)
        foot = QPointF(x + math.sin(ang) * 15, -1 + (0 if math.cos(ang) > -0.2 else -3))
        p.setPen(QPen((legs if near else legs.darker(130)), 4.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        path = QPainterPath(hip)
        path.quadTo(knee, foot)
        p.drawPath(path)
        p.setPen(QPen(legs.darker(160), 2.4, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(foot, foot + QPointF(3, 0))

    a = phase * 2
    # far legs
    leg(-13 * stretch, math.sin(a + math.pi) * amp, False)
    leg(12 * stretch, math.sin(a) * amp, False)
    # tail
    sway = math.sin(phase * 1.5) * 3
    tail = QPainterPath(QPointF(-21 * stretch, body_y - 3))
    up = -8 if pose == "attack" else (0 if not run else -4)
    tail.cubicTo(QPointF(-32 * stretch, body_y + up), QPointF(-38 * stretch, body_y + 10 + sway + up),
                 QPointF(-36 * stretch, body_y + 20 + sway + up * 0.5))
    tail.cubicTo(QPointF(-31 * stretch, body_y + 14 + sway), QPointF(-27 * stretch, body_y + 6),
                 QPointF(-20 * stretch, body_y + 3))
    p.setPen(line)
    p.setBrush(base)
    p.drawPath(tail)
    p.setPen(Qt.NoPen)
    p.setBrush(saddle)
    p.drawEllipse(QPointF(-36 * stretch, body_y + 18 + sway + up * 0.5), 2.6, 3.4)
    # body
    body = QPainterPath()
    body.addEllipse(QPointF(0, body_y), 23 * stretch, 9.5)
    g = QLinearGradient(0, body_y - 10, 0, body_y + 10)
    g.setColorAt(0, saddle)
    g.setColorAt(0.45, base)
    g.setColorAt(1, belly)
    p.setPen(line)
    p.setBrush(QBrush(g))
    p.drawPath(body)
    # chest and neck
    head_y = body_y - 12 + low * 0.6
    head_x = 27 * stretch
    if pose == "eat":
        head_x, head_y = 30, -9
    elif pose == "howl":
        head_x, head_y = 21, body_y - 26
    elif run:
        head_x, head_y = 31, body_y - 6
    elif pose == "sneak":
        head_x, head_y = 29, body_y - 4
    elif pose == "attack":
        head_x, head_y = 32, body_y - 7
    neck = QPainterPath(QPointF(12 * stretch, body_y - 7))
    neck.lineTo(QPointF(head_x - 6, head_y - 4))
    neck.lineTo(QPointF(head_x - 1, head_y + 5))
    neck.lineTo(QPointF(17 * stretch, body_y + 7))
    neck.closeSubpath()
    p.setBrush(base)
    p.drawPath(neck)
    p.setPen(Qt.NoPen)
    p.setBrush(belly)
    p.drawEllipse(QPointF(17 * stretch, body_y + 2), 6, 6.5)
    # near legs
    leg(-10 * stretch, math.sin(a) * amp, True)
    leg(15 * stretch, math.sin(a + math.pi) * amp, True)
    _wolf_head(p, QPointF(head_x, head_y), base, saddle, belly, line,
               up=(pose == "howl"), open_mouth=pose in ("attack", "howl"), down=(pose == "eat"))
    if hurt:
        p.setPen(QPen(QColor("#B01818"), 1.6))
        p.drawLine(QPointF(-6, body_y - 4), QPointF(0, body_y + 2))
        p.drawLine(QPointF(-2, body_y - 5), QPointF(4, body_y + 1))
    p.restore()


def _wolf_head(p, c, base, saddle, belly, line, up=False, open_mouth=False, down=False):
    p.save()
    p.translate(c)
    if up:
        p.rotate(-55)
    elif down:
        p.rotate(35)
    # ears
    p.setPen(line)
    p.setBrush(saddle)
    p.drawPolygon(QPolygonF([QPointF(-5, -5), QPointF(-4, -15), QPointF(1, -6)]))
    p.setBrush(base)
    p.drawPolygon(QPolygonF([QPointF(-1, -6), QPointF(2, -15), QPointF(5, -5)]))
    # skull and muzzle
    head = QPainterPath()
    head.addEllipse(QPointF(0, 0), 8, 7)
    p.setBrush(base)
    p.drawPath(head)
    muzzle = QPainterPath(QPointF(4, -3.5))
    muzzle.lineTo(QPointF(14, -1.5))
    muzzle.quadTo(QPointF(16, 1), QPointF(14, 2.5 if not open_mouth else 1))
    muzzle.lineTo(QPointF(4, 5))
    muzzle.closeSubpath()
    p.setBrush(belly)
    p.drawPath(muzzle)
    if open_mouth:
        jaw = QPainterPath(QPointF(5, 4))
        jaw.lineTo(QPointF(13, 6))
        jaw.lineTo(QPointF(12, 8))
        jaw.lineTo(QPointF(4, 6.5))
        jaw.closeSubpath()
        p.setBrush(belly.darker(110))
        p.drawPath(jaw)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#8A2A2A"))
        p.drawPolygon(QPolygonF([QPointF(6, 4), QPointF(13, 2.6), QPointF(12.5, 5.6)]))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#1A1614"))
    p.drawEllipse(QPointF(14.6, -0.6), 1.7, 1.5)
    p.setBrush(QColor("#E0B030"))
    p.drawEllipse(QPointF(3.5, -2.5), 1.6, 1.2)
    p.setBrush(QColor("#101010"))
    p.drawEllipse(QPointF(3.9, -2.5), 0.7, 0.8)
    # cheek ruff
    p.setBrush(belly)
    p.drawEllipse(QPointF(-3, 3.5), 4, 3)
    p.restore()


def _wolf_lying(p, base, saddle, belly, legs, line, sleep, phase):
    breathe = math.sin(phase * 0.8) * 0.6
    p.setPen(line)
    p.setBrush(base)
    tail = QPainterPath(QPointF(-18, -8))
    tail.cubicTo(QPointF(-30, -6), QPointF(-30, 2), QPointF(-12, 1))
    tail.cubicTo(QPointF(-20, -2), QPointF(-22, -6), QPointF(-16, -10))
    p.drawPath(tail)
    g = QLinearGradient(0, -20, 0, 0)
    g.setColorAt(0, saddle)
    g.setColorAt(0.5, base)
    g.setColorAt(1, belly)
    p.setBrush(QBrush(g))
    p.drawEllipse(QPointF(-2, -9 - breathe), 22, 9 + breathe)
    p.setPen(QPen(legs, 4, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(10, -3), QPointF(26, -1))
    p.drawLine(QPointF(14, -2), QPointF(28, 1))
    if sleep:
        _wolf_head(p, QPointF(22, -7), base, saddle, belly, line, down=True)
    else:
        _wolf_head(p, QPointF(21, -16), base, saddle, belly, line)


def _wolf_dead(p, base, saddle, belly, legs, line):
    shadow(p, 30, 6)
    p.setPen(line)
    p.setBrush(base)
    p.drawEllipse(QPointF(0, -7), 24, 8)
    p.setPen(QPen(legs, 4, Qt.SolidLine, Qt.RoundCap))
    for x in (-12, -6, 10, 16):
        p.drawLine(QPointF(x, -2), QPointF(x + 4, 6))
    _wolf_head(p, QPointF(24, -5), base, saddle, belly, line)


# ---- the other animals -------------------------------------------------------------------------------------------

PREY = {
    # name: (length, height, body colour, dark (neck/legs), light (rump/belly), speed px/s, hp, meat)
    "elk": (40, 46, "#B88A58", "#5A3A22", "#EAD8B0", 240, 230, 120),
    "deer": (28, 34, "#A87A52", "#6A4A30", "#EEE2CC", 260, 105, 60),
    "bison": (48, 44, "#4A3424", "#2A1C12", "#6A4A34", 190, 460, 220),
    "hare": (10, 9, "#A89880", "#6A5A48", "#E8E0D0", 280, 10, 8),
    "bear": (40, 40, "#6A4426", "#3E2614", "#8A6040", 200, 380, 0),
    "cougar": (36, 26, "#C8A070", "#7A5A38", "#EADCC4", 280, 160, 0),
}


def draw_animal(p, kind, phase=0.0, moving=False, s=1.0, bull=False, calf=False, dead=False, winter=False):
    if kind == "hare":
        _hare(p, phase, moving, s, dead, winter)
        return
    length, height, body_c, dark_c, light_c, *_ = PREY[kind]
    body_c, dark_c, light_c = QColor(body_c), QColor(dark_c), QColor(light_c)
    if calf:
        s *= 0.62
        if kind == "elk":
            body_c = QColor("#C49A6A")
    p.save()
    p.scale(s, s)
    line = QPen(dark_c.darker(150), 1.0)
    L, H = length, height
    if dead:
        shadow(p, L * 0.9, 7)
        p.setPen(line)
        p.setBrush(body_c)
        p.drawEllipse(QPointF(0, -9), L * 0.75, 10)
        p.setPen(QPen(dark_c, 4, Qt.SolidLine, Qt.RoundCap))
        for x in (-L * 0.4, -L * 0.25, L * 0.3, L * 0.45):
            p.drawLine(QPointF(x, -3), QPointF(x + 6, 8))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(140, 20, 20, 160))
        p.drawEllipse(QPointF(L * 0.1, -12), 8, 4)
        p.restore()
        return
    shadow(p, L * 0.8, 7 + L * 0.06)
    body_y = -H * 0.62
    amp = 0.75 if moving else 0.0
    a = phase * 2

    def leg(x, ang, near, thick=4.5):
        top = QPointF(x, body_y + H * 0.12)
        foot = QPointF(x + math.sin(ang) * H * 0.3, -1)
        p.setPen(QPen(dark_c if near else dark_c.darker(130), thick, Qt.SolidLine, Qt.RoundCap))
        path = QPainterPath(top)
        path.quadTo(QPointF(x + math.sin(ang) * H * 0.18, body_y + H * 0.42), foot)
        p.drawPath(path)

    legw = 6.5 if kind in ("bison", "bear") else 3.6
    leg(-L * 0.42, math.sin(a + math.pi) * amp, False, legw)
    leg(L * 0.38, math.sin(a) * amp, False, legw)
    # tail
    p.setPen(Qt.NoPen)
    if kind == "cougar":
        tail = QPainterPath(QPointF(-L * 0.5, body_y))
        tail.cubicTo(QPointF(-L * 0.9, body_y + 4), QPointF(-L * 1.0, body_y + 18 + math.sin(phase) * 3),
                     QPointF(-L * 0.85, body_y + 22))
        p.setPen(QPen(body_c, 5, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawPath(tail)
        p.setPen(QPen(dark_c, 5, Qt.SolidLine, Qt.RoundCap))
        p.drawPoint(QPointF(-L * 0.85, body_y + 22))
    elif kind in ("elk", "deer"):
        p.setBrush(light_c)
        p.drawEllipse(QPointF(-L * 0.52, body_y - 2), 7 if kind == "elk" else 5, 8)
    # body
    p.setPen(line)
    g = QLinearGradient(0, body_y - H * 0.25, 0, body_y + H * 0.25)
    g.setColorAt(0, body_c.darker(115))
    g.setColorAt(0.6, body_c)
    g.setColorAt(1, light_c if kind not in ("bison", "bear") else body_c.darker(120))
    p.setBrush(QBrush(g))
    if kind == "bison":
        hump = QPainterPath(QPointF(-L * 0.5, body_y + 6))
        hump.cubicTo(QPointF(-L * 0.5, body_y - 14), QPointF(L * 0.1, body_y - 30), QPointF(L * 0.35, body_y - 14))
        hump.cubicTo(QPointF(L * 0.55, body_y), QPointF(L * 0.45, body_y + 14), QPointF(0, body_y + 14))
        hump.cubicTo(QPointF(-L * 0.4, body_y + 14), QPointF(-L * 0.55, body_y + 12), QPointF(-L * 0.5, body_y + 6))
        p.drawPath(hump)
        p.setPen(Qt.NoPen)
        p.setBrush(dark_c)
        p.drawEllipse(QPointF(L * 0.25, body_y - 6), L * 0.28, 16)
    elif kind == "bear":
        p.drawEllipse(QPointF(0, body_y), L * 0.6, H * 0.32)
        p.drawEllipse(QPointF(L * 0.1, body_y - 6), L * 0.3, H * 0.25)
    else:
        p.drawEllipse(QPointF(0, body_y), L * 0.56, H * (0.2 if kind == "cougar" else 0.24))
        if kind == "elk":
            p.setPen(Qt.NoPen)
            p.setBrush(light_c)
            p.drawEllipse(QPointF(-L * 0.42, body_y - 1), 9, 9)
    leg(-L * 0.36, math.sin(a) * amp, True, legw)
    leg(L * 0.44, math.sin(a + math.pi) * amp, True, legw)
    # neck and head
    p.setPen(line)
    if kind in ("elk", "deer"):
        nx, ny = L * 0.62, body_y - H * 0.42
        neck = QPainterPath(QPointF(L * 0.3, body_y - H * 0.14))
        neck.lineTo(QPointF(nx - 3, ny))
        neck.lineTo(QPointF(nx + 5, ny + 6))
        neck.lineTo(QPointF(L * 0.5, body_y + H * 0.1))
        neck.closeSubpath()
        p.setBrush(dark_c if kind == "elk" else body_c)
        p.drawPath(neck)
        head = QPainterPath(QPointF(nx - 4, ny - 4))
        head.lineTo(QPointF(nx + 13, ny + 3))
        head.lineTo(QPointF(nx + 12, ny + 7))
        head.lineTo(QPointF(nx - 2, ny + 6))
        head.closeSubpath()
        p.setBrush(body_c.darker(110))
        p.drawPath(head)
        p.setBrush(dark_c)
        p.drawPolygon(QPolygonF([QPointF(nx - 3, ny - 3), QPointF(nx - 9, ny - 10), QPointF(nx, ny - 4)]))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#101010"))
        p.drawEllipse(QPointF(nx + 2, ny), 1.3, 1.3)
        if bull and not calf:
            p.setPen(QPen(QColor("#E8DCC0"), 2.2, Qt.SolidLine, Qt.RoundCap))
            base_pt = QPointF(nx - 1, ny - 4)
            tip = QPointF(nx - 14, ny - 34)
            p.drawLine(base_pt, tip)
            for t in (0.3, 0.55, 0.8):
                q = QPointF(base_pt.x() + (tip.x() - base_pt.x()) * t, base_pt.y() + (tip.y() - base_pt.y()) * t)
                p.drawLine(q, q + QPointF(9, -6))
    elif kind == "bison":
        hx, hy = L * 0.52, body_y + 2
        p.setBrush(dark_c)
        p.drawEllipse(QPointF(hx, hy), 11, 12)
        p.setPen(QPen(QColor("#D8CCB0"), 2.4, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(QRectF(hx - 8, hy - 16, 10, 12), 90 * 16, 120 * 16)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#101010"))
        p.drawEllipse(QPointF(hx + 5, hy - 2), 1.3, 1.3)
        p.setBrush(dark_c.darker(130))
        p.drawEllipse(QPointF(hx + 1, hy + 11), 5, 4)
    elif kind == "bear":
        hx, hy = L * 0.6, body_y - 4
        p.setBrush(body_c)
        p.drawEllipse(QPointF(hx, hy), 11, 10)
        p.drawEllipse(QPointF(hx - 5, hy - 9), 4, 4)
        p.setBrush(light_c)
        p.drawEllipse(QPointF(hx + 9, hy + 2), 6, 4.5)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#101010"))
        p.drawEllipse(QPointF(hx + 14, hy + 1), 2, 1.6)
        p.drawEllipse(QPointF(hx + 3, hy - 3), 1.3, 1.3)
    elif kind == "cougar":
        hx, hy = L * 0.62, body_y - 6
        p.setBrush(body_c)
        p.drawEllipse(QPointF(hx, hy), 8, 7)
        p.drawPolygon(QPolygonF([QPointF(hx - 4, hy - 5), QPointF(hx - 3, hy - 11), QPointF(hx + 1, hy - 6)]))
        p.setBrush(light_c)
        p.drawEllipse(QPointF(hx + 6, hy + 2), 4, 3)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#101010"))
        p.drawEllipse(QPointF(hx + 9.5, hy + 1), 1.4, 1.2)
        p.setBrush(QColor("#C8B020"))
        p.drawEllipse(QPointF(hx + 2, hy - 2), 1.4, 1.1)
    if winter and kind in ("elk", "bison"):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 140))
        p.drawEllipse(QPointF(0, body_y - H * 0.2), L * 0.4, 4)
    p.restore()


def _hare(p, phase, moving, s, dead, winter):
    p.save()
    p.scale(s, s)
    fur = QColor("#F2F0EA" if winter else "#A89880")
    dark = QColor("#6A5A48") if not winter else QColor("#B8B4AC")
    hop = abs(math.sin(phase * 3)) * 6 if moving else 0
    shadow(p, 8, 2.4)
    p.setPen(QPen(dark, 0.8))
    p.setBrush(fur)
    if dead:
        p.drawEllipse(QPointF(0, -3), 8, 3.5)
        p.restore()
        return
    p.drawEllipse(QPointF(0, -7 - hop), 8, 5.5)
    p.drawEllipse(QPointF(7, -11 - hop), 4, 3.5)
    p.drawEllipse(QPointF(5, -18 - hop), 1.6, 5)
    p.drawEllipse(QPointF(7.5, -18 - hop), 1.6, 5)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#101010"))
    p.drawEllipse(QPointF(8.6, -11.5 - hop), 0.9, 0.9)
    p.setBrush(QColor("#FFFFFF"))
    p.drawEllipse(QPointF(-7.5, -8 - hop), 2.4, 2.4)
    p.restore()


def draw_carcass(p, kind, meat_frac, winter=False):
    """What's left of a kill: the body, then bones."""
    if meat_frac > 0.25:
        draw_animal(p, kind if kind in PREY else "elk", dead=True, winter=winter,
                    s=0.6 if kind == "hare" else 1.0)
    p.save()
    p.setPen(QPen(QColor("#EDE6D6"), 2.2, Qt.SolidLine, Qt.RoundCap))
    if meat_frac <= 0.6:
        for i in range(4):
            x = -14 + i * 7
            p.drawLine(QPointF(x, -10), QPointF(x + 3, -2))
        p.drawLine(QPointF(-18, -6), QPointF(14, -6))
    p.restore()


# ---- trees, rocks and the den ------------------------------------------------------------------------------------

SEASON_LEAVES = {"spring": "#6FB03E", "summer": "#4E9030", "autumn": "#E0A820", "winter": None}


def decor_pixmap(kind, season, variant=0):
    """A tree/rock/bush picture and its anchor (the point that sits on the ground)."""
    w, h = 90, 130
    pm = QPixmap(w, h)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    rnd = random.Random(f"{kind}{variant}")
    cx, cy = w / 2, h - 10
    snow = season == "winter"
    if kind == "pine":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 60))
        p.drawEllipse(QPointF(cx, cy), 20, 6)
        p.setBrush(QColor("#5A3A22"))
        p.drawRect(QRectF(cx - 3, cy - 18, 6, 18))
        scale = 0.85 + rnd.random() * 0.3
        for i, (y, hw) in enumerate(((-14, 24), (-38, 20), (-60, 15), (-80, 10))):
            y *= scale
            hw *= scale
            col = QColor(["#1E4A2C", "#24583A", "#2C6644", "#34724C"][i])
            p.setPen(QPen(col.darker(140), 1))
            p.setBrush(col)
            p.drawPolygon(QPolygonF([QPointF(cx - hw, cy + y), QPointF(cx + hw, cy + y),
                                     QPointF(cx, cy + y - 30 * scale)]))
            if snow:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(250, 252, 255, 235))
                p.drawPolygon(QPolygonF([QPointF(cx - hw * 0.55, cy + y - 12 * scale),
                                         QPointF(cx + hw * 0.55, cy + y - 12 * scale),
                                         QPointF(cx, cy + y - 30 * scale)]))
    elif kind == "aspen":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 55))
        p.drawEllipse(QPointF(cx, cy), 16, 5)
        p.setBrush(QColor("#E8E4DA"))
        p.drawRect(QRectF(cx - 2.5, cy - 60, 5, 60))
        p.setPen(QPen(QColor("#3A3A3A"), 1))
        for y in range(-55, -5, 9):
            p.drawLine(QPointF(cx - 2, cy + y), QPointF(cx + 1, cy + y))
        leaves = SEASON_LEAVES[season]
        if leaves:
            for dx, dy, r in ((-10, -62, 13), (9, -66, 13), (0, -78, 14), (-4, -70, 11)):
                c = QColor(leaves).lighter(100 + rnd.randint(-10, 20))
                p.setPen(QPen(c.darker(140), 1))
                p.setBrush(c)
                p.drawEllipse(QPointF(cx + dx, cy + dy), r, r * 0.9)
        else:
            p.setPen(QPen(QColor("#9A9488"), 1.4))
            for ang in (-50, -20, 15, 45):
                rad = math.radians(ang - 90)
                p.drawLine(QPointF(cx, cy - 55), QPointF(cx + math.cos(rad) * 18, cy - 55 + math.sin(rad) * 22))
    elif kind == "rock":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 60))
        p.drawEllipse(QPointF(cx, cy), 20, 6)
        p.setPen(QPen(QColor("#4A4A4E"), 1))
        p.setBrush(QColor("#8A8A90"))
        sc = 0.8 + rnd.random() * 0.6
        p.drawPolygon(QPolygonF([QPointF(cx - 18 * sc, cy), QPointF(cx - 13 * sc, cy - 14 * sc),
                                 QPointF(cx - 2 * sc, cy - 22 * sc), QPointF(cx + 12 * sc, cy - 16 * sc),
                                 QPointF(cx + 18 * sc, cy - 2 * sc), QPointF(cx + 4 * sc, cy + 4 * sc)]))
        p.setBrush(QColor("#A8A8AE") if not snow else QColor("#F4F6FA"))
        p.drawPolygon(QPolygonF([QPointF(cx - 13 * sc, cy - 14 * sc), QPointF(cx - 2 * sc, cy - 22 * sc),
                                 QPointF(cx + 12 * sc, cy - 16 * sc), QPointF(cx, cy - 10 * sc)]))
    elif kind == "sage":
        col = QColor("#8A9A78") if not snow else QColor("#C8D0C4")
        for dx, dy, r in ((-6, -5, 7), (6, -6, 7), (0, -10, 8)):
            p.setPen(QPen(col.darker(140), 1))
            p.setBrush(col)
            p.drawEllipse(QPointF(cx + dx, cy + dy), r, r * 0.75)
    elif kind == "log":
        p.setPen(QPen(QColor("#3A2414"), 1))
        p.setBrush(QColor("#7A5230"))
        p.drawRoundedRect(QRectF(cx - 24, cy - 9, 48, 9), 4, 4)
        p.setBrush(QColor("#C8A070"))
        p.drawEllipse(QPointF(cx + 24, cy - 4.5), 3, 4.5)
        if snow:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(250, 252, 255, 230))
            p.drawRoundedRect(QRectF(cx - 24, cy - 11, 48, 4), 2, 2)
    elif kind == "den":
        p.setPen(QPen(QColor("#4A4038"), 1))
        p.setBrush(QColor("#8A7A68"))
        p.drawPolygon(QPolygonF([QPointF(cx - 40, cy), QPointF(cx - 30, cy - 30), QPointF(cx - 6, cy - 44),
                                 QPointF(cx + 24, cy - 34), QPointF(cx + 40, cy - 4)]))
        p.setBrush(QColor("#1A1410"))
        p.drawEllipse(QPointF(cx, cy - 10), 14, 10)
        p.setBrush(QColor("#9A8A78") if not snow else QColor("#F4F6FA"))
        p.drawPolygon(QPolygonF([QPointF(cx - 30, cy - 30), QPointF(cx - 6, cy - 44), QPointF(cx + 24, cy - 34),
                                 QPointF(cx, cy - 26)]))
    elif kind == "marker":
        p.setPen(QPen(QColor("#5A3A22"), 3))
        p.drawLine(QPointF(cx, cy), QPointF(cx, cy - 22))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 210, 90, 160))
        p.drawEllipse(QPointF(cx, cy - 2), 9, 3)
    p.end()
    return pm, QPointF(cx, cy)


# ---- terrain ---------------------------------------------------------------------------------------------------

TERRAIN = {
    # name: {season: (base, speckles)}
    "grass": {"spring": ("#6AAE44", ["#7ABE52", "#5A9E38"]), "summer": ("#8AA848", ["#9AB858", "#7A983C"]),
              "autumn": ("#B8A04A", ["#C8B05A", "#A88E3C"]), "winter": ("#EEF2F8", ["#FFFFFF", "#DCE4F0"])},
    "meadow": {"spring": ("#74B44A", ["#F0E060", "#F070A0", "#FFFFFF", "#84C45A"]),
               "summer": ("#94AE4C", ["#F0D040", "#C060E0", "#A4BE5C"]),
               "autumn": ("#C0A450", ["#D0B460", "#B0944A"]), "winter": ("#F0F4FA", ["#FFFFFF", "#DCE4F0"])},
    "tall": {"spring": ("#5A9E3A", ["#4A8E2E", "#6AAE46"]), "summer": ("#A0A048", ["#B0B058", "#8A8A3A"]),
             "autumn": ("#C8A848", ["#D8B858", "#B0923A"]), "winter": ("#E4EAF2", ["#FFFFFF", "#D0D8E6"])},
    "sage": {"spring": ("#9AA878", ["#8A9868", "#AAB888"]), "summer": ("#B0AA78", ["#A09A68", "#C0BA88"]),
             "autumn": ("#B8A470", ["#A89460", "#C8B480"]), "winter": ("#EAEEF4", ["#FFFFFF", "#D6DEEA"])},
    "forest": {"spring": ("#4A6A34", ["#3A5A28", "#5A7A40"]), "summer": ("#4E6630", ["#3E5626", "#5E763C"]),
               "autumn": ("#6A6030", ["#5A5026", "#7A7040"]), "winter": ("#DCE4EE", ["#F4F8FC", "#C8D2E0"])},
    "dirt": {"spring": ("#9A7A50", ["#8A6A44", "#AA8A5E"]), "summer": ("#A88A5A", ["#987A4C", "#B89A68"]),
             "autumn": ("#9A7A50", ["#8A6A44", "#AA8A5E"]), "winter": ("#D8D4CC", ["#E8E4DC", "#C8C4BC"])},
    "rock": {"spring": ("#7A7670", ["#6A6660", "#8A8680", "#5A5650"]), "summer": ("#7A7670", ["#6A6660", "#8A8680"]),
             "autumn": ("#7A7670", ["#6A6660", "#8A8680"]), "winter": ("#C4C8D0", ["#E8ECF2", "#A8ACB4"])},
    "water": {"spring": ("#3A78B8", ["#4A88C8", "#2E6AA8"]), "summer": ("#3A78B8", ["#4A88C8", "#2E6AA8"]),
              "autumn": ("#38709E", ["#48809E", "#2C6090"]), "winter": ("#B8D8EE", ["#D0E8F8", "#A0C8E4"])},
}


def tile_pixmap(name, season, variant):
    base, specks = TERRAIN[name][season]
    pm = QPixmap(TILE, TILE)
    pm.fill(QColor(base))
    p = QPainter(pm)
    rnd = random.Random(f"{name}{season}{variant}")
    n = {"rock": 30, "water": 18, "tall": 70}.get(name, 45)
    for _ in range(n):
        c = QColor(rnd.choice(specks))
        x, y = rnd.randrange(TILE), rnd.randrange(TILE)
        if name == "tall" and season != "winter":
            p.setPen(QPen(c, 1))
            p.drawLine(x, y, x + rnd.choice((-1, 0, 1)), y - rnd.randint(3, 6))
        elif name == "water":
            p.setPen(QPen(c, 1))
            p.drawLine(x, y, x + rnd.randint(3, 7), y)
        elif name == "rock":
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawRect(x, y, rnd.randint(2, 5), rnd.randint(2, 4))
        else:
            p.setPen(c)
            p.drawPoint(x, y)
            if name == "meadow" and season in ("spring", "summer") and rnd.random() < 0.3:
                p.drawPoint(x + 1, y)
    p.end()
    return pm


def icon_pixmap(size=32):
    """The program icon: a howling wolf's head against a moon."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    p.setPen(QPen(QColor("#20305A"), max(1.0, s)))
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#2A4A8A"))
    g.setColorAt(1, QColor("#10183A"))
    p.setBrush(QBrush(g))
    p.drawRoundedRect(QRectF(1 * s, 1 * s, 30 * s, 30 * s), 5 * s, 5 * s)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#F4E8B0"))
    p.drawEllipse(QPointF(21 * s, 10 * s), 6.5 * s, 6.5 * s)
    p.translate(11 * s, 29 * s)
    p.scale(s * 0.55, s * 0.55)
    draw_wolf(p, "gray", 1.0, "howl", 0.0)
    p.end()
    return pm
