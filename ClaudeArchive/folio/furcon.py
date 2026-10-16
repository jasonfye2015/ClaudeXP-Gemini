"""Furry Con CD Viewer: the yearly convention recap discs on E: (Local Storage/Furry Media Archive.../FurCon CDs...).

The lobby is a wall of con badges on lanyards (name, year and a photo from that weekend, in the con's own colours),
grouped by convention and ordered by year. Opening a con lays the whole weekend out on one page like a scrapbook:
every photo first, then the videos, gathered from its sub-folders. Photos open in FurFolio's framed viewer, videos
in the built-in player (both shared with Fur CD Viewer)."""
import hashlib
import os
import re
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from shiboken6 import isValid

from comix.library import natural_key
from .cdviewer import CDViewer, listing
from .gallery import TILE, Node, piece_title
from claudecore import host

# Known conventions: (match, proper name, badge colour, accent).
CONS = [("anthrocon", "Anthrocon", "#1E4AA0", "#F2C230"),
        ("eurofurence", "Eurofurence", "#1E6A3A", "#F0E6C0"),
        ("furtherconfusion", "Further Confusion", "#7A1E5A", "#F2D060"),
        ("midwestfurfest", "Midwest FurFest", "#A04A10", "#FFE0A0")]


def con_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#1A2A6A"), 2))
    p.drawLine(9, 0, 13, 9)
    p.drawLine(23, 0, 19, 9)                                       # lanyard
    p.setPen(QPen(QColor("#202020"), 1))
    p.setBrush(QColor("#1E4AA0"))
    p.drawRoundedRect(QRectF(5.5, 8.5, 21, 22), 2, 2)
    p.setBrush(QColor("#F7F2E4"))
    p.drawRect(QRectF(9.5, 16.5, 13, 10))                           # photo window
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#C07040"))
    p.drawEllipse(QRectF(13, 18, 6, 6))
    p.setBrush(QColor("#F2C230"))
    p.drawRect(QRectF(6, 9, 20, 5))
    p.end()
    return QIcon(pm)


def cons_root():
    from archivepaths import archive_folder
    archive = archive_folder("mediaarchive")
    if archive is None:
        return None
    return next((d for d in sorted(archive.iterdir())
                 if d.is_dir() and re.sub(r"\W", "", d.name.lower()).startswith(("furcon", "conventioncd"))), None)


def con_info(folder_name):
    """'EuroFurence5 1999' -> ('Eurofurence', '5', '1999', colour, accent)."""
    flat = re.sub(r"[^a-z]", "", folder_name.lower())
    year = (re.findall(r"(?:19|20)\d\d", folder_name) or [""])[-1]
    edition = ""
    m = re.search(r"[a-z](\d{1,2})\b", folder_name.lower())
    if m and m.group(1) != year[-2:]:
        edition = m.group(1)
    for key, name, colour, accent in CONS:
        if flat.startswith(key) or key in flat:
            return name, edition, year, colour, accent
    name = re.sub(r"\s*(?:19|20)\d\d\s*", " ", folder_name).strip()
    h = int(hashlib.md5(name.encode()).hexdigest(), 16)
    colour = ["#2A4A8A", "#6A2A2A", "#2A6A5A", "#5A3A7A"][h % 4]
    return name, edition, year, colour, "#F0E0A0"


def gather(folder, limit=2000):
    """All photos then all videos in a con folder and its sub-folders, in order."""
    pics, vids = [], []
    stack = [folder]
    while stack and len(pics) < limit:
        f = stack.pop(0)
        dirs, p, v = listing(f)
        pics += [f / n for n in p]
        vids += [f / n for n in v]
        stack += [f / d for d in dirs]
    return pics, vids


