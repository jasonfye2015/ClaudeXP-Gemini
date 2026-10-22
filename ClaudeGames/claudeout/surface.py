"""The surface: the hill the vault comes up on, the path down, and Serenity Hills - the old cul-de-sac, two hundred
and ten years after the bombs. Dead grass, a cracked ring road, eight clapboard houses with their roofs half gone,
rusted cars, bare trees, a river with a wooden bridge out of town. Your old house, the robot who kept it, and the
pests in the neighbourhood are Part Two.

The ground is a grid of 1 m cells with a height at every corner (the hill, the river's banks, the hills round the
edge); the houses and props are boxes stood on it; trees are crossed quads. (What changes lives in world.py.)"""
import math
import random
from array import array

from . import art
from .mesh import box, box_grid, cross, quad, quad_uv

SW, SH = 120, 110
HILL = (20.0, 14.0)
PLATFORM_R = 4.2
PATH = [(23.0, 18.5), (26.5, 24.0), (31.0, 30.0), (36.0, 36.5), (41.0, 42.0), (45.5, 45.5)]
RING = (44, 44, 92, 84)         # the ring road: x0, z0, x1, z1 (exclusive), a 4-cell band round the edge
BAND = 4
RIVER = (100, 108)              # x range of the water
BRIDGE = (99, 48, 108, 52)      # cells x 99..107, z 48..51
BRIDGE_END_X = 104.0            # past here you've left town
WATER_Y = -0.8
START = (20.5, 14.5)
START_YAW = 225.0               # facing south-east, down the path
ROBOT = (54.5, 42.8)
ROBOT_NAME = "Rustworth"
TOWN = "Serenity Hills"
TEX = {"g": "grass", "d": "dirt", "r": "road", "p": "pavement", "c": "concrete", "k": "rock", "f": "house_floor",
       "e": "gear", "b": "water", "w": "water"}

HOUSES = [
    dict(x0=50, z0=33, x1=59, z1=41, colour="house_blue", front="s", home=True),
    dict(x0=64, z0=33, x1=73, z1=41, colour="house_yellow", front="s"),
    dict(x0=78, z0=33, x1=87, z1=41, colour="house_white", front="s"),
    dict(x0=33, z0=52, x1=41, z1=60, colour="house_yellow", front="e"),
    dict(x0=33, z0=66, x1=41, z1=74, colour="house_white", front="e"),
    dict(x0=72, z0=54, x1=81, z1=62, colour="house_white", front="n"),
    dict(x0=56, z0=68, x1=65, z1=76, colour="house_yellow", front="s"),
    dict(x0=64, z0=87, x1=73, z1=95, colour="house_blue", front="n"),
]
# items: id -> (kind, x, z)
ITEMS = {
    "radaway": ("radaway", 57.0, 36.5), "stim_home": ("stimpak", 52.0, 36.8),
    "cola1": ("cola", 66.5, 36.5), "ammo_h3": ("ammo", 80.5, 36.5),
    "cola2": ("cola", 35.5, 54.5), "stim_h4": ("stimpak", 38.5, 58.5),
    "cola3": ("cola", 35.5, 68.5), "ammo_h6": ("ammo", 74.5, 57.0),
    "cola4": ("cola", 58.5, 70.5), "stim_h8": ("stimpak", 66.5, 89.5), "cola5": ("cola", 70.5, 92.5),
    "ammo_path": ("ammo", 34.0, 34.5),
}
# nests: (name, region, [(kind, x, z)]) - they come out when you're in the region
NESTS = [
    ("slope", (24, 22, 38, 38), [("bloatfly", 29.0, 26.5), ("bloatfly", 33.5, 32.0)]),
    ("gate", (38, 38, 50, 50), [("molerat", 42.5, 41.0), ("molerat", 47.5, 42.5)]),
    ("yard", (49, 32, 60, 42), [("roach", 55.5, 36.5)]),
]
# the pests Rustworth wants seen to (they come out when he asks)
PESTS = [("roach", 82.5, 43.0), ("roach", 37.0, 63.0), ("roach", 60.5, 66.5), ("bloatfly", 68.5, 43.0),
         ("bloatfly", 76.5, 52.5), ("bloatfly", 68.5, 85.5), ("bloatfly", 90.0, 62.0), ("molerat", 46.0, 46.0),
         ("molerat", 86.0, 82.0)]
