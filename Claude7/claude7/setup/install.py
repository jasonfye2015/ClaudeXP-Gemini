"""Installing Windows 7 from the DVD: 'Press any key to boot from CD or DVD', 'Windows is loading files...', the
Install Windows wizard (language, Install now, the licence, Custom, where to install - with Claude7's choices of
what to keep), 'Installing Windows...' with its steps, and the restart."""
from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton,
                               QStackedWidget, QVBoxLayout, QWidget)

from . import ms
from ..paths import IMAGES

DIALOG_CSS = """
QFrame#dlg { background: white; border: 1px solid #5B7FA8; }
QLabel { font-family: 'Segoe UI'; font-size: 12px; color: #1E1E1E; background: transparent; }
QLabel#title { font-size: 20px; color: #003399; }
QLabel#head { font-size: 15px; color: #003399; }
QLabel#grey { color: #6D6D6D; }
QPushButton { font-family: 'Segoe UI'; font-size: 12px; padding: 4px 16px; min-width: 70px;
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F6F6F6, stop:1 #DDDDDD);
              border: 1px solid #707070; border-radius: 3px; }
QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #EAF6FD, stop:1 #BEE6FD);
                    border: 1px solid #3C7FB1; }
QPushButton:disabled { color: #9A9A9A; border: 1px solid #ADB2B5; background: #F4F4F4; }
QPushButton#big { font-size: 15px; padding: 10px 28px; }
QComboBox { font-family: 'Segoe UI'; font-size: 12px; padding: 2px 6px; min-width: 260px; }
QCheckBox { font-family: 'Segoe UI'; font-size: 12px; }
QProgressBar { border: 1px solid #BCBCBC; background: #E6E6E6; height: 14px; text-align: center; }
QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9BE39B, stop:1 #06B025); }
QFrame#row { border: 1px solid #C8D4E2; background: #F7FAFD; }
"""
STEPS = ["Copying Windows files", "Expanding Windows files", "Installing features", "Installing updates",
         "Completing installation"]


def _flag(p, x, y, size):
    from ..logon import LogonScreen
    LogonScreen._flag(p, x, y, size)


