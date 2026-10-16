"""The XP Welcome screen: 'To begin, click your user name'."""
from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QLineEdit, QPushButton, QWidget

from . import sound
from .paths import pixmap
from .user import draw_user_picture, user_name

TILE_W, TILE_H = 340, 76
PIC = 56


class WelcomeScreen(QWidget):
    logged_on = Signal()
    turn_off = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logo = pixmap("xp_logo.png")
        self.setMouseTracking(True)
        self.hover = None        # "user" or "turnoff"
        from .user import account
        account().changed.connect(self.update)
        self.loading = False
        self.prompting = False       # showing the password box
        self.bad_password = False
        self.pw = QLineEdit(self)
        self.pw.setEchoMode(QLineEdit.Password)
        self.pw.setFixedSize(170, 24)
        self.pw.setStyleSheet("QLineEdit { border: 1px solid #1C3D91; border-radius: 3px; padding: 1px 4px;"
                              " font-family: Tahoma; font-size: 12px; }")
        self.pw.returnPressed.connect(self._submit)
        self.go = QPushButton("➜", self)
        self.go.setFixedSize(24, 24)
        self.go.setCursor(Qt.PointingHandCursor)
        self.go.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7FD46A,"
                              " stop:1 #2E9A1A); color: white; border: 1px solid #FFFFFF; border-radius: 4px;"
                              " font-size: 14px; font-weight: bold; }")
        self.go.clicked.connect(self._submit)
        self.pw.hide()
        self.go.hide()
        self.status_lines = []

    def reset(self):
        self.status_lines = []           # 'N programs running' after Switch User
        self.loading = False
        self.hover = None
        self.prompting = False
        self.bad_password = False
        self.pw.hide()
        self.go.hide()
        self.pw.clear()
        self.update()

    def _place_password(self):
        r = self._tile_rect()
        x = r.x() + 10 + PIC + 14
        self.pw.move(x, r.center().y() + 6)
        self.go.move(x + self.pw.width() + 6, r.center().y() + 6)

    def resizeEvent(self, event):
        self._place_password()

    def _submit(self):
        from .user import check_windows_password
        if check_windows_password(self.pw.text()):
            self.pw.hide()
            self.go.hide()
            self.prompting = False
            self.bad_password = False
            self._log_on()
        else:
            self.bad_password = True
            sound.play("default")
            self.pw.selectAll()
            self.pw.setFocus()
            self.update()

    def _log_on(self):
        self.loading = True
        self.hover = "user"
        self.unsetCursor()
        self.update()
        QTimer.singleShot(1800, self.logged_on.emit)

    # ---- layout -------------------------------------------------------------
    def _bands(self):
        top = max(50, int(self.height() * 0.11))
        bottom = max(60, int(self.height() * 0.13))
        return top, bottom

    def _divider_x(self):
        return self.width() // 2

    def _tile_rect(self):
        x = self._divider_x() + 28
        y = self.height() // 2 - TILE_H // 2 - 10
        return QRect(x, y, TILE_W, TILE_H)

    def _turnoff_rect(self):
        _, bottom = self._bands()
        return QRect(28, self.height() - bottom + (bottom - 30) // 2, 170, 30)

    def _item_at(self, pos):
        if self._tile_rect().contains(pos):
            return "user"
        if self._turnoff_rect().contains(pos):
            return "turnoff"
        return None

    # ---- events -------------------------------------------------------------
    def mouseMoveEvent(self, event):
        if self.loading:
            return
        item = self._item_at(event.position().toPoint())
        if item != self.hover:
            self.hover = item
            self.setCursor(Qt.PointingHandCursor if item else Qt.ArrowCursor)
            self.update()

    def leaveEvent(self, event):
        if self.hover and not self.loading:
            self.hover = None
            self.update()

    def mousePressEvent(self, event):
        if self.loading or event.button() != Qt.LeftButton:
            return
        item = self._item_at(event.position().toPoint())
        if item == "user":
            from .user import has_windows_password
            if has_windows_password():
                if not self.prompting:
                    self.prompting = True
                    self.hover = "user"
                    self._place_password()
                    self.pw.show()
                    self.go.show()
                    self.pw.setFocus()
                    self.update()
                return
            self._log_on()
        elif item == "turnoff":
            sound.play("menu")
            self.turn_off.emit()

    # ---- painting -----------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        w, h = self.width(), self.height()
        top, bottom = self._bands()

        # Background: XP blue with a soft glow in the upper left.
        p.fillRect(self.rect(), QColor("#5A7EDC"))
        glow = QRadialGradient(QPointF(w * 0.08, top + 10), w * 0.45)
        glow.setColorAt(0, QColor(160, 190, 250, 150))
        glow.setColorAt(1, QColor(160, 190, 250, 0))
        p.fillRect(self.rect(), glow)

        # Top and bottom bands, with the white and orange highlight lines.
        p.fillRect(0, 0, w, top, QColor("#00309C"))
        p.fillRect(0, h - bottom, w, bottom, QColor("#00309C"))
        self._fade_line(p, top, QColor(255, 255, 255), 0.05, 0.45)
        self._fade_line(p, h - bottom - 1, QColor("#F99736"), 0.0, 0.5)

        # Vertical divider.
        dx = self._divider_x()
        vg = QLinearGradient(0, top + 30, 0, h - bottom - 30)
        vg.setColorAt(0, QColor(255, 255, 255, 0))
        vg.setColorAt(0.5, QColor(255, 255, 255, 200))
        vg.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillRect(QRectF(dx, top + 30, 1, h - top - bottom - 60), vg)

        self._draw_logo(p, dx)
        self._draw_tile(p)
        self._draw_turnoff(p)

        # Bottom right hint text.
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("white"))
        hint = QRect(dx + 28, h - bottom, w - dx - 40, bottom)
        p.drawText(hint, Qt.AlignVCenter | Qt.AlignLeft,
                   "After you log on, you can add or change accounts.\n"
                   "Just go to Control Panel and click User Accounts.")

    def _fade_line(self, p, y, color, peak_from, peak_to):
        g = QLinearGradient(0, 0, self.width(), 0)
        clear = QColor(color)
        clear.setAlpha(0)
        g.setColorAt(0, clear if peak_from > 0 else color)
        g.setColorAt(max(0.0, peak_from), color)
        g.setColorAt(peak_to, color)
        g.setColorAt(1, clear)
        p.fillRect(QRectF(0, y, self.width(), 2), g)

    def _draw_logo(self, p, dx):
        if self.logo.isNull():
            return
        lw = min(dx - 60, 300)
        lh = lw * self.logo.height() / self.logo.width()
        x = dx - 30 - lw
        y = self.height() / 2 - lh / 2 - 30
        p.drawPixmap(QRectF(x, y, lw, lh), self.logo, QRectF(self.logo.rect()))
        font = QFont("Franklin Gothic Medium", 14)
        p.setFont(font)
        p.setPen(QColor("white"))
        text = "Please wait..." if self.loading else "To begin, click your user name"
        p.drawText(QRectF(x - 120, y + lh + 14, lw + 120, 30), Qt.AlignRight | Qt.AlignTop, text)

    def _draw_tile(self, p):
        r = self._tile_rect()
        active = self.hover == "user"
        if active:
            g = QLinearGradient(r.left(), 0, r.right(), 0)
            g.setColorAt(0, QColor("#00309C"))
            g.setColorAt(1, QColor(0, 48, 156, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(g)
            p.drawRoundedRect(QRectF(r), 8, 8)

        pic = QRect(r.x() + 10, r.center().y() - PIC // 2, PIC, PIC)
        p.setOpacity(1.0 if active else 0.75)
        draw_user_picture(p, pic)
        p.setOpacity(1.0)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor("#FFC83C") if active else QColor("white"), 3 if active else 2))
        p.drawRoundedRect(QRectF(pic).adjusted(-1, -1, 1, 1), 4, 4)

        name_font = QFont("Tahoma", 14)
        p.setFont(name_font)
        p.setPen(QColor("white"))
        text_x = pic.right() + 14
        if self.prompting:
            p.drawText(QRect(text_x, r.y() - 6, r.right() - text_x, r.height() // 2 - 4),
                       Qt.AlignBottom | Qt.AlignLeft, user_name())
            p.setFont(QFont("Tahoma", 8))
            p.setPen(QColor("#D6E2FF"))
            p.drawText(QRect(text_x, r.center().y() - 12, r.right() - text_x, 16), Qt.AlignLeft,
                       "Type your password")
            if self.bad_password:
                self._draw_hint(p, QRect(text_x - 20, r.bottom() + 10, 300, 70))
        elif self.loading:
            p.drawText(QRect(text_x, r.y() + 8, r.right() - text_x, r.height() // 2 - 4),
                       Qt.AlignBottom | Qt.AlignLeft, user_name())
            p.setFont(QFont("Tahoma", 9))
            p.setPen(QColor("#D6E2FF"))
            p.drawText(QRect(text_x, r.center().y() + 4, r.right() - text_x, 20),
                       Qt.AlignTop | Qt.AlignLeft, "Loading your personal settings...")
        elif self.status_lines:
            p.drawText(QRect(text_x, r.y() + 2, r.right() - text_x, r.height() // 2 - 2),
                       Qt.AlignBottom | Qt.AlignLeft, user_name())
            p.setFont(QFont("Tahoma", 8))
            p.setPen(QColor("#D6E2FF"))
            for i, line in enumerate(self.status_lines[:2]):
                p.drawText(QRect(text_x, r.center().y() + 2 + i * 14, r.right() - text_x, 14),
                           Qt.AlignTop | Qt.AlignLeft, line)
        else:
            p.drawText(QRect(text_x, r.y(), r.right() - text_x, r.height()),
                       Qt.AlignVCenter | Qt.AlignLeft, user_name())

    def _draw_hint(self, p, box):
        """XP's yellow 'Did you forget your password?' balloon."""
        p.setPen(QPen(QColor("#000000"), 1))
        p.setBrush(QColor("#FFFFE1"))
        p.drawRoundedRect(QRectF(box), 6, 6)
        p.setFont(QFont("Tahoma", 8, QFont.Bold))
        p.drawText(box.adjusted(10, 6, -8, 0), Qt.AlignLeft | Qt.AlignTop, "Did you forget your password?")
        p.setFont(QFont("Tahoma", 8))
        p.drawText(box.adjusted(10, 24, -8, -4), Qt.AlignLeft | Qt.TextWordWrap,
                   "Please type your password again. Be sure to use the correct uppercase and lowercase letters.")

    def _draw_turnoff(self, p):
        r = self._turnoff_rect()
        box = QRectF(r.x(), r.center().y() - 13, 26, 26)
        g = QLinearGradient(0, box.top(), 0, box.bottom())
        base = QColor("#E0582F").lighter(115 if self.hover == "turnoff" else 100)
        g.setColorAt(0, base.lighter(135))
        g.setColorAt(1, base)
        p.setPen(QPen(QColor("white"), 1.5))
        p.setBrush(g)
        p.drawRoundedRect(box, 4, 4)
        c = box.center()
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor("white"), 2))
        p.drawArc(QRectF(c.x() - 6, c.y() - 5, 12, 12), 120 * 16, 300 * 16)
        p.drawLine(QPointF(c.x(), c.y() - 8), QPointF(c.x(), c.y()))
        font = QFont("Tahoma", 10)
        font.setUnderline(self.hover == "turnoff")
        p.setFont(font)
        p.setPen(QColor("white"))
        p.drawText(r.adjusted(36, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, "Turn off computer")
