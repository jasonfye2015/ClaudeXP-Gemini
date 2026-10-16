"""Build Claude Timeline/Residents from ClaudeXP's scattered resident files (ClaudeXP itself is only read).

Sources, per resident:
  - Program Files/ClaudeAIM/contacts/<Name>.json        the AIM contact (main furs), its picture folder <Name>/ and
    <Name>.txt character profile; the buddy icon in Program Files/ClaudeAIM/assets/icons/
  - Program Files/The Fur Directory/residents/<Name>.json   the directory record (everyone)
  - Program Files/ClaudeIRC/regulars.json, Program Files/ClaudeMUCK/world/regulars.json
  - ClaudeXP Profiles/{Support,Background} Furry Profiles/<n>_<Name>.txt   the original character profiles

Usage: python migrate_xp_residents.py [--force]   (from anywhere; paths are found from this file)
"""
import hashlib
import json
import random
import re
import shutil
import sys
from datetime import date
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
XP = TIMELINE / "ClaudeXP"
OUT = TIMELINE / "Residents"
AIM = XP / "Program Files" / "ClaudeAIM" / "contacts"
AIM_ICONS = XP / "Program Files" / "ClaudeAIM" / "assets" / "icons"
DIRECTORY = XP / "Program Files" / "The Fur Directory"
IRC = XP / "Program Files" / "ClaudeIRC" / "regulars.json"
MUCK = XP / "Program Files" / "ClaudeMUCK" / "world" / "regulars.json"
PROFILES = XP / "ClaudeXP Profiles"
ERA = 2001
TODAY = "2026-10-17"

HEADER = re.compile(r"^\*\*(.+?):\*\*\s*(.*?)\s*$")
SECTION = re.compile(r"^##\s+(.+?)\s*$")
AGE = re.compile(r"\b(\d{2})\s*(?:-?\s*year[- ]old|yo\b|y/o|years old)|\byou'?re (\d{2})\b", re.I)
MET = re.compile(r"[^.]*\b(?:met|know|known)\b[^.]*\b(?:buddy|the user|you)\b[^.]*\.|[^.]*\byour buddy\b[^.]*\bmet\b[^.]*\.",
                 re.I)


def load(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def parse_profile(text):
    """The '## Character Profile' markdown: header fields, then sections."""
    head, sections, current = {}, {}, None
    for line in text.splitlines():
        m = SECTION.match(line)
        if m:
            current = m.group(1).strip()
            sections[current] = []
            continue
        if current in (None, "Character Profile"):
            h = HEADER.match(line)
            if h:
                head[h.group(1).strip().lower()] = h.group(2).strip()
                continue
        if current:
            sections[current].append(line)
    out = {k: "\n".join(v).strip() for k, v in sections.items()}
    short = re.search(r"\*\*In short:\*\*\s*(.+)", text)
    return head, out, short.group(1).strip() if short else ""


def stable_rng(name):
    return random.Random(int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:12], 16))


def born_date(name, year):
    """A birthday in `year` that has already passed by the mid-October snapshot, so the age comes out right."""
    rnd = stable_rng(name + ":day")
    month = rnd.randint(1, 10)
    return date(year, month, rnd.randint(1, 15 if month == 10 else 28)).isoformat()


def section(sections, *names):
    for n in names:
        for k, v in sections.items():
            if k.lower().startswith(n.lower()) and v:
                return v
    return ""


def first(*values):
    return next((v for v in values if v), "")


