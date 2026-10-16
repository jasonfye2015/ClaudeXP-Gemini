"""Fill residents' empty fields from a drafts file (ClaudeCore/tools/drafts/*.json), never overwriting anything.

Each resident gets "drafted": {"date", "fields"} listing what was filled, and a review flag, so drafted details are
easy to find and check. History entries are added if the resident has none.
Usage: python apply_drafts.py drafts/<file>.json
"""
import json
import sys
from datetime import date
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
RESIDENTS = TIMELINE / "Residents"
ERA_FIELDS = ("occupation", "work_schedule", "sleep_schedule", "residence", "location")
FLAG = "drafted-details: some details were drafted, please review (see \"drafted\")"


def fill(target, source, prefix, filled):
    """Copy source's values into target wherever target is empty."""
    for key, value in source.items():
        if isinstance(value, dict):
            sub = target.setdefault(key, {})
            if isinstance(sub, dict):
                fill(sub, value, f"{prefix}{key}.", filled)
        elif value and not target.get(key):
            target[key] = value
            filled.append(prefix + key)


def apply(path):
    drafts = json.loads(Path(path).read_text(encoding="utf-8"))
    for name, d in drafts.items():
        if name.startswith("_"):
            continue
        folder = RESIDENTS / name
        rp, ep = folder / "resident.json", folder / "eras" / "2001.json"
        if not rp.exists():
            print(f"  skip {name}: no resident folder")
            continue
        r = json.loads(rp.read_text(encoding="utf-8"))
        e = json.loads(ep.read_text(encoding="utf-8")) if ep.exists() else {}
        filled = []
        fill(r, {k: v for k, v in d.items() if k not in ("era", "history")}, "", filled)
        era_filled = []
        fill(e, {k: v for k, v in (d.get("era") or {}).items() if k in ERA_FIELDS}, "", era_filled)
        filled += [f"eras/2001.{f}" for f in era_filled]
        if d.get("history") and not r.get("history"):
            r["history"] = d["history"]
            filled.append("history")
        if filled:
            r["drafted"] = {"date": date.today().isoformat(),
                            "fields": sorted(set((r.get("drafted") or {}).get("fields", []) + filled))}
            if FLAG not in r.get("flags", []):
                r.setdefault("flags", []).append(FLAG)
        rp.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if ep.exists():
            ep.write_text(json.dumps(e, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  {name}: filled {len(filled)} fields")


if __name__ == "__main__":
    apply(sys.argv[1])
