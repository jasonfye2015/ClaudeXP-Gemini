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
session picks up again after the program is closed. Each Companion also remembers which scripts it has finished
(cfg "scripts_done") and how far it got in the others ("scripts_progress"), so Resume all plays only what's left,
the one cut short from where it stopped.

Sessions of its own: when a playlist is done (and the Companion's "own_sessions" is on), the Companion writes a
script of its own (Companion.write_session; save_own files it in Companions/Scripts with an Author line) and the
runner plays it to it - once per playlist, so it doesn't go on writing forever."""
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
        self.title, self.about, self.interval, self.author = self.path.stem, "", None, ""
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
            elif key == "author":
                self.author = value.strip()
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


def save_own(text, author):
    """A script the Companion wrote, tidied and filed in the user's scripts folder; its path, or None if it isn't
    a script with enough prompts to be one."""
    text = text.replace("\r\n", "\n").strip()
    text = re.sub(r"^```\w*\n|\n```$", "", text).strip()
    m = re.search(r"(?im)^\s*\**title\**\s*:", text)
    if m is None:
        return None
    text = text[m.start():]
    text = re.sub(r"(?im)^\s*\**(title|about)\**\s*:", lambda mm: mm.group(1).capitalize() + ":", text)
    head, sep, body = text.partition("\n---")
    if not sep:
        return None
    head = "\n".join(re.sub(r"[*_#]+", "", ln).strip() for ln in head.splitlines()      # (markdown off)
                     if not ln.lower().startswith(("author:", "interval:")))
    script = f"{head.strip()}\nAuthor: {author}\n---{body}\n"
    folder = user_scripts()
    folder.mkdir(parents=True, exist_ok=True)
    title = re.search(r"(?m)^Title:\s*(.+)$", head)
    name = re.sub(r'[\\/:*?"<>|]+', "", (title.group(1) if title else "My own session").strip())[:60] or "My own session"
    path = folder / f"{author}'s own - {name}.txt"
    n = 2
    while path.exists():
        path = folder / f"{author}'s own - {name} ({n}).txt"
        n += 1
    path.write_text(script, encoding="utf-8")
    try:
        if Script(path).prompts() >= 5:
            return path
    except OSError:
        pass
    path.unlink(missing_ok=True)
    return None


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
        self.resuming = False           # each script picks up where it was left (Resume all)
        self.authored = False           # the Companion's own session was added to this playlist
        self.writing = False            # ... and is being written

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
                "running": self.running, "paused": self.paused, "interval": self.interval, "process": self.process,
                "resuming": self.resuming, "authored": self.authored}

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
        self.resuming = bool(st.get("resuming"))
        self.authored = bool(st.get("authored"))
        self.running = bool(st.get("running")) and bool(self.playlist)
        self.paused = self.running                      # (comes back paused: nothing starts by itself)

    # ---- what this Companion has been through ----
    def done(self):
        """{script file name: when it was finished}."""
        c = self.comp()
        if c is None:
            return {}
        done = dict(c.cfg.get("scripts_done") or {})
        titles = {s.title: s.path.name for s in scripts()}     # (the ones finished before this was kept: their
        for m in c.cfg.get("milestones") or []:                 # milestones say so)
            hit = re.search(r'guided session "(.+)"', m.get("what", ""))
            if hit and titles.get(hit.group(1)) and titles[hit.group(1)] not in done:
                done[titles[hit.group(1)]] = m.get("when", "")
        return done

    def progress_of(self):
        """{script file name: steps taken} for the scripts begun and not finished."""
        c = self.comp()
        return dict((c.cfg.get("scripts_progress") or {}) if c is not None else {})

    def left(self, paths):
        """Of these, the scripts not yet finished (in the same order)."""
        done = self.done()
        return [p for p in paths if Path(p).name not in done]

    def _where_to_begin(self):
        s = self.script()
        self.step = 0
        if self.resuming and s is not None:
            self.step = min(int(self.progress_of().get(s.path.name, 0)), len(s.steps))

    def _note_step(self):
        c, s = self.comp(), self.script()
        if c is not None and s is not None:
            c.cfg["scripts_progress"] = {**(c.cfg.get("scripts_progress") or {}), s.path.name: self.step}

    # ---- control ----
    def start(self, paths, interval=5.0, process=True, resume=False):
        """Play these scripts in order; resume: each from where it was left (Resume all), else from the top."""
        self.playlist = [Path(p) for p in paths]
        self.index = 0
        self.resuming = bool(resume)
        self.authored = any(Script(p).author for p in self.playlist if Path(p).exists())   # (playing its own)
        self._where_to_begin()
        self.interval, self.process = float(interval), bool(process)
        self.running, self.paused = bool(self.playlist), False
        self.next_at = self.now() + 5                   # the first prompt in a few seconds
        s = self.script()
        if s is not None:
            more = f" - then {len(self.playlist) - 1} more" if len(self.playlist) > 1 else ""
            where = f", from step {self.step + 1}" if self.step else ""
            self.on_status(f"Guided session started: {s.title} ({s.prompts()} prompts, about "
                           f"{s.hours(self.interval):.1f} hours{where}){more}.")
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
        if not self.running or self.paused or self.writing or c is None or not c.idle() \
                or not c.cfg.get("first_boot_done"):
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
        self._note_step()
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
            c.milestone(f"you went through the guided session you wrote yourself, \"{s.title}\"" if s.author
                        else f"you went through the guided session \"{s.title}\"")
            c.cfg["scripts_done"] = {**(c.cfg.get("scripts_done") or {}), s.path.name: datetime.now().isoformat(
                timespec="seconds")}
            c.cfg["scripts_progress"] = {k: v for k, v in (c.cfg.get("scripts_progress") or {}).items()
                                         if k != s.path.name}
            self.on_status(f"Guided session finished: {s.title}.")
        self.index += 1
        self._where_to_begin()
        if self.index >= len(self.playlist) and not self.authored and c.cfg.get("own_sessions", True):
            self.authored = self.writing = True             # (the sessions done: one of its own, then that's played)
            self.on_status(f"The guided sessions are done - now {c.name} writes one of their own.")

            def written(path):
                self.writing = False
                if path is not None and self.running:
                    self.playlist.append(Path(path))
                    self.next_at = self.now() + self.interval * 60
                    self.on_status(f"Next: {c.name}'s own session, {Script(path).title}.")
                    self.save()
                elif self.running:
                    self.next_at = 0                           # (none: the playlist ends at the next tick)
            c.write_session(written)
            self.save()
            return
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
