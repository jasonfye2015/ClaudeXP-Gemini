"""Claudeablo's loot: item bases, magic affixes, random drops, names, prices and tooltips.

Items are plain dicts so they save as JSON:
  {"base": "Long Sword", "ilvl": 12, "rarity": "magic", "affixes": [["dmg_pct", 35], ...],
   "prefix": "Vicious", "suffix": "of the Leech", "ident": False, "qty": 1}
Stats scale with the item level (the depth it dropped at), so a Long Sword from level 40 hits far harder than one
from level 2. Magic (blue) and rare (yellow) items drop unidentified: their powers already work, but you only see
them after a Scroll of Identify or a visit to the Elder.
"""
import random

# ---- bases ------------------------------------------------------------------------------------------------------
# name: (kind, slot, ilvl, stat, requirements (str, dex, mag), value)
#   weapons: stat = (min dmg, max dmg); armour pieces: stat = armour class
BASES = {
    # swords, axes, maces (one hand unless noted)
    "Dagger": ("dagger", "weapon", 1, (1, 4), (0, 0, 0), 60),
    "Short Sword": ("sword", "weapon", 1, (2, 6), (18, 0, 0), 120),
    "Club": ("mace", "weapon", 1, (1, 6), (0, 0, 0), 40),
    "Hand Axe": ("axe", "weapon", 2, (2, 7), (22, 0, 0), 110),
    "Mace": ("mace", "weapon", 3, (3, 8), (24, 0, 0), 200),
    "Long Sword": ("sword", "weapon", 4, (3, 10), (30, 30, 0), 350),
    "Broad Axe": ("axe", "weapon", 6, (4, 12), (40, 0, 0), 450),
    "Morning Star": ("mace", "weapon", 8, (5, 11), (36, 0, 0), 520),
    "Scimitar": ("sword", "weapon", 9, (4, 14), (25, 45, 0), 600),
    "Bastard Sword": ("sword", "weapon", 12, (6, 15), (50, 0, 0), 900),
    "War Hammer": ("mace", "weapon", 14, (6, 18), (55, 0, 0), 1100),
    "Great Sword": ("sword", "weapon", 18, (10, 22), (75, 0, 0), 1800),
    "Grand Axe": ("axe", "weapon", 22, (12, 26), (85, 0, 0), 2400),
    "Maul": ("mace", "weapon", 26, (12, 30), (95, 0, 0), 3000),
    "Runeblade": ("sword", "weapon", 32, (14, 32), (80, 60, 20), 4200),
    # bows
    "Short Bow": ("bow", "weapon", 1, (1, 4), (0, 15, 0), 100),
    "Hunter's Bow": ("bow", "weapon", 3, (2, 6), (20, 35, 0), 300),
    "Long Bow": ("bow", "weapon", 6, (3, 9), (25, 45, 0), 500),
    "Composite Bow": ("bow", "weapon", 10, (4, 12), (30, 55, 0), 900),
    "War Bow": ("bow", "weapon", 16, (6, 16), (45, 70, 0), 1600),
    "Hellfire Bow": ("bow", "weapon", 28, (10, 24), (55, 95, 0), 3600),
    # staves (two hands; add mana)
    "Short Staff": ("staff", "weapon", 1, (2, 4), (0, 0, 20), 120),
    "Long Staff": ("staff", "weapon", 5, (4, 8), (0, 0, 35), 400),
    "Composite Staff": ("staff", "weapon", 12, (5, 10), (0, 0, 50), 1000),
    "War Staff": ("staff", "weapon", 22, (8, 16), (30, 0, 70), 2200),
    "Archon Staff": ("staff", "weapon", 34, (10, 20), (35, 0, 100), 4400),
    # body armour
    "Rags": ("armor", "armor", 1, 2, (0, 0, 0), 10),
    "Quilted Armor": ("armor", "armor", 1, 5, (0, 0, 0), 60),
    "Leather Armor": ("armor", "armor", 3, 8, (0, 0, 0), 150),
    "Studded Leather": ("armor", "armor", 6, 12, (20, 0, 0), 300),
    "Ring Mail": ("armor", "armor", 9, 17, (30, 0, 0), 600),
    "Chain Mail": ("armor", "armor", 13, 22, (35, 0, 0), 900),
    "Scale Mail": ("armor", "armor", 17, 28, (45, 0, 0), 1300),
    "Splint Mail": ("armor", "armor", 22, 34, (55, 0, 0), 1800),
    "Plate Mail": ("armor", "armor", 27, 42, (65, 0, 0), 2600),
    "Full Plate": ("armor", "armor", 33, 52, (80, 0, 0), 3600),
    "Gothic Plate": ("armor", "armor", 40, 64, (95, 0, 0), 5000),
    # helms
    "Cap": ("helm", "helm", 1, 2, (0, 0, 0), 20),
    "Skull Cap": ("helm", "helm", 3, 4, (0, 0, 0), 80),
    "Helm": ("helm", "helm", 7, 7, (25, 0, 0), 250),
    "Full Helm": ("helm", "helm", 13, 11, (35, 0, 0), 600),
    "Crown": ("helm", "helm", 18, 13, (0, 0, 0), 1000),
    "Great Helm": ("helm", "helm", 25, 18, (55, 0, 0), 1700),
    "Bone Visage": ("helm", "helm", 36, 25, (70, 0, 0), 3200),
    # shields
    "Buckler": ("shield", "shield", 1, 3, (0, 0, 0), 40),
    "Small Shield": ("shield", "shield", 3, 6, (25, 0, 0), 120),
    "Large Shield": ("shield", "shield", 8, 10, (40, 0, 0), 400),
    "Kite Shield": ("shield", "shield", 14, 14, (50, 0, 0), 800),
    "Tower Shield": ("shield", "shield", 22, 20, (65, 0, 0), 1500),
    "Gothic Shield": ("shield", "shield", 32, 27, (80, 0, 0), 2800),
    # jewellery (always magic or better)
    "Ring": ("ring", "ring", 2, 0, (0, 0, 0), 300),
    "Amulet": ("amulet", "amulet", 5, 0, (0, 0, 0), 500),
}
TWO_HANDED = {"bow", "staff"}
LARGE_TWO_HANDED = {"Great Sword", "Grand Axe", "Maul"}

