"""Start > Programs > Accessories > Office Assistant: call Clippy over (even when he's hiding)."""
from PySide6.QtGui import QIcon


def clippy_icon():
    from .art import icon_pixmap
    return QIcon(icon_pixmap(32))


def summon(desktop):
    from . import get, install, save, settings
    c = get() or install(desktop)
    if not c.cfg["enabled"]:
        data = settings()
        data["enabled"] = True
        save(data)
        c.cfg = data
    if not c.started:
        c.start(greet=False)
    c.summon()


def shutdown():
    from . import get
    if get() is not None:
        get().stop()
