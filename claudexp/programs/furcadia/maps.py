"""Claudecadia's maps: Willowmere Commons (the town everyone starts in) and the dreams beyond it. Three portals in
the Commons lead to the Glade, the Seaside and the Inn; the other dreams are found further in, through portals
tucked away in those (and in each other).

Grid coordinates: x runs down-right on screen, y down-left. Each map is built in code with a few drawing helpers,
from a fixed seed, so it's the same every time.
"""
import random
from collections import deque

from . import art

FLOATS = {"lilypad", "portal"}


class Map:
    def __init__(self, mid, name, desc, w, h, base, seed):
        self.id, self.name, self.desc = mid, name, desc
        self.w, self.h = w, h
        self.base = base
        self.floor = [[base] * w for _ in range(h)]
        self.obj = {}
        self.portals = {}            # (x, y) -> target map id
        self.signs = {}              # (x, y) -> text
        self.spawn = (w // 2, h // 2)
        self.tint = None             # (r, g, b, a) laid over the map: night, caves, underwater
        self.particles = None        # "fireflies", "snow", "bubbles" or "stars"
        self.rnd = random.Random(seed)

    # ---- building ----------------------------------------------------------------------------------------
    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def set(self, x, y, floor):
        if self.inside(x, y):
            self.floor[y][x] = floor

    def put(self, x, y, obj):
        if self.inside(x, y):
            self.obj[(x, y)] = obj

    def rect(self, x0, y0, x1, y1, floor):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, floor)

    def disk(self, cx, cy, r, floor):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + r:
                    self.set(x, y, floor)

    def line(self, x0, y0, x1, y1, floor, width=1):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            x = round(x0 + (x1 - x0) * i / steps)
            y = round(y0 + (y1 - y0) * i / steps)
            for dx in range(width):
                for dy in range(width):
                    self.set(x + dx, y + dy, floor)

    def border(self, objs, depth=2, chance=0.85):
        for y in range(self.h):
            for x in range(self.w):
                edge = min(x, y, self.w - 1 - x, self.h - 1 - y)
                if edge < depth and (edge == 0 or self.rnd.random() < chance) and (x, y) not in self.obj and                         self.floor[y][x] == self.base:
                    self.put(x, y, self.rnd.choice(objs))

    def clear_line(self, x0, y0, x1, y1, floor=None):
        """A trail: no solid objects along a line (and optionally a floor)."""
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            x = round(x0 + (x1 - x0) * i / steps)
            y = round(y0 + (y1 - y0) * i / steps)
            if floor:
                self.set(x, y, floor)
            o = self.obj.get((x, y))
            if o and not art.obj_walkable(o):
                del self.obj[(x, y)]

    def ring(self, cx, cy, r, obj, n=8):
        import math
        for i in range(n):
            a = 2 * math.pi * i / n
            self.put(round(cx + math.cos(a) * r), round(cy + math.sin(a) * r), obj)

    def scatter(self, objs, n, floors, keep_clear=()):
        tries = 0
        while n > 0 and tries < n * 40:
            tries += 1
            x, y = self.rnd.randrange(self.w), self.rnd.randrange(self.h)
            if self.floor[y][x] in floors and (x, y) not in self.obj and \
                    all(abs(x - cx) + abs(y - cy) > r for cx, cy, r in keep_clear):
                self.put(x, y, self.rnd.choice(objs))
                n -= 1

    def portal(self, x, y, target, label):
        self.put(x, y, "portal")
        self.portals[(x, y)] = target
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):      # keep the way in clear
            if self.obj.get((nx, ny)) and not art.obj_walkable(self.obj[(nx, ny)]):
                del self.obj[(nx, ny)]
        for nx, ny in ((x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1), (x + 1, y + 1)):
            if self.obj.get((nx, ny)) and not art.obj_walkable(self.obj[(nx, ny)]):
                del self.obj[(nx, ny)]
            if self.inside(nx, ny) and (nx, ny) not in self.obj and art.walkable_floor(self.floor[ny][nx]):
                self.put(nx, ny, "sign")
                self.signs[(nx, ny)] = label
                break

    # ---- using -------------------------------------------------------------------------------------------
    def walkable(self, x, y):
        if not self.inside(x, y):
            return False
        o = self.obj.get((x, y))
        if o in FLOATS:                              # lily pads (and portals) can sit on water
            return True
        if not art.walkable_floor(self.floor[y][x]):
            return False
        return o is None or art.obj_walkable(o)

    def seat(self, x, y):
        o = self.obj.get((x, y))
        return o is not None and art.obj_seat(o)

    def seats(self):
        return [pos for pos, o in self.obj.items() if art.obj_seat(o)]

    def path(self, start, goal, blocked=frozenset()):
        """Shortest hop path from start to goal (excluding start), or [] if there's none."""
        if start == goal or not self.walkable(*goal):
            return []
        prev = {start: None}
        q = deque([start])
        while q:
            cur = q.popleft()
            if cur == goal:
                break
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (cur[0] + dx, cur[1] + dy)
                if nxt not in prev and self.walkable(*nxt) and (nxt not in blocked or nxt == goal):
                    prev[nxt] = cur
                    q.append(nxt)
        if goal not in prev:
            return []
        out = []
        cur = goal
        while cur != start:
            out.append(cur)
            cur = prev[cur]
        return out[::-1]

    def free_near(self, x, y, taken, radius=6):
        """The nearest walkable tile to (x, y) that nobody stands on (and isn't a portal)."""
        for r in range(radius + 1):
            ring = [(x + dx, y + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)
                    if max(abs(dx), abs(dy)) == r]
            self.rnd.shuffle(ring)
            for pos in ring:
                if self.walkable(*pos) and pos not in taken and pos not in self.portals:
                    return pos
        return (x, y)

    def arrival_from(self, other_id):
        """Where you appear when you come through from another map: beside the portal that leads back."""
        for pos, target in self.portals.items():
            if target == other_id:
                return pos
        return self.spawn

    def random_walkable(self):
        for _ in range(400):
            x, y = self.rnd.randrange(self.w), self.rnd.randrange(self.h)
            if self.walkable(x, y) and (x, y) not in self.portals:
                return (x, y)
        return self.spawn


