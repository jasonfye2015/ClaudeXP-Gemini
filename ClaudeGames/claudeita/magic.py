"""Claudeita's magic: spells, wands, and casting a wand's spells in order.

A wand is a row of spell slots read left to right. Each cast draws spells until it has a projectile to shoot:
modifiers on the way change every projectile in the cast, and multicasts (Double, Triple, Scatter) draw more
projectiles into the same cast. When the wand reaches its last slot it recharges and starts again. Every spell costs
mana, and adds to the delay before the next cast."""
import random

# kind: "proj" (shoots), "mod" (changes the projectiles of its cast), "multi" (draws more projectiles)
SPELLS = {
    # projectiles
    "Spark Bolt": {"kind": "proj", "mana": 5, "delay": 0.05, "dmg": 4, "speed": 7.0, "life": 40, "colour": "#FFE36E",
                   "size": 1.5, "tier": 0, "desc": "A quick little bolt."},
    "Magic Missile": {"kind": "proj", "mana": 30, "delay": 0.4, "dmg": 18, "speed": 4.0, "life": 80, "boom": 7,
                      "colour": "#9EE6FF", "size": 2.5, "tier": 1, "desc": "A slow missile that explodes."},
    "Bouncing Burst": {"kind": "proj", "mana": 5, "delay": -0.03, "dmg": 4, "speed": 6.0, "life": 140, "bounce": 10,
                       "colour": "#FFB347", "size": 1.5, "tier": 0, "desc": "Bounces off walls many times."},
    "Fireball": {"kind": "proj", "mana": 60, "delay": 0.5, "dmg": 15, "speed": 3.5, "life": 90, "boom": 10,
                 "fire": True, "gravity": 0.06, "colour": "#FF6A1A", "size": 3.0, "tier": 2,
                 "desc": "Arcs, explodes and sets things alight."},
    "Bomb": {"kind": "proj", "mana": 25, "delay": 1.0, "dmg": 60, "speed": 3.0, "life": 70, "boom": 16,
             "gravity": 0.15, "bounce": 2, "fuse": True, "colour": "#3A3A3A", "size": 3.0, "tier": 1,
             "desc": "A bomb that bounces, then blows a big hole."},
    "Energy Orb": {"kind": "proj", "mana": 18, "delay": 0.1, "dmg": 12, "speed": 3.0, "life": 110, "pierce": True,
                   "colour": "#C77DFF", "size": 3.0, "tier": 1, "desc": "A glowing orb that passes through foes."},
    "Digging Bolt": {"kind": "proj", "mana": 0, "delay": 0.03, "dmg": 2, "speed": 6.0, "life": 22, "dig": 2,
                     "colour": "#B88A5A", "size": 1.0, "tier": 0, "desc": "Digs through soft ground."},
    "Luminous Drill": {"kind": "proj", "mana": 10, "delay": -0.02, "dmg": 10, "speed": 8.0, "life": 9, "dig": 3,
                       "drill": True, "pierce": True, "colour": "#FFF6B0", "size": 2.0, "tier": 1,
                       "desc": "A short beam that drills through rock."},
    "Chain Lightning": {"kind": "proj", "mana": 40, "delay": 0.25, "dmg": 20, "speed": 0, "life": 6, "lightning": True,
                        "colour": "#E8F1FF", "size": 1.0, "tier": 2, "desc": "Strikes the nearest foe, then jumps."},
    "Acid Ball": {"kind": "proj", "mana": 20, "delay": 0.2, "dmg": 8, "speed": 3.5, "life": 80, "gravity": 0.08,
                  "splash": "acid", "colour": "#7CE33A", "size": 2.5, "tier": 1, "desc": "Bursts into eating acid."},
    "Water Ball": {"kind": "proj", "mana": 10, "delay": 0.15, "dmg": 3, "speed": 3.5, "life": 80, "gravity": 0.08,
                   "splash": "water", "colour": "#3F8DF0", "size": 2.5, "tier": 0, "desc": "Bursts into water."},
    "Ice Shard": {"kind": "proj", "mana": 12, "delay": 0.1, "dmg": 9, "speed": 5.5, "life": 50, "freeze": True,
                  "colour": "#BDEBFF", "size": 2.0, "tier": 1, "desc": "Sharp, and freezes water it hits."},
    "Black Hole": {"kind": "proj", "mana": 120, "delay": 0.6, "dmg": 6, "speed": 1.6, "life": 110, "dig": 7,
                   "drill": True, "pierce": True, "colour": "#05010A", "size": 5.0, "tier": 3,
                   "desc": "Slowly devours everything in its path."},
    # modifiers
    "Damage Plus": {"kind": "mod", "mana": 5, "delay": 0.1, "add_dmg": 10, "tier": 0, "desc": "+10 damage."},
    "Speed Up": {"kind": "mod", "mana": 3, "delay": 0.0, "speed_x": 1.6, "tier": 0, "desc": "Faster projectiles."},
    "Homing": {"kind": "mod", "mana": 40, "delay": 0.1, "homing": True, "tier": 2, "desc": "Projectiles seek foes."},
    "Bounce": {"kind": "mod", "mana": 1, "delay": 0.0, "add_bounce": 5, "tier": 0, "desc": "Projectiles bounce."},
    "Explosive Shot": {"kind": "mod", "mana": 30, "delay": 0.15, "add_boom": 6, "tier": 1,
                       "desc": "Projectiles explode."},
    "Piercing": {"kind": "mod", "mana": 30, "delay": 0.0, "pierce": True, "tier": 2, "desc": "Pass through foes."},
    "Heavy Shot": {"kind": "mod", "mana": 7, "delay": 0.15, "dmg_x": 1.6, "add_dmg": 5, "speed_x": 0.6, "tier": 1,
                   "desc": "Slower, much harder hitting."},
    "Fire Trail": {"kind": "mod", "mana": 10, "delay": 0.0, "trail": True, "tier": 1, "desc": "Leaves fire behind."},
    # multicasts
    "Double Spell": {"kind": "multi", "mana": 0, "delay": 0.0, "draw": 2, "tier": 1,
                     "desc": "Casts the next two spells at once."},
    "Triple Spell": {"kind": "multi", "mana": 2, "delay": 0.0, "draw": 3, "tier": 2,
                     "desc": "Casts the next three spells at once."},
    "Scatter 4": {"kind": "multi", "mana": 1, "delay": 0.0, "draw": 4, "spread": 18, "tier": 2,
                  "desc": "Four spells at once, scattered."},
}
WAND_NAMES = ("Twig", "Rod", "Scepter", "Staff", "Wand", "Branch", "Spindle", "Baton")
WAND_ADJ = ("Humble", "Crackling", "Ancient", "Whispering", "Bright", "Hungry", "Restless", "Sly", "Grim", "Gilded")


