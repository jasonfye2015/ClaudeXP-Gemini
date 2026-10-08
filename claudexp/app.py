"""ClaudeXP main window: the 'monitor' of the virtual PC."""
from PySide6.QtCore import QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from . import programs, sound
from .boot import BootScreen, ShutdownScreen
from .desktop import Desktop
from .welcome import WelcomeScreen


class ClaudeXP(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ClaudeXP")
        self.resize(1024, 768)
        self.setMinimumSize(800, 600)
        self._shutting_down = False

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.boot = BootScreen()
        self.welcome = WelcomeScreen()
        self.desktop = Desktop()
        self.shutdown_screen = ShutdownScreen()
        self.stack.addWidget(self.boot)
        self.stack.addWidget(self.welcome)
        self.stack.addWidget(self.desktop)
        self.stack.addWidget(self.shutdown_screen)

        self.boot.finished.connect(self.show_welcome)
        self.welcome.logged_on.connect(self.show_desktop)
        self.welcome.turn_off.connect(self.shut_down)
        self.desktop.shutdown_requested.connect(self.shut_down)
        self.desktop.logoff_requested.connect(self.log_off)
        self.desktop.restart_requested.connect(self.restart)
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)

    def start(self):
        self.show()
        self.stack.setCurrentWidget(self.boot)
        self.boot.setFocus()
        self.boot.start()

    def show_welcome(self):
        self.welcome.reset()
        self.stack.setCurrentWidget(self.welcome)

    def show_desktop(self):
        self.stack.setCurrentWidget(self.desktop)
        sound.play("startup")

    def log_off(self):
        self.desktop.hide_start_menu()
        programs.shutdown_all()
        for win in list(self.desktop.windows):
            self.desktop.close_window(win)
        self.show_welcome()

    def shut_down(self):
        if self._shutting_down:
            return
        self._shutting_down = True
        programs.shutdown_all()
        self.desktop.hide_start_menu()
        self.stack.setCurrentWidget(self.shutdown_screen)
        sound.play("shutdown", QApplication.quit)

    def restart(self):
        """Restart (after Windows Update): close everything, then boot again."""
        if self._shutting_down:
            return
        self._shutting_down = True
        programs.shutdown_all()
        self.desktop.hide_start_menu()
        for win in list(self.desktop.windows):
            self.desktop.close_window(win)
        self.shutdown_screen.text = "Windows is restarting..."
        self.stack.setCurrentWidget(self.shutdown_screen)

        def boot_again():
            self._shutting_down = False
            self.shutdown_screen.text = "Windows is shutting down..."
            self.start()

        sound.play("shutdown", lambda: QTimer.singleShot(1500, boot_again))

    def closeEvent(self, event):
        # Closing the real window counts as Turn Off: play the shutdown first.
        if self._shutting_down:
            event.accept()
            QApplication.quit()
        else:
            event.ignore()
            self.shut_down()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
