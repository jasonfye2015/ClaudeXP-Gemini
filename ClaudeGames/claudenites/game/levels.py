"""Levels: a grid of squares, one world unit a side (square (cx, cy) spans x in [cx, cx+1], z in [cy, cy+1]), each solid
or open; an open square has a floor height and (indoors) a ceiling height, so a level has steps, daises, pits and
high halls, not just corridors. Arrays are indexed [cy, cx].

    dungeon(depth, seed) -> Level      a floor of the Deep, made from the seed (the same seed, the same floor)
    town(seed) -> Level                Thornwick, in its clearing in the forest
"""
import heapq
import math
import random

import numpy as np

from . import data as D

STEP = 0.42                          # the highest step a walker takes without a jump
INVISIBLE = 255                      # a wall texture that draws nothing (the forest's edge: trees stand there instead)


class Level:
    def __init__(self, w, h, depth, outdoor=False):
        self.w, self.h, self.depth, self.outdoor = w, h, depth, outdoor
        self.solid = np.ones((h, w), bool)
        self.floor = np.zeros((h, w), np.float32)
        self.ceil = np.full((h, w), 1.7, np.float32)
        self.top = np.full((h, w), 1.7, np.float32)      # a solid square's top (outdoors: walls and houses have tops)
        self.wtex = np.zeros((h, w), np.uint8)
        self.ftex = np.zeros((h, w), np.uint8)
        self.ctex = np.zeros((h, w), np.uint8)
        self.textures = []                               # layer names, in texture-array order
        self.tint = (1.0, 1.0, 1.0)
        self.fog = ((0.05, 0.05, 0.05), 0.1)
        self.ambient = 0.2
        self.name = ""
        self.line = ""
        self.props = []                                  # {"model": plant name, "x", "z", "yaw", "scale", "y"?}
        self.spawns = []                                 # {"monster", "x", "z"}
        self.npcs = []                                   # {"vendor", "x", "z", "yaw"}
        self.lights = []                                 # static torches: (x, y, z, r, g, b, radius)
        self.rooms = []
        self.start = (1.5, 1.5, 0.0)                     # x, z, yaw
        self.stairs = None                               # (x, z): the way down
        self.portal = None                               # (x, z): the way home (a floor's way back up), or the Deep's mouth
        self.guardian = None
        self.seed = 0
        self.houses = []                                 # (x0, y0, x1, y1, wall top, roof texture, door side (dx, dy))

    def tex(self, name):
        if name not in self.textures:
            self.textures.append(name)
        return self.textures.index(name)

    # ---- asking about places -------------------------------------------------------------------------------------
    def inside(self, cx, cy):
        return 0 <= cx < self.w and 0 <= cy < self.h

    def open_at(self, cx, cy):
        return self.inside(cx, cy) and not self.solid[cy, cx]

    def floor_at(self, x, z):
        cx, cy = int(math.floor(x)), int(math.floor(z))
        if not self.open_at(cx, cy):
            return 99.0
        return float(self.floor[cy, cx])

    def ceil_at(self, x, z):
        cx, cy = int(math.floor(x)), int(math.floor(z))
        if not self.open_at(cx, cy):
            return -99.0
        return 99.0 if self.outdoor else float(self.ceil[cy, cx])

    def can_stand(self, x, z, radius, foot):
        """Whether a walker of this radius, feet at height foot, fits here (walls, steps too high, low ceilings)."""
        for cx in range(int(math.floor(x - radius)), int(math.floor(x + radius)) + 1):
            for cy in range(int(math.floor(z - radius)), int(math.floor(z + radius)) + 1):
                if not self.open_at(cx, cy):
                    nx, nz = min(max(x, cx), cx + 1), min(max(z, cy), cy + 1)   # the square's nearest point
                    if (x - nx) ** 2 + (z - nz) ** 2 < radius * radius:
                        return False
                    continue
                if self.floor[cy, cx] > foot + STEP:
                    nx, nz = min(max(x, cx), cx + 1), min(max(z, cy), cy + 1)
                    if (x - nx) ** 2 + (z - nz) ** 2 < radius * radius * 0.5:
                        return False
        return True

    def stand_height(self, x, z, radius):
        """The highest floor under a walker's circle (so a step up is taken as the edge is reached)."""
        best = -99.0
        for cx, cy in ((math.floor(x), math.floor(z)),):
            if self.open_at(int(cx), int(cy)):
                best = max(best, float(self.floor[int(cy), int(cx)]))
        return best if best > -99 else 0.0

    def line_of_sight(self, x0, z0, y0, x1, z1, y1):
        """Nothing solid (and no floor or ceiling) between two points: walked in small steps."""
        d = math.hypot(x1 - x0, z1 - z0)
        n = max(2, int(d / 0.2))
        for i in range(1, n):
            t = i / n
            x, z, y = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t, y0 + (y1 - y0) * t
            if y < self.floor_at(x, z) or y > self.ceil_at(x, z):
                return False
        return True

    def open_squares(self):
        ys, xs = np.nonzero(~self.solid)
        return list(zip(xs.tolist(), ys.tolist()))

    def distances(self, sx, sy):
        """Walking distance (in squares) from one square to every square it can reach (-1: can't)."""
        dist = np.full((self.h, self.w), -1, np.int32)
        dist[sy, sx] = 0
        q = [(0, sx, sy)]
        while q:
            d, x, y = heapq.heappop(q)
            if d > dist[y, x] >= 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if self.open_at(nx, ny) and dist[ny, nx] < 0 and abs(self.floor[ny, nx] - self.floor[y, x]) <= STEP + 0.01:
                    dist[ny, nx] = d + 1
                    heapq.heappush(q, (d + 1, nx, ny))
        return dist


