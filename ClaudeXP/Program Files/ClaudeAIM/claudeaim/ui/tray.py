"""System tray icon: flashes while messages are waiting, click to open them."""
from PySide6.QtCore import QObject, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from .. import host, paths

FLASH_MS = 600
NOTE = "\U0001F4DD"


def _tray_pixmaps():
    """The running man, and the running man with a message note in the corner."""
    size = 64
    base = QPixmap(paths.image("buddyicon.jpg")).scaled(
        size, size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    alert = QPixmap(base)
    painter = QPainter(alert)
    painter.setFont(QFont("Segoe UI Emoji", 26))
    painter.drawText(QRect(size // 3, size // 3, size * 2 // 3, size * 2 // 3), Qt.AlignCenter, NOTE)
    painter.end()
    return base, alert


class Tray(QObject):
    open_list = Signal()
    open_im = Signal(str)
    away_requested = Signal()
    back_requested = Signal()
    exit_requested = Signal()

    def __init__(self, settings, world, parent=None):
        super().__init__(parent)
        self.settings, self.world = settings, world
        base, alert = _tray_pixmaps()
        self.icon_normal, self.icon_alert = QIcon(base), QIcon(alert)
        self.flash_on = False
        self.told_about_tray = False

        self.tray = host.tray_icon(self.icon_normal, self)
        menu = QMenu()
        open_action = QAction("Open Buddy List", menu)
        open_action.triggered.connect(self.open_list)
        menu.addAction(open_action)
        self.away_action = QAction("", menu)
        self.away_action.triggered.connect(self._away_clicked)
        menu.addAction(self.away_action)
        menu.addSeparator()
        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self.exit_requested)
        menu.addAction(exit_action)
        menu.setDefaultAction(open_action)
        self.menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._activated)

        self.flash_timer = QTimer(self)
        self.flash_timer.setInterval(FLASH_MS)
        self.flash_timer.timeout.connect(self._flash)

        world.unread_changed.connect(self.refresh)
        world.user_away_changed.connect(self.refresh)
        self.refresh()
        self.tray.show()

    @staticmethod
    def available():
        return host.tray_available()

    def _waiting(self):
        return [b for b in self.world.buddies.values() if b.history.unread]

    def refresh(self, *_):
        waiting = self._waiting()
        name = self.settings["screen_name"]
        tip = f"ClaudeAIM - {name}" + (" *Away*" if self.world.user_away else "")
        if len(waiting) == 1:
            tip += f"\n{waiting[0].name} has a message waiting"
        elif waiting:
            tip += f"\nMessages waiting from {', '.join(b.name for b in waiting)}"
        self.tray.setToolTip(tip)
        self.away_action.setText("I'm Back" if self.world.user_away else "Set Away Status...")
        if waiting and not self.flash_timer.isActive():
            self.flash_timer.start()
        elif not waiting:
            self.flash_timer.stop()
            self.flash_on = False
            self.tray.setIcon(self.icon_normal)

    def _flash(self):
        self.flash_on = not self.flash_on
        self.tray.setIcon(self.icon_alert if self.flash_on else self.icon_normal)

    def _activated(self, reason):
        if reason not in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            return
        waiting = self._waiting()
        if waiting:
            self.open_im.emit(waiting[0].id)
        else:
            self.open_list.emit()

    def _away_clicked(self):
        if self.world.user_away:
            self.back_requested.emit()
        else:
            self.away_requested.emit()

    def tell_still_running(self):
        """One gentle notice per session the first time the Buddy List is closed."""
        if not self.told_about_tray:
            self.told_about_tray = True
            self.tray.showMessage("ClaudeAIM is still running",
                                  "Your buddies can still message you. Click the icon to open "
                                  "your Buddy List, or right-click it to exit.",
                                  self.icon_normal, 5000)

    def hide(self):
        self.flash_timer.stop()
        self.tray.hide()
