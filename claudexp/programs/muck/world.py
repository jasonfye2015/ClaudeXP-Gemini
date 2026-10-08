"""PawPrints MUCK, simulated: rooms, characters connecting and wandering, and the command parser.

The client only sees text: World.line(kind, text) signals, and World.command(text) for input.
Rooms and MUCK-only characters live in 'Program Files/ClaudeMUCK/world'; AIM buddies come from
ClaudeAIM's contacts (an optional "muck" section there customises them).
"""
import random
import time
from collections import deque
from dataclasses import dataclass, field

from PySide6.QtCore import QObject, QTimer, Signal

from ...paths import ROOT
from ..people import aim_screen_name, available, load_buddies, parse_hours
from ..people import load_json as _load_json
from ..people import save_json as _save_json
from .brain import WORLD_NAME, Brain

MUCK_DIR = ROOT / "Program Files" / "ClaudeMUCK"
WORLD_DIR = MUCK_DIR / "world"
DATA_DIR = MUCK_DIR / "data"
PLAYER_FILE = DATA_DIR / "player.json"
DESCS_FILE = DATA_DIR / "descriptions.json"

TICK_MS = 5000
SESSION_MINUTES = (40, 180)       # how long a character stays connected
OFFLINE_MINUTES = (20, 120)       # how long they stay away between sessions
MOVE_MINUTES = (4, 20)            # how often a wandering character changes rooms
AMBIENT_SECONDS = (75, 240)       # quiet time before someone in your room does something
REPLY_TYPING = (1.5, 5.0)         # seconds of 'typing' before a reply shows up
SPEED = 1.0                       # >1 makes everything happen faster (for testing)

HELP = """\
PawPrints MUCK commands:
  look (l)                 look at the room          look <name>   look at someone
  "<text>   or  say <text> say something             :<text>       pose an action
  page <name>=<text>       private message           whisper <name>=<text>
  <exit name>              walk that way (n, s, e, w, out, ...)
  home                     go to your den            WHO           who's online
  @doing <text>            set your WHO 'doing'      @describe me=<text>
  @describe here=<text>    describe your den         inventory (i)
  QUIT                     disconnect"""

BANNER = """\
  ____                 ____       _       _
 |  _ \\ __ ___      __|  _ \\ _ __(_)_ __ | |_ ___
 | |_) / _` \\ \\ /\\ / /| |_) | '__| | '_ \\| __/ __|
 |  __/ (_| |\\ V  V / |  __/| |  | | | | | |_\\__ \\
 |_|   \\__,_| \\_/\\_/  |_|   |_|  |_|_| |_|\\__|___/   M U C K

        A furry social MUCK -- since 1997 -- TinyMUCK 2.2fb6.0

  To connect to your character:   connect <name> <password>
  To create a new character:       create <name> <password>
  To see who is online:            WHO
  To leave:                        QUIT
"""


def _now():
    return time.monotonic() * SPEED


def _heard(c, program, speaker, text):
    """Tell the shared memory about a line of conversation with a buddy."""
    from ...life import get as life
    if c is not None and c.contact is not None and life() is not None:
        life().heard(c.contact.screen_name, program, speaker, text)


def _minutes(lo_hi):
    return random.uniform(*lo_hi) * 60


@dataclass
class Exit:
    names: list
    target: str


@dataclass
class Room:
    id: str
    name: str
    desc: str
    exits: list
    public: bool = True
    popularity: float = 1.0

    def exit_named(self, word):
        word = word.lower()
        for ex in self.exits:
            if word in ex.names:
                return ex
        return None


@dataclass
class Character:
    name: str
    species: str
    persona: str
    desc: str = ""
    haunts: list = field(default_factory=list)
    doing: str = ""
    wizard: bool = False
    idle_only: bool = False
    moves: bool = True
    hours: tuple = None            # (start, end) local minutes, for MUCK-only characters
    start_chance: float = 0.6
    temperature: float = 0.9
    contact: object = None         # the AIM contact, for buddies
    # state
    online: bool = False
    room: str = ""
    on_since: float = 0.0
    last_active: float = 0.0
    session_end: float = 0.0
    next_online: float = 0.0
    next_move: float = 0.0
    thinking: bool = False
    page_history: list = field(default_factory=list)

    def available(self):
        """Awake and free to be online right now (in their own time zone)."""
        return available(self.contact, self.hours)


