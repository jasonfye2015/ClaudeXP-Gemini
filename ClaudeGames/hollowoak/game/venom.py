"""Her venom (phase 4d): if she bites, Claude lives - at first. It stays in him the rest of the night: the edges of his
sight darken and pulse; his hands shake, and spells sometimes come apart in them; what he types to her comes out
slurred and changed; and now and then he sees through her eyes - places and memories otherwise hidden. A second bite
while it's in him ends the night. An antidote is in the den (her larder), and she can choose to give it.

    venom = Venom(rng)
    venom.start() / venom.cure(how)       her bite; the antidote (drunk, or given)
    venom.active, venom.cured
    venom.step(dt, night)                 -> events: ("vision", id) when one begins, ("vision_end", id)
    venom.vision                          the vision he's in, or None: (id, age)
    venom.camera(night)                   where he sees from in it: (eye, yaw, pitch)
    venom.misses()                        a spell, coming apart in his shaking hands?
    slur(text, rng)                       his words, as they come out
Plain Python: the tests poison him."""
import math


FIRST_VISION, EVERY = 40.0, (120.0, 180.0)
VISION_FOR = 7.0
MISS = 0.3
FLOOR = 20.0                    # (while it's in him, his poison never wears below this)
VISIONS = {
    "larder": ("Through her eyes: her larder, in the dark - and behind her stores, a small stoppered phial, green as "
               "the fungus-light. Kept for the ones she means to keep.", "antidote"),
    "him": ("Through her eyes: yourself, small and warm and lit, far below. She has watched you all night. She does "
            "not look away.", "her_eyes"),
    "before": ("Through her eyes, long ago: the oak whole, and green inside - and someone with hands, cutting a word "
               "into its heart.", "vision_before"),
}
ORDER = ("larder", "him", "before")


class Venom:
    def __init__(self, rng):
        self.rng = rng
        self.active = False
        self.cured = None               # (how it left him: "drunk", "given")
        self.t = 0.0
        self.next = 0.0
        self.vision = None
        self.seen = []                  # (visions seen, in order)

    def start(self):
        self.active = True
        self.cured = None
        self.t = 0.0
        self.next = FIRST_VISION

    def cure(self, how):
        self.active = False
        self.cured = how
        self.vision = None

    @property
    def revealed(self):
        """Has a vision shown him where the antidote is?"""
        return "larder" in self.seen

    def misses(self):
        return self.active and self.rng.random() < MISS

    def step(self, dt, night):
        out = []
        if not self.active:
            return out
        self.t += dt
        if self.vision is not None:
            vid, age = self.vision
            age += dt
            if age >= VISION_FOR:
                self.vision = None
                out.append(("vision_end", vid))
            else:
                self.vision = (vid, age)
            return out
        left = [v for v in ORDER if v not in self.seen]
        if left and self.t >= self.next and not night.quiet and night.dying is None:
            vid = left[0]
            self.seen.append(vid)
            self.vision = (vid, 0.0)
            self.next = self.t + VISION_FOR + self.rng.uniform(*EVERY)
            out.append(("vision", vid))
        return out

    def camera(self, night):
        """Where he sees from, through her eyes: (eye, yaw, pitch)."""
        if self.vision is None:
            return None
        vid, age = self.vision
        tree = night.tree
        if vid == "larder":
            target = night.finds.spots["antidote"]                 # (from above it, a little way off: her place)
            th = math.atan2(target[2], target[0])
            eye = (target[0] - math.cos(th + 0.35) * 1.5, target[1] + 1.1, target[2] - math.sin(th + 0.35) * 1.5)
        elif vid == "him":
            eye = night.her.at()
            target = night.eye
        else:
            from .spells import mark_at
            target = mark_at(tree, "crown", 0.0)
            th = math.atan2(target[2], target[0])
            r = tree.wall_r(th, target[1]) - 2.6
            eye = (math.cos(th + 0.3) * r, target[1] + 0.8, math.sin(th + 0.3) * r)
        dx, dy, dz = (target[0] - eye[0], target[1] - eye[1], target[2] - eye[2])
        sway = 0.04 * math.sin(age * 1.3)                          # (her eyes, drifting: it isn't his body)
        return eye, math.atan2(dx, -dz) + sway, math.atan2(dy, math.hypot(dx, dz)) + sway * 0.5


def slur(text, rng):
    """His words through her venom: a letter lost, a sound dragged out, a word stumbled on, two swapped."""
    words = text.split()
    out = []
    for w in words:
        r = rng.random()
        if r < 0.12 and len(w) > 3:
            k = rng.randrange(1, len(w) - 1)
            w = w[:k] + w[k + 1:]                                   # (a letter lost)
        elif r < 0.24 and any(c in w for c in "sS"):
            w = w.replace("s", "sh", 1).replace("S", "Sh", 1)       # (dragged out)
        elif r < 0.32 and len(w) > 2:
            w = w[:2] + "-" + w                                     # (stumbled on)
        elif r < 0.38 and len(w) > 2:
            k = rng.randrange(1, len(w))
            w = w[:k] + w[k - 1] * 2 + w[k:]                        # (a sound held too long)
        out.append(w)
    if len(out) > 3 and rng.random() < 0.4:
        k = rng.randrange(len(out) - 1)
        out[k], out[k + 1] = out[k + 1], out[k]                     # (two words, the wrong way round)
    s = " ".join(out)
    if rng.random() < 0.35:
        s = s.rstrip(".!?") + "..."
    return s
