"""Claudeita's world: a tall grid of materials, made a few rows at a time as you descend, with the loose ones (sand,
snow, water, lava, acid, fire) simulated only where something is happening.

The grid is a bytearray of material ids; `image` holds every cell's colour, updated only where a cell changes, so a
frame just draws the camera's part of it. Five biomes are stacked, each ending in a boss arena and a sanctuary."""
import random
from array import array

from PySide6.QtGui import QColor, QImage

W = 512
BIOME_H = 700
SURFACE = 70
ARENA_H = 130
SANCTUARY_H = 80

AIR, DIRT, ROCK, BEDROCK, SAND, WATER, LAVA, ACID, GOLD, WOOD, ICE, FUNGUS, OBSIDIAN, CRYSTAL, FIRE, SNOW = range(16)
NAMES = ["air", "dirt", "rock", "bedrock", "sand", "water", "lava", "acid", "gold", "wood", "ice", "fungus",
         "obsidian", "crystal", "fire", "snow"]
SOLID = {DIRT, ROCK, BEDROCK, GOLD, WOOD, ICE, FUNGUS, OBSIDIAN, CRYSTAL, SAND, SNOW}
LIQUID = {WATER, LAVA, ACID}
POWDER = {SAND, SNOW}
SOFT = {DIRT, SAND, SNOW, FUNGUS, WOOD, ICE}               # what a digging bolt gets through
UNBREAKABLE = {BEDROCK}
BURNS = {WOOD, FUNGUS}
COLOURS = {AIR: None, DIRT: "#6B4A2E", BEDROCK: "#1E1B22", SAND: "#C9A65A", WATER: "#2F6FD0", LAVA: "#F2561D",
           ACID: "#7CE33A", GOLD: "#F2C230", WOOD: "#7A5230", ICE: "#A9DDF3", FUNGUS: "#8E4FB0", OBSIDIAN: "#2A1E36",
           CRYSTAL: "#D06BF0", FIRE: "#FFB020", SNOW: "#EEF4FA"}

BIOMES = [
    {"name": "The Mines", "rock": "#5B4636", "sky": "#140F0C", "soft": DIRT, "liquid": WATER, "extra": WOOD,
     "boss": "Gravelmaw", "enemies": ["slime", "bat", "hiisi", "slime"]},
    {"name": "The Frozen Depths", "rock": "#6E8296", "sky": "#0B1118", "soft": SNOW, "liquid": WATER, "extra": ICE,
     "boss": "Rimecaller", "enemies": ["bat", "frost", "hiisi", "slime"]},
    {"name": "The Fungal Caverns", "rock": "#4B3A5E", "sky": "#100B14", "soft": FUNGUS, "liquid": ACID, "extra": FUNGUS,
     "boss": "Mother Spore", "enemies": ["slime", "spore", "bat", "worm"]},
    {"name": "The Magma Vault", "rock": "#4A2420", "sky": "#140806", "soft": SAND, "liquid": LAVA, "extra": OBSIDIAN,
     "boss": "Cinder Colossus", "enemies": ["imp", "hiisi", "worm", "turret"]},
    {"name": "The Hollow Heart", "rock": "#2A2333", "sky": "#07050A", "soft": OBSIDIAN, "liquid": LAVA,
     "extra": CRYSTAL, "boss": "The Unmaker", "enemies": ["ghost", "imp", "turret", "frost"]},
]
H = SURFACE + BIOME_H * len(BIOMES)