def _badge(node, img, con):
    name, edition, year, colour, accent = con
    pm = QPixmap(TILE)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    W = TILE.width()
    badge = QRectF(26, 26, W - 52, TILE.height() - 30)
    strap = QColor(colour).darker(130)
    p.setPen(QPen(strap, 5, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(int(W / 2 - 34), 0, int(W / 2 - 8), int(badge.top() - 4))                # lanyard
    p.drawLine(int(W / 2 + 34), 0, int(W / 2 + 8), int(badge.top() - 4))
    p.setPen(QPen(QColor("#909090"), 2))
    p.setBrush(QColor("#C8C8C8"))
    p.drawRoundedRect(QRectF(W / 2 - 9, badge.top() - 9, 18, 12), 3, 3)                # clip
    p.fillRect(badge.translated(3, 4), QColor(0, 0, 0, 70))
    p.setPen(QPen(QColor("#303030"), 1))
    p.setBrush(QColor("#FBFAF4"))
    p.drawRoundedRect(badge, 4, 4)
    head = QRectF(badge.left(), badge.top(), badge.width(), 30)
    path = QPainterPath()
    path.addRoundedRect(head, 4, 4)
    p.fillPath(path, QColor(colour))
    p.fillRect(QRectF(head.left(), head.bottom() - 4, head.width(), 4), QColor(colour))
    p.setPen(QColor(accent))
    f = QFont("Arial Black", 8)
    p.setFont(f)
    title = name.upper() + (f" {edition}" if edition else "")
    fm = p.fontMetrics()
    if fm.horizontalAdvance(title) > head.width() - 8:
        p.setFont(QFont("Arial Black", 6))
    p.drawText(head.adjusted(4, 0, -4, 0), Qt.AlignCenter, title)
    photo = QRectF(badge.left() + 10, head.bottom() + 6, badge.width() - 20, badge.height() - 64)
    if img is not None and not img.isNull():
        scale = max(photo.width() / img.width(), photo.height() / img.height())
        sw, sh = photo.width() / scale, photo.height() / scale
        p.drawImage(photo, img, QRectF((img.width() - sw) / 2, (img.height() - sh) / 2, sw, sh))
    else:
        p.fillRect(photo, QColor("#E4E0D4"))
    p.setPen(QPen(QColor("#A0A0A0"), 1))
    p.setBrush(Qt.NoBrush)
    p.drawRect(photo)
    p.setPen(QColor(colour).darker(120))
    p.setFont(QFont("Arial Black", 14))
    p.drawText(QRectF(badge.left(), photo.bottom() + 2, badge.width(), badge.bottom() - photo.bottom() - 4),
               Qt.AlignCenter, year or "")
    p.end()
    return pm


class ConViewer(CDViewer):
    TITLE = "Furry Con CD Viewer"
    PLACE = "FurCon CDs"
    RACK = "All Cons"

    def find_root(self):
        return cons_root()

    def __init__(self, desktop):
        self.video_badges = {}                 # video path -> badge waiting for a still
        super().__init__(desktop)

    def show_rack(self):
        if self.root is None:
            return
        self._reset()
        self.history.clear()
        self.here = self.disc = None
        dirs, _p, _v = listing(self.root)
        nodes = []
        for d in dirs:
            name, edition, year, _c, _a = con_info(d)
            label = f"{name}{' ' + edition if edition else ''} {year}".strip()
            nodes.append(Node(self.root / d, "disc", label))
        nodes.sort(key=lambda n: (con_info(n.path.name)[0], natural_key(con_info(n.path.name)[2])))
        self._set_wall_look(True)
        self.wall.setStyleSheet("QListWidget { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #5A1E1E,"
                                " stop:1 #2A0E10); border: none; font: bold 11px Tahoma; color: #F4E8D0; }"
                                "QListWidget::item:selected { background: rgba(255,210,120,70); }")    # hotel carpet
        self.wall.fill(nodes)
        self.back_btn.setEnabled(False)
        self.where.setText(self.PLACE)
        self.status.setText(f"{len(nodes)} conventions")
        self.stack.setCurrentIndex(0)
        if self.frame is not None:
            self.frame.set_title(self.TITLE)

    def open_node(self, node):
        if node.kind == "disc":
            self.disc = node
            self.history = [None]
            self._reset()
            self.here = node.path
            pics, vids = gather(node.path)
            nodes = [Node(pth, "piece", piece_title(pth.name), node.name) for pth in pics]
            nodes += [Node(pth, "video", piece_title(pth.name), node.name) for pth in vids]
            self._set_wall_look(False)
            self.wall.fill(nodes)
            self.back_btn.setEnabled(True)
            self.where.setText(f"{self.PLACE}  ›  {node.name}")
            bits = [f"{len(pics)} photo{'s' if len(pics) != 1 else ''}" if pics else "",
                    f"{len(vids)} video{'s' if len(vids) != 1 else ''}" if vids else ""]
            self.status.setText(", ".join(b for b in bits if b) or "Nothing on this disc.")
            self.stack.setCurrentIndex(0)
            if self.frame is not None:
                self.frame.set_title(f"{node.name} - {self.TITLE}")
        else:
            super().open_node(node)

    def want_thumb(self, node, callback=None):
        if node.kind == "disc" and node.key not in self.thumbs:
            from .gallery import make_thumb
            path = node.path
            self.thumbs[node.key] = None

            def first_photo():
                pics, _v = gather(path, limit=12)
                for pth in pics[:8]:
                    img = make_thumb(pth)
                    if not img.isNull():
                        return img
                from PySide6.QtGui import QImage
                return QImage()
            self.loader.request(node.key, first_photo)
            return
        super().want_thumb(node, callback)

    def _thumb_loaded(self, key, img):
        if key.startswith("disc:") and img.isNull():
            _p, vids = gather(Path(key[5:]), limit=40)
            if vids:
                self.video_badges[str(vids[0])] = key
                self.grabber.request(vids[0])
        if key.startswith("video:") and key[6:] in self.video_badges:
            super()._thumb_loaded(self.video_badges.pop(key[6:]), img)
        super()._thumb_loaded(key, img)

    def paint_tile(self, item):
        node = item.data(Qt.UserRole)
        if node.kind == "disc":
            img = self.thumbs.get(node.key) if node.key in self.thumbs else None
            item.setIcon(QIcon(_badge(node, img, con_info(node.path.name))))
        else:
            super().paint_tile(item)


_open = {}


def open_furcon(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = ConViewer(desktop)
        win = host.window(desktop, ConViewer.TITLE, body, con_icon(), (840, 610))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.video.stop()
