"""Automatic version history: a snapshot of a program before the AI changes it, before it runs, and when it is saved."""
import hashlib
import time
from pathlib import Path

KEEP = 40


def history_dir(path):
    path = Path(path)
    return path.parent / ".history" / path.name


def snapshot(path, text, reason="save"):
    """Remember `text` as a version of the file at `path`. Skips empty text and repeats of the newest version."""
    if not path or not text.strip():
        return None
    folder = history_dir(path)
    try:
        folder.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
        newest = versions(path)[:1]
        if newest and newest[0][0].stem.rsplit("_", 1)[-1] == digest:
            return None
        stamp = time.strftime("%Y%m%d-%H%M%S")
        target = folder / f"{stamp}_{reason}_{digest}.py.txt"
        target.write_text(text, encoding="utf-8", newline="\n")
        for old in versions(path)[KEEP:]:
            old[0].unlink(missing_ok=True)
        return target
    except OSError:
        return None


def versions(path):
    """[(file, label)] newest first."""
    folder = history_dir(path)
    if not folder.is_dir():
        return []
    out = []
    for f in sorted(folder.glob("*.py.txt"), reverse=True):
        parts = f.name.split("_")
        try:
            when = time.strftime("%d %b %Y  %H:%M:%S", time.strptime(parts[0], "%Y%m%d-%H%M%S"))
        except ValueError:
            when = parts[0]
        reason = {"ai": "before an AI change", "run": "when run", "save": "when saved", "debug": "when debugged",
                  "restore": "before a restore", "tidy": "before tidying"}.get(parts[1] if len(parts) > 2 else "", "")
        out.append((f, f"{when}   {reason}".strip()))
    return out
