"""The clock, top right, as the Timeline's other games show theirs: the sky of the hour with the sun or the moon on its
arc over a strip of ground (white when snow lies), the moon's face, the time and the part of the day, the date, and
the weather - its sign, its name, and how hard it's coming down."""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen

SERIF = "Georgia"
PARTS = {"dusk": "dusk", "night": "night", "dawn": "dawn", "day": "day"}


def _q(rgb, a=255, lift=1.0):
    return QColor(*(max(0, min(255, int((c ** (1 / 2.2)) * 255 * lift))) for c in rgb), a)


def moon(p, c, r, phase):
    """The moon in its phase (0 new .. 4 full .. 8 new)."""
    p.save()
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(40, 44, 60))
    p.drawEllipse(c, r, r)
    if phase % 8:
        k = math.cos(phase / 4 * math.pi) if phase <= 4 else math.cos((phase - 4) / 4 * math.pi)
        waxing = phase <= 4
        pts = []
        for i in range(41):
            a = -math.pi / 2 + math.pi * i / 40
            x = math.cos(a) * r
            pts.append(QPointF(c.x() + (x if waxing else -x), c.y() + math.sin(a) * r))
        for i in range(40, -1, -1):
            a = -math.pi / 2 + math.pi * i / 40
            x = math.cos(a) * r * k
            pts.append(QPointF(c.x() + (x if waxing else -x), c.y() + math.sin(a) * r))
        path = QPainterPath(pts[0])
        for q in pts[1:]:
            path.lineTo(q)
        p.setBrush(QColor("#ECE8D6"))
        p.drawPath(path)
    p.restore()


def weather_icon(p, c, s, kind, night):
    p.save()
    if kind == "clear":
        if night:                                            # (a clear night: the aurora)
            g = QLinearGradient(c.x() - s * 0.5, 0, c.x() + s * 0.5, 0)
            g.setColorAt(0, QColor(60, 230, 140, 220))
            g.setColorAt(1, QColor(150, 80, 230, 220))
            p.setPen(QPen(g, 3))
            for dy in (-0.15, 0.1):
                p.drawLine(QPointF(c.x() - 0.5 * s, c.y() + dy * s), QPointF(c.x() + 0.5 * s, c.y() + (dy - 0.2) * s))
        else:
            p.setPen(QPen(QColor("#F8D060"), 1.5))
            p.setBrush(QColor("#F8D060"))
            p.drawEllipse(c, s * 0.3, s * 0.3)
            for i in range(8):
                a = i * math.pi / 4
                p.drawLine(QPointF(c.x() + math.cos(a) * s * 0.45, c.y() + math.sin(a) * s * 0.45),
                           QPointF(c.x() + math.cos(a) * s * 0.65, c.y() + math.sin(a) * s * 0.65))
    else:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#C8CED8") if kind != "storm" else QColor("#7A808C"))
        for dx, dy, r in ((-0.25, 0.05, 0.3), (0.1, -0.12, 0.38), (0.35, 0.08, 0.26)):
            p.drawEllipse(QPointF(c.x() + dx * s, c.y() + dy * s), r * s, r * s)
        if kind in ("rain", "storm"):
            p.setPen(QPen(QColor("#80B0F0"), 1.5))
            for dx in (-0.25, 0.0, 0.25):
                p.drawLine(QPointF(c.x() + dx * s, c.y() + 0.4 * s), QPointF(c.x() + (dx - 0.08) * s, c.y() + 0.65 * s))
        if kind == "storm":
            p.setPen(QPen(QColor("#FFE860"), 2))
            p.drawPolyline([QPointF(c.x() + 0.05 * s, c.y() + 0.3 * s), QPointF(c.x() - 0.08 * s, c.y() + 0.5 * s),
                            QPointF(c.x() + 0.06 * s, c.y() + 0.5 * s), QPointF(c.x() - 0.06 * s, c.y() + 0.72 * s)])
        if kind == "snow":
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#FFFFFF"))
            for dx in (-0.25, 0.0, 0.25):
                p.drawEllipse(QPointF(c.x() + dx * s, c.y() + 0.55 * s), 2.2, 2.2)
    p.restore()


def draw(p, W, H, sky, alpha=1.0):
    if alpha <= 0.01 or sky is None:
        return
    p.save()
    p.setOpacity(alpha)
    p.setRenderHint(QPainter.Antialiasing)
    r = QRectF(W - 236, 14, 222, 112)
    p.setPen(QPen(QColor(92, 70, 50, 210), 1.2))
    p.setBrush(QColor(8, 5, 6, 190))
    p.drawRoundedRect(r, 8, 8)
    lit = sky.light()
    name, k = sky.phase()
    night = name in ("night", "dusk") and not (name == "dusk" and k < 0.4)
    band = QRectF(r.x() + 7, r.y() + 7, r.width() - 56, 46)
    g = QLinearGradient(0, band.top(), 0, band.bottom())
    g.setColorAt(0, _q(lit["sky_top"], lift=2.2))
    g.setColorAt(1, _q(lit["sky_low"], lift=1.6))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawRoundedRect(band, 4, 4)
    p.setBrush(QColor(210, 214, 222) if sky.snow > 0.3 else QColor(40, 52, 32))
    p.drawRect(QRectF(band.x(), band.bottom() - 7, band.width(), 7))
    cx, base = band.center().x(), band.bottom() - 7
    R = min(band.width() / 2 - 8, band.height() - 12)
    p.setPen(QPen(QColor(255, 255, 255, 45), 1, Qt.DashLine))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(cx - R, base - R, 2 * R, 2 * R), 0, 180 * 16)
    hour = (sky.clock % 1440) / 60.0
    phase = (sky.day() + 2) % 8
    p.setClipRect(QRectF(band.x(), band.y(), band.width(), band.height() - 7))
    for ang_h, is_sun in ((hour - 6.0, True), (hour - 18.0, False)):     # (the sun by day, the moon by night, on the arc)
        t = (ang_h % 24) / 12.0 * math.pi
        if t > math.pi:
            continue
        pos = QPointF(cx - math.cos(t) * R, base - math.sin(t) * R)
        if is_sun:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#FFE070"))
            p.drawEllipse(pos, 5, 5)
        else:
            moon(p, pos, 4.5, phase)
    p.setClipping(False)
    moon(p, QPointF(r.right() - 25, r.y() + 30), 17, phase)
    p.setPen(QColor("#F0E4C8"))
    p.setFont(QFont(SERIF, 11, QFont.Bold))
    p.drawText(QPointF(r.x() + 9, r.y() + 71), f"{sky.hour_words()}  ·  {PARTS[name]}")
    p.setFont(QFont(SERIF, 8))
    p.setPen(QColor("#C8BCA0"))
    p.drawText(QPointF(r.x() + 9, r.y() + 86), sky.date_words())
    weather_icon(p, QPointF(r.x() + 18, r.y() + 99), 15, sky.weather, night)
    p.setPen(QColor("#E0D8C0"))
    p.drawText(QPointF(r.x() + 33, r.y() + 103), sky.weather_words())
    if sky.weather != "clear":
        for i in range(5):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(230, 210, 150, 230) if sky.strength > i / 5 + 0.05 else QColor(255, 255, 255, 40))
            p.drawRect(QRectF(r.right() - 50 + i * 8, r.y() + 97, 6, 6))
    p.restore()
