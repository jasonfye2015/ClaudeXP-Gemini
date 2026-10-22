"""Vault 111: the rooms, the doors, the furniture, where the radroaches live and what's lying about.

The vault is a grid of 1 m cells, 3 m high. Rooms are carved from solid rock, doors are cells of their own that
slide up, and the furniture is boxes with textures from art.py. Part One runs from the cryo pod to the elevator;
the terminals and the Pip-Boy gate the doors. (What changes - doors, items taken, roaches - lives in world.py.)"""
import random
from array import array

from .mesh import box, box_grid, quad

W, H = 72, 36
WALL_H = 3.0
ROOMS = {                      # name: (x0, z0, x1, z1) of floor cells, inclusive
    "cryo": (2, 2, 14, 12),
    "corr1": (16, 6, 32, 8),
    "medical": (22, 1, 30, 4),
    "cafeteria": (34, 2, 46, 14),
    "corr2": (39, 16, 40, 24),
    "security": (34, 26, 46, 33),
    "overseer": (48, 26, 58, 33),
    "corr3": (53, 14, 54, 24),
    "exit": (48, 2, 62, 12),
    "antechamber": (65, 4, 70, 10),
}
# doors: id -> (cells, kind)   kind: "auto" opens when you're near; "locked" needs an event; "gear" is the vault door
DOORS = {
    "cryo_exit": ([(15, 6), (15, 7), (15, 8)], "auto"),
    "medical": ([(26, 5)], "auto"),
    "cafeteria": ([(33, 6), (33, 7), (33, 8)], "auto"),
    "corr2": ([(39, 15), (40, 15)], "auto"),
    "security": ([(39, 25), (40, 25)], "auto"),
    "overseer": ([(47, 29), (47, 30)], "locked"),
    "exit_path": ([(53, 25), (54, 25)], "locked"),
    "exit_room": ([(53, 13), (54, 13)], "auto"),
    "gear": ([(63, z) for z in range(5, 10)] + [(64, z) for z in range(5, 10)], "gear"),
}
ELEVATOR = (66, 5, 69, 9)
START = (5.5, 10.6, 0.0)       # x, z, yaw (0 = looking down -z: across the room at the other pod)
SPOUSE_POD = (5, 2)            # the pod across from yours

# boxes: (x0, z0, x1, z1, height, top texture, side texture)  - in cell units; x1/z1 exclusive
BOXES = []
for _x in (3, 5, 7, 9, 11, 13):
    for _z in (2, 12):
        BOXES.append((_x + 0.1, _z + 0.1, _x + 0.9, _z + 0.95, 2.5, "pod_side", "pod"))
BOXES += [
    (22.1, 1.1, 24.0, 2.1, 0.6, "bed", "metal"), (28.0, 1.1, 29.9, 2.1, 0.6, "bed", "metal"),
    (25.2, 1.1, 27.8, 1.9, 1.0, "desk_top", "desk_side"),
    (36.0, 4.0, 38.0, 5.2, 0.9, "table", "metal"), (41.0, 4.0, 43.0, 5.2, 0.9, "table", "metal"),
    (38.5, 9.0, 40.5, 10.2, 0.9, "table", "metal"), (43.0, 9.5, 45.0, 10.7, 0.9, "table", "metal"),
    (34.0, 12.0, 38.0, 13.2, 1.1, "counter", "counter"), (44.0, 2.0, 46.9, 3.0, 2.2, "locker", "locker"),
    (35.0, 27.0, 37.6, 28.2, 1.0, "desk_top", "desk_side"), (43.0, 27.0, 46.9, 28.2, 1.0, "desk_top", "desk_side"),
    (34.1, 31.0, 36.1, 32.0, 2.2, "locker", "locker"), (44.0, 32.0, 46.9, 33.0, 1.0, "crate", "crate"),
    (51.0, 28.8, 55.0, 30.4, 1.0, "desk_top", "desk_side"), (56.5, 26.1, 58.9, 27.1, 2.2, "locker", "locker"),
    (48.1, 32.0, 50.2, 33.0, 1.0, "crate", "crate"),
    (49.0, 2.1, 51.0, 3.1, 1.0, "crate", "crate"), (58.0, 2.1, 61.0, 3.2, 1.1, "counter", "counter"),
    (62.4, 10.3, 63.0, 11.7, 1.5, "metal", "panel"),       # the door control, on the east wall beside the door
    (70.4, 6.0, 71.0, 8.0, 1.5, "metal", "panel"),         # the elevator control
]
BOX_GRID = box_grid(BOXES)
SCREENS = [(26.2, 1.1, 26.8, 1.6, 1.0, 1.6), (45.0, 27.0, 45.6, 27.5, 1.0, 1.6), (52.6, 28.8, 53.2, 29.3, 1.0, 1.6)]
# terminals: id -> (x, z, title, lines)
TERMINALS = {
    "security": (45.3, 27.3, "SECURITY TERMINAL",
                 ["Vault 111 Security Office", "> Overseer's office: LOCKED", "> Unlock Overseer's office"]),
    "overseer": (52.9, 29.1, "OVERSEER'S TERMINAL",
                 ["Vault 111 Overseer", "> Exit corridor: SEALED", "> Unseal the exit corridor"]),
    "medical": (26.5, 1.3, "MEDICAL TERMINAL",
                ["Cryogenic stasis log", "Pods 1-12: life signs ended.", "Pod 4: REVIVED.", "> Close"]),
}
CONTROLS = {"door": (62.5, 11.0), "elevator": (70.5, 7.0)}
WALL_ART = {(8, 1): "wall_111", (4, 1): "sign", (40, 1): "poster", (22, 5): "vent", (46, 11): "vent",
            (33, 27): "vent", (59, 25): "vent", (56, 1): "vent", (49, 1): "wall_111", (20, 5): "pipe",
            (28, 9): "pipe", (41, 34): "poster", (33, 31): "sign", (55, 25): "poster", (62, 3): "sign"}
