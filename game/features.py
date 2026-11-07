"""What makes a floor of the Deep more than rooms and monsters, laid on after it's made (and found whole):

The special floors - about one in five, from the second floor on, never a guardian's:
    dream     the Dreaming: the lights turned red, green and blue and shifting, the air swimming with colour, and
              ghosts of the band's creatures drifting about - they can't be hurt, and they don't hurt
    hoard     a Hoard: gold piled everywhere, more chests (some of them guarded), and coin on the floors
    den       a Den: one kind of creature only, and many of them, their nests and the bones of what they ate
    drowned   Drowned: the rooms flooded to the knee, the pipes in the walls pouring into them

The locked doors: a dead-end room (one way in, a passage a square wide) closed by a coloured door - red, blue,
green or gold - and its key somewhere Claude can reach without it; behind it, the vault: chests and gold.

The puzzles:
    levers    a door sealed with runes, no key to it: it opens when every lever on the floor has been pulled
    braziers  a room of cold braziers: shoot one and the trial begins - light them all before the first goes out
              (twelve seconds), and a chest rises from the floor

    L.special, L.doors, L.keys (on L.pickups as kind "key"), L.levers, L.braziers"""
import random
from collections import deque

from . import data as D
from . import dress

SPECIALS = {
    "dream": ("the Dreaming", "The air tastes of copper and the light won't hold still. Nothing here is quite what it seems."),
    "hoard": ("a Hoard", "Gold. Heaps of it, spilled and stacked and glinting. Someone - something - has been collecting."),
    "den": ("a Den", "A den. The smell says one kind of thing lives here, and lots of it."),
    "drowned": ("Drowned", "Water everywhere: pouring from the pipes, standing to the knee in the rooms. Wade carefully."),
    "rush": ("the Gauntlet", "Old roars echo from the far hall. Everything you've beaten down here wants another try."),
}
DOOR_COLOURS = {"red": (1.0, 0.25, 0.2), "blue": (0.3, 0.5, 1.0), "green": (0.3, 0.95, 0.4), "gold": (1.0, 0.8, 0.25),
                "rune": (0.75, 0.45, 1.0)}
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
BRAZIER_TIME = 12.0


def special_of(depth, seed):
    """Which special floor this is, if any (the same for the same run and floor)."""
    if depth < 2 or depth % 10 == 0:
        return None
    rng = random.Random(f"{seed}:special:{depth}")
    if rng.random() > 0.2:
        return None
    kinds = [k for k in SPECIALS if k != "rush" or depth > 11]       # (the Gauntlet: once a guardian has fallen)
    return rng.choice(kinds)


def apply(L, depth, seed):
    rng = random.Random(f"{seed}:features:{depth}")
    L.special = special_of(depth, seed)
    if L.special:
        name, line = SPECIALS[L.special]
        L.name, L.line = f"{L.name}: {name}", line
        {"dream": _dream, "hoard": _hoard, "den": _den, "drowned": _drowned, "rush": _rush}[L.special](L, rng, depth)
    if depth % 10 and rng.random() < 0.5:
        _locked_doors(L, rng, depth)
    if depth % 10 and rng.random() < 0.3:
        _levers(L, rng, depth)
    if rng.random() < 0.3:
        _braziers(L, rng, depth)
    if depth >= 2:
        _traps(L, rng, depth)
    _secrets(L, rng, depth)


