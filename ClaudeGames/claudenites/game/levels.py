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
from . import dress
from . import forest

# what breaks: props (radius and height at scale 0.4) and sprites by picture
BREAK_PROPS = {"barrel": (0.27, 0.5), "crate": (0.26, 0.32)}
CHEST_SIZE = (0.33, 0.55)                # a chest's reach and height (the 3D chest, engine/render.py), for bolts
BREAK_SPRITES = {"fu.rack", "fu.shelf", "fu.table", "fu.bench", "sp.eggsac", "sp.cocoon", "sp.egg", "fungus", "sp.cage"}
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
        self.paths = set()                               # every square a corridor runs through (rooms keep them open)
        # the dressing (game/dress.py says what each is)
        self.decals, self.flats, self.webs, self.hangs, self.sprites, self.drips, self.chests = [], [], [], [], [], [], []
        self.water, self.pieces, self.gold_squares = set(), [], set()
        self.pickups = []                                # things lying about: {x, z, y, kind (gold/health/mana/item/scroll)}
        self.boxes = []                                  # furniture: (x0, y0, z0, x1, y1, z1, texture name)
        self.extra_blockers = []                         # (x, z, r): what stands in the way besides
        self.kind = "floor"                              # floor, town, cabin
        self.spots = {}                                  # named places to use: cabin door, bed, hearth, stash, exit, sign
        self.farm_cells = []                             # the farm's plots' squares, in order
        # the finer detail (game/detail.py): the ambient by square, puddles, stains, light from above, ceiling things
        self.amb, self.wet, self.stain, self.shafts, self.ceils = None, {}, {}, [], []
        self.caches = []
        self.safe = None                                 # (outdoors: the town's squares, where nothing hunts him)

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

    def breakables(self):
        """What a bolt can smash, by square: [(thing, x, z, y, r, h)] - barrels and crates (props), racks, shelves,
        tables, benches, egg sacs, cocoons and fungus (sprites). Made again when one breaks."""
        if getattr(self, "_breakables", None) is None:
            out = {}
            for p in self.props:
                if p["model"] in BREAK_PROPS:
                    r, h = BREAK_PROPS[p["model"]]
                    out.setdefault((int(p["x"]), int(p["z"])), []).append((p, p["x"], p["z"], p.get("y", 0.0), r * p["scale"] / 0.4, h * p["scale"] / 0.4))
            for c in self.chests:                             # (a chest: shot open, or shot to pieces once empty)
                if not c.get("broken"):
                    out.setdefault((int(c["x"]), int(c["z"])), []).append((c, c["x"], c["z"], c["y"], *CHEST_SIZE))
            for s in self.sprites:
                if s["name"] in BREAK_SPRITES:
                    out.setdefault((int(s["x"]), int(s["z"])), []).append((s, s["x"], s["z"], s["y"], max(0.2, s["w"] * 0.4), s["h"]))
            self._breakables = out
        return self._breakables

    def smash(self, thing):
        """Take a broken thing out of the floor (it no longer stands in the way, and isn't drawn)."""
        if thing in self.props:
            self.props.remove(thing)
        elif thing in self.sprites:
            self.sprites.remove(thing)
        elif any(thing is c for c in self.chests):
            thing["broken"] = True
            thing["opened"] = True
        self._breakables = None
        self._blockers = None
        self.version = getattr(self, "version", 0) + 1

    def blockers(self):
        """Things that stand in the way, by square: [(x, z, r)] (solid sprites, chests, solid props)."""
        if getattr(self, "_blockers", None) is None:
            b = {}
            things = [(s["x"], s["z"], s["solid"]) for s in self.sprites if s.get("solid")]
            things += [(c["x"], c["z"], 0.3) for c in self.chests if not c.get("broken")]
            things = [(x, z, min(0.45, r)) for x, z, r in things] + list(self.extra_blockers)
            things += [(p["x"], p["z"], p.get("trunk") or (0.26 if p.get("scale", 1) < 0.5 else 0.32)) for p in self.props
                       if p.get("solid")]
            for x, z, r in things:
                for cx in range(int(x - r), int(x + r) + 1):
                    for cy in range(int(z - r), int(z + r) + 1):
                        b.setdefault((cx, cy), []).append((x, z, r))
            self._blockers = b
        return self._blockers

    def can_stand(self, x, z, radius, foot):
        """Whether a walker of this radius, feet at height foot, fits here (walls, steps too high, low ceilings)."""
        B = self.blockers()
        if B:
            for cx in (int(x) - 1, int(x), int(x) + 1):
                for cy in (int(z) - 1, int(z), int(z) + 1):
                    for bx, bz, r in B.get((cx, cy), ()):
                        if (x - bx) ** 2 + (z - bz) ** 2 < (r + radius) ** 2:
                            return False
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


