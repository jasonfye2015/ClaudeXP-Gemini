"""The PC's power states around Windows: the BIOS power-on self test, and 'It's now safe to turn off
your computer' after shutting down (the PC stays 'on' there, so the world keeps moving)."""
import random

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from . import sound
from .paths import pixmap

GREY = QColor("#AAAAAA")
WHITE = QColor("#FFFFFF")
MEMORY_KB = 262144


def _dos_font(size):
    font = QFont("Lucida Console")
    font.setStyleHint(QFont.Monospace)
    font.setPixelSize(size)
    return font


class BiosScreen(QWidget):
    """AMIBIOS power-on self test: memory count, POST beep, floppy seek, drive detection."""
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logo = pixmap("ami_bios_logo.png")
        self.lines = []          # (text, color)
        self.memory = None       # KB counted so far, while the memory test runs
        self.footer = ""
        self.steps = []
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._next)
        self.count_timer = QTimer(self)
        self.count_timer.timeout.connect(self._count)
        self._done = True
        self.recovery_requested = False    # SPACE pressed: show the System Recovery menu after the test

    # ---- the script -------------------------------------------------------------------
    def start(self, recovery=False):
        """Run the self test. recovery=True boots into System Recovery (as if SPACE had been pressed)."""
        self._done = False
        self.recovery_requested = recovery
        self.lines, self.memory, self.footer = [], None, ""
        sound.play_file(random.choice(["harddrive_startup1.mp3", "harddrive_startup2.mp3"]))  # power on
        say = lambda text, color=GREY: lambda: self.lines.append((text, color))
        self.steps = [
            (400, say("AMIBIOS (C)2001 American Megatrends, Inc.", WHITE)),
            (150, say("CLAUDEXP P3V-133 ACPI BIOS Revision 1007")),
            (500, say("CPU : Intel(R) Pentium(R) III CPU 866MHz")),
            (100, say(" Speed : 866 MHz")),
            (300, say("")),
            (100, say("Press DEL to run Setup")),
            (100, say("Press <F8> for BBS POPUP")),
            (100, say("System Recovery requested..." if recovery else "Press <SPACE> for System Recovery",
                      WHITE if recovery else GREY)),
            (100, say("DDR Frequency 133MHz, Single-Channel, Linear Mode")),
            (400, self._start_memory_test),
        ]
        self.footer = "62-0101-001199-00101111-071595-VIA_K7-P3V133-00"
        self.timer.start(200)
        self.update()

    def _next(self):
        if self._done:
            return
        if not self.steps:
            self._finish()
            return
        delay, action = self.steps.pop(0)
        action()
        self.update()
        if self.steps or self.memory is None or self.memory >= MEMORY_KB:
            self.timer.start(self.steps[0][0] if self.steps else 900)

    def _start_memory_test(self):
        self.memory = 0
        self.lines.append(("Memory Test :      0K", GREY))
        self.count_timer.start(25)

    def _count(self):
        self.memory = min(MEMORY_KB, self.memory + 4096)
        self.lines[-1] = (f"Memory Test : {self.memory:6d}K", GREY)
        self.update()
        if self.memory >= MEMORY_KB:
            self.count_timer.stop()
            self.lines[-1] = (f"Memory Test : {MEMORY_KB}K OK", GREY)
            self.memory = None
            sound.play_file(random.choice(["post_beep1.wav", "post_beep2.wav"]))   # POST: all OK
            QTimer.singleShot(400, lambda: sound.play_clip(
                random.choice(["floppydrive_reading1.mp3", "floppydrive_reading2.mp3"]), 1400))  # floppy seek
            say = lambda text, color=GREY: lambda: self.lines.append((text, color))
            self.steps = [
                (900, say("")),
                (200, say("Auto-Detecting Pri Master..IDE Hard Disk")),
                (700, lambda: self._replace("Pri Master   : ST320413A  3.39")),
                (150, say("               Ultra DMA Mode-5, S.M.A.R.T. Capable and Status OK")),
                (300, say("Auto-Detecting Pri Slave...Not Detected")),
                (400, say("Auto-Detecting Sec Master..ATAPI CDROM")),
                (500, lambda: self._replace("Sec Master   : ATAPI CDROM  CD-540E  1.0A")),
                (200, say("               Ultra DMA Mode-2")),
                (300, say("Auto-Detecting Sec Slave...Not Detected")),
                (300, say("USB Device(s) : 1 Storage Device (External Drive)")),
                (200, say("Floppy Drive B: 1.44 MB 3½\"")),
                (600, say("")),
                (300, say("Verifying DMI Pool Data ........", WHITE)),
                (1200, say("Boot from Hard Disk...", WHITE)),
                (900, lambda: None),
            ]
            self.timer.start(self.steps[0][0])

    def _replace(self, text):
        self.lines[-1] = (text, GREY)

    def _finish(self):
        if self._done:
            return
        self._done = True
        self.timer.stop()
        self.count_timer.stop()
        self.finished.emit()

    def mousePressEvent(self, event):
        self._finish()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            if not self.recovery_requested:
                self.recovery_requested = True
                for i, (text, color) in enumerate(self.lines):
                    if text.startswith("Press <SPACE>"):
                        self.lines[i] = ("System Recovery requested...", WHITE)
                self.update()
            return
        self._finish()

    # ---- drawing --------------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        size = max(12, self.height() // 34)
        font = _dos_font(size)
        p.setFont(font)
        line_h = QFontMetrics(font).lineSpacing()
        margin = size
        if not self.logo.isNull():
            logo_w = self.width() * 0.3
            logo_h = logo_w * self.logo.height() / self.logo.width()
            p.drawPixmap(QRectF(self.width() - logo_w - margin, margin, logo_w, logo_h), self.logo,
                         QRectF(self.logo.rect()))
        y = margin + line_h
        for text, color in self.lines:
            p.setPen(color)
            p.drawText(margin, y, text)
            y += line_h
        if self.footer:
            p.setPen(GREY)
            p.drawText(margin, self.height() - margin, self.footer)


