"""The PC's power states around Windows: the BIOS power-on self test, and 'It's now safe to turn off
your computer' after shutting down (the PC stays 'on' there, so the world keeps moving)."""
import random

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from . import sound
from .paths import IMAGES, pixmap

GREY = QColor("#AAAAAA")
# The row of logos along the bottom of the self test: the models ClaudeXP runs, and who helped build it.
LOGO_DIR = IMAGES / "Bios Logos"
LOGO_GROUPS = [("Internal LLMs:", ["LLM-Qwen-Logo.png", "LLM-Mistral Logos.png", "LLM-Gemma-logo.png"]),
               ("Help from:", ["Claude-Logo.png", "ChatGPT-Logo.png", "Copilot-Logo.png", "gemini-star-logo.jpg",
                               "Grok-Logo.png"])]
LOGO_START_MS = 1200          # the first logo shows up this long after power on
LOGO_EVERY_MS = 420           # then one more every this often
_logos = None


INVERT = {"ChatGPT-Logo.png"}          # a dark mark on a light tile: becomes a light mark like the rest
LOGO_BOX = 128                        # every logo is fitted into a square this size, then scaled to the row


def _load_logo(name):
    """A logo standardised for the black screen: its black (or, for ChatGPT, light) square taken away, trimmed to
    what's drawn, brightened so its brightest part is full brightness, and centred in a square."""
    img = QImage(str(LOGO_DIR / name))
    if img.isNull():
        return None
    img = img.convertToFormat(QImage.Format_ARGB32)
    w, h = img.width(), img.height()
    invert = name in INVERT
    outside = set()
    if invert:                                            # the black around the tile (flood fill from the edges)
        def dark(x, y):
            c = img.pixelColor(x, y)
            return 0.3 * c.red() + 0.59 * c.green() + 0.11 * c.blue() < 100
        todo = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
        while todo:
            x, y = todo.pop()
            if (x, y) in outside or not (0 <= x < w and 0 <= y < h) or not dark(x, y):
                continue
            outside.add((x, y))
            todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        for _ in range(2):                                # and the tile's soft edge
            outside |= {(x + dx, y + dy) for x, y in outside for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    left, top, right, bottom, brightest = w, h, -1, -1, 1
    for y in range(h):
        for x in range(w):
            c = img.pixelColor(x, y)
            lum = 0.3 * c.red() + 0.59 * c.green() + 0.11 * c.blue()
            if invert:                                    # tile -> clear, mark -> white
                a = 0.0 if (x, y) in outside else max(0.0, min(1.0, (170 - lum) / 120)) * c.alphaF()
                c = QColor(255, 255, 255, int(a * 255))
            else:                                         # black -> clear, with a soft edge
                fade = max(0.0, min(1.0, (lum - 22) / 40))
                c.setAlphaF(c.alphaF() * fade)
            img.setPixelColor(x, y, c)
            if c.alpha() > 40:
                left, top, right, bottom = min(left, x), min(top, y), max(right, x), max(bottom, y)
                brightest = max(brightest, c.red(), c.green(), c.blue())
    if right < 0:
        return None
    gain = 255 / brightest
    if gain > 1.05:
        for y in range(top, bottom + 1):
            for x in range(left, right + 1):
                c = img.pixelColor(x, y)
                img.setPixelColor(x, y, QColor(min(255, int(c.red() * gain)), min(255, int(c.green() * gain)),
                                               min(255, int(c.blue() * gain)), c.alpha()))
    img = img.copy(left, top, right - left + 1, bottom - top + 1)
    img = img.scaled(LOGO_BOX, LOGO_BOX, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    square = QImage(LOGO_BOX, LOGO_BOX, QImage.Format_ARGB32)
    square.fill(Qt.transparent)
    p = QPainter(square)
    p.drawImage((LOGO_BOX - img.width()) // 2, (LOGO_BOX - img.height()) // 2, img)
    p.end()
    return QPixmap.fromImage(square)


def bios_logos():
    """[(label, [pixmaps])] - whatever of the logos are there."""
    global _logos
    if _logos is None:
        _logos = [(label, [pm for pm in (_load_logo(n) for n in names) if pm is not None])
                  for label, names in LOGO_GROUPS]
    return _logos
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
        self.shown_logos = 0               # how many of the bottom row's logos have appeared
        self.logo_fade = 1.0
        self.logo_timer = QTimer(self)
        self.logo_timer.timeout.connect(self._reveal)

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
        self.shown_logos, self.logo_fade = 0, 1.0
        QTimer.singleShot(LOGO_START_MS, lambda: None if self._done else self.logo_timer.start(40))
        self.update()

    def _reveal(self):
        """Fade the next logo in; when it's in, wait a little and start the next one."""
        total = sum(len(pms) for _l, pms in bios_logos())
        if self.shown_logos >= total and self.logo_fade >= 1.0:
            self.logo_timer.stop()
            return
        if self.logo_fade >= 1.0:
            self.shown_logos += 1
            self.logo_fade = 0.0
        self.logo_fade = min(1.0, self.logo_fade + 40 / 260)
        if self.logo_fade >= 1.0:
            self.logo_timer.start(LOGO_EVERY_MS)
        else:
            self.logo_timer.start(40)
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
        self.logo_timer.stop()
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
        icon_h = int(line_h * 1.7)
        if self.footer:                    # the serial-number line, just above the row of logos
            p.setPen(GREY)
            p.drawText(margin, self.height() - margin - icon_h - line_h // 2, self.footer)
        self._draw_logos(p, margin, self.height() - margin - icon_h, icon_h)

    def _draw_logos(self, p, x, top, icon_h):
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        fm = p.fontMetrics()
        n = 0
        for label, pms in bios_logos():
            if n >= self.shown_logos or not pms:
                break
            p.setOpacity(1.0)
            p.setPen(WHITE)
            p.drawText(x, top + icon_h // 2 + fm.ascent() // 2 - 1, label)
            x += fm.horizontalAdvance(label) + icon_h // 3
            for pm in pms:
                if n >= self.shown_logos:
                    break
                n += 1
                p.setOpacity(self.logo_fade if n == self.shown_logos else 1.0)
                w = icon_h * pm.width() / max(1, pm.height())
                p.drawPixmap(QRectF(x, top, w, icon_h), pm, QRectF(pm.rect()))
                x += w + icon_h // 3
            x += icon_h // 2
        p.setOpacity(1.0)


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
