"""EPOCH-2001's host for the Timeline's shared programs: XP windows, XP sounds, ClaudeXP's data folder, drive E:."""
from claudecore.host import Host

from . import sound
from .paths import DATA


class XPHost(Host):
    year = 2001

    def window(self, desktop, title, body, icon, size):
        from .wm import XPWindow
        return XPWindow(desktop, title, body, icon, size=size)

    def sound(self, event):
        sound.play(event)

    def data_dir(self):
        return DATA

    def local_storage(self):
        from .explorer import vfs
        return vfs.local_storage()

    def user_name(self):
        from . import user
        return user.muck_name() if user.linked() else user.user_name()

    def muted(self):
        return sound.is_muted()

    def message(self, desktop, title, text, icon="info"):
        from .explorer.dialogs import msgbox
        return msgbox(desktop, title, text, icon)

    def menu_style(self):
        from .programs.notepad import MENU_STYLE
        return MENU_STYLE

    def in_front(self, desktop, frame):
        from PySide6.QtWidgets import QApplication, QMenu
        if frame is None or not frame.isVisible() or desktop.active is not frame:
            return False
        if desktop.start_menu.isVisible():
            return False
        return not any(isinstance(w, QMenu) and w.isVisible() for w in QApplication.topLevelWidgets())
