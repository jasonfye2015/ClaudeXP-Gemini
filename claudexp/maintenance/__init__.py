"""System maintenance that 'buys time' for the model: Windows Update, the virus scanner and
Disk Defragmenter.

Each task runs for at least a minimum time and never finishes while the model broker still has
background work queued; its progress bar follows the background batch. The coordinator starts a
fitting task when a big batch of background work begins (like the catch-up after the PC was off).
"""
import random
import time

from PySide6.QtCore import QObject

from .. import broker, network

COVER_MIN_JOBS = 3          # a batch this big gets a maintenance task to hide behind
COVER_COOLDOWN = 40 * 60    # seconds between automatic tasks
IDLE_FOR_DEFRAG = 3 * 60    # seconds without input before Disk Defragmenter may run by itself


class CoverClock:
    """Progress 0..1 for a maintenance task."""

    def __init__(self, min_seconds):
        self.start = time.monotonic()
        self.min_seconds = max(1.0, min_seconds)
        self.broker = broker.get()

    def fraction(self):
        f = min(1.0, (time.monotonic() - self.start) / self.min_seconds)
        b = self.broker
        if b.background_pending():
            batch = b.bg_done / max(1, b.bg_total)
            f = min(f, 0.1 + 0.87 * batch, 0.97)
        return f

    def done(self):
        return self.fraction() >= 1.0


class Maintenance(QObject):
    def __init__(self, desktop):
        super().__init__(desktop)
        from .antivirus import AntiVirus
        from .updates import AutoUpdates
        self.desktop = desktop
        self.updates = AutoUpdates(desktop)
        self.antivirus = AntiVirus(desktop)
        self.last_cover = -COVER_COOLDOWN
        broker.get().batch_progress.connect(self._batch)

    def _logged_in(self):
        return self.desktop.isVisible()

    def busy(self):
        return self.updates.busy() or self.antivirus.busy() or self._defrag_running()

    def _defrag_running(self):
        from . import defrag
        return defrag.running()

    def _batch(self, done, total):
        if total - done < COVER_MIN_JOBS or not self._logged_in() or self.busy():
            return
        if time.monotonic() - self.last_cover < COVER_COOLDOWN:
            return
        self.start_cover()

    def start_cover(self, kind=None):
        """Start a maintenance task (a random fitting one unless kind is given)."""
        options = []
        if network.is_connected():
            options += ["updates", "liveupdate"]
        options += ["scan"]
        if time.monotonic() - self.desktop.last_input >= IDLE_FOR_DEFRAG:
            options.append("defrag")
        kind = kind or random.choice(options)
        self.last_cover = time.monotonic()
        if kind == "updates":
            self.updates.start_download()
        elif kind == "liveupdate":
            self.antivirus.live_update(automatic=True)
        elif kind == "scan":
            self.antivirus.scan(automatic=True)
        elif kind == "defrag":
            from . import defrag
            defrag.launch(self.desktop, automatic=True)


_maintenance = None


def install(desktop):
    global _maintenance
    _maintenance = Maintenance(desktop)
    return _maintenance


def get():
    return _maintenance
