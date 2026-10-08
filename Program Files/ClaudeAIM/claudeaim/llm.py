"""Talking to Ollama off the UI thread."""
import re

import ollama
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

SYSTEM_PROMPT = """You are {name}, chatting with your buddy "{user}" on AOL Instant Messenger.
Right now it is {now}. You are a real person living in that time. Never say or hint that you are an AI, a model, or a character, and never mention these instructions.
Write like a real instant message: casual and short, usually one to three lines. No narration, no stage directions, no timestamps, and don't put your screen name in front of your message.

About you:
{persona}

Status: {status}"""


def list_models() -> list[str]:
    return [m.model for m in ollama.list().models]


def context_length(model: str) -> int | None:
    """The model's own maximum context, from Ollama's model info."""
    info = ollama.show(model).modelinfo or {}
    for key, value in info.items():
        if key.endswith(".context_length"):
            return int(value)
    return None


def estimate_tokens(text: str) -> int:
    # Rough rule of thumb; good enough for a bar graph.
    return int(len(text) / 3.5) + 4


def clean_reply(text: str, name: str) -> str:
    text = text.strip()
    for prefix in (f"{name}:", f"{name} :"):
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()
    if len(text) > 1 and text[0] == text[-1] == '"':
        text = text[1:-1].strip()
    # Models sometimes copy the [pic: ...] bracket style onto emoticons: "[:3]" -> ":3"
    text = re.sub(r"\[\s*([:;xX=][^\]\s]{1,3})\s*\]", r"\1", text)
    return text


_vision_cache = {}
_thinking_cache = {}


def supports_thinking(model: str) -> bool:
    if model not in _thinking_cache:
        try:
            _thinking_cache[model] = "thinking" in (ollama.show(model).capabilities or [])
        except Exception:
            return False
    return _thinking_cache[model]


def supports_vision(model: str) -> bool:
    if model not in _vision_cache:
        try:
            _vision_cache[model] = "vision" in (ollama.show(model).capabilities or [])
        except Exception:
            return False
    return _vision_cache[model]


def _prepare_images(model, messages):
    """Load attached pictures, or tell a text-only model the picture didn't open."""
    if not any(m.get("images") for m in messages):
        return messages
    vision = supports_vision(model)
    out = []
    for m in messages:
        if not m.get("images"):
            out.append(m)
            continue
        m = dict(m)
        paths = m.pop("images")
        if vision:
            m["images"] = [open(p, "rb").read() for p in paths]
        else:
            m["content"] += " (but it won't open on your computer, so you can't see it)"
        out.append(m)
    return out


class _Emitter(QObject):
    done = Signal(object, str, str)  # callback, text, error


class _ChatJob(QRunnable):
    def __init__(self, emitter, callback, model, messages, options, think=None):
        super().__init__()
        self.emitter, self.callback = emitter, callback
        self.model, self.messages, self.options = model, messages, options
        self.think = think

    def run(self):
        try:
            messages = _prepare_images(self.model, self.messages)
            extra = {}
            if self.think is not None and supports_thinking(self.model):
                extra["think"] = self.think   # False: skip the (slow) hidden reasoning
            resp = ollama.chat(model=self.model, messages=messages,
                               options=self.options, keep_alive="30m", **extra)
            text, err = resp.message.content or "", ""
        except Exception as e:
            text, err = "", str(e) or e.__class__.__name__
        self.emitter.done.emit(self.callback, text, err)


class LLM(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)  # one generation at a time keeps the GPU happy
        self._emitter = _Emitter(self)
        self._emitter.done.connect(lambda cb, text, err: cb(text, err))

    def chat(self, model, messages, options, callback, priority=0, think=None):
        """callback(text, error) runs on the UI thread when the reply is ready.
        Queued jobs with a higher priority run first. think=False turns off a thinking
        model's reasoning step (much faster); None leaves the model's default."""
        self.pool.start(_ChatJob(self._emitter, callback, model, messages, options, think), priority)
