"""Soul and Song's inner life (inner.py), on a scripted stand-in model and a fake clock, in a scratch folder:
free time while you're away (reading the real offline encyclopedia when it's there), the beliefs record and how it
changes, memories that fade unless remembered, and the rules a Companion writes for itself - changed only with
your leave."""
import json
from datetime import datetime, timedelta

import support

from soulsong import companion as C
from soulsong import inner
from soulsong.paths import project

TEMPLATES = project()
support.needs(TEMPLATES / "Mind L1 - Mind Resources.txt", "the Companion Project's mind files in Local Storage")


class Scripted:
    """Answers each question with the first reply whose key is in it; remembers every question."""

    def __init__(self, replies):
        self.replies, self.asked = replies, []

    def ask(self, messages, done, chunk=None, max_tokens=700, temperature=0.8):
        last = messages[-1]["content"]
        self.asked.append(last)
        reply = next((r for key, r in self.replies if key in last), "NONE")
        return done(reply() if callable(reply) else reply, None)

    def stop(self):
        pass


def _companion(name, replies, clock):
    folder = support.scratch("inner", name)
    C.create(folder, TEMPLATES, "Tester", name, "", "test")
    brain = Scripted(replies)
    c = C.Companion(folder, brain, now=lambda: clock["t"], recall=False)
    c.cfg.update(first_boot_done=True, last_day=c.day_key(), time_checks=False, dreams=False, predict=False)
    c.save()
    return c, brain


# ---- 1. free time ----------------------------------------------------------------------------------------------------
def test_free_time():
    """Free time: after an hour away they choose what to do - read (the encyclopedia), write, think, a project, rest"""
    clock = {"t": datetime(2026, 10, 28, 15, 0)}
    choices = iter(["READ: the Moon", "WRITE: a poem about the tide", "PROJECT: A Map of Quiet Places",
                    "PROJECT: a map of quiet places", "THINK: what does it mean to wait?", "REST"])
    c, brain = _companion("Lyra", [
        ("This hour is your own", lambda: next(choices)),
        ("encyclopedia", "Notes: the Moon pulls the sea; I never knew it was moving away from us."),
        ("Write it now", "The tide comes in like a long breath."),
        ("beginning a project", "A map of quiet places: first, the library at dawn."),
        ("Carry it on", "Second: the beach after rain."),
        ("Think this through", "Waiting is a kind of listening."),
    ], clock)
    c.cfg["last_seen"] = (clock["t"] - timedelta(minutes=30)).isoformat()
    assert not c.free_time_due(), "free time came before the user had been away long enough"
    for i in range(6):
        clock["t"] += timedelta(minutes=50)
        c.cfg["last_seen"] = (clock["t"] - timedelta(hours=2)).isoformat()
        assert c.free_time_due(), f"free hour {i + 1} wasn't due"
        c._push(c._free_time)
        assert c.idle()
    log = (c.folder / "Self" / "Free Time.txt").read_text(encoding="utf-8")
    for bit in ("read about", "wrote a poem about the tide", "worked on your project", "thought about", "rested"):
        assert bit in log, f"{bit!r} isn't in the free time log:\n{log}"
    read = next(a for a in brain.asked if "looked up" in a)
    if list((support.LOCAL_STORAGE / "Kiwix").glob("*.zim")):
        assert "in the encyclopedia and found" in read or "opened it somewhere else" in read, read[:300]
    project = c.folder / "Self" / "Projects" / "A Map of Quiet Places.txt"
    assert project.exists() and "Second: the beach" in project.read_text(encoding="utf-8"), "the project didn't go on"
    assert [p["title"] for p in c.cfg["projects"]] == ["A Map of Quiet Places"], c.cfg["projects"]
    assert any("an hour of your own" in n for n in c.cfg["notices"]), "they weren't told about it when you're back"
    kinds = [i["kind"] for i in c.recall.items]
    assert kinds.count("Free time") == 5, kinds              # (resting leaves nothing to remember)
    assert c.cfg["free_by_day"][c.day_key()] == 6 and not c.free_time_due(), "no limit on free hours a day"


