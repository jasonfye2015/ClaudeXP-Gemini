"""The start-up self-check: looks for the problems that have actually stopped a computer from starting, before one
boots - so a bad file name or a half-written settings file shows up as a plain message instead of a computer that
won't load.

    findings = selfcheck.run()                 # [Finding(level, area, message, advice)]
    selfcheck.blocking(findings, "xp")         # the errors that would stop that computer
    selfcheck.run(quick=True)                  # without the code check (what a computer runs on its own at start)

level: "error" (it won't start, or will lose something), "warning" (it may misbehave), "info" (worth knowing).
area: "xp", "w7", "w11" (one computer), "all" (every computer), or "storage" / "backup".

Checks: program names Windows can't use as file names, and duplicate program keys; Python syntax in every program
file (only files changed since the last check are re-read; the results are kept in Profile/selfcheck.json); settings
and save files that can't be read; leftovers of an interrupted restore or backup; free space on the drive; the
Python runtime, each computer and the language-model engine being there; and how long since the last backup."""
import ast
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
CACHE = TIMELINE / "Profile" / "selfcheck.json"
COMPUTERS = {"xp": ("EPOCH-2001", "ClaudeXP", "claudexp"), "w7": ("SYSTEM-2011", "Claude7", "claude7"),
             "w11": ("WORKSTATION-2025", "Claude11", "claude11")}
SHARED_CODE = ["ClaudeCore/claudecore", "ClaudeApps", "ClaudeGames", "ClaudeArchive", "ClaudeLauncher"]
BAD_CHARS = set('<>:"/\\|?*')
RESERVED = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}
SKIP_DIRS = {"__pycache__", ".venv", "venv", "env", "node_modules", "data", "Saves", "Art", "Models", "Data", "seed",
             "Program Files", "logs", ".git", "game"}


@dataclass
class Finding:
    level: str
    area: str
    message: str
    advice: str = ""


def name_problem(name):
    """Why Windows wouldn't accept `name` as a file name, or None."""
    bad = sorted({c for c in name if c in BAD_CHARS})
    if bad:
        return "contains " + " ".join(repr(c) for c in bad)
    if name != name.rstrip(" ."):
        return "ends with a space or a dot"
    if name.split(".")[0].upper() in RESERVED:
        return "is a name Windows reserves"
    if any(ord(c) < 32 for c in name):
        return "contains a control character"
    return None


# ---- program names -------------------------------------------------------------------------------------------
def _program_calls(path):
    """[(key, name, line)] from the Program("key", "name", ...) calls in a registry file."""
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "Program" and len(node.args) >= 2:
            k, n = node.args[0], node.args[1]
            if isinstance(k, ast.Constant) and isinstance(n, ast.Constant) and isinstance(n.value, str):
                out.append((k.value, n.value, node.lineno))
    return out


def _renames(path):
    """{key: new name} from a RENAMED = {...} dict (Windows 7 and 11 rename XP's programs)."""
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "RENAMED" for t in node.targets):
            try:
                value = ast.literal_eval(node.value)
                return {k: v[0] for k, v in value.items() if isinstance(v, tuple) and v}
            except (ValueError, TypeError):
                return {}
    return {}


def check_programs():
    found = []
    reg = TIMELINE / "ClaudeXP" / "claudexp" / "programs" / "__init__.py"
    calls = _program_calls(reg)
    seen = {}
    for key, name, line in calls:
        why = name_problem(name)
        if why:
            found.append(Finding("error", "all", f'The program "{name}" {why}, so its shortcut can\'t be made.',
                                 f"Rename it in ClaudeXP\\claudexp\\programs\\__init__.py (line {line})."))
        if key in seen:
            found.append(Finding("error", "all", f'Two programs share the key "{key}" (lines {seen[key]} and {line}).',
                                 "Give one of them a different key."))
        seen[key] = line
    for area, folder in (("w7", "Claude7/claude7"), ("w11", "Claude11/claude11")):
        for key, name in _renames(TIMELINE / folder / "programs" / "__init__.py").items():
            why = name_problem(name)
            if why:
                found.append(Finding("error", area, f'{COMPUTERS[area][0]} renames "{key}" to "{name}", which {why}.',
                                     f"Change it in {folder.replace('/', chr(92))}\\programs\\__init__.py."))
    return found


