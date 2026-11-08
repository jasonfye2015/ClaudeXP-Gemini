"""Ysmeine's moods (phase 3b): how she regards him, in five hidden values she hints at but never shows. Each is 0..100.

    fascination   rises with magic shown well, honest answers, strange or personal gifts; and with his watching her,
                  steadily, when she comes to the edge of his light. Falls with small talk, repetition, flattery she
                  has heard before; drifts back toward indifference. Too low, and her patience drains faster.
    patience      rises with slow movement, with listening, with answers to what she asked. Falls with evasion,
                  rushing (running, jumping, scrambling on her silk, coming at her), demanding, interrupting. At zero
                  she stops talking and starts hunting.
    hunger        rises with the clock, always; with fear and fast movement (a scramble on the silk is prey). Falls
                  with offerings of food, distraction, deep conversation - and a bite. Past its limit, she bites.
    suspicion     rises with lies (she remembers), bright light, harm to her small ones, broken promises. Falls with
                  his word kept, a true memory shown; and slowly, with time. High enough, and kindness reads as a trick.
    regard        every good moment, slowly; every betrayal, sharply. The deep score: it decides which ending dawn brings.

They move her body (game/mother.py): fascination brings her closer and keeps her longer; suspicion keeps her off;
hunger brings her more often, and when it's high she circles; patience gone, or hunger past its limit, and she hunts -
and bites. They show in the den, never in numbers: the fungus-light warms toward amber as she hungers, brightens with
her fascination, dims and cools with suspicion; the hum of her silk rises in pitch with her hunger.

    moods = Moods()
    moods.step(dt, night, events)       -> events ("her", "hunts"), ...
    moods.heard(kind)                   what he said or did to her, in conversation (phase 3c): "honest", "lie",
                                        "flattery", "small_talk", "repeat", "answer", "evasion", "demand", "interrupt",
                                        "gift", "food", "magic", "memory", "promise_kept", "promise_broken",
                                        "deep", "light", "harm_small"
    moods.bit()                         she has bitten him: her hunger eased, for a while
Plain Python: the tests read it; the player never does (F3 shows it, for building the game)."""
import math

LIMIT = 100.0                   # (hunger past this: she bites)
HUNT_PATIENCE = 0.0
TRICK = 75.0                    # (suspicion above this: kindness reads as a trick)

# what each thing he says or does in conversation moves: (fascination, patience, hunger, suspicion, regard)
HEARD = {
    "honest": (6, 3, 0, -2, 2), "lie": (0, -4, 0, 18, -8), "flattery": (-5, -3, 0, 4, 0),
    "small_talk": (-4, -2, 0, 0, 0), "repeat": (-6, -5, 0, 0, -1), "answer": (2, 5, 0, -1, 1),
    "evasion": (-2, -8, 0, 5, -2), "demand": (-2, -10, 2, 3, -3), "interrupt": (-3, -9, 0, 1, -2),
    "gift": (8, 3, 0, -2, 4), "food": (2, 4, -25, 0, 2), "magic": (12, 2, 0, 0, 3), "memory": (10, 4, -4, -15, 6),
    "promise_kept": (2, 4, 0, -10, 6), "promise_broken": (0, -8, 0, 20, -15), "deep": (6, 6, -8, -2, 4),
    "light": (0, -6, 0, 8, -2), "harm_small": (-4, -10, 4, 15, -8),
}
NAMES = ("fascination", "patience", "hunger", "suspicion", "regard")


def _clip(v):
    return max(0.0, min(100.0, v))


