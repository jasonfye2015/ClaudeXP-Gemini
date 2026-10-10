"""Copilot Python Studio: write, check and run Python programs entirely offline, with its own Python runtime."""
import json
import re
import shutil
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QProcess, QProcessEnvironment, QSize, Qt, QTimer
from PySide6.QtGui import (QAction, QColor, QFont, QIcon, QKeySequence, QPainter, QPixmap, QTextCharFormat,
                           QTextCursor)
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem,
                               QMenuBar, QMessageBox, QPlainTextEdit, QPushButton, QSplitter, QTabWidget,
                               QToolButton, QVBoxLayout, QWidget)

from ...paths import DATA
from . import backups
from .assistant import AssistantPanel
from .debugger import DebugPanel, DebugSession
from .editor import CodeEditor, is_warning
from .ghost import GhostCompleter

SETTINGS_FILE = DATA / "pystudio.json"
STUDIO_DIR = "Python Studio"
TRACE = re.compile(r'File "([^"]+)", line (\d+)')
PLAIN = re.compile(r"^(.+?):(\d+)(?::\d+)?: ")

STYLE = """
QWidget#pystudio { background: #ECE9D8; }
QMenuBar { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
QMenuBar::item { padding: 3px 7px; background: transparent; }
QMenuBar::item:selected { background: #316AC5; color: white; }
QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }
QMenu::item { padding: 4px 24px 4px 20px; }
QMenu::item:selected { background: #316AC5; color: white; }
QMenu::item:disabled { color: #ACA899; }
QToolButton { font-family: Tahoma; font-size: 11px; padding: 3px 8px; border: 1px solid transparent; }
QToolButton:hover { border: 1px solid #316AC5; background: #E8EEF8; }
QToolButton:disabled { color: #ACA899; }
QLabel { font-family: Tahoma; font-size: 11px; color: black; }
QTabWidget::pane { border: 1px solid #919B9C; background: white; }
QTabBar::tab { font-family: Tahoma; font-size: 11px; padding: 3px 10px; background: #F4F3EE; border: 1px solid #919B9C;
               border-bottom: none; margin-right: 1px; }
QTabBar::tab:selected { background: white; }
QListWidget { font-family: Tahoma; font-size: 11px; background: white; color: black; border: 1px solid #7F9DB9; }
QListWidget::item:selected { background: #316AC5; color: white; }
QLineEdit { font-family: Tahoma; font-size: 11px; background: white; color: black; border: 1px solid #7F9DB9; padding: 1px 3px; }
QCheckBox { font-family: Tahoma; font-size: 11px; }
QPushButton { font-family: Tahoma; font-size: 11px; padding: 2px 8px; }
"""

SAMPLE = '''"""Welcome to Copilot Python Studio! Press F5 to run this program."""
import random

name = input("What is your name? ")
print(f"Hello, {name}!")

total = sum(random.randint(1, 6) for _ in range(2))
print("Your lucky dice roll is", total)
'''


def studio_root():
    from ...explorer import vfs
    return vfs.local_storage() / STUDIO_DIR


def python_exe():
    return studio_root() / "python312" / "python.exe"


def wheels_dir():
    return studio_root() / "wheels"


def projects_dir():
    from ...explorer import vfs
    folder = vfs.my_documents() / "Python Programs"
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "hello.py").write_text(SAMPLE, encoding="utf-8")
    return folder


def app_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#2D5E8E"))
    p.drawRoundedRect(int(2 * s), int(2 * s), int(17 * s), int(17 * s), 5 * s, 5 * s)
    p.setBrush(QColor("#F7C531"))
    p.drawRoundedRect(int(13 * s), int(13 * s), int(17 * s), int(17 * s), 5 * s, 5 * s)
    p.setBrush(QColor("white"))
    p.drawEllipse(int(6 * s), int(6 * s), max(2, int(3 * s)), max(2, int(3 * s)))
    p.drawEllipse(int(23 * s), int(23 * s), max(2, int(3 * s)), max(2, int(3 * s)))
    p.end()
    return QIcon(pm)


class _Reporter:
    def __init__(self):
        self.items = []

    def unexpectedError(self, filename, msg):
        self.items.append((1, str(msg)))

    def syntaxError(self, filename, msg, lineno, offset, text):
        self.items.append((lineno or 1, f"Syntax error: {msg}"))

    def flake(self, message):
        self.items.append((message.lineno, message.message % message.message_args))


def lint(code, name="<editor>"):
    from pyflakes import api
    reporter = _Reporter()
    api.check(code, name, reporter)
    return sorted(reporter.items)


