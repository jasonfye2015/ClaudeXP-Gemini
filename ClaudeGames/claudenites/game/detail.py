"""The Deep's finer detail, laid over a floor after its dressing (game/dress.py): what makes it look lived in and
left - timber, stains, wet, litter, the light.

    the wood     corridor frames (two posts and a lintel, every few squares down a straight run), skirting boards
                 along the walls of some rooms, and beams across their ceilings - real boxes (L.boxes)
    the light    the corridors darker than the rooms (L.amb: the ambient by square, 0..1), a torch now and then
                 along a long corridor, and here and there a grate in the ceiling with light falling through it
                 (L.shafts: x, z, floor, ceiling) - daylight, or the moon's, from somewhere above
    the wet      puddles (L.wet: square -> 0..1), most under the pipes' drips and in the low places
    the stains   how stained each square's floor and walls are (L.stain: square -> 0..1), and water stains down the
                 walls (decal.stain)
    the litter   bones, old bottles (empty), vines down the walls and hanging from the roof

The shader draws the stains, the grime at the walls' feet and the puddles' sheen from L.amb, L.wet and L.stain
(engine/render.py, engine/groundmap.py's dungeon map)."""
import math

import numpy as np

from . import dress

# per band: how much wood (0..1), how wet, how stained, how green (vines), what lies about
BANDS = [
    {"wood": 0.9, "wet": 0.5, "stain": 0.7, "green": 0.25},     # the Root Cellars
    {"wood": 0.5, "wet": 0.7, "stain": 0.5, "green": 0.9},      # the Mossway
    {"wood": 0.4, "wet": 1.0, "stain": 0.8, "green": 0.4},      # the Sunken Halls
    {"wood": 0.3, "wet": 0.3, "stain": 0.7, "green": 0.15},     # the Barrows
    {"wood": 0.1, "wet": 0.2, "stain": 0.2, "green": 0.0},      # the Glass Caves
    {"wood": 0.8, "wet": 0.15, "stain": 1.0, "green": 0.0},     # the Old Foundry
    {"wood": 0.4, "wet": 0.5, "stain": 0.4, "green": 1.0},      # the Thornwild
    {"wood": 0.2, "wet": 0.0, "stain": 0.9, "green": 0.0},      # the Ember Deep
    {"wood": 0.5, "wet": 0.3, "stain": 0.6, "green": 0.2},      # the Bone Court
    {"wood": 0.3, "wet": 0.3, "stain": 0.6, "green": 0.1},      # the Hollow Throne
]
BOTTLES = ["item:s7_I_Bottle01.png", "item:s7_I_Bottle02.png", "item:s7_I_Bottle03.png", "item:s7_I_Bottle04.png"]
BONES = ["item:s7_E_Bones02.png", "item:s7_E_Bones03.png", "item:s7_I_Bone.png"]
WOOD = "ground.planks"
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _room_cells(L):
    cells = set()
    for r in getattr(L, "rooms", []):
        cells.update(r.cells())
    return cells


def detail(L, rng, band_index):
    B = BANDS[band_index]
    L.tex(WOOD)
    rooms = _room_cells(L)
    corridor = {c for c in L.paths if c not in rooms and L.open_at(*c)}
    taken = {(int(s["x"]), int(s["z"])) for s in L.sprites} | {(int(c["x"]), int(c["z"])) for c in L.chests}
    taken |= {(int(p["x"]), int(p["z"])) for p in L.props}
    _light(L, rng, rooms, corridor)
    _wood(L, rng, B, corridor)
    _wet_and_stains(L, rng, B, rooms)
    _litter(L, rng, B, taken, corridor)
    _shafts(L, rng, taken)


