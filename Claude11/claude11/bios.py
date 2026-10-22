"""Power on: the ASUS UEFI splash of a 2025 PC (the Intel badge, the glowing Windows logo, ASUS underneath), the
ASUS UEFI BIOS Utility behind DEL or F2, and the Windows Recovery Environment behind F8 (Troubleshoot > Reset this
PC reinstalls Windows). Modern boards have no speaker and NVMe drives make no sound: the self test is silent.

The splash is the user's own picture (assets/images/boot/asus_splash.png); the boot screen keeps it up and adds the
spinning dots under the logo (boot.py)."""
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from .paths import IMAGES

WHITE = QColor("#FFFFFF")
GREY = QColor("#9A9A9A")
SPLASH_FILE = IMAGES / "boot" / "asus_splash.png"
POST_MS = 2600                 # how long the splash stays before Windows starts (a fast UEFI board)
_splash = None


def splash():
    global _splash
    if _splash is None:
        _splash = QPixmap(str(SPLASH_FILE))
    return _splash


def draw_splash(p, widget, with_text=True, dim=0):
    """The ASUS splash scaled to the screen, black behind it; the DEL/F2 line along the bottom during the self test."""
    p.fillRect(widget.rect(), QColor("black"))
    pm = splash()
    if not pm.isNull():
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        scale = min(widget.width() / pm.width(), widget.height() / pm.height())
        w, h = pm.width() * scale, pm.height() * scale
        p.drawPixmap(QRectF((widget.width() - w) / 2, (widget.height() - h) / 2, w, h), pm, QRectF(pm.rect()))
    else:
        draw_logo(p, widget.width() / 2, widget.height() * 0.46, min(widget.width(), widget.height()) * 0.12)
    if dim:
        p.fillRect(widget.rect(), QColor(0, 0, 0, dim))
    if with_text:
        f = QFont("Segoe UI")
        f.setPixelSize(max(12, widget.height() // 54))
        p.setFont(f)
        p.setPen(GREY)
        p.drawText(QRectF(24, widget.height() - 48, widget.width() - 48, 24), Qt.AlignLeft | Qt.AlignVCenter,
                   "Please press DEL or F2 to enter UEFI BIOS setting")


def logo_rect(widget):
    """Where the Windows logo sits in the splash as drawn: (center x, center y, half size), for the spinner."""
    pm = splash()
    if pm.isNull():
        s = min(widget.width(), widget.height()) * 0.12
        return widget.width() / 2, widget.height() * 0.46, s
    scale = min(widget.width() / pm.width(), widget.height() / pm.height())
    w, h = pm.width() * scale, pm.height() * scale
    ox, oy = (widget.width() - w) / 2, (widget.height() - h) / 2
    # the logo in the user's picture: centred, about 48% down, 11% of the picture's height tall
    return ox + w * 0.5, oy + h * 0.483, h * 0.055


def draw_logo(p, cx, cy, half, colour="#45C8FF", glow=True):
    """Windows 11's logo: four squares, simple enough not to need a picture."""
    p.setRenderHint(QPainter.Antialiasing)
    if glow:
        for i in range(6, 0, -1):
            c = QColor(colour)
            c.setAlpha(int(14 * (1 - i / 7)))
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawRoundedRect(QRectF(cx - half - i * half * 0.35, cy - half - i * half * 0.35,
                                     2 * half + i * half * 0.7, 2 * half + i * half * 0.7), half * 0.3, half * 0.3)
    gap = half * 0.08
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(colour))
    for dx in (-1, 1):
        for dy in (-1, 1):
            x = cx + (gap / 2 if dx > 0 else -half)
            y = cy + (gap / 2 if dy > 0 else -half)
            p.drawRoundedRect(QRectF(x, y, half - gap / 2, half - gap / 2), half * 0.06, half * 0.06)


class BiosScreen(QWidget):
    """The UEFI self test: the splash, a moment, then Windows. DEL/F2 for Setup, F8 for the recovery menu."""
    finished = Signal()
    setup_requested = Signal()
    boot_menu_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._after_post)
        self._done = True
        self.recovery_requested = False
        self.setup_wanted = False
        self.note = ""
        self.setFocusPolicy(Qt.StrongFocus)

    def start(self, recovery=False):
        self._done = False
        self.recovery_requested = recovery
        self.setup_wanted = False
        self.note = "Advanced startup requested..." if recovery else ""
        self.timer.start(POST_MS)
        self.update()

    def _after_post(self):
        if self._done:
            return
        if self.setup_wanted:
            self._enter_setup()
        elif self.recovery_requested:
            self._boot_menu()
        else:
            self._finish()

    def _enter_setup(self):
        self._done = True
        self._stop_timers()
        self.setup_requested.emit()

    def _boot_menu(self):
        self._done = True
        self._stop_timers()
        self.boot_menu_requested.emit()

    def _stop_timers(self):
        self.timer.stop()

    def _finish(self):
        if self._done:
            return
        self._done = True
        self._stop_timers()
        self.finished.emit()

    def mousePressEvent(self, event):
        self._after_post()

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        key = event.key()
        if key in (Qt.Key_Delete, Qt.Key_F2):
            if not self.setup_wanted:
                self.setup_wanted = True
                self.note = "Entering UEFI BIOS setting..."
                self.update()
            return
        if key in (Qt.Key_F8, Qt.Key_Space):
            if not self.recovery_requested:
                self.recovery_requested = True
                self.note = "Advanced startup requested..."
                self.update()
            return
        if self._done:
            return
        self._after_post()

    def paintEvent(self, event):
        p = QPainter(self)
        draw_splash(p, self, with_text=True)
        if self.note:
            f = QFont("Segoe UI")
            f.setPixelSize(max(12, self.height() // 54))
            p.setFont(f)
            p.setPen(WHITE)
            p.drawText(QRectF(24, self.height() - 48, self.width() - 48, 24), Qt.AlignRight | Qt.AlignVCenter,
                       self.note)


# ---- the ASUS UEFI BIOS Utility --------------------------------------------------------------------------------
PANEL = QColor("#1E232B")
PANEL_LIGHT = QColor("#2A313B")
ASUS_BLUE = QColor("#2D8CEB")
TEXT = QColor("#E6E9EE")
DIM = QColor("#8A94A3")
SETUP_TABS = ["My Favorites", "Main", "Ai Tweaker", "Advanced", "Monitor", "Boot", "Tool", "Exit"]
SETUP_PAGES = {
    "My Favorites": [("CPU Core Ratio", "[Auto]", "Set the CPU core ratio."),
                     ("DRAM Frequency", "[DDR5-6000]", "EXPO profile loaded: DDR5-6000 CL30."),
                     ("Resizable BAR", "[Enabled]", ""), ("Fast Boot", "[Enabled]", "")],
    "Main": [("System Language", "[English]", "Choose the system default language."),
             ("System Date", "[{date}]", "Set the system date."), ("System Time", "[{time}]", "Set the system time."),
             ("", "", ""),
             ("BIOS Information", "", "ASUS TUF GAMING B650-PLUS WIFI\nBIOS Version 3222  Build Date 08/18/2025\n"
                                      "EC Version MBEC-B650-0506"),
             ("Processor Information", "", "AMD Ryzen 7 7800X3D 8-Core Processor\nSpeed : 4200 MHz\n"
                                           "Total Memory : 32768 MB (DDR5)"),
             ("Security", "", "Administrator Password : Not Installed\nUser Password : Not Installed")],
    "Ai Tweaker": [("Ai Overclock Tuner", "[EXPO I]", "Load the memory module's EXPO profile."),
                   ("Precision Boost Overdrive", "[Auto]", ""), ("Curve Optimizer", "[Negative 20]", ""),
                   ("DRAM Voltage", "[1.350]", ""), ("SoC Voltage", "[Auto]", "")],
    "Advanced": [("Trusted Computing", "", "fTPM 2.0 : Enabled (Windows 11 needs it)."),
                 ("CPU Configuration", "", "SVM Mode : Enabled"), ("PCI Subsystem Settings", "", "Above 4G Decoding"),
                 ("USB Configuration", "", "Legacy USB Support : Enabled"),
                 ("Onboard Devices Configuration", "", "Wi-Fi 6E : Enabled    Bluetooth : Enabled\nRealtek 2.5G LAN"),
                 ("NVMe Configuration", "", "M.2_1 : Samsung SSD 990 PRO 2TB")],
    "Monitor": [("CPU Temperature", "[  41C /105F ]", ""), ("MotherBoard Temperature", "[  34C / 93F ]", ""),
                ("CPU Fan Speed", "[ 1150 RPM ]", ""), ("Chassis Fan 1 Speed", "[  820 RPM ]", ""),
                ("CPU Core Voltage", "[ 1.188 V ]", ""), ("Q-Fan Configuration", "", "Tune every fan's curve.")],
    "Boot": [("Boot Option #1", "[Windows Boot Manager (Samsung SSD 990 PRO 2TB)]", ""),
             ("Boot Option #2", "[UEFI: SanDisk SSD (External Drive)]", ""),
             ("Fast Boot", "[Enabled]", "Skip the slow parts of POST."),
             ("Boot Logo Display", "[Auto]", "Show the full screen logo during POST."),
             ("POST Delay Time", "[3 sec]", "Extra time to press DEL or F2."),
             ("CSM (Compatibility Support Module)", "[Disabled]", "UEFI only: Secure Boot stays on."),
             ("Secure Boot", "[Windows UEFI mode]", "")],
    "Tool": [("ASUS EZ Flash 3 Utility", "", "Update the BIOS from a file."), ("ASUS Armoury Crate", "[Enabled]", ""),
             ("ASUS User Profile", "", "Save and load overclocking profiles."), ("ASUS SPD Information", "", "")],
    "Exit": [("Save Changes & Reset", "", "Save and restart the computer."),
             ("Discard Changes & Exit", "", "Leave without saving."),
             ("Discard Changes", "", "Throw away the changes made so far."),
             ("Load Optimized Defaults", "", "Load the board's default settings."),
             ("Launch EFI Shell from USB drives", "", "")],
}


class BiosSetup(QWidget):
    """The ASUS UEFI BIOS Utility - Advanced Mode: tabs along the top, a dark panel, the help column on the right.
    Arrow keys look around; Esc or F10 leaves and boots."""
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab = 1
        self.row = 0
        self.setFocusPolicy(Qt.StrongFocus)

    def reset(self):
        self.tab, self.row = 1, 0
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

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        for i, rect in enumerate(self._tab_rects()):
            if rect.contains(pos):
                self.tab, self.row = i, 0
                self.update()
                return
        for i, rect in self._row_rects():
            if rect.contains(pos):
                self.row = i
                self.update()
                return

    def _font(self, size):
        f = QFont("Segoe UI")
        f.setPixelSize(size)
        return f

    def _metrics(self):
        size = max(12, self.height() // 42)
        return size, QFontMetrics(self._font(size))

    def _tab_rects(self):
        size, fm = self._metrics()
        rects, x = [], 24
        for name in SETUP_TABS:
            w = fm.horizontalAdvance(name) + 2 * size
            rects.append(QRectF(x, 60 + size, w, size * 2))
            x += w + 2
        return rects

    def _row_rects(self):
        size, fm = self._metrics()
        lh = size * 2
        page = SETUP_PAGES[SETUP_TABS[self.tab]]
        top = 60 + size * 3 + 16
        out = []
        for i, (label, _v, _h) in enumerate(page):
            if label:
                out.append((i, QRectF(32, top + i * lh, self.width() * 0.62 - 48, lh)))
        return out

    def paintEvent(self, event):
        from . import clock
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), PANEL)
        size, fm = self._metrics()
        w, h = self.width(), self.height()
        # the header: ASUS, the utility's name, the date and time
        p.fillRect(0, 0, w, 60, QColor("#14181E"))
        f = self._font(size + 8)
        f.setBold(True)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(TEXT)
        p.drawText(QRectF(24, 0, 200, 60), Qt.AlignLeft | Qt.AlignVCenter, "/SUS")
        p.setFont(self._font(size))
        p.setPen(DIM)
        p.drawText(QRectF(130, 0, 400, 60), Qt.AlignLeft | Qt.AlignVCenter, "UEFI BIOS Utility - Advanced Mode")
        now = clock.now()
        p.setPen(TEXT)
        p.drawText(QRectF(w - 320, 0, 296, 60), Qt.AlignRight | Qt.AlignVCenter,
                   f"{now:%m/%d/%Y}   {now:%H:%M}")
        p.setPen(ASUS_BLUE)
        p.drawText(QRectF(w - 320, 30, 296, 30), Qt.AlignRight | Qt.AlignVCenter, "English    EZ Mode (F7)")
        # the tabs
        for i, (name, rect) in enumerate(zip(SETUP_TABS, self._tab_rects())):
            if i == self.tab:
                p.setPen(Qt.NoPen)
                p.setBrush(ASUS_BLUE)
                p.drawRoundedRect(rect, 3, 3)
                p.setPen(WHITE)
            else:
                p.setPen(DIM)
            p.drawText(rect, Qt.AlignCenter, name)
        # the two panels
        top = 60 + size * 3 + 8
        split = int(w * 0.62)
        p.setPen(Qt.NoPen)
        p.setBrush(PANEL_LIGHT)
        p.drawRoundedRect(QRectF(16, top, split - 24, h - top - 90), 4, 4)
        p.drawRoundedRect(QRectF(split + 8, top, w - split - 24, h - top - 90), 4, 4)
        page = SETUP_PAGES[SETUP_TABS[self.tab]]
        lh = size * 2
        y = top + 8
        for i, (label, value, _help) in enumerate(page):
            value = value.format(time=now.strftime("%H:%M:%S"), date=now.strftime("%m/%d/%Y"))
            row = QRectF(32, y + i * lh, split - 56, lh)
            if i == self.row and label:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#3B4654"))
                p.drawRoundedRect(row, 3, 3)
            p.setPen(TEXT if label else DIM)
            p.drawText(row.adjusted(10, 0, 0, 0), Qt.AlignLeft | Qt.AlignVCenter, label)
            if value:
                p.setPen(ASUS_BLUE if i == self.row else TEXT)
                p.drawText(row.adjusted(0, 0, -10, 0), Qt.AlignRight | Qt.AlignVCenter, value)
        # the help column
        p.setPen(TEXT)
        hy = top + 12
        text = page[self.row][2] if self.row < len(page) else ""
        for line in text.split("\n"):
            while line:
                cut = len(line)
                while fm.horizontalAdvance(line[:cut]) > w - split - 56 and cut > 1:
                    cut = line.rfind(" ", 0, cut) if " " in line[:cut] else cut - 1
                p.drawText(QRectF(split + 20, hy, w - split - 48, lh), Qt.AlignLeft | Qt.AlignVCenter, line[:cut])
                line = line[cut:].lstrip()
                hy += lh
        # the legend
        p.setPen(DIM)
        legend = "Version 2.22.1288 Copyright (C) 2025 AMI      Left/Right: Select Screen   Up/Down: Select Item   " \
                 "Enter: Select   F10: Save & Exit   ESC: Exit"
        p.drawText(QRectF(16, h - 70, w - 32, 30), Qt.AlignLeft | Qt.AlignVCenter,
                   fm.elidedText(legend, Qt.ElideRight, w - 32))
        p.setPen(ASUS_BLUE)
        p.drawText(QRectF(16, h - 40, w - 32, 30), Qt.AlignRight | Qt.AlignVCenter,
                   "Last Modified   EzMode(F7)   Hot Keys(F9)   Search(F9)   AURA(F4)")


# ---- Windows Recovery Environment (F8) -----------------------------------------------------------------------
WINRE_BLUE = QColor("#0063B1")
MAIN_OPTIONS = [("Continue", "Exit and continue to Windows 11"), ("Use a device", "Use a USB drive, network "
                "connection, or Windows recovery DVD"), ("Troubleshoot", "Reset your PC or see advanced options"),
                ("Turn off your PC", "")]
TROUBLE_OPTIONS = [("Reset this PC", "Lets you choose to keep or remove your personal files, and then reinstalls "
                    "Windows."), ("Advanced options", ""), ("Back", "")]
ADVANCED_OPTIONS = [("Startup Repair", "Fix problems that keep Windows from loading"),
                    ("Startup Settings", "Change Windows startup behavior (Safe Mode)"),
                    ("System Restore", "Use a restore point recorded on your PC to restore Windows"),
                    ("UEFI Firmware Settings", "Change settings in your PC's UEFI firmware"),
                    ("Uninstall Updates", "Remove recently installed quality or feature updates from Windows"),
                    ("Command Prompt", "Use the Command Prompt for advanced troubleshooting"), ("Back", "")]


class BootOptions(QWidget):
    """'Choose an option' on the recovery environment's blue, with its tiles."""
    start_normally = Signal()
    safe_mode = Signal()
    reinstall = Signal()
    restart = Signal()
    firmware = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.menu = MAIN_OPTIONS
        self.title = "Choose an option"
        self.row = 0
        self.hover = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    def reset(self):
        self.menu, self.title, self.row = MAIN_OPTIONS, "Choose an option", 0
        self.update()

    def _tiles(self):
        w = min(560, self.width() - 80)
        x = (self.width() - w) // 2
        y = int(self.height() * 0.3)
        out = []
        for i, (label, _d) in enumerate(self.menu):
            out.append((i, QRectF(x, y + i * 74, w, 64)))
        return out

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Down:
            self.row = (self.row + 1) % len(self.menu)
        elif key == Qt.Key_Up:
            self.row = (self.row - 1) % len(self.menu)
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            self._choose(self.menu[self.row][0])
            return
        elif key == Qt.Key_Escape:
            if self.menu is MAIN_OPTIONS:
                self.start_normally.emit()
            else:
                self._back()
            return
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.position()
        hover = next((i for i, r in self._tiles() if r.contains(pos)), None)
        if hover != self.hover:
            self.hover = hover
            self.update()

    def mousePressEvent(self, event):
        pos = event.position()
        for i, r in self._tiles():
            if r.contains(pos):
                self.row = i
                self._choose(self.menu[i][0])
                return

    def _back(self):
        if self.menu is ADVANCED_OPTIONS:
            self.menu, self.title, self.row = TROUBLE_OPTIONS, "Troubleshoot", 0
        else:
            self.reset()
        self.update()

    def _choose(self, item):
        if item == "Troubleshoot":
            self.menu, self.title, self.row = TROUBLE_OPTIONS, "Troubleshoot", 0
        elif item == "Advanced options":
            self.menu, self.title, self.row = ADVANCED_OPTIONS, "Advanced options", 0
        elif item == "Back":
            self._back()
            return
        elif item == "Reset this PC":
            self.reinstall.emit()
            return
        elif item == "Turn off your PC":
            self.restart.emit()
            return
        elif item == "Startup Settings":
            self.safe_mode.emit()
            return
        elif item == "UEFI Firmware Settings":
            self.firmware.emit()
            return
        else:
            self.start_normally.emit()
            return
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), WINRE_BLUE)
        f = QFont("Segoe UI")
        f.setPixelSize(max(26, self.height() // 22))
        f.setWeight(QFont.Light)
        p.setFont(f)
        p.setPen(WHITE)
        tiles = self._tiles()
        x = tiles[0][1].x() if tiles else 40
        p.drawText(QRectF(x, self.height() * 0.3 - 90, 600, 60), Qt.AlignLeft | Qt.AlignVCenter, self.title)
        for i, r in tiles:
            label, desc = self.menu[i]
            hot = i == self.row or i == self.hover
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 60 if hot else 30))
            p.drawRoundedRect(r, 4, 4)
            f = QFont("Segoe UI")
            f.setPixelSize(17)
            p.setFont(f)
            p.setPen(WHITE)
            p.drawText(r.adjusted(16, 0, -16, 0 if not desc else -26), Qt.AlignLeft | Qt.AlignVCenter, label)
            if desc:
                f.setPixelSize(12)
                p.setFont(f)
                p.setPen(QColor(230, 240, 255, 220))
                p.drawText(r.adjusted(16, 30, -16, -8), Qt.AlignLeft | Qt.AlignVCenter,
                           QFontMetrics(f).elidedText(desc, Qt.ElideRight, int(r.width() - 32)))
        f = QFont("Segoe UI")
        f.setPixelSize(13)
        p.setFont(f)
        p.setPen(QColor(230, 240, 255, 200))
        p.drawText(QRectF(0, self.height() - 60, self.width(), 24), Qt.AlignCenter,
                   "Use the arrow keys and Enter, or click an option.   Esc goes back.")
