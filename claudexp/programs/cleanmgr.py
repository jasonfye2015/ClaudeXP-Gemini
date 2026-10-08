"""Disk Cleanup for (C:): it 'calculates' for a moment, then lists what can go, with real sizes: the Recycle Bin,
temporary files in C:\\WINDOWS\\Temp, Temporary Internet Files (Netscape's page cache), plus XP's ever-present
'Compress old files' and 'Catalog files for the Content Indexer'. OK asks "Are you sure?" and then really cleans
the ticked items."""
import random
import shutil

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QProgressBar, QPushButton, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import sound


def cleanup_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#505050"), 1))
    p.setBrush(QColor("#C8C8C8"))
    p.drawRoundedRect(QRectF(3.5, 16.5, 24, 10), 2, 2)
    p.setBrush(QColor("#40C040"))
    p.drawEllipse(QRectF(21, 20, 3, 3))
    p.setPen(QPen(QColor("#8B5A2B"), 2.5))
    p.drawLine(27, 3, 17, 15)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#E0B040"))
    p.drawPolygon(QPolygonF([QPointF(14, 12), QPointF(20, 15), QPointF(18, 22), QPointF(9, 18)]))
    p.end()
    return QIcon(pm)


def _size(path):
    if path is None or not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def _items():
    """(key, label, bytes, description, ticked)"""
    from ..explorer import vfs
    from .navigator import web
    recycle = sum(_size(p) for p in vfs.RECYCLE_DIR.iterdir() if p.name != "INFO.json") if vfs.RECYCLE_DIR.exists() else 0
    temp = _size(vfs.DRIVE_C / "WINDOWS" / "Temp")
    cache_dir = getattr(web, "CACHE_DIR", None)
    cache = _size(cache_dir)
    return [("downloaded", "Downloaded Program Files", 0,
             "Downloaded Program Files are ActiveX controls and Java applets downloaded automatically from the "
             "Internet when you view certain pages.", True),
            ("internet", "Temporary Internet Files", cache,
             "The Temporary Internet Files folder contains Web pages stored on your hard disk for quick viewing. "
             "Netscape will download them again the next time you visit.", True),
            ("recycle", "Recycle Bin", recycle,
             "The Recycle Bin contains files you have deleted from your computer. These files are not permanently "
             "removed until you empty the Recycle Bin.", False),
            ("temp", "Temporary files", temp,
             "Programs sometimes store temporary information in a TEMP folder. Before a program closes, it usually "
             "deletes this information.", False),
            ("compress", "Compress old files", random.randint(20, 90) * 1024 * 1024,
             "Windows can compress files that you haven't used in a while. Compressing files saves disk space while "
             "still enabling you to access them.", False),
            ("catalog", "Catalog files for the Content Indexer", 0,
             "The Indexing service speeds up and improves file searches by maintaining an index of the files on "
             "the disk.", False)]


def _clean(key):
    from ..explorer import vfs
    from .navigator import web
    if key == "recycle":
        vfs.empty_recycle_bin()
    elif key == "temp":
        temp = vfs.DRIVE_C / "WINDOWS" / "Temp"
        if temp.exists():
            for p in temp.iterdir():
                shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    elif key == "internet":
        cache_dir = getattr(web, "CACHE_DIR", None)
        if cache_dir is not None and cache_dir.exists():
            for p in cache_dir.iterdir():
                if p.is_file():
                    p.unlink(missing_ok=True)


