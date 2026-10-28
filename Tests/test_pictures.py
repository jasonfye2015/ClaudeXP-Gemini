"""Pictures in Soul and Song: the engine loading a model's vision add-on (only when asked), the graphics memory
counting it, a Companion shown a picture once and remembering it after in its own words (or told it can't see it),
and the window - a picture added, pasted or dropped, kept small in the Companion's Pictures folder, shown in the
conversation and the raw log, and the Pictures setting. No model is ever started."""
import json
from pathlib import Path

import support

from soulsong import companion as C
from soulsong.paths import project

TEMPLATES = project()
support.needs(TEMPLATES / "Mind L1 - Mind Resources.txt", "the Companion Project's mind files in Local Storage")


def _picture(path, colour="tomato", size=(64, 48), alpha=False):
    """A plain picture, saved (for the tests' own folders only)."""
    support.qapp()
    from PySide6.QtGui import QColor, QImage
    img = QImage(size[0], size[1], QImage.Format_ARGB32 if alpha else QImage.Format_RGB32)
    img.fill(QColor(colour))
    path.parent.mkdir(parents=True, exist_ok=True)
    assert img.save(str(path)), f"couldn't make {path.name}"
    return path


def test_the_engine_loads_the_vision_add_on():
    """The engine: a model's vision add-on found beside it (or beside its base), and loaded only when asked for"""
    support.qapp()
    from kithylinai import engine
    from kithylinai.paths import TIMELINE_MODELS
    seeing, blind = support.scratch("models", "seeing"), support.scratch("models", "blind")
    for folder in (seeing, blind):
        (folder / "model.gguf").write_bytes(b"GGUF")
    (seeing / "mmproj-model-f16.gguf").write_bytes(b"GGUF")
    sees = engine.ModelEntry("own:a", "Seeing", seeing / "model.gguf", "test")
    not_sees = engine.ModelEntry("own:b", "Blind", blind / "model.gguf", "test")
    assert engine.mmproj_for(sees) == seeing / "mmproj-model-f16.gguf" and engine.mmproj_for(not_sees) is None
    gemma = TIMELINE_MODELS / "gemma3-4b"
    if (gemma / "mmproj-model-f16.gguf").exists():         # (an add-on model: its base's vision add-on)
        addon = engine.ModelEntry("own:c", "Lyra v1", blind / "model.gguf", "test",
                                  {"lora_base": "gemma3-4b", "lora_base_file": "gemma-3-4b-it-Q4_K_M.gguf"})
        assert engine.mmproj_for(addon) == gemma / "mmproj-model-f16.gguf", engine.mmproj_for(addon)
    started = []

    class Stopped:
        def poll(self):
            return 1                                       # (it "stops" at once - nothing ever runs)

    def popen(args, **_k):
        started.append(args)
        return Stopped()
    real = engine.subprocess.Popen, engine.engine_exe
    engine.subprocess.Popen, engine.engine_exe = popen, lambda _choice: Path("llama-server.exe")
    try:
        for model, vision in ((sees, True), (sees, False), (not_sees, True)):
            try:
                engine._Server().start(model, "auto", 8192, lambda _s: None, vision)
            except RuntimeError:
                pass
    finally:
        engine.subprocess.Popen, engine.engine_exe = real
    assert ["--mmproj" in a for a in started] == [True, False, False], started
    assert started[0][started[0].index("--mmproj") + 1] == str(seeing / "mmproj-model-f16.gguf"), started[0]


def test_the_graphics_memory_counts_it():
    """The graphics memory a model needs counts its vision add-on, when that's loaded too"""
    from kithylinai.paths import TIMELINE_MODELS
    from soulsong import hardware
    folder = TIMELINE_MODELS / "gemma3-4b"
    model, proj = next(folder.glob("gemma-3-4b*.gguf"), None), next(folder.glob("mmproj*.gguf"), None)
    if model is None or proj is None:
        support.skip("Gemma 3 4B and its vision add-on aren't in Local Storage")
    without, with_it = hardware.memory_gb(model, 32768), hardware.memory_gb(model, 32768, mmproj=proj)
    assert abs(with_it - without - proj.stat().st_size / 2**30 - hardware.VISION_GB) < 0.01, (without, with_it)


