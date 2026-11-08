"""His satchel: four places, a hand to hold one thing, things that don't keep, things put down - and what he learns."""
import tempfile

from hollowoak.game import night as N
from hollowoak.game import offerings as O
from hollowoak.game import records as R
from hollowoak.game import satchel as S
from hollowoak.game import saving as SV


def _step(n, secs, dt=0.05):
    inp = N.Input()
    inp.yaw, inp.pitch = n.yaw, n.pitch
    seen = []
    for _ in range(int(secs / dt)):
        n.step(dt, inp)
        seen += n.events
        n.events.clear()
    return seen


def _calm(n):
    n.lamp.next_out = 1e9
    n.danglers.next = n.crawlers.next = 1e9
    n.moods.hunger = 0.0
    n.her.at = lambda *a: (0.0, 40.0, 0.0)


def test_four_places_and_a_hand():
    n = N.Night(seed=41)
    for item in ("ring", "mouse", "moths", "honey"):
        assert n.take(item)
    assert n.held == "ring"                                       # (an empty hand took the first)
    assert not n.take("journal") and ("satchel", "full") in n.events
    assert S.choose(n, 1) == "mouse" and S.choose(n, 1) == "moths"
    assert S.choose(n, -1) == "mouse"
    for _ in range(2):
        S.choose(n, 1)
    assert S.choose(n, 1) is None                                 # (an empty hand, between the last and the first)


def test_what_doesnt_keep():
    n = N.Night(seed=42)
    _calm(n)
    n.take("mouse")
    n.take("moths")
    n.take("honey")
    seen = _step(n, S.MOTH_EVERY + 1)
    assert ("satchel", "moth_out") in seen and n.items["moths"]["moths"] == S.MOTHS - 1
    seen = _step(n, S.MOUSE_LIFE - S.MOTH_EVERY)
    assert ("satchel", "honey") in seen and ("satchel", "mouse_still") in seen and n.items["mouse"]["still"]
    n.moods.hunger = 20
    assert O.worth("mouse", n)[0] == "insult"                     # (dead in his fist)
    seen = _step(n, S.MOTH_EVERY * S.MOTHS)
    assert ("satchel", "moths_gone") in seen and "moths" not in n.pack


def test_put_down_and_taken_again():
    n = N.Night(seed=43)
    n.take("ring")
    n.take("mouse")
    n.held = "ring"
    assert n.put_down() == "ring" and "ring" not in n.pack and "ring" in n.finds.dropped
    assert n.finds.where("ring", n) == n.finds.dropped["ring"]
    assert n.take("ring") and "ring" in n.pack and "ring" not in n.finds.dropped
    n.held = "mouse"
    assert n.put_down() == "mouse" and "mouse" not in n.finds.dropped     # (a live mouse: gone)
    assert not n.take("mouse")


def test_what_he_learns_is_kept():
    n = N.Night(seed=44)
    n.take("mouse")
    n.moods.hunger = 80
    tier, _line = O.give("mouse", n)
    assert tier == "delight" and n.learned and n.learned[0][0] == "mouse"
    assert "mouse" not in n.pack and n.held is None
    with tempfile.TemporaryDirectory() as tmp:
        rec = R.Records(tmp)
        assert rec.learn(*n.learned[0]) and not rec.learn(*n.learned[0])
        assert R.Records(tmp).learned["mouse"] == [n.learned[0][1]]


def test_the_satchel_is_saved():
    n = N.Night(seed=45)
    n.take("moths")
    n.take("ring")
    n.held = "ring"
    n.items["moths"]["moths"] = 3
    n.put_down()
    with tempfile.TemporaryDirectory() as tmp:
        saves = SV.Saves(tmp)
        saves.save("quick", n)
        m, _talk = saves.load("quick")
    assert m.pack == ["moths"] and m.items["moths"]["moths"] == 3 and m.held is None
    assert "ring" in m.finds.dropped and m.take("ring")
