"""ClaudeQuest's valley and everything living in it: the map, your pack, the herds, rival packs, bears and cougars,
the seasons, and the events that test the pack.

Time: a day lasts DAY_SECONDS of play, a season DAYS_PER_SEASON days. Spring brings pups (feed them by eating your
fill at a kill and carrying the rest back to the den), summer good hunting, autumn the elk rut, winter deep snow,
blizzards, thin herds and hungrier rivals. The game ends when no grown wolves are left.
"""
import math
import random

from . import art

SEASONS = ["spring", "summer", "autumn", "winter"]
DAY_SECONDS = 180.0
DAYS_PER_SEASON = 6
MAP_TILES = 90
TILE = art.TILE
WORLD = MAP_TILES * TILE

WALK, RUN, SNEAK = 105.0, 235.0, 55.0
BITE_RANGE = 46.0
TERRITORY_R = 330.0        # a scent mark claims this radius
RIVAL_TERRITORY_R = 720.0

MALE_NAMES = ["Ash", "Thorn", "Kodiak", "Rook", "Flint", "Sage", "Bramble", "Cedar", "Ember", "Hawk", "Juniper",
              "Kestrel", "Loki", "Moss", "Nash", "Orion", "Pike", "Quill", "Ridge", "Storm", "Talon", "Vale", "Wren",
              "Yukon", "Birch", "Canyon", "Dusk", "Frost", "Granite", "Hollow"]
FEMALE_NAMES = ["Aspen", "Briar", "Cinder", "Dawn", "Echo", "Fern", "Gale", "Hazel", "Iris", "Juno", "Kaya",
                "Luna", "Maple", "Nova", "Opal", "Poppy", "Rain", "Sky", "Tansy", "Willow", "Winter", "Yarrow",
                "Zephyr", "Clover", "Ivy", "Lark", "Misty", "Rue", "Sorrel", "Tundra"]


def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def _noise(seed):
    rnd = random.Random(seed)
    grid = {}

    def at(ix, iy):
        k = (ix, iy)
        if k not in grid:
            grid[k] = random.Random(hash((seed, ix, iy)) & 0xFFFFFFFF).random()
        return grid[k]

    def value(x, y, scale):
        x, y = x / scale, y / scale
        ix, iy = int(math.floor(x)), int(math.floor(y))
        fx, fy = x - ix, y - iy
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        a = at(ix, iy) + (at(ix + 1, iy) - at(ix, iy)) * fx
        b = at(ix, iy + 1) + (at(ix + 1, iy + 1) - at(ix, iy + 1)) * fx
        return a + (b - a) * fy

    def octave(x, y):
        return value(x, y, 18) * 0.6 + value(x + 100, y + 50, 7) * 0.3 + value(x + 7, y + 300, 3) * 0.1
    del rnd
    return octave


# ---- the map ---------------------------------------------------------------------------------------------------

