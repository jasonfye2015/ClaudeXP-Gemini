"""CopilotAI, a general-purpose local chat assistant."""
import traceback

from shiboken6 import isValid

from ...wm import XPWindow
from ..placeholder import open_placeholder

_frame = None


def copilotai_icon():
    from .app import app_icon
    return app_icon()


def launch(desktop, new_chat=False):
    global _frame
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        if new_chat:
            _frame.content.new_chat()
        return _frame
    try:
        from .app import CopilotAI
        content = CopilotAI(desktop)
    except Exception:
        open_placeholder(desktop, "CopilotAI", copilotai_icon(),
                         "CopilotAI couldn't start.\n\n" + traceback.format_exc(limit=3), sound_event="error")
        return None
    _frame = XPWindow(desktop, "CopilotAI", content, copilotai_icon(), size=(1000, 700))
    content.frame = _frame
    _frame.destroyed.connect(_forget)
    desktop.open_window(_frame)
    content.prompt.setFocus()
    return _frame


def _forget(*_):
    global _frame
    _frame = None


def shutdown():
    global _frame
    if _frame is not None and isValid(_frame):
        frame, _frame = _frame, None
        frame.content.shutdown()
        frame.desktop.close_window(frame)
