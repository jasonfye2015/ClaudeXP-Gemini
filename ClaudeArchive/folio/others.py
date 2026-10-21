"""Other's Files Archive Viewer: files saved from other people over the years (Local Storage/Others Files
Archived), one folder per person.

Home is a shelf of everyone, an album each with a picture from inside on the cover (folders whose names differ
only by spaces, underscores, hyphens or capitals - '12 String' and '12string' - are one person). A person opens as
their folders, pictures, videos and writing together; Show picks Everything, Pictures, Videos or Text, and Sort
orders by name, date or type. Pictures open in FurFolio's framed viewer, videos in this computer's media player,
text, web pages, Word, WordPad and PDF files in the reading pane. Programs, sounds, archives and the rest are left
out. Built on the Personal Document Gallery (and so on Fur CD Viewer); nothing is indexed up front."""
import json
import os
import re
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QMenu, QToolButton
from shiboken6 import isValid

from comix.library import natural_key
from .cdviewer import VIDEO_EXTS, CDViewer
from .documents import DOC_EXTS, PICTURE_EXTS, SIZE, DocumentGallery, ReadingPane, folder_peek
from .gallery import Node
from claudecore import host

SETTINGS = host.data("others") / "settings.json"
SHOWS = {"all": "Everything", "pictures": "Pictures", "videos": "Videos", "text": "Text"}
SORTS = {"name": "Name", "date": "Date modified", "type": "Type"}
MOVIE_EXTS = VIDEO_EXTS | {".flv", ".webm"}
TEXT_EXTS = DOC_EXTS - {".xls", ".xlsx", ".ods", ".wks"}
SKIP_DIRS = {"thumbs", "thumbnails", "_vti_cnf", "_vti_pvt"}


def others_icon():
    """A little stack of folders with name tags."""
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    for i, colour in enumerate(("#C89030", "#E0A840", "#F4C860")):
        y = 6 + i * 6
        p.setPen(QPen(QColor("#8A6020"), 1))
        p.setBrush(QColor(colour))
        p.drawRoundedRect(QRectF(3.5 + i * 2, y - 2.5, 10, 4), 1.5, 1.5)
        p.drawRoundedRect(QRectF(3.5 + i * 2, y, 25 - i * 2, 16 - i * 2), 2, 2)
    p.setBrush(QColor("white"))
    p.drawRoundedRect(QRectF(13.5, 21.5, 14, 7), 1.5, 1.5)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#D8261C"))
    for x, y, r in ((20.5, 25.6, 1.6), (18.2, 23.6, 0.8), (19.8, 22.9, 0.8), (21.4, 22.9, 0.8), (23.0, 23.6, 0.8)):
        p.drawEllipse(QRectF(x - r, y - r, 2 * r, 2 * r))
    p.end()
    return QIcon(pm)


def others_root():
    root = host.local_storage()
    try:
        return next((d for d in sorted(root.iterdir()) if d.is_dir() and d.name.lower().startswith("others files")),
                    None)
    except OSError:
        return None


def person_key(name):
    """'12 String', '12string' and 'Black_Spirit' / 'Black Spirit' are the same person."""
    return re.sub(r"[\s_\-.]+", "", name).lower()


def kind_of(name):
    ext = os.path.splitext(name.lower())[1]
    if ext in PICTURE_EXTS:
        return "piece"
    if ext in MOVIE_EXTS:
        return "video"
    if ext in TEXT_EXTS:
        return "doc"
    return None


def listing(folder, show, sort):
    """([sub-folder paths], [(path, kind)], how many files are left out) for one folder."""
    dirs, files, skipped = [], [], 0
    try:
        with os.scandir(folder) as it:
            entries = list(it)
    except OSError:
        entries = []
    wanted = {"all": ("piece", "video", "doc"), "pictures": ("piece",), "videos": ("video",), "text": ("doc",)}[show]
    for e in entries:
        low = e.name.lower()
        if low.startswith(".") or low in ("thumbs.db", "desktop.ini"):
            continue
        try:
            is_dir = e.is_dir()
        except OSError:
            continue
        if is_dir:
            if low not in SKIP_DIRS and not low.endswith("_files"):
                dirs.append(e)
            continue
        kind = kind_of(e.name)
        if kind in wanted:
            files.append((e, kind))
        else:
            skipped += 1

    def when(entry):
        try:
            return -entry.stat().st_mtime
        except OSError:
            return 0
    if sort == "date":
        dirs.sort(key=when)
        files.sort(key=lambda f: when(f[0]))
    elif sort == "type":
        dirs.sort(key=lambda e: natural_key(e.name))
        files.sort(key=lambda f: ({"piece": 0, "video": 1, "doc": 2}[f[1]], natural_key(f[0].name)))
    else:
        dirs.sort(key=lambda e: natural_key(e.name))
        files.sort(key=lambda f: natural_key(f[0].name))
    return [Path(e.path) for e in dirs], [(Path(e.path), k) for e, k in files], skipped


