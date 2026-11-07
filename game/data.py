"""The tables: the ten bands of the Deep (ten floors each, a guardian at every tenth), the monsters (each drawn by one of
Claude and Magic's figures, by its "monster:<name>" mapping), the wand bodies and parts, the gear and the potions.
Numbers here are the base at the band's first floor; game/balance.py scales them with depth."""

ELEMENTS = ("arcane", "fire", "frost", "storm", "venom")
ELEMENT_COLOUR = {                       # the bolt's colour, and its light's
    "arcane": (0.70, 0.45, 1.00),
    "fire": (1.00, 0.55, 0.18),
    "frost": (0.55, 0.85, 1.00),
    "storm": (0.95, 0.95, 0.55),
    "venom": (0.45, 1.00, 0.35),
}
ELEMENT_WORD = {"arcane": "Arcane", "fire": "Fire", "frost": "Frost", "storm": "Storm", "venom": "Venom"}

# ---- the bands -----------------------------------------------------------------------------------------------------
# tex: (wall, floor, ceiling) texture names in assets/textures; tint multiplies them; fog is the far colour and how
# thick; light is the ambient. monsters: names in MONSTERS; guardian: who waits on the band's tenth floor.
BANDS = [
    {"name": "The Root Cellars", "tex": ("t0.wall", "t0.floor", "t0.ceiling"), "tint": (1.0, 0.95, 0.88),
     "fog": ((0.05, 0.04, 0.03), 0.10), "light": 0.20,
     "monsters": ["Giant Rat", "Kobold", "Goblin", "Cellar Spider", "Green Blob"], "guardian": "The Rat King",
     "line": "Under the town the cellars go on further than the town does."},
    {"name": "The Mossway", "tex": ("t1.wall", "ground.moss", "t1.ceiling"), "tint": (0.85, 1.0, 0.82),
     "fog": ((0.03, 0.06, 0.03), 0.11), "light": 0.20,
     "monsters": ["Mushnub", "Spore Beast", "Bog Frog", "Fen Adder", "Mycelid Crawler", "Marsh Wasp"],
     "guardian": "The Mushroom King", "line": "Green on every stone, and the green is breathing."},
    {"name": "The Sunken Halls", "tex": ("t2.wall", "ground.flags", "t2.ceiling"), "tint": (0.78, 0.92, 1.0),
     "fog": ((0.02, 0.05, 0.08), 0.12), "light": 0.18,
     "monsters": ["Drowned", "Eel", "Glub", "Squidle", "Fishfolk", "Drowned Sailor"], "guardian": "The Drowned Knight",
     "line": "Someone built halls down here, and then the water came to look at them."},
    {"name": "The Barrows", "tex": ("t3.wall", "t3.floor", "t3.ceiling"), "tint": (0.92, 0.92, 0.86),
     "fog": ((0.04, 0.04, 0.05), 0.12), "light": 0.16,
     "monsters": ["Skeleton", "Zombie", "Ghoul", "Barrow Wight", "Grave Priest", "Charnel Hound"],
     "guardian": "The Barrow-King", "line": "The dead were laid here with care. They have stopped caring."},
    {"name": "The Glass Caves", "tex": ("solid.cliff", "t2.floor", "solid.cliff"), "tint": (0.85, 0.78, 1.05),
     "fog": ((0.06, 0.04, 0.10), 0.10), "light": 0.24,
     "monsters": ["Crystal Golem", "Shard Wisp", "Glass Hound", "Prism Sentinel"], "guardian": "The Crystal Tyrant",
     "line": "The walls ring when a bolt goes by, and something rings back."},
    {"name": "The Old Foundry", "tex": ("solid.townwall", "ground.cobbles", "t0.ceiling"), "tint": (1.0, 0.82, 0.70),
     "fog": ((0.09, 0.04, 0.02), 0.11), "light": 0.22,
     "monsters": ["Iron Hound", "Foundry Imp", "Bellows Imp", "Slag Golem", "Sellsword"],
     "guardian": "The Foundry Master", "line": "The fires were never put out. Somebody is still feeding them."},
    {"name": "The Thornwild", "tex": ("solid.hedge", "ground.needles", "solid.bark"), "tint": (0.92, 1.0, 0.85),
     "fog": ((0.03, 0.05, 0.02), 0.12), "light": 0.18,
     "monsters": ["Wolf", "Bear", "Root Wyrm", "Thornback", "Bramble Blob", "Bog Troll"], "guardian": "The Mire Mother",
     "line": "A forest that grew downward, looking for a sun it heard about once."},
    {"name": "The Ember Deep", "tex": ("solid.cliff", "ground.dirt", "solid.cliff"), "tint": (1.05, 0.70, 0.55),
     "fog": ((0.12, 0.03, 0.01), 0.10), "light": 0.26,
     "monsters": ["Cinder Imp", "Ember Hound", "Magma Blob", "Raptor", "Pit Fiend", "Ember Drake"],
     "guardian": "The Ember Dragon", "line": "The rock is warm to the hand, and then it is not rock."},
    {"name": "The Bone Court", "tex": ("solid.plaster", "ground.flags", "t3.ceiling"), "tint": (0.95, 0.90, 0.95),
     "fog": ((0.05, 0.03, 0.06), 0.11), "light": 0.17,
     "monsters": ["Wraith", "Vampire", "Bone Colossus", "Dark Elf", "Gargoyle", "Demon"],
     "guardian": "The Bone Patriarch", "line": "A court still sitting, though nobody has come to be judged in an age."},
    {"name": "The Hollow Throne", "tex": ("t3.wall", "t0.floor", "t1.ceiling"), "tint": (0.80, 0.75, 0.95),
     "fog": ((0.02, 0.01, 0.04), 0.13), "light": 0.14,
     "monsters": ["Blue Demon", "Minotaur", "Ogre", "Troll", "Hollow One", "Drakeling"], "guardian": "The Unmade King",
     "line": "Every step down here is a step somebody took before you, and didn't take back."},
]
FLOORS = 100


