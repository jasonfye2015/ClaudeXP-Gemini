"""Dressing a floor of the Deep with Claude and Magic's things (its painted art, exported into assets/cm by
tools/export_cm_art.py): pipe mouths that drip, barred grates and drain ports at the walls' feet, webs in the
corners, moss, roots, chains, sconces and banners on the walls, beams, ribs, stalactites and hanging roots overhead,
stalagmites, and each band's own things on the floor - and its set-piece rooms ("the unique rooms": the Bone Room,
the Chapel of Candles, the Cold Store, the Wolf Den and the rest, with their own lines), read from
assets/cm/setpieces.json and laid into the floor's rooms.

What a floor gets (all in squares, y up; names are the pictures in assets/cm without .png):
  L.decals   (x, y0, z, nx, nz, w, h, name)        a picture on a wall face, facing (nx, nz)
  L.flats    (x, y, z, size, name, yaw)            a picture lying on the floor
  L.webs     (x, y, z, ax, az, size, name)         a picture across a corner under the ceiling (ax, az: the corner)
  L.hangs    (x, y, z, w, h, name)                 a picture hanging from the ceiling (two crossed)
  L.sprites  dicts: x, z, y, w, h, name, glow (rgb) or None, solid (radius) or 0
  L.drips    (x, y_top, z, y_floor)                a pipe mouth's drip
  L.chests   dicts: x, z, opened, guard [names], gold (times), items, note
  L.water    set of (cx, cy): wading water
  L.pieces   dicts: name, line, x0, y0, x1, y1 (the set pieces)
"""
import json
import math
from pathlib import Path

from . import data as D

ASSETS = Path(__file__).resolve().parents[1] / "assets" / "cm"
# Claude and Magic's ten themes, as its set pieces name them by index, for each of our bands
CM_THEME_OF_BAND = [0, 5, 1, 8, 6, 7, 9, 2, 3, 4]

# per band: wall pictures; wall-foot things; overheads; floor things (name, w, h, glow, solid); stalagmites; webs
BANDS = [
    {"walls": ["decal.crack", "decal.sconce", "decal.chains", "decal.niche", "decal.soot", "decal.patch"],
     "feet": ["clut.grate", "clut.port"], "over": ["over.beam"], "webs": 0.35, "stal": 0.08,
     "floor": [("bones", 0.5, 0.3, None, 0), ("fu.shelf", 0.9, 0.9, None, 0.3), ("fu.rack", 0.8, 0.9, None, 0.3)]},
    {"walls": ["decal.moss", "decal.roots", "decal.wet", "mood.vines"], "feet": ["clut.port"], "over": ["over.hangroot"],
     "webs": 0.1, "stal": 0.12,
     "floor": [("clut.glowcap", 0.55, 0.45, (0.45, 1.0, 0.55), 0), ("fungus", 0.6, 0.6, (0.3, 0.7, 0.4), 0.2),
               ("lm.caps", 0.8, 0.8, (0.35, 0.8, 0.45), 0.25)]},
    {"walls": ["decal.wet", "decal.moss", "decal.crack"], "feet": ["clut.pipe", "clut.port", "clut.grate", "clut.pipe"],
     "over": ["over.beam"], "webs": 0.08, "stal": 0.18, "pools": True,
     "floor": [("rope", 0.5, 0.5, None, 0), ("fountain_dry", 0.9, 0.9, None, 0.35)]},
    {"walls": ["decal.niche", "decal.crack", "decal.sconce", "decal.chains"], "feet": ["clut.grate"], "over": ["over.rib"],
     "webs": 0.4, "stal": 0.06,
     "floor": [("bones", 0.5, 0.3, None, 0), ("fu.sarc", 1.0, 0.7, None, 0.4), ("lm.skulls", 0.8, 0.8, None, 0.3)]},
    {"walls": ["decal.crack", "decal.frost"], "feet": [], "over": ["over.stalactite"], "webs": 0.05, "stal": 0.34,
     "floor": [("crystal", 0.6, 0.8, (0.7, 0.5, 1.0), 0.2), ("lm.crystal", 0.9, 1.3, (0.75, 0.55, 1.0), 0.3),
               ("sp.crystal", 0.5, 0.8, (0.6, 0.8, 1.0), 0.2)]},
    {"walls": ["decal.soot", "decal.chains", "decal.crack"], "feet": ["clut.pipe", "clut.pipe", "clut.grate"],
     "over": ["over.beam"], "webs": 0.1, "stal": 0.0,
     "floor": [("anvil", 0.8, 0.6, None, 0.3), ("lm.crucible", 0.9, 0.8, (1.0, 0.5, 0.15), 0.35),
               ("brazier", 0.6, 0.8, (1.0, 0.55, 0.2), 0.25)]},
    {"walls": ["decal.roots", "decal.moss", "mood.vines", "mood.roots"], "feet": [], "over": ["over.hangroot"],
     "webs": 0.15, "stal": 0.1,
     "floor": [("root", 0.8, 0.7, None, 0.25), ("lm.root", 1.0, 1.0, None, 0.3), ("clut.glowcap", 0.5, 0.4, (0.5, 1.0, 0.5), 0)]},
    {"walls": ["decal.soot", "decal.crack"], "feet": ["clut.pipe"], "over": ["over.stalactite"], "webs": 0.05, "stal": 0.2,
     "floor": [("ember", 0.7, 0.4, (1.0, 0.45, 0.15), 0), ("brazier", 0.6, 0.8, (1.0, 0.55, 0.2), 0.25),
               ("lm.pour", 0.8, 1.0, (1.0, 0.5, 0.1), 0.3)]},
    {"walls": ["decal.banner", "decal.sconce", "decal.niche", "decal.chains"], "feet": ["clut.grate"], "over": ["over.rib"],
     "webs": 0.3, "stal": 0.04,
     "floor": [("lm.skulls", 0.8, 0.8, None, 0.3), ("fu.banner", 0.7, 1.2, None, 0.2), ("lm.candles", 0.7, 0.7, (1.0, 0.75, 0.4), 0.2),
               ("fu.sarc", 1.0, 0.7, None, 0.4)]},
    {"walls": ["decal.banner", "decal.crack", "decal.soot", "decal.chains"], "feet": ["clut.grate"],
     "over": ["over.rib", "over.beam"], "webs": 0.25, "stal": 0.1,
     "floor": [("lm.candles", 0.7, 0.7, (1.0, 0.75, 0.4), 0.2), ("lm.saint", 0.8, 1.4, None, 0.3), ("bones", 0.5, 0.3, None, 0)]},
]

