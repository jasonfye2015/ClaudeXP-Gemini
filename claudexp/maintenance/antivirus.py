"""ClaudeShield AntiVirus 2002: Auto-Protect in the tray, full system scans, LiveUpdate and Quarantine."""
import random
from datetime import timedelta

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QProgressBar, QPushButton, QStackedWidget,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import clock, network, sound
from ..paths import DATA, ROOT
from ..programs.people import load_json, save_json
from ..wm import XPWindow
from . import CoverClock

NAME = "ClaudeShield AntiVirus 2002"
STATE_FILE = DATA / "antivirus.json"
INFECTION_CHANCE = 0.08
VIRUSES = [
    ("W32.Nimda.A@mm", r"C:\Documents and Settings\{user}\Local Settings\Temporary Internet Files\Content.IE5\readme.eml"),
    ("W32.Sircam.Worm@mm", r"C:\Recycled\SirC32.exe"),
    ("W32.Badtrans.B@mm", r"C:\Documents and Settings\{user}\My Documents\Me_nude.MP3.scr"),
    ("W32.Nimda.E@mm", r"C:\WINDOWS\Temp\readme.exe"),
    ("VBS.LoveLetter.Var", r"C:\Documents and Settings\{user}\My Documents\LOVE-LETTER-FOR-YOU.TXT.vbs"),
]
SYSTEM_FILES = ["advapi32.dll", "comctl32.dll", "comdlg32.dll", "gdi32.dll", "kernel32.dll", "mshtml.dll",
                "msvcrt.dll", "ole32.dll", "oleaut32.dll", "rpcrt4.dll", "shell32.dll", "shlwapi.dll",
                "user32.dll", "wininet.dll", "winmm.dll", "ws2_32.dll", "ntdll.dll", "urlmon.dll",
                "explorer.exe", "svchost.exe", "winlogon.exe", "services.exe", "lsass.exe", "notepad.exe",
                "msiexec.exe", "wmplayer.exe", "dxdiag.exe", "mspaint.exe", "calc.exe", "sndrec32.exe"]