class Seeing:
    """The model, as a test sees it: every request kept; a picture described, anything else answered."""

    def __init__(self):
        self.asked = []

    def ask(self, messages, done, chunk=None, max_tokens=700, temperature=0.8):
        self.asked.append(messages)
        last = messages[-1]["content"]
        if isinstance(last, list) and "For your own memory of it" in last[0]["text"]:
            return done("A small grey cat asleep on a red blanket, in the sun.", None)
        return done("What a lovely cat!", None)

    def stop(self):
        pass


def test_seen_once_then_remembered():
    """A picture is shown to the model once, with its words; after that the conversation has what the Companion
    saw in it, in its own words - and a model that can't see is told so, instead of being shown it"""
    folder = support.scratch("pictures", "Lyra")
    C.create(folder, TEMPLATES, "Tester", "Lyra", "", "test")
    brain = Seeing()
    c = C.Companion(folder, brain, recall=False)
    c.cfg.update(first_boot_done=True, last_day=c.day_key(), time_checks=False, dreams=False, free_time=False)
    c.can_see = lambda: True
    shown = []
    c.on_picture = lambda path, kind, text: shown.append((Path(path).name, kind, text))
    c.say("Look at her!", picture=_picture(folder / "Pictures" / "cat.jpg"))
    assert c.idle() and len(brain.asked) == 2, len(brain.asked)
    reply, seen = brain.asked[0][-1]["content"], brain.asked[1][-1]["content"]
    assert isinstance(reply, list) and "Look at her!" in reply[0]["text"], reply
    assert reply[1]["type"] == "image_url" and reply[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert isinstance(seen, list) and "Tester just showed you this picture" in seen[0]["text"], seen[0]
    entry = c.history[-2]
    assert entry["picture"] == "Pictures/cat.jpg" and entry["seen"].startswith("A small grey cat"), entry
    assert shown == [("cat.jpg", "user", "Look at her!")], shown
    c.say("What colour was the blanket?")
    after = brain.asked[-1]
    assert all(isinstance(m["content"], str) for m in after), "the picture was shown to the model a second time"
    assert "What you saw in it: A small grey cat asleep on a red blanket" in json.dumps(after)
    raw = [json.loads(ln) for ln in (folder / "Raw Logs" / f"{c.day_key()}.jsonl").read_text("utf-8").splitlines()]
    said = next(e for e in raw if e["kind"] == "user" and e.get("picture"))
    assert said["picture"] == "Pictures/cat.jpg" and said["text"] == "Look at her!", said
    asked = [e["text"] for e in raw if e["kind"] == "asked"]
    assert any("[+ a picture]" in a for a in asked) and not any("base64" in a for a in asked), "the raw log has it raw"
    kept = json.loads((folder / "session.json").read_text(encoding="utf-8"))
    assert any(m.get("seen") for m in kept["history"]), "what it saw wasn't kept with the conversation"
    # a model that can't see pictures: told so, and not asked to describe it
    c.can_see = lambda: False
    n = len(brain.asked)
    c.say("", picture=_picture(folder / "Pictures" / "dog.jpg", "sienna"))
    last = brain.asked[-1][-1]["content"]
    assert len(brain.asked) == n + 1 and isinstance(last, str), "a model that can't see was shown the picture"
    assert "Tester sent a picture, but the model you're running on can't see pictures" in last, last
    assert c.history[-2]["content"] == "" and "seen" not in c.history[-2]


def test_the_window_with_pictures():
    """The window: a big picture pasted, kept small in Pictures and shown; a picture file dropped; the raw log shows
    them; the Pictures setting, and the Status tab saying whether they see them"""
    support.qapp()
    caught = support.catch_errors()
    from PySide6.QtCore import QMimeData, QTimer, QUrl
    from PySide6.QtGui import QColor, QImage
    import soulsong.app as A
    from soulsong import automation, paths
    from soulsong import interlink as I
    support.no_engines()                              # (before the window: it opens the Companion, and its model)
    base = support.scratch("pictures window")
    A.companions = paths.companions = automation.companions = I.companions = lambda: base
    folder = base / "companion-test"
    C.create(folder, TEMPLATES, "Tester", "Lyra")
    cfg = json.loads((folder / "companion.json").read_text(encoding="utf-8"))
    cfg.update(first_boot_done=True, last_day="2099-01-01", dreams=False, time_checks=False, free_time=False)
    (folder / "companion.json").write_text(json.dumps(cfg), encoding="utf-8")
    asked = []

    def ask(messages, done, chunk=None, max_tokens=700, temperature=0.8):
        asked.append(messages[-1]["content"])
        last = messages[-1]["content"]
        text = "A tomato-red square." if isinstance(last, list) and "For your own memory" in last[0]["text"] else "Red!"
        QTimer.singleShot(10, lambda: done(text, ""))

    w = A.SoulAndSong(None)
    w.load_model = lambda *a, **k: None
    w.brain.ask = ask
    w.brain.engine.ready = True
    w.brain.engine.vision = True                      # (as if its vision add-on were loaded)
    w.resize(1280, 800)
    w.show()
    w.fill_companions(select=str(folder))
    support.pump(0.5)
    assert w.comp is not None and w.comp.name == "Lyra", "the Companion didn't open"
    w.comp.cfg["last_day"] = w.comp.day_key()
    # a big picture, pasted
    big = QImage(3000, 2000, QImage.Format_RGB32)
    big.fill(QColor("tomato"))
    mime = QMimeData()
    mime.setImageData(big)
    assert w.composer.canInsertFromMimeData(mime)
    w.composer.insertFromMimeData(mime)
    assert w._picture is not None and w.attach_bar.isVisible(), "the pasted picture wasn't taken"
    w.composer.setPlainText("What colour is this?")
    w.send()
    assert support.pump(10, until=lambda: w.comp.idle() and len(asked) >= 2), "it wasn't answered and seen"
    kept = sorted((folder / "Pictures").glob("*.jpg"))
    size = QImage(str(kept[0])).size() if kept else None
    assert len(kept) == 1 and max(size.width(), size.height()) == A.PICTURE_MAX, (kept, size)
    assert not w.attach_bar.isVisible() and w._picture is None, "the picture was still waiting after it went"
    assert isinstance(asked[0], list) and "What colour is this?" in asked[0][0]["text"], asked[0]
    assert w.comp.history[-2].get("seen") == "A tomato-red square.", w.comp.history[-2]
    assert w.chat.toHtml().count("<img") == 1, "the picture isn't in the conversation"
    # a picture file dropped in, on its own (see-through: kept on white)
    png = _picture(base / "drop.png", "#8000FF00", (200, 100), alpha=True)
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(png))])
    assert w.composer.canInsertFromMimeData(mime)
    w.composer.insertFromMimeData(mime)
    w.send()
    assert support.pump(10, until=lambda: w.comp.idle() and len(asked) >= 4), "the dropped picture wasn't answered"
    assert len(list((folder / "Pictures").glob("*.jpg"))) == 2 and w.comp.history[-2]["content"] == ""
    # the raw log shows them; reopened, the conversation does too
    w.tabs.setCurrentWidget(w.raw_page)
    support.pump(0.3)
    assert w.raw_view.toHtml().count("<img") == 2, "the raw log doesn't show the pictures"
    w.open(str(folder))
    support.pump(0.3)
    assert w.chat.toHtml().count("<img") == 2, "reopened, the conversation lost its pictures"
    # the Pictures setting; Status says whether they see them
    w.tabs.setCurrentIndex(0)                         # (the Status tab: it's filled while it's showing)
    w.brain.engine.ready = True
    w.brain.engine.vision = True
    w.refresh_status()
    assert w.status_rows["Pictures"].text() == "sees them", w.status_rows["Pictures"].text()
    assert w.s_pictures.isChecked(), "pictures should be on to begin with"
    assert not w.s_mem.text() or "pictures" in w.s_mem.text(), w.s_mem.text()
    w.s_pictures.setChecked(False)
    w.save_settings()
    assert w.comp.cfg["pictures"] is False and w._vision(None, w.comp) is None
    w.brain.engine.vision = False
    w.refresh_status()
    assert w.status_rows["Pictures"].text() == "off (Settings)", w.status_rows["Pictures"].text()
    w.shutdown()
    support.no_errors(caught)


if __name__ == "__main__":
    support.main(globals())
