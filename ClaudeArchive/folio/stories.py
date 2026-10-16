"""FurStory Reader (installed with FurFolio Reader): the stories in E:\\...\\Authors and Stories... as a bookshelf.

Every folder (or loose file) at the top is a book on the shelf; only names are needed for that, so the shelf appears
at once. Opening a book walks that one folder: every readable file becomes a chapter, grouped under its sub-folder,
which reads naturally whether the folder is one story in chapters or a collection of stories.

Readable: HTML (pictures included, colours tamed), plain text (hard-wrapped 1990s lines are reflowed), RTF (via
WordPad's reader), PDF text, best-effort Word .doc / WordPerfect / Write text, and anything inside .zip or .gz.
Comic chapters (.cbr/.cbz) open in FurComix. Damaged or unreadable files simply show what could be recovered.

Keys while reading: Space/PgDn scroll (and turn to the next chapter at the end), Right/Left chapters, +/- text size,
Esc contents."""
import gzip
import hashlib
import html
import json
import os
import re
import time
import zipfile
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QIcon, QLinearGradient, QPainter, QPainterPath, QPen,
                           QPixmap, QTextDocument)
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QScrollArea,
                               QStackedWidget, QTextBrowser, QToolButton, QVBoxLayout, QWidget)
from shiboken6 import isValid

from comix.library import natural_key, nice_name
from claudecore import host

STATE_FILE = host.data("stories") / "stories.json"
TEXT_EXTS = {".txt", ".text", ".asc", ".nfo", ".me", ".1st"}
HTML_EXTS = {".htm", ".html", ".shtml", ".xhtml", ".wastestate"}
WORD_EXTS = {".doc", ".wpd", ".wri", ".wps"}
READABLE = TEXT_EXTS | HTML_EXTS | WORD_EXTS | {".rtf", ".pdf"}
COMIC_EXTS = {".cbr", ".cbz"}
SKIP_NAMES = {"thumbs.db", "desktop.ini", "robots.txt"}
MIN_BYTES = 150
THEMES = {"Paper": ("#FBF6E9", "#2A2418", "#8A3A10"), "Sepia": ("#EFE0C0", "#3A2A14", "#7A3A00"),
          "Night": ("#1C1C20", "#D6CFBE", "#C8A050")}
LEATHER = ["#7A1E1E", "#1E4A2A", "#1E2E5A", "#5A3A1A", "#4A1E4A", "#2A4A4A", "#6A4A1A", "#3A1E10", "#1A3A3A",
           "#5A1A2A"]


def story_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#3A1E08"), 1))
    p.setBrush(QColor("#F6F0DC"))
    left = QPainterPath()
    left.moveTo(16, 9)
    left.cubicTo(11, 6, 6, 6, 2.5, 8)
    left.lineTo(2.5, 27)
    left.cubicTo(6, 25, 11, 25, 16, 28)
    left.closeSubpath()
    right = QPainterPath()
    right.moveTo(16, 9)
    right.cubicTo(21, 6, 26, 6, 29.5, 8)
    right.lineTo(29.5, 27)
    right.cubicTo(26, 25, 21, 25, 16, 28)
    right.closeSubpath()
    p.drawPath(left)
    p.drawPath(right)
    p.setPen(QPen(QColor("#9A8A68"), 0.8))
    for y in (12, 15, 18, 21):
        p.drawLine(5, y, 13, y + 1)
        p.drawLine(19, y + 1, 27, y)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#B0201A"))
    p.drawRect(QRectF(21, 4, 3, 10))                                 # ribbon bookmark
    p.end()
    return QIcon(pm)


def stories_root():
    from archivepaths import archive_folder
    archive = archive_folder("mediaarchive")
    if archive is None:
        return None
    return next((d for d in sorted(archive.iterdir())
                 if d.is_dir() and d.name.lower().startswith(("authors and stories", "stories"))), None)


def _ext(name):
    """'.html' for 'page.html.WASTESTATE' and 'x.txt.gz' -> '.txt' (with gz noted separately)."""
    n = name.lower()
    if n.endswith(".gz"):
        n = n[:-3]
    if n.endswith(".wastestate"):
        n = n[:-len(".wastestate")]
    return os.path.splitext(n)[1]


def readable(name):
    return _ext(name) in READABLE or name.lower().endswith((".zip",) + tuple(COMIC_EXTS))