# ---- the maps -----------------------------------------------------------------------------------------------

def commons():
    m = Map("commons", "Willowmere Commons",
            "The friendly town square where every furre arrives: a cobbled plaza around a fountain, benches and "
            "lamp posts, flower beds, a duck pond, and three glowing portals to the dreams.",
            30, 30, "grass", 101)
    m.disk(15, 15, 5, "cobble")
    m.line(2, 15, 10, 15, "dirt", 2)
    m.line(15, 2, 15, 10, "dirt", 2)
    m.line(20, 15, 27, 15, "dirt", 2)
    m.line(15, 20, 15, 27, "dirt", 2)
    m.disk(22, 7, 3, "water")
    m.disk(22, 7, 1, "deepwater")
    for (x, y) in ((8, 9), (9, 22), (21, 22)):
        m.disk(x, y, 1, "flowers")
    m.put(15, 15, "fountain")
    for pos in ((11, 13), (11, 18), (19, 13), (19, 18), (13, 11), (18, 11), (13, 19), (18, 19)):
        m.put(*pos, "bench")
    for pos in ((11, 11), (20, 11), (11, 20), (20, 20), (6, 13), (24, 17)):
        m.put(*pos, "lamp")
    for pos in ((18, 5), (25, 9), (19, 9), (24, 4)):
        m.put(*pos, "rock")
    m.border(["tree", "tree", "pine", "bigtree", "bush"], depth=2)
    m.scatter(["tree", "bush", "bush", "pine"], 22, ("grass",), keep_clear=((15, 15, 8), (4, 15, 3), (15, 4, 3),
                                                                           (26, 15, 3), (15, 26, 3)))
    m.scatter(["mushroom"], 4, ("grass",), keep_clear=((15, 15, 7),))
    m.line(4, 8, 10, 14, "dirt", 1)
    m.line(22, 23, 26, 22, "dirt", 1)
    m.clear_line(4, 8, 10, 14)
    m.clear_line(22, 23, 26, 22)
    m.portal(4, 8, "meadow", "To the Sunflower Meadow")
    m.portal(26, 22, "market", "To the Lantern Night Market")
    m.portal(15, 2, "glade", "To the Moonlit Glade")
    m.portal(27, 15, "seaside", "To the Seaside Boardwalk")
    m.portal(15, 27, "inn", "To the Hearthstone Inn")
    m.put(3, 13, "sign")
    m.signs[(3, 13)] = ("Welcome to Willowmere Commons! Walk with the arrow keys or click where to go. Step on a "
                        "glowing portal to visit a dream.")
    m.spawn = (4, 15)
    return m


