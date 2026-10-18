"""Camera Roll Archive: every photo and video in Local Storage/Camera Rolls, by year, then month, in the order they
were taken - whichever backup folder they were copied into.

When each one was taken comes from the picture itself: the date in its file name (IMG_20180602_..., PXL_...,
VID-...-WA...), else the camera's own date in the file (EXIF, in JPEG, HEIC and RAW files), else a video's recording
date, else the file's date. Working that out reads a little of each file, so it's done once in the background and
kept (data/camroll/index.json); later only new or changed files are looked at.

Home is a shelf of years; a year opens as its months; a month as a wall of its photos and videos in Thumbnails or
Extra Large Thumbnails. Pictures open in FurFolio's framed viewer (slideshow and all), videos in this computer's media
player. HEIC and RAW photos can't be drawn here and show as labelled cards. The '_Duplicates (delete me)' folder the
duplicate finder leaves, and phones' hidden thumbnail folders, are skipped."""
import calendar
import json
import os
import re
import struct
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QObject, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from shiboken6 import isValid

from .gallery import Node
from .miscfurry import MiscFurryViewer, _album_tile, _picture_tile, thumb
from claudecore import host

DATA = host.data("camroll")
INDEX = DATA / "index.json"
PICTURE_EXTS = {".jpg", ".jpeg", ".jpe", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}
CARD_EXTS = {".heic", ".heif", ".cr2", ".dng", ".nef", ".arw"}              # photos Qt can't draw
VIDEO_EXTS = {".mp4", ".mov", ".3gp", ".avi", ".mkv", ".m4v", ".mts", ".m2ts", ".wmv", ".mpg", ".mpeg", ".webm"}
MEDIA_EXTS = PICTURE_EXTS | CARD_EXTS | VIDEO_EXTS
SKIP_DIRS = {"_duplicates (delete me)", "cache", "thumbnails", ".thumbnails", ".aux", ".trashed"}
FIRST_YEAR, LAST_YEAR = 1990, 2100


def camroll_icon():
    """A little camera with a red paw on its lens cap."""
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 8, 0, 28)
    g.setColorAt(0, QColor("#5A5A62"))
    g.setColorAt(1, QColor("#26262C"))
    p.setPen(QPen(QColor("#101014"), 1))
    p.setBrush(QColor("#3A3A42"))
    p.drawRoundedRect(QRectF(10.5, 5.5, 10, 5), 1.5, 1.5)           # viewfinder hump
    p.setBrush(g)
    p.drawRoundedRect(QRectF(2.5, 9.5, 27, 18), 3, 3)
    p.setBrush(QColor("#C8C8D0"))
    p.drawEllipse(QRectF(9.5, 11.5, 13, 13))
    p.setBrush(QColor("#1A1A20"))
    p.drawEllipse(QRectF(11.5, 13.5, 9, 9))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#E8261C"))
    for x, y, r in ((16, 19.2, 1.9), (13.6, 16.6, 0.9), (15.2, 15.6, 0.9), (16.8, 15.6, 0.9), (18.4, 16.6, 0.9)):
        p.drawEllipse(QRectF(x - r, y - r, 2 * r, 2 * r))
    p.setBrush(QColor("#F0C040"))
    p.drawRect(QRectF(24, 11.5, 3, 2))                                  # flash
    p.end()
    return QIcon(pm)


def _count(n, word):
    return f"{n:,} {word}{'' if n == 1 else 's'}"


def _items(n):
    return "1 photo or video" if n == 1 else f"{n:,} photos and videos"


def camroll_root():
    root = host.local_storage() / "Camera Rolls"
    return root if root.is_dir() else None


# ---- when was it taken? ---------------------------------------------------------------------------------------
def _valid(y, mo, d, h=0, mi=0, s=0):
    try:
        if FIRST_YEAR <= y <= LAST_YEAR:
            return datetime(y, mo, d, h, mi, s)
    except ValueError:
        pass
    return None


_NAME_DATE = re.compile(r"(?<!\d)((?:19|20)\d\d)[-_.]?(\d\d)[-_.]?(\d\d)(?:[-_ T.]?(\d\d)[-_.:]?(\d\d)[-_.:]?(\d\d))?")


