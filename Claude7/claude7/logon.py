"""The Windows 7 logon screen: your user tile in its glass frame over the blue, the password box, Switch User,
the power button in the corner, 'Windows 7 Home Premium' at the bottom. Locking the computer comes back here with
'Locked' under your name and what's still running."""
from PySide6.QtCore import QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QLineEdit, QPushButton, QWidget

from . import sound, user
from .paths import IMAGES

DESIGN_W, DESIGN_H = 1280, 720
TILE = (598, 290, 83, 83)
FRAME = (589, 282, 100, 99)
NAME = (480, 384, 320, 26)
PASSWORD = (565, 423, 150, 26)
GO = (720, 423, 30, 26)
SWITCH = (600, 468, 79, 21)
LOGON_DIR = IMAGES / "logon"


class PowerMenu(QWidget):
    """The little menu above the power button: Restart, Sleep, Shut Down (the seed's artwork)."""
    chosen = Signal(str)
    ROWS = {"restart": (0.0, 0.34), "sleep": (0.45, 0.70), "shutdown": (0.70, 1.0)}

    def __init__(self, parent):
        super().__init__(parent)
        self.images = {name: QPixmap(str(LOGON_DIR / f)) for name, f in (
            ("menu", "Button_Power_Menu.jpg"), ("restart", "Button_Power_Menu_Restart_Highlight.jpg"),
            ("sleep", "Button_Power_Menu_Sleep_Highlight.jpg"),
            ("shutdown", "Button_Power_Menu_Shutdown_Highlight.jpg"))}
        self.hover = None
        self.setMouseTracking(True)
        self.hide()

    def _at(self, y):
        frac = y / max(1, self.height())
        for name, (lo, hi) in self.ROWS.items():
            if lo <= frac < hi:
                return name
        return None

    def mouseMoveEvent(self, event):
        h = self._at(event.position().y())
        if h != self.hover:
            self.hover = h
            self.update()

    def leaveEvent(self, event):
        self.hover = None
        self.update()

    def mousePressEvent(self, event):
        h = self._at(event.position().y())
        if h:
            self.chosen.emit(h)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        pm = self.images.get(self.hover) if self.hover else None
        if pm is None or pm.isNull():
            pm = self.images["menu"]
        if not pm.isNull():
            p.drawPixmap(QRectF(self.rect()), pm, QRectF(pm.rect()))


