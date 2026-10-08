"""The text-mode screens: the System Recovery menu, 'Press any key to boot from CD...', and blue
text-mode Windows XP Setup (Welcome, licence, partitions, format, copying files, restart)."""
import random

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter
from PySide6.QtWidgets import QWidget

from .. import sound
from . import ms

COLS, ROWS = 80, 25
BLACK, BLUE = QColor("#000000"), QColor("#0000AA")
GREY, WHITE = QColor("#AAAAAA"), QColor("#FFFFFF")
YELLOW, RED = QColor("#FFFF55"), QColor("#AA0000")
DISK = "20480 MB Disk 0 at Id 0 on bus 0 on atapi [MBR]"
PART = "C:  Partition1 [NTFS]"
PART_SIZE = "19077 MB (  12841 MB free)"


class TextScreen(QWidget):
    """An 80x25 character screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.background = BLACK
        self.ops = []

    # drawing helpers (filled in by each page)
    def put(self, col, row, text, fg=GREY, bg=None):
        self.ops.append(("text", col, row, text, fg, bg))

    def fill(self, col, row, width, height, color):
        self.ops.append(("fill", col, row, width, height, color))

    def page(self):
        pass

    def _font(self, cw, ch):
        font = QFont("Lucida Console")
        font.setStyleHint(QFont.Monospace)
        size = max(6.0, ch * 0.78)
        font.setPixelSize(int(size))
        while QFontMetricsF(font).horizontalAdvance("M") > cw and size > 6:
            size -= 0.5
            font.setPixelSize(int(size))
        font.setLetterSpacing(QFont.AbsoluteSpacing, cw - QFontMetricsF(font).horizontalAdvance("M"))
        return font

    def paintEvent(self, event):
        self.ops = []
        self.page()
        p = QPainter(self)
        p.fillRect(self.rect(), self.background)
        cw, ch = self.width() / COLS, self.height() / ROWS
        font = self._font(cw, ch)
        p.setFont(font)
        ascent = QFontMetricsF(font).ascent()
        pad = (ch - QFontMetricsF(font).height()) / 2
        for op in self.ops:
            if op[0] == "fill":
                _, col, row, w, h, color = op
                p.fillRect(QRectF(col * cw, row * ch, w * cw, h * ch), color)
            else:
                _, col, row, text, fg, bg = op
                if bg is not None:
                    p.fillRect(QRectF(col * cw, row * ch, len(text) * cw, ch), bg)
                p.setPen(fg)
                p.drawText(QPointF(col * cw, row * ch + pad + ascent), text)


def wrap(text, width):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return lines


# ---- the OEM recovery menu (SPACE during the BIOS test) ------------------------------------------------------

class RecoveryMenu(TextScreen):
    start_normally = Signal()
    reinstall = Signal()

    ITEMS = ["Start Windows Normally", "Reinstall Windows XP from the System Recovery CD"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.choice = 0

    def reset(self):
        self.choice = 0
        self.update()

    def page(self):
        self.put(2, 1, "ClaudeXP System Recovery", WHITE)
        self.put(2, 2, "=" * 24, WHITE)
        self.put(2, 4, "Please select an option:")
        for i, item in enumerate(self.ITEMS):
            text = f"  {item}  "
            if i == self.choice:
                self.put(4, 6 + i, text.ljust(56), BLACK, GREY)
            else:
                self.put(4, 6 + i, text)
        lines = wrap("Reinstalling Windows erases drive C: and returns the computer to the way it was when it "
                     "came from the factory. Files on your external drive (E:) are not affected.", 72)
        for i, line in enumerate(lines):
            self.put(4, 10 + i, line)
        self.put(2, 21, "Use the UP and DOWN arrow keys to move the highlight to your choice.")
        self.put(2, 22, "Press ENTER to choose.")

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Up, Qt.Key_Down):
            self.choice = 1 - self.choice
            self.update()
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            (self.start_normally if self.choice == 0 else self.reinstall).emit()


class BootFromCD(TextScreen):
    """'Press any key to boot from CD...' with dots. A key boots Setup; otherwise Windows starts."""
    boot_cd = Signal()
    timed_out = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dots = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.active = False

    def start(self):
        self.dots, self.active = 0, True
        sound.play_clip(random.choice(["cdrom_startup1.mp3", "cdrom_startup2.mp3"]), 3500)
        self.timer.start(ms(700))
        self.update()

    def _tick(self):
        self.dots += 1
        self.update()
        if self.dots > 6:
            self._stop()
            self.timed_out.emit()

    def _stop(self):
        self.active = False
        self.timer.stop()

    def page(self):
        self.put(0, 1, "Press any key to boot from CD" + "." * self.dots)

    def keyPressEvent(self, event):
        if self.active:
            self._stop()
            self.boot_cd.emit()

    def mousePressEvent(self, event):
        pass


# ---- text-mode Setup --------------------------------------------------------------------------------------------------

LOADING = ["Windows Executive", "Hardware Abstraction Layer", "Windows Setup", "PCI IDE Bus Driver",
           "Intel IDE Controller", "ATAPI IDE CD-ROM Driver", "Disk Driver", "NTFS File System",
           "FAT/FAT32 File System", "Floppy Disk Driver", "Keyboard Driver", "Setup Font", "Fonts/Locale Specific Data"]
COPYING = ["hal.dll", "ntoskrnl.exe", "kernel32.dll", "user32.dll", "gdi32.dll", "shell32.dll", "comctl32.dll",
           "explorer.exe", "mshtml.dll", "wmp.dll", "msmsgs.exe", "notepad.exe", "winmine.exe", "freecell.exe",
           "sol.exe", "spider.exe", "mshearts.exe", "dfrgntfs.exe", "Bliss.bmp", "tahoma.ttf", "trebuc.ttf",
           "mmsys.cpl", "desk.cpl", "sysdm.cpl", "rasdlg.dll", "wininet.dll", "aim.exe", "netscape.exe",
           "mirc32.exe", "claudeai.exe", "oobe.exe", "msoobe.exe", "title.wma", "logonui.exe", "winlogon.exe"]

EULA = [
    "END-USER LICENSE AGREEMENT FOR CLAUDEXP (WINDOWS XP EDITION)",
    "",
    "PLEASE READ THIS CAREFULLY. By installing this software you agree that it is the year 2001,",
    "that dial-up is a perfectly reasonable way to reach the Internet, and that the Spider",
    "Solitaire deal you just lost was fair.",
    "",
    "1. GRANT OF LICENSE. You may install and use one copy of the software on one",
    "   imaginary computer, which lives inside a real one.",
    "",
    "2. YOUR BUDDIES. The people you meet on ClaudeAIM, FurNet IRC and PawPrints MUCK are",
    "   simulated. Reinstalling erases everything they remember about you; they will greet",
    "   you as a stranger.",
    "",
    "3. YOUR FILES. Formatting drive C: erases your documents, settings and saved games.",
    "   Setup moves them to the 'Recovery Backups' folder on the real computer, just in case.",
    "",
    "4. NO WARRANTY. The software is provided 'as is', including the modem noises.",
]


class TextSetup(TextScreen):
    quit_setup = Signal()
    reboot = Signal(bool, bool, bool)     # format C:, erase program history, erase buddies' memories

    FS_OPTIONS = ["Format the partition using the NTFS file system (Quick)",
                  "Format the partition using the NTFS file system",
                  "Leave the current file system intact (no changes)"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.state = "inspect"

    # ---- flow -------------------------------------------------------------------------------------------------
    def start(self):
        self.fs_choice = 0
        self.erase_programs = True
        self.erase_memories = True
        self.progress = 0
        self.status = ""
        self._go("inspect")
        QTimer.singleShot(ms(2500), lambda: self._go("loading") if self.state == "inspect" else None)

    def _go(self, state):
        self.state = state
        self.timer.stop()
        self.progress = 0
        self.background = BLACK if state == "inspect" else BLUE
        if state == "loading":
            sound.play_clip(random.choice(["cdrom_startup1.mp3", "cdrom_startup2.mp3"]), 5000)
            self.timer.start(ms(450))
        elif state == "starting":
            self.status = "Setup is starting Windows"
            QTimer.singleShot(ms(1800), lambda: self._go("welcome") if self.state == "starting" else None)
        elif state in ("format", "examine", "copy"):
            self.timer.start(ms(100))
            self._disk_noise()
        elif state == "init":
            QTimer.singleShot(ms(3500), lambda: self._go("restart") if self.state == "init" else None)
        elif state == "restart":
            self.progress = 15.0
            self.timer.start(ms(100))
        self.update()

    def _disk_noise(self):
        if self.state in ("format", "examine", "copy"):
            sound.play_clip(random.choice(["harddrive_startup1.mp3", "harddrive_startup2.mp3"]), 2500)
            QTimer.singleShot(ms(random.randint(2600, 5000)), self._disk_noise)

    def _tick(self):
        if self.state == "loading":
            self.progress += 1
            if self.progress >= len(LOADING):
                self._go("starting")
                return
            self.status = f"Setup is loading files ({LOADING[self.progress]})..."
        elif self.state in ("format", "examine"):
            # Quick format ~10 s, a full format ~45 s, examining disks ~6 s.
            seconds = {0: 10, 1: 45}.get(self.fs_choice, 6)
            self.progress = min(100, self.progress + 100 / (seconds * 10))
            if self.progress >= 100:
                self._go("copy")
                return
        elif self.state == "copy":
            self.progress = min(100, self.progress + 100 / (35 * 10))       # ~35 s
            self.status = f"Copying: {random.choice(COPYING)}" if random.random() < 0.3 else self.status
            if self.progress >= 100:
                self.status = ""
                self._go("init")
                return
        elif self.state == "restart":
            self.progress -= 0.1
            if self.progress <= 0:
                self._restart()
                return
        self.update()

    def _restart(self):
        self.timer.stop()
        self.state = "rebooting"
        self.reboot.emit(self.fs_choice < 2, self.erase_programs, self.erase_memories)

    # ---- keys ----------------------------------------------------------------------------------------------------
    def keyPressEvent(self, event):
        key, text = event.key(), event.text().lower()
        s = self.state
        if s == "welcome":
            if key in (Qt.Key_Return, Qt.Key_Enter):
                self._go("eula")
            elif key in (Qt.Key_F3, Qt.Key_Escape) or text == "q":
                self._go("quit")
        elif s == "eula":
            if key == Qt.Key_F8 or text == "y":
                self._go("partitions")
            elif key == Qt.Key_Escape:
                self._go("quit")
        elif s == "partitions":
            if key in (Qt.Key_Return, Qt.Key_Enter):
                self._go("filesystem")
            elif key in (Qt.Key_F3, Qt.Key_Escape) or text == "q":
                self._go("quit")
        elif s == "filesystem":
            if key == Qt.Key_Up:
                self.fs_choice = (self.fs_choice - 1) % 3
            elif key == Qt.Key_Down:
                self.fs_choice = (self.fs_choice + 1) % 3
            elif text == "p":
                self.erase_programs = not self.erase_programs
            elif text == "m":
                self.erase_memories = not self.erase_memories
            elif key in (Qt.Key_Return, Qt.Key_Enter):
                self._go("confirm" if self.fs_choice < 2 else "examine")
                return
            elif key == Qt.Key_Escape:
                self._go("partitions")
                return
            self.update()
        elif s == "confirm":
            if text == "f":
                self._go("format")
            elif key == Qt.Key_Escape:
                self._go("filesystem")
        elif s == "quit":
            if key == Qt.Key_F3 or text == "q":
                self.quit_setup.emit()
            elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape):
                self._go("welcome")
        elif s == "restart" and key in (Qt.Key_Return, Qt.Key_Enter):
            self._restart()

    # ---- pages ---------------------------------------------------------------------------------------------------------
    def header(self, title="Windows XP Home Edition Setup"):
        self.put(1, 1, title, WHITE)
        self.put(0, 2, "=" * (len(title) + 2), WHITE)

    def footer(self, text):
        self.fill(0, ROWS - 1, COLS, 1, GREY)
        self.put(2, ROWS - 1, text, BLACK, GREY)

    def para(self, col, row, text, width=72, fg=GREY):
        lines = wrap(text, width)
        for i, line in enumerate(lines):
            self.put(col, row + i, line, fg)
        return row + len(lines)

    def bullet(self, col, row, text, width=66):
        lines = wrap(text, width)
        self.put(col, row, "•", GREY)
        for i, line in enumerate(lines):
            self.put(col + 3, row + i, line, GREY)
        return row + len(lines)

    def box_bar(self, row, label, color=YELLOW):
        """The progress box: a label, a frame, and a filling bar with its percentage."""
        left, width = 14, 52
        self.fill(left, row, width, 6, GREY)
        self.put(left + (width - len(label)) // 2, row + 1, label, BLACK, GREY)
        pct = f"{int(self.progress)}%"
        self.put(left + (width - len(pct)) // 2, row + 2, pct, BLACK, GREY)
        self.fill(left + 2, row + 3, width - 4, 1, WHITE)
        self.fill(left + 2, row + 3, (width - 4) * self.progress / 100, 1, color)

    def page(self):
        getattr(self, "page_" + self.state, lambda: None)()

    def page_inspect(self):
        self.put(1, 1, "Setup is inspecting your computer's hardware configuration...")

    def page_loading(self):
        self.header("Windows Setup")
        self.footer(self.status)

    def page_starting(self):
        self.header("Windows Setup")
        self.footer(self.status)

    def page_welcome(self):
        self.header()
        self.put(3, 4, "Welcome to Setup.", WHITE)
        r = self.para(3, 6, "This portion of the Setup program prepares Microsoft(R) Windows(R) XP to run on your computer.")
        r = self.bullet(6, r + 1, "To set up Windows XP now, press ENTER.")
        r = self.bullet(6, r + 1, "To repair a Windows XP installation using Recovery Console, press R.", 70)
        self.bullet(6, r + 1, "To quit Setup without installing Windows XP, press F3 (or Q).")
        self.footer("ENTER=Continue  R=Repair  F3 (or Q)=Quit")

    def page_eula(self):
        self.put(1, 1, "Windows XP Licensing Agreement", WHITE)
        self.fill(2, 3, 76, 19, GREY)
        for i, line in enumerate(EULA):
            self.put(3, 4 + i, line, BLACK, GREY)
        self.footer("F8 (or Y)=I agree  ESC=I do not agree  PAGE DOWN=Next Page")

    def page_partitions(self):
        self.header()
        r = self.para(3, 4, "The following list shows the existing partitions and unpartitioned space on this computer.")
        r = self.para(3, r + 1, "Use the UP and DOWN ARROW keys to select an item in the list.")
        r = self.bullet(6, r + 1, "To set up Windows XP on the selected item, press ENTER.")
        r = self.bullet(6, r + 1, "To create a partition in the unpartitioned space, press C.")
        r = self.bullet(6, r + 1, "To delete the selected partition, press D.")
        top = r + 1
        self.fill(3, top, 74, 7, GREY)
        self.put(5, top + 1, DISK, BLACK, GREY)
        self.put(8, top + 3, f"{PART:<36}{PART_SIZE}".ljust(66), WHITE, BLUE)
        self.put(8, top + 4, f"{'    Unpartitioned space':<36}{'8 MB':>10}", BLACK, GREY)
        self.footer("ENTER=Install  D=Delete Partition  F3 (or Q)=Quit")

    def page_filesystem(self):
        self.header()
        r = self.para(3, 3, f"Setup will install Windows XP on partition {PART} {PART_SIZE} on {DISK}.")
        r = self.para(3, r + 1, "Use the UP and DOWN ARROW keys to select the file system you want, and then press ENTER. "
                                "If you want to select a different partition for Windows XP, press ESC.")
        top = r + 1
        for i, option in enumerate(self.FS_OPTIONS):
            line = f" {option} ".ljust(60)
            if i == self.fs_choice:
                self.put(6, top + i, line, BLUE, GREY)
            else:
                self.put(6, top + i, line)
        r = top + 4
        if self.fs_choice < 2:
            r = self.para(6, r, "Formatting erases everything on C: (Windows settings, your documents, desktop "
                                "and saved games). Also erase:", 68)
        else:
            r = self.para(6, r, "Your documents and files are kept; Windows settings go back to their defaults. "
                                "Also erase:", 68)
        for i, (letter, label, on) in enumerate((
                ("P", "Program history (ClaudeAIM, IRC, MUCK, ClaudeAI, Netscape)", self.erase_programs),
                ("M", "Buddies' memories of you (journals, stories, e-mail)", self.erase_memories))):
            row = r + 1 + i
            self.put(8, row, f"[{'X' if on else ' '}]", WHITE)
            self.put(12, row, label, WHITE if on else GREY)
            self.put(13 + len(label), row, f"({letter})")
        self.para(6, r + 4, "Files on your external drive (E:) are never erased.", 68)
        self.footer("ENTER=Continue  P,M=Check/Uncheck  ESC=Cancel")

    def page_confirm(self):
        self.header()
        self.put(3, 4, "WARNING:", WHITE)
        r = self.para(12, 4, "Formatting this partition will delete all files on it.", 62)
        r = self.para(3, r + 1, f"{PART} {PART_SIZE}")
        erasing = ["your files and settings on C:"]
        if self.erase_programs:
            erasing.append("your program history")
        if self.erase_memories:
            erasing.append("everything your buddies remember about you")
        r = self.para(3, r + 1, "Setup will erase " + ", ".join(erasing[:-1]) + (" and " if len(erasing) > 1 else "")
                      + erasing[-1] + ".")
        r = self.bullet(6, r + 1, "To format the drive, press F.")
        self.bullet(6, r + 1, "To select a different file system, press ESC.")
        self.footer("F=Format  ESC=Cancel")

    def page_format(self):
        self.header()
        self.para(3, 5, f"Please wait while Setup formats the partition {PART} {PART_SIZE} on {DISK}.")
        self.box_bar(11, "Setup is formatting...")

    def page_examine(self):
        self.header()
        self.para(3, 5, "Please wait while Setup examines your disks. This might take several minutes, depending "
                        "on the size of the disks.")
        self.box_bar(11, "Setup is examining your disks...")

    def page_copy(self):
        self.header()
        self.para(3, 5, "Please wait while Setup copies files to the Windows installation folders. This might take "
                        "several minutes to complete.")
        self.box_bar(11, "Setup is copying files...")
        self.footer(self.status)

    def page_init(self):
        self.header()
        self.para(3, 5, "Please wait while Setup initializes your Windows XP configuration.")

    def page_restart(self):
        self.header()
        r = self.para(3, 4, "This portion of Setup has completed successfully.")
        r = self.para(3, r + 1, "If there is a floppy disk in drive A:, remove it.")
        r = self.para(3, r + 1, "To restart your computer, press ENTER. When your computer restarts, Setup will continue.")
        self.fill(14, r + 3, 52, 4, GREY)
        secs = max(0, int(self.progress + 0.99))
        label = f"Your computer will reboot in {secs} seconds..."
        self.put(14 + (52 - len(label)) // 2, r + 4, label, BLACK, GREY)
        self.fill(16, r + 5, 48, 1, WHITE)
        self.fill(16, r + 5, 48 * self.progress / 15, 1, RED)
        self.footer("ENTER=Restart Computer")

    def page_rebooting(self):
        self.background = BLACK

    def page_quit(self):
        self.header()
        self.fill(10, 6, 60, 11, GREY)
        self.put(13, 7, "Windows XP is not completely set up on your computer.", BLACK, GREY)
        self.put(13, 8, "If you quit Setup now, you will need to run Setup", BLACK, GREY)
        self.put(13, 9, "again to set up Windows XP.", BLACK, GREY)
        self.put(16, 11, "•  To continue Setup, press ENTER.", BLACK, GREY)
        self.put(16, 12, "•  To quit Setup, press F3 (or Q).", BLACK, GREY)
        self.put(13, 14, "Your current Windows installation is not changed.", BLACK, GREY)
        self.footer("F3 (or Q)=Quit  ENTER=Continue")
