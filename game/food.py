"""Food: the crops Claude can grow, the raw things he can find or harvest (crops, meat from beasts, fish from the
water's creatures, mushrooms from the fungal ones, honey from the wasps and bees), and the meals he can cook from
them at his cabin's hearth - each meal a buff that lasts in real time (one to five hours), up to three at once. The
cookbook fills in as he finds the recipes.

The larder (player.larder) keeps counts by key: "seed:carrot", "raw:carrot", "raw:meat", "cooked:stew" ..."""
import time

# crop -> name, game days to grow, what a harvest gives (min, max), seeds back (chance), its price as seed
CROPS = {
    "radish": ("Radish", 1.5, (2, 3), 0.5, 8), "carrot": ("Carrot", 2, (2, 4), 0.5, 10),
    "onion": ("Onion", 2, (2, 3), 0.45, 10), "potato": ("Potato", 3, (3, 5), 0.45, 12),
    "cabbage": ("Cabbage", 3, (1, 2), 0.45, 14), "tomato": ("Tomato", 3, (2, 4), 0.4, 14),
    "strawberry": ("Strawberry", 3, (3, 5), 0.4, 16), "pepper": ("Pepper", 3, (2, 3), 0.4, 16),
    "corn": ("Corn", 4, (2, 3), 0.4, 18), "eggplant": ("Eggplant", 4, (1, 3), 0.4, 18),
    "cauliflower": ("Cauliflower", 4, (1, 2), 0.4, 20), "squash": ("Squash", 4, (1, 3), 0.4, 20),
    "pumpkin": ("Pumpkin", 5, (1, 2), 0.35, 26), "watermelon": ("Watermelon", 5, (1, 2), 0.35, 26),
}
# raw things that aren't crops: name, picture key (items.json "food"), what eating it raw gives (life %, mana %)
RAW = {"meat": ("Raw Meat", "meat", 0.08, 0.0), "fish": ("Raw Fish", "fish", 0.06, 0.04),
       "mushroom": ("Mushroom", "mushroom", 0.03, 0.08), "honey": ("Honeycomb", "honey", 0.06, 0.06)}
RAW_CROP = (0.05, 0.03)                 # a crop eaten raw

# the meals: key -> name, picture, ingredients (raw keys; order doesn't matter), buff, hours, what it says
RECIPES = {
    "roast": ("Roast Haunch", "roast", ["meat"], {"power": 8}, 1, "Charred outside, red in the middle, and very welcome."),
    "grilled": ("Grilled Fish", "grilled", ["fish"], {"regen": 1.5}, 1, "Salt, smoke and a squeeze of nothing."),
    "corncob": ("Buttered Corn", "veg:corn", ["corn"], {"find": 12}, 1, "Gold on the cob. Gold in the pocket, they say."),
    "bakedpotato": ("Baked Potato", "veg:potato", ["potato"], {"life": 25}, 1, "Fluffy, and hotter than any sensible thing."),
    "sausage": ("Hunter's Sausage", "sausage", ["meat", "onion"], {"power": 12, "crit": 3}, 2, "Hesper won't ask what's in it."),
    "jerky": ("Spiced Jerky", "jerky", ["meat", "pepper"], {"swift": 8}, 3, "Chewed on the run, which is where it belongs."),
    "fishpie": ("Fisherman's Pie", "pie", ["fish", "potato"], {"life%": 10, "armour": 10}, 2, "Heavy as a stone. Stays with you like one."),
    "cornbread": ("Harvest Bread", "bread", ["corn", "potato"], {"life": 40, "regen": 0.5}, 2, "A loaf to walk a long way on."),
    "skillet": ("Mushroom Skillet", "pizza", ["mushroom", "onion"], {"mana%": 12, "regen": 1.0}, 2, "Earthy, and a little bit glowing."),
    "pumpkinpie": ("Pumpkin Pie", "pie", ["pumpkin", "honey"], {"haste": 8, "find": 15}, 3, "Sweet enough to make the Deep feel shallower."),
    "tart": ("Strawberry Tart", "ambrosia", ["strawberry", "honey"], {"leech": 1.0, "crit": 2}, 2, "Red as a wound, sweet as an apology."),
    "cooler": ("Melon Cooler", "veg:watermelon", ["watermelon"], {"armour": 8, "frost": 10}, 3, "Cold all the way down."),
    "salad": ("Garden Salad", "fruit", ["cabbage", "carrot", "radish"], {"regen": 2.0, "mana": 30}, 3, "Crisp, green, and smug about it."),
    "stew": ("Hearty Stew", "stew", ["meat", "potato", "carrot"], {"life%": 15, "armour": 15}, 4, "The pot's been on since the town was founded."),
    "fishsoup": ("Fisherman's Soup", "ration", ["fish", "onion", "cauliflower"], {"mana%": 15, "haste": 5}, 3, "Clears the head and the sinuses both."),
    "ham": ("Honeyed Ham", "roast", ["meat", "honey"], {"life": 30, "leech": 0.5}, 2, "Sticky fingers, steady hands."),
    "chili": ("Dragonfire Chili", "chunk", ["meat", "pepper", "tomato"], {"fire": 20, "power": 10}, 5, "It fights back. Then it fights for you."),
    "frostfish": ("Frost-Cured Fish", "grilled", ["fish", "radish"], {"frost": 20}, 3, "Cured in the cold cellar until it tasted of winter."),
    "stormbroth": ("Storm Broth", "jelly", ["mushroom", "cauliflower", "eggplant"], {"storm": 20, "haste": 5}, 4, "It crackles in the bowl. Drink it anyway."),
    "venomstew": ("Toadstool Stew", "mushroom", ["mushroom", "pepper"], {"venom": 20}, 3, "Mother Wren swears it's the safe kind."),
    "ratatouille": ("Garden Ratatouille", "pizza", ["tomato", "eggplant", "squash"], {"power": 10, "haste": 6, "swift": 5}, 4, "Every colour of the plot, in one pot."),
    "feast": ("Feast of the Deep", "ambrosia", ["meat", "fish", "mushroom"], {"power": 15, "life%": 10, "swift": 5}, 5, "A meal for the night before the guardian."),
    "arcanepie": ("Starlight Pie", "pie", ["pumpkin", "strawberry", "honey"], {"arcane": 20, "mana%": 10}, 5, "Baked under the full moon, if you believe Hesper."),
    "hotpot": ("Thornwick Hotpot", "stew", ["potato", "onion", "cabbage"], {"life%": 12, "regen": 1.0}, 3, "What every house in Thornwick has on a cold night."),
}
BUFF_WORDS = {"power": "+{v}% spell damage", "crit": "+{v}% critical chance", "swift": "+{v}% move speed",
              "life%": "+{v}% life", "armour": "+{v} armour", "life": "+{v} life", "regen": "+{v} mana a second",
              "mana%": "+{v}% mana", "mana": "+{v} mana", "haste": "+{v}% casting speed", "find": "+{v}% gold found",
              "leech": "{v}% of damage healed", "fire": "+{v}% fire damage", "frost": "+{v}% frost damage",
              "storm": "+{v}% storm damage", "venom": "+{v}% venom damage", "arcane": "+{v}% arcane damage"}