def glade():
    m = Map("glade", "The Moonlit Glade",
            "A clearing in a pine forest under a full moon: a crackling campfire ringed with logs to sit on, "
            "fireflies, red mushrooms, and a little stream with a plank bridge.",
            26, 26, "darkgrass", 202)
    m.tint, m.particles = (10, 16, 60, 120), "fireflies"
    m.disk(13, 12, 4, "dirt")
    m.line(2, 20, 24, 4, "water", 2)
    m.line(13, 13, 13, 24, "dirt", 1)
    for y in range(9, 14):                       # the plank bridge over the stream
        for x in range(9, 17):
            if m.floor[y][x] == "water":
                m.set(x, y, "wood")
    m.put(13, 12, "campfire")
    for pos in ((11, 12), (15, 12), (13, 10), (13, 14), (11, 10), (15, 14)):
        m.put(*pos, "log")
    for pos in ((10, 15), (17, 9), (8, 8)):
        m.put(*pos, "lantern")
    m.border(["pine", "pine", "tree", "bigtree"], depth=3, chance=0.8)
    m.scatter(["pine", "tree", "bush"], 26, ("darkgrass",), keep_clear=((13, 12, 6), (13, 22, 2)))
    m.scatter(["mushroom"], 12, ("darkgrass",), keep_clear=((13, 12, 4),))
    m.scatter(["rock"], 5, ("darkgrass",), keep_clear=((13, 12, 5),))
    m.portal(13, 23, "commons", "Back to Willowmere Commons")
    m.line(13, 8, 13, 3, "dirt", 1)                  # a trail north into the snow
    m.clear_line(13, 8, 13, 3)
    m.portal(13, 3, "frost", "A cold wind blows from the north...")
    m.clear_line(11, 10, 5, 5)                        # a faint deer path to a fairy ring
    m.portal(4, 4, "caverns", "A ring of mushrooms hums softly.")
    m.ring(4, 4, 2, "mushroom", 10)
    m.spawn = (13, 21)
    return m


def seaside():
    m = Map("seaside", "The Seaside Boardwalk",
            "A sunny beach with a wooden boardwalk, a little café deck with striped umbrellas and a counter that "
            "sells lemonade, palm trees, seashells, and a pier out over the waves.",
            28, 28, "sand", 303)
    for y in range(m.h):
        for x in range(m.w):
            wave = (y * 7) % 3 - 1
            if x >= 20 + wave:
                m.set(x, y, "water" if x < 24 + wave else "deepwater")
    m.rect(14, 0, 15, 27, "boardwalk")
    m.rect(5, 7, 12, 17, "boardwalk")
    m.rect(16, 19, 25, 20, "boardwalk")        # the pier
    for pos in ((7, 9), (10, 9), (7, 13), (10, 13), (8, 16)):
        m.put(*pos, "umbrella")
        x, y = pos
        for cx, cy in ((x - 1, y), (x + 1, y), (x, y + 1)):
            if m.walkable(cx, cy) and (cx, cy) not in m.obj:
                m.put(cx, cy, "chair")
    for x in range(5, 9):
        m.put(x, 7, "counter")
    m.put(9, 7, "barrel")
    m.put(12, 7, "plant")
    m.put(5, 17, "plant")
    for y in (2, 6, 11, 22, 25):
        m.put(13, y, "lamp" if y % 2 else "palm")
    m.scatter(["palm", "palm", "rock"], 14, ("sand",), keep_clear=((8, 12, 7), (3, 14, 2)))
    m.scatter(["shell"], 10, ("sand",), keep_clear=((8, 12, 6),))
    m.put(24, 20, "barrel")
    m.portal(25, 19, "coral", "Dive here! (Coral Grotto)")
    m.clear_line(4, 16, 6, 25)
    m.portal(6, 25, "oasis", "Follow the dunes to the Desert Oasis")
    m.put(20, 19, "stool")
    m.put(22, 20, "stool")
    m.portal(2, 14, "commons", "Back to Willowmere Commons")
    m.spawn = (4, 14)
    return m


