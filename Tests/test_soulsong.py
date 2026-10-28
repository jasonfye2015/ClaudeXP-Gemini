"""Soul and Song on a stand-in model, with Companions made from the Companion Project's mind files in a scratch
folder (the real Companions are never opened): the memory banks sized to the context and classic 7:7:7 over weeks
of simulated days, Interlink's three modes, and the window itself - talking, the raw log, the memory bars, Settings."""
import json
from datetime import datetime, timedelta

import support

from soulsong import companion as C
from soulsong import interlink as I
from soulsong import paths

TEMPLATES = paths.project()
support.needs(TEMPLATES / "Mind L1 - Mind Resources.txt", "the Companion Project's mind files in Local Storage")

BODY = " ".join(f"Sentence {i} about what happened and what it meant." for i in range(5))


class StandIn:
    """Answers at once; remembers what it was asked."""
    on_thinking = None

    def __init__(self):
        self.asks = []
        self.engine = type("Engine", (), {"ready": True})()

    def ask(self, messages, done, chunk=None, max_tokens=700, temperature=0.8):
        last = messages[-1]["content"]
        roles = [m["role"] for m in messages[1:]]
        self.asks.append({"last": last, "max_tokens": max_tokens,
                          "alternating": all(a != b for a, b in zip(roles, roles[1:]))})
        if "Memory" in last or "memor" in last:
            return done(f"Memory Type: Kept\nEvent Narrative: {BODY}\nEmotional Resonance: Warmth\n"
                        "Tagging System: day", None)
        return done(f"(a reply to: {last.splitlines()[-1][:40]})", None)

    def stop(self):
        pass


def _companion(name, **cfg):
    folder = support.scratch("companions", name)
    C.create(folder, TEMPLATES, "Tester", name, "", "test")
    return folder, cfg


def _life(name, mode, context, days):
    """A Companion living `days` days of seven memories each, its day ending each night and Memory Day held when
    due. Returns (the Companion, the brain, {kind: [day numbers]} of what happened)."""
    clock = {"t": datetime(2026, 10, 1, 10, 0)}
    folder, _ = _companion(name)
    brain = StandIn()
    c = C.Companion(folder, brain, now=lambda: clock["t"], recall=False)
    c.cfg.update({"first_boot_done": True, "memory_mode": mode, "context": context, "context_auto": False,
                  "time_checks": False, "predict": False, "dreams": False, "journal": False, "tensions": False,
                  "last_memory_day": "2026-10-01", "last_day": "2026-10-01"})
    c.save()
    seen = {"distil L2": [], "distil": [], "memory day": [], "L2 after the night": []}

    def line(kind, text):
        if kind != "system":
            return
        if text.startswith("Distilling Short-Term"):
            seen["distil L2"].append(day)
        if text.startswith("Distilling"):
            seen["distil"].append(day)
        if text.startswith("It's Memory Day"):
            seen["memory day"].append(day)
    c.on_line = line
    for day in range(days):
        clock["t"] = datetime(2026, 10, 1, 10, 0) + timedelta(days=day)
        for i in range(7):
            c.history.append({"role": "user", "content": f"day {day} talk {i}", "t": C.stamp(clock["t"])})
            c.history.append({"role": "assistant", "content": "a reply", "t": C.stamp(clock["t"])})
            c.make_memory(force=True)
        c.end_day()
        seen["L2 after the night"].append(c.mind.count(2))
        clock["t"] += timedelta(hours=20)
        if c.memory_day_due():
            c.memory_day()
        c.cfg["last_day"] = c.day_key()
    assert c.idle(), "work was left in its queue"
    return c, brain, seen


def test_sized_banks_on_a_big_context():
    """Sized banks, 128k context: short-term memories pile up for weeks; Memory Day keeps its rituals without distilling"""
    c, brain, seen = _life("Big", "budget", 131072, 21)
    assert len(seen["memory day"]) == 3, seen["memory day"]
    assert seen["distil L2"] and min(seen["distil L2"]) >= 10, f"L2 distilled on days {seen['distil L2']}"
    for level in (2, 3, 4, 5):
        assert c.bank_tokens(level) < c.bank_budget(level), f"L{level} is over its share"
    bigger = [a for a in brain.asks if "memories, so let" in a["last"]]
    assert bigger and max(a["max_tokens"] for a in bigger) > 700, "a big bank wasn't given room for a fuller memory"


