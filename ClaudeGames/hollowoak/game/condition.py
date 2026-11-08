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

    body = Condition(rng)
    body.step(dt, night, events)  -> events: ("bitten", where), ("hurt", amount)
    body.critical()               -> the orbs in danger now: "health" and/or "sanity" (for the edge of the view)

For now (only her babies about) it barely touches him: a careful player hardly sees the orbs move. Left standing in the
dark - doing nothing, never shaking the lantern - his mind goes at last, in ten or twelve minutes: Supper.
    body.spent()                  -> what did for him ("health", "poison", "sanity", "stupor"), or None
"""
import math

MARGIN = 20.0                   # (closer than this, the rising fluid to the other: danger)


class Condition:
    def __init__(self, rng):
        self.rng = rng
        self.health, self.poison, self.sanity, self.stupor = 100.0, 0.0, 100.0, 0.0

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

    def _bite(self, out, where, venom, hurt=2.0):
        self.poison += venom
        self.health -= hurt
        out.append(("bitten", where))

    def step(self, dt, night, events):
        rng = self.rng
        out = []
        calm = True
        for e in events:
            kind = e[0]
            if kind == "fall":                                          # (the wood is hard; her silk gives)
                dmg = max(0.0, e[1] - 7.0) * 6.0 * (0.25 if night.on is not None else 1.0)
                if dmg > 0:
                    self.health -= dmg
                    out.append(("hurt", dmg))
                    if dmg > 20:
                        self.stupor += dmg * 0.5                        # (a knock to the head)
            elif kind == "dangler" and e[1] == "face":
                self.sanity -= 2
                calm = False
                if rng.random() < 0.2:
                    self._bite(out, "face", 5.0, 1.0)
            elif kind == "crawler":
                self.sanity -= 1 * e[1]
                calm = False
                if rng.random() < 0.1:
                    self._bite(out, "face", 2.0, 0.5)
            elif kind == "silk" and e[1] == "slip":
                self.sanity -= 1.5
            elif kind == "silk" and e[1] == "caught":
                self.sanity -= 2
        on_lantern = len(night.swarm.crawling()) if night.lantern else 0
        for _ in range(on_lantern):                                    # (on his hand, in the dark)
            if rng.random() < 0.01 * dt:
                self._bite(out, "hand", 2.0, 0.5)
        dark = night.lamp.state == "out" or not night.lantern
        if dark:
            self.sanity -= (0.045 + 0.006 * on_lantern) * dt
            calm = False
        watched = night.eye_alpha if night.eyes() else 0.0
        self.sanity -= 0.01 * watched * dt                             # (being watched: the slowest creep)
        if calm and not dark and night.lamp.level > 0.4 and watched < 0.3:
            self.sanity += 0.3 * dt
        # the poison: eating at him a little, wearing off slowly
        self.health -= self.poison * 0.006 * dt
        self.poison = max(0.0, self.poison - 0.2 * dt)
        if self.poison < 5:
            self.health += 0.1 * dt
        rise = max(0.0, self.poison - 40) * 0.025 + (0.2 if self.sanity < 30 else 0.0)
        if rise > 0:
            self.stupor += rise * dt
        elif self.poison < 40:
            self.stupor -= 0.6 * dt
        for k in ("health", "poison", "sanity", "stupor"):
            setattr(self, k, max(0.0, min(100.0, getattr(self, k))))
        return out


def pulse(t, period=1.1):
    """A critical warning's beat: 0..1."""
    return 0.5 + 0.5 * math.sin(t * math.tau / period)
