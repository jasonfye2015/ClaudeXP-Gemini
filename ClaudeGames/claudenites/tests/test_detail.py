"""The Deep's finer detail (game/detail.py) and the rarities of things."""
import random

import numpy as np

from claudenites.engine import groundmap
from claudenites.game import data as D
from claudenites.game import items as I
from claudenites.game import levels
from claudenites.game.player import Player


def test_the_deep_is_detailed():
    for depth in (1, 12, 23, 54):
        L = levels.dungeon(depth, 7)
        rooms = {c for r in L.rooms for c in r.cells()}
        corr = [c for c in L.paths if c not in rooms and L.open_at(*c)]
        assert corr and all(L.amb[y, x] < 0.6 for x, y in corr)              # (the corridors darker)
        assert all(L.amb[y, x] == 1.0 for x, y in list(rooms)[:50] if L.open_at(x, y) and (x, y) not in L.paths)
        assert L.shafts and L.ceils                                           # (light from a grate above)
        for x, z, f, c in L.shafts:
            assert L.open_at(int(x), int(z)) and c > f
        assert L.stain and any(v > 0.5 for v in L.wet.values())
        for (dx, _t, dz, _f) in L.drips:                                      # (a puddle under every drip)
            assert L.wet.get((int(dx), int(dz)), 0) > 0 or (int(dx), int(dz)) in L.water or not L.open_at(int(dx), int(dz))
        names = {s["name"] for s in L.sprites}
        assert any("Bottle" in n for n in names) and ("bones" in names or any("Bone" in n for n in names))
        assert any(d[7] == "decal.stain" for d in L.decals)
        M = groundmap.deep(L)
        assert M.shape == (L.h, L.w, 4) and (M[..., 2][L.solid] == -1).all()
        assert np.allclose(M[..., 1], L.floor)
    cellars = levels.dungeon(2, 3)
    assert len(cellars.boxes) > 20                                            # (the cellars: timber everywhere)


def test_rarities_make_things_better():
    assert [r[0] for r in D.RARITIES] == ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    plain = I.make_wand("willow", 5)
    gold = I.make_wand("willow", 5, rarity=4)
    assert len(gold["parts"]) == len(plain["parts"]) + 1
    a, b = I.wand_stats(plain), I.wand_stats(gold)
    assert b["damage"] > a["damage"] * 1.6 and b["rate"] > a["rate"]
    for kind in D.PART_KINDS:
        p0, p4 = I.make_part(kind, 3, "fire" if kind == "core" else None), I.make_part(kind, 3, "fire" if kind == "core" else None, 4)
        e0, e4 = I.part_effects(p0), I.part_effects(p4)
        for stat, v in e0.items():
            if stat in ("damage", "rate", "homing") and v > 0:
                assert e4[stat] > v, (kind, stat)
            if stat == "mana" and v > 0:
                assert e4[stat] < v, (kind, stat)                             # (its cost lessened, not grown)
            if stat in ("bullets", "bounce", "pierce") and v > 0:
                assert e4[stat] == v + 1
    rng = random.Random(4)
    for r in range(5):
        g = I.make_gear("robe", 20, r, rng)
        assert len(g["stats"]) == 1 + r and I.price(g) > 0
    assert I.price(I.make_part("lens", 3, rarity=3)) > I.price(I.make_part("lens", 3))


def test_rarity_rolls_and_old_saves():
    rng = random.Random(1)
    seen = [I.roll_rarity(rng, 40) for _ in range(20000)]
    counts = [seen.count(k) for k in range(5)]
    assert counts[0] > counts[1] > counts[2] > counts[3] > counts[4] > 0
    found = [I.roll_item(rng, 30) for _ in range(400)]
    assert all("rarity" in it for it in found)
    assert any(it["type"] in ("wand", "part") and it["rarity"] >= 2 for it in found)
    old = {"level": 3, "inventory": [{"type": "gear", "slot": "ring", "base": "Copper Ring", "rarity": 3, "level": 3,
                                      "stats": {"power": 4}, "id": "a"},
                                     {"type": "part", "kind": "lens", "tier": 2, "id": "b"}],
           "wands": [{"type": "wand", "body": "birch", "parts": [None], "level": 1, "id": "c"}, None, None, None]}
    p = Player.from_json(old)
    assert p.inventory[0]["rarity"] == 4                                      # (an old Legendary is Legendary still)
    assert p.inventory[1]["rarity"] == 0 and p.wands[0]["rarity"] == 0
    p2 = Player.from_json(p.to_json())
    assert p2.inventory[0]["rarity"] == 4                                     # (and not made more of twice)
