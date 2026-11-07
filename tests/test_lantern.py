"""Claude's lantern: it flickers, it sputters, it goes out - and a shake (usually) brings it back."""
import random

from hollowoak.game import night as N
from hollowoak.game.lantern import EMBER, FIRST_OUT, Lantern


def test_it_flickers_and_goes_out():
    lamp = Lantern(random.Random(1))
    seen, levels = [], []
    t = 0.0
    while t < FIRST_OUT[1] + 3:
        seen += lamp.step(0.05)
        levels.append(lamp.level)
        t += 0.05
    assert "sputter" in seen and "dying" in seen and "out" in seen
    assert lamp.state == "out" and lamp.level <= EMBER
    lit = levels[: int(FIRST_OUT[0] / 0.05)]
    assert max(lit) <= 1.0 and min(lit) < 0.5 and max(lit) - min(lit) > 0.3      # (never steady)


def test_a_shake_brings_it_back_usually():
    back = failed = 0
    for seed in range(40):
        lamp = Lantern(random.Random(seed))
        lamp.state = "out"
        lamp.shake()
        assert not lamp.shake()                                  # (one shake at a time)
        got = []
        for _ in range(int(2.5 / 0.05)):
            got += lamp.step(0.05)
        if "relit" in got:
            back += 1
            assert lamp.state == "lit" and lamp.level > 0.4
        else:
            failed += 1
            assert "failed" in got and lamp.state == "out"
    assert back > failed > 0


def test_the_light_follows_the_lamp():
    n = N.Night(seed=5)
    inp = N.Input()
    inp.yaw = n.yaw
    reach_lit, k_lit = n.lantern_reach()
    n.lamp.state, n.lamp.level = "out", EMBER
    reach_out, k_out = n.lantern_reach()
    assert reach_out < reach_lit * 0.5 and k_out < 0.05
    n.lamp.shake()
    for _ in range(40):
        n.step(0.05, inp)
    assert any(e == ("lantern", "shake") for e in n.events)
