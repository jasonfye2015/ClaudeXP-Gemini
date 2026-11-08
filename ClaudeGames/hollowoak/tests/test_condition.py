"""How he holds up - health with poison rising under it, sanity with stupor rising under it - and the end of him when
the green reaches the other."""
import random

from hollowoak.game import night as N
from hollowoak.game.condition import Condition
from hollowoak.game.death import DRAG_END, FADE_END, LIFT_END


def _night():
    n = N.Night(seed=21)
    n.x, n.z = 2.5, 1.0
    n.y = n.floor_at(2.5, 1.0, 0.0)
    n.danglers.next = n.crawlers.next = 1e9
    return n


def test_steady_light_keeps_him_whole():
    n = _night()
    n.lamp.next_out = 1e9
    for _ in range(int(120 / 0.05)):
        n.step(0.05, N.Input())
    v = n.body.values()
    assert v["health"] == 100 and v["poison"] == 0 and v["stupor"] == 0 and v["sanity"] > 90
    assert not n.body.critical() and n.dying is None


def test_the_dark_and_the_poison_wear_at_him():
    n = _night()
    b = n.body
    n.lamp.next_out = 0.0                                                     # (out, and never shaken)
    for _ in range(int(30 / 0.05)):
        n.step(0.05, N.Input())
    assert 60 < b.sanity < 95
    c = Condition(random.Random(1))                                            # (bitten: it eats at health, then him)
    c.poison = 90.0
    m = _night()
    m.lamp.next_out = 1e9
    for _ in range(int(20 / 0.05)):
        c.step(0.05, m, [])
    assert c.health < 95 and c.stupor > 5 and "poison" in c.critical()
    hurt = Condition(random.Random(2))                                         # (a long fall onto the wood)
    hurt.step(0.05, m, [("fall", 18.0)])
    assert hurt.health < 40 and hurt.stupor > 30 and not hurt.critical()     # (hurt, dazed: not yet in danger)


def test_when_it_gives_out_supper():
    n = _night()
    n.lamp.next_out = 1e9
    n.body.sanity = 0.0
    n.step(0.05, N.Input())
    assert n.dying is not None and n.dying.cause == "sanity" and ("collapse", "sanity") in n.events
    seen = {}
    while not n.dying.done:
        n.step(0.05, N.Input())
        t = n.dying.t
        if abs(t - 3.0) < 0.03:
            seen["down"] = (n.eye[1] - n.y, n.lantern, len(n.dying.spiders), len(n.dying.webs))
        if abs(t - (DRAG_END - 0.1)) < 0.03:
            seen["dragged"] = (n.x, n.z)
        if abs(t - (LIFT_END - 0.1)) < 0.03:
            seen["hung"] = (n.y, n.roll, n.eye[1] - n.y)
    eye, lit, spiders, webs = seen["down"]
    assert eye < 0.2 and not lit and spiders > 10 and webs > 5                 # (down; the lantern broken; them on him)
    assert len(n.dying.spiders) >= 40 and len(n.dying.webs) >= 60             # (his eyes mostly silk)
    assert abs(seen["dragged"][0]) < 0.3 and abs(seen["dragged"][1]) < 0.3   # (to the middle of the floor)
    y, roll, eye = seen["hung"]
    assert y > 12 and abs(roll - 3.14159) < 0.05 and eye < 0                   # (upside down, half way up the trunk)
    assert n.dying.black == 1.0 and n.dying.t >= FADE_END and ("lantern", "break") in n.events


def test_the_green_reaching_the_other_is_the_end():
    m = _night()
    for life, rising, lv, rv, gone in (("health", "poison", 50, 49, None), ("health", "poison", 50, 50, "poison"),
                                       ("health", "poison", 25, 25, "poison"), ("sanity", "stupor", 40, 41, "stupor"),
                                       ("sanity", "stupor", 0, 0, "sanity"), ("health", "poison", 60, 30, None)):
        c = Condition(random.Random(3))
        setattr(c, life, lv)
        setattr(c, rising, rv)
        assert c.spent() == gone, (life, lv, rising, rv)
    c = Condition(random.Random(4))
    c.health, c.poison = 50, 36                                                 # (close: the edge beats green)
    assert c.critical() == ["poison"]
    c.health, c.poison = 15, 0                                                  # (low, nothing rising: red)
    assert c.critical() == ["health"]
    m.body.health, m.body.poison = 50.0, 49.9
    m.body.poison += 1.0
    m.step(0.05, N.Input())
    assert m.dying is not None and m.dying.cause == "poison"
