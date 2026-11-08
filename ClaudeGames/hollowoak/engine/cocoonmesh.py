"""Her guests, made: each a man's length wrapped round and round in silk (the bands of it winding up him), hung from the
wall by a few threads, leaning back against it - and beneath him, what he brought: a broken lute, a sword, picks, a
book, prayer beads, arrows tipped for fire.

    build(cocoons)    -> (float32 (n, 9) triangles: position, normal, colour;  [threads] for the silk)
"""
import math

import numpy as np

SILK = (0.5, 0.49, 0.46)
BAND = (0.38, 0.37, 0.35)


def _v(a):
    return np.asarray(a, np.float64)


def _unit(v):
    v = _v(v)
    return v / (np.linalg.norm(v) or 1.0)


def _box(out, c, size, axes, col):
    """A box at c, half-sizes `size` along `axes` (three unit vectors)."""
    c = _v(c)
    ax = [_v(a) * s for a, s in zip(axes, size)]
    corner = lambda i, j, k: c + ax[0] * i + ax[1] * j + ax[2] * k      # noqa: E731
    faces = (((1, 0, 0), [(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)]),
             ((-1, 0, 0), [(-1, -1, 1), (-1, 1, 1), (-1, 1, -1), (-1, -1, -1)]),
             ((0, 1, 0), [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)]),
             ((0, -1, 0), [(-1, -1, 1), (-1, -1, -1), (1, -1, -1), (1, -1, 1)]),
             ((0, 0, 1), [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]),
             ((0, 0, -1), [(1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1)]))
    for n, quad in faces:
        nw = _unit(sum(_v(a) * k for a, k in zip(axes, n)))
        pts = [corner(*q) for q in quad]
        for i in (0, 1, 2, 0, 2, 3):
            out.append((*pts[i], *nw, *col))


def _blob(out, c, radii, axes, col, seg=10):
    """An ellipsoid: a lute's belly, a bead."""
    c = _v(c)
    ax = [_v(a) for a in axes]
    rings = []
    for i in range(seg + 1):
        th = math.pi * i / seg
        ring = []
        for j in range(seg * 2 + 1):
            ph = math.tau * j / (seg * 2)
            d = (math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph))
            p = c + ax[0] * d[0] * radii[0] + ax[1] * d[1] * radii[1] + ax[2] * d[2] * radii[2]
            n = _unit(ax[0] * d[0] / radii[0] + ax[1] * d[1] / radii[1] + ax[2] * d[2] / radii[2])
            ring.append((p, n))
        rings.append(ring)
    for i in range(seg):
        for j in range(seg * 2):
            a, b, cc, d = rings[i][j], rings[i + 1][j], rings[i + 1][j + 1], rings[i][j + 1]
            for p, n in (a, b, cc, a, cc, d):
                out.append((*p, *n, *col))


def _wrapped(out, s):
    """The man, wrapped: a body's outline, banded round and round with silk."""
    x, y, z = s["pos"]
    a = s["angle"]
    wall = _v((math.cos(a), 0.0, math.sin(a)))
    up = _unit(_v((0.0, 1.0, 0.0)) * math.cos(s["lean"]) + wall * math.sin(s["lean"]))
    side = _unit(np.cross(up, wall))
    front = _unit(np.cross(side, up))
    mid = _v((x, y, z))
    length = 0.85
    steps, around = 26, 18
    rings = []
    for i in range(steps + 1):
        u = i / steps
        body = 0.1 + 0.07 * math.sin(math.pi * min(1.0, u * 1.15)) ** 0.7     # (feet narrow, shoulders broad)
        if u > 0.82:
            body *= 0.78 + 0.22 * math.cos((u - 0.82) / 0.18 * math.pi / 2)   # (the head)
        if u < 0.04 or u > 0.98:
            body *= 0.55
        ring = []
        for j in range(around + 1):
            ph = math.tau * j / around
            band = 1.0 + 0.07 * math.sin(u * 46.0 + ph * 1.0 + s["angle"] * 3)  # (the silk, wound round and up)
            r = body * band
            d = side * math.cos(ph) * 1.15 + front * math.sin(ph) * 0.85
            p = mid + up * (u - 0.5) * length + d * r
            col = BAND if math.sin(u * 46.0 + ph + s["angle"] * 3) > 0.55 else SILK
            ring.append((p, _unit(d), col))
        rings.append(ring)
    for i in range(steps):
        for j in range(around):
            a0, b0, c0, d0 = rings[i][j], rings[i + 1][j], rings[i + 1][j + 1], rings[i][j + 1]
            for p, n, col in (a0, b0, c0, a0, c0, d0):
                out.append((*p, *n, *col))
    return mid, up, front


