"""The layers: a cave carved into a tile grid, descending left to right and down, with ledges, drops, pools,
glass, the loot earlier expeditions left, a trader's camp, lore notes, and the hatch down. Layer 5 holds the cargo.

Tiles: 0 air, 1 rock, 2 water, 3 glass (cuts bare legs), 4 hatch, 5 ledge (one-way platform). Things stand in
`things`: dicts with "kind" (loot, note, trader, cargo, light) and a tile position."""
import random

TW = 16                      # a tile in map pixels (drawn at 2x)
W, H = 150, 46
LAYER_NAMES = ["The Shallows", "Glass Gardens", "The Flooded Halls", "The Dark", "The Bottom"]
TRADERS = {1: "dune", 3: "mil", 5: "exp"}

LOOT = {
    "common": ["gauze", "gauze", "water", "bread", "banana", "scrap", "scrap", "stick", "cloth", "candy", "canteen", "tin"],
    "medical": ["gauze", "medkit", "pills", "acidfruit", "acidfruit", "tweezers", "syringe", "splint", "blanket"],
    "tools": ["flashlight", "battery", "battery", "knife", "rope", "rope", "shovel", "torch", "aed"],
    "odd": ["vial", "hat", "wrap", "crystal", "sweet", "meat", "jar", "bag"],
}


