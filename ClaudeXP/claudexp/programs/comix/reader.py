"""FurComix Reader: the shelves of comics on E: as a gallery of covers, and a CDisplay-style page viewer.

Library: one tile per series or comic (shelves draw as a stack), covers fade in as they scroll into view, a
'Continue Reading' row at the top, and a filter box. Reading: black backdrop, Fit Page / Fit Width / two-page
spreads, a filmstrip of page thumbnails, and the next pages are decoded ahead so turning a page is instant.

Keys while reading: Right/Space/PgDn next (Space and the wheel scroll a tall page first), Left/Backspace/PgUp back,
Home/End, W fit width, P fit page, D two pages, F filmstrip, Esc back to the shelf. Double-click: full screen."""
import math
from collections import OrderedDict

from PySide6.QtCore import QObject, QPointF, QRectF, QRunnable, QSize, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QLabel, QLineEdit, QListView, QListWidget,
                               QListWidgetItem, QStackedWidget, QToolButton, QVBoxLayout, QWidget)
from shiboken6 import isValid

from ...wm import XPWindow
from . import library as L

TILE = QSize(132, 186)
STRIP = QSize(60, 84)
PRELOAD = 3


def comix_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#5A3A00"), 1))
    p.setBrush(QColor("#F7F2E4"))
    p.drawRect(QRectF(7.5, 4.5, 20, 25))                     # back page
    g = QLinearGradient(0, 2, 0, 28)
    g.setColorAt(0, QColor("#FFE04A"))
    g.setColorAt(1, QColor("#F09A10"))
    p.setBrush(g)
    p.drawRect(QRectF(3.5, 2.5, 20, 25))
    burst = QPolygonF()
    centre = QRectF(3.5, 2.5, 20, 25).center()
    for k in range(16):
        r = 8.5 if k % 2 == 0 else 4.5
        a = k * math.pi / 8
        burst.append(centre + QPointF(r * math.cos(a), r * math.sin(a)))
    p.setBrush(QColor("#E8261C"))
    p.setPen(QPen(QColor("#7A0A00"), 0.8))
    p.drawPolygon(burst)
    p.setPen(QColor("white"))
    f = QFont("Arial Black", 5)
    p.setFont(f)
    p.drawText(QRectF(3.5, 2.5, 20, 25), Qt.AlignCenter, "POW")
    p.end()
    return QIcon(pm)


# ---- background image loading ---------------------------------------------------------------------------------

class _Signals(QObject):
    done = Signal(object, object)                # key, QImage


class _Job(QRunnable):
    def __init__(self, key, fn, signals):
        super().__init__()
        self.key, self.fn, self.signals = key, fn, signals
        self.setAutoDelete(True)

    def run(self):
        try:
            img = self.fn()
        except Exception:                        # a damaged file just shows no picture
            img = QImage()
        try:
            self.signals.done.emit(self.key, img)
        except RuntimeError:                     # the window closed meanwhile
            pass


class Loader(QObject):
    """Runs image jobs on a small thread pool, once per key; results arrive on the UI thread."""
    loaded = Signal(object, object)

    def __init__(self, parent, threads=3):
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(threads)
        self.signals = _Signals()
        self.signals.done.connect(self._done)
        self.pending = set()

    def request(self, key, fn, front=False):
        if key in self.pending:
            return
        self.pending.add(key)
        self.pool.start(_Job(key, fn, self.signals), 1 if front else 0)

    def _done(self, key, img):
        self.pending.discard(key)
        self.loaded.emit(key, img)

    def clear(self):
        self.pool.clear()
        self.pending.clear()


# ---- tiles ---------------------------------------------------------------------------------------------------

