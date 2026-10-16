"""Shared look-and-feel: retro styling, image-backed windows, image buttons."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QPalette, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

from .. import host, paths

GREY = "#c0c0c0"


def apply_retro_style(app: QApplication):
    try:
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    except AttributeError:
        pass
    app.setStyle("Windows")
    pal = QPalette()
    for role, color in [
        (QPalette.Window, GREY), (QPalette.Button, GREY), (QPalette.Base, "#ffffff"),
        (QPalette.AlternateBase, "#ffffff"), (QPalette.WindowText, "#000000"),
        (QPalette.Text, "#000000"), (QPalette.ButtonText, "#000000"),
        (QPalette.Highlight, "#000080"), (QPalette.HighlightedText, "#ffffff"),
        (QPalette.ToolTipBase, "#ffffe1"), (QPalette.ToolTipText, "#000000"),
    ]:
        pal.setColor(role, QColor(color))
    app.setPalette(pal)
    app.setFont(QFont("Microsoft Sans Serif", 8))
    app.setWindowIcon(QIcon(paths.image("buddyicon.jpg")))


def tiled_background(widget: QWidget):
    """Fill a widget with the window_background.jpg texture (or plain grey)."""
    pal = widget.palette()
    tile = QPixmap(paths.image("window_background.jpg"))
    pal.setBrush(QPalette.Window, QBrush(tile) if not tile.isNull() else QBrush(QColor(GREY)))
    widget.setPalette(pal)
    widget.setAutoFillBackground(True)


class ImageWindow(host.HostedWindow, QWidget):
    """A fixed-size window whose background is one of the skin images.

    Widgets are placed on top with absolute coordinates measured from the image.
    extra_height adds plain space under the image for buttons.
    """

    def __init__(self, image, title, extra_height=0, bg=GREY, parent=None, dialog=False):
        flags = Qt.Dialog if dialog else Qt.Window
        super().__init__(parent, flags)
        self.setWindowTitle(title)
        pix = QPixmap(paths.image(image))
        self.setFixedSize(pix.width(), pix.height() + extra_height)
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(bg))
        self.setPalette(pal)
        self.setAutoFillBackground(True)
        self.background = QLabel(self)
        self.background.setPixmap(pix)
        self.background.setGeometry(0, 0, pix.width(), pix.height())

    def center_on_screen(self):
        screen = host.available_geometry(self)
        self.move(screen.center() - self.rect().center())


class ImageButton(QPushButton):
    """A button drawn entirely by one of the skin images."""

    def __init__(self, image, parent=None, tooltip=""):
        super().__init__(parent)
        pix = QPixmap(paths.image(image))
        self.setIcon(QIcon(pix))
        self.setIconSize(pix.size())
        self.setFixedSize(pix.size())
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        if tooltip:
            self.setToolTip(tooltip)
        self.setStyleSheet(
            "QPushButton { border: none; padding: 0; background: transparent; }"
            "QPushButton:pressed { padding-left: 2px; padding-top: 2px; }"
        )


def icon_pixmap(path: str, size: int = 48) -> QPixmap:
    pix = QPixmap(path)
    if pix.isNull():
        return pix
    return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
