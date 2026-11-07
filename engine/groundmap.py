"""The ground's map, for the ground to blend as Claude and Magic's does (its 76zzzzzzzzzz0-groundblend, 26c-wear,
26d-forestfloor and 40-render's uGBlend): one texel a square -
    R  cover: walls, houses, standing stones 255 (leaves drift at them); the trees' trunks 128 (dappled light)
    G  water
    B  the ground drawn there: its layer in the texture array + 1 (0: no ground - a wall)
    A  wear: how trodden (the grass worn to earth along the ways people walk)
Outdoors only. The forest floor is the picture only: grass under close trees is drawn as leaf litter (needles among
the pines' thick stands), and at the trees' edge as moss - the square's own ground is as it was.

    build(L, layer_of) -> uint8 array (H, W, 4)"""
from collections import deque

import numpy as np

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _trees(L):
    """Where the solid trees stand: {(x, y)}."""
    out = set()
    for p in L.props:
        if p.get("solid") and p.get("trunk"):
            out.add((int(p["x"]), int(p["z"])))
    return out


def forest_floor(L, trees):
    """A grass square's picture by the trees about it (within two squares; the four beside count double)."""
    out = {}
    if not trees or "ground.grass" not in L.textures:
        return out
    T = np.zeros((L.h + 4, L.w + 4), np.float32)
    for x, y in trees:
        if 0 <= x < L.w and 0 <= y < L.h:
            T[y + 2, x + 2] = 1
    n = np.zeros((L.h, L.w), np.float32)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx or dy:
                n += T[2 + dy:2 + dy + L.h, 2 + dx:2 + dx + L.w] * (2 if abs(dx) + abs(dy) <= 1 else 1)
    grass = (L.ftex == L.textures.index("ground.grass")) & ~L.solid
    for y, x in zip(*np.nonzero(grass & (n >= 9))):
        out[(int(x), int(y))] = "ground.litter"
    for y, x in zip(*np.nonzero(grass & (n >= 5) & (n < 9))):
        out[(int(x), int(y))] = "ground.moss"
    return out


def _way(L, a, b):
    """The shortest walk between two open squares, as a list of squares (none if there's no way)."""
    prev = {a: None}
    q = deque([a])
    while q:
        c = q.popleft()
        if c == b:
            break
        for dx, dy in DIRS:
            n = (c[0] + dx, c[1] + dy)
            if n in prev or not (0 <= n[0] < L.w and 0 <= n[1] < L.h) or L.solid[n[1], n[0]]:
                continue
            prev[n] = c
            q.append(n)
    if b not in prev:
        return []
    out, c = [], b
    while c is not None:
        out.append(c)
        c = prev[c]
    return out


def wear(L):
    """How trodden each square is (0..1): the places people go - the vendors, the Deep's mouth, the cabin's door, the
    farm's sign, the forest's ways out - most, and the shortest ways between them, spreading a little aside."""
    W = np.zeros((L.h, L.w), np.float32)
    spots = [(int(n["x"]), int(n["z"])) for n in L.npcs]
    if L.portal:
        spots.append((int(L.portal[0]) + 3, int(L.portal[1])))
    spots += [(int(x), int(z)) for x, z in L.spots.values()]
    spots = [s for s in spots if 0 <= s[0] < L.w and 0 <= s[1] < L.h and not L.solid[s[1], s[0]]]
    if L.start:
        spots.append((int(L.start[0]), int(L.start[1])))

    def add(x, y, v):
        if 0 <= x < L.w and 0 <= y < L.h and not L.solid[y, x]:
            W[y, x] = min(1.0, W[y, x] + v)
    for x, y in spots:
        add(x, y, 0.9)
        for dx, dy in DIRS:
            add(x + dx, y + dy, 0.35)
    for i in range(len(spots)):
        for x, y in _way(L, spots[i], spots[(i + 1) % len(spots)]):
            add(x, y, 0.3)
            for dx, dy in DIRS:
                add(x + dx, y + dy, 0.08)
    return W


def build(L, layer_of):
    M = np.zeros((L.h, L.w, 4), np.uint8)
    trees = _trees(L)
    M[..., 0] = np.where(L.solid, 255, 0)
    for x, y in trees:                                     # (a trunk: half - dappled light, but no drifts of leaves)
        if 0 <= x < L.w and 0 <= y < L.h and not L.solid[y, x]:
            M[y, x, 0] = 128
    for x, y in getattr(L, "water", ()):
        if 0 <= x < L.w and 0 <= y < L.h:
            M[y, x, 1] = 255
    lay = np.vectorize(lambda i: layer_of(i) + 1, otypes=[np.int32])(L.ftex)
    M[..., 2] = np.where(L.solid, 0, np.clip(lay, 0, 255))
    for (x, y), name in forest_floor(L, trees).items():
        M[y, x, 2] = layer_of(L.tex(name)) + 1
    M[..., 3] = (wear(L) * 255).astype(np.uint8)
    return M