ROOM_KINDS = ["plain", "plain", "pillars", "dais", "pit", "hall", "plain", "cross", "L", "ring", "split", "steps", "L"]
BAND_PROPS = [                                       # what lies about in each band's rooms (plant pack names)
    ["barrel", "crate", "rock1", "rock2"], ["stump_moss", "log_moss", "plant1", "plant3", "rock1"],
    ["barrel", "rock2", "lilypad", "rock1"], ["rock1", "rock2", "stump", "crate"], ["rock1", "rock2"],
    ["barrel", "crate", "rock2", "barrel"], ["stump_moss", "log_moss", "bush", "plant2", "willow_dead"],
    ["rock1", "rock2", "stump"], ["rock1", "crate", "barrel"], ["rock1", "rock2"],
]


def dungeon(depth, seed):
    """A floor: rooms at their own heights joined by corridors that climb and fall between them; if the heights
    happen to cut anything off, the same floor is made again level."""
    for heights in (2, 1, 0):                                        # (high and low; gentler; level)
        L = _dungeon(depth, seed, heights)
        if heights == 0 or _whole(L):
            return L
    return L


def _whole(L):
    sx, sy = int(L.start[0]), int(L.start[1])
    dist = L.distances(sx, sy)
    for r in L.rooms:
        cells = [(x, y) for x, y in r.cells() if L.open_at(x, y)]
        if cells and not any(dist[y, x] >= 0 for x, y in cells):
            return False
    if dist[int(L.stairs[1]), int(L.stairs[0])] < 0:
        return False
    reach = walkable_reach(L)
    B = L.blockers()
    for (x, y) in L.open_squares():                                  # (every square he could stand on, he can reach)
        if (x, y) not in reach and L.floor[y, x] > -0.5 and not B.get((x, y)):
            return False
    return True


