"""A small "Loading AI Model" box with a progress bar, the first time each model loads in a session.

llama.cpp doesn't say how far along a load is, so the bar is timed: it fills over however long that model took to
load last time (remembered in data/llm_load_times.json; a first-ever load is guessed from the file's size) and jumps
to 100% the moment the router reports the model ready. A watcher thread asks the router which models are loading.
"""
import json
import math
import threading
import time

from PySide6.QtCore import QObject, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .paths import DATA

TIMES_FILE = DATA / "llm_load_times.json"
POLL_SECONDS = 0.4


def _times():
    try:
        return json.loads(TIMES_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _remember(model_id, seconds):
    times = _times()
    old = times.get(model_id)
    times[model_id] = round(seconds if old is None else old * 0.4 + seconds * 0.6, 2)
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        TIMES_FILE.write_text(json.dumps(times, indent=2), encoding="utf-8")
    except OSError:
        pass


def _expected(model_id):
    known = _times().get(model_id)
    if known:
        return max(1.0, float(known))
    from . import ai_models
    m = ai_models.get(model_id)
    gb = (m.size / 1e9) if m is not None else 4.0
    return 2.0 + gb * 1.6                      # a guess until it's been loaded once


def _title(model_id):
    from . import ai_models
    m = ai_models.get(model_id)
    return m.title if m is not None else model_id


class _Watcher(QObject):
    states = Signal(dict)

    def __init__(self):
        super().__init__()
        self.running = True
        threading.Thread(target=self._run, daemon=True, name="llm-load-watch").start()

    def _run(self):
        from . import llm_server
        while self.running:
            if llm_server.running():
                try:
                    self.states.emit(llm_server.model_states())
                except RuntimeError:            # the Qt side has gone (ClaudeXP closing)
                    return
                time.sleep(POLL_SECONDS)
            else:
                time.sleep(2.0)


class LoadingBox(QWidget):
    """A little XP-style dialog by the clock. It never takes the keyboard focus from what you're typing in."""

    W, H = 318, 118

    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)
        self.resize(self.W, self.H)
        self.model = None
        self.title = ""
        self.t0 = 0.0
        self.expected = 1.0
        self.done_at = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.hide()

    def start(self, model_id):
        self.model, self.title = model_id, _title(model_id)
        self.t0, self.expected, self.done_at = time.monotonic(), _expected(model_id), None
        area = self.desktop.work_area()
        self.move(area.right() - self.W - 10, area.bottom() - self.H - 10)
        self.show()
        self.raise_()
        self.timer.start(50)

    def finish(self):
        if self.model is not None and self.done_at is None:
            self.done_at = time.monotonic()
            _remember(self.model, self.done_at - self.t0)
            QTimer.singleShot(900, self.close_box)

    def close_box(self):
        self.timer.stop()
        self.model = None
        self.hide()

    def fraction(self):
        if self.done_at is not None:
            return 1.0
        r = (time.monotonic() - self.t0) / self.expected
        if r < 1:
            return 0.9 * r
        return 0.9 + 0.09 * (1 - math.exp(-(r - 1) * 1.5))      # taking longer than last time: creep, never 100%

    def _tick(self):
        self.raise_()                                            # stay above windows opened meanwhile
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        # the frame and title bar
        p.setPen(QPen(QColor("#0831D9"), 1))
        p.setBrush(QColor("#0054E3"))
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 6, 6)
        g = QLinearGradient(0, 0, 0, 24)
        g.setColorAt(0, QColor("#3A8CFF"))
        g.setColorAt(0.5, QColor("#0058EE"))
        g.setColorAt(1, QColor("#0047D0"))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(QRectF(1, 1, w - 2, 24), 6, 6)
        p.fillRect(QRect(4, 25, w - 8, h - 29), QColor("#ECE9D8"))
        if not hasattr(self, "_icon"):
            from .aimodels_cpl import ai_icon
            self._icon = ai_icon(16)
        p.drawPixmap(6, 5, self._icon)
        p.setPen(QColor("white"))
        p.setFont(QFont("Trebuchet MS", 9, QFont.Bold))
        p.drawText(QRect(28, 1, w - 34, 24), Qt.AlignVCenter, "Loading AI Model")
        # the text
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("#000000"))
        frac = self.fraction()
        line = f"Loading {self.title} into memory..." if self.done_at is None else f"{self.title} is ready."
        p.drawText(QRect(14, 32, w - 28, 16), Qt.AlignLeft | Qt.AlignVCenter, line)
        # the XP progress bar: green blocks in a sunken white trough
        bar = QRect(14, 56, w - 74, 16)
        p.setPen(QPen(QColor("#686868"), 1))
        p.setBrush(QColor("#FFFFFF"))
        p.drawRoundedRect(QRectF(bar).adjusted(0.5, 0.5, -0.5, -0.5), 3, 3)
        inner = bar.adjusted(3, 3, -3, -3)
        filled = int(inner.width() * frac)
        p.setPen(Qt.NoPen)
        x = inner.left()
        while x + 6 <= inner.left() + filled:
            gg = QLinearGradient(0, inner.top(), 0, inner.bottom())
            gg.setColorAt(0, QColor("#ACEDAD"))
            gg.setColorAt(0.45, QColor("#28C830"))
            gg.setColorAt(1, QColor("#1E9E24"))
            p.setBrush(gg)
            p.drawRect(QRectF(x, inner.top(), 6, inner.height()))
            x += 8
        p.setPen(QColor("#000000"))
        p.setFont(QFont("Tahoma", 8, QFont.Bold))
        p.drawText(QRect(bar.right() + 6, bar.top(), 46, bar.height()), Qt.AlignVCenter | Qt.AlignLeft,
                   f"{int(frac * 100)}%")
        p.setFont(QFont("Tahoma", 7))
        p.setPen(QColor("#555555"))
        p.drawText(QRect(14, 80, w - 28, 28), Qt.TextWordWrap,
                   "This happens once per session for each model. Replies may wait until it's done.")
        p.end()

    def mousePressEvent(self, _e):
        self.close_box()                                         # click to dismiss (loading carries on)


class LoadingNotices(QObject):
    """Watches the router and shows the box for each model's first load this session."""

    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.box = LoadingBox(desktop)
        self.seen = set()                  # models that have been loaded (or shown) this session
        self.queue = []
        self.watcher = _Watcher()
        self.watcher.states.connect(self._states, Qt.QueuedConnection)
        desktop.destroyed.connect(self._stop)

    def _stop(self, *_):
        self.watcher.running = False

    def _states(self, states):
        box = self.box
        for model_id, state in states.items():
            if state == "loading" and model_id not in self.seen and model_id not in self.queue:
                self.queue.append(model_id)
            elif state == "loaded" and model_id not in self.seen and model_id != box.model:
                self.seen.add(model_id)            # loaded before we noticed: nothing to show
                if model_id in self.queue:
                    self.queue.remove(model_id)
        if box.model is not None and box.done_at is None:
            state = states.get(box.model)
            if state == "loaded":
                self.seen.add(box.model)
                box.finish()
            elif state != "loading":               # the load failed or was cancelled
                self.seen.add(box.model)
                box.close_box()
        if (box.model is None) and self.queue:
            model_id = self.queue.pop(0)
            if states.get(model_id) == "loading":
                box.start(model_id)


_notices = None


def start(desktop):
    global _notices
    if _notices is None or _notices.desktop is not desktop:
        if _notices is not None:
            _notices._stop()
        _notices = LoadingNotices(desktop)
    return _notices
