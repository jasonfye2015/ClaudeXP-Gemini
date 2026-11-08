"""The Hollow Oak, walked: in through the roots, across the hollow, up the ledge to the crown - and never through a wall."""
import math

from hollowoak.game import night as N
from hollowoak.game import tree as T


def test_the_ledge_climbs_unbroken_to_the_crown():
    t = T.Tree()
    assert 24 < t.top_h < T.TOP and set(t.landing_h) == {"gallery", "larder", "high hollow", "crown"}
    prev = 0.0
    s = 0.0
    while s <= t.s_end:
        h = t.ledge_h(s)
        assert h is not None and h >= prev - 1e-9 and h - prev < T.STEP     # (never a step too high, never down)
        a = t.theta_of(s)
        mid = t.base_r(a, h + 0.5) - T.LEDGE_W / 2
        x, z = math.cos(a) * mid, math.sin(a) * mid
        if h > 0.5:
            assert abs(t.floor_at(x, z, h) - h) < 1e-6, (s, h)
            assert t.can_stand(x, z, h), (s, h)                              # (room for him all the way up)
        prev = h
        s += 0.05


def test_the_way_in():
    t = T.Tree()
    sx, sz, facing = t.start
    assert t.in_tunnel(sx, sz) and t.can_stand(sx, sz, t.floor_at(sx, sz, 1.0))
    for along in (0.5, 3.0, 6.0, T.TUNNEL_LEN - 0.6):                      # (the tunnel, its length)
        x, z = t.tunnel_point(along, 0.0)
        assert t.can_stand(x, z, t.floor_at(x, z, 1.0))
    x, z = t.tunnel_point(4.0, T.TUNNEL_HALF + 0.05)                          # (not through its sides)
    assert not t.can_stand(x, z, 0.1)
    x, z = t.tunnel_point(T.TUNNEL_LEN + 0.5, 0.0)                            # (nor out through the far end)
    assert not t.can_stand(x, z, 0.1)


def test_the_wall_holds():
    t = T.Tree()
    for k in range(72):
        a = k / 72 * math.tau
        for y in (0.3, 5.0, 12.0, 20.0, 27.0):
            r = t.wall_r(a, y)
            assert 4.0 < r < 11.0
            x, z = math.cos(a) * (r + 0.1), math.sin(a) * (r + 0.1)
            if not t.in_tunnel(x, z):
                assert not t.can_stand(x, z, y), (a, y)
    # the chambers: the wall opens out where a landing is
    for name, start, run in T.LANDINGS[:-1]:
        a = t.theta_of(start + run / 2)
        h = t.landing_h[name]
        assert t.wall_r(a, h + 1.3) > t.base_r(a, h + 1.3) + 1.5, name


def test_he_walks_in_and_up():
    n = N.Night(seed=1)
    inp = N.Input()
    inp.yaw = n.yaw
    inp.forward = 1.0
    for _ in range(int(14 / 0.05)):                                           # (in from the tunnel's end)
        n.step(0.05, inp)
    assert n.where() == "hollow" and "The roots" in [e[1] for e in n.events if e[0] == "place"]
    # up the ledge, following it round: aim along the spiral each step
    t = n.tree
    n.lamp.next_out = 1e9                                                    # (a steady light: this is about the climb)
    s = 0.25                                                                 # (the ledge's foot)
    a = t.theta_of(s)
    r = t.base_r(a, 0.5) - T.LEDGE_W / 2
    n.x, n.z = math.cos(a) * r, math.sin(a) * r
    n.y = t.floor_at(n.x, n.z, 0.0)
    best = 0.0
    for _ in range(int(400 / 0.05)):
        s_here = min((s for s in t.ledge_turns(math.atan2(n.z, n.x)) if abs(t.ledge_h(s) - n.y) < 0.6), default=None)
        if s_here is None:
            break
        ahead = t.theta_of(s_here + 0.25)
        h2 = t.ledge_h(min(t.s_end, s_here + 0.25))
        r = t.base_r(ahead, h2 + 0.5) - T.LEDGE_W / 2
        tx, tz = math.cos(ahead) * r, math.sin(ahead) * r
        inp.yaw = math.atan2(tx - n.x, -(tz - n.z))
        n.step(0.05, inp)
        best = max(best, n.y)
        if s_here > t.s_end - 0.4:
            break
    assert best > t.landing_h["crown"] - 0.2, best
    names = {e[1] for e in n.events if e[0] == "place"}
    assert {"The gallery", "The larder", "The high hollow", "The crown"} <= names, names


def test_the_clock_and_her_eyes():
    n = N.Night(seed=2)
    assert n.clock_words() == "7:00 pm"
    inp = N.Input()
    inp.yaw = n.yaw
    for _ in range(int(30 / 0.05)):
        n.step(0.05, inp)
    assert n.clock_words() == "7:02 pm"                                      # (the night is long: ~2.75 real hours)
    assert abs((N.DAWN - N.DUSK) / N.CLOCK_RATE / 3600 - 2.74) < 0.1
    assert n.eyes() and n.eye_alpha > 0.5                                     # (something up there, watching)
    px, py, pz = n.perches[n.perch]
    assert py > n.eye[1] + 1.5


def test_the_lantern_is_close_in_the_roots():
    """In the root tunnel his lantern throws its light only a little way; in the hollow it reaches out."""
    n = N.Night(seed=3)
    deep, k_deep = n.lantern_reach()                                          # (he starts deep in the roots)
    x, z = n.tree.tunnel_point(-0.5, 0.0)
    n.x, n.z = x, z
    open_, k_open = n.lantern_reach()
    assert deep < 2.0 and k_deep < 0.3 and open_ >= 5.9 and k_open == n.lamp.level == 1.0
