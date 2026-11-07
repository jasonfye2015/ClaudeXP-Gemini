"""The lantern in Claude's hand: an old iron lantern with a brass foot - four posts, a cap, a ring to hold it by - held
up at the lower right of his view, swinging a little as he walks, jolted about when he shakes it. Its flame is the
light (the renderer puts its light where the flame is).

    local = parts()                         the lantern's triangles, about its foot: [(position, normal, colour)]
    origin, axes = hold(night, now)         where it hangs this frame, and its axes (right, up, forward)
    flame(origin, axes)                     the flame's place
"""
import math

import numpy as np

IRON = (0.07, 0.062, 0.055)
BRASS = (0.24, 0.17, 0.08)
H = 0.15                           # (its height, foot to cap)


def _box(out, x0, y0, z0, x1, y1, z1, col):
    p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = (((0, 1, 2, 3), (0, 0, -1)), ((5, 4, 7, 6), (0, 0, 1)), ((4, 0, 3, 7), (-1, 0, 0)), ((1, 5, 6, 2), (1, 0, 0)),
             ((3, 2, 6, 7), (0, 1, 0)), ((4, 5, 1, 0), (0, -1, 0)))
    for idx, n in faces:
        for i in (0, 1, 2, 0, 2, 3):
            out.append((p[idx[i]], n, col))


def parts():
    out = []
    w = 0.042
    _box(out, -w, 0.0, -w, w, 0.014, w, BRASS)                              # (the foot)
    for sx in (-1, 1):                                                       # (the four posts)
        for sz in (-1, 1):
            _box(out, sx * w - 0.005, 0.014, sz * w - 0.005, sx * w + 0.005, H - 0.03, sz * w + 0.005, IRON)
    _box(out, -w - 0.004, H - 0.032, -w - 0.004, w + 0.004, H - 0.02, w + 0.004, IRON)     # (the cap's rim)
    tip = (0.0, H + 0.012, 0.0)                                              # (the cap: a low pyramid)
    corners = [(-w, H - 0.02, -w), (w, H - 0.02, -w), (w, H - 0.02, w), (-w, H - 0.02, w)]
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        n = np.cross(np.subtract(b, a), np.subtract(tip, a))
        n = tuple(n / (np.linalg.norm(n) or 1))
        out += [(a, n, BRASS), (b, n, BRASS), (tip, n, BRASS)]
    for k in range(10):                                                      # (the ring it hangs by)
        a0, a1 = k / 10 * math.pi, (k + 1) / 10 * math.pi
        for (u0, u1) in ((a0, a1),):
            p0 = (math.cos(u0) * 0.03, H + 0.012 + math.sin(u0) * 0.035, 0.0)
            p1 = (math.cos(u1) * 0.03, H + 0.012 + math.sin(u1) * 0.035, 0.0)
            _box(out, min(p0[0], p1[0]) - 0.003, min(p0[1], p1[1]) - 0.003, -0.003,
                 max(p0[0], p1[0]) + 0.003, max(p0[1], p1[1]) + 0.003, 0.003, IRON)
    return out


def hold(night, now):
    """Where the lantern hangs: low at the right of his view, a little ahead; it bobs and swings with his steps, and
    a shake throws it about. -> (origin, (right, up, forward))"""
    yaw, pitch = night.yaw, night.pitch
    fwd_v = np.array((math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch)))
    right = np.array((math.cos(yaw), 0.0, math.sin(yaw)))
    up_v = np.cross(right, fwd_v)
    eye = np.array(night.eye)
    step = night.moved
    origin = eye + right * 0.21 - up_v * 0.22 + fwd_v * 0.42
    origin = origin + up_v * (0.012 * abs(math.sin(step * 2.8))) + right * (0.008 * math.sin(step * 1.4))
    sh = night.lamp.shaking
    swing = 0.07 * math.sin(step * 1.4) + 0.025 * math.sin(now * 0.9)
    if sh > 0:
        jolt = (1 - sh) * math.sin(sh * math.pi * 7)
        origin = origin + right * 0.035 * jolt + up_v * 0.02 * math.sin(sh * math.pi * 9) * (1 - sh)
        swing += 0.45 * jolt
    flat_fwd = np.array((math.sin(yaw), 0.0, -math.cos(yaw)))
    up = np.array((0.0, 1.0, 0.0)) * math.cos(swing) + right * math.sin(swing)        # (swinging about his line of sight)
    r = right * math.cos(swing) - np.array((0.0, 1.0, 0.0)) * math.sin(swing)
    return origin, (r, up, flat_fwd)


def place(local, origin, axes):
    """The lantern's triangles where it hangs: -> float32 (n, 9)."""
    r, u, f = axes
    M = np.stack([r, u, f], axis=1)
    pts = np.array([p for p, _n, _c in local], np.float64)
    nrm = np.array([n for _p, n, _c in local], np.float64)
    col = np.array([c for _p, _n, c in local], np.float64)
    world = pts @ M.T + origin
    wn = nrm @ M.T
    return np.hstack([world, wn, col]).astype(np.float32)


def flame(origin, axes):
    return origin + axes[1] * (H * 0.45)