class Moods:
    def __init__(self):
        self.fascination, self.patience, self.hunger, self.suspicion, self.regard = 30.0, 70.0, 20.0, 10.0, 0.0
        self.hunting = False
        self.bites = 0

    def values(self):
        return {k: getattr(self, k) for k in NAMES}

    def _move(self, d, scale=1.0):
        for k, v in zip(NAMES, d):
            if self.suspicion > TRICK and k in ("fascination", "regard") and v > 0:     # (a trick, she thinks)
                self.suspicion = _clip(self.suspicion + v * 0.5)
                continue
            setattr(self, k, _clip(getattr(self, k) + v * scale))

    def heard(self, kind):
        """Something he said or did, in conversation."""
        if kind in HEARD:
            self._move(HEARD[kind])

    def bit(self):
        self.bites += 1
        self.hunger = _clip(self.hunger - 45)
        self.patience = _clip(self.patience + 25)
        self.hunting = False

    def step(self, dt, night, events):
        out = []
        her = night.her
        ex, ey, ez = night.eye
        d = math.dist(her.at(), (ex, ey, ez))
        # the clock: her hunger, always (about half a night to grow hungry from nothing - if nothing else moves it)
        self.hunger = _clip(self.hunger + 0.012 * dt)
        # how he moves, as she feels it through her silk and sees it
        running = night.inp_hurry and night.moved_now > 0
        if running:
            self.patience = _clip(self.patience - 0.06 * dt)
            self.hunger = _clip(self.hunger + 0.02 * dt)
        towards = 0.0
        if night.moved_now > 0 and d < 9:                       # (coming at her)
            look = (math.sin(night.yaw), -math.cos(night.yaw))
            hx, _hy, hz = her.at()
            to = (hx - ex, hz - ez)
            n = math.hypot(*to) or 1.0
            towards = max(0.0, (look[0] * to[0] + look[1] * to[1]) / n)
            if running and towards > 0.7:
                self.patience = _clip(self.patience - 0.4 * dt)
                self.hunger = _clip(self.hunger + 0.15 * dt)
        for e in events:
            kind = e[0]
            if kind == "silk" and e[1] == "step":
                if e[2]:
                    self.hunger, self.patience = _clip(self.hunger + 0.6), _clip(self.patience - 0.4)
                else:
                    self.patience = _clip(self.patience + 0.05)
                    self.regard = _clip(self.regard + 0.02)            # (respect, in how he walks her silk)
            elif kind == "silk" and e[1] == "slip":
                self.hunger, self.patience = _clip(self.hunger + 5), _clip(self.patience - 3)
            elif kind == "silk" and e[1] == "caught":
                self.hunger, self.patience = _clip(self.hunger + 8), _clip(self.patience - 4)
            elif kind == "jump" and night.on is None and night.tremor > 1.0:
                self.hunger = _clip(self.hunger + 1.5)
            elif kind == "swipe":
                self.suspicion = _clip(self.suspicion + 0.5 * e[1])    # (flung from his face: her small ones)
        # watching her, steadily, when she comes to him: a good moment
        if her.lean > 0.6 and d < 9 and night.moved_now == 0:
            look = (math.sin(night.yaw) * math.cos(night.pitch), math.sin(night.pitch), -math.cos(night.yaw) * math.cos(night.pitch))
            hx, hy, hz = her.at()
            to = (hx - ex, hy - ey, hz - ez)
            n = math.sqrt(sum(c * c for c in to)) or 1.0
            if sum(a * b for a, b in zip(look, to)) / n > 0.85:
                self.fascination = _clip(self.fascination + 1.2 * dt)
                self.regard = _clip(self.regard + 0.08 * dt)
        # calm: patience comes back; fascination drifts toward indifference; suspicion fades, slowly
        if not running and towards < 0.5:
            self.patience = _clip(self.patience + (0.03 if self.fascination >= 20 else 0.01) * dt)
        if self.fascination < 20:                               # (bored: her patience goes faster)
            self.patience = _clip(self.patience - 0.02 * dt)
        self.fascination += (30.0 - self.fascination) * min(1.0, 0.002 * dt)
        self.suspicion = _clip(self.suspicion - 0.008 * dt)
        hunting = self.patience <= HUNT_PATIENCE or self.hunger >= LIMIT
        if hunting and not self.hunting:
            out.append(("her", "hunts"))
        self.hunting = hunting
        return out

    # ---- the den's tells ---------------------------------------------------------------------------------------
    def fungus_tint(self):
        """The fungus-light's colour and strength: warmer as she hungers, brighter with fascination, dimmer and cooler
        with suspicion. -> (r, g, b) multipliers on its blue-green."""
        warm = max(0.0, (self.hunger - 45) / 55)
        bright = 0.8 + 0.4 * self.fascination / 100
        cold = max(0.0, (self.suspicion - 40) / 60)
        r = (1.0 + 1.9 * warm) * bright * (1 - 0.3 * cold)
        g = (1.0 - 0.35 * warm) * bright * (1 - 0.35 * cold)
        b = (1.0 - 0.6 * warm) * bright * (1 - 0.15 * cold)
        return (r, g, b)

    def hum_pitch(self):
        return 1.0 + 0.18 * self.hunger / 100
