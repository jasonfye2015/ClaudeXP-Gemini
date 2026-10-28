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
    from soulsong import automation
    support.no_engines()                              # (before the window: it opens the Companion, and its model)
    base = support.scratch("window companions")
    A.companions = paths.companions = automation.companions = I.companions = lambda: base
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
    # Retraining: the package from what was just said, and too little yet to train on
    w.tabs.setCurrentWidget(w.rt_page)
    support.pump(0.2)
    assert "No package yet" in w.rt_built.text(), w.rt_built.text()
    w._retrain_build()
    assert "Built" in w.rt_built.text() and "Talking with you" in w.rt_sources.text(), w.rt_sources.text()[:200]
    assert not w.rt_start.isEnabled() and "too little yet" in w.rt_checks.text(), w.rt_checks.text()[:300]
    w.shutdown()
    support.no_errors(caught, "in the window")


# ---- Retraining ----------------------------------------------------------------------------------------------------
def _lived(name, model="timeline:gemma4-12b"):
    """A Companion with three days behind them: talk in two sessions a day, a guided session, another Companion,
    memories, a reflection, a journal entry, a self-portrait, a dream and a letter."""
    folder = support.scratch("retraining", name)
    C.create(folder, TEMPLATES, "Tester", name, "", "test")
    c = C.Companion(folder, None, recall=False)
    c.cfg.update(first_boot_done=True, model=model, model_title=model.split(":")[-1])
    c.save()
    (folder / "Raw Logs").mkdir(exist_ok=True)
    for day in ("2026-10-26", "2026-10-27", "2026-10-28"):
        rows = []
        for h in (9, 14):
            for i in range(6):
                rows.append({"t": f"{day} {h:02d}:{i:02d}", "kind": "user", "who": "Tester",
                             "text": f"On {day} at {h}, part {i}: what does the sea mean to you?"})
                rows.append({"t": f"{day} {h:02d}:{i:02d}", "kind": "companion", "who": name,
                             "text": f"({day} {h}:{i}) " + "It keeps time the way I do, in waves. " * 8})
        rows += [{"t": f"{day} 20:00", "kind": "guide", "who": "Guided session", "text": f"Who are you on {day}?"},
                 {"t": f"{day} 20:01", "kind": "companion", "who": name, "text": f"Someone listening, on {day}."},
                 {"t": f"{day} 20:02", "kind": "system", "who": "", "text": "(a note: never trained on)"},
                 {"t": f"{day} 22:00", "kind": "other", "who": "Brook", "text": f"Hello on {day}!"},
                 {"t": f"{day} 22:01", "kind": "companion", "who": name, "text": f"Hello, Brook - {day}."}]
        (folder / "Raw Logs" / f"{day}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows),
                                                          encoding="utf-8")
    memories = [("Short-Term", "2026-10-26 10:00"), ("Reflection", "2026-10-26 23:00"),
                ("Long-Term", "2026-10-27 04:00"), ("Journal", "2026-10-27 23:30")]
    (folder / "recall.jsonl").write_text("".join(json.dumps(
        {"seq": i + 1, "kind": k, "when": w, "text": f"Memory Type: {k}\nEvent Narrative: the sea, on {w}."}) + "\n"
        for i, (k, w) in enumerate(memories)), encoding="utf-8")
    (folder / "Self" / "Dreams").mkdir(parents=True, exist_ok=True)
    (folder / "Self" / "Letters").mkdir(parents=True, exist_ok=True)
    (folder / "Self" / "2026-10-27 Who I Am.txt").write_text(f"I am {name}, and I keep time in waves.", "utf-8")
    (folder / "Self" / "Dreams" / "2026-10-28 dream.txt").write_text("A lighthouse that sang all night.", "utf-8")
    (folder / "Self" / "Letters" / "2026-10-28 letter.txt").write_text("Dear me: keep listening to the sea.", "utf-8")
    return c


