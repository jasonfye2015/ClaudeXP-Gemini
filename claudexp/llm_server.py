"""ClaudeXP's own language-model engine: llama.cpp's llama-server in router mode, run from Local Storage/LLM Models.

  Local Storage/LLM Models/
    llama.cpp/vulkan/llama-server.exe    the engine (any GPU via Vulkan, else the CPU)
    llama.cpp/cuda/llama-server.exe      optional: NVIDIA's CUDA build (chosen in Control Panel > AI Models)
    models/<name>/                       one folder per model: its .gguf, an optional mmproj-*.gguf (pictures)
                                         and an optional info.json (see ai_models.py)

One router server runs quietly on 127.0.0.1. ClaudeXP writes its model list (data/llm_models.ini) from the
models folder; the router loads a model the first time a request names it, keeps up to 'max_loaded' of them in
memory and unloads the least recently used. The whole family of processes lives in a Windows job object that closes
with ClaudeXP, so nothing is left holding the graphics card - even after a crash. Without the engine or any model,
status() says what's missing and every request fails at once with a plain message."""
import json
import os
import socket
import subprocess
import threading
import time
import urllib.request

from .paths import DATA

MODELS_DIR_NAME = "LLM Models"
DEFAULT_CTX = 16384
START_TIMEOUT = 60             # seconds for the router itself to come up (models load on demand)
LOAD_TIMEOUT = 300             # seconds a request may wait while a big model loads

_lock = threading.RLock()
_proc = None
_port = None
_settings = None               # the settings the router was started with
_error = ""
_job = None


def models_dir():
    from .explorer.vfs import local_storage
    return local_storage() / MODELS_DIR_NAME


def engines():
    """{'vulkan': exe, 'cuda': exe, ...} for the builds that are installed."""
    base = models_dir() / "llama.cpp"
    return {f: base / f / "llama-server.exe" for f in ("vulkan", "cuda", "cpu")
            if (base / f / "llama-server.exe").exists()}


def find_engine():
    """The chosen build (AI Models > Engine; the old engine.txt still counts), else Vulkan - measured faster than
    CUDA on a GTX 1080 Ti - else whichever build is there."""
    from . import ai_models
    have = engines()
    chosen = ai_models.config().get("engine") or ""
    if not chosen:
        try:
            chosen = (models_dir() / "engine.txt").read_text(encoding="utf-8").strip().lower()
        except OSError:
            chosen = ""
    for flavour in ([chosen] if chosen else []) + ["vulkan", "cuda", "cpu"]:
        if flavour in have:
            return have[flavour]
    return None


def status():
    """'' when models can run, otherwise what's missing (for messages and the tray)."""
    from . import ai_models
    if find_engine() is None:
        return ("The language model engine (llama.cpp) isn't installed. Put it in "
                f"E:\\{MODELS_DIR_NAME}\\llama.cpp\\vulkan.")
    if not ai_models.installed():
        return f"No language model is installed. Put a model's folder in E:\\{MODELS_DIR_NAME}\\models."
    return _error


def available():
    return status() == ""


# ---- running the router ---------------------------------------------------------------------------------------

def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _kill_with_us(proc):
    """Put the server in a job object that Windows closes (killing it) when ClaudeXP's process ends."""
    global _job
    if os.name != "nt":
        return
    try:
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateJobObjectW.restype = wintypes.HANDLE
        k32.OpenProcess.restype = wintypes.HANDLE
        if _job is None:
            _job = k32.CreateJobObjectW(None, None)

            class BASIC(ctypes.Structure):
                _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                            ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                            ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                            ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                            ("SchedulingClass", wintypes.DWORD)]

            class IO(ctypes.Structure):
                _fields_ = [(n, ctypes.c_uint64) for n in ("r", "w", "o", "rb", "wb", "ob")]

            class EXTENDED(ctypes.Structure):
                _fields_ = [("Basic", BASIC), ("Io", IO), ("ProcessMemoryLimit", ctypes.c_size_t),
                            ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                            ("PeakJobMemoryUsed", ctypes.c_size_t)]
            info = EXTENDED()
            info.Basic.LimitFlags = 0x2000                       # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            k32.SetInformationJobObject(wintypes.HANDLE(_job), 9, ctypes.byref(info), ctypes.sizeof(info))
        handle = k32.OpenProcess(0x0101, False, proc.pid)        # PROCESS_SET_QUOTA | PROCESS_TERMINATE
        k32.AssignProcessToJobObject(wintypes.HANDLE(_job), wintypes.HANDLE(handle))
        k32.CloseHandle(wintypes.HANDLE(handle))
    except Exception:
        pass


