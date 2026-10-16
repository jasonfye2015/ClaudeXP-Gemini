"""The host: what a shared program (ClaudeGames, ClaudeArchive, ClaudeApps) asks of the computer it's running on.

A shared program never imports an OS's own modules. It asks the host instead:

    from claudecore import host
    win = host.window(desktop, "Claudeggle", body, icon, (990, 676))   # a window in this OS's style
    host.sound("ding")                                                  # one of this OS's sounds
    host.saves("claudeggle")      # Claude Timeline/ClaudeGames/Saves/claudeggle - shared by every era
    host.data("claudeai")         # this computer's own data folder for that program
    host.local_storage()          # the shared Local Storage (drive E: on XP)
    host.user_name()              # the user's name as the world knows them
    host.muted()                  # is this computer's sound muted?
    host.message(desktop, title, text, "info", buttons, on_button)   # a message box in this OS's style
    host.menu_style()             # a stylesheet for menus that look like this OS's
    host.in_front(desktop, win)   # is that the window the user is looking at?
    host.now()                    # the computer's clock (the real date and time, in the era's year)
    host.open_flash(desktop, path), host.open_media(desktop, path)   # hand a file to this OS's players
    host.era()                    # 2001, 2011 or 2025

Each OS registers its host once at startup (ClaudeXP: claudexp/xphost.py) with register(), or register_factory() so
nothing heavy is imported until a program first asks. The window it returns is that OS's own window class, with at
least .content (the body) and request_close(). The `desktop` a program is given is the OS's own desktop, with
open_window(win) and close_window(win) for any dialogs it opens.

Sound events are the shared names: "menu", "default", "ding", "notify", "exclamation", "critical", "error". An OS
plays its own sound for each, or nothing.
"""
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
SAVES = TIMELINE / "ClaudeGames" / "Saves"

_host = None
_factory = None


class Host:
    """The interface. An OS subclasses this and overrides what it supports."""
    year = 2001

    def window(self, desktop, title, body, icon, size):
        raise NotImplementedError

    def sound(self, event):
        pass

    def data_dir(self):
        raise NotImplementedError

    def local_storage(self):
        return TIMELINE / "Local Storage"

    def user_name(self):
        """The user's name as the world knows them (their online handle, or their account name)."""
        return ""

    def muted(self):
        return False

    def message(self, desktop, title, text, icon="info", buttons=("OK",), on_button=None):
        """A message box in this OS's style; icon is "info", "warning" or "error". on_button(label) is called with
        the button pressed (or "Cancel" if it's closed)."""
        from PySide6.QtWidgets import QMessageBox
        box = QMessageBox(QMessageBox.Information, title, text)
        made = [box.addButton(b, QMessageBox.AcceptRole) for b in buttons]
        box.exec()
        if on_button is not None:
            clicked = box.clickedButton()
            on_button(buttons[made.index(clicked)] if clicked in made else "Cancel")

    def menu_style(self):
        """A Qt stylesheet that makes menus look like this OS's."""
        return ""

    def in_front(self, desktop, frame):
        """Is this window the one the user is looking at, with nothing (menus, the Start menu) over it?"""
        return frame is not None and frame.isVisible()

    def now(self):
        """The computer's clock: the real date and time, in the era's year."""
        from datetime import datetime
        real = datetime.now()
        return real.replace(year=self.year, day=28 if (real.month, real.day) == (2, 29) else real.day)

    def open_flash(self, desktop, path):
        """Play a Flash movie (.swf) in this OS's Flash player. Returns False if there isn't one."""
        return False

    def open_media(self, desktop, path):
        """Play a sound or video in this OS's media player. Returns False if it can't play that kind of file."""
        return False

    # ---- for the apps (ClaudeApps) ----
    def account_name(self):
        """The name on this computer's user account."""
        return self.user_name()

    def on_account_changed(self, callback):
        """Call callback() when the user changes their account name or picture."""

    def print_document(self, desktop, title, document):
        """Print a QTextDocument on this OS's printer."""

    def dialog_body(self):
        """An empty widget styled as this OS's dialog background, to lay a small dialog out on."""
        from PySide6.QtWidgets import QWidget
        return QWidget()

    def fixed_window(self, desktop, title, body, closer):
        """A small fixed-size dialog window around body; closer() runs when it's closed."""
        return self.window(desktop, title, body, None, (body.sizeHint().width(), body.sizeHint().height()))

    def tray_icon(self, desktop, icon):
        """An icon in this OS's notification area (a QSystemTrayIcon-like object)."""
        from PySide6.QtWidgets import QSystemTrayIcon
        return QSystemTrayIcon(icon)

    def open_file(self, desktop, path):
        """Open a file the way this OS would (a picture in its picture viewer, and so on)."""

    def open_dialog(self, desktop, title, exts, on_open, icon=None, start=None):
        """This OS's Open dialog; on_open(path) is called with the chosen file."""

    def open_folder(self, desktop, path):
        """Show a folder in this OS's file manager."""

    def my_pictures(self):
        raise NotImplementedError

    def my_documents(self):
        raise NotImplementedError

    def voice_license_accepted(self):
        """Did the user already accept the speech models' licences (e.g. in this OS's Setup)?"""
        return False

    def placeholder(self, desktop, title, icon, message, sound_event="default"):
        """A window explaining that something isn't available (or couldn't start)."""
        self.message(desktop, title, message, "error")