class Map:
    def __init__(self, seed):
        self.seed = seed
        n = MAP_TILES
        rnd = random.Random(seed)
        elev, moist, flower = _noise(seed), _noise(seed + 1), _noise(seed + 2)
        self.tiles = [["grass"] * n for _ in range(n)]
        river_x = n * 0.58
        phase = rnd.random() * 6
        for y in range(n):
            rx = river_x + math.sin(y * 0.09 + phase) * 9 + (elev(3, y) - 0.5) * 6
            for x in range(n):
                e, m = elev(x, y), moist(x, y)
                edge = min(x, y, n - 1 - x, n - 1 - y)
                t = "grass"
                if m > 0.62:
                    t = "forest"
                elif m > 0.52:
                    t = "tall"
                elif m < 0.36:
                    t = "sage"
                elif flower(x, y) > 0.62:
                    t = "meadow"
                if e > 0.74 or edge < 2 or (edge < 4 and e > 0.55):
                    t = "rock"
                if abs(x - rx) < 1.6 + (0.6 if y % 17 < 9 else 0) and edge >= 2:
                    t = "water"
                self.tiles[y][x] = t
        lx, ly = int(n * 0.28), int(n * 0.3)                 # a lake in the north-west
        for y in range(ly - 4, ly + 5):
            for x in range(lx - 6, lx + 7):
                if ((x - lx) / 6.5) ** 2 + ((y - ly) / 4.5) ** 2 < 1 and 0 < x < n and 0 < y < n:
                    self.tiles[y][x] = "water"
        # dens: yours in the south-west quarter, two rivals in the north
        self.den = self._clear_spot(int(n * 0.32), int(n * 0.68), rnd)
        self.rival_dens = [self._clear_spot(int(n * 0.82), int(n * 0.22), rnd),
                           self._clear_spot(int(n * 0.16), int(n * 0.12), rnd)]
        # trees, rocks, sage, logs
        self.decor = []                                  # (kind, x, y, radius)
        self.grid = {}
        keep = [self.den] + self.rival_dens
        for y in range(n):
            for x in range(n):
                t = self.tiles[y][x]
                px, py = x * TILE + rnd.uniform(6, TILE - 6), y * TILE + rnd.uniform(6, TILE - 6)
                if any(math.hypot(px - kx, py - ky) < 90 for kx, ky in keep):
                    continue
                r = rnd.random()
                kind = None
                if t == "forest" and r < 0.42:
                    kind = "pine" if rnd.random() < 0.7 else "aspen"
                elif t == "forest" and r < 0.45:
                    kind = "log"
                elif t in ("grass", "meadow", "tall") and r < 0.012:
                    kind = "rock"
                elif t in ("grass", "tall") and r < 0.03:
                    kind = "aspen"
                elif t == "sage" and r < 0.22:
                    kind = "sage"
                elif t == "sage" and r < 0.235:
                    kind = "rock"
                if kind:
                    radius = {"pine": 11, "aspen": 6, "rock": 13, "sage": 0, "log": 0}[kind]
                    self._add_decor(kind, px, py, radius)
        self._add_decor("den", self.den[0], self.den[1], 24)
        for d in self.rival_dens:
            self._add_decor("den", d[0], d[1], 24)

    def _add_decor(self, kind, x, y, r):
        d = (kind, x, y, r)
        self.decor.append(d)
        self.grid.setdefault((int(x // TILE), int(y // TILE)), []).append(d)

    def _clear_spot(self, tx, ty, rnd):
        for radius in range(0, 20):
            for _ in range(30):
                x, y = tx + rnd.randint(-radius, radius), ty + rnd.randint(-radius, radius)
                if 4 < x < MAP_TILES - 4 and 4 < y < MAP_TILES - 4 and all(
                        self.tiles[y + dy][x + dx] in ("grass", "meadow", "sage", "tall")
                        for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    return (x * TILE + TILE / 2, y * TILE + TILE / 2)
        return (tx * TILE, ty * TILE)

    def tile_at(self, x, y):
        tx, ty = int(x // TILE), int(y // TILE)
        if 0 <= tx < MAP_TILES and 0 <= ty < MAP_TILES:
            return self.tiles[ty][tx]
        return "rock"

    def blocked(self, x, y):
        return self.tile_at(x, y) == "rock"

    def nearby_decor(self, x, y):
        tx, ty = int(x // TILE), int(y // TILE)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                yield from self.grid.get((tx + dx, ty + dy), ())

    def random_land(self, rnd, kinds=("grass", "meadow", "sage", "tall"), near=None, spread=None):
        for _ in range(400):
            if near:
                x = near[0] + rnd.uniform(-spread, spread)
                y = near[1] + rnd.uniform(-spread, spread)
            else:
                x, y = rnd.uniform(3 * TILE, WORLD - 3 * TILE), rnd.uniform(3 * TILE, WORLD - 3 * TILE)
            if self.tile_at(x, y) in kinds:
                return x, y
        return WORLD / 2, WORLD / 2


# ---- creatures -------------------------------------------------------------------------------------------------

class Creature:
    _ids = 0

    def __init__(self, x, y):
        Creature._ids += 1
        self.id = Creature._ids
        self.x, self.y = x, y
        self.vx = self.vy = 0.0
        self.facing = 1
        self.phase = random.random() * 6
        self.dead = False
        self.cool = 0.0

    @property
    def moving(self):
        return abs(self.vx) + abs(self.vy) > 8


class Wolf(Creature):
    def __init__(self, x, y, name, coat, sex, pack="player", age_days=400, pup=False):
        super().__init__(x, y)
        self.name, self.coat, self.sex, self.pack = name, coat, sex, pack
        self.age = age_days
        self.pup = pup
        self.hp = self.maxhp = 60.0 if pup else 100.0
        self.hunger = 80.0
        self.stamina = 100.0
        self.pose = "stand"
        self.carried = 0.0
        self.mange = False
        self.target = None
        self.goal = None
        self.flee_until = 0.0
        self.guard = False
        self.hurt_t = 0.0
        self.strength = 0.6 if pup else 1.0

    def to_json(self):
        return {"name": self.name, "coat": self.coat, "sex": self.sex, "age": self.age, "pup": self.pup,
                "hp": round(self.hp, 1), "hunger": round(self.hunger, 1), "x": round(self.x), "y": round(self.y),
                "mange": self.mange, "carried": round(self.carried, 1)}

    @classmethod
    def from_json(cls, d):
        w = cls(d["x"], d["y"], d["name"], d["coat"], d["sex"], age_days=d.get("age", 400), pup=d.get("pup", False))
        w.hp, w.hunger = d.get("hp", 100), d.get("hunger", 80)
        w.mange, w.carried = d.get("mange", False), d.get("carried", 0)
        w.maxhp = 60.0 if w.pup else 100.0
        w.strength = 0.6 if w.pup else 1.0
        return w


class Prey(Creature):
    def __init__(self, x, y, kind, herd=None, calf=False, bull=False):
        super().__init__(x, y)
        self.kind, self.herd, self.calf, self.bull = kind, herd, calf, bull
        length, height, _b, _d, _l, speed, hp, meat = art.PREY[kind]
        self.speed = speed * (0.82 if calf else 1.0)
        self.hp = self.maxhp = hp * (0.5 if calf else 1.0) * (1.25 if bull else 1.0)
        self.meat = meat * (0.5 if calf else 1.0)
        self.stamina = 100.0
        self.fleeing_until = 0.0
        self.fear_from = None
        self.wander = None


class Beast(Creature):
    """A bear or a cougar."""

    def __init__(self, x, y, kind):
        super().__init__(x, y)
        self.kind = kind
        self.hp = self.maxhp = art.PREY[kind][6]
        self.speed = art.PREY[kind][5]
        self.goal = None
        self.leaving = False
        self.timer = 0.0


class Carcass:
    def __init__(self, x, y, kind, meat):
        self.x, self.y, self.kind = x, y, kind
        self.meat = self.maxmeat = meat
        self.age = 0.0


class Marker:
    def __init__(self, x, y, strength=1.0):
        self.x, self.y, self.strength = x, y, strength


class RivalPack:
    def __init__(self, name, den, coat):
        self.name, self.den, self.coat = name, den, coat
        self.angry_until = 0.0
        self.wolves = []


# ---- the world ---------------------------------------------------------------------------------------------------

class World:
    def __init__(self, seed, leader=None):
        self.seed = seed
        self.rnd = random.Random(seed * 7 + 1)
        self.map = Map(seed)
        self.t = DAY_SECONDS * 0.3                         # mid-morning on the first day of spring
        self.messages = []                                 # (text, kind, time) for the screen
        self.log = []
        self.prompt = None                                 # ("lone wolf", Wolf) waiting for Y/N
        self.pack = []
        self.player = None
        self.prey, self.beasts, self.carcasses, self.markers = [], [], [], []
        self.rivals = []
        self.hunt_target = None
        self.blizzard_until = 0.0
        self.last_day = -1
        self.stats = {"years": 0, "pups_born": 0, "pups_raised": 0, "kills": {}, "rivals_beaten": 0, "max_pack": 0,
                      "lost": 0}
        self.flags = {"pups_year": -1}
        self.over = False
        self.events_today = set()
        if leader is not None:
            self._new_pack(leader)
        self._new_rivals()
        self._populate(initial=True)

    # ---- time -----------------------------------------------------------------------------------------------
    @property
    def day(self):
        return int(self.t // DAY_SECONDS)

    @property
    def time_of_day(self):
        return (self.t % DAY_SECONDS) / DAY_SECONDS            # 0 = midnight

    @property
    def season(self):
        return SEASONS[(self.day // DAYS_PER_SEASON) % 4]

    @property
    def year(self):
        return self.day // (DAYS_PER_SEASON * 4) + 1

    @property
    def day_of_season(self):
        return self.day % DAYS_PER_SEASON + 1

    @property
    def night(self):
        tod = self.time_of_day
        return tod < 0.22 or tod > 0.86

    def clock_text(self):
        minutes = int(self.time_of_day * 24 * 60)
        h, m = divmod(minutes, 60)
        return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"

    def say(self, text, kind="info"):
        self.messages.append((text, kind, self.t))
        self.log.append((self.day, text))
        del self.messages[:-6]
        del self.log[:-80]

    # ---- setting up -----------------------------------------------------------------------------------------
    def _new_pack(self, leader):
        dx, dy = self.map.den
        name, coat, sex = leader
        me = Wolf(dx + 30, dy + 30, name, coat, sex, age_days=3 * 365)
        mate_sex = "female" if sex == "male" else "male"
        names = FEMALE_NAMES if mate_sex == "female" else MALE_NAMES
        mate = Wolf(dx - 30, dy + 34, self.rnd.choice(names), self.rnd.choice(list(art.COATS)), mate_sex,
                    age_days=3 * 365)
        others = [Wolf(dx + self.rnd.uniform(-60, 60), dy + self.rnd.uniform(40, 80),
                       self.rnd.choice(MALE_NAMES + FEMALE_NAMES), self.rnd.choice(list(art.COATS)),
                       self.rnd.choice(("male", "female")), age_days=500) for _ in range(2)]
        self.pack = [me, mate] + others
        self.player = me
        self.stats["max_pack"] = len(self.pack)
        self.say(f"{me.name} and {mate.name} lead a small pack in the valley. Spring has come - pups are on the "
                 "way. Keep the pack fed!", "big")

    def _new_rivals(self):
        names = ["the Ridgeback pack", "the Blackwater pack"]
        self.rivals = []
        for i, den in enumerate(self.map.rival_dens):
            rp = RivalPack(names[i], den, art.RIVAL_COATS[i])
            for _ in range(self.rnd.randint(3, 5)):
                x, y = self.map.random_land(self.rnd, near=den, spread=200)
                w = Wolf(x, y, self.rnd.choice(MALE_NAMES + FEMALE_NAMES),
                         self.rnd.choice([art.RIVAL_COATS[i], art.RIVAL_COATS[(i + 2) % 4]]),
                         self.rnd.choice(("male", "female")), pack=i)
                rp.wolves.append(w)
            self.rivals.append(rp)

    def _herd_targets(self):
        s = self.season
        return {"elk": 3 if s == "winter" else 5, "deer": 3 if s == "winter" else 4, "bison": 2, "hare": 10}

    def _populate(self, initial=False):
        """Bring herds up to the season's numbers (new arrivals come in from the edges of the valley)."""
        targets = self._herd_targets()
        herds = {}
        for p in self.prey:
            if not p.dead:
                herds.setdefault((p.kind, p.herd), []).append(p)
        counts = {}
        for (kind, _h) in herds:
            counts[kind] = counts.get(kind, 0) + 1
        for kind, want in targets.items():
            have = counts.get(kind, 0) if kind != "hare" else len([p for p in self.prey if p.kind == "hare"])
            for _ in range(max(0, want - have)):
                if kind == "hare":
                    x, y = self.map.random_land(self.rnd, ("grass", "sage", "meadow", "tall"))
                    self.prey.append(Prey(x, y, "hare", herd=None))
                    continue
                if initial:
                    cx, cy = self.map.random_land(self.rnd, ("grass", "meadow", "sage", "tall"))
                else:
                    edge = self.rnd.choice(("n", "s", "e", "w"))
                    cx = {"e": WORLD - 6 * TILE, "w": 6 * TILE}.get(edge, self.rnd.uniform(8 * TILE, WORLD - 8 * TILE))
                    cy = {"s": WORLD - 6 * TILE, "n": 6 * TILE}.get(edge, self.rnd.uniform(8 * TILE, WORLD - 8 * TILE))
                    cx, cy = self.map.random_land(self.rnd, near=(cx, cy), spread=300)
                hid = self.rnd.randint(1, 10 ** 9)
                size = {"elk": (6, 10), "deer": (3, 6), "bison": (5, 8)}[kind]
                n = self.rnd.randint(*size)
                if self.season == "winter":
                    n = max(2, n - 2)
                for i in range(n):
                    x, y = self.map.random_land(self.rnd, near=(cx, cy), spread=90)
                    calf = self.season in ("spring", "summer") and i >= 2 and self.rnd.random() < 0.35
                    bull = kind in ("elk", "deer") and i == 0 and not calf
                    self.prey.append(Prey(x, y, kind, herd=hid, calf=calf, bull=bull))
        self.prey = [p for p in self.prey if not p.dead]

    # ---- the main step ------------------------------------------------------------------------------------
    def update(self, dt, ctl):
        if self.over:
            return
        if self.prompt is None:
            self.t += dt
        if self.day != self.last_day:
            self._new_day()
        winter = self.season == "winter"
        self._player(dt, ctl)
        for w in self.pack:
            if w is not self.player and not w.dead:
                self._pack_ai(w, dt)
        for rp in self.rivals:
            for w in rp.wolves:
                if not w.dead:
                    self._rival_ai(rp, w, dt)
        for p in self.prey:
            if not p.dead:
                self._prey_ai(p, dt, winter)
        for b in self.beasts:
            if not b.dead:
                self._beast_ai(b, dt)
        self._needs(dt, winter)
        for c in self.carcasses:
            c.age += dt
        self.carcasses = [c for c in self.carcasses if c.meat > 0.5 and c.age < DAY_SECONDS * 3]
        self.prey = [p for p in self.prey if not p.dead]
        self.beasts = [b for b in self.beasts if not b.dead and not (b.leaving and self._off_map(b))]
        for rp in self.rivals:
            rp.wolves = [w for w in rp.wolves if not w.dead]
        if self.hunt_target is not None and (self.hunt_target.dead or dist(self.hunt_target, self.player) > 900):
            self.hunt_target = None
        for m in self.markers:
            m.strength -= dt / (DAY_SECONDS * DAYS_PER_SEASON * 2)
        self.markers = [m for m in self.markers if m.strength > 0]
        self._check_pack()

    def _off_map(self, c):
        return c.x < TILE or c.y < TILE or c.x > WORLD - TILE or c.y > WORLD - TILE

    # ---- moving --------------------------------------------------------------------------------------------
    def _speed_factor(self, c, wolfish=True):
        t = self.map.tile_at(c.x, c.y)
        f = {"water": 0.45, "tall": 0.9, "forest": 0.86}.get(t, 1.0)
        if self.season == "winter":
            deep = t in ("tall", "meadow")
            f *= (0.62 if deep else 0.8) if wolfish else (0.48 if deep else 0.7)
        return f

    def _move(self, c, dx, dy, speed, dt, wolfish=True, avoid_water=False):
        n = math.hypot(dx, dy)
        if n < 1e-6:
            c.vx *= 0.7
            c.vy *= 0.7
            return
        speed *= self._speed_factor(c, wolfish)
        vx, vy = dx / n * speed, dy / n * speed
        nx, ny = c.x + vx * dt, c.y + vy * dt
        if self.map.blocked(nx, ny) or (avoid_water and self.map.tile_at(nx, ny) == "water"):
            # slide along: try each axis, then turn
            if not self.map.blocked(nx, c.y) and not (avoid_water and self.map.tile_at(nx, c.y) == "water"):
                ny = c.y
            elif not self.map.blocked(c.x, ny) and not (avoid_water and self.map.tile_at(c.x, ny) == "water"):
                nx = c.x
            else:
                ang = math.atan2(vy, vx) + (1.2 if c.id % 2 else -1.2)
                nx, ny = c.x + math.cos(ang) * speed * dt, c.y + math.sin(ang) * speed * dt
                if self.map.blocked(nx, ny):
                    return
        for kind, x, y, r in self.map.nearby_decor(nx, ny):
            if r:
                d = math.hypot(nx - x, ny - y)
                if d < r + 6:
                    push = (r + 6 - d) / max(d, 0.1)
                    nx += (nx - x) * push
                    ny += (ny - y) * push
        c.vx, c.vy = (nx - c.x) / dt, (ny - c.y) / dt
        c.x = min(WORLD - TILE, max(TILE, nx))
        c.y = min(WORLD - TILE, max(TILE, ny))
        if abs(vx) > 1:
            c.facing = 1 if vx > 0 else -1
        c.phase += dt * (speed / 22.0)

    # ---- the player's wolf -----------------------------------------------------------------------------------
    def _player(self, dt, ctl):
        me = self.player
        if me is None or me.dead:
            return
        dx, dy = ctl.get("move", (0, 0))
        running = ctl.get("run") and me.stamina > 2 and (dx or dy)
        sneaking = ctl.get("sneak") and not running
        speed = RUN if running else SNEAK if sneaking else WALK
        if me.mange or me.hp < 30:
            speed *= 0.8
        if me.hunger <= 0:
            speed *= 0.85
        if running:
            me.stamina = max(0, me.stamina - 8 * dt)
        else:
            me.stamina = min(100, me.stamina + (6 if self.blizzard_until > self.t else 12) * dt)
        eating = False
        if ctl.get("eat") and not (dx or dy):
            c = self._carcass_near(me, 52)
            if c is not None:
                eating = self._eat(me, c, dt, carry=True)
        self._move(me, dx, dy, speed, dt)
        me.idle = 0.0 if (dx or dy or eating) else getattr(me, "idle", 0.0) + dt
        me.pose = ("eat" if eating else "run" if running and me.moving else "sneak" if sneaking and me.moving
                   else "trot" if me.moving else "stand")
        if ctl.get("howl"):
            me.pose = "howl"
            if me.cool <= 0:
                me.cool = 3.0
                for w in self.pack:
                    w.goal = None
                    w.guard = w.guard and self.season in ("spring", "summer")
                self.say(f"{me.name} howls. The pack gathers.", "pack")
        me.cool = max(0.0, me.cool - dt)
        if ctl.get("bite"):
            self._bite(me, player=True)
        if ctl.get("mark"):
            self._mark(me)
        if ctl.get("rest") and not me.moving:
            me.pose = "lie"
            me.stamina = min(100, me.stamina + 10 * dt)
        # crossing into a rival pack's land: their scent marks warn you first
        inside = next((rp for rp in self.rivals if math.hypot(me.x - rp.den[0], me.y - rp.den[1]) < RIVAL_TERRITORY_R),
                      None)
        if inside is not getattr(self, "_inside", None):
            self._inside = inside
            if inside is not None:
                self.say(f"You smell {inside.name}'s scent marks - this is their territory. Tread carefully.", "bad")
        # feeding the pups at the den
        if me.carried > 0 and math.hypot(me.x - self.map.den[0], me.y - self.map.den[1]) < 120:
            self._feed_at_den(me)

    def _carcass_near(self, w, r):
        best, bd = None, r
        for c in self.carcasses:
            d = math.hypot(c.x - w.x, c.y - w.y)
            if d < bd:
                best, bd = c, d
        return best

    def _eat(self, w, c, dt, carry=False):
        if c.meat <= 0:
            return False
        if w.hunger < 99:
            gain = min(14 * dt, c.meat * 2, 100 - w.hunger)
            w.hunger += gain
            c.meat -= gain / 2
            if w.mange:
                w.mange_meal = getattr(w, "mange_meal", 0) + gain
                if w.mange_meal > 160:
                    w.mange = False
                    self.say(f"{w.name} is eating well again - the mange is clearing up.", "good")
            return True
        if carry and w.carried < 40 and self._hungry_at_den():
            take = min(8 * dt, c.meat, 40 - w.carried)
            w.carried += take
            c.meat -= take
            if w.carried >= 40 - 1e-3 and not getattr(w, "told_full", False):
                w.told_full = True
                self.say(f"{w.name} carries all the food she can - take it back to the den."
                         if w.sex == "female" else
                         f"{w.name} carries all the food he can - take it back to the den.", "pack")
            return True
        return False

    def _hungry_at_den(self):
        return any(w.pup and not w.dead and w.hunger < 95 for w in self.pack) or \
            any(w.guard and not w.dead and w.hunger < 70 for w in self.pack)

    def _feed_at_den(self, me):
        fed = []
        for w in sorted((w for w in self.pack if not w.dead and (w.pup or w.guard)), key=lambda w: w.hunger):
            if me.carried <= 0:
                break
            need = 100 - w.hunger
            if need < 5 or math.hypot(w.x - self.map.den[0], w.y - self.map.den[1]) > 220:
                continue
            give = min(me.carried, need / 2.2)
            w.hunger += give * 2.2
            me.carried -= give
            fed.append(w.name)
        if fed:
            me.told_full = False
            self.say(f"{me.name} brings food home: {', '.join(fed)} eat{'s' if len(fed) == 1 else ''}.", "good")

    def _mark(self, w):
        if w.cool > 0:
            return
        w.cool = 4.0
        for m in self.markers:
            if math.hypot(m.x - w.x, m.y - w.y) < 120:
                m.strength = 1.0
                self.say("You freshen the scent mark.", "pack")
                return
        self.markers.append(Marker(w.x, w.y))
        self.say("You leave a scent mark - this land is yours.", "pack")

    def territory_strength(self, x, y):
        return max((m.strength for m in self.markers if math.hypot(m.x - x, m.y - y) < TERRITORY_R), default=0.0)

    # ---- fighting ------------------------------------------------------------------------------------------
    def _hostiles_for(self, w):
        out = list(self.beasts)
        for rp in self.rivals:
            if w.pack == "player":
                out += rp.wolves
        if w.pack != "player":
            out += [x for x in self.pack if not x.dead]
        return [h for h in out if not h.dead]

    def _bite(self, w, player=False, target=None):
        if w.cool > 0:
            return
        if target is None:
            best, bd = None, BITE_RANGE
            pool = [p for p in self.prey if not p.dead] + self._hostiles_for(w)
            for c in pool:
                d = math.hypot(c.x - w.x, c.y - w.y)
                ahead = (c.x - w.x) * w.facing > -12
                if d < bd and (ahead or d < 26):
                    best, bd = c, d
            target = best
        if target is None or math.hypot(target.x - w.x, target.y - w.y) > BITE_RANGE + 6:
            if player:
                w.pose = "attack"
                w.cool = 0.4
            return
        w.cool = 0.75 if player else 1.2
        w.pose = "attack"
        w.facing = 1 if target.x > w.x else -1
        dmg = (11 + self.rnd.uniform(0, 6)) * w.strength * (0.8 if w.hunger < 15 else 1.0)
        if isinstance(target, Prey):
            target.hp -= dmg
            target.fleeing_until = max(target.fleeing_until, self.t + 8)
            target.fear_from = w
            if w.pack == "player":
                self.hunt_target = target
            # elk and bison fight back
            kick = {"elk": 0.16 if not target.bull else 0.28, "bison": 0.34, "deer": 0.06}.get(target.kind, 0)
            if self.season == "autumn" and target.bull:
                kick += 0.1
            if self.rnd.random() < kick:
                hurt = {"elk": 12, "bison": 22, "deer": 6}[target.kind] * self.rnd.uniform(0.6, 1.2)
                self._hurt(w, hurt, f"{'A bull' if target.bull else 'An'} {target.kind} kicks {w.name}!"
                           if target.kind != "bison" else f"A bison gores {w.name}!")
            if target.hp <= 0:
                self._kill_prey(target, w)
        elif isinstance(target, Beast):
            target.hp -= dmg * 0.8
            target.goal = w
            if target.hp < target.maxhp * 0.6 and not target.leaving:
                target.leaving = True
                self.say(f"The {target.kind} has had enough and retreats!", "good")
        elif isinstance(target, Wolf):
            target.hp -= dmg
            target.hurt_t = 1.0
            if target.pack != "player":
                rp = self.rivals[target.pack]
                rp.angry_until = self.t + 40
                if target.hp <= 0:
                    target.dead = True
                    self.stats["rivals_beaten"] += 1
                    self.say(f"{w.name} drives off a {rp.name.split()[1]} wolf for good.", "good")
                elif target.hp < 50:
                    target.flee_until = self.t + 25
            else:
                who = self.rivals[w.pack].name if w.pack != "player" else "rival wolves"
                self._hurt(target, 0, None, f"killed by {who}")

    def _hurt(self, w, amount, text, cause=""):
        w.hp -= amount
        w.hurt_t = 1.2
        if text:
            self.say(text, "bad")
        if w.hp < 25 and not w.dead and w is not self.player:
            w.flee_until = self.t + 20                     # badly hurt: it backs off from the fight
        if w.hp <= 0 and not w.dead:
            self._die(w, cause)

    def _die(self, w, cause=""):
        w.dead = True
        w.hp = 0
        self.stats["lost"] += 1
        self.say(f"{w.name} has died{(' - ' + cause) if cause else ''}.", "bad")
        self.carcasses.append(Carcass(w.x, w.y, "wolf", 0.6))

    def _kill_prey(self, p, w):
        p.dead = True
        self.carcasses.append(Carcass(p.x, p.y, p.kind, p.meat))
        self.stats["kills"][p.kind] = self.stats["kills"].get(p.kind, 0) + 1
        if getattr(w, "pack", None) == "player":
            name = {"elk": "an elk" if not p.calf else "an elk calf", "deer": "a deer", "bison": "a bison",
                    "hare": "a hare"}[p.kind]
            self.say(f"The pack brings down {name}! Hold F to eat.", "good")
            self.hunt_target = None

    # ---- your packmates -----------------------------------------------------------------------------------------
    def _pack_ai(self, w, dt):
        me, den = self.player, self.map.den
        w.cool = max(0.0, w.cool - dt)
        w.hurt_t = max(0.0, w.hurt_t - dt)
        w.stamina = min(100, w.stamina + 8 * dt)
        speed = WALK
        young_pups = [p for p in self.pack if p.pup and not p.dead and p.age < 120]
        # pups: play near the den until autumn
        if w.pup and w.age < 120:
            threat = self._threat_near(den, 200)
            if threat is not None and dist(threat, w) < 140:
                self._move(w, w.x - threat.x, w.y - threat.y, RUN * 0.6, dt)
                w.pose = "run"
                return
            self._wander(w, den, 70, dt, WALK * 0.55)
            return
        threat = self._threat_near((w.x, w.y), 280)
        if w.guard:
            threat = threat or self._threat_near(den, 300)
        if threat is not None and w.flee_until > self.t and dist(threat, w) < 200:
            self._move(w, w.x - threat.x, w.y - threat.y, RUN * 0.8, dt)     # hurt: keep away from it
            w.pose = "run"
            return
        if threat is not None and w.flee_until <= self.t:
            self._chase_and_bite(w, threat, dt)
            return
        # the guard stays home with young pups
        if w.guard and w.hunger < 25:                        # a starving guard slips away to eat
            c = self._carcass_near(w, 1600)
            if c is not None:
                if math.hypot(c.x - w.x, c.y - w.y) > 34:
                    self._move(w, c.x - w.x, c.y - w.y, RUN * 0.8, dt)
                    w.pose = "run"
                else:
                    w.pose = "eat" if self._eat(w, c, dt) else "stand"
                return
        if young_pups and (w.guard or (not any(x.guard and not x.dead for x in self.pack) and w is not me)):
            if not any(x.guard and not x.dead for x in self.pack):
                w.guard = True
                self.say(f"{w.name} stays at the den to guard the pups.", "pack")
            if math.hypot(w.x - den[0], w.y - den[1]) > 110:
                self._move(w, den[0] - w.x, den[1] - w.y, WALK, dt)
                w.pose = "trot"
            else:
                w.pose = "lie"
                w.vx = w.vy = 0
            return
        w.guard = False
        # a hungry wolf eats before it hunts again
        if w.hunger < 50:
            c = self._carcass_near(w, 900)
            if c is not None:
                if math.hypot(c.x - w.x, c.y - w.y) > 34:
                    self._move(w, c.x - w.x, c.y - w.y, RUN * 0.8, dt)
                    w.pose = "run"
                else:
                    w.pose = "eat" if self._eat(w, c, dt) else "stand"
                    w.vx = w.vy = 0
                return
        # join the hunt
        ht = self.hunt_target
        if ht is not None and not ht.dead and dist(ht, w) < 700 and (w.hp > 30):
            self._chase_and_bite(w, ht, dt)
            return
        # eat at a kill
        c = self._carcass_near(w, 520)
        if c is not None and w.hunger < 85:
            if math.hypot(c.x - w.x, c.y - w.y) > 34:
                self._move(w, c.x - w.x, c.y - w.y, RUN * 0.8 if w.hunger < 40 else WALK, dt)
                w.pose = "trot"
            else:
                w.pose = "eat" if self._eat(w, c, dt) else "stand"
                w.vx = w.vy = 0
            return
        # follow the leader
        if me is None or me.dead:
            return
        i = [x for x in self.pack if not x.dead and not (x.pup and x.age < 120) and x is not me].index(w) \
            if w in self.pack else 0
        ang = math.pi + (i - 1.5) * 0.55 + (0 if me.facing > 0 else math.pi)
        ring = 60 + (i // 4) * 30
        tx = me.x + math.cos(ang) * ring * (1 if me.facing > 0 else 1)
        ty = me.y + math.sin(ang) * ring * 0.6
        d = math.hypot(tx - w.x, ty - w.y)
        if d > 40:
            speed = RUN * 0.95 if d > 220 else WALK * (1.25 if me.moving else 0.8)
            self._move(w, tx - w.x, ty - w.y, speed, dt)
            w.pose = "run" if speed > WALK * 1.5 else "trot"
        else:
            w.vx = w.vy = 0
            w.pose = "lie" if not me.moving and me.pose in ("lie", "stand", "eat") and \
                getattr(me, "idle", 0) > 3 else "stand"
            w.facing = me.facing

    def _threat_near(self, pos, r):
        x, y = pos if isinstance(pos, tuple) else (pos.x, pos.y)
        best, bd = None, r
        den = self.map.den
        for b in self.beasts:
            if not b.dead and not b.leaving:
                d = math.hypot(b.x - x, b.y - y)
                # the pack only takes on a bear or cougar that's attacking one of them, is close, or is near the den
                fighting = isinstance(b.goal, Wolf) or b.kind == "cougar" or d < 90 or                     math.hypot(b.x - den[0], b.y - den[1]) < 320
                if d < bd and fighting:
                    best, bd = b, d
        for rp in self.rivals:
            if rp.angry_until > self.t or any(getattr(w, "raiding", False) for w in rp.wolves):
                for w in rp.wolves:
                    if not w.dead and w.flee_until < self.t:
                        d = math.hypot(w.x - x, w.y - y)
                        if d < bd:
                            best, bd = w, d
        return best

    def _chase_and_bite(self, w, target, dt):
        d = dist(w, target)
        if d > BITE_RANGE - 8:
            run = d > 90 and w.stamina > 5
            self._move(w, target.x - w.x, target.y - w.y, RUN * (0.95 if run else 0.6), dt)
            w.stamina = max(0, w.stamina - (7 * dt if run else 0))
            w.pose = "run" if run else "trot"
        else:
            w.pose = "attack"
            w.vx = w.vy = 0
            self._bite(w, target=target)

    def _wander(self, w, home, radius, dt, speed):
        if w.goal is None or math.hypot(w.goal[0] - w.x, w.goal[1] - w.y) < 10 or self.rnd.random() < 0.002:
            if self.rnd.random() < 0.4:
                w.goal = (w.x, w.y)
            else:
                w.goal = (home[0] + self.rnd.uniform(-radius, radius), home[1] + self.rnd.uniform(-radius, radius))
        dx, dy = w.goal[0] - w.x, w.goal[1] - w.y
        if math.hypot(dx, dy) > 8:
            self._move(w, dx, dy, speed, dt)
            w.pose = "trot"
        else:
            w.vx = w.vy = 0
            w.pose = "sleep" if self.night else ("lie" if w.id % 3 else "stand")

    # ---- rival wolves ----------------------------------------------------------------------------------------
    def _rival_ai(self, rp, w, dt):
        w.cool = max(0.0, w.cool - dt)
        w.hurt_t = max(0.0, w.hurt_t - dt)
        den = rp.den
        me = self.player
        if w.flee_until > self.t:
            self._move(w, den[0] - w.x, den[1] - w.y, RUN * 0.8, dt)
            w.pose = "run"
            if math.hypot(den[0] - w.x, den[1] - w.y) < 100:
                w.flee_until = 0
                w.raiding = False
                w.hp = min(w.maxhp, w.hp + 30)
            return
        # trespassers in their land make them angry
        if me is not None and not me.dead and math.hypot(me.x - den[0], me.y - den[1]) < RIVAL_TERRITORY_R \
                and dist(me, w) < 330 and rp.angry_until < self.t:
            rp.angry_until = self.t + 25
            self.say(f"You've wandered into {rp.name}'s territory - they're coming for you!", "bad")
        angry = rp.angry_until > self.t
        raiding = getattr(w, "raiding", False)
        if angry or raiding:
            targets = [x for x in self.pack if not x.dead]
            if raiding:
                targets.sort(key=lambda x: math.hypot(x.x - self.map.den[0], x.y - self.map.den[1]))
            else:
                targets.sort(key=lambda x: dist(x, w))
            if targets:
                t = targets[0]
                if raiding and dist(t, w) > 400:
                    self._move(w, self.map.den[0] - w.x, self.map.den[1] - w.y, RUN * 0.75, dt)
                    w.pose = "run"
                    if self.t > getattr(w, "raid_until", 0):
                        w.raiding = False
                        w.flee_until = self.t + 30
                    return
                home = math.hypot(t.x - den[0], t.y - den[1])
                if not raiding and (dist(t, w) > 900 or home > RIVAL_TERRITORY_R + 150):
                    pass                                     # out of their land: they let you go
                else:
                    self._chase_and_bite(w, t, dt)
                    if dist(t, w) < BITE_RANGE:
                        self._bite(w, target=t)
                    return
        # patrol and eat at home
        c = self._carcass_near(w, 400)
        if c is not None and w.hunger < 80:
            if math.hypot(c.x - w.x, c.y - w.y) > 34:
                self._move(w, c.x - w.x, c.y - w.y, WALK, dt)
                w.pose = "trot"
            else:
                w.pose = "eat" if self._eat(w, c, dt) else "stand"
            return
        self._wander(w, den, 360, dt, WALK * 0.8)
        # rivals hunt a little too (it keeps the herds moving and makes kills to steal)
        if self.rnd.random() < 0.00015 and w.hunger < 60:
            for p in self.prey:
                if not p.dead and math.hypot(p.x - den[0], p.y - den[1]) < RIVAL_TERRITORY_R and p.kind != "bison":
                    self._kill_prey(p, w)
                    w.hunger = 90
                    break

    # ---- the herds ---------------------------------------------------------------------------------------------
    def _prey_ai(self, p, dt, winter):
        p.cool = max(0.0, p.cool - dt)
        # spotting wolves
        detect = {"elk": 250, "deer": 270, "bison": 190, "hare": 140}[p.kind]
        if self.night:
            detect *= 0.75
        nearest, nd = None, 1e9
        for w in self._all_wolves():
            d = math.hypot(w.x - p.x, w.y - p.y)
            r = detect * (0.45 if (w is self.player and w.pose == "sneak") else 1.0)
            if d < r and d < nd:
                nearest, nd = w, d
        if nearest is not None:
            if p.fleeing_until < self.t and p.kind != "bison":
                self._alarm(p, nearest)
            elif p.kind == "bison" and nd < 110:
                self._alarm(p, nearest)
            p.fear_from = nearest
        speed_base = p.speed
        if winter:
            speed_base *= 0.9
        if p.fleeing_until > self.t and p.fear_from is not None:
            f = p.fear_from
            dx, dy = p.x - f.x, p.y - f.y
            # bulls in the rut (and cornered bison) may stand their ground
            if p.kind == "bison" and self.rnd.random() < 0.01 and math.hypot(dx, dy) < 70:
                p.fleeing_until = self.t + 1
            speed = speed_base * (0.45 + 0.55 * p.stamina / 100) * (0.6 + 0.4 * p.hp / p.maxhp)
            p.stamina = max(0, p.stamina - (9 if p.kind != "hare" else 5) * dt)
            jitter = math.sin(self.t * 1.7 + p.id) * 0.5
            ang = math.atan2(dy, dx) + jitter
            self._move(p, math.cos(ang), math.sin(ang), speed, dt, wolfish=False, avoid_water=True)
            return
        p.stamina = min(100, p.stamina + 5 * dt)
        # grazing and wandering together as a herd
        if p.wander is None or math.hypot(p.wander[0] - p.x, p.wander[1] - p.y) < 12 or self.rnd.random() < 0.003:
            if p.herd is not None:
                mates = [q for q in self.prey if q.herd == p.herd and not q.dead]
                hx = sum(q.x for q in mates) / len(mates)
                hy = sum(q.y for q in mates) / len(mates)
                drift = getattr(self, "_drift", {}).get(p.herd)
                if drift is None or self.rnd.random() < 0.01:
                    drift = (self.rnd.uniform(-1, 1), self.rnd.uniform(-1, 1))
                    self.__dict__.setdefault("_drift", {})[p.herd] = drift
                p.wander = (hx + drift[0] * 120 + self.rnd.uniform(-60, 60), hy + drift[1] * 120 +
                            self.rnd.uniform(-60, 60))
            else:
                p.wander = (p.x + self.rnd.uniform(-120, 120), p.y + self.rnd.uniform(-120, 120))
            if self.rnd.random() < 0.5:
                p.wander = (p.x, p.y)                          # stop and graze
        dx, dy = p.wander[0] - p.x, p.wander[1] - p.y
        if math.hypot(dx, dy) > 6:
            self._move(p, dx, dy, speed_base * 0.18, dt, wolfish=False, avoid_water=True)
        else:
            p.vx = p.vy = 0

    def _alarm(self, p, wolf):
        until = self.t + self.rnd.uniform(6, 10)
        for q in self.prey:
            if not q.dead and ((p.herd is not None and q.herd == p.herd) or q is p) and \
                    math.hypot(q.x - p.x, q.y - p.y) < 400:
                q.fleeing_until = until
                q.fear_from = wolf

    def _all_wolves(self):
        out = [w for w in self.pack if not w.dead and not (w.pup and w.age < 120)]
        for rp in self.rivals:
            out += [w for w in rp.wolves if not w.dead]
        return out

    # ---- bears and cougars ------------------------------------------------------------------------------------
    def _beast_ai(self, b, dt):
        b.cool = max(0.0, b.cool - dt)
        b.timer += dt
        if b.leaving or b.timer > DAY_SECONDS * 1.2:
            b.leaving = True
            ex = TILE * 2 if b.x < WORLD / 2 else WORLD - TILE * 2
            self._move(b, ex - b.x, 0.001, b.speed * 0.7, dt, wolfish=False)
            if self._off_map(b) or abs(b.x - ex) < 30:
                b.dead = True
            return
        target = b.goal if isinstance(b.goal, Creature) and not b.goal.dead else None
        if b.kind == "cougar" and target is None:
            pups = [w for w in self.pack if w.pup and not w.dead]
            if pups:
                target = min(pups, key=lambda w: dist(w, b))
        if target is not None:
            d = dist(b, target)
            if d > 40:
                self._move(b, target.x - b.x, target.y - b.y, b.speed * (0.75 if b.kind == "bear" else 0.9), dt,
                           wolfish=False)
            elif b.cool <= 0:
                b.cool = 1.7 if b.kind == "bear" else 1.5
                dmg = (15 if b.kind == "bear" else 11) * self.rnd.uniform(0.7, 1.2)
                if isinstance(target, Wolf):
                    self._hurt(target, dmg, None, f"killed by the {b.kind}")
                    near = [w for w in self.pack if not w.dead and dist(w, b) < 60]
                    if near and self.rnd.random() < 0.5:
                        b.goal = self.rnd.choice(near)        # it lashes out at whoever is closest
                    if target.dead and target.pup:
                        self.say(f"The {b.kind} killed the pup {target.name}.", "bad")
                    if target.dead:
                        b.goal = None
                elif isinstance(target, Prey):
                    target.hp -= dmg
                    if target.hp <= 0:
                        self._kill_prey(target, b)
            return
        # a bear makes for the nearest kill and eats it
        if b.kind == "bear":
            c = min(self.carcasses, key=lambda c: math.hypot(c.x - b.x, c.y - b.y), default=None)
            if c is not None:
                if math.hypot(c.x - b.x, c.y - b.y) > 34:
                    self._move(b, c.x - b.x, c.y - b.y, b.speed * 0.6, dt, wolfish=False)
                else:
                    c.meat -= 7 * dt
                    b.vx = b.vy = 0
                return
        if b.goal is None or not isinstance(b.goal, tuple) or math.hypot(b.goal[0] - b.x, b.goal[1] - b.y) < 20:
            b.goal = self.map.random_land(self.rnd)
        self._move(b, b.goal[0] - b.x, b.goal[1] - b.y, b.speed * 0.3, dt, wolfish=False)

    # ---- hunger, health, growing up ---------------------------------------------------------------------------------
    def _needs(self, dt, winter):
        rate = 100 / (2.6 * DAY_SECONDS) * (1.5 if winter else 1.0)
        blizzard = self.blizzard_until > self.t
        den = self.map.den
        for w in self.pack:
            if w.dead:
                continue
            w.age += dt / DAY_SECONDS
            r = rate * (1.1 if w.pup else 1.0) * (1.4 if w.pose == "run" else 1.0) * (0.7 if w.pose in ("lie", "sleep")
                                                                                      else 1.0)
            w.hunger = max(0.0, w.hunger - r * dt)
            if w.hunger < 22 and not getattr(w, "warned", False) and w is not self.player:
                w.warned = True
                self.say(f"The pup {w.name} is hungry - bring food to the den!" if w.pup else
                         f"{w.name} is starving.", "bad")
            elif w.hunger > 40:
                w.warned = False
            if w.hunger <= 0:
                w.hp -= (0.3 if not w.pup else 0.22) * dt
                if w.hp <= 0:
                    self._die(w, "starved")
                    continue
            elif w.hunger > 55 and not w.mange:
                w.hp = min(w.maxhp, w.hp + 0.3 * dt)
            if w.mange:
                w.hp -= 0.05 * dt
            if blizzard and self.map.tile_at(w.x, w.y) != "forest" and \
                    math.hypot(w.x - den[0], w.y - den[1]) > 160:
                w.hp -= 0.12 * dt
            if w.hp <= 0 and not w.dead:
                self._die(w, "the cold" if blizzard else "")
        for rp in self.rivals:
            for w in rp.wolves:
                w.hunger = max(0.0, w.hunger - rate * dt * 0.6)

    def _check_pack(self):
        alive = [w for w in self.pack if not w.dead]
        adults = [w for w in alive if not w.pup]
        self.stats["max_pack"] = max(self.stats["max_pack"], len(alive))
        if self.player is None or self.player.dead:
            if adults:
                self.player = max(adults, key=lambda w: w.hp)
                self.player.guard = False
                self.say(f"You now lead the pack as {self.player.name}.", "big")
            else:
                self.player = None
                self.over = True
                self.say("The last of your pack is gone. The valley falls quiet.", "big")
        self.pack = [w for w in self.pack if not w.dead or w is self.player]

    # ---- each new day ------------------------------------------------------------------------------------------
    def _new_day(self):
        first = self.last_day < 0
        self.last_day = self.day
        season, dos = self.season, self.day_of_season
        if not first and dos == 1:
            self.say(f"{season.title()} has come to the valley (year {self.year}).", "big")
            if season == "spring":
                self._new_year()
            if season == "autumn":
                for w in self.pack:
                    if w.pup and not w.dead:
                        w.strength = 0.8
                self.say("The pups are big enough to travel with the pack now.", "pack")
            if season == "winter":
                self.say("Winter: deep snow slows everyone (the elk worst of all), and food is scarce.", "info")
        if season == "spring" and dos == 2 and self.flags["pups_year"] != self.year:
            self._pups()
        self._populate()
        if first:
            return
        # the day's events
        r = self.rnd.random
        chances = {
            "bear": {"spring": 0.3, "summer": 0.25, "autumn": 0.3, "winter": 0.0},
            "cougar": {"spring": 0.2, "summer": 0.18, "autumn": 0.12, "winter": 0.08},
            "raid": {"spring": 0.1, "summer": 0.12, "autumn": 0.16, "winter": 0.28},
            "blizzard": {"spring": 0.0, "summer": 0.0, "autumn": 0.05, "winter": 0.4},
            "lone": {"spring": 0.08, "summer": 0.1, "autumn": 0.1, "winter": 0.06},
            "mange": {"spring": 0.03, "summer": 0.05, "autumn": 0.04, "winter": 0.06},
            "migration": {"spring": 0.0, "summer": 0.0, "autumn": 0.35, "winter": 0.0},
        }
        guard = self.territory_strength(*self.map.den)
        for ev, by_season in chances.items():
            p = by_season[season]
            if ev == "raid":
                p *= (1.0 - 0.6 * guard)
            if r() < p:
                getattr(self, "_ev_" + ev)()

    def _ev_bear(self):
        x, y = self.map.random_land(self.rnd, near=(self.rnd.choice((3 * TILE, WORLD - 3 * TILE)),
                                                     self.rnd.uniform(WORLD * 0.2, WORLD * 0.8)), spread=200)
        self.beasts.append(Beast(x, y, "bear"))
        self.say("A grizzly bear has come down into the valley - it will steal any kill it finds.", "bad")

    def _ev_cougar(self):
        if not any(w.pup and not w.dead for w in self.pack):
            return
        den = self.map.den
        x, y = self.map.random_land(self.rnd, near=den, spread=900)
        self.beasts.append(Beast(x, y, "cougar"))
        self.say("A cougar is stalking the den - the pups are in danger!", "bad")

    def _ev_raid(self):
        rp = self.rnd.choice([r for r in self.rivals if r.wolves] or [None])
        if rp is None:
            return
        raiders = rp.wolves[:self.rnd.randint(2, min(3, len(rp.wolves)))]
        for w in raiders:
            w.raiding = True
            w.raid_until = self.t + DAY_SECONDS * 0.4
        self.say(f"Wolves from {rp.name} are heading for your den!", "bad")

    def _ev_blizzard(self):
        self.blizzard_until = self.t + DAY_SECONDS * 0.45
        self.say("A blizzard is blowing in! Shelter in the forest or at the den.", "bad")

    def _ev_lone(self):
        alive = [w for w in self.pack if not w.dead]
        if len(alive) >= 10 or self.player is None:
            return
        sex = self.rnd.choice(("male", "female"))
        name = self.rnd.choice(MALE_NAMES if sex == "male" else FEMALE_NAMES)
        x, y = self.player.x + self.rnd.choice((-1, 1)) * 260, self.player.y + self.rnd.uniform(-120, 120)
        w = Wolf(x, y, name, self.rnd.choice(list(art.COATS)), sex, age_days=600)
        w.hunger = 30
        self.prompt = ("lone", w)
        self.say(f"A lone {sex} wolf, {name}, wants to join your pack. Press Y to welcome them or N to send them "
                 "away.", "big")

    def answer(self, yes):
        if not self.prompt:
            return
        _kind, w = self.prompt
        self.prompt = None
        if yes:
            self.pack.append(w)
            self.say(f"{w.name} joins the pack!", "good")
        else:
            self.say(f"{w.name} lopes away to find another valley.", "info")

    def _ev_mange(self):
        cands = [w for w in self.pack if not w.dead and not w.pup and not w.mange]
        if cands:
            w = self.rnd.choice(cands)
            w.mange = True
            w.mange_meal = 0
            self.say(f"{w.name} has caught mange. Only plenty of food will see it through.", "bad")

    def _ev_migration(self):
        before = len(self.prey)
        cx, cy = self.map.random_land(self.rnd, near=(WORLD - 8 * TILE, WORLD * 0.5), spread=400)
        hid = self.rnd.randint(1, 10 ** 9)
        for i in range(self.rnd.randint(8, 12)):
            x, y = self.map.random_land(self.rnd, near=(cx, cy), spread=110)
            self.prey.append(Prey(x, y, "elk", herd=hid, bull=(i == 0)))
        if len(self.prey) > before:
            self.say("A big elk herd is migrating through the east of the valley.", "good")

    def _pups(self):
        alive = [w for w in self.pack if not w.dead and not w.pup]
        mothers = [w for w in alive if w.sex == "female" and w.age > 700]
        fathers = [w for w in alive if w.sex == "male" and w.age > 700]
        if not mothers or not fathers:
            return
        self.flags["pups_year"] = self.year
        mom = mothers[0]
        n = self.rnd.randint(2, 5)
        names = []
        dx, dy = self.map.den
        for _ in range(n):
            sex = self.rnd.choice(("male", "female"))
            name = self.rnd.choice([x for x in (MALE_NAMES if sex == "male" else FEMALE_NAMES)
                                    if x not in [w.name for w in self.pack]] or ["Pup"])
            coat = self.rnd.choice([mom.coat, fathers[0].coat, self.rnd.choice(list(art.COATS))])
            pup = Wolf(dx + self.rnd.uniform(-30, 30), dy + self.rnd.uniform(5, 30), name, coat, sex, age_days=0,
                       pup=True)
            pup.hunger = 70
            self.pack.append(pup)
            names.append(name)
        self.stats["pups_born"] += n
        self.say(f"{mom.name} has given birth to {n} pups at the den: {', '.join(names)}! Bring them food - eat "
                 "your fill at a kill, keep eating to carry more, then go home.", "big")

    def _new_year(self):
        self.stats["years"] += 1
        for w in self.pack:
            if w.dead:
                continue
            if w.pup:
                w.pup = False
                w.maxhp = 100.0
                w.strength = 1.0
                self.stats["pups_raised"] += 1
                self.say(f"{w.name} is a yearling now - a full member of the pack.", "good")
            elif w.age > 8 * 365 and self.rnd.random() < 0.35 and w is not self.player:
                w.dead = True
                self.say(f"Old {w.name} passed away peacefully over the winter.", "bad")
        alive = [w for w in self.pack if not w.dead]
        yearlings = [w for w in alive if 300 < w.age < 500 and w is not self.player]
        if len(alive) > 8 and yearlings and self.rnd.random() < 0.5:
            w = self.rnd.choice(yearlings)
            w.dead = True
            self.say(f"{w.name} has left the pack to find a mate and a territory of their own.", "info")
        for rp in self.rivals:                              # rival packs have pups too
            while len(rp.wolves) < 4:
                x, y = self.map.random_land(self.rnd, near=rp.den, spread=150)
                rp.wolves.append(Wolf(x, y, self.rnd.choice(MALE_NAMES), rp.coat, "male", pack=self.rivals.index(rp)))

    # ---- saving --------------------------------------------------------------------------------------------
    def to_json(self):
        alive = [w for w in self.pack if not w.dead]
        return {"seed": self.seed, "t": self.t, "pack": [w.to_json() for w in alive],
                "player": alive.index(self.player) if self.player in alive else 0,
                "markers": [[round(m.x), round(m.y), round(m.strength, 3)] for m in self.markers],
                "carcasses": [[round(c.x), round(c.y), c.kind, round(c.meat, 1), round(c.age)] for c in self.carcasses],
                "stats": self.stats, "flags": self.flags, "log": self.log[-30:],
                "rivals": [len(rp.wolves) for rp in self.rivals]}

    @classmethod
    def from_json(cls, d):
        w = cls(d["seed"])
        w.t = d["t"]
        w.last_day = w.day
        w.pack = [Wolf.from_json(x) for x in d["pack"]]
        w.player = w.pack[d.get("player", 0)] if w.pack else None
        w.markers = [Marker(*m) for m in d.get("markers", [])]
        w.carcasses = []
        for x, y, kind, meat, age in d.get("carcasses", []):
            c = Carcass(x, y, kind, meat)
            c.age = age
            w.carcasses.append(c)
        w.stats.update(d.get("stats", {}))
        w.flags.update(d.get("flags", {}))
        w.log = [tuple(x) for x in d.get("log", [])]
        for rp, n in zip(w.rivals, d.get("rivals", [])):
            rp.wolves = rp.wolves[:max(1, n)]
        w.prey = []
        w._populate(initial=True)
        w.say(f"Welcome back. It is day {w.day_of_season} of {w.season}, year {w.year}.", "big")
        return w
