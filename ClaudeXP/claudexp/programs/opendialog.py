"""A small XP-style Open dialog for the media players: a Look in list of places, then folders you can walk into and
the files of the wanted types. open_dialog(desktop, title, exts, on_open, icon=None, start=None)."""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QLabel, QListWidget, QListWidgetItem, QStyle,
                               QWidget)

from .comix.library import natural_key


def places():
    from ..explorer import vfs
    from . import archive_folder
    out = [("My Documents", vfs.user_home() / "My Documents"), ("Desktop", vfs.user_home() / "Desktop"),
           ("My Music", vfs.my_music()), ("External Drive (E:)", vfs.local_storage())]
    archive = archive_folder("mediaarchive")
    if archive is not None:
        video = next((d for d in sorted(archive.iterdir()) if d.is_dir() and d.name.lower().startswith("video")), None)
        if video is not None:
            out.append(("Video", video))
    return [(label, folder) for label, folder in out if folder.is_dir()]


def open_dialog(desktop, title, exts, on_open, icon=None, start=None):
    from .paint import _dialog
    body = QWidget()
    g = QGridLayout(body)
    g.setContentsMargins(0, 0, 0, 0)
    where = QComboBox()
    style = QApplication.style()
    for label, folder in places():
        where.addItem(style.standardIcon(QStyle.SP_DirIcon), label, str(folder))
    g.addWidget(QLabel("Look in:"), 0, 0)
    g.addWidget(where, 0, 1)
    files = QListWidget()
    files.setMinimumSize(420, 240)
    files.setStyleSheet("QListWidget { background: white; color: black; font: 11px Tahoma; }")
    g.addWidget(files, 1, 0, 1, 2)
    state = {"folder": Path(start) if start else None}

    def show(folder):
        state["folder"] = folder = Path(folder)
        files.clear()
        top = Path(where.currentData()) if where.currentData() else None
        if top is not None and folder != top and top in folder.parents:
            up = QListWidgetItem(style.standardIcon(QStyle.SP_FileDialogToParent), "..")
            up.setData(Qt.UserRole, ("dir", str(folder.parent)))
            files.addItem(up)
        try:
            entries = sorted(folder.iterdir(), key=lambda p: natural_key(p.name))
        except OSError:
            entries = []
        for p in entries:
            if p.is_dir() and not p.name.startswith("."):
                item = QListWidgetItem(style.standardIcon(QStyle.SP_DirIcon), p.name)
                item.setData(Qt.UserRole, ("dir", str(p)))
                files.addItem(item)
        for p in entries:
            if p.is_file() and p.suffix.lower() in exts:
                item = QListWidgetItem(style.standardIcon(QStyle.SP_FileIcon), p.name)
                item.setData(Qt.UserRole, ("file", str(p)))
                files.addItem(item)

    where.currentIndexChanged.connect(lambda _i: show(where.currentData()))
    if state["folder"] is not None and state["folder"].is_dir():
        for i in range(where.count()):
            if Path(where.itemData(i)) in (state["folder"], *state["folder"].parents):
                where.blockSignals(True)
                where.setCurrentIndex(i)
                where.blockSignals(False)
                break
        show(state["folder"])
    elif where.count():
        show(where.currentData())

    def accept():
        item = files.currentItem()
        if item is None:
            return False
        kind, path = item.data(Qt.UserRole)
        if kind == "dir":
            show(path)
            return False
        on_open(Path(path))

    win = _dialog(desktop, title, body, accept)
    if icon is not None:
        win.icon = icon

    def double(item):
        if accept() is not False:
            desktop.close_window(win)
    files.itemDoubleClicked.connect(double)
    return win
