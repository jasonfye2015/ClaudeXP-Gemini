"""Lavasoft Ad-aware 5.62 (autumn 2001): scans memory, the registry, your drives and cookies for adware and
data miners, lists what it found, and removes what you tick.

The scan is a maintenance task: it takes a few minutes and never finishes while the model broker still has
background work queued (see CoverClock), so it doubles as a way to let the world catch up. What it finds is
remembered in data/adaware.json: spyware piles up between scans (more when the program it comes bundled with
is on the computer), cookies come from the pages you've browsed, and removed objects stay gone.
"""
import random
from datetime import datetime

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QHBoxLayout, QHeaderView, QLabel, QListWidget, QMenu,
                               QProgressBar, QPushButton, QRadioButton, QStackedWidget, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import clock, sound
from ..paths import DATA
from ..programs.people import load_json, save_json
from ..wm import XPWindow
from . import CoverClock

NAME = "Ad-aware 5.62"
TITLE = "Lavasoft Ad-aware 5.62"
STATE_FILE = DATA / "adaware.json"
REF_FILE = "01R128"
REF_DATE = "10.09.2001"
REF_OBJECTS = 1147

# vendor -> (category, comment, the program it rides in with or None, [(type, object)])
# types: Process, RegKey, RegValue, File, Folder
SPYWARE = {
    "Alexa": ("Datamining", "IE's 'Show Related Links' reports every page you visit", "iexplore", [
        ("RegKey", r"HKEY_LOCAL_MACHINE:Software\Microsoft\Internet Explorer\Extensions\{c95fe080-8f5d-11d2-a20b-00aa003c157a}"),
        ("RegKey", r"HKEY_CURRENT_USER:Software\Microsoft\Internet Explorer\Extensions\{c95fe080-8f5d-11d2-a20b-00aa003c157a}"),
        ("File", r"C:\WINDOWS\Web\related.htm")]),
    "Gator": ("Adware", "GAIN - pop-up ads that follow what you do online", None, [
        ("Process", r"C:\Program Files\Gator\gator.exe"),
        ("RegKey", r"HKEY_LOCAL_MACHINE:Software\Gator.com"),
        ("RegValue", r"HKEY_LOCAL_MACHINE:Software\Microsoft\Windows\CurrentVersion\Run [Trickler]"),
        ("File", r"C:\Program Files\Common Files\CMEII\CMEIIAPI.dll"),
        ("Folder", r"C:\Program Files\Gator")]),
    "Cydoor": ("Adware", "Ad banners bundled with file-sharing programs", "torrent", [
        ("Process", r"C:\WINDOWS\System32\cd_load.exe"),
        ("RegKey", r"HKEY_LOCAL_MACHINE:Software\Cydoor"),
        ("File", r"C:\WINDOWS\System32\cd_clint.dll"),
        ("File", r"C:\WINDOWS\System32\cd_htm.dll")]),
    "New.net": ("Hijacker", "Adds fake top-level domains to your browser", "torrent", [
        ("RegKey", r"HKEY_LOCAL_MACHINE:Software\New.net"),
        ("File", r"C:\WINDOWS\System32\NewDotNet4_67.dll"),
        ("Folder", r"C:\Program Files\New.net")]),
    "webHancer": ("Datamining", "Reports how fast the pages you visit load, and which ones", "trillian", [
        ("Process", r"C:\Program Files\webHancer\Programs\whagent.exe"),
        ("RegKey", r"HKEY_LOCAL_MACHINE:Software\webHancer"),
        ("File", r"C:\WINDOWS\System32\whiehlpr.dll"),
        ("Folder", r"C:\Program Files\webHancer")]),
    "Comet Systems": ("Adware", "Comet Cursor - animated cursors that phone home", "stylexp", [
        ("RegKey", r"HKEY_LOCAL_MACHINE:Software\Comet Systems"),
        ("File", r"C:\Program Files\Comet\cometcursor.exe"),
        ("File", r"C:\WINDOWS\System32\comet.dll"),
        ("Folder", r"C:\Program Files\Comet")]),
    "Radiate": ("Adware", "Aureate/Radiate ad engine from 'free' downloads", "claudeamp", [
        ("RegKey", r"HKEY_LOCAL_MACHINE:Software\Aureate"),
        ("File", r"C:\WINDOWS\System32\advert.dll"),
        ("File", r"C:\WINDOWS\System32\amcis.dll"),
        ("File", r"C:\WINDOWS\System32\anadsc.ocx")]),
    "Conducent": ("Adware", "TimeSink ad gateway from ad-supported shareware", "winzip", [
        ("Process", r"C:\Program Files\TimeSink\Ad-Gateway\TSADBOT.EXE"),
        ("RegKey", r"HKEY_LOCAL_MACHINE:Software\TimeSink"),
        ("Folder", r"C:\Program Files\TimeSink")]),
    "SaveNow": ("Adware", "WhenU pop-ups when you visit shopping sites", None, [
        ("Process", r"C:\Program Files\SaveNow\SaveNow.exe"),
        ("RegValue", r"HKEY_LOCAL_MACHINE:Software\Microsoft\Windows\CurrentVersion\Run [SaveNow]"),
        ("Folder", r"C:\Program Files\SaveNow")]),
    "Hotbar": ("Adware", "Toolbar skins for Internet Explorer and Outlook Express - with ads", "outlook", [
        ("RegKey", r"HKEY_CLASSES_ROOT:CLSID\{B195B3B3-8A05-11D3-97A4-0004ACA6948E}"),
        ("File", r"C:\Program Files\Hotbar\hotbar.dll"),
        ("Folder", r"C:\Program Files\Hotbar")]),
    "Bonzi Software": ("Adware", "BonziBUDDY - the 'friendly' purple gorilla", "clippy", [
        ("Process", r"C:\Program Files\BonziBuddy332\BonziBDY.exe"),
        ("RegKey", r"HKEY_LOCAL_MACHINE:Software\Bonzi"),
        ("Folder", r"C:\Program Files\BonziBuddy332")]),
}
AD_HOSTS = ["doubleclick.net", "atdmt.com", "hitbox.com", "valueclick.com", "fastclick.net", "linksynergy.com",
            "burstnet.com", "advertising.com", "ads.x10.com", "mediaplex.com", "247realmedia.com", "bfast.com",
            "qksrv.net", "tribalfusion.com", "falkag.net"]
