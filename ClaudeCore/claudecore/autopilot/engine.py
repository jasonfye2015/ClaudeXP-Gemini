"""The autopilot engine: legs, the scheduler that keeps two to four of them going, the pause and stop controls.

A leg is a generator. It yields a number of seconds to wait, or a predicate (a callable; the engine polls it until
it's true or a timeout passes), and it uses the shared hands and voice through its context:

    class WatchTV(Leg):
        key, title, kind = "tv", "ClaudeTV", BACKGROUND
        def run(self, ctx):
            yield from ctx.hands.take(self.key)
            try:
                ... yield from ctx.hands.click(button) ...
            finally:
                ctx.hands.release(self.key)
            yield 60 * 20                       # watch for twenty minutes

Kinds: ALWAYS (the messengers: open the whole session), BACKGROUND (TV, a game, the MUCK: long, up to two at once
beside the messengers), FOREGROUND (mail, the Web, a roleplay, a break: one at a time, in front). An adapter (one
per computer) hands the engine its legs; the engine knows nothing of the computer itself.
"""
import random
import time
import traceback

from PySide6.QtCore import QEvent, QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication

from .hud import Banner, Cursor, Glow, Hands
from .voice import Voice

ALWAYS, BACKGROUND, FOREGROUND = "always", "background", "foreground"
TICK_MS = 100
WIND_DOWN_STEPS = 600


class LegEnding(BaseException):
    """Thrown into a leg that's being cut short (Stop, or another leg asked for): its finally blocks run, and may
    still use the hands to close what it opened - straight through, without the waits."""


class Leg:
    key = ""
    title = ""
    blurb = ""                  # one line for the settings panel: what he does
    kind = FOREGROUND
    minutes = (15, 40)          # how long one stretch lasts, before the pace
    weight = 1.0                # how often it's picked, among its kind
    cooldown = 10 * 60          # seconds before the same leg can start again

    def run(self, ctx):
        yield 1

    def duration(self, pace):
        lo, hi = self.minutes
        return random.uniform(lo, hi) * 60 * pace


class Context:
    """What a leg gets: the desktop, the hands, the voice, the settings, the clock, and a way to say what it's up to."""

    def __init__(self, engine):
        self.engine = engine
        self.desktop = engine.desktop
        self.hands = engine.hands
        self.voice = engine.voice
        self.settings = engine.settings
        self.pace = engine.settings.get("pace", 1.0)

    def status(self, text):
        self.engine.set_status(text)

    def note(self, text):
        self.engine.log(text)

    @property
    def stopping(self):
        return self.engine.stopping

    def allowed(self, key):
        return key in self.engine.settings.get("allowed", [])


class _Task:
    def __init__(self, leg, gen, until):
        self.leg, self.gen, self.until = leg, gen, until
        self.wake = 0.0
        self.waiting = None         # (predicate, deadline)


