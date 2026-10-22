"""The browsers of 2011 on ClaudeXP's web engine (the model-written Web, the Furry Web's real sites, Hotmail and
LiveJournal): Internet Explorer 9 with its one-row chrome and tab beside the address bar, and Mozilla Firefox 7 with
the orange Firefox button and the Google search box. Both are the XP Browser class with a different face."""
import math
import traceback

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QKeySequence, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QMenu, QMenuBar, QProgressBar, QSizePolicy, QToolBar,
                               QToolButton, QWidget)
from shiboken6 import isValid

from .. import network, sound
from ..paths import PROGRAM_FILES, icon as asset_icon
from ..wm import AeroWindow

IE9_STYLE = """
QWidget { font-family: 'Segoe UI'; font-size: 12px; }
QMenu { background: #F0F0F0; border: 1px solid #979797; }
QMenu::item { padding: 4px 24px 4px 28px; }
QMenu::item:selected { background: #CCE8FF; border: 1px solid #99D1FF; }
QMenu::separator { height: 1px; background: #D7D7D7; margin: 3px 2px; }
QToolBar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F7F9FC, stop:1 #E3EAF2);
           border: none; border-bottom: 1px solid #B9C9DA; spacing: 3px; padding: 3px 4px; }
QToolButton { border: 1px solid transparent; border-radius: 3px; padding: 2px; }
QToolButton:hover { border: 1px solid #7DA2CE; background: #E8F0FA; }
QToolButton::menu-indicator { image: none; }
QLineEdit#address { background: white; border: 1px solid #ABADB3; padding: 2px 4px; min-height: 20px; }
QToolButton#tab { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #E9EEF5);
                  border: 1px solid #A9B9CC; border-bottom: none; border-top-left-radius: 4px;
                  border-top-right-radius: 4px; padding: 3px 10px; min-width: 120px; text-align: left; }
QToolButton#newtab { border: 1px solid #A9B9CC; border-bottom: none; border-top-left-radius: 4px;
                     border-top-right-radius: 4px; padding: 3px 6px; background: #EEF2F7; }
QWidget#statusbar { background: #F0F0F0; border-top: 1px solid #D5D5D5; }
QLabel#status { color: #1E1E1E; }
"""
FF_STYLE = """
QWidget { font-family: 'Segoe UI'; font-size: 12px; }
QMenu { background: #F0F0F0; border: 1px solid #979797; }
QMenu::item { padding: 4px 24px 4px 28px; }
QMenu::item:selected { background: #CCE8FF; border: 1px solid #99D1FF; }
QMenu::separator { height: 1px; background: #D7D7D7; margin: 3px 2px; }
QToolBar#tabs { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5A86BE, stop:1 #3E6AA4);
                border: none; spacing: 2px; padding: 4px 4px 0 4px; }
QToolBar#nav { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F5F7FA, stop:1 #E6EBF1);
               border: none; border-bottom: 1px solid #B9C4D1; spacing: 4px; padding: 3px 4px; }
QToolButton { border: 1px solid transparent; border-radius: 3px; padding: 2px; }
QToolButton:hover { border: 1px solid #8DA6C3; background: #E8F0FA; }
QToolButton::menu-indicator { image: none; }
QToolButton#ffbutton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFA735, stop:1 #E8650F);
                       color: white; font-weight: bold; border: 1px solid #B9530C; border-radius: 4px;
                       padding: 3px 12px; }
QToolButton#ffbutton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFB955, stop:1 #F07420); }
QToolButton#fftab { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F7F9FC, stop:1 #E6EBF1);
                    border: 1px solid #2E5584; border-bottom: none; border-top-left-radius: 5px;
                    border-top-right-radius: 5px; padding: 4px 12px; min-width: 140px; text-align: left; }
QToolButton#ffnewtab { color: white; font-size: 15px; padding: 1px 8px; }
QLineEdit#address { background: white; border: 1px solid #ABADB3; border-radius: 3px; padding: 2px 4px; min-height: 22px; }
QLineEdit#google { background: white; border: 1px solid #ABADB3; border-radius: 3px; padding: 2px 4px; min-height: 22px;
                   color: #6D6D6D; }
QLineEdit#google:focus { color: black; }
QWidget#statusbar { background: #F0F0F0; border-top: 1px solid #D5D5D5; }
QLabel#status { color: #1E1E1E; }
"""
_frames = {}
_open = {}


