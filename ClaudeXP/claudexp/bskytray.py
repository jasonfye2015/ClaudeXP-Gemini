"""Kithy on Bluesky in the notification area: the Bluesky watcher's icon (claudexp/bsky.py), on every system.

Click it to open the profile site (http://bsky.app/profile/<handle>) in the system's own browser; right-click for
the menu: open the site, Sync now, the status box, the Bsky-Kithy folder, how often to sync, pause, and whether the
status box comes up by itself. While a sync is downloading, a small status box above the icon shows how far it's got:
a bar with the percentage, and a bar chart of the files coming in. The icon gets a little blue arrow while it syncs
and goes grey when Bluesky can't be reached. Also the art for the desktop's link (bsky_icon)."""
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QSystemTrayIcon, QVBoxLayout, QWidget

from . import bsky

NAME = "Kithy on Bluesky"
SITE_URL = f"http://bsky.app/profile/{bsky.HANDLE}"
POLL_MS = 500
BLUE = QColor("#1185FE")


# ---- the art ------------------------------------------------------------------------------------------------------
def _butterfly(p, rect, colour):
    """Bluesky's butterfly, drawn: two pairs of wings."""
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    p.setPen(Qt.NoPen)
    p.setBrush(colour)
    for side in (-1, 1):
        cx = x + w / 2
        top = QPainterPath()
        top.moveTo(cx, y + h * 0.48)
        top.cubicTo(cx + side * w * 0.10, y + h * 0.10, cx + side * w * 0.52, y - h * 0.02, cx + side * w * 0.48,
                    y + h * 0.26)
        top.cubicTo(cx + side * w * 0.46, y + h * 0.44, cx + side * w * 0.24, y + h * 0.56, cx, y + h * 0.50)
        p.drawPath(top)
        low = QPainterPath()
        low.moveTo(cx, y + h * 0.52)
        low.cubicTo(cx + side * w * 0.30, y + h * 0.50, cx + side * w * 0.44, y + h * 0.72, cx + side * w * 0.30,
                    y + h * 0.88)
        low.cubicTo(cx + side * w * 0.18, y + h * 0.98, cx + side * w * 0.04, y + h * 0.80, cx, y + h * 0.56)
        p.drawPath(low)


def bsky_pixmap(size=32, state="idle"):
    """The butterfly on white; syncing adds a small arrow, waiting (offline) or paused turns it grey."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    grey = state in ("waiting", "paused")
    p.setPen(QPen(QColor("#9AA5B1") if grey else QColor("#0A5CC2"), max(1.0, s)))
    p.setBrush(QColor("#FFFFFF"))
    p.drawRoundedRect(QRectF(1.5 * s, 1.5 * s, 29 * s, 29 * s), 7 * s, 7 * s)
    _butterfly(p, QRectF(4 * s, 6 * s, 24 * s, 21 * s), QColor("#8C99A6") if grey else BLUE)
    if state == "syncing":                                # a round arrow badge in the corner
        r = QRectF(size - 15 * s, size - 15 * s, 14 * s, 14 * s)
        p.setPen(QPen(QColor("white"), max(1.0, s)))
        p.setBrush(QColor("#2E9E44"))
        p.drawEllipse(r)
        p.setPen(QPen(QColor("white"), max(1.2, 1.6 * s), Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(r.center().x(), r.top() + 3 * s), QPointF(r.center().x(), r.bottom() - 3.5 * s))
        p.drawLine(QPointF(r.center().x() - 3 * s, r.bottom() - 6.5 * s), QPointF(r.center().x(), r.bottom() - 3.5 * s))
        p.drawLine(QPointF(r.center().x() + 3 * s, r.bottom() - 6.5 * s), QPointF(r.center().x(), r.bottom() - 3.5 * s))
    elif state == "paused":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#5B6670"))
        p.drawRect(QRectF(size - 11 * s, size - 12 * s, 3 * s, 10 * s))
        p.drawRect(QRectF(size - 6 * s, size - 12 * s, 3 * s, 10 * s))
    p.end()
    return pm


def bsky_icon(size=32):
    icon = QIcon()
    for sz in (16, 32, 48):
        icon.addPixmap(bsky_pixmap(sz))
    return icon


# ---- doing things -------------------------------------------------------------------------------------------------
def open_site(desktop):
    """The profile site, in this system's default browser."""
    from .programs import navigator
    navigator.open_url(desktop, SITE_URL)


