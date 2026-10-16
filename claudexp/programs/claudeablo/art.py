"""Claudeablo's art, painted in code: isometric floor tiles and wall blocks for every theme, the town's houses and
trees, chests, barrels, shrines and portals, heroes, townsfolk, monsters (and Diablo), and inventory icons.

Figures are drawn with their feet on (0, 0) facing down-right ('front') or up-right ('back'); the caller mirrors
for the two left-facing directions.
"""
import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF,
                           QRadialGradient)

TW, TH = 64, 32            # a floor tile's diamond
WALL_H = 56

THEMES = {
    # floor base, floor specks, wall top, wall left, wall right, mortar
    "town": ("#5E8A3A", ["#6E9A44", "#4E7A30", "#7AA64E"], "#7A6A58", "#6A5A48", "#5A4A3A", "#3A2A1A"),
    "cathedral": ("#4A4640", ["#56524A", "#3E3A34", "#5E5A52"], "#6E6A64", "#56524C", "#46423C", "#2A2824"),
    "catacombs": ("#4A3E30", ["#56483A", "#3E3428", "#5E5040"], "#6A5A46", "#54463A", "#44382C", "#2A2018"),
    "caves": ("#4A3A2E", ["#58463A", "#3C2E24", "#62503E"], "#5E4A3A", "#4A3A2C", "#3A2C20", "#20160E"),
    "hell": ("#3A1E1A", ["#4A2620", "#2E1612", "#5A2E24"], "#5A2A22", "#46201A", "#361812", "#1A0806"),
    "abyss": ("#241A2E", ["#2E2238", "#1C1426", "#382A44"], "#3E2E4A", "#30243A", "#24182E", "#100818"),
    "sanctum": ("#1E1414", ["#2A1A1A", "#140C0C", "#321E1E"], "#3A2020", "#2C1818", "#201010", "#0A0404"),
}


def _diamond(w=TW, h=TH, ox=0.0, oy=0.0):
    return QPolygonF([QPointF(ox + w / 2, oy), QPointF(ox + w, oy + h / 2), QPointF(ox + w / 2, oy + h),
                      QPointF(ox, oy + h / 2)])


def floor_tile(theme, variant, lava=False):
    pm = QPixmap(TW, TH)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    path = QPainterPath()
    path.addPolygon(_diamond())
    path.closeSubpath()
    p.setClipPath(path)
    rnd = random.Random(f"{theme}{variant}{lava}")
    if lava:
        g = QLinearGradient(0, 0, TW, TH)
        g.setColorAt(0, QColor("#FF8A20"))
        g.setColorAt(0.5, QColor("#E04010"))
        g.setColorAt(1, QColor("#FFB030"))
        p.fillRect(0, 0, TW, TH, QBrush(g))
        p.setPen(QPen(QColor(255, 230, 120, 180), 1.4))
        for _ in range(4):
            x, y = rnd.uniform(0, TW), rnd.uniform(0, TH)
            p.drawArc(QRectF(x, y, rnd.uniform(6, 14), rnd.uniform(3, 6)), 0, 180 * 16)
        p.end()
        return pm
    base, specks = THEMES[theme][0], THEMES[theme][1]
    p.fillRect(0, 0, TW, TH, QColor(base))
    if theme in ("cathedral", "catacombs", "sanctum", "hell", "abyss"):
        # flagstones
        p.setPen(QPen(QColor(0, 0, 0, 70), 1))
        for i in range(-2, 4):
            p.drawLine(QPointF(i * 16, 0), QPointF(i * 16 + 32, TH))
            p.drawLine(QPointF(i * 16 + 32, 0), QPointF(i * 16, TH))
    for _ in range(60):
        p.setPen(QColor(rnd.choice(specks)))
        p.drawPoint(rnd.randrange(TW), rnd.randrange(TH))
    if theme == "town":
        p.setPen(QColor("#7AA64E"))
        for _ in range(10):
            x, y = rnd.randrange(4, TW - 4), rnd.randrange(4, TH - 2)
            p.drawLine(x, y, x + rnd.choice((-1, 1)), y - 3)
    p.end()
    return pm


