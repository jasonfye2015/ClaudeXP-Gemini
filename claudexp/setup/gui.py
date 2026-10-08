"""GUI-mode Windows XP Setup: steps down the left, 'Setup will complete in approximately: N minutes',
rotating slides, a progress bar, and the setup wizard pages (regional settings, your name, computer name,
date and time, networking) part way through."""
import random

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QRadioButton, QStackedWidget, QVBoxLayout, QWidget)

from .. import clock
from ..paths import pixmap
from . import ms

STEPS = ["Collecting information", "Dynamic Update", "Preparing installation", "Installing Windows",
         "Finalizing installation"]

# (task label, seconds, minutes left at the end, step index). "wizard" pauses for the setup pages.
PLAN = [("Installing Devices", 24, 34, 3), ("wizard", 0, 34, 3), ("Installing Network", 14, 30, 3),
        ("Copying files...", 20, 22, 3), ("Installing Start menu items", 8, 15, 4),
        ("Registering components", 10, 8, 4), ("Saving settings", 6, 4, 4),
        ("Removing any temporary files used", 6, 1, 4)]
START_MINUTES = 39

SLIDES = [
    ("A fresh new look",
     "Windows XP brings a clean, friendly new design. The Start menu puts the programs you use most "
     "right where you need them, and related windows group together on the taskbar."),
    ("Stay in touch",
     "Your buddies are only a click away. ClaudeAIM tells you who's online, FurNet IRC is always busy, "
     "and PawPrints MUCK is open all night. Everyone will be glad to meet you."),
    ("The Internet, your way",
     "Dial up with America Online and explore the Web with Netscape Navigator. Save your favorite pages "
     "and print them, right to your external drive."),
    ("Take a break",
     "Solitaire, FreeCell, Spider Solitaire, Hearts and Minesweeper are all included. "
     "Find them in Start, All Programs, Games."),
    ("Your computer, under control",
     "Automatic Updates keeps Windows current, ClaudeShield AntiVirus watches for trouble, and Disk "
     "Defragmenter keeps your hard disk running smoothly."),
    ("Make it yours",
     "Pick a desktop background and a screen saver, choose a picture for your account, and arrange your "
     "desktop just the way you like it."),
]


def _logo():
    """The Windows XP flag and wordmark, lifted off the setup background (its blue made transparent)."""
    src = pixmap("setup_background.png").toImage().copy(950, 270, 490, 310).convertToFormat(QImage.Format_ARGB32)
    bg = QColor(src.pixel(5, 5))
    for y in range(src.height()):
        for x in range(src.width()):
            c = QColor(src.pixel(x, y))
            d = abs(c.red() - bg.red()) + abs(c.green() - bg.green()) + abs(c.blue() - bg.blue())
            if d < 120:
                c.setAlpha(int(255 * d / 120))
                if d < 25:
                    c = QColor(0, 0, 0, 0)
                src.setPixelColor(x, y, c)
    return QPixmap.fromImage(src)


WIZARD_STYLE = """
QFrame#wizard { background: #ECE9D8; border: 1px solid #0831D9; }
QWidget#wizhead { background: white; border-bottom: 1px solid #ACA899; }
QLabel { font-family: Tahoma; font-size: 11px; color: black; }
QLabel#wiztitle { font-weight: bold; }
QLabel#wizsub { padding-left: 16px; }
QLabel#captionbar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0A5FEA, stop:1 #0040C8);
                    color: white; font-family: Trebuchet MS; font-size: 13px; font-weight: bold; padding: 4px 8px; }
QLineEdit, QComboBox { font-family: Tahoma; font-size: 11px; }
QRadioButton, QCheckBox { font-family: Tahoma; font-size: 11px; }
QPushButton { font-family: Tahoma; font-size: 11px; min-width: 75px; min-height: 23px; }
"""


def draw_cover(p, rect, pm):
    """Fill rect with the picture, keeping its shape (cropping the sides or top and bottom)."""
    if pm.isNull():
        return
    scale = max(rect.width() / pm.width(), rect.height() / pm.height())
    w, h = rect.width() / scale, rect.height() / scale
    p.drawPixmap(QRectF(rect), pm, QRectF((pm.width() - w) / 2, (pm.height() - h) / 2, w, h))


