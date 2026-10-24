"""Backing up and restoring what's yours in the Timeline: the game saves, each computer's data, your profile, Kithylin
AI's chats (and, if you want, its models and the training results).

A backup is one .zip with a manifest.json inside, named by date and time ("Claude Timeline backup 2026-10-24 1530.zip";
automatic ones say "auto-backup"). Paths inside are relative to the Timeline folder, so a backup restores onto any copy
of the Timeline, on any drive.

    from claudecore import backup
    backup.create(["saves", "xp"], folder, progress=lambda done, total, name: ...)   # -> the .zip's path
    backup.listing(folder)                     # [(path, manifest)] newest first
    backup.restore(zip_path, ["saves"])        # a safety backup first, then those parts replaced
    backup.settings() / backup.save_settings(d)

Restoring a computer's data while that computer is running would pull the files out from under it, so the callers
refuse that (blocked=...)."""
import json
import os
import shutil
import time
import zipfile
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
SETTINGS = TIMELINE / "Profile" / "backup.json"

# key: (label, [paths relative to the Timeline], default on, what it is)
PARTS = {
    "saves": ("Game saves", ["ClaudeGames/Saves"], True, "Progress and high scores, shared by all three computers"),
    "xp": ("EPOCH-2001 (Windows XP)", ["ClaudeXP/data"], True, "Its accounts, mail, chats, desktop and residents' activity"),
    "w7": ("SYSTEM-2011 (Windows 7)", ["Claude7/data"], True, "Its accounts, mail, chats, desktop and residents' activity"),
    "w11": ("WORKSTATION-2025 (Windows 11)", ["Claude11/data"], True, "Its accounts, mail, chats, desktop and residents' activity"),
    "identity": ("Your profile", ["Profile", "ClaudeLauncher/settings.json"], True, "Your Timeline identity, codes and launcher settings"),
    "kithylin": ("Kithylin AI chats", ["ClaudeApps/kithylinai/Data"], True, "Its saved chats and settings"),
    "models": ("Kithylin models (large)", ["ClaudeApps/kithylinai/Models"], False, "The trained Kithylins, about 2.5 GB"),
    "training": ("Training results (large)", ["Local Storage/LLM Models/selfmodel/runs",
                                              "Local Storage/LLM Models/selfmodel/adapter",
                                              "Local Storage/LLM Models/selfmodel/train_log.jsonl"], False,
                 "The adapters and logs the Kithylin models were made from, about 700 MB"),
}
ORDER = list(PARTS)
ERA_PART = {2001: "xp", 2011: "w7", 2025: "w11"}
SKIP_DIRS = {"__pycache__"}
SKIP_SUFFIX = (".tmp", ".pyc")
STORED = (".gguf", ".safetensors", ".zip", ".mp3", ".mp4", ".jpg", ".png", ".webp", ".pt")   # already compressed or huge
DEFAULTS = {"folder": "", "parts": [k for k, v in PARTS.items() if v[2]], "auto": False, "keep": 5}


# ---- settings ------------------------------------------------------------------------------------------------
def default_folder():
    """Beside the Timeline on the same drive (better somewhere else: another drive survives this one failing)."""
    return TIMELINE.parent / "Claude Timeline Backups"


def settings():
    try:
        data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    out = dict(DEFAULTS)
    out.update({k: v for k, v in data.items() if k in DEFAULTS})
    out["parts"] = [p for p in out["parts"] if p in PARTS]
    return out


def save_settings(data):
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    tmp.replace(SETTINGS)


def folder():
    chosen = settings().get("folder")
    return Path(chosen) if chosen else default_folder()


def same_drive(path):
    try:
        return Path(path).resolve().anchor.lower() == TIMELINE.resolve().anchor.lower()
    except OSError:
        return True


# ---- what's there --------------------------------------------------------------------------------------------
def _files(part):
    for rel in PARTS[part][1]:
        src = TIMELINE / rel
        if src.is_file():
            yield src
        elif src.is_dir():
            for root, dirs, files in os.walk(src):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith("sounds-") and d != "sfx"]
                for name in files:
                    if not name.endswith(SKIP_SUFFIX):
                        yield Path(root) / name


def size(part):
    total = 0
    for f in _files(part):
        try:
            total += f.stat().st_size
        except OSError:
            pass
    return total


