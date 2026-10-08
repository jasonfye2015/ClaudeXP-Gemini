"""The desktop: wallpaper, icons, window management, taskbar and Start menu."""
from PySide6.QtCore import QEvent, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter
from PySide6.QtWidgets import QApplication, QStyle, QWidget

from . import programs
from .paths import pixmap
from .programs.placeholder import open_placeholder
from .startmenu import StartMenu
from .taskbar import TASKBAR_H, Taskbar
from .tray import Balloon
from .wm import XPWindow


class DesktopIcon(QWidget):
    W, H = 76, 70

    def __init__(self, desktop, label, icon, on_open):
        super().__init__(desktop)
        self.desktop = desktop
        self.label = label
        self.icon = icon
        self.on_open = on_open
        self.selected = False
        self.setFixedSize(self.W, self.H)

    def mousePressEvent(self, event):
        self.desktop.select_icon(self)

    def mouseDoubleClickEvent(self, event):
        self.desktop.select_icon(None)
        self.on_open()

    def paintEvent(self, event):
        p = QPainter(self)
        pm = self.icon.pixmap(32, 32, QIcon.Selected if self.selected else QIcon.Normal)
        p.drawPixmap((self.W - 32) // 2, 2, pm)
        p.setFont(QFont("Tahoma", 8))
        text_rect = QRect(2, 38, self.W - 4, self.H - 38)
        flags = Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap
        if self.selected:
            bounds = p.boundingRect(text_rect, flags, self.label).adjusted(-2, 0, 2, 0)
            p.fillRect(bounds, QColor("#316AC5"))
        else:
            p.setPen(QColor(0, 0, 0, 200))
            p.drawText(text_rect.translated(1, 1), flags, self.label)
        p.setPen(QColor("white"))
        p.drawText(text_rect, flags, self.label)


class Desktop(QWidget):
    shutdown_requested = Signal()
    logoff_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.windows = []      # z-order, bottom to top
        self.task_order = []   # order windows were opened
        self.active = None
        self.wallpaper = pixmap("windows-xp-bliss-4k-lu-1024x768.jpg")
        self._wall_scaled = None
        self._cascade = 0

        style = QApplication.style()
        self.icons = [
            DesktopIcon(self, "My Computer", style.standardIcon(QStyle.SP_ComputerIcon),
                        lambda: programs.launch(self, "mycomputer")),
            DesktopIcon(self, "Notepad", style.standardIcon(QStyle.SP_FileIcon),
                        lambda: programs.launch(self, "notepad")),
            DesktopIcon(self, "America Online", QIcon(pixmap("aol_icon.png")),
                        lambda: programs.launch(self, "connect")),
            DesktopIcon(self, "Netscape Navigator", programs.get("navigator").icon(),
                        lambda: programs.launch(self, "navigator")),
            DesktopIcon(self, "ClaudeAIM", programs.get("aim").icon(),
                        lambda: programs.launch(self, "aim")),
            DesktopIcon(self, "ClaudeIRC", programs.get("irc").icon(),
                        lambda: programs.launch(self, "irc")),
            DesktopIcon(self, "ClaudeMUCK", programs.get("muck").icon(),
                        lambda: programs.launch(self, "muck")),
            DesktopIcon(self, "Recycle Bin", style.standardIcon(QStyle.SP_TrashIcon),
                        lambda: open_placeholder(self, "Recycle Bin", style.standardIcon(QStyle.SP_TrashIcon),
                                                 "The Recycle Bin is empty.")),
        ]
        for i, icon in enumerate(self.icons):
            icon.move(8, 8 + i * (DesktopIcon.H + 8))

        self.taskbar = Taskbar(self)
        self.balloon = Balloon(self)
        self.start_menu = StartMenu(self)
        QApplication.instance().installEventFilter(self)
        QApplication.instance().applicationStateChanged.connect(self._app_state_changed)

    # ---- layout -------------------------------------------------------------
    def work_area(self):
        return QRect(0, 0, self.width(), self.height() - TASKBAR_H)

    def resizeEvent(self, event):
        self._wall_scaled = None
        self.taskbar.setGeometry(0, self.height() - TASKBAR_H, self.width(), TASKBAR_H)
        self.start_menu.move(0, self.height() - TASKBAR_H - self.start_menu.height())
        for win in self.windows:
            if win.maximized:
                win.setGeometry(self.work_area())

    def paintEvent(self, event):
        p = QPainter(self)
        if self.wallpaper.isNull():
            p.fillRect(self.rect(), QColor("#3A6EA5"))
            return
        if self._wall_scaled is None or self._wall_scaled.size() != self.size():
            self._wall_scaled = self.wallpaper.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        p.drawPixmap(0, 0, self._wall_scaled)

    # ---- icons --------------------------------------------------------------
    def select_icon(self, chosen):
        for icon in self.icons:
            if icon.selected != (icon is chosen):
                icon.selected = icon is chosen
                icon.update()

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
            self.select_icon(None)
            self.activate(None)
        elif isinstance(obj, DesktopIcon):
            self.activate(None)
