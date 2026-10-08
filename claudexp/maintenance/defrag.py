"""Disk Defragmenter: the striped red/blue/green/white disk map, slowly tidied left to right."""
import random

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
                               QWidget)
from shiboken6 import isValid

from .. import sound
from ..wm import XPWindow
from . import CoverClock

FRAG, CONTIG, SYSTEM, FREE = range(4)
COLORS = {FRAG: QColor("#E00000"), CONTIG: QColor("#0000E0"), SYSTEM: QColor("#00A000"), FREE: QColor("#FFFFFF")}
CELLS = 220
FILES = [r"\WINDOWS\system32\shell32.dll", r"\WINDOWS\system32\mshtml.dll", r"\WINDOWS\Prefetch\NETSCAPE.EXE-1A2B.pf",
         r"\Program Files\ClaudeAIM\data\history\KittyKat.json", r"\WINDOWS\Temp\~DF3A2.tmp",
         r"\Documents and Settings\{user}\My Documents\My Music\smashmouth_allstar.mp3",
         r"\Documents and Settings\{user}\Local Settings\Temporary Internet Files\Content.IE5\index[1].htm",
         r"\Program Files\Netscape\data\cache\furrycities.html", r"\WINDOWS\system32\dllcache\explorer.exe",
         r"\Documents and Settings\{user}\My Documents\My Pictures\fursuit035.jpg", r"\pagefile.sys",
         r"\WINDOWS\system32\config\software", r"\Program Files\ClaudeIRC\data\queries\ArcticFox.json",
         r"\WINDOWS\Fonts\tahoma.ttf", r"\Documents and Settings\{user}\NTUSER.DAT"]

_window = None


def icon_pixmap(size=16):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    s = size / 16
    for i, c in enumerate((FRAG, CONTIG, FRAG, SYSTEM, CONTIG, FREE)):
        p.fillRect(int((1 + i * 2.3) * s), int(3 * s), max(1, int(2.3 * s)), int(10 * s), COLORS[c])
    p.setPen(QPen(QColor("#404040"), 1))
    p.drawRect(int(s), int(3 * s), int(14 * s), int(10 * s))
    p.end()
    return pm


def running():
    return _window is not None and isValid(_window) and _window.content.clock is not None


class DiskMap(QWidget):
    def __init__(self):
        super().__init__()
        self.cells = []
        self.setFixedHeight(42)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("white"))
        if self.cells:
            w = self.width() / len(self.cells)
            for i, c in enumerate(self.cells):
                p.fillRect(int(i * w), 2, max(1, int(w + 0.99)), self.height() - 4, COLORS[c])
        p.setPen(QPen(QColor("#7F9DB9"), 1))
        p.drawRect(0, 0, self.width() - 1, self.height() - 1)


