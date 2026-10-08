"""Printing to ClaudeXP's dot matrix printer, which 'prints' PDFs into E:\\Printed (the Local Storage folder).

Text comes out like a real dot matrix printout: monospaced, on green-bar continuous paper with tractor
feed holes. Web pages, chats and pictures print as ordinary pages. While a job prints, a printer icon
sits in the tray and the printer sound plays (longer for more pages).
"""
import random
from pathlib import Path

from PySide6.QtCore import QMarginsF, QObject, QPointF, QRectF, QSizeF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPageLayout, QPageSize, QPainter, QPdfWriter, QPen, QPixmap, QTextDocument
from PySide6.QtWidgets import (QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
                               QRadioButton, QSpinBox, QTreeWidget, QTreeWidgetItem, QVBoxLayout)
from shiboken6 import isValid

from . import clock, sound
from .wm import XPWindow

PRINTER = "Epson LQ-570+ (Dot Matrix)"
COLUMNS, LINES = 80, 60            # a dot matrix page: 80 columns, 60 lines at 6 lines per inch
SECONDS_PER_PAGE = 9


def printed_folder():
    from .explorer import vfs
    folder = vfs.local_storage() / "Printed"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def printer_icon(size=32, busy=False):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    p.setPen(QPen(QColor("#404040"), max(1.0, s)))
    p.setBrush(QColor("#FFFFFF"))
    p.drawRect(QRectF(9 * s, 3 * s, 14 * s, 11 * s))          # paper in
    p.setBrush(QColor("#C9C5B9"))
    p.drawRoundedRect(QRectF(3 * s, 12 * s, 26 * s, 12 * s), 2 * s, 2 * s)
    p.setBrush(QColor("#FFFFFF"))
    p.drawRect(QRectF(8 * s, 21 * s, 16 * s, 9 * s))          # paper out
    p.setPen(QPen(QColor("#9A9A9A"), max(1.0, s * 0.8)))
    for y in (24, 26.5):
        p.drawLine(QPointF(10 * s, y * s), QPointF(22 * s, y * s))   # printed lines
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#3BB54A" if busy else "#2A7A2A"))
    p.drawEllipse(QRectF(24 * s, 15 * s, 3 * s, 3 * s))
    p.end()
    return pm


# ---- rendering a job to PDF ------------------------------------------------------------------------

def _wrap(text, width=COLUMNS):
    lines = []
    for raw in text.replace("\t", "    ").splitlines() or [""]:
        while len(raw) > width:
            cut = raw.rfind(" ", 0, width)
            cut = cut if cut > width // 2 else width
            lines.append(raw[:cut])
            raw = raw[cut:].lstrip()
        lines.append(raw)
    return lines


