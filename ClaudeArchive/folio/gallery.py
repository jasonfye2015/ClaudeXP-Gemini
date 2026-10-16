"""FurFolio Reader: the artists' portfolios on E: (Local Storage/Furry Media Archive.../Portfolios...) as an art
gallery. Artists hang as matted prints, their folios as portfolio cases, and a folio opens as a wall of thumbnails
of every piece. Pieces are shown matted and framed on a charcoal wall with a caption plate, with a slideshow, Fit or
Actual Size (drag to pan), a filmstrip, and a My Favorites collection.

Like FurComix, nothing is indexed up front: each level lists one folder, and thumbnails are decoded (scaled while
decoding) only once their tile is on screen, then cached in data/folio_thumbs.

Keys in the viewer: Left/Right, Home/End, Space slideshow, F favorite, 1 actual size, 0 fit, I info,
Esc back. Double-click: full screen."""
import hashlib
import json
import os
import re
import time
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QImageReader, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QLabel, QLineEdit, QListView, QListWidget,
                               QListWidgetItem, QStackedWidget, QToolButton, QVBoxLayout, QWidget)
from shiboken6 import isValid

from comix.library import IMAGE_EXTS, natural_key, nice_name
from comix.reader import Loader
from claudecore import host

THUMBS = host.data("folio") / "thumbs"          # this computer's cache
STATE_FILE = host.data("folio") / "folio.json"
THUMB = QSize(150, 150)                 # thumbnails are made to fit this
TILE = QSize(170, 170)                  # a matted tile on a wall
FAVORITES = "★ My Favorites"
WALL = QColor("#2B2A28")


def folio_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#1A1A1A"), 1))
    p.setBrush(QColor("#2E2E34"))
    p.drawRoundedRect(QRectF(2.5, 6.5, 27, 22), 2, 2)            # the case
    p.setBrush(QColor("#8A6A3A"))
    p.drawRoundedRect(QRectF(12.5, 3.5, 7, 4), 1.5, 1.5)          # handle
    p.setBrush(QColor("#F6F1E2"))
    p.setPen(QPen(QColor("#B8A878"), 1))
    p.drawRect(QRectF(6.5, 10.5, 19, 14))                           # mat
    g = QLinearGradient(0, 13, 0, 22)
    g.setColorAt(0, QColor("#7FB8F0"))
    g.setColorAt(1, QColor("#3E8A3A"))
    p.setBrush(g)
    p.setPen(Qt.NoPen)
    p.drawRect(QRectF(9, 13, 14, 9))                                # the picture
    p.setBrush(QColor("#F4D040"))
    p.drawEllipse(QRectF(18, 14, 3, 3))
    p.end()
    return QIcon(pm)


def portfolios_root():
    from archivepaths import archive_folder
    archive = archive_folder("mediaarchive")
    if archive is None:
        return None
    return next((d for d in sorted(archive.iterdir()) if d.is_dir() and d.name.lower().startswith("portfolio")), None)


# ---- folders ---------------------------------------------------------------------------------------------------

def scan(folder):
    """(sub-folders, images, info text file) directly in folder (names only)."""
    dirs, images, info = [], [], None
    try:
        with os.scandir(folder) as it:
            for e in it:
                if e.name.startswith(".") or e.name.lower() in ("thumbs.db", "desktop.ini"):
                    continue
                ext = os.path.splitext(e.name)[1].lower()
                if e.is_dir():
                    dirs.append(e.name)
                elif ext in IMAGE_EXTS:
                    images.append(e.name)
                elif ext == ".txt" and info is None:
                    info = e.name
    except OSError:
        pass
    return sorted(dirs, key=natural_key), sorted(images, key=natural_key), info


def look_through(folder):
    """Skip folders that only wrap one other folder."""
    folder = Path(folder)
    for _ in range(6):
        dirs, images, info = scan(folder)
        if len(dirs) == 1 and not images:
            folder = folder / dirs[0]
            continue
        return folder, (dirs, images, info)
    return folder, scan(folder)


def piece_title(name):
    """'[fxa]_show_ponies_07.jpg' -> 'Show Ponies 07'."""
    stem = os.path.splitext(name)[0]
    t = nice_name(stem).replace("_", " ")
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t[:1].upper() + t[1:] if t else stem


class Node:
    """kind: 'artist' | 'folio' | 'piece' | 'favorites'."""
    __slots__ = ("path", "kind", "name", "artist")

    def __init__(self, path, kind, name, artist=""):
        self.path, self.kind, self.name, self.artist = Path(path) if path else None, kind, name, artist

    @property
    def key(self):
        return f"{self.kind}:{self.path}"