def wall_block(theme, style=None, variant=0, height=WALL_H):
    """An isometric wall block; returns (pixmap, anchor = the point that sits on the tile's centre)."""
    w, h = TW, TH + height
    pm = QPixmap(w, h + 10)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    cx, cy = w / 2, h - TH / 2
    rnd = random.Random(f"{theme}{style}{variant}")
    if style == "tree":
        _tree(p, cx, cy, rnd)
        p.end()
        return pm, QPointF(cx, cy)
    if style == "well":
        _well(p, cx, cy)
        p.end()
        return pm, QPointF(cx, cy)
    top, left, right, mortar = THEMES[theme][2:]
    if style == "house":
        top, left, right, mortar = "#8A6A44", "#C8B090", "#A89070", "#5A3A1E"
    elif style == "church":
        top, left, right, mortar = "#7A766E", "#9A968E", "#86827A", "#4A4640"
    hh = height
    left_poly = QPolygonF([QPointF(cx - TW / 2, cy), QPointF(cx, cy + TH / 2), QPointF(cx, cy + TH / 2 - hh),
                           QPointF(cx - TW / 2, cy - hh)])
    right_poly = QPolygonF([QPointF(cx, cy + TH / 2), QPointF(cx + TW / 2, cy), QPointF(cx + TW / 2, cy - hh),
                            QPointF(cx, cy + TH / 2 - hh)])
    top_poly = QPolygonF([QPointF(cx - TW / 2, cy - hh), QPointF(cx, cy + TH / 2 - hh), QPointF(cx + TW / 2, cy - hh),
                          QPointF(cx, cy - TH / 2 - hh)])
    p.setPen(QPen(QColor(mortar), 1))
    p.setBrush(QColor(left))
    p.drawPolygon(left_poly)
    p.setBrush(QColor(right))
    p.drawPolygon(right_poly)
    # bricks / planks / rock
    p.setPen(QPen(QColor(mortar), 1))
    if style == "house":
        for i in range(1, 4):
            p.drawLine(QPointF(cx - TW / 2, cy - hh * i / 4), QPointF(cx, cy + TH / 2 - hh * i / 4))
            p.drawLine(QPointF(cx, cy + TH / 2 - hh * i / 4), QPointF(cx + TW / 2, cy - hh * i / 4))
        p.setPen(QPen(QColor("#4A2E14"), 3))
        p.drawLine(QPointF(cx - TW / 2 + 2, cy - 1), QPointF(cx - TW / 2 + 2, cy - hh))
        p.drawLine(QPointF(cx, cy + TH / 2 - 1), QPointF(cx, cy + TH / 2 - hh))
    elif theme in ("caves",) or style == "rock":
        for _ in range(9):
            x, y = rnd.uniform(cx - 28, cx + 28), rnd.uniform(cy - hh + 4, cy + 4)
            p.setBrush(QColor(left).darker(rnd.randint(105, 135)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(x, y), rnd.uniform(3, 7), rnd.uniform(2, 5))
    else:
        rows = 6
        for i in range(1, rows):
            y = hh * i / rows
            p.drawLine(QPointF(cx - TW / 2, cy - y), QPointF(cx, cy + TH / 2 - y))
            p.drawLine(QPointF(cx, cy + TH / 2 - y), QPointF(cx + TW / 2, cy - y))
            off = 8 if i % 2 else 0
            for k in range(1, 3):
                t = (k * 11 + off) / 32
                p.drawLine(QPointF(cx - TW / 2 + t * 32, cy + t * 16 - y), QPointF(cx - TW / 2 + t * 32,
                                                                                       cy + t * 16 - y + hh / rows))
                p.drawLine(QPointF(cx + t * 32, cy + TH / 2 - t * 16 - y),
                           QPointF(cx + t * 32, cy + TH / 2 - t * 16 - y + hh / rows))
        if theme == "catacombs" and rnd.random() < 0.3:                # a skull niche
            p.setBrush(QColor("#1A140E"))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(cx - 16, cy - hh / 2 + 6), 6, 7)
            p.setBrush(QColor("#E0D8C0"))
            p.drawEllipse(QPointF(cx - 16, cy - hh / 2 + 7), 3.5, 4)
        if theme in ("hell", "sanctum", "abyss") and rnd.random() < 0.5:   # glowing cracks
            p.setPen(QPen(QColor(255, 90, 30, 200) if theme != "abyss" else QColor(190, 90, 255, 200), 1.4))
            x = rnd.uniform(cx - 26, cx + 26)
            pts = [QPointF(x, cy - hh + 6)]
            for i in range(5):
                pts.append(QPointF(pts[-1].x() + rnd.uniform(-5, 5), pts[-1].y() + hh / 6))
            p.drawPolyline(QPolygonF(pts))
        if style == "church" and rnd.random() < 0.6:                    # a gothic window
            p.setBrush(QColor("#30406A"))
            p.setPen(QPen(QColor("#2A2824"), 1))
            p.drawRoundedRect(QRectF(cx - 22, cy - hh + 12, 9, 22), 4, 4)
    p.setPen(QPen(QColor(mortar), 1))
    p.setBrush(QColor(top))
    p.drawPolygon(top_poly)
    if style in ("house", "church"):
        # a solid roof across the whole building: the top face in roof tiles, with shingle rows
        roof = QColor("#8A2E20" if style == "house" else "#44444E")
        p.setPen(QPen(roof.darker(170), 1))
        p.setBrush(roof)
        p.drawPolygon(top_poly)
        p.setPen(QPen(roof.darker(135), 1))
        for i in range(1, 4):
            t = i / 4
            p.drawLine(QPointF(cx - TW / 2 + t * TW / 2, cy - hh - t * TH / 2),
                       QPointF(cx + t * TW / 2, cy - hh + TH / 2 - t * TH / 2))
    p.end()
    return pm, QPointF(cx, cy)


def _tree(p, cx, cy, rnd):
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 60))
    p.drawEllipse(QPointF(cx, cy), 22, 9)
    p.setBrush(QColor("#4A3018"))
    p.drawRect(QRectF(cx - 3, cy - 30, 6, 30))
    for i, (dx, dy, r) in enumerate(((-12, -44, 16), (12, -46, 16), (0, -62, 18), (-5, -52, 14))):
        c = QColor(["#2E5A22", "#3A6A2A", "#467A32", "#365E26"][i]).darker(100 + rnd.randint(0, 25))
        p.setPen(QPen(c.darker(140), 1))
        p.setBrush(c)
        p.drawEllipse(QPointF(cx + dx, cy + dy), r, r * 0.86)


def _well(p, cx, cy):
    p.setPen(QPen(QColor("#3A3A3E"), 1))
    p.setBrush(QColor("#8A8A90"))
    p.drawEllipse(QPointF(cx, cy - 6), 20, 10)
    p.setBrush(QColor("#1A2A4A"))
    p.drawEllipse(QPointF(cx, cy - 8), 14, 6)
    p.setPen(QPen(QColor("#5A3A1E"), 3))
    p.drawLine(QPointF(cx - 16, cy - 6), QPointF(cx - 16, cy - 40))
    p.drawLine(QPointF(cx + 16, cy - 6), QPointF(cx + 16, cy - 40))
    p.setPen(QPen(QColor("#7A2A1E"), 1))
    p.setBrush(QColor("#7A2A1E"))
    p.drawPolygon(QPolygonF([QPointF(cx - 22, cy - 38), QPointF(cx + 22, cy - 38), QPointF(cx, cy - 54)]))


