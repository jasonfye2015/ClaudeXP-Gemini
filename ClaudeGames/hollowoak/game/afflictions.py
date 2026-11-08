"""What the night does to him (phase 8): each of the four, at 75, 50 and 25 - effects that overlap, and that change what
he can do, and what she makes of him.

    health  75 panting; his heart's resting beat up; she hears him breathing
            50 a red tint; blood from his eyes at the edges of his sight, beating with his heart
            25 blood down the wand onto the lantern - the light goes red; drops behind him; she smells it (her hunger)
    poison  25 he vomits (at once, then every five to ten minutes) - a puddle; it eases the poison a little; her small
               ones gather at it (five puddles at most)
            50 a green tint; foam and drips at the bottom of his sight; a cough; his heart skipping beats
            75 vomiting, oftener and greener, over the wand and the lantern - the light goes green (a shake, E, flings
               some of it off)
    sanity  75 his sight sways and swims; false eyes in the fungus; the bark breathing
            50 down on his hands and knees: crawling, slower, five to seven minutes up, ten to fifteen down - on her
               silk, a crawl sways less, but it reads to her as wounded prey
            25 his left eye: his hand comes up to it, and his sight goes dark on that side, and the hand comes away red
               - and in it, when he looks down, his eye (into his satchel); once a night
    stupor  25 his sight wavers like heat; sounds go dull
            50 bouts of not answering himself - his head shaking "No"
            75 he falls, now and then, and drags himself up; moments lost (dark, and the clock gone on)

Each starts at its line, and ends a little past it (no flicker). Nothing that takes him from himself begins on a strand
or in her scenes. Options (records): fx_all, fx_health, fx_poison, fx_sanity, fx_stupor, fx_gore (blood and vomit),
fx_eye, fx_distort (sway, haze, swimming sight), fx_control (crawling, refusing, falling).

    af = Afflictions(rng)
    af.step(dt, night) -> events: ("afflict", what)
    af.tier(stat)                     0..3
    af.busy                           something's being done to him (vomit, fall, the eye, a refusal): his hands aren't his
    af.posture                        0 standing .. 1 down on the ground (his eye's height)
    af.pace                           how fast he goes (crawling: slower)
    af.warp, af.haze, af.roll         for his sight
Plain Python: the tests make him ill."""
import math

from .web import Bridge

LINES = {"health": (75, 50, 25), "sanity": (75, 50, 25), "poison": (25, 50, 75), "stupor": (25, 50, 75)}
SLACK = 5.0
VOMIT_EVERY, VOMIT_EVERY_75 = (300.0, 600.0), (120.0, 240.0)
VOMIT_FOR = 2.6
UP_FOR, DOWN_FOR = (300.0, 420.0), (600.0, 900.0)
REFUSE_EVERY, REFUSE_FOR = (40.0, 90.0), (2.5, 4.0)
FALL_EVERY = (300.0, 600.0)
FALL_FOR = 7.5                  # (down, a while on the wood, and dragging himself up)
EYE_FOR = 6.5
PUDDLES = 5
DEFAULTS = {"fx_all": True, "fx_health": True, "fx_poison": True, "fx_sanity": True, "fx_stupor": True,
            "fx_gore": True, "fx_eye": True, "fx_distort": True, "fx_control": True}


