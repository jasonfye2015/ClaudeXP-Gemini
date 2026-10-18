"""Personal Document Gallery: the user's own papers on E: (Local Storage/Personal Texts and Docs).

A gallery like the other archive readers (built on Fur CD Viewer): folders as folders with a peek at a page inside,
documents as paper pages showing how they start (a PDF's first page, the opening lines of everything else) with a
coloured badge for the kind of file. The folders are read as they are every time, so however they're sorted later,
the gallery follows.

Show: Documents (text, web pages, Word, WordPad, OpenOffice, PDF, spreadsheets), Documents and pictures (the
default, for scanned papers), or All files. Sort by Name, Date or Type. A document opens in the reading pane - text,
web pages, RTF, Word and OpenOffice as text, PDFs as pages - and 'Open in its program' hands it to this computer's
own program for it.

Nothing is indexed up front; previews are made as they scroll into view (PDF pages are cached in data/documents)."""
import hashlib
import html
import json
import os
import re
import zipfile
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QUrl
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QMenu, QStackedWidget, QTextBrowser, QToolButton, QVBoxLayout,
                               QWidget)
from shiboken6 import isValid

from comix.library import natural_key, nice_name
from .cdviewer import CDViewer
from .gallery import Node
from claudecore import host

DATA = host.data("documents")
THUMBS = DATA / "thumbs"
SETTINGS = DATA / "settings.json"
SIZE = 150

TEXT_EXTS = {".txt", ".log", ".ini", ".nfo", ".csv", ".json", ".xml", ".md", ".cfg", ".eml", ".diz", ".me", ".1st"}
WEB_EXTS = {".html", ".htm", ".shtml", ".mht", ".xhtml"}
WORD_EXTS = {".doc", ".docx", ".rtf", ".wri", ".odt", ".sxw", ".wpd"}
PDF_EXTS = {".pdf"}
SHEET_EXTS = {".xls", ".xlsx", ".ods", ".wks"}
DOC_EXTS = TEXT_EXTS | WEB_EXTS | WORD_EXTS | PDF_EXTS | SHEET_EXTS
PICTURE_EXTS = {".jpg", ".jpeg", ".jpe", ".jfif", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}
SHOWS = {"documents": "Documents", "pictures": "Documents and pictures", "all": "All files"}
SORTS = {"name": "Name", "date": "Date modified", "type": "Type"}
# the badge on each kind of page: (label, colour)
BADGES = [(TEXT_EXTS, "TXT", "#6A6A6A"), (WEB_EXTS, "HTML", "#D86A10"), ({".doc", ".docx", ".wri", ".wpd"}, "DOC",
          "#2A5CB0"), ({".rtf"}, "RTF", "#2A7CB0"), ({".odt", ".sxw"}, "ODT", "#2A8AA0"), (PDF_EXTS, "PDF", "#C01818"),
          (SHEET_EXTS, "XLS", "#1E7A30")]
MAX_READ = 2 * 2 ** 20                       # the reading pane shows the first 2 MB of a huge text file


def docs_icon():
    """A little stack of papers with a red paw on the top sheet."""
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    for dx, dy, fill in ((6, 1, "#E4E0D4"), (3, 3, "#EEEBE2")):
        p.setPen(QPen(QColor("#8A8478"), 1))
        p.setBrush(QColor(fill))
        p.drawRect(QRectF(4.5 + dx, 2.5 + dy, 18, 23))
    page = QPainterPath()
    page.moveTo(4.5, 6.5)
    page.lineTo(17.5, 6.5)
    page.lineTo(22.5, 11.5)
    page.lineTo(22.5, 30.5)
    page.lineTo(4.5, 30.5)
    page.closeSubpath()
    p.setPen(QPen(QColor("#6A6458"), 1))
    p.setBrush(QColor("white"))
    p.drawPath(page)
    p.setPen(QPen(QColor("#9AA4C0"), 1))
    for y in (15, 18, 21, 24, 27):
        p.drawLine(QPointF(7, y + 0.5), QPointF(20, y + 0.5))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#D8261C"))
    for x, y, r in ((11, 12, 2.2), (8.2, 9.4, 1.1), (10.2, 8.2, 1.1), (12.2, 8.2, 1.1), (14.0, 9.4, 1.1)):
        p.drawEllipse(QRectF(x - r, y - r, 2 * r, 2 * r))
    p.end()
    return QIcon(pm)


