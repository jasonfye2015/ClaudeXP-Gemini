"""File icons ClaudeXP draws itself, for kinds of file Windows XP would have shown with an installed program's icon:
.py and .pyw files (Python) get a page with the blue and yellow snakes. XPIconProvider hands these to Explorer and
the desktop, and the system's own icons for everything else."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QFileIconProvider

_cache = {}


def py_icon(size=32):
    """The icon .py files wear: a page with the blue and yellow Python snakes."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size / 32, size / 32)
    sheet = QPolygonF([QPointF(5.5, 1.5), QPointF(20.5, 1.5), QPointF(26.5, 7.5), QPointF(26.5, 30.5),
                       QPointF(5.5, 30.5)])
    p.setPen(QPen(QColor("#7A7A7A"), 1))
    p.setBrush(QColor("white"))
    p.drawPolygon(sheet)
    p.setBrush(QColor("#E0E0E0"))
    p.drawPolygon(QPolygonF([QPointF(20.5, 1.5), QPointF(20.5, 7.5), QPointF(26.5, 7.5)]))
    # the two snakes: blue top-left, yellow bottom-right, each with an eye
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#3B78B4"))
    p.drawRoundedRect(QRectF(9, 9, 7, 9), 2.5, 2.5)
    p.drawRoundedRect(QRectF(9, 13, 11, 5), 2, 2)
    p.setBrush(QColor("#FFD43B"))
    p.drawRoundedRect(QRectF(16, 16, 7, 10), 2.5, 2.5)
    p.drawRoundedRect(QRectF(12, 19, 11, 5), 2, 2)
    p.setBrush(QColor("white"))
    p.drawEllipse(QRectF(10.5, 10.4, 2, 2))
    p.drawEllipse(QRectF(19.5, 22.6, 2, 2))
    p.end()
    return QIcon(pm)


class XPIconProvider(QFileIconProvider):
    """The system's icons, except for the kinds of file ClaudeXP draws itself. (Explorer's file model may ask from a
    background thread, so the drawing is done up front, here, and only the finished icon is handed out.)"""

    def __init__(self):
        super().__init__()
        if "py" not in _cache:
            _cache["py"] = py_icon()
        self._py = _cache["py"]

    def icon(self, what):
        if not isinstance(what, QFileIconProvider.IconType):
            suffix = what.suffix().lower() if hasattr(what, "suffix") else ""
            if suffix in ("py", "pyw"):
                return self._py
        return super().icon(what)
