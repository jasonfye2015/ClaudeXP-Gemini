"""Supper: when the poison reaches his health, or stupor his sanity (or either runs dry). He collapses where he stands; the lantern falls and breaks
and its flame dies on the ground. They come - onto him, over his face, laying silk across his eyes until he can hardly
see. They turn him over and over, wrapping him in thick bands of silk. Then he's dragged, in pulls, to the middle of the
hollow's floor; turned, lifted by the feet on her ropes - thick silk from far above - and drawn up, upside down, half
the height of the trunk, swinging. Then black - and, small, "Ending 1 of 8: Supper".

    death = Death(night, cause, rng)
    death.step(dt, night)       -> events ("lantern", "break"), ("death", "drag"), ("death", "lift"), ("death", "end")
    death.cover()               -> [(u, v, du, dv, size, t)] the spiders on his face (as Crawlers.active())
    death.webs                  -> what's been laid across his eyes: dicts of kind "strand" (a, b, sag), "orb" (c, r,
                                   turn) or "band" (a, b, sag, width - the wrapping), each with how far it's drawn in
    death.ropes()               -> her ropes, from far above down to his feet, while he's drawn up: [(top, bottom)]
    death.black                 0..1, the end coming down
    death.done                  over: the ending's line is showing
Plain Python: it moves the night's own Claude - where he is, how he lies, which way is up."""
import math

from . import tree as T

COLLAPSE = 1.4
BREAK = 0.55
COVER_END = 7.4                 # (by now his eyes are mostly silk)
WRAP_END = 10.4                 # (turned over and over, bound)
DRAG_END = 15.4
LIFT_END = 22.4
FADE_END = 24.4
LEAN = DRAG_END + 2.4           # (she comes down to him, close, and leans into his sight)
SPEAK = LEAN + 1.2
BANDS = 16
PULLS = 5
SPIDERS = 46
WEBS = 70
ENDING = ("Ending 1 of 8: Supper", "Wrapped, and hung, and kept for later.")


def last_words(night, reputation=None, lies=0):
    """What she says to him as he's hung: quiet, without cruelty - from what she made of him, tonight and before."""
    m = night.moods
    cause = night.dying.cause if night.dying is not None else None
    if m.regard >= 55:
        return "I didn't want it to be you. Hush, now. I'll keep you close, where it's warm."
    if lies:
        return "You lied to me, little wizard. I would so have liked to know the truth of you."
    if (reputation or {}).get("met", 0) >= 1:
        return "You again. You keep coming back to me, little wizard - and I keep you, every time."
    if night.manner() > 0.5:
        return "You walked so gently on my silk. I'll remember that, when I'm hungry again."
    if cause == "bite":
        return "Only a little bite. Only a little more. Sleep."
    return "Hush. It's only the dark - and the dark is my house, and you are in it."


def _ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


