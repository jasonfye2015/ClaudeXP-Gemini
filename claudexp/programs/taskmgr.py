"""Windows Task Manager: Applications (End Task, Switch To, New Task), Processes (End Process; ending
explorer.exe takes the taskbar and desktop icons away until you run 'explorer' again), Performance (CPU and
page-file graphs; the CPU really climbs while the model is thinking, filed under svchost.exe like a Windows
Update) and Networking (the dial-up adapter)."""
import random
from collections import deque

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
                               QMenuBar, QPushButton, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
                               QWidget)
from shiboken6 import isValid

from .. import broker, network, sound
from ..wm import XPWindow
from .notepad import MENU_STYLE

STYLE = MENU_STYLE + """
QWidget#taskmgr { background: #ECE9D8; }
QWidget, QLabel, QPushButton, QTabBar::tab, QGroupBox { font-family: Tahoma; font-size: 11px; }
QTreeWidget { background: white; border: 1px solid #7F9DB9; }
QLabel#status { border-top: 1px solid #ACA899; padding: 2px 6px; }
"""
CRITICAL = {"System", "smss.exe", "csrss.exe", "winlogon.exe", "services.exe", "lsass.exe"}
# (image, user, memory K) of what's always running
SYSTEM = [("System Idle Process", "SYSTEM", 16), ("System", "SYSTEM", 216), ("smss.exe", "SYSTEM", 388),
          ("csrss.exe", "SYSTEM", 3420), ("winlogon.exe", "SYSTEM", 4872), ("services.exe", "SYSTEM", 3164),
          ("lsass.exe", "SYSTEM", 1196), ("svchost.exe", "SYSTEM", 4608), ("svchost.exe", "NETWORK SERVICE", 2972),
          ("svchost.exe", "SYSTEM", 17240), ("svchost.exe", "LOCAL SERVICE", 3540), ("spoolsv.exe", "SYSTEM", 4316),
          ("explorer.exe", None, 18432), ("ctfmon.exe", None, 2884), ("shieldtray.exe", None, 3972)]
# window content module -> process image
MODULE_IMAGES = [("taipei", "taipei.exe"), ("rodent", "rodent.exe"), ("blockfall", "blockfall.exe"),
                 ("peaks", "tripeaks.exe"), ("skifree", "ski.exe"), ("jezzball", "jezzball.exe"), ("programs.nes.", "fceu.exe"), ("programs.tv.", "claudetv.exe"), ("programs.comix.", "furcomix.exe"), ("programs.folio.stories", "furstory.exe"), ("programs.folio.furcon", "furcon.exe"), ("programs.folio.videos", "furvideo.exe"), ("programs.flash", "flashpla.exe"), ("programs.amp", "claudeamp.exe"), ("programs.stylexp", "stylexp.exe"), ("programs.torrent", "claudetorrent.exe"), ("programs.furdir", "furdir.exe"), ("programs.rpg", "clauderpg.exe"), ("programs.folio.cdviewer", "furcd.exe"), ("programs.folio.", "furfolio.exe"), ("helpctr", "helpctr.exe"), ("tour", "tourstart.exe"),
                 ("sysrestore", "rstrui.exe"), ("charmap", "charmap.exe"), ("msinfo", "msinfo32.exe"), ("sndrec", "sndrec32.exe"),
                 ("pinball", "pinball.exe"), ("ibackgammon", "bckgzm.exe"), ("ihearts", "hrtzzm.exe"), ("ispades", "shvlzm.exe"),
                 ("icheckers", "chkrzm.exe"), ("ireversi", "rvsezm.exe"), ("zone", "zclientm.exe"),
                 ("wmp", "wmplayer.exe"), ("wordpad", "wordpad.exe"), ("outlook", "msimn.exe"),
                 ("paint", "mspaint.exe"), ("notepad", "notepad.exe"), ("calc", "calc.exe"), (".cmd", "cmd.exe"),
                 ("taskmgr", "taskmgr.exe"), ("freecell", "freecell.exe"), ("solitaire", "sol.exe"), ("spider", "spider.exe"),
                 ("minesweeper", "winmine.exe"), ("hearts", "mshearts.exe"), ("navigator", "netscape.exe"),
                 ("claudeai", "claudeai.exe"), ("claudeaim", "aim.exe"), ("irc", "mirc32.exe"),
                 ("muck", "claudemuck.exe"), ("defrag", "dfrgntfs.exe"), ("antivirus", "claudeshield.exe"),
                 ("updates", "wuauclt.exe"), ("printing", "spoolsv.exe")]
