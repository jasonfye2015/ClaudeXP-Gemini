"""ClaudeAI: a Claude Desktop-style chat app for the local model."""
import traceback

from shiboken6 import isValid

from ...wm import XPWindow
from ..placeholder import open_placeholder

_frame = None


def claudeai_icon():
    from .app import app_icon
    return app_icon()


def launch(desktop):
    global _frame
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        return
    try:
        from ..aim import ensure_aim_path
        ensure_aim_path()
        from .app import ClaudeAI
        content = ClaudeAI(desktop)
    except Exception:
        open_placeholder(desktop, "ClaudeAI", claudeai_icon(),
                         "ClaudeAI couldn't start.\n\n" + traceback.format_exc(limit=3), sound_event="error")
        return
    _frame = XPWindow(desktop, "ClaudeAI", content, claudeai_icon(), size=(900, 640))
    content.frame = _frame
    _frame.destroyed.connect(_forget)
    desktop.open_window(_frame)
    content.prompt.setFocus()


def _forget(*_):
    global _frame
    _frame = None


def shutdown():
    if _frame is not None and isValid(_frame):
        _frame.content.shutdown()
        _frame.desktop.close_window(_frame)
