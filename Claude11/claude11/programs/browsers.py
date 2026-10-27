"""The browsers of 2025 on ClaudeXP's web engine (the model-written Web, the Furry Web's real sites, Outlook.com and
LiveJournal): Microsoft Edge with its rounded tabs, the pill address bar and the Settings-and-more menu, and Mozilla
Firefox 144 in its Proton look. Both are the XP Browser class with a different face."""
import math
import traceback

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QKeySequence, QLinearGradient, QPainter, QPainterPath, QPen, \
    QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QMenu, QMenuBar, QProgressBar, QSizePolicy, QToolBar,
                               QToolButton, QWidget)
from shiboken6 import isValid

from .. import network, sound
from ..paths import PROGRAM_FILES, icon as asset_icon
from ..wm import MicaWindow

MENU_CSS = """
QMenu { background: #F9F9F9; border: 1px solid #E0E0E0; border-radius: 8px; padding: 4px; }
QMenu::item { padding: 6px 28px 6px 12px; border-radius: 4px; margin: 1px 2px; }
QMenu::item:selected { background: #EAEAEA; }
QMenu::separator { height: 1px; background: #E5E5E5; margin: 4px 8px; }
"""
EDGE_STYLE = """
QWidget { font-family: 'Segoe UI Variable Text', 'Segoe UI'; font-size: 12px; color: #1A1A1A; }
""" + MENU_CSS + """
QToolBar#tabs { background: #DEE4EB; border: none; spacing: 2px; padding: 6px 8px 0 8px; }
QToolBar#nav { background: #FFFFFF; border: none; border-bottom: 1px solid #E5E5E5; spacing: 2px; padding: 4px 8px; }
QToolButton { border: none; border-radius: 6px; padding: 4px; }
QToolButton:hover { background: rgba(0, 0, 0, 16); }
QToolButton:disabled { color: #9A9A9A; }
QToolButton::menu-indicator { image: none; }
QToolButton#tab { background: #FFFFFF; border: none; border-top-left-radius: 8px; border-top-right-radius: 8px;
                  padding: 6px 12px; min-width: 170px; text-align: left; }
QToolButton#tab:hover { background: #FFFFFF; }
QToolButton#newtab { padding: 2px 8px; font-size: 15px; }
QToolButton#profile { padding: 2px; border-radius: 12px; }
QLineEdit#address { background: #F0F3F6; border: 1px solid transparent; border-radius: 16px; padding: 5px 12px;
                    min-height: 22px; }
QLineEdit#address:focus { background: #FFFFFF; border: 1px solid #0067C0; }
QWidget#statusbar { background: #F3F3F3; border-top: 1px solid #E5E5E5; }
QLabel#status { color: #5C5C5C; }
QProgressBar { border: none; background: #E0E0E0; border-radius: 2px; }
QProgressBar::chunk { background: #0067C0; border-radius: 2px; }
"""
FF_STYLE = """
QWidget { font-family: 'Segoe UI Variable Text', 'Segoe UI'; font-size: 12px; color: #15141A; }
""" + MENU_CSS + """
QToolBar#tabs { background: #F0F0F4; border: none; spacing: 4px; padding: 6px 8px 4px 8px; }
QToolBar#nav { background: #F9F9FB; border: none; border-bottom: 1px solid #E0E0E6; spacing: 4px; padding: 4px 8px; }
QToolButton { border: none; border-radius: 4px; padding: 4px; }
QToolButton:hover { background: rgba(0, 0, 0, 18); }
QToolButton::menu-indicator { image: none; }
QToolButton#fftab { background: #FFFFFF; border: none; border-radius: 4px; padding: 7px 12px; min-width: 170px;
                    text-align: left; }
QToolButton#ffnewtab { font-size: 15px; padding: 2px 8px; }
QToolButton#hamburger { font-size: 16px; padding: 2px 8px; }
QLineEdit#address { background: #FFFFFF; border: 1px solid transparent; border-radius: 4px; padding: 5px 10px;
                    min-height: 22px; }
QLineEdit#address:focus { border: 1px solid #0060DF; }
QWidget#statusbar { background: #F0F0F4; border-top: 1px solid #E0E0E6; }
QLabel#status { color: #5B5B66; }
QProgressBar { border: none; background: #E0E0E6; border-radius: 2px; }
QProgressBar::chunk { background: #0060DF; border-radius: 2px; }
"""
_frames = {}
_open = {}


