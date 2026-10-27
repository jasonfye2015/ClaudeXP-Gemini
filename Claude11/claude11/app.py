"""Claude11's main window: the monitor of WORKSTATION-2025. Power on -> the ASUS splash -> Windows -> the lock screen -> the desktop,
and the ways back out: sign out, lock, sleep, restart, shut down, reset."""
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget

from . import setup, sound
from .bios import BiosScreen, BiosSetup, BootOptions
from .boot import BootScreen, PoweredOffScreen, ShutdownScreen
from .desktop import Desktop
from .logon import LogonScreen


class SleepScreen(QWidget):
    """The monitor asleep: black until the mouse moves or a key is pressed."""

    def __init__(self, on_wake, parent=None):
        super().__init__(parent)
        self.on_wake = on_wake
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.moves = 0

    def showEvent(self, event):
        self.moves = 0
        self.setCursor(Qt.BlankCursor)

    def paintEvent(self, event):
        QPainter(self).fillRect(self.rect(), QColor("black"))

    def mouseMoveEvent(self, event):
        self.moves += 1
        if self.moves > 3:
            self._wake()

    def mousePressEvent(self, event):
        self._wake()

    def keyPressEvent(self, event):
        self._wake()

    def _wake(self):
        self.unsetCursor()
        self.on_wake()