def text_pages(text):
    lines = _wrap(text)
    return max(1, -(-len(lines) // LINES))


def render_text(text, path, title, copies=1):
    """Dot matrix style: green-bar continuous paper, tractor holes, a monospaced 'pin' font."""
    writer = QPdfWriter(str(path))
    writer.setTitle(title)
    writer.setCreator(PRINTER)
    writer.setPageSize(QPageSize(QPageSize.Letter))
    writer.setPageMargins(QMarginsF(0, 0, 0, 0))
    writer.setResolution(300)
    p = QPainter(writer)
    w, h = writer.width(), writer.height()
    dpi = 300
    left, right = int(0.75 * dpi), int(0.75 * dpi)
    top = int(0.5 * dpi)
    line_h = dpi / 6
    font = QFont("Courier New")
    font.setPixelSize(int(line_h * 0.8))
    font.setBold(True)
    lines = _wrap(text)
    pages = ([lines[i:i + LINES] for i in range(0, len(lines), LINES)] or [[]]) * copies
    for n, page in enumerate(pages):
        if n:
            writer.newPage()
        # green bars every three lines
        for band in range(0, LINES + 6, 6):
            p.fillRect(QRectF(left - 20, top + band * line_h, w - left - right + 40, 3 * line_h), QColor("#DDEFD9"))
        # tractor feed strips with their sprocket holes, and the perforations
        p.setPen(QPen(QColor("#B0B0B0"), 2, Qt.DashLine))
        p.drawLine(int(0.5 * dpi), 0, int(0.5 * dpi), h)
        p.drawLine(w - int(0.5 * dpi), 0, w - int(0.5 * dpi), h)
        p.drawLine(0, 2, w, 2)
        p.setPen(QPen(QColor("#C8C8C8"), 2))
        p.setBrush(QColor("#F4F4F4"))
        y = dpi / 4
        while y < h:
            p.drawEllipse(QRectF(0.25 * dpi - 22, y - 22, 44, 44))
            p.drawEllipse(QRectF(w - 0.25 * dpi - 22, y - 22, 44, 44))
            y += dpi / 2
        p.setFont(font)
        p.setPen(QColor(35, 35, 45))
        for i, line in enumerate(page):
            # a slightly uneven ribbon: each line a touch darker or lighter
            p.setOpacity(random.uniform(0.78, 0.95))
            p.drawText(int(left), int(top + (i + 0.8) * line_h), line)
        p.setOpacity(1.0)
    p.end()
    return len(pages) // copies


def render_document(doc: QTextDocument, path, title):
    """A web page or chat: the document as it looks on screen, on Letter pages."""
    writer = QPdfWriter(str(path))
    writer.setTitle(title)
    writer.setCreator(PRINTER)
    writer.setPageSize(QPageSize(QPageSize.Letter))
    writer.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Millimeter)
    writer.setResolution(96)        # lay the page out at screen size, so it looks like it did on screen
    copy = doc.clone()
    copy.setPageSize(QSizeF(writer.width(), writer.height()))
    copy.print_(writer)
    return max(1, copy.pageCount())


def render_image(image_path, path, title, copies=1):
    writer = QPdfWriter(str(path))
    writer.setTitle(title)
    writer.setCreator(PRINTER)
    writer.setPageSize(QPageSize(QPageSize.Letter))
    writer.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Millimeter)
    pm = QPixmap(str(image_path))
    p = QPainter(writer)
    for copy in range(copies):
        if copy:
            writer.newPage()
        _draw_image_page(p, writer, pm, image_path)
    p.end()
    return 1


def _draw_image_page(p, writer, pm, image_path):
    if not pm.isNull():
        area = QRectF(0, 0, writer.width(), writer.height() * 0.9)
        scale = min(area.width() / pm.width(), area.height() / pm.height())
        w, h = pm.width() * scale, pm.height() * scale
        p.drawPixmap(QRectF((area.width() - w) / 2, 0, w, h), pm, QRectF(pm.rect()))
        font = QFont("Arial")
        font.setPixelSize(int(writer.height() * 0.015))
        p.setFont(font)
        p.drawText(QRectF(0, h + 40, writer.width(), 200), Qt.AlignHCenter, Path(image_path).name)


# ---- the print spooler ----------------------------------------------------------------------------------

class Job:
    def __init__(self, title, kind, content, pages, copies):
        self.title, self.kind, self.content = title, kind, content
        self.pages, self.copies = pages, copies
        self.status = "Spooling"
        self.submitted = clock.now()
        self.output = None


