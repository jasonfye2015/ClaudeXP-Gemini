"""Heretic and Hexen: Chocolate Heretic / Chocolate Hexen (assets/engines/chocolate) running inside an XP window.

There is no libretro core for these games, so the real engine runs as its own Windows program and its window is
adopted as a child of the XP window (QWindow.fromWinId + createWindowContainer). A native child always draws on
top of ClaudeXP's own windows, so whenever this window isn't the one in front (or a menu is open), the game is
swapped for a still picture of itself (PrintWindow) until it comes back to the front.

WADs come from E:\\WADs (the user's, not in git); config and saves go to data/<game>/. The Hexen demo WAD lacks the
yellow menu font Chocolate Hexen expects, so a tiny add-on WAD is made from the demo's own font (data/hexen)."""
import ctypes
import os
import struct
import subprocess
import time
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QImage, QKeySequence, QPixmap, QWindow
from PySide6.QtWidgets import (QLabel, QListWidget, QListWidgetItem, QMenuBar, QStackedWidget,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from claudecore import host

HERE = Path(__file__).resolve().parent
_pixmaps = {}


def pixmap(name):
    """One of this package's icons (cached)."""
    if name not in _pixmaps:
        _pixmaps[name] = QPixmap(str(HERE / "icons" / name))
    return _pixmaps[name]

ENGINES = HERE / "engines"
GAMES = {
    "heretic": {"title": "Heretic", "exe": "chocolate-heretic.exe", "icon": "heretic_icon.png", "process": "heretic.exe",
                "wads": {"heretic.wad": "Heretic", "heretic1.wad": "Heretic (Shareware)"},
                "help": "Move / turn:  Arrow keys\nFire:  Ctrl\nUse / open:  Space\nRun:  Shift\nStrafe:  Alt + arrows\n"
                        "Fly up / down:  Page Up / Page Down\nUse item:  Enter    Item bar:  [ and ]\n"
                        "Weapons:  1 - 7\nAutomap:  Tab\nMenu:  Esc"},
    "hexen": {"title": "Hexen", "exe": "chocolate-hexen.exe", "icon": "hexen_icon.png", "process": "hexen.exe",
              "wads": {"hexen.wad": "Hexen"},
              "help": "Move / turn:  Arrow keys\nFire:  Ctrl\nUse / open:  Space\nRun:  Shift\nStrafe:  Alt + arrows\n"
                      "Jump:  /\nFly up / down:  Page Up / Page Down\nUse item:  Enter    Item bar:  [ and ]\n"
                      "Weapons:  1 - 4\nAutomap:  Tab\nMenu:  Esc"},
}
CREDITS = ("Chocolate Doom 3.1.1 by Simon Howard and contributors, based on the original id Software and Raven "
           "Software source. Free software under the GNU GPL.")
GAME_W, GAME_H = 640, 480

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
GWL_STYLE = -16
WS_CHILD, WS_CAPTION, WS_THICKFRAME, WS_POPUP = 0x40000000, 0x00C00000, 0x00040000, 0x80000000
WS_MINIMIZEBOX, WS_MAXIMIZEBOX, WS_SYSMENU = 0x00020000, 0x00010000, 0x00080000
CREATE_NO_WINDOW = 0x08000000


def icon_for(key):
    pm = pixmap(GAMES[key]["icon"])
    return QIcon(pm) if not pm.isNull() else QIcon()


def wads_folder():
    local_storage = host.local_storage
    return next((d for d in local_storage().iterdir() if d.is_dir() and d.name.lower() == "wads"), None)


def game_windows(pid):
    """Visible top-level windows of a process: [(hwnd, width, height)]."""
    found = []

    def cb(hwnd, _):
        p = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            r = wintypes.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(r))
            found.append((hwnd, r.right, r.bottom))
        return True
    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return found


class _BMI(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG), ("biYPelsPerMeter", wintypes.LONG),
                ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]


def snapshot(hwnd):
    """The game window's own picture (PrintWindow with PW_RENDERFULLCONTENT, which also catches Direct3D)."""
    r = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(r))
    w, h = r.right, r.bottom
    if w <= 0 or h <= 0:
        return QImage()
    hdc = user32.GetDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    old = gdi32.SelectObject(mem, bmp)
    user32.PrintWindow(hwnd, mem, 3)
    buf = ctypes.create_string_buffer(w * h * 4)
    bmi = _BMI(ctypes.sizeof(_BMI), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bmi), 0)
    gdi32.SelectObject(mem, old)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    user32.ReleaseDC(hwnd, hdc)
    return QImage(buf.raw, w, h, QImage.Format_RGB32).copy()


