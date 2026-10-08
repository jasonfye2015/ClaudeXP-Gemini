"""A plain window for features that aren't built yet."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from .. import sound
from ..wm import XPWindow


def open_placeholder(desktop, title, icon, message="This part of ClaudeXP hasn't been built yet.",
                     sound_event="navigate"):
    body = QWidget()
    body.setAutoFillBackground(True)
    body.setStyleSheet("background: white; color: black; font-family: Tahoma; font-size: 11px;")
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
    win = XPWindow(desktop, title, body, icon, (420, 260))
    desktop.open_window(win)
    if sound_event:
        sound.play(sound_event)
    return win
