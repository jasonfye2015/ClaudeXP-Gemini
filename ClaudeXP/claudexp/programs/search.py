"""Search Companion, with Rover the dog: 'What do you want to search for?' Pictures, music or video; documents;
all files and folders (part of the name, wildcards, a word or phrase inside the file, where to look); computers or
people; Help and Support; or the Internet. Results stream into a list you can open. Rover wags, blinks, and sniffs
while he searches (Change preferences can send him home)."""
import fnmatch
import math
import os
import random
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton,
                               QSplitter, QStackedWidget, QStyle, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import sound
from ..paths import DATA
from ..wm import XPWindow
from .people import load_json, save_json

SETTINGS = DATA / "search.json"
KINDS = {"media": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".mp3", ".wav", ".wma", ".ogg", ".flac", ".m4a",
                   ".avi", ".mpg", ".wmv"},
         "docs": {".txt", ".rtf", ".doc", ".htm", ".html", ".pdf", ".xls", ".wri", ".log", ".ini", ".csv"},
         "all": None}
TEXTY = {".txt", ".rtf", ".htm", ".html", ".log", ".ini", ".csv", ".json", ".xml", ".md", ".bat", ".wri", ".nfo"}
STYLE = """
QWidget#companion { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7BA2E7, stop:1 #6375D6); }
QLabel { font-family: Tahoma; font-size: 11px; color: #10206B; }
QLabel#question { font-size: 13px; font-weight: bold; color: #FFFFFF; }
QLabel#panel { background: #D6DFF7; border: 1px solid #FFFFFF; border-radius: 3px; padding: 8px; }
QPushButton#link { border: none; background: transparent; color: #10206B; text-align: left; font-family: Tahoma;
                   font-size: 11px; padding: 2px; }
QPushButton#link:hover { color: #3366FF; text-decoration: underline; }
QPushButton { font-family: Tahoma; font-size: 11px; }
QTreeWidget { font-family: Tahoma; font-size: 11px; background: white; }
"""