MAX_BUFFS = 3

# what the dead leave to eat: by monster name
MEAT = {"Giant Rat", "Wolf", "Boar", "Bear", "Deer", "Bog Frog", "Raptor", "Iron Hound", "Glass Hound", "Charnel Hound",
        "Ember Hound", "Root Wyrm", "Fen Adder", "Minotaur", "Ogre", "Troll", "Bog Troll", "Cellar Spider", "The Rat King"}
FISH = {"Eel", "Glub", "Squidle", "Fishfolk", "Drowned Sailor", "The Drowned Knight"}
MUSHROOM = {"Mushnub", "Spore Beast", "Mycelid Crawler", "The Mushroom King", "Bramble Blob", "Green Blob"}
HONEY = {"Marsh Wasp"}


def food_of(monster):
    """What a dead monster may leave to eat ("meat", "fish", "mushroom", "honey" or None)."""
    if monster in MEAT:
        return "meat"
    if monster in FISH:
        return "fish"
    if monster in MUSHROOM:
        return "mushroom"
    if monster in HONEY:
        return "honey"
    return None


def name_of(key):
    """The larder's key -> its name: "seed:carrot" -> Carrot Seeds, "raw:meat" -> Raw Meat, "cooked:stew" -> Hearty Stew."""
    kind, _, k = key.partition(":")
    if kind == "seed":
        return f"{CROPS[k][0]} Seeds"
    if kind == "raw":
        return RAW[k][0] if k in RAW else CROPS[k][0]
    if kind == "cooked":
        return RECIPES[k][0]
    return key


def match(ingredients):
    """The recipe these raw things make (a list of raw keys, order no matter), or None."""
    want = sorted(ingredients)
    for k, r in RECIPES.items():
        if sorted(r[2]) == want:
            return k
    return None


def buff_lines(buff):
    return [BUFF_WORDS[k].format(v=v) for k, v in buff.items()]


def add(larder, key, n=1):
    larder[key] = larder.get(key, 0) + n
    if larder[key] <= 0:
        larder.pop(key, None)


def has(larder, keys):
    need = {}
    for k in keys:
        need[k] = need.get(k, 0) + 1
    return all(larder.get(k, 0) >= n for k, n in need.items())


def active(buffs, now=None):
    """The meals still working: [(recipe key, ends at)] - their time is the wall clock's."""
    now = time.time() if now is None else now
    return [(k, t) for k, t in buffs if t > now]


def bonus(buffs, now=None):
    out = {}
    for k, _t in active(buffs, now):
        for stat, v in RECIPES[k][3].items():
            out[stat] = out.get(stat, 0) + v
    return out
