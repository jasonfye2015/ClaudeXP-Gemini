"""The game's rules, played headless."""
import math
import random
import tempfile
from pathlib import Path

import numpy as np

from claudenites.game import data as D
from claudenites.game import items as I
from claudenites.game import levels, shop, skills
from claudenites.game.player import Player
from claudenites.game.saves import Saves
from claudenites.game.world import Game, Input


def _aim(g, inp):
    alive = [m for m in g.monsters if not m.dead]
    if not alive:
        return None
    m = min(alive, key=lambda m: (m.x - g.x) ** 2 + (m.z - g.z) ** 2)
    inp.yaw = math.atan2(m.x - g.x, -(m.z - g.z))
    inp.pitch = math.atan2(m.centre_y - g.eye[1], max(0.1, math.hypot(m.x - g.x, m.z - g.z)))
    return m


def test_every_floor_is_whole():
    """All hundred floors: the way down reachable from where Claude comes in, monsters on open ground, a guardian on
    every tenth (in its hall, with the stairs), and the band's look."""
    for depth in range(1, D.FLOORS + 1):
        L = levels.dungeon(depth, 99)
        sx, sz = int(L.start[0]), int(L.start[1])
        assert L.open_at(sx, sz), depth
        dist = L.distances(sx, sz)
        tx, tz = int(L.stairs[0]), int(L.stairs[1])
        assert dist[tz, tx] > 0, f"floor {depth}: the stairs can't be reached"
        for s in L.spawns:
            assert L.open_at(int(s["x"]), int(s["z"])), (depth, s)
            assert s["monster"] in D.MONSTERS
        guardians = [s for s in L.spawns if s.get("guardian")]
        if depth % 10 == 0:
            assert len(guardians) == 1 and guardians[0]["monster"] == D.band_of(depth)["guardian"], depth
            gx, gz = int(guardians[0]["x"]), int(guardians[0]["z"])
            assert dist[gz, gx] > 0, f"floor {depth}: the guardian can't be reached"
        else:
            assert not guardians
        assert L.name == D.band_of(depth)["name"]
        assert len(L.spawns) >= 6, (depth, len(L.spawns))


def test_floors_are_the_same_from_the_same_seed():
    a, b = levels.dungeon(17, "x:0"), levels.dungeon(17, "x:0")
    assert (a.solid == b.solid).all() and (a.floor == b.floor).all() and a.spawns == b.spawns
    c = levels.dungeon(17, "x:1")
    assert not (a.solid == c.solid).all()


def test_thornwick():
    T = levels.town(3)
    assert T.outdoor and T.depth == 0
    assert {n["vendor"] for n in T.npcs} == set(D.VENDORS)
    for n in T.npcs:
        assert T.can_stand(n["x"], n["z"], 0.2, 0.0), n
    assert T.can_stand(T.start[0], T.start[1], 0.24, 0.0)
    assert T.portal and len(T.houses) >= 4
    dist = T.distances(int(T.start[0]), int(T.start[1]))
    for n in T.npcs:
        assert dist[int(n["z"]), int(n["x"])] >= 0, n


def test_every_monster_has_a_figure():
    from claudenites.engine.figures import Pack
    p = Pack.load()
    for name, m in D.MONSTERS.items():
        fig = p.figure("monster:" + (m["figure"] or name))
        assert fig, name
        model = p.model(fig["model"])
        assert model.n_joints <= 64, (name, model.n_joints)
        for clip in ("idle", "walk"):
            if model.has(clip):
                J = model.skin_matrices(clip, 0.3)
                assert np.isfinite(J).all(), (name, clip)
        assert model.height() > 0
    for v in D.VENDORS.values():
        p.model(v["figure"])
    w = p.model("gear:wand")
    assert len(w.positions) > 10


