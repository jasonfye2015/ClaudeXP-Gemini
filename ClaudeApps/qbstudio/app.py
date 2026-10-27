"""Claude QBasic Studio: write, run and debug QBasic programs, with an AI that vibe-codes them.

The window: files and an outline on the left; the editor (tabs) in the middle with Problems, Debug, Output, Help and
Immediate below it; the program's screen and the Vibe Coder on the right. Programs live in Local Storage\\Projects\\
QBasic Projects, beside the other Projects, so every computer's studio shares them."""
import json
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import QObject, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QKeySequence, QPainter, QPixmap, QTextCursor
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMenuBar, QMessageBox, QPlainTextEdit, QPushButton, QSplitter, QTabWidget,
                               QTextBrowser, QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from claudecore import host

from . import examples, helpref, interp, screen
from .editor import THEMES, CodeEditor, format_source
from .screenview import ScreenView
from .vibe import VibePanel

TITLE = "Claude QBasic Studio"
FOLDER = "QBasic Projects"
SETTINGS = "qbstudio.json"
STYLE = """
QWidget#qbstudio { background: #ECE9D8; }
QMenuBar { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
QMenuBar::item { padding: 3px 7px; background: transparent; }
QMenuBar::item:selected { background: #316AC5; color: white; }
QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }
QMenu::item { padding: 4px 24px 4px 20px; }
QMenu::item:selected { background: #316AC5; color: white; }
QMenu::item:disabled { color: #ACA899; }
QToolButton { font-family: Tahoma; font-size: 11px; padding: 3px 7px; border: 1px solid transparent; }
QToolButton:hover { border: 1px solid #316AC5; background: #E8EEF8; }
QToolButton:disabled { color: #ACA899; }
QLabel, QCheckBox, QPushButton, QSpinBox, QComboBox { font-family: Tahoma; font-size: 11px; }
QTabWidget::pane { border: 1px solid #919B9C; background: white; }
QTabBar::tab { font-family: Tahoma; font-size: 11px; padding: 3px 10px; background: #F4F3EE; border: 1px solid #919B9C;
               border-bottom: none; margin-right: 1px; }
QTabBar::tab:selected { background: white; }
QListWidget, QTreeWidget { font-family: Tahoma; font-size: 11px; background: white; color: black;
                           border: 1px solid #7F9DB9; }
QListWidget::item:selected, QTreeWidget::item:selected { background: #316AC5; color: white; }
QLineEdit { font-family: Tahoma; font-size: 11px; background: white; color: black; border: 1px solid #7F9DB9;
            padding: 1px 3px; }
QTextBrowser { font-family: Tahoma; font-size: 11px; background: white; color: black; border: 1px solid #7F9DB9; }
QPushButton { background: #F4F3EE; color: black; border: 1px solid #7F9DB9; border-radius: 3px; padding: 3px 10px; }
QPushButton:hover { background: #E8EEF8; border-color: #316AC5; }
QPushButton:pressed { background: #D8E4F8; }
QPushButton:disabled { color: #ACA899; border-color: #C9C7BA; }
QComboBox { background: white; color: black; border: 1px solid #7F9DB9; padding: 1px 4px; }
QComboBox QAbstractItemView { background: white; color: black; selection-background-color: #316AC5;
                              selection-color: white; }
QSpinBox { background: white; color: black; border: 1px solid #7F9DB9; padding: 1px 2px; }
QCheckBox, QLabel { color: black; }
QPlainTextEdit { background: white; color: black; border: 1px solid #7F9DB9; }
QTreeWidget QHeaderView::section { background: #F4F3EE; color: black; border: 1px solid #C9C7BA; padding: 2px 4px;
                                   font-family: Tahoma; font-size: 11px; }
"""
NEW_PROGRAM = "' A new QBasic program. Press F5 to run it - or describe what you want in the Vibe Coder.\nCLS\n" \
              "PRINT \"Hello from QBasic!\"\n"
threading.stack_size(64 * 1024 * 1024)            # (deep recursion in a BASIC program needs a deep Python stack)
sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))


def app_icon(size=32):
    """A blue QBasic screen with QB on it and a little spark."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    p.setPen(QColor("#202020"))
    p.setBrush(QColor("#C0C0C0"))
    p.drawRoundedRect(int(1 * s), int(3 * s), int(28 * s), int(22 * s), 3 * s, 3 * s)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#0000AA"))
    p.drawRect(int(4 * s), int(6 * s), int(22 * s), int(16 * s))
    p.setBrush(QColor("#808080"))
    p.drawRect(int(11 * s), int(25 * s), int(8 * s), int(3 * s))
    f = QFont("Consolas")
    f.setBold(True)
    f.setPixelSize(max(6, int(11 * s)))
    p.setFont(f)
    p.setPen(QColor("#FFFF55"))
    p.drawText(QRect(int(4 * s), int(6 * s), int(22 * s), int(16 * s)), Qt.AlignCenter, "QB")
    p.setBrush(QColor("#D97757"))                  # Claude's spark
    p.setPen(Qt.NoPen)
    cx, cy, r = 26 * s, 6 * s, 5 * s
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QPolygonF
    pts = []
    import math
    for k in range(8):
        rr = r if k % 2 == 0 else r * 0.35
        a = k * math.pi / 4
        pts.append(QPointF(cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    p.drawPolygon(QPolygonF(pts))
    p.end()
    return QIcon(pm)


def projects_dir():
    folder = host.local_storage() / "Projects" / FOLDER
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return folder


class _Bridge(QObject):
    """The program's thread tells the studio things through these (they arrive on the GUI thread)."""
    paused = Signal(int, str)
    finished = Signal(object)


