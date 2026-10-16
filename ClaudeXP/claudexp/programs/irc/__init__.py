"""ClaudeIRC: a mIRC-style client for the simulated FurNet IRC network."""
import traceback

from PySide6.QtGui import QIcon
from shiboken6 import isValid

from ... import network
from ...paths import pixmap
from ...wm import XPWindow
from ..placeholder import open_placeholder

_frame = None
_listening = False


def irc_icon():
    return QIcon(pixmap("mirc_icon.png"))


def launch(desktop):
    global _frame, _listening
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        return
    try:
        from .client import IrcClient
        from .furnet import FurNet
        client = IrcClient(desktop, FurNet())
    except Exception:
        open_placeholder(desktop, "ClaudeIRC", irc_icon(),
                         "ClaudeIRC couldn't start.\n\n" + traceback.format_exc(limit=3), sound_event="error")
        return
    if not _listening:
        network.on_disconnect(desktop, _network_lost)
        _listening = True
    _frame = XPWindow(desktop, "ClaudeIRC", client, irc_icon(), size=(800, 560))
    client.frame = _frame
    _frame.destroyed.connect(_forget)
    desktop.open_window(_frame)
    client.start()


def _forget(*_):
    global _frame
    _frame = None


def _network_lost(quiet):
    if _frame is not None and isValid(_frame):
        _frame.content.network_lost()


def shutdown():
    """Log Off / Turn Off."""
    if _frame is not None and isValid(_frame):
        _frame.content.shutdown()
        _frame.desktop.close_window(_frame)
