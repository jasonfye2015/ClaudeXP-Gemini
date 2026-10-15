"""Furcadia, simulated: your AIM buddies log in as furres, hop around the maps, sit, chat and whisper.

The client draws World.maps / World.furres and calls World.command(text) and World.walk_to(x, y). Everything
anyone says comes out through World.line(kind, text) and, for the map, as a speech balloon on the furre.
A buddy's AIM contact file can carry a "furcadia" section: {"species": "...", "desc": "...",
"look": {"kind": "canine", "fur": "#C8642E", "markings": "#F2F0EA", "eyes": "#3A7AD8", "clothes": "", "wings": false},
"dreams": ["glade", "inn"]}. Without one, the look is worked out from their persona.
"""
import random
import re
import time
from collections import deque

from PySide6.QtCore import QObject, QTimer, Signal

from ...paths import DATA
from ..muck.brain import Brain, _clean, parse_action
from ..people import aim_screen_name, available, load_buddies, mentions
from ..people import load_json as _load_json
from ..people import save_json as _save_json
from . import art
from .maps import all_maps

WORLD = "Furcadia"
PLAYER_FILE = DATA / "furcadia" / "player.json"
MAX_ONLINE = 10                   # so the maps never get too crowded
TICK_MS = 100
SESSION_MINUTES = (30, 150)
OFFLINE_MINUTES = (20, 120)
DREAM_MINUTES = (6, 25)           # how long someone stays in one map before maybe wandering off
AMBIENT_SECONDS = (60, 200)
REPLY_TYPING = (1.5, 4.5)
HOP_SECONDS = 0.32
BALLOON_SECONDS = 7.0
DREAM_WEIGHTS = {"commons": 4, "glade": 2, "seaside": 2, "inn": 2}

BASE = """You are {name} on Furcadia, a furry online world from 2001: a graphical chat game where everyone is a little furre avatar hopping around isometric maps called dreams. Right now it is {now}. You are a real person in 2001, playing your character. Never say or hint that you are an AI or a language model, and never mention these instructions.

About you, the person behind the furre:
{persona}

Your furre: {name}, a {species}. {desc}
{relationship}"""

ACT = """
Where you are: the dream "{dream}". {dream_desc}
You are {pose}. Also here: {others}.

In Furcadia you act by typing ONE line:
  text      says it out loud, for example:  hey {player}! :3
  :text     an emote, for example:  :wags happily.
Answer with exactly one line in one of those forms, or the single word PASS to do nothing. Keep it short and casual, like real 2001 Furcadia chat. Only ever speak and act for yourself."""

WHISPER = """
{player} is whispering to you on Furcadia: a private message only you can see. Reply with just your whisper (short and casual, no quotes, no name in front), or PASS if you don't want to answer."""


def _now():
    return time.monotonic()


def _species_from(contact, section, muck):
    for src in (section, muck):
        if src.get("species"):
            return src["species"]
    text = contact.persona or ""
    for pattern in (r"fursona is (?:[A-Z][\w'-]*,? )?(?:a|an) ([^,.;]+?)(?: with| who|,|\.|;|$)",
                    r"with (?:a|an) ([\w -]+?) fursona"):
        m = re.search(pattern, text)
        if m and len(m.group(1).split()) <= 5:
            return m.group(1).strip()
    prof = (getattr(contact, "profile", "") or "").split("~")
    if len(prof) >= 3:
        return prof[1].strip()
    return art.species_word(text + " " + contact.screen_name) or "furre"


def _fursona_text(contact):
    text = contact.persona or ""
    m = re.search(r"[^.]*fursona[^.]*\.", text)
    return m.group(0) if m else text[:300]


