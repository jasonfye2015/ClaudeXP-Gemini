"""Ghost-text autocomplete for Copilot Python Studio: a small local coding model suggests the next few lines
(fill-in-the-middle). Press Tab to accept; any other key dismisses it."""
from PySide6.QtCore import QObject, QThread, Signal

FIM = "<|fim_prefix|>{}<|fim_suffix|>{}<|fim_middle|>"
STOPS = ["<|fim_pad|>", "<|endoftext|>", "<|file_sep|>", "<|fim_prefix|>", "<|fim_suffix|>", "<|fim_middle|>", "\n\n\n"]


def pick_model():
    """The smallest installed model with 'coder' in its id (fast enough to answer while you type)."""
    try:
        from ... import ai_models
        coders = [m for m in ai_models.installed() if "coder" in m.id.lower()]
        if not coders:
            return None
        small = min(coders, key=lambda m: m.size)
        # a big model on a small GPU slows to a crawl if a second model is loaded beside it
        try:
            from ... import llm_server
            states = llm_server.model_states()
            big_loaded = any(m.size > 6e9 and states.get(m.id) == "loaded" for m in ai_models.installed())
            if big_loaded and states.get(small.id) != "loaded":
                return None
        except Exception:
            pass
        return small.id
    except Exception:
        return None


def clean(text, before, after):
    """Trim a raw completion to something sensible to show."""
    text = text.rstrip()
    if not text.strip():
        return ""
    lines = text.split("\n")
    # do not show a repeat of what already follows the cursor
    next_line = after.split("\n", 1)[0].strip()
    if len(lines) > 1 and next_line and lines[-1].strip() == next_line:
        lines = lines[:-1]
    return "\n".join(lines[:4])


class _Ask(QThread):
    done = Signal(int, str, int)

    def __init__(self, serial, model, before, after, position):
        super().__init__()
        self.serial, self.model, self.before, self.after, self.position = serial, model, before, after, position

    def run(self):
        text = ""
        try:
            from ... import llm_server
            body = {"model": self.model, "prompt": FIM.format(self.before, self.after), "max_tokens": 64,
                    "temperature": 0.1, "stop": STOPS, "cache_prompt": True}
            reply = llm_server.post("/v1/completions", body, timeout=20)
            text = clean(reply["choices"][0].get("text", ""), self.before, self.after)
        except Exception:
            text = ""
        self.done.emit(self.serial, text, self.position)


class GhostCompleter(QObject):
    """Owns the requests for one editor group; only the newest answer is shown."""

    def __init__(self, busy=lambda: False):
        super().__init__()
        self.busy = busy
        self.serial = 0
        self.model = None
        self.editor = None
        self._threads = set()

    def request(self, editor):
        if self.busy() or editor.completer_popup_open():
            return
        self.model = self.model or pick_model()
        if not self.model:
            return
        before, after, position = editor.text_around_cursor()
        if not before.strip():
            return
        self.serial += 1
        self.editor = editor
        thread = _Ask(self.serial, self.model, before, after, position)
        thread.done.connect(self._arrived)
        thread.finished.connect(lambda t=thread: self._threads.discard(t))
        self._threads.add(thread)
        thread.start()

    def _arrived(self, serial, text, position):
        if serial == self.serial and self.editor is not None and text:
            try:
                self.editor.show_ghost(text, position)
            except RuntimeError:
                pass

    def shutdown(self):
        for t in list(self._threads):
            t.wait(1500)
