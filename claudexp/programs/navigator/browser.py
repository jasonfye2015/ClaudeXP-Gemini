"""The Netscape Navigator window: Netscape 4-style toolbars, Location bar, page view, status bar."""
import html
import math
import re
from urllib.parse import urlparse

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import (QAction, QColor, QFont, QIcon, QKeySequence, QLinearGradient, QPainter, QPixmap,
                           QImageReader, QPolygonF, QTextDocument)
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QMenuBar, QPlainTextEdit, QProgressBar, QSizePolicy,
                               QStackedWidget, QStyle, QTextBrowser, QToolBar, QToolButton, QVBoxLayout, QWidget)

from ... import network, sound
from ...paths import IMAGES, pixmap
from ...wm import XPWindow
from ..people import load_json, save_json
from . import sites, web

BOOKMARKS_FILE = web.DATA_DIR / "bookmarks.json"
DEFAULT_BOOKMARKS = [
    {"title": "Netscape Netcenter", "url": web.HOME_URL},
    {"title": "FurNet IRC Network", "url": "http://www.furnet.irc/"},
    {"title": "PawPrints MUCK", "url": "http://www.pawprintsmuck.com/"},
    {"title": "FurryCities", "url": "http://www.furrycities.com/"},
]
EXPECTED_SIZE = 6000      # rough page size, for the progress meter
ABOUT_PAGE = """<html><head><title>About Netscape Navigator</title></head><body bgcolor="#C0C0C0">
<center><img src="about:logo" width="780" height="336"><br><br>
<font face="Times New Roman" size="3">Netscape Navigator 4.79 for ClaudeXP.<br>
Every page on this Web is written for you, on the fly, as you browse.</font></center></body></html>"""

STYLE = """
QMenuBar { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
QMenuBar::item { padding: 3px 7px; background: transparent; }
QMenuBar::item:selected { background: #316AC5; color: white; }
QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }
QMenu::item { padding: 4px 24px 4px 20px; }
QMenu::item:selected { background: #316AC5; color: white; }
QToolBar { background: #ECE9D8; border: none; border-bottom: 1px solid #ACA899; spacing: 1px; padding: 1px; }
QToolButton { font-family: Tahoma; font-size: 10px; padding: 1px 4px; border: 1px solid transparent; }
QToolButton:hover { border: 1px solid #ACA899; background: #F4F2E8; }
QToolButton:pressed { background: #DCD8C4; }
QLabel#status { font-family: Tahoma; font-size: 11px; }
QWidget#statusbar { background: #ECE9D8; border-top: 1px solid #ACA899; }
"""


