"""ClaudeXP's own language-model engine: llama.cpp's llama-server, run from Local Storage/LLM Models.

  Local Storage/LLM Models/
    llama.cpp/vulkan/llama-server.exe    the engine (any GPU via Vulkan, else the CPU)
    llama.cpp/cuda/llama-server.exe      optional: NVIDIA's CUDA build, used when engine.txt says 'cuda'
    engine.txt                           optional: 'vulkan' (the default) or 'cuda'
    <model>.gguf                         the model (gemma-3-4b-it-Q4_K_M.gguf)
    mmproj-<...>.gguf                    optional: its picture 'projector', so the model can see images

The server is started quietly on 127.0.0.1 the first time it's needed (or at log on), with a context as large as
any program asks for, and it dies with ClaudeXP - even if ClaudeXP crashes - because it lives in a Windows job
object that closes with us. Nothing here needs Ollama or the Internet. Everything copes with the engine or the
model being missing: status() says what's wrong and requests fail at once with a plain message."""
import json
import os
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

from .paths import DATA

MODELS_DIR_NAME = "LLM Models"
DEFAULT_CTX = 16384
START_TIMEOUT = 180            # seconds to load a model (slow disks, CPU-only PCs)

_lock = threading.RLock()
_proc = None
_port = None
_ctx = 0
_error = ""
_job = None


def models_dir():
    from .explorer.vfs import local_storage
    return local_storage() / MODELS_DIR_NAME


def find_engine():
    """llama-server.exe: the build named in LLM Models/engine.txt ('vulkan' or 'cuda'), else Vulkan - measured
    faster than CUDA on a GTX 1080 Ti - else whichever build is there."""
    base = models_dir() / "llama.cpp"
    try:
        chosen = (models_dir() / "engine.txt").read_text(encoding="utf-8").strip().lower()
    except OSError:
        chosen = ""
    order = ([chosen] if chosen in ("vulkan", "cuda", "cpu") else []) + ["vulkan", "cuda", "cpu"]
    for flavour in order:
        exe = base / flavour / "llama-server.exe"
        if exe.exists():
            return exe
    return None


def find_model():
    d = models_dir()
    if not d.is_dir():
        return None
    models = [f for f in sorted(d.glob("*.gguf")) if not f.name.lower().startswith("mmproj")]
    return models[0] if models else None


def find_projector():
    d = models_dir()
    return next(iter(sorted(d.glob("mmproj*.gguf"))), None) if d.is_dir() else None


def model_name():
    """'gemma-3-4b-it-Q4_K_M.gguf' -> 'gemma3:4b' (the name the programs show and ask for)."""
    import re
    m = find_model()
    if m is None:
        return ""
    hit = re.match(r"([a-z]+)-?(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?[bm])", m.stem.lower())
    return f"{hit.group(1)}{hit.group(2)}:{hit.group(3)}" if hit else m.stem


def status():
    """'' when a model can run, otherwise what's missing (for messages and the tray)."""
    if find_engine() is None:
        return ("The language model engine (llama.cpp) isn't installed. Put it in "
                f"E:\\{MODELS_DIR_NAME}\\llama.cpp\\vulkan.")
    if find_model() is None:
        return f"No language model is installed. Put the model (.gguf) in E:\\{MODELS_DIR_NAME}."
    return _error


def available():
    return status() == ""


# ---- running the server ---------------------------------------------------------------------------------------

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


def _healthy():
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{_port}/health", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def ensure_started(ctx=None):
    """Start (or restart, for a bigger context) the server and wait until the model is loaded.
    Returns the base URL; raises RuntimeError with a plain message when it can't run."""
    global _proc, _port, _ctx, _error
    want = max(2048, min(131072, int(ctx or DEFAULT_CTX)))
    with _lock:
        if find_engine() is None or find_model() is None:
            raise RuntimeError(status())
        if _proc is not None and _proc.poll() is None and want <= _ctx:
            return f"http://127.0.0.1:{_port}"
        stop()
        _error = ""
        _port, _ctx = _free_port(), max(want, DEFAULT_CTX)
        args = [str(find_engine()), "-m", str(find_model()), "--host", "127.0.0.1", "--port", str(_port),
                "-c", str(_ctx), "-ngl", "999", "-np", "1", "--jinja"]
        if find_projector() is not None:
            args += ["--mmproj", str(find_projector())]
        DATA.mkdir(parents=True, exist_ok=True)
        log = open(DATA / "llama-server.log", "w", encoding="utf-8", errors="replace")
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        _proc = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                 cwd=str(find_engine().parent), creationflags=flags)
        _kill_with_us(_proc)
        deadline = time.monotonic() + START_TIMEOUT
        while time.monotonic() < deadline:
            if _proc.poll() is not None:
                _error = ("The language model engine stopped while loading the model "
                          "(see data\\llama-server.log).")
                _proc = None
                raise RuntimeError(_error)
            if _healthy():
                return f"http://127.0.0.1:{_port}"
            time.sleep(0.25)
        stop()
        _error = "The language model took too long to load."
        raise RuntimeError(_error)


def at_logon(desktop):
    """Load the model now (so the first reply is quick), or put up a warning by the clock if it can't run."""
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


def start_in_background():
    """Load the model ahead of time (at log on) so the first reply isn't slow."""
    if available():
        threading.Thread(target=lambda: _quiet(ensure_started), daemon=True, name="llm-start").start()


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


def context_size():
    return _ctx or DEFAULT_CTX


def post(path, body, stream=False, timeout=600):
    """POST JSON to the running server; returns the open response (for streaming) or the parsed JSON."""
    base = ensure_started(body.pop("_ctx", None))
    req = urllib.request.Request(base + path, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    if stream:
        return resp
    with resp:
        return json.loads(resp.read().decode("utf-8"))


def train_context():
    """The model's own maximum context (from the server), or a safe guess."""
    try:
        base = ensure_started()
        with urllib.request.urlopen(base + "/v1/models", timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
        return int(data["data"][0]["meta"]["n_ctx_train"])
    except Exception:
        return 131072 if "gemma3" in model_name() else 8192
