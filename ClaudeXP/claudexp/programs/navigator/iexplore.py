"""Internet Explorer 6: the same model-written 2001 Web and Furry Web as Netscape Navigator, with IE's own
toolbars, Address bar, Favorites, the waving Windows flag, and MSN.com for a home page."""
import html
import math
import random
import traceback
from urllib.parse import unquote, urlparse

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import (QAction, QColor, QFont, QIcon, QKeySequence, QLinearGradient, QPainter, QPainterPath,
                           QPen, QPixmap, QPolygonF, QRadialGradient)
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QMenuBar, QProgressBar, QToolBar,
                               QToolButton, QWidget)
from shiboken6 import isValid

from ... import network, sound
from ...paths import ROOT
from ...wm import XPWindow
from . import web
from .browser import STYLE, Browser

FAVORITES_FILE = ROOT / "Program Files" / "Internet Explorer" / "favorites.json"
DEFAULT_FAVORITES = [
    {"title": "MSN.com", "url": web.MSN_URL},
    {"title": "Free Hotmail", "url": "http://www.hotmail.com/"},
    {"title": "Windows Media", "url": "http://www.windowsmedia.com/"},
    {"title": "Windows Update", "url": "http://windowsupdate.microsoft.com/"},
    {"title": "FurryCities", "url": "http://www.furrycities.com/"},
    {"title": "FurNet IRC Network", "url": "http://www.furnet.irc/"},
    {"title": "PawPrints MUCK", "url": "http://www.pawprintsmuck.com/"},
]
LINKS = [("Customize Links", "http://www.microsoft.com/isapi/redir.dll?prd=ie&ar=CLinks"),
         ("Free Hotmail", "http://www.hotmail.com/"), ("Windows", "http://www.microsoft.com/windows/"),
         ("Windows Media", "http://www.windowsmedia.com/"), ("Windows Update", "http://windowsupdate.microsoft.com/")]
ABOUT_PAGE = """<html><head><title>About Internet Explorer</title></head><body bgcolor="#FFFFFF">
<center><img src="about:logo" width="420" height="140"><br><br>
<font face="Tahoma" size="2">Version: 6.0.2600.0000<br>Cipher Strength: 128-bit<br>Product ID: 55274-640-0000000-23040<br>
Update Versions: ;SP1;<br><br>Every page on this Web is written for you, on the fly, as you browse.<br><br>
<font size="1">Copyright &copy;1995-2001 Microsoft Corp.</font></font></center></body></html>"""

IE_STYLE = STYLE + """
QToolBar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F6F5EE, stop:1 #E3E0D0);
           border: none; border-bottom: 1px solid #C4C0B0; spacing: 0px; padding: 1px 2px; }
QToolBar::separator { background: #C4C0B0; width: 1px; margin: 4px 3px; }
QToolButton { font-family: Tahoma; font-size: 11px; padding: 2px 3px; border: 1px solid transparent; border-radius: 3px; }
QToolButton:hover { border: 1px solid #C4C0B0; background: #FBFAF6; }
QToolButton:pressed { background: #E0DDD0; }
QToolButton:disabled { color: #A0A0A0; }
QLabel#addr { font-family: Tahoma; font-size: 11px; color: #555555; padding: 0 3px; }
QWidget#statusbar { background: #ECE9D8; border-top: 1px solid #ACA899; }
QFrame#panel { border: 1px solid; border-color: #ACA899 #FFFFFF #FFFFFF #ACA899; }
"""


# ---- artwork --------------------------------------------------------------------------------------------------------