def docs_root():
    from archivepaths import archive_folder
    return archive_folder("personaldocs")


def kind_of(name):
    ext = os.path.splitext(name.lower())[1]
    if ext in DOC_EXTS:
        return "doc"
    if ext in PICTURE_EXTS:
        return "piece"
    return "file"


def badge(name):
    ext = os.path.splitext(name.lower())[1]
    for exts, label, colour in BADGES:
        if ext in exts:
            return label, colour
    return (ext[1:5].upper() or "FILE"), "#707070"


def listing(folder, show, sort):
    """(sub-folders, files to show [(name, kind)], how many files are hidden) for a folder."""
    dirs, files, hidden = [], [], 0
    try:
        with os.scandir(folder) as it:
            entries = list(it)
    except OSError:
        entries = []
    for e in entries:
        low = e.name.lower()
        if low.startswith(".") or low in ("thumbs.db", "desktop.ini"):
            continue
        try:
            is_dir = e.is_dir()
        except OSError:
            continue
        if is_dir:
            if show != "all" and low.endswith("_files"):              # a saved web page's pictures and scripts
                hidden += 1
                continue
            dirs.append(e)
            continue
        kind = kind_of(e.name)
        if kind == "doc" or show == "all" or (show == "pictures" and kind == "piece"):
            files.append((e, kind))
        else:
            hidden += 1

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
        files.sort(key=lambda f: (os.path.splitext(f[0].name.lower())[1], natural_key(f[0].name)))
    else:
        dirs.sort(key=lambda e: natural_key(e.name))
        files.sort(key=lambda f: natural_key(f[0].name))
    return [e.name for e in dirs], [(e.name, k) for e, k in files], hidden


# ---- reading text out of documents (worker threads and the reading pane) -------------------------------------
def _decode(data):
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="replace")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def _read(path, limit):
    try:
        with open(path, "rb") as f:
            return f.read(limit)
    except OSError:
        return b""


def _html_text(markup):
    markup = re.sub(r"(?is)<(script|style|head)\b.*?</\1>", " ", markup)
    markup = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</h\d>|</li>|</tr>", "\n", markup)
    text = html.unescape(re.sub(r"(?s)<[^>]+>", " ", markup))
    return re.sub(r"[ \t\r\f\v]+", " ", text)


def _xml_paragraphs(xml, para_end):
    xml = re.sub(para_end, "\n", xml)
    xml = re.sub(r"<w:tab/>|<text:tab/>", "\t", xml)
    return html.unescape(re.sub(r"(?s)<[^>]+>", "", xml))


def _word97_text(data):
    """Old Word (.doc) keeps its text as plain runs inside the file: take the longest readable runs, whether the
    document stored them as 8-bit or as UTF-16."""
    narrow = [m.decode("cp1252") for m in re.findall(rb"[\x20-\x7e\x91-\x97\r\t]{12,}", data)]
    wide = [m.decode("utf-16-le", errors="ignore") for m in re.findall(rb"(?:[\x20-\x7e\r\t]\x00){12,}", data)]
    runs = wide if sum(map(len, wide)) > sum(map(len, narrow)) else narrow
    junk = re.compile(r"(Times New Roman|Microsoft Word|Normal\.dot|Arial|Symbol|Courier New|Default Paragraph"
                      r"|Root Entry|SummaryInformation|WordDocument|CompObj|Document Summary|MSWordDoc|Word\.Document)")
    return "\n".join(r.replace("\r", "\n") for r in runs if not junk.search(r))


