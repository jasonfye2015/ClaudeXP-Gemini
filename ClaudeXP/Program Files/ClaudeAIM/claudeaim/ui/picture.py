"""A simple window for viewing a picture a buddy sent, full size."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .. import host

SCREEN_FRACTION = 0.9  # only shrink pictures that wouldn't fit on screen


class PictureViewer(host.HostedWindow, QWidget):
    def __init__(self, path, title, parent=None):
        super().__init__(parent, Qt.Dialog)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(title)
        screen = host.available_geometry(parent or self)
        max_w = int(screen.width() * SCREEN_FRACTION)
        max_h = int(screen.height() * SCREEN_FRACTION) - 40  # room for the title bar
        pix = QPixmap(path)
        if pix.width() > max_w or pix.height() > max_h:
            pix = pix.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label = QLabel()
        label.setPixmap(pix)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("background: white; border: 2px inset #808080;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(label)
        self.setFixedSize(self.sizeHint())
        self.move(screen.center() - self.rect().center())