def spells_up_to(tier):
    return [n for n, s in SPELLS.items() if s["tier"] <= tier]


def random_spell(depth, rng=random):
    tier = min(3, int(depth + rng.random() * 1.2))
    pool = spells_up_to(tier)
    weights = [3.0 if SPELLS[n]["kind"] == "proj" else 1.5 for n in pool]
    return rng.choices(pool, weights)[0]


class Wand:
    def __init__(self, slots, mana_max, charge, delay, recharge, spread, name="Wand", colour="#7A5230"):
        self.slots = slots + [None] * 0
        self.mana_max = mana_max
        self.mana = mana_max
        self.charge = charge
        self.delay = delay
        self.recharge = recharge
        self.spread = spread
        self.name = name
        self.colour = colour
        self.cursor = 0
        self.wait = 0.0                      # cast delay or recharge left
        self.recharging = False

    def to_dict(self):
        return {k: getattr(self, k) for k in ("slots", "mana_max", "charge", "delay", "recharge", "spread", "name",
                                              "colour")}

    def tick(self, dt):
        self.mana = min(self.mana_max, self.mana + self.charge * dt)
        if self.wait > 0:
            self.wait = max(0.0, self.wait - dt)
            if self.wait == 0:
                self.recharging = False

    def cast(self):
        """-> [(spell name, [modifier names], spread)] to shoot now, or [] if it can't."""
        if self.wait > 0 or not any(self.slots):
            return []
        shots, mods, want, spread = [], [], 1, self.spread
        delay = self.delay
        start = self.cursor
        while want > 0:
            if self.cursor >= len(self.slots):
                break
            name = self.slots[self.cursor]
            self.cursor += 1
            if name is None:
                continue
            s = SPELLS[name]
            if self.mana < s["mana"]:
                break                         # (not enough mana: the cast fizzles here)
            self.mana -= s["mana"]
            delay += s["delay"]
            if s["kind"] == "mod":
                mods.append(name)
            elif s["kind"] == "multi":
                want += s["draw"] - 1
                spread += s.get("spread", 4)
            else:
                shots.append([name, None, spread])
                want -= 1
        for shot in shots:
            shot[1] = list(mods)
        end = self.cursor >= len(self.slots) or all(n is None for n in self.slots[self.cursor:])
        if end:
            self.cursor = 0
            self.wait = max(delay, self.recharge)
            self.recharging = True
        else:
            self.wait = max(0.03, delay)
        if not shots and self.cursor == start:
            self.wait = 0.2
        return [tuple(s) for s in shots]


def random_wand(depth, rng=random, slots=None):
    """A wand found (or sold) at this depth (0 = the Mines .. 4 = the Hollow Heart): better the deeper."""
    t = depth + rng.random()
    cap = slots or max(2, min(12, int(2 + t * 1.6 + rng.random() * 2)))
    mana_max = int(80 + t * 220 * rng.uniform(0.7, 1.3))
    charge = int(25 + t * 60 * rng.uniform(0.6, 1.4))
    delay = round(max(0.02, 0.3 - t * 0.05 * rng.uniform(0.5, 1.2)), 2)
    recharge = round(max(0.05, 0.9 - t * 0.15 * rng.uniform(0.5, 1.3)), 2)
    spread = round(max(0.0, rng.uniform(0, 12) - t * 2), 1)
    fill = []
    projs = [n for n in spells_up_to(min(3, int(t))) if SPELLS[n]["kind"] == "proj" and n != "Digging Bolt"]
    for i in range(cap):
        if rng.random() < 0.55 + 0.05 * depth:
            fill.append(random_spell(depth, rng) if i else rng.choice(projs))
        else:
            fill.append(None)
    if not any(n and SPELLS[n]["kind"] == "proj" for n in fill):
        fill[0] = rng.choice(projs)
    name = f"{rng.choice(WAND_ADJ)} {rng.choice(WAND_NAMES)}"
    colour = rng.choice(("#7A5230", "#5E6E7A", "#8E3B46", "#3F6E4A", "#6B4FA0", "#B08A2E"))
    return Wand(fill, mana_max, charge, delay, recharge, spread, name, colour)


def starter_wands():
    return [Wand(["Spark Bolt", "Spark Bolt", None], 110, 40, 0.12, 0.35, 3.0, "Apprentice's Wand", "#7A5230"),
            Wand(["Bomb", None], 60, 15, 0.2, 1.2, 0.0, "Miner's Rod", "#5E6E7A")]
