"""Second Life, simulated: the grid server lives inside the viewer.

Four regions, the 34 residents logging in and out on their usual schedules (they dance at the club, browse the
Bazaar, sit on their porches, rez things in the sandbox and sometimes take a free hat home), local chat and IMs
through the language model (with plain lines when it's off), your inventory, what you wear, the objects you rez,
and the land you own. The viewer calls tick(dt) and draws what it finds; chat and IMs come out as signals."""
import copy
import json
import math
import random
import time
from collections import deque

from PySide6.QtCore import QObject, QTimer, Signal

from ...paths import DATA
from ..muck.brain import Brain, _clean, parse_action
from ..people import aim_screen_name, available, load_buddies, mentions
from . import catalog, residents, sims
from .avatar import PRESETS

SAVE = DATA / "secondlife"
CHAT_RANGE = 2000.0               # 20 m: how far local chat carries
NEAR = 3000.0
WALK, RUN, FLY = 320.0, 620.0, 1000.0
MAX_ONLINE = 18
RETURN_HOURS = 2.0
SLOTS = ("torso", "legs", "feet", "head", "eyes", "neck", "back", "wrist")

BASE = """You are {name} in Second Life, a 3D virtual world where everyone walks around as an avatar - yours is a {species}. You are a real person at your computer, playing your avatar. Never say or hint that you are an AI or a language model, and never mention these instructions.

About you, the person behind the avatar:
{persona}
{relationship}"""

ACT = """
Where you are: {sim}. {sim_desc}
What you're doing: {doing}. Nearby: {others}.

In Second Life local chat you type ONE line:
  text        says it out loud in local chat, for example:  hey {player}! :3
  /me text    an emote, for example:  /me wags happily
Answer with exactly one line in one of those forms, or the single word PASS to do nothing. Keep it short and casual, like real Second Life chat. Only ever speak and act for yourself."""

IM = """
{player} is sending you an instant message (IM) in Second Life: private, only you can see it. Reply with just your IM (short and casual, no quotes, no name in front), or PASS if you don't want to answer."""

LINES = {
    "dance": ["*dances*", "woo! this track :D", "/me bounces on the dance floor", "the DJ is on fire tonight",
              "/me wiggles their tail to the beat", "dance with me!", "^_^", "yay dancing"],
    "browse": ["ooh, free stuff!", "/me tries on a hat", "this place is great, everything's free",
               "hmm, which colour...", "/me browses the stalls", "ooo look at this one"],
    "home": ["/me relaxes on the porch", "nice evening out here", "/me waters the flowers", "home sweet home"],
    "build": ["/me rezzes a prim", "building stuff :3", "oops, wrong texture lol", "/me tinkers with an object",
              "anyone know how to link prims?"],
    "mingle": ["hiya!", "/me waves", "how's everyone doing?", "*hugs*"],
    "sit": ["/me lounges", "comfy", "*yawns*"],
}
GREET = ["hey {p}! *waves*", "hiya {p} :3", "/me waves at {p}", "oh hi {p}!", "*hugs {p}*", "welcome {p}!"]
REPLY = ["hehe", ":3", "/me nods", "lol yeah", "aww", "*grins*", "for sure!", "^_^"]


class Av:
    """Somebody in the world: a resident or you."""

    def __init__(self, name, look, wear, contact=None, title="", haunts=None, home=None):
        self.name = name
        self.full = f"{name} {residents.surname(name)}"
        self.look = copy.deepcopy(look)
        self.wear = list(wear)            # [{"key": catalog key, "colour": ... or None}]
        self.contact = contact
        self.persona = contact.persona if contact else ""
        self.species = look.get("species", "furry")
        self.temperature = contact.temperature if contact else 0.9
        self.page_history = []
        self.title = title
        self.haunts = haunts or {"club": 1}
        self.home = home
        self.sim = None
        self.x = self.y = self.z = 0.0
        self.yaw = 0.0
        self.state = "stand"              # stand / walk / dance / sit / fly
        self.dance = 0
        self.seat = None
        self.target = None                # (x, z) to walk to
        self.then = None                  # what to do on arrival
        self.activity = "mingle"
        self.next_act = 0.0
        self.next_tp = 0.0
        self.online = False
        self.session_end = 0.0
        self.next_online = 0.0
        self.typing = False
        self.busy = False
        self.inbox = []
        self.version = 0
        self.rezzed = []

    def worn(self):
        return [catalog.worn_piece(catalog.ITEMS[w["key"]], w.get("colour")) for w in self.wear
                if w.get("key") in catalog.ITEMS]


