"""Contact Persona Styles: frozen versions of how the residents are made and how they're prompted.

A style is chosen when this computer is formatted (the launcher's Load and Format) and stays until the next format.
A frozen style lives in <Timeline>/Persona Styles/V<id>/:

  style.json        its name, id and when it was made
  Residents/        the residents' data as it was (resident.json and eras/*.json for everyone)
  generated/        what that data became - each AIM contact's persona (with its codes and the 'About you' and
                    'Your codes' blocks, in that order), the Fur Directory cards, the IRC and MUCK regulars - put
                    back at every start instead of being rebuilt
  prompting.json    every program's prompt templates and prompt-building functions, word for word; they're loaded
                    back over the live code at every start, so later changes to the code don't reach this style
  prompts/          the same, as plain text to read, and a sample AIM system prompt for every contact

The "dev" style is everything as it currently is in the code and in Residents/ - where new work happens.
A computer with no style recorded yet is on V1.0 (that's what everything was when styles began)."""
import ast
import inspect
import json
import shutil
import sys
import textwrap
import time
from pathlib import Path

from .paths import DATA, ROOT

STYLE_FILE = DATA / "persona_style.json"
DEV = "dev"
DEFAULT = "1.0"
ERA = 2001
ENV = "CLAUDE_TIMELINE_PERSONA_STYLE"          # set by the launcher's Load and Format


def styles_dir():
    from . import timeline
    return (timeline.TIMELINE if timeline.active() else ROOT) / "Persona Styles"


def folder(sid):
    return styles_dir() / f"V{sid}"


def available():
    """[{"id", "name", "description", "created"}], oldest first, then the development style."""
    out = []
    base = styles_dir()
    for d in sorted(base.iterdir(), key=lambda p: _version_key(p.name[1:])) if base.is_dir() else []:
        meta = _load(d / "style.json")
        if meta.get("id"):
            out.append(meta)
    out.append({"id": DEV, "name": "Development (latest changes)",
                "description": "Whatever the residents and the prompting are right now - where new work happens."})
    return out


def _version_key(v):
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (9999,)


def installed():
    """The style this computer was set up with."""
    sid = _load(STYLE_FILE).get("style")
    if sid == DEV or (sid and folder(sid).is_dir()):
        return sid
    return DEFAULT if folder(DEFAULT).is_dir() else DEV


def set_installed(sid):
    STYLE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STYLE_FILE.write_text(json.dumps({"style": sid, "since": time.strftime("%Y-%m-%d %H:%M")}, indent=2),
                          encoding="utf-8")


def name(sid=None):
    sid = sid or installed()
    return next((s["name"] for s in available() if s["id"] == sid), sid)


def frozen():
    return (_testing or installed()) != DEV


_testing = None


def testing(sid):
    """Make uses() answer for this style (the realism test runs a style other than the installed one)."""
    global _testing
    _testing = sid


def uses(feature):
    """Does this computer's style have a feature that came after the styles recorded so far? New behaviour that
    isn't in a recorded prompt function (a reply post-processor, say) asks this first. The Development style has
    everything; a frozen style only what its style.json lists under "features" (V1.0 lists none)."""
    sid = _testing or installed()
    if sid == DEV:
        return True
    return feature in (_load(folder(sid) / "style.json").get("features") or [])


