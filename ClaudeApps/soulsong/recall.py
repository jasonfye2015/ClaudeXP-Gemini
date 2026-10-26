"""Recall from the archive: every memory a Companion has ever had, kept whole, and brought back when it matters.

Distillation keeps the essence and lets details go. The originals aren't lost - the banks were archived before each
one emptied - and this index (recall.jsonl in the Companion's folder) holds every memory ever filed, with a vector
of its meaning. When the user says something, the closest older memories that aren't already in the Companion's
banks come back into the conversation, in full ("adaptive recall").

Meanings come from nomic-embed-text (Local Storage/LLM Models), run here by a small llama-server of its own on the
processor - it never takes the graphics card from the Companion's model. Without it, recall matches words."""
import json
import math
import os
import re
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

MIN_SCORE = 0.62            # cosine similarity a memory needs to be recalled
MIN_WORDS = 2               # (without the embedder: rare words in common)
STOP = set("""a an and are as at be been but by for from had has have he her his i if in into is it its me my of on or
our she so that the their them then there they this to was we were what when where which who will with you your
about just like really very can could would should did does do not no yes all any some more most one two also
today tonight day days time me we us i'm it's that's""".split())

_embedder = None
_lock = threading.Lock()


class Embedder:
    """nomic-embed-text on a llama-server of our own (CPU only), started in the background the first time."""

    def __init__(self):
        self.url, self.proc, self.state = None, None, "off"

    def start(self):
        if self.state != "off":
            return
        self.state = "starting"
        threading.Thread(target=self._start, name="soulsong-embedder", daemon=True).start()

    def _start(self):
        try:
            from kithylinai.engine import engine_exe
            from kithylinai.paths import TIMELINE_MODELS
            model = next(iter(sorted((TIMELINE_MODELS / "nomic-embed-text").glob("*.gguf"))), None)
            exe = engine_exe("cpu")
            if model is None or exe is None:
                self.state = "unavailable"
                return
            with socket.socket() as s:
                s.bind(("127.0.0.1", 0))
                port = s.getsockname()[1]
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            self.proc = subprocess.Popen([str(exe), "-m", str(model), "--embedding", "--port", str(port), "--host",
                                          "127.0.0.1", "-c", "2048", "--device", "none", "-ngl", "0"],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                         stdin=subprocess.DEVNULL, cwd=str(exe.parent), creationflags=flags)
            url = f"http://127.0.0.1:{port}"
            end = time.monotonic() + 90
            while time.monotonic() < end and self.proc.poll() is None:
                try:
                    with urllib.request.urlopen(url + "/health", timeout=2) as r:
                        if r.status == 200:
                            self.url, self.state = url, "ready"
                            return
                except Exception:
                    time.sleep(0.4)
            self.state = "unavailable"
        except Exception:
            self.state = "unavailable"

    def embed(self, texts, query=False):
        """[vector] for the texts, or None (not running, or it failed)."""
        if self.state != "ready" or not texts:
            return None
        prefix = "search_query: " if query else "search_document: "
        body = json.dumps({"input": [prefix + t[:1500] for t in texts]}).encode()
        try:
            req = urllib.request.Request(self.url + "/v1/embeddings", data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read())["data"]
            return [d["embedding"] for d in sorted(data, key=lambda d: d.get("index", 0))]
        except Exception:
            return None

    def stop(self):
        if self.proc is not None:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.proc, self.state = None, "off"


def embedder():
    global _embedder
    with _lock:
        if _embedder is None:
            import atexit
            _embedder = Embedder()
            atexit.register(_embedder.stop)           # (its llama-server goes when the program does)
        return _embedder


def shutdown():
    if _embedder is not None:
        _embedder.stop()


def _words(text):
    return {w for w in re.findall(r"[a-z][a-z']{2,}", text.lower()) if w not in STOP}


def _cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class Recall:
    def __init__(self, folder, use_embedder=True):
        self.file = Path(folder) / "recall.jsonl"
        self.emb = embedder() if use_embedder else None
        if self.emb is not None:
            self.emb.start()
        self.items = []
        try:
            for line in self.file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self.items.append(json.loads(line))
        except (OSError, ValueError):
            pass

    def _save(self):
        tmp = self.file.with_suffix(".part")
        tmp.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in self.items), encoding="utf-8")
        tmp.replace(self.file)

    def known(self, seq):
        return any(i["seq"] == seq for i in self.items)

    def add(self, seq, kind, when, text):
        """A memory into the archive, kept whole (with its meaning, when the embedder is up)."""
        if seq and self.known(seq):
            return
        item = {"seq": seq, "kind": kind, "when": when, "text": text.strip()}
        vec = self.emb.embed([text]) if self.emb is not None else None
        if vec:
            item["vec"] = [round(v, 5) for v in vec[0]]
        self.items.append(item)
        self._save()

    def backfill(self):
        """Give meanings to archived memories that came in while the embedder wasn't up."""
        if self.emb is None or self.emb.state != "ready":
            return 0
        todo = [i for i in self.items if "vec" not in i]
        for start in range(0, len(todo), 16):
            batch = todo[start:start + 16]
            vecs = self.emb.embed([i["text"] for i in batch])
            if not vecs:
                break
            for i, v in zip(batch, vecs):
                i["vec"] = [round(x, 5) for x in v]
        if todo:
            self._save()
        return len(todo)

    def search(self, text, exclude=(), k=2):
        """The older memories closest to `text`, not counting the ones in `exclude` (already in the banks)."""
        pool = [i for i in self.items if i["seq"] not in set(exclude)]
        if not pool or len(text.strip()) < 12:
            return []
        q = self.emb.embed([text], query=True) if self.emb is not None else None
        scored = []
        if q:
            for i in pool:
                if "vec" in i:
                    s = _cos(q[0], i["vec"])
                    if s >= MIN_SCORE:
                        scored.append((s, i))
        if not scored:                               # (no meanings yet: words in common)
            want = _words(text)
            for i in pool:
                shared = want & _words(i["text"])
                if len(shared) >= MIN_WORDS:
                    scored.append((len(shared) / 10, i))
        scored.sort(key=lambda x: -x[0])
        return [i for _s, i in scored[:k]]
