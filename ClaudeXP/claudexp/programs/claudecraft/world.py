"""ClaudeCraft's world: blocks, terrain generation, chunk meshing and the block texture atlas.

The world is SIZE_X x HEIGHT x SIZE_Z blocks in one bytearray (index (y * SIZE_Z + z) * SIZE_X + x), generated from a
seed: value-noise hills, sand beaches, a sea, stone under the dirt, bedrock at the bottom, and trees. Changes you make
are kept as edits on top of the generated terrain (save()/load()). Chunks (16 x 16 columns) are meshed into float
arrays - x, y, z, u, v, shade per vertex - with only the faces that can be seen.
"""
import json
import math
import random
from array import array

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter

CHUNK = 16
CHUNKS = 10
SIZE_X = SIZE_Z = CHUNK * CHUNKS
HEIGHT = 64
SEA = 24

AIR, GRASS, DIRT, STONE, SAND, LOG, LEAVES, PLANKS, COBBLE, WATER, GLASS, BRICK, BEDROCK, SNOW, GRAVEL = range(15)
NAMES = {GRASS: "Grass", DIRT: "Dirt", STONE: "Stone", SAND: "Sand", LOG: "Wood", LEAVES: "Leaves",
         PLANKS: "Planks", COBBLE: "Cobblestone", WATER: "Water", GLASS: "Glass", BRICK: "Bricks",
         BEDROCK: "Bedrock", SNOW: "Snow", GRAVEL: "Gravel"}
HOTBAR = [GRASS, DIRT, STONE, COBBLE, PLANKS, LOG, GLASS, BRICK, SAND]
TRANSPARENT = {AIR, WATER, GLASS, LEAVES}      # you can see past these
SOLID = set(range(1, 15)) - {WATER}            # you can't walk through these
ATLAS_TILES = 4                                # the atlas is 4 x 4 tiles of 16 x 16 pixels
TILE = {"grass_top": 0, "grass_side": 1, "dirt": 2, "stone": 3, "sand": 4, "log_side": 5, "log_top": 6,
        "leaves": 7, "planks": 8, "cobble": 9, "water": 10, "glass": 11, "brick": 12, "bedrock": 13, "snow": 14,
        "gravel": 15}
# block -> (top, side, bottom) tiles
FACES = {GRASS: ("grass_top", "grass_side", "dirt"), DIRT: ("dirt",) * 3, STONE: ("stone",) * 3,
         SAND: ("sand",) * 3, LOG: ("log_top", "log_side", "log_top"), LEAVES: ("leaves",) * 3,
         PLANKS: ("planks",) * 3, COBBLE: ("cobble",) * 3, WATER: ("water",) * 3, GLASS: ("glass",) * 3,
         BRICK: ("brick",) * 3, BEDROCK: ("bedrock",) * 3, SNOW: ("snow", "snow", "dirt"), GRAVEL: ("gravel",) * 3}
# the six faces: (normal, shade, 6 corners as (dx, dy, dz, u, v)) - two triangles, counter-clockwise from outside
_FACE_DEFS = [
    ((0, 1, 0), 1.00, [(0, 1, 0, 0, 0), (0, 1, 1, 0, 1), (1, 1, 1, 1, 1), (0, 1, 0, 0, 0), (1, 1, 1, 1, 1), (1, 1, 0, 1, 0)]),
    ((0, -1, 0), 0.50, [(0, 0, 0, 0, 0), (1, 0, 0, 1, 0), (1, 0, 1, 1, 1), (0, 0, 0, 0, 0), (1, 0, 1, 1, 1), (0, 0, 1, 0, 1)]),
    ((1, 0, 0), 0.70, [(1, 0, 0, 1, 1), (1, 1, 0, 1, 0), (1, 1, 1, 0, 0), (1, 0, 0, 1, 1), (1, 1, 1, 0, 0), (1, 0, 1, 0, 1)]),
    ((-1, 0, 0), 0.70, [(0, 0, 0, 0, 1), (0, 0, 1, 1, 1), (0, 1, 1, 1, 0), (0, 0, 0, 0, 1), (0, 1, 1, 1, 0), (0, 1, 0, 0, 0)]),
    ((0, 0, 1), 0.85, [(0, 0, 1, 0, 1), (1, 0, 1, 1, 1), (1, 1, 1, 1, 0), (0, 0, 1, 0, 1), (1, 1, 1, 1, 0), (0, 1, 1, 0, 0)]),
    ((0, 0, -1), 0.85, [(0, 0, 0, 1, 1), (0, 1, 0, 1, 0), (1, 1, 0, 0, 0), (0, 0, 0, 1, 1), (1, 1, 0, 0, 0), (1, 0, 0, 0, 1)]),
]


