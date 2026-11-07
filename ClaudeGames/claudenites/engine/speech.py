"""The townsfolk's voices: llama.cpp, through the Timeline's own language-model engine (claudecore.ai.llm_server -
llama-server from Local Storage/LLM Models, the same one the computers and the code studios use), asked in a thread
so the game never waits on it.

    Speech.available()                         is there an engine and a model? (False with no Timeline, or in tests)
    speech.ask(messages, done)                 done(text or None) is called later, on the Qt side, by the caller's
                                               own means (here: from the thread; the window posts it back)
    speech.model                               the model's id (a folder in LLM Models/models)

The model: a small, quick one suits a line of talk - Qwen3 4B Instruct when it's there, else the Timeline's
'background' choice (Gemma 3 1B), else whatever is smallest."""
import threading

PREFERRED = ("qwen3-4b-instruct", "gemma3-4b", "gemma3-1b")


class Speech:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.model = None
        self.busy = 0
        self.error = ""

    @staticmethod
    def _server():
        try:
            from claudecore.ai import ai_models, llm_server
            return ai_models, llm_server
        except Exception:
            return None, None

    def available(self):
        if not self.enabled:
            return False
        ai_models, llm_server = self._server()
        if llm_server is None:
            return False
        try:
            if not llm_server.ready():
                return False
            ids = [m.id for m in ai_models.installed()]
        except Exception:
            return False
        if not ids:
            return False
        if self.model not in ids:
            self.model = next((m for m in PREFERRED if m in ids), None) or ai_models.model_for("background") or ids[0]
        return True

    def warm(self):
        """Start the engine and load the model in the background (so the first word comes quickly)."""
        if not self.available():
            return
        ai_models, llm_server = self._server()

        def run():
            try:
                llm_server.ensure_started()
                llm_server.load(self.model, wait=True)
            except Exception as exc:
                self.error = str(exc)
        threading.Thread(target=run, daemon=True, name="nites-warm").start()

    def ask(self, messages, done, max_tokens=110):
        if not self.available():
            done(None)
            return
        _ai, llm_server = self._server()
        body = {"model": self.model, "messages": messages, "temperature": 0.85, "top_p": 0.95, "max_tokens": max_tokens,
                "cache_prompt": True, "chat_template_kwargs": {"enable_thinking": False}}
        self.busy += 1

        def run():
            text = None
            try:
                r = llm_server.post("/v1/chat/completions", body, timeout=120)
                text = r["choices"][0]["message"]["content"]
            except Exception as exc:
                self.error = str(exc)
            finally:
                self.busy -= 1
            done(text)
        threading.Thread(target=run, daemon=True, name="nites-speech").start()