def title_from(name):
    n = name
    for suffix in (".gz", ".wastestate"):
        if n.lower().endswith(suffix):
            n = n[:-len(suffix)]
    stem = os.path.splitext(n)[0]
    t = nice_name(stem).replace("_", " ")
    t = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", t) if " " not in t else t          # ForWhomStarsDontShine
    return t.strip() or stem


# ---- books and chapters -----------------------------------------------------------------------------------

class Chapter:
    """One readable thing: a file, a member of a zip, or a comic (handed to FurComix)."""
    __slots__ = ("path", "member", "title", "section", "kind")

    def __init__(self, path, title, section="", member=None, kind="text"):
        self.path, self.title, self.section, self.member, self.kind = Path(path), title, section, member, kind

    @property
    def key(self):
        return f"{self.path}|{self.member or ''}"

    @property
    def base(self):
        return self.path.parent


class Book:
    __slots__ = ("path", "name", "color", "height", "thick")

    def __init__(self, path):
        self.path = Path(path)
        self.name = title_from(self.path.name) if self.path.is_file() else nice_name(self.path.name)
        h = int(hashlib.md5(self.path.name.encode("utf-8", "replace")).hexdigest(), 16)
        self.color = LEATHER[h % len(LEATHER)]
        self.height = 132 + h % 40
        self.thick = 22 + (h >> 8) % 14

    @property
    def key(self):
        return str(self.path)

    def chapters(self, limit=2000):
        """Every readable file in the book, in reading order, grouped by sub-folder."""
        if self.path.is_file():
            return _file_chapters(self.path, "")
        out = []
        for folder, dirs, files in os.walk(self.path):
            dirs[:] = sorted((d for d in dirs if not d.startswith((".", "_vti"))), key=natural_key)
            rel = Path(folder).relative_to(self.path)
            section = "  \u203A  ".join(nice_name(part) for part in rel.parts)
            files = sorted(files, key=lambda n: (not re.match(r"(index|contents|toc|readme)\b", n.lower()),
                                                 natural_key(n)))
            for name in files:
                if name.lower() in SKIP_NAMES or not readable(name):
                    continue
                out += _file_chapters(Path(folder) / name, section)
                if len(out) >= limit:
                    return out
        return out


def _file_chapters(path, section):
    n = path.name.lower()
    try:
        if path.stat().st_size < MIN_BYTES:
            return []
    except OSError:
        return []
    if n.endswith(tuple(COMIC_EXTS)):
        return [Chapter(path, title_from(path.name) + "  (comic)", section, kind="comic")]
    if n.endswith(".zip"):
        try:
            with zipfile.ZipFile(path) as z:
                names = sorted((m for m in z.namelist() if not m.endswith("/") and readable(m)
                                and z.getinfo(m).file_size >= MIN_BYTES), key=natural_key)
        except (OSError, zipfile.BadZipFile, RuntimeError):
            return []
        zsec = (section + "  \u203A  " if section else "") + title_from(path.name)
        return [Chapter(path, title_from(Path(m).name), zsec if len(names) > 1 else section, member=m)
                for m in names]
    return [Chapter(path, title_from(path.name), section)]


def list_books(root):
    out = []
    try:
        with os.scandir(root) as it:
            for e in it:
                if e.name.startswith(".") or e.name.lower() in SKIP_NAMES:
                    continue
                if e.is_dir() or readable(e.name):
                    out.append(Book(Path(e.path)))
    except OSError:
        pass
    return sorted(out, key=lambda b: natural_key(b.name))


# ---- turning files into pages --------------------------------------------------------------------------------

def _raw(ch):
    if ch.member is not None:
        with zipfile.ZipFile(ch.path) as z:
            data = z.read(ch.member)
        name = ch.member
    else:
        data = ch.path.read_bytes()
        name = ch.path.name
    if name.lower().endswith(".gz"):
        try:
            data = gzip.decompress(data)
        except (OSError, EOFError):
            pass
    return data, name


def _decode(data):
    if data[:3] == b"\xef\xbb\xbf":
        return data[3:].decode("utf-8", "replace")
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16", "replace")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252", "replace")


