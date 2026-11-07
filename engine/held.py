"""What Claude holds up before him: his crooked wand, and hung from its crook his old lantern - iron posts, a brass foot
and cap, a ring - swinging under it like a pendulum as he walks, thrown about when he shakes it. Its flame is the
light (the renderer puts its light where the flame is).

The wand is KayKit's (Kay Lousberg, CC0, the Adventurers pack): its shape kept in assets/wand.npz and its colours in
assets/wand.png, copied out once by tools/export_wand.py, so this game needs nothing of any other.

    parts()                      the lantern's triangles, about its ring: [(position, normal, colour)]
    wand_parts()                 the wand's, about its grip
    hold(night, now)             -> (the wand's grip, its axes), (the lantern's ring, its axes) this frame
    place(local, origin, axes)   -> float32 (n, 9) where they are
    flame(origin, axes)          the flame's place
"""
import math
from pathlib import Path

import numpy as np

IRON = (0.07, 0.062, 0.055)
BRASS = (0.24, 0.17, 0.08)
H = 0.15                           # (the lantern's height, foot to cap)
HANG = H + 0.045                   # (from the crook to its foot)
ASSETS = Path(__file__).resolve().parents[1] / "assets"
WAND_LEN = 0.5                     # (the wand as he holds it, grip to crook)


def _box(out, x0, y0, z0, x1, y1, z1, col):
    p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = (((0, 1, 2, 3), (0, 0, -1)), ((5, 4, 7, 6), (0, 0, 1)), ((4, 0, 3, 7), (-1, 0, 0)), ((1, 5, 6, 2), (1, 0, 0)),
             ((3, 2, 6, 7), (0, 1, 0)), ((4, 5, 1, 0), (0, -1, 0)))
    for idx, n in faces:
        for i in (0, 1, 2, 0, 2, 3):
            out.append((p[idx[i]], n, col))


def parts():
    """The lantern, hanging: its ring at the origin, its foot HANG below."""
    out = []
    w = 0.042
    y0 = -HANG
    _box(out, -w, y0, -w, w, y0 + 0.014, w, BRASS)                              # (the foot)
    for sx in (-1, 1):                                                           # (the four posts)
        for sz in (-1, 1):
            _box(out, sx * w - 0.005, y0 + 0.014, sz * w - 0.005, sx * w + 0.005, y0 + H - 0.03, sz * w + 0.005, IRON)
    _box(out, -w - 0.004, y0 + H - 0.032, -w - 0.004, w + 0.004, y0 + H - 0.02, w + 0.004, IRON)     # (the cap's rim)
    tip = (0.0, y0 + H + 0.012, 0.0)                                             # (the cap: a low pyramid)
    corners = [(-w, y0 + H - 0.02, -w), (w, y0 + H - 0.02, -w), (w, y0 + H - 0.02, w), (-w, y0 + H - 0.02, w)]
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        n = np.cross(np.subtract(b, a), np.subtract(tip, a))
        n = tuple(n / (np.linalg.norm(n) or 1))
        out += [(a, n, BRASS), (b, n, BRASS), (tip, n, BRASS)]
    for k in range(10):                                                          # (the ring it hangs by)
        a0, a1 = k / 10 * math.pi, (k + 1) / 10 * math.pi
        p0 = (math.cos(a0) * 0.022, y0 + H + 0.012 + math.sin(a0) * 0.03, 0.0)
        p1 = (math.cos(a1) * 0.022, y0 + H + 0.012 + math.sin(a1) * 0.03, 0.0)
        _box(out, min(p0[0], p1[0]) - 0.003, min(p0[1], p1[1]) - 0.003, -0.003,
             max(p0[0], p1[0]) + 0.003, max(p0[1], p1[1]) + 0.003, 0.003, IRON)
    return out


_wand = {}


