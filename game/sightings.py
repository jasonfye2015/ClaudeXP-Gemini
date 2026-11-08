"""Her, between her scenes (polish 9c): seen in pieces, and gone again. Beside her leaning out at the edge of his light
(game/mother.py's glimpse), now and then:

    cross     a shape crossing the wall above him, fast, the way she does - only when he's near enough the wall for
              the lantern to catch her
    legs      legs drawn back past the edge of the light, quick, at his side
    behind    he turns round fast - and she's there, close; the lantern stutters, and she isn't
    thrum     while she moves near him, her web thrums with it: a low hum, the silk shivering

    s = Sightings(rng)
    s.step(dt, night) -> events: ("sight", kind)
    s.thrum           0..1, her web shivering with her moving (for the silk, and the hum)
Never in her scenes, never while she hunts, never in the first minute. Plain Python: the tests watch for her."""
import math

EVERY = (70.0, 150.0)
BEHIND_EVERY = 150.0
BEHIND_FOR = 0.85
TURN = 2.2                     # (radians turned in TURN_IN seconds: round, fast)
TURN_IN = 0.7


def _wrap(a):
    return (a + math.pi) % math.tau - math.pi


class Sightings:
    def __init__(self, rng):
        self.rng = rng
        self.t = 0.0
        self.next = rng.uniform(*EVERY)
        self.behind_ok = 60.0
        self.yaws = []                        # [(t, yaw)]: which way he's been looking, lately
        self.behind_until = None
        self.thrum = 0.0
        self.seen = []

    def step(self, dt, night):
        self.t += dt
        out = []
        her = night.her
        self.yaws.append((self.t, night.yaw))
        self.yaws = [y for y in self.yaws if self.t - y[0] <= TURN_IN]
        near = math.dist(her.at(), night.eye)
        want = min(1.0, her.moving * max(0.0, 1.0 - near / 12.0) * 1.6)     # (her web, shivering as she goes)
        self.thrum += (want - self.thrum) * min(1.0, dt * 3.0)
        if self.behind_until is not None:                                   # (there, behind him - and then not)
            if self.t >= self.behind_until:
                self.behind_until = None
                lamp = night.lamp
                lamp.sputter_until = lamp.t + 0.35                          # (the light stutters: she's gone in it)
                her.unstage()
            return out
        quiet = night.quiet or night.dying is not None or night.ending is not None or self.t < 60.0 or \
            her.state in ("hunt", "strike") or her.staged is not None or getattr(night.afflict, "busy", False)
        if quiet:
            return out
        if self._turned() and self.t >= self.behind_ok and self.rng.random() < 0.5:
            if self._behind(night):
                self.behind_ok = self.t + BEHIND_EVERY
                self.seen.append("behind")
                night.body.startle += 30.0
                out.append(("sight", "behind"))
                return out
        if self.t < self.next or her.state != "watch":
            return out
        fasc = night.moods.fascination / 100.0
        hunger = night.moods.hunger / 100.0
        self.next = self.t + self.rng.uniform(*EVERY) * (1.25 - 0.4 * fasc - 0.3 * hunger)
        kind = self.rng.choice(("cross", "cross", "legs"))
        if kind == "cross" and self._cross(night):
            self.seen.append("cross")
            out.append(("sight", "cross"))
        elif self._legs(night):
            self.seen.append("legs")
            out.append(("sight", "legs"))
        return out

    def _turned(self):
        if len(self.yaws) < 2:
            return False
        return abs(_wrap(self.yaws[-1][1] - self.yaws[0][1])) >= TURN or \
            sum(abs(_wrap(b[1] - a[1])) for a, b in zip(self.yaws, self.yaws[1:])) >= TURN

    def _cross(self, night):
        """Above him, along the wall, fast - started out of his sight, so she's simply there, going."""
        ex, ey, ez = night.eye
        th = math.atan2(ez, ex)
        r = night.tree.base_r(th, ey)
        if r - math.hypot(ex, ez) > 3.8:                                     # (too far from the wall: nothing to see)
            return False
        side = self.rng.choice((-1.0, 1.0))
        her = night.her
        her.th, her.y = th - side * 1.1, min(ey + 3.2, 27.0)
        her.state, her.cross_to, her.until = "cross", th + side * 1.1, her.t + 6.0
        her.head = 0.0 if side > 0 else math.pi
        return True

    def _legs(self, night):
        """A glimpse, cut short: to the edge of his light, a reach of legs - and drawn back, quick."""
        her = night.her
        her.state, her.until = "glimpse", her.t + 40.0
        her.leaned = her.announced = False
        her.quick = True
        return True

    def _behind(self, night):
        """Where he's looking now, close: her, still, facing him. (If there's floor there to hold her.)"""
        ex, ey, ez = night.eye
        fx, fz = math.sin(night.yaw), -math.cos(night.yaw)
        for d in (3.0, 2.5):
            x, z = ex + fx * d, ez + fz * d
            f = night.floor_at(x, z, night.y + 0.5)
            if abs(f - night.y) < 0.6 and night.tree.can_stand(x, z, f, 0.6, 0.8):
                night.her.stage((x, f, z), (-fx, 0.0, -fz))
                self.behind_until = self.t + BEHIND_FOR
                return True
        return False