def logo_pixmap(size=40, frame=None):
    """The Netscape 'C' with a meteor; frame (0..) animates the meteor shower while loading."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, size, size)
    g.setColorAt(0, QColor("#1B3A8C"))
    g.setColorAt(1, QColor("#081A4A"))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawRoundedRect(QRectF(0, 0, size, size), size * 0.12, size * 0.12)
    p.setBrush(QColor("white"))
    for i in range(6):   # stars
        a = (i * 1.7 + (frame or 0) * 0.15) % 6.28
        x = size * (0.15 + 0.7 * ((math.sin(a * 3 + i) + 1) / 2))
        y = size * (0.12 + 0.25 * ((math.cos(a * 2 + i) + 1) / 2))
        r = size * 0.025
        p.drawEllipse(QPointF(x, y), r, r)
    if frame is not None:  # a meteor sweeping across
        t = (frame % 16) / 16
        mx, my = size * (1.1 - 1.3 * t), size * (0.1 + 0.5 * t)
        trail = QLinearGradient(mx, my, mx + size * 0.4, my - size * 0.15)
        trail.setColorAt(0, QColor(255, 220, 120, 230))
        trail.setColorAt(1, QColor(255, 220, 120, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(trail)
        p.drawPolygon(QPolygonF([QPointF(mx, my - size * 0.03), QPointF(mx + size * 0.4, my - size * 0.18),
                                 QPointF(mx, my + size * 0.03)]))
        p.setBrush(QColor("#FFE9A0"))
        p.drawEllipse(QPointF(mx, my), size * 0.045, size * 0.045)
    font = QFont("Georgia", max(6, int(size * 0.5)))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QColor("#FFFFFF"))
    p.drawText(QRectF(0, size * 0.18, size, size * 0.8), Qt.AlignCenter, "C")
    p.end()
    return pm


THROBBER_SIZE = 40
_throbber_frames = None


def nav_icon():
    pm = pixmap("netscape_icon.jpg")
    if not pm.isNull():
        return QIcon(pm)
    icon = QIcon()
    for size in (16, 32, 48):
        icon.addPixmap(logo_pixmap(size))
    return icon


def throbber_frames():
    """The meteor-shower animation (netscape_throbber.gif), scaled for the toolbar."""
    global _throbber_frames
    if _throbber_frames is None:
        reader = QImageReader(str(IMAGES / "netscape_throbber.gif"))
        frames = []
        while True:
            img = reader.read()
            if img.isNull():
                break
            frames.append(QPixmap.fromImage(img.scaled(THROBBER_SIZE, THROBBER_SIZE, Qt.KeepAspectRatio,
                                                       Qt.SmoothTransformation)))
        _throbber_frames = frames or [logo_pixmap(THROBBER_SIZE, f) for f in range(16)]
    return _throbber_frames


class PageView(QTextBrowser):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.setOpenLinks(False)
        self.setStyleSheet("QTextBrowser { background: white; border: 1px solid #7F9DB9; }")
        self.anchorClicked.connect(browser.link_clicked)
        self.highlighted.connect(browser.link_hovered)

    def loadResource(self, kind, url):
        if kind == QTextDocument.ImageResource and url.toString() == "about:logo":
            return pixmap("netscape_about.jpg")
        if kind == QTextDocument.ImageResource:
            return web.image_for(self.browser.resolve(url.toString()))
        return None

    def show_page(self, page):
        text, link, _bg = web.body_colors(page)
        css = ""
        if text:
            css += f"body {{ color: {text}; }} "
        if link:
            css += f"a {{ color: {link}; }}"
        self.document().setDefaultStyleSheet(css)
        bar = self.verticalScrollBar()
        pos = bar.value()
        self.setHtml(page)
        bar.setValue(pos)


class Browser(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.knowledge = web.WebKnowledge()
        self.cache = web.Cache()
        from claudeaim.storage import Settings
        aim_settings = Settings()
        self.model = aim_settings["default_model"]
        self.num_ctx = int(aim_settings["context_size"])
        self.history = []
        self.index = -1
        self.url = ""
        self.page = ""
        self.links = {}
        self.loader = None
        self.old_loaders = set()     # stopped loads still finishing in the background
        self.partial = ""
        self.loading_url = ""
        self.throb_frame = 0
        self.bookmarks = load_json(BOOKMARKS_FILE, None) or list(DEFAULT_BOOKMARKS)
        self.setStyleSheet(STYLE)

        # ---- menus ----
        bar = QMenuBar()
        file_menu = bar.addMenu("&File")
        file_menu.addAction("Open &Location...", self._focus_location, QKeySequence("Ctrl+L"))
        file_menu.addSeparator()
        file_menu.addAction("&Close", lambda: self.frame.request_close() if self.frame else self.close())
        edit_menu = bar.addMenu("&Edit")
        edit_menu.addAction("&Copy", lambda: self._page_action("Copy", self.view.copy))
        edit_menu.addAction("Select &All", lambda: self._page_action("SelectAll", self.view.selectAll))
        view_menu = bar.addMenu("&View")
        view_menu.addAction("&Reload", self.reload, QKeySequence("Ctrl+R"))
        view_menu.addAction("Re&generate Page", lambda: self.reload(regenerate=True))
        view_menu.addAction("&Stop Loading", self.stop, QKeySequence("Esc"))
        view_menu.addSeparator()
        view_menu.addAction("Page So&urce", self.view_source, QKeySequence("Ctrl+U"))
        self.go_menu = bar.addMenu("&Go")
        self.go_menu.aboutToShow.connect(self._fill_go_menu)
        self.bookmarks_menu = bar.addMenu("&Bookmarks")
        self.bookmarks_menu.aboutToShow.connect(self._fill_bookmarks)
        help_menu = bar.addMenu("&Help")
        help_menu.addAction("&About Netscape Navigator", self._about)
        bar.triggered.connect(lambda _a: sound.play("menu"))

        # ---- navigation toolbar ----
        nav = QToolBar()
        nav.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        style = self.style()

        def button(text, icon, slot, tip=""):
            act = QAction(icon, text, self)
            act.setToolTip(tip or text)
            act.triggered.connect(slot)
            nav.addAction(act)
            return act

        self.back_act = button("Back", style.standardIcon(QStyle.SP_ArrowBack), self.back)
        self.fwd_act = button("Forward", style.standardIcon(QStyle.SP_ArrowForward), self.forward)
        button("Reload", style.standardIcon(QStyle.SP_BrowserReload), self.reload)
        button("Home", style.standardIcon(QStyle.SP_DirHomeIcon), self.home)
        button("Search", style.standardIcon(QStyle.SP_FileDialogContentsView), self._search)
        button("Print", style.standardIcon(QStyle.SP_DialogSaveButton), self.print_page, "Print this page")
        self.stop_act = button("Stop", style.standardIcon(QStyle.SP_BrowserStop), self.stop)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        nav.addWidget(spacer)
        self.throbber = QToolButton()
        self.throbber.setIcon(QIcon(throbber_frames()[0]))
        self.throbber.setIconSize(throbber_frames()[0].size())
        self.throbber.setToolTip("Go to the Netscape Netcenter")
        self.throbber.clicked.connect(self.home)
        nav.addWidget(self.throbber)

        # ---- location toolbar ----
        loc = QToolBar()
        bm_button = QToolButton()
        bm_button.setText("Bookmarks")
        bm_button.setPopupMode(QToolButton.InstantPopup)
        bm_button.setMenu(self.bookmarks_menu)
        loc.addWidget(bm_button)
        self.loc_label = QLabel("  Location: ")
        self.loc_label.setStyleSheet("font-family: Tahoma; font-size: 11px;")
        loc.addWidget(self.loc_label)
        self.location = QLineEdit()
        self.location.setStyleSheet("QLineEdit { background: white; border: 1px solid #7F9DB9; padding: 1px; "
                                    "font-family: Tahoma; font-size: 11px; }")
        self.location.returnPressed.connect(lambda: self.navigate(web.normalize(self.location.text())))
        loc.addWidget(self.location)

        # ---- page + status bar ----
        self.view = PageView(self)
        self.site_view = None                 # the real web engine, made the first time a furry-web site is visited
        self.pages = QStackedWidget()
        self.pages.addWidget(self.view)
        status = QWidget()
        status.setObjectName("statusbar")
        status.setAttribute(Qt.WA_StyledBackground, True)
        srow = QHBoxLayout(status)
        srow.setContentsMargins(4, 1, 4, 1)
        self.lock = QLabel()
        self.lock.setPixmap(style.standardIcon(QStyle.SP_DialogNoButton).pixmap(14, 14))
        self.lock.setToolTip("This page is not secure")
        self.status = QLabel("Document: Done")
        self.status.setObjectName("status")
        self.progress = QProgressBar()
        self.progress.setFixedSize(120, 12)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        srow.addWidget(self.lock)
        srow.addWidget(self.status, 1)
        srow.addWidget(self.progress)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setMenuBar(bar)
        root.addWidget(nav)
        root.addWidget(loc)
        root.addWidget(self.pages, 1)
        root.addWidget(status)

        self.throb_timer = QTimer(self)
        self.throb_timer.timeout.connect(self._throb)
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self._render_partial)
        self._update_buttons()

    # ---- navigation ------------------------------------------------------------------
    def resolve(self, href):
        return QUrl(self.url or web.HOME_URL).resolved(QUrl(href)).toString()

    def link_clicked(self, qurl):
        href = qurl.toString()
        url = self.resolve(href)
        if url.startswith("mailto:"):
            self.status.setText("Netscape Mail isn't installed on this computer.")
            sound.play("default")
            return
        text = self.links.get(href) or self.links.get(url) or href
        self.navigate(url, referrer=(self.url, web.title_of(self.page), text))

    def link_hovered(self, qurl):
        self.status.setText(self.resolve(qurl.toString()) if qurl.toString() else
                            ("Document: Done" if self.loader is None else self.status.text()))

    def navigate(self, url, referrer=None, regenerate=False, push=True):
        url = web.normalize(url) if not url.startswith(("http://", "https://", "about:", "file:")) else url
        self.stop(quiet=True)
        if push:
            del self.history[self.index + 1:]
            if not self.history or self.history[-1] != url:
                self.history.append(url)
            self.index = len(self.history) - 1
        self.url = url
        self.location.setText(url)
        self._update_buttons()
        if url == web.HOME_URL:
            box = self._mailbox()
            self._show(web.home_page(self.knowledge, len(box.unread()) if box else 0), url)
            return
        if url.startswith(web.WEBMAIL_URL):
            self._webmail(url)
            return
        if url.startswith("file:"):
            self._local_file(url)
            return
        if url in ("about:", "about:netscape"):
            self._show(ABOUT_PAGE, url)
            return
        if url == "about:blank":
            self._show("<html><head><title></title></head><body></body></html>", url)
            return
        site = sites.site_for(url)
        if site is not None:                  # one of the furry web's real sites (from the archive on E:)
            if not network.is_connected():
                self.status.setText("Dialing your Internet connection...")
                network.connect(self.desktop, then=lambda: self.navigate(url, referrer, regenerate, push=False))
                QTimer.singleShot(300, lambda: self._check_offline(url))
                return
            if not site.installed():
                self._show(sites.not_found_page(url, site), url)
                return
            self._show_site(url)
            return
        cached = None if regenerate else self.cache.get(url)
        person = self.knowledge.person_in(url)
        if cached is not None and person and person[2] and web.life_updated_since(person[0], self.cache.mtime(url)):
            cached = None   # their life moved on since we last saw the page: it's been updated
        if not network.is_connected():
            self.status.setText("Dialing your Internet connection...")
            network.connect(self.desktop, then=lambda: self.navigate(url, referrer, regenerate, push=False))
            QTimer.singleShot(300, lambda: self._check_offline(url))
            return
        if cached is not None:
            self.status.setText(f"Contacting host: {urlparse(url).netloc}...")
            self._start_throbber()
            QTimer.singleShot(400, lambda: self._finish_cached(url, cached))
            return
        self._load(url, referrer)

    # ---- the furry web's real sites ----------------------------------------------------------------------
    def _site_view(self):
        if self.site_view is None:
            from .webview import SiteView
            v = self.site_view = SiteView()
            v.setStyleSheet("border: 1px solid #7F9DB9;")
            v.link_followed.connect(lambda url: self.navigate(url, referrer=(self.url, v.title(), url)))
            v.flash_requested.connect(self._play_flash)
            v.page().linkHovered.connect(lambda u: self.status.setText(sites.logical_url(u) if u else "Document: Done"))
            v.loadStarted.connect(lambda: (self._start_throbber(), self.progress.setRange(0, 100)))
            v.loadProgress.connect(lambda n: (self.progress.setValue(n),
                                              self.status.setText(f"Document: Received {n}%") if n < 100 else None))
            v.loadFinished.connect(self._site_loaded)
            v.titleChanged.connect(self._site_title)
            v.urlChanged.connect(self._site_url_changed)
            self.pages.addWidget(v)
        return self.site_view

    def _show_site(self, url):
        v = self._site_view()
        self.page = ""
        self.links = {}
        self.status.setText(f"Contacting host: {urlparse(url).netloc}...")
        self.pages.setCurrentWidget(v)
        v.open(url)

    def _site_loaded(self, ok):
        if self.site_view is not None:
            self._site_url_changed(self.site_view.url())     # (a redirect back to the same page sends no urlChanged)
        self._stop_throbber()
        self.progress.setValue(0)
        self.status.setText("Document: Done" if ok else "Transfer interrupted!")

    def _site_title(self, title):
        if self.frame is not None and self.pages.currentWidget() is self.site_view:
            self.frame.set_title(f"Netscape: {title}" if title else "Netscape Navigator")

    def _site_url_changed(self, qurl):
        """A redirect inside a site (e.g. after 'Add to Favorites'): keep the address bar and history honest."""
        url = sites.logical_url(qurl.toString())
        if self.pages.currentWidget() is self.site_view and url != self.url and sites.site_for(url):
            self.url = url
            self.location.setText(url)
            if 0 <= self.index < len(self.history):
                if self.index > 0 and self.history[self.index - 1] == url:
                    del self.history[self.index]               # back where we were: no duplicate in Back
                    self.index -= 1
                else:
                    self.history[self.index] = url
            self._update_buttons()

    def _play_flash(self, local):
        """A .swf link on a site: play it in ClaudeXP's Flash Player (it's a file in the archive)."""
        import urllib.request
        from pathlib import Path
        from ...paths import DATA
        try:
            data = urllib.request.urlopen(local, timeout=20).read()
        except OSError:
            return
        name = Path(urlparse(sites.logical_url(local)).path).name or "movie.swf"
        target = DATA / "web_flash" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        from ..flash import open_flash
        open_flash(self.desktop, target)

    def _page_action(self, name, fallback):
        if self.site_view is not None and self.pages.currentWidget() is self.site_view:
            from PySide6.QtWebEngineCore import QWebEnginePage
            self.site_view.triggerPageAction(getattr(QWebEnginePage.WebAction, name))
        else:
            fallback()

    def _local_file(self, url):
        """A page saved on C: or E: (opened from My Computer): shown as it is, no Internet needed."""
        from pathlib import Path
        path = Path(QUrl(url).toLocalFile())
        try:
            page = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            self._error(url, "The file could not be found.")
            return
        self._show(page, url)

    def _mailbox(self):
        from ...life import get as life
        return life().mailbox if life() else None

    def _webmail(self, url):
        box = self._mailbox()
        if box is None:
            self._error(url, "WebMail is not available.")
            return
        if not network.is_connected():
            network.connect(self.desktop, then=lambda: self.navigate(url, push=False))
            return
        if "read?id=" in url:
            try:
                msg_id = int(url.split("read?id=")[1].split("&")[0])
            except ValueError:
                msg_id = -1
            msg = next((m for m in box.messages() if m["id"] == msg_id), None)
            if msg is None:
                self._error(url, "That message could not be found.")
                return
            box.mark_read(msg_id)
            self._show(web.message_page(msg), url)
        else:
            self._show(web.webmail_page([m for m in box.messages() if m.get("folder", "inbox") == "inbox"]), url)

    def _check_offline(self, url):
        dialer = network.get(self.desktop)
        if dialer.connected or url != self.url:
            return
        if dialer.connect_win is None and dialer.progress_win is None:
            self._error(url, "There was no response. You are not connected to the Internet.")
        else:
            QTimer.singleShot(500, lambda: self._check_offline(url))

    def _finish_cached(self, url, page):
        if url != self.url:
            return
        self._stop_throbber()
        self._show(page, url)

    def _load(self, url, referrer):
        self.loading_url = url
        self.partial = ""
        self.loader = web.PageLoader(url, referrer, self.knowledge, self.model, self.num_ctx)
        loader = self.loader
        self.old_loaders.add(loader)   # keep it alive until its thread really ends
        self.loader.chunk.connect(self._chunk)
        self.loader.finished_page.connect(self._finished)
        loader.finished_page.connect(lambda *_: (self.old_loaders.discard(loader), loader.deleteLater()))
        self.status.setText(f"Contacting host: {urlparse(url).netloc}...")
        self.progress.setRange(0, 0)
        self._start_throbber()
        self.view.show_page("<html><body></body></html>")
        self.loader.start()
        self.render_timer.start(600)

    def _chunk(self, text):
        if self.sender() is not self.loader:
            return
        if not self.partial:
            self.status.setText("Host contacted. Waiting for reply...")
            self.progress.setRange(0, 100)
        self.partial = text
        kb = len(text.encode()) / 1024
        self.status.setText(f"Document: Received {kb:.1f}K")
        self.progress.setValue(min(95, int(len(text) / EXPECTED_SIZE * 100)))

    def _render_partial(self):
        if self.partial:
            self.view.show_page(web.clean_html(self.partial))

    def _finished(self, text, err):
        if self.sender() is not self.loader:
            return   # a load that was stopped or replaced
        self.loader = None
        self.render_timer.stop()
        self._stop_throbber()
        page = web.clean_html(text)
        if err == "stopped":
            self.view.show_page(page)
            self.status.setText("Transfer interrupted!")
            return
        if err or "<" not in page:
            self._error(self.loading_url, "The server isn't responding." + (f" ({err})" if err else ""))
            return
        if "</html>" not in page.lower():
            page += "</body></html>"
        self.cache.put(self.loading_url, page)
        self._show(page, self.loading_url)

    def _show(self, page, url):
        self.pages.setCurrentWidget(self.view)
        self.page = page
        self.links = {}
        for href, inner in re.findall(r'<a\s[^>]*href\s*=\s*"([^"]+)"[^>]*>(.*?)</a>', page, re.I | re.S):
            text = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
            if text:
                self.links[href] = text
        self.view.show_page(page)
        self.view.verticalScrollBar().setValue(0)
        title = web.title_of(page)
        if self.frame is not None:
            self.frame.set_title(f"Netscape: {title}" if title else "Netscape Navigator")
        self.status.setText("Document: Done")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

    def _error(self, url, why):
        self._stop_throbber()
        self.pages.setCurrentWidget(self.view)
        if self.frame is not None:
            self.frame.set_title("Netscape Navigator")
        host = urlparse(url).netloc or url
        self.page = ""
        self.view.show_page(f"""<html><head><title>Unable to connect</title></head><body bgcolor="#FFFFFF">