def main(force=False):
    records = {p.stem: load(p, {}) for p in sorted((DIRECTORY / "residents").glob("*.json"))}
    irc = {r["nick"]: r for r in load(IRC, {}).get("regulars", [])}
    muck = {r["name"]: r for r in load(MUCK, {}).get("regulars", [])}
    profiles = {}
    for p in PROFILES.rglob("*.txt"):
        profiles[re.sub(r"^\d+_", "", p.stem)] = (p, "support" if "Support" in p.parent.name else "background")
    made, skipped, flagged = 0, 0, []
    for name, rec in records.items():
        folder = OUT / name
        if folder.exists() and not force:
            skipped += 1
            continue
        if folder.exists():
            shutil.rmtree(folder)
        aim = load(AIM / f"{name}.json")
        profile_path = AIM / f"{name}.txt" if (AIM / f"{name}.txt").exists() else profiles.get(name, (None,))[0]
        head, sections, short = parse_profile(profile_path.read_text(encoding="utf-8", errors="replace")) \
            if profile_path else ({}, {}, "")
        personal = rec.get("personal") or {}
        sona = rec.get("fursona") or {}
        personas = [x for x in ((aim or {}).get("persona"), (irc.get(name) or {}).get("persona"),
                                (muck.get(name) or {}).get("persona")) if x]
        flags = []

        # birth date: the profile's DOB, else an age in a persona, else assigned (an adult in 2001)
        dob = head.get("dob", "")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", dob):
            born, source = dob, "profile"
        else:
            texts = personas + [(aim or {}).get("profile", "")]
            ages = [int(next(g for g in m.groups() if g)) for t in texts for m in AGE.finditer(t)]
            if ages:
                age = ages[0]
                if age < 18:
                    flags.append(f"minor-in-persona: their 2001 text says {age}; given an adult birth date instead")
                    age = stable_rng(name).randint(19, 23)
                born, source = born_date(name, ERA - age), "persona"
            else:
                born, source = born_date(name, ERA - stable_rng(name).randint(21, 40)), "assigned"

        # tier: the record's, else AIM = main, else the profile folder's, else a chatting IRC/MUCK regular is support
        # (bots stay background), else background - The Fur Directory's own rule
        tier = rec.get("tier") or ("main" if aim else profiles.get(name, (None, ""))[1] or (
            "support" if (name in irc or name in muck) and "bot" not in name.lower() else "background"))
        how_met = ""
        for t in personas:
            m = MET.search(t)
            if m:
                how_met = m.group(0).strip()
                break
        resident = {
            "name": name,
            "fur_name": rec.get("fur_name") or head.get("full character name") or name,
            "tier": tier,
            "born": born,
            "born_source": source,
            "identity": {"real_name": first(personal.get("real_name"), head.get("real name")),
                         "gender": first(personal.get("sex"), head.get("gender")),
                         "pronouns": head.get("pronouns", ""), "height": head.get("height", ""),
                         "build": head.get("build", "")},
            "fursona": {"species": first(sona.get("species"), head.get("species")),
                        "colors": first(sona.get("colors"), head.get("fur / coat / scales / feathers")),
                        "eyes": head.get("eyes", ""),
                        "markings": first(sona.get("markings"), head.get("distinguishing features")),
                        "accessories": first(sona.get("clothing"), head.get("accessories")),
                        "description": first(sona.get("description"), section(sections, "Description"))},
            "summary": first(rec.get("summary"), short),
            "personality": first(rec.get("personality"), section(sections, "Personality")),
            "mannerisms": first(rec.get("mannerisms"), section(sections, "Mannerisms")),
            "interests": first(rec.get("interests"), section(sections, "Interests")),
            "roleplay_hooks": first(rec.get("roleplay_hooks"), section(sections, "Roleplay Hooks")),
            "roleplay_notes": first(rec.get("roleplay_notes"), section(sections, "Roleplay Notes")),
            "favorites": rec.get("favorites") or {},
            "how_met": how_met,
            "relationship": rec.get("relationship") or {},
            "friends": rec.get("friends") or [],
            "relationships": rec.get("relationships") or [],
            "notes": rec.get("notes") or "",
            "history": [],
            "flags": flags,
        }
        services = {}
        if aim:
            services["aim"] = aim
        if name in irc:
            services["irc"] = irc[name]
        if name in muck:
            services["muck"] = muck[name]
        directory = {k: rec[k] for k in ("screen_names", "webpages", "files", "icon") if rec.get(k)}
        if directory:
            services["directory"] = directory
        era = {
            "year": ERA,
            "persona": personas[0] if personas else "",
            "occupation": first(personal.get("job"), head.get("occupation")),
            "work_schedule": first(personal.get("work_hours"), head.get("work schedule")),
            "sleep_schedule": first(personal.get("sleep_hours"), head.get("sleep schedule")),
            "residence": first(personal.get("residence"), head.get("residence")),
            "location": personal.get("location", ""),
            "timezone": (aim or {}).get("timezone", ""),
            "services": services,
        }
        (folder / "eras").mkdir(parents=True)
        (folder / "resident.json").write_text(json.dumps(resident, indent=2, ensure_ascii=False) + "\n", "utf-8")
        (folder / "eras" / f"{ERA}.json").write_text(json.dumps(era, indent=2, ensure_ascii=False) + "\n", "utf-8")
        # media: the buddy icon, the AIM picture folder (photos and captions), a directory icon
        media = folder / "media" / str(ERA)
        if aim and aim.get("icon") and (AIM_ICONS / aim["icon"]).exists():
            media.mkdir(parents=True, exist_ok=True)
            shutil.copy2(AIM_ICONS / aim["icon"], media / aim["icon"])
        if (AIM / name).is_dir():
            shutil.copytree(AIM / name, media, dirs_exist_ok=True)
        if rec.get("icon") and (DIRECTORY / rec["icon"]).exists():
            media.mkdir(parents=True, exist_ok=True)
            shutil.copy2(DIRECTORY / rec["icon"], media / Path(rec["icon"]).name)
        # sources, for reference
        src = folder / "sources"
        src.mkdir()
        if profile_path:
            shutil.copy2(profile_path, src / "character_profile.txt")
        shutil.copy2(DIRECTORY / "residents" / f"{name}.json", src / "fur_directory_record.json")
        made += 1
        if flags:
            flagged.append((name, flags))
    print(f"made {made}, kept {skipped} existing (use --force to rebuild them)")
    for name, flags in flagged:
        print(f"  FLAG {name}: {'; '.join(flags)}")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