def _duration(seconds):
    seconds = int(max(0, seconds))
    if seconds < 3600 * 24:
        return f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}"
    return f"{seconds // 86400}d {seconds // 3600 % 24:02d}:{seconds // 60 % 60:02d}"


def _idle(seconds):
    seconds = int(max(0, seconds))
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


class World(QObject):
    line = Signal(str, str)      # (kind, text) for the client to show
    closed = Signal()            # QUIT

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rooms = {}
        self.start_room = "welcome"
        self.people = []
        self.load_errors = []
        self.descs = _load_json(DESCS_FILE, {})
        self.player = _load_json(PLAYER_FILE, None)
        self.aim_name = aim_screen_name()
        self.logged_in = False
        self.player_room = ""
        self.player_on_since = 0.0
        self.player_last_active = 0.0
        self.logs = {}
        self.next_ambient = 0.0
        self._load_world()
        self.brain = Brain(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    # ---- loading ----------------------------------------------------------------
    def _load_world(self):
        data = _load_json(WORLD_DIR / "map.json", {})
        self.start_room = data.get("start", "welcome")
        for rid, r in data.get("rooms", {}).items():
            exits = [Exit([n.strip().lower() for n in key.split(";") if n.strip()], target)
                     for key, target in r.get("exits", {}).items()]
            self.rooms[rid] = Room(rid, r.get("name", rid), r.get("desc", ""), exits, r.get("public", True),
                                   float(r.get("popularity", 1)))
        public = [rid for rid, room in self.rooms.items() if room.public]

        for r in _load_json(WORLD_DIR / "regulars.json", {}).get("regulars", []):
            try:
                self.people.append(Character(
                    name=r["name"], species=r.get("species", "critter"), persona=r.get("persona", ""),
                    desc=r.get("desc", ""), haunts=[h for h in r.get("haunts", public) if h in self.rooms],
                    doing=r.get("doing", ""), wizard=bool(r.get("wizard")), idle_only=bool(r.get("idle_only")),
                    moves=r.get("moves", True), start_chance=float(r.get("start_chance", 0.6)),
                    hours=parse_hours(r.get("hours")),
                    temperature=float(r.get("temperature", 0.9))))
            except (KeyError, ValueError) as e:
                self.load_errors.append(f"regulars.json: {e}")

        buddies, errors = load_buddies("muck")
        self.load_errors += errors
        for c, muck in buddies:
            self.people.append(Character(
                name=muck.get("name", c.screen_name), species=muck.get("species", "furry"),
                persona=c.persona, desc=muck.get("desc", ""),
                haunts=[h for h in muck.get("haunts", public) if h in self.rooms] or public,
                doing=muck.get("doing", ""), start_chance=c.start_online_chance,
                temperature=c.temperature, contact=c))

    # ---- helpers ----------------------------------------------------------------
    @property
    def player_name(self):
        return self.player["name"] if self.player else "someone"

    def out(self, kind, text):
        self.line.emit(kind, text)

    def people_in(self, room_id):
        return [p for p in self.people if p.online and p.room == room_id]

    def find_person(self, word, online_only=True):
        word = word.strip().lower()
        if not word:
            return None
        pool = [p for p in self.people if p.online or not online_only]
        for p in pool:
            if p.name.lower() == word:
                return p
        matches = [p for p in pool if p.name.lower().startswith(word)]
        return matches[0] if len(matches) == 1 else None

    def description_of(self, c):
        return c.desc or self.descs.get(c.name, "")

    def room(self, rid):
        room = self.rooms.get(rid) or self.rooms[self.start_room]
        if room.id == "home" and self.player:
            name = room.name.replace("{player}", self.player["name"])
            desc = self.player.get("home_desc") or room.desc
            return Room(room.id, name, desc, room.exits, room.public)
        return room

    def log(self, room_id, text):
        self.logs.setdefault(room_id, deque(maxlen=30)).append(text)

    def _here(self, c):
        return self.logged_in and c.online and c.room == self.player_room

    # ---- session ------------------------------------------------------------------
    def connect_session(self):
        for line in BANNER.splitlines():
            self.out("banner", line)
        if self.load_errors:
            self.out("error", "Warning: " + "; ".join(self.load_errors))
        if self.player and self.player.get("autologin"):
            QTimer.singleShot(600, lambda: self.command(f"connect {self.player['name']} {self.player['password']}",
                                                        echo=False))

    def disconnect_session(self):
        self.timer.stop()
        if self.logged_in:
            self._save_player()
        self.logged_in = False

    def _login(self, new=False):
        self.logged_in = True
        now = _now()
        self.player_on_since = self.player_last_active = now
        self.player_room = self.player.get("room") or self.start_room
        self._populate()
        self.next_ambient = now + random.uniform(*AMBIENT_SECONDS)
        self.timer.start(TICK_MS)
        if not new:
            self.out("system", f"Welcome back to {WORLD_NAME}, {self.player['name']}!")
        self.look()
        if new:
            QTimer.singleShot(2500, self._wizard_welcome)

    def _wizard_welcome(self):
        """Staff pop in to greet brand new players, like on a real MUCK."""
        wizards = [p for p in self.people if p.wizard and p.online and not p.thinking]
        if not wizards or not self.logged_in:
            return
        wiz = wizards[0]
        if wiz.room != self.player_room:
            if self._here(wiz):
                self.out("arrive", f"{wiz.name} has left.")
            self.log(wiz.room, f"{wiz.name} has left.")
            wiz.room = self.player_room
            self.log(wiz.room, f"{wiz.name} has arrived.")
            self.out("arrive", f"{wiz.name} has arrived.")
        wiz.next_move = _now() + _minutes(MOVE_MINUTES)
        self._ask(wiz, f"{self.player_name} is a brand new player who just created their character. "
                       "As a wizard, welcome them warmly and offer to help them get started.", 5)

    def _populate(self):
        """Who's already online when you connect."""
        now = _now()
        for p in self.people:
            if p.available() and random.random() < p.start_chance:
                self._bring_online(p, announce=False)
                p.on_since = now - random.uniform(5, 150) * 60
                p.last_active = now - random.uniform(0, 30) * 60 if not p.idle_only \
                    else now - random.uniform(2, 9) * 3600
            else:
                p.online = False
                p.next_online = now + _minutes((2, 40))

    def _bring_online(self, p, announce=True):
        now = _now()
        p.online = True
        p.on_since = p.last_active = now
        p.room = self._pick_room(p.haunts)
        p.session_end = now + _minutes(SESSION_MINUTES)
        p.next_move = now + _minutes(MOVE_MINUTES)
        if announce:
            self.log(p.room, f"{p.name} has connected.")
            if self._here(p):
                self.out("arrive", f"{p.name} has connected.")
                self._maybe_greet(p)

    def _pick_room(self, rooms):
        """A room from rooms, favouring popular ones."""
        if not rooms:
            return self.start_room
        return random.choices(rooms, weights=[self.rooms[r].popularity for r in rooms])[0]

    def _take_offline(self, p):
        if self._here(p):
            self.out("arrive", f"{p.name} has disconnected.")
        self.log(p.room, f"{p.name} has disconnected.")
        p.online = False
        p.next_online = _now() + _minutes(OFFLINE_MINUTES)

    # ---- the clock ------------------------------------------------------------------
    def _tick(self):
        now = _now()
        for p in self.people:
            if p.online and not p.idle_only and (now >= p.session_end or not p.available()):
                self._take_offline(p)
            elif not p.online and now >= p.next_online:
                if p.available():
                    self._bring_online(p)
                else:
                    p.next_online = now + _minutes((15, 45))
            elif p.online and p.moves and not p.idle_only and now >= p.next_move and not p.thinking:
                self._wander(p)
        if now >= self.next_ambient:
            self.next_ambient = now + random.uniform(*AMBIENT_SECONDS)
            talkers = [p for p in self.people_in(self.player_room) if not p.idle_only and not p.thinking]
            if talkers:
                self._ask(random.choice(talkers), "It's been quiet for a little while. Do or say something "
                                                  "small if you feel like it, or PASS.")

    def _wander(self, p):
        p.next_move = _now() + _minutes(MOVE_MINUTES)
        here = self.rooms.get(p.room)
        choices = [ex for ex in (here.exits if here else []) if self.rooms.get(ex.target, Room("", "", "", [])).public]
        choices = [ex for ex in choices if ex.target in p.haunts] or choices
        if not choices:
            return
        ex = random.choices(choices, weights=[self.rooms[c.target].popularity for c in choices])[0]
        if self._here(p):
            self.out("arrive", f"{p.name} has left.")
        self.log(p.room, f"{p.name} has left.")
        p.room = ex.target
        self.log(p.room, f"{p.name} has arrived.")
        if self._here(p):
            self.out("arrive", f"{p.name} has arrived.")
            self._maybe_greet(p)

    def _maybe_greet(self, p, chance=0.4):
        if not p.idle_only and random.random() < chance:
            self._ask(p, f"You just got here and {self.player_name} is here. Say hi if you feel like it, or PASS.")

    # ---- characters acting --------------------------------------------------------------
    def _ask(self, p, nudge, priority=0):
        """Ask the model what p does in the player's room, then show it after a typing pause."""
        if p.thinking or p.idle_only:
            return
        p.thinking = True
        room_id = self.player_room
        room = self.room(room_id)

        def done(action):
            p.thinking = False
            if action is None or not self.logged_in:
                return
            delay = random.uniform(*REPLY_TYPING) + min(len(action[1]) / 25, 6)
            QTimer.singleShot(int(delay * 1000), lambda: self._perform(p, room_id, action))

        if priority == 0 and self.brain.llm_busy():
            p.thinking = False
            return  # don't pile ambient chatter up behind other work
        self.brain.act(p, room, list(self.logs.get(room_id, [])), nudge, done, priority)

    def _perform(self, p, room_id, action):
        if not (p.online and p.room == room_id):
            return
        kind, text = action
        p.last_active = _now()
        line = f'{p.name} says, "{text}"' if kind == "say" else self._pose_text(p.name, text)
        self.log(room_id, line)
        if self.logged_in and self.player_room == room_id:
            self.out(kind, line)
            _heard(p, f"the MUCK ({self.room(room_id).name})", p.name, line)
            self.next_ambient = max(self.next_ambient, _now() + random.uniform(*AMBIENT_SECONDS) / 2)
            # Sometimes someone else answers them.
            others = [o for o in self.people_in(room_id) if o is not p and not o.idle_only]
            addressed = [o for o in others if o.name.lower() in text.lower()]
            if addressed:
                self._ask(addressed[0], f"{p.name} just said something to you. Respond if it makes sense, or PASS.", 5)
            elif others and random.random() < 0.2:
                self._ask(random.choice(others), "Respond if you have something to add, or PASS.")

    @staticmethod
    def _pose_text(name, text):
        if text.startswith(("'s ", "' ", ",", ".")):
            return f"{name}{text}"
        return f"{name} {text}"

    def _player_spoke(self, text):
        """After the player says/poses something, the people here may react."""
        present = [p for p in self.people_in(self.player_room) if not p.idle_only]
        if not present:
            return
        lowered = text.lower()
        addressed = [p for p in present if p.name.lower() in lowered
                     or (len(p.name) > 4 and p.name.lower()[:5] in lowered)]
        if addressed:
            responders = addressed[:2]
        else:
            chance = 0.75 if len(present) == 1 else 0.4
            responders = [p for p in random.sample(present, len(present)) if random.random() < chance][:2]
        for p in responders:
            nudge = (f"{self.player_name} is talking to you. Respond." if p in addressed
                     else "Respond if it makes sense to, or PASS.")
            self._ask(p, nudge, 5)
        self.next_ambient = _now() + random.uniform(*AMBIENT_SECONDS)

    # ---- input --------------------------------------------------------------------------
    def command(self, text, echo=True):
        text = text.strip()
        if not text:
            return
        if not self.logged_in:
            self._login_command(text)
            return
        self.player_last_active = _now()
        if text[0] in "\":;":
            self.say(text[1:].lstrip()) if text[0] == '"' else self.pose(text[1:], possessive=text[0] == ";")
            return
        verb, _, rest = text.partition(" ")
        verb_l = verb.lower()
        rest = rest.strip()
        handlers = {
            "look": self.look, "l": self.look, "read": self.look,
            "say": self.say, "pose": self.pose, ":": self.pose,
            "page": self.page, "p": self.page, "whisper": self.whisper, "w": self.whisper,
            "who": self.who, "home": self.home, "go": self.go, "move": self.go,
            "@doing": self.set_doing, "@describe": self.describe, "@desc": self.describe,
            "inventory": self.inventory, "i": self.inventory, "inv": self.inventory,
            "help": self.help, "+help": self.help, "news": self.help,
            "quit": self.quit, "score": self.score,
        }
        if verb_l in handlers:
            handlers[verb_l](rest)
            return
        ex = self.room(self.player_room).exit_named(text)
        if ex:
            self._move_player(ex.target)
            return
        self.out("system", 'Huh?  (Type "help" for help.)')

    def _login_command(self, text):
        verb, _, rest = text.partition(" ")
        verb = verb.lower()
        if verb == "who":
            self.who("")
        elif verb == "quit":
            self.quit("")
        elif verb in ("connect", "co", "create"):
            parts = rest.split()
            if len(parts) < 2:
                self.out("system", f"Usage: {verb} <name> <password>")
                return
            name, password = parts[0], parts[1]
            if verb == "create":
                if not name.isalnum() or len(name) > 20:
                    self.out("system", "That's a silly name for a player!")
                elif self.find_person(name, online_only=False) or (self.player and self.player["name"].lower() == name.lower()):
                    self.out("system", "There is already a player with that name.")
                else:
                    self.player = {"name": name, "password": password, "desc": "", "doing": "",
                                   "room": self.start_room, "autologin": True}
                    self._save_player()
                    self.out("system", f"Character {name} created. Welcome to {WORLD_NAME}!")
                    self._login(new=True)
            else:
                if (self.player and self.player["name"].lower() == name.lower()
                        and self.player["password"] == password):
                    self._login()
                else:
                    self.out("system", "Either that player does not exist, or has a different password.")
        else:
            self.out("system", "Please connect or create a character first. (connect <name> <password>)")

    def _save_player(self):
        if self.player:
            self.player["room"] = self.player_room or self.player.get("room", self.start_room)
            _save_json(PLAYER_FILE, self.player)

    # ---- commands --------------------------------------------------------------------------
    def look(self, rest=""):
        target = rest.strip()
        if target and target.lower() not in ("here", "room"):
            self._look_at(target)
            return
        room = self.room(self.player_room)
        self.out("room", room.name)
        self.out("desc", room.desc)
        here = self.people_in(self.player_room)
        if here:
            self.out("contents", "Contents:")
            for p in sorted(here, key=lambda p: p.name.lower()):
                self.out("contents", f"  {p.name}")
        exits = [ex.names[0].capitalize() for ex in room.exits]
        if exits:
            self.out("exits", "Obvious exits: " + ", ".join(exits))

    def _look_at(self, target):
        if target.lower() in ("me", (self.player_name or "").lower()):
            self.out("room", self.player_name)
            self.out("desc", self.player.get("desc") or "You see nothing special.")
            return
        p = self.find_person(target)
        if p is None or p.room != self.player_room:
            self.out("system", "I don't see that here.")
            return
        self.out("room", p.name)
        desc = self.description_of(p)
        if desc:
            self.out("desc", desc)
            return

        def got(text):
            if text:
                self.descs[p.name] = text
                _save_json(DESCS_FILE, self.descs)
            self.out("desc", text or "You see nothing special.")

        self.brain.describe(p, got)

    def say(self, text):
        if not text:
            self.out("system", "What do you want to say?")
            return
        self.out("say", f'You say, "{text}"')
        self.log(self.player_room, f'{self.player_name} says, "{text}"')
        self._tell_room_memory(f'{self.player_name} says, "{text}"')
        self._player_spoke(text)

    def pose(self, text, possessive=False):
        text = text.strip() if not possessive else text
        if not text.strip():
            self.out("system", "What do you want to do?")
            return
        line = f"{self.player_name}{text}" if possessive else self._pose_text(self.player_name, text)
        self.out("pose", line)
        self.log(self.player_room, line)
        self._tell_room_memory(line)
        self._player_spoke(text)

    def _tell_room_memory(self, line):
        where = f"the MUCK ({self.room(self.player_room).name})"
        for c in self.people_in(self.player_room):
            _heard(c, where, self.player_name, line)

    def _split_target(self, rest, usage):
        name, eq, msg = rest.partition("=")
        if not eq or not name.strip() or not msg.strip():
            self.out("system", usage)
            return None, None
        return name.strip(), msg.strip()

    def page(self, rest):
        name, msg = self._split_target(rest, "Usage: page <name>=<message>")
        if name is None:
            return
        p = self.find_person(name)
        if p is None:
            known = self.find_person(name, online_only=False)
            self.out("system", f"{known.name} is not connected." if known else "I don't recognize that player.")
            return
        if msg.startswith(":"):
            self.out("page", f"You page-pose, \"{self.player_name} {msg[1:].strip()}\" to {p.name}.")
        else:
            self.out("page", f'You page, "{msg}" to {p.name}.')
        if p.idle_only:
            return
        if p.thinking:
            QTimer.singleShot(4000, lambda: self._answer_page(p, msg))
        else:
            self._answer_page(p, msg)

    def _answer_page(self, p, msg):
        _heard(p, "the MUCK (pages)", self.player_name, msg)
        p.thinking = True

        def done(reply):
            p.thinking = False
            if reply and p.online and self.logged_in:
                delay = random.uniform(*REPLY_TYPING) + min(len(reply) / 25, 6)
                QTimer.singleShot(int(delay * 1000), lambda: self._show_page(p, reply))

        self.brain.page(p, msg, done)

    def _show_page(self, p, reply):
        if p.online and self.logged_in:
            p.last_active = _now()
            self.out("page", f'{p.name} pages, "{reply}" to you.')
            _heard(p, "the MUCK (pages)", p.name, reply)

    def whisper(self, rest):
        name, msg = self._split_target(rest, "Usage: whisper <name>=<message>")
        if name is None:
            return
        p = self.find_person(name)
        if p is None or p.room != self.player_room:
            self.out("system", "I don't see that player here.")
            return
        self.out("page", f'You whisper, "{msg}" to {p.name}.')
        if not p.idle_only:
            self._answer_page(p, f"(whispered to you in person) {msg}")

    def who(self, rest=""):
        now = _now()
        rows = []
        if self.logged_in:
            rows.append((self.player_name, now - self.player_on_since, now - self.player_last_active,
                         self.player.get("doing", "")))
        for p in self.people:
            if p.online:
                rows.append((p.name, now - p.on_since, now - p.last_active, p.doing))
        rows.sort(key=lambda r: r[1])
        self.out("who", f"{'Player Name':<18}{'On For':>8}{'Idle':>6}  Doing...")
        for name, on_for, idle, doing in rows:
            self.out("who", f"{name:<18}{_duration(on_for):>8}{_idle(idle):>6}  {doing[:40]}")
        self.out("who", f"{len(rows)} players are connected.  (Max was 214)")

    def _move_player(self, target):
        old = self.player_room
        self.log(old, f"{self.player_name} has left.")
        self.player_room = target
        self.log(target, f"{self.player_name} has arrived.")
        self.look()
        present = [p for p in self.people_in(target) if not p.idle_only]
        if present and random.random() < 0.5:
            self._ask(random.choice(present), f"{self.player_name} just arrived. Greet them if you want, or PASS.", 5)
        self.next_ambient = _now() + random.uniform(*AMBIENT_SECONDS)

    def go(self, rest):
        ex = self.room(self.player_room).exit_named(rest)
        if ex:
            self._move_player(ex.target)
        else:
            self.out("system", "You can't go that way.")

    def home(self, rest=""):
        self.out("system", "There's no place like home...")
        self._move_player("home" if "home" in self.rooms else self.start_room)

    def set_doing(self, rest):
        self.player["doing"] = rest[:40]
        self._save_player()
        self.out("system", "Doing set." if rest else "Doing cleared.")

    def describe(self, rest):
        what, eq, text = rest.partition("=")
        what = what.strip().lower()
        if not eq:
            self.out("system", "Usage: @describe me=<text>   or   @describe here=<text>")
        elif what == "me":
            self.player["desc"] = text.strip()
            self._save_player()
            self.out("system", "Description set.")
        elif what == "here" and self.player_room == "home":
            self.player["home_desc"] = text.strip()
            self._save_player()
            self.out("system", "Description set.")
        else:
            self.out("system", "Permission denied.")

    def inventory(self, rest=""):
        self.out("system", "You aren't carrying anything.")

    def score(self, rest=""):
        self.out("system", "You have 42 pennies.")

    def help(self, rest=""):
        for line in HELP.splitlines():
            self.out("system", line)

    def quit(self, rest=""):
        self.out("system", "Goodbye! Come back soon!")
        self.disconnect_session()
        self.closed.emit()
