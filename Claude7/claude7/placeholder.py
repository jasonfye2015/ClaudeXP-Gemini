"""A plain window for features that aren't built yet (Windows 7 style)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from . import sound
from .wm import AeroWindow


def open_placeholder(desktop, title, icon, message="This part of Claude7 hasn't been built yet.",
                     sound_event="navigate"):
    body = QWidget()
    body.setAutoFillBackground(True)
    body.setStyleSheet("background: white; color: #1E1E1E; font-family: 'Segoe UI'; font-size: 12px;")
    layout = QHBoxLayout(body)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(16)
    pic = QLabel()
    pic.setPixmap(icon.pixmap(32, 32))
    pic.setAlignment(Qt.AlignTop)
    text = QLabel(message)
    text.setWordWrap(True)
    text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    layout.addWidget(pic)
    layout.addWidget(text, 1)
    win = AeroWindow(desktop, title, body, icon, (440, 260))
    desktop.open_window(win)
    if sound_event:
        sound.play(sound_event)
    return win
