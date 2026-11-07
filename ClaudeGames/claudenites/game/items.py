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
def make_wand(body="birch", level=1, parts=None):
    b = D.WAND_BODIES[body]
    slots = list(parts or [])[:b["slots"]]
    slots += [None] * (b["slots"] - len(slots))
    return {"type": "wand", "body": body, "parts": slots, "level": level, "id": new_id()}


def make_part(kind, tier=1, element=None):
    p = {"type": "part", "kind": kind, "tier": max(1, int(tier)), "id": new_id()}
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


def part_effects(p):
    k = D.PART_KINDS[p["kind"]]
    eff = dict(k["effects"])
    for stat, per in k.get("per_tier", {}).items():
        eff[stat] = eff.get(stat, 0) + per * (p["tier"] - 1)
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
    for stat in rng.sample(pool, k=min(len(pool), [0, 1, 2, 3][rarity] + (1 if rarity == 3 else 0))):
        stats[stat] = affix_value(stat, level, rng)
    if rarity == 3:                                        # a legendary: its main stat doubled
        stats[main] = stats[main] * 2
    return {"type": "gear", "slot": slot, "base": base, "rarity": rarity, "level": level, "stats": stats, "id": new_id()}


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
    return str(it.get("name", "?"))


def item_level(it):
    return it.get("level") or it.get("tier", 1) * 10


def price(it):
    """What a vendor asks for it; they pay a quarter back."""
    t = it.get("type")
    if t == "wand":
        b = D.WAND_BODIES[it["body"]]
        return int(40 * (1 + b["tier"]) ** 1.6 * (1 + 0.08 * it.get("level", 1))) + sum(price(p) // 2 for p in it["parts"] if p)
    if t == "part":
        return int(30 * it["tier"] ** 1.7)
    if t == "gear":
        return int(12 * (1 + it["level"] * 0.35) * (1, 2.2, 4.5, 10)[it["rarity"]])
    return 1


def sell_price(it):
    return max(1, price(it) // 4)


# ---- rolling loot --------------------------------------------------------------------------------------------------
def roll_rarity(rng, depth, luck=0.0):
    r = rng.random() * (1 - min(0.5, luck))
    legend = 0.004 + depth * 0.0004
    rare = 0.05 + depth * 0.002
    magic = 0.30 + depth * 0.002
    if r < legend:
        return 3
    if r < legend + rare:
        return 2
    if r < legend + rare + magic:
        return 1
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
        return make_part(kind, tier, rng.choice(D.ELEMENTS[1:]) if kind == "core" else None)
    bodies = [k for k, b in D.WAND_BODIES.items() if b["tier"] <= tier]
    w = make_wand(rng.choice(bodies), level)
    if rng.random() < 0.5:                                  # found with a part already in it
        w["parts"][0] = make_part("core", tier, rng.choice(D.ELEMENTS[1:]))
    return w


def depth_scale(depth):
    """How much harder a monster is at this depth than at the first floor (a gentle curve, then steeper)."""
    d = max(0, depth - 1)
    return 1 + 0.16 * d + 0.0045 * d * d


def gold_for(depth, rng, find=0.0):
    return int(rng.randint(2, 6) * (1 + depth * 0.35) * (1 + find / 100))


def xp_to_next(level):
    return int(60 * level ** 1.55)
