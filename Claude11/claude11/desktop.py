"""The Windows 11 desktop: wallpaper, icons, window management (with Snap and Snap layouts), the centered taskbar,
the Start menu, the toasts, the Widgets board - and the same interface ClaudeXP's desktop gives its programs, so
the period programs run here untouched."""
import time

from PySide6.QtCore import QEvent, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

from . import sound
from .icons import IconManager
from .startmenu import StartMenu
from .taskbar import TASKBAR_H, Taskbar
from .tray import Balloon
from .wm import MicaWindow, SnapLayouts


class SnapHint(QWidget):
    """The translucent rounded rectangle that shows where a dragged window will snap."""

    def __init__(self, desktop):
        super().__init__(desktop)
        self.hide()
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        p.setPen(QPen(QColor(255, 255, 255, 190), 1.5))
        p.setBrush(QColor(255, 255, 255, 60))
        p.drawRoundedRect(r, 8, 8)


class Desktop(QWidget):
    shutdown_requested = Signal()
    restart_requested = Signal()
    logoff_requested = Signal()
    switch_user_requested = Signal()
    lock_requested = Signal()
    sleep_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.windows = []
        self.task_order = []
        self.active = None
        self.explorer_running = True
        self.shown_desktop = []           # windows minimized by Show desktop, to bring back
        self.peeking = False              # (kept for the period code: Windows 11 has no hover peek by default)
        self.peeked, self.peek_frames = [], []
        self.notifications = []           # the toasts that came in, for the notification center
        from . import display
        self.display = display.get()
        self.display.changed.connect(self.update)
        self._cascade = 0
        self.setFocusPolicy(Qt.ClickFocus)
        self.icons = IconManager(self)
        self.taskbar = Taskbar(self)
        self.balloon = Balloon(self)
        self.snap = SnapHint(self)
        self.snap_layouts = SnapLayouts(self)
        self.last_input = time.monotonic()
        from .shims import clippy
        self.clippy = clippy.install(self)
        self.neko = None
        try:
            from claudexp import hdd
            self.hdd = hdd.HddLight(self)
        except Exception:
            self.hdd = None
        try:
            from claudexp import maintenance
            self.maintenance = maintenance.install(self)
        except Exception:
            self.maintenance = None
        from claudexp import life
        self.life = life.install(self)
        try:
            from claudexp import mailtray
            self.mailtray = mailtray.install(self)
        except Exception:
            self.mailtray = None
        self.start_menu = StartMenu(self)
        try:
            from claudexp.programs import neko
            self.neko = neko.install(self)
            if self.neko is not None:
                self.neko.raise_()
        except Exception:
            self.neko = None
        from .programs import widgets
        self.widgets = widgets.install(self)
        from claudexp import menus
        menus.install(self)
        QApplication.instance().installEventFilter(self)
        QApplication.instance().applicationStateChanged.connect(self._app_state_changed)

    # ---- layout ----
    def work_area(self):
        return QRect(0, 0, self.width(), self.height() - TASKBAR_H)

    def showEvent(self, event):
        super().showEvent(event)
        self.icons.ready()

    def resizeEvent(self, event):
        if self.icons.icons and self.icons.state["auto_arrange"]:
            self.icons.layout()
        self.taskbar.setGeometry(0, self.height() - TASKBAR_H, self.width(), TASKBAR_H)
        self.start_menu.place()
        if self.neko is not None:
            try:
                self.neko._place_default()
            except Exception:
                pass
        self.widgets.on_resize()
        for win in self.windows:
            if win.maximized:
                win.setGeometry(self.work_area())
            elif win.snapped:
                win.snap(win.snapped)

    def paintEvent(self, event):
        p = QPainter(self)
        p.drawPixmap(0, 0, self.display.render(self.width(), self.height()))
        if self.peeking:
            p.setRenderHint(QPainter.Antialiasing)
            for rect in self.peek_frames:
                p.setPen(QPen(QColor(255, 255, 255, 200), 1.5))
                p.setBrush(QColor(255, 255, 255, 40))
                p.drawRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)

    # ---- a look at the desktop through the windows (the period code's Aero Peek) ----
    def peek(self, on):
        if on == self.peeking:
            return
        self.peeking = on
        if on:
            self.peeked = [w for w in self.windows if w.isVisible()]
            self.peek_frames = [w.geometry() for w in self.peeked]
            for w in self.peeked:
                w.hide()
        else:
            from shiboken6 import isValid
            for w in self.peeked:
                if isValid(w) and w in self.windows:
                    w.show()
            self.peeked, self.peek_frames = [], []
            self.taskbar.raise_()
            self.balloon.raise_()
        self.update()

    def contextMenuEvent(self, event):
        if self.childAt(event.pos()) is not None:
            return
        self.icons.clear_selection()
        self.icons.desktop_menu(event.globalPos())

    def mousePressEvent(self, event):
        self.icons.desktop_pressed(event)

    def mouseMoveEvent(self, event):
        self.icons.desktop_dragged(event)

    def mouseReleaseEvent(self, event):
        self.icons.desktop_released(event)

    def keyPressEvent(self, event):
        # A key a window's control didn't use (a chat box passes Enter on after sending) bubbles up to here, since
        # every window lives inside the desktop: only keys pressed on the desktop itself are the icons' business.
        if self._key_from_window() or not self.icons.key_pressed(event):
            super().keyPressEvent(event)

    def _key_from_window(self):
        w = QApplication.focusWidget()
        while w is not None and w is not self:
            if hasattr(w, "on_taskbar") and hasattr(w, "content"):
                return True
            w = w.parentWidget()
        return False

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

    # ---- Snap's hint ----
    def snap_hint(self, target):
        if target is None:
            self.snap.hide()
            return
        area = self.work_area()
        if target == "max":
            self.snap.setGeometry(area)
        elif target == "left":
            self.snap.setGeometry(QRect(area.left(), area.top(), area.width() // 2, area.height()))
        else:
            self.snap.setGeometry(QRect(area.left() + area.width() // 2, area.top(), area.width() // 2, area.height()))
        self.snap.show()
        self.snap.raise_()
        self.taskbar.raise_()

    # ---- window management ----
    def open_window(self, win):
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
            if win.resizable and (win.width() > area.width() or win.height() > area.height()):
                win.resize(max(win.minimumSizeHint().width(), min(win.width(), area.width())),
                           max(win.minimumSizeHint().height(), min(win.height(), area.height())))
            x = max(0, min(x, area.right() + 1 - win.width()))
            y = max(0, min(y, area.bottom() + 1 - win.height()))
            win.move(x, y)
            win.placed = True
        self.windows.append(win)
        if win.on_taskbar:
            self.task_order.append(win)
        win.show()
        self.activate(win)

    def withdraw(self, win):
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
        self.widgets.raise_all()
        self.taskbar.raise_()
        self.taskbar.raise_flyouts()
        self.balloon.raise_()
        self.start_menu.raise_()
        self.snap_layouts.raise_()
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

    def toggle_show_desktop(self):
        """The Show desktop sliver: minimize everything, or bring it all back."""
        from shiboken6 import isValid
        visible = [w for w in self.windows if w.isVisible() and w.on_taskbar]
        if visible:
            self.shown_desktop = visible
            for w in visible:
                w.hide()
            self.activate(None)
            sound.play("minimize")
        else:
            back = [w for w in self.shown_desktop if isValid(w) and w in self.windows]
            self.shown_desktop = []
            for w in back:
                w.show()
            if back:
                self.activate(back[-1])
                sound.play("restore")
        self.taskbar.update()

    def set_explorer_running(self, running):
        """Task Manager's End task on explorer.exe: the taskbar and icons go away until it's started again."""
        self.explorer_running = running
        self.taskbar.setVisible(running)
        for icon in self.icons.icons:
            icon.setVisible(running and self.icons.state["show_icons"])
        if not running:
            self.hide_start_menu()

    # ---- the Start menu, the Widgets board and power ----
    def toggle_start_menu(self):
        if self.start_menu.isVisible():
            self.hide_start_menu()
        else:
            self.taskbar.hide_flyouts()
            self.widgets.hide_board()
            self.start_menu.place()
            self.start_menu.show()
            self.start_menu.raise_()
            self.taskbar.update()

    def hide_start_menu(self):
        if self.start_menu.isVisible():
            self.start_menu.hide()
            self.taskbar.update()

    def toggle_widgets(self):
        self.hide_start_menu()
        self.taskbar.hide_flyouts()
        self.widgets.toggle_board()

    def log_off(self):
        self.logoff_requested.emit()

    def switch_user(self):
        self.switch_user_requested.emit()

    def lock(self):
        self.lock_requested.emit()

    def restart(self):
        self.restart_requested.emit()

    def sleep(self):
        self.sleep_requested.emit()

    def turn_off(self):
        self.shutdown_requested.emit()

    # ---- global click handling ----
    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseButtonPress, QEvent.KeyPress, QEvent.Wheel, QEvent.MouseMove):
            self.last_input = time.monotonic()
        if event.type() == QEvent.MouseButtonPress and isinstance(obj, QWidget) and self.isVisible():
            self._on_any_press(obj, event)
        return False

    def _inside(self, obj, widget):
        return widget is not None and widget.isVisible() and (obj is widget or widget.isAncestorOf(obj))

    def _on_any_press(self, obj, event):
        if not (obj is self or self.isAncestorOf(obj)):
            return
        gp = event.globalPosition().toPoint()
        on_taskbar = obj is self.taskbar
        if self.start_menu.isVisible():
            on_start = on_taskbar and self.taskbar.start_rect().contains(self.taskbar.mapFromGlobal(gp))
            if not self._inside(obj, self.start_menu) and not on_start:
                self.hide_start_menu()
        for flyout in self.taskbar.flyout_widgets():
            if flyout.isVisible() and not self._inside(obj, flyout) and not on_taskbar:
                flyout.hide()
        board = self.widgets.board
        if board is not None and board.isVisible() and not self._inside(obj, board) and not on_taskbar:
            self.widgets.hide_board()
        if self.snap_layouts.isVisible() and not self._inside(obj, self.snap_layouts):
            self.snap_layouts.hide()
        if on_taskbar or obj is self.start_menu or obj is self.balloon or obj is self.taskbar.thumb \
                or any(self._inside(obj, f) for f in self.taskbar.flyout_widgets()):
            return
        if self.taskbar.thumb.isVisible():
            self.taskbar.thumb.hide()
        w = obj
        while w is not None and not isinstance(w, MicaWindow):
            w = w.parentWidget()
        if w is not None:
            self.activate(w)
        elif obj is self:
            self.activate(None)
        else:
            from .icons import DesktopIcon
            if isinstance(obj, DesktopIcon):
                self.activate(None)