def register(h):
    global _host
    _host = h


def register_factory(make):
    """make() builds the host the first time it's needed (keeps startup light)."""
    global _factory
    _factory = make


def get():
    global _host
    if _host is None and _factory is not None:
        _host = _factory()
    if _host is None:
        raise RuntimeError("No Claude Timeline host is registered: shared programs run inside one of the computers.")
    return _host


# ---- what programs call --------------------------------------------------------------------------------------
def window(desktop, title, body, icon, size):
    return get().window(desktop, title, body, icon, size)


def sound(event):
    try:
        get().sound(event)
    except Exception:
        pass                                   # a missing sound never breaks a program


def saves(program):
    """The shared save folder for a program (created on demand): progress and high scores follow you between eras."""
    folder = SAVES / program
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def data(program):
    """This computer's own folder for a program's settings and history (created on demand)."""
    folder = Path(get().data_dir()) / program
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def local_storage():
    return Path(get().local_storage())


def era():
    return get().year


def user_name():
    try:
        return get().user_name() or ""
    except Exception:
        return ""


def muted():
    try:
        return bool(get().muted())
    except Exception:
        return False


def message(desktop, title, text, icon="info", buttons=("OK",), on_button=None):
    return get().message(desktop, title, text, icon, buttons, on_button)


def menu_style():
    return get().menu_style()


def in_front(desktop, frame):
    return get().in_front(desktop, frame)


def now():
    return get().now()


def open_flash(desktop, path):
    return get().open_flash(desktop, path)


def open_media(desktop, path):
    return get().open_media(desktop, path)


def account_name():
    try:
        return get().account_name() or ""
    except Exception:
        return ""


def on_account_changed(callback):
    return get().on_account_changed(callback)


def print_document(desktop, title, document):
    return get().print_document(desktop, title, document)


def dialog_body():
    return get().dialog_body()


def fixed_window(desktop, title, body, closer):
    return get().fixed_window(desktop, title, body, closer)


def tray_icon(desktop, icon):
    return get().tray_icon(desktop, icon)


def open_file(desktop, path):
    return get().open_file(desktop, path)


def open_dialog(desktop, title, exts, on_open, icon=None, start=None):
    return get().open_dialog(desktop, title, exts, on_open, icon, start)


def open_folder(desktop, path):
    return get().open_folder(desktop, path)


def my_pictures():
    return Path(get().my_pictures())


def my_documents():
    return Path(get().my_documents())


def voice_license_accepted():
    try:
        return bool(get().voice_license_accepted())
    except Exception:
        return False


def placeholder(desktop, title, icon, message, sound_event="default"):
    return get().placeholder(desktop, title, icon, message, sound_event)
