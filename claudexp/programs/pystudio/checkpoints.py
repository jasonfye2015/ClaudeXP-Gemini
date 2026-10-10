"""Named project checkpoints for Copilot Python Studio: a labelled copy of every program (and small data file) in the
project folder, so you can try something risky and roll the whole project back. No Qt in this module."""
import json
import re
import shutil
import time
from pathlib import Path

FOLDER = ".checkpoints"
TEXT_EXT = {".py", ".json", ".csv", ".txt", ".tmx", ".md", ".ini", ".cfg"}
SKIP_DIRS = {".history", FOLDER, "__pycache__", "Built Programs", "build", "dist", ".git", "venv", ".venv",
             ".pytest_cache"}
MAX_FILE = 1_000_000
MAX_FILES = 400
KEEP_AUTO = 8


def tracked(root):
    """{relative posix path: Path} of the files a checkpoint covers. Assets are skipped except Assets/Maps."""
    root = Path(root)
    found = {}
    for p in sorted(root.rglob("*")):
        if len(found) >= MAX_FILES:
            break
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        parts = rel.parts
        if any(part in SKIP_DIRS or part.startswith(".") for part in parts[:-1]):
            continue
        if parts[0] == "Assets" and not (len(parts) > 2 and parts[1] == "Maps"):
            continue
        if p.is_file() and p.suffix.lower() in TEXT_EXT:
            try:
                if p.stat().st_size <= MAX_FILE:
                    found[rel.as_posix()] = p
            except OSError:
                pass
    return found


def _slug(name):
    return re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()[:30] or "checkpoint"


def folder(root):
    return Path(root) / FOLDER


def create(root, name, auto=False):
    """Copy the project into a new checkpoint and return its info dict (see `listing`)."""
    root = Path(root)
    name = name.strip() or "Checkpoint"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    cid = f"{stamp}_{_slug(name)}"
    target = folder(root) / cid
    n = 1
    while target.exists():
        n += 1
        cid = f"{stamp}_{_slug(name)}-{n}"
        target = folder(root) / cid
    files = tracked(root)
    for rel, src in files.items():
        dest = target / "files" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    meta = {"name": name, "when": time.strftime("%d %b %Y  %H:%M:%S"), "auto": auto, "files": sorted(files)}
    (target / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    if auto:
        for old in [c for c in listing(root) if c["auto"]][KEEP_AUTO:]:
            delete(root, old["id"])
    return {"id": cid, **meta}


def listing(root):
    """Checkpoints, newest first: dicts with id, name, when, auto, files."""
    base = folder(root)
    out = []
    if base.is_dir():
        for d in sorted(base.iterdir(), reverse=True):
            try:
                meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            out.append({"id": d.name, "name": meta.get("name", d.name), "when": meta.get("when", ""),
                        "auto": bool(meta.get("auto")), "files": meta.get("files", [])})
    return out


def saved_text(root, cid, rel):
    try:
        return (folder(root) / cid / "files" / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def changes(root, cid):
    """[(relative path, status)] comparing the checkpoint with the folder now. Status is "changed", "deleted" (it was
    in the checkpoint but is gone now) or "new" (it exists now but not in the checkpoint). Unchanged files are left out."""
    root = Path(root)
    cp = next((c for c in listing(root) if c["id"] == cid), None)
    if cp is None:
        return []
    now = tracked(root)
    out = []
    for rel in cp["files"]:
        if rel not in now:
            out.append((rel, "deleted"))
        elif _read(now[rel]) != saved_text(root, cid, rel):
            out.append((rel, "changed"))
    out += [(rel, "new") for rel in sorted(now) if rel not in cp["files"]]
    return sorted(out)


def _read(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def restore(root, cid, only=None, remove_new=False):
    """Put the checkpoint's files back. `only` limits it to those relative paths; `remove_new` also deletes files that
    did not exist at the time (only when restoring everything). Returns the relative paths that were written or
    removed. Take your own checkpoint first if you may want the current state back."""
    root = Path(root)
    done = []
    for rel, status in changes(root, cid):
        if only is not None and rel not in only:
            continue
        target = root / rel
        if status == "new":
            if remove_new and only is None:
                target.unlink(missing_ok=True)
                done.append(rel)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(folder(root) / cid / "files" / rel, target)
        done.append(rel)
    return done


def delete(root, cid):
    shutil.rmtree(folder(root) / cid, ignore_errors=True)