# consumables and books: name: (kind, value, ilvl)
SUPPLIES = {
    "Potion of Healing": ("potion", 50, 1),
    "Potion of Mana": ("potion", 50, 1),
    "Potion of Full Healing": ("potion", 160, 8),
    "Potion of Full Mana": ("potion", 160, 8),
    "Potion of Rejuvenation": ("potion", 300, 14),
    "Scroll of Town Portal": ("scroll", 200, 1),
    "Scroll of Identify": ("scroll", 100, 1),
}
SPELLS = {
    # name: (mana, book value, min level to find, class bonus, description)
    "Firebolt": (6, 1000, 1, "Hurls a bolt of fire."),
    "Healing": (10, 1000, 1, "Restores some of your life."),
    "Lightning": (12, 3000, 5, "A crackling bolt that tears through a line of foes."),
    "Fireball": (18, 6000, 10, "A ball of fire that explodes among your enemies."),
    "Town Portal": (24, 3000, 6, "Opens a portal back to town (and back again)."),
    "Chain Lightning": (26, 11000, 18, "Lightning that leaps from foe to foe."),
    "Teleport": (28, 14000, 22, "Blink to where you point."),
    "Nova": (36, 21000, 28, "A ring of lightning bursts out around you."),
    "Inferno": (14, 9000, 15, "Breathes a stream of flame."),
}
for _n, (_mana, _val, _lvl, _desc) in SPELLS.items():
    SUPPLIES[f"Book of {_n}"] = ("book", _val, _lvl)