def _load(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


# ---- what a style keeps -----------------------------------------------------------------------------------
PROGRAM_FILES = ROOT / "Program Files"
GENERATED = [("ClaudeAIM/contacts", "*.json"), ("ClaudeAIM/contacts", "*.txt"),
             ("The Fur Directory/residents", "*.json"), ("ClaudeIRC", "regulars.json"),
             ("ClaudeMUCK/world", "regulars.json")]
# the prompting: (module, [names]) - CAPITALS are templates, the rest functions or Class.methods
PROMPTING = [
    ("claudeaim.llm", ["SYSTEM_PROMPT", "clean_reply"]),
    ("claudeaim.engine", ["World._system_prompt", "World._work_note", "World._pictures_prompt", "World._conversation",
                          "World.build_messages"]),
    ("claudexp.hosting", ["AppHost.extra_context", "AppHost._picture_pacing"]),
    ("claudexp.fursonas", ["knowledge"]),
    ("claudexp.life", ["STORY_PROMPT", "TALK_PROMPT", "EMAIL_PROMPT", "REPLY_PROMPT", "REACH_OUT",
                       "LifeSim._story_prompt", "LifeSim.context"]),
    ("claudexp.life.lj", ["BACKFILL_PROMPT", "COMMENT_PROMPT", "REPLY_PROMPT"]),
    ("claudexp.life.mail_extras", ["FORWARD_PROMPT", "GROUP_PROMPT", "GROUP_REPLY_PROMPT"]),
    ("claudexp.programs.messengers.core", ["PROMPT", "Network._reply"]),
    ("claudexp.programs.messengers.discord", ["CHANNEL_PROMPT", "DiscordNetwork._channel_reply"]),
    ("claudexp.programs.irc.brain", ["BASE", "CHANNEL", "QUERY", "Brain._system", "Brain.channel_line",
                                     "Brain.query_line", "parse_line"]),
    ("claudexp.programs.muck.brain", ["BASE", "ACT", "PAGE", "DESCRIBE", "_clean", "parse_action", "Brain._model",
                                      "Brain._options", "Brain._system", "Brain.act", "Brain.page", "Brain.describe"]),
    ("claudexp.programs.furcadia.world", ["BASE", "ACT", "WHISPER", "FurcBrain._system", "FurcBrain.act",
                                          "FurcBrain.whisper"]),
    ("claudexp.programs.secondlife.world", ["BASE", "ACT", "IM", "LINES", "GREET", "REPLY", "SLBrain._system",
                                            "SLBrain.act", "SLBrain.im"]),
    ("claudexp.programs.navigator.web", ["PROMPT", "SEARCH_EXTRA", "BUDDY_EXTRA", "WebKnowledge.context"]),
]
# whole modules recorded as they are (from V1.1): the residents' typing voices and how replies are retyped
MODULES = ["claudexp.voices"]
# kept for reading only: how the personas were put together (the generated files are what's actually used)
REFERENCE = ["claudexp.residents_sync", "claudecore.furcodes.steering"]


def _ready():
    """The module paths ClaudeXP's programs expect."""
    from .programs.aim import ensure_aim_path
    ensure_aim_path()
    from . import timeline
    core = timeline.TIMELINE / "ClaudeCore"
    if core.is_dir() and str(core) not in sys.path:
        sys.path.insert(0, str(core))


def _import(modname):
    import importlib
    return importlib.import_module(modname)


def _get(mod, dotted):
    obj = mod
    for part in dotted.split("."):
        obj = getattr(obj, part)
    return obj


def _source(fn):
    fn = inspect.unwrap(fn.__func__ if isinstance(fn, (staticmethod, classmethod)) else fn)
    if getattr(fn, "__persona_source__", None):        # (restored from a style: its recorded source)
        return fn.__persona_source__
    src = textwrap.dedent(inspect.getsource(fn))
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "super" \
                and not node.args:
            raise ValueError(f"{fn.__qualname__} uses super() with no arguments, which can't be reloaded")
    return src


def _raw(mod, dotted):
    """The attribute as defined (a staticmethod stays a staticmethod)."""
    parts = dotted.split(".")
    owner = _get(mod, ".".join(parts[:-1])) if len(parts) > 1 else mod
    return owner.__dict__.get(parts[-1], getattr(owner, parts[-1]))


def capture():
    """The live prompting, as {module: {name: {"kind", "value"}}}."""
    _ready()
    out = {}
    for modname, names in PROMPTING:
        mod = _import(modname)
        entry = {}
        for n in names:
            obj = _raw(mod, n)
            if n.split(".")[-1].isupper():
                value = obj if isinstance(obj, str) else list(obj) if isinstance(obj, (tuple, list)) else obj
                entry[n] = {"kind": "text", "value": value, "type": type(obj).__name__}
            else:
                kind = "static" if isinstance(obj, staticmethod) else "code"
                try:
                    entry[n] = {"kind": kind, "value": _source(obj)}
                except (OSError, TypeError) as exc:       # (no source to read: it can't match a recording)
                    entry[n] = {"kind": kind, "value": f"<no source: {exc}>"}
        out[modname] = entry
    for modname in MODULES:
        mod = _import(modname)
        src = getattr(mod, "__persona_source__", None) or inspect.getsource(mod)
        out.setdefault(modname, {})["<module>"] = {"kind": "module", "value": src}
    return out


# ---- making a style ----------------------------------------------------------------------------------------
def record(sid, title, description="", features=()):
    """Freeze everything as it is now into Persona Styles/V<sid>/. features: what uses() should say yes to."""
    from . import timeline
    testing(DEV)                                        # (the live code is what's being recorded)
    from . import residents_sync
    residents_sync.sync()                               # (this computer may hold a frozen style's files: make them anew)
    dest = folder(sid)
    if dest.exists():
        raise FileExistsError(f"{dest} already exists")
    dest.mkdir(parents=True)
    # the residents' data
    residents = timeline.TIMELINE / "Residents"
    count = 0
    for f in residents.rglob("*"):
        if f.is_file() and (f.name == "resident.json" or (f.parent.name == "eras" and f.suffix == ".json")
                            or f.name == "README.txt" and f.parent == residents):
            out = dest / "Residents" / f.relative_to(residents)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out)
            count += 1
    # what it became
    gen = 0
    for sub, pattern in GENERATED:
        for f in (PROGRAM_FILES / sub).glob(pattern):
            out = dest / "generated" / f.relative_to(PROGRAM_FILES)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out)
            gen += 1
    # the prompting
    prompting = capture()
    (dest / "prompting.json").write_text(json.dumps(prompting, indent=1, ensure_ascii=False), encoding="utf-8")
    _write_readable(dest, prompting)
    meta = {"id": sid, "name": title, "description": description, "era": ERA,
            "created": time.strftime("%Y-%m-%d %H:%M"), "resident_files": count, "generated_files": gen}
    if features:
        meta["features"] = list(features)
    if "voice" in features:
        from . import voices
        people = {f.stem for f in (dest / "generated" / "ClaudeAIM" / "contacts").glob("*.json")}
        (dest / "voices.json").write_text(json.dumps({n: voices.describe(n) for n in sorted(people)}, indent=1,
                                                     ensure_ascii=False), encoding="utf-8")
    (dest / "style.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    testing(None)
    restore_generated()                                 # (and back to this computer's own style's files)
    return meta


def _write_readable(dest, prompting):
    out = dest / "prompts"
    for modname, entry in prompting.items():
        lines = []
        for n, v in entry.items():
            lines.append(f"==== {n} ({'template' if v['kind'] == 'text' else 'function'})")
            value = v["value"]
            lines.append(value if isinstance(value, str) else json.dumps(value, indent=1, ensure_ascii=False))
            lines.append("")
        (out / "templates and functions").mkdir(parents=True, exist_ok=True)
        (out / "templates and functions" / f"{modname}.txt").write_text("\n".join(lines), encoding="utf-8")
    ref = out / "how personas are assembled"
    ref.mkdir(parents=True, exist_ok=True)
    for modname in REFERENCE:
        try:
            mod = _import(modname)
            (ref / f"{modname}.py.txt").write_text(inspect.getsource(mod), encoding="utf-8")
        except Exception:
            pass
    samples = out / "AIM system prompts"
    samples.mkdir(parents=True, exist_ok=True)
    for name_, text in sample_aim_prompts().items():
        (samples / f"{name_}.txt").write_text(text, encoding="utf-8")


def sample_aim_prompts(user="Kithylin", contacts=None):
    """What each AIM contact's system prompt looks like (at a fixed moment, before any chats or diaries).
    contacts: [Contact] to use instead of the ones in Program Files."""
    _ready()
    from types import SimpleNamespace

    from claudeaim import contacts as aim_contacts
    from claudeaim import engine, timefmt
    out = {}
    import datetime
    fixed = "Monday, October 15, 2001, 7:30 PM"
    saved = (timefmt.now_text, timefmt.clock_text, engine.host.extra_context
             if hasattr(engine, "host") else None, timefmt.local_now, timefmt.shifted)
    timefmt.now_text = lambda tz=None: fixed
    timefmt.clock_text = lambda: "7:30 PM"
    timefmt.local_now = lambda tz=None: datetime.datetime(2001, 10, 15, 19, 30)
    timefmt.shifted = lambda d: d
    try:
        if hasattr(engine, "host"):
            from .hosting import AppHost
            engine.host.extra_context = lambda name: ("\n\n[...then their diary notes and what they know about you]"
                                                      + AppHost._voice_note(name))
        if contacts is None:
            loaded = aim_contacts.load_contacts()
            contacts = loaded[0] if isinstance(loaded, tuple) else loaded
        contact_list = contacts
        fake = SimpleNamespace(settings={"screen_name": user}, user_away=False, user_away_message="")
        fake._pictures_prompt = lambda b: engine.World._pictures_prompt(fake, b)
        fake._work_note = lambda b: engine.World._work_note(fake, b)
        fake._sent_pictures = lambda b: set()
        fake._shared_recently = lambda b: False
        fake._busy_now = lambda b: False
        for c in contact_list:
            b = SimpleNamespace(name=c.screen_name, contact=c)
            try:
                out[c.screen_name] = engine.World._system_prompt(fake, b)
            except Exception as exc:
                out[c.screen_name] = f"(couldn't render: {exc})"
    finally:
        timefmt.now_text, timefmt.clock_text, timefmt.local_now, timefmt.shifted = saved[0], saved[1], saved[3], saved[4]
        if saved[2] is not None:
            engine.host.extra_context = saved[2]
    return out


# ---- using a style -----------------------------------------------------------------------------------------
def restore_generated():
    """Put the style's contact files back (instead of rebuilding them). Returns how many changed."""
    src = folder(installed()) / "generated"
    if not src.is_dir():
        return 0
    changed = 0
    keep = set()
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(src)
        keep.add(rel)
        out = PROGRAM_FILES / rel
        try:
            if out.exists() and out.read_bytes() == f.read_bytes():
                continue
        except OSError:
            pass
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, out)
        changed += 1
    for sub, pattern in GENERATED:                    # nobody who wasn't in the style
        for f in (PROGRAM_FILES / sub).glob(pattern):
            if f.relative_to(PROGRAM_FILES) not in keep:
                try:
                    f.unlink()
                    changed += 1
                except OSError:
                    pass
    return changed