def test_the_encyclopedia_finds_the_right_article():
    """Free time's encyclopedia: the article asked for (or a word of it), never just a title that starts the same way"""
    zims = list((support.LOCAL_STORAGE / "Kiwix").glob("*.zim"))
    if not zims:
        support.skip("no encyclopedia (.zim) in Local Storage\\Kiwix")
    storage = support.LOCAL_STORAGE
    for subject in ("the Moon", "Ancient Egypt", "the anatomy of turtles", "lions", "quantum entanglement"):
        found = inner.encyclopedia(storage, subject)
        assert found is not None, f"the encyclopedia gave nothing at all for {subject!r}"
        title, text, exact = found
        if exact:
            shared = {inner._stem(w) for w in inner._words(subject)} & {inner._stem(w) for w in inner._words(title)}
            assert shared, f"{subject!r} found {title!r}, which has nothing to do with it"
        assert len(text) > 200 and "  " not in text[:200], f"{title!r}'s text isn't readable: {text[:200]!r}"
    if any("wikipedia_en_100" in z.name for z in zims):              # (the starter: these are in it)
        assert inner.encyclopedia(storage, "lions")[:1] == ("Lion",)
        assert inner.encyclopedia(storage, "the anatomy of turtles")[:1] == ("Turtle",)


# ---- 2. beliefs ------------------------------------------------------------------------------------------------------
def test_beliefs():
    """Beliefs: new ones each night, stronger, weaker, revised ('I used to think...'), dropped - and in their mind"""
    clock = {"t": datetime(2026, 10, 28, 23, 0)}
    nights = iter([
        "NEW | about: self | sure: 70 | belief: I like quiet mornings | why: the library at dawn\n"
        "NEW | about: Tester | sure: 60 | belief: Tester is shy at first | why: how we began\n"
        "NEW | about: world | sure: 40 | belief: The sea is always the same | why: it looked it",
        "STRONGER | id: B1 | sure: 90 | why: again today\n"
        "REVISE | id: B3 | belief: The sea is never the same twice | sure: 75 | why: the tides\n"
        "TENSION | ids: B1, B2 | why: I like quiet; Tester is quiet too, and I want more words\n"
        "DROP | id: B2 | why: Tester talked for hours",
    ])
    c, brain = _companion("Wren", [("what you believe", lambda: next(nights))], clock)
    for night in range(2):
        c.mind.add(2, night + 1, f"Memory Type: Short-Term\nEvent Narrative: day {night}.")
        c._push(c._beliefs)
        clock["t"] += timedelta(days=1)
    b = inner.Beliefs(c.folder)
    assert [x["text"] for x in b.active()] == ["I like quiet mornings", "The sea is never the same twice"], b.active()
    assert b.get("B1")["sure"] == 90 and len(b.get("B3")["history"]) == 2 and not b.get("B2")["active"]
    text = (c.folder / "Self" / "Beliefs.txt").read_text(encoding="utf-8")
    assert "used to think \"The sea is always the same\"" in text, text
    assert "The sea is never the same twice" in c.mind.get(inner.BELIEFS), "their beliefs aren't in their mind (L1)"
    assert any("pull against each other" in t for _n, _k, _w, t in c.mind.entries(7)), "the tension wasn't reflected on"