class Layer:
    def __init__(self, index, preset, seed=None):
        self.index = index                       # 1..5
        self.preset = preset
        self.rng = random.Random(seed if seed is not None else random.randrange(1 << 30))
        self.name = LAYER_NAMES[index - 1]
        self.tiles = [[1] * W for _ in range(H)]
        self.things = []
        self.cold = 0.6 + 0.35 * index           # how cold the water is
        self.dark = index >= 3                   # a flashlight matters from here down
        self.danger = preset["danger"] * (0.7 + 0.15 * index)
        self._carve()

    # ---- building -------------------------------------------------------------------------------------------
    def _room(self, x, y, w, h):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if 1 <= xx < W - 1 and 1 <= yy < H - 1:
                    self.tiles[yy][xx] = 0

    def _carve(self):
        rng = self.rng
        x, y = 4, 6
        self._room(2, 4, 14, 7)                   # the arrival ledge
        self.start = (5, 10)
        rooms = [(2, 4, 14, 7)]
        floor_y = 10
        step = 0
        while x < W - 24 and floor_y < H - 8:
            step += 1
            # a corridor on, then a drop
            run = rng.randint(8, 16)
            if x + 12 + run >= W - 20:
                break
            self._room(x, floor_y - 4, 12 + run, 5)        # on from where the last room ended
            x = x + 12 + run - 3
            drop = rng.randint(3, 5 + int(2 * self.index * self.preset["danger"]))
            drop = min(drop, H - 9 - floor_y)
            if drop <= 0:
                break
            shaft_w = rng.randint(3, 6)
            self._room(x, floor_y - 4, shaft_w, drop + 5)
            # ledges to break a long fall
            if drop > 7 and rng.random() < 0.7:
                ly = floor_y + drop // 2
                for lx in range(x, x + shaft_w):
                    if lx != x + shaft_w // 2:
                        self.tiles[ly][lx] = 5
            floor_y += drop
            rw, rh = rng.randint(10, 18), rng.randint(5, 8)
            rw = min(rw, W - 6 - x)
            if rw < 6 or floor_y >= H - 4:
                break
            self._room(x - 2, floor_y - rh + 1, rw + 4, rh)
            rooms.append((x - 2, floor_y - rh + 1, rw + 4, rh))
            # water in some rooms
            if rng.random() < 0.25 + 0.1 * self.index and floor_y < H - 4:
                depth = rng.randint(1, 2 + self.index // 2)
                for yy in range(floor_y - depth + 1, floor_y + 1):
                    for xx in range(x, x + rw):
                        if self.tiles[yy][xx] == 0:
                            self.tiles[yy][xx] = 2
                for yy in range(floor_y + 1, min(H - 1, floor_y + depth + 1)):
                    for xx in range(x, x + rw):
                        self.tiles[yy][xx] = 2 if self.tiles[yy][xx] == 1 else self.tiles[yy][xx]
            # glass on some floors
            if rng.random() < 0.2 + 0.12 * self.index:
                gx = rng.randint(x + 1, x + rw - 4)
                for xx in range(gx, gx + rng.randint(2, 5)):
                    if self.tiles[floor_y][xx] == 0 and self.tiles[floor_y + 1][xx] == 1:
                        self.tiles[floor_y][xx] = 3
            # loot
            for _ in range(rng.randint(2, 3) + (1 if rng.random() < self.preset["loot"] - 1 else 0)):
                lx = rng.randint(x, x + rw - 1)
                if self.tiles[floor_y][lx] == 0 and self.tiles[floor_y + 1][lx] in (1, 5):
                    self.things.append({"kind": "loot", "x": lx, "y": floor_y, "items": self._loot(), "open": False})
            if rng.random() < 0.3:
                nx = rng.randint(x, x + rw - 1)
                if self.tiles[floor_y][nx] == 0:
                    self.things.append({"kind": "note", "x": nx, "y": floor_y, "note": rng.randrange(24), "read": False})
            if rng.random() < 0.5:
                self.things.append({"kind": "light", "x": x + rw // 2, "y": floor_y - rh + 2})
            x += rw
        # the exit room
        ex = min(W - 14, x + 4)
        ey = min(H - 3, floor_y)
        self._room(ex - 6, ey - 6, 16, 7)
        for xx in range(ex - 8, ex + 10):                # the exit room: dry, with solid ground under it
            for yy in range(ey - 6, ey + 1):
                if self.tiles[yy][xx] in (2, 3):
                    self.tiles[yy][xx] = 0
            for yy in range(ey + 1, min(H, ey + 4)):
                if self.tiles[yy][xx] in (0, 2, 3):
                    self.tiles[yy][xx] = 1
        self.exit = (ex + 4, ey + 1)               # the hatch is set into the floor you stand on
        if self.index < 5:
            for hx in (ex + 3, ex + 4, ex + 5):
                self.tiles[ey + 1][hx] = 4
        else:
            self.things.append({"kind": "cargo", "x": ex + 4, "y": ey})
        self.things.append({"kind": "light", "x": ex + 2, "y": ey - 4})
        # the trader's camp in a middle room
        kind = TRADERS.get(self.index)
        if kind and len(rooms) > 2:
            rx, ry, rw, rh = rooms[len(rooms) // 2]
            tx = rx + rw // 2
            ty = ry + rh - 1
            while ty < H - 2 and self.tiles[ty + 1][tx] not in (1, 5):
                ty += 1
            for xx in range(tx - 3, tx + 4):
                if self.tiles[ty][xx] == 3:
                    self.tiles[ty][xx] = 0
            self.things.append({"kind": "trader", "x": tx, "y": ty, "trader": kind, "stock": self._stock(kind)})
            self.things.append({"kind": "light", "x": tx, "y": ty - 3})
        # make sure nothing solid blocks the start, and every pool has a way out
        self._room(2, 4, 14, 7)
        for row in range(1, H - 1):                # hanging single tiles and floating rock dust: fine as they are
            pass

    def _loot(self):
        rng = self.rng
        n = rng.randint(1, 3)
        out = []
        for _ in range(n):
            table = rng.choices(("common", "medical", "tools", "odd"), weights=(5, 3, 2 + self.index * 0.4, 1))[0]
            out.append(rng.choice(LOOT[table]))
        if rng.random() < 0.3 * self.preset["loot"]:
            out.append(rng.choice(LOOT["medical"]))
        return out

    def _stock(self, kind):
        base = {"dune": [("water", 2), ("bread", 3), ("gauze", 2), ("rope", 4), ("canteen", 3)],
                "mil": [("medkit", 8), ("battery", 3), ("splint", 4), ("syringe", 7), ("flashlight", 6), ("aed", 12)],
                "exp": [("pills", 4), ("vial", 5), ("acidfruit", 2), ("blanket", 5), ("medkit", 9), ("tweezers", 3)]}[kind]
        return [{"item": i, "price": p, "left": self.rng.randint(1, 3)} for i, p in base]

    # ---- queries -------------------------------------------------------------------------------------------------
    def tile(self, x, y):
        if x < 0 or x >= W:
            return 1
        if y < 0:
            return 0
        if y >= H:
            return 1
        return self.tiles[y][x]

    def solid(self, x, y):
        return self.tile(x, y) == 1

    def platform(self, x, y):
        return self.tile(x, y) == 5

    def thing_at(self, x, y, reach=1):
        best, bd = None, 99
        for t in self.things:
            if t["kind"] == "light":
                continue
            d = abs(t["x"] - x) + abs(t["y"] - y)
            if d <= reach and d < bd:
                best, bd = t, d
        return best
