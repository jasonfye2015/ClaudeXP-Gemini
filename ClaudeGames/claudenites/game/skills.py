"""The three schools Mother Wren teaches: Evocation (harm), Warding (staying alive) and Arcana (mana, speed and luck).
A point comes with each level; what's learned stays learned through death. A skill opens once enough points are in
its school (need). bonus(ranks) -> the stats they add, in the same words as gear's (power, life, haste...)."""

TREES = {
    "Evocation": [
        ("kindling", "Kindling", "+4% Spell Damage", {"power": 4}, 5, 0),
        ("arcane_weight", "Arcane Weight", "+8% Arcane Damage", {"arcane": 8}, 3, 2),
        ("fire_lore", "Fire Lore", "+8% Fire Damage", {"fire": 8}, 3, 2),
        ("rime_lore", "Rime Lore", "+8% Frost Damage", {"frost": 8}, 3, 2),
        ("storm_lore", "Storm Lore", "+8% Storm Damage", {"storm": 8}, 3, 2),
        ("venom_lore", "Venom Lore", "+8% Venom Damage", {"venom": 8}, 3, 2),
        ("keen_eye", "Keen Eye", "+2% chance of a critical hit", {"crit": 2}, 5, 6),
        ("mastery", "Evoker's Mastery", "+15% Spell Damage", {"power": 15}, 1, 15),
    ],
    "Warding": [
        ("thick_skin", "Thick Skin", "+12 Life", {"life": 12}, 5, 0),
        ("warded_robes", "Warded Robes", "+6 Armour", {"armour": 6}, 5, 0),
        ("fleet_foot", "Fleet Foot", "+3% Move Speed", {"swift": 3}, 5, 3),
        ("hearty", "Hearty Draughts", "Health Potions heal 10% more", {"draught": 10}, 3, 5),
        ("second_wind", "Second Wind", "+4% Life", {"life%": 4}, 5, 6),
        ("bloodthirst", "Bloodthirst", "0.5% of damage healed", {"leech": 0.5}, 3, 9),
        ("bulwark", "Bulwark", "+25 Armour", {"armour": 25}, 1, 15),
    ],
    "Arcana": [
        ("deep_well", "Deep Well", "+10 Mana", {"mana": 10}, 5, 0),
        ("flowing_mind", "Flowing Mind", "+0.5 Mana a second", {"regen": 0.5}, 5, 0),
        ("quick_hands", "Quick Hands", "+3% Casting Speed", {"haste": 3}, 5, 3),
        ("gold_sense", "Gold Sense", "+8% Gold Found", {"find": 8}, 3, 3),
        ("thrift", "Thrift", "Wands cost 5% less mana", {"thrift": 5}, 5, 6),
        ("attunement", "Attunement", "+6% Mana", {"mana%": 6}, 3, 9),
        ("archmage", "Archmage's Ease", "+10% Casting Speed", {"haste": 10}, 1, 15),
    ],
}
NODES = {n[0]: (tree, n) for tree, nodes in TREES.items() for n in nodes}


def spent_in(ranks, tree):
    return sum(ranks.get(n[0], 0) for n in TREES[tree])


def can_learn(player, node_id):
    tree, (nid, _name, _what, _eff, top, need) = NODES[node_id]
    return player.skill_points > 0 and player.skills.get(nid, 0) < top and spent_in(player.skills, tree) >= need


def learn(player, node_id):
    if not can_learn(player, node_id):
        return False
    player.skills[node_id] = player.skills.get(node_id, 0) + 1
    player.skill_points -= 1
    player.life = min(player.life, player.max_life())
    return True


def unlearn_cost(player):
    return 40 * player.level


def unlearn_all(player):
    """Mother Wren will take it all back, for a price: every point returned."""
    cost = unlearn_cost(player)
    spent = sum(player.skills.values())
    if not spent or player.gold < cost:
        return False
    player.gold -= cost
    player.skill_points += spent
    player.skills = {}
    player.life = min(player.life, player.max_life())
    player.mana = min(player.mana, player.max_mana())
    return True


def bonus(ranks):
    out = {}
    for nid, r in (ranks or {}).items():
        if nid not in NODES or r <= 0:
            continue
        for k, v in NODES[nid][1][3].items():
            out[k] = out.get(k, 0) + v * r
    return out