TARGETS = {"descend": (45.5, 45.5), "home": (54.5, 43.0), "robot": ROBOT, "report": ROBOT,
           "bridge": (104.0, 50.0)}
# what Rustworth says: node -> (text, [(choice, next node)]); "end:..." ends the talk with an effect
DIALOGUE = {
    "start": ("As I live and breathe... it's you! It's really you! Oh, I'd nearly given up hope. How long has it "
              "been - two hundred and ten years, if the chronometer's right, and it always is.",
              [("Where is everyone?", "everyone"), ("What happened here?", "what"), ("You waited all this time?", "waited")]),
    "everyone": ("The neighbours went down into the vault with you, and... well. The ones who came back up were in "
                 "no state to talk. The house has been very quiet, I'm afraid.",
                 [("What happened here?", "what"), ("You waited all this time?", "waited"), ("What now?", "ask")]),
    "what": ("The bombs, of course. The bright flash, the wind, and then two centuries of rain that hisses when it "
             "lands. I've kept the lawn as best I could.",
             [("Where is everyone?", "everyone"), ("What now?", "ask")]),
    "waited": ("Someone had to keep the place up. I'm afraid the lawn has rather got away from me. And the roof. "
               "And most of the walls.",
               [("What now?", "ask")]),
    "ask": ("Chin up. The houses are crawling with pests - radroaches, bloatflies, those dreadful mole rats. If "
            "you'd see them off, I could make a proper start on the garden.",
            [("I'll handle the pests.", "end:clear")]),
    "progress": ("Still some scuttling about, I'm afraid. Do mind the mole rats - they come up from underneath.",
                 [("On it.", "end")]),
    "cleared": ("Splendid work! Quite like old times. Now - there were people over in Concord, across the bridge, "
                "not two weeks ago. Someone there may know more than I do. Do be careful.",
                [("Thanks, Rustworth.", "end:bridge")]),
    "after": ("Concord is across the bridge, past the old filling station. I'll keep the home fires burning. "
              "Figuratively, of course.",
              [("Goodbye.", "end")]),
}


# ---- the ground ----------------------------------------------------------------------------------------------------
def _hash(x, z, seed=9):
    n = (x * 374761393 + z * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def _smooth(t):
    return t * t * (3 - 2 * t)


def _noise(x, z, scale):
    x, z = x / scale, z / scale
    ix, iz = int(math.floor(x)), int(math.floor(z))
    fx, fz = _smooth(x - ix), _smooth(z - iz)
    a, b, c, d = _hash(ix, iz), _hash(ix + 1, iz), _hash(ix, iz + 1), _hash(ix + 1, iz + 1)
    return (a + (b - a) * fx) * (1 - fz) + (c + (d - c) * fx) * fz - 0.5


def _dist_to_path(x, z):
    best = 1e9
    for (ax, az), (bx, bz) in zip(PATH, PATH[1:]):
        dx, dz = bx - ax, bz - az
        t = max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz)))
        best = min(best, math.hypot(x - (ax + dx * t), z - (az + dz * t)))
    return best


def _raw_height(x, z):
    d = math.hypot(x - HILL[0], z - HILL[1])
    h = 7.0 * _smooth(1 - max(0.0, min(1.0, (d - 5.0) / 19.0)))      # flat on top, down to the ground by 24 m
    r0, r1 = RIVER
    if r0 - 3 <= x <= r1 + 3:                                          # the river's trough, banks sloping in
        gap = 0.0 if r0 <= x <= r1 else (r0 - x if x < r0 else x - r1)
        h -= 1.6 * _smooth(max(0.0, 1 - gap / 3.0))
    e = min(x, z, SW - x, SH - z)
    if e < 9:                                                          # hills all round the edge
        h += 8.0 * ((9 - e) / 9) ** 2 + 1.5 * _noise(x, z, 5) * ((9 - e) / 9)
    inside = 28 <= x <= 100 and 28 <= z <= 100
    h += _noise(x, z, 7) * (0.3 if inside else 0.9)
    return h