def _tile_pixmap(entry, cover, progress):
    """A cover on the shelf: a single comic, or a stack for a series; a reading bar under it."""
    pm = QPixmap(TILE)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    w, h = (L.THUMB.width(), L.THUMB.height())
    if cover is not None and not cover.isNull():
        w, h = cover.width(), cover.height()
    x = (TILE.width() - w) // 2
    y = TILE.height() - h - 10
    if entry.kind == "shelf":
        for off, shade in ((8, "#C8C2B0"), (4, "#E0DACA")):
            p.setPen(QPen(QColor("#807A68"), 1))
            p.setBrush(QColor(shade))
            p.drawRect(QRectF(x + off + 0.5, y - off + 0.5, w - 1, h - 1))
        x -= 2
    p.fillRect(QRectF(x + 3, y + 3, w, h), QColor(0, 0, 0, 60))                 # shadow
    if cover is not None and not cover.isNull():
        p.drawImage(QRectF(x, y, w, h), cover)
    else:
        g = QLinearGradient(0, y, 0, y + h)
        g.setColorAt(0, QColor("#F4F1E6"))
        g.setColorAt(1, QColor("#D8D2BE"))
        p.fillRect(QRectF(x, y, w, h), g)
        p.setPen(QColor("#9A927A"))
        p.setFont(QFont("Tahoma", 8))
        p.drawText(QRectF(x + 6, y, w - 12, h), Qt.AlignCenter | Qt.TextWordWrap,
                   "Loading..." if cover is None else entry.name)
    p.setPen(QPen(QColor("#404040"), 1))
    p.setBrush(Qt.NoBrush)
    p.drawRect(QRectF(x + 0.5, y + 0.5, w - 1, h - 1))
    if progress is not None:
        page, pages = progress
        done = pages and page >= pages - 1
        bar = QRectF(x, TILE.height() - 6, w, 5)
        p.fillRect(bar, QColor("#D0D0D0"))
        p.fillRect(QRectF(bar.x(), bar.y(), bar.width() * (1 if done else (page + 1) / max(1, pages)), 5),
                   QColor("#2FA84F") if done else QColor("#3A6EE8"))
        if done:
            p.setBrush(QColor("#2FA84F"))
            p.setPen(QPen(Qt.white, 1.5))
            p.drawEllipse(QRectF(x + w - 20, y + 4, 16, 16))
            p.drawPolyline(QPolygonF([QPointF(x + w - 16, y + 12), QPointF(x + w - 13, y + 15),
                                      QPointF(x + w - 8, y + 8)]))
    p.end()
    return pm


class Gallery(QListWidget):
    """A grid of tiles whose covers are requested only once they're on screen."""
    opened = Signal(object)

    def __init__(self, owner, tile=TILE, flow_lr=True, single_row=False):
        super().__init__()
        self.owner = owner
        self.setViewMode(QListView.IconMode)
        self.setIconSize(tile)
        self.setGridSize(QSize(tile.width() + 22, tile.height() + 40))
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setUniformItemSizes(True)
        self.setWordWrap(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        if single_row:
            self.setFlow(QListView.LeftToRight)
            self.setWrapping(False)
            self.setFixedHeight(tile.height() + 62)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("QListWidget { background: white; border: none; font: 11px Tahoma; }"
                           "QListWidget::item:selected { background: #316AC5; color: white; }")
        self.itemActivated.connect(lambda item: self.opened.emit(item.data(Qt.UserRole)))
        self.verticalScrollBar().valueChanged.connect(self.request_visible)
        self.horizontalScrollBar().valueChanged.connect(self.request_visible)
        self._timer = QTimer(self, singleShot=True, interval=60, timeout=self._request_now)

    def fill(self, entries):
        self.clear()
        for e in entries:
            item = QListWidgetItem(e.name)
            item.setData(Qt.UserRole, e)
            item.setToolTip(e.name)
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignTop)
            self.addItem(item)
            self.owner.paint_tile(item)
        self.request_visible()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.request_visible()

    def showEvent(self, event):
        super().showEvent(event)
        self.request_visible()

    def request_visible(self, *_):
        self._timer.start()

    def _request_now(self):
        view = self.viewport().rect().adjusted(0, -TILE.height(), 0, TILE.height())      # and a row either side
        for i in range(self.count()):
            item = self.item(i)
            if view.intersects(self.visualItemRect(item)):
                self.owner.want_cover(item.data(Qt.UserRole))

    def items_for(self, key):
        return [self.item(i) for i in range(self.count()) if self.item(i).data(Qt.UserRole).key == key]


# ---- the page viewer -----------------------------------------------------------------------------------------