def human(n):
    for unit in ("bytes", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "bytes" else f"{n:.1f} {unit}"
        n /= 1024


# ---- making one ------------------------------------------------------------------------------------------------
def create(parts, dest=None, auto=False, label="", progress=None, cancel=None):
    """Zip those parts into dest (the settings' folder by default). Returns the backup's path."""
    dest = Path(dest) if dest else folder()
    dest.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H%M%S")
    kind = "auto-backup" if auto else ("backup before restoring" if label == "pre-restore" else "backup")
    path = dest / f"Claude Timeline {kind} {stamp}.zip"
    files = [(part, f) for part in parts if part in PARTS for f in _files(part)]
    total = sum(_safe_size(f) for _p, f in files) or 1
    done = 0
    manifest = {"made": time.strftime("%Y-%m-%d %H:%M:%S"), "parts": [p for p in parts if p in PARTS], "auto": auto,
                "label": label, "files": len(files), "bytes": total, "timeline": TIMELINE.name}
    tmp = path.with_suffix(".partial")
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            z.writestr("manifest.json", json.dumps(manifest, indent=1))
            for part, f in files:
                if cancel and cancel():
                    raise InterruptedError("cancelled")
                rel = f.relative_to(TIMELINE).as_posix()
                method = zipfile.ZIP_STORED if f.suffix.lower() in STORED else zipfile.ZIP_DEFLATED
                try:
                    z.write(f, rel, compress_type=method)
                except (OSError, ValueError):
                    continue                      # a file that vanished or is locked mid-backup: skip it
                done += _safe_size(f)
                if progress:
                    progress(done, total, rel)
        tmp.replace(path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    if auto:
        prune(dest, settings().get("keep", 5))
    return path


def _safe_size(f):
    try:
        return f.stat().st_size
    except OSError:
        return 0


def prune(dest, keep):
    """Keep only the newest `keep` automatic backups (the ones you made yourself are never removed)."""
    autos = sorted((p for p in Path(dest).glob("Claude Timeline auto-backup *.zip")), key=lambda p: p.name, reverse=True)
    for old in autos[max(1, int(keep)):]:
        try:
            old.unlink()
        except OSError:
            pass


# ---- finding them ----------------------------------------------------------------------------------------------
def manifest(path):
    try:
        with zipfile.ZipFile(path) as z:
            return json.loads(z.read("manifest.json").decode("utf-8"))
    except (OSError, KeyError, ValueError, zipfile.BadZipFile):
        return None


def listing(dest=None):
    dest = Path(dest) if dest else folder()
    if not dest.is_dir():
        return []
    out = []
    for p in dest.glob("Claude Timeline *.zip"):
        m = manifest(p)
        if m is not None:
            out.append((p, m))
    out.sort(key=lambda t: t[1].get("made", ""), reverse=True)
    return out


# ---- restoring -------------------------------------------------------------------------------------------------
def restore(path, parts, progress=None, safety=True):
    """Put those parts back from the backup. First a safety backup of what's there now (in the same folder); then
    each part's folders are set aside, the backup's copy unpacked, and the old copy deleted only once that worked.
    Returns the safety backup's path (or None)."""
    m = manifest(path) or {}
    parts = [p for p in parts if p in PARTS and p in m.get("parts", [])]
    if not parts:
        return None
    safe = create(parts, Path(path).parent, label="pre-restore") if safety else None
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n != "manifest.json"]
        for part in parts:
            roots = PARTS[part][1]
            mine = [n for n in names if any(n == r or n.startswith(r.rstrip("/") + "/") for r in roots)]
            aside = []
            try:
                for r in roots:
                    target = TIMELINE / r
                    if target.exists():
                        held = target.with_name(target.name + f".restoring-{int(time.time())}")
                        target.rename(held)
                        aside.append((target, held))
                for i, n in enumerate(mine):
                    out = TIMELINE / n
                    if ".." in Path(n).parts:
                        continue
                    out.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(n) as src, open(out, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    if progress:
                        progress(i + 1, len(mine), n)
            except BaseException:
                for target, held in aside:           # put the old copy back
                    if target.exists():
                        shutil.rmtree(target, ignore_errors=True) if target.is_dir() else target.unlink()
                    held.rename(target)
                raise
            for _target, held in aside:
                if held.is_dir():
                    shutil.rmtree(held, ignore_errors=True)
                else:
                    try:
                        held.unlink()
                    except OSError:
                        pass
    return safe
