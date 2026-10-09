"""The desktop: wallpaper, icons, window management, taskbar and Start menu."""
import time

from PySide6.QtCore import QEvent, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter
from PySide6.QtWidgets import QApplication, QStyle, QWidget

from . import programs, sound
from .paths import pixmap
from .programs.placeholder import open_placeholder
from .startmenu import StartMenu
from .taskbar import TASKBAR_H, Taskbar
from .hdd import HddLight
from .tray import Balloon
from .wm import XPWindow


class Desktop(QWidget):
    shutdown_requested = Signal()
    restart_requested = Signal()
    logoff_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.windows = []      # z-order, bottom to top
        self.task_order = []   # order windows were opened
        self.active = None
        from . import display
        self.display = display.get()
        self.display.changed.connect(self.update)
        self._cascade = 0

        self.setFocusPolicy(Qt.ClickFocus)
        from .desktop_icons import IconManager
        self.icons = IconManager(self)

        self.taskbar = Taskbar(self)
        self.balloon = Balloon(self)
        self.hdd = HddLight(self)
        self.last_input = time.monotonic()
        from . import maintenance
        self.maintenance = maintenance.install(self)
        from . import life
        self.life = life.install(self)
        self.start_menu = StartMenu(self)
        from . import menus
        menus.install(self)              # pop-up menus stay inside the XP screen
        QApplication.instance().installEventFilter(self)
        QApplication.instance().applicationStateChanged.connect(self._app_state_changed)

    # ---- layout -------------------------------------------------------------
    def work_area(self):
        return QRect(0, 0, self.width(), self.height() - TASKBAR_H)

    def showEvent(self, event):
        super().showEvent(event)
        self.icons.ready()            # the icons need the real screen size for their grid

    def resizeEvent(self, event):
        if self.icons.icons and self.icons.state["auto_arrange"]:
            self.icons.layout()
        self.taskbar.setGeometry(0, self.height() - TASKBAR_H, self.width(), TASKBAR_H)
        self.start_menu.move(0, self.height() - TASKBAR_H - self.start_menu.height())
        for win in self.windows:
            if win.maximized:
                win.setGeometry(self.work_area())

    def paintEvent(self, event):
        p = QPainter(self)
        p.drawPixmap(0, 0, self.display.render(self.width(), self.height()))

    def contextMenuEvent(self, event):
        """Right-clicking the desktop itself: XP's desktop menu."""
        if self.childAt(event.pos()) is not None:
            return
        self.icons.clear_selection()
        self.icons.desktop_menu(event.globalPos())

    # ---- mouse, keyboard and drops on the empty desktop (icons handle their own) ----
    def mousePressEvent(self, event):
        self.icons.desktop_pressed(event)

    def mouseMoveEvent(self, event):
        self.icons.desktop_dragged(event)

    def mouseReleaseEvent(self, event):
        self.icons.desktop_released(event)

    def keyPressEvent(self, event):
        if not self.icons.key_pressed(event):
            super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()

    dragMoveEvent = dragEnterEvent

    def dropEvent(self, event):
        from pathlib import Path
        paths = [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            event.setDropAction(Qt.CopyAction)
            event.accept()
            self.icons.drop_files(paths, event.position().toPoint())

    # ---- icons --------------------------------------------------------------
    def _open_recycle_bin(self):
        from . import explorer
        explorer.launch(self, explorer.RECYCLE_BIN)


    # ---- window management ----------------------------------------------------
    def open_window(self, win: XPWindow):
        """Put a window on screen (first time: place it), or bring a withdrawn one back."""
        if win in self.windows:
            self.activate(win)
            return
        if not win.placed:
            area = self.work_area()
            x = 90 + self._cascade * 26
            y = 40 + self._cascade * 26
            if x + win.width() > area.right() or y + win.height() > area.bottom():
                self._cascade = 0
                x, y = 90, 40
            self._cascade = (self._cascade + 1) % 8
            win.move(x, y)
            win.placed = True
        self.windows.append(win)
        if win.on_taskbar:
            self.task_order.append(win)
        win.show()
        self.activate(win)

    def withdraw(self, win):
        """The program hid this window: take it off the screen and the taskbar, but keep it."""
        if win not in self.windows:
            return
        self.windows.remove(win)
        if win in self.task_order:
            self.task_order.remove(win)
        win.hide()
        if self.active is win:
            self.activate(self._topmost_visible())
        self.taskbar.update()

    def _topmost_visible(self):
        for win in reversed(self.windows):
            if win.isVisible():
                return win
        return None

    def activate(self, win):
        if win is not None and win not in self.windows:
            return
        if win is not None:
            if not win.isVisible():
                win.show()
            win.raise_()
            self.windows.remove(win)
            self.windows.append(win)
            win.flashing = False
        self.taskbar.raise_()
        self.balloon.raise_()
        self.start_menu.raise_()
        changed = win is not self.active
        self.active = win
        for w in self.windows:
            if w.active != (w is win):
                w.active = w is win
                w.update()
                w.notify_activation()
        if changed and win is not None:
            win.focus_content()
        self.taskbar.update()

    def is_active(self, win):
        """True if the user can see this window and it has focus."""
        return (win is self.active and win.isVisible() and self.isVisible()
                and QApplication.applicationState() == Qt.ApplicationActive)

    def _app_state_changed(self, *_):
        if self.active is not None:
            self.active.notify_activation()

    def minimize(self, win):
        sound.play("minimize")
        win.hide()
        self.activate(self._topmost_visible())
        self.taskbar.update()

    def close_window(self, win):
        """Destroy a window and its content."""
        if win in self.windows:
            self.windows.remove(win)
        if win in self.task_order:
            self.task_order.remove(win)
        win.hide()
        win.deleteLater()
        if self.active is win:
            self.active = None
            self.activate(self._topmost_visible())
        self.taskbar.update()

    def taskbar_clicked(self, win):
        self.hide_start_menu()
        if win is self.active and win.isVisible():
            self.minimize(win)
        else:
            if not win.isVisible():
                sound.play("restore")
            self.activate(win)

    # ---- start menu -----------------------------------------------------------
    def toggle_start_menu(self):
        if self.start_menu.isVisible():
            self.hide_start_menu()
        else:
            self.start_menu.show()
            self.start_menu.raise_()
            self.taskbar.update()

    def hide_start_menu(self):
        if self.start_menu.isVisible():
            self.start_menu.hide()
            self.taskbar.update()

    def log_off(self):
        self.logoff_requested.emit()

    def turn_off(self):
        self.shutdown_requested.emit()

    # ---- global click handling -------------------------------------------------
    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseButtonPress, QEvent.KeyPress, QEvent.Wheel, QEvent.MouseMove):
            self.last_input = time.monotonic()   # for 'only when idle' maintenance
        if event.type() == QEvent.MouseButtonPress and isinstance(obj, QWidget) and self.isVisible():
            self._on_any_press(obj, event)
        return False

    def _on_any_press(self, obj, event):
        if not (obj is self or self.isAncestorOf(obj)):
            return
        gp = event.globalPosition().toPoint()
        if self.start_menu.isVisible():
            in_menu = obj is self.start_menu or self.start_menu.isAncestorOf(obj)
            on_start = self.taskbar.start_rect().contains(self.taskbar.mapFromGlobal(gp)) and obj is self.taskbar
            if not in_menu and not on_start:
                self.hide_start_menu()
        if obj is self.taskbar or obj is self.start_menu or obj is self.balloon:
            return
        w = obj
        while w is not None and not isinstance(w, XPWindow):
            w = w.parentWidget()
        if w is not None:
            self.activate(w)
        elif obj is self:
            self.activate(None)
        else:
            from .desktop_icons import DesktopIcon
            if isinstance(obj, DesktopIcon):
                self.activate(None)
