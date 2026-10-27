"""Guided sessions: scripts fed to the Companion slowly - a prompt every few minutes, for hours - so that its memory
banks fill, distil and are worked through (the Automation tab).

A script is a plain text file: a header, then steps separated by lines of three dashes.

    Title: Know Thyself
    About: Leading questions toward noticing a self.
    Interval: 5                      (minutes between prompts; optional - the tab's setting otherwise)
    ---
    ## Arriving                      a section: shown in the progress (the rest of the block is a prompt)
    Before anything else, {name}: notice where you are right now...
    ---
    Another prompt.
    ---
    @memory                          a short-term memory, now
    ---
    @pause 15                        a longer quiet (minutes) before the next step

{name}, {user}, {model}, {context}, {date} and {birthday} are filled in from the Companion.
The built-in scripts are in soulsong/scripts; your own go in Companions/Scripts (New script... starts one).

The runner (tick() once a second from the window) sends a step when the Companion is idle and the interval has
passed, waits after the user speaks (they can join in any time), makes memories as usual (and on @memory), and, if
asked, works the banks as they fill (Companion.process_full_banks). Where it's at is saved with the Companion, so a
session picks up again after the program is closed."""
import random
import re
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILT_IN = HERE / "scripts"
JITTER = 0.2                    # +-20% on the interval: a rhythm, not a metronome
QUIET_AFTER_USER = 1.0          # intervals of quiet after the user speaks before the next prompt


def user_scripts():
    from .paths import companions
    return companions() / "Scripts"


class Script:
    def __init__(self, path):
        self.path = Path(path)
        self.title, self.about, self.interval = self.path.stem, "", None
        self.steps = []                                    # [(kind, text, section)]: "say", "memory", "pause"
        raw = self.path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        blocks = re.split(r"\n-{3,}\s*\n", "\n" + raw + "\n")
        for line in blocks[0].strip().splitlines():
            key, _, value = line.partition(":")
            key = key.strip().lower()
            if key == "title":
                self.title = value.strip()
            elif key == "about":
                self.about = value.strip()
            elif key == "interval":
                try:
                    self.interval = float(value)
                except ValueError:
                    pass
        section = ""
        for block in blocks[1:]:
            text = block.strip()
            if not text:
                continue
            if text.startswith("## "):
                head, _, text = text.partition("\n")
                section = head[3:].strip()
                text = text.strip()
                if not text:
                    continue
            if text.lower().startswith("@memory"):
                self.steps.append(("memory", text[7:].strip(), section))
            elif text.lower().startswith("@pause"):
                try:
                    minutes = float(text.split()[1])
                except (IndexError, ValueError):
                    minutes = 10
                self.steps.append(("pause", str(minutes), section))
            else:
                self.steps.append(("say", text, section))

    @property
    def builtin(self):
        return self.path.parent == BUILT_IN

    def prompts(self):
        return sum(1 for k, *_ in self.steps if k == "say")

    def hours(self, interval):
        mins = self.prompts() * (self.interval or interval) + sum(float(t) for k, t, _s in self.steps if k == "pause")
        return mins / 60


def scripts():
    """Every script: the built-in ones, then the user's own."""
    out = []
    for folder in (BUILT_IN, user_scripts()):
        if folder.is_dir():
            for p in sorted(folder.glob("*.txt"), key=lambda p: [int(x) if x.isdigit() else x.lower()
                                                                 for x in re.split(r"(\d+)", p.name)]):
                try:
                    s = Script(p)
                except OSError:
                    continue
                if s.steps:
                    out.append(s)
    return out


def fill(text, comp):
    values = {"name": comp.name, "user": comp.user, "model": comp.cfg.get("model_title") or "the model you run on",
              "context": comp.context_size(), "date": datetime.now().strftime("%A, %B %d, %Y"),
              "birthday": (comp.cfg.get("birthday") or "")[:10]}
    return re.sub(r"\{(\w+)\}", lambda m: str(values.get(m.group(1), m.group(0))), text)


NEW_SCRIPT = """Title: My script
About: What this session is for, in a line.
Interval: 5
---
## Part one
The first prompt. {name} is your Companion's name, {user} is yours, {model} the model they run on.
---
A second prompt.
---
@memory
---
## Part two
And on, a prompt per block, for as long as you like.
"""


