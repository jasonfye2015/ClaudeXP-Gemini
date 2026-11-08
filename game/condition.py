"""How Claude himself is holding up - his own state, shown in the two orbs (her moods stay hidden, in the den). Each orb
holds two fluids: the one he lives on, and the one rising under it from the bottom. When the rising one reaches the
other, he's done - so the poison in him is a ceiling coming down on his health, and stupor on his sanity.

    health      red. Falls onto the wood hurt (into her silk, far less); poison eats at it slowly
    poison      green, rising in the same orb: bites - one he walked into, one running over his face, the babies on his
                lantern in the dark; it wears off, slowly
    sanity      blue. The dark (the lantern out - and worse with them all over it), spiders on his face, her eyes on him,
                slipping, falling into her web; steady light brings it back
    stupor      yellow, rising in the sanity orb: heavy poison, a mind giving way, a hard knock; it clears when those ease

He collapses when poison reaches his health, or stupor his sanity (or either runs dry). Plain Python: the tests run it.

And his heart: resting near 66 beats a minute; faster in the dark, with less sanity left in him, with poison; leaping
when something drops onto his face or he slips or falls; slower with stupor. body.beats holds when it beat (the last
ten seconds), body.history its rate every half second (the last minute) - for the monitor at the bottom of the view.
At the end (body.dying_heart) it races, then slows, and stops.

    body = Condition(rng)
    body.step(dt, night, events)  -> events: ("bitten", where), ("hurt", amount)
    body.critical()               -> the orbs in danger now: "health" and/or "sanity" (for the edge of the view)

For now (only her babies about) it barely touches him: a careful player hardly sees the orbs move. Left standing in the
dark - doing nothing, never shaking the lantern - his mind goes at last, in ten or twelve minutes: Supper.
    body.spent()                  -> what did for him ("health", "poison", "sanity", "stupor"), or None
"""
import math

MARGIN = 20.0                   # (closer than this, the rising fluid to the other: danger)


class Level:
    """How hard the night is on him: what hurts him, by how much; how fast it goes again."""

    def __init__(self, hurt, venom, mind, calm, wear, heal, daze, clear, eat, hunger):
        self.hurt, self.venom, self.mind, self.calm = hurt, venom, mind, calm        # (damage; bites; the mind's losses;
        self.wear, self.heal, self.daze, self.clear = wear, heal, daze, clear        #  its mending; poison wearing off;
        self.eat, self.hunger = eat, hunger                                          #  health back; stupor in and out;
                                                                                     #  poison eating; her hunger)


