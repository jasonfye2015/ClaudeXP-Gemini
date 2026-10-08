"""Notification-area icons for hosted programs, and XP's yellow balloon tips."""
from PySide6.QtCore import QObject, QPointF, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QSystemTrayIcon, QWidget
from shiboken6 import isValid


class TrayIcon(QObject):
    """Same interface as QSystemTrayIcon (the parts programs use), but lives in the XP taskbar."""
    activated = Signal(QSystemTrayIcon.ActivationReason)
    messageClicked = Signal()

    def __init__(self, desktop, icon=None, parent=None):
        super().__init__(parent)
        self.desktop = desktop
        self._icon = icon or QIcon()
        self._tooltip = ""
        self._menu = None
        self._visible = False
        self.destroyed.connect(lambda *_: desktop.taskbar.remove_tray_icon(self)
                               if isValid(desktop.taskbar) else None)

    def setIcon(self, icon):
        self._icon = icon
        self.desktop.taskbar.update()

    def icon(self):
        return self._icon

    def setToolTip(self, text):
        self._tooltip = text

    def toolTip(self):
        return self._tooltip

    def setContextMenu(self, menu):
        self._menu = menu

    def contextMenu(self):
        return self._menu

    def show(self):
        self._visible = True
        self.desktop.taskbar.add_tray_icon(self)

    def hide(self):
        self._visible = False
        self.desktop.taskbar.remove_tray_icon(self)
        self.desktop.balloon.dismiss(self)

    def setVisible(self, visible):
        self.show() if visible else self.hide()

    def isVisible(self):
        return self._visible

    def showMessage(self, title, message, icon=None, msecs=10000):
        if self._visible:
            self.desktop.balloon.pop(self, title, message, msecs)


class Balloon(QWidget):
    """The yellow XP balloon tip pointing at a tray icon."""
    WIDTH = 270
    TAIL = 16
    PAD = 10

    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.owner = None
        self.title = ""
        self.message = ""
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)
        self.hide()

    def pop(self, owner, title, message, msecs):
        self.owner, self.title, self.message = owner, title, message
        anchor = self.desktop.taskbar.tray_icon_center(owner)
        if anchor is None:
            return
        title_font, body_font = self._fonts()
        text_w = self.WIDTH - 2 * self.PAD - 18
        title_h = QFontMetrics(title_font).boundingRect(
            QRect(0, 0, text_w, 1000), Qt.TextWordWrap, title).height()
        body_h = QFontMetrics(body_font).boundingRect(
            QRect(0, 0, self.WIDTH - 2 * self.PAD, 1000), Qt.TextWordWrap, message).height()
        box_h = self.PAD + title_h + 6 + body_h + self.PAD
        x = min(self.desktop.width() - self.WIDTH - 6, anchor.x() - self.WIDTH + 40)
        y = self.desktop.taskbar.y() - box_h - self.TAIL
        self.setGeometry(max(4, x), y, self.WIDTH, box_h + self.TAIL)
        self.tail_x = anchor.x() - self.x()
        self.title_h = title_h
        self.show()
        self.raise_()
        self.update()
        self.timer.start(max(1000, msecs))

    def dismiss(self, owner=None):
        if owner is None or owner is self.owner:
            self.timer.stop()
            self.hide()

    @staticmethod
    def _fonts():
        title = QFont("Tahoma", 8)
        title.setBold(True)
        return title, QFont("Tahoma", 8)

    def mousePressEvent(self, event):
        owner = self.owner
        self.dismiss()
        if owner is not None and isValid(owner) and not self._close_rect().contains(event.position().toPoint()):
            owner.messageClicked.emit()

    def _close_rect(self):
        return QRect(self.width() - self.PAD - 12, self.PAD - 1, 13, 13)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        box = QRectF(0.5, 0.5, self.width() - 1, self.height() - self.TAIL - 1)
        path = QPainterPath()
        path.addRoundedRect(box, 7, 7)
        tx = max(20.0, min(float(self.tail_x), self.width() - 6.0))
        tail = QPainterPath()
        tail.addPolygon(QPolygonF([QPointF(tx - 24, box.bottom() - 1), QPointF(tx - 6, box.bottom() - 1),
                                   QPointF(tx, self.height() - 1.0)]))
        path = path.united(tail)
        p.setPen(QPen(QColor("#4D4D4D"), 1))
        p.setBrush(QColor("#FFFFE1"))
        p.drawPath(path)

        title_font, body_font = self._fonts()
        icon = self.owner.icon() if self.owner is not None and isValid(self.owner) else QIcon()
        x = self.PAD
        if not icon.isNull():
            p.drawPixmap(x, self.PAD, icon.pixmap(16, 16))
            x += 20
        p.setPen(QColor("black"))
        p.setFont(title_font)
        p.drawText(QRect(x, self.PAD + 1, self.width() - x - self.PAD - 16, self.title_h),
                   Qt.TextWordWrap, self.title)
        p.setFont(body_font)
        body_top = self.PAD + max(self.title_h, 16) + 6
        p.drawText(QRect(self.PAD, body_top, self.width() - 2 * self.PAD, int(box.bottom()) - body_top),
                   Qt.TextWordWrap, self.message)

        c = self._close_rect()
        p.setPen(QPen(QColor("#8C8C8C"), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(c).adjusted(0.5, 0.5, -0.5, -0.5), 2, 2)
        p.setPen(QPen(QColor("#4D4D4D"), 1.5))
        p.drawLine(c.x() + 4, c.y() + 4, c.right() - 3, c.bottom() - 3)
        p.drawLine(c.right() - 3, c.y() + 4, c.x() + 4, c.bottom() - 3)