MEM = {"taipei.exe": 3640, "rodent.exe": 2980, "blockfall.exe": 2760, "tripeaks.exe": 3320, "ski.exe": 2840, "jezzball.exe": 3120, "fceu.exe": 24310, "snes9x.exe": 31840, "gambatte.exe": 14120, "gambatte_gbc.exe": 14160,
       "mgba.exe": 28870, "picodrive.exe": 26450, "gpgx.exe": 29980, "gearsystem.exe": 16240, "applewin.exe": 22760, "mupen64plus.exe": 61840,
       "doom.exe": 19120, "doom2.exe": 19840, "wolf3d.exe": 18760, "heretic.exe": 24800, "hexen.exe": 27300, "claudetv.exe": 21480, "furcomix.exe": 16920, "furfolio.exe": 14880, "furstory.exe": 9640, "furcd.exe": 18300, "furcon.exe": 17460, "furvideo.exe": 18120, "flashpla.exe": 13560, "claudeamp.exe": 7240, "stylexp.exe": 6480, "claudetorrent.exe": 11320, "furdir.exe": 8460, "clauderpg.exe": 64820, "helpctr.exe": 12400, "tourstart.exe": 9800, "rstrui.exe": 6100, "charmap.exe": 3360, "msinfo32.exe": 7720, "sndrec32.exe": 3410, "pinball.exe": 11260, "msimn.exe": 9140, "wordpad.exe": 5480, "bckgzm.exe": 7900, "hrtzzm.exe": 8120, "shvlzm.exe": 8040,
       "chkrzm.exe": 7420, "rvsezm.exe": 7064, "zclientm.exe": 6900, "wmplayer.exe": 18260, "mspaint.exe": 6840,
       "notepad.exe": 2964, "calc.exe": 3108, "cmd.exe": 1468, "taskmgr.exe": 4072, "freecell.exe": 3256,
       "sol.exe": 3920, "spider.exe": 4484, "winmine.exe": 2440, "mshearts.exe": 3672, "netscape.exe": 21336,
       "claudeai.exe": 15872, "aim.exe": 9840, "mirc32.exe": 6212, "claudemuck.exe": 5532, "dfrgntfs.exe": 4908,
       "claudeshield.exe": 8820, "wuauclt.exe": 5216, "waol.exe": 14204}

_open = {}


def taskmgr_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#404040"), 1))
    p.setBrush(QColor("#D8D4C4"))
    p.drawRoundedRect(QRectF(3.5, 4.5, 25, 19), 2, 2)
    p.fillRect(QRectF(6, 7, 20, 14), QColor("black"))
    p.setPen(QPen(QColor("#00FF00"), 1.5))
    pts = [(6, 18), (10, 15), (13, 17), (17, 10), (20, 13), (25, 9)]
    for a, b in zip(pts, pts[1:]):
        p.drawLine(*a, *b)
    p.setPen(QPen(QColor("#404040"), 1))
    p.setBrush(QColor("#B8B4A4"))
    p.drawRect(QRectF(11.5, 24.5, 9, 3))
    p.end()
    return QIcon(pm)


# ---- explorer.exe -----------------------------------------------------------------------------------------------

def explorer_running(desktop):
    return getattr(desktop, "explorer_running", True)


def end_explorer(desktop):
    """Like ending explorer.exe on XP: the taskbar and desktop icons vanish; windows stay."""
    desktop.explorer_running = False
    desktop.hide_start_menu()
    desktop.taskbar.hide()
    for icon in desktop.icons.icons:
        icon.hide()


def start_explorer(desktop):
    desktop.explorer_running = True
    desktop.taskbar.show()
    desktop.taskbar.raise_()
    desktop.icons.layout()


# ---- graphs -------------------------------------------------------------------------------------------------------

