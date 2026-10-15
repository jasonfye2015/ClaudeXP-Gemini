"""The disk check after an unclean shutdown: XP's blue autochk screen before the boot logo.

Windows marks C: as 'in use' while it runs (DIRTY_FILE) and clears the mark when it shuts down properly, so if
ClaudeXP crashed or was killed, the next boot finds the mark and checks the disk. Press any key during the
10-second countdown to skip it, as on the real thing; Esc skips the rest of the check at any time.
"""
import random
import time

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QWidget

from .paths import DATA

DIRTY_FILE = DATA / "dirty_shutdown"
COUNTDOWN = 10
BLUE = QColor("#00007F")


def needed():
    return DIRTY_FILE.exists()


def mark_running():
    """Windows has booted: C: is in use until a proper shutdown."""
    try:
        DIRTY_FILE.parent.mkdir(parents=True, exist_ok=True)
        DIRTY_FILE.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
    except OSError:
        pass


def mark_clean():
    try:
        DIRTY_FILE.unlink()
    except OSError:
        pass


def _disk():
    """Numbers for the summary, from the ClaudeXP C: drive."""
    from .explorer import vfs
    files = folders = used = 0
    if vfs.DRIVE_C.exists():
        for f in vfs.DRIVE_C.rglob("*"):
            try:
                if f.is_file():
                    files += 1
                    used += f.stat().st_size
                elif f.is_dir():
                    folders += 1
            except OSError:
                pass
    # a real XP install had tens of thousands of files; ours sit on top of them
    files += 38412
    folders += 3194
    total_kb = vfs.C_TOTAL // 1024
    free_kb = max(0, vfs.C_FREE - used) // 1024
    return files, folders, total_kb, free_kb


def _problems():
    """What the crash left behind (or nothing, most of the time)."""
    found = []
    roll = random.random()
    if roll < 0.45:
        n = random.randint(2, 40)
        found += ["Cleaning up minor inconsistencies on the drive.",
                  f"Cleaning up {n} unused index entries from index $SII of file 0x9.",
                  f"Cleaning up {n} unused index entries from index $SDH of file 0x9.",
                  f"Cleaning up {n} unused security descriptors."]
    if roll < 0.2:
        tmp = f"~DF{random.randint(0x1000, 0xFFFF):X}.TMP"
        rec = random.randint(20000, 60000)
        found += [f"Deleting index entry {tmp} in index $I30 of file {random.randint(25, 400)}.",
                  f"Recovering orphaned file {tmp} ({rec}) into directory file 5."]
    if roll < 0.08:
        found += ["Correcting errors in the Volume Bitmap."]
    return found