def reflow(text):
    """Plain text -> HTML paragraphs. Lines hard-wrapped at ~70 columns are joined; blank lines, indents and
    short lines end paragraphs; centred/ruled lines (titles, *** breaks) stay as they are."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").expandtabs(4).split("\n")
    widths = sorted(len(ln.rstrip()) for ln in lines if ln.strip())
    wrap = widths[int(len(widths) * 0.9)] if widths else 80
    hard_wrapped = 55 <= wrap <= 90
    paras, cur = [], []

    def flush():
        if cur:
            paras.append(" ".join(s.strip() for s in cur))
            cur.clear()
    for ln in lines:
        s = ln.rstrip()
        if not s.strip():
            flush()
            continue
        stripped = s.strip()
        if re.fullmatch(r"[-=*~_#+.\s]{3,}", stripped):                      # scene breaks
            flush()
            paras.append("\u2042")
            continue
        indent = len(s) - len(s.lstrip())
        if cur and (indent >= 2 or not hard_wrapped):
            flush()
        cur.append(s)
        if hard_wrapped and len(s) < wrap * 0.6:
            flush()
    flush()
    out = []
    for p in paras:
        if p == "\u2042":
            out.append("<p align='center'>*&nbsp;&nbsp;&nbsp;*&nbsp;&nbsp;&nbsp;*</p>")
        else:
            out.append(f"<p>{html.escape(p)}</p>")
    return "\n".join(out)


def _tame_html(src):
    """Old web pages: keep the words and pictures, drop scripts and the page's own colours and fonts."""
    src = re.sub(r"(?is)<(script|style|noscript|iframe|object|embed)\b.*?</\1\s*>", "", src)
    src = re.sub(r"(?is)<(script|link|meta|base)\b[^>]*>", "", src)
    src = re.sub(r"(?i)\s(bgcolor|background|text|link|vlink|alink|color|face)\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)",
                 "", src)
    src = re.sub(r"(?i)\sstyle\s*=\s*(\"[^\"]*\"|'[^']*')", "", src)
    return src


def _binary_text(data):
    """Best-effort words from Word / WordPerfect / Write files: long runs of readable text."""
    found = []
    for m in re.finditer(rb"[\x20-\x7e\x91-\x97\xa0-\xff\r\n\t]{40,}", data):
        found.append((m.start(), m.group().decode("cp1252", "replace")))
    for m in re.finditer(rb"(?:[\x20-\x7e\r\n\t]\x00){40,}", data):
        found.append((m.start(), m.group().decode("utf-16-le", "replace")))
    found.sort()
    keep = []
    for _pos, t in found:
        letters = sum(c.isalpha() or c in " ,.'\"!?;:-\r\n" for c in t)
        if letters / len(t) > 0.85 and t.count(" ") > len(t) / 12:
            keep.append(t)
    text = "\n\n".join(keep)
    return text.replace("\r", "\n")


def _wpd_text(data):
    """WordPerfect 5/6: text starts at the document pointer; printable bytes are text, 0x0A/0xCC hard returns,
    0xD0-0xFF start length-prefixed function groups (skipped), anything else is a space."""
    if data[1:4] != b"WPC" or len(data) < 16:
        return ""
    import struct
    i, n, out = struct.unpack("<I", data[4:8])[0], len(data), []
    while i < n:
        b = data[i]
        if 0x20 <= b <= 0x7E:
            out.append(chr(b))
            i += 1
        elif b in (0x0A, 0xCC):
            out.append("\n\n")
            i += 1
        elif 0xD0 <= b <= 0xFF and i + 3 < n:
            length = struct.unpack("<H", data[i + 2:i + 4])[0]
            if b == 0xD0 and data[i + 1] in (0x00, 0x01, 0x04, 0x06):
                out.append("\n\n")
            i += length if 4 <= length < 4096 else 1
        else:
            out.append(" ")
            i += 1
    return re.sub(r"[ ]{2,}", " ", "".join(out))


def render(ch):
    """(html, base folder, title) for a chapter."""
    try:
        data, name = _raw(ch)
    except (OSError, KeyError, zipfile.BadZipFile, RuntimeError) as exc:
        return f"<p><i>This chapter couldn't be opened ({html.escape(str(exc))}).</i></p>", ch.base, ch.title
    ext = _ext(name)
    title = ch.title
    if ext in HTML_EXTS:
        src = _decode(data)
        m = re.search(r"(?is)<title>(.*?)</title>", src)
        if m:
            t = re.sub(r"\s+", " ", html.unescape(m.group(1))).strip(" |-:·\t")
            if 2 < len(t) < 80:
                title = t
        return _tame_html(src), ch.base, title
    if ext == ".rtf":
        from claudecore.rtf import from_rtf
        doc = QTextDocument()
        try:
            from_rtf(_decode(data), doc)
            return _tame_html(doc.toHtml()), ch.base, title
        except Exception:                      # odd RTF: fall back to its words
            text = re.sub(r"\\[a-z]+-?\d* ?|[{}]", "", _decode(data))
            return reflow(text), ch.base, title
    if ext == ".pdf":
        return _pdf_html(ch.path if ch.member is None else None, data), ch.base, title
    if ext in WORD_EXTS:
        text = _wpd_text(data) if ext == ".wpd" else ""
        if len(text.split()) < 50:
            text = _binary_text(data)
        if len(text) < 200:
            return "<p><i>Not much could be recovered from this file.</i></p>" + reflow(text), ch.base, title
        return reflow(text), ch.base, title
    return reflow(_decode(data)), ch.base, title


