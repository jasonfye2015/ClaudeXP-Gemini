from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QStyleFactory,
)

from .config import (
    ensure_storage_folders,
    load_bios_password_hashes_with_status,
    load_bios_settings,
    recover_interrupted_bios_password_recovery,
    reset_user_data,
)
from .desktop import DesktopPage
from .identity import (
    AccountStoreError,
    UserAccount,
    load_account,
    save_account,
)
from .screens import (
    BiosScreen,
    ErrorScreen,
    LoginScreen,
    SetupWizard,
    ShutdownScreen,
    UserSelectionScreen,
    WindowsStartScreen,
)
from .theme import APPLICATION_STYLE


class SimulationWindow(QMainWindow):
    """Owns the boot → setup/login → desktop → shutdown state transitions."""

    def __init__(
        self,
        parent=None,
        *,
        boot_drive_present: bool = True,
        bootable_dvd_present: bool = False,
        bootable_usb_present: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Windows 7: 2011")
        self.setMinimumSize(960, 600)
        self.setObjectName("simulationWindow")
        self.stack = QStackedWidget(self)
        self.stack.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.stack)

        self.account: UserAccount | None = None
        self._bios_settings: dict[str, list[int]] = {}
        self._bios_password_hashes: dict[str, str] = {}
        self._bios_passwords_available = True
        self._bios_recovery_status: str | None = None
        self._bios_settings_warning: str | None = None
        self._load_error: str | None = None
        self._stage = "starting"
        self._shutting_down = False
        self._allow_close = False
        self._fast_boot = os.environ.get("WIN7_SIM_FAST_BOOT") == "1"
        self._boot_drive_present = boot_drive_present
        self._bootable_dvd_present = bootable_dvd_present
        self._bootable_usb_present = bootable_usb_present
        self._shutdown_safe_delay = 100 if self._fast_boot else 3000

        try:
            ensure_storage_folders()
            self._bios_recovery_status = (
                recover_interrupted_bios_password_recovery()
            )
            self.account = load_account()
        except (AccountStoreError, OSError, ValueError) as exc:
            self._load_error = str(exc)

        try:
            (
                self._bios_password_hashes,
                password_recovery_status,
            ) = load_bios_password_hashes_with_status()
            if password_recovery_status:
                self._bios_recovery_status = "; ".join(
                    status
                    for status in (
                        password_recovery_status,
                        self._bios_recovery_status,
                    )
                    if status
                )
        except (OSError, ValueError) as exc:
            self._bios_passwords_available = False
            self._load_error = self._load_error or str(exc)

        self._fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        self._fullscreen_shortcut.activated.connect(self._toggle_fullscreen)
        self._show_bios()

    def _set_page(self, page) -> None:
        current = self.stack.currentWidget()
        if current is not None:
            self.stack.removeWidget(current)
            current.deleteLater()
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def _show_bios(self) -> None:
        # A new boot must use choices saved or restored during this process,
        # not the startup snapshot (including an obsolete damage warning).
        self._bios_settings_warning = None
        try:
            self._bios_settings = load_bios_settings()
        except (OSError, ValueError):
            self._bios_settings = {}
            self._bios_settings_warning = (
                "Saved BIOS settings could not be loaded; defaults are being used."
            )
        self._stage = "bios"
        screen = BiosScreen(
            fast_boot=self._fast_boot,
            auto_start=False,
            boot_drive_present=self._boot_drive_present,
            bootable_dvd_present=self._bootable_dvd_present,
            bootable_usb_present=self._bootable_usb_present,
            settings=self._bios_settings,
            password_hashes=self._bios_password_hashes,
            passwords_available=self._bios_passwords_available,
            recovery_status=self._bios_recovery_status,
            settings_warning=self._bios_settings_warning,
        )
        screen.advanceRequested.connect(self._skip_bios)
        screen.postComplete.connect(self._show_windows_start)
        screen.setupClosed.connect(self._show_windows_start)
        self._set_page(screen)
        if not self._fast_boot:
            self._play_bios_sound()
        screen.start_post()

    def _skip_bios(self) -> None:
        if self._stage != "bios":
            return
        screen = self.stack.currentWidget()
        if not isinstance(screen, BiosScreen) or not screen.post_complete:
            return
        self._stop_bios_sound()
        self._show_windows_start()

    def _stop_bios_sound(self) -> None:
        if sys.platform != "win32":
            return
        import winsound

        try:
            winsound.PlaySound(None, 0)
        except (RuntimeError, OSError) as exc:
            print(f"Could not stop BIOS boot sound: {exc}", file=sys.stderr)

    def _play_bios_sound(self) -> None:
        sound_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "bios"
            / "boot-post.wav"
        )
        if not sound_path.is_file():
            print(f"BIOS boot sound is missing: {sound_path}", file=sys.stderr)
            return
        if sys.platform != "win32":
            return

        import winsound

        try:
            winsound.PlaySound(
                str(sound_path),
                winsound.SND_FILENAME | winsound.SND_ASYNC,
            )
        except (RuntimeError, OSError) as exc:
            print(f"Could not play BIOS boot sound: {exc}", file=sys.stderr)

    def _show_windows_start(self) -> None:
        if self._stage != "bios":
            return
        screen = self.stack.currentWidget()
        if isinstance(screen, BiosScreen) and screen.setup_open:
            return
        if isinstance(screen, BiosScreen) and not screen.post_complete:
            return
        if isinstance(screen, BiosScreen) and screen.selected_boot_source is None:
            return
        if (
            not self._load_error
            and isinstance(screen, BiosScreen)
            and not screen.authorize_startup()
        ):
            return
        self._stop_bios_sound()
        self._stage = "windows-start"
        try:
            screen = WindowsStartScreen(
                loop_count=0 if self._fast_boot else 3,
                frame_interval_ms=12 if self._fast_boot else 50,
            )
        except (OSError, RuntimeError) as exc:
            self._show_error(str(exc))
            return
        screen.finished.connect(self._continue_startup)
        self._set_page(screen)

    def _continue_startup(self) -> None:
        if self._stage != "windows-start":
            return
        if self._load_error:
            self._show_error(self._load_error)
        elif self.account is None:
            self._show_setup()
        else:
            self._show_login()

    def _show_setup(self) -> None:
        self._stage = "setup"
        wizard = SetupWizard()
        wizard.accountCreated.connect(self._account_created)
        self._set_page(wizard)

    def _account_created(self, account: UserAccount) -> None:
        account.active_profile_id = account.fursonas[0].profile_id
        try:
            ensure_storage_folders()
            save_account(account)
        except (AccountStoreError, OSError) as exc:
            self._show_error(str(exc))
            return
        self.account = account
        self._show_login()

    def _show_login(self) -> None:
        if self.account is None:
            self._show_error("No local account is available.")
            return
        self._stage = "login"
        screen = LoginScreen(self.account)
        screen.loginRequested.connect(self._start_desktop)
        screen.restartRequested.connect(self._restart_from_login)
        screen.shutdownRequested.connect(self._begin_shutdown)
        screen.switchUserRequested.connect(self._show_user_selection)
        self._set_page(screen)

    def _show_user_selection(self) -> None:
        if self._stage != "login" or self.account is None:
            return
        try:
            screen = UserSelectionScreen(self.account)
        except (FileNotFoundError, RuntimeError) as exc:
            self._show_error(str(exc))
            return
        self._stage = "user-selection"
        screen.profileSelected.connect(self._select_user_profile)
        screen.soundRequested.connect(self._play_user_selection_sound)
        screen.restartRequested.connect(self._restart_from_login)
        screen.shutdownRequested.connect(self._begin_shutdown)
        self._set_page(screen)

    def _select_user_profile(self, profile_id: str) -> None:
        if self._stage != "user-selection" or self.account is None:
            return

        profile = self.account.profile_by_id(profile_id)
        if profile is None:
            self._show_error("The selected fursona is not part of this account.")
            return
        previous_profile_id = self.account.active_profile_id
        self.account.active_profile_id = profile.profile_id
        try:
            save_account(self.account)
        except AccountStoreError as exc:
            self.account.active_profile_id = previous_profile_id
            self._show_error(str(exc))
            return
        self._show_login()

    def _play_user_selection_sound(self, filename: str) -> None:
        if filename not in {"User_Highlight.wav", "User_Select.wav"}:
            return
        sound_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "user-selection"
            / filename
        )
        if not sound_path.is_file():
            print(f"User-selection sound is missing: {sound_path}", file=sys.stderr)
            return
        if sys.platform != "win32":
            return
        import winsound

        try:
            winsound.PlaySound(
                str(sound_path),
                winsound.SND_FILENAME | winsound.SND_ASYNC,
            )
        except (RuntimeError, OSError) as exc:
            print(f"Could not play user-selection sound: {exc}", file=sys.stderr)

    def _restart_from_login(self) -> None:
        if self._stage not in {"login", "user-selection"}:
            return
        self._show_bios()

    def _start_desktop(self, profile_id: str) -> None:
        if self.account is None or self.account.profile_by_id(profile_id) is None:
            self._show_error("The selected fursona is not part of this account.")
            return
        self.account.active_profile_id = profile_id
        try:
            save_account(self.account)
        except AccountStoreError as exc:
            self._show_error(str(exc))
            return

        self._stage = "desktop"
        try:
            desktop = DesktopPage(self.account)
        except (FileNotFoundError, RuntimeError) as exc:
            self._show_error(str(exc))
            return
        desktop.shutdownRequested.connect(self._begin_shutdown)
        desktop.formatReinstallRequested.connect(self._format_and_reinstall)
        desktop.logOffRequested.connect(self._log_off)
        self._set_page(desktop)
        QTimer.singleShot(0, lambda: self._refresh_saved_ai_servers(desktop))
        QTimer.singleShot(0, self._play_startup_sound)

    def _refresh_saved_ai_servers(self, desktop: DesktopPage) -> None:
        if (
            self._stage != "desktop"
            or self.stack.currentWidget() is not desktop
            or desktop.ai_service.load_error
            or not desktop.ai_service.can_reconnect
        ):
            return
        try:
            desktop.ai_service.reconnect()
        except (RuntimeError, ValueError) as exc:
            desktop.ai_service._status(
                f"Could not refresh saved servers after login: {exc}", True
            )

    def _log_off(self) -> None:
        if self._stage != "desktop":
            return
        current = self.stack.currentWidget()
        if isinstance(current, DesktopPage):
            if not current.confirm_session_end("log off"):
                return
            current.stop_session()
        self._show_login()

    def _play_startup_sound(self) -> None:
        if self._stage != "desktop":
            return
        sound_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "boot"
            / "windows-7-startup.wav"
        )
        if not sound_path.is_file():
            print(f"Windows startup sound is missing: {sound_path}", file=sys.stderr)
            return
        if sys.platform != "win32":
            print(
                "Windows startup sound playback is only available on Windows.",
                file=sys.stderr,
            )
            return

        import winsound

        try:
            winsound.PlaySound(
                str(sound_path),
                winsound.SND_FILENAME | winsound.SND_ASYNC,
            )
        except (RuntimeError, OSError) as exc:
            print(f"Could not play Windows startup sound: {exc}", file=sys.stderr)

    def _format_and_reinstall(self) -> None:
        current = self.stack.currentWidget()
        if isinstance(current, DesktopPage):
            if not current.confirm_session_end("format and reinstall"):
                return
        try:
            reset_user_data()
        except OSError as exc:
            self._show_error(f"Could not safely format user data: {exc}")
            return
        self.account = None
        # The destructive reset was already approved. Do not offer to save old
        # in-memory chats back into the freshly erased storage during shutdown.
        self._begin_shutdown(confirm_unsaved=False)

    def _begin_shutdown(self, *, confirm_unsaved: bool = True) -> None:
        if self._shutting_down:
            return
        current = self.stack.currentWidget()
        if isinstance(current, DesktopPage):
            if confirm_unsaved and not current.confirm_session_end("shut down"):
                return
            current.stop_session()
        self._stage = "shutdown"
        self._shutting_down = True
        screen = ShutdownScreen(safe_delay_ms=self._shutdown_safe_delay)
        screen.restartRequested.connect(self._restart_pc)
        screen.endProgramRequested.connect(self._finish_shutdown)
        screen.recoveryRequested.connect(self._enter_recovery_mode)
        self._set_page(screen)
        self._play_shutdown_sound()

    def _play_shutdown_sound(self) -> None:
        sound_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "shutdown"
            / "windows-shutdown.wav"
        )
        if not sound_path.is_file():
            print(f"Windows shutdown sound is missing: {sound_path}", file=sys.stderr)
            return
        if sys.platform != "win32":
            return

        import winsound

        try:
            winsound.PlaySound(
                str(sound_path),
                winsound.SND_FILENAME | winsound.SND_ASYNC,
            )
        except (RuntimeError, OSError) as exc:
            print(f"Could not play Windows shutdown sound: {exc}", file=sys.stderr)

    def _restart_pc(self) -> None:
        if self._stage != "shutdown":
            return
        self._shutting_down = False
        self._show_bios()

    def _enter_recovery_mode(self) -> None:
        if self._stage != "shutdown":
            return
        if self.account is not None:
            answer = QMessageBox.question(
                self,
                "Start Recovery Mode?",
                "Recovery Mode permanently removes the Windows account, fursona "
                "profiles and their local images, saved personal documents and "
                "Sticky Notes, saved Media Player playlists, and Messenger "
                "conversations in Storage/UserData/Messenger, screen-saver "
                "preferences in Storage/UserData/Screen Saver, and private "
                "per-fursona LLM activity logs. "
                "Preinstalled programs and Storage/Media, Storage/ROMs, and "
                "Storage/Models will be kept. Saved playlists in "
                "Storage/UserData/Media Player Playlists will be erased.\n\n"
                "To keep your saved chats, choose No, use Restart PC without "
                "Recovery Mode, and open Windows Live Messenger after signing "
                "in. Use “Export all saved chats…” for each fursona, or "
                "“Export saved conversation…” for one contact. Save the "
                "export outside Storage before continuing.\n"
                "To keep the LLM log, export it from the hard-drive activity "
                "icon on the taskbar and save it outside Storage.\n\n"
                "If you are formatting the real computer, copy the backup "
                "to another drive first; a file on the drive being formatted "
                "will also be erased.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            try:
                reset_user_data()
            except OSError as exc:
                self._show_error(f"Could not safely format user data: {exc}")
                return
            self.account = None
        self._restart_pc()

    def _finish_shutdown(self) -> None:
        self._allow_close = True
        self.close()
        QApplication.instance().quit()

    def _show_error(self, message: str) -> None:
        self._stage = "error"
        screen = ErrorScreen(message)
        screen.closeRequested.connect(self.close)
        self._set_page(screen)

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if self._stage == "desktop" and not self._allow_close:
            event.ignore()
            self._begin_shutdown()
            return
        event.accept()


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Windows 7: 2011")
    app.setOrganizationName("Private Local Simulation")
    app.setFont(QFont("Segoe UI", 10))
    available_styles = {style.lower(): style for style in QStyleFactory.keys()}
    if "windowsvista" in available_styles:
        app.setStyle(available_styles["windowsvista"])
    else:
        app.setStyle("Fusion")
    app.setStyleSheet(APPLICATION_STYLE)

    window = SimulationWindow()
    window.showFullScreen()
    return app.exec()