class Meter(QWidget):
    """The black box with the green LED bar and the percentage (or MB) under it."""

    def __init__(self, label_fn):
        super().__init__()
        self.value = 0.0
        self.label_fn = label_fn
        self.setMinimumSize(70, 90)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        w, h = self.width(), self.height()
        bar = QRectF(w / 2 - 16, 8, 32, h - 32)
        rows = int(bar.height() // 3)
        lit = round(rows * self.value)
        for i in range(rows):
            y = bar.bottom() - (i + 1) * 3
            on = i < lit
            p.fillRect(QRectF(bar.left(), y, 15, 2), QColor("#00FF00") if on else QColor("#008000"))
            p.fillRect(QRectF(bar.left() + 17, y, 15, 2), QColor("#00FF00") if on else QColor("#008000"))
        p.setPen(QColor("#00FF00"))
        f = QFont("Tahoma")
        f.setPixelSize(11)
        p.setFont(f)
        p.drawText(QRectF(0, h - 20, w, 16), Qt.AlignCenter, self.label_fn(self.value))


class History(QWidget):
    """The scrolling green grid graph."""

    def __init__(self, color="#00FF00", points=60):
        super().__init__()
        self.values = deque([0.0] * points, maxlen=points)
        self.color = QColor(color)
        self.offset = 0
        self.setMinimumSize(160, 90)

    def push(self, value):
        self.values.append(max(0.0, min(1.0, value)))
        self.offset = (self.offset + 2) % 12
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        w, h = self.width(), self.height()
        p.setPen(QPen(QColor("#008040"), 1))
        x = w - self.offset
        while x > 0:
            p.drawLine(int(x), 0, int(x), h)
            x -= 12
        for y in range(0, h, 12):
            p.drawLine(0, y, w, y)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(self.color, 1.5))
        n = len(self.values)
        step = w / max(1, n - 1)
        pts = [(i * step, h - 2 - v * (h - 4)) for i, v in enumerate(self.values)]
        for a, b in zip(pts, pts[1:]):
            p.drawLine(int(a[0]), int(a[1]), int(b[0]), int(b[1]))


def _box(title, widget):
    g = QGroupBox(title)
    lay = QVBoxLayout(g)
    lay.setContentsMargins(6, 6, 6, 6)
    lay.addWidget(widget)
    return g


# ---- the window ----------------------------------------------------------------------------------------------------