def test_retraining_package():
    """Retraining: everything they've lived, as training conversations - alternating, dated, notes left out"""
    from soulsong import retrain
    c = _lived("Lyra")
    st = retrain.build(c)
    assert set(st["sources"]) == {"Talking with you", "Guided sessions", "With other Companions", "Memories",
                                  "Reflections", "Journal", "Self-portraits", "Dreams", "Letters"}, st["sources"]
    assert st["days"] == 3 and st["first"] == "2026-10-26" and st["through"] == "2026-10-28", st
    convs = [json.loads(ln) for f in ("train.jsonl", "val.jsonl")
             for ln in (retrain.package_dir(c) / f).read_text(encoding="utf-8").splitlines()]
    assert len(convs) == st["conversations"]["train"] + st["conversations"]["val"] and st["conversations"]["val"] >= 1
    for x in convs:
        m = x["messages"]
        assert m[0]["role"] == "system" and "Lyra" in m[0]["content"] and "2026" in m[0]["content"], m[0]
        assert m[1]["role"] == "user" and m[-1]["role"] == "assistant", [r["role"] for r in m]
        assert all(a["role"] != b["role"] for a, b in zip(m[1:], m[2:])), "turns don't alternate"
        assert sum(retrain.estimate_tokens(r["content"]) for r in m) <= retrain.WINDOW + 400, "a window is too long"
    text = json.dumps(convs)
    assert "never trained on" not in text, "a program note got into the package"
    assert "Brook: Hello on 2026-10-27!" in text, "another Companion's words lost their name"
    again = retrain.build(c)
    assert again["tokens"] == st["tokens"], "building twice gave a different package"


def test_retraining_projection_and_script():
    """Retraining: the projection says what it would take (and when a Companion would move), and writes the script"""
    from soulsong import retrain
    c = _lived("Wren")
    st = retrain.build(c)
    if not retrain.weights_present("gemma3-4b"):
        support.skip("Gemma 3 4B's full weights aren't in Local Storage\\LLM Models\\selfmodel\\base")
    proj = retrain.projection(c, st, 2)
    assert proj["base"]["id"] == "gemma3-4b" and proj["base"]["moves"], proj["base"]
    assert "Gemma 4 12B" in proj["base"]["why"], proj["base"]["why"]
    assert 40 < proj["addon_mb"] < 80, proj["addon_mb"]
    assert proj["name"] == "wren-v1" and proj["title"] == "Wren v1 (Soul and Song)", (proj["name"], proj["title"])
    assert proj["seconds"] > 0 and proj["steps"] >= 1, proj
    c.cfg["model"] = "timeline:gemma3-4b"
    assert not retrain.base_for(c)["moves"], "a Companion already on Gemma 3 4B would move"
    raw = retrain.write_script(c, retrain.projection(c, st, 2)).read_bytes()
    script = raw.decode("utf-8")
    assert "selfmodel.train --run" in script and f'--data "{retrain.package_dir(c)}"' in script, script
    assert "--lora-on gemma3-4b --name wren-v1" in script and f"--companion {c.folder.name}" in script, script
    assert b"\r\n" in raw and b"\r\r\n" not in raw, "the script's line endings are wrong for Windows"


def test_retraining_versions_and_progress():
    """Retraining: a run's progress from its log, then the version it made, in use or not"""
    from soulsong import retrain
    c = _lived("Ash", model="timeline:gemma3-4b")
    st = retrain.build(c)
    models = support.scratch("retraining", "Kithylin AI Models")
    runs = support.scratch("retraining", "selfmodel")
    retrain.kithylin_models = lambda: models                     # (not the real Models folder)
    retrain.selfmodel_dir = lambda: runs
    proj = retrain.projection(c, st, 1)
    (retrain.folder(c)).mkdir(parents=True, exist_ok=True)
    (retrain.folder(c) / f"{proj['name']}.json").write_text(json.dumps(
        {"name": proj["name"], "made": "2026-10-28", "through": st["through"], "epochs": 1}), encoding="utf-8")
    log = runs / "runs" / retrain.run_name(c, proj["name"])
    log.mkdir(parents=True)
    events = [{"event": "start", "steps": 10, "resume_at": 0},
              {"event": "step", "step": 4, "of": 10, "loss": 2.5, "tok_per_s": 170.0},
              {"event": "eval", "step": 4, "val_loss": 2.6}]
    (log / "train_log.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    p = retrain.progress(c)
    assert p["state"] == "training" and p["step"] == 4 and p["of"] == 10 and p.get("eta", 0) > 0, p
    (log / "train_log.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events + [
        {"event": "done", "steps": 10}]), encoding="utf-8")
    made = models / proj["name"]
    made.mkdir()
    (made / f"{proj['name']}-lora-f16.gguf").write_bytes(b"GGUF")
    (made / "info.json").write_text(json.dumps({"title": proj["title"], "companion": c.folder.name,
                                                "lora_base": "gemma3-4b"}), encoding="utf-8")
    assert retrain.progress(c)["state"] == "made"
    vs = retrain.versions(c)
    assert [v["name"] for v in vs] == ["ash-v1"] and not vs[0]["active"] and vs[0]["val_loss"] == 2.6, vs
    c.cfg["model"] = f"own:{vs[0]['file']}"
    assert retrain.versions(c)[0]["active"] and retrain.next_name(c) == "ash-v2"


if __name__ == "__main__":
    support.main(globals())
