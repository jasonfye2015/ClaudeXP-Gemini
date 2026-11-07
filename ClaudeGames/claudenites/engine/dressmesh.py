"""A floor's dressing as meshes (see game/dress.py for what each list holds): one static mesh of the pictures on the
walls, on the floor, across the corners and hanging from the ceiling; the billboards (standing things, chests),
made each frame to face the eye; the drips falling from the pipes; and the water's surface.
Vertex: position 3, normal 3, uv 2, art layer 1, shade 1 (above 1: it glows by that much)."""
import math

import numpy as np


def _quad(out, p0, p1, p2, p3, n, layer, shade=1.0, uvs=((0, 1), (1, 1), (1, 0), (0, 0))):
    for i in (0, 1, 2, 0, 2, 3):
        p = (p0, p1, p2, p3)[i]
        out.append((p[0], p[1], p[2], n[0], n[1], n[2], uvs[i][0], uvs[i][1], layer, shade))


def static(L, layer_of):
    """-> float32 (n, 10): the walls' pictures, the floors', the webs, the hanging things."""
    out = []
    for (x, y0, z, nx, nz, w, h, name) in L.decals:
        lay = layer_of(name)
        if lay is None:
            continue
        tx, tz = -nz, nx                                     # (along the wall)
        ox, oz = x + nx * 0.004, z + nz * 0.004
        a = (ox - tx * w / 2, y0, oz - tz * w / 2)
        b = (ox + tx * w / 2, y0, oz + tz * w / 2)
        _quad(out, a, b, (b[0], y0 + h, b[2]), (a[0], y0 + h, a[2]), (nx, 0, nz), lay,
              1.6 if "torch" in name else 1.0)
    for (x, y, z, size, name, yaw) in L.flats:
        lay = layer_of(name)
        if lay is None:
            continue
        c, s = math.cos(yaw) * size, math.sin(yaw) * size
        pts = [(x + (-c + s), y, z + (-s - c)), (x + (c + s), y, z + (s - c)), (x + (c - s), y, z + (s + c)), (x + (-c - s), y, z + (-s + c))]
        _quad(out, *pts, (0, 1, 0), lay, 1.0, ((0, 0), (1, 0), (1, 1), (0, 1)))
    for (x, y, z, ax, az, size, name) in L.webs:
        lay = layer_of(name)
        if lay is None:
            continue
        # across the corner (ax, az: toward it), its top edge under the ceiling
        tx, tz = -az, ax
        ln = math.hypot(tx, tz) or 1
        tx, tz = tx / ln * size * 0.7, tz / ln * size * 0.7
        cx, cz = x - ax * size * 0.32, z - az * size * 0.32
        a, b = (cx - tx, y - 0.02, cz - tz), (cx + tx, y - 0.02, cz + tz)
        _quad(out, (a[0], y - size, a[2]), (b[0], y - size, b[2]), b, a, (-ax, 0, -az), lay, 1.0)
    for (x, y, z, size, name, yaw) in getattr(L, "ceils", ()):       # (on the ceiling, facing down: a grate)
        lay = layer_of(name)
        if lay is None:
            continue
        c, s = math.cos(yaw) * size, math.sin(yaw) * size
        pts = [(x + (-c + s), y, z + (-s - c)), (x + (c + s), y, z + (s - c)), (x + (c - s), y, z + (s + c)), (x + (-c - s), y, z + (-s + c))]
        _quad(out, pts[3], pts[2], pts[1], pts[0], (0, -1, 0), lay, 1.0, ((0, 1), (1, 1), (1, 0), (0, 0)))
    for (x, y, z, w, h, name) in L.hangs:
        lay = layer_of(name)
        if lay is None:
            continue
        for ang in (0.0, math.pi / 2):
            tx, tz = math.cos(ang) * w / 2, math.sin(ang) * w / 2
            _quad(out, (x - tx, y - h, z - tz), (x + tx, y - h, z + tz), (x + tx, y, z + tz), (x - tx, y, z - tz),
                  (math.sin(ang), 0, -math.cos(ang)), lay, 1.0)
    return np.array(out, np.float32).reshape(-1, 10)


def billboards(things, eye, yaw, reach=24.0):
    """things: [(x, y, z, w, h, layer, shade)] -> float32 (n, 10), each turned to face the eye about the up axis."""
    if not things:
        return np.zeros((0, 10), np.float32)
    T = np.array(things, np.float32)
    d = (T[:, 0] - eye[0]) ** 2 + (T[:, 2] - eye[2]) ** 2
    T = T[d < reach * reach]
    if not len(T):
        return np.zeros((0, 10), np.float32)
    rx, rz = math.cos(yaw), math.sin(yaw)                    # (the view's right, flat)
    nx, nz = math.sin(yaw), -math.cos(yaw)
    out = np.zeros((len(T), 6, 10), np.float32)
    corners = [(-0.5, 0, 0, 1), (0.5, 0, 1, 1), (0.5, 1, 1, 0), (-0.5, 0, 0, 1), (0.5, 1, 1, 0), (-0.5, 1, 0, 0)]
    for k, (sx, sy, u, v) in enumerate(corners):
        out[:, k, 0] = T[:, 0] + rx * sx * T[:, 3]
        out[:, k, 1] = T[:, 1] + sy * T[:, 4]
        out[:, k, 2] = T[:, 2] + rz * sx * T[:, 3]
        out[:, k, 3], out[:, k, 4], out[:, k, 5] = -nx, 0.35, -nz
        out[:, k, 6], out[:, k, 7] = u, v
        out[:, k, 8] = T[:, 5]
        out[:, k, 9] = T[:, 6]
    return out.reshape(-1, 10)


def water(L, layer):
    """The water's surface over its squares, a little under the floor's lip."""
    out = []
    for (x, y) in L.water:
        h = float(L.floor[y, x]) + 0.24
        _quad(out, (x, h, y), (x + 1, h, y), (x + 1, h, y + 1), (x, h, y + 1), (0, 1, 0), layer, 1.0,
              ((x * 0.5, y * 0.5), ((x + 1) * 0.5, y * 0.5), ((x + 1) * 0.5, (y + 1) * 0.5), (x * 0.5, (y + 1) * 0.5)))
    return np.array(out, np.float32).reshape(-1, 10)