def spinner_frames(size=16, colour="#4A90D9"):
    key = (size, colour)
    if key not in _frames:
        out = []
        for i in range(8):
            pm = QPixmap(size, size)
            pm.fill(Qt.transparent)
            p = QPainter(pm)
            p.setRenderHint(QPainter.Antialiasing)
            r = size / 2
            for j in range(8):
                a = math.radians(i * 45 + j * 45)
                alpha = int(255 * (j + 1) / 8)
                c = QColor(colour)
                c.setAlpha(alpha)
                p.setPen(Qt.NoPen)
                p.setBrush(c)
                d = r * 0.3
                p.drawEllipse(QRectF(r + math.cos(a) * (r - d) - d / 2, r + math.sin(a) * (r - d) - d / 2, d, d))
            p.end()
            out.append(pm)
        _frames[key] = out
    return _frames[key]


def _glyph(text, size=18, colour="#2F5F99"):
    pm = QPixmap(size + 4, size + 4)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    f = QFont("Segoe UI Symbol")
    f.setPixelSize(size)
    p.setFont(f)
    p.setPen(QColor(colour))
    p.drawText(pm.rect(), Qt.AlignCenter, text)
    p.end()
    return QIcon(pm)


def firefox_icon():
    ic = asset_icon("Firefox.ico")
    if not ic.isNull():
        return ic
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, 32, 32)
    g.setColorAt(0, QColor("#FFB347"))
    g.setColorAt(1, QColor("#E8650F"))
    p.setPen(QPen(QColor("#B9530C"), 1))
    p.setBrush(g)
    p.drawEllipse(QRectF(3, 3, 26, 26))
    p.setBrush(QColor("#3E6AA4"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QRectF(9, 9, 14, 14))
    p.end()
    return QIcon(pm)


def _status_bar(self):
    status = QWidget()
    status.setObjectName("statusbar")
    status.setAttribute(Qt.WA_StyledBackground, True)
    srow = QHBoxLayout(status)
    srow.setContentsMargins(6, 1, 6, 1)
    srow.setSpacing(6)
    self.lock = QLabel()
    self.status = QLabel(self.DONE)
    self.status.setObjectName("status")
    self.progress = QProgressBar()
    self.progress.setFixedSize(120, 10)
    self.progress.setTextVisible(False)
    self.progress.setRange(0, 100)
    self.progress.setValue(0)
    srow.addWidget(self.lock)
    srow.addWidget(self.status, 1)
    srow.addWidget(self.progress)
    return status


def _menus(self, app_name, extra=None):
    """A hidden menu bar (both browsers hide theirs in 2011): the actions' shortcuts still work."""
    bar = QMenuBar()
    file_menu = bar.addMenu("&File")
    file_menu.addAction("Open &Location...", self._focus_location, QKeySequence("Ctrl+L"))
    file_menu.addAction("&Print...", self.print_page, QKeySequence("Ctrl+P"))
    file_menu.addAction("&Close", lambda: self.frame.request_close() if self.frame else self.close())
    edit_menu = bar.addMenu("&Edit")
    edit_menu.addAction("&Copy", lambda: self._page_action("Copy", self.view.copy), QKeySequence("Ctrl+C"))
    edit_menu.addAction("Select &All", lambda: self._page_action("SelectAll", self.view.selectAll), QKeySequence("Ctrl+A"))
    view_menu = bar.addMenu("&View")
    view_menu.addAction("&Reload", self.reload, QKeySequence("F5"))
    view_menu.addAction("Re&write Page", lambda: self.reload(regenerate=True))
    view_menu.addAction("&Stop", self.stop, QKeySequence("Esc"))
    view_menu.addAction("Page So&urce", self.view_source, QKeySequence("Ctrl+U"))
    self.go_menu = QMenu("History", self)
    self.go_menu.aboutToShow.connect(self._fill_go_menu)
    self.bookmarks_menu = QMenu("Bookmarks", self)
    self.bookmarks_menu.aboutToShow.connect(self._fill_bookmarks)
    bar.addMenu(self.go_menu)
    bar.addMenu(self.bookmarks_menu)
    help_menu = bar.addMenu("&Help")
    help_menu.addAction(f"&About {app_name}", self._about)
    bar.triggered.connect(lambda _a: sound.play("menu"))
    bar.hide()
    for top in bar.actions():                        # the shortcuts keep working with the menus out of sight
        if top.menu() is not None:
            for act in top.menu().actions():
                if not act.shortcut().isEmpty():
                    self.addAction(act)
    return bar


def _tool(toolbar, icon, tip, slot, size=20, name=None, menu=None):
    b = QToolButton()
    if name:
        b.setObjectName(name)
    b.setIcon(icon)
    b.setIconSize(QSize(size, size))
    b.setToolTip(tip)
    if slot is not None:
        b.clicked.connect(lambda _c=False: slot())
    if menu is not None:
        b.setMenu(menu)
        b.setPopupMode(QToolButton.InstantPopup)
    toolbar.addWidget(b)
    return b


# ---- Internet Explorer 9 --------------------------------------------------------------------------------------------
def _ie_base():
    from claudexp.programs.navigator import iexplore
    return iexplore


def make_ie9():
    iexplore = _ie_base()

    class IE9Browser(iexplore.IEBrowser):
        APP = "Windows Internet Explorer"
        TITLE = "{} - Windows Internet Explorer"

        def _build_chrome(self):
            self.setStyleSheet(IE9_STYLE)
            bar = _menus(self, "Internet Explorer")
            nav = QToolBar()
            nav.setMovable(False)
            self.back_act = QAction(iexplore.tool_icon("back", 22), "Back", self)
            self.back_act.triggered.connect(self.back)
            self.fwd_act = QAction(iexplore.tool_icon("forward", 22), "Forward", self)
            self.fwd_act.triggered.connect(self.forward)
            for act in (self.back_act, self.fwd_act):
                nav.addAction(act)
                nav.widgetForAction(act).setIconSize(QSize(24, 24))
            self.loc_label = QLabel("")
            self.location = QLineEdit()
            self.location.setObjectName("address")
            self.location.setPlaceholderText("Search or enter address")
            self.location.addAction(iexplore.tool_icon("doc", 16), QLineEdit.LeadingPosition)
            self.location.returnPressed.connect(self._go_typed)
            self.location.setMinimumWidth(260)
            self.location.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            nav.addWidget(self.location)
            self.stop_act = QAction(iexplore.tool_icon("stop", 16), "Stop", self)
            self.stop_act.triggered.connect(self.stop)
            refresh = QAction(iexplore.tool_icon("refresh", 16), "Refresh", self)
            refresh.triggered.connect(self.reload)
            nav.addAction(refresh)
            nav.addAction(self.stop_act)
            self.throbber = QToolButton()
            self.throbber.setIcon(QIcon(spinner_frames()[0]))
            self.throbber.setIconSize(QSize(16, 16))
            self.throbber.setToolTip("Internet Explorer")
            self.throbber.clicked.connect(lambda: self.navigate("http://windows.microsoft.com/ie"))
            nav.addWidget(self.throbber)
            self.tab = QToolButton()
            self.tab.setObjectName("tab")
            self.tab.setText("New Tab")
            self.tab.setIcon(iexplore.tool_icon("doc", 16))
            self.tab.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            nav.addWidget(self.tab)
            newtab = QToolButton()
            newtab.setObjectName("newtab")
            newtab.setText("□")
            newtab.setToolTip("New tab (Ctrl+T)")
            newtab.clicked.connect(lambda _c=False: self.status.setText("Tabs: one at a time on this computer."))
            nav.addWidget(newtab)
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            spacer.setMaximumWidth(30)
            nav.addWidget(spacer)
            _tool(nav, iexplore.tool_icon("home", 20), "Home (Alt+Home)", self.home)
            _tool(nav, iexplore.tool_icon("favorites", 20), "View favorites, feeds, and history (Alt+C)", None,
                  menu=self.bookmarks_menu)
            tools = QMenu(self)
            tools.addAction("Print...", self.print_page)
            tools.addAction("Zoom (100%)", lambda: None)
            tools.addAction("Safety", lambda: self.status.setText("InPrivate Browsing is off."))
            tools.addAction("View downloads", lambda: self.status.setText("No downloads."))
            tools.addAction("Manage add-ons", lambda: self.status.setText("Add-ons: the toolbars Ad-Aware finds."))
            tools.addAction("F12 developer tools", self.view_source)
            tools.addAction("Compatibility View settings", lambda: None)
            tools.addSeparator()
            tools.addAction("Internet options", self._options)
            tools.addAction("About Internet Explorer", self._about)
            _tool(nav, _glyph("⚙", 18, "#4C607A"), "Tools (Alt+X)", None, menu=tools)
            status = _status_bar(self)
            from claudexp.maintenance.toolbars import AdBars
            self.adbars = AdBars(self)
            return bar, [nav, self.adbars], status

        def throbber_frames(self):
            return spinner_frames()

        def _set_title(self, title):
            super()._set_title(title)
            if hasattr(self, "tab"):
                self.tab.setText((title or "New Tab")[:28])

        def _error_page(self, host, why):
            import html
            return f"""<html><head><title>This page can't be displayed</title></head><body bgcolor="#FFFFFF">
<font face="Segoe UI" size="4" color="#1E395B"><b>This page can't be displayed</b></font>
<font face="Segoe UI" size="2"><ul><li>Make sure the web address <b>{html.escape(host)}</b> is correct.</li>
<li>Look for the page with your search engine.</li><li>Refresh the page in a few minutes.</li></ul>
<font color="#808080">({html.escape(why)})</font></font></body></html>"""

    return IE9Browser


# ---- Mozilla Firefox 7 ---------------------------------------------------------------------------------------------
FF_HOME = "http://www.google.com/firefox"
FF_SEARCH = "http://www.google.com/search?q="
FF_BOOKMARKS = PROGRAM_FILES / "Mozilla Firefox" / "bookmarks.json"
FF_DEFAULT_BOOKMARKS = [{"title": "Getting Started", "url": "http://www.mozilla.com/firefox/central/"},
                        {"title": "Most Visited", "url": "http://www.google.com/"},
                        {"title": "Fur Affinity", "url": "http://www.furaffinity.net/"},
                        {"title": "Hotmail", "url": "http://www.hotmail.com/"},
                        {"title": "LiveJournal", "url": "http://www.livejournal.com/"}]
FF_ABOUT = """<html><head><title>About Mozilla Firefox</title></head><body bgcolor="#FFFFFF">
<font face="Segoe UI" size="5" color="#E8650F"><b>Mozilla Firefox</b></font><br>
<font face="Segoe UI" size="2">Version 7.0.1<br><br>Firefox is made by Mozilla, a global community working together
to keep the Web open, public and accessible to all.<br><br>&copy; 1998-2011 Contributors.</font></body></html>"""


def make_firefox():
    from claudexp.programs.navigator import browser as nb

    class FirefoxBrowser(nb.Browser):
        APP = "Mozilla Firefox"
        TITLE = "{} - Mozilla Firefox"
        HOME = FF_HOME
        SEARCH = FF_SEARCH
        DONE = "Done"
        ABOUT = FF_ABOUT
        BOOKMARKS = FF_BOOKMARKS
        DEFAULT_BOOKMARKS = FF_DEFAULT_BOOKMARKS

        def _build_chrome(self):
            self.setStyleSheet(FF_STYLE)
            bar = _menus(self, "Firefox")
            iexplore = _ie_base()
            # the tab strip with the Firefox button
            tabs = QToolBar()
            tabs.setObjectName("tabs")
            tabs.setMovable(False)
            ffmenu = QMenu(self)
            ffmenu.addAction("New Tab", lambda: self.status.setText("Tabs: one at a time on this computer."))
            ffmenu.addAction("New Window", lambda: launch_firefox(self.desktop))
            ffmenu.addSeparator()
            ffmenu.addMenu(self.bookmarks_menu)
            ffmenu.addMenu(self.go_menu)
            ffmenu.addAction("Downloads", lambda: self.status.setText("No downloads."))
            ffmenu.addAction("Add-ons", lambda: self.status.setText("No add-ons installed."))
            ffmenu.addAction("Options", lambda: self._options())
            ffmenu.addSeparator()
            ffmenu.addAction("Print...", self.print_page)
            ffmenu.addAction("Page Source", self.view_source)
            ffmenu.addSeparator()
            ffmenu.addAction("About Firefox", self._about)
            ffmenu.addAction("Exit", lambda: self.frame.request_close() if self.frame else self.close())
            ffb = QToolButton()
            ffb.setObjectName("ffbutton")
            ffb.setText("Firefox  ▾")
            ffb.setMenu(ffmenu)
            ffb.setPopupMode(QToolButton.InstantPopup)
            tabs.addWidget(ffb)
            self.tab = QToolButton()
            self.tab.setObjectName("fftab")
            self.tab.setText("New Tab")
            self.tab.setIcon(iexplore.tool_icon("doc", 16))
            self.tab.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            tabs.addWidget(self.tab)
            newtab = QToolButton()
            newtab.setObjectName("ffnewtab")
            newtab.setText("+")
            newtab.setToolTip("Open a new tab")
            newtab.clicked.connect(lambda _c=False: self.status.setText("Tabs: one at a time on this computer."))
            tabs.addWidget(newtab)
            # the navigation toolbar
            nav = QToolBar()
            nav.setObjectName("nav")
            nav.setMovable(False)
            self.back_act = QAction(iexplore.tool_icon("back", 22), "Back", self)
            self.back_act.triggered.connect(self.back)
            self.fwd_act = QAction(iexplore.tool_icon("forward", 22), "Forward", self)
            self.fwd_act.triggered.connect(self.forward)
            for act in (self.back_act, self.fwd_act):
                nav.addAction(act)
                nav.widgetForAction(act).setIconSize(QSize(24, 24))
            self.loc_label = QLabel("")
            self.location = QLineEdit()
            self.location.setObjectName("address")
            self.location.setPlaceholderText("Go to a Website")
            self.location.addAction(iexplore.tool_icon("globe", 16), QLineEdit.LeadingPosition)
            self.location.returnPressed.connect(self._go_typed)
            self.location.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            star = QAction(_glyph("☆", 16, "#777777"), "Bookmark this page", self)
            star.triggered.connect(self.add_bookmark)
            self.location.addAction(star, QLineEdit.TrailingPosition)
            nav.addWidget(self.location)
            self.stop_act = QAction(iexplore.tool_icon("stop", 16), "Stop", self)
            self.stop_act.triggered.connect(self.stop)
            refresh = QAction(iexplore.tool_icon("refresh", 16), "Reload current page", self)
            refresh.triggered.connect(self.reload)
            nav.addAction(refresh)
            nav.addAction(self.stop_act)
            self.search_box = QLineEdit()
            self.search_box.setObjectName("google")
            self.search_box.setPlaceholderText("Google")
            self.search_box.setFixedWidth(180)
            self.search_box.returnPressed.connect(self._google)
            nav.addWidget(self.search_box)
            _tool(nav, iexplore.tool_icon("home", 20), "Firefox Start Page", self.home)
            _tool(nav, _glyph("☆", 18, "#4C607A"), "Display your bookmarks", None, menu=self.bookmarks_menu)
            self.throbber = QToolButton()
            self.throbber.setIcon(QIcon(spinner_frames(16, "#E8650F")[0]))
            self.throbber.setIconSize(QSize(16, 16))
            self.throbber.setToolTip("Mozilla Firefox")
            self.throbber.clicked.connect(self.home)
            nav.addWidget(self.throbber)
            status = _status_bar(self)
            return bar, [tabs, nav], status

        def throbber_frames(self):
            return spinner_frames(16, "#E8650F")

        def app_icon(self):
            return firefox_icon()

        def _google(self):
            q = self.search_box.text().strip()
            if q:
                from urllib.parse import quote_plus
                self.navigate(self.SEARCH + quote_plus(q))

        def _options(self):
            from claudexp.cpl_extra import internet_options
            internet_options(self.desktop)

        def _set_title(self, title):
            super()._set_title(title)
            if hasattr(self, "tab"):
                self.tab.setText((title or "New Tab")[:28])

        def _mailto(self, url):
            from claudexp.programs.outlook import open_outlook
            from urllib.parse import unquote, urlparse
            win = open_outlook(self.desktop)
            if win is not None and isValid(win):
                win.content.compose(to=unquote(urlparse(url).path) if url.startswith("mailto:") else "")

        def _error_page(self, host, why):
            import html
            return f"""<html><head><title>Server not found</title></head><body bgcolor="#FFFFFF">
<font face="Segoe UI" size="4" color="#1E1E1E"><b>Server not found</b></font><br><br>
<font face="Segoe UI" size="2">Firefox can't find the server at <b>{html.escape(host)}</b>.<ul>
<li>Check the address for typing errors such as <b>ww</b>.example.com instead of <b>www</b>.example.com</li>
<li>If you are unable to load any pages, check your computer's network connection.</li></ul>
<font color="#808080">({html.escape(why)})</font></font></body></html>"""

    return FirefoxBrowser


# ---- the programs ----------------------------------------------------------------------------------------------------
def _launch(desktop, key, make, name, icon, url=None, size=(900, 650)):
    frame = _open.get(key)
    if frame is not None and isValid(frame):
        desktop.open_window(frame)
        if url:
            frame.content.navigate(url)
        return
    try:
        browser = make()(desktop)
    except Exception:
        from ..placeholder import open_placeholder
        open_placeholder(desktop, name, icon, f"{name} couldn't start.\n\n" + traceback.format_exc(limit=3),
                         sound_event="error")
        return
    if not _open.get(key + ":listening"):
        network.on_disconnect(desktop, lambda quiet: _network_lost(key, quiet))
        _open[key + ":listening"] = True
    frame = AeroWindow(desktop, name, browser, icon, size=size)
    browser.frame = frame
    frame.destroyed.connect(lambda *_: _open.pop(key, None))
    _open[key] = frame
    desktop.open_window(frame)
    browser.start(url)


def _network_lost(key, quiet):
    frame = _open.get(key)
    if frame is not None and isValid(frame):
        frame.content.network_lost()


def _shutdown(key):
    frame = _open.pop(key, None)
    if frame is not None and isValid(frame):
        frame.content.shutdown()
        frame.desktop.close_window(frame)


def launch_ie(desktop, url=None):
    _launch(desktop, "ie", make_ie9, "Windows Internet Explorer", _ie_base().ie_icon(), url)


def shutdown_ie():
    _shutdown("ie")


def launch_firefox(desktop, url=None):
    _launch(desktop, "firefox", make_firefox, "Mozilla Firefox", firefox_icon(), url)


def shutdown_firefox():
    _shutdown("firefox")


def open_url(desktop, url=None):
    """A link from another program opens in the default browser (Control Panel > Default Programs)."""
    try:
        from claudexp.programs.people import load_json
        from ..paths import DATA
        default = load_json(DATA / "cpl.json", {}).get("default_browser", "Internet Explorer")
    except Exception:
        default = "Internet Explorer"
    if default == "Mozilla Firefox":
        launch_firefox(desktop, url)
    else:
        launch_ie(desktop, url)


def install():
    """Internet Explorer is IE9 everywhere in the XP code, and links open in the default browser."""
    from claudexp.programs import navigator
    iexplore = _ie_base()
    iexplore.launch = launch_ie
    iexplore.shutdown = shutdown_ie
    navigator.open_url = open_url
