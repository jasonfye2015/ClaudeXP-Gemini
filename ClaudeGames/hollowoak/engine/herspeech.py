"""Her voice, aloud (as well as on screen): Kathleen, a Piper voice the Timeline already has, made rasping (engine/rasp.py).

Piper runs in the Timeline's voice runtime (Local Storage/LLM Models/voice - the same the Copilot's voice uses),
in a worker kept open (engine/piper_worker.py), so a line comes in about a second. No runtime, no Kathleen, or the
option off - and she is only read, never heard.

    her = HerSpeech()
    her.available()            -> is the runtime and the voice there?
    her.warm()                 start her voice now, quietly (the first start takes a few seconds)
    her.say(text, done)        done(samples float32 at rasp.OUT_RATE, or None), from a thread
    her.stop()
"""
import json
import os
import queue
import subprocess
import tempfile
import threading
from pathlib import Path

import numpy as np

from .rasp import rasp

VOICE = "en_US-kathleen-low"
WORKER = Path(__file__).with_name("piper_worker.py")
LENGTH = 1.3                     # (slow: she has never needed to hurry)


def voice_root():
    try:
        from claudecore.ai import llm_server
        return llm_server.models_dir() / "voice"
    except Exception:
        return None


def runtime():
    root = voice_root()
    if root is None:
        return None, None
    py = root / "runtime312" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    model = root / "models" / VOICE / f"{VOICE}.onnx"
    return (py if py.exists() else None), (model if model.exists() else None)


class HerSpeech:
    def __init__(self):
        self.proc = None
        self.jobs = queue.Queue()
        self.thread = None
        self.error = ""
        self.folder = Path(tempfile.mkdtemp(prefix="hollowoak-voice-"))
        self.n = 0

    def available(self):
        py, model = runtime()
        return py is not None and model is not None

    def _start(self):
        py, model = runtime()
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.proc = subprocess.Popen([str(py), "-I", str(WORKER), str(model), str(LENGTH)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                                     creationflags=flags)
        first = json.loads(self.proc.stdout.readline() or "{}")
        if "ready" not in first:
            raise RuntimeError("her voice didn't start")

    def _run(self):
        while True:
            text, done = self.jobs.get()
            if text is None:
                return
            samples = None
            try:
                if self.proc is None or self.proc.poll() is not None:
                    self._start()
                if done is None:                                 # (only warming her up)
                    continue
                self.n += 1
                out = str(self.folder / f"line{self.n}.npy")
                self.proc.stdin.write(json.dumps({"text": text, "out": out}) + "\n")
                self.proc.stdin.flush()
                reply = json.loads(self.proc.stdout.readline() or "{}")
                if "out" in reply:
                    raw = np.load(reply["out"])
                    os.remove(reply["out"])
                    samples = rasp(raw, reply["rate"])
                else:
                    self.error = reply.get("error", "no reply")
            except Exception as exc:
                self.error = str(exc)
                self.proc = None
            if done is not None:
                done(samples)

    def warm(self):
        if self.available() and self.thread is None:
            self.thread = threading.Thread(target=self._run, daemon=True, name="oak-her-voice")
            self.thread.start()
            self.jobs.put(("", None))

    def say(self, text, done):
        if not self.available() or not text.strip():
            done(None)
            return
        if self.thread is None:
            self.thread = threading.Thread(target=self._run, daemon=True, name="oak-her-voice")
            self.thread.start()
        self.jobs.put((text, done))

    def stop(self):
        if self.thread is not None:
            self.jobs.put((None, None))
        if self.proc is not None and self.proc.poll() is None:
            try:
                self.proc.stdin.close()
                self.proc.wait(timeout=2)
            except Exception:
                try:
                    self.proc.kill()                             # (our own worker, by its handle)
                except Exception:
                    pass
        self.proc = None
