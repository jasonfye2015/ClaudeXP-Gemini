"""The special floors (the Dreaming, a Hoard, a Den, Drowned), the coloured doors and their keys, and the puzzles."""
from collections import Counter

from claudenites.game import data as D
from claudenites.game import features, levels
from claudenites.game.world import Bolt, Game


def _floor_with(test, seed="f", top=100):
    for d in range(1, top):
        L = levels.dungeon(d, seed)
        if test(L):
            return d, L
    raise AssertionError("no floor like that")


def test_special_floors_come_now_and_then():
    seen = Counter(features.special_of(d, "s") for d in range(1, 101))
    assert set(seen) >= {None, "dream", "hoard", "den", "drowned"}
    assert 8 <= sum(v for k, v in seen.items() if k) <= 35
    assert all(features.special_of(d, "s") is None for d in (1, 10, 20, 50, 100))     # (never the first, nor a guardian's)


def test_each_special_is_what_it_says():
    for sp in features.SPECIALS:
        d = next(d for d in range(2, 100) if features.special_of(d, "s") == sp)
        L = levels.dungeon(d, "s")
        assert L.special == sp and features.SPECIALS[sp][0] in L.name
        if sp == "dream":
            assert L.ghosts and len(L.spawns) >= 6
        if sp == "hoard":
            assert sum(p["kind"] == "gold" for p in L.pickups) > 25 and len(L.gold_squares) > 5
        if sp == "den":
            assert L.den and {s["monster"] for s in L.spawns} == {L.den} and len(L.spawns) > 15
        if sp == "drowned":
            assert len(L.water) > 60 and L.pours
            assert (int(L.stairs[0]), int(L.stairs[1])) not in L.water


def test_the_dreaming_s_ghosts_are_harmless_and_untouchable():
    d = next(d for d in range(2, 100) if features.special_of(d, "s") == "dream")
    g = Game.new(seed=1)
    g.go_floor(d)
    g.level = levels.dungeon(d, "s")
    g._enter(g.level)
    assert g.ghosts
    gh = g.ghosts[0]
    g.monsters = []
    life = g.player.life
    g.x, g.z = gh.x + 0.2, gh.z
    for _ in range(60):
        g._ghosts(0.05)
    assert g.player.life == life and gh not in g.monsters
    g.bolts = [Bolt(gh.x - 1, gh.centre_y, gh.z, 8, 0, 0, 50, "fire")]
    g._bolts(0.3)
    assert gh.hp == gh.max_hp


def test_doors_keys_and_the_vault():
    d, L = _floor_with(lambda L: any(x["colour"] != "rune" for x in L.doors))
    door = next(x for x in L.doors if x["colour"] != "rune")
    key = next(p for p in L.pickups if p["kind"] == "key" and p["colour"] == door["colour"])
    shut = features.reach(L)
    assert (int(key["x"]), int(key["z"])) in shut                 # (the key: reachable with the door shut)
    assert (door["x"], door["y"]) not in shut
    assert (int(L.stairs[0]), int(L.stairs[1])) in shut           # (and the way down never behind a door)
    rx, ry, rw, rh = door["room"]
    assert any(rx <= c["x"] < rx + rw and ry <= c["z"] < ry + rh for c in L.chests)
    assert not L.can_stand(door["x"] + 0.5, door["y"] + 0.5, 0.24, L.floor[door["y"], door["x"]])
    g = Game.new(seed=2)
    g._enter(L)
    g.monsters = []
    g.x, g.z = door["x"] + 0.5, door["y"] + 0.5
    for dx, dz in ((0, 1.1), (0, -1.1), (1.1, 0), (-1.1, 0)):
        if L.can_stand(door["x"] + 0.5 + dx, door["y"] + 0.5 + dz, 0.24, 0) and (int(door["x"] + 0.5 + dx), int(door["y"] + 0.5 + dz)) in shut:
            g.x, g.z = door["x"] + 0.5 + dx, door["y"] + 0.5 + dz
            break
    what, label = g.near()
    assert what[0] == "locked" and "locked" in label
    L.pickups.remove(key)
    g._take(key)
    assert door["colour"] in g.keys
    what, label = g.near()
    assert what[0] == "door" and g.interact()
    assert door["open"] and door["colour"] not in g.keys
    assert L.can_stand(door["x"] + 0.5, door["y"] + 0.5, 0.24, L.floor[door["y"], door["x"]])


def test_the_levers_open_the_sealed_door():
    d, L = _floor_with(lambda L: bool(L.levers))
    door = next(x for x in L.doors if x["colour"] == "rune")
    reach = features.reach(L)
    assert all((lv["x"], lv["y"]) in reach for lv in L.levers) and len(L.levers) >= 2
    g = Game.new(seed=3)
    g._enter(L)
    for i, lv in enumerate(L.levers):
        assert not door["open"]
        g.x, g.z = lv["x"] + 0.5, lv["y"] + 0.5
        assert g.near()[0] == ("lever", i)
        g.interact()
    assert door["open"]


def test_the_brazier_trial():
    d, L = _floor_with(lambda L: bool(L.braziers))
    g = Game.new(seed=4)
    g._enter(L)
    chests = len(L.chests)
    # too slow: they go out
    g._light_brazier(L.braziers[0])
    assert L.trial["until"] and L.sprites[L.braziers[0]["sprite"]]["name"] == "brazier"
    g.time += 20
    g._trial()
    assert not any(b["lit"] for b in L.braziers) and len(L.chests) == chests
    # all of them in time: a chest
    for b in L.braziers:
        g._light_brazier(b)
    g._trial()
    assert L.trial["done"] and len(L.chests) == chests + 1
    # (and a bolt lights one)
    d2, L2 = _floor_with(lambda L: bool(L.braziers), seed="g")
    g2 = Game.new(seed=5)
    g2._enter(L2)
    g2.monsters = []
    b = L2.braziers[0]
    import math
    cx, cz = L2.trial["x"] + 0.5, L2.trial["y"] + 0.5                 # (shot from the room's middle)
    dx, dz = b["x"] - cx, b["z"] - cz
    n = math.hypot(dx, dz)
    g2.bolts = [Bolt(cx, b["y"] + 0.5, cz, dx / n * 8, 0, dz / n * 8, 10, "frost")]
    for _ in range(40):
        g2._bolts(0.03)
    assert b["lit"]


def test_every_floor_is_still_whole_with_its_doors():
    for depth in range(1, D.FLOORS + 1, 3):
        L = levels.dungeon(depth, "w")
        shut = features.reach(L)
        assert (int(L.stairs[0]), int(L.stairs[1])) in shut, depth
        for p in L.pickups:
            if p["kind"] == "key":
                assert (int(p["x"]), int(p["z"])) in shut, depth