class Canvas(QWidget):
    """The pages on a black backdrop."""

    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.images = []                      # 1 or 2 QImages (None while loading)
        self.offset = 0                        # vertical scroll in Fit Width
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(200, 200)
        self.message = ""

    def set_pages(self, images, keep_offset=False):
        self.images = images
        if not keep_offset:
            self.offset = 0
        self.update()

    def _layout(self):
        """[(QRectF target, image)] and the total content height."""
        imgs = [i for i in self.images if i is not None and not i.isNull()]
        if not imgs:
            return [], self.height()
        W, H = self.width(), self.height()
        total_w = sum(i.width() for i in imgs)
        max_h = max(i.height() for i in imgs)
        if self.viewer.fit == "width":
            scale = (W - 8) / total_w
        else:
            scale = min((W - 8) / total_w, (H - 8) / max_h)
        scale = min(scale, 3.0)
        out_w = total_w * scale
        x = (W - out_w) / 2
        content_h = max_h * scale
        y = max(4, (H - content_h) / 2) if content_h < H else 4 - self.offset
        rects = []
        for img in imgs:
            w, h = img.width() * scale, img.height() * scale
            rects.append((QRectF(x, y + (max_h * scale - h) / 2, w, h), img))
            x += w
        return rects, content_h + 8

    def max_offset(self):
        _r, content_h = self._layout()
        return max(0, int(content_h - self.height()))

    def scroll_by(self, dy):
        """Scroll a tall page; False when already at that end."""
        new = max(0, min(self.max_offset(), self.offset + dy))
        if new == self.offset:
            return False
        self.offset = new
        self.update()
        return True

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#101010"))
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        rects, _h = self._layout()
        for r, img in rects:
            p.drawImage(r, img)
        if not rects:
            p.setPen(QColor("#B0B0B0"))
            p.setFont(QFont("Tahoma", 10))
            p.drawText(self.rect().adjusted(40, 0, -40, 0), Qt.AlignCenter | Qt.TextWordWrap,
                       self.message or "Loading page...")

    def wheelEvent(self, event):
        dy = -event.angleDelta().y()
        if not self.scroll_by(dy):
            if dy > 0:
                self.viewer.next_page()
            elif dy < 0:
                self.viewer.prev_page(to_bottom=True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            (self.viewer.next_page if event.position().x() > self.width() * 0.35 else self.viewer.prev_page)()

    def mouseDoubleClickEvent(self, event):
        self.viewer.owner.toggle_full_screen()

    def resizeEvent(self, event):
        self.offset = min(self.offset, self.max_offset())

    def keyPressEvent(self, event):
        if not self.viewer.key(event):
            super().keyPressEvent(event)


class Viewer(QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.book = None
        self.page = 0
        self.fit = owner.state.get("fit", "page")
        self.spread = bool(owner.state.get("spread", False))
        self.cache = OrderedDict()             # page -> QImage
        self.loader = Loader(self, threads=2)
        self.loader.loaded.connect(self._loaded)
        self.strip_loader = Loader(self, threads=1)
        self.strip_loader.loaded.connect(self._strip_loaded)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.bar = self._toolbar()
        lay.addWidget(self.bar)
        self.canvas = Canvas(self)
        lay.addWidget(self.canvas, 1)
        self.strip = QListWidget()
        self.strip.setViewMode(QListView.IconMode)
        self.strip.setFlow(QListView.LeftToRight)
        self.strip.setWrapping(False)
        self.strip.setIconSize(STRIP)
        self.strip.setGridSize(QSize(STRIP.width() + 12, STRIP.height() + 22))
        self.strip.setFixedHeight(STRIP.height() + 42)
        self.strip.setMovement(QListView.Static)
        self.strip.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.strip.setStyleSheet("QListWidget { background: #2A2A2A; color: #D0D0D0; border: none;"
                                 " border-top: 1px solid #000; font: 10px Tahoma; }"
                                 "QListWidget::item:selected { background: #316AC5; color: white; }")
        self.strip.setFocusPolicy(Qt.NoFocus)
        self.strip.itemClicked.connect(lambda item: self.go(item.data(Qt.UserRole)))
        self.strip.horizontalScrollBar().valueChanged.connect(lambda *_: self._strip_timer.start())
        self._strip_timer = QTimer(self, singleShot=True, interval=80, timeout=self._strip_request)
        self.strip.setVisible(bool(owner.state.get("filmstrip", True)))
        lay.addWidget(self.strip)

    def _toolbar(self):
        bar = QWidget()
        bar.setObjectName("bar")
        bar.setAttribute(Qt.WA_StyledBackground)
        bar.setStyleSheet("QWidget#bar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FDFDFB,"
                          " stop:1 #E3E0D2); border-bottom: 1px solid #A0A0A0; }"
                          "QToolButton { font: 11px Tahoma; padding: 2px 6px; border: 1px solid transparent;"
                          " border-radius: 3px; } QToolButton:hover { border-color: #C0BCA8; background: #FFFFFF; }"
                          "QToolButton:checked { background: #D8E4F8; border-color: #7A96D0; }"
                          "QLabel { font: 11px Tahoma; color: #202020; }")
        row = QHBoxLayout(bar)
        row.setContentsMargins(4, 2, 6, 2)
        row.setSpacing(2)

        def tool(text, tip, slot, checkable=False, checked=False):
            b = QToolButton()
            b.setText(text)
            b.setToolTip(tip)
            b.setCheckable(checkable)
            b.setChecked(checked)
            b.setFocusPolicy(Qt.NoFocus)
            b.clicked.connect(slot)
            row.addWidget(b)
            return b
        tool("◄ Shelf", "Back to the shelf (Esc)", self.owner.close_book)
        row.addSpacing(8)
        tool("|◄", "First page (Home)", lambda: self.go(0))
        tool("◄", "Previous page (Left)", self.prev_page)
        self.page_label = QLabel()
        self.page_label.setMinimumWidth(110)
        self.page_label.setAlignment(Qt.AlignCenter)
        row.addWidget(self.page_label)
        tool("►", "Next page (Right, Space)", self.next_page)
        tool("►|", "Last page (End)", lambda: self.go(len(self.book.pages) - 1 if self.book else 0))
        row.addStretch(1)
        self.fit_page_btn = tool("Fit Page", "Whole page in the window (P)", lambda: self.set_fit("page"), True,
                                 self.fit == "page")
        self.fit_width_btn = tool("Fit Width", "Page as wide as the window (W)", lambda: self.set_fit("width"), True,
                                  self.fit == "width")
        self.spread_btn = tool("Two Pages", "Side-by-side spreads (D)", self.toggle_spread, True, self.spread)
        self.strip_btn = tool("Filmstrip", "Page thumbnails (F)", self.toggle_strip, True,
                              bool(self.owner.state.get("filmstrip", True)))
        return bar

    # ---- opening -----------------------------------------------------------------------------------------------
    def open(self, entry, page=0):
        self.close_book()
        self.book = L.Book(entry)
        self.cache.clear()
        self.loader.clear()
        self.strip_loader.clear()
        self.strip.clear()
        if self.book.error:
            self.canvas.message = self.book.error
            self.canvas.set_pages([])
            self.page_label.setText("")
            return
        self.canvas.message = ""
        for i, name in enumerate(self.book.pages):
            item = QListWidgetItem(str(i + 1))
            item.setData(Qt.UserRole, i)
            item.setTextAlignment(Qt.AlignHCenter)
            self.strip.addItem(item)
        self.go(min(page, len(self.book.pages) - 1))
        self._strip_timer.start()

    def close_book(self):
        if self.book is not None:
            self.loader.clear()
            self.strip_loader.clear()
            self.book.close()
            self.book = None

    # ---- pages ------------------------------------------------------------------------------------------------
    def shown(self):
        """The pages on screen: a spread pairs 1-2, 3-4... after the cover."""
        if not self.spread or self.page == 0:
            return [self.page]
        first = self.page if self.page % 2 == 1 else self.page - 1
        return [p for p in (first, first + 1) if p < len(self.book.pages)]

    def go(self, page, to_bottom=False):
        if self.book is None or not self.book.pages:
            return
        self.page = max(0, min(page, len(self.book.pages) - 1))
        if self.spread and self.page > 0 and self.page % 2 == 0:
            self.page -= 1
        pages = self.shown()
        self.canvas.set_pages([self._image(p) for p in pages])
        if to_bottom:
            self.canvas.offset = self.canvas.max_offset()
        n = len(self.book.pages)
        self.page_label.setText(f"Page {'-'.join(str(p + 1) for p in pages)} of {n}")
        self.strip.setCurrentRow(self.page)
        self.strip.scrollToItem(self.strip.item(self.page), QAbstractItemView.PositionAtCenter)
        for p in range(pages[-1] + 1, pages[-1] + 1 + PRELOAD * (2 if self.spread else 1)):
            self._image(p)
        self.owner.page_turned(self.book.entry, pages[-1], n)

    def _image(self, page):
        """The decoded page if we have it (and start decoding it if not)."""
        if page in self.cache:
            self.cache.move_to_end(page)
            return self.cache[page]
        if not 0 <= page < len(self.book.pages):
            return None
        book = self.book
        if book.entry.source == "pdf":            # QtPdf stays on the UI thread
            img = book.image(page)
            self._store(page, img)
            return img
        self.loader.request((id(book), page), lambda: book.image(page), front=page in self.shown())
        return None

    def _store(self, page, img):
        self.cache[page] = img
        while len(self.cache) > 10:
            self.cache.popitem(last=False)

    def _loaded(self, key, img):
        book_id, page = key
        if self.book is None or id(self.book) != book_id:
            return
        if img.isNull():
            img = self._broken()
        self._store(page, img)
        if page in self.shown():
            self.canvas.set_pages([self.cache.get(p) for p in self.shown()], keep_offset=True)

    @staticmethod
    def _broken():
        img = QImage(400, 560, QImage.Format_RGB32)
        img.fill(QColor("#303030"))
        p = QPainter(img)
        p.setPen(QColor("#A0A0A0"))
        p.setFont(QFont("Tahoma", 14))
        p.drawText(img.rect(), Qt.AlignCenter, "This page couldn't\nbe displayed.")
        p.end()
        return img

    def next_page(self):
        if self.book is None:
            return
        last = self.shown()[-1]
        if last + 1 < len(self.book.pages):
            self.go(last + 1)
        else:
            self.owner.finished_book()

    def prev_page(self, to_bottom=False):
        if self.book is None:
            return
        first = self.shown()[0]
        if first > 0:
            self.go(first - 1, to_bottom=to_bottom and self.fit == "width")

    # ---- view options -------------------------------------------------------------------------------------------
    def set_fit(self, fit):
        self.fit = fit
        self.fit_page_btn.setChecked(fit == "page")
        self.fit_width_btn.setChecked(fit == "width")
        self.owner.state["fit"] = fit
        self.canvas.offset = 0
        self.canvas.update()

    def toggle_spread(self):
        self.spread = not self.spread
        self.spread_btn.setChecked(self.spread)
        self.owner.state["spread"] = self.spread
        if self.book is not None:
            self.go(self.page)

    def toggle_strip(self):
        on = not self.strip.isVisible()
        self.strip.setVisible(on)
        self.strip_btn.setChecked(on)
        self.owner.state["filmstrip"] = on
        if on:
            self._strip_timer.start()

    def _strip_request(self):
        if self.book is None or not self.strip.isVisible():
            return
        view = self.strip.viewport().rect().adjusted(-200, 0, 200, 0)
        book = self.book
        for i in range(self.strip.count()):
            item = self.strip.item(i)
            if item.icon().isNull() and view.intersects(self.strip.visualItemRect(item)):
                if book.entry.source == "pdf":
                    self._strip_loaded((id(book), i), book.image(i, STRIP))
                else:
                    self.strip_loader.request((id(book), i), lambda i=i: book.image(i, STRIP))

    def _strip_loaded(self, key, img):
        book_id, i = key
        if self.book is None or id(self.book) != book_id or i >= self.strip.count():
            return
        pm = QPixmap(STRIP)
        pm.fill(Qt.transparent)
        if not img.isNull():
            p = QPainter(pm)
            s = img.scaled(STRIP, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            p.drawImage((STRIP.width() - s.width()) // 2, STRIP.height() - s.height(), s)
            p.end()
        self.strip.item(i).setIcon(QIcon(pm))

    def key(self, event):
        k = event.key()
        if k in (Qt.Key_Right, Qt.Key_PageDown, Qt.Key_N):
            self.next_page()
        elif k == Qt.Key_Space:
            if not self.canvas.scroll_by(int(self.canvas.height() * 0.85)):
                self.next_page()
        elif k in (Qt.Key_Left, Qt.Key_PageUp, Qt.Key_Backspace):
            self.prev_page()
        elif k == Qt.Key_Down:
            if not self.canvas.scroll_by(60):
                self.next_page()
        elif k == Qt.Key_Up:
            self.canvas.scroll_by(-60)
        elif k == Qt.Key_Home:
            self.go(0)
        elif k == Qt.Key_End and self.book:
            self.go(len(self.book.pages) - 1)
        elif k == Qt.Key_W:
            self.set_fit("width")
        elif k == Qt.Key_P:
            self.set_fit("page")
        elif k == Qt.Key_D:
            self.toggle_spread()
        elif k == Qt.Key_F:
            self.toggle_strip()
        elif k == Qt.Key_Escape:
            self.owner.close_book()
        else:
            return False
        return True


# ---- the window ----------------------------------------------------------------------------------------------

class ComixReader(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.state = L.load_state()
        self.root = L.comics_root()
        self.history = []                      # shelves we came through
        self.folder = None
        self.covers = {}                       # key -> QImage (None = asked for)
        self.loader = Loader(self, threads=3)
        self.loader.loaded.connect(self._cover_loaded)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack)

        # library page
        lib = QWidget()
        col = QVBoxLayout(lib)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        col.addWidget(self._library_bar())
        self.recent_label = QLabel("  Continue Reading")
        self.recent_label.setStyleSheet("font: bold 12px Tahoma; color: #1E3C8C; padding: 6px 4px 2px 4px;"
                                        " background: white;")
        col.addWidget(self.recent_label)
        self.recent = Gallery(self, single_row=True)
        self.recent.opened.connect(self.open_entry)
        col.addWidget(self.recent)
        self.shelf_label = QLabel()
        self.shelf_label.setStyleSheet("font: bold 12px Tahoma; color: #1E3C8C; padding: 6px 4px 2px 4px;"
                                       " background: white; border-top: 1px solid #E0E0E0;")
        col.addWidget(self.shelf_label)
        self.grid = Gallery(self)
        self.grid.opened.connect(self.open_entry)
        col.addWidget(self.grid, 1)
        self.status = QLabel()
        self.status.setStyleSheet("font: 11px Tahoma; padding: 2px 6px; background: #ECE9D8;"
                                  " border-top: 1px solid #A0A0A0;")
        col.addWidget(self.status)
        self.stack.addWidget(lib)

        self.viewer = Viewer(self)
        self.stack.addWidget(self.viewer)
        self.reading = None

        if self.root is None:
            self.shelf_label.setText("  No comics found")
            self.status.setText("Put the Furry Media Archive (with its Comic Scans folder) on drive E: "
                                "(Local Storage), then click Library.")
            self.recent_label.hide()
            self.recent.hide()
        else:
            self.show_shelf(self.root, remember=False)

    def _library_bar(self):
        bar = QWidget()
        bar.setObjectName("bar")
        bar.setAttribute(Qt.WA_StyledBackground)
        bar.setStyleSheet("QWidget#bar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FDFDFB,"
                          " stop:1 #E3E0D2); border-bottom: 1px solid #A0A0A0; }"
                          "QToolButton { font: 11px Tahoma; padding: 3px 8px; border: 1px solid transparent;"
                          " border-radius: 3px; } QToolButton:hover { border-color: #C0BCA8; background: white; }"
                          "QToolButton:disabled { color: #A0A0A0; }"
                          "QLineEdit { font: 11px Tahoma; border: 1px solid #7F9DB9; padding: 1px 4px; }"
                          "QLabel { font: 11px Tahoma; }")
        row = QHBoxLayout(bar)
        row.setContentsMargins(4, 3, 6, 3)
        row.setSpacing(3)

        def tool(text, tip, slot):
            b = QToolButton()
            b.setText(text)
            b.setToolTip(tip)
            b.setFocusPolicy(Qt.NoFocus)
            b.clicked.connect(slot)
            row.addWidget(b)
            return b
        self.back_btn = tool("◄ Back", "Back", self.go_back)
        self.home_btn = tool("Library", "All comics", self.go_home)
        row.addSpacing(10)
        self.where = QLabel()
        self.where.setStyleSheet("color: #404040;")
        row.addWidget(self.where, 1)
        row.addWidget(QLabel("Find:"))
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Title")
        self.filter.setFixedWidth(150)
        self.filter.textChanged.connect(self._apply_filter)
        row.addWidget(self.filter)
        return bar

    # ---- shelves -----------------------------------------------------------------------------------------------
    def show_shelf(self, folder, remember=True):
        if self.root is None:
            return
        if remember and self.folder is not None:
            self.history.append(self.folder)
        self.loader.clear()
        self.folder, entries = L.list_shelf(folder)
        self.filter.blockSignals(True)
        self.filter.clear()
        self.filter.blockSignals(False)
        at_root = self.folder == L.resolve(self.root)[0]
        self.back_btn.setEnabled(bool(self.history))
        try:
            rel = self.folder.relative_to(self.root)
            crumbs = ["Comic Scans"] + [L.nice_name(part) for part in rel.parts]
        except ValueError:
            crumbs = [L.nice_name(self.folder.name)]
        self.where.setText("  ›  ".join(crumbs))
        self.shelf_label.setText("  All Comics" if at_root else "  " + L.nice_name(self.folder.name))
        recent = L.recent(self.state) if at_root else []
        self.recent_label.setVisible(bool(recent))
        self.recent.setVisible(bool(recent))
        self.recent.fill(recent)
        self.grid.fill(entries)
        self.grid.scrollToTop()
        shelves = sum(e.kind == "shelf" for e in entries)
        comics = len(entries) - shelves
        bits = [f"{shelves} series" if shelves else "", f"{comics} comic{'s' if comics != 1 else ''}" if comics else ""]
        self.status.setText(", ".join(b for b in bits if b) or "This shelf is empty.")
        if self.frame is not None:
            self.frame.set_title("FurComix Reader")

    def go_back(self):
        if self.history:
            self.show_shelf(self.history.pop(), remember=False)

    def go_home(self):
        if self.root is None:
            self.root = L.comics_root()
            if self.root is None:
                return
        self.history.clear()
        self.show_shelf(self.root, remember=False)

    def _apply_filter(self, text):
        t = text.lower().strip()
        for i in range(self.grid.count()):
            item = self.grid.item(i)
            item.setHidden(bool(t) and t not in item.text().lower())
        self.grid.request_visible()

    # ---- covers ------------------------------------------------------------------------------------------------
    def want_cover(self, entry):
        if entry.key in self.covers:
            return
        self.covers[entry.key] = None
        self.loader.request(entry.key, lambda e=entry: L.cover(e))

    def _cover_loaded(self, key, img):
        self.covers[key] = img
        for gallery in (self.grid, self.recent):
            for item in gallery.items_for(key):
                self.paint_tile(item)

    def paint_tile(self, item):
        entry = item.data(Qt.UserRole)
        img = self.covers.get(entry.key)
        info = self.state.get("books", {}).get(entry.key) if entry.kind == "comic" else None
        progress = (info["page"], info["pages"]) if info else None
        item.setIcon(QIcon(_tile_pixmap(entry, img if entry.key in self.covers else None, progress)))

    # ---- reading -----------------------------------------------------------------------------------------------
    def open_entry(self, entry):
        if entry.kind == "shelf":
            self.show_shelf(entry.path)
            return
        info = self.state.get("books", {}).get(entry.key)
        page = info["page"] if info and info["page"] < info["pages"] - 1 else 0
        self.reading = entry
        self.stack.setCurrentWidget(self.viewer)
        self.viewer.open(entry, page)
        self.viewer.canvas.setFocus()
        if self.frame is not None:
            self.frame.set_title(f"{entry.name} - FurComix Reader")

    def page_turned(self, entry, page, pages):
        L.remember(self.state, entry, page, pages)

    def finished_book(self):
        """Past the last page: back to the shelf, with the next comic picked out."""
        done = self.reading
        self.close_book()
        if done is None:
            return
        for i in range(self.grid.count()):
            if self.grid.item(i).data(Qt.UserRole).key == done.key and i + 1 < self.grid.count():
                self.grid.setCurrentRow(i + 1)
                self.grid.scrollToItem(self.grid.item(i + 1))
                self.status.setText(f"Finished {done.name}. Next: {self.grid.item(i + 1).text()}")
                break

    def close_book(self):
        self.viewer.close_book()
        self.stack.setCurrentIndex(0)
        if self.reading is not None:
            for gallery in (self.grid, self.recent):
                for item in gallery.items_for(self.reading.key):
                    self.paint_tile(item)
            at_root = self.folder == L.resolve(self.root)[0] if self.root else False
            if at_root:
                recent = L.recent(self.state)
                self.recent_label.setVisible(bool(recent))
                self.recent.setVisible(bool(recent))
                self.recent.fill(recent)
        self.reading = None
        if self.frame is not None:
            self.frame.set_title("FurComix Reader")
        self.grid.setFocus()

    def toggle_full_screen(self):
        if self.frame is not None:
            self.frame.toggle_maximize()

    def keyPressEvent(self, event):
        if self.stack.currentWidget() is self.viewer:
            if self.viewer.key(event):
                return
        elif event.key() == Qt.Key_Backspace:
            self.go_back()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.loader.clear()
        self.viewer.close_book()
        L.save_state(self.state)
        event.accept()


_open = {}


def open_comix(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = ComixReader(desktop)
        win = XPWindow(desktop, "FurComix Reader", body, comix_icon(), (800, 580))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win
