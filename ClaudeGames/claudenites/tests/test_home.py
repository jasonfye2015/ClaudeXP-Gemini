"""The homestead: the cabin, its bed, hearth and chest; the farm and its sign; food, meals and their buffs."""
import random
import tempfile
import time

from claudenites.engine import itempics
from claudenites.game import food as F
from claudenites.game import levels, shop
from claudenites.game.farm import Farm
from claudenites.game.player import Player
from claudenites.game.saves import Saves
from claudenites.game.sky import Sky
from claudenites.game.world import Game


def _dry_sky(seed=1):
    s = Sky(seed)
    s.now = lambda: {"kind": "clear", "strength": 0.0}
    return s


def test_the_homestead_is_in_town_and_reachable():
    T = levels.town(3)
    assert T.kind == "town" and len(T.farm_cells) == 20
    for key in ("cabin_door", "sign"):
        assert key in T.spots
    dist = T.distances(int(T.start[0]), int(T.start[1]))
    dx, dz = T.spots["cabin_door"]
    assert dist[int(dz), int(dx)] >= 0 and T.can_stand(dx, dz, 0.2, 0.0)
    sx, sz = T.spots["sign"]
    near = [(x, y) for x in range(int(sx) - 1, int(sx) + 2) for y in range(int(sz) - 1, int(sz) + 2)
            if 0 <= y < T.h and 0 <= x < T.w and dist[y, x] >= 0]
    assert near
    for x, y in T.farm_cells:
        assert not T.solid[y, x] and dist[y, x] >= 0, (x, y)


def test_the_cabin():
    C = levels.cabin(1)
    assert C.kind == "cabin" and C.boxes
    for key in ("bed", "hearth", "stash", "exit"):
        assert C.can_stand(*C.spots[key], 0.2, 0.0), key
    assert sum(1 for c in C.chests if c.get("stash")) == 1
    g = Game.new(seed=5)
    g.go_cabin()
    assert g.level.kind == "cabin" and g.in_town()
    g.x, g.z = C.spots["stash"]
    what, _ = g.near()
    assert what == ("stash",)
    g.x, g.z = C.spots["hearth"]
    assert g.near()[0] == ("hearth",)
    g.interact()
    assert g.dialog == ("hearth",)
    g.leave_cabin()
    assert g.level.kind == "town"


def test_sleep_brings_the_morning_and_mends():
    g = Game.new(seed=6)
    g.go_cabin()
    g.sky.tick(14 * 60)                                       # (the afternoon)
    day = g.sky.day
    g.player.life, g.player.mana = 1, 0
    g.x, g.z = g.level.spots["bed"]
    assert g.near()[0] == ("bed",)
    g.interact()
    assert g.sky.day == day + 1 and abs(g.sky.hour - 6) < 0.05
    assert g.player.life == g.player.max_life() and g.player.mana == g.player.max_mana()
    assert any(e[0] == "sleep" for e in g.events)


def test_crops_grow_only_when_watered():
    s, f, rng = _dry_sky(), Farm(), random.Random(1)
    assert len(f.plots) == 8
    assert f.plant(0, "radish", s.day) and not f.plant(0, "carrot", s.day)
    f.plant(1, "radish", s.day)
    f.grow(s, 600)
    assert f.plots[0]["growth"] == 0                           # (dry: nothing)
    f.water_all(s.day)
    for _ in range(int(1.5 * 1440 / 60) + 30):
        s.tick(60)
        f.water_all(s.day)
        f.grow(s, 60)
    assert f.ripe(0) and f.stage(0) == 4
    got = f.harvest(0, rng)
    assert got["raw:radish"] >= 2 and f.plots[0] is None
    assert f.harvest(0, rng) == {}


def test_rain_and_the_sprinkler_water_it():
    s, f = Sky(2), Farm()
    s.now = lambda: {"kind": "rain", "strength": 0.8}
    f.plant(0, "carrot", s.day)
    f.grow(s, 30)
    assert f.plots[0]["watered"] == s.day and f.plots[0]["growth"] > 0
    d = _dry_sky()
    p = Player()
    p.gold = 10000
    assert f.buy("sprinkler", p) and not f.buy("sprinkler", p)
    d.tick(24 * 60)
    f.grow(d, 10)
    assert f.plots[0]["watered"] == d.day
    assert f.buy("expand", p) and len(f.plots) == 12
    for _ in range(3):
        f.buy("expand", p)
    assert len(f.plots) == 20 and not f.buy("expand", p)