def _get(path, timeout=3):
    with urllib.request.urlopen(f"http://127.0.0.1:{_port}{path}", timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _healthy():
    try:
        _get("/models", 2)
        return True
    except Exception:
        return False


def _wanted():
    """What the router should be started with, from AI Models' settings and the models folder."""
    from . import ai_models
    cfg = ai_models.config()
    return {"engine": str(find_engine()), "max_loaded": int(cfg["max_loaded"]), "context": int(cfg["context"]),
            "idle": int(cfg["idle_minutes"]), "compact": bool(cfg.get("compact_cache", True)),
            "models": [(m.id, str(m.path), str(m.mmproj or ""), str(m.info.get("chat_template") or ""))
                       for m in ai_models.installed()]}


def _write_presets(settings):
    lines = []
    for model_id, path, mmproj, template in settings["models"]:
        lines += [f"[{model_id}]", f"model = {path}"]
        if mmproj:
            lines.append(f"mmproj = {mmproj}")
        if template:                                # a model whose file has no chat template (info.json)
            lines.append(f"chat-template = {template}")
        # no n-gpu-layers: llama.cpp's --fit (on by default) puts as much on the GPU as the free memory allows,
        # so a second model still loads (partly on the CPU) when the first is using most of the card
        lines += [f"ctx-size = {settings['context']}", "parallel = 1", "jinja = true"]
        if settings.get("compact", True):           # an 8-bit context cache: half the memory, so two models fit
            lines += ["flash-attn = on", "cache-type-k = q8_0", "cache-type-v = q8_0"]
        lines.append("")
    path = DATA / "llm_models.ini"
    DATA.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def ensure_started():
    """Start the router (or restart it if the models or settings changed). Returns the base URL; raises
    RuntimeError with a plain message when it can't run."""
    global _proc, _port, _settings, _error
    with _lock:
        if find_engine() is None or not _wanted()["models"]:
            raise RuntimeError(status())
        want = _wanted()
        if _proc is not None and _proc.poll() is None and want == _settings:
            return f"http://127.0.0.1:{_port}"
        stop()
        _error = ""
        _port, _settings = _free_port(), want
        args = [want["engine"], "--host", "127.0.0.1", "--port", str(_port),
                "--models-preset", str(_write_presets(want)), "--models-max", str(max(1, want["max_loaded"]))]
        if want["idle"] > 0:
            args += ["--sleep-idle-seconds", str(want["idle"] * 60)]
        log = open(DATA / "llama-server.log", "w", encoding="utf-8", errors="replace")
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        _proc = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                 cwd=str(find_engine().parent), creationflags=flags)
        _kill_with_us(_proc)
        deadline = time.monotonic() + START_TIMEOUT
        while time.monotonic() < deadline:
            if _proc.poll() is not None:
                _error = "The language model engine stopped while starting (see data\\llama-server.log)."
                _proc = None
                raise RuntimeError(_error)
            if _healthy():
                return f"http://127.0.0.1:{_port}"
            time.sleep(0.25)
        stop()
        _error = "The language model engine took too long to start."
        raise RuntimeError(_error)


def restart():
    stop()
    return ensure_started()


def running():
    return _proc is not None and _proc.poll() is None


def model_states():
    """{model id: 'loaded' | 'loading' | 'unloaded'} from the router (empty when it isn't running)."""
    if not running():
        return {}
    try:
        return {m["id"]: (m.get("status") or {}).get("value", "") for m in _get("/models").get("data", [])}
    except Exception:
        return {}