class Console(QPlainTextEdit):
    """Program output. Ctrl-click or double-click a traceback line to jump to it."""

    def __init__(self, on_jump):
        super().__init__()
        self.on_jump = on_jump
        self.setProperty("nospell", True)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 10))
        self.setMaximumBlockCount(20000)
        self.setStyleSheet("QPlainTextEdit { background: white; color: black; border: none; }")
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)

    def write(self, text, color=None, bold=False):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color or "#000000"))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        scroll = self.verticalScrollBar()
        stick = scroll.value() >= scroll.maximum() - 4
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text, fmt)
        if stick:
            scroll.setValue(scroll.maximum())

    def mouseDoubleClickEvent(self, event):
        line = self.cursorForPosition(event.position().toPoint()).block().text()
        match = TRACE.search(line) or PLAIN.match(line)
        if match:
            self.on_jump(match.group(1), int(match.group(2)))
            return
        super().mouseDoubleClickEvent(event)


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
        row.addWidget(self.find, 2)
        row.addWidget(self.replace, 2)
        for text, slot in (("Next", lambda: self.step(True)), ("Previous", lambda: self.step(False)),
                           ("Replace", self.replace_one), ("Replace All", self.replace_all)):
            button = QPushButton(text)
            button.clicked.connect(slot)
            row.addWidget(button)
        row.addWidget(self.case)
        close = QToolButton()
        close.setText("x")
        close.clicked.connect(self.hide)
        row.addWidget(close)
        self.find.returnPressed.connect(lambda: self.step(True))
        self.hide()

    def flags(self, backward=False):
        from PySide6.QtGui import QTextDocument
        flags = QTextDocument.FindFlag(0)
        if self.case.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if backward:
            flags |= QTextDocument.FindBackward
        return flags

    def step(self, forward=True):
        editor = self.studio.editor()
        text = self.find.text()
        if editor is None or not text:
            return False
        if editor.find(text, self.flags(not forward)):
            return True
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.Start if forward else QTextCursor.End)
        editor.setTextCursor(cursor)
        return editor.find(text, self.flags(not forward))

    def replace_one(self):
        editor = self.studio.editor()
        if editor is None:
            return
        cursor = editor.textCursor()
        selected = cursor.selectedText()
        same = selected == self.find.text() if self.case.isChecked() else selected.lower() == self.find.text().lower()
        if cursor.hasSelection() and same:
            cursor.insertText(self.replace.text())
        self.step(True)

    def replace_all(self):
        editor = self.studio.editor()
        text = self.find.text()
        if editor is None or not text:
            return
        cursor = editor.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.Start)
        editor.setTextCursor(cursor)
        count = 0
        while editor.find(text, self.flags()):
            editor.textCursor().insertText(self.replace.text())
            count += 1
        cursor.endEditBlock()
        self.studio.status.setText(f"Replaced {count} occurrence(s).")

    def popup(self):
        self.show()
        editor = self.studio.editor()
        if editor is not None and editor.textCursor().hasSelection():
            self.find.setText(editor.textCursor().selectedText())
        self.find.setFocus()
        self.find.selectAll()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            editor = self.studio.editor()
            if editor is not None:
                editor.setFocus()
            return
        super().keyPressEvent(event)


class BuildDialog(QDialog):
    def __init__(self, parent, script):
        super().__init__(parent)
        self.setWindowTitle("Build Executable")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Turn {script.name} into a program that runs without Python installed.\n"
                                "Needs no network. The .exe goes in 'Built Programs' beside your scripts."))
        self.one_file = QCheckBox("Single file (slower to start, easier to share)")
        self.one_file.setChecked(True)
        self.windowed = QCheckBox("No console window (for programs with their own windows)")
        layout.addWidget(self.one_file)
        layout.addWidget(self.windowed)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Build")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def ask(parent, script):
        dialog = BuildDialog(parent, script)
        if dialog.exec() != QDialog.Accepted:
            return None
        return dialog.one_file.isChecked(), dialog.windowed.isChecked()


