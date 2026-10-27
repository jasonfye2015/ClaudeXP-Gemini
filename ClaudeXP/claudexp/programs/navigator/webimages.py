"""Pictures for the Web, painted by the Copilot Image Creator's engine.

A page's pictures (/img/photo.gif?text=what+it+shows - and any picture the page invented, rewritten to that by
web.fix_images) show the old placeholder at first; meanwhile Stable Diffusion 1.5 paints them in the background, one
at a time, the current page's first, and the page is shown again as they arrive. Each is kept for good in the
browser's data folder (web_images/), so a page seen before has its pictures at once.

The engine runs as one worker (imagegen_worker.py serve) that loads the model once and closes after a few idle
minutes, giving the graphics card back. Only when the Image Creator's engine and SD 1.5 are installed; pictures of
anything adult stay placeholders."""
import hashlib
import json
import re
import subprocess
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QPixmap

from .web import DATA_DIR

CACHE = DATA_DIR / "web_images"
IDLE_SECONDS = 300               # the worker goes (and the graphics card is free) after this long with nothing to do
MAX_WAITING = 16                 # older requests are dropped beyond this (the pages they were for are long gone)
STYLE = "photograph, amateur digital camera photo from 2001, slightly low resolution"
NEGATIVE = ("text, words, letters, watermark, logo, signature, frame, border, nsfw, nude, naked, sexual, explicit, "
            "gore, blood, child")
ADULT = re.compile(r"\b(nsfw|nude|naked|sex\w*|yiff\w*|porn\w*|explicit|xxx|adult|erotic\w*|hentai|fetish\w*|"
                   r"murr\w*|lewd|kink\w*|bondage|genital\w*|penis|vagina|breasts?|butt|ass)\b", re.I)


def size_for(w, h):
    """The picture painted at SD 1.5's own scale, in the shape the page asked for."""
    if w and h:
        r = w / h
        if r > 1.15:
            return 512, 384
        if r < 0.87:
            return 384, 512
        return 512, 512
    return 512, 384


def key(text, w=0, h=0):
    sw, sh = size_for(w, h)
    return hashlib.sha1(f"{text.strip().lower()}|{sw}x{sh}".encode("utf-8")).hexdigest()[:20]


def allowed(text):
    return bool(text.strip()) and not ADULT.search(text)


class Painter(QObject):
    ready = Signal(str)                    # a picture's key, when it's there

    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()
        self.waiting = []                  # [(key, job)], newest last: the newest is painted first
        self.pending = set()
        self.failed = set()
        self.event = threading.Event()
        self.thread = None

    @staticmethod
    def engine():
        """(python, worker, model path) when the Image Creator's engine and SD 1.5 are installed, else None."""
        try:
            import imagegen
            if imagegen._engine_ready() and imagegen._installed("sd15"):
                return imagegen._runtime_python(), imagegen.WORKER, imagegen._model_path("sd15")
        except Exception:
            pass
        return None

    def pixmap(self, text, w=0, h=0):
        """The picture, if it has been painted (and if not, it's asked for); None meanwhile."""
        k = key(text, w, h)
        f = CACHE / f"{k}.png"
        if f.exists():
            pm = QPixmap(str(f))
            if not pm.isNull():
                return pm.scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation) if w and h else pm
        if allowed(text) and k not in self.failed:
            self.want(k, text, w, h)
        return None

    def want(self, k, text, w, h):
        with self.lock:
            if k in self.pending:
                for i, (kk, job) in enumerate(self.waiting):     # (asked for again: to the front)
                    if kk == k:
                        self.waiting.append(self.waiting.pop(i))
                        break
                return
            if self.engine() is None:
                return
            sw, sh = size_for(w, h)
            seed = int(k[:8], 16)
            job = {"id": k, "prompt": f"{text.strip()}, {STYLE}", "negative_prompt": NEGATIVE, "width": sw,
                   "height": sh, "steps": 16, "guidance": 7, "seed": seed, "output": str(CACHE / f"{k}.png")}
            self.waiting.append((k, job))
            self.pending.add(k)
            while len(self.waiting) > MAX_WAITING:
                old, _job = self.waiting.pop(0)
                self.pending.discard(old)
            if self.thread is None or not self.thread.is_alive():
                self.thread = threading.Thread(target=self._run, name="web-images", daemon=True)
                self.thread.start()
        self.event.set()

    def _next(self):
        with self.lock:
            return self.waiting.pop() if self.waiting else None

    def _run(self):
        """The worker's life: started for the first picture, fed one at a time, closed when idle."""
        eng = self.engine()
        if eng is None:
            return
        python, worker, model = eng
        CACHE.mkdir(parents=True, exist_ok=True)
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        proc = None
        try:
            import imagegen
        except Exception:
            imagegen = None
        try:
            while True:
                item = self._next()
                if item is None:
                    self.event.clear()
                    if not self.event.wait(IDLE_SECONDS):
                        with self.lock:
                            if not self.waiting:
                                self.thread = None
                                return
                    continue
                k, job = item
                if proc is None or proc.poll() is not None:
                    proc = subprocess.Popen([str(python), str(worker), "serve", "--model", "sd15", "--model-path",
                                             str(model)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                                            creationflags=flags)
                if imagegen is not None:
                    imagegen._active.add("web")                   # (the System Monitor shows it's at work)
                try:
                    proc.stdin.write(json.dumps(job) + "\n")
                    proc.stdin.flush()
                    ok = False
                    for line in proc.stdout:
                        if line.startswith(f"IMAGE_READY:{k}"):
                            ok = True
                            break
                        if line.startswith(f"ERROR:{k}"):
                            break
                except (OSError, ValueError):
                    ok = False
                finally:
                    if imagegen is not None:
                        imagegen._active.discard("web")
                with self.lock:
                    self.pending.discard(k)
                    if not ok:
                        self.failed.add(k)
                if ok:
                    self.ready.emit(k)
        finally:
            if proc is not None and proc.poll() is None:
                try:
                    proc.stdin.close()
                    proc.wait(20)
                except Exception:
                    proc.kill()


_painter = None


def painter():
    global _painter
    if _painter is None:
        _painter = Painter()
    return _painter


def shutdown():
    if _painter is not None:
        with _painter.lock:
            _painter.waiting.clear()
        _painter.event.set()