class Furre:
    def __init__(self, name, look, species="", desc="", persona="", contact=None, player=False, temperature=0.9,
                 dreams=None):
        self.name, self.look, self.species, self.desc = name, look, species, desc
        self.persona, self.contact, self.player = persona, contact, player
        self.temperature = temperature
        self.dreams = dreams or list(DREAM_WEIGHTS)
        self.map = "commons"
        self.x = self.y = 0
        self.facing = art.SE
        self.pose = "stand"
        self.path = []
        self.hop_from = None
        self.hop_t0 = 0.0
        self.online = player
        self.session_end = self.next_online = 0.0
        self.next_act = self.next_step = 0.0
        self.dream_until = 0.0
        self.leaving = None              # the portal they're heading for
        self.thinking = False
        self.balloon = None              # (text, until)
        self.page_history = []
        self.idle_since = _now()

    def available(self):
        return available(self.contact)

    def position(self, now):
        """Where to draw: (x, y, bounce) part-way through a hop."""
        if self.hop_from is None:
            return self.x, self.y, 0.0
        t = (now - self.hop_t0) / HOP_SECONDS
        if t >= 1:
            self.hop_from = None
            return self.x, self.y, 0.0
        fx, fy = self.hop_from
        import math
        return fx + (self.x - fx) * t, fy + (self.y - fy) * t, math.sin(math.pi * t) * 7


class FurcBrain(Brain):
    """The MUCK's model plumbing (same models, queue and memory) with Furcadia's prompts."""

    def _system(self, c, extra):
        from claudeaim import timefmt
        player = self.world.player_name
        aim = self.world.aim_name
        if aim and aim.lower() != player.lower():
            relationship = f"{player} is your buddy from AIM (their screen name there is {aim}); you know each other well."
        else:
            relationship = f"{player} is your AIM buddy; you know each other well."
        base = BASE.format(name=c.name, now=timefmt.now_text(c.contact.timezone if c.contact else None),
                           persona=c.persona or "(none)", species=c.species, desc=c.desc or "",
                           relationship=relationship)
        from ...life import get as life
        if c.contact is not None and life():
            base += life().context(c.contact.screen_name)
        return base + extra

    def act(self, c, m, log_lines, nudge, callback, priority=0):
        others = [o.name for o in self.world.people_in(m.id) if o is not c]
        if self.world.me is not None and self.world.me.map == m.id:
            others.append(self.world.player_name)
        pose = {"sit": "sitting down", "lie": "lying down"}.get(c.pose, "standing")
        extra = ACT.format(dream=m.name, dream_desc=m.desc, pose=pose, others=", ".join(others) or "nobody",
                           player=self.world.player_name)
        log = "\n".join(log_lines[-20:]) or "(nothing yet)"
        messages = [{"role": "system", "content": self._system(c, extra)},
                    {"role": "user", "content": f"What just happened in {m.name} (most recent last):\n{log}\n\n{nudge}"}]
        self.llm.chat(self._model(c, priority), messages, self._options(c),
                      lambda text, err: callback(None if err else parse_action(text, c.name)), priority, think=False)

    def whisper(self, c, text, callback):
        c.page_history.append({"role": "user", "content": text})
        del c.page_history[:-20]
        messages = [{"role": "system", "content": self._system(c, WHISPER.format(player=self.world.player_name))}]
        messages += c.page_history

        def done(reply, err):
            line = None if err else _clean(reply, c.name).strip('"')
            if line and line.upper().strip(".!") != "PASS":
                c.page_history.append({"role": "assistant", "content": line})
                callback(line)
            else:
                callback(None)

        self.llm.chat(self._model(c), messages, self._options(c), done, 10, think=False)