def biome_at(y):
    return max(0, min(len(BIOMES) - 1, (y - SURFACE) // BIOME_H))


def biome_top(b):
    return SURFACE + b * BIOME_H


def arena_rect(b):
    """(x0, y0, x1, y1) of a biome's boss arena (inside its bedrock walls)."""
    top = biome_top(b) + BIOME_H - ARENA_H - SANCTUARY_H
    return 56, top + 6, W - 56, top + ARENA_H - 6


def sanctuary_rect(b):
    top = biome_top(b) + BIOME_H - SANCTUARY_H
    return 120, top + 8, W - 120, top + SANCTUARY_H - 8


def _shade(hex_colour, k, seed):
    """A cell's colour: the material's, a little lighter or darker by its position (the grain)."""
    c = QColor(hex_colour)
    j = ((seed * 2654435761) >> 7) % 23 - 11
    return (0xFF << 24) | (max(0, min(255, c.red() + j + k)) << 16) | (max(0, min(255, c.green() + j + k)) << 8) | \
        max(0, min(255, c.blue() + j + k))


class World:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randrange(1 << 30)
        self.rng = random.Random(self.seed)
        self.cells = bytearray(W * H)
        self.image = QImage(W, H, QImage.Format_ARGB32)
        self.image.fill(0xFF000000)
        self.made = 0                              # rows made so far
        self.active = set()                        # cells that may move
        self.fire_life = {}
        self.spawns = []                           # (kind, x, y) for the game to bring to life
        self.items = []                            # ("wand"/"spell"/"heart"/"gold", x, y)
        self.gates = {}                            # biome -> cells of its arena's lower gate
        self._plans = {}
        self.changed = 0

    # ---- reading and writing ----
    def get(self, x, y):
        if 0 <= x < W and 0 <= y < H:
            return self.cells[y * W + x]
        return BEDROCK

    def solid(self, x, y):
        return self.get(int(x), int(y)) in SOLID

    def colour_of(self, m, x, y):
        if m == AIR:                               # (open cave: near-black, the faintest grain)
            c = QColor(BIOMES[biome_at(y)]["sky"])
            j = ((x * 92821 + y * 68917) >> 5) % 5
            return (0xFF << 24) | ((c.red() + j) << 16) | ((c.green() + j) << 8) | (c.blue() + j)
        if m == ROCK:
            return _shade(BIOMES[biome_at(y)]["rock"], 0, x * 92821 + y)
        return _shade(COLOURS[m], 0, x * 92821 + y)

    def set(self, x, y, m, wake=True):
        if not (0 <= x < W and 0 <= y < H):
            return
        i = y * W + x
        if self.cells[i] == m:
            return
        self.cells[i] = m
        self.image.setPixel(x, y, self.colour_of(m, x, y))
        self.changed += 1
        if m == FIRE:
            self.fire_life[i] = self.rng.randint(30, 70)
        if wake:
            self.wake(x, y)

    def wake(self, x, y):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H:
                    m = self.cells[yy * W + xx]
                    if m in LIQUID or m in POWDER or m == FIRE:
                        self.active.add(yy * W + xx)

    # ---- making the world ----
    def _plan(self, b):
        """A biome's layout before its rows are made: the noise lattice, a winding way down, where the pools go."""
        if b in self._plans:
            return self._plans[b]
        rng = random.Random(self.seed * 31 + b)
        top = biome_top(b)
        lat = {}
        for scale in (48, 16):
            cols, rows = W // scale + 2, BIOME_H // scale + 2
            lat[scale] = [[rng.random() for _ in range(cols)] for _ in range(rows)]
        path = []                                  # a winding passage from the top to the arena
        x = W // 2 if b == 0 else W // 2 + rng.randint(-60, 60)
        arena_top = BIOME_H - ARENA_H - SANCTUARY_H
        for y in range(BIOME_H):
            if y > arena_top - 160:                # (steering back to the middle, where the arena's door is)
                x += (1 if x < W // 2 else -1 if x > W // 2 else 0)
            elif y % 3 == 0:
                x += rng.choice((-2, -1, 0, 1, 2)) + (1 if x < 120 else -1 if x > W - 120 else 0)
            path.append(x)
        ix = {s: [(x // s, (x % s) / s) for x in range(W)] for s in (48, 16)}
        plan = {"lat": lat, "path": path, "ix": ix, "rng": rng, "top": top}
        self._plans[b] = plan
        return plan

    def make_rows(self, upto):
        """Make rows until `upto` (and finish any band of features that completes)."""
        upto = min(H, upto)
        while self.made < upto:
            self._make_row(self.made)
            self.made += 1
            y = self.made
            if y > SURFACE and (y - SURFACE) % 140 == 0:
                self._features(y - 140, y)

    def _make_row(self, y):
        row = array("I", [0]) * W
        out = self.cells
        if y < SURFACE:                            # the surface: a ledge to start from, sky above
            for x in range(W):
                m = BEDROCK if x < 3 or x >= W - 3 else (ROCK if y > SURFACE - 6 and abs(x - W // 2) > 18 else AIR)
                out[y * W + x] = m
                row[x] = self.colour_of(m, x, y) if m else 0xFF0A0A12
            self._row_image(y, row)
            return
        b = biome_at(y)
        bio = BIOMES[b]
        plan = self._plan(b)
        ly = y - plan["top"]
        a0, a1 = self._lerp_rows(plan["lat"][48], ly / 48), self._lerp_rows(plan["lat"][16], ly / 16)
        n48 = [a0[i] + (a0[i + 1] - a0[i]) * t for i, t in plan["ix"][48]]
        n16 = [a1[i] + (a1[i + 1] - a1[i]) * t for i, t in plan["ix"][16]]
        cx = plan["path"][ly]
        arena_top = BIOME_H - ARENA_H - SANCTUARY_H
        soft, extra = bio["soft"], bio["extra"]
        for x in range(W):
            n = n48[x] * 0.65 + n16[x] * 0.35
            if x < 3 or x >= W - 3:
                m = BEDROCK
            elif n > 0.56:
                m = ROCK
                if n16[x] > 0.9 and n48[x] > 0.62:             # gold: small veins deep in the rock
                    m = GOLD
                elif n48[x] > 0.86 and n16[x] < 0.45:          # the biome's own stone, in patches
                    m = extra if extra not in (WOOD,) else ROCK
            elif n > 0.5:
                m = soft
            else:
                m = AIR
            if abs(x - cx) < 9 and ly < arena_top:  # the way down
                m = AIR
            out[y * W + x] = m
        if ly >= arena_top:                        # the boss arena and the sanctuary below it
            self._structures(b, y, ly - arena_top)
        if ly < 10 and b > 0:                      # the hole from the sanctuary above into this biome
            for x in range(W // 2 - 10, W // 2 + 10):
                out[y * W + x] = AIR
        for x in range(W):
            m = out[y * W + x]
            row[x] = self.colour_of(m, x, y)
        self._row_image(y, row)

    @staticmethod
    def _lerp_rows(lat, fy):
        i = int(fy)
        t = fy - i
        r0, r1 = lat[min(i, len(lat) - 1)], lat[min(i + 1, len(lat) - 1)]
        t = t * t * (3 - 2 * t)
        return [a + (b - a) * t for a, b in zip(r0, r1)]

    def _structures(self, b, y, ay):
        """The arena (a big bedrock-walled hall with a gate in its floor) and the sanctuary under it."""
        out = self.cells
        x0, y0, x1, y1 = arena_rect(b)
        s0, sy0, s1, sy1 = sanctuary_rect(b)
        base = y * W
        if ay < ARENA_H:
            for x in range(W):
                inside = x0 <= x < x1 and y0 <= y < y1
                wall = (x0 - 6 <= x < x1 + 6) and (y0 - 6 <= y < y1 + 6) and not inside
                if inside:
                    out[base + x] = AIR
                elif wall:
                    out[base + x] = BEDROCK
            if y0 - 6 <= y < y0:                   # a way in from the cave above
                for x in range(W // 2 - 9, W // 2 + 9):
                    out[base + x] = AIR
            if y1 <= y < y1 + 6:                   # the gate down (opens when the boss falls)
                gate = self.gates.setdefault(b, [])
                for x in range(W // 2 - 9, W // 2 + 9):
                    gate.append((x, y))
        else:
            for x in range(W):
                inside = s0 <= x < s1 and sy0 <= y < sy1
                if inside or (y < sy0 and abs(x - W // 2) < 9):     # (the way in from the arena's gate)
                    out[base + x] = AIR
                elif s0 - 8 <= x < s1 + 8 or y < sy0:
                    out[base + x] = BEDROCK
            if y >= sy1 and b < len(BIOMES) - 1:   # a hole in the sanctuary floor: the way to the next biome
                for x in range(W // 2 - 10, W // 2 + 10):
                    out[base + x] = AIR
            if y == sy1 - 1:
                if b < len(BIOMES) - 1:
                    self.items.append(("fountain", s0 + 30, y))
                    for i, kind in enumerate(("wand", "spell", "spell", "wand", "spell")):
                        self.items.append((f"shop_{kind}", s0 + 70 + i * 34, y, b))

    def _row_image(self, y, row):
        bits = self.image.bits()
        start = y * W * 4
        bits[start:start + W * 4] = row.tobytes()

    def _features(self, y0, y1):
        """Pools, enemies and finds for a band of rows that's now complete."""
        b = biome_at(y0)
        bio = BIOMES[b]
        rng = self.rng
        arena_top = biome_top(b) + BIOME_H - ARENA_H - SANCTUARY_H
        y1 = min(y1, arena_top - 4)
        if y1 - y0 < 20:
            return
        for _ in range(6):                         # pools on cave floors
            spot = self._floor_spot(rng, y0 + 5, y1 - 2)
            if spot:
                self._pool(spot[0], spot[1], bio["liquid"] if rng.random() < 0.75 else WATER, rng.randint(3, 7))
        if b < 3 and rng.random() < 0.6:           # a wooden platform or two in the upper caves
            for _try in range(30):
                x, y = rng.randint(30, W - 60), rng.randint(y0 + 5, y1 - 5)
                if all(self.get(x + i, y) == AIR for i in range(0, 30, 5)):
                    for i in range(rng.randint(14, 30)):
                        if self.get(x + i, y) == AIR:
                            self.set(x + i, y, WOOD, wake=False)
                    break
        depth = b + (y0 - biome_top(b)) / BIOME_H
        for _ in range(int(6 + depth * 1.6)):      # enemies (flyers anywhere open; the rest on a floor)
            kind = rng.choice(bio["enemies"])
            if kind in ("bat", "imp", "ghost", "frost"):
                for _try in range(40):
                    x, y = rng.randint(10, W - 10), rng.randint(y0 + 4, y1 - 2)
                    if self.get(x, y) == AIR and self.get(x, y - 6) == AIR:
                        self.spawns.append((kind, x, y, b))
                        break
            else:
                spot = self._floor_spot(rng, y0 + 4, y1 - 2)
                if spot:
                    self.spawns.append((kind, spot[0], spot[1], b))
        for kind, n in (("wand", 0.6), ("spell", 1.6), ("heart", 0.2)):
            k = int(n) + (1 if rng.random() < n % 1 else 0)
            for _ in range(k):
                spot = self._floor_spot(rng, y0 + 4, y1 - 2)
                if spot:
                    self.items.append((kind, spot[0], spot[1], b))

    def _floor_spot(self, rng, y0, y1):
        """A random spot on a cave floor in these rows (air, with something solid under it), or None."""
        for _try in range(30):
            x = rng.randint(12, W - 12)
            y = rng.randint(y0, y1 - 1)
            while y < y1 and self.get(x, y) != AIR:
                y += 1
            while y < y1 and self.get(x, y + 1) == AIR:
                y += 1
            if y < y1 and self.get(x, y) == AIR and self.get(x, y + 1) in SOLID and self.get(x, y - 10) == AIR:
                return x, y
        return None

    def _pool(self, x, y, liquid, depth):
        for dy in range(depth):
            yy = y - dy
            for d in (-1, 1):
                xx = x if d == 1 else x - 1
                for _ in range(60):
                    if self.get(xx, yy) != AIR or self.get(xx, yy + 1) == AIR:
                        break
                    self.set(xx, yy, liquid, wake=False)
                    xx += d

    def open_gate(self, b):
        for x, y in self.gates.get(b, []):
            self.set(x, y, AIR)

    # ---- the loose stuff ----
    def step(self, budget=2500):
        """Move what moves: powders fall, liquids flow, lava meets water, acid eats, fire burns."""
        if not self.active:
            return
        cells = self.cells
        todo = sorted(self.active, reverse=True)[:budget]
        self.active.difference_update(todo)
        rng = self.rng
        for i in todo:
            m = cells[i]
            y, x = divmod(i, W)
            if y >= H - 1:
                continue
            if m == FIRE:
                life = self.fire_life.get(i, 0) - 1
                for dx, dy in ((1, 0), (-1, 0), (0, -1), (0, 1)):
                    n = self.get(x + dx, y + dy)
                    if n in BURNS and rng.random() < 0.08:
                        self.set(x + dx, y + dy, FIRE)
                    elif n == ICE and rng.random() < 0.1:
                        self.set(x + dx, y + dy, WATER)
                    elif n == WATER:
                        life = 0
                if life <= 0:
                    self.fire_life.pop(i, None)
                    self.set(x, y, AIR)
                else:
                    self.fire_life[i] = life
                    if rng.random() < 0.3 and self.get(x, y - 1) == AIR:     # flames rise a little
                        self.set(x, y, AIR)
                        self.set(x, y - 1, FIRE)
                        self.fire_life[(y - 1) * W + x] = life
                    else:
                        self.active.add(i)
                continue
            if m not in LIQUID and m not in POWDER:
                continue
            below = cells[i + W]
            if m in POWDER:
                if below == AIR or below in LIQUID:
                    self._swap(x, y, x, y + 1)
                    continue
                d = rng.choice((-1, 1))
                for dx in (d, -d):
                    if self.get(x + dx, y + 1) in (AIR, WATER):
                        self._swap(x, y, x + dx, y + 1)
                        break
                continue
            # liquids
            if m == LAVA or m == ACID:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = self.get(x + dx, y + dy)
                    if m == LAVA and n == WATER:
                        self.set(x, y, OBSIDIAN)
                        self.set(x + dx, y + dy, AIR)
                        break
                    if m == LAVA and n in BURNS and rng.random() < 0.05:
                        self.set(x + dx, y + dy, FIRE)
                    if m == ACID and n not in (AIR, ACID, BEDROCK, GOLD) and n not in LIQUID and \
                            rng.random() < 0.03:
                        self.set(x + dx, y + dy, AIR)
                        if rng.random() < 0.3:
                            self.set(x, y, AIR)
                        break
                if cells[i] != m:
                    continue
            if below == AIR:
                self._swap(x, y, x, y + 1)
                continue
            d = rng.choice((-1, 1))
            moved = False
            for dx in (d, -d):
                if self.get(x + dx, y + 1) == AIR:
                    self._swap(x, y, x + dx, y + 1)
                    moved = True
                    break
            if moved:
                continue
            for dx in (d, -d):
                reach = 1
                while reach <= 3 and self.get(x + dx * reach, y) == AIR:
                    reach += 1
                if reach > 1:
                    self._swap(x, y, x + dx * (reach - 1), y)
                    break

    def _swap(self, x0, y0, x1, y1):
        a, b = self.get(x0, y0), self.get(x1, y1)
        self.set(x0, y0, b, wake=False)
        self.set(x1, y1, a, wake=False)
        self.wake(x0, y0)
        self.wake(x1, y1)
        for i in (y0 * W + x0, y1 * W + x1):
            m = self.cells[i]
            if m in LIQUID or m in POWDER:
                self.active.add(i)

    # ---- making holes ----
    def carve(self, cx, cy, r, *, hard=True, fire=False, soft_only=False):
        """Clear a disc. Returns how many gold cells it broke (they drop gold)."""
        gold = 0
        r2 = r * r
        cx, cy = int(cx), int(cy)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy > r2:
                    continue
                x, y = cx + dx, cy + dy
                m = self.get(x, y)
                if m == AIR or m in UNBREAKABLE or (m in LIQUID):
                    continue
                if soft_only and m not in SOFT:
                    continue
                if not hard and m in (OBSIDIAN, CRYSTAL) and dx * dx + dy * dy > r2 * 0.3:
                    continue
                if m == GOLD:
                    gold += 1
                self.set(x, y, FIRE if fire and self.rng.random() < 0.25 else AIR)
        for dy in range(-r - 1, r + 2):             # wake whatever sits around the hole
            for dx in (-r - 1, r + 1):
                self.wake(cx + dx, cy + dy)
        for dx in range(-r - 1, r + 2):
            self.wake(cx + dx, cy - r - 1)
        return gold

    def splash(self, cx, cy, m, r=3):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r and self.get(int(cx) + dx, int(cy) + dy) == AIR:
                    self.set(int(cx) + dx, int(cy) + dy, m)

    def freeze(self, cx, cy, r=5):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                x, y = int(cx) + dx, int(cy) + dy
                if dx * dx + dy * dy <= r * r and self.get(x, y) == WATER:
                    self.set(x, y, ICE)
                    self.active.discard(y * W + x)
