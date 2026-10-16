"""Copilot Python Studio: an offline Python editor and runner."""
import traceback

from shiboken6 import isValid
from claudecore import host

_frame = None


def studio_icon():
    from .app import app_icon
    return app_icon()


def launch(desktop):
    global _frame
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        return _frame
    try:
        from .app import PythonStudio
        content = PythonStudio(desktop)
    except Exception:
        host.placeholder(desktop, "Copilot Python Studio", studio_icon(),
                         "Copilot Python Studio couldn't start.\n\n" + traceback.format_exc(limit=3),
                         sound_event="error")
        return None
    _frame = host.window(desktop, "Copilot Python Studio", content, studio_icon(), size=(900, 640))
    content.frame = _frame
    _frame.destroyed.connect(_forget)
    desktop.open_window(_frame)
    content.editor().setFocus()
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