class Wizard(QFrame):
    """The setup pages, in an XP dialog."""
    done = Signal(dict)

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("wizard")
        self.setStyleSheet(WIZARD_STYLE)
        self.setFixedSize(500, 390)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        caption = QLabel("Windows XP Home Edition Setup")
        caption.setObjectName("captionbar")
        v.addWidget(caption)
        head = QWidget()
        head.setObjectName("wizhead")
        hv = QVBoxLayout(head)
        hv.setContentsMargins(14, 10, 14, 10)
        self.title = QLabel()
        self.title.setObjectName("wiztitle")
        self.sub = QLabel()
        self.sub.setObjectName("wizsub")
        self.sub.setWordWrap(True)
        self.sub.setFixedWidth(450)
        self.sub.setMinimumHeight(30)
        hv.addWidget(self.title)
        hv.addWidget(self.sub)
        v.addWidget(head)
        self.pages = QStackedWidget()
        v.addWidget(self.pages, 1)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #ACA899;")
        v.addWidget(line)
        buttons = QHBoxLayout()
        buttons.setContentsMargins(10, 8, 10, 10)
        buttons.addStretch()
        self.back = QPushButton("< &Back")
        self.next = QPushButton("&Next >")
        self.next.setDefault(True)
        buttons.addWidget(self.back)
        buttons.addWidget(self.next)
        v.addLayout(buttons)
        self.back.clicked.connect(lambda: self._show(self.pages.currentIndex() - 1))
        self.next.clicked.connect(self._next)
        self.heads = []
        self._build()
        self._show(0)

    def _page(self, title, sub):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(40, 14, 30, 8)
        self.pages.addWidget(w)
        self.heads.append((title, sub))
        return lay

    def _label(self, text):
        lab = QLabel(text)
        lab.setWordWrap(True)
        return lab

    def _build(self):
        lay = self._page("Regional and Language Options", "You can customize Windows XP for different regions and languages.")
        lay.addWidget(self._label("Regional and Language Options allow you to change the way numbers, dates, currencies "
                                  "and the time are displayed. The Standards and formats setting is set to English "
                                  "(United States), and the location is set to United States."))
        row = QHBoxLayout()
        row.addStretch()
        b = QPushButton("&Customize...")
        b.setEnabled(False)
        row.addWidget(b)
        lay.addLayout(row)
        lay.addWidget(self._label("Text Input Languages allow you to enter text in many different languages. "
                                  "Your default text input language and method is: US keyboard layout."))
        row = QHBoxLayout()
        row.addStretch()
        b = QPushButton("D&etails...")
        b.setEnabled(False)
        row.addWidget(b)
        lay.addLayout(row)
        lay.addStretch()

        lay = self._page("Personalize Your Software", "Setup uses the information you provide about yourself to "
                                                      "personalize your Windows XP software.")
        lay.addWidget(self._label("Type your full name and the name of your company or organization."))
        form = QFormLayout()
        self.owner = QLineEdit()
        self.org = QLineEdit()
        form.addRow("Na&me:", self.owner)
        form.addRow("&Organization:", self.org)
        for edit in (self.owner, self.org):
            form.labelForField(edit).setBuddy(edit)
        lay.addSpacing(10)
        lay.addLayout(form)
        lay.addStretch()
        self.owner.textChanged.connect(self._update_next)

        lay = self._page("What's Your Computer's Name?", "Setup has suggested a name for your computer. You can "
                                                         "change it if you like.")
        lay.addWidget(self._label("Your computer will be known on the network by this name. Computer names are limited "
                                  "to 15 characters."))
        form = QFormLayout()
        self.computer = QLineEdit()
        self.computer.setMaxLength(15)
        form.addRow("Computer &name:", self.computer)
        form.labelForField(self.computer).setBuddy(self.computer)
        lay.addSpacing(10)
        lay.addLayout(form)
        lay.addStretch()
        self.computer.textChanged.connect(self._update_next)

        lay = self._page("Date and Time Settings", "Set the correct date and time for your Windows computer.")
        form = QFormLayout()
        date = QLineEdit(clock.long_date_text())
        time = QLineEdit(clock.time_text())
        for w in (date, time):
            w.setReadOnly(True)
        form.addRow("Date && Time:", date)
        form.addRow("", time)
        zone = QComboBox()
        zone.addItems(["(GMT-08:00) Pacific Time (US & Canada); Tijuana", "(GMT-07:00) Mountain Time (US & Canada)",
                       "(GMT-06:00) Central Time (US & Canada)", "(GMT-05:00) Eastern Time (US & Canada)",
                       "(GMT) Greenwich Mean Time : Dublin, Edinburgh, Lisbon, London"])
        zone.setCurrentIndex(3)
        form.addRow("&Time Zone:", zone)
        lay.addLayout(form)
        dst = QCheckBox("Automatically adjust clock for &daylight saving changes")
        dst.setChecked(True)
        lay.addWidget(dst)
        lay.addStretch()

        lay = self._page("Networking Settings", "Installing network software allows you to connect to other "
                                                "computers, networks, and the Internet.")
        lay.addWidget(self._label("Choose whether to use typical or custom settings:"))
        group = QButtonGroup(self)
        typical = QRadioButton("&Typical settings")
        custom = QRadioButton("&Custom settings")
        typical.setChecked(True)
        for r, text in ((typical, "Creates network connections using the Client for Microsoft Networks, File and Print "
                                  "Sharing for Microsoft Networks, and the TCP/IP transport protocol."),
                        (custom, "Allows you to manually configure networking components.")):
            group.addButton(r)
            lay.addWidget(r)
            lab = self._label(text)
            lab.setContentsMargins(20, 0, 0, 6)
            lay.addWidget(lab)
        lay.addStretch()

    def start(self, suggested_owner=""):
        self.owner.setText(suggested_owner)
        self._show(0)

    def _show(self, index):
        index = max(0, min(index, self.pages.count() - 1))
        if index == 2 and not self.computer.text():
            base = "".join(ch for ch in self.owner.text().upper() if ch.isalnum())[:6] or "HOME"
            self.computer.setText(f"{base}-{''.join(random.choice('ABCDEF0123456789') for _ in range(6))}"[:15])
        self.pages.setCurrentIndex(index)
        title, sub = self.heads[index]
        self.title.setText(title)
        self.sub.setText(sub)
        self.back.setEnabled(index > 0)
        self._update_next()
        focus = {1: self.owner, 2: self.computer}.get(index)
        if focus:
            focus.setFocus()
        else:
            self.next.setFocus()

    def _update_next(self):
        i = self.pages.currentIndex()
        self.next.setEnabled(not ((i == 1 and not self.owner.text().strip()) or
                                  (i == 2 and not self.computer.text().strip())))

    def _next(self):
        i = self.pages.currentIndex()
        if i < self.pages.count() - 1:
            self._show(i + 1)
        else:
            self.done.emit({"owner": self.owner.text().strip(), "organization": self.org.text().strip(),
                            "computer": self.computer.text().strip().upper()})

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.next.isEnabled():
            self._next()
        else:
            super().keyPressEvent(event)