def name_date(name):
    """IMG_20180602_123456.jpg, PXL_20230101_..., VID-20180602-WA0001.mp4, 2018-06-02 12.34.56.jpg..."""
    for m in _NAME_DATE.finditer(name):
        parts = [int(x) if x else 0 for x in m.groups()]
        when = _valid(*parts)
        if when is not None:
            return when
    return None


def _tiff_date(data, start):
    """DateTimeOriginal (or DateTime) from a TIFF/EXIF block beginning at data[start]."""
    try:
        order = data[start:start + 2]
        if order not in (b"II", b"MM"):
            return None
        e = "<" if order == b"II" else ">"

        def ifd(offset):
            entries = {}
            n = struct.unpack_from(e + "H", data, start + offset)[0]
            for i in range(min(n, 400)):
                tag, kind, count, value = struct.unpack_from(e + "HHII", data, start + offset + 2 + i * 12)
                entries[tag] = (kind, count, value, start + offset + 2 + i * 12 + 8)
            return entries

        def text(entry):
            kind, count, value, _at = entry
            raw = data[start + value:start + value + count]
            return raw.split(b"\0")[0].decode("ascii", "ignore")

        first = ifd(struct.unpack_from(e + "I", data, start + 4)[0])
        found = []
        if 0x8769 in first:
            exif = ifd(first[0x8769][2])
            for tag in (0x9003, 0x9004):
                if tag in exif:
                    found.append(text(exif[tag]))
        if 0x0132 in first:
            found.append(text(first[0x0132]))
        for stamp in found:
            m = re.match(r"(\d{4}):(\d\d):(\d\d)[ T](\d\d):(\d\d):(\d\d)", stamp)
            if m:
                when = _valid(*map(int, m.groups()))
                if when is not None:
                    return when
    except (struct.error, IndexError, ValueError):
        pass
    return None


def exif_date(path):
    """The camera's date in a JPEG, HEIC or TIFF-based RAW file (reads at most the first 512 KB)."""
    try:
        with open(path, "rb") as f:
            data = f.read(512 * 1024)
    except OSError:
        return None
    if data[:4] in (b"II*\0", b"MM\0*"):                                # TIFF-based RAW (CR2, DNG, NEF...)
        return _tiff_date(data, 0)
    at = data.find(b"Exif\0\0")
    while at != -1:
        when = _tiff_date(data, at + 6)
        if when is not None:
            return when
        at = data.find(b"Exif\0\0", at + 6)
    return None


def video_date(path):
    """A QuickTime/MP4's recording date (the movie header's creation time), if it's a sensible one."""
    try:
        with open(path, "rb") as f:
            size = os.fstat(f.fileno()).st_size
            pos = 0
            while pos + 8 <= size:
                f.seek(pos)
                head = f.read(16)
                if len(head) < 8:
                    break
                length, kind = struct.unpack(">I4s", head[:8])
                header = 8
                if length == 1:
                    length = struct.unpack(">Q", head[8:16])[0]
                    header = 16
                elif length == 0:
                    length = size - pos
                if kind == b"moov":
                    box = f.read(min(length - header, 4096)) if header == 16 else head[8:] + f.read(min(length, 4096))
                    at = box.find(b"mvhd")
                    if at == -1:
                        return None
                    version = box[at + 4]
                    secs = struct.unpack_from(">Q" if version == 1 else ">I", box, at + 8)[0]
                    if secs <= 0:
                        return None
                    when = datetime.fromtimestamp(secs - 2082844800, tz=timezone.utc).astimezone().replace(tzinfo=None)
                    return when if FIRST_YEAR <= when.year <= LAST_YEAR else None
                if length < header:
                    break
                pos += length
    except (OSError, struct.error, ValueError, OverflowError, IndexError):
        pass
    return None


def taken(path, mtime):
    name = os.path.basename(path)
    when = name_date(name)
    if when is None:
        ext = os.path.splitext(name.lower())[1]
        if ext in VIDEO_EXTS:
            when = video_date(path)
        else:
            when = exif_date(path)
    if when is None:
        when = datetime.fromtimestamp(mtime)
    return when.strftime("%Y-%m-%d %H:%M:%S")