def first_image(folder, depth=5):
    """The first piece inside a folder (looking into its first sub-folders)."""
    folder = Path(folder)
    for _ in range(depth):
        dirs, images, _info = scan(folder)
        if images:
            return folder / images[0]
        if not dirs:
            return None
        folder = folder / dirs[0]
    return None


def cover_thumb(folder, tries=6):
    """A folder's cover: the first of its pieces that actually decodes (archives have damaged files)."""
    folder = Path(folder)
    for _ in range(5):
        dirs, images, _info = scan(folder)
        if images:
            for name in images[:tries]:
                img = make_thumb(folder / name)
                if not img.isNull():
                    return img
            return QImage()
        if not dirs:
            return QImage()
        folder = folder / dirs[0]
    return QImage()


def folio_name(name, artist):
    """'fred perry - bounce' under Fred Perry -> 'Bounce'."""
    n = nice_name(name)
    a = re.escape(artist.strip())
    n = re.sub(rf"^{a}('s\s+|\s*[-:]\s*|\s+)", "", n, flags=re.I).strip(" -_") or n
    return n[:1].upper() + n[1:]


def make_thumb(path):
    """A cached thumbnail of one image file (runs on a worker thread)."""
    if path is None:
        return QImage()
    path = Path(path)
    try:
        st = path.stat()
    except OSError:
        return QImage()
    f = THUMBS / (hashlib.sha1(f"{path}|{int(st.st_mtime)}|{st.st_size}".encode()).hexdigest()[:20] + ".jpg")
    if f.exists():
        img = QImage(str(f))
        if not img.isNull():
            return img
    from . import oldimages
    if path.suffix.lower() in oldimages.EXTS:
        img = oldimages.load(path)
        if img.isNull():
            return img
        img = img.scaled(THUMB, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        try:
            THUMBS.mkdir(parents=True, exist_ok=True)
            img.save(str(f), "JPG", 88)
        except OSError:
            pass
        return img
    reader = QImageReader(str(path))
    reader.setDecideFormatFromContent(True)              # '.jpe' and other odd JPEG names
    reader.setAutoTransform(True)
    full = reader.size()
    if full.isValid() and (full.width() > THUMB.width() * 2 or full.height() > THUMB.height() * 2):
        reader.setScaledSize(full.scaled(THUMB * 2, Qt.KeepAspectRatio))
    img = reader.read()
    if img.isNull():
        return img
    img = img.scaled(THUMB, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    if img.hasAlphaChannel():
        flat = QImage(img.size(), QImage.Format_RGB32)
        flat.fill(Qt.white)
        p = QPainter(flat)
        p.drawImage(0, 0, img)
        p.end()
        img = flat
    try:
        THUMBS.mkdir(parents=True, exist_ok=True)
        img.save(str(f), "JPG", 88)
    except OSError:
        pass
    return img


def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=1), encoding="utf-8")
    except OSError:
        pass


# ---- tiles ------------------------------------------------------------------------------------------------------