class TaskManager(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.ended = set()          # (image, user) system processes ended this session
        self.cpu = 0.0
        self.last_net = None
        self.setObjectName("taskmgr")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        bar = QMenuBar()
        bar.triggered.connect(lambda _a: sound.play("menu"))
        file_menu = bar.addMenu("&File")
        file_menu.addAction("&New Task (Run...)", self.new_task)
        file_menu.addSeparator()
        file_menu.addAction("E&xit Task Manager", lambda: self.frame.request_close())
        view = bar.addMenu("&View")
        view.addAction("&Refresh Now", self.refresh, "F5")
        shut = bar.addMenu("Sh&ut Down")
        shut.addAction("Turn &Off", desktop.turn_off)
        shut.addAction("&Restart", lambda: desktop.window().restart())
        shut.addAction("&Log Off " + self._user(), desktop.log_off)
        bar.addMenu("&Help").addAction("&About Task Manager", self.about)
        v.addWidget(bar)
        self.tabs = QTabWidget()
        body = QVBoxLayout()
        body.setContentsMargins(7, 7, 7, 7)
        body.addWidget(self.tabs)
        v.addLayout(body, 1)
        self.status = QLabel()
        self.status.setObjectName("status")
        v.addWidget(self.status)
        self._apps_tab()
        self._procs_tab()
        self._perf_tab()
        self._net_tab()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)
        self.tick()

    @staticmethod
    def _user():
        from .. import user
        return user.user_name()

    # ---- tabs ---------------------------------------------------------------------------------------------
    def _apps_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        self.apps = QTreeWidget()
        self.apps.setHeaderLabels(["Task", "Status"])
        self.apps.setRootIsDecorated(False)
        self.apps.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.apps.itemDoubleClicked.connect(lambda *_: self.switch_to())
        lay.addWidget(self.apps)
        row = QHBoxLayout()
        row.addStretch()
        for text, slot in (("&End Task", self.end_task), ("&Switch To", self.switch_to), ("&New Task...", self.new_task)):
            b = QPushButton(text)
            b.setFixedSize(80, 23)
            b.clicked.connect(slot)
            row.addWidget(b)
        lay.addLayout(row)
        self.tabs.addTab(w, "Applications")

    def _procs_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        self.procs = QTreeWidget()
        self.procs.setHeaderLabels(["Image Name", "User Name", "CPU", "Mem Usage"])
        self.procs.setRootIsDecorated(False)
        self.procs.setSortingEnabled(False)
        self.procs.setSelectionMode(QAbstractItemView.SingleSelection)
        for col, width in ((0, 130), (1, 100), (2, 40)):
            self.procs.setColumnWidth(col, width)
        lay.addWidget(self.procs)
        row = QHBoxLayout()
        row.addStretch()
        b = QPushButton("&End Process")
        b.setFixedSize(90, 23)
        b.clicked.connect(self.end_process)
        row.addWidget(b)
        lay.addLayout(row)
        self.tabs.addTab(w, "Processes")

    def _perf_tab(self):
        w = QWidget()
        grid = QGridLayout(w)
        self.cpu_meter = Meter(lambda v: f"{round(v * 100)} %")
        self.cpu_hist = History()
        self.pf_meter = Meter(lambda v: f"{round(v * 1249)} MB")
        self.pf_hist = History("#FFFF00")
        grid.addWidget(_box("CPU Usage", self.cpu_meter), 0, 0)
        grid.addWidget(_box("CPU Usage History", self.cpu_hist), 0, 1)
        grid.addWidget(_box("PF Usage", self.pf_meter), 1, 0)
        grid.addWidget(_box("Page File Usage History", self.pf_hist), 1, 1)
        grid.setColumnStretch(1, 1)
        self.totals = QLabel()
        self.physical = QLabel()
        grid.addWidget(_box("Totals", self.totals), 2, 0, 1, 1)
        grid.addWidget(_box("Physical Memory (K)", self.physical), 2, 1)
        self.tabs.addTab(w, "Performance")

    def _net_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        self.net_hist = History()
        self.net_box = _box("America Online (Dial-up)", self.net_hist)
        self.no_net = QLabel("No Active Network Adapters Found.")
        self.no_net.setAlignment(Qt.AlignCenter)
        self.net_label = QLabel()
        lay.addWidget(self.net_box, 1)
        lay.addWidget(self.no_net, 1)
        lay.addWidget(self.net_label)
        self.tabs.addTab(w, "Networking")

    # ---- what's running -------------------------------------------------------------------------------------
    def windows(self):
        return [win for win in self.desktop.windows if isValid(win) and win.on_taskbar]

    @staticmethod
    def image_for(win):
        content = win.content if isValid(win.content) else None
        if getattr(content, "process_image", None):
            return content.process_image
        # game windows wrap their play area; name the process after the game itself
        module = type(getattr(content, "play", content)).__module__ if content is not None else ""
        for key, image in MODULE_IMAGES:
            if key in module:
                return image
        return None

    def processes(self):
        """[(image, user, cpu %, mem K, window-or-None)]"""
        me = self._user()
        rows = [(img, user or me, 0, mem, None) for img, user, mem in SYSTEM
                if (img, user or me) not in self.ended and (img != "explorer.exe" or explorer_running(self.desktop))]
        seen = set()
        for win in self.windows():
            img = self.image_for(win)
            if img and img not in seen:
                seen.add(img)
                rows.append((img, me, 0, MEM.get(img, 4000) + random.randint(-40, 40) * 4, win))
        if network.is_connected():
            rows.append(("waol.exe", me, 0, MEM["waol.exe"], None))
        # CPU: the model thinking shows up as svchost.exe (netsvcs), like a Windows Update scan
        busy = broker.get().busy() if hasattr(broker, "get") else False
        target = random.uniform(0.62, 0.97) if busy else random.uniform(0.0, 0.06)
        self.cpu = self.cpu * 0.4 + target * 0.6
        total = round(self.cpu * 100)
        out = []
        spare = total
        for img, user, _, mem, win in rows:
            cpu = 0
            if img == "svchost.exe" and mem == 17240 and busy:
                cpu = max(0, total - 2)
            elif img == "taskmgr.exe" and total:
                cpu = min(2, total)
            spare -= cpu
            out.append([img, user, cpu, mem, win])
        if spare > 0 and not busy and len(out) > 12:
            out[random.choice([12, 13, -1])][2] += spare
        out[0][2] = max(0, 100 - total)
        return out

    def tick(self):
        if not isValid(self):
            return
        self.refresh()

    def refresh(self):
        # Applications
        selected = self.apps.currentItem().data(0, Qt.UserRole) if self.apps.currentItem() else None
        self.apps.clear()
        for win in self.windows():
            item = QTreeWidgetItem([win.title, "Running"])
            item.setIcon(0, win.icon)
            item.setData(0, Qt.UserRole, win)
            self.apps.addTopLevelItem(item)
            if win is selected:
                self.apps.setCurrentItem(item)
        # Processes
        procs = self.processes()
        cur = self.procs.currentItem()
        sel = (cur.text(0), cur.text(1)) if cur else None
        self.procs.clear()
        for img, user, cpu, mem, win in procs:
            item = QTreeWidgetItem([img, user, f"{cpu:02d}", f"{mem:,} K"])
            item.setData(0, Qt.UserRole, win)
            item.setTextAlignment(2, Qt.AlignRight)
            item.setTextAlignment(3, Qt.AlignRight)
            self.procs.addTopLevelItem(item)
            if sel == (img, user):
                self.procs.setCurrentItem(item)
        # Performance
        cpu = self.cpu
        commit = 118 + len(procs) * 3 + random.randint(0, 3)
        self.cpu_meter.value = cpu
        self.cpu_meter.update()
        self.cpu_hist.push(cpu)
        self.pf_meter.value = commit / 1249
        self.pf_meter.update()
        self.pf_hist.push(commit / 1249 * 2.5)
        threads = 280 + len(procs) * 9
        self.totals.setText(f"Handles\t{5400 + len(procs) * 120:,}\nThreads\t{threads}\nProcesses\t{len(procs)}")
        avail = 262000 - commit * 1024 // 2
        self.physical.setText(f"Total\t261,616\nAvailable\t{avail:,}\nSystem Cache\t{68000 + random.randint(0, 900):,}")
        # Networking
        connected = network.is_connected()
        self.net_box.setVisible(connected)
        self.no_net.setVisible(not connected)
        if connected:
            net = network.get(self.desktop)
            total_bytes = net.sent + net.received
            delta = 0 if self.last_net is None else max(0, total_bytes - self.last_net)
            self.last_net = total_bytes
            use = min(1.0, delta / 7000)
            self.net_hist.push(use)
            self.net_label.setText(f"Adapter Name: America Online    Network Utilization: {round(use * 100)} %    "
                                   f"Link Speed: 53.2 Kbps    State: Connected")
        else:
            self.last_net = None
            self.net_label.setText("")
        self.status.setText(f"Processes: {len(procs)}        CPU Usage: {round(cpu * 100)}%        "
                            f"Commit Charge: {commit}M / 1249M")

    # ---- actions ------------------------------------------------------------------------------------------
    def end_task(self):
        item = self.apps.currentItem()
        win = item.data(0, Qt.UserRole) if item else None
        if win is not None and isValid(win):
            win.request_close()
            QTimer.singleShot(300, self.refresh)

    def switch_to(self):
        item = self.apps.currentItem()
        win = item.data(0, Qt.UserRole) if item else None
        if win is not None and isValid(win):
            self.desktop.activate(win)

    def new_task(self):
        from .run import open_run
        open_run(self.desktop, title="Create New Task")

    def end_process(self):
        from ..explorer.dialogs import msgbox
        item = self.procs.currentItem()
        if item is None:
            return
        img, user, win = item.text(0), item.text(1), item.data(0, Qt.UserRole)
        if img == "System Idle Process":
            return msgbox(self.desktop, "Unable to Terminate Process",
                          "The operation could not be completed.\n\nThe operation is not valid for this process.", "error")
        if img in CRITICAL:
            return msgbox(self.desktop, "Unable to Terminate Process",
                          "This is a critical system process. Task Manager cannot end this process.", "error")

        def go(button):
            if button != "Yes":
                return
            if img == "explorer.exe":
                end_explorer(self.desktop)
            elif img == "taskmgr.exe":
                self.frame.request_close()
                return
            elif win is not None and isValid(win):
                for w in self.windows():
                    if self.image_for(w) == img:
                        self.desktop.close_window(w)
            elif img == "waol.exe":
                network.disconnect(quiet=True)
            else:
                self.ended.add((img, user))
            self.refresh()

        msgbox(self.desktop, "Task Manager Warning",
               "WARNING: Terminating a process can cause undesired results including loss of data and system "
               "instability. The process will not be given the chance to save its state or data before it is "
               "terminated. Are you sure you want to terminate the process?", "warning", ("Yes", "No"), go)

    def about(self):
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, "About Windows Task Manager", "Windows Task Manager\nVersion 5.1 (Build 2600)", "info")

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()


def open_taskmgr(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        desktop.activate(win)
        return win
    body = TaskManager(desktop)
    win = XPWindow(desktop, "Windows Task Manager", body, taskmgr_icon(), size=(430, 470))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    return win
