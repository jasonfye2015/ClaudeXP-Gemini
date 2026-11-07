"""The night: Claude inside the Hollow Oak, from dusk on - where he stands, where he looks, his lantern, the clock, and
(for now) the only sign of her: eyes, high in the dark, watching him climb.

    night = Night()
    night.step(dt, inp)            (inp: an Input - forward, strafe, yaw, pitch, hurry)
    night.eye                      where he looks from
    night.events                   what happened, for the view: ("place", name, line), ...

Plain Python: the view draws it, the tests walk it."""
import math
import random

from . import tree as T

EYE = 0.62
RADIUS = 0.24
WALK = 1.35                    # (unhurried: she feels every step)
HURRY = 2.3                    # (a hurried walk - never a run, in here)
GRAVITY = 16.0
DUSK = 19 * 60.0               # (the clock: minutes from midnight)
DAWN = 30 * 60.0 + 30.0        # (half past six in the morning)
CLOCK_RATE = 0.07              # (minutes of the night a real second: dusk to dawn in about two and three-quarter hours)

PLACES = {
    "tunnel": ("The roots", "A way in through the roots of the Hollow Oak. Dry leaves, and something that isn't wind."),
    "hollow": ("The Hollow", "The inside of the tree, going up and up into the dark. A ledge winds up the wall."),
    "gallery": ("The gallery", "A chamber in the wood. The walls here are hung with something wrapped in silk."),
    "larder": ("The larder", "A low chamber that smells of old honey and older meat."),
    "high hollow": ("The high hollow", "Wind moves through the wood here. You are very far from the ground."),
    "crown": ("The crown", "The top of the oak, broken open to the sky. The moon is very close."),
}


class Input:
    def __init__(self):
        self.forward = 0.0
        self.strafe = 0.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.hurry = False


class Night:
    def __init__(self, seed=None):
        self.tree = T.Tree()
        self.rng = random.Random(seed)
        sx, sz, facing = self.tree.start
        self.x, self.z = sx, sz
        self.y = self.tree.floor_at(sx, sz, 1.0)
        self.yaw = math.atan2(math.cos(facing), -math.sin(facing))
        self.pitch = 0.0
        self.vy = 0.0
        self.time = 0.0
        self.clock = DUSK
        self.lantern = True
        self.events = []
        self.seen = set()
        self.place = None
        self.moved = 0.0
        self.perches = self._perches()
        self.perch = 0
        self.eye_alpha = 0.0
        self.eye_gone_until = 0.0

    # ---- where he is --------------------------------------------------------------------------------------------
    @property
    def eye(self):
        return (self.x, self.y + EYE, self.z)

    def where(self):
        t = self.tree
        if t.in_tunnel(self.x, self.z) and t.in_tunnel(self.x, self.z)[0] > 0.2:
            return "tunnel"
        return t.landing_at(self.x, self.z, self.y) or "hollow"

    def clock_words(self):
        m = int(self.clock + 1e-6) % (24 * 60)
        h = m // 60
        return f"{(h - 1) % 12 + 1}:{m % 60:02d} {'pm' if 12 <= h < 24 else 'am'}"

    # ---- a step ------------------------------------------------------------------------------------------------
    def step(self, dt, inp):
        dt = min(dt, 0.05)
        self.time += dt
        self.clock = min(DAWN, self.clock + dt * CLOCK_RATE)
        self.yaw, self.pitch = inp.yaw, max(-1.45, min(1.45, inp.pitch))
        self._move(dt, inp)
        p = self.where()
        if p != self.place:
            self.place = p
            if p not in self.seen:
                self.seen.add(p)
                name, line = PLACES[p]
                self.events.append(("place", name, line))
        self._watch(dt)

    def _move(self, dt, inp):
        t = self.tree
        fwd, side = inp.forward, inp.strafe
        n = math.hypot(fwd, side)
        if n > 1:
            fwd, side = fwd / n, side / n
        speed = HURRY if inp.hurry else WALK
        sy, cy = math.sin(self.yaw), math.cos(self.yaw)
        dx = (sy * fwd + cy * side) * speed * dt
        dz = (-cy * fwd + sy * side) * speed * dt
        on_ground = self.y <= t.floor_at(self.x, self.z, self.y) + 0.01
        for mx, mz in ((dx, dz), (dx, 0.0), (0.0, dz)):        # (straight on, or sliding along what's in the way)
            if not (mx or mz):
                continue
            nx, nz = self.x + mx, self.z + mz
            f = t.floor_at(nx, nz, self.y)
            if f > self.y + T.STEP:
                continue
            if t.can_stand(nx, nz, max(self.y, f) if on_ground else self.y, RADIUS):
                self.x, self.z = nx, nz
                self.moved += math.hypot(mx, mz)
                break
        f = t.floor_at(self.x, self.z, self.y)
        if self.y > f + 0.01:                                 # (falling: off the ledge's edge)
            self.vy -= GRAVITY * dt
            self.y = max(f, self.y + self.vy * dt)
            if self.y == f:
                if self.vy < -9:
                    self.events.append(("fall", -self.vy))
                self.vy = 0.0
        else:
            self.y, self.vy = f, 0.0

    # ---- her eyes ----------------------------------------------------------------------------------------------
    def _perches(self):
        """Places high on the ledge, away from the wall a little, where something could sit and watch."""
        t = self.tree
        out = []
        for k in range(14):
            s = 1.2 + k * (t.s_end - 1.5) / 13
            a = t.theta_of(s)
            h = t.ledge_h(s)
            r = t.base_r(a, h + 0.5) - 0.5
            out.append((math.cos(a) * r, h + 1.1, math.sin(a) * r))
        return out

    def _watch(self, dt):
        """The eyes sit on a perch above him; when he comes within eight units, they're gone - and turn up
        again, higher, a while later."""
        ex, ey, ez = self.eye
        if self.time < self.eye_gone_until:
            self.eye_alpha = max(0.0, self.eye_alpha - dt * 3)
            return
        px, py, pz = self.perches[self.perch]
        d = math.dist((px, py, pz), (ex, ey, ez))
        if d < 8.0 or py < ey + 1.5:
            self.eye_alpha = max(0.0, self.eye_alpha - dt * 4)
            if self.eye_alpha == 0.0:
                above = [k for k, p in enumerate(self.perches) if p[1] > ey + 3 and math.dist(p, (ex, ey, ez)) > 10]
                self.perch = self.rng.choice(above) if above else self.perch
                self.eye_gone_until = self.time + self.rng.uniform(6, 14)
                self.events.append(("eyes_gone",))
        else:
            self.eye_alpha = min(1.0, self.eye_alpha + dt * 0.4)

    def eyes(self):
        if self.eye_alpha <= 0.01:
            return []
        blink = 0.15 if (self.time * 0.37) % 4.0 < 0.12 else 1.0
        return [{"pos": self.perches[self.perch], "alpha": self.eye_alpha * blink}]
