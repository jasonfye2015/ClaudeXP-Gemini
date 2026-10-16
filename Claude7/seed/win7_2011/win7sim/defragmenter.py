"""A looping, purely visual Windows 7 disk-defragmentation simulation."""

from __future__ import annotations

import random
import time

from PySide6.QtCore import QObject, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QDoubleSpinBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .config import (
    DEFRAGMENTER_MAX_CYCLE_DURATION_MS,
    DEFRAGMENTER_MAX_RESET_PAUSE_MS,
    DEFRAGMENTER_MIN_CYCLE_DURATION_MS,
    DEFRAGMENTER_MIN_RESET_PAUSE_MS,
    load_defragmenter_settings,
    save_defragmenter_settings,
)


class DefragmenterService(QObject):
    changed = Signal()
    maintenanceModeChanged = Signal(bool)
    settingsError = Signal(str)

    COLUMNS = 80
    ROWS = 44
    BLOCK_BATCH_WEIGHTS = (75, 15, 5, 3, 2)
    AVERAGE_BLOCKS_PER_TICK = 1.42
    FRAME_INTERVAL_MS = 16
    CYCLE_DURATION_MS = 42_000
    RESET_PAUSE_MS = 1_400
    # Keep the animation at or below about 60 updates per second so each small
    # block movement remains visible instead of demanding a high-speed timer.
    MIN_CYCLE_DURATION_MS = DEFRAGMENTER_MIN_CYCLE_DURATION_MS
    MAX_CYCLE_DURATION_MS = DEFRAGMENTER_MAX_CYCLE_DURATION_MS
    MIN_RESET_PAUSE_MS = DEFRAGMENTER_MIN_RESET_PAUSE_MS
    MAX_RESET_PAUSE_MS = DEFRAGMENTER_MAX_RESET_PAUSE_MS
    COLORS = {
        "contiguous": "#1886c7",

        "fragmented": "#db4848",

        "system": "#68a343",

        "free": "#f0f2f4",
    }

    def __init__(self, parent=None, *, seed: int | None = None):

        super().__init__(parent)

        self._seed = seed if seed is not None else time.time_ns()

        self._drive_states = {
            drive: {
                "completed_passes": 0,
                "progress": 0,
                "settled_cells": 0,
                "cells": [],
                "target_cells": [],
            }
            for drive in self.AVAILABLE_DRIVES
    }

    def __init__(self, parent=None, *, seed: int | None = None):
        super().__init__(parent)
        self._seed = seed if seed is not None else time.time_ns()
        self.completed_passes = 0
        self.running = False
        self.paused = False
        self.progress = 0
        self.status_message = "Ready. Drive C: is fragmented (simulation)."
        self._settled_cells = 0
        self._maintenance_active = False
        saved_settings = load_defragmenter_settings({
            "cycle_duration_ms": self.CYCLE_DURATION_MS,
            "reset_pause_ms": self.RESET_PAUSE_MS,
        })
        self.cycle_duration_ms = saved_settings["cycle_duration_ms"]
        self.reset_pause_ms = saved_settings["reset_pause_ms"]
        self._step_rng = random.Random(self._seed ^ 0xD3F4A6)
        self.cells: list[str] = []
        self._target_cells: list[str] = []
        self._make_messy_layout()

        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._update_timer_interval()
        self._timer.timeout.connect(self._tick)
        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.setInterval(self.reset_pause_ms)
        self._reset_timer.timeout.connect(self._begin_next_pass)

    @property
    def fragmented_blocks(self) -> int:
        return self.cells.count("fragmented")

    @property
    def estimated_remaining_ms(self) -> int | None:
        if not self.running or self.progress >= 100 or not self.cells:
            return None
        remaining_cells = len(self.cells) - self._settled_cells
        return (
            self.cycle_duration_ms * remaining_cells + len(self.cells) - 1
        ) // len(self.cells)

    @property
    def time_remaining_text(self) -> str:
        if self.paused:
            return "Paused — countdown stopped."
        remaining_ms = self.estimated_remaining_ms
        if remaining_ms is not None:
            remaining_seconds = (remaining_ms + 999) // 1000
            if remaining_seconds >= 60:
                minutes, seconds = divmod(remaining_seconds, 60)
                remaining = f"{minutes}m {seconds:02d}s"
            else:
                remaining = f"{remaining_seconds}s"
            return f"Estimated time remaining: {remaining}"
        if self.progress >= 100:
            return "Pass complete — preparing the next pass (no countdown)."
        return "Ready — no countdown."

    def set_cycle_duration_ms(self, duration_ms: int) -> None:
        duration_ms = max(
            self.MIN_CYCLE_DURATION_MS,
            min(self.MAX_CYCLE_DURATION_MS, int(duration_ms)),
        )
        if duration_ms == self.cycle_duration_ms:
            return
        self.cycle_duration_ms = duration_ms
        self._update_timer_interval()
        self._save_timing_settings()
        self.changed.emit()

    def _update_timer_interval(self) -> None:
        total_cells = self.COLUMNS * self.ROWS
        expected_ticks = total_cells / self.AVERAGE_BLOCKS_PER_TICK
        interval_ms = round(self.cycle_duration_ms / expected_ticks)
        self._timer.setInterval(max(self.FRAME_INTERVAL_MS, interval_ms))

    def set_reset_pause_ms(self, pause_ms: int) -> None:
        pause_ms = max(
            self.MIN_RESET_PAUSE_MS,
            min(self.MAX_RESET_PAUSE_MS, int(pause_ms)),
        )
        if pause_ms == self.reset_pause_ms:
            return
        self.reset_pause_ms = pause_ms
        self._reset_timer.setInterval(pause_ms)
        if self._reset_timer.isActive():
            self._reset_timer.start()
        self._save_timing_settings()
        self.changed.emit()

    def _save_timing_settings(self) -> None:
        try:
            save_defragmenter_settings({
                "cycle_duration_ms": self.cycle_duration_ms,
                "reset_pause_ms": self.reset_pause_ms,
            })
        except (OSError, ValueError) as exc:
            self.settingsError.emit(str(exc))

    def start(self) -> None:
        if self.running:
            return
        if self.progress >= 100:
            self._begin_next_pass()
        self.running = True
        self.paused = False
        self.status_message = (
            f"Defragmenting Drive C: — pass {self.completed_passes + 1} "
            "(simulation)."
        )
        self._set_maintenance_mode(True)
        self._timer.start()
        self.changed.emit()

    def pause(self) -> None:
        if not self.running:
            return
        self._timer.stop()
        self._reset_timer.stop()
        self.running = False
        self.paused = True
        self.status_message = f"Paused at {self.progress}%."
        self._set_maintenance_mode(False)
        self.changed.emit()

    def stop(self) -> None:
        self._timer.stop()
        self._reset_timer.stop()
        self.running = False
        self.paused = False
        self.progress = 0
        self._settled_cells = 0
        self._make_messy_layout()
        self.status_message = "Stopped. Drive C: reset to a fragmented layout (simulation)."
        self._set_maintenance_mode(False)
        self.changed.emit()

    def _tick(self) -> None:
        if not self.running:
            return
        total_cells = len(self.cells)
        batch_size = self._step_rng.choices(
            (1, 2, 3, 4, 5),
            weights=self.BLOCK_BATCH_WEIGHTS,
            k=1,
        )[0]
        settled = min(total_cells, self._settled_cells + batch_size)
        for index in range(self._settled_cells, settled):
            self.cells[index] = self._target_cells[index]
        self._settled_cells = settled
        self.progress = settled * 100 // total_cells
        if settled >= total_cells:
            self._finish_pass()
        else:
            self.status_message = (
                f"Defragmenting Drive C: {self.progress}% — "
                f"{self.fragmented_blocks:,} fragmented blocks remain."
            )
            self.changed.emit()

    def _finish_pass(self) -> None:
        self.progress = 100
        self.completed_passes += 1
        self.status_message = (
            f"Pass {self.completed_passes} complete. Preparing a new fragmented "
            "layout for the next simulated pass…"
        )
        self._timer.stop()
        self.changed.emit()
        self._reset_timer.start()

    def _begin_next_pass(self) -> None:
        self._make_messy_layout()
        self.progress = 0
        self._settled_cells = 0
        self.status_message = (
            f"New fragmented layout ready — defragmenting pass "
            f"{self.completed_passes + 1} (simulation)."
        )
        self.changed.emit()
        if self.running:
            self._timer.start()

    def _make_messy_layout(self) -> None:
        total = self.COLUMNS * self.ROWS
        rng = random.Random(self._seed + self.completed_passes)
        fragmented = int(total * 0.19)
        contiguous = int(total * 0.44)
        system = int(total * 0.13)
        free = total - fragmented - contiguous - system
        cells = (
            ["fragmented"] * fragmented
            + ["contiguous"] * contiguous
            + ["system"] * system
            + ["free"] * free
        )
        rng.shuffle(cells)
        self.cells = cells
        self._target_cells = (
            ["system"] * system
            + ["contiguous"] * (contiguous + fragmented)
            + ["free"] * free
        )

    def _set_maintenance_mode(self, active: bool) -> None:
        active = bool(active)
        if self._maintenance_active == active:
            return
        self._maintenance_active = active
        self.maintenanceModeChanged.emit(active)


