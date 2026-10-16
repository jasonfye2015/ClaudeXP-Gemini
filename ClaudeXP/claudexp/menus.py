"""Keep every pop-up menu inside the XP screen instead of spilling onto the real desktop.

install(desktop) adds one application-wide event filter: whenever any QMenu is shown (context menus,
menu-bar drop-downs, the Start menu's All Programs, tray menus, hosted programs' menus) it is moved
back inside the desktop's work area (above the taskbar). Too low and it slides up; a submenu with no
room on the right opens to the left of its parent, like XP's."""
from PySide6.QtCore import QEvent, QObject, QPoint, QRect
from PySide6.QtWidgets import QApplication, QMenu
from shiboken6 import isValid


class _MenuKeeper(QObject):
    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Show and isinstance(obj, QMenu) and isValid(self.desktop):
            self.contain(obj)
        return False

    def bounds(self):
        area = self.desktop.work_area()
        return QRect(self.desktop.mapToGlobal(area.topLeft()), area.size())

    def contain(self, menu):
        b, g = self.bounds(), menu.geometry()
        if not b.intersects(g):
            return                                 # not over the XP screen at all; leave it be
        x, y = g.x(), g.y()
        if g.right() > b.right():
            parent = menu.parentWidget()
            if isinstance(parent, QMenu) and parent.isVisible() and parent.geometry().left() - g.width() >= b.left():
                x = parent.geometry().left() - g.width() + 3
            else:
                x = b.right() - g.width() + 1
        if g.bottom() > b.bottom():
            y = b.bottom() - g.height() + 1
        x, y = max(x, b.left()), max(y, b.top())
        if (x, y) != (g.x(), g.y()):
            menu.move(QPoint(x, y))


def install(desktop):
    keeper = _MenuKeeper(desktop)
    QApplication.instance().installEventFilter(keeper)
    return keeper
