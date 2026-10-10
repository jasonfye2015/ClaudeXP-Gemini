"""Offline documentation: the Python 3.12 manual and pygame's reference, searchable, in a small browser window."""
import json
import re
import zipfile
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QSplitter, QTextBrowser,
                               QToolButton, QVBoxLayout, QWidget)

TITLE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
SKIP = ("_static", "_sources", "_images", "genindex", "py-modindex", "search.html", "glossary", "bugs", "about",
        "copyright", "license", "whatsnew", "contents.html", "download", "_modules")


def _docs_root():
    from .app import studio_root
    return studio_root() / "docs"


def _python_zip():
    return next(iter(sorted(_docs_root().glob("python-*-docs-html.zip"))), None)


def _pygame_docs():
    from .app import studio_root
    return studio_root() / "python312" / "Lib" / "site-packages" / "pygame" / "docs" / "generated"


def _extract():
    """Unpack the Python manual the first time it is wanted. Returns the folder (or None if it isn't there)."""
    root = _docs_root() / "python312"
    marker = root / ".done"
    if marker.exists():
        return root
    archive = _python_zip()
    if archive is None:
        return None
    root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        top = names[0].split("/")[0] + "/"
        for n in names:
            if n.endswith("/") or not n.startswith(top):
                continue
            target = root / n[len(top):]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(n))
    marker.write_text("ok", encoding="utf-8")
    return root


def _scan(folder, label, wanted=lambda p: True):
    out = []
    for f in folder.rglob("*.html"):
        rel = f.relative_to(folder).as_posix()
        if any(s in rel for s in SKIP) or not wanted(rel):
            continue
        try:
            head = f.read_text(encoding="utf-8", errors="ignore")[:3000]
        except OSError:
            continue
        m = TITLE.search(head)
        title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else f.stem
        title = re.sub(r"\s*[—\u2014-]+\s*(Python 3\.\d+\.\d+ documentation|pygame.*)$", "", title).strip()
        out.append([f"{label}: {title}", str(f), rel.lower() + " " + title.lower()])
    return out


def index():
    """[[title, path, search text]] for every manual page; cached in docs/index.json."""
    cache = _docs_root() / "index.json"
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
        if data:
            return data
    except (OSError, ValueError):
        pass
    data = []
    py = _extract()
    if py is not None:
        data += _scan(py, "Python", lambda r: r.startswith(("library/", "tutorial/", "reference/", "howto/",
                                                              "faq/")))
    pg = _pygame_docs()
    if pg.is_dir():
        data += _scan(pg, "pygame")
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass
    return data


def available():
    return _python_zip() is not None or _pygame_docs().is_dir()


class DocsViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.entries = []
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        top = QHBoxLayout()
        self.back = QToolButton()
        self.back.setText("\u25C0 Back")
        self.forward = QToolButton()
        self.forward.setText("Forward \u25B6")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search the manuals, e.g. \"pygame.draw\", \"random\", \"str.split\"")
        self.search.textChanged.connect(self._filter)
        self.search.returnPressed.connect(lambda: self._open_row(0))
        top.addWidget(self.back)
        top.addWidget(self.forward)
        top.addWidget(self.search, 1)
        root.addLayout(top)
        split = QSplitter(Qt.Horizontal)
        self.results = QListWidget()
        self.results.itemActivated.connect(lambda i: self._open_item(i))
        self.results.itemClicked.connect(lambda i: self._open_item(i))
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        self.back.clicked.connect(self.browser.backward)
        self.forward.clicked.connect(self.browser.forward)
        split.addWidget(self.results)
        split.addWidget(self.browser)
        split.setSizes([230, 520])
        root.addWidget(split, 1)
        self.note = QLabel("")
        root.addWidget(self.note)
        self.load()

    def load(self):
        self.note.setText("Preparing the manuals (first time only)...")
        self.entries = index()
        if not self.entries:
            self.note.setText("No documentation found in Python Studio\\docs.")
            self.browser.setHtml("<h3>No documentation installed</h3><p>Put python-3.12.x-docs-html.zip in "
                                 "Local Storage\\Python Studio\\docs.</p>")
            return
        self.note.setText(f"{len(self.entries)} pages. Press Enter to open the first match.")
        self._filter("")
        self.open_title("Python: Python Tutorial") or self._open_row(0)

    def _filter(self, text):
        words = text.lower().split()
        self.results.clear()
        shown = 0
        scored = []
        for title, path, hay in self.entries:
            if all(w in hay for w in words):
                lower = title.lower()
                rank = 0 if words and lower.split(": ", 1)[-1].startswith(words[0]) else 1
                scored.append((rank, len(title), title, path))
        scored.sort()
        for _r, _l, title, path in scored[:300]:
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, path)
            self.results.addItem(item)
            shown += 1
        self.note.setText(f"{shown} match(es)" if text else f"{len(self.entries)} pages")

    def _open_item(self, item):
        self.browser.setSource(QUrl.fromLocalFile(item.data(Qt.UserRole)))

    def _open_row(self, row):
        item = self.results.item(row)
        if item is not None:
            self._open_item(item)

    def search_for(self, text):
        self.search.setText(text.strip())
        self._open_row(0)

    def open_title(self, title):
        for t, path, _h in self.entries:
            if t == title:
                self.browser.setSource(QUrl.fromLocalFile(path))
                return True
        return False

    def look_up(self, text):
        self.search.setText(text.strip())
        self._open_row(0)
