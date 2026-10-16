from __future__ import annotations

import zipfile
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPixmap,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .config import (
    STORAGE_ROOT,
    hash_bios_password,
    load_bios_settings_backup,
    recover_bios_password,
    restore_bios_settings,
    save_bios_password_hashes,
    save_bios_settings,
    verify_bios_password,
)
from .identity import FursonaProfile, UserAccount, validate_account


class BiosScreen(QWidget):
    """Render the AMI POST and its keyboard-navigable setup utility."""

    advanceRequested = Signal()
    postComplete = Signal()
    setupClosed = Signal()
    BOOT_FAILURE_MESSAGE = "ERROR: No bootable device found"
    CPU_CHECK_DELAY_MS = 300
    USB_CHECK_DELAY_MS = 1300
    SATA_PORT_1_CHECK_DELAY_MS = 2300
    SATA_PORT_2_CHECK_DELAY_MS = 3300
    MEMORY_CHECK_DELAY_MS = 6500
    CANVAS_WIDTH = 640
    CANVAS_HEIGHT = 480
    SETUP_GROUPS = (
        ("Setup", (
            ("Standard", "standard"),
            ("Advanced", "advanced"),
            ("Chipset", "chipset"),
            ("Power Mgmt", "power"),
        )),
        ("Utility", (
            ("Detect C", "detect_c"),
            ("Detect D", "detect_d"),
            ("Color Set", "colors"),
        )),
        ("Security", (
            ("Password", "password"),
            ("Anti-Virus", "antivirus"),
        )),
        ("Default", (
            ("Original", "original"),
            ("Optimal", "optimal"),
            ("Fail-Safe", "fail_safe"),
        )),
    )
    SETUP_PAGES = {
        "standard": (
            "STANDARD CMOS SETUP",
            (
                ("Date", ("01/01/2011", "01/02/2011", "01/03/2011")),
                ("Time", ("12:00:00", "12:30:00", "18:00:00")),
                ("Floppy Drive A", ("1.44 MB 3½-inch", "Not Installed")),
                ("Primary Master", ("1 TB SATA Hard Disk", "Not Installed")),
                ("Primary Slave", ("Not Installed", "1 TB SATA Hard Disk")),
                ("Secondary Master", ("ATAPI DVD-ROM", "Not Installed")),
                ("Secondary Slave", ("Not Installed", "ATAPI DVD-ROM")),
            ),
        ),
        "advanced": (
            "ADVANCED BIOS FEATURES",
            (
                ("CPU", ("Intel Core i7-2600K @ 3.40GHz",)),
                ("Intel SpeedStep", ("Enabled", "Disabled")),
                ("Intel Virtualization Tech", ("Enabled", "Disabled")),
                ("Boot Device Priority", ("Hard Disk, DVD-ROM, USB", "DVD-ROM, Hard Disk, USB")),
                ("Quick Boot", ("Enabled", "Disabled")),
            ),
        ),
        "chipset": (
            "CHIPSET CONFIGURATION",
            (
                ("North Bridge", ("Intel P67 Express",)),
                ("Primary Display Adapter", ("PCI Express", "Onboard")),
                ("DRAM Frequency", ("Auto", "DDR3-1333", "DDR3-1600")),
                ("Memory Remap Feature", ("Enabled", "Disabled")),
            ),
        ),
        "power": (
            "POWER MANAGEMENT SETUP",
            (
                ("ACPI 2.0 Support", ("Enabled", "Disabled")),
                ("Suspend Mode", ("S3 (STR)", "S1 (POS)", "Disabled")),
                ("Restore on AC Power Loss", ("Power Off", "Power On", "Last State")),
                ("Wake on Keyboard", ("Disabled", "Enabled")),
            ),
        ),
        "colors": (
            "COLOR SET",
            (("Setup screen colors", ("Gray / Magenta", "Blue / White", "Black / Green")),),
        ),
        "password": (
            "SECURITY PASSWORD",
            (
                ("Supervisor Password", ("Not Installed", "Installed")),
                ("User Password", ("Not Installed", "Installed")),
            ),
        ),
        "antivirus": (
            "ANTI-VIRUS PROTECTION",
            (("Boot Sector Virus Protection", ("Disabled", "Enabled")),),
        ),
    }
    SETUP_PRESETS = {
        "original": {
            "standard": (0, 0, 0, 0, 0, 0, 0),
            "advanced": (0, 0, 0, 0, 0),
            "chipset": (0, 0, 0, 0),
            "power": (0, 0, 0, 0),
            "colors": (0,),
            "antivirus": (0,),
        },
        "optimal": {
            "standard": (0, 0, 0, 0, 0, 0, 0),
            "advanced": (0, 0, 0, 0, 0),
            "chipset": (0, 0, 2, 0),
            "power": (0, 0, 0, 0),
            "colors": (0,),
            "antivirus": (0,),
        },
        "fail_safe": {
            "standard": (0, 0, 1, 0, 0, 1, 0),
            "advanced": (0, 1, 1, 1, 1),
            "chipset": (0, 1, 1, 1),
            "power": (1, 1, 2, 0),
            "colors": (0,),
            "antivirus": (1,),
        },
    }

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        fast_boot: bool = False,
        auto_start: bool = True,
        boot_drive_present: bool = True,
        bootable_dvd_present: bool = False,
        bootable_usb_present: bool = False,
        settings: dict[str, list[int]] | None = None,
        password_hashes: dict[str, str] | None = None,
        passwords_available: bool = True,
        recovery_status: str | None = None,
        settings_warning: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("biosScreen")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(640, 480)
        self.setStyleSheet("#biosScreen { background-color: black; }")
        assets = Path(__file__).resolve().parent.parent / "assets" / "bios"
        self._ami_logo = QPixmap(str(assets / "amibios-logo.jpg"))
        self._energy_star_logo = QPixmap(str(assets / "energystar-logo.jpg"))
        self._gemma_logo = QPixmap(str(assets / "gemma4-logo.jpg"))
        self._gemini_logo = QPixmap(str(assets / "gemini-star-logo.jpg"))
        if (
            self._ami_logo.isNull()
            or self._energy_star_logo.isNull()
            or self._gemma_logo.isNull()
            or self._gemini_logo.isNull()
        ):
            raise RuntimeError(f"Could not load BIOS logo assets from {assets}")

        self._cpu_check_complete = False
        self._usb_check_complete = False
        self._sata_port_1_check_complete = False
        self._sata_port_2_check_complete = False
        self._boot_drive_present = boot_drive_present
        self._boot_drive_detected = False
        self._dvd_drive_detected = False
        self._bootable_dvd_present = bootable_dvd_present
        self._bootable_dvd_detected = False
        self._bootable_usb_present = bootable_usb_present
        self._bootable_usb_detected = False
        self._selected_boot_source: str | None = None
        self._memory_test_complete = False
        self._post_complete = False
        self._fast_boot = fast_boot
        self._post_timers: list[QTimer] = []
        self._setup_open = False
        self._setup_group = 0
        self._setup_item_indices = [0] * len(self.SETUP_GROUPS)
        self._setup_page: str | None = None
        self._setup_page_item = 0
        self._setup_values = {
            key: [0] * len(rows)
            for key, (_title, rows) in self.SETUP_PAGES.items()
        }
        self._password_hashes = dict(password_hashes or {})
        self._passwords_available = passwords_available
        self._settings_warning = settings_warning
        if not self._load_setup_values(settings or {}):
            self._settings_warning = (
                "Saved BIOS settings are invalid; defaults are being used."
            )
        self._sync_password_statuses()
        self._paused_post_timers: dict[QTimer, int] = {}
        self._setup_status = (
            recovery_status
            or self._settings_warning
            or "Use arrow keys to select an item; press Enter."
        )
        self._setup_texture = QPixmap(4, 4)
        self._setup_texture.fill(QColor("#b0b0b0"))
        texture_painter = QPainter(self._setup_texture)
        texture_painter.fillRect(0, 0, 1, 1, QColor("#a7a7a7"))
        texture_painter.fillRect(2, 2, 1, 1, QColor("#a7a7a7"))
        texture_painter.end()
        if auto_start:
            self.start_post()

    def start_post(self) -> None:
        """Begin the hardware checks after the POST sound has been queued."""
        if self._post_timers or self._post_complete:
            return

        checks = (
            (self.CPU_CHECK_DELAY_MS, self._complete_cpu_check),
            (self.USB_CHECK_DELAY_MS, self._complete_usb_check),
            (self.SATA_PORT_1_CHECK_DELAY_MS, self._complete_sata_port_1_check),
            (self.SATA_PORT_2_CHECK_DELAY_MS, self._complete_sata_port_2_check),
            (self.MEMORY_CHECK_DELAY_MS, self._complete_memory_test),
        )
        for index, (delay_ms, callback) in enumerate(checks, start=1):
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.setInterval(index if self._fast_boot else delay_ms)
            timer.timeout.connect(callback)
            timer.start()
            self._post_timers.append(timer)

    @property
    def cpu_check_complete(self) -> bool:
        return self._cpu_check_complete

    @property
    def usb_check_complete(self) -> bool:
        return self._usb_check_complete

    @property
    def sata_port_1_check_complete(self) -> bool:
        return self._sata_port_1_check_complete

    @property
    def sata_port_2_check_complete(self) -> bool:
        return self._sata_port_2_check_complete

    @property
    def memory_test_complete(self) -> bool:
        return self._memory_test_complete

    @property
    def boot_drive_detected(self) -> bool:
        return self._boot_drive_detected

    @property
    def bootable_dvd_detected(self) -> bool:
        return self._bootable_dvd_detected

    @property
    def bootable_usb_detected(self) -> bool:
        return self._bootable_usb_detected

    @property
    def selected_boot_source(self) -> str | None:
        return self._selected_boot_source

    @property
    def post_complete(self) -> bool:
        return self._post_complete

    @property
    def setup_open(self) -> bool:
        return self._setup_open

    def _pause_post_timers(self) -> None:
        self._paused_post_timers.clear()
        for timer in self._post_timers:
            if timer.isActive():
                self._paused_post_timers[timer] = max(1, timer.remainingTime())
                timer.stop()

    def _resume_post_timers(self) -> None:
        for timer, remaining_ms in self._paused_post_timers.items():
            if not self._post_complete:
                timer.start(remaining_ms)
        self._paused_post_timers.clear()

    def _complete_cpu_check(self) -> None:
        self._cpu_check_complete = True
        self.update()

    def _complete_usb_check(self) -> None:
        self._usb_check_complete = True
        self._bootable_usb_detected = self._bootable_usb_present
        self.update()

    def _complete_sata_port_1_check(self) -> None:
        self._sata_port_1_check_complete = True
        self._boot_drive_detected = (
            self._boot_drive_present
            and self._configured_drive_present(
                (3, 4),
                "1 TB SATA Hard Disk",
            )
        )
        self.update()

    def _complete_sata_port_2_check(self) -> None:
        self._sata_port_2_check_complete = True
        self._dvd_drive_detected = self._configured_drive_present(
            (5, 6),
            "ATAPI DVD-ROM",
        )
        self._bootable_dvd_detected = (
            self._bootable_dvd_present and self._dvd_drive_detected
        )
        self.update()

    def _configured_drive_present(
        self,
        slot_indices: tuple[int, int],
        drive_name: str,
    ) -> bool:
        """Return whether a BIOS master/slave slot is configured for this drive."""
        rows = self.SETUP_PAGES["standard"][1]
        values = self._setup_values["standard"]
        return any(
            rows[index][1][values[index]] == drive_name
            for index in slot_indices
        )

    def _complete_memory_test(self) -> None:
        if self._post_complete:
            return
        self._memory_test_complete = True
        self._selected_boot_source = self._select_boot_source()
        self._post_complete = True
        self.update()
        self.postComplete.emit()

    def _select_boot_source(self) -> str | None:
        """Choose the first detected bootable device in the configured order."""
        priority_options = self.SETUP_PAGES["advanced"][1][3][1]
        priority = priority_options[self._setup_values["advanced"][3]].split(", ")
        bootable_sources = {
            "Hard Disk": self._boot_drive_detected,
            "DVD-ROM": self._bootable_dvd_detected,
            "USB": self._bootable_usb_detected,
        }
        return next(
            (source for source in priority if bootable_sources[source]),
            None,
        )

    def showEvent(self, event) -> None:  # noqa: N802 - Qt event name
        super().showEvent(event)
        self.setFocus(Qt.FocusReason.OtherFocusReason)

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if self._setup_open:
            self._handle_setup_key(event)
            return
        if event.key() == Qt.Key.Key_F8:
            self._recover_bios_password()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Delete:
            if not self._passwords_available:
                self._setup_status = (
                    "Neither BIOS password file could be verified; setup is locked. "
                    "Restore a valid password file from a trusted copy."
                )
                self.update()
                event.accept()
                return
            supervisor_hash = self._password_hashes.get("supervisor")
            if supervisor_hash and not self._request_setup_password(supervisor_hash):
                event.accept()
                return
            self._setup_open = True
            self._setup_page = None
            self._setup_status = (
                "F9: Restore known-good settings; F10: Save; Esc: leave unchanged."
                if self._settings_warning
                else "Use arrow keys to select an item; press Enter."
            )
            self._pause_post_timers()
            self.update()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Space and self._post_complete:
            self.advanceRequested.emit()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Space:
            event.accept()
            return
        super().keyPressEvent(event)

    def _handle_setup_key(self, event) -> None:
        key = event.key()
        if key == Qt.Key.Key_Escape:
            if self._setup_page is not None:
                self._setup_page = None
                self._setup_status = "Select an item or press Escape to return to POST."
            else:
                self._setup_open = False
                self._resume_post_timers()
                self.update()
                self.setupClosed.emit()
                event.accept()
                return
        elif key == Qt.Key.Key_F10:
            self._save_and_exit_setup()
            event.accept()
            return
        elif key == Qt.Key.Key_F9 and self._settings_warning:
            self._restore_saved_settings()
        elif key in (Qt.Key.Key_F1, Qt.Key.Key_H):
            self._setup_status = (
                "Arrows: navigate   Enter: select/change   Esc: back/exit   F1: help"
            )
        elif self._setup_page is not None:
            self._handle_setup_page_key(key)
        else:
            self._handle_setup_menu_key(key)
        self.update()
        event.accept()

    def _load_setup_values(self, settings: dict[str, list[int]]) -> bool:
        """Apply saved choice indexes, rejecting the whole set if any are invalid."""
        validated: dict[str, list[int]] = {}
        for page, values in settings.items():
            if (
                page not in self.SETUP_PAGES
                or page == "password"
                or not isinstance(values, list)
            ):
                continue
            rows = self.SETUP_PAGES[page][1]
            if len(values) != len(rows):
                return False
            if not all(
                type(value) is int and 0 <= value < len(row[1])
                for value, row in zip(values, rows, strict=True)
            ):
                return False
            validated[page] = list(values)
        self._setup_values.update(validated)
        return True

    def _sync_password_statuses(self) -> None:
        self._setup_values["password"] = [
            int(role in self._password_hashes)
            for role in ("supervisor", "user")
        ]

    def _request_setup_password(self, encoded_hash: str) -> bool:
        password, accepted = QInputDialog.getText(
            self,
            "BIOS Supervisor Password",
            "Enter the supervisor password to open setup:",
            QLineEdit.EchoMode.Password,
        )
        if accepted and verify_bios_password(password, encoded_hash):
            return True
        self._setup_status = "Incorrect supervisor password; setup remains locked."
        self.update()
        return False

    def authorize_startup(self) -> bool:
        """Require the configured user password before continuing into Windows."""
        if not self._passwords_available:
            self._setup_status = (
                "Neither BIOS password file could be verified; startup is locked. "
                "Restore a valid password file from a trusted copy."
            )
            self.update()
            return False
        encoded_hash = self._password_hashes.get("user")
        if not encoded_hash:
            return True
        password, accepted = QInputDialog.getText(
            self,
            "BIOS User Password",
            "Enter the user password to continue startup:",
            QLineEdit.EchoMode.Password,
        )
        if accepted and verify_bios_password(password, encoded_hash):
            return True
        self._setup_status = "Incorrect user password; startup remains locked."
        self.update()
        return False

    def _set_bios_password(self, role: str) -> None:
        label = "supervisor" if role == "supervisor" else "user"
        password, accepted = QInputDialog.getText(
            self,
            f"Set {label.title()} Password",
            f"Enter a new {label} password:",
            QLineEdit.EchoMode.Password,
        )
        if not accepted:
            return
        if not password:
            self._setup_status = "Password was not changed: passwords cannot be empty."
            self.update()
            return
        confirmation, confirmed = QInputDialog.getText(
            self,
            f"Confirm {label.title()} Password",
            f"Re-enter the new {label} password:",
            QLineEdit.EchoMode.Password,
        )
        if not confirmed:
            return
        if password != confirmation:
            self._setup_status = "Passwords did not match; no change was saved."
            self.update()
            return

        updated_hashes = dict(self._password_hashes)
        updated_hashes[role] = hash_bios_password(password)
        try:
            save_bios_password_hashes(updated_hashes)
        except (OSError, ValueError) as exc:
            self._setup_status = f"Password not saved: {exc}"
            self.update()
            return
        self._password_hashes = updated_hashes
        self._sync_password_statuses()
        self._setup_status = f"{label.title()} password saved."
        self.update()

    def _clear_bios_password(self, role: str) -> None:
        if role not in self._password_hashes:
            self._setup_status = f"No {role} password is installed."
            self.update()
            return
        label = role.title()
        answer = QMessageBox.question(
            self,
            f"Clear {label} Password",
            f"Remove the {role} password?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        updated_hashes = dict(self._password_hashes)
        del updated_hashes[role]
        try:
            save_bios_password_hashes(updated_hashes)
        except (OSError, ValueError) as exc:
            self._setup_status = f"Password not cleared: {exc}"
            self.update()
            return
        self._password_hashes = updated_hashes
        self._sync_password_statuses()
        self._setup_status = f"{label} password cleared."
        self.update()

    def _recover_bios_password(self) -> None:
        if not self._passwords_available:
            self._setup_status = (
                "Recovery unavailable: neither BIOS password file could be verified. "
                "Restore a valid password file from a trusted copy; startup and "
                "setup remain locked."
            )
            self.update()
            return

        installed_roles = [
            role for role in ("supervisor", "user") if role in self._password_hashes
        ]
        if not installed_roles:
            self._setup_status = "No BIOS password is installed to recover."
            self.update()
            return

        role_labels = {
            "supervisor": "Supervisor Password",
            "user": "User Password",
        }
        labels = [role_labels[role] for role in installed_roles]
        selected_label, accepted = QInputDialog.getItem(
            self,
            "BIOS Password Recovery",
            "Select the forgotten BIOS password to remove:",
            labels,
            0,
            False,
        )
        if not accepted:
            return
        role = installed_roles[labels.index(selected_label)]
        label = role_labels[role]
        answer = QMessageBox.question(
            self,
            "Confirm BIOS Password Recovery",
            (
                f"Remove only the selected {label}? The other BIOS password, "
                "if installed, will remain. Recovery also resets saved BIOS "
                "setup choices to defaults: date and time, drive configuration, "
                "boot order, chipset, power management, display color, and "
                "boot-sector virus protection. Continue?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            updated_hashes = recover_bios_password(role)
        except (OSError, ValueError) as exc:
            self._setup_status = f"BIOS password recovery failed: {exc}"
            self.update()
            return

        self._password_hashes = updated_hashes
        for page in self._setup_values:
            self._setup_values[page] = [0] * len(self._setup_values[page])
        self._sync_password_statuses()
        if self._post_complete:
            self._selected_boot_source = self._select_boot_source()
        self._setup_status = (
            f"{label} removed. Saved BIOS setup choices were reset to defaults."
        )
        self.update()

    def _save_and_exit_setup(self) -> None:
        if self._settings_warning:
            answer = QMessageBox.question(
                self,
                "Replace damaged BIOS settings?",
                "Save the current choices instead of restoring the known-good copy?\n"
                "The original file will be preserved as bios.damaged-*.json first.\n"
                "The known-good copy will be updated to these choices.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        try:
            save_bios_settings(
                {
                    page: values
                    for page, values in self._setup_values.items()
                    if page != "password"
                },
                preserve_original=bool(self._settings_warning),
            )
        except (OSError, ValueError) as exc:
            self._setup_status = f"Settings not saved: {exc}"
            self.update()
            return
        self._settings_warning = None
        if self._post_complete:
            self._selected_boot_source = self._select_boot_source()
        self._setup_open = False
        self._resume_post_timers()
        self.update()
        self.setupClosed.emit()

    def _restore_saved_settings(self) -> None:
        answer = QMessageBox.question(
            self,
            "Restore known-good BIOS settings?",
            "Restore the last successfully saved choices? Current setup edits "
            "will be discarded.\nThe original file will first be preserved as "
            "bios.damaged-*.json. BIOS passwords will not change.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        previous_values = {
            page: list(values) for page, values in self._setup_values.items()
        }
        try:
            settings = load_bios_settings_backup()
            if not self._load_setup_values(settings):
                raise ValueError("The backup contains invalid BIOS choices.")
            # Validation is tentative: failed recovery must not change the UI.
            self._setup_values = previous_values
            archive = restore_bios_settings(settings)
        except (OSError, ValueError) as exc:
            self._setup_values = previous_values
            self._setup_status = f"Settings not restored: {exc}"
            self.update()
            return
        self._setup_values = {
            key: [0] * len(rows)
            for key, (_title, rows) in self.SETUP_PAGES.items()
        }
        self._load_setup_values(settings)
        self._sync_password_statuses()
        self._settings_warning = None
        # Re-evaluate already completed hardware checks using restored choices.
        if self._sata_port_1_check_complete:
            self._complete_sata_port_1_check()
        if self._sata_port_2_check_complete:
            self._complete_sata_port_2_check()
        if self._post_complete:
            self._selected_boot_source = self._select_boot_source()
        self._setup_status = (
            f"Restored; original preserved: {archive.name}"
        )
        self.update()

    def _handle_setup_menu_key(self, key: int) -> None:
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            direction = -1 if key == Qt.Key.Key_Left else 1
            self._setup_group = (
                self._setup_group + direction
            ) % len(self.SETUP_GROUPS)
        elif key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            items = self.SETUP_GROUPS[self._setup_group][1]
            direction = -1 if key == Qt.Key.Key_Up else 1
            self._setup_item_indices[self._setup_group] = (
                self._setup_item_indices[self._setup_group] + direction
            ) % len(items)
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            _label, action = self.SETUP_GROUPS[self._setup_group][1][
                self._setup_item_indices[self._setup_group]
            ]
            if action in self.SETUP_PAGES:
                self._setup_page = action
                self._setup_page_item = 0
                self._setup_status = "Use Left/Right or Enter to change a setting."
            else:
                self._apply_setup_action(action)
    def _handle_setup_page_key(self, key: int) -> None:
        assert self._setup_page is not None
        _title, rows = self.SETUP_PAGES[self._setup_page]
        if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            direction = -1 if key == Qt.Key.Key_Up else 1
            self._setup_page_item = (self._setup_page_item + direction) % len(rows)
            return
        if self._setup_page == "password":
            role = ("supervisor", "user")[self._setup_page_item]
            if key in (Qt.Key.Key_Right, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._set_bios_password(role)
            elif key == Qt.Key.Key_Delete:
                self._clear_bios_password(role)
            return
        if key not in (
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):
            return
        label, choices = rows[self._setup_page_item]
        if len(choices) < 2:
            self._setup_status = f"{label}: {choices[0]}"
            return
        direction = -1 if key == Qt.Key.Key_Left else 1
        values = self._setup_values[self._setup_page]
        values[self._setup_page_item] = (
            values[self._setup_page_item] + direction
        ) % len(choices)
        self._setup_status = f"{label}: {choices[values[self._setup_page_item]]}"

    def _apply_setup_action(self, action: str) -> None:
        messages = {
            "detect_c": "Primary master detected: 1 TB SATA hard disk.",
            "detect_d": "Secondary master detected: ATAPI DVD-ROM.",
            "original": "Original setup defaults applied.",
            "optimal": "Optimal performance defaults applied.",
            "fail_safe": "Fail-safe defaults applied.",
        }
        if action in self.SETUP_PRESETS:
            # Presets configure normal firmware choices, never installed passwords.
            for page, values in self.SETUP_PRESETS[action].items():
                self._setup_values[page] = list(values)
        self._setup_status = messages[action]

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt event name
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#000000"))

        scale = min(
            self.width() / self.CANVAS_WIDTH,
            self.height() / self.CANVAS_HEIGHT,
        )
        painter.translate(
            (self.width() - self.CANVAS_WIDTH * scale) / 2,
            (self.height() - self.CANVAS_HEIGHT * scale) / 2,
        )
        painter.scale(scale, scale)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        if self._setup_open:
            self._paint_setup(painter)
            painter.end()
            return

        painter.drawPixmap(
            QRectF(0, 0, 292, 76),
            self._ami_logo,
            QRectF(self._ami_logo.rect()),
        )
        painter.drawPixmap(
            QRectF(492, 0, 148, 80),
            self._energy_star_logo,
            QRectF(self._energy_star_logo.rect()),
        )
        painter.drawPixmap(
            QRectF(496, 374, 132, 32),
            self._gemma_logo,
            QRectF(self._gemma_logo.rect()),
        )
        painter.drawPixmap(
            QRectF(466, 378, 24, 25),
            self._gemini_logo,
            QRectF(self._gemini_logo.rect()),
        )

        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Consolas", 9))
        lines = [
            (92, "AMI BIOS (C) 2011 American Megatrends Inc., Version 1204"),
            (110, "ASUS P8P67 DELUXE UEFI BIOS  •  BIOS 1204"),
        ]
        if self._cpu_check_complete:
            lines.append((136, "CPU: Intel(R) Core(TM) i7-2600K CPU @ 3.40GHz"))
        lines.append(
            (
                154,
                "Memory Test: 8192 MB OK"
                if self._memory_test_complete
                else "Memory Test: 8192 MB ...",
            )
        )
        if self._usb_check_complete:
            usb_status = "USB Devices: Keyboard, Mouse"
            if self._bootable_usb_detected:
                usb_status += ", bootable media detected"
            lines.append((172, usb_status))
        if self._sata_port_1_check_complete:
            lines.append(
                (
                    190,
                    "SATA Port 1: 1 TB Hard Disk"
                    if self._boot_drive_detected
                    else "SATA Port 1: Device Not Detected",
                )
            )
        if self._sata_port_2_check_complete:
            dvd_status = (
                "SATA Port 2: ATAPI DVD-ROM"
                if self._dvd_drive_detected
                else "SATA Port 2: Device Not Detected"
            )
            if self._dvd_drive_detected and self._bootable_dvd_detected:
                dvd_status += " (bootable media detected)"
            lines.append((208, dvd_status))
        if self._post_complete:
            lines.append((240, "System Configuration Data Updated"))
            if self._selected_boot_source is not None:
                boot_messages = {
                    "Hard Disk": "Booting from AHCI hard disk ...",
                    "DVD-ROM": "Booting from ATAPI DVD-ROM ...",
                    "USB": "Booting from USB device ...",
                }
                lines.extend(
                    [
                        (258, boot_messages[self._selected_boot_source]),
                        (314, "Press <SPACE> to continue to Windows"),
                    ]
                )
            else:
                lines.extend(
                    [
                        (258, self.BOOT_FAILURE_MESSAGE),
                        (276, "Check the SATA connection and boot device."),
                    ]
                )
        if self._settings_warning:
            lines.append((222, self._settings_warning))
        lines.extend(
            [
                (292, "Press <DEL> to enter UEFI BIOS Setup"),
                (310, "Press <F8> for password recovery; setup choices will reset"),
                (426, "ASUS P8P67 DELUXE  •  EFI AMI BIOS  •  2011"),
            ]
        )
        if self._setup_status.startswith(
            (
                "Incorrect supervisor password",
                "Incorrect user password",
                "BIOS password recovery",
                "Recovery unavailable",
                "No BIOS password",
                "Supervisor Password removed",
                "User Password removed",
                "Interrupted BIOS recovery",
                "BIOS password backup recovery used",
            )
        ):
            lines.append((350, self._setup_status))
        for y, line in lines:
            painter.drawText(QPointF(0, y), line)
        painter.end()

    def _paint_setup(self, painter: QPainter) -> None:
        painter.fillRect(
            QRectF(0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT),
            QBrush(self._setup_texture),
        )
        painter.fillRect(QRectF(47, 13, 546, 30), QColor("#c2c2c2"))
        painter.setPen(QColor("#777777"))
        painter.drawRect(QRectF(47, 13, 546, 30))
        painter.drawPixmap(
            QRectF(59, 15, 99, 26),
            self._ami_logo,
            QRectF(self._ami_logo.rect()),
        )
        painter.drawPixmap(
            QRectF(526, 14, 60, 29),
            self._energy_star_logo,
            QRectF(self._energy_star_logo.rect()),
        )
        painter.setPen(QColor("#11114c"))
        painter.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        painter.drawText(QPointF(303, 25), "AMIBIOS Setup")
        painter.drawText(QPointF(286, 37), "American Megatrends Inc.")

        panels = (
            (33, 70, 319, 141),
            (392, 70, 216, 141),
            (33, 223, 215, 86),
            (288, 223, 320, 86),
        )
        for group_index, (x, y, width, height) in enumerate(panels):
            self._paint_setup_panel(
                painter,
                group_index,
                QRectF(x, y, width, height),
            )

        if self._setup_page is not None:
            self._paint_setup_page(painter)

        painter.setPen(QColor("#11114c"))
        painter.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        painter.drawText(QPointF(23, 333), self._setup_status[:70])
        painter.fillRect(QRectF(504, 321, 120, 16), QColor("#101044"))
        painter.setPen(QColor("#ffffff"))
        painter.drawText(QPointF(511, 333), "F1: Help  Esc: Exit")
        painter.setPen(QColor("#11114c"))
        painter.drawText(QPointF(25, 366), "Arrows: Move  Enter: Select  F10: Save & Exit")
        if self._settings_warning:
            painter.drawText(QPointF(25, 386), "F9: Restore known-good settings (preserves original)")

    def _paint_setup_panel(
        self,
        painter: QPainter,
        group_index: int,
        rect: QRectF,
    ) -> None:
        title, entries = self.SETUP_GROUPS[group_index]
        selected_panel = self._setup_page is None and group_index == self._setup_group
        selected_row = self._setup_item_indices[group_index]
        painter.fillRect(
            rect,
            QColor("#dedede") if selected_panel else QColor("#aaaaaa"),
        )
        painter.setPen(QColor("#555555"))
        painter.drawRect(rect)
        painter.fillRect(
            QRectF(rect.x() + 1, rect.y() + 1, rect.width() - 2, 13),
            QColor("#9b0099") if selected_panel else QColor("#555555"),
        )
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        painter.drawText(
            QRectF(rect.x(), rect.y() + 1, rect.width(), 13),
            Qt.AlignmentFlag.AlignCenter,
            title,
        )

        painter.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        columns = 3 if group_index in (0, 3) else 2
        row_height = 25 if group_index in (0, 1) else 26
        column_width = (rect.width() - 20) / columns
        for row_index, (label, _action) in enumerate(entries):
            column = row_index % columns
            row = row_index // columns
            item_x = rect.x() + 10 + column * column_width
            item_y = rect.y() + 34 + row * row_height
            if selected_panel and selected_row == row_index:
                painter.fillRect(
                    QRectF(item_x - 3, item_y - 12, column_width - 2, 17),
                    QColor("#222255"),
                )
                painter.setPen(QColor("#ffffff"))
            else:
                painter.setPen(QColor("#171717"))
            painter.drawText(QPointF(item_x, item_y), label)

    def _paint_setup_page(self, painter: QPainter) -> None:
        assert self._setup_page is not None
        page_title, rows = self.SETUP_PAGES[self._setup_page]
        rect = QRectF(32, 61, 576, 254)
        painter.fillRect(rect, QColor("#dedede"))
        painter.setPen(QColor("#555555"))
        painter.drawRect(rect)
        painter.fillRect(
            QRectF(rect.x() + 1, rect.y() + 1, rect.width() - 2, 18),
            QColor("#555555"),
        )
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        painter.drawText(
            QRectF(rect.x(), rect.y() + 1, rect.width(), 18),
            Qt.AlignmentFlag.AlignCenter,
            page_title,
        )
        painter.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        for row_index, (label, choices) in enumerate(rows):
            row_y = rect.y() + 43 + row_index * 26
            is_selected = row_index == self._setup_page_item
            if is_selected:
                painter.fillRect(
                    QRectF(rect.x() + 12, row_y - 16, rect.width() - 24, 21),
                    QColor("#222255"),
                )
            painter.setPen(QColor("#ffffff") if is_selected else QColor("#171717"))
            painter.drawText(QPointF(rect.x() + 22, row_y), label[:36])
            value_index = self._setup_values[self._setup_page][row_index]
            if self._setup_page == "password":
                value = "Installed" if value_index else "Not Installed"
            else:
                value = choices[value_index]
            painter.drawText(
                QPointF(rect.x() + 300, row_y),
                value[:38],
            )
        painter.setPen(QColor("#11114c"))
        painter.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        painter.drawText(
            QPointF(50, 304),
            (
                "Enter/Right: set or change; Delete: clear password."
                if self._setup_page == "password"
                else "Use Up/Down to move, Left/Right to change values."
            ),
        )


class WindowsStartScreen(QWidget):
    """Plays the supplied Windows 7 startup frames in their specified sequence."""

    finished = Signal()
    FRAME_COUNT = 105
    FRAME_ARCHIVE = (
        Path(__file__).resolve().parent.parent
        / "assets"
        / "boot"
        / "windows7_boot_frames.zip"
    )

    def __init__(
        self,
        loop_count: int = 3,
        frame_interval_ms: int = 50,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setMinimumSize(800, 560)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet("background: #000000;")
        if loop_count < 0:
            raise ValueError("loop_count cannot be negative")
        if frame_interval_ms < 1:
            raise ValueError("frame_interval_ms must be positive")

        self._frames = self._load_frames()
        self._sequence = self.make_sequence(loop_count)
        self._sequence_position = 0
        self._finished = False
        self._timer = QTimer(self)
        self._timer.setInterval(frame_interval_ms)
        self._timer.timeout.connect(self._advance_frame)
        self._timer.start()

    @classmethod
    def make_sequence(cls, loop_count: int) -> list[int]:
        sequence = list(range(cls.FRAME_COUNT))
        for _ in range(loop_count):
            sequence.extend(range(103, 59, -1))
            sequence.extend(range(61, 105))
        return sequence

    @classmethod
    def _load_frames(cls) -> list[QPixmap]:
        if not cls.FRAME_ARCHIVE.is_file():
            raise FileNotFoundError(
                f"Windows startup frame archive is missing: {cls.FRAME_ARCHIVE}"
            )
        try:
            with zipfile.ZipFile(cls.FRAME_ARCHIVE) as archive:
                frames = []
                for index in range(cls.FRAME_COUNT):
                    name = f"activity{index:03d}.bmp"
                    image = QPixmap()
                    if not image.loadFromData(archive.read(name), "BMP"):
                        raise RuntimeError(f"Could not load Windows startup frame {name}")
                    frames.append(image)
                return frames
        except (OSError, KeyError, zipfile.BadZipFile) as exc:
            raise RuntimeError(f"Could not read Windows startup frames: {exc}") from exc

    def _advance_frame(self) -> None:
        if self._sequence_position + 1 >= len(self._sequence):
            self._finish_animation()
            return
        self._sequence_position += 1
        self.update()

    def _finish_animation(self) -> None:
        if self._finished:
            return
        self._finished = True
        self._timer.stop()
        self.finished.emit()

    def showEvent(self, event) -> None:  # noqa: N802 - Qt event name
        super().showEvent(event)
        self.setFocus(Qt.FocusReason.OtherFocusReason)

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if event.key() == Qt.Key.Key_Space:
            self._finish_animation()
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt event name
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#000000"))

        width = self.width()
        height = self.height()
        center = QPointF(width / 2, height / 2 - 38)
        frame_index = self._sequence[self._sequence_position]
        image = self._frames[frame_index]
        painter.drawPixmap(
            QRectF(center.x() - 100, center.y() - 100, 200, 200),
            image,
            QRectF(image.rect()),
        )

        painter.setPen(QColor("#f2f4f8"))
        painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        painter.drawText(
            QRectF(0, center.y() + 130, width, 42),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "Starting Windows",
        )
        painter.setFont(QFont("Segoe UI", 10))
        painter.setPen(QColor("#808080"))
        painter.drawText(
            QRectF(0, height - 42, width, 24),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "© Microsoft Corporation",
        )


class FursonaEditor(QGroupBox):
    removeRequested = Signal(object)

    def __init__(self, number: int, parent: QWidget | None = None) -> None:
        super().__init__(f"Fursona {number}", parent)
        self.fursona_name = QLineEdit()
        self.fursona_name.setPlaceholderText("Fursona name")
        self.species = QLineEdit()
        self.species.setPlaceholderText("Species")
        self.pronouns = QLineEdit()
        self.pronouns.setPlaceholderText("Pronouns")
        self.date_of_birth = QLineEdit()
        self.date_of_birth.setPlaceholderText("YYYY-MM-DD")
        self.date_of_birth.setMaxLength(10)
        self.gender = QLineEdit()
        self.gender.setPlaceholderText("Gender")
        self.location = QLineEdit()
        self.location.setPlaceholderText("Location")
        self.bio = QLineEdit()
        self.bio.setPlaceholderText("Short description (optional)")
        self.avatar_path = QLineEdit()
        self.avatar_path.setPlaceholderText("Optional image file path")
        self.avatar_path.setReadOnly(True)

        form = QFormLayout()
        form.addRow("Fursona name", self.fursona_name)
        form.addRow("Species", self.species)
        form.addRow("Pronouns", self.pronouns)
        form.addRow("Date of birth", self.date_of_birth)
        form.addRow("Gender", self.gender)
        form.addRow("Location", self.location)
        form.addRow("About this fursona", self.bio)

        avatar_row = QHBoxLayout()
        avatar_row.addWidget(self.avatar_path, 1)
        self.browse_button = QPushButton("Choose image…")
        self.browse_button.clicked.connect(self._choose_avatar)
        avatar_row.addWidget(self.browse_button)
        form.addRow("Profile image", avatar_row)

        self.remove_button = QPushButton("Remove this fursona")
        self.remove_button.clicked.connect(lambda: self.removeRequested.emit(self))

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.remove_button, 0, Qt.AlignmentFlag.AlignRight)

    def _choose_avatar(self) -> None:
        start_dir = STORAGE_ROOT / "Profiles"
        start_dir.mkdir(parents=True, exist_ok=True)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose a profile image",
            str(start_dir),
            "Image files (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if file_path:
            self.avatar_path.setText(file_path)

    def to_profile(self) -> FursonaProfile:
        return FursonaProfile(
            fursona_name=self.fursona_name.text().strip(),
            species=self.species.text().strip(),
            pronouns=self.pronouns.text().strip(),
            date_of_birth=self.date_of_birth.text().strip(),
            gender=self.gender.text().strip(),
            location=self.location.text().strip(),
            bio=self.bio.text().strip(),
            avatar_path=self.avatar_path.text().strip(),
        )


class SetupWizard(QWidget):
    accountCreated = Signal(object)
    DEFAULT_FURSONAS = (
        {
            "fursona_name": "Kithylin",
            "species": "Angelic anthro husky dog",
            "pronouns": "He/Him",
            "date_of_birth": "1964-04-25",
            "gender": "Male",
            "location": "Buffalo NY",
            "bio": "White feathery wings, a halo, blue eyes, and typical husky fur coloration.",
        },
        {
            "fursona_name": "Beep",
            "species": "Wolf protogen",
            "pronouns": "He/Him",
            "date_of_birth": "1988-05-12",
            "gender": "Male",
            "location": "England",
            "bio": "White-on-black IPS face screen, grey grizzled fur, and loves eating RAM sticks.",
        },
        {
            "fursona_name": "Foxy",
            "species": "Red fox",
            "pronouns": "He/Him",
            "date_of_birth": "1989-01-02",
            "gender": "Male",
            "location": "Lawrence Kansas",
            "bio": "Tall red fox with golden amber eyes, typical fox coloration, and a very sweet personality.",
        },
        {
            "fursona_name": "Sheppie",
            "species": "German Shepherd dog",
            "pronouns": "He/Him",
            "date_of_birth": "1986-08-10",
            "gender": "Male",
            "location": "New Zealand",
            "bio": "Playful, brown-eyed dog with a constantly wagging tail; loves dancing and chasing balls.",
        },
        {
            "fursona_name": "Snowmew",
            "species": "Snow leopard",
            "pronouns": "She/Her",
            "date_of_birth": "1983-05-12",
            "gender": "Female",
            "location": "",
            "bio": "Tall snow leopard with typical fur coloration, striking silver eyes, and a thick fluffy tail that shows her emotions and focus.",
        },
        {
            "fursona_name": "Quake",
            "species": "Hyena",
            "pronouns": "He/Him",
            "date_of_birth": "1985-03-27",
            "gender": "Male",
            "location": "London",
            "bio": "Short hyena with spots and fluffy tan and gold fur; loves a good joke and laughs at anything.",
        },
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("setupScreen")
        self.setStyleSheet(
            "#setupScreen { background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            " stop:0 #dcecf7, stop:1 #91b8d2); }"
        )
        self.profile_editors: list[FursonaEditor] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(34, 22, 34, 18)
        root.setSpacing(10)

        title = QLabel("Set up Windows")
        title.setStyleSheet("font-size: 24pt; font-weight: 300; color: #244c6c;")
        subtitle = QLabel(
            "Create the local desktop account and review the fursona profiles. "
            "Profile details are fixed after setup; changing them requires a full reset."
        )
        subtitle.setStyleSheet("color: #395b75;")
        root.addWidget(title)
        root.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contents = QWidget()
        contents_layout = QVBoxLayout(contents)
        contents_layout.setContentsMargins(4, 6, 4, 12)
        contents_layout.setSpacing(12)

        account_box = QGroupBox("Windows account")
        account_form = QFormLayout(account_box)
        self.desktop_name = QLineEdit()
        self.desktop_name.setPlaceholderText("Name shown on the desktop")
        self.same_online_name = QCheckBox(
            "Use this name for all online accounts"
        )
        self.same_online_name.setChecked(True)
        self.online_name = QLineEdit()
        self.online_name.setPlaceholderText("Shared online name")
        self.online_name.setEnabled(False)
        self.same_online_name.toggled.connect(self._sync_online_name)
        self.desktop_name.textChanged.connect(self._sync_online_name)
        account_form.addRow("Desktop account name", self.desktop_name)
        account_form.addRow("", self.same_online_name)
        account_form.addRow("Online account name", self.online_name)
        contents_layout.addWidget(account_box)

        adult_note = QLabel(
            "This fictional community is adults-only. To keep every profile 21+ "
            "throughout the fixed 2011 year, dates of birth must make the profile "
            "21 on January 1, 2011."
        )
        adult_note.setWordWrap(True)
        adult_note.setStyleSheet(
            "padding: 9px; color: #294961; background: rgba(255,255,255,175); "
            "border: 1px solid #bad0df; border-radius: 5px;"
        )
        contents_layout.addWidget(adult_note)

        self.profiles_box = QGroupBox("Fursona profiles")
        self.profile_layout = QVBoxLayout(self.profiles_box)
        self.profile_layout.setSpacing(10)
        contents_layout.addWidget(self.profiles_box)

        self.add_profile_button = QPushButton("Add another fursona")
        self.add_profile_button.clicked.connect(self._add_profile)
        contents_layout.addWidget(
            self.add_profile_button, 0, Qt.AlignmentFlag.AlignLeft
        )
        contents_layout.addStretch(1)

        scroll.setWidget(contents)
        root.addWidget(scroll, 1)

        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #a3271d; font-weight: 600;")
        self.error_label.hide()
        root.addWidget(self.error_label)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self.create_button = QPushButton("Create account")
        self.create_button.setDefault(True)
        self.create_button.clicked.connect(self._create_account)
        footer.addWidget(self.create_button)
        root.addLayout(footer)

        for profile_data in self.DEFAULT_FURSONAS:
            self._add_profile(profile_data)

    def _sync_online_name(self, *_args) -> None:
        shared = self.same_online_name.isChecked()
        self.online_name.setEnabled(not shared)
        if shared:
            self.online_name.setText(self.desktop_name.text())

    def _add_profile(self, profile_data: dict[str, str] | None = None) -> None:
        editor = FursonaEditor(len(self.profile_editors) + 1, self)
        if profile_data:
            editor.fursona_name.setText(profile_data["fursona_name"])
            editor.species.setText(profile_data["species"])
            editor.pronouns.setText(profile_data["pronouns"])
            editor.date_of_birth.setText(profile_data["date_of_birth"])
            editor.gender.setText(profile_data["gender"])
            editor.location.setText(profile_data["location"])
            editor.bio.setText(profile_data["bio"])
        editor.removeRequested.connect(self._remove_profile)
        self.profile_editors.append(editor)
        self.profile_layout.addWidget(editor)
        self._update_remove_buttons()

    def _remove_profile(self, editor: FursonaEditor) -> None:
        if len(self.profile_editors) <= 1:
            return
        self.profile_editors.remove(editor)
        self.profile_layout.removeWidget(editor)
        editor.deleteLater()
        for index, remaining in enumerate(self.profile_editors, start=1):
            remaining.setTitle(f"Fursona {index}")
        self._update_remove_buttons()

    def _update_remove_buttons(self) -> None:
        allow_remove = len(self.profile_editors) > 1
        for editor in self.profile_editors:
            editor.remove_button.setEnabled(allow_remove)

    def collect_account(self) -> UserAccount:
        shared_name = self.same_online_name.isChecked()
        return UserAccount(
            desktop_name=self.desktop_name.text().strip(),
            online_name=(
                self.desktop_name.text().strip()
                if shared_name
                else self.online_name.text().strip()
            ),
            use_desktop_name_online=shared_name,
            fursonas=[editor.to_profile() for editor in self.profile_editors],
        )

    def _create_account(self) -> None:
        account = self.collect_account()
        errors = validate_account(account)
        if errors:
            self.error_label.setText("\n".join(errors))
            self.error_label.show()
            return
        self.error_label.hide()
        self.accountCreated.emit(account)


class _PowerMenuImage(QWidget):
    choiceActivated = Signal(str)
    CHOICES = ("restart", "sleep", "shutdown")

    def __init__(self, images: dict[str, QPixmap], parent: QWidget) -> None:
        super().__init__(parent)
        self._images = images
        self._hovered_choice: str | None = None
        self.setMouseTracking(True)
        self.resize(148, 80)
        self.hide()

    def _choice_at(self, y: float) -> str:
        index = min(2, max(0, int(y * 3 / max(1, self.height()))))
        return self.CHOICES[index]

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt event name
        image_name = (
            f"menu-{self._hovered_choice}"
            if self._hovered_choice
            else "menu"
        )
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self._images[image_name])
        painter.end()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt event name
        choice = self._choice_at(event.position().y())
        if choice != self._hovered_choice:
            self._hovered_choice = choice
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt event name
        self._hovered_choice = None
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if event.button() == Qt.MouseButton.LeftButton:
            self.choiceActivated.emit(self._choice_at(event.position().y()))
            event.accept()
            return
        super().mousePressEvent(event)


def load_profile_icon(profile: FursonaProfile, icon_directory: Path) -> QPixmap:
    if profile.avatar_path:
        custom_image = QPixmap(str(Path(profile.avatar_path).expanduser()))
        if not custom_image.isNull():
            return custom_image

    requested_name = profile.fursona_name.strip().casefold()
    for icon_path in icon_directory.glob("Icon_*"):
        parts = icon_path.stem.split("_", 2)
        if len(parts) == 3 and parts[2].casefold() == requested_name:
            image = QPixmap(str(icon_path))
            if not image.isNull():
                return image

    placeholder = QPixmap(83, 83)
    placeholder.fill(QColor("#5b8caf"))
    painter = QPainter(placeholder)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QColor("#eaf4fb"))
    painter.setFont(QFont("Segoe UI", 34, QFont.Weight.DemiBold))
    painter.drawText(
        placeholder.rect(),
        Qt.AlignmentFlag.AlignCenter,
        (profile.fursona_name.strip() or "?")[:1].upper(),
    )
    painter.end()
    return placeholder


class _ProfileChoiceButton(QPushButton):
    highlightChanged = Signal(bool)
    DESIGN_WIDTH = 130
    DESIGN_HEIGHT = 138

    def __init__(
        self,
        profile_name: str,
        profile_id: str,
        icon: QPixmap,
        frame: QPixmap,
        highlighted_frame: QPixmap,
        parent: QWidget,
    ) -> None:
        super().__init__(parent)
        self.profile_name = profile_name
        self.profile_id = profile_id
        self._icon = icon
        self._frame = frame
        self._highlighted_frame = highlighted_frame
        self._hovered = False
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("QPushButton { border: 0; padding: 0; background: transparent; }")

    def enterEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if not self._hovered:
            self._hovered = True
            self.highlightChanged.emit(True)
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if self._hovered:
            self._hovered = False
            self.highlightChanged.emit(False)
            self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt event name
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.scale(
            self.width() / self.DESIGN_WIDTH,
            self.height() / self.DESIGN_HEIGHT,
        )
        frame = self._highlighted_frame if self._hovered else self._frame
        painter.drawPixmap(QRectF(15, 0, 100, 99), frame, QRectF(frame.rect()))
        icon = self._icon.scaled(
            QSize(83, 83),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap(
            QRectF(23.5, 8, 83, 83),
            icon,
            QRectF(icon.rect()),
        )
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        painter.drawText(
            QRectF(0, 103, self.DESIGN_WIDTH, 30),
            Qt.AlignmentFlag.AlignCenter,
            self.profile_name,
        )
        painter.end()


class UserSelectionScreen(QWidget):
    profileSelected = Signal(str)
    soundRequested = Signal(str)
    restartRequested = Signal()
    shutdownRequested = Signal()

    DESIGN_WIDTH = 1920
    DESIGN_HEIGHT = 1200
    MAX_PROFILES_PER_ROW = 6
    PROFILE_GAP_X = 30
    PROFILE_GAP_Y = 60
    DEFAULT_PROFILE_ICONS = (
        "Icon_1_Kithylin.jpg",
        "Icon_2_Beep.jpg",
        "Icon_3_Foxy.jpg",
        "Icon_4_Sheppie.png",
        "Icon_5_Snowmew.jpg",
        "Icon_6_Quake.jpg",
    )

    def __init__(self, account: UserAccount, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.account = account
        assets = Path(__file__).resolve().parent.parent / "assets" / "user-selection"
        login_assets = Path(__file__).resolve().parent.parent / "assets" / "login"
        self._images = {
            "background": QPixmap(str(assets / "User_Selection_Background.jpg")),
            "frame": QPixmap(str(assets / "Icon_Frame.png")),
            "frame-highlight": QPixmap(str(assets / "Icon_Frame_Highlight.png")),
            "power": QPixmap(str(assets / "Button_Power_Choices.jpg")),
            "menu": QPixmap(str(assets / "Button_Power_Menu.jpg")),
            "menu-restart": QPixmap(
                str(assets / "Button_Power_Menu_Restart_Highlight.jpg")
            ),
            "menu-sleep": QPixmap(
                str(assets / "Button_Power_Menu_Sleep_Highlight.jpg")
            ),
            "menu-shutdown": QPixmap(
                str(assets / "Button_Power_Menu_Shutdown_Highlight.jpg")
            ),
            "restart-background": QPixmap(
                str(login_assets / "Restart_Background.jpg")
            ),
        }
        missing = [name for name, image in self._images.items() if image.isNull()]
        if missing:
            raise RuntimeError(
                f"Could not load Windows user-selection artwork from {assets}: "
                f"{', '.join(missing)}"
            )
        self._highlight_sound = assets / "User_Highlight.wav"
        self._select_sound = assets / "User_Select.wav"
        for sound_path in (self._highlight_sound, self._select_sound):
            if not sound_path.is_file():
                raise FileNotFoundError(f"User-selection sound is missing: {sound_path}")

        self._sleeping = False
        self._restarting = False
        self._power_menu_visible = False
        self.setMinimumSize(800, 560)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        self._controls = QWidget(self)
        self._controls.setStyleSheet("background: transparent;")
        self.profile_buttons: list[_ProfileChoiceButton] = []
        bundled_icons = {
            Path(filename).stem.split("_", 2)[2].casefold(): assets / filename
            for filename in self.DEFAULT_PROFILE_ICONS
        }
        for profile in account.fursonas:
            profile_name = profile.fursona_name.strip()
            icon_path = bundled_icons.get(profile_name.casefold())
            if icon_path is not None:
                icon = QPixmap(str(icon_path))
                if icon.isNull():
                    raise RuntimeError(f"Could not load user icon: {icon_path}")
            else:
                icon = load_profile_icon(profile, assets)
            button = _ProfileChoiceButton(
                profile_name,
                profile.profile_id,
                icon,
                self._images["frame"],
                self._images["frame-highlight"],
                self._controls,
            )
            button.highlightChanged.connect(self._profile_highlighted)
            button.clicked.connect(
                lambda _checked=False, selected_id=profile.profile_id: (
                    self._select_profile(selected_id)
                )
            )
            self.profile_buttons.append(button)

        self.power_button = QPushButton(self._controls)
        self.power_button.setObjectName("selectionPowerChoicesButton")
        self.power_button.setIcon(QIcon(str(assets / "Button_Power_Choices.jpg")))
        self.power_button.setFlat(True)
        self.power_button.setStyleSheet(
            "QPushButton { border: 0; padding: 0; background: transparent; }"
        )
        self.power_button.clicked.connect(self._toggle_power_menu)
        self.power_menu = _PowerMenuImage(
            {
                key: self._images[key]
                for key in ("menu", "menu-restart", "menu-sleep", "menu-shutdown")
            },
            self._controls,
        )
        self.power_menu.choiceActivated.connect(self._choose_power_action)

        self._restart_message = QLabel("Windows is restarting...", self)
        self._restart_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._restart_message.setStyleSheet(
            "background: transparent; color: white; font-size: 24px;"
        )
        self._restart_message.hide()
        self._restart_timer = QTimer(self)
        self._restart_timer.setSingleShot(True)
        self._restart_timer.setInterval(3000)
        self._restart_timer.timeout.connect(self.restartRequested.emit)
        self._layout_controls()

    def _design_rect(
        self, x: int, y: int, width: int, height: int
    ) -> tuple[int, int, int, int]:
        scale = max(
            self.width() / self.DESIGN_WIDTH,
            self.height() / self.DESIGN_HEIGHT,
        )
        offset_x = (self.width() - self.DESIGN_WIDTH * scale) / 2
        offset_y = (self.height() - self.DESIGN_HEIGHT * scale) / 2
        return (
            round(offset_x + x * scale),
            round(offset_y + y * scale),
            round(width * scale),
            round(height * scale),
        )

    def _layout_controls(self) -> None:
        self._controls.setGeometry(self.rect())
        profile_count = len(self.profile_buttons)
        row_count = max(1, (profile_count + self.MAX_PROFILES_PER_ROW - 1) // self.MAX_PROFILES_PER_ROW)
        total_height = (
            row_count * _ProfileChoiceButton.DESIGN_HEIGHT
            + (row_count - 1) * self.PROFILE_GAP_Y
        )
        first_y = (self.DESIGN_HEIGHT - total_height) // 2
        for index, button in enumerate(self.profile_buttons):
            row = index // self.MAX_PROFILES_PER_ROW
            row_start = row * self.MAX_PROFILES_PER_ROW
            row_count_now = min(
                self.MAX_PROFILES_PER_ROW,
                profile_count - row_start,
            )
            row_width = (
                row_count_now * _ProfileChoiceButton.DESIGN_WIDTH
                + (row_count_now - 1) * self.PROFILE_GAP_X
            )
            column = index - row_start
            x = (self.DESIGN_WIDTH - row_width) // 2
            x += column * (
                _ProfileChoiceButton.DESIGN_WIDTH + self.PROFILE_GAP_X
            )
            y = first_y + row * (
                _ProfileChoiceButton.DESIGN_HEIGHT + self.PROFILE_GAP_Y
            )
            button.setGeometry(
                *self._design_rect(
                    x,
                    y,
                    _ProfileChoiceButton.DESIGN_WIDTH,
                    _ProfileChoiceButton.DESIGN_HEIGHT,
                )
            )
        scale = max(
            self.width() / self.DESIGN_WIDTH,
            self.height() / self.DESIGN_HEIGHT,
        )
        margin = round(24 * scale)
        power_width = round(self._images["power"].width() * scale)
        power_height = round(self._images["power"].height() * scale)
        self.power_button.setGeometry(
            self.width() - margin - power_width,
            self.height() - margin - power_height,
            power_width,
            power_height,
        )
        self.power_button.setIconSize(self.power_button.size())
        menu_width = round(148 * scale)
        menu_height = round(80 * scale)
        self.power_menu.setGeometry(
            self.width() - margin - menu_width,
            self.height() - margin - power_height - menu_height,
            menu_width,
            menu_height,
        )
        self._restart_message.setGeometry(self.rect())

    def _profile_highlighted(self, highlighted: bool) -> None:
        if highlighted:
            self.soundRequested.emit(self._highlight_sound.name)

    def _select_profile(self, profile_id: str) -> None:
        if self._sleeping or self._restarting:
            return
        self.soundRequested.emit(self._select_sound.name)
        self.profileSelected.emit(profile_id)

    def _toggle_power_menu(self) -> None:
        self._power_menu_visible = not self._power_menu_visible
        self.power_menu.setVisible(self._power_menu_visible)
        if self._power_menu_visible:
            self.power_menu.raise_()

    def _choose_power_action(self, action: str) -> None:
        self._power_menu_visible = False
        self.power_menu.hide()
        if action == "restart":
            self._restarting = True
            self._controls.hide()
            self._restart_message.show()
            self._restart_message.raise_()
            self._restart_timer.start()
            self.update()
        elif action == "sleep":
            self._sleeping = True
            self._controls.hide()
            self.setCursor(Qt.CursorShape.BlankCursor)
            self.setFocus()
            self.update()
        elif action == "shutdown":
            self.shutdownRequested.emit()

    def _wake_from_sleep(self) -> None:
        if not self._sleeping:
            return
        self._sleeping = False
        self.unsetCursor()
        self._controls.show()
        self.setFocus()
        self.update()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt event name
        super().resizeEvent(event)
        self._layout_controls()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt event name
        painter = QPainter(self)
        if self._sleeping:
            painter.fillRect(self.rect(), QColor("#000000"))
        elif self._restarting:
            painter.drawPixmap(
                self.rect(),
                self._images["restart-background"].scaled(
                    self.size(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ),
            )
        else:
            painter.drawPixmap(
                self.rect(),
                self._images["background"].scaled(
                    self.size(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ),
            )
        painter.end()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if self._sleeping:
            self._wake_from_sleep()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if self._sleeping:
            self._wake_from_sleep()
            event.accept()
            return
        super().keyPressEvent(event)


class LoginScreen(QWidget):
    loginRequested = Signal(str)
    restartRequested = Signal()
    shutdownRequested = Signal()
    switchUserRequested = Signal()

    DESIGN_WIDTH = 1280
    DESIGN_HEIGHT = 720

    def __init__(self, account: UserAccount, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.account = account
        self._profile_id = account.active_profile_id or (
            account.fursonas[0].profile_id if account.fursonas else ""
        )
        assets = Path(__file__).resolve().parent.parent / "assets" / "login"
        self._images = {
            "background": QPixmap(str(assets / "Logon_Template.png")),
            "profile": QPixmap(str(assets / "Kithylin_Profile_Icon.jpg")),
            "power": QPixmap(str(assets / "Button_Power_Choices.jpg")),
            "switch": QPixmap(str(assets / "Button_Switch_User.jpg")),
            "menu": QPixmap(str(assets / "Button_Power_Menu.jpg")),
            "menu-restart": QPixmap(
                str(assets / "Button_Power_Menu_Restart_Highlight.jpg")
            ),
            "menu-sleep": QPixmap(
                str(assets / "Button_Power_Menu_Sleep_Highlight.jpg")
            ),
            "menu-shutdown": QPixmap(
                str(assets / "Button_Power_Menu_Shutdown_Highlight.jpg")
            ),
            "restart-background": QPixmap(str(assets / "Restart_Background.jpg")),
        }
        missing = [name for name, image in self._images.items() if image.isNull()]
        if missing:
            raise RuntimeError(
                f"Could not load Windows login artwork from {assets}: "
                f"{', '.join(missing)}"
            )
        self._profile_image = self._images["profile"]

        self._sleeping = False
        self._restarting = False
        self._power_menu_visible = False
        self.setObjectName("loginScreen")
        self.setMinimumSize(800, 560)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        self._controls = QWidget(self)
        self._controls.setStyleSheet("background: transparent;")
        self.profile_icon = QLabel(self._controls)
        self.profile_icon.setPixmap(self._profile_image)
        self.profile_icon.setScaledContents(False)

        self.username_label = QLabel(account.desktop_name, self._controls)
        self.username_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.username_label.setStyleSheet(
            "background: transparent; color: white; font-size: 15px; "
            "font-weight: 600;"
        )

        self.password_entry = QLineEdit(self._controls)
        self.password_entry.setObjectName("passwordEntry")
        self.password_entry.setPlaceholderText("Password")
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_entry.setStyleSheet(
            "QLineEdit { background: rgba(255,255,255,235); color: #202020; "
            "border: 1px solid #a5a5a5; padding: 3px 6px; }"
        )
        self.password_entry.returnPressed.connect(self._login)

        self.login_button = QPushButton("OK", self._controls)
        self.login_button.setObjectName("loginButton")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self._login)
        self.login_button.setStyleSheet(
            "QPushButton { color: #202020; background: rgba(245,245,245,225); "
            "border: 1px solid #888; padding: 2px 10px; }"
            "QPushButton:hover { background: white; }"
        )

        self.switch_user_button = QPushButton(self._controls)
        self.switch_user_button.setObjectName("switchUserButton")
        self.switch_user_button.setIcon(QIcon(str(assets / "Button_Switch_User.jpg")))
        self.switch_user_button.setIconSize(self._images["switch"].size())
        self.switch_user_button.setFlat(True)
        self.switch_user_button.setStyleSheet(
            "QPushButton { border: 0; padding: 0; background: transparent; }"
        )
        self.switch_user_button.clicked.connect(self.switchUserRequested.emit)

        self.power_button = QPushButton(self._controls)
        self.power_button.setObjectName("powerChoicesButton")
        self.power_button.setIcon(QIcon(str(assets / "Button_Power_Choices.jpg")))
        self.power_button.setIconSize(self._images["power"].size())
        self.power_button.setFlat(True)
        self.power_button.setStyleSheet(
            "QPushButton { border: 0; padding: 0; background: transparent; }"
        )
        self.power_button.clicked.connect(self._toggle_power_menu)

        self.power_menu = _PowerMenuImage(
            {
                name: self._images[name]
                for name in (
                    "menu",
                    "menu-restart",
                    "menu-sleep",
                    "menu-shutdown",
                )
            },
            self._controls,
        )
        self.power_menu.choiceActivated.connect(self._choose_power_action)

        self._restart_message = QLabel(
            "Windows is restarting...", self
        )
        self._restart_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._restart_message.setStyleSheet(
            "background: transparent; color: white; font-size: 24px; "
            "font-weight: 400;"
        )
        self._restart_message.hide()
        self._restart_timer = QTimer(self)
        self._restart_timer.setSingleShot(True)
        self._restart_timer.setInterval(3000)
        self._restart_timer.timeout.connect(self.restartRequested.emit)

        self._layout_login_controls()
        QTimer.singleShot(0, self.password_entry.setFocus)

    def _layout_login_controls(self) -> None:
        self._controls.setGeometry(self.rect())
        profile_rect = self._design_rect(598, 290, 83, 83)
        self.profile_icon.setGeometry(*profile_rect)
        self.profile_icon.setPixmap(
            self._profile_image.scaled(
                QSize(profile_rect[2], profile_rect[3]),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.username_label.setGeometry(*self._design_rect(520, 386, 240, 25))
        self.password_entry.setGeometry(*self._design_rect(565, 425, 150, 28))
        self.login_button.setGeometry(*self._design_rect(720, 425, 44, 28))
        switch_rect = self._design_rect(600, 465, 79, 21)
        self.switch_user_button.setGeometry(*switch_rect)
        self.switch_user_button.setIconSize(QSize(switch_rect[2], switch_rect[3]))
        scale = max(
            self.width() / self.DESIGN_WIDTH,
            self.height() / self.DESIGN_HEIGHT,
        )
        margin = round(24 * scale)
        power_width = round(self._images["power"].width() * scale)
        power_height = round(self._images["power"].height() * scale)
        self.power_button.setGeometry(
            self.width() - margin - power_width,
            self.height() - margin - power_height,
            power_width,
            power_height,
        )
        self.power_button.setIconSize(self.power_button.size())
        menu_width = round(148 * scale)
        menu_height = round(80 * scale)
        self.power_menu.setGeometry(
            self.width() - margin - menu_width,
            self.height() - margin - power_height - menu_height,
            menu_width,
            menu_height,
        )
        self._restart_message.setGeometry(self.rect())

    def _design_rect(
        self, x: int, y: int, width: int, height: int
    ) -> tuple[int, int, int, int]:
        scale = max(
            self.width() / self.DESIGN_WIDTH,
            self.height() / self.DESIGN_HEIGHT,
        )
        offset_x = (self.width() - self.DESIGN_WIDTH * scale) / 2
        offset_y = (self.height() - self.DESIGN_HEIGHT * scale) / 2
        return (
            round(offset_x + x * scale),
            round(offset_y + y * scale),
            round(width * scale),
            round(height * scale),
        )

    def _toggle_power_menu(self) -> None:
        self._power_menu_visible = not self._power_menu_visible
        self.power_menu.setVisible(self._power_menu_visible)
        if self._power_menu_visible:
            self.power_menu.raise_()

    def _choose_power_action(self, action: str) -> None:
        self._power_menu_visible = False
        self.power_menu.hide()
        if action == "restart":
            self._begin_login_restart()
        elif action == "sleep":
            self._enter_sleep()
        elif action == "shutdown":
            self.shutdownRequested.emit()

    def _begin_login_restart(self) -> None:
        self._restarting = True
        self._controls.hide()
        self._restart_message.show()
        self._restart_message.raise_()
        self._restart_timer.start()
        self.update()

    def _enter_sleep(self) -> None:
        self._sleeping = True
        self._controls.hide()
        self.setCursor(Qt.CursorShape.BlankCursor)
        self.setFocus()
        self.update()

    def _wake_from_sleep(self) -> None:
        if not self._sleeping:
            return
        self._sleeping = False
        self.unsetCursor()
        self._controls.show()
        self.password_entry.setFocus()
        self.update()

    def _login(self) -> None:
        if self._profile_id:
            self.loginRequested.emit(self._profile_id)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt event name
        super().resizeEvent(event)
        self._layout_login_controls()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt event name
        painter = QPainter(self)
        if self._sleeping:
            painter.fillRect(self.rect(), QColor("#000000"))
        elif self._restarting:
            painter.drawPixmap(
                self.rect(),
                self._images["restart-background"].scaled(
                    self.size(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ),
            )
        else:
            scale = max(
                self.width() / self.DESIGN_WIDTH,
                self.height() / self.DESIGN_HEIGHT,
            )
            scaled_size = self._images["background"].size() * scale
            scaled = self._images["background"].scaled(
                scaled_size,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        painter.end()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if self._sleeping:
            self._wake_from_sleep()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if self._sleeping:
            self._wake_from_sleep()
            event.accept()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._login()
            event.accept()
        else:
            super().keyPressEvent(event)


class ShutdownScreen(QWidget):
    restartRequested = Signal()
    endProgramRequested = Signal()
    recoveryRequested = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        safe_delay_ms: int = 3000,
    ) -> None:
        super().__init__(parent)
        assets = Path(__file__).resolve().parent.parent / "assets" / "shutdown"
        self._background = QPixmap(str(assets / "shutdown-screen.jpg"))
        self._safe_image = QPixmap(str(assets / "shutdown-safe.jpg"))
        if self._background.isNull() or self._safe_image.isNull():
            raise RuntimeError(f"Could not load shutdown artwork from {assets}")

        self._safe_mode = False
        self.setMinimumSize(800, 560)
        self.setStyleSheet("background-color: black; color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 18, 28, 24)
        layout.setSpacing(14)
        layout.addStretch(1)
        self._message = QLabel("Shutting down...")
        self._message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message.setStyleSheet(
            "background: transparent; color: white; font-size: 26pt; "
            "font-weight: 300;"
        )
        layout.addWidget(self._message)
        self._safe_image_label = QLabel()
        self._safe_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._safe_image_label.setStyleSheet("background: transparent;")
        self._safe_image_label.hide()
        layout.addWidget(self._safe_image_label)
        layout.addStretch(1)
        button_row = QHBoxLayout()
        button_row.setSpacing(18)
        self.restart_button = self._make_button("Restart", "restartButton")
        self.end_button = self._make_button("End Program", "endProgramButton")
        self.recovery_button = self._make_button("Recovery Mode", "recoveryButton")
        self.restart_button.clicked.connect(
            lambda _checked=False: self.restartRequested.emit()
        )
        self.end_button.clicked.connect(
            lambda _checked=False: self.endProgramRequested.emit()
        )
        self.recovery_button.clicked.connect(
            lambda _checked=False: self.recoveryRequested.emit()
        )
        button_row.addStretch(1)
        button_row.addWidget(self.restart_button)
        button_row.addWidget(self.end_button)
        button_row.addWidget(self.recovery_button)
        button_row.addStretch(1)
        self._button_row = QWidget()
        self._button_row.setLayout(button_row)
        self._button_row.setStyleSheet("background: transparent;")
        self._button_row.hide()
        layout.addWidget(self._button_row)

        self._safe_timer = QTimer(self)
        self._safe_timer.setSingleShot(True)
        self._safe_timer.setInterval(safe_delay_ms)
        self._safe_timer.timeout.connect(self._show_safe_screen)
        self._safe_timer.start()

    @staticmethod
    def _make_button(text: str, object_name: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setMinimumSize(150, 44)
        button.setStyleSheet(
            "QPushButton { color: #c97b51; background: rgba(0,0,0,150); "
            "border: 1px solid #c97b51; padding: 8px 16px; font-size: 11pt; }"
            "QPushButton:hover { background: rgba(201,123,81,35); }"
            "QPushButton:pressed { background: rgba(201,123,81,70); }"
        )
        return button

    def _show_safe_screen(self) -> None:
        self._safe_mode = True
        self.setStyleSheet("background-color: black;")
        self._message.hide()
        self._safe_image_label.show()
        self._button_row.show()
        self._update_safe_image()

    def _update_safe_image(self) -> None:
        available = QSize(max(1, self.width() - 56), max(1, self.height() - 150))
        self._safe_image_label.setPixmap(
            self._safe_image.scaled(
                available,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt event name
        super().resizeEvent(event)
        if self._safe_mode:
            self._update_safe_image()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if self._safe_mode:
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor("#000000"))
            painter.end()
            return
        painter = QPainter(self)
        scaled = self._background.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()


class ErrorScreen(QWidget):
    closeRequested = Signal()

    def __init__(self, message: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: #e7eff5;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addStretch(1)
        title = QLabel("Windows could not load the local account")
        title.setStyleSheet("font-size: 22pt; font-weight: 300; color: #294d68;")
        layout.addWidget(title)
        details = QLabel(message)
        details.setWordWrap(True)
        details.setStyleSheet("padding: 12px; background: white; border: 1px solid #c4d4e1;")
        layout.addWidget(details)
        layout.addWidget(
            QLabel("The existing Storage file has not been reset or overwritten.")
        )
        footer = QHBoxLayout()
        footer.addStretch(1)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.closeRequested.emit)
        footer.addWidget(close_button)
        layout.addLayout(footer)
        layout.addStretch(1)