REGISTRY = [r"HKEY_LOCAL_MACHINE\Software\Classes\CLSID", r"HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion",
            r"HKEY_CURRENT_USER\Software\Microsoft\Internet Explorer\Main", r"HKEY_LOCAL_MACHINE\Software\Microsoft\Internet Explorer",
            r"HKEY_CLASSES_ROOT\Interface", r"HKEY_CLASSES_ROOT\TypeLib", r"HKEY_LOCAL_MACHINE\System\CurrentControlSet\Services",
            r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer", r"HKEY_USERS\.DEFAULT\Software",
            r"HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Uninstall",
            r"HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects"]
# where each kind of object turns up during the scan (fraction of the progress bar)
PHASES = [(0.0, "Scanning memory", "Process"), (0.10, "Scanning registry", "RegKey"),
          (0.30, "Deep scanning registry", "RegValue"), (0.38, "Scanning drives", "File"),
          (0.92, "Scanning cookies", "Cookie")]
REVEAL = {"Process": 0.08, "RegKey": 0.25, "RegValue": 0.36, "File": 0.7, "Folder": 0.85, "Cookie": 0.97}

STYLE = """
QWidget#aa { background: #DCE2EA; }
QWidget#side { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #42557A, stop:1 #26334D); }
QLabel { font-family: Tahoma; font-size: 11px; color: #1D2A40; }
QLabel#head { font-size: 15px; font-weight: bold; color: #26334D; }
QLabel#sub { color: #4A5A78; }
QPushButton#nav { text-align: left; padding: 7px 10px; border: none; color: #E8EEF8; font-family: Tahoma;
                  font-size: 11px; font-weight: bold; background: transparent; }
QPushButton#nav:hover { background: #5A70A0; }
QPushButton#nav:disabled { color: #7A88A4; }
QPushButton#big { font-family: Tahoma; font-size: 13px; font-weight: bold; color: white; border: 1px solid #1D2A40;
                  border-radius: 4px; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6F8BC0, stop:1 #34497A);
                  padding: 6px 18px; }
QPushButton#big:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #86A2D6, stop:1 #42598E); }
QPushButton { font-family: Tahoma; font-size: 11px; }
QTreeWidget, QListWidget { background: white; border: 1px solid #7F9DB9; font-family: Tahoma; font-size: 11px; }
QRadioButton, QCheckBox { font-family: Tahoma; font-size: 11px; color: #1D2A40; }
QProgressBar { border: 1px solid #7F9DB9; background: white; height: 14px; }
QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8FB0E8, stop:1 #34497A); }
"""


