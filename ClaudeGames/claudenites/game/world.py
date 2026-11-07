"""The game as it runs: where Claude is (Thornwick or a floor of the Deep), what's alive there, the bolts in the air,
and the rules of the run. No drawing and no Qt: the window feeds it input and draws what it holds; the tests drive it
the same way.

    g = Game.new(slot)                     a fresh Claude, in Thornwick
    g.step(dt, inp)                        advance; inp is an Input (move, look, fire, jump)
    g.events                               what happened since last asked (drained by the window): toasts, hits...
    g.interact()                           F: talk to whoever's near, or take the stairs / the Deep's mouth
"""
import math
import random
from collections import deque

from . import data as D
from . import items as I
from . import levels
from .player import Player
from .sky import Sky

EYE = 0.62
RADIUS = 0.24
GRAVITY = 16.0
JUMP = 5.2
RUN = 1.65                     # how much faster he runs (Shift)
RUN_JUMP = 1.3                 # and how much higher a running jump goes


class Input:
    def __init__(self):
        self.forward = 0.0       # -1..1
        self.strafe = 0.0        # -1..1 (right positive)
        self.fire = False
        self.jump = False
        self.run = False         # (Shift: faster, and a higher, longer jump)
        self.yaw = 0.0
        self.pitch = 0.0


class Monster:
    _n = 0

    def __init__(self, name, x, z, depth, rng, guardian=False):
        Monster._n += 1
        self.id = Monster._n
        self.name = name
        self.d = D.MONSTERS[name]
        k = I.depth_scale(depth)
        self.max_hp = self.hp = self.d["hp"] * k * (1.0 if guardian else rng.uniform(0.9, 1.1))
        self.dmg = self.d["dmg"] * (0.5 + 0.5 * k)
        self.speed = self.d["speed"]
        self.kind = self.d["kind"]
        self.element = self.d["element"]
        self.xp = int(self.d["xp"] * (0.6 + 0.4 * k) * (8 if guardian else 1))
        self.x, self.z = x, z
        self.y = 0.0
        self.yaw = rng.uniform(0, math.tau)
        self.size = self.d.get("size", 1.0)
        self.radius = 0.28 * self.size
        self.height = 0.8 * self.size
        self.guardian = guardian
        self.awake = False
        self.cool = rng.uniform(0.5, 1.5)
        self.strike = -1.0                   # seconds into a strike (the blow lands at STRIKE_AT)
        self.dead = False
        self.dead_time = 0.0
        self.hit_flash = 0.0
        self.status = {}                     # "burn": (dps, left), "chill": left, "venom": [(dps, left)...]
        self.moving = False
        self.anim = {}                       # the renderer's: its clip player state
        self.wander = 0.0
        self.lift = 0.0

    @property
    def centre_y(self):
        return self.y + self.lift + self.height * 0.5


class Bolt:
    __slots__ = ("x", "y", "z", "vx", "vy", "vz", "dmg", "element", "life", "homing", "bounce", "pierce", "hit",
                 "foe", "radius", "trail")

    def __init__(self, x, y, z, vx, vy, vz, dmg, element, foe=False):
        self.x, self.y, self.z, self.vx, self.vy, self.vz = x, y, z, vx, vy, vz
        self.dmg, self.element, self.foe = dmg, element, foe
        self.life = 2.6 if not foe else 4.0
        self.homing = 0.0
        self.bounce = 0
        self.pierce = 0
        self.hit = set()
        self.radius = 0.07 if not foe else 0.12
        self.trail = 0.0


STRIKE_AT = 0.35
STRIKE_LEN = 0.8


