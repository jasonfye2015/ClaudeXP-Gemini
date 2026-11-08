"""Ysmeine, the Weaver Below: her body in the den (phase 3a - before she ever speaks).

She is on the wall of the hollow, a leg-span of near seven units, and she keeps to the dark. Mostly she is across
the hollow from him and a little above, watching - eight red lights and a shape in the black. She keeps pace with him
as he climbs. Now and then she comes closer, to the very edge of his light, and leans out toward him, legs reaching -
and is gone again. When his lantern goes out she comes close and stays close. When he comes at her, she withdraws. When
the silk shakes hard (a fall, a slip, a scramble) she turns to him at once, and comes. She is seen in fragments: a leg
at the edge of the light, eyes in a gap, the web shifting under her weight.

    her = Mother(tree, rng)
    her.step(dt, night)       -> events: ("her", "glimpse"), ("her", "withdraw"), ("her", "near"), ("her", "turn")
    her.pose()                -> (position, forward, up, size, clip, t, lean) for drawing
    her.eyes()                -> (where her eyes are, how bright) - for the glow, and for the night to know she's looking
    her.moving                how fast she's going now, 0..1 (for the sound of her)

She walks the wall itself: (angle, height) on it, her body along it, her back to the hollow. Plain Python: the tests
watch where she goes."""
import math

from . import tree as T

SIZE = 6.75                      # (her leg-span, nose to tail with her legs)
EYES = (0.01, 0.19, 0.06)        # (where her eyes are on her, in the spider's own units)
CREEP, PACE, FLEE = 0.55, 1.3, 3.4
GLIMPSE_EVERY = (40.0, 80.0)
REST = 0.25                      # (how far her body stands off the wall)


def _wrap(a):
    return (a + math.pi) % math.tau - math.pi


