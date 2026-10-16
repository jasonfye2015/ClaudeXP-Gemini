"""Runs ClaudeAIM (installed in 'Program Files/ClaudeAIM') inside ClaudeXP."""
import sys
import traceback

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .. import network
from ..hosting import AppHost
from ..paths import ROOT, pixmap
from .placeholder import open_placeholder

AIM_DIR = ROOT / "Program Files" / "ClaudeAIM"

_app = None   # the running ClaudeAIM, if any
_listening = False


def ensure_aim_path():
    """Make the installed ClaudeAIM package importable (other programs share its buddies)."""
    if str(AIM_DIR) not in sys.path:
        sys.path.insert(0, str(AIM_DIR))
        from claudeaim import llm
        from .. import broker
        llm.install_broker(broker.get())


def aim_icon():
    return QIcon(pixmap("aol_messenger_icon.png"))


def launch(desktop):
    global _app, _listening
    if _app is not None:
        _bring_forward(_app)
        return
    if not network.is_connected():
        # Like a real 2001 PC: no Internet, so dial first, then start AIM.
        network.connect(desktop, then=lambda: launch(desktop))
        return
    if not _listening:
        network.on_disconnect(desktop, _disconnected)
        _listening = True
    try:
        ensure_aim_path()
        from claudeaim import host
        from claudeaim.app import ClaudeAIM
    except Exception:
        _failed(desktop)
        return
    apply_identity()
    host.install(AppHost(desktop, "ClaudeAIM", aim_icon(),
                         on_exit=_exited, on_restart=lambda: _restart(desktop)))
    _app = ClaudeAIM(QApplication.instance())
    try:
        _app.start()
    except Exception:
        _app = None
        _failed(desktop)


def apply_identity():
    """With one online identity, AIM signs on as the shared handle, password saved, Auto-login on."""
    from .. import user
    if not user.linked():
        return
    ensure_aim_path()
    from claudeaim.storage import Settings
    password = user.online_password()
    Settings().update(screen_name=user.aim_name(), password=password, save_password=True, auto_login=True)


def _bring_forward(app):
    from claudeaim import host
    if app.buddy_list is not None:
        host.present(app.buddy_list)
    elif app.window is not None:
        host.present(app.window)


def _exited():
    global _app
    _app = None


def _restart(desktop):
    _exited()
    launch(desktop)


def shutdown():
    """Log off / Turn Off: close ClaudeAIM quietly (no goodbye sound)."""
    global _app
    app, _app = _app, None
    if app is not None:
        app._quit()


def _disconnected(quiet):
    """The modem hung up: AIM gets signed off."""
    if _app is None:
        return
    shutdown()
    if not quiet:
        def tell():
            from claudeaim import host
            host.information(None, "ClaudeAIM", "You have been disconnected from the AIM service.")
        QTimer.singleShot(300, tell)


def _failed(desktop):
    details = traceback.format_exc(limit=3)
    open_placeholder(desktop, "ClaudeAIM", aim_icon(),
                     "ClaudeAIM couldn't start.\n\n" + details, sound_event="error")