def open_cleanup(desktop):
    from ..network import DialogBody, _fixed_window
    from ..explorer.dialogs import msgbox, size_text
    from ..explorer import vfs
    body = DialogBody()
    v = QVBoxLayout(body)
    v.setContentsMargins(14, 12, 14, 12)
    note = QLabel("Disk Cleanup is calculating how much space you will be able to free on (C:). "
                  "This may take a few minutes to complete.")
    note.setWordWrap(True)
    v.addWidget(note)
    bar = QProgressBar()
    bar.setRange(0, 100)
    bar.setTextVisible(False)
    v.addWidget(bar)
    scanning = QLabel("Scanning:")
    v.addWidget(scanning)
    body.setFixedWidth(380)
    holder = {}

    def close():
        w = holder.pop("win", None)
        if w is not None and isValid(w):
            desktop.close_window(w)

    holder["win"] = _fixed_window(desktop, "Disk Cleanup", body, close)
    holder["win"].icon = cleanup_icon()
    desktop.open_window(holder["win"])
    steps = ["Compress old files", "Downloaded Program Files", "Temporary Internet Files", "Recycle Bin",
             "Temporary files", "Catalog files for the Content Indexer"]
    state = {"i": 0}

    def tick():
        if not isValid(bar):
            return
        state["i"] += 1
        bar.setValue(min(100, state["i"] * 4))
        scanning.setText(f"Scanning:  {steps[min(len(steps) - 1, state['i'] // 5)]}")
        if state["i"] < 25:
            QTimer.singleShot(120, tick)
        else:
            close()
            _results(desktop, size_text, msgbox, vfs)
    QTimer.singleShot(150, tick)


def _results(desktop, size_text, msgbox, vfs):
    from ..network import DialogBody, _fixed_window
    items = _items()
    usage = vfs.drive("C").usage()
    body = DialogBody()
    v = QVBoxLayout(body)
    v.setContentsMargins(14, 12, 14, 12)
    total = sum(i[2] for i in items)
    head = QLabel(f"You can use Disk Cleanup to free up to {size_text(total)} of disk space on (C:).")
    head.setWordWrap(True)
    v.addWidget(head)
    v.addWidget(QLabel("Files to delete:"))
    tree = QTreeWidget()
    tree.setHeaderHidden(True)
    tree.setRootIsDecorated(False)
    tree.setColumnCount(2)
    tree.setFixedHeight(130)
    for key, label, size, desc, ticked in items:
        item = QTreeWidgetItem([label, size_text(size) if size else "0 KB"])
        item.setCheckState(0, Qt.Checked if ticked else Qt.Unchecked)
        item.setData(0, Qt.UserRole, (key, desc, size))
        item.setTextAlignment(1, Qt.AlignRight)
        tree.addTopLevelItem(item)
    tree.setColumnWidth(0, 260)
    v.addWidget(tree)
    gained = QLabel()
    v.addWidget(gained)
    desc = QLabel()
    desc.setWordWrap(True)
    desc.setFixedHeight(60)
    v.addWidget(desc)
    row = QHBoxLayout()
    row.addStretch()
    ok, cancel = QPushButton("OK"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(75, 23)
        row.addWidget(b)
    v.addLayout(row)
    body.setFixedWidth(420)
    holder = {}

    def update():
        amount = sum(tree.topLevelItem(i).data(0, Qt.UserRole)[2] for i in range(tree.topLevelItemCount())
                     if tree.topLevelItem(i).checkState(0) == Qt.Checked)
        gained.setText(f"Total amount of disk space you gain:   {size_text(amount) if amount else '0 KB'}")
        item = tree.currentItem() or tree.topLevelItem(0)
        desc.setText(item.data(0, Qt.UserRole)[1])

    def close():
        w = holder.pop("win", None)
        if w is not None and isValid(w):
            desktop.close_window(w)

    def go():
        chosen = [tree.topLevelItem(i).data(0, Qt.UserRole)[0] for i in range(tree.topLevelItemCount())
                  if tree.topLevelItem(i).checkState(0) == Qt.Checked]

        def answer(button):
            if button != "Yes":
                return
            close()
            for key in chosen:
                _clean(key)
            sound.play("default")
        msgbox(desktop, "Disk Cleanup for (C:)", "Are you sure you want to perform these actions?", "question",
               ("Yes", "No"), answer)

    tree.itemChanged.connect(lambda *_: update())
    tree.currentItemChanged.connect(lambda *_: update())
    ok.clicked.connect(go)
    cancel.clicked.connect(close)
    update()
    holder["win"] = _fixed_window(desktop, "Disk Cleanup for (C:)", body, close)
    holder["win"].icon = cleanup_icon()
    desktop.open_window(holder["win"])