def _keepsake(out, s, front):
    kind = s["keepsake"]
    if kind is None:
        return
    a = s["angle"]
    base = _v((s["pos"][0], s["floor"] + 0.02, s["pos"][2])) - _v((math.cos(a), 0, math.sin(a))) * 0.42
    f = _unit(_v((-math.sin(a), 0.0, math.cos(a))))
    up = _v((0, 1, 0))
    r = _unit(np.cross(up, f))
    if kind == "lute":                                     # (its belly cracked, its neck snapped off beside it)
        _blob(out, base + up * 0.03, (0.13, 0.035, 0.1), (f, up, r), (0.42, 0.25, 0.12))
        _box(out, base + f * 0.22 + r * 0.05 + up * 0.02, (0.11, 0.012, 0.02), (_unit(f + r * 0.4), up, r), (0.3, 0.18, 0.08))
    elif kind == "sword":
        _box(out, base + up * 0.012, (0.32, 0.005, 0.022), (f, up, r), (0.55, 0.56, 0.6))
        _box(out, base - f * 0.33 + up * 0.015, (0.015, 0.012, 0.08), (f, up, r), (0.4, 0.32, 0.15))
        _box(out, base - f * 0.41 + up * 0.015, (0.07, 0.014, 0.016), (f, up, r), (0.28, 0.16, 0.08))
    elif kind == "picks":
        for k in range(4):
            d = _unit(f * math.cos(k * 0.5) + r * math.sin(k * 0.5))
            _box(out, base + d * 0.05 + up * 0.006, (0.07, 0.004, 0.005), (d, up, _unit(np.cross(up, d))), (0.45, 0.45, 0.48))
    elif kind == "book":
        _box(out, base + up * 0.025, (0.11, 0.025, 0.14), (f, up, r), (0.35, 0.08, 0.06))
        _box(out, base + up * 0.025 + r * 0.004, (0.104, 0.021, 0.137), (f, up, r), (0.72, 0.66, 0.52))
    elif kind == "beads":
        for k in range(14):
            t = k / 14 * math.tau
            _blob(out, base + f * math.cos(t) * 0.09 + r * math.sin(t) * 0.06 + up * 0.012, (0.012, 0.012, 0.012),
                  (f, up, r), (0.6, 0.48, 0.3), seg=4)
    elif kind == "arrows":
        for k in range(5):
            d = _unit(f * math.cos(k * 0.18 - 0.36) + r * math.sin(k * 0.18 - 0.36))
            c = base + r * (k - 2) * 0.03 + up * 0.008
            _box(out, c, (0.3, 0.005, 0.005), (d, up, _unit(np.cross(up, d))), (0.5, 0.36, 0.2))
            _box(out, c + d * 0.31, (0.025, 0.012, 0.012), (d, up, _unit(np.cross(up, d))), (0.75, 0.3, 0.08))


def build(cocoons):
    out, threads = [], []
    for s in cocoons.spots:
        mid, up, front = _wrapped(out, s)
        _keepsake(out, s, front)
        head = mid + up * 0.44
        threads.append(([tuple(head), tuple(s["top"])], 0.006, 6, [0.0, 0.0], 0.0))      # (hung from the wall)
        for k, dy in enumerate((0.0, -0.35)):
            side = np.cross(up, front) * (0.12 if k else -0.12)
            anchor = _v(s["top"]) + side * 3 + _v((0, dy - 0.8, 0))
            threads.append(([tuple(mid + up * (0.25 - k * 0.3) + side), tuple(anchor)], 0.004, 6, [0.0, 0.0], 0.0))
    return np.array(out, np.float32), threads