# ---- noise ------------------------------------------------------------------------------------------------------------

def _hash(seed, x, z):
    n = (x * 374761393 + z * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def _smooth(t):
    return t * t * (3 - 2 * t)


def value_noise(seed, x, z, scale):
    fx, fz = x / scale, z / scale
    x0, z0 = math.floor(fx), math.floor(fz)
    tx, tz = _smooth(fx - x0), _smooth(fz - z0)
    a, b = _hash(seed, x0, z0), _hash(seed, x0 + 1, z0)
    c, d = _hash(seed, x0, z0 + 1), _hash(seed, x0 + 1, z0 + 1)
    return (a + (b - a) * tx) * (1 - tz) + (c + (d - c) * tx) * tz


# ---- the world ---------------------------------------------------------------------------------------------------------

class World:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randrange(1, 2 ** 31)
        self.blocks = bytearray(SIZE_X * SIZE_Z * HEIGHT)
        self.edits = {}                       # (x, y, z) -> block, on top of the generated terrain
        self.heights = [[0] * SIZE_Z for _ in range(SIZE_X)]

    def index(self, x, y, z):
        return (y * SIZE_Z + z) * SIZE_X + x

    def inside(self, x, y, z):
        return 0 <= x < SIZE_X and 0 <= y < HEIGHT and 0 <= z < SIZE_Z

    def get(self, x, y, z):
        if not (0 <= x < SIZE_X and 0 <= z < SIZE_Z) or y < 0:
            return BEDROCK if y < 0 else AIR
        if y >= HEIGHT:
            return AIR
        return self.blocks[(y * SIZE_Z + z) * SIZE_X + x]

    def set(self, x, y, z, block, record=True):
        if not self.inside(x, y, z):
            return False
        self.blocks[self.index(x, y, z)] = block
        if record:
            self.edits[(x, y, z)] = block
        return True

    # ---- generating ----
    def generate(self):
        s = self.seed
        rnd = random.Random(s)
        b = self.blocks
        for x in range(SIZE_X):
            for z in range(SIZE_Z):
                n = (value_noise(s, x, z, 48) * 0.6 + value_noise(s + 1, x, z, 20) * 0.3
                     + value_noise(s + 2, x, z, 8) * 0.1)
                mountain = value_noise(s + 3, x, z, 64)
                h = int(14 + n * 22 + max(0.0, mountain - 0.6) * 60)
                h = max(2, min(HEIGHT - 8, h))
                # a little island: the world slopes down into the sea near its edges
                edge = min(x, z, SIZE_X - 1 - x, SIZE_Z - 1 - z)
                if edge < 12:
                    h = min(h, SEA - 6 + edge // 2)
                self.heights[x][z] = h
                for y in range(h + 1):
                    if y == 0:
                        block = BEDROCK
                    elif y < h - 3:
                        block = STONE
                    elif h <= SEA + 1:
                        block = SAND if h >= SEA - 3 else GRAVEL
                    elif y == h:
                        block = SNOW if h > 44 else GRASS
                    else:
                        block = DIRT
                    b[(y * SIZE_Z + z) * SIZE_X + x] = block
                for y in range(h + 1, SEA + 1):
                    b[(y * SIZE_Z + z) * SIZE_X + x] = WATER
        for _ in range(SIZE_X * SIZE_Z // 70):          # trees
            x, z = rnd.randrange(3, SIZE_X - 3), rnd.randrange(3, SIZE_Z - 3)
            h = self.heights[x][z]
            if self.get(x, h, z) != GRASS:
                continue
            trunk = rnd.randint(4, 6)
            for y in range(h + 1, h + 1 + trunk):
                self.set(x, y, z, LOG, record=False)
            top = h + trunk
            for dy in range(-2, 2):
                r = 2 if dy < 0 else 1
                for dx in range(-r, r + 1):
                    for dz in range(-r, r + 1):
                        if abs(dx) == r and abs(dz) == r and (dy == 1 or rnd.random() < 0.5):
                            continue
                        if self.get(x + dx, top + dy, z + dz) == AIR:
                            self.set(x + dx, top + dy, z + dz, LEAVES, record=False)
            self.set(x, top + 1, z, LEAVES, record=False)
        for (x, y, z), block in self.edits.items():
            self.set(x, y, z, block, record=False)

    def spawn(self):
        x = z = SIZE_X // 2
        for r in range(0, SIZE_X // 2):
            for dx in range(-r, r + 1):
                for dz in (-r, r):
                    for cx, cz in ((x + dx, z + dz), (x + dz, z + dx)):
                        if 0 <= cx < SIZE_X and 0 <= cz < SIZE_Z:
                            h = self.top(cx, cz)
                            if h > SEA and self.get(cx, h, cz) not in (WATER, LEAVES):
                                return cx + 0.5, h + 1.01, cz + 0.5
        return x + 0.5, HEIGHT - 2, z + 0.5

    def top(self, x, z):
        for y in range(HEIGHT - 1, -1, -1):
            if self.get(x, y, z) != AIR:
                return y
        return 0

    # ---- saving ----
    def to_json(self):
        return {"seed": self.seed, "edits": [[x, y, z, b] for (x, y, z), b in self.edits.items()]}

    @classmethod
    def from_json(cls, data):
        w = cls(data.get("seed"))
        w.edits = {(x, y, z): b for x, y, z, b in data.get("edits", [])}
        return w

    # ---- meshing ----
    def mesh_chunk(self, cx, cz):
        """-> (opaque floats, water floats) for one chunk: x, y, z, u, v, shade per vertex."""
        b = self.blocks
        get = self.get
        opaque, water = array("f"), array("f")
        ts = 1.0 / ATLAS_TILES
        tiles = {}
        for block, (t, s, bt) in FACES.items():
            tiles[block] = [TILE[t], TILE[bt], TILE[s], TILE[s], TILE[s], TILE[s]]
        x0, z0 = cx * CHUNK, cz * CHUNK
        top = max(self.heights[x][z] for x in range(x0, x0 + CHUNK) for z in range(z0, z0 + CHUNK))
        top = min(HEIGHT - 1, max(top + 12, SEA + 1))
        for y in range(0, top + 1):
            row = y * SIZE_Z
            for z in range(z0, z0 + CHUNK):
                base = (row + z) * SIZE_X
                for x in range(x0, x0 + CHUNK):
                    block = b[base + x]
                    if block == AIR:
                        continue
                    tl = tiles[block]
                    out = water if block == WATER else opaque
                    for f, ((nx, ny, nz), shade, corners) in enumerate(_FACE_DEFS):
                        nb = get(x + nx, y + ny, z + nz)
                        if block == WATER:
                            if nb != AIR:
                                continue
                        elif nb not in TRANSPARENT or nb == block:
                            continue
                        tile = tl[f]
                        u0 = (tile % ATLAS_TILES) * ts
                        v0 = (tile // ATLAS_TILES) * ts
                        for dx, dy, dz, u, v in corners:
                            out.extend((x + dx, y + dy - (0.12 if block == WATER and dy else 0), z + dz,
                                        u0 + u * ts, v0 + v * ts, shade))
        return opaque, water

    def raycast(self, origin, direction, reach=6.0):
        """Amanatides & Woo: -> (hit block, the empty block before it) or (None, None)."""
        x, y, z = (math.floor(c) for c in origin)
        dx, dy, dz = direction
        step = [1 if d > 0 else -1 for d in direction]
        tmax, tdelta = [], []
        for c, d, cell in zip(origin, direction, (x, y, z)):
            if abs(d) < 1e-9:
                tmax.append(float("inf"))
                tdelta.append(float("inf"))
            else:
                boundary = cell + (1 if d > 0 else 0)
                tmax.append((boundary - c) / d)
                tdelta.append(abs(1 / d))
        prev = None
        t = 0.0
        while t <= reach:
            block = self.get(x, y, z)
            if block not in (AIR, WATER):
                return (x, y, z), prev
            prev = (x, y, z)
            i = tmax.index(min(tmax))
            t = tmax[i]
            tmax[i] += tdelta[i]
            if i == 0:
                x += step[0]
            elif i == 1:
                y += step[1]
            else:
                z += step[2]
        return None, None


# ---- textures --------------------------------------------------------------------------------------------------------

def _tile_image(name, rnd):
    img = QImage(16, 16, QImage.Format_ARGB32)

    def noisy(base, spread, alpha=255):
        c = QColor(base)
        for y in range(16):
            for x in range(16):
                k = rnd.uniform(-spread, spread)
                img.setPixelColor(x, y, QColor(max(0, min(255, int(c.red() + k))), max(0, min(255, int(c.green() + k))),
                                               max(0, min(255, int(c.blue() + k))), alpha))
    if name == "grass_top":
        noisy("#5FA33A", 22)
    elif name == "dirt":
        noisy("#866043", 20)
    elif name == "grass_side":
        noisy("#866043", 20)
        for x in range(16):
            for y in range(3 + rnd.randint(0, 2)):
                img.setPixelColor(x, y, QColor("#5FA33A").darker(100 + rnd.randint(0, 20)))
    elif name == "stone":
        noisy("#7F7F7F", 18)
    elif name == "sand":
        noisy("#DBCF95", 12)
    elif name == "gravel":
        noisy("#8A8580", 30)
    elif name == "snow":
        noisy("#F2F6FA", 6)
    elif name == "log_side":
        noisy("#6B5233", 12)
        for x in (2, 6, 10, 13):
            for y in range(16):
                img.setPixelColor(x, y, QColor("#4E3B24"))
    elif name == "log_top":
        noisy("#A68A5A", 10)
        p = QPainter(img)
        p.setPen(QColor("#6B5233"))
        p.drawRect(0, 0, 15, 15)
        p.drawRect(3, 3, 9, 9)
        p.end()
    elif name == "leaves":
        img.fill(Qt.transparent)
        for y in range(16):
            for x in range(16):
                if rnd.random() < 0.78:
                    img.setPixelColor(x, y, QColor("#3E7A26").darker(90 + rnd.randint(0, 40)))
    elif name == "planks":
        noisy("#B08D57", 10)
        for y in (3, 7, 11, 15):
            for x in range(16):
                img.setPixelColor(x, y, QColor("#7E6238"))
    elif name == "cobble":
        noisy("#7A7A7A", 26)
        p = QPainter(img)
        p.setPen(QColor("#4F4F4F"))
        for r in (QRect(0, 0, 7, 5), QRect(8, 0, 7, 6), QRect(0, 6, 5, 5), QRect(6, 7, 9, 4), QRect(0, 12, 9, 3),
                  QRect(10, 12, 5, 3)):
            p.drawRect(r)
        p.end()
    elif name == "water":
        noisy("#3459C9", 10, alpha=170)
    elif name == "glass":
        img.fill(QColor(200, 230, 255, 40))
        p = QPainter(img)
        p.setPen(QColor(230, 245, 255, 230))
        p.drawRect(0, 0, 15, 15)
        p.drawLine(4, 4, 7, 1)
        p.end()
    elif name == "brick":
        noisy("#9B4A3A", 10)
        p = QPainter(img)
        p.setPen(QColor("#C9BFB0"))
        for y in (3, 7, 11, 15):
            p.drawLine(0, y, 15, y)
        for row, y in enumerate((0, 4, 8, 12)):
            for x in ((3, 11) if row % 2 else (7, 15)):
                p.drawLine(x, y, x, y + 2)
        p.end()
    elif name == "bedrock":
        noisy("#3A3A3A", 40)
    return img


def atlas():
    rnd = random.Random(7)
    img = QImage(16 * ATLAS_TILES, 16 * ATLAS_TILES, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    for name, i in TILE.items():
        p.drawImage((i % ATLAS_TILES) * 16, (i // ATLAS_TILES) * 16, _tile_image(name, rnd))
    p.end()
    return img


def tile_image(block, atlas_img):
    """The top-face tile of a block (for the hotbar)."""
    t = TILE[FACES[block][0] if block not in (GRASS, LOG) else FACES[block][1]]
    return atlas_img.copy((t % ATLAS_TILES) * 16, (t // ATLAS_TILES) * 16, 16, 16)


def save_json(path, world, player):
    data = world.to_json()
    data["player"] = player
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(path)