class Afflictions:
    def __init__(self, rng):
        self.rng = rng
        self.tiers = {k: 0 for k in LINES}
        self.opts = dict(DEFAULTS)
        self.t = 0.0
        self.act = None                    # (what's being done to him now: (kind, started))
        self.next_vomit = None
        self.next_refuse = None
        self.next_fall = None
        self.down = False                  # (on his hands and knees)
        self.cycle_until = None
        self.posture, self.pace = 0.0, 1.0
        self.eye_lost = False
        self.bloodied = 0.0                # (blood on the wand and lantern: 0..1, for the night)
        self.coat = 0.0                    # (vomit on them: 0..1, wearing off; a shake flings some away)
        self.puddles = []                  # [(x, y, z, green, born)]
        self.drops = []                    # (his blood, behind him: [(x, y, z, born)])
        self.glimpses = []                 # (false eyes: [(position, born)])
        self.warp = self.haze = self.roll = 0.0
        self.blackout = 0.0
        self._last_drop = None
        self.said = set()

    # ---- the lines ------------------------------------------------------------------------------------------------
    def on(self, stat, key=None):
        o = self.opts
        return o.get("fx_all", True) and o.get("fx_" + stat, True) and (key is None or o.get("fx_" + key, True))

    def tier(self, stat):
        return self.tiers[stat] if self.on(stat) else 0

    def _tiers(self, night, cap):
        b = night.body
        for stat, lines in LINES.items():
            v = getattr(b, stat)
            falling = stat in ("health", "sanity")
            have = self.tiers[stat]
            want = 0
            for k, line in enumerate(lines):
                past = v <= line if falling else v >= line
                held = (v <= line + SLACK if falling else v >= line - SLACK) and have > k
                if past or held:
                    want = k + 1
            self.tiers[stat] = min(want, cap)

    @property
    def busy(self):
        return self.act is not None

    # ---- a step ---------------------------------------------------------------------------------------------------
    def step(self, dt, night):
        self.t += dt
        out = []
        self._tiers(night, 2 if night.flags.get("first") else 3)      # (the first night: never the worst of it)
        free = not night.quiet and not isinstance(night.on, Bridge) and night.dying is None and night.ending is None
        h, p, s, st = (self.tier(k) for k in ("health", "poison", "sanity", "stupor"))
        control = self.opts.get("fx_control", True) and self.opts.get("fx_all", True)
        # health: his heart, his breath; at 25, blood on the wand, and a trail
        if h >= 1:
            self._once(out, "pant")
        if h >= 2:
            self._once(out, "bleed")
        if h >= 3 and self.on("health", "gore") and self.bloodied < 1.0:
            if self.bloodied == 0.0:
                out.append(("afflict", "bloodied"))
            self.bloodied = min(1.0, self.bloodied + dt / 6.0)
        if h >= 3:
            night.moods.hunger = min(100.0, night.moods.hunger + 0.03 * dt)      # (she smells it)
            if self._last_drop is None or math.dist(self._last_drop, (night.x, night.z)) > 1.8:
                self._last_drop = (night.x, night.z)
                self.drops.append((night.x, night.y + 0.01, night.z, self.t))
                del self.drops[:-40]
        # poison: vomiting; foam; at 75, over the lantern
        if p >= 1:
            if self.next_vomit is None:
                self.next_vomit = self.t                                     # (at once, the first time)
            if self.act is None and free and self.t >= self.next_vomit:
                self._begin("vomit", out)
                lo, hi = VOMIT_EVERY_75 if p >= 3 else VOMIT_EVERY
                self.next_vomit = self.t + self.rng.uniform(lo, hi)
        else:
            self.next_vomit = None
        if p >= 2:
            self._once(out, "foam")
        night.body.skips = 0.12 if p >= 2 else 0.0                           # (his heart, skipping)
        self.coat = max(0.0, self.coat - dt / 240.0)
        # sanity: his sight swaying; down on his hands and knees; his eye
        if s >= 1:
            self._once(out, "sway")
            if self.rng.random() < dt / 25.0 and self.on("sanity", "distort"):
                self._glimpse(night)
        if s >= 2 and control:
            if self.cycle_until is None:
                self.down, self.cycle_until = True, self.t + self.rng.uniform(*DOWN_FOR)
                out.append(("afflict", "crawl"))
            elif self.t >= self.cycle_until and (self.down or free):
                self.down = not self.down
                self.cycle_until = self.t + self.rng.uniform(*(DOWN_FOR if self.down else UP_FOR))
                out.append(("afflict", "crawl" if self.down else "stand"))
        elif self.down or self.cycle_until is not None:
            if self.down:
                out.append(("afflict", "stand"))
            self.down, self.cycle_until = False, None
        if s >= 3 and not self.eye_lost and self.on("sanity", "eye") and self.act is None and free:
            self._begin("eye", out)
        # stupor: the haze; refusing; falling, and moments lost
        if st >= 1:
            self._once(out, "haze")
        if st >= 2 and control:
            if self.next_refuse is None:
                self.next_refuse = self.t + self.rng.uniform(*REFUSE_EVERY) * 0.4
            if self.act is None and free and self.t >= self.next_refuse:
                self._begin("refuse", out)
                self.next_refuse = self.t + self.rng.uniform(*REFUSE_EVERY)
        else:
            self.next_refuse = None
        if st >= 3 and control:
            if self.next_fall is None:
                self.next_fall = self.t + self.rng.uniform(*FALL_EVERY) * 0.3
            if self.act is None and free and self.t >= self.next_fall:
                if self.rng.random() < 0.3:
                    self._begin("lost", out)                                 # (a moment gone)
                else:
                    self._begin("fall", out)
                self.next_fall = self.t + self.rng.uniform(*FALL_EVERY)
        else:
            self.next_fall = None
        self._doing(dt, night, out)
        # how he stands, how fast he goes, and his sight
        want = 1.0 if self.act and self.act[0] == "fall" and self._fall_k() > 0 else (0.62 if self.down else 0.0)
        if self.act and self.act[0] == "fall":
            self.posture = self._fall_k()
        else:
            self.posture += (want - self.posture) * min(1.0, dt * 1.8)
        self.pace = 1.0 - 0.6 * min(1.0, self.posture / 0.62)
        distort = self.opts.get("fx_distort", True)
        sway_w = (0.35 if s >= 1 else 0.0) + (0.35 if s >= 2 else 0.0) + (0.3 if s >= 3 else 0.0)
        self.warp += ((sway_w if distort and self.on("sanity") else 0.0) - self.warp) * min(1.0, dt)
        haze_w = (0.35 if st >= 1 else 0.0) + (0.3 if st >= 2 else 0.0) + (0.35 if st >= 3 else 0.0)
        self.haze += ((haze_w if distort and self.on("stupor") else 0.0) - self.haze) * min(1.0, dt)
        self.roll = 0.05 * self.warp * math.sin(self.t * 0.7) + 0.02 * self.warp * math.sin(self.t * 1.9)
        self.glimpses = [g for g in self.glimpses if self.t - g[1] < 1.8]
        return out

    def _once(self, out, what):
        if what not in self.said:
            self.said.add(what)
            out.append(("afflict", what))

    def _glimpse(self, night):
        """False eyes: a pair of red lights in the fungus, where she isn't."""
        from . import tree as T
        a, hgt, _s = self.rng.choice(T.FUNGI)
        if abs(hgt - night.y) > 6:
            return
        r = night.tree.wall_r(a, hgt) - 0.25
        self.glimpses.append(((math.cos(a) * r, hgt + 0.3, math.sin(a) * r), self.t))

    def _begin(self, kind, out):
        self.act = (kind, self.t)
        out.append(("afflict", kind))

    def _fall_k(self):
        if not self.act or self.act[0] != "fall":
            return 0.0
        k = self.t - self.act[1]
        if k < 0.7:
            return (k / 0.7) ** 2
        if k < 3.0:
            return 1.0
        return max(0.0, 1.0 - (k - 3.0) / (FALL_FOR - 3.0))

    def _doing(self, dt, night, out):
        """What's being done to him, through to its end."""
        if self.act is None:
            return
        kind, t0 = self.act
        k = self.t - t0
        if kind == "vomit":
            if k >= 1.1 and not getattr(self, "_spilt", False):
                self._spilt = True
                fx, fz = math.sin(night.yaw), -math.cos(night.yaw)
                x, z = night.x + fx * 0.8, night.z + fz * 0.8
                green = self.tier("poison") >= 3
                if self.on("poison", "gore"):
                    self.puddles.append((x, night.floor_at(x, z, night.y + 0.3) + 0.005, z, green, self.t))
                    del self.puddles[:-PUDDLES]
                    if green:
                        if self.coat < 0.5:
                            out.append(("afflict", "coat"))
                        self.coat = 1.0                                       # (over the wand, the lantern)
                night.body.poison = max(0.0, night.body.poison - 6.0)        # (out of him, some of it)
                night.body.stupor = min(100.0, night.body.stupor + 2.0)
            if k >= VOMIT_FOR:
                self._spilt = False
                self.act = None
        elif kind == "refuse":
            if k >= getattr(self, "_refuse_for", 3.0):
                self._refuse_for = self.rng.uniform(*REFUSE_FOR)
                self.act = None
        elif kind == "fall":
            if k >= FALL_FOR:
                self.act = None
        elif kind == "lost":
            self.blackout = min(1.0, k / 0.3) if k < 2.0 else max(0.0, 1.0 - (k - 2.0) / 0.6)
            if k >= 2.0 and not getattr(self, "_lost_done", False):
                self._lost_done = True
                night.sky.clock += 6.0                                         # (the clock gone on without him)
            if k >= 2.6:
                self._lost_done = False
                self.blackout = 0.0
                self.act = None
        elif kind == "eye":
            if k >= 2.0 and not self.eye_lost:
                self.eye_lost = True
                night.body.sanity = min(100.0, night.body.sanity + 8.0)     # (a terrible quiet, after)
            if k >= EYE_FOR:
                self.act = None
                out.append(("afflict", "eye_taken"))

    def shaken(self):
        """E: the lantern shaken - some of what's on it flung off."""
        self.coat = max(0.0, self.coat - 0.35)

    def phase(self):
        """What's being done now, and how far through: (kind, seconds) or None."""
        return (self.act[0], self.t - self.act[1]) if self.act else None

    def filter(self, inp, night):
        """His input, as his body lets it through: nothing while it's busy with him; slower, crawling; no jumps down."""
        from .night import Input
        if self.act is not None:
            still = Input()
            still.yaw, still.pitch = inp.yaw, inp.pitch
            kind, k = self.phase()
            if kind == "refuse":                                              # (his head, shaking: no)
                still.yaw = inp.yaw + 0.22 * math.sin(k * 9.0) * max(0.0, 1.0 - k / 3.5)
            elif kind == "vomit":
                still.pitch = inp.pitch - 0.5 * math.sin(min(1.0, k / VOMIT_FOR) * math.pi)
            elif kind == "eye":
                if k > 3.6:
                    still.pitch = inp.pitch - 0.7 * min(1.0, (k - 3.6) / 0.6) * (1.0 if k < 5.8 else
                                                                              max(0.0, 1 - (k - 5.8) / 0.7))
            return still
        if self.posture > 0.3:
            inp.jump = False
            inp.hurry = False
        return inp