class DiskMapWidget(QWidget):
    """Large, colored block map that visibly consolidates as defrag progresses."""

    def __init__(self, service: DefragmenterService, parent=None):
        super().__init__(parent)
        self.service = service
        self.setObjectName("diskMap")
        self.setMinimumSize(720, 390)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._colors = {
            category: QColor(color)
            for category, color in service.COLORS.items()
        }
        service.changed.connect(self.update)

    def sizeHint(self) -> QSize:
        return QSize(790, 435)

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt event name
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(self.rect(), QColor("#15212b"))

        margin = 22
        available_width = max(1, self.width() - margin * 2)
        available_height = max(1, self.height() - margin * 2)
        cell = max(
            2,
            int(min(
                available_width / self.service.COLUMNS,
                available_height / self.service.ROWS,
            )),
        )
        gap = max(1, cell // 7)
        map_width = self.service.COLUMNS * (cell + gap) - gap
        map_height = self.service.ROWS * (cell + gap) - gap
        left = (self.width() - map_width) // 2
        top = (self.height() - map_height) // 2

        for index, category in enumerate(self.service.cells):
            row, column = divmod(index, self.service.COLUMNS)
            x = left + column * (cell + gap)
            y = top + row * (cell + gap)
            painter.fillRect(
                x, y, cell, cell, self._colors[category]
            )

        if self.service.running and self.service.progress < 100:
            marker_x = left + map_width * self.service.progress // 100
            painter.setPen(QPen(QColor("#ffe06b"), 2))
            painter.drawLine(marker_x, top - 4, marker_x, top + map_height + 3)
        painter.setPen(QPen(QColor("#52697b"), 1))
        painter.drawRect(left - 1, top - 1, map_width + 1, map_height + 1)


class DiskDefragmenterApp(QWidget):
    """Full-drive visualization with a repeating synthetic defragmentation pass."""

    def __init__(self, service: DefragmenterService, parent=None):
        super().__init__(parent)
        self.service = service
        self.setObjectName("diskDefragmenter")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        heading = QHBoxLayout()
        title = QLabel("Disk Defragmenter")
        title.setStyleSheet("font-size: 17pt; font-weight: bold; color: #244d72;")
        heading.addWidget(title)
        heading.addStretch(1)
        heading.addWidget(QLabel("Drive:"))
        self.drive_selector = QComboBox()
        self.drive_selector.setObjectName("driveSelector")
        for drive, label in (
            ("C:", "C: (Internal HD)"),
            ("F:", "F: (External HD)"),
        ):
            self.drive_selector.addItem(label, drive)
        self.drive_selector.setCurrentIndex(
            self.drive_selector.findData(service.selected_drive)
        )
        self.drive_selector.setToolTip(
            "Choose a simulated hard drive. No real drives or files are accessed."
        )
        heading.addWidget(self.drive_selector)
        layout.addLayout(heading)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.disk_map = DiskMapWidget(service)
        layout.addWidget(self.disk_map, 1)

        legend = QHBoxLayout()
        legend.addWidget(QLabel("Disk map:"))
        self._add_legend_item(legend, "Contiguous files", "contiguous")
        self._add_legend_item(legend, "Fragmented files", "fragmented")
        self._add_legend_item(legend, "System files", "system")
        self._add_legend_item(legend, "Free space", "free")
        legend.addStretch(1)
        layout.addLayout(legend)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.time_remaining_label = QLabel()
        self.time_remaining_label.setObjectName("timeRemainingLabel")
        layout.addWidget(self.time_remaining_label)

        timing_controls = QHBoxLayout()
        timing_controls.addWidget(QLabel("Pass duration:"))
        self.pass_duration_control = QDoubleSpinBox()
        self.pass_duration_control.setObjectName("passDurationControl")
        self.pass_duration_control.setRange(
            self.service.MIN_CYCLE_DURATION_MS / 1000,
            self.service.MAX_CYCLE_DURATION_MS / 1000,
        )
        self.pass_duration_control.setDecimals(1)
        self.pass_duration_control.setSingleStep(1.0)
        self.pass_duration_control.setSuffix(" s")
        self.pass_duration_control.setToolTip(
            "Time for one defragmentation pass. The 40-second minimum keeps "
            "the one-to-five-block animation visible. Changing it preserves progress."
        )
        self.pass_duration_control.setValue(self.service.cycle_duration_ms / 1000)
        timing_controls.addWidget(self.pass_duration_control)

        timing_controls.addSpacing(12)
        timing_controls.addWidget(QLabel("Reset pause:"))
        self.reset_pause_control = QDoubleSpinBox()
        self.reset_pause_control.setObjectName("resetPauseControl")
        self.reset_pause_control.setRange(
            self.service.MIN_RESET_PAUSE_MS / 1000,
            self.service.MAX_RESET_PAUSE_MS / 1000,
        )
        self.reset_pause_control.setDecimals(1)
        self.reset_pause_control.setSingleStep(0.1)
        self.reset_pause_control.setSuffix(" s")
        self.reset_pause_control.setToolTip(
            "Wait between completed passes. Changing it restarts an active reset pause."
        )
        self.reset_pause_control.setValue(self.service.reset_pause_ms / 1000)
        timing_controls.addWidget(self.reset_pause_control)
        timing_controls.addStretch(1)
        layout.addLayout(timing_controls)

        controls = QHBoxLayout()
        self.mode_note = QLabel(
            "Simulation only — no real drive is read or modified. "
            "While running, queued background AI work receives priority."
        )
        self.mode_note.setWordWrap(True)
        self.mode_note.setStyleSheet("color: #4a5e70;")
        controls.addWidget(self.mode_note, 1)
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        controls.addWidget(self.pause_button)
        controls.addWidget(self.stop_button)
        layout.addLayout(controls)

        self.pause_button.clicked.connect(self._toggle_pause)
        self.stop_button.clicked.connect(service.stop)
        self.drive_selector.currentIndexChanged.connect(
            lambda index: service.select_drive(
                service.AVAILABLE_DRIVES[index]
            )
        )
        self.pass_duration_control.valueChanged.connect(
            lambda seconds: service.set_cycle_duration_ms(round(seconds * 1000))
        )
        self.reset_pause_control.valueChanged.connect(
            lambda seconds: service.set_reset_pause_ms(round(seconds * 1000))
        )
        service.changed.connect(self._refresh)
        self._refresh()

    def _add_legend_item(self, layout: QHBoxLayout, label: str, category: str) -> None:
        swatch = QFrame()
        swatch.setFixedSize(13, 13)
        swatch.setStyleSheet(
            f"background: {self.service.COLORS[category]}; "
            "border: 1px solid #53616c;"
        )
        layout.addWidget(swatch)
        layout.addWidget(QLabel(label))

    def _toggle_pause(self) -> None:
        if self.service.running:
            self.service.pause()
        else:
            self.service.start()

    def _refresh(self) -> None:
        selector_index = self.drive_selector.findData(self.service.selected_drive)
        if selector_index != self.drive_selector.currentIndex():
            was_blocked = self.drive_selector.blockSignals(True)
            self.drive_selector.setCurrentIndex(selector_index)
            self.drive_selector.blockSignals(was_blocked)
        self.status_label.setText(
            f"{self.service.status_message}  "
            f"Fragmented blocks: {self.service.fragmented_blocks:,} · "
            f"Completed passes: {self.service.completed_passes}"
        )
        self.time_remaining_label.setText(self.service.time_remaining_text)
        self.progress_bar.setValue(self.service.progress)
        self._set_control_value(
            self.pass_duration_control, self.service.cycle_duration_ms / 1000
        )
        self._set_control_value(
            self.reset_pause_control, self.service.reset_pause_ms / 1000
        )
        self.pause_button.setText(
            "Pause" if self.service.running else "Resume" if self.service.paused else "Start"
        )
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(self.service.running or self.service.paused)
        self.disk_map.update()

    @staticmethod
    def _set_control_value(control: QDoubleSpinBox, value: float) -> None:
        was_blocked = control.blockSignals(True)
        control.setValue(value)
        control.blockSignals(was_blocked)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt event name
        self.service.stop()
        super().closeEvent(event)