class Autopilot(QObject):
    """One session of Kithylin at the computer. start() puts up the HUD and begins the legs; the user's own mouse or
    keyboard pauses him; Stop winds the legs down (their finally blocks close what they opened)."""
    changed = Signal()              # running / paused / stopped
    DEFAULTS = {"allowed": ["messengers", "mail", "browse", "tv", "rpg", "muck", "roleplay", "idle", "comics",
                            "portfolios", "pictures", "miscart", "artcds", "camroll", "stories", "chatlogs", "explore",
                            "wikipedia", "music", "journal"], "offered": [],
                "hours": 0, "pace": 1.0, "voice": "auto", "whole_movies": True, "adult_web": False,
                "pause_on_input": True,
                "background_slots": 2}

    def __init__(self, desktop, adapter, settings=None):
        super().__init__(desktop)
        self.desktop = desktop
        self.adapter = adapter
        self.settings = dict(self.DEFAULTS)
        self.settings.update(settings or {})
        self.running = self.paused = self.stopping = False
        self.tasks = {}
        self.last_run = {}
        self.started_at = None
        self.ends_at = None
        self.next_foreground = 0.0
        self.next_background = 0.0
        self.recent = []
        self.cursor = Cursor(desktop)
        self.cursor.hide()
        self.glow = Glow(desktop)
        self.banner = Banner(desktop, self.toggle_pause, self.stop)
        self.banner.hide()
        self.hands = Hands(desktop, self.cursor, self.settings.get("pace", 1.0))
        self.voice = Voice(self.settings.get("voice", "auto"))
        self.timer = QTimer(self, interval=TICK_MS, timeout=self._tick)
        self.legs = {leg.key: leg for leg in adapter.legs()}
        self.filter_on = False
        self.claims = set()                 # buddies a leg has to itself (a roleplay), for the others to leave be

    # ---- the session -----------------------------------------------------------------------------------------
    def start(self):
        if self.running:
            return
        self.running, self.paused, self.stopping = True, False, False
        self.started_at = time.monotonic()
        hours = float(self.settings.get("hours") or 0)
        self.ends_at = self.started_at + hours * 3600 if hours > 0 else None
        self.glow.start()
        self.banner.set_paused(False)
        self.banner.show()
        self.banner.place()
        self.cursor.show()
        self.cursor.raise_()
        if self.settings.get("pause_on_input", True):
            QApplication.instance().installEventFilter(self)
            self.filter_on = True
        self.log("Kithylin sat down at the computer.")
        self.set_status("Getting settled...")
        self.next_foreground = time.monotonic() + random.uniform(20, 60) * self.hands.pace
        self.next_background = time.monotonic() + random.uniform(5, 20)
        for leg in self.legs.values():
            if leg.kind == ALWAYS and leg.key in self.settings["allowed"]:
                self._start_leg(leg)
        self.timer.start()
        self.changed.emit()

    def toggle_pause(self, *_):
        self.pause("" if not self.paused else None) if not self.paused else self.resume()

    def pause(self, why=""):
        if not self.running or self.paused:
            return
        self.paused = True
        self.voice.stop()
        self.glow.paused = True
        self.banner.set_paused(True, why or "")
        self.cursor.hide()
        self.log("Paused" + (f" ({why})" if why else "") + ".")
        self.changed.emit()

    def resume(self):
        if not self.running or not self.paused:
            return
        self.paused = False
        self.glow.paused = False
        self.banner.set_paused(False)
        self.cursor.show()
        self.cursor.raise_()
        for task in self.tasks.values():            # whatever they were waiting for, give them a moment first
            task.wake = max(task.wake, time.monotonic() + 1.5)
        self.log("Resumed.")
        self.changed.emit()

    def stop(self, *_):
        if not self.running:
            return
        self.stopping = True
        self.set_status("Logging off...")
        for key in list(self.tasks):
            self._finish(key, closing=True)
        self.timer.stop()
        self.running = self.paused = False
        self.voice.stop()
        if self.filter_on:
            QApplication.instance().removeEventFilter(self)
            self.filter_on = False
        self.glow.stop()
        self.banner.hide()
        self.cursor.hide()
        mins = int((time.monotonic() - (self.started_at or time.monotonic())) / 60)
        self.log(f"Kithylin got up after {mins} minutes.")
        self.changed.emit()

    def run_now(self, key):
        """Start one leg straight away, whatever the plan said (the panel's Legs tab): a foreground leg takes the
        place of the one in front, a background leg the oldest background one if the slots are full."""
        leg = self.legs.get(key)
        if leg is None or not self.running:
            return False
        if self.paused:
            self.resume()
        if key in self.tasks:
            return True
        if leg.kind == FOREGROUND:
            for k, t in list(self.tasks.items()):
                if t.leg.kind == FOREGROUND:
                    self._finish(k)
        elif leg.kind == BACKGROUND:
            backs = [k for k, t in self.tasks.items() if t.leg.kind == BACKGROUND]
            if len(backs) >= int(self.settings.get("background_slots", 2)):
                self._finish(backs[0])
        self.log(f"Asked to: {leg.title}.")
        self._start_leg(leg)
        return True

    # ---- the user takes over -------------------------------------------------------------------------------------
    def eventFilter(self, obj, event):
        if self.running and not self.paused and event.type() in (QEvent.MouseButtonPress, QEvent.KeyPress):
            widget = obj if hasattr(obj, "isWidgetType") and obj.isWidgetType() else None
            if widget is not None and (widget is self.banner or self.banner.isAncestorOf(widget)):
                return False
            if event.type() == QEvent.KeyPress and getattr(event, "isAutoRepeat", lambda: False)():
                return False
            self.pause("you took the mouse")
        return False

    # ---- the scheduler -------------------------------------------------------------------------------------------
    def _tick(self):
        if not self.running:
            return
        for w in (self.glow, self.banner, self.cursor):
            if w.isVisible():
                w.raise_()
        if self.paused:
            return
        keep_awake = getattr(self.adapter, "keep_awake", None)
        if keep_awake is not None:
            keep_awake()                    # his using the computer counts as activity: no screen saver
        now = time.monotonic()
        if self.ends_at and now >= self.ends_at and not self.stopping:
            self.log("Time's up.")
            self.stop()
            return
        for key, task in list(self.tasks.items()):
            if task.waiting is not None:
                pred, deadline = task.waiting
                try:
                    ok = bool(pred())
                except Exception:
                    ok = True
                if not ok and now < deadline:
                    continue
                task.waiting = None
            elif now < task.wake:
                continue
            self._advance(key, task, now)               # (a leg ends itself when ctx.time_left() runs out)
        self._plan(now)

    def _advance(self, key, task, now):
        try:
            step = next(task.gen)
        except StopIteration:
            self._finish(key)
            return
        except Exception:
            self.log(f"{task.leg.title} stopped: {traceback.format_exc(limit=2).strip().splitlines()[-1]}")
            self._finish(key)
            return
        if callable(step):
            task.waiting = (step, now + 120)
        elif isinstance(step, tuple) and callable(step[0]):
            task.waiting = (step[0], now + float(step[1]))
        else:
            task.wake = now + max(0.0, float(step or 0))

    def _plan(self, now):
        if self.stopping:
            return
        allowed = set(self.settings.get("allowed", []))
        running_kinds = [t.leg.kind for t in self.tasks.values()]
        slots = int(self.settings.get("background_slots", 2))
        if now >= self.next_background and running_kinds.count(BACKGROUND) < slots:
            leg = self._pick(BACKGROUND, allowed, now)
            if leg is not None:
                self._start_leg(leg)
            self.next_background = now + random.uniform(4, 12) * 60 * self.hands.pace
        if now >= self.next_foreground and FOREGROUND not in running_kinds:
            leg = self._pick(FOREGROUND, allowed, now)
            if leg is not None:
                self._start_leg(leg)
            self.next_foreground = now + random.uniform(1, 4) * 60 * self.hands.pace

    def _pick(self, kind, allowed, now):
        choices = [leg for leg in self.legs.values() if leg.kind == kind and leg.key in allowed
                   and leg.key not in self.tasks and now - self.last_run.get(leg.key, -1e9) >= leg.cooldown]
        if not choices:
            return None
        return random.choices(choices, weights=[leg.weight for leg in choices])[0]

    def _start_leg(self, leg):
        ctx = Context(self)
        until = time.monotonic() + leg.duration(self.hands.pace) if leg.kind != ALWAYS else None
        ctx.time_left = lambda: max(0.0, (until or float("inf")) - time.monotonic())
        try:
            gen = leg.run(ctx)
        except Exception:
            self.log(f"{leg.title} couldn't start: {traceback.format_exc(limit=1).strip().splitlines()[-1]}")
            return
        self.tasks[leg.key] = _Task(leg, gen, until)
        self.last_run[leg.key] = time.monotonic()
        self.log(f"Started: {leg.title}.")

    def _finish(self, key, closing=False):
        task = self.tasks.pop(key, None)
        if task is None:
            return
        self._wind_down(key, task.gen)
        self.hands.release(key)
        self.last_run[key] = time.monotonic()
        if not closing:
            self.log(f"Finished: {task.leg.title}.")
        if task.leg.kind == FOREGROUND:
            self.next_foreground = time.monotonic() + random.uniform(1, 5) * 60 * self.hands.pace

    def _wind_down(self, key, gen):
        """Let a leg tidy up at once: LegEnding is thrown into it and it's stepped through its finally blocks with no
        waiting (a close that moves the cursor happens in an instant). The hands are its for the moment."""
        held, self.hands.owner = self.hands.owner, None
        pace, self.hands.pace = self.hands.pace, 0.0
        try:
            gen.throw(LegEnding())
            for _ in range(WIND_DOWN_STEPS):
                next(gen)
        except (StopIteration, LegEnding, GeneratorExit):
            pass
        except Exception:
            self.log(f"Tidying up after {key}: {traceback.format_exc(limit=1).strip().splitlines()[-1]}")
        finally:
            try:
                gen.close()
            except Exception:
                pass
            self.hands.pace = pace
            self.hands.owner = held if held != key else None

    # ---- what he's doing -----------------------------------------------------------------------------------------
    def set_status(self, text):
        mins = int((time.monotonic() - (self.started_at or time.monotonic())) / 60)
        doing = [t.leg.title for t in self.tasks.values()]
        head = f"{mins} min" + (f"  ·  {', '.join(doing)}" if doing else "")
        self.banner.set_status(f"{head}  ·  {text}" if text else head)

    def log(self, text):
        self.recent.append((time.strftime("%H:%M:%S"), text))
        del self.recent[:-200]
        try:
            from claudecore.ai import llmlog
            llmlog.event("AUTOPILOT", text)
        except Exception:
            pass