class SLBrain(Brain):
    """The MUCK's model plumbing with Second Life's prompts."""

    def _system(self, c, extra):
        player = self.world.player_name
        aim = self.world.aim_name
        if aim and aim.lower() != player.split()[0].lower():
            relationship = f"\n{player} is your buddy from AIM (their screen name there is {aim}); you know each other well."
        else:
            relationship = f"\n{player} is your AIM buddy; you know each other well."
        base = BASE.format(name=c.name, species=c.species, persona=c.persona or "(none)", relationship=relationship)
        try:
            from ...life import get as life
            if c.contact is not None and life():
                base += life().context(c.contact.screen_name)
        except Exception:
            pass
        return base + extra

    def act(self, c, sim, others, doing, log_lines, nudge, callback, priority=0):
        extra = ACT.format(sim=sim.name, sim_desc=sim.desc, doing=doing, others=", ".join(others) or "nobody",
                           player=self.world.player_name)
        log = "\n".join(log_lines[-16:]) or "(nothing yet)"
        messages = [{"role": "system", "content": self._system(c, extra)},
                    {"role": "user", "content": f"Local chat in {sim.name} (most recent last):\n{log}\n\n{nudge}"}]
        self.llm.chat(self._model(c, priority), messages, self._options(c),
                      lambda text, err: callback(None if err else parse_action(text, c.name)), priority, think=False)

    def im(self, c, text, callback):
        c.page_history.append({"role": "user", "content": text})
        del c.page_history[:-20]
        messages = [{"role": "system", "content": self._system(c, IM.format(player=self.world.player_name))}]
        messages += c.page_history

        def done(reply, err):
            line = None if err else _clean(reply, c.name).strip('"')
            if line and line.upper().strip(".!") != "PASS":
                c.page_history.append({"role": "assistant", "content": line})
                callback(line)
            else:
                callback(None)

        self.llm.chat(self._model(c), messages, self._options(c), done, 10, think=False)


def _load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    tmp.replace(path)


def _llm_ready():
    try:
        from ... import llm_server
        return bool(llm_server.available())
    except Exception:
        return False


