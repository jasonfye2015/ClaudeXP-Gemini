"""Talking with her: the script (every way through the first audience), a model (judged, remembered, answered - here
a stand-in that answers as one would), her murmurs, and what the rules keep out of her mouth."""
import random
import tempfile

from hollowoak.game import dialogue as D
from hollowoak.game import moods as M
from hollowoak.game import night as N
from hollowoak.game import persona as P
from hollowoak.game import script as S
from hollowoak.game.records import Records


class FakeModel:
    """Answers as a model would: the judge's two lines for a judging, her words (with some mess to clean) otherwise."""

    def __init__(self, verdict="TAGS: honest, deep\nREMEMBER: He is afraid of the dark, and came anyway."):
        self.verdict, self.asked = verdict, []

    def speaking(self):
        return "fake"

    def ask(self, messages, done, max_tokens=160, temperature=0.9):
        self.asked.append(messages)
        if messages[0]["content"].startswith("You read a conversation"):
            done(self.verdict)
        else:
            done('*She shifts on the silk.* "Afraid, and still here. Good." Ysmeine: tell me more.\nClaude: I will.')


def test_every_way_through_the_first_audience_ends():
    nodes = S.SCENES["audience"]["nodes"]
    for nid, node in nodes.items():                                            # (the script hangs together)
        assert "her" in node and len(node["her"]) < 260
        nexts = [c[2] for c in node.get("choices", [])] + ([node["next"]] if "next" in node else [])
        assert nexts or "end" in node, nid
        for nx in nexts:
            assert nx in nodes, (nid, nx)
        for c in node.get("choices", []):
            assert all(k in M.HEARD for k in c[1]), c
    seen_ends = set()
    for seed in range(60):                                                     # (walk it, choosing at random)
        rng = random.Random(seed)
        n = N.Night(seed=seed)
        talk = D.Conversation(n, None, rng=rng)
        assert talk.mode == "script"
        out = []
        talk.open("audience", lambda t, ch: out.append((t, ch)))
        for _ in range(30):
            text, choices = out[-1]
            assert text
            if choices is None:
                break
            talk.choose(rng.randrange(len(choices)), lambda t, ch: out.append((t, ch)))
        assert out[-1][1] is None and talk.ended in ("done", "cold")
        seen_ends.add(talk.ended)
    assert seen_ends == {"done", "cold"}


def test_her_choices_move_her():
    n = N.Night(seed=1)
    talk = D.Conversation(n, None)
    out = []
    talk.open("audience", lambda t, ch: out.append((t, ch)))
    before = n.moods.values()
    talk.choose(2, lambda t, ch: out.append((t, ch)))                         # ("Somewhere I can learn...": honest, deep)
    after = n.moods.values()
    assert after["fascination"] > before["fascination"] and after["regard"] > before["regard"]
    assert "hunger behind the eyes" in out[-1][0]


def test_a_model_judges_remembers_and_answers():
    n = N.Night(seed=2)
    fake = FakeModel()
    talk = D.Conversation(n, fake, {"met": 2, "summary": "Last time, he left before the night was out."})
    assert talk.mode == "model"
    out = []
    talk.open("audience", lambda t, ch: out.append((t, ch)))
    before = n.moods.values()
    talk.say("I'm afraid of the dark, but I came anyway.", lambda t, ch: out.append((t, ch)))
    text, choices = out[-1]
    assert text == "Afraid, and still here. Good. Tell me more." and choices == []    # (her words only: cleaned)
    assert n.moods.fascination > before["fascination"]
    assert talk.memory == ["He is afraid of the dark, and came anyway."]
    sysmsg = fake.asked[-1][0]["content"]
    assert "Ysmeine" in sysmsg and "Never say you are an AI" in sysmsg and "afraid of the dark" in sysmsg
    assert "You have met him before: 2 other nights" in sysmsg
    fake.verdict = "TAGS: none\nREMEMBER: none"
    mid = n.moods.patience
    talk.say("I'm afraid of the dark, but I came anyway.", lambda t, ch: out.append((t, ch)))
    assert n.moods.patience < mid - 4                                         # (the same thing again: repetition)
    fake.verdict = "TAGS: none\nREMEMBER: He asked whether she is an AI."     # (nothing from outside the night kept)
    talk.say("Are you an AI?", lambda t, ch: out.append((t, ch)))
    assert all("AI" not in m for m in talk.memory)
    for _ in range(D.TURNS):
        talk.say("Tell me of the others.", lambda t, ch: out.append((t, ch)))
    assert out[-1][1] is None and talk.ended == "done"                        # (and in time she sends him on)


def test_the_judge_read_however_it_writes():
    assert P.read_judgement("TAGS: flattery, evasion\nREMEMBER: none") == (["flattery", "evasion"], None)
    assert P.read_judgement("lie\nHe claims he isn't afraid.") == (["lie"], "He claims he isn't afraid.")
    assert P.read_judgement("") == ([], None)
    assert P.clean("Why? user I want to know.") == "Why?"
    assert P.clean("(She smiles.) One. Two. Three. Four.") == "One. Two. Three."


def test_her_murmurs_and_what_she_remembers_between_nights():
    n = N.Night(seed=3)
    talk = D.Conversation(n, None, rng=random.Random(1))
    got = []
    for _ in range(len(S.MURMURS["dark"])):
        talk.murmur("dark", got.append)
    assert len(set(got)) == len(S.MURMURS["dark"])                             # (no line again till all are said)
    with tempfile.TemporaryDirectory() as d:
        r = Records(d)
        r.night_over({"seconds": 300, "ending": "your larder", "lies": 2, "manner": 0.8,
                      "kept": "He set his teacher's beard alight."})
        again = Records(d)
        assert again.reputation["met"] == 1
        s = again.reputation["summary"]
        assert "your larder" in s and "lied to you 2 times" in s and "with care" in s and "beard" in s
