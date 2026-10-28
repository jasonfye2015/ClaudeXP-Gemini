"""Interlink: two Companions together (the Interlink tab).

Three ways:
- Guided together: a script leads them both - a prompt for the two of them, then they talk it over for a few turns,
  then the next; @memory makes each of them a memory.
- Open conversation: an opening (a topic, or the user's own) and then they talk between themselves for as many
  messages as the user chose, a memory each every so often and at the end.
- Group chat: the user and both Companions; a script can lead it (a prompt, then a few rounds of the user's
  messages each), or it's just the three of them.

How it works: each Companion keeps its own side of the conversation (its own history, its own memories). What one
says goes into the other's inbox; on its turn a Companion hears everything in its inbox and answers the last of it
(Companion.hear). The two take turns on the model - on one model they share it (Lane), a request at a time.

A script is a plain text file like the Automation scripts: a header, then steps separated by lines of three dashes.

    Title: First Meeting
    Mode: guided                     guided | open | group
    About: Two Companions meet for the first time.
    Turns: 6                         messages in each step's exchange (guided; default 6)
    Rounds: 3                        the user's messages before the next step (group; default 3)
    Messages: 20                     how long the conversation runs (open; the tab's setting otherwise)
    ---
    ## Hello                         a section: shown in the progress
    {A}, {B}: this is the first time you meet...     a prompt (the guide's words, to both)
    ---
    @first B                         who answers first: A, B or alternate (the default)
    @turns 4                         this step's exchange
    Another prompt.
    ---
    @memory                          a memory each, now

An open conversation's script is a list of openings, one per step: one is picked (or the next, in order).
{A} and {B} are the Companions' names, {user} the user's."""
import random
import re
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILT_IN = HERE / "scripts" / "interlink"
MODES = {"guided": "Guided together", "open": "Open conversation", "group": "Group chat"}
DEFAULT_TURNS = 6
DEFAULT_ROUNDS = 3
OPEN_MEMORY_EVERY = 12           # an open conversation: a memory each every this many messages
GAP = 2.5                        # seconds between messages, to read them

ARRIVE = {
    "guided": "You're about to spend some time with {other}, another Companion who lives in Soul and Song too, on a "
              "guided session for the two of you. Their messages are marked with their name; the guide's prompts "
              "come to you both. {user} may be watching.",
    "open": "You're about to talk with {other}, another Companion who lives in Soul and Song too - just the two of "
            "you, for a while, about whatever comes up. Their messages are marked with their name. {user} may be "
            "watching.",
    "group": "{user} has brought {other} - another Companion who lives in Soul and Song too - into your "
             "conversation: it's the three of you now. {other}'s messages are marked with their name.",
}
OPENING = ("{first}, {second}: this is a conversation just for the two of you. Start it off, {first}: {topic} "
           "Speak to each other directly, ask each other things, and take it wherever it goes.")
AFTER = ("This is the end of your {kind} with {other}{also}. Make a Short-Term Memory of it, and of who {other} "
         "is to you.")


# ---- one model, two Companions ---------------------------------------------------------------------------------------
class Lane:
    """One brain (EngineBrain) shared by Companions that run on the same model: their requests wait their turn.
    on_active(handle or None) tells the window whose request is running (for the glow)."""

    def __init__(self, brain, on_active=lambda h: None):
        self.brain = brain
        self.on_active = on_active
        self.waiting = []
        self.current = None

    def handle(self, colour="", name=lambda: ""):
        return Handle(self, colour, name)

    def _pump(self):
        if self.current is not None or not self.waiting:
            if self.current is None:
                self.on_active(None)
            return
        handle, args = self.waiting.pop(0)
        self.current = handle
        messages, done, chunk, max_tokens, temperature = args
        self.on_active(handle)
        self.brain.on_thinking = handle.on_thinking

        def finished(text, err):
            self.current = None
            done(text, err)
            self._pump()
        self.brain.ask(messages, finished, chunk, max_tokens, temperature)

    def stop(self, handle=None):
        """Stop a handle's request (and drop the ones it has waiting); no handle: everything."""
        self.waiting = [w for w in self.waiting if handle is not None and w[0] is not handle]
        if self.current is not None and (handle is None or self.current is handle):
            self.brain.stop()


class Handle:
    """What a Companion uses as its brain: ask() queues on the Lane."""

    def __init__(self, lane, colour, name):
        self.lane, self.colour, self.name = lane, colour, name
        self.on_thinking = lambda text: None

    def ask(self, messages, done, chunk=None, max_tokens=700, temperature=0.8):
        self.lane.waiting.append((self, (messages, done, chunk, max_tokens, temperature)))
        self.lane._pump()

    def stop(self):
        self.lane.stop(self)

    @property
    def engine(self):
        return self.lane.brain.engine


# ---- scripts ---------------------------------------------------------------------------------------------------------
def user_scripts():
    from .paths import companions
    return companions() / "Scripts" / "Interlink"