class Spooler(QObject):
    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.jobs = []
        self.current = None
        self.tray = None
        self.queue_win = None
        self.blink = QTimer(self)
        self.blink.timeout.connect(self._blink)
        self.blink_on = False

    def submit(self, job):
        self.jobs.append(job)
        self._show_tray()
        self._refresh_queue()
        if self.current is None:
            QTimer.singleShot(600, self._next)

    def _next(self):
        pending = [j for j in self.jobs if j.status in ("Spooling", "Waiting")]
        if not pending:
            self.current = None
            self._hide_tray()
            return
        job = self.current = pending[0]
        job.status = "Printing"
        self._refresh_queue()
        self.blink.start(400)
        try:
            job.output = self._unique(printed_folder(), job.title)
            if job.kind == "text":
                job.pages = render_text(job.content, job.output, job.title, job.copies)
            elif job.kind == "document":
                job.pages = render_document(job.content, job.output, job.title)
            else:
                job.pages = render_image(job.content, job.output, job.title, job.copies)
        except Exception as e:
            job.status = f"Error - {e}"
            self.blink.stop()
            self.current = None
            self._refresh_queue()
            QTimer.singleShot(200, self._next)
            return
        seconds = min(55, max(6, job.pages * job.copies * SECONDS_PER_PAGE))
        name = "printer_sound1.mp3" if seconds <= 19 else "printer_sound2.mp3"
        sound.play_clip(name, int(seconds * 1000))
        QTimer.singleShot(int(seconds * 1000), lambda: self._done(job))

    def _done(self, job):
        from .explorer import vfs
        job.status = "Printed"
        self.blink.stop()
        self._refresh_queue()
        if self.tray is not None:
            where = vfs.to_virtual(job.output) or str(job.output)
            self.tray.showMessage("Document Printed",
                                  f"'{job.title}' ({job.pages} page{'s' if job.pages != 1 else ''}) was printed on "
                                  f"{PRINTER} and saved as {where}", None, 8000)
        self.current = None
        QTimer.singleShot(2000, self._next)

    @staticmethod
    def _unique(folder, title):
        safe = "".join(c for c in title if c not in '\\/:*?"<>|').strip() or "Document"
        if Path(safe).suffix.lower() in (".txt", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".htm", ".html", ".log"):
            safe = Path(safe).stem   # 'photo.jpg' prints to 'photo.pdf'
        safe = safe[:60]
        target = folder / f"{safe}.pdf"
        n = 2
        while target.exists():
            target = folder / f"{safe} ({n}).pdf"
            n += 1
        return target

    # ---- tray icon -----------------------------------------------------------------------------------
    def _show_tray(self):
        from .tray import TrayIcon
        if self.tray is None:
            self.tray = TrayIcon(self.desktop, QIcon(printer_icon(16)))
            self.tray.activated.connect(lambda _r: self.open_queue())
            self.tray.show()
        n = sum(1 for j in self.jobs if j.status not in ("Printed",) and not j.status.startswith("Error"))
        self.tray.setToolTip(f"{n} document(s) pending for {self._user()}")

    def _hide_tray(self):
        if self.tray is not None:
            tray, self.tray = self.tray, None
            QTimer.singleShot(9000, lambda: (tray.hide(), tray.deleteLater()) if isValid(tray) else None)

    def _blink(self):
        self.blink_on = not self.blink_on
        if self.tray is not None:
            self.tray.setIcon(QIcon(printer_icon(16, self.blink_on)))

    @staticmethod
    def _user():
        from .user import user_name
        return user_name()

    # ---- the print queue window --------------------------------------------------------------------------
    def open_queue(self):
        if self.queue_win is not None and isValid(self.queue_win):
            self.desktop.open_window(self.queue_win)
            return
        tree = QTreeWidget()
        tree.setHeaderLabels(["Document Name", "Status", "Owner", "Pages", "Submitted"])
        tree.setRootIsDecorated(False)
        tree.setColumnWidth(0, 220)
        tree.setStyleSheet("QTreeWidget { background: white; font-family: Tahoma; font-size: 11px; }")
        self.queue_tree = tree
        self.queue_win = XPWindow(self.desktop, PRINTER, tree, QIcon(printer_icon(16)), size=(600, 260))
        self.desktop.open_window(self.queue_win)
        self._refresh_queue()

    def _refresh_queue(self):
        if self.tray is not None:
            self._show_tray()
        if self.queue_win is None or not isValid(self.queue_win):
            return
        tree = self.queue_tree
        tree.clear()
        for job in reversed(self.jobs[-30:]):
            when = f"{clock.time_text(job.submitted)}  {job.submitted.month}/{job.submitted.day}/{job.submitted.year}"
            item = QTreeWidgetItem([job.title, job.status, self._user(), str(job.pages), when])
            tree.addTopLevelItem(item)


_spooler = None


def spooler(desktop):
    global _spooler
    if _spooler is None or not isValid(_spooler):
        _spooler = Spooler(desktop)
    return _spooler


# ---- the Print dialog --------------------------------------------------------------------------------------

