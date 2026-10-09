"""Furry Video Browser: the video archive on E: (Local Storage/Furry Media Archive.../Video).

A gallery like Fur CD Viewer's (and built on it): folders as tiles with a peek inside, videos as film tiles with a
still from a few seconds in, pictures as thumbnails, and Shockwave Flash animations as Flash cards. The Flash movies
are never run just to make a thumbnail - there are far too many of them. Double-click to play: videos and sounds
open in ClaudeAmp, Flash in Macromedia Flash Player, pictures in FurFolio's framed viewer."""
import os
import re
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from shiboken6 import isValid

from ...wm import XPWindow
from ..comix.library import natural_key, nice_name
from .cdviewer import VIDEO_EXTS, CDViewer, listing
from .gallery import TILE, Node, piece_title

FLASH_EXTS = {".swf"}


def video_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#101010"), 1))
    p.setBrush(QColor("#2A2A2E"))
    p.drawRoundedRect(QRectF(1.5, 5.5, 29, 21), 2, 2)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#E8E8E8"))
    for x in range(4, 29, 5):                                       # sprocket holes
        p.drawRect(QRectF(x, 7, 2.5, 2.5))
        p.drawRect(QRectF(x, 22.5, 2.5, 2.5))
    g = QLinearGradient(0, 11, 0, 21)
    g.setColorAt(0, QColor("#6AA8F0"))
    g.setColorAt(1, QColor("#1E4A9A"))
    p.fillRect(QRectF(4, 11, 24, 10), g)
    p.setBrush(QColor("#E8261C"))                                   # a paw on the frame
    for x, y, r in ((16, 17.5, 2.6), (12.2, 14.2, 1.3), (14.6, 12.6, 1.3), (17.4, 12.6, 1.3), (19.8, 14.2, 1.3)):
        p.drawEllipse(QRectF(x - r, y - r, 2 * r, 2 * r))
    p.end()
    return QIcon(pm)


def videos_root():
    from .. import archive_folder
    archive = archive_folder("mediaarchive")
    if archive is None:
        return None
    return next((d for d in sorted(archive.iterdir()) if d.is_dir() and d.name.lower().startswith("video")), None)


def clean_title(name):
    """'1249280389.baddoganimations_commission.swf' -> 'Baddoganimations commission' (FA's upload stamps go)."""
    name = re.sub(r"^\d{9,11}\.", "", name)
    return piece_title(name)


def flash_files(folder):
    try:
        with os.scandir(folder) as it:
            names = [e.name for e in it if e.is_file() and os.path.splitext(e.name.lower())[1] in FLASH_EXTS]
    except OSError:
        names = []
    return sorted(names, key=natural_key)


def first_video(folder, budget=40):
    """A video somewhere near the top of a folder, for the folder tile's peek (breadth-first, a few folders)."""
    queue = [Path(folder)]
    while queue and budget > 0:
        budget -= 1
        f = queue.pop(0)
        dirs, _pics, vids = listing(f)
        for name in vids:
            if os.path.splitext(name.lower())[1] not in (".rm", ".ram"):
                return f / name
        queue += [f / d for d in dirs]
    return None


def first_flash(folder, budget=40):
    queue = [Path(folder)]
    while queue and budget > 0:
        budget -= 1
        f = queue.pop(0)
        if flash_files(f):
            return True
        queue += [f / d for d in listing(f)[0]]
    return False