# ---- the special floors ------------------------------------------------------------------------------------------
def _dream(L, rng, depth):
    """The lights coloured (the renderer turns them), half the creatures real, and ghosts of the rest."""
    cols = [(1.0, 0.15, 0.2), (0.15, 1.0, 0.3), (0.2, 0.35, 1.0)]
    L.lights = [(x, y, z, *rng.choice(cols), r * 1.2) for (x, y, z, _r, _g, _b, r) in L.lights]
    for room in L.rooms[1:]:
        if rng.random() < 0.6:
            x, y = room.centre
            if L.open_at(x, y):
                L.lights.append((x + 0.5, float(L.floor[y, x]) + 1.6, y + 0.5, *rng.choice(cols), 5.0))
    real = [s for s in L.spawns if not s.get("guardian")]
    rng.shuffle(real)
    L.spawns = real[: max(6, len(real) // 2)] + [s for s in L.spawns if s.get("guardian")]
    band = D.band_of(depth)
    for room in L.rooms[1:]:
        for _ in range(rng.randint(1, 3)):
            x, y = rng.randint(room.x, room.x + room.w - 1), rng.randint(room.y, room.y + room.h - 1)
            if L.open_at(x, y):
                L.ghosts.append({"monster": rng.choice(band["monsters"]), "x": x + 0.5, "z": y + 0.5})


def _hoard(L, rng, depth):
    from .levels import _pickup
    for room in L.rooms[1:]:
        for _ in range(rng.randint(3, 7)):
            x, y = rng.randint(room.x, room.x + room.w - 1), rng.randint(room.y, room.y + room.h - 1)
            if L.open_at(x, y) and not dress.clear_way(L, x, y):
                _pickup(L, x, y, rng, depth, "gold")
        for _ in range(rng.randint(2, 5)):
            x, y = rng.randint(room.x, room.x + room.w - 1), rng.randint(room.y, room.y + room.h - 1)
            if L.open_at(x, y) and not dress.clear_way(L, x, y):
                L.flats.append((x + 0.5, float(L.floor[y, x]) + 0.012, y + 0.5, 0.48, "sp.coins", rng.uniform(0, 6.3)))
                L.gold_squares.add((x, y))
    band = D.band_of(depth)
    for room in rng.sample(L.rooms[1:], k=min(len(L.rooms) - 1, 4)):
        for _ in range(20):
            x, y = rng.randint(room.x, room.x + room.w - 1), rng.randint(room.y, room.y + room.h - 1)
            if L.open_at(x, y) and not dress.clear_way(L, x, y) and not _taken(L, x, y):
                guard = [rng.choice(band["monsters"])] * rng.randint(1, 2) if rng.random() < 0.5 else None
                dress.chest(L, x, y, rng, guard=guard, rich=1.5)
                break
    L.tint = tuple(min(1.3, t * k) for t, k in zip(L.tint, (1.08, 1.02, 0.9)))
    L.lights = [(x, y, z, 1.0, 0.78, 0.32, r) for (x, y, z, _r, _g, _b, r) in L.lights]     # (the torches burn gold)


def _den(L, rng, depth):
    band = D.band_of(depth)
    kind = rng.choice(band["monsters"])
    L.den = kind
    L.line = f"A den of {kind}s. They know you're here." if not kind.endswith("s") else f"A den of {kind}. They know you're here."
    out = [s for s in L.spawns if s.get("guardian")]
    for s in L.spawns:
        if not s.get("guardian"):
            out.append(dict(s, monster=kind))
    start = L.rooms[0]
    for room in L.rooms[1:]:                                 # (and more of them)
        for _ in range(rng.randint(1, 3)):
            x, y = rng.randint(room.x, room.x + room.w - 1), rng.randint(room.y, room.y + room.h - 1)
            if L.open_at(x, y) and abs(x - start.centre[0]) + abs(y - start.centre[1]) > 8:
                out.append({"monster": kind, "x": x + rng.uniform(0.3, 0.7), "z": y + rng.uniform(0.3, 0.7)})
        if rng.random() < 0.6:
            for _ in range(10):
                x, y = rng.randint(room.x, room.x + room.w - 1), rng.randint(room.y, room.y + room.h - 1)
                if L.open_at(x, y) and not dress.clear_way(L, x, y) and not _taken(L, x, y):
                    spider = "Spider" in kind
                    L.sprites.append({"x": x + 0.5, "z": y + 0.5, "y": float(L.floor[y, x]), "w": 0.9 if not spider else 0.6,
                                      "h": 0.5 if not spider else 0.6, "name": "nest" if not spider else "sp.eggsac",
                                      "glow": None, "solid": 0})
                    break
    L.spawns = out


def _drowned(L, rng, depth):
    """Every room but the first and the stairs' flooded; pipes pouring into them from the walls."""
    start = L.rooms[0]
    sx, sy = int(L.stairs[0]), int(L.stairs[1])
    for room in L.rooms[1:]:
        if room.x <= sx < room.x + room.w and room.y <= sy < room.y + room.h:
            continue
        if room.kind == "piece":
            continue
        cells = [(x, y) for x, y in room.cells() if L.open_at(x, y)]
        for c in cells:
            L.water.add(c)
            L.wet.pop(c, None)
        # pipes pouring into it
        walls = [(x, y, dx, dy) for x, y in cells for dx, dy in DIRS if not L.open_at(x + dx, y + dy)]
        rng.shuffle(walls)
        for x, y, dx, dy in walls[: rng.randint(1, 3)]:
            f, c = float(L.floor[y, x]), float(L.ceil[y, x])
            top = f + min(c - f - 0.4, rng.uniform(1.2, 1.7))
            L.decals.append((x + 0.5 + dx * 0.495, top, y + 0.5 + dy * 0.495, -dx, -dy, 0.42, 0.42, "clut.pipe"))
            L.pours.append((x + 0.5 + dx * 0.36, top + 0.1, y + 0.5 + dy * 0.36, f + 0.24, -dx, -dy))
    for c in list(L.wet):
        L.wet[c] = 1.0
    del start


# ---- the locked doors --------------------------------------------------------------------------------------------
def _taken(L, x, y):
    return any(int(s["x"]) == x and int(s["z"]) == y for s in L.sprites) or \
        any(int(c["x"]) == x and int(c["z"]) == y for c in L.chests) or \
        (L.stairs and abs(x + 0.5 - L.stairs[0]) < 1.6 and abs(y + 0.5 - L.stairs[1]) < 1.6)


def _vaults(L):
    """Rooms with one way in, by a passage a square wide: -> [(room, mouth square, axis)] (axis: "ns" - the
    passage runs north-south, the door across it - or "ew")."""
    sx, sy = int(L.stairs[0]), int(L.stairs[1])
    out = []
    for room in L.rooms[1:]:
        if room.kind == "piece" or (room.x <= sx < room.x + room.w and room.y <= sy < room.y + room.h):
            continue
        inside = set(room.cells())
        mouths = set()
        for x, y in inside:
            if not L.open_at(x, y):
                continue
            for dx, dy in DIRS:
                n = (x + dx, y + dy)
                if n not in inside and L.open_at(*n):
                    mouths.add(n)
        if len(mouths) != 1:
            continue
        mx, my = next(iter(mouths))
        ns = not L.open_at(mx - 1, my) and not L.open_at(mx + 1, my)
        ew = not L.open_at(mx, my - 1) and not L.open_at(mx, my + 1)
        if ns == ew:
            continue
        if any(int(s["x"]) == mx and int(s["z"]) == my for s in L.spawns):
            continue
        out.append((room, (mx, my), "ns" if ns else "ew"))
    return out


def reach(L, shut=True):
    """The squares reachable from where Claude comes in, the closed doors closed (shut) or not."""
    blocked = {(d["x"], d["y"]) for d in L.doors if shut and not d["open"]}
    sx, sy = int(L.start[0]), int(L.start[1])
    seen = {(sx, sy)}
    q = deque([(sx, sy)])
    while q:
        x, y = q.popleft()
        for dx, dy in DIRS:
            n = (x + dx, y + dy)
            if n not in seen and n not in blocked and L.open_at(*n):
                seen.add(n)
                q.append(n)
    return seen


def _door(L, sq, axis, colour, room):
    x, y = sq
    L.doors.append({"x": x, "y": y, "axis": axis, "colour": colour, "open": False, "room": (room.x, room.y, room.w, room.h)})
    L.spawns = [s for s in L.spawns if not (room.x <= s["x"] < room.x + room.w and room.y <= s["z"] < room.y + room.h)]
    L.ghosts = [s for s in L.ghosts if not (room.x <= s["x"] < room.x + room.w and room.y <= s["z"] < room.y + room.h)]


def _fill_vault(L, room, rng, depth):
    from .levels import _pickup
    cells = [(x, y) for x, y in room.cells() if L.open_at(x, y) and not _taken(L, x, y)]
    rng.shuffle(cells)
    walls = [c for c in cells if any(not L.open_at(c[0] + dx, c[1] + dy) for dx, dy in DIRS)]
    for c in walls[: rng.randint(1, 2)]:
        dress.chest(L, c[0], c[1], rng, rich=2.2)
        cells.remove(c)
    for c in cells[: rng.randint(3, 6)]:
        _pickup(L, c[0], c[1], rng, depth, rng.choice(["gold", "gold", "item", "health", "mana"]))


def _locked_doors(L, rng, depth):
    vaults = _vaults(L)
    rng.shuffle(vaults)
    colours = ["red", "blue", "green", "gold"]
    rng.shuffle(colours)
    for (room, sq, axis), colour in zip(vaults[: rng.randint(1, 2)], colours):
        _door(L, sq, axis, colour, room)
        _fill_vault(L, room, rng, depth)
        # the key: somewhere he can get to with every door shut, well away from the door
        can = [c for c in reach(L) if not dress.clear_way(L, *c) and not _taken(L, *c)
               and abs(c[0] - sq[0]) + abs(c[1] - sq[1]) > 10 and (c[0], c[1]) not in L.water]
        if not can:
            L.doors.pop()
            continue
        kx, ky = rng.choice(can)
        L.pickups.append({"x": kx + 0.5, "z": ky + 0.5, "y": float(L.floor[ky, kx]), "kind": "key", "colour": colour,
                          "phase": rng.uniform(0, 6.28)})


# ---- the puzzles -------------------------------------------------------------------------------------------------
def _levers(L, rng, depth):
    vaults = [v for v in _vaults(L) if v[1] not in {(d["x"], d["y"]) for d in L.doors}]
    if not vaults:
        return
    room, sq, axis = rng.choice(vaults)
    _door(L, sq, axis, "rune", room)
    _fill_vault(L, room, rng, depth)
    can = [c for c in reach(L) if any(not L.open_at(c[0] + dx, c[1] + dy) for dx, dy in DIRS)
           and not dress.clear_way(L, *c) and not _taken(L, *c) and c not in L.water]
    rng.shuffle(can)
    for x, y in can:
        if len(L.levers) >= 3:
            break
        if any(abs(x - lv["x"]) + abs(y - lv["y"]) < 12 for lv in L.levers) or abs(x - sq[0]) + abs(y - sq[1]) < 8:
            continue
        for dx, dy in DIRS:
            if not L.open_at(x + dx, y + dy):
                f = float(L.floor[y, x])
                L.decals.append((x + 0.5 + dx * 0.495, f + 0.55, y + 0.5 + dy * 0.495, -dx, -dy, 0.45, 0.6, "lever"))
                L.levers.append({"x": x, "y": y, "px": x + 0.5 + dx * 0.38, "pz": y + 0.5 + dy * 0.38, "py": f + 0.85,
                                 "pulled": False})
                break
    if len(L.levers) < 2:                                  # (not enough places for them: no puzzle after all)
        L.doors.pop()
        L.levers.clear()


def _braziers(L, rng, depth):
    rooms = [r for r in L.rooms[1:] if r.w >= 4 and r.h >= 4 and r.kind != "piece" and
             not (r.x <= L.stairs[0] < r.x + r.w and r.y <= L.stairs[1] < r.y + r.h)]
    if not rooms:
        return
    room = rng.choice(rooms)
    n = rng.choice((3, 4, 4, 5))
    corners = [(room.x, room.y), (room.x + room.w - 1, room.y), (room.x, room.y + room.h - 1),
               (room.x + room.w - 1, room.y + room.h - 1), (room.x + room.w // 2, room.y)]
    for x, y in corners[:n]:
        if not L.open_at(x, y) or dress.clear_way(L, x, y) or _taken(L, x, y):
            continue
        f = float(L.floor[y, x])
        L.braziers.append({"x": x + 0.5, "z": y + 0.5, "y": f, "lit": False, "sprite": len(L.sprites)})
        L.sprites.append({"x": x + 0.5, "z": y + 0.5, "y": f, "w": 0.8, "h": 1.05, "name": "nx.brazier_cold", "glow": None,
                          "solid": 0.25})
    if len(L.braziers) < 3:
        for b in reversed(L.braziers):
            L.sprites.pop(b["sprite"])
        L.braziers.clear()
        return
    cx, cy = room.centre
    L.trial = {"x": cx, "y": cy, "done": False, "until": 0.0}
    L.pieces.append({"name": "the cold braziers", "line": "Cold braziers stand round the room. Something waits for them "
                     "to burn together - all at once, and quickly.", "x0": room.x, "y0": room.y,
                     "x1": room.x + room.w - 1, "y1": room.y + room.h - 1})


# ---- the Gauntlet: a boss rush ----------------------------------------------------------------------------------
RUSH_HP, RUSH_DMG = 0.55, 0.8                              # (each champion: lighter than at its own floor - there are several)


def _rush(L, rng, depth):
    """The guardians of the bands already passed, the newest last, waiting in the stairs' hall - they come one at a
    time once he steps in, and the stairs stay sealed till the last falls. A Legendary chest for the end of it."""
    bi = (depth - 1) // 10
    L.rush = [b["guardian"] for b in D.BANDS[:bi]][-4:]
    sx, sy = int(L.stairs[0]), int(L.stairs[1])
    hall = next((r for r in L.rooms if r.x <= sx < r.x + r.w and r.y <= sy < r.y + r.h), None)
    if hall is None or not L.rush:
        L.rush = []
        return
    L.arena = (hall.x, hall.y, hall.w, hall.h)
    L.guardian = "The Gauntlet"
    L.spawns = [s for s in L.spawns if not (hall.x <= s["x"] < hall.x + hall.w and hall.y <= s["z"] < hall.y + hall.h)]
    L.lights += [(hall.x + 0.5, float(L.floor[hall.y, hall.x]) + 1.4, hall.y + 0.5, 1.0, 0.35, 0.25, 7.0),
                 (hall.x + hall.w - 0.5, float(L.floor[hall.y, hall.x + hall.w - 1]) + 1.4, hall.y + hall.h - 0.5, 1.0, 0.35, 0.25, 7.0)]


# ---- the traps ---------------------------------------------------------------------------------------------------
TRAPS = {"spikes": "nx.spikeplate", "darts": "nx.dartplate", "fire": "nx.vent"}
FIRE_CYCLE, FIRE_ON = 4.0, 1.4                             # (a vent: every four seconds, a second and a half of flame)


def _traps(L, rng, depth):
    """Spike plates, dart plates (the darts from the wall beside them) and fire vents, two to eight of them - never in
    the first room, by the stairs, in water, by a door, on a chest."""
    start = L.rooms[0] if L.rooms else None
    arena = getattr(L, "arena", None)
    doors = {(d["x"], d["y"]) for d in L.doors}
    n = min(8, 2 + depth // 12)
    cells = [c for c in L.open_squares()
             if not (start and start.x - 1 <= c[0] <= start.x + start.w and start.y - 1 <= c[1] <= start.y + start.h)
             and not (arena and arena[0] <= c[0] < arena[0] + arena[2] and arena[1] <= c[1] < arena[1] + arena[3])
             and c not in L.water and c not in doors and not _taken(L, *c)
             and all(abs(c[0] - dx) + abs(c[1] - dy) > 2 for dx, dy in doors)]
    rng.shuffle(cells)
    for x, y in cells:
        if len(L.traps) >= n:
            break
        if any(abs(x - t["x"]) + abs(y - t["y"]) < 6 for t in L.traps):
            continue
        walls = [(dx, dy) for dx, dy in DIRS if not L.open_at(x + dx, y + dy)]
        kind = rng.choice(["spikes", "spikes", "fire"] + (["darts", "darts"] if walls else []))
        f = float(L.floor[y, x])
        t = {"kind": kind, "x": x, "y": y, "f": f, "at": -99.0, "phase": rng.uniform(0, FIRE_CYCLE)}
        if kind == "darts":
            dx, dy = rng.choice(walls)                       # (the dart-hole: in the wall beside the plate)
            t["from"] = (x + 0.5 + dx * 0.46, f + 0.95, y + 0.5 + dy * 0.46)
            L.decals.append((x + 0.5 + dx * 0.495, f + 0.8, y + 0.5 + dy * 0.495, -dx, -dy, 0.32, 0.3, "clut.port"))
        L.flats.append((x + 0.5, f + 0.014, y + 0.5, 0.42 if kind != "fire" else 0.36, TRAPS[kind], rng.choice((0.0, 1.5708))))
        L.traps.append(t)


# ---- secrets: rooms behind cracked walls, and two that are always where they are -----------------------------------
EGGS = ("workshop", "answer", "moon", "xyzzy", "lich")


def _secrets(L, rng, depth):
    if depth == 1:
        _hidden_room(L, rng, depth, "workshop")
    elif depth == 42:
        _hidden_room(L, rng, depth, "answer")
    elif depth % 10 and rng.random() < 0.15:
        _hidden_room(L, rng, depth, "cache")


def _hidden_room(L, rng, depth, what):
    """A 3x3 room carved out of the rock behind a room's wall, the wall left standing with a crack in it - a bolt
    breaks it (L.secret_walls). -> True if there was rock enough for it."""
    spots = []
    for room in L.rooms[1:]:
        if room.kind == "piece":
            continue
        for x, y in room.cells():
            if not L.open_at(x, y):
                continue
            for dx, dy in DIRS:
                wx, wy = x + dx, y + dy
                if L.open_at(wx, wy) or (wx, wy) in L.paths:
                    continue
                # the room beyond: 3x3 from the wall on, and a square of rock all round it
                cx, cy = wx + dx * 2, wy + dy * 2
                box = [(cx + i, cy + j) for i in range(-2, 3) for j in range(-2, 3)]
                if all(1 <= bx < L.w - 1 and 1 <= by < L.h - 1 and not L.open_at(bx, by) and (bx, by) not in L.paths
                       for bx, by in box):
                    spots.append((x, y, dx, dy))
    if not spots:
        return False
    x, y, dx, dy = rng.choice(spots)
    wx, wy = x + dx, y + dy
    cx, cy = wx + dx * 2, wy + dy * 2
    f, c = float(L.floor[y, x]), float(L.ceil[y, x])
    for i in range(-1, 2):
        for j in range(-1, 2):
            L.solid[cy + j, cx + i] = False
            L.floor[cy + j, cx + i] = f
            L.ceil[cy + j, cx + i] = min(c, f + 2.4)
    L.secret_walls[(wx, wy)] = {"open": False, "what": what, "room": (cx - 1, cy - 1, 3, 3), "f": f, "c": c}
    L.decals.append((x + 0.5 + dx * 0.495, f + 0.15, y + 0.5 + dy * 0.495, -dx, -dy, 0.9, 1.3, "decal.crack"))
    lines = {"workshop": ("a hidden workshop", "A tiny workshop: sawdust, candle-ends, a bench. Carved into the bench, "
                          "in two hands: 'Made by Jason and Claude, in the Claude Timeline. Thank you for playing.'"),
             "answer": ("a quiet room", "A small, quiet room. A towel hangs on a peg. Scratched into the wall: 'The "
                        "answer was forty-two. Nobody remembers the question.'"),
             "cache": ("a hidden cache", "Somebody walled this up on purpose. Somebody isn't coming back for it.")}
    name, line = lines[what]
    L.pieces.append({"name": name, "line": line, "x0": cx - 1, "y0": cy - 1, "x1": cx + 1, "y1": cy + 1,
                     "egg": what if what in EGGS else None})
    from .levels import _pickup
    dress.chest(L, cx + dx, cy + dy, rng, rich=2.0 if what == "cache" else 2.5)
    L.chests[-1]["secret"] = True
    if what == "workshop":
        L.sprites.append({"x": cx + 0.5 - dx * 0.0 + dy * 0.9, "z": cy + 0.5 + dx * 0.9, "y": f, "w": 1.0, "h": 0.7,
                          "name": "fu.table", "glow": None, "solid": 0.35})
        L.sprites.append({"x": cx + 0.5 - dy * 0.9, "z": cy + 0.5 - dx * 0.9, "y": f, "w": 0.6, "h": 0.6,
                          "name": "lm.candles", "glow": (1.0, 0.75, 0.4), "solid": 0.1})
        L.lights.append((cx + 0.5, f + 1.0, cy + 0.5, 1.0, 0.75, 0.4, 4.0))
    elif what == "answer":
        L.pickups.append({"x": cx + 0.5, "z": cy + 0.5, "y": f, "kind": "egg", "egg": "answer", "phase": 0.0})
    else:
        for _ in range(3):
            _pickup(L, cx + rng.randint(-1, 1), cy + rng.randint(-1, 1), rng, depth, "gold")
    return True