# the set pieces' letters: what stands on the square. sprite: (name, w, h, glow, solid); floor: a height change;
# spawn: monsters that wait there; chest: a chest; water: wading water; light: a light there; tree: a tree mesh
LETTERS = {
    "T": {"tree": True}, "~": {"water": True}, "G": {"sprite": ("clut.glowcap", 0.55, 0.45, (0.45, 1.0, 0.55), 0)},
    "B": {"sprite": ("bones", 0.9, 0.55, None, 0.35)}, "b": {"sprite": ("bones", 0.9, 0.55, None, 0.35), "chest": True},
    "X": {}, "c": {"chest": True}, "R": {"floor": 0.35}, "V": {"floor": -0.35},
    "*": {"sprite": ("brazier", 0.6, 0.8, (1.0, 0.55, 0.2), 0.25)}, "A": {"sprite": ("lm.altar", 1.0, 0.9, (1.0, 0.8, 0.5), 0.4)},
    "M": {"sprite": ("lm.cap", 1.2, 1.5, (0.4, 0.9, 0.5), 0.45)}, "H": {"walldoor": "door"}, "h": {"walldoor": "decal.niche"},
    "m": {"chest": True, "spawn": ["Mimic"]}, "F": {"plant": "flowers"}, "q": {"drip": True}, "r": {"sprite": ("rope", 0.4, 1.6, None, 0.1)},
    "e": {"sprite": ("sp.bell", 0.8, 1.2, None, 0.3)}, "v": {"sprite": ("sp.fire", 0.5, 0.5, (1.0, 0.5, 0.2), 0)},
    "w": {"sprite": ("sp.scale", 0.9, 1.1, None, 0.35)}, "s": {"sprite": ("fu.sarc", 1.0, 0.7, None, 0.4)},
    "d": {"spawn": ["Wolf"]}, "z": {"sprite": ("sp.meat", 0.6, 0.4, None, 0)}, "y": {"spawn": ["Troll"]},
    "p": {"sprite": ("sp.mural", 0.9, 1.1, None, 0.3)}, "o": {"sprite": ("sp.orrery", 1.1, 1.3, (0.9, 0.8, 0.5), 0.4)},
    "u": {"sprite": ("sp.desk", 1.0, 0.8, None, 0.4)}, "x": {"flat": "decal.patch"}, "i": {"sprite": ("sp.mirror", 0.7, 1.4, None, 0.25)},
    "f": {"sprite": ("sp.hook", 0.5, 1.1, None, 0.1)}, "l": {"sprite": ("sp.ice", 0.8, 1.0, (0.6, 0.85, 1.0), 0.35)},
    "a": {"flat": "dl.grate"}, "k": {"sprite": ("sp.lever", 0.4, 0.7, None, 0.1)}, "9": {"chest": True},
    "S": {"sprite": ("lm.saint", 0.8, 1.5, None, 0.3)}, "g": {"sprite": ("lm.candles", 0.6, 0.6, (1.0, 0.75, 0.4), 0.1)},
    "1": {"sprite": ("sp.eggsac", 0.6, 0.6, None, 0.2)}, "7": {"sprite": ("sp.cocoon", 0.5, 1.1, None, 0.2)},
    "j": {"spawn": ["Cellar Spider", "Cellar Spider"]}, "2": {"sprite": ("sp.cage", 0.8, 1.1, None, 0.35)},
    "3": {"sprite": ("sp.cage", 0.8, 1.1, None, 0.35), "spawn": ["Iron Hound"]}, "4": {"spawn": ["Charnel Hound"]},
    "5": {"sprite": ("sp.plaque", 0.6, 0.7, None, 0.1)}, "6": {"sprite": ("sp.bell", 0.8, 1.2, None, 0.3)},
    "0": {"sprite": ("bones", 1.0, 0.6, None, 0.35)}, "8": {"plant": "crate"}, "=": {"floor_tex": "ground.planks"},
    "_": {"floor": -0.7}, "+": {"sprite": ("sp.seastone", 1.0, 0.8, (1.0, 0.6, 0.3), 0.45)}, "|": {"drip": True, "water": True},
    "@": {"light": (1.0, 0.8, 0.5)}, "^": {"sprite": ("rope", 0.4, 1.6, None, 0.1)}, "&": {"sprite": ("lm.altar", 1.0, 0.9, None, 0.4), "water": True},
    "!": {"plant": "willow_dead"}, "%": {"plant": "common_dead"}, "Y": {"sprite": ("lm.throne", 1.2, 1.6, None, 0.45)},
    "I": {"sprite": ("sp.hourglass", 0.8, 1.6, None, 0.35)}, "?": {"sprite": ("lm.saint", 0.8, 1.5, None, 0.3)},
    "J": {"sprite": ("sp.blade", 0.9, 1.4, None, 0.0)}, "Z": {"dark": True}, "O": {"sprite": ("sp.ice", 0.8, 1.0, (0.6, 0.85, 1.0), 0.35)},
    "E": {}, "$": {"flat": "sp.coins", "gold": True}, "N": {"sprite": ("lm.altar", 1.0, 0.9, (1.0, 0.85, 0.4), 0.4), "chest": True},
    "U": {"sprite": ("gate", 1.0, 1.4, None, 0.0)}, "Q": {"low": 1.15}, "K": {"sprite": ("sp.scale", 0.9, 1.1, (1.0, 0.9, 0.6), 0.35)},
    ",": {"sprite": ("sp.die", 0.7, 0.7, None, 0.3)}, "P": {"sprite": ("nest", 1.0, 0.6, None, 0.35), "spawn": ["Giant Rat"] * 3},
    "(": {"sprite": ("sp.egg", 0.5, 0.6, None, 0.2)}, ")": {"sprite": ("sp.fire", 0.7, 0.7, (1.0, 0.55, 0.2), 0.25), "spawn": ["Sellsword"]},
    "<": {"sprite": ("sp.coffin", 1.0, 0.7, None, 0.4), "spawn": ["Vampire"]}, ">": {"sprite": ("lm.anvil", 0.9, 0.8, (1.0, 0.5, 0.2), 0.35), "spawn": ["Slag Golem"]},
    "{": {"sprite": ("lm.water", 1.0, 1.0, (0.4, 0.7, 1.0), 0.4)}, "[": {"walldoor": "sp.mural"},
    "]": {"sprite": ("sp.coldfire", 0.7, 0.5, None, 0.2)}, ":": {"sprite": ("fu.table", 1.0, 0.7, None, 0.4)},
    ";": {"walldoor": "decal.crack"}, "n": {"sprite": ("nest", 0.9, 0.5, None, 0.3)}, "t": {"sprite": ("fu.table", 1.0, 0.7, None, 0.4)},
    "L": {}, "W": {}, "D": {}, "S'": {},
}
_pieces = None


