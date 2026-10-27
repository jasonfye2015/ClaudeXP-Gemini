"""Running the model: which Kithylin models there are, starting llama-server for the chosen one, and streaming
replies from it. Everything the model engine does is reported through `status` (the purple system messages).

Models come from kithylinai/Models/<name>/*.gguf first, then the Timeline's Local Storage/LLM Models/models.
Inside the Timeline a Local Storage model is run by the Timeline's own engine router (it shares the graphics card
with the residents properly); a Kithylin model, or anything standalone, gets a llama-server of its own here."""
import atexit
import json
import os
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request

from PySide6.QtCore import QObject, QThread, Signal

from .paths import DATA, ENGINE, MODELS, SERVER, TIMELINE_ENGINES, TIMELINE_MODELS, hosted

START_TIMEOUT = 240


class ModelEntry:
    def __init__(self, key, title, path, where, info=None):
        self.key, self.title, self.path, self.where, self.info = key, title, path, where, info or {}

    @property
    def label(self):
        return f"{self.title}   ({self.where})"


def _info(folder):
    try:
        return json.loads((folder / "info.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def memory_limit():
    """On a Mac (one pool of memory for everything): the biggest model worth offering, half the memory - an 8 GB
    MacBook runs the 4B Kithylins, not the 12B ones. Elsewhere None."""
    import sys
    if sys.platform != "darwin":
        return None
    try:
        return os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") // 2
    except (ValueError, OSError, AttributeError):
        return None


def _fits(entry):
    limit = memory_limit()
    if limit is None:
        return True
    base = lora_base(entry)
    size = entry.path.stat().st_size + (base.stat().st_size if base is not None else 0)
    return size <= limit


def models():
    """Every model Kithylin AI can run on this computer, Kithylin's own first."""
    return [m for m in _all_models() if _fits(m)]


def _all_models():
    out = []
    if MODELS.is_dir():
        for folder in sorted(MODELS.iterdir()):
            files = sorted(f for f in folder.glob("*.gguf") if not f.name.lower().startswith("mmproj")) \
                if folder.is_dir() else ([folder] if folder.suffix.lower() == ".gguf" else [])
            for f in files:
                info = _info(folder) if folder.is_dir() else {}
                if info.get("lora_base") and f.name == info.get("lora_base_file"):
                    continue                        # the base an add-on goes on, copied in beside it
                out.append(ModelEntry(f"own:{f}", info.get("title") or folder.stem, f, "Kithylin AI", info))
    if TIMELINE_MODELS.is_dir():
        for folder in sorted(TIMELINE_MODELS.iterdir()):
            if not folder.is_dir():
                continue
            info = _info(folder)
            if info.get("embedding"):
                continue
            files = sorted(f for f in folder.glob("*.gguf") if not f.name.lower().startswith(("mmproj", "mtp")))
            if files:
                out.append(ModelEntry(f"timeline:{folder.name}", info.get("title") or folder.name, files[0],
                                      "Timeline", info))
    return out


def find(key):
    for m in models():
        if m.key == key:
            return m
    if key.startswith("own:") and os.path.exists(key[4:]):          # a file picked with Browse
        from pathlib import Path
        p = Path(key[4:])
        return ModelEntry(key, p.stem, p, "file")
    return None


def lora_base(model):
    """For an add-on model (info.json "lora_base"): the base .gguf it goes on - a copy in its own folder (when the
    program has been lifted out of the Timeline), else the Timeline's models folder. None if it isn't one, or the
    base can't be found."""
    if not model.info.get("lora_base"):
        return None
    name = model.info.get("lora_base_file") or ""
    for folder in (model.path.parent, TIMELINE_MODELS / model.info["lora_base"]):
        if name and (folder / name).exists():
            return folder / name
    folder = TIMELINE_MODELS / model.info["lora_base"]
    found = sorted(f for f in folder.glob("*.gguf") if not f.name.lower().startswith("mmproj")) if folder.is_dir() else []
    return found[0] if found else None


def engine_exe(choice):
    """llama-server.exe for the chosen engine ("auto", "vulkan", "cuda" or "cpu"), or None."""
    order = {"auto": ["vulkan", "cuda", "macos"], "cpu": ["vulkan", "cuda", "macos"]}.get(choice, [choice])
    dirs = [ENGINE] + [TIMELINE_ENGINES[k] for k in order if k in TIMELINE_ENGINES]
    for d in dirs:
        exe = d / SERVER
        if exe.exists():
            return exe
    return None


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _Server:
    """A llama-server of our own for one model file."""

    def __init__(self):
        self.proc = None
        self.port = None
        self.model = None
        self.settings = None

    def url(self):
        return f"http://127.0.0.1:{self.port}"

    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def healthy(self):
        try:
            with urllib.request.urlopen(self.url() + "/health", timeout=2) as r:
                return r.status == 200
        except Exception:
            return False

    def start(self, model, engine_choice, context, status):
        exe = engine_exe(engine_choice)
        if exe is None:
            raise RuntimeError("No llama-server.exe found: put a llama.cpp build in kithylinai\\Engine\\ (or keep the "
                               "Timeline's in Local Storage\\LLM Models\\llama.cpp).")
        want = (str(model.path), engine_choice, int(context))
        if self.running() and self.settings == want and self.healthy():
            return
        self.stop()
        self.port = _free_port()
        base = lora_base(model)
        if model.info.get("lora_base") and base is None:
            raise RuntimeError(f"This model is an add-on for {model.info.get('lora_base_file') or model.info['lora_base']}, "
                               "which isn't here: put that .gguf in its folder or in the Timeline's models.")
        model_args = ["-m", str(base), "--lora", str(model.path)] if base else ["-m", str(model.path)]
        args = [str(exe), "--host", "127.0.0.1", "--port", str(self.port)] + model_args + [
                "-c", str(int(context)), "--jinja", "--parallel", "1", "--flash-attn", "on",
                "--cache-type-k", "q8_0", "--cache-type-v", "q8_0"]
        if engine_choice == "cpu":
            args += ["--device", "none", "-ngl", "0"]      # the graphics card isn't touched at all
        if model.info.get("chat_template"):
            args += ["--chat-template", model.info["chat_template"]]
        DATA.mkdir(parents=True, exist_ok=True)
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        status(f"Starting the engine ({exe.parent.name} build) for {model.path.name}...")
        with open(DATA / "llama-server.log", "w", encoding="utf-8", errors="replace") as log:
            self.proc = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                         cwd=str(exe.parent), creationflags=flags)
        self.model, self.settings = model, want
        deadline = time.monotonic() + START_TIMEOUT
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                self.proc = None
                raise RuntimeError("The engine stopped while loading the model (see Data\\llama-server.log).")
            if self.healthy():
                return
            time.sleep(0.25)
        self.stop()
        raise RuntimeError("The engine took too long to load the model.")

    def stop(self):
        if self.proc is not None:
            try:
                self.proc.terminate()
                self.proc.wait(5)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
        self.proc = None
        self.model = None
        self.settings = None


_server = _Server()
atexit.register(_server.stop)


class _Loader(QThread):
    finished_with = Signal(str, float)      # error ("" if fine), seconds

    def __init__(self, model, engine_choice, context, status_cb, shared=True):
        super().__init__()
        self.model, self.engine_choice, self.context, self.status_cb = model, engine_choice, context, status_cb
        self.shared = shared

    def run(self):
        t = time.monotonic()
        try:
            if self.shared and self.model.key.startswith("timeline:") and hosted():
                from claudecore.ai import llm_server
                llm_server.ensure_started()
                llm_server.load(self.model.key.split(":", 1)[1], wait=True)
            else:
                _server.start(self.model, self.engine_choice, self.context, self.status_cb)
            self.finished_with.emit("", time.monotonic() - t)
        except Exception as e:
            self.finished_with.emit(str(e) or e.__class__.__name__, time.monotonic() - t)


class _Streamer(QThread):
    chunk = Signal(str)
    thinking = Signal(str)          # a thinking model's reasoning so far (before its answer)
    done = Signal(str, str)

    def __init__(self, url, body):
        super().__init__()
        self.url, self.body = url, body
        self._stop = False
        self._resp = None

    def stop(self):
        self._stop = True
        try:
            if self._resp is not None:
                self._resp.close()
        except Exception:
            pass

    def run(self):
        text = reasoning = ""
        try:
            req = urllib.request.Request(self.url + "/v1/chat/completions", data=json.dumps(self.body).encode(),
                                         headers={"Content-Type": "application/json"})
            self._resp = urllib.request.urlopen(req, timeout=600)
            for raw in self._resp:
                if self._stop:
                    break
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    delta = json.loads(payload)["choices"][0].get("delta") or {}
                except (ValueError, KeyError, IndexError):
                    continue
                piece = delta.get("content")
                if piece:
                    text += piece
                    self.chunk.emit(text)
                thought = delta.get("reasoning_content")
                if thought:
                    reasoning += thought
                    self.thinking.emit(reasoning)
            self.done.emit(text, "stopped" if self._stop else "")
        except urllib.error.HTTPError as e:
            try:
                detail = json.loads(e.read().decode("utf-8", "replace")).get("error", {}).get("message", "")
            except Exception:
                detail = ""
            self.done.emit(text, "stopped" if self._stop else f"HTTP {e.code} {detail}".strip())
        except Exception as e:
            self.done.emit(text, "stopped" if self._stop else (str(e) or e.__class__.__name__))


class Engine(QObject):
    status = Signal(str)            # a line for the chat, in purple
    loaded = Signal(bool)           # is a model ready?
    chunk = Signal(str)             # the reply so far
    thinking = Signal(str)          # a thinking model's reasoning so far
    done = Signal(str, str)         # the reply, error

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = None
        self.ready = False
        self.shared = True              # a Timeline model on the Timeline's shared engine (False: one of our own)
        self._loader = None
        self._streamer = None
        self._lock = threading.Lock()

    # ---- loading -----------------------------------------------------------------------------------------------
    def load(self, model, engine_choice="auto", context=8192, shared=True):
        """shared=False: even a Timeline model gets a llama-server of our own (its own context size), instead of the
        Timeline's shared engine."""
        if self._loader is not None and self._loader.isRunning():
            self.status.emit("Still loading the last model - one moment.")
            return
        self.stop()
        if not self.shared and shared:
            _server.stop()                      # (our own engine isn't needed any more)
        self.model, self.ready, self.shared = model, False, shared
        self.loaded.emit(False)
        base = lora_base(model)
        if base is not None:
            self.status.emit(f"Now loading {model.title}: {base.name} ({base.stat().st_size / 2**30:.1f} GB) with the "
                             f"add-on {model.path.name} ({model.path.stat().st_size / 2**20:.0f} MB)...")
        else:
            self.status.emit(f"Now loading {model.title} ({model.path.name}, {model.path.stat().st_size / 2**30:.1f} GB)...")
        self._loader = _Loader(model, engine_choice, context, lambda s: self.status.emit(s), shared)
        self._loader.finished_with.connect(self._loaded)
        self._loader.start()

    def _loaded(self, err, seconds):
        if err:
            self.model, self.ready = None, False
            self.status.emit(f"Couldn't load the model: {err}")
        else:
            self.ready = True
            self.status.emit(f"{self.model.title} is loaded and ready ({seconds:.0f}s).")
        self.loaded.emit(self.ready)

    def unload(self):
        self.stop()
        if self.model is not None:
            if self.shared and self.model.key.startswith("timeline:") and hosted():
                try:
                    from claudecore.ai import llm_server
                    llm_server.unload(self.model.key.split(":", 1)[1])
                except Exception:
                    pass
            else:
                _server.stop()
            self.status.emit(f"{self.model.title} unloaded.")
        self.model, self.ready = None, False
        self.loaded.emit(False)

    # ---- talking ------------------------------------------------------------------------------------------------
    def chat(self, messages, temperature=0.9, max_tokens=600, extra=None):
        """extra: more for llama-server's request (e.g. {"chat_template_kwargs": {"enable_thinking": False}})."""
        if not self.ready or self.model is None:
            self.done.emit("", "no model loaded")
            return
        self.stop()
        if self.shared and self.model.key.startswith("timeline:") and hosted():
            from claudecore.ai import llm_server
            url, name = llm_server.ensure_started(), self.model.key.split(":", 1)[1]
        else:
            url, name = _server.url(), self.model.path.stem
        body = {"model": name, "messages": messages, "stream": True, "temperature": float(temperature),
                "max_tokens": int(max_tokens), "cache_prompt": True}
        if self.model.info.get("stop"):
            body["stop"] = list(self.model.info["stop"])
        body.update(extra or {})
        self._streamer = _Streamer(url, body)
        self._streamer.chunk.connect(self.chunk)
        self._streamer.thinking.connect(self.thinking)
        self._streamer.done.connect(self._done)
        self._streamer.start()

    def _done(self, text, err):
        self._streamer = None
        self.done.emit(text, err)

    def busy(self):
        return self._streamer is not None and self._streamer.isRunning()

    def stop(self):
        if self._streamer is not None:
            self._streamer.stop()
            self._streamer.wait(3000)
            self._streamer = None

    def shutdown(self):
        self.stop()
        _server.stop()