# ---- affixes ------------------------------------------------------------------------------------------------------
# stat: (allowed kinds, [(min ilvl, name, low, high), ...])  - prefixes then suffixes
WEAPONS = {"dagger", "sword", "axe", "mace", "bow", "staff"}
ARMOUR = {"armor", "helm", "shield"}
JEWEL = {"ring", "amulet"}
PREFIXES = {
    "to_hit": (WEAPONS | JEWEL, [(1, "Bronze", 5, 10), (5, "Iron", 11, 20), (12, "Steel", 21, 35),
                                  (20, "Silver", 36, 50), (30, "Gold", 51, 75), (40, "Platinum", 76, 100)]),
    "dmg_pct": (WEAPONS, [(1, "Jagged", 20, 35), (4, "Deadly", 36, 50), (8, "Heavy", 51, 65),
                          (13, "Vicious", 66, 80), (18, "Brutal", 81, 95), (24, "Massive", 96, 120),
                          (30, "Savage", 121, 150), (38, "Ruthless", 151, 180), (45, "Merciless", 181, 220)]),
    "ac_pct": (ARMOUR, [(1, "Sturdy", 20, 35), (4, "Strong", 36, 50), (9, "Glorious", 51, 65),
                        (14, "Blessed", 66, 80), (20, "Saintly", 81, 100), (27, "Awesome", 101, 130),
                        (34, "Holy", 131, 160), (42, "Godly", 161, 200)]),
    "res_fire": (ARMOUR | JEWEL, [(3, "Red", 10, 20), (10, "Crimson", 21, 30), (20, "Garnet", 31, 45),
                                   (32, "Ruby", 46, 60)]),
    "res_light": (ARMOUR | JEWEL, [(3, "Blue", 10, 20), (10, "Azure", 21, 30), (20, "Lapis", 31, 45),
                                    (32, "Sapphire", 46, 60)]),
    "life": (ARMOUR | JEWEL, [(1, "Fox's", 10, 15), (6, "Jackal's", 16, 25), (12, "Wolf's", 26, 40),
                              (20, "Tiger's", 41, 55), (28, "Lion's", 56, 70), (36, "Mammoth's", 71, 90),
                              (44, "Whale's", 91, 120)]),
    "mana": (JEWEL | {"staff", "helm", "armor"}, [(1, "Spider's", 10, 15), (6, "Raven's", 16, 25),
                                                   (12, "Snake's", 26, 40), (20, "Serpent's", 41, 55),
                                                   (28, "Drake's", 56, 70), (36, "Dragon's", 71, 90),
                                                   (44, "Wyrm's", 91, 120)]),
    "spell_lvl": ({"staff", "amulet"}, [(15, "Angel's", 1, 1), (35, "Arch-Angel's", 2, 2)]),
}
SUFFIXES = {
    "str": (WEAPONS | ARMOUR | JEWEL, [(1, "of Strength", 1, 5), (8, "of Might", 6, 10), (16, "of Power", 11, 15),
                                       (26, "of Giants", 16, 20), (38, "of Titans", 21, 30)]),
    "dex": (WEAPONS | ARMOUR | JEWEL, [(1, "of Dexterity", 1, 5), (8, "of Skill", 6, 10),
                                       (16, "of Accuracy", 11, 15), (26, "of Precision", 16, 20),
                                       (38, "of Perfection", 21, 30)]),
    "mag": (WEAPONS | ARMOUR | JEWEL, [(1, "of Magic", 1, 5), (8, "of the Mind", 6, 10),
                                       (16, "of Brilliance", 11, 15), (26, "of Sorcery", 16, 20),
                                       (38, "of Wizardry", 21, 30)]),
    "vit": (WEAPONS | ARMOUR | JEWEL, [(1, "of Vitality", 1, 5), (8, "of Zest", 6, 10), (16, "of Vim", 11, 15),
                                       (26, "of Vigor", 16, 20), (38, "of Life", 21, 30)]),
    "all": (ARMOUR | JEWEL | WEAPONS, [(20, "of the Sky", 3, 6), (34, "of the Moon", 7, 10),
                                       (45, "of the Heavens", 11, 15)]),
    "leech": (WEAPONS | JEWEL, [(6, "of the Leech", 3, 5), (20, "of Blood", 6, 9)]),
    "speed": (WEAPONS, [(4, "of Readiness", 10, 10), (14, "of Swiftness", 20, 20), (28, "of Speed", 30, 30),
                        (40, "of Haste", 40, 40)]),
    "fire_dmg": (WEAPONS, [(4, "of Burning", 1, 6), (16, "of Flame", 4, 14), (30, "of Hellfire", 10, 30)]),
    "light_dmg": (WEAPONS, [(6, "of Shock", 1, 8), (18, "of Lightning", 4, 18), (32, "of Thunder", 10, 36)]),
    "light_radius": (ARMOUR | JEWEL, [(1, "of Light", 1, 1), (12, "of Radiance", 2, 2)]),
    "thorns": (ARMOUR, [(5, "of Thorns", 1, 3), (18, "of Spikes", 4, 8), (32, "of Barbs", 9, 15)]),
    "regen": (ARMOUR | JEWEL, [(10, "of Regeneration", 2, 4), (26, "of Rejuvenation", 5, 8)]),
}
LABELS = {
    "to_hit": "+{v}% chance to hit", "dmg_pct": "+{v}% damage", "ac_pct": "+{v}% armor",
    "res_fire": "Resist Fire: {v}%", "res_light": "Resist Lightning: {v}%", "life": "+{v} to life",
    "mana": "+{v} to mana", "spell_lvl": "+{v} to all spell levels", "str": "+{v} to Strength",
    "dex": "+{v} to Dexterity", "mag": "+{v} to Magic", "vit": "+{v} to Vitality", "all": "+{v} to all attributes",
    "leech": "Steals {v}% of damage as life", "speed": "{v}% faster attacks", "fire_dmg": "Adds {v} fire damage",
    "light_dmg": "Adds {v} lightning damage", "light_radius": "+{v} to light radius",
    "thorns": "Attackers take {v} damage", "regen": "Regenerates {v} life per second",
}
RARE_A = ["Doom", "Grim", "Blood", "Dread", "Storm", "Bone", "Raven", "Gloom", "Wraith", "Ghoul", "Plague", "Soul",
          "Viper", "Shadow", "Rune", "Fiend", "Hell", "Night", "Skull", "Corpse", "Death", "Wolf", "Demon", "Ash"]
