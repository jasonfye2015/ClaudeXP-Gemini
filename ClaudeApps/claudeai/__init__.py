"""ClaudeAI: a Claude Desktop-style chat app for the local model.

While it runs it sits in the notification area: double-click the spark to open the window, right-click for
Open / New Chat / Load at Startup / Exit. 'Load at Startup' (on by default) puts it in the tray at logon without
opening a window, and closing the window just tucks it back into the tray; Exit really quits."""
import traceback

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMenu, QSystemTrayIcon
from shiboken6 import isValid
from claudecore import host

_frame = None
_tray = None


def claudeai_icon():
    from .app import app_icon
    return app_icon()


def launch(desktop, new_chat=False):
    global _frame
    ensure_tray(desktop)
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        if new_chat:
            _frame.content.new_chat()
        return
    try:
        from .app import ClaudeAI
        content = ClaudeAI(desktop)
    except Exception:
        host.placeholder(desktop, "ClaudeAI", claudeai_icon(),
                         "ClaudeAI couldn't start.\n\n" + traceback.format_exc(limit=3), sound_event="error")
        return
    _frame = host.window(desktop, "ClaudeAI", content, claudeai_icon(), size=(900, 640))
    content.frame = _frame
    _frame.destroyed.connect(_forget)
    desktop.open_window(_frame)
    content.prompt.setFocus()


def _forget(*_):
    global _frame
    _frame = None


# ---- the notification area --------------------------------------------------------------------------------

def load_at_startup():
    from .store import Settings
    return bool(Settings()["startup"])


def set_load_at_startup(on):
    from .store import Settings
    Settings().set("startup", bool(on))
    if _tray is not None and isValid(_tray) and _tray.contextMenu() is not None:
        for action in _tray.contextMenu().actions():
            if action.isCheckable():
                action.setChecked(bool(on))


def start_at_logon(desktop):
    """Called when the desktop appears: into the tray, quietly, if the user wants it."""
    if load_at_startup():
        ensure_tray(desktop)


def ensure_tray(desktop):
    global _tray
    if _tray is not None and isValid(_tray) and _tray.desktop is desktop:
        return _tray
    _tray = host.tray_icon(desktop, claudeai_icon())
    _tray.setToolTip("ClaudeAI")
    menu = QMenu()
    open_action = menu.addAction("&Open ClaudeAI", lambda: launch(desktop))
    f = open_action.font()
    f.setBold(True)                                       # the default action, as XP shows it
    open_action.setFont(f)
    menu.addAction("&New Chat", lambda: launch(desktop, new_chat=True))
    menu.addSeparator()
    startup = menu.addAction("&Load at Startup")
    startup.setCheckable(True)
    startup.setChecked(load_at_startup())
    startup.toggled.connect(set_load_at_startup)
    menu.addSeparator()
    menu.addAction("E&xit", shutdown)
    _tray.setContextMenu(menu)
    _tray._menu_keepalive = menu
    _tray.activated.connect(lambda reason: launch(desktop)
                            if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger) else None)
    _tray.show()
    return _tray


def tucked_away(desktop):
    """The window was closed with X: say once that ClaudeAI is still in the tray."""
    from .store import Settings
    settings = Settings()
    if _tray is not None and isValid(_tray) and not settings["tray_tip_shown"]:
        settings.set("tray_tip_shown", True)

        def tip():
            if _tray is not None and isValid(_tray):         # (logged off or exited in the meantime: no tray)
                _tray.showMessage("ClaudeAI is still running", "ClaudeAI keeps running in the notification area. "
                                  "Double-click its icon to open it again, or right-click it and choose Exit to "
                                  "close it.")
        QTimer.singleShot(300, tip)


def shutdown():
    global _tray
    if _frame is not None and isValid(_frame):
        _frame.content.shutdown()
        _frame.content._exiting = True
        _frame.desktop.close_window(_frame)
    if _tray is not None and isValid(_tray):
        _tray.hide()
        _tray.deleteLater()
    _tray = None