def open_folder(desktop):
    """Local Storage/Bsky-Kithy in this system's own file browser."""
    import sys
    folder = bsky.folder()
    folder.mkdir(parents=True, exist_ok=True)
    for name in ("claude11.explorer11", "claude7.explorer7"):        # the system that's running has its own
        mod = sys.modules.get(name)
        if mod is not None:
            mod.launch(desktop, folder)
            return
    from . import explorer
    explorer.launch(desktop, folder)


def _ago(t):
    if not t:
        return "not yet"
    mins = int((time.time() - t) // 60)
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    return time.strftime("%I:%M %p", time.localtime(t)).lstrip("0")


def _size(n):
    return f"{n / 1048576:.1f} MB" if n >= 1048576 else f"{max(1, n // 1024)} KB"


# ---- the status box -----------------------------------------------------------------------------------------------
class Chart(QWidget):
    """The progress bar with its percentage, and under it the files coming in as bars (their sizes)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(78)
        self.percent = 0
        self.sizes = []

    def set(self, percent, sizes):
        self.percent, self.sizes = percent, sizes
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        bar = QRectF(0.5, 0.5, w - 1, 20)
        p.setPen(QPen(QColor("#9DB3C8")))
        p.setBrush(QColor("#EEF3F8"))
        p.drawRoundedRect(bar, 4, 4)
        if self.percent > 0:
            fill = QRectF(bar.x() + 1, bar.y() + 1, max(6.0, (bar.width() - 2) * self.percent / 100), bar.height() - 2)
            p.setPen(Qt.NoPen)
            p.setBrush(BLUE)
            p.drawRoundedRect(fill, 3, 3)
        f = QFont("Segoe UI")
        f.setPixelSize(12)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("#0B0F14") if self.percent < 55 else QColor("white"))
        p.drawText(bar, Qt.AlignCenter, f"{self.percent}%")
        chart = QRectF(0, 28, w, 50)                     # the downloads, newest at the right
        p.setPen(QPen(QColor("#D5DEE7")))
        p.drawLine(QPointF(chart.left(), chart.bottom() - 0.5), QPointF(chart.right(), chart.bottom() - 0.5))
        if self.sizes:
            top = max(self.sizes)
            n = 40
            gap = 2
            bw = (chart.width() - gap * (n - 1)) / n
            p.setPen(Qt.NoPen)
            for i, size in enumerate(self.sizes[-n:]):
                hgt = max(2.0, (chart.height() - 4) * size / top)
                x = chart.left() + (n - len(self.sizes[-n:]) + i) * (bw + gap)
                p.setBrush(QColor("#4CA2FF") if i < len(self.sizes[-n:]) - 1 else QColor("#0A5CC2"))
                p.drawRect(QRectF(x, chart.bottom() - 1 - hgt, bw, hgt))
        else:
            f.setBold(False)
            f.setPixelSize(11)
            p.setFont(f)
            p.setPen(QColor("#8A9AAB"))
            p.drawText(chart, Qt.AlignCenter, "Nothing to download yet")
        p.end()


class StatusBox(QFrame):
    """A small box above the tray: what the sync is doing, how far it's got."""

    def __init__(self, desktop, tray):
        super().__init__(desktop)
        self.desktop, self.tray = desktop, tray
        self.setObjectName("bskybox")
        self.setStyleSheet("QWidget { background: transparent; }"
                           " #bskybox { background: white; border: 1px solid #7A8A9A; border-radius: 6px; }"
                           " QLabel { color: #0B0F14; font: 12px 'Segoe UI'; }")
        self.setFixedWidth(300)
        v = QVBoxLayout(self)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(6)
        head = QLabel()
        head.setPixmap(bsky_pixmap(20))
        self.title = QLabel(f"<b>{NAME}</b>")
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(head)
        h.addWidget(self.title, 1)
        close = QLabel('<a href="x" style="color:#5B6670;text-decoration:none">&#x2715;</a>')
        close.linkActivated.connect(lambda _x: self.dismiss())
        h.addWidget(close)
        v.addWidget(row)
        self.phase = QLabel()
        v.addWidget(self.phase)
        self.chart = Chart()
        v.addWidget(self.chart)
        self.detail = QLabel()
        self.detail.setWordWrap(True)
        self.detail.setStyleSheet("color: #5B6670; font: 11px 'Segoe UI';")
        v.addWidget(self.detail)
        self.hide()
        self.dismissed = False

    def refresh(self, st):
        total, done = st.get("total") or 0, st.get("done") or 0
        pct = 100 if st.get("phase") == "Up to date" else (int(done * 100 / total) if total else 0)
        self.chart.set(min(pct, 100), st.get("recent") or [])
        if st.get("state") == "syncing":
            self.phase.setText(f"{st.get('phase') or 'Starting'}...")
        elif st.get("error"):
            self.phase.setText("Couldn't reach Bluesky - it'll try again.")
        else:
            self.phase.setText("Your local copy is up to date.")
        self.detail.setText(f"{min(done, total) if total else done} of {total} posts checked · "
                            f"{st.get('files', 0)} file{'s' if st.get('files', 0) != 1 else ''} downloaded "
                            f"({_size(st.get('bytes', 0))})" if st.get("files") or done else
                            f"{st.get('kept', 0)} posts kept on this computer")
        self.place()
        self.raise_()

    def place(self):
        self.adjustSize()
        anchor = None
        try:
            anchor = self.desktop.taskbar.tray_icon_center(self.tray)
        except Exception:
            pass
        area = self.desktop.rect()
        x = (anchor.x() - self.width() + 30) if anchor is not None else area.right() - self.width() - 10
        bottom = (anchor.y() - 18) if anchor is not None else area.bottom() - 60
        x = max(4, min(x, area.right() - self.width() - 4))
        self.move(x, max(4, bottom - self.height()))

    def pop(self):
        self.dismissed = False
        self.show()
        self.raise_()

    def dismiss(self):
        self.dismissed = True
        self.hide()


# ---- the tray icon ------------------------------------------------------------------------------------------------
class BskyTray:
    def __init__(self, desktop):
        from .tray import TrayIcon
        self.desktop = desktop
        self.state = None
        self.was_syncing = False
        self.hide_at = 0
        self.tray = TrayIcon(desktop, QIcon(bsky_pixmap(16)), desktop)
        self.tray.setToolTip(f"{NAME}\nStarting...")
        self.tray.activated.connect(self._activated)
        self.tray.messageClicked.connect(lambda: open_site(desktop))
        self.box = StatusBox(desktop, self.tray)
        self.menu = QMenu(desktop)
        self.menu.aboutToShow.connect(self._update_menu)
        opened = self.menu.addAction(f"Open {NAME}", lambda: open_site(desktop))
        f = opened.font()
        f.setBold(True)
        opened.setFont(f)
        self.sync_action = self.menu.addAction("Sync now", self._sync_now)
        self.menu.addAction("Show sync status", self._show_box)
        self.menu.addAction("Open the Bsky-Kithy folder", lambda: open_folder(desktop))
        self.menu.addSeparator()
        every = self.menu.addMenu("Check for new posts every")
        self.every_group = QActionGroup(every)
        for m in bsky.MINUTES_CHOICES:
            a = QAction(f"{m} minutes" if m < 60 else f"{m // 60} hour{'s' if m > 60 else ''}", every)
            a.setCheckable(True)
            a.setData(m)
            a.triggered.connect(lambda _c=False, m=m: bsky.set_setting("minutes", m))
            self.every_group.addAction(a)
            every.addAction(a)
        self.popup_action = self.menu.addAction("Show the status box while downloading",
                                                lambda: bsky.set_setting("popup", not bsky.settings().get("popup")))
        self.popup_action.setCheckable(True)
        self.pause_action = self.menu.addAction("Pause syncing", self._toggle_pause)
        self.pause_action.setCheckable(True)
        self.status_line = self.menu.addAction("")
        self.status_line.setEnabled(False)
        self.menu.insertSeparator(self.status_line)
        self.tray.setContextMenu(self.menu)
        self.timer = QTimer(desktop)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(POLL_MS)
        self.tray.show()
        QTimer.singleShot(0, self.refresh)

    # ---- the menu ----
    def _update_menu(self):
        s = bsky.settings()
        for a in self.every_group.actions():
            a.setChecked(a.data() == int(s.get("minutes") or bsky.SYNC_MINUTES))
        self.popup_action.setChecked(bool(s.get("popup", True)))
        self.pause_action.setChecked(bool(s.get("paused")))
        st = bsky.status()
        self.sync_action.setEnabled(st.get("state") != "syncing")
        self.status_line.setText(self._summary(st))

    def _sync_now(self):
        bsky.sync_now()
        self.box.pop()
        self.hide_at = 0

    def _show_box(self):
        self.box.refresh(bsky.status())
        self.box.pop()
        self.hide_at = time.monotonic() + 8 if bsky.status().get("state") != "syncing" else 0

    def _toggle_pause(self):
        bsky.set_setting("paused", not bsky.settings().get("paused"))

    def _activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            open_site(self.desktop)

    # ---- keeping up with the watcher ----
    def _summary(self, st):
        state = st.get("state")
        if state == "syncing":
            total = st.get("total") or 0
            pct = int((st.get("done") or 0) * 100 / total) if total else 0
            return f"Syncing... {min(pct, 100)}%"
        if state == "paused":
            return "Syncing is paused"
        if state == "waiting":
            return "Couldn't reach Bluesky - will try again"
        return f"{st.get('kept', 0)} posts kept - last synced {_ago(st.get('last'))}"

    def refresh(self):
        st = bsky.status()
        state = st.get("state")
        if state != self.state:
            self.state = state
            self.tray.setIcon(QIcon(bsky_pixmap(16, state if state in ("syncing", "waiting", "paused") else "idle")))
        self.tray.setToolTip(f"{NAME}\n{self._summary(st)}")
        syncing = state == "syncing"
        downloading = syncing and (st.get("files") or 0) > 0
        if syncing and not self.box.isVisible() and not self.box.dismissed:
            if st.get("manual") or (downloading and bsky.settings().get("popup", True)):
                self.box.pop()                              # (a quick check with nothing new stays quiet)
        if self.box.isVisible():
            self.box.refresh(st)
        if self.was_syncing and not syncing:               # finished: the box stays a moment, then goes
            self.hide_at = time.monotonic() + 6
            self.box.dismissed = False
            if st.get("new"):
                self.tray.showMessage(NAME, f"{st['new']} new post{'s' if st['new'] != 1 else ''} saved to your "
                                            "local copy.", None, 6000)
        if self.hide_at and time.monotonic() >= self.hide_at and not syncing:
            self.box.hide()
            self.hide_at = 0
        self.was_syncing = syncing


_tray = None


def install(desktop):
    """The watcher, and its icon in the notification area (once per running system)."""
    global _tray
    bsky.install(desktop)
    if _tray is None:
        _tray = BskyTray(desktop)
    return _tray


def get():
    return _tray
