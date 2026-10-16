"""Wires the windows together: dial-up -> sign on -> connecting -> buddy list."""
import sys

from PySide6.QtCore import QProcess, Qt, QTimer
from PySide6.QtWidgets import QApplication

from . import host

from .contacts import load_contacts
from .engine import World
from .sound import Sounds
from .storage import Settings
from .ui.away import AwayWindow
from .ui.buddylist import BuddyListWindow
from .ui.common import apply_retro_style
from .ui.connecting import ConnectingWindow
from .ui.dialup import DialupWindow
from .ui.guide import show_guide
from .ui.icons import IconsWindow
from .ui.im import IMWindow
from .ui.login import LoginWindow
from .ui.setup import SetupWindow
from .ui.tray import Tray


class ClaudeAIM:
    def __init__(self, qapp: QApplication):
        self.qapp = qapp
        if not host.hosted():  # inside ClaudeXP the desktop owns the app-wide look
            qapp.setQuitOnLastWindowClosed(False)
            apply_retro_style(qapp)
        self.settings = Settings()
        self.sounds = Sounds(self.settings)
        self.contacts, self.contact_errors = load_contacts()
        self.world = None
        self.window = None          # the current step of the sign-on flow
        self.buddy_list = None
        self.im_windows = {}
        self.away_window = None
        self.icons_window = None
        self.tray = None
        self.exiting = False

    # ----- sign-on flow ----------------------------------------------------

    def start(self):
        if self.contact_errors:
            host.warning(None, "ClaudeAIM",
                                "Some buddies couldn't be loaded:\n\n" + "\n".join(self.contact_errors))
        if self.settings["skip_dialup"] or host.hosted():  # inside ClaudeXP, XP does the dialing
            self._after_dialup()
        else:
            self.window = DialupWindow(self.settings, self.sounds)
            self.window.finished.connect(self._after_dialup)
            self.window.cancelled.connect(self._quit)
            self.window.start()

    def _after_dialup(self):
        if self.settings["auto_login"] and self.settings["screen_name"]:
            self._show_connecting()
        else:
            self._show_login()

    def _show_login(self):
        self.window = LoginWindow(self.settings)
        self.window.signed_on.connect(self._show_connecting)
        self.window.help_requested.connect(lambda: show_guide("signing-on"))
        self.window.setup_requested.connect(lambda: self._show_setup(self.window))
        self.window.quit_requested.connect(self._quit)
        self.window.show()

    def _show_connecting(self):
        self.window = ConnectingWindow(self.settings, self.sounds)
        self.window.connected.connect(self._show_buddy_list)
        self.window.cancelled.connect(self._show_login)
        self.window.start()

    def _show_buddy_list(self):
        self.window = None
        self.world = World(self.settings, self.sounds, self.contacts, self.qapp)
        bl = self.buddy_list = BuddyListWindow(self.settings, self.world)
        bl.open_im.connect(self.open_im)
        bl.away_requested.connect(self._show_away)
        bl.icon_requested.connect(self._show_icons)
        bl.setup_requested.connect(lambda: self._show_setup(bl))
        bl.help_requested.connect(lambda: show_guide("buddy-list"))
        bl.exit_requested.connect(self.exit)
        bl.close_requested.connect(self._buddy_list_closed)
        bl.show()
        if Tray.available():
            self.tray = Tray(self.settings, self.world, self.qapp)
            self.tray.open_list.connect(self._show_buddy_list_window)
            self.tray.open_im.connect(self.open_im)
            self.tray.away_requested.connect(self._show_away)
            self.tray.back_requested.connect(self._im_back)
            self.tray.exit_requested.connect(self.exit)
        self.world.start()
        host.world_started(self.world)
        if self.world.has_unread():
            QTimer.singleShot(2500, lambda: self.sounds.play("gotmail.wav"))

    def _show_buddy_list_window(self):
        host.present(self.buddy_list)

    def _buddy_list_closed(self):
        """Closing the Buddy List tucks ClaudeAIM into the tray (or exits if there's no tray)."""
        if self.tray:
            self.buddy_list.hide()
            self.tray.tell_still_running()
        else:
            self.exit()

    def _im_back(self):
        if self.away_window:
            self.away_window.close()  # closing it ends away status
        else:
            self.world.set_user_away(False)

    # ----- buddy list windows ------------------------------------------------------

    def open_im(self, buddy_id):
        win = self.im_windows.get(buddy_id)
        if win is None:
            win = IMWindow(self.settings, self.world, buddy_id)
            win.closed.connect(self._im_closed)
            offset = 30 * (len(self.im_windows) % 8)
            screen = host.available_geometry(win)
            win.move(screen.left() + 200 + offset, screen.top() + 150 + offset)
            self.im_windows[buddy_id] = win
        host.present(win)

    def _im_closed(self, buddy_id):
        win = self.im_windows.pop(buddy_id, None)
        if win:
            win.deleteLater()

    def _show_away(self):
        if self.away_window is None:
            self.away_window = AwayWindow(self.settings, self.world, self.buddy_list)
            self.away_window.destroyed.connect(lambda: setattr(self, "away_window", None))
            self.away_window.setAttribute(Qt.WA_DeleteOnClose)
        host.present(self.away_window)

    def _show_icons(self):
        if self.icons_window is None:
            self.icons_window = IconsWindow(self.settings, self.buddy_list)
            self.icons_window.icon_changed.connect(self._icon_changed)
            self.icons_window.destroyed.connect(lambda: setattr(self, "icons_window", None))
            self.icons_window.setAttribute(Qt.WA_DeleteOnClose)
        host.present(self.icons_window)

    def _icon_changed(self):
        for win in self.im_windows.values():
            win.refresh_user_icon()

    def _show_setup(self, parent):
        dlg = SetupWindow(self.settings, self.contacts, parent)
        dlg.reset_requested.connect(self._restart)
        dlg.exec()
        dlg.deleteLater()

    # ----- leaving -----------------------------------------------------------------

    def _quit(self):
        if self.world:
            self.world.stop()
        if self.tray:
            self.tray.hide()
        host.exit_app()

    def _restart(self):
        if self.world:
            self.world.stop()
        if self.tray:
            self.tray.hide()
        if not host.restart_app():
            QProcess.startDetached(sys.executable, sys.argv)
            self._quit()

    def exit(self):
        if self.exiting:
            return
        self.exiting = True
        if self.world:
            self.world.stop()
        if self.tray:
            self.tray.hide()
        host.hide_all_windows()
        self.sounds.play("goodbye.wav", on_finished=self._quit)
        QTimer.singleShot(5000, self._quit)  # in case the sound never finishes

