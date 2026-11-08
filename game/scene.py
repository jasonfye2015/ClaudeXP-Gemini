"""Her scenes (phase 3d): a turning point, taken out of his hands. The frame letterboxes; the view goes dark a moment
while she takes her place before him; then a composed camera holds on her - low, a little to one side of him, looking
up at her - drifting slowly. The night goes on (her hunger with it: stalling costs, as it always does), but nothing
small drops onto him while she talks. Between her lines, small motion: her breathing, a leg shifting, her small ones
crossing her back.

    scene = Scene(night, "audience")
    scene.step(dt)              moves it on: in (letterbox, the dark, her placed) -> talk -> out -> done
    scene.ready                 her place taken, the camera set: talk may begin
    scene.end()                 the talk is over: she goes, the frame opens
    scene.done
    scene.camera()              -> (eye, yaw, pitch) for the renderer while it lasts
    scene.box, scene.dim        the letterbox (0..1) and the dark (0..1), for the view
    scene.riders                her small ones on her back: [(position, forward, up, size, clip, t)]
Plain Python: the tests watch it."""
import math

from .mother import EYES

IN, CUT = 0.9, 0.55             # (the letterbox closing; the dark, down and up again)
GAP = 2.9                       # (how far before him she settles)


def _norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


class Scene:
    def __init__(self, night, name, rng=None):
        import random
        self.night, self.name = night, name
        self.rng = rng or random.Random()
        self.t = 0.0
        self.phase = "in"
        self.box = 0.0
        self.dim = 0.0
        self.ready = False
        self.done = False
        self.placed = False
        self.riders = []
        self._out_t = 0.0
        self._next_rider = 1.5
        self._shift = 4.0
        night.quiet = True                                   # (nothing small onto him while she talks)

    # ---- where she goes, and where we look from ---------------------------------------------------------------------
    def _place(self):
        """Before him, on whatever he stands on (her loom, mostly), facing him."""
        n = self.night
        her = n.her
        fx, fz = math.sin(n.yaw), -math.cos(n.yaw)
        t = n.tree
        x, z = n.x + fx * GAP, n.z + fz * GAP
        r = math.hypot(x, z)
        lim = t.base_r(math.atan2(z, x), n.y + 0.5) - 1.8           # (inside the hollow: her legs not through the wall)
        if r > lim:
            x, z = x * lim / r, z * lim / r
        y = n.floor_at(x, z, n.y + 0.3)
        face = _norm((n.x - x, 0.0, n.z - z))
        her.stage((x, y, z), face)
        n.yaw = math.atan2(x - n.x, -(z - n.z))                  # (and he turns to her)
        self.her_at = (x, y, z)
        self.placed = True

    def camera(self):
        """Low, a little to one side of him and behind, looking up at her face; drifting slowly."""
        n = self.night
        hx, hy, hz = self.her_at
        ex, ey, ez = n.x, n.y + n.eye_h, n.z
        to = _norm((hx - ex, 0.0, hz - ez))
        side = (-to[2], 0.0, to[0])
        if (ex + side[0]) ** 2 + (ez + side[2]) ** 2 > ex * ex + ez * ez:   # (on the hollow's side of him, not the wall's)
            side = (-side[0], 0.0, -side[2])
        drift = math.sin(self.t * 0.11) * 0.35
        breath = math.sin(self.t * 1.45) * 0.012
        cx = ex - to[0] * 0.45 + side[0] * (0.8 + drift)
        cz = ez - to[2] * 0.45 + side[2] * (0.8 + drift)
        cy = ey - 0.12 + breath
        tree = n.tree
        if not tree.can_stand(cx, cz, n.y, 0.15, 0.3):            # (never through the wall: his own eye, then)
            cx, cz = ex, ez
        p, f, up, size, *_ = n.her.pose()
        eyes = tuple(p[i] + up[i] * EYES[1] * size * 0.9 for i in range(3))
        dx, dy, dz = eyes[0] - cx, eyes[1] - 0.25 - cy, eyes[2] - cz
        yaw = math.atan2(dx, -dz)
        pitch = math.atan2(dy, math.hypot(dx, dz))
        return (cx, cy, cz), yaw, pitch

    # ---- a step -------------------------------------------------------------------------------------------------
    def step(self, dt):
        self.t += dt
        if self.phase == "in":
            self.box = min(1.0, self.t / IN)
            if self.t < CUT:
                self.dim = self.t / CUT
            else:
                if not self.placed:
                    self._place()
                self.dim = max(0.0, 1.0 - (self.t - CUT) / CUT)
            if self.t >= CUT * 2 and self.box >= 1.0:
                self.phase, self.ready = "talk", True
        elif self.phase == "talk":
            self._small_motion(dt)
        elif self.phase == "out":
            k = self.t - self._out_t
            self.dim = min(1.0, k / CUT) if k < CUT else max(0.0, 1.0 - (k - CUT) / CUT)
            if k >= CUT and self.night.her.staged is not None:
                self.night.her.unstage()                         # (gone, into the dark, while the eye was shut)
                self.riders.clear()
            self.box = max(0.0, 1.0 - max(0.0, k - CUT) / IN)
            if k >= CUT + IN:
                self.done = True
                self.night.quiet = False
        for r in self.riders:
            r["u"] += r["v"] * dt
        self.riders = [r for r in self.riders if r["u"] < 1.0]

    def end(self):
        if self.phase != "out":
            self.phase, self._out_t = "out", self.t

    def _small_motion(self, dt):
        """Her small ones crossing her back, now and then; a leg shifting."""
        her = self.night.her
        if self.t >= self._next_rider:
            self._next_rider = self.t + self.rng.uniform(4.0, 9.0)
            self.riders.append({"u": 0.0, "v": self.rng.uniform(0.12, 0.25), "side": self.rng.uniform(-0.25, 0.25),
                                "size": self.rng.uniform(0.07, 0.11), "anim": 0.0})
        for r in self.riders:
            r["anim"] += dt * 6
        if self.t >= self._shift:
            self._shift = self.t + self.rng.uniform(5.0, 11.0)
            her.shift = 0.9                                    # (a leg moved, and set down)

    def rider_poses(self):
        """Her small ones on her back, from her tail toward her head."""
        if not self.riders:
            return []
        p, f, up, size, *_ = self.night.her.pose()
        right = (up[1] * f[2] - up[2] * f[1], up[2] * f[0] - up[0] * f[2], up[0] * f[1] - up[1] * f[0])
        out = []
        for r in self.riders:
            along = (r["u"] - 0.55) * size * 0.55
            hump = 0.33 * size * (1.0 - (2 * r["u"] - 1.1) ** 2 * 0.6)          # (over the curve of her)
            pos = tuple(p[i] + f[i] * along + up[i] * hump + right[i] * r["side"] * size * 0.25 for i in range(3))
            out.append((pos, f, up, r["size"], "walk", r["anim"]))
        return out