def document_text(path, limit=6000):
    """A document's text (as best it can be had without its program), up to about limit characters."""
    ext = Path(path).suffix.lower()
    if ext in WEB_EXTS:
        return _html_text(_decode(_read(path, limit * 8)))[:limit]
    if ext == ".docx":
        try:
            with zipfile.ZipFile(path) as z:
                return _xml_paragraphs(z.read("word/document.xml").decode("utf-8", "replace"), r"</w:p>")[:limit]
        except (OSError, KeyError, zipfile.BadZipFile):
            return ""
    if ext in (".odt", ".sxw"):
        try:
            with zipfile.ZipFile(path) as z:
                return _xml_paragraphs(z.read("content.xml").decode("utf-8", "replace"), r"</text:p>|</text:h>")[:limit]
        except (OSError, KeyError, zipfile.BadZipFile):
            return ""
    if ext in (".rtf", ".wri") and _read(path, 5).startswith(b"{\\rtf"):
        from PySide6.QtGui import QTextDocument
        from claudecore.rtf import from_rtf
        doc = QTextDocument()
        from_rtf(_decode(_read(path, limit * 20)), doc)
        return doc.toPlainText()[:limit]
    if ext in (".doc", ".wri", ".wpd"):
        return _word97_text(_read(path, max(limit * 40, 400000)))[:limit]
    if ext in TEXT_EXTS or ext in (".rtf",):
        return _decode(_read(path, limit * 2))[:limit]
    return ""


# ---- previews (worker threads) -----------------------------------------------------------------------------------
def _cache(path, tag):
    try:
        st = os.stat(path)
    except OSError:
        return None
    return THUMBS / (hashlib.sha1(f"{path}|{int(st.st_mtime)}|{st.st_size}|{tag}".encode()).hexdigest()[:20] + ".jpg")


def pdf_page(path, size=SIZE):
    """The first page of a PDF (cached)."""
    f = _cache(path, "pdf")
    if f is not None and f.exists():
        img = QImage(str(f))
        if not img.isNull():
            return img
    from PySide6.QtPdf import QPdfDocument
    doc = QPdfDocument()
    if doc.load(str(path)) != QPdfDocument.Error.None_ or doc.pageCount() < 1:
        return QImage()
    page = doc.pagePointSize(0)
    if page.width() <= 0 or page.height() <= 0:
        return QImage()
    scale = min(size * 1.6 / page.width(), size * 1.6 / page.height())
    img = doc.render(0, QSize(max(1, int(page.width() * scale)), max(1, int(page.height() * scale))))
    doc.close()
    if img.isNull():
        return img
    flat = QImage(img.size(), QImage.Format_RGB32)
    flat.fill(Qt.white)
    p = QPainter(flat)
    p.drawImage(0, 0, img)
    p.end()
    try:
        THUMBS.mkdir(parents=True, exist_ok=True)
        flat.save(str(f), "JPG", 88)
    except (OSError, TypeError):
        pass
    return flat


def text_page(text, size=SIZE):
    """The opening lines of a document typed onto a little page."""
    w, h = int(size * 0.74), size
    img = QImage(w * 2, h * 2, QImage.Format_RGB32)            # drawn at twice the size, for crisp tiny type
    img.fill(Qt.white)
    p = QPainter(img)
    p.setRenderHint(QPainter.TextAntialiasing)
    p.setPen(QColor("#303030"))
    font = QFont("Tahoma")
    font.setPixelSize(13)
    p.setFont(font)
    lines = [ln.strip() for ln in text.replace("\t", "    ").splitlines()]
    body = "\n".join(ln for ln in lines if ln)[:1400]
    p.drawText(QRectF(14, 14, w * 2 - 28, h * 2 - 28), Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop, body)
    p.end()
    return img


def preview(path, kind):
    """What a tile shows: a picture's thumbnail, a PDF's first page, or a page with the document's first lines."""
    from .miscfurry import thumb
    if kind == "piece":
        return thumb(path)
    if Path(path).suffix.lower() in PDF_EXTS:
        return pdf_page(path)
    text = document_text(path, 1400).strip()
    return text_page(text) if text else QImage()


