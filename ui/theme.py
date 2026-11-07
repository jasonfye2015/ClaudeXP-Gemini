"""The look: dark leather and old gold. One place for the colours, the fonts, the widgets' stylesheet, the painted
panel (gradient, grain, a double gold rim, filigree corners), the HUD's pieces (glass orbs with moving liquid, the
gold-rimmed plate, bars with a shimmer, outlined text, ribbons) and the small animations (a panel rising in)."""
import math
import random

from PySide6.QtCore import QEasingCurve, QPointF, QPropertyAnimation, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QImage, QLinearGradient, QPainter, QPainterPath, QPainterPathStroker,
                           QPen, QPixmap, QRadialGradient)
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect

HEAD = "Palatino Linotype"                    # (Windows has it; Qt falls back to a serif where it doesn't)
BODY = "Segoe UI"
GOLD = QColor("#E8C068")
GOLD_HI = QColor("#FFF0B8")
GOLD_LO = QColor("#8A6420")
INK = QColor("#F0E4C8")
DIM = QColor("#B8A888")

CSS = f"""
QLabel {{ color: #F0E4C8; font-family: '{HEAD}', Georgia; font-size: 14px; background: transparent; }}
QLabel#title {{ color: #F6D98A; font-size: 34px; font-weight: bold; }}
QLabel#heading {{ color: #F6D98A; font-size: 21px; font-weight: bold; padding-bottom: 3px;
                  border-bottom: 1px solid qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(232,192,104,0),
                  stop:0.15 rgba(232,192,104,200), stop:0.85 rgba(232,192,104,200), stop:1 rgba(232,192,104,0)); }}
QLabel#sub {{ color: #C8B898; font-size: 14px; font-style: italic; }}
QLabel#small {{ color: #C8BCA0; font-size: 12px; font-family: '{BODY}'; }}
QFrame#card {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(52,40,28,235), stop:1 rgba(30,23,16,235));
               border: 1px solid #5A4630; border-radius: 8px; }}
QPushButton {{ color: #FFF2D0; font-family: '{HEAD}', Georgia; font-size: 14px; padding: 7px 18px; border-radius: 7px;
               border: 1px solid #A07C40;
               background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6A4E2C, stop:0.48 #4A3420, stop:0.52 #3C2A18, stop:1 #2A1E12); }}
QPushButton:hover {{ border: 1px solid #FFD878; color: #FFFFFF;
                     background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8A6838, stop:0.48 #6A4C28, stop:0.52 #5A3E20, stop:1 #3A2814); }}
QPushButton:pressed {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2A1E12, stop:1 #4A3420); padding-top: 8px; }}
QPushButton:disabled {{ color: #7A7060; border-color: #4A4030; background: #2A2418; }}
QPushButton#danger {{ border-color: #B05040; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6A2A20, stop:1 #3A1410); }}
QPushButton#danger:hover {{ border-color: #FF8868; }}
QLineEdit {{ background: rgba(20,15,10,220); color: #F0E4C8; border: 1px solid #7A6040; border-radius: 6px; padding: 7px;
             font-family: '{HEAD}', Georgia; font-size: 14px; selection-background-color: #8A6420; }}
QLineEdit:focus {{ border-color: #E8C068; }}
QToolTip {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2E2418, stop:1 #17120C); color: #F0E4C8;
            border: 1px solid #C8A060; font-family: '{BODY}'; font-size: 12px; padding: 4px; }}
QScrollArea {{ background: transparent; border: none; }}
"""

_grain = None


def grain():
    """A faint grain to lie over a panel's gradient, made once."""
    global _grain
    if _grain is None:
        rng = random.Random(7)
        img = QImage(128, 128, QImage.Format_ARGB32)
        for y in range(128):
            for x in range(128):
                v = rng.randint(0, 255)
                img.setPixelColor(x, y, QColor(v, v, v, rng.randint(4, 14)))
        _grain = QPixmap.fromImage(img)
    return _grain


def gold_pen(rect, width=2.0):
    g = QLinearGradient(rect.topLeft(), rect.bottomRight())
    g.setColorAt(0, GOLD_HI)
    g.setColorAt(0.3, GOLD)
    g.setColorAt(0.6, GOLD_LO)
    g.setColorAt(1, GOLD)
    return QPen(QBrush(g), width)