LEVELS = {                     # (Easy: as it was made. The others: what the night really costs)
    "easy": Level(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    "normal": Level(2.2, 2.6, 2.0, 0.6, 0.45, 0.5, 2.0, 0.5, 2.0, 1.25),
    "hard": Level(3.5, 4.0, 3.0, 0.4, 0.3, 0.3, 3.0, 0.35, 3.0, 1.55),
    "nightmare": Level(5.0, 6.0, 4.5, 0.25, 0.2, 0.15, 4.5, 0.2, 4.0, 1.9),
}
LEVEL_NAMES = (("easy", "Easy"), ("normal", "Normal"), ("hard", "Hard"), ("nightmare", "Nightmare"))


def level(night):
    return LEVELS.get(getattr(night, "difficulty", "easy"), LEVELS["easy"])


class Condition:
    def __init__(self, rng):
        self.rng = rng
        self.health, self.poison, self.sanity, self.stupor = 100.0, 0.0, 100.0, 0.0
        self.bpm, self.startle, self.t = 66.0, 0.0, 0.0
        self._phase, self._sample = 0.0, 0.0
        self.beats, self.history = [], []
        self.skips = 0.0                    # (how often a beat doesn't come: poison past half - game/afflictions.py)

    def values(self):
        return {"health": self.health, "poison": self.poison, "sanity": self.sanity, "stupor": self.stupor}

    def critical(self):
        out = []
        for life, rising in (("health", "poison"), ("sanity", "stupor")):
            lv, rv = getattr(self, life), getattr(self, rising)
            if lv - rv < MARGIN:
                out.append(life)
        return out

    def spent(self):
        for life, rising in (("health", "poison"), ("sanity", "stupor")):
            lv, rv = getattr(self, life), getattr(self, rising)
            if lv < 0.5:
                return life
            if rv > 0.5 and rv >= lv:                                  # (it's reached him)
                return rising
        return None

    def _heart(self, dt, target, ease=0.6):
        """Toward a rate; beating as it goes."""
        self.t += dt
        self.bpm += (target - self.bpm) * min(1.0, dt * ease)
        self.bpm = max(0.0, self.bpm)
        self._phase += self.bpm / 60.0 * dt
        if self._phase >= 1.0:
            self._phase -= math.floor(self._phase)
            if not (self.skips and self.rng.random() < self.skips):
                self.beats.append(self.t)
        while self.beats and self.t - self.beats[0] > 10.0:
            self.beats.pop(0)
        self._sample += dt
        if self._sample >= 0.5:
            self._sample -= 0.5
            self.history.append(self.bpm)
            del self.history[:-120]

    def dying_heart(self, dt, t):
        """At the end: racing as they come, slowing as he's drawn up, and still."""
        if t < 2.0:
            target, ease = 165.0, 2.0
        elif t < 10.0:
            target, ease = 150.0 - (t - 2.0) * 2.0, 1.0
        elif t < 22.0:
            target, ease = max(0.0, 134.0 - (t - 10.0) * 11.0), 0.5
        else:
            target, ease = 0.0, 3.0
        if t >= 21.0:
            target, ease = 0.0, 8.0
        self._heart(dt, target, ease)

    def _bite(self, out, where, venom, hurt=2.0):
        lv = getattr(self, "lv", LEVELS["easy"])
        self.poison += venom * lv.venom
        self.health -= hurt * lv.hurt
        out.append(("bitten", where))

    def step(self, dt, night, events):
        rng = self.rng
        out = []
        lv = self.lv = level(night)
        calm = True
        for e in events:
            kind = e[0]
            if kind == "fall":                                          # (the wood is hard; her silk gives)
                dmg = max(0.0, e[1] - 7.0) * 6.0 * (0.25 if night.on is not None else 1.0) * lv.hurt
                if dmg > 0:
                    self.health -= dmg
                    out.append(("hurt", dmg))
                    if dmg > 20 * lv.hurt:
                        self.stupor += dmg * 0.5 * lv.daze              # (a knock to the head)
            elif kind == "dangler" and e[1] == "face":
                self.sanity -= 2 * lv.mind
                calm = False
                if rng.random() < 0.2:
                    self._bite(out, "face", 5.0, 1.0)
            elif kind == "crawler":
                self.sanity -= 1 * e[1] * lv.mind
                calm = False
                if rng.random() < 0.1:
                    self._bite(out, "face", 2.0, 0.5)
            elif kind == "silk" and e[1] == "slip":
                self.sanity -= 1.5 * lv.mind
            elif kind == "silk" and e[1] == "caught":
                self.sanity -= 2 * lv.mind
        on_lantern = len(night.swarm.crawling()) if night.lantern else 0
        for _ in range(on_lantern):                                    # (on his hand, in the dark)
            if rng.random() < 0.01 * dt:
                self._bite(out, "hand", 2.0, 0.5)
        dark = night.lamp.state == "out" or not night.lantern
        if dark:
            self.sanity -= (0.045 + 0.006 * on_lantern) * dt * lv.mind
            calm = False
        watched = night.eye_alpha if night.eyes() else 0.0
        self.sanity -= 0.01 * watched * dt * lv.mind                   # (being watched: the slowest creep)
        if calm and not dark and night.lamp.level > 0.4 and watched < 0.3:
            self.sanity += 0.3 * dt * lv.calm
        # the poison: eating at him a little, wearing off slowly
        self.health -= self.poison * 0.003 * dt * lv.eat
        self.poison = max(0.0, self.poison - 0.06 * dt * lv.wear)  # (it lingers: minutes, not moments)
        if self.poison < 5:
            self.health += 0.1 * dt * lv.heal
        rise = max(0.0, self.poison - 40) * 0.025 + (0.2 if self.sanity < 30 else 0.0)
        if rise > 0:
            self.stupor += rise * dt * lv.daze
        elif self.poison < 40:
            self.stupor -= 0.6 * dt * lv.clear
        for k in ("health", "poison", "sanity", "stupor"):
            setattr(self, k, max(0.0, min(100.0, getattr(self, k))))
        # his heart: what's in him, what's about him, and what just made it leap
        for e in events:
            kind = e[0]
            jump = {"crawler": 14.0, "swipe": 6.0, "collapse": 30.0}.get(kind, 0.0)
            if kind == "dangler":
                jump = 24.0 if e[1] == "face" else 5.0
            elif kind == "silk" and e[1] in ("slip", "caught", "teeter"):
                jump = {"slip": 26.0, "caught": 30.0, "teeter": 10.0}[e[1]]
            elif kind == "fall":
                jump = min(35.0, e[1] * 1.5)
            elif kind == "lantern" and e[1] == "out":
                jump = 12.0
            self.startle += jump
        for e in out:
            if e[0] == "bitten":
                self.startle += 12.0
        self.startle *= math.exp(-dt / 7.0)
        target = 66.0 + (100.0 - self.sanity) * 0.35 + self.poison * 0.25 - self.stupor * 0.2
        target += 14.0 if self.health <= 75 else 0.0                  # (hurt: panting, his heart's rest raised)
        target += (9.0 if dark else 0.0) + (12.0 if night.inp_hurry and night.moved_now > 0 else 0.0)
        target += min(80.0, self.startle)
        self._heart(dt, max(40.0, min(185.0, target)))
        return out


def pulse(t, period=1.1):
    """A critical warning's beat: 0..1."""
    return 0.5 + 0.5 * math.sin(t * math.tau / period)
