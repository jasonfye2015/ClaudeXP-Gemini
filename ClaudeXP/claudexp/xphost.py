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

    def message(self, desktop, title, text, icon="info", buttons=("OK",), on_button=None):
        from .explorer.dialogs import msgbox
        return msgbox(desktop, title, text, icon, buttons=buttons, on_button=on_button)

    def menu_style(self):
        from .programs.notepad import MENU_STYLE
        return MENU_STYLE

    def now(self):
        from . import clock
        return clock.now()

    def open_flash(self, desktop, path):
        from .programs.flash import open_flash
        open_flash(desktop, path)
        return True

    def open_media(self, desktop, path):
        from .programs.amp import MEDIA_EXTS, open_amp
        if path.suffix.lower() not in MEDIA_EXTS:
            return False
        open_amp(desktop, path)
        return True

    # ---- for the apps ----
    def account_name(self):
        from .user import user_name
        return user_name()

    def on_account_changed(self, callback):
        from .user import account
        account().changed.connect(callback)

    def print_document(self, desktop, title, document):
        from .printing import print_document
        return print_document(desktop, title, document)

    def dialog_body(self):
        from .network import DialogBody
        return DialogBody()

    def fixed_window(self, desktop, title, body, closer):
        from .network import _fixed_window
        return _fixed_window(desktop, title, body, closer)

    def tray_icon(self, desktop, icon):
        from .tray import TrayIcon
        return TrayIcon(desktop, icon)

    def open_file(self, desktop, path):
        from .explorer import viewers
        return viewers.open_file(desktop, path)

    def open_dialog(self, desktop, title, exts, on_open, icon=None, start=None):
        from .programs.opendialog import open_dialog
        return open_dialog(desktop, title, exts, on_open, icon, start=start)

    def open_folder(self, desktop, path):
        from . import explorer
        return explorer.launch(desktop, path)

    def my_pictures(self):
        from .explorer import vfs
        return vfs.my_pictures()

    def my_documents(self):
        from .explorer import vfs
        return vfs.my_documents()

    def voice_license_accepted(self):
        from .setup import speechcheck
        return speechcheck.accepted()

    def placeholder(self, desktop, title, icon, message, sound_event="default"):
        from .programs.placeholder import open_placeholder
        return open_placeholder(desktop, title, icon, message, sound_event=sound_event)

    def in_front(self, desktop, frame):
        from PySide6.QtWidgets import QApplication, QMenu
        if frame is None or not frame.isVisible() or desktop.active is not frame:
            return False
        if desktop.start_menu.isVisible():
            return False
        return not any(isinstance(w, QMenu) and w.isVisible() for w in QApplication.topLevelWidgets())