def inn():
    m = Map("inn", "The Hearthstone Inn",
            "A warm wooden tavern: a big stone fireplace with cushions on the rug in front of it, tables and chairs, "
            "a bar counter with stools, barrels, and shelves full of books.",
            20, 20, "wood", 404)
    m.rect(6, 4, 12, 9, "rug")
    for x in range(m.w):
        m.put(x, 0, "woodwall")
    for y in range(1, m.h):
        m.put(0, y, "woodwall")
    m.put(9, 1, "fireplace")
    for x in (3, 4, 14, 15):
        m.put(x, 1, "bookshelf")
    for pos in ((7, 5), (9, 4), (11, 5), (8, 7), (10, 7)):
        m.put(*pos, "cushion")
    for pos in ((5, 12), (10, 13), (5, 16), (11, 17)):
        m.put(*pos, "table")
        x, y = pos
        for cx, cy in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if m.walkable(cx, cy) and (cx, cy) not in m.obj:
                m.put(cx, cy, "chair")
    for y in range(3, 9):
        m.put(16, y, "counter")
    for y in (3, 5, 7):
        m.put(15, y, "stool")
    for y in (1, 2):
        m.put(18, y, "barrel")
    m.put(17, 1, "barrel")
    m.put(1, 1, "plant")
    m.put(1, 18, "plant")
    for y in (4, 5, 9, 10):
        m.put(1, y, "bookshelf")
    m.put(1, 13, "lantern")
    m.portal(17, 18, "commons", "Back to Willowmere Commons")
    m.portal(18, 6, "observatory", "A spiral stair leads up to the Starlight Observatory")
    m.spawn = (16, 16)
    return m


def frost():
    m = Map("frost", "Frostpine Hollow",
            "A snowy hollow ringed with frosted pines: a frozen pond to slide on, snowmen built by earlier visitors, "
            "and a little campfire with logs to warm your paws by. Snow is gently falling.",
            26, 26, "snow", 505)
    m.particles = "snow"
    m.disk(13, 12, 4, "ice")
    m.disk(7, 19, 2, "dirt")
    m.put(7, 19, "campfire")
    for pos in ((5, 19), (9, 19), (7, 17), (7, 21)):
        m.put(*pos, "log")
    for pos in ((18, 18), (19, 7), (8, 8)):
        m.put(*pos, "snowman")
    m.put(16, 21, "lantern")
    m.put(10, 21, "lantern")
    m.border(["snowpine", "snowpine", "pine"], depth=3, chance=0.85)
    m.scatter(["snowpine", "rock"], 18, ("snow",), keep_clear=((13, 12, 6), (7, 19, 3), (13, 22, 2)))
    m.portal(13, 23, "glade", "Back to the Moonlit Glade")
    m.spawn = (13, 21)
    return m