def _tile(node, img, favorite=False):
    """Artists and pieces hang as matted prints; folios are black portfolio cases with the cover inset."""
    pm = QPixmap(TILE)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    has = img is not None and not img.isNull()
    iw, ih = (img.width(), img.height()) if has else (110, 130)
    if node.kind == "folio":
        case = QRectF(8, 18, TILE.width() - 16, TILE.height() - 24)
        p.setPen(QPen(QColor("#0C0C0C"), 1))
        p.setBrush(QColor("#7A5A2E"))
        p.drawRoundedRect(QRectF(case.center().x() - 18, case.y() - 9, 36, 12), 4, 4)        # handle
        g = QLinearGradient(0, case.top(), 0, case.bottom())
        g.setColorAt(0, QColor("#3A3A42"))
        g.setColorAt(1, QColor("#16161A"))
        p.setBrush(g)
        p.drawRoundedRect(case, 5, 5)
        p.setPen(QPen(QColor("#56565E"), 1, Qt.DashLine))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(case.adjusted(4, 4, -4, -4), 3, 3)                                  # stitching
        room = case.adjusted(16, 14, -16, -14)
        scale = min(room.width() / iw, room.height() / ih, 1.0)
        w, h = iw * scale, ih * scale
        r = QRectF(room.center().x() - w / 2, room.center().y() - h / 2, w, h)
        p.fillRect(r.adjusted(-5, -5, 5, 5), QColor("#F4EEDC"))
        if has:
            p.drawImage(r, img)
    else:
        room = QRectF(10, 6, TILE.width() - 20, TILE.height() - 14)
        scale = min((room.width() - 20) / iw, (room.height() - 20) / ih, 1.0)
        w, h = iw * scale, ih * scale
        r = QRectF(room.center().x() - w / 2, room.center().y() - h / 2, w, h)
        mat = r.adjusted(-9, -9, 9, 9)
        p.fillRect(mat.translated(3, 4), QColor(0, 0, 0, 70))                                 # shadow
        p.setPen(QPen(QColor("#5A4630"), 2))
        p.setBrush(QColor("#F7F2E4"))
        p.drawRect(mat)                                                                        # frame + mat
        if has:
            p.drawImage(r, img)
        else:
            p.fillRect(r, QColor("#E2DCCA"))
        p.setPen(QPen(QColor("#B8AE90"), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(r.adjusted(-0.5, -0.5, 0.5, 0.5))
    if not has:
        p.setPen(QColor("#8A8270"))
        p.setFont(QFont("Tahoma", 8))
        p.drawText(QRectF(14, 0, TILE.width() - 28, TILE.height()), Qt.AlignCenter,
                   "Loading..." if img is None else "")
    if favorite:
        p.setPen(QPen(QColor("#8A6000"), 1))
        p.setBrush(QColor("#FFD23A"))
        p.drawEllipse(QRectF(TILE.width() - 30, 8, 20, 20))
        p.setPen(QColor("#6A4A00"))
        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.drawText(QRectF(TILE.width() - 30, 8, 20, 20), Qt.AlignCenter, "★")
    p.end()
    return pm


class Wall(QListWidget):
    """A grid of tiles that asks for thumbnails only once they're on screen."""
    opened = Signal(object)

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setViewMode(QListView.IconMode)
        self.setIconSize(TILE)
        self.setGridSize(QSize(TILE.width() + 18, TILE.height() + 38))
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setUniformItemSizes(True)
        self.setWordWrap(True)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setStyleSheet("QListWidget { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #EFEBE0,"
                           " stop:1 #E2DCCC); border: none; font: 11px Georgia; color: #2A2418; }"
                           "QListWidget::item:selected { background: rgba(49,106,197,70); color: #102050; }")
        self.itemActivated.connect(lambda item: self.opened.emit(item.data(Qt.UserRole)))
        self.verticalScrollBar().valueChanged.connect(lambda *_: self._timer.start())
        self._timer = QTimer(self, singleShot=True, interval=60, timeout=self._request)

    def fill(self, nodes):
        self.clear()
        for n in nodes:
            item = QListWidgetItem(n.name)
            item.setData(Qt.UserRole, n)
            item.setToolTip(n.name if not n.artist else f"{n.name}\n{n.artist}")
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignTop)
            self.addItem(item)
            self.owner.paint_tile(item)
        self.scrollToTop()
        self._timer.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._timer.start()

    def showEvent(self, event):
        super().showEvent(event)
        self._timer.start()

    def _request(self):
        view = self.viewport().rect().adjusted(0, -TILE.height(), 0, TILE.height())
        for i in range(self.count()):
            item = self.item(i)
            if not item.isHidden() and view.intersects(self.visualItemRect(item)):
                self.owner.want_thumb(item.data(Qt.UserRole))

    def items_for(self, key):
        return [self.item(i) for i in range(self.count()) if self.item(i).data(Qt.UserRole).key == key]


# ---- the viewer ---------------------------------------------------------------------------------------------------

class Easel(QWidget):
    """One piece, matted and framed on the gallery wall, with its caption plate."""

    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.image = None
        self.actual = False
        self.pan = QPointF(0, 0)
        self._drag = None
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(240, 200)

    def set_image(self, img):
        self.image = img
        self.pan = QPointF(0, 0)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor("#34322E"))
        g.setColorAt(1, QColor("#1E1D1B"))
        p.fillRect(self.rect(), g)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.setRenderHint(QPainter.Antialiasing)
        node = self.viewer.current()
        plate_h = 44 if node is not None else 0
        if self.image is None or self.image.isNull():
            p.setPen(QColor("#A8A090"))
            p.setFont(QFont("Georgia", 11))
            p.drawText(self.rect(), Qt.AlignCenter, "Hanging the next piece..." if self.image is None
                       else "This piece couldn't be displayed.")
            return
        W, H = self.width(), self.height() - plate_h
        iw, ih = self.image.width(), self.image.height()
        if self.actual:
            w, h = iw, ih
            x = (W - w) / 2 + self.pan.x()
            y = (H - h) / 2 + self.pan.y()
            p.drawImage(QRectF(x, y, w, h), self.image)
        else:
            mat = 18
            scale = min((W - 2 * mat - 40) / iw, (H - 2 * mat - 30) / ih, 2.0)
            w, h = iw * scale, ih * scale
            r = QRectF((W - w) / 2, (H - h) / 2 + 4, w, h)
            frame = r.adjusted(-mat - 6, -mat - 6, mat + 6, mat + 6)
            p.fillRect(frame.translated(6, 8), QColor(0, 0, 0, 90))                            # shadow
            fg = QLinearGradient(frame.topLeft(), frame.bottomRight())
            fg.setColorAt(0, QColor("#6E5434"))
            fg.setColorAt(1, QColor("#3E2C18"))
            p.fillRect(frame, fg)                                                               # frame
            p.fillRect(r.adjusted(-mat, -mat, mat, mat), QColor("#F7F2E4"))                     # mat
            p.setPen(QPen(QColor("#C8BC98"), 1))
            p.drawRect(r.adjusted(-1.5, -1.5, 1.5, 1.5))                                        # bevel
            p.drawImage(r, self.image)
        if node is not None:
            plate = QRectF(W / 2 - 170, H + 6, 340, plate_h - 12)
            pg = QLinearGradient(0, plate.top(), 0, plate.bottom())
            pg.setColorAt(0, QColor("#E8D68E"))
            pg.setColorAt(1, QColor("#B89A48"))
            p.setPen(QPen(QColor("#6A5420"), 1))
            p.setBrush(pg)
            p.drawRoundedRect(plate, 3, 3)                                                      # brass plate
            p.setPen(QColor("#2A2010"))
            p.setFont(QFont("Georgia", 9, QFont.Bold))
            fm = p.fontMetrics()
            p.drawText(plate.adjusted(8, 2, -8, -plate.height() / 2), Qt.AlignCenter,
                       fm.elidedText(node.name, Qt.ElideRight, int(plate.width() - 16)))
            p.setFont(QFont("Georgia", 8))
            fm = p.fontMetrics()
            p.drawText(plate.adjusted(8, plate.height() / 2 - 1, -8, -2), Qt.AlignCenter,
                       fm.elidedText(node.artist, Qt.ElideRight, int(plate.width() - 16)))

    def mousePressEvent(self, event):
        if self.actual and event.button() == Qt.LeftButton:
            self._drag = (event.position(), QPointF(self.pan))
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.LeftButton:
            (self.viewer.next if event.position().x() > self.width() * 0.35 else self.viewer.prev)()

    def mouseMoveEvent(self, event):
        if self._drag is not None:
            start, pan = self._drag
            self.pan = pan + (event.position() - start)
            self.update()

    def mouseReleaseEvent(self, event):
        self._drag = None
        self.setCursor(Qt.OpenHandCursor if self.actual else Qt.ArrowCursor)

    def mouseDoubleClickEvent(self, event):
        self.viewer.owner.toggle_full_screen()

    def wheelEvent(self, event):
        (self.viewer.next if event.angleDelta().y() < 0 else self.viewer.prev)()

    def keyPressEvent(self, event):
        if not self.viewer.key(event):
            super().keyPressEvent(event)


