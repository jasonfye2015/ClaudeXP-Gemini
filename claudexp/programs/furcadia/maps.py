"""Claudecadia's maps: Willowmere Commons (the town everyone starts in) and three dreams reached through its portals.

Grid coordinates: x runs down-right on screen, y down-left. Each map is built in code with a few drawing helpers,
from a fixed seed, so it's the same every time.
"""
import random
from collections import deque

from . import art


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
        self.night = False
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
        if not self.inside(x, y) or not art.walkable_floor(self.floor[y][x]):
            return False
        o = self.obj.get((x, y))
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
    m.night = True
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
    for pos in ((25, 19), (25, 20)):
        m.put(*pos, "barrel")
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
    m.spawn = (16, 16)
    return m


def all_maps():
    return {m.id: m for m in (commons(), glade(), seaside(), inn())}
