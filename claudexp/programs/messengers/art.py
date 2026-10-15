"""Drawn icons for the messengers: MSN's butterfly and green buddy, Yahoo!'s smiley. A PNG with the same name in
assets/images/messengers/ (msn_butterfly.png, msn_online.png, yim_online.png...) replaces any of them."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient

from ...paths import IMAGES

ART = IMAGES / "messengers"
_cache = {}
_trimmed = {}


# the program icons the user supplied (assets/images/MSN.png, YIM.png)
SUPPLIED = {"msn_logo": IMAGES / "MSN.png", "yim_logo": IMAGES / "YIM.png", "icq_logo": IMAGES / "ICQ.png",
            "kik_logo": IMAGES / "KIK.png", "skype_logo": IMAGES / "Skyoe.png", "trillian_logo": IMAGES / "Trillian.png"}


def _trim(img):
    """Cut away empty transparent margins (an icon drawn in the middle of a big canvas)."""
    if not img.hasAlphaChannel():
        return img
    small = img.scaled(min(img.width(), 256), min(img.height(), 256), Qt.KeepAspectRatio)
    xs, ys = [], []
    for y in range(small.height()):
        for x in range(small.width()):
            if small.pixelColor(x, y).alpha() > 16:
                xs.append(x)
                ys.append(y)
    if not xs:
        return img
    fx, fy = img.width() / small.width(), img.height() / small.height()
    x0, y0 = int(min(xs) * fx), int(min(ys) * fy)
    x1, y1 = int((max(xs) + 1) * fx), int((max(ys) + 1) * fy)
    return img.copy(x0, y0, x1 - x0, y1 - y0)


def _custom(name, size):
    path = ART / f"{name}.png"
    if not path.is_file() and name in SUPPLIED:
        path = SUPPLIED[name]
    if path.is_file():
        from PySide6.QtGui import QImage
        img = QImage(str(path))
        if not img.isNull():
            key = str(path)
            if key not in _trimmed:
                _trimmed[key] = _trim(img)
            img = _trimmed[key].scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            return QPixmap.fromImage(img)
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
    "msn_logo": _butterfly,
    "msn_online": _msn_person("#3DAA35", "#2B6DD9"),
    "msn_offline": _msn_person("#D9483B", "#A33A30"),
    "msn_away": _msn_away,
    "yim_logo": _yim_logo,
    "yim_online": _smiley("#FFD400", "#9A7400"),
    "yim_offline": _smiley("#C8C8C8", "#8A8A8A"),
    "yim_away": _yim_away,
}


# ---- ICQ, Skype, Trillian, KIK -----------------------------------------------------------------------------------

def _flower(petal, centre="#FFE000", odd=None):
    """ICQ's flower: eight petals around a yellow middle (offline: all red)."""
    def draw(size):
        pm, p = _canvas(size)
        import math
        for i in range(8):
            a = math.radians(i * 45)
            cx, cy = 32 + 17 * math.cos(a), 32 + 17 * math.sin(a)
            p.setBrush(QColor(odd if odd and i == 3 else petal))
            p.setPen(QPen(QColor("#1A1A1A"), 2))
            p.save()
            p.translate(cx, cy)
            p.rotate(i * 45)
            p.drawEllipse(QRectF(-11, -8, 22, 16))
            p.restore()
        p.setBrush(QColor(centre))
        p.drawEllipse(QRectF(22, 22, 20, 20))
        p.end()
        return pm
    return draw


def _disc(fill, mark=None):
    """A round status light: green with a tick, grey, or yellow with a clock."""
    def draw(size):
        pm, p = _canvas(size)
        g = QRadialGradient(QPointF(24, 22), 34)
        g.setColorAt(0, QColor(fill).lighter(150))
        g.setColorAt(1, QColor(fill))
        p.setBrush(g)
        p.setPen(QPen(QColor(fill).darker(150), 3))
        p.drawEllipse(QRectF(6, 6, 52, 52))
        p.setPen(QPen(QColor("#FFFFFF"), 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        if mark == "tick":
            path = QPainterPath()
            path.moveTo(19, 33)
            path.lineTo(28, 42)
            path.lineTo(45, 22)
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)
        elif mark == "clock":
            p.drawLine(QPointF(32, 32), QPointF(32, 18))
            p.drawLine(QPointF(32, 32), QPointF(42, 38))
        p.end()
        return pm
    return draw


DRAW.update({
    "icq_logo": _flower("#3DCC2B", odd="#E8281E"),
    "icq_online": _flower("#3DCC2B"),
    "icq_offline": _flower("#E8281E"),
    "icq_away": _flower("#3DCC2B", centre="#FFFFFF"),
    "skype_logo": _disc("#00AFF0"),
    "skype_online": _disc("#3CB43C", "tick"),
    "skype_offline": _disc("#B0B0B0"),
    "skype_away": _disc("#F2C200", "clock"),
    "trillian_logo": _disc("#2E8BA8"),
    "kik_logo": _disc("#82BC23"),
    "dot_online": _disc("#3CB43C"),
    "dot_offline": _disc("#B0B0B0"),
    "dot_away": _disc("#F2C200"),
})
