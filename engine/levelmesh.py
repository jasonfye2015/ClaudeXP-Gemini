"""A level's squares as one static mesh: floors, ceilings, walls, the risers of steps and the lintels where a ceiling
drops, and (outdoors) the walls and roofs of the houses and the standing stones. Vertex: position 3, normal 3, uv 2,
texture layer 1, shade 1 (a little darkness in the corners and at the foot of walls)."""
import numpy as np

from ..game.levels import INVISIBLE

UV_SCALE = 1 / 1.5                   # a texture spans a square and a half


def build(L, layer_of):
    """-> float32 array (n, 10). layer_of maps the level's texture index to the texture array's layer."""
    out = []
    solid, floor, ceil, top = L.solid, L.floor, L.ceil, L.top
    H, W = solid.shape

    def is_solid(x, y):
        return not (0 <= x < W and 0 <= y < H) or solid[y, x]

    def corner_shade(x, y):
        """the corner (x, y) of the grid: darker the more rock meets there"""
        n = sum(is_solid(x + dx, y + dy) for dx in (-1, 0) for dy in (-1, 0))
        return 1.0 - 0.13 * n

    def quad(p0, p1, p2, p3, n, uvs, layer, shades):
        for i in (0, 1, 2, 0, 2, 3):
            p = (p0, p1, p2, p3)[i]
            out.append((*p, *n, *uvs[i], layer, shades[i]))

    for y in range(H):
        for x in range(W):
            if solid[y, x]:
                if L.outdoor and L.wtex[y, x] != INVISIBLE:                     # a house's ceiling under its roof, a stone's top
                    t = float(top[y, x])
                    lay = layer_of(L.wtex[y, x])
                    u0, v0, u1, v1 = x * UV_SCALE, y * UV_SCALE, (x + 1) * UV_SCALE, (y + 1) * UV_SCALE
                    quad((x, t, y), (x + 1, t, y), (x + 1, t, y + 1), (x, t, y + 1), (0, 1, 0),
                         ((u0, v0), (u1, v0), (u1, v1), (u0, v1)), lay, (0.95,) * 4)
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):            # its sides that face open ground
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < W and 0 <= ny < H and solid[ny, nx] and L.wtex[ny, nx] != INVISIBLE and top[ny, nx] >= t:
                            continue
                        bottom = float(floor[ny, nx]) if (0 <= nx < W and 0 <= ny < H and not solid[ny, nx]) else 0.0
                        bottom = min(bottom, 0.0) - 0.05
                        if 0 <= nx < W and 0 <= ny < H and solid[ny, nx] and L.wtex[ny, nx] != INVISIBLE:
                            bottom = float(top[ny, nx])
                        _side(quad, x, y, dx, dy, bottom, t, layer_of(L.wtex[y, x]), outward=True)
                continue
            f = float(floor[y, x])
            c = float(ceil[y, x])
            u0, v0, u1, v1 = x * UV_SCALE, y * UV_SCALE, (x + 1) * UV_SCALE, (y + 1) * UV_SCALE
            sh = (corner_shade(x, y), corner_shade(x + 1, y), corner_shade(x + 1, y + 1), corner_shade(x, y + 1))
            quad((x, f, y), (x + 1, f, y), (x + 1, f, y + 1), (x, f, y + 1), (0, 1, 0),
                 ((u0, v0), (u1, v0), (u1, v1), (u0, v1)), layer_of(L.ftex[y, x]), sh)
            if not L.outdoor:
                quad((x, c, y + 1), (x + 1, c, y + 1), (x + 1, c, y), (x, c, y), (0, -1, 0),
                     ((u0, v1), (u1, v1), (u1, v0), (u0, v0)), layer_of(L.ctex[y, x]), tuple(s * 0.9 for s in sh[::-1]))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if is_solid(nx, ny):
                    if L.outdoor:
                        continue                                                 # (the stone or house draws its own)
                    _side(quad, x, y, dx, dy, f, c, layer_of(L.wtex[ny, nx] if 0 <= nx < W and 0 <= ny < H else L.wtex[y, x]))
                    continue
                nf = float(floor[ny, nx])
                if nf > f + 1e-3:                                                # a step up: its riser
                    _side(quad, x, y, dx, dy, f, nf, layer_of(L.wtex[y, x]), riser=True)
                if not L.outdoor:
                    nc = float(ceil[ny, nx])
                    if nc < c - 1e-3:                                            # a lower ceiling: its lintel
                        _side(quad, x, y, dx, dy, nc, c, layer_of(L.wtex[y, x]))
    for h in getattr(L, "houses", []):
        _house(quad, h, layer_of, L)
    return np.array(out, np.float32).reshape(-1, 10)