def _pdf_html(path, data):
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice
    from PySide6.QtPdf import QPdfDocument
    doc = QPdfDocument()
    if path is not None:
        doc.load(str(path))
    else:
        buf = QBuffer()
        buf.setData(QByteArray(data))
        buf.open(QIODevice.ReadOnly)
        doc.load(buf)
    pages = []
    for i in range(doc.pageCount()):
        pages.append(doc.getAllText(i).text())
    doc.close()
    text = "\n\n".join(pages)
    if len(text.strip()) < 100:
        return "<p><i>This PDF is scanned pages with no text in it.</i></p>"
    return reflow(text)


# ---- state ---------------------------------------------------------------------------------------------------

def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=1), encoding="utf-8")
    except OSError:
        pass


# ---- the bookshelf ---------------------------------------------------------------------------------------------

SHELF_PAD = 14
PLANK = 16


class Shelves(QWidget):
    """Spines on wooden shelves. Hovering lifts a book; clicking takes it down."""
    opened = Signal(object)

    def __init__(self):
        super().__init__()
        self.books = []
        self.visible = []
        self.rects = []                      # (QRectF, Book)
        self.hover = None
        self.reading = set()
        self.setMouseTracking(True)

    def set_books(self, books, reading=()):
        self.books = books
        self.reading = set(reading)
        self.filter("")

    def filter(self, text):
        t = text.lower().strip()
        self.visible = [b for b in self.books if not t or t in b.name.lower()]
        self.relayout()

    def relayout(self):
        width = max(300, self.parentWidget().width() if self.parentWidget() else self.width())
        self.rects = []
        x, y = SHELF_PAD, SHELF_PAD
        row_h = 190
        for b in self.visible:
            if x + b.thick > width - SHELF_PAD:
                x = SHELF_PAD
                y += row_h + PLANK + 18
            self.rects.append((QRectF(x, y + row_h - b.height, b.thick, b.height), b))
            x += b.thick + 1
        self.setMinimumHeight(int(y + row_h + PLANK + 30))
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if event.oldSize().width() != event.size().width():
            QTimer.singleShot(0, self.relayout)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg = QLinearGradient(0, 0, 0, self.height())
        bg.setColorAt(0, QColor("#3A2614"))
        bg.setColorAt(1, QColor("#24160A"))
        p.fillRect(self.rect(), bg)                                                     # the bookcase back
        rows = sorted({int(r.bottom()) for r, _b in self.rects})
        for bottom in rows:
            plank = QRectF(0, bottom, self.width(), PLANK)
            g = QLinearGradient(0, plank.top(), 0, plank.bottom())
            g.setColorAt(0, QColor("#9A6A3A"))
            g.setColorAt(0.4, QColor("#7A5028"))
            g.setColorAt(1, QColor("#4A2E14"))
            p.fillRect(plank, g)
            p.fillRect(QRectF(0, plank.bottom(), self.width(), 6), QColor(0, 0, 0, 90))  # shadow under the shelf
        for r, b in self.rects:
            if not event.rect().intersects(r.toAlignedRect().adjusted(-2, -12, 2, 2)):
                continue
            lift = 8 if b is self.hover else 0
            rr = r.translated(0, -lift)
            base = QColor(b.color)
            g = QLinearGradient(rr.left(), 0, rr.right(), 0)
            g.setColorAt(0, base.darker(150))
            g.setColorAt(0.35, base.lighter(125))
            g.setColorAt(1, base.darker(170))
            p.setPen(QPen(QColor(0, 0, 0, 160), 1))
            p.setBrush(g)
            p.drawRoundedRect(rr, 2, 2)
            gold = QColor("#E8C870")
            p.setPen(QPen(gold, 1))
            for yy in (rr.top() + 10, rr.top() + 14, rr.bottom() - 14, rr.bottom() - 10):    # gilt bands
                p.drawLine(int(rr.left() + 3), int(yy), int(rr.right() - 3), int(yy))
            if b.key in self.reading:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#C0201A"))
                p.drawRect(QRectF(rr.center().x() - 2.5, rr.top() - 6, 5, 14))              # a bookmark ribbon
            p.save()
            p.translate(rr.center())
            p.rotate(90)
            f = QFont("Georgia", 8 if b.thick < 28 else 9, QFont.Bold)
            p.setFont(f)
            fm = QFontMetrics(f)
            room = rr.height() - 36
            text = fm.elidedText(b.name, Qt.ElideRight, int(room))
            p.setPen(gold)
            p.drawText(QRectF(-room / 2, -rr.width() / 2, room, rr.width()), Qt.AlignCenter, text)
            p.restore()

    def _hit(self, pos):
        for r, b in self.rects:
            if r.adjusted(0, -10, 0, 0).contains(pos):
                return b
        return None

    def mouseMoveEvent(self, event):
        b = self._hit(event.position())
        if b is not self.hover:
            self.hover = b
            self.setCursor(Qt.PointingHandCursor if b else Qt.ArrowCursor)
            self.setToolTip(b.name if b else "")
            self.update()

    def leaveEvent(self, event):
        self.hover = None
        self.update()

    def mouseReleaseEvent(self, event):
        b = self._hit(event.position())
        if b is not None and event.button() == Qt.LeftButton:
            self.opened.emit(b)


