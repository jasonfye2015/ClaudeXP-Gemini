"""XP's 'Log Off Windows' box: Switch User or Log Off, over a screen that slowly fades to grey.

Switch User leaves every program running and goes to the Welcome screen, which shows how many programs are still
open; clicking your name comes straight back. Log Off closes everything, as before.
"""
import time

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from . import sound

BOX_W, BOX_H = 312, 196
FADE_SECONDS = 1.6


def _switch_icon(size=34):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 34
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#7ED36A"))
    g.setColorAt(1, QColor("#2A8A1E"))
    p.setPen(QPen(QColor("#FFFFFF"), 1.6 * s))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(1.5 * s, 1.5 * s, 31 * s, 31 * s), 5 * s, 5 * s)
    p.setPen(QPen(QColor("#FFFFFF"), 2.6 * s, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(8 * s, 8 * s, 18 * s, 18 * s), 30 * 16, 150 * 16)
    p.drawArc(QRectF(8 * s, 8 * s, 18 * s, 18 * s), 210 * 16, 150 * 16)
    p.setBrush(QColor("#FFFFFF"))
    p.setPen(Qt.NoPen)
    from PySide6.QtGui import QPolygonF
    p.drawPolygon(QPolygonF([QPointF(24.5 * s, 6 * s), QPointF(28 * s, 13 * s), QPointF(20.5 * s, 12 * s)]))
    p.drawPolygon(QPolygonF([QPointF(9.5 * s, 28 * s), QPointF(6 * s, 21 * s), QPointF(13.5 * s, 22 * s)]))
    p.end()
    return pm


def _logoff_icon(size=34):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 34
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#FFC85A"))
    g.setColorAt(1, QColor("#E07A10"))
    p.setPen(QPen(QColor("#FFFFFF"), 1.6 * s))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(1.5 * s, 1.5 * s, 31 * s, 31 * s), 5 * s, 5 * s)
    p.setPen(QPen(QColor("#FFFFFF"), 2.4 * s))
    p.setBrush(Qt.NoBrush)
    p.drawRect(QRectF(8 * s, 8 * s, 12 * s, 18 * s))                    # the door
    p.setPen(QPen(QColor("#FFFFFF"), 2.8 * s, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(15 * s, 17 * s), QPointF(27 * s, 17 * s))         # the arrow out of it
    path = QPainterPath(QPointF(23 * s, 13 * s))
    path.lineTo(QPointF(27 * s, 17 * s))
    path.lineTo(QPointF(23 * s, 21 * s))
    p.drawPath(path)
    p.end()
    return pm


def _windows_flag(p, x, y, s):
    for (dx, dy, c) in ((0, 0, "#F05A28"), (1, 0, "#7FBA00"), (0, 1, "#00A4EF"), (1, 1, "#FFB900")):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(c))
        p.drawRoundedRect(QRectF(x + dx * 9 * s, y + dy * 9 * s, 8 * s, 8 * s), 1.5 * s, 1.5 * s)