# ---- the light ---------------------------------------------------------------------------------------------------
def _light(L, rng, rooms, corridor):
    """The ambient by square: the rooms 1, the corridors a fifth of it (softened a square into the room's mouth);
    and on a long corridor a torch every dozen squares or so."""
    A = np.ones((L.h, L.w), np.float32)
    for x, y in corridor:
        A[y, x] = 0.2
    for x, y in corridor:                                  # (the corridor's last square before a room: between)
        if any((x + dx, y + dy) in rooms for dx, dy in DIRS):
            A[y, x] = 0.5
    L.amb = A
    theme = dress.CM_THEME_OF_BAND[min(9, (L.depth - 1) // 10)]
    run = 0
    for x, y in sorted(corridor, key=lambda c: (c[1], c[0])):
        run += 1
        if run < 12 or rng.random() > 0.25:
            continue
        for dx, dy in DIRS:
            if not L.open_at(x + dx, y + dy):
                f = float(L.floor[y, x])
                L.decals.append((x + 0.5 + dx * 0.495, f + 0.75, y + 0.5 + dy * 0.495, -dx, -dy, 0.5, 0.6,
                                 f"t{theme}.torch0"))
                L.lights.append((x + 0.5 + dx * 0.42, f + 1.15, y + 0.5 + dy * 0.42, 1.0, 0.62, 0.28, 5.5))
                run = 0
                break


# ---- the wood ----------------------------------------------------------------------------------------------------
def _wood(L, rng, B, corridor):
    if B["wood"] <= 0:
        return
    boxes = L.boxes
    # corridor frames: on a straight run (rock both sides), every fourth square or so
    since = {}
    for x, y in sorted(corridor):
        f, c = float(L.floor[y, x]), float(L.ceil[y, x])
        ew = not L.open_at(x, y - 1) and not L.open_at(x, y + 1) and L.open_at(x - 1, y) and L.open_at(x + 1, y)
        ns = not L.open_at(x - 1, y) and not L.open_at(x + 1, y) and L.open_at(x, y - 1) and L.open_at(x, y + 1)
        if not (ew or ns) or c - f > 3.2:
            continue
        key = ("ew", y) if ew else ("ns", x)
        last = since.get(key, -99)
        here = x if ew else y
        if here - last < 4 or rng.random() > B["wood"]:
            continue
        since[key] = here
        t, d = 0.11, 0.07                                   # (a post's width along the way, and how far it stands out)
        if ew:
            cx = x + 0.5
            boxes += [(cx - t / 2, f, y, cx + t / 2, c, y + d, WOOD), (cx - t / 2, f, y + 1 - d, cx + t / 2, c, y + 1, WOOD),
                      (cx - t / 2 - 0.02, c - 0.16, y, cx + t / 2 + 0.02, c, y + 1, WOOD)]
        else:
            cz = y + 0.5
            boxes += [(x, f, cz - t / 2, x + d, c, cz + t / 2, WOOD), (x + 1 - d, f, cz - t / 2, x + 1, c, cz + t / 2, WOOD),
                      (x, c - 0.16, cz - t / 2 - 0.02, x + 1, c, cz + t / 2 + 0.02, WOOD)]
    # the rooms: skirting boards, and beams across the ceiling
    for r in getattr(L, "rooms", []):
        if rng.random() > B["wood"] * 0.75:
            continue
        for x, y in r.cells():
            if not L.open_at(x, y):
                continue
            f = float(L.floor[y, x])
            for dx, dy in DIRS:
                if L.open_at(x + dx, y + dy):
                    continue
                h, d = 0.17, 0.035
                if dx == 1:
                    boxes.append((x + 1 - d, f, y, x + 1, f + h, y + 1, WOOD))
                elif dx == -1:
                    boxes.append((x, f, y, x + d, f + h, y + 1, WOOD))
                elif dy == 1:
                    boxes.append((x, f, y + 1 - d, x + 1, f + h, y + 1, WOOD))
                else:
                    boxes.append((x, f, y, x + 1, f + h, y + d, WOOD))
        if r.w >= 3 and r.h >= 3 and rng.random() < 0.7:
            along_x = r.w <= r.h                             # (the beams span the short way)
            n = r.h if along_x else r.w
            for k in range(1, n, 3):
                cells = [(xx, r.y + k) for xx in range(r.x, r.x + r.w)] if along_x else [(r.x + k, yy) for yy in range(r.y, r.y + r.h)]
                for x, y in cells:
                    if not L.open_at(x, y):
                        continue
                    c = float(L.ceil[y, x])
                    if c - float(L.floor[y, x]) > 3.4:
                        continue
                    if along_x:
                        boxes.append((x, c - 0.2, y + 0.42, x + 1, c, y + 0.58, WOOD))
                    else:
                        boxes.append((x + 0.42, c - 0.2, y, x + 0.58, c, y + 1, WOOD))


# ---- the wet and the stains ----------------------------------------------------------------------------------------
def _wet_and_stains(L, rng, B, rooms):
    wet, stain = {}, {}
    for (dx, _dt, dz, _df) in L.drips:                    # (under every drip, a puddle)
        x, y = int(dx), int(dz)
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                if L.open_at(x + ox, y + oy):
                    wet[(x + ox, y + oy)] = max(wet.get((x + ox, y + oy), 0), 1.0 if not (ox or oy) else 0.55)
    for x, y in L.open_squares():                          # (puddles in patches, more in the low squares)
        low = float(L.floor[y, x]) < -0.05
        if rng.random() < B["wet"] * (0.05 if not low else 0.3):
            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    if L.open_at(x + ox, y + oy) and rng.random() < 0.7:
                        wet[(x + ox, y + oy)] = max(wet.get((x + ox, y + oy), 0), rng.uniform(0.5, 1.0))
        stain[(x, y)] = min(1.0, B["stain"] * rng.uniform(0.3, 1.0) + (0.3 if (x, y) not in rooms else 0.0))
    for c in getattr(L, "water", ()):
        wet.pop(c, None)
    L.wet, L.stain = wet, stain
    # water stains down the walls
    for x, y in L.open_squares():
        f, c = float(L.floor[y, x]), float(L.ceil[y, x])
        for dx, dy in DIRS:
            if not L.open_at(x + dx, y + dy) and rng.random() < 0.045 * (0.4 + B["stain"]):
                h = min(c - f - 0.05, rng.uniform(1.1, 2.0))
                w = rng.uniform(0.35, 0.6)
                L.decals.append((x + 0.5 + dx * 0.4935 + (-dy) * rng.uniform(-0.25, 0.25), c - h - 0.02,
                                 y + 0.5 + dy * 0.4935 + dx * rng.uniform(-0.25, 0.25), -dx, -dy, w, h, "decal.stain"))


# ---- the litter --------------------------------------------------------------------------------------------------
def _litter(L, rng, B, taken, corridor):
    for x, y in L.open_squares():
        if (x, y) in taken or dress.clear_way(L, x, y) or (L.stairs and abs(x + 0.5 - L.stairs[0]) < 1.6
                                                          and abs(y + 0.5 - L.stairs[1]) < 1.6):
            continue
        f, c = float(L.floor[y, x]), float(L.ceil[y, x])
        walls = [(dx, dy) for dx, dy in DIRS if not L.open_at(x + dx, y + dy)]
        r = rng.random()
        if walls and r < 0.022:                           # bones against the wall
            w = walls[0]
            if rng.random() < 0.5:
                L.sprites.append({"x": x + 0.5 + w[0] * 0.25, "z": y + 0.5 + w[1] * 0.25, "y": f, "w": 0.55, "h": 0.33,
                                  "name": "bones", "glow": None, "solid": 0})
            else:
                L.sprites.append({"x": x + 0.5 + w[0] * 0.28 + rng.uniform(-0.2, 0.2), "z": y + 0.5 + w[1] * 0.28,
                                  "y": f, "w": 0.32, "h": 0.32, "name": rng.choice(BONES), "glow": None, "solid": 0})
            taken.add((x, y))
        elif r < 0.034:                                    # an old bottle, empty, or two
            for _ in range(rng.choice((1, 1, 2))):
                L.sprites.append({"x": x + rng.uniform(0.2, 0.8), "z": y + rng.uniform(0.2, 0.8), "y": f, "w": 0.2,
                                  "h": 0.2, "name": rng.choice(BOTTLES), "glow": None, "solid": 0})
            taken.add((x, y))
        # vines: down the walls, and hanging from the roof
        for dx, dy in walls:
            if rng.random() < 0.012 + 0.06 * B["green"]:
                h = min(c - f - 0.1, rng.uniform(0.9, 1.7))
                L.decals.append((x + 0.5 + dx * 0.4945, c - h - 0.02, y + 0.5 + dy * 0.4945, -dx, -dy,
                                 rng.uniform(0.6, 0.95), h, "mood.vines"))
        if rng.random() < 0.004 + 0.03 * B["green"] and c - f < 3.4:
            L.hangs.append((x + rng.uniform(0.3, 0.7), c, y + rng.uniform(0.3, 0.7), 0.6, rng.uniform(0.5, 0.9), "mood.vines"))


# ---- light from above --------------------------------------------------------------------------------------------
def _shafts(L, rng, taken):
    """One to three grates in the ceilings of the rooms, the light falling through each onto the floor."""
    L.shafts = []
    rooms = [r for r in getattr(L, "rooms", []) if r.w >= 3 and r.h >= 3]
    rng.shuffle(rooms)
    for r in rooms[:rng.randint(1, 3)]:
        for _ in range(12):
            x, y = rng.randint(r.x + 1, r.x + r.w - 2), rng.randint(r.y + 1, r.y + r.h - 2)
            if not L.open_at(x, y) or (L.stairs and abs(x + 0.5 - L.stairs[0]) < 2 and abs(y + 0.5 - L.stairs[1]) < 2):
                continue
            f, c = float(L.floor[y, x]), float(L.ceil[y, x])
            if c - f > 4.0:
                continue
            L.shafts.append((x + 0.5, y + 0.5, f, c))
            L.ceils.append((x + 0.5, c - 0.01, y + 0.5, 0.36, "dl.grate", rng.choice((0.0, math.pi / 2))))
            break
