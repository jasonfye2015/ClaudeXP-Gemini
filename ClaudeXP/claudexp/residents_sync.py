"""In the Claude Timeline, Residents/ is where the cast lives; ClaudeXP's own resident files are made from it.

At startup (main.py, before anything reads them) this rebuilds, from each resident's resident.json and eras/2001.json:
  - Program Files/The Fur Directory/residents/<Name>.json     the Fur Directory card
  - Program Files/ClaudeAIM/contacts/<Name>.json, <Name>/      the AIM contact, and its photos and captions
    (and the buddy icon in Program Files/ClaudeAIM/assets/icons/)
  - Program Files/ClaudeIRC/regulars.json, Program Files/ClaudeMUCK/world/regulars.json   the regulars
so every program - AIM and the other messengers, IRC, the MUCK, the Fur Directory, the life simulation, Hotmail -
reads the Timeline's details without changing how it reads. Each persona gets an "About you" block from Residents
(real name, age, home, work, fursona, history with you), so buddies stay consistent with their cards.

Only files whose contents change are written. Outside a Timeline nothing happens: ClaudeXP keeps its own files.
"""
import json
import shutil
import sys
from datetime import date

from .paths import ROOT
from . import timeline

ERA = 2001
AIM = ROOT / "Program Files" / "ClaudeAIM" / "contacts"
AIM_ICONS = ROOT / "Program Files" / "ClaudeAIM" / "assets" / "icons"
RECORDS = ROOT / "Program Files" / "The Fur Directory" / "residents"
IRC = ROOT / "Program Files" / "ClaudeIRC" / "regulars.json"
MUCK = ROOT / "Program Files" / "ClaudeMUCK" / "world" / "regulars.json"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def _residents():
    core = timeline.TIMELINE / "ClaudeCore"
    if not (timeline.TIMELINE / "Residents").is_dir() or not core.is_dir():
        return None
    if str(core) not in sys.path:
        sys.path.insert(0, str(core))
    import residents
    return residents


def _write_json(path, data):
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    try:
        if path.read_text(encoding="utf-8") == text:
            return False
    except OSError:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return True


def _copy_if_changed(src, dst):
    try:
        if dst.exists() and dst.stat().st_size == src.stat().st_size and dst.stat().st_mtime >= src.stat().st_mtime:
            return False
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except OSError:
        return False


# ---- what a persona is told about itself -----------------------------------------------------------------
def about_you(r, buddy=True):
    """A short, factual block from the resident's card, appended to the era persona."""
    core, era = r.core, r.era
    ident, sona = core.get("identity") or {}, core.get("fursona") or {}
    lines = []
    if ident.get("real_name"):
        lines.append(f"Your real name is {ident['real_name']}.")
    if r.born and r.age is not None:
        lines.append(f"You were born on {r.born.day} {MONTHS[r.born.month - 1]} {r.born.year}, so you're {r.age}.")
    if era.get("location") or era.get("residence"):
        where = era.get("location") or era["residence"]
        extra = f" ({era['residence']})" if era.get("location") and era.get("residence") else ""
        lines.append(f"You live in {where}{extra}.")
    if era.get("occupation"):
        work = era["occupation"] + (f" ({era['work_schedule']})" if era.get("work_schedule") else "")
        lines.append(f"Work: {work}.")
    parts = [sona.get("species"), sona.get("colors"), f"{sona['eyes']} eyes" if sona.get("eyes") else "",
             sona.get("markings")]
    looks = ", ".join(x for i, x in enumerate(parts) if x and x.lower() not in [str(y).lower() for y in parts[:i]])
    if looks:
        lines.append(f"Your fursona: {looks}.")
    who = "your buddy" if buddy else "the user"
    for h in r.history_lines():
        lines.append(h.replace("the user", who))
    block = "\n\nAbout you (keep consistent with this):\n- " + "\n- ".join(lines) if lines else ""
    return block + codes_block(r)


# ---- Furry Code and YIFF Code ------------------------------------------------------------------------------------
def codes(r):
    """The resident's codes as this era has them (the Furry Code's age bracket worked out for the era), or {}."""
    c = dict(r.core.get("codes") or {})
    if c.get("furcode"):
        from claudecore.furcodes import furcode
        c["furcode"] = furcode.with_age(c["furcode"], r.age)
    return c


def codes_block(r):
    """What their codes and the user's mean for how they get along (see claudecore.furcodes.steering)."""
    c = codes(r)
    if not c:
        return ""
    from claudecore.furcodes import steering
    me = timeline.profile() or {}
    return steering.about(c, timeline.user_codes(), user=me.get("handle") or me.get("name") or "your buddy")


