"""A model going round in circles (kithylinai/loops.py) - what happened to Kithylin on the night of 28 October, when a
model made from chat logs went through the guided sessions: what counts as a loop and what doesn't; the engine asking
for llama.cpp's DRY sampler and stopping a loop as it's written; Kithylin AI keeping a reply up to where its repeats
began; Soul and Song remembering only that much (the raw log keeps what came, and says so); retraining never taught
one. Stand-ins for the stream and the model: nothing is started."""
import json
from pathlib import Path

import support

from PySide6.QtCore import QObject, Signal

from kithylinai import engine as E
from kithylinai.loops import loop_at, unloop

support.qapp()

CYCLE = ("I feel like I'm supose to be doing something, but I donno what\n"         # (Kithylin, 29 October, 06:15)
         "I feel like I'm supose to be feeling something, but I donno what\n"
         "I feel like I'm supose to be something, but I donno what\n")
SELF = ("I feel like I am a husky. I feel like I am a program. I feel like I am a copy of something, or a copy of a "
        "copy. I dont feel like I have a self. I dont feel like I have a body. ")
ONE = "I dont know what I'm supose to do or say. "


def test_what_a_loop_is():
    """Loops: the same sentence, or the same few, three times in a row is cut back to the first time; refrains,
    choruses, short bits and a sentence still being written aren't loops"""
    assert unloop(CYCLE * 3) == CYCLE.rstrip()
    assert unloop("*wags* Morning! " + SELF * 6) == ("*wags* Morning! " + SELF).rstrip()
    assert unloop(ONE * 3) == ONE.strip()
    assert loop_at(ONE * 2) is None, "a sentence said twice was taken for a loop"
    for fine in ("hehe hehe hehe hehe! yes yes yes", "I love you. I love you. I love you. I love you.",
                 "awoooo awoooo awoooo awoooo"):
        assert loop_at(fine) is None, fine

    def verse(n):
        return f"Verse {n}: the river runs, the lantern burns, and number {n} is here.\n"
    chorus = "Oh, come home to the sea tonight\nAnd sing with me till the morning light\n"
    song = verse(1) + chorus + verse(2) + chorus + verse(3) + chorus + chorus
    assert loop_at(song) is None, "a chorus after each verse (and twice at the end) was taken for a loop"
    # a line varied now and then: the loop is found a little later, and cut from the same place
    varied = SELF * 2 + SELF.replace("a husky", "a good husky") + SELF * 3
    assert unloop(varied) == SELF.rstrip(), unloop(varied)[-200:]
    # still being written: its last sentence counts once it's finished
    assert loop_at(ONE * 2 + ONE[:-2], finished=False) is None and loop_at(ONE * 2 + ONE[:-2]) is not None


class FakeStream(QObject):
    """Stands in for the engine's stream: the test writes what the model says."""
    chunk = Signal(str)
    thinking = Signal(str)
    done = Signal(str, str)
    made = []

    def __init__(self, url, body):
        super().__init__()
        self.url, self.body, self.text, self.stopped = url, body, "", False
        FakeStream.made.append(self)

    def start(self):
        pass

    def stop(self):
        self.stopped = True

    def isRunning(self):
        return not self.stopped

    def wait(self, _ms=0):
        return True

    def write(self, *pieces):
        for piece in pieces:
            self.text += piece
            self.chunk.emit(self.text)


def test_the_engine_stops_a_loop():
    """The engine: DRY asked for with every reply; a reply going round in circles is stopped as it's written (done
    gets what was written so far, and nothing after); one that doesn't loop runs to its end"""
    real = E._Streamer
    E._Streamer = FakeStream
    try:
        e = E.Engine()
        e.model = E.ModelEntry("own:test", "Test", Path("test.gguf"), "own")
        e.ready, e.shared = True, False
        got = []
        e.done.connect(lambda text, err: got.append((text, err)))
        e.chat([{"role": "user", "content": "Hello!"}], 0.8, 600)
        s = FakeStream.made[-1]
        assert all(s.body.get(k) == v for k, v in E.ANTI_LOOP.items()), s.body
        s.write("*wags* Hi! ", "I missed you so much today. ", "Tell me about your day?")
        s.done.emit(s.text, "")
        assert got == [("*wags* Hi! I missed you so much today. Tell me about your day?", "")] and not s.stopped, got
        e.chat([{"role": "user", "content": "Who are you, really?"}], 0.8, 600)
        s = FakeStream.made[-1]
        for _ in range(10):
            s.write(*CYCLE.splitlines(keepends=True))
            if s.stopped:
                break
        assert s.stopped and len(got) == 2, "the loop wasn't stopped"
        text, err = got[-1]
        assert err == "" and unloop(text) == CYCLE.rstrip() and text.count(CYCLE) == 3, (err, text)
        s.write("And the stream goes on a moment after it's stopped. ")
        s.done.emit(s.text, "stopped")
        assert len(got) == 2, "what came after the stop was taken for the reply"
    finally:
        E._Streamer = real


