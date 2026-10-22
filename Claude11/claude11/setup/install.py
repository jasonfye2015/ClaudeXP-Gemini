"""Installing Windows 11 from the USB drive: 'Press any key to boot from USB', the Windows Setup window (language,
Install now, the licence, Custom, where to install - with Claude11's choices of what to keep), 'Installing Windows'
with its steps, and the restart."""
from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton,
                               QStackedWidget, QVBoxLayout, QWidget)

from . import ms

DIALOG_CSS = """
QFrame#dlg { background: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 8px; }
QLabel { font-family: 'Segoe UI Variable Text', 'Segoe UI'; font-size: 13px; color: #1A1A1A; background: transparent; }
QLabel#title { font-size: 26px; font-weight: 600; }
QLabel#head { font-size: 20px; font-weight: 600; }
QLabel#grey { color: #5C5C5C; }
QPushButton { font-family: 'Segoe UI Variable Text', 'Segoe UI'; font-size: 13px; padding: 7px 24px; min-width: 90px;
              background: #FBFBFB; border: 1px solid #D0D0D0; border-radius: 4px; }
QPushButton:hover { background: #F0F0F0; }
QPushButton:disabled { color: #9A9A9A; border: 1px solid #E5E5E5; background: #F5F5F5; }
QPushButton#big { font-size: 15px; padding: 12px 36px; background: #0067C0; color: white; border-color: #0067C0; }
QPushButton#big:hover { background: #1975C5; }
QComboBox { font-family: 'Segoe UI'; font-size: 13px; padding: 5px 10px; min-width: 280px; border: 1px solid #D0D0D0;
            border-radius: 4px; background: #FBFBFB; }
QCheckBox { font-family: 'Segoe UI'; font-size: 13px; spacing: 10px; }
QProgressBar { border: none; background: #E0E0E0; border-radius: 2px; height: 4px; text-align: center; }
QProgressBar::chunk { background: #0067C0; border-radius: 2px; }
QFrame#row { border: 1px solid #E0E0E0; background: #FBFBFB; border-radius: 6px; }
"""
STEPS = ["Copying Windows files", "Getting files ready for installation", "Installing features", "Installing updates",
         "Finishing up"]


def _flag(p, x, y, size):
    from ..bios import draw_logo
    draw_logo(p, x + size / 2, y + size / 2, size / 2, "#0078D4", glow=False)