def caverns():
    m = Map("caverns", "The Crystal Caverns",
            "A cave deep under the glade, lit only by glowing crystals and a few torches: stalagmites, an "
            "underground lake, and strange luminous mushrooms.",
            26, 26, "cave", 606)
    m.tint = (8, 6, 24, 165)
    m.disk(16, 9, 3, "water")
    m.disk(16, 9, 1, "deepwater")
    m.border(["stalagmite", "stalagmite", "rock"], depth=3, chance=0.9)
    m.scatter(["stalagmite", "rock"], 16, ("cave",), keep_clear=((13, 22, 3), (13, 13, 3)))
    m.scatter(["crystal"], 12, ("cave",), keep_clear=((13, 22, 2),))
    m.scatter(["mushroom"], 8, ("cave",), keep_clear=((13, 22, 2),))
    for pos in ((10, 20), (16, 20), (8, 12), (19, 14)):
        m.put(*pos, "torch")
    m.put(12, 13, "crystal")
    m.put(14, 13, "crystal")
    for pos in ((12, 15), (14, 15), (13, 16)):
        m.put(*pos, "cushion")
    m.put(20, 5, "chest")
    m.portal(13, 23, "glade", "Back up to the Moonlit Glade")
    m.spawn = (13, 21)
    return m


def meadow():
    m = Map("meadow", "The Sunflower Meadow",
            "Rolling farm fields on a summer afternoon: rows of sunflowers, golden wheat, hay bales to sit on, a "
            "friendly scarecrow and a winding dirt lane.",
            28, 28, "grass", 707)
    m.rect(3, 3, 11, 10, "wheat")
    m.rect(16, 15, 24, 23, "wheat")
    m.line(14, 26, 14, 14, "dirt", 2)
    m.line(14, 14, 25, 6, "dirt", 2)
    m.line(14, 14, 4, 20, "dirt", 1)
    for x in range(17, 24, 2):
        for y in (4, 6, 8, 10):
            m.put(x, y, "sunflower")
    m.disk(6, 22, 2, "flowers")
    m.put(7, 7, "scarecrow")
    m.put(20, 19, "scarecrow")
    for pos in ((11, 16), (12, 18), (17, 13), (9, 13), (5, 15)):
        m.put(*pos, "hay")
    for x in range(3, 12):
        m.put(x, 12, "fence")
    m.put(12, 21, "tree")
    m.put(22, 25, "tree")
    m.border(["tree", "bush", "bigtree", "bush"], depth=2, chance=0.7)
    m.scatter(["bush", "tree"], 8, ("grass",), keep_clear=((14, 14, 5), (14, 25, 2), (25, 6, 2)))
    m.portal(14, 26, "commons", "Back to Willowmere Commons")
    m.portal(25, 6, "marsh", "Down to the Lily Pond Marsh")
    m.spawn = (14, 24)
    return m


def marsh():
    m = Map("marsh", "The Lily Pond Marsh",
            "A misty wetland of still water and reeds: boardwalks, mossy islands with logs to sit on, and lily pads "
            "you can hop across if you're brave.",
            26, 26, "water", 808)
    m.disk(5, 13, 3, "mud")
    m.disk(18, 7, 3, "grass")
    m.disk(17, 19, 3, "grass")
    m.rect(5, 12, 17, 13, "boardwalk")
    m.rect(16, 8, 17, 19, "boardwalk")
    for pos in ((19, 8), (17, 5), (18, 20), (15, 18)):
        m.put(*pos, "log")
    for pos in ((10, 16), (11, 17), (12, 18), (13, 19), (14, 20), (9, 9), (10, 8), (11, 7), (12, 6), (13, 5),
                (14, 5), (15, 5), (16, 5)):
        m.put(*pos, "lilypad")
    m.scatter(["reeds"], 30, ("water",))
    m.scatter(["reeds", "bush"], 6, ("grass", "mud"), keep_clear=((3, 13, 2),))
    m.put(19, 21, "tree")
    m.put(20, 6, "tree")
    m.put(7, 15, "lantern")
    m.portal(3, 13, "meadow", "Back up to the Sunflower Meadow")
    m.spawn = (5, 12)
    return m


