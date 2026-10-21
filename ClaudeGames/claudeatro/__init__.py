"""Claudeatro: poker hands, chips x mult, and the jokers that break the rules - after Balatro.

Play poker hands to beat each Blind's score; a Small, a Big and a Boss Blind make an Ante, and beating Ante 8's boss
wins the run (then it goes on, endlessly). Between Blinds the shop sells Jokers, Tarot and Planet cards, booster
packs and vouchers. Drag cards and jokers to reorder them; right-click clears a selection. (The rules are in game.py;
the soundscape - all synthesized - is in sound.py, and the music and the sound effects can each be switched off.)

The run saves itself as you go."""
import json
import math
import time

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QIcon, QImage, QLinearGradient, QPainter, QPainterPath, QPen,
                           QPixmap, QRadialGradient)
from PySide6.QtWidgets import QWidget
from shiboken6 import isValid

from claudecore import host

from .game import (DECKS, EDITIONS, ENHANCEMENTS, FACE, HANDS, JOKERS, PACK_SIZES, PACKS, PLANETS, SECRET,
                   SUIT_NAME, SUIT_SYMBOL, SUITS, TAGS, TAROTS, VOUCHERS, Run, fmt, pack_name, rank_chips, rank_label,
                   rank_name)
from .sound import Audio

TITLE = "Claudeatro"
EMOJI = "Segoe UI Emoji"
UI = "Segoe UI"
SYMBOL = "Segoe UI Symbol"
CHIPS = "#009DFF"
MULT = "#FE5F55"
MONEY = "#F5B143"
ORANGE = "#FDA200"
GREEN = "#3FAF7A"
DIM = "#9FB0B3"
SUIT_COLOUR = {"S": "#2B3A55", "H": "#E0463A", "D": "#E8862A", "C": "#2C7C9E"}
RARITY = {1: ("Common", "#3C82D0"), 2: ("Uncommon", "#3AA05E"), 3: ("Rare", "#D24A3E")}
PLANET_COLOUR = {"Pluto": "#B9A69A", "Mercury": "#A7A7A7", "Uranus": "#7FD6E0", "Venus": "#E8C27A",
                 "Saturn": "#D9B26A", "Jupiter": "#D49A6A", "Earth": "#4C8FD6", "Mars": "#D2553A",
                 "Neptune": "#3C5FD6", "Planet X": "#9A6BE0", "Ceres": "#9A9A8A", "Eris": "#D0D6E0"}
ENH_TAG = {"bonus": "+30", "mult": "+4", "lucky": "LUCKY", "glass": "GLASS", "steel": "STEEL", "gold": "GOLD",
           "wild": "WILD"}
CW, CH = 84, 116                # a playing card
JW, JH = 80, 108                # a joker, tarot, planet, pack or voucher
SIDE = 250
PIPS = {2: [(.5, .1), (.5, .9)], 3: [(.5, .1), (.5, .5), (.5, .9)],
        4: [(.2, .1), (.8, .1), (.2, .9), (.8, .9)],
        5: [(.2, .1), (.8, .1), (.5, .5), (.2, .9), (.8, .9)],
        6: [(.2, .1), (.8, .1), (.2, .5), (.8, .5), (.2, .9), (.8, .9)],
        7: [(.2, .1), (.8, .1), (.5, .3), (.2, .5), (.8, .5), (.2, .9), (.8, .9)],
        8: [(.2, .1), (.8, .1), (.5, .3), (.2, .5), (.8, .5), (.5, .7), (.2, .9), (.8, .9)],
        9: [(.2, .1), (.8, .1), (.2, .37), (.8, .37), (.5, .5), (.2, .63), (.8, .63), (.2, .9), (.8, .9)],
        10: [(.2, .1), (.8, .1), (.5, .25), (.2, .37), (.8, .37), (.2, .63), (.8, .63), (.5, .75), (.2, .9),
             (.8, .9)]}
SPEEDS = (1, 2, 4)

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


def text(p, rect, s, size, colour="#FFFFFF", align=Qt.AlignCenter, bold=True, shadow=True, family=UI):
    p.setFont(font(size, bold, family))
    if shadow:
        p.setPen(QColor(0, 0, 0, 120))
        p.drawText(rect.translated(1.2, 1.8), align, s)
    p.setPen(QColor(colour))
    p.drawText(rect, align, s)


def panel(p, rect, fill="#1E2C30", border="#3A5157", radius=10, width=2.0):
    p.setPen(QPen(QColor(border), width) if border else Qt.NoPen)
    p.setBrush(QColor(fill))
    p.drawRoundedRect(rect, radius, radius)


def fmt_mult(m):
    return fmt(m) if abs(m - round(m)) < 1e-6 or m >= 1000 else f"{m:.1f}"


def _shadow(p, r, radius=7):
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 80))
    p.drawRoundedRect(r.translated(2, 5), radius, radius)


def _edition(p, path, r, ed, t):
    if not ed:
        return
    shift = (math.sin(t * 1.3) + 1) / 2
    g = QLinearGradient(r.topLeft(), r.bottomRight())
    if ed == "poly":
        for k, col in enumerate(("#FF6B6B", "#FFD36B", "#6BFF8E", "#6BC8FF", "#C46BFF", "#FF6B6B")):
            g.setColorAt(k / 5, QColor(col).lighter(110))
        p.setOpacity(0.33)
    else:
        col = QColor(130, 200, 255, 150) if ed == "foil" else QColor(255, 80, 150, 140)
        g.setColorAt(0, QColor(0, 0, 0, 0))
        g.setColorAt(max(0.01, min(0.98, shift - 0.15)), QColor(0, 0, 0, 0))
        g.setColorAt(max(0.02, min(0.99, shift)), col)
        g.setColorAt(min(1.0, shift + 0.2), QColor(0, 0, 0, 0))
        g.setColorAt(1, QColor(0, 0, 0, 0))
        p.setOpacity(0.9)
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawPath(path)
    p.setOpacity(1.0)


_cache = {}


def _cached(p, r, key, draw):
    """Draw something that never changes from a pixmap (painting cards from scratch every frame is slow)."""
    pm = _cache.get(key)
    if pm is None:
        if len(_cache) > 600:
            _cache.clear()
        w, h = r.width(), r.height()
        pm = QPixmap(int((w + 8) * 2), int((h + 11) * 2))
        pm.setDevicePixelRatio(2)
        pm.fill(Qt.transparent)
        q = QPainter(pm)
        q.setRenderHint(QPainter.Antialiasing)
        q.setRenderHint(QPainter.TextAntialiasing)
        draw(q, QRectF(2, 2, w, h))
        q.end()
        _cache[key] = pm
    p.drawPixmap(QPointF(r.x() - 2, r.y() - 2), pm)


def paint_card(p, r, c, t=0.0, debuffed=False):
    """A playing card (rank, suit, enhancement and edition)."""
    key = ("card", c["r"], c["s"], c["enh"], c["id"] if c["enh"] == "stone" else 0, r.width(), r.height())
    _cached(p, r, key, lambda q, rr: _card_face(q, rr, c))
    path = QPainterPath()
    path.addRoundedRect(r, 7, 7)
    _edition(p, path, r, c["ed"], t + c["id"] * 0.37)
    if debuffed:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(30, 30, 30, 150))
        p.drawPath(path)
        p.setPen(QPen(QColor("#E0463A"), 4))
        p.drawLine(r.topLeft() + QPointF(16, 24), r.bottomRight() - QPointF(16, 24))
        p.drawLine(QPointF(r.right() - 16, r.y() + 24), QPointF(r.x() + 16, r.bottom() - 24))


def _card_face(p, r, c):
    enh = c["enh"]
    path = QPainterPath()
    path.addRoundedRect(r, 7, 7)
    _shadow(p, r)
    if enh == "stone":
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, QColor("#A3A39C"))
        g.setColorAt(1, QColor("#6C6C67"))
        p.setBrush(g)
        p.setPen(QPen(QColor("#4A4A46"), 1.5))
        p.drawPath(path)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(60, 60, 55, 110))
        for k in range(16):
            x = r.x() + 8 + ((c["id"] * 37 + k * 53) % 97) / 97 * (r.width() - 16)
            y = r.y() + 8 + ((c["id"] * 61 + k * 29) % 89) / 89 * (r.height() - 16)
            p.drawEllipse(QPointF(x, y), 2 + k % 3, 1.5 + k % 2)
        text(p, QRectF(r.x(), r.bottom() - 24, r.width(), 18), "+50", 12, "#EEEEEE")
    else:
        if enh == "wild":
            brush = QLinearGradient(r.topLeft(), r.bottomRight())
            for k, col in enumerate(("#FFD9D6", "#FFF1C9", "#D6F5DA", "#D3E9FF", "#EAD9FF")):
                brush.setColorAt(k / 4, QColor(col))
        elif enh in ("gold", "steel"):
            brush = QLinearGradient(r.topLeft(), r.bottomRight())
            a, b = ("#FBE38A", "#D9A42B") if enh == "gold" else ("#E4E8EC", "#A6AEB8")
            brush.setColorAt(0, QColor(a))
            brush.setColorAt(1, QColor(b))
        else:
            brush = QColor({"bonus": "#D3E8FF", "mult": "#FFDAD5", "lucky": "#DFF6CC",
                            "glass": "#E9F7FF"}.get(enh, "#F8F6EF"))
        if enh == "glass":
            p.setOpacity(0.86)
        p.setBrush(brush)
        p.setPen(QPen(QColor("#B8892A" if enh == "gold" else "#3A3A3A"), 1.5))
        p.drawPath(path)
        p.setOpacity(1.0)
        col = QColor(SUIT_COLOUR[c["s"]])
        sym = SUIT_SYMBOL[c["s"]]
        lab = rank_label(c["r"])
        for flip in (False, True):
            p.save()
            if flip:
                p.translate(r.right(), r.bottom())
                p.rotate(180)
                o = QPointF(0, 0)
            else:
                o = r.topLeft()
            text(p, QRectF(o.x() + 3, o.y() + 3, 22, 20), lab, 17, col, Qt.AlignHCenter | Qt.AlignTop, shadow=False)
            text(p, QRectF(o.x() + 3, o.y() + 21, 22, 16), sym, 13, col, Qt.AlignHCenter | Qt.AlignTop,
                 shadow=False, family=SYMBOL)
            p.restore()
        inner = r.adjusted(22, 18, -22, -18)
        if c["r"] in FACE:
            tint = QColor(col)
            tint.setAlpha(38)
            p.setPen(QPen(col, 1.2))
            p.setBrush(tint)
            p.drawRoundedRect(inner.adjusted(-4, 0, 4, 0), 4, 4)
            text(p, inner.adjusted(0, -10, 0, 0), lab, 34, col, shadow=False, family="Georgia")
            text(p, QRectF(inner.x(), inner.bottom() - 26, inner.width(), 22), sym, 18, col, shadow=False,
                 family=SYMBOL)
        elif c["r"] == 14:
            text(p, inner, sym, 46, col, shadow=False, family=SYMBOL)
        else:
            for fx, fy in PIPS.get(c["r"], []):
                x = inner.x() + fx * inner.width()
                y = inner.y() + fy * inner.height()
                text(p, QRectF(x - 11, y - 11, 22, 22), sym, 17, col, shadow=False, family=SYMBOL)
        if enh in ENH_TAG:
            text(p, QRectF(r.x() + 22, r.y() + 3, r.width() - 44, 12), ENH_TAG[enh], 9,
                 "#C0392B" if enh in ("mult", "lucky") else "#2B6CB0" if enh == "bonus" else "#555555", shadow=False)


