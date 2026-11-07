"""The weather you can see falling (Claude and Magic's air: rain, snow, leaves on the wind, a twister's dust) and,
below, what comes down the shaft (its below: drips from the ceilings, water through the grates) - built each frame
as soft billboards, from the time and fixed hashes, so nothing has to be remembered from frame to frame.
Vertex: as the glow program's - position 3, uv 2, colour 4, mode 1 (5 a flake, 6 a streak)."""
import math

import numpy as np

_H = None


def _hashes(n):
    global _H
    if _H is None or len(_H) < n:
        rng = np.random.default_rng(1234)
        _H = rng.random((max(n, 4096), 4)).astype(np.float32)
    return _H[:n]


def _quads(P, right, up, w, h, col, mode):
    """P (n,3) centres; right/up (3,) or (n,3); w, h scalars or (n,); col (4,) or (n,4) -> (n*6, 10)"""
    n = len(P)
    if not n:
        return np.zeros((0, 10), np.float32)
    w = np.broadcast_to(np.asarray(w, np.float32), (n,))[:, None]
    h = np.broadcast_to(np.asarray(h, np.float32), (n,))[:, None]
    R = np.broadcast_to(np.asarray(right, np.float32), (n, 3)) * w
    U = np.broadcast_to(np.asarray(up, np.float32), (n, 3)) * h
    C = np.broadcast_to(np.asarray(col, np.float32), (n, 4))
    corners = [(-1, -1, 0, 0), (1, -1, 1, 0), (1, 1, 1, 1), (-1, -1, 0, 0), (1, 1, 1, 1), (-1, 1, 0, 1)]
    out = np.zeros((n, 6, 10), np.float32)
    for k, (sx, sy, u, v) in enumerate(corners):
        out[:, k, 0:3] = P + R * sx + U * sy
        out[:, k, 3] = u
        out[:, k, 4] = v
        out[:, k, 5:9] = C
        out[:, k, 9] = mode
    return out.reshape(-1, 10)


def _box(eye, H, R):
    """Particles anchored in the world, wrapped into a box of half-width R round the eye."""
    ex, _ey, ez = eye
    x = (H[:, 0] * 2 * R - ex) % (2 * R) + ex - R
    z = (H[:, 1] * 2 * R - ez) % (2 * R) + ez - R
    return x, z


def surface(atm, eye, right, now, twister=None, ground=0.0):
    out = []
    ex, ey, ez = eye
    sp, (wx, wz) = atm["wind"]
    if atm["rain"] > 0.02:
        n = int(700 * atm["rain"])
        H = _hashes(n)
        x, z = _box(eye, H, 13.0)
        top, span = ey + 7.0, 10.0
        fall = (now * 15.0 + H[:, 2] * span) % span
        y = top - fall
        slant = 0.25 + sp * 0.9
        x = x + wx * slant * fall
        z = z + wz * slant * fall
        keep = y > ground
        P = np.stack([x, y, z], 1)[keep]
        up = np.array([wx * slant * 0.3, 1.0, wz * slant * 0.3], np.float32)
        up /= np.linalg.norm(up)
        a = 0.28 + 0.2 * atm["storm"]
        out.append(_quads(P, right, up, 0.012, 0.32, (0.72, 0.76, 0.84, a), 6.0))
    if atm["snowfall"] > 0.02:
        n = int(700 * atm["snowfall"])
        H = _hashes(n)
        x, z = _box(eye, H, 12.0)
        span = 8.0
        fall = (now * (0.9 + H[:, 3] * 0.6) + H[:, 2] * span) % span
        y = ey + 5.0 - fall
        x = x + np.sin(now * 1.3 + H[:, 3] * 9) * 0.35 + wx * sp * fall * 0.6
        z = z + np.cos(now * 1.1 + H[:, 2] * 7) * 0.35 + wz * sp * fall * 0.6
        keep = y > ground
        P = np.stack([x, y, z], 1)[keep]
        out.append(_quads(P, right, (0, 1, 0), 0.035, 0.035, (0.95, 0.96, 1.0, 0.9), 5.0))
    if atm["leaves"] > 0.05:
        n = int(90 * atm["leaves"])
        H = _hashes(n)
        span = 26.0
        d = (now * (3.0 + sp * 4) + H[:, 0] * span) % span - span / 2
        side = (H[:, 1] - 0.5) * 22
        x = ex + wx * d - wz * side
        z = ez + wz * d + wx * side
        y = ground + 0.2 + H[:, 2] * 3.0 + np.sin(now * 3 + H[:, 3] * 20) * 0.3
        col = np.stack([0.55 + H[:, 3] * 0.3, 0.32 + H[:, 2] * 0.2, 0.1 + 0 * H[:, 0], np.full(n, 0.9)], 1)
        out.append(_quads(np.stack([x, y, z], 1), right, (0, 1, 0), 0.05, 0.035, col, 5.0))
    if twister:
        tx, tz, k = twister
        n = int(360 * max(0.3, k))
        H = _hashes(n)
        t = H[:, 0]
        r = 0.35 + t * t * 3.2
        a = now * (5.0 - t * 2) + H[:, 1] * math.tau
        x = tx + np.cos(a) * r
        z = tz + np.sin(a) * r
        y = ground + t * 11.0
        col = np.stack([0.2 + H[:, 2] * 0.08, 0.19 + H[:, 2] * 0.06, 0.16 + 0 * t, 0.16 + 0.16 * (1 - t)], 1)
        out.append(_quads(np.stack([x, y, z], 1), right, (0, 1, 0), 0.3 + t * 0.4, 0.3 + t * 0.4, col, 5.0))
    return np.concatenate(out) if out else np.zeros((0, 10), np.float32)


