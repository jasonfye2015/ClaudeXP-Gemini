"""Her guests: seven, wrapped - four on the hollow's floor - each in reach of a walker, and bursting when looked at."""
import math

from hollowoak.engine import cocoonmesh
from hollowoak.game import night as N
from hollowoak.game import notes
from hollowoak.game import tree as T


def test_where_they_hang():
    n = N.Night(seed=4)
    spots = n.cocoons.spots
    assert sorted(s["id"] for s in spots) == sorted(notes.SUITORS)
    floor = [s for s in spots if s["floor"] < 1.0]
    assert len(floor) == 4
    for s in spots:
        x, y, z = s["pos"]
        th = math.atan2(z, x)
        assert math.hypot(x, z) < n.tree.wall_r(th, y)                         # (inside the hollow, against its wall)
        assert y > s["floor"] and s["top"][1] > y                             # (above what's under it; hung from higher)
        for a, h, _size in T.FUNGI:                                           # (not in the fungus's light)
            if abs(h - y) < 1.5:
                assert abs((th - a + math.pi) % math.tau - math.pi) > 0.35, (s["id"], a)
    tris, threads = cocoonmesh.build(n.cocoons)
    assert tris.shape[1] == 9 and len(tris) % 3 == 0 and len(threads) == 3 * len(spots)


def test_look_closer_and_they_pour_out():
    n = N.Night(seed=5)
    s = n.cocoons.spots[0]
    x, y, z = s["pos"]
    a = s["angle"]
    n.x, n.z = x - math.cos(a) * 1.2, z - math.sin(a) * 1.2
    n.y = n.floor_at(n.x, n.z, s["floor"] + 0.2)
    ex, ey, ez = n.eye
    n.yaw = math.atan2(x - ex, -(z - ez))
    n.pitch = math.atan2(y - ey, math.hypot(x - ex, z - ez))
    assert n.cocoons.near(n) is s
    before = n.moods.suspicion
    n.examine()
    assert ("cocoon", s["id"], s["pos"], True) in n.events
    assert len(n.brood.pouring) == 34 and len(n.crawlers.runs) == 2 and n.moods.suspicion > before
    n.events.clear()
    n.examine()                                                               # (again: nothing more in him)
    assert n.events == [("cocoon", s["id"], s["pos"], False)]
    for _ in range(int(5 / 0.05)):
        n.brood.step(0.05, n.eye)
    assert not n.brood.pouring                                                # (and they're gone, after a while)
    n.yaw += math.pi                                                          # (looking away: nothing to look closer at)
    assert n.cocoons.near(n) is None