def paint_back(p, r, colour="#D9473C"):
    _cached(p, r, ("back", colour, r.width(), r.height()), lambda q, rr: _back(q, rr, colour))


def _back(p, r, colour):
    path = QPainterPath()
    path.addRoundedRect(r, 7, 7)
    _shadow(p, r)
    p.setBrush(QColor("#F4F0E6"))
    p.setPen(QPen(QColor("#2A2A2A"), 1.5))
    p.drawPath(path)
    inner = r.adjusted(6, 6, -6, -6)
    p.setBrush(QColor(colour))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(inner, 4, 4)
    p.save()
    p.setClipRect(inner)
    p.setPen(QPen(QColor(255, 255, 255, 60), 2))
    step = 12
    for k in range(-int(inner.height()), int(inner.width()) + int(inner.height()), step):
        p.drawLine(QPointF(inner.x() + k, inner.y()), QPointF(inner.x() + k + inner.height(), inner.bottom()))
        p.drawLine(QPointF(inner.x() + k, inner.bottom()), QPointF(inner.x() + k + inner.height(), inner.y()))
    p.restore()


def paint_joker(p, r, j, t=0.0, disabled=False):
    _cached(p, r, ("joker", j["k"], r.width(), r.height()), lambda q, rr: _joker_face(q, rr, j["k"]))
    path = QPainterPath()
    path.addRoundedRect(r, 7, 7)
    _edition(p, path, r, j["ed"], t + j["id"] * 0.53)
    if disabled:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(20, 20, 20, 170))
        p.drawPath(path)
        text(p, r, "Disabled", 13, MULT)


def _joker_face(p, r, key):
    emoji, rarity, _cost, _d = JOKERS[key]
    col = QColor(RARITY[rarity][1])
    path = QPainterPath()
    path.addRoundedRect(r, 7, 7)
    _shadow(p, r)
    g = QLinearGradient(r.topLeft(), r.bottomLeft())
    g.setColorAt(0, col.lighter(125))
    g.setColorAt(1, col.darker(120))
    p.setBrush(g)
    p.setPen(QPen(col.darker(170), 1.5))
    p.drawPath(path)
    inner = r.adjusted(5, 5, -5, -27)
    p.setBrush(QColor("#F4EBD6"))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(inner, 5, 5)
    text(p, inner, emoji, 38, "#000000", shadow=False, family=EMOJI)
    text(p, QRectF(r.x() + 2, r.bottom() - 26, r.width() - 4, 24), key, 10, "#FFFFFF",
         Qt.AlignCenter | Qt.TextWordWrap)


def paint_planet(p, center, rad, name):
    col = QColor(PLANET_COLOUR.get(name, "#AAAAAA"))
    if name == "Saturn":
        p.setPen(QPen(col.lighter(130), 3))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, rad * 1.7, rad * 0.45)
    g = QRadialGradient(center - QPointF(rad * 0.35, rad * 0.35), rad * 1.4)
    g.setColorAt(0, col.lighter(150))
    g.setColorAt(1, col.darker(170))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawEllipse(center, rad, rad)


def paint_consumable(p, r, kind, name, t=0.0):
    _cached(p, r, ("cons", kind, name, r.width(), r.height()), lambda q, rr: _consumable(q, rr, kind, name))


def _consumable(p, r, kind, name):
    path = QPainterPath()
    path.addRoundedRect(r, 7, 7)
    _shadow(p, r)
    g = QLinearGradient(r.topLeft(), r.bottomLeft())
    if kind == "tarot":
        g.setColorAt(0, QColor("#9A79D0"))
        g.setColorAt(1, QColor("#5B3E8C"))
    else:
        g.setColorAt(0, QColor("#3A62A8"))
        g.setColorAt(1, QColor("#1B2A4A"))
    p.setBrush(g)
    p.setPen(QPen(QColor("#2A1C40" if kind == "tarot" else "#0E1830"), 1.5))
    p.drawPath(path)
    inner = r.adjusted(5, 5, -5, -27)
    if kind == "tarot":
        p.setBrush(QColor("#F4EBD6"))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(inner, 5, 5)
        text(p, inner, TAROTS[name][0], 34, "#000000", shadow=False, family=EMOJI)
    else:
        p.setBrush(QColor("#0B1228"))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(inner, 5, 5)
        p.setBrush(QColor(255, 255, 255, 170))
        seed = sum(map(ord, name))
        for k in range(9):
            x = inner.x() + 4 + ((seed * 31 + k * 47) % 89) / 89 * (inner.width() - 8)
            y = inner.y() + 4 + ((seed * 17 + k * 71) % 83) / 83 * (inner.height() - 8)
            p.drawEllipse(QPointF(x, y), 0.9, 0.9)
        paint_planet(p, inner.center(), min(inner.width(), inner.height()) * 0.26, name)
    text(p, QRectF(r.x() + 2, r.bottom() - 26, r.width() - 4, 24), name, 10, "#FFFFFF",
         Qt.AlignCenter | Qt.TextWordWrap)


def paint_pack(p, r, kind, size):
    _cached(p, r, ("pack", kind, size, r.width(), r.height()), lambda q, rr: _pack(q, rr, kind, size))