def observatory():
    m = Map("observatory", "The Starlight Observatory",
            "A domed marble observatory at the top of the inn's spiral stair: a great brass telescope, star charts, "
            "cushions for stargazing, and the night sky glittering overhead.",
            20, 20, "marble", 909)
    m.tint, m.particles = (12, 16, 60, 110), "stars"
    m.disk(10, 10, 4, "rug")
    for x in range(m.w):
        m.put(x, 0, "wall")
    for y in range(1, m.h):
        m.put(0, y, "wall")
    m.put(10, 10, "telescope")
    m.ring(10, 10, 3, "cushion", 6)
    for x in (3, 4, 5):
        m.put(x, 1, "bookshelf")
    for pos in ((14, 1), (1, 6), (1, 14)):
        m.put(*pos, "column")
    m.put(1, 9, "chest")
    for pos in ((6, 5), (15, 15), (5, 15)):
        m.put(*pos, "plant")
    for pos in ((16, 4), (4, 12)):
        m.put(*pos, "lantern")
    m.portal(17, 18, "inn", "Down the stair to the Hearthstone Inn")
    m.portal(2, 17, "sky", "A shimmering stair climbs into the clouds")
    m.spawn = (16, 16)
    return m


def sky():
    m = Map("sky", "The Sky Isles",
            "Islands of cloud floating high above the world, joined by rainbow bridges: old marble columns, a "
            "statue of a winged dreamer, and a treasure chest on the farthest isle.",
            30, 30, "sky", 1010)
    for cx, cy, r in ((6, 23, 4), (16, 15, 5), (24, 6, 4), (7, 7, 3), (24, 23, 3)):
        m.disk(cx, cy, r, "cloud")
    m.line(9, 21, 12, 18, "rainbow", 2)
    m.line(19, 12, 22, 9, "rainbow", 2)
    m.line(8, 9, 12, 13, "rainbow", 2)
    m.line(19, 18, 22, 21, "rainbow", 2)
    m.put(16, 15, "statue")
    for pos in ((13, 13), (19, 13), (13, 17), (19, 17)):
        m.put(*pos, "column")
    m.put(26, 5, "chest")
    m.put(7, 6, "crystal")
    m.put(25, 24, "ruin")
    m.set(23, 22, "flowers")
    for pos in ((15, 18), (17, 12), (5, 21), (25, 7)):
        m.put(*pos, "bench")
    m.portal(5, 25, "observatory", "Back down to the Starlight Observatory")
    m.spawn = (6, 23)
    return m


def oasis():
    m = Map("oasis", "The Desert Oasis",
            "Endless dunes around a palm-ringed pool of cool water: a camp of striped tents around a fire, cacti in "
            "bloom, and the tumbled stones of something very old to the south.",
            28, 28, "sand", 1111)
    m.disk(14, 12, 5, "grass")
    m.disk(14, 12, 3, "water")
    m.ring(14, 12, 5, "palm", 9)
    for pos in ((7, 20), (11, 22), (5, 16)):
        m.put(*pos, "tent")
    m.put(9, 18, "campfire")
    for pos in ((8, 17), (10, 19), (8, 19)):
        m.put(*pos, "log")
    m.scatter(["cactus", "cactus", "rock"], 16, ("sand",), keep_clear=((14, 12, 7), (8, 19, 4), (3, 14, 2),
                                                                        (24, 24, 3)))
    for pos in ((21, 21), (23, 20), (20, 24)):
        m.put(*pos, "ruin")
    m.portal(3, 14, "seaside", "Back to the Seaside Boardwalk")
    m.portal(24, 24, "ruins", "Into the Ancient Ruins")
    m.spawn = (5, 13)
    return m


