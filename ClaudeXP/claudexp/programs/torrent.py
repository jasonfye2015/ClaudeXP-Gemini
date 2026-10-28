"""ClaudeTorrent 0.9 beta: a BitTorrent client, for show.

Six multi-gigabyte torrents (programs, video, music) at various stages, a details pane (General with the pieces
bar, Files, Peers, Speed graph), start/stop one or all - but torrents can't be removed. Over dial-up it crawls
along at a few kB/s while 'Connect to the Internet' is online, and waits for the connection otherwise. Nothing is
ever written to disk, and a torrent that somehow finishes is checked, reset and downloaded again.

It lives in the notification area: arrows that light up with traffic (grey when offline), a speed tooltip, and a
menu with Open / Start All / Stop All / Load at Startup / Exit. Closing the window tucks it into the tray; Exit
really quits. Settings > Preferences can turn off loading at startup. State lives in data/claudetorrent.json."""
import hashlib
import math
import random
import time
from collections import deque

from PySide6.QtCore import QObject, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (QAction, QColor, QFont, QIcon, QKeySequence, QLinearGradient, QPainter, QPainterPath,
                           QPen, QPixmap, QPolygonF)
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QHBoxLayout, QHeaderView, QLabel, QMenu, QMenuBar,
                               QPushButton, QSplitter, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QToolButton,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import network, sound
from ..paths import DATA
from ..wm import XPWindow
from .notepad import MENU_STYLE
from .people import load_json, save_json

STATE_FILE = DATA / "claudetorrent.json"
TITLE = "ClaudeTorrent 0.9 beta"
GB, MB, KB = 1024 ** 3, 1024 ** 2, 1024
DIALUP = 4.6 * KB                   # what a good 56k day gives a single download, bytes/s
TRACKER = "http://tracker.claudetorrent.net:6969/announce"

# name, kind, size, starting progress, status, seed availability (0 = nobody's seeding right now), files
TORRENTS = [
    ("Red Hat Linux 7.2 (Enigma) - i386 CD ISOs", "Program", int(1.97 * GB), 0.412, "downloading", 6,
     [("enigma-i386-disc1.iso", 0.34), ("enigma-i386-disc2.iso", 0.33), ("enigma-SRPMS-disc1.iso", 0.33)]),
    ("Space Shuttle Launches - The Complete Collection (TV-Rip DivX 5)", "Video", int(4.37 * GB), 0.087, "queued",
     3, [(f"STS-{n:03d} Launch.avi", 1 / 12) for n in (1, 7, 31, 41, 51, 61, 71, 82, 88, 95, 99, 104)]),
    ("Grateful Dead - Live 1977 Soundboards (SHN, trade-friendly)", "Music", int(2.41 * GB), 0.634, "paused", 9,
     [(f"gd77-05-{d:02d}d{disc}t{t:02d}.shn", 1 / 36) for d in (8, 9, 11) for disc in (1, 2, 3)
      for t in (1, 2, 3, 4)]),
    ("Public Domain Cartoons 1930-1950 (MPEG-1)", "Video", int(3.18 * GB), 0.218, "stalled", 0,
     [(f"Cartoon {n:02d}.mpg", 1 / 40) for n in range(1, 41)]),
    ("Best of 80s Synth Pop - 180 MP3s (192 kbps)", "Music", int(1.09 * GB), 0.951, "stopped", 2,
     [(f"Track {n:03d}.mp3", 1 / 180) for n in range(1, 181)]),
    ("Game Demos Mega Pack - Fall 2001 (installers)", "Program", int(2.86 * GB), 0.0, "queued", 4,
     [(f"demo{n:02d}_setup.exe", 1 / 18) for n in range(1, 19)]),
]
CLIENTS = ["BitTorrent 2.0", "BitTorrent 2.0", "BitTorrent 3.0 beta", "Shad0w's 5.0", "ClaudeTorrent 0.9b"]
STATUS_TEXT = {"downloading": "Downloading", "queued": "Queued", "paused": "Paused", "stopped": "Stopped",
               "stalled": "Stalled - no seeds", "checking": "Checking", "waiting": "Waiting for connection",
               "connecting": "Connecting to tracker..."}


def fmt_size(n):
    for unit, size in (("GB", GB), ("MB", MB), ("kB", KB)):
        if n >= size:
            return f"{n / size:.2f} {unit}" if unit == "GB" else f"{n / size:.1f} {unit}"
    return f"{int(n)} B"


def fmt_rate(bps):
    return f"{bps / KB:.1f} kB/s" if bps > 0 else ""