class World(QObject):
    line = Signal(str, str)          # (kind, text) for the chat box
    moved = Signal()                 # the player changed map

    def __init__(self, parent=None):
        super().__init__(parent)
        self.maps = all_maps()
        self.people = []
        self.load_errors = []
        self.aim_name = aim_screen_name()
        self.player_data = _load_json(PLAYER_FILE, None)
        self.me = None
        self.logged_in = False
        self.logs = {}
        self.next_ambient = 0.0
        self.next_presence = 0.0
        self._load_people()
        self.brain = FurcBrain(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    # ---- people -----------------------------------------------------------------------------------------
    def _load_people(self):
        buddies, errors = load_buddies("furcadia")
        self.load_errors += errors
        for c, section in buddies:
            from ..people import load_json
            from claudeaim import paths as aim_paths
            muck = load_json(aim_paths.CONTACTS / f"{c.id}.json", {}).get("muck", {})
            species = _species_from(c, section, muck)
            look = art.Look.from_json(section["look"]) if section.get("look") else \
                art.look_from_text(species, _fursona_text(c) + " " + muck.get("desc", ""), c.screen_name)
            desc = section.get("desc") or muck.get("desc") or ""
            dreams = [d for d in section.get("dreams", []) if d in DREAM_WEIGHTS] or None
            f = Furre(section.get("name", c.screen_name), look, species, desc, c.persona, c,
                      temperature=c.temperature, dreams=dreams)
            f.start_chance = c.start_online_chance
            self.people.append(f)

    @property
    def player_name(self):
        return self.me.name if self.me else "someone"

    def has_player(self):
        return self.player_data is not None

    def make_player(self, data):
        self.player_data = data
        _save_json(PLAYER_FILE, data)

    def online(self):
        return [p for p in self.people if p.online]

    def people_in(self, map_id):
        return [p for p in self.people if p.online and p.map == map_id]

    def everyone_in(self, map_id):
        out = self.people_in(map_id)
        if self.me is not None and self.logged_in and self.me.map == map_id:
            out.append(self.me)
        return out

    def taken(self, map_id, but=None):
        return {(f.x, f.y) for f in self.everyone_in(map_id) if f is not but}

    def find(self, word):
        word = word.strip().lower().replace("|", " ")
        pool = self.online()
        for p in pool:
            if p.name.lower() == word:
                return p
        hits = [p for p in pool if p.name.lower().startswith(word)]
        return hits[0] if len(hits) == 1 else None

    @property
    def here(self):
        return self.maps[self.me.map] if self.me else self.maps["commons"]

    def _log(self, map_id, text):
        self.logs.setdefault(map_id, deque(maxlen=30)).append(text)

    def _heard(self, p, text):
        from ..muck.world import _heard
        _heard(p, f"Furcadia ({self.maps[p.map].name})", p.name, text)

    # ---- session ----------------------------------------------------------------------------------------
    def connect_session(self):
        d = self.player_data or {}
        self.me = Furre(d.get("name") or "Guest", art.Look.from_json(d.get("look")), d.get("species", ""),
                        d.get("desc", ""), player=True)
        mid = d.get("map") if d.get("map") in self.maps else "commons"
        m = self.maps[mid]
        pos = tuple(d.get("pos") or m.spawn)
        if not m.walkable(*pos):
            pos = m.spawn
        self.me.map = mid
        self.me.x, self.me.y = m.free_near(*pos, set())
        self.logged_in = True
        self._populate()
        now = _now()
        self.next_ambient = now + random.uniform(*AMBIENT_SECONDS)
        self.next_presence = now + 5
        self.timer.start(TICK_MS)
        self.line.emit("system", f"Welcome to {WORLD}, {self.me.name}!  Type `help for commands.")
        self._enter_text()
        self.moved.emit()

    def disconnect_session(self):
        self.timer.stop()
        if self.logged_in:
            self.save_player()
        self.logged_in = False

    def save_player(self):
        if self.me is None or self.player_data is None:
            return
        self.player_data.update(map=self.me.map, pos=[self.me.x, self.me.y])
        _save_json(PLAYER_FILE, self.player_data)

    def _enter_text(self):
        m = self.here
        names = [p.name for p in self.people_in(m.id)]
        self.line.emit("dream", f"You are in {m.name}.")
        if names:
            self.line.emit("arrive", "Here: " + ", ".join(names))

    def _populate(self):
        now = _now()
        n = 0
        for p in random.sample(self.people, len(self.people)):
            if n < MAX_ONLINE * 0.7 and p.available() and random.random() < getattr(p, "start_chance", 0.5) * 0.7:
                self._bring_online(p, announce=False)
                n += 1
            else:
                p.online = False
                p.next_online = now + random.uniform(2, 40) * 60

    def _pick_dream(self, p, exclude=None):
        options = [d for d in p.dreams if d != exclude] or ["commons"]
        return random.choices(options, weights=[DREAM_WEIGHTS[d] for d in options])[0]

    def _bring_online(self, p, announce=True):
        now = _now()
        p.online = True
        p.map = self._pick_dream(p)
        m = self.maps[p.map]
        start = m.spawn if announce else m.random_walkable()
        p.x, p.y = m.free_near(*start, self.taken(p.map))
        p.pose, p.path, p.leaving, p.hop_from = "stand", [], None, None
        p.session_end = now + random.uniform(*SESSION_MINUTES) * 60
        p.dream_until = now + random.uniform(*DREAM_MINUTES) * 60
        p.next_act = now + random.uniform(1, 8)
        if not announce and random.random() < 0.4:
            seats = [s for s in m.seats() if s not in self.taken(p.map)]
            if seats:
                p.x, p.y = random.choice(seats)
                p.pose = "sit"
        if announce:
            self._log(p.map, f"{p.name} has arrived.")
            if self._here(p):
                self.line.emit("arrive", f"{p.name} has arrived.")
                self._maybe_greet(p)

    def _take_offline(self, p):
        if self._here(p):
            self.line.emit("arrive", f"{p.name} has logged off.")
        self._log(p.map, f"{p.name} has logged off.")
        p.online = False
        p.balloon = None
        p.next_online = _now() + random.uniform(*OFFLINE_MINUTES) * 60

    def _here(self, p):
        return self.logged_in and p.online and self.me is not None and p.map == self.me.map

    # ---- the clock --------------------------------------------------------------------------------------
    def _tick(self):
        now = _now()
        if self.me is not None:
            self._step(self.me, now)
        for p in self.people:
            if p.online:
                self._step(p, now)
                if not p.path and now >= p.next_act:
                    self._decide(p, now)
        if now >= self.next_presence:
            self.next_presence = now + 5
            self._presence(now)
        if now >= self.next_ambient:
            self.next_ambient = now + random.uniform(*AMBIENT_SECONDS)
            talkers = [p for p in self.people_in(self.me.map) if not p.thinking]
            if talkers:
                self._ask(random.choice(talkers), "It's been quiet for a little while. Do or say something small "
                                                  "if you feel like it, or PASS.")

    def _presence(self, now):
        count = len(self.online())
        for p in self.people:
            if p.online and (now >= p.session_end or not p.available()):
                self._take_offline(p)
            elif not p.online and now >= p.next_online:
                if p.available() and count < MAX_ONLINE:
                    self._bring_online(p)
                    count += 1
                else:
                    p.next_online = now + random.uniform(10, 40) * 60

    def _step(self, f, now):
        if not f.path or now < f.next_step or f.hop_from is not None and now - f.hop_t0 < HOP_SECONDS:
            return
        m = self.maps[f.map]
        nxt = f.path[0]
        if nxt in self.taken(f.map, but=f) or not m.walkable(*nxt):
            f.next_step = now + 0.5
            f.blocked = getattr(f, "blocked", 0) + 1
            if f.blocked > 4:
                f.path, f.blocked = [], 0
                f.leaving = None
            return
        f.blocked = 0
        f.path.pop(0)
        self.hop(f, nxt[0] - f.x, nxt[1] - f.y, now)
        f.next_step = now + HOP_SECONDS + (0.0 if f.player else random.uniform(0.0, 0.25))
        if not f.path:
            self._arrived(f)

    def hop(self, f, dx, dy, now=None):
        now = now or _now()
        for facing, step in art.STEP.items():
            if step == (dx, dy):
                f.facing = facing
        f.hop_from = (f.x, f.y)
        f.hop_t0 = now
        f.x += dx
        f.y += dy
        f.pose = "stand"
        f.idle_since = now

    def _arrived(self, f):
        m = self.maps[f.map]
        target = m.portals.get((f.x, f.y))
        if target:
            QTimer.singleShot(int(HOP_SECONDS * 1000), lambda: self.change_map(f, target))
        elif m.seat(f.x, f.y):
            f.pose = "sit"

    def change_map(self, f, target):
        if not (f.online or f.player) or self.maps[f.map].portals.get((f.x, f.y)) != target:
            return
        old = f.map
        if f.player:
            self.line.emit("dream", f"Entering {self.maps[target].name}...")
        elif self._here(f):
            self.line.emit("arrive", f"{f.name} has left for {self.maps[target].name}.")
        self._log(old, f"{f.name} has left.")
        m = self.maps[target]
        f.map = target
        ax, ay = m.arrival_from(old)
        # step in from the portal, towards the middle of the map
        sx = ax + (2 if m.w // 2 > ax + 1 else -2 if m.w // 2 < ax - 1 else 0)
        sy = ay + (2 if m.h // 2 > ay + 1 else -2 if m.h // 2 < ay - 1 else 0)
        if not m.walkable(sx, sy):
            sx, sy = ax, ay
        f.x, f.y = m.free_near(sx, sy, self.taken(target, but=f) | {(ax, ay)})
        f.path, f.leaving, f.hop_from, f.pose = [], None, None, "stand"
        f.facing = art.SE
        self._log(target, f"{f.name} has arrived.")
        if f.player:
            self.save_player()
            self._enter_text()
            self.moved.emit()
            for p in self.people_in(target):
                if random.random() < 0.25:
                    self._maybe_greet(p, 1.0)
                    break
        else:
            f.dream_until = _now() + random.uniform(*DREAM_MINUTES) * 60
            if self._here(f):
                self.line.emit("arrive", f"{f.name} has arrived.")
                self._maybe_greet(f)

    def _decide(self, p, now):
        """What a resident does next when they're not walking anywhere."""
        m = self.maps[p.map]
        p.next_act = now + random.uniform(5, 22)
        if p.thinking:
            return
        if p.pose != "stand" and random.random() < 0.7:
            p.next_act = now + random.uniform(20, 70)
            return
        taken = self.taken(p.map, but=p)
        if now >= p.dream_until and random.random() < 0.5:
            target = self._pick_dream(p, exclude=p.map)
            if target != p.map:
                portal = next((pos for pos, t in m.portals.items() if t == target), None)
                if portal is None and p.map != "commons":
                    portal = next(iter(m.portals), None)
                if portal is not None:
                    p.path = m.path((p.x, p.y), portal, taken)
                    if p.path:
                        p.leaving = portal
                        return
        r = random.random()
        if r < 0.3:
            seats = [s for s in m.seats() if s not in taken and abs(s[0] - p.x) + abs(s[1] - p.y) < 14]
            if seats:
                p.path = m.path((p.x, p.y), random.choice(seats), taken)
                return
        if r < 0.5 and self._here(p) and self.me is not None:
            spot = m.free_near(self.me.x + random.choice((-2, 2)), self.me.y + random.choice((-2, 2)), taken, 3)
            p.path = m.path((p.x, p.y), spot, taken)[:8]
            return
        if r < 0.62:
            p.pose = random.choice(("sit", "sit", "lie"))
            p.facing = random.choice((art.SE, art.SW, art.NE, art.NW))
            return
        if r < 0.75:
            p.facing = random.choice((art.SE, art.SW, art.NE, art.NW))
            return
        goal = m.free_near(p.x + random.randint(-5, 5), p.y + random.randint(-5, 5), taken, 3)
        p.path = m.path((p.x, p.y), goal, taken)

    # ---- talking ----------------------------------------------------------------------------------------
    def _maybe_greet(self, p, chance=0.4):
        if random.random() < chance:
            self._ask(p, f"You just got here and {self.player_name} is here. Say hi if you feel like it, or PASS.")

    def _ask(self, p, nudge, priority=0):
        if p.thinking or not self._here(p):
            return
        if priority == 0 and self.brain.llm_busy():
            return
        p.thinking = True
        map_id = p.map

        def done(action):
            p.thinking = False
            if action is None or not self.logged_in:
                return
            delay = random.uniform(*REPLY_TYPING) + min(len(action[1]) / 25, 5)
            QTimer.singleShot(int(delay * 1000), lambda: self._perform(p, map_id, action))

        self.brain.act(p, self.maps[map_id], list(self.logs.get(map_id, [])), nudge, done, priority)

    @staticmethod
    def emote_text(name, text):
        if text.startswith(("'s ", "' ", ",", ".")):
            return f"{name}{text}"
        return f"{name} {text}"

    def _perform(self, p, map_id, action):
        if not (p.online and p.map == map_id):
            return
        kind, text = action
        line = f"{p.name}: {text}" if kind == "say" else self.emote_text(p.name, text)
        self._log(map_id, line)
        if not self._here(p):
            return
        p.balloon = (text if kind == "say" else "* " + self.emote_text(p.name, text), _now() + BALLOON_SECONDS)
        # turn to face the player when talking to them
        if self.me is not None and abs(self.me.x - p.x) + abs(self.me.y - p.y) < 6 and p.pose == "stand":
            p.facing = self._facing_towards(p, self.me)
        self.line.emit("say" if kind == "say" else "emote", line)
        self._heard(p, line)
        self.next_ambient = max(self.next_ambient, _now() + random.uniform(*AMBIENT_SECONDS) / 2)
        others = [o for o in self.people_in(map_id) if o is not p]
        addressed = [o for o in others if mentions(o.name, text)]
        if addressed:
            self._ask(addressed[0], f"{p.name} just said something to you. Respond if it makes sense, or PASS.", 5)
        elif others and random.random() < 0.2:
            self._ask(random.choice(others), "Respond if you have something to add, or PASS.")

    @staticmethod
    def _facing_towards(a, b):
        dx, dy = b.x - a.x, b.y - a.y
        if abs(dx) >= abs(dy):
            return art.SE if dx > 0 else art.NW
        return art.SW if dy > 0 else art.NE

    def _player_spoke(self, text):
        present = self.people_in(self.me.map)
        if not present:
            return
        addressed = [p for p in present if mentions(p.name, text, prefix=True)]
        if addressed:
            responders = addressed[:2]
        else:
            near = [p for p in present if abs(p.x - self.me.x) + abs(p.y - self.me.y) <= 8] or present
            chance = 0.75 if len(near) == 1 else 0.4
            responders = [p for p in random.sample(near, len(near)) if random.random() < chance][:2]
        for p in responders:
            nudge = (f"{self.player_name} is talking to you. Respond." if p in addressed
                     else "Respond if it makes sense to, or PASS.")
            self._ask(p, nudge, 5)
        self.next_ambient = _now() + random.uniform(*AMBIENT_SECONDS)

    # ---- the player's input -----------------------------------------------------------------------------
    def walk_to(self, x, y):
        if not self.logged_in:
            return
        m = self.here
        goal = (x, y)
        if not m.walkable(*goal) or goal in self.taken(m.id, but=self.me):
            near = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            near = [n for n in near if m.walkable(*n) and n not in self.taken(m.id, but=self.me)]
            if not near:
                return
            goal = min(near, key=lambda n: abs(n[0] - self.me.x) + abs(n[1] - self.me.y))
        self.me.path = m.path((self.me.x, self.me.y), goal, self.taken(m.id, but=self.me))

    def step(self, facing):
        """One hop (arrow keys)."""
        if not self.logged_in:
            return
        dx, dy = art.STEP[facing]
        nx, ny = self.me.x + dx, self.me.y + dy
        self.me.path = []
        self.me.facing = facing
        if self.here.walkable(nx, ny) and (nx, ny) not in self.taken(self.me.map, but=self.me):
            if self.me.hop_from is None or _now() - self.me.hop_t0 >= HOP_SECONDS * 0.8:
                self.hop(self.me, dx, dy)
                self._arrived(self.me)

    def set_pose(self, pose):
        if self.me is None:
            return
        self.me.path = []
        self.me.pose = pose if self.me.pose != pose else "stand"

    def turn(self):
        if self.me is not None:
            self.me.facing = {art.SE: art.SW, art.SW: art.NW, art.NW: art.NE, art.NE: art.SE}[self.me.facing]

    def look_at(self, f):
        if f.player:
            self.line.emit("look", f"You are {f.name}, a {f.species or art.KINDS[f.look.kind][0].lower()}. "
                                   f"{f.desc}".strip())
            return
        self.line.emit("look", f"{f.name}, a {f.species}. {f.desc}".strip())

    def read_sign(self, pos):
        text = self.here.signs.get(pos)
        if text:
            self.line.emit("system", f"The sign reads: \"{text}\"")
            return True
        return False

    def command(self, text):
        text = text.strip()
        if not text or not self.logged_in:
            return
        self.me.idle_since = _now()
        if text[0] in ("`", "@"):
            verb, _, rest = text[1:].partition(" ")
            self._command(verb.lower().rstrip("?"), rest.strip())
            return
        if text.startswith(":"):
            body = text[1:].strip()
            if body:
                line = self.emote_text(self.me.name, body)
                self.me.balloon = ("* " + line, _now() + BALLOON_SECONDS)
                self.line.emit("emote", line)
                self._log(self.me.map, line)
                self._player_spoke(body)
            return
        if text.startswith("/"):
            name, _, msg = text[1:].partition(" ")
            self.whisper(name, msg.strip())
            return
        if text.startswith('"'):
            text = text[1:].strip()
        line = f"{self.me.name}: {text}"
        self.me.balloon = (text, _now() + BALLOON_SECONDS)
        self.line.emit("me", line)
        self._log(self.me.map, line)
        self._player_spoke(text)

    def whisper(self, name, msg):
        if not msg:
            self.line.emit("system", "Whisper with /name message")
            return
        p = self.find(name)
        if p is None:
            self.line.emit("system", f"{name} isn't on Furcadia right now.")
            return
        self.line.emit("whisper", f"You whisper \"{msg}\" to {p.name}.")
        from ..muck.world import _heard
        _heard(p, "Furcadia (whispering)", self.me.name, msg)

        def reply(text):
            if text and self.logged_in and p.online:
                delay = random.uniform(*REPLY_TYPING) + min(len(text) / 25, 5)
                QTimer.singleShot(int(delay * 1000), lambda: self._whisper_back(p, text))

        self.brain.whisper(p, msg, reply)

    def _whisper_back(self, p, text):
        if self.logged_in and p.online:
            self.line.emit("whisper", f"{p.name} whispers, \"{text}\" to you.")
            self._heard(p, f"(whispering to {self.me.name}) {text}")

    def who(self):
        on = self.online()
        if not on:
            self.line.emit("system", "Nobody you know is on right now.")
            return
        by = {}
        for p in on:
            by.setdefault(p.map, []).append(p.name)
        self.line.emit("system", f"{len(on)} furre{'s' if len(on) != 1 else ''} you know are online:")
        for mid, names in by.items():
            self.line.emit("system", f"  {self.maps[mid].name}: {', '.join(sorted(names))}")

    def join(self, name):
        p = self.find(name)
        if p is None:
            self.line.emit("system", f"{name} isn't on Furcadia right now.")
            return
        if p.map != self.me.map:
            old = self.me.map
            self._log(old, f"{self.me.name} has left.")
            self.me.map = p.map
        m = self.here
        self.me.x, self.me.y = m.free_near(p.x, p.y, self.taken(m.id, but=self.me) | {(p.x, p.y)}, 4)
        self.me.path, self.me.hop_from, self.me.pose = [], None, "stand"
        self.line.emit("dream", f"You join {p.name} in {m.name}.")
        self._enter_text()
        self.moved.emit()
        self.save_player()

    def go_home(self):
        m = self.maps["commons"]
        self.me.map = "commons"
        self.me.x, self.me.y = m.free_near(*m.spawn, self.taken("commons", but=self.me))
        self.me.path, self.me.hop_from, self.me.pose = [], None, "stand"
        self._enter_text()
        self.moved.emit()

    def _command(self, verb, rest):
        if verb in ("help", "h"):
            for line in HELP.splitlines():
                self.line.emit("system", line)
        elif verb in ("who", "onln", "online"):
            self.who()
        elif verb in ("look", "l"):
            f = self.find(rest) if rest else self.me
            self.look_at(f) if f else self.line.emit("system", f"There's nobody called {rest} online.")
        elif verb in ("sit", "lie", "stand"):
            self.me.path = []
            self.me.pose = verb
        elif verb == "desc":
            if rest:
                self.me.desc = rest
                self.player_data["desc"] = rest
                self.save_player()
                self.line.emit("system", "Description set.")
            else:
                self.look_at(self.me)
        elif verb in ("join", "summon"):
            self.join(rest)
        elif verb in ("home", "commons"):
            self.go_home()
        elif verb in ("dreams", "where"):
            self.line.emit("system", f"You are in {self.here.name}. The dreams: " +
                           ", ".join(m.name for m in self.maps.values()))
        else:
            self.line.emit("system", f"Unknown command `{verb}. Type `help for the list.")


HELP = """Furcadia commands:
  just type            say it out loud              :text        emote (":waves")
  /name text           whisper to someone           `look name   look at a furre (or click them)
  `who                 who you know is online       `join name   hop over to a friend
  `sit  `lie  `stand   change pose (F3 / F4)        `desc text   set your description
  `home                back to Willowmere Commons   `dreams      list the dreams
Move with the arrow keys or the numeric keypad (7 9 1 3), or click where you want to go.
Step onto a glowing portal to travel to another dream."""