# ---- the Deep --------------------------------------------------------------------------------------------------------
class Room:
    def __init__(self, x, y, w, h, kind="plain"):
        self.x, self.y, self.w, self.h, self.kind = x, y, w, h, kind

    @property
    def centre(self):
        return (self.x + self.w // 2, self.y + self.h // 2)

    def overlaps(self, o, gap=2):
        return not (self.x + self.w + gap <= o.x or o.x + o.w + gap <= self.x or
                    self.y + self.h + gap <= o.y or o.y + o.h + gap <= self.y)

    def cells(self):
        for yy in range(self.y, self.y + self.h):
            for xx in range(self.x, self.x + self.w):
                yield xx, yy


ROOM_KINDS = ["plain", "plain", "pillars", "dais", "pit", "hall", "plain", "cross"]
BAND_PROPS = [                                       # what lies about in each band's rooms (plant pack names)
    ["barrel", "crate", "rock1", "rock2"], ["stump_moss", "log_moss", "plant1", "plant3", "rock1"],
    ["barrel", "rock2", "lilypad", "rock1"], ["rock1", "rock2", "stump", "crate"], ["rock1", "rock2"],
    ["barrel", "crate", "rock2", "barrel"], ["stump_moss", "log_moss", "bush", "plant2", "willow_dead"],
    ["rock1", "rock2", "stump"], ["rock1", "crate", "barrel"], ["rock1", "rock2"],
]


def dungeon(depth, seed):
    rng = random.Random(f"{seed}:floor:{depth}")
    band = D.band_of(depth)
    bi = D.BANDS.index(band)
    guardian = depth % 10 == 0
    size = 44 + min(36, depth // 3) + (6 if guardian else 0)
    L = Level(size, size, depth)
    L.seed = seed
    L.paths = set()                                    # every square a corridor runs through (rooms keep them open)
    L.name, L.line = band["name"], band["line"]
    L.tint, L.fog, L.ambient = band["tint"], band["fog"], band["light"]
    wt, ft, ct = (L.tex(n) for n in band["tex"])
    L.wtex[:], L.ftex[:], L.ctex[:] = wt, ft, ct
    alt_floor = L.tex("ground.flags" if band["tex"][1] != "ground.flags" else "ground.cobbles")
    # the rooms
    want = 8 + min(14, depth // 6)
    rooms = []
    if guardian:                                       # the guardian's hall: big, high, at the far side
        rooms.append(Room(size - 22, size - 22, 17, 17, "arena"))
    for _ in range(600):
        if len(rooms) >= want:
            break
        w, h = rng.randint(5, 11), rng.randint(5, 11)
        r = Room(rng.randint(2, size - w - 3), rng.randint(2, size - h - 3), w, h, rng.choice(ROOM_KINDS))
        if all(not r.overlaps(o) for o in rooms):
            rooms.append(r)
    if guardian:                                       # (the hall first in the list: it's placed, then moved last)
        rooms.append(rooms.pop(0))
    for r in rooms:
        ceil = {"hall": rng.uniform(3.0, 3.8), "arena": 4.2, "pillars": rng.uniform(2.4, 3.0)}.get(r.kind, rng.uniform(1.9, 2.6))
        for x, y in r.cells():
            L.solid[y, x] = False
            L.floor[y, x] = 0.0
            L.ceil[y, x] = ceil
    # the corridors: a spanning tree over the rooms' centres, and a few loops
    centres = [r.centre for r in rooms]
    joined, edges = {0}, []
    while len(joined) < len(rooms):
        best = None
        for a in joined:
            for b in range(len(rooms)):
                if b in joined:
                    continue
                d = abs(centres[a][0] - centres[b][0]) + abs(centres[a][1] - centres[b][1])
                if best is None or d < best[0]:
                    best = (d, a, b)
        edges.append(best[1:])
        joined.add(best[2])
    for _ in range(max(1, len(rooms) // 4)):
        a, b = rng.sample(range(len(rooms)), 2)
        edges.append((a, b))
    for a, b in edges:
        _corridor(L, centres[a], centres[b], rng, wide=rng.random() < 0.25)
    # the rooms' shapes (after the corridors, which only cut through rock)
    for r in rooms:
        _shape(L, r, rng, alt_floor)
    L.rooms = rooms
    # where Claude comes in, and the way down: the room furthest from it
    start = rooms[0] if not guardian else rooms[0]
    sx, sy = start.centre
    dist = L.distances(sx, sy)
    far = rooms[-1] if guardian else max(rooms[1:], key=lambda r: dist[r.centre[1], r.centre[0]])
    L.start = (sx + 0.5, sy + 0.5, rng.uniform(0, math.tau))
    L.portal = (sx + 0.5, sy + 0.5)
    tx, ty = far.centre
    for yy in range(ty - 1, ty + 2):                       # (a clear square round the stairs: no pillar on them)
        for xx in range(tx - 1, tx + 2):
            if far.x <= xx < far.x + far.w and far.y <= yy < far.y + far.h and L.solid[yy, xx]:
                L.solid[yy, xx] = False
                L.floor[yy, xx] = L.floor[ty, tx]
    L.stairs = (tx + 0.5, ty + 0.5)
    if guardian:
        L.guardian = band["guardian"]
    # the monsters: a few to a room, none in the first, more the deeper
    kinds = band["monsters"]
    for r in rooms:
        if r is start:
            continue
        if guardian and r is far:
            continue
        groups = rng.randint(1, 2) + (1 if depth > 30 and rng.random() < 0.4 else 0)
        for _ in range(groups):
            name = rng.choice(kinds)
            n = rng.randint(2, 4) if D.MONSTERS[name]["kind"] == "swarm" else rng.randint(1, 2 + depth // 25)
            for _ in range(n):
                for _try in range(20):
                    x, y = rng.randint(r.x, r.x + r.w - 1), rng.randint(r.y, r.y + r.h - 1)
                    if L.open_at(x, y) and dist[y, x] > 6:
                        L.spawns.append({"monster": name, "x": x + rng.uniform(0.3, 0.7), "z": y + rng.uniform(0.3, 0.7)})
                        break
    if guardian:
        L.spawns.append({"monster": band["guardian"], "x": tx + 0.5, "z": ty - 3.5, "guardian": True})
    # the clutter, and the torches
    props = BAND_PROPS[bi]
    for r in rooms:
        for _ in range(rng.randint(0, 3)):
            x, y = rng.randint(r.x, r.x + r.w - 1), rng.randint(r.y, r.y + r.h - 1)
            if not L.open_at(x, y) or _near(L, x, y, L.stairs) or _near(L, x, y, L.portal):
                continue
            edge = sum(not L.open_at(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge or rng.random() < 0.3:
                L.props.append({"model": rng.choice(props), "x": x + 0.5, "z": y + 0.5, "yaw": rng.uniform(0, math.tau),
                                "scale": rng.uniform(0.32, 0.45), "y": float(L.floor[y, x]), "solid": True})
        for _ in range(1 + (r.w * r.h) // 30):
            spot = _wall_spot(L, r, rng)
            if spot:
                L.lights.append(spot)
    return L


def _near(L, x, y, at, d=1.6):
    return at is not None and abs(x + 0.5 - at[0]) < d and abs(y + 0.5 - at[1]) < d


def _corridor(L, a, b, rng, wide=False):
    (x0, y0), (x1, y1) = a, b
    ceil = rng.uniform(1.5, 1.9)
    pts = []
    if rng.random() < 0.5:
        pts += [(x, y0) for x in _span(x0, x1)] + [(x1, y) for y in _span(y0, y1)]
    else:
        pts += [(x0, y) for y in _span(y0, y1)] + [(x, y1) for x in _span(x0, x1)]
    for x, y in pts:
        for dx, dy in ((0, 0), (1, 0), (0, 1)) if wide else ((0, 0),):
            cx, cy = x + dx, y + dy
            L.paths.add((cx, cy))
            if 1 <= cx < L.w - 1 and 1 <= cy < L.h - 1 and L.solid[cy, cx]:
                L.solid[cy, cx] = False
                L.floor[cy, cx] = 0.0
                L.ceil[cy, cx] = ceil


def _span(a, b):
    return range(a, b + 1) if b >= a else range(a, b - 1, -1)


def _shape(L, r, rng, alt_floor):
    x0, y0, x1, y1 = r.x, r.y, r.x + r.w, r.y + r.h
    if r.kind == "pillars" and r.w >= 7 and r.h >= 7:
        for y in range(y0 + 2, y1 - 1, 3):
            for x in range(x0 + 2, x1 - 1, 3):
                if (x, y) not in L.paths:
                    L.solid[y, x] = True
    elif r.kind == "dais" and r.w >= 7 and r.h >= 7:
        L.floor[y0 + 2:y1 - 2, x0 + 2:x1 - 2] = 0.3
        L.floor[y0 + 3:y1 - 3, x0 + 3:x1 - 3] = 0.6
        L.ftex[y0 + 2:y1 - 2, x0 + 2:x1 - 2] = alt_floor
    elif r.kind == "pit" and r.w >= 7 and r.h >= 7:
        L.floor[y0 + 2:y1 - 2, x0 + 2:x1 - 2] = -0.35
        L.floor[y0 + 3:y1 - 3, x0 + 3:x1 - 3] = -0.7
    elif r.kind == "cross" and r.w >= 7 and r.h >= 7:      # four blocks of rock in the corners: a cross-shaped room
        for x, y in list(r.cells()):
            if (x < x0 + 2 or x >= x1 - 2) and (y < y0 + 2 or y >= y1 - 2):
                if not _corridor_mouth(L, x, y, r) and (x, y) not in L.paths:
                    L.solid[y, x] = True
    elif r.kind == "arena":
        L.floor[y0 + 3:y1 - 3, x0 + 3:x1 - 3] = -0.3
        for x, y in ((x0 + 3, y0 + 3), (x1 - 4, y0 + 3), (x0 + 3, y1 - 4), (x1 - 4, y1 - 4)):
            if (x, y) not in L.paths:
                L.solid[y, x] = True
        L.ftex[y0:y1, x0:x1] = alt_floor


def _corridor_mouth(L, x, y, r):
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if not (r.x <= nx < r.x + r.w and r.y <= ny < r.y + r.h) and L.open_at(nx, ny):
            return True
    return False


def _wall_spot(L, r, rng):
    """A torch on a wall of the room: a square at the room's edge with rock behind it."""
    for _ in range(30):
        x, y = rng.randint(r.x, r.x + r.w - 1), rng.randint(r.y, r.y + r.h - 1)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if L.open_at(x, y) and not L.open_at(x + dx, y + dy):
                px, pz = x + 0.5 + dx * 0.42, y + 0.5 + dy * 0.42
                return (px, float(L.floor[y, x]) + 1.15, pz, 1.0, 0.62, 0.28, 5.5)
    return None


# ---- Thornwick -------------------------------------------------------------------------------------------------------
TOWN_SIZE = 64


def town(seed=1):
    rng = random.Random(f"{seed}:town")
    S = TOWN_SIZE
    L = Level(S, S, 0, outdoor=True)
    L.name, L.line = D.TOWN_NAME, "Home: a clearing in the forest, a ring of roofs, and the Deep under the old stones."
    L.tint, L.fog, L.ambient = (1.0, 1.0, 1.0), ((0.42, 0.52, 0.58), 0.035), 0.55
    grass, dirt, cobble, flags = L.tex("ground.grass"), L.tex("ground.dirt"), L.tex("ground.cobbles"), L.tex("ground.flags")
    needles = L.tex("ground.needles")
    plaster, roof, stone, bark = L.tex("solid.plaster"), L.tex("solid.roof"), L.tex("solid.cliff"), L.tex("solid.bark")
    L.tex("ground.planks")
    cx = cy = S // 2
    yy, xx = np.mgrid[0:S, 0:S]
    r = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
    clearing = r < 21 + 2.5 * np.sin(np.arctan2(yy - cy, xx - cx) * 5 + 1.3)
    L.solid[:] = ~clearing
    L.wtex[:] = INVISIBLE
    L.top[:] = 0.0
    L.ftex[:] = grass
    L.ftex[(r > 17) & clearing] = needles
    # paths: a ring road and four ways out to the stalls, cobbled square in the middle
    L.ftex[(r > 9.5) & (r < 11.5)] = dirt
    for ang in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):
        for t in np.arange(0, 17, 0.25):
            px, py = int(cx + math.cos(ang) * t), int(cy + math.sin(ang) * t)
            for d in (-1, 0):
                qx, qy = (px + d, py) if abs(math.sin(ang)) > 0.5 else (px, py + d)
                if L.inside(qx, qy) and not L.solid[qy, qx]:
                    L.ftex[qy, qx] = dirt
    L.ftex[(r < 5.5)] = cobble
    L.ftex[(r < 2.6)] = flags
    # the Deep's mouth: a ring of old standing stones round a sunken floor in the middle of the square
    L.floor[r < 2.6] = -0.18
    for k in range(8):
        a = k / 8 * math.tau + math.pi / 8
        sx, sy = int(cx + math.cos(a) * 3.6), int(cy + math.sin(a) * 3.6)
        L.solid[sy, sx] = True
        L.wtex[sy, sx] = stone
        L.top[sy, sx] = 1.4 + 0.25 * (k % 3)
    L.portal = (cx + 0.5, cy + 0.5)
    # the houses and the stalls: a vendor before each, facing the square
    spots = {"apothecary": 0.35, "wandwright": 1.95, "outfitter": 3.55, "sage": 5.15}
    for key, ang in spots.items():
        hx, hy = cx + math.cos(ang) * 14.5, cy + math.sin(ang) * 14.5
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                qx, qy = int(hx) + dx, int(hy) + dy
                L.solid[qy, qx] = True
                L.wtex[qy, qx] = plaster
                L.top[qy, qx] = 2.6
        door = (round(math.cos(ang + math.pi)), 0) if abs(math.cos(ang)) > abs(math.sin(ang)) else (0, round(math.sin(ang + math.pi)))
        L.houses.append((int(hx) - 2, int(hy) - 2, int(hx) + 3, int(hy) + 3, 2.6, roof, door))
        nx, nz = cx + math.cos(ang) * 11.2, cy + math.sin(ang) * 11.2
        L.npcs.append({"vendor": key, "x": nx, "z": nz, "yaw": math.atan2(-(cx - nx), cy - nz)})
        L.lights.append((nx + math.cos(ang) * 0.9, 1.9, nz + math.sin(ang) * 0.9, 1.0, 0.75, 0.4, 6.0))
    L.roof = roof
    # more houses, to make a town of it
    for k in range(7):
        ang = 0.35 + 0.8 + k * (math.tau / 7)
        if any(abs(((ang - a + math.pi) % math.tau) - math.pi) < 0.45 for a in spots.values()):
            continue
        hx, hy = cx + math.cos(ang) * 16.5, cy + math.sin(ang) * 16.5
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                qx, qy = int(hx) + dx, int(hy) + dy
                if L.inside(qx, qy):
                    L.solid[qy, qx] = True
                    L.wtex[qy, qx] = bark if k % 2 else plaster
                    L.top[qy, qx] = 2.2
        door = (round(math.cos(ang + math.pi)), 0) if abs(math.cos(ang)) > abs(math.sin(ang)) else (0, round(math.sin(ang + math.pi)))
        L.houses.append((int(hx) - 1, int(hy) - 1, int(hx) + 2, int(hy) + 2, 2.2, roof, door))
    # the forest: trees thick round the edge, a few in the clearing's skirts
    trees = ["pine", "pine2", "common", "common2", "birch", "birch2", "willow"]
    for (x, y) in zip(*np.nonzero(L.solid.T)):
        if L.wtex[y, x] != INVISIBLE:
            continue
        if r[y, x] < 30 and rng.random() < (0.5 if r[y, x] < 26 else 0.25):
            L.props.append({"model": rng.choice(trees), "x": x + rng.uniform(0.2, 0.8), "z": y + rng.uniform(0.2, 0.8),
                            "yaw": rng.uniform(0, math.tau), "scale": rng.uniform(0.9, 1.5), "y": 0.0})
    for (x, y) in L.open_squares():
        if r[y, x] > 17.5 and rng.random() < 0.06:
            L.props.append({"model": rng.choice(["bush", "bush2", "bushberries", "plant1", "plant2", "flowers", "rock1",
                                                 "stump_moss", "grass", "grass2"]),
                            "x": x + 0.5, "z": y + 0.5, "yaw": rng.uniform(0, math.tau), "scale": rng.uniform(0.5, 0.8),
                            "y": 0.0})
    L.start = (cx + 0.5, cy + 7.5, 0.0)
    return L