class InterScript:
    def __init__(self, path):
        self.path = Path(path)
        self.title, self.about, self.mode = self.path.stem, "", "guided"
        self.turns, self.rounds, self.messages = DEFAULT_TURNS, DEFAULT_ROUNDS, None
        self.steps = []          # [(kind, text, section, options)]: "say", "memory", "pause"
        raw = self.path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        blocks = re.split(r"\n-{3,}\s*\n", "\n" + raw + "\n")
        for line in blocks[0].strip().splitlines():
            key, _, value = line.partition(":")
            key, value = key.strip().lower(), value.strip()
            if key == "title":
                self.title = value
            elif key == "about":
                self.about = value
            elif key == "mode" and value.lower() in MODES:
                self.mode = value.lower()
            elif key in ("turns", "rounds", "messages"):
                try:
                    setattr(self, key, max(1, int(value)))
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
            opts = {}
            body = []
            for line in text.splitlines():
                if line.startswith("## "):                 # (a section heading anywhere in the step)
                    section = line[3:].strip()
                    continue
                m = re.match(r"\s*@(first|turns|rounds|pause|memory)\b\s*(.*)$", line, re.I)
                if m:
                    opts[m.group(1).lower()] = m.group(2).strip()
                else:
                    body.append(line)
            text = "\n".join(body).strip()
            if "memory" in opts and not text:
                self.steps.append(("memory", opts["memory"], section, opts))
            elif "pause" in opts and not text:
                self.steps.append(("pause", opts["pause"] or "30", section, opts))
            elif text:
                self.steps.append(("say", text, section, opts))

    @property
    def builtin(self):
        return self.path.parent == BUILT_IN


def scripts(mode=None):
    out = []
    for folder in (BUILT_IN, user_scripts()):
        if folder.is_dir():
            for p in sorted(folder.glob("*.txt"), key=lambda p: p.name.lower()):
                try:
                    s = InterScript(p)
                except OSError:
                    continue
                if s.steps and (mode is None or s.mode == mode):
                    out.append(s)
    return out


def fill(text, a, b, user):
    return text.replace("{A}", a).replace("{B}", b).replace("{user}", user)


