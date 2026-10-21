"""Internet Explorer toolbars that nobody asked for (2001's favourite plague).

Every few days, while you're browsing online, one of them slips in with a 'free' download nobody remembers
agreeing to: it shows up under IE's Address bar, sends its search box (and sometimes your searches or home page)
to its own sites, and can't be closed. Never more than three at once. Ad-aware finds their files and registry
entries; once all of a toolbar's objects are removed, it's gone. Remembered in data/toolbars.json."""
import random
from datetime import datetime

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QToolButton, QWidget
from shiboken6 import isValid

from ..paths import DATA
from ..programs.people import load_json, save_json

STATE_FILE = DATA / "toolbars.json"
MOST = 3                                    # never more than this many at once
EVERY_DAYS = (2.0, 5.0)                     # how long until the next one sneaks in
BHO = r"HKEY_LOCAL_MACHINE:Software\Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects"
IE_TOOLBAR = r"HKEY_LOCAL_MACHINE:Software\Microsoft\Internet Explorer\Toolbar"

# key -> what it is, what it looks like, where it sends you, and what Ad-aware finds
TOOLBARS = {
    "searchsurf": {
        "name": "SearchSurf Toolbar", "vendor": "SearchSurf", "category": "Hijacker",
        "comment": "Toolbar that sends your Address bar searches to its own engine",
        "colours": ("#1E4C9E", "#5B8BDD"), "text": "white", "badge": ("S", "#FFB000"),
        "search": "http://www.searchsurf.com/search.php?q=", "hijack_search": True,
        "buttons": [("Top 100", "http://www.searchsurf.com/top100.html"),
                    ("Free Games", "http://games.searchsurf.com/"),
                    ("Horoscopes", "http://www.searchsurf.com/horoscopes/")],
        "guid": "{8E1A7C2D-3B4F-4D51-9A61-55D0C3E9B214}",
        "objects": [("Process", r"C:\Program Files\SearchSurf\ssupdate.exe"),
                    ("File", r"C:\WINDOWS\System32\ssbar.dll"),
                    ("Folder", r"C:\Program Files\SearchSurf")]},
    "megasmiley": {
        "name": "MegaSmiley Bar", "vendor": "MegaSmiley", "category": "Adware",
        "comment": "'FREE smileys for your e-mail!' - and ads in every message",
        "colours": ("#F7D23A", "#F09A1A"), "text": "#5A2A00", "badge": ("☺", "#FFFFFF"),
        "search": None,
        "buttons": [("FREE Smileys!", "http://www.megasmiley.com/smileys/"),
                    ("Animated Cursors", "http://www.megasmiley.com/cursors/"),
                    ("Screensavers", "http://www.megasmiley.com/screensavers/"),
                    ("E-Cards", "http://www.megasmiley.com/ecards/")],
        "guid": "{2C61B4E0-7F2A-11D5-A9C4-0050DA2A9F31}",
        "objects": [("File", r"C:\WINDOWS\System32\msmbar.dll"),
                    ("File", r"C:\Program Files\MegaSmiley\SmileyCentral.exe"),
                    ("RegValue", r"HKEY_LOCAL_MACHINE:Software\Microsoft\Windows\CurrentVersion\Run [MSmiley]"),
                    ("Folder", r"C:\Program Files\MegaSmiley")]},
    "bargainbuddy": {
        "name": "BargainBuddy Bar", "vendor": "BargainBuddy", "category": "Adware",
        "comment": "Shopping toolbar that pops up 'deals' on the sites you visit",
        "colours": ("#167A3E", "#3DB36B"), "text": "white", "badge": ("$", "#FFE14D"),
        "search": "http://www.bargainbuddy.com/compare.asp?item=",
        "buttons": [("Today's Deals", "http://www.bargainbuddy.com/deals/"),
                    ("Coupons", "http://www.bargainbuddy.com/coupons/"),
                    ("Free Shipping!", "http://www.bargainbuddy.com/freeshipping/")],
        "guid": "{5A0F9A13-6E6B-4F0E-8C2A-1B9D7E4C0A66}",
        "objects": [("Process", r"C:\Program Files\BargainBuddy\bbuddy.exe"),
                    ("File", r"C:\WINDOWS\System32\bbhelper.dll"),
                    ("Folder", r"C:\Program Files\BargainBuddy")]},
    "skycast": {
        "name": "SkyCast Weather Bar", "vendor": "SkyCast", "category": "Datamining",
        "comment": "Weather in your toolbar; reports your ZIP code and the pages you visit",
        "colours": ("#3E8BD8", "#9CCBF5"), "text": "#0B2D55", "badge": ("☀", "#FFD23A"),
        "search": None, "weather": True,
        "buttons": [("5-Day Forecast", "http://www.skycastweather.com/forecast/"),
                    ("Doppler Radar", "http://www.skycastweather.com/radar/"),
                    ("Weather Alerts", "http://www.skycastweather.com/alerts/")],
        "guid": "{B4D6E8F0-1A2C-4E6A-8B0D-2F4A6C8E0B13}",
        "objects": [("Process", r"C:\Program Files\SkyCast\skycast.exe"),
                    ("File", r"C:\WINDOWS\System32\skyband.dll"),
                    ("RegKey", r"HKEY_LOCAL_MACHINE:Software\SkyCast"),
                    ("Folder", r"C:\Program Files\SkyCast")]},
    "winprize": {
        "name": "WinPrize Toolbar", "vendor": "WinPrize", "category": "Adware",
        "comment": "Flashing 'You're a WINNER!' ads; signs you up for sweepstakes mailings",
        "colours": ("#8E1BA8", "#D24BE8"), "text": "white", "badge": ("★", "#FFE14D"),
        "search": None, "flashing": "★ CONGRATULATIONS! You're today's 1,000,000th visitor - CLAIM YOUR PRIZE! ★",
        "buttons": [("Claim Prize", "http://www.winprize-sweeps.com/claim.asp?id=1000000"),
                    ("Free iPod... er, MP3 player", "http://www.winprize-sweeps.com/mp3/"),
                    ("Sweepstakes", "http://www.winprize-sweeps.com/")],
        "guid": "{E7A2C9B1-4D3F-11D5-B2E8-00A0C9F1D2A7}",
        "objects": [("File", r"C:\WINDOWS\System32\wpbar.dll"),
                    ("RegKey", r"HKEY_LOCAL_MACHINE:Software\WinPrize"),
                    ("Folder", r"C:\Program Files\WinPrize")]},
    "pawsearch": {
        "name": "PawSearch Furry Bar", "vendor": "PawSearch", "category": "Hijacker",
        "comment": "Furry search toolbar that changes your Internet Explorer home page",
        "colours": ("#7A4A22", "#C98B4E"), "text": "white", "badge": ("🐾", "#FFFFFF"),
        "search": "http://www.pawsearch.net/find.cgi?q=", "home": "http://www.pawsearch.net/",
        "buttons": [("Furry Art", "http://www.pawsearch.net/art/"),
                    ("Conventions", "http://www.pawsearch.net/cons/"),
                    ("Fursuits", "http://www.pawsearch.net/fursuits/"),
                    ("Top Furry Sites", "http://www.pawsearch.net/top50/")],
        "guid": "{9F3B1E57-2C8D-4A66-B1F0-77E2D5A3C981}",
        "objects": [("File", r"C:\WINDOWS\System32\pawbar.dll"),
                    ("RegValue", r"HKEY_CURRENT_USER:Software\Microsoft\Internet Explorer\Main [Start Page]"),
                    ("Folder", r"C:\Program Files\PawSearch")]},
    "xplorerplus": {
        "name": "XplorerPlus Navigation Bar", "vendor": "XplorerPlus", "category": "Hijacker",
        "comment": "Navigation 'helper' that redirects mistyped addresses and your home page",
        "colours": ("#2A2A2A", "#5C5C5C"), "text": "#7CFF6B", "badge": ("X", "#7CFF6B"),
        "search": "http://www.xplorerplus.com/nav.php?go=", "home": "http://www.xplorerplus.com/start/",
        "buttons": [("Kewl Links", "http://www.xplorerplus.com/kewl/"),
                    ("Popular Sites", "http://www.xplorerplus.com/popular/"),
                    ("Free MP3s", "http://www.xplorerplus.com/mp3/")],
        "guid": "{0D4C7A88-61E3-4B2B-9E50-C3A1F7B60E42}",
        "objects": [("Process", r"C:\WINDOWS\System32\xpnav32.exe"),
                    ("File", r"C:\WINDOWS\System32\xpnav.dll"),
                    ("RegValue", r"HKEY_LOCAL_MACHINE:Software\Microsoft\Windows\CurrentVersion\Run [xpnav]")]},
}
for _tb in TOOLBARS.values():               # every toolbar is a Browser Helper Object and an IE toolbar band
    _tb["objects"] = [("RegKey", rf"{BHO}\{_tb['guid']}"), ("RegValue", rf"{IE_TOOLBAR} [{_tb['guid']}]")] \
        + _tb["objects"]

