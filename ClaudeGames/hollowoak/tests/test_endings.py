"""The rest of the endings (4f): Fire, The hidden - and each ending's own scene."""
from hollowoak.game import acts as A
from hollowoak.game import dialogue as D
from hollowoak.game import ending as E
from hollowoak.game import hidden
from hollowoak.game import night as N
from hollowoak.game import notes


def _step(n, secs, dt=0.05):
    inp = N.Input()
    inp.yaw, inp.pitch = n.yaw, n.pitch
    for _ in range(int(secs / dt)):
        n.step(dt, inp)
        n.events.clear()


def test_every_ending_has_its_words_and_look():
    assert len(E.ORDER) == 8
    for name in E.ORDER[1:]:                                       # (Supper: game/death.py's own)
        e = E.Ending(name)
        assert e.her and e.after and len(e.light) == 3
    assert E.card("Fire") == "Ending 7 of 8: Fire" and E.card("Spellbound") == "Ending 8 of 8: Spellbound"


def test_fire_the_second_time():
    n = N.Night(seed=21)
    n.on = n.web.loom
    out = n.cast("warmth")
    assert out[-1][0] == "smoulder" and n.ending is None           # (once: a warning)
    n.spells.rest["warmth"] = 0.0
    n.on = n.web.loom
    out = n.cast("warmth")
    assert ("ablaze",) in out and n.ending is not None and n.ending.name == "Fire"
    assert n.ending_scene is None                                  # (she isn't before him for this one)
    _step(n, E.CARD + 0.5)
    assert n.ending.done


def test_fire_in_her_scene():
    n = N.Night(seed=22)
    n.on = n.web.loom
    n.flags["smouldered"] = 1
    tier, line, _said = n.spells.in_scene("warmth", n)
    assert tier == "insult" and n.flags.get("ablaze")
    _step(n, 0.1)
    assert n.ending is not None and n.ending.name == "Fire"


def test_dawn_staged_before_him():
    n = N.Night(seed=23)
    n.x, n.z = 1.0, 0.5
    n.y = n.tree.floor_at(1.0, 0.5, 1.0)
    n.end("Dawn")
    assert n.ending_scene is not None
    _step(n, 3.0)
    assert n.her.staged is not None and n.camera is not None


def test_what_she_hides():
    assert hidden.unlock({"mark_crown"}) == []
    assert hidden.unlock({"mark_crown", "vision_before"}) == ["true_name"]
    got = hidden.unlock({"mark_crown", "vision_before", "unnamed", "journal"})
    assert set(got) == {"true_name", "what_she_was"}
    assert not hidden.knows({"true_name"}) and hidden.knows({"true_name", "what_she_was"})
    for pid in ("true_name", "what_she_was"):
        assert pid in notes.PAGES and notes.PAGES[pid][0] in notes.SECTIONS
    assert hidden.spoken("I know who you were. Ilsabet.") and not hidden.spoken("Ysmeine")


def test_spoken_is_the_hidden():
    n = N.Night(seed=24)
    talk = D.Conversation(n, None)
    talk.open("crown", lambda *a: None)
    assert not talk.knows_her and not n.flags.get("named")
    talk.knows_her = True
    got = []
    talk.say("I know your name. Ilsabet.", lambda t, ch: got.append(t))
    assert n.flags.get("named") and hidden.NAME in got[0]
    assert A.Acts().decide(n) == "The hidden"
