"""Her babies, close: dropping on a thread to the height of his face, and onto it when he walks into one; and all
over his lantern when it's out, letting go on threads of silk when it lights again."""
import math
import random

from hollowoak.game import night as N
from hollowoak.game.babies import CAP, FOOT, SWARM_MOST, Danglers, Swarm


def _in_hollow():
    n = N.Night(seed=12)
    n.x, n.z = 1.5, 1.0
    n.y = n.floor_at(1.5, 1.0, 0.0)
    return n


def test_one_drops_to_his_face_now_and_then():
    n = _in_hollow()
    n.danglers = Danglers(random.Random(3))
    drops = []
    for _ in range(int(200 / 0.05)):
        n.step(0.05, N.Input())
        drops += [n.time for e in n.events if e == ("dangler", "drop")]
        n.events.clear()
        for x, y, z, top, size, _ph in n.danglers.active():
            assert top > y and 0.12 <= size <= 0.18
    assert 4 <= len(drops) <= 9 and all(24.5 < b - a for a, b in zip(drops, drops[1:]))
    n.danglers.next = n.danglers.t
    n.step(0.05, N.Input())
    d = n.danglers.hanging[-1]
    for _ in range(int(4 / 0.05)):
        n.step(0.05, N.Input())
    ex, ey, ez = n.eye
    assert d["state"] == "hang" and abs(d["y"] - ey) < 0.12                # (stopped at the height of his face)
    assert 1.2 < math.hypot(d["x"] - ex, d["z"] - ez) < 2.9                # (a little way before him)


def test_walk_into_it_and_its_on_his_face():
    n = _in_hollow()
    n.danglers.next = 1e9
    n.crawlers.next = 1e9
    ex, ey, ez = n.eye
    look = (math.sin(n.yaw), -math.cos(n.yaw))
    n.danglers.hanging = [{"x": ex + look[0] * 1.2, "z": ez + look[1] * 1.2, "top": ey + 4, "y": ey, "stop": ey,
                           "state": "hang", "until": 99, "size": 0.15, "phase": 0.0}]
    inp = N.Input()
    inp.yaw, inp.forward = n.yaw, 1.0
    for _ in range(int(2 / 0.05)):
        n.step(0.05, inp)
        if not n.danglers.hanging:
            break
    assert not n.danglers.hanging and any(e == ("dangler", "face") for e in n.events)
    runs = n.crawlers.runs
    assert len(runs) == 1 and 0.3 < runs[0]["from"][0] < 0.7 and runs[0]["time"] <= 0.75     # (from his face, away)
    to = runs[0]["to"]
    assert min(to) < 0 or max(to) > 1


def test_in_the_dark_they_come_for_the_lantern():
    s = Swarm(random.Random(5))
    t, arrivals = 0.0, []
    while t < 150:
        for e in s.step(0.05, "out", []):
            if e == ("swarm", "up"):
                arrivals.append(t)
        t += 0.05
    assert 2.0 <= arrivals[0] <= 4.1
    assert all(9.9 < b - a < 20.1 for a, b in zip(arrivals, arrivals[1:]))
    assert SWARM_MOST[0] <= len(s.crawling()) == len(arrivals) <= SWARM_MOST[1]
    for b in s.crawling():
        assert b["state"] == "lantern" and FOOT <= b["h"] <= CAP
    # a shake that doesn't catch throws one or two off; one that lights it, all of them - each on a thread a while
    before = len(s.crawling())
    s.step(0.05, "out", ["failed"])
    assert before - 2 <= len(s.crawling()) <= before - 1
    s.step(0.05, "catching", ["relit"])
    assert not s.crawling() and all(b["state"] == "hang" for b in s.babies)
    states = []
    for _ in range(int(8 / 0.05)):
        s.step(0.05, "lit", [])
        states.append({b["state"] for b in s.babies})
    assert {"hang"} in states and any("fall" in x for x in states) and not s.babies