class FindBar(QWidget):
    def __init__(self, studio):
        super().__init__()
        self.studio = studio
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 3, 4, 3)
        self.find = QLineEdit()
        self.find.setPlaceholderText("Find")
        self.replace = QLineEdit()
        self.replace.setPlaceholderText("Replace with")
        self.case = QCheckBox("Match case")
        self.whole = QCheckBox("Whole word")
        row.addWidget(self.find, 2)
        row.addWidget(self.replace, 2)
        for text, slot in (("Next", lambda: self.step(True)), ("Previous", lambda: self.step(False)),
                           ("Replace", self.replace_one), ("Replace All", self.replace_all)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            row.addWidget(b)
        row.addWidget(self.case)
        row.addWidget(self.whole)
        close = QToolButton()
        close.setText("✕")
        close.clicked.connect(self.close_bar)
        row.addWidget(close)
        self.find.returnPressed.connect(lambda: self.step(True))
        self.hide()

    def flags(self, backward=False):
        from PySide6.QtGui import QTextDocument
        flags = QTextDocument.FindFlag(0)
        if self.case.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.whole.isChecked():
            flags |= QTextDocument.FindWholeWords
        if backward:
            flags |= QTextDocument.FindBackward
        return flags

    def step(self, forward=True):
        ed = self.studio.editor()
        text = self.find.text()
        if ed is None or not text:
            return False
        if ed.find(text, self.flags(not forward)):
            return True
        c = ed.textCursor()
        c.movePosition(QTextCursor.Start if forward else QTextCursor.End)
        ed.setTextCursor(c)
        found = ed.find(text, self.flags(not forward))
        if not found:
            self.studio.say(f"\"{text}\" wasn't found.")
        return found

    def replace_one(self):
        ed = self.studio.editor()
        if ed is None:
            return
        c = ed.textCursor()
        sel = c.selectedText()
        same = sel == self.find.text() if self.case.isChecked() else sel.lower() == self.find.text().lower()
        if c.hasSelection() and same:
            c.insertText(self.replace.text())
        self.step(True)

    def replace_all(self):
        ed = self.studio.editor()
        text = self.find.text()
        if ed is None or not text:
            return
        c = ed.textCursor()
        c.beginEditBlock()
        c.movePosition(QTextCursor.Start)
        ed.setTextCursor(c)
        n = 0
        while ed.find(text, self.flags()):
            ed.textCursor().insertText(self.replace.text())
            n += 1
        c.endEditBlock()
        self.studio.say(f"Replaced {n} time{'s' if n != 1 else ''}.")

    def popup(self, replace=False):
        self.show()
        ed = self.studio.editor()
        if ed is not None and ed.textCursor().hasSelection():
            self.find.setText(ed.textCursor().selectedText())
        (self.replace if replace and self.find.text() else self.find).setFocus()
        self.find.selectAll()

    def close_bar(self):
        self.hide()
        ed = self.studio.editor()
        if ed is not None:
            ed.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_bar()
            return
        super().keyPressEvent(event)


class QBasicStudio(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.setObjectName("qbstudio")
        self.setStyleSheet(STYLE)
        self.desktop = desktop
        self.frame = None
        self.closing = False
        self.folder = projects_dir()
        self.settings = self._load_settings()
        self.theme = self.settings.get("theme", "QBasic Blue")
        if self.theme not in THEMES:
            self.theme = "QBasic Blue"
        self.font_points = int(self.settings.get("font", 11))
        self.untitled = 0
        # the running program
        self.vm = None
        self.thread = None
        self.run_started = 0.0
        self.paused_line = None
        self.paused_editor = None
        self.run_editor = None
        self.on_settled = None
        self.settle_timer = QTimer(self, singleShot=True)
        self.settle_timer.timeout.connect(self._settle_now)
        self.bridge = _Bridge()
        self.bridge.paused.connect(self._paused)
        self.bridge.finished.connect(self._finished)
        self.popped = None
        screen.make_glyphs()
        self.scr = screen.Screen()
        self.sound = screen.Sound(host.muted)
        self._build()
        self._build_menus()
        self.check_timer = QTimer(self, singleShot=True, interval=600)
        self.check_timer.timeout.connect(self.check_now)
        self.autosave_timer = QTimer(self, interval=120000)
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start()
        self._restore()
        self._update_run_buttons()

    # ---- settings ----
    def _load_settings(self):
        try:
            return json.loads((host.data("qbstudio") / SETTINGS).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save_settings(self):
        self.settings.update({
            "theme": self.theme, "font": self.font_points,
            "open": [ed.path for ed in self.open_editors() if ed.path],
            "current": self.editor().path if self.editor() is not None else None,
            "split": [self.main_split.sizes(), self.center_split.sizes(), self.right_split.sizes()],
            "autorun": self.vibe.autorun.isChecked(), "tries": self.vibe.tries.value(),
        })
        try:
            (host.data("qbstudio") / SETTINGS).write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _restore(self):
        opened = 0
        for p in self.settings.get("open", []):
            if p and Path(p).exists() and self.open_path(p) is not None:
                opened += 1
        if not opened:
            self.new_file(NEW_PROGRAM)
        cur = self.settings.get("current")
        for i in range(self.tabs.count()):
            if self.tabs.widget(i).path == cur:
                self.tabs.setCurrentIndex(i)
        split = self.settings.get("split")
        if split and len(split) == 3:
            self.main_split.setSizes(split[0])
            self.center_split.setSizes(split[1])
            self.right_split.setSizes(split[2])
        self.vibe.autorun.setChecked(bool(self.settings.get("autorun", True)))
        self.vibe.tries.setValue(int(self.settings.get("tries", 4)))
        self.refresh_files()

    # ---- the window ----
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.menubar = QMenuBar()
        root.addWidget(self.menubar)
        root.addWidget(self._toolbar())
        self.main_split = QSplitter(Qt.Horizontal)
        root.addWidget(self.main_split, 1)
        # left: files and outline
        self.side = QTabWidget()
        self.files = QListWidget()
        self.files.itemActivated.connect(self._file_activated)
        self.files.itemDoubleClicked.connect(self._file_activated)
        self.outline = QListWidget()
        self.outline.itemActivated.connect(self._outline_activated)
        self.outline.itemClicked.connect(self._outline_activated)
        self.side.addTab(self.files, "Programs")
        self.side.addTab(self.outline, "Outline")
        self.main_split.addWidget(self.side)
        # middle: editors over the panels
        self.center_split = QSplitter(Qt.Vertical)
        mid = QWidget()
        mv = QVBoxLayout(mid)
        mv.setContentsMargins(0, 0, 0, 0)
        mv.setSpacing(0)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._tab_changed)
        mv.addWidget(self.tabs, 1)
        self.find_bar = FindBar(self)
        mv.addWidget(self.find_bar)
        self.center_split.addWidget(mid)
        self.bottom = QTabWidget()
        self.problems = QListWidget()
        self.problems.itemActivated.connect(self._problem_activated)
        self.problems.itemClicked.connect(self._problem_activated)
        self.bottom.addTab(self.problems, "Problems")
        dbg = QWidget()
        dl = QHBoxLayout(dbg)
        dl.setContentsMargins(0, 0, 0, 0)
        self.vars = QTreeWidget()
        self.vars.setHeaderLabels(["Variable", "Value"])
        self.vars.setColumnWidth(0, 160)
        self.stack = QListWidget()
        sp = QSplitter(Qt.Horizontal)
        sp.addWidget(self.vars)
        sp.addWidget(self.stack)
        sp.setSizes([400, 160])
        dl.addWidget(sp)
        self.bottom.addTab(dbg, "Debug")
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 9))
        self.bottom.addTab(self.output, "Output")
        self.help = QTextBrowser()
        self.help.setOpenLinks(False)
        self.help.anchorClicked.connect(lambda url: self.show_help(url.toString().split(":", 1)[-1]))
        self.help.setHtml(helpref.index_html())
        self.bottom.addTab(self.help, "Help")
        imm = QWidget()
        il = QVBoxLayout(imm)
        il.setContentsMargins(2, 2, 2, 2)
        self.imm_out = QPlainTextEdit()
        self.imm_out.setReadOnly(True)
        self.imm_out.setFont(QFont("Consolas", 9))
        self.imm_out.setPlainText("Type a statement and press Enter - it runs on the screen at once (PRINT 2 + 2, "
                                  "CIRCLE ...). While a program is paused, it can see the program's variables.")
        self.imm = QLineEdit()
        self.imm.setFont(QFont("Consolas", 10))
        self.imm.setPlaceholderText("Immediate: PRINT x")
        self.imm.returnPressed.connect(self.immediate)
        il.addWidget(self.imm_out, 1)
        il.addWidget(self.imm)
        self.bottom.addTab(imm, "Immediate")
        self.center_split.addWidget(self.bottom)
        self.center_split.setSizes([520, 170])
        self.main_split.addWidget(self.center_split)
        # right: the screen over the Vibe Coder
        self.right_split = QSplitter(Qt.Vertical)
        holder = QWidget()
        hv = QVBoxLayout(holder)
        hv.setContentsMargins(0, 0, 0, 0)
        hv.setSpacing(0)
        bar = QHBoxLayout()
        bar.setContentsMargins(4, 2, 4, 2)
        self.screen_label = QLabel("<b>Screen</b>")
        bar.addWidget(self.screen_label)
        bar.addStretch()
        pop = QToolButton()
        pop.setText("Pop out")
        pop.setToolTip("Show the screen in its own big window  (F4)")
        pop.clicked.connect(self.pop_out)
        shot = QToolButton()
        shot.setText("Save picture")
        shot.setToolTip("Save what's on the screen as a PNG picture in the programs folder")
        shot.clicked.connect(self.save_picture)
        bar.addWidget(pop)
        bar.addWidget(shot)
        hv.addLayout(bar)
        self.view = ScreenView(self.scr)
        self.view.stop_requested.connect(self.stop_program)
        hv.addWidget(self.view, 1)
        self.right_split.addWidget(holder)
        self.vibe = VibePanel(self)
        self.vibe.status.connect(self.say)
        self.right_split.addWidget(self.vibe)
        self.right_split.setSizes([330, 420])
        self.main_split.addWidget(self.right_split)
        self.main_split.setSizes([150, 640, 460])
        # the status bar
        sb = QHBoxLayout()
        sb.setContentsMargins(6, 2, 6, 2)
        self.status = QLabel("Ready")
        self.where = QLabel("")
        sb.addWidget(self.status, 1)
        sb.addWidget(self.where)
        status = QWidget()
        status.setLayout(sb)
        status.setStyleSheet("QWidget { background: #ECE9D8; border-top: 1px solid #ACA899; }")
        root.addWidget(status)

    def _toolbar(self):
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(2, 1, 2, 1)
        row.setSpacing(1)
        self.tool = {}
        for key, text, tip, slot in (
                ("new", "New", "New program  Ctrl+N", lambda: self.new_file()),
                ("open", "Open", "Open a program  Ctrl+O", self.open_dialog),
                ("save", "Save", "Save  Ctrl+S", lambda: self.save()),
                (None, None, None, None),
                ("run", "▶ Run", "Run the program  F5", self.run_or_continue),
                ("stop", "■ Stop", "Stop it  Shift+F5", self.stop_program),
                ("into", "Step", "Run one statement  F8", lambda: self.step("into")),
                ("over", "Step over", "Run one statement, a SUB call in one go  F10", lambda: self.step("over")),
                ("out", "Step out", "Run to the end of this SUB  Shift+F11", lambda: self.step("out")),
                ("bp", "Breakpoint", "Stop at this line when running  F9", self.toggle_breakpoint),
                (None, None, None, None),
                ("fmt", "Format", "Indent the blocks and capitalise the keywords  Shift+Alt+F", self.format_document),
                ("vibe", "✨ Vibe", "Show or hide the Vibe Coder", self.toggle_vibe)):
            if key is None:
                sep = QLabel("|")
                sep.setStyleSheet("QLabel { color: #ACA899; }")
                row.addWidget(sep)
                continue
            b = QToolButton()
            b.setText(text)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            row.addWidget(b)
            self.tool[key] = b
        row.addStretch()
        return bar

    def _action(self, menu, text, slot, shortcut=None, checkable=False, checked=False):
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
            a.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        if checkable:
            a.setCheckable(True)
            a.setChecked(checked)
        a.triggered.connect(lambda _c=False: slot())
        menu.addAction(a)
        self.addAction(a)
        return a

    def _build_menus(self):
        mb = self.menubar
        m = mb.addMenu("&File")
        self._action(m, "&New", lambda: self.new_file(), "Ctrl+N")
        self._action(m, "&Open...", self.open_dialog, "Ctrl+O")
        ex = m.addMenu("Open an &Example")
        for name, code in examples.EXAMPLES.items():
            a = QAction(name, self)
            a.triggered.connect(lambda _c=False, n=name, c=code: self.new_file(c, n.split(" (")[0].replace(" ", "")
                                                                                 .replace(",", "") + ".bas"))
            ex.addAction(a)
        self.recent_menu = m.addMenu("&Recent")
        self.recent_menu.aboutToShow.connect(self._fill_recent)
        m.addSeparator()
        self._action(m, "&Save", lambda: self.save(), "Ctrl+S")
        self._action(m, "Save &As...", lambda: self.save_as())
        self._action(m, "Save A&ll", self.save_all, "Ctrl+Shift+S")
        self._action(m, "&Close", lambda: self.close_tab(self.tabs.currentIndex()), "Ctrl+W")
        m.addSeparator()
        self._action(m, "Show the Programs &Folder", lambda: host.open_folder(self.desktop, self.folder))
        self._action(m, "Save the Screen as a &Picture", self.save_picture)
        m.addSeparator()
        self._action(m, "E&xit", lambda: self.frame.request_close() if self.frame else None)
        m = mb.addMenu("&Edit")
        self._action(m, "&Undo", lambda: self._ed("undo"), "Ctrl+Z")
        self._action(m, "&Redo", lambda: self._ed("redo"), "Ctrl+Y")
        m.addSeparator()
        self._action(m, "Cu&t", lambda: self._ed("cut"), "Ctrl+X")
        self._action(m, "&Copy", lambda: self._ed("copy"), "Ctrl+C")
        self._action(m, "&Paste", lambda: self._ed("paste"), "Ctrl+V")
        self._action(m, "Select &All", lambda: self._ed("selectAll"), "Ctrl+A")
        m.addSeparator()
        self._action(m, "&Find...", lambda: self.find_bar.popup(), "Ctrl+F")
        self._action(m, "Find &Next", lambda: self.find_bar.step(True), "F3")
        self._action(m, "R&eplace...", lambda: self.find_bar.popup(replace=True), "Ctrl+H")
        self._action(m, "&Go to Line...", self.goto_line, "Ctrl+G")
        m.addSeparator()
        self._action(m, "Toggle &Comment", lambda: self._ed("toggle_comment"), "Ctrl+/")
        self._action(m, "&Duplicate Line", lambda: self._ed("duplicate_line"), "Ctrl+D")
        self._action(m, "&Indent", lambda: self._ed("indent_selection", 1), "Ctrl+]")
        self._action(m, "&Outdent", lambda: self._ed("indent_selection", -1), "Ctrl+[")
        self._action(m, "F&ormat Document", self.format_document, "Shift+Alt+F")
        m = mb.addMenu("&View")
        tm = m.addMenu("&Theme")
        self.theme_actions = {}
        for name in THEMES:
            a = QAction(name, self)
            a.setCheckable(True)
            a.setChecked(name == self.theme)
            a.triggered.connect(lambda _c=False, n=name: self.set_theme(n))
            tm.addAction(a)
            self.theme_actions[name] = a
        self._action(m, "Zoom &In", lambda: self.zoom(1), "Ctrl+=")
        self._action(m, "Zoom &Out", lambda: self.zoom(-1), "Ctrl+-")
        m.addSeparator()
        self._action(m, "&Programs and Outline", lambda: self.side.setVisible(not self.side.isVisible()))
        self._action(m, "&Vibe Coder", self.toggle_vibe)
        self._action(m, "&Screen in its Own Window", self.pop_out, "F4")
        m = mb.addMenu("&Run")
        self._action(m, "&Start / Continue", self.run_or_continue, "F5")
        self._action(m, "Run &without Breakpoints", lambda: self.run_program(debug=False), "Ctrl+F5")
        self._action(m, "S&top", self.stop_program, "Shift+F5")
        self._action(m, "&Restart", self.restart, "Ctrl+Shift+F5")
        self._action(m, "&Pause", self.pause, "Ctrl+Pause")
        m.addSeparator()
        self._action(m, "Step &Into", lambda: self.step("into"), "F8")
        self._action(m, "Step &Over", lambda: self.step("over"), "F10")
        self._action(m, "Step O&ut", lambda: self.step("out"), "Shift+F11")
        m.addSeparator()
        self._action(m, "Toggle &Breakpoint", self.toggle_breakpoint, "F9")
        self._action(m, "&Clear All Breakpoints", self.clear_breakpoints)
        m.addSeparator()
        self._action(m, "&Check for Problems", self.check_now, "Ctrl+Shift+B")
        m = mb.addMenu("&AI")
        self._action(m, "✨ &Vibe Code...", self.focus_vibe, "Ctrl+I")
        for label, prompt in __import__("qbstudio.vibe", fromlist=["QUICK"]).QUICK:
            self._action(m, f"{label} the Program", lambda p=prompt, lab=label: self.vibe.quick(lab, p))
        m = mb.addMenu("&Help")
        self._action(m, "&QBasic Reference", lambda: self.show_help(""), None)
        self._action(m, "Help on the &Word Here", lambda: self.show_help(self.editor().word_under_cursor()
                                                                          if self.editor() else ""), "F1")
        self._action(m, "&About Claude QBasic Studio", self.about)

    # ---- editors ----
    def editor(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, CodeEditor) else None

    def open_editors(self):
        return [self.tabs.widget(i) for i in range(self.tabs.count())]

    def _ed(self, name, *args):
        ed = self.editor()
        if ed is not None:
            getattr(ed, name)(*args)

    def _new_editor(self, path, text, title=None):
        ed = CodeEditor(self.theme, self.font_points)
        ed.setPlainText(text)
        ed.document().setModified(False)
        ed.path = str(path) if path else None
        ed.title = title or (Path(path).name if path else "Untitled.bas")
        ed.textChanged.connect(lambda e=ed: self._edited(e))
        ed.document().modificationChanged.connect(lambda _m, e=ed: self._retitle(e))
        ed.cursor_info.connect(lambda r, c: self.where.setText(f"Ln {r}, Col {c}"))
        ed.breakpoints_changed.connect(self._breakpoints_changed)
        ed.help_wanted.connect(self.show_help)
        i = self.tabs.addTab(ed, ed.title)
        self.tabs.setCurrentIndex(i)
        self._retitle(ed)
        self.check_now()
        return ed

    def new_file(self, text=None, title=None):
        self.untitled += 1
        ed = self._new_editor(None, text if text is not None else NEW_PROGRAM,
                              title or f"Untitled{self.untitled}.bas")
        if text is not None:
            ed.document().setModified(True)
        ed.setFocus()
        return ed

    def open_dialog(self):
        host.open_dialog(self.desktop, "Open QBasic Program", {".bas", ".txt"}, self.open_path, app_icon(16),
                         start=self.folder)

    def open_path(self, path):
        path = Path(path)
        for ed in self.open_editors():
            if ed.path and Path(ed.path) == path:
                self.tabs.setCurrentWidget(ed)
                return ed
        try:
            data = path.read_bytes()
        except OSError as e:
            QMessageBox.warning(self, TITLE, f"Can't open {path.name}: {e.strerror}")
            return None
        for enc in ("utf-8-sig", "cp437"):
            try:
                text = data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        ed = self._new_editor(path, text.replace("\r\n", "\n").replace("\x1a", ""))
        self._remember(path)
        return ed

    def _remember(self, path):
        recent = [p for p in self.settings.get("recent", []) if p != str(path)]
        self.settings["recent"] = [str(path)] + recent[:9]

    def _fill_recent(self):
        self.recent_menu.clear()
        for p in self.settings.get("recent", []):
            a = QAction(Path(p).name, self)
            a.setToolTip(p)
            a.triggered.connect(lambda _c=False, q=p: self.open_path(q))
            self.recent_menu.addAction(a)
        if not self.recent_menu.actions():
            a = QAction("(none yet)", self)
            a.setEnabled(False)
            self.recent_menu.addAction(a)

    def put_code(self, code, new_tab=False, title=None):
        """The Vibe Coder's program into the editor: a new tab, or over the current program (one undo step)."""
        ed = self.editor()
        if new_tab or ed is None:
            ed = self.new_file(code, title)
            return ed
        c = ed.textCursor()
        c.beginEditBlock()
        c.select(QTextCursor.Document)
        c.insertText(code)
        c.endEditBlock()
        ed.moveCursor(QTextCursor.Start)
        return ed

    def _retitle(self, ed):
        i = self.tabs.indexOf(ed)
        if i >= 0:
            self.tabs.setTabText(i, ed.title + (" *" if ed.document().isModified() else ""))
            self.tabs.setTabToolTip(i, ed.path or "Not saved yet")
        self._update_frame_title()

    def _update_frame_title(self):
        ed = self.editor()
        if self.frame is not None and ed is not None:
            try:
                self.frame.set_title(f"{ed.title} - {TITLE}")
            except Exception:
                pass

    def _tab_changed(self, _i):
        self._update_frame_title()
        self.check_now()

    def _edited(self, ed):
        if ed is self.editor():
            self.check_timer.start()

    def save(self, ed=None):
        ed = ed if isinstance(ed, CodeEditor) else self.editor()
        if ed is None:
            return False
        if not ed.path:
            return self.save_as(ed)
        try:
            Path(ed.path).write_text(ed.toPlainText(), encoding="utf-8", newline="\r\n")
        except OSError as e:
            QMessageBox.warning(self, TITLE, f"Can't save {Path(ed.path).name}: {e.strerror}")
            return False
        ed.document().setModified(False)
        self.say(f"Saved {Path(ed.path).name}")
        self.refresh_files()
        return True

    def save_as(self, ed=None):
        ed = ed if isinstance(ed, CodeEditor) else self.editor()
        if ed is None:
            return False
        name, ok = QInputDialog.getText(self, "Save As", f"File name (saved in {self.folder.name}):",
                                        text=Path(ed.path).name if ed.path else ed.title)
        name = name.strip()
        if not ok or not name:
            return False
        if any(c in name for c in '\\/:*?"<>|'):
            QMessageBox.warning(self, "Save As", "That file name isn't allowed.")
            return False
        if not Path(name).suffix:
            name += ".bas"
        target = self.folder / name
        if target.exists() and str(target) != ed.path:
            if QMessageBox.question(self, "Save As", f"{name} already exists.\nReplace it?") != QMessageBox.Yes:
                return False
        ed.path = str(target)
        ed.title = target.name
        done = self.save(ed)
        self._remember(target)
        self._retitle(ed)
        return done

    def save_all(self):
        for ed in self.open_editors():
            if ed.document().isModified():
                self.save(ed)

    def autosave(self):
        for ed in self.open_editors():
            if ed.path and ed.document().isModified():
                try:
                    Path(ed.path).write_text(ed.toPlainText(), encoding="utf-8", newline="\r\n")
                    ed.document().setModified(False)
                except OSError:
                    pass

    def _ask_save(self, ed):
        if not ed.document().isModified():
            return True
        answer = QMessageBox.question(self, TITLE, f"{ed.title} has changed.\n\nSave the changes?",
                                      QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if answer == QMessageBox.Cancel:
            return False
        return self.save(ed) if answer == QMessageBox.Yes else True

    def close_tab(self, index):
        ed = self.tabs.widget(index)
        if ed is None or not self._ask_save(ed):
            return
        if ed is self.run_editor:
            self.stop_program()
        self.tabs.removeTab(index)
        ed.deleteLater()
        if self.tabs.count() == 0:
            self.new_file(NEW_PROGRAM)
            self.editor().document().setModified(False)

    def refresh_files(self):
        self.files.clear()
        try:
            names = sorted(self.folder.glob("*.bas"), key=lambda p: p.name.lower())
        except OSError:
            names = []
        for p in names:
            it = QListWidgetItem(p.name)
            it.setData(Qt.UserRole, str(p))
            self.files.addItem(it)
        head = QListWidgetItem("— Examples —")
        head.setFlags(Qt.NoItemFlags)
        self.files.addItem(head)
        for name in examples.EXAMPLES:
            it = QListWidgetItem("  " + name)
            it.setData(Qt.UserRole, "example:" + name)
            it.setForeground(QColor("#305080"))
            self.files.addItem(it)

    def _file_activated(self, item):
        ref = item.data(Qt.UserRole)
        if not ref:
            return
        if ref.startswith("example:"):
            name = ref[8:]
            self.new_file(examples.EXAMPLES[name], name.split(" (")[0].replace(" ", "").replace(",", "") + ".bas")
        else:
            self.open_path(ref)

    # ---- checking ----
    def compile_errors(self):
        ed = self.editor()
        if ed is None:
            return []
        return interp.compile_program(ed.toPlainText()).errors

    def source_line(self, n, running=False):
        """A line of the program in the editor (running: of the program that last ran)."""
        ed = (self.run_editor if running else None) or self.editor()
        if ed is None or not n:
            return ""
        block = ed.document().findBlockByNumber(n - 1)
        return block.text() if block.isValid() else ""

    def check_now(self):
        ed = self.editor()
        if ed is None:
            return
        prog = interp.compile_program(ed.toPlainText())
        ed.words = {v for v in prog.variables} | set(prog.subs) | set(prog.functions)
        problems = {}
        self.problems.clear()
        for e in prog.errors:
            problems.setdefault(e.line or 1, e.message)
            it = QListWidgetItem(f"Line {e.line}: {e.message}")
            it.setData(Qt.UserRole, e.line or 1)
            it.setForeground(QColor("#B00000"))
            self.problems.addItem(it)
        if not prog.errors:
            it = QListWidgetItem("No problems found.")
            it.setForeground(QColor("#2E7D32"))
            self.problems.addItem(it)
        self.bottom.setTabText(0, f"Problems ({len(prog.errors)})" if prog.errors else "Problems")
        ed.set_problems(problems)
        self.outline.clear()
        for kind, name, line in sorted(prog.outline, key=lambda o: o[2]):
            it = QListWidgetItem(f"{kind:<8} {name}" if kind != "label" else f"label    {name}:")
            it.setData(Qt.UserRole, line)
            it.setFont(QFont("Consolas", 9))
            self.outline.addItem(it)
        return prog

    def _problem_activated(self, item):
        line = item.data(Qt.UserRole)
        if line and self.editor() is not None:
            self.editor().go_to_line(line)

    def _outline_activated(self, item):
        line = item.data(Qt.UserRole)
        if line and self.editor() is not None:
            self.editor().go_to_line(line)

    # ---- running ----
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def run_or_continue(self):
        if self.vm is not None and self.vm.paused.is_set():
            self._resume(None)
            return
        if self.running():
            return
        self.run_program(debug=True)

    def run_program(self, debug=True, step=False, on_settled=None, settle_secs=None):
        """Compile the program in the editor and run it on its own thread. on_settled(outcome, error, screen text)
        is called once: when it ends, or settle_secs after it starts if it's still running (a game, or waiting for
        keys) - the Vibe Coder's way of knowing whether its program works."""
        ed = self.editor()
        if ed is None:
            return False
        if self.running():
            self.stop_program(wait=True)
        prog = self.check_now()
        if prog.errors:
            self.bottom.setCurrentIndex(0)
            e = prog.errors[0]
            ed.go_to_line(e.line or 1)
            self.say(f"Can't run it yet: line {e.line}: {e.message}")
            if on_settled is not None:
                on_settled("error", e, "")
            return False
        self.scr = screen.Screen()
        self.view.set_screen(self.scr)
        if self.popped is not None:
            self.popped_view.set_screen(self.scr)
        base = Path(ed.path).parent if ed.path else self.folder
        vm = interp.Machine(prog, self.scr, self.sound, base_dir=base,
                            on_pause=lambda line, unit: self.bridge.paused.emit(line, unit))
        if debug:
            vm.set_breakpoints(ed.breakpoints)
        if step:
            vm.cont("into")
            vm.resume_event.clear()
        self.vm = vm
        self.run_editor = ed
        self.on_settled = on_settled
        self.view.on_key = vm.keys.append
        self.view.message = ""
        if self.popped is not None:
            self.popped_view.on_key = vm.keys.append
        self.output.appendPlainText(f"▶ {ed.title} started at {time.strftime('%H:%M:%S')}")
        self.run_started = time.monotonic()
        self.thread = threading.Thread(target=self._worker, args=(vm,), daemon=True, name="qbasic")
        self.thread.start()
        if settle_secs:
            self.settle_timer.start(int(settle_secs * 1000))
        self.view.setFocus()
        self.screen_label.setText("<b>Screen</b> - running")
        self.say(f"Running {ed.title} - click the screen to type; Shift+F5 stops it.")
        self._update_run_buttons()
        return True

    def _worker(self, vm):
        result = vm.run()
        self.bridge.finished.emit((vm, result))

    def _finished(self, payload):
        vm, result = payload
        if vm is not self.vm:
            return
        took = time.monotonic() - self.run_started
        ed = self.run_editor
        self._clear_debug()
        self.view.on_key = None
        if self.popped is not None:
            self.popped_view.on_key = None
        if isinstance(result, interp.BasicError):
            self.output.appendPlainText(f"✖ {result.message} in line {result.line}")
            self.say(f"{result.message} in line {result.line}")
            self.view.message = f"{result.message} in line {result.line}"
            if ed is not None and self.tabs.indexOf(ed) >= 0:
                self.tabs.setCurrentWidget(ed)
                ed.go_to_line(result.line or 1)
                ed.set_problems({result.line or 1: result.message})
            self.problems.clear()
            it = QListWidgetItem(f"Line {result.line}: {result.message}  (while running)")
            it.setData(Qt.UserRole, result.line)
            it.setForeground(QColor("#B00000"))
            self.problems.addItem(it)
            self.bottom.setCurrentIndex(0)
            host.sound("error")
            outcome = "error"
        elif result == "stopped":
            self.output.appendPlainText(f"■ Stopped after {took:.1f} s")
            self.say("Stopped.")
            self.view.message = "Stopped"
            outcome = "stopped"
        else:
            self.output.appendPlainText(f"✔ Finished in {took:.1f} s")
            self.say("The program finished.")
            self.view.message = "Press F5 to run it again"
            outcome = "ended"
        self.screen_label.setText("<b>Screen</b>")
        self.view.update()
        self.thread = None
        self._update_run_buttons()
        self._settle(outcome, result if isinstance(result, interp.BasicError) else None)

    def _settle_now(self):
        if self.running():
            self._settle("running", None)

    def _settle(self, outcome, error):
        hook, self.on_settled = self.on_settled, None
        self.settle_timer.stop()
        if hook is not None and outcome != "stopped":
            text = "\n".join(self.scr.text_lines())
            hook(outcome, error, text)

    def stop_program(self, wait=False):
        vm = self.vm
        if vm is None or not self.running():
            return
        vm.stop()
        if wait and self.thread is not None:
            self.thread.join(1.5)

    def restart(self):
        self.stop_program(wait=True)
        QTimer.singleShot(50, lambda: self.run_program(debug=True))

    def pause(self):
        if self.running() and self.vm is not None:
            self.vm.request_pause()

    def step(self, how):
        if self.vm is not None and self.vm.paused.is_set():
            self._resume(how)
            return
        if not self.running():
            self.run_program(debug=True, step=True)

    def _resume(self, how):
        self._clear_debug()
        self.vm.cont(how)
        self.view.setFocus()
        self.screen_label.setText("<b>Screen</b> - running")
        self._update_run_buttons()

    def _paused(self, line, unit):
        ed = self.run_editor
        self.paused_line = line
        if ed is not None and self.tabs.indexOf(ed) >= 0:
            self.tabs.setCurrentWidget(ed)
            ed.set_debug_line(line)
        where = "" if unit == "(main)" else f" in {unit}"
        self.say(f"Paused at line {line}{where} - F5 carries on, F8 steps, F10 steps over.")
        self.screen_label.setText(f"<b>Screen</b> - paused at line {line}")
        self._fill_variables()
        self.bottom.setCurrentIndex(1)
        self._update_run_buttons()
        if self.frame is not None:
            host.in_front(self.desktop, self.frame)

    def _clear_debug(self):
        ed = self.run_editor
        if ed is not None and self.tabs.indexOf(ed) >= 0:
            ed.set_debug_line(None)
        self.paused_line = None

    def _fill_variables(self):
        vm = self.vm
        self.vars.clear()
        self.stack.clear()
        if vm is None:
            return
        for unit, _frame in reversed(vm.stack):
            self.stack.addItem(unit.name if unit.name != "(main)" else "main program")
        frames = [("Main program", vm.g)]
        if vm.frame is not vm.g:
            frames.insert(0, (f"In {vm.frame.unit.name}", vm.frame))
        for title, frame in frames:
            top = QTreeWidgetItem([title, ""])
            self.vars.addTopLevelItem(top)
            for key in sorted(frame.vars):
                if key.startswith("\x00"):
                    if key == "\x00result":
                        top.addChild(QTreeWidgetItem([f"{frame.unit.name} (its answer)", _show(frame.vars[key])]))
                    continue
                item = QTreeWidgetItem([key[:-1] if key.endswith("!") else key, _show(frame.vars[key])])
                _children(item, frame.vars[key])
                top.addChild(item)
            for key in sorted(frame.arrays):
                a = frame.arrays[key]
                dims = ", ".join(f"{lo} TO {hi}" for lo, hi in a.bounds)
                item = QTreeWidgetItem([key.replace("()", f"({dims})"), f"{len(a.data)} values"])
                for k, v in enumerate(a.data[:200]):
                    sub = QTreeWidgetItem([_index_label(a, k), _show(v)])
                    _children(sub, v)
                    item.addChild(sub)
                top.addChild(item)
            top.setExpanded(True)

    def _update_run_buttons(self):
        running = self.running()
        paused = self.vm is not None and self.vm.paused.is_set() and running
        self.tool["run"].setText("▶ Continue" if paused else "▶ Run")
        self.tool["run"].setEnabled(not running or paused)
        self.tool["stop"].setEnabled(running)
        for k in ("over", "out"):
            self.tool[k].setEnabled(paused)

    def toggle_breakpoint(self):
        ed = self.editor()
        if ed is not None:
            ed.toggle_breakpoint()

    def clear_breakpoints(self):
        for ed in self.open_editors():
            ed.breakpoints.clear()
            ed.gutter.update()
        self._breakpoints_changed()

    def _breakpoints_changed(self):
        if self.vm is not None and self.running() and self.run_editor is not None:
            self.vm.set_breakpoints(self.run_editor.breakpoints)

    # ---- the Immediate window ----
    def immediate(self):
        line = self.imm.text().strip()
        if not line:
            return
        self.imm.clear()
        self.imm_out.appendPlainText("> " + line)
        prog = interp.compile_program(line)
        if prog.errors:
            self.imm_out.appendPlainText(f"  {prog.errors[0].message}")
            return
        paused = self.vm is not None and self.vm.paused.is_set()
        if self.running() and not paused:
            self.imm_out.appendPlainText("  (the program is running - pause it first)")
            return
        m = interp.Machine(prog, self.scr, self.sound, base_dir=self.folder)
        if paused:
            m.g = self.vm.g
            m.frame = self.vm.g
            for k, v in self.vm.frame.vars.items():
                m.g.vars.setdefault(k, v)
        before = self.scr.text_lines()
        done = {}
        t = threading.Thread(target=lambda: done.setdefault("r", m.run()), daemon=True)
        m.keys = self.vm.keys if paused else m.keys
        t.start()
        t.join(2.0)
        if t.is_alive():
            m.stop()
            t.join(1.0)
            self.imm_out.appendPlainText("  (stopped after 2 seconds)")
        r = done.get("r")
        if isinstance(r, interp.BasicError):
            self.imm_out.appendPlainText(f"  {r.message}")
        after = self.scr.text_lines()
        new = [a for a, b in zip(after, before) if a != b]
        for ln in new[-5:]:
            if ln.strip():
                self.imm_out.appendPlainText("  " + ln.strip())
        if paused:
            self._fill_variables()

    # ---- view ----
    def set_theme(self, name):
        self.theme = name
        for n, a in self.theme_actions.items():
            a.setChecked(n == name)
        for ed in self.open_editors():
            ed.apply_theme(name)

    def zoom(self, step):
        self.font_points = max(7, min(28, self.font_points + step))
        for ed in self.open_editors():
            ed.set_font_size(self.font_points)

    def toggle_vibe(self):
        self.vibe.setVisible(not self.vibe.isVisible())

    def focus_vibe(self):
        self.vibe.show()
        self.vibe.input.setFocus()

    def pop_out(self):
        from shiboken6 import isValid
        if self.popped is not None and isValid(self.popped):
            self.desktop.open_window(self.popped)
            return
        self.popped_view = ScreenView(self.scr)
        self.popped_view.on_key = self.view.on_key
        self.popped_view.stop_requested.connect(self.stop_program)
        self.popped = host.window(self.desktop, "QBasic Screen", self.popped_view, app_icon(16), size=(800, 620))
        self.popped.destroyed.connect(self._unpop)
        self.desktop.open_window(self.popped)
        self.popped_view.setFocus()

    def _unpop(self, *_):
        self.popped = None

    def save_picture(self):
        if self.view.image is None:
            return
        name = time.strftime("Screen %Y-%m-%d %H%M%S.png")
        target = self.folder / name
        img = self.view.image.scaled(640, 480, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        if img.save(str(target)):
            self.say(f"Saved {name} in {self.folder.name}")

    def goto_line(self):
        ed = self.editor()
        if ed is None:
            return
        n, ok = QInputDialog.getInt(self, "Go to Line", f"Line (1 - {ed.blockCount()}):",
                                    ed.textCursor().blockNumber() + 1, 1, ed.blockCount())
        if ok:
            ed.go_to_line(n)

    def format_document(self):
        ed = self.editor()
        if ed is None:
            return
        text = ed.toPlainText()
        fixed = format_source(text)
        if fixed != text:
            line = ed.textCursor().blockNumber() + 1
            c = ed.textCursor()
            c.beginEditBlock()
            c.select(QTextCursor.Document)
            c.insertText(fixed)
            c.endEditBlock()
            ed.go_to_line(line)
            self.say("Formatted.")

    def show_help(self, word):
        page = helpref.html(word) if word else None
        self.help.setHtml(page or helpref.index_html())
        self.bottom.setCurrentWidget(self.help)

    def say(self, text):
        self.status.setText(text)

    def about(self):
        QMessageBox.about(self, TITLE, f"<b>{TITLE}</b><p>QBasic 1.1, the way it was - text and graphics screens, "
                          "sound, files, SUBs and FUNCTIONs, a debugger with breakpoints and stepping - and an AI that "
                          "writes programs for you and fixes them until they run.</p><p>Programs are kept in "
                          f"{self.folder}.</p>")

    # ---- closing ----
    def shutdown(self):
        self.stop_program(wait=True)
        if self.vibe.worker is not None:
            self.vibe.worker.stop()
        self._save_settings()

    def closeEvent(self, event):
        if self.closing:
            self.shutdown()
            event.accept()
            return
        event.ignore()
        for ed in self.open_editors():
            if not self._ask_save(ed):
                return
            ed.document().setModified(False)
        self.closing = True
        if self.frame is not None:
            self.desktop.close_window(self.frame)


def _show(v):
    if isinstance(v, str):
        return '"' + (v if len(v) < 200 else v[:200] + "...") + '"'
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k} = {_show(x)}" for k, x in list(v.items())[:6]) + "}"
    if isinstance(v, float):
        return interp.num_text(v)
    return str(v)


def _children(item, v):
    if isinstance(v, dict):
        for k, x in v.items():
            sub = QTreeWidgetItem([k, _show(x)])
            _children(sub, x)
            item.addChild(sub)


def _index_label(a, k):
    idx = []
    for (lo, _hi), stride in zip(a.bounds, a.strides):
        idx.append(str(lo + k // stride))
        k %= stride
    return "(" + ", ".join(idx) + ")"
