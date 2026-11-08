"""Her moods: hidden, moved by how he goes and (later) what he says; steering her body - and, at the edge, her bite."""
import math

from hollowoak.game import night as N
from hollowoak.game.moods import Moods


def _ledge_night(seed=3):
    n = N.Night(seed=seed)
    t = n.tree
    s = 1.0 * math.tau
    a = t.theta_of(s)
    r = t.base_r(a, t.ledge_h(s) + 0.5) - 0.8
    n.x, n.z = math.cos(a) * r, math.sin(a) * r
    n.y = n.floor_at(n.x, n.z, t.ledge_h(s) + 0.1)
    n.danglers.next = n.crawlers.next = 1e9
    n.lamp.next_out = 1e9
    return n


def test_what_he_says_moves_her_and_too_much_doubt_turns_kindness_to_a_trick():
    m = Moods()
    m.heard("magic")
    m.heard("honest")
    assert m.fascination > 45 and m.regard > 0
    before = (m.fascination, m.regard)
    m.heard("lie")
    m.heard("lie")
    m.heard("lie")
    m.heard("promise_broken")
    assert m.suspicion > 75
    m.heard("gift")                                                           # (now it reads as a trick)
    assert (m.fascination, m.regard) <= before and m.suspicion > 80
    m.heard("food")
    assert m.hunger < 20


def test_a_calm_watcher_fascinates_her():
    n = _ledge_night()
    inp = N.Input()
    for _ in range(int(240 / 0.05)):
        hx, hy, hz = n.her.at()
        ex, ey, ez = n.eye
        inp.yaw = math.atan2(hx - ex, -(hz - ez))
        inp.pitch = math.atan2(hy - ey, math.hypot(hx - ex, hz - ez))
        n.step(0.05, inp)
        n.events.clear()
    m = n.moods
    assert m.fascination > 38 and m.patience > 70 and m.regard > 0.5 and m.hunger < 30 and not m.hunting


def test_a_careless_runner_is_prey():
    n = _ledge_night()
    inp = N.Input()
    inp.hurry, inp.forward = True, 1.0
    seen, k = [], 0
    while n.time < 12 * 60 and not any(e == ("her", "bite") for e in seen):
        k += 1
        inp.yaw += 0.03
        if k % 40 == 0:
            inp.jump = True
        if n.lamp.state == "out" and n.lamp.shaking == 0:
            n.lamp.shake()
        n.step(0.05, inp)
        seen += n.events
        n.events.clear()
    assert ("her", "hunts") in seen and ("her", "strike") in seen and ("her", "bite") in seen
    assert n.moods.bites == 1 and n.body.poison > 20 and n.dying is None   # (bitten once: venom - and still standing)


def test_a_second_bite_is_supper():
    n = _ledge_night()
    n.moods.bites = 1
    n.venom.start()                                                          # (her first bite still in him)
    her = n.her
    her.state, her.strike_t = "strike", her.t - 0.3                          # (mid-strike, and he's within reach)
    hx, hy, hz = n.eye
    her.th, her.y = math.atan2(hz, hx), hy
    for _ in range(10):
        n.step(0.05, N.Input())
        if n.dying is not None:
            break
    assert n.dying is not None and n.dying.cause == "bite"


def test_her_moods_show_in_the_den():
    m = Moods()
    calm = m.fungus_tint()
    m.hunger = 95
    warm = m.fungus_tint()
    m.hunger, m.suspicion = 20, 95
    cold = m.fungus_tint()
    assert warm[0] > calm[0] * 1.5 and warm[2] < calm[2]                      # (hungry: warmer, toward amber)
    assert sum(cold) < sum(calm) * 0.85                                       # (doubting: dimmer, colder)
    m.suspicion = 10
    m.hunger = 90
    assert m.hum_pitch() > 1.1
