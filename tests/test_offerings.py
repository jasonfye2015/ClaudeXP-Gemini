"""Offerings: found in her house, carried, given in her scenes - worth what her mood and the hour make them."""
import math

from hollowoak.game import dialogue as D
from hollowoak.game import night as N
from hollowoak.game import offerings as O
from hollowoak.game import sky as SK


def test_the_same_gift_early_and_late():
    n = N.Night(seed=1)
    n.moods.hunger = 40
    assert O.worth("moths", n)[0] == "delight"                               # (early: soft, dusty, like you)
    n.sky.clock = 1440 + 60                                                   # (past midnight)
    assert O.worth("moths", n)[0] == "plain"
    n.moods.hunger = 80
    assert O.worth("moths", n)[0] == "insult"                                # (starving: crumbs)
    assert O.worth("mouse", n)[0] == "delight"
    n.moods.hunger = 20
    assert O.worth("mouse", n)[0] == "insult"                                # (fed: I am not a cat)
    n.moods.regard = 10
    assert O.worth("ring", n)[0] == "insult"
    n.moods.regard = 40
    assert O.worth("ring", n)[0] == "delight"
    n.moods.fascination = 30
    assert O.worth("honey", n)[0] == "insult" and O.worth("string", n)[0] == "insult"
    n.moods.fascination = 70
    assert O.worth("honey", n)[0] == "delight" and O.worth("string", n)[0] == "delight"


def test_found_carried_given():
    n = N.Night(seed=2)
    f = n.finds
    for item, p in f.spots.items():                                          # (each where he can stand to reach it)
        assert math.isfinite(sum(p))
    x, y, z = f.where("honey", n)
    th = math.atan2(z, x)
    assert abs(math.hypot(x, z) - n.tree.wall_r(th, y)) < 0.3                 # (on the larder wall)
    rx, ry, rz = f.where("ring", n)                                           # (walk to the ring, look down at it)
    tx, tz = n.tree.tunnel_point(4.4, 0.0)
    n.x, n.z = tx, tz
    n.y = n.floor_at(tx, tz, 0.5)
    ex, ey, ez = n.eye
    n.yaw = math.atan2(rx - ex, -(rz - ez))
    n.pitch = math.atan2(ry - ey, math.hypot(rx - ex, rz - ez))
    assert f.near(n) == "ring"
    n.examine()
    assert n.pack == ["ring"] and ("take", "ring") in n.events and f.near(n) is None
    n.moods.regard = 40
    before = n.moods.fascination
    tier, said = O.give("ring", n)
    assert tier == "delight" and n.pack == [] and n.moods.fascination > before and "Silver" in said


def test_offered_in_a_scene():
    n = N.Night(seed=3)
    n.pack = ["mouse"]
    n.moods.hunger = 70
    talk = D.Conversation(n, None)
    out = []
    talk.open("supper", lambda t, ch: out.append((t, ch)))
    first = out[-1][1]
    talk.offer("mouse", lambda t, ch: out.append((t, ch)))
    text, choices = out[-1]
    assert "kicking" in text and choices == first and n.moods.hunger <= 50   # (she's eased; the talk goes on)
    n.sky.clock = SK.DUSK

    class Fake:
        def __init__(self):
            self.asked = []

        def speaking(self):
            return "fake"

        def ask(self, messages, done, max_tokens=160, temperature=0.9):
            self.asked.append(messages)
            done("Warm. Thank you.")
    fake = Fake()
    n.pack = ["moths"]
    talk = D.Conversation(n, fake)
    talk.open("audience", lambda t, ch: out.append((t, ch)))
    talk.offer("moths", lambda t, ch: out.append((t, ch)))
    assert out[-1] == ("Warm. Thank you.", []) and "moths" in fake.asked[-1][-1]["content"]
    assert "delights you" in fake.asked[-1][-1]["content"]
