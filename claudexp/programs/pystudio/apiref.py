"""A compact API cheat sheet of the installed game/image/sound libraries, built from the studio runtime itself.

Small models guess at library calls; the lines that match a question are put in front of the model so they don't have
to. The sheet is built once (by running the studio's own Python) and cached in Python Studio/apiref.json."""
import json
import re
import subprocess
import threading

_BUILDER = r'''
import inspect, importlib, json, sys, warnings
warnings.simplefilter("ignore")
MODS = ["pygame", "pygame.draw", "pygame.mixer", "pygame.sprite", "pygame.transform", "pygame.image", "pygame.font",
        "pygame.key", "pygame.mouse", "pygame.time", "pygame.math", "pygame.display", "pygame.event", "pygame.mask",
        "pygame.surfarray", "pygame.gfxdraw", "pygame.joystick", "pygame.mixer_music",
        "pymunk", "pymunk.pygame_util", "pytmx", "pytmx.util_pygame", "pygame_menu", "opensimplex", "soundfile",
        "pathfinding.core.grid", "pathfinding.finder.a_star", "PIL.Image", "PIL.ImageDraw", "PIL.ImageOps",
        "PIL.ImageFilter", "PIL.ImageFont", "pydub", "mido", "imageio"]
CLASSES = ["pygame.Surface", "pygame.Rect", "pygame.FRect", "pygame.sprite.Sprite", "pygame.sprite.Group",
           "pygame.mixer.Sound", "pygame.mixer.Channel", "pygame.font.Font", "pygame.math.Vector2",
           "pygame.time.Clock", "pygame.mask.Mask", "pymunk.Space", "pymunk.Body", "pymunk.Circle", "pymunk.Poly",
           "pymunk.Segment", "pymunk.Vec2d", "pygame_menu.Menu", "pytmx.TiledMap", "PIL.Image.Image",
           "PIL.ImageDraw.ImageDraw", "pydub.AudioSegment"]
out = {}
def first(obj):
    d = inspect.getdoc(obj) or ""
    d = d.strip().split("\n")[0].strip()
    return d[:150]
def sig(obj):
    try:
        return str(inspect.signature(obj))
    except Exception:
        return ""
def add(qual, obj):
    s = sig(obj)
    d = first(obj)
    if d.startswith(qual.split(".")[-1] + "("):
        line = d
    else:
        line = (s + "  " if s else "") + d
    out[qual] = line.strip()[:170]
def walk_class(qual, cls):
    add(qual, cls)
    for name, member in inspect.getmembers(cls):
        if name.startswith("_"):
            continue
        if callable(member) or isinstance(member, property):
            add(qual + "." + name, member)
for m in MODS:
    try:
        mod = importlib.import_module(m)
    except Exception:
        continue
    for name, member in inspect.getmembers(mod):
        if name.startswith("_") or inspect.ismodule(member):
            continue
        if getattr(member, "__module__", m) and not str(getattr(member, "__module__", m)).startswith(m.split(".")[0]):
            continue
        if callable(member):
            add(m + "." + name, member)
for q in CLASSES:
    mod, _, name = q.rpartition(".")
    try:
        obj = getattr(importlib.import_module(mod), name)
    except Exception:
        continue
    walk_class(q, obj)
json.dump(out, sys.stdout)
'''

_cache = None
_lock = threading.Lock()


def cache_file():
    from .app import studio_root
    return studio_root() / "apiref.json"


def build(python):
    """Run the introspection under the studio's Python and store the result. Returns the entry count."""
    flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    import os
    env = {k: v for k, v in os.environ.items() if k.upper() not in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV")}
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
    res = subprocess.run([str(python), "-c", _BUILDER], capture_output=True, text=True, timeout=180,
                         creationflags=flags, env=env)
    data = json.loads(res.stdout)
    cache_file().write_text(json.dumps(data), encoding="utf-8")
    return len(data)


def load(python=None):
    """The cheat sheet ({qualified name: line}); builds it first if needed and a runtime is given."""
    global _cache
    with _lock:
        if _cache is not None:
            return _cache
        try:
            _cache = json.loads(cache_file().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _cache = {}
            if python is not None:
                try:
                    build(python)
                    _cache = json.loads(cache_file().read_text(encoding="utf-8"))
                except Exception:
                    _cache = {}
        return _cache


WORDS = re.compile(r"[a-z][a-z0-9]{2,}")
STOP = {"the", "and", "for", "with", "that", "this", "make", "write", "create", "how", "can", "you", "from", "into",
        "use", "using", "when", "game", "code", "program", "function", "add", "show", "set", "get", "new", "line"}


def lookup(text, imports=(), limit=22, max_chars=2800):
    """Cheat-sheet lines relevant to `text` (the question) and the modules the open file imports."""
    sheet = _cache if _cache is not None else load()
    if not sheet:
        return ""
    words = {w for w in WORDS.findall(text.lower()) if w not in STOP}
    imports = {i.lower() for i in imports}
    scored = []
    for qual, line in sheet.items():
        parts = [p.lower() for p in re.split(r"[._]", qual) if p]
        tail = qual.split(".")[-1].lower()
        score = 0
        for w in words:
            if w == tail:
                score += 4
            elif w in parts:
                score += 2
            elif len(w) > 4 and (w in tail or tail in w and len(tail) > 3):
                score += 1
        if score and qual.split(".")[0].lower() in imports:
            score += 1
        if score >= 2:
            scored.append((score, -len(qual), qual, line))
    scored.sort(reverse=True)
    out, size = [], 0
    for _s, _l, qual, line in scored[:limit]:
        entry = f"{qual}{'' if line.startswith('(') else ': '}{line}"
        if size + len(entry) > max_chars:
            break
        out.append(entry)
        size += len(entry) + 1
    return "\n".join(out)
