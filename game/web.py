"""Her silk: what can be walked on, and what only hangs there.

Walkable: three strands - bridges of a few cables woven together - thrown across the hollow from one turn of the ledge
to a higher one (narrow, sagging, swaying: a short way up, and a test of nerve); her loom, a great orb web across the
hollow low down, meeting the ledge where it passes; and the crown web, across the top, under the moon. Everything else
is dressing: webs over the knot-holes, tangles under the ledge and at the backs of the chambers, low sheets among the
roots, threads hanging down into the dark, the first strands in the root tunnel.

    web = Web(tree)
    web.floor_at(x, z, feet)      -> (height, piece) of the highest silk under (x, z) he can step onto, or None
    web.strands()                 -> [(points (n, 3), width, group, free (n,), phase)] - every thread, for the renderer
    web.bridges, web.loom, web.crown

A thread's `free` is how far it can move at each point (0 where it's anchored, 1 at the middle of a span) and `group`
which piece of silk it belongs to: they shiver together when something walks on them. His weight dips whatever he
stands on by DIP, and the heights here include it (he always stands where his weight is).
Plain Python: the tests walk it."""
import math
import random

from . import tree as T

H_LOOM = 4.5                    # (her loom: across the hollow, a little below the first turn of the ledge's height)
LOOM_SAG = 0.5
CROWN_SAG = 0.6
BRIDGE_HALF = 0.34              # (half the walkable width of a strand: two cables either side of his feet)
BRIDGE_SAG = 0.32
DIP = 0.1                       # (his weight)
CABLES = (-0.3, -0.1, 0.1, 0.3)
# the strands: (name, from how far round the spiral (in turns), to how far)
BRIDGES = (("the low strand", 0.95, 1.45), ("the gallery strand", 2.18, 2.8), ("the high strand", 3.3, 3.62))
GROUPS = 8                      # (0-2 the strands, 3 the loom, 4 the crown web, 5-7 the dressing)


class Bridge:
    """A strand across the hollow: from a on one turn of the ledge to b on a higher one, straight across in plan,
    sagging between."""

    def __init__(self, tree, k, name, turn_a, turn_b):
        self.k, self.name, self.group, self.tree = k, name, k, tree
        self.a = self._end(tree, turn_a * math.tau)
        self.b = self._end(tree, turn_b * math.tau)
        dx, dz = self.b[0] - self.a[0], self.b[2] - self.a[2]
        self.length = math.hypot(dx, dz)
        self.dir = (dx / self.length, dz / self.length)
        self.side = (-self.dir[1], self.dir[0])

    @staticmethod
    def _end(tree, s):
        th = tree.theta_of(s)
        h = tree.ledge_h(s)
        r = tree.base_r(th, h + 0.5) - T.LEDGE_W + 0.02                # (at the ledge's edge)
        return (math.cos(th) * r, h, math.sin(th) * r)

    def locate(self, x, z):
        """-> (u, across): how far along (0 at a, 1 at b), and how far to the side of its middle."""
        rx, rz = x - self.a[0], z - self.a[2]
        return (rx * self.dir[0] + rz * self.dir[1]) / self.length, rx * self.side[0] + rz * self.side[1]

    def height(self, u, weighted=True):
        u = max(0.0, min(1.0, u))
        y = self.a[1] + (self.b[1] - self.a[1]) * u - BRIDGE_SAG * 4 * u * (1 - u)
        return y - (DIP * math.sin(math.pi * u) if weighted else 0.0)

    def point(self, u, across=0.0, weighted=False):
        return (self.a[0] + self.dir[0] * self.length * u + self.side[0] * across, self.height(u, weighted),
                self.a[2] + self.dir[1] * self.length * u + self.side[1] * across)

    def floor_at(self, x, z):
        u, across = self.locate(x, z)
        if 0.0 <= u <= 1.0 and abs(across) <= BRIDGE_HALF:
            y = self.height(u)
            if math.hypot(x, z) < self.tree.base_r(math.atan2(z, x), y + 0.5) - T.LEDGE_W:   # (out over the hollow)
                return y
        return None