# ---- the index -------------------------------------------------------------------------------------------------
class Indexer(QObject):
    """Walks Camera Rolls on a worker thread, dating every photo and video; old answers come from the index."""
    progress = Signal(int, int)                 # dated so far, found so far
    finished = Signal(object)                   # [(taken, path)]

    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = Path(root)
        self.stopped = False

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            old = json.loads(INDEX.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            old = {}
        files = []
        for dirpath, dirs, names in os.walk(self.root):
            dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS and not d.startswith(".")]
            for name in names:
                if os.path.splitext(name.lower())[1] in MEDIA_EXTS:
                    files.append(os.path.join(dirpath, name))
            if self.stopped:
                return
        new, items, last = {}, [], 0.0
        for i, path in enumerate(files):
            if self.stopped:
                return
            rel = os.path.relpath(path, self.root)
            try:
                st = os.stat(path)
            except OSError:
                continue
            known = old.get(rel)
            if known and known[0] == st.st_size and known[1] == int(st.st_mtime):
                stamp = known[2]
            else:
                stamp = taken(path, st.st_mtime)
            new[rel] = [st.st_size, int(st.st_mtime), stamp]
            items.append((stamp, path))
            if time.time() - last > 0.25:
                last = time.time()
                self.progress.emit(i + 1, len(files))
        try:
            DATA.mkdir(parents=True, exist_ok=True)
            tmp = INDEX.with_suffix(".tmp")
            tmp.write_text(json.dumps(new), encoding="utf-8")
            tmp.replace(INDEX)
        except OSError:
            pass
        items.sort()
        self.finished.emit(items)


class Album(Node):
    """A year or a month on the shelf: its cover picture and the level it opens."""
    __slots__ = ("cover", "level")