_state = None
_listeners = []


def _load():
    global _state
    if _state is None:
        _state = load_json(STATE_FILE, {})
        _state.setdefault("installed", {})       # key -> when it arrived
        _state["installed"] = {k: v for k, v in _state["installed"].items() if k in TOOLBARS}
    return _state


def _save():
    save_json(STATE_FILE, _load())


def installed():
    """The toolbars on the computer, oldest first."""
    st = _load()
    return sorted(st["installed"], key=lambda k: st["installed"][k])


def listen(callback):
    """callback() runs whenever a toolbar arrives or is removed (Internet Explorer redraws its bars)."""
    _listeners.append(callback)


def _changed():
    for cb in list(_listeners):
        try:
            cb()
        except RuntimeError:                     # (a closed IE window)
            _listeners.remove(cb)


def maybe_install():
    """While you browse: if it's been a few days since the last one, one more sneaks in. Returns its key or None."""
    st = _load()
    now = datetime.now().timestamp()
    if "next" not in st:                         # the first one takes a day or two
        st["next"] = now + random.uniform(1.0, 2.5) * 86400
        _save()
        return None
    if now < st["next"] or len(st["installed"]) >= MOST:
        return None
    key = random.choice([k for k in TOOLBARS if k not in st["installed"]])
    st["installed"][key] = now
    st["next"] = now + random.uniform(*EVERY_DAYS) * 86400
    _save()
    _changed()
    return key


