"""The forest round Thornwick: its glades, its trails, its creatures, and the town kept safe from them."""
import math

from claudenites.game import data as D
from claudenites.game import forest, levels
from claudenites.game.world import Game, Input, Monster

_walkable_reach = levels.walkable_reach


def test_the_wood_and_its_glades():
    for seed in (1, 2, 3):
        T = levels.town(seed)
        names = [p["name"] for p in T.pieces]
        assert names == [g[0] for g in forest.GLADES], names
        assert sum(1 for p in T.props if p.get("trunk")) > 1500
        reach = _walkable_reach(T)
        for p in T.pieces:                                     # (every glade can be walked to, trees and all)
            sq = [(x, y) for x in range(p["x0"], p["x1"] + 1) for y in range(p["y0"], p["y1"] + 1) if (x, y) in reach]
            assert sq, (seed, p["name"])
        for c in T.chests:
            assert any((int(c["x"]) + dx, int(c["z"]) + dy) in reach for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        for n in T.npcs:
            assert (int(n["x"]), int(n["z"])) in reach or any((int(n["x"]) + dx, int(n["z"]) + dy) in reach
                                                                for dx in (-1, 0, 1) for dy in (-1, 0, 1)), n
        assert {n["vendor"] for n in T.npcs} == set(D.VENDORS)
        for s in T.spawns:
            assert not T.safe[int(s["z"]), int(s["x"])], s
            assert s["monster"] in D.MONSTERS


def test_nothing_hunts_in_the_town():
    g = Game.new(seed=5)
    L = g.level
    p = g.player
    p.life = p.max_life()
    # stand just inside the clearing's edge, a wolf and a bandit wizard outside, awake and wanting him
    cx, cy = L.w // 2, L.h // 2
    for r in range(28, 10, -1):
        if L.safe[cy, cx + r] and L.can_stand(cx + r + 0.5, cy + 0.5, 0.24, 0.0):
            break
    g.x, g.z, g.y = cx + r + 0.5, cy + 0.5, 0.0
    g.monsters = []
    for name, d in (("Wolf", 4), ("Hedge Wizard", 7)):
        m = Monster(name, g.x + d, g.z, 1, __import__("random").Random(1))
        m.home = (m.x, m.z)
        m.awake = True
        g.monsters.append(m)
    inp = Input()
    for _ in range(60 * 20):
        g.step(1 / 60, inp)
        for m in g.monsters:
            assert not L.safe[int(m.z), int(m.x)], (m.name, m.x, m.z)
    assert p.life == p.max_life()                              # (no blow, no bolt cast at him in the town)
    inp.fire = True
    g.step(0.05, inp)
    assert not g.bolts                                         # (and he doesn't cast in the town either)


def test_a_deer_runs():
    g = Game.new(seed=6)
    L = g.level
    deer = next((m for m in g.monsters if m.name == "Deer"), None)
    assert deer is not None
    for (x, y) in L.open_squares():
        if 3 < math.hypot(x + 0.5 - deer.x, y + 0.5 - deer.z) < 5 and not L.safe[y, x] and L.can_stand(x + 0.5, y + 0.5, 0.24, 0):
            g.x, g.z = x + 0.5, y + 0.5
            break
    d0 = math.hypot(deer.x - g.x, deer.z - g.z)
    deer.awake = True
    for _ in range(90):
        g.step(1 / 60, Input())
    assert math.hypot(deer.x - g.x, deer.z - g.z) > d0 + 0.5
    assert g.player.life == g.player.max_life()


def test_falling_in_the_forest():
    g = Game.new(seed=7)
    g.run_floor = 9
    p = g.player
    for (x, y) in g.level.open_squares():
        if not g.level.safe[y, x]:
            g.x, g.z = x + 0.5, y + 0.5
            break
    p.life = 0
    g.step(0.02, Input())
    assert g.depth == 0 and g.in_town() and g.run_floor == 9 and p.stats["deaths"] == 0 and p.life == p.max_life()