def band_of(depth):
    """The band a floor is in; past the hundredth (endless), the bands come round again."""
    return BANDS[((max(1, depth) - 1) // 10) % len(BANDS)]


# ---- the monsters --------------------------------------------------------------------------------------------------
# figure: the Claude and Magic figure ("monster:<figure>"), when it isn't the monster's own name.
# kind: melee (closes and strikes), ranged (keeps its distance and casts), swarm (quick, weak, in numbers),
#       brute (slow, heavy), flyer (lifted, erratic). hp/dmg/speed at the band's first floor; xp likewise.
def _m(hp, dmg, speed, kind="melee", element="arcane", xp=None, figure=None, size=1.0, resist=None):
    return {"hp": hp, "dmg": dmg, "speed": speed, "kind": kind, "element": element, "xp": xp or max(1, hp // 3),
            "figure": figure, "size": size, "resist": resist or {}}


MONSTERS = {
    # the Root Cellars
    "Giant Rat": _m(14, 4, 2.6, "swarm"), "Kobold": _m(22, 6, 2.0), "Goblin": _m(26, 7, 2.2),
    "Cellar Spider": _m(18, 5, 2.8, "swarm", "venom"), "Green Blob": _m(36, 6, 1.3, "brute", "venom"),
    "The Rat King": _m(420, 14, 2.2, "brute", figure="The Rat King", size=1.4),
    # the Mossway
    "Mushnub": _m(30, 7, 1.8), "Spore Beast": _m(40, 8, 1.6, "brute", "venom"), "Bog Frog": _m(28, 7, 2.4),
    "Fen Adder": _m(22, 8, 2.8, "swarm", "venom"), "Mycelid Crawler": _m(30, 7, 2.4, "melee", "venom"),
    "Marsh Wasp": _m(18, 6, 3.2, "flyer", "venom"), "The Mushroom King": _m(700, 18, 1.8, "ranged", "venom", size=1.4),
    # the Sunken Halls
    "Drowned": _m(40, 9, 1.8), "Eel": _m(26, 9, 3.0, "swarm"), "Glub": _m(30, 8, 2.0, "ranged", "frost"),
    "Squidle": _m(34, 9, 2.2, "ranged", "frost"), "Fishfolk": _m(44, 10, 2.2), "Drowned Sailor": _m(40, 10, 2.0, "ranged", "frost"),
    "The Drowned Knight": _m(1000, 22, 2.0, "brute", "frost", size=1.3),
    # the Barrows
    "Skeleton": _m(40, 10, 2.0, resist={"venom": 0.5}), "Zombie": _m(56, 11, 1.4, "brute", resist={"venom": 0.5}),
    "Ghoul": _m(42, 11, 2.4, resist={"venom": 0.5}), "Barrow Wight": _m(40, 11, 2.2, "ranged", "frost"),
    "Grave Priest": _m(38, 12, 1.8, "ranged", "arcane"), "Charnel Hound": _m(36, 11, 3.0, "swarm"),
    "The Barrow-King": _m(1400, 26, 2.0, "ranged", "frost", size=1.4),
    # the Glass Caves
    "Crystal Golem": _m(80, 14, 1.4, "brute", resist={"arcane": 0.5}), "Shard Wisp": _m(34, 12, 2.6, "ranged", "arcane"),
    "Glass Hound": _m(44, 13, 3.0, "swarm", "frost"), "Prism Sentinel": _m(70, 15, 1.8, "melee", resist={"arcane": 0.5}),
    "The Crystal Tyrant": _m(1900, 30, 1.9, "brute", "arcane", size=1.3),
    # the Old Foundry
    "Iron Hound": _m(50, 14, 3.0, "swarm", resist={"fire": 0.5}), "Foundry Imp": _m(36, 13, 2.6, "ranged", "fire"),
    "Bellows Imp": _m(38, 13, 2.6, "ranged", "fire"), "Slag Golem": _m(90, 17, 1.4, "brute", "fire", resist={"fire": 0.5}),
    "Sellsword": _m(60, 16, 2.2), "The Foundry Master": _m(2500, 34, 1.9, "brute", "fire", size=1.35),
    # the Thornwild
    "Wolf": _m(50, 15, 3.2, "swarm"), "Bear": _m(100, 19, 2.0, "brute"), "Root Wyrm": _m(70, 17, 2.2, "melee", "venom"),
    "Thornback": _m(60, 16, 2.0), "Bramble Blob": _m(70, 15, 1.6, "brute", "venom"), "Bog Troll": _m(110, 20, 1.8, "brute"),
    "The Mire Mother": _m(3200, 38, 1.8, "ranged", "venom", size=1.5),
    # the Ember Deep
    "Cinder Imp": _m(46, 17, 2.8, "ranged", "fire", resist={"fire": 0.6}), "Ember Hound": _m(58, 18, 3.2, "swarm", "fire"),
    "Magma Blob": _m(90, 18, 1.5, "brute", "fire", resist={"fire": 0.6}), "Raptor": _m(70, 20, 3.4),
    "Pit Fiend": _m(110, 22, 2.0, "melee", "fire"), "Ember Drake": _m(80, 20, 2.6, "flyer", "fire", resist={"fire": 0.6}),
    "The Ember Dragon": _m(4200, 44, 2.0, "ranged", "fire", size=1.2, resist={"fire": 0.5}),
    # the Bone Court
    "Wraith": _m(70, 21, 2.6, "ranged", "frost", resist={"venom": 0.6}), "Vampire": _m(100, 23, 2.6),
    "Bone Colossus": _m(170, 26, 1.4, "brute", resist={"venom": 0.6}), "Dark Elf": _m(80, 22, 2.8, "ranged", "storm"),
    "Gargoyle": _m(110, 22, 2.2, "flyer", resist={"arcane": 0.4}), "Demon": _m(130, 25, 2.4, "melee", "fire"),
    "The Bone Patriarch": _m(5400, 48, 1.9, "ranged", "frost", size=1.3),
    # the Hollow Throne
    "Blue Demon": _m(130, 26, 2.4, "ranged", "storm"), "Minotaur": _m(190, 30, 2.2, "brute"),
    "Ogre": _m(200, 30, 1.7, "brute"), "Troll": _m(170, 27, 2.0, "brute"), "Hollow One": _m(110, 26, 2.8),
    "Drakeling": _m(110, 25, 2.8, "flyer", "fire"),
    "The Unmade King": _m(9000, 60, 2.1, "ranged", "arcane", figure="Pit Fiend", size=2.0),
    # the forest round Thornwick (as strong as Claude is)
    "Deer": _m(22, 0, 3.6, "timid", xp=6), "Boar": _m(34, 7, 2.8),
    "Hedge Wizard": _m(30, 8, 2.0, "ranged", "storm"),
}
GUARDIANS = {b["guardian"] for b in BANDS}


# ---- wands ---------------------------------------------------------------------------------------------------------
# A wand is a body and the parts set in its slots. The body gives the rate (shots a second), the bolt's speed (squares
# a second), its base damage, its mana a shot and how many slots it has. The parts add the rest: a core sets the
# element; lenses, splitters, focusers, quickeners, seekers, rebounders and piercers change the shot.
WAND_BODIES = {
    "birch": {"name": "Birch Wand", "rate": 2.6, "speed": 16.0, "damage": 7.0, "mana": 2.0, "slots": 2, "tier": 0},
    "willow": {"name": "Willow Wand", "rate": 3.6, "speed": 15.0, "damage": 5.5, "mana": 1.6, "slots": 2, "tier": 1},
    "ash": {"name": "Ashwood Wand", "rate": 2.2, "speed": 20.0, "damage": 10.0, "mana": 2.6, "slots": 3, "tier": 1},
    "yew": {"name": "Yew Wand", "rate": 3.0, "speed": 18.0, "damage": 8.5, "mana": 2.2, "slots": 3, "tier": 2},
    "bone": {"name": "Bone Wand", "rate": 1.6, "speed": 14.0, "damage": 16.0, "mana": 3.4, "slots": 3, "tier": 3},
    "ironbark": {"name": "Ironbark Wand", "rate": 2.8, "speed": 19.0, "damage": 11.0, "mana": 2.6, "slots": 4, "tier": 4},
    "crystal": {"name": "Crystal Wand", "rate": 4.2, "speed": 24.0, "damage": 7.5, "mana": 2.0, "slots": 4, "tier": 5},
    "emberwood": {"name": "Emberwood Wand", "rate": 3.2, "speed": 21.0, "damage": 12.0, "mana": 2.8, "slots": 5, "tier": 6},
    "starsteel": {"name": "Starsteel Wand", "rate": 3.6, "speed": 26.0, "damage": 13.0, "mana": 2.8, "slots": 5, "tier": 8},
    "heartwood": {"name": "Heartwood Wand", "rate": 4.0, "speed": 24.0, "damage": 15.0, "mana": 3.0, "slots": 6, "tier": 9},
}
# kind -> what one part of that kind does (at tier 1; "per_tier" grows it). Effects:
#   element: sets the bolt's element (the first core set wins)   damage: x(1 + v) damage
#   bullets: + v bolts a shot (spread across the cone)          spread: + v degrees of cone
#   speed: x(1 + v) bolt speed                                  rate: x(1 + v) shots a second
#   mana: x(1 + v) mana a shot                                  homing: v turn (radians a second)
#   bounce: + v bounces off walls                               pierce: + v monsters passed through
PART_KINDS = {
    "core": {"name": "{el} Core", "effects": {"damage": 0.10}, "per_tier": {"damage": 0.05}, "element": True},
    "lens": {"name": "Lens of Force", "effects": {"damage": 0.30}, "per_tier": {"damage": 0.10}},
    "splitter": {"name": "Splitting Prism", "effects": {"bullets": 2, "spread": 14, "damage": -0.25, "mana": 0.4},
                 "per_tier": {"damage": 0.03}},
    "focus": {"name": "Focusing Ring", "effects": {"spread": -10, "speed": 0.25, "damage": 0.05}, "per_tier": {"damage": 0.04}},
    "quickener": {"name": "Quickening Rune", "effects": {"rate": 0.30, "mana": 0.15}, "per_tier": {"rate": 0.06}},
    "seeker": {"name": "Seeker's Eye", "effects": {"homing": 3.0, "speed": -0.1}, "per_tier": {"homing": 0.4}},
    "rebound": {"name": "Rebounding Band", "effects": {"bounce": 2}, "per_tier": {"damage": 0.04}},
    "piercer": {"name": "Piercing Thorn", "effects": {"pierce": 1, "speed": 0.1}, "per_tier": {"damage": 0.04}},
}
WAND_SLOTS = 4                             # wands Claude can carry ready (1-4 to switch)

# ---- gear ----------------------------------------------------------------------------------------------------------
GEAR_SLOTS = ("hat", "robe", "gloves", "boots", "ring", "amulet")
GEAR_BASES = {
    "hat": ["Cloth Hood", "Wool Cap", "Pointed Hat", "Circlet", "Starweave Hood"],
    "robe": ["Apprentice's Robe", "Traveller's Robe", "Runed Robe", "Battlemage's Robe", "Starweave Robe"],
    "gloves": ["Cloth Wraps", "Leather Gloves", "Runed Gloves", "Spellwright's Gloves", "Starweave Gloves"],
    "boots": ["Sandals", "Soft Boots", "Runed Boots", "Wayfarer's Boots", "Starweave Boots"],
    "ring": ["Copper Ring", "Silver Ring", "Gold Ring", "Moonstone Ring", "Starsteel Ring"],
    "amulet": ["Wooden Charm", "Bone Charm", "Silver Amulet", "Moonstone Amulet", "Star Amulet"],
}
# stat -> (what it reads as, its base roll at item level 1, how it grows a level)
AFFIXES = {
    "life": ("+{v} Life", 6, 1.6), "mana": ("+{v} Mana", 5, 1.3), "armour": ("+{v} Armour", 3, 0.9),
    "regen": ("+{v} Mana a second", 0.4, 0.05), "power": ("+{v}% Spell Damage", 4, 0.35),
    "haste": ("+{v}% Casting Speed", 3, 0.15), "swift": ("+{v}% Move Speed", 3, 0.08),
    "fire": ("+{v}% Fire Damage", 6, 0.4), "frost": ("+{v}% Frost Damage", 6, 0.4), "storm": ("+{v}% Storm Damage", 6, 0.4),
    "venom": ("+{v}% Venom Damage", 6, 0.4), "arcane": ("+{v}% Arcane Damage", 6, 0.4),
    "leech": ("{v}% of damage healed", 0.6, 0.02), "find": ("+{v}% Gold Found", 6, 0.3),
}
BASE_STAT = {"hat": "armour", "robe": "life", "gloves": "haste", "boots": "swift", "ring": "power", "amulet": "mana"}
# the rarities, for everything found: name, rank, colour, and what it does to the thing - a wand's damage and casting
# speed, a part's effects, gear's extra affixes (an Epic wand or better has a slot more; a Legendary part an extra
# bolt, bounce or pierce where it gives any)
RARITIES = [("Common", 0, (0.82, 0.82, 0.8)), ("Uncommon", 1, (0.38, 0.88, 0.42)), ("Rare", 2, (0.35, 0.62, 1.0)),
            ("Epic", 3, (0.76, 0.42, 1.0)), ("Legendary", 4, (1.0, 0.6, 0.16))]
WAND_POWER = (1.0, 1.12, 1.26, 1.42, 1.65)
WAND_HASTE = (0.0, 0.04, 0.08, 0.12, 0.18)
PART_POWER = (1.0, 1.15, 1.32, 1.5, 1.75)
RARITY_PRICE = (1.0, 1.6, 2.5, 4.0, 7.0)

# ---- potions and scrolls -------------------------------------------------------------------------------------------
CONSUMABLES = {
    "health": {"name": "Health Potion", "price": 25, "what": "Heals 40% of your Life at once, and more over three seconds."},
    "mana": {"name": "Mana Potion", "price": 20, "what": "Restores half your Mana."},
    "return": {"name": "Scroll of Return", "price": 60,
               "what": "Read it in the Deep and you're home in the clearing. The way back down stays open to this floor."},
}

# ---- the town ------------------------------------------------------------------------------------------------------
TOWN_NAME = "Thornwick"
VENDORS = {
    "apothecary": {"name": "Hesper", "title": "the Apothecary", "figure": "mage", "tint": (130, 160, 110),
                   "sells": "consumables"},
    "wandwright": {"name": "Old Tamsin", "title": "the Wandwright", "figure": "rogue_hooded", "tint": (150, 110, 70),
                   "sells": "wands"},
    "outfitter": {"name": "Bramwell", "title": "the Outfitter", "figure": "barbarian", "tint": (140, 120, 100),
                  "sells": "gear"},
    "sage": {"name": "Mother Wren", "title": "the Sage", "figure": "mage", "tint": (110, 100, 150), "sells": "skills"},
    "woodcutter": {"name": "Rook", "title": "the Woodcutter", "figure": "barbarian", "tint": (110, 90, 70), "sells": "talk"},
}
