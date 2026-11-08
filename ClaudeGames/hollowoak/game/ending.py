"""The endings that dawn brings (Supper has its own: game/death.py). The light comes down into the den from the
crown; her last words to him, in her hand and her voice; then the dark, and the line that says which ending it was.

    ending = Ending(name)
    ending.step(dt)     -> events: ("ending", "line", text) when she speaks
    ending.glow         0..1, the dawn light down into the den
    ending.black        0..1, the dark after
    ending.show_line    her words, while they're up
    ending.done         over: the card is showing
"""
ORDER = ("Supper", "Cast out", "Dawn", "Bound", "The gift", "The hidden", "Fire", "Spellbound")
LINES = {
    "Dawn": ("Go home, little wizard. Come back when you have something new to tell me.",
             "She let you go, curious. That evening, on your doorstep: a square of silk."),
    "Cast out": ("You are not worth the rest of you. Go, before I change my mind.",
                 "You woke in the forest at first light, her venom in you, alone. The oak was silent."),
    "Bound": ("Then stay. Hold still. It will not hurt as much as you fear.",
              "Wrapped in silk at your own asking. She hums to you, sometimes, in the long nights."),
    "The gift": ("Here: my venom, and a secret. Death is a door, little wizard - and some of us learn to walk back "
                 "through it.",
                 "You left at dawn with her venom in your blood, and the first word of something older than death."),
    "The hidden": ("Ilsabet. Say it once more, little wizard, so I know I did not dream it.",
                   "At first light she told you everything she had been. You left knowing the oldest name in the forest "
                   "- and she, for the first time in three hundred years, was known."),
    "Spellbound": ("You never once looked away, little wizard. Sleep, now. Come back awake.",
                   "You woke on your own doorstep at first light, with no memory of the night. Your notebook was full - "
                   "in your own hand, but slower, more careful, as if someone had guided it."),
    "Fire": ("Not the silk - not the silk - go. Go, little wizard - the roots - now!",
             "The Hollow Oak burned until morning. You came out through the roots with your sleeves alight. Of her, "
             "nothing was found - not a leg, not a thread."),
}
# each ending's own scene: the light it comes in (r, g, b), whether she's before him for it, and what else is drawn
LOOK = {"Dawn": ((150, 118, 86), True, None), "Cast out": ((70, 82, 100), False, "cold"),
        "Bound": ((130, 126, 130), True, "silk"), "The gift": ((96, 140, 92), True, "venom"),
        "The hidden": ((170, 128, 60), True, "name"), "Fire": ((220, 96, 30), False, "fire"),
        "Spellbound": ((118, 108, 150), True, "dream")}
LIGHT, SPEAK, QUIET, CARD = 3.0, 2.6, 9.5, 11.5


def number(name):
    return ORDER.index(name) + 1


def card(name):
    return f"Ending {number(name)} of {len(ORDER)}: {name}"


class Ending:
    def __init__(self, name):
        self.name = name
        self.her, self.after = LINES[name]
        self.light, self.staged, self.fx = LOOK[name]
        self.t = 0.0
        self.glow = 0.0
        self.black = 0.0
        self.show_line = None
        self.done = False
        self._said = False

    def step(self, dt):
        self.t += dt
        out = []
        t = self.t
        self.glow = min(1.0, t / LIGHT)
        if t >= SPEAK and not self._said:
            self._said = True
            out.append(("ending", "line", self.her))
        self.show_line = self.her if SPEAK <= t < QUIET + 1.0 else None
        self.black = max(0.0, min(1.0, (t - QUIET) / (CARD - QUIET)))
        self.done = t >= CARD
        return out