# ---- artwork --------------------------------------------------------------------------------------------------------

def aa_logo(size=32):
    """Ad-aware's badge: a steel-blue disc with a white 'a' under a red scan line."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#9DB4DC"))
    g.setColorAt(0.5, QColor("#42598E"))
    g.setColorAt(1, QColor("#1D2A40"))
    p.setPen(QPen(QColor("#141D2E"), max(1.0, s)))
    p.setBrush(g)
    p.drawEllipse(QRectF(1.5 * s, 1.5 * s, 29 * s, 29 * s))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 255, 255, 60))
    p.drawEllipse(QRectF(6 * s, 3 * s, 20 * s, 10 * s))
    font = QFont("Arial Black", 1)
    font.setPixelSize(max(6, int(22 * s)))
    font.setBold(True)
    path = QPainterPath()
    path.addText(0, 0, font, "a")
    r = path.boundingRect()
    path.translate(16 * s - r.center().x(), 17 * s - r.center().y())
    p.setPen(QPen(QColor("#141D2E"), max(0.6, 0.8 * s)))
    p.setBrush(QColor("white"))
    p.drawPath(path)
    p.setPen(QPen(QColor("#E8341C"), max(1.2, 2.2 * s), Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(5 * s, 21.5 * s), QPointF(27 * s, 21.5 * s))
    p.end()
    return pm


def aa_icon():
    icon = QIcon()
    for size in (16, 32, 48):
        icon.addPixmap(aa_logo(size))
    return icon


class Banner(QWidget):
    """The header strip, drawn to whatever width the window is."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(64)

    def paintEvent(self, _e):
        p = QPainter(self)
        _paint_banner(p, self.width(), self.height())
        p.end()


def _paint_banner(p, width, height):
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, width, 0)
    g.setColorAt(0, QColor("#1D2A40"))
    g.setColorAt(0.6, QColor("#42598E"))
    g.setColorAt(1, QColor("#8FA6D0"))
    p.fillRect(QRectF(0, 0, width, height), g)
    p.setPen(QPen(QColor(255, 255, 255, 30), 1))
    for x in range(-height, width, 9):                  # faint scan lines
        p.drawLine(x, height, x + height, 0)
    p.drawPixmap(12, 8, aa_logo(48))
    f = QFont("Arial", 24)
    f.setBold(True)
    f.setItalic(True)
    p.setFont(f)
    p.setPen(QColor("white"))
    p.drawText(QRectF(70, 6, 300, 40), Qt.AlignLeft | Qt.AlignVCenter, "Ad-aware")
    right = 70 + p.fontMetrics().horizontalAdvance("Ad-aware") + 10
    f = QFont("Arial", 14)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#FFB23C"))
    p.drawText(QRectF(right, 10, 80, 36), Qt.AlignLeft | Qt.AlignVCenter, "5.62")
    p.setFont(QFont("Tahoma", 8))
    p.setPen(QColor("#D8E2F2"))
    p.drawText(QRectF(72, 40, 300, 18), Qt.AlignLeft, "Personal Edition  -  Your privacy is our concern")
    f = QFont("Arial", 13)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#1D2A40"))
    p.drawText(QRectF(width - 140, 0, 128, height), Qt.AlignRight | Qt.AlignVCenter, "Lavasoft")