class _TextScreen(QWidget):
    """Black screen, white text, like the real thing before Windows is up."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lines = []
        self.bar = None                   # (fraction) for the loading screen
        self.setFocusPolicy(Qt.StrongFocus)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        f = QFont("Consolas")
        f.setPixelSize(max(12, self.height() // 36))
        p.setFont(f)
        p.setPen(QColor("#C0C0C0"))
        lh = QFontMetrics(f).lineSpacing()
        y = lh * 2
        for line in self.lines:
            p.drawText(lh, y, line)
            y += lh
        if self.bar is not None:
            from ..boot import draw_spinner
            cx, cy = self.width() / 2, self.height() * 0.55
            draw_spinner(p, cx, cy, 22, self.bar % 1.0)


class BootFromDvd(_TextScreen):
    """'Press any key to boot from USB...' - the installation drive."""
    boot_dvd = Signal()
    timed_out = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dots = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self._done = False

    def start(self):
        self._done = False
        self.dots = 0
        self.lines = ["Press any key to boot from USB."]
        self.timer.start(ms(600))
        self.setFocus()
        self.update()

    def _tick(self):
        self.dots += 1
        self.lines = ["Press any key to boot from USB." + "." * self.dots]
        self.update()
        if self.dots >= 8:
            self.timer.stop()
            if not self._done:
                self._done = True
                self.timed_out.emit()

    def keyPressEvent(self, event):
        if not self._done:
            self._done = True
            self.timer.stop()
            self.boot_dvd.emit()

    mousePressEvent = keyPressEvent


class LoadingFiles(_TextScreen):
    """The Windows logo and the spinner while Setup loads."""
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def start(self):
        self.lines = []
        self.bar = 0.0
        self.timer.start(ms(33))

    def _tick(self):
        self.bar += 33 / 1800
        self.update()
        if self.bar >= 2.4:
            self.timer.stop()
            QTimer.singleShot(ms(300), self.finished.emit)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.bar is not None:
            p = QPainter(self)
            from ..bios import draw_logo
            draw_logo(p, self.width() / 2, self.height() * 0.4, min(self.width(), self.height()) * 0.08)


class InstallWizard(QWidget):
    """Windows Setup's white window on the light backdrop."""
    reboot = Signal(bool, bool, bool)          # format_drive, program_history, memories
    quit_setup = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dlg = QFrame(self)
        self.dlg.setObjectName("dlg")
        self.dlg.setStyleSheet(DIALOG_CSS)
        self.dlg.setFixedSize(760, 540)
        v = QVBoxLayout(self.dlg)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        head = QWidget()
        head.setFixedHeight(44)
        hl = QHBoxLayout(head)
        hl.setContentsMargins(24, 0, 24, 0)
        self.head_label = QLabel("Windows Setup")
        self.head_label.setStyleSheet("font-size: 13px; color: #5C5C5C;")
        hl.addWidget(self.head_label)
        v.addWidget(head)
        self.stack = QStackedWidget()
        v.addWidget(self.stack, 1)
        foot = QWidget()
        foot.setFixedHeight(64)
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(40, 12, 40, 16)
        self.foot_note = QLabel("")
        self.foot_note.setObjectName("grey")
        fl.addWidget(self.foot_note, 1)
        self.back = QPushButton("Back")
        self.next = QPushButton("Next")
        self.next.setStyleSheet("background: #0067C0; color: white; border-color: #0067C0;")
        self.back.clicked.connect(lambda: self._go(-1))
        self.next.clicked.connect(lambda: self._go(1))
        fl.addWidget(self.back)
        fl.addWidget(self.next)
        v.addWidget(foot)
        self.pages = []
        self._build_pages()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._install_tick)
        self.countdown = QTimer(self)
        self.countdown.timeout.connect(self._count_tick)

    # ---- pages ----
    def _page(self, title, *widgets, stretch=True):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(40, 16, 40, 8)
        v.setSpacing(12)
        t = QLabel(title)
        t.setObjectName("head")
        t.setWordWrap(True)
        v.addWidget(t)
        for x in widgets:
            if isinstance(x, QWidget):
                v.addWidget(x)
            else:
                v.addLayout(x)
        if stretch:
            v.addStretch()
        self.stack.addWidget(w)
        self.pages.append(w)
        return w

    def _build_pages(self):
        # 1. language
        rows = QVBoxLayout()
        for label, items in (("Language to install", ["English (United States)"]),
                             ("Time and currency format", ["English (United States)"]),
                             ("Keyboard or input method", ["US"])):
            r = QVBoxLayout()
            r.addWidget(QLabel(label))
            c = QComboBox()
            c.addItems(items)
            r.addWidget(c, 0, Qt.AlignLeft)
            rows.addLayout(r)
        self._page("Select language settings", self._logo_row(), rows)
        # 2. install now
        big = QPushButton("Install now")
        big.setObjectName("big")
        big.clicked.connect(lambda: self._go(1))
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(big)
        row.addStretch()
        links = QLabel("<a href='#' style='color:#0067C0'>Repair my PC</a>")
        links.setTextInteractionFlags(Qt.TextBrowserInteraction)
        links.linkActivated.connect(lambda _l: None)
        self._page("Windows 11 Home", self._logo_row(), QLabel(""), row, QLabel(""), links)
        # 3. licence
        terms = QLabel("<b>MICROSOFT SOFTWARE LICENSE TERMS</b><br>WINDOWS OPERATING SYSTEM<br><br>These license terms "
                       "are an agreement between you and Microsoft Corporation (or one of its affiliates). They apply "
                       "to the software named above and any Microsoft services or software updates (except to the "
                       "extent such services or updates are accompanied by new or additional terms).<br><br>Nothing "
                       "here is real: this is Claude11, a Windows 11 computer from October 2025 in the Claude Timeline. "
                       "Everything Setup erases is kept in Claude11/Recovery Backups.")
        terms.setWordWrap(True)
        terms.setAlignment(Qt.AlignTop)
        terms.setStyleSheet("background: #FBFBFB; border: 1px solid #E0E0E0; border-radius: 6px; padding: 12px;")
        self.accept = QCheckBox("I accept the Microsoft Software License Terms")
        self.accept.toggled.connect(self._refresh)
        self._page("Applicable notices and license terms", terms, self.accept)
        # 4. upgrade or custom
        up = QFrame()
        up.setObjectName("row")
        ul = QVBoxLayout(up)
        ul.addWidget(QLabel("<b>Upgrade: Install Windows and keep files, settings, and apps</b><br>Only available "
                            "when an existing version of Windows is running."))
        up.setEnabled(False)
        cu = QFrame()
        cu.setObjectName("row")
        cl = QVBoxLayout(cu)
        cl.addWidget(QLabel("<b>Custom: Install Windows only (advanced)</b><br>A clean copy of Windows. This option "
                            "does not keep your files, settings, and apps."))
        self.custom = QPushButton("Custom")
        self.custom.clicked.connect(lambda: self._go(1))
        cl.addWidget(self.custom, 0, Qt.AlignRight)
        self._page("Select setup option", up, cu)
        # 5. where
        disk = QFrame()
        disk.setObjectName("row")
        dl = QVBoxLayout(disk)
        dl.addWidget(QLabel("<b>Disk 0 Partition 3</b> &nbsp;&nbsp; Samsung SSD 990 PRO 2TB &nbsp;&nbsp; "
                            "Total size: 1862.7 GB &nbsp;&nbsp; Free space: 1518.2 GB &nbsp;&nbsp; Type: Primary"))
        self.fmt = QCheckBox("Format drive C: (erase everything on it; the current data is kept in Recovery Backups)")
        self.fmt.setChecked(True)
        self.keep_history = QCheckBox("Keep the programs' history (ClaudeAI's chats, the messengers' logs, favourites)")
        self.keep_memories = QCheckBox("Keep the residents' memories (their journals and your mail with them)")
        self.fmt.toggled.connect(self._refresh)
        self._page("Select location to install Windows 11", disk, self.fmt, self.keep_history, self.keep_memories)
        # 6. installing
        self.step_labels = []
        box = QVBoxLayout()
        for name in STEPS:
            lab = QLabel(name)
            lab.setObjectName("grey")
            box.addWidget(lab)
            self.step_labels.append(lab)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.restart_note = QLabel("")
        self.restart_note.setObjectName("grey")
        self._page("Installing Windows 11", QLabel("Your PC will restart several times. This might take a while."), box,
                   self.progress, self.restart_note)

    def _logo_row(self):
        w = QWidget()
        w.setFixedHeight(70)
        w.paintEvent = lambda e, w=w: self._paint_logo(w)
        return w

    def _paint_logo(self, w):
        p = QPainter(w)
        p.setRenderHint(QPainter.Antialiasing)
        _flag(p, 4, 16, 36)
        f = QFont("Segoe UI Variable Display", 24)
        f.setPixelSize(28)
        f.setWeight(QFont.DemiBold)
        p.setFont(f)
        p.setPen(QColor("#1A1A1A"))
        p.drawText(56, 44, "Windows 11")
        p.end()

    # ---- flow ----
    def start(self):
        self.stack.setCurrentIndex(0)
        self.accept.setChecked(False)
        self.fmt.setChecked(True)
        self.keep_history.setChecked(False)
        self.keep_memories.setChecked(False)
        self.progress.setValue(0)
        self.restart_note.setText("")
        for lab in self.step_labels:
            lab.setText(lab.text().split(" (")[0].replace("✔ ", ""))
        self._refresh()
        self._place()

    def _refresh(self):
        i = self.stack.currentIndex()
        self.back.setVisible(0 < i < 5)
        self.next.setVisible(i in (0, 2, 4))
        if i == 2:
            self.next.setEnabled(self.accept.isChecked())
        else:
            self.next.setEnabled(True)
        self.keep_history.setEnabled(self.fmt.isChecked())
        self.keep_memories.setEnabled(self.fmt.isChecked())
        self.foot_note.setText({5: "Installing Windows 11"}.get(i, ""))

    def _go(self, step):
        i = self.stack.currentIndex() + step
        if i < 0:
            self.quit_setup.emit()
            return
        if i >= len(self.pages):
            return
        self.stack.setCurrentIndex(i)
        self._refresh()
        if i == 5:
            self._begin_install()

    def _begin_install(self):
        self.step = 0
        self.progress.setValue(0)
        self.timer.start(ms(120))

    def _install_tick(self):
        v = self.progress.value() + 1
        if v > 100:
            self.step_labels[self.step].setText("✔ " + STEPS[self.step])
            self.step += 1
            if self.step >= len(STEPS):
                self.timer.stop()
                self.secs = 10
                self.restart_note.setText(f"Windows needs to restart to continue. Restarting in {self.secs} seconds...")
                self.countdown.start(ms(1000))
                return
            v = 0
            self.timer.setInterval(ms(120 if self.step != 1 else 60))
        self.progress.setValue(v)
        self.step_labels[self.step].setText(f"{STEPS[self.step]} ({v}%)")

    def _count_tick(self):
        self.secs -= 1
        if self.secs <= 0:
            self.countdown.stop()
            self._restart()
            return
        self.restart_note.setText(f"Windows needs to restart to continue. Restarting in {self.secs} seconds...")

    def _restart(self):
        fmt = self.fmt.isChecked()
        self.reboot.emit(fmt, not (fmt and self.keep_history.isChecked()), not (fmt and self.keep_memories.isChecked()))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.next.isVisible() and self.next.isEnabled():
            self._go(1)
        elif self.countdown.isActive():
            self.countdown.stop()
            self._restart()

    # ---- painting ----
    def resizeEvent(self, event):
        self._place()

    def _place(self):
        self.dlg.move((self.width() - self.dlg.width()) // 2, (self.height() - self.dlg.height()) // 2)

    def paintEvent(self, event):
        from .oobe import paint_oobe_background
        paint_oobe_background(self, QPainter(self))