def test_plants_and_textures():
    from claudenites.engine.figures import Plants
    P = Plants.load()
    T = levels.town(1)
    for name in {p["model"] for p in T.props}:
        pos, col, idx = P.mesh(name)
        assert len(idx) % 3 == 0 and idx.max() < len(pos)
    tex = Path(__file__).resolve().parents[1] / "assets" / "textures"
    for b in D.BANDS:
        for t in b["tex"]:
            assert (tex / f"{t}.jpg").exists(), t
    for d in (1, 25, 63, 95):
        for p in levels.dungeon(d, 1).props:
            P.mesh(p["model"])


def test_a_fight_on_the_first_floor():
    g = Game.new(seed=11)
    g.go_floor(1)
    inp = Input()
    p = g.player
    p.potions["health"] = 50
    p.potions["mana"] = 50
    L = g.level
    for _ in range(60 * 90):
        if _aim(g, inp) is None:
            break
        m = min((m for m in g.monsters if not m.dead), key=lambda m: (m.x - g.x) ** 2 + (m.z - g.z) ** 2)
        if not L.line_of_sight(g.x, g.z, g.eye[1], m.x, m.z, m.centre_y) or math.hypot(m.x - g.x, m.z - g.z) > 8:
            # (the bot doesn't find its way: it stands somewhere in sight of the nearest one)
            for (x, y) in L.open_squares():
                d = math.hypot(x + 0.5 - m.x, y + 0.5 - m.z)
                if 2.5 < d < 5 and L.line_of_sight(x + 0.5, y + 0.5, 0.6 + L.floor[y, x], m.x, m.z, m.centre_y):
                    g.x, g.z, g.y = x + 0.5, y + 0.5, float(L.floor[y, x])
                    break
            _aim(g, inp)
        inp.fire = True
        if p.life < p.max_life() * 0.4:
            g.drink("health")
        if p.mana < 5:
            g.drink("mana")
        g.step(1 / 60, inp)
        if g.depth == 0:
            break
    assert p.stats["kills"] >= 3, p.stats
    assert p.gold > 30
    assert p.xp > 0 or p.level > 1


def test_death_keeps_what_he_has():
    g = Game.new(seed=2)
    g.go_floor(1)
    g.run_floor = 7
    p = g.player
    p.gold = 500
    p.add_xp(400)
    lvl = p.level
    p.inventory.append(I.make_gear("robe", 5, 2))
    p.life = 0
    g.step(0.02, Input())
    assert g.depth == 0 and g.run_floor == 1
    assert p.gold == 500 and p.level == lvl and len(p.inventory) == 1
    assert p.life == p.max_life() and p.stats["deaths"] == 1


def test_stairs_and_the_scroll():
    g = Game.new(seed=3)
    g.go_floor(4)
    g.descend()
    assert g.depth == 5 and g.run_floor == 5
    g.stairs_home()
    assert g.depth == 0 and g.run_floor == 6
    g.go_floor(g.run_floor)
    n = g.player.potions["return"]
    assert g.read_return() and g.depth == 0 and g.player.potions["return"] == n - 1
    assert g.run_floor == 6
    # a guardian seals the stairs until it falls
    g.go_floor(10)
    L = g.level
    g.x, g.z = L.stairs
    what, _ = g.near()
    assert what == ("sealed",)
    boss = next(m for m in g.monsters if m.guardian)
    g._kill(boss)
    what, _ = g.near()
    assert what == ("stairs",)


def test_wands_are_built_from_parts():
    w = I.make_wand("birch")
    base = I.wand_stats(w)
    assert base["element"] == "arcane" and base["bullets"] == 1
    w["parts"][0] = I.make_part("core", 1, "fire")
    w["parts"][1] = I.make_part("splitter", 1)
    s = I.wand_stats(w)
    assert s["element"] == "fire" and s["bullets"] == 3 and s["spread"] > base["spread"]
    assert s["mana"] > base["mana"]
    q = I.make_wand("willow", parts=[I.make_part("quickener", 3)])
    assert I.wand_stats(q)["rate"] > D.WAND_BODIES["willow"]["rate"]
    assert I.wand_stats(w, {"power": 50})["damage"] > s["damage"]
    assert "Fire" in I.wand_name(w)
    # in the game: three bolts a shot
    g = Game.new(seed=4)
    g.go_floor(1)
    g.player.wands[0] = w
    g.player.mana = 100
    inp = Input()
    inp.fire = True
    g.step(0.01, inp)
    assert len(g.bolts) == 3 and all(b.element == "fire" for b in g.bolts)


