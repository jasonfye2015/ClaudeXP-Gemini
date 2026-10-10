"""Remembers the last few program runs (output and the code that ran) so you can look back. No Qt here."""
import difflib
import json
import time
from pathlib import Path

from ...paths import DATA

FILE = DATA / "pystudio_runs.json"
KEEP = 20
MAX_OUTPUT = 30000
MAX_SOURCE = 200000


def load():
    try:
        data = json.loads(Path(FILE).read_text(encoding="utf-8"))
        return [r for r in data if isinstance(r, dict) and "file" in r]
    except Exception:
        return []


def _save(records):
    try:
        Path(FILE).parent.mkdir(parents=True, exist_ok=True)
        Path(FILE).write_text(json.dumps(records), encoding="utf-8")
    except OSError:
        pass


def add(file, kind, exit_code, stopped, seconds, output, source):
    """Appends a record (newest last) and keeps only the latest KEEP. Returns the record."""
    output = output or ""
    if len(output) > MAX_OUTPUT:
        output = "...(earlier output cut)\n" + output[-MAX_OUTPUT:]
    record = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "file": str(file), "kind": kind, "exit": exit_code,
              "stopped": bool(stopped), "seconds": round(float(seconds), 1), "output": output,
              "source": (source or "")[:MAX_SOURCE]}
    records = load()
    records.append(record)
    _save(records[-KEEP:])
    return record


def clear():
    _save([])


def ok(record):
    return record.get("exit") == 0 and not record.get("stopped")


def label(record):
    mark = "\u25A0" if record.get("stopped") else ("\u2714" if ok(record) else "\u2718")
    name = Path(record["file"]).name
    return f"{record['time'][5:16]}  {mark} {record['kind']}  {name}  ({record['seconds']} s)"


def previous_same(records, index):
    """Index of the run before `index` of the same file and kind, or None."""
    rec = records[index]
    for j in range(index - 1, -1, -1):
        if records[j]["file"] == rec["file"] and records[j]["kind"] == rec["kind"]:
            return j
    return None


def last_good_before(records, index):
    """Index of the most recent successful run of the same file before `index`, or None."""
    rec = records[index]
    for j in range(index - 1, -1, -1):
        r = records[j]
        if r["file"] == rec["file"] and r["kind"] == rec["kind"] and ok(r):
            return j
    return None


def code_diff(old, new, old_name="before", new_name="after", limit=8000):
    """A readable diff, or '' when identical."""
    rows = difflib.unified_diff((old or "").splitlines(), (new or "").splitlines(), old_name, new_name,
                                lineterm="", n=2)
    text = "\n".join(rows)
    return text if len(text) <= limit else text[:limit] + "\n...(diff cut)"


def why_prompt(records, index):
    """The question for 'what changed since it last worked?', or None when there is no earlier good run."""
    good = last_good_before(records, index)
    if good is None or ok(records[index]):
        return None
    bad, old = records[index], records[good]
    diff = code_diff(old["source"], bad["source"], f"worked {old['time']}", f"failed {bad['time']}")
    out = bad["output"].strip()[-2500:]
    if not diff:
        diff = "(the code is identical, so the cause is outside this file: its inputs, other files or the data)"
    return ("My program "
            f"{Path(bad['file']).name} worked at {old['time']} but failed at {bad['time']}. I am a beginner. "
            "Explain in simple words which change most likely caused the problem and how to fix it. Do not rewrite "
            f"my whole program.\n\nWhat I changed (diff):\n```diff\n{diff}\n```\n\nThe error:\n```\n{out}\n```")
