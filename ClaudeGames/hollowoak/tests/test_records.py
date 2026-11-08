"""What's kept between nights (in a scratch folder - never the real one), and his heart."""
import random
import tempfile

from hollowoak.game import night as N
from hollowoak.game.condition import Condition
from hollowoak.game.records import OPTIONS, Records


def test_the_records_keep():
    with tempfile.TemporaryDirectory() as d:
        r = Records(d)
        assert r.found == {} and r.options == OPTIONS and r.totals["nights"] == 0
        assert r.ending("Supper") is True and r.ending("Supper") is False      # (the first time, and not again)
        r.night_over({"seconds": 600.4, "bites": 3, "slips": 1})
        r.night_over({"seconds": 120, "swipes": 2})
        r.options["volume"] = 35
        r.save()
        again = Records(d)
        assert list(again.found) == ["Supper"] and again.totals["endings"] == 2
        assert again.totals["nights"] == 2 and again.totals["seconds"] == 720 and again.totals["longest"] == 600
        assert again.totals["bites"] == 3 and again.totals["swipes"] == 2 and again.options["volume"] == 35
        (again.path).write_text("{ not json", encoding="utf-8")                # (spoiled: starts over, quietly)
        assert Records(d).found == {}


def test_his_heart():
    n = N.Night(seed=30)
    n.lamp.next_out = 1e9
    n.danglers.next = n.crawlers.next = 1e9
    for _ in range(int(30 / 0.05)):
        n.step(0.05, N.Input())
    b = n.body
    assert 60 < b.bpm < 75 and 9 <= len(b.beats) <= 14                        # (resting: about 66; ten seconds kept)
    assert 59 <= len(b.history) <= 60 and all(t > b.t - 10.01 for t in b.beats)
    rest = b.bpm
    n.events.append(("dangler", "face"))                                      # (one on his face: it leaps)
    b.step(0.05, n, [("dangler", "face"), ("crawler", 1)])
    for _ in range(int(3 / 0.05)):
        b.step(0.05, n, [])
    assert b.bpm > rest + 20
    for _ in range(int(60 / 0.05)):
        b.step(0.05, n, [])
    assert b.bpm < rest + 8                                                    # (and settles)
    c = Condition(random.Random(1))                                            # (at the end: racing, slowing, still)
    rates = {}
    t = 0.0
    while t < 24.4:
        c.dying_heart(0.05, t)
        t += 0.05
        for mark in (4.0, 18.0, 23.9):
            if abs(t - mark) < 0.026:
                rates[mark] = c.bpm
    assert rates[4.0] > 130 and 20 < rates[18.0] < 110 and rates[23.9] < 1.0