def below(L, above, k_below, eye, right, now, cells):
    """What reaches down the shaft on the first floors: drips from the ceilings in rain, water through the grates in
    a storm."""
    out = []
    kind, s = above["kind"], above["strength"]
    ex, ey, ez = eye
    if kind in ("rain", "storm") and s > 0.05 and k_below > 0 and len(cells):
        near = cells[(np.abs(cells[:, 0] - ex) < 12) & (np.abs(cells[:, 1] - ez) < 12)]
        n = min(len(near), int(45 * s * k_below))
        if n:
            H = _hashes(len(near))
            pick = near[np.argsort(H[:, 0])[:n]]
            hh = H[:n]
            ph = (now * (0.7 + hh[:, 1] * 0.5) + hh[:, 2]) % 1.0
            top, flo = pick[:, 3], pick[:, 2]
            y = top - (top - flo) * ph * ph
            P = np.stack([pick[:, 0] + hh[:, 3] * 0.8 - 0.4, y, pick[:, 1] + hh[:, 0] * 0.8 - 0.4], 1)
            out.append(_quads(P, right, (0, 1, 0), 0.012, 0.09, (0.65, 0.75, 0.9, 0.7), 6.0))
    if kind == "storm" and s > 0.2 and k_below > 0:
        grates = [d for d in L.decals if d[7] in ("clut.grate", "clut.port") and abs(d[0] - ex) < 14 and abs(d[2] - ez) < 14]
        for (gx, gy, gz, nx, nz, w, h, _name) in grates[:12]:
            m = 14
            t = ((now * 1.4 + np.arange(m) / m) % 1.0) * 0.55
            dist = t * 2.2 * s
            P = np.stack([gx + nx * dist + (np.arange(m) % 3 - 1) * 0.08 * -nz, gy + h * 0.55 - 4.9 * t * t,
                          gz + nz * dist + (np.arange(m) % 3 - 1) * 0.08 * nx], 1)
            P[:, 1] = np.maximum(P[:, 1], gy + 0.02)
            out.append(_quads(P, right, (0, 1, 0), 0.05, 0.1, (0.6, 0.72, 0.85, 0.55 * k_below), 6.0))
    return np.concatenate(out) if out else np.zeros((0, 10), np.float32)


def ceiling_cells(L):
    """(n, 4): x, z, floor, ceiling for every open square (where a drip can fall)."""
    sq = L.open_squares()
    if not sq:
        return np.zeros((0, 4), np.float32)
    a = np.array(sq, np.int32)
    return np.stack([a[:, 0] + 0.5, a[:, 1] + 0.5, L.floor[a[:, 1], a[:, 0]], L.ceil[a[:, 1], a[:, 0]]], 1).astype(np.float32)
