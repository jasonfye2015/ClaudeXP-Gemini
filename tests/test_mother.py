"""Ysmeine on the wall: across the hollow and above, watching; now and then at the edge of his light, leaning out;
close in the dark; gone when he comes at her - and always on the wall."""
import math

from hollowoak.game import night as N
from hollowoak.game import tree as T
from hollowoak.game.mother import SIZE


def _night(seed=8):
    n = N.Night(seed=seed)
    n.x, n.z = 2.0, 1.0
    n.y = n.floor_at(2.0, 1.0, 0.0)
    n.danglers.next = n.crawlers.next = 1e9
    n.lamp.next_out = 1e9
    return n


def test_she_watches_from_across_the_hollow_and_comes_to_the_edge_of_the_light():
    n = _night()
    her, t = n.her, n.tree
    inp = N.Input()
    inp.yaw = n.yaw
    seen, glimpses, leaned = [], 0, 0.0
    for _ in range(int(200 / 0.05)):
        n.step(0.05, inp)
        glimpses += sum(1 for e in n.events if e == ("her", "glimpse"))
        n.events.clear()
        x, y, z = her.at()
        assert abs(math.hypot(x, z) - (t.base_r(her.th, her.y) - 0.25)) < 1e-6       # (on the wall)
        assert 1.9 <= her.y <= T.TOP - 2.4
        seen.append((her.state, math.dist(her.at(), n.eye)))
        leaned = max(leaned, her.lean)
    watching = [d for s, d in seen[1200:] if s == "watch"]
    assert watching and sum(watching) / len(watching) > 7.0                   # (mostly across the hollow)
    assert glimpses >= 2 and leaned > 0.9                                      # (and now and then, close, leaning out)
    assert min(d for _s, d in seen) < 5.5
    assert n.eyes() and abs(SIZE - 4.5) < 1e-9


def test_in_the_dark_she_comes_close_and_when_he_comes_at_her_she_goes():
    n = _night(9)
    her = n.her
    inp = N.Input()
    for _ in range(int(20 / 0.05)):
        n.step(0.05, inp)
    far = math.dist(her.at(), n.eye)
    n.lamp.state, n.lamp.level = "out", 0.02
    for _ in range(int(40 / 0.05)):
        n.step(0.05, inp)
        n.lamp.state, n.lamp.level = "out", 0.02
    assert her.state == "near" and math.dist(her.at(), n.eye) < min(far, 6.0)
    n.lamp.state, n.lamp.level = "lit", 1.0                                  # (light again)
    n.step(0.05, inp)
    assert her.state in ("watch", "withdraw")
    hx, hy, hz = her.at()                                                     # (he walks right up to her: she's off)
    n.x, n.z = hx * 0.75, hz * 0.75
    n.y = n.floor_at(n.x, n.z, 0.0)
    her.y = n.eye[1] + 0.5
    n.events.clear()
    for _ in range(int(4 / 0.05)):
        n.step(0.05, inp)
    assert ("her", "withdraw") in n.events and math.dist(her.at(), n.eye) > 4.0
