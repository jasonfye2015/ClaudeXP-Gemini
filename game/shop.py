"""What Thornwick's vendors have to sell. Their stock is made from the save's seed and how many times Claude has come
home (so it changes each visit, and is the same if he looks twice), at the depth he's reached."""
import random

from . import data as D
from . import items as I


def stock(vendor, seed, visit, reach):
    """-> a list of items for sale (dicts). reach: the deepest floor Claude has seen."""
    rng = random.Random(f"{seed}:shop:{vendor}:{visit}")
    level = max(1, reach)
    tier = max(1, min(10, 1 + reach // 10))
    out = []
    if vendor == "wandwright":
        bodies = [k for k, b in D.WAND_BODIES.items() if b["tier"] <= tier and k != "birch"] or ["willow"]
        for _ in range(3):
            out.append(I.make_wand(rng.choice(bodies), level))
        kinds = list(D.PART_KINDS)
        for _ in range(6):
            k = rng.choice(kinds)
            out.append(I.make_part(k, max(1, tier - rng.randint(0, 1)), rng.choice(D.ELEMENTS[1:]) if k == "core" else None))
    elif vendor == "outfitter":
        for slot in D.GEAR_SLOTS:
            out.append(I.make_gear(slot, level, rng.choice((0, 0, 1, 1, 2)), rng))
        for _ in range(3):
            out.append(I.make_gear(rng.choice(D.GEAR_SLOTS), level, rng.choice((1, 2)), rng))
    return out


def buy(player, item):
    """Buy one thing: -> True when paid for and in the pack."""
    cost = I.price(item)
    if player.gold < cost or len(player.inventory) >= 48:
        return False
    player.gold -= cost
    player.inventory.append(item)
    return True


def buy_consumable(player, kind):
    cost = D.CONSUMABLES[kind]["price"]
    if player.gold < cost:
        return False
    player.gold -= cost
    player.potions[kind] = player.potions.get(kind, 0) + 1
    return True


def sell(player, item):
    if item not in player.inventory:
        return 0
    player.inventory.remove(item)
    got = I.sell_price(item)
    player.gold += got
    return got