class _TextScreen(QWidget):
    """Black screen, white text, like the real thing before Windows is up."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lines = []
        self.bar = None                   # (fraction) for 'Windows is loading files...'
        self.setFocusPolicy(Qt.StrongFocus)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        f = QFont("Lucida Console")
        f.setPixelSize(max(12, self.height() // 36))
        p.setFont(f)
        p.setPen(QColor("#C0C0C0"))
        lh = QFontMetrics(f).lineSpacing()
        y = lh * 2
        for line in self.lines:
            p.drawText(lh, y, line)
            y += lh
        if self.bar is not None:
            w = self.width() - 2 * lh
            r = QRectF(lh, self.height() - 4 * lh, w, lh)
            p.setPen(QPen(QColor("#C0C0C0"), 1))
            p.drawRect(r)
            p.fillRect(QRectF(r.x() + 2, r.y() + 2, (r.width() - 4) * self.bar, r.height() - 4), QColor("#C0C0C0"))


class BootFromDvd(_TextScreen):
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
        self.lines = ["Press any key to boot from CD or DVD."]
        self.timer.start(ms(600))
        self.setFocus()
        self.update()

    def _tick(self):
        self.dots += 1
        self.lines = ["Press any key to boot from CD or DVD." + "." * self.dots]
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
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def start(self):
        self.lines = ["Windows is loading files..."]
        self.bar = 0.0
        self.timer.start(ms(60))

    def _tick(self):
        self.bar = min(1.0, self.bar + 0.02)
        self.update()
        if self.bar >= 1.0:
            self.timer.stop()
            QTimer.singleShot(ms(400), self.finished.emit)


class InstallWizard(QWidget):
    """The blue screen with the 'Install Windows' dialog in the middle."""
    reboot = Signal(bool, bool, bool)          # format_drive, program_history, memories
    quit_setup = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.background = QPixmap(str(IMAGES / "shutdown" / "shutdown-screen.jpg"))
        self.dlg = QFrame(self)
        self.dlg.setObjectName("dlg")
        self.dlg.setStyleSheet(DIALOG_CSS)
        self.dlg.setFixedSize(640, 470)
        v = QVBoxLayout(self.dlg)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        head = QWidget()
        head.setFixedHeight(34)
        head.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #E9EFF7);")
        hl = QHBoxLayout(head)
        hl.setContentsMargins(10, 0, 10, 0)
        self.head_label = QLabel("Install Windows")
        self.head_label.setStyleSheet("font-size: 13px; color: #1E1E1E;")
        hl.addWidget(self.head_label)
        v.addWidget(head)
        self.stack = QStackedWidget()
        v.addWidget(self.stack, 1)
        foot = QWidget()
        foot.setFixedHeight(48)
        foot.setStyleSheet("background: #F0F0F0; border-top: 1px solid #DFDFDF;")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(12, 8, 12, 8)
        self.foot_note = QLabel("")
        self.foot_note.setObjectName("grey")
        fl.addWidget(self.foot_note, 1)
        self.back = QPushButton("Back")
        self.next = QPushButton("Next")
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
        v.setContentsMargins(28, 22, 28, 16)
        v.setSpacing(10)
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
        for label, items in (("Language to install:", ["English (United States)"]),
                             ("Time and currency format:", ["English (United States)"]),
                             ("Keyboard or input method:", ["US"])):
            r = QHBoxLayout()
            lab = QLabel(label)
            lab.setFixedWidth(190)
            r.addWidget(lab)
            c = QComboBox()
            c.addItems(items)
            r.addWidget(c)
            r.addStretch()
            rows.addLayout(r)
        note = QLabel("Enter your language and other preferences and click \"Next\" to continue.")
        note.setObjectName("grey")
        self._page("Install Windows", self._logo_row(), rows, note)
        # 2. install now
        big = QPushButton("Install now →")
        big.setObjectName("big")
        big.clicked.connect(lambda: self._go(1))
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(big)
        row.addStretch()
        links = QLabel("<a href='#'>What to know before installing Windows</a><br><br>"
                       "<a href='#'>Repair your computer</a>")
        links.setTextInteractionFlags(Qt.TextBrowserInteraction)
        links.linkActivated.connect(lambda _l: None)
        self._page("Windows 7 Home Premium", self._logo_row(), QLabel(""), row, QLabel(""), links)
        # 3. licence
        terms = QLabel("<b>MICROSOFT SOFTWARE LICENSE TERMS</b><br>WINDOWS 7 HOME PREMIUM<br><br>These license terms "
                       "are an agreement between Microsoft Corporation (or based on where you live, one of its "
                       "affiliates) and you. Please read them. They apply to the software named above, which includes "
                       "the media on which you received it, if any. Printed-paper license terms, which may come with "
                       "the software, may replace or modify any on-screen license terms.<br><br>Nothing here is real: "
                       "this is Claude7, a Windows 7 computer from October 2011 in the Claude Timeline. Everything "
                       "Setup erases is kept in Claude7/Recovery Backups.")
        terms.setWordWrap(True)
        terms.setAlignment(Qt.AlignTop)
        terms.setStyleSheet("background: white; border: 1px solid #ABADB3; padding: 8px;")
        self.accept = QCheckBox("I accept the license terms")
        self.accept.toggled.connect(self._refresh)
        self._page("Please read the license terms", terms, self.accept)
        # 4. upgrade or custom
        up = QFrame()
        up.setObjectName("row")
        ul = QVBoxLayout(up)
        ul.addWidget(QLabel("<b>Upgrade</b><br>Upgrade to a newer version of Windows and keep your files, settings, "
                            "and programs. The option to upgrade is only available when an existing version of "
                            "Windows is running. We recommend backing up your files before you proceed."))
        up.setEnabled(False)
        cu = QFrame()
        cu.setObjectName("row")
        cl = QVBoxLayout(cu)
        cl.addWidget(QLabel("<b>Custom (advanced)</b><br>Install a clean copy of Windows. This option does not keep "
                            "your files, settings, and programs. The option to use this is only available when "
                            "you start your computer using the installation disc."))
        self.custom = QPushButton("Custom (advanced)")
        self.custom.clicked.connect(lambda: self._go(1))
        cl.addWidget(self.custom, 0, Qt.AlignRight)
        self._page("Which type of installation do you want?", up, cu)
        # 5. where
        disk = QFrame()
        disk.setObjectName("row")
        dl = QVBoxLayout(disk)
        dl.addWidget(QLabel("<b>Disk 0 Partition 1</b> &nbsp;&nbsp; Total size: 931.5 GB &nbsp;&nbsp; "
                            "Free space: 812.3 GB &nbsp;&nbsp; Type: System"))
        self.fmt = QCheckBox("Format drive C: (erase everything on it; the current data is kept in Recovery Backups)")
        self.fmt.setChecked(True)
        self.keep_history = QCheckBox("Keep the programs' history (ClaudeAI's chats, the messengers' logs, bookmarks)")
        self.keep_memories = QCheckBox("Keep the residents' memories (their journals and your mail with them)")
        self.fmt.toggled.connect(self._refresh)
        self._page("Where do you want to install Windows?", disk, self.fmt, self.keep_history, self.keep_memories)
        # 6. installing
        self.step_labels = []
        box = QVBoxLayout()
        for name in STEPS:
            lab = QLabel(name)
            box.addWidget(lab)
            self.step_labels.append(lab)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.restart_note = QLabel("")
        self.restart_note.setObjectName("grey")
        self._page("Installing Windows...", QLabel("That's all the information we need right now. Your computer "
                                                   "may restart several times during installation."), box,
                   self.progress, self.restart_note)

    def _logo_row(self):
        w = QWidget()
        w.setFixedHeight(70)
        w.paintEvent = lambda e, w=w: self._paint_logo(w)
        return w

    def _paint_logo(self, w):
        p = QPainter(w)
        p.setRenderHint(QPainter.Antialiasing)
        _flag(p, 10, 14, 40)
        f = QFont("Segoe UI")
        f.setPixelSize(30)
        f.setWeight(QFont.Light)
        p.setFont(f)
        p.setPen(QColor("#1E1E1E"))
        p.drawText(66, 48, "Windows 7")
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
            lab.setText(lab.text().split(" (")[0].replace("✓ ", ""))
        self._refresh()
        self._place()

    def _refresh(self):
        i = self.stack.currentIndex()
        self.back.setVisible(0 < i < 5)
        self.next.setVisible(i in (0, 2, 4))
        if i == 2:
            self.next.setEnabled(self.accept.isChecked())
        elif i == 4:
            self.next.setEnabled(True)
        else:
            self.next.setEnabled(True)
        self.keep_history.setEnabled(self.fmt.isChecked())
        self.keep_memories.setEnabled(self.fmt.isChecked())
        self.foot_note.setText({0: "Collecting information", 1: "", 2: "Collecting information",
                                3: "Collecting information", 4: "Collecting information",
                                5: "Installing Windows"}.get(i, ""))
        self.head_label.setText("Install Windows")

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
            self.step_labels[self.step].setText("✓ " + STEPS[self.step])
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
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        if self.background.isNull():
            g = QLinearGradient(0, 0, 0, self.height())
            g.setColorAt(0, QColor("#1F5FA8"))
            g.setColorAt(1, QColor("#0B2E5C"))
            p.fillRect(self.rect(), g)
        else:
            scale = max(self.width() / self.background.width(), self.height() / self.background.height())
            w, h = self.background.width() * scale, self.background.height() * scale
            p.drawPixmap(QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h), self.background,
                         QRectF(self.background.rect()))
        f = QFont("Segoe UI")
        f.setPixelSize(12)
        p.setFont(f)
        p.setPen(QColor(255, 255, 255, 200))
        p.drawText(QRectF(0, self.height() - 30, self.width(), 20), Qt.AlignCenter,
                   "© 2009 Microsoft Corporation. All rights reserved.")
