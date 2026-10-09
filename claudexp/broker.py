"""The model broker: every program's language-model requests go through one queue, one at a time.
(`ollama` here is ClaudeXP's stand-in, claudexp/stubs/ollama, answered by the bundled llama.cpp engine.)

There's one GPU, so requests run in priority order:
  FOREGROUND  something you're waiting on (an IM reply, a page, a private message)
  REPLY       people answering you in a room or channel
  CHATTER     ambient chatter in open programs
  BACKGROUND  world upkeep while you're busy elsewhere (journals, mail, catch-up)

Background jobs are counted as a 'batch' so maintenance programs (Windows Update, the virus
scanner, Disk Defragmenter) can show real progress while the model works.
"""
import threading

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

FOREGROUND, AIM, REPLY, CHATTER, BACKGROUND = 10, 8, 5, 0, -10

_thinking_cache = {}


def _supports_thinking(model):
    if model not in _thinking_cache:
        try:
            import ollama
            _thinking_cache[model] = "thinking" in (ollama.show(model).capabilities or [])
        except Exception:
            return False
    return _thinking_cache[model]


class _Emitter(QObject):
    done = Signal(object, str, str)     # job, text, error
    chunk = Signal(object, str)         # job, text so far
    thinking = Signal(object, str)      # job, reasoning so far (thinking models)
    started = Signal(object)


class Job(QRunnable):
    def __init__(self, broker, model, messages, options, priority, think, stream, on_done, on_chunk, images,
                 on_thinking=None):
        super().__init__()
        self.on_thinking = on_thinking
        self.setAutoDelete(False)
        self.broker = broker
        self.model, self.messages, self.options = model, messages, options
        self.priority, self.think, self.stream = priority, think, stream
        self.on_done, self.on_chunk = on_done, on_chunk
        self.prepare = images
        self.stop_flag = threading.Event()

    def stop(self):
        """Cancel: a queued job is skipped, a streaming one ends early."""
        self.stop_flag.set()

    def run(self):
        em = self.broker._emitter
        if self.stop_flag.is_set():
            em.done.emit(self, "", "stopped")
            return
        em.started.emit(self)
        text, reasoning, err = "", "", ""
        try:
            import ollama
            messages = self.prepare(self.model, self.messages) if self.prepare else self.messages
            extra = {}
            if self.think is not None and _supports_thinking(self.model):
                extra["think"] = self.think
            if self.stream:
                for part in ollama.chat(model=self.model, messages=messages, options=self.options,
                                        keep_alive="30m", stream=True, **extra):
                    if self.stop_flag.is_set():
                        err = "stopped"
                        break
                    if getattr(part.message, "thinking", None):
                        reasoning += part.message.thinking
                        em.thinking.emit(self, reasoning)
                    if part.message.content:
                        text += part.message.content
                        em.chunk.emit(self, text)
            else:
                resp = ollama.chat(model=self.model, messages=messages, options=self.options,
                                   keep_alive="30m", **extra)
                text = resp.message.content or ""
        except Exception as e:
            err = str(e) or e.__class__.__name__
        em.done.emit(self, text, err)


class Broker(QObject):
    busy_changed = Signal(bool)
    batch_progress = Signal(int, int)    # background jobs done, total in this batch

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self._emitter = _Emitter(self)
        self._emitter.done.connect(self._done)
        self._emitter.chunk.connect(lambda job, text: job.on_chunk and job.on_chunk(text))
        self._emitter.thinking.connect(lambda job, text: job.on_thinking and job.on_thinking(text))
        self._emitter.started.connect(self._started)
        self.jobs = set()
        self.running = None
        self.bg_total = 0
        self.bg_done = 0

    # ---- requests --------------------------------------------------------------------
    def chat(self, model, messages, options, callback, priority=CHATTER, think=None, images=None):
        """callback(text, error) on the UI thread. Returns the Job (job.stop() cancels)."""
        return self._submit(model, messages, options, priority, think, False, callback, None, images)

    def stream(self, model, messages, options, on_chunk, on_done, priority=FOREGROUND, think=None, on_thinking=None):
        """on_chunk(text_so_far) as it arrives, then on_done(text, error). on_thinking(reasoning_so_far)
        receives a thinking model's reasoning while it thinks."""
        return self._submit(model, messages, options, priority, think, True, on_done, on_chunk, None, on_thinking)

    def _submit(self, model, messages, options, priority, think, stream, on_done, on_chunk, images, on_thinking=None):
        job = Job(self, model, messages, options, priority, think, stream, on_done, on_chunk, images, on_thinking)
        self.jobs.add(job)
        if priority <= BACKGROUND:
            if self.bg_done >= self.bg_total:     # a new batch starts
                self.bg_total = self.bg_done = 0
            self.bg_total += 1
            self.batch_progress.emit(self.bg_done, self.bg_total)
        was_busy = len(self.jobs) > 1
        self.pool.start(job, priority)
        if not was_busy:
            self.busy_changed.emit(True)
        return job

    def _started(self, job):
        self.running = job

    def _done(self, job, text, err):
        self.jobs.discard(job)
        if self.running is job:
            self.running = None
        if job.priority <= BACKGROUND:
            self.bg_done += 1
            self.batch_progress.emit(self.bg_done, self.bg_total)
        if not self.jobs:
            self.busy_changed.emit(False)
        if job.on_done:
            job.on_done(text, err)

    # ---- status -------------------------------------------------------------------------
    def busy(self):
        return bool(self.jobs)

    def pending(self, at_least=None):
        """How many jobs are waiting or running (optionally only those at or above a priority)."""
        if at_least is None:
            return len(self.jobs)
        return sum(1 for j in self.jobs if j.priority >= at_least)

    def background_pending(self):
        return sum(1 for j in self.jobs if j.priority <= BACKGROUND)

    def foreground_waiting(self):
        return any(j.priority >= REPLY for j in self.jobs)


_broker = None


def get():
    global _broker
    if _broker is None:
        _broker = Broker()
    return _broker