def _house(quad, h, layer_of, L):
    """A pitched roof over a house's block (the ridge along x), its gables, and a door on the side toward the square."""
    x0, y0, x1, y1, t, roof, (ddx, ddy) = h
    o = 0.35                                           # the eaves' overhang
    peak = t + 0.55 * (y1 - y0)
    zm = (y0 + y1) / 2
    rl = layer_of(roof)
    wl = layer_of(L.wtex[y0, x0])
    run = (y1 - y0) / 2 + o
    slope = ((peak - t) ** 2 + run ** 2) ** 0.5
    for side in (-1, 1):                               # the two slopes, north and south
        ze = zm + side * run
        ny, nz = run / slope, side * (peak - t) / slope
        a, b, c, d = (x0 - o, t - 0.12, ze), (x1 + o, t - 0.12, ze), (x1 + o, peak, zm), (x0 - o, peak, zm)
        u = (x1 - x0 + 2 * o) * UV_SCALE
        v = slope * UV_SCALE
        if side < 0:
            a, b, c, d = b, a, d, c
        quad(a, b, c, d, (0, ny, nz), ((0, 0), (u, 0), (u, v), (0, v)), rl, (0.85, 0.85, 1.0, 1.0))
    for gx, n in ((x0, -1), (x1, 1)):                  # the gables: triangles of wall, east and west
        tri = ((gx, t, y0), (gx, t, y1), (gx, peak, zm))
        uvs = ((y0 * UV_SCALE, 0), (y1 * UV_SCALE, 0), (zm * UV_SCALE, (peak - t) * UV_SCALE))
        quad(tri[0], tri[1], tri[2], tri[2], (n, 0, 0), (uvs[0], uvs[1], uvs[2], uvs[2]), wl, (0.9, 0.9, 1.0, 1.0))
    # the door
    pl = layer_of(L.textures.index("ground.planks")) if "ground.planks" in L.textures else wl
    w, hgt, e = 0.55, 1.45, 0.02
    if ddx:
        fx = (x0 - e) if ddx < 0 else (x1 + e)
        zc = (y0 + y1) / 2
        a, b = (fx, 0.0, zc - w), (fx, 0.0, zc + w)
        if ddx > 0:
            a, b = b, a
        quad(a, b, (b[0], hgt, b[2]), (a[0], hgt, a[2]), (ddx, 0, 0), ((0, 0), (0.7, 0), (0.7, 1), (0, 1)), pl, (0.5,) * 4)
    else:
        fz = (y0 - e) if ddy < 0 else (y1 + e)
        xc = (x0 + x1) / 2
        a, b = (xc + w, 0.0, fz), (xc - w, 0.0, fz)
        if ddy > 0:
            a, b = b, a
        quad(a, b, (b[0], hgt, b[2]), (a[0], hgt, a[2]), (0, 0, ddy), ((0, 0), (0.7, 0), (0.7, 1), (0, 1)), pl, (0.5,) * 4)


def _side(quad, x, y, dx, dy, y0, y1, layer, riser=False, outward=False):
    """A vertical face on the edge of square (x, y) toward (dx, dy), from height y0 to y1, facing back into (x, y)
    (or out of it, for a house's wall)."""
    if dx == 1:
        a, b = (x + 1, y + 1), (x + 1, y)
    elif dx == -1:
        a, b = (x, y), (x, y + 1)
    elif dy == 1:
        a, b = (x, y + 1), (x + 1, y + 1)
    else:
        a, b = (x + 1, y), (x, y)
    n = (-dx, 0, -dy)
    if outward:
        a, b = b, a
        n = (dx, 0, dy)
    ua = (a[0] + a[1]) * UV_SCALE
    ub = ua + UV_SCALE
    va, vb = -y0 * UV_SCALE, -y1 * UV_SCALE
    lo, hi = (0.72, 0.95) if not riser else (0.7, 0.85)
    quad((a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1]), n,
         ((ua, va), (ub, va), (ub, vb), (ua, vb)), layer, (lo, lo, hi, hi))
