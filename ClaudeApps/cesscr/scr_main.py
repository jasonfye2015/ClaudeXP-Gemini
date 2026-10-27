"""Claude Entertainment System.scr - the Timeline's NES clock games as a real Windows screen saver.

Windows runs a screen saver with one of:
    /s          show it, full screen (on every monitor: the games on the main one, black on the rest)
    /p <hwnd>   draw it in the little monitor in Screen Saver Settings (the window it's given)
    /c[:hwnd]   its Settings (no argument at all means this too)
    /a          change password - nothing to do on Windows NT and later
Any key, click or a real move of the mouse ends /s.

The games are ClaudeXP's own (supercb, smb3cb, zeldacb, zelda2cb, metroidcb and ces), copied in at build time by
build_scr.py with small stand-ins for the parts of ClaudeXP they lean on (the shim folder)."""
import ctypes
import os
import sys
import time


def parse(argv):
    """('s' | 'p' | 'c' | 'a', hwnd or None) from Windows' arguments: /s, /p 1234, /c:1234 ..."""
    args = argv[1:]
    if not args:
        return "c", None
    first = args[0].lower().lstrip("/-")
    mode, rest = first[:1], first[1:].lstrip(":")
    hwnd = int(rest) if rest.isdigit() else int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    return mode, hwnd


MODE, HWND = parse(sys.argv)
if MODE == "p":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"     # (the preview window is given in real pixels)

from PySide6.QtCore import QEvent, QObject, Qt, QTimer  # noqa: E402
from PySide6.QtGui import QColor, QPainter, QWindow  # noqa: E402
from PySide6.QtWidgets import QApplication, QWidget  # noqa: E402

NAME = "Claude Entertainment System"


def saver_class():
    from claudexp.screensaver import SAVERS
    return SAVERS[NAME]


class Black(QWidget):
    def paintEvent(self, event):
        QPainter(self).fillRect(self.rect(), QColor("black"))


class Waker(QObject):
    """Ends the show on a key, a click, the wheel, or the mouse really moving (not the jitter as it starts)."""
    GRACE = 1.0

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.started = time.monotonic()
        self.origin = None

    def eventFilter(self, obj, event):
        t = event.type()
        if t in (QEvent.KeyPress, QEvent.MouseButtonPress, QEvent.Wheel):
            self.app.exit(0)
        elif t == QEvent.MouseMove:
            pos = event.globalPosition().toPoint()
            if self.origin is None or time.monotonic() - self.started < self.GRACE:
                self.origin = pos
            elif (pos - self.origin).manhattanLength() > 6:
                self.app.exit(0)
        return False


def show(app):
    cls = saver_class()
    covers = []
    primary = app.primaryScreen()
    for screen in app.screens():
        w = Black()
        w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        w.setMouseTracking(True)
        w.setCursor(Qt.BlankCursor)
        w.setGeometry(screen.geometry())
        if screen is primary:
            game = cls(w)
            game.setAttribute(Qt.WA_TransparentForMouseEvents)
            game.setGeometry(w.rect())
            w.game = game
        w.show()
        w.windowHandle().setScreen(screen)
        w.showFullScreen()
        covers.append(w)
    covers[0].activateWindow()
    waker = Waker(app)
    app.installEventFilter(waker)
    app.setOverrideCursor(Qt.BlankCursor)
    return covers, waker


def preview(app, hwnd):
    user32 = ctypes.windll.user32

    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long)]
    r = RECT()
    user32.GetClientRect(hwnd, ctypes.byref(r))
    w = saver_class()()
    w.setWindowFlags(Qt.FramelessWindowHint)
    w.winId()
    w.windowHandle().setParent(QWindow.fromWinId(hwnd))
    w.setGeometry(0, 0, max(1, r.right - r.left), max(1, r.bottom - r.top))
    w.show()

    def check():                                       # the Settings window closed, or another saver chosen
        if not user32.IsWindow(hwnd) or not user32.IsWindowVisible(hwnd):
            app.exit(0)
    timer = QTimer()
    timer.timeout.connect(check)
    timer.start(500)
    return w, timer


def configure(app):
    from claudexp import ces

    class Host:
        """What the Settings dialogs open their windows on."""
        def open_window(self, win):
            win.exec()

        def close_window(self, win):
            win.done(0)
    ces.settings_dialog(Host())


def main():
    if MODE == "a":
        return 0
    app = QApplication(sys.argv)
    app.setApplicationName(NAME)
    if MODE == "s":
        app.kept = show(app)                          # (held on to while it runs)
    elif MODE == "p" and HWND:
        app.kept = preview(app, HWND)
    else:
        configure(app)
        return 0
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
