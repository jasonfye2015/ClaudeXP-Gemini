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
    host.message(desktop, title, text, "info")   # a message box in this OS's style
    host.menu_style()             # a stylesheet for menus that look like this OS's
    host.in_front(desktop, win)   # is that the window the user is looking at?
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

    def message(self, desktop, title, text, icon="info"):
        """A message box in this OS's style; icon is "info", "warning" or "error"."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(None, title, text)

    def menu_style(self):
        """A Qt stylesheet that makes menus look like this OS's."""
        return ""

    def in_front(self, desktop, frame):
        """Is this window the one the user is looking at, with nothing (menus, the Start menu) over it?"""
        return frame is not None and frame.isVisible()


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


def message(desktop, title, text, icon="info"):
    return get().message(desktop, title, text, icon)


def menu_style():
    return get().menu_style()


def in_front(desktop, frame):
    return get().in_front(desktop, frame)
