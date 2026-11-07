"""The Hollow Oak as meshes, built from game/tree.py's own functions (so what is drawn is what is walked):

    world(tree)    -> float32 (n, 10): the wall, the floor, the ledge, the root tunnel, the broken crown
                      vertex: position 3, normal 3, uv 2, texture layer 1, shade 1 (baked darkness)
    fungus(tree)   -> float32 (n, 6): the glowing shelf fungus (position 3, colour 3), and its lights
    shafts(tree)   -> the moonbeams through the knot-holes: (start, end, width)

Texture layers: 0 the heartwood (bark), 1 the earth, 2 dry leaves."""
import math

import numpy as np

from ..game import tree as T

BARK, EARTH, LEAVES = 0, 1, 2
UV = 0.5                              # (texture repeats per unit)


def _quad(out, p0, p1, p2, p3, layer, uvs, shades=(1, 1, 1, 1), n=None):
    if n is None:
        a = np.subtract(p1, p0)
        b = np.subtract(p3, p0)
        n = np.cross(b, a)
        ln = float(np.linalg.norm(n)) or 1.0
        n = n / ln
    for i in (0, 1, 2, 0, 2, 3):
        p = (p0, p1, p2, p3)[i]
        out.append((p[0], p[1], p[2], n[0], n[1], n[2], uvs[i][0], uvs[i][1], layer, shades[i]))


def _shade_wall(y, r_in_chamber):
    """Darker low down, darker still deep in a chamber."""
    return max(0.35, min(1.0, 0.55 + y * 0.05)) * (0.75 if r_in_chamber else 1.0)


def world(tree):
    out = []
    _wall(tree, out)
    _floor(tree, out)
    _ledge(tree, out)
    _tunnel(tree, out)
    _crown(tree, out)
    return np.array(out, np.float32).reshape(-1, 10)


def _wall(tree, out):
    N, dy = 220, 0.33
    rows = int((T.TOP + 1.6) / dy) + 1
    ys = [-0.4 + i * dy for i in range(rows)]
    th = [i / N * math.tau for i in range(N + 1)]
    top = [T.TOP + 1.2 * math.sin(3 * a + 0.4) + 0.7 * math.sin(7 * a) for a in th]     # (the broken rim)
    P = {}
    for i, a in enumerate(th):
        for j, y in enumerate(ys):
            r = tree.wall_r(a, y)
            P[i, j] = (math.cos(a) * r, y, math.sin(a) * r, r - tree.base_r(a, y) > 0.2)
    for i in range(N):
        a0, a1 = th[i], th[i + 1]
        for j in range(rows - 1):
            y0, y1 = ys[j], ys[j + 1]
            if y0 >= max(top[i], top[i + 1]):
                continue
            am, ym = (a0 + a1) / 2, (y0 + y1) / 2
            if tree.knot_at(am, ym):
                continue
            rm = tree.wall_r(am, ym)
            if ym < T.TUNNEL_CEIL + 0.1 and tree.in_tunnel(math.cos(am) * (rm + 0.2), math.sin(am) * (rm + 0.2)):
                continue
            p00, p10, p11, p01 = P[i, j], P[i + 1, j], P[i + 1, j + 1], P[i, j + 1]
            if y1 > min(top[i], top[i + 1]):                # (the broken rim: the last row cut to its ragged edge)
                cut = []
                for a, t_, p0, p1 in ((a0, top[i], p00, p01), (a1, top[i + 1], p10, p11)):
                    yy = max(p0[1], min(p1[1], t_))
                    rr = tree.wall_r(a, yy)
                    cut.append((math.cos(a) * rr, yy, math.sin(a) * rr, p1[3]))
                p01, p11 = cut
            u0, u1 = a0 * T.R0 * UV, a1 * T.R0 * UV
            sh = [_shade_wall(p[1], p[3]) for p in (p00, p10, p11, p01)]
            _quad(out, p00[:3], p01[:3], p11[:3], p10[:3], BARK,
                  ((u0, y0 * UV), (u0, y1 * UV), (u1, y1 * UV), (u1, y0 * UV)), (sh[0], sh[3], sh[2], sh[1]))
    # the knot-holes' rims: a short throat out through the wood, so each reads as a hole, not a gap
    for a, h, rad in T.KNOTS:
        r = tree.base_r(a, h)
        k = 16
        for m in range(k):
            b0, b1 = m / k * math.tau, (m + 1) / k * math.tau
            pts = []
            for b in (b0, b1):
                da = math.cos(b) * rad / r
                y = h + math.sin(b) * rad
                rr = tree.wall_r(a + da, y)
                pts.append(((math.cos(a + da) * rr, y, math.sin(a + da) * rr),
                            (math.cos(a + da) * (rr + 1.0), y, math.sin(a + da) * (rr + 1.0))))
            _quad(out, pts[0][0], pts[1][0], pts[1][1], pts[0][1], BARK, ((0, 0), (0.3, 0), (0.3, 0.5), (0, 0.5)),
                  (0.6, 0.6, 0.4, 0.4))


