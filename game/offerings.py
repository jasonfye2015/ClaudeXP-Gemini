"""Offerings (phase 4b): things he finds in her house and gives her in her scenes. What each is worth to her depends on
her mood, the hour, and what she already knows of him - the same gift can delight her early in the night and insult
her later.

    ITEMS                    id -> (name, how it's said he offers it, where it's found)
    finds = Finds(tree)      where the loose ones lie (the ring, the mouse, the moths, the honey)
    finds.near(night)        -> the find he's close to and looking at, or None
    finds.take(night, id)    into his pack (night.pack)
    worth(item, night)       -> ("delight" | "plain" | "insult", [kinds], the moods it moves directly)
    give(item, night)        -> (tier, her answer in the script) - and her moods moved
Orrin's lute string and Maudren's journal are under their cocoons: taken once those are opened (game/cocoons.py)."""
import math

from . import tree as T

ITEMS = {
    "ring": ("a silver ring", "He offers you a silver ring he found in the mud of your roots, among old bones.", "roots"),
    "mouse": ("a live mouse", "He offers you a live mouse, held by its tail, kicking.", "roots"),
    "moths": ("a handful of moths", "He opens his cupped hands: a handful of moths, caught by your fungus.", "fungus"),
    "string": ("Orrin's lute string", "He offers you a string from Orrin Vale's broken lute, taken from beneath him.",
               "orrin"),
    "journal": ("Maudren's journal", "He offers you Maudren Hale's journal, every page filled with your words.",
                "maudren"),
    "honey": ("a comb of honey", "He offers you a comb of honey - your own, from your larder wall.", "larder"),
    "antidote": ("a stoppered phial", "He holds out your own phial - the antidote, from your larder.", "larder"),
}
KEPT = ("antidote",)            # (his to drink, not to give: never offered)
ORDER = ("ring", "mouse", "moths", "string", "journal", "honey")
REACH = 1.5


def _late(night):
    """Past midnight."""
    return night.sky.clock % 1440 < 7 * 60


def worth(item, night):
    """What it's worth to her, now: (tier, kinds for her moods, direct moves {mood: amount})."""
    m = night.moods
    if item == "mouse":
        if m.hunger < 30:
            return "insult", ["demand"], {"patience": -5}                    # (I am not a cat)
        return ("delight" if m.hunger > 55 else "plain"), ["food", "gift"], {"hunger": -25}
    if item == "moths":
        if m.hunger > 70:
            return "insult", ["small_talk"], {"patience": -6}               # (crumbs, when she's starving)
        return ("plain" if _late(night) else "delight"), ["gift"], {"hunger": -6, "fascination": 2}
    if item == "ring":
        if m.regard > 25:
            return "delight", ["gift", "honest"], {"regard": 6, "fascination": 4}
        return "insult", ["gift"], {"suspicion": 5}                         # (a bribe, from a stranger)
    if item == "string":
        if m.fascination > 50:
            return "delight", ["gift", "deep"], {"fascination": 8, "regard": 3}     # (he remembered Orrin)
        return "insult", ["harm_small"], {"suspicion": 10}                  # (a thief, like Wick)
    if item == "journal":
        return ("delight" if not _late(night) else "plain"), ["gift", "deep"], {"suspicion": -5, "regard": 3}
    if item == "honey":
        if m.fascination > 50:
            return "delight", ["food", "gift"], {"fascination": 5, "hunger": -20}  # (her own honey: she's amused)
        return "insult", ["demand"], {"patience": -10, "suspicion": 6}       # (her own honey: he's stolen from her)
    return "plain", ["gift"], {}