class Disc:
    """A web across the whole hollow at height h, its rim just meeting the ledge's inner edge, sagging to its hub."""

    def __init__(self, tree, group, name, h, sag):
        self.group, self.name, self.h, self.sag = group, name, h, sag
        self._rim = [tree.base_r(k / 72 * math.tau, h + 0.5) - T.LEDGE_W + 0.04 for k in range(72)]

    def rim(self, th):
        f = (th % math.tau) / math.tau * 72
        i = int(f)
        k = f - i
        return self._rim[i % 72] * (1 - k) + self._rim[(i + 1) % 72] * k

    def height(self, x, z, weighted=True):
        r = math.hypot(x, z)
        f = min(1.0, r / self.rim(math.atan2(z, x)))
        return self.h - self.sag * (1 - f * f) - (DIP * (1 - f) if weighted else 0.0)

    def floor_at(self, x, z):
        if math.hypot(x, z) < self.rim(math.atan2(z, x)):
            return self.height(x, z)
        return None


class Web:
    def __init__(self, tree, seed=5):
        self.tree = tree
        self.bridges = [Bridge(tree, k, *b) for k, b in enumerate(BRIDGES)]
        self.loom = Disc(tree, 3, "her loom", H_LOOM, LOOM_SAG)
        self.crown = Disc(tree, 4, "the crown web", tree.landing_h["crown"], CROWN_SAG)
        self.discs = [self.loom, self.crown]
        self.pieces = self.bridges + self.discs
        self.rng = random.Random(seed)
        self._strands = None

    def floor_at(self, x, z, feet):
        """The highest silk under (x, z) that a walker with feet at `feet` can step onto (or falls to)."""
        best = None
        for p in self.pieces:
            h = p.floor_at(x, z)
            if h is not None and h <= feet + T.STEP and (best is None or h > best[0]):
                best = (h, p)
        return best

    # ---- every thread, for drawing ---------------------------------------------------------------------------
    def strands(self):
        if self._strands is None:
            out = []
            for b in self.bridges:
                self._bridge(out, b)
            self._disc(out, self.loom, 40, 0.24)
            self._disc(out, self.crown, 32, 0.32)
            self._dressing(out)
            self._strands = out
        return self._strands

    def _line(self, out, pts, width, group, free=None, phase=None):
        n = len(pts)
        if free is None:                                            # (anchored at both ends, free in the middle)
            free = [math.sin(math.pi * i / max(1, n - 1)) for i in range(n)]
        out.append((pts, width, group, free, self.rng.uniform(0, math.tau) if phase is None else phase))

    def _span(self, a, b, n, sag):
        """A thread from a to b, sagging by `sag` in the middle."""
        return [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t - sag * 4 * t * (1 - t), a[2] + (b[2] - a[2]) * t)
                for t in (i / (n - 1) for i in range(n))]

    def _wall(self, th, y, inset=0.03):
        r = self.tree.wall_r(th, y) - inset
        return (math.cos(th) * r, y, math.sin(th) * r)

    def _bridge(self, out, b):
        n = 40
        for c in CABLES:                                             # (the cables, side by side)
            self._line(out, [b.point(i / (n - 1), c) for i in range(n)], 0.016 if abs(c) > 0.2 else 0.013, b.group)
        m = int(b.length / 0.22)                                      # (woven across, zig and zag)
        for i in range(m):
            u0, u1 = i / m, (i + 1) / m
            c0, c1 = (CABLES[0], CABLES[-1]) if i % 2 else (CABLES[-1], CABLES[0])
            free = math.sin(math.pi * (u0 + u1) / 2)
            self._line(out, [b.point(u0, c0), b.point(u1, c1)], 0.006, b.group, [free, free], 0.0)
        for end, u in ((b.a, 0.0), (b.b, 1.0)):                       # (its anchors: fanned up to the wall behind)
            th = math.atan2(end[2], end[0])
            for dth, dy in ((-0.16, 0.9), (0.0, 1.7), (0.16, 0.9), (-0.08, 2.6), (0.1, 2.3)):
                w = self._wall(th + dth, end[1] + dy)
                start = b.point(u, CABLES[0] if dth < 0 else CABLES[-1])
                self._line(out, self._span(start, w, 8, 0.05), 0.009, b.group,
                           [0.3 * (1 - i / 7) for i in range(8)])

    def _disc(self, out, d, radials, spacing):
        angles = [k / radials * math.tau + 0.05 * math.sin(k * 2.3) for k in range(radials)]

        def at(th, f):
            r = d.rim(th) * f
            x, z = math.cos(th) * r, math.sin(th) * r
            return (x, d.height(x, z, False), z)
        for th in angles:                                             # (the radials, hub to rim)
            pts = [at(th, i / 13) for i in range(14)]
            self._line(out, pts, 0.011, d.group, [1 - (i / 13) ** 2 for i in range(14)])
        r_max = min(d._rim)
        turns = (r_max * 0.95 - 0.5) / spacing                        # (the spiral, out from near the hub)
        pts, free = [], []
        steps = int(turns * radials)
        for i in range(steps + 1):
            k = i / radials
            th = angles[i % radials]
            f = (0.5 + k * spacing) / r_max
            f = min(0.97, f)
            pts.append(at(th, f))
            free.append(1 - f * f)
            if len(pts) >= 80:                                        # (in lengths, so no one line is too long)
                self._line(out, pts, 0.006, d.group, free)
                pts, free = [pts[-1]], [free[-1]]
        if len(pts) > 1:
            self._line(out, pts, 0.006, d.group, free)
        for k in range(0, radials, 2):                                # (moored to the wall, above and below)
            th = angles[k]
            rim = at(th, 1.0)
            for dy in (1.4, -1.2) if k % 4 == 0 else (2.2,):
                w = self._wall(th + 0.04 * dy, d.h + dy)
                self._line(out, self._span(rim, w, 6, 0.03), 0.008, d.group, [0.2 * (1 - i / 5) for i in range(6)])

    def _dressing(self, out):
        t = self.tree
        rng = self.rng
        # webs over three of the knot-holes: small orbs, the moon behind them
        for a, h, rad in (T.KNOTS[0], T.KNOTS[2], T.KNOTS[4]):
            c = self._wall(a, h, 0.12)
            r = rad * 1.5
            ex, ez = -math.sin(a), math.cos(a)                        # (across the wall, and up it)
            spokes = 14
            for k in range(spokes):
                ang = k / spokes * math.tau
                end = (c[0] + ex * math.cos(ang) * r, c[1] + math.sin(ang) * r, c[2] + ez * math.cos(ang) * r)
                self._line(out, self._span(c, end, 5, 0.0), 0.004, 5, [0.6 * (1 - i / 4) for i in range(5)])
            pts = []
            for i in range(spokes * 7):
                ang = i / spokes * math.tau
                f = 0.15 + 0.8 * i / (spokes * 7)
                pts.append((c[0] + ex * math.cos(ang) * r * f, c[1] + math.sin(ang) * r * f, c[2] + ez * math.cos(ang) * r * f))
            self._line(out, pts, 0.003, 5, [0.5] * len(pts))
        # tangles under the ledge: threads from its underside down to the wall below
        for k in range(16):
            s = rng.uniform(0.5, t.s_end - 0.5)
            h = t.ledge_h(s)
            if h < 2.0:
                continue
            th0 = t.theta_of(s)
            for _ in range(rng.randint(14, 24)):
                th = th0 + rng.uniform(-0.25, 0.25)
                r_in = t.base_r(th, h) - T.LEDGE_W + 0.05
                top = (math.cos(th) * r_in, h - 0.36, math.sin(th) * r_in)
                low = self._wall(th + rng.uniform(-0.15, 0.15), h - rng.uniform(0.7, 1.8), 0.04)
                self._line(out, self._span(top, low, 6, rng.uniform(0.0, 0.12)), 0.0035, 5 + k % 3)
        # threads hanging down into the dark, from the ledge's edge and from the strands
        for k in range(26):
            if k < 18:
                s = rng.uniform(0.8, t.s_end - 0.3)
                h = t.ledge_h(s)
                th = t.theta_of(s)
                r_in = t.base_r(th, h) - T.LEDGE_W + 0.04
                top = (math.cos(th) * r_in, h - 0.35, math.sin(th) * r_in)
            else:
                b = self.bridges[k % 3]
                top = b.point(rng.uniform(0.2, 0.8), rng.choice(CABLES))
            drop = rng.uniform(1.5, 5.5)
            bottom = max(t.ground(top[0], top[2]) + 0.6, top[1] - drop)
            n = 10
            pts = [(top[0], top[1] + (bottom - top[1]) * i / (n - 1), top[2]) for i in range(n)]
            self._line(out, pts, 0.004, 5 + k % 3, [(i / (n - 1)) ** 1.5 for i in range(n)])
        # low sheets among the roots, near the wall
        for k in range(12):
            th0 = rng.uniform(0, math.tau)
            if abs((th0 - T.THETA_IN + math.pi) % math.tau - math.pi) < 0.5:
                continue
            for _ in range(rng.randint(12, 20)):
                th1, th2 = th0 + rng.uniform(-0.2, 0.2), th0 + rng.uniform(-0.2, 0.2)
                d1, d2 = t.base_r(th1, 0.2) - rng.uniform(0.2, 0.9), t.base_r(th2, 0.2) - rng.uniform(0.2, 0.9)
                p1 = (math.cos(th1) * d1, 0.0, math.sin(th1) * d1)
                p2 = (math.cos(th2) * d2, 0.0, math.sin(th2) * d2)
                p1 = (p1[0], t.ground(p1[0], p1[2]) + rng.uniform(0.08, 0.35), p1[2])
                p2 = (p2[0], t.ground(p2[0], p2[2]) + rng.uniform(0.05, 0.3), p2[2])
                self._line(out, self._span(p1, p2, 5, 0.03), 0.003, 5 + k % 3)
        # the backs of the chambers: tangles across them
        for name, start, run in T.LANDINGS[:-1]:
            h = t.landing_h[name]
            mid = t.theta_of(start + run / 2)
            for _ in range(40):
                th1, th2 = mid + rng.uniform(-0.35, 0.35) * run, mid + rng.uniform(-0.35, 0.35) * run
                p1 = self._wall(th1, h + rng.uniform(0.3, 2.3), 0.05)
                p2 = self._wall(th2, h + rng.uniform(0.3, 2.3), 0.05)
                self._line(out, self._span(p1, p2, 6, rng.uniform(0.02, 0.2)), 0.0035, 6)
        # the first strands, in the root tunnel: high in its corners, over his head
        for k in range(14):
            along = rng.uniform(0.8, T.TUNNEL_LEN - 1.5)
            f = t.tunnel_floor(along)
            a = t.tunnel_point(along, -T.TUNNEL_HALF + 0.02)
            b = t.tunnel_point(along + rng.uniform(-0.6, 0.6), T.TUNNEL_HALF - 0.02)
            ya, yb = f + rng.uniform(1.2, 1.62), f + rng.uniform(1.2, 1.62)
            self._line(out, self._span((a[0], ya, a[1]), (b[0], yb, b[1]), 7, rng.uniform(0.05, 0.25)), 0.0035, 7)
