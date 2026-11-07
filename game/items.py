"""Items as plain dicts (so they save as JSON as they are): wands, wand parts, gear. What a wand does is worked out from
its body and parts each time it's asked (wand_stats); gear's stats are rolled once, when it's found or stocked.

    {"type": "wand", "body": "birch", "parts": [part or None, ...], "level": 1, "id": "..."}
    {"type": "part", "kind": "core", "element": "fire", "tier": 1, "id": "..."}
    {"type": "gear", "slot": "robe", "base": "Apprentice's Robe", "rarity": 0, "level": 1, "stats": {"life": 6}, "id": "..."}
"""
import random

from . import data as D

_ids = random.Random()


def new_id():
    return "%012x" % _ids.getrandbits(48)


# ---- wands ---------------------------------------------------------------------------------------------------------
def make_wand(body="birch", level=1, parts=None, rarity=0):
    b = D.WAND_BODIES[body]
    n = b["slots"] + (1 if rarity >= 3 else 0)              # (an Epic or Legendary wand: a slot more)
    slots = list(parts or [])[:n]
    slots += [None] * (n - len(slots))
    return {"type": "wand", "body": body, "parts": slots, "level": level, "rarity": rarity, "rv": 2, "id": new_id()}


def make_part(kind, tier=1, element=None, rarity=0):
    p = {"type": "part", "kind": kind, "tier": max(1, int(tier)), "rarity": rarity, "rv": 2, "id": new_id()}
    if D.PART_KINDS[kind].get("element"):
        p["element"] = element or "fire"
    return p


def part_name(p):
    k = D.PART_KINDS[p["kind"]]
    name = k["name"].format(el=D.ELEMENT_WORD.get(p.get("element", ""), ""))
    return f"{name} {roman(p['tier'])}"


