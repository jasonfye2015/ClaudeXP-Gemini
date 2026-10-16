"""ClaudeCity's simulation, in the spirit of SimCity Classic: terrain, building with tools, power grids, R/C/I zones
that grow with demand, traffic, pollution, crime, land value, fire, taxes and the yearly budget, disasters,
the city evaluation, and scenarios.

The map is MAP_W x MAP_H tiles. Each tile has terrain (land, water, trees) and at most one structure: a network
piece ('road', 'rail', 'wire', crossings 'road_wire', 'road_rail', 'rail_wire'), 'park', 'rubble', 'fire',
'flood', or a part of a building (zones and big buildings, kept in City.buildings and pointed to by City.owner).
A month passes every few seconds; the screen calls City.tick(dt).
"""
import json
import math
import random

MAP_W, MAP_H = 120, 100
LAND, WATER, TREES = 0, 1, 2
NETWORK = {"road", "rail", "wire", "road_wire", "road_rail", "rail_wire"}

# tool: (cost, size, building kind or None)
TOOLS = {
    "bulldozer": (1, 1, None), "road": (10, 1, None), "rail": (20, 1, None), "wire": (5, 1, None),
    "park": (10, 1, None), "res": (100, 3, "res"), "com": (100, 3, "com"), "ind": (100, 3, "ind"),
    "police": (500, 3, "police"), "fire": (500, 3, "fire"), "stadium": (3000, 4, "stadium"),
    "seaport": (5000, 4, "seaport"), "coal": (3000, 4, "coal"), "nuclear": (5000, 4, "nuclear"),
    "airport": (10000, 6, "airport"), "query": (0, 1, None),
}
TOOL_NAMES = {"bulldozer": "Bulldozer", "road": "Road", "rail": "Rail", "wire": "Power Line", "park": "Park",
              "res": "Residential Zone", "com": "Commercial Zone", "ind": "Industrial Zone",
              "police": "Police Station", "fire": "Fire Station", "stadium": "Stadium", "seaport": "Seaport",
              "coal": "Coal Power Plant", "nuclear": "Nuclear Power Plant", "airport": "Airport", "query": "Query"}
POWER_CAP = {"coal": 60, "nuclear": 160}            # zones a plant can power
R_PEOPLE = [0, 60, 150, 320, 640, 1200]
C_JOBS = [0, 40, 100, 220, 450, 900]
I_JOBS = [0, 60, 140, 300, 600]
MAX_LEVEL = {"res": 5, "com": 5, "ind": 4}
SPEEDS = {"Paused": 0, "Slow": 6.0, "Medium": 3.0, "Fast": 1.5, "Fastest": 0.6}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
LEVELS = {"Easy": 20000, "Medium": 10000, "Hard": 5000}


class Building:
    def __init__(self, kind, x, y, size, level=0):
        self.kind, self.x, self.y, self.size, self.level = kind, x, y, size, level
        self.powered = False
        self.age = 0
        self.variant = random.randint(0, 3)

    def centre(self):
        return self.x + self.size / 2, self.y + self.size / 2

    def tiles(self):
        return [(self.x + dx, self.y + dy) for dy in range(self.size) for dx in range(self.size)]

    def to_json(self):
        return [self.kind, self.x, self.y, self.size, self.level, self.variant]


def _noise(seed):
    cache = {}

    def at(ix, iy):
        k = (ix, iy)
        if k not in cache:
            cache[k] = random.Random(hash((seed, ix, iy)) & 0xFFFFFFFF).random()
        return cache[k]

    def value(x, y, s):
        x, y = x / s, y / s
        ix, iy = math.floor(x), math.floor(y)
        fx, fy = x - ix, y - iy
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        a = at(ix, iy) + (at(ix + 1, iy) - at(ix, iy)) * fx
        b = at(ix, iy + 1) + (at(ix + 1, iy + 1) - at(ix, iy + 1)) * fx
        return a + (b - a) * fy
    return lambda x, y: value(x, y, 14) * 0.65 + value(x + 50, y + 30, 5) * 0.35


