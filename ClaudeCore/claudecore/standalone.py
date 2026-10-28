"""Shared programs on their own, outside the Timeline's computers - the launcher's APPS window:

    python -m claudecore.standalone soulsong       (or rpg, pystudio, qbstudio)
    python -m claudecore.standalone qbstudio --check    open it, close it again, and say whether that worked

(Kithylin AI has always had its own: python -m kithylinai, from ClaudeApps.)

A small host stands in for a computer (see host.py): a program's windows are ordinary windows on the real desktop,
Open... and Show in folder are the real ones, the game saves and Local Storage are the shared ones, and what a
computer would keep for a program - its settings, and the code studios' choice of language model - lives in
Profile/Standalone Apps. None of a computer's simulation runs around it: no residents, no life, no web - just the
program, so it starts quickly and has the graphics card to itself. Soul and Song and Kithylin AI run their models
on an engine of their own (kithylinai.paths.hosted() is False here), at the context their own Settings choose."""
import importlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from claudecore import host

TIMELINE = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("CLAUDE_STANDALONE_DATA") or TIMELINE / "Profile" / "Standalone Apps")
# key: (name, module, the function that opens it, its icon function, what it is)
APPS = {
    "kithylinai": ("Kithylin AI", "kithylinai", None, None, "Chat with Kithylin, played by the models made from you"),
    "soulsong": ("Soul and Song", "soulsong", "launch", "soulsong_icon",
                 "Your AI Companion, with a memory that grows day by day"),
    "rpg": ("ClaudeRPG", "clauderpg", "open_rpg", "rpg_icon", "A cozy, endless dungeon adventure"),
    "pystudio": ("Copilot Python Studio", "pystudio", "launch", "studio_icon",
                 "Write, debug and run Python, with an AI Helper"),
    "qbstudio": ("Claude QBasic Studio", "qbstudio", "launch", "studio_icon",
                 "QBasic as it was, and a Vibe Coder that writes it for you"),
}
# these share their files with the same program inside a computer (Companions, chats, game saves): not both at once
SHARED_FILES = {"kithylinai", "soulsong", "rpg"}


def _paths():
    for folder in (TIMELINE / "ClaudeApps", TIMELINE / "ClaudeGames", TIMELINE / "ClaudeCore"):
        if folder.is_dir() and str(folder) not in sys.path:
            sys.path.append(str(folder))


def _read(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def local_storage():
    """Where the launcher's Config says Local Storage is (relative: inside the Timeline), as the computers see it."""
    override = os.environ.get("CLAUDE_STANDALONE_STORAGE")         # (the tests' empty stand-in)
    if override:
        return Path(override)
    chosen = _read(TIMELINE / "ClaudeLauncher" / "settings.json").get("local_storage")
    if chosen:
        p = Path(chosen)
        return p if p.is_absolute() else TIMELINE / p
    return TIMELINE / "Local Storage"


def reveal(path):
    """Show a folder, or open a file, the way this PC would."""
    path = str(path)
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", path])
        elif os.name == "nt":
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])
    except OSError:
        pass


# ---- what stands in for a computer ----------------------------------------------------------------------------------
def _window_class():
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QMainWindow
    from shiboken6 import isValid

    class AppWindow(QMainWindow):
        """A program's window on the real desktop: what host.window() gives it here instead of an OS's own."""

        def __init__(self, desktop, title, body, icon, size):
            super().__init__()
            self.desktop, self.content = desktop, body
            self.adopted = False
            self.closing = False
            self.setWindowTitle(title)
            if icon is not None:
                self.setWindowIcon(icon if isinstance(icon, QIcon) else QIcon(icon))
            self.setCentralWidget(body)
            self.resize(int(size[0]), int(size[1]))

        def set_title(self, text):
            self.setWindowTitle(text)

        def toggle_maximize(self):
            self.showNormal() if self.isMaximized() else self.showMaximized()

        def request_close(self):
            """Close it the way a computer's window manager does: the program is asked first (it may want to save),
            and closes the window itself if it needs a moment."""
            c = self.content
            c._host_user_close = True
            try:
                accepted = c.close()
            finally:
                if isValid(c):
                    c._host_user_close = False
            if accepted:
                self.desktop.close_window(self)

        def closeEvent(self, event):
            if self.closing:
                event.accept()
                return
            event.ignore()                              # (the X: the program decides)
            self.request_close()

    return AppWindow