class LogonScreen(QWidget):
    logged_on = Signal()
    shut_down = Signal()
    restart = Signal()
    sleep = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.background = QPixmap(str(LOGON_DIR / "Logon_Template.png"))
        self.frame = QPixmap(str(LOGON_DIR / "Icon_Frame.png"))
        self.frame_hot = QPixmap(str(LOGON_DIR / "Icon_Frame_Highlight.png"))
        self.power_pm = QPixmap(str(LOGON_DIR / "Button_Power_Choices.jpg"))
        self.switch_pm = QPixmap(str(LOGON_DIR / "Button_Switch_User.jpg"))
        self.status_lines = []
        self.locked = False
        self.hover_tile = False
        self.error = ""
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Password")
        self.password.setStyleSheet("QLineEdit { background: white; color: #202020; border: 1px solid #8E9BAE;"
                                    " padding: 2px 6px; font-family: 'Segoe UI'; font-size: 13px; }")
        self.password.returnPressed.connect(self._submit)
        self.go = QPushButton("→", self)
        self.go.setCursor(Qt.PointingHandCursor)
        self.go.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5FA3E8,"
                              " stop:1 #1E66C0); color: white; border: 1px solid #10457F; border-radius: 3px;"
                              " font-size: 16px; font-weight: bold; }"
                              "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8CC3F5,"
                              " stop:1 #2F7AD3); }")
        self.go.clicked.connect(self._submit)
        self.switch = QPushButton(self)
        self.switch.setFlat(True)
        self.switch.setCursor(Qt.PointingHandCursor)
        self.switch.setStyleSheet("QPushButton { border: 0; padding: 0; background: transparent; }")
        self.switch.setIcon(QIcon(self.switch_pm))
        self.switch.clicked.connect(self._switch_user)
        self.power = QPushButton(self)
        self.power.setFlat(True)
        self.power.setCursor(Qt.PointingHandCursor)
        self.power.setStyleSheet("QPushButton { border: 0; padding: 0; background: transparent; }")
        self.power.setIcon(QIcon(self.power_pm))
        self.power.clicked.connect(self._toggle_power_menu)
        self.menu = PowerMenu(self)
        self.menu.chosen.connect(self._power_action)
        self.ok = QPushButton("OK", self)
        self.ok.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F6F6F6,"
                              " stop:1 #D9D9D9); color: #202020; border: 1px solid #707070; border-radius: 3px;"
                              " padding: 3px 18px; font-family: 'Segoe UI'; font-size: 12px; }")
        self.ok.clicked.connect(self._clear_error)
        self.ok.hide()

    # ---- geometry ----
    def _scale(self):
        return max(self.width() / DESIGN_W, self.height() / DESIGN_H)

    def _rect(self, x, y, w, h):
        s = self._scale()
        ox = (self.width() - DESIGN_W * s) / 2
        oy = (self.height() - DESIGN_H * s) / 2
        return QRect(round(ox + x * s), round(oy + y * s), round(w * s), round(h * s))

    def _layout(self):
        s = self._scale()
        self.password.setGeometry(self._rect(*PASSWORD))
        self.password.setVisible(not self.error)           # (the box is part of the template: always there)
        self.go.setGeometry(self._rect(*GO))
        self.go.setVisible(not self.error)
        sw = self._rect(*SWITCH)
        self.switch.setGeometry(sw)
        self.switch.setIconSize(QSize(sw.width(), sw.height()))
        self.switch.setVisible(not self.error)
        margin = round(24 * s)
        pw_w, pw_h = round(self.power_pm.width() * s), round(self.power_pm.height() * s)
        self.power.setGeometry(self.width() - margin - pw_w, self.height() - margin - pw_h, pw_w, pw_h)
        self.power.setIconSize(self.power.size())
        self.power.setVisible(not self.error)
        mw, mh = round(148 * s), round(80 * s)
        self.menu.setGeometry(self.width() - margin - mw, self.height() - margin - pw_h - mh, mw, mh)
        self.ok.setGeometry(self.width() // 2 - 40, self.height() // 2 + 40, 80, 28)

    def resizeEvent(self, event):
        self._layout()

    def reset(self, locked=False, status_lines=None):
        self.locked = locked
        self.status_lines = list(status_lines or [])
        self.error = ""
        self.ok.hide()
        self.menu.hide()
        self.password.clear()
        self._layout()
        self.update()
        QTimer.singleShot(0, self.password.setFocus)

    # ---- logging on ----
    def _submit(self):
        if self.error:
            return
        if user.has_windows_password() and not user.check_windows_password(self.password.text()):
            self.error = "The user name or password is incorrect."
            self.password.clear()
            self._layout()
            self.ok.show()
            self.ok.setFocus()
            sound.play("critical")
            self.update()
            return
        sound.play("user_select")
        self.logged_on.emit()

    def _clear_error(self):
        self.error = ""
        self.ok.hide()
        self._layout()
        self.update()
        self.password.setFocus()

    def _switch_user(self):
        sound.play("menu")
        self.locked = False
        self.update()

    def _toggle_power_menu(self):
        self.menu.setVisible(not self.menu.isVisible())
        if self.menu.isVisible():
            self.menu.raise_()

    def _power_action(self, what):
        self.menu.hide()
        {"restart": self.restart, "sleep": self.sleep, "shutdown": self.shut_down}[what].emit()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.error:
                self._clear_error()
            else:
                self._submit()
        elif event.key() == Qt.Key_Escape:
            self.menu.hide()
            if self.error:
                self._clear_error()
        else:
            super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        hot = self._rect(*FRAME).contains(event.position().toPoint()) and not self.error
        if hot != self.hover_tile:
            self.hover_tile = hot
            if hot:
                sound.play("user_highlight")
            self.update()

    def mousePressEvent(self, event):
        if self.menu.isVisible():
            self.menu.hide()
        if self._rect(*FRAME).contains(event.position().toPoint()) and not self.error:
            if user.has_windows_password():
                self.password.setFocus()
            else:
                self._submit()
        elif self._rect(*SWITCH).adjusted(-30, -30, 30, 30).contains(event.position().toPoint()):
            pass

    # ---- painting ----
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.setRenderHint(QPainter.Antialiasing)
        s = self._scale()
        if self.background.isNull():
            p.fillRect(self.rect(), QColor("#1F5FA8"))
        else:
            w, h = self.background.width() * s, self.background.height() * s
            p.drawPixmap(QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h), self.background,
                         QRectF(self.background.rect()))
        if self.error:
            self._paint_error(p)
            return
        frame = self._rect(*FRAME)
        fpm = self.frame_hot if self.hover_tile and not self.frame_hot.isNull() else self.frame
        tile = self._rect(*TILE)
        if not fpm.isNull():
            p.drawPixmap(QRectF(frame), fpm, QRectF(fpm.rect()))
        user.draw_user_picture(p, tile)
        f = QFont("Segoe UI")
        f.setPixelSize(max(13, round(17 * s)))
        p.setFont(f)
        name = user.user_name()
        r = self._rect(*NAME)
        p.setPen(QColor(0, 0, 0, 140))
        p.drawText(r.translated(1, 1), Qt.AlignCenter, name)
        p.setPen(QColor("white"))
        p.drawText(r, Qt.AlignCenter, name)
        f.setPixelSize(max(11, round(12 * s)))
        p.setFont(f)
        lines = (["Locked"] if self.locked else []) + self.status_lines
        y = self._rect(*SWITCH).bottom() + 8
        for line in lines:
            lr = QRect(r.x(), y, r.width(), 18)
            p.setPen(QColor(0, 0, 0, 120))
            p.drawText(lr.translated(1, 1), Qt.AlignCenter, line)
            p.setPen(QColor("#E8F0F8"))
            p.drawText(lr, Qt.AlignCenter, line)
            y += 18
        # the edition name at the bottom, with the flag
        f = QFont("Segoe UI")
        f.setPixelSize(max(14, round(19 * s)))
        f.setWeight(QFont.Light)
        p.setFont(f)
        text = "Windows 7 Home Premium"
        tw = QFontMetrics(f).horizontalAdvance(text)
        x = (self.width() - tw) // 2
        by = self.height() - round(46 * s)
        self._flag(p, x - 36, by - 22, 26)
        p.setPen(QColor(0, 0, 0, 120))
        p.drawText(x + 1, by + 1, text)
        p.setPen(QColor("white"))
        p.drawText(x, by, text)
        # Ease of access, bottom left
        margin = round(24 * s)
        d = round(28 * s)
        p.setPen(QPen(QColor(255, 255, 255, 180), 1.5))
        p.setBrush(QColor(40, 90, 150, 120))
        p.drawEllipse(QRect(margin, self.height() - margin - d, d, d))
        cx, cy = margin + d / 2, self.height() - margin - d / 2
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("white"))
        p.drawEllipse(QRectF(cx - d * 0.09, cy - d * 0.36, d * 0.18, d * 0.18))
        p.setPen(QPen(QColor("white"), 2))
        p.drawLine(QPointF(cx - d * 0.26, cy - d * 0.1), QPointF(cx + d * 0.26, cy - d * 0.1))
        p.drawLine(QPointF(cx, cy - d * 0.1), QPointF(cx, cy + d * 0.14))
        p.drawLine(QPointF(cx, cy + d * 0.14), QPointF(cx - d * 0.2, cy + d * 0.38))
        p.drawLine(QPointF(cx, cy + d * 0.14), QPointF(cx + d * 0.2, cy + d * 0.38))

    def _paint_error(self, p):
        f = QFont("Segoe UI")
        f.setPixelSize(16)
        p.setFont(f)
        p.setPen(QColor(0, 0, 0, 140))
        p.drawText(self.rect().translated(1, 1), Qt.AlignCenter, self.error)
        p.setPen(QColor("white"))
        p.drawText(self.rect(), Qt.AlignCenter, self.error)

    @staticmethod
    def _flag(p, x, y, size):
        """The four-colour Windows flag, waving a little."""
        colours = ["#F35325", "#81BC06", "#05A6F0", "#FFBA08"]
        half = size / 2
        gap = size * 0.06
        lean = size * 0.1
        for i, colour in enumerate(colours):
            col, row = i % 2, i // 2
            x0 = x + col * (half + gap)
            y0 = y + row * (half + gap)
            top_l = y0 + (lean if col == 0 else lean * 0.4)
            top_r = y0 + (lean * 0.4 if col == 0 else 0)
            bot_l = y0 + half - gap - (0 if col == 0 else lean * 0.2)
            bot_r = y0 + half - gap - (lean * 0.2 if col == 0 else lean * 0.5)
            poly = QPolygonF([QPointF(x0, top_l), QPointF(x0 + half - gap, top_r),
                              QPointF(x0 + half - gap, bot_r), QPointF(x0, bot_l)])
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(colour))
            p.drawPolygon(poly)