def set_pieces():
    global _pieces
    if _pieces is None:
        try:
            _pieces = json.loads((ASSETS / "setpieces.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _pieces = []
    return _pieces


def pieces_for(depth):
    """The set pieces that may stand on this floor (their least floor, their bands - Claude and Magic's)."""
    band = (depth - 1) // 10
    theme = CM_THEME_OF_BAND[min(9, band)]
    out = []
    for p in set_pieces():
        if depth < max(1, int(p.get("min", 1) * 1.4)):
            continue
        if p.get("max") and depth > int(p["max"] * 1.4) + 4:
            continue
        if p.get("bands") and theme not in p["bands"]:
            continue
        out.append(p)
    return out


def size_of(p):
    rows = p["rows"]
    return len(rows[0]) - 2, len(rows) - 2


def dress(L, rng, band_index):
    """The band's dressing on every room and corridor of a floor (after its shapes and set pieces)."""
    B = BANDS[band_index]
    taken = {(int(s["x"]), int(s["z"])) for s in L.sprites} | {(int(c["x"]), int(c["z"])) for c in L.chests}
    near_stairs = lambda x, y: L.stairs and abs(x + 0.5 - L.stairs[0]) < 1.6 and abs(y + 0.5 - L.stairs[1]) < 1.6   # noqa: E731
    in_piece = lambda x, y: any(p["x0"] <= x <= p["x1"] and p["y0"] <= y <= p["y1"] for p in L.pieces)   # noqa: E731
    for (x, y) in L.open_squares():
        f, c = float(L.floor[y, x]), float(L.ceil[y, x])
        walls = [(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if not L.open_at(x + dx, y + dy)]
        piece = in_piece(x, y)
        # on the walls
        for dx, dy in walls:
            r = rng.random()
            if r < 0.07 and B["walls"]:
                name = rng.choice(B["walls"])
                tall = name in ("decal.banner", "decal.chains", "decal.roots", "mood.vines", "mood.roots", "decal.wet", "decal.moss")
                h = min(c - f - 0.1, 1.3 if tall else 0.8)
                lift = (c - f - h - 0.05) if name in ("decal.roots", "mood.roots", "mood.vines", "decal.banner") else \
                    (0.0 if name in ("decal.moss", "decal.wet") else rng.uniform(0.35, 0.6))
                _wall(L, x, y, dx, dy, f + max(0.0, lift), 0.95 if tall else 0.8, h, name)
            elif r < 0.10 and B["feet"] and not piece:
                name = rng.choice(B["feet"])
                if name == "clut.pipe":
                    top = f + min(c - f - 0.5, rng.uniform(1.0, 1.35))
                    _wall(L, x, y, dx, dy, top, 0.42, 0.42, name)
                    px, pz = x + 0.5 + dx * 0.36, y + 0.5 + dy * 0.36
                    L.drips.append((px, top + 0.08, pz, f))
                    L.flats.append((px - dx * 0.05, f + 0.012, pz - dy * 0.05, 0.32, "dk.pool", rng.uniform(0, math.tau)))
                else:
                    _wall(L, x, y, dx, dy, f, 0.6, 0.45, name)
        # webs in the corners, under the ceiling
        if len(walls) >= 2 and rng.random() < B["webs"]:
            for (ax, ay), (bx, by) in ((walls[0], walls[1]),):
                if ax == -bx and ay == -by:
                    continue
                cx, cz = x + 0.5 + (ax + bx) * 0.5, y + 0.5 + (ay + by) * 0.5
                L.webs.append((cx, c, cz, ax + bx, ay + by, 0.55, "clut.web"))
        # overhead
        if B["over"] and rng.random() < 0.06 and c - f < 3.2:
            name = rng.choice(B["over"])
            L.hangs.append((x + 0.5, c, y + 0.5, 0.9 if name in ("over.beam", "over.rib") else 0.7,
                            0.35 if name in ("over.beam", "over.rib") else 0.6, name))
        # on the floor
        if (x, y) in taken or near_stairs(x, y) or piece:
            continue
        if walls and rng.random() < 0.035 and B["floor"]:
            name, w, h, glow, solid = rng.choice(B["floor"])
            k = rng.uniform(0.85, 1.15)
            ox, oz = (walls[0][0] * 0.22, walls[0][1] * 0.22)
            L.sprites.append({"x": x + 0.5 + ox, "z": y + 0.5 + oz, "y": f, "w": w * k, "h": h * k, "name": name,
                              "glow": glow, "solid": solid})
            taken.add((x, y))
            if glow:
                L.lights.append((x + 0.5 + ox, f + h * 0.6, y + 0.5 + oz, *glow, 3.2))
        elif walls and rng.random() < B["stal"]:
            w = walls[0]
            L.props.append({"model": rng.choice(["stalagmite_s", "stalagmite_m", "stalagmite_l"]),
                            "x": x + 0.5 + w[0] * 0.3, "z": y + 0.5 + w[1] * 0.3, "yaw": rng.uniform(0, math.tau),
                            "scale": rng.uniform(0.8, 1.2), "y": f})
        if rng.random() < B["stal"] * 0.6 and c - f < 3.5:
            L.props.append({"model": rng.choice(["stalactite_s", "stalactite_m"]), "x": x + rng.uniform(0.2, 0.8),
                            "z": y + rng.uniform(0.2, 0.8), "yaw": rng.uniform(0, math.tau), "scale": rng.uniform(0.8, 1.2),
                            "y": c})


def _wall(L, x, y, dx, dy, y0, w, h, name):
    """A picture on the wall of square (x, y) toward (dx, dy): centred on the face, a hair off it."""
    cx, cz = x + 0.5 + dx * 0.495, y + 0.5 + dy * 0.495
    L.decals.append((cx, y0, cz, -dx, -dy, w, h, name))


def chest(L, x, y, rng, guard=None, note=None, rich=1.0):
    L.chests.append({"x": x + 0.5, "z": y + 0.5, "y": float(L.floor[y, x]), "opened": False,
                     "guard": [g for g in (guard or []) if g in D.MONSTERS], "rich": rich, "note": note})


def place_piece(L, room, piece, rng):
    """Lay a set piece's letters into a room carved for it (its walls and squares; the corridors kept open)."""
    rows = piece["rows"]
    x0, y0 = room.x - 1, room.y - 1
    chests = piece.get("chests") or {}
    L.pieces.append({"name": piece["name"], "line": piece.get("line", ""), "x0": room.x, "y0": room.y,
                     "x1": room.x + room.w - 1, "y1": room.y + room.h - 1})
    for ry, row in enumerate(rows):
        for rx, ch in enumerate(row):
            x, y = x0 + rx, y0 + ry
            if not (room.x <= x < room.x + room.w and room.y <= y < room.y + room.h):
                continue                                   # (the ring: the room's own walls)
            if ch == "#":
                if (x, y) not in L.paths:
                    L.solid[y, x] = True
                continue
            spec = LETTERS.get(ch, {})
            if (x, y) in L.paths:                          # (a corridor runs through: it stays level and clear)
                spec = {k: v for k, v in spec.items() if k not in ("floor", "water", "low", "tree", "plant", "sprite")}
            f = float(L.floor[y, x])
            if "floor" in spec:
                f = spec["floor"]
                L.floor[y, x] = f
            if spec.get("water"):
                L.water.add((x, y))
                L.floor[y, x] = f = -0.3
            if "floor_tex" in spec:
                L.ftex[y, x] = L.tex(spec["floor_tex"])
            if "low" in spec:
                L.ceil[y, x] = spec["low"]
            if spec.get("tree"):
                L.props.append({"model": rng.choice(["common", "birch", "willow"]), "x": x + 0.5, "z": y + 0.5,
                                "yaw": rng.uniform(0, math.tau), "scale": 0.55, "y": f, "solid": True})
            if "plant" in spec:
                L.props.append({"model": spec["plant"], "x": x + 0.5, "z": y + 0.5, "yaw": rng.uniform(0, math.tau),
                                "scale": 0.5, "y": f})
            if "sprite" in spec:
                name, w, h, glow, solid = spec["sprite"]
                L.sprites.append({"x": x + 0.5, "z": y + 0.5, "y": f, "w": w, "h": h, "name": name, "glow": glow, "solid": solid})
                if glow:
                    L.lights.append((x + 0.5, f + h * 0.7, y + 0.5, *glow, 3.5))
            if "flat" in spec:
                L.flats.append((x + 0.5, f + 0.012, y + 0.5, 0.48, spec["flat"], 0.0))
            if "walldoor" in spec:
                for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                    if not L.open_at(x + dx, y + dy):
                        _wall(L, x, y, dx, dy, f, 0.85, 1.35, spec["walldoor"])
                        break
            if "light" in spec:
                L.lights.append((x + 0.5, f + 1.4, y + 0.5, *spec["light"], 5.0))
            if spec.get("drip"):
                L.drips.append((x + 0.5, float(L.ceil[y, x]) - 0.05, y + 0.5, f))
            if spec.get("gold"):
                L.gold_squares = getattr(L, "gold_squares", set()) | {(x, y)}
            if spec.get("chest"):
                c = chests.get(ch, {})
                chest(L, x, y, rng, c.get("guard") or (piece.get("stir") if ch == "b" else None), c.get("note"), rich=1.6)
            for name in spec.get("spawn", []):
                if name in D.MONSTERS:
                    L.spawns.append({"monster": name, "x": x + 0.5, "z": y + 0.5, "piece": piece["name"]})