def apply(sid=None):
    """Load a frozen style's prompting back over the live code. Returns [names replaced]."""
    sid = sid or installed()
    if sid == DEV:
        return []
    prompting = _load(folder(sid) / "prompting.json")
    if not prompting:
        return []
    _ready()
    replaced = []
    swaps = {}
    for modname, entry in prompting.items():
        try:
            mod = _import(modname)
        except Exception as exc:
            print(f"Persona style: can't load {modname}: {exc}", file=sys.stderr)
            continue
        for n, v in entry.items():
            if v["kind"] == "module":                 # a whole module: run the recorded one in its place
                live = getattr(mod, "__persona_source__", None) or inspect.getsource(mod)
                if live != v["value"]:
                    try:
                        exec(compile(v["value"], f"<{sid} {modname}>", "exec"), mod.__dict__)
                        mod.__persona_source__ = v["value"]
                        replaced.append(modname)
                    except Exception as exc:
                        print(f"Persona style: couldn't restore {modname}: {exc}", file=sys.stderr)
                continue
            parts = n.split(".")
            try:
                owner = _get(mod, ".".join(parts[:-1])) if len(parts) > 1 else mod
                current = owner.__dict__.get(parts[-1])
                if v["kind"] == "text":
                    value = tuple(v["value"]) if v.get("type") == "tuple" else v["value"]
                    if current != value:
                        setattr(owner, parts[-1], value)
                        replaced.append(f"{modname}.{n}")
                    continue
                try:
                    same = current is not None and _source(current) == v["value"]
                except (OSError, TypeError):
                    same = False
                if same:
                    continue                          # (the live code still matches the style)
                ns = {}
                exec(compile(v["value"], f"<{sid} {modname}.{n}>", "exec"), mod.__dict__, ns)
                new = ns[parts[-1]]
                inner = new.__func__ if isinstance(new, (staticmethod, classmethod)) else new
                inner.__persona_source__ = v["value"]
                setattr(owner, parts[-1], new)
                if current is not None:
                    swaps[id(current)] = (current, new)
                replaced.append(f"{modname}.{n}")
            except Exception as exc:
                print(f"Persona style: couldn't restore {modname}.{n}: {exc}", file=sys.stderr)
    if swaps:                                         # names other modules imported directly
        for m in list(sys.modules.values()):
            d = getattr(m, "__dict__", None)
            if not isinstance(d, dict):
                continue
            for k, val in list(d.items()):
                hit = swaps.get(id(val))
                if hit is not None and hit[0] is val:
                    d[k] = hit[1]
    return replaced


def check(sid=None):
    """What in the live code differs from a style's recorded prompting: [names]."""
    sid = sid or installed()
    if sid == DEV:
        return []
    recorded = _load(folder(sid) / "prompting.json")
    live = capture()
    out = []
    for modname, entry in recorded.items():
        for n, v in entry.items():
            if live.get(modname, {}).get(n, {}).get("value") != v["value"]:
                out.append(f"{modname}.{n}")
    return out


def requested():
    """The style the launcher asked for with Load and Format (or None)."""
    import os
    sid = os.environ.get(ENV)
    return sid or None


def consume_request():
    import os
    os.environ.pop(ENV, None)