class ChkdskScreen(QWidget):
    """Emits finished() when the check is done or skipped."""
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lines = []
        self.progress_line = None         # index of the line showing 'NN percent completed.'
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._step)
        self.done = True
        self.setFocusPolicy(Qt.StrongFocus)

    # ---- the script ------------------------------------------------------------------------------------------
    def start(self):
        self.done = False
        self.counting = True
        self.left = COUNTDOWN
        self.lines = ["Checking file system on C:", "The type of the file system is NTFS.", "",
                      "One of your disks needs to be checked for consistency. You",
                      "may cancel the disk check, but it is strongly recommended",
                      "that you continue.", ""]
        self.lines.append(self._countdown_text())
        self.update()
        self.timer.start(1000)

    def _countdown_text(self):
        return f"To skip disk checking, press any key within {self.left} second(s)."

    def _begin_check(self):
        self.counting = False
        self.lines[-1] = "Windows will now check the disk."
        files, folders, total_kb, free_kb = _disk()
        problems = _problems()
        stages = [("files", "File verification completed."), ("indexes", "Index verification completed."),
                  ("security descriptors", "Security descriptor verification completed.")]
        self.script = []                  # ("line", text) | ("stage", n, name, done_text)
        for text in problems[:4]:
            self.script.append(("line", text))
        for n, (name, done) in enumerate(stages, 1):
            self.script.append(("stage", n, name, done))
        for text in problems[4:]:
            self.script.append(("line", text))
        fixed = bool(problems)
        unit = 4096
        sys_kb, log_kb, idx_kb = random.randint(90000, 120000), 65536, folders * 4
        file_kb = max(0, total_kb - free_kb - sys_kb - log_kb - idx_kb)
        summary = ["", "Windows has made corrections to the file system." if fixed
                   else "Windows has checked the file system and found no problems.", "",
                   f"{total_kb:>12} KB total disk space.",
                   f"{file_kb:>12} KB in {files} files.",
                   f"{idx_kb:>12} KB in {folders} indexes.",
                   f"{0:>12} KB in bad sectors.",
                   f"{sys_kb:>12} KB in use by the system.",
                   f"{log_kb:>12} KB occupied by the log file.",
                   f"{free_kb:>12} KB available on disk.", "",
                   f"{unit:>12} bytes in each allocation unit.",
                   f"{total_kb * 1024 // unit:>12} total allocation units on disk.",
                   f"{free_kb * 1024 // unit:>12} allocation units available on disk."]
        self.script += [("line", t) for t in summary]
        self.script.append(("wait", 3500))
        self.percent = None
        self.timer.start(60)

    def _step(self):
        if self.counting:
            self.left -= 1
            if self.left <= 0:
                self.timer.stop()
                self._begin_check()
            else:
                self.lines[-1] = self._countdown_text()
            self.update()
            return
        if not self.script:
            self._finish()
            return
        item = self.script[0]
        if item[0] == "line":
            self.lines.append(item[1])
            self.script.pop(0)
            self.timer.setInterval(120 if item[1] else 60)
        elif item[0] == "wait":
            self.script.pop(0)
            self.timer.setInterval(item[1])
        else:
            _kind, n, name, done = item
            if self.percent is None:
                self.lines.append(f"CHKDSK is verifying {name} (stage {n} of 3)...")
                self.lines.append("  0 percent completed.")
                self.progress_line = len(self.lines) - 1
                self.percent = 0
                # stage 1 (files) is the long one, as on a real disk
                self.speed = (0.9, 2.2) if n == 1 else (1.5, 4.0) if n == 2 else (3.0, 7.0)
                self.timer.setInterval(90)
            else:
                self.percent = min(100, self.percent + random.uniform(*self.speed))
                if self.percent >= 100:
                    self.lines[self.progress_line] = done
                    self.percent = None
                    self.script.pop(0)
                    self.timer.setInterval(400)
                else:
                    self.lines[self.progress_line] = f"{int(self.percent):3d} percent completed."
        self.update()

    def _finish(self):
        if self.done:
            return
        self.done = True
        self.timer.stop()
        mark_clean()
        self.finished.emit()

    # ---- skipping ----------------------------------------------------------------------------------------------
    def keyPressEvent(self, event):
        if self.done:
            return
        if self.counting:
            self.timer.stop()
            self.lines[-1] = "Disk checking has been cancelled."
            self.update()
            self.counting = False
            self.done = True
            QTimer.singleShot(700, self.finished.emit)
        elif event.key() == Qt.Key_Escape:
            self._finish()

    def mousePressEvent(self, event):
        if self.counting:
            self.keyPressEvent(event)

    # ---- drawing -----------------------------------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), BLUE)
        font = QFont("Lucida Console")
        font.setStyleHint(QFont.Monospace)
        size = max(11, min(18, self.height() // 40))
        font.setPixelSize(size)
        p.setFont(font)
        p.setPen(QColor("white"))
        line_h = int(size * 1.35)
        rows = max(1, (self.height() - 2 * line_h) // line_h)
        shown = self.lines[-rows:]
        x = max(10, self.width() // 40)
        for i, text in enumerate(shown):
            p.drawText(QRectF(x, line_h + i * line_h, self.width() - 2 * x, line_h),
                       Qt.AlignLeft | Qt.AlignVCenter, text)
