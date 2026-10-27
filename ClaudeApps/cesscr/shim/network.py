"""Stands in for ClaudeXP's dialog windows in the .scr: the games' Settings dialogs open as ordinary Windows dialogs."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget


class DialogBody(QWidget):
    def __init__(self):
        super().__init__()
        self.on_close = None


def _fixed_window(desktop, title, body, closer, icon=None):
    dlg = QDialog()
    dlg.setWindowTitle(title)
    dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
    lay = QVBoxLayout(dlg)
    lay.addWidget(body)
    body.on_close = closer
    dlg.setFixedSize(dlg.sizeHint())
    return dlg