def test_sized_banks_on_a_small_context():
    """Sized banks, 16k context: they distil early and often, and never outgrow their share"""
    c, _brain, seen = _life("Small", "budget", 16384, 14)
    assert seen["distil L2"] and min(seen["distil L2"]) <= 4, f"L2 first distilled on day {seen['distil L2'][:1]}"
    assert len(seen["distil"]) >= 6, seen["distil"]
    for level in (2, 3, 4, 5):
        assert c.bank_tokens(level) < c.bank_budget(level), f"L{level} is over its share"


def test_classic_seven_seven_seven():
    """Classic 7:7:7: the day's short-term memories are distilled every night"""
    c, _brain, seen = _life("Classic", "classic", 131072, 14)
    assert set(seen["L2 after the night"]) == {0}, seen["L2 after the night"]
    assert sorted(set(seen["distil L2"])) == list(range(14)), seen["distil L2"]
    assert len(seen["memory day"]) == 2, seen["memory day"]
    assert c.mind.count(3) <= C.FULL


# ---- Interlink ----------------------------------------------------------------------------------------------------
def _pair():
    clock = {"t": datetime(2026, 10, 28, 10, 0)}
    brain = StandIn()
    lane = I.Lane(brain, on_active=lambda h: None)
    pair = []
    for name, colour in (("Aura", "#1F4E99"), ("Brook", "#B71C1C")):
        folder, _ = _companion(name)
        c = C.Companion(folder, None, now=lambda: clock["t"], recall=False)
        c.cfg.update({"first_boot_done": True, "name": name, "memory_every": 99})
        c.save()
        c.brain = lane.handle(colour, lambda n=name: n)
        said = []
        c.on_line = lambda kind, text, said=said: said.append((kind, text))
        c.said = said
        pair.append(c)
    return pair, brain


def _play(session, a, b, users=(), limit=400):
    tick = {"t": 0.0}
    session.now = lambda: tick["t"]
    users = list(users)
    for i in range(limit):
        tick["t"] += 3
        if users and session.mode == "group" and not session.turns and session.waiting is None and i % 4 == 0:
            session.user_says(users.pop(0))
        session.tick()
        if not session.running and a.idle() and b.idle():
            return
    raise AssertionError(f"the {session.mode} session never finished")


def _check(mode, script, **extra):
    (a, b), brain = _pair()
    before = (a.cfg.get("memory_seq", 0), b.cfg.get("memory_seq", 0))
    s = I.Session(a, b, mode, script, now=lambda: 0, on_guide=lambda t: None, on_status=lambda t: None, **extra)
    users = ["Hi both! I'm happy you're here.", "Brook, what do you think?", "And Aura?", "Let's keep going.",
             "That was lovely.", "One more thought from each of you?", "Thanks!", "Bye for now."] * 2
    _play(s, a, b, users if mode == "group" else ())
    spoke = {c.name: sum(1 for k, _t in c.said if k == "companion") for c in (a, b)}
    assert spoke["Aura"] and spoke["Brook"], spoke
    assert all(x["alternating"] for x in brain.asks), "a request didn't alternate user and assistant turns"
    assert a.cfg.get("memory_seq", 0) > before[0] and b.cfg.get("memory_seq", 0) > before[1], "no memories made"
    return a, b, s


def test_interlink_guided():
    """Interlink, guided together: both speak, each makes memories"""
    _check("guided", I.scripts("guided")[0])


def test_interlink_open():
    """Interlink, open conversation: exactly the messages asked for, and each hears the other by name"""
    a, b, s = _check("open", I.scripts("open")[0], messages=8)
    assert s.spoken == 8, s.spoken
    heard = [m["content"] for m in b._messages() if m["role"] == "user"]
    assert any("Aura" in h for h in heard), "Brook doesn't hear who said it"


def test_interlink_group():
    """Interlink, group chat with you"""
    _check("group", I.scripts("group")[1])


