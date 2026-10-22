"""Claudeout 4's textures and sprites, all painted in code into one atlas: the vault's steel panels, grating, cryo
pods, terminals and the big gear door; the surface's dead grass, cracked road, clapboard houses, rusted cars and
bare trees; and the sprites for radroaches, bloatflies, mole rats, the robot, the skeleton and the things you pick up.

The atlas is 16 x 16 tiles of 64 pixels; a few sprites (the tree, the robot) take 2 x 2 tiles for the detail."""
import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF, QRadialGradient

TILE = 64
COLS = 16                                      # the atlas is 16 x 16 tiles
# name, or (name, tiles wide, tiles high)
NAMES = [
    # the vault
    "wall", "wall_base", "wall_top", "floor", "grate", "ceiling", "light", "door", "pod_front", "pod_side",
    "desk_top", "desk_side", "screen", "locker", "table", "counter", "bed", "gear", "panel", "metal", "vent",
    "pod_open", "glass", "sign", "wall_111", "elevator", "pipe", "crate", "poster",
    # the surface
    "grass", "dirt", "road", "pavement", "concrete", "water", "rock", "house_blue", "house_yellow", "house_white",
    "house_window", "house_floor", "roof", "fence", "railing", "car", "car_top", "rubble", "mailbox", "workbench",
    "bridge", "couch", "fridge", "crib", "tv", "sign_welcome", "sign_vault",
    # sprites
    "roach", "roach_dead", "skeleton", "baton", "pistol", "stimpak", "pipboy", "ammo", "spouse",
    ("tree", 2, 2), "bush", "bloatfly", "bloatfly_dead", "molerat", "molerat_dead", ("robot", 2, 2),
    "meat", "meat_fly", "meat_rat", "cola", "radaway", "marker",
]
STEEL = "#5A6670"
STEEL_DARK = "#3C454D"
STEEL_LIGHT = "#7B8893"
YELLOW = "#E2B13C"
GREEN = "#36E07A"


def _pack():
    """Where each tile goes: first fit, row by row, the big ones taking several cells."""
    taken = set()
    out = {}
    for entry in NAMES:
        name, w, h = (entry, 1, 1) if isinstance(entry, str) else entry
        for row in range(COLS):
            for col in range(COLS):
                cells = [(col + i, row + j) for i in range(w) for j in range(h)]
                if col + w <= COLS and row + h <= COLS and not any(c in taken for c in cells):
                    taken.update(cells)
                    out[name] = (col, row, w, h)
                    break
            if name in out:
                break
    return out


INDEX = _pack()


def uv(name):
    """(u0, v0, u1, v1) of a tile in the atlas (a hair inside its edges, so nothing bleeds from the next tile)."""
    col, row, w, h = INDEX[name]
    e = 0.4 / (TILE * COLS)
    return col / COLS + e, row / COLS + e, (col + w) / COLS - e, (row + h) / COLS - e


def _rivets(p, r, inset=5):
    p.setPen(Qt.NoPen)
    for x, y in ((r.left() + inset, r.top() + inset), (r.right() - inset, r.top() + inset),
                 (r.left() + inset, r.bottom() - inset), (r.right() - inset, r.bottom() - inset)):
        p.setBrush(QColor("#2A3137"))
        p.drawEllipse(QPointF(x + 0.6, y + 0.6), 2.2, 2.2)
        p.setBrush(QColor("#9AA7B2"))
        p.drawEllipse(QPointF(x, y), 2.0, 2.0)
        p.setBrush(QColor("#CFD8E0"))
        p.drawEllipse(QPointF(x - 0.6, y - 0.6), 0.8, 0.8)


def _panel(p, r, base=STEEL, seams=True):
    g = QLinearGradient(r.topLeft(), r.bottomRight())
    c = QColor(base)
    g.setColorAt(0, c.lighter(112))
    g.setColorAt(1, c.darker(115))
    p.fillRect(r, g)
    if seams:
        p.setPen(QPen(QColor(STEEL_DARK), 2))
        p.drawRect(r.adjusted(1, 1, -1, -1))
        p.setPen(QPen(QColor(STEEL_LIGHT), 1))
        p.drawLine(QPointF(r.left() + 3, r.top() + 3), QPointF(r.right() - 3, r.top() + 3))


