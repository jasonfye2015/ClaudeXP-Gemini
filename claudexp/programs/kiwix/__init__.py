"""Kiwix - Wikipedia (and more) offline, a clone of the Kiwix desktop reader.

The Library tab shows the books in E:\\Kiwix (ZIM files); open one and it reads in its own tab, with Back/Forward,
Home (the book's main page), Random article, zoom, and a search box that suggests article titles as you type. Get
Content downloads the offline packages that fit ClaudeXP's 15 GB budget (library.py), or adds a .zim you already
have. If the library is empty, Kiwix opens on Get Content. Pages come from ZIM files read by zim.py and served on
127.0.0.1 (server.py); nothing goes online except downloads you start.
"""
import threading

from PySide6.QtCore import QRectF, QSize, QStringListModel, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QCompleter, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMenu, QProgressBar, QPushButton, QStackedWidget, QTabWidget,
                               QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from shiboken6 import isValid

from ...wm import XPWindow
from . import library, server

STYLE = """
QWidget#kiwix { background: #F4F5F7; }
QWidget#bar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #E6E8EC);
              border-bottom: 1px solid #C8CCD2; }
QToolButton { border: 1px solid transparent; border-radius: 3px; padding: 3px 6px; font-family: Tahoma; font-size: 11px; }
QToolButton:hover { border: 1px solid #B8C0CC; background: #FFFFFF; }
QLineEdit#search { border: 1px solid #A8B0BC; border-radius: 10px; padding: 3px 10px; font-family: Tahoma;
                   font-size: 12px; background: white; }
QLabel, QPushButton { font-family: Tahoma; font-size: 11px; }
QLabel#head { font-size: 16px; font-weight: bold; color: #2A2F38; }
QListWidget#books { background: #F4F5F7; border: none; font-family: Tahoma; font-size: 11px; }
QTreeWidget { background: white; border: 1px solid #C8CCD2; font-family: Tahoma; font-size: 11px; }
QTabWidget::pane { border: none; }
QTabBar::tab { font-family: Tahoma; font-size: 11px; padding: 4px 10px; background: #E6E8EC; border: 1px solid #C8CCD2;
               border-bottom: none; margin-right: 1px; }
QTabBar::tab:selected { background: #FFFFFF; }
"""


def kiwix_pixmap(size=32):
    """Kiwix's kiwi: a round brown bird with a long beak, on a blue disc."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#4A90D9"))
    g.setColorAt(1, QColor("#1D4F8F"))
    p.setPen(QPen(QColor("#163B6A"), max(1.0, s)))
    p.setBrush(g)
    p.drawEllipse(QRectF(1 * s, 1 * s, 30 * s, 30 * s))
    body = QLinearGradient(0, 9 * s, 0, 25 * s)
    body.setColorAt(0, QColor("#B88A55"))
    body.setColorAt(1, QColor("#7A5530"))
    p.setPen(QPen(QColor("#4A3018"), max(0.8, 0.8 * s)))
    p.setBrush(body)
    p.drawEllipse(QRectF(6 * s, 10 * s, 15 * s, 13 * s))             # the body
    p.drawEllipse(QRectF(17 * s, 9 * s, 7 * s, 7 * s))               # the head
    beak = QPainterPath()
    beak.moveTo(23 * s, 12 * s)
    beak.quadTo(27 * s, 15 * s, 29 * s, 21 * s)
    beak.lineTo(28 * s, 21.4 * s)
    beak.quadTo(25.5 * s, 16 * s, 22.5 * s, 13.6 * s)
    p.setBrush(QColor("#E8D5A0"))
    p.drawPath(beak)
    p.setPen(QPen(QColor("#E8D5A0"), max(1.0, 1.4 * s)))
    p.drawLine(int(11 * s), int(22 * s), int(10 * s), int(27 * s))   # legs
    p.drawLine(int(15 * s), int(22 * s), int(16 * s), int(27 * s))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#101010"))
    p.drawEllipse(QRectF(20.5 * s, 11 * s, 1.6 * s, 1.6 * s))       # the eye
    p.end()
    return pm


def kiwix_icon():
    icon = QIcon()
    for sz in (16, 32, 48):
        icon.addPixmap(kiwix_pixmap(sz))
    return icon


_profile = None


def _web_profile():
    """Off the record, and only ever talks to Kiwix's own server."""
    global _profile
    if _profile is None:
        from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineUrlRequestInterceptor
        from PySide6.QtWidgets import QApplication

        class _LocalOnly(QWebEngineUrlRequestInterceptor):
            def interceptRequest(self, info):
                url = info.requestUrl().toString()
                if not (server.is_local(url) or url.startswith(("data:", "blob:", "about:"))):
                    info.block(True)
        _profile = QWebEngineProfile(QApplication.instance())
        _profile.interceptor = _LocalOnly(_profile)
        _profile.setUrlRequestInterceptor(_profile.interceptor)
    return _profile


