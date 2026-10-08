"""Netscape Navigator: a Netscape-style browser for the model-written 2001 Web."""
import traceback

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel
from shiboken6 import isValid

from ... import network
from ...paths import pixmap
from ...wm import XPWindow
from ..placeholder import open_placeholder

SPLASH_MS = 2200

_frame = None
_listening = False
_splash = None


def nav_icon():
    from .browser import nav_icon as icon
    return icon()


def launch(desktop, url=None):
    global _splash
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        if url:
            _frame.content.navigate(url)
        return
    if _splash is not None:
        return   # already starting up
    splash_pm = pixmap("netscape_splash.jpg")
    if splash_pm.isNull():
        _open(desktop, url)
        return
    # The borderless splash window Navigator showed while it loaded.
    _splash = QLabel(desktop)
    _splash.setPixmap(splash_pm)
    _splash.setStyleSheet("border: 1px solid black;")
    _splash.adjustSize()
    area = desktop.work_area()
    _splash.move(area.center() - _splash.rect().center())
    _splash.show()
    _splash.raise_()
    QTimer.singleShot(SPLASH_MS, lambda: _open(desktop, url))


def _open(desktop, url=None):
    global _frame, _listening, _splash
    if _splash is not None:
        _splash.deleteLater()
        _splash = None
    try:
        from .browser import Browser
        browser = Browser(desktop)
    except Exception:
        open_placeholder(desktop, "Netscape Navigator", nav_icon(),
                         "Netscape Navigator couldn't start.\n\n" + traceback.format_exc(limit=3),
                         sound_event="error")
        return
    if not _listening:
        network.on_disconnect(desktop, _network_lost)
        _listening = True
    _frame = XPWindow(desktop, "Netscape Navigator", browser, nav_icon(), size=(840, 640))
    browser.frame = _frame
    _frame.destroyed.connect(_forget)
    desktop.open_window(_frame)
    browser.start(url)


def _forget(*_):
    global _frame
    _frame = None


def _network_lost(quiet):
    if _frame is not None and isValid(_frame):
        _frame.content.network_lost()


def shutdown():
    if _frame is not None and isValid(_frame):
        _frame.content.shutdown()
        _frame.desktop.close_window(_frame)
