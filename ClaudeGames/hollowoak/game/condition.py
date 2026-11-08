"""How Claude himself is holding up - his own state, shown in the two orbs (her moods stay hidden, in the den):

    health          falls onto the wood hurt (into her silk, far less); poison eats at it
    poison          bites - one he walked into, one running over his face, the babies on his lantern in the dark;
                    it wears off, slowly
    sanity          the dark (the lantern out - and worse with them all over it), spiders on his face, her eyes on
                    him, slipping, falling into her web; steady light brings it back
    consciousness   heavy poison, a mind giving way, a hard knock; it comes back when those ease

Any of health, sanity or consciousness gone, and he collapses. Plain Python: the tests run it.

    body = Condition(rng)
    body.step(dt, night, events)  -> events: ("bitten", where), ("hurt", amount)
    body.critical()               -> the names of those in danger now
    body.spent()                  -> what gave out ("health", "sanity", "conscious"), or None
"""
import math

CRITICAL = {"health": lambda v: v < 25, "poison": lambda v: v > 70, "sanity": lambda v: v < 25,
            "conscious": lambda v: v < 25}


class Condition:
    def __init__(self, rng):
        self.rng = rng
        self.health, self.poison, self.sanity, self.conscious = 100.0, 0.0, 100.0, 100.0

    def values(self):
        return {"health": self.health, "poison": self.poison, "sanity": self.sanity, "conscious": self.conscious}

    def critical(self):
        return [k for k, v in self.values().items() if CRITICAL[k](v)]

    def spent(self):
        for k in ("health", "conscious", "sanity"):
            if getattr(self, k) < 0.5:                                  # (as good as gone)
                return k
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
                speed = e[1]
                dmg = max(0.0, speed - 7.0) * 6.0 * (0.25 if night.on is not None else 1.0)
                if dmg > 0:
                    self.health -= dmg
                    out.append(("hurt", dmg))
                    if dmg > 20:
                        self.conscious -= dmg * 0.5                     # (a knock to the head)
            elif kind == "dangler" and e[1] == "face":
                self.sanity -= 6
                calm = False
                if rng.random() < 0.4:
                    self._bite(out, "face", 12.0)
            elif kind == "crawler":
                self.sanity -= 3 * e[1]
                calm = False
                if rng.random() < 0.12:
                    self._bite(out, "face", 5.0, 1.0)
            elif kind == "silk" and e[1] == "slip":
                self.sanity -= 4
            elif kind == "silk" and e[1] == "caught":
                self.sanity -= 6
        on_lantern = len(night.swarm.crawling()) if night.lantern else 0
        for _ in range(on_lantern):                                    # (on his hand, in the dark)
            if rng.random() < 0.03 * dt:
                self._bite(out, "hand", 4.0, 1.0)
        dark = night.lamp.state == "out" or not night.lantern
        if dark:
            self.sanity -= (0.7 + 0.12 * on_lantern) * dt
            calm = False
        watched = night.eye_alpha if night.eyes() else 0.0
        self.sanity -= 0.05 * watched * dt                               # (being watched: a slow creep)
        if calm and not dark and night.lamp.level > 0.4 and watched < 0.3:
            self.sanity += 0.3 * dt
        # the poison: eating at him, wearing off
        self.health -= self.poison * 0.015 * dt
        self.poison = max(0.0, self.poison - 0.2 * dt)
        if self.poison < 5:
            self.health += 0.1 * dt
        drop = max(0.0, self.poison - 40) * 0.025 + (0.3 if self.sanity < 20 else 0.0)
        if drop > 0:
            self.conscious -= drop * dt
        elif self.poison < 40:
            self.conscious += 0.6 * dt
        self.health = max(0.0, min(100.0, self.health))
        self.poison = max(0.0, min(100.0, self.poison))
        self.sanity = max(0.0, min(100.0, self.sanity))
        self.conscious = max(0.0, min(100.0, self.conscious))
        return out


def pulse(t, period=1.1):
    """A critical warning's beat: 0..1."""
    return 0.5 + 0.5 * math.sin(t * math.tau / period)