class GuiSetup(QWidget):
    finished = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg = pixmap("setup_background_nologo.png")
        self.logo = None
        self.wizard = Wizard(self)
        self.wizard.hide()
        self.wizard.done.connect(self._wizard_done)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.slide_timer = QTimer(self)
        self.slide_timer.timeout.connect(self._next_slide)
        self.info = {}

    def start(self):
        if self.logo is None:
            self.logo = _logo()
        self.phase = 0
        self.phase_progress = 0.0
        self.minutes = START_MINUTES
        self.slide = 0
        self.info = {}
        self.wizard.hide()
        self.timer.start(ms(100))
        self.slide_timer.start(ms(12000))
        self.update()

    def stop(self):
        self.timer.stop()
        self.slide_timer.stop()

    def _next_slide(self):
        self.slide = (self.slide + 1) % len(SLIDES)
        self.update()

    def _tick(self):
        label, seconds, end_minutes, _ = PLAN[self.phase]
        if label == "wizard":
            if not self.wizard.isVisible():
                self.wizard.start()
                self._place_wizard()
                self.wizard.show()
                self.wizard.raise_()
            return
        start_minutes = PLAN[self.phase - 1][2] if self.phase else START_MINUTES
        self.phase_progress = min(1.0, self.phase_progress + 0.1 / seconds)
        self.minutes = round(start_minutes - (start_minutes - end_minutes) * self.phase_progress)
        if self.phase_progress >= 1.0:
            self._advance()
        self.update()

    def _advance(self):
        self.phase += 1
        self.phase_progress = 0.0
        if self.phase >= len(PLAN):
            self.stop()
            QTimer.singleShot(ms(1500), lambda: self.finished.emit(self.info))

    def _wizard_done(self, info):
        self.info = info
        self.wizard.hide()
        self._advance()
        self.setFocus()

    def _place_wizard(self):
        self.wizard.move(int(self.width() * 0.62 - self.wizard.width() / 2), int((self.height() - self.wizard.height()) / 2))

    def resizeEvent(self, event):
        self._place_wizard()

    # ---- painting --------------------------------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        w, h = self.width(), self.height()
        draw_cover(p, self.rect(), self.bg)
        top, bottom = h * 77 / 766, h * 671 / 766
        if self.logo is not None:
            lh = top * 0.8
            lw = lh * self.logo.width() / self.logo.height()
            p.drawPixmap(QRectF(w * 0.03, top * 0.1, lw, lh), self.logo, QRectF(self.logo.rect()))
        # the steps down the left
        current = PLAN[min(self.phase, len(PLAN) - 1)][3]
        x = w * 0.045
        y = top + h * 0.08
        step_font = QFont("Tahoma")
        step_font.setPixelSize(max(11, int(h * 0.019)))
        for i, step in enumerate(STEPS):
            f = QFont(step_font)
            f.setBold(i == current)
            p.setFont(f)
            r = h * 0.009
            cy = y + h * 0.012
            if i == current:
                glow = QLinearGradient(x - r, cy - r, x + r, cy + r)
                glow.setColorAt(0, QColor("#FFE38A"))
                glow.setColorAt(1, QColor("#F08A1C"))
                p.setBrush(glow)
            else:
                p.setBrush(QColor("#9DC0FF") if i < current else QColor(255, 255, 255, 70))
            p.setPen(QPen(QColor(255, 255, 255, 150), 1))
            p.drawEllipse(QRectF(x - r, cy - r, 2 * r, 2 * r))
            p.setPen(QColor("white") if i >= current else QColor(255, 255, 255, 190))
            p.drawText(QRectF(x + r * 2.2, y, w * 0.25, h * 0.03), Qt.AlignVCenter | Qt.AlignLeft, step)
            y += h * 0.05
        # estimate
        y += h * 0.04
        f = QFont("Tahoma")
        f.setPixelSize(max(11, int(h * 0.018)))
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(QRectF(x - h * 0.01, y, w * 0.26, h * 0.06), Qt.TextWordWrap, "Setup will complete in approximately:")
        y += h * 0.06
        big = QFont("Tahoma")
        big.setPixelSize(max(14, int(h * 0.03)))
        big.setBold(True)
        p.setFont(big)
        p.drawText(QRectF(x - h * 0.01, y, w * 0.26, h * 0.05), Qt.AlignLeft,
                   f"{max(1, self.minutes)} minute{'s' if self.minutes != 1 else ''}")
        # the task and its progress bar
        label = PLAN[min(self.phase, len(PLAN) - 1)][0]
        if label != "wizard" and self.phase < len(PLAN):
            p.setFont(f)
            bar_y = bottom - h * 0.075
            p.drawText(QRectF(x - h * 0.01, bar_y - h * 0.035, w * 0.3, h * 0.03), Qt.AlignLeft | Qt.AlignVCenter, label)
            self._bar(p, QRectF(x - h * 0.01, bar_y, w * 0.23, h * 0.022), self.phase_progress)
        # the slide (hidden while the setup pages are up)
        if self.wizard.isVisible():
            return
        title, body = SLIDES[self.slide]
        sx, sw = w * 0.36, w * 0.56
        tf = QFont("Trebuchet MS")
        tf.setPixelSize(max(18, int(h * 0.042)))
        tf.setBold(True)
        p.setFont(tf)
        p.setPen(QColor(0, 0, 0, 60))
        p.drawText(QRectF(sx + 2, top + h * 0.12 + 2, sw, h * 0.08), Qt.AlignLeft, title)
        p.setPen(QColor("white"))
        p.drawText(QRectF(sx, top + h * 0.12, sw, h * 0.08), Qt.AlignLeft, title)
        bf = QFont("Tahoma")
        bf.setPixelSize(max(12, int(h * 0.022)))
        p.setFont(bf)
        p.drawText(QRectF(sx, top + h * 0.22, sw * 0.85, h * 0.4), Qt.TextWordWrap, body)

    @staticmethod
    def _bar(p, rect, fraction):
        p.setPen(QPen(QColor("#1B3A8C"), 1))
        p.setBrush(QColor("white"))
        p.drawRoundedRect(rect, 3, 3)
        inner = rect.adjusted(3, 3, -3, -3)
        block, gap = inner.height() * 0.6, 2
        n = int((inner.width() * fraction) // (block + gap))
        p.setPen(Qt.NoPen)
        for i in range(n):
            r = QRectF(inner.x() + i * (block + gap), inner.y(), block, inner.height())
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            g.setColorAt(0, QColor("#B6F2A8"))
            g.setColorAt(0.5, QColor("#2DBF2D"))
            g.setColorAt(1, QColor("#1E9A1E"))
            p.setBrush(g)
            p.drawRect(r)
