"""Welcome to Microsoft Windows (the first-boot 'OOBE'): the intro music, a welcome page, registration,
'Who will use this computer?' (your account name), and 'Thank you!'."""
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPalette, QPen, QRadialGradient
from PySide6.QtWidgets import QButtonGroup, QLabel, QLineEdit, QRadioButton, QVBoxLayout, QWidget

from .. import sound
from ..paths import pixmap
from . import ms
from .gui import draw_cover

TOP, BOTTOM = 77 / 766, 671 / 766        # the dark bands of the background, as fractions of its height
PAGES = ["welcome", "register", "users", "online", "passwords", "thanks"]


class NavButton(QWidget):
    """OOBE's round arrow buttons: green 'Next' / 'Finish', blue 'Back'."""
    clicked = Signal()

    def __init__(self, text, forward, parent=None):
        super().__init__(parent)
        self.text, self.forward = text, forward
        self.hover = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(130, 40)

    def enterEvent(self, event):
        self.hover = True
        self.update()

    def leaveEvent(self, event):
        self.hover = False
        self.update()

    def mouseReleaseEvent(self, event):
        if self.isEnabled() and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()

    def changeEvent(self, event):
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        d = 30
        circle = QRectF(self.width() - d - 4, 5, d, d) if self.forward else QRectF(4, 5, d, d)
        g = QRadialGradient(circle.center() - QPointF(5, 6), d)
        if not self.isEnabled():
            g.setColorAt(0, QColor("#C8C8C8"))
            g.setColorAt(1, QColor("#7A7A7A"))
        elif self.forward:
            g.setColorAt(0, QColor("#D5FFB8" if self.hover else "#B6F5A0"))
            g.setColorAt(1, QColor("#2E9A1A"))
        else:
            g.setColorAt(0, QColor("#D6E6FF" if self.hover else "#B4CEFF"))
            g.setColorAt(1, QColor("#1C4FC4"))
        p.setPen(QPen(QColor(255, 255, 255, 200), 1.5))
        p.setBrush(g)
        p.drawEllipse(circle)
        arrow = QPainterPath()
        c = circle.center()
        s = 1 if self.forward else -1
        arrow.moveTo(c.x() - 6 * s, c.y() - 3)
        arrow.lineTo(c.x(), c.y() - 3)
        arrow.lineTo(c.x(), c.y() - 8)
        arrow.lineTo(c.x() + 8 * s, c.y())
        arrow.lineTo(c.x(), c.y() + 8)
        arrow.lineTo(c.x(), c.y() + 3)
        arrow.lineTo(c.x() - 6 * s, c.y() + 3)
        arrow.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("white"))
        p.drawPath(arrow)
        f = QFont("Tahoma")
        f.setPixelSize(15)
        f.setBold(True)
        f.setUnderline(self.hover and self.isEnabled())
        p.setFont(f)
        p.setPen(QColor("white") if self.isEnabled() else QColor(255, 255, 255, 120))
        text_rect = QRectF(0, 0, circle.left() - 6, self.height()) if self.forward else \
            QRectF(circle.right() + 6, 0, self.width(), self.height())
        p.drawText(text_rect, (Qt.AlignRight if self.forward else Qt.AlignLeft) | Qt.AlignVCenter, self.text)


FORM_STYLE = """
QLabel { color: white; font-family: Tahoma; font-size: 13px; }
QLineEdit { font-family: Tahoma; font-size: 13px; padding: 2px; border: 1px solid #7F9DB9; color: black; }
QLineEdit:disabled { background: #C8D4F0; }
QListWidget { background: rgba(255, 255, 255, 40); border: 1px solid #B0C4F0; }
QListWidget::item:selected { background: #F5A623; }
"""