def shows_yiff(r):
    """Some residents put their YIFF Code in their profiles too (the ones who don't keep it private)."""
    from claudecore.furcodes import yiff_public
    return yiff_public(r.name, codes(r).get("yiffcode", ""), codes(r).get("show_yiff"))


def _profile_with_codes(profile, r):
    c = codes(r)
    if not c.get("furcode"):
        return profile
    extra = f"\n\nFurry Code 2.0: {c['furcode']}"
    if shows_yiff(r):
        extra += f"\n{c['yiffcode']}"
    return (profile or "").rstrip() + extra


# ---- the Fur Directory card --------------------------------------------------------------------------------
def _record(r):
    core, era = r.core, r.era
    ident, sona = core.get("identity") or {}, core.get("fursona") or {}
    directory = (era.get("services") or {}).get("directory") or {}
    born = r.born
    rec = {
        "fur_name": core.get("fur_name") or r.name,
        "tier": core.get("tier", ""),
        "summary": core.get("summary", ""),
        "screen_names": directory.get("screen_names") or {"aim": "", "irc": "", "muck": "", "email": ""},
        "personal": {"real_name": ident.get("real_name", ""), "location": era.get("location", ""),
                     "residence": era.get("residence", ""), "sex": ident.get("gender", ""),
                     "pronouns": ident.get("pronouns", ""), "age": "",
                     "dob": f"{born.month}/{born.day}/{born.year}" if isinstance(born, date) else "",
                     "height": ident.get("height", ""), "job": era.get("occupation", ""),
                     "work_hours": era.get("work_schedule", ""), "sleep_hours": era.get("sleep_schedule", "")},
        "favorites": core.get("favorites") or {"movies": [], "music": [], "food": []},
        "fursona": {"species": sona.get("species", ""), "colors": sona.get("colors", ""), "eyes": sona.get("eyes", ""),
                    "build": ident.get("build", ""), "markings": sona.get("markings", ""),
                    "accessories": sona.get("accessories", ""), "clothing": "",
                    "description": sona.get("description", "")},
        "personality": core.get("personality", ""),
        "mannerisms": core.get("mannerisms", ""),
        "interests": core.get("interests", ""),
        "roleplay_hooks": core.get("roleplay_hooks", ""),
        "roleplay_notes": core.get("roleplay_notes", ""),
        "relationship": core.get("relationship") or {"status": "", "partner": ""},
        "friends": core.get("friends") or [],
        "relationships": core.get("relationships") or [],
        "files": directory.get("files") or [],
        "webpages": directory.get("webpages") or [],
        "notes": core.get("notes", ""),
    }
    if directory.get("icon"):
        rec["icon"] = directory["icon"]
    if codes(r):
        rec["codes"] = codes(r)
        rec["codes"]["yiff_public"] = shows_yiff(r)
    if not rec["relationships"]:
        del rec["relationships"]
    return rec


def _regulars(path, key, entries):
    """Rewrite a regulars.json: same order as before, each entry as Residents has it, newcomers at the end."""
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"regulars": []}
    old = data.get("regulars", [])
    known = {e.get(key) for e in old}
    data["regulars"] = [entries.get(e.get(key), e) for e in old] + [entries[n] for n in sorted(entries) if n not in known]
    return _write_json(path, data)


def sync():
    """Make ClaudeXP's resident files from Residents/. Returns how many files changed (0 outside a Timeline)."""
    if not timeline.active():
        return 0
    R = _residents()
    if R is None:
        return 0
    changed = 0
    irc, muck = {}, {}
    for name in R.names(ERA):
        r = R.load(name, ERA)
        if r is None:
            continue
        changed += _write_json(RECORDS / f"{name}.json", _record(r))
        aim = r.service("aim")
        if aim:
            aim = dict(aim, persona=(aim.get("persona") or r.persona) + about_you(r, buddy=True),
                       profile=_profile_with_codes(aim.get("profile", ""), r))
            changed += _write_json(AIM / f"{name}.json", aim)
            for folder in r.media[:1]:                  # this era's photos, captions and buddy icon
                for f in folder.iterdir() if folder.is_dir() else []:
                    if f.is_file():
                        dst = AIM_ICONS / f.name if f.name == aim.get("icon") else AIM / name / f.name
                        changed += _copy_if_changed(f, dst)
        for svc, bucket in (("irc", irc), ("muck", muck)):
            entry = r.service(svc)
            if entry:
                extra = about_you(r, buddy=False) if entry.get("persona") else ""
                bucket[name] = dict(entry, persona=entry.get("persona", "") + extra) if extra else dict(entry)
    changed += _regulars(IRC, "nick", irc)
    changed += _regulars(MUCK, "name", muck)
    return changed