class City:
    def __init__(self, name="Claudeville", seed=None, level="Easy", year=1900, blank=False):
        self.name = name
        self.seed = seed if seed is not None else random.randint(1, 10 ** 8)
        self.level = level
        self.funds = LEVELS.get(level, 20000)
        self.year, self.month = year, 0
        self.tax = 7
        self.funding = {"road": 100, "police": 100, "fire": 100}
        self.speed = "Medium"
        self.auto_budget = False
        self.auto_bulldoze = True
        self.disasters_on = True
        self.terrain = [[LAND] * MAP_W for _ in range(MAP_H)]
        self.tile = [[None] * MAP_W for _ in range(MAP_H)]
        self.owner = [[None] * MAP_W for _ in range(MAP_H)]
        self.buildings = {}
        self.next_id = 1
        self.powered = set()                      # tiles with power
        self.traffic = [[0] * MAP_W for _ in range(MAP_H)]
        self.burning = {}                         # (x, y) -> months left
        self.flooded = {}
        self.half = (MAP_W // 2, MAP_H // 2)
        hw, hh = self.half
        self.pollution = [[0.0] * hw for _ in range(hh)]
        self.crime = [[0.0] * hw for _ in range(hh)]
        self.landvalue = [[0.0] * hw for _ in range(hh)]
        self.police_cov = [[0.0] * hw for _ in range(hh)]
        self.fire_cov = [[0.0] * hw for _ in range(hh)]
        self.demand = {"res": 0.5, "com": 0.3, "ind": 0.5}
        self.messages = []                        # (text, kind, (x, y) or None)
        self.history = {"res": [], "com": [], "ind": [], "funds": [], "crime": [], "pollution": []}
        self.clock = 0.0
        self.last_budget = None
        self.budget_due = False
        self.year_income = self.year_expense = 0
        self.score = 500
        self.approval = 50
        self.population = 0
        self.last_pop = 0
        self.problems = {}
        self.milestones = set()
        self.sprites = []                         # moving things: monster, tornado, plane crash marker
        self.scenario = None
        self.power_used = self.power_cap = 0
        self.cash_flow = 0
        if not blank:
            self.generate_terrain()
            self.recompute()

    # ---- terrain -----------------------------------------------------------------------------------------
    def generate_terrain(self, water=0.5, trees=0.5):
        rnd = random.Random(self.seed)
        n1, n2 = _noise(self.seed), _noise(self.seed + 7)
        # a river from one edge to another, a lake, coast on one side sometimes
        rx = rnd.uniform(MAP_W * 0.25, MAP_W * 0.75)
        ph = rnd.uniform(0, 6)
        coast = rnd.random() < 0.4
        for y in range(MAP_H):
            cx = rx + math.sin(y * 0.06 + ph) * 14 + (n1(3, y) - 0.5) * 10
            width = 2.2 + 1.5 * water + n2(y, 2) * 2
            for x in range(MAP_W):
                t = LAND
                if abs(x - cx) < width:
                    t = WATER
                if coast and x > MAP_W - 10 - n1(x * 0.3, y) * 14:
                    t = WATER
                if t == LAND and n2(x, y) > 1.05 - trees * 0.55:
                    t = TREES
                self.terrain[y][x] = t
        lx, ly, lr = rnd.randint(15, MAP_W - 15), rnd.randint(15, MAP_H - 15), rnd.randint(3, 6)
        for y in range(ly - lr, ly + lr + 1):
            for x in range(lx - lr * 2, lx + lr * 2 + 1):
                if 0 <= x < MAP_W and 0 <= y < MAP_H and ((x - lx) / (lr * 2)) ** 2 + ((y - ly) / lr) ** 2 < 1:
                    self.terrain[y][x] = WATER

    # ---- reading the map ---------------------------------------------------------------------------------
    def inside(self, x, y):
        return 0 <= x < MAP_W and 0 <= y < MAP_H

    def building_at(self, x, y):
        bid = self.owner[y][x] if self.inside(x, y) else None
        return self.buildings.get(bid) if bid is not None else None

    def has(self, x, y, part):
        """Does this tile carry a road / rail / wire?"""
        if not self.inside(x, y):
            return False
        t = self.tile[y][x]
        if t is None:
            return False
        return t == part or (t.startswith(part + "_") or t.endswith("_" + part))

    def conducts(self, x, y):
        if not self.inside(x, y):
            return False
        if self.owner[y][x] is not None:
            return True
        return self.has(x, y, "wire")

    def date_text(self):
        return f"{MONTHS[self.month]} {self.year}"

    def say(self, text, kind="info", where=None):
        self.messages.append((text, kind, where))
        del self.messages[:-30]

    # ---- building ------------------------------------------------------------------------------------------
    def can_place(self, tool, x, y):
        cost, size, kind = TOOLS[tool]
        if kind:
            for dy in range(size):
                for dx in range(size):
                    tx, ty = x + dx, y + dy
                    if not self.inside(tx, ty) or self.terrain[ty][tx] == WATER or self.owner[ty][tx] is not None:
                        return False
                    t = self.tile[ty][tx]
                    if t is not None and t != "rubble" and not (self.auto_bulldoze and t == "park"):
                        return False
            if kind == "seaport" and not any(self.inside(x + dx, y + dy) and self.terrain[y + dy][x + dx] == WATER
                                             for dx in range(-1, size + 1) for dy in range(-1, size + 1)):
                return False
            return True
        return self.inside(x, y)

    def apply(self, tool, x, y):
        """Use a tool on a tile (the top-left tile for buildings). Returns an error message or None."""
        cost, size, kind = TOOLS[tool]
        if tool == "query":
            return None
        if self.funds < cost:
            return "Insufficient funds."
        if kind:
            if not self.can_place(tool, x, y):
                return "Can't build there."
            for dy in range(size):
                for dx in range(size):
                    self.tile[y + dy][x + dx] = None
                    self.terrain[y + dy][x + dx] = LAND
            b = Building(kind, x, y, size)
            bid = self.next_id
            self.next_id += 1
            self.buildings[bid] = b
            for tx, ty in b.tiles():
                self.owner[ty][tx] = bid
            self.funds -= cost
            self.recompute_power()
            return None
        if not self.inside(x, y):
            return None
        if tool == "bulldozer":
            return self.bulldoze(x, y)
        t, ter = self.tile[y][x], self.terrain[y][x]
        if self.owner[y][x] is not None:
            return None
        extra = 0
        if ter == TREES:
            if not self.auto_bulldoze:
                return "Bulldoze the trees first."
            extra = 1
        if tool == "park":
            if t is not None or ter == WATER:
                return None
            self.tile[y][x] = "park"
            self.funds -= cost + extra
            return None
        if ter == WATER:
            if tool == "wire":
                cost = 25
            elif tool in ("road", "rail"):
                cost = 50                          # a bridge
                if t is not None:
                    return None
                if self.funds < cost:
                    return "Insufficient funds."
            if t is not None:
                return None
        new = self._combine(t, tool)
        if new is None:
            return None if t is not None and (t == tool) else "Can't build there."
        if new == t:
            return None
        self.tile[y][x] = new
        self.terrain[y][x] = WATER if ter == WATER else LAND
        self.funds -= cost + extra
        if "wire" in new:
            self.recompute_power()
        return None

    @staticmethod
    def _combine(t, tool):
        if t in (None, "rubble", "park"):
            return tool
        if t == tool:
            return t
        pair = {frozenset(("road", "wire")): "road_wire", frozenset(("road", "rail")): "road_rail",
                frozenset(("rail", "wire")): "rail_wire"}
        if t in NETWORK and "_" not in t:
            return pair.get(frozenset((t, tool)))
        return None

    def bulldoze(self, x, y):
        if self.funds < 1:
            return "Insufficient funds."
        b = self.building_at(x, y)
        if b is not None:
            self.destroy(b)
            self.funds -= 1 if b.kind in ("res", "com", "ind") else 5
            return None
        t = self.tile[y][x]
        if t is not None:
            self.tile[y][x] = None
            self.funds -= 1
            if "wire" in t:
                self.recompute_power()
        elif self.terrain[y][x] == TREES:
            self.terrain[y][x] = LAND
            self.funds -= 1
        return None

    def destroy(self, b, rubble=True):
        for tx, ty in b.tiles():
            self.owner[ty][tx] = None
            self.tile[ty][tx] = "rubble" if rubble else None
        bid = next((k for k, v in self.buildings.items() if v is b), None)
        if bid is not None:
            del self.buildings[bid]
        self.recompute_power()

    # ---- the monthly simulation --------------------------------------------------------------------------
    def tick(self, dt):
        """Advance the clock; returns True when a month went by."""
        per = SPEEDS.get(self.speed, 0)
        self._sprites(dt)
        if not per or self.budget_due:
            return False
        self.clock += dt
        if self.clock < per:
            return False
        self.clock = 0.0
        self.month_step()
        return True

    def month_step(self):
        self.month += 1
        if self.month >= 12:
            self.month = 0
            self.year += 1
            self._year_end()
        self.recompute()
        self._grow()
        self._fires()
        self._floods()
        self._random_events()
        self._record()
        self._scenario_check()

    def recompute(self):
        self.recompute_power()
        self._traffic()
        self._maps()
        self._demand()
        self._evaluate()

    def recompute_power(self):
        plants = [b for b in self.buildings.values() if b.kind in POWER_CAP]
        powered = set()
        zones_needing = 0
        cap = sum(POWER_CAP[b.kind] for b in plants)
        budget = cap
        seen_buildings = set()
        from collections import deque
        q = deque()
        for b in plants:
            for t in b.tiles():
                q.append(t)
                powered.add(t)
            seen_buildings.add(id(b))
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in powered or not self.conducts(*n):
                    continue
                b = self.building_at(*n)
                if b is not None and id(b) not in seen_buildings:
                    seen_buildings.add(id(b))
                    if b.kind not in POWER_CAP:
                        zones_needing += 1
                        if budget <= 0:
                            continue                  # brownout: this one goes without
                        budget -= 1
                    for t in b.tiles():
                        powered.add(t)
                        q.append(t)
                    continue
                powered.add(n)
                q.append(n)
        self.powered = powered
        for b in self.buildings.values():
            b.powered = (b.x, b.y) in powered
        self.power_used, self.power_cap = zones_needing, cap

    def _road_near(self, b, r=3):
        for dy in range(-r, b.size + r):
            for dx in range(-r, b.size + r):
                x, y = b.x + dx, b.y + dy
                if self.inside(x, y) and (self.has(x, y, "road") or self.has(x, y, "rail")):
                    return True
        return False

    def _traffic(self):
        """Traffic on each road tile: the trips made by developed zones within a few tiles."""
        tr = [[0] * MAP_W for _ in range(MAP_H)]
        for b in self.buildings.values():
            if b.kind not in ("res", "com", "ind") or b.level == 0:
                continue
            trips = b.level * (14 if b.kind == "res" else 18)
            cx, cy = int(b.x + 1), int(b.y + 1)
            for dy in range(-6, 7):
                for dx in range(-6, 7):
                    x, y = cx + dx, cy + dy
                    if self.inside(x, y) and self.has(x, y, "road"):
                        tr[y][x] += trips / (1 + abs(dx) + abs(dy))
        for kind, extra in (("stadium", 60), ("airport", 40), ("seaport", 40)):
            for b in self.buildings.values():
                if b.kind == kind:
                    cx, cy = int(b.x + b.size / 2), int(b.y + b.size / 2)
                    for dy in range(-6, 7):
                        for dx in range(-6, 7):
                            x, y = cx + dx, cy + dy
                            if self.inside(x, y) and self.has(x, y, "road"):
                                tr[y][x] += extra / (1 + abs(dx) + abs(dy))
        rails = sum(1 for y in range(MAP_H) for x in range(MAP_W) if self.has(x, y, "rail"))
        relief = 1 / (1 + rails / 150)                 # trains take cars off the road
        self.traffic = [[min(255, int(v * relief)) for v in row] for row in tr]

    def _maps(self):
        hw, hh = self.half
        pol = [[0.0] * hw for _ in range(hh)]
        crime = [[0.0] * hw for _ in range(hh)]
        dens = [[0.0] * hw for _ in range(hh)]
        lv = [[0.0] * hw for _ in range(hh)]
        police = [[0.0] * hw for _ in range(hh)]
        fire = [[0.0] * hw for _ in range(hh)]
        for y in range(MAP_H):
            row_tr = self.traffic[y]
            for x in range(MAP_W):
                if row_tr[x] > 40:
                    pol[y // 2][x // 2] += row_tr[x] * 0.25
        res_pts = []
        for b in self.buildings.values():
            cx, cy = int(b.x + b.size / 2) // 2, int(b.y + b.size / 2) // 2
            cx, cy = min(hw - 1, cx), min(hh - 1, cy)
            if b.kind == "ind":
                pol[cy][cx] += 40 + b.level * 60
            elif b.kind == "coal":
                pol[cy][cx] += 500
            elif b.kind in ("airport", "seaport"):
                pol[cy][cx] += 200
            if b.kind in ("res", "com"):
                dens[cy][cx] += b.level * (40 if b.kind == "res" else 30)
                if b.kind == "res" and b.level:
                    res_pts.append((cx, cy, b.level))
            if b.kind in ("police", "fire") and b.powered:
                fund = self.funding["police" if b.kind == "police" else "fire"] / 100
                grid = police if b.kind == "police" else fire
                r = 10
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        x, y = cx + dx, cy + dy
                        if 0 <= x < hw and 0 <= y < hh:
                            d = math.hypot(dx, dy)
                            if d <= r:
                                grid[y][x] += 100 * fund * (1 - d / (r + 1))
        pol = self._blur(self._blur(pol))
        # land value: near the centre of town, near water, trees and parks, away from pollution and crime
        if res_pts:
            tw = sum(l for _x, _y, l in res_pts)
            ccx = sum(x * l for x, _y, l in res_pts) / tw
            ccy = sum(y * l for _x, y, l in res_pts) / tw
        else:
            ccx, ccy = hw / 2, hh / 2
        nature = [[0.0] * hw for _ in range(hh)]
        for y in range(MAP_H):
            for x in range(MAP_W):
                t = self.terrain[y][x]
                if t == WATER or t == TREES or self.tile[y][x] == "park":
                    nature[y // 2][x // 2] += 8 if self.tile[y][x] == "park" else 4
        nature = self._blur(self._blur(nature))
        dens = self._blur(dens)
        for y in range(hh):
            for x in range(hw):
                c = max(0.0, dens[y][x] * 1.1 - police[y][x] * 0.9)
                crime[y][x] = min(250.0, c)
        crime = self._blur(crime)
        for y in range(hh):
            for x in range(hw):
                d = math.hypot(x - ccx, y - ccy)
                v = 120 - d * 2.2 + min(60, nature[y][x] * 1.5) - pol[y][x] * 0.35 - crime[y][x] * 0.25
                lv[y][x] = max(0.0, min(250.0, v))
        self.pollution, self.crime, self.landvalue = pol, crime, lv
        self.police_cov, self.fire_cov = police, fire

    @staticmethod
    def _blur(g):
        h, w = len(g), len(g[0])
        out = [[0.0] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                s, n = 0.0, 0
                for dy in (-1, 0, 1):
                    yy = y + dy
                    if 0 <= yy < h:
                        row = g[yy]
                        for dx in (-1, 0, 1):
                            xx = x + dx
                            if 0 <= xx < w:
                                s += row[xx]
                                n += 1
                out[y][x] = s / n
        return out

    def at_half(self, grid, x, y):
        return grid[min(self.half[1] - 1, int(y) // 2)][min(self.half[0] - 1, int(x) // 2)]

    def totals(self):
        res = sum(R_PEOPLE[b.level] for b in self.buildings.values() if b.kind == "res")
        com = sum(C_JOBS[b.level] for b in self.buildings.values() if b.kind == "com")
        ind = sum(I_JOBS[min(b.level, 4)] for b in self.buildings.values() if b.kind == "ind")
        return res, com, ind

    def has_kind(self, kind):
        return any(b.kind == kind for b in self.buildings.values())

    def _demand(self):
        res, com, ind = self.totals()
        self.population = res
        workers = res * 0.55
        jobs = com + ind
        tax_drag = (self.tax - 7) * 0.07
        r = (jobs + 250 - workers) / max(300, workers) - tax_drag
        c = (res * 0.28 + 80 - com) / max(150, res * 0.28) - tax_drag
        i = (res * 0.32 + 200 - ind) / max(200, res * 0.32) - tax_drag
        caps = {}
        if res > 30000 and not self.has_kind("stadium"):
            r = min(r, 0.0)
            caps["res"] = "Residents demand a Stadium."
        if com > 15000 and not self.has_kind("airport"):
            c = min(c, 0.0)
            caps["com"] = "Commerce requires an Airport."
        if ind > 12000 and not self.has_kind("seaport"):
            i = min(i, 0.0)
            caps["ind"] = "Industry requires a Seaport."
        self.caps = caps
        self.demand = {k: max(-1.0, min(1.0, v)) for k, v in (("res", r), ("com", c), ("ind", i))}

    def _grow(self):
        rnd = random
        for b in list(self.buildings.values()):
            if b.kind not in ("res", "com", "ind"):
                continue
            b.age += 1
            cx, cy = b.x + 1, b.y + 1
            access = self._road_near(b)
            s = self.demand[b.kind]
            if not b.powered:
                s -= 0.9
            if not access:
                s -= 0.8
            pol = self.at_half(self.pollution, cx, cy)
            crime = self.at_half(self.crime, cx, cy)
            lv = self.at_half(self.landvalue, cx, cy)
            tr = max((self.traffic[y][x] for x, y in self._ring(b)), default=0)
            if b.kind == "res":
                s += (lv - 60) / 200 - pol / 180 - crime / 220
                if b.level >= 3 and lv < 70 + b.level * 12:
                    s -= 0.4                                  # tall buildings need valuable land
            elif b.kind == "com":
                s += (lv - 50) / 300 - crime / 300
            if tr > 200:
                s -= 0.35
            p_up = 0.18 + 0.25 * max(0.0, s)
            if s > 0.05 and b.level < MAX_LEVEL[b.kind] and rnd.random() < p_up:
                b.level += 1
            elif s < -0.25 and b.level > 0 and rnd.random() < 0.12 + 0.2 * min(1.0, -s):
                b.level -= 1
                if b.level == 0:
                    b.variant = rnd.randint(0, 3)

    def _ring(self, b):
        for d in range(-1, b.size + 1):
            yield (b.x + d, b.y - 1)
            yield (b.x + d, b.y + b.size)
            yield (b.x - 1, b.y + d)
            yield (b.x + b.size, b.y + d)

    def _ring_ok(self, b):
        return [(x, y) for x, y in self._ring(b) if self.inside(x, y)]

    # ---- fire, floods and other trouble ------------------------------------------------------------------------
    def start_fire(self, x, y):
        if self.inside(x, y) and self.terrain[y][x] != WATER:
            b = self.building_at(x, y)
            if b is not None and b.kind in ("fire",):
                return
            self.burning[(x, y)] = random.randint(3, 6)

    def _fires(self):
        rnd = random
        for (x, y), left in list(self.burning.items()):
            cov = self.at_half(self.fire_cov, x, y)
            left -= 1 + (2 if cov > 60 else 1 if cov > 25 else 0)
            b = self.building_at(x, y)
            if b is not None:
                self.destroy(b)
            elif self.tile[y][x] not in (None, "rubble") or self.terrain[y][x] == TREES:
                self.tile[y][x] = None
                if self.terrain[y][x] == TREES:
                    self.terrain[y][x] = LAND
            if cov < 60:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (x + dx, y + dy)
                    if n not in self.burning and self.inside(*n) and rnd.random() < 0.18 and \
                            (self.owner[n[1]][n[0]] is not None or self.terrain[n[1]][n[0]] == TREES):
                        self.burning[n] = rnd.randint(3, 6)
            if left <= 0:
                del self.burning[(x, y)]
                if self.tile[y][x] is None and self.owner[y][x] is None:
                    self.tile[y][x] = "rubble"
            else:
                self.burning[(x, y)] = left

    def _floods(self):
        for (x, y), left in list(self.flooded.items()):
            if left <= 1:
                del self.flooded[(x, y)]
                if self.tile[y][x] == "flood":
                    self.tile[y][x] = None
            else:
                self.flooded[(x, y)] = left - 1

    def _random_events(self):
        rnd = random
        # ordinary fires: more likely in dense, poorly covered places
        for b in list(self.buildings.values()):
            if b.kind in ("res", "com", "ind") and b.level >= 2:
                cov = self.at_half(self.fire_cov, b.x + 1, b.y + 1)
                if rnd.random() < 0.0009 * b.level * (0.2 if cov > 40 else 1.0):
                    self.start_fire(b.x + 1, b.y + 1)
                    self.say("Fire reported!", "bad", (b.x + 1, b.y + 1))
        # roads crumble without funding
        if self.funding["road"] < 70 and rnd.random() < (70 - self.funding["road"]) / 140:
            roads = [(x, y) for y in range(MAP_H) for x in range(MAP_W) if self.has(x, y, "road")]
            if roads:
                x, y = rnd.choice(roads)
                self.tile[y][x] = "rubble" if self.tile[y][x] == "road" else self.tile[y][x]
                self.say("Roads are deteriorating due to lack of funds.", "bad", (x, y))
        if self.disasters_on and rnd.random() < 0.004:
            rnd.choice([self.disaster_fire, self.disaster_tornado, self.disaster_flood])()
        nukes = [b for b in self.buildings.values() if b.kind == "nuclear"]
        if self.disasters_on and nukes and rnd.random() < 0.0008:
            self.disaster_meltdown(rnd.choice(nukes))

    # ---- disasters -------------------------------------------------------------------------------------------
    def disaster_fire(self):
        cands = [b for b in self.buildings.values()] or None
        if cands:
            b = random.choice(cands)
            x, y = b.x + 1, b.y + 1
        else:
            x, y = random.randrange(MAP_W), random.randrange(MAP_H)
        self.start_fire(x, y)
        self.say("Fire reported!", "bad", (x, y))

    def disaster_flood(self):
        shore = [(x, y) for y in range(MAP_H) for x in range(MAP_W) if self.terrain[y][x] == LAND and any(
            self.inside(x + dx, y + dy) and self.terrain[y + dy][x + dx] == WATER for dx, dy in
            ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        if not shore:
            return
        sx, sy = random.choice(shore)
        for y in range(sy - 6, sy + 7):
            for x in range(sx - 6, sx + 7):
                if self.inside(x, y) and self.terrain[y][x] == LAND and math.hypot(x - sx, y - sy) < 6 * random.uniform(
                        0.6, 1.1):
                    b = self.building_at(x, y)
                    if b is not None and b.kind in ("res", "com", "ind"):
                        self.destroy(b, rubble=False)
                    elif self.owner[y][x] is not None:
                        continue
                    self.tile[y][x] = "flood"
                    self.flooded[(x, y)] = random.randint(3, 6)
        self.say("Flooding reported!", "bad", (sx, sy))

    def disaster_tornado(self):
        x, y = random.uniform(10, MAP_W - 10), random.uniform(10, MAP_H - 10)
        self.sprites.append({"kind": "tornado", "x": x, "y": y, "ang": random.uniform(0, 6.28), "life": 18.0})
        self.say("Tornado reported!", "bad", (int(x), int(y)))

    def disaster_quake(self):
        cx, cy = random.uniform(30, MAP_W - 30), random.uniform(30, MAP_H - 30)
        for _ in range(80):
            x, y = int(cx + random.gauss(0, 14)), int(cy + random.gauss(0, 14))
            if not self.inside(x, y):
                continue
            b = self.building_at(x, y)
            if b is not None and random.random() < 0.5:
                self.destroy(b)
                if random.random() < 0.3:
                    self.start_fire(x, y)
            elif self.tile[y][x] in NETWORK and random.random() < 0.4:
                self.tile[y][x] = "rubble"
        self.recompute_power()
        self.say("Major earthquake reported!", "bad", (int(cx), int(cy)))
        self.sprites.append({"kind": "shake", "life": 3.0})

    def disaster_monster(self):
        ind = [b for b in self.buildings.values() if b.kind in ("ind", "coal")]
        target = random.choice(ind).centre() if ind else (MAP_W / 2, MAP_H / 2)
        water = [(x, y) for y in range(MAP_H) for x in range(MAP_W) if self.terrain[y][x] == WATER]
        sx, sy = min(water, key=lambda p: (p[0] - target[0]) ** 2 + (p[1] - target[1]) ** 2 + random.uniform(0, 900)) \
            if water else (0, target[1])
        self.sprites.append({"kind": "monster", "x": sx, "y": sy, "tx": target[0], "ty": target[1], "life": 40.0,
                             "step": 0.0})
        self.say("Monster sighted!", "bad", (int(sx), int(sy)))

    def disaster_crash(self):
        airports = [b for b in self.buildings.values() if b.kind == "airport"]
        if not airports:
            return self.disaster_fire()
        b = random.choice(airports)
        x, y = int(b.x + random.uniform(-6, 12)), int(b.y + random.uniform(-6, 12))
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                self.start_fire(x + dx, y + dy)
        self.say("Plane crashed!", "bad", (x, y))

    def disaster_meltdown(self, plant=None):
        plants = [b for b in self.buildings.values() if b.kind == "nuclear"]
        if plant is None:
            if not plants:
                return
            plant = random.choice(plants)
        cx, cy = plant.centre()
        self.destroy(plant)
        for _ in range(30):
            x, y = int(cx + random.gauss(0, 5)), int(cy + random.gauss(0, 5))
            self.start_fire(x, y)
        self.say("A nuclear meltdown has occurred!", "bad", (int(cx), int(cy)))

    def _sprites(self, dt):
        for s in list(self.sprites):
            s["life"] -= dt
            if s["kind"] == "tornado":
                s["ang"] += random.uniform(-0.6, 0.6) * dt
                s["x"] += math.cos(s["ang"]) * 3 * dt
                s["y"] += math.sin(s["ang"]) * 3 * dt
                self._smash(s["x"], s["y"], 1)
            elif s["kind"] == "monster":
                s["step"] += dt
                dx, dy = s["tx"] - s["x"], s["ty"] - s["y"]
                d = math.hypot(dx, dy)
                if d < 1.5:
                    s["tx"] += random.uniform(-15, 15)
                    s["ty"] += random.uniform(-15, 15)
                else:
                    s["x"] += dx / d * 2.2 * dt
                    s["y"] += dy / d * 2.2 * dt
                if s["step"] > 0.5:
                    s["step"] = 0
                    self._smash(s["x"], s["y"], 1, fire=0.25)
            if s["life"] <= 0 or not (0 <= s.get("x", 1) < MAP_W and 0 <= s.get("y", 1) < MAP_H):
                self.sprites.remove(s)

    def _smash(self, fx, fy, r, fire=0.0):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                x, y = int(fx) + dx, int(fy) + dy
                if not self.inside(x, y):
                    continue
                b = self.building_at(x, y)
                if b is not None:
                    self.destroy(b)
                elif self.tile[y][x] not in (None, "rubble", "flood"):
                    self.tile[y][x] = "rubble"
                elif self.terrain[y][x] == TREES:
                    self.terrain[y][x] = LAND
                if fire and random.random() < fire:
                    self.start_fire(x, y)

    # ---- money --------------------------------------------------------------------------------------------
    def budget_numbers(self):
        res, com, ind = self.totals()
        lvf = 0.7 + self.average(self.landvalue) / 200
        taxes = int(self.tax / 100 * (res * 1.2 + (com + ind) * 1.0) * lvf)
        roads = int(0.3 * sum(1 for y in range(MAP_H) for x in range(MAP_W) if self.has(x, y, "road")) +
                    0.6 * sum(1 for y in range(MAP_H) for x in range(MAP_W) if self.has(x, y, "rail")))
        police = 100 * sum(1 for b in self.buildings.values() if b.kind == "police")
        fire = 100 * sum(1 for b in self.buildings.values() if b.kind == "fire")
        return {"taxes": taxes, "road": roads, "police": police, "fire": fire}

    def _year_end(self):
        nums = self.budget_numbers()
        spend = sum(int(nums[k] * self.funding[k] / 100) for k in ("road", "police", "fire"))
        self.last_budget = dict(nums, spend=spend, flow=nums["taxes"] - spend)
        self.cash_flow = nums["taxes"] - spend
        self.funds += self.cash_flow
        if self.auto_budget:
            self.say(f"Budget: collected ${nums['taxes']:,}, spent ${spend:,}.", "info")
        else:
            self.budget_due = True
        if self.funds < 0:
            self.say("The city is in debt! Raise taxes or cut spending.", "bad")

    def average(self, grid):
        vals = [v for row in grid for v in row]
        return sum(vals) / len(vals)

    def developed_average(self, grid):
        vals = []
        for b in self.buildings.values():
            if b.kind in ("res", "com", "ind") and b.level:
                vals.append(self.at_half(grid, b.x + 1, b.y + 1))
        return sum(vals) / len(vals) if vals else 0.0

    # ---- evaluation ---------------------------------------------------------------------------------------
    def category(self):
        p = self.population
        return ("Village" if p < 2000 else "Town" if p < 10000 else "City" if p < 50000 else
                "Capital" if p < 100000 else "Metropolis" if p < 500000 else "Megalopolis")

    def _evaluate(self):
        crime = self.developed_average(self.crime)
        pol = self.developed_average(self.pollution)
        traffic_roads = [self.traffic[y][x] for y in range(MAP_H) for x in range(MAP_W) if self.has(x, y, "road")]
        traffic = sum(traffic_roads) / len(traffic_roads) if traffic_roads else 0
        res, com, ind = self.totals()
        unemployment = max(0.0, (res * 0.55 - (com + ind)) / max(1, res * 0.55)) * 100
        housing = max(0.0, self.developed_average(self.landvalue) - 100)
        fires = len(self.burning)
        zones = [b for b in self.buildings.values() if b.kind in ("res", "com", "ind")]
        dark = sum(1 for b in zones if not b.powered) / len(zones) * 100 if zones else 0
        problems = {"Power": dark * 1.5, "Crime": crime / 2.5, "Pollution": pol / 3, "Housing Costs": housing / 1.5,
                    "Taxes": max(0, (self.tax - 5) * 6), "Traffic": traffic / 2, "Unemployment": unemployment,
                    "Fires": min(100, fires * 5)}
        total = sum(problems.values()) or 1
        self.problems = {k: int(round(v / total * 100)) for k, v in sorted(problems.items(), key=lambda kv: -kv[1])}
        score = 1000 - sum(problems.values()) * 3.2
        score -= len(getattr(self, "caps", {})) * 40
        if self.power_used > self.power_cap:
            score -= 80
        if self.funds < 0:
            score -= 100
        growth = (self.population - self.last_pop) / max(1, self.last_pop) if self.last_pop else 0
        score += max(-100, min(100, growth * 500))
        self.score = int(max(0, min(1000, self.score * 0.7 + score * 0.3)))
        self.approval = int(max(5, min(95, 30 + self.score / 15)))
        self.migration = self.population - self.last_pop
        self.assessed = int(sum((b.level + 1) * {"res": 1500, "com": 2200, "ind": 1800}.get(b.kind, 6000)
                                for b in self.buildings.values()) +
                            sum(1 for y in range(MAP_H) for x in range(MAP_W) if self.tile[y][x] in NETWORK) * 120)

    def _record(self):
        res, com, ind = self.totals()
        for k, v in (("res", res), ("com", com), ("ind", ind), ("funds", self.funds),
                     ("crime", self.developed_average(self.crime)), ("pollution", self.developed_average(self.pollution))):
            self.history[k].append(v)
            del self.history[k][:-240]
        if self.month == 0:
            self.last_pop = self.population
        for mark in (2000, 10000, 50000, 100000, 500000):
            if self.population >= mark and mark not in self.milestones:
                self.milestones.add(mark)
                self.say(f"Population has reached {mark:,}! {self.name} is now a {self.category()}.", "good")
        # advice, now and then
        if random.random() < 0.15:
            res, com, ind = self.totals()
            tips = []
            if self.power_used > self.power_cap:
                tips.append("Brownouts! Build another Power Plant.")
            if not any(b.kind in POWER_CAP for b in self.buildings.values()) and self.buildings:
                tips.append("Build a Power Plant.")
            if self.demand["res"] > 0.5:
                tips.append("More residential zones needed.")
            if self.demand["com"] > 0.5 and res > 500:
                tips.append("More commercial zones needed.")
            if self.demand["ind"] > 0.5:
                tips.append("More industrial zones needed.")
            if self.problems and next(iter(self.problems)) == "Traffic" and res > 3000:
                tips.append("Frequent traffic jams reported.")
            if self.problems and next(iter(self.problems)) == "Crime" and res > 3000:
                tips.append("Citizens demand a Police Station.")
            if self.problems and next(iter(self.problems)) == "Pollution" and res > 3000:
                tips.append("Pollution very high.")
            if not any(b.kind == "fire" for b in self.buildings.values()) and res > 2000:
                tips.append("Citizens demand a Fire Department.")
            tips += list(getattr(self, "caps", {}).values())
            if tips:
                self.say(random.choice(tips), "advice")

    # ---- scenarios ------------------------------------------------------------------------------------------
    def _scenario_check(self):
        sc = self.scenario
        if not sc or sc.get("done"):
            return
        months = (self.year - sc["start_year"]) * 12 + self.month
        goal = sc["goal"]
        met = {"pop": lambda: self.population >= goal[1], "score": lambda: self.score >= goal[1],
               "pollution": lambda: self.developed_average(self.pollution) <= goal[1],
               "traffic": lambda: self.problems.get("Traffic", 100) <= goal[1],
               "crime": lambda: self.developed_average(self.crime) <= goal[1]}[goal[0]]()
        if met and months >= 12:
            sc["done"] = "won"
            self.say(f"Congratulations! You have met the goal of the {sc['name']} scenario. The citizens throw you "
                     "a parade!", "win")
        elif months >= sc["years"] * 12:
            sc["done"] = "lost"
            self.say(f"Time is up on {sc['name']}. The citizens have run you out of town...", "lose")

    # ---- saving --------------------------------------------------------------------------------------------
    def to_json(self):
        return {"name": self.name, "seed": self.seed, "level": self.level, "funds": self.funds, "year": self.year,
                "month": self.month, "tax": self.tax, "funding": self.funding, "speed": self.speed,
                "auto_budget": self.auto_budget, "auto_bulldoze": self.auto_bulldoze,
                "disasters_on": self.disasters_on,
                "terrain": ["".join(str(v) for v in row) for row in self.terrain],
                "tile": [[t for t in row] for row in self.tile],
                "buildings": [b.to_json() for b in self.buildings.values()],
                "burning": [[x, y, v] for (x, y), v in self.burning.items()],
                "history": self.history, "milestones": sorted(self.milestones), "score": self.score,
                "scenario": self.scenario, "last_pop": self.last_pop}

    @classmethod
    def from_json(cls, d):
        c = cls(d["name"], d["seed"], d["level"], d["year"], blank=True)
        for k in ("funds", "month", "tax", "funding", "speed", "auto_budget", "auto_bulldoze", "disasters_on",
                  "history", "score", "scenario", "last_pop"):
            if k in d:
                setattr(c, k, d[k])
        c.milestones = set(d.get("milestones", []))
        c.terrain = [[int(ch) for ch in row] for row in d["terrain"]]
        c.tile = [list(row) for row in d["tile"]]
        for kind, x, y, size, level, variant in d["buildings"]:
            b = Building(kind, x, y, size, level)
            b.variant = variant
            bid = c.next_id
            c.next_id += 1
            c.buildings[bid] = b
            for tx, ty in b.tiles():
                c.owner[ty][tx] = bid
        c.burning = {(x, y): v for x, y, v in d.get("burning", [])}
        c.recompute()
        return c


# ---- scenarios --------------------------------------------------------------------------------------------------

SCENARIOS = [
    dict(key="dullsville", name="Dullsville, USA 1900", start_year=1900, funds=5000, years=30,
         goal=("pop", 50000), size=0.25, disaster=None,
         text="Dullsville, USA 1900 - Things haven't changed much around here in the last hundred years or so, "
              "and the residents are beginning to get bored. They think Dullsville could be the next great city "
              "with the right leader. Your goal is to make it a Metropolis of 50,000 people within 30 years."),
    dict(key="bay", name="Bay City 1957: Claudezilla!", start_year=1957, funds=20000, years=5,
         goal=("score", 500), size=0.7, disaster="monster",
         text="Bay City 1957 - A large reptilian creature has been spotted heading for the bay. It seems to be "
              "attracted to the heavy levels of industrial pollution. Try to control the fires, then rebuild the "
              "industrial centre. You have five years to raise the city score to 500."),
    dict(key="riverton", name="Riverton 1972: Flood", start_year=1972, funds=15000, years=10,
         goal=("pop", 0), size=0.55, disaster="flood",
         text="Riverton 1972 - Days of rain have swollen the river and it has burst its banks. Clear the damage "
              "and bring the population back to where it was before the flood, within ten years."),
    dict(key="smog", name="Smogburg 1985: Pollution", start_year=1985, funds=15000, years=10,
         goal=("pollution", 45), size=0.75, disaster=None, smoggy=True,
         text="Smogburg 1985 - Factories and a coal plant have turned the sky brown. Reduce the average pollution "
              "in developed areas to a healthy level within ten years, without letting the city collapse."),
    dict(key="gridlock", name="Gridlock 1990: Traffic", start_year=1990, funds=20000, years=8,
         goal=("traffic", 12), size=0.8, disaster=None,
         text="Gridlock 1990 - Commuters spend half their lives in jams. Get traffic down to a minor complaint "
              "(12% or less of the citizens' worries) within eight years. Rail and better roads are your friends."),
    dict(key="shakes", name="Shakesville 1906: Earthquake", start_year=1906, funds=20000, years=5,
         goal=("score", 500), size=0.65, disaster="quake",
         text="Shakesville 1906 - A huge earthquake has just struck! Fires are breaking out across the city. Put "
              "them out, rebuild, and raise the city score to 500 within five years."),
]


def build_scenario(sc):
    """Lay out a ready-made town for a scenario: a road grid with zones, power and services."""
    rnd = random.Random(sc["key"])
    c = City(sc["name"].split(":")[0].split(" 1")[0], seed=rnd.randint(1, 10 ** 6), level="Medium",
             year=sc["start_year"])
    c.funds = sc["funds"]
    c.auto_bulldoze = True
    cx, cy = MAP_W // 2, MAP_H // 2
    span = int(10 + sc["size"] * 40)
    # find a dry centre
    for _ in range(200):
        if all(c.terrain[cy + dy][cx + dx] != WATER for dx in range(-4, 5) for dy in range(-4, 5)):
            break
        cx, cy = rnd.randint(30, MAP_W - 30), rnd.randint(25, MAP_H - 25)
    funds = c.funds
    c.funds = 10 ** 9
    x0, y0 = max(2, cx - span // 2), max(2, cy - span // 2)
    x1, y1 = min(MAP_W - 3, cx + span // 2), min(MAP_H - 3, cy + span // 2)
    for y in range(y0, y1 + 1, 4):
        for x in range(x0, x1 + 1):
            c.apply("road", x, y)
    for x in range(x0, x1 + 1, 8):
        for y in range(y0, y1 + 1):
            c.apply("road", x, y)
    for y in range(y0, y1 + 1):                       # power lines run along the streets
        for x in range(x0, x1 + 1):
            if c.has(x, y, "road"):
                c.apply("wire", x, y)
    kinds = ["res", "res", "res", "com", "ind"]
    for y in range(y0 + 1, y1 - 2, 4):
        for x in range(x0 + 1, x1 - 2, 4):
            dist = math.hypot(x - cx, y - cy) / max(1, span / 2)
            if sc.get("smoggy"):
                kind = rnd.choice(["ind", "ind", "res", "com"])
            else:
                kind = "com" if dist < 0.3 and rnd.random() < 0.6 else rnd.choice(kinds)
            if c.can_place(kind, x, y):
                c.apply(kind, x, y)
                b = c.building_at(x, y)
                b.level = max(0, min(MAX_LEVEL[kind], int((1 - dist) * MAX_LEVEL[kind] + rnd.uniform(-1, 1.4))))
    for kind in ("police", "fire"):
        for _ in range(2 if sc["size"] > 0.5 else 1):
            for _try in range(40):
                x, y = rnd.randint(x0 + 1, x1 - 3), rnd.randint(y0 + 1, y1 - 3)
                b = c.building_at(x, y)
                if b and b.kind in ("res", "com", "ind"):
                    c.destroy(b, rubble=False)
                    if c.can_place(kind, b.x, b.y):
                        c.apply(kind, b.x, b.y)
                        break
    # power plants right against the wired streets, enough for every zone
    plant = "coal" if sc.get("smoggy") or rnd.random() < 0.7 else "nuclear"
    zones = sum(1 for b in c.buildings.values() if b.kind in ("res", "com", "ind"))
    need = max(1, -(-zones // (POWER_CAP[plant] - 5)))
    spots = [(x, y) for y in range(y0 - 6, y1 + 3) for x in range(x0 - 6, x1 + 3)
             if not (x0 <= x <= x1 - 3 and y0 <= y <= y1 - 3)]
    rnd.shuffle(spots)
    for (px, py) in spots:
        if need <= 0:
            break
        if not c.can_place(plant, px, py):
            continue
        touching = any(c.has(px + dx, py + dy, "wire") for dx in range(-1, 5) for dy in range(-1, 5)
                       if (0 <= dx < 4) != (0 <= dy < 4))           # edge neighbours, not corners
        if touching:
            c.apply(plant, px, py)
            need -= 1
    c.funds = funds
    c.recompute()
    c.scenario = {"key": sc["key"], "name": sc["name"], "start_year": sc["start_year"], "years": sc["years"],
                  "goal": list(sc["goal"]), "text": sc["text"]}
    if sc["key"] == "riverton":
        c.scenario["goal"] = ["pop", int(c.population * 0.95)]
    if sc["disaster"] == "monster":
        c.disaster_monster()
    elif sc["disaster"] == "flood":
        for _ in range(3):
            c.disaster_flood()
    elif sc["disaster"] == "quake":
        c.disaster_quake()
    c.disasters_on = True
    return c


def save_city(city, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(city.to_json()), encoding="utf-8")
    tmp.replace(path)


def load_city(path):
    return City.from_json(json.loads(path.read_text(encoding="utf-8")))
