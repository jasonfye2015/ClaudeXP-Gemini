"""Saving the night: what's kept, where it goes, when it can't be made - always in a scratch folder."""
import json
import tempfile

from hollowoak.game import dialogue as D
from hollowoak.game import night as N
from hollowoak.game import records as R
from hollowoak.game import saving as S


def _lived_in():
    n = N.Night(seed=11)
    n.x, n.z = 1.0, 0.5
    n.y = n.tree.floor_at(1.0, 0.5, 1.0)
    n.sky.clock += 200
    n.moods.regard, n.moods.hunger, n.moods.bites = 61.0, 33.0, 1
    n.body.health, n.body.poison = 77.0, 31.0
    n.acts.act, n.acts.outcomes = "gallery", {"audience": "done"}
    n.pack, n.taken, n.given = ["ring"], {"ring", "moths"}, [("moths", "delight")]
    n.cocoons.burst.add("orrin")
    n.cocoons.burst_at["orrin"] = 12.5
    n.flags["smouldered"] = 1
    n.met = {"audience": "done"}
    n.venom.start()
    n.venom.seen.append("larder")
    n.spells.shown.add("hands")
    n.seen.add("hollow")
    talk = D.Conversation(n, None)
    talk.memory = ["He said he came because you asked."]
    talk.lies = 1
    return n, talk


def test_kept_and_given_back():
    n, talk = _lived_in()
    with tempfile.TemporaryDirectory() as tmp:
        saves = S.Saves(tmp)
        assert saves.list() == [] and saves.load("act") is None
        assert saves.save("act", n, talk)
        json.loads(open(f"{tmp}/night_act.json", encoding="utf-8").read())          # (plain JSON)
        (kind, label), = saves.list()
        assert kind == "act" and "Her guests" in label
        m, said = saves.load("act")
    assert (m.x, m.y, m.z) == (n.x, n.y, n.z) and m.sky.clock == n.sky.clock and m.sky.weather == n.sky.weather
    assert m.moods.regard == 61.0 and m.moods.bites == 1 and m.body.poison == 31.0
    assert m.acts.act == "gallery" and m.acts.outcomes == {"audience": "done"} and m.met == {"audience": "done"}
    assert m.pack == ["ring"] and m.taken == {"ring", "moths"} and m.given == [("moths", "delight")]
    assert m.cocoons.burst == {"orrin"} and m.flags["smouldered"] == 1
    assert m.venom.active and m.venom.revealed and m.spells.unshown() == ["candle", "thrown"]
    assert "hollow" in m.seen and isinstance(m.sky.target, tuple)
    assert said == {"memory": ["He said he came because you asked."], "lies": 1}
    inp = N.Input()                                                  # (and it goes on, as a night)
    inp.yaw, inp.pitch = m.yaw, m.pitch
    for _ in range(60):
        m.step(0.05, inp)
    assert m.dying is None and abs(m.y - n.y) < 0.05


def test_two_kinds_and_a_new_night_clears_them():
    n, talk = _lived_in()
    with tempfile.TemporaryDirectory() as tmp:
        saves = S.Saves(tmp)
        saves.save("act", n, talk)
        n.sky.clock += 30
        saves.save("quick", n, talk)
        assert {k for k, _l in saves.list()} == {"act", "quick"}
        assert saves.load("quick")[0].sky.clock == n.sky.clock
        open(f"{tmp}/night_act.json", "w").write("{ not json")
        assert saves.load("act") is None and [k for k, _l in saves.list()] == ["quick"]
        saves.clear()
        assert saves.list() == []


def test_when_it_cant_be_made():
    n = N.Night(seed=12)
    assert S.why_not(n) is None
    assert S.why_not(n, scene=True)                                  # (not while she's talking)
    n.vy = -2.0
    assert S.why_not(n)
    n.vy = 0.0
    n.venom.start()
    n.venom.vision = ("larder", 1.0)
    assert S.why_not(n)
    n.venom.vision = None
    n.her.state = "hunt"
    assert S.why_not(n)


def test_a_night_gone_on_with_is_not_another_night():
    with tempfile.TemporaryDirectory() as tmp:
        rec = R.Records(tmp)
        rec.night_over({"seconds": 100})
        rec.night_over({"seconds": 50, "resumed": True})
        assert rec.totals["nights"] == 1 and rec.totals["seconds"] == 150 and rec.reputation["met"] == 1