class Mother:
    def __init__(self, tree, rng):
        self.tree, self.rng = tree, rng
        self.th, self.y = math.pi * 0.9, 13.5                # (half way up the hollow, to begin with)
        self.head = 0.0                      # (which way she faces on the wall: 0 round it, pi/2 up it)
        self.state = "watch"
        self.until = 0.0
        self.t = 0.0
        self.next_glimpse = rng.uniform(*GLIMPSE_EVERY)
        self.anim = 0.0
        self.clip = "idle"
        self.lean = 0.0                      # (0 flat to the wall .. 1 leaning out, reaching)
        self.moving = 0.0
        self.alpha = 0.0                     # (her eyes: how much they show)
        self.leaned = self.announced = False

    # ---- where she is --------------------------------------------------------------------------------------------
    def at(self, th=None, y=None):
        th = self.th if th is None else th
        y = self.y if y is None else y
        r = self.tree.base_r(th, y) - REST
        return (math.cos(th) * r, y, math.sin(th) * r)

    def _normal(self):
        return (-math.cos(self.th), 0.0, -math.sin(self.th))

    def _along(self, head):
        """A heading on the wall as a direction in the den."""
        e = (-math.sin(self.th), 0.0, math.cos(self.th))
        return tuple(math.cos(head) * a + math.sin(head) * b for a, b in zip(e, (0.0, 1.0, 0.0)))

    def pose(self):
        up = self._normal()
        lean = self.lean
        x, y, z = self.at()
        p = (x + up[0] * lean * 0.9, y, z + up[2] * lean * 0.9)
        f = self._along(self.head)
        if lean > 0:                                    # (leaning out: her front lifts off the wall, toward him)
            f = tuple(a * (1 - lean * 0.55) + b * lean * 0.55 for a, b in zip(f, up))
            n = math.sqrt(sum(c * c for c in f)) or 1.0
            f = tuple(c / n for c in f)
        return p, f, up, SIZE, self.clip, self.anim, lean

    def eyes(self):
        """Where her eyes are, and how much they show."""
        p, f, up, s, _c, _t, _l = self.pose()
        right = (up[1] * f[2] - up[2] * f[1], up[2] * f[0] - up[0] * f[2], up[0] * f[1] - up[1] * f[0])
        pos = tuple(p[i] + (right[i] * EYES[0] + up[i] * EYES[1] + f[i] * EYES[2]) * s for i in range(3))
        return pos, self.alpha

    # ---- where she wants to be -----------------------------------------------------------------------------------
    def _target(self, night):
        """Across the hollow from him and above, watching; or close, at the edge of his light."""
        ex, ey, ez = night.eye
        th_him = math.atan2(ez, ex)
        reach = night.lantern_reach()[0] if night.lantern and night.lamp.state != "out" else 0.0
        if self.state in ("near", "glimpse"):
            gap = max(3.4, reach * 0.95) if self.state == "glimpse" else 3.6     # (her size: she never quite touches him)
            r = self.tree.base_r(th_him, ey)
            d_wall = max(0.3, r - math.hypot(ex, ez))
            off = math.sqrt(max(0.0, gap * gap - d_wall * d_wall)) / max(1.0, r)
            side = 1.0 if _wrap(self.th - th_him) >= 0 else -1.0
            return th_him + side * min(1.2, off + 0.15), ey + (0.6 if self.state == "glimpse" else 1.2)
        return th_him + math.pi + 0.35 * math.sin(self.t * 0.05), max(ey + 2.2, 12.5)   # (high, unless he is)

    # ---- a step ---------------------------------------------------------------------------------------------------
    def step(self, dt, night):
        self.t += dt
        rng = self.rng
        out = []
        ex, ey, ez = night.eye
        me = self.at()
        d = math.dist(me, night.eye)
        dark = not night.lantern or night.lamp.state == "out"
        reach = night.lantern_reach()[0] if not dark else 0.0
        # what she means to do
        if night.tremor > 2.2 and self.state not in ("near", "glimpse", "withdraw"):
            self.state, self.until = "near", self.t + rng.uniform(6, 10)         # (she felt that)
            out.append(("her", "turn"))
        if dark and self.state in ("watch",):
            self.state, self.until = "near", self.t + 1e9
            out.append(("her", "near"))
        if not dark and self.state == "near" and self.until > self.t + 1e8:
            self.state, self.until = "watch", 0.0                                  # (light again: back to the dark)
            self.next_glimpse = max(self.next_glimpse, self.t + rng.uniform(15, 30))
        if self.state == "watch" and self.t >= self.next_glimpse:
            self.state, self.until = "glimpse", self.t + 40.0              # (as long as it takes her to get there)
            self.leaned = self.announced = False
            self.next_glimpse = self.t + rng.uniform(*GLIMPSE_EVERY)
        if self.state == "glimpse" and self.lean > 0.9 and not self.leaned:
            self.leaned = True
            self.until = self.t + rng.uniform(2.5, 4.0)                    # (there: a long moment, leaning out, then gone)
        if self.state in ("near", "glimpse") and self.t >= self.until:
            self.state, self.until = "withdraw", self.t + rng.uniform(3, 5)
            out.append(("her", "withdraw"))
        if self.state == "watch" and not dark and d < max(3.5, reach * 0.7):      # (he comes at her: she goes)
            self.state, self.until = "withdraw", self.t + rng.uniform(3, 5)
            out.append(("her", "withdraw"))
        if self.state == "withdraw" and self.t >= self.until:
            self.state = "watch"
        # where that takes her
        if self.state == "withdraw":
            th_t, y_t = math.atan2(ez, ex) + math.pi, ey + 3.0
            speed = FLEE
        else:
            th_t, y_t = self._target(night)
            speed = PACE
        y_t = max(2.0, min(T.TOP - 2.5, y_t))
        r = self.tree.base_r(self.th, self.y)
        dth = _wrap(th_t - self.th) * r                       # (round the wall, the short way: in units)
        dy = y_t - self.y
        gap = math.hypot(dth, dy)
        if self.state in ("near", "glimpse") and gap < 3.0:
            speed = CREEP                                        # (the last of the way: slowly)
        step = min(gap, speed * dt)
        if gap > 0.15:
            self.th += dth / gap * step / r
            self.y += dy / gap * step
            want = math.atan2(dy, dth)
            self.head += _wrap(want - self.head) * min(1.0, dt * 2.5)
            self.moving = min(1.0, step / dt / FLEE) if dt > 0 else 0.0
            self.clip = "walk"
            self.anim += dt * step / dt / SIZE * 3.0 if dt > 0 else 0.0
        else:
            to_him = math.atan2(ey - self.y, _wrap(math.atan2(ez, ex) - self.th) * r)
            self.head += _wrap(to_him - self.head) * min(1.0, dt * 1.2)            # (still: facing him)
            self.moving = 0.0
            self.clip = "idle"
            self.anim += dt
        # leaning out toward him, at the edge of the light
        want_lean = 1.0 if self.state == "glimpse" and (gap < 1.0 or self.announced) else 0.0
        if self.state == "near" and dark and gap < 1.0:
            want_lean = 0.5
        if want_lean > 0.9 and not self.announced:
            self.announced = True
            out.append(("her", "glimpse"))
        self.lean += (want_lean - self.lean) * min(1.0, dt * (0.8 if want_lean > self.lean else 3.0))
        if self.lean > 0.1:
            self.clip = "attack"
            self.anim = 0.35 + self.lean * 0.3                                    # (the reach: held, not struck)
        # her eyes: on him, more the darker it is
        look = 1.0 if self.state != "withdraw" else 0.2
        self.alpha += (look * (1.0 if d > 3.0 or dark else 0.6) - self.alpha) * min(1.0, dt * 1.5)
        return out
