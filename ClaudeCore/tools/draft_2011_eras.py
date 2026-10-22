"""Draft Residents/<Name>/eras/2011.json for everyone who has a 2001 era and no 2011 one yet.

Ten years on: every age in the persona and the profile goes up by ten, the accounts and schedules are carried over,
and a paragraph says what 2011 is like for them. The file is marked "drafted" so the hand-written version can replace
it later; nothing already there is overwritten unless --force is given.

    python draft_2011_eras.py            everyone without a 2011 era
    python draft_2011_eras.py --force    everyone (rewrites drafted files too, never hand-edited ones)
    python draft_2011_eras.py Antler RedFawks
    python draft_2011_eras.py --apply drafts/main_2011_2026-10-22.json
        a drafts file: {name: {"era": {occupation, work_schedule, sleep_schedule, residence, location, timezone},
        "persona": the whole 2011 persona, "profile": the AIM profile, "history": [...]}} - the era fields and
        the persona go into eras/2011.json (every service's persona too), the history into resident.json
"""
import copy
import json
import re
import sys
from datetime import date
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
RESIDENTS = TIMELINE / "Residents"
FROM, TO = 2001, 2011
AGE_RE = re.compile(r"\b(\d{1,2})(-| )year(-| )old\b")
YOURE_RE = re.compile(r"\b(You're|you're|You are|I'm|I am)\s+(\d{2})\b")
YO_RE = re.compile(r"\b(\d{2})\s?[Yy][Oo]\b")
AGED_RE = re.compile(r"\b(aged|age)\s+(\d{2})\b")
NOTE = ("\n\nIt's October 2011 now, ten years on from the AIM days: you're {age}. The old messengers are still "
        "running (and Skype, and Facebook on the side), your phone does e-mail, and you still log on to see the same "
        "crowd. Your life has moved on in small ways, but you're the same person at heart. Don't mention anything "
        "that happens after 2011.")


def bump(text, by=TO - FROM):
    if not text:
        return text
    text = AGE_RE.sub(lambda m: f"{int(m.group(1)) + by}{m.group(2)}year{m.group(3)}old", text)
    text = YOURE_RE.sub(lambda m: f"{m.group(1)} {int(m.group(2)) + by}", text)
    text = YO_RE.sub(lambda m: f"{int(m.group(1)) + by} Yo", text)
    text = AGED_RE.sub(lambda m: f"{m.group(1)} {int(m.group(2)) + by}", text)
    return text


def age_in(core, year):
    try:
        born = date.fromisoformat(core.get("born", ""))
    except ValueError:
        return None
    snap = date(year, 10, 15)
    return snap.year - born.year - ((snap.month, snap.day) < (born.month, born.day))


