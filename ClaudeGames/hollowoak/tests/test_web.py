"""Her silk: the strands across the hollow, her loom, the crown web - walked on, swayed on, slipped from, fallen into -
and what she feels of it all through the silk."""
import math

import numpy as np

from hollowoak.game import night as N
from hollowoak.game import tree as T
from hollowoak.game import web as W


def _onto(n, b, u=0.0):
    """Stand him on the ledge just short of strand b's end, facing along it."""
    n.x, n.z = b.a[0] - b.dir[0] * 0.3, b.a[2] - b.dir[1] * 0.3
    n.y = n.floor_at(n.x, n.z, b.a[1] + 0.1)
    inp = N.Input()
    inp.yaw = math.atan2(b.dir[0], -b.dir[1])
    inp.forward = 1.0
    return inp


def test_the_strands_run_from_ledge_to_ledge():
    t = T.Tree()
    w = W.Web(t)
    assert len(w.bridges) == 3
    for b in w.bridges:
        for end in (b.a, b.b):                                           # (each end at the ledge's edge, at its height)
            th = math.atan2(end[2], end[0])
            assert abs(math.hypot(end[0], end[2]) - (t.base_r(th, end[1] + 0.5) - T.LEDGE_W)) < 0.05
            assert min(abs(t.ledge_h(s) - end[1]) for s in t.ledge_turns(th)) < 0.05
        assert b.b[1] > b.a[1] + 1.0 and 7.0 < b.length < 13.0         # (up, and across)
        mid = b.point(0.5)
        assert b.height(0.5) < (b.a[1] + b.b[1]) / 2 - 0.2              # (sagging)
        h, piece = w.floor_at(mid[0], mid[2], mid[1] + 0.2)
        assert piece is b and abs(h - b.height(0.5)) < 1e-9
        assert w.floor_at(*b.point(0.5, W.BRIDGE_HALF + 0.1)[::2], mid[1] + 0.2) is None or \
            w.floor_at(*b.point(0.5, W.BRIDGE_HALF + 0.1)[::2], mid[1] + 0.2)[1] is not b    # (narrow)


def test_her_loom_meets_the_ledge_and_catches_what_falls():
    t = T.Tree()
    w = W.Web(t)
    lo = w.loom
    assert lo.height(0, 0) < lo.h - lo.sag + 1e-9                        # (sagging to its hub)
    s = next(s / 100 for s in range(1200) if abs(t.ledge_h(s / 100) - lo.h) < 0.03)   # (where the ledge passes it)
    th = t.theta_of(s)
    edge = t.base_r(th, lo.h + 0.5) - T.LEDGE_W
    x, z = math.cos(th) * (edge - 0.1), math.sin(th) * (edge - 0.1)
    assert abs(w.floor_at(x, z, lo.h)[0] - t.ledge_h(s)) < 0.15          # (step off the ledge onto it)
    n = N.Night(seed=2)                                                  # (dropped from above, he lands on it)
    n.x, n.z, n.y = 1.0, 0.5, 9.0
    for _ in range(40):
        n.step(0.05, N.Input())
    assert n.on is n.web.loom and abs(n.y - lo.height(1.0, 0.5)) < 1e-6
    assert n.silk["falls"] == 1 and any(e[:2] == ("silk", "caught") for e in n.events)
    assert n.tremor > 1.5                                                # (still shaking, a second on)


def test_walking_a_strand_gently():
    for seed in range(6):
        n = N.Night(seed=seed)
        b = n.web.bridges[seed % 3]
        inp = _onto(n, b)
        for _ in range(int(20 / 0.05)):
            n.step(0.05, inp)
            if b.locate(n.x, n.z)[0] > 1.05:
                break
        assert b.locate(n.x, n.z)[0] > 1.0 and n.silk["slips"] == 0, seed      # (across: never off)
        assert abs(n.y - n.tree.floor_at(n.x, n.z, n.y)) < 0.05             # (and onto the ledge on the far side)
        assert n.silk["gentle"] > b.length * 0.8 and n.silk["hurried"] == 0
        assert n.manner() > 0.99
        assert sum(1 for e in n.events if e[:2] == ("silk", "step")) >= b.length / N.STEP_SILK - 2


def test_hurrying_a_strand_and_leaning_against_the_sway():
    slips = steadied = 0
    for seed in range(20):
        for steer in (False, True):
            n = N.Night(seed=100 + seed)
            b = n.web.bridges[seed % 3]
            inp = _onto(n, b)
            inp.hurry = True
            for _ in range(int(12 / 0.05)):
                if steer:
                    inp.strafe = max(-1.0, min(1.0, -n.sway * 2.5 - n.sway_v * 0.8))
                n.step(0.05, inp)
                if n.silk["slips"] or b.locate(n.x, n.z)[0] > 1.05:
                    break
            if steer:
                steadied += n.silk["slips"] == 0
            else:
                slips += n.silk["slips"]
            if n.silk["slips"]:                                          # (off the side: falling, and she felt it)
                assert n.on is None and n.tremor > 3 and n.manner() < 0
                y0 = n.y
                for _ in range(40):
                    n.step(0.05, N.Input())
                assert n.y < y0 - 0.5
    assert slips >= 4 and steadied >= 18, (slips, steadied)          # (leaning saves him - nearly always)


def test_the_silk_threads_for_drawing():
    w = W.Web(T.Tree())
    strands = w.strands()
    assert len(strands) > 500
    groups = {g for _p, _w, g, _f, _ph in strands}
    assert groups <= set(range(W.GROUPS)) and {0, 1, 2, 3, 4} <= groups
    for pts, width, g, free, _ph in strands:
        assert len(pts) == len(free) and 0.001 < width < 0.03
        assert all(0.0 <= f <= 1.0 for f in free)
    # the cables of a strand lie where it can be walked; the loom's threads on the loom
    b = w.bridges[1]
    cable = next(np.array(p) for p, _w, g, _f, _ph in strands if g == 1 and len(p) == 40)
    for x, y, z in cable[5:-5]:
        u, across = b.locate(x, z)
        assert abs(y - b.height(u, weighted=False)) < 1e-6 and abs(across) <= W.BRIDGE_HALF


def test_she_feels_it():
    """Gentle steps read as respect; scrambling as prey - and when the silk shakes hard, her eyes come sooner."""
    n = N.Night(seed=9)
    n.silk.update(gentle=10.0)
    assert n.manner() == 1.0
    n.silk.update(hurried=3.0, slips=2)
    assert -1.0 < n.manner() < 0.0
    n.eye_gone_until = n.time + 30
    n.tremor = 5.0
    n.step(0.05, N.Input())
    assert n.eye_gone_until < n.time + 2