def roman(n):
    out, vals = "", [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    for v, s in vals:
        while n >= v:
            out, n = out + s, n - v
    return out


def rarity(it):
    return int(it.get("rarity", 0)) if it else 0


def rarity_name(it):
    return D.RARITIES[rarity(it)][0]


def part_effects(p):
    """A part's effects, its tier's growth and its rarity's strength in them: the good grows, the cost shrinks."""
    k = D.PART_KINDS[p["kind"]]
    eff = dict(k["effects"])
    for stat, per in k.get("per_tier", {}).items():
        eff[stat] = eff.get(stat, 0) + per * (p["tier"] - 1)
    r = rarity(p)
    if r:
        m = D.PART_POWER[r]
        for stat, v in list(eff.items()):
            if stat in ("bullets", "bounce", "pierce"):
                eff[stat] = v + (1 if r >= 4 and v > 0 else 0)
            elif stat in ("mana", "spread"):
                eff[stat] = v * m if v < 0 else v / m          # (less mana, tighter - or the cost of it lessened)
            elif v > 0:
                eff[stat] = v * m
            else:
                eff[stat] = v / m
    return eff


def wand_name(w):
    b = D.WAND_BODIES[w["body"]]
    el = wand_stats(w)["element"]
    return f"{b['name']} of {D.ELEMENT_WORD[el]}" if el != "arcane" or any(w["parts"]) else b["name"]


def wand_stats(w, bonus=None):
    """What the wand does, with the wearer's bonuses (power %, haste %, element %) folded in when given."""
    b = D.WAND_BODIES[w["body"]]
    lvl = w.get("level", 1)
    s = {"rate": b["rate"], "speed": b["speed"], "damage": b["damage"] * (1 + 0.11 * (lvl - 1)),
         "mana": b["mana"] * (1 + 0.05 * (lvl - 1)), "bullets": 1, "spread": 2.0, "homing": 0.0, "bounce": 0,
         "pierce": 0, "element": None}
    dmg_mul, rate_mul, speed_mul, mana_mul = 1.0, 1.0, 1.0, 1.0
    for p in w["parts"]:
        if not p:
            continue
        if p.get("element") and s["element"] is None:
            s["element"] = p["element"]
        e = part_effects(p)
        dmg_mul += e.get("damage", 0)
        rate_mul += e.get("rate", 0)
        speed_mul += e.get("speed", 0)
        mana_mul += e.get("mana", 0)
        s["bullets"] += int(e.get("bullets", 0))
        s["spread"] += e.get("spread", 0)
        s["homing"] += e.get("homing", 0)
        s["bounce"] += int(e.get("bounce", 0))
        s["pierce"] += int(e.get("pierce", 0))
    s["element"] = s["element"] or "arcane"
    r = rarity(w)
    dmg_mul *= D.WAND_POWER[r]
    rate_mul += D.WAND_HASTE[r]
    bonus = bonus or {}
    dmg_mul *= 1 + (bonus.get("power", 0) + bonus.get(s["element"], 0)) / 100
    rate_mul *= 1 + bonus.get("haste", 0) / 100
    s["damage"] *= max(0.1, dmg_mul)
    s["rate"] *= max(0.2, rate_mul)
    s["speed"] *= max(0.3, speed_mul)
    s["mana"] *= max(0.2, mana_mul) * (1 - min(0.6, bonus.get("thrift", 0) / 100))
    s["spread"] = max(0.0, s["spread"]) + (s["bullets"] - 1) * 3.0
    s["dps"] = s["damage"] * s["bullets"] * s["rate"]
    return s


def wand_lines(w, bonus=None):
    s = wand_stats(w, bonus)
    out = [f"{D.ELEMENT_WORD[s['element']]} bolts", f"{s['damage']:.0f} damage x {s['bullets']}" if s["bullets"] > 1
           else f"{s['damage']:.0f} damage", f"{s['rate']:.1f} shots a second", f"Bolt speed {s['speed']:.0f}",
           f"{s['mana']:.1f} mana a shot", f"{s['dps']:.0f} damage a second"]
    if s["spread"] > 3:
        out.append(f"Spread {s['spread']:.0f} degrees")
    if s["homing"]:
        out.append("Seeks its target")
    if s["bounce"]:
        out.append(f"Bounces {s['bounce']} times")
    if s["pierce"]:
        out.append(f"Passes through {s['pierce']}")
    return out


# ---- gear ----------------------------------------------------------------------------------------------------------
def affix_value(stat, level, rng):
    _label, base, grow = D.AFFIXES[stat]
    v = (base + grow * (level - 1)) * rng.uniform(0.7, 1.3)
    return round(v, 1) if base < 2 else int(round(v))


def make_gear(slot, level, rarity, rng=None):
    rng = rng or random.Random()
    bases = D.GEAR_BASES[slot]
    base = bases[min(len(bases) - 1, (level - 1) // 20)]
    stats = {}
    main = D.BASE_STAT[slot]
    stats[main] = affix_value(main, level, rng)
    pool = [k for k in D.AFFIXES if k != main]
    for stat in rng.sample(pool, k=min(len(pool), [0, 1, 2, 3, 4][rarity])):
        stats[stat] = affix_value(stat, level, rng)
    if rarity == 3:                                        # an epic: its main stat half again
        stats[main] = _times(stats[main], 1.5)
    if rarity == 4:                                        # a legendary: its main stat doubled, the rest a fifth more
        stats = {k: _times(v, 2.0 if k == main else 1.2) for k, v in stats.items()}
    return {"type": "gear", "slot": slot, "base": base, "rarity": rarity, "level": level, "stats": stats, "rv": 2,
            "id": new_id()}


def _times(v, k):
    return round(v * k, 1) if isinstance(v, float) else int(round(v * k))


def migrate(it):
    """An item from an older save: gear's four rarities become five (its Legendary stays Legendary); wands and parts,
    which had none, are Common."""
    if not isinstance(it, dict) or it.get("rv") == 2:
        return it
    if it.get("type") == "gear" and it.get("rarity", 0) == 3:
        it["rarity"] = 4
    it.setdefault("rarity", 0)
    it["rv"] = 2
    if it.get("type") == "wand":
        for p in it.get("parts", []):
            migrate(p)
    return it


def gear_name(g):
    rname = D.RARITIES[g["rarity"]][0]
    return g["base"] if g["rarity"] == 0 else f"{rname} {g['base']}"


def gear_lines(g):
    return [D.AFFIXES[k][0].format(v=v) for k, v in g["stats"].items()]


def item_name(it):
    t = it.get("type")
    if t == "wand":
        return wand_name(it)
    if t == "part":
        return part_name(it)
    if t == "gear":
        return gear_name(it)
    if t == "larder":
        from .food import name_of
        return name_of(it["key"])
    return str(it.get("name", "?"))


def item_level(it):
    return it.get("level") or it.get("tier", 1) * 10


def price(it):
    """What a vendor asks for it; they pay a quarter back."""
    t = it.get("type")
    if t == "wand":
        b = D.WAND_BODIES[it["body"]]
        return int(40 * (1 + b["tier"]) ** 1.6 * (1 + 0.08 * it.get("level", 1)) * D.RARITY_PRICE[rarity(it)]) + \
            sum(price(p) // 2 for p in it["parts"] if p)
    if t == "part":
        return int(30 * it["tier"] ** 1.7 * D.RARITY_PRICE[rarity(it)])
    if t == "gear":
        return int(12 * (1 + it["level"] * 0.35) * (1, 2, 4, 7, 12)[it["rarity"]])
    return 1


def sell_price(it):
    return max(1, price(it) // 4)


# ---- rolling loot --------------------------------------------------------------------------------------------------
def roll_rarity(rng, depth, luck=0.0):
    """Common most, then Uncommon, Rare, Epic, and now and then Legendary - all likelier the deeper, and with luck."""
    r = rng.random() * (1 - min(0.5, luck))
    edges = (0.003 + depth * 0.0003, 0.014 + depth * 0.0008, 0.06 + depth * 0.002, 0.28 + depth * 0.002)
    acc = 0.0
    for k, e in enumerate(edges):
        acc += e
        if r < acc:
            return 4 - k
    return 0


def roll_item(rng, depth, luck=0.0):
    """One item fit for this depth: gear most often, then wand parts, then a wand."""
    r = rng.random()
    level = max(1, depth + rng.randint(-2, 2))
    if r < 0.55:
        return make_gear(rng.choice(D.GEAR_SLOTS), level, roll_rarity(rng, depth, luck), rng)
    tier = max(1, min(10, 1 + depth // 10 + (1 if rng.random() < 0.25 else 0)))
    if r < 0.88:
        kind = rng.choice(list(D.PART_KINDS))
        return make_part(kind, tier, rng.choice(D.ELEMENTS[1:]) if kind == "core" else None, roll_rarity(rng, depth, luck))
    bodies = [k for k, b in D.WAND_BODIES.items() if b["tier"] <= tier]
    rar = roll_rarity(rng, depth, luck)
    w = make_wand(rng.choice(bodies), level, rarity=rar)
    if rng.random() < 0.5 or rar >= 3:                      # found with a part already in it
        w["parts"][0] = make_part("core", tier, rng.choice(D.ELEMENTS[1:]), max(0, rar - rng.randint(0, 1)))
    return w


def depth_scale(depth):
    """How much harder a monster is at this depth than at the first floor (a gentle curve, then steeper)."""
    d = max(0, depth - 1)
    return 1 + 0.16 * d + 0.0045 * d * d


def gold_for(depth, rng, find=0.0):
    return int(rng.randint(2, 6) * (1 + depth * 0.35) * (1 + find / 100))


def xp_to_next(level):
    return int(60 * level ** 1.55)