# items: id -> (kind, x, z)
ITEMS = {
    "stim1": ("stimpak", 23.0, 1.6), "baton": ("baton", 35.0, 12.6), "stim2": ("stimpak", 44.0, 9.9),
    "pistol": ("pistol", 36.3, 27.6), "ammo1": ("ammo", 45.0, 32.5), "stim3": ("stimpak", 53.9, 29.6),
    "ammo2": ("ammo", 50.0, 2.6), "pipboy": ("pipboy", 60.2, 8.2), "stim4": ("stimpak", 59.0, 2.6),
}
SKELETON = (60.5, 7.6)
# radroach nests: when you're inside the region, these come out
NESTS = [
    ("corr1", (19, 6, 32, 8), [("roach", 29.5, 6.5), ("roach", 31.5, 7.5)]),
    ("cafeteria", (34, 2, 46, 14), [("roach", 44.5, 3.5), ("roach", 45.5, 11.5), ("roach", 38.5, 13.5)]),
    ("security", (34, 26, 46, 33), [("roach", 45.5, 30.5), ("roach", 35.5, 32.5)]),
    ("overseer", (48, 26, 58, 33), [("roach", 57.5, 32.5)]),
    ("exit", (48, 2, 62, 12), [("roach", 50.5, 3.5), ("roach", 60.5, 3.5), ("roach", 56.5, 11.5),
                               ("roach", 49.5, 11.5)]),
]
# where each objective points
TARGETS = {"leave_cryo": (15.5, 7.5), "explore": (24.0, 7.5), "weapon": (35.0, 12.6), "security": (40.0, 28.5),
           "unlock": (45.3, 27.3), "overseer": (47.5, 29.5), "unseal": (52.9, 29.1), "exit_room": (55.0, 8.0),
           "pipboy": (60.2, 8.2), "open": (62.5, 11.0), "elevator": (67.5, 7.0)}


def build_grid():
    g = [["#"] * W for _ in range(H)]
    for x0, z0, x1, z1 in ROOMS.values():
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                g[z][x] = "."
    for cells, _k in DOORS.values():
        for x, z in cells:
            g[z][x] = "D"
    x0, z0, x1, z1 = ELEVATOR
    for z in range(z0, z1 + 1):
        for x in range(x0, x1 + 1):
            g[z][x] = "E"
    return g


GRID = build_grid()
DOOR_AT = {c: did for did, (cells, _k) in DOORS.items() for c in cells}


def cell(x, z):
    if 0 <= x < W and 0 <= z < H:
        return GRID[z][x]
    return "#"


def room_at(x, z):
    for name, (x0, z0, x1, z1) in ROOMS.items():
        if x0 <= x <= x1 and z0 <= z <= z1:
            return name
    return None