def spinner_frames(size=16, colour="#0067C0"):
    key = (size, colour)
    if key not in _frames:
        out = []
        for i in range(8):
            pm = QPixmap(size, size)
            pm.fill(Qt.transparent)
            p = QPainter(pm)
            p.setRenderHint(QPainter.Antialiasing)
            r = size / 2
            pen = QPen(QColor(colour), 2)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            p.drawArc(QRectF(2, 2, size - 4, size - 4), -i * 45 * 16, 270 * 16)
            p.end()
            out.append(pm)
        _frames[key] = out
    return _frames[key]


def _glyph(text, size=16, colour="#1A1A1A"):
    pm = QPixmap(size + 8, size + 8)
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


def _arrow(direction, size=20, colour="#1A1A1A"):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(colour), 1.6)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    c = size / 2
    if direction == "back":
        p.drawLine(QRectF(c - 6, c, 0, 0).topLeft(), QRectF(c + 6, c, 0, 0).topLeft())
        p.drawLine(QRectF(c - 6, c, 0, 0).topLeft(), QRectF(c - 1, c - 5, 0, 0).topLeft())
        p.drawLine(QRectF(c - 6, c, 0, 0).topLeft(), QRectF(c - 1, c + 5, 0, 0).topLeft())
    elif direction == "forward":
        p.drawLine(QRectF(c - 6, c, 0, 0).topLeft(), QRectF(c + 6, c, 0, 0).topLeft())
        p.drawLine(QRectF(c + 6, c, 0, 0).topLeft(), QRectF(c + 1, c - 5, 0, 0).topLeft())
        p.drawLine(QRectF(c + 6, c, 0, 0).topLeft(), QRectF(c + 1, c + 5, 0, 0).topLeft())
    elif direction == "refresh":
        p.drawArc(QRectF(c - 6, c - 6, 12, 12), 30 * 16, 300 * 16)
        p.drawLine(QRectF(c + 5, c - 7, 0, 0).topLeft(), QRectF(c + 6, c - 2, 0, 0).topLeft())
        p.drawLine(QRectF(c + 6, c - 2, 0, 0).topLeft(), QRectF(c + 1, c - 3, 0, 0).topLeft())
    elif direction == "home":
        path = QPainterPath()
        path.moveTo(c - 7, c + 1)
        path.lineTo(c, c - 6)
        path.lineTo(c + 7, c + 1)
        p.drawPath(path)
        p.drawRect(QRectF(c - 5, c, 10, 6))
    elif direction == "star":
        path = QPainterPath()
        for i in range(10):
            a = math.radians(-90 + i * 36)
            r = 7 if i % 2 == 0 else 3
            pt = QRectF(c + math.cos(a) * r, c + math.sin(a) * r, 0, 0).topLeft()
            if i == 0:
                path.moveTo(pt)
            else:
                path.lineTo(pt)
        path.closeSubpath()
        p.drawPath(path)
    elif direction == "dots":
        p.setBrush(QColor(colour))
        p.setPen(Qt.NoPen)
        for dx in (-5, 0, 5):
            p.drawEllipse(QRectF(c + dx - 1.5, c - 1.5, 3, 3))
    elif direction == "lock":
        p.drawRoundedRect(QRectF(c - 5, c - 1, 10, 8), 1.5, 1.5)
        p.drawArc(QRectF(c - 3.5, c - 7, 7, 8), 0, 180 * 16)
    elif direction == "collections":
        p.drawRoundedRect(QRectF(c - 6, c - 6, 12, 12), 2, 2)
        p.drawLine(QRectF(c - 3, c - 2, 0, 0).topLeft(), QRectF(c + 3, c - 2, 0, 0).topLeft())
        p.drawLine(QRectF(c - 3, c + 2, 0, 0).topLeft(), QRectF(c + 3, c + 2, 0, 0).topLeft())
    elif direction == "puzzle":
        p.drawRoundedRect(QRectF(c - 6, c - 4, 12, 10), 2, 2)
        p.drawEllipse(QRectF(c - 2.5, c - 8, 5, 5))
    p.end()
    return QIcon(pm)