def floor_decor(p, kind, rnd):
    """Something lying on a floor tile; drawn around (0, 0), the tile's centre."""
    if kind == "blood":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(110, 10, 10, 170))
        for _ in range(3):
            p.drawEllipse(QPointF(rnd.uniform(-10, 10), rnd.uniform(-4, 4)), rnd.uniform(4, 9), rnd.uniform(2, 4))
    elif kind in ("bones", "skulls"):
        p.setPen(QPen(QColor("#D8D0B8"), 2, Qt.SolidLine, Qt.RoundCap))
        for _ in range(2):
            x, y = rnd.uniform(-12, 8), rnd.uniform(-5, 3)
            p.drawLine(QPointF(x, y), QPointF(x + rnd.uniform(6, 12), y + rnd.uniform(-3, 3)))
        if kind == "skulls" or rnd.random() < 0.4:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#E0D8C0"))
            p.drawEllipse(QPointF(4, -3), 4, 3.5)
            p.setBrush(QColor("#201810"))
            p.drawEllipse(QPointF(3, -3.5), 1, 1)
            p.drawEllipse(QPointF(5.5, -3.5), 1, 1)
    elif kind == "rug":
        p.setPen(QPen(QColor("#C8A040"), 1))
        p.setBrush(QColor(110, 24, 24, 200))
        p.drawPolygon(_diamond(44, 22, -22, -11))
    elif kind == "cracks":
        p.setPen(QPen(QColor(0, 0, 0, 110), 1))
        p.drawPolyline(QPolygonF([QPointF(-14, 2), QPointF(-6, -2), QPointF(0, 1), QPointF(8, -3), QPointF(14, 0)]))
    elif kind == "rocks":
        p.setPen(Qt.NoPen)
        for _ in range(3):
            p.setBrush(QColor("#5A4A3A").darker(rnd.randint(100, 140)))
            p.drawEllipse(QPointF(rnd.uniform(-12, 12), rnd.uniform(-5, 5)), rnd.uniform(2, 4), rnd.uniform(1.5, 3))
    elif kind == "pentagram":
        pass                        # drawn once over the whole sanctum
    elif kind == "path":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(140, 110, 70, 200))
        p.drawPolygon(_diamond(TW, TH, -TW / 2, -TH / 2))
    elif kind == "flowers":
        p.setPen(Qt.NoPen)
        for _ in range(5):
            p.setBrush(QColor(rnd.choice(["#F0E060", "#F080B0", "#FFFFFF", "#A080F0"])))
            p.drawEllipse(QPointF(rnd.uniform(-14, 14), rnd.uniform(-6, 6)), 1.8, 1.4)
    elif kind == "grasstuft":
        p.setPen(QPen(QColor("#3E6A28"), 1))
        for i in range(6):
            x = rnd.uniform(-8, 8)
            p.drawLine(QPointF(x, 2), QPointF(x + rnd.uniform(-3, 3), -6))
    elif kind == "stone":
        p.setPen(QPen(QColor("#5A5A5E"), 1))
        p.setBrush(QColor("#8A8A90"))
        p.drawEllipse(QPointF(rnd.uniform(-8, 8), 0), 5, 3)


# ---- objects ---------------------------------------------------------------------------------------------------

def draw_object(p, kind, t=0.0, opened=False, colour=None):
    """Chests, barrels, shrines, stairs, portals, the waystone, gold - around (0, 0), the tile centre."""
    if kind == "stairs_down":
        p.setPen(QPen(QColor("#1A1410"), 1))
        p.setBrush(QColor("#0A0806"))
        p.drawPolygon(_diamond(52, 26, -26, -13))
        for i in range(4):
            c = QColor("#6A625A").darker(100 + i * 30)
            p.setBrush(c)
            p.drawPolygon(QPolygonF([QPointF(-18 + i * 5, -2 + i * 3), QPointF(-2 + i * 5, -10 + i * 3),
                                     QPointF(2 + i * 5, -8 + i * 3), QPointF(-14 + i * 5, 0 + i * 3)]))
    elif kind == "stairs_up":
        for i in range(4):
            p.setPen(QPen(QColor("#2A2824"), 1))
            p.setBrush(QColor("#8A8478").darker(100 + (3 - i) * 15))
            p.drawPolygon(QPolygonF([QPointF(-20 + i * 6, 4 - i * 6), QPointF(0 + i * 6, -6 - i * 6),
                                     QPointF(6 + i * 6, -3 - i * 6), QPointF(-14 + i * 6, 7 - i * 6)]))
    elif kind == "chest":
        _box(p, 0, 0, 13, 7, 12, "#9A6A30", "#7A5020", "#6A4418")
        if opened:
            p.setPen(QPen(QColor("#3A2410"), 1))
            p.setBrush(QColor("#1A1008"))
            p.drawPolygon(QPolygonF([QPointF(-13, -12), QPointF(0, -5), QPointF(13, -12), QPointF(0, -19)]))
            p.setBrush(QColor("#9A6A30"))
            p.drawPolygon(QPolygonF([QPointF(-13, -12), QPointF(0, -19), QPointF(0, -32), QPointF(-13, -25)]))
        else:
            p.setPen(QPen(QColor("#E8C040"), 1.5))
            p.drawLine(QPointF(-13, -8), QPointF(0, -1))
            p.drawLine(QPointF(0, -1), QPointF(13, -8))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#F8D040"))
            p.drawRect(QRectF(-2, -6, 4, 4))
    elif kind == "barrel":
        if opened:
            p.setPen(QPen(QColor("#3A2410"), 2))
            for i in range(5):
                a = i * 1.3
                p.drawLine(QPointF(math.cos(a) * 4, math.sin(a) * 2), QPointF(math.cos(a) * 12, math.sin(a) * 6))
            return
        p.setPen(QPen(QColor("#3A2410"), 1))
        p.setBrush(QColor("#7A5230"))
        p.drawRoundedRect(QRectF(-9, -24, 18, 25), 6, 4)
        p.setBrush(QColor("#9A7048"))
        p.drawEllipse(QPointF(0, -23), 9, 4)
        p.setPen(QPen(QColor("#404048"), 1.6))
        p.drawLine(QPointF(-9, -16), QPointF(9, -16))
        p.drawLine(QPointF(-9, -6), QPointF(9, -6))
    elif kind == "shrine":
        _box(p, 0, 0, 14, 7, 14, "#8A8A90", "#6A6A70", "#5A5A60")
        glow = QColor(colour or "#60C0FF")
        if not opened:
            g = QRadialGradient(QPointF(0, -26), 16)
            g.setColorAt(0, QColor(glow.red(), glow.green(), glow.blue(), 200))
            g.setColorAt(1, QColor(glow.red(), glow.green(), glow.blue(), 0))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(0, -26), 16, 16)
            p.setBrush(glow.lighter(130))
            p.drawPolygon(QPolygonF([QPointF(0, -34 + math.sin(t * 3) * 2), QPointF(5, -26), QPointF(0, -18),
                                     QPointF(-5, -26)]))
    elif kind in ("portal", "red_portal"):
        c1, c2 = (("#80C8FF", "#2050C0") if kind == "portal" else ("#FF8080", "#A01010"))
        g = QRadialGradient(QPointF(0, -28), 30)
        g.setColorAt(0, QColor(c1))
        g.setColorAt(0.7, QColor(c2))
        g.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(0, -28), 16, 28)
        p.setPen(QPen(QColor(255, 255, 255, 160), 1.5))
        p.setBrush(Qt.NoBrush)
        for i in range(3):
            r = 4 + ((t * 18 + i * 7) % 14)
            p.drawEllipse(QPointF(0, -28), r * 0.6, r)
    elif kind == "waystone":
        p.setPen(QPen(QColor("#2A2A30"), 1))
        p.setBrush(QColor("#6A6A74"))
        p.drawPolygon(QPolygonF([QPointF(-9, 0), QPointF(-7, -40), QPointF(0, -48), QPointF(7, -40), QPointF(9, 0)]))
        a = 140 + 80 * math.sin(t * 2)
        p.setPen(QPen(QColor(120, 200, 255, int(a)), 2))
        p.drawLine(QPointF(0, -38), QPointF(0, -12))
        p.drawLine(QPointF(-4, -30), QPointF(4, -22))
        p.drawLine(QPointF(4, -30), QPointF(-4, -22))
    elif kind == "gold":
        p.setPen(QPen(QColor("#8A6010"), 1))
        for dx, dy in ((-4, 0), (3, -1), (0, -3), (-1, 2), (4, 2)):
            p.setBrush(QColor("#F8D040"))
            p.drawEllipse(QPointF(dx, dy - 2), 3.5, 2)
    elif kind == "corpse":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(90, 10, 10, 150))
        p.drawEllipse(QPointF(0, 0), 14, 6)