class Defrag(QWidget):
    def __init__(self, desktop):
        super().__init__()
        from ..user import user_name
        self.desktop = desktop
        self.user = user_name()
        self.clock = None
        self.automatic = False
        self.setStyleSheet("QWidget#defrag { background: #ECE9D8; } QLabel { font-family: Tahoma; font-size: 11px; }")
        self.setObjectName("defrag")
        self.setAttribute(Qt.WA_StyledBackground, True)
        rnd = random.Random()
        self.before = []
        for i in range(CELLS):
            if i < 8 or 100 <= i < 104:
                self.before.append(SYSTEM)
            else:
                self.before.append(rnd.choices((FRAG, CONTIG, FREE), weights=(3, 4, 3))[0])

        vols = QTreeWidget()
        vols.setHeaderLabels(["Volume", "Session Status", "File System", "Capacity", "Free Space", "% Free Space"])
        vols.setRootIsDecorated(False)
        vols.setFixedHeight(64)
        vols.setStyleSheet("QTreeWidget { background: white; }")
        self.vol_item = QTreeWidgetItem(["(C:)", "", "NTFS", "19.53 GB", "7.21 GB", "36 %"])
        vols.addTopLevelItem(self.vol_item)
        for i, wdt in enumerate((60, 110, 70, 70, 70, 80)):
            vols.setColumnWidth(i, wdt)

        self.before_map = DiskMap()
        self.after_map = DiskMap()
        self.status = QLabel(" ")
        self.analyze_btn = QPushButton("Analyze")
        self.defrag_btn = QPushButton("Defragment")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        buttons = QHBoxLayout()
        for b in (self.analyze_btn, self.defrag_btn, self.stop_btn):
            b.setFixedSize(85, 23)
            buttons.addWidget(b)
        buttons.addStretch()
        legend = QHBoxLayout()
        for label, kind in (("Fragmented files", FRAG), ("Contiguous files", CONTIG),
                            ("Unmovable files", SYSTEM), ("Free space", FREE)):
            sw = QLabel()
            pm = QPixmap(12, 12)
            pm.fill(COLORS[kind])
            sw.setPixmap(pm)
            sw.setStyleSheet("border: 1px solid #808080;")
            legend.addWidget(sw)
            legend.addWidget(QLabel(label))
            legend.addSpacing(10)
        legend.addStretch()

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.addWidget(vols)
        root.addWidget(QLabel("Estimated disk usage before defragmentation:"))
        root.addWidget(self.before_map)
        root.addWidget(QLabel("Estimated disk usage after defragmentation:"))
        root.addWidget(self.after_map)
        root.addLayout(buttons)
        root.addWidget(self.status)
        root.addLayout(legend)

        self.analyze_btn.clicked.connect(self.analyze)
        self.defrag_btn.clicked.connect(lambda: self.defragment())
        self.stop_btn.clicked.connect(self.stop)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def analyze(self):
        self.before_map.cells = list(self.before)
        self.before_map.update()
        frag = sum(1 for c in self.before if c == FRAG) * 100 // CELLS
        self.vol_item.setText(1, "Analyzed")
        self.status.setText(f"Analysis is complete for: (C:)  -  {frag}% of the files are fragmented. "
                            "You should defragment this volume.")

    def defragment(self, automatic=False):
        if self.clock is not None:
            return
        self.automatic = automatic
        self.analyze()
        self.after_map.cells = list(self.before)
        self.clock = CoverClock(random.uniform(150, 300))
        self.vol_item.setText(1, "Defragmenting...")
        self.analyze_btn.setEnabled(False)
        self.defrag_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.timer.start(250)

    def _target(self):
        """Where everything ends up: files packed to the front, free space at the end."""
        used = sum(1 for c in self.before if c in (FRAG, CONTIG))
        final, n = [], 0
        for c in self.before:
            if c == SYSTEM:
                final.append(SYSTEM)
            else:
                final.append(CONTIG if n < used else FREE)
                n += 1
        return final

    def _tick(self):
        f = self.clock.fraction()
        upto = int(f * CELLS)
        final = self._target()
        cells = final[:upto] + self.before[upto:]
        if upto < CELLS and cells[upto] != SYSTEM:
            cells[upto] = CONTIG      # the block being moved right now
        self.after_map.cells = cells
        self.after_map.update()
        name = random.choice(FILES).replace("{user}", self.user)
        self.status.setText(f"(C:) Defragmenting...  {int(f * 100)}%   Relocating: {name}")
        if f >= 1.0:
            self._finished()

    def _finished(self):
        self.timer.stop()
        self.clock = None
        self.before = self._target()
        self.after_map.cells = list(self.before)
        self.after_map.update()
        self.vol_item.setText(1, "Defragmented")
        self.status.setText("Defragmentation is complete for: (C:)")
        self.analyze_btn.setEnabled(True)
        self.defrag_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        sound.play("info")

    def stop(self):
        if self.clock is not None:
            self.timer.stop()
            self.clock = None
            self.vol_item.setText(1, "Stopped")
            self.status.setText("Defragmentation was stopped.")
            self.analyze_btn.setEnabled(True)
            self.defrag_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def closeEvent(self, event):
        self.timer.stop()
        self.clock = None
        event.accept()


def launch(desktop, automatic=False):
    global _window
    if _window is None or not isValid(_window):
        content = Defrag(desktop)
        _window = XPWindow(desktop, "Disk Defragmenter", content, QIcon(icon_pixmap(16)), size=(600, 330))
        _window.destroyed.connect(_forget)
        desktop.open_window(_window)
    else:
        desktop.open_window(_window)
    if automatic:
        _window.content.defragment(automatic=True)
        if desktop.active is not None and desktop.active is not _window:
            desktop.minimize(_window)   # scheduled runs start quietly in the background


def _forget(*_):
    global _window
    _window = None
