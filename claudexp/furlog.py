"""Furry Log's recorder: a plain-text diary of everything the language model does, for debugging and curiosity.

Every request any program makes goes through the `ollama` stand-in (claudexp/stubs/ollama), which reports here:
the exact prompt (all messages), the options, which model was asked for and which one really answered, then the
raw reply (and any reasoning), how long it took, and any error. Image generation and speech jobs add a line each.
One file per day in data/furry_log/, with real wall-clock times (not ClaudeXP's 2001 clock), so the files read well
in any editor. Recording can never break the program being logged: every failure in here is swallowed."""
import itertools
import json
import threading
from datetime import date, datetime, timedelta

from .paths import DATA

LOG_DIR = DATA / "furry_log"
SETTINGS_FILE = DATA / "furry_log.json"
DEFAULTS = {"enabled": True, "full_text": True, "keep_days": 30}
MAX_CHARS = 100_000          # one prompt or reply longer than this is clipped in the file

context = threading.local()  # the broker says who is asking (context.info = {"source": ..., "priority": ...})
_lock = threading.Lock()
_ids = itertools.count(1)
_settings = None
_session_marked = False
_pruned = False


def settings():
    global _settings
    if _settings is None:
        _settings = dict(DEFAULTS)
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        if isinstance(data, dict):
            for key, default in DEFAULTS.items():
                value = data.get(key)
                if isinstance(default, bool) and isinstance(value, bool):
                    _settings[key] = value
                elif (isinstance(default, int) and not isinstance(default, bool) and isinstance(value, int)
                      and not isinstance(value, bool)):
                    _settings[key] = max(1, min(3650, value))
    return _settings


def save_settings():
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(settings(), indent=2), encoding="utf-8")
    except OSError:
        pass


def enabled():
    return settings()["enabled"]


# ---- files ------------------------------------------------------------------------------------------------------
def path_for(day):
    return LOG_DIR / f"{day:%Y-%m-%d}.log"


def log_days():
    """Dates that have a log file, newest first."""
    days = []
    try:
        for f in LOG_DIR.glob("*.log"):
            try:
                days.append(datetime.strptime(f.stem, "%Y-%m-%d").date())
            except ValueError:
                pass
    except OSError:
        pass
    return sorted(days, reverse=True)


def _prune():
    cutoff = date.today() - timedelta(days=settings()["keep_days"])
    for day in log_days():
        if day < cutoff:
            try:
                path_for(day).unlink()
            except OSError:
                pass


def _stamp(now=None):
    return (now or datetime.now()).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _write(text):
    global _session_marked, _pruned
    try:
        with _lock:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            now = datetime.now()
            chunks = []
            if not _session_marked:
                _session_marked = True
                chunks.append(f"==== {_stamp(now)}  SESSION  ClaudeXP started (log is {'ON' if enabled() else 'OFF'})\n\n")
            chunks.append(text)
            with open(path_for(now.date()), "a", encoding="utf-8", errors="replace", newline="\n") as f:
                f.write("".join(chunks))
            if not _pruned:
                _pruned = True
                _prune()
    except Exception:
        pass


def _clip(text):
    text = "" if text is None else str(text)
    if len(text) > MAX_CHARS:
        return text[:MAX_CHARS] + f"\n[... {len(text) - MAX_CHARS:,} more characters not logged]"
    return text


def _images(message):
    items = message.get("images") or []
    if not items:
        return ""
    bits = []
    for img in items:
        bits.append(f"{len(img):,} bytes" if isinstance(img, (bytes, bytearray)) else str(img))
    return f"[{len(items)} image(s): {', '.join(bits)}]"


def _who():
    info = getattr(context, "info", None) or {}
    return info.get("source") or "direct call", info.get("priority") or "-"


# ---- recording --------------------------------------------------------------------------------------------------
def request(asked, used, messages, options, stream, think):
    """Log a prompt about to be sent. Returns the entry number to pass to response()."""
    if not enabled():
        return None
    rid = next(_ids)
    try:
        source, priority = _who()
        model = used if asked in (None, "", used) else f"{used} (asked for: {asked})"
        lines = [f"==== {_stamp()}  #{rid}  REQUEST  model: {model}",
                 f"mode: {'streamed' if stream else 'single reply'}   from: {source}   priority: {priority}   "
                 f"thinking: {'default' if think is None else 'on' if think else 'off'}"]
        if options:
            lines.append("options: " + json.dumps(options, default=str, sort_keys=True))
        chars = sum(len(str(m.get("content") or "")) for m in messages)
        lines.append(f"messages: {len(messages)}   prompt characters: {chars:,}")
        if settings()["full_text"]:
            for m in messages:
                lines.append(f"--- {m.get('role', 'user')} ---")
                lines.append(_clip(m.get("content")))
                pics = _images(m)
                if pics:
                    lines.append(pics)
        else:
            lines.append("(full text recording is off)")
        _write("\n".join(lines) + "\n\n")
    except Exception:
        pass
    return rid


def response(rid, text, thinking, seconds, error="", timings=None):
    """Log the raw reply (or the failure) for entry rid."""
    if rid is None:
        return
    try:
        timings = timings or {}
        status = f"ERROR: {error}" if error else "ok"
        bits = [f"{seconds:.2f}s", f"{len(text or ''):,} chars"]
        if timings.get("predicted_n"):
            bits.append(f"{int(timings['predicted_n'])} tokens")
        if timings.get("predicted_per_second"):
            bits.append(f"{float(timings['predicted_per_second']):.1f} tok/s")
        lines = [f"==== {_stamp()}  #{rid}  RESPONSE  {status}   ({', '.join(bits)})"]
        if settings()["full_text"]:
            if thinking:
                lines += ["--- thinking ---", _clip(thinking)]
            lines += ["--- output ---", _clip(text)]
        _write("\n".join(lines) + "\n\n")
    except Exception:
        pass


def event(kind, text, **fields):
    """A one-off entry: an image prompt, a spoken sentence, a transcription, a failure."""
    if not enabled():
        return
    try:
        extra = "   ".join(f"{k}: {v}" for k, v in fields.items() if v not in (None, ""))
        lines = [f"==== {_stamp()}  EVENT  {kind}" + (f"   {extra}" if extra else "")]
        if text and settings()["full_text"]:
            lines.append(_clip(text))
        _write("\n".join(lines) + "\n\n")
    except Exception:
        pass