# ---- tiles -----------------------------------------------------------------------------------------------------
def _card_tile(node, size):
    """A HEIC or RAW photo: a dark slide with its kind and when it was taken (it can't be drawn here)."""
    t = size + 20
    pm = QPixmap(t, t)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    r = QRectF(14, 18, size - 8, size * 0.72)
    p.fillRect(r.translated(3, 4), QColor(0, 0, 0, 60))
    p.setPen(QPen(QColor("#B8B0A0"), 1))
    p.setBrush(QColor("white"))
    p.drawRect(r.adjusted(-6, -6, 6, 6))
    p.fillRect(r, QColor("#3A3E48"))
    p.setPen(QColor("#E8ECF4"))
    p.setFont(QFont("Tahoma", max(9, size // 12), QFont.Bold))
    p.drawText(r.adjusted(0, 0, 0, -r.height() * 0.3), Qt.AlignCenter, node.path.suffix[1:].upper())
    p.setFont(QFont("Tahoma", max(7, size // 20)))
    p.setPen(QColor("#B0B8C8"))
    p.drawText(r.adjusted(4, r.height() * 0.45, -4, 0), Qt.AlignCenter | Qt.TextWordWrap,
               "photo - open it in its program")
    p.end()
    return pm


# ---- the program --------------------------------------------------------------------------------------------------
class CameraRollArchive(MiscFurryViewer):
    TITLE = "Camera Roll Archive"
    PLACE = "Camera Rolls"
    RACK = "All Years"

    def find_root(self):
        return camroll_root()

    def __init__(self, desktop):
        self.items = None                         # [(taken, path)] once the index is ready
        self.level = ("home",)
        self.levels = []
        super().__init__(desktop)
        self.find.setPlaceholderText("Name")
        if self.root is None:
            self.status.setText("Put a 'Camera Rolls' folder on drive E: (Local Storage).")
            return
        self.indexer = Indexer(self.root, self)
        self.indexer.progress.connect(self._indexing)
        self.indexer.finished.connect(self._indexed)
        self.indexer.start()

    def _indexing(self, done, total):
        if self.items is None:
            self.status.setText(f"Looking through the camera rolls... {done:,} of {total:,} photos and videos dated")

    def _indexed(self, items):
        self.items = items
        self.show_level(self.level, remember=False)

    # ---- browsing ---------------------------------------------------------------------------------------------
    def show_rack(self):
        self.levels.clear()
        self.show_level(("home",), remember=False)

    def show_level(self, level, remember=True):
        if remember and level != self.level:
            self.levels.append(self.level)
        self.level = level
        self._reset()
        self.here = None
        self.stack.setCurrentIndex(0)
        self.back_btn.setEnabled(bool(self.levels))
        if self.items is None:
            self.wall.clear()
            self.where.setText(self.PLACE)
            self.status.setText("Looking through the camera rolls...")
            return
        if level[0] == "home":
            years = {}
            for stamp, path in self.items:
                years.setdefault(stamp[:4], []).append(path)
            nodes = [self._album("year", y, f"{y}", paths) for y, paths in sorted(years.items())]
            crumbs, words = [], f"{_count(len(nodes), 'year')}, {_items(len(self.items))}"
            self._set_wall_look(True)
        elif level[0] == "year":
            months = {}
            for stamp, path in self.items:
                if stamp[:4] == level[1]:
                    months.setdefault(stamp[5:7], []).append(path)
            nodes = [self._album("month", f"{level[1]}-{m}", calendar.month_name[int(m)], paths)
                     for m, paths in sorted(months.items())]
            total = sum(len(p) for p in months.values())
            crumbs, words = [level[1]], f"{_count(len(nodes), 'month')}, {_items(total)}"
            self._set_wall_look(True)
        else:
            y, m = level[1].split("-")
            nodes, pics, vids = [], 0, 0
            for stamp, path in self.items:
                if stamp[:7] == level[1]:
                    ext = os.path.splitext(path.lower())[1]
                    kind = "video" if ext in VIDEO_EXTS else "card" if ext in CARD_EXTS else "piece"
                    node = Node(path, kind, Path(path).stem, self._when(stamp))
                    nodes.append(node)
                    vids += kind == "video"
                    pics += kind != "video"
            crumbs = [y, calendar.month_name[int(m)]]
            words = ", ".join(_count(n, w) for n, w in ((pics, "photo"), (vids, "video")) if n)
            self._set_wall_look(False)
        self.wall.fill(nodes)
        self.where.setText("  ›  ".join([self.PLACE] + crumbs))
        self.status.setText(words)
        if self.frame is not None:
            self.frame.set_title(f"{' '.join(reversed(crumbs))} - {self.TITLE}" if crumbs else self.TITLE)

    @staticmethod
    def _when(stamp):
        try:
            return datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S").strftime("%A, %B %d, %Y  %I:%M %p")
        except ValueError:
            return stamp

    @staticmethod
    def _album(kind, key, name, paths):
        node = Album(f"{kind}/{key}", kind, name, _items(len(paths)))
        node.cover = next((p for p in paths if os.path.splitext(p.lower())[1] in PICTURE_EXTS), None)
        node.level = (kind, key)
        return node

    def go_back(self):
        if self.levels:
            self.show_level(self.levels.pop(), remember=False)

    def open_node(self, node):
        if node.kind in ("year", "month"):
            self.show_level(node.level)
        elif node.kind == "card":
            host.open_file(self.desktop, node.path)
        else:
            super().open_node(node)

    # ---- tiles ------------------------------------------------------------------------------------------------
    def want_thumb(self, node, callback=None):
        if node.kind in ("year", "month"):
            key = node.key
            if key in self.thumbs:
                return
            self.thumbs[key] = None
            cover = node.cover
            from PySide6.QtGui import QImage
            self.loader.request(key, (lambda: thumb(cover)) if cover else QImage)
            return
        if node.kind == "card":
            return
        super().want_thumb(node, callback)

    def paint_tile(self, item):
        node = item.data(Qt.UserRole)
        img = self.thumbs.get(node.key) if node.key in self.thumbs else None
        if node.kind in ("year", "month"):
            pm = _album_tile(node, img, self.tile)
        elif node.kind == "card":
            pm = _card_tile(node, self.tile)
        else:
            pm = _picture_tile(node, img, self.tile, video=node.kind == "video")
        item.setIcon(QIcon(pm))
        if node.kind in ("year", "month"):
            item.setToolTip(f"{node.name}\n{node.artist}")
            item.setText(node.artist)
        else:
            item.setToolTip(f"{node.path.name}\nTaken {node.artist}\nIn {node.path.parent.name}")

    def closeEvent(self, event):
        if getattr(self, "indexer", None) is not None:
            self.indexer.stopped = True
        super().closeEvent(event)


_open = {}


def open_camroll(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = CameraRollArchive(desktop)
        win = host.window(desktop, CameraRollArchive.TITLE, body, camroll_icon(), (900, 640))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.video.stop()
        if getattr(win.content, "indexer", None) is not None:
            win.content.indexer.stopped = True