def test_the_farmhand_harvests_and_replants():
    f, p, rng = Farm(), Player(), random.Random(3)
    p.gold = 1000
    f.buy("farmhand", p)
    f.plant(0, "carrot", 0)
    f.plots[0]["growth"] = 1.0
    seeds = {"seed:carrot": 2}
    assert f.tend(rng, seeds, 4)
    assert f.basket.get("raw:carrot", 0) >= 2
    assert f.plots[0] and f.plots[0]["crop"] == "carrot" and seeds["seed:carrot"] == 1


def test_eating_and_the_buffs():
    p = Player()
    p.larder = {"raw:meat": 2, "cooked:stew": 1, "cooked:chili": 1, "cooked:roast": 2, "cooked:tart": 1}
    p.life = 10
    assert "Raw Meat".lower() in p.eat("raw:meat").lower() and p.life > 10
    base_armour = p.armour()
    p.eat("cooked:stew")
    assert p.armour() == base_armour + 15
    for k in ("cooked:chili", "cooked:roast", "cooked:tart"):
        p.eat(k)
    assert len(p.buffs) == 3 and "stew" not in [b for b, _ in p.buffs]     # (three at most: the oldest went)
    p.eat("cooked:roast")
    assert [b for b, _ in p.buffs].count("roast") == 1
    end = dict((b, t) for b, t in p.buffs)["chili"]
    assert 4.9 * 3600 < end - time.time() <= 5 * 3600                   # (five real hours)
    assert F.bonus(p.buffs, time.time() + 6 * 3600) == {}              # (and then gone)
    assert p.eat("seed:carrot") is None and p.eat("raw:fish") is None


def test_recipes():
    assert F.match(["carrot", "meat", "potato"]) == "stew"
    assert F.match(["meat"]) == "roast"
    assert F.match(["radish", "radish"]) is None
    names = set()
    for k, r in F.RECIPES.items():
        assert 1 <= r[4] <= 5 and r[3] and 1 <= len(r[2]) <= 3, k
        for x in r[2]:
            assert x in F.RAW or x in F.CROPS, (k, x)
        for stat in r[3]:
            assert stat in F.BUFF_WORDS, (k, stat)
        names.add(tuple(sorted(r[2])))
    assert len(names) == len(F.RECIPES)                                 # (no two the same pot)
    assert len(F.RECIPES) >= 20


def test_every_food_has_a_picture():
    for crop in F.CROPS:
        for key in (f"seed:{crop}", f"raw:{crop}"):
            assert itempics.larder_picture(key), key
        for st in range(5):
            assert itempics.crop_picture(crop, st), (crop, st)
    for k in F.RAW:
        assert itempics.larder_picture(f"raw:{k}"), k
    for k in F.RECIPES:
        assert itempics.larder_picture(f"cooked:{k}"), k
        assert (itempics.ITEMS / itempics.larder_picture(f"cooked:{k}")).exists()


def test_monsters_leave_meat_and_seeds():
    from claudenites.game import data as D
    from claudenites.game.world import Monster
    for name in F.MEAT | F.FISH | F.MUSHROOM | F.HONEY:
        assert name in D.MONSTERS, name
    g = Game.new(seed=8)
    g.go_floor(1)
    m = Monster("Wolf", g.x, g.z, 1, g.rng, guardian=True)
    for _ in range(3):
        g._loot(m)
    assert g.player.larder.get("raw:meat", 0) >= 9
    assert any(k.startswith("seed:") for k in g.player.larder)


def test_seeds_for_sale():
    st = shop.seed_stock(1, 3, 20)
    assert st[:4] == sorted(F.CROPS, key=lambda k: F.CROPS[k][1])[:4] and len(set(st)) == len(st)
    p = Player()
    p.gold = 9
    n = p.larder.get("seed:radish", 0)
    assert shop.buy_seed(p, "radish") and p.larder["seed:radish"] == n + 1 and p.gold == 1
    assert not shop.buy_seed(p, "pumpkin")


def test_the_homestead_saves():
    with tempfile.TemporaryDirectory() as d:
        S = Saves(d)
        g = Game.new(seed=9)
        g.farm.plant(2, "tomato", 0)
        g.farm.upgrades["sprinkler"] = True
        g.player.stash.append({"type": "part", "kind": "core", "tier": 1, "element": "fire", "id": "x"})
        g.player.stash_larder["raw:fish"] = 4
        g.player.larder["cooked:stew"] = 1
        g.player.eat("cooked:stew")
        g.player.cookbook.append("stew")
        S.save(0, g.to_json())
        h = Game.from_json(S.load(0), 0)
        assert h.farm.plots[2]["crop"] == "tomato" and h.farm.upgrades["sprinkler"]
        assert h.player.stash[0]["element"] == "fire" and h.player.stash_larder["raw:fish"] == 4
        assert h.player.buffs and h.player.buffs[0][0] == "stew" and h.player.cookbook == ["stew"]