class Oobe(QWidget):
    finished = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg_logo = pixmap("setup_background.png")
        self.bg = pixmap("setup_background_nologo.png")
        self.page = 0
        self.fade = 0.0
        self.player = None
        self.form = QWidget(self)
        self.form.setStyleSheet(FORM_STYLE)
        form = QVBoxLayout(self.form)
        form.setContentsMargins(0, 0, 0, 0)
        # registration
        self.reg = QWidget()
        rv = QVBoxLayout(self.reg)
        rv.setContentsMargins(0, 0, 0, 0)
        group = QButtonGroup(self)
        self.reg_yes = QRadioButton("Yes, I'd like to register with Microsoft now")
        self.reg_no = QRadioButton("No, not at this time")
        self.reg_no.setChecked(True)
        for r in (self.reg_yes, self.reg_no):
            group.addButton(r)
            rv.addWidget(r)
        self.reg_note = QLabel("")
        self.reg_note.setWordWrap(True)
        rv.addSpacing(12)
        rv.addWidget(self.reg_note)
        rv.addStretch()
        self.reg_yes.toggled.connect(lambda on: self.reg_note.setText(
            "Registration needs an Internet connection. You can register later from Help and Support." if on else ""))
        form.addWidget(self.reg)
        # who will use this computer
        self.users = QWidget()
        uv = QVBoxLayout(self.users)
        uv.setContentsMargins(0, 0, 0, 0)
        lab = QLabel("&Your name:")
        self.name = QLineEdit()
        self.name.setMaxLength(20)
        self.name.setFixedWidth(260)
        lab.setBuddy(self.name)
        uv.addWidget(lab)
        uv.addWidget(self.name)
        uv.addSpacing(10)
        uv.addWidget(QLabel("Pick a picture for your account:"))
        from ..accounts import OnlineNameForm, PasswordForm, PicturePicker, PRETEND_NOTE
        self.pictures = PicturePicker(40)
        self.pictures.setFixedHeight(120)
        if self.pictures.count():
            self.pictures.setCurrentRow(0)
        uv.addWidget(self.pictures)
        uv.addStretch()
        form.addWidget(self.users)
        self.name.textChanged.connect(self._update_buttons)
        self.name.returnPressed.connect(lambda: self._go(1))
        # your online name
        self.online = OnlineNameForm(lambda: self.name.text())
        self.online.changed.connect(self._update_buttons)
        form.addWidget(self.online)
        # passwords
        self.passwords = QWidget()
        pv = QVBoxLayout(self.passwords)
        pv.setContentsMargins(0, 0, 0, 0)
        self.win_pw = PasswordForm("Windows password", "Don't use a Windows password (the Welcome screen "
                                   "logs you on with one click)")
        self.online_pw = PasswordForm("Online password", "Don't use an online password")
        for f in (self.win_pw, self.online_pw):
            f.changed.connect(self._update_buttons)
            pv.addWidget(f)
            pv.addSpacing(8)
        note = QLabel(PRETEND_NOTE)
        note.setWordWrap(True)
        pv.addWidget(note)
        pv.addStretch()
        form.addWidget(self.passwords)
        # white text for radio buttons and checkboxes, without restyling (and hiding) their check marks
        from PySide6.QtWidgets import QCheckBox
        for box in self.form.findChildren(QRadioButton) + self.form.findChildren(QCheckBox):
            box.setStyleSheet("")
            f = QFont("Tahoma")
            f.setPixelSize(13)
            box.setFont(f)
            pal = box.palette()
            pal.setColor(QPalette.WindowText, QColor("white"))
            box.setPalette(pal)
        self.back = NavButton("Back", False, self)
        self.next = NavButton("Next", True, self)
        self.back.clicked.connect(lambda: self._go(-1))
        self.next.clicked.connect(lambda: self._go(1))
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self._fade_step)

    # ---- flow ---------------------------------------------------------------------------------------------
    def start(self, suggested_name=""):
        self.page = 0
        self.fade = 0.0
        self.name.setText(suggested_name)
        self.player = sound.play_file("oobe_music.mp3")
        self.fade_timer.start(30)
        self._layout()
        self.setFocus()

    def _fade_step(self):
        self.fade = min(1.0, self.fade + 30 / ms(1500))
        if self.fade >= 1.0:
            self.fade_timer.stop()
        self.update()

    def _go(self, step):
        if step > 0 and not self.next.isEnabled():
            return
        if PAGES[self.page] == "thanks" and step > 0:
            self._finish()
            return
        self.page = max(0, min(len(PAGES) - 1, self.page + step))
        self._layout()

    def _finish(self):
        name = self.name.text().strip()
        result = {"name": name, "picture": self.pictures.selected(), "handle": self.online.value() or name,
                  "linked": self.online.linked(), "windows_password": self.win_pw.value(),
                  "online_password": self.online_pw.value()}
        player = self.player
        self.player = None
        if player is not None:
            from shiboken6 import isValid
            out = player.audioOutput()
            steps = {"n": 0}

            def fade_out():
                if not isValid(player):
                    return
                steps["n"] += 1
                out.setVolume(max(0.0, 1.0 - steps["n"] / 20))
                if steps["n"] >= 20:
                    player.stop()
                else:
                    QTimer.singleShot(60, fade_out)
            fade_out()
        self.finished.emit(result)

    def stop_music(self):
        if self.player is not None:
            from shiboken6 import isValid
            if isValid(self.player):
                self.player.stop()
            self.player = None

    def _layout(self):
        page = PAGES[self.page]
        w, h = self.width(), self.height()
        self.reg.setVisible(page == "register")
        self.users.setVisible(page == "users")
        self.online.setVisible(page == "online")
        self.passwords.setVisible(page == "passwords")
        self.form.setVisible(page in ("register", "users", "online", "passwords"))
        if page == "register":
            self.form.setGeometry(int(w * 0.12), int(h * 0.42), int(w * 0.6), int(h * 0.3))
        else:
            self.form.setGeometry(int(w * 0.12), int(h * 0.34), int(w * 0.76), int(h * 0.52))
        if page == "online" and not self.online.value():
            self.online.set_values(self.name.text(), True)
        band_mid = h * (BOTTOM + 1) / 2
        self.next.text = "Finish" if page == "thanks" else "Next"
        self.next.move(int(w * 0.97 - self.next.width()), int(band_mid - self.next.height() / 2))
        self.back.move(int(w * 0.97 - self.next.width() - self.back.width() - 10), int(band_mid - self.back.height() / 2))
        self.back.setVisible(0 < self.page < len(PAGES) - 1)
        self._update_buttons()
        if page == "users":
            self.name.setFocus()
        else:
            self.setFocus()
        self.update()

    def _update_buttons(self):
        page = PAGES[self.page]
        ok = {"users": bool(self.name.text().strip()), "online": self.online.valid(),
              "passwords": self.win_pw.valid() and self.online_pw.valid()}.get(page, True)
        self.next.setEnabled(ok)
        self.next.update()

    def resizeEvent(self, event):
        self._layout()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._go(1)

    # ---- painting --------------------------------------------------------------------------------------------
    TEXT = {
        "welcome": ("Welcome to Microsoft Windows",
                    "Thanks for choosing Windows XP. Over the next few minutes we'll get your new computer ready to use."
                    "\n\nTo continue, click Next."),
        "register": ("Ready to register with Microsoft?",
                     "Registering lets Microsoft tell you about product updates and special offers. Registration is "
                     "optional."),
        "users": ("Who will use this computer?",
                  "Type your name and pick a picture. Windows will create a user account for you, so your desktop, "
                  "documents and settings are your own."),
        "online": ("What's your name online?",
                   "Your buddies, chat rooms and e-mail will know you by this name. Use your Windows name, or pick "
                   "a screen name. You can change it later in Control Panel, User Accounts."),
        "passwords": ("Do you want to use passwords?",
                      "Passwords are optional. A Windows password is asked for on the Welcome screen; an online "
                      "password is filled in for you when you sign on."),
        "thanks": ("Thank you!",
                   "Congratulations, your computer is ready to use Windows XP.\n\nTo begin, click Finish."),
    }

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        w, h = self.width(), self.height()
        page = PAGES[self.page]
        draw_cover(p, self.rect(), self.bg_logo if page == "welcome" else self.bg)
        title, body = self.TEXT[page]
        tf = QFont("Franklin Gothic Medium")
        tf.setPixelSize(max(22, int(h * 0.05)))
        p.setFont(tf)
        x = w * 0.08 if page == "welcome" else w * 0.12
        y = h * (TOP + 0.08)
        tw = w * 0.5 if page == "welcome" else w * 0.75
        p.setPen(QColor(0, 0, 0, 50))
        p.drawText(QRectF(x + 2, y + 2, tw, h * 0.16), Qt.TextWordWrap, title)
        p.setPen(QColor("white"))
        p.drawText(QRectF(x, y, tw, h * 0.16), Qt.TextWordWrap, title)
        bf = QFont("Tahoma")
        bf.setPixelSize(max(13, int(h * 0.022)))
        p.setFont(bf)
        by = y + (h * 0.17 if page == "welcome" else h * 0.1)
        p.drawText(QRectF(x, by, w * (0.42 if page == "welcome" else 0.6), h * 0.3), Qt.TextWordWrap, body)
        if self.fade < 1.0:
            p.fillRect(self.rect(), QColor(0, 0, 0, int(255 * (1 - self.fade))))
