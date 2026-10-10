"""Painted artwork for Copilot Desktop Widgets: weather glyphs, the moon, and the program/tray icon."""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

from . import weather as wx

SUN = QColor("#FFD23C")
CLOUD_LIGHT = QColor("#F4F7FC")
CLOUD_MID = QColor("#C5CEDD")
CLOUD_DARK = QColor("#8793A8")
STORM = QColor("#5E6678")


def _cloud(p, color, x, y, scale):
    """A cloud drawn in a 100x100 box; (x, y) and scale place it inside the glyph."""
    path = QPainterPath()
    path.addEllipse(QRectF(10, 40, 36, 36))
    path.addEllipse(QRectF(28, 24, 44, 44))
    path.addEllipse(QRectF(54, 38, 36, 36))
    path.addRoundedRect(QRectF(26, 50, 48, 26), 13, 13)
    path.setFillRule(Qt.WindingFill)
    p.save()
    p.translate(x, y)
    p.scale(scale, scale)
    p.setPen(QPen(color.darker(125), 2))
    p.setBrush(color)
    p.drawPath(path.simplified())
    p.restore()


def _sun(p, cx, cy, r):
    p.save()
    p.setPen(QPen(SUN, max(1.5, r * 0.16), Qt.SolidLine, Qt.RoundCap))
    for i in range(8):
        a = math.radians(i * 45)
        p.drawLine(QPointF(cx + math.cos(a) * r * 1.35, cy + math.sin(a) * r * 1.35),
                   QPointF(cx + math.cos(a) * r * 1.8, cy + math.sin(a) * r * 1.8))
    p.setPen(QPen(QColor("#E8A814"), 1.5))
    p.setBrush(SUN)
    p.drawEllipse(QPointF(cx, cy), r, r)
    p.restore()


def _crescent(p, cx, cy, r):
    path = QPainterPath()
    path.addEllipse(QPointF(cx, cy), r, r)
    cut = QPainterPath()
    cut.addEllipse(QPointF(cx + r * 0.5, cy - r * 0.25), r * 0.85, r * 0.85)
    p.save()
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#F4EBC1"))
    p.drawPath(path.subtracted(cut))
    p.restore()


def _body(p, night, cx, cy, r):
    _crescent(p, cx, cy, r) if night else _sun(p, cx, cy, r)


def _drops(p, n=3):
    p.setPen(QPen(QColor("#5CA8FF"), 3.2, Qt.SolidLine, Qt.RoundCap))
    for i in range(n):
        x = 30 + i * 18
        p.drawLine(QPointF(x + 4, 78), QPointF(x - 2, 92))


def draw_condition(p, rect, cond, night=False):
    """Draw a weather glyph filling rect."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    p.translate(rect.x(), rect.y())
    p.scale(rect.width() / 100.0, rect.height() / 100.0)
    if cond == wx.CLEAR:
        _body(p, night, 50, 50, 24)
    elif cond == wx.PARTLY:
        _body(p, night, 36, 36, 17)
        _cloud(p, CLOUD_LIGHT, 8, 8, 0.9)
    elif cond == wx.CLOUDY:
        _body(p, night, 34, 32, 15)
        _cloud(p, CLOUD_MID, 0, 6, 0.95)
    elif cond == wx.OVERCAST:
        _cloud(p, CLOUD_DARK, 0, 14, 1.0)
    elif cond == wx.FOG:
        _cloud(p, CLOUD_MID, 0, 0, 0.95)
        p.setPen(QPen(QColor("#DDE5F2"), 4, Qt.SolidLine, Qt.RoundCap))
        for i, (x1, x2) in enumerate(((16, 84), (24, 76), (16, 84))):
            p.drawLine(QPointF(x1, 78 + i * 8), QPointF(x2, 78 + i * 8))
    elif cond == wx.RAIN:
        _cloud(p, CLOUD_DARK, 0, -6, 1.0)
        _drops(p)
    elif cond == wx.THUNDER:
        _cloud(p, STORM, 0, -8, 1.0)
        bolt = QPolygonF([QPointF(52, 60), QPointF(38, 82), QPointF(49, 82), QPointF(42, 98),
                          QPointF(64, 74), QPointF(52, 74), QPointF(58, 60)])
        p.setPen(QPen(QColor("#C88A00"), 1.5))
        p.setBrush(SUN)
        p.drawPolygon(bolt)
    elif cond == wx.SNOW:
        _cloud(p, CLOUD_MID, 0, -6, 1.0)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("white"))
        for x, y in ((30, 82), (50, 90), (70, 82), (40, 70), (62, 72)):
            p.drawEllipse(QPointF(x, y), 4.2, 4.2)
    p.restore()


def draw_moon(p, cx, cy, r, age, hemisphere="Northern"):
    """The moon's disc with its lit part, from its age in days."""
    synodic = 29.530588853
    frac = age / synodic
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#6C7A9E"), 1))
    p.setBrush(QColor("#243056"))
    p.drawEllipse(QPointF(cx, cy), r, r)
    waxing = frac < 0.5
    if hemisphere == "Southern":
        waxing = not waxing
    half = QPainterPath()
    half.moveTo(cx, cy - r)
    half.arcTo(QRectF(cx - r, cy - r, 2 * r, 2 * r), 90, -180 if waxing else 180)
    half.closeSubpath()
    k = math.cos(2 * math.pi * frac)
    width = abs(k) * r
    term = QPainterPath()
    term.addEllipse(QPointF(cx, cy), max(0.01, width), r)
    lit = half.subtracted(term) if k > 0 else half.united(term)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#F6F0CE"))
    p.drawPath(lit)
    p.restore()