def ie_logo(size=32):
    """The blue 'e' with its gold orbit."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    p.translate(size / 2, size / 2)
    # the back half of the orbit, behind the e
    p.save()
    p.rotate(-28)
    ring = QPen(QColor("#E8A317"), max(1.2, 2.6 * s))
    p.setPen(ring)
    p.drawArc(QRectF(-15.5 * s, -7 * s, 31 * s, 14 * s), 0, 180 * 16)
    p.restore()
    font = QFont("Times New Roman", 1)
    font.setPixelSize(int(30 * s))
    font.setBold(True)
    path = QPainterPath()
    path.addText(0, 0, font, "e")
    r = path.boundingRect()
    path.translate(-r.center().x(), -r.center().y())
    g = QLinearGradient(0, -12 * s, 0, 12 * s)
    g.setColorAt(0, QColor("#7FC4FF"))
    g.setColorAt(0.5, QColor("#1E78D8"))
    g.setColorAt(1, QColor("#0B3E9A"))
    p.setPen(QPen(QColor("#0A2F78"), max(0.6, 0.8 * s)))
    p.setBrush(g)
    p.drawPath(path)
    # the front half of the orbit, across the e
    p.rotate(-28)
    p.setPen(ring)
    p.drawArc(QRectF(-15.5 * s, -7 * s, 31 * s, 14 * s), 180 * 16, 180 * 16)
    p.end()
    return pm


def ie_icon():
    icon = QIcon()
    for size in (16, 24, 32, 48):
        icon.addPixmap(ie_logo(size))
    return icon


FLAG_W, FLAG_H = 38, 26
_flag_frames = None


def _flag(phase=None):
    """The Windows flag in IE's corner box; phase (0..1) makes it wave while a page loads."""
    pm = QPixmap(FLAG_W, FLAG_H)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    bg = QLinearGradient(0, 0, 0, FLAG_H)
    bg.setColorAt(0, QColor("#FFFFFF"))
    bg.setColorAt(1, QColor("#E4E2D6"))
    p.setPen(QPen(QColor("#C4C0B0")))
    p.setBrush(bg)
    p.drawRect(QRectF(0.5, 0.5, FLAG_W - 1, FLAG_H - 1))
    colors = (("#F65314", "#7CBB00"), ("#00A1F1", "#FFBB00"))
    x0, y0, cw, ch, gap = 9.0, 4.0, 9.0, 8.0, 1.2

    def wave(x):
        if phase is None:
            return -(x - x0) * 0.12
        return math.sin((x - x0) / 7 + phase * 2 * math.pi) * 1.6 - (x - x0) * 0.12

    for row in range(2):
        for col in range(2):
            left = x0 + col * (cw + gap)
            top = y0 + row * (ch + gap)
            pts = []
            for i in range(7):
                x = left + cw * i / 6
                pts.append(QPointF(x, top + wave(x)))
            for i in range(6, -1, -1):
                x = left + cw * i / 6
                pts.append(QPointF(x, top + ch + wave(x)))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(colors[row][col]))
            p.drawPolygon(QPolygonF(pts))
    p.end()
    return pm


def flag_frames():
    global _flag_frames
    if _flag_frames is None:
        _flag_frames = [_flag()] + [_flag(i / 12) for i in range(12)]
    return _flag_frames


def _circle_arrow(p, s, right):
    g = QRadialGradient(QPointF(10 * s, 8 * s), 13 * s)
    g.setColorAt(0, QColor("#9BE07E"))
    g.setColorAt(1, QColor("#1F8A1F"))
    p.setPen(QPen(QColor("#176B17"), s))
    p.setBrush(g)
    p.drawEllipse(QRectF(1.5 * s, 1.5 * s, 21 * s, 21 * s))
    pts = [(6, 12), (12, 6), (12, 9.5), (18, 9.5), (18, 14.5), (12, 14.5), (12, 18)]
    if right:
        pts = [(24 - x, y) for x, y in pts]
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("white"))
    p.drawPolygon(QPolygonF([QPointF(x * s, y * s) for x, y in pts]))


def _page(p, s, rect=(4, 2, 14, 19)):
    x, y, w, h = rect
    p.setPen(QPen(QColor("#7A8794"), s))
    p.setBrush(QColor("white"))
    p.drawRect(QRectF(x * s + 0.5, y * s + 0.5, w * s, h * s))
    p.setPen(QPen(QColor("#B8C4D0"), s))
    for i in range(4):
        yy = (y + 4 + i * 3) * s
        p.drawLine(QPointF((x + 3) * s, yy), QPointF((x + w - 3) * s, yy))