def folder_peek(folder):
    """A preview of the first document (or picture) just inside a folder."""
    dirs, files, _hidden = listing(folder, "pictures", "name")
    for name, kind in files[:4]:
        if Path(name).suffix.lower() in SHEET_EXTS:
            continue
        img = preview(Path(folder) / name, kind)
        if not img.isNull():
            return img
    return QImage()


# ---- tiles ------------------------------------------------------------------------------------------------------
def _page_tile(node, img, size=SIZE):
    """A sheet of paper with a folded corner: the preview on it, and the kind of file on a badge."""
    t = size + 20
    pm = QPixmap(t, t)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    has = img is not None and not img.isNull()
    ph = size - 6
    pw = ph * 0.74
    if has and img.width() > img.height():                          # a landscape PDF page
        pw, ph = size - 6, (size - 6) * img.height() / img.width()
    sheet = QRectF((t - pw) / 2, 6 + (size - 6 - ph) / 2, pw, ph)
    fold = min(18.0, pw * 0.16)
    path = QPainterPath()
    path.moveTo(sheet.topLeft())
    path.lineTo(sheet.right() - fold, sheet.top())
    path.lineTo(sheet.right(), sheet.top() + fold)
    path.lineTo(sheet.bottomRight())
    path.lineTo(sheet.bottomLeft())
    path.closeSubpath()
    p.fillPath(path.translated(3, 4), QColor(0, 0, 0, 60))
    p.setPen(QPen(QColor("#A8A498"), 1))
    p.setBrush(QColor("white"))
    p.drawPath(path)
    if has:
        p.save()
        p.setClipPath(path)
        inner = sheet.adjusted(1, 1, -1, -1)
        p.drawImage(inner, img, QRectF(0, 0, img.width(), min(img.height(), img.width() * inner.height()
                                                                / max(1.0, inner.width()))))
        p.restore()
    elif node.kind == "file" or img is not None:
        p.setPen(QPen(QColor("#C8C4B8"), 1))
        for i in range(6):                                              # ruled lines on a page with nothing to show
            y = sheet.top() + 26 + i * 12
            p.drawLine(QPointF(sheet.left() + 12, y), QPointF(sheet.right() - 12, y))
    else:
        p.setPen(QColor("#A09880"))
        p.setFont(QFont("Tahoma", 8))
        p.drawText(sheet, Qt.AlignCenter, "Loading...")
    corner = QPainterPath()
    corner.moveTo(sheet.right() - fold, sheet.top())
    corner.lineTo(sheet.right() - fold, sheet.top() + fold)
    corner.lineTo(sheet.right(), sheet.top() + fold)
    corner.closeSubpath()
    p.setPen(QPen(QColor("#A8A498"), 1))
    p.setBrush(QColor("#E8E4D8"))
    p.drawPath(corner)
    label, colour = badge(node.path.name)
    p.setFont(QFont("Tahoma", 7, QFont.Bold))
    bw = max(30, p.fontMetrics().horizontalAdvance(label) + 10)
    b = QRectF(sheet.left() - 4, sheet.bottom() - 22, bw, 15)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(colour))
    p.drawRoundedRect(b, 3, 3)
    p.setPen(QColor("white"))
    p.drawText(b, Qt.AlignCenter, label)
    p.end()
    return pm


