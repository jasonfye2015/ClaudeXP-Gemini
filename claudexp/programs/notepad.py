"""Notepad: open, edit and save text files (on C: or the external E: drive)."""
from pathlib import Path

from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMenuBar,
                               QPlainTextEdit, QPushButton, QStyle, QVBoxLayout, QWidget)

from .. import sound
from ..wm import XPWindow

MENU_STYLE = """
QMenuBar { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
QMenuBar::item { padding: 3px 7px; background: transparent; }
QMenuBar::item:selected { background: #316AC5; color: white; }
QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }
QMenu::item { padding: 4px 24px 4px 20px; }
QMenu::item:selected { background: #316AC5; color: white; }
"""


def _read(path):
    data = Path(path).read_bytes()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace")


class Notepad(QWidget):
    def __init__(self, desktop, path=None):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.path = Path(path) if path else None
        self.closing = False
        self.setStyleSheet(MENU_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        bar = QMenuBar()
        bar.triggered.connect(lambda _action: sound.play("menu"))
        self.edit = QPlainTextEdit()
        self.edit.setFont(QFont("Lucida Console", 10))
        self.edit.setStyleSheet("QPlainTextEdit { border: 1px solid #7F9DB9; background: white; color: black; }")
        layout.addWidget(bar)
        layout.addWidget(self.edit)

        file_menu = bar.addMenu("&File")
        file_menu.addAction("&New", self.new, QKeySequence("Ctrl+N"))
        file_menu.addAction("&Save", self.save, QKeySequence("Ctrl+S"))
        file_menu.addAction("Save &As...", self.save_as)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", lambda: self.frame.request_close() if self.frame else None)
        edit_menu = bar.addMenu("&Edit")
        edit_menu.addAction("&Undo", self.edit.undo)
        edit_menu.addSeparator()
        edit_menu.addAction("Cu&t", self.edit.cut)
        edit_menu.addAction("&Copy", self.edit.copy)
        edit_menu.addAction("&Paste", self.edit.paste)
        edit_menu.addSeparator()
        edit_menu.addAction("Select &All", self.edit.selectAll)
        format_menu = bar.addMenu("F&ormat")
        wrap = QAction("&Word Wrap", format_menu, checkable=True, checked=True)
        wrap.toggled.connect(lambda on: self.edit.setLineWrapMode(
            QPlainTextEdit.WidgetWidth if on else QPlainTextEdit.NoWrap))
        format_menu.addAction(wrap)
        bar.addMenu("&View")
        bar.addMenu("&Help")
        for key, slot in (("Ctrl+S", self.save), ("Ctrl+N", self.new)):
            act = QAction(self)
            act.setShortcut(QKeySequence(key))
            act.triggered.connect(slot)
            self.addAction(act)

        if self.path is not None:
            try:
                self.edit.setPlainText(_read(self.path))
            except OSError:
                self.path = None
        self.edit.document().setModified(False)
        self.edit.document().modificationChanged.connect(lambda _m: self._update_title())

    def name(self):
        return self.path.name if self.path else "Untitled"

    def _update_title(self):
        if self.frame is not None:
            self.frame.set_title(f"{self.name()} - Notepad")

    def new(self):
        self._maybe_save(lambda: (self.edit.clear(), setattr(self, "path", None),
                                  self.edit.document().setModified(False), self._update_title()))

    def save(self, then=None):
        if self.path is None:
            self.save_as(then)
            return
        try:
            self.path.write_text(self.edit.toPlainText().replace("\r\n", "\n"), encoding="utf-8", newline="\r\n")
        except OSError as e:
            from ..explorer.dialogs import msgbox
            msgbox(self.desktop, "Notepad", f"Cannot save {self.path.name}: {e.strerror}", "error")
            return
        self.edit.document().setModified(False)
        self._update_title()
        if then:
            then()

    def save_as(self, then=None):
        SaveAsDialog(self.desktop, self.name() if self.path else "Untitled.txt",
                     self.path.parent if self.path else None, lambda path: self._saved_as(path, then))

    def _saved_as(self, path, then):
        self.path = path
        self.save(then)

    def _maybe_save(self, proceed):
        """XP's 'Do you want to save the changes?' before throwing text away."""
        if not self.edit.document().isModified():
            proceed()
            return
        from ..explorer.dialogs import msgbox

        def answer(button):
            if button == "Yes":
                self.save(proceed)
            elif button == "No":
                proceed()

        msgbox(self.desktop, "Notepad", f"The text in the {self.name()} file has changed.\n\n"
                                        "Do you want to save the changes?", "warning", ("Yes", "No", "Cancel"), answer)

    def closeEvent(self, event):
        if self.closing or not self.edit.document().isModified():
            event.accept()
            return
        event.ignore()

        def really_close():
            self.closing = True
            if self.frame is not None:
                self.desktop.close_window(self.frame)

        self._maybe_save(really_close)


class SaveAsDialog:
    """A simple Save As: pick a folder (My Documents, the desktop folders, C:, E:) and a file name."""

    def __init__(self, desktop, name, folder, on_save):
        from ..explorer import vfs
        from ..explorer.dialogs import msgbox
        from ..network import DialogBody, _fixed_window
        self.desktop, self.on_save = desktop, on_save
        places = [("My Documents", vfs.my_documents()), ("My Pictures", vfs.my_pictures()),
                  ("Shared Documents", vfs.shared_documents()), ("Local Disk (C:)", vfs.DRIVE_C),
                  ("External Drive (E:)", vfs.local_storage())]
        if folder is not None and all(Path(folder).resolve() != p.resolve() for _n, p in places):
            places.insert(0, (vfs.to_virtual(folder) or Path(folder).name, Path(folder)))
        body = DialogBody()
        grid = QGridLayout(body)
        grid.setContentsMargins(14, 12, 14, 12)
        grid.addWidget(QLabel("Save &in:"), 0, 0)
        where = QComboBox()
        for label, path in places:
            where.addItem(QApplication.style().standardIcon(QStyle.SP_DirIcon), label, str(path))
        if folder is not None:
            where.setCurrentIndex(next((i for i, (_n, p) in enumerate(places)
                                        if p.resolve() == Path(folder).resolve()), 0))
        grid.addWidget(where, 0, 1)
        grid.addWidget(QLabel("File &name:"), 1, 0)
        name_edit = QLineEdit(name)
        grid.addWidget(name_edit, 1, 1)
        row = QHBoxLayout()
        row.addStretch()
        save_btn = QPushButton("&Save")
        cancel = QPushButton("Cancel")
        for b in (save_btn, cancel):
            b.setFixedSize(75, 23)
            row.addWidget(b)
        grid.addLayout(row, 2, 0, 1, 2)
        body.setFixedWidth(380)
        holder = {}

        def close():
            if holder.get("win") is not None:
                desktop.close_window(holder.pop("win"))

        def save():
            text = name_edit.text().strip()
            if not text or any(c in text for c in '\\/:*?"<>|'):
                msgbox(desktop, "Save As", "The file name is not valid.", "error")
                return
            if not Path(text).suffix:
                text += ".txt"
            path = Path(where.currentData()) / text

            def go(button="Yes"):
                if button == "Yes":
                    close()
                    on_save(path)

            if path.exists():
                msgbox(desktop, "Save As", f"{text} already exists.\nDo you want to replace it?", "warning",
                       ("Yes", "No"), go)
            else:
                go()

        save_btn.clicked.connect(save)
        name_edit.returnPressed.connect(save)
        cancel.clicked.connect(close)
        holder["win"] = _fixed_window(desktop, "Save As", body, close)
        desktop.open_window(holder["win"])
        name_edit.setFocus()
        name_edit.selectAll()


def open_notepad(desktop, path=None):
    body = Notepad(desktop, path)
    icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
    win = XPWindow(desktop, f"{body.name()} - Notepad", body, icon, (560, 400))
    body.frame = win
    desktop.open_window(win)
    body.edit.setFocus()
    return win