# ---- what's on the computer -----------------------------------------------------------------------------------------

def _user():
    from ..user import profile_name
    return profile_name()


def _today():
    now = clock.now()
    return f"{now.month}/{now.day}/{now.year}"


def _browsed_since(stamp):
    """How many web pages were written into the browser cache since stamp (a POSIX time)."""
    try:
        from ..programs.navigator import web
        return sum(1 for f in web.CACHE_DIR.rglob("*") if f.is_file() and f.stat().st_mtime > stamp)
    except OSError:
        return 0


def _scan_paths():
    from .antivirus import _scan_paths as paths
    return paths()


class AdAware:
    def __init__(self, desktop):
        self.desktop = desktop
        self.state = load_json(STATE_FILE, {})
        self.state.setdefault("present", {})        # vendor -> date it arrived
        self.state.setdefault("cookies", [])
        self.state.setdefault("cleared", {})        # vendor -> its objects already removed
        self.state.setdefault("quarantine", [])
        self.state.setdefault("removed_total", 0)
        self.state.setdefault("runs", 0)
        self.win = None
        self.scanning = False
        self.timer = None

    def _save(self):
        save_json(STATE_FILE, self.state)

    def busy(self):
        return self.scanning

    # ---- spyware arriving between scans ----------------------------------------------------------------------------
    def _accrue(self):
        """Adware that crept in since the last scan; cookies from the pages browsed since then."""
        st = self.state
        last = st.get("last_scan_ts")
        now = datetime.now().timestamp()
        days = 30 if last is None else max(0.0, (now - last) / 86400)
        first = last is None
        for vendor, (_cat, _comment, rides_with, _objs) in SPYWARE.items():
            if vendor in st["present"]:
                continue
            if first and vendor == "Alexa":
                chance = 1.0                           # IE6 ships with it switched on
            elif vendor == "Alexa":
                chance = 0.0
            else:
                chance = (0.32 if rides_with else 0.14) * min(1.0, days / 21 + 0.15)
            if random.random() < chance:
                st["present"][vendor] = _today()
        pages = _browsed_since(last or 0)
        if first:
            pages = max(pages, 6)
        if pages:
            have = set(st["cookies"])
            fresh = [h for h in AD_HOSTS if h not in have]
            random.shuffle(fresh)
            st["cookies"] += fresh[:min(len(fresh), 1 + pages // 3)]

    def findings(self):
        """[(vendor, type, category, object, comment)] for everything currently on the computer."""
        user = _user().lower().replace(" ", "")
        rows = []
        for vendor in self.state["present"]:
            if vendor not in SPYWARE:
                continue
            cat, comment, _r, objs = SPYWARE[vendor]
            cleared = self.state["cleared"].get(vendor, [])
            rows += [(vendor, kind, cat, obj, comment) for kind, obj in objs if obj not in cleared]
        for host in self.state["cookies"]:
            rows.append((host.split(".")[0].title() if host != "ads.x10.com" else "X10", "Cookie",
                         "Tracking Cookie", f"Cookie:{user}@{host}/", "Tracks you from site to site"))
        return rows

    # ---- the window ------------------------------------------------------------------------------------------------
    def open(self, automatic=False):
        if self.win is not None and isValid(self.win):
            self.desktop.open_window(self.win)
            return self.win
        self.state["runs"] += 1
        self._save()
        body = QWidget()
        body.setObjectName("aa")
        body.setAttribute(Qt.WA_StyledBackground, True)
        body.setStyleSheet(STYLE)
        body.process_image = "ad-aware.exe"          # for Task Manager
        outer = QVBoxLayout(body)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(Banner())
        row = QHBoxLayout()
        row.setSpacing(0)
        outer.addLayout(row, 1)

        side = QWidget()
        side.setObjectName("side")
        side.setAttribute(Qt.WA_StyledBackground, True)
        side.setFixedWidth(130)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(0, 10, 0, 10)
        sv.setSpacing(2)
        self.nav = []
        for label, slot in (("Status", self.show_status), ("Scan now", self.show_prepare),
                            ("Quarantine", self.show_quarantine), ("Web update", self.web_update),
                            ("Help", self.show_help)):
            b = QPushButton(label)
            b.setObjectName("nav")
            b.clicked.connect(slot)
            sv.addWidget(b)
            self.nav.append(b)
        sv.addStretch()
        ver = QLabel("<font color='#AFC0DC'>Ad-aware 5.62<br>&copy; Lavasoft 2001</font>")
        ver.setAlignment(Qt.AlignCenter)
        sv.addWidget(ver)
        row.addWidget(side)

        self.pages = QStackedWidget()
        row.addWidget(self.pages, 1)
        self._build_pages()
        self.win = XPWindow(self.desktop, TITLE, body, aa_icon(), size=(700, 480))
        self.win.destroyed.connect(self._closed)
        prev = self.desktop.active
        self.desktop.open_window(self.win)
        if automatic and prev is not None and isValid(prev):
            self.desktop.activate(prev)
        self.show_status()
        return self.win

    def _closed(self, *_):
        self.win = None
        if self.timer is not None:
            self.timer.stop()
        self.scanning = False

    def _page(self, title, sub=""):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(18, 14, 18, 14)
        head = QLabel(title)
        head.setObjectName("head")
        v.addWidget(head)
        if sub:
            s = QLabel(sub)
            s.setObjectName("sub")
            s.setWordWrap(True)
            v.addWidget(s)
        v.addSpacing(6)
        self.pages.addWidget(page)
        return page, v

    def _buttons(self, v, *buttons):
        row = QHBoxLayout()
        row.addStretch()
        for b in buttons:
            if b.objectName() != "big":
                b.setFixedSize(85, 24)
            row.addWidget(b)
        v.addLayout(row)

    def _build_pages(self):
        # status
        self.p_status, v = self._page("Status", "Ad-aware finds and removes adware, data miners and tracking "
                                                "objects that collect information about you.")
        self.status_text = QLabel()
        self.status_text.setAlignment(Qt.AlignTop)
        self.status_text.setMinimumHeight(190)
        v.addWidget(self.status_text)
        v.addStretch()
        start = QPushButton("Start")
        start.setObjectName("big")
        start.clicked.connect(self.show_prepare)
        self._buttons(v, start)

        # preparing the scan
        self.p_prepare, v = self._page("Preparing system scan", "Select a scan mode:")
        self.mode = QButtonGroup(self.p_prepare)
        smart = QRadioButton("Use default scan settings (memory, registry, cookies, system folders)")
        full = QRadioButton("Use custom scan settings (all local drives, deep registry scan)")
        smart.setChecked(True)
        self.mode.addButton(smart, 0)
        self.mode.addButton(full, 1)
        v.addWidget(smart)
        v.addWidget(full)
        v.addSpacing(8)
        self.indepth = QCheckBox("Activate in-depth scan (recommended)")
        self.indepth.setChecked(True)
        v.addWidget(self.indepth)
        v.addStretch()
        back = QPushButton("< Back")
        back.clicked.connect(self.show_status)
        nxt = QPushButton("Next >")
        nxt.clicked.connect(lambda: self.scan())
        self._buttons(v, back, nxt)

        # scanning
        self.p_scan, v = self._page("Scanning", "Please wait while Ad-aware scans your system.")
        self.phase = QLabel()
        self.phase.setStyleSheet("font-weight: bold;")
        v.addWidget(self.phase)
        self.current = QLabel(" ")
        self.current.setFixedWidth(440)
        v.addWidget(self.current)
        v.addSpacing(6)
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        v.addWidget(self.bar)
        v.addSpacing(6)
        self.counts = QLabel()
        v.addWidget(self.counts)
        v.addStretch()
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_scan)
        self._buttons(v, self.stop_btn)

        # scan complete
        self.p_done, v = self._page("Scan complete")
        self.summary = QLabel()
        self.summary.setAlignment(Qt.AlignTop)
        self.summary.setMinimumHeight(260)
        v.addWidget(self.summary)
        v.addStretch()
        self.done_next = QPushButton("Next >")
        self.done_next.clicked.connect(self.show_results)
        self._buttons(v, self.done_next)

        # results
        self.p_results, v = self._page("Scanning results", "Tick the objects to remove. Right-click for more options.")
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Obj", "Vendor", "Type", "Category", "Object", "Comment"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        h = self.tree.header()
        for col, w in enumerate((44, 96, 64, 96, 300, 260)):
            h.resizeSection(col, w)
        h.setSectionResizeMode(QHeaderView.Interactive)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._results_menu)
        v.addWidget(self.tree, 1)
        back = QPushButton("< Back")
        back.clicked.connect(lambda: self.pages.setCurrentWidget(self.p_done))
        self.remove_btn = QPushButton("Next >")
        self.remove_btn.clicked.connect(self.remove_checked)
        self._buttons(v, back, self.remove_btn)

        # quarantine
        self.p_quar, v = self._page("Quarantine", "Every removal is backed up first, so it can be restored.")
        self.qlist = QListWidget()
        v.addWidget(self.qlist, 1)

        # help
        self.p_help, v = self._page("Help")
        help_text = QLabel(
            "<b>What is adware?</b> 'Free' programs often pay for themselves by installing components that show "
            "ads or report what you do online. Ad-aware recognises them from its reference file and removes them "
            "safely.<br><br><b>Tracking cookies</b> are left by advertising networks on the pages you browse, so "
            "they can follow you from site to site.<br><br>Scan regularly - new objects appear every time you "
            "install something or surf the Web.<br><br><b>Tip:</b> a full scan takes a while. It's a good time "
            "to get a cup of coffee.")
        help_text.setWordWrap(True)
        help_text.setAlignment(Qt.AlignTop)
        v.addWidget(help_text)
        v.addStretch()

    # ---- pages -----------------------------------------------------------------------------------------------------
    def _nav_enabled(self, on):
        for b in self.nav:
            b.setEnabled(on)

    def show_status(self):
        if self.scanning:
            return
        st = self.state
        n = len(self.findings()) if st.get("last_scan") else 0
        objs = (f"<font color='#C02010'><b>{n} objects not removed</b></font>" if n else "None") \
            if st.get("last_scan") else "No scan performed yet"
        self.status_text.setText(
            "<table cellpadding='3'>"
            "<tr><td><b>Status:</b></td><td><font color='#207020'><b>Initialized</b></font></td></tr>"
            f"<tr><td><b>Reference file:</b></td><td>{REF_FILE} ({REF_DATE})</td></tr>"
            f"<tr><td><b>Objects in reference file:</b></td><td>{REF_OBJECTS:,}</td></tr>"
            f"<tr><td><b>Usage:</b></td><td>Ad-aware started {st['runs']} time{'s' if st['runs'] != 1 else ''}</td></tr>"
            f"<tr><td><b>Last system scan:</b></td><td>{st.get('last_scan', 'Never')}</td></tr>"
            f"<tr><td><b>Objects removed total:</b></td><td>{st['removed_total']}</td></tr>"
            f"<tr><td><b>Found last scan:</b></td><td>{objs}</td></tr></table>")
        self.pages.setCurrentWidget(self.p_status)

    def show_prepare(self):
        if not self.scanning:
            self.pages.setCurrentWidget(self.p_prepare)

    def show_quarantine(self):
        if self.scanning:
            return
        self.qlist.clear()
        self.qlist.addItems([f"{q['date']}  -  {q['count']} objects  ({q['name']})" for q in self.state["quarantine"]]
                            or ["(no backups yet)"])
        self.pages.setCurrentWidget(self.p_quar)

    def show_help(self):
        if not self.scanning:
            self.pages.setCurrentWidget(self.p_help)

    def web_update(self):
        from .. import network
        from ..explorer.dialogs import msgbox
        if self.scanning:
            return
        if not network.is_connected():
            msgbox(self.desktop, "Ad-aware Web Update", "Could not connect to the Lavasoft update server.\n\n"
                   "Connect to the Internet and try again.", icon="warning", window_icon=aa_icon())
            return
        msgbox(self.desktop, "Ad-aware Web Update", f"You have the latest reference file ({REF_FILE}, {REF_DATE}).",
               icon="info", window_icon=aa_icon())

    # ---- scanning --------------------------------------------------------------------------------------------------
    def scan(self, automatic=False):
        """Start a system scan (opening the window if needed)."""
        if self.scanning:
            if self.win is not None and isValid(self.win):
                self.desktop.open_window(self.win)
            return
        self.open(automatic=automatic)
        self._accrue()
        found = self.findings()
        full = self.mode.checkedId() == 1 or automatic
        seconds = random.uniform(90, 170) if full else random.uniform(55, 100)
        if self.indepth.isChecked():
            seconds *= 1.2
        self.scanning = True
        self._nav_enabled(False)
        self.stop_btn.setEnabled(True)
        self.pages.setCurrentWidget(self.p_scan)
        clock_ = CoverClock(seconds)
        files = _scan_paths()
        procs = self._processes()
        rows = list(found)
        random.shuffle(rows)
        state = {"objects": 0, "i": 0}
        self.timer = QTimer(self.p_scan)
        win = self.win

        def tick():
            if not isValid(win):
                return
            f = clock_.fraction()
            phase = next(name for at, name, _k in reversed(PHASES) if f >= at)
            self.phase.setText(phase + "...")
            if phase == "Scanning memory":
                obj = random.choice(procs)
                state["objects"] += random.randint(1, 3)
            elif "registry" in phase:
                obj = random.choice(REGISTRY) + "\\" + "".join(random.choice("0123456789ABCDEF") for _ in range(8))
                state["objects"] += random.randint(30, 140)
            elif phase == "Scanning drives":
                state["i"] = (state["i"] + random.randint(1, 4)) % len(files)
                obj = files[state["i"]]
                state["objects"] += random.randint(8, 40)
            else:
                obj = rf"C:\Documents and Settings\{_user()}\Cookies\{_user().lower()}@{random.choice(AD_HOSTS)}[1].txt"
                state["objects"] += random.randint(1, 4)
            self.current.setText(self.current.fontMetrics().elidedText(obj, Qt.ElideMiddle, 440))
            seen = sum(1 for r in rows if REVEAL.get(r[1], 0.7) <= f)
            self.counts.setText(f"Objects scanned: {state['objects']:,}        Objects identified: {seen}")
            self.bar.setValue(int(f * 100))
            if f >= 1.0:
                self.timer.stop()
                self._scan_done(state["objects"], automatic)

        self.timer.timeout.connect(tick)
        self.timer.start(110)

    def _processes(self):
        from ..programs import taskmgr
        procs = [rf"C:\WINDOWS\System32\{img}" for img, _u, _m in taskmgr.SYSTEM if img.endswith(".exe")]
        procs += [rf"C:\Program Files\{p}" for p in ("ClaudeAIM\\ClaudeAIM.exe", "Internet Explorer\\IEXPLORE.EXE",
                                                     "Lavasoft\\Ad-aware 5.6\\Ad-aware.exe")]
        procs += [o for v in self.state["present"] for k, o in SPYWARE.get(v, ("", "", None, []))[3]
                  if k == "Process"]
        return procs

    def stop_scan(self):
        if self.timer is not None:
            self.timer.stop()
        self.scanning = False
        self._nav_enabled(True)
        self.show_status()

    def _scan_done(self, objects, automatic):
        self.scanning = False
        self._nav_enabled(True)
        now = clock.now()
        st = self.state
        st["last_scan"] = f"{now.month}/{now.day}/{now.year} {clock.time_text(now)}"
        st["last_scan_ts"] = datetime.now().timestamp()
        self._save()
        rows = self.findings()
        by_type = {}
        for r in rows:
            by_type[r[1]] = by_type.get(r[1], 0) + 1
        lines = "".join(f"<tr><td>{label}:</td><td><b>{by_type.get(k, 0)}</b></td></tr>" for k, label in (
            ("Process", "Processes in memory"), ("RegKey", "Registry keys"), ("RegValue", "Registry values"),
            ("File", "Files"), ("Folder", "Folders"), ("Cookie", "Tracking cookies")))
        self.summary.setText(
            f"<b>Ad-aware has finished scanning your system.</b><br><br>Objects scanned: {objects:,}<br>"
            f"<font size='4' color='{'#C02010' if rows else '#207020'}'><b>{len(rows)} new objects identified</b>"
            f"</font><br><br><table cellpadding='2'>{lines}</table>"
            + ("<br>Click <b>Next</b> to review the objects and remove them." if rows
               else "<br>Your system is clean."))
        self.done_next.setEnabled(bool(rows))
        self._fill_results(rows)
        self.pages.setCurrentWidget(self.p_done)
        sound.play("notify")
        if automatic and self.win is not None and isValid(self.win):
            self.win.flash()

    def _fill_results(self, rows):
        self.tree.clear()
        for vendor, kind, cat, obj, comment in rows:
            item = QTreeWidgetItem(["", vendor, kind, cat, obj, comment])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked)
            item.setToolTip(4, obj)
            item.setData(0, Qt.UserRole, (vendor, kind, obj))
            self.tree.addTopLevelItem(item)

    def show_results(self):
        self.pages.setCurrentWidget(self.p_results)

    def _results_menu(self, pos):
        m = QMenu(self.tree)
        m.addAction("Select all objects", lambda: self._check_all(Qt.Checked))
        m.addAction("Deselect all objects", lambda: self._check_all(Qt.Unchecked))
        m.addAction("Invert selection", self._invert)
        m.exec(self.tree.viewport().mapToGlobal(pos))

    def _items(self):
        return [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())]

    def _check_all(self, state):
        for item in self._items():
            item.setCheckState(0, state)

    def _invert(self):
        for item in self._items():
            item.setCheckState(0, Qt.Unchecked if item.checkState(0) == Qt.Checked else Qt.Checked)

    def remove_checked(self):
        from ..explorer.dialogs import msgbox
        chosen = [item.data(0, Qt.UserRole) for item in self._items() if item.checkState(0) == Qt.Checked]
        if not chosen:
            self.show_status()
            return

        def answer(button):
            if button == "OK":
                self._remove(chosen)

        msgbox(self.desktop, "Ad-aware", f"{len(chosen)} objects will be removed. Continue?", icon="question",
               buttons=("OK", "Cancel"), on_button=answer, window_icon=aa_icon())

    def _remove(self, chosen):
        st = self.state
        cookies = {obj.split("@", 1)[1].rstrip("/") for _v, kind, obj in chosen if kind == "Cookie"}
        st["cookies"] = [c for c in st["cookies"] if c not in cookies]
        for vendor in {v for v, kind, _o in chosen if kind != "Cookie"}:
            objs = SPYWARE.get(vendor, ("", "", None, []))[3]
            cleared = st["cleared"].setdefault(vendor, [])
            cleared += [o for v, _k, o in chosen if v == vendor and o not in cleared]
            if all(o in cleared for _k, o in objs):         # all of it gone: the vendor's gone
                st["present"].pop(vendor, None)
                st["cleared"].pop(vendor, None)
        now = clock.now()
        st["quarantine"].insert(0, {"date": f"{now.month}/{now.day}/{now.year} {clock.time_text(now)}",
                                    "count": len(chosen),
                                    "name": f"ad-aware-backup-{now:%Y%m%d-%H%M%S}.ref"})
        st["removed_total"] += len(chosen)
        self._save()
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, "Ad-aware", f"{len(chosen)} objects removed.\n\nA backup was saved in Quarantine.",
               icon="info", window_icon=aa_icon())
        self.show_status()


_adaware = None


def get(desktop):
    global _adaware
    if _adaware is None:
        _adaware = AdAware(desktop)
    return _adaware


def launch(desktop):
    get(desktop).open()


def running():
    return _adaware is not None and _adaware.busy()