# ---- the reading pane -------------------------------------------------------------------------------------------
class ReadingPane(QWidget):
    """One document: text, web pages, RTF, Word and OpenOffice as text in a browser, PDFs as pages."""

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.path = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        bar = QWidget()
        bar.setObjectName("readbar")
        bar.setAttribute(Qt.WA_StyledBackground)
        bar.setStyleSheet("QWidget#readbar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FDFDFB,"
                          " stop:1 #E3E0D2); border-bottom: 1px solid #A0A0A0; }"
                          "QToolButton { font: 11px Tahoma; padding: 3px 8px; border: 1px solid transparent;"
                          " border-radius: 3px; } QToolButton:hover { border-color: #C0BCA8; background: white; }"
                          "QLabel { font: bold 11px Tahoma; color: #303030; }")
        row = QHBoxLayout(bar)
        row.setContentsMargins(4, 3, 6, 3)
        back = QToolButton()
        back.setText("◄ Back to the folder")
        back.clicked.connect(owner.close_reading)
        row.addWidget(back)
        row.addSpacing(10)
        self.title = QLabel()
        row.addWidget(self.title, 1)
        self.note = QLabel()
        self.note.setStyleSheet("font: 11px Tahoma; color: #806040;")
        row.addWidget(self.note)
        self.open_btn = QToolButton()
        self.open_btn.setText("Open in its program")
        self.open_btn.clicked.connect(lambda: self.path and host.open_file(owner.desktop, self.path))
        row.addWidget(self.open_btn)
        lay.addWidget(bar)
        self.views = QStackedWidget()
        self.text = QTextBrowser()
        self.text.setOpenLinks(False)
        self.text.setStyleSheet("QTextBrowser { background: white; border: none; padding: 12px; }")
        self.views.addWidget(self.text)
        self.pdf = None
        lay.addWidget(self.views, 1)

    def _pdf_view(self):
        if self.pdf is None:
            from PySide6.QtPdf import QPdfDocument
            from PySide6.QtPdfWidgets import QPdfView
            self.pdf_doc = QPdfDocument(self)
            self.pdf = QPdfView()
            self.pdf.setDocument(self.pdf_doc)
            self.pdf.setPageMode(QPdfView.PageMode.MultiPage)
            self.pdf.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            self.pdf.setStyleSheet("QPdfView { background: #808080; border: none; }")
            self.views.addWidget(self.pdf)
        return self.pdf

    def show_document(self, path):
        """Returns False if it can't be shown here (the caller hands it to the computer's program instead)."""
        path = Path(path)
        ext = path.suffix.lower()
        self.path = path
        self.title.setText(path.name)
        self.note.setText("")
        if ext in PDF_EXTS:
            view = self._pdf_view()
            if self.pdf_doc.load(str(path)) != self.pdf_doc.Error.None_:
                return False
            self.views.setCurrentWidget(view)
            return True
        if ext in SHEET_EXTS:
            return False
        self.text.clear()
        self.text.setFont(QFont("Lucida Console", 10) if ext in TEXT_EXTS else QFont("Times New Roman", 12))
        doc = self.text.document()
        doc.setBaseUrl(QUrl.fromLocalFile(str(path)))
        if ext in WEB_EXTS:
            self.text.setHtml(_decode(_read(path, MAX_READ)))
        elif ext in (".rtf", ".wri") and _read(path, 5).startswith(b"{\\rtf"):
            from claudecore.rtf import from_rtf
            from_rtf(_decode(_read(path, MAX_READ)), doc)
        elif ext in TEXT_EXTS:
            self.text.setPlainText(_decode(_read(path, MAX_READ)))
        else:
            text = document_text(path, MAX_READ)
            if not text.strip():
                return False
            self.text.setPlainText(text)
            self.note.setText("Text only  ")
        self.views.setCurrentWidget(self.text)
        self.text.verticalScrollBar().setValue(0)
        return True

    def clear(self):
        self.text.clear()
        if self.pdf is not None:
            self.pdf_doc.close()


