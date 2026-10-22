"""Power on: the AMI BIOS self test of a 2011 PC (Core i5-2500K, 8 GB, a 1 TB SATA disk and a DVD writer), the
BIOS Setup Utility behind DEL, and the F8 Advanced Boot Options menu (Repair Your Computer reinstalls Windows)."""
import random

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from . import sound
from .paths import IMAGES

GREY = QColor("#AAAAAA")
WHITE = QColor("#FFFFFF")
MEMORY_KB = 8388608
LOGO_START_MS = 1200
LOGO_EVERY_MS = 420


def _dos_font(size):
    font = QFont("Lucida Console")
    font.setStyleHint(QFont.Monospace)
    font.setPixelSize(size)
    return font


def _logos():
    """The LLM and helper logos along the bottom, as ClaudeXP shows them (its artwork)."""
    try:
        from claudexp.power import bios_logos
        return bios_logos()
    except Exception:
        return []


class BiosScreen(QWidget):
    """AMIBIOS power-on self test: memory count, POST beep, SATA detection."""
    finished = Signal()
    setup_requested = Signal()
    boot_menu_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logo = QPixmap(str(IMAGES / "bios" / "amibios-logo.jpg"))
        self.energy = QPixmap(str(IMAGES / "bios" / "energystar-logo.jpg"))
        self.lines = []
        self.memory = None
        self.footer = ""
        self.steps = []
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._next)
        self.count_timer = QTimer(self)
        self.count_timer.timeout.connect(self._count)
        self._done = True
        self.recovery_requested = False
        self.setup_wanted = False
        self.shown_logos = 0
        self.logo_fade = 1.0
        self.logo_timer = QTimer(self)
        self.logo_timer.timeout.connect(self._reveal)

    def start(self, recovery=False):
        self._done = False
        self.recovery_requested = recovery
        self.setup_wanted = False
        self.lines, self.memory, self.footer = [], None, ""
        sound.play_file(random.choice(["harddrive_startup1.mp3", "harddrive_startup2.mp3"]))
        say = lambda text, color=GREY: lambda: self.lines.append((text, color))
        self.steps = [
            (400, say("AMIBIOS(C)2010 American Megatrends, Inc.", WHITE)),
            (150, say("CLAUDE7 P8P67 ACPI BIOS Revision 1305")),
            (500, say("CPU : Intel(R) Core(TM) i5-2500K CPU @ 3.30GHz")),
            (100, say(" Speed : 3.30 GHz    Count : 4")),
            (300, say("")),
            (100, say("Press DEL to run Setup")),
            (100, say("Press <F8> for Advanced Boot Options" if not recovery else "Advanced Boot Options requested...",
                      GREY if not recovery else WHITE)),
            (100, say("DDR3 Frequency 1333MHz, Dual-Channel, Interleaved Mode")),
            (400, self._start_memory_test),
        ]
        self.footer = "63-0100-000001-00101111-121010-P67-P8P67-00"
        self.timer.start(200)
        self.shown_logos, self.logo_fade = 0, 1.0
        QTimer.singleShot(LOGO_START_MS, lambda: None if self._done else self.logo_timer.start(40))
        self.update()

    def _reveal(self):
        total = sum(len(pms) for _l, pms in _logos())
        if self.shown_logos >= total and self.logo_fade >= 1.0:
            self.logo_timer.stop()
            return
        if self.logo_fade >= 1.0:
            self.shown_logos += 1
            self.logo_fade = 0.0
        self.logo_fade = min(1.0, self.logo_fade + 40 / 260)
        self.logo_timer.start(LOGO_EVERY_MS if self.logo_fade >= 1.0 else 40)
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
        self.lines.append(("Memory Test :        0K", GREY))
        self.count_timer.start(20)

    def _count(self):
        self.memory = min(MEMORY_KB, self.memory + 131072)
        self.lines[-1] = (f"Memory Test : {self.memory:8d}K", GREY)
        self.update()
        if self.memory >= MEMORY_KB:
            self.count_timer.stop()
            self.lines[-1] = (f"Memory Test : {MEMORY_KB}K OK", GREY)
            self.memory = None
            sound.play_file(random.choice(["post_beep1.wav", "post_beep2.wav"]))
            say = lambda text, color=GREY: lambda: self.lines.append((text, color))
            self.steps = [
                (900, say("")),
                (200, say("USB Device(s) : 1 Keyboard, 1 Mouse, 1 Storage Device (External Drive)")),
                (300, say("Auto-Detecting SATA 1..IDE Hard Disk")),
                (700, lambda: self._replace("SATA 1 : ST31000528AS  CC38")),
                (150, say("         Ultra DMA Mode-6, S.M.A.R.T. Capable and Status OK")),
                (300, say("Auto-Detecting SATA 2..ATAPI CDROM")),
                (500, lambda: self._replace("SATA 2 : ATAPI DVD A  DH24AAL  1.05")),
                (200, say("         Ultra DMA Mode-5")),
                (300, say("Auto-Detecting SATA 3..Not Detected")),
                (300, say("Auto-Detecting SATA 4..Not Detected")),
                (600, say("")),
                (300, say("Verifying DMI Pool Data ........", WHITE)),
                (900, self._after_post),
            ]
            self.timer.start(self.steps[0][0])

    def _after_post(self):
        """The end of the self test: Setup, the boot menu, or Windows."""
        if self.setup_wanted:
            self.lines.append(("Entering SETUP ...", WHITE))
            self.steps = [(700, self._enter_setup)]
        elif self.recovery_requested:
            self.lines.append(("Boot from Hard Disk...", WHITE))
            self.steps = [(700, self._boot_menu)]
        else:
            self.lines.append(("Boot from Hard Disk...", WHITE))
            self.steps = [(900, lambda: None)]

    def _enter_setup(self):
        self._done = True
        self._stop_timers()
        self.setup_requested.emit()

    def _boot_menu(self):
        self._done = True
        self._stop_timers()
        self.boot_menu_requested.emit()

    def _replace(self, text):
        self.lines[-1] = (text, GREY)

    def _stop_timers(self):
        self.timer.stop()
        self.count_timer.stop()
        self.logo_timer.stop()

    def _finish(self):
        if self._done:
            return
        self._done = True
        self._stop_timers()
        self.finished.emit()

    def mousePressEvent(self, event):
        self._finish()

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        key = event.key()
        if key == Qt.Key_Delete:
            if not self.setup_wanted:
                self.setup_wanted = True
                self._note("Press DEL to run Setup", "Entering SETUP after the self test...")
            return
        if key in (Qt.Key_F8, Qt.Key_Space):
            if not self.recovery_requested:
                self.recovery_requested = True
                self._note("Press <F8> for Advanced Boot Options", "Advanced Boot Options requested...")
            return
        if self._done:
            return
        # any other key: skip the rest of the test (Setup and the boot menu still come if asked for)
        if self.setup_wanted:
            self._enter_setup()
        elif self.recovery_requested:
            self._boot_menu()
        else:
            self._finish()

    def _note(self, prefix, text):
        for i, (line, _c) in enumerate(self.lines):
            if line.startswith(prefix):
                self.lines[i] = (text, WHITE)
        self.update()

    # ---- drawing ----
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        size = max(12, self.height() // 34)
        font = _dos_font(size)
        p.setFont(font)
        line_h = QFontMetrics(font).lineSpacing()
        margin = size
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        right = self.width() - margin
        if not self.logo.isNull():
            logo_w = self.width() * 0.22
            logo_h = logo_w * self.logo.height() / self.logo.width()
            p.drawPixmap(QRectF(right - logo_w, margin, logo_w, logo_h), self.logo, QRectF(self.logo.rect()))
            if not self.energy.isNull():
                e_w = logo_w * 0.5
                e_h = e_w * self.energy.height() / self.energy.width()
                p.drawPixmap(QRectF(right - e_w, margin + logo_h + margin, e_w, e_h), self.energy,
                             QRectF(self.energy.rect()))
        y = margin + line_h
        for text, color in self.lines:
            p.setPen(color)
            p.drawText(margin, y, text)
            y += line_h
        icon_h = int(line_h * 1.7)
        if self.footer:
            p.setPen(GREY)
            p.drawText(margin, self.height() - margin - icon_h - line_h // 2, self.footer)
        self._draw_logos(p, margin, self.height() - margin - icon_h, icon_h)

    def _draw_logos(self, p, x, top, icon_h):
        fm = p.fontMetrics()
        n = 0
        for label, pms in _logos():
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


# ---- the BIOS Setup Utility ----------------------------------------------------------------------------------------
BLUE = QColor("#0000A8")
PANEL = QColor("#A8A8A8")
SETUP_TABS = ["Main", "Advanced", "Power", "Boot", "Tools", "Exit"]
SETUP_PAGES = {
    "Main": [("System Time", "[{time}]", "Use [+] or [-] to configure system Time."),
             ("System Date", "[{date}]", "Use [+] or [-] to configure system Date."),
             ("", "", ""),
             ("SATA 1", "[ST31000528AS]", "While entering setup, BIOS auto detects the presence of IDE devices."),
             ("SATA 2", "[ATAPI DVD A DH24AAL]", ""),
             ("SATA 3", "[Not Detected]", ""), ("SATA 4", "[Not Detected]", ""),
             ("", "", ""),
             ("System Information", "", "Intel(R) Core(TM) i5-2500K CPU @ 3.30GHz\nSpeed : 3300MHz\n"
                                        "Usable Memory : 8192MB\nBIOS Version : 1305  Build Date : 12/10/10")],
    "Advanced": [("JumperFree Configuration", "", "Adjust system frequency/voltage."),
                 ("CPU Configuration", "", "Configure CPU."),
                 ("Chipset", "[Intel P67]", "Configure the chipset."),
                 ("Onboard Devices Configuration", "", ""),
                 ("USB Configuration", "[Enabled]", "Configure the USB support."),
                 ("PCI PnP", "", "")],
    "Power": [("Suspend Mode", "[Auto]", "Select the ACPI state used for System Suspend."),
              ("ACPI 2.0 Support", "[Enabled]", ""),
              ("ACPI APIC support", "[Enabled]", ""),
              ("APM Configuration", "", "Restore on AC Power Loss, Power On By PCI/PCIE, Power On By RTC Alarm"),
              ("Hardware Monitor", "", "CPU Temperature 38C/100F   MB Temperature 31C/87F   CPU Fan 1203RPM")],
    "Boot": [("Boot Device Priority", "", "1st Boot Device [SATA: ST31000528AS]\n2nd Boot Device [SATA: ATAPI DVD A]\n"
                                          "3rd Boot Device [USB: External Drive]"),
             ("Hard Disk Drives", "", ""), ("CDROM Drives", "", ""), ("Removable Drives", "", ""),
             ("Boot Settings Configuration", "", "Quick Boot [Enabled]\nFull Screen Logo [Enabled]\n"
                                                 "Wait For 'F1' If Error [Enabled]"),
             ("Security", "", "Supervisor Password : Not Installed\nUser Password : Not Installed")],
    "Tools": [("ASUS EZ Flash 2", "", "Press ENTER to run the utility to select and update BIOS."),
              ("ASUS O.C. Profile", "", ""), ("AI NET 2", "", "")],
    "Exit": [("Exit & Save Changes", "", "Exit system setup after saving the changes."),
             ("Exit & Discard Changes", "", "Exit system setup without saving any changes."),
             ("Discard Changes", "", "Discards changes done so far to any of the setup questions."),
             ("Load Setup Defaults", "", "Load Setup Default values for all the setup questions.")],
}


class BiosSetup(QWidget):
    """The blue AMI BIOS SETUP UTILITY: look around with the arrow keys; Esc or F10 leaves it and boots."""
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab = 0
        self.row = 0
        self.setFocusPolicy(Qt.StrongFocus)

    def reset(self):
        self.tab, self.row = 0, 0
        self.update()

    def keyPressEvent(self, event):
        key = event.key()
        page = SETUP_PAGES[SETUP_TABS[self.tab]]
        if key == Qt.Key_Right:
            self.tab, self.row = (self.tab + 1) % len(SETUP_TABS), 0
        elif key == Qt.Key_Left:
            self.tab, self.row = (self.tab - 1) % len(SETUP_TABS), 0
        elif key == Qt.Key_Down:
            self.row = min(len(page) - 1, self.row + 1)
            while page[self.row][0] == "" and self.row < len(page) - 1:
                self.row += 1
        elif key == Qt.Key_Up:
            self.row = max(0, self.row - 1)
            while page[self.row][0] == "" and self.row > 0:
                self.row -= 1
        elif key in (Qt.Key_Escape, Qt.Key_F10):
            self.closed.emit()
            return
        elif key in (Qt.Key_Return, Qt.Key_Enter) and SETUP_TABS[self.tab] == "Exit":
            self.closed.emit()
            return
        self.update()

    def paintEvent(self, event):
        from . import clock
        p = QPainter(self)
        p.fillRect(self.rect(), BLUE)
        size = max(12, self.height() // 34)
        font = _dos_font(size)
        p.setFont(font)
        fm = QFontMetrics(font)
        lh = fm.lineSpacing()
        w, h = self.width(), self.height()
        m = size
        # title bar and tabs
        p.fillRect(0, 0, w, lh + 6, PANEL)
        p.setPen(BLUE)
        p.drawText(QRectF(0, 0, w, lh + 6), Qt.AlignCenter, "BIOS SETUP UTILITY")
        x = m
        for i, name in enumerate(SETUP_TABS):
            tw = fm.horizontalAdvance(name) + 2 * m
            if i == self.tab:
                p.fillRect(int(x), lh + 6, int(tw), lh + 4, PANEL)
                p.setPen(BLUE)
            else:
                p.setPen(WHITE)
            p.drawText(QRectF(x, lh + 6, tw, lh + 4), Qt.AlignCenter, name)
            x += tw
        top = 2 * lh + 14
        p.setPen(WHITE)
        p.drawRect(m, top, w - 2 * m, h - top - 4 * lh)
        split = int(w * 0.62)
        p.drawLine(split, top, split, h - 4 * lh)
        # the page
        page = SETUP_PAGES[SETUP_TABS[self.tab]]
        now = clock.now()
        y = top + lh + 4
        for i, (label, value, _help) in enumerate(page):
            value = value.format(time=now.strftime("%H:%M:%S"), date=now.strftime("%a %m/%d/%Y"))
            if i == self.row and label:
                p.fillRect(m + 4, y - fm.ascent() - 1, split - m - 8, lh, WHITE)
                p.setPen(BLUE)
            else:
                p.setPen(WHITE)
            p.drawText(m + 10, y, label)
            if value:
                p.drawText(m + 10 + fm.horizontalAdvance("X" * 28), y, value)
            y += lh
        # the help column
        p.setPen(WHITE)
        hy = top + lh + 4
        text = page[self.row][2] if self.row < len(page) else ""
        for line in text.split("\n"):
            while line:
                cut = len(line)
                while fm.horizontalAdvance(line[:cut]) > w - split - 2 * m and cut > 1:
                    cut = line.rfind(" ", 0, cut) if " " in line[:cut] else cut - 1
                p.drawText(split + m, hy, line[:cut])
                line = line[cut:].lstrip()
                hy += lh
        # the legend
        p.fillRect(m, h - 4 * lh + 2, w - 2 * m, 3 * lh, PANEL)
        p.setPen(BLUE)
        legend = ["←→  Select Screen      ↑↓  Select Item      Enter  Go to Sub Screen",
                  "F1   General Help     F10  Save and Exit    ESC    Exit"]
        for i, line in enumerate(legend):
            p.drawText(m + 10, h - 4 * lh + 2 + (i + 1) * lh, line)
        p.setPen(WHITE)
        p.drawText(QRectF(0, h - lh, w, lh), Qt.AlignCenter, "v02.61 (C)Copyright 1985-2010, American Megatrends, Inc.")


# ---- Advanced Boot Options (F8) -------------------------------------------------------------------------------------
BOOT_OPTIONS = ["Repair Your Computer", "", "Safe Mode", "Safe Mode with Networking", "Safe Mode with Command Prompt",
                "", "Enable Boot Logging", "Enable low-resolution video (640x480)",
                "Last Known Good Configuration (advanced)", "Directory Services Restore Mode", "Debugging Mode",
                "Disable automatic restart on system failure", "Disable Driver Signature Enforcement", "",
                "Start Windows Normally"]
RECOVERY_OPTIONS = ["Startup Repair", "System Restore", "System Image Recovery", "Windows Memory Diagnostic",
                    "Command Prompt", "", "Reinstall Windows (format drive C:)", "", "Restart"]


class BootOptions(QWidget):
    """The black-and-white F8 menu, then (Repair Your Computer) System Recovery Options."""
    start_normally = Signal()
    safe_mode = Signal()
    reinstall = Signal()
    restart = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.menu = BOOT_OPTIONS
        self.title = "Advanced Boot Options"
        self.row = 0
        self.setFocusPolicy(Qt.StrongFocus)

    def reset(self):
        self.menu, self.title, self.row = BOOT_OPTIONS, "Advanced Boot Options", 0
        self.update()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Down:
            self.row = (self.row + 1) % len(self.menu)
            while not self.menu[self.row]:
                self.row = (self.row + 1) % len(self.menu)
        elif key == Qt.Key_Up:
            self.row = (self.row - 1) % len(self.menu)
            while not self.menu[self.row]:
                self.row = (self.row - 1) % len(self.menu)
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            self._choose(self.menu[self.row])
            return
        elif key == Qt.Key_Escape:
            if self.menu is RECOVERY_OPTIONS:
                self.reset()
                return
            self.start_normally.emit()
            return
        self.update()

    def _choose(self, item):
        if item == "Repair Your Computer":
            self.menu, self.title, self.row = RECOVERY_OPTIONS, "System Recovery Options", 0
            self.update()
        elif item.startswith("Reinstall Windows"):
            self.reinstall.emit()
        elif item == "Restart":
            self.restart.emit()
        elif item.startswith("Safe Mode"):
            self.safe_mode.emit()
        else:
            self.start_normally.emit()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        size = max(12, self.height() // 36)
        font = _dos_font(size)
        p.setFont(font)
        fm = QFontMetrics(font)
        lh = fm.lineSpacing()
        m = size * 2
        p.setPen(WHITE)
        p.drawText(m, m + lh, self.title)
        p.drawText(m, m + 2 * lh, "Choose Advanced Options for: Windows 7" if self.menu is BOOT_OPTIONS
                   else "Choose a recovery tool")
        p.drawText(m, m + 3 * lh, "(Use the arrow keys to highlight your choice.)")
        y = m + 5 * lh
        for i, item in enumerate(self.menu):
            if item:
                if i == self.row:
                    p.fillRect(m - 4, y - fm.ascent() - 2, fm.horizontalAdvance(item) + 8, lh, WHITE)
                    p.setPen(QColor("black"))
                else:
                    p.setPen(WHITE)
                p.drawText(m + 4, y, item)
            y += lh
        p.setPen(WHITE)
        p.drawText(m, self.height() - m - 2 * lh, "Description: " + {
            "Repair Your Computer": "View a list of system recovery tools you can use to repair startup problems, "
                                    "run diagnostics, or restore your system.",
            "Start Windows Normally": "Start Windows with its regular settings.",
            "Reinstall Windows (format drive C:)": "Erase drive C: and install Windows 7 again from the DVD.",
        }.get(self.menu[self.row], ""))
        p.drawText(m, self.height() - m, "ENTER=Choose                                        ESC=Cancel")