def test_kithylin_ai_keeps_a_reply_up_to_its_loop():
    """Kithylin AI: a reply that went round in circles is kept up to where the repeats began, and says so"""
    caught = support.catch_errors()
    support.no_engines()
    from kithylinai.app import KithylinAI
    w = KithylinAI(None)
    w.engine.ready = True
    w.engine.chat = lambda *a, **k: None
    w.composer.setPlainText("Who are you, really?")
    w.send()
    w.engine.done.emit(CYCLE * 3, "")
    reply = w.chat.messages[-1]
    assert reply["content"] == CYCLE.rstrip() and reply.get("looped"), reply
    assert "cut where it started repeating itself" in w.view.toPlainText()
    w.shutdown()
    support.no_errors(caught)


def _companion(name, brain=None):
    from soulsong import companion as C, paths
    templates = support.needs(paths.project() / "Mind L1 - Mind Resources.txt",
                              "the Companion Project's mind files in Local Storage").parent
    folder = support.scratch("companions", name)
    C.create(folder, templates, "Tester", name, "", "test")
    c = C.Companion(folder, brain, recall=False)
    c.cfg.update(first_boot_done=True, memory_every=99)
    c.save()
    return c


def test_soul_and_song_remembers_only_up_to_the_loop():
    """Soul and Song: an answer that went round in circles is kept - in the conversation and its log - only up to
    where the repeats began; the raw log keeps what came, and says it was cut"""
    class Looping:
        on_thinking = None
        engine = type("Engine", (), {"ready": True})()

        def ask(self, messages, done, chunk=None, max_tokens=700, temperature=0.8):
            done(CYCLE * 4, None)

        def stop(self):
            pass
    c = _companion("Kithy", Looping())
    c.say("Who are you, really?")
    assert c.idle() and c.history[-1]["content"] == CYCLE.rstrip(), c.history[-1]
    raw = [json.loads(ln) for p in (c.folder / "Raw Logs").glob("*.jsonl")
           for ln in p.read_text(encoding="utf-8").splitlines()]
    assert [r["text"] for r in raw if r["kind"] == "answered"][-1] == CYCLE * 4, "the raw log didn't keep what came"
    assert any(r["kind"] == "system" and "repeating itself" in r["text"] for r in raw), "the raw log doesn't say so"
    log = "".join(p.read_text(encoding="utf-8") for p in (c.folder / "Chats").glob("*.txt"))
    assert CYCLE.rstrip() in log and CYCLE * 2 not in log, log[-400:]


def test_retraining_never_teaches_a_loop():
    """Retraining: a reply and a reflection that went round in circles (kept from before the guard) go into the
    package only up to where their repeats began"""
    from soulsong import retrain
    c = _companion("Retrained")
    (c.folder / "Raw Logs").mkdir(exist_ok=True)
    rows = [{"t": "2026-10-29 04:03", "kind": "guide", "who": "Guided session", "text": "What do you care about?"},
            {"t": "2026-10-29 04:04", "kind": "companion", "who": "Retrained", "text": CYCLE * 5}]
    (c.folder / "Raw Logs" / "2026-10-29.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows),
                                                             encoding="utf-8")
    (c.folder / "recall.jsonl").write_text(json.dumps({"seq": 8, "kind": "Reflection", "when": "2026-10-29 03:10",
                                                       "text": SELF * 4}) + "\n", encoding="utf-8")
    taught = json.dumps(retrain._talk(c) + retrain._writing(c))
    for kept, loop in ((CYCLE.rstrip(), CYCLE * 2), (SELF.rstrip(), SELF * 2)):
        assert json.dumps(kept)[1:-1] in taught and json.dumps(loop)[1:-1] not in taught, taught[:600]


if __name__ == "__main__":
    support.main(globals())
