"""What a model can hold, and what that costs: its own context limit (from the .gguf file's header) and an estimate of
the graphics memory a given context needs - the model itself plus its context cache.

Gemma 3 and 4 keep most of their layers to a 1,024-token sliding window, so only their few "global" layers grow with
the context: a 128k context costs them about 1.5 GB, not tens. The estimate reads each layer's shape from the file
(heads, key length, sliding or not) and counts an 8-bit cache (the engine's q8_0)."""
import json
import struct
import subprocess
from pathlib import Path

MAX_CONTEXT = 131072            # 128k: the most a Companion is given, even if its model could take more
CACHE_BYTES = 1.0625            # q8_0: a byte a value, plus its scales
OVERHEAD_GB = 0.9               # the engine's working buffers, roughly
_SCALARS = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1, 10: 8, 11: 8, 12: 8}
_FMT = {0: "<B", 1: "<b", 2: "<H", 3: "<h", 4: "<I", 5: "<i", 6: "<f", 7: "<?", 10: "<Q", 11: "<q", 12: "<d"}
_cache = {}


def _meta(path):
    """The header of a .gguf file, without its tokenizer (big arrays are skipped)."""
    out = {}
    with open(path, "rb") as f:
        if f.read(4) != b"GGUF":
            return out
        f.read(4)
        _n_tensors, n_kv = struct.unpack("<QQ", f.read(16))

        def string():
            n, = struct.unpack("<Q", f.read(8))
            return f.read(n).decode("utf-8", "replace")

        def value(t, keep=True):
            if t in _FMT:
                return struct.unpack(_FMT[t], f.read(_SCALARS[t]))[0]
            if t == 8:
                return string()
            if t == 9:
                at, = struct.unpack("<I", f.read(4))
                n, = struct.unpack("<Q", f.read(8))
                if at == 8:
                    for _ in range(n):
                        k, = struct.unpack("<Q", f.read(8))
                        f.seek(k, 1)
                    return None
                if n > 1024 or not keep:
                    f.seek(n * _SCALARS[at], 1)
                    return None
                return [value(at) for _ in range(n)]
            raise ValueError(t)
        for _ in range(n_kv):
            key = string()
            t, = struct.unpack("<I", f.read(4))
            v = value(t, keep="tokenizer" not in key)
            if v is not None and "tokenizer" not in key:
                out[key] = v
    return out


def model_facts(path):
    """{"context", "layers"...} for a .gguf (cached by path and size)."""
    path = Path(path)
    try:
        key = (str(path), path.stat().st_size)
    except OSError:
        return {}
    if key not in _cache:
        try:
            m = _meta(path)
        except (OSError, ValueError, struct.error):
            m = {}
        arch = m.get("general.architecture", "")
        g = lambda name, default=None: m.get(f"{arch}.{name}", default)
        n = int(g("block_count", 0) or 0)

        def per_layer(v, default):
            if isinstance(v, list):
                return [int(x) for x in v][:n] + [default] * max(0, n - len(v))
            return [int(v if v is not None else default)] * n
        kv = per_layer(g("attention.head_count_kv"), int(g("attention.head_count", 8) or 8))
        window = int(g("attention.sliding_window", 0) or 0)
        pattern = g("attention.sliding_window_pattern")
        if isinstance(pattern, list):
            sliding = [bool(x) for x in pattern][:n]
        elif window and arch == "gemma3":
            sliding = [(i + 1) % 6 != 0 for i in range(n)]     # (Gemma 3: five local layers, then one global)
        else:
            sliding = [False] * n
        _cache[key] = {"context": int(g("context_length", 0) or 0), "layers": n, "kv": kv, "window": window,
                       "sliding": sliding, "key": int(g("attention.key_length", 128) or 128),
                       "key_swa": int(g("attention.key_length_swa", 0) or g("attention.key_length", 128) or 128),
                       "file_gb": path.stat().st_size / 2**30}
    return _cache[key]


def full_context(path, lora=None):
    """The context a Companion on this model gets by default: the model's own, up to 128k - or, if that wouldn't fit
    on the graphics card, the biggest that does (halving from 128k, no lower than 8k)."""
    c = model_facts(path).get("context") or 0
    ctx = min(c, MAX_CONTEXT) if c else 32768
    card = card_gb()
    if card:
        while ctx > 8192 and (memory_gb(path, ctx, lora) or 0) > card * 0.92:
            ctx //= 2
    return ctx


def memory_gb(path, context, lora=None):
    """Roughly how much graphics memory the model takes at this context (None if the file can't be read)."""
    f = model_facts(path)
    if not f.get("layers"):
        return None
    values = 0
    for i in range(f["layers"]):
        swa = f["sliding"][i] if i < len(f["sliding"]) else False
        tokens = min(context, f["window"] + 512) if swa and f["window"] else context
        head = f["key_swa"] if swa else f["key"]
        values += 2 * f["kv"][i] * head * tokens
    extra = Path(lora).stat().st_size / 2**30 if lora and Path(lora).exists() else 0
    return f["file_gb"] + extra + values * CACHE_BYTES / 2**30 + OVERHEAD_GB


def card_gb():
    """The graphics card's memory (NVIDIA), or None."""
    if "card" not in _cache:
        try:
            out = subprocess.run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                                 capture_output=True, text=True, timeout=5,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
            _cache["card"] = int(out.split()[0]) / 1024 if out.strip() else None
        except (OSError, ValueError, subprocess.SubprocessError, IndexError):
            _cache["card"] = None
    return _cache["card"]