class SafeOffScreen(QWidget):
    """'It's now safe to turn off your computer.' The PC is still on underneath."""
    turn_off = Signal()
    restart = Signal()
    recovery = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = pixmap("safe_shutdown.jpg")
        style = ("QPushButton { background: black; color: #E8862A; border: 2px solid #E8862A; padding: 6px 18px;"
                 " font-family: 'Lucida Console'; font-size: 15px; }"
                 "QPushButton:hover { background: #2A1606; }"
                 "QPushButton:pressed { background: #E8862A; color: black; }")
        self.off_btn = QPushButton("Turn off")
        self.restart_btn = QPushButton("Restart computer")
        self.recovery_btn = QPushButton("Start recovery/format")
        self.recovery_btn.setToolTip("Restart into System Recovery to reinstall Windows XP")
        for b in (self.off_btn, self.restart_btn, self.recovery_btn):
            b.setStyleSheet(style)
            b.setCursor(Qt.PointingHandCursor)
        self.off_btn.clicked.connect(self.turn_off)
        self.restart_btn.clicked.connect(self.restart)
        self.recovery_btn.clicked.connect(self.recovery)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.off_btn)
        row.addSpacing(30)
        row.addWidget(self.restart_btn)
        row.addSpacing(30)
        row.addWidget(self.recovery_btn)
        row.addStretch()
        root = QVBoxLayout(self)
        root.addStretch()
        root.addLayout(row)
        root.setContentsMargins(20, 20, 20, 40)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        if self.image.isNull():
            p.setPen(QColor("#E8862A"))
            p.setFont(_dos_font(28))
            p.drawText(self.rect(), Qt.AlignCenter, "It's now safe to turn off\nyour computer.")
            return
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        scale = min(self.width() / self.image.width(), (self.height() - 80) / self.image.height())
        w, h = self.image.width() * scale, self.image.height() * scale
        p.drawPixmap(QRectF((self.width() - w) / 2, (self.height() - 80 - h) / 2, w, h), self.image,
                     QRectF(self.image.rect()))