def tool_icon(kind, size=24):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 24
    if kind in ("back", "forward"):
        _circle_arrow(p, s, kind == "forward")
    elif kind == "stop":
        _page(p, s)
        p.setPen(QPen(QColor("#9A1A0A"), s))
        p.setBrush(QColor("#E0401E"))
        p.drawRoundedRect(QRectF(9 * s, 9 * s, 13 * s, 13 * s), 2 * s, 2 * s)
        p.setPen(QPen(QColor("white"), 2.2 * s))
        p.drawLine(QPointF(12 * s, 12 * s), QPointF(19 * s, 19 * s))
        p.drawLine(QPointF(19 * s, 12 * s), QPointF(12 * s, 19 * s))
    elif kind == "refresh":
        _page(p, s)
        pen = QPen(QColor("#1F8A1F"), 2.4 * s)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        r = QRectF(9 * s, 9 * s, 12 * s, 12 * s)
        p.drawArc(r, 20 * 16, 150 * 16)
        p.drawArc(r, 200 * 16, 150 * 16)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1F8A1F"))
        p.drawPolygon(QPolygonF([QPointF(20 * s, 8 * s), QPointF(23 * s, 14 * s), QPointF(17 * s, 13 * s)]))
        p.drawPolygon(QPolygonF([QPointF(10 * s, 22 * s), QPointF(7 * s, 16 * s), QPointF(13 * s, 17 * s)]))
    elif kind == "home":
        p.setPen(QPen(QColor("#6B4A2A"), s))
        p.setBrush(QColor("#FFF6E0"))
        p.drawRect(QRectF(5.5 * s, 11.5 * s, 13 * s, 10 * s))
        p.setBrush(QColor("#C0392B"))
        p.drawPolygon(QPolygonF([QPointF(2 * s, 12.5 * s), QPointF(12 * s, 3 * s), QPointF(22 * s, 12.5 * s)]))
        p.setBrush(QColor("#2D6FC0"))
        p.drawRect(QRectF(10.5 * s, 15.5 * s, 4 * s, 6 * s))
    elif kind == "search":
        p.setPen(QPen(QColor("#5A3A1A"), 3 * s))
        p.drawLine(QPointF(15 * s, 15 * s), QPointF(21.5 * s, 21.5 * s))
        g = QRadialGradient(QPointF(8 * s, 8 * s), 9 * s)
        g.setColorAt(0, QColor("#FFFFFF"))
        g.setColorAt(1, QColor("#8EC8F0"))
        p.setPen(QPen(QColor("#3A5A80"), 1.6 * s))
        p.setBrush(g)
        p.drawEllipse(QRectF(2.5 * s, 2.5 * s, 13 * s, 13 * s))
    elif kind == "favorites":
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = (10.5 if i % 2 == 0 else 4.6) * s
            pts.append(QPointF(12 * s + r * math.cos(a), 12.8 * s + r * math.sin(a)))
        g = QLinearGradient(0, 2 * s, 0, 22 * s)
        g.setColorAt(0, QColor("#FFF07A"))
        g.setColorAt(1, QColor("#E8A317"))
        p.setPen(QPen(QColor("#A06A00"), s))
        p.setBrush(g)
        p.drawPolygon(QPolygonF(pts))
    elif kind == "media":
        g = QRadialGradient(QPointF(9 * s, 8 * s), 13 * s)
        g.setColorAt(0, QColor("#FFD27A"))
        g.setColorAt(1, QColor("#E06A00"))
        p.setPen(QPen(QColor("#9A4A00"), s))
        p.setBrush(g)
        p.drawEllipse(QRectF(1.5 * s, 1.5 * s, 21 * s, 21 * s))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("white"))
        p.drawPolygon(QPolygonF([QPointF(9 * s, 6.5 * s), QPointF(18 * s, 12 * s), QPointF(9 * s, 17.5 * s)]))
    elif kind == "history":
        p.setPen(QPen(QColor("#3A5A80"), 1.4 * s))
        p.setBrush(QColor("white"))
        p.drawEllipse(QRectF(4 * s, 3 * s, 18 * s, 18 * s))
        p.setPen(QPen(QColor("#203040"), 1.6 * s))
        p.drawLine(QPointF(13 * s, 12 * s), QPointF(13 * s, 6.5 * s))
        p.drawLine(QPointF(13 * s, 12 * s), QPointF(17 * s, 14 * s))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1F8A1F"))
        p.drawPolygon(QPolygonF([QPointF(1 * s, 14 * s), QPointF(5 * s, 22 * s), QPointF(9 * s, 14 * s)]))
    elif kind == "mail":
        p.setPen(QPen(QColor("#6A7A8A"), s))
        p.setBrush(QColor("#FFFDF2"))
        p.drawRect(QRectF(2.5 * s, 6.5 * s, 19 * s, 13 * s))
        p.drawPolyline(QPolygonF([QPointF(2.5 * s, 6.5 * s), QPointF(12 * s, 14 * s), QPointF(21.5 * s, 6.5 * s)]))
    elif kind == "print":
        p.setPen(QPen(QColor("#5A6470"), s))
        p.setBrush(QColor("white"))
        p.drawRect(QRectF(6.5 * s, 2.5 * s, 11 * s, 8 * s))
        g = QLinearGradient(0, 9 * s, 0, 19 * s)
        g.setColorAt(0, QColor("#E6E6E6"))
        g.setColorAt(1, QColor("#9AA0A8"))
        p.setBrush(g)
        p.drawRoundedRect(QRectF(2.5 * s, 9.5 * s, 19 * s, 9 * s), 2 * s, 2 * s)
        p.setBrush(QColor("white"))
        p.drawRect(QRectF(6.5 * s, 15.5 * s, 11 * s, 6 * s))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#3CB043"))
        p.drawEllipse(QRectF(17 * s, 11.5 * s, 2.4 * s, 2.4 * s))
    elif kind == "go":
        g = QLinearGradient(0, 0, 0, size)
        g.setColorAt(0, QColor("#7ED36A"))
        g.setColorAt(1, QColor("#2A8A1E"))
        p.setPen(QPen(QColor("#1F6A17"), s))
        p.setBrush(g)
        p.drawRoundedRect(QRectF(1.5 * s, 1.5 * s, 21 * s, 21 * s), 4 * s, 4 * s)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("white"))
        p.drawPolygon(QPolygonF([QPointF(x * s, y * s) for x, y in
                                 ((6, 10), (12, 10), (12, 6), (19, 12), (12, 18), (12, 14), (6, 14))]))
    elif kind == "globe":
        g = QRadialGradient(QPointF(9 * s, 9 * s), 12 * s)
        g.setColorAt(0, QColor("#BFE6FF"))
        g.setColorAt(1, QColor("#2A7FD0"))
        p.setPen(QPen(QColor("#1A4F8A"), s))
        p.setBrush(g)
        p.drawEllipse(QRectF(2 * s, 2 * s, 20 * s, 20 * s))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#4CAF50"))
        p.drawEllipse(QRectF(6 * s, 6 * s, 7 * s, 6 * s))
        p.drawEllipse(QRectF(12 * s, 13 * s, 6 * s, 5 * s))
    elif kind == "doc":
        _page(p, s, (5, 3, 13, 17))
        p.drawPixmap(int(10 * s), int(11 * s), ie_logo(max(8, int(12 * s))))
    p.end()
    return QIcon(pm)