def ruins():
    m = Map("ruins", "The Ancient Ruins",
            "An overgrown temple of a forgotten furre civilisation: rows of marble columns, broken and whole, weathered "
            "statues, a sunken plaza, and vines everywhere.",
            26, 26, "grass", 1212)
    m.rect(6, 6, 19, 19, "flagstone")
    m.rect(10, 10, 15, 15, "marble")
    for i in range(6, 20, 3):
        m.put(i, 6, "column" if i % 2 else "ruin")
        m.put(i, 19, "ruin" if i % 2 else "column")
        m.put(6, i, "column" if i % 2 == 0 else "ruin")
        m.put(19, i, "ruin")
    m.put(12, 12, "statue")
    m.put(14, 14, "statue")
    m.put(13, 11, "chest")
    for pos in ((10, 13), (15, 12), (11, 15)):
        m.put(*pos, "bench")
    for pos in ((10, 10), (15, 15)):
        m.put(*pos, "torch")
    m.border(["tree", "bigtree", "bush", "ruin"], depth=2, chance=0.8)
    m.scatter(["bush", "tree", "ruin", "rock"], 16, ("grass",), keep_clear=((13, 3, 2),))
    m.clear_line(13, 3, 13, 10, "flagstone")
    m.portal(13, 2, "oasis", "Back to the Desert Oasis")
    m.spawn = (13, 4)
    return m


def market():
    m = Map("market", "The Lantern Night Market",
            "A bustling night bazaar: rows of striped stalls selling trinkets and sweets, strings of lanterns, "
            "torches, and tables where furres sit and share treats under the stars.",
            26, 26, "cobble", 1313)
    m.tint, m.particles = (16, 18, 60, 105), "fireflies"
    for y in (6, 11, 16):
        for x in range(6, 21, 4):
            m.put(x, y, "stall")
    for x in range(5, 22, 3):
        m.put(x, 3, "lantern")
        m.put(x, 21, "lantern")
    for pos in ((9, 19), (14, 19), (19, 19)):
        m.put(*pos, "table")
        x, y = pos
        m.put(x - 1, y, "stool")
        m.put(x + 1, y, "stool")
    for pos in ((4, 9), (4, 14), (22, 9), (22, 14)):
        m.put(*pos, "bench")
    for pos in ((3, 4), (22, 4), (3, 22), (22, 22)):
        m.put(*pos, "torch")
    for pos in ((21, 7), (5, 17), (21, 17)):
        m.put(*pos, "barrel")
    m.put(5, 7, "crate")
    m.put(12, 13, "fountain")
    m.portal(2, 13, "commons", "Back to Willowmere Commons")
    m.spawn = (4, 12)
    return m


def coral():
    m = Map("coral", "The Coral Grotto",
            "Under the waves off the pier, somehow you can breathe: a sandy sea floor with bright coral, swaying "
            "kelp, glittering shells, a sunken statue and an old treasure chest. Bubbles drift upward.",
            26, 26, "seafloor", 1414)
    m.tint, m.particles = (20, 110, 210, 105), "bubbles"
    m.border(["rock", "coral", "kelp"], depth=2, chance=0.85)
    m.scatter(["coral", "coral", "kelp", "rock"], 30, ("seafloor",), keep_clear=((13, 22, 3), (13, 12, 3)))
    m.scatter(["shell"], 14, ("seafloor",))
    m.put(13, 11, "statue")
    m.put(8, 6, "chest")
    for pos in ((11, 13), (15, 13), (13, 14)):
        m.put(*pos, "rock")
    m.put(12, 15, "log")
    m.portal(13, 23, "seaside", "Swim back up to the Seaside Boardwalk")
    m.spawn = (13, 21)
    return m


def all_maps():
    return {m.id: m for m in (commons(), glade(), seaside(), inn(), frost(), caverns(), meadow(), marsh(),
                               observatory(), sky(), oasis(), ruins(), market(), coral())}


def route(maps, start, goal):
    """The first portal to take from map 'start' towards map 'goal' (or None)."""
    from collections import deque as _dq
    prev = {start: None}
    q = _dq([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for pos, target in maps[cur].portals.items():
            if target in maps and target not in prev:
                prev[target] = (cur, pos)
                q.append(target)
    if goal not in prev or goal == start:
        return None
    cur = goal
    while prev[cur][0] != start:
        cur = prev[cur][0]
    return prev[cur][1]