def _build():
    rng = random.Random(2077)
    types = [["g"] * SW for _ in range(SH)]
    # the river and the bridge
    for z in range(SH):
        for x in range(RIVER[0], RIVER[1]):
            types[z][x] = "w"
    bx0, bz0, bx1, bz1 = BRIDGE
    for z in range(bz0, bz1):
        for x in range(bx0, bx1):
            types[z][x] = "b"
    # the ring road and the way to the bridge
    x0, z0, x1, z1 = RING
    for z in range(z0, z1):
        for x in range(x0, x1):
            if x < x0 + BAND or x >= x1 - BAND or z < z0 + BAND or z >= z1 - BAND:
                types[z][x] = "r"
    for z in range(bz0, bz1):
        for x in range(x1 - BAND, RIVER[0]):
            types[z][x] = "r"
    # the path down the hill
    path_cells = set()
    for z in range(SH):
        for x in range(SW):
            if _dist_to_path(x + 0.5, z + 0.5) < 1.6:
                path_cells.add((x, z))
                if types[z][x] == "g":
                    types[z][x] = "d"
    # the hill top: the platform, a concrete apron, and boulders all round but for the path
    boulders = []
    for z in range(SH):
        for x in range(SW):
            d = math.hypot(x + 0.5 - HILL[0], z + 0.5 - HILL[1])
            if d <= PLATFORM_R:
                types[z][x] = "e"
            elif d <= 5.6:
                types[z][x] = "c"
            elif d <= 8.6 and (x, z) not in path_cells:
                types[z][x] = "k"
                if rng.random() < 0.45:
                    s = rng.uniform(0.7, 1.4)
                    boulders.append((x + 0.5 - s / 2, z + 0.5 - s / 2, x + 0.5 + s / 2, z + 0.5 + s / 2,
                                     rng.uniform(0.8, 1.9), "rock", "rock"))
    # the hills round the edge
    for z in range(SH):
        for x in range(SW):
            if x < 5 or z < 5 or x >= SW - 5 or z >= SH - 5:
                types[z][x] = "k"
    # the houses' floors
    for h in HOUSES:
        for z in range(h["z0"], h["z1"]):
            for x in range(h["x0"], h["x1"]):
                types[z][x] = "f"
    # heights at the corners
    heights = [[_raw_height(x, z) for x in range(SW + 1)] for z in range(SH + 1)]
    for z in range(SH + 1):                              # the platform and its apron are dead level
        for x in range(SW + 1):
            if math.hypot(x - HILL[0], z - HILL[1]) <= 6.2:
                heights[z][x] = 7.0
    for h in HOUSES:                                     # a house stands on level ground
        base = heights[(h["z0"] + h["z1"]) // 2][(h["x0"] + h["x1"]) // 2]
        for z in range(h["z0"] - 1, h["z1"] + 2):
            for x in range(h["x0"] - 1, h["x1"] + 2):
                heights[z][x] = base
    for z in range(SH + 1):                              # so does the road
        for x in range(SW + 1):
            near = [types[zz][xx] for zz in (z - 1, z) for xx in (x - 1, x) if 0 <= zz < SH and 0 <= xx < SW]
            if near and all(t in "rb" for t in near):
                heights[z][x] = 0.0 if (any(t == "b" for t in near) or x >= 94) else round(heights[z][x] * 4) / 4
    return types, heights, boulders, path_cells


TYPES, HEIGHTS, BOULDERS, PATH_CELLS = _build()


def cell(x, z):
    if 0 <= x < SW and 0 <= z < SH:
        return TYPES[z][x]
    return "k"


def solid_cell(x, z):
    return cell(int(math.floor(x)), int(math.floor(z))) in "kw"


def terrain(x, z):
    """The ground's height at a point (between the corner heights)."""
    i, j = int(math.floor(x)), int(math.floor(z))
    i = max(0, min(SW - 1, i))
    j = max(0, min(SH - 1, j))
    fx, fz = x - i, z - j
    h00, h10, h01, h11 = HEIGHTS[j][i], HEIGHTS[j][i + 1], HEIGHTS[j + 1][i], HEIGHTS[j + 1][i + 1]
    return (h00 + (h10 - h00) * fx) * (1 - fz) + (h01 + (h11 - h01) * fx) * fz


def walk_height(x, z):
    """Where your feet are: the bridge's deck over the river, the ground elsewhere."""
    if cell(int(math.floor(x)), int(math.floor(z))) == "b":
        return 0.0
    return terrain(x, z)


# ---- the props -----------------------------------------------------------------------------------------------------
def _house_boxes(h, idx, rng):
    """Walls (with a doorway in the front and some fallen), a bit of roof, the furniture."""
    x0, z0, x1, z1 = h["x0"], h["z0"], h["x1"], h["z1"]
    tex = h["colour"]
    t = 0.3
    out = []
    sides = {"n": ((x0, z0, x1, z0 + t), "x"), "s": ((x0, z1 - t, x1, z1), "x"),
             "w": ((x0, z0, x0 + t, z1), "z"), "e": ((x1 - t, z0, x1, z1), "z")}
    for side, ((sx0, sz0, sx1, sz1), along) in sides.items():
        length = (sx1 - sx0) if along == "x" else (sz1 - sz0)
        n = int(round(length / 1.5))
        seg = length / n
        for k in range(n):
            if side == h["front"] and k == n // 2:       # the doorway
                continue
            a = (sx0 if along == "x" else sz0) + k * seg
            b = a + seg
            if along == "x":
                bx0, bz0, bx1, bz1 = a, sz0, b, sz1
            else:
                bx0, bz0, bx1, bz1 = sx0, a, sx1, b
            r = rng.random()
            height = 1.1 if r < 0.22 else 2.7
            wall_tex = "house_window" if (height > 2 and 0.22 <= r < 0.45) else tex
            out.append((bx0, bz0, bx1, bz1, height, "roof" if height > 2 else "rubble", wall_tex))
    # what's left of the roof: a slab over the back half
    if h["front"] == "s":
        out.append((x0, z0, x1, (z0 + z1) / 2, 0.25, "roof", "roof", 2.7))
    elif h["front"] == "n":
        out.append((x0, (z0 + z1) / 2, x1, z1, 0.25, "roof", "roof", 2.7))
    else:
        out.append((x0, z0, (x0 + x1) / 2, z1, 0.25, "roof", "roof", 2.7))
    # the furniture, along the back wall
    back = {"s": "n", "n": "s", "e": "w", "w": "e"}[h["front"]]
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    pieces = [("couch", 2.2, 0.9, 0.8), ("fridge", 0.9, 0.9, 1.8), ("tv", 1.2, 0.8, 1.0), ("bed", 2.0, 1.0, 0.6),
              ("table", 1.6, 1.0, 0.8)]
    chosen = [pieces[(idx + k) % len(pieces)] for k in range(3)]
    if h.get("home"):
        chosen = [("crib", 1.2, 0.8, 0.9), ("couch", 2.2, 0.9, 0.8), ("fridge", 0.9, 0.9, 1.8), ("tv", 1.2, 0.8, 1.0)]
    for k, (name, w, d, hh) in enumerate(chosen):
        off = -2.6 + k * 2.4
        if back in ("n", "s"):
            px, pz = cx + off, (z0 + t + 0.2 + d / 2) if back == "n" else (z1 - t - 0.2 - d / 2)
            out.append((px - w / 2, pz - d / 2, px + w / 2, pz + d / 2, hh, name, name))
        else:
            px, pz = (x0 + t + 0.2 + d / 2) if back == "w" else (x1 - t - 0.2 - d / 2), cz + off
            out.append((px - d / 2, pz - w / 2, px + d / 2, pz + w / 2, hh, name, name))
    # out front: a mailbox, a picket fence with a gap, some rubble
    if h["front"] == "s":
        fx, fz = cx + 2.5, z1 + 1.2
        out.append((fx - 0.2, fz - 0.15, fx + 0.2, fz + 0.15, 1.1, "mailbox", "mailbox"))
        fz = z1 + 2.6
        out.append((x0, fz, cx - 1.2, fz + 0.12, 1.0, "fence", "fence"))
        out.append((cx + 1.2, fz, x1, fz + 0.12, 1.0, "fence", "fence"))
    elif h["front"] == "n":
        fx, fz = cx + 2.5, z0 - 1.2
        out.append((fx - 0.2, fz - 0.15, fx + 0.2, fz + 0.15, 1.1, "mailbox", "mailbox"))
        fz = z0 - 2.6
        out.append((x0, fz - 0.12, cx - 1.2, fz, 1.0, "fence", "fence"))
        out.append((cx + 1.2, fz - 0.12, x1, fz, 1.0, "fence", "fence"))
    else:
        fx, fz = x1 + 1.2, cz + 2.5
        out.append((fx - 0.15, fz - 0.2, fx + 0.15, fz + 0.2, 1.1, "mailbox", "mailbox"))
        fx = x1 + 2.6
        out.append((fx, z0, fx + 0.12, cz - 1.2, 1.0, "fence", "fence"))
        out.append((fx, cz + 1.2, fx + 0.12, z1, 1.0, "fence", "fence"))
    out.append((x0 - 1.6, z1 - 1.5, x0 - 0.2, z1 + 0.2, 0.5, "rubble", "rubble"))
    out.append((x1 + 0.2, z0 + 0.5, x1 + 1.8, z0 + 2.0, 0.6, "rubble", "rubble"))
    return out


def _props():
    rng = random.Random(1111)
    boxes = list(BOULDERS)
    for idx, h in enumerate(HOUSES):
        boxes += _house_boxes(h, idx, rng)
    # the workbench by your house
    boxes.append((60.0, 37.5, 62.0, 38.6, 1.0, "workbench", "workbench"))
    # cars, rusting where they were left
    for cx, cz, along in ((61.5, 44.9, "x"), (75.0, 45.0, "x"), (44.6, 62.0, "z"), (84.0, 66.0, "z"), (58.0, 51.5, "x"),
                          (95.0, 46.0, "x"), (61.5, 85.6, "x")):
        if along == "x":
            boxes.append((cx - 2.1, cz - 0.95, cx + 2.1, cz + 0.95, 1.0, "car_top", "car"))
            boxes.append((cx - 1.1, cz - 0.8, cx + 1.1, cz + 0.8, 0.55, "car_top", "car", 1.0))
        else:
            boxes.append((cx - 0.95, cz - 2.1, cx + 0.95, cz + 2.1, 1.0, "car_top", "car"))
            boxes.append((cx - 0.8, cz - 1.1, cx + 0.8, cz + 1.1, 0.55, "car_top", "car", 1.0))
    # lamp posts round the ring
    for lx, lz in ((48.5, 48.5), (87.5, 48.5), (48.5, 79.5), (87.5, 79.5), (68.0, 48.5), (68.0, 79.5), (48.5, 64.0),
                   (87.5, 64.0)):
        boxes.append((lx - 0.12, lz - 0.12, lx + 0.12, lz + 0.12, 4.6, "metal", "metal"))
    # signs: the town's, and Vault-Tec's up on the hill
    boxes.append((41.0, 46.8, 43.4, 47.0, 2.2, "metal", "sign_welcome"))
    boxes.append((24.5, 17.2, 26.9, 17.4, 2.2, "metal", "sign_vault"))
    # a railing round the back of the platform
    for k in range(-4, 5):
        boxes.append((HILL[0] + k - 0.5, HILL[1] - 4.6, HILL[0] + k + 0.5, HILL[1] - 4.45, 1.1, "railing", "railing"))
        boxes.append((HILL[0] - 4.6, HILL[1] + k - 0.5, HILL[0] - 4.45, HILL[1] + k + 0.5, 1.1, "railing", "railing"))
    # the bridge's rails
    bx0, bz0, bx1, bz1 = BRIDGE
    boxes.append((bx0, bz0 - 0.15, bx1, bz0, 1.0, "railing", "railing"))
    boxes.append((bx0, bz1, bx1, bz1 + 0.15, 1.0, "railing", "railing"))
    return boxes


BOXES = _props()
BOX_GRID = box_grid([b for b in BOXES if (len(b) < 8 or b[7] < 1.0)])     # (car roofs are above your head)
DECOR = [(BRIDGE[0] - 0.5, BRIDGE[1] - 0.15, BRIDGE[2] + 0.5, BRIDGE[3] + 0.15, 0.35, "bridge", "bridge", -0.35)]


def _trees():
    rng = random.Random(31)
    trees, bushes = [], []
    yards = [(h["x0"] - 4, h["z0"] - 4, h["x1"] + 4, h["z1"] + 4) for h in HOUSES]

    def clear(x, z, margin):
        for dz in range(-margin, margin + 1):
            for dx in range(-margin, margin + 1):
                if cell(x + dx, z + dz) != "g":
                    return False
        if math.hypot(x - HILL[0], z - HILL[1]) < 11:
            return False
        if any(x0 <= x < x1 and z0 <= z < z1 for x0, z0, x1, z1 in yards):
            return False
        return True
    tries = 0
    while len(trees) < 90 and tries < 6000:
        tries += 1
        x, z = rng.randrange(5, SW - 5), rng.randrange(5, SH - 5)
        if not clear(x, z, 2):
            continue
        if any(math.hypot(x - tx, z - tz) < 3.5 for tx, tz, _s in trees):
            continue
        trees.append((x + rng.uniform(0.2, 0.8), z + rng.uniform(0.2, 0.8), rng.uniform(0.8, 1.35)))
    tries = 0
    while len(bushes) < 45 and tries < 4000:
        tries += 1
        x, z = rng.randrange(5, SW - 5), rng.randrange(5, SH - 5)
        if clear(x, z, 1) and not any(math.hypot(x - tx, z - tz) < 1.5 for tx, tz, _s in trees):
            bushes.append((x + rng.uniform(0.2, 0.8), z + rng.uniform(0.2, 0.8), rng.uniform(0.6, 1.1)))
    return trees, bushes


TREES, BUSHES = _trees()
TREE_GRID = box_grid([(x - 0.25, z - 0.25, x + 0.25, z + 0.25) for x, z, _s in TREES])


# ---- the mesh ------------------------------------------------------------------------------------------------------
def static_mesh():
    buf = array("f")
    px0, pz0 = HILL[0] - 4.5, HILL[1] - 4.5
    for z in range(SH):
        for x in range(SW):
            t = TYPES[z][x]
            if t in "wb":
                quad(buf, (x, WATER_Y, z + 1), (x + 1, WATER_Y, z + 1), (x + 1, WATER_Y, z), (x, WATER_Y, z), "water", 0.85)
                continue
            h00, h10, h01, h11 = HEIGHTS[z][x], HEIGHTS[z][x + 1], HEIGHTS[z + 1][x], HEIGHTS[z + 1][x + 1]
            slope = max(abs(h00 - h11), abs(h10 - h01))
            shade = max(0.5, 0.92 - min(0.4, slope * 0.1))
            pts = ((x, h01, z + 1), (x + 1, h11, z + 1), (x + 1, h10, z), (x, h00, z))
            if t == "e":                                 # the platform is one big gear, spread over its cells
                u0, v0, u1, v1 = art.uv("gear")
                uvs = []
                for (xx, _y, zz) in pts:
                    uvs.append((u0 + (u1 - u0) * (xx - px0) / 9.0, v0 + (v1 - v0) * (zz - pz0) / 9.0))
                quad_uv(buf, pts, uvs, shade)
            else:
                quad(buf, *pts, TEX[t], shade)
    for b in BOXES + DECOR:
        x0, z0, x1, z1, h, top, side = b[:7]
        yoff = b[7] if len(b) > 7 else 0.0
        base = terrain((x0 + x1) / 2, (z0 + z1) / 2) - 0.08 + yoff
        if top == "bridge":
            base = yoff
        box(buf, x0, base, z0, x1, base + h, z1, top, side)
    for x, z, s in TREES:
        cross(buf, x, terrain(x, z) - 0.1, z, 3.2 * s, 5.6 * s, "tree", 0.85)
    for x, z, s in BUSHES:
        cross(buf, x, terrain(x, z) - 0.05, z, 1.4 * s, 1.1 * s, "bush", 0.9)
    return buf