def _box(p, cx, cy, hw, hh, height, top, left, right):
    p.setPen(QPen(QColor(0, 0, 0, 120), 1))
    p.setBrush(QColor(left))
    p.drawPolygon(QPolygonF([QPointF(cx - hw, cy), QPointF(cx, cy + hh), QPointF(cx, cy + hh - height),
                             QPointF(cx - hw, cy - height)]))
    p.setBrush(QColor(right))
    p.drawPolygon(QPolygonF([QPointF(cx, cy + hh), QPointF(cx + hw, cy), QPointF(cx + hw, cy - height),
                             QPointF(cx, cy + hh - height)]))
    p.setBrush(QColor(top))
    p.drawPolygon(QPolygonF([QPointF(cx - hw, cy - height), QPointF(cx, cy + hh - height),
                             QPointF(cx + hw, cy - height), QPointF(cx, cy - hh - height)]))


# ---- people and monsters ------------------------------------------------------------------------------------------

LOOKS = {
    # heroes
    "warrior": dict(skin="#E0B090", body="#8A8A94", trim="#C8A040", legs="#4A4A52", head="helm", weapon="sword",
                    shield=True, cape="#7A1A1A"),
    "rogue": dict(skin="#E8C0A0", body="#3E5A2E", trim="#8A6A3A", legs="#3A2E24", head="hood", weapon="bow",
                  cape="#2E3E22"),
    "sorcerer": dict(skin="#E0B898", body="#2A3A8A", trim="#C8A040", legs="#1E2A60", head="wizard", weapon="staff",
                     robe=True),
    # townsfolk
    "smith": dict(skin="#D8A07A", body="#6A4A30", trim="#3A2A1A", legs="#3A3A40", head="bald", weapon="hammer",
                  apron=True, size=1.08),
    "witch": dict(skin="#E0C0A0", body="#5A2A6A", trim="#C8A040", legs="#3A1A4A", head="witch", robe=True),
    "healer": dict(skin="#E8C8A8", body="#E8E4DA", trim="#3A6AC0", legs="#C8C4BA", head="human", robe=True),
    "elder": dict(skin="#E0C0A0", body="#6A6460", trim="#C8A040", legs="#4A4440", head="beard", robe=True,
                  weapon="cane"),
    # monsters
    "zombie": dict(skin="#7A9A5A", body="#4A5A3A", trim="#3A2A1A", legs="#3A3A2A", head="zombie", hunch=True),
    "ghoul": dict(skin="#9AA88A", body="#3A3A30", trim="#2A2A20", legs="#2A2A20", head="zombie", hunch=True),
    "skeleton": dict(skin="#E8E0C8", body=None, legs=None, head="skull", weapon="sword", bones=True),
    "skeleton_archer": dict(skin="#E8E0C8", body=None, legs=None, head="skull", weapon="bow", bones=True),
    "fallen": dict(skin="#C8402A", body="#8A2A1A", trim="#3A1A10", legs="#6A1A10", head="imp", weapon="spear",
                   size=0.72),
    "goatman": dict(skin="#7A5A3A", body="#5A4028", trim="#3A2A1A", legs="#4A3420", head="goat", weapon="axe",
                    size=1.05),
    "hidden": dict(skin="#8AA0C8", body="#2A3448", trim="#1A2030", legs="#1A2030", head="hood", weapon="dagger",
                   ghost=True),
    "hellwitch": dict(skin="#C890A0", body="#5A1A2A", trim="#E04060", legs="#3A0E1A", head="horned", robe=True,
                      wings=True),
    "knight": dict(skin="#2A2A30", body="#2E2E36", trim="#7A1A1A", legs="#202026", head="greathelm",
                   weapon="sword", shield=True, size=1.1),
    "magma": dict(skin="#6A2A1A", body="#5A2214", trim="#FF7020", legs="#4A1A10", head="horned", hulk=True,
                  size=1.35, glow=True),
    "pitlord": dict(skin="#4A1E30", body="#3A1426", trim="#C83030", legs="#2A0E1A", head="horned", hulk=True,
                    size=1.5, weapon="axe", wings=True),
    "diablo": dict(skin="#B0281A", body="#8A1A10", trim="#F0C040", legs="#6A1208", head="diablo", hulk=True,
                   size=2.0, spikes=True, tail=True, glow=True),
}


