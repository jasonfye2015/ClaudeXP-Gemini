"""SYSTEM-2011's host for the Timeline's shared programs: Aero windows, Windows 7 sounds, Claude7's data folder,
the external drive E:, and the period programs' viewers and dialogs (run here through xpcompat)."""
from claudecore.host import Host

from . import sound
from .paths import DATA


class Host7(Host):
    year = 2011

    def window(self, desktop, title, body, icon, size):
        from .wm import AeroWindow
        return AeroWindow(desktop, title, body, icon, size=size)

    def sound(self, event):
        sound.play(event)

    def data_dir(self):
        return DATA

    def local_storage(self):
        from . import vfs
        return vfs.local_storage()

    def user_name(self):
        from . import user
        return user.muck_name() if user.linked() else user.user_name()

    def muted(self):
        return sound.is_muted()

    def message(self, desktop, title, text, icon="info", buttons=("OK",), on_button=None):
        from .dialogs import msgbox
        return msgbox(desktop, title, text, icon, buttons=buttons, on_button=on_button)

    def menu_style(self):
        from .shims import MENU_CSS
        return ("QMenuBar { background: #F0F0F0; font-family: 'Segoe UI'; font-size: 12px; }"
                "QMenuBar::item { padding: 3px 7px; background: transparent; }"
                "QMenuBar::item:selected { background: #CCE8FF; border: 1px solid #99D1FF; }" + MENU_CSS)

    def now(self):
        from . import clock
        return clock.now()

    def open_flash(self, desktop, path):
        from claudexp.programs.flash import open_flash
        open_flash(desktop, path)
        return True

    def open_media(self, desktop, path):
        from claudexp.programs.amp import MEDIA_EXTS, open_amp
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
        from claudexp.printing import print_document
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
        from claudexp.explorer import viewers
        return viewers.open_file(desktop, path)

    def open_dialog(self, desktop, title, exts, on_open, icon=None, start=None):
        from claudexp.programs.opendialog import open_dialog
        return open_dialog(desktop, title, exts, on_open, icon, start=start)

    def open_folder(self, desktop, path):
        from claudexp import explorer
        return explorer.launch(desktop, path)

    def my_pictures(self):
        from . import vfs
        return vfs.my_pictures()

    def my_documents(self):
        from . import vfs
        return vfs.my_documents()

    def voice_license_accepted(self):
        import json
        try:
            return bool(json.loads((DATA / "speech.json").read_text(encoding="utf-8")).get("accepted"))
        except (OSError, ValueError):
            return False

    def placeholder(self, desktop, title, icon, message, sound_event="default"):
        from .placeholder import open_placeholder
        return open_placeholder(desktop, title, icon, message, sound_event=sound_event)

    def in_front(self, desktop, frame):
        from PySide6.QtWidgets import QApplication, QMenu
        if frame is None or not frame.isVisible() or desktop.active is not frame:
            return False
        if desktop.start_menu.isVisible():
            return False
        return not any(isinstance(w, QMenu) and w.isVisible() for w in QApplication.topLevelWidgets())