RARE_B = {"weapon": ["Bite", "Fang", "Song", "Edge", "Thirst", "Kill", "Reaver", "Splitter", "Gnash", "Scythe"],
          "armor": ["Shell", "Hide", "Carapace", "Shroud", "Cloak", "Coat", "Wrap", "Mantle"],
          "helm": ["Crown", "Visage", "Brow", "Veil", "Horn", "Mask"],
          "shield": ["Wall", "Guard", "Ward", "Aegis", "Bastion"],
          "ring": ["Loop", "Coil", "Band", "Grip", "Circle"],
          "amulet": ["Eye", "Heart", "Star", "Talisman", "Charm"]}

RARITY_COLOURS = {"normal": "#E8E8E8", "magic": "#7090FF", "rare": "#F0E060", "unique": "#C8A060",
                  "supply": "#E8E8E8"}


def scale(ilvl):
    """How much stronger an item of this level is than its base."""
    return 1.0 + 0.045 * max(0, ilvl - 1)


# ---- making items ----------------------------------------------------------------------------------------------

def make(base, ilvl=1, rarity="normal", rnd=None, ident=None):
    rnd = rnd or random
    if base in SUPPLIES:
        return {"base": base, "ilvl": ilvl, "rarity": "supply", "affixes": [], "ident": True, "qty": 1}
    item = {"base": base, "ilvl": ilvl, "rarity": rarity, "affixes": [], "prefix": "", "suffix": "",
            "ident": True if ident is None else ident, "qty": 1}
    kind = BASES[base][0]
    if kind in JEWEL and rarity == "normal":
        rarity = item["rarity"] = "magic"
    if rarity == "magic":
        picks = rnd.choice([("p",), ("s",), ("p", "s"), ("p", "s")])
        for which in picks:
            _add_affix(item, which, rnd)
    elif rarity == "rare":
        for which in rnd.sample(["p", "p", "p", "s", "s", "s"], rnd.randint(3, 5)):
            _add_affix(item, which, rnd, named=False)
        item["rare_name"] = f"{rnd.choice(RARE_A)} {rnd.choice(RARE_B.get(BASES[base][1], RARE_B['weapon']))}"
    if rarity in ("magic", "rare") and ident is None:
        item["ident"] = False
    return item


def _add_affix(item, which, rnd, named=True):
    kind = BASES[item["base"]][0]
    table = PREFIXES if which == "p" else SUFFIXES
    have = {a for a, _v in item["affixes"]}
    options = [(stat, tiers) for stat, (kinds, tiers) in table.items() if kind in kinds and stat not in have]
    if not options:
        return
    stat, tiers = rnd.choice(options)
    usable = [t for t in tiers if t[0] <= item["ilvl"]] or tiers[:1]
    # higher tiers are rarer: lean towards the middle of what's allowed
    tier = usable[min(len(usable) - 1, int(len(usable) * (rnd.random() ** 0.7)))]
    _lvl, name, lo, hi = tier
    item["affixes"].append([stat, rnd.randint(lo, hi)])
    if named:
        item["prefix" if which == "p" else "suffix"] = name


def random_drop(ilvl, rnd, magic_find=0.0, kinds=None):
    """A random item that could drop at this depth."""
    bases = [b for b, v in BASES.items() if v[2] <= ilvl + 2 and (kinds is None or v[0] in kinds)]
    # newer bases are more likely the deeper you are
    weights = [1.0 + (BASES[b][2] / max(1, ilvl)) * 2 for b in bases]
    base = rnd.choices(bases, weights=weights)[0]
    r = rnd.random() * (1 - magic_find)
    rarity = "rare" if r < 0.06 + ilvl * 0.0015 else "magic" if r < 0.3 + ilvl * 0.003 else "normal"
    return make(base, ilvl, rarity, rnd)


