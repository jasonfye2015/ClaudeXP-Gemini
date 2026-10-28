"""The model threads (Kithylin AI's engine, which Soul and Song runs on, and the code studios' AI helper) never take
the program down: a thread let go of while it still runs aborts the whole process ("QThread: Destroyed while thread
is still running" - the crash of 27 and 28 October 2026). A fake llama-server here holds its first byte back the way
a model reading a long prompt does. If one of these breaks, this whole file crashes rather than failing politely."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import support

support.qapp()
from kithylinai import engine as E  # noqa: E402

DELAY = {"first": 0.2}


class _SlowModel(BaseHTTPRequestHandler):
    def log_message(self, *_a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        tag = body["messages"][-1]["content"]
        time.sleep(DELAY["first"])                       # (reading the prompt: nothing to cut off yet)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        try:
            for i in range(5):
                piece = {"choices": [{"delta": {"content": f"{tag}-{i} "}}]}
                self.wfile.write(f"data: {json.dumps(piece)}\n\n".encode())
                self.wfile.flush()
                time.sleep(0.1)
            self.wfile.write(b"data: [DONE]\n\n")
        except OSError:
            pass


_server = ThreadingHTTPServer(("127.0.0.1", 0), _SlowModel)
threading.Thread(target=_server.serve_forever, daemon=True).start()
E._server.url = lambda: f"http://127.0.0.1:{_server.server_address[1]}"
E.hosted = lambda: False
MODEL = SimpleNamespace(key="own:test", info={}, title="test",
                        path=SimpleNamespace(stem="test", name="test.gguf", stat=lambda: SimpleNamespace(st_size=2**30)))


def _engine():
    eng = E.Engine()
    eng.model, eng.ready, eng.shared = MODEL, True, False
    got = []
    eng.done.connect(lambda text, err: got.append((text.strip(), err)))
    return eng, got


def _settled():
    return support.pump(10, until=lambda: not E._running)


def test_overlapping_requests():
    """A new request while a reply is still coming: the old one stops quietly, the new one gets its own words"""
    DELAY["first"] = 0.2
    eng, got = _engine()
    eng.chat([{"role": "user", "content": "A"}])
    support.pump(0.4)
    eng.chat([{"role": "user", "content": "B"}])
    assert support.pump(10, until=lambda: got), "no reply came"
    assert got == [("B-0 B-1 B-2 B-3 B-4", "")], got
    assert _settled(), "a thread was never let go of"


def test_stop_while_the_model_reads_the_prompt():
    """Stop while the model is still reading the prompt: whoever asked hears "stopped" at once, and the next reply works"""
    DELAY["first"] = 4.0
    eng, got = _engine()
    eng.chat([{"role": "user", "content": "A"}])
    support.pump(0.4)
    t = time.monotonic()
    eng.stop()
    assert got == [("", "stopped")], got
    assert time.monotonic() - t < 4, "stop() waited for the model"
    DELAY["first"] = 0.2
    eng.chat([{"role": "user", "content": "B"}])
    assert support.pump(15, until=lambda: len(got) == 2)
    assert got[1] == ("B-0 B-1 B-2 B-3 B-4", ""), got
    assert _settled()


def test_engine_thrown_away_while_loading():
    """The window (and its engine) closed while a model is still loading"""
    real = E._server.start
    E._server.start = lambda *a: time.sleep(1.5)
    try:
        eng, _got = _engine()
        eng.load(MODEL, "auto", 4096, shared=False)
        del eng
        support.pump(0.2)
        assert _settled()
    finally:
        E._server.start = real


def test_interlink_turns_after_a_stop():
    """Interlink: stopping one Companion's request still frees the shared model for the other"""
    from soulsong.app import EngineBrain
    from soulsong.interlink import Handle, Lane
    DELAY["first"] = 3.0
    brain = EngineBrain()
    eng, _got = _engine()
    brain.engine = eng
    eng.done.connect(brain._done)
    eng.chunk.connect(brain._chunk)
    lane = Lane(brain)
    one, two = Handle(lane, "blue", "A"), Handle(lane, "red", "B")
    heard = []
    one.ask([{"role": "user", "content": "A"}], lambda t, e: heard.append(("A", e)))
    two.ask([{"role": "user", "content": "B"}], lambda t, e: heard.append(("B", t.strip(), e)))
    support.pump(0.4)
    one.stop()
    DELAY["first"] = 0.2
    assert support.pump(15, until=lambda: len(heard) == 2), heard
    assert heard == [("A", "stopped"), ("B", "B-0 B-1 B-2 B-3 B-4", "")], heard
    assert _settled()


def test_studio_helper_thread_let_go():
    """Python Studio and QBasic Studio: their AI helper's thread let go of mid-answer"""
    from pystudio import threads as T
    from pystudio.assistant import _Stream
    s = _Stream("test", [])
    s.run = lambda: time.sleep(1.0)
    s.start()
    del s
    support.pump(0.1)
    assert len(T._running) == 1, "it wasn't kept while it ran"
    assert support.pump(5, until=lambda: not T._running), "it was never let go of"


if __name__ == "__main__":
    support.main(globals())