ANSWERS = {
    "ring": {"delight": "Silver. Someone's promise, once. You give it to me as though it were yours to give. I will "
                        "wear it on my thought of you.",
             "insult": "A ring, from a stranger in the dark. What do you mean to buy with it?"},
    "mouse": {"delight": "Warm, and kicking. Oh, you do know how to talk to me.",
              "plain": "A mouse. Thoughtful. I will keep it for later.",
              "insult": "I am not a cat, little wizard. I have eaten."},
    "moths": {"delight": "Moths. Soft, and dusty, and drawn to my light. Like you.",
              "plain": "Moths. A little thing, late. Still - thank you.",
              "insult": "Crumbs. I am starving, and you bring me crumbs."},
    "string": {"delight": "Orrin's. You took it from under him for me. He would have liked that - a song, at last.",
               "insult": "You have been stealing from my guests. Wick did that, once. Look where he hangs."},
    "journal": {"delight": "Maudren's book. Every word I ever said to her, and she understood none of them. Will you?",
                "plain": "Her book. I know what is in it. So, now, do you."},
    "honey": {"delight": "My own honey, from my own wall, given back to me. You are either very bold or very foolish. "
                         "I like it.",
              "insult": "That is mine. You took it from my larder, and you offer it to me as a gift?"},
}


def give(item, night):
    """He offers it: it leaves his pack; her moods move. -> (tier, her answer in the script)."""
    tier, kinds, direct = worth(item, night)
    for k in kinds:
        night.moods.heard(k)
    for name, amount in direct.items():
        setattr(night.moods, name, max(0.0, min(100.0, getattr(night.moods, name) + amount)))
    if item in night.pack:
        night.pack.remove(item)
    night.given.append((item, tier))
    answers = ANSWERS[item]
    return tier, answers.get(tier) or answers.get("plain") or answers["delight"]


def hidden_shown(night):
    """The antidote: seen only once a vision through her eyes has shown him where - or while his Light is up."""
    venom, spells = getattr(night, "venom", None), getattr(night, "spells", None)
    return (venom is not None and venom.revealed) or (spells is not None and spells.shining("light") > 0)


class Finds:
    """The loose things in her house, where they lie (the keepsakes are under her guests)."""

    def __init__(self, tree):
        self.tree = tree
        rx, rz = tree.tunnel_point(5.2, T.TUNNEL_HALF - 0.25)
        mx, mz = tree.tunnel_point(-0.2, -0.35)
        fa, fh, _s = T.FUNGI[1]                                          # (the low patch: moths about it)
        fr = tree.wall_r(fa, fh) - 0.7
        start, run = next((s, r) for n, s, r in T.LANDINGS if n == "larder")
        la = tree.theta_of(start + run / 2) + 0.15
        lh = tree.landing_h["larder"]
        lr = tree.wall_r(la, lh + 1.2) - 0.12
        self.spots = {
            "ring": (rx, tree.tunnel_floor(5.2) + 0.02, rz),
            "mouse": (mx, tree.ground(mx, mz) + 0.03, mz),
            "moths": (math.cos(fa) * fr, fh + 0.4, math.sin(fa) * fr),
            "honey": (math.cos(la) * lr, lh + 1.2, math.sin(la) * lr),
        }
        aa = tree.theta_of(start + run / 2) - 0.2                         # (behind her stores, low in the dark)
        ar = tree.wall_r(aa, lh + 0.3) - 0.3
        ax, az = math.cos(aa) * ar, math.sin(aa) * ar
        self.spots["antidote"] = (ax, tree.floor_at(ax, az, lh + 0.5), az)

    def where(self, item, night):
        """Where it is now (the mouse wanders a little)."""
        if item == "mouse":
            return self.mouse(night.time)
        return self.spots[item]

    def mouse(self, t):
        """The mouse, scurrying about its little patch of the roots."""
        x, _y, z = self.spots["mouse"]
        x += 0.35 * math.cos(t * 0.9) + 0.12 * math.sin(t * 2.3)
        z += 0.35 * math.sin(t * 0.7)
        return (x, self.tree.ground(x, z) + 0.03, z)

    def near(self, night):
        ex, ey, ez = night.eye
        look = (math.sin(night.yaw) * math.cos(night.pitch), math.sin(night.pitch),
                -math.cos(night.yaw) * math.cos(night.pitch))
        best = None
        for item in self.spots:
            if item in night.taken or (item == "antidote" and not hidden_shown(night)):
                continue
            p = self.where(item, night)
            d = math.dist(p, (ex, ey, ez))
            if d > REACH:
                continue
            facing = sum(a * (b - c) / d for a, b, c in zip(look, p, (ex, ey, ez)))
            if facing > 0.6 and (best is None or d < best[0]):
                best = (d, item)
        return best[1] if best else None