def print_dialog(desktop, title, kind, content, pages=1):
    """XP's Print dialog. kind: 'text' (str), 'document' (QTextDocument) or 'image' (path)."""
    from .network import DialogBody, _fixed_window
    body = DialogBody()
    v = QVBoxLayout(body)
    v.setContentsMargins(12, 12, 12, 12)
    group = QGroupBox("Select Printer")
    gv = QVBoxLayout(group)
    printers = QListWidget()
    printers.setViewMode(QListWidget.IconMode)
    printers.setFixedHeight(76)
    printers.setStyleSheet("QListWidget { background: white; }")
    item = QListWidgetItem(QIcon(printer_icon(32)), PRINTER)
    printers.addItem(item)
    printers.setCurrentItem(item)
    gv.addWidget(printers)
    from .explorer import vfs
    status = QLabel(f"Status:  Ready\nLocation:  {vfs.to_virtual(printed_folder()) or 'E:'}  (prints to PDF)\n"
                    "Comment:  9-pin dot matrix, continuous feed")
    status.setStyleSheet("font-family: Tahoma; font-size: 11px;")
    gv.addWidget(status)
    v.addWidget(group)
    row = QHBoxLayout()
    rng = QGroupBox("Page Range")
    rv = QVBoxLayout(rng)
    all_pages = QRadioButton("A&ll")
    all_pages.setChecked(True)
    rv.addWidget(all_pages)
    rv.addWidget(QLabel(f"({pages} page{'s' if pages != 1 else ''})"))
    row.addWidget(rng)
    copies_box = QGroupBox("Copies")
    cv = QHBoxLayout(copies_box)
    copies_label = QLabel("Number of &copies:")
    cv.addWidget(copies_label)
    copies = QSpinBox()
    copies.setRange(1, 9)
    copies_label.setBuddy(copies)
    cv.addWidget(copies)
    row.addWidget(copies_box)
    v.addLayout(row)
    buttons = QHBoxLayout()
    buttons.addStretch()
    ok, cancel = QPushButton("&Print"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(75, 23)
        buttons.addWidget(b)
    v.addLayout(buttons)
    body.setFixedWidth(420)
    holder = {}

    def close():
        if holder.get("win") is not None:
            desktop.close_window(holder.pop("win"))

    def go():
        close()
        spooler(desktop).submit(Job(title, kind, content, pages, copies.value()))

    ok.clicked.connect(go)
    cancel.clicked.connect(close)
    holder["win"] = _fixed_window(desktop, "Print", body, close)
    holder["win"].icon = QIcon(printer_icon(16))
    desktop.open_window(holder["win"])
    ok.setFocus()


def print_text(desktop, title, text):
    print_dialog(desktop, title, "text", text, text_pages(text))


def print_document(desktop, title, doc):
    probe = doc.clone()
    probe.setPageSize(QSizeF(703, 942))     # a Letter page at 96 dpi, minus the margins
    print_dialog(desktop, title, "document", doc, max(1, probe.pageCount()))


def print_image(desktop, path):
    print_dialog(desktop, Path(path).name, "image", str(path), 1)


def print_file(desktop, path):
    """Explorer's right-click Print."""
    from . import display
    path = Path(path)
    ext = path.suffix.lower()
    if ext in display.IMAGE_EXTS:
        print_image(desktop, path)
    elif ext in (".htm", ".html"):
        doc = QTextDocument()
        doc.setHtml(path.read_text(encoding="utf-8", errors="replace"))
        print_document(desktop, path.name, doc)
    else:
        print_text(desktop, path.name, path.read_text(encoding="utf-8", errors="replace"))


# ---- Printers and Faxes -------------------------------------------------------------------------------------

def printers_and_faxes(desktop):
    from PySide6.QtCore import QSize
    lst = QListWidget()
    lst.setViewMode(QListWidget.IconMode)
    lst.setIconSize(QSize(32, 32))
    lst.setGridSize(QSize(170, 80))
    lst.setWordWrap(True)
    lst.setStyleSheet("QListWidget { background: white; border: none; font-family: Tahoma; font-size: 11px; }")
    lst.addItem(QListWidgetItem(QIcon(printer_icon(32)), f"{PRINTER}\nReady (prints to E:\\Printed)"))
    lst.itemActivated.connect(lambda _i: spooler(desktop).open_queue())
    win = XPWindow(desktop, "Printers and Faxes", lst, QIcon(printer_icon(16)), size=(520, 300))
    desktop.open_window(win)
    sound.play("navigate")
    return win