# ---- a session -------------------------------------------------------------------------------------------------------
class Session:
    """Two Companions (a, b) together. tick() once a second from the window moves it along; user_says(text) is the
    user joining in. on_guide(text) shows a guide prompt, on_status(text) a note."""

    def __init__(self, a, b, mode, script=None, messages=20, topic="", first="A", gap=GAP,
                 on_guide=lambda text: None, on_status=lambda text: None, now=time.monotonic):
        self.a, self.b, self.mode, self.script = a, b, mode, script
        self.total = int(messages)
        self.topic = topic
        self.first = first
        self.gap = gap
        self.on_guide, self.on_status, self.now = on_guide, on_status, now
        self.inbox = {"A": [], "B": []}            # [(text, speaker or None, guide)]
        self.turns = []                            # who speaks next: "A" / "B"
        self.waiting = None                        # who is answering now
        self.step = -1                             # the script step being played
        self.spoken = 0                            # Companion messages so far
        self.user_messages = 0                     # the user's, in this group step
        self.rounds = 0
        self.next_at = 0.0
        self.paused = False
        self.running = True
        self.finishing = False
        self.alt = 0                               # (for "alternate": who went first last time)
        self.last_speaker = None
        self.since_memory = 0
        for key, comp, other in (("A", a, b), ("B", b, a)):
            comp.notice(ARRIVE[mode].format(other=other.name, user=comp.user))
        if mode == "open":
            self._open()
        elif mode == "group" and script is None:
            self.on_status(f"Group chat with {a.name} and {b.name} - say something.")
        else:
            self._next_step()

    def comp(self, key):
        return self.a if key == "A" else self.b

    def other(self, key):
        return "B" if key == "A" else "A"

    # ---- what's going on, for the window ----
    def progress(self):
        """(title, section, done, of) for the tab and the top bar."""
        if self.mode == "open":
            return (f"Open conversation: {self.a.name} and {self.b.name}", self.topic[:60], self.spoken, self.total)
        title = self.script.title if self.script else f"Group chat: {self.a.name}, {self.b.name} and you"
        if self.script is None:
            return (title, "", 0, 0)
        steps = [s for s in self.script.steps if s[0] == "say"]
        done = sum(1 for k, *_ in self.script.steps[:max(0, self.step)] if k == "say")
        section = self.script.steps[self.step][2] if 0 <= self.step < len(self.script.steps) else ""
        return (title, section, done, len(steps))

    def speaking(self):
        return self.waiting

    # ---- moving along ----
    def tick(self):
        if not self.running or self.paused or self.waiting is not None:
            return
        if not (self.a.idle() and self.b.idle()) or self.now() < self.next_at:
            return
        while self.turns:
            key = self.turns.pop(0)
            if self.inbox[key]:
                self._turn(key)
                return
        if self.finishing:
            self._end()
            return
        if self.mode == "open":
            if self.spoken >= self.total:
                self._wrap_up()
            else:
                self._keep_talking()
            return
        if self.mode == "group" and (self.script is None or self.rounds_left()):
            return                                     # (the user's turn)
        self._next_step()

    def rounds_left(self):
        if self.script is None or not (0 <= self.step < len(self.script.steps)):
            return False
        opts = self.script.steps[self.step][3]
        want = _int(opts.get("rounds"), self.script.rounds)
        return self.user_messages < want

    def _turn(self, key):
        comp = self.comp(key)
        items, self.inbox[key] = self.inbox[key], []
        self.waiting = key
        for i, (text, speaker, guide) in enumerate(items):
            last = i == len(items) - 1
            comp.hear(text, speaker=speaker, guide=guide, respond=last,
                      then=(lambda reply, k=key: self._answered(k, reply)) if last else None)

    def _answered(self, key, reply):
        self.waiting = None
        self.next_at = self.now() + self.gap
        if reply is None:
            self.on_status(f"{self.comp(key).name} didn't answer - carrying on.")
            return
        self.spoken += 1
        self.since_memory += 1
        self.last_speaker = key
        self.inbox[self.other(key)].append((reply, self.comp(key).name, False))
        if self.mode == "open" and self.since_memory >= OPEN_MEMORY_EVERY:
            self.since_memory = 0
            self._memories("This is part of your conversation with {other}, so far.")

    def _order(self, opts):
        first = (opts.get("first") or self.first or "alternate").upper()
        if first not in ("A", "B"):
            first = "AB"[self.alt % 2]
            self.alt += 1
        return [first, self.other(first)]

    def _next_step(self):
        if self.script is None:
            return
        self.step += 1
        self.user_messages = 0
        if self.step >= len(self.script.steps):
            self._wrap_up()
            return
        kind, text, section, opts = self.script.steps[self.step]
        if kind == "memory":
            self._memories(text or "This is a moment of your time with {other}.")
            self.next_at = self.now() + self.gap
            return
        if kind == "pause":
            self.next_at = self.now() + _int(text, 30)
            self.on_status(f"A pause of {_int(text, 30)} seconds.")
            return
        prompt = fill(text, self.a.name, self.b.name, self.a.user)
        self.on_guide(prompt)
        for key in ("A", "B"):
            self.inbox[key].append((prompt, None, True))
        order = self._order(opts)
        if self.mode == "group":
            self.turns = order
            self.on_status("Your turn, whenever you like - they'll both answer you." if self.rounds_left() else "")
            return
        n = max(2, _int(opts.get("turns"), self.script.turns))
        self.turns = [order[i % 2] for i in range(n)]

    def _open(self):
        topic = self.topic
        if not topic and self.script is not None:
            openings = [t for k, t, *_ in self.script.steps if k == "say"]
            topic = random.choice(openings) if openings else ""
            self.topic = topic
        first = self._order({"first": self.first})[0]
        a, b = self.comp(first).name, self.comp(self.other(first)).name
        topic = fill(topic or "talk about whatever you're curious about in each other.", self.a.name, self.b.name,
                     self.a.user)
        opening = OPENING.format(first=a, second=b, topic=topic)
        self.on_guide(opening)
        for key in ("A", "B"):
            self.inbox[key].append((opening, None, True))
        self.turns = [first]

    def _keep_talking(self):
        nxt = self.other(self.last_speaker) if self.last_speaker else "A"
        self.turns = [nxt]

    def user_says(self, text):
        """The user joins in: both hear it; whoever's turn it is next answers it, then the other (in a group chat,
        the one they named answers first)."""
        for key in ("A", "B"):
            self.inbox[key].append((text, None, False))
        if self.mode == "group":
            self.user_messages += 1
            named = [k for k in ("A", "B") if re.search(rf"\b{re.escape(self.comp(k).name)}\b", text, re.I)]
            first = named[0] if len(named) == 1 else ("B" if self.last_speaker == "A" else "A")
            self.turns = [first, self.other(first)]
            return
        nxt = self.other(self.last_speaker) if self.last_speaker else "A"
        self.turns = [nxt, self.other(nxt)] + self.turns

    def _memories(self, note):
        for key in ("A", "B"):
            comp = self.comp(key)
            comp.make_memory(note.format(other=self.comp(self.other(key)).name))

    def _wrap_up(self):
        """Last words heard, then a memory each of the time together."""
        self.finishing = True
        kind = {"guided": "guided session", "open": "conversation", "group": "time together"}[self.mode]
        for key in ("A", "B"):
            comp, other = self.comp(key), self.comp(self.other(key))
            for text, speaker, guide in self.inbox[key]:
                comp.hear(text, speaker=speaker, guide=guide, respond=False)
            self.inbox[key] = []
            also = f" and {comp.user}" if self.mode == "group" else ""
            comp.make_memory(AFTER.format(kind=kind, other=other.name, also=also))
        self.turns = []
        self.on_status("Making their memories of it...")

    def _end(self):
        self.running = False
        self.on_status("Interlink finished: each of them has a memory of it.")

    def stop(self):
        """Stop now - what was said is kept, and each makes a memory of it (if anything was said)."""
        if not self.running:
            return
        if self.spoken:
            self._wrap_up()
        self.running = False


def _int(value, default):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default