class Desktop:
    """What a program is handed as its computer's desktop: here, the real one. When the program's first window
    closes, the program has ended."""

    def __init__(self):
        self.windows = []
        self.main = None

    def open_window(self, win):
        if win not in self.windows:
            self.windows.append(win)
            if self.main is None:
                self.main = win
                self._centre(win)
        win.show()
        win.raise_()
        win.activateWindow()

    def close_window(self, win):
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication
        if win in self.windows:
            self.windows.remove(win)
        win.closing = True
        win.hide()
        win.deleteLater()
        if win is self.main:
            QTimer.singleShot(0, QApplication.quit)

    def _screen(self):
        from PySide6.QtWidgets import QApplication
        return QApplication.primaryScreen().availableGeometry()

    def width(self):
        return self._screen().width()

    def height(self):
        return self._screen().height()

    def _centre(self, win):
        area = self._screen()
        w, h = min(win.width(), area.width() - 40), min(win.height(), area.height() - 60)
        win.resize(w, h)
        win.move(area.x() + (area.width() - w) // 2, area.y() + (area.height() - h) // 2)


class StandaloneHost(host.Host):
    standalone = True
    year = 2025                                     # (a program that dresses up by era takes the newest)

    def window(self, desktop, title, body, icon, size):
        return _window_class()(desktop, title, body, icon, size)

    def data_dir(self):
        DATA.mkdir(parents=True, exist_ok=True)
        return DATA

    def local_storage(self):
        return local_storage()

    def user_name(self):
        me = _read(TIMELINE / "Profile" / "profile.json")
        return me.get("handle") or me.get("name") or ""

    def account_name(self):
        return _read(TIMELINE / "Profile" / "profile.json").get("name") or ""

    def now(self):
        return datetime.now()                       # (on its own, a program lives in the real year)

    def sound(self, event):
        if event in ("error", "critical", "exclamation"):
            from PySide6.QtWidgets import QApplication
            QApplication.beep()

    def message(self, desktop, title, text, icon="info", buttons=("OK",), on_button=None):
        from PySide6.QtWidgets import QMessageBox
        kind = {"warning": QMessageBox.Warning, "error": QMessageBox.Critical}.get(icon, QMessageBox.Information)
        box = QMessageBox(kind, title, text)
        made = [box.addButton(b, QMessageBox.AcceptRole) for b in buttons]
        box.exec()
        if on_button is not None:
            clicked = box.clickedButton()
            on_button(buttons[made.index(clicked)] if clicked in made else "Cancel")

    def in_front(self, desktop, frame):
        return frame is not None and frame.isVisible() and frame.isActiveWindow()

    def open_folder(self, desktop, path):
        reveal(path)

    def open_file(self, desktop, path):
        reveal(path)

    def open_dialog(self, desktop, title, exts, on_open, icon=None, start=None):
        from PySide6.QtWidgets import QFileDialog
        pattern = " ".join(f"*{e}" for e in sorted(exts))
        path, _ = QFileDialog.getOpenFileName(None, title, str(start or ""), f"{title} ({pattern});;All files (*)")
        if path:
            on_open(path)

    def my_pictures(self):
        return Path.home() / "Pictures"

    def my_documents(self):
        return Path.home() / "Documents"

    def print_document(self, desktop, title, document):
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter
        printer = QPrinter()
        dlg = QPrintDialog(printer)
        dlg.setWindowTitle(f"Print {title}")
        if dlg.exec():
            document.print_(printer)

    def placeholder(self, desktop, title, icon, message, sound_event="default"):
        self.message(desktop, title, message, "error")


def install():
    """Register the stand-in host (once; a computer's own host is never replaced)."""
    try:
        host.get()
        return
    except RuntimeError:
        pass
    _paths()
    host.register(StandaloneHost())


# ---- running one -------------------------------------------------------------------------------------------------
def icon(key, size=48):
    """An app's icon, drawn at this size where it can be."""
    from PySide6.QtGui import QIcon, QPixmap
    _paths()
    if key == "kithylinai":
        pic = TIMELINE / "ClaudeApps" / "kithylinai" / "assets" / "kithylin.jpg"
        return QIcon(QPixmap(str(pic))) if pic.exists() else QIcon()
    _name, module, _open, icon_fn, _what = APPS[key]
    try:
        install()
        mod = importlib.import_module(module)
        if key in ("pystudio", "qbstudio"):                  # (their app_icon takes a size)
            return QIcon(importlib.import_module(f"{module}.app").app_icon(size))
        ic = getattr(mod, icon_fn)()
        sizes = ic.availableSizes()
        biggest = max(sizes, key=lambda s: s.width()) if sizes else None
        if biggest is not None and biggest.width() < size:   # (drawn smaller: scaled up to match the others)
            from PySide6.QtCore import Qt
            return QIcon(ic.pixmap(biggest).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        return ic
    except Exception:
        return QIcon()


def open_app(key, desktop):
    """Open one in this process (a QApplication must exist); its windows land in desktop.windows."""
    install()
    _name, module, open_name, _icon, _what = APPS[key]
    getattr(importlib.import_module(module), open_name)(desktop)


def main(argv):
    key = argv[0] if argv else ""
    if key not in APPS or APPS[key][2] is None:
        print(f"Which app? One of: {', '.join(k for k, v in APPS.items() if v[2])}", file=sys.stderr)
        return 2
    check = "--check" in argv
    from PySide6.QtCore import QCoreApplication, Qt, QTimer
    from PySide6.QtWidgets import QApplication
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)     # (before the app exists: ClaudeRPG's web view)
    app = QApplication(sys.argv[:1])
    app.setApplicationName(APPS[key][0])
    try:
        from claudecore import macfonts
        macfonts.apply()                                         # on a Mac: Mac fonts for the Windows ones
    except ImportError:
        pass
    install()
    app.setWindowIcon(icon(key, 64))
    desktop = Desktop()
    open_app(key, desktop)
    if not desktop.windows:
        return 1                                                 # (it couldn't start, and said why)
    mod = importlib.import_module(APPS[key][1])
    app.aboutToQuit.connect(lambda: getattr(mod, "shutdown", lambda: None)())
    if check:
        QTimer.singleShot(1500, desktop.main.request_close)
        QTimer.singleShot(8000, lambda: (print("it didn't close", flush=True), app.exit(3)))
    code = app.exec()
    if check and code == 0:
        print("ok", flush=True)
    import atexit
    atexit._run_exitfuncs()                    # (stops any engine it started)
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)                             # (straight out: a reply still streaming can't hold the exit up)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