def remove(key):
    st = _load()
    if st["installed"].pop(key, None) is not None:
        _save()
        _changed()


def by_vendor(vendor):
    return next((k for k, tb in TOOLBARS.items() if tb["vendor"] == vendor), None)


def home_hijack():
    """A hijacker's start page, if one is installed (the newest wins)."""
    return next((TOOLBARS[k]["home"] for k in reversed(installed()) if TOOLBARS[k].get("home")), None)


def search_hijack():
    return next((TOOLBARS[k]["search"] for k in reversed(installed()) if TOOLBARS[k].get("hijack_search")), None)


# ---- in Internet Explorer ------------------------------------------------------------------------------------------
def badge(key, size=18):
    tb = TOOLBARS[key]
    letter, colour = tb["badge"]
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(0, 0, 0, 90), 1))
    p.setBrush(QColor(tb["colours"][0]).darker(130))
    p.drawEllipse(QRectF(0.5, 0.5, size - 1, size - 1))
    p.setPen(QColor(colour))
    f = QFont("Segoe UI Symbol" if not letter.isalnum() else "Arial Black")
    f.setPixelSize(int(size * 0.62))
    f.setBold(True)
    p.setFont(f)
    p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, letter)
    p.end()
    return pm


def _weather():
    """Today's made-up weather, the same all day."""
    rng = random.Random(datetime.now().strftime("%Y%m%d"))
    month = datetime.now().month
    base = {12: 34, 1: 30, 2: 34, 3: 45, 4: 56, 5: 66, 6: 75, 7: 80, 8: 78, 9: 70, 10: 58, 11: 46}[month]
    sky = rng.choice(["Sunny", "Partly Cloudy", "Mostly Cloudy", "Light Rain", "Clear", "Windy"])
    return f"{base + rng.randint(-6, 6)}°F  {sky}"


