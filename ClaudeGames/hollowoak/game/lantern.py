"""Claude's lantern: old, nearly out of oil, and not to be trusted. It flickers all the time; now and then it sputters,
dipping almost to nothing; every so often it gutters out altogether, and only an ember is left. A shake (E) may bring
it back - usually, not always.

    lantern = Lantern(rng)
    lantern.step(dt)            -> events: "sputter", "dying", "out", "shake", "relit", "failed"
    lantern.level               how bright it is now, 0..1 (an ember when out)
    lantern.shake()             give it a shake
    lantern.shaking             0..1 through a shake (for the hand that holds it)
Plain Python: the tests watch it go out and come back."""
import math

FIRST_OUT = (35.0, 55.0)            # (the first time it goes out: early enough to be learned)
OUT_EVERY = (55.0, 120.0)           # (then every minute or two)
SPUTTER_EVERY = (5.0, 16.0)
SHAKE_TIME = 0.85
RELIGHT = 0.65                      # (the chance a shake brings it back)
EMBER = 0.035


class Lantern:
    def __init__(self, rng):
        self.rng = rng
        self.state = "lit"          # lit, dying, out, catching
        self.t = 0.0
        self.level = 1.0
        self.next_out = rng.uniform(*FIRST_OUT)
        self.next_sputter = rng.uniform(*SPUTTER_EVERY)
        self.sputter_until = 0.0
        self.state_t = 0.0
        self.shake_t = -1.0
        self.phase = (rng.uniform(0, 9), rng.uniform(0, 9), rng.uniform(0, 9))
        self.events = []

    @property
    def shaking(self):
        return 0.0 if self.shake_t < 0 else min(1.0, self.shake_t / SHAKE_TIME)

    @property
    def lit(self):
        return self.state != "out"

    def shake(self):
        if self.shake_t >= 0:
            return False
        self.shake_t = 0.0
        self.events.append("shake")
        return True

    def step(self, dt):
        self.t += dt
        self.state_t += dt
        a, b, c = self.phase
        t = self.t
        # the flame's own unsteadiness: always
        flicker = 0.86 + 0.07 * math.sin(t * 9.3 + a) + 0.05 * math.sin(t * 23.1 + b) + 0.03 * math.sin(t * 41.7 + c)
        if self.shake_t >= 0:
            self.shake_t += dt
            if self.shake_t >= SHAKE_TIME:
                self.shake_t = -1.0
                if self.state == "out":
                    if self.rng.random() < RELIGHT:
                        self._enter("catching")
                        self.events.append("relit")
                    else:
                        self.events.append("failed")
        if self.state == "lit":
            if t >= self.next_sputter:
                self.sputter_until = t + self.rng.uniform(0.25, 1.1)
                self.next_sputter = t + self.rng.uniform(*SPUTTER_EVERY)
                self.events.append("sputter")
            if t < self.sputter_until:                       # (sputtering: dips, almost to nothing, and back)
                flicker *= 0.25 + 0.75 * abs(math.sin(t * 17.0 + a)) * (0.5 + 0.5 * math.sin(t * 5.3 + b))
            if t >= self.next_out:
                self._enter("dying")
                self.events.append("dying")
            self.level = flicker
        elif self.state == "dying":                          # (a second and a half of guttering, then dark)
            k = max(0.0, 1.0 - self.state_t / 1.5)
            self.level = flicker * k * (0.3 + 0.7 * abs(math.sin(t * 13.0 + c)))
            if self.state_t >= 1.5:
                self._enter("out")
                self.events.append("out")
        elif self.state == "out":
            self.level = EMBER * (0.6 + 0.4 * math.sin(t * 3.1 + a))
        elif self.state == "catching":                       # (it takes, unsteadily, and climbs back)
            k = min(1.0, self.state_t / 0.9)
            self.level = flicker * (0.15 + 0.85 * k) * (0.6 + 0.4 * abs(math.sin(t * 19.0 + b)) if k < 1 else 1.0)
            if self.state_t >= 0.9:
                self._enter("lit")
                self.next_out = t + self.rng.uniform(*OUT_EVERY)
                self.next_sputter = t + self.rng.uniform(*SPUTTER_EVERY)
        if self.shake_t >= 0 and self.state in ("lit", "catching"):
            self.level *= 0.7 + 0.3 * abs(math.sin(self.shake_t * 30))   # (a shake jostles the flame)
        out, self.events = self.events, []
        return out

    def _enter(self, state):
        self.state = state
        self.state_t = 0.0