def corner(p, x, y, sx, sy, size=18):
    """A filigree corner: a diamond and two curls, in gold (sx, sy: which way the corner opens)."""
    p.save()
    p.translate(x, y)
    p.scale(sx, sy)
    path = QPainterPath()
    path.moveTo(0, size)
    path.cubicTo(0, size * 0.4, size * 0.4, 0, size, 0)
    path.moveTo(size * 0.25, size * 1.3)
    path.cubicTo(size * 0.3, size * 0.75, size * 0.75, size * 0.3, size * 1.3, size * 0.25)
    p.setPen(QPen(GOLD, 1.6))
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)
    d = QPainterPath()
    d.moveTo(size * 0.32, size * 0.06)
    d.lineTo(size * 0.5, size * 0.32)
    d.lineTo(size * 0.32, size * 0.58)
    d.lineTo(size * 0.06, size * 0.32)
    d.closeSubpath()
    g = QRadialGradient(QPointF(size * 0.3, size * 0.3), size * 0.4)
    g.setColorAt(0, GOLD_HI)
    g.setColorAt(1, GOLD_LO)
    p.setPen(QPen(QColor(40, 26, 10), 1))
    p.setBrush(g)
    p.drawPath(d)
    p.restore()


def paint_frame(p, rect, radius=12):
    """A panel: a dark leather gradient with a warm light at the top, grain, a double gold rim and the corners."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    r = QRectF(rect).adjusted(2, 2, -2, -2)
    bg = QLinearGradient(r.topLeft(), r.bottomLeft())
    bg.setColorAt(0, QColor(44, 33, 22, 246))
    bg.setColorAt(0.35, QColor(28, 21, 15, 246))
    bg.setColorAt(1, QColor(16, 12, 9, 248))
    path = QPainterPath()
    path.addRoundedRect(r, radius, radius)
    p.fillPath(path, bg)
    glow = QRadialGradient(QPointF(r.center().x(), r.top()), r.width() * 0.7)
    glow.setColorAt(0, QColor(255, 200, 120, 34))
    glow.setColorAt(1, QColor(255, 200, 120, 0))
    p.fillPath(path, glow)
    p.setClipPath(path)
    p.drawTiledPixmap(r, grain())
    p.setClipping(False)
    p.setPen(QPen(QColor(10, 6, 3, 230), 4))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(r, radius, radius)
    p.setPen(gold_pen(r, 2.2))
    p.drawRoundedRect(r.adjusted(1, 1, -1, -1), radius, radius)
    p.setPen(QPen(QColor(232, 192, 104, 70), 1))
    p.drawRoundedRect(r.adjusted(6, 6, -6, -6), radius - 4, radius - 4)
    for x, y, sx, sy in ((r.left() + 5, r.top() + 5, 1, 1), (r.right() - 5, r.top() + 5, -1, 1),
                         (r.left() + 5, r.bottom() - 5, 1, -1), (r.right() - 5, r.bottom() - 5, -1, -1)):
        corner(p, x, y, sx, sy)
    p.restore()


class Ornate(QFrame):
    """A panel that paints itself (paint_frame), with a shadow under it."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._shadow()

    def _shadow(self):
        sh = QGraphicsDropShadowEffect(self)
        sh.setBlurRadius(42)
        sh.setOffset(0, 10)
        sh.setColor(QColor(0, 0, 0, 200))
        self.setGraphicsEffect(sh)

    def paintEvent(self, e):
        p = QPainter(self)
        paint_frame(p, self.rect())
        p.end()


def fade_in(widget, ms=220):
    """A widget comes in: from nothing to whole."""
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    a = QPropertyAnimation(eff, b"opacity", widget)
    a.setDuration(ms)
    a.setStartValue(0.0)
    a.setEndValue(1.0)
    a.setEasingCurve(QEasingCurve.OutCubic)
    a.finished.connect(lambda: widget._shadow() if hasattr(widget, "_shadow") else widget.setGraphicsEffect(None))
    a.start()
    widget._fade = a