class PythonStudio(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.closing = False
        self.process = None
        self.on_run_end = None                 # called with (exit code, stopped, output) when a run ends
        self.started = 0.0
        self._work = None
        self._done = None
        self.untitled = 0
        self.settings = self._load_settings()
        self.setObjectName("pystudio")
        self.setStyleSheet(STYLE)
        self.folder = projects_dir()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.menubar = QMenuBar()
        root.addWidget(self.menubar)
        root.addWidget(self._toolbar())

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setDocumentMode(False)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._tab_changed)
        self.find_bar = FindBar(self)
        editor_box = QWidget()
        box = QVBoxLayout(editor_box)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)
        box.addWidget(self.tabs, 1)
        box.addWidget(self.find_bar)

        self.console = Console(self.jump)
        self.problems = QListWidget()
        self.problems.itemActivated.connect(self._problem_clicked)
        self.problems.itemClicked.connect(self._problem_clicked)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Type input for the running program and press Enter")
        self.input.returnPressed.connect(self.send_input)
        self.input.setEnabled(False)
        console_box = QWidget()
        cbox = QVBoxLayout(console_box)
        cbox.setContentsMargins(0, 0, 0, 0)
        cbox.setSpacing(0)
        cbox.addWidget(self.console, 1)
        cbox.addWidget(self.input)
        self.bottom = QTabWidget()
        self.bottom.addTab(console_box, "Console")
        self.bottom.addTab(self.problems, "Problems")
        self.debug_panel = DebugPanel(self.debug_eval, self.debug_show_frame)
        self.bottom.addTab(self.debug_panel, "Debug")
        self.session = None
        self.tools = {}
        self.ghost = GhostCompleter(busy=lambda: self.assistant.worker is not None)
        self.fix_bar = QWidget()
        fix_row = QHBoxLayout(self.fix_bar)
        fix_row.setContentsMargins(4, 2, 4, 2)
        fix_row.addWidget(QLabel("The program stopped with an error."))
        fix_button = QPushButton("\u2728 Ask AI Helper to fix this")
        fix_button.clicked.connect(self.fix_with_helper)
        fix_row.addWidget(fix_button)
        auto_button = QPushButton("\U0001F501 Auto-fix and re-run")
        auto_button.setToolTip("The AI Helper fixes it, you approve each change, and it runs again (up to 3 tries)")
        auto_button.clicked.connect(lambda: self.assistant.autofix(first_output=self._last_run_output()))
        fix_row.addWidget(auto_button)
        fix_row.addStretch()
        self.fix_bar.setStyleSheet("QWidget { background: #FFF4C8; }")
        self.fix_bar.hide()
        self.run_mark = 0
        cbox.insertWidget(0, self.fix_bar)

        self.files = QListWidget()
        self.files.itemActivated.connect(lambda item: self.open_path(Path(item.data(Qt.UserRole))))
        self.files.itemDoubleClicked.connect(lambda item: self.open_path(Path(item.data(Qt.UserRole))))
        side = QWidget()
        sbox = QVBoxLayout(side)
        sbox.setContentsMargins(0, 0, 0, 0)
        sbox.setSpacing(2)
        sbox.addWidget(QLabel(" My Python Programs"))
        sbox.addWidget(self.files, 1)

        right = QSplitter(Qt.Vertical)
        right.addWidget(editor_box)
        right.addWidget(self.bottom)
        right.setStretchFactor(0, 3)
        right.setStretchFactor(1, 1)
        right.setSizes([380, 200])
        main = QSplitter(Qt.Horizontal)
        main.addWidget(side)
        main.addWidget(right)
        self.assistant = AssistantPanel(self)
        self.assistant.setVisible(self.settings.get("helper", True))
        main.addWidget(self.assistant)
        main.setStretchFactor(1, 1)
        main.setSizes([170, 640, 360])
        root.addWidget(main, 1)

        bar = QWidget()
        brow = QHBoxLayout(bar)
        brow.setContentsMargins(6, 2, 6, 2)
        self.status = QLabel("Ready")
        self.signature = QLabel("")
        self.signature.setStyleSheet("QLabel { color: #1A4F9C; font-family: Consolas; }")
        self.position = QLabel("Ln 1, Col 1")
        self.runtime_label = QLabel()
        brow.addWidget(self.status, 2)
        brow.addWidget(self.signature, 4)
        brow.addWidget(self.position)
        brow.addWidget(self.runtime_label)
        root.addWidget(bar)

        self._build_menus()
        self.lint_timer = QTimer(self, singleShot=True, interval=700)
        self.lint_timer.timeout.connect(self._run_lint)
        self._refresh_runtime_label()
        self.refresh_files()
        self._restore()
        if self.tabs.count() == 0:
            self.new_file()
        if not python_exe().exists():
            self.console.write("The Python runtime was not found.\n"
                               f"Expected: {python_exe()}\n"
                               "Copy the 'Python Studio' folder into Local Storage to run programs.\n\n", "#B00000")
        else:
            self.console.write(f"Copilot Python Studio - {self._runtime_version()}. Press F5 to run.\n", "#606060")
        QTimer.singleShot(800, self._background_setup)

    def _background_setup(self):
        """First start: unpack the game assets, and build the signature cache the AI Helper looks things up in."""
        if self.closing:
            return
        try:
            from . import assets
            if assets.install():
                self.refresh_files()
                self.status.setText("Game assets installed in Python Programs\\Assets")
        except Exception:
            pass
        if python_exe().exists():
            import threading
            from . import apiref
            if not apiref.cache_file().exists():
                threading.Thread(target=lambda: apiref.build(python_exe()), daemon=True).start()

    # ---- settings -------------------------------------------------------------------------------
    @staticmethod
    def _load_settings():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save_settings(self):
        paths = [str(self.tabs.widget(i).path) for i in range(self.tabs.count()) if self.tabs.widget(i).path]
        self.settings.update(open=paths, font=self.font_points(), wrap=self.wrap_action.isChecked(),
                             helper=not self.assistant.isHidden(), ghost=self.ghost_action.isChecked())
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _restore(self):
        for name in self.settings.get("open", []):
            path = Path(name)
            if path.is_file():
                self.open_path(path)

    def font_points(self):
        return self.settings.get("font", 10)

    # ---- UI pieces --------------------------------------------------------------------------------
    def _toolbar(self):
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(4, 2, 4, 2)
        row.setSpacing(2)
        self.run_button = QToolButton()
        self.run_button.setText("\u25B6 Run  (F5)")
        self.run_button.clicked.connect(self.run_current)
        self.stop_button = QToolButton()
        self.stop_button.setText("\u25A0 Stop")
        self.stop_button.clicked.connect(self.stop)
        self.stop_button.setEnabled(False)
        check = QToolButton()
        check.setText("\u2713 Check  (F7)")
        check.clicked.connect(self.check_syntax)
        build = QToolButton()
        build.setText("\u2699 Build .exe  (F9)")
        build.clicked.connect(self.build_exe)
        helper = QToolButton()
        helper.setText("\u2728 AI Helper  (F6)")
        helper.clicked.connect(self.toggle_helper)
        debug = QToolButton()
        debug.setText("\U0001F41E Debug  (F8)")
        debug.clicked.connect(self.debug_continue)
        for b in (self.run_button, self.stop_button, debug, check, build, helper):
            row.addWidget(b)
        row.addStretch()
        return bar

    def _action(self, menu, text, slot, shortcut=None):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
            action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        action.triggered.connect(lambda _c=False: slot())
        menu.addAction(action)
        self.addAction(action)
        return action

    def _build_menus(self):
        m = self.menubar.addMenu("&File")
        self._action(m, "&New", self.new_file, "Ctrl+N")
        self.template_menu = m.addMenu("New from &Template")
        from .templates import TEMPLATES
        for name, description, code in TEMPLATES:
            act = self.template_menu.addAction(name)
            act.setToolTip(description)
            act.setStatusTip(description)
            act.triggered.connect(lambda _c=False, n=name, c=code: self.new_from_template(n, c))
        self._action(m, "&Open...", self.open_dialog, "Ctrl+O")
        self._action(m, "&Save", self.save, "Ctrl+S")
        self._action(m, "Save &As...", self.save_as, "Ctrl+Shift+S")
        self._action(m, "Save A&ll", self.save_all)
        self._action(m, "&Restore Previous Version...", self.restore_version)
        m.addSeparator()
        self._action(m, "&Close Tab", lambda: self.close_tab(self.tabs.currentIndex()), "Ctrl+W")
        self._action(m, "E&xit", lambda: self.frame.request_close() if self.frame else None)
        m = self.menubar.addMenu("&Edit")
        self._action(m, "&Undo", lambda: self._ed("undo"), "Ctrl+Z")
        self._action(m, "&Redo", lambda: self._ed("redo"), "Ctrl+Y")
        m.addSeparator()
        self._action(m, "Cu&t", lambda: self._ed("cut"), "Ctrl+X")
        self._action(m, "&Copy", lambda: self._ed("copy"), "Ctrl+C")
        self._action(m, "&Paste", lambda: self._ed("paste"), "Ctrl+V")
        self._action(m, "Select &All", lambda: self._ed("selectAll"), "Ctrl+A")
        m.addSeparator()
        self._action(m, "&Find / Replace...", self.find_bar.popup, "Ctrl+F")
        self._action(m, "Find &Next", lambda: self.find_bar.step(True), "F3")
        self._action(m, "&Go to Line...", self.goto_line, "Ctrl+G")
        m.addSeparator()
        self._action(m, "Co&mment / Uncomment", lambda: self._ed("toggle_comment"), "Ctrl+/")
        self._action(m, "&Indent", lambda: self._ed("indent_selection", True))
        self._action(m, "&Dedent", lambda: self._ed("indent_selection", False))
        m = self.menubar.addMenu("&Run")
        self._action(m, "&Run Program", self.run_current, "F5")
        self._action(m, "Run and &Auto-Fix Errors", lambda: self.assistant.autofix(), "Ctrl+F5")
        self._action(m, "&Stop", self.stop, "Shift+F5")
        self._action(m, "&Check Syntax", self.check_syntax, "F7")
        self._action(m, "&Build Executable (.exe)...", self.build_exe, "F9")
        m.addSeparator()
        self._action(m, "Python &Prompt (interactive)", self.run_repl)
        self._action(m, "&Clear Console", self.console.clear)
        m = self.menubar.addMenu("&Debug")
        self._action(m, "Start / &Continue", self.debug_continue, "F8")
        self._action(m, "Step &Over", self.debug_step_over, "F10")
        self._action(m, "Step &Into", self.debug_step_into, "F11")
        self._action(m, "Step Ou&t", self.debug_step_out, "Shift+F11")
        self._action(m, "S&top Debugging", self.stop)
        m.addSeparator()
        self._action(m, "Toggle &Breakpoint", lambda: self._ed("toggle_breakpoint"), "Ctrl+B")
        self._action(m, "&Remove All Breakpoints", self.clear_breakpoints)
        m = self.menubar.addMenu("&Tools")
        self._action(m, "Game &Assets, Sprites and Sound Maker...", self.open_assets)
        self._action(m, "Sprite Sheets, &Tile Maps and Pixel Art...", self.open_gametools)
        self._action(m, "Python && pygame &Manuals...", self.open_docs, "F1")
        m.addSeparator()
        self._action(m, "&Installed Packages", self.list_packages)
        self._action(m, "Install Package from &Offline Wheels...", self.install_package)
        self._action(m, "Open Python Programs &Folder", self.show_folder)
        m = self.menubar.addMenu("&View")
        self.wrap_action = QAction("&Word Wrap", self, checkable=True, checked=self.settings.get("wrap", False))
        self.wrap_action.toggled.connect(self._apply_wrap)
        m.addAction(self.wrap_action)
        self._action(m, "&AI Helper", self.toggle_helper, "F6")
        self.ghost_action = QAction("AI Auto&complete (grey suggestions, Tab accepts)", self, checkable=True,
                                    checked=self.settings.get("ghost", True))
        self.ghost_action.toggled.connect(self._apply_ghost)
        m.addAction(self.ghost_action)
        self._action(m, "Zoom &In", lambda: self._zoom(1), "Ctrl+=")
        self._action(m, "Zoom &Out", lambda: self._zoom(-1), "Ctrl+-")
        m = self.menubar.addMenu("&Help")
        self._action(m, "&About Python Studio", self.about)

    def toggle_helper(self):
        show = not self.assistant.isVisible()
        self.assistant.setVisible(show)
        if show:
            self.assistant.refresh_models()
            self.assistant.input.setFocus()

    def show_helper(self):
        if not self.assistant.isVisible():
            self.toggle_helper()

    def open_editors(self):
        return [self.tabs.widget(i) for i in range(self.tabs.count())]

    def _apply_ghost(self, on):
        self.settings["ghost"] = on
        for ed in self.open_editors():
            ed.ghost_enabled = on
            ed.clear_ghost()

    # ---- templates, backups, manuals, assets ---------------------------------------------------------------
    def new_from_template(self, name, code):
        self.untitled += 1
        ed = self._new_editor(None, code)
        ed.title = f"Untitled{self.untitled}.py"
        self._add_tab(ed)
        self.status.setText(f"New program from the \"{name}\" template. Save it, then press F5.")

    def restore_version(self):
        ed = self.editor()
        if ed is None or not ed.path:
            QMessageBox.information(self, "Restore Previous Version", "Save the file first; versions are kept per file.")
            return
        found = backups.versions(ed.path)
        if not found:
            QMessageBox.information(self, "Restore Previous Version", "No earlier versions of this file yet.")
            return
        label, ok = QInputDialog.getItem(self, "Restore Previous Version", "Pick a version (newest first):",
                                         [lbl for _f, lbl in found], 0, False)
        if not ok:
            return
        file = next(f for f, lbl in found if lbl == label)
        from .diffview import DiffDialog
        old = ed.toPlainText()
        new = Path(file).read_text(encoding="utf-8")
        if DiffDialog.ask(self, "Restore Previous Version", old, new, lint(new), "Restore",
                          "The file will change like this (the current text is kept as a version too):"):
            backups.snapshot(ed.path, old, "restore")
            cur = QTextCursor(ed.document())
            cur.beginEditBlock()
            cur.select(QTextCursor.Document)
            cur.insertText(new)
            cur.endEditBlock()

    def _tool_window(self, key, title, factory, size):
        from shiboken6 import isValid
        from ...wm import XPWindow
        frame = self.tools.get(key)
        if frame is not None and isValid(frame):
            self.desktop.open_window(frame)
            return frame.content
        content = factory()
        frame = XPWindow(self.desktop, title, content, app_icon(16), size=size)
        self.tools[key] = frame
        self.desktop.open_window(frame)
        return content

    def open_docs(self):
        from . import docs
        if not docs.available():
            QMessageBox.information(self, "Manuals", "No manuals found in Local Storage\\Python Studio\\docs.")
            return
        viewer = self._tool_window("docs", "Python & pygame Manuals", docs.DocsViewer, (860, 600))
        ed = self.editor()
        word = ""
        if ed is not None:
            cur = ed.textCursor()
            word = cur.selectedText().strip()
            if not word:
                cur.select(QTextCursor.WordUnderCursor)
                word = cur.selectedText().strip()
        if word and re.fullmatch(r"[\w.]+", word):
            viewer.search_for(word)

    def open_assets(self):
        from . import assets
        assets.install()

        def insert(text):
            ed = self.editor()
            if ed is not None:
                ed.textCursor().insertText(text)
                ed.setFocus()
        self._tool_window("assets", "Game Assets", lambda: assets.AssetBrowser(python_exe(), insert, projects_dir),
                          (760, 560))

    def open_gametools(self):
        from . import assets, gametools
        assets.install()

        def insert(text):
            ed = self.editor()
            if ed is not None:
                ed.textCursor().insertText(text)
                ed.setFocus()
        return self._tool_window("gametools", "Sprite Sheets, Tile Maps and Pixel Art",
                                 lambda: gametools.GameTools(insert), (980, 640))

    # ---- fix-this-error --------------------------------------------------------------------------------------
    def _last_run_output(self):
        return self.console.toPlainText()[self.run_mark:]

    def fix_with_helper(self):
        self.fix_bar.hide()
        out = self._last_run_output()
        marker = out.rfind("Traceback (most recent call last)")
        self.assistant.fix_error(out[marker:] if marker >= 0 else out)

    # ---- debugging -------------------------------------------------------------------------------------------
    def _debugging(self):
        return self.session is not None and not self.session.finished

    def start_debug(self, stepping):
        ed = self.editor()
        if ed is None or self._busy() or not self._runtime_ok():
            return
        if not ed.path and not self.save_as(ed):
            return
        self.save_all()
        if any(p[1].startswith("Syntax error") for p in ed.problems):
            self.bottom.setCurrentIndex(1)
            self.status.setText("Fix the syntax error first.")
            return
        backups.snapshot(ed.path, ed.toPlainText(), "debug")
        breaks = {e.path: e.breakpoints() for e in self.open_editors() if e.path and e.breakpoints()}
        self.session = DebugSession()
        self.session.stopped.connect(self._debug_stopped)
        self.session.evaluated.connect(lambda _e, r: self.debug_panel.result.setText(r))
        self.session.raised.connect(lambda text: self.console.write(f"\n[debugger] stopped at an error: {text}\n", "#C00000"))
        self.session.ended.connect(self._debug_ended)
        path = Path(ed.path)
        self.console.write(f"\n>>> Debugging {path.name}\n", "#316AC5", bold=True)
        runner = str(Path(__file__).with_name("dbg_runner.py"))
        self._start(["-u", runner, str(self.session.port()), str(path), json.dumps(breaks),
                     "step" if stepping else "run"], path.parent)

    def _debug_stopped(self, info):
        ed = self.open_path(Path(info["file"]))
        self._show_debug_line(ed, info["line"])
        self.debug_panel.show_stop(info)
        self.bottom.setCurrentIndex(2)
        self.status.setText(f"Paused at line {info['line']} in {info['func']}")

    def _show_debug_line(self, ed, line):
        for other in self.open_editors():
            other.set_debug_line(None)
        if ed is not None:
            ed.set_debug_line(line)

    def _debug_ended(self):
        for ed in self.open_editors():
            ed.set_debug_line(None)
        self.debug_panel.clear()

    def debug_show_frame(self, file, line):
        ed = self.open_path(Path(file))
        if ed is not None:
            ed.goto_line(line)

    def debug_eval(self, expr):
        if self._debugging() and self.session.paused:
            self.session.command("eval", expr=expr)
        else:
            self.debug_panel.result.setText("(the program is not paused)")

    def _debug_move(self, cmd):
        if not self._debugging():
            self.start_debug(stepping=cmd != "continue")
            return
        if self.session.paused:
            self._debug_ended()
            self.session.command(cmd)
            self.status.setText("Running...")

    def debug_continue(self):
        self._debug_move("continue")

    def debug_step_over(self):
        self._debug_move("next")

    def debug_step_into(self):
        self._debug_move("step")

    def debug_step_out(self):
        self._debug_move("out")

    def clear_breakpoints(self):
        for ed in self.open_editors():
            for line in ed.breakpoints():
                ed.toggle_breakpoint(line)

    def _breakpoint_edited(self, ed, line, on):
        if self._debugging() and ed.path:
            self.session.command("break" if on else "clear", file=ed.path, line=line)

    def about(self):
        QMessageBox.information(self, "Copilot Python Studio",
                                "Copilot Python Studio\n\nEdit and run Python programs without a network.\n"
                                f"Runtime: {self._runtime_version()}\n"
                                "Ctrl+Space: completions   F5: run   F7: check\n"
                                "Double-click a traceback line in the console to jump to it.")

    # ---- runtime info -----------------------------------------------------------------------------------
    def _runtime_version(self):
        return "Python 3.12" if python_exe().exists() else "no Python runtime"

    def _refresh_runtime_label(self):
        self.runtime_label.setText("Python 3.12 (offline)" if python_exe().exists() else "No runtime")

    # ---- tabs and files ---------------------------------------------------------------------------------
    def editor(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, CodeEditor) else None

    def _ed(self, name, *args):
        ed = self.editor()
        if ed is not None:
            getattr(ed, name)(*args)

    def _new_editor(self, path, text):
        ed = CodeEditor(python_exe() if python_exe().exists() else None)
        ed.set_font_size(self.font_points())
        ed.setLineWrapMode(QPlainTextEdit.WidgetWidth if self.wrap_action.isChecked() else QPlainTextEdit.NoWrap)
        ed.path = str(path) if path else None
        ed.setPlainText(text)
        ed.document().setModified(False)
        ed.document().modificationChanged.connect(lambda _m, e=ed: self._retitle(e))
        ed.document().contentsChanged.connect(self.lint_timer.start)
        ed.signature_changed.connect(self.signature.setText)
        ed.cursor_info.connect(lambda ln, col: self.position.setText(f"Ln {ln}, Col {col}"))
        ed.ghost_enabled = self.settings.get("ghost", True)
        ed.ghost_wanted.connect(lambda e=ed: self.ghost.request(e))
        ed.breakpoints_changed.connect(lambda line, on, e=ed: self._breakpoint_edited(e, line, on))
        return ed

    def _tab_title(self, ed):
        name = Path(ed.path).name if ed.path else ed.title
        return name + ("*" if ed.document().isModified() else "")

    def _retitle(self, ed):
        i = self.tabs.indexOf(ed)
        if i >= 0:
            self.tabs.setTabText(i, self._tab_title(ed))
        self._update_frame_title()

    def _add_tab(self, ed):
        i = self.tabs.addTab(ed, self._tab_title(ed))
        self.tabs.setCurrentIndex(i)
        ed.setFocus()

    def new_file(self):
        self.untitled += 1
        ed = self._new_editor(None, "")
        ed.title = f"Untitled{self.untitled}.py"
        self._add_tab(ed)

    def open_dialog(self):
        from ..opendialog import open_dialog
        open_dialog(self.desktop, "Open Python Program", {".py", ".pyw", ".txt"}, self.open_path, app_icon(16),
                    start=self.folder)

    def open_path(self, path):
        path = Path(path)
        for i in range(self.tabs.count()):
            if self.tabs.widget(i).path and Path(self.tabs.widget(i).path) == path:
                self.tabs.setCurrentIndex(i)
                return self.tabs.widget(i)
        try:
            data = path.read_bytes()
        except OSError as e:
            QMessageBox.warning(self, "Open", f"Cannot open {path.name}: {e.strerror}")
            return None
        text = next((data.decode(enc) for enc in ("utf-8-sig", "cp1252") if _ok(data, enc)), data.decode("latin-1"))
        ed = self._new_editor(path, text.replace("\r\n", "\n"))
        ed.title = path.name
        self._add_tab(ed)
        return ed

    def refresh_files(self):
        self.files.clear()
        try:
            entries = sorted(self.folder.glob("*.py"), key=lambda p: p.name.lower())
        except OSError:
            entries = []
        for p in entries:
            item = QListWidgetItem(p.name)
            item.setData(Qt.UserRole, str(p))
            self.files.addItem(item)

    def save(self, ed=None):
        ed = ed or self.editor()
        if ed is None:
            return False
        if not ed.path:
            return self.save_as(ed)
        try:
            Path(ed.path).write_text(ed.toPlainText(), encoding="utf-8", newline="\n")
        except OSError as e:
            QMessageBox.warning(self, "Save", f"Cannot save {Path(ed.path).name}: {e.strerror}")
            return False
        backups.snapshot(ed.path, ed.toPlainText(), "save")
        ed.document().setModified(False)
        self.status.setText(f"Saved {Path(ed.path).name}")
        self.refresh_files()
        return True

    def save_as(self, ed=None):
        ed = ed if isinstance(ed, CodeEditor) else self.editor()
        if ed is None:
            return False
        suggestion = Path(ed.path).name if ed.path else ed.title
        name, ok = QInputDialog.getText(self, "Save As", f"File name (saved in {self.folder.name}):", text=suggestion)
        name = name.strip()
        if not ok or not name:
            return False
        if any(c in name for c in '\\/:*?"<>|'):
            QMessageBox.warning(self, "Save As", "The file name is not valid.")
            return False
        if not Path(name).suffix:
            name += ".py"
        target = self.folder / name
        if target.exists() and str(target) != ed.path:
            answer = QMessageBox.question(self, "Save As", f"{name} already exists.\nDo you want to replace it?")
            if answer != QMessageBox.Yes:
                return False
        ed.path = str(target)
        done = self.save(ed)
        self._retitle(ed)
        return done

    def save_all(self):
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            if ed.document().isModified():
                self.save(ed)

    def _ask_save(self, ed):
        """True when it is OK to throw the editor away."""
        if not ed.document().isModified():
            return True
        name = Path(ed.path).name if ed.path else ed.title
        answer = QMessageBox.question(self, "Copilot Python Studio",
                                      f"The file {name} has changed.\n\nDo you want to save the changes?",
                                      QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if answer == QMessageBox.Cancel:
            return False
        return self.save(ed) if answer == QMessageBox.Yes else True

    def close_tab(self, index):
        ed = self.tabs.widget(index)
        if ed is None or not self._ask_save(ed):
            return
        self.tabs.removeTab(index)
        ed.deleteLater()
        if self.tabs.count() == 0:
            self.new_file()

    def _tab_changed(self, _i):
        self._update_frame_title()
        self._run_lint()

    def _update_frame_title(self):
        ed = self.editor()
        if self.frame is not None and ed is not None:
            self.frame.set_title(f"{self._tab_title(ed)} - Copilot Python Studio")

    def _apply_wrap(self, on):
        for i in range(self.tabs.count()):
            self.tabs.widget(i).setLineWrapMode(QPlainTextEdit.WidgetWidth if on else QPlainTextEdit.NoWrap)

    def _zoom(self, step):
        self.settings["font"] = max(7, min(28, self.font_points() + step))
        for i in range(self.tabs.count()):
            self.tabs.widget(i).set_font_size(self.settings["font"])

    def goto_line(self):
        ed = self.editor()
        if ed is None:
            return
        number, ok = QInputDialog.getInt(self, "Go to Line", "Line number:", ed.textCursor().blockNumber() + 1,
                                         1, ed.blockCount())
        if ok:
            ed.goto_line(number)

    def show_folder(self):
        from ... import explorer
        explorer.launch(self.desktop, self.folder)

    # ---- lint ----------------------------------------------------------------------------------
    def _run_lint(self):
        ed = self.editor()
        if ed is None:
            return
        try:
            ed.set_problems(lint(ed.toPlainText(), ed.path or "<editor>"))
        except Exception:
            ed.set_problems([])
        self._fill_problems(ed)

    def _fill_problems(self, ed):
        self.problems.clear()
        for line, message in ed.problems:
            item = QListWidgetItem(f"Line {line}: {message}")
            item.setData(Qt.UserRole, line)
            self.problems.addItem(item)
        self.bottom.setTabText(1, f"Problems ({len(ed.problems)})" if ed.problems else "Problems")

    def _problem_clicked(self, item):
        ed = self.editor()
        if ed is not None:
            ed.goto_line(item.data(Qt.UserRole))

    def check_syntax(self):
        ed = self.editor()
        if ed is None:
            return
        self._run_lint()
        count = len(ed.problems)
        self.bottom.setCurrentIndex(1 if count else 0)
        self.status.setText("No problems found." if not count else f"{count} problem(s) found.")
        if not count:
            self.console.write("Check complete: no syntax errors or warnings.\n", "#006000")

    # ---- running --------------------------------------------------------------------------------------
    def _runtime_ok(self):
        if python_exe().exists():
            return True
        QMessageBox.warning(self, "Copilot Python Studio",
                            f"The Python runtime was not found.\n\nExpected:\n{python_exe()}")
        return False

    def _busy(self):
        if self.process is not None:
            self.status.setText("A program is already running. Stop it first.")
            return True
        return False

    def run_current(self):
        ed = self.editor()
        if ed is None or self._busy() or not self._runtime_ok():
            return
        if not ed.path and not self.save_as(ed):
            return
        self.save_all()
        if ed.document().isModified() or not Path(ed.path).exists():
            self.save(ed)
        problems = [p for p in ed.problems if p[1].startswith("Syntax error")]
        if problems:
            self.bottom.setCurrentIndex(1)
            self.status.setText("Fix the syntax error first.")
            return
        path = Path(ed.path)
        backups.snapshot(ed.path, ed.toPlainText(), "run")
        self.console.write(f"\n>>> Running {path.name}\n", "#316AC5", bold=True)
        self._start(["-u", str(path)], path.parent)

    def run_repl(self):
        if self._busy() or not self._runtime_ok():
            return
        self.console.write("\n>>> Python prompt (type exit() to leave)\n", "#316AC5", bold=True)
        self._start(["-u", "-i"], self.folder)

    def build_exe(self):
        ed = self.editor()
        if ed is None or self._busy() or not self._runtime_ok():
            return
        if not ed.path and not self.save_as(ed):
            return
        if ed.document().isModified() or not Path(ed.path).exists():
            self.save(ed)
        script = Path(ed.path)
        if any(not is_warning(m) for _l, m in lint(ed.toPlainText(), ed.path)):
            self.bottom.setCurrentIndex(1)
            self.status.setText("Fix the errors before building an .exe.")
            return
        options = BuildDialog.ask(self, script)
        if options is None:
            return
        one_file, windowed = options
        out = self.folder / "Built Programs"
        work = Path(tempfile.mkdtemp(prefix="pystudio-build-"))
        args = ["-m", "PyInstaller", "--noconfirm", "--clean", "--onefile" if one_file else "--onedir",
                "--windowed" if windowed else "--console", "--name", script.stem,
                "--distpath", str(out), "--workpath", str(work / "build"), "--specpath", str(work),
                str(script)]
        self.console.write(f"\n>>> Building {script.stem}.exe (this takes a minute or two)\n", "#316AC5", bold=True)
        target = out / f"{script.stem}.exe" if one_file else out / script.stem / f"{script.stem}.exe"

        def finished():
            size = target.stat().st_size / 2**20 if target.exists() else 0
            self.console.write(f"\nBuilt {target}  ({size:.1f} MB)\n", "#006000", bold=True)
            self.status.setText(f"Built {target.name}")
            self.refresh_files()

        self._start(args, script.parent, done=finished, err_color="#606060")
        self._work = work
        self.status.setText(f"Building {script.stem}.exe...")

    def list_packages(self):
        if self._busy() or not self._runtime_ok():
            return
        self.console.write("\n>>> Installed packages\n", "#316AC5", bold=True)
        self._start(["-m", "pip", "list", "--disable-pip-version-check"], self.folder)

    def install_package(self):
        if self._busy() or not self._runtime_ok():
            return
        wheels = wheels_dir()
        found = sorted({re.split(r"-\d", p.name)[0] for p in wheels.glob("*.whl")}) if wheels.is_dir() else []
        hint = ("Available offline: " + ", ".join(found)) if found else "No wheels found in the wheels folder."
        name, ok = QInputDialog.getText(self, "Install Package", f"Package name (installed without a network).\n{hint}")
        name = name.strip()
        if not ok or not name or not re.fullmatch(r"[A-Za-z0-9_.\-\[\]=<>,]+", name):
            return
        self.console.write(f"\n>>> Installing {name} from {wheels}\n", "#316AC5", bold=True)
        self._start(["-m", "pip", "install", "--no-index", "--find-links", str(wheels),
                     "--disable-pip-version-check", name], self.folder)

    def _start(self, args, cwd, done=None, err_color="#C00000"):
        proc = QProcess(self)
        self._done = done
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUNBUFFERED", "1")
        env.insert("PYTHONIOENCODING", "utf-8")
        env.insert("PYTHONUTF8", "1")
        env.insert("PIP_NO_INDEX", "1")
        for var in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
            env.remove(var)
        proc.setProcessEnvironment(env)
        proc.setWorkingDirectory(str(cwd))
        proc.readyReadStandardOutput.connect(lambda: self.console.write(
            bytes(proc.readAllStandardOutput()).decode("utf-8", "replace")))
        proc.readyReadStandardError.connect(lambda: self.console.write(
            bytes(proc.readAllStandardError()).decode("utf-8", "replace"), err_color))
        proc.finished.connect(lambda code, status, p=proc: self._finished(p, code, status))
        proc.errorOccurred.connect(lambda err, p=proc: self._error(p, err))
        self.process = proc
        self.fix_bar.hide()
        self.run_mark = len(self.console.toPlainText())
        self.started = time.monotonic()
        self.bottom.setCurrentIndex(0)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.input.setEnabled(True)
        self.status.setText("Running...")
        proc.start(str(python_exe()), args)

    def _error(self, proc, err):
        if proc is self.process and err == QProcess.FailedToStart:
            self.console.write("The program could not be started.\n", "#C00000")
            self._cleanup(proc)
            hook, self.on_run_end = self.on_run_end, None
            if hook is not None:
                hook(-1, True, "")

    def _finished(self, proc, code, status):
        if proc is not self.process:
            return
        elapsed = time.monotonic() - self.started
        stopped = status == QProcess.CrashExit
        self.console.write("\n" + (f"Stopped after {elapsed:.1f} s.\n" if stopped else
                                   f"Finished with exit code {code} in {elapsed:.1f} s.\n"),
                           "#808080" if code == 0 or stopped else "#C00000")
        done, self._done = self._done, None
        failed = code != 0 and not stopped and "Traceback (most recent call last)" in self._last_run_output()
        self._cleanup(proc)
        if failed and self.assistant.models.count():
            self.fix_bar.show()
        if code == 0 and not stopped and done is not None:
            done()
        hook, self.on_run_end = self.on_run_end, None
        if hook is not None:
            hook(code, stopped, self._last_run_output())

    def _cleanup(self, proc):
        self._done = None
        work, self._work = self._work, None
        if work is not None:
            shutil.rmtree(work, ignore_errors=True)
        self.process = None
        if self.session is not None:
            self.session.close()
            self._debug_ended()
            self.session = None
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.input.setEnabled(False)
        self.status.setText("Ready")
        proc.deleteLater()

    def stop(self):
        if self.process is not None:
            self.process.kill()

    def send_input(self):
        if self.process is None:
            return
        text = self.input.text()
        self.input.clear()
        self.console.write(text + "\n", "#316AC5")
        self.process.write((text + "\n").encode("utf-8"))

    def jump(self, name, line):
        path = Path(name)
        if not path.is_file():
            return
        ed = self.open_path(path)
        if ed is not None:
            ed.goto_line(line)

    # ---- closing --------------------------------------------------------------------------------------
    def shutdown(self):
        from shiboken6 import isValid
        self.assistant.shutdown()
        self.ghost.shutdown()
        for frame in list(self.tools.values()):
            if isValid(frame):
                self.desktop.close_window(frame)
        self.tools.clear()
        if self.process is not None:
            self.process.kill()
            self.process.waitForFinished(1000)
        self._save_settings()

    def closeEvent(self, event):
        if self.closing:
            self.shutdown()
            event.accept()
            return
        event.ignore()
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            if not self._ask_save(ed):
                return
            ed.document().setModified(False)
        self.closing = True
        if self.frame is not None:
            self.desktop.close_window(self.frame)


def _ok(data, enc):
    try:
        data.decode(enc)
        return True
    except UnicodeDecodeError:
        return False