def _floor(tree, out):
    N, M = 160, 34
    for i in range(N):
        a0, a1 = i / N * math.tau, (i + 1) / N * math.tau
        r0, r1 = tree.base_r(a0, 0.0) + 0.6, tree.base_r(a1, 0.0) + 0.6
        for j in range(M):
            f0, f1 = j / M, (j + 1) / M
            pts = []
            for (a, rr, f) in ((a0, r0, f0), (a1, r1, f0), (a1, r1, f1), (a0, r0, f1)):
                x, z = math.cos(a) * rr * f, math.sin(a) * rr * f
                pts.append((x, tree.ground(x, z), z))
            sh = [0.55 + 0.45 * (1 - f) for f in (f0, f0, f1, f1)]
            _quad(out, pts[0], pts[3], pts[2], pts[1], EARTH,
                  [(p[0] * UV, p[2] * UV) for p in (pts[0], pts[3], pts[2], pts[1])], (sh[0], sh[3], sh[2], sh[1]))


def _ledge(tree, out):
    ds = 0.03
    n = int(tree.s_end / ds)
    prev = None
    for k in range(n + 1):
        s = min(tree.s_end, k * ds)
        h = tree.ledge_h(s)
        a = tree.theta_of(s)
        ri = tree.base_r(a, h + 0.5) - T.LEDGE_W
        ro = tree.wall_r(a, h + 0.3) + 0.25
        c, sn = math.cos(a), math.sin(a)
        cur = dict(s=s, h=h, a=a, ti=(c * ri, h, sn * ri), to=(c * ro, h, sn * ro),
                   bi=(c * ri, h - 0.35, sn * ri), bo=(c * ro, h - 0.35, sn * ro))
        if prev is not None and h > 0.15:
            u0, u1 = prev["s"] * T.R0 * UV, s * T.R0 * UV
            # its top: dry leaves; its front edge and underside: the wood
            _quad(out, prev["ti"], prev["to"], cur["to"], cur["ti"], EARTH,
                  ((u0, 0), (u0, 0.8), (u1, 0.8), (u1, 0)), (0.85, 0.65, 0.65, 0.85), n=(0, 1, 0))
            _quad(out, prev["bi"], prev["ti"], cur["ti"], cur["bi"], BARK,
                  ((u0, 0), (u0, 0.2), (u1, 0.2), (u1, 0)), (0.55, 0.8, 0.8, 0.55))
            _quad(out, prev["bo"], prev["bi"], cur["bi"], cur["bo"], BARK,
                  ((u0, 0), (u0, 0.8), (u1, 0.8), (u1, 0)), (0.3, 0.4, 0.4, 0.3), n=(0, -1, 0))
        prev = cur


def _tunnel(tree, out):
    L, W, steps = T.TUNNEL_LEN, T.TUNNEL_HALF, 18
    for k in range(steps):
        a0, a1 = -0.4 + k * (L + 0.4) / steps, -0.4 + (k + 1) * (L + 0.4) / steps
        f0, f1 = tree.tunnel_floor(max(0, a0)), tree.tunnel_floor(max(0, a1))
        wob = lambda a: 0.08 * math.sin(a * 2.3)      # noqa: E731
        p = lambda a, c, y: (*tree.tunnel_point(a, c),)      # noqa: E731
        (x00, z00), (x01, z01) = p(a0, -W - wob(a0), 0), p(a0, W + wob(a0), 0)
        (x10, z10), (x11, z11) = p(a1, -W - wob(a1), 0), p(a1, W + wob(a1), 0)
        c0, c1 = f0 + T.TUNNEL_CEIL + wob(a0), f1 + T.TUNNEL_CEIL + wob(a1)
        u0, u1 = a0 * UV, a1 * UV
        _quad(out, (x00, f0, z00), (x10, f1, z10), (x11, f1, z11), (x01, f0, z01), LEAVES,
              ((u0 * 2.2, 0), (u1 * 2.2, 0), (u1 * 2.2, 1.7), (u0 * 2.2, 1.7)), (0.42, 0.42, 0.42, 0.42))
        _quad(out, (x01, c0, z01), (x11, c1, z11), (x10, c1, z10), (x00, c0, z00), BARK,
              ((u0, 0), (u1, 0), (u1, 0.8), (u0, 0.8)), (0.24, 0.24, 0.24, 0.24))
        for (xa, za), (xb, zb) in (((x00, z00), (x10, z10)), ((x11, z11), (x01, z01))):
            first = (xa, za) == (x00, z00)
            fa, fb = (f0, f1) if first else (f1, f0)
            ca, cb = (c0, c1) if first else (c1, c0)
            _quad(out, (xa, fa, za), (xa, ca, za), (xb, cb, zb), (xb, fb, zb), BARK,
                  ((u0, 0), (u0, 0.85), (u1, 0.85), (u1, 0)), (0.3, 0.36, 0.36, 0.3))
    # its far end: earth and roots, the night beyond showing through a gap (drawn as a glow)
    (xa, za), (xb, zb) = tree.tunnel_point(L, -W), tree.tunnel_point(L, W)
    f = tree.tunnel_floor(L)
    _quad(out, (xa, f, za), (xb, f, zb), (xb, f + T.TUNNEL_CEIL, zb), (xa, f + T.TUNNEL_CEIL, za), BARK,
          ((0, 0), (0.8, 0), (0.8, 0.85), (0, 0.85)), (0.35, 0.35, 0.35, 0.35))