def search_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#205080"), 2.5))
    p.setBrush(QColor(200, 230, 255, 180))
    p.drawEllipse(QRectF(4, 4, 17, 17))
    p.setPen(QPen(QColor("#604020"), 4, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(19, 19, 27, 27)
    p.end()
    return QIcon(pm)


class Rover(QWidget):
    """The Search Companion's puppy, drawn rather than animated from bitmaps."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(150, 120)
        self.mode = "idle"            # idle / sniff / happy
        self.t = 0.0
        self.blink = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(50)

    def _tick(self):
        self.t += 0.05
        if self.blink > 0:
            self.blink -= 1
        elif random.random() < 0.015:
            self.blink = 3
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t = self.t
        fur, dark = QColor("#E8B860"), QColor("#B07A2A")
        sniff = self.mode == "sniff"
        bob = math.sin(t * 9) * 2.5 if sniff else math.sin(t * 2) * 0.8
        wag = math.sin(t * (14 if self.mode != "idle" else 6)) * (28 if self.mode != "idle" else 16)
        # shadow
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 40, 50))
        p.drawEllipse(QRectF(22, 100, 100, 12))
        # tail
        p.save()
        p.translate(110, 62)
        p.rotate(-40 + wag)
        p.setPen(QPen(dark, 1))
        p.setBrush(fur)
        tail = QPainterPath()
        tail.moveTo(0, 0)
        tail.cubicTo(8, -10, 18, -18, 22, -30)
        tail.cubicTo(16, -16, 8, -6, 0, 6)
        p.drawPath(tail)
        p.restore()
        # body and legs
        p.setPen(QPen(dark, 1.2))
        p.setBrush(fur)
        p.drawEllipse(QRectF(48, 50, 70, 42))
        for x in (56, 70, 96, 108):
            p.drawRoundedRect(QRectF(x, 80, 10, 24), 4, 4)
        p.setBrush(QColor("#F5DDA8"))
        p.drawEllipse(QRectF(60, 72, 34, 18))
        # head (dips toward the ground while sniffing)
        hx, hy = 28, (42 if sniff else 26) + bob
        p.setBrush(fur)
        p.drawEllipse(QRectF(hx, hy, 46, 42))
        p.drawEllipse(QRectF(hx - 12, hy + 18, 30, 22))         # muzzle
        # ear
        p.setBrush(dark)
        ear = QPainterPath()
        ear.moveTo(hx + 28, hy + 4)
        ear.cubicTo(hx + 48, hy + 2, hx + 50, hy + 30, hx + 40, hy + 38)
        ear.cubicTo(hx + 34, hy + 26, hx + 30, hy + 16, hx + 28, hy + 4)
        p.drawPath(ear)
        # nose, eye, mouth
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#202020"))
        p.drawEllipse(QRectF(hx - 14, hy + 20, 9, 8))
        if self.blink:
            p.setPen(QPen(QColor("#202020"), 2))
            p.drawLine(QPointF(hx + 12, hy + 15), QPointF(hx + 20, hy + 15))
        else:
            p.drawEllipse(QRectF(hx + 12, hy + 10, 8, 9))
            p.setBrush(QColor("white"))
            p.drawEllipse(QRectF(hx + 14, hy + 11, 3, 3))
        p.setPen(QPen(QColor("#603010"), 1.5))
        p.drawArc(QRectF(hx - 6, hy + 28, 14, 8), 200 * 16, 140 * 16)
        if self.mode == "happy":
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#E05060"))
            p.drawEllipse(QRectF(hx - 2, hy + 33, 7, 9))       # tongue
        if sniff:
            p.setPen(QPen(QColor(255, 255, 255, 160), 1.5))
            for i in range(3):
                phase = (t * 3 + i * 0.33) % 1
                p.drawEllipse(QPointF(hx - 22 - phase * 10, hy + 26 + phase * 4), 2 + phase * 3, 2 + phase * 3)


class SearchCompanion(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.walker = None
        self.found = 0
        self.kind = "all"
        self.setStyleSheet(STYLE)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        split = QSplitter(Qt.Horizontal)
        left = QWidget()
        left.setObjectName("companion")
        left.setAttribute(Qt.WA_StyledBackground, True)
        left.setFixedWidth(230)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(10, 10, 10, 6)
        self.pages = QStackedWidget()
        lv.addWidget(self.pages, 1)
        self.rover = Rover()
        lv.addWidget(self.rover, alignment=Qt.AlignHCenter | Qt.AlignBottom)
        split.addWidget(left)
        self.results = QTreeWidget()
        self.results.setRootIsDecorated(False)
        self.results.setHeaderLabels(["Name", "In Folder", "Size", "Type", "Date Modified"])
        self.results.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results.setColumnWidth(0, 170)
        self.results.itemDoubleClicked.connect(self._open)
        split.addWidget(self.results)
        root.addWidget(split)
        self._build()
        self.rover.setVisible(load_json(SETTINGS, {}).get("rover", True))
        self.go("start")

    # ---- pages --------------------------------------------------------------------------------------------
    def _page(self, key):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        self.pages.addWidget(w)
        self.page_index = getattr(self, "page_index", {})
        self.page_index[key] = self.pages.count() - 1
        return v

    def _link(self, v, text, slot):
        b = QPushButton(text)
        b.setObjectName("link")
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(slot)
        v.addWidget(b)
        return b

    def _question(self, v, text):
        q = QLabel(text)
        q.setObjectName("question")
        q.setWordWrap(True)
        v.addWidget(q)

    def _build(self):
        v = self._page("start")
        self._question(v, "What do you want to search for?")
        self._link(v, "▶  Pictures, music, or video", lambda: self.form("media"))
        self._link(v, "▶  Documents (word processing, spreadsheet, etc.)", lambda: self.form("docs"))
        self._link(v, "▶  All files and folders", lambda: self.form("all"))
        self._link(v, "▶  Computers or people", lambda: self.go("people"))
        self._link(v, "▶  Information in Help and Support Center", self._help)
        v.addSpacing(8)
        lab = QLabel("You may also want to...")
        v.addWidget(lab)
        self._link(v, "▶  Search the Internet", lambda: self.go("internet"))
        self._link(v, "▶  Change preferences", self._toggle_rover)
        v.addStretch()

        v = self._page("form")
        self.form_question = QLabel()
        self.form_question.setObjectName("question")
        self.form_question.setWordWrap(True)
        v.addWidget(self.form_question)
        v.addWidget(QLabel("All or part of the file name:"))
        self.name = QLineEdit()
        v.addWidget(self.name)
        v.addWidget(QLabel("A word or phrase in the file:"))
        self.phrase = QLineEdit()
        v.addWidget(self.phrase)
        v.addWidget(QLabel("Look in:"))
        self.where = QComboBox()
        v.addWidget(self.where)
        row = QHBoxLayout()
        back = QPushButton("Back")
        go = QPushButton("Search")
        row.addWidget(back)
        row.addWidget(go)
        v.addLayout(row)
        back.clicked.connect(lambda: self.go("start"))
        go.clicked.connect(self.start_search)
        self.name.returnPressed.connect(self.start_search)
        self.phrase.returnPressed.connect(self.start_search)
        v.addStretch()

        v = self._page("searching")
        self._question(v, "Searching...")
        self.progress = QLabel("")
        self.progress.setWordWrap(True)
        v.addWidget(self.progress)
        stop = QPushButton("Stop")
        stop.clicked.connect(self.stop)
        v.addWidget(stop)
        v.addStretch()

        v = self._page("done")
        self.done_text = QLabel()
        self.done_text.setObjectName("question")
        self.done_text.setWordWrap(True)
        v.addWidget(self.done_text)
        v.addWidget(QLabel("Did you find what you wanted?"))
        self._link(v, "▶  Yes, finished searching", lambda: self.frame.request_close())
        self._link(v, "▶  No, refine this search", lambda: self.go("form"))
        self._link(v, "▶  Start a new search", lambda: self.go("start"))
        v.addStretch()

        v = self._page("people")
        self._question(v, "What are you looking for?")
        self._link(v, "▶  A computer on the network", self._computers)
        self._link(v, "▶  People in your address book", self._people)
        self._link(v, "▶  Back", lambda: self.go("start"))
        self.people_note = QLabel("")
        self.people_note.setWordWrap(True)
        v.addWidget(self.people_note)
        v.addStretch()

        v = self._page("internet")
        self._question(v, "What are you looking for?")
        self.web = QLineEdit()
        v.addWidget(self.web)
        row = QHBoxLayout()
        back = QPushButton("Back")
        go = QPushButton("Search")
        row.addWidget(back)
        row.addWidget(go)
        v.addLayout(row)
        back.clicked.connect(lambda: self.go("start"))
        go.clicked.connect(self._web_search)
        self.web.returnPressed.connect(self._web_search)
        v.addStretch()

    def go(self, key):
        self.pages.setCurrentIndex(self.page_index[key])
        self.rover.mode = {"searching": "sniff", "done": "happy"}.get(key, "idle")

    def form(self, kind):
        from ..explorer import vfs
        self.kind = kind
        self.form_question.setText({"media": "Search for all pictures, music, or video files, by name:",
                                    "docs": "Search for documents by name:",
                                    "all": "Search by any or all of the criteria below."}[kind])
        self.where.clear()
        places = [("Local Hard Drives (C:;E:)", [vfs.DRIVE_C, vfs.local_storage()]),
                  ("Local Disk (C:)", [vfs.DRIVE_C]), ("External Drive (E:)", [vfs.local_storage()]),
                  ("My Documents", [vfs.my_documents()]), ("Desktop", [vfs.user_home() / "Desktop"])]
        for label, roots in places:
            self.where.addItem(QApplication.style().standardIcon(QStyle.SP_DriveHDIcon), label, roots)
        self.go("form")
        self.name.setFocus()

    # ---- searching --------------------------------------------------------------------------------------------------
    def start_search(self):
        from ..explorer import vfs
        pattern = self.name.text().strip()
        phrase = self.phrase.text().strip().lower()
        if pattern and not any(ch in pattern for ch in "*?"):
            pattern = f"*{pattern}*"
        self.criteria = (pattern.lower() or "*", phrase, KINDS[self.kind])
        self.results.clear()
        self.found = 0
        roots = self.where.currentData() or [vfs.DRIVE_C]
        self.walker = self._walk(roots)
        self.go("searching")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._step)
        self.timer.start(30)

    def _walk(self, roots):
        from ..explorer import vfs
        for root in roots:
            for folder, dirs, files in os.walk(root):
                dirs[:] = [d for d in dirs if not vfs.hidden(Path(folder) / d)]
                yield Path(folder), None
                for name in dirs + files:
                    yield Path(folder), name

    def _step(self):
        from ..explorer import vfs
        pattern, phrase, exts = self.criteria
        for _ in range(250):
            try:
                folder, name = next(self.walker)
            except StopIteration:
                return self._finished()
            if name is None:
                self.progress.setText(f"Searching in:\n{vfs.to_virtual(folder) or folder}")
                continue
            path = folder / name
            if vfs.hidden(path) or not fnmatch.fnmatch(name.lower(), pattern):
                continue
            if exts is not None and (path.is_dir() or path.suffix.lower() not in exts):
                continue
            if phrase:
                if path.is_dir() or path.suffix.lower() not in TEXTY:
                    continue
                try:
                    if path.stat().st_size > 2_000_000 or phrase not in path.read_text(
                            encoding="utf-8", errors="ignore").lower():
                        continue
                except OSError:
                    continue
            self._add(path)

    def _add(self, path):
        from ..explorer import vfs
        from ..explorer.dialogs import short_date_2001, size_text
        st = path.stat()
        is_dir = path.is_dir()
        kind = "File Folder" if is_dir else (f"{path.suffix[1:].upper()} File" if path.suffix else "File")
        item = QTreeWidgetItem([path.name, vfs.to_virtual(path.parent) or str(path.parent),
                                "" if is_dir else size_text(st.st_size), kind, short_date_2001(st.st_mtime)])
        item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon if is_dir else QStyle.SP_FileIcon))
        item.setData(0, Qt.UserRole, str(path))
        self.results.addTopLevelItem(item)
        self.found += 1

    def _finished(self):
        self.timer.stop()
        self.walker = None
        if not self.found:
            text = "Search is complete. There are no results to display."
        elif self.found == 1:
            text = "Search is complete. There is 1 file or folder that matches your criteria."
        else:
            text = f"Search is complete. There are {self.found} files and folders that match your criteria."
        self.done_text.setText(text)
        self.go("done")
        if not self.found:
            sound.play("default")

    def stop(self):
        if self.walker is not None:
            self._finished()

    def _open(self, item):
        from .. import explorer
        from ..explorer.viewers import open_file
        path = Path(item.data(0, Qt.UserRole))
        if path.is_dir():
            explorer.launch(self.desktop, path)
        elif path.exists():
            open_file(self.desktop, path)

    # ---- other searches ----------------------------------------------------------------------------------------------
    def _computers(self):
        self.people_note.setText("Searching the network...")
        QTimer.singleShot(1800, lambda: isValid(self) and self.people_note.setText(
            "No computers were found. This computer isn't on a network; it connects to the Internet by dial-up."))

    def _people(self):
        from .outlook import open_address_book
        open_address_book(self.desktop)

    def _help(self):
        from .helpctr import open_help
        open_help(self.desktop)

    def _web_search(self):
        from urllib.parse import quote_plus
        from . import navigator
        q = self.web.text().strip()
        if q:
            navigator.open_url(self.desktop, f"http://www.altavista.com/web/results?q={quote_plus(q)}")

    def _toggle_rover(self):
        on = not self.rover.isVisible()
        self.rover.setVisible(on)
        save_json(SETTINGS, {"rover": on})

    def closeEvent(self, event):
        if self.walker is not None:
            self.timer.stop()
        self.rover.timer.stop()
        event.accept()


def open_search(desktop):
    body = SearchCompanion(desktop)
    win = XPWindow(desktop, "Search Results", body, search_icon(), (760, 500))
    body.frame = win
    desktop.open_window(win)
    return win