# ---- the program --------------------------------------------------------------------------------------------------
class DocumentGallery(CDViewer):
    TITLE = "Personal Document Gallery"
    PLACE = "Personal Texts and Docs"
    RACK = "Home"

    def find_root(self):
        return docs_root()

    def __init__(self, desktop):
        try:
            saved = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            saved = {}
        self.show_mode = saved.get("show") if saved.get("show") in SHOWS else "pictures"
        self.sort_mode = saved.get("sort") if saved.get("sort") in SORTS else "name"
        super().__init__(desktop)
        self.reading = ReadingPane(self)
        self.stack.addWidget(self.reading)
        if self.root is None:
            self.status.setText("Put a 'Personal Texts and Docs' folder on drive E: (Local Storage).")

    def _bar(self):
        bar = super()._bar()
        row = bar.layout()
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
        """Home is the Personal Texts and Docs folder itself."""
        if self.root is None:
            return
        self.history.clear()
        self.here = self.disc = None
        self.show_folder(self.root, remember=False)
        self.back_btn.setEnabled(False)

    def folder_contents(self, path):
        folder = Path(path)
        dirs, files, hidden = listing(folder, self.show_mode, self.sort_mode)
        nodes = [Node(folder / d, "folder", d) for d in dirs]
        nodes += [Node(folder / n, kind, n) for n, kind in files]
        docs = sum(1 for _n, k in files if k == "doc")
        pics = sum(1 for _n, k in files if k == "piece")
        return folder, nodes, [("folder", len(dirs)), ("document", docs), ("picture", pics),
                               ("other file", len(files) - docs - pics), ("hidden item", hidden)]

    def show_folder(self, path, remember=True):
        super().show_folder(path, remember)
        if Path(path) == self.root:
            self.back_btn.setEnabled(bool(self.history))

    def crumbs(self, folder):
        try:
            return list(Path(folder).relative_to(self.root).parts)
        except ValueError:
            return [Path(folder).name]

    def open_node(self, node):
        if node.kind == "doc":
            before = self.status.text()
            self.status.setText(f"Opening {node.path.name}...")
            if self.reading.show_document(node.path):
                self.stack.setCurrentWidget(self.reading)
                self.reading.text.setFocus()
                if self.frame is not None:
                    self.frame.set_title(f"{node.path.name} - {self.TITLE}")
            else:
                host.open_file(self.desktop, node.path)
            self.status.setText(before)
        elif node.kind == "file":
            host.open_file(self.desktop, node.path)
        else:
            super().open_node(node)

    def close_reading(self):
        self.reading.clear()
        self.stack.setCurrentIndex(0)
        if self.frame is not None and self.here is not None:
            crumbs = self.crumbs(self.here)
            self.frame.set_title(f"{crumbs[-1] if crumbs else self.PLACE} - {self.TITLE}")

    def keyPressEvent(self, event):
        if self.stack.currentWidget() is self.reading and event.key() in (Qt.Key_Escape, Qt.Key_Backspace):
            self.close_reading()
            return
        super().keyPressEvent(event)

    # ---- tiles ------------------------------------------------------------------------------------------------
    def want_thumb(self, node, callback=None):
        key = node.key
        if callback is not None:
            if self.thumbs.get(key) is not None:
                callback(self.thumbs[key])
                return
            self.waiting.setdefault(key, []).append(callback)
        if key in self.thumbs or node.kind == "file":
            return
        self.thumbs[key] = None
        path, kind = node.path, node.kind
        if kind == "folder":
            job = lambda: folder_peek(path)
        elif kind == "doc" and path.suffix.lower() in SHEET_EXTS:
            job = QImage                                   # spreadsheets: just the badge
        else:
            job = lambda: preview(path, kind)
        self.loader.request(key, job)

    def paint_tile(self, item):
        from .miscfurry import _folder_tile, _picture_tile
        node = item.data(Qt.UserRole)
        img = self.thumbs.get(node.key) if node.key in self.thumbs else None
        if node.kind == "folder":
            pm = _folder_tile(node, img, SIZE)
        elif node.kind == "piece":
            pm = _picture_tile(node, img, SIZE)
        else:
            pm = _page_tile(node, img, SIZE)
        item.setIcon(QIcon(pm))

    def closeEvent(self, event):
        self.reading.clear()
        super().closeEvent(event)


_open = {}


def open_documents(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = DocumentGallery(desktop)
        win = host.window(desktop, DocumentGallery.TITLE, body, docs_icon(), (900, 640))
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
