"""Gallery: every picture shared between the user and one buddy, as thumbnails."""
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QImage, QImageReader, QPainter, QPixmap
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QPushButton, QVBoxLayout, QWidget)

from .. import host, paths, timefmt
from .common import tiled_background
from .picture import PictureViewer

THUMB = 96
SHOW_ALL, SHOW_THEIRS, SHOW_MINE = "All pictures", "From {name}", "From you"


def thumbnail(path, size=THUMB) -> QPixmap:
    """A square thumbnail on white, loaded at reduced size so big pictures stay fast."""
    reader = QImageReader(str(path))
    full = reader.size()
    if full.width() > 0 and full.height() > 0:
        scale = min(size / full.width(), size / full.height(), 1.0)
        reader.setScaledSize(QSize(max(int(full.width() * scale), 1), max(int(full.height() * scale), 1)))
    img = reader.read()
    canvas = QImage(size, size, QImage.Format_RGB32)
    canvas.fill(Qt.white)
    if not img.isNull():
        painter = QPainter(canvas)
        painter.drawImage((size - img.width()) // 2, (size - img.height()) // 2, img)
        painter.end()
    return QPixmap.fromImage(canvas)


class GalleryWindow(host.HostedWindow, QWidget):
    def __init__(self, settings, world, buddy_id, parent=None):
        super().__init__(parent, Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.settings, self.world = settings, world
        self.buddy = world.buddies[buddy_id]
        self.setWindowTitle(f"Gallery - {self.buddy.name}")
        tiled_background(self)
        self.resize(470, 420)
        self.viewers = []

        root = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("Show:"))
        self.filter = QComboBox()
        self.filter.addItems([SHOW_ALL, SHOW_THEIRS.format(name=self.buddy.name), SHOW_MINE])
        self.filter.currentIndexChanged.connect(self._refresh)
        top.addWidget(self.filter)
        top.addStretch()
        self.count = QLabel()
        top.addWidget(self.count)
        root.addLayout(top)

        self.grid = QListWidget()
        self.grid.setViewMode(QListWidget.IconMode)
        self.grid.setIconSize(QSize(THUMB, THUMB))
        self.grid.setGridSize(QSize(THUMB + 32, THUMB + 44))
        self.grid.setResizeMode(QListWidget.Adjust)
        self.grid.setMovement(QListWidget.Static)
        self.grid.setWordWrap(True)
        self.grid.setSpacing(4)
        self.grid.setFrameShape(QListWidget.StyledPanel)
        self.grid.setFrameShadow(QListWidget.Sunken)
        self.grid.setStyleSheet("QListWidget { background: white; font: 8pt 'Arial'; }")
        self.grid.setToolTip("Click a picture to see it full size")
        self.grid.itemClicked.connect(self._open)
        root.addWidget(self.grid, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        close = QPushButton("Close")
        close.clicked.connect(self.close)
        buttons.addWidget(close)
        root.addLayout(buttons)

        self._refresh()
        world.message_added.connect(self._message_added)

    def _pictures(self):
        """(path, from_user, timestamp) for every picture in the conversation, oldest first."""
        out = []
        for m in self.buddy.history.messages:
            if not m.get("image"):
                continue
            if m["kind"] == "user":
                path = paths.DATA / m["image"]
                out.append((path, True, m["ts"]))
            elif m["kind"] == "contact" and self.buddy.contact.pictures:
                out.append((self.buddy.contact.pictures.path(m["image"]), False, m["ts"]))
        return out

    def _refresh(self, *_):
        mode = self.filter.currentIndex()  # 0 all, 1 theirs, 2 mine
        self.grid.clear()
        shown = 0
        tz = self.buddy.contact.timezone
        for path, from_user, ts in self._pictures():
            if (mode == 1 and from_user) or (mode == 2 and not from_user) or not path.exists():
                continue
            who = "From you" if from_user else f"From {self.buddy.name}"
            when = timefmt.stamp(ts, None if from_user else tz).split(" ")[0]
            item = QListWidgetItem(QIcon(thumbnail(path)), f"{who}\n{when}")
            item.setData(Qt.UserRole, (str(path), from_user))
            item.setToolTip(f"{who}, {timefmt.stamp(ts, None if from_user else tz)}")
            self.grid.addItem(item)
            shown += 1
        self.count.setText(f"{shown} picture{'s' if shown != 1 else ''}")
        if not shown:
            empty = QListWidgetItem("No pictures shared yet.")
            empty.setFlags(Qt.NoItemFlags)
            self.grid.addItem(empty)

    def _message_added(self, buddy_id, entry):
        if buddy_id == self.buddy.id and entry.get("image"):
            self._refresh()

    def _open(self, item):
        data = item.data(Qt.UserRole)
        if not data:
            return
        path, from_user = data
        title = "Picture you sent" if from_user else f"Picture from {self.buddy.name}"
        viewer = PictureViewer(path, title, self)
        self.viewers.append(viewer)
        viewer.destroyed.connect(lambda *_: self.viewers.remove(viewer) if viewer in self.viewers else None)
        viewer.show()
