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