class Viewer(QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.nodes = []
        self.index = 0
        self.full = {}                        # index -> QImage (a few around the current one)
        self.loader = Loader(self, threads=2)
        self.loader.loaded.connect(self._loaded)
        self.slideshow = QTimer(self, interval=int(owner.state.get("slide_ms", 5000)), timeout=self._slide)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._toolbar())
        self.easel = Easel(self)
        lay.addWidget(self.easel, 1)
        self.strip = QListWidget()
        self.strip.setViewMode(QListView.IconMode)
        self.strip.setFlow(QListView.LeftToRight)
        self.strip.setWrapping(False)
        self.strip.setIconSize(QSize(64, 64))
        self.strip.setGridSize(QSize(74, 72))
        self.strip.setFixedHeight(92)
        self.strip.setMovement(QListView.Static)
        self.strip.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.strip.setFocusPolicy(Qt.NoFocus)
        self.strip.setStyleSheet("QListWidget { background: #161514; border: none; border-top: 1px solid #000; }"
                                 "QListWidget::item:selected { background: #C8A848; }")
        self.strip.itemClicked.connect(lambda item: self.go(item.data(Qt.UserRole)))
        self.strip.horizontalScrollBar().valueChanged.connect(lambda *_: self._strip_timer.start())
        self._strip_timer = QTimer(self, singleShot=True, interval=80, timeout=self._strip_request)
        lay.addWidget(self.strip)

    def _toolbar(self):
        bar = QWidget()
        bar.setObjectName("bar")
        bar.setAttribute(Qt.WA_StyledBackground)
        bar.setStyleSheet("QWidget#bar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #4A4844,"
                          " stop:1 #2E2C29); border-bottom: 1px solid #111; }"
                          "QToolButton { font: 11px Tahoma; color: #EDE6D0; padding: 2px 7px;"
                          " border: 1px solid transparent; border-radius: 3px; }"
                          "QToolButton:hover { border-color: #8A7A50; background: #56524A; }"
                          "QToolButton:checked { background: #7A6630; border-color: #C8A848; }"
                          "QLabel { font: 11px Tahoma; color: #EDE6D0; }")
        row = QHBoxLayout(bar)
        row.setContentsMargins(4, 2, 6, 2)
        row.setSpacing(2)

        def tool(text, tip, slot, checkable=False):
            b = QToolButton()
            b.setText(text)
            b.setToolTip(tip)
            b.setCheckable(checkable)
            b.setFocusPolicy(Qt.NoFocus)
            b.clicked.connect(slot)
            row.addWidget(b)
            return b
        tool("◄ Gallery", "Back to the folio (Esc)", self.owner.close_viewer)
        row.addSpacing(8)
        tool("◄", "Previous (Left)", self.prev)
        self.count_label = QLabel()
        self.count_label.setMinimumWidth(80)
        self.count_label.setAlignment(Qt.AlignCenter)
        row.addWidget(self.count_label)
        tool("►", "Next (Right)", self.next)
        row.addSpacing(8)
        self.play_btn = tool("▶ Slideshow", "Slideshow (Space)", self.toggle_slideshow, True)
        row.addStretch(1)
        self.fav_btn = tool("☆ Favorite", "Add to My Favorites (F)", self.toggle_favorite, True)
        self.actual_btn = tool("Actual Size", "1:1, drag to look around (1 / 0)", self.toggle_actual, True)
        self.info_btn = tool("Info", "About this folio (I)", self.owner.show_info)
        return bar

    # ---- showing ----------------------------------------------------------------------------------------------
    def open(self, nodes, index):
        self.stop_slideshow()
        self.nodes = nodes
        self.full.clear()
        self.loader.clear()
        self.strip.clear()
        for i, n in enumerate(nodes):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, i)
            item.setToolTip(n.name)
            self.strip.addItem(item)
        self.go(index)
        self._strip_timer.start()

    def current(self):
        return self.nodes[self.index] if 0 <= self.index < len(self.nodes) else None

    def go(self, index):
        if not self.nodes:
            return
        self.index = index % len(self.nodes)
        node = self.nodes[self.index]
        self.easel.actual = self.actual_btn.isChecked()
        self.easel.set_image(self._image(self.index))
        for k in (1, 2, -1):
            self._image((self.index + k) % len(self.nodes))
        for k in [k for k in self.full if abs(k - self.index) > 3]:
            del self.full[k]
        self.count_label.setText(f"{self.index + 1} of {len(self.nodes)}")
        fav = self.owner.is_favorite(node)
        self.fav_btn.setChecked(fav)
        self.fav_btn.setText(("★" if fav else "☆") + " Favorite")
        self.info_btn.setEnabled(self.owner.info_for(node) is not None)
        self.strip.setCurrentRow(self.index)
        self.strip.scrollToItem(self.strip.item(self.index), QAbstractItemView.PositionAtCenter)
        self.owner.set_caption(node)

    def _image(self, i):
        if i in self.full:
            return self.full[i]
        path = self.nodes[i].path
        self.loader.request((id(self.nodes), i), lambda: _read_full(path), front=i == self.index)
        return None

    def _loaded(self, key, img):
        nodes_id, i = key
        if nodes_id != id(self.nodes):
            return
        self.full[i] = img
        if i == self.index:
            self.easel.set_image(img)

    def next(self):
        self.go(self.index + 1)

    def prev(self):
        self.go(self.index - 1)

    def _slide(self):
        self.next()

    def toggle_slideshow(self):
        if self.slideshow.isActive():
            self.stop_slideshow()
        else:
            self.slideshow.start()
            self.play_btn.setChecked(True)
            self.play_btn.setText("❚❚ Pause")

    def stop_slideshow(self):
        self.slideshow.stop()
        self.play_btn.setChecked(False)
        self.play_btn.setText("▶ Slideshow")

    def toggle_actual(self):
        self.easel.actual = self.actual_btn.isChecked()
        self.easel.pan = QPointF(0, 0)
        self.easel.setCursor(Qt.OpenHandCursor if self.easel.actual else Qt.ArrowCursor)
        self.easel.update()

    def toggle_favorite(self):
        node = self.current()
        if node is not None:
            self.owner.set_favorite(node, self.fav_btn.isChecked())
            self.go(self.index)

    def _strip_request(self):
        view = self.strip.viewport().rect().adjusted(-150, 0, 150, 0)
        for i in range(self.strip.count()):
            item = self.strip.item(i)
            if item.icon().isNull() and view.intersects(self.strip.visualItemRect(item)):
                node = self.nodes[i]
                self.owner.want_thumb(node, lambda img, item=item: _strip_icon(item, img))

    def stop(self):
        self.stop_slideshow()
        self.loader.clear()
        self.full.clear()

    def key(self, event):
        k = event.key()
        if k in (Qt.Key_Right, Qt.Key_PageDown, Qt.Key_Down):
            self.next()
        elif k in (Qt.Key_Left, Qt.Key_PageUp, Qt.Key_Up, Qt.Key_Backspace):
            self.prev()
        elif k == Qt.Key_Home:
            self.go(0)
        elif k == Qt.Key_End:
            self.go(len(self.nodes) - 1)
        elif k == Qt.Key_Space:
            self.toggle_slideshow()
        elif k == Qt.Key_F:
            self.fav_btn.toggle()
            self.toggle_favorite()
        elif k == Qt.Key_1:
            self.actual_btn.setChecked(True)
            self.toggle_actual()
        elif k == Qt.Key_0:
            self.actual_btn.setChecked(False)
            self.toggle_actual()
        elif k == Qt.Key_I:
            self.owner.show_info()
        elif k == Qt.Key_Escape:
            self.owner.close_viewer()
        else:
            return False
        return True