def _lock(p, x, y, s, locked):
    p.save()
    p.setPen(QPen(QColor("#6A4B00"), max(1.0, s * 0.09)))
    p.setBrush(QColor("#FFD23C"))
    p.drawRoundedRect(QRectF(x, y + s * 0.42, s, s * 0.58), s * 0.1, s * 0.1)
    p.setBrush(Qt.NoBrush)
    shackle = QPainterPath()
    left = x + s * 0.2
    if locked:
        shackle.moveTo(left, y + s * 0.42)
        shackle.lineTo(left, y + s * 0.22)
        shackle.arcTo(QRectF(left, y, s * 0.6, s * 0.44), 180, -180)
        shackle.lineTo(x + s * 0.8, y + s * 0.42)
    else:
        shackle.moveTo(x + s * 0.8, y + s * 0.42)
        shackle.lineTo(x + s * 0.8, y + s * 0.16)
        shackle.arcTo(QRectF(left + s * 0.2, y - s * 0.06, s * 0.6, s * 0.44), 0, 180)
        shackle.lineTo(left + s * 0.2, y + s * 0.2)
    p.drawPath(shackle)
    p.restore()


def widgets_pixmap(size=32, locked=None):
    """A blue tile of mini widgets (clock, calendar, sun and a TV). locked=True/False adds a padlock."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32.0
    grad = QLinearGradient(0, 0, 0, size)
    grad.setColorAt(0, QColor("#4F8BE8"))
    grad.setColorAt(1, QColor("#1B4DB0"))
    p.setPen(QPen(QColor("#0E2F7A"), max(1.0, s)))
    p.setBrush(grad)
    p.drawRoundedRect(QRectF(1 * s, 1 * s, 30 * s, 30 * s), 6 * s, 6 * s)

    tile = QColor(255, 255, 255, 235)
    p.setPen(Qt.NoPen)
    p.setBrush(tile)
    for x, y in ((4, 4), (17, 4), (4, 17), (17, 17)):
        p.drawRoundedRect(QRectF(x * s, y * s, 11 * s, 11 * s), 2 * s, 2 * s)
    # clock
    p.setPen(QPen(QColor("#1B4DB0"), max(1.0, 1.2 * s), Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(9.5 * s, 9.5 * s), QPointF(9.5 * s, 6 * s))
    p.drawLine(QPointF(9.5 * s, 9.5 * s), QPointF(12 * s, 10.5 * s))
    # calendar
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#D33A2C"))
    p.drawRoundedRect(QRectF(17 * s, 4 * s, 11 * s, 3.5 * s), 1.5 * s, 1.5 * s)
    p.setBrush(QColor("#1B4DB0"))
    for i in range(3):
        for j in range(2):
            p.drawRect(QRectF((18.5 + i * 3) * s, (9 + j * 2.6) * s, 1.8 * s, 1.5 * s))
    # sun
    p.setBrush(SUN)
    p.drawEllipse(QPointF(9.5 * s, 22.5 * s), 3 * s, 3 * s)
    # tv
    p.setBrush(QColor("#2C3E5E"))
    p.drawRoundedRect(QRectF(19 * s, 19 * s, 8 * s, 6.5 * s), 1 * s, 1 * s)
    p.setBrush(QColor("#7BD3FF"))
    p.drawRect(QRectF(20 * s, 20 * s, 6 * s, 4.2 * s))
    if locked is not None:
        _lock(p, 19 * s, 17.5 * s, 12.5 * s, locked)
    p.end()
    return pm


def widgets_icon(size=32, locked=None):
    return QIcon(widgets_pixmap(size, locked))