def _dungeon(depth, seed, varied):
    rng = random.Random(f"{seed}:floor:{depth}")
    band = D.band_of(depth)
    bi = D.BANDS.index(band)
    guardian = depth % 10 == 0
    size = 64 + min(44, depth // 2) + (8 if guardian else 0)            # (twice the floor it was)
    L = Level(size, size, depth)
    L.seed = seed
    L.name, L.line = band["name"], band["line"]
    L.tint, L.fog, L.ambient = band["tint"], band["fog"], band["light"]
    wt, ft, ct = (L.tex(n) for n in band["tex"])
    L.wtex[:], L.ftex[:], L.ctex[:] = wt, ft, ct
    alt_floor = L.tex("ground.flags" if band["tex"][1] != "ground.flags" else "ground.cobbles")
    # the rooms
    want = 16 + min(20, depth // 5)
    rooms = []
    if guardian:                                       # the guardian's hall: big, high, at the far side
        rooms.append(Room(size - 22, size - 22, 17, 17, "arena"))
    # a set piece - one of Claude and Magic's unique rooms - on most floors, in a room made to its size
    piece = None
    fits = dress.pieces_for(depth)
    if fits and rng.random() < 0.6:
        piece = rng.choice(fits)
        pw, ph = dress.size_of(piece)
        for _ in range(400):
            r = Room(rng.randint(2, size - pw - 3), rng.randint(2, size - ph - 3), pw, ph, "piece")
            if all(not r.overlaps(o) for o in rooms):
                r.piece = piece
                rooms.append(r)
                break
        else:
            piece = None
    for _ in range(600):
        if len(rooms) >= want:
            break
        w, h = rng.randint(5, 13), rng.randint(5, 13)
        r = Room(rng.randint(2, size - w - 3), rng.randint(2, size - h - 3), w, h, rng.choice(ROOM_KINDS))
        if all(not r.overlaps(o) for o in rooms):
            rooms.append(r)
    if guardian:                                       # (the hall first in the list: it's placed, then moved last)
        rooms.append(rooms.pop(0))
    if piece is not None:                              # (never the room Claude comes in by)
        pr = next(r for r in rooms if r.kind == "piece")
        rooms.remove(pr)
        rooms.insert(min(len(rooms), 2), pr)
    for k, r in enumerate(rooms):
        # each room at its own height (Claude comes in on level ground; the guardian's hall and set pieces too)
        r.base = 0.0
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
    # each room at its own height, a step or two from the room it's joined to (along the tree from the first)
    if varied:
        steps = [-0.3, 0.0, 0.3, 0.3, -0.3] if varied == 2 else [-0.3, 0.0, 0.0, 0.3]
        limit = 1.2 if varied == 2 else 0.6
        kids = {}
        for a, b in edges:
            kids.setdefault(a, []).append(b)
        todo = [0]
        while todo:
            a = todo.pop()
            for b in kids.get(a, []):
                rb = rooms[b]
                if rb.kind not in ("arena", "piece"):
                    rb.base = max(-limit, min(limit, rooms[a].base + rng.choice(steps)))
                else:
                    rb.base = 0.0
                todo.append(b)
        for r in rooms:
            r.base = round(r.base, 1)
    for _ in range(max(2, len(rooms) // 3)):                      # (loops: more than one way round)
        a, b = rng.sample(range(len(rooms)), 2)
        edges.append((a, b))
    for a, b in edges:
        if rng.random() < 0.3:
            _winding(L, centres[a], centres[b], rng)
        else:
            _corridor(L, centres[a], centres[b], rng, wide=rng.random() < 0.25)
    caches = _alcoves(L, rooms, rng, 3 + depth % 4)                  # (dead ends, with something at the end)
    # the heights: rooms raised and sunk, the corridors between them climbing in gentle steps
    in_room = {}
    for r in rooms:
        for x, y in r.cells():
            in_room[(x, y)] = r
    for r in rooms:
        if r.base:
            for x, y in r.cells():
                L.floor[y, x] += r.base
                L.ceil[y, x] += r.base
    # the rooms' shapes (after the corridors, which only cut through rock), and the set piece's letters
    for r in rooms:
        if r.kind == "piece":
            dress.place_piece(L, r, r.piece, rng)
        else:
            _shape(L, r, rng, alt_floor)
    _relax(L, in_room, caches)
    L.caches = caches
    L.rooms = rooms
    # where Claude comes in, and the way down: the room furthest from it
    start = rooms[0] if not guardian else rooms[0]
    sx, sy = start.centre
    dist = L.distances(sx, sy)
    far = rooms[-1] if guardian else max((r for r in rooms[1:] if r.kind != "piece"),
                                          key=lambda r: dist[r.centre[1], r.centre[0]])
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
        if r.kind == "piece":
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
    # chests: two to five a floor, against a wall in a room; and one at the end of most dead ends
    for (x, y) in caches:
        if rng.random() < 0.6:
            dress.chest(L, x, y, rng, rich=1.3)
        else:
            _pickup(L, x, y, rng, depth, "item")
    for r in rng.sample(rooms[1:], k=min(len(rooms) - 1, rng.randint(2, 5))):
        if r.kind == "piece":
            continue
        for _ in range(20):
            x, y = rng.randint(r.x, r.x + r.w - 1), rng.randint(r.y, r.y + r.h - 1)
            if L.open_at(x, y) and not _near(L, x, y, L.stairs, 2) and not clear_way(L, x, y) and \
                    any(not L.open_at(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                dress.chest(L, x, y, rng)
                break
    # things lying about: gold, potions, scrolls, and now and then something that glints
    for r in rooms[1:]:
        if r.kind == "piece":
            continue
        for _ in range(rng.randint(0, 2) + (1 if r.w * r.h > 60 else 0)):
            x, y = rng.randint(r.x, r.x + r.w - 1), rng.randint(r.y, r.y + r.h - 1)
            if L.open_at(x, y) and not clear_way(L, x, y) and not _near(L, x, y, L.stairs):
                _pickup(L, x, y, rng, depth)
    # the clutter (more of it: barrels and crates in clusters), and the torches
    props = BAND_PROPS[bi]
    for r in rooms:
        for _ in range(rng.randint(1, 5)):
            x, y = rng.randint(r.x, r.x + r.w - 1), rng.randint(r.y, r.y + r.h - 1)
            if not L.open_at(x, y) or _near(L, x, y, L.stairs) or _near(L, x, y, L.portal) or clear_way(L, x, y):
                continue
            edge = sum(not L.open_at(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge or rng.random() < 0.3:
                model = rng.choice(props)
                L.props.append({"model": model, "x": x + 0.5, "z": y + 0.5, "yaw": rng.uniform(0, math.tau),
                                "scale": rng.uniform(0.32, 0.45), "y": float(L.floor[y, x]),
                                "solid": model in ("barrel", "crate", "stump", "stump_moss", "willow_dead")})
        for _ in range(1 + (r.w * r.h) // 30):
            spot = _wall_spot(L, r, rng)
            if spot:
                L.lights.append(spot)
    dress.dress(L, rng, bi)
    from . import detail
    detail.detail(L, rng, bi)
    return L


def walkable_reach(L, radius=0.24):
    """The squares Claude's own body can walk to from where he comes in, things in the way and all (square to square,
    the way between looked at in small steps)."""
    from collections import deque
    sx, sy = int(L.start[0]), int(L.start[1])
    seen = {(sx, sy)}
    q = deque([(sx, sy)])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if (nx, ny) in seen or not L.open_at(nx, ny) or abs(L.floor[ny, nx] - L.floor[y, x]) > STEP:
                continue
            foot = max(L.floor[y, x], L.floor[ny, nx]) - 0.01
            if all(L.can_stand(x + 0.5 + dx * t, y + 0.5 + dy * t, radius, foot) for t in (0.25, 0.5, 0.75, 1.0)):
                seen.add((nx, ny))
                q.append((nx, ny))
    return seen


def clear_way(L, x, y):
    """A square that must stay free to walk: a corridor runs through it, or it's a passage a square wide."""
    if (x, y) in L.paths:
        return True
    return (not L.open_at(x - 1, y) and not L.open_at(x + 1, y)) or (not L.open_at(x, y - 1) and not L.open_at(x, y + 1))


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


def _pickup(L, x, y, rng, depth, kind=None):
    kind = kind or rng.choices(["gold", "gold", "gold", "health", "mana", "item", "scroll"], [5, 3, 2, 2, 2, 1.2, 0.3])[0]
    L.pickups.append({"x": x + rng.uniform(0.3, 0.7), "z": y + rng.uniform(0.3, 0.7), "y": float(L.floor[y, x]), "kind": kind,
                      "phase": rng.uniform(0, 6.28)})


def _winding(L, a, b, rng):
    """A corridor that wanders: a few doglegs between the rooms."""
    (x0, y0), (x1, y1) = a, b
    pts = [(x0, y0)]
    for _ in range(rng.randint(1, 3)):
        px, py = pts[-1]
        pts.append((max(2, min(L.w - 3, (px + x1) // 2 + rng.randint(-6, 6))), max(2, min(L.h - 3, (py + y1) // 2 + rng.randint(-6, 6)))))
    pts.append((x1, y1))
    for p, q in zip(pts, pts[1:]):
        _corridor(L, p, q, rng)


def _alcoves(L, rooms, rng, n):
    """Short dead-end passages off rooms' walls, a little alcove at their end: -> the alcoves' squares."""
    out = []
    for _ in range(n * 6):
        if len(out) >= n:
            break
        r = rng.choice(rooms[1:]) if len(rooms) > 1 else rooms[0]
        if r.kind not in ("plain", "hall", "dais", "pit", "split", "steps"):      # (not where a shape cuts rock away)
            continue
        side = rng.randrange(4)
        dx, dy = ((1, 0), (-1, 0), (0, 1), (0, -1))[side]
        sx = r.x + r.w if dx == 1 else r.x - 1 if dx == -1 else rng.randint(r.x + 1, r.x + r.w - 2)
        sy = r.y + r.h if dy == 1 else r.y - 1 if dy == -1 else rng.randint(r.y + 1, r.y + r.h - 2)
        length = rng.randint(3, 6)
        cells = [(sx + dx * k, sy + dy * k) for k in range(length)]
        ex, ey = cells[-1]
        ok = all(2 <= cx < L.w - 2 and 2 <= cy < L.h - 2 and L.solid[cy, cx] and
                 all(L.solid[cy + oy, cx + ox] for ox, oy in ((-dy, -dx), (dy, dx)) if (cx, cy) != cells[0]) for cx, cy in cells)
        ok = ok and all(L.solid[ey + oy, ex + ox] for ox in (-1, 0, 1) for oy in (-1, 0, 1) if (ox, oy) != (-dx, -dy))
        if not ok:
            continue
        ceil = rng.uniform(1.4, 1.8)
        for cx, cy in cells:
            L.solid[cy, cx] = False
            L.floor[cy, cx] = 0.0
            L.ceil[cy, cx] = ceil
            L.paths.add((cx, cy))
        L.paths.discard((ex, ey))
        L.paths.add((sx - dx, sy - dy))                     # (the room's square at its mouth stays open)
        out.append((ex, ey))
    return out


def _relax(L, in_room, extra=()):
    """The corridors' heights between the rooms' fixed ones: each square the mean of its neighbours, many times
    over, then cut to steps a tenth high - so a corridor climbs or falls between rooms in gentle steps."""
    cor = [(x, y) for (x, y) in list(L.paths) + list(extra) if L.open_at(x, y) and (x, y) not in in_room]
    if not cor:
        return
    ceil_h = {(x, y): float(L.ceil[y, x] - L.floor[y, x]) for (x, y) in cor}
    for _ in range(90):
        for (x, y) in cor:
            hs = [float(L.floor[y + dy, x + dx]) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if L.open_at(x + dx, y + dy)]
            if hs:
                L.floor[y, x] = sum(hs) / len(hs)
    for (x, y) in cor:
        L.floor[y, x] = round(float(L.floor[y, x]) * 10) / 10
        L.ceil[y, x] = L.floor[y, x] + ceil_h[(x, y)]


def _shape(L, r, rng, alt_floor):
    x0, y0, x1, y1 = r.x, r.y, r.x + r.w, r.y + r.h
    b = getattr(r, "base", 0.0)
    if r.kind == "pillars" and r.w >= 7 and r.h >= 7:
        for y in range(y0 + 2, y1 - 1, 3):
            for x in range(x0 + 2, x1 - 1, 3):
                if (x, y) not in L.paths:
                    L.solid[y, x] = True
    elif r.kind == "dais" and r.w >= 7 and r.h >= 7:
        L.floor[y0 + 2:y1 - 2, x0 + 2:x1 - 2] = b + 0.3
        L.floor[y0 + 3:y1 - 3, x0 + 3:x1 - 3] = b + 0.6
        L.ftex[y0 + 2:y1 - 2, x0 + 2:x1 - 2] = alt_floor
    elif r.kind == "pit" and r.w >= 7 and r.h >= 7:
        L.floor[y0 + 2:y1 - 2, x0 + 2:x1 - 2] = b - 0.35
        L.floor[y0 + 3:y1 - 3, x0 + 3:x1 - 3] = b - 0.7
    elif r.kind == "cross" and r.w >= 7 and r.h >= 7:      # four blocks of rock in the corners: a cross-shaped room
        for x, y in list(r.cells()):
            if (x < x0 + 2 or x >= x1 - 2) and (y < y0 + 2 or y >= y1 - 2):
                if not _corridor_mouth(L, x, y, r) and (x, y) not in L.paths:
                    L.solid[y, x] = True
    elif r.kind == "L" and r.w >= 7 and r.h >= 7:           # a corner of rock taken out of it
        cx, cy = (x0, y0) if rng.random() < 0.5 else (x1 - r.w // 2, y1 - r.h // 2)
        for y in range(cy, cy + r.h // 2):
            for x in range(cx, cx + r.w // 2):
                if (x, y) not in L.paths and not _corridor_mouth(L, x, y, r):
                    L.solid[y, x] = True
    elif r.kind == "ring" and r.w >= 8 and r.h >= 8:        # a block of rock in the middle: a walk round it
        for y in range(y0 + 2, y1 - 2):
            for x in range(x0 + 2, x1 - 2):
                if (x, y) not in L.paths:
                    L.solid[y, x] = True
    elif r.kind == "split":                                 # one half a step up
        if r.w >= r.h:
            L.floor[y0:y1, x0 + r.w // 2:x1] = b + 0.35
        else:
            L.floor[y0 + r.h // 2:y1, x0:x1] = b + 0.35
    elif r.kind == "steps":                                 # climbing across the room
        for k, x in enumerate(range(x0, x1)):
            L.floor[y0:y1, x] = b + 0.2 * (k // 2)
            L.ceil[y0:y1, x] = max(L.ceil[y0, x], L.floor[y0, x] + 1.9)
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
                L.decals.append((x + 0.5 + dx * 0.495, float(L.floor[y, x]) + 0.75, y + 0.5 + dy * 0.495, -dx, -dy,
                                 0.5, 0.6, f"t{dress.CM_THEME_OF_BAND[min(9, (L.depth - 1) // 10)]}.torch0"))
                return (px, float(L.floor[y, x]) + 1.15, pz, 1.0, 0.62, 0.28, 5.5)
    return None


# ---- Thornwick -------------------------------------------------------------------------------------------------------
TOWN_SIZE = 176


HOME_ANGLE = 2.75
FARM_COLS, FARM_ROWS = 5, 4


def _homestead(L, cx, cy, bark, roof):
    """The cabin (a log house, its door to the east), and north of it the farm: twenty squares of tilled earth in
    five columns, the first eight dug, the rest for later; the sign at the plot's east foot."""
    hx = int(round(cx + math.cos(HOME_ANGLE) * 18))
    hy = int(round(cy + math.sin(HOME_ANGLE) * 18))
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            L.solid[hy + dy, hx + dx] = True
            L.wtex[hy + dy, hx + dx] = bark
            L.top[hy + dy, hx + dx] = 2.4
    L.houses.append((hx - 2, hy - 2, hx + 3, hy + 3, 2.4, roof, (1, 0)))
    L.spots["cabin_door"] = (hx + 3.45, hy + 0.5)
    tilled = L.tex("ground.tilled")
    L.farm_cells = []
    for row in range(FARM_ROWS):                         # (the nearest row first: the first plots by the cabin)
        for col in range(FARM_COLS):
            x, y = hx - 2 + col, hy - 4 - row
            L.solid[y, x] = False
            L.ftex[y, x] = tilled
            L.floor[y, x] = 0.0
            L.farm_cells.append((x, y))
    sx, sy = hx + 4, hy - 4
    L.spots["sign"] = (sx + 0.5, sy + 0.5)
    planks = L.tex("ground.planks")
    L.boxes += [(sx + 0.45, 0.0, sy + 0.45, sx + 0.55, 1.15, sy + 0.55, "ground.planks"),
                (sx + 0.1, 0.75, sy + 0.42, sx + 0.9, 1.2, sy + 0.58, "ground.planks")]
    L.extra_blockers.append((sx + 0.5, sy + 0.5, 0.2))
    _ = planks


def cabin(seed=1):
    """Claude's cabin, inside: a room of logs and planks - the bed by the north wall, the hearth with its cauldron
    in the east wall, the chest he keeps things in, a table and a shelf, and the door south."""
    W, H = 9, 7
    L = Level(W, H, 0)
    L.kind = "cabin"
    L.name, L.line = "Claude's Cabin", "Home: four walls of logs, a fire, a bed, and the chest."
    L.tint, L.fog, L.ambient = (1.0, 0.95, 0.88), ((0.05, 0.04, 0.03), 0.02), 0.32
    L.tex("solid.bark")
    floor, wall, ceil = L.tex("ground.planks"), L.tex("solid.bark"), L.tex("ground.planks")
    L.wtex[:], L.ftex[:], L.ctex[:] = wall, floor, ceil
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            L.solid[y, x] = False
            L.floor[y, x] = 0.0
            L.ceil[y, x] = 2.5
    L.safe = ~L.solid
    for name in ("solid.plaster", "solid.hedge", "solid.townwall", "solid.roof"):
        L.tex(name)
    # the bed, against the north wall in the west corner
    L.boxes += [(1.05, 0.0, 1.02, 2.95, 0.32, 2.05, "ground.planks"),
                (1.1, 0.32, 1.06, 2.9, 0.48, 2.0, "solid.plaster"),
                (1.15, 0.48, 1.12, 1.55, 0.6, 1.94, "solid.plaster"),
                (1.6, 0.48, 1.04, 2.92, 0.54, 2.02, "solid.hedge"),
                (1.02, 0.0, 1.0, 1.12, 0.85, 2.07, "ground.planks")]
    L.extra_blockers += [(1.5, 1.5, 0.45), (2.5, 1.5, 0.45)]
    L.spots["bed"] = (2.0, 2.5)
    # the hearth: a block of stone in the east wall, a fire before it and the cauldron on it
    L.boxes += [(7.35, 0.0, 2.3, 8.0, 2.5, 4.7, "solid.townwall"),
                (7.0, 0.0, 2.6, 7.35, 0.25, 4.4, "solid.townwall")]
    L.extra_blockers += [(7.4, 3.5, 0.5)]
    L.sprites.append({"x": 7.25, "z": 3.5, "y": 0.25, "w": 0.6, "h": 0.55, "name": "sp.fire", "glow": (1.0, 0.55, 0.2), "solid": 0})
    L.sprites.append({"x": 7.05, "z": 3.5, "y": 0.2, "w": 0.75, "h": 0.65, "name": "lm.crucible", "glow": None, "solid": 0})
    L.lights.append((7.0, 0.8, 3.5, 1.0, 0.6, 0.28, 5.5))
    L.spots["hearth"] = (6.4, 3.5)
    # the chest, in the north-east corner
    L.chests.append({"x": 6.5, "z": 1.5, "y": 0.0, "opened": False, "broken": False, "yaw": 0.0, "guard": [], "rich": 0,
                     "stash": True})
    L.spots["stash"] = (6.5, 2.4)
    # a table and a shelf; a lamp over the table
    L.sprites.append({"x": 3.5, "z": 4.3, "y": 0.0, "w": 1.1, "h": 0.75, "name": "fu.table", "glow": None, "solid": 0.4})
    L.sprites.append({"x": 4.6, "z": 1.12, "y": 0.0, "w": 0.95, "h": 1.15, "name": "fu.shelf", "glow": None, "solid": 0.3})
    L.lights.append((3.5, 2.1, 4.0, 1.0, 0.8, 0.5, 6.0))
    # the door, south
    L.decals.append((4.5, 0.0, 5.995, 0, -1, 0.95, 1.6, "door"))
    L.spots["exit"] = (4.5, 5.4)
    L.start = (4.5, 4.9, 0.0)
    L.portal = None
    L.stairs = None
    return L


def town(seed=1):
    rng = random.Random(f"{seed}:town")
    S = TOWN_SIZE
    L = Level(S, S, 0, outdoor=True)
    L.name, L.line = D.TOWN_NAME, "Home: a clearing in the forest, a ring of roofs, and the Deep under the old stones."
    L.tint, L.fog, L.ambient = (1.0, 1.0, 1.0), ((0.40, 0.50, 0.52), 0.042), 0.55
    grass, dirt, cobble, flags = L.tex("ground.grass"), L.tex("ground.dirt"), L.tex("ground.cobbles"), L.tex("ground.flags")
    needles = L.tex("ground.needles")
    plaster, roof, bark = L.tex("solid.plaster"), L.tex("solid.roof"), L.tex("solid.bark")
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
        L.solid[sy, sx] = True                          # (an old standing stone: a rock, stood on end)
        L.props.append({"model": "rock2" if k % 2 else "rock1", "x": sx + 0.5, "z": sy + 0.5, "yaw": k * 1.7,
                        "scale": 2.1 + 0.3 * (k % 3), "y": 0.0})
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
    # Claude's cabin, its farm and the farm's sign (west of the square, between the Wandwright and the Outfitter)
    _homestead(L, cx, cy, bark, roof)
    # more houses, to make a town of it
    for k in range(7):
        ang = 0.35 + 0.8 + k * (math.tau / 7)
        if any(abs(((ang - a + math.pi) % math.tau) - math.pi) < 0.45 for a in list(spots.values()) + [HOME_ANGLE]):
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
    # the forest round it all (game/forest.py): its trails, its glades, its trees and its creatures
    solid_town = L.solid & clearing                           # (the houses and the stones)
    forest.grow(L, rng, cx, cy, clearing)
    L.solid |= solid_town
    keep_clear = set(L.farm_cells) | {(int(px) + dx, int(pz) + dy) for px, pz in L.spots.values() for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    for (x, y) in L.open_squares():
        if (x, y) in keep_clear:
            continue
        if 17.5 < r[y, x] < 22 and rng.random() < 0.06:
            L.props.append({"model": rng.choice(["bush", "bush2", "bushberries", "plant1", "plant2", "flowers", "rock1",
                                                 "stump_moss", "grass", "grass2"]),
                            "x": x + 0.5, "z": y + 0.5, "yaw": rng.uniform(0, math.tau), "scale": rng.uniform(0.5, 0.8),
                            "y": 0.0})
    L.start = (cx + 0.5, cy + 7.5, 0.0)
    L.kind = "town"
    return L