def load(model_id, wait=False):
    """Load a model now (the AI Models 'Load' button, and warming the conversation model at log on)."""
    base = ensure_started()
    req = urllib.request.Request(base + "/models/load", data=json.dumps({"model": model_id}).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10).close()
    except Exception:
        pass
    deadline = time.monotonic() + (LOAD_TIMEOUT if wait else 0)
    while wait and time.monotonic() < deadline:
        if model_states().get(model_id) == "loaded":
            return True
        time.sleep(0.5)
    return model_states().get(model_id) == "loaded"


def unload(model_id):
    if not running():
        return
    req = urllib.request.Request(f"http://127.0.0.1:{_port}/models/unload",
                                 data=json.dumps({"model": model_id}).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10).close()
    except Exception:
        pass


def start_in_background():
    """Start the router and load the conversation model ahead of time (at log on) so the first reply is quick."""
    if available():
        from . import ai_models

        def warm():
            ensure_started()
            load(ai_models.model_for("conversation"))
        threading.Thread(target=lambda: _quiet(warm), daemon=True, name="llm-start").start()


def _quiet(fn):
    try:
        fn()
    except Exception:
        pass


def stop():
    global _proc
    with _lock:
        if _proc is not None and _proc.poll() is None:
            _proc.terminate()
            try:
                _proc.wait(5)
            except Exception:
                _proc.kill()
        _proc = None


def post(path, body, stream=False, timeout=LOAD_TIMEOUT + 300):
    """POST JSON to the router; returns the open response (for streaming) or the parsed JSON."""
    base = ensure_started()
    req = urllib.request.Request(base + path, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    if stream:
        return resp
    with resp:
        return json.loads(resp.read().decode("utf-8"))


def train_context(model_id):
    """A model's own maximum context, from its router entry (or a safe guess)."""
    try:
        ensure_started()
        for m in _get("/models").get("data", []):
            if m["id"] == model_id:
                meta = m.get("meta") or {}
                if meta.get("n_ctx_train"):
                    return int(meta["n_ctx_train"])
    except Exception:
        pass
    return 131072 if model_id.startswith(("gemma3", "gemma4")) else 32768


def devices():
    """The graphics devices the engine can use, e.g. ['Vulkan0: NVIDIA GeForce GTX 1080 Ti (11320 MiB, ...)']."""
    exe = find_engine()
    if exe is None:
        return []
    try:
        out = subprocess.run([str(exe), "--list-devices"], capture_output=True, text=True, timeout=30,
                             cwd=str(exe.parent), creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        return [line.strip() for line in (out.stdout + out.stderr).splitlines() if ":" in line and "(" in line
                and not line.strip().lower().startswith("available")]
    except Exception:
        return []


def at_logon(desktop):
    """Load the model now (so the first reply is quick), or put up a warning by the clock if it can't run."""
    from . import ai_models
    ai_models.sync_aim()                       # ClaudeAIM's model settings follow Control Panel > AI Models
    if available():
        start_in_background()
        return
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QStyle, QSystemTrayIcon
    from .tray import TrayIcon
    old = getattr(desktop, "_llm_tray", None)
    if old is not None:
        old.hide()
    tray = TrayIcon(desktop, QApplication.style().standardIcon(QStyle.SP_MessageBoxWarning))
    tray.setToolTip("Language model missing - your buddies can't talk")
    desktop._llm_tray = tray

    def explain(*_):
        from .explorer.dialogs import msgbox
        msgbox(desktop, "Language model", status() + "\n\nEverything else in ClaudeXP works as usual. Your "
               "buddies, IRC, the MUCK and ClaudeAI need the model to talk; once it's in place, log off and on "
               "again.", "warning")
    tray.activated.connect(lambda reason: explain() if reason in (QSystemTrayIcon.Trigger,
                                                                    QSystemTrayIcon.DoubleClick) else None)
    tray.show()
    QTimer.singleShot(1500, lambda: tray.showMessage(
        "Your buddies can't talk", "ClaudeXP's language model isn't installed (E:\\LLM Models). Everything else "
        "works. Click here for details."))
    tray.messageClicked.connect(explain)


