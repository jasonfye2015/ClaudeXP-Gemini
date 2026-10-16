"""A local-only Windows Update simulation with a rare automatic schedule."""

from __future__ import annotations

import random
import time

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .config import load_windows_update_state, save_windows_update_state

# KB identifiers and release dates are from Microsoft's 2011 security bulletins.
# For example, the individual Windows 7 x64 package entries are listed in:
# https://learn.microsoft.com/en-us/security-updates/securitybulletins/2011/ms11-053
# https://learn.microsoft.com/en-us/security-updates/securitybulletins/2011/ms11-071
UPDATE_CATALOG = (
    "Security Update for Windows 7 for x64-based Systems (KB2419640) — 2011-01-11",
    "Security Update for Windows 7 for x64-based Systems (KB2425227) — 2011-02-08",
    "Security Update for Windows 7 for x64-based Systems (KB2479943) — 2011-03-08",
    "Security Update for Remote Desktop Connection 7.0 Client (KB2483614) — 2011-03-08",
    "Security Update for Windows Fax Cover Page Editor (KB2491683) — 2011-04-12",
    "Security Update for Windows Fax Cover Page Editor (KB2506212) — 2011-04-12",
    "Security Update for Microsoft .NET Framework 3.5.1 for Windows 7 x64 (KB2446709) — 2011-04-12",
    "Security Update for JScript 5.8 and VBScript 5.8 (KB2510531) — 2011-04-12",
    "Security Update for Microsoft .NET Framework 3.5.1 for Windows 7 x64 (KB2478661) — 2011-06-14",
    "Security Update for Microsoft .NET Framework 4.0 for Windows 7 x64 (KB2478663) — 2011-06-14",
    "Security Update for Windows 7 for x64-based Systems (KB2503665) — 2011-06-14",
    "Security Update for Bluetooth Stack for Windows 7 x64 (KB2532531) — 2011-07-12",
    "Security Update for Windows Components for Windows 7 x64 (KB2570947) — 2011-09-13",
    "Security Update for Microsoft Active Accessibility for Windows 7 x64 (KB2564958) — 2011-10-11",
    "Security Update for Windows Media Center for Windows 7 x64 (KB2579686) — 2011-10-11",
    "Update for Windows 7 for x64-based Systems (KB2506014) — 2011-04-12",
    "Update for Windows 7 for x64-based Systems (KB2533623) — 2011-07-12",
)