def _pack(p, r, kind, size):
    emoji, colour, _d = PACKS[kind]
    col = QColor(colour)
    path = QPainterPath()
    path.addRoundedRect(r, 6, 6)
    _shadow(p, r)
    g = QLinearGradient(r.topLeft(), r.bottomRight())
    g.setColorAt(0, col.lighter(135))
    g.setColorAt(0.5, col)
    g.setColorAt(1, col.darker(140))
    p.setBrush(g)
    p.setPen(QPen(col.darker(180), 1.5))
    p.drawPath(path)
    p.setPen(QPen(QColor(255, 255, 255, 120), 1.5))           # the crimped ends of the wrapper
    for y in (r.y() + 7, r.bottom() - 7):
        for k in range(int(r.width() // 6)):
            x = r.x() + 3 + k * 6
            p.drawLine(QPointF(x, y - 2), QPointF(x + 3, y + 2))
            p.drawLine(QPointF(x + 3, y + 2), QPointF(x + 6, y - 2))
    text(p, r.adjusted(0, 6, 0, -30), emoji, 32, "#000000", shadow=False, family=EMOJI)
    label = kind if size == "normal" else f"{PACK_SIZES[size][0].strip().upper()}\n{kind}"
    text(p, QRectF(r.x(), r.bottom() - 40, r.width(), 32), label, 10, "#FFFFFF", Qt.AlignCenter)


def paint_voucher(p, r, name):
    _cached(p, r, ("voucher", name, r.width(), r.height()), lambda q, rr: _voucher(q, rr, name))


def _voucher(p, r, name):
    path = QPainterPath()
    path.addRoundedRect(r, 6, 6)
    for y in (r.center().y(),):
        notch = QPainterPath()
        notch.addEllipse(QPointF(r.x(), y), 8, 8)
        notch.addEllipse(QPointF(r.right(), y), 8, 8)
        path = path.subtracted(notch)
    _shadow(p, r)
    g = QLinearGradient(r.topLeft(), r.bottomRight())
    g.setColorAt(0, QColor("#F2D27A"))
    g.setColorAt(1, QColor("#B8862C"))
    p.setBrush(g)
    p.setPen(QPen(QColor("#6E4F14"), 1.5))
    p.drawPath(path)
    text(p, r.adjusted(0, 4, 0, -30), VOUCHERS[name][0], 30, "#000000", shadow=False, family=EMOJI)
    text(p, QRectF(r.x() + 2, r.bottom() - 28, r.width() - 4, 24), name, 10, "#3A2A08",
         Qt.AlignCenter | Qt.TextWordWrap, shadow=False)


def paint_tag(p, center, rad, tag):
    p.setPen(QPen(QColor("#FFFFFF"), 2))
    p.setBrush(QColor("#2C3E44"))
    p.drawEllipse(center, rad, rad)
    text(p, QRectF(center.x() - rad, center.y() - rad, rad * 2, rad * 2), TAGS[tag][0], rad * 1.1, "#000000",
         shadow=False, family=EMOJI)


class Swirl:
    """Balatro's swirling backdrop, done by colour-cycling a fixed spiral pattern (cheap in Python)."""
    W, H = 168, 105

    def __init__(self):
        img = QImage(self.W, self.H, QImage.Format_Indexed8)
        img.setColorCount(256)
        cx, cy = self.W / 2, self.H / 2
        for y in range(self.H):
            for x in range(self.W):
                dx, dy = (x - cx) / self.W, (y - cy) / self.W
                rr = math.hypot(dx, dy)
                a = math.atan2(dy, dx)
                v = (a / (2 * math.pi) + rr * 2.4 + 0.08 * math.sin(x * 0.11 + y * 0.07)
                     + 0.06 * math.sin(y * 0.19 - x * 0.05))
                img.setPixel(x, y, int(v * 256) % 256)
        self.img = img
        self.colours = None

    def frame(self, t, a, b, dark="#14201F"):
        ca, cb, cd = QColor(a), QColor(b), QColor(dark)
        table = []
        for i in range(256):
            ph = i / 256 * 2 * math.pi * 2 - t * 0.5
            k = 0.5 + 0.5 * math.sin(ph)
            k2 = 0.5 + 0.5 * math.sin(ph * 0.5 + 1.3 + t * 0.15)
            rr = ca.red() * k + cb.red() * (1 - k)
            gg = ca.green() * k + cb.green() * (1 - k)
            bb = ca.blue() * k + cb.blue() * (1 - k)
            d = 0.25 + 0.45 * k2
            rr, gg, bb = rr * (1 - d) + cd.red() * d, gg * (1 - d) + cd.green() * d, bb * (1 - d) + cd.blue() * d
            table.append(0xFF000000 | (int(rr) << 16) | (int(gg) << 8) | int(bb))
        self.img.setColorTable(table)
        return self.img


# ---- the table -------------------------------------------------------------------------------------------------
class Table(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setMouseTracking(True)
        self.setMinimumSize(1100, 720)
        self.settings = self._load("settings.json", {}) or {}
        self.speed = self.settings.get("speed", 1) if self.settings.get("speed") in SPEEDS else 1
        self.deck_choice = self.settings.get("deck", "Red Deck")
        if self.deck_choice not in DECKS:
            self.deck_choice = "Red Deck"
        self.music_on = self.settings.get("music", True)
        self.sfx_on = self.settings.get("sfx", True)
        self.audio = Audio(self, self.music_on, self.sfx_on)
        self.stats = self._load("stats.json", {}) or {}
        self.run = None
        saved = self._load("run.json", None)
        if saved:
            try:
                self.run = Run.from_json(saved)
            except (KeyError, TypeError, ValueError, IndexError):
                self.run = None
        self.screen = "title"
        self.sel = []                   # selected card ids (in a round)
        self.psel = []                  # selected card ids (in an Arcana pack's hand)
        self.jsel = None                # selected joker
        self.csel = None                # selected consumable
        self.overlay = None             # "info" / "deck"
        self.anim = None                # a played hand being scored
        self.drag = None
        self.toast = None
        self.recorded = False
        self.mouse = QPointF(-1, -1)
        self.hits, self.drags, self.tips, self.anchors = [], [], [], {}
        self.pos, self.targets = {}, {}
        self.seen = set()
        self.swirl = Swirl()
        self.t = 0.0
        self.last = time.perf_counter()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    # ---- saving ----
    def _load(self, name, default):
        try:
            return json.loads((host.saves(TITLE) / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return default

    def _write(self, name, data):
        try:
            path = host.saves(TITLE) / name
            if data is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(json.dumps(data), encoding="utf-8")
        except OSError:
            pass

    def _save(self):
        run = self.run
        if run is None or self.anim:
            return
        if run.stage == "over":
            self._write("run.json", None)
            return
        self._write("run.json", run.to_json())

    def _save_settings(self):
        self._write("settings.json", {"speed": self.speed, "deck": self.deck_choice, "music": self.music_on,
                                      "sfx": self.sfx_on})

    def _record(self, won=False):
        s = self.stats
        run = self.run
        s["best_hand"] = max(s.get("best_hand", 0), run.best_hand)
        s["highest_ante"] = max(s.get("highest_ante", 0), run.ante)
        if won:
            s["wins"] = s.get("wins", 0) + 1
        else:
            s["runs"] = s.get("runs", 0) + 1
        self._write("stats.json", s)

    # ---- the clock ----
    def _tick(self):
        now = time.perf_counter()
        dt = min(0.1, now - self.last)
        self.last = now
        self.t += dt
        k = 1 - math.exp(-dt * 15)
        for key, (tx, ty) in self.targets.items():
            cur = self.pos.get(key)
            if cur is not None:
                cur[0] += (tx - cur[0]) * k
                cur[1] += (ty - cur[1]) * k
        if self.anim:
            self._step_anim(dt)
        self.audio.mood = self._mood()
        self.audio.tick(dt)
        if self.toast and self.t > self.toast[1]:
            self.toast = None
        self.update()

    def _at(self, key, x, y, spawn=None):
        """Where a card is drawn: it glides toward (x, y)."""
        cur = self.pos.get(key)
        if cur is None:
            cur = list(spawn) if spawn else [x, y]
            self.pos[key] = cur
        self.targets[key] = (x, y)
        self.seen.add(key)
        return cur[0], cur[1]

    def _mood(self):
        run = self.run
        if self.screen == "title" or run is None:
            return "main"
        if run.rnd and run.rnd.kind == "boss" and run.stage == "round":
            return "boss"
        return "shop" if run.stage in ("shop", "pack", "cashout") else "main"

    def sfx(self, name):
        self.audio.play(name)

    def say(self, msg, secs=2.2):
        if msg:
            self.toast = (msg, self.t + secs)

    # ---- the scoring animation ----
    def _step_anim(self, dt):
        a = self.anim
        a["clock"] += dt * self.speed
        ev = a["res"]["events"]
        if a["phase"] == "lift":
            if a["clock"] >= 0.45:
                a["clock"] = 0.0
                a["phase"] = "events" if ev else "total"
                a["i"] = 0 if ev else -1
                if ev:
                    self._event_sound(ev[0])
                else:
                    self.sfx("total")
        elif a["phase"] == "events":
            if a["clock"] >= 0.34:
                a["clock"] = 0.0
                a["i"] += 1
                if a["i"] >= len(ev):
                    a["i"] = len(ev) - 1
                    a["phase"] = "total"
                    self.sfx("total")
                else:
                    self._event_sound(ev[a["i"]])
        elif a["phase"] == "total" and a["clock"] >= 1.1:
            self.anim = None
            self.run.after_play()
            if self.run.stage == "cashout":
                self.sfx("win")
            elif self.run.stage == "over":
                self.sfx("lose")
            self._after_change()

    def _event_sound(self, e):
        kind = e["kind"]
        if kind == "chips":
            self.audio.chips(self.anim["chips_n"])          # (climbing the scale as the hand scores)
            self.anim["chips_n"] += 1
        elif kind in ("mult", "xmult", "money"):
            self.sfx(kind)
        elif e["text"] == "Broken!":
            self.sfx("glass")
        elif e["text"] in ("Debuffed", "Not allowed!"):
            self.sfx("nope")
        else:
            self.sfx("joker")

    def _after_change(self):
        run = self.run
        if run.stage == "over" and not self.recorded:
            self.recorded = True
            self._record()
        if run.won and not self.recorded:
            self.recorded = True
            self._record(won=True)
        self.sel = [i for i in self.sel if run.rnd and any(c["id"] == i for c in run.rnd.hand)]
        self._save()

    # ---- painting ----
    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.setRenderHint(QPainter.TextAntialiasing)
        self.hits, self.drags, self.tips, self.anchors = [], [], [], {}
        self.seen = set()
        self._background(p)
        if self.screen == "title" or self.run is None:
            self._draw_title(p)
        else:
            self._draw_game(p)
        self._draw_toast(p)
        self._draw_tip(p)
        p.end()
        for key in [k for k in self.pos if k not in self.seen]:
            del self.pos[key]
            self.targets.pop(key, None)

    def _background(self, p):
        a, b = "#DE443B", "#006BB4"
        run = self.run
        if self.screen != "title" and run:
            if run.rnd:
                if run.rnd.kind == "boss":
                    a, b = run.boss_info(run.rnd.boss)[0], "#1D2B30"
                elif run.rnd.kind == "big":
                    a, b = "#D08B1A", "#1E5F7A"
                else:
                    a, b = "#2E6DA4", "#3A8F7A"
            elif run.stage == "shop":
                a, b = "#C2453B", "#6B3E8C"
            elif run.stage == "pack" and run.pack:
                a, b = PACKS[run.pack["kind"]][1], "#1D2B30"
        p.drawImage(QRectF(self.rect()), self.swirl.frame(self.t, a, b))
        p.fillRect(self.rect(), QColor(0, 0, 0, 55))

    def _layout(self):
        w, h = self.width(), self.height()
        x0, x1 = SIDE + 30, w - 18
        span = x1 - x0
        hand_y = h - CH - 88
        return {"w": w, "h": h, "x0": x0, "x1": x1,
                "jokers": QRectF(x0 + 8, 22, span * 0.64 - 16, JH),
                "cons": QRectF(x0 + span * 0.69, 22, span * 0.31 - 8, JH),
                "mid": QRectF(x0, JH + 62, span, h - JH - 62 - 14),
                "play_y": (JH + 62 + hand_y) / 2 - CH / 2 - 6,
                "hand": QRectF(x0, hand_y, span - 118, CH),
                "deck": QRectF(x1 - 96, hand_y + 6, CW, CH)}

    def _draw_game(self, p):
        run = self.run
        L = self._layout()
        self._draw_side(p, L)
        st = run.stage
        if st == "blind":
            self._draw_blinds(p, L)
        elif st in ("round", "over") and run.rnd:
            self._draw_round(p, L)
        elif st == "cashout":
            self._draw_cashout(p, L)
        elif st == "shop":
            self._draw_shop(p, L)
        elif st == "pack" and run.pack:
            self._draw_pack(p, L)
        self._draw_jokers(p, L)
        self._draw_consumables(p, L)
        self._draw_popup(p)
        if st == "over":
            self._modal()
            self._draw_over(p, L)
        elif run.won and st == "cashout":
            self._modal()
            self._draw_win(p, L)
        elif self.overlay == "info":
            self._modal()
            self._draw_info(p, L)
        elif self.overlay == "deck":
            self._modal()
            self._draw_deck(p, L)

    def _modal(self):
        self.hits, self.drags, self.tips = [], [], []

    def _btn(self, p, rect, label, colour, action, enabled=True, size=16):
        hover = enabled and rect.contains(self.mouse)
        c = QColor(colour) if enabled else QColor("#4A5558")
        p.setPen(Qt.NoPen)
        p.setBrush(c.darker(160))
        p.drawRoundedRect(rect.translated(0, 4), 8, 8)
        r2 = rect.translated(0, 2) if hover else rect
        p.setBrush(c.lighter(112) if hover else c)
        p.drawRoundedRect(r2, 8, 8)
        text(p, r2, label, size, "#FFFFFF" if enabled else "#9AA5A8", Qt.AlignCenter | Qt.TextWordWrap)
        if enabled and action:
            self.hits.append((rect, action))

    def _tip(self, rect, title, lines, colour="#3A5157"):
        self.tips.append((rect, title, [ln for ln in lines if ln], colour))

    # ---- the side panel ----
    def _draw_side(self, p, L):
        run = self.run
        r = run.rnd
        side = QRectF(12, 12, SIDE, L["h"] - 24)
        panel(p, side, "#162127", "#2C3E44", 14)
        x, w = 24, SIDE - 24
        y = 24
        box = QRectF(x, y, w, 112)
        st = run.stage
        if r:
            b = run.blinds()[min(2, run.blind)] if r.kind == "boss" else None
            colour = b["colour"] if b else ("#2E6DA4" if r.kind == "small" else "#D08B1A")
            panel(p, box, QColor(colour).darker(150).name(), colour, 10)
            text(p, QRectF(x, y + 6, w, 26), r.name, 21, "#FFFFFF")
            text(p, QRectF(x, y + 34, w, 16), "Score at least", 12, DIM, bold=False)
            text(p, QRectF(x, y + 50, w, 30), fmt(r.target), 26, MULT)
            text(p, QRectF(x, y + 82, w, 22), "Reward: " + "$" * r.reward, 14, MONEY)
            if r.boss:
                self._tip(box, r.boss, [run.boss_info(r.boss)[3]], colour)
        else:
            label = {"blind": "Choose your\nnext Blind", "shop": "Improve your run!", "cashout": "Cash Out",
                     "pack": pack_name(run.pack["kind"], run.pack["size"]) if run.pack else "",
                     "over": "Game Over"}.get(st, "")
            panel(p, box, "#2A1F2E" if st == "shop" else "#20323A", ORANGE if st == "shop" else "#3A5157", 10)
            text(p, box, label, 22, ORANGE if st == "shop" else "#FFFFFF", Qt.AlignCenter | Qt.TextWordWrap)
        y += 122
        score = r.score if r else 0
        if self.anim:
            a = self.anim
            k = min(1.0, a["clock"] / 0.6) if a["phase"] == "total" else 0.0
            score = a["from"] + (a["to"] - a["from"]) * k
        sb = QRectF(x, y, w, 46)
        panel(p, sb, "#1E2C30", "#2C3E44", 8)
        text(p, QRectF(x + 10, y, 80, 46), "Round\nscore", 12, DIM, Qt.AlignVCenter | Qt.AlignLeft, bold=False)
        text(p, QRectF(x + 76, y, w - 86, 46), fmt(score), 24, "#FFFFFF", Qt.AlignVCenter | Qt.AlignRight)
        y += 54
        # the hand being played (or previewed)
        name, level, chips, mult = "", None, 0, 0
        if self.anim:
            a = self.anim
            res = a["res"]
            name, level = res["hand"], res["level"]
            chips, mult = res["base"]
            if a["i"] >= 0:
                e = res["events"][a["i"]]
                chips, mult = e["chips"], e["mult"]
        elif r and self.sel:
            pv = run.preview([c for c in r.hand if c["id"] in self.sel])
            if pv:
                name, level, chips, mult = pv
        hb = QRectF(x, y, w, 100)
        panel(p, hb, "#1E2C30", "#2C3E44", 8)
        if name:
            text(p, QRectF(x, y + 6, w, 24), name, 18, "#FFFFFF")
            text(p, QRectF(x, y + 28, w, 16), f"lvl.{level}", 12, DIM)
        cb = QRectF(x + 10, y + 48, (w - 44) / 2, 42)
        mb = QRectF(cb.right() + 24, y + 48, (w - 44) / 2, 42)
        panel(p, cb, CHIPS, None, 7)
        panel(p, mb, MULT, None, 7)
        text(p, cb, fmt(chips), 22)
        text(p, mb, fmt_mult(mult), 22)
        text(p, QRectF(cb.right(), cb.y(), 24, 42), "X", 20, MULT)
        self.anchors[("hand",)] = QPointF(hb.center().x(), hb.y() + 44)
        y += 108
        # hands, discards, money, ante
        hands = r.hands if r else run.hands_base
        discards = r.discards if r else run.discards_base
        for k, (lab, val, col) in enumerate((("Hands", hands, CHIPS), ("Discards", discards, MULT))):
            bx = QRectF(x + k * (w / 2 + 3), y, w / 2 - 3, 56)
            panel(p, bx, "#1E2C30", "#2C3E44", 8)
            text(p, QRectF(bx.x(), bx.y() + 4, bx.width(), 16), lab, 12, DIM, bold=False)
            text(p, QRectF(bx.x(), bx.y() + 20, bx.width(), 32), str(val), 26, col)
        y += 62
        mbx = QRectF(x, y, w, 48)
        panel(p, mbx, "#1E2C30", "#2C3E44", 8)
        text(p, mbx, f"${run.money}" if run.money >= 0 else f"-${-run.money}", 28, MONEY)
        y += 54
        for k, (lab, val) in enumerate((("Ante", f"{run.ante}/8"), ("Round", str(run.round_no)))):
            bx = QRectF(x + k * (w / 2 + 3), y, w / 2 - 3, 56)
            panel(p, bx, "#1E2C30", "#2C3E44", 8)
            text(p, QRectF(bx.x(), bx.y() + 4, bx.width(), 16), lab, 12, DIM, bold=False)
            text(p, QRectF(bx.x(), bx.y() + 20, bx.width(), 32), val, 24, ORANGE)
        y += 64
        bh = min(38, (side.bottom() - y - 12) / 4 - 6)
        self._btn(p, QRectF(x, y, w, bh), "Run Info", "#D9473C", lambda: self._set_overlay("info"),
                  enabled=not self.anim)
        y += bh + 6
        self._btn(p, QRectF(x, y, w, bh), "Your Deck", "#2E6DA4", lambda: self._set_overlay("deck"),
                  enabled=not self.anim)
        y += bh + 6
        self._btn(p, QRectF(x, y, w / 2 - 3, bh), f"Speed x{self.speed}", "#5C6E73", self._cycle_speed, size=14)
        self._btn(p, QRectF(x + w / 2 + 3, y, w / 2 - 3, bh), "Main Menu", ORANGE, self._to_title,
                  enabled=not self.anim, size=14)
        y += bh + 6
        self._sound_buttons(p, QRectF(x, y, w, bh))

    def _sound_buttons(self, p, rect):
        w = rect.width() / 2 - 3
        self._btn(p, QRectF(rect.x(), rect.y(), w, rect.height()), "Music: On" if self.music_on else "Music: Off",
                  "#7A4FA8" if self.music_on else "#4A3A5A", self._toggle_music, size=14)
        self._btn(p, QRectF(rect.x() + w + 6, rect.y(), w, rect.height()),
                  "Sounds: On" if self.sfx_on else "Sounds: Off", "#7A4FA8" if self.sfx_on else "#4A3A5A",
                  self._toggle_sfx, size=14)

    # ---- jokers and consumables (always on show) ----
    def _row_xs(self, n, rect, w):
        if n == 0:
            return []
        span = rect.width() - w
        step = min(w + 10, span / max(1, n - 1))
        total = step * (n - 1) + w
        x = rect.x() + (rect.width() - total) / 2
        return [x + i * step for i in range(n)]

    def _draw_jokers(self, p, L):
        run = self.run
        rect = L["jokers"]
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 70))
        p.drawRoundedRect(rect.adjusted(-8, -8, 8, 8), 10, 10)
        text(p, QRectF(rect.right() - 60, rect.bottom() + 6, 66, 16), f"{len(run.jokers)}/{run.joker_slots}", 12,
             "#FFFFFF")
        xs = self._row_xs(len(run.jokers), rect, JW)
        dis = run.rnd.disabled if run.rnd else None
        hover = self._hover_index([QRectF(x, rect.y(), JW, JH) for x in xs])
        for i, j in enumerate(run.jokers):
            x, y = xs[i], rect.y() - (12 if self.jsel == i else 4 if hover == i else 0)
            if self.drag and self.drag["kind"] == "joker" and self.drag["i"] == i and self.drag["moved"]:
                x, y = self.mouse.x() - JW / 2, self.mouse.y() - JH / 2
                self.pos[("j", j["id"])] = [x, y]
            cx, cy = self._at(("j", j["id"]), x, y)
            r = QRectF(cx, cy, JW, JH)
            jig = self._jiggle(("joker", i))
            p.save()
            p.translate(r.center())
            p.scale(jig, jig)
            paint_joker(p, QRectF(-JW / 2, -JH / 2, JW, JH), j, self.t, disabled=j["id"] == dis)
            p.restore()
            self.anchors[("joker", i)] = QPointF(r.center().x(), r.y())
            emoji, rarity, _c, desc = JOKERS[j["k"]]
            self._tip(QRectF(xs[i], rect.y(), JW, JH), j["k"],
                      [desc, run.joker_status(j), RARITY[rarity][0],
                       f"{EDITIONS[j['ed']][0]}: {EDITIONS[j['ed']][1]}" if j["ed"] else "",
                       f"Sells for ${j['sell']}"], RARITY[rarity][1])
            self.drags.append((QRectF(xs[i], rect.y(), JW, JH), "joker", i))
            if self.jsel == i and not self.anim:
                self._btn(p, QRectF(r.x() + 2, r.bottom() + 6, JW - 4, 30), f"Sell ${j['sell']}", GREEN,
                          lambda i=i: self._sell_joker(i), size=13)

    def _draw_consumables(self, p, L):
        run = self.run
        rect = L["cons"]
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 70))
        p.drawRoundedRect(rect.adjusted(-8, -8, 8, 8), 10, 10)
        text(p, QRectF(rect.right() - 60, rect.bottom() + 6, 66, 16),
             f"{len(run.consumables)}/{run.cons_slots}", 12, "#FFFFFF")
        xs = self._row_xs(len(run.consumables), rect, JW)
        hover = self._hover_index([QRectF(x, rect.y(), JW, JH) for x in xs])
        for i, c in enumerate(run.consumables):
            y = rect.y() - (12 if self.csel == i else 4 if hover == i else 0)
            r = QRectF(xs[i], y, JW, JH)
            paint_consumable(p, r, c["type"], c["k"], self.t)
            self._tip(QRectF(xs[i], rect.y(), JW, JH), c["k"], self._cons_lines(c["type"], c["k"]),
                      "#7A4FA8" if c["type"] == "tarot" else "#2C5A9E")
            self.hits.append((QRectF(xs[i], rect.y(), JW, JH), lambda i=i: self._pick_cons(i)))
            if self.csel == i and not self.anim:
                ok = self._can_use(c)
                self._btn(p, QRectF(r.x() - 6, r.bottom() + 6, JW / 2 + 4, 30), "Use", MULT,
                          lambda i=i: self._use(i), enabled=ok, size=13)
                self._btn(p, QRectF(r.x() + JW / 2 + 2, r.bottom() + 6, JW / 2 + 4, 30), "Sell $1", GREEN,
                          lambda i=i: self._sell_cons(i), size=12)

    def _cons_lines(self, kind, name):
        if kind == "tarot":
            return [TAROTS[name][3], "Tarot"]
        hand = PLANETS[name]
        chips, mult, lc, lm = dict((h[0], h[1:]) for h in HANDS)[hand]
        lv = self.run.levels[hand] if self.run else 1
        return [f"Levels up {hand}", f"+{lc} Chips and +{lm} Mult", f"(currently level {lv})", "Planet"]

    def _hover_index(self, rects):
        hit = None
        for i, r in enumerate(rects):
            if r.contains(self.mouse):
                hit = i
        return hit

    def _jiggle(self, key):
        a = self.anim
        if not a or a["phase"] != "events" or a["i"] < 0:
            return 1.0
        e = a["res"]["events"][a["i"]]
        if tuple(e["at"]) != key:
            return 1.0
        return 1.0 + 0.14 * max(0.0, 1 - a["clock"] / 0.2)

    # ---- choosing a blind ----
    def _draw_blinds(self, p, L):
        run = self.run
        mid = L["mid"]
        blinds = run.blinds()
        pw = min(240, (mid.width() - 60) / 3)
        gap = 22
        x0 = mid.x() + (mid.width() - 3 * pw - 2 * gap) / 2
        for i, b in enumerate(blinds):
            current = i == run.blind
            rect = QRectF(x0 + i * (pw + gap), mid.y() + (8 if current else 44), pw, mid.height() - 52)
            colour = QColor(b["colour"])
            panel(p, rect, "#1B282C", b["colour"] if current else "#33464A", 12, 3 if current else 2)
            cx = rect.center().x()
            y = rect.y() + 14
            state = run.blind_state[i]
            if current:
                self._btn(p, QRectF(rect.x() + 18, y, pw - 36, 40), "Select", ORANGE, self._select_blind, size=18)
            else:
                lab = {"skipped": "Skipped", "beaten": "Defeated"}.get(state, "Upcoming")
                text(p, QRectF(rect.x(), y, pw, 40), lab, 18, DIM)
            y += 54
            text(p, QRectF(rect.x(), y, pw, 28), b["name"], 20, "#FFFFFF")
            y += 34
            g = QRadialGradient(QPointF(cx - 10, y + 30), 50)
            g.setColorAt(0, colour.lighter(140))
            g.setColorAt(1, colour.darker(130))
            p.setPen(QPen(colour.darker(170), 3))
            p.setBrush(g)
            p.drawEllipse(QPointF(cx, y + 36), 36, 36)
            initial = b["name"].replace("The ", "")[:1] if b["kind"] == "boss" else b["name"][0]
            text(p, QRectF(cx - 36, y, 72, 72), initial, 34, "#FFFFFF")
            y += 84
            if b["text"]:
                text(p, QRectF(rect.x() + 12, y, pw - 24, 44), b["text"], 13, "#E8E8E8",
                     Qt.AlignCenter | Qt.TextWordWrap, bold=False)
            y += 50
            sb = QRectF(rect.x() + 14, y, pw - 28, 66)
            panel(p, sb, "#24363B", None, 8)
            text(p, QRectF(sb.x(), sb.y() + 4, sb.width(), 16), "Score at least", 12, DIM, bold=False)
            text(p, QRectF(sb.x(), sb.y() + 20, sb.width(), 26), fmt(b["target"]), 23, MULT)
            text(p, QRectF(sb.x(), sb.y() + 46, sb.width(), 18), "Reward: " + "$" * b["reward"], 13, MONEY)
            y += 76
            if i < 2 and state == "":
                tag = run.skip_tags[i]
                tc = QPointF(rect.x() + 34, y + 24)
                paint_tag(p, tc, 18, tag)
                self._tip(QRectF(tc.x() - 18, tc.y() - 18, 36, 36), tag, [TAGS[tag][1]], "#2C3E44")
                if current:
                    self._btn(p, QRectF(rect.x() + 62, y + 6, pw - 78, 38), "Skip Blind", MULT,
                              self._skip_blind, size=15)
                else:
                    text(p, QRectF(rect.x() + 62, y + 6, pw - 78, 38), "or skip for a tag", 12, DIM, bold=False)
            if not current:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(10, 16, 18, 90))
                p.drawRoundedRect(rect, 12, 12)

    # ---- a round ----
    def _hand_slots(self, n, rect):
        if n == 0:
            return []
        span = rect.width() - CW
        step = min(CW + 6, span / max(1, n - 1))
        total = step * (n - 1) + CW
        x = rect.x() + (rect.width() - total) / 2
        mid = (n - 1) / 2
        return [(x + i * step, rect.y() + abs(i - mid) ** 2 * 1.6, (i - mid) * 1.8) for i in range(n)]

    def _draw_cards_in_hand(self, p, cards, rect, sel, kind, spawn):
        run = self.run
        slots = self._hand_slots(len(cards), rect)
        hover = None
        if not self.anim:
            hover = self._hover_index([QRectF(x, y - (28 if c["id"] in sel else 0), CW, CH)
                                       for (x, y, _a), c in zip(slots, cards)])
        for i, c in enumerate(cards):
            x, y, ang = slots[i]
            if c["id"] in sel:
                y -= 28
            elif hover == i:
                y -= 8
            dragged = self.drag and self.drag["kind"] == kind and self.drag["i"] == i and self.drag["moved"]
            if dragged:
                x, y, ang = self.mouse.x() - CW / 2, self.mouse.y() - CH / 2, 0
                self.pos[("c", c["id"])] = [x, y]
            cx, cy = self._at(("c", c["id"]), x, y, spawn)
            jig = self._jiggle(("held", i)) if kind == "hand" else 1.0
            p.save()
            p.translate(cx + CW / 2, cy + CH / 2)
            p.rotate(ang)
            p.scale(jig, jig)
            paint_card(p, QRectF(-CW / 2, -CH / 2, CW, CH), c, self.t, debuffed=run.debuffed(c))
            p.restore()
            hit = QRectF(slots[i][0], slots[i][1] - (28 if c["id"] in sel else 0), CW, CH)
            self.anchors[("held", i)] = QPointF(cx + CW / 2, cy)
            self._tip(hit, self._card_title(c), self._card_lines(c), SUIT_COLOUR[c["s"]])
            self.drags.append((hit, kind, i))

    def _card_title(self, c):
        if c["enh"] == "stone":
            return "Stone Card"
        return f"{rank_name(c['r'])} of {SUIT_NAME[c['s']]}"

    def _card_lines(self, c):
        lines = []
        if c["enh"] != "stone":
            lines.append(f"+{rank_chips(c['r']) + c['bonus']} Chips")
        elif c["bonus"]:
            lines.append(f"+{50 + c['bonus']} Chips")
        if c["enh"]:
            lines.append(f"{ENHANCEMENTS[c['enh']][0]}: {ENHANCEMENTS[c['enh']][1]}")
        if c["ed"]:
            lines.append(f"{EDITIONS[c['ed']][0]}: {EDITIONS[c['ed']][1]}")
        if self.run.debuffed(c):
            lines.append("Debuffed by the boss: it won't score")
        return lines

    def _draw_round(self, p, L):
        run = self.run
        r = run.rnd
        mid = L["mid"]
        if r.boss:
            text(p, QRectF(mid.x(), mid.y() - 2, mid.width(), 20), f"{r.boss}: {run.boss_info(r.boss)[3]}", 13,
                 run.boss_info(r.boss)[0], bold=True)
        deck_r = L["deck"]
        spawn = (deck_r.x(), deck_r.y())
        # the played hand
        if r.played:
            n = len(r.played)
            step = CW + 14
            x0 = mid.center().x() - (step * n - 14) / 2
            scoring = set(self.anim["res"]["scoring"]) if self.anim else set()
            lifted = self.anim and self.anim["phase"] != "lift"
            for i, c in enumerate(r.played):
                y = L["play_y"] - (20 if lifted and c["id"] in scoring else 0)
                cx, cy = self._at(("c", c["id"]), x0 + i * step, y, spawn)
                jig = self._jiggle(("played", i))
                p.save()
                p.translate(cx + CW / 2, cy + CH / 2)
                p.scale(jig, jig)
                paint_card(p, QRectF(-CW / 2, -CH / 2, CW, CH), c, self.t, debuffed=run.debuffed(c))
                p.restore()
                self.anchors[("played", i)] = QPointF(cx + CW / 2, cy)
            a = self.anim
            if a and a["phase"] == "total":
                res = a["res"]
                k = min(1.0, a["clock"] / 0.25)
                text(p, QRectF(mid.x(), L["play_y"] - 74, mid.width(), 50), fmt(res["total"]), 26 + 14 * k,
                     ORANGE if res["total"] else DIM)
        # the hand
        self._draw_cards_in_hand(p, r.hand, L["hand"], self.sel, "hand", spawn)
        text(p, QRectF(L["hand"].right() - 70, L["hand"].bottom() + 8, 70, 18),
             f"{len(r.hand)}/{r.hand_size}", 13, "#FFFFFF")
        # the deck
        dr = L["deck"]
        for k in range(min(4, max(1, len(r.draw) // 12 + 1))):
            paint_back(p, dr.translated(-k * 1.5, -k * 1.5), DECKS[run.deck_name][0])
        text(p, QRectF(dr.x() - 10, dr.bottom() + 4, dr.width() + 20, 18), f"{len(r.draw)}/{len(run.deck)}", 13,
             "#FFFFFF")
        self.hits.append((dr, lambda: self._set_overlay("deck")))
        # the buttons
        if run.stage == "round":
            busy = bool(self.anim)
            n = len(self.sel)
            by = L["h"] - 58
            cx = L["hand"].center().x()
            self._btn(p, QRectF(cx - 260, by, 150, 44), "Play Hand", CHIPS, self._play,
                      enabled=not busy and 1 <= n <= 5)
            self._btn(p, QRectF(cx - 94, by + 4, 88, 36), "Rank", ORANGE, lambda: self._sort("rank"),
                      enabled=not busy, size=14)
            self._btn(p, QRectF(cx + 6, by + 4, 88, 36), "Suit", ORANGE, lambda: self._sort("suit"),
                      enabled=not busy, size=14)
            text(p, QRectF(cx - 94, by - 18, 188, 16), "Sort hand", 11, DIM, bold=False)
            self._btn(p, QRectF(cx + 110, by, 150, 44), "Discard", MULT, self._discard,
                      enabled=not busy and 1 <= n <= 5 and r.discards > 0)

    def _draw_popup(self, p):
        a = self.anim
        if not a or a["phase"] != "events" or a["i"] < 0:
            return
        e = a["res"]["events"][a["i"]]
        at = self.anchors.get(tuple(e["at"]))
        if at is None:
            return
        colour = {"chips": CHIPS, "mult": MULT, "xmult": MULT, "money": MONEY}.get(e["kind"], ORANGE)
        s = 1 + 0.35 * max(0.0, 1 - a["clock"] / 0.12)
        fm = QFontMetrics(font(16))
        w = fm.horizontalAdvance(e["text"]) + 18
        p.save()
        p.translate(at.x(), at.y() - 20)
        p.scale(s, s)
        r = QRectF(-w / 2, -15, w, 30)
        panel(p, r, colour, "#FFFFFF" if e["kind"] == "xmult" else None, 8, 2)
        text(p, r, e["text"], 16)
        p.restore()

    # ---- cashing out ----
    def _draw_cashout(self, p, L):
        run = self.run
        mid = L["mid"]
        rect = QRectF(mid.center().x() - 240, mid.y() + 14, 480, min(mid.height() - 28, 470))
        panel(p, rect, "#1B282C", "#3A5157", 12)
        self._btn(p, QRectF(rect.x() + 30, rect.y() + 22, rect.width() - 60, 56),
                  f"Cash Out: ${run.cash_total()}", ORANGE, self._cash_out, enabled=not run.won, size=22)
        y = rect.y() + 98
        for label, amount in run.cash:
            text(p, QRectF(rect.x() + 30, y, rect.width() - 160, 28), label, 15, "#FFFFFF",
                 Qt.AlignVCenter | Qt.AlignLeft)
            text(p, QRectF(rect.right() - 160, y, 130, 28), "$" * amount if amount <= 8 else f"${amount}", 17,
                 MONEY, Qt.AlignVCenter | Qt.AlignRight)
            y += 34
            p.setPen(QPen(QColor(255, 255, 255, 30), 1))
            p.drawLine(QPointF(rect.x() + 30, y - 4), QPointF(rect.right() - 30, y - 4))
        for note in run.notes:
            y += 6
            text(p, QRectF(rect.x() + 30, y, rect.width() - 60, 26), note, 15, ORANGE)
            y += 28

    # ---- the shop ----
    def _shop_item(self, p, r, item):
        t = item["type"]
        if t == "joker":
            paint_joker(p, r, item["item"], self.t)
            j = item["item"]
            emoji, rarity, _c, desc = JOKERS[j["k"]]
            self._tip(r, j["k"], [desc, RARITY[rarity][0],
                                  f"{EDITIONS[j['ed']][0]}: {EDITIONS[j['ed']][1]}" if j["ed"] else ""],
                      RARITY[rarity][1])
        elif t in ("tarot", "planet"):
            paint_consumable(p, r, t, item["item"], self.t)
            self._tip(r, item["item"], self._cons_lines(t, item["item"]),
                      "#7A4FA8" if t == "tarot" else "#2C5A9E")
        elif t == "pack":
            paint_pack(p, r, item["kind"], item["size"])
            _p, _price, n, picks = PACK_SIZES[item["size"]]
            if item["kind"] == "Buffoon":
                n = 2 if item["size"] == "normal" else 4
            self._tip(r, pack_name(item["kind"], item["size"]),
                      [f"Choose {picks} of {n} {PACKS[item['kind']][2]}"], PACKS[item["kind"]][1])
        elif t == "voucher":
            paint_voucher(p, r, item["item"])
            self._tip(r, item["item"], [VOUCHERS[item["item"]][1], "Voucher"], "#B8862C")

    def _price_tag(self, p, r, price):
        tag = QRectF(r.center().x() - 26, r.y() - 28, 52, 24)
        panel(p, tag, "#2A2214", MONEY, 7, 1.5)
        text(p, tag, f"${price}" if price else "Free", 14, MONEY)

    def _draw_shop(self, p, L):
        run = self.run
        s = run.shop
        mid = L["mid"]
        rect = QRectF(mid.x() + 10, mid.y() + 6, mid.width() - 20, min(mid.height() - 12, 470))
        panel(p, rect, "#1B2226", MULT, 14, 2.5)
        bx = rect.x() + 18
        self._btn(p, QRectF(bx, rect.y() + 22, 150, 74), "Next\nRound", MULT, self._next_round, size=19)
        reroll = "Reroll\nFree" if s["free"] else f"Reroll\n${s['reroll']}"
        self._btn(p, QRectF(bx, rect.y() + 108, 150, 74), reroll, GREEN, self._reroll, size=19)
        x0 = rect.x() + 200
        y1 = rect.y() + 52
        for i, item in enumerate(s["cards"]):
            r = QRectF(x0 + i * 112, y1, JW, JH)
            if item is None:
                p.setPen(QPen(QColor(255, 255, 255, 40), 1.5, Qt.DashLine))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(r, 7, 7)
                continue
            self._shop_item(p, r, item)
            self._price_tag(p, r, item["price"])
            self._btn(p, QRectF(r.x() + 4, r.bottom() + 8, JW - 8, 30), "Buy", CHIPS,
                      lambda i=i: self._buy("cards", i), size=14)
        y2 = y1 + JH + 92
        text(p, QRectF(x0 - 10, y2 - 50, 100, 18), "Voucher", 12, DIM, bold=False)
        v = s["voucher"]
        vr = QRectF(x0, y2, JW, JH)
        if v:
            self._shop_item(p, vr, v)
            self._price_tag(p, vr, v["price"])
            self._btn(p, QRectF(vr.x() + 4, vr.bottom() + 8, JW - 8, 30), "Redeem", CHIPS,
                      lambda: self._buy("voucher"), size=13)
        else:
            p.setPen(QPen(QColor(255, 255, 255, 40), 1.5, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(vr, 7, 7)
        text(p, QRectF(x0 + 150, y2 - 50, 200, 18), "Booster Packs", 12, DIM, bold=False)
        for i, item in enumerate(s["packs"]):
            r = QRectF(x0 + 150 + i * 112, y2, JW, JH)
            if item is None:
                continue
            self._shop_item(p, r, item)
            self._price_tag(p, r, item["price"])
            self._btn(p, QRectF(r.x() + 4, r.bottom() + 8, JW - 8, 30), "Open", CHIPS,
                      lambda i=i: self._buy("packs", i), size=14)

    # ---- an open booster pack ----
    def _draw_pack(self, p, L):
        run = self.run
        pk = run.pack
        mid = L["mid"]
        title = pack_name(pk["kind"], pk["size"])
        text(p, QRectF(mid.x(), mid.y(), mid.width(), 30), title, 24, "#FFFFFF")
        text(p, QRectF(mid.x(), mid.y() + 30, mid.width(), 20),
             f"Choose {pk['picks']}" + ("  -  select cards in your hand first, if the card asks for them"
                                         if pk["kind"] == "Arcana" else ""), 13, DIM, bold=False)
        n = len(pk["choices"])
        w = CW if pk["kind"] == "Standard" else JW
        h = CH if pk["kind"] == "Standard" else JH
        step = w + 34
        x0 = mid.center().x() - (step * n - 34) / 2
        y = mid.y() + 70
        hand = run.pack_hand()
        sel = [c for c in hand if c["id"] in self.psel]
        for i, ch in enumerate(pk["choices"]):
            r = QRectF(x0 + i * step, y, w, h)
            t = ch["type"]
            if t == "card":
                paint_card(p, r, ch["item"], self.t)
                self._tip(r, self._card_title(ch["item"]), self._card_lines(ch["item"]),
                          SUIT_COLOUR[ch["item"]["s"]])
                label = "Take"
            elif t == "joker":
                self._shop_item(p, r, {"type": "joker", "item": ch["item"]})
                label = "Take"
            else:
                self._shop_item(p, r, {"type": t, "item": ch["item"]})
                label = "Use"
            ok = True
            if t == "tarot":
                lo, hi = TAROTS[ch["item"]][1:3]
                ok = not lo or lo <= len(sel) <= hi
            self._btn(p, QRectF(r.x() + 2, r.bottom() + 10, w - 4, 32), label, MULT if label == "Use" else CHIPS,
                      lambda i=i: self._pack_pick(i), enabled=ok, size=14)
        self._btn(p, QRectF(mid.right() - 130, y + h / 2 - 22, 110, 44), "Skip", "#5C6E73", self._skip_pack)
        if hand:
            self._draw_cards_in_hand(p, hand, L["hand"], self.psel, "phand", (L["deck"].x(), L["deck"].y()))

    # ---- overlays ----
    def _overlay_panel(self, p, L, w, h, title, colour="#FFFFFF"):
        p.fillRect(self.rect(), QColor(0, 0, 0, 140))
        rect = QRectF((L["w"] - w) / 2, (L["h"] - h) / 2, w, h)
        panel(p, rect, "#17232A", "#3A5157", 14, 2.5)
        text(p, QRectF(rect.x(), rect.y() + 14, rect.width(), 40), title, 30, colour)
        return rect

    def _draw_info(self, p, L):
        run = self.run
        rect = self._overlay_panel(p, L, 640, min(L["h"] - 40, 640), "Run Info")
        y = rect.y() + 66
        rows = [h for h in HANDS if h[0] not in SECRET or run.played[h[0]] > 0]
        rh = min(34, (rect.height() - 190) / max(1, len(rows)))
        for name, *_v in rows:
            chips, mult = run.hand_value(name)
            lv = QRectF(rect.x() + 26, y + 3, 58, rh - 6)
            panel(p, lv, "#33464A", None, 6)
            text(p, lv, f"lvl.{run.levels[name]}", 13)
            text(p, QRectF(rect.x() + 98, y, 220, rh), name, 16, "#FFFFFF", Qt.AlignVCenter | Qt.AlignLeft)
            cb = QRectF(rect.x() + 330, y + 3, 92, rh - 6)
            mb = QRectF(rect.x() + 446, y + 3, 72, rh - 6)
            panel(p, cb, CHIPS, None, 6)
            panel(p, mb, MULT, None, 6)
            text(p, cb, fmt(chips), 15)
            text(p, mb, fmt(mult), 15)
            text(p, QRectF(cb.right(), y, 24, rh), "X", 14, MULT)
            text(p, QRectF(rect.x() + 528, y, 90, rh), f"# {run.played[name]}", 14, ORANGE)
            y += rh
        y += 10
        text(p, QRectF(rect.x() + 26, y, rect.width() - 52, 20),
             "Vouchers: " + (", ".join(run.vouchers) if run.vouchers else "none yet"), 13, DIM,
             Qt.AlignLeft | Qt.TextWordWrap, bold=False)
        text(p, QRectF(rect.x() + 26, y + 22, rect.width() - 52, 20),
             f"{run.deck_name}  -  best hand {fmt(run.best_hand)}  -  seed {run.seed}", 13, DIM, Qt.AlignLeft,
             bold=False)
        self._btn(p, QRectF(rect.center().x() - 80, rect.bottom() - 56, 160, 42), "Back", ORANGE,
                  lambda: self._set_overlay(None))

    def _draw_deck(self, p, L):
        run = self.run
        rect = self._overlay_panel(p, L, min(L["w"] - 40, 1040), min(L["h"] - 40, 600), "Your Deck")
        left = {c["id"] for c in run.rnd.draw} if run.rnd else None
        order = {s: i for i, s in enumerate(SUITS)}
        rows = {s: [] for s in SUITS}
        for c in sorted(run.deck, key=lambda c: (-(0 if c["enh"] == "stone" else c["r"]), order[c["s"]])):
            rows[c["s"]].append(c)
        sc = 0.62
        y = rect.y() + 70
        rh = (rect.height() - 150) / 4
        for s in SUITS:
            cards = rows[s]
            text(p, QRectF(rect.x() + 14, y, 40, rh), SUIT_SYMBOL[s], 30, SUIT_COLOUR[s], family=SYMBOL)
            area = QRectF(rect.x() + 60, y, rect.width() - 90, rh)
            n = len(cards)
            step = min(CW * sc + 6, (area.width() - CW * sc) / max(1, n - 1)) if n else 0
            for i, c in enumerate(cards):
                x = area.x() + i * step
                p.save()
                p.translate(x, y + 4)
                p.scale(sc, sc)
                if left is not None and c["id"] not in left:
                    p.setOpacity(0.35)
                paint_card(p, QRectF(0, 0, CW, CH), c, self.t)
                p.restore()
                self._tip(QRectF(x, y + 4, min(step, CW * sc), CH * sc), self._card_title(c), self._card_lines(c),
                          SUIT_COLOUR[s])
            y += rh
        note = f"{len(run.deck)} cards" + (f"  -  {len(left)} left to draw (the faded ones are out)"
                                           if left is not None else "")
        text(p, QRectF(rect.x(), rect.bottom() - 82, rect.width(), 20), note, 13, DIM, bold=False)
        self._btn(p, QRectF(rect.center().x() - 80, rect.bottom() - 56, 160, 42), "Back", ORANGE,
                  lambda: self._set_overlay(None))

    def _draw_over(self, p, L):
        run = self.run
        rect = self._overlay_panel(p, L, 460, 400, "Game Over", MULT)
        most = run.most_played()
        lines = [("Best hand", fmt(run.best_hand)), ("Most played hand", most or "-"),
                 ("Ante reached", str(run.ante)), ("Rounds", str(run.round_no)), ("Seed", str(run.seed))]
        y = rect.y() + 80
        for lab, val in lines:
            text(p, QRectF(rect.x() + 40, y, 200, 30), lab, 16, DIM, Qt.AlignVCenter | Qt.AlignLeft, bold=False)
            text(p, QRectF(rect.x() + 200, y, rect.width() - 240, 30), val, 18, "#FFFFFF",
                 Qt.AlignVCenter | Qt.AlignRight)
            y += 38
        self._btn(p, QRectF(rect.x() + 40, rect.bottom() - 70, 170, 48), "New Run", CHIPS, self._new_run)
        self._btn(p, QRectF(rect.right() - 210, rect.bottom() - 70, 170, 48), "Main Menu", ORANGE,
                  self._abandon)

    def _draw_win(self, p, L):
        run = self.run
        rect = self._overlay_panel(p, L, 500, 330, "You Win!", MONEY)
        text(p, QRectF(rect.x() + 30, rect.y() + 70, rect.width() - 60, 110),
             f"You beat Ante 8 with the {run.deck_name}.\nBest hand: {fmt(run.best_hand)}\n\n"
             "Keep going in endless mode - the blinds get very big.", 15, "#FFFFFF",
             Qt.AlignCenter | Qt.TextWordWrap, bold=False)
        self._btn(p, QRectF(rect.x() + 40, rect.bottom() - 70, 190, 48), "Endless Mode", CHIPS, self._endless)
        self._btn(p, QRectF(rect.right() - 230, rect.bottom() - 70, 190, 48), "Main Menu", ORANGE, self._abandon)

    def _draw_toast(self, p):
        if not self.toast:
            return
        msg = self.toast[0]
        fm = QFontMetrics(font(16))
        w = fm.horizontalAdvance(msg) + 40
        r = QRectF((self.width() + SIDE) / 2 - w / 2, 150, w, 40)
        panel(p, r, "#1E2C30", ORANGE, 10, 2)
        text(p, r, msg, 16)

    def _draw_tip(self, p):
        if self.drag and self.drag["moved"]:
            return
        tip = None
        for t in self.tips:
            if t[0].contains(self.mouse):
                tip = t
        if tip is None:
            return
        rect, title, lines, colour = tip
        w = 250
        fm_body = QFontMetrics(font(13, False))
        body = "\n".join(lines)
        bh = fm_body.boundingRect(QRect(0, 0, w - 24, 1000), Qt.TextWordWrap, body).height() if body else 0
        h = 40 + bh + (10 if body else 0)
        x = min(max(8, rect.center().x() - w / 2), self.width() - w - 8)
        y = rect.y() - h - 10
        if y < 8:
            y = rect.bottom() + 10
        y = min(y, self.height() - h - 8)
        box = QRectF(x, y, w, h)
        panel(p, box, "#F4F1EA", colour, 10, 3)
        hdr = QRectF(x + 3, y + 3, w - 6, 32)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(colour))
        p.drawRoundedRect(hdr, 8, 8)
        text(p, hdr, title, 15)
        if body:
            text(p, QRectF(x + 12, y + 40, w - 24, bh + 4), body, 13, "#2A2A2A",
                 Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, bold=False, shadow=False)

    # ---- the title ----
    def _draw_title(self, p):
        w, h = self.width(), self.height()
        word = "CLAUDEATRO"
        size = 78
        fm = QFontMetrics(font(size, family="Arial Black"))
        total = fm.horizontalAdvance(word)
        x = w / 2 - total / 2
        for i, ch in enumerate(word):
            cw = fm.horizontalAdvance(ch)
            bob = math.sin(self.t * 2.2 + i * 0.55) * 7
            col = (MULT, "#FFFFFF", CHIPS)[i % 3]
            p.save()
            p.translate(x + cw / 2, h * 0.2 + bob)
            p.rotate(math.sin(self.t * 1.7 + i) * 3)
            text(p, QRectF(-cw, -60, cw * 2, 120), ch, size, col, family="Arial Black")
            p.restore()
            x += cw
        # a fan of cards
        cards = [{"r": 14, "s": "S", "enh": None, "ed": None, "bonus": 0, "id": 1},
                 {"r": 13, "s": "H", "enh": None, "ed": "holo", "bonus": 0, "id": 2},
                 {"r": 12, "s": "D", "enh": "gold", "ed": None, "bonus": 0, "id": 3},
                 {"r": 11, "s": "C", "enh": None, "ed": "foil", "bonus": 0, "id": 4}]
        for i, c in enumerate(cards):
            p.save()
            p.translate(w / 2 + (i - 1.5) * 52, h * 0.44 + abs(i - 1.5) * 8)
            p.rotate((i - 1.5) * 9 + math.sin(self.t + i) * 2)
            paint_card(p, QRectF(-CW / 2, -CH / 2, CW, CH), c, self.t)
            p.restore()
        p.save()
        p.translate(w / 2, h * 0.44 - 20)
        p.rotate(math.sin(self.t * 0.8) * 4)
        paint_joker(p, QRectF(-JW / 2, -JH / 2 - 30, JW, JH), {"k": "Joker", "ed": "poly", "id": 9}, self.t)
        p.restore()
        # the deck to play with
        box = QRectF(w / 2 - 260, h * 0.6, 520, 104)
        panel(p, box, "#17232A", "#3A5157", 12)
        colour, desc = DECKS[self.deck_choice]
        paint_back(p, QRectF(box.x() + 74, box.y() + 12, 58, 80), colour)
        text(p, QRectF(box.x() + 146, box.y() + 14, box.width() - 210, 28), self.deck_choice, 20, "#FFFFFF",
             Qt.AlignLeft | Qt.AlignVCenter)
        text(p, QRectF(box.x() + 146, box.y() + 44, box.width() - 210, 50), desc, 13, DIM,
             Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, bold=False)
        self._btn(p, QRectF(box.x() + 12, box.y() + 30, 44, 44), "<", MULT, lambda: self._next_deck(-1), size=20)
        self._btn(p, QRectF(box.right() - 56, box.y() + 30, 44, 44), ">", MULT, lambda: self._next_deck(1), size=20)
        by = box.bottom() + 22
        if self.run is not None:
            self._btn(p, QRectF(w / 2 - 230, by, 210, 54), "Continue", ORANGE, self._continue, size=20)
            self._btn(p, QRectF(w / 2 + 20, by, 210, 54), "New Run", CHIPS, self._new_run, size=20)
            text(p, QRectF(0, by + 60, w, 18), "(a new run replaces the one you're in the middle of)", 12, DIM,
                 bold=False)
        else:
            self._btn(p, QRectF(w / 2 - 105, by, 210, 54), "Play", CHIPS, self._new_run, size=22)
        s = self.stats
        line = (f"Best hand {fmt(s.get('best_hand', 0))}   -   Highest ante {s.get('highest_ante', 0)}   -   "
                f"Wins {s.get('wins', 0)}   -   Runs lost {s.get('runs', 0)}")
        text(p, QRectF(0, h - 40, w, 20), line, 13, "#E8E8E8", bold=False)
        self._sound_buttons(p, QRectF(w - 270, h - 54, 250, 38))

    # ---- actions ----
    def _next_deck(self, d):
        names = list(DECKS)
        self.deck_choice = names[(names.index(self.deck_choice) + d) % len(names)]
        self._save_settings()

    def _new_run(self):
        self.run = Run(self.deck_choice)
        self.screen = "game"
        self.recorded = False
        self.sel, self.psel, self.jsel, self.csel, self.overlay = [], [], None, None, None
        self.pos.clear()
        self._save()

    def _continue(self):
        self.screen = "game"
        self.recorded = self.run.stage == "over"

    def _abandon(self):
        self._write("run.json", None)
        self.run = None
        self.screen = "title"
        self.overlay = None

    def _to_title(self):
        self._save()
        self.screen = "title"
        self.overlay = None

    def _endless(self):
        self.run.won = False
        self.run.endless = True
        self._save()

    def _toggle_music(self):
        self.music_on = not self.music_on
        self.audio.music_on = self.music_on
        self._save_settings()

    def _toggle_sfx(self):
        self.sfx_on = not self.sfx_on
        self.audio.sfx_on = self.sfx_on
        self._save_settings()

    def _cycle_speed(self):
        self.speed = SPEEDS[(SPEEDS.index(self.speed) + 1) % len(SPEEDS)]
        self._save_settings()

    def _set_overlay(self, which):
        self.overlay = which

    def _select_blind(self):
        self.sfx("blind")
        self.run.select_blind()
        self.sel = []
        self._save()

    def _skip_blind(self):
        self.sfx("joker")
        self.say(self.run.skip_blind())
        self._save()

    def _selected(self):
        r = self.run.rnd
        return [i for i, c in enumerate(r.hand) if c["id"] in self.sel]

    def _play(self):
        run = self.run
        r = run.rnd
        res = run.play(self._selected())
        if not res:
            return
        self.sel = []
        self.jsel = self.csel = None
        self.anim = {"res": res, "i": -1, "clock": 0.0, "phase": "lift", "from": r.score - res["total"],
                     "to": r.score, "chips_n": 0}
        self.sfx("play")

    def _discard(self):
        if self.run.discard(self._selected()):
            self.sfx("discard")
            self.sel = []
            self._after_change()

    def _sort(self, mode):
        self.sfx("reroll")
        self.run.sort_hand(mode)

    def _cash_out(self):
        self.sfx("cashout")
        self.run.collect()
        self._save()

    def _buy(self, where, i=0):
        err = self.run.buy(where, i)
        self.say(err)
        self.sfx("nope" if err else "pack" if self.run.stage == "pack" else "buy")
        self.psel = []
        self._save()

    def _reroll(self):
        err = self.run.reroll()
        self.sfx("nope" if err else "reroll")
        self.say(err)
        self._save()

    def _next_round(self):
        self.run.next_round()
        self.jsel = self.csel = None
        self._save()

    def _pack_pick(self, i):
        run = self.run
        sel = [c for c in run.pack_hand() if c["id"] in self.psel]
        kind = run.pack["choices"][i]["type"]
        ok, msg = run.pack_pick(i, sel)
        self.sfx({"tarot": "tarot", "planet": "planet", "joker": "joker"}.get(kind, "buy") if ok else "nope")
        self.say(msg)
        if ok:
            self.psel = []
        self._save()

    def _skip_pack(self):
        self.run.close_pack()
        self.psel = []
        self._save()

    def _sell_joker(self, i):
        self.sfx("sell")
        j = self.run.sell_joker(i)
        self.say(f"Sold {j['k']} for ${j['sell']}")
        self.jsel = None
        self._save()

    def _sell_cons(self, i):
        self.sfx("sell")
        self.run.sell_consumable(i)
        self.csel = None
        self._save()

    def _pick_cons(self, i):
        if self.anim:
            return
        self.csel = None if self.csel == i else i
        self.jsel = None

    def _use_targets(self):
        run = self.run
        if run.stage == "round" and run.rnd:
            return [c for c in run.rnd.hand if c["id"] in self.sel]
        if run.stage == "pack":
            return [c for c in run.pack_hand() if c["id"] in self.psel]
        return []

    def _can_use(self, c):
        if self.anim:
            return False
        if c["type"] == "planet":
            return True
        lo, hi = TAROTS[c["k"]][1:3]
        return not lo or lo <= len(self._use_targets()) <= hi

    def _use(self, i):
        run = self.run
        kind = run.consumables[i]["type"]
        ok, msg = run.use_consumable(i, self._use_targets())
        self.sfx(kind if ok else "nope")
        self.say(msg)
        if ok:
            self.csel = None
            if run.rnd:
                ids = {c["id"] for c in run.rnd.hand}
                self.sel = [x for x in self.sel if x in ids]
                if run.rnd.sort:
                    run.sort_hand()
            self.psel = []
        self._save()

    # ---- input ----
    def mouseMoveEvent(self, e):
        self.mouse = e.position()
        d = self.drag
        if d and not d["moved"] and (e.position() - d["start"]).manhattanLength() > 8:
            d["moved"] = True

    def mousePressEvent(self, e):
        self.mouse = e.position()
        if e.button() == Qt.RightButton:
            self.sel, self.psel, self.jsel, self.csel = [], [], None, None
            self.overlay = None if self.overlay else None
            return
        if e.button() != Qt.LeftButton:
            return
        pos = e.position()
        for rect, action in reversed(self.hits):
            if rect.contains(pos):
                self.sfx("click")
                action()
                return
        for rect, kind, i in reversed(self.drags):
            if rect.contains(pos):
                if self.anim and kind in ("hand", "joker"):
                    return
                self.drag = {"kind": kind, "i": i, "start": pos, "moved": False}
                return
        self.jsel = self.csel = None

    def mouseReleaseEvent(self, e):
        d = self.drag
        self.drag = None
        if not d or self.run is None:
            return
        run = self.run
        kind, i = d["kind"], d["i"]
        if kind == "hand":
            lst = run.rnd.hand if run.rnd else None
        elif kind == "phand":
            lst = None
        else:
            lst = run.jokers
        if d["moved"] and lst is not None and i < len(lst):
            L = self._layout()
            if kind == "joker":
                xs = [x + JW / 2 for x in self._row_xs(len(lst), L["jokers"], JW)]
            else:
                xs = [x + CW / 2 for x, _y, _a in self._hand_slots(len(lst), L["hand"])]
            new = sum(1 for k, x in enumerate(xs) if k != i and x < e.position().x())
            item = lst.pop(i)
            lst.insert(new, item)
            if kind == "hand":
                run.rnd.sort = None
            elif self.jsel is not None:
                self.jsel = new if self.jsel == i else self.jsel
            self._save()
            return
        if d["moved"]:
            return
        if kind == "hand" and run.stage == "round" and not self.anim:
            cid = run.rnd.hand[i]["id"]
            if cid in self.sel:
                self.sel.remove(cid)
                self.sfx("deselect")
            elif len(self.sel) < 5:
                self.sel.append(cid)
                self.sfx("select")
        elif kind == "phand":
            hand = run.pack_hand()
            if i < len(hand):
                cid = hand[i]["id"]
                if cid in self.psel:
                    self.psel.remove(cid)
                    self.sfx("deselect")
                elif len(self.psel) < 5:
                    self.psel.append(cid)
                    self.sfx("select")
        elif kind == "joker":
            self.jsel = None if self.jsel == i else i
            self.csel = None
            self.sfx("select" if self.jsel is not None else "deselect")

    def closeEvent(self, event):
        if self.anim and self.run:
            self.anim = None
            self.run.after_play()
        self._save()
        self.timer.stop()
        self.audio.stop()
        event.accept()


def atro_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#1A1A1A"), 1))
    p.setBrush(QColor("#2E6DA4"))
    p.save()
    p.translate(13, 17)
    p.rotate(-12)
    p.drawRoundedRect(QRectF(-8, -12, 16, 23), 2.5, 2.5)
    p.restore()
    p.setBrush(QColor("#F8F6EF"))
    p.save()
    p.translate(19, 15)
    p.rotate(10)
    p.drawRoundedRect(QRectF(-8, -12, 16, 23), 2.5, 2.5)
    f = QFont(UI)
    f.setPixelSize(13)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor(MULT))
    p.drawText(QRectF(-8, -10, 16, 20), Qt.AlignCenter, "C")
    p.restore()
    p.end()
    return QIcon(pm)


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = Table(desktop)
        win = host.window(desktop, TITLE, body, atro_icon(), (1240, 780))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.close()
