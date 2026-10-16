"""The Guide (Help > Guide): assets/guide/guide.html with screenshots, plus a contents list."""
import html as htmllib
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QTextBrowser,
                               QVBoxLayout, QWidget)

from .. import host, paths
from .common import tiled_background

GUIDE_DIR = paths.ASSETS / "guide"
GUIDE_FILE = GUIDE_DIR / "guide.html"

_window = None


def show_guide(section: str = ""):
    """Open the Guide (one shared window), optionally at a section anchor."""
    global _window
    if _window is None:
        _window = GuideWindow()
        _window.destroyed.connect(_forget)
    host.present(_window)
    if section:
        _window.go_to(section)


def _forget(*_):
    global _window
    _window = None


class GuideWindow(host.HostedWindow, QWidget):
    def __init__(self):
        super().__init__(None, Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("ClaudeAIM Guide")
        tiled_background(self)
        self.resize(860, 640)

        self.contents = QListWidget()
        self.contents.setFixedWidth(190)
        self.contents.setStyleSheet("QListWidget { background: white; font: 9pt 'Arial'; }")
        self.contents.itemClicked.connect(lambda item: self.go_to(item.data(Qt.UserRole)))

        self.page = QTextBrowser()
        self.page.setOpenExternalLinks(True)
        self.page.setSearchPaths([str(GUIDE_DIR)])
        self.page.setStyleSheet("QTextBrowser { background: white; }")

        body = QHBoxLayout()
        body.addWidget(self.contents)
        body.addWidget(self.page, 1)

        close = QPushButton("Close")
        close.clicked.connect(self.close)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(close)

        root = QVBoxLayout(self)
        root.addLayout(body, 1)
        root.addLayout(buttons)

        self._load()

    def _load(self):
        if not GUIDE_FILE.exists():
            self.page.setHtml("<h2>The Guide is missing</h2><p>Expected it at "
                              f"<code>{GUIDE_FILE}</code>.</p>")
            return
        html = GUIDE_FILE.read_text(encoding="utf-8")
        self.page.setHtml(html)
        # Contents: every <h2 id="..."> in the guide.
        for anchor, title in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', html):
            item = QListWidgetItem(htmllib.unescape(re.sub(r"<[^>]+>", "", title)).strip())
            item.setData(Qt.UserRole, anchor)
            self.contents.addItem(item)

    def go_to(self, anchor):
        self.page.scrollToAnchor(anchor)
        for i in range(self.contents.count()):
            if self.contents.item(i).data(Qt.UserRole) == anchor:
                self.contents.setCurrentRow(i)