def _read_full(path):
    from . import oldimages
    if Path(path).suffix.lower() in oldimages.EXTS:
        return oldimages.load(path)
    reader = QImageReader(str(path))
    reader.setDecideFormatFromContent(True)
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid() and max(size.width(), size.height()) > 4000:          # huge scans: keep memory sane
        reader.setScaledSize(size.scaled(QSize(4000, 4000), Qt.KeepAspectRatio))
    return reader.read()


def _strip_icon(item, img):
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    if img is not None and not img.isNull():
        p = QPainter(pm)
        s = img.scaled(QSize(64, 64), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        p.drawImage((64 - s.width()) // 2, (64 - s.height()) // 2, s)
        p.end()
    try:
        item.setIcon(QIcon(pm))
    except RuntimeError:
        pass


# ---- the window ---------------------------------------------------------------------------------------------------

class FolioReader(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.state = load_state()
        self.root = portfolios_root()
        self.history = []                     # (level node) stack
        self.here = None                      # the Node being shown on the wall (None = all artists)
        self.thumbs = {}                      # key -> QImage (None while loading)
        self.waiting = {}                     # key -> [callbacks]
        self.loader = Loader(self, threads=3)
        self.loader.loaded.connect(self._thumb_loaded)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack)
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        col.addWidget(self._bar())
        self.heading = QLabel()
        self.heading.setStyleSheet("background: #E9E4D6; color: #3A2C14; font: italic 15px Georgia;"
                                   " padding: 8px 12px 2px 12px;")
        col.addWidget(self.heading)
        self.info = QLabel()
        self.info.setWordWrap(True)
        self.info.setStyleSheet("background: #E9E4D6; color: #4A4030; font: 11px Georgia; padding: 0 12px 6px 12px;")
        col.addWidget(self.info)
        self.wall = Wall(self)
        self.wall.opened.connect(self.open_node)
        col.addWidget(self.wall, 1)
        self.status = QLabel()
        self.status.setStyleSheet("font: 11px Tahoma; padding: 2px 6px; background: #ECE9D8;"
                                  " border-top: 1px solid #A0A0A0;")
        col.addWidget(self.status)
        self.stack.addWidget(page)
        self.viewer = Viewer(self)
        self.stack.addWidget(self.viewer)
        if self.root is None:
            self.heading.setText("No portfolios found")
            self.info.setText("Put the Furry Media Archive (with its Portfolios folder) on drive E: (Local Storage).")
            self.status.setText("")
        else:
            self.show_node(None, remember=False)

    def _bar(self):
        bar = QWidget()
        bar.setObjectName("bar")
        bar.setAttribute(Qt.WA_StyledBackground)
        bar.setStyleSheet("QWidget#bar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FDFDFB,"
                          " stop:1 #E3E0D2); border-bottom: 1px solid #A0A0A0; }"
                          "QToolButton { font: 11px Tahoma; padding: 3px 8px; border: 1px solid transparent;"
                          " border-radius: 3px; } QToolButton:hover { border-color: #C0BCA8; background: white; }"
                          "QToolButton:disabled { color: #A0A0A0; }"
                          "QLineEdit { font: 11px Tahoma; border: 1px solid #7F9DB9; padding: 1px 4px; }"
                          "QLabel { font: 11px Tahoma; }")
        row = QHBoxLayout(bar)
        row.setContentsMargins(4, 3, 6, 3)
        row.setSpacing(3)

        def tool(text, tip, slot):
            b = QToolButton()
            b.setText(text)
            b.setToolTip(tip)
            b.setFocusPolicy(Qt.NoFocus)
            b.clicked.connect(slot)
            row.addWidget(b)
            return b
        self.back_btn = tool("◄ Back", "Back", self.go_back)
        tool("Artists", "All artists", self.go_home)
        tool(FAVORITES, "Your favorite pieces", lambda: self.open_node(Node(None, "favorites", FAVORITES)))
        row.addSpacing(10)
        self.where = QLabel()
        self.where.setStyleSheet("color: #404040;")
        row.addWidget(self.where, 1)
        row.addWidget(QLabel("Find:"))
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Artist or title")
        self.filter.setFixedWidth(150)
        self.filter.textChanged.connect(self._filter)
        row.addWidget(self.filter)
        return bar

    # ---- walls ----------------------------------------------------------------------------------------------
    def nodes_for(self, node):
        """What hangs on the wall for a node: artists, an artist's folios, or a folio's pieces."""
        if node is None:
            dirs, _images, _info = scan(self.root)
            return [Node(self.root / d, "artist", nice_name(d), d) for d in dirs if first_image(self.root / d)]
        if node.kind == "favorites":
            return [Node(p, "piece", piece_title(Path(p).name), info.get("artist", ""))
                    for p, info in self.state.get("favorites", {}).items() if os.path.exists(p)]
        folder, (dirs, images, _info) = look_through(node.path)
        artist = node.artist
        if node.kind == "artist":
            out = []
            if images:
                loose = "Loose Pieces" if folder == node.path else folio_name(folder.name, artist)
                out.append(Node(folder, "folio", loose, artist))
            out += [Node(folder / d, "folio", folio_name(d, artist), artist) for d in dirs if first_image(folder / d)]
            return out
        out = [Node(folder / name, "piece", piece_title(name), f"{node.name} · {artist}") for name in images]
        for d in dirs:                         # a folio's sub-folders hang as folios of their own
            if first_image(folder / d):
                out.append(Node(folder / d, "folio", folio_name(d, artist), artist))
        return out

    def show_node(self, node, remember=True):
        if remember:
            self.history.append(self.here)
        self.here = node
        self.loader.clear()
        self.waiting.clear()
        self.thumbs = {k: v for k, v in self.thumbs.items() if v is not None}
        nodes = self.nodes_for(node)
        if node is not None and node.kind == "artist" and len(nodes) == 1 and nodes[0].kind == "folio":
            node = self.here = nodes[0]                  # one folio: open it straight away
            nodes = self.nodes_for(node)
        self.filter.blockSignals(True)
        self.filter.clear()
        self.filter.blockSignals(False)
        self.back_btn.setEnabled(bool(self.history))
        self.wall.fill(nodes)
        pieces = sum(n.kind == "piece" for n in nodes)
        if node is None:
            self.heading.setText("The Artists")
            self.where.setText("Portfolios")
            self.info.setText("")
            self.status.setText(f"{len(nodes)} artists")
        elif node.kind == "favorites":
            self.heading.setText(FAVORITES)
            self.where.setText("Portfolios  ›  My Favorites")
            self.info.setText("" if nodes else "Press ☆ Favorite (or F) while viewing a piece to hang it here.")
            self.status.setText(f"{pieces} piece{'s' if pieces != 1 else ''}")
        else:
            self.heading.setText(node.name if node.kind == "artist" else f"{node.name}  —  {node.artist}")
            self.where.setText("Portfolios  ›  " + (node.artist if node.kind == "artist"
                                                        else f"{node.artist}  ›  {node.name}"))
            text = self.info_for(node) if node.kind == "folio" else None
            self.info.setText(_short(text) if text else "")
            folios = sum(n.kind == "folio" for n in nodes)
            bits = [f"{folios} folio{'s' if folios != 1 else ''}" if folios else "",
                    f"{pieces} piece{'s' if pieces != 1 else ''}" if pieces else ""]
            self.status.setText(", ".join(b for b in bits if b))
        self.info.setVisible(bool(self.info.text()))
        if self.frame is not None:
            self.frame.set_title("FurFolio Reader" if node is None else f"{node.name} - FurFolio Reader")

    def open_node(self, node):
        if node.kind == "piece":
            pieces = [self.wall.item(i).data(Qt.UserRole) for i in range(self.wall.count())
                      if self.wall.item(i).data(Qt.UserRole).kind == "piece"]
            self.stack.setCurrentWidget(self.viewer)
            self.viewer.open(pieces, pieces.index(node))
            self.viewer.easel.setFocus()
        else:
            self.show_node(node)

    def go_back(self):
        if self.history:
            self.show_node(self.history.pop(), remember=False)

    def go_home(self):
        self.history.clear()
        if self.root is None:
            self.root = portfolios_root()
            if self.root is None:
                return
        self.show_node(None, remember=False)

    def close_viewer(self):
        self.viewer.stop()
        self.stack.setCurrentIndex(0)
        if self.here is not None and self.here.kind == "favorites":
            self.show_node(self.here, remember=False)
        else:
            for i in range(self.wall.count()):
                self.paint_tile(self.wall.item(i))
            if self.viewer.current() is not None:
                for item in self.wall.items_for(self.viewer.current().key):
                    self.wall.setCurrentItem(item)
                    self.wall.scrollToItem(item)
        if self.frame is not None:
            self.frame.set_title("FurFolio Reader" if self.here is None else f"{self.here.name} - FurFolio Reader")
        self.wall.setFocus()

    def set_caption(self, node):
        if self.frame is not None:
            self.frame.set_title(f"{node.name} - FurFolio Reader")
        self.viewer.easel.update()

    def _filter(self, text):
        t = text.lower().strip()
        for i in range(self.wall.count()):
            item = self.wall.item(i)
            node = item.data(Qt.UserRole)
            item.setHidden(bool(t) and t not in (node.name + " " + node.artist).lower())
        self.wall._timer.start()

    # ---- info and favorites ------------------------------------------------------------------------------
    def info_for(self, node):
        """The folio's own Info.txt (or any .txt) if it has one."""
        folder = node.path.parent if node.kind == "piece" else node.path
        if folder is None:
            return None
        _d, _i, info = scan(folder)
        if info is None:
            return None
        try:
            return (folder / info).read_text(encoding="utf-8", errors="replace").strip() or None
        except OSError:
            return None

    def show_info(self):
        node = self.viewer.current() if self.stack.currentWidget() is self.viewer else self.here
        text = self.info_for(node) if node is not None else None
        if text:
            host.message(self.desktop, "About this folio", text[:1500], "info")

    def is_favorite(self, node):
        return str(node.path) in self.state.get("favorites", {})

    def set_favorite(self, node, on):
        favs = self.state.setdefault("favorites", {})
        if on:
            favs[str(node.path)] = {"artist": node.artist, "added": time.time()}
        else:
            favs.pop(str(node.path), None)
        save_state(self.state)

    # ---- thumbnails -------------------------------------------------------------------------------------------
    def want_thumb(self, node, callback=None):
        key = node.key
        if callback is not None:
            if self.thumbs.get(key) is not None:
                callback(self.thumbs[key])
                return
            self.waiting.setdefault(key, []).append(callback)
        if key in self.thumbs:
            return
        self.thumbs[key] = None
        target = node.path if node.kind == "piece" else None
        folder = node.path
        self.loader.request(key, lambda: make_thumb(target) if target is not None else cover_thumb(folder))

    def _thumb_loaded(self, key, img):
        self.thumbs[key] = img
        for item in self.wall.items_for(key):
            self.paint_tile(item)
        for cb in self.waiting.pop(key, []):
            cb(img)

    def paint_tile(self, item):
        node = item.data(Qt.UserRole)
        img = self.thumbs.get(node.key) if node.key in self.thumbs else None
        item.setIcon(QIcon(_tile(node, img, node.kind == "piece" and self.is_favorite(node))))

    def toggle_full_screen(self):
        if self.frame is not None:
            self.frame.toggle_maximize()

    def keyPressEvent(self, event):
        if self.stack.currentWidget() is self.viewer and self.viewer.key(event):
            return
        if event.key() == Qt.Key_Backspace:
            self.go_back()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.loader.clear()
        self.viewer.stop()
        save_state(self.state)
        event.accept()


def _short(text, n=400):
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "…"


_open = {}


def open_folio(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = FolioReader(desktop)
        win = host.window(desktop, "FurFolio Reader", body, folio_icon(), (820, 600))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win