class LogOffScreen(QWidget):
    """Covers the whole desktop: the faded screenshot and the Log Off box in the middle."""

    def __init__(self, desktop, on_switch, on_logoff):
        super().__init__(desktop)
        self.desktop = desktop
        self.on_switch, self.on_logoff = on_switch, on_logoff
        self.setGeometry(desktop.rect())
        self.shot = desktop.grab().toImage()
        self.grey = self.shot.convertToFormat(QImage.Format_Grayscale8).convertToFormat(QImage.Format_RGB32)
        self.t0 = time.monotonic()
        self.hover = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.icons = {"switch": _switch_icon(), "logoff": _logoff_icon()}
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(40)
        self.show()
        self.raise_()
        self.setFocus()

    def _box(self):
        return QRect((self.width() - BOX_W) // 2, (self.height() - BOX_H) // 2, BOX_W, BOX_H)

    def _buttons(self):
        b = self._box()
        y = b.top() + 70
        return {"switch": QRect(b.left() + 60, y, 80, 70), "logoff": QRect(b.left() + 172, y, 80, 70),
                "cancel": QRect(b.right() - 86, b.bottom() - 32, 75, 22)}

    def paintEvent(self, _e):
        p = QPainter(self)
        p.drawImage(0, 0, self.shot)
        fade = min(1.0, (time.monotonic() - self.t0) / FADE_SECONDS)
        if fade >= 1.0:
            self.timer.stop()
        p.setOpacity(fade)
        p.drawImage(0, 0, self.grey)
        p.setOpacity(1.0)
        p.setRenderHint(QPainter.Antialiasing)
        b = self._box()
        # three bands: dark title, lighter middle, dark bottom
        p.setPen(QPen(QColor("#00136B"), 1))
        p.setBrush(QColor("#5A7EDC"))
        p.drawRect(b.adjusted(0, 0, -1, -1))
        top = QRect(b.left(), b.top(), b.width(), 48)
        g = QLinearGradient(0, top.top(), 0, top.bottom())
        g.setColorAt(0, QColor("#0A246A"))
        g.setColorAt(1, QColor("#0E3A9C"))
        p.fillRect(top.adjusted(1, 1, -1, 0), g)
        bottom = QRect(b.left(), b.bottom() - 44, b.width(), 45)
        p.fillRect(bottom.adjusted(1, 0, -1, -1), QColor("#0E3A9C"))
        p.setPen(QPen(QColor("#F0A030"), 2))
        p.drawLine(top.bottomLeft() + QPointF(1, 0).toPoint(), top.bottomRight())
        p.setPen(QColor("#FFFFFF"))
        p.setFont(QFont("Franklin Gothic Medium", 14))
        p.drawText(top.adjusted(14, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, "Log Off Windows")
        _windows_flag(p, top.right() - 34, top.top() + 13, 1.2)
        # the two buttons
        p.setFont(QFont("Tahoma", 9))
        for key, label in (("switch", "Switch User"), ("logoff", "Log Off")):
            r = self._buttons()[key]
            icon = self.icons[key]
            if self.hover == key:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 255, 255, 40))
                p.drawRoundedRect(QRectF(r.center().x() - 24, r.top() - 4, 48, 46), 6, 6)
            p.drawPixmap(r.center().x() - icon.width() // 2, r.top(), icon)
            p.setPen(QColor("#FFFFFF"))
            p.drawText(QRect(r.left() - 10, r.top() + 40, r.width() + 20, 20), Qt.AlignHCenter | Qt.AlignTop, label)
        c = self._buttons()["cancel"]
        p.setPen(QPen(QColor("#003C74"), 1))
        g2 = QLinearGradient(0, c.top(), 0, c.bottom())
        g2.setColorAt(0, QColor("#FFFFFF") if self.hover != "cancel" else QColor("#FFF4D8"))
        g2.setColorAt(1, QColor("#E3E3DB"))
        p.setBrush(g2)
        p.drawRoundedRect(QRectF(c).adjusted(0.5, 0.5, -0.5, -0.5), 3, 3)
        p.setPen(QColor("#000000"))
        p.setFont(QFont("Tahoma", 8))
        p.drawText(c, Qt.AlignCenter, "Cancel")
        p.end()

    def _at(self, pos):
        for key, r in self._buttons().items():
            if r.contains(pos):
                return key
        return None

    def mouseMoveEvent(self, e):
        key = self._at(e.position().toPoint())
        if key != self.hover:
            self.hover = key
            self.setCursor(Qt.PointingHandCursor if key else Qt.ArrowCursor)
            self.update()

    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        key = self._at(e.position().toPoint())
        if key == "switch":
            self._close()
            self.on_switch()
        elif key == "logoff":
            self._close()
            self.on_logoff()
        elif key == "cancel":
            self._close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self._close()

    def _close(self):
        self.timer.stop()
        self.hide()
        self.deleteLater()


def ask(desktop):
    """Start > Log Off: the box (the desktop's switch_user_requested / logoff_requested signals do the rest)."""
    sound.play("menu")
    desktop.hide_start_menu()
    QTimer.singleShot(0, lambda: LogOffScreen(desktop, desktop.switch_user_requested.emit,
                                              desktop.logoff_requested.emit))