class BookView(QWidget):
    """One open book: a web view on Kiwix's server."""

    def __init__(self, book_id, path=""):
        super().__init__()
        from PySide6.QtWebEngineCore import QWebEnginePage
        from PySide6.QtWebEngineWidgets import QWebEngineView
        self.book_id = book_id
        self.view = QWebEngineView()
        self.view.setPage(QWebEnginePage(_web_profile(), self.view))
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.view)
        self.view.load(QUrl(server.url_for(book_id, path)))

    def open(self, path):
        self.view.load(QUrl(server.url_for(self.book_id, path)))


class Kiwix(QWidget):
    copied = Signal(str, str)               # file name, error ('' when it worked)
    latest_found = Signal(object)           # {family: (file name, size, url)} from the Kiwix server

    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setObjectName("kiwix")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        bar = QWidget()
        bar.setObjectName("bar")
        bar.setAttribute(Qt.WA_StyledBackground, True)
        h = QHBoxLayout(bar)
        h.setContentsMargins(6, 4, 6, 4)

        def tool(text, slot, tip=""):
            b = QToolButton()
            b.setText(text)
            b.setToolTip(tip or text)
            b.clicked.connect(slot)
            h.addWidget(b)
            return b
        tool("\u25C0", lambda: self._web(lambda w: w.view.back()), "Back")
        tool("\u25B6", lambda: self._web(lambda w: w.view.forward()), "Forward")
        tool("\u2302 Home", self.home, "The book's main page")
        tool("\u2630 Library", lambda: self.tabs.setCurrentIndex(0), "Your library")
        tool("\u2684 Random", self.random_article, "A random article")
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText("Search")
        self.model = QStringListModel()
        comp = QCompleter(self.model, self)
        comp.setCaseSensitivity(Qt.CaseInsensitive)
        comp.setFilterMode(Qt.MatchContains)
        comp.activated.connect(self._go_suggestion)
        self.search.setCompleter(comp)
        self.search.textEdited.connect(self._suggest)
        self.search.returnPressed.connect(self._search_enter)
        h.addWidget(self.search, 1)
        tool("\u2212", lambda: self._web(lambda w: w.view.setZoomFactor(max(0.4, w.view.zoomFactor() - 0.1))),
             "Zoom out")
        tool("+", lambda: self._web(lambda w: w.view.setZoomFactor(min(3.0, w.view.zoomFactor() + 0.1))), "Zoom in")
        menu_btn = QToolButton()
        menu_btn.setText("\u2261")
        menu_btn.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(menu_btn)
        menu.addAction("Open ZIM File...", self.add_file)
        menu.addAction("Get Content...", lambda: self.show_library(get=True))
        menu.addAction("Random Article", self.random_article)
        menu.addSeparator()
        menu.addAction("About Kiwix", self._about)
        menu_btn.setMenu(menu)
        h.addWidget(menu_btn)
        v.addWidget(bar)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.lib = QStackedWidget()
        self.lib.addWidget(self._library_page())
        self.lib.addWidget(self._get_page())
        self.tabs.addTab(self.lib, "Library")
        self.tabs.tabBar().setTabButton(0, self.tabs.tabBar().ButtonPosition.RightSide, None)
        v.addWidget(self.tabs, 1)
        self.suggestions = {}
        self.copied.connect(self._copied)
        self.latest_found.connect(self._apply_latest)
        self.inst = library.KiwixInstaller(self)
        self.inst.status.connect(lambda k, t: isValid(self) and self.dl_line.setText(t))
        self.inst.progress.connect(lambda k, d, t: isValid(self) and t and self.dl_bar.setValue(int(d * 100 / t)))
        self.inst.item_done.connect(self._item_done)
        self.inst.all_done.connect(self._all_done)
        self.refresh_library()
        if not library.books():
            self.show_library(get=True)

    # ---- the library ---------------------------------------------------------------------------------------
    def _library_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(16, 12, 16, 12)
        top = QHBoxLayout()
        head = QLabel("Library")
        head.setObjectName("head")
        top.addWidget(head)
        top.addStretch()
        add = QPushButton("Open ZIM File...")
        get = QPushButton("Get Content...")
        add.clicked.connect(self.add_file)
        get.clicked.connect(lambda: self.show_library(get=True))
        top.addWidget(add)
        top.addWidget(get)
        v.addLayout(top)
        self.lib_info = QLabel()
        v.addWidget(self.lib_info)
        self.book_list = QListWidget()
        self.book_list.setObjectName("books")
        self.book_list.setViewMode(QListWidget.IconMode)
        self.book_list.setIconSize(QSize(64, 64))
        self.book_list.setGridSize(QSize(200, 150))
        self.book_list.setWordWrap(True)
        self.book_list.setResizeMode(QListWidget.Adjust)
        self.book_list.setMovement(QListWidget.Static)
        self.book_list.itemActivated.connect(lambda it: self.open_book(it.data(Qt.UserRole)))
        self.book_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.book_list.customContextMenuRequested.connect(self._book_menu)
        v.addWidget(self.book_list, 1)
        return page

    def refresh_library(self):
        from .zim import info
        self.book_list.clear()
        total = 0
        for path in library.books():
            try:
                meta = info(path)
            except Exception:
                continue
            total += meta["size"]
            icon = QPixmap()
            if meta["illustration"]:
                icon.loadFromData(meta["illustration"])
            item = QListWidgetItem(QIcon(icon) if not icon.isNull() else kiwix_icon(),
                                   f"{meta['title']}\n{library.fmt(meta['size'])} - {meta['date']}")
            item.setToolTip(f"{meta['title']}\n{meta['description']}\n{meta['count']:,} entries\n{path.name}")
            item.setData(Qt.UserRole, path.stem)
            self.book_list.addItem(item)
        n = self.book_list.count()
        self.lib_info.setText(f"{n} book{'s' if n != 1 else ''}, {library.fmt(total)} of the "
                              f"{library.fmt(library.BUDGET)} set aside for Kiwix on drive E:. Double-click a book "
                              "to read it." if n else "Your library is empty. Click Get Content to download "
                                                      "Wikipedia, or Open ZIM File to add one you have.")

    def show_library(self, get=False):
        self.tabs.setCurrentIndex(0)
        self.lib.setCurrentIndex(1 if get else 0)
        if get:
            self._fill_catalog()

    def _book_menu(self, pos):
        it = self.book_list.itemAt(pos)
        if it is None:
            return
        m = QMenu(self)
        m.addAction("Open", lambda: self.open_book(it.data(Qt.UserRole)))
        m.addAction("Delete This Book...", lambda: self._delete(it.data(Qt.UserRole)))
        m.exec(self.book_list.viewport().mapToGlobal(pos))

    def _delete(self, book_id):
        from ...explorer.dialogs import msgbox

        def answer(b):
            if b != "Yes":
                return
            for i in range(self.tabs.count() - 1, 0, -1):
                w = self.tabs.widget(i)
                if getattr(w, "book_id", None) == book_id:
                    self._close_tab(i)
            server.forget(book_id)
            try:
                (library.folder() / f"{book_id}.zim").unlink()
            except OSError as e:
                msgbox(self.desktop, "Kiwix", f"The book couldn't be deleted: {e}", "error")
            self.refresh_library()
        msgbox(self.desktop, "Kiwix", f"Delete {book_id}.zim from drive E:? You can download it again from Get "
               "Content.", "question", ("Yes", "No"), answer)

    # ---- reading ----------------------------------------------------------------------------------------------
    def open_book(self, book_id, path=""):
        z = server.book(book_id)
        if z is None:
            return
        view = BookView(book_id, path)
        view.view.titleChanged.connect(lambda t, v=view: self._title(v, t))
        i = self.tabs.addTab(view, z.title()[:28])
        self.tabs.setCurrentIndex(i)

    def _title(self, view, title):
        i = self.tabs.indexOf(view)
        if i > 0:
            self.tabs.setTabText(i, (title or "")[:28])
            if self.frame is not None and self.tabs.currentIndex() == i:
                self.frame.set_title(f"{title} - Kiwix")

    def _current_book(self):
        w = self.tabs.currentWidget()
        if isinstance(w, BookView):
            return w
        return None

    def _web(self, fn):
        w = self._current_book()
        if w is not None:
            fn(w)

    def _close_tab(self, i):
        if i > 0:
            w = self.tabs.widget(i)
            self.tabs.removeTab(i)
            w.deleteLater()

    def home(self):
        w = self._current_book()
        if w is not None:
            w.open("")
        else:
            self.show_library()

    def _book_for_search(self):
        w = self._current_book()
        if w is not None:
            return w.book_id
        ids = [p.stem for p in library.books()]
        return ids[0] if ids else None

    def random_article(self):
        book_id = self._book_for_search()
        if book_id is None:
            return self.show_library(get=True)
        z = server.book(book_id)
        path = z.random_article() if z else None
        if path is None:
            return
        w = self._current_book()
        if w is not None and w.book_id == book_id:
            w.open(path)
        else:
            self.open_book(book_id, path)

    def _suggest(self, text):
        book_id = self._book_for_search()
        if not book_id or len(text.strip()) < 2:
            return
        z = server.book(book_id)
        try:
            hits = z.suggest(text.strip(), 15)
        except Exception:
            hits = []
        self.suggestions = {t: (book_id, p) for t, p in hits}
        self.model.setStringList([t for t, _p in hits])

    def _go_suggestion(self, title):
        target = self.suggestions.get(title)
        if target is None:
            return
        book_id, path = target
        w = self._current_book()
        if w is not None and w.book_id == book_id:
            w.open(path)
        else:
            self.open_book(book_id, path)

    def _search_enter(self):
        text = self.search.text().strip()
        if not text:
            return
        if text not in self.suggestions:
            self._suggest(text)
        if text in self.suggestions:
            return self._go_suggestion(text)
        if self.suggestions:
            return self._go_suggestion(next(iter(self.suggestions)))
        from ...explorer.dialogs import msgbox
        msgbox(self.desktop, "Kiwix", f"No article titles start with '{text}'.", "info")

    # ---- getting content ------------------------------------------------------------------------------------------
    def _get_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(16, 12, 16, 12)
        top = QHBoxLayout()
        head = QLabel("Get Content")
        head.setObjectName("head")
        top.addWidget(head)
        top.addStretch()
        back = QPushButton("Back to Library")
        back.clicked.connect(lambda: self.show_library())
        top.addWidget(back)
        v.addLayout(top)
        self.get_info = QLabel()
        self.get_info.setWordWrap(True)
        v.addWidget(self.get_info)
        self.catalog = QTreeWidget()
        self.catalog.setHeaderLabels(["Content", "Size", "Status"])
        self.catalog.setRootIsDecorated(False)
        self.catalog.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.catalog.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.catalog.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.catalog.itemChanged.connect(lambda *_: self._budget())
        v.addWidget(self.catalog, 1)
        self.budget_label = QLabel()
        v.addWidget(self.budget_label)
        self.dl_bar = QProgressBar()
        self.dl_bar.setTextVisible(False)
        self.dl_bar.setFixedHeight(14)
        v.addWidget(self.dl_bar)
        self.dl_line = QLabel(" ")
        v.addWidget(self.dl_line)
        row = QHBoxLayout()
        self.dl_go = QPushButton("Download")
        self.dl_stop = QPushButton("Stop")
        self.dl_stop.setEnabled(False)
        have = QPushButton("Use a File I Have...")
        other = QPushButton("Other Address...")
        for b in (self.dl_go, self.dl_stop, have, other):
            row.addWidget(b)
        row.addStretch()
        v.addLayout(row)
        self.dl_go.clicked.connect(self.download)
        self.dl_stop.clicked.connect(self.inst_stop)
        have.clicked.connect(self.add_file)
        other.clicked.connect(self.other_address)
        self.catalog_rows = {}
        return page

    def _fill_catalog(self):
        self.catalog.blockSignals(True)
        self.catalog.clear()
        self.catalog_rows = {}
        empty = not library.books()
        for key, directory, title, what, known, size, rec in library.CATALOG:
            have = library.installed_family(key)
            row = QTreeWidgetItem([title, library.fmt(size), "Installed" if have else "Not installed"])
            row.setToolTip(0, what)
            row.setFlags(row.flags() | Qt.ItemIsUserCheckable)
            row.setCheckState(0, Qt.Checked if (rec and empty and not have) else Qt.Unchecked)
            if have:
                row.setFlags(row.flags() & ~Qt.ItemIsEnabled)
            row.setData(0, Qt.UserRole, {"key": key, "dir": directory, "title": title, "file": known, "size": size,
                                         "url": library.SERVER + directory + "/" + known})
            self.catalog.addTopLevelItem(row)
            self.catalog_rows[key] = row
        self.catalog.blockSignals(False)
        self.get_info.setText("Offline Wikipedia from Kiwix, chosen to fit in 15 GB. The recommended set (ticked) "
                              "gives you the most-read articles with pictures, introductions to a million more, and "
                              "Simple English Wikipedia. Sizes are being checked with the Kiwix server...")
        self._budget()
        threading.Thread(target=self._resolve_latest, daemon=True).start()

    def _resolve_latest(self):
        """Ask the server for the newest file of each family (in the background)."""
        found = {}
        for key, directory, _t, _w, known, size, _r in library.CATALOG:
            found[key] = library.latest(key, directory, known, size)
        if isValid(self):
            self.latest_found.emit(found)

    def _apply_latest(self, found):
        if not found or not isValid(self):
            return
        self.catalog.blockSignals(True)
        for key, (name, size, url) in found.items():
            row = self.catalog_rows.get(key)
            if row is None:
                continue
            d = row.data(0, Qt.UserRole)
            d.update(file=name, size=size, url=url)
            row.setData(0, Qt.UserRole, d)
            row.setText(1, library.fmt(size))
        self.catalog.blockSignals(False)
        self.get_info.setText("Offline Wikipedia from Kiwix, chosen to fit in 15 GB. The recommended set (ticked) "
                              "gives you the most-read articles with pictures, introductions to a million more, and "
                              "Simple English Wikipedia - the newest editions on the Kiwix server.")
        self._budget()

    def _selected(self):
        return [r.data(0, Qt.UserRole) for r in self.catalog_rows.values()
                if r.checkState(0) == Qt.Checked and r.flags() & Qt.ItemIsEnabled]

    def _budget(self):
        chosen = self._selected()
        need = sum(d["size"] for d in chosen)
        have = library.used()
        total = need + have
        over = total > library.BUDGET
        self.budget_label.setText(
            f"Selected: {library.fmt(need)}.  Library: {library.fmt(have)}.  Total {library.fmt(total)} of "
            f"{library.fmt(library.BUDGET)}" + ("  <font color='#C02010'><b>- over the 15 GB budget; untick something"
                                                "</b></font>" if over else ""))
        self.dl_go.setEnabled(bool(chosen) and not over and not self.inst.busy())

    def download(self, urls=None):
        chosen = self._selected()
        if not chosen:
            return
        from ...llm_setup import free_space
        need = sum(d["size"] for d in chosen)
        if need > free_space():
            from ...explorer.dialogs import msgbox
            msgbox(self.desktop, "Kiwix", "There isn't enough free space on drive E: for that.", "warning")
            return
        keys = []
        for d in chosen:
            self.inst.add(d["key"], d["title"], d["file"], d["url"], d["size"])
            keys.append(d["key"])
            self.catalog_rows[d["key"]].setText(2, "Waiting...")
        self.failed = []
        self.dl_go.setEnabled(False)
        self.dl_stop.setEnabled(True)
        self.inst.download(keys, urls or {})

    def inst_stop(self):
        self.inst.stop()
        self.dl_line.setText("Stopping... (what's downloaded so far is kept and resumes next time)")

    def _item_done(self, key, ok, error):
        if not isValid(self):
            return
        row = self.catalog_rows.get(key)
        if row is not None:
            row.setText(2, "Installed" if ok else "Failed")
        if not ok and error != "Cancelled.":
            self.failed.append((key, error))

    def _all_done(self):
        if not isValid(self):
            return
        self.dl_stop.setEnabled(False)
        self.dl_bar.setValue(0)
        self.refresh_library()
        self._fill_catalog()
        if getattr(self, "failed", None):
            key, error = self.failed[0]
            from ...explorer.dialogs import msgbox

            def answer(b):
                if b == "Try Again":
                    self.catalog_rows[key].setCheckState(0, Qt.Checked)
                    self.download()
                elif b == "Use My File":
                    self.add_file()
                elif b == "Other Address":
                    self.other_address(key)
            msgbox(self.desktop, "Kiwix", f"The download didn't work:\n\n{error}\n\nYou can try again, use a .zim "
                   "file you already have, or give another web address.", "warning",
                   ("Try Again", "Use My File", "Other Address", "Cancel"), answer)
        elif library.books():
            self.dl_line.setText("Done - your books are in the Library.")

    def add_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open a ZIM file", "", "ZIM files (*.zim)")
        if not path:
            return
        from pathlib import Path
        size = Path(path).stat().st_size
        if library.used() + size > library.BUDGET:
            from ...explorer.dialogs import msgbox
            msgbox(self.desktop, "Kiwix", f"That book ({library.fmt(size)}) would take the library past its 15 GB "
                   "budget. Delete a book first (right-click it in the Library).", "warning")
            return
        self.dl_line.setText(f"Adding {Path(path).name}...")

        def work():
            try:
                library.bring_in(path)
                self.copied.emit(Path(path).name, "")
            except Exception as e:
                self.copied.emit(Path(path).name, str(e))
        threading.Thread(target=work, daemon=True).start()

    def _copied(self, name, error):
        if not isValid(self):
            return
        from ...explorer.dialogs import msgbox
        if error:
            msgbox(self.desktop, "Kiwix", f"{name} couldn't be added: {error}", "error")
            return
        self.refresh_library()
        self.show_library()
        self.dl_line.setText(f"Added {name}.")

    def other_address(self, key=None):
        from ...network import DialogBody, _fixed_window
        if key is None:
            cur = self.catalog.currentItem() or next((r for r in self.catalog_rows.values()
                                                      if r.checkState(0) == Qt.Checked), None)
            if cur is None:
                return
            d = cur.data(0, Qt.UserRole)
        else:
            d = self.catalog_rows[key].data(0, Qt.UserRole)
        body = DialogBody()
        v = QVBoxLayout(body)
        v.setContentsMargins(14, 12, 14, 12)
        v.addWidget(QLabel(f"<b>Download {d['title']} from another address</b><br>A mirror or direct link to "
                           f"{d['file']}:"))
        e = QLineEdit(d["url"])
        e.setMinimumWidth(460)
        v.addWidget(e)
        row = QHBoxLayout()
        row.addStretch()
        ok, cancel = QPushButton("Download"), QPushButton("Cancel")
        for b in (ok, cancel):
            b.setFixedSize(80, 23)
            row.addWidget(b)
        v.addLayout(row)
        holder = {}

        def close():
            if holder.get("win") is not None and isValid(holder["win"]):
                self.desktop.close_window(holder.pop("win"))

        def go():
            url = e.text().strip()
            close()
            for r in self.catalog_rows.values():
                r.setCheckState(0, Qt.Checked if r.data(0, Qt.UserRole)["key"] == d["key"] else Qt.Unchecked)
            self.download({d["file"]: url})
        ok.clicked.connect(go)
        cancel.clicked.connect(close)
        holder["win"] = _fixed_window(self.desktop, "Other Address", body, close)
        self.desktop.open_window(holder["win"])

    def _about(self):
        from ...explorer.dialogs import msgbox
        msgbox(self.desktop, "About Kiwix", "Kiwix - the Internet, offline.\n\nA reader for ZIM files: Wikipedia and "
               "more, without a connection. Content from the Kiwix project (kiwix.org) and Wikipedia's editors, "
               "CC BY-SA.", "info", window_icon=kiwix_icon())

    def shutdown(self):
        for i in range(self.tabs.count() - 1, 0, -1):
            self._close_tab(i)


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = Kiwix(desktop)
    win = XPWindow(desktop, "Kiwix", body, kiwix_icon(), size=(900, 640))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.shutdown()
    server.close_all()