def edge_icon(size=32):
    """Microsoft Edge's wave, near enough: a blue-green disc with the white swoosh."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    g = QLinearGradient(4 * s, 4 * s, 28 * s, 28 * s)
    g.setColorAt(0, QColor("#0C59A4"))
    g.setColorAt(0.5, QColor("#1E88D1"))
    g.setColorAt(1, QColor("#49C1A4"))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawEllipse(QRectF(2 * s, 2 * s, 28 * s, 28 * s))
    pen = QPen(QColor("#FFFFFF"), 5 * s)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(8 * s, 8 * s, 16 * s, 16 * s), 20 * 16, 250 * 16)
    p.drawLine(QRectF(9 * s, 16 * s, 0, 0).topLeft(), QRectF(23 * s, 16 * s, 0, 0).topLeft())
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
    g.setColorAt(0, QColor("#FF9640"))
    g.setColorAt(1, QColor("#E31587"))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawEllipse(QRectF(3, 3, 26, 26))
    p.setBrush(QColor("#20123A"))
    p.drawEllipse(QRectF(10, 10, 12, 12))
    p.end()
    return QIcon(pm)


def _status_bar(self):
    status = QWidget()
    status.setObjectName("statusbar")
    status.setAttribute(Qt.WA_StyledBackground, True)
    srow = QHBoxLayout(status)
    srow.setContentsMargins(8, 2, 8, 2)
    srow.setSpacing(6)
    self.lock = QLabel()
    self.status = QLabel(self.DONE)
    self.status.setObjectName("status")
    self.progress = QProgressBar()
    self.progress.setFixedSize(120, 4)
    self.progress.setTextVisible(False)
    self.progress.setRange(0, 100)
    self.progress.setValue(0)
    srow.addWidget(self.lock)
    srow.addWidget(self.status, 1)
    srow.addWidget(self.progress)
    return status


def _menus(self, app_name):
    """A hidden menu bar (neither browser shows one in 2025): the actions' shortcuts still work."""
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
    self.bookmarks_menu = QMenu("Favorites", self)
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


