"""Now and then, something small runs across his eyes: a little spider crossing the whole view in a second or less,
in from one edge and out at another - every twenty to thirty seconds, sometimes two at once, never by the same way.

    crawlers = Crawlers(rng)
    crawlers.step(dt)        -> events: ("crawler", how many) when they set off
    crawlers.active()        -> [(u, v, du, dv, size, t)] - where each is on the screen (0..1 across, 0..1 up), which way
                                it's going, its size (a share of the screen's height) and its legs' time

Plain Python: the view draws them, the tests time them."""
import random

EVERY = (20.0, 30.0)
TWO = 0.3                       # (how often two come at once)
SIZE = (0.03, 0.085)
TIME = (0.55, 1.0)


def _edge_point(rng, edge):
    k = rng.uniform(0.08, 0.92)
    return ((0.0, k), (1.0, k), (k, 0.0), (k, 1.0))[edge]


class Crawlers:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.t = 0.0
        self.next = self.rng.uniform(*EVERY)
        self.runs = []                  # {from, ctrl, to, born, time, size}

    def step(self, dt):
        self.t += dt
        self.runs = [r for r in self.runs if self.t - r["born"] < r["time"]]
        if self.t < self.next:
            return []
        self.next = self.t + self.rng.uniform(*EVERY)
        count = 2 if self.rng.random() < TWO else 1
        used = []
        for _ in range(count):
            self.runs.append(self._run(used))
        return [("crawler", count)]

    def _run(self, used):
        rng = self.rng
        for _ in range(40):                                  # (a way across, not near one already taken)
            a, b = rng.sample(range(4), 2)                    # (in at one edge, out at another)
            p, q = _edge_point(rng, a), _edge_point(rng, b)
            if ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5 < 0.7:
                continue
            if all(((p[0] - s[0]) ** 2 + (p[1] - s[1]) ** 2) ** 0.5 > 0.25 and
                   ((q[0] - e[0]) ** 2 + (q[1] - e[1]) ** 2) ** 0.5 > 0.25 for s, e in used):
                break
        used.append((p, q))
        size = rng.uniform(*SIZE)
        out = ((-1, 0), (1, 0), (0, -1), (0, 1))              # (start and end just off the screen: in, across, gone)
        p = (p[0] + out[a][0] * size * 0.8, p[1] + out[a][1] * size * 0.8)
        q = (q[0] + out[b][0] * size * 0.8, q[1] + out[b][1] * size * 0.8)
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        nx, ny = -(q[1] - p[1]), q[0] - p[0]
        bend = rng.uniform(-0.3, 0.3)                         # (never quite straight)
        return {"from": p, "ctrl": (mx + nx * bend, my + ny * bend), "to": q, "born": self.t,
                "time": rng.uniform(*TIME), "size": size, "wiggle": rng.uniform(0, 6.28)}

    def scurry(self, size):
        """One that was on his face (he walked into it): from near the middle of his view, off by a random way."""
        rng = self.rng
        p = (0.5 + rng.uniform(-0.12, 0.12), 0.48 + rng.uniform(-0.1, 0.1))
        edge = rng.randrange(4)
        s = rng.uniform(0.085, 0.12) * (0.8 + size * 4)            # (close: bigger than the ones that cross)
        q = _edge_point(rng, edge)
        out = ((-1, 0), (1, 0), (0, -1), (0, 1))[edge]
        q = (q[0] + out[0] * s * 0.8, q[1] + out[1] * s * 0.8)
        ctrl = ((p[0] + q[0]) / 2 + rng.uniform(-0.12, 0.12), (p[1] + q[1]) / 2 + rng.uniform(-0.12, 0.12))
        self.runs.append({"from": p, "ctrl": ctrl, "to": q, "born": self.t, "time": rng.uniform(0.45, 0.75),
                          "size": s, "wiggle": rng.uniform(0, 6.28)})

    def active(self):
        out = []
        for r in self.runs:
            s = min(1.0, (self.t - r["born"]) / r["time"])
            (ax, ay), (cx, cy), (bx, by) = r["from"], r["ctrl"], r["to"]
            u = (1 - s) ** 2 * ax + 2 * (1 - s) * s * cx + s * s * bx
            v = (1 - s) ** 2 * ay + 2 * (1 - s) * s * cy + s * s * by
            du = 2 * (1 - s) * (cx - ax) + 2 * s * (bx - cx)
            dv = 2 * (1 - s) * (cy - ay) + 2 * s * (by - cy)
            out.append((u, v, du, dv, r["size"], (self.t - r["born"]) * 6.0 + r["wiggle"]))
        return out