def _flash_peek():
    """What pokes out of a folder of Flash movies: a little stage with the Flash badge."""
    from PySide6.QtGui import QImage
    img = QImage(150, 100, QImage.Format_ARGB32)
    img.fill(QColor("#F4F4F8"))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    badge = QRectF(51, 8, 48, 48)
    p.setPen(QPen(QColor("#7A0000"), 1))
    p.setBrush(QColor("#D8161C"))
    p.drawRoundedRect(badge, 9, 9)
    f = QPainterPath()
    x, y = badge.left(), badge.top()
    f.moveTo(x + 35, y + 11)
    f.cubicTo(x + 26, y + 9.5, x + 22.5, y + 14, x + 21.5, y + 22)
    f.lineTo(x + 19.5, y + 33)
    f.cubicTo(x + 18.5, y + 38.5, x + 16, y + 40, x + 12, y + 39)
    p.setPen(QPen(QColor("white"), 5, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawPath(f)
    p.drawLine(QPointF(x + 15.5, y + 23.5), QPointF(x + 30, y + 23.5))
    p.end()
    return img


def _flash_tile(node):
    """A Flash card: the red 'f' badge on a movie stage, with the file's name (nothing is run to draw it)."""
    pm = QPixmap(TILE)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    card = QRectF(16, 26, TILE.width() - 32, TILE.height() - 52)
    p.fillRect(card.translated(3, 4), QColor(0, 0, 0, 70))
    g = QLinearGradient(card.topLeft(), card.bottomRight())
    g.setColorAt(0, QColor("#FFFFFF"))
    g.setColorAt(1, QColor("#E2E4EC"))
    p.setPen(QPen(QColor("#9098A8"), 1))
    p.setBrush(g)
    p.drawRect(card)
    c = QPointF(card.center().x(), card.center().y() - 6)
    badge = QRectF(c.x() - 24, c.y() - 24, 48, 48)
    p.setPen(QPen(QColor("#7A0000"), 1))
    p.setBrush(QColor("#D8161C"))
    p.drawRoundedRect(badge, 9, 9)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 255, 255, 60))
    p.drawRoundedRect(QRectF(badge.left() + 3, badge.top() + 3, badge.width() - 6, 20), 7, 7)
    f = QPainterPath()
    x, y = badge.left(), badge.top()
    f.moveTo(x + 35, y + 11)
    f.cubicTo(x + 26, y + 9.5, x + 22.5, y + 14, x + 21.5, y + 22)
    f.lineTo(x + 19.5, y + 33)
    f.cubicTo(x + 18.5, y + 38.5, x + 16, y + 40, x + 12, y + 39)
    p.setPen(QPen(QColor("white"), 5, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawPath(f)
    p.drawLine(QPointF(x + 15.5, y + 23.5), QPointF(x + 30, y + 23.5))
    p.setPen(QColor("#505868"))
    p.setFont(QFont("Tahoma", 7, QFont.Bold))
    p.drawText(QRectF(card.left(), card.bottom() - 18, card.width(), 14), Qt.AlignCenter, "SHOCKWAVE FLASH")
    p.end()
    return pm


class VideoBrowser(CDViewer):
    TITLE = "Furry Video Browser"
    PLACE = "Video"
    RACK = "Video Home"

    def find_root(self):
        return videos_root()

    def __init__(self, desktop):
        self.folder_peeks = {}                 # first video path -> the folder tile waiting for its still
        super().__init__(desktop)
        if self.root is None:
            self.status.setText("Put the Furry Media Archive (with its Video folder) on drive E: (Local Storage).")

    # ---- browsing ---------------------------------------------------------------------------------------------
    def show_rack(self):
        """Home is the Video folder itself."""
        if self.root is None:
            return
        self.history.clear()
        self.here = self.disc = None
        self.show_folder(self.root, remember=False)
        self.back_btn.setEnabled(False)

    def folder_contents(self, path):
        folder = Path(path)
        dirs, pics, vids = listing(folder)
        from .cdviewer import extras
        sounds, archives = extras(folder)
        flash = flash_files(folder)
        nodes = [Node(folder / d, "folder", nice_name(d).lstrip("- ").strip() or d) for d in dirs]
        nodes += [Node(folder / n, "video", clean_title(n)) for n in vids]
        nodes += [Node(folder / n, "flash", clean_title(n)) for n in flash]
        nodes += [Node(folder / n, "piece", clean_title(n)) for n in pics]
        nodes += [Node(folder / n, "sound", clean_title(n)) for n in sounds]
        nodes += [Node(folder / n, "archive", n) for n in archives]
        return folder, nodes, [("folder", len(dirs)), ("video", len(vids)), ("Flash animation", len(flash)),
                               ("picture", len(pics)), ("sound", len(sounds)), ("archive", len(archives))]

    def crumbs(self, folder):
        try:
            return [nice_name(x).lstrip("- ").strip() or x for x in Path(folder).relative_to(self.root).parts]
        except ValueError:
            return self._archive_crumbs(folder)

    def open_node(self, node):
        if node.kind == "flash":
            from ..flash import open_flash
            open_flash(self.desktop, node.path)
            return
        if node.kind in ("video", "sound"):
            from ..amp import MEDIA_EXTS, open_amp
            if node.path.suffix.lower() in MEDIA_EXTS:
                open_amp(self.desktop, node.path)
                return
        super().open_node(node)

    # ---- tiles ------------------------------------------------------------------------------------------------
    def want_thumb(self, node, callback=None):
        if node.kind == "flash":
            return                                               # never run a movie just for a picture
        if node.kind == "folder" and callback is None and node.key not in self.thumbs:
            self.thumbs[node.key] = None
            path = node.path

            def peek():
                from .cdviewer import disc_cover
                return disc_cover(path)
            self.loader.request(node.key, peek)
            return
        super().want_thumb(node, callback)

    def _thumb_loaded(self, key, img):
        if key.startswith("folder:") and img.isNull():               # no pictures: a still from a video instead
            video = first_video(Path(key[7:]))
            if video is not None:
                self.folder_peeks.setdefault(str(video), []).append(key)
                self.grabber.request(video)
            elif first_flash(Path(key[7:])):
                img = _flash_peek()
        if key.startswith("video:"):
            for folder_key in self.folder_peeks.pop(key[6:], []):
                super()._thumb_loaded(folder_key, img)
        super()._thumb_loaded(key, img)

    def paint_tile(self, item):
        node = item.data(Qt.UserRole)
        if node.kind == "flash":
            item.setIcon(QIcon(_flash_tile(node)))
        else:
            super().paint_tile(item)


_open = {}


def open_videos(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = VideoBrowser(desktop)
        win = XPWindow(desktop, VideoBrowser.TITLE, body, video_icon(), (840, 610))
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
