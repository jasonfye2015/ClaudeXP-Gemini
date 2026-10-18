"""Explorer's Thumbnails views: pictures drawn small inside a frame, and folders showing up to four of the pictures
inside them, like XP. Pictures are decoded on worker threads only when their tile is on screen (scaled while
decoding), and kept in data/explorer_thumbs so a folder is quick the second time.

Which view each folder uses is remembered (data/explorer_views.json); a folder with no choice of its own takes its
nearest parent's, and pictures folders (My Pictures, Misc Personal Image Folders) start in Thumbnails."""
import hashlib
import json
import os
from pathlib import Path

from PySide6.QtCore import QObject, QRect, QRunnable, QSize, Qt, QThreadPool, Signal
from PySide6.QtGui import QColor, QIcon, QImage, QImageReader, QPainter, QPen, QPixmap

from ..paths import DATA

CACHE = DATA / "explorer_thumbs"
VIEWS_FILE = DATA / "explorer_views.json"
PICTURE_EXTS = {".jpg", ".jpeg", ".jfif", ".jpe", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp", ".tga", ".ico"}
STORED = 256                    # cached pictures fit this; the views draw them at 96 or 192
# the views: (mode, menu label, thumbnail size or 0)
VIEWS = [("thumbnails", "T&humbnails", 96), ("xlthumbs", "E&xtra Large Thumbnails", 192),
         ("icons", "Ic&ons", 0), ("list", "&List", 0), ("details", "&Details", 0)]
SIZES = {mode: size for mode, _label, size in VIEWS}


_MISSING = object()


def is_picture(path):
    return os.path.splitext(str(path).lower())[1] in PICTURE_EXTS


# ---- which view a folder uses --------------------------------------------------------------------------------
def _load_views():
    try:
        data = json.loads(VIEWS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _picture_folders():
    from . import vfs
    folders = [vfs.my_pictures()]
    try:
        from ..programs import archive_folder
        misc = archive_folder("miscimages")
        if misc is not None:
            folders.append(misc)
    except Exception:
        pass
    return [os.path.normcase(str(f)) for f in folders]


def view_for(folder):
    views = _load_views()
    here = os.path.normcase(str(folder))
    pictures = _picture_folders()
    while True:
        if here in views and views[here] in SIZES:
            return views[here]
        if here in pictures:
            return "thumbnails"
        parent = os.path.dirname(here)
        if parent == here:
            return "icons"
        here = parent


def remember_view(folder, mode):
    views = _load_views()
    views[os.path.normcase(str(folder))] = mode
    try:
        VIEWS_FILE.parent.mkdir(parents=True, exist_ok=True)
        VIEWS_FILE.write_text(json.dumps(views, indent=1), encoding="utf-8")
    except OSError:
        pass


# ---- making thumbnails (worker threads) ----------------------------------------------------------------------
def _cache_file(path):
    try:
        st = os.stat(path)
    except OSError:
        return None
    key = f"{os.path.normcase(str(path))}|{int(st.st_mtime)}|{st.st_size}"
    return CACHE / (hashlib.sha1(key.encode("utf-8")).hexdigest() + ".png")


def picture_thumb(path, size=STORED):
    """The picture scaled to fit size x size (cached), or a null QImage if it can't be read."""
    cached = _cache_file(path) if size == STORED else None
    if cached is not None and cached.exists():
        img = QImage(str(cached))
        if not img.isNull():
            return img
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    full = reader.size()
    if full.isValid() and (full.width() > size or full.height() > size):
        reader.setScaledSize(full.scaled(size, size, Qt.KeepAspectRatio))
    img = reader.read()
    if img.isNull():
        return img
    if img.width() > size or img.height() > size:
        img = img.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    if cached is not None:
        try:
            CACHE.mkdir(parents=True, exist_ok=True)
            img.save(str(cached), "PNG")
        except OSError:
            pass
    return img


def folder_peeks(folder, count=4):
    """Up to four pictures from just inside a folder, small, for its folder thumbnail."""
    names = []
    try:
        with os.scandir(folder) as it:
            for e in it:
                if is_picture(e.name) and e.is_file():
                    names.append(e.name)
                    if len(names) >= 40:
                        break
    except OSError:
        return []
    names.sort(key=str.lower)
    peeks = []
    for name in names:
        img = picture_thumb(Path(folder) / name, 96)
        if not img.isNull():
            peeks.append(img)
            if len(peeks) == count:
                break
    return peeks


class _Job(QRunnable):
    def __init__(self, owner, path, is_dir):
        super().__init__()
        self.owner, self.path, self.is_dir = owner, path, is_dir

    def run(self):
        try:
            result = folder_peeks(self.path) if self.is_dir else picture_thumb(self.path)
        except Exception:
            result = [] if self.is_dir else QImage()
        try:
            self.owner.done.emit(self.path, result)
        except RuntimeError:
            pass                                   # the Explorer closed meanwhile


class Thumbnails(QObject):
    """One per Explorer window: thumbnails asked for by its views, made in the background."""
    ready = Signal(str)                            # a path whose thumbnail is now available
    done = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(3)
        self.images = {}                           # path -> QImage, or [QImage] for a folder (None while loading)
        self.icons = {}                            # (path, size) -> QIcon
        self.done.connect(self._done)

    def clear(self):
        self.pool.clear()
        self.images = {k: v for k, v in self.images.items() if v is not None}
        if len(self.images) > 3000:
            self.images.clear()
            self.icons.clear()

    def icon(self, path, size, is_dir, plain_icon):
        """The thumbnail for a picture or folder at this size, or a framed placeholder while it's being made."""
        got = self.images.get(path, _MISSING)
        if got is _MISSING:
            self.images[path] = None
            self.pool.start(_Job(self, path, is_dir))
            got = None
        if got is None:
            return QIcon(frame(size, None, plain_icon, is_dir))
        key = (path, size)
        if key not in self.icons:
            if is_dir:
                self.icons[key] = QIcon(folder_frame(size, got, plain_icon))
            else:
                self.icons[key] = QIcon(frame(size, got if not got.isNull() else None, plain_icon, False))
        return self.icons[key]

    def _done(self, path, result):
        self.images[path] = result
        for key in [k for k in self.icons if k[0] == path]:
            del self.icons[key]
        self.ready.emit(path)


# ---- drawing --------------------------------------------------------------------------------------------------
def frame(size, img, plain_icon, is_dir):
    """XP's thumbnail tile: a white square with a thin grey border, the picture fitted inside (or the file's own
    icon in the middle when there's no picture)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    p.fillRect(QRect(0, 0, size - 1, size - 1), QColor("white"))
    p.setPen(QPen(QColor("#D0CEC4"), 1))
    p.drawRect(QRect(0, 0, size - 1, size - 1))
    if img is not None:
        inner = size - 8
        scaled = img.scaled(inner, inner, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        p.drawImage((size - scaled.width()) // 2, (size - scaled.height()) // 2, scaled)
    elif plain_icon is not None and not plain_icon.isNull():
        side = 48 if size >= 96 else 32
        p.drawPixmap((size - side) // 2, (size - side) // 2, plain_icon.pixmap(side, side))
    p.end()
    return pm


def folder_frame(size, peeks, plain_icon):
    """A folder's thumbnail: a big folder with up to four of its pictures laid on it."""
    pm = frame(size, None, None, True)
    p = QPainter(pm)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_folder(p, size)
    p.setBrush(Qt.NoBrush)                      # (the picture borders below are outlines only)
    if peeks:
        cell = int(size * 0.27)
        gap = max(2, size // 40)
        left = (size - 2 * cell - gap) // 2
        top = int(size * 0.30)
        for i, img in enumerate(peeks[:4]):
            x = left + (i % 2) * (cell + gap)
            y = top + (i // 2) * (cell + gap)
            scaled = img.scaled(cell, cell, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            cx, cy = (scaled.width() - cell) // 2, (scaled.height() - cell) // 2
            p.drawImage(QRect(x, y, cell, cell), scaled, QRect(cx, cy, cell, cell))
            p.setPen(QPen(QColor("#FFFFFF"), 1))
            p.drawRect(QRect(x, y, cell - 1, cell - 1))
    p.end()
    return pm


def _draw_folder(p, size):
    """XP's big manila folder: the back with its tab, and the front panel the pictures sit on."""
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QLinearGradient, QPainterPath
    s = size / 96.0
    back = QPainterPath()
    back.moveTo(10 * s, 22 * s)
    back.lineTo(10 * s, 16 * s)
    back.quadTo(10 * s, 13 * s, 13 * s, 13 * s)
    back.lineTo(34 * s, 13 * s)
    back.lineTo(39 * s, 19 * s)
    back.lineTo(83 * s, 19 * s)
    back.quadTo(86 * s, 19 * s, 86 * s, 22 * s)
    back.lineTo(86 * s, 80 * s)
    back.lineTo(10 * s, 80 * s)
    back.closeSubpath()
    p.setPen(QPen(QColor("#C8A040"), max(1.0, s)))
    p.setBrush(QColor("#E9C25C"))
    p.drawPath(back)
    front = QRectF(8 * s, 26 * s, 80 * s, 56 * s)
    g = QLinearGradient(front.topLeft(), front.bottomLeft())
    g.setColorAt(0, QColor("#FCE9A6"))
    g.setColorAt(1, QColor("#F1C858"))
    p.setPen(QPen(QColor("#C8A040"), max(1.0, s)))
    p.setBrush(g)
    p.drawRoundedRect(front, 2 * s, 2 * s)


def tile_size(size):
    """The grid cell for a thumbnail of this size (room for the name underneath)."""
    return QSize(size + 24, size + 34)