class Death:
    def __init__(self, night, cause, rng):
        self.cause, self.rng = cause, rng
        self.t = 0.0
        self.x0, self.y0, self.z0 = night.x, night.y, night.z
        self.yaw0, self.pitch0 = night.yaw, night.pitch
        self.eye0 = night.eye_h
        f = (math.sin(night.yaw), -math.cos(night.yaw))
        self.lamp_at = (night.x + f[0] * 0.35, night.y + 0.03, night.z + f[1] * 0.35)    # (where the lantern lands)
        self.broke = False
        self.spiders = []
        self.webs = []
        self.black = 0.0
        self.done = False
        self.said = set()
        self.centre_y = night.tree.ground(0.0, 0.0)
        self._ropes = []
        self.top = T.TOP * 0.5
        self.her_line = None            # (her last words to him: set by whoever knows what she made of him)
        self.asked = False
        self.spoke = False
        self.show_line = None
        self.her_at = None

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
        if t >= LEAN and self.her_at is None:                          # (her, down to him, close)
            self._lean(night)
        self._pose(night)
        self.hold(night)
        self._cover(dt)
        if t >= SPEAK and not self.spoke and self.her_line:
            self.spoke = True
            out.append(("death", "line", self.her_line))
        self.show_line = self.her_line if self.spoke and t < FADE_END - 0.3 else None
        for name, at in (("wrap", COVER_END), ("drag", WRAP_END), ("lift", DRAG_END), ("end", FADE_END)):
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
            night.eye_h = self.eye0 * (1 - k) + 0.1 * k
            night.roll = 1.25 * k
            night.pitch = self.pitch0 * (1 - k) - 0.25 * k + 0.02 * math.sin(t * 1.3)
            night.yaw = self.yaw0
        elif t < WRAP_END:                                              # (turned over and over in their silk)
            k = _ease((t - COVER_END) / (WRAP_END - COVER_END))
            night.x, night.y, night.z = self.x0, self.y0, self.z0
            night.eye_h = 0.1
            night.roll = 1.25 + (4 * math.pi - 1.25) * k
            night.pitch = -0.25 + 1.45 * k + 0.05 * math.sin(t * 9.0)
            night.yaw = self.yaw0
        elif t < DRAG_END:                                              # (dragged by the feet, in pulls, on his back)
            f = (t - WRAP_END) / (DRAG_END - WRAP_END) * PULLS
            n = min(PULLS - 1, int(f))
            k = (n + _ease((f - n) * 1.6)) / PULLS
            night.x = self.x0 * (1 - k)
            night.z = self.z0 * (1 - k)
            night.y = max(self.y0 * (1 - k) + self.centre_y * k, night.tree.ground(night.x, night.z))  # (let down, if high)
            night.eye_h = 0.1
            night.roll = 0.0
            night.pitch = 1.2 + 0.06 * math.sin(f * math.pi * 2)                            # (jerked; staring up)
            night.yaw = self.yaw0 + 0.15 * math.sin(f * 2.1)
        elif self.her_at is not None:                                    # (hung; and she's there, close: he looks at her)
            self._hung(night, t)
            ex, ey, ez = night.eye
            hx, _hy, hz = self.her_at
            self.her_at = (hx, ey - 0.9, hz)                            # (she comes up with him, on her own thread)
            if night.her.staged is not None:
                night.her.staged = (self.her_at, night.her.staged[1])
            hy = self.her_at[1]
            k = _ease((t - LEAN) / 1.6)
            want_yaw = math.atan2(hx - ex, -(hz - ez))
            want_pitch = math.atan2(hy + 0.9 - ey, math.hypot(hx - ex, hz - ez))
            dy = (want_yaw - night.yaw + math.pi) % math.tau - math.pi
            night.yaw += dy * k
            night.pitch = night.pitch * (1 - k) + want_pitch * k
        else:
            self._hung(night, t)

    def _lean(self, night):
        """She comes down her rope to him, and leans close - before his face."""
        ex, ey, ez = night.eye
        f = (math.sin(night.yaw), -math.cos(night.yaw))
        x, z = ex + f[0] * 2.5, ez + f[1] * 2.5
        self.her_at = (x, ey - 0.9, z)
        face = (ex - x, 0.0, ez - z)
        k = math.hypot(face[0], face[2]) or 1.0
        night.her.stage(self.her_at, (face[0] / k, 0.0, face[2] / k))

    def _hung(self, night, t):
        """Turned, lifted by the feet, drawn up, swinging."""
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
        bands = sum(1 for w in self.webs if w["kind"] == "band")
        want = int(BANDS * min(1.0, max(0.0, (t - COVER_END) / (WRAP_END - COVER_END))))
        while bands < want:                                             # (the wrapping: thick bands, across and across)
            bands += 1
            y0 = rng.uniform(-0.1, 1.1)
            a, b = (-0.15, y0), (1.15, y0 + rng.uniform(-1.1, 1.1))       # (round and round him, at all angles)
            self.webs.append({"kind": "band", "a": a, "b": b, "sag": rng.uniform(-0.15, 0.15),
                              "width": rng.uniform(0.03, 0.08), "born": t})
        for w in self.webs:
            w["drawn"] = min(1.0, (t - w["born"]) / (0.35 if w["kind"] == "band" else 0.6))   # (laid, not appearing)

    def ropes(self):
        """Her ropes while he's drawn up: from far above, down to his feet."""
        if self.t < DRAG_END:
            return []
        return self._ropes

    def hold(self, night):
        """Where her ropes meet him now (his feet), for drawing them."""
        feet = (night.x, night.y + 0.05, night.z)
        top = T.TOP * 0.5 + 10.0
        self._ropes = [((dx, top, dz), feet) for dx, dz in ((0.0, 0.0), (0.5, 0.3), (-0.4, 0.45))]

    def cover(self):
        return [(s["u"], s["v"], math.cos(s["head"]), math.sin(s["head"]), s["size"], s["anim"])
                for s in self.spiders]
