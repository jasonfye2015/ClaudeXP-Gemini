"""Her scenes: the letterbox and the dark; her set down before him, facing him; a camera that looks at her; nothing
small dropping onto him while she talks; and all of it undone after."""
import math

from hollowoak.game import night as N
from hollowoak.game.scene import CUT, IN, Scene


def _on_her_loom():
    n = N.Night(seed=11)
    t, lo = n.tree, n.web.loom
    s = next(s / 100 for s in range(1200) if abs(t.ledge_h(s / 100) - lo.h) < 0.03)
    a = t.theta_of(s)
    edge = t.base_r(a, lo.h + 0.5) - 1.6
    n.x, n.z = math.cos(a) * (edge - 0.3), math.sin(a) * (edge - 0.3)
    n.y = n.floor_at(n.x, n.z, lo.h + 0.2)
    n.yaw = math.atan2(-n.x, n.z)
    return n


def test_a_scene_from_start_to_end():
    n = _on_her_loom()
    sc = Scene(n, "audience")
    inp = N.Input()
    inp.yaw = n.yaw
    assert n.quiet and not sc.ready
    seen_dark, steps = 0.0, 0
    while not sc.ready:
        sc.step(0.05)
        n.step(0.05, inp)
        seen_dark = max(seen_dark, sc.dim)
        steps += 1
        inp.yaw = n.yaw
        assert steps < 100
    assert seen_dark > 0.95 and sc.box == 1.0 and sc.dim < 0.05            # (dark a moment; then the frame, held)
    her = n.her
    hx, hy, hz = her.at()
    assert her.staged is not None and 2.0 < math.hypot(hx - n.x, hz - n.z) < 3.2
    assert abs(hy - n.floor_at(hx, hz, n.y + 0.3)) < 1e-6                 # (on what he stands on: her loom)
    p, f, up, *_ = her.pose()
    to_him = (n.x - hx, n.z - hz)
    assert (f[0] * to_him[0] + f[2] * to_him[1]) / math.hypot(*to_him) > 0.99   # (facing him)
    (cx, cy, cz), yaw, pitch = sc.camera()
    look = (math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch))
    to = (hx - cx, hy + 0.7 - cy, hz - cz)
    d = math.sqrt(sum(c * c for c in to))
    assert sum(a * b for a, b in zip(look, to)) / d > 0.9                   # (the camera on her)
    n.crawlers.next = n.crawlers.t                                           # (nothing small onto him meanwhile)
    n.danglers.next = n.danglers.t
    for _ in range(int(20 / 0.05)):
        sc.step(0.05)
        n.step(0.05, inp)
    assert not n.crawlers.runs and not n.danglers.hanging
    assert sc.rider_poses() or sc.riders == [] and sc._next_rider > sc.t   # (her small ones, now and then, on her back)
    sc.end()
    while not sc.done:
        sc.step(0.05)
        n.step(0.05, inp)
    assert her.staged is None and not n.quiet and sc.box == 0.0 and sc.dim == 0.0
    assert sc.t < 20 + CUT * 4 + IN * 2 + 1
