"""The den's dressing, laid out once from a seed: where water drips and pools, the vines hanging down the wall, the
roots snaking over the floor, the leaves that have fallen in, and the dark places near the ground where small eyes
watch. (The renderer draws them; the night keeps the eyes' blinking and scattering.)

    den = Den(tree, seed)
    den.drips      [(x, top, z, bottom)]        water falling from a ledge's edge or the wood above, into a puddle
    den.vines      [[(x, y, z), ...]]           each a line down the wall, from its root to its tip
    den.roots      [[(x, y, z, radius), ...]]   each a tapering line across the floor, partly buried
    den.leaves     [(x, y, z, size, turn, shade)]
    den.lurks      [(x, y, z)]                  low, dark places: where the small eyes are
Plain Python: the tests look at it."""
import math
import random

from . import tree as T


class Den:
    def __init__(self, tree, seed=11):
        self.tree = tree
        rng = random.Random(seed)
        self.drips = self._drips(rng)
        self.vines = self._vines(rng)
        self.roots = self._roots(rng)
        self.leaves = self._leaves(rng)
        self.lurks = self._lurks(rng)

    # ---- water -----------------------------------------------------------------------------------------------
    def _drips(self, rng):
        """From the ledge's inner edge (water runs down the wood and off it) to whatever is below; and a few from
        the knot-holes' rims."""
        t, out = self.tree, []
        for k in range(16):
            s = rng.uniform(1.5, t.s_end - 0.6)
            a = t.theta_of(s)
            h = t.ledge_h(s)
            r = t.base_r(a, h + 0.5) - T.LEDGE_W + 0.08
            x, z = math.cos(a) * r, math.sin(a) * r
            bottom = t.floor_at(x, z, h - 0.5)
            if h - 0.35 - bottom > 1.0:
                out.append((x, h - 0.38, z, bottom))
        for a, h, rad in T.KNOTS[:3]:
            r = t.base_r(a, h) - 0.25
            x, z = math.cos(a) * r, math.sin(a) * r
            bottom = t.floor_at(x, z, h - 0.6)
            if h - rad - bottom > 1.0:
                out.append((x, h - rad, z, bottom))
        return out

    # ---- vines -----------------------------------------------------------------------------------------------
    def _vines(self, rng):
        """Down the wall: from under the ledge's lip, and from the broken crown - wandering a little as they hang."""
        t, out = self.tree, []
        starts = []
        for k in range(56):
            s = rng.uniform(0.8, t.s_end)
            a = t.theta_of(s) + rng.uniform(-0.05, 0.05)
            starts.append((a, t.ledge_h(s) - 0.4))
        for k in range(22):
            a = rng.uniform(0, math.tau)
            starts.append((a, T.TOP - 0.6 + 1.2 * math.sin(3 * a + 0.4)))
        for a, y0 in starts:
            length = rng.uniform(2.0, 6.5)
            pts, sway, ph = [], rng.uniform(0.03, 0.09), rng.uniform(0, math.tau)
            y = y0
            while y > max(0.25, y0 - length):
                aa = a + sway * math.sin(ph + (y0 - y) * 1.3) / max(3.0, t.base_r(a, y))
                r = t.wall_r(aa, y) - 0.06
                pts.append((math.cos(aa) * r, y, math.sin(aa) * r))
                y -= 0.18
            if len(pts) > 4:
                out.append(pts)
        return out

    # ---- roots -----------------------------------------------------------------------------------------------
    def _roots(self, rng):
        """From the buttresses at the wall's foot, out across the floor toward the middle, tapering, half buried."""
        t, out = self.tree, []
        for k in range(26):
            a = (k / 26) * math.tau + rng.uniform(-0.12, 0.12)
            r0 = t.base_r(a, 0.0) - 0.1
            length = rng.uniform(2.2, 4.8)
            rad0 = rng.uniform(0.17, 0.32)
            bend, ph = rng.uniform(-0.35, 0.35), rng.uniform(0, math.tau)
            pts, n = [], 16
            for i in range(n + 1):
                f = i / n
                aa = a + bend * f * f + 0.06 * math.sin(ph + f * 6)
                rr = min(r0 - length * f, t.base_r(aa, 0.0) - 0.12)        # (never into the wall's flutes)
                x, z = math.cos(aa) * rr, math.sin(aa) * rr
                rad = rad0 * (1 - 0.75 * f) * (1 + 0.18 * math.sin(f * 23 + ph))      # (knotted, tapering)
                pts.append((x, t.ground(x, z) - rad * 0.35, z, rad))
            out.append(pts)
        return out

    # ---- leaves ----------------------------------------------------------------------------------------------
    def _leaves(self, rng):
        """Fallen in through the crown over a hundred autumns: thick on the floor, drifted against the wall, a scatter
        along the ledge, a few in the tunnel."""
        t, out = self.tree, []
        for k in range(2600):
            a = rng.uniform(0, math.tau)
            f = 1 - rng.random() ** 2.2                                  # (more toward the wall)
            r = f * (t.base_r(a, 0.0) - 0.2)
            x, z = math.cos(a) * r, math.sin(a) * r
            g = t.ground(x, z)
            out.append((x, t.floor_at(x, z, g) + 0.012, z, rng.uniform(0.035, 0.075), rng.uniform(0, math.tau), rng.random()))
        for k in range(1200):
            s = rng.uniform(0.4, t.s_end)
            a = t.theta_of(s)
            h = t.ledge_h(s)
            r = t.base_r(a, h + 0.5) - rng.uniform(0.05, T.LEDGE_W - 0.05)
            out.append((math.cos(a) * r, h + 0.012, math.sin(a) * r, rng.uniform(0.035, 0.07), rng.uniform(0, math.tau),
                        rng.random()))
        for k in range(320):
            along, across = rng.uniform(0.3, T.TUNNEL_LEN - 0.3), rng.uniform(-T.TUNNEL_HALF + 0.08, T.TUNNEL_HALF - 0.08)
            x, z = t.tunnel_point(along, across)
            out.append((x, t.tunnel_floor(along) + 0.012, z, rng.uniform(0.035, 0.065), rng.uniform(0, math.tau), rng.random()))
        return out

    # ---- the dark places near the ground -----------------------------------------------------------------------
    def _lurks(self, rng):
        """Low among the roots at the wall's foot, under the first turns of the ledge, at the tunnel's mouth."""
        t, out = self.tree, []
        for k in range(14):
            a = rng.uniform(0, math.tau)
            r = t.base_r(a, 0.2) - rng.uniform(0.25, 0.7)
            x, z = math.cos(a) * r, math.sin(a) * r
            out.append((x, t.ground(x, z) + rng.uniform(0.08, 0.4), z))
        for k in range(6):
            s = rng.uniform(2.0, 9.0)
            a = t.theta_of(s)
            h = t.ledge_h(s)
            r = t.base_r(a, h + 0.5) - 0.35
            out.append((math.cos(a) * r, h + rng.uniform(0.1, 0.35), math.sin(a) * r))
        return out