def test_the_pack():
    p = Player()
    robe = I.make_gear("robe", 3, 1, random.Random(1))
    p.give(robe)
    life = p.max_life()
    assert p.equip(robe) and p.gear["robe"] is robe and robe not in p.inventory
    assert p.max_life() > life
    assert p.unequip("robe") and robe in p.inventory
    part = I.make_part("lens", 2)
    p.give(part)
    w = p.wands[0]
    assert p.set_part(w, 0, part) and w["parts"][0] is part and part not in p.inventory
    assert p.set_part(w, 0, None) and part in p.inventory
    wand = I.make_wand("ash")
    p.give(wand)
    assert p.ready_wand(wand, 1) and p.wands[1] is wand
    for _ in range(60):
        p.give(I.make_part("lens", 1))
    assert len(p.inventory) == 48


def test_loot_and_levels():
    rng = random.Random(5)
    kinds = {I.roll_item(rng, 30)["type"] for _ in range(300)}
    assert kinds == {"gear", "part", "wand"}
    for it in (I.roll_item(rng, d) for d in (1, 50, 100) for _ in range(30)):
        assert I.price(it) > 0 and I.item_name(it)
    p = Player()
    assert p.add_xp(I.xp_to_next(1) + 1) == 1 and p.level == 2 and p.skill_points == 1


def test_skills():
    p = Player()
    assert not skills.learn(p, "kindling")
    p.skill_points = 10
    assert skills.learn(p, "kindling") and p.skills["kindling"] == 1
    assert not skills.learn(p, "fire_lore")                   # (needs 2 in Evocation)
    assert skills.learn(p, "kindling") and skills.learn(p, "fire_lore")
    assert p.bonus()["power"] == 8 and p.bonus()["fire"] == 8
    life = p.max_life()
    skills.learn(p, "thick_skin")
    assert p.max_life() == life + 12
    p.gold = 1000
    assert skills.unlearn_all(p) and p.skill_points == 10 and not p.skills


def test_shops():
    a = shop.stock("wandwright", 1, 3, 12)
    b = shop.stock("wandwright", 1, 3, 12)
    assert [I.item_name(x) for x in a] == [I.item_name(x) for x in b]
    assert any(x["type"] == "wand" for x in a) and any(x["type"] == "part" for x in a)
    gear = shop.stock("outfitter", 1, 3, 12)
    assert {x["slot"] for x in gear} >= set(D.GEAR_SLOTS)
    p = Player()
    p.gold = 10 ** 6
    assert shop.buy(p, gear[0]) and gear[0] in p.inventory
    got = shop.sell(p, gear[0])
    assert got == I.sell_price(gear[0]) and gear[0] not in p.inventory
    n = p.potions["health"]
    assert shop.buy_consumable(p, "health") and p.potions["health"] == n + 1


def test_saves():
    with tempfile.TemporaryDirectory() as d:
        S = Saves(d)
        assert S.summary(0) is None
        g = Game.new(seed=9)
        g.player.gold = 777
        g.player.inventory.append(I.make_part("core", 2, "frost"))
        g.run_floor = 12
        S.save(1, g.to_json())
        info = S.summary(1)
        assert info["gold"] == 777 and info["floor"] == 12
        h = Game.from_json(S.load(1), 1)
        assert h.player.gold == 777 and h.run_floor == 12 and h.depth == 0
        assert h.player.inventory[0]["element"] == "frost"
        assert I.wand_stats(h.player.wand())["element"] == "arcane"
        S.delete(1)
        assert S.load(1) is None