def yellow_font_wad(iwad, out):
    """Hexen demo: copy its FONTA lumps as FONTAY (the yellow menu font) into a small PWAD. Returns the path or None."""
    try:
        with open(iwad, "rb") as h:
            _kind, n, off = struct.unpack("<4sII", h.read(12))
            h.seek(off)
            entries = [struct.unpack("<II8s", h.read(16)) for _ in range(n)]
            names = [e[2].rstrip(b"\0").decode("latin-1") for e in entries]
            if any(nm.startswith("FONTAY") for nm in names):
                return None                                   # the full game has it already
            lumps = []
            for (pos, size, _raw), nm in zip(entries, names):
                if nm.startswith("FONTA"):
                    h.seek(pos)
                    lumps.append((nm.replace("FONTA", "FONTAY", 1), h.read(size)))
    except (OSError, struct.error):
        return None
    if not lumps:
        return None
    body = b"".join(data for _nm, data in lumps)
    directory, pos = b"", 12
    for nm, data in lumps:
        directory += struct.pack("<II8s", pos if data else 0, len(data), nm.encode()[:8].ljust(8, b"\0"))
        pos += len(data)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(struct.pack("<4sII", b"PWAD", len(lumps), 12 + len(body)) + body + directory)
    return out


class NativeGame(QWidget):
    def __init__(self, desktop, key):
        super().__init__()
        self.desktop = desktop
        self.key = key
        self.game = GAMES[key]
        self.process_image = self.game["process"]               # for Task Manager
        self.frame = None
        self.data = host.saves(key)                       # save games, shared by every era
        self.proc = None
        self.hwnd = None
        self.container = None
        self.started = 0.0
        self.showing = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._menus())
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self.list = QListWidget()
        self.list.setIconSize(pixmap(self.game["icon"]).size().scaled(24, 24, Qt.KeepAspectRatio))
        self.list.setStyleSheet("QListWidget { background: white; border: none; font: 11px Tahoma; }"
                                "QListWidget::item { padding: 4px; } QListWidget::item:selected {"
                                " background: #316AC5; color: white; }")
        self.list.itemActivated.connect(lambda item: self.play(Path(item.data(Qt.UserRole))))
        self.stack.addWidget(self.list)
        self.holder = QWidget()
        self.holder.setStyleSheet("background: black;")
        self.holder_lay = QVBoxLayout(self.holder)
        self.holder_lay.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(self.holder)
        self.still = QLabel()
        self.still.setAlignment(Qt.AlignCenter)
        self.still.setStyleSheet("background: black; color: #C0C0C0; font: 11px Tahoma;")
        self.stack.addWidget(self.still)
        self.status = QLabel()
        self.status.setStyleSheet("font: 11px Tahoma; padding: 2px 6px; background: #ECE9D8;"
                                  " border-top: 1px solid #A0A0A0;")
        lay.addWidget(self.status)
        self.watch = QTimer(self, interval=250, timeout=self._watch)
        self.fill()

    def _menus(self):
        MENU_STYLE = host.menu_style()
        bar = QMenuBar()
        bar.setStyleSheet(MENU_STYLE)
        f = bar.addMenu("&File")
        f.addAction("&Game List", self.stop)
        f.addSeparator()
        f.addAction("E&xit", lambda: self.frame.request_close() if self.frame else None)
        h = bar.addMenu("&Help")
        h.addAction("&Controls...", lambda: self._msg("Controls", self.game["help"]))
        h.addAction(f"&About {self.game['title']}...",
                    lambda: self._msg(f"About {self.game['title']}", f"{self.game['title']}\n\n{CREDITS}"))
        return bar

    def _msg(self, title, text):
        host.message(self.desktop, title, text, "info")

    def fill(self):
        self.list.clear()
        folder = wads_folder()
        found = []
        if folder is not None:
            names = {p.name.lower(): p for p in folder.iterdir()}
            found = [(names[n], t) for n, t in self.game["wads"].items() if n in names]
        icon = QIcon(pixmap(self.game["icon"]))
        for path, title in found:
            item = QListWidgetItem(icon, title)
            item.setData(Qt.UserRole, str(path))
            self.list.addItem(item)
        if not found:
            item = QListWidgetItem(f"Put {self.game['title'].upper()}.WAD in E:\\WADs, then choose File > Game List.")
            item.setFlags(Qt.NoItemFlags)
            self.list.addItem(item)
        self.status.setText(f"{len(found)} game{'s' if len(found) != 1 else ''}  \u2014  double-click to play"
                            if found else "No game files found")

    # ---- running the engine ----------------------------------------------------------------------------
    def play(self, wad):
        self.stop()
        exe = ENGINES / self.game["exe"]
        if not exe.exists():
            self._msg(self.game["title"], f"The game engine ({self.game['exe']}) is missing from assets\\engines.")
            return
        self.data.mkdir(parents=True, exist_ok=True)
        extra = self.data / "claudexp.cfg"
        extra.write_text("graphical_startup 0\nfullscreen 0\ngrabmouse 0\nshow_endoom 0\nnovert 1\n", encoding="ascii")
        args = [str(exe), "-iwad", str(wad), "-window", "-geometry", f"{GAME_W}x{GAME_H}", "-nograbmouse",
                "-config", str(self.data / f"{self.key}.cfg"), "-extraconfig", str(extra), "-savedir", str(self.data)]
        if self.key == "hexen":
            addon = yellow_font_wad(wad, self.data / "claudexp-fonts.wad")
            if addon is not None:
                args += ["-file", str(addon)]
        log = open(self.data / "engine.log", "w", encoding="utf-8", errors="replace")
        self.proc = subprocess.Popen(args, cwd=str(ENGINES), stdout=log, stderr=subprocess.STDOUT,
                                     creationflags=CREATE_NO_WINDOW)
        log.close()
        self.started = time.monotonic()
        self.title = self.game["wads"].get(wad.name.lower(), self.game["title"])
        self.still.setText(f"Loading {self.title}...")
        self.stack.setCurrentWidget(self.still)
        self.status.setText(f"{self.title}  \u2014  starting")
        if self.frame is not None:
            self.frame.set_title(f"{self.game['title']} - {self.title}")
            self._fit()
        QTimer.singleShot(200, self._adopt)

    def _adopt(self):
        """Wait for the engine's window, then make it a child of this XP window."""
        if self.proc is None:
            return
        if self.proc.poll() is not None:
            self._ended()
            return
        wins = [w for w in game_windows(self.proc.pid) if w[1] >= 320]
        if not wins:
            if time.monotonic() - self.started < 20:
                QTimer.singleShot(200, self._adopt)
            else:
                self._msg(self.game["title"], "The game didn't start. See engine.log in ClaudeXP's data folder.")
                self.stop()
            return
        self.hwnd = wins[0][0]
        style = user32.GetWindowLongW(self.hwnd, GWL_STYLE)
        style &= ~(WS_CAPTION | WS_THICKFRAME | WS_POPUP | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU)
        user32.SetWindowLongW(self.hwnd, GWL_STYLE, style | WS_CHILD)
        window = QWindow.fromWinId(self.hwnd)
        self.container = QWidget.createWindowContainer(window, self.holder)
        self.container.setFocusPolicy(Qt.StrongFocus)
        self.holder_lay.addWidget(self.container)
        self.stack.setCurrentWidget(self.holder)
        self.showing = True
        self.container.setFocus()
        self.status.setText(f"{self.title}  \u2014  click the game if the keys don't respond  \u2014  "
                            f"Help > Controls")
        self.watch.start()

    def _in_front(self):
        """Is this window the one the user is looking at, with nothing (menus, Start menu) over it?"""
        return self.frame is not None and self.frame.isVisible() and host.in_front(self.desktop, self.frame)

    def _watch(self):
        if self.proc is None:
            return
        if self.proc.poll() is not None:
            self._ended()
            return
        front = self._in_front()
        if front and not self.showing:
            self.container.show()
            self.stack.setCurrentWidget(self.holder)
            self.container.setFocus()
            self.showing = True
        elif not front and self.showing:
            img = snapshot(self.hwnd)                 # a still of the game stands in while it's covered
            if not img.isNull():
                self.still.setPixmap(QPixmap.fromImage(img).scaled(self.holder.size(), Qt.KeepAspectRatio,
                                                                   Qt.FastTransformation))
            self.stack.setCurrentWidget(self.still)
            self.container.hide()
            self.showing = False

    def _ended(self):
        """The player quit from the game's own menu."""
        self.proc = None
        self._drop_container()
        self.watch.stop()
        self.stack.setCurrentWidget(self.list)
        self.fill()
        if self.frame is not None:
            self.frame.set_title(self.game["title"])

    def _drop_container(self):
        if self.container is not None and isValid(self.container):
            self.container.hide()
            self.container.deleteLater()
        self.container = None
        self.hwnd = None

    def stop(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.kill()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                pass
        self.proc = None
        self._drop_container()
        self.watch.stop()
        self.stack.setCurrentWidget(self.list)
        self.fill()
        if self.frame is not None:
            self.frame.set_title(self.game["title"])

    def _fit(self):
        if self.frame is None or self.frame.maximized:
            return
        chrome = self.frame.size() - self.size()
        extra_h = self.height() - self.stack.height()
        area = self.desktop.work_area()
        w, h = GAME_W + chrome.width(), GAME_H + extra_h + chrome.height()
        if h > area.height():
            w, h = int(w * area.height() / h), area.height()
        self.frame.resize(w, h)

    def closeEvent(self, event):
        self.stop()
        event.accept()


_open = {}


def open_game(desktop, key):
    win = _open.get(key)
    if win is None or not isValid(win):
        body = NativeGame(desktop, key)
        win = host.window(desktop, GAMES[key]["title"], body, icon_for(key), (GAME_W + 16, GAME_H + 90))
        body.frame = win
        _open[key] = win
    desktop.open_window(win)
    return win


def shutdown_game(key):
    win = _open.get(key)
    if win is not None and isValid(win):
        win.content.stop()


def heretic_icon():
    return icon_for("heretic")


def open_heretic(desktop):
    return open_game(desktop, "heretic")


def shutdown_heretic():
    shutdown_game("heretic")


def hexen_icon():
    return icon_for("hexen")


def open_hexen(desktop):
    return open_game(desktop, "hexen")


def shutdown_hexen():
    shutdown_game("hexen")
