"""A tiny Notepad, mostly to exercise the window manager."""
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import QApplication, QMenuBar, QPlainTextEdit, QStyle, QVBoxLayout, QWidget

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


def open_notepad(desktop):
    body = QWidget()
    body.setStyleSheet(MENU_STYLE)
    layout = QVBoxLayout(body)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    bar = QMenuBar()
    bar.triggered.connect(lambda _action: sound.play("menu"))
    edit = QPlainTextEdit()
    edit.setFont(QFont("Lucida Console", 10))
    edit.setStyleSheet("QPlainTextEdit { border: 1px solid #7F9DB9; background: white; }")
    layout.addWidget(bar)
    layout.addWidget(edit)

    icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
    win = XPWindow(desktop, "Untitled - Notepad", body, icon, (520, 380))

    file_menu = bar.addMenu("File")
    file_menu.addAction("New", edit.clear)
    file_menu.addSeparator()
    file_menu.addAction("Exit", lambda: desktop.close_window(win))
    edit_menu = bar.addMenu("Edit")
    edit_menu.addAction("Undo", edit.undo)
    edit_menu.addSeparator()
    edit_menu.addAction("Cut", edit.cut)
    edit_menu.addAction("Copy", edit.copy)
    edit_menu.addAction("Paste", edit.paste)
    edit_menu.addSeparator()
    edit_menu.addAction("Select All", edit.selectAll)
    format_menu = bar.addMenu("Format")
    wrap = QAction("Word Wrap", format_menu, checkable=True, checked=True)
    wrap.toggled.connect(lambda on: edit.setLineWrapMode(
        QPlainTextEdit.WidgetWidth if on else QPlainTextEdit.NoWrap))
    format_menu.addAction(wrap)
    bar.addMenu("View")
    bar.addMenu("Help")

    desktop.open_window(win)
    edit.setFocus()
    return win
