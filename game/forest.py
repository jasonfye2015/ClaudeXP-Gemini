"""The forest round Thornwick: the clearing sits in the middle of a wood far bigger than the town, and trails wind out
from the clearing's four ways to its glades - each a place of its own, with a line said on the first step in:

    the Mossy Pond        still water, lilypads and the frogs that own it
    the Old Shrine        a ring of standing stones about an altar, and something left on it
    the Woodcutter's Camp Rook's fire, his logs and his stumps (Rook talks, as the vendors do)
    the Fairy Ring        glowcaps in a perfect ring, and a chest in the middle nobody has dared to open
    the Hollow Oak        a tree older than the town, with roots like walls
    the Wolf Hollow       bones, and the pack that leaves them
    the Bandits' Camp     a fire, a pile of what they've taken, and the ones who took it
    the Stream            running water across the trail, and a plank bridge

The forest's creatures (deer that run, boar, wolves, bears, bandits) are as strong as Claude is (his level), roam
the wood, and never come into the clearing - the town is safe. Everything here is made from the save's seed."""
import math

import numpy as np

from . import dress

TREES = ["pine", "pine2", "common", "common2", "birch", "birch2", "willow", "common", "pine"]
UNDER = ["bush", "bush2", "bushberries", "plant1", "plant2", "plant3", "flowers", "grass", "grass2", "rock1",
         "stump_moss", "log_moss"]

GLADES = [
    ("the Mossy Pond", "Still water under the trees, green at the edges, and the frogs that live here watch you come "
                       "with the patience of things that have never had to hurry."),
    ("the Old Shrine", "Standing stones in a ring, older than the town, and an altar in the middle with fresh candles "
                       "on it. Nobody in Thornwick admits to lighting them."),
    ("the Woodcutter's Camp", "Smoke, sawdust and a kettle on a fire. Logs stacked higher than a man, and a man "
                              "beside them who looks as if he was cut from the same tree."),
    ("the Fairy Ring", "Glowcaps in a perfect circle, lit from inside, and the grass inside the ring greener than "
                       "the grass outside it. There is a chest in the middle. Nobody has dared."),
    ("the Hollow Oak", "A tree older than anything in Thornwick, its roots like walls and its trunk split wide enough "
                       "to walk into. Something has been keeping its treasures here."),
    ("the Wolf Hollow", "Bones in the bracken, picked clean, and the ground trodden flat. The pack is never far "
                        "from its hollow."),
    ("the Bandits' Camp", "A fire, a pile of what they've taken, and the ones who took it, looking up from their "
                          "supper. They have been expecting someone. Not you, but you'll do."),
    ("the Stream", "Running water across the way, cold from somewhere deep, and an old plank bridge over it."),
]


