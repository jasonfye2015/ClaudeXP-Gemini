"""Kithylin's Art: the gallery. Folders down the left, thumbnails in the middle, and a viewer with Previous and
Next. Videos show as film tiles and open in the computer's player. Reads Art/index.json (build_art.py)."""
import json

from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QSizePolicy,
                               QSplitter, QStackedWidget, QVBoxLayout, QWidget)

from .paths import ART

INDEX = ART / "index.json"
THUMBS = ART / ".thumbs"
TILE = 180


def load_index():
    try:
        return json.loads(INDEX.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"folders": []}


def film_tile(name):
    pm = QPixmap(TILE, int(TILE * 0.62))
    pm.fill(QColor("#2a2a3a"))
    p = QPainter(pm)
    p.setPen(QColor("#9FD3FF"))
    p.drawText(pm.rect().adjusted(8, 8, -8, -8), Qt.AlignCenter | Qt.TextWordWrap, "▶  " + name)
    p.end()
    return pm


class Picture(QLabel):
    """A picture scaled to fit, re-scaled when the window changes."""

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setMinimumSize(200, 150)
        self._pix = QPixmap()

    def set_path(self, path):
        self._pix = QPixmap(str(path))
        self._refit()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._refit()

    def _refit(self):
        if self._pix.isNull():
            self.setText("(couldn't read this picture)")
            return
        self.setPixmap(self._pix.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))


class Gallery(QWidget):
    use_as_background = Signal(str)       # "folder/file" relative to Art

    def __init__(self, open_media=None):
        super().__init__()
        self.index = load_index()
        self.open_media = open_media
        self.folder = None
        self.items = []
        self.position = 0

        self.stack = QStackedWidget()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.stack)

        # page 0: browse
        browse = QWidget()
        split = QSplitter(Qt.Horizontal, browse)
        b_lay = QVBoxLayout(browse)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lay.addWidget(split)
        self.folders = QListWidget()
        self.folders.setObjectName("folders")
        self.folders.setIconSize(QSize(40, 40))
        self.folders.setMinimumWidth(190)
        self.folders.setMaximumWidth(280)
        for f in self.index.get("folders", []):
            item = QListWidgetItem(f"{f['name']}  ({f['count']})")
            cover = THUMBS / f["name"] / (f["cover"].rsplit(".", 1)[0] + ".jpg") if f.get("cover") else None
            if cover and cover.exists():
                item.setIcon(QIcon(str(cover)))
            item.setData(Qt.UserRole, f["name"])
            self.folders.addItem(item)
        self.folders.currentItemChanged.connect(lambda cur, _prev: self.show_folder(cur.data(Qt.UserRole)) if cur else None)
        self.grid = QListWidget()
        self.grid.setObjectName("grid")
        self.grid.setViewMode(QListWidget.IconMode)
        self.grid.setResizeMode(QListWidget.Adjust)
        self.grid.setMovement(QListWidget.Static)
        self.grid.setIconSize(QSize(TILE, TILE))
        self.grid.setGridSize(QSize(TILE + 16, TILE + 36))
        self.grid.setSpacing(6)
        self.grid.setWordWrap(True)
        self.grid.setUniformItemSizes(True)
        self.grid.itemActivated.connect(lambda it: self.open(self.grid.row(it)))
        self.grid.itemDoubleClicked.connect(lambda it: self.open(self.grid.row(it)))
        split.addWidget(self.folders)
        split.addWidget(self.grid)
        split.setStretchFactor(1, 1)
        self.empty = QLabel("No art yet. Run ClaudeApps\\kithylinai\\build_art.py once to copy Kithylin's Art into "
                            "the program and make its thumbnails.")
        self.empty.setWordWrap(True)
        self.empty.setAlignment(Qt.AlignCenter)
        if not self.index.get("folders"):
            b_lay.addWidget(self.empty)
            split.hide()
        self.stack.addWidget(browse)

        # page 1: view
        view = QWidget()
        v_lay = QVBoxLayout(view)
        v_lay.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self.back = QPushButton("◀ Back to the gallery")
        self.back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.prev = QPushButton("◀ Previous")
        self.prev.clicked.connect(lambda: self.step(-1))
        self.next_ = QPushButton("Next ▶")
        self.next_.clicked.connect(lambda: self.step(1))
        self.caption = QLabel("")
        self.caption.setObjectName("caption")
        self.as_bg = QPushButton("Use as chat background")
        self.as_bg.clicked.connect(self._use_bg)
        for w in (self.back, self.prev, self.next_):
            bar.addWidget(w)
        bar.addWidget(self.caption, 1)
        bar.addWidget(self.as_bg)
        v_lay.addLayout(bar)
        self.picture = Picture()
        v_lay.addWidget(self.picture, 1)
        self.stack.addWidget(view)

        if self.folders.count():
            self.folders.setCurrentRow(0)

    # ---- browsing ------------------------------------------------------------------------------------------------
    def show_folder(self, name):
        self.folder = next((f for f in self.index["folders"] if f["name"] == name), None)
        self.grid.clear()
        self.items = self.folder["items"] if self.folder else []
        for it in self.items:
            if it["kind"] == "image":
                thumb = THUMBS / name / (it["file"].rsplit(".", 1)[0] + ".jpg")
                icon = QIcon(str(thumb)) if thumb.exists() else QIcon()
            else:
                icon = QIcon(film_tile(it["file"]))
            label = it["file"] if len(it["file"]) <= 26 else it["file"][:23] + "…"
            item = QListWidgetItem(icon, label)
            item.setToolTip(it["file"])
            self.grid.addItem(item)

    def open(self, row):
        if not (0 <= row < len(self.items)):
            return
        it = self.items[row]
        path = ART / self.folder["name"] / it["file"]
        if it["kind"] == "video":
            if self.open_media is None or not self.open_media(path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
            return
        self.position = row
        self.picture.set_path(path)
        self.caption.setText(f"{self.folder['name']}  ·  {it['file']}  ·  {it.get('w', '?')}×{it.get('h', '?')}  "
                             f"·  {row + 1} of {len(self.items)}")
        self.stack.setCurrentIndex(1)

    def step(self, d):
        n = len(self.items)
        if not n:
            return
        row = self.position
        for _ in range(n):
            row = (row + d) % n
            if self.items[row]["kind"] == "image":
                self.open(row)
                return

    def _use_bg(self):
        if self.folder and 0 <= self.position < len(self.items):
            self.use_as_background.emit(f"{self.folder['name']}/{self.items[self.position]['file']}")

    def keyPressEvent(self, e):
        if self.stack.currentIndex() == 1:
            if e.key() in (Qt.Key_Left, Qt.Key_PageUp):
                return self.step(-1)
            if e.key() in (Qt.Key_Right, Qt.Key_PageDown, Qt.Key_Space):
                return self.step(1)
            if e.key() == Qt.Key_Escape:
                return self.stack.setCurrentIndex(0)
        super().keyPressEvent(e)
