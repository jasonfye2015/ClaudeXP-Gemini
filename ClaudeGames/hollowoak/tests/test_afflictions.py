"""What the night does to him: the four, at their lines - what shows, what it changes, what it costs, and the switches."""
from hollowoak.game import afflictions as AF
from hollowoak.game import night as N
from hollowoak.game import offerings as O


def _quiet(n):
    n.lamp.next_out = 1e9
    n.danglers.next = n.crawlers.next = 1e9
    n.moods.hunger = 0.0
    n.her.at = lambda *a: (0.0, 40.0, 0.0)


def _run(n, secs, inp=None):
    inp = inp or N.Input()
    inp.yaw, inp.pitch = n.yaw, n.pitch
    seen = []
    for _ in range(int(secs / 0.05)):
        n.step(0.05, inp)
        seen += n.events
        n.events.clear()
    return seen


def test_the_lines_and_the_slack():
    n = N.Night(seed=1)
    _quiet(n)
    n.body.health = 49.0
    _run(n, 0.2)
    assert n.afflict.tier("health") == 2
    n.body.health = 52.0                                       # (a little back: still there - no flicker)
    _run(n, 0.2)
    assert n.afflict.tier("health") == 2
    n.body.health = 58.0
    _run(n, 0.2)
    assert n.afflict.tier("health") == 1


def test_sick_and_the_puddles():
    n = N.Night(seed=2)
    _quiet(n)
    n.body.poison = 40.0
    seen = _run(n, 3.0)
    assert ("afflict", "vomit") in seen and len(n.afflict.puddles) == 1     # (at once, the first time)
    assert n.body.poison < 40.0                                             # (it eases, a little)
    for _ in range(8):
        n.afflict.next_vomit = n.afflict.t
        n.body.poison = 80.0
        n.body.health = 100.0
        _run(n, 3.0)
    assert len(n.afflict.puddles) == AF.PUDDLES and n.afflict.coat > 0      # (five at most; the lantern green)
    c = n.afflict.coat
    n.shake()
    assert n.afflict.coat < c                                               # (a shake flings some off)


def test_on_his_hands_and_knees():
    n = N.Night(seed=3)
    _quiet(n)
    n.body.sanity = 45.0
    seen = _run(n, 3.0)
    assert ("afflict", "crawl") in seen and n.afflict.down
    assert n.afflict.pace < 0.6 and n.eye_h < N.EYE * 0.7
    n.body.sanity = 90.0
    _run(n, 3.0)
    assert not n.afflict.down and n.afflict.pace > 0.9


def test_his_eye():
    n = N.Night(seed=4)
    _quiet(n)
    for item in ("ring", "mouse", "moths", "honey"):
        n.take(item)
    n.body.sanity = 20.0
    seen = _run(n, AF.EYE_FOR + 1.0)
    assert ("afflict", "eye") in seen and ("afflict", "eye_taken") in seen
    assert n.afflict.eye_lost and "eye" in n.pack and len(n.pack) == 4 and n.held == "eye"
    n.moods.fascination = 70.0
    assert O.worth("eye", n)[0] == "delight"
    _run(n, 30.0)
    assert ("afflict", "eye") not in _run(n, 5.0)                          # (once a night)


def test_not_himself():
    n = N.Night(seed=5)
    _quiet(n)
    n.body.stupor = 80.0
    n.body.sanity = 100.0
    n.body.health = 100.0
    n.afflict.next_fall = 0.0
    inp = N.Input()
    inp.forward = 1.0
    x0 = (n.x, n.z)
    seen = _run(n, 1.0, inp)
    assert any(e in seen for e in (("afflict", "fall"), ("afflict", "lost")))
    assert n.afflict.busy
    assert abs(n.x - x0[0]) + abs(n.z - x0[1]) < 0.2                         # (nothing he tells himself gets through)


def test_the_switches():
    n = N.Night(seed=6)
    _quiet(n)
    n.afflict.opts["fx_control"] = False
    n.body.sanity = 45.0
    _run(n, 2.0)
    assert not n.afflict.down                                                # (no crawling, with that off)
    n.afflict.opts["fx_all"] = False
    n.body.health = 20.0
    _run(n, 2.0)
    assert n.afflict.tier("health") == 0 and n.afflict.bloodied == 0.0


def test_kept_from_the_worst():
    n = N.Night(seed=7)
    _quiet(n)
    n.flags["first"] = True
    n.body.sanity = 10.0
    seen = _run(n, AF.EYE_FOR + 1)
    assert ("afflict", "eye") not in seen and not n.afflict.eye_lost         # (the first night: never the worst)
    n = N.Night(seed=8)
    _quiet(n)
    n.flags["led"] = True
    n.body.health = 5.0
    _run(n, 0.5)
    assert n.body.health >= 30.0                                             # (led: above thirty)