# ---- code ------------------------------------------------------------------------------------------------------
def _py_files(folder):
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if f.endswith(".py"):
                yield Path(root) / f


def check_code(progress=None):
    """Compile every program file that changed since last time. Returns findings; keeps what passed in the cache."""
    try:
        cache = json.loads(CACHE.read_text(encoding="utf-8")).get("ok", {})
    except (OSError, ValueError):
        cache = {}
    groups = [(area, TIMELINE / folder / pkg) for area, (_n, folder, pkg) in COMPUTERS.items()]
    groups += [("all", TIMELINE / rel) for rel in SHARED_CODE]
    files = [(area, f) for area, folder in groups if folder.is_dir() for f in _py_files(folder)]
    found, ok = [], {}
    for i, (area, f) in enumerate(files):
        rel = f.relative_to(TIMELINE).as_posix()
        try:
            stamp = f"{f.stat().st_mtime_ns}:{f.stat().st_size}"
        except OSError:
            continue
        if cache.get(rel) == stamp:
            ok[rel] = stamp
            continue
        try:
            compile(f.read_bytes(), str(f), "exec", dont_inherit=True)
            ok[rel] = stamp
        except SyntaxError as exc:
            who = COMPUTERS[area][0] if area in COMPUTERS else "every computer"
            found.append(Finding("error", area, f"A code error in {rel}, line {exc.lineno}: {exc.msg}.",
                                 f"This stops {who} from starting until it's fixed."))
        except (ValueError, OSError) as exc:
            found.append(Finding("warning", area, f"{rel} couldn't be read: {exc}."))
        if progress and i % 50 == 0:
            progress(i, len(files))
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps({"checked": time.strftime("%Y-%m-%d %H:%M:%S"), "ok": ok}), encoding="utf-8")
    except OSError:
        pass
    return found


# ---- data ------------------------------------------------------------------------------------------------------
def _json_files(folder, depth):
    if not folder.is_dir():
        return
    base = len(folder.parts)
    for root, dirs, files in os.walk(folder):
        if len(Path(root).parts) - base >= depth:
            dirs[:] = []
        dirs[:] = [d for d in dirs if d not in ("Drive C", "Recycle Bin", "System Volume Information", "__pycache__")]
        for f in files:
            if f.endswith(".json"):
                yield Path(root) / f


def check_data():
    found = []
    places = [(area, TIMELINE / folder / "data", 2) for area, (_n, folder, _p) in COMPUTERS.items()]
    places += [("all", TIMELINE / "ClaudeGames" / "Saves", 3), ("all", TIMELINE / "Profile", 1),
               ("all", TIMELINE / "ClaudeApps" / "kithylinai" / "Data", 2)]
    for area, folder, depth in places:
        for f in _json_files(folder, depth):
            try:
                text = f.read_text(encoding="utf-8")
                if text.strip():
                    json.loads(text)
            except (ValueError, UnicodeDecodeError):
                who = COMPUTERS[area][0] if area in COMPUTERS else "the Timeline"
                found.append(Finding("warning", area, f"{f.relative_to(TIMELINE)} is damaged and can't be read.",
                                     f"{who} will start with that setting reset. Restore it from a backup to get it back."))
            except OSError:
                pass
    for area, (_n, folder, _p) in COMPUTERS.items():
        data = TIMELINE / folder / "data"
        if data.is_dir():
            for p in data.iterdir():
                if ".restoring-" in p.name:
                    found.append(Finding("warning", area, f"{p.relative_to(TIMELINE)} is left over from a restore that "
                                                          f"didn't finish.", "Check the computer's data, then delete it."))
    for p in TIMELINE.parent.glob("*/*.partial"):
        if "Backup" in p.parent.name:
            found.append(Finding("info", "backup", f"An unfinished backup file was left behind: {p.name}.",
                                 "It's safe to delete."))
    return found


