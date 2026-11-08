"""Supper: when health, sanity or consciousness gives out. He collapses where he stands; the lantern falls and breaks
and its flame dies on the ground. They come - onto him, over his face, laying silk across his eyes until he can hardly
see. Then he's dragged, in pulls, to the middle of the hollow's floor; turned, lifted by the feet, and drawn up, upside
down, half the height of the trunk, swinging. Then black - and, small, "Ending 1 of 6: Supper".

    death = Death(night, cause, rng)
    death.step(dt, night)       -> events ("lantern", "break"), ("death", "drag"), ("death", "lift"), ("death", "end")
    death.cover()               -> [(u, v, du, dv, size, t)] the spiders on his face (as Crawlers.active())
    death.webs                  -> what's been laid across his eyes: [("strand", (u0, v0), (u1, v1), sag) |
                                   ("orb", (u, v), radius, turn)], with how far each is drawn in ("drawn")
    death.black                 0..1, the end coming down
    death.done                  over: the ending's line is showing
Plain Python: it moves the night's own Claude - where he is, how he lies, which way is up."""
import math

from . import tree as T

COLLAPSE = 1.4
BREAK = 0.55
COVER_END = 7.4                 # (by now his eyes are mostly silk)
DRAG_END = 12.4
LIFT_END = 19.4
FADE_END = 21.4
PULLS = 5
SPIDERS = 46
WEBS = 70
ENDING = ("Ending 1 of 6: Supper", "Wrapped, and hung, and kept for later.")


def _ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