def grow(L, rng, cx, cy, clearing):
    """The wood round the clearing (L is the town; cx, cy its middle; clearing its open mask)."""
    S = L.w
    yy, xx = np.mgrid[0:S, 0:S]
    r = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
    ang = np.arctan2(yy + 0.5 - cy, xx + 0.5 - cx)
    edge = S / 2 - 4 + 2.5 * np.sin(ang * 7 + 0.4)
    L.solid[:] = r > edge                                  # (the wood's far edge: too thick to pass)
    L.safe = clearing.copy()                               # (the town: no creature comes in, and he mends here)
    grass, dirt, needles, moss = L.tex("ground.grass"), L.tex("ground.dirt"), L.tex("ground.needles"), L.tex("ground.moss")
    litter, planks = L.tex("ground.litter"), L.tex("ground.planks")
    stone = None
    wild = ~clearing & ~L.solid
    noise = np.sin(xx * 0.21 + 1.3) * np.cos(yy * 0.17 - 0.7) + np.sin((xx + yy) * 0.09)
    L.ftex[wild] = needles
    L.ftex[wild & (noise > 0.45)] = moss
    L.ftex[wild & (noise < -0.95)] = litter
    L.ftex[wild & (r < 30) & (noise > -0.2)] = grass
    keep = np.zeros_like(L.solid)                          # (squares the trees leave alone: the trails and glades)
    keep[clearing] = True
    # the glades, in a ring round the town
    glades = []
    base = rng.uniform(0, math.tau)
    for k, (name, line) in enumerate(GLADES):
        a = base + k / len(GLADES) * math.tau + rng.uniform(-0.2, 0.2)
        d = rng.uniform(42, S / 2 - 16)
        gx, gy = cx + math.cos(a) * d, cy + math.sin(a) * d
        rad = 6 if name != "the Stream" else 0
        glades.append((name, line, gx, gy, rad))
    # the trails: from the clearing's four ways, winding out to the glades; and a ring trail joining the glades
    def trail(x0, y0, x1, y1, width=1):
        x, y = x0, y0
        steps = 0
        while math.hypot(x1 - x, y1 - y) > 1.2 and steps < 900:
            steps += 1
            a = math.atan2(y1 - y, x1 - x) + rng.uniform(-0.55, 0.55)
            x += math.cos(a) * 0.7
            y += math.sin(a) * 0.7
            for dx in range(-width, width + 1):
                for dy in range(-width, width + 1):
                    qx, qy = int(x) + dx, int(y) + dy
                    if 0 <= qx < S and 0 <= qy < S and not L.solid[qy, qx]:
                        keep[qy, qx] = True
                        if abs(dx) + abs(dy) <= width and not clearing[qy, qx]:
                            L.ftex[qy, qx] = dirt
    ways = [(cx + 22, cy), (cx, cy + 22), (cx - 22, cy), (cx, cy - 22)]
    for k, (name, line, gx, gy, rad) in enumerate(glades):
        wx, wy = min(ways, key=lambda w: (w[0] - gx) ** 2 + (w[1] - gy) ** 2)
        trail(wx, wy, gx, gy)
        nxt = glades[(k + 1) % len(glades)]
        trail(gx, gy, nxt[2], nxt[3], 0)
    # each glade
    for name, line, gx, gy, rad in glades:
        if rad:
            m = np.hypot(xx + 0.5 - gx, yy + 0.5 - gy) < rad
            keep |= m
            L.ftex[m & ~L.solid] = grass
            L.pieces.append({"name": name, "line": line, "x0": int(gx - rad + 1), "y0": int(gy - rad + 1),
                             "x1": int(gx + rad - 1), "y1": int(gy + rad - 1)})
        _glade(L, rng, name, gx, gy, rad, xx, yy, stone, planks, keep, glades)
    # the trees: thick, but never so thick a man can't pass between them; then the undergrowth
    taken = {}
    for (y, x) in zip(*np.nonzero(wild & ~keep)):
        if rng.random() > (0.42 if r[y, x] > 28 else 0.25):
            continue
        tx, tz = x + rng.uniform(0.2, 0.8), y + rng.uniform(0.2, 0.8)
        if _crowded(taken, tx, tz):
            continue
        taken.setdefault((int(tx) // 3, int(tz) // 3), []).append((tx, tz))
        sc = rng.uniform(0.95, 1.55)
        L.props.append({"model": rng.choice(TREES), "x": tx, "z": tz, "yaw": rng.uniform(0, math.tau),
                        "scale": sc, "y": 0.0, "solid": True, "trunk": 0.16 * sc})
    for (y, x) in zip(*np.nonzero(wild)):
        if rng.random() < (0.05 if keep[y, x] else 0.1):
            L.props.append({"model": rng.choice(UNDER), "x": x + rng.uniform(0.2, 0.8), "z": y + rng.uniform(0.2, 0.8),
                            "yaw": rng.uniform(0, math.tau), "scale": rng.uniform(0.45, 0.8), "y": 0.0})
    # the creatures: in packs and herds through the wood, never near the town
    herds = [["Deer", "Deer", "Deer"], ["Boar", "Boar"], ["Wolf", "Wolf", "Wolf"], ["Bear"], ["Deer", "Deer"],
             ["Boar"], ["Sellsword", "Hedge Wizard"], ["Wolf", "Wolf"]]
    for _ in range(14):
        herd = rng.choice(herds)
        for _try in range(60):
            x, y = rng.randrange(S), rng.randrange(S)
            if wild[y, x] and r[y, x] > 32 and L.can_stand(x + 0.5, y + 0.5, 0.3, 0.0):
                for k, mname in enumerate(herd):
                    L.spawns.append({"monster": mname, "x": x + 0.5 + (k % 2) * 0.8, "z": y + 0.5 + (k // 2) * 0.8,
                                     "forest": True})
                break


def _crowded(taken, x, z):
    cx, cy = int(x) // 3, int(z) // 3
    for gx in (cx - 1, cx, cx + 1):
        for gy in (cy - 1, cy, cy + 1):
            for ox, oz in taken.get((gx, gy), ()):
                if (x - ox) ** 2 + (z - oz) ** 2 < 1.6 ** 2:
                    return True
    return False


def _sprite(L, x, z, name, w, h, glow=None, solid=0.0):
    L.sprites.append({"x": x, "z": z, "y": float(L.floor[int(z), int(x)]), "w": w, "h": h, "name": name, "glow": glow,
                      "solid": solid})
    if glow:
        L.lights.append((x, h * 0.7, z, *glow, 3.5))


def _glade(L, rng, name, gx, gy, rad, xx, yy, stone, planks, keep, glades):
    if name == "the Mossy Pond":
        pond = np.hypot(xx + 0.5 - gx, yy + 0.5 - gy) < 3.2
        for (y, x) in zip(*np.nonzero(pond & ~L.solid)):
            L.water.add((int(x), int(y)))
            L.floor[y, x] = -0.3
            if rng.random() < 0.35:
                L.props.append({"model": "lilypad", "x": x + rng.uniform(0.2, 0.8), "z": y + rng.uniform(0.2, 0.8),
                                "yaw": rng.uniform(0, math.tau), "scale": 0.5, "y": -0.06})
        for k in range(3):
            a = k * 2.1
            L.spawns.append({"monster": "Bog Frog", "x": gx + math.cos(a) * 4.3, "z": gy + math.sin(a) * 4.3, "forest": True})
        for k in range(10):
            a = k / 10 * math.tau
            L.props.append({"model": "grass2" if k % 2 else "plant3", "x": gx + math.cos(a) * 3.6, "z": gy + math.sin(a) * 3.6,
                            "yaw": a, "scale": 0.6, "y": 0.0})
    elif name == "the Old Shrine":
        for k in range(7):
            a = k / 7 * math.tau
            sx, sy = int(gx + math.cos(a) * 4), int(gy + math.sin(a) * 4)
            L.solid[sy, sx] = True
            L.props.append({"model": "rock2" if k % 2 else "rock1", "x": sx + 0.5, "z": sy + 0.5, "yaw": k * 2.3,
                            "scale": 1.9 + 0.35 * (k % 3), "y": 0.0})
        _sprite(L, gx + 0.5, gy + 0.5, "lm.altar", 1.1, 1.0, (1.0, 0.8, 0.5), 0.45)
        _sprite(L, gx + 1.5, gy + 0.5, "lm.candles", 0.6, 0.6, (1.0, 0.75, 0.4))
        dress.chest(L, int(gx), int(gy) + 1, rng, rich=1.5)
    elif name == "the Woodcutter's Camp":
        L.npcs.append({"vendor": "woodcutter", "x": gx - 1.2, "z": gy + 0.4, "yaw": 1.2})
        _sprite(L, gx + 0.5, gy + 0.5, "sp.fire", 0.8, 0.8, (1.0, 0.55, 0.2), 0.35)
        for k in range(6):
            a = k / 6 * math.tau + 0.3
            L.props.append({"model": rng.choice(["log", "log_moss", "stump", "stump"]), "x": gx + math.cos(a) * 3.5,
                            "z": gy + math.sin(a) * 3.5, "yaw": a, "scale": 0.7, "y": 0.0, "solid": True})
        L.props.append({"model": "crate", "x": gx + 2.4, "z": gy - 1.6, "yaw": 0.4, "scale": 0.45, "y": 0.0, "solid": True})
        L.props.append({"model": "barrel", "x": gx + 2.6, "z": gy - 0.6, "yaw": 0.0, "scale": 0.4, "y": 0.0, "solid": True})
    elif name == "the Fairy Ring":
        for k in range(14):
            a = k / 14 * math.tau
            _sprite(L, gx + math.cos(a) * 3.0, gy + math.sin(a) * 3.0, "clut.glowcap", 0.45, 0.4,
                    (0.5, 1.0, 0.6) if k % 3 == 0 else None)
        dress.chest(L, int(gx), int(gy), rng, rich=2.0)
    elif name == "the Hollow Oak":
        L.props.append({"model": "common", "x": gx + 0.5, "z": gy - 1.5, "yaw": 0.3, "scale": 4.2, "y": 0.0,
                        "solid": True, "trunk": 0.9})
        for k in range(4):
            _sprite(L, gx - 1.5 + k, gy + 0.6, "lm.root", 0.9, 0.7)
        dress.chest(L, int(gx) + 2, int(gy) + 2, rng, guard=["Bear"], rich=1.8)
    elif name == "the Wolf Hollow":
        for k in range(5):
            _sprite(L, gx + rng.uniform(-3, 3), gy + rng.uniform(-3, 3), "bones", 0.7, 0.4)
        for k in range(4):
            L.spawns.append({"monster": "Wolf", "x": gx + math.cos(k * 1.6) * 2, "z": gy + math.sin(k * 1.6) * 2, "forest": True})
    elif name == "the Bandits' Camp":
        _sprite(L, gx + 0.5, gy + 0.5, "sp.fire", 0.8, 0.8, (1.0, 0.55, 0.2), 0.35)
        for k, m in enumerate(["Sellsword", "Sellsword", "Hedge Wizard", "Sellsword"]):
            a = k / 4 * math.tau
            L.spawns.append({"monster": m, "x": gx + math.cos(a) * 2.2, "z": gy + math.sin(a) * 2.2, "forest": True})
        for k in range(3):
            L.props.append({"model": rng.choice(["crate", "barrel"]), "x": gx + 3.5, "z": gy - 1 + k, "yaw": 0.0,
                            "scale": 0.42, "y": 0.0, "solid": True})
        dress.chest(L, int(gx) - 3, int(gy), rng, rich=2.2)
    elif name == "the Stream":
        # a stream running across the wood near here, a plank bridge where a trail crosses it
        a = rng.uniform(0, math.pi)
        dx, dy = math.cos(a), math.sin(a)
        for t in np.arange(-26, 26, 0.5):
            x = gx + dx * t + math.sin(t * 0.3) * 2.0 * -dy
            y = gy + dy * t + math.sin(t * 0.3) * 2.0 * dx
            for w in (-0.6, 0.0, 0.6):
                qx, qy = int(x - dy * w), int(y + dx * w)
                if 0 <= qx < L.w and 0 <= qy < L.h and not L.solid[qy, qx] and not L.safe[qy, qx]:
                    if keep[qy, qx] and L.ftex[qy, qx] == L.tex("ground.dirt"):
                        L.ftex[qy, qx] = planks                   # (the bridge)
                        L.floor[qy, qx] = 0.06
                    elif (qx, qy) not in L.water:
                        L.water.add((qx, qy))
                        L.floor[qy, qx] = -0.3
        L.pieces.append({"name": name, "line": GLADES[-1][1], "x0": int(gx) - 2, "y0": int(gy) - 2,
                         "x1": int(gx) + 2, "y1": int(gy) + 2})
