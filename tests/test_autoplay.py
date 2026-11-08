"""Led by her letter: a whole night walked for him, to Spellbound; waking from it; the first night's lessons."""
import math

from hollowoak.game import acts as A
from hollowoak.game import ending as E
from hollowoak.game import night as N
from hollowoak.game import tutorial as TU
from hollowoak.game.autoplay import Director, best_gift, choose_line


def _night(n, d, secs, scenes=True, on_event=None):
    """The night, the letter leading, its scenes played out as they come (her words aside)."""
    inp = N.Input()
    inp.yaw, inp.pitch = n.yaw, n.pitch
    seen = []
    for _ in range(int(secs / 0.05)):
        for r in d.step(0.05, n, inp):
            if r == ("dawn",):
                n.skip_to_dawn()
        n.step(0.05, inp)
        sc = n.acts.scene_for(n) if scenes and n.dying is None and n.ending is None else None
        if sc and sc not in n.met:
            n.met[sc] = "done"
            n.events.extend(n.acts.scene_over(sc, "guest" if sc == "supper" else "done", n))
        seen += n.events
        n.events.clear()
        if n.ending is not None or n.dying is not None:
            break
    return seen


def test_a_whole_night_spellbound():
    n = N.Night(seed=1)
    n.flags["led"] = True
    n.lamp.next_out = 1e9
    seen = _night(n, Director(n), 4000)
    assert n.dying is None and n.ending is not None and n.ending.name == "Spellbound"
    assert {"orrin", "aldric", "wick", "isolde", "maudren", "fennick"} <= n.cocoons.burst
    assert {"mark_roots", "mark_tally", "mark_crown"} <= n.spells.marks_seen
    assert ("take", "ring") in seen and ("take", "journal") in seen
    assert [e[1] for e in seen if e[0] == "act"][:4] == ["gallery", "supper", "crown", "dawn"]
    assert E.card("Spellbound") == "Ending 8 of 8: Spellbound"


def test_her_guests_counted_bring_supper_sooner():
    n = N.Night(seed=2)
    n.acts.found = 3                                                  # (three of her guests looked at)
    n.acts.act = "gallery"
    n.sky.clock = A.S.DUSK + 205
    assert ("act", "supper") in n.acts.step(0.05, n)


def test_woken_is_no_longer_spellbound():
    n = N.Night(seed=3)
    n.flags["led"] = True
    assert n.charmed() and A.Acts().decide(n) == "Spellbound"
    n.flags["woke"] = True
    assert not n.charmed() and A.Acts().decide(n) != "Spellbound"


def test_his_words_chosen_well():
    choices = [("You're beautiful.", ["flattery"], None), ("I came because you asked me to.", ["honest", "answer"], None),
               ("I'll stay.", ["honest"], "stay"), ("I'm a prince.", ["lie"], None)]
    assert choose_line(choices) == 1
    n = N.Night(seed=4)
    n.take("mouse")
    n.moods.hunger = 80
    assert best_gift(n) == "mouse"
    n.moods.hunger = 10
    assert best_gift(n) is None


def test_the_guide_reaches_every_lesson():
    for name in ("light_spot", "ring_spot", "loom_edge", "orrin_spot", "strand_end", "larder_door", "antidote_spot",
                 "crown_edge"):
        n = N.Night(seed=5)
        n.lamp.next_out = 1e9
        n.danglers.next = n.crawlers.next = 1e9
        d = Director(n, guide=True)
        task = TU.travel_task(name, n, d.nav)
        d.tasks = [task]
        arrived = False
        inp = N.Input()
        inp.yaw, inp.pitch = n.yaw, n.pitch
        for _ in range(int(500 / 0.05)):
            if ("done", "go") in d.step(0.05, n, inp):
                arrived = True
                break
            n.step(0.05, inp)
            n.events.clear()
        x, z = task["at"][-2], task["at"][-1]
        assert arrived and n.dying is None, name
        assert math.hypot(n.x - x, n.z - z) < 0.6 or task["at"][0] == "tunnel", name


def test_the_lessons_go_on():
    n = N.Night(seed=6)
    t = TU.Tutorial(n)
    assert t.lesson[0] == "walk"
    t.step(0.05, n, [], {})
    assert t.his_turn and t.note and t.prompt                         # (no travel: his turn at once)
    n.moved += 3.0
    for _ in range(40):
        t.step(0.05, n, [], {})
    assert t.lesson[0] == "lantern"
    t.step(0.05, n, [], {})
    assert n.lamp.state == "out"                                      # (it gutters, to be shaken)
    t.skip()
    assert t.lesson[0] == "light" and t.step(0.05, n, [], {}) == [("travel", "light_spot")]
    for _ in range(len(TU.LESSONS)):
        t.skip()
    assert t.done


def test_the_first_night_is_kept():
    n = N.Night(seed=7)
    n.flags["first"] = True
    n.body.health, n.body.poison = 10.0, 9.0
    inp = N.Input()
    for _ in range(40):
        n.step(0.05, inp)
    assert n.dying is None and n.body.health >= n.body.poison + 20
