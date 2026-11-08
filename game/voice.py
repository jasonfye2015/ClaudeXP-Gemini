"""Her voice: which language model speaks for her, if any - and asking it, in a thread, so the night never waits.

Three choices (Before the night > Options > Her voice):
    nemomix-unleashed-12b   NemoMix Unleashed 12B - the best of them at playing a part; large (about 7.5 GB)
    gemma3-4b               Gemma 3 4B - lighter (about 2.5 GB), quicker, a little plainer
    none                    no model: she speaks from a script, and he answers by choosing from lines offered
The models run in the Timeline's own engine (llama.cpp, through claudecore.ai - the same the computers use); they live
in Local Storage/LLM Models/models/<name>/. No Timeline, no engine or no such model, and it's as if "none" were chosen.

    voice = Voice(choice)
    voice.status(model)       -> "ready", "missing" (no such model), "no engine", "no timeline"
    voice.speaking()          -> the model that will speak, or None (the script)
    voice.ask(messages, done) done(text or None), called from the thread (the caller posts it back to Qt)
"""
import threading

CHOICES = (
    ("nemomix-unleashed-12b", "NemoMix Unleashed 12B", "The best at playing her. Large: about 7.5 GB, and a graphics "
     "card with 8 GB or more to run well."),
    ("gemma3-4b", "Gemma 3 4B", "Lighter and quicker: about 2.5 GB. A little plainer in her mouth."),
    ("none", "None", "No model. She speaks from a script, and you answer by choosing from the lines offered - no "
     "typing."),
)
HELP = {
    "nemomix-unleashed-12b": {"page": "https://huggingface.co/bartowski/NemoMix-Unleashed-12B-GGUF",
                              "file": "NemoMix-Unleashed-12B-Q4_K_M.gguf", "size": "about 7.5 GB",
                              "info": '{\n  "title": "NemoMix Unleashed 12B",\n  "chat_template": "chatml",\n'
                                      '  "stop": ["<|im_end|>", "<|im_start|>"]\n}'},
    "gemma3-4b": {"page": "https://huggingface.co/ggml-org/gemma-3-4b-it-GGUF", "file": "gemma-3-4b-it-Q4_K_M.gguf",
                  "size": "about 2.5 GB", "info": None},
}
ENGINE_PAGE = "https://github.com/ggml-org/llama.cpp/releases"


def _ai():
    try:
        from claudecore.ai import ai_models, llm_server
        return ai_models, llm_server
    except Exception:
        return None, None


def models_folder():
    """Where the models go (Local Storage/LLM Models/models), or None outside the Timeline."""
    ai_models, _s = _ai()
    try:
        return ai_models.models_root() if ai_models is not None else None
    except Exception:
        return None


def installed_ids():
    ai_models, _s = _ai()
    if ai_models is None:
        return set()
    try:
        return {m.id for m in ai_models.installed()}
    except Exception:
        return set()


def engine_ok():
    _m, llm_server = _ai()
    try:
        return llm_server is not None and llm_server.find_engine() is not None
    except Exception:
        return False


def best_choice(installed):
    """With nothing chosen yet: the best that's there."""
    for cid, _name, _what in CHOICES[:2]:
        if cid in installed:
            return cid
    return "none"


class Voice:
    def __init__(self, choice):
        self.choice = choice
        self.error = ""
        self.busy = 0

    def status(self, model, installed=None, engine=None):
        if model == "none":
            return "ready"
        ai_models, _s = _ai()
        if ai_models is None and installed is None:
            return "no timeline"
        if not (engine_ok() if engine is None else engine):
            return "no engine"
        have = installed_ids() if installed is None else installed
        return "ready" if model in have else "missing"

    def speaking(self):
        if self.choice == "none" or self.status(self.choice) != "ready":
            return None
        return self.choice

    def warm(self):
        """Start the engine and load her model in the background, so her first words come quickly."""
        model = self.speaking()
        if model is None:
            return
        _m, llm_server = _ai()

        def run():
            try:
                llm_server.ensure_started()
                llm_server.load(model, wait=True)
            except Exception as exc:
                self.error = str(exc)
        threading.Thread(target=run, daemon=True, name="oak-voice-warm").start()

    def ask(self, messages, done, max_tokens=160, temperature=0.9):
        model = self.speaking()
        if model is None:
            done(None)
            return
        _m, llm_server = _ai()
        body = {"model": model, "messages": messages, "temperature": temperature, "top_p": 0.95, "min_p": 0.05,
                "max_tokens": max_tokens, "cache_prompt": True, "chat_template_kwargs": {"enable_thinking": False}}
        self.busy += 1

        def run():
            text = None
            try:
                r = llm_server.post("/v1/chat/completions", body, timeout=180)
                text = r["choices"][0]["message"]["content"]
            except Exception as exc:
                self.error = str(exc)
            finally:
                self.busy -= 1
            done(text)
        threading.Thread(target=run, daemon=True, name="oak-voice").start()