def _profile_button():
    from ..user import picture_pixmap
    b = QToolButton()
    b.setObjectName("profile")
    pm = picture_pixmap()
    if pm is not None and not pm.isNull():
        round_pm = QPixmap(24, 24)
        round_pm.fill(Qt.transparent)
        p = QPainter(round_pm)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(QRectF(0, 0, 24, 24))
        p.setClipPath(path)
        p.drawPixmap(0, 0, pm.scaled(24, 24, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        p.end()
        b.setIcon(QIcon(round_pm))
    b.setIconSize(QSize(24, 24))
    b.setToolTip("Profile")
    return b


# ---- Microsoft Edge --------------------------------------------------------------------------------------------------
def _ie_base():
    from claudexp.programs.navigator import iexplore
    return iexplore


def make_edge():
    iexplore = _ie_base()

    class EdgeBrowser(iexplore.IEBrowser):
        APP = "Microsoft Edge"
        TITLE = "{} - Microsoft Edge"

        def _build_chrome(self):
            self.setStyleSheet(EDGE_STYLE)
            bar = _menus(self, "Microsoft Edge")
            tabs = QToolBar()
            tabs.setObjectName("tabs")
            tabs.setMovable(False)
            _tool(tabs, _glyph("☰", 13, "#5C5C5C"), "Tab actions menu", None, menu=self.go_menu)
            self.tab = QToolButton()
            self.tab.setObjectName("tab")
            self.tab.setText("New tab")
            self.tab.setIcon(iexplore.tool_icon("doc", 16))
            self.tab.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            tabs.addWidget(self.tab)
            newtab = QToolButton()
            newtab.setObjectName("newtab")
            newtab.setText("+")
            newtab.setToolTip("New tab (Ctrl+T)")
            newtab.clicked.connect(lambda _c=False: self.status.setText("Tabs: one at a time on this computer."))
            tabs.addWidget(newtab)
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            tabs.addWidget(spacer)
            _tool(tabs, _glyph("⌄", 14, "#5C5C5C"), "Minimize", None)
            nav = QToolBar()
            nav.setObjectName("nav")
            nav.setMovable(False)
            self.back_act = QAction(_arrow("back"), "Back", self)
            self.back_act.triggered.connect(self.back)
            self.fwd_act = QAction(_arrow("forward"), "Forward", self)
            self.fwd_act.triggered.connect(self.forward)
            refresh = QAction(_arrow("refresh"), "Refresh", self)
            refresh.triggered.connect(self.reload)
            self.stop_act = QAction(iexplore.tool_icon("stop", 16), "Stop", self)
            self.stop_act.triggered.connect(self.stop)
            home = QAction(_arrow("home"), "Home", self)
            home.triggered.connect(self.home)
            for act in (self.back_act, self.fwd_act, refresh, self.stop_act, home):
                nav.addAction(act)
                nav.widgetForAction(act).setIconSize(QSize(20, 20))
            self.loc_label = QLabel("")
            self.location = QLineEdit()
            self.location.setObjectName("address")
            self.location.setPlaceholderText("Search or enter web address")
            self.location.addAction(_arrow("lock", 16, "#5C5C5C"), QLineEdit.LeadingPosition)
            self.location.returnPressed.connect(self._go_typed)
            self.location.setMinimumWidth(260)
            self.location.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            star = QAction(_arrow("star", 16, "#5C5C5C"), "Add this page to favorites (Ctrl+D)", self)
            star.triggered.connect(self.add_bookmark)
            self.location.addAction(star, QLineEdit.TrailingPosition)
            nav.addWidget(self.location)
            self.throbber = QToolButton()
            self.throbber.setIcon(QIcon(spinner_frames()[0]))
            self.throbber.setIconSize(QSize(16, 16))
            self.throbber.setToolTip("Microsoft Edge")
            self.throbber.clicked.connect(lambda: self.navigate("http://www.microsoft.com/edge"))
            nav.addWidget(self.throbber)
            _tool(nav, _arrow("star"), "Favorites (Ctrl+Shift+O)", None, menu=self.bookmarks_menu)
            _tool(nav, _arrow("collections"), "Collections", lambda: self.status.setText("No collections yet."))
            _tool(nav, _arrow("puzzle"), "Extensions", lambda: self.status.setText("No extensions installed."))
            nav.addWidget(_profile_button())
            more = QMenu(self)
            more.setStyleSheet(MENU_CSS)
            more.addAction("New tab", lambda: self.status.setText("Tabs: one at a time on this computer."))
            more.addAction("New window", lambda: launch_edge(self.desktop))
            more.addSeparator()
            more.addMenu(self.bookmarks_menu)
            more.addMenu(self.go_menu)
            more.addAction("Downloads", lambda: self.status.setText("No downloads."))
            more.addAction("Collections", lambda: self.status.setText("No collections yet."))
            more.addAction("Extensions", lambda: self.status.setText("No extensions installed."))
            more.addSeparator()
            more.addAction("Zoom (100%)", lambda: None)
            more.addAction("Print...", self.print_page)
            more.addAction("Find on page", lambda: None)
            more.addAction("More tools", lambda: None)
            more.addAction("Developer tools (F12)", self.view_source)
            more.addSeparator()
            more.addAction("Settings", self._options)
            more.addAction("Help and feedback", self._about)
            more.addAction("Close Microsoft Edge", lambda: self.frame.request_close() if self.frame else self.close())
            _tool(nav, _arrow("dots"), "Settings and more (Alt+F)", None, menu=more)
            status = _status_bar(self)
            from claudexp.maintenance.toolbars import AdBars
            self.adbars = AdBars(self)
            return bar, [tabs, nav, self.adbars], status

        def throbber_frames(self):
            return spinner_frames()

        def app_icon(self):
            return edge_icon()

        def _set_title(self, title):
            super()._set_title(title)
            if hasattr(self, "tab"):
                self.tab.setText((title or "New tab")[:28])

        def _error_page(self, host, why):
            import html
            return f"""<html><head><title>Hmmm... can't reach this page</title></head>
<body style="font-family:'Segoe UI',Arial;background:#FFFFFF;color:#1A1A1A;padding:60px 80px">
<div style="font-size:26px;font-weight:600;margin-bottom:12px">Hmmm… can't reach this page</div>
<div style="font-size:14px;color:#5C5C5C"><b>{html.escape(host)}</b> took too long to respond. Try:
<ul><li>Checking the connection</li><li>Checking the proxy and the firewall</li><li>Running Windows Network Diagnostics</li></ul>
<span style="color:#8A8A8A">{html.escape(why)}</span></div></body></html>"""

    return EdgeBrowser


make_ie9 = make_edge


# ---- Mozilla Firefox 144 ---------------------------------------------------------------------------------------------
FF_HOME = "http://www.google.com/firefox"
FF_SEARCH = "http://www.google.com/search?q="
FF_BOOKMARKS = PROGRAM_FILES / "Mozilla Firefox" / "bookmarks.json"
FF_DEFAULT_BOOKMARKS = [{"title": "Getting Started", "url": "http://www.mozilla.org/firefox/central/"},
                        {"title": "Fur Affinity", "url": "http://www.furaffinity.net/"},
                        {"title": "Outlook.com", "url": "http://www.hotmail.com/"},
                        {"title": "Bluesky", "url": "http://bsky.app/"},
                        {"title": "LiveJournal", "url": "http://www.livejournal.com/"}]
FF_ABOUT = """<html><head><title>About Mozilla Firefox</title></head>
<body style="font-family:'Segoe UI',Arial;background:#FFFFFF;color:#15141A;padding:40px 60px">
<div style="font-size:26px;font-weight:600;color:#FF7139">Mozilla Firefox</div>
<div style="font-size:14px;margin-top:8px">Version 144.0 (64-bit)<br><br>Firefox is made by Mozilla, a global
community working together to keep the Web open, public and accessible to all.<br><br>&copy; 1998-2025
Contributors.</div></body></html>"""


def make_firefox():
    from claudexp.programs.navigator import browser as nb

    class FirefoxBrowser(nb.Browser):
        APP = "Mozilla Firefox"
        TITLE = "{} — Mozilla Firefox"
        HOME = FF_HOME
        SEARCH = FF_SEARCH
        DONE = ""
        ABOUT = FF_ABOUT
        BOOKMARKS = FF_BOOKMARKS
        DEFAULT_BOOKMARKS = FF_DEFAULT_BOOKMARKS

        def _build_chrome(self):
            self.setStyleSheet(FF_STYLE)
            bar = _menus(self, "Firefox")
            iexplore = _ie_base()
            tabs = QToolBar()
            tabs.setObjectName("tabs")
            tabs.setMovable(False)
            self.tab = QToolButton()
            self.tab.setObjectName("fftab")
            self.tab.setText("New Tab")
            self.tab.setIcon(iexplore.tool_icon("doc", 16))
            self.tab.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            tabs.addWidget(self.tab)
            newtab = QToolButton()
            newtab.setObjectName("ffnewtab")
            newtab.setText("+")
            newtab.setToolTip("Open a new tab (Ctrl+T)")
            newtab.clicked.connect(lambda _c=False: self.status.setText("Tabs: one at a time on this computer."))
            tabs.addWidget(newtab)
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            tabs.addWidget(spacer)
            _tool(tabs, _glyph("⌄", 14, "#5B5B66"), "List all tabs", None, menu=self.go_menu)
            nav = QToolBar()
            nav.setObjectName("nav")
            nav.setMovable(False)
            self.back_act = QAction(_arrow("back", 20, "#15141A"), "Back", self)
            self.back_act.triggered.connect(self.back)
            self.fwd_act = QAction(_arrow("forward", 20, "#15141A"), "Forward", self)
            self.fwd_act.triggered.connect(self.forward)
            refresh = QAction(_arrow("refresh", 20, "#15141A"), "Reload current page", self)
            refresh.triggered.connect(self.reload)
            self.stop_act = QAction(iexplore.tool_icon("stop", 16), "Stop", self)
            self.stop_act.triggered.connect(self.stop)
            home = QAction(_arrow("home", 20, "#15141A"), "Firefox Home", self)
            home.triggered.connect(self.home)
            for act in (self.back_act, self.fwd_act, refresh, self.stop_act, home):
                nav.addAction(act)
                nav.widgetForAction(act).setIconSize(QSize(20, 20))
            self.loc_label = QLabel("")
            self.location = QLineEdit()
            self.location.setObjectName("address")
            self.location.setPlaceholderText("Search with Google or enter address")
            self.location.addAction(_glyph("⚠", 13, "#5B5B66") if False else _arrow("lock", 16, "#5B5B66"),
                                    QLineEdit.LeadingPosition)
            self.location.returnPressed.connect(self._go_typed)
            self.location.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            star = QAction(_arrow("star", 16, "#5B5B66"), "Bookmark this page (Ctrl+D)", self)
            star.triggered.connect(self.add_bookmark)
            self.location.addAction(star, QLineEdit.TrailingPosition)
            nav.addWidget(self.location)
            self.throbber = QToolButton()
            self.throbber.setIcon(QIcon(spinner_frames(16, "#0060DF")[0]))
            self.throbber.setIconSize(QSize(16, 16))
            self.throbber.setToolTip("Mozilla Firefox")
            self.throbber.clicked.connect(self.home)
            nav.addWidget(self.throbber)
            _tool(nav, _arrow("puzzle", 20, "#15141A"), "Extensions", lambda: self.status.setText("No add-ons installed."))
            nav.addWidget(_profile_button())
            ffmenu = QMenu(self)
            ffmenu.setStyleSheet(MENU_CSS)
            ffmenu.addAction("New tab", lambda: self.status.setText("Tabs: one at a time on this computer."))
            ffmenu.addAction("New window", lambda: launch_firefox(self.desktop))
            ffmenu.addSeparator()
            ffmenu.addMenu(self.bookmarks_menu)
            ffmenu.addMenu(self.go_menu)
            ffmenu.addAction("Downloads", lambda: self.status.setText("No downloads."))
            ffmenu.addAction("Passwords", lambda: None)
            ffmenu.addAction("Extensions and themes", lambda: self.status.setText("No add-ons installed."))
            ffmenu.addSeparator()
            ffmenu.addAction("Print...", self.print_page)
            ffmenu.addAction("Find in page...", lambda: None)
            ffmenu.addAction("More tools", self.view_source)
            ffmenu.addSeparator()
            ffmenu.addAction("Settings", lambda: self._options())
            ffmenu.addAction("Help", self._about)
            ffmenu.addAction("Quit", lambda: self.frame.request_close() if self.frame else self.close())
            ham = QToolButton()
            ham.setObjectName("hamburger")
            ham.setText("☰")
            ham.setToolTip("Open application menu")
            ham.setMenu(ffmenu)
            ham.setPopupMode(QToolButton.InstantPopup)
            nav.addWidget(ham)
            status = _status_bar(self)
            return bar, [tabs, nav], status

        def throbber_frames(self):
            return spinner_frames(16, "#0060DF")

        def app_icon(self):
            return firefox_icon()

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
            return f"""<html><head><title>Hmm. We're having trouble finding that site.</title></head>
<body style="font-family:'Segoe UI',Arial;background:#FFFFFF;color:#15141A;padding:60px 80px">
<div style="font-size:26px;font-weight:600;margin-bottom:12px">Hmm. We're having trouble finding that site.</div>
<div style="font-size:14px;color:#5B5B66">We can't connect to the server at <b>{html.escape(host)}</b>.<ul>
<li>Check the address for typing errors such as <b>ww</b>.example.com instead of <b>www</b>.example.com</li>
<li>If you are unable to load any pages, check your computer's network connection.</li></ul>
<span style="color:#8A8A8A">{html.escape(why)}</span></div></body></html>"""

    return FirefoxBrowser


# ---- the programs ----------------------------------------------------------------------------------------------------
def _launch(desktop, key, make, name, icon, url=None, size=(1000, 680)):
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
    frame = MicaWindow(desktop, name, browser, icon, size=size)
    browser.frame = frame
    frame.destroyed.connect(lambda *_: _open.pop(key, None))
    _open[key] = frame
    if key == "edge":                                  # (XP code that looks for IE's window - the autopilot - finds it)
        ie = _ie_base()
        ie._frame = frame
        frame.destroyed.connect(lambda *_: setattr(ie, "_frame", None))
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


def launch_edge(desktop, url=None):
    _launch(desktop, "edge", make_edge, "Microsoft Edge", edge_icon(), url)


def shutdown_edge():
    _shutdown("edge")


launch_ie, shutdown_ie = launch_edge, shutdown_edge


def launch_firefox(desktop, url=None):
    _launch(desktop, "firefox", make_firefox, "Mozilla Firefox", firefox_icon(), url)


def shutdown_firefox():
    _shutdown("firefox")


def open_url(desktop, url=None):
    """A link from another program opens in the default browser (Settings > Apps > Default apps)."""
    try:
        from claudexp.programs.people import load_json
        from ..paths import DATA
        default = load_json(DATA / "cpl.json", {}).get("default_browser", "Microsoft Edge")
    except Exception:
        default = "Microsoft Edge"
    if default == "Mozilla Firefox":
        launch_firefox(desktop, url)
    else:
        launch_edge(desktop, url)


def install():
    """Internet Explorer is Microsoft Edge everywhere in the XP code, and links open in the default browser."""
    from claudexp.programs import navigator
    iexplore = _ie_base()
    iexplore.launch = launch_edge
    iexplore.shutdown = shutdown_edge
    try:
        iexplore.ie_icon = edge_icon
    except Exception:
        pass
    navigator.open_url = open_url
