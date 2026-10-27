"""Claude QBasic Studio: write, run and debug QBasic programs, with an AI that vibe-codes them."""
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
        from .app import QBasicStudio, TITLE
        content = QBasicStudio(desktop)
    except Exception:
        host.placeholder(desktop, "Claude QBasic Studio", studio_icon(),
                         "Claude QBasic Studio couldn't start.\n\n" + traceback.format_exc(limit=3),
                         sound_event="error")
        return None
    _frame = host.window(desktop, TITLE, content, studio_icon(), size=(1260, 800))
    content.frame = _frame
    content._update_frame_title()
    _frame.destroyed.connect(_forget)
    desktop.open_window(_frame)
    if content.editor() is not None:
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