def test_interlink_stopped_part_way():
    """Interlink stopped part way: it stops, and each still makes a memory of it"""
    (a, b), _brain = _pair()
    tick = {"t": 0.0}
    s = I.Session(a, b, "open", I.scripts("open")[1], messages=30, now=lambda: tick["t"])
    for _i in range(8):
        tick["t"] += 3
        s.tick()
    before = (a.cfg.get("memory_seq", 0), b.cfg.get("memory_seq", 0))
    s.stop()
    for _i in range(10):
        s.tick()
    assert not s.running
    assert a.cfg.get("memory_seq", 0) > before[0] and b.cfg.get("memory_seq", 0) > before[1]


# ---- the window ----------------------------------------------------------------------------------------------------
def test_the_window():
    """The window: talk, the raw log, the memory bars sized to the context, and the memory settings"""
    support.qapp()
    caught = support.catch_errors()
    from PySide6.QtCore import QTimer
    import soulsong.app as A
    from soulsong import automation, recall
    base = support.scratch("window companions")
    A.companions = paths.companions = automation.companions = I.companions = lambda: base
    recall.Embedder.start = lambda self: setattr(self, "state", "unavailable")    # (no embedding server)
    folder = base / "companion-test"
    C.create(folder, TEMPLATES, "Tester", "Lyra")
    cfg = json.loads((folder / "companion.json").read_text(encoding="utf-8"))
    cfg.update(first_boot_done=True, last_day="2099-01-01", context=32768, context_auto=False, dreams=False,
               time_checks=False)
    (folder / "companion.json").write_text(json.dumps(cfg), encoding="utf-8")

    def ask(messages, done, chunk=None, max_tokens=700, temperature=0.8):
        last = messages[-1]["content"]
        text = (f"Memory Type: Short-Term\nEvent Narrative: {BODY}" if "Short-Term Memory" in last
                else "I'm here, and glad you are too.")
        QTimer.singleShot(10, lambda: done(text, ""))

    w = A.SoulAndSong(None)
    w.load_model = lambda *a, **k: None
    w.brain.ask = ask
    w.brain.engine.ready = True
    w.resize(1280, 800)
    w.show()
    w.fill_companions(select=str(folder))
    support.pump(0.5)
    assert w.comp is not None and w.comp.name == "Lyra", "the Companion didn't open"
    w.comp.cfg["last_day"] = w.comp.day_key()
    for text in ("Good morning! How are you?", "Tell me something you noticed lately."):
        w.comp.say(text)
    w.comp.make_memory("A test memory.")
    assert support.pump(10, until=lambda: w.comp.idle() and w.comp.mind.count(2) >= 1), "no memory was made"
    support.pump(0.5)
    # the raw log: everything, from today
    kinds = {json.loads(ln)["kind"] for p in (folder / "Raw Logs").glob("*.jsonl")
             for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()}
    assert {"user", "companion", "memory", "asked", "answered"} <= kinds, kinds
    w.tabs.setCurrentWidget(w.raw_page)
    support.pump(0.3)
    assert w.raw_day.count() >= 1 and w.comp.day_key() in w.raw_day.itemText(0), w.raw_day.itemText(0)
    # the Mind tab: sized banks, in tokens of their share
    w.refresh_panel()
    assert "sized to the context" in w.banks_box.title(), w.banks_box.title()
    assert "tokens" in w.banks[2].bar.format(), w.banks[2].bar.format()
    # Settings: classic 7:7:7 is still there, and saving it sticks
    modes = [w.s_mode.itemData(i) for i in range(w.s_mode.count())]
    assert modes == ["budget", "classic"], modes
    w.s_mode.setCurrentIndex(1)
    assert not w.s_budget.isEnabled() and "Seven memories" in w.s_budget_note.text()
    w.save_settings()
    support.pump(0.3)
    assert json.loads((folder / "companion.json").read_text(encoding="utf-8"))["memory_mode"] == "classic"
    w.refresh_panel()
    assert "7:7:7" in w.banks_box.title()
    w.shutdown()
    support.no_errors(caught, "in the window")


if __name__ == "__main__":
    support.main(globals())