def draw_figure(p, look, pose="stand", phase=0.0, back=False, hurt=0.0, equip=None):
    """A person or monster. pose: stand, walk, attack, cast, hit, dead. equip may override weapon/armour colours."""
    spec = dict(LOOKS[look])
    if equip:
        spec.update(equip)
    s = spec.get("size", 1.0)
    p.save()
    p.scale(s, s)
    if pose == "dead":
        _dead(p, spec)
        p.restore()
        return
    if spec.get("ghost"):
        p.setOpacity(0.55)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 80))
    p.drawEllipse(QPointF(0, 0), 14, 5)
    walk = pose == "walk"
    swing = math.sin(phase * 2) * (9 if walk else 0)
    bob = abs(math.sin(phase * 2)) * 1.5 if walk else 0
    hunch = 4 if spec.get("hunch") else 0
    hulk = spec.get("hulk")
    skin, body, trim, legs = (QColor(spec[k]) if spec.get(k) else None for k in ("skin", "body", "trim", "legs"))
    bones = spec.get("bones")
    line = QPen(QColor(20, 14, 10, 200), 1)
    if hurt > 0:
        skin = skin.lighter(150) if skin else skin
    tw = 20 if hulk else 14                       # torso width
    top = -46 - (6 if hulk else 0) + bob          # shoulder height
    hip = -24 + bob

    def leg(dx, ang, far):
        c = (legs or skin).darker(125 if far else 100)
        p.setPen(QPen(c, 6 if hulk else (3 if bones else 5), Qt.SolidLine, Qt.RoundCap))
        foot = QPointF(dx + ang * 0.5, -1)
        p.drawLine(QPointF(dx, hip), foot)
        p.setPen(QPen(c.darker(140), 4 if not bones else 3, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(foot, foot + QPointF(3, 0))

    if spec.get("tail"):
        p.setPen(QPen(skin.darker(120), 4, Qt.SolidLine, Qt.RoundCap))
        path = QPainterPath(QPointF(-6, hip))
        path.cubicTo(QPointF(-22, hip + 6), QPointF(-26, hip - 14 + math.sin(phase) * 4), QPointF(-18, hip - 24))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
    if spec.get("wings"):
        _wings(p, spec, top, phase)
    if spec.get("cape") and not back:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(spec["cape"]).darker(120))
        p.drawPolygon(QPolygonF([QPointF(-tw / 2 - 1, top + 2), QPointF(tw / 2, top + 2), QPointF(tw / 2 - 2, hip + 14),
                                 QPointF(-tw / 2 - 5, hip + 16)]))
    leg(-4, -swing, True)
    leg(4, swing, False)
    # torso
    p.setPen(line)
    if bones:
        p.setPen(QPen(skin, 2.5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(0, top + hunch), QPointF(0, hip))
        for i in range(4):
            y = top + 4 + i * 5
            p.drawLine(QPointF(-6, y), QPointF(6, y))
        p.drawLine(QPointF(-5, hip), QPointF(5, hip))
    else:
        g = QLinearGradient(-tw / 2, 0, tw / 2, 0)
        g.setColorAt(0, body.darker(130))
        g.setColorAt(0.5, body)
        g.setColorAt(1, body.darker(115))
        p.setBrush(QBrush(g))
        robe = spec.get("robe")
        bottom = (-2 if robe else hip + 2)
        torso = QPolygonF([QPointF(-tw / 2 + hunch, top + hunch), QPointF(tw / 2 + hunch, top + hunch),
                           QPointF(tw / 2 - 1 + (4 if robe else 0), bottom), QPointF(-tw / 2 + 1 - (4 if robe else 0),
                                                                                     bottom)])
        p.drawPolygon(torso)
        p.setPen(QPen(trim, 2))
        p.drawLine(QPointF(-tw / 2 + 2, hip - 2), QPointF(tw / 2 - 2, hip - 2))
        if spec.get("apron"):
            p.setPen(line)
            p.setBrush(QColor("#5A3A1E"))
            p.drawRect(QRectF(-tw / 2 + 3, top + 10, tw - 6, hip - top - 4))
        if spec.get("glow"):
            p.setPen(QPen(QColor(255, 140, 40, 210), 1.5))
            p.drawLine(QPointF(-4, top + 6), QPointF(2, top + 14))
            p.drawLine(QPointF(2, top + 14), QPointF(-1, hip - 4))
        if spec.get("spikes"):
            p.setPen(QPen(QColor("#E8D8B0"), 2))
            for i in range(4):
                y = top + 3 + i * 6
                p.drawLine(QPointF(-tw / 2 + 1, y), QPointF(-tw / 2 - 6, y - 4))
    # arms and weapon
    attack = pose == "attack"
    cast = pose == "cast"
    arm_c = skin if bones else (body.darker(110) if body else skin)
    sh_back = QPointF(-tw / 2 + hunch, top + 3 + hunch)
    sh_front = QPointF(tw / 2 + hunch, top + 3 + hunch)
    if cast:
        hand_b, hand_f = sh_back + QPointF(-4, -16), sh_front + QPointF(6, -18)
    elif attack:
        reach = math.sin(min(1.0, phase) * math.pi)
        hand_b = sh_back + QPointF(2, 16)
        hand_f = sh_front + QPointF(6 + 10 * reach, 4 - 14 * (1 - reach))
    else:
        hand_b = sh_back + QPointF(-2 + swing * 0.3, 18)
        hand_f = sh_front + QPointF(2 - swing * 0.3, 18 - (8 if spec.get("hunch") else 0))
        if spec.get("hunch"):
            hand_f = sh_front + QPointF(12, 6)
    w_arm = 6 if hulk else (2.5 if bones else 4.5)
    p.setPen(QPen(arm_c.darker(115), w_arm, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(sh_back, hand_b)
    if spec.get("shield"):
        sc = QColor(spec.get("shield_colour", "#6A4A2A"))
        p.setPen(QPen(QColor(spec.get("trim") or "#C8A040"), 1.5))
        p.setBrush(sc)
        p.drawEllipse(hand_b + QPointF(-1, 0), 7, 9)
    weapon = spec.get("weapon")
    if weapon:
        _weapon(p, weapon, hand_f, attack, spec)
    p.setPen(QPen(arm_c, w_arm, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(sh_front, hand_f)
    p.setPen(Qt.NoPen)
    p.setBrush(skin)
    p.drawEllipse(hand_f, 2.4, 2.4)
    if cast:
        g = QRadialGradient(hand_f + QPointF(0, -4), 12)
        g.setColorAt(0, QColor(255, 220, 120, 220))
        g.setColorAt(1, QColor(255, 120, 40, 0))
        p.setBrush(QBrush(g))
        p.drawEllipse(hand_f + QPointF(0, -4), 12, 12)
    _head(p, spec, QPointF(2 + hunch, top - 8 + hunch), back)
    p.restore()


def _weapon(p, kind, hand, attack, spec):
    colour = QColor(spec.get("weapon_colour", "#C8CCD4"))
    if kind in ("sword", "dagger"):
        n = 22 if kind == "sword" else 11
        tip = hand + (QPointF(n, -n * 0.5) if attack else QPointF(4, -n))
        p.setPen(QPen(colour, 3 if kind == "sword" else 2, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(hand, tip)
        p.setPen(QPen(QColor("#8A6A30"), 2.5))
        p.drawLine(hand + QPointF(-4, 1), hand + QPointF(4, -1))
    elif kind in ("axe", "hammer", "mace"):
        tip = hand + (QPointF(16, -8) if attack else QPointF(2, -18))
        p.setPen(QPen(QColor("#6A4A2A"), 2.5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(hand, tip)
        p.setPen(QPen(QColor(0, 0, 0, 120), 1))
        p.setBrush(colour)
        if kind == "axe":
            p.drawPolygon(QPolygonF([tip, tip + QPointF(7, -5), tip + QPointF(8, 6), tip + QPointF(1, 4)]))
        else:
            p.drawRect(QRectF(tip.x() - 4, tip.y() - 3, 8, 6))
    elif kind == "spear":
        tip = hand + (QPointF(22, -6) if attack else QPointF(2, -26))
        p.setPen(QPen(QColor("#6A4A2A"), 2, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(hand + (QPointF(-8, 3) if attack else QPointF(0, 10)), tip)
        p.setPen(QPen(colour, 3))
        p.drawPoint(tip)
    elif kind == "bow":
        p.setPen(QPen(QColor("#7A5230"), 2.5))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(hand.x() - 4, hand.y() - 16, 12, 32), -80 * 16, 160 * 16)
        p.setPen(QPen(QColor(230, 230, 230, 180), 0.8))
        p.drawLine(hand + QPointF(1, -15), hand + QPointF(1, 15))
    elif kind == "staff":
        p.setPen(QPen(QColor("#6A4A2A"), 3, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(hand + QPointF(-2, 14), hand + QPointF(2, -26))
        g = QRadialGradient(hand + QPointF(2, -28), 6)
        g.setColorAt(0, QColor(spec.get("orb", "#A0E0FF")))
        g.setColorAt(1, QColor(80, 140, 255, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(hand + QPointF(2, -28), 6, 6)
    elif kind == "cane":
        p.setPen(QPen(QColor("#6A4A2A"), 2.5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(hand, hand + QPointF(3, 22))


def _wings(p, spec, top, phase):
    flap = math.sin(phase * 1.5) * 6
    c = QColor(spec.get("skin")).darker(150)
    p.setPen(QPen(c.darker(150), 1))
    p.setBrush(c)
    for sign in (-1, 1):
        p.drawPolygon(QPolygonF([QPointF(0, top + 6), QPointF(sign * 26, top - 14 - flap), QPointF(sign * 30, top + 4),
                                 QPointF(sign * 18, top + 2), QPointF(sign * 20, top + 14)]))


def _head(p, spec, c, back):
    kind = spec.get("head", "human")
    skin = QColor(spec["skin"])
    line = QPen(QColor(20, 14, 10, 200), 1)
    p.setPen(line)
    big = 1.25 if spec.get("hulk") else 1.0
    r = 6.5 * big
    if kind == "skull":
        p.setBrush(skin)
        p.drawEllipse(c, r, r)
        if not back:
            p.setBrush(QColor("#1A1410"))
            p.drawEllipse(c + QPointF(-1, -1), 1.6, 1.8)
            p.drawEllipse(c + QPointF(3, -1), 1.6, 1.8)
            p.drawRect(QRectF(c.x() - 1, c.y() + 3, 4, 2))
        return
    if kind == "hood":
        p.setBrush(QColor(spec["body"]).darker(120))
        p.drawEllipse(c, r + 1.5, r + 1.5)
        if not back:
            p.setBrush(skin.darker(140 if spec.get("ghost") else 110))
            p.drawEllipse(c + QPointF(2, 1), r - 2.5, r - 2)
        return
    p.setBrush(skin)
    p.drawEllipse(c, r, r)
    if kind == "helm":
        p.setBrush(QColor(spec.get("helm_colour", "#9A9AA4")))
        p.drawChord(QRectF(c.x() - r - 1, c.y() - r - 1, 2 * r + 2, 2 * r + 2), 0, 180 * 16)
        p.drawRect(QRectF(c.x() + 1, c.y() - 1, 2, 6)) if not back else None
    elif kind == "greathelm":
        p.setBrush(QColor(spec["body"]))
        p.drawRoundedRect(QRectF(c.x() - r, c.y() - r - 1, 2 * r, 2 * r + 2), 2, 2)
        p.setPen(QPen(QColor(255, 60, 30, 220), 1.4))
        if not back:
            p.drawLine(c + QPointF(-1, -1), c + QPointF(5, -1))
    elif kind == "wizard":
        p.setBrush(QColor(spec["body"]))
        p.drawPolygon(QPolygonF([c + QPointF(-r - 2, -2), c + QPointF(r + 2, -2), c + QPointF(-2, -r - 14)]))
        p.setPen(QPen(QColor(spec["trim"]), 1.5))
        p.drawLine(c + QPointF(-r - 2, -2), c + QPointF(r + 2, -2))
    elif kind == "witch":
        p.setBrush(QColor("#2A1A2E"))
        p.drawPolygon(QPolygonF([c + QPointF(-r - 5, -3), c + QPointF(r + 5, -3), c + QPointF(4, -r - 16)]))
    elif kind == "beard":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#E8E4DC"))
        p.drawPolygon(QPolygonF([c + QPointF(-2, 2), c + QPointF(6, 2), c + QPointF(2, 13)]))
        p.drawChord(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), 30 * 16, 120 * 16)
    elif kind == "bald":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#5A3A20"))
        p.drawPolygon(QPolygonF([c + QPointF(-1, 3), c + QPointF(6, 3), c + QPointF(3, 8)]))
    elif kind == "zombie":
        if not back:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#2A0A0A"))
            p.drawEllipse(c + QPointF(3, 2), 2, 1.4)
    elif kind == "imp":
        p.setBrush(skin.darker(120))
        p.drawPolygon(QPolygonF([c + QPointF(-4, -4), c + QPointF(-7, -12), c + QPointF(-1, -6)]))
        p.drawPolygon(QPolygonF([c + QPointF(3, -5), c + QPointF(6, -13), c + QPointF(6, -4)]))
    elif kind == "goat":
        p.setBrush(skin.darker(110))
        p.drawEllipse(c + QPointF(5, 2), 5, 3.5)
        p.setPen(QPen(QColor("#D8CCB0"), 2.2, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(c.x() - 8, c.y() - 12, 10, 12), 30 * 16, 160 * 16)
    elif kind in ("horned", "diablo"):
        r *= 0.62                                    # horns in proportion to the head
        p.setPen(QPen(QColor("#E8D8B0"), 2.0, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        horn = QPainterPath(c + QPointF(-3, -r + 1))
        horn.cubicTo(c + QPointF(-9, -r - 6), c + QPointF(-10, -r - 12), c + QPointF(-4, -r - 16))
        p.drawPath(horn)
        horn2 = QPainterPath(c + QPointF(3, -r + 1))
        horn2.cubicTo(c + QPointF(9, -r - 6), c + QPointF(10, -r - 12), c + QPointF(5, -r - 16))
        p.drawPath(horn2)
        if kind == "diablo":
            p.setPen(QPen(QColor("#E8D8B0"), 1.6))
            for i in range(3):
                p.drawLine(c + QPointF(-2 + i * 2, -r), c + QPointF(-2 + i * 2, -r - 6))
    if not back and kind not in ("hood", "skull", "greathelm"):
        p.setPen(Qt.NoPen)
        eye = QColor("#FFE040") if kind in ("horned", "diablo", "imp") else QColor("#202020")
        p.setBrush(eye)
        p.drawEllipse(c + QPointF(1.5, -0.5), 1.1 * big, 1.1 * big)
        p.drawEllipse(c + QPointF(4.5, -0.5), 1.1 * big, 1.1 * big)


def _dead(p, spec):
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(80, 10, 10, 150))
    p.drawEllipse(QPointF(2, 1), 16, 6)
    body = QColor(spec.get("body") or spec["skin"])
    p.setBrush(body.darker(120))
    p.setPen(QPen(QColor(0, 0, 0, 140), 1))
    p.drawRoundedRect(QRectF(-12, -6, 22, 8), 3, 3)
    p.setBrush(QColor(spec["skin"]).darker(115))
    p.drawEllipse(QPointF(13, -3), 5, 4.5)


def draw_bat(p, phase, hurt=0.0, colour="#4A3A3A"):
    flap = math.sin(phase * 4) * 9
    y = -30 + math.sin(phase * 1.3) * 4
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 60))
    p.drawEllipse(QPointF(0, 0), 8, 3)
    c = QColor(colour).lighter(150 if hurt else 100)
    p.setPen(QPen(c.darker(150), 1))
    p.setBrush(c)
    for sign in (-1, 1):
        p.drawPolygon(QPolygonF([QPointF(0, y), QPointF(sign * 16, y - 6 - flap), QPointF(sign * 12, y + 2),
                                 QPointF(sign * 6, y + 1)]))
    p.drawEllipse(QPointF(0, y), 4, 4)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#FF3030"))
    p.drawEllipse(QPointF(1.5, y - 1), 0.9, 0.9)


def draw_beast(p, phase, moving, hurt=0.0, colour="#6A4A3A", dead=False):
    """A scavenger: a hunched hyena-ish carrion beast."""
    c = QColor(colour).lighter(150 if hurt else 100)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 70))
    p.drawEllipse(QPointF(0, 0), 16, 5)
    if dead:
        p.setBrush(c.darker(120))
        p.drawEllipse(QPointF(0, -4), 15, 5)
        return
    a = phase * 2
    p.setPen(QPen(c.darker(140), 3.5, Qt.SolidLine, Qt.RoundCap))
    for x, ph in ((-9, 0), (8, math.pi)):
        sw = math.sin(a + ph) * (5 if moving else 0)
        p.drawLine(QPointF(x, -10), QPointF(x + sw, -1))
    p.setPen(QPen(c.darker(160), 1))
    p.setBrush(c)
    p.drawEllipse(QPointF(0, -14), 14, 7)
    p.setBrush(c.darker(120))
    p.drawPolygon(QPolygonF([QPointF(-8, -20), QPointF(4, -24), QPointF(10, -18), QPointF(-6, -16)]))
    p.setBrush(c)
    p.drawEllipse(QPointF(14, -16), 6, 5)
    p.drawPolygon(QPolygonF([QPointF(16, -18), QPointF(24, -14), QPointF(16, -12)]))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#FFD040"))
    p.drawEllipse(QPointF(15, -18), 1, 1)


# ---- inventory icons -----------------------------------------------------------------------------------------------

def item_icon(kind, base="", size=30, rarity="normal"):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 30
    p.scale(s, s)
    steel, wood, gold = QColor("#C8CCD4"), QColor("#7A5230"), QColor("#E8C040")
    if rarity == "rare":
        steel = QColor("#E8DC90")
    elif rarity == "magic":
        steel = QColor("#B0C0F0")
    line = QPen(QColor(0, 0, 0, 160), 1)
    if kind in ("sword", "dagger"):
        n = 24 if kind == "sword" else 15
        p.setPen(QPen(steel, 3.5 if kind == "sword" else 2.5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(8, 22), QPointF(8 + n * 0.7, 22 - n * 0.7))
        p.setPen(QPen(gold, 2.5))
        p.drawLine(QPointF(4, 19), QPointF(11, 26))
        p.setPen(QPen(wood, 3, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(7, 23), QPointF(4, 26))
    elif kind in ("axe", "mace"):
        p.setPen(QPen(wood, 3, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(6, 26), QPointF(20, 8))
        p.setPen(line)
        p.setBrush(steel)
        if kind == "axe":
            p.drawPolygon(QPolygonF([QPointF(17, 6), QPointF(26, 4), QPointF(26, 16), QPointF(20, 13)]))
        else:
            p.drawEllipse(QPointF(21, 7), 5, 5)
            for a in range(0, 360, 60):
                r = math.radians(a)
                p.drawLine(QPointF(21 + math.cos(r) * 5, 7 + math.sin(r) * 5),
                           QPointF(21 + math.cos(r) * 8, 7 + math.sin(r) * 8))
    elif kind == "bow":
        p.setPen(QPen(wood, 3))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(4, 3, 18, 24), -70 * 16, 140 * 16)
        p.setPen(QPen(QColor("#E0E0E0"), 1))
        p.drawLine(QPointF(16, 4), QPointF(16, 26))
    elif kind == "staff":
        p.setPen(QPen(wood, 3, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(8, 27), QPointF(20, 7))
        g = QRadialGradient(QPointF(21, 6), 6)
        g.setColorAt(0, QColor("#E0F4FF"))
        g.setColorAt(1, QColor(60, 120, 255, 40))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(21, 6), 6, 6)
    elif kind == "armor":
        p.setPen(line)
        p.setBrush(steel.darker(115))
        p.drawPolygon(QPolygonF([QPointF(6, 6), QPointF(11, 4), QPointF(15, 7), QPointF(19, 4), QPointF(24, 6),
                                 QPointF(23, 26), QPointF(7, 26)]))
        p.setPen(QPen(QColor(0, 0, 0, 80), 1))
        for y in (12, 17, 22):
            p.drawLine(QPointF(8, y), QPointF(22, y))
    elif kind == "helm":
        p.setPen(line)
        p.setBrush(steel.darker(110))
        p.drawChord(QRectF(5, 6, 20, 22), 0, 180 * 16)
        p.drawRect(QRectF(5, 16, 20, 6))
        p.setBrush(QColor("#202020"))
        p.drawRect(QRectF(10, 17, 10, 2))
    elif kind == "shield":
        p.setPen(QPen(gold, 1.5))
        p.setBrush(QColor("#6A4A2A") if "Buckler" in base or "Small" in base else steel.darker(130))
        p.drawPolygon(QPolygonF([QPointF(6, 5), QPointF(24, 5), QPointF(23, 17), QPointF(15, 27), QPointF(7, 17)]))
        p.setPen(QPen(gold, 2))
        p.drawLine(QPointF(15, 8), QPointF(15, 23))
    elif kind == "ring":
        p.setPen(QPen(gold, 3))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(15, 17), 7, 7)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#E04060") if rarity != "rare" else QColor("#40E0A0"))
        p.drawEllipse(QPointF(15, 9), 3.5, 3.5)
    elif kind == "amulet":
        p.setPen(QPen(gold, 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(6, 2, 18, 18), 200 * 16, 140 * 16)
        p.setPen(line)
        p.setBrush(QColor("#4080E0"))
        p.drawEllipse(QPointF(15, 21), 5, 6)
    elif kind == "potion":
        colour = {"Healing": "#D02020", "Mana": "#2040D0", "Rejuvenation": "#9030C0"}
        c = next((v for k, v in colour.items() if k in base), "#D02020")
        p.setPen(line)
        p.setBrush(QColor(c))
        p.drawEllipse(QPointF(15, 19), 8, 8)
        p.setBrush(QColor("#C8C8D0"))
        p.drawRect(QRectF(12, 6, 6, 7))
        p.setBrush(QColor("#7A5230"))
        p.drawRect(QRectF(12, 4, 6, 3))
        if "Full" in base:
            p.setPen(QPen(QColor(255, 255, 255, 150), 1.5))
            p.drawArc(QRectF(9, 13, 8, 8), 90 * 16, 90 * 16)
    elif kind == "scroll":
        p.setPen(line)
        p.setBrush(QColor("#E8DCB0"))
        p.drawRect(QRectF(7, 7, 16, 16))
        p.setBrush(QColor("#C8B888"))
        p.drawEllipse(QPointF(7, 15), 3, 8)
        p.drawEllipse(QPointF(23, 15), 3, 8)
        p.setPen(QPen(QColor("#2050C0") if "Portal" in base else QColor("#802020"), 1))
        for y in (11, 15, 19):
            p.drawLine(QPointF(10, y), QPointF(20, y))
    elif kind == "book":
        c = QColor("#A02020") if "Fire" in base or "Inferno" in base else QColor("#2050A0") if "Light" in base or \
            "Nova" in base else QColor("#208040") if "Heal" in base else QColor("#6A3A8A")
        p.setPen(line)
        p.setBrush(c)
        p.drawRect(QRectF(7, 5, 16, 21))
        p.setPen(QPen(gold, 1.5))
        p.drawRect(QRectF(9, 7, 12, 17))
    elif kind == "gold":
        p.setPen(QPen(QColor("#8A6010"), 1))
        p.setBrush(gold)
        for dx, dy in ((-4, 4), (3, 3), (0, -1), (-2, 8), (5, 8)):
            p.drawEllipse(QPointF(15 + dx, 15 + dy), 5, 3)
    p.end()
    return pm


def icon_pixmap(size=32):
    """The program icon: Diablo's horned head in flames."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#3A0A06"))
    g.setColorAt(1, QColor("#100202"))
    p.setPen(QPen(QColor("#6A1A10"), max(1.0, s)))
    p.setBrush(QBrush(g))
    p.drawRoundedRect(QRectF(1 * s, 1 * s, 30 * s, 30 * s), 4 * s, 4 * s)
    fl = QRadialGradient(QPointF(16 * s, 26 * s), 16 * s)
    fl.setColorAt(0, QColor(255, 160, 40, 220))
    fl.setColorAt(1, QColor(255, 60, 20, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(fl))
    p.drawEllipse(QPointF(16 * s, 26 * s), 16 * s, 12 * s)
    p.setPen(QPen(QColor("#E8D8B0"), 2.2 * s, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(4 * s, 3 * s, 12 * s, 16 * s), 90 * 16, 120 * 16)
    p.drawArc(QRectF(16 * s, 3 * s, 12 * s, 16 * s), -30 * 16, 120 * 16)
    p.setPen(QPen(QColor("#4A0A06"), s))
    p.setBrush(QColor("#B0281A"))
    p.drawEllipse(QPointF(16 * s, 17 * s), 8 * s, 9 * s)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#FFE040"))
    p.drawEllipse(QPointF(13 * s, 15 * s), 1.6 * s, 1.2 * s)
    p.drawEllipse(QPointF(19 * s, 15 * s), 1.6 * s, 1.2 * s)
    p.setBrush(QColor("#2A0604"))
    p.drawRect(QRectF(12 * s, 20 * s, 8 * s, 2 * s))
    p.end()
    return pm


def icon():
    ic = QIcon()
    for sz in (16, 32, 48):
        ic.addPixmap(icon_pixmap(sz))
    return ic