def _noise(p, r, rng, n=60, alpha=28):
    p.setPen(Qt.NoPen)
    for _ in range(n):
        x, y = rng.uniform(r.left(), r.right()), rng.uniform(r.top(), r.bottom())
        p.setBrush(QColor(0, 0, 0, alpha) if rng.random() < 0.6 else QColor(255, 255, 255, alpha // 2))
        p.drawRect(QRectF(x, y, rng.uniform(1, 4), rng.uniform(1, 2)))


def _text(p, r, s, size, colour, family="Consolas", align=Qt.AlignCenter, bold=True):
    f = QFont(family)
    f.setPixelSize(size)
    f.setBold(bold)
    p.setFont(f)
    p.setPen(QColor(colour))
    p.drawText(r, align, s)


def _cracks(p, rng, r, n=3, colour="#1E1E1E", width=1.5):
    p.setPen(QPen(QColor(colour), width))
    for _ in range(n):
        x, y = rng.uniform(r.left(), r.right()), rng.uniform(r.top(), r.bottom())
        for _k in range(rng.randint(3, 6)):
            nx, ny = x + rng.uniform(-14, 14), y + rng.uniform(-14, 14)
            p.drawLine(QPointF(x, y), QPointF(nx, ny))
            x, y = nx, ny


def _siding(p, r, rng, colour):
    """Clapboard siding, the paint peeling."""
    base = QColor(colour)
    p.fillRect(r, base)
    p.setPen(QPen(base.darker(135), 1.5))
    for y in range(6, TILE, 8):
        p.drawLine(QPointF(0, y), QPointF(TILE, y))
        p.setPen(QPen(base.lighter(115), 1))
        p.drawLine(QPointF(0, y + 1), QPointF(TILE, y + 1))
        p.setPen(QPen(base.darker(135), 1.5))
    p.setPen(Qt.NoPen)
    for _ in range(9):                                   # bare wood showing through
        x, y = rng.uniform(0, TILE), rng.uniform(0, TILE)
        p.setBrush(QColor("#8A7A5A"))
        p.drawRoundedRect(QRectF(x, y, rng.uniform(4, 14), rng.uniform(2, 5)), 2, 2)
    _noise(p, r, rng, 50, 36)


def _tile(name, rng, w=1, h=1):
    W, H = TILE * w, TILE * h
    img = QImage(W, H, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    r = QRectF(0, 0, W, H)
    # ---- the vault ----
    if name == "wall":
        _panel(p, r)
        _rivets(p, r)
        _noise(p, r, rng)
    elif name == "wall_base":
        _panel(p, r)
        p.setPen(Qt.NoPen)
        p.fillRect(QRectF(0, 44, TILE, 20), QColor(YELLOW))
        p.setBrush(QColor("#1E1E1E"))
        for x in range(-20, TILE + 20, 16):
            p.drawPolygon(QPolygonF([QPointF(x, 64), QPointF(x + 8, 64), QPointF(x + 20, 44), QPointF(x + 12, 44)]))
        p.setPen(QPen(QColor(STEEL_DARK), 2))
        p.drawLine(QPointF(0, 44), QPointF(TILE, 44))
        _rivets(p, QRectF(0, 0, TILE, 44))
        _noise(p, r, rng)
    elif name == "wall_top":
        _panel(p, r)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2A3137"))
        p.drawRoundedRect(QRectF(12, 18, 40, 28), 3, 3)
        p.setPen(QPen(QColor(STEEL_LIGHT), 2))
        for y in range(22, 46, 5):
            p.drawLine(QPointF(15, y), QPointF(49, y))
        _rivets(p, r)
    elif name == "wall_111":
        _panel(p, r)
        _rivets(p, r)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(YELLOW))
        p.drawRoundedRect(QRectF(8, 14, 48, 36), 4, 4)
        _text(p, QRectF(8, 14, 48, 36), "111", 26, "#1E1E1E", "Arial Black")
    elif name == "floor":
        p.fillRect(r, QColor("#3A3F45"))
        p.setPen(QPen(QColor("#2A2E33"), 2))
        for k in (0, 32):
            p.drawLine(QPointF(k, 0), QPointF(k, TILE))
            p.drawLine(QPointF(0, k), QPointF(TILE, k))
        p.setPen(QPen(QColor("#4A5057"), 1))
        for k in (1, 33):
            p.drawLine(QPointF(k, 0), QPointF(k, TILE))
            p.drawLine(QPointF(0, k), QPointF(TILE, k))
        _noise(p, r, rng, 90)
    elif name == "grate":
        p.fillRect(r, QColor("#23272B"))
        p.setPen(QPen(QColor("#6A737C"), 3))
        for k in range(4, TILE, 8):
            p.drawLine(QPointF(k, 0), QPointF(k, TILE))
        p.setPen(QPen(QColor("#4A525A"), 3))
        for k in range(4, TILE, 16):
            p.drawLine(QPointF(0, k), QPointF(TILE, k))
        p.setPen(QPen(QColor("#8A939C"), 2))
        p.drawRect(r.adjusted(1, 1, -1, -1))
    elif name == "ceiling":
        _panel(p, r, "#3E474E")
        _rivets(p, r, 6)
        p.setPen(QPen(QColor("#2A3137"), 1))
        p.drawLine(QPointF(0, 32), QPointF(TILE, 32))
    elif name == "light":
        _panel(p, r, "#3E474E")
        g = QLinearGradient(0, 0, 0, TILE)
        g.setColorAt(0, QColor("#FFFDE8"))
        g.setColorAt(0.5, QColor("#FFF6C0"))
        g.setColorAt(1, QColor("#FFFDE8"))
        p.setPen(QPen(QColor("#1E2226"), 2))
        p.setBrush(g)
        p.drawRoundedRect(QRectF(6, 20, 52, 24), 4, 4)
    elif name == "door":
        _panel(p, r, "#4C6A8A")
        p.setPen(QPen(QColor("#22303C"), 3))
        p.drawLine(QPointF(0, 32), QPointF(TILE, 32))
        p.setBrush(QColor("#1A2A36"))
        p.drawRoundedRect(QRectF(20, 8, 24, 16), 3, 3)
        p.setBrush(QColor(YELLOW))
        p.setPen(Qt.NoPen)
        p.drawRect(QRectF(0, 44, TILE, 6))
        _rivets(p, r)
    elif name == "pod_front":
        _panel(p, r, "#6A7682")
        glass = QRectF(14, 6, 36, 52)
        g = QLinearGradient(glass.topLeft(), glass.bottomRight())
        g.setColorAt(0, QColor("#CFE8F5"))
        g.setColorAt(0.5, QColor("#8FB8D0"))
        g.setColorAt(1, QColor("#5A7F96"))
        p.setPen(QPen(QColor("#2A3137"), 3))
        p.setBrush(g)
        p.drawRoundedRect(glass, 14, 14)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 110))
        for _ in range(26):                             # frost
            x, y = rng.uniform(16, 48), rng.uniform(8, 56)
            p.drawEllipse(QPointF(x, y), rng.uniform(1, 3), rng.uniform(1, 3))
        p.setBrush(QColor(40, 50, 60, 120))             # a dim shape inside
        p.drawEllipse(QPointF(32, 20), 7, 8)
        p.drawRoundedRect(QRectF(24, 28, 16, 26), 6, 6)
        p.setBrush(QColor("#E04040"))
        p.drawEllipse(QPointF(10, 10), 2.5, 2.5)
    elif name == "pod_open":
        _panel(p, r, "#6A7682")
        p.setPen(QPen(QColor("#2A3137"), 3))
        p.setBrush(QColor("#141A20"))
        p.drawRoundedRect(QRectF(14, 6, 36, 52), 14, 14)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2A3A48"))
        p.drawRoundedRect(QRectF(22, 12, 20, 40), 8, 8)
        p.setBrush(QColor(GREEN))
        p.drawEllipse(QPointF(10, 10), 2.5, 2.5)
    elif name == "pod_side":
        _panel(p, r, "#6A7682")
        p.setPen(QPen(QColor("#2A3137"), 2))
        for y in (16, 32, 48):
            p.drawLine(QPointF(4, y), QPointF(60, y))
        _rivets(p, r)
    elif name == "glass":
        p.fillRect(r, QColor(150, 200, 230, 90))
        p.setPen(QPen(QColor(220, 240, 255, 140), 2))
        p.drawLine(QPointF(8, 56), QPointF(56, 8))
    elif name == "desk_top":
        p.fillRect(r, QColor("#6E6358"))
        p.setPen(QPen(QColor("#4A423A"), 2))
        p.drawRect(r.adjusted(1, 1, -1, -1))
        _noise(p, r, rng, 50)
    elif name == "desk_side":
        _panel(p, r, "#5A5047", False)
        p.setPen(QPen(QColor("#3A332C"), 2))
        p.drawRect(QRectF(6, 10, 22, 44))
        p.drawRect(QRectF(36, 10, 22, 44))
        p.setBrush(QColor("#9A8E80"))
        p.setPen(Qt.NoPen)
        p.drawRect(QRectF(13, 30, 8, 3))
        p.drawRect(QRectF(43, 30, 8, 3))
    elif name == "screen":
        _panel(p, r, "#5A5F64")
        scr = QRectF(6, 6, 52, 44)
        p.setPen(QPen(QColor("#1A1E22"), 3))
        p.setBrush(QColor("#0A1A10"))
        p.drawRoundedRect(scr, 4, 4)
        _text(p, QRectF(10, 8, 44, 12), "VAULT-TEC", 9, GREEN, align=Qt.AlignLeft | Qt.AlignVCenter)
        p.setPen(QPen(QColor(GREEN), 2))
        for k, w_ in enumerate((30, 40, 22, 36, 18)):
            p.drawLine(QPointF(10, 24 + k * 5), QPointF(10 + w_, 24 + k * 5))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#3A4046"))
        p.drawRoundedRect(QRectF(10, 54, 44, 7), 2, 2)
    elif name == "locker":
        _panel(p, r, "#6A7378")
        p.setPen(QPen(QColor("#2A3137"), 2))
        p.drawLine(QPointF(32, 0), QPointF(32, TILE))
        for x in (8, 40):
            p.setBrush(QColor("#2A3137"))
            p.drawRoundedRect(QRectF(x, 8, 16, 10), 2, 2)
            p.setBrush(QColor("#9AA7B2"))
            p.drawRect(QRectF(x + 18, 30, 3, 8))
    elif name == "table":
        p.fillRect(r, QColor("#D9CDB0"))
        p.setPen(QPen(QColor("#9A8E70"), 2))
        p.drawRect(r.adjusted(1, 1, -1, -1))
        p.setPen(QPen(QColor("#C4B890"), 1))
        for k in range(8, TILE, 12):
            p.drawLine(QPointF(k, 2), QPointF(k, 62))
    elif name == "counter":
        _panel(p, r, "#7A858E")
        p.setPen(QPen(QColor("#2A3137"), 2))
        p.drawLine(QPointF(0, 12), QPointF(TILE, 12))
        _rivets(p, QRectF(0, 12, TILE, 52))
    elif name == "bed":
        p.fillRect(r, QColor("#D8DCE0"))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#5A6F9A"))
        p.drawRect(QRectF(0, 26, TILE, 38))
        p.setBrush(QColor("#F4F4F0"))
        p.drawRoundedRect(QRectF(14, 6, 36, 14), 5, 5)
        p.setPen(QPen(QColor("#4A5F8A"), 1))
        p.drawLine(QPointF(0, 40), QPointF(TILE, 40))
    elif name == "gear":
        p.fillRect(r, QColor("#2E3338"))
        c = QPointF(32, 32)
        path = QPainterPath()
        teeth = 14
        for k in range(teeth * 2):
            a = k * math.pi / teeth
            rad = 31 if k % 2 == 0 else 25
            pt = QPointF(c.x() + math.cos(a) * rad, c.y() + math.sin(a) * rad)
            path.moveTo(pt) if k == 0 else path.lineTo(pt)
        path.closeSubpath()
        g = QRadialGradient(c, 32)
        g.setColorAt(0, QColor("#8A949C"))
        g.setColorAt(1, QColor("#4A535A"))
        p.setPen(QPen(QColor("#1A1E22"), 2))
        p.setBrush(g)
        p.drawPath(path)
        p.setBrush(QColor("#3A4248"))
        p.drawEllipse(c, 16, 16)
        p.setBrush(QColor(YELLOW))
        p.drawEllipse(c, 12, 12)
        _text(p, QRectF(16, 16, 32, 32), "111", 12, "#1E1E1E", "Arial Black")
        for k in range(8):
            a = k * math.pi / 4
            p.setBrush(QColor("#2A3137"))
            p.drawEllipse(QPointF(c.x() + math.cos(a) * 20, c.y() + math.sin(a) * 20), 2, 2)
    elif name == "panel":
        _panel(p, r, "#5A5F64")
        p.setPen(QPen(QColor("#1A1E22"), 2))
        p.setBrush(QColor("#0A1A10"))
        p.drawRoundedRect(QRectF(8, 8, 48, 22), 3, 3)
        _text(p, QRectF(8, 8, 48, 22), "DOOR CTRL", 9, GREEN)
        p.setBrush(QColor("#C02020"))
        p.drawEllipse(QPointF(20, 46), 8, 8)
        p.setBrush(QColor("#FF6A5A"))
        p.drawEllipse(QPointF(18, 44), 3, 3)
        p.setBrush(QColor("#3A4046"))
        p.drawRoundedRect(QRectF(34, 38, 22, 16), 2, 2)
        p.setBrush(QColor("#7A8A94"))
        p.drawRect(QRectF(38, 42, 14, 8))
    elif name == "metal":
        _panel(p, r, "#464E55", False)
        p.setPen(QPen(QColor("#2A3137"), 1))
        p.drawRect(r.adjusted(1, 1, -1, -1))
        _noise(p, r, rng, 40)
    elif name == "elevator":
        _panel(p, r, "#4A525A", False)
        p.setPen(QPen(QColor(YELLOW), 4))
        p.drawRect(r.adjusted(3, 3, -3, -3))
        p.setPen(QPen(QColor("#2A3137"), 2))
        for k in (16, 32, 48):
            p.drawLine(QPointF(k, 8), QPointF(k, 56))
    elif name == "vent":
        _panel(p, r)
        p.setPen(QPen(QColor("#1A1E22"), 2))
        p.setBrush(QColor("#101316"))
        p.drawRoundedRect(QRectF(8, 14, 48, 36), 3, 3)
        p.setPen(QPen(QColor("#6A737C"), 3))
        for y in range(19, 50, 6):
            p.drawLine(QPointF(11, y), QPointF(53, y))
    elif name == "pipe":
        _panel(p, r)
        for y, col in ((14, "#8A5A3A"), (38, "#5A6A7A")):
            g = QLinearGradient(0, y, 0, y + 14)
            g.setColorAt(0, QColor(col).lighter(140))
            g.setColorAt(0.5, QColor(col))
            g.setColorAt(1, QColor(col).darker(150))
            p.setPen(Qt.NoPen)
            p.setBrush(g)
            p.drawRect(QRectF(0, y, TILE, 14))
            p.setBrush(QColor(col).darker(130))
            p.drawRect(QRectF(20, y - 2, 6, 18))
            p.drawRect(QRectF(44, y - 2, 6, 18))
    elif name == "crate":
        p.fillRect(r, QColor("#4C6A8A"))
        p.setPen(QPen(QColor("#22303C"), 3))
        p.drawRect(r.adjusted(2, 2, -2, -2))
        p.drawLine(QPointF(2, 2), QPointF(62, 62))
        p.drawLine(QPointF(62, 2), QPointF(2, 62))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(YELLOW))
        p.drawRect(QRectF(22, 26, 20, 12))
    elif name == "sign":
        _panel(p, r)
        p.setPen(QPen(QColor("#1A1E22"), 2))
        p.setBrush(QColor("#1E5A8A"))
        p.drawRoundedRect(QRectF(4, 16, 56, 32), 3, 3)
        _text(p, QRectF(4, 16, 56, 16), "VAULT 111", 10, "#FFFFFF")
        _text(p, QRectF(4, 30, 56, 16), "→ EXIT", 10, YELLOW)
    elif name == "poster":
        _panel(p, r)
        p.setPen(QPen(QColor("#1A1E22"), 2))
        p.setBrush(QColor("#F0E6C8"))
        p.drawRect(QRectF(10, 6, 44, 52))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1E5A8A"))
        p.drawRect(QRectF(10, 6, 44, 14))
        _text(p, QRectF(10, 6, 44, 14), "VAULT-TEC", 8, "#FFFFFF")
        p.setBrush(QColor(YELLOW))
        p.drawEllipse(QPointF(32, 36), 11, 11)
        p.setBrush(QColor("#1E1E1E"))
        p.drawEllipse(QPointF(28, 33), 1.6, 1.6)
        p.drawEllipse(QPointF(36, 33), 1.6, 1.6)
        p.setPen(QPen(QColor("#1E1E1E"), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(26, 34, 12, 8), 200 * 16, 140 * 16)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1E5A8A"))
        p.drawRect(QRectF(22, 48, 20, 4))
    # ---- the surface ----
    elif name == "grass":
        p.fillRect(r, QColor("#7A7446"))
        p.setPen(Qt.NoPen)
        for _ in range(70):                              # dead tufts
            x, y = rng.uniform(0, TILE), rng.uniform(0, TILE)
            p.setBrush(QColor(rng.choice(("#8C8450", "#6A6438", "#9A8E58", "#5E5A34"))))
            p.drawRoundedRect(QRectF(x, y, rng.uniform(2, 6), rng.uniform(1.5, 3)), 1, 1)
        p.setPen(QPen(QColor("#5A5430"), 1))
        for _ in range(30):
            x, y = rng.uniform(0, TILE), rng.uniform(0, TILE)
            p.drawLine(QPointF(x, y), QPointF(x + rng.uniform(-3, 3), y - rng.uniform(3, 7)))
    elif name == "dirt":
        p.fillRect(r, QColor("#6E5A42"))
        p.setPen(Qt.NoPen)
        for _ in range(40):
            x, y = rng.uniform(0, TILE), rng.uniform(0, TILE)
            p.setBrush(QColor(rng.choice(("#7E6A50", "#5E4C36", "#8A7A62"))))
            p.drawEllipse(QPointF(x, y), rng.uniform(1.5, 4), rng.uniform(1, 2.5))
        _noise(p, r, rng, 60)
    elif name == "road":
        p.fillRect(r, QColor("#3A3A3C"))
        _noise(p, r, rng, 120, 22)
        _cracks(p, rng, r, 3, "#242426", 1.5)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#4A4A4C"))
        for _ in range(6):
            p.drawEllipse(QPointF(rng.uniform(0, TILE), rng.uniform(0, TILE)), rng.uniform(2, 5), rng.uniform(1, 3))
    elif name in ("pavement", "concrete"):
        p.fillRect(r, QColor("#8A8A82" if name == "pavement" else "#7A7A74"))
        _noise(p, r, rng, 90, 20)
        _cracks(p, rng, r, 2, "#5A5A54", 1.2)
        p.setPen(QPen(QColor("#6A6A64"), 2))
        if name == "pavement":
            p.drawLine(QPointF(0, 32), QPointF(TILE, 32))
    elif name == "water":
        g = QLinearGradient(0, 0, TILE, TILE)
        g.setColorAt(0, QColor("#3E5A48"))
        g.setColorAt(1, QColor("#2A4234"))
        p.fillRect(r, g)
        p.setPen(QPen(QColor(120, 160, 130, 90), 1.5))
        for k in range(6):
            y = 6 + k * 10
            path = QPainterPath(QPointF(0, y))
            for x in range(8, TILE + 8, 8):
                path.quadTo(QPointF(x - 4, y + (3 if (x // 8) % 2 else -3)), QPointF(x, y))
            p.drawPath(path)
    elif name == "rock":
        p.fillRect(r, QColor("#5E5A52"))
        p.setPen(Qt.NoPen)
        for _ in range(14):
            x, y = rng.uniform(-6, TILE), rng.uniform(-6, TILE)
            c = QColor(rng.choice(("#6E6A60", "#4E4A42", "#7A766C", "#57534B")))
            p.setBrush(c)
            p.drawPolygon(QPolygonF([QPointF(x, y), QPointF(x + rng.uniform(8, 20), y + rng.uniform(-4, 4)),
                                     QPointF(x + rng.uniform(6, 18), y + rng.uniform(8, 18)),
                                     QPointF(x + rng.uniform(-2, 4), y + rng.uniform(6, 14))]))
        _cracks(p, rng, r, 2, "#3A3630", 1.2)
    elif name == "house_blue":
        _siding(p, r, rng, "#6A8AA8")
    elif name == "house_yellow":
        _siding(p, r, rng, "#C8B068")
    elif name == "house_white":
        _siding(p, r, rng, "#CFCABC")
    elif name == "house_window":
        _siding(p, r, rng, "#A0A49A")
        p.setPen(QPen(QColor("#2A2A2A"), 3))
        p.setBrush(QColor("#1A2024"))
        p.drawRect(QRectF(14, 12, 36, 34))
        p.setPen(QPen(QColor("#4A4A4A"), 2))
        p.drawLine(QPointF(32, 12), QPointF(32, 46))
        p.drawLine(QPointF(14, 29), QPointF(50, 29))
        p.setPen(QPen(QColor(200, 220, 230, 120), 1.5))  # broken glass
        p.drawLine(QPointF(18, 16), QPointF(30, 26))
        p.drawLine(QPointF(44, 40), QPointF(36, 32))
    elif name == "house_floor":
        p.fillRect(r, QColor("#7A6448"))
        p.setPen(QPen(QColor("#5A4834"), 2))
        for y in range(0, TILE, 11):
            p.drawLine(QPointF(0, y), QPointF(TILE, y))
        p.setPen(QPen(QColor("#4A3A28"), 1.5))
        for k in range(6):
            x = rng.uniform(0, TILE)
            y = (k * 11) + 2
            p.drawLine(QPointF(x, y), QPointF(x, y + 8))
        _noise(p, r, rng, 80, 30)
    elif name == "roof":
        p.fillRect(r, QColor("#4A4440"))
        p.setPen(QPen(QColor("#2E2A28"), 1.5))
        for y in range(0, TILE, 8):
            p.drawLine(QPointF(0, y), QPointF(TILE, y))
            off = 8 if (y // 8) % 2 else 0
            for x in range(off, TILE, 16):
                p.drawLine(QPointF(x, y), QPointF(x, y + 8))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#6A6058"))
        for _ in range(5):
            p.drawRect(QRectF(rng.uniform(0, 56), rng.uniform(0, 56) // 8 * 8, 8, 8))
    elif name == "fence":                                # pickets with gaps (transparent) between
        p.setPen(QPen(QColor("#8A8478"), 1))
        p.setBrush(QColor("#D8D2C4"))
        for x in (4, 24, 44):
            p.drawPolygon(QPolygonF([QPointF(x, 10), QPointF(x + 8, 2), QPointF(x + 16, 10), QPointF(x + 16, 64),
                                     QPointF(x, 64)]))
        p.setBrush(QColor("#C4BEB0"))
        p.drawRect(QRectF(0, 20, TILE, 6))
        p.drawRect(QRectF(0, 46, TILE, 6))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#8A7A5A"))
        for _ in range(6):
            p.drawRect(QRectF(rng.uniform(0, 60), rng.uniform(10, 60), 4, 3))
    elif name == "railing":
        p.setPen(QPen(QColor("#3A2E26"), 1))
        p.setBrush(QColor("#7A5A3A"))
        p.drawRect(QRectF(0, 8, TILE, 6))
        p.drawRect(QRectF(0, 34, TILE, 6))
        p.drawRect(QRectF(6, 0, 7, TILE))
        p.drawRect(QRectF(51, 0, 7, TILE))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#B06A3A"))
        for _ in range(8):
            p.drawEllipse(QPointF(rng.uniform(0, TILE), rng.choice((11, 37))), 2, 2)
    elif name == "car":
        p.fillRect(QRectF(0, 26, TILE, 38), QColor("#8A4A32"))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#6A3A26"))
        for _ in range(10):                              # rust
            p.drawEllipse(QPointF(rng.uniform(0, TILE), rng.uniform(26, 64)), rng.uniform(2, 6), rng.uniform(2, 4))
        p.setBrush(QColor("#2A3238"))
        p.drawRoundedRect(QRectF(8, 4, 48, 24), 6, 6)
        p.setBrush(QColor("#4A5A68"))
        p.drawRect(QRectF(12, 8, 18, 16))
        p.drawRect(QRectF(34, 8, 18, 16))
        p.setPen(QPen(QColor("#1A1A1A"), 2))
        p.setBrush(QColor("#2A2A2A"))
        p.drawEllipse(QPointF(14, 58), 8, 8)
        p.drawEllipse(QPointF(50, 58), 8, 8)
        p.setBrush(QColor("#9A8A6A"))
        p.drawEllipse(QPointF(14, 58), 3, 3)
        p.drawEllipse(QPointF(50, 58), 3, 3)
    elif name == "car_top":
        p.fillRect(r, QColor("#8A4A32"))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#6A3A26"))
        for _ in range(12):
            p.drawEllipse(QPointF(rng.uniform(0, TILE), rng.uniform(0, TILE)), rng.uniform(2, 7), rng.uniform(2, 5))
        p.setBrush(QColor("#2A3238"))
        p.drawRect(QRectF(8, 6, 48, 12))
        p.drawRect(QRectF(8, 46, 48, 12))
    elif name == "rubble":
        p.fillRect(r, QColor("#6A665E"))
        p.setPen(QPen(QColor("#3A3832"), 1))
        for _ in range(16):
            x, y = rng.uniform(-4, TILE), rng.uniform(-4, TILE)
            p.setBrush(QColor(rng.choice(("#8A8680", "#5A564E", "#9A9690", "#7A6A5A"))))
            p.drawPolygon(QPolygonF([QPointF(x, y), QPointF(x + rng.uniform(6, 16), y + rng.uniform(-3, 3)),
                                     QPointF(x + rng.uniform(4, 14), y + rng.uniform(5, 12)),
                                     QPointF(x - 1, y + rng.uniform(4, 10))]))
    elif name == "mailbox":
        p.fillRect(r, QColor("#3A3A3A"))
        p.setPen(QPen(QColor("#1A1A1A"), 2))
        p.setBrush(QColor("#4A4A4A"))
        p.drawRoundedRect(QRectF(6, 10, 52, 30), 10, 10)
        p.setBrush(QColor("#C03030"))
        p.drawRect(QRectF(44, 4, 6, 20))
        _text(p, QRectF(6, 14, 52, 22), "111", 12, "#D8D2C4")
    elif name == "workbench":
        p.fillRect(r, QColor("#9A3A2A"))
        _noise(p, r, rng, 60, 40)
        p.setPen(QPen(QColor("#2A1A14"), 2))
        p.setBrush(QColor("#4A4A4A"))
        p.drawRect(QRectF(8, 30, 48, 10))
        p.setBrush(QColor("#C8C8C8"))
        p.drawRect(QRectF(14, 12, 6, 16))
        p.drawEllipse(QPointF(40, 18), 7, 7)
        p.setBrush(QColor("#6A6A6A"))
        p.drawRect(QRectF(24, 48, 20, 8))
    elif name == "bridge":
        p.fillRect(r, QColor("#6A5436"))
        p.setPen(QPen(QColor("#3E2E1C"), 2))
        for y in range(0, TILE, 9):
            p.drawLine(QPointF(0, y), QPointF(TILE, y))
        p.setPen(QPen(QColor("#8A7450"), 1))
        for y in range(2, TILE, 9):
            p.drawLine(QPointF(0, y), QPointF(TILE, y))
        _noise(p, r, rng, 60, 30)
    elif name == "couch":
        p.fillRect(r, QColor("#5A6A48"))
        p.setPen(QPen(QColor("#3A4A2C"), 2))
        p.drawLine(QPointF(0, 24), QPointF(TILE, 24))
        p.drawLine(QPointF(32, 24), QPointF(32, TILE))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#8A7A5A"))
        for _ in range(4):
            p.drawRoundedRect(QRectF(rng.uniform(0, 54), rng.uniform(0, 54), 10, 6), 3, 3)
        _noise(p, r, rng, 40)
    elif name == "fridge":
        p.fillRect(r, QColor("#CFCABC"))
        p.setPen(QPen(QColor("#6A6A64"), 2))
        p.drawLine(QPointF(0, 22), QPointF(TILE, 22))
        p.setBrush(QColor("#8A8A84"))
        p.drawRect(QRectF(50, 6, 5, 12))
        p.drawRect(QRectF(50, 28, 5, 24))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#9A6A4A"))
        for _ in range(8):
            p.drawEllipse(QPointF(rng.uniform(0, TILE), rng.uniform(0, TILE)), rng.uniform(2, 5), rng.uniform(2, 4))
    elif name == "crib":
        p.fillRect(r, QColor("#D8D2C4"))
        p.setPen(QPen(QColor("#9A9488"), 3))
        for x in range(6, TILE, 10):
            p.drawLine(QPointF(x, 6), QPointF(x, 58))
        p.setPen(QPen(QColor("#8A8478"), 4))
        p.drawLine(QPointF(0, 8), QPointF(TILE, 8))
        p.drawLine(QPointF(0, 56), QPointF(TILE, 56))
    elif name == "tv":
        p.fillRect(r, QColor("#6A4A30"))
        p.setPen(QPen(QColor("#2A2A2A"), 3))
        p.setBrush(QColor("#2E3A3E"))
        p.drawRoundedRect(QRectF(8, 8, 40, 34), 8, 8)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#5A5A5A"))
        p.drawEllipse(QPointF(55, 18), 4, 4)
        p.drawEllipse(QPointF(55, 32), 4, 4)
        p.setBrush(QColor("#4A4A4A"))
        p.drawRect(QRectF(6, 48, 52, 10))
    elif name == "sign_welcome":
        p.setPen(QPen(QColor("#1A2A1A"), 2))
        p.setBrush(QColor("#2E6A3E"))
        p.drawRoundedRect(QRectF(2, 8, 60, 48), 4, 4)
        _text(p, QRectF(2, 10, 60, 14), "WELCOME TO", 8, "#E8E4D0", "Arial")
        _text(p, QRectF(2, 24, 60, 18), "SERENITY", 12, "#FFFFFF", "Arial Black")
        _text(p, QRectF(2, 40, 60, 14), "HILLS", 10, "#E8E4D0", "Arial")
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#7A5A3A"))
        for _ in range(6):
            p.drawEllipse(QPointF(rng.uniform(4, 60), rng.uniform(10, 54)), 3, 2)
    elif name == "sign_vault":
        p.setPen(QPen(QColor("#1A1E22"), 2))
        p.setBrush(QColor("#1E5A8A"))
        p.drawRoundedRect(QRectF(2, 8, 60, 48), 4, 4)
        _text(p, QRectF(2, 10, 60, 16), "VAULT-TEC", 10, "#FFFFFF", "Arial Black")
        p.setBrush(QColor(YELLOW))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(32, 40), 12, 12)
        _text(p, QRectF(20, 28, 24, 24), "111", 9, "#1E1E1E", "Arial Black")
    # ---- sprites (transparent) ----
    elif name in ("roach", "roach_dead"):
        dead = name == "roach_dead"
        p.save()
        if dead:
            p.translate(32, 40)
            p.rotate(180)
            p.translate(-32, -40)
        body = QRectF(16, 24, 32, 30)
        g = QRadialGradient(QPointF(28, 32), 24)
        g.setColorAt(0, QColor("#B06A3A"))
        g.setColorAt(1, QColor("#4A2A14"))
        p.setPen(QPen(QColor("#1A0E06"), 2))
        p.setBrush(g)
        p.drawEllipse(body)
        p.setBrush(QColor("#6A3A1A"))
        p.drawEllipse(QRectF(22, 16, 20, 16))
        p.setPen(QPen(QColor("#2A1A0A"), 2))
        for sx in (-1, 1):
            for y0, y1 in ((30, 20), (38, 36), (46, 54)):
                p.drawLine(QPointF(32 + sx * 12, y0), QPointF(32 + sx * 28, y1))
            p.drawLine(QPointF(32 + sx * 6, 18), QPointF(32 + sx * 18, 4))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#FF4040") if not dead else QColor("#3A1A0A"))
        p.drawEllipse(QPointF(27, 22), 2, 2)
        p.drawEllipse(QPointF(37, 22), 2, 2)
        p.setPen(QPen(QColor("#2A1A0A"), 1))
        p.drawLine(QPointF(32, 30), QPointF(32, 52))
        p.restore()
    elif name in ("bloatfly", "bloatfly_dead"):
        dead = name == "bloatfly_dead"
        p.save()
        if dead:
            p.translate(32, 36)
            p.rotate(160)
            p.translate(-32, -36)
        p.setPen(QPen(QColor(120, 140, 120, 150), 1.5))
        p.setBrush(QColor(190, 210, 200, 110))
        for sx in (-1, 1):                               # the wings
            p.drawEllipse(QRectF(32 + (sx * 24 - 14 if sx < 0 else sx * 2), 8, 24, 14))
        g = QRadialGradient(QPointF(28, 34), 20)
        g.setColorAt(0, QColor("#9AB06A"))
        g.setColorAt(1, QColor("#4A5A2A"))
        p.setPen(QPen(QColor("#1A2A10"), 2))
        p.setBrush(g)
        p.drawEllipse(QRectF(14, 22, 36, 28))
        p.setPen(QPen(QColor("#3A4A1A"), 2))
        for y in (32, 40):
            p.drawLine(QPointF(18, y), QPointF(46, y))
        p.setBrush(QColor("#6A7A3A"))
        p.drawEllipse(QRectF(22, 12, 20, 16))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#E03030") if not dead else QColor("#3A1A10"))
        p.drawEllipse(QPointF(27, 18), 3.5, 3.5)
        p.drawEllipse(QPointF(37, 18), 3.5, 3.5)
        p.setPen(QPen(QColor("#2A2A1A"), 2))
        p.drawLine(QPointF(32, 50), QPointF(32, 60))
        p.restore()
    elif name in ("molerat", "molerat_dead"):
        dead = name == "molerat_dead"
        p.save()
        if dead:
            p.translate(32, 44)
            p.rotate(90)
            p.translate(-32, -44)
        g = QRadialGradient(QPointF(30, 36), 26)
        g.setColorAt(0, QColor("#C09A86"))
        g.setColorAt(1, QColor("#6A4A3A"))
        p.setPen(QPen(QColor("#2A1A12"), 2))
        p.setBrush(g)
        p.drawEllipse(QRectF(8, 20, 48, 34))
        p.setBrush(QColor("#A8806C"))
        p.drawEllipse(QRectF(34, 16, 26, 22))                # the head
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#E8A8A0"))
        p.drawEllipse(QPointF(58, 27), 4, 3)                 # the nose
        p.setBrush(QColor("#F0ECD8"))
        p.drawRect(QRectF(50, 32, 4, 9))                      # the teeth
        p.drawRect(QRectF(55, 32, 4, 9))
        p.setBrush(QColor("#1A1A1A") if not dead else QColor("#5A4A42"))
        p.drawEllipse(QPointF(46, 23), 2.2, 2.2)
        p.setPen(QPen(QColor("#2A1A12"), 2))
        p.setBrush(QColor("#9A7A66"))
        for x in (14, 24, 38):
            p.drawRoundedRect(QRectF(x, 48, 8, 12), 3, 3)
        p.setPen(QPen(QColor("#7A5A4A"), 2))
        p.drawLine(QPointF(8, 30), QPointF(2, 16))
        p.restore()
    elif name == "skeleton":
        p.setPen(QPen(QColor("#4A4238"), 2))
        p.setBrush(QColor("#E8E0CC"))
        p.drawEllipse(QRectF(22, 4, 20, 20))
        p.setBrush(QColor("#2A2420"))
        p.drawEllipse(QPointF(28, 13), 2.8, 3)
        p.drawEllipse(QPointF(36, 13), 2.8, 3)
        p.drawRect(QRectF(27, 19, 10, 4))
        p.setPen(QPen(QColor("#D8D0BC"), 3))
        p.drawLine(QPointF(32, 24), QPointF(32, 44))
        for k in range(4):
            p.drawLine(QPointF(24, 28 + k * 4), QPointF(40, 28 + k * 4))
        p.drawLine(QPointF(32, 28), QPointF(14, 44))
        p.drawLine(QPointF(32, 28), QPointF(50, 40))
        p.drawLine(QPointF(32, 44), QPointF(22, 62))
        p.drawLine(QPointF(32, 44), QPointF(44, 60))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(60, 90, 140, 150))
        p.drawRect(QRectF(26, 30, 12, 14))
    elif name == "baton":
        p.save()
        p.translate(32, 32)
        p.rotate(-35)
        p.setPen(QPen(QColor("#111111"), 2))
        p.setBrush(QColor("#2A2A2A"))
        p.drawRoundedRect(QRectF(-4, -28, 8, 56), 3, 3)
        p.setBrush(QColor("#555555"))
        p.drawRoundedRect(QRectF(-5, 10, 10, 18), 3, 3)
        p.setBrush(QColor("#4AA0FF"))
        p.drawEllipse(QPointF(0, -24), 3, 3)
        p.restore()
    elif name == "pistol":
        p.setPen(QPen(QColor("#111111"), 2))
        p.setBrush(QColor("#4A4A4A"))
        p.drawRoundedRect(QRectF(8, 22, 46, 14), 3, 3)
        p.drawRoundedRect(QRectF(30, 32, 14, 24), 3, 3)
        p.setBrush(QColor("#2A2A2A"))
        p.drawRect(QRectF(8, 26, 10, 6))
        p.drawRoundedRect(QRectF(22, 36, 8, 8), 2, 2)
        p.setBrush(QColor("#6A5A3A"))
        p.drawRoundedRect(QRectF(33, 38, 9, 16), 2, 2)
    elif name == "stimpak":
        p.setPen(QPen(QColor("#111111"), 2))
        p.setBrush(QColor("#DDE6EE"))
        p.drawRoundedRect(QRectF(26, 10, 12, 36), 3, 3)
        p.setBrush(QColor("#E04040"))
        p.drawRect(QRectF(27, 24, 10, 10))
        p.setPen(QPen(QColor("#9AA7B2"), 2))
        p.drawLine(QPointF(32, 46), QPointF(32, 58))
        p.setPen(QPen(QColor("#111111"), 2))
        p.setBrush(QColor("#6A7378"))
        p.drawRect(QRectF(22, 6, 20, 6))
    elif name == "pipboy":
        p.setPen(QPen(QColor("#111111"), 2))
        p.setBrush(QColor("#5A6A4A"))
        p.drawRoundedRect(QRectF(8, 14, 48, 36), 8, 8)
        p.setBrush(QColor("#0A1A10"))
        p.drawRoundedRect(QRectF(14, 20, 28, 22), 3, 3)
        p.setPen(QPen(QColor(GREEN), 2))
        for k, w_ in enumerate((18, 12, 20)):
            p.drawLine(QPointF(17, 25 + k * 5), QPointF(17 + w_, 25 + k * 5))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#9AA07A"))
        p.drawEllipse(QPointF(49, 31), 4, 4)
        p.setBrush(QColor("#2A2A2A"))
        p.drawRect(QRectF(20, 50, 24, 6))
    elif name == "ammo":
        p.setPen(QPen(QColor("#111111"), 2))
        p.setBrush(QColor("#5A7A4A"))
        p.drawRoundedRect(QRectF(12, 18, 40, 30), 3, 3)
        p.setBrush(QColor("#C8A040"))
        for x in (18, 26, 34, 42):
            p.drawRoundedRect(QRectF(x, 8, 6, 14), 2, 2)
        _text(p, QRectF(12, 30, 40, 16), "10mm", 10, "#F0F0D0")
    elif name == "spouse":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(180, 210, 230, 150))
        p.drawEllipse(QRectF(20, 6, 24, 24))
        p.drawRoundedRect(QRectF(18, 30, 28, 30), 8, 8)
    elif name == "tree":                                 # 128 x 128: a bare, dead tree
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#3A2E24"))
        p.drawPolygon(QPolygonF([QPointF(56, 128), QPointF(72, 128), QPointF(67, 70), QPointF(61, 70)]))
        p.setBrush(QColor("#4A3A2E"))
        p.drawPolygon(QPolygonF([QPointF(58, 128), QPointF(64, 128), QPointF(63, 72), QPointF(61, 72)]))

        def branch(x, y, angle, length, width, depth):
            if depth == 0 or length < 4:
                return
            nx, ny = x + math.cos(angle) * length, y - math.sin(angle) * length
            p.setPen(QPen(QColor("#3A2E24"), width, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(x, y), QPointF(nx, ny))
            for da in (rng.uniform(0.35, 0.8), -rng.uniform(0.35, 0.8)):
                branch(nx, ny, angle + da, length * rng.uniform(0.55, 0.75), max(1.0, width * 0.6), depth - 1)
            if rng.random() < 0.5:
                branch(nx, ny, angle + rng.uniform(-0.2, 0.2), length * 0.6, max(1.0, width * 0.6), depth - 1)
        branch(64, 74, math.pi / 2 + 0.15, 26, 7, 5)
        branch(64, 90, math.pi / 2 + 0.9, 22, 5, 4)
        branch(64, 84, math.pi / 2 - 0.9, 24, 5, 4)
    elif name == "bush":
        p.setPen(QPen(QColor("#4A3E2A"), 1.5, Qt.SolidLine, Qt.RoundCap))
        for _ in range(26):
            x = rng.uniform(16, 48)
            p.drawLine(QPointF(32, 60), QPointF(x, rng.uniform(18, 44)))
            p.drawLine(QPointF(x, rng.uniform(24, 44)), QPointF(x + rng.uniform(-10, 10), rng.uniform(12, 36)))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(140, 130, 80, 150))
        for _ in range(14):
            p.drawEllipse(QPointF(rng.uniform(14, 50), rng.uniform(16, 48)), rng.uniform(2, 5), rng.uniform(2, 4))
    elif name == "robot":                                # 128 x 128: a Mr. Handy sort of butler
        cx, cy = 64, 62
        for k, ang in enumerate((-0.9, 0.0, 0.9)):       # three eye stalks
            ex, ey = cx + math.sin(ang) * 30, cy - 44 - abs(math.cos(ang)) * 6
            p.setPen(QPen(QColor("#3A4046"), 7, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(cx + math.sin(ang) * 10, cy - 24), QPointF(ex, ey))
            p.setPen(QPen(QColor("#1A1E22"), 2))
            p.setBrush(QColor("#6A737C"))
            p.drawEllipse(QPointF(ex, ey), 9, 9)
            p.setBrush(QColor("#102A18"))
            p.drawEllipse(QPointF(ex, ey), 6, 6)
            p.setBrush(QColor("#5AE07A"))
            p.drawEllipse(QPointF(ex - 1, ey - 1), 3, 3)
        g = QRadialGradient(QPointF(cx - 12, cy - 12), 36)
        g.setColorAt(0, QColor("#AAB4BC"))
        g.setColorAt(1, QColor("#4A535A"))
        p.setPen(QPen(QColor("#1A1E22"), 2.5))
        p.setBrush(g)
        p.drawEllipse(QPointF(cx, cy), 30, 30)
        p.setPen(QPen(QColor("#2A3137"), 1.5))
        p.drawLine(QPointF(cx - 30, cy), QPointF(cx + 30, cy))
        p.drawEllipse(QPointF(cx, cy), 18, 18)
        for k in range(8):
            a = k * math.pi / 4
            p.setBrush(QColor("#2A3137"))
            p.drawEllipse(QPointF(cx + math.cos(a) * 24, cy + math.sin(a) * 24), 2, 2)
        for ang in (-1.1, 0.0, 1.1):                      # three arms, one with a pincer, one a saw, one a torch
            ax, ay = cx + math.sin(ang) * 40, cy + 30 + abs(math.cos(ang)) * 8
            p.setPen(QPen(QColor("#3A4046"), 6, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(cx + math.sin(ang) * 16, cy + 22), QPointF(ax, ay))
            p.setPen(QPen(QColor("#1A1E22"), 2))
            p.setBrush(QColor("#7A858E"))
            if ang == 0.0:
                p.drawEllipse(QPointF(ax, ay + 4), 8, 8)
                p.setPen(QPen(QColor("#1A1E22"), 1.5))
                for t in range(8):
                    a = t * math.pi / 4
                    p.drawLine(QPointF(ax, ay + 4), QPointF(ax + math.cos(a) * 11, ay + 4 + math.sin(a) * 11))
            elif ang < 0:
                p.drawPolygon(QPolygonF([QPointF(ax - 8, ay), QPointF(ax, ay + 12), QPointF(ax + 8, ay),
                                         QPointF(ax + 4, ay - 2), QPointF(ax, ay + 5), QPointF(ax - 4, ay - 2)]))
            else:
                p.drawRect(QRectF(ax - 4, ay, 8, 10))
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#FFB040"))
                p.drawEllipse(QPointF(ax, ay + 14), 4, 5)
        g2 = QRadialGradient(QPointF(cx, cy + 44), 16)   # the thruster flame
        g2.setColorAt(0, QColor(255, 240, 160, 230))
        g2.setColorAt(0.5, QColor(255, 150, 50, 170))
        g2.setColorAt(1, QColor(255, 80, 20, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(g2)
        p.drawEllipse(QPointF(cx, cy + 44), 14, 22)
        p.setPen(QPen(QColor("#1A1E22"), 2))
        p.setBrush(QColor("#5A636A"))
        p.drawPolygon(QPolygonF([QPointF(cx - 10, cy + 28), QPointF(cx + 10, cy + 28), QPointF(cx + 7, cy + 38),
                                 QPointF(cx - 7, cy + 38)]))
    elif name in ("meat", "meat_fly", "meat_rat"):
        col = {"meat": ("#8A5A3A", "#C08A60"), "meat_fly": ("#6A7A3A", "#A8B870"), "meat_rat": ("#A8404A", "#E08A8A")}[name]
        p.setPen(QPen(QColor("#2A1A10"), 2))
        g = QRadialGradient(QPointF(28, 30), 22)
        g.setColorAt(0, QColor(col[1]))
        g.setColorAt(1, QColor(col[0]))
        p.setBrush(g)
        p.drawPolygon(QPolygonF([QPointF(12, 34), QPointF(22, 18), QPointF(44, 16), QPointF(54, 30), QPointF(46, 50),
                                 QPointF(24, 52)]))
        p.setPen(QPen(QColor(col[1]).lighter(130), 2))
        p.drawLine(QPointF(20, 36), QPointF(40, 26))
        p.drawLine(QPointF(28, 46), QPointF(44, 38))
    elif name == "cola":
        p.setPen(QPen(QColor("#2A1A10"), 2))
        p.setBrush(QColor("#7A4A20"))
        p.drawRoundedRect(QRectF(24, 20, 16, 40), 5, 5)
        p.drawRect(QRectF(28, 6, 8, 16))
        p.setBrush(QColor("#B02020"))
        p.setPen(Qt.NoPen)
        p.drawRect(QRectF(24, 32, 16, 14))
        _text(p, QRectF(22, 32, 20, 14), "NUKA", 6, "#FFFFFF", "Arial")
        p.setBrush(QColor("#C8C8C8"))
        p.drawRect(QRectF(27, 4, 10, 4))
    elif name == "radaway":
        p.setPen(QPen(QColor("#2A1A10"), 2))
        p.setBrush(QColor("#E8902A"))
        p.drawRoundedRect(QRectF(18, 10, 28, 40), 6, 6)
        p.setPen(QPen(QColor("#9AA7B2"), 2.5))
        p.drawLine(QPointF(32, 50), QPointF(36, 60))
        _text(p, QRectF(18, 20, 28, 20), "RAD", 8, "#FFFFFF", "Arial Black")
    elif name == "marker":
        p.setPen(QPen(QColor("#FFFFFF"), 3))
        p.setBrush(QColor(80, 220, 255, 200))
        p.drawPolygon(QPolygonF([QPointF(32, 6), QPointF(56, 32), QPointF(32, 58), QPointF(8, 32)]))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 180))
        p.drawPolygon(QPolygonF([QPointF(32, 18), QPointF(44, 32), QPointF(32, 46), QPointF(20, 32)]))
    p.end()
    return img


def atlas():
    rng = random.Random(111)
    img = QImage(TILE * COLS, TILE * COLS, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    for name, (col, row, w, h) in INDEX.items():
        p.drawImage(col * TILE, row * TILE, _tile(name, rng, w, h))
    p.end()
    return img


def tile_image(name, atlas_img):
    col, row, w, h = INDEX[name]
    return atlas_img.copy(col * TILE, row * TILE, TILE * w, TILE * h)