def fmt_eta(seconds):
    if seconds is None or seconds <= 0 or seconds > 10 ** 9:
        return "∞"
    d, rem = divmod(int(seconds), 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    if d > 365:
        return f"{d // 365}y {d % 365}d"
    if d:
        return f"{d}d {h}h"
    return f"{h}h {m}m" if h else f"{m}m"


# ---- icons -------------------------------------------------------------------------------------------------------

def _arrows(p, s, down_on, up_on, offline=False):
    """The two transfer arrows: green down, red up (dim when idle, grey when offline)."""
    down = QColor("#2EA02E" if down_on else "#9FC49F")
    up = QColor("#D03020" if up_on else "#D8A8A0")
    if offline:
        down = up = QColor("#A0A0A0")
    p.setPen(QPen(down.darker(150), 0.8))
    p.setBrush(down)
    p.drawPolygon(QPolygonF([QPointF(s * 0.05, s * 0.48), QPointF(s * 0.45, s * 0.48), QPointF(s * 0.25, s * 0.95)]))
    p.drawRect(QRectF(s * 0.15, s * 0.08, s * 0.2, s * 0.42))
    p.setPen(QPen(up.darker(150), 0.8))
    p.setBrush(up)
    p.drawPolygon(QPolygonF([QPointF(s * 0.55, s * 0.52), QPointF(s * 0.95, s * 0.52), QPointF(s * 0.75, s * 0.05)]))
    p.drawRect(QRectF(s * 0.65, s * 0.5, s * 0.2, s * 0.42))


def torrent_icon(size=32, down_on=True, up_on=True, offline=False):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    if size >= 24:                                                      # a disc behind the arrows
        g = QLinearGradient(0, 0, size, size)
        g.setColorAt(0, QColor("#F4F8FF"))
        g.setColorAt(1, QColor("#8AA8D8"))
        p.setPen(QPen(QColor("#4A6A9A"), 1))
        p.setBrush(g)
        p.drawEllipse(QRectF(1.5, 1.5, size - 3, size - 3))
        p.translate(size * 0.18, size * 0.18)
        _arrows(p, size * 0.64, down_on, up_on, offline)
    else:
        _arrows(p, size, down_on, up_on, offline)
    p.end()
    return QIcon(pm)


def tray_icon(down_on, up_on, offline):
    return torrent_icon(16, down_on, up_on, offline)


# ---- the engine ----------------------------------------------------------------------------------------------------

class Torrent:
    def __init__(self, d):
        self.name, self.kind, self.size = d["name"], d["kind"], d["size"]
        self.done = float(d.get("done", 0))
        self.status = d.get("status", "queued")
        self.seeds_avail = d.get("seeds_avail", 3)
        self.files = d.get("files", [])
        self.uploaded = float(d.get("uploaded", 0))
        self.added = d.get("added", "2001-09-28")
        self.down = self.up = 0.0
        self.seeds = self.peers = 0
        self.peer_list = []
        self.connect_until = 0.0
        self.check_until = 0.0
        self.hash = hashlib.sha1(self.name.encode()).hexdigest().upper()
        self.piece = 512 * KB if self.size < 2 * GB else 1 * MB
        self.pieces = math.ceil(self.size / self.piece)
        order = list(range(self.pieces))
        random.Random(self.hash).shuffle(order)
        self.order = order                                               # rarest-first, more or less

    def to_dict(self):
        return {"name": self.name, "kind": self.kind, "size": self.size, "done": round(self.done),
                "status": self.status if self.status not in ("waiting", "connecting", "checking") else "downloading",
                "seeds_avail": self.seeds_avail, "files": self.files, "uploaded": round(self.uploaded),
                "added": self.added}

    @property
    def running(self):
        return self.status in ("downloading", "waiting", "connecting", "stalled", "checking")

    @property
    def progress(self):
        return min(1.0, self.done / self.size)

    def have_map(self, columns):
        """Fraction of pieces held, per column of a bar `columns` wide."""
        have = int(self.progress * self.pieces)
        got = [0] * columns
        per = self.pieces / columns
        for idx in self.order[:have]:
            got[min(columns - 1, int(idx / per))] += 1
        return [g / per for g in got]


class Engine(QObject):
    """Moves the bytes. Runs whenever ClaudeTorrent is running (tray or window)."""
    updated = Signal()

    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        st = load_json(STATE_FILE, {})
        if st.get("torrents"):
            self.torrents = [Torrent(d) for d in st["torrents"]]
        else:
            self.torrents = [Torrent({"name": n, "kind": k, "size": s, "done": s * p, "status": stt,
                                      "seeds_avail": sa, "files": f, "uploaded": s * p * random.uniform(0.05, 0.3)})
                             for n, k, s, p, stt, sa, f in TORRENTS]
        self.total_down = float(st.get("total_down", 0))
        self.total_up = float(st.get("total_up", 0))
        self.online = False
        self.history = deque([(0.0, 0.0)] * 120, maxlen=120)
        self.rnd = random.Random()
        self.line_speed = DIALUP
        self.ticks = 0
        self.timer = QTimer(self, interval=1000, timeout=self.tick)
        self.timer.start()
        self.tick()

    def save(self):
        st = load_json(STATE_FILE, {})
        st.update(torrents=[t.to_dict() for t in self.torrents], total_down=round(self.total_down),
                  total_up=round(self.total_up))
        save_json(STATE_FILE, st)

    def tick(self):
        now = time.monotonic()
        self.ticks += 1
        online = network.is_connected()
        if online != self.online:
            self.online = online
            for t in self.torrents:
                if t.running and t.status != "checking":
                    t.status = "connecting" if online else "waiting"
                    t.connect_until = now + self.rnd.uniform(2.5, 6)
                    t.peer_list = []
        # the line wanders: a good minute, a bad minute
        self.line_speed = max(1.2 * KB, min(5.4 * KB, self.line_speed + self.rnd.uniform(-0.5, 0.5) * KB))
        active = []
        for t in self.torrents:
            t.down = t.up = 0.0
            if t.status == "checking":
                if now >= t.check_until:
                    t.status = "connecting" if online else "waiting"
                    t.connect_until = now + 3
                continue
            if not t.running:
                t.seeds = t.peers = 0
                t.peer_list = []
                continue
            if not online:
                t.status = "waiting"
                t.seeds = t.peers = 0
                continue
            if t.status == "connecting" and now < t.connect_until:
                continue
            if self.rnd.random() < 0.004:                               # seeds come and go
                t.seeds_avail = max(0, t.seeds_avail + self.rnd.choice([-1, 1]))
            t.status = "downloading" if t.seeds_avail > 0 else "stalled"
            active.append(t)
        share = len([t for t in active if t.status == "downloading"]) or 1
        uploaders = len([t for t in active if t.peer_list]) or 1         # a modem only sends ~1-2 kB/s in all
        for t in active:
            self._swarm(t)
            if t.status == "downloading":
                t.down = max(0.0, self.line_speed / share * self.rnd.uniform(0.6, 1.25))
                t.done += t.down
                if t.done >= t.size:                                    # never really finishes: check, start over
                    t.done = 0.0
                    t.status = "checking"
                    t.check_until = now + 8
            t.up = self.rnd.uniform(0.6, 2.2) * KB / uploaders if t.peer_list else 0.0
            t.uploaded += t.up
            for key, total in (("down", t.down), ("up", t.up)):       # the peers' share adds up to the torrent's
                got = sum(peer[key] for peer in t.peer_list)
                for peer in t.peer_list:
                    peer[key] = peer[key] / got * total if got else 0.0
        down, up = sum(t.down for t in self.torrents), sum(t.up for t in self.torrents)
        self.total_down += down
        self.total_up += up
        self.history.append((down, up))
        if self.ticks % 30 == 0:
            self.save()
        self.updated.emit()

    def _swarm(self, t):
        """The peers list drifts: people join, leave, and trickle data."""
        want_seeds = t.seeds_avail
        want_peers = max(1, int(t.seeds_avail * 2.5) + 3)
        while len(t.peer_list) < want_seeds + want_peers and self.rnd.random() < 0.5:
            seed = len([p for p in t.peer_list if p["have"] >= 1]) < want_seeds
            t.peer_list.append({"ip": f"{self.rnd.choice([24, 64, 66, 152, 205, 207, 209, 216])}."
                                      f"{self.rnd.randint(1, 254)}.{self.rnd.randint(1, 254)}.{self.rnd.randint(1, 254)}",
                                "client": self.rnd.choice(CLIENTS), "have": 1.0 if seed else self.rnd.random() * 0.9,
                                "down": 0.0, "up": 0.0})
        if t.peer_list and self.rnd.random() < 0.06:
            t.peer_list.pop(self.rnd.randrange(len(t.peer_list)))
        for peer in t.peer_list:
            peer["down"] = self.rnd.uniform(0, 1.8) * KB if peer["have"] > t.progress else 0.0
            peer["up"] = self.rnd.uniform(0, 0.6) * KB if self.rnd.random() < 0.4 else 0.0
            if peer["have"] < 1:
                peer["have"] = min(1.0, peer["have"] + self.rnd.uniform(0, 0.0004))
        t.seeds = len([p for p in t.peer_list if p["have"] >= 1])
        t.peers = len(t.peer_list) - t.seeds

    # ---- control --------------------------------------------------------------------------------------------
    def start(self, t):
        if not t.running:
            t.status = "connecting" if self.online else "waiting"
            t.connect_until = time.monotonic() + self.rnd.uniform(2, 5)
            self.save()
            self.updated.emit()

    def stop(self, t):
        if t.running:
            t.status = "stopped"
            t.peer_list = []
            t.down = t.up = 0.0
            self.save()
            self.updated.emit()

    def start_all(self):
        for t in self.torrents:
            self.start(t)

    def stop_all(self):
        for t in self.torrents:
            self.stop(t)

    def rates(self):
        return sum(t.down for t in self.torrents), sum(t.up for t in self.torrents)


# ---- the window ---------------------------------------------------------------------------------------------------

COLS = ["Name", "Size", "Done", "Status", "Seeds", "Peers", "Down Speed", "Up Speed", "ETA", "Uploaded"]


class ProgressDelegate(QStyledItemDelegate):
    def paint(self, p, option, index):
        frac = index.data(Qt.UserRole) or 0.0
        r = QRectF(option.rect).adjusted(2, 3, -2, -3)
        p.save()
        p.fillRect(r, QColor("white"))
        p.setPen(QPen(QColor("#8A98AC"), 1))
        p.drawRect(r.adjusted(0.5, 0.5, -0.5, -0.5))
        g = QLinearGradient(0, r.top(), 0, r.bottom())
        g.setColorAt(0, QColor("#9FE08A"))
        g.setColorAt(1, QColor("#3AA028"))
        p.fillRect(QRectF(r.left() + 1, r.top() + 1, (r.width() - 2) * frac, r.height() - 2), g)
        p.setPen(QColor("black"))
        p.setFont(QFont("Tahoma", 7))
        p.drawText(r, Qt.AlignCenter, f"{frac * 100:.1f}%")
        p.restore()


class PiecesBar(QWidget):
    def __init__(self):
        super().__init__()
        self.torrent = None
        self.setFixedHeight(18)

    def paintEvent(self, event):
        p = QPainter(self)
        r = self.rect().adjusted(0, 0, -1, -1)
        p.fillRect(r, QColor("white"))
        if self.torrent is not None:
            cols = max(1, r.width() - 2)
            for x, f in enumerate(self.torrent.have_map(cols)):
                if f > 0:
                    c = QColor("#2E6AD0")
                    c.setAlphaF(min(1.0, 0.25 + f))
                    p.fillRect(QRect(r.left() + 1 + x, r.top() + 1, 1, r.height() - 1), c)
        p.setPen(QColor("#7F9DB9"))
        p.drawRect(r)


class SpeedGraph(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(40, 8, -8, -18)
        p.fillRect(self.rect(), QColor("black"))
        hist = list(self.engine.history)
        top = max(6 * KB, max(max(d, u) for d, u in hist) * 1.15)
        p.setPen(QPen(QColor("#1E3A1E"), 1))
        for k in range(5):
            y = r.top() + r.height() * k / 4
            p.drawLine(QPointF(r.left(), y), QPointF(r.right(), y))
            p.setPen(QColor("#6A8A6A"))
            p.setFont(QFont("Tahoma", 7))
            p.drawText(QRectF(0, y - 6, 36, 12), Qt.AlignRight | Qt.AlignVCenter, f"{top * (1 - k / 4) / KB:.1f}")
            p.setPen(QPen(QColor("#1E3A1E"), 1))
        for idx, col in ((0, "#40E040"), (1, "#E05040")):
            path = QPainterPath()
            for i, pair in enumerate(hist):
                x = r.left() + r.width() * i / (len(hist) - 1)
                y = r.bottom() - r.height() * pair[idx] / top
                (path.moveTo if i == 0 else path.lineTo)(x, y)
            p.setPen(QPen(QColor(col), 1.5))
            p.drawPath(path)
        p.setPen(QColor("#A0C0A0"))
        p.drawText(QRectF(r.left(), r.bottom() + 2, r.width(), 14), Qt.AlignLeft,
                   "kB/s  -  last 2 minutes   (green: download, red: upload)")


class TorrentWindow(QWidget):
    def __init__(self, desktop, engine):
        super().__init__()
        self.desktop = desktop
        self.engine = engine
        self.frame = None
        self._exiting = False
        self.setObjectName("bt")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(MENU_STYLE + "QWidget#bt { background: #ECE9D8; }"
                           "QTreeWidget { background: white; font: 11px Tahoma; }"
                           "QToolButton { font: 11px Tahoma; padding: 3px 6px; border: 1px solid transparent;"
                           " border-radius: 3px; } QToolButton:hover { border-color: #C0BCA8; background: white; }"
                           "QToolButton:disabled { color: #A0A0A0; } QLabel { font: 11px Tahoma; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.menu = QMenuBar()
        self.menu.triggered.connect(lambda _a: sound.play("menu"))
        lay.addWidget(self.menu)
        lay.addWidget(self._toolbar())
        split = QSplitter(Qt.Vertical)
        self.list = QTreeWidget()
        self.list.setHeaderLabels(COLS)
        self.list.setRootIsDecorated(False)
        self.list.setUniformRowHeights(True)
        self.list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list.setItemDelegateForColumn(2, ProgressDelegate(self.list))
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._context)
        h = self.list.header()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        for col, w in ((1, 66), (2, 86), (3, 128), (4, 44), (5, 44), (6, 70), (7, 64), (8, 60), (9, 66)):
            self.list.setColumnWidth(col, w)
        for t in engine.torrents:
            item = QTreeWidgetItem([t.name])
            item.setData(0, Qt.UserRole, t)
            self.list.addTopLevelItem(item)
        self.list.setCurrentItem(self.list.topLevelItem(0))
        split.addWidget(self.list)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { font: 11px Tahoma; padding: 3px 10px; }")
        self.tabs.addTab(self._general(), "General")
        self.files = QTreeWidget()
        self.files.setHeaderLabels(["File", "Size", "Done"])
        self.files.setRootIsDecorated(False)
        self.files.setItemDelegateForColumn(2, ProgressDelegate(self.files))
        self.files.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.files.setColumnWidth(1, 80)
        self.files.setColumnWidth(2, 90)
        self.tabs.addTab(self.files, "Files")
        self.peers = QTreeWidget()
        self.peers.setHeaderLabels(["IP", "Client", "Have", "Down Speed", "Up Speed"])
        self.peers.setRootIsDecorated(False)
        self.peers.setItemDelegateForColumn(2, ProgressDelegate(self.peers))
        self.peers.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabs.addTab(self.peers, "Peers")
        self.graph = SpeedGraph(engine)
        self.tabs.addTab(self.graph, "Speed")
        split.addWidget(self.tabs)
        split.setSizes([220, 200])
        lay.addWidget(split, 1)
        self.status = QLabel()
        self.status.setStyleSheet("padding: 2px 6px; border-top: 1px solid #A0A0A0;")
        lay.addWidget(self.status)
        self._menus()
        self.list.currentItemChanged.connect(lambda *_: self.refresh(full=True))
        self.list.itemSelectionChanged.connect(self._update_buttons)
        self.tabs.currentChanged.connect(lambda *_: self.refresh(full=True))
        engine.updated.connect(self.refresh)
        self.refresh(full=True)

    # ---- layout pieces -------------------------------------------------------------------------------------
    def _toolbar(self):
        bar = QWidget()
        bar.setObjectName("tb")
        bar.setAttribute(Qt.WA_StyledBackground, True)
        bar.setStyleSheet("QWidget#tb { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FDFDFB,"
                          " stop:1 #E3E0D2); border-bottom: 1px solid #A0A0A0; }")
        row = QHBoxLayout(bar)
        row.setContentsMargins(4, 2, 4, 2)
        row.setSpacing(2)
        self.buttons = {}
        for key, text, fn in (("start", "Start", self.start_selected), ("stop", "Stop", self.stop_selected),
                              (None, None, None), ("start_all", "Start All", self.engine.start_all),
                              ("stop_all", "Stop All", self.engine.stop_all), (None, None, None),
                              ("prefs", "Preferences", self.preferences)):
            if key is None:
                row.addSpacing(10)
                continue
            b = QToolButton()
            b.setText(text)
            b.setIcon(QIcon(self._tool_icon(key)))
            b.setIconSize(QSize(20, 20))
            b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            b.clicked.connect(fn)
            row.addWidget(b)
            self.buttons[key] = b
        row.addStretch()
        return bar

    @staticmethod
    def _tool_icon(kind):
        pm = QPixmap(20, 20)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        green, red = QColor("#2EA02E"), QColor("#C83020")
        if kind in ("start", "start_all"):
            p.setBrush(green)
            p.setPen(QPen(green.darker(150), 1))
            p.drawPolygon(QPolygonF([QPointF(5, 3), QPointF(17, 10), QPointF(5, 17)]))
            if kind == "start_all":
                p.drawPolygon(QPolygonF([QPointF(1, 5), QPointF(9, 10), QPointF(1, 15)]))
        elif kind in ("stop", "stop_all"):
            p.setBrush(red)
            p.setPen(QPen(red.darker(150), 1))
            p.drawRoundedRect(QRectF(4, 4, 12, 12), 2, 2)
            if kind == "stop_all":
                p.drawRoundedRect(QRectF(1, 1, 8, 8), 2, 2)
        else:
            p.setPen(QPen(QColor("#505868"), 2.2))
            p.setBrush(QColor("#C0C8D8"))
            p.drawEllipse(QPointF(10, 10), 5.5, 5.5)
            for k in range(8):
                a = k * math.pi / 4
                p.drawLine(QPointF(10 + math.cos(a) * 6, 10 + math.sin(a) * 6),
                           QPointF(10 + math.cos(a) * 8.5, 10 + math.sin(a) * 8.5))
            p.setBrush(QColor("white"))
            p.drawEllipse(QPointF(10, 10), 2, 2)
        p.end()
        return pm

    def _general(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(8, 6, 8, 6)
        v.addWidget(QLabel("Pieces:"))
        self.bar = PiecesBar()
        v.addWidget(self.bar)
        self.info = QLabel()
        self.info.setTextFormat(Qt.RichText)
        self.info.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        v.addWidget(self.info, 1)
        return page

    def _menus(self):
        m = self.menu
        f = m.addMenu("&File")
        f.addAction("&Close to Tray", lambda: self.frame.request_close(), QKeySequence("Ctrl+W"))
        f.addAction("E&xit ClaudeTorrent", lambda: shutdown(), QKeySequence("Ctrl+Q"))
        t = m.addMenu("&Torrent")
        self.start_act = t.addAction("&Start", self.start_selected)
        self.stop_act = t.addAction("S&top", self.stop_selected)
        t.addSeparator()
        t.addAction("Start &All", self.engine.start_all)
        t.addAction("Stop A&ll", self.engine.stop_all)
        o = m.addMenu("&Options")
        o.addAction("&Preferences...", self.preferences, QKeySequence("Ctrl+P"))
        m.addMenu("&Help").addAction(f"&About {TITLE}...", self.about)

    # ---- actions -----------------------------------------------------------------------------------------------
    def selected(self):
        return [i.data(0, Qt.UserRole) for i in self.list.selectedItems()]

    def start_selected(self):
        for t in self.selected():
            self.engine.start(t)

    def stop_selected(self):
        for t in self.selected():
            self.engine.stop(t)

    def _update_buttons(self):
        sel = self.selected()
        can_start = any(not t.running for t in sel)
        can_stop = any(t.running for t in sel)
        self.buttons["start"].setEnabled(can_start)
        self.buttons["stop"].setEnabled(can_stop)
        self.start_act.setEnabled(can_start)
        self.stop_act.setEnabled(can_stop)

    def _context(self, pos):
        m = QMenu(self)
        m.setStyleSheet(MENU_STYLE)
        sel = self.selected()
        m.addAction("&Start", self.start_selected).setEnabled(any(not t.running for t in sel))
        m.addAction("S&top", self.stop_selected).setEnabled(any(t.running for t in sel))
        m.addSeparator()
        m.addAction("Start &All", self.engine.start_all)
        m.addAction("Stop A&ll", self.engine.stop_all)
        m.exec(self.list.viewport().mapToGlobal(pos))

    def preferences(self):
        preferences(self.desktop)

    def about(self):
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, f"About {TITLE}", f"{TITLE}\n\nA BitTorrent client for Windows XP.\nBased on the "
               "BitTorrent protocol by Bram Cohen (2001).\n\nThis is beta software: expect bugs!", "info")

    # ---- showing it ---------------------------------------------------------------------------------------------
    def refresh(self, full=False):
        eng = self.engine
        for i in range(self.list.topLevelItemCount()):
            item = self.list.topLevelItem(i)
            t = item.data(0, Qt.UserRole)
            eta = (t.size - t.done) / t.down if t.down > 0 else None
            vals = [t.name, fmt_size(t.size), "", STATUS_TEXT.get(t.status, t.status),
                    f"{t.seeds} ({t.seeds_avail})" if t.running else "", str(t.peers) if t.running else "",
                    fmt_rate(t.down), fmt_rate(t.up), fmt_eta(eta) if t.status == "downloading" else "",
                    fmt_size(t.uploaded)]
            for col, v in enumerate(vals):
                if item.text(col) != v:
                    item.setText(col, v)
            item.setData(2, Qt.UserRole, t.progress)
            color = {"downloading": "#106010", "stalled": "#A06000", "waiting": "#606060",
                     "connecting": "#1A4AB0", "checking": "#1A4AB0"}.get(t.status, "#000000")
            item.setForeground(3, QColor(color))
        self.list.viewport().update()
        cur = self.list.currentItem()
        t = cur.data(0, Qt.UserRole) if cur else None
        tab = self.tabs.currentIndex()
        if t is not None and tab == 0:
            self.bar.torrent = t
            self.bar.update()
            have = int(t.progress * t.pieces)
            ratio = t.uploaded / t.done if t.done else 0
            self.info.setText(
                "<table cellspacing=3>"
                f"<tr><td><b>Name:</b></td><td>{t.name}</td></tr>"
                f"<tr><td><b>Type:</b></td><td>{t.kind}</td></tr>"
                f"<tr><td><b>Size:</b></td><td>{fmt_size(t.size)}  ({t.pieces:,} pieces of {fmt_size(t.piece)})"
                f"</td></tr><tr><td><b>Have:</b></td><td>{have:,} pieces - {fmt_size(t.done)}  "
                f"({t.progress * 100:.2f}%)</td></tr>"
                f"<tr><td><b>Uploaded:</b></td><td>{fmt_size(t.uploaded)}  (share ratio {ratio:.3f})</td></tr>"
                f"<tr><td><b>Tracker:</b></td><td>{TRACKER}</td></tr>"
                f"<tr><td><b>Info hash:</b></td><td>{t.hash}</td></tr>"
                f"<tr><td><b>Added:</b></td><td>{t.added}</td></tr></table>")
        elif t is not None and tab == 1:
            if full or self.files.topLevelItemCount() != len(t.files):
                self.files.clear()
                for name, share in t.files:
                    self.files.addTopLevelItem(QTreeWidgetItem([name, fmt_size(t.size * share), ""]))
            # files fill in order of the pieces they hold: spread progress evenly with some jitter
            rnd = random.Random(t.hash)
            for i, (name, share) in enumerate(t.files):
                jitter = rnd.uniform(-0.15, 0.15)
                frac = max(0.0, min(1.0, t.progress + jitter * (1 - t.progress) * t.progress * 4))
                self.files.topLevelItem(i).setData(2, Qt.UserRole, frac)
            self.files.viewport().update()
        elif t is not None and tab == 2:
            self.peers.clear()
            for peer in t.peer_list:
                item = QTreeWidgetItem([peer["ip"], peer["client"], "", fmt_rate(peer["down"]), fmt_rate(peer["up"])])
                item.setData(2, Qt.UserRole, peer["have"])
                self.peers.addTopLevelItem(item)
        elif tab == 3:
            self.graph.update()
        down, up = eng.rates()
        running = len([x for x in eng.torrents if x.status == "downloading"])
        net = "Connected" if eng.online else "Offline - waiting for an Internet connection"
        self.status.setText(f"{net}     D: {down / KB:.1f} kB/s     U: {up / KB:.1f} kB/s     "
                            f"{running} of {len(eng.torrents)} downloading     "
                            f"Total: {fmt_size(eng.total_down)} down, {fmt_size(eng.total_up)} up")
        if full:
            self._update_buttons()

    def closeEvent(self, event):
        """X tucks ClaudeTorrent into the tray; File > Exit really quits."""
        if not self._exiting:
            self.desktop.withdraw(self.frame)
            event.ignore()
            tucked_away()
            return
        event.accept()


# ---- preferences --------------------------------------------------------------------------------------------------

def load_at_startup():
    return bool(load_json(STATE_FILE, {}).get("startup", True))


def set_load_at_startup(on):
    st = load_json(STATE_FILE, {})
    st["startup"] = bool(on)
    save_json(STATE_FILE, st)
    if _tray is not None and isValid(_tray) and _tray.contextMenu() is not None:
        for action in _tray.contextMenu().actions():
            if action.isCheckable():
                action.setChecked(bool(on))


def preferences(desktop):
    from ..network import DialogBody, _fixed_window
    body = DialogBody()
    v = QVBoxLayout(body)
    v.setContentsMargins(14, 12, 14, 12)
    head = QLabel("<b>General</b>")
    v.addWidget(head)
    startup = QCheckBox("&Load ClaudeTorrent when Windows starts")
    startup.setChecked(load_at_startup())
    v.addWidget(startup)
    v.addWidget(QLabel("Closing the window keeps ClaudeTorrent running in the notification area.\n"
                       "To quit completely, use File > Exit or right-click the tray icon."))
    v.addSpacing(6)
    v.addWidget(QLabel("<b>Connection</b>"))
    v.addWidget(QLabel("Listening port: 6881     Connection type: Modem (56k)"))
    row = QHBoxLayout()
    row.addStretch()
    ok, cancel = QPushButton("OK"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(75, 23)
        row.addWidget(b)
    v.addLayout(row)
    body.setFixedWidth(380)
    holder = {}

    def close():
        w = holder.pop("win", None)
        if w is not None and isValid(w):
            desktop.close_window(w)
    ok.clicked.connect(lambda: (set_load_at_startup(startup.isChecked()), close()))
    cancel.clicked.connect(close)
    win = _fixed_window(desktop, "ClaudeTorrent Preferences", body, close)
    win.icon = torrent_icon()
    holder["win"] = win
    desktop.open_window(win)


# ---- running it: the engine, the tray, the window -----------------------------------------------------------------

_engine = None
_tray = None
_frame = None


def engine(desktop):
    global _engine
    if _engine is None or not isValid(_engine):
        _engine = Engine(desktop)
        _engine.updated.connect(_update_tray)
    return _engine


def ensure_tray(desktop):
    global _tray
    engine(desktop)
    if _tray is not None and isValid(_tray) and _tray.desktop is desktop:
        return _tray
    from ..tray import TrayIcon
    _tray = TrayIcon(desktop, tray_icon(False, False, True))
    _tray.setToolTip(TITLE)
    menu = QMenu()
    menu.setStyleSheet(MENU_STYLE)
    open_action = menu.addAction("&Open ClaudeTorrent", lambda: open_torrent(desktop))
    f = open_action.font()
    f.setBold(True)
    open_action.setFont(f)
    menu.addSeparator()
    menu.addAction("Start &All", lambda: engine(desktop).start_all())
    menu.addAction("Stop A&ll", lambda: engine(desktop).stop_all())
    menu.addSeparator()
    startup = menu.addAction("&Load at Startup")
    startup.setCheckable(True)
    startup.setChecked(load_at_startup())
    startup.toggled.connect(set_load_at_startup)
    menu.addSeparator()
    menu.addAction("E&xit", shutdown)
    _tray.setContextMenu(menu)
    _tray._menu_keepalive = menu
    _tray.activated.connect(lambda reason: open_torrent(desktop)
                            if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger) else None)
    _tray.show()
    _update_tray()
    return _tray


def _update_tray():
    if _tray is None or not isValid(_tray) or _engine is None:
        return
    down, up = _engine.rates()
    blink = _engine.ticks % 2 == 0
    key = (down > 0 and blink, up > 0 and not blink, not _engine.online)
    if getattr(_tray, "_state", None) != key:
        _tray._state = key
        _tray.setIcon(tray_icon(*key))
    n = len([t for t in _engine.torrents if t.status == "downloading"])
    _tray.setToolTip(f"{TITLE}\nDown: {down / KB:.1f} kB/s   Up: {up / KB:.1f} kB/s\n"
                     + (f"{n} of {len(_engine.torrents)} torrents downloading" if _engine.online
                        else "Waiting for an Internet connection"))


def tucked_away():
    st = load_json(STATE_FILE, {})
    if _tray is not None and isValid(_tray) and not st.get("tray_tip_shown"):
        st["tray_tip_shown"] = True
        save_json(STATE_FILE, st)

        def tip():
            if _tray is not None and isValid(_tray):         # (logged off or exited in the meantime: no tray)
                _tray.showMessage("ClaudeTorrent is still running", "Your torrents keep downloading in the "
                                  "background. Double-click the arrows to open ClaudeTorrent, or right-click them "
                                  "and choose Exit to quit.")
        QTimer.singleShot(300, tip)


def start_at_logon(desktop):
    if load_at_startup():
        ensure_tray(desktop)


def open_torrent(desktop):
    global _frame
    ensure_tray(desktop)
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        return _frame
    body = TorrentWindow(desktop, engine(desktop))
    _frame = XPWindow(desktop, TITLE, body, torrent_icon(), (820, 560))
    body.frame = _frame
    desktop.open_window(_frame)
    return _frame


def shutdown():
    """Exit: save, close the window, leave the tray."""
    global _tray, _frame, _engine
    if _engine is not None and isValid(_engine):
        _engine.save()
        _engine.timer.stop()
        _engine.deleteLater()
    _engine = None
    if _frame is not None and isValid(_frame):
        _frame.content._exiting = True
        _frame.desktop.close_window(_frame)
    _frame = None
    if _tray is not None and isValid(_tray):
        _tray.hide()
        _tray.deleteLater()
    _tray = None
