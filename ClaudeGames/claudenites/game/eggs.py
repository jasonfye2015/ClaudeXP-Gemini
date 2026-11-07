"""Secrets, for whoever goes looking. Each is found once a save (player.stats["eggs"]); what they give is made here.

(Kept out of the README on purpose.)"""
import math
import random

from . import items as I

TOTAL = 5                                                  # (the save's own; the title keeps one more of its own)


def found(game, name):
    """Mark a secret found: -> True the first time (and a toast saying so)."""
    eggs = game.player.stats.setdefault("eggs", [])
    if name in eggs:
        return False
    eggs.append(name)
    game.events.append(("secret", name, len(eggs), TOTAL))
    return True


def towel(level):
    rng = random.Random("towel")
    g = I.make_gear("robe", max(10, level), 4, rng)
    g["base"] = "Well-Travelled Towel"
    g["stats"] = {"armour": 42, "life": 42, "swift": 4, "find": 42}
    g["egg"] = True
    return g


def moon_band(level):
    rng = random.Random("moon")
    g = I.make_gear("ring", max(10, level), 4, rng)
    g["base"] = "Moonkissed Band"
    g["stats"] = {"power": 14, "arcane": 30, "mana": 40, "regen": 2.0}
    g["egg"] = True
    return g


def moon_vector(sky):
    """Where the moon hangs (as the sky draws it: engine/atmosphere.py)."""
    ma = math.radians(sky.dial()["moon"])
    v = (math.sin(ma) * 0.94, math.cos(ma), -0.3)
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def phrase(game, vendor, said):
    """Some words get answers no language model gives. -> the reply, or None."""
    s = said.strip().lower()
    if s in ("xyzzy", "plugh"):
        if found(game, "xyzzy"):
            game.player.gold += 42
            return "Nothing happens. ...Then, quietly, your purse is forty-two coins heavier than it was."
        return "Nothing happens. (It only works the once. Most things do.)"
    if "lich" in s and vendor == "sage":
        found(game, "lich")
        return ("Mother Wren goes very still, and the fire in her stall gutters blue. \"Where did you hear that "
                "word, child?\" A long breath. \"Some crowns are put on. Some grow, from the inside, slowly, "
                "and the one who wears it never notices the cold.\" She will not say more today.")
    return None
