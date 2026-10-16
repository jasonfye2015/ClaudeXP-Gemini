from __future__ import annotations

import random
from enum import Enum

from PySide6.QtCore import QObject, QTimer, Signal


class ServiceState(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    MAINTENANCE = "maintenance"
    SLOWDOWN = "slowdown"


class ConnectionSimulator(QObject):
    """Simulates in-world service interruptions only for an active desktop session."""

    stateChanged = Signal(object, str)
    backgroundWorkPausedChanged = Signal(bool)

    def __init__(self, parent: QObject | None = None, rng=None) -> None:
        super().__init__(parent)
        self._rng = rng or random.Random()
        self.state = ServiceState.CONNECTED
        self._restore_timer = QTimer(self)
        self._restore_timer.setSingleShot(True)
        self._restore_timer.timeout.connect(self._restore_connection)
        self._next_event_timer = QTimer(self)
        self._next_event_timer.setSingleShot(True)
        self._next_event_timer.timeout.connect(self._begin_random_interruption)
        self.schedule_next_interruption()

    @property
    def background_work_paused(self) -> bool:
        return self.state is not ServiceState.CONNECTED

    @property
    def chat_available(self) -> bool:
        return self.state in (ServiceState.CONNECTED, ServiceState.SLOWDOWN)

    def schedule_next_interruption(self) -> None:
        # Interruptions are rare, and these timers exist only while the desktop does.
        self._next_event_timer.start(self._rng.randint(240, 540) * 1000)

    def stop(self) -> None:
        """Stop all simulated world activity when the desktop session ends."""
        self._next_event_timer.stop()
        self._restore_timer.stop()

    def begin_interruption(self, state: ServiceState, duration_ms: int) -> None:
        if state is ServiceState.CONNECTED:
            raise ValueError("An interruption must use a non-connected service state.")
        was_paused = self.background_work_paused
        self.state = state
        self.stateChanged.emit(state, self.status_text)
        if not was_paused:
            self.backgroundWorkPausedChanged.emit(True)
        self._next_event_timer.stop()
        self._restore_timer.start(max(1, duration_ms))

    def _begin_random_interruption(self) -> None:
        state = self._rng.choices(
            (
                ServiceState.DISCONNECTED,
                ServiceState.MAINTENANCE,
                ServiceState.SLOWDOWN,
            ),
            weights=(4, 2, 4),
            k=1,
        )[0]
        duration_seconds = {
            ServiceState.DISCONNECTED: self._rng.randint(18, 45),
            ServiceState.MAINTENANCE: self._rng.randint(30, 75),
            ServiceState.SLOWDOWN: self._rng.randint(60, 150),
        }[state]
        self.begin_interruption(state, duration_seconds * 1000)

    def _restore_connection(self) -> None:
        was_paused = self.background_work_paused
        self.state = ServiceState.CONNECTED
        self.stateChanged.emit(self.state, self.status_text)
        if was_paused:
            self.backgroundWorkPausedChanged.emit(False)
        self.schedule_next_interruption()

    @property
    def status_text(self) -> str:
        return {
            ServiceState.CONNECTED: "Internet: Connected",
            ServiceState.DISCONNECTED: "Internet: Disconnected",
            ServiceState.MAINTENANCE: "Service: Maintenance",
            ServiceState.SLOWDOWN: "Service: Slow response",
        }[self.state]