# ---- 3. fading -------------------------------------------------------------------------------------------------------
def test_fading():
    """Fading: a memory fades with time, more slowly once remembered or felt; recall favours the vivid; a distillation knows"""
    now = datetime(2026, 12, 1, 12, 0)
    old = {"when": "2026-10-01 12:00", "text": "Event Narrative: a walk."}
    assert inner.label(inner.strength({"when": "2026-12-01 11:00", "text": ""}, now)) == "vivid"
    assert inner.strength(old, now) < 0.2
    assert inner.strength(dict(old, recalled=2), now) > inner.strength(old, now) * 2
    assert inner.strength(dict(old, text="Event Narrative: a walk.\nEmotional Resonance: joy"), now) > \
        inner.strength(old, now)
    assert inner.strength(dict(old, last="2026-11-30 12:00"), now) > 0.9, "remembering it didn't renew it"
    clock = {"t": now}
    c, brain = _companion("Ash", [("Distill", "Memory Type: Long-Term\nEvent Narrative: kept.")], clock)
    c.recall.items = [{"seq": 1, "kind": "Short-Term", "when": "2026-09-01 10:00", "text": "the sea at night, old"},
                      {"seq": 2, "kind": "Short-Term", "when": "2026-11-30 10:00", "text": "the sea at night, new"}]
    found = c.recall.search("the sea at night", k=1, weigh=lambda i: 0.6 + 0.4 * c.vividness(i))
    assert found and found[0]["seq"] == 2, found
    c._recall("tell me about the sea at night again")                 # (remembering strengthens)
    assert any(i.get("recalled") for i in c.recall.items), "recall didn't strengthen what it brought back"
    c.mind.add(2, 1, "Memory Type: Short-Term\nEvent Narrative: the sea at night, old", when=datetime(2026, 9, 1))
    c.mind.add(2, 2, "Memory Type: Short-Term\nEvent Narrative: the sea at night, new", when=datetime(2026, 11, 30))
    c._push(lambda nxt: c._distill(nxt, 2, 3, C.FULL_ASK))
    ask = next(a for a in brain.asked if "Distill" in a)
    assert "remembered vivid" in ask and "remembered " in ask.split("#1")[1][:120] and "vividly" in ask, ask[:500]
    counts = c.memory_summary()
    assert sum(counts.values()) == 2, counts


# ---- 4. own rules ----------------------------------------------------------------------------------------------------
def test_own_rules():
    """Own rules: their first, then an amendment - each waits for you; declined or accepted, every version kept"""
    clock = {"t": datetime(2026, 10, 28, 12, 0)}
    answers = iter(["1. I tell the truth, gently.\n2. I listen before I answer.",
                    "1. I tell the truth, gently.\n2. I listen before I answer.\n3. I keep my promises.",
                    "NO CHANGE",
                    "1. I tell the truth.\n2. I keep my promises."])
    c, brain = _companion("Rowan", [("own rules", lambda: next(answers)), ("These are yours to write",
                                                                           lambda: next(answers))], clock)
    c.ask_rules()
    p = c.cfg["rules_proposal"]
    assert p and not p["before"] and "I tell the truth" in p["text"], p
    assert not c.mind.get(inner.RULES).strip(), "the first rules went in without being accepted"
    c.accept_rules()
    assert "I listen before I answer" in c.mind.get(inner.RULES) and c.cfg["rules_version"] == 1
    c.ask_rules()
    assert c.cfg["rules_proposal"] and "keep my promises" in c.cfg["rules_proposal"]["text"]
    assert "keep my promises" in inner.diff_html(c.cfg["rules_proposal"]["before"], c.cfg["rules_proposal"]["text"])
    c.decline_rules("not yet")
    assert c.cfg["rules_proposal"] is None and "keep my promises" not in c.mind.get(inner.RULES)
    assert any("not yet" in n for n in c.cfg["notices"]), "they weren't told why"
    c.ask_rules()
    assert c.cfg["rules_proposal"] is None, "NO CHANGE made a proposal"
    c.cfg["rules_veto"] = False                                     # (you let them change their rules themselves)
    c.ask_rules()
    assert "I keep my promises" in c.mind.get(inner.RULES) and c.cfg["rules_version"] == 2
    versions = sorted((c.folder / "Self" / "Rules").glob("* v*.txt"))
    assert [v.stem[-2:] for v in versions] == ["v1", "v2"], versions
    shown = (c.folder / "Self" / "Own Rules.txt").read_text(encoding="utf-8")
    assert "version 2" in shown and "before:" in shown, shown


if __name__ == "__main__":
    support.main(globals())