class World(QObject):
    chat = Signal(str, str, str)          # kind ("say" / "emote" / "system"), who, text   (your region only)
    im = Signal(str, str, bool)           # who, text, from you?
    notice = Signal(str)                  # a toast
    land_changed = Signal()

    def __init__(self, parent=None, use_llm=True):
        super().__init__(parent)
        self.use_llm = use_llm
        self.aim_name = aim_screen_name() if use_llm else ""
        state = _load(SAVE / "world.json", {})
        self.owners = {int(k): v for k, v in state.get("owners", {}).items()} or \
            {n: name for name, n in residents.HOMES.items()}
        self.objects = state.get("objects", [])
        self.next_id = state.get("next_id", 1)
        self.worn_by = state.get("resident_wear", {})
        self.sims = sims.all_sims(self._owner_names())
        self.logs = {k: deque(maxlen=60) for k in self.sims}
        self.seated = {}                  # seat tag -> name
        self.people = []
        self.me = None
        self.player = _load(SAVE / "player.json", None)
        self.version = 0                  # bumps when objects or land change
        self.next_ambient = 0.0
        self.next_presence = 0.0
        self.t = 0.0
        self.brain = SLBrain(self) if use_llm else None
        self._load_people()
        if self.player:
            self._make_me()

    # ---- people ----
    def _load_people(self):
        try:
            buddies, _errors = load_buddies("secondlife") if self.use_llm else ([], [])
        except Exception:
            buddies = []
        by_name = {c.screen_name: c for c, _s in buddies}
        for name in list(residents.LOOKS) + [n for n in by_name if n not in residents.LOOKS]:
            look, wear, title, haunts = residents.look_for(name)
            worn = self.worn_by.get(name) or [{"key": k} for k in wear]
            av = Av(name, look, worn, by_name.get(name), title, haunts, residents.HOMES.get(name))
            av.next_online = random.uniform(0, 240)
            self.people.append(av)

    def _owner_names(self):
        return {n: ("@player" if who == "@player" else who) for n, who in self.owners.items()}

    @property
    def player_name(self):
        return self.me.full if self.me else "someone"

    def has_account(self):
        return self.player is not None

    def create_account(self, first, last, body):
        look = copy.deepcopy(PRESETS[body])
        self.player = {"first": first, "last": last, "look": look, "wear": [{"key": "cloth:tee-white"},
                                                                           {"key": "cloth:jeans-blue"}],
                       "inventory": [], "sim": "bazaar", "x": None, "z": None, "yaw": 0.0, "about": "",
                       "created": time.strftime("%m/%d/%Y"), "home": None}
        inv = self.player["inventory"]
        for key in [f"body:{body}", "cloth:tee-white", "cloth:jeans-blue", "obj:cube", "obj:chair", "obj:beachball",
                    "obj:plushfox", "obj:campfire"]:
            inv.append(self._inv_item(key))
        self._make_me()
        self.save()

    def _make_me(self):
        p = self.player
        me = Av(p["first"], p["look"], p["wear"], None, p.get("title", ""))
        me.full = f"{p['first']} {p['last']}"
        me.name = p["first"]
        self.me = me
        sim = self.sims.get(p.get("sim")) or self.sims["bazaar"]
        if p.get("x") is None:
            me.x, me.z, me.yaw = sim.landing
        else:
            me.x, me.z, me.yaw = p["x"], p["z"], p.get("yaw", 0.0)
        me.sim = sim.key
        me.online = True

    def _inv_item(self, key, **data):
        it = catalog.ITEMS[key]
        self.next_id += 1
        folder = {"body": "Body Parts", "clothing": "Clothing", "accessory": "Accessories", "object": "Objects"}
        return {"id": self.next_id, "key": key, "name": it["name"], "kind": it["kind"], "folder": folder[it["kind"]],
                "data": data}

    def residents_online(self):
        return [a for a in self.people if a.online]

    def here(self):
        """Everyone in your region (you included)."""
        out = [a for a in self.people if a.online and a.sim == self.me.sim]
        return out + [self.me]

    def find(self, name):
        for a in self.people:
            if a.name.lower() == name.lower() or a.full.lower() == name.lower():
                return a
        return None

    def sim(self):
        return self.sims[self.me.sim]

    # ---- saving ----
    def save(self):
        if self.player and self.me:
            me = self.me
            self.player.update(sim=me.sim, x=me.x, z=me.z, yaw=me.yaw, look=me.look, wear=me.wear)
            _save(SAVE / "player.json", self.player)
        keep = [o for o in self.objects if o.get("owner") == "@player"]
        _save(SAVE / "world.json", {"owners": {str(k): v for k, v in self.owners.items()}, "objects": keep,
                                     "next_id": self.next_id,
                                     "resident_wear": {a.name: a.wear for a in self.people}})

    # ---- the clock ----
    def tick(self, dt):
        self.t += dt
        if self.me is None:
            return
        if self.t >= self.next_presence:
            self.next_presence = self.t + 5
            self._presence()
        for a in self.people:
            if a.online:
                self._step(a, dt)
        if self.t >= self.next_ambient:
            self.next_ambient = self.t + random.uniform(40, 110)
            self._ambient()
        if int(self.t) % 30 == 0 and int(self.t - dt) % 30 != 0:
            self._auto_return()

    def login(self):
        """You've just logged in: some people are already about."""
        n = 0
        for a in sorted(self.people, key=lambda _a: random.random()):
            if n >= 10:
                break
            if self._available(a) and random.random() < 0.6:
                self._bring_online(a, quiet=True)
                n += 1
        self._log(self.me.sim, "system", "", f"Welcome to {self.sim().name}.")
        self.next_ambient = self.t + random.uniform(12, 25)
        QTimer.singleShot(4000, self._greet)

    def _available(self, a):
        if a.contact is None:
            return True
        try:
            return available(a.contact)
        except Exception:
            return True

    def _presence(self):
        now = self.t
        count = len(self.residents_online())
        for a in self.people:
            if a.online and now >= a.session_end and not a.busy:
                self._take_offline(a)
            elif not a.online and now >= a.next_online:
                if count < MAX_ONLINE and self._available(a):
                    self._bring_online(a)
                    count += 1
                else:
                    a.next_online = now + random.uniform(60, 300)

    def _pick_sim(self, a):
        keys = list(a.haunts)
        if a.home is not None and "estates" not in keys:
            keys.append("estates")
        weights = [a.haunts.get(k, 1) for k in keys]
        return random.choices(keys, weights)[0]

    def _bring_online(self, a, quiet=False):
        a.online = True
        a.session_end = self.t + random.uniform(20, 80) * 60
        a.next_tp = self.t + random.uniform(4, 14) * 60
        self._arrive(a, self._pick_sim(a), at_landing=not quiet)
        if not quiet:
            self.notice.emit(f"{a.name} is online.")
            if a.inbox and self.brain and self.use_llm:
                text = a.inbox.pop(0)
                QTimer.singleShot(random.randint(6000, 15000), lambda: self.send_im(a.name, text, quiet=True))
            elif self.brain and random.random() < 0.08 and _llm_ready():
                QTimer.singleShot(random.randint(8000, 30000), lambda: self._say_hi_im(a))

    def _take_offline(self, a):
        self._stand(a)
        if a.sim == self.me.sim:
            self._log(a.sim, "system", "", f"{a.name} logged off.")
        a.online = False
        a.sim = None
        a.next_online = self.t + random.uniform(15, 70) * 60
        self._clear_rezzed(a)
        self.notice.emit(f"{a.name} is offline.")

    def _arrive(self, a, key, at_landing=True):
        """Teleport a resident into a region."""
        self._stand(a)
        self._clear_rezzed(a)
        a.sim = key
        s = self.sims[key]
        if at_landing:
            a.x, a.z, a.yaw = s.landing
            a.x += random.uniform(-150, 150)
            a.z += random.uniform(-150, 150)
        else:
            spot = self._spot(a, s)
            a.x, a.z = spot[0] + random.uniform(-60, 60), spot[1] + random.uniform(-60, 60)
            a.yaw = random.uniform(0, 360)
        a.y = 0.0
        a.state = "stand"
        a.next_act = self.t + random.uniform(1, 5)
        if key == self.me.sim:
            self._log(key, "system", "", f"{a.name} arrived.")

    def _spot(self, a, s):
        if s.key == "club":
            return random.choice(s.spots["dance"])
        if s.key == "bazaar":
            return random.choice(s.spots["browse"])
        if s.key == "estates":
            homes = s.spots.get("home", [])
            mine = [h for h in homes if h[0] == a.home]
            h = mine[0] if mine else random.choice(homes)
            return h[2], h[3]
        return random.choice(s.spots["build"])

    def _stand(self, a):
        if a.seat:
            self.seated.pop(a.seat, None)
        a.seat = None
        if a.state in ("sit", "dance"):
            a.state = "stand"
        a.dance = 0
        a.y = 0.0 if a.state != "fly" else a.y

    # ---- residents doing things ----
    def _step(self, a, dt):
        if a.target is not None:
            tx, tz = a.target
            dx, dz = tx - a.x, tz - a.z
            d = math.hypot(dx, dz)
            step = WALK * dt
            a.yaw = math.degrees(math.atan2(dx, dz))
            if d <= step:
                a.x, a.z = tx, tz
                a.target = None
                a.state = "stand"
                then, a.then = a.then, None
                if then:
                    then()
            else:
                a.x += dx / d * step
                a.z += dz / d * step
                a.state = "walk"
            return
        if self.t < a.next_act or a.busy:
            return
        if self.t >= a.next_tp and random.random() < 0.5:
            a.next_tp = self.t + random.uniform(5, 15) * 60
            dest = self._pick_sim(a)
            if dest != a.sim:
                if a.sim == self.me.sim:
                    self._log(a.sim, "system", "", f"{a.name} left.")
                self._arrive(a, dest)
                return
        self._decide(a)

    def _walk(self, a, x, z, then=None):
        self._stand(a)
        a.target = (x, z)
        a.then = then

    def _decide(self, a):
        s = self.sims[a.sim]
        r = random.random()
        a.next_act = self.t + random.uniform(25, 90)
        if s.key == "club":
            if r < 0.7:
                x, z, _y = random.choice(s.spots["dance"])
                a.activity = "dance"
                self._walk(a, x + random.uniform(-40, 40), z + random.uniform(-40, 40),
                           lambda: self._start_dance(a, random.randint(1, 4)))
                a.next_act = self.t + random.uniform(60, 180)
            elif r < 0.85:
                self._go_sit(a, s)
            else:
                x, z, _y = random.choice(s.spots["mingle"])
                a.activity = "mingle"
                self._walk(a, x + random.uniform(-80, 80), z + random.uniform(-80, 80))
        elif s.key == "bazaar":
            if r < 0.8:
                x, z, yaw = random.choice(s.spots["browse"])
                a.activity = "browse"
                self._walk(a, x + random.uniform(-50, 50), z + random.uniform(-50, 50),
                           lambda: self._browse(a, yaw))
            else:
                self._go_sit(a, s)
        elif s.key == "estates":
            homes = s.spots.get("home", [])
            mine = [h for h in homes if h[0] == a.home]
            h = mine[0] if (mine and r < 0.8) else random.choice(homes)
            a.activity = "home"
            seat = h[1]
            if r < 0.5 and seat not in self.seated:
                sx, sy, sz, syaw = s.seats[seat]
                self._walk(a, sx, sz + 60, lambda: self.sit(a, seat))
            else:
                self._walk(a, h[2] + random.uniform(-150, 150), h[3] + random.uniform(-80, 80))
        else:
            x, z, yaw = random.choice(s.spots["build"])
            a.activity = "build"
            self._walk(a, x + random.uniform(-100, 100), z + random.uniform(-100, 100), lambda: self._build(a))

    def _go_sit(self, a, s):
        free = [t for t in s.spots.get("sit", []) if t not in self.seated]
        if not free:
            return
        seat = random.choice(free)
        sx, sy, sz, syaw = s.seats[seat]
        a.activity = "sit"
        self._walk(a, sx + math.sin(math.radians(syaw)) * 70, sz + math.cos(math.radians(syaw)) * 70,
                   lambda: self.sit(a, seat))

    def _start_dance(self, a, style):
        self._stand(a)
        a.state = "dance"
        a.dance = style
        a.yaw = random.uniform(0, 360)

    def _browse(self, a, yaw):
        a.yaw = yaw
        if random.random() < 0.3:
            item = random.choice([i for i in catalog.ITEMS.values() if i["kind"] in ("clothing", "accessory")])
            self._dress(a, item["key"])
            if a.sim == self.me.sim and random.random() < 0.5:
                self._ambient(a, f"You just picked up a free {item['name']} at the Bazaar and put it on.")

    def _dress(self, a, key):
        slot = catalog.ITEMS[key]["slot"]
        a.wear = [w for w in a.wear if catalog.ITEMS.get(w["key"], {}).get("slot") != slot] + [{"key": key}]
        a.version += 1

    def _build(self, a):
        s = self.sims[a.sim]
        if len(a.rezzed) >= 3:
            gone = a.rezzed.pop(0)
            self.objects = [o for o in self.objects if o["id"] != gone]
        key = random.choice(["cube", "sphere", "cylinder", "cone", "crate", "barrel", "beachball", "duck", "lamp",
                             "plushfox", "chest", "snowman", "flowerpot"])
        yaw = math.radians(a.yaw)
        x = a.x + math.sin(yaw) * 160
        z = a.z + math.cos(yaw) * 160
        x0, z0, x1, z1 = s.build_area
        x, z = min(max(x, x0 + 60), x1 - 60), min(max(z, z0 + 60), z1 - 60)
        colour = random.choice(["#E85A5A", "#5AA8E8", "#F2C230", "#6AC86A", "#B08AF0", "#F0F0F0", "#E8783A"])
        obj = self._new_object(key, a.sim, x, 10.0, z, random.uniform(0, 360), owner=a.name, colour=colour)
        a.rezzed.append(obj["id"])
        self.version += 1

    def _clear_rezzed(self, a):
        if a.rezzed:
            gone = set(a.rezzed)
            self.objects = [o for o in self.objects if o["id"] not in gone]
            a.rezzed = []
            self.version += 1

    def sit(self, a, seat):
        s = self.sims[a.sim]
        if seat not in s.seats or self.seated.get(seat) not in (None, a.name):
            return False
        self._stand(a)
        x, y, z, yaw = s.seats[seat]
        a.target = None
        a.x, a.y, a.z, a.yaw = x, y, z, yaw
        a.state = "sit"
        a.seat = seat
        self.seated[seat] = a.name
        return True

    # ---- talking ----
    def _log(self, sim, kind, who, text):
        if sim not in self.logs:
            return
        if kind == "say":
            self.logs[sim].append(f"{who}: {text}")
        elif kind == "emote":
            self.logs[sim].append(f"{who} {text}")
        if self.me and sim == self.me.sim:
            self.chat.emit(kind, who, text)

    def _near(self, a, r=NEAR):
        return [o for o in self.people if o.online and o.sim == a.sim and o is not a
                and math.hypot(o.x - a.x, o.z - a.z) < r]

    def _doing(self, a):
        return {"dance": "dancing on the dance floor", "browse": "browsing the free stalls at the Bazaar",
                "home": "hanging out at home", "build": "building things in the sandbox",
                "sit": "sitting and chatting", "mingle": "hanging out"}.get(a.activity, "hanging out")

    def _perform(self, a, action):
        if action is None or not a.online:
            return
        kind, text = action
        text = text.strip()
        if not text:
            return
        if kind == "pose":
            self._log(a.sim, "emote", a.name, text)
        else:
            self._log(a.sim, "say", a.name, text)

    def _ask(self, a, nudge, priority=0, fallback=None):
        """Have a resident say or do something in local chat (the model if it's there, else a plain line)."""
        if a.busy:
            return
        if not (self.brain and _llm_ready()):
            if fallback:
                line = random.choice(fallback)
                a.typing = True

                def plain():
                    a.typing = False
                    self._perform(a, parse_action(line, a.name))
                QTimer.singleShot(random.randint(1500, 4000), plain)
            return
        a.busy = True
        a.typing = priority > 0
        others = [o.name for o in self._near(a)]
        if self.me.sim == a.sim and math.hypot(self.me.x - a.x, self.me.z - a.z) < NEAR:
            others.append(self.player_name)

        def done(action):
            a.busy = False
            a.typing = False
            self._perform(a, action)
        self.brain.act(a, self.sims[a.sim], others, self._doing(a), list(self.logs[a.sim]), nudge, done, priority)

    def _ambient(self, a=None, nudge=None):
        """Now and then someone near you says something."""
        me = self.me
        near = [o for o in self.people if o.online and o.sim == me.sim and not o.busy
                and math.hypot(o.x - me.x, o.z - me.z) < NEAR]
        if not near:
            return
        a = a or random.choice(near)
        nudge = nudge or "Say or do something that fits what's going on, or PASS."
        self._ask(a, nudge, 0, LINES.get(a.activity, LINES["mingle"]))

    def _greet(self):
        me = self.me
        near = [o for o in self.people if o.online and o.sim == me.sim and math.hypot(o.x - me.x, o.z - me.z) < 4000]
        if near and random.random() < 0.7:
            a = random.choice(near)
            self._ask(a, f"{self.player_name} just arrived nearby. Greet them if you like, or PASS.", 5,
                      [g.format(p=me.name) for g in GREET])

    def say(self, text):
        """You said something in local chat."""
        text = text.strip()
        if not text:
            return
        me = self.me
        if text.startswith("/me ") or text.startswith(":"):
            self._log(me.sim, "emote", me.name, text.split(" ", 1)[1] if text.startswith("/me ") else text[1:])
        else:
            self._log(me.sim, "say", me.name, text)
        near = [o for o in self.people if o.online and o.sim == me.sim and math.hypot(o.x - me.x, o.z - me.z)
                < CHAT_RANGE * 1.5]
        if not near:
            return
        named = [o for o in near if mentions(o.name, text, prefix=True)]
        answer = named[:2] or ([random.choice(near)] if random.random() < 0.75 else [])
        for k, a in enumerate(answer):
            nudge = (f"{self.player_name} just said that in local chat" + (" - to you" if a in named else "") +
                     ". Answer them, or PASS.")
            QTimer.singleShot(400 + k * 2500, lambda a=a, nudge=nudge: self._ask(a, nudge, 5, REPLY))

    def send_im(self, name, text, quiet=False):
        a = self.find(name)
        if a is None:
            return
        if not quiet:
            self.im.emit(a.name, text, True)
        if not a.online:
            a.inbox.append(text)
            self.im.emit(a.name, f"{a.name} is offline. They'll see your message when they log in.", False)
            return
        if not (self.brain and _llm_ready()):
            QTimer.singleShot(random.randint(3000, 7000),
                              lambda: self.im.emit(a.name, random.choice(["hey! :3", "hiya!", "*waves*", "hehe",
                                                                           "omg hi"]), False))
            return
        a.busy = True

        def done(line):
            a.busy = False
            if line:
                self.im.emit(a.name, line, False)
        self.brain.im(a, text, done)

    def _say_hi_im(self, a):
        """A friend who's just logged in sometimes IMs you first."""
        if not a.online or not self.brain or a.busy:
            return
        a.busy = True
        nudge = (f"[You just logged into Second Life and saw {self.player_name} is online too. Send them a short "
                 "IM, or PASS.]")
        messages = [{"role": "system", "content": self.brain._system(a, IM.format(player=self.player_name))},
                    {"role": "user", "content": nudge}]

        def done(text, err):
            a.busy = False
            line = None if err else _clean(text, a.name).strip('"')
            if line and not line.upper().startswith("PASS"):
                a.page_history.append({"role": "assistant", "content": line})
                self.im.emit(a.name, line, False)
        self.brain.llm.chat(self.brain._model(a), messages, self.brain._options(a), done, 5, think=False)

    # ---- you ----
    def teleport(self, key):
        me = self.me
        if key not in self.sims or key == me.sim:
            return
        self._stand(me)
        me.state = "stand"
        me.sim = key
        me.x, me.z, me.yaw = self.sims[key].landing
        me.y = 0.0
        self._log(key, "system", "", f"Teleported to {self.sims[key].name}.")
        QTimer.singleShot(3000, self._greet)
        self.next_ambient = self.t + random.uniform(15, 30)
        self.save()

    def me_sit(self, seat):
        return self.sit(self.me, seat)

    def me_stand(self):
        self._stand(self.me)
        self.me.state = "stand"

    def me_dance(self, style):
        self._start_dance(self.me, style)

    # ---- inventory and wearing ----
    def inventory(self):
        return self.player["inventory"]

    def take(self, key):
        """A freebie into your inventory."""
        it = self._inv_item(key)
        self.inventory().append(it)
        self.save()
        return it

    def item(self, iid):
        return next((i for i in self.inventory() if i["id"] == iid), None)

    def wear(self, it):
        me = self.me
        kind = it["kind"]
        if kind == "body":
            me.look = copy.deepcopy(it["data"].get("spec") or catalog.ITEMS[it["key"]]["spec"])
            me.species = me.look.get("species", "furry")
        elif kind in ("clothing", "accessory"):
            slot = catalog.ITEMS[it["key"]]["slot"]
            me.wear = [w for w in me.wear if catalog.ITEMS.get(w["key"], {}).get("slot") != slot]
            me.wear.append({"key": it["key"], "colour": it["data"].get("colour")})
        elif kind == "outfit":
            me.look = copy.deepcopy(it["data"]["spec"])
            me.wear = copy.deepcopy(it["data"]["wear"])
        me.version += 1
        self.save()

    def take_off(self, slot):
        me = self.me
        me.wear = [w for w in me.wear if catalog.ITEMS.get(w["key"], {}).get("slot") != slot]
        me.version += 1
        self.save()

    def wearing(self, it):
        if it["kind"] in ("clothing", "accessory"):
            return any(w["key"] == it["key"] for w in self.me.wear)
        return False

    def save_outfit(self, name):
        self.next_id += 1
        it = {"id": self.next_id, "key": None, "name": name, "kind": "outfit", "folder": "Outfits",
              "data": {"spec": copy.deepcopy(self.me.look), "wear": copy.deepcopy(self.me.wear)}}
        self.inventory().append(it)
        self.save()
        return it

    def save_body(self, name):
        self.next_id += 1
        it = {"id": self.next_id, "key": None, "name": name, "kind": "body", "folder": "Body Parts",
              "data": {"spec": copy.deepcopy(self.me.look)}}
        self.inventory().append(it)
        self.save()
        return it

    def delete_item(self, it):
        if it in self.inventory():
            self.inventory().remove(it)
            self.save()

    def rename_item(self, it, name):
        it["name"] = name
        self.save()

    # ---- land ----
    def my_parcel(self):
        return next((n for n, who in self.owners.items() if who == "@player"), None)

    def claim(self, n):
        if self.owners.get(n):
            return "Somebody already owns this land."
        if self.my_parcel() is not None:
            return "You already own a lot here - abandon it first."
        self.owners[n] = "@player"
        self._rebuild_estates()
        return None

    def abandon(self):
        n = self.my_parcel()
        if n is None:
            return
        del self.owners[n]
        x0, z0, x1, z1 = self._parcel_rect(n)
        back = [o for o in self.objects if o["sim"] == "estates" and o.get("owner") == "@player"
                and x0 <= o["x"] <= x1 and z0 <= o["z"] <= z1]
        for o in back:
            self._return(o)
        self._rebuild_estates()

    def _parcel_rect(self, n):
        return sims.parcel_rect(n)

    def parcel_at(self, x, z):
        for p in self.sims["estates"].parcels:
            if p["x0"] <= x <= p["x1"] and p["z0"] <= z <= p["z1"]:
                return p["n"]
        return None

    def _rebuild_estates(self):
        self.sims["estates"] = sims.estates(self._owner_names())
        self.seated = {k: v for k, v in self.seated.items() if not k.startswith("seat:estates")}
        self.version += 1
        self.save()
        self.land_changed.emit()

    def owner_label(self, n):
        who = self.owners.get(n)
        if who == "@player":
            return self.player_name
        return who

    # ---- building ----
    def can_build(self, x, z):
        me = self.me
        s = self.sims[me.sim]
        if s.build_area:
            x0, z0, x1, z1 = s.build_area
            if x0 <= x <= x1 and z0 <= z <= z1:
                return True, None
            return False, "You can only build on the deck here."
        if me.sim == "estates":
            n = self.parcel_at(x, z)
            if n is not None and self.owners.get(n) == "@player":
                return True, None
            return False, "You can only build on land you own."
        return False, "Building isn't allowed in this region."

    def _new_object(self, key, sim, x, y, z, yaw, owner="@player", colour=None, text=None, scale=1.0):
        self.next_id += 1
        o = {"id": self.next_id, "obj": key, "name": catalog.OBJECTS[key][0], "sim": sim, "x": x, "y": y, "z": z,
             "yaw": yaw, "scale": scale, "owner": owner, "colour": colour, "text": text, "hover": None,
             "rezzed": time.time()}
        self.objects.append(o)
        return o

    def rez(self, it, x=None, z=None):
        """Rez an object from your inventory in front of you (or at x, z)."""
        me = self.me
        if x is None:
            a = math.radians(me.yaw)
            x, z = me.x + math.sin(a) * 200, me.z + math.cos(a) * 200
        ok, why = self.can_build(x, z)
        if not ok:
            return None, why
        d = it["data"]
        key = d.get("obj") or catalog.ITEMS[it["key"]]["obj"]
        y = 10.0 if self.sims[me.sim].build_area else 0.0
        o = self._new_object(key, me.sim, x, y, z, me.yaw + 180, colour=d.get("colour"), text=d.get("text"),
                             scale=d.get("scale", 1.0))
        o["name"] = it["name"]
        self.version += 1
        self.save()
        return o, None

    def obj(self, oid):
        return next((o for o in self.objects if o["id"] == oid), None)

    def edit(self, o, **changes):
        o.update(changes)
        o["edits"] = o.get("edits", 0) + 1
        self.version += 1
        self.save()

    def take_object(self, o):
        """Pick an object back up into your inventory."""
        self.next_id += 1
        it = {"id": self.next_id, "key": f"obj:{o['obj']}", "name": o["name"], "kind": "object", "folder": "Objects",
              "data": {"obj": o["obj"], "colour": o.get("colour"), "text": o.get("text"), "scale": o.get("scale", 1)}}
        self.inventory().append(it)
        self.delete_object(o)
        return it

    def copy_object(self, o):
        n = self._new_object(o["obj"], o["sim"], o["x"] + 60, o["y"], o["z"] + 60, o["yaw"], colour=o.get("colour"),
                             text=o.get("text"), scale=o.get("scale", 1.0))
        n["name"] = o["name"]
        self.version += 1
        self.save()
        return n

    def delete_object(self, o):
        if o in self.objects:
            self.objects.remove(o)
            self.version += 1
            self.save()

    def _return(self, o):
        self.next_id += 1
        self.inventory().append({"id": self.next_id, "key": f"obj:{o['obj']}", "name": o["name"], "kind": "object",
                                 "folder": "Lost and Found", "data": {"obj": o["obj"], "colour": o.get("colour"),
                                                                       "text": o.get("text"),
                                                                       "scale": o.get("scale", 1)}})
        if o in self.objects:
            self.objects.remove(o)
        self.version += 1

    def _auto_return(self):
        """The sandbox sends your things home after two hours."""
        cutoff = time.time() - RETURN_HOURS * 3600
        old = [o for o in self.objects if o["sim"] == "sandbox" and o.get("owner") == "@player"
               and o.get("rezzed", 0) < cutoff]
        for o in old:
            self._return(o)
        if old:
            self.notice.emit(f"{len(old)} of your sandbox objects were returned to your Lost and Found folder.")
            self.save()

    # ---- profiles ----
    def profile(self, name):
        if self.me and name in (self.me.name, self.me.full):
            from ... import timeline
            codes = timeline.user_codes() or {}
            p = timeline.profile() or {}
            pic = p.get("picture")
            return {"name": self.me.name, "full": self.me.full, "born": self.player.get("created", ""),
                    "about": self.player.get("about", ""), "species": self.me.look.get("species", ""), "look": "",
                    "interests": "", "pronouns": "", "partner": "", "furcode": codes.get("furcode", ""),
                    "yiffcode": codes.get("yiffcode", ""), "picture": pic, "me": True}
        a = self.find(name)
        icon = a.contact.icon if a and a.contact else None
        p = residents.profile(a.name if a else name, icon)
        if a:
            p["title"] = a.title
            p["online"] = a.online
            p["where"] = self.sims[a.sim].name if a.online and a.sim else ""
            if a.home is not None:
                p["home"] = a.home
        return p

    def set_about(self, text):
        self.player["about"] = text
        self.save()
