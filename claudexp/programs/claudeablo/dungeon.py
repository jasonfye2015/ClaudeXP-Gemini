"""Claudeablo's places: the town, and fifty levels of dungeon generated from the game's seed and the depth.

Levels 1-10 are the Cathedral (rooms and halls), 11-20 the Catacombs (tighter rooms, long passages), 21-30 the
Caves (natural caverns with lava), 31-40 Hell and 41-49 the Abyss (rooms with lava pools), and 50 is Diablo's
Sanctum. Tiles: WALL, FLOOR, LAVA (impassable but not a wall). Coordinates are tile units; a tile's centre is
(x + 0.5, y + 0.5).
"""
import random
from collections import deque

WALL, FLOOR, LAVA = 0, 1, 2


def theme_for(depth):
    if depth <= 0:
        return "town"
    if depth == 50:
        return "sanctum"
    return ["cathedral", "catacombs", "caves", "hell", "abyss"][min(4, (depth - 1) // 10)]


THEME_NAMES = {"town": "Haven", "cathedral": "Cathedral", "catacombs": "Catacombs", "caves": "Caves",
               "hell": "Hell", "abyss": "The Abyss", "sanctum": "Diablo's Sanctum"}


class Level:
    def __init__(self, w, h, theme, depth):
        self.w, self.h, self.theme, self.depth = w, h, theme, depth
        self.grid = [[WALL] * w for _ in range(h)]
        self.style = {}                 # (x, y) -> wall look: 'tree', 'house', 'fence' (town)
        self.decor = {}                 # (x, y) -> floor decoration: 'blood', 'bones', 'rug', 'pentagram', ...
        self.rooms = []
        self.up = self.down = self.spawn = None
        self.places = {}                # named spots (town: smith, witch, healer, elder, waystone, portal)

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def floor(self, x, y):
        return self.inside(x, y) and self.grid[y][x] == FLOOR

    def wall(self, x, y):
        return not self.inside(x, y) or self.grid[y][x] == WALL

    def walkable(self, x, y):
        return self.floor(int(x), int(y))

    def carve(self, x0, y0, x1, y1, t=FLOOR):
        for y in range(max(1, y0), min(self.h - 1, y1 + 1)):
            for x in range(max(1, x0), min(self.w - 1, x1 + 1)):
                self.grid[y][x] = t

    def floors(self):
        return [(x, y) for y in range(self.h) for x in range(self.w) if self.grid[y][x] == FLOOR]

    def distances(self, start):
        """Steps from start to every reachable floor tile."""
        d = {start: 0}
        q = deque([start])
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n not in d and self.floor(*n):
                    d[n] = d[(x, y)] + 1
                    q.append(n)
        return d


# ---- dungeon levels ---------------------------------------------------------------------------------------------

def generate(seed, depth):
    rnd = random.Random(f"{seed}:{depth}")
    theme = theme_for(depth)
    if theme == "sanctum":
        return _sanctum(rnd, depth)
    size = 46 + min(depth, 30) // 2
    lv = Level(size, size, theme, depth)
    if theme == "caves":
        _caves(lv, rnd)
    else:
        small = theme == "catacombs"
        _rooms(lv, rnd, min_room=4 if small else 5, max_room=8 if small else 12)
        if theme in ("hell", "abyss"):
            _lava_pools(lv, rnd)
    _keep_connected(lv)
    _stairs(lv, rnd)
    _scatter_decor(lv, rnd)
    return lv


def _rooms(lv, rnd, min_room, max_room):
    """Binary space partition: split the map into leaves, a room in each, halls between siblings."""
    def split(x, y, w, h, depth=0):
        if depth > 5 or (w < max_room * 2 and h < max_room * 2):
            return [(x, y, w, h)]
        horizontal = h > w if abs(h - w) > 4 else rnd.random() < 0.5
        if horizontal and h >= min_room * 2 + 2:
            cut = rnd.randint(min_room + 1, h - min_room - 1)
            return split(x, y, w, cut, depth + 1) + split(x, y + cut, w, h - cut, depth + 1)
        if not horizontal and w >= min_room * 2 + 2:
            cut = rnd.randint(min_room + 1, w - min_room - 1)
            return split(x, y, cut, h, depth + 1) + split(x + cut, y, w - cut, h, depth + 1)
        return [(x, y, w, h)]

    leaves = split(1, 1, lv.w - 2, lv.h - 2)
    for (x, y, w, h) in leaves:
        rw = rnd.randint(min_room, max(min_room, min(max_room, w - 2)))
        rh = rnd.randint(min_room, max(min_room, min(max_room, h - 2)))
        rx = x + rnd.randint(1, max(1, w - rw - 1))
        ry = y + rnd.randint(1, max(1, h - rh - 1))
        lv.carve(rx, ry, rx + rw - 1, ry + rh - 1)
        lv.rooms.append((rx, ry, rw, rh))
    # join each room to the next (sorted along a winding path) and a few extra loops
    centres = [(rx + rw // 2, ry + rh // 2) for rx, ry, rw, rh in lv.rooms]
    order = sorted(range(len(centres)), key=lambda i: (centres[i][1] // 12, centres[i][0] * (1 if
                   (centres[i][1] // 12) % 2 == 0 else -1)))
    for a, b in zip(order, order[1:]):
        _hall(lv, centres[a], centres[b], rnd)
    for _ in range(max(1, len(centres) // 4)):
        a, b = rnd.sample(range(len(centres)), 2)
        _hall(lv, centres[a], centres[b], rnd)


def _hall(lv, a, b, rnd):
    (x0, y0), (x1, y1) = a, b
    wide = rnd.random() < 0.35 and lv.theme != "catacombs"
    if rnd.random() < 0.5:
        lv.carve(min(x0, x1), y0, max(x0, x1), y0 + (1 if wide else 0))
        lv.carve(x1, min(y0, y1), x1 + (1 if wide else 0), max(y0, y1))
    else:
        lv.carve(x0, min(y0, y1), x0 + (1 if wide else 0), max(y0, y1))
        lv.carve(min(x0, x1), y1, max(x0, x1), y1 + (1 if wide else 0))


def _caves(lv, rnd):
    g = [[WALL if (x in (0, lv.w - 1) or y in (0, lv.h - 1) or rnd.random() < 0.44) else FLOOR
          for x in range(lv.w)] for y in range(lv.h)]
    for _ in range(5):
        n = [[WALL] * lv.w for _ in range(lv.h)]
        for y in range(1, lv.h - 1):
            for x in range(1, lv.w - 1):
                walls = sum(g[y + dy][x + dx] == WALL for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                n[y][x] = WALL if walls >= 5 else FLOOR
        g = n
    lv.grid = g
    # a lava river or two
    for _ in range(rnd.randint(1, 2)):
        x, y = rnd.randint(5, lv.w - 6), 2
        while y < lv.h - 2:
            for dx in (0, 1):
                if lv.grid[y][x + dx] == FLOOR and rnd.random() < 0.85:
                    lv.grid[y][x + dx] = LAVA
            y += 1
            x = max(3, min(lv.w - 5, x + rnd.choice((-1, 0, 0, 1))))
    # gaps in the river so it can be crossed
    for y in range(2, lv.h - 2, rnd.randint(6, 9)):
        for x in range(1, lv.w - 1):
            if lv.grid[y][x] == LAVA:
                lv.grid[y][x] = FLOOR


def _lava_pools(lv, rnd):
    for rx, ry, rw, rh in lv.rooms:
        if rw >= 8 and rh >= 8 and rnd.random() < 0.55:
            cx, cy = rx + rw // 2, ry + rh // 2
            r = min(rw, rh) // 4
            for y in range(cy - r, cy + r + 1):
                for x in range(cx - r, cx + r + 1):
                    if (x - cx) ** 2 + (y - cy) ** 2 <= r * r and lv.grid[y][x] == FLOOR:
                        lv.grid[y][x] = LAVA


def _keep_connected(lv):
    """Only the biggest connected area of floor stays walkable (pockets are walled in)."""
    seen, best = set(), set()
    for f in lv.floors():
        if f in seen:
            continue
        area = set(lv.distances(f))
        seen |= area
        if len(area) > len(best):
            best = area
    for (x, y) in lv.floors():
        if (x, y) not in best:
            lv.grid[y][x] = WALL


def _stairs(lv, rnd):
    floors = lv.floors()
    start = None
    if lv.rooms:
        rx, ry, rw, rh = lv.rooms[0]
        start = (rx + rw // 2, ry + rh // 2)
    if start is None or not lv.floor(*start):
        start = rnd.choice(floors)
    d = lv.distances(start)
    lv.up = start
    lv.down = max(d, key=d.get)
    lv.spawn = _near_free(lv, start)


def _near_free(lv, spot):
    x, y = spot
    for r in range(1, 6):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if lv.floor(x + dx, y + dy) and (x + dx, y + dy) not in (lv.up, lv.down):
                    return (x + dx, y + dy)
    return spot


def _scatter_decor(lv, rnd):
    marks = {"cathedral": ["blood", "bones", "rug", "cracks"], "catacombs": ["bones", "bones", "blood", "cracks"],
             "caves": ["rocks", "bones", "cracks"], "hell": ["blood", "bones", "skulls", "cracks"],
             "abyss": ["skulls", "blood", "cracks"]}[lv.theme]
    for f in rnd.sample(lv.floors(), max(1, len(lv.floors()) // 30)):
        if f not in (lv.up, lv.down):
            lv.decor[f] = rnd.choice(marks)


def _sanctum(rnd, depth):
    lv = Level(44, 44, "sanctum", depth)
    cx, cy, r = 22, 16, 11
    for y in range(lv.h):
        for x in range(lv.w):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                lv.grid[y][x] = FLOOR
    lv.carve(cx - 1, cy + r - 1, cx + 1, 40)                  # the long approach
    lv.carve(cx - 4, 36, cx + 4, 41)
    for y in range(lv.h):
        for x in range(lv.w):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if lv.grid[y][x] == FLOOR and 30 <= d2 <= 40 and (x + y) % 3 == 0:
                lv.grid[y][x] = LAVA
            if lv.grid[y][x] == FLOOR and d2 <= 20:
                lv.decor[(x, y)] = "pentagram"
    lv.up = (cx, 40)
    lv.down = None
    lv.spawn = (cx, 38)
    lv.places["diablo"] = (cx, cy - 2)
    return lv


# ---- the town ----------------------------------------------------------------------------------------------------

def town():
    """Haven: a little village above the cathedral, the same every time."""
    lv = Level(44, 44, "town", 0)
    lv.carve(2, 2, 41, 41)
    for x in range(lv.w):                                     # the woods all around
        for y in range(lv.h):
            edge = min(x, y, lv.w - 1 - x, lv.h - 1 - y)
            if edge < 2:
                lv.grid[y][x] = WALL
                lv.style[(x, y)] = "tree"
    rnd = random.Random(7)
    for _ in range(60):
        x, y = rnd.randint(2, 41), rnd.randint(2, 41)
        if min(x, y, 43 - x, 43 - y) < 5 and not (18 <= x <= 25):
            lv.grid[y][x] = WALL
            lv.style[(x, y)] = "tree"

    def house(x0, y0, w, h, door, key):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                lv.grid[y][x] = WALL
                lv.style[(x, y)] = "house"
        lv.places[key] = door

    house(8, 9, 6, 5, (11, 15), "smith")
    house(29, 8, 6, 5, (32, 14), "witch")
    house(8, 27, 5, 5, (10, 33), "healer")
    house(30, 28, 6, 5, (33, 34), "elder")
    # the cathedral in the north, with the way down at its door
    for y in range(3, 8):
        for x in range(18, 26):
            lv.grid[y][x] = WALL
            lv.style[(x, y)] = "church"
    lv.down = (22, 9)
    lv.places["waystone"] = (25, 20)
    lv.places["portal"] = (19, 22)
    lv.places["well"] = (22, 21)
    lv.grid[21][22] = WALL
    lv.style[(22, 21)] = "well"
    lv.spawn = (22, 24)
    lv.up = None
    for x in range(14, 30):                                   # paths
        lv.decor[(x, 22)] = "path"
    for y in range(10, 36):
        lv.decor[(22, y)] = lv.decor.get((22, y), "path")
    for (x, y) in [(11, 16), (12, 16), (32, 15), (10, 34), (33, 35)]:
        lv.decor[(x, y)] = "path"
    for f in rnd.sample(lv.floors(), 70):
        if f not in lv.decor:
            lv.decor[f] = rnd.choice(["flowers", "grasstuft", "grasstuft", "stone"])
    return lv


def path(lv, start, goal, blocked=frozenset(), limit=4000):
    """A* over floor tiles (8 directions, no corner cutting). Returns a list of tiles after start, or []."""
    import heapq
    if not lv.floor(*goal):
        return []
    open_ = [(0, start)]
    came = {start: None}
    cost = {start: 0}
    while open_ and len(came) < limit:
        _f, cur = heapq.heappop(open_)
        if cur == goal:
            break
        x, y = cur
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            n = (x + dx, y + dy)
            if not lv.floor(*n) or (n in blocked and n != goal):
                continue
            if dx and dy and (not lv.floor(x + dx, y) or not lv.floor(x, y + dy)):
                continue
            c = cost[cur] + (1.414 if dx and dy else 1.0)
            if n not in cost or c < cost[n]:
                cost[n] = c
                came[n] = cur
                h = max(abs(goal[0] - n[0]), abs(goal[1] - n[1]))
                heapq.heappush(open_, (c + h, n))
    if goal not in came:
        return []
    out = []
    cur = goal
    while cur != start:
        out.append(cur)
        cur = came[cur]
    return out[::-1]