# ---- the drive, the runtime, the engine ------------------------------------------------------------------------
def check_setup():
    found = []
    try:
        free = shutil.disk_usage(TIMELINE).free
        if free < 1 << 30:
            found.append(Finding("error", "all", f"Only {free / 2**20:.0f} MB free on the Timeline's drive.",
                                 "The computers save as they run; free some space before starting one."))
        elif free < 5 << 30:
            found.append(Finding("warning", "all", f"Only {free / 2**30:.1f} GB free on the Timeline's drive.",
                                 "Fine for now, but language models and backups need room."))
    except OSError:
        pass
    if sys.platform == "darwin":
        runtime = TIMELINE / "Python-mac" / "bin" / "python3"
    else:
        runtime = TIMELINE / "Python" / "pythonw.exe"
    if not runtime.exists():
        found.append(Finding("warning", "all", "The Timeline's own Python isn't on this drive.",
                             "The computers will run on this PC's Python instead, if it has one."))
    for area, (name, folder, _p) in COMPUTERS.items():
        if not (TIMELINE / folder / "main.py").exists():
            found.append(Finding("error", area, f"{name} isn't installed ({folder}\\main.py is missing)."))
    llm = TIMELINE / "Local Storage" / "LLM Models"
    if not (TIMELINE / "Local Storage").is_dir():
        found.append(Finding("warning", "storage", "Local Storage (the external drive with the archive and models) "
                                                   "isn't where the Timeline expects it.",
                             "Set it in a computer's Config in the launcher."))
    else:
        exe = "llama-server" if os.name != "nt" else "llama-server.exe"
        flavours = ("macos",) if sys.platform == "darwin" else ("vulkan", "cuda", "cpu")
        if not any((llm / "llama.cpp" / f / exe).exists() for f in flavours):
            found.append(Finding("warning", "storage", "The language-model engine (llama.cpp) is missing.",
                                 "The residents, the messengers' buddies and the AI programs won't be able to talk."))
        models = llm / "models"
        if not models.is_dir() or not any(models.glob("*/*.gguf")):
            found.append(Finding("warning", "storage", "No language models are installed.",
                                 "Add them in Control Panel > AI Models."))
    return found


def check_backup():
    try:
        from . import backup
        items = backup.listing()
    except Exception:
        return []
    if not items:
        return [Finding("info", "backup", "There are no backups yet.", "BACKUP in the launcher makes one.")]
    try:
        newest = time.mktime(time.strptime(items[0][1].get("made", ""), "%Y-%m-%d %H:%M:%S"))
        days = (time.time() - newest) / 86400
    except ValueError:
        return []
    if days > 14:
        return [Finding("info", "backup", f"The newest backup is {int(days)} days old.", "BACKUP in the launcher.")]
    return []


# ---- all of it -------------------------------------------------------------------------------------------------
def run(quick=False, progress=None):
    findings = []
    for check in (check_programs, check_data, check_setup, check_backup):
        try:
            findings += check()
        except Exception as exc:                      # a check that fails must never stop anything
            findings.append(Finding("info", "all", f"One of the checks couldn't run ({exc})."))
    if not quick:
        try:
            findings += check_code(progress)
        except Exception as exc:
            findings.append(Finding("info", "all", f"The code check couldn't run ({exc})."))
    order = {"error": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda f: order.get(f.level, 3))
    return findings


def blocking(findings, area):
    """The errors that would stop that computer ('xp', 'w7' or 'w11') from starting."""
    return [f for f in findings if f.level == "error" and f.area in (area, "all")]


def report(findings):
    if not findings:
        return "Everything checks out."
    return "\n".join(f"[{f.level.upper()}] {f.message}" + (f"  {f.advice}" if f.advice else "") for f in findings)


def at_start(area):
    """What a computer runs as it starts: the quick checks, written to its logs folder. Never stops it starting."""
    try:
        findings = [f for f in run(quick=True) if f.area in (area, "all") and f.level != "info"]
        folder = TIMELINE / COMPUTERS[area][1] / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "selfcheck.log").write_text(time.strftime("%Y-%m-%d %H:%M:%S\n") + report(findings) + "\n",
                                              encoding="utf-8")
        if findings and sys.stderr is not None:
            sys.stderr.write("Self-check:\n" + report(findings) + "\n")
        return findings
    except Exception:
        return []