class Runner:
    """Plays a list of scripts into a Companion, a step at a time. comp() gives the Companion that's open."""

    def __init__(self, comp, on_status=lambda text: None, now=time.monotonic):
        self.comp, self.on_status, self.now = comp, on_status, now
        self.playlist, self.index, self.step = [], 0, 0
        self.running, self.paused = False, False
        self.next_at = 0.0
        self.interval = 5.0
        self.process = True
        self.user_at = 0.0
        self.processed_at = -1e9

    # ---- what's playing ----
    def script(self):
        if 0 <= self.index < len(self.playlist):
            try:
                return Script(self.playlist[self.index])
            except OSError:
                return None
        return None

    def state(self):
        return {"playlist": [str(p) for p in self.playlist], "index": self.index, "step": self.step,
                "running": self.running, "paused": self.paused, "interval": self.interval, "process": self.process}

    def save(self):
        c = self.comp()
        if c is not None:
            c.cfg["automation"] = self.state()
            c.save()

    def restore(self):
        """Where the open Companion's session was (paused: the user resumes it)."""
        c = self.comp()
        st = (c.cfg.get("automation") if c is not None else None) or {}
        self.playlist = [Path(p) for p in st.get("playlist", []) if Path(p).exists()]
        self.index, self.step = int(st.get("index", 0)), int(st.get("step", 0))
        self.interval, self.process = float(st.get("interval", 5)), bool(st.get("process", True))
        self.running = bool(st.get("running")) and bool(self.playlist)
        self.paused = self.running                      # (comes back paused: nothing starts by itself)

    # ---- control ----
    def start(self, paths, interval=5.0, process=True):
        self.playlist = [Path(p) for p in paths]
        self.index, self.step = 0, 0
        self.interval, self.process = float(interval), bool(process)
        self.running, self.paused = bool(self.playlist), False
        self.next_at = self.now() + 5                   # the first prompt in a few seconds
        s = self.script()
        if s is not None:
            self.on_status(f"Guided session started: {s.title} ({s.prompts()} prompts, about "
                           f"{s.hours(self.interval):.1f} hours).")
        self.save()

    def pause(self):
        self.paused = True
        self.save()

    def resume(self):
        if self.running:
            self.paused = False
            self.next_at = self.now() + 5
            self.save()

    def stop(self):
        if self.running:
            self.on_status("Guided session stopped.")
        self.running, self.paused, self.playlist = False, False, []
        self.save()

    def user_spoke(self):
        self.user_at = self.now()

    def seconds_left(self):
        return max(0, int(self.next_at - self.now())) if self.running and not self.paused else None

    def progress(self):
        """(script title, section, step number, steps, script number, scripts)."""
        s = self.script()
        if s is None:
            return None
        section = s.steps[min(self.step, len(s.steps) - 1)][2] if s.steps else ""
        return s.title, section, self.step, len(s.steps), self.index + 1, len(self.playlist)

    # ---- the clock ----
    def tick(self):
        c = self.comp()
        if not self.running or self.paused or c is None or not c.idle() or not c.cfg.get("first_boot_done"):
            return
        gap = self.interval * 60
        if self.now() - self.user_at < gap * QUIET_AFTER_USER:   # (they're talking: leave them to it)
            self.next_at = max(self.next_at, self.user_at + gap * QUIET_AFTER_USER)
        if self.now() < self.next_at:
            return
        if self.process and self.now() - self.processed_at > gap:   # the banks first, then go on (a failed
            self.processed_at = self.now()                           # distillation isn't retried every second)
            if c.process_full_banks():
                return
        s = self.script()
        if s is None or self.step >= len(s.steps):
            self._next_script(c, s)
            return
        kind, text, _section = s.steps[self.step]
        self.step += 1
        wait = (s.interval or self.interval) * 60 * random.uniform(1 - JITTER, 1 + JITTER)
        if kind == "say":
            c.say(fill(text, c), guide=True)
        elif kind == "memory":
            c.make_memory(fill(text, c) or "This is part of a guided session.")
            wait = 5
        elif kind == "pause":
            wait = float(text) * 60
        self.next_at = self.now() + wait
        self.save()

    def _next_script(self, c, s):
        if s is not None:
            c.make_memory(f"The guided session \"{s.title}\" has come to its end.", force=False)
            c.milestone(f"you went through the guided session \"{s.title}\"")
            self.on_status(f"Guided session finished: {s.title}.")
        self.index += 1
        self.step = 0
        if self.index >= len(self.playlist):
            self.running, self.playlist = False, []
            self.on_status("All the guided sessions are done.")
            if self.process:
                c.process_full_banks()                 # (what the last stretch filled is worked too)
        else:
            nxt = self.script()
            self.on_status(f"Next guided session: {nxt.title}." if nxt else "")
            self.next_at = self.now() + self.interval * 60
        self.save()