# ---- the mesh ------------------------------------------------------------------------------------------------------
def wall_face(buf, x, z, side, x0, z0, x1, z1):
    """One wall of a cell, from the floor to the ceiling, in three bands (base, panel, top)."""
    tex = WALL_ART.get((x, z))
    bands = (("wall_base", 0.0, 1.0), (tex or "wall", 1.0, 2.0), ("wall_top", 2.0, 3.0))
    shade = 0.78 if side in ("n", "s") else 0.62
    for t, y0, y1 in bands:
        quad(buf, (x0, y0, z0), (x1, y0, z1), (x1, y1, z1), (x0, y1, z0), t, shade)


def static_mesh(rng=None):
    """Floors, ceilings, walls, furniture: everything that never moves."""
    rng = rng or random.Random(4)
    buf = array("f")
    for z in range(H):
        for x in range(W):
            c = cell(x, z)
            if c == "#":
                continue
            floor = "elevator" if c == "E" else ("grate" if (x + z) % 7 == 0 and c == "." else "floor")
            quad(buf, (x, 0, z + 1), (x + 1, 0, z + 1), (x + 1, 0, z), (x, 0, z), floor, 0.9)
            ceil = "light" if (x % 3 == 1 and z % 3 == 1) else "ceiling"
            quad(buf, (x, WALL_H, z), (x + 1, WALL_H, z), (x + 1, WALL_H, z + 1), (x, WALL_H, z + 1), ceil, 0.55)
            if cell(x, z - 1) == "#":
                wall_face(buf, x, z - 1, "n", x, z, x + 1, z)
            if cell(x, z + 1) == "#":
                wall_face(buf, x, z + 1, "s", x + 1, z + 1, x, z + 1)
            if cell(x - 1, z) == "#":
                wall_face(buf, x - 1, z, "w", x, z + 1, x, z)
            if cell(x + 1, z) == "#":
                wall_face(buf, x + 1, z, "e", x + 1, z, x + 1, z + 1)
    for x0, z0, x1, z1, h, top, side in BOXES:
        if side == "pod":
            front = "pod_open" if (int(x0), int(z0)) == (5, 12) else "pod_front"
            if z0 < 6:                                   # the north row faces south (+z)
                box(buf, x0, 0, z0, x1, h, z1, "pod_side", "pod_side")
                quad(buf, (x0, 0, z1 + 0.01), (x1, 0, z1 + 0.01), (x1, h, z1 + 0.01), (x0, h, z1 + 0.01),
                     "pod_front", 0.85)
            else:
                box(buf, x0, 0, z0, x1, h, z1, "pod_side", "pod_side", front=front)
            continue
        box(buf, x0, 0, z0, x1, h, z1, top, side)
    for x0, z0, x1, z1, y0, y1 in SCREENS:               # terminal screens stand on their desks, facing +z
        box(buf, x0, y0, z0, x1, y1, z1, "metal", "metal")
        quad(buf, (x0, y0, z1 + 0.01), (x1, y0, z1 + 0.01), (x1, y1, z1 + 0.01), (x0, y1, z1 + 0.01), "screen", 1.0)
    return buf


def door_mesh(did):
    cells, kind = DOORS[did]
    xs = [c[0] for c in cells]
    zs = [c[1] for c in cells]
    x0, x1, z0, z1 = min(xs), max(xs) + 1, min(zs), max(zs) + 1
    buf = array("f")
    if kind == "gear":                                   # a thick slab with the gear on both faces
        box(buf, x0, 0, z0, x1, WALL_H, z1, "metal", "metal")
        quad(buf, (x0 - 0.01, 0, z1), (x0 - 0.01, 0, z0), (x0 - 0.01, WALL_H, z0), (x0 - 0.01, WALL_H, z1), "gear", 0.9)
        quad(buf, (x1 + 0.01, 0, z0), (x1 + 0.01, 0, z1), (x1 + 0.01, WALL_H, z1), (x1 + 0.01, WALL_H, z0), "gear", 0.9)
        return buf
    # a thin slab across the opening: it runs along the longer side
    if cell(x0, z0 - 1) == "." or cell(x0, z1) == ".":
        zc = (z0 + z1) / 2                               # connects north-south: thin in z
        box(buf, x0, 0, zc - 0.12, x1, WALL_H, zc + 0.12, "metal", "door", bottom=True)
    else:
        xc = (x0 + x1) / 2
        box(buf, xc - 0.12, 0, z0, xc + 0.12, WALL_H, z1, "metal", "door", bottom=True)
    return buf
