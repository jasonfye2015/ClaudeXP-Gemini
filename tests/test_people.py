"""Thornwick's people: what a language model is told about them and about Claude, and their own lines without one."""
import random

from claudenites.engine.speech import Speech
from claudenites.game import people
from claudenites.game.world import Game


def test_what_the_model_is_told():
    g = Game.new(seed=3)
    p = g.player
    p.stats.update(deepest=23, deaths=4, kills=210, guardians=["The Rat King", "The Mushroom King"])
    g.run_floor = 21
    for key in people.PEOPLE:
        sp = people.system_prompt(key, g)
        assert "floor 23" in sp and "4 times" in sp and "The Mushroom King" in sp and "floor 21" in sp
        assert "one to three short sentences" in sp and "AI" in sp
        msgs = people.chat_request(key, g, [("claude", "Hello"), ("them", "Hm.")], "What's below?")
        assert [m["role"] for m in msgs] == ["system", "user", "assistant", "user"]
        assert msgs[-1]["content"] == "What's below?"
    assert people.greeting_request("sage", g)[0]["role"] == "system"


def test_cleaning_a_reply():
    assert people.clean('*leans in* "Set a storm core \u2014 lad."') == "Set a storm core - lad."
    assert people.clean("(smiling) Hm.\nYes.") == "Hm. Yes."
    long = "Word. " * 200
    assert len(people.clean(long)) <= 420


def test_their_own_lines():
    g = Game.new(seed=4)
    rng = random.Random(1)
    for key in people.PEOPLE:
        for _ in range(10):
            line = people.line(key, g, rng)
            assert line and "{" not in line
    g.player.stats.update(deepest=9, deaths=2)
    assert any("9" in people.line("apothecary", g, random.Random(s)) for s in range(30))


def test_no_engine_no_talk():
    s = Speech(enabled=False)
    assert not s.available()
    got = []
    s.ask([{"role": "user", "content": "hi"}], got.append)
    assert got == [None]
