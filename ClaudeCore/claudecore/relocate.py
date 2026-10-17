"""Keeping a computer's saved paths right when the Claude Timeline moves (the Desktop, an external SSD as F:, another
PC where that drive is E:...).

Programs save some full paths (Doom's recent WADs, the Recycle Bin's original locations, ClaudeTV's index). At
startup a computer calls fix(its data folder): if the Timeline was somewhere else last time, every saved path under
the old folder is pointed at the new one. Text files only (.json, .ini, .txt, .cfg); a small marker
(timeline_root.txt) remembers where the Timeline was.
"""
import json
import re
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
MARKER = "timeline_root.txt"
EXTS = {".json", ".ini", ".txt", ".cfg"}
MAX_SIZE = 32 * 1024 * 1024


def _named(name):
    """A full Windows path ending in a folder of this name (for data saved before the marker existed)."""
    return re.compile(r"[A-Za-z]:(?:\\\\|\\|/)(?:[^\\/:*?\"<>|\r\n]+(?:\\\\|\\|/))*?" + re.escape(name)
                      + r"(?=\\|/|\"|$)", re.M)


def _forms(root):
    """A folder as it can appear in a file: plain (C:\\x), JSON-escaped (C:\\\\x) and with forward slashes."""
    plain = str(root)
    return [json.dumps(plain)[1:-1], plain, plain.replace("\\", "/")]


def _rewrite(text, old_roots, new):
    new_forms = _forms(new)
    for old in old_roots:
        if Path(old) == new:
            continue
        for old_form, new_form in zip(_forms(old), new_forms):
            text = text.replace(old_form, new_form)

    def named(m):
        found = m.group(0)
        if found.replace("\\\\", "\\").replace("/", "\\").lower() == str(new).lower():
            return found
        if "\\\\" in found:
            return new_forms[0]
        return new_forms[2] if "/" in found else new_forms[1]
    return _named(new.name).sub(named, text)


def fix(data_dir, timeline=TIMELINE):
    """Point saved paths in data_dir at where the Timeline is now. Returns the files changed."""
    data_dir, timeline = Path(data_dir), Path(timeline)
    marker = data_dir / MARKER
    try:
        last = marker.read_text(encoding="utf-8").strip()
    except OSError:
        last = ""
    if last and Path(last) == timeline:
        return []
    changed = []
    if data_dir.is_dir():
        for path in data_dir.rglob("*"):
            if path.suffix.lower() not in EXTS or path.name == MARKER or not path.is_file():
                continue
            try:
                if path.stat().st_size > MAX_SIZE:
                    continue
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            new = _rewrite(text, [last] if last else [], timeline)
            if new != text:
                try:
                    path.write_text(new, encoding="utf-8")
                    changed.append(path)
                except OSError:
                    pass
        try:
            marker.write_text(str(timeline), encoding="utf-8")
        except OSError:
            pass
    return changed
