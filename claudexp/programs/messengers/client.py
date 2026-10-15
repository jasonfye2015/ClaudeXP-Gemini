"""A messenger program: its main window (sign-in, then the buddy list), its conversation windows, its tray icon
and toasts. MSN Messenger and Yahoo! Messenger are each a Client with their own look (msn.py, yim.py)."""
from PySide6.QtCore import QTimer
from shiboken6 import isValid

from ... import sound
from ...wm import XPWindow
from .ui import Conversation, Toast


class Client:
    """network: the Network; skin: the look (see msn.py). One per messenger, created on first launch."""

    def __init__(self, desktop, network, skin):
        self.desktop, self.network, self.skin = desktop, network, skin
        self.window = None
        self.body = None
        self.convos = {}             # buddy id -> XPWindow
        self.tray = None
        self.was_online = {}
        network.presence_changed.connect(self._presence)
        network.message_added.connect(self._message)

    # ---- the main window -----------------------------------------------------------------------------------
    def show(self):
        if self.window is not None and isValid(self.window):
            self.desktop.open_window(self.window)
            return
        self.body = self.skin.main_window(self)
        self.window = XPWindow(self.desktop, self.skin.title, self.body, self.skin.app_icon(), self.skin.main_size)
        self.body.frame = self.window
        self.desktop.open_window(self.window)
        self._tray_on()

    def signed_in(self):
        self.network.sign_in()
        self.was_online = {bid: b.presence for bid, b in self.network.buddies.items()}
        sound.play("logon") if self.skin.login_sound else None

    def sign_out(self):
        self.network.sign_out()
        for win in list(self.convos.values()):
            if isValid(win):
                self.desktop.close_window(win)
        self.convos.clear()

    def shutdown(self):
        self.sign_out()
        if self.window is not None and isValid(self.window):
            self.desktop.close_window(self.window)
        self.window = None
        if self.tray is not None:
            self.tray.hide()
            self.tray = None

    def _tray_on(self):
        if self.tray is None:
            from ...tray import TrayIcon
            self.tray = TrayIcon(self.desktop, self.skin.app_icon(), self.desktop)
            self.tray.setToolTip(self.skin.title)
            self.tray.activated.connect(lambda *_a: self.show())
            self.tray.show()

    # ---- conversations --------------------------------------------------------------------------------------
    def open_convo(self, bid, activate=True):
        b = self.network.buddies.get(bid)
        if b is None:
            return None
        win = self.convos.get(bid)
        if win is None or not isValid(win):
            body = Conversation(self.network, b, self.skin)
            win = XPWindow(self.desktop, self.skin.convo_title(b), body, self.skin.app_icon(), self.skin.convo_size)
            body.frame = win
            self.convos[bid] = win
            if not activate:
                self.desktop.open_window(win)
                win.flash()
                return win
        self.desktop.open_window(win)
        if activate:
            win.content.focus_input()
        return win

    def _message(self, bid, entry):
        if entry.get("kind") != "contact":
            return
        win = self.convos.get(bid)
        b = self.network.buddies.get(bid)
        open_and_front = win is not None and isValid(win) and self.desktop.is_active(win)
        if not open_and_front:
            sound.play(self.skin.message_sound)
            self.open_convo(bid, activate=False)
            self.toast(f"{self.skin.display(b)} says:", entry["text"][:80], bid)

    def _presence(self, bid):
        b = self.network.buddies.get(bid)
        before = self.was_online.get(bid)
        self.was_online[bid] = b.presence
        if self.network.signed_in and before == "offline" and b.presence == "online":
            sound.play(self.skin.signin_sound)
            self.toast(self.skin.title, f"{self.skin.display(b)} has just signed in.", bid)

    def toast(self, title, text, bid):
        t = Toast(self.desktop, title, text, self.skin.toast_logo(), self.skin.toast_colors)
        t.clicked.connect(lambda: self.open_convo(bid))
        QTimer.singleShot(0, t.raise_)