class WindowsUpdateService(QObject):
    """Simulates downloads and installs without reading or changing real files."""

    changed = Signal()
    maintenanceModeChanged = Signal(bool)
    networkTransferRequested = Signal(str, int, str)

    MIN_AUTO_INTERVAL_DAYS = 14
    MAX_AUTO_INTERVAL_DAYS = 28
    AUTO_CHECK_RETRY_MS = 24 * 60 * 60 * 1000
    AUTO_START_DELAY_MS = (60_000, 180_000)
    RESUME_DELAY_MS = 8_000
    PHASE_DURATION_MS = (3_000, 6_000)
    TICK_INTERVAL_MS = 100

    def __init__(self, parent=None, *, seed: int | None = None):
        super().__init__(parent)
        self._rng = random.Random(seed if seed is not None else time.time_ns())
        self.running = False
        self._session_stopped = False
        self._maintenance_active = False
        self.updates: list[str] = []
        self.current_index = 0
        self.stage: str | None = None
        self.stage_progress = 0
        self.batch_progress = 0
        self.automatic_run = False
        self.network_available = True
        self._download_payload_bytes = 0
        self.status_message = "Windows is up to date (simulation)."
        self.settings_error: str | None = None

        try:
            state = load_windows_update_state()
        except (OSError, ValueError) as exc:
            self.settings_error = str(exc)
            self.state = self._new_state(automatic_enabled=False)
        else:
            self.state = state if state is not None else self._new_state()
            if state is None:
                self._save_state()
        self.updates = list(self.state["pending_updates"] or [])
        self.current_index = int(self.state["pending_index"])
        self.stage = self.state["pending_stage"]

        self._phase_duration_ms = 0
        self._phase_started_at = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(self.TICK_INTERVAL_MS)
        self._timer.timeout.connect(self._tick)
        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._automatic_check_due)
        self._resume_timer = QTimer(self)
        self._resume_timer.setSingleShot(True)
        self._resume_timer.timeout.connect(self._resume_pending_updates)

        if self.updates:
            self.status_message = (
                f"Updates paused at {self.current_index + 1} of {len(self.updates)}; "
                "they will resume after Windows starts."
            )
            self._resume_timer.start(self.RESUME_DELAY_MS)
        else:
            self._schedule_automatic_check()

    @property
    def automatic_enabled(self) -> bool:
        return bool(self.state["automatic_enabled"])

    @property
    def has_pending_updates(self) -> bool:
        return bool(self.updates)

    def start_updates(self, *, automatic: bool = False) -> bool:
        if self.running or self._session_stopped:
            return False
        self._auto_timer.stop()
        self._resume_timer.stop()
        self.automatic_run = bool(automatic)
        if not self.updates:
            count = self._rng.randint(7, 14)
            self.updates = self._rng.sample(UPDATE_CATALOG, count)
            self.current_index = 0
            self.stage = "downloading"
        elif self.stage is None:
            self.stage = "downloading"

        self.state["pending_updates"] = list(self.updates)
        self.state["pending_index"] = self.current_index
        self.state["pending_stage"] = self.stage
        self._set_next_automatic_check()
        self.running = True
        self._start_phase()
        return True

    def set_automatic_enabled(self, enabled: bool) -> None:
        if type(enabled) is not bool:
            raise ValueError("Automatic update preference must be enabled or disabled.")
        self.state["automatic_enabled"] = enabled
        self._save_state()
        if enabled:
            self._schedule_automatic_check()
        else:
            self._auto_timer.stop()
        self.changed.emit()

    def set_network_available(self, available: bool) -> None:
        available = bool(available)
        if self.network_available == available:
            return
        self.network_available = available
        if not self.running or self.stage != "downloading":
            return
        if not available and self._timer.isActive():
            elapsed_ms = min(
                self._phase_duration_ms,
                (time.monotonic() - self._phase_started_at) * 1000,
            )
            self.stage_progress = min(
                100, int(elapsed_ms * 100 / max(1, self._phase_duration_ms))
            )
            self._phase_started_at = time.monotonic() - elapsed_ms / 1000
            self._timer.stop()
            self.status_message = (
                "Waiting for the broadband connection to return before downloading "
                f"update {self.current_index + 1} of {len(self.updates)}."
            )
            self._set_maintenance_mode(False)
            self.changed.emit()
        elif available and not self._timer.isActive():
            self._phase_started_at = time.monotonic() - (
                self.stage_progress * self._phase_duration_ms / 100_000
            )
            remaining_bytes = int(
                self._download_payload_bytes * (100 - self.stage_progress) / 100
            )
            if remaining_bytes:
                self.networkTransferRequested.emit(
                    "incoming",
                    remaining_bytes,
                    f"Windows Update — {self.updates[self.current_index]}",
                )
            self.status_message = (
                f"Resuming download {self.current_index + 1} of {len(self.updates)}: "
                f"{self.updates[self.current_index]}"
            )
            self._set_maintenance_mode(True)
            self._timer.start()
            self.changed.emit()

    def cancel_updates(self) -> None:
        self._timer.stop()
        self._resume_timer.stop()
        was_running = self.running
        self.running = False
        self.updates = []
        self.current_index = 0
        self.stage = None
        self.stage_progress = 0
        self.batch_progress = 0
        self.state["pending_updates"] = None
        self.state["pending_index"] = 0
        self.state["pending_stage"] = None
        self.status_message = "The simulated update batch was canceled."
        if was_running or self._maintenance_active:
            self._set_maintenance_mode(False)
        self._save_state()
        self._schedule_automatic_check()
        self.changed.emit()

    def stop_session(self) -> None:
        """Pause active work at the current package when Windows closes."""
        self._session_stopped = True
        self._auto_timer.stop()
        self._resume_timer.stop()
        self._timer.stop()
        was_running = self.running
        self.running = False
        if self.updates and was_running:
            self.status_message = (
                f"Windows Update paused at {self.current_index + 1} of "
                f"{len(self.updates)}. It will resume next time Windows starts."
            )
        if was_running or self._maintenance_active:
            self._set_maintenance_mode(False)
        self.changed.emit()

    def _new_state(self, *, automatic_enabled: bool = True) -> dict[str, object]:
        return {
            "automatic_enabled": automatic_enabled,
            "next_auto_check_at": self._next_check_timestamp(),
            "last_install_at": None,
            "last_installed_updates": [],
            "completed_batches": 0,
            "pending_updates": None,
            "pending_index": 0,
            "pending_stage": None,
        }

    def _next_check_timestamp(self) -> float:
        days = self._rng.randint(
            self.MIN_AUTO_INTERVAL_DAYS,
            self.MAX_AUTO_INTERVAL_DAYS,
        )
        return time.time() + days * 24 * 60 * 60

    def _set_next_automatic_check(self) -> None:
        self.state["next_auto_check_at"] = self._next_check_timestamp()
        self._save_state()

    def _save_state(self) -> bool:
        try:
            save_windows_update_state(self.state)
        except (OSError, ValueError) as exc:
            self.settings_error = str(exc)
            self.changed.emit()
            return False
        self.settings_error = None
        return True

    def _schedule_automatic_check(self) -> None:
        self._auto_timer.stop()
        if (
            self._session_stopped
            or not self.automatic_enabled
            or self.updates
            or self.settings_error
        ):
            return
        remaining_ms = int(
            (float(self.state["next_auto_check_at"]) - time.time()) * 1000
        )
        if remaining_ms <= 0:
            delay_ms = self._rng.randint(*self.AUTO_START_DELAY_MS)
        else:
            delay_ms = min(remaining_ms, self.AUTO_CHECK_RETRY_MS)
        self._auto_timer.start(max(1_000, delay_ms))

    def _automatic_check_due(self) -> None:
        if self._session_stopped or not self.automatic_enabled:
            return
        if float(self.state["next_auto_check_at"]) > time.time():
            self._schedule_automatic_check()
            return
        self.start_updates(automatic=True)

    def _resume_pending_updates(self) -> None:
        if not self._session_stopped and self.updates:
            self.start_updates(automatic=False)

    def _start_phase(self) -> None:
        if self.current_index >= len(self.updates):
            self._finish_batch()
            return
        self._phase_duration_ms = self._rng.randint(*self.PHASE_DURATION_MS)
        self._phase_started_at = time.monotonic()
        self.stage_progress = 0
        action = "Downloading" if self.stage == "downloading" else "Installing"
        self.status_message = (
            f"{action} update {self.current_index + 1} of {len(self.updates)}: "
            f"{self.updates[self.current_index]}"
        )
        if self.stage == "downloading":
            self._download_payload_bytes = self._rng.randint(
                512 * 1024, 2 * 1024 * 1024
            )
            if not self.network_available:
                self.status_message = (
                    "Waiting for the broadband connection to return before "
                    f"downloading update {self.current_index + 1} of {len(self.updates)}."
                )
                self._set_maintenance_mode(False)
                self._save_state()
                self.changed.emit()
                return
            self.networkTransferRequested.emit(
                "incoming",
                self._download_payload_bytes,
                f"Windows Update — {self.updates[self.current_index]}",
            )
        self._set_maintenance_mode(True)
        self._timer.start()
        self._save_state()
        self.changed.emit()

    def _tick(self) -> None:
        if not self.running or self.stage is None:
            return
        elapsed_ms = (time.monotonic() - self._phase_started_at) * 1000
        self.stage_progress = min(100, int(elapsed_ms * 100 / self._phase_duration_ms))
        phase_index = 0 if self.stage == "downloading" else 1
        total_phases = max(1, len(self.updates) * 2)
        self.batch_progress = min(
            100,
            int(
                (self.current_index * 2 + phase_index + self.stage_progress / 100)
                * 100
                / total_phases
            ),
        )
        if elapsed_ms >= self._phase_duration_ms:
            self._advance_phase()
        else:
            self.changed.emit()

    def _advance_phase(self) -> None:
        if self.stage == "downloading":
            self.stage = "installing"
        else:
            self.current_index += 1
            if self.current_index >= len(self.updates):
                self._finish_batch()
                return
            self.stage = "downloading"
        self.state["pending_updates"] = list(self.updates)
        self.state["pending_index"] = self.current_index
        self.state["pending_stage"] = self.stage
        self._start_phase()

    def _finish_batch(self) -> None:
        self._timer.stop()
        self.running = False
        self.stage = None
        self.stage_progress = 100
        self.batch_progress = 100
        self.state["last_install_at"] = time.time()
        self.state["last_installed_updates"] = list(self.updates)
        self.state["completed_batches"] = int(self.state["completed_batches"]) + 1
        self.state["pending_updates"] = None
        self.state["pending_index"] = 0
        self.state["pending_stage"] = None
        self.status_message = (
            f"{len(self.updates)} updates installed. No restart is required (simulation)."
        )
        self._save_state()
        self._set_maintenance_mode(False)
        self._schedule_automatic_check()
        self.changed.emit()

    def _set_maintenance_mode(self, active: bool) -> None:
        active = bool(active)
        if self._maintenance_active == active:
            return
        self._maintenance_active = active
        self.maintenanceModeChanged.emit(active)