# ---- the HUD's pieces ---------------------------------------------------------------------------------------------
def outlined(p, x, y, text, font, fill, alpha=255, outline=QColor(10, 6, 3), width=3.0, centre=False):
    """Text with a dark edge round it, readable on anything."""
    path = QPainterPath()
    path.addText(0, 0, font, text)
    br = path.boundingRect()
    path.translate(x - (br.width() / 2 + br.x() if centre else 0), y)
    o = QColor(outline)
    o.setAlpha(int(alpha * 0.85))
    f = QColor(fill)
    f.setAlpha(alpha)
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    st = QPainterPathStroker()
    st.setWidth(width)
    st.setJoinStyle(Qt.RoundJoin)
    p.fillPath(st.createStroke(path), o)
    p.fillPath(path, f)
    p.restore()
    return br.width()


def plate(p, r, radius=10, alpha=215):
    """A dark plate with a gold rim (the HUD's bar, its boxes)."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(r.topLeft(), r.bottomLeft())
    g.setColorAt(0, QColor(46, 34, 22, alpha))
    g.setColorAt(1, QColor(14, 10, 7, alpha))
    p.setPen(QPen(QColor(8, 5, 2, 220), 3))
    p.setBrush(g)
    p.drawRoundedRect(r, radius, radius)
    p.setPen(gold_pen(r, 1.5))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(r.adjusted(1.5, 1.5, -1.5, -1.5), radius - 1, radius - 1)
    p.restore()


def orb(p, cx, cy, r, frac, colour, label, t, warn=False):
    """A glass orb, its liquid rising to frac with a moving surface, a shine on the glass, a rim of old gold; it
    pulses when warn (life running low)."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    c = QPointF(cx, cy)
    if warn:
        k = 0.5 + 0.5 * math.sin(t * 6)
        halo = QRadialGradient(c, r * 1.6)
        halo.setColorAt(0.55, QColor(255, 40, 30, int(120 * k)))
        halo.setColorAt(1, QColor(255, 40, 30, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(halo)
        p.drawEllipse(c, r * 1.6, r * 1.6)
    # the empty glass
    back = QRadialGradient(QPointF(cx, cy - r * 0.2), r)
    back.setColorAt(0, QColor(30, 26, 30, 235))
    back.setColorAt(1, QColor(6, 5, 7, 245))
    p.setPen(Qt.NoPen)
    p.setBrush(back)
    p.drawEllipse(c, r, r)
    # the liquid, its surface moving
    frac = max(0.0, min(1.0, frac))
    if frac > 0:
        level = cy + r - 2 * r * frac
        wave = QPainterPath()
        wave.moveTo(cx - r, cy + r)
        steps = 24
        for i in range(steps + 1):
            x = cx - r + 2 * r * i / steps
            y = level + math.sin(t * 2.4 + i * 0.55) * r * 0.045 + math.sin(t * 3.7 + i * 0.9) * r * 0.025
            wave.lineTo(x, y)
        wave.lineTo(cx + r, cy + r)
        wave.closeSubpath()
        clip = QPainterPath()
        clip.addEllipse(c, r - 2, r - 2)
        liquid = QRadialGradient(QPointF(cx - r * 0.25, level + r * 0.3), r * 1.5)
        liquid.setColorAt(0, colour.lighter(165))
        liquid.setColorAt(0.5, colour)
        liquid.setColorAt(1, colour.darker(260))
        p.setClipPath(clip)
        p.fillPath(wave, liquid)
        p.setPen(QPen(colour.lighter(190), 1.2))
        p.setBrush(Qt.NoBrush)
        top = QPainterPath()
        for i in range(25):
            x = cx - r + 2 * r * i / 24
            y = level + math.sin(t * 2.4 + i * 0.55) * r * 0.045 + math.sin(t * 3.7 + i * 0.9) * r * 0.025
            top.moveTo(x, y) if i == 0 else top.lineTo(x, y)
        p.drawPath(top)
        for k in range(3):                                   # (a few bubbles rising)
            bx = cx + math.sin(k * 2.1 + t * 0.7) * r * 0.45
            by = cy + r - ((t * (14 + k * 5) + k * 30) % (2 * r * frac + 1))
            p.setPen(QPen(colour.lighter(200), 1))
            p.drawEllipse(QPointF(bx, by), 1.6 + k * 0.5, 1.6 + k * 0.5)
        p.setClipping(False)
    # the glass's shine
    shine = QRadialGradient(QPointF(cx - r * 0.35, cy - r * 0.45), r * 0.6)
    shine.setColorAt(0, QColor(255, 255, 255, 110))
    shine.setColorAt(1, QColor(255, 255, 255, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(shine)
    p.drawEllipse(QPointF(cx - r * 0.3, cy - r * 0.4), r * 0.55, r * 0.4)
    # the rim
    ring = QRectF(cx - r - 3, cy - r - 3, 2 * r + 6, 2 * r + 6)
    p.setPen(QPen(QColor(10, 6, 3, 230), 6))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(ring)
    p.setPen(gold_pen(ring, 3))
    p.drawEllipse(ring)
    for k in range(4):                                       # (four studs on the rim)
        a = k * math.pi / 2 + math.pi / 4
        sx, sy = cx + math.cos(a) * (r + 3), cy + math.sin(a) * (r + 3)
        g = QRadialGradient(QPointF(sx - 1, sy - 1), 4)
        g.setColorAt(0, GOLD_HI)
        g.setColorAt(1, GOLD_LO)
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(QPointF(sx, sy), 3.5, 3.5)
    outlined(p, cx, cy + 5, label, QFont(BODY, 10, QFont.Bold), QColor("#FFFFFF"), centre=True)
    p.restore()


def bar(p, r, frac, c0, c1, t, shimmer=True):
    """A bar filling to frac, a gradient from c0 to c1, a light running along it."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(8, 5, 2, 220), 2))
    p.setBrush(QColor(0, 0, 0, 170))
    p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
    frac = max(0.0, min(1.0, frac))
    if frac > 0:
        f = QRectF(r.x() + 1, r.y() + 1, (r.width() - 2) * frac, r.height() - 2)
        g = QLinearGradient(f.topLeft(), f.bottomLeft())
        g.setColorAt(0, c1)
        g.setColorAt(0.5, c0)
        g.setColorAt(1, c0.darker(170))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(f, f.height() / 2, f.height() / 2)
        if shimmer:
            x = r.x() + ((t * 120) % (r.width() + 120)) - 60
            sg = QLinearGradient(QPointF(x - 40, 0), QPointF(x + 40, 0))
            sg.setColorAt(0, QColor(255, 255, 255, 0))
            sg.setColorAt(0.5, QColor(255, 255, 255, 90))
            sg.setColorAt(1, QColor(255, 255, 255, 0))
            path = QPainterPath()
            path.addRoundedRect(f, f.height() / 2, f.height() / 2)
            p.fillPath(path, sg)
    p.setPen(gold_pen(r, 1))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
    p.restore()


def ribbon(p, cx, y, w, h, alpha=255):
    """A dark ribbon fading out at its ends, for a line of words to sit on."""
    g = QLinearGradient(QPointF(cx - w / 2, 0), QPointF(cx + w / 2, 0))
    g.setColorAt(0, QColor(10, 7, 4, 0))
    g.setColorAt(0.18, QColor(10, 7, 4, int(170 * alpha / 255)))
    g.setColorAt(0.82, QColor(10, 7, 4, int(170 * alpha / 255)))
    g.setColorAt(1, QColor(10, 7, 4, 0))
    p.fillRect(QRectF(cx - w / 2, y, w, h), g)
    line = QLinearGradient(QPointF(cx - w / 2, 0), QPointF(cx + w / 2, 0))
    gc = QColor(232, 192, 104, int(160 * alpha / 255))
    line.setColorAt(0, QColor(232, 192, 104, 0))
    line.setColorAt(0.5, gc)
    line.setColorAt(1, QColor(232, 192, 104, 0))
    p.fillRect(QRectF(cx - w / 2, y, w, 1), line)
    p.fillRect(QRectF(cx - w / 2, y + h - 1, w, 1), line)