def _crown(tree, out):
    """The trunk's broken top: a rim of wood, seen from inside as the lip against the sky."""
    N = 120
    for i in range(N):
        a0, a1 = i / N * math.tau, (i + 1) / N * math.tau
        t0 = T.TOP + 1.2 * math.sin(3 * a0 + 0.4) + 0.7 * math.sin(7 * a0)
        t1 = T.TOP + 1.2 * math.sin(3 * a1 + 0.4) + 0.7 * math.sin(7 * a1)
        r0, r1 = tree.wall_r(a0, t0), tree.wall_r(a1, t1)
        pi0, pi1 = (math.cos(a0) * r0, t0, math.sin(a0) * r0), (math.cos(a1) * r1, t1, math.sin(a1) * r1)
        po0, po1 = (math.cos(a0) * (r0 + 1.4), t0 - 0.3, math.sin(a0) * (r0 + 1.4)), \
            (math.cos(a1) * (r1 + 1.4), t1 - 0.3, math.sin(a1) * (r1 + 1.4))
        u0, u1 = a0 * T.R0 * UV, a1 * T.R0 * UV
        _quad(out, pi0, po0, po1, pi1, BARK, ((u0, 0), (u0, 0.7), (u1, 0.7), (u1, 0)), (1, 0.8, 0.8, 1))


# ---- the fungus, glowing --------------------------------------------------------------------------------------------
GLOW = (0.32, 0.95, 0.78)


def fungus(tree):
    """Shelf fungus on the wall: a few fans to a cluster, cold blue-green; -> (vertices (n, 6), lights)."""
    out, lights = [], []
    for k, (a, h, size) in enumerate(T.FUNGI):
        r = tree.wall_r(a, h)
        for m in range(3):
            da = (m - 1) * 0.05 * size
            y = h + (m - 1) * 0.28 * size + 0.1 * math.sin(k + m)
            rad = size * (0.55 - 0.1 * abs(m - 1))
            rr = tree.wall_r(a + da, y)
            cx, cz = math.cos(a + da) * rr, math.sin(a + da) * rr
            inx, inz = -math.cos(a + da), -math.sin(a + da)
            tx, tz = -inz, inx
            col = tuple(c * (0.75 + 0.25 * math.sin(k * 1.7 + m)) for c in GLOW)
            seg = 9
            for q in range(seg):
                b0, b1 = q / seg * math.pi, (q + 1) / seg * math.pi
                pts = [(cx, y, cz)]
                for b in (b0, b1):
                    ox = tx * math.cos(b) * rad + inx * math.sin(b) * rad
                    oz = tz * math.cos(b) * rad + inz * math.sin(b) * rad
                    pts.append((cx + ox, y - 0.06 * math.sin(b), cz + oz))
                rim = tuple(c * 1.25 for c in col)
                for p, c in zip(pts, (col, rim, rim)):
                    out.append((*p, *c))
                lo = [(p[0], p[1] - 0.09, p[2]) for p in pts[1:]]             # (its rim: a thickness, glowing)
                for p, c in zip((pts[1], pts[2], lo[1], pts[1], lo[1], lo[0]), (rim,) * 6):
                    out.append((*p, *tuple(v * 0.7 for v in c)))
        r_in = r - 0.6
        lights.append((math.cos(a) * r_in, h, math.sin(a) * r_in, GLOW[0] * 0.6, GLOW[1] * 0.6, GLOW[2] * 0.6, 4.6 + size))
    return np.array(out, np.float32).reshape(-1, 6), lights


def shafts(tree):
    """The moon through each knot-hole: a beam slanting in and down. -> [(start, end, width)]"""
    out = []
    for a, h, rad in T.KNOTS:
        r = tree.base_r(a, h)
        start = np.array((math.cos(a) * (r + 0.4), h, math.sin(a) * (r + 0.4)), np.float32)
        inward = np.array((-math.cos(a + 0.35), -1.15, -math.sin(a + 0.35)), np.float32)
        inward /= np.linalg.norm(inward)
        length = min(14.0, (h + 0.2) / 1.15 * math.sqrt(1 + 1.15 ** 2) * 0.62)
        out.append((start, start + inward * length, rad * 1.5))
    return out