<br><table width="90%" align="center" cellpadding="10" border="1" bgcolor="#F0F0F0"><tr><td>
<font face="Arial" size="3"><b>Netscape is unable to connect to {html.escape(host)}.</b></font><br><br>
<font face="Arial" size="2">{html.escape(why)}<br><br>Check your connection and try again with the
<b>Reload</b> button.</font></td></tr></table></body></html>""")
        self.status.setText("Document: Done")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        sound.play("default")

    def stop(self, quiet=False):
        if self.site_view is not None and self.pages.currentWidget() is self.site_view and not quiet:
            self.site_view.stop()
        if self.loader is not None:
            self.loader.stop()
            if quiet:
                self.loader = None   # its late chunks and result will be ignored
                self.render_timer.stop()
                self._stop_throbber()

    def reload(self, regenerate=False):
        if self.url:
            self.navigate(self.url, regenerate=regenerate, push=False)

    def back(self):
        if self.index > 0:
            self.index -= 1
            self.navigate(self.history[self.index], push=False)

    def forward(self):
        if self.index < len(self.history) - 1:
            self.index += 1
            self.navigate(self.history[self.index], push=False)

    def home(self):
        self.navigate(web.HOME_URL)

    def _search(self):
        self._focus_location()
        self.status.setText("Type what you're looking for in the Location box and press Enter.")

    def _focus_location(self):
        self.location.setFocus()
        self.location.selectAll()

    def _update_buttons(self):
        self.back_act.setEnabled(self.index > 0)
        self.fwd_act.setEnabled(self.index < len(self.history) - 1)

    # ---- throbber ----------------------------------------------------------------------
    def _start_throbber(self):
        self.stop_act.setEnabled(True)
        if not self.throb_timer.isActive():
            self.throb_timer.start(110)

    def _stop_throbber(self):
        self.throb_timer.stop()
        self.stop_act.setEnabled(False)
        self.throb_frame = 0
        self.throbber.setIcon(QIcon(throbber_frames()[0]))

    def _throb(self):
        frames = throbber_frames()
        self.throb_frame = (self.throb_frame + 1) % len(frames)
        self.throbber.setIcon(QIcon(frames[self.throb_frame]))

    # ---- menus --------------------------------------------------------------------------
    def _fill_go_menu(self):
        m = self.go_menu
        m.clear()
        m.addAction("&Back", self.back).setEnabled(self.index > 0)
        m.addAction("&Forward", self.forward).setEnabled(self.index < len(self.history) - 1)
        m.addAction("&Home", self.home)
        m.addSeparator()
        for i in range(len(self.history) - 1, max(-1, len(self.history) - 11), -1):
            url = self.history[i]
            act = m.addAction(url, lambda i=i: self._go_to(i))
            act.setCheckable(True)
            act.setChecked(i == self.index)

    def _go_to(self, i):
        self.index = i
        self.navigate(self.history[i], push=False)

    def _fill_bookmarks(self):
        m = self.bookmarks_menu
        m.clear()
        m.addAction("&Add Bookmark", self.add_bookmark, QKeySequence("Ctrl+D"))
        m.addSeparator()
        for bm in self.bookmarks:
            m.addAction(bm["title"], lambda u=bm["url"]: self.navigate(u))

    def add_bookmark(self):
        if not self.url or any(b["url"] == self.url for b in self.bookmarks):
            return
        on_site = self.site_view is not None and self.pages.currentWidget() is self.site_view
        title = (self.site_view.title() if on_site else web.title_of(self.page)) or self.url
        self.bookmarks.append({"title": title, "url": self.url})
        save_json(BOOKMARKS_FILE, self.bookmarks)
        self.status.setText("Bookmark added.")

    def print_page(self):
        if self.site_view is not None and self.pages.currentWidget() is self.site_view:
            self.status.setText("This page can't be printed from Netscape 4.79.")
            sound.play("default")
            return
        from ...printing import print_document
        title = web.title_of(self.page) or self.url or "Netscape"
        print_document(self.desktop, title, self.view.document())

    def view_source(self):
        if self.site_view is not None and self.pages.currentWidget() is self.site_view:
            self.site_view.page().toHtml(self._show_source)
            return
        self._show_source(self.page or "")

    def _show_source(self, source):
        text = QPlainTextEdit(source)
        text.setReadOnly(True)
        text.setFont(QFont("Courier New", 9))
        text.setStyleSheet("QPlainTextEdit { background: white; color: black; }")
        win = XPWindow(self.desktop, f"Source of: {self.url}", text, nav_icon(), size=(640, 460))
        self.desktop.open_window(win)

    def _about(self):
        self.navigate("about:")

    # ---- lifecycle ------------------------------------------------------------------------
    def start(self, url=None):
        if url:
            self.navigate(url)
        else:
            self.home()

    def network_lost(self):
        if self.loader is not None:
            self.stop()

    def shutdown(self):
        if self.loader is not None:
            self.loader.stop()
        self.render_timer.stop()
        self.throb_timer.stop()

    def closeEvent(self, event):
        self.shutdown()
        event.accept()