class Game:
    def __init__(self, player, seed, slot=0):
        self.player = player
        self.seed = seed
        self.slot = slot
        self.run_floor = 1                   # where the Deep's mouth takes him: the floor the run has reached
        self.depth = 0                       # 0: Thornwick
        self.level = None
        self.monsters = []
        self.bolts = []
        self.events = []
        self.fx = []                         # short-lived sparks: {"x","y","z","c","t","kind"}
        self.drops = []                      # what was had, flying to him: {"x","y","z","vx","vy","vz","t","what"}
        self.x = self.z = 0.0
        self.y = 0.0
        self.vy = 0.0
        self.yaw = self.pitch = 0.0
        self.time = 0.0
        self.cool = 0.0
        self.hurt = 0.0                      # the red at the screen's edge
        self.dead = False
        self.dialog = None                   # what the window should show: ("vendor", key) / ("stairs",) / ("mouth",)
        self.rng = random.Random(seed)
        self._flow = None
        self._flow_at = None
        self.guardian_down = False
        self.regen_block = 0.0
        self.heal_over = 0.0
        self.visits = 0                      # times home: the vendors' stock changes each
        self.sky = Sky(seed)                 # the clock, the moon and the weather (game/sky.py)
        self.wx = self.sky.effects(True, 0)
        self.storm_hit = 0.0

    # ---- making one ---------------------------------------------------------------------------------------------
    @classmethod
    def new(cls, slot=0, seed=None):
        seed = seed if seed is not None else random.randrange(1 << 30)
        g = cls(Player(), seed, slot)
        g.go_town()
        return g

    def to_json(self):
        return {"version": 1, "seed": self.seed, "run_floor": self.run_floor, "visits": self.visits,
                "sky": self.sky.to_json(),
                "player": self.player.to_json()}

    @classmethod
    def from_json(cls, d, slot=0):
        g = cls(Player.from_json(d.get("player", {})), d.get("seed", 1), slot)
        g.run_floor = max(1, int(d.get("run_floor", 1)))
        g.visits = int(d.get("visits", 0))
        g.sky = Sky.from_json(g.seed, d.get("sky"))
        g.go_town()
        return g

    # ---- places ------------------------------------------------------------------------------------------------
    def _enter(self, level):
        self.level = level
        self.monsters = []
        self.bolts = []
        self.fx = []
        self.drops = []
        self.x, self.z, self.yaw = level.start
        self.y = level.floor_at(self.x, self.z)
        self.vy = 0.0
        self.pitch = 0.0
        self._flow = None
        self.dialog = None
        self.guardian_down = False
        self.pieces_seen = set()
        rng = random.Random(f"{self.seed}:spawns:{level.depth}:{self.visits}")
        strength = level.depth or max(1, min(60, self.player.level))        # (the forest's creatures: as strong as he is)
        night = level.outdoor and self.sky.night
        for s in level.spawns:
            m = Monster(s["monster"], s["x"], s["z"], strength, rng, s.get("guardian", False))
            m.home = (s["x"], s["z"])
            if night:                                                   # (the wood by night is fiercer)
                m.dmg *= 1.15
                m.speed *= 1.05
            m.y = level.floor_at(m.x, m.z)
            if m.kind == "flyer":
                m.lift = 0.35
            self.monsters.append(m)
        self.events.append(("level", level))

    def go_town(self):
        self.visits += 1
        self.depth = 0
        self._enter(levels.town(self.seed))

    def go_floor(self, n):
        n = max(1, min(D.FLOORS, n))
        self.depth = n
        # a floor is the same floor each time the run reaches it, and a new one each run (the run counts deaths)
        L = levels.dungeon(n, f"{self.seed}:{self.player.stats['deaths']}")
        self._enter(L)
        p = self.player
        p.stats["deepest"] = max(p.stats["deepest"], n)
        self.events.append(("toast", f"Floor {n}: {L.name}", (0.9, 0.85, 0.7)))
        if L.guardian:
            self.events.append(("toast", f"{L.guardian} waits on this floor.", (1.0, 0.5, 0.4)))

    def descend(self):
        """Down the stairs (the run reaches the next floor; the stairs take an hour)."""
        if self.depth >= D.FLOORS:
            return
        self._sky_events(self.sky.tick(60))
        self.run_floor = max(self.run_floor, self.depth + 1)
        self.go_floor(self.depth + 1)

    def stairs_home(self):
        """Up and home from the stairs: the run waits at the next floor down."""
        self.run_floor = max(self.run_floor, min(D.FLOORS, self.depth + 1))
        self.go_town()
        self.events.append(("toast", f"Home to {D.TOWN_NAME}. The way down waits at floor {self.run_floor}.", (0.8, 0.9, 1.0)))
        self.events.append(("save",))

    def read_return(self):
        p = self.player
        if self.depth == 0 or p.potions.get("return", 0) <= 0:
            return False
        p.potions["return"] -= 1
        self.run_floor = max(self.run_floor, self.depth)
        self.go_town()
        self.events.append(("toast", f"The scroll folds the Deep away. Floor {self.run_floor} waits.", (0.8, 0.9, 1.0)))
        self.events.append(("save",))
        return True

    def in_town(self):
        S = self.level.safe
        return S is not None and bool(S[min(S.shape[0] - 1, max(0, int(self.z))), min(S.shape[1] - 1, max(0, int(self.x)))])

    def die(self):
        p = self.player
        if self.depth == 0:                                  # (fallen in the forest: home, and the Deep is as it was)
            self.go_town()
            p.life, p.mana = p.max_life(), p.max_mana()
            self.dead = False
            self.events.append(("toast", "Claude wakes in the clearing, bruised. The forest lets him go, this time.",
                                (1.0, 0.7, 0.5)))
            self.events.append(("save",))
            return
        p.stats["deaths"] += 1
        self.events.append(("died", self.depth))
        self.run_floor = 1
        self.go_town()
        p.life, p.mana = p.max_life(), p.max_mana()
        self.dead = False
        self.events.append(("toast", "Claude wakes in the clearing. The Deep has closed behind him: it starts again at floor 1.",
                            (1.0, 0.6, 0.5)))
        self.events.append(("save",))

    # ---- near things --------------------------------------------------------------------------------------------
    def near(self):
        """What F would do here: ("vendor", key) / ("stairs",) / ("mouth",) / None, and its label."""
        L = self.level
        for n in L.npcs:
            if math.hypot(n["x"] - self.x, n["z"] - self.z) < 1.7:
                v = D.VENDORS[n["vendor"]]
                return ("vendor", n["vendor"]), f"Talk to {v['name']}, {v['title']}"
        if self.depth == 0 and L.portal and math.hypot(L.portal[0] - self.x, L.portal[1] - self.z) < 2.0:
            return ("mouth",), "Go down into the Deep"
        for i, c in enumerate(L.chests):
            if not c["opened"] and math.hypot(c["x"] - self.x, c["z"] - self.z) < 1.3:
                return ("chest", i), "Open the chest"
        if self.depth and L.stairs and math.hypot(L.stairs[0] - self.x, L.stairs[1] - self.z) < 1.4:
            if L.guardian and not self.guardian_down:
                return ("sealed",), f"The stairs are sealed while {L.guardian} lives"
            return ("stairs",), "Take the stairs"
        return None, ""

    def interact(self):
        what, _label = self.near()
        if what and what[0] == "chest":
            self.open_chest(what[1])
        elif what and what[0] != "sealed":
            self.dialog = what
        return what

    def open_chest(self, i):
        """Its gold and its things straight into the pack - and whatever was set to guard it, up and about."""
        c = self.level.chests[i]
        if c["opened"]:
            return
        c["opened"] = True
        mark = len(self.events)
        p, rng, depth = self.player, self.rng, max(1, self.depth)
        find = p.bonus().get("find", 0)
        gold = int(I.gold_for(depth, rng, find) * 5 * c.get("rich", 1.0))
        p.gold += gold
        got = [f"+{gold} gold"]
        for _ in range(1 + (1 if c.get("rich", 1) > 1.2 or rng.random() < 0.3 else 0)):
            it = I.roll_item(rng, depth + 1, find / 300)
            kept = p.give(it)
            got.append(I.item_name(it) if kept else f"{I.item_name(it)} (pack full: sold)")
            self.events.append(("found", it))
        if rng.random() < 0.35:
            k = rng.choice(["health", "mana"])
            p.potions[k] += 1
            got.append("a Health Potion" if k == "health" else "a Mana Potion")
        self.events.append(("loot", (c["x"], c["y"] + 0.6, c["z"]), got))
        self._drops((c["x"], c["y"] + 0.5, c["z"]), got, mark, c["y"])
        self.events.append(("chest", c))
        srng = random.Random(f"{self.seed}:guard:{depth}:{i}")
        for k, name in enumerate(c.get("guard") or []):
            a = k / max(1, len(c["guard"])) * math.tau
            x, z = c["x"] + math.cos(a) * 1.2, c["z"] + math.sin(a) * 1.2
            if not self.level.can_stand(x, z, 0.2, c["y"]):
                x, z = c["x"], c["z"] + 0.9
            m = Monster(name, x, z, depth, srng)
            m.y = self.level.floor_at(x, z)
            m.awake = True
            self.monsters.append(m)
        if c.get("guard"):
            self.events.append(("toast", "The chest was not unguarded.", (1.0, 0.6, 0.45)))

    # ---- the step ----------------------------------------------------------------------------------------------
    def step(self, dt, inp):
        dt = min(dt, 0.05)
        self.time += dt
        if self.dialog:
            return
        p = self.player
        self.yaw, self.pitch = inp.yaw, max(-1.45, min(1.45, inp.pitch))
        self._sky_events(self.sky.tick(dt))                # (a second of play is a minute of the game's day)
        self.wx = self.sky.effects(self.level.outdoor, self.depth)
        self._weather(dt)
        self._move(dt, inp)
        self._places()
        # mana and life come back
        p.mana = min(p.max_mana(), p.mana + p.mana_regen() * dt)
        if self.heal_over > 0:
            amt = min(self.heal_over, p.max_life() * 0.2 * dt)
            p.life = min(p.max_life(), p.life + amt)
            self.heal_over -= amt
        if self.depth == 0 and self.in_town():
            p.life = min(p.max_life(), p.life + p.max_life() * 0.25 * dt)      # (home: he mends)
        self.hurt = max(0.0, self.hurt - dt * 1.5)
        # the wand
        self.cool -= dt
        if inp.fire and self.cool <= 0 and (self.depth > 0 or not self.in_town()):
            self._fire()
        self._bolts(dt)
        self._monsters(dt)
        self.fx = [f for f in self.fx if self.time - f["t"] < f.get("life", 0.5)]
        self._fly_drops(dt)
        for f in self.fx:                                        # (splinters fly and fall)
            if f.get("kind") == "debris":
                f["vy"] -= GRAVITY * dt
                f["x"] += f["vx"] * dt
                f["z"] += f["vz"] * dt
                f["y"] += f["vy"] * dt
                if f["y"] < f["floor"] + 0.03:
                    f["y"] = f["floor"] + 0.03
                    f["vy"] = -f["vy"] * 0.3
                    f["vx"] *= 0.5
                    f["vz"] *= 0.5
        if p.life <= 0 and not self.dead:
            self.dead = True
            self.die()

    # ---- the sky -------------------------------------------------------------------------------------------------
    WEATHER_LINES = {
        "rain": ("The rain comes on.", "Above, the rain has come on: water runs down the walls."),
        "storm": ("A storm breaks over the wood.", "Thunder, far above: a storm has broken over Thornwick."),
        "mist": ("A mist comes up between the trees.", None), "wind": ("The wind gets up.", "A draft moans up the stairs."),
        "snow": ("Snow begins to fall.", None), "heat": ("The heat lies heavy on the clearing.", None),
        "aurora": ("Lights hang in the northern sky.", None),
        "tornado": ("A twister is coming through the wood!", "The whole Deep shudders: something is tearing at the town above."),
        "cloud": ("Cloud comes over.", None), "clear": ("The sky clears.", None),
    }

    def _sky_events(self, said):
        for kind, what in said:
            if kind == "weather":
                up, down = self.WEATHER_LINES.get(what, (None, None))
                line = up if self.level is None or self.level.outdoor else (down if self.depth <= 10 else None)
                if line:
                    self.events.append(("toast", line, (0.75, 0.85, 1.0)))
                self.events.append(("weather", what))
            elif kind == "flood" and self.depth in range(1, 4):
                self.events.append(("toast", "Water comes down the stairs in a sheet: the storm above is flooding the low halls."
                                    if what else "The last of the floodwater drains away down the cracks.", (0.6, 0.8, 1.0)))

    def flooded(self, cx, cy):
        """A sunken square of the first floors standing in a storm's floodwater."""
        L = self.level
        return self.wx.get("flood", 0) > 0 and L.open_at(cx, cy) and L.floor[cy, cx] < -0.1

    def _weather(self, dt):
        """Lightning in a storm; a tornado crossing the wood."""
        L = self.level
        if not L.outdoor:
            above = self.sky.now()
            if above["kind"] == "storm" and 1 <= self.depth <= 10 and self.rng.random() < 0.05 * above["strength"] * dt:
                self.events.append(("lightning_below", 1 - (self.depth - 1) / 10))
            return
        if self.wx["lightning"] and not self.in_town() and self.rng.random() < self.wx["lightning"] * dt * 3:
            a = self.rng.uniform(0, math.tau)
            d = self.rng.uniform(1.5, 9)
            x, z = self.x + math.cos(a) * d, self.z + math.sin(a) * d
            self.events.append(("lightning", (x, L.floor_at(x, z), z)))
            if d < 2.5:
                self._hurt_player(self.player.max_life() * 0.18, "storm")
                self.events.append(("toast", "Lightning! The air smells of it.", (1.0, 1.0, 0.6)))
            for m in self.monsters:
                if not m.dead and (m.x - x) ** 2 + (m.z - z) ** 2 < 4:
                    self._hit(m, m.max_hp * 0.4, "storm", chained=True)
        tw = self.sky.twister(L.w)
        if tw:
            tx, tz, k = tw
            for who in [self] + [m for m in self.monsters if not m.dead]:
                dx, dz = who.x - tx, who.z - tz
                d = math.hypot(dx, dz)
                if d < 3.2 * max(0.4, k):
                    # (round and away: the wind flings it)
                    push = (3.2 - d) * 1.6 * dt
                    nx, nz = who.x + (-dz / max(d, 0.1) + dx / max(d, 0.1) * 0.6) * push, who.z + (dx / max(d, 0.1) + dz / max(d, 0.1) * 0.6) * push
                    if L.can_stand(nx, nz, 0.24, getattr(who, "y", 0.0)):
                        who.x, who.z = nx, nz
                    if who is self and not self.in_town():
                        self._hurt_player(self.player.max_life() * 0.06 * dt, "storm")
                    elif who is not self:
                        who.hp -= who.max_hp * 0.08 * dt
                        if who.hp <= 0:
                            self._kill(who)

    def _places(self):
        """Stepping into a set piece (its line, once), onto a floor of coin, into water."""
        L = self.level
        cx, cy = int(self.x), int(self.z)
        for k, pc in enumerate(L.pieces):
            if k not in self.pieces_seen and pc["x0"] <= cx <= pc["x1"] and pc["y0"] <= cy <= pc["y1"]:
                self.pieces_seen.add(k)
                name = pc["name"][0].upper() + pc["name"][1:]
                self.events.append(("piece", name, pc["line"]))
        for pk in list(L.pickups):
            if (pk["x"] - self.x) ** 2 + (pk["z"] - self.z) ** 2 < 0.55 ** 2 and abs(pk["y"] - self.y) < 0.8:
                L.pickups.remove(pk)
                self._take(pk)
        if (cx, cy) in L.gold_squares:
            L.gold_squares.discard((cx, cy))
            n = max(1, I.gold_for(max(1, self.depth), self.rng) // 2)
            self.player.gold += n
            self.events.append(("loot", (self.x, self.y + 0.3, self.z), [f"+{n} gold"]))

    def _take(self, pk):
        p, rng, depth = self.player, self.rng, max(1, self.depth)
        k = pk["kind"]
        if k == "gold":
            n = I.gold_for(depth, rng, p.bonus().get("find", 0)) * rng.randint(2, 4)
            p.gold += n
            got = [f"+{n} gold"]
        elif k in ("health", "mana"):
            p.potions[k] += 1
            got = ["a Health Potion" if k == "health" else "a Mana Potion"]
        elif k == "scroll":
            p.potions["return"] += 1
            got = ["a Scroll of Return"]
        else:
            it = I.roll_item(rng, depth + 1, p.bonus().get("find", 0) / 400)
            kept = p.give(it)
            got = [I.item_name(it) if kept else f"{I.item_name(it)} (pack full: sold)"]
            self.events.append(("found", it))
        self.events.append(("loot", (pk["x"], pk["y"] + 0.4, pk["z"]), got))
        self.events.append(("pickup", k))

    def _move(self, dt, inp):
        p, L = self.player, self.level
        fwd = (math.sin(self.yaw), -math.cos(self.yaw))
        right = (math.cos(self.yaw), math.sin(self.yaw))
        mx = fwd[0] * inp.forward + right[0] * inp.strafe
        mz = fwd[1] * inp.forward + right[1] * inp.strafe
        ln = math.hypot(mx, mz)
        if ln > 1:
            mx, mz = mx / ln, mz / ln
        here = (int(self.x), int(self.z))
        on_ground0 = self.y <= L.floor_at(self.x, self.z) + 0.02
        running = inp.run and inp.forward > 0
        if on_ground0:
            self.leap = 1.0                                  # (the boost of a running jump lasts while he's in the air)
        sp = p.speed() * (0.6 if here in L.water or self.flooded(*here) else 1.0) * self.wx.get("speed", 1.0)
        sp *= (RUN if running else 1.0) * getattr(self, "leap", 1.0)
        self.running = running
        step_x, step_z = mx * sp * dt, mz * sp * dt
        foot = self.y
        if L.can_stand(self.x + step_x, self.z, RADIUS, foot):
            self.x += step_x
        if L.can_stand(self.x, self.z + step_z, RADIUS, foot):
            self.z += step_z
        ground = L.floor_at(self.x, self.z)
        on_ground = self.y <= ground + 0.02
        if inp.jump and on_ground:
            self.vy = JUMP * (RUN_JUMP if self.running else 1.0)
            if self.running:
                self.leap = 1.18                             # (and he carries further)
            self.events.append(("jump", self.running))
            inp.jump = False
        self.vy -= GRAVITY * dt
        self.y += self.vy * dt
        if self.y <= ground:
            if ground - self.y < levels.STEP + 0.05:
                self.y = ground
            self.vy = 0.0
        head = L.ceil_at(self.x, self.z)
        if self.y + EYE + 0.08 > head:
            self.y = head - EYE - 0.08
            self.vy = min(0.0, self.vy)

    @property
    def eye(self):
        return (self.x, self.y + EYE, self.z)

    def aim(self):
        cp = math.cos(self.pitch)
        return (math.sin(self.yaw) * cp, math.sin(self.pitch), -math.cos(self.yaw) * cp)

    def _fire(self):
        p = self.player
        s = p.wand_stats()
        if s is None:
            return
        if p.mana < s["mana"]:
            self.cool = 0.25
            self.events.append(("nomana",))
            return
        p.mana -= s["mana"]
        self.cool = 1.0 / s["rate"]
        ex, ey, ez = self.eye
        right = (math.cos(self.yaw), 0, math.sin(self.yaw))
        ox, oy, oz = ex + right[0] * 0.12, ey - 0.1, ez + right[2] * 0.12     # (from the wand's tip, low and right)
        n = s["bullets"]
        spread = math.radians(s["spread"])
        for k in range(n):
            off = (k - (n - 1) / 2) / max(1, n - 1) * spread if n > 1 else self.rng.uniform(-0.5, 0.5) * spread
            yaw = self.yaw + off
            pitch = self.pitch + self.rng.uniform(-0.3, 0.3) * spread * 0.3
            cp = math.cos(pitch)
            d = (math.sin(yaw) * cp, math.sin(pitch), -math.cos(yaw) * cp)
            b = Bolt(ox, oy, oz, d[0] * s["speed"], d[1] * s["speed"], d[2] * s["speed"], s["damage"], s["element"])
            b.homing, b.bounce, b.pierce = s["homing"], s["bounce"], s["pierce"]
            self.bolts.append(b)
        self.events.append(("cast", s["element"]))

    # ---- bolts --------------------------------------------------------------------------------------------------
    def _bolts(self, dt):
        L = self.level
        keep = []
        for b in self.bolts:
            b.life -= dt
            if b.life <= 0:
                continue
            if b.homing and not b.foe:
                tgt = self._nearest_ahead(b)
                if tgt:
                    dx, dy, dz = tgt.x - b.x, tgt.centre_y - b.y, tgt.z - b.z
                    ln = math.sqrt(dx * dx + dy * dy + dz * dz) or 1
                    sp = math.sqrt(b.vx * b.vx + b.vy * b.vy + b.vz * b.vz)
                    k = min(1.0, b.homing * dt)
                    b.vx += (dx / ln * sp - b.vx) * k
                    b.vy += (dy / ln * sp - b.vy) * k
                    b.vz += (dz / ln * sp - b.vz) * k
            sp = math.sqrt(b.vx * b.vx + b.vy * b.vy + b.vz * b.vz)
            n = max(1, int(sp * dt / 0.12) + 1)
            alive = True
            for _ in range(n):
                nx, ny, nz = b.x + b.vx * dt / n, b.y + b.vy * dt / n, b.z + b.vz * dt / n
                if ny < L.floor_at(nx, nz) or ny > L.ceil_at(nx, nz):
                    if b.bounce > 0:
                        b.bounce -= 1
                        self._reflect(b, nx, ny, nz)
                        continue
                    self._spark(b.x, b.y, b.z, b.element, "impact")
                    alive = False
                    break
                b.x, b.y, b.z = nx, ny, nz
                if b.foe:
                    ex, ey, ez = self.eye
                    if (b.x - ex) ** 2 + (b.y - (ey - 0.25)) ** 2 + (b.z - ez) ** 2 < (0.32 + b.radius) ** 2:
                        self._hurt_player(b.dmg, b.element)
                        self._spark(b.x, b.y, b.z, b.element, "impact")
                        alive = False
                        break
                else:
                    if self._smash_at(b):
                        alive = False
                        break
                    for m in self.monsters:
                        if m.dead or m.id in b.hit:
                            continue
                        if (b.x - m.x) ** 2 + (b.z - m.z) ** 2 < (m.radius + b.radius) ** 2 and \
                                m.y + m.lift - 0.05 < b.y < m.y + m.lift + m.height + 0.1:
                            self._hit(m, b.dmg, b.element)
                            b.hit.add(m.id)
                            self._spark(b.x, b.y, b.z, b.element, "impact")
                            if b.pierce > 0:
                                b.pierce -= 1
                            else:
                                alive = False
                            break
                    if not alive:
                        break
            if alive:
                keep.append(b)
        self.bolts = keep

    def _smash_at(self, b):
        """A bolt meeting a barrel, a crate, a rack: it takes the blow, and enough of them break it."""
        L = self.level
        B = L.breakables()
        if not B:
            return False
        cx, cy = int(b.x), int(b.z)
        for gx in (cx - 1, cx, cx + 1):
            for gy in (cy - 1, cy, cy + 1):
                for thing, x, z, y, r, h in B.get((gx, gy), ()):
                    if (b.x - x) ** 2 + (b.z - z) ** 2 < (r + b.radius) ** 2 and y - 0.05 < b.y < y + h + 0.05:
                        thing["hurt"] = thing.get("hurt", 0) + b.dmg
                        self._spark(b.x, b.y, b.z, b.element, "impact")
                        if thing["hurt"] >= 8 + 3 * max(1, self.depth) ** 0.5:
                            self.smash(thing, x, y, z, h)
                        else:
                            self.events.append(("thud", (x, y + h * 0.5, z)))
                        return True
        return False

    def smash(self, thing, x, y, z, h):
        L = self.level
        L.smash(thing)
        name = thing.get("model") or thing.get("name")
        self.events.append(("break", (x, y, z), name, h))
        for _ in range(9):                                       # (the splinters)
            a = self.rng.uniform(0, math.tau)
            sp = self.rng.uniform(1.0, 2.6)
            self.fx.append({"x": x, "y": y + h * 0.5, "z": z, "vx": math.cos(a) * sp, "vy": self.rng.uniform(1.5, 3.5),
                            "vz": math.sin(a) * sp, "t": self.time, "life": 1.1, "kind": "debris", "c": (0.5, 0.36, 0.22),
                            "floor": y, "size": self.rng.uniform(0.05, 0.11), "pic": name})
        p, rng = self.player, self.rng
        got = []
        if rng.random() < 0.3:
            n = max(1, I.gold_for(max(1, self.depth), rng, p.bonus().get("find", 0)) // 2)
            p.gold += n
            got.append(f"+{n} gold")
        if rng.random() < 0.06:
            k = rng.choice(["health", "mana"])
            p.potions[k] += 1
            got.append("a Health Potion" if k == "health" else "a Mana Potion")
        if got:
            self.events.append(("loot", (x, y + 0.5, z), got))
            self._drops((x, y + h * 0.5, z), got, len(self.events), y)

    def _reflect(self, b, nx, ny, nz):
        L = self.level
        if ny < L.floor_at(b.x, b.z) or ny > L.ceil_at(b.x, b.z):
            b.vy = -b.vy
            return
        if L.floor_at(nx, b.z) > b.y or L.ceil_at(nx, b.z) < b.y:
            b.vx = -b.vx
        if L.floor_at(b.x, nz) > b.y or L.ceil_at(b.x, nz) < b.y:
            b.vz = -b.vz

    def _nearest_ahead(self, b):
        best, bd = None, 64.0
        for m in self.monsters:
            if m.dead:
                continue
            dx, dz = m.x - b.x, m.z - b.z
            d = dx * dx + dz * dz
            if d < bd and dx * b.vx + dz * b.vz > 0:
                best, bd = m, d
        return best

    def _spark(self, x, y, z, element, kind):
        self.fx.append({"x": x, "y": y, "z": z, "c": D.ELEMENT_COLOUR.get(element, (1, 1, 1)), "t": self.time,
                        "kind": kind, "life": 0.35})

    # ---- harm --------------------------------------------------------------------------------------------------
    def _hit(self, m, dmg, element, chained=False):
        if m.dead:
            return
        res = m.d["resist"].get(element, 0.0)
        dmg *= self.wx.get("element", {}).get(element, 1.0)               # (the weather: rain dulls fire, feeds storm)
        if element == "arcane":
            dmg *= 1.15
        dmg *= (1 - res) * self.rng.uniform(0.9, 1.1)
        crit = self.rng.random() < 0.06 + self.player.bonus().get("crit", 0) / 100
        if crit:
            dmg *= 1.8
        m.hp -= dmg
        m.hit_flash = 0.12
        m.awake = True
        if element == "fire":
            m.status["burn"] = (dmg * 0.12, 3.0)
        elif element == "frost":
            m.status["chill"] = 2.0
        elif element == "venom":
            stacks = [s for s in m.status.get("venom", []) if s[1] > 0][-4:]
            m.status["venom"] = stacks + [(dmg * 0.08, 4.0)]
        elif element == "storm" and not chained:
            other = min((o for o in self.monsters if not o.dead and o is not m),
                        key=lambda o: (o.x - m.x) ** 2 + (o.z - m.z) ** 2, default=None)
            if other and (other.x - m.x) ** 2 + (other.z - m.z) ** 2 < 9:
                self.events.append(("arc", (m.x, m.centre_y, m.z), (other.x, other.centre_y, other.z)))
                self._hit(other, dmg * 0.5, "storm", chained=True)
        leech = self.player.bonus().get("leech", 0)
        if leech:
            p = self.player
            p.life = min(p.max_life(), p.life + dmg * leech / 100)
        self.events.append(("dmg", (m.x, m.centre_y + 0.3, m.z), int(round(dmg)), element, crit))
        if m.hp <= 0:
            self._kill(m)

    def _kill(self, m):
        m.dead = True
        m.dead_time = self.time
        p = self.player
        p.stats["kills"] += 1
        gained = p.add_xp(m.xp)
        self.events.append(("kill", m))
        if gained:
            self.events.append(("toast", f"Claude is level {p.level}. A skill point to spend with Mother Wren.", (1.0, 0.9, 0.4)))
            self.events.append(("levelup", p.level))
        self._loot(m)
        if m.guardian:
            self.guardian_down = True
            if m.name not in p.stats["guardians"]:
                p.stats["guardians"].append(m.name)
            self.events.append(("toast", f"{m.name} falls. The stairs are open.", (1.0, 0.8, 0.4)))
            if self.depth >= D.FLOORS:
                self.events.append(("victory",))

    def _loot(self, m):
        """Gold always; sometimes a potion; sometimes a thing - straight into the pack (and seen going there)."""
        mark = len(self.events)
        p, rng, depth = self.player, self.rng, max(1, self.depth)
        find = p.bonus().get("find", 0)
        gold = I.gold_for(depth, rng, find) * (10 if m.guardian else 1)
        p.gold += gold
        got = [f"+{gold} gold"]
        if rng.random() < 0.10:
            p.potions["health"] += 1
            got.append("a Health Potion")
        if rng.random() < 0.08:
            p.potions["mana"] += 1
            got.append("a Mana Potion")
        if rng.random() < 0.012:
            p.potions["return"] += 1
            got.append("a Scroll of Return")
        drops = 3 if m.guardian else (1 if rng.random() < 0.12 + (0.05 if m.kind == "brute" else 0) else 0)
        for _ in range(drops):
            it = I.roll_item(rng, depth, find / 400)
            if m.guardian and it.get("type") == "gear":
                it = I.make_gear(it["slot"], it["level"], max(2, it["rarity"]), rng)
            kept = p.give(it)
            got.append(I.item_name(it) if kept else f"{I.item_name(it)} (pack full: sold)")
            self.events.append(("found", it))
        self.events.append(("loot", (m.x, m.centre_y, m.z), got))
        self._drops((m.x, m.y + m.lift + m.height * 0.6, m.z), got, mark, m.y)

    DROP_POP, DROP_HOLD, DROP_FLY = 0.75, 0.55, 0.45

    def _fly_drops(self, dt):
        """Out, down, a bounce; a moment glinting where it lies; then away to him."""
        keep = []
        ex, ey, ez = self.eye
        for d in self.drops:
            age = self.time - d["t"]
            if age < 0:
                keep.append(d)
                continue
            if age < self.DROP_POP + self.DROP_HOLD:
                d["vy"] -= GRAVITY * 0.8 * dt
                d["x"] += d["vx"] * dt
                d["z"] += d["vz"] * dt
                d["y"] += d["vy"] * dt
                if d["y"] < d["floor"] + 0.12:
                    d["y"] = d["floor"] + 0.12
                    d["vy"] = -d["vy"] * 0.35 if abs(d["vy"]) > 0.6 else 0.0
                    d["vx"] *= 0.55
                    d["vz"] *= 0.55
                if not self.level.can_stand(d["x"], d["z"], 0.05, d["floor"]):
                    d["x"] -= d["vx"] * dt
                    d["z"] -= d["vz"] * dt
                    d["vx"] = d["vz"] = 0.0
                keep.append(d)
            elif age < self.DROP_POP + self.DROP_HOLD + self.DROP_FLY:
                k = min(1.0, dt / max(0.05, self.DROP_POP + self.DROP_HOLD + self.DROP_FLY - age) * 1.0)
                d["x"] += (ex - d["x"]) * k
                d["y"] += (ey - 0.35 - d["y"]) * k
                d["z"] += (ez - d["z"]) * k
                d["fly"] = (age - self.DROP_POP - self.DROP_HOLD) / self.DROP_FLY
                keep.append(d)
        self.drops = keep

    def _drops(self, pos, got, mark, floor):
        """What was had, seen: each thing pops out where it came from, bounces, glints a moment, then flies to Claude
        (it's already in the pack: this is only the sight of it). got: the loot's lines; the items are the "found"
        events since mark."""
        items = [e[1] for e in self.events[mark:] if e[0] == "found"]
        whats = []
        for line in got:
            if "gold" in line and line.startswith("+"):
                whats.append("gold")
            elif "Health Potion" in line:
                whats.append("health")
            elif "Mana Potion" in line:
                whats.append("mana")
            elif "Scroll of Return" in line:
                whats.append("scroll")
            elif items:
                whats.append(items.pop(0))
        x, y, z = pos
        for k, what in enumerate(whats):
            a = self.rng.uniform(0, math.tau)
            sp = self.rng.uniform(0.8, 1.8)
            self.drops.append({"x": x, "y": y, "z": z, "vx": math.cos(a) * sp, "vy": self.rng.uniform(2.5, 4.0),
                               "vz": math.sin(a) * sp, "t": self.time + k * 0.08, "floor": floor, "what": what,
                               "rare": isinstance(what, dict) and (what.get("rarity", 0) >= 2 or what.get("type") != "gear")})

    def _hurt_player(self, dmg, element="arcane"):
        p = self.player
        taken = p.damage_taken(dmg)
        p.life -= taken
        self.hurt = min(1.0, self.hurt + 0.35 + taken / max(1, p.max_life()))
        self.events.append(("hurt", int(round(taken)), element))

    # ---- potions -------------------------------------------------------------------------------------------------
    def drink(self, kind):
        p = self.player
        if p.potions.get(kind, 0) <= 0:
            return False
        if kind == "health":
            if p.life >= p.max_life():
                return False
            more = 1 + p.bonus().get("draught", 0) / 100
            p.life = min(p.max_life(), p.life + p.max_life() * 0.4 * more)
            self.heal_over += p.max_life() * 0.3 * more
        elif kind == "mana":
            if p.mana >= p.max_mana():
                return False
            p.mana = min(p.max_mana(), p.mana + p.max_mana() * 0.5)
        else:
            return False
        p.potions[kind] -= 1
        self.events.append(("drink", kind))
        return True

    # ---- the monsters -----------------------------------------------------------------------------------------
    def _flow_field(self):
        """Walking distance from Claude's square to everywhere, made again when he moves square."""
        at = (int(self.x), int(self.z))
        if self._flow_at != at or self._flow is None:
            L = self.level
            dist = [[-1] * L.w for _ in range(L.h)]
            q = deque([at])
            if L.open_at(*at):
                dist[at[1]][at[0]] = 0
            while q:
                x, y = q.popleft()
                d = dist[y][x]
                if d > 40:
                    continue
                fh = L.floor[y, x]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < L.w and 0 <= ny < L.h and dist[ny][nx] < 0 and not L.solid[ny, nx] and \
                            abs(L.floor[ny, nx] - fh) <= levels.STEP + 0.01:
                        dist[ny][nx] = d + 1
                        q.append((nx, ny))
            self._flow, self._flow_at = dist, at
        return self._flow

    def _monsters(self, dt):
        L = self.level
        if not self.monsters:
            return
        flow = self._flow_field()
        ex, ey, ez = self.eye
        for m in self.monsters:
            m.hit_flash = max(0.0, m.hit_flash - dt)
            if m.dead:
                continue
            # what's on it
            slow = 1.0
            if "burn" in m.status:
                dps, left = m.status["burn"]
                m.hp -= dps * dt
                m.status["burn"] = (dps, left - dt)
                if left - dt <= 0:
                    del m.status["burn"]
            if "chill" in m.status:
                slow = 0.55
                m.status["chill"] -= dt
                if m.status["chill"] <= 0:
                    del m.status["chill"]
            if m.status.get("venom"):
                m.status["venom"] = [(d, left - dt) for d, left in m.status["venom"] if left - dt > 0]
                m.hp -= sum(d for d, _ in m.status["venom"]) * dt
            if m.hp <= 0:
                self._kill(m)
                continue
            dx, dz = self.x - m.x, self.z - m.z
            dist = math.hypot(dx, dz)
            if not m.awake:
                if dist > 24:
                    if self.time - getattr(m, "idle_at", 0) > 0.5:     # (far off and asleep: it wanders now and then)
                        m.idle_at = self.time
                        self._wander(m, 0.5)
                    continue
                if dist < 11 * self.wx.get("sight", 1.0) and L.line_of_sight(m.x, m.z, m.centre_y, ex, ez, ey):
                    m.awake = True
                    self.events.append(("notice", m))
                elif dist < 3:
                    m.awake = True
                else:
                    self._wander(m, dt)
                    continue
            if self.time >= getattr(m, "los_at", 0):          # (sight is looked at five times a second, not every frame)
                m.los_at = self.time + 0.2
                m.los = dist < 16 and L.line_of_sight(m.x, m.z, m.centre_y, ex, ez, ey)
            sees = m.los and dist < 16
            if m.kind == "timid":                                       # (a deer: it runs)
                if dist < 12:
                    self._walk(m, -dx / max(dist, 1e-3), -dz / max(dist, 1e-3), m.speed, dt)
                else:
                    m.awake = False
                continue
            if self.depth == 0 and math.hypot(m.x - m.home[0], m.z - m.home[1]) > 28 and dist > 8:
                m.awake = False                                         # (too far from home: it goes back)
                continue
            m.yaw = math.atan2(-dx, dz) if sees or dist < 2 else m.yaw
            m.cool -= dt
            # striking
            if m.strike >= 0:
                m.strike += dt
                if m.strike >= STRIKE_AT and m.strike - dt < STRIKE_AT:
                    if m.kind in ("ranged",) or (m.kind == "flyer" and dist > 1.6):
                        self._cast_at_player(m)
                    elif dist < m.radius + RADIUS + 0.75:
                        self._hurt_player(m.dmg, m.element)
                if m.strike >= STRIKE_LEN:
                    m.strike = -1.0
                m.moving = False
                continue
            want_range = 5.5 if m.kind == "ranged" else 0.0
            reach = m.radius + RADIUS + 0.55
            if m.kind == "ranged" and sees and dist < 9 and m.cool <= 0 and not self.in_town():
                m.strike, m.cool = 0.0, self.rng.uniform(1.8, 2.8)
                continue
            if m.kind != "ranged" and dist < reach and m.cool <= 0 and abs(self.y - m.y) < 1.0 and not self.in_town():
                m.strike, m.cool = 0.0, (1.7 if m.kind == "brute" else 1.15)
                continue
            # moving: straight at him when in sight, else down the flow field
            if m.kind == "ranged" and sees and want_range - 1 < dist < want_range + 2:
                gx, gz = -dz / max(dist, 1e-3), dx / max(dist, 1e-3)              # (sidestep while it waits)
                if int(self.time / 2 + m.id) % 2:
                    gx, gz = -gx, -gz
                speed = m.speed * 0.4
            elif m.kind == "ranged" and sees and dist < want_range - 1:
                gx, gz = -dx / max(dist, 1e-3), -dz / max(dist, 1e-3)
                speed = m.speed * 0.7
            elif sees and dist > reach * 0.9:
                gx, gz = dx / max(dist, 1e-3), dz / max(dist, 1e-3)
                speed = m.speed
            else:
                gx, gz = self._downhill(flow, m)
                speed = m.speed
            if m.kind == "flyer":
                gx += math.sin(self.time * 3 + m.id) * 0.5
                gz += math.cos(self.time * 2.6 + m.id) * 0.5
                m.lift = 0.35 + 0.12 * math.sin(self.time * 2 + m.id)
            if dist <= reach * 0.9 and m.kind != "ranged":
                gx = gz = 0.0
            self._walk(m, gx, gz, speed * slow, dt)

    def _downhill(self, flow, m):
        cx, cy = int(m.x), int(m.z)
        here = flow[cy][cx] if self.level.open_at(cx, cy) else -1
        best, bd = (0.0, 0.0), here if here >= 0 else 1 << 30
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            nx, ny = cx + dx, cy + dy
            if not self.level.open_at(nx, ny):
                continue
            d = flow[ny][nx]
            if d >= 0 and d < bd:
                if dx and dy and (not self.level.open_at(cx + dx, cy) or not self.level.open_at(cx, cy + dy)):
                    continue
                tx, tz = nx + 0.5 - m.x, ny + 0.5 - m.z
                ln = math.hypot(tx, tz) or 1
                best, bd = (tx / ln, tz / ln), d
        return best

    def _walk(self, m, gx, gz, speed, dt):
        # keep apart from the others
        for o in self.monsters:
            if o is m or o.dead:
                continue
            dx, dz = m.x - o.x, m.z - o.z
            d2 = dx * dx + dz * dz
            r = m.radius + o.radius
            if 1e-6 < d2 < r * r:
                d = math.sqrt(d2)
                gx += dx / d * (r - d) * 3
                gz += dz / d * (r - d) * 3
        ln = math.hypot(gx, gz)
        m.moving = ln > 0.05
        if not m.moving:
            return
        gx, gz = gx / max(1.0, ln), gz / max(1.0, ln)
        L = self.level
        nx, nz = m.x + gx * speed * dt, m.z + gz * speed * dt
        if L.safe is not None and L.safe[min(L.h - 1, int(nz)), min(L.w - 1, int(nx))]:
            return                                                      # (nothing hunts in the town)
        r = min(m.radius, 0.4)
        if L.can_stand(nx, m.z, r, m.y):
            m.x = nx
        if L.can_stand(m.x, nz, r, m.y):
            m.z = nz
        m.y = L.floor_at(m.x, m.z)
        if math.hypot(gx, gz) > 0.1:
            m.yaw = math.atan2(-gx, gz)

    def _wander(self, m, dt):
        m.wander -= dt
        if m.wander <= 0:
            m.wander = self.rng.uniform(1.5, 4.0)
            m.wdir = self.rng.uniform(0, math.tau) if self.rng.random() < 0.6 else None
        d = getattr(m, "wdir", None)
        if d is None:
            m.moving = False
            return
        self._walk(m, math.cos(d), math.sin(d), m.speed * 0.3, dt)

    def _cast_at_player(self, m):
        ex, ey, ez = self.eye
        sx, sy, sz = m.x, m.centre_y + 0.15, m.z
        dx, dy, dz = ex - sx, (ey - 0.2) - sy, ez - sz
        ln = math.sqrt(dx * dx + dy * dy + dz * dz) or 1
        sp = 7.5 + min(5, self.depth / 15)
        self.bolts.append(Bolt(sx, sy, sz, dx / ln * sp, dy / ln * sp, dz / ln * sp, m.dmg, m.element, foe=True))
        self.events.append(("foecast", m))