def wand_parts():
    """The crooked wand: about its grip, along +z to the crook (which bends toward -x), scaled to WAND_LEN.
    -> ([(position, normal, colour)], the crook's end)"""
    if "parts" in _wand:
        return _wand["parts"], _wand["tip"]
    from PIL import Image
    d = np.load(ASSETS / "wand.npz")
    v, uv, idx = d["positions"], d["uv"], d["indices"].reshape(-1, 3)
    tex = Image.open(ASSETS / "wand.png").convert("RGB")
    lo_z, hi_z = float(v[:, 2].min()), float(v[:, 2].max())
    grip = np.array((v[:, 0].mean(), v[:, 1].mean(), lo_z + 0.12 * (hi_z - lo_z)), np.float32)
    s = WAND_LEN / (hi_z - lo_z)
    local = (v - grip) * s
    tip = local[int(np.argmax(v[:, 2]))]
    out = []
    for tri in idx:
        p = [local[i] for i in tri]
        n = np.cross(p[1] - p[0], p[2] - p[0])
        n = n / (np.linalg.norm(n) or 1)
        u = uv[tri].mean(0)
        c = tex.getpixel((int(u[0] * (tex.width - 1)), int(u[1] * (tex.height - 1))))
        col = tuple(ch / 255 * 0.42 for ch in c)                             # (darkened: old wood, old cord)
        for q in p:
            out.append((tuple(q), tuple(n), col))
    _wand["parts"], _wand["tip"] = out, tip
    return out, tip


def _basis(z, down):
    """Axes with +z along z and -x as near as can be to `down`: -> (x, y, z) unit vectors."""
    z = z / np.linalg.norm(z)
    dp = down - z * float(np.dot(down, z))
    dp = dp / (np.linalg.norm(dp) or 1)
    x = -dp
    y = np.cross(z, x)
    return x, y, z


def hold(night, now):
    """The wand held out from low at the right, rising forward with its crook turned down; the lantern hung from the
    crook, swinging about it as he walks, thrown about when he shakes it.
    -> ((grip, wand axes), (ring, lantern axes))"""
    yaw, pitch = night.yaw, night.pitch
    fwd_v = np.array((math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch)))
    right = np.array((math.cos(yaw), 0.0, math.sin(yaw)))
    up_v = np.cross(right, fwd_v)
    world_up = np.array((0.0, 1.0, 0.0))
    eye = np.array(night.eye)
    step = night.moved
    sh = night.lamp.shaking
    jolt = (1 - sh) * math.sin(sh * math.pi * 7) if sh > 0 else 0.0
    grip = eye + right * 0.24 - up_v * 0.3 + fwd_v * 0.22
    grip = grip + up_v * (0.01 * abs(math.sin(step * 2.8))) + right * (0.006 * math.sin(step * 1.4)) + up_v * 0.03 * jolt
    along = fwd_v * 0.8 + up_v * 0.45 - right * 0.32 + right * 0.08 * jolt
    wx, wy, wz = _basis(along, -up_v)
    _parts, tip = wand_parts()
    crook = grip + wx * tip[0] + wy * tip[1] + wz * tip[2]
    # the lantern: a pendulum from the crook - swung across his view and fore and aft by his steps, flung by a shake
    side = 0.08 * math.sin(step * 1.4) + 0.03 * math.sin(now * 0.8) + 0.55 * jolt - 0.45 * getattr(night, "sway", 0.0)
    fore = 0.05 * math.sin(step * 2.8 + 0.6) + 0.15 * jolt * math.sin(sh * 11)
    flat_r = right
    flat_f = np.array((math.sin(yaw), 0.0, -math.cos(yaw)))
    up = world_up * math.cos(side) * math.cos(fore) + flat_r * math.sin(side) + flat_f * math.sin(fore)
    up = up / np.linalg.norm(up)
    r = flat_r - up * float(np.dot(flat_r, up))
    r = r / np.linalg.norm(r)
    f = np.cross(r, up)
    return (grip, (wx, wy, wz)), (crook, (r, up, -f))


def place(local, origin, axes):
    """Triangles where they hang: -> float32 (n, 9)."""
    a, b, c = axes
    M = np.stack([a, b, c], axis=1)
    pts = np.array([p for p, _n, _c in local], np.float64)
    nrm = np.array([n for _p, n, _c in local], np.float64)
    col = np.array([c_ for _p, _n, c_ in local], np.float64)
    return np.hstack([pts @ M.T + origin, nrm @ M.T, col]).astype(np.float32)


def flame(origin, axes):
    return origin + axes[1] * (-HANG + H * 0.45)
