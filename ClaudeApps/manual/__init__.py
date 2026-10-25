"""The Claude Timeline Manual: the Markdown pages in the Timeline's Manual folder, read in a window of this computer's
own style (or on their own, from the launcher or `python -m manual`).

Contents down the left, the page on the right, Back / Forward / Contents, and a search box that looks through every
page. Links between pages work; a screenshot that hasn't been taken yet shows as a note instead of a broken picture.
The pages themselves are plain Markdown, so they read fine in any editor too."""
import re
from pathlib import Path

from PySide6.QtCore import QRectF, Qt, QUrl
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap, QTextDocument
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QSplitter, QTextBrowser, QVBoxLayout, QWidget)
from shiboken6 import isValid

TIMELINE = Path(__file__).resolve().parents[2]
MANUAL = TIMELINE / "Manual"
TITLE = "Claude Timeline Manual"
HOME = "index.md"
IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
LINK = re.compile(r"\[([^\]]+)\]\(([0-9A-Za-z_-]+\.md)\)")
PAGE_CSS = """
body { font-family: 'Segoe UI', Tahoma, sans-serif; font-size: 13px; color: #1E1E1E; }
h1 { font-size: 22px; font-weight: 600; color: #1F3A68; margin-bottom: 6px; }
h2 { font-size: 16px; font-weight: 600; color: #2A4F8A; margin-top: 18px; }
h3 { font-size: 14px; font-weight: 600; color: #2A4F8A; }
a { color: #1F5FBF; }
code { font-family: Consolas, 'Courier New', monospace; font-size: 12px; background: #F0F2F6; }
pre { font-family: Consolas, 'Courier New', monospace; font-size: 12px; background: #F0F2F6; }
th { background: #E6EBF4; padding: 4px 8px; }
td { padding: 4px 8px; }
blockquote { color: #5A6478; }
"""


def manual_icon():
    """A blue book with a light-blue spine."""
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#1A2E55"), 1.2))
    p.setBrush(QColor("#2E5FA8"))
    p.drawRoundedRect(QRectF(5, 3, 23, 26), 2.5, 2.5)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#8FB4FF"))
    p.drawRoundedRect(QRectF(5, 3, 5, 26), 2, 2)
    p.setBrush(QColor("#F4F6FA"))
    p.drawRect(QRectF(12, 8, 13, 2))
    p.drawRect(QRectF(12, 13, 13, 2))
    p.drawRect(QRectF(12, 18, 9, 2))
    p.end()
    return QIcon(pm)


def pages():
    """[(file name, title)] in the order the contents page lists them, index first; any page it doesn't list after."""
    out = [(HOME, "The Claude Timeline Manual")]
    seen = {HOME}
    try:
        text = (MANUAL / HOME).read_text(encoding="utf-8")
    except OSError:
        text = ""
    for title, name in LINK.findall(text):
        if name not in seen and (MANUAL / name).is_file():
            out.append((name, re.sub(r"^\d+\.\s*", "", title)))
            seen.add(name)
    for path in sorted(MANUAL.glob("*.md")):
        if path.name not in seen:
            out.append((path.name, _heading(path) or path.stem))
            seen.add(path.name)
    return out


def _heading(path):
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return re.sub(r"^\d+\.\s*", "", line[2:].strip())
    except OSError:
        pass
    return ""


def prepare(markdown):
    """The page's Markdown, with pictures that aren't there yet shown as a note."""
    def picture(m):
        alt, src = m.group(1), m.group(2)
        if (MANUAL / src).is_file():
            return m.group(0)
        return f"> *Screenshot: {alt or src} (not taken yet)*"
    return IMAGE.sub(picture, markdown)


