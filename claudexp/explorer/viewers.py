"""Opening files: which program handles what, plus Windows Picture and Fax Viewer and a small
Windows Media Player."""
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QStyle, QVBoxLayout, QWidget

from ..wm import XPWindow
from . import vfs
from .dialogs import msgbox

TEXT = {".txt", ".ini", ".log", ".bat", ".sys", ".json", ".csv", ".md", ".cfg", ".nfo", ".py", ".xml", ".reg"}
IMAGES = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
AUDIO = {".wav", ".mp3", ".wma", ".m4a", ".ogg", ".flac"}
WEB = {".htm", ".html"}


def open_file(desktop, path):
    path = Path(path)
    ext = path.suffix.lower()
    vpath = vfs.to_virtual(path) or path.name
    from .. import programs
    if ext == ".exe":
        key = vfs.EXECUTABLES.get(path.name.lower())
        if key:
            programs.launch(desktop, key)
        else:
            msgbox(desktop, vpath, f"{vpath} is not a valid Win32 application.", "error")
    elif ext in (".rtf", ".wri"):
        from ..programs.wordpad import open_wordpad
        open_wordpad(desktop, path)
    elif ext in TEXT:
        from ..programs.notepad import open_notepad
        open_notepad(desktop, path)
    elif ext in IMAGES:
        PictureViewer.open(desktop, path)
    elif ext in AUDIO:
        from ..programs.wmp import open_wmp
        open_wmp(desktop, path)
    elif ext in WEB:
        from ..programs import navigator
        navigator.launch(desktop, url=QUrl.fromLocalFile(str(path)).toString())
    else:
        msgbox(desktop, "Windows", f"Windows cannot open this file:\n\nFile: {path.name}\n\n"
                                   "To open this file, Windows needs to know what program created it.", "info")


class PictureViewer(QWidget):
    """Windows Picture and Fax Viewer: the picture, scaled to fit, with Previous/Next."""

    @classmethod
    def open(cls, desktop, path):
        viewer = cls(desktop, path)
        viewer.frame = XPWindow(desktop, "", viewer, QIcon(viewer.style().standardIcon(QStyle.SP_FileIcon)),
                                size=(640, 520))
        viewer.show_image(path)
        desktop.open_window(viewer.frame)

    def __init__(self, desktop, path):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setStyleSheet("QWidget#viewer { background: #ECE9D8; }")
        self.setObjectName("viewer")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.picture = QLabel()
        self.picture.setAlignment(Qt.AlignCenter)
        self.picture.setStyleSheet("background: white;")
        self.picture.setMinimumSize(200, 150)
        prev_btn = QPushButton("◀ Previous")
        next_btn = QPushButton("Next ▶")
        prev_btn.clicked.connect(lambda: self.step(-1))
        next_btn.clicked.connect(lambda: self.step(1))
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(prev_btn)
        row.addWidget(next_btn)
        print_btn = QPushButton("🖨 Print...")
        print_btn.clicked.connect(self._print)
        row.addWidget(print_btn)
        row.addStretch()
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.addWidget(self.picture, 1)
        root.addLayout(row)
        self.path = Path(path)
        self.pixmap = QPixmap()

    def _print(self):
        from ..printing import print_image
        print_image(self.desktop, self.path)

    def siblings(self):
        return sorted(p for p in self.path.parent.iterdir() if p.suffix.lower() in IMAGES)

    def step(self, delta):
        files = self.siblings()
        if self.path in files and files:
            self.show_image(files[(files.index(self.path) + delta) % len(files)])

    def show_image(self, path):
        self.path = Path(path)
        self.pixmap = QPixmap(str(path))
        self._fit()
        if self.frame is not None:
            self.frame.set_title(f"{self.path.name} - Windows Picture and Fax Viewer")

    def _fit(self):
        if self.pixmap.isNull():
            self.picture.setText("Drawing failed.")
            return
        size = self.picture.size()
        pm = self.pixmap
        if pm.width() > size.width() or pm.height() > size.height():
            pm = pm.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.picture.setPixmap(pm)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit()