def random_supply(ilvl, rnd):
    names = [n for n, (_k, _v, lvl) in SUPPLIES.items() if lvl <= ilvl and not n.startswith("Book")]
    weights = [6 if "Healing" in n and "Full" not in n else 4 if "Mana" in n and "Full" not in n else
               2 if "Scroll" in n else 1 for n in names]
    return make(rnd.choices(names, weights=weights)[0], ilvl)


# ---- reading items ------------------------------------------------------------------------------------------------

def kind(item):
    return SUPPLIES[item["base"]][0] if item["base"] in SUPPLIES else BASES[item["base"]][0]


def slot(item):
    return None if item["base"] in SUPPLIES else BASES[item["base"]][1]


def two_handed(item):
    return item["base"] in BASES and (BASES[item["base"]][0] in TWO_HANDED or item["base"] in LARGE_TWO_HANDED)


def stat(item, name):
    return sum(v for a, v in item["affixes"] if a == name or (a == "all" and name in ("str", "dex", "mag", "vit")))


def damage(item):
    lo, hi = BASES[item["base"]][3]
    s = scale(item["ilvl"])
    return max(1, round(lo * s)), max(2, round(hi * s))


def armour(item):
    base = BASES[item["base"]][3]
    if not base:
        return 0
    return round(base * scale(item["ilvl"]) * (1 + stat(item, "ac_pct") / 100))


def requirements(item):
    if item["base"] not in BASES:
        return (0, 0, 0)
    s = 1 + 0.012 * item["ilvl"]
    return tuple(round(r * s) for r in BASES[item["base"]][4])


def name(item):
    if item["base"] in SUPPLIES:
        return item["base"] if item.get("qty", 1) == 1 else f"{item['base']} ({item['qty']})"
    if not item["ident"] and item["rarity"] in ("magic", "rare"):
        return item["base"]
    if item["rarity"] == "rare":
        return item.get("rare_name", item["base"])
    return " ".join(x for x in (item.get("prefix"), item["base"], item.get("suffix")) if x)


def colour(item):
    return RARITY_COLOURS.get(item["rarity"], "#E8E8E8")


def value(item):
    if item["base"] in SUPPLIES:
        return SUPPLIES[item["base"]][1] * item.get("qty", 1)
    v = BASES[item["base"]][5] * scale(item["ilvl"])
    for a, x in item["affixes"]:
        v += {"dmg_pct": 12, "ac_pct": 10, "to_hit": 6, "life": 18, "mana": 14, "spell_lvl": 3000, "leech": 400,
              "speed": 80, "all": 450, "fire_dmg": 60, "light_dmg": 50, "light_radius": 300}.get(a, 80) * x
    if item["rarity"] == "rare":
        v *= 1.6
    return int(v)


def sell_price(item):
    v = value(item) // 4
    if not item.get("ident", True):
        v //= 2
    return max(1, v)


def buy_price(item):
    return max(1, int(value(item) * (1.0 if item["base"] in SUPPLIES else 1.25)))


def tooltip(item, player=None):
    """Lines of (text, colour) for hovering over an item."""
    lines = [(name(item), colour(item))]
    if item["base"] in SUPPLIES:
        k = SUPPLIES[item["base"]][0]
        if k == "book":
            spell = item["base"][8:]
            lines.append((SPELLS[spell][3], "#C8C8C8"))
            lines.append((f"Mana: {SPELLS[spell][0]}", "#C8C8C8"))
            lines.append(("Right-click to read", "#A0A0A0"))
        else:
            lines.append(("Right-click to use", "#A0A0A0"))
        return lines
    k = BASES[item["base"]][0]
    if item["rarity"] == "rare" and item["ident"]:
        lines.append((item["base"], colour(item)))
    if k in WEAPONS:
        lo, hi = damage(item)
        lines.append((f"Damage: {lo}-{hi}" + ("  (two-handed)" if two_handed(item) else ""), "#FFFFFF"))
    elif BASES[item["base"]][3]:
        lines.append((f"Armor: {armour(item)}", "#FFFFFF"))
    if item["ident"] or item["rarity"] == "normal":
        for a, v in item["affixes"]:
            lines.append((LABELS[a].format(v=v), "#8098FF"))
    else:
        lines.append(("Not identified", "#FF6060"))
    req = requirements(item)
    for label, need, have in zip(("Strength", "Dexterity", "Magic"), req,
                                 (player.str_, player.dex, player.mag) if player else (999, 999, 999)):
        if need:
            lines.append((f"Requires {need} {label}", "#FF6060" if have < need else "#C8C8C8"))
    lines.append((f"Item level {item['ilvl']}", "#808080"))
    return lines
