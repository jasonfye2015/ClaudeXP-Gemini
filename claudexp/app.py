"""ClaudeXP main window: the 'monitor' of the virtual PC."""
from PySide6.QtCore import QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from . import programs, sound
from .boot import BootScreen, ShutdownScreen
from .power import BiosScreen, SafeOffScreen
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
        self.bios = BiosScreen()
        self.safe_off = SafeOffScreen()
        self.stack.addWidget(self.bios)
        self.stack.addWidget(self.safe_off)
        self.stack.addWidget(self.boot)
        self.stack.addWidget(self.welcome)
        self.stack.addWidget(self.desktop)
        self.stack.addWidget(self.shutdown_screen)
        from .setup.gui import GuiSetup
        from .setup.oobe import Oobe
        from .setup.textmode import BootFromCD, RecoveryMenu, TextSetup
        self.recovery_menu = RecoveryMenu()
        self.boot_cd = BootFromCD()
        self.text_setup = TextSetup()
        self.gui_setup = GuiSetup()
        self.oobe = Oobe()
        for screen in (self.recovery_menu, self.boot_cd, self.text_setup, self.gui_setup, self.oobe):
            self.stack.addWidget(screen)
        self.recovery_menu.start_normally.connect(self._boot_hard_disk)
        self.recovery_menu.reinstall.connect(self._prompt_boot_cd)
        self.boot_cd.boot_cd.connect(self._text_setup)
        self.boot_cd.timed_out.connect(self._boot_hard_disk)
        self.text_setup.quit_setup.connect(self.start)
        self.text_setup.reboot.connect(self._setup_reboot)
        self.gui_setup.finished.connect(self._gui_setup_done)
        self.oobe.finished.connect(self._oobe_done)
        self._after_boot = self.show_welcome

        self.bios.finished.connect(self._windows_boot)
        self.boot.finished.connect(lambda: self._after_boot())
        self.safe_off.turn_off.connect(QApplication.quit)
        self.safe_off.restart.connect(self.restart_from_off)
        self.welcome.logged_on.connect(self.show_desktop)
        self.welcome.turn_off.connect(self.shut_down)
        self.desktop.shutdown_requested.connect(self.shut_down)
        self.desktop.logoff_requested.connect(self.log_off)
        self.desktop.restart_requested.connect(self.restart)
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
        from .screensaver import ScreenSaverManager
        self.locked = False
        self.screensaver = ScreenSaverManager(self)

    def start(self):
        """Power on: the BIOS self test, then Windows boots."""
        self.show()
        self.desktop.life.powered_off = False
        self.stack.setCurrentWidget(self.bios)
        self.bios.setFocus()
        self.bios.start()

    def _windows_boot(self):
        """After the BIOS: the recovery menu (SPACE), Setup still finishing, or Windows."""
        from . import setup
        if self.bios.recovery_requested:
            self.recovery_menu.reset()
            self._show_screen(self.recovery_menu)
        elif setup.stage() in ("gui", "oobe"):
            # The recovery CD is still in the drive: pressing a key now would start Setup over.
            self._prompt_boot_cd()
        else:
            self._boot_hard_disk()

    def _show_screen(self, screen):
        self.stack.setCurrentWidget(screen)
        screen.setFocus()

    def _boot_hard_disk(self):
        """The Windows XP boot screen, then whatever comes next (Setup, OOBE or the Welcome screen)."""
        from . import setup
        stage = setup.stage()
        self._after_boot = {"gui": self._start_gui_setup, "oobe": self._start_oobe}.get(stage, self.show_welcome)
        self._show_screen(self.boot)
        self.boot.start()

    # ---- System Recovery / reinstalling Windows ----------------------------------------------------------
    def _prompt_boot_cd(self):
        self._show_screen(self.boot_cd)
        self.boot_cd.start()

    def _text_setup(self):
        self.desktop.life.powered_off = False
        self._show_screen(self.text_setup)
        self.text_setup.start()

    def _setup_reboot(self, format_drive, program_history, memories):
        """The end of text-mode Setup: restart ClaudeXP for real (main.py wipes C: first)."""
        from . import setup
        programs.shutdown_all()
        setup.reboot_into_gui_setup(QApplication.instance(), format_drive, program_history, memories)

    def _start_gui_setup(self):
        self._show_screen(self.gui_setup)
        self.gui_setup.start()

    def _gui_setup_done(self, info):
        from . import setup
        setup.set_stage("oobe", **info)
        self._after_boot = self._start_oobe
        self.shutdown_screen.text = "Please wait..."
        self._show_screen(self.shutdown_screen)
        QTimer.singleShot(setup.ms(2500), self._restart_for_oobe)

    def _restart_for_oobe(self):
        self.shutdown_screen.text = "Windows is shutting down..."
        self._show_screen(self.boot)
        self.boot.start()

    def _start_oobe(self):
        from . import setup
        self._show_screen(self.oobe)
        self.oobe.start(setup.info().get("owner", ""))

    def _oobe_done(self, name):
        """Create the account from 'Who will use this computer?', then on to the Welcome screen."""
        from . import setup, user
        info = setup.info()
        user.new_account(name, owner=info.get("owner", name), organization=info.get("organization", ""),
                         computer=info.get("computer", ""))
        setup.finished()
        self._after_boot = self.show_welcome
        self.show_welcome()

    def show_welcome(self):
        self.welcome.reset()
        self.stack.setCurrentWidget(self.welcome)

    def lock(self):
        """Screen saver 'On resume, display Welcome screen': back to Welcome, programs stay open."""
        self.locked = True
        self.desktop.hide_start_menu()
        self.welcome.reset()
        self.stack.setCurrentWidget(self.welcome)

    def show_desktop(self):
        if self.locked:
            self.locked = False
            self.stack.setCurrentWidget(self.desktop)
            return
        self.stack.setCurrentWidget(self.desktop)
        sound.play("startup")
        # The world moved on while the PC was off: catch up in the background (Windows Update
        # or a virus scan will start to cover for it).
        QTimer.singleShot(1500, self.desktop.life.catch_up)

    def log_off(self):
        self.locked = False
        self.desktop.hide_start_menu()
        programs.shutdown_all()
        for win in list(self.desktop.windows):
            self.desktop.close_window(win)
        self.show_welcome()

    def shut_down(self):
        """Turn Off Computer: Windows shuts down to 'It's now safe to turn off your computer'.
        The PC stays on there, so buddies' lives keep moving until Turn off or Restart."""
        if self._shutting_down:
            return
        self._shutting_down = True
        self.locked = False
        programs.shutdown_all()
        self.desktop.hide_start_menu()
        for win in list(self.desktop.windows):
            self.desktop.close_window(win)
        self.stack.setCurrentWidget(self.shutdown_screen)
        sound.play("shutdown", self._safe_to_turn_off)

    def _safe_to_turn_off(self):
        self.desktop.life.powered_off = True
        self.stack.setCurrentWidget(self.safe_off)

    def restart_from_off(self):
        self._shutting_down = False
        self.start()

    def _exit(self):
        """Closing the real ClaudeXP window: shut down quickly and quit."""
        self._exiting = True
        if self.stack.currentWidget() is self.safe_off:
            QApplication.quit()
            return
        programs.shutdown_all()
        self.desktop.hide_start_menu()
        self.shutdown_screen.text = "Windows is shutting down..."
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
        # Closing the real window exits: play the shutdown first (a second close quits at once).
        if getattr(self, "_exiting", False) or self.stack.currentWidget() is self.safe_off:
            event.accept()
            QApplication.quit()
        else:
            event.ignore()
            self._exit()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