class WindowsUpdateApp(QWidget):
    """A Control Panel-style page for checking updates and setting auto-checks."""

    def __init__(self, service: WindowsUpdateService, parent=None):
        super().__init__(parent)
        self.service = service
        self.setObjectName("windowsUpdate")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title = QLabel("Windows Update")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #244d72;")
        layout.addWidget(title)
        self.status_label = QLabel()
        self.status_label.setObjectName("windowsUpdateStatus")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("windowsUpdateProgress")
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.update_list = QListWidget()
        self.update_list.setObjectName("windowsUpdateList")
        layout.addWidget(self.update_list, 1)

        self.automatic_checkbox = QCheckBox(
            "Check for and install updates automatically every 2–4 weeks"
        )
        self.automatic_checkbox.setObjectName("windowsUpdateAutomatic")
        self.automatic_checkbox.toggled.connect(service.set_automatic_enabled)
        layout.addWidget(self.automatic_checkbox)

        self.history_label = QLabel()
        self.history_label.setObjectName("windowsUpdateHistory")
        layout.addWidget(self.history_label)
        self.notice_label = QLabel(
            "Simulation only: no update files are downloaded or system files changed. "
            "These updates do not require restarting Windows. While they run, queued "
            "background AI work gets priority; active generation is never interrupted."
        )
        self.notice_label.setWordWrap(True)
        self.notice_label.setStyleSheet("color: #4a5e70;")
        layout.addWidget(self.notice_label)

        buttons = QHBoxLayout()
        self.check_button = QPushButton("Check for updates")
        self.check_button.setObjectName("windowsUpdateCheck")
        self.cancel_button = QPushButton("Cancel updates")
        self.cancel_button.setObjectName("windowsUpdateCancel")
        buttons.addWidget(self.check_button)
        buttons.addWidget(self.cancel_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.check_button.clicked.connect(
            lambda: service.start_updates(automatic=False)
        )
        self.cancel_button.clicked.connect(service.cancel_updates)
        service.changed.connect(self._refresh)
        self._refresh()

    def _refresh(self) -> None:
        service = self.service
        self.status_label.setText(service.status_message)
        self.progress_bar.setValue(service.batch_progress)
        self.progress_bar.setVisible(service.running or service.has_pending_updates)
        self.check_button.setEnabled(not service.running)
        self.check_button.setText(
            "Resume updates" if service.has_pending_updates and not service.running
            else "Checking for updates…" if service.running
            else "Check for updates"
        )
        self.cancel_button.setEnabled(service.running or service.has_pending_updates)
        self.automatic_checkbox.blockSignals(True)
        self.automatic_checkbox.setChecked(service.automatic_enabled)
        self.automatic_checkbox.blockSignals(False)

        if service.updates:
            titles = service.updates
            current_index = service.current_index
        else:
            titles = list(service.state["last_installed_updates"])
            current_index = len(titles)
        if self.update_list.count() != len(titles) or any(
            self.update_list.item(index).data(Qt.ItemDataRole.UserRole) != title
            for index, title in enumerate(titles)
        ):
            self.update_list.clear()
            for title in titles:
                item = QListWidgetItem(title)
                item.setData(Qt.ItemDataRole.UserRole, title)
                self.update_list.addItem(item)

        for index in range(self.update_list.count()):
            item = self.update_list.item(index)
            if index < current_index:
                label = "Installed"
            elif index == current_index and service.running:
                label = (
                    f"{service.stage.title()} — {service.stage_progress}%"
                    if service.stage
                    else "Working"
                )
            elif index == current_index and service.has_pending_updates:
                label = "Paused"
            elif not service.has_pending_updates and titles:
                label = "Installed"
            else:
                label = "Waiting"
            item.setText(f"{titles[index]}  —  {label}")

        last_update = service.state["last_install_at"]
        if last_update is None:
            history = "Last installed: Never"
        else:
            local_time = time.localtime(float(last_update))
            history = time.strftime("Last installed: %b %d, 2011 at %I:%M %p", local_time).replace(
                " 0", " "
            )
        history += f"   ·   Completed batches: {service.state['completed_batches']}"
        self.history_label.setText(history)
        if service.settings_error:
            self.notice_label.setText(
                "Could not save automatic-update settings: "
                + service.settings_error
                + "\n"
                + self._default_notice()
            )
        else:
            self.notice_label.setText(self._default_notice())

    def _default_notice(self) -> str:
        return (
            "Simulation only: no update files are downloaded or system files changed. "
            "These updates do not require restarting Windows. While they run, queued "
            "background AI work gets priority; active generation is never interrupted."
        )
