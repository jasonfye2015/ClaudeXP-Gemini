"""Misc Furry Image Viewer: the numbered folders of assorted furry pictures on E:
(Local Storage/Furry Media Archive.../Misc Furry Images/Misc Furry Images 001, 002, ...).

Home is a shelf of numbered albums, each with a peek at a picture inside; it's read afresh every time, so new
numbered folders turn up as soon as they're added. An album opens as a wall of thumbnails - pictures, and videos as
film tiles with a still - in two sizes (Thumbnails or Extra Large Thumbnails, remembered). Anything else in the
folders (text, Flash, odd files) is left out. Pictures open in FurFolio's framed viewer with its slideshow; videos
play in this computer's media player.

Nothing is indexed up front: a folder is listed when it's opened, and thumbnails are made only as they scroll into
view, then cached (data/miscfurry)."""
import hashlib
import json
import os
import re
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QImageReader, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QMenu, QToolButton
from shiboken6 import isValid

from comix.library import natural_key, nice_name
from .cdviewer import SKIP_DIRS, VIDEO_EXTS, CDViewer
from .gallery import Node
from claudecore import host

DATA = host.data("miscfurry")
THUMBS = DATA / "thumbs"
SETTINGS = DATA / "settings.json"
PICTURE_EXTS = {".jpg", ".jpeg", ".jpe", ".jfif", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}
MOVIE_EXTS = VIDEO_EXTS | {".webm"}
STORED = 300                                   # cached thumbnails fit this
SIZES = {"thumbnails": 150, "xlthumbs": 300}
LABELS = {"thumbnails": "Thumbnails", "xlthumbs": "Extra Large Thumbnails"}


def misc_icon():
    """A little album with a red paw on its cover."""
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#3A1E08"), 1))
    p.setBrush(QColor("#F4EEDC"))
    p.drawRect(QRectF(7.5, 3.5, 21, 25))                           # pages
    g = QLinearGradient(0, 2, 0, 30)
    g.setColorAt(0, QColor("#A0522D"))
    g.setColorAt(1, QColor("#5E2C10"))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(3.5, 2.5, 22, 27), 2, 2)              # cover
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 60))
    p.drawRect(QRectF(5, 3, 2.5, 26))                              # spine
    p.setBrush(QColor("#F8F0D8"))
    p.drawRect(QRectF(9.5, 7.5, 13, 13))                           # label
    p.setBrush(QColor("#D8261C"))
    for x, y, r in ((16, 16, 2.6), (12.4, 12.6, 1.3), (14.8, 11, 1.3), (17.2, 11, 1.3), (19.6, 12.6, 1.3)):
        p.drawEllipse(QRectF(x - r, y - r, 2 * r, 2 * r))
    p.end()
    return QIcon(pm)


def misc_root():
    """Furry Media Archive/Misc Furry Images, or None."""
    from archivepaths import archive_folder
    archive = archive_folder("mediaarchive")
    if archive is None:
        return None
    return next((d for d in sorted(archive.iterdir()) if d.is_dir() and d.name.lower().startswith("misc furry")),
                None)


def album_name(name):
    """'Misc Furry Images 042' -> 'No. 042' (any other folder name is kept)."""
    m = re.search(r"(\d+)\s*$", name)
    return f"No. {m.group(1)}" if m else nice_name(name)


def listing(folder):
    """(sub-folders, pictures, videos) in a folder, names only; everything else is ignored."""
    dirs, pics, vids = [], [], []
    try:
        with os.scandir(folder) as it:
            for e in it:
                low = e.name.lower()
                if low.startswith(".") or low in ("thumbs.db", "desktop.ini"):
                    continue
                if e.is_dir():
                    if low not in SKIP_DIRS:
                        dirs.append(e.name)
                    continue
                ext = os.path.splitext(low)[1]
                if ext in PICTURE_EXTS:
                    pics.append(e.name)
                elif ext in MOVIE_EXTS:
                    vids.append(e.name)
    except OSError:
        pass
    return sorted(dirs, key=natural_key), sorted(pics, key=natural_key), sorted(vids, key=natural_key)


