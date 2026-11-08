"""Her small ones: spiders the length of a forearm, legs and all, about the den - on the wall, across the floor among
the roots, out on her silk. They go in fits and starts: still a while, then a scurry, then still. When he comes near,
or hurries, or his lantern finds them, they're off, fast, away from him. They keep about him as he goes; the den is
full of them.

    brood = Brood(tree, web, rng)
    brood.step(dt, eye, hurry, reach)   -> events: ("skitter", position, distance) when one bolts near him
    brood.near(eye, limit)              -> [(position, forward, up, size, clip, t)] for drawing ("walk" or "idle")

Each one is on a surface - "wall" (angle, height), "floor" (x, z), "disc" (which, x, z), "strand" (which, u, cable) -
and heads somewhere on it. Plain Python: the tests watch them."""
import math

from . import tree as T
from .web import CABLES

COUNT = 24
NEAR, FAR = 5.0, 13.0           # (where a stray one turns up again: out of the light, not too far)
LOST = 16.0                     # (further than this, and it's somewhere else)


def _norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


class Brood:
    def __init__(self, tree, web, rng, count=COUNT):
        self.tree, self.web, self.rng = tree, web, rng
        self.spiders = []
        self.pouring = []                         # (out of a split cocoon: for a few seconds, everywhere)
        sx, sz, _f = tree.start
        start = (sx * 0.4, 0.62, sz * 0.4)
        for _ in range(count):
            sp = {"size": rng.uniform(0.09, 0.2), "state": "rest", "until": rng.uniform(0, 3), "speed": 0.0,
                  "anim": rng.uniform(0, 5), "head": rng.uniform(0, math.tau)}
            self._place(sp, start)
            self.spiders.append(sp)

    # ---- where it is ---------------------------------------------------------------------------------------------
    def pos(self, sp, p=None):
        t = self.tree
        kind = sp["on"]
        p = sp["p"] if p is None else p
        if kind == "floor":
            return (p[0], t.ground(p[0], p[1]) + 0.004, p[1])
        if kind == "wall":
            th, y = p
            r = t.wall_r(th, y) - 0.025
            return (math.cos(th) * r, y, math.sin(th) * r)
        if kind == "disc":
            d = self.web.discs[p[0]]
            return (p[1], d.height(p[1], p[2], False) + 0.01, p[2])
        b = self.web.bridges[p[0]]
        x, y, z = b.point(p[1], p[2])
        return (x, y + 0.012, z)

    def up(self, sp):
        if sp["on"] == "wall":
            th = sp["p"][0]
            return (-math.cos(th), 0.0, -math.sin(th))
        return (0.0, 1.0, 0.0)

    def _moved(self, sp, d):
        """Where it would be a distance d on along its heading: -> new params, or None if it can't go there."""
        t, p, h = self.tree, sp["p"], sp["head"]
        kind = sp["on"]
        if kind == "floor":
            x, z = p[0] + math.cos(h) * d, p[1] + math.sin(h) * d
            th = math.atan2(z, x)
            tun = t.in_tunnel(x, z)
            if math.hypot(x, z) > t.base_r(th, 0.2) - 0.45 or (tun and tun[0] > -0.6):
                return None
            return (x, z)
        if kind == "wall":
            th, y = p
            r = t.wall_r(th, y)
            th, y = th + math.cos(h) * d / r, y + math.sin(h) * d
            if not 0.3 < y < T.TOP - 2.0 or t.wall_r(th, y) - t.base_r(th, y) > 0.12 or t.knot_at(th, y):
                return None
            if abs((th - T.THETA_IN + math.pi) % math.tau - math.pi) < 0.22 and y < 2.2:       # (the tunnel's mouth)
                return None
            for s in t.ledge_turns(th):
                lh = t.ledge_h(s)
                if lh is not None and lh - 0.6 < y < lh + 0.2:             # (the ledge, where it meets the wall)
                    return None
            return (th % math.tau, y)
        if kind == "disc":
            k, x, z = p
            x, z = x + math.cos(h) * d, z + math.sin(h) * d
            if math.hypot(x, z) > self.web.discs[k].rim(math.atan2(z, x)) - 0.15:
                return None
            return (k, x, z)
        k, u, c = p
        b = self.web.bridges[k]
        u += (1 if math.cos(h) >= 0 else -1) * d / b.length
        if not 0.04 < u < 0.96:
            return None
        return (k, u, c)

    def forward(self, sp):
        here = self.pos(sp)
        q = self._moved(sp, 0.03)
        if q is None:
            sp2 = dict(sp, head=sp["head"] + math.pi)
            q2 = self._moved(sp2, 0.03)
            there = self.pos(sp, q2) if q2 else (here[0] + 0.01, here[1], here[2])
            return _norm(tuple(a - b for a, b in zip(here, there)))
        there = self.pos(sp, q)
        return _norm(tuple(b - a for a, b in zip(here, there)))

    # ---- a step -------------------------------------------------------------------------------------------------
    def pour_out(self, pos, floor, count=30):
        """A wrapped guest split open: her small ones pouring out of him, every way, across the floor - and gone."""
        rng = self.rng
        for _ in range(count):
            a = rng.uniform(0, math.tau)
            self.pouring.append({"x": pos[0] + math.cos(a) * 0.12, "z": pos[2] + math.sin(a) * 0.12, "y": floor,
                                 "drop": max(0.0, pos[1] - floor - 0.1) * rng.uniform(0.2, 1.0), "head": a,
                                 "speed": rng.uniform(1.4, 3.2), "life": rng.uniform(1.8, 4.2),
                                 "size": rng.uniform(0.06, 0.13), "anim": rng.uniform(0, 3)})

    def _pour(self, dt):
        keep = []
        for s in self.pouring:
            s["life"] -= dt
            if s["life"] <= 0:
                continue
            s["head"] += self.rng.gauss(0, 2.2) * dt
            x = s["x"] + math.cos(s["head"]) * s["speed"] * dt
            z = s["z"] + math.sin(s["head"]) * s["speed"] * dt
            if math.hypot(x, z) < self.tree.base_r(math.atan2(z, x), s["y"] + 0.3) - 0.25:
                s["x"], s["z"] = x, z
            else:
                s["head"] += math.pi
            s["drop"] = max(0.0, s["drop"] - dt * 4.0)          # (dropping from him to the floor first)
            s["anim"] += dt * s["speed"] / s["size"] * 0.7
            keep.append(s)
        self.pouring = keep

    def step(self, dt, eye, hurry=False, reach=0.0):
        rng = self.rng
        events = []
        self._pour(dt)
        scare = 3.4 if hurry else 2.2
        for sp in self.spiders:
            p = self.pos(sp)
            d = math.dist(p, eye)
            if d > LOST and sp["state"] != "flee":
                self._place(sp, eye)
                continue
            if sp["state"] != "flee" and (d < scare or (reach > 0 and d < reach * 0.45)):
                sp["state"], sp["until"] = "flee", rng.uniform(1.2, 2.4)
                sp["speed"] = rng.uniform(2.0, 2.8) * (0.7 + sp["size"] * 2)
                sp["head"] = self._away(sp, p, eye)
                events.append(("skitter", p, d))
            sp["until"] -= dt
            if sp["state"] == "rest":
                sp["anim"] += dt
                if sp["until"] <= 0:
                    sp["state"], sp["until"] = "go", rng.uniform(0.4, 2.4)
                    sp["speed"] = rng.uniform(0.35, 0.95) * (0.6 + sp["size"] * 2.5)
                    sp["head"] += rng.uniform(-1.3, 1.3)
                continue
            if sp["state"] == "go":
                sp["head"] += rng.gauss(0, 1.6) * dt
            elif sp["state"] == "flee" and d < 4.0:
                sp["head"] = self._away(sp, p, eye) + rng.gauss(0, 0.4) * dt
            dist = sp["speed"] * dt
            q = self._moved(sp, dist)
            if q is None:                                           # (in the way: off another way)
                sp["head"] += math.pi + rng.uniform(-0.9, 0.9)
                q = self._moved(sp, dist)
            if q is not None:
                sp["p"] = q
            sp["anim"] += dt * sp["speed"] / sp["size"] * 0.7          # (its legs keeping up with it)
            if sp["until"] <= 0:
                sp["state"], sp["until"] = "rest", rng.uniform(0.6, 4.5) if sp["state"] == "go" else rng.uniform(2, 6)
        return events

    def _away(self, sp, p, eye):
        """The heading on its surface that takes it most directly away from him."""
        best, far = sp["head"], -1.0
        for k in range(12):
            h = k / 12 * math.tau
            q = self._moved(dict(sp, head=h), 0.3)
            if q is None:
                continue
            dd = math.dist(self.pos(sp, q), eye)
            if dd > far:
                best, far = h, dd
        return best

    def _place(self, sp, eye):
        """Somewhere about him, on something, out of the lantern's reach (or as near that as can be found)."""
        rng, web = self.rng, self.web
        ex, ey, ez = eye
        for attempt in range(60):
            roll = rng.random()
            if roll < 0.45:
                sp["on"], sp["p"] = "wall", (rng.uniform(0, math.tau), max(0.4, ey + rng.uniform(-4, 5)))
            elif roll < 0.7 and ey < 7:
                th, r = rng.uniform(0, math.tau), rng.uniform(1.0, T.R0 - 1.2)
                sp["on"], sp["p"] = "floor", (math.cos(th) * r, math.sin(th) * r)
            elif roll < 0.85:
                k = 0 if abs(ey - web.loom.h) < abs(ey - web.crown.h) else 1
                d = web.discs[k]
                th = rng.uniform(0, math.tau)
                r = rng.uniform(0.3, d.rim(th) - 0.3)
                sp["on"], sp["p"] = "disc", (k, math.cos(th) * r, math.sin(th) * r)
            else:
                k = rng.randrange(len(web.bridges))
                sp["on"], sp["p"] = "strand", (k, rng.uniform(0.1, 0.9), rng.choice(CABLES))
            if sp["on"] == "wall" and self._moved(dict(sp, head=0.0), 0.0) is None:
                continue
            if sp["on"] == "floor" and self._moved(dict(sp, head=0.0), 0.0) is None:
                continue
            d = math.dist(self.pos(sp), eye)
            if NEAR <= d <= FAR or (attempt > 40 and d <= LOST):
                break
        sp["state"], sp["until"] = "rest", rng.uniform(0.5, 4.0)

    def near(self, eye, limit=18.0):
        out = []
        for s in self.pouring:
            y = self.tree.floor_at(s["x"], s["z"], s["y"] + 0.3) + 0.004 + s["drop"]
            if math.dist((s["x"], y, s["z"]), eye) <= limit:
                out.append(((s["x"], y, s["z"]), (math.cos(s["head"]), 0.0, math.sin(s["head"])), (0.0, 1.0, 0.0),
                            s["size"], "walk", s["anim"]))
        for sp in self.spiders:
            p = self.pos(sp)
            if math.dist(p, eye) > limit:
                continue
            clip = "idle" if sp["state"] == "rest" else "walk"
            out.append((p, self.forward(sp), self.up(sp), sp["size"], clip, sp["anim"]))
        return out