class OthersArchive(DocumentGallery):
    TITLE = "Other's Files Archive Viewer"
    PLACE = "Others Files Archived"
    RACK = "Everyone"

    def find_root(self):
        return others_root()

    def __init__(self, desktop):
        try:
            saved = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            saved = {}
        self.show_mode = saved.get("show") if saved.get("show") in SHOWS else "all"
        self.sort_mode = saved.get("sort") if saved.get("sort") in SORTS else "name"
        self.merged = {}                          # a person's first folder -> all of their folders
        CDViewer.__init__(self, desktop)          # (the Document Gallery's own settings aren't ours)
        self.reading = ReadingPane(self)
        self.stack.addWidget(self.reading)
        if self.root is None:
            self.status.setText("Put an 'Others Files Archived' folder on drive E: (Local Storage).")

    def _bar(self):
        bar = CDViewer._bar(self)
        row = bar.layout()
        self.find.setPlaceholderText("Name")
        self.menu_actions = {}
        for title, options, attr in (("Show", SHOWS, "show_mode"), ("Sort", SORTS, "sort_mode")):
            button = QToolButton()
            button.setText(f"{title} ▾")
            button.setPopupMode(QToolButton.InstantPopup)
            menu = QMenu(button)
            menu.setStyleSheet(host.menu_style())
            for key, label in options.items():
                act = menu.addAction(label, lambda a=attr, k=key: self._choose(a, k))
                act.setCheckable(True)
                act.setChecked(getattr(self, attr) == key)
                self.menu_actions[(attr, key)] = act
            button.setMenu(menu)
            row.insertWidget(row.count() - 2, button)
        return bar

    def _choose(self, attr, key):
        setattr(self, attr, key)
        for (a, k), act in self.menu_actions.items():
            if a == attr:
                act.setChecked(k == key)
        try:
            SETTINGS.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS.write_text(json.dumps({"show": self.show_mode, "sort": self.sort_mode}), encoding="utf-8")
        except OSError:
            pass
        if self.here is not None:
            self.show_folder(self.here, remember=False)

    # ---- browsing ---------------------------------------------------------------------------------------------
    def show_rack(self):
        """Home: everyone, one album each (read afresh, so new people turn up)."""
        if self.root is None:
            return
        self._reset()
        self.history.clear()
        self.here = self.disc = None
        groups = {}
        try:
            folders = sorted((d for d in self.root.iterdir() if d.is_dir()), key=lambda d: natural_key(d.name))
        except OSError:
            folders = []
        for d in folders:
            groups.setdefault(person_key(d.name), []).append(d)
        self.merged = {g[0]: g for g in groups.values() if len(g) > 1}
        nodes = [Node(g[0], "user", g[0].name) for g in groups.values()]
        self._set_wall_look(True)
        self.wall.fill(nodes)
        self.back_btn.setEnabled(False)
        self.where.setText(self.PLACE)
        self.status.setText(f"{len(nodes)} people" + (f" ({len(folders)} folders)" if len(folders) != len(nodes) else ""))
        self.stack.setCurrentIndex(0)
        if self.frame is not None:
            self.frame.set_title(self.TITLE)

    def show_folder(self, path, remember=True):
        CDViewer.show_folder(self, path, remember)

    def folder_contents(self, path):
        folder = Path(path)
        dirs, files, skipped = [], [], 0
        for f in self.merged.get(folder, [folder]):            # a person under more than one spelling
            d, fl, s = listing(f, self.show_mode, self.sort_mode)
            dirs += d
            files += fl
            skipped += s
        nodes = [Node(d, "folder", d.name) for d in dirs]
        nodes += [Node(p, kind, p.name if kind == "doc" else p.stem) for p, kind in files]
        count = {k: sum(1 for _p, kk in files if kk == k) for k in ("piece", "video", "doc")}
        return folder, nodes, [("folder", len(dirs)), ("picture", count["piece"]), ("video", count["video"]),
                               ("document", count["doc"]), ("hidden item", skipped)]

    def crumbs(self, folder):
        try:
            return list(Path(folder).relative_to(self.root).parts)
        except ValueError:
            return [Path(folder).name]

    def open_node(self, node):
        if node.kind == "user":
            self.show_folder(node.path)
        elif node.kind == "video" and host.open_media(self.desktop, node.path):
            return                                        # this computer's media player plays it
        else:
            super().open_node(node)

    # ---- tiles ------------------------------------------------------------------------------------------------
    def want_thumb(self, node, callback=None):
        if node.kind == "video":
            CDViewer.want_thumb(self, node, callback)
            return
        if node.kind == "user":
            key = node.key
            if key in self.thumbs:
                return
            self.thumbs[key] = None
            folders = self.merged.get(node.path, [node.path])
            self.loader.request(key, lambda fs=folders: next((img for img in map(folder_peek, fs)
                                                              if not img.isNull()), folder_peek(fs[0])))
            return
        super().want_thumb(node, callback)

    def paint_tile(self, item):
        from .miscfurry import _album_tile, _picture_tile
        node = item.data(Qt.UserRole)
        img = self.thumbs.get(node.key) if node.key in self.thumbs else None
        if node.kind == "user":
            item.setIcon(QIcon(_album_tile(node, img, SIZE)))
            others = [d.name for d in self.merged.get(node.path, [])[1:]]
            item.setToolTip(node.name + (f"\n(also filed as {', '.join(others)})" if others else ""))
        elif node.kind == "video":
            item.setIcon(QIcon(_picture_tile(node, img, SIZE, video=True)))
        else:
            super().paint_tile(item)


_open = {}


def open_others(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = OthersArchive(desktop)
        win = host.window(desktop, OthersArchive.TITLE, body, others_icon(), (920, 640))
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