class Claude11(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Claude11")
        self.resize(1366, 768)
        self.setMinimumSize(1024, 600)
        self._shutting_down = False
        self._logged_off = False
        self._first_logon = False
        self.locked = False
        from . import user
        if not user.USER_FILE.exists() and setup.stage() is None:
            setup.set_stage("oobe", fresh=True)          # a brand-new PC: Set Up Windows on the first boot
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.bios = BiosScreen()
        self.bios_setup = BiosSetup()
        self.boot_options = BootOptions()
        self.boot = BootScreen()
        self.logon = LogonScreen()
        self.desktop = Desktop()
        self.shutdown_screen = ShutdownScreen()
        self.powered_off = PoweredOffScreen()
        self.sleep_screen = SleepScreen(self._woken)
        from .setup.install import BootFromDvd, InstallWizard, LoadingFiles
        from .setup.oobe import Oobe
        self.boot_dvd = BootFromDvd()
        self.loading = LoadingFiles()
        self.install = InstallWizard()
        self.oobe = Oobe()
        for screen in (self.bios, self.bios_setup, self.boot_options, self.boot, self.logon, self.desktop,
                       self.shutdown_screen, self.powered_off, self.sleep_screen, self.boot_dvd, self.loading,
                       self.install, self.oobe):
            self.stack.addWidget(screen)
        self._after_boot = self.show_logon
        # wiring
        self.bios.finished.connect(self._windows_boot)
        self.bios.setup_requested.connect(self._bios_setup)
        self.bios.boot_menu_requested.connect(self._boot_menu)
        self.bios_setup.closed.connect(self._windows_boot)
        self.boot_options.start_normally.connect(self._boot_hard_disk)
        self.boot_options.safe_mode.connect(lambda: self._boot_hard_disk(safe=True))
        self.boot_options.reinstall.connect(self._install_windows)
        self.boot_options.restart.connect(lambda: self.start())
        self.boot_options.firmware.connect(self._bios_setup)
        self.boot_dvd.boot_dvd.connect(self._loading_files)
        self.boot_dvd.timed_out.connect(self._boot_hard_disk)
        self.loading.finished.connect(self._install_wizard)
        self.install.reboot.connect(self._setup_reboot)
        self.install.quit_setup.connect(lambda: self.start())
        self.oobe.finished.connect(self._oobe_done)
        self.boot.finished.connect(lambda: self._after_boot())
        self.logon.logged_on.connect(self.show_desktop)
        self.logon.shut_down.connect(self.shut_down)
        self.logon.restart.connect(self.restart)
        self.logon.sleep.connect(self.sleep)
        self.desktop.shutdown_requested.connect(self.shut_down)
        self.desktop.logoff_requested.connect(self.log_off)
        self.desktop.switch_user_requested.connect(self.lock)
        self.desktop.lock_requested.connect(self.lock)
        self.desktop.restart_requested.connect(self.restart)
        self.desktop.sleep_requested.connect(self.sleep)
        self.powered_off.turn_on.connect(lambda: self.start())
        self.powered_off.exit_app.connect(QApplication.quit)
        self.powered_off.recovery.connect(self._install_windows)
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
        QShortcut(QKeySequence("Ctrl+Alt+End"), self, self._task_manager)
        from . import alttab
        self.alttab = alttab.install(self)
        from .screensaver import ScreenSaverManager
        self.screensaver = ScreenSaverManager(self)

    # ---- power on ----
    def start(self, recovery=False):
        self.show()
        self._shutting_down = False
        self.desktop.life.powered_off = False
        self._show_screen(self.bios)
        self.bios.start(recovery=recovery)

    def _show_screen(self, screen):
        self.stack.setCurrentWidget(screen)
        screen.setFocus()

    def _windows_boot(self):
        if self.bios.recovery_requested and not self.bios.setup_wanted:
            self._boot_menu()
        else:
            self._boot_hard_disk()

    def _bios_setup(self):
        self.bios_setup.reset()
        self._show_screen(self.bios_setup)

    def _boot_menu(self):
        self.boot_options.reset()
        self._show_screen(self.boot_options)

    def _boot_hard_disk(self, safe=False):
        stage = setup.stage()
        self._after_boot = self._start_oobe if stage == "oobe" else self.show_logon
        self._show_screen(self.boot)
        self.boot.start(safe_mode=safe)

    # ---- reinstalling Windows ----
    def _install_windows(self):
        self._shutting_down = False
        self.desktop.life.powered_off = False
        self._show_screen(self.boot_dvd)
        self.boot_dvd.start()

    def _loading_files(self):
        self._show_screen(self.loading)
        self.loading.start()

    def _install_wizard(self):
        self._show_screen(self.install)
        self.install.start()

    def _setup_reboot(self, format_drive, program_history, memories):
        from claudexp import programs
        programs.shutdown_all()
        setup.reboot_into_oobe(QApplication.instance(), format_drive, program_history, memories)

    def _start_oobe(self):
        self.shutdown_screen.text = "Getting ready"
        self._show_screen(self.shutdown_screen)
        QTimer.singleShot(setup.ms(3000), self._oobe_pages)

    def _oobe_pages(self):
        from . import user
        self.oobe.start(user.user_name() if user.exists() else "")
        self._show_screen(self.oobe)

    def _oobe_done(self, chosen):
        from . import user
        user.new_account(chosen["name"], computer=chosen.get("computer"), picture=chosen.get("picture"),
                         handle=chosen.get("handle"), linked_=chosen.get("linked", True),
                         windows_password=chosen.get("windows_password") or None)
        if chosen.get("hint"):
            user.set_password_hint(chosen["hint"])
        if chosen.get("fursona"):
            try:
                from claudexp import fursonas
                preset = fursonas.get(chosen["fursona"])
                if preset is not None:
                    fursonas.apply(preset)
            except Exception:
                pass
        setup.finished()
        self._first_logon = True
        self._after_boot = self.show_logon
        self.shutdown_screen.text = "Hi"
        self._show_screen(self.shutdown_screen)
        QTimer.singleShot(setup.ms(1500), self.show_logon)

    # ---- logging on and off ----
    def show_logon(self, locked=False):
        lines = []
        if locked:
            n = len([w for w in self.desktop.windows if w.on_taskbar])
            if n:
                lines.append(f"{n} program{'s' if n != 1 else ''} running")
            try:
                mail = self.desktop.mailtray._unread()
                if mail:
                    lines.append(f"{mail} unread e-mail message{'s' if mail != 1 else ''}")
            except Exception:
                pass
        self.logon.reset(locked=locked, status_lines=lines)
        self._show_screen(self.logon)

    def lock(self):
        self.locked = True
        self.desktop.hide_start_menu()
        self.show_logon(locked=True)

    def sleep(self):
        self.desktop.hide_start_menu()
        self._show_screen(self.sleep_screen)

    def _woken(self):
        if self.stack.currentWidget() is self.sleep_screen:
            self.locked = True
            self.show_logon(locked=True)

    def show_desktop(self):
        if self.locked:
            self.locked = False
            self._show_screen(self.desktop)
            return
        self._show_screen(self.desktop)
        from . import volume
        volume.apply()
        sound.play("logon" if self._logged_off else "startup")
        self._logged_off = False
        QTimer.singleShot(1500, self.desktop.life.catch_up)
        from .programs import stickynotes, widgets
        QTimer.singleShot(600, lambda: widgets.start_at_logon(self.desktop))
        QTimer.singleShot(900, lambda: stickynotes.start_at_logon(self.desktop))
        try:
            from claudexp.programs import sysrestore
            QTimer.singleShot(2500, lambda: sysrestore.check_completed(self.desktop))
            QTimer.singleShot(8000, sysrestore.auto_checkpoint)
        except Exception:
            pass
        from claudexp.startup import enabled
        try:
            import claudeai
            if enabled("claudeai"):
                QTimer.singleShot(2000, lambda: claudeai.start_at_logon(self.desktop))
        except Exception:
            pass
        try:
            from claudexp import llm_loading, llm_logon
            llm_loading.start(self.desktop)
            QTimer.singleShot(1200, lambda: llm_logon.at_logon(self.desktop, warm=enabled("llm")))
        except Exception:
            pass
        try:
            from claudexp.programs import torrent
            if enabled("torrent"):
                QTimer.singleShot(2600, lambda: torrent.start_at_logon(self.desktop))
        except Exception:
            pass
        try:
            from claudexp.programs import neko
            if enabled("neko"):
                neko.start_at_logon(self.desktop)
        except Exception:
            pass
        try:
            from claudexp.programs import doggo
            if enabled("doggo"):
                QTimer.singleShot(3000, lambda: doggo.start_at_logon(self.desktop))
            if enabled("deskmario"):
                from claudexp.programs import deskmario
                QTimer.singleShot(3500, lambda: deskmario.start_at_logon(self.desktop))
        except Exception:
            pass
        try:
            from claudexp.programs import msconfig
            QTimer.singleShot(4500, lambda: self.desktop.isVisible() and msconfig.at_logon(self.desktop))
        except Exception:
            pass
        try:
            from claudexp.programs.navigator.sites import activity as furry_web_activity
            QTimer.singleShot(15000, lambda: furry_web_activity.start(self.desktop))
        except Exception:
            pass
        if self._first_logon:
            self._first_logon = False
            QTimer.singleShot(5000, self._getting_started)

    def _getting_started(self):
        if self.stack.currentWidget() is self.desktop:
            from .programs.helpctr import open_help
            open_help(self.desktop, "claude11-about")

    def log_off(self):
        from claudexp import programs
        self.locked = False
        self.desktop.hide_start_menu()
        programs.shutdown_all()
        from .programs import stickynotes, widgets
        widgets.hide_all(self.desktop)
        stickynotes.hide_all(self.desktop)
        for win in list(self.desktop.windows):
            self.desktop.close_window(win)
        self.shutdown_screen.text = "Signing out"
        self._show_screen(self.shutdown_screen)
        sound.play("logoff")
        self._logged_off = True
        QTimer.singleShot(1400, self.show_logon)

    # ---- shutting down ----
    def _close_everything(self):
        from claudexp import programs
        programs.shutdown_all()
        self.desktop.hide_start_menu()
        from .programs import stickynotes, widgets
        widgets.hide_all(self.desktop)
        stickynotes.hide_all(self.desktop)
        for win in list(self.desktop.windows):
            self.desktop.close_window(win)

    def shut_down(self):
        if self._shutting_down:
            return
        self._shutting_down = True
        self.locked = False
        self._close_everything()
        self.shutdown_screen.text = "Shutting down"
        self._show_screen(self.shutdown_screen)
        sound.play("shutdown", lambda: QTimer.singleShot(800, self._off))

    def _off(self):
        self.desktop.life.powered_off = True
        self._show_screen(self.powered_off)

    def restart(self, recovery=False):
        if self._shutting_down:
            return
        self._shutting_down = True
        self.locked = False
        self._close_everything()
        self.shutdown_screen.text = "Restarting"
        self._show_screen(self.shutdown_screen)

        def boot_again():
            self._shutting_down = False
            self.shutdown_screen.text = "Shutting down"
            self.start(recovery=recovery)
        sound.play("shutdown", lambda: QTimer.singleShot(1200, boot_again))

    def _exit(self):
        self._exiting = True
        if self.stack.currentWidget() is self.powered_off:
            QApplication.quit()
            return
        self._close_everything()
        self.shutdown_screen.text = "Shutting down"
        self._show_screen(self.shutdown_screen)
        sound.play("shutdown", QApplication.quit)

    def closeEvent(self, event):
        if getattr(self, "_exiting", False) or self.stack.currentWidget() is self.powered_off:
            event.accept()
            QApplication.quit()
        else:
            event.ignore()
            self._exit()

    def _task_manager(self):
        if self.stack.currentWidget() is self.desktop:
            from claudexp import programs
            programs.launch(self.desktop, "taskmgr")

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
