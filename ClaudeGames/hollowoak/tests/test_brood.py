"""Her small ones: on the wall, the floor and her silk; still, then scurrying; bolting from him; always about him;
and the den's sound."""
import math

import numpy as np

from hollowoak.engine import silkmesh, sound
from hollowoak.game import night as N


def test_they_keep_to_their_surfaces():
    n = N.Night(seed=3)
    br = n.brood
    t = n.tree
    for _ in range(int(30 / 0.05)):
        n.step(0.05, N.Input())
    kinds = {sp["on"] for sp in br.spiders}
    assert {"wall", "floor"} <= kinds
    for sp in br.spiders:
        x, y, z = br.pos(sp)
        if sp["on"] == "wall":
            assert abs(math.hypot(x, z) - t.wall_r(math.atan2(z, x), y)) < 0.05
        elif sp["on"] == "floor":
            assert abs(y - t.ground(x, z)) < 0.01
        elif sp["on"] == "disc":
            d = n.web.discs[sp["p"][0]]
            assert math.hypot(x, z) < d.rim(math.atan2(z, x)) and abs(y - d.height(x, z, False)) < 0.02
        f, up = br.forward(sp), br.up(sp)
        assert abs(math.sqrt(sum(c * c for c in f)) - 1) < 1e-6 and abs(sum(a * b for a, b in zip(up, up)) - 1) < 1e-6


def test_they_go_in_fits_and_starts_and_bolt_from_him():
    n = N.Night(seed=4)
    br = n.brood
    states = set()
    for _ in range(int(20 / 0.05)):
        n.step(0.05, N.Input())
        states |= {sp["state"] for sp in br.spiders}
    assert {"rest", "go"} <= states
    sp = br.spiders[0]                                                   # (put one at his feet: off it goes)
    sp["on"], sp["p"], sp["state"], sp["until"] = "floor", (1.6, 0.5), "rest", 5.0
    n.x, n.z = 1.0, 0.5
    n.y = n.floor_at(n.x, n.z, 0.0)
    d0 = math.dist(br.pos(sp), n.eye)
    n.events.clear()
    n.step(0.05, N.Input())
    assert sp["state"] == "flee" and any(e[0] == "skitter" for e in n.events)
    for _ in range(20):
        n.step(0.05, N.Input())
    assert math.dist(br.pos(sp), n.eye) > d0 + 0.8


def test_they_keep_about_him():
    n = N.Night(seed=5)
    t = n.tree
    s = 3.7 * math.tau                                                   # (high up on the ledge)
    a = t.theta_of(s)
    r = t.base_r(a, t.ledge_h(s) + 0.5) - 0.6
    n.x, n.z = math.cos(a) * r, math.sin(a) * r
    n.y = n.floor_at(n.x, n.z, t.ledge_h(s) + 0.1)
    for _ in range(int(5 / 0.05)):
        n.step(0.05, N.Input())
    near = n.brood.near(n.eye)
    assert len(near) >= len(n.brood.spiders) * 0.7
    assert all(clip in ("walk", "idle") for *_x, clip, _t in near)


def test_the_spider_frames():
    v, clips, per = silkmesh.spider_frames()
    assert set(clips) == {"walk", "idle"} and v.shape[1] == 9
    assert v.shape[0] == per * sum(f for _a, f, _r in clips.values())
    first, frames, _fps = clips["walk"]
    a, b = v[first * per:(first + 1) * per], v[(first + frames // 2) * per:(first + frames // 2 + 1) * per]
    assert np.abs(a[:, :3] - b[:, :3]).max() > 0.02                     # (the legs move)
    assert -0.02 < a[:, 1].min() < 0.05 and 0.25 < np.ptp(a[:, 2]) < 1.2  # (feet down; about a unit long)
    assert np.allclose(np.linalg.norm(a[:, 3:6], axis=1), 1.0, atol=1e-3)


def test_the_den_sounds():
    s = sound.Synth()
    quiet = s.render(4410)
    assert quiet.dtype == np.float32 and np.isfinite(quiet).all() and np.abs(quiet).max() < 0.3
    s.set(hum=1.0, height=0.0)
    for _ in range(6):
        s.render(2205)
    hum = s.render(4410)
    assert np.sqrt(np.mean(hum ** 2)) > np.sqrt(np.mean(quiet ** 2)) * 1.5     # (the silk humming under him)
    for name in ("creak", "slip", "catch", "skitter", "rattle", "puff", "thud"):
        s.play(name)
    loud = np.concatenate([s.render(2205) for _ in range(10)])
    assert np.isfinite(loud).all() and np.abs(loud).max() <= 1.0 and not s.voices or len(s.voices) <= 12
