"""The Windows 11 lock screen and sign-in: the lock screen picture with the big clock, then (a click, a key) the
same picture blurred behind your account picture, your name, the PIN box, 'Sign-in options', and the network,
accessibility and power buttons in the corner. Locking the computer comes back to the lock screen."""
from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QLineEdit, QMenu, QWidget

from . import clock, sound, user
from .bios import draw_logo


class LogonScreen(QWidget):
    logged_on = Signal()
    shut_down = Signal()
    restart = Signal()
    sleep = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.locked = False
        self.status_lines = []
        self.stage = "lock"                 # "lock" (the picture and the clock) or "signin"
        self.error = ""
        self.hover = None
        self.offset = 0.0                   # the lock screen sliding up
        self.slide = QTimer(self)
        self.slide.timeout.connect(self._slide_tick)
        self._cache = {}
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update)
        self.clock_timer.start(1000)
        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("PIN")
        self.password.setAlignment(Qt.AlignCenter)
        self.password.setStyleSheet(
            "QLineEdit { background: rgba(255,255,255,0.9); color: #1A1A1A; border: 1px solid rgba(255,255,255,0.4);"
            " border-bottom: 2px solid #0067C0; border-radius: 4px; padding: 4px 36px 4px 12px;"
            " font-family: 'Segoe UI'; font-size: 15px; }")
        self.password.returnPressed.connect(self._submit)
        self.password.hide()

    # ---- state ----
    def reset(self, locked=False, status_lines=None):
        self.locked = locked
        self.status_lines = list(status_lines or [])
        self.error = ""
        self.stage = "lock"
        self.offset = 0.0
        self.slide.stop()
        self.password.clear()
        self.password.hide()
        self._layout()
        self.update()
        self.setFocus()

    def _layout(self):
        w = 300
        self.password.setGeometry((self.width() - w) // 2, self._name_bottom() + 18, w, 36)

    def resizeEvent(self, event):
        self._layout()

    def _lock_pixmap(self):
        from . import display
        path = display.get().lock_image()
        key = (str(path), self.width(), self.height())
        if key not in self._cache:
            pm = display.load_image(path) if path else QPixmap()
            if pm.isNull():
                pm = display.bloom(self.width(), self.height())
            else:
                scale = max(self.width() / pm.width(), self.height() / pm.height())
                pm = pm.scaled(int(pm.width() * scale) + 1, int(pm.height() * scale) + 1, Qt.IgnoreAspectRatio,
                               Qt.SmoothTransformation)
            self._cache = {key: pm}
        return self._cache[key]

    def _blurred(self):
        """The lock picture, blurred for the sign-in screen (a cheap blur: shrink, grow, darken)."""
        pm = self._lock_pixmap()
        key = ("blur", pm.cacheKey())
        if key not in self._cache:
            small = pm.scaled(max(1, pm.width() // 24), max(1, pm.height() // 24), Qt.IgnoreAspectRatio,
                              Qt.SmoothTransformation)
            big = small.scaled(pm.width(), pm.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            p = QPainter(big)
            p.fillRect(big.rect(), QColor(0, 0, 0, 70))
            p.end()
            self._cache[key] = big
        return self._cache[key]

    # ---- the lock screen lifting ----
    def _wake(self):
        if self.stage != "lock":
            return
        self.stage = "signin"
        self.offset = 0.0
        self.slide.start(16)
        sound.play("unlock") if self.locked else None

    def _slide_tick(self):
        self.offset = min(1.0, self.offset + 0.07)
        if self.offset >= 1.0:
            self.slide.stop()
            self.password.setVisible(user.has_windows_password() and not self.error)
            if user.has_windows_password():
                self.password.setFocus()
        self.update()

    # ---- signing in ----
    def _submit(self):
        if self.error:
            return
        if user.has_windows_password() and not user.check_windows_password(self.password.text()):
            self.error = "The PIN is incorrect. Try again."
            self.password.clear()
            self.password.hide()
            sound.play("critical")
            self.update()
            return
        sound.play("user_select")
        self.logged_on.emit()

    def _clear_error(self):
        self.error = ""
        self.password.setVisible(user.has_windows_password())
        self.password.setFocus()
        self.update()

    def keyPressEvent(self, event):
        key = event.key()
        if self.stage == "lock":
            self._wake()
            return
        if key in (Qt.Key_Return, Qt.Key_Enter):
            if self.error:
                self._clear_error()
            else:
                self._submit()
        elif key == Qt.Key_Escape:
            if self.error:
                self._clear_error()
            else:
                self.reset(self.locked, self.status_lines)
        else:
            super().keyPressEvent(event)

    # ---- geometry of the sign-in screen ----
    def _pic_rect(self):
        d = 180
        return QRect((self.width() - d) // 2, int(self.height() * 0.5) - d - 40, d, d)

    def _name_bottom(self):
        return self._pic_rect().bottom() + 56

    def _corner_buttons(self):
        """[(name, rect)] of the network, accessibility and power buttons, bottom right."""
        out = []
        x = self.width() - 36 - 40
        y = self.height() - 36 - 40
        for name in ("power", "ease", "network"):
            out.append((name, QRect(x, y, 40, 40)))
            x -= 48
        return out

    def _options_rect(self):
        f = QFont("Segoe UI")
        f.setPixelSize(13)
        tw = QFontMetrics(f).horizontalAdvance("Sign-in options")
        return QRect((self.width() - tw) // 2 - 10, self._name_bottom() + 70, tw + 20, 24)

    def _go_rect(self):
        pw = self.password.geometry()
        return QRect(pw.right() - 32, pw.top() + 4, 28, 28)

    # ---- mouse ----
    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        hover = None
        if self.stage == "signin":
            for name, r in self._corner_buttons():
                if r.contains(pos):
                    hover = name
            if self._options_rect().contains(pos):
                hover = "options"
            if self._pic_rect().contains(pos):
                hover = "pic"
        if hover != self.hover:
            self.hover = hover
            self.setCursor(Qt.PointingHandCursor if hover else Qt.ArrowCursor)
            self.update()

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        if self.stage == "lock":
            self._wake()
            return
        if self.error:
            self._clear_error()
            return
        for name, r in self._corner_buttons():
            if r.contains(pos):
                {"power": self._power_menu, "ease": self._ease_menu, "network": self._network_tip}[name](r)
                return
        if self._pic_rect().contains(pos) or (self._go_rect().contains(pos) and self.password.isVisible()):
            self._submit()
            return
        if self._options_rect().contains(pos):
            self._options_menu()

    def _menu(self):
        from .shims import MENU_CSS
        menu = QMenu(self)
        menu.setStyleSheet(MENU_CSS)
        return menu

    def _power_menu(self, rect):
        menu = self._menu()
        menu.addAction("Sleep", self.sleep.emit)
        menu.addAction("Shut down", self.shut_down.emit)
        menu.addAction("Restart", self.restart.emit)
        menu.popup(self.mapToGlobal(rect.topLeft()) - QPointF(0, 110).toPoint())

    def _ease_menu(self, rect):
        menu = self._menu()
        for name in ("Narrator", "Magnifier", "On-Screen Keyboard", "High contrast", "Sticky Keys", "Filter Keys"):
            menu.addAction(name, lambda n=name: None)
        menu.popup(self.mapToGlobal(rect.topLeft()) - QPointF(0, 180).toPoint())

    def _network_tip(self, rect):
        menu = self._menu()
        menu.addAction("Wi-Fi: HomeNetwork - Connected, secured").setEnabled(False)
        menu.popup(self.mapToGlobal(rect.topLeft()) - QPointF(0, 40).toPoint())

    def _options_menu(self):
        menu = self._menu()
        menu.addAction("PIN" if user.has_windows_password() else "No PIN set: click your picture to sign in")
        menu.addAction("Password", lambda: self.password.setPlaceholderText("Password"))
        menu.addAction("Windows Hello face: no camera", lambda: None).setEnabled(False)
        r = self._options_rect()
        menu.popup(self.mapToGlobal(r.bottomLeft()))

    # ---- painting ----
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.setRenderHint(QPainter.Antialiasing)
        if self.stage == "lock" or self.offset < 1.0:
            self._paint_lock(p, lift=int(self.offset * self.height()))
        if self.stage == "signin":
            self._paint_signin(p, alpha=self.offset)

    def _paint_lock(self, p, lift=0):
        pm = self._lock_pixmap()
        p.save()
        p.translate(0, -lift)
        p.drawPixmap(0, 0, pm)
        g = QLinearGradient(0, self.height() * 0.55, 0, self.height())
        g.setColorAt(0, QColor(0, 0, 0, 0))
        g.setColorAt(1, QColor(0, 0, 0, 110))
        p.fillRect(self.rect(), g)
        # the clock, big, centred near the bottom
        from .style import display_family
        f = QFont(display_family())
        f.setPixelSize(max(60, self.height() // 7))
        f.setWeight(QFont.Light)
        p.setFont(f)
        now = clock.now()
        time_text = clock.time_text(now).rsplit(" ", 1)[0]
        base = int(self.height() * 0.84)
        p.setPen(QColor(0, 0, 0, 90))
        p.drawText(QRectF(2, base - f.pixelSize() + 2, self.width(), f.pixelSize() + 10), Qt.AlignCenter, time_text)
        p.setPen(QColor("white"))
        p.drawText(QRectF(0, base - f.pixelSize(), self.width(), f.pixelSize() + 10), Qt.AlignCenter, time_text)
        f = QFont("Segoe UI")
        f.setPixelSize(max(18, self.height() // 32))
        p.setFont(f)
        date = f"{now:%A, %B} {now.day}"
        p.setPen(QColor(0, 0, 0, 90))
        p.drawText(QRectF(1, base + 13, self.width(), 40), Qt.AlignCenter, date)
        p.setPen(QColor("white"))
        p.drawText(QRectF(0, base + 12, self.width(), 40), Qt.AlignCenter, date)
        p.restore()

    def _paint_signin(self, p, alpha=1.0):
        p.setOpacity(alpha)
        p.drawPixmap(0, 0, self._blurred())
        p.setOpacity(1.0 if alpha >= 1.0 else alpha)
        pic = self._pic_rect()
        if self.hover == "pic":
            p.setPen(QPen(QColor(255, 255, 255, 160), 3))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(pic).adjusted(-4, -4, 4, 4))
        user.draw_user_picture(p, pic, circle=True)
        f = QFont("Segoe UI")
        f.setPixelSize(28)
        f.setWeight(QFont.Normal)
        p.setFont(f)
        name = user.user_name()
        nr = QRect(0, pic.bottom() + 14, self.width(), 40)
        p.setPen(QColor(0, 0, 0, 100))
        p.drawText(nr.translated(1, 1), Qt.AlignCenter, name)
        p.setPen(QColor("white"))
        p.drawText(nr, Qt.AlignCenter, name)
        f.setPixelSize(13)
        p.setFont(f)
        y = self._name_bottom() + 18
        if self.error:
            p.setPen(QColor("white"))
            p.drawText(QRect(0, y, self.width(), 40), Qt.AlignCenter, self.error + "\nPress Enter or click to try again.")
            return
        if not user.has_windows_password():
            p.setPen(QColor(235, 240, 250))
            p.drawText(QRect(0, y + 8, self.width(), 24), Qt.AlignCenter, "Click your picture to sign in")
        else:
            # the arrow in the PIN box
            gr = self._go_rect()
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#0067C0"))
            p.drawRoundedRect(QRectF(gr), 4, 4)
            pen = QPen(QColor("white"), 1.6)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            c = gr.center()
            p.drawLine(QPointF(c.x() - 5, c.y()), QPointF(c.x() + 5, c.y()))
            p.drawLine(QPointF(c.x() + 1, c.y() - 4), QPointF(c.x() + 5, c.y()))
            p.drawLine(QPointF(c.x() + 1, c.y() + 4), QPointF(c.x() + 5, c.y()))
        lines = (["Locked"] if self.locked else []) + self.status_lines
        ly = y + 44
        p.setPen(QColor(235, 240, 250, 220))
        for line in lines:
            p.drawText(QRect(0, ly, self.width(), 20), Qt.AlignCenter, line)
            ly += 20
        opt = self._options_rect()
        p.setPen(QColor("white") if self.hover == "options" else QColor(235, 240, 250, 230))
        p.drawText(opt, Qt.AlignCenter, "Sign-in options")
        # the corner buttons
        for name, r in self._corner_buttons():
            if self.hover == name:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 255, 255, 40))
                p.drawRoundedRect(QRectF(r), 6, 6)
            self._glyph(p, name, r)

    @staticmethod
    def _glyph(p, name, r):
        c = r.center()
        pen = QPen(QColor("white"), 1.6)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        if name == "power":
            p.drawArc(QRectF(c.x() - 8, c.y() - 7, 16, 16), 60 * 16, 300 * 16)
            p.drawLine(QPointF(c.x(), c.y() - 10), QPointF(c.x(), c.y() - 1))
        elif name == "ease":
            p.setBrush(QColor("white"))
            p.drawEllipse(QPointF(c.x(), c.y() - 7), 2.2, 2.2)
            p.setBrush(Qt.NoBrush)
            p.drawLine(QPointF(c.x() - 7, c.y() - 2), QPointF(c.x() + 7, c.y() - 2))
            p.drawLine(QPointF(c.x(), c.y() - 2), QPointF(c.x(), c.y() + 3))
            p.drawLine(QPointF(c.x(), c.y() + 3), QPointF(c.x() - 5, c.y() + 10))
            p.drawLine(QPointF(c.x(), c.y() + 3), QPointF(c.x() + 5, c.y() + 10))
        else:
            for i, rad in enumerate((4, 8, 12)):
                p.setPen(QPen(QColor("white"), 1.6))
                p.drawArc(QRectF(c.x() - rad, c.y() + 4 - rad, 2 * rad, 2 * rad), 45 * 16, 90 * 16)
            p.setBrush(QColor("white"))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(c.x(), c.y() + 5), 1.8, 1.8)

    @staticmethod
    def _flag(p, x, y, size):
        """The Windows 11 logo (the period code asks for the flag by this name)."""
        draw_logo(p, x + size / 2, y + size / 2, size / 2, "#0078D4", glow=False)