class Death:
    def __init__(self, night, cause, rng):
        self.cause, self.rng = cause, rng
        self.t = 0.0
        self.x0, self.y0, self.z0 = night.x, night.y, night.z
        self.yaw0, self.pitch0 = night.yaw, night.pitch
        f = (math.sin(night.yaw), -math.cos(night.yaw))
        self.lamp_at = (night.x + f[0] * 0.35, night.y + 0.03, night.z + f[1] * 0.35)    # (where the lantern lands)
        self.broke = False
        self.spiders = []
        self.webs = []
        self.black = 0.0
        self.done = False
        self.said = set()
        self.centre_y = night.tree.ground(0.0, 0.0)
        self.top = T.TOP * 0.5

    def flame(self):
        """The broken lantern's flame on the ground, dying: 0..1."""
        if not self.broke:
            return 0.0
        k = (self.t - BREAK) / 2.6
        return max(0.0, 1.0 - k) * (0.6 + 0.4 * math.sin(self.t * 23.0) * math.sin(self.t * 7.0))

    def step(self, dt, night):
        self.t += dt
        t = self.t
        out = []
        if not self.broke and t >= BREAK:
            self.broke = True
            night.lantern = False
            out.append(("lantern", "break"))
        self._pose(night)
        self._cover(dt)
        for name, at in (("drag", COVER_END), ("lift", DRAG_END), ("end", FADE_END)):
            if t >= at and name not in self.said:
                self.said.add(name)
                out.append(("death", name))
        self.black = _ease((t - LIFT_END) / (FADE_END - LIFT_END))
        self.done = t >= FADE_END
        return out

    def _pose(self, night):
        """Where he is, and how he lies, at this moment of it."""
        t = self.t
        if t < COVER_END:                                               # (down, on his side, and there he stays)
            k = _ease(t / COLLAPSE)
            night.x, night.y, night.z = self.x0, self.y0, self.z0
            night.eye_h = 0.62 * (1 - k) + 0.1 * k
            night.roll = 1.25 * k
            night.pitch = self.pitch0 * (1 - k) - 0.25 * k + 0.02 * math.sin(t * 1.3)
            night.yaw = self.yaw0
        elif t < DRAG_END:                                              # (dragged by the feet, in pulls, onto his back)
            f = (t - COVER_END) / (DRAG_END - COVER_END) * PULLS
            n = min(PULLS - 1, int(f))
            k = (n + _ease((f - n) * 1.6)) / PULLS
            night.x = self.x0 * (1 - k)
            night.z = self.z0 * (1 - k)
            night.y = max(self.y0 * (1 - k) + self.centre_y * k, night.tree.ground(night.x, night.z))  # (let down, if high)
            night.eye_h = 0.1
            night.roll = 1.25 * (1 - _ease(f / 2))
            night.pitch = -0.25 + 1.45 * _ease(f / 2) + 0.06 * math.sin(f * math.pi * 2)   # (jerked; staring up)
            night.yaw = self.yaw0 + 0.15 * math.sin(f * 2.1)
        else:                                                           # (turned, lifted by the feet, drawn up, swinging)
            u = t - DRAG_END
            turn = _ease(u / 1.6)
            rise = _ease((u - 0.8) / (LIFT_END - DRAG_END - 1.0))
            swing = math.sin(u * 1.9) * (0.15 + 0.55 * rise)
            night.x = swing
            night.z = 0.25 * math.sin(u * 1.3)
            night.y = self.centre_y + 0.7 * turn + (self.top - self.centre_y - 0.7) * rise
            night.eye_h = 0.1 - 0.72 * turn                             # (his head below his feet)
            night.roll = math.pi * turn
            night.pitch = 1.2 * (1 - turn) - 0.15 * turn + 0.12 * math.sin(u * 1.9 + 0.5)
            night.yaw = self.yaw0 + 0.5 * math.sin(u * 0.45) + u * 0.05

    def _cover(self, dt):
        """They come onto his face, more and more; and lay their silk across his eyes."""
        rng, t = self.rng, self.t
        want = int(SPIDERS * min(1.0, max(0.0, (t - 0.9) / 6.0)))
        while len(self.spiders) < want:
            edge = rng.randrange(4)
            k = rng.uniform(0.05, 0.95)
            u, v = ((-0.05, k), (1.05, k), (k, -0.05), (k, 1.05))[edge]
            self.spiders.append({"u": u, "v": v, "head": math.atan2(0.5 - v, 0.5 - u) + rng.uniform(-0.8, 0.8),
                                 "speed": rng.uniform(0.06, 0.22), "size": rng.uniform(0.035, 0.11),
                                 "anim": rng.uniform(0, 5), "rest": 0.0})
        for s in self.spiders:
            if s["rest"] > 0:
                s["rest"] -= dt
                continue
            s["head"] += rng.gauss(0, 2.0) * dt
            s["u"] += math.cos(s["head"]) * s["speed"] * dt
            s["v"] += math.sin(s["head"]) * s["speed"] * dt
            if not 0.03 < s["u"] < 0.97 or not 0.03 < s["v"] < 0.97:      # (they stay on him)
                s["head"] = math.atan2(0.5 - s["v"], 0.5 - s["u"]) + rng.uniform(-0.6, 0.6)
            s["anim"] += dt * s["speed"] * 40
            if rng.random() < dt * 0.4:
                s["rest"] = rng.uniform(0.3, 1.8)
        want = int(WEBS * min(1.0, max(0.0, (t - 1.6) / (COVER_END - 1.6))))
        while len(self.webs) < want:
            if rng.random() < 0.7:
                a = (rng.uniform(-0.1, 1.1), rng.uniform(-0.1, 1.1))
                b = (rng.uniform(-0.1, 1.1), rng.uniform(-0.1, 1.1))
                self.webs.append({"kind": "strand", "a": a, "b": b, "sag": rng.uniform(-0.12, 0.12), "born": t})
            else:
                self.webs.append({"kind": "orb", "c": (rng.uniform(0.1, 0.9), rng.uniform(0.1, 0.9)),
                                  "r": rng.uniform(0.08, 0.22), "turn": rng.uniform(0, math.tau), "born": t})
        for w in self.webs:
            w["drawn"] = min(1.0, (t - w["born"]) / 0.6)                 # (laid, not appearing)

    def cover(self):
        return [(s["u"], s["v"], math.cos(s["head"]), math.sin(s["head"]), s["size"], s["anim"])
                for s in self.spiders]