def _about_banner():
    pm = QPixmap(420, 140)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, 420, 140)
    g.setColorAt(0, QColor("#0A246A"))
    g.setColorAt(1, QColor("#3A6EA5"))
    p.fillRect(pm.rect(), g)
    p.drawPixmap(24, 22, ie_logo(96))
    p.setPen(QColor("white"))
    f = QFont("Tahoma", 11)
    p.setFont(f)
    p.drawText(QRectF(136, 34, 280, 20), Qt.AlignLeft, "Microsoft®")
    f = QFont("Tahoma", 22)
    f.setBold(True)
    p.setFont(f)
    p.drawText(QRectF(136, 52, 280, 40), Qt.AlignLeft, "Internet Explorer")
    f = QFont("Tahoma", 30)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#FFCC33"))
    p.drawText(QRectF(136, 84, 280, 50), Qt.AlignLeft, "6")
    p.end()
    return pm


# ---- the browser ------------------------------------------------------------------------------------------------------

class IEBrowser(Browser):
    APP = "Microsoft Internet Explorer"
    TITLE = "{} - Microsoft Internet Explorer"

    @property
    def HOME(self):                       # Control Panel > Internet Options > Home page (unless a toolbar hijacked it)
        from ...cpl_extra import ie_home
        from ...maintenance import toolbars
        return toolbars.home_hijack() or ie_home()

    @property
    def SEARCH(self):                     # MSN Search, or wherever a hijacking toolbar sends your searches
        from ...maintenance import toolbars
        return toolbars.search_hijack() or web.MSN_SEARCH_URL

    def navigate(self, url, *args, **kwargs):
        super().navigate(url, *args, **kwargs)
        if network.is_connected():        # browsing is how the toolbars get in (a 'free' download, a pop-up...)
            from ...maintenance import toolbars
            QTimer.singleShot(random.randint(3000, 9000), toolbars.maybe_install)
    DONE = "Done"
    ABOUT = ABOUT_PAGE
    BOOKMARKS = FAVORITES_FILE
    DEFAULT_BOOKMARKS = DEFAULT_FAVORITES

    def _build_chrome(self):
        self.setStyleSheet(IE_STYLE)

        # ---- menus ----
        bar = QMenuBar()
        file_menu = bar.addMenu("&File")
        file_menu.addAction("&Open...", self._focus_location, QKeySequence("Ctrl+O"))
        file_menu.addSeparator()
        file_menu.addAction("&Print...", self.print_page, QKeySequence("Ctrl+P"))
        file_menu.addSeparator()
        file_menu.addAction("&Work Offline", lambda: self.status.setText("You are working online."))
        file_menu.addAction("&Close", lambda: self.frame.request_close() if self.frame else self.close())
        edit_menu = bar.addMenu("&Edit")
        edit_menu.addAction("&Copy", lambda: self._page_action("Copy", self.view.copy), QKeySequence("Ctrl+C"))
        edit_menu.addAction("Select &All", lambda: self._page_action("SelectAll", self.view.selectAll),
                            QKeySequence("Ctrl+A"))
        view_menu = bar.addMenu("&View")
        go_to = view_menu.addMenu("&Go To")
        go_to.addAction("&Back", self.back, QKeySequence("Alt+Left"))
        go_to.addAction("&Forward", self.forward, QKeySequence("Alt+Right"))
        go_to.addSeparator()
        go_to.addAction("&Home Page", self.home, QKeySequence("Alt+Home"))
        view_menu.addAction("&Stop", self.stop, QKeySequence("Esc"))
        view_menu.addAction("&Refresh", self.reload, QKeySequence("F5"))
        view_menu.addAction("Re&write Page", lambda: self.reload(regenerate=True))
        view_menu.addSeparator()
        view_menu.addAction("Sour&ce", self.view_source)
        self.bookmarks_menu = bar.addMenu("F&avorites")
        self.bookmarks_menu.aboutToShow.connect(self._fill_bookmarks)
        tools = bar.addMenu("&Tools")
        mail = tools.addMenu("&Mail and News")
        mail.addAction("&Read Mail", self._open_mail)
        mail.addAction("&New Message...", lambda: self._mailto("mailto:"))
        tools.addAction("Windows &Update", lambda: self._launch("winupdate"))
        tools.addSeparator()
        tools.addAction("Windows &Messenger", lambda: self._launch("msn"))
        tools.addSeparator()
        tools.addAction("Internet &Options...", self._options)
        help_menu = bar.addMenu("&Help")
        help_menu.addAction("&Tip of the Day", lambda: self.status.setText(
            "Tip: type a few words in the Address bar and press Enter to search MSN."))
        help_menu.addSeparator()
        help_menu.addAction("&About Internet Explorer", self._about)
        bar.triggered.connect(lambda _a: sound.play("menu"))
        self.throbber = QToolButton()
        self.throbber.setAutoRaise(True)
        self.throbber.setStyleSheet("QToolButton { border: none; padding: 0; margin: 0; }")
        self.throbber.setIcon(QIcon(flag_frames()[0]))
        self.throbber.setIconSize(flag_frames()[0].size())
        self.throbber.setToolTip("Microsoft Internet Explorer")
        self.throbber.clicked.connect(lambda: self.navigate("http://www.microsoft.com/windows/ie/"))
        bar.setCornerWidget(self.throbber, Qt.TopRightCorner)
        self.go_menu = QMenu(self)                # History
        self.go_menu.aboutToShow.connect(self._fill_go_menu)

        # ---- Standard Buttons ----
        nav = QToolBar()
        nav.setIconSize(QSize(24, 24))

        def button(text, kind, slot, label=True, menu=None):
            act = QAction(tool_icon(kind), text, self)
            act.setToolTip(text)
            act.triggered.connect(slot)
            nav.addAction(act)
            w = nav.widgetForAction(act)
            w.setToolButtonStyle(Qt.ToolButtonTextBesideIcon if label else Qt.ToolButtonIconOnly)
            if menu is not None:
                act.setMenu(menu)
                w.setPopupMode(QToolButton.InstantPopup)
            return act

        self.back_act = button("Back", "back", self.back)
        self.fwd_act = button("Forward", "forward", self.forward, label=False)
        self.stop_act = button("Stop", "stop", self.stop, label=False)
        button("Refresh", "refresh", self.reload, label=False)
        button("Home", "home", self.home, label=False)
        nav.addSeparator()
        button("Search", "search", self._search)
        button("Favorites", "favorites", lambda: None, menu=self.bookmarks_menu)
        button("Media", "media", lambda: self._launch("wmp"))
        button("History", "history", lambda: None, label=False, menu=self.go_menu)
        nav.addSeparator()
        mail_menu = QMenu(self)
        mail_menu.addAction("Read Mail", self._open_mail)
        mail_menu.addAction("New Message...", lambda: self._mailto("mailto:"))
        mail_menu.addAction("Send a Link...", self._send_link)
        button("Mail", "mail", lambda: None, label=False, menu=mail_menu)
        button("Print", "print", self.print_page, label=False)

        # ---- Address bar + Links ----
        loc = QToolBar()
        self.loc_label = QLabel("Address")
        self.loc_label.setObjectName("addr")
        loc.addWidget(self.loc_label)
        self.location = QLineEdit()
        self.location.setStyleSheet("QLineEdit { background: white; border: 1px solid #7F9DB9; padding: 1px 2px; "
                                    "font-family: Tahoma; font-size: 11px; }")
        self.location.addAction(tool_icon("doc", 16), QLineEdit.LeadingPosition)
        self.location.returnPressed.connect(self._go_typed)
        loc.addWidget(self.location)
        go = QAction(tool_icon("go", 18), "Go", self)
        go.setToolTip("Go to the address in the Address bar")
        go.triggered.connect(self._go_typed)
        loc.addAction(go)
        loc.widgetForAction(go).setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        loc.addSeparator()
        links = QToolButton()
        links.setText("Links  »")
        links.setStyleSheet("color: #555555;")
        links.setPopupMode(QToolButton.InstantPopup)
        links_menu = QMenu(links)
        for title, url in LINKS:
            links_menu.addAction(tool_icon("doc", 16), title, lambda u=url: self.navigate(u))
        links.setMenu(links_menu)
        loc.addWidget(links)

        # ---- status bar ----
        status = QWidget()
        status.setObjectName("statusbar")
        status.setAttribute(Qt.WA_StyledBackground, True)
        srow = QHBoxLayout(status)
        srow.setContentsMargins(2, 2, 14, 2)
        srow.setSpacing(2)

        def panel(*widgets, stretch=0, width=None):
            f = QFrame()
            f.setObjectName("panel")
            row = QHBoxLayout(f)
            row.setContentsMargins(3, 0, 3, 0)
            row.setSpacing(4)
            for w in widgets:
                row.addWidget(w, 1 if w is widgets[-1] else 0)
            if width:
                f.setFixedWidth(width)
            srow.addWidget(f, stretch)
            return f

        page_icon = QLabel()
        page_icon.setPixmap(tool_icon("doc", 16).pixmap(16, 16))
        self.status = QLabel(self.DONE)
        self.status.setObjectName("status")
        panel(page_icon, self.status, stretch=1)
        self.progress = QProgressBar()
        self.progress.setFixedHeight(11)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setStyleSheet("QProgressBar { border: none; background: transparent; } "
                                    "QProgressBar::chunk { background: #2F6FD6; width: 6px; margin: 1px; }")
        panel(self.progress, width=130)
        self.lock = QLabel()                       # the padlock panel: empty unless the page is secure
        panel(self.lock, width=26)
        globe = QLabel()
        globe.setPixmap(tool_icon("globe", 16).pixmap(16, 16))
        zone = QLabel("Internet")
        zone.setObjectName("status")
        panel(globe, zone, width=150)
        from ...maintenance.toolbars import AdBars
        self.adbars = AdBars(self)                 # toolbars that installed themselves (Ad-aware removes them)
        return bar, [nav, loc, self.adbars], status

    # ---- IE's own bits ----------------------------------------------------------------------------------------------
    def throbber_frames(self):
        return flag_frames()

    def app_icon(self):
        return ie_icon()

    def about_logo(self):
        return _about_banner()

    def _launch(self, key):
        from .. import launch
        launch(self.desktop, key)

    def _open_mail(self):
        from ..outlook import open_outlook
        return open_outlook(self.desktop)

    def _mailto(self, url):
        """IE hands mailto: links to Outlook Express."""
        to = unquote(urlparse(url).path) if url.startswith("mailto:") else ""
        win = self._open_mail()
        if win is not None and isValid(win):
            win.content.compose(to=to)

    def _send_link(self):
        win = self._open_mail()
        if win is not None and isValid(win) and self.url:
            title = self._current_title()
            win.content.compose(subject=title, body=f"{title}\n{self.url}\n")

    def _current_title(self):
        on_site = self.site_view is not None and self.pages.currentWidget() is self.site_view
        return (self.site_view.title() if on_site else web.title_of(self.page)) or self.url

    def _options(self):
        from ...cpl_extra import internet_options
        internet_options(self.desktop)

    def _fill_bookmarks(self):
        m = self.bookmarks_menu
        m.clear()
        m.addAction("&Add to Favorites...", self.add_bookmark, QKeySequence("Ctrl+D"))
        m.addAction("&Organize Favorites...", lambda: self.status.setText("Your Favorites are listed below."))
        m.addSeparator()
        links = m.addMenu(QIcon(), "Links")
        for title, url in LINKS:
            links.addAction(tool_icon("doc", 16), title, lambda u=url: self.navigate(u))
        for bm in self.bookmarks:
            m.addAction(tool_icon("doc", 16), bm["title"], lambda u=bm["url"]: self.navigate(u))

    def add_bookmark(self):
        super().add_bookmark()
        if self.status.text() == "Bookmark added.":
            self.status.setText("Added to Favorites.")

    def _fill_go_menu(self):
        m = self.go_menu
        m.clear()
        seen = []
        for url in reversed(self.history):
            if url not in seen:
                seen.append(url)
        if not seen:
            m.addAction("(No history yet)").setEnabled(False)
        for url in seen[:15]:
            m.addAction(tool_icon("doc", 16), urlparse(url).netloc or url, lambda u=url: self.navigate(u))

    def _error_page(self, host, why):
        return f"""<html><head><title>Cannot find server</title></head><body bgcolor="#FFFFFF">
<table width="400" cellpadding="3"><tr><td valign="top"><font face="Tahoma" size="4" color="#4E6C9A">
<b>The page cannot be displayed</b></font></td></tr></table>
<font face="Tahoma" size="2">The page you are looking for is currently unavailable. The Web site might be
experiencing technical difficulties, or you may need to adjust your browser settings.<br>
<font color="#808080">({html.escape(host)}: {html.escape(why)})</font></font>
<hr size="1" color="#C0C0C0">
<font face="Tahoma" size="2">Please try the following:<ul>
<li>Click the <b>Refresh</b> button, or try again later.</li>
<li>If you typed the page address in the Address bar, make sure that it is spelled correctly.</li>
<li>To check your connection settings, click the <b>Tools</b> menu, and then click <b>Internet Options</b>.</li>
<li>Click the <b>Back</b> button to try another link.</li></ul>
Cannot find server or DNS Error<br>Internet Explorer</font></body></html>"""


# ---- the program ------------------------------------------------------------------------------------------------------

_frame = None
_listening = False


def launch(desktop, url=None):
    global _frame, _listening
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        if url:
            _frame.content.navigate(url)
        return
    try:
        browser = IEBrowser(desktop)
    except Exception:
        from ..placeholder import open_placeholder
        open_placeholder(desktop, "Internet Explorer", ie_icon(),
                         "Internet Explorer couldn't start.\n\n" + traceback.format_exc(limit=3), sound_event="error")
        return
    if not _listening:
        network.on_disconnect(desktop, _network_lost)
        _listening = True
    _frame = XPWindow(desktop, IEBrowser.APP, browser, ie_icon(), size=(860, 640))
    browser.frame = _frame
    _frame.destroyed.connect(_forget)
    desktop.open_window(_frame)
    browser.start(url)


def _forget(*_):
    global _frame
    _frame = None


def _network_lost(quiet):
    if _frame is not None and isValid(_frame):
        _frame.content.network_lost()


def shutdown():
    if _frame is not None and isValid(_frame):
        _frame.content.shutdown()
        _frame.desktop.close_window(_frame)