def draft(name, force=False):
    folder = RESIDENTS / name
    core_path, src, dst = folder / "resident.json", folder / "eras" / f"{FROM}.json", folder / "eras" / f"{TO}.json"
    if not core_path.exists() or not src.exists():
        return "skipped (no 2001 era)"
    if dst.exists():
        existing = json.loads(dst.read_text(encoding="utf-8"))
        if not force or "drafted" not in existing:
            return "kept"
    core = json.loads(core_path.read_text(encoding="utf-8"))
    era = copy.deepcopy(json.loads(src.read_text(encoding="utf-8")))
    age = age_in(core, TO)
    note = NOTE.format(age=age if age is not None else "ten years older")
    era["year"] = TO
    era["persona"] = bump(era.get("persona", "")) + note
    for key, svc in (era.get("services") or {}).items():
        if not isinstance(svc, dict):
            continue
        if svc.get("persona"):
            svc["persona"] = bump(svc["persona"]) + note
        if svc.get("profile"):
            svc["profile"] = bump(svc["profile"])
        if svc.get("away_message"):
            svc["away_message"] = bump(svc["away_message"])
        for trig in svc.get("triggers") or []:
            if isinstance(trig, dict) and trig.get("prompt"):
                trig["prompt"] = bump(trig["prompt"])
    if core.get("tier") == "main" and "skype" not in (era.get("services") or {}):
        era.setdefault("services", {})["skype"] = {"handle": name.lower()}
    era["drafted"] = {"date": date.today().isoformat(), "from": FROM,
                      "note": "ages +10 and a 2011 paragraph; everything else carried from 2001 - please review"}
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(era, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return "drafted"


def apply_drafts(path):
    drafts = json.loads(Path(path).read_text(encoding="utf-8"))
    done = 0
    for name, d in drafts.items():
        if name.startswith("_"):
            continue
        folder = RESIDENTS / name
        core_path, era_path = folder / "resident.json", folder / "eras" / f"{TO}.json"
        if not era_path.exists():
            print(f"  skip {name}: no {TO} era (run the draft first)")
            continue
        era = json.loads(era_path.read_text(encoding="utf-8"))
        for key, value in (d.get("era") or {}).items():
            if value:
                era[key] = value
        persona = d.get("persona")
        if persona:
            era["persona"] = persona
            for svc in (era.get("services") or {}).values():
                if isinstance(svc, dict) and svc.get("persona"):
                    svc["persona"] = persona
        profile = d.get("profile")
        aim = (era.get("services") or {}).get("aim")
        if profile and isinstance(aim, dict):
            aim["profile"] = profile
        era["drafted"] = {"date": date.today().isoformat(), "from": FROM,
                          "note": f"{TO} life drafted by hand from {Path(path).name}; please review"}
        era_path.write_text(json.dumps(era, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if d.get("history") and core_path.exists():
            core = json.loads(core_path.read_text(encoding="utf-8"))
            history = core.setdefault("history", [])
            known = {h.get("text") for h in history}
            for h in d["history"]:
                if h.get("text") not in known:
                    history.append(h)
            core_path.write_text(json.dumps(core, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        done += 1
    print(f"{done} residents updated from {Path(path).name}")


OPENERS = ["It's October 2011 now, ten years on from the AIM days: you're {age}.",
           "Ten years have gone by since 2001; it's October 2011 and you're {age}.",
           "It's the autumn of 2011. You're {age} now, and the AIM days feel a long time ago.",
           "It's 2011 - October, to be exact - and you're {age}, ten years older than when you first logged on."]
WORK = {
    "retired": ["Retirement suits you; your days are your own.", "You're still retired, and still busy with your own things."],
    "none": ["You've had a few jobs since 2001 and you're between them again just now, so you're online a lot.",
             "Work has come and gone over the years; right now you're not working, which leaves plenty of time online."],
    "student": ["You finished your studies years ago and found work in your field, on much the same hours.",
                "You graduated a long time ago now; the job you found keeps the same odd hours you always kept."],
    "other": ["You're still {a} {occupation}, with a bit more responsibility than you had in 2001.",
              "The job hasn't changed much: {a} {occupation}, the same sort of hours.",
              "You've stuck with being {a} {occupation}; you're one of the experienced ones now.",
              "You're {a} {occupation} these days too, same line of work, a few more grey hairs."],
}
TECH = ["You've got a smartphone that does e-mail and Facebook, but you still log on from the PC in the evenings.",
        "Facebook and Skype sit beside the old messengers now, and you check Fur Affinity most days.",
        "You tweet now and then, mostly about work and the fandom, and you keep up with friends on Facebook.",
        "You never took to Facebook much; IRC and the MUCK are still home, with Skype for the people who left.",
        "You read everyone's LiveJournals less than you used to and their Facebook walls more."]
FANDOM = ["You've been to a handful of furry conventions over the years.",
          "You still haven't got a fursuit, and you're fine with that.",
          "The fandom is far bigger than it was, and you like that the old crowd is still around.",
          "You commission art of your fursona when you can afford it.",
          "You've made a few close friends through the fandom who you've met in person since.",
          "Most of your furry life is still online, the way it always was."]
CLOSER = ("Your life has moved on in small ways, but you're the same person at heart. Don't mention anything that "
          "happens after 2011.")


def _work_class(occupation):
    o = (occupation or "").lower().strip()
    if not o or any(k in o for k in ("no current", "between jobs", "not working", "unemployed", "none at present",
                                    "none")):
        return "none"
    if "retired" in o:
        return "retired"
    if "student" in o:
        return "student"
    return "other"


def _article(word):
    return "an" if word[:1].lower() in "aeiou" else "a"


def varied_paragraph(name, era, age):
    """A 2011 paragraph of this resident's own (the same one every time, picked by their name)."""
    import hashlib
    h = int(hashlib.md5(name.encode()).hexdigest(), 16)
    pick = lambda seq, k: seq[(h >> (k * 5)) % len(seq)]
    occupation = (era.get("occupation") or "").strip().rstrip(".")
    cls = _work_class(occupation)
    work = pick(WORK[cls], 1).format(a=_article(occupation), occupation=occupation.lower() if occupation[:1].isupper()
                                      and not occupation.isupper() else occupation)
    return "\n\n" + " ".join([pick(OPENERS, 0).format(age=age if age is not None else "ten years older"), work,
                              pick(TECH, 2), pick(FANDOM, 3), CLOSER])


def vary_all(force=False):
    """Give every resident with the generic 2011 paragraph their own variation (hand-drafted ones are left alone)."""
    changed = 0
    for folder in sorted(p for p in RESIDENTS.iterdir() if (p / "resident.json").exists()):
        era_path = folder / "eras" / f"{TO}.json"
        if not era_path.exists():
            continue
        era = json.loads(era_path.read_text(encoding="utf-8"))
        drafted = era.get("drafted") or {}
        if "by hand" in drafted.get("note", "") or (drafted.get("varied") and not force):
            continue
        core = json.loads((folder / "resident.json").read_text(encoding="utf-8"))
        age = age_in(core, TO)
        generic = NOTE.format(age=age if age is not None else "ten years older")
        new = varied_paragraph(folder.name, era, age)
        hit = False
        for holder in [era] + [s for s in (era.get("services") or {}).values() if isinstance(s, dict)]:
            if holder.get("persona") and generic in holder["persona"]:
                holder["persona"] = holder["persona"].replace(generic, new)
                hit = True
        if hit:
            era["drafted"] = dict(drafted, varied=True, date=date.today().isoformat(),
                                  note="ages +10 and a 2011 paragraph of their own; everything else carried from 2001 - please review")
            era_path.write_text(json.dumps(era, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            changed += 1
    print(f"{changed} residents given their own 2011 paragraph")


def main(argv):
    if "--apply" in argv:
        apply_drafts(argv[argv.index("--apply") + 1])
        return
    if "--vary" in argv:
        vary_all(force="--force" in argv)
        return
    force = "--force" in argv
    names = [a for a in argv if not a.startswith("--")]
    if not names:
        names = sorted(p.name for p in RESIDENTS.iterdir() if (p / "resident.json").exists())
    counts = {}
    for name in names:
        result = draft(name, force=force)
        counts[result] = counts.get(result, 0) + 1
    print(", ".join(f"{v} {k}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main(sys.argv[1:])