def shield_icon(size=16, ok=True):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 16
    path = QPainterPath()
    path.moveTo(8 * s, 0.6 * s)
    path.lineTo(14.6 * s, 2.8 * s)
    path.cubicTo(14.6 * s, 9.5 * s, 12 * s, 13.2 * s, 8 * s, 15.4 * s)
    path.cubicTo(4 * s, 13.2 * s, 1.4 * s, 9.5 * s, 1.4 * s, 2.8 * s)
    path.closeSubpath()
    g = QLinearGradient(0, 0, size, size)
    g.setColorAt(0, QColor("#4FA3FF" if ok else "#FF7A5A"))
    g.setColorAt(1, QColor("#0B3F99" if ok else "#A01800"))
    p.setPen(QPen(QColor("#0A2A66" if ok else "#600000"), max(1.0, s)))
    p.setBrush(g)
    p.drawPath(path)
    p.setPen(QPen(QColor("white"), 2 * s, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    if ok:
        p.drawPolyline([QPointF(4.5 * s, 8 * s), QPointF(7 * s, 10.6 * s), QPointF(11.5 * s, 5.2 * s)])
    else:
        p.drawLine(QPointF(8 * s, 4 * s), QPointF(8 * s, 9 * s))
        p.drawPoint(QPointF(8 * s, 11.6 * s))
    p.end()
    return pm


def _scan_paths():
    """Plausible files to show while scanning, including real files on the ClaudeXP 'drive'."""
    from ..user import user_name
    user = user_name()
    paths = [rf"C:\WINDOWS\system32\{f}" for f in SYSTEM_FILES]
    paths += [rf"C:\WINDOWS\system32\dllcache\{f}" for f in SYSTEM_FILES[:12]]
    for base in (ROOT / "Program Files", ROOT / "assets"):
        if base.exists():
            for f in list(base.rglob("*"))[:600]:
                if f.is_file() and ".venv" not in f.parts:
                    rel = f.relative_to(ROOT)
                    if rel.parts[0] == "assets":
                        paths.append(rf"C:\WINDOWS\Media\{f.name}" if f.suffix == ".wav"
                                     else rf"C:\Documents and Settings\{user}\My Documents\My Pictures\{f.name}")
                    else:
                        paths.append("C:\\" + "\\".join(rel.parts))
    random.shuffle(paths)
    return paths


class AntiVirus:
    def __init__(self, desktop):
        self.desktop = desktop
        self.state = load_json(STATE_FILE, {})
        if "defs" not in self.state:
            self.state["defs"] = (clock.now() - timedelta(days=5)).strftime("%m/%d/%Y")
        self.main = None
        self.scan_win = None
        self.update_win = None
        self.tray = None
        QTimer.singleShot(0, self._show_tray)

    def _save(self):
        save_json(STATE_FILE, self.state)

    def busy(self):
        return any(w is not None and isValid(w) for w in (self.scan_win, self.update_win))

    def _show_tray(self):
        from ..tray import TrayIcon
        self.tray = TrayIcon(self.desktop, QIcon(shield_icon(16)))
        self.tray.setToolTip(f"{NAME}\nAuto-Protect: Enabled")
        self.tray.activated.connect(lambda _r: self.open())
        self.tray.show()

    def _quietly(self, win, automatic):
        """Scheduled tasks open without stealing focus from what you're doing."""
        prev = self.desktop.active
        self.desktop.open_window(win)
        if automatic and prev is not None and isValid(prev):
            self.desktop.activate(prev)

    def _window(self, title, body, size):
        win = XPWindow(self.desktop, title, body, QIcon(shield_icon(16)), size=size)
        return win

    # ---- main window ---------------------------------------------------------------------
    def open(self):
        if self.main is not None and isValid(self.main):
            self.desktop.open_window(self.main)
            self._refresh()
            return
        body = QWidget()
        body.setObjectName("av")
        body.setAttribute(Qt.WA_StyledBackground, True)
        body.setStyleSheet("QWidget#av { background: white; } QLabel { font-family: Tahoma; font-size: 11px; }"
                           "QPushButton#nav { text-align: left; padding: 6px 10px; border: none; color: white;"
                           " font-family: Tahoma; font-size: 11px; font-weight: bold; background: transparent; }"
                           "QPushButton#nav:hover { background: #2E5FB0; }"
                           "QWidget#side { background: #123E8C; }")
        side = QWidget()
        side.setObjectName("side")
        side.setAttribute(Qt.WA_StyledBackground, True)
        side.setFixedWidth(150)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(0, 10, 0, 10)
        logo = QLabel()
        logo.setPixmap(shield_icon(48))
        logo.setAlignment(Qt.AlignCenter)
        sv.addWidget(logo)
        name = QLabel("<font color='white'><b>ClaudeShield</b><br>AntiVirus 2002</font>")
        name.setAlignment(Qt.AlignCenter)
        sv.addWidget(name)
        sv.addSpacing(12)
        self.pages = QStackedWidget()
        for i, label in enumerate(("Status", "Scan for Viruses", "LiveUpdate", "Quarantine")):
            b = QPushButton(label)
            b.setObjectName("nav")
            b.clicked.connect(lambda _c=False, i=i: (self.pages.setCurrentIndex(i), self._refresh()))
            sv.addWidget(b)
        sv.addStretch()

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignTop)
        self.pages.addWidget(self._page("System Status", self.status_label))
        scan_btn = QPushButton("Scan My Computer")
        scan_btn.clicked.connect(lambda: self.scan())
        self.pages.addWidget(self._page("Scan for Viruses", QLabel("Check every file on your computer for viruses."),
                                        scan_btn))
        lu_btn = QPushButton("Run LiveUpdate")
        lu_btn.clicked.connect(lambda: self.live_update())
        self.pages.addWidget(self._page("LiveUpdate", QLabel("Download the newest virus definitions. New viruses "
                                                              "appear every day: run LiveUpdate every week."), lu_btn))
        self.quarantine = QListWidget()
        self.pages.addWidget(self._page("Quarantine", QLabel("Infected files that were isolated so they can't harm "
                                                              "your computer:"), self.quarantine))
        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(side)
        layout.addWidget(self.pages, 1)
        self.main = self._window(NAME, body, (560, 380))
        self.desktop.open_window(self.main)
        self._refresh()

    def _page(self, title, *widgets):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(16, 14, 16, 14)
        head = QLabel(title)
        head.setFont(QFont("Tahoma", 13, QFont.Bold))
        head.setStyleSheet("color: #123E8C; font-size: 16px;")
        v.addWidget(head)
        for w in widgets:
            if isinstance(w, QPushButton):
                w.setFixedSize(150, 26)
            v.addWidget(w)
        v.addStretch()
        return page

    def _refresh(self):
        if self.main is None or not isValid(self.main):
            return
        defs_age = self._defs_age()
        q = self.state.get("quarantine", [])
        self.status_label.setText(
            "<table cellpadding='4'>"
            "<tr><td><b>Auto-Protect:</b></td><td><font color='green'><b>Enabled</b></font></td></tr>"
            f"<tr><td><b>Virus definitions:</b></td><td>{self.state['defs']}"
            f"{' <font color=red>(out of date)</font>' if defs_age > 7 else ''}</td></tr>"
            f"<tr><td><b>Last full system scan:</b></td><td>{self.state.get('last_scan', 'Never')}</td></tr>"
            f"<tr><td><b>Quarantined items:</b></td><td>{len(q)}</td></tr></table>")
        self.quarantine.clear()
        self.quarantine.addItems([f"{v}  -  {p}" for v, p in q] or ["(empty)"])

    def _defs_age(self):
        try:
            m, d, y = (int(x) for x in self.state["defs"].split("/"))
            now = clock.now()
            return (now.date() - now.date().replace(year=y, month=m, day=d)).days
        except ValueError:
            return 0

    # ---- scanning ----------------------------------------------------------------------------
    def scan(self, automatic=False):
        if self.scan_win is not None and isValid(self.scan_win):
            self.desktop.open_window(self.scan_win)
            return
        from ..user import user_name
        body = QWidget()
        body.setObjectName("scan")
        body.setAttribute(Qt.WA_StyledBackground, True)
        body.setStyleSheet("QWidget#scan { background: #ECE9D8; } QLabel { font-family: Tahoma; font-size: 11px; }")
        v = QVBoxLayout(body)
        v.setContentsMargins(14, 12, 14, 12)
        v.addWidget(QLabel("<b>Scanning:</b>"))
        current = QLabel(" ")
        current.setFixedWidth(420)
        v.addWidget(current)
        counts = QLabel()
        v.addWidget(counts)
        bar = QProgressBar()
        bar.setTextVisible(False)
        v.addWidget(bar)
        row = QHBoxLayout()
        row.addStretch()
        stop = QPushButton("Stop Scan")
        stop.setFixedSize(85, 23)
        row.addWidget(stop)
        v.addLayout(row)
        title = "Scheduled Scan" if automatic else "Scan Progress"
        self.scan_win = self._window(f"{NAME} - {title}", body, (460, 190))
        self._quietly(self.scan_win, automatic)

        paths = _scan_paths()
        clock_ = CoverClock(random.uniform(80, 160))
        infected = []
        if random.random() < INFECTION_CHANCE:
            virus, path = random.choice(VIRUSES)
            infected.append((virus, path.replace("{user}", user_name())))
        timer = QTimer(body)
        state = {"i": 0, "files": 0}
        win = self.scan_win

        def tick():
            f = clock_.fraction()
            state["i"] = (state["i"] + random.randint(1, 4)) % len(paths)
            state["files"] += random.randint(9, 41)
            path = paths[state["i"]]
            current.setText(current.fontMetrics().elidedText(path, Qt.ElideMiddle, 420))
            counts.setText(f"Files scanned: {state['files']:,}      Infected: {len(infected) if f > 0.6 else 0}")
            bar.setValue(int(f * 100))
            if f >= 1.0:
                timer.stop()
                self._scan_done(win, state["files"], infected, automatic)

        def stop_scan():
            timer.stop()
            self.desktop.close_window(win)
            self.scan_win = None

        stop.clicked.connect(stop_scan)
        timer.timeout.connect(tick)
        timer.start(120)

    def _scan_done(self, win, files, infected, automatic):
        now = clock.now()
        self.state["last_scan"] = f"{now.month}/{now.day}/{now.year} {clock.time_text(now)}"
        if infected:
            self.state.setdefault("quarantine", []).extend([list(i) for i in infected])
        self._save()
        self._refresh()
        if isValid(win):
            self.desktop.close_window(win)
        self.scan_win = None
        if infected:
            virus, path = infected[0]
            self.tray.setIcon(QIcon(shield_icon(16, ok=False)))
            self._alert("Virus Found", f"<b>{NAME} found a virus</b><br><br>Virus: <b>{virus}</b><br>"
                                       f"File: {path}<br><br>Action taken: <b>Quarantined</b>. "
                                       "The file can no longer harm your computer.", ok=False)
            sound.play("exclamation")
        else:
            self.tray.showMessage(NAME, f"Scan complete: {files:,} files scanned. No viruses found.", None, 6000)

    def _alert(self, title, html, ok=True):
        from ..network import DialogBody, _fixed_window
        body = DialogBody()
        row = QHBoxLayout(body)
        row.setContentsMargins(14, 12, 14, 12)
        pic = QLabel()
        pic.setPixmap(shield_icon(40, ok))
        pic.setAlignment(Qt.AlignTop)
        row.addWidget(pic)
        col = QVBoxLayout()
        text = QLabel(html)
        text.setWordWrap(True)
        text.setFixedWidth(330)
        col.addWidget(text)
        btn = QPushButton("OK")
        btn.setFixedSize(75, 23)
        col.addWidget(btn, 0, Qt.AlignRight)
        row.addLayout(col)
        holder = {}

        def close():
            self.tray.setIcon(QIcon(shield_icon(16)))
            if holder.get("win") is not None and isValid(holder["win"]):
                self.desktop.close_window(holder["win"])

        btn.clicked.connect(close)
        holder["win"] = _fixed_window(self.desktop, f"{NAME} - {title}", body, close)
        holder["win"].icon = QIcon(shield_icon(16, ok))
        self.desktop.open_window(holder["win"])

    # ---- LiveUpdate ----------------------------------------------------------------------------
    def live_update(self, automatic=False):
        if self.update_win is not None and isValid(self.update_win):
            self.desktop.open_window(self.update_win)
            return
        body = QWidget()
        body.setObjectName("lu")
        body.setAttribute(Qt.WA_StyledBackground, True)
        body.setStyleSheet("QWidget#lu { background: #ECE9D8; } QLabel { font-family: Tahoma; font-size: 11px; }")
        v = QVBoxLayout(body)
        v.setContentsMargins(14, 12, 14, 12)
        status = QLabel("Connecting to the LiveUpdate server...")
        v.addWidget(status)
        bar = QProgressBar()
        bar.setTextVisible(False)
        v.addWidget(bar)
        row = QHBoxLayout()
        row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setFixedSize(75, 23)
        row.addWidget(cancel)
        v.addLayout(row)
        self.update_win = self._window("LiveUpdate", body, (400, 130))
        self._quietly(self.update_win, automatic)
        win = self.update_win
        timer = QTimer(body)
        size = random.uniform(0.8, 2.4)

        def close():
            timer.stop()
            if isValid(win):
                self.desktop.close_window(win)
            self.update_win = None

        def online():
            if not isValid(win):
                return
            clock_ = CoverClock(random.uniform(40, 90))

            def tick():
                f = clock_.fraction()
                bar.setValue(int(f * 100))
                if f < 0.85:
                    status.setText(f"Downloading: {NAME} virus definitions ({size:.1f} MB)...  "
                                   f"{size * f / 0.85:.1f} MB")
                else:
                    status.setText("Installing virus definitions...")
                if f >= 1.0:
                    timer.stop()
                    now = clock.now()
                    self.state["defs"] = now.strftime("%m/%d/%Y")
                    self._save()
                    self._refresh()
                    close()
                    self.tray.showMessage("LiveUpdate", f"Your virus definitions are up to date ({self.state['defs']}).",
                                          None, 6000)

            timer.timeout.connect(tick)
            timer.start(300)

        cancel.clicked.connect(close)
        if network.is_connected():
            QTimer.singleShot(1500, online)
        else:
            status.setText("Waiting for your Internet connection...")
            network.connect(self.desktop, then=lambda: QTimer.singleShot(1500, online))