# ---- the window ----------------------------------------------------------------------------------------------------

BAR_STYLE = ("QWidget#bar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FDFDFB, stop:1 #E3E0D2);"
             " border-bottom: 1px solid #A0A0A0; }"
             "QToolButton { font: 11px Tahoma; padding: 3px 8px; border: 1px solid transparent; border-radius: 3px; }"
             "QToolButton:hover { border-color: #C0BCA8; background: white; }"
             "QToolButton:checked { background: #D8E4F8; border-color: #7A96D0; }"
             "QToolButton:disabled { color: #A0A0A0; }"
             "QLineEdit { font: 11px Tahoma; border: 1px solid #7F9DB9; padding: 1px 4px; } QLabel { font: 11px Tahoma; }")


class StoryReader(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.state = load_state()
        self.root = stories_root()
        self.book = None
        self.chapters = []
        self.index = 0
        self.size = int(self.state.get("size", 12))
        self.theme = self.state.get("theme", "Paper")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack)
        self.stack.addWidget(self._shelf_page())
        self.stack.addWidget(self._contents_page())
        self.stack.addWidget(self._reading_page())
        if self.root is None:
            self.shelf_status.setText("Put the Furry Media Archive (with Authors and Stories) on drive E: "
                                      "(Local Storage).")
        else:
            self.show_shelf()

    def _bar(self):
        bar = QWidget()
        bar.setObjectName("bar")
        bar.setAttribute(Qt.WA_StyledBackground)
        bar.setStyleSheet(BAR_STYLE)
        row = QHBoxLayout(bar)
        row.setContentsMargins(4, 3, 6, 3)
        row.setSpacing(3)
        return bar, row

    @staticmethod
    def _tool(row, text, tip, slot, checkable=False):
        b = QToolButton()
        b.setText(text)
        b.setToolTip(tip)
        b.setCheckable(checkable)
        b.setFocusPolicy(Qt.NoFocus)
        b.clicked.connect(slot)
        row.addWidget(b)
        return b

    # ---- shelf ------------------------------------------------------------------------------------------------
    def _shelf_page(self):
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        bar, row = self._bar()
        self.continue_btn = self._tool(row, "", "Pick up where you left off", self.continue_reading)
        row.addStretch(1)
        row.addWidget(QLabel("Find:"))
        self.find = QLineEdit()
        self.find.setPlaceholderText("Title")
        self.find.setFixedWidth(160)
        self.find.textChanged.connect(lambda t: self.shelves.filter(t))
        row.addWidget(self.find)
        col.addWidget(bar)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: #24160A; }")
        self.shelves = Shelves()
        self.shelves.opened.connect(self.open_book)
        self.scroll.setWidget(self.shelves)
        col.addWidget(self.scroll, 1)
        self.shelf_status = QLabel()
        self.shelf_status.setStyleSheet("font: 11px Tahoma; padding: 2px 6px; background: #ECE9D8;"
                                        " border-top: 1px solid #A0A0A0;")
        col.addWidget(self.shelf_status)
        return page

    def show_shelf(self):
        books = list_books(self.root) if self.root else []
        reading = [k for k, v in self.state.get("books", {}).items() if not v.get("finished")]
        self.shelves.set_books(books, reading)
        self.shelf_status.setText(f"{len(books)} books")
        last = self._last_read()
        self.continue_btn.setVisible(last is not None)
        if last is not None:
            self.continue_btn.setText(f"\u25B6 Continue: {last[1]['name']}")
        self.stack.setCurrentIndex(0)
        if self.frame is not None:
            self.frame.set_title("FurStory Reader")

    def _last_read(self):
        books = [(k, v) for k, v in self.state.get("books", {}).items() if os.path.exists(k)]
        return max(books, key=lambda kv: kv[1].get("last", 0)) if books else None

    def continue_reading(self):
        last = self._last_read()
        if last is not None:
            self.open_book(Book(last[0]), resume=True)

    # ---- contents ---------------------------------------------------------------------------------------------
    def _contents_page(self):
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        bar, row = self._bar()
        self._tool(row, "\u25C4 Bookshelf", "Back to the bookshelf", self.show_shelf)
        row.addStretch(1)
        self.start_btn = self._tool(row, "Start Reading", "Open the first chapter", lambda: self.read(self._resume()))
        col.addWidget(bar)
        body = QWidget()
        body.setStyleSheet("background: #F3EEDF;")
        h = QHBoxLayout(body)
        h.setContentsMargins(18, 18, 18, 18)
        h.setSpacing(18)
        self.cover = QLabel()
        self.cover.setFixedSize(190, 260)
        h.addWidget(self.cover, 0, Qt.AlignTop)
        right = QVBoxLayout()
        self.book_title = QLabel()
        self.book_title.setWordWrap(True)
        self.book_title.setStyleSheet("font: bold 20px Georgia; color: #3A2410;")
        right.addWidget(self.book_title)
        self.book_info = QLabel()
        self.book_info.setStyleSheet("font: italic 12px Georgia; color: #6A5A40;")
        right.addWidget(self.book_info)
        self.toc = QListWidget()
        self.toc.setStyleSheet("QListWidget { background: #FBF7EA; border: 1px solid #C8BC98; font: 12px Georgia;"
                               " color: #2A2418; } QListWidget::item { padding: 3px 6px; }"
                               "QListWidget::item:selected { background: #E8D6A0; color: #2A1A08; }")
        self.toc.itemActivated.connect(lambda item: item.data(Qt.UserRole) is not None and
                                       self.read(item.data(Qt.UserRole)))
        right.addWidget(self.toc, 1)
        h.addLayout(right, 1)
        col.addWidget(body, 1)
        return page

    def open_book(self, book, resume=False):
        self.book = book
        self.chapters = book.chapters()
        self.toc.clear()
        info = self.state.get("books", {}).get(book.key, {})
        section = None
        for i, ch in enumerate(self.chapters):
            if ch.section != section and ch.section:
                head = QListWidgetItem(ch.section)
                f = QFont("Georgia", 10, QFont.Bold)
                head.setFont(f)
                head.setForeground(QColor("#8A5A20"))
                head.setFlags(Qt.NoItemFlags)
                head.setData(Qt.UserRole, None)
                self.toc.addItem(head)
            section = ch.section
            item = QListWidgetItem(("      " if ch.section else "") + ch.title)
            item.setData(Qt.UserRole, i)
            if info.get("chapter") == i:
                item.setText(item.text() + "   \u25C2 you are here")
            self.toc.addItem(item)
        self.book_title.setText(book.name)
        n = len(self.chapters)
        self.book_info.setText(f"{n} chapter{'s' if n != 1 else ''}" if n else "Nothing readable in this one.")
        self.cover.setPixmap(self._cover(book))
        self.start_btn.setEnabled(bool(n))
        self.start_btn.setText(f"Continue (chapter {info['chapter'] + 1})" if info and info.get("chapter", 0) < n
                               and not info.get("finished") and info.get("chapter", 0) > 0 else "Start Reading")
        if self.frame is not None:
            self.frame.set_title(f"{book.name} - FurStory Reader")
        if resume and n:
            self.read(self._resume(), restore=True)
        else:
            self.stack.setCurrentIndex(1)

    def _resume(self):
        info = self.state.get("books", {}).get(self.book.key, {}) if self.book else {}
        i = info.get("chapter", 0)
        return i if 0 <= i < len(self.chapters) else 0

    def _cover(self, book):
        pm = QPixmap(self.cover.size())
        pm.fill(QColor("#F3EEDF"))
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(6, 4, pm.width() - 14, pm.height() - 12)
        p.fillRect(r.translated(5, 6), QColor(0, 0, 0, 70))
        base = QColor(book.color)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, base.lighter(130))
        g.setColorAt(1, base.darker(160))
        p.setPen(QPen(QColor(0, 0, 0, 160), 1))
        p.setBrush(g)
        p.drawRoundedRect(r, 3, 3)
        p.fillRect(QRectF(r.left(), r.top(), 12, r.height()), QColor(0, 0, 0, 60))        # spine fold
        gold = QColor("#E8C870")
        p.setPen(QPen(gold, 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawRect(r.adjusted(22, 14, -10, -14))
        p.setFont(QFont("Georgia", 13, QFont.Bold))
        p.drawText(r.adjusted(30, 30, -18, -60), Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextWordWrap, book.name)
        p.setFont(QFont("Georgia", 16))
        p.drawText(r.adjusted(22, 0, -10, -24), Qt.AlignHCenter | Qt.AlignBottom, "\u2766")
        p.end()
        return pm

    # ---- reading ------------------------------------------------------------------------------------------------
    def _reading_page(self):
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        bar, row = self._bar()
        self._tool(row, "\u25C4 Contents", "Table of contents (Esc)", self.show_contents)
        row.addSpacing(6)
        self.prev_btn = self._tool(row, "\u25C4 Previous", "Previous chapter (Left)", lambda: self.step(-1))
        self.chapter_label = QLabel()
        self.chapter_label.setStyleSheet("color: #303030; padding: 0 8px;")
        row.addWidget(self.chapter_label, 1)
        self.next_btn = self._tool(row, "Next \u25BA", "Next chapter (Right)", lambda: self.step(1))
        row.addSpacing(10)
        self._tool(row, "A\u2212", "Smaller text (-)", lambda: self.resize_text(-1))
        self._tool(row, "A+", "Larger text (+)", lambda: self.resize_text(1))
        row.addSpacing(6)
        self.theme_btns = {name: self._tool(row, name, f"{name} pages", lambda _c=False, n=name: self.set_theme(n),
                                            True) for name in THEMES}
        col.addWidget(bar)
        self.page = Page(self)
        self.page.anchorClicked.connect(self._link)
        self.page.verticalScrollBar().valueChanged.connect(lambda *_: self._progress_timer.start())
        col.addWidget(self.page, 1)
        self.read_status = QLabel()
        self.read_status.setStyleSheet("font: 11px Tahoma; padding: 2px 6px; background: #ECE9D8;"
                                       " border-top: 1px solid #A0A0A0;")
        col.addWidget(self.read_status)
        self._progress_timer = QTimer(self, singleShot=True, interval=400, timeout=self._save_place)
        self.set_theme(self.theme, save=False)
        return page

    def read(self, index, restore=False):
        if not self.chapters:
            return
        self.index = max(0, min(index, len(self.chapters) - 1))
        ch = self.chapters[self.index]
        if ch.kind == "comic":
            self._open_comic(ch)
            return
        html_text, base, title = render(ch)
        self.page.setSearchPaths([str(base)])
        self.page.document().setBaseUrl(QUrl.fromLocalFile(str(base) + os.sep))
        self.page.setHtml(html_text)
        self.apply_look()
        self.stack.setCurrentIndex(2)
        n = len(self.chapters)
        self.chapter_label.setText(f"{self.book.name}  \u2014  Chapter {self.index + 1} of {n}: {title}")
        self.prev_btn.setEnabled(self.index > 0)
        self.next_btn.setEnabled(self.index < n - 1)
        info = self.state.get("books", {}).get(self.book.key, {})
        frac = info.get("scroll", 0) if restore and info.get("chapter") == self.index else 0
        QTimer.singleShot(0, lambda: self._scroll_to(frac))
        self.page.setFocus()
        self._save_place()
        if self.frame is not None:
            self.frame.set_title(f"{title} - FurStory Reader")

    def _scroll_to(self, frac):
        sb = self.page.verticalScrollBar()
        sb.setValue(int(sb.maximum() * frac))

    def _open_comic(self, ch):
        from comix import library as CL
        from comix.reader import open_comix
        win = open_comix(self.desktop)
        source = "zip" if ch.path.suffix.lower() == ".cbz" else "7z"
        win.content.open_entry(CL.Entry(ch.path, "comic", source))

    def step(self, delta):
        i = self.index + delta
        if 0 <= i < len(self.chapters):
            self.read(i)
        elif i >= len(self.chapters):
            books = self.state.setdefault("books", {})
            books.setdefault(self.book.key, {})["finished"] = True
            save_state(self.state)
            self.read_status.setText("The End.")

    def show_contents(self):
        if self.book is not None:
            self.open_book(self.book)

    def _save_place(self):
        if self.book is None or self.stack.currentIndex() != 2:
            return
        sb = self.page.verticalScrollBar()
        frac = sb.value() / sb.maximum() if sb.maximum() else 1.0
        books = self.state.setdefault("books", {})
        books[self.book.key] = {"chapter": self.index, "scroll": round(frac, 4), "name": self.book.name,
                                "last": time.time(),
                                "finished": self.index == len(self.chapters) - 1 and frac > 0.97}
        save_state(self.state)
        pct = int(frac * 100)
        self.read_status.setText(f"{pct}% of this chapter")

    def _link(self, url):
        """Links between a story's own pages turn to that chapter; anything else is ignored."""
        if url.isLocalFile() or not url.scheme():
            target = Path(url.toLocalFile() if url.isLocalFile() else
                          os.path.join(self.chapters[self.index].base, url.path()))
            for i, ch in enumerate(self.chapters):
                if ch.member is None and ch.path.resolve() == target.resolve():
                    self.read(i)
                    return
        elif url.scheme() in ("http", "https"):
            self.read_status.setText(f"That link goes out to the web ({url.host()}).")

    # ---- look ---------------------------------------------------------------------------------------------------
    def set_theme(self, name, save=True):
        self.theme = name if name in THEMES else "Paper"
        for n, b in self.theme_btns.items():
            b.setChecked(n == self.theme)
        if save:
            self.state["theme"] = self.theme
            save_state(self.state)
        self.apply_look()

    def resize_text(self, delta):
        self.size = max(9, min(22, self.size + delta))
        self.state["size"] = self.size
        save_state(self.state)
        self.apply_look()

    def apply_look(self):
        bg, fg, link = THEMES[self.theme]
        self.page.setStyleSheet(f"QTextBrowser {{ background: {bg}; color: {fg}; border: none; }}")
        doc = self.page.document()
        doc.setDefaultFont(QFont("Georgia", self.size))
        doc.setDefaultStyleSheet(f"a {{ color: {link}; }} p {{ margin-bottom: {self.size // 2}px; }}")
        doc.setDocumentMargin(0)
        self.page.update_margins()

    def keyPressEvent(self, event):
        if self.stack.currentIndex() == 2 and self.page.key(event):
            return
        if event.key() == Qt.Key_Escape and self.stack.currentIndex() == 1:
            self.show_shelf()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self._save_place()
        event.accept()


class Page(QTextBrowser):
    """The page: a comfortable column of text in the middle of the window."""

    def __init__(self, reader):
        super().__init__()
        self.reader = reader
        self.setOpenLinks(False)
        self.setFrameShape(QTextBrowser.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def update_margins(self):
        """Centre a ~720px column by giving the document's root frame wide side margins."""
        width = self.viewport().width()
        column = min(720, max(320, width - 60))
        side = max(24, (width - column) // 2)
        root = self.document().rootFrame()
        fmt = root.frameFormat()
        if fmt.leftMargin() != side:
            fmt.setLeftMargin(side)
            fmt.setRightMargin(side)
            fmt.setTopMargin(24)
            fmt.setBottomMargin(48)
            root.setFrameFormat(fmt)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_margins()

    def key(self, event):
        k = event.key()
        sb = self.verticalScrollBar()
        if k in (Qt.Key_Space, Qt.Key_PageDown):
            if sb.value() >= sb.maximum():
                self.reader.step(1)
            else:
                sb.setValue(sb.value() + int(self.viewport().height() * 0.9))
        elif k == Qt.Key_PageUp:
            sb.setValue(sb.value() - int(self.viewport().height() * 0.9))
        elif k == Qt.Key_Right:
            self.reader.step(1)
        elif k == Qt.Key_Left:
            self.reader.step(-1)
        elif event.text() in ("+", "="):
            self.reader.resize_text(1)
        elif event.text() in ("-", "_"):
            self.reader.resize_text(-1)
        elif k == Qt.Key_Escape:
            self.reader.show_contents()
        else:
            return False
        return True

    def keyPressEvent(self, event):
        if not self.key(event):
            super().keyPressEvent(event)


_open = {}


def open_stories(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = StoryReader(desktop)
        win = host.window(desktop, "FurStory Reader", body, story_icon(), (820, 600))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win
