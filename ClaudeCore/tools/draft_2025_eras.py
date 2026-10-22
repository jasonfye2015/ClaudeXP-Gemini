"""Draft Residents/<Name>/eras/2025.json for everyone who has a 2011 era and no 2025 one yet.

Fourteen years on: every age in the persona and the profile goes up by fourteen, the 2011 paragraph at the end of
the persona is replaced by a 2025 one, the accounts and schedules are carried over (Skype is gone - it closed in May
2025 - and the main residents get Telegram and Discord handles), and the file is marked "drafted" so the hand-written
version can replace it later; nothing already there is overwritten unless --force is given.

    python draft_2025_eras.py            everyone without a 2025 era
    python draft_2025_eras.py --force    everyone (rewrites drafted files too, never hand-edited ones)
    python draft_2025_eras.py Antler RedFawks
    python draft_2025_eras.py --vary     give everyone with the generic 2025 paragraph one of their own
    python draft_2025_eras.py --apply drafts/main_2025_2026-10-22.json
        a drafts file: {name: {"era": {occupation, work_schedule, sleep_schedule, residence, location, timezone},
        "persona": the whole 2025 persona, "summary": the one-line 2025 bio, "profile": the messenger profile,
        "history": [...]}} - the era fields, the persona and the summary go into eras/2025.json (every service's
        persona too), the history into resident.json
"""
import copy
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
RESIDENTS = TIMELINE / "Residents"
FROM, TO = 2011, 2025
AGE_RE = re.compile(r"\b(\d{1,2})(-| )year(-| )old\b")
YOURE_RE = re.compile(r"\b(You're|you're|You are|I'm|I am)\s+(\d{2})\b")
YO_RE = re.compile(r"\b(\d{2})\s?[Yy][Oo]\b")
AGED_RE = re.compile(r"\b(aged|age)\s+(\d{2})\b")
GONE = ("skype", "msn", "yim", "icq")           # services that closed between 2011 and 2025
NOTE = ("\n\nIt's October 2025 now, fourteen years on from 2011: you're {age}. The old messengers closed years ago "
        "(AIM in 2017, Skype only this spring); these days you talk on Telegram and Discord, you still log on to IRC "
        "and the MUCK out of habit, and you follow your friends on Bluesky and Fur Affinity. Your phone does "
        "everything, but you still sit down at the PC in the evenings. Your life has moved on - the pandemic years, "
        "a job or two, the fandom grown enormous - but you're the same person at heart. Don't mention anything that "
        "happens after October 2025.")


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


def strip_2011(text):
    """Take the 2011 paragraph off the end of a 2011 persona (the one the 2011 draft or --vary added), and turn the
    hand-written 'It's October 2011.' into something that reads as the past."""
    if not text:
        return text
    paras = text.split("\n\n")
    if len(paras) > 1 and "2011" in paras[-1] and "Don't mention" in paras[-1]:
        paras = paras[:-1]
    out = "\n\n".join(paras)
    out = out.replace("It's October 2011. ", "Back in 2011, ").replace("It's October 2011, and ", "Back in 2011, ")
    out = out.replace("You've known your buddy for ten years", "You've known your buddy for twenty-four years")
    out = out.replace("You've known your buddy for ten years now", "You've known your buddy for twenty-four years now")
    out = out.replace("for fifteen years", "for twenty-nine years")
    return out