class ManualView(QWidget):
    def __init__(self, parent=None, start=HOME):
        super().__init__(parent)
        self.history, self.at = [], -1
        self.setStyleSheet("ManualView { background: #FFFFFF; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(6)
        bar = QHBoxLayout()
        self.back = QPushButton("Back")
        self.fwd = QPushButton("Forward")
        home = QPushButton("Contents")
        self.back.clicked.connect(lambda: self._step(-1))
        self.fwd.clicked.connect(lambda: self._step(1))
        home.clicked.connect(lambda: self.open(HOME))
        for b in (self.back, self.fwd, home):
            bar.addWidget(b)
        bar.addStretch(1)
        bar.addWidget(QLabel("Search:"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("a word or phrase, then Enter")
        self.search.setMinimumWidth(220)
        self.search.returnPressed.connect(self._search)
        bar.addWidget(self.search)
        lay.addLayout(bar)
        split = QSplitter(Qt.Horizontal)
        self.contents = QListWidget()
        self.contents.setMinimumWidth(200)
        for name, title in pages():
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, name)
            self.contents.addItem(item)
        self.contents.itemClicked.connect(lambda it: self.open(it.data(Qt.UserRole)))
        split.addWidget(self.contents)
        self.view = QTextBrowser()
        self.view.setOpenLinks(False)
        self.view.setOpenExternalLinks(False)
        self.view.setSearchPaths([str(MANUAL)])
        self.view.anchorClicked.connect(self._link)
        self.view.document().setDefaultStyleSheet(PAGE_CSS)
        self.view.document().setDocumentMargin(14)
        split.addWidget(self.view)
        split.setStretchFactor(1, 1)
        split.setSizes([230, 800])
        lay.addWidget(split, 1)
        self.open(start)

    # ---- pages -----------------------------------------------------------------------------------------------
    def open(self, name, remember=True):
        path = MANUAL / name
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            text = f"# Page not found\n\nThere's no `{name}` in the Manual folder."
        self._show(text, QUrl.fromLocalFile(str(MANUAL) + "/"))
        if remember:
            del self.history[self.at + 1:]
            self.history.append(name)
            self.at = len(self.history) - 1
        for i in range(self.contents.count()):
            if self.contents.item(i).data(Qt.UserRole) == name:
                self.contents.setCurrentRow(i)
                break
        self._buttons()

    def _show(self, markdown, base):
        doc = self.view.document()
        doc.setBaseUrl(base)
        doc.setMarkdown(prepare(markdown), QTextDocument.MarkdownDialectGitHub)
        self.view.verticalScrollBar().setValue(0)

    def _step(self, d):
        at = self.at + d
        if 0 <= at < len(self.history):
            self.at = at
            self.open(self.history[at], remember=False)

    def _buttons(self):
        self.back.setEnabled(self.at > 0)
        self.fwd.setEnabled(self.at < len(self.history) - 1)

    def _link(self, url):
        target = url.toString()
        if target.endswith(".md") or ".md#" in target:
            name = Path(url.path() if url.isLocalFile() else target.split("#")[0]).name
            self.open(name)
        elif url.scheme() in ("http", "https"):
            pass                   # the manual doesn't leave the computer

    # ---- search ----------------------------------------------------------------------------------------------
    def _search(self):
        words = self.search.text().strip()
        if not words:
            return
        needle = words.lower()
        lines = [f"# Search: {words}", ""]
        hits = 0
        for name, title in pages():
            try:
                text = (MANUAL / name).read_text(encoding="utf-8")
            except OSError:
                continue
            found = [ln.strip() for ln in text.splitlines() if needle in ln.lower() and not ln.startswith("#")]
            if not found:
                continue
            hits += len(found)
            lines.append(f"## [{title}]({name})")
            for ln in found[:6]:
                ln = re.sub(r"[`*>|]", "", ln)
                lines.append(f"- {ln[:160]}")
            if len(found) > 6:
                lines.append(f"- ... and {len(found) - 6} more")
            lines.append("")
        if not hits:
            lines.append(f"Nothing in the manual mentions \"{words}\".")
        self._show("\n".join(lines), QUrl.fromLocalFile(str(MANUAL) + "/"))
        self.contents.clearSelection()


# ---- inside a computer -----------------------------------------------------------------------------------------
_open = {}


def launch(desktop, page=HOME):
    from claudecore import host
    win = _open.get("win")
    if win is None or not isValid(win):
        body = ManualView(start=page)
        win = host.window(desktop, TITLE, body, manual_icon(), (1120, 740))
        _open["win"] = win
    elif page != HOME:
        win.content.open(page)
    desktop.open_window(win)
    return win


# ---- on its own ------------------------------------------------------------------------------------------------
def main():
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    win = ManualView()
    win.setWindowTitle(TITLE)
    win.setWindowIcon(manual_icon())
    win.resize(1120, 740)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