class AdBar(QWidget):
    """One unwanted toolbar under IE's Address bar."""

    def __init__(self, browser, key):
        super().__init__()
        self.key = key
        self.tb = tb = TOOLBARS[key]
        self.setFixedHeight(27)
        self.setAttribute(Qt.WA_StyledBackground, False)
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 1, 2, 1)
        row.setSpacing(3)
        text = tb["text"]
        style = (f"QToolButton {{ color: {text}; font-family: Tahoma; font-size: 11px; font-weight: bold;"
                 " border: 1px solid transparent; border-radius: 2px; padding: 1px 5px; background: transparent; }"
                 " QToolButton:hover { border: 1px solid rgba(255,255,255,150); background: rgba(255,255,255,50); }")
        logo = QToolButton()
        logo.setIcon(QIcon(badge(key)))
        logo.setText(tb["name"].replace(" Toolbar", "").replace(" Bar", ""))
        logo.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        logo.setStyleSheet(style)
        home = tb.get("home") or tb["buttons"][0][1].split("/", 3)[:3]
        home = home if isinstance(home, str) else "/".join(home) + "/"
        logo.clicked.connect(lambda: browser.navigate(home))
        row.addWidget(logo)
        if tb.get("search"):
            self.box = QLineEdit()
            self.box.setFixedWidth(150)
            self.box.setPlaceholderText("Search the Web")
            self.box.setStyleSheet("QLineEdit { background: white; border: 1px solid #555; padding: 0 2px;"
                                   " font-family: Tahoma; font-size: 11px; }")
            from urllib.parse import quote_plus

            def go():
                q = self.box.text().strip()
                if q:
                    browser.navigate(tb["search"] + quote_plus(q))
            self.box.returnPressed.connect(go)
            row.addWidget(self.box)
            find = QToolButton()
            find.setText("Search")
            find.setStyleSheet(style)
            find.clicked.connect(go)
            row.addWidget(find)
        if tb.get("weather"):
            w = QLabel(_weather())
            w.setStyleSheet(f"QLabel {{ color: {text}; font: bold 11px Tahoma; padding: 0 6px; }}")
            row.addWidget(w)
        for label, url in tb["buttons"]:
            b = QToolButton()
            b.setText(label)
            b.setStyleSheet(style)
            b.clicked.connect(lambda _c=False, u=url: browser.navigate(u))
            row.addWidget(b)
        if tb.get("flashing"):
            self.flash = QLabel(tb["flashing"])
            self.flash.setCursor(Qt.PointingHandCursor)
            self.flash.setMinimumWidth(1)                 # (long: it's cut off rather than widening IE)
            self.flash.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            self.flash.mousePressEvent = lambda _e: browser.navigate(tb["buttons"][0][1])
            row.addWidget(self.flash)
            self._on = False
            self.timer = QTimer(self, interval=600, timeout=self._blink)
            self.timer.start()
            self._blink()
        row.addStretch(1)
        close = QToolButton()
        close.setText("×")
        close.setToolTip(f"Close {tb['name']}")
        close.setStyleSheet(style)
        close.clicked.connect(lambda: self._no_closing(browser))
        row.addWidget(close)

    def _blink(self):
        self._on = not self._on
        self.flash.setStyleSheet(f"QLabel {{ color: {'#FFE14D' if self._on else '#FFFFFF'}; font: bold 11px Tahoma;"
                                 " padding: 0 6px; }")

    def _no_closing(self, browser):
        from ..explorer.dialogs import msgbox
        name = self.tb["name"]
        msgbox(browser.desktop, name, f"{name} cannot be closed while Internet Explorer is running.\n\n"
               f"Upgrade to {name} PLUS for only $19.95 to hide the toolbar and remove ads!", icon="info")

    def paintEvent(self, event):
        p = QPainter(self)
        a, b = self.tb["colours"]
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor(b))
        g.setColorAt(1, QColor(a))
        p.fillRect(self.rect(), g)
        p.setPen(QColor(0, 0, 0, 80))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)


class AdBars(QWidget):
    """The stack of installed toolbars, kept up to date as they come and go."""

    def __init__(self, browser):
        super().__init__()
        from PySide6.QtWidgets import QVBoxLayout
        self.browser = browser
        self.col = QVBoxLayout(self)
        self.col.setContentsMargins(0, 0, 0, 0)
        self.col.setSpacing(0)
        listen(self.refresh)
        self.refresh()

    def refresh(self):
        if not isValid(self):
            raise RuntimeError("gone")
        while self.col.count():
            w = self.col.takeAt(0).widget()
            if w is not None:
                w.hide()
                w.deleteLater()
        keys = installed()
        for key in keys:
            self.col.addWidget(AdBar(self.browser, key))
        self.setVisible(bool(keys))
