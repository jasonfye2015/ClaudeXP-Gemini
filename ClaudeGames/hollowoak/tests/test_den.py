"""The den's dressing: water dripping into puddles, vines down the wall, roots across the floor, fallen leaves, and the
small eyes in the dark near the ground that are gone when he comes close."""
import math

from hollowoak.game import night as N
from hollowoak.game import tree as T
from hollowoak.game.den import Den


def test_water_drips_from_above_onto_something():
    t = T.Tree()
    d = Den(t)
    assert len(d.drips) >= 10
    for x, top, z, bottom in d.drips:
        assert top - bottom > 1.0                                        # (a real fall)
        assert abs(t.floor_at(x, z, top - 0.5) - bottom) < 1e-6          # (onto the floor or a lower turn of the ledge)


def test_vines_hang_on_the_wall_and_roots_lie_on_the_floor():
    t = T.Tree()
    d = Den(t)
    assert len(d.vines) > 40 and len(d.roots) > 20
    for line in d.vines:
        assert line[0][1] > line[-1][1]                                   # (hanging down)
        for x, y, z in line:
            assert abs(math.hypot(x, z) - (t.wall_r(math.atan2(z, x), y) - 0.06)) < 0.05
    for line in d.roots:
        for x, y, z, rad in line:
            assert y < t.ground(x, z) + rad and rad < T.STEP            # (half buried; low enough to step over)
            assert math.hypot(x, z) < t.base_r(math.atan2(z, x), 0.0)


def test_leaves_lie_where_they_fell():
    t = T.Tree()
    d = Den(t)
    assert len(d.leaves) > 3000
    for x, y, z, size, turn, shade in d.leaves[::7]:                     # (on the floor, the ledge, the tunnel's floor)
        tun = t.in_tunnel(x, z)
        under = [t.ground(x, z)] + [t.ledge_h(s) for s in t.ledge_turns(math.atan2(z, x))] +             ([t.tunnel_floor(tun[0])] if tun else [])
        assert min(abs(y - 0.012 - h) for h in under if h is not None) < 1e-6, (x, y, z)


def test_the_small_eyes_in_the_dark():
    n = N.Night(seed=4)
    inp = N.Input()
    inp.yaw = n.yaw
    n.x, n.z = 0.0, 0.0
    n.y = n.tree.ground(0.0, 0.0)
    for _ in range(int(14 / 0.05)):
        n.step(0.05, inp)
    seen = n.lurking()
    assert seen and all(p[1] - n.tree.floor_at(p[0], p[2], p[1]) < 0.45 for p, _a, _k, _s in seen)   # (low: just off the floor)
    # walk him right up to one: it's gone, and turns up again somewhere else
    l = next(l for l in n.lurkers if l["alpha"] > 0.5)
    spot = l["spot"]
    x, y, z = n.den.lurks[spot]
    n.x, n.z = x * 0.93, z * 0.93
    n.y = n.tree.floor_at(n.x, n.z, y + 0.2)
    for _ in range(int(3 / 0.05)):
        n._lurk(0.05)
    assert l["spot"] != spot and l["alpha"] == 0.0 and l["hidden_until"] > n.time
    assert any(e[0] == "scatter" for e in n.events)
