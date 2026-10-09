"""AppHost: what a hosted program (like ClaudeAIM) sees of ClaudeXP.

The program's top-level windows are 'adopted' into XP window frames on the desktop
the first time they're shown, and its tray icon goes into the XP notification area.
The program side of this lives in its own host.py (see Program Files/ClaudeAIM).
"""
from PySide6.QtCore import QPoint, QSize, Qt
from shiboken6 import isValid

from . import sound
from .tray import TrayIcon
from . import theme
from .wm import BORDER, TITLE_H, XPWindow

DEFAULT_SIZE = QSize(400, 300)


class AppHost:
    def __init__(self, desktop, name, icon, on_exit=None, on_restart=None):
        self.desktop = desktop
        self.name = name
        self.icon = icon
        self.on_exit = on_exit
        self.on_restart = on_restart
        self.frames = []

    # ---- windows -------------------------------------------------------------
    def adopt(self, widget):
        """Move a top-level program window into an XP frame on the desktop."""
        if self._frame(widget) is not None:
            return
        owner = widget.parentWidget()
        dialog = widget.windowType() == Qt.Dialog
        pos = QPoint(widget.pos()) if widget.testAttribute(Qt.WA_Moved) else None
        if widget.testAttribute(Qt.WA_Resized):
            size = widget.size()
        else:
            size = widget.sizeHint()
            if not size.isValid():
                size = DEFAULT_SIZE
            size = size.expandedTo(widget.minimumSize())

        frame = XPWindow(self.desktop, widget.windowTitle() or self.name, widget, self.icon,
                         size=(size.width() + 2 * BORDER, size.height() + TITLE_H + BORDER),   # Luna metrics; XPWindow adapts
                         buttons=("close",) if dialog else ("min", "max", "close"),
                         on_taskbar=not dialog)
        # Keep QDialog from re-centering itself inside the frame when shown.
        widget.setAttribute(Qt.WA_Moved, True)
        frame.adopt_content()
        widget._xp_frame = frame

        area = self.desktop.work_area()
        if pos is not None:
            target = pos - QPoint(theme.border(), theme.title_h())
        elif dialog:
            target = area.center() - frame.rect().center()
        else:
            target = None
        if target is not None:
            x = max(0, min(target.x(), area.right() - frame.width()))
            y = max(0, min(target.y(), area.bottom() - frame.height()))
            frame.move(x, y)
            frame.placed = True

        if owner is not None:
            # Child windows (dialogs, viewers) used to die with their owner; keep that.
            owner.destroyed.connect(lambda *_: widget.deleteLater() if isValid(widget) else None)
        self.frames.append(frame)
        frame.destroyed.connect(lambda *_: self.frames.remove(frame) if frame in self.frames else None)

    def _frame(self, widget):
        frame = getattr(widget, "_xp_frame", None)
        return frame if frame is not None and isValid(frame) else None

    def work_area(self):
        return self.desktop.work_area()

    def activate(self, widget):
        frame = self._frame(widget)
        if frame is not None:
            self.desktop.activate(frame)

    def is_active(self, widget):
        frame = self._frame(widget)
        return frame is not None and self.desktop.is_active(frame)

    def alert(self, widget):
        frame = self._frame(widget)
        if frame is not None:
            frame.flash()

    def hide_all(self):
        for frame in list(self.frames):
            if isValid(frame) and isValid(frame.content):
                frame.content.hide()

    def close_all(self):
        for frame in list(self.frames):
            if isValid(frame):
                self.desktop.close_window(frame)
        self.frames.clear()

    # ---- the rest of the system ------------------------------------------------
    def extra_context(self, name):
        from . import life
        return life.get().context(name) if life.get() else ""

    def world_started(self, world):
        from . import life
        if life.get():
            life.get().watch_aim(world)

    def muted(self):
        return sound.is_muted()

    def tray_icon(self, icon, parent):
        return TrayIcon(self.desktop, icon, parent)

    def app_exited(self):
        self.close_all()
        if self.on_exit:
            self.on_exit()

    def app_restart(self):
        self.close_all()
        if self.on_restart:
            self.on_restart()
