"""Drawn icons for the messengers: MSN's butterfly and green buddy, Yahoo!'s smiley. A PNG with the same name in
assets/images/messengers/ (msn_butterfly.png, msn_online.png, yim_online.png...) replaces any of them."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient

from ...paths import IMAGES

ART = IMAGES / "messengers"
_cache = {}


def _custom(name, size):
    path = ART / f"{name}.png"
    if path.is_file():
        pm = QPixmap(str(path))
        if not pm.isNull():
            return pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return None


def _canvas(size):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size / 64, size / 64)
    return pm, p


def pixmap(name, size=32):
    key = (name, size)
    if key not in _cache:
        _cache[key] = _custom(name, size) or DRAW[name](size)
    return _cache[key]


def icon(name, size=32):
    return QIcon(pixmap(name, size))


# ---- MSN ---------------------------------------------------------------------------------------------------------

def _butterfly(size):
    """The MSN butterfly: four wings, blue, green, orange and red, around a dark body."""
    pm, p = _canvas(size)
    wings = [(QRectF(6, 6, 28, 26), "#2B6DD9", "#8FC1FF", -18), (QRectF(30, 6, 28, 26), "#3DAA35", "#B8F08A", 18),
             (QRectF(10, 32, 22, 24), "#F28A14", "#FFD38A", 15), (QRectF(32, 32, 22, 24), "#E0301E", "#FF9A8A", -15)]
    for rect, dark, light, angle in wings:
        p.save()
        p.translate(rect.center())
        p.rotate(angle)
        p.translate(-rect.center())
        g = QRadialGradient(rect.center() - QPointF(3, 3), rect.width() * 0.7)
        g.setColorAt(0, QColor(light))
        g.setColorAt(1, QColor(dark))
        p.setBrush(g)
        p.setPen(QPen(QColor(dark).darker(130), 1.2))
        p.drawEllipse(rect)
        p.restore()
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#2A2A2A"))
    p.drawRoundedRect(QRectF(29.5, 12, 5, 42), 2.5, 2.5)
    p.end()
    return pm


def _msn_person(color_head, color_body):
    def draw(size):
        pm, p = _canvas(size)
        g = QLinearGradient(0, 30, 0, 60)
        g.setColorAt(0, QColor(color_body).lighter(140))
        g.setColorAt(1, QColor(color_body))
        p.setPen(QPen(QColor(color_body).darker(160), 2))
        p.setBrush(g)
        body = QPainterPath()
        body.moveTo(12, 60)
        body.cubicTo(12, 36, 52, 36, 52, 60)
        body.closeSubpath()
        p.drawPath(body)
        hg = QRadialGradient(QPointF(28, 18), 16)
        hg.setColorAt(0, QColor(color_head).lighter(150))
        hg.setColorAt(1, QColor(color_head))
        p.setBrush(hg)
        p.setPen(QPen(QColor(color_head).darker(160), 2))
        p.drawEllipse(QRectF(19, 4, 26, 26))
        p.end()
        return pm
    return draw


def _msn_away(size):
    pm = _msn_person("#3DAA35", "#2B6DD9")(size).copy()
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size / 64, size / 64)
    p.setPen(QPen(QColor("#7A5A00"), 2))
    p.setBrush(QColor("#FFD400"))
    p.drawEllipse(QRectF(36, 34, 26, 26))
    p.setPen(QPen(QColor("#5A4000"), 2.5))
    p.drawLine(QPointF(49, 39), QPointF(49, 47))
    p.drawLine(QPointF(49, 47), QPointF(55, 51))
    p.end()
    return pm


# ---- Yahoo! ------------------------------------------------------------------------------------------------------

def _smiley(face, rim):
    def draw(size):
        pm, p = _canvas(size)
        g = QRadialGradient(QPointF(24, 22), 34)
        g.setColorAt(0, QColor(face).lighter(130))
        g.setColorAt(1, QColor(face))
        p.setBrush(g)
        p.setPen(QPen(QColor(rim), 3))
        p.drawEllipse(QRectF(5, 5, 54, 54))
        p.setBrush(QColor("#1A1A1A"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(21, 20, 7, 11))
        p.drawEllipse(QRectF(36, 20, 7, 11))
        p.setPen(QPen(QColor("#1A1A1A"), 3.5, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(17, 22, 30, 26), 200 * 16, 140 * 16)
        p.end()
        return pm
    return draw


def _yim_away(size):
    pm = _smiley("#FFD400", "#9A7400")(size).copy()
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size / 64, size / 64)
    p.setBrush(QColor("#FFFFFF"))
    p.setPen(QPen(QColor("#5A2A88"), 2))
    p.drawEllipse(QRectF(38, 36, 24, 24))
    p.setPen(QPen(QColor("#5A2A88"), 2.5))
    p.drawLine(QPointF(50, 40), QPointF(50, 48))
    p.drawLine(QPointF(50, 48), QPointF(56, 52))
    p.end()
    return pm


def _yim_logo(size):
    """The program icon: a smiley on Yahoo! purple."""
    pm, p = _canvas(size)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#6B1FA0"))
    p.drawRoundedRect(QRectF(2, 2, 60, 60), 12, 12)
    p.end()
    face = _smiley("#FFD400", "#9A7400")(int(size * 0.8))
    p = QPainter(pm)
    p.drawPixmap(int(size * 0.1), int(size * 0.1), face)
    p.end()
    return pm


def yahoo_wordmark(height=28, color="#FFFFFF"):
    """'Yahoo!' in the logo's heavy serif, for the window headers."""
    f = QFont("Georgia", int(height * 0.62), QFont.Black)
    f.setItalic(False)
    from PySide6.QtGui import QFontMetrics
    w = QFontMetrics(f).horizontalAdvance("Yahoo!") + 6
    pm = QPixmap(w, height)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setFont(f)
    p.setPen(QColor(color))
    p.drawText(QRectF(0, 0, w, height), Qt.AlignVCenter | Qt.AlignLeft, "Yahoo!")
    p.end()
    return pm


DRAW = {
    "msn_butterfly": _butterfly,
    "msn_online": _msn_person("#3DAA35", "#2B6DD9"),
    "msn_offline": _msn_person("#D9483B", "#A33A30"),
    "msn_away": _msn_away,
    "yim_logo": _yim_logo,
    "yim_online": _smiley("#FFD400", "#9A7400"),
    "yim_offline": _smiley("#C8C8C8", "#8A8A8A"),
    "yim_away": _yim_away,
}
