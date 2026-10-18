"""Personal Image Gallery: the user's own pictures on E: (Local Storage/Misc Personal Image Folders).

Built on the Furry Video Browser (and so on Fur CD Viewer): folders as tiles with a peek at a picture inside, pictures
as thumbnails, videos as film tiles with a still, Flash movies as Flash cards. Double-click a picture for FurFolio's
framed viewer (with its slideshow); videos and sounds play in this computer's media player.

The folders are personal and mostly unsorted, so nothing is hidden for looking like a thumbnail, and Targa (.tga)
pictures are shown too. Camera RAW and Paint Shop Pro files can't be drawn: the status bar counts them, and the
folder itself (in My Computer) still has them."""
import os
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from shiboken6 import isValid

from comix.library import natural_key, nice_name
from .cdviewer import SHOW_IMAGES, SKIP_DIRS, VIDEO_EXTS, extras
from .gallery import Node
from .videos import VideoBrowser, clean_title, flash_files
from claudecore import host

PICTURE_EXTS = SHOW_IMAGES | {".tga", ".ico"}
CANT_SHOW = {".cr2", ".nef", ".arw", ".dng", ".raw", ".pspimage", ".psp", ".psd", ".xcf"}


def photos_icon():
    """A little stack of snapshots, the top one with a red paw."""
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    for angle, dx, fill in ((-14, -2, "#E8E4D8"), (9, 2, "#F2EFE6")):
        p.save()
        p.translate(16 + dx, 17)
        p.rotate(angle)
        p.setPen(QPen(QColor("#7A7468"), 1))
        p.setBrush(QColor(fill))
        p.drawRect(QRectF(-11, -11, 22, 22))
        p.restore()
    p.setPen(QPen(QColor("#6A6458"), 1))
    p.setBrush(QColor("#FFFFFF"))
    p.drawRect(QRectF(5.5, 4.5, 21, 23))
    p.setPen(Qt.NoPen)
    p.fillRect(QRectF(7.5, 6.5, 17, 14), QColor("#5C9AE0"))
    p.fillRect(QRectF(7.5, 15.5, 17, 5), QColor("#4E9A3C"))
    p.setBrush(QColor("#E8261C"))
    for x, y, r in ((16, 13.5, 2.4), (12.6, 10.4, 1.2), (14.8, 9, 1.2), (17.2, 9, 1.2), (19.4, 10.4, 1.2)):
        p.drawEllipse(QRectF(x - r, y - r, 2 * r, 2 * r))
    p.end()
    return QIcon(pm)


def photos_root():
    from archivepaths import archive_folder
    return archive_folder("miscimages")


def photo_listing(folder):
    """(sub-folders, pictures, videos, how many files can't be shown) in a folder (names only)."""
    dirs, pics, vids, cant = [], [], [], 0
    try:
        with os.scandir(folder) as it:
            for e in it:
                name = e.name
                low = name.lower()
                if low.startswith(".") or low in ("thumbs.db", "desktop.ini"):
                    continue
                ext = os.path.splitext(low)[1]
                if e.is_dir():
                    if low not in SKIP_DIRS:
                        dirs.append(name)
                elif ext in PICTURE_EXTS:
                    pics.append(name)
                elif ext in VIDEO_EXTS:
                    vids.append(name)
                elif ext in CANT_SHOW:
                    cant += 1
    except OSError:
        pass
    return sorted(dirs, key=natural_key), sorted(pics, key=natural_key), sorted(vids, key=natural_key), cant


class PhotoGallery(VideoBrowser):
    TITLE = "Personal Image Gallery"
    PLACE = "Misc Personal Image Folders"
    RACK = "Gallery Home"

    def find_root(self):
        return photos_root()

    def __init__(self, desktop):
        super().__init__(desktop)
        if self.root is None:
            self.status.setText("Put a 'Misc Personal Image Folders' folder on drive E: (Local Storage).")

    def folder_contents(self, path):
        folder = Path(path)
        dirs, pics, vids, cant = photo_listing(folder)
        sounds, archives = extras(folder)
        flash = flash_files(folder)
        nodes = [Node(folder / d, "folder", nice_name(d).lstrip("- ").strip() or d) for d in dirs]
        nodes += [Node(folder / n, "piece", clean_title(n)) for n in pics]
        nodes += [Node(folder / n, "video", clean_title(n)) for n in vids]
        nodes += [Node(folder / n, "flash", clean_title(n)) for n in flash]
        nodes += [Node(folder / n, "sound", clean_title(n)) for n in sounds]
        nodes += [Node(folder / n, "archive", n) for n in archives]
        return folder, nodes, [("folder", len(dirs)), ("picture", len(pics)), ("video", len(vids)),
                               ("Flash animation", len(flash)), ("sound", len(sounds)), ("archive", len(archives)),
                               ("unviewable RAW/PSP file", cant)]


_open = {}


def open_photos(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = PhotoGallery(desktop)
        win = host.window(desktop, PhotoGallery.TITLE, body, photos_icon(), (860, 620))
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
