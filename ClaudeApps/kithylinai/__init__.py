"""Kithylin AI: chat with Kithylin the Angelic Husky, played by your own fine-tuned models, over Kithylin's art.

A chat window (your words in white, Kithylin's in light blue, the system's in purple), the Furry Code / YIFF Code
encoder-decoder, a gallery of Kithylin's Art, and settings for the model, the two editable system prompts (who he
is, and his codes), the look, and the chat history. Everything it uses - art, models, chats - lives in this folder.

In the Timeline it's a shared program (one window in each era's style); standalone, run `python -m kithylinai`
or "Kithylin AI.bat"."""
import traceback

from shiboken6 import isValid

_frame = None
_content = None


def kithylin_icon():
    from .app import app_icon
    return app_icon()


def launch(desktop):
    global _frame, _content
    from claudecore import host
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        return
    try:
        from .app import KithylinAI
        _content = KithylinAI(desktop)
    except Exception:
        host.placeholder(desktop, "Kithylin AI", kithylin_icon(),
                         "Kithylin AI couldn't start.\n\n" + traceback.format_exc(limit=3), sound_event="error")
        return
    _frame = host.window(desktop, "Kithylin AI", _content, kithylin_icon(), size=(980, 700))
    _content.frame = _frame
    _frame.destroyed.connect(_forget)
    desktop.open_window(_frame)
    _content.composer.setFocus()


def _forget(*_):
    global _frame, _content
    if _content is not None:
        try:
            _content.shutdown()
        except Exception:
            pass
    _frame = None
    _content = None


def shutdown():
    global _frame
    if _content is not None:
        try:
            _content.shutdown()
        except Exception:
            pass
    if _frame is not None and isValid(_frame):
        _frame.desktop.close_window(_frame)
    _frame = None
