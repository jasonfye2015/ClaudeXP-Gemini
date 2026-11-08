"""Her, between her scenes: across the wall above, legs at the edge of the light, behind him when he turns."""
import math

from hollowoak.game import night as N
from hollowoak.game import sightings as SG


def _night(seed):
    n = N.Night(seed=seed)
    n.lamp.next_out = 1e9
    n.danglers.next = n.crawlers.next = 1e9
    n.moods.hunger = 0.0
    a = 2.0
    r = n.tree.base_r(a, 0.6) - 2.6                                  # (near the wall, on the floor)
    n.x, n.z = math.cos(a) * r, math.sin(a) * r
    n.y = n.tree.floor_at(n.x, n.z, 1.0)
    n.sightings.t = 100.0
    return n


def _run(n, secs, inp=None):
    inp = inp or N.Input()
    seen = []
    for _ in range(int(secs / 0.05)):
        inp.yaw = getattr(inp, "yaw", n.yaw)
        n.step(0.05, inp)
        seen += n.events
        n.events.clear()
    return seen


def test_across_the_wall_above():
    n = _night(1)
    n.her.state = "watch"
    n.sightings.next = 0.0
    n.sightings.rng.choice = lambda xs: "cross" if "cross" in xs else xs[0]
    seen = _run(n, 0.2)
    assert ("sight", "cross") in seen and n.her.state == "cross"
    th0 = n.her.th
    _run(n, 1.0)
    assert abs(n.her.th - th0) > 0.05 and n.her.y > n.eye[1]          # (going, fast, above him)
    _run(n, 8.0)
    assert n.her.state in ("withdraw", "watch")


def test_behind_him():
    n = _night(2)
    n.sightings.rng.random = lambda: 0.0
    inp = N.Input()
    inp.yaw = n.yaw
    _run(n, 0.2, inp)
    seen = []
    for k in range(12):                                              # (he turns round, fast)
        inp.yaw += 0.3
        n.step(0.05, inp)
        seen += n.events
        n.events.clear()
    assert ("sight", "behind") in seen and n.her.staged is not None
    _run(n, SG.BEHIND_FOR + 0.2, inp)
    assert n.her.staged is None                                      # (and then she isn't)


def test_her_web_thrums_as_she_goes():
    n = _night(3)
    n.her.th = math.atan2(n.z, n.x) + 0.4
    n.her.y = n.eye[1] + 2.0
    n.her.moving = 1.0
    n.sightings.step(0.5, n)
    assert n.sightings.thrum > 0.2


def test_never_in_her_scenes():
    n = _night(4)
    n.quiet = True
    n.sightings.next = 0.0
    seen = _run(n, 1.0)
    assert not any(e[0] == "sight" for e in seen)