def draft(name, force=False):
    folder = RESIDENTS / name
    core_path, src, dst = folder / "resident.json", folder / "eras" / f"{FROM}.json", folder / "eras" / f"{TO}.json"
    if not core_path.exists() or not src.exists():
        return "skipped (no 2011 era)"
    if dst.exists():
        existing = json.loads(dst.read_text(encoding="utf-8"))
        if not force or "drafted" not in existing or "by hand" in (existing.get("drafted") or {}).get("note", ""):
            return "kept"
    core = json.loads(core_path.read_text(encoding="utf-8"))
    era = copy.deepcopy(json.loads(src.read_text(encoding="utf-8")))
    age = age_in(core, TO)
    note = NOTE.format(age=age if age is not None else "fourteen years older")
    era["year"] = TO
    era["persona"] = bump(strip_2011(era.get("persona", ""))) + note
    services = era.get("services") or {}
    for key in list(services):
        if key in GONE:
            del services[key]
    for key, svc in services.items():
        if not isinstance(svc, dict):
            continue
        if svc.get("persona"):
            svc["persona"] = bump(strip_2011(svc["persona"])) + note
        if svc.get("profile"):
            svc["profile"] = bump(svc["profile"])
        if svc.get("away_message"):
            svc["away_message"] = bump(svc["away_message"])
        for trig in svc.get("triggers") or []:
            if isinstance(trig, dict) and trig.get("prompt"):
                trig["prompt"] = bump(trig["prompt"])
    if core.get("tier") == "main":
        handle = name.lower()
        services.setdefault("telegram", {"handle": f"@{handle}"})
        services.setdefault("discord", {"handle": handle})
        services.setdefault("bluesky", {"handle": f"{handle}.bsky.social"})
    era["services"] = services
    era["drafted"] = {"date": date.today().isoformat(), "from": FROM,
                      "note": "ages +14 and a 2025 paragraph; everything else carried from 2011 - please review"}
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
        if d.get("summary"):
            era["summary"] = d["summary"]
        profile = d.get("profile")
        aim = (era.get("services") or {}).get("aim")
        if profile and isinstance(aim, dict):
            aim["profile"] = profile
        for key, value in (d.get("services") or {}).items():
            era.setdefault("services", {})[key] = value
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
            if d.get("relationship"):
                core["relationship"] = d["relationship"]
            core_path.write_text(json.dumps(core, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        done += 1
    print(f"{done} residents updated from {Path(path).name}")


OPENERS = ["It's October 2025 now, fourteen years on from 2011: you're {age}.",
           "Fourteen more years have gone by; it's October 2025 and you're {age}.",
           "It's the autumn of 2025. You're {age} now, and 2001 is a lifetime ago.",
           "It's 2025 - October, to be exact - and you're {age}, twenty-four years older than when you first logged on."]
WORK = {
    "retired": ["You've been retired for years now and your days are your own.",
                "Retirement suits you more every year; you fill the days with your own things."],
    "none": ["Work has come and gone over the years, and right now you're not working, so you're online a lot.",
             "You've had more jobs than you can count since 2001 and you're between them again, which leaves plenty "
             "of time online."],
    "student": ["You've been working in your field for most of twenty years now, on much the same odd hours.",
                "The studies are a distant memory; the job you found afterwards still keeps the same hours."],
    "other": ["You're still {a} {occupation}, one of the old hands now, and you've thought about retiring more than "
              "once.", "The job hasn't changed much in all this time: {a} {occupation}, the same sort of hours, and "
              "you worked from home for a stretch during the pandemic.",
              "You've stuck with being {a} {occupation} all these years; the people you trained are managers now.",
              "You're {a} {occupation} these days too, same line of work, a good deal more grey."],
}
TECH = ["The old messengers closed years ago (AIM in 2017, Skype only this spring); you talk on Telegram and Discord "
        "now, and you still log on to IRC and the MUCK out of habit.",
        "You moved to Telegram when AIM shut down in 2017, you've got a Discord server with the old crowd, and you "
        "follow everyone on Bluesky; IRC and the MUCK are still where you feel most at home.",
        "Your phone does everything, but you still sit down at the PC in the evenings for IRC, the MUCK and Discord. "
        "You left Facebook years ago and never looked back.",
        "Discord is where the old crowd ended up after AIM closed; you post on Bluesky now and then and check Fur "
        "Affinity most days.",
        "You never took to the big social networks; Telegram for the close friends, IRC and the MUCK for everyone "
        "else, and that's enough."]
FANDOM = ["The fandom is enormous now - the cons draw thousands - and you like that the old crowd is still around.",
          "You finally got a fursuit a few years back, and you wear it once a year.",
          "You've been to a dozen furry conventions over the years, fewer since the pandemic.",
          "You commission art of your fursona now and then, and you've kept every piece.",
          "Some of the friends you made online in 2001 you've since met in person; it still feels like a miracle.",
          "Most of your furry life is still online, the way it always was, and you're fine with that."]
CLOSER = ("Your life has moved on - the pandemic years, a job or two, the fandom grown enormous - but you're the same "
          "person at heart. Don't mention anything that happens after October 2025.")


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
    """A 2025 paragraph of this resident's own (the same one every time, picked by their name)."""
    h = int(hashlib.md5((name + "2025").encode()).hexdigest(), 16)
    pick = lambda seq, k: seq[(h >> (k * 5)) % len(seq)]
    occupation = (era.get("occupation") or "").strip().rstrip(".")
    cls = _work_class(occupation)
    work = pick(WORK[cls], 1).format(a=_article(occupation), occupation=occupation.lower() if occupation[:1].isupper()
                                      and not occupation.isupper() else occupation)
    return "\n\n" + " ".join([pick(OPENERS, 0).format(age=age if age is not None else "fourteen years older"), work,
                              pick(TECH, 2), pick(FANDOM, 3), CLOSER])


def vary_all(force=False):
    """Give every resident with the generic 2025 paragraph their own variation (hand-drafted ones are left alone)."""
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
        generic = NOTE.format(age=age if age is not None else "fourteen years older")
        new = varied_paragraph(folder.name, era, age)
        hit = False
        for holder in [era] + [s for s in (era.get("services") or {}).values() if isinstance(s, dict)]:
            if holder.get("persona") and generic in holder["persona"]:
                holder["persona"] = holder["persona"].replace(generic, new)
                hit = True
        if hit:
            era["drafted"] = dict(drafted, varied=True, date=date.today().isoformat(),
                                  note="ages +14 and a 2025 paragraph of their own; everything else carried from 2011 - please review")
            era_path.write_text(json.dumps(era, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            changed += 1
    print(f"{changed} residents given their own 2025 paragraph")


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
