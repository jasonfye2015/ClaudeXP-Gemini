"""Buddy Icon picker (icons.jpg)."""
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QImage, QPainter
from PySide6.QtWidgets import (QFileDialog, QLabel, QListWidget, QListWidgetItem,
                               QPushButton)

from .. import host, paths
from .common import ImageWindow, icon_pixmap

ICON_SIZE = 96  # saved size of uploaded icons (shown at 48, sharp on high-DPI screens)


def make_custom_icon(source: str):
    """Crop a picture to a centered square, resize it, and save it as assets/icons/customNNN.jpg.

    Returns the new file's name, or None if the picture couldn't be read.
    """
    img = QImage(source)
    if img.isNull():
        return None
    side = min(img.width(), img.height())
    img = img.copy((img.width() - side) // 2, (img.height() - side) // 2, side, side)
    img = img.scaled(ICON_SIZE, ICON_SIZE, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    icon = QImage(ICON_SIZE, ICON_SIZE, QImage.Format_RGB32)  # JPG has no transparency: use white
    icon.fill(Qt.white)
    painter = QPainter(icon)
    painter.drawImage(0, 0, img)
    painter.end()
    paths.ICONS.mkdir(parents=True, exist_ok=True)
    n = 1
    while (paths.ICONS / f"custom{n:03d}.jpg").exists():
        n += 1
    name = f"custom{n:03d}.jpg"
    icon.save(str(paths.ICONS / name), "JPG", 92)
    return name


class IconsWindow(ImageWindow):
    icon_changed = Signal()

    def __init__(self, settings, parent=None):
        super().__init__("icons.jpg", "Buddy Icon", parent=parent, dialog=True)
        self.settings = settings
        icons = paths.buddy_icons()
        current = settings["buddy_icon"] or (icons[0].name if icons else "")
        self.chosen = current

        self.preview = QLabel(self)
        self.preview.setGeometry(112, 182, 52, 52)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("background: white; border: 1px solid #808080;")

        self.grid = QListWidget(self)
        self.grid.setGeometry(299, 35, 249, 338)
        self.grid.setViewMode(QListWidget.IconMode)
        self.grid.setIconSize(QSize(48, 48))
        self.grid.setGridSize(QSize(72, 76))
        self.grid.setResizeMode(QListWidget.Adjust)
        self.grid.setMovement(QListWidget.Static)
        self.grid.setFrameShape(QListWidget.NoFrame)
        for path in icons:
            item = self._add_item(path.name)
            if path.name == current:
                self.grid.setCurrentItem(item)
        self.grid.itemClicked.connect(self._pick)

        # Your own picture, in the space under "Images to use for buddies".
        own = QLabel("Use your own picture:", self)
        own.setGeometry(100, 282, 185, 16)
        own.setStyleSheet("font-weight: bold;")
        browse = QPushButton("Browse...", self)
        browse.setGeometry(100, 302, 85, 23)
        browse.setToolTip("Pick any picture to use as your buddy icon")
        browse.clicked.connect(self._browse)
        hint = QLabel("It will be cropped to a square and resized to fit. "
                      "Click OK or Apply to use it.", self)
        hint.setGeometry(100, 330, 187, 40)
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #404040;")

        for i, (text, slot) in enumerate([("OK", self._ok), ("Cancel", self.close),
                                          ("Apply", self._apply)]):
            btn = QPushButton(text, self)
            btn.setGeometry(299 + i * 85, 380, 78, 23)
            btn.clicked.connect(slot)

        self._show_preview()

    def _add_item(self, name):
        item = QListWidgetItem(QIcon(icon_pixmap(str(paths.ICONS / name))), name.rsplit(".", 1)[0])
        item.setData(Qt.UserRole, name)
        self.grid.addItem(item)
        return item

    def _browse(self):
        exts = " ".join(f"*{e}" for e in sorted(paths.ICON_EXTS))
        source, _ = QFileDialog.getOpenFileName(self, "Choose a Buddy Icon", "",
                                                f"Pictures ({exts});;All files (*)")
        if not source:
            return
        name = make_custom_icon(source)
        if not name:
            host.information(self, "Buddy Icon", "That picture couldn't be opened.")
            return
        item = self._add_item(name)
        self.grid.setCurrentItem(item)
        self.grid.scrollToItem(item)
        self._pick(item)

    def _pick(self, item):
        self.chosen = item.data(Qt.UserRole)
        self._show_preview()

    def _show_preview(self):
        self.preview.setPixmap(icon_pixmap(paths.resolve_icon(self.chosen)))

    def _apply(self):
        self.settings.set("buddy_icon", self.chosen)
        self.icon_changed.emit()

    def _ok(self):
        self._apply()
        self.close()