# ---- thumbnails (worker threads) -------------------------------------------------------------------------------
def thumb(path):
    """The picture fitted into STORED x STORED, cached; a null QImage if it can't be read."""
    try:
        st = os.stat(path)
    except OSError:
        return QImage()
    f = THUMBS / (hashlib.sha1(f"{path}|{int(st.st_mtime)}|{st.st_size}".encode()).hexdigest()[:20] + ".jpg")
    if f.exists():
        img = QImage(str(f))
        if not img.isNull():
            return img
    reader = QImageReader(str(path))
    reader.setDecideFormatFromContent(True)
    reader.setAutoTransform(True)
    full = reader.size()
    if full.isValid() and (full.width() > STORED or full.height() > STORED):
        reader.setScaledSize(full.scaled(STORED, STORED, Qt.KeepAspectRatio))
    img = reader.read()
    if img.isNull():
        return img
    if img.width() > STORED or img.height() > STORED:
        img = img.scaled(STORED, STORED, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    flat = QImage(img.size(), QImage.Format_RGB32)               # transparent pictures on white
    flat.fill(Qt.white)
    p = QPainter(flat)
    p.drawImage(0, 0, img)
    p.end()
    try:
        THUMBS.mkdir(parents=True, exist_ok=True)
        flat.save(str(f), "JPG", 88)
    except OSError:
        pass
    return flat


def peek(folder, budget=12):
    """A thumbnail of the first picture in a folder (looking a little way into its sub-folders)."""
    queue = [Path(folder)]
    while queue and budget > 0:
        budget -= 1
        here = queue.pop(0)
        dirs, pics, _vids = listing(here)
        for name in pics[:3]:
            img = thumb(here / name)
            if not img.isNull():
                return img
        queue += [here / d for d in dirs]
    return QImage()


def _load_settings():
    try:
        data = json.loads(SETTINGS.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


# ---- tiles -----------------------------------------------------------------------------------------------------
def _fit(img, w, h):
    s = min(w / img.width(), h / img.height(), 2.0)              # little pictures grow at most 2x
    return img.width() * s, img.height() * s


def _album_tile(node, img, size):
    """A numbered album on the shelf: a leather cover with a print on it and the number on a label."""
    t = size + 20
    pm = QPixmap(t, t)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    k = size / 150
    cover = QRectF(14 * k, 6 * k, t - 28 * k, t - 12 * k)
    p.fillRect(cover.translated(3, 4), QColor(0, 0, 0, 80))
    p.setPen(QPen(QColor("#F4EEDC"), 1))
    p.setBrush(QColor("#F4EEDC"))
    p.drawRect(cover.adjusted(6 * k, 3 * k, 3 * k, -3 * k))                       # page edges
    g = QLinearGradient(cover.topLeft(), cover.bottomRight())
    g.setColorAt(0, QColor("#8E4A24"))
    g.setColorAt(1, QColor("#4E2410"))
    p.setPen(QPen(QColor("#2A1206"), 1))
    p.setBrush(g)
    p.drawRoundedRect(cover, 4 * k, 4 * k)
    p.fillRect(QRectF(cover.left() + 3 * k, cover.top(), 6 * k, cover.height()), QColor(0, 0, 0, 55))   # spine
    room = QRectF(cover.left() + 18 * k, cover.top() + 12 * k, cover.width() - 30 * k, cover.height() - 52 * k)
    if img is not None and not img.isNull():
        w, h = _fit(img, room.width(), room.height())
        r = QRectF(room.center().x() - w / 2, room.center().y() - h / 2, w, h)
        p.fillRect(r.adjusted(-4 * k, -4 * k, 4 * k, 4 * k), QColor("#F8F2E2"))
        p.drawImage(r, img)
    else:
        p.fillRect(room.adjusted(10 * k, 10 * k, -10 * k, -10 * k), QColor(255, 255, 255, 30))
    label = QRectF(cover.left() + 22 * k, cover.bottom() - 34 * k, cover.width() - 38 * k, 24 * k)
    p.setPen(QPen(QColor("#B89A60"), 1))
    p.setBrush(QColor("#F6EBCB"))
    p.drawRoundedRect(label, 3 * k, 3 * k)
    p.setPen(QColor("#3A2410"))
    p.setFont(QFont("Georgia", max(7, int(11 * k)), QFont.Bold))
    p.drawText(label, Qt.AlignCenter, p.fontMetrics().elidedText(node.name, Qt.ElideRight, int(label.width() - 6)))
    p.end()
    return pm


def _picture_tile(node, img, size, video=False):
    """A picture (or a video's still) in a white frame; videos get sprocket edges and a play badge."""
    t = size + 20
    pm = QPixmap(t, t)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    has = img is not None and not img.isNull()
    room = QRectF(10, 6, size, size - 4)
    w, h = _fit(img, room.width() - 12, room.height() - 12) if has else (size * 0.7, size * 0.55)
    r = QRectF(room.center().x() - w / 2, room.center().y() - h / 2, w, h)
    mat = r.adjusted(-6, -6, 6, 6)
    if video:
        mat = r.adjusted(-6, -13, 6, 13)
        p.fillRect(mat.translated(3, 4), QColor(0, 0, 0, 70))
        p.fillRect(mat, QColor("#1C1C20"))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#E8E8E8"))
        x = mat.left() + 4
        while x < mat.right() - 6:
            p.drawRect(QRectF(x, mat.top() + 3, 5, 5))
            p.drawRect(QRectF(x, mat.bottom() - 8, 5, 5))
            x += 10
    else:
        p.fillRect(mat.translated(3, 4), QColor(0, 0, 0, 60))
        p.setPen(QPen(QColor("#B8B0A0"), 1))
        p.setBrush(QColor("white"))
        p.drawRect(mat)
    if has:
        p.drawImage(r, img)
    else:
        p.fillRect(r, QColor("#3A3A40") if video else QColor("#ECE8DC"))
        p.setPen(QColor("#A09880"))
        p.setFont(QFont("Tahoma", 8))
        p.drawText(r, Qt.AlignCenter, "Loading..." if img is None else "")
    if video:
        c = r.center()
        p.setPen(QPen(QColor(255, 255, 255, 220), 2))
        p.setBrush(QColor(0, 0, 0, 120))
        p.drawEllipse(c, 15, 15)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("white"))
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QPolygonF
        p.drawPolygon(QPolygonF([QPointF(c.x() - 5, c.y() - 8), QPointF(c.x() - 5, c.y() + 8),
                                 QPointF(c.x() + 9, c.y())]))
    p.end()
    return pm


def _folder_tile(node, img, size):
    """A sub-folder: a manila folder with a peek at a picture sticking out."""
    t = size + 20
    pm = QPixmap(t, t)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    k = size / 150
    back = QRectF(14 * k, 24 * k, t - 28 * k, t - 44 * k)
    p.setPen(QPen(QColor("#B08A30"), 1))
    p.setBrush(QColor("#E2B850"))
    p.drawRoundedRect(QRectF(back.left(), back.top() - 10 * k, 50 * k, 16 * k), 3 * k, 3 * k)
    p.drawRoundedRect(back, 3 * k, 3 * k)
    if img is not None and not img.isNull():
        w, h = _fit(img, back.width() - 24 * k, back.height() - 10 * k)
        r = QRectF(back.center().x() - w / 2, back.top() - 6 * k, w, h)
        p.fillRect(r.adjusted(-3, -3, 3, 3), QColor("white"))
        p.drawImage(r, img)
    front = QRectF(back.left(), back.top() + back.height() * 0.42, back.width(), back.height() * 0.62)
    g = QLinearGradient(front.topLeft(), front.bottomLeft())
    g.setColorAt(0, QColor("#FCE7A0"))
    g.setColorAt(1, QColor("#EDC254"))
    p.setPen(QPen(QColor("#B08A30"), 1))
    p.setBrush(g)
    p.drawRoundedRect(front, 3 * k, 3 * k)
    p.end()
    return pm


# ---- the program -----------------------------------------------------------------------------------------------
class MiscFurryViewer(CDViewer):
    TITLE = "Misc Furry Image Viewer"
    PLACE = "Misc Furry Images"
    RACK = "All Albums"

    def find_root(self):
        return misc_root()

    def __init__(self, desktop):
        mode = _load_settings().get("view")
        self.view = mode if mode in SIZES else "thumbnails"
        self.tile = SIZES[self.view]
        super().__init__(desktop)
        self.viewer.fav_btn.hide()
        self._apply_size()
        if self.root is None:
            self.status.setText("Put the Furry Media Archive (with its Misc Furry Images folder) on drive E: "
                                "(Local Storage).")

    def _bar(self):
        bar = super()._bar()
        row = bar.layout()
        views = QToolButton()
        views.setText("Views ▾")
        views.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(views)
        menu.setStyleSheet(host.menu_style())
        self.view_actions = {}
        for mode in SIZES:
            act = menu.addAction(LABELS[mode], lambda m=mode: self.set_view(m))
            act.setCheckable(True)
            self.view_actions[mode] = act
        views.setMenu(menu)
        row.insertWidget(row.count() - 2, views)        # before 'Find:'
        return bar

    def set_view(self, mode):
        self.view, self.tile = mode, SIZES[mode]
        try:
            SETTINGS.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS.write_text(json.dumps({"view": mode}), encoding="utf-8")
        except OSError:
            pass
        self._apply_size()
        for i in range(self.wall.count()):
            self.paint_tile(self.wall.item(i))
        self.wall._timer.start()

    def _apply_size(self):
        t = self.tile + 20
        self.wall.setIconSize(QSize(t, t))
        self.wall.setGridSize(QSize(t + 16, t + 34))
        for mode, act in getattr(self, "view_actions", {}).items():
            act.setChecked(mode == self.view)

    # ---- browsing ---------------------------------------------------------------------------------------------
    def show_rack(self):
        """Home: every numbered album, read afresh so new ones appear."""
        if self.root is None:
            return
        self._reset()
        self.history.clear()
        self.here = self.disc = None
        dirs, _p, _v = listing(self.root)
        nodes = [Node(self.root / d, "album", album_name(d)) for d in dirs]
        self._set_wall_look(True)
        self.wall.fill(nodes)
        self.back_btn.setEnabled(False)
        self.where.setText(self.PLACE)
        self.status.setText(f"{len(nodes)} albums")
        self.stack.setCurrentIndex(0)
        if self.frame is not None:
            self.frame.set_title(self.TITLE)

    def folder_contents(self, path):
        folder = Path(path)
        dirs, pics, vids = listing(folder)
        nodes = [Node(folder / d, "folder", nice_name(d)) for d in dirs]
        nodes += [Node(folder / n, "piece", Path(n).stem) for n in pics]
        nodes += [Node(folder / n, "video", Path(n).stem) for n in vids]
        return folder, nodes, [("folder", len(dirs)), ("picture", len(pics)), ("video", len(vids))]

    def crumbs(self, folder):
        try:
            parts = list(Path(folder).relative_to(self.root).parts)
        except ValueError:
            return [nice_name(Path(folder).name)]
        return [album_name(parts[0])] + [nice_name(x) for x in parts[1:]] if parts else []

    def open_node(self, node):
        if node.kind == "album":
            self.history.clear()
            self.here = None
            self.show_folder(node.path, remember=True)
        elif node.kind == "video" and host.open_media(self.desktop, node.path):
            return                                       # this computer's media player plays it
        else:
            super().open_node(node)

    # ---- tiles ------------------------------------------------------------------------------------------------
    def want_thumb(self, node, callback=None):
        if node.kind == "video":
            super().want_thumb(node, callback)
            return
        key = node.key
        if callback is not None:
            if self.thumbs.get(key) is not None:
                callback(self.thumbs[key])
                return
            self.waiting.setdefault(key, []).append(callback)
        if key in self.thumbs:
            return
        self.thumbs[key] = None
        path = node.path
        job = (lambda: peek(path)) if node.kind in ("album", "folder") else (lambda: thumb(path))
        self.loader.request(key, job)

    def paint_tile(self, item):
        node = item.data(Qt.UserRole)
        img = self.thumbs.get(node.key) if node.key in self.thumbs else None
        if node.kind == "album":
            pm = _album_tile(node, img, self.tile)
        elif node.kind == "folder":
            pm = _folder_tile(node, img, self.tile)
        else:
            pm = _picture_tile(node, img, self.tile, video=node.kind == "video")
        item.setIcon(QIcon(pm))


_open = {}


def open_miscfurry(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = MiscFurryViewer(desktop)
        win = host.window(desktop, MiscFurryViewer.TITLE, body, misc_icon(), (900, 640))
        body.frame = win
        _open["win"] = win
        if body.root is not None:
            body.show_rack()
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.video.stop()
