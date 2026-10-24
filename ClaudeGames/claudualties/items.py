"""What can be picked up: name, where its picture is on the Items sheet (x, y, w, h), what kind of thing it is, and
what it's worth to a trader (in scrap)."""

ITEMS = {
    # medical: used on a body part
    "gauze": ("Gauze", (665, 253, 10, 26), "medical", 2, "Wrap a bleeding part. Soaks through in time."),
    "medkit": ("Medkit", (607, 266, 16, 16), "medical", 8, "Cleans, closes and dresses any wound, and splints a break."),
    "splint": ("Splint", (254, 304, 20, 24), "medical", 4, "Holds a broken limb so it can mend."),
    "acidfruit": ("Acid fruit", (476, 234, 14, 14), "medical", 2, "Burns an infection out of a wound. Stings."),
    "disinfectant": ("Disinfectant", (142, 268, 10, 14), "medical", 5, "Cleans an infected wound properly."),
    "tweezers": ("Tweezers", (90, 41, 7, 5), "medical", 3, "Get glass out of a wound without tearing it."),
    # taken
    "pills": ("Painkillers", (510, 378, 6, 20), "consume", 4, "Dulls the pain for a while and lifts the mood."),
    "syringe": ("Antibiotics", (142, 268, 10, 14), "consume", 7, "Knocks back every infection and the fever."),
    "vial": ("Strange vial", (70, 34, 6, 12), "consume", 5, "Nobody knows. Lifts the mood; costs the head a little."),
    "blanket": ("Blanket", (223, 389, 8, 7), "consume", 5, "Warm and dry again."),
    "water": ("Water", (241, 234, 10, 14), "consume", 2, "Drink."),
    "canteen": ("Canteen", (81, 334, 6, 6), "consume", 3, "Drink."),
    "bottle": ("Bottle", (566, 330, 10, 10), "consume", 2, "Drink."),
    "jar": ("Jar of water", (294, 236, 6, 12), "consume", 1, "Drink; a small one."),
    "bread": ("Bread", (206, 36, 10, 10), "consume", 3, "Eat."),
    "banana": ("Banana", (266, 36, 14, 10), "consume", 2, "Eat."),
    "cheese": ("Cheese", (338, 238, 10, 10), "consume", 3, "Eat."),
    "pancakes": ("Pancakes", (188, 330, 14, 10), "consume", 4, "Eat. Someone's breakfast, long ago."),
    "meat": ("Meat", (774, 267, 8, 15), "consume", 3, "Eat. It's been down here a while."),
    "tin": ("Tin of food", (121, 335, 10, 5), "consume", 4, "Eat."),
    "candy": ("Candy", (634, 31, 14, 15), "consume", 1, "Eat. A little joy."),
    "sweet": ("Sweet", (388, 38, 6, 8), "consume", 1, "Eat. A little joy."),
    # tools
    "flashlight": ("Flashlight", (426, 234, 6, 14), "tool", 6, "F to switch on. Eats batteries."),
    "battery": ("Battery", (403, 378, 10, 20), "tool", 3, "For the flashlight."),
    "torch": ("Torch", (385, 342, 11, 39), "tool", 2, "Light without batteries, while it lasts."),
    "knife": ("Knife", (65, 416, 8, 24), "tool", 4, "Cuts cloth into gauze; gets glass out, roughly."),
    "rope": ("Rope", (361, 352, 16, 29), "tool", 4, "U at a drop: the next fall is a climb down."),
    "shovel": ("Shovel", (342, 348, 9, 34), "tool", 4, "U to dig through the rock under you. Warms you up."),
    "aed": ("AED", (566, 272, 14, 10), "tool", 12, "Restarts a stopped heart - if you get the timing."),
    "stick": ("Stick", (254, 304, 20, 24), "material", 1, "With gauze or cloth: a splint. With cloth: a torch."),
    "cloth": ("Cloth", (647, 253, 10, 26), "material", 1, "Cut into gauze, or part of a splint or torch."),
    "scrap": ("Scrap", (738, 240, 8, 8), "currency", 1, "What the traders want."),
    "crystal": ("Crystal", (61, 236, 8, 12), "currency", 4, "Pretty. Traders pay for it."),
    "bag": ("Pack", (284, 270, 12, 12), "tool", 3, "Four more slots."),
    "hat": ("Hat", (226, 476, 17, 10), "wear", 2, "A little dignity. Mood up while worn."),
    "wrap": ("Scarf", (176, 474, 13, 16), "wear", 2, "Warmer in the cold water."),
    "cargo": ("THE CARGO", (160, 441, 32, 15), "goal", 0, "What you came for."),
}

RECIPES = [
    ("splint", {"stick": 1, "gauze": 1}, "a splint"),
    ("splint", {"stick": 1, "cloth": 1}, "a splint"),
    ("torch", {"stick": 1, "cloth": 1}, "a torch"),
    ("gauze", {"cloth": 1, "knife": 0}, "two gauze (needs a knife)"),
]
FOOD = {"bread", "banana", "cheese", "pancakes", "meat", "tin", "candy", "sweet"}
DRINK = {"water", "canteen", "bottle", "jar"}


def name(key):
    return ITEMS[key][0] if key in ITEMS else key


def kind(key):
    return ITEMS[key][2] if key in ITEMS else "junk"


def value(key):
    return ITEMS[key][3] if key in ITEMS else 1


def blurb(key):
    return ITEMS[key][4] if key in ITEMS else ""
