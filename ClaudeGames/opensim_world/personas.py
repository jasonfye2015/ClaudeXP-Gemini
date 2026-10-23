"""Each main resident's Second Life persona: how they use the Furry Hollow. The Persona Studio edits these; the
bridge reads them to shape what the residents do in the world (when they're on, where they go, who they'll sit
with, how they talk). personas.json holds them; a resident without an entry gets defaults drawn from their
Residents record (sleep schedule and time zone, interests, personality, fur codes) and from wardrobe.json.

A persona:
    sl_name, display_name, about, partner, groups, maturity (General / Moderate / Adult)
    home: the region they call home, and where in it they usually are
    schedule: {days_per_week, hours: [[from, to], ...] in their own time zone, session_hours, timezone}
    usually / sometimes: activities (ACTIVITIES), which decide the regions they go to
    favourite_regions / avoids_regions
    social: {crowds -1..1 (avoids..seeks gatherings), chattiness 0..1, im_over_local 0..1, roleplay bool,
             rp_receptive 0..1, invites_receptive 0..1, initiates 0..1, rp_style text}
    adult: {visits: never / sometimes / often, engages: [...], with: anyone / friends / partner / user, with_user bool}
    look: {body, clothes: [[folder, name], ...]}       (mirrored in wardrobe.json for the Tailor)
    notes: free text the Studio keeps for the user
"""
import datetime as dt
import hashlib
import json
import random
import re

from . import HERE, REGIONS

FILE = HERE / "personas.json"

ACTIVITIES = ["local chat", "IMs", "exploring", "shopping", "dancing", "music", "beach", "gardening", "art",
              "building", "quiet spots", "parties", "roleplay", "cuddling", "adult", "fishing", "cafe"]
# what each region is good for (the activities that bring residents there)
REGION_ROLES = {"Furry Hollow": ["local chat", "cafe", "music", "quiet spots", "art"],
                "Whisker Falls": ["quiet spots", "gardening", "fishing", "exploring", "IMs"],
                "Tailwind Beach": ["beach", "parties", "dancing", "music"],
                "Lantern Market": ["shopping", "building", "local chat"],
                "Love Island": ["cuddling", "quiet spots", "dancing", "gardening"],
                "Fantasy Island": ["exploring", "roleplay", "parties", "art"],
                "Whitewood": ["adult", "roleplay", "parties"],
                "Castle LoveGlo": ["adult", "cuddling", "dancing"],
                "Maple Row": ["local chat", "IMs", "quiet spots", "cafe"],
                "Heartland": ["quiet spots", "cuddling", "gardening", "IMs"],
                "The Commons": ["shopping", "local chat", "parties", "art"],
                "Hollow Hall": ["local chat", "parties", "music", "roleplay"]}
HOME_REGIONS = ["Maple Row", "Heartland"]            # where the residents' own homes are
ADULT_REGIONS = {"Whitewood", "Castle LoveGlo"}
ADULT_ACTS = ["flirting", "cuddling", "dancing close", "adult poseballs", "sub/dom poses", "watching", "exhibition"]
MATURITY = ["General", "Moderate", "Adult"]
ADULT_VISITS = ["never", "sometimes", "often"]
ADULT_WITH = ["anyone", "friends", "partner", "user"]

_INTERESTS = [(r"danc", "dancing"), (r"music|guitar|cello|piano|radio|opera|woodwind|fiddle|blues|record|salsa", "music"),
              (r"garden|orchard|herb|plant|leaves|botan|greenhouse|flower", "gardening"),
              (r"photo|sketch|draw|paint|watercolor|art|embroider|weav|costume|tattoo", "art"),
              (r"walk|hik|trail|snowshoe|kayak|river|lake|desert|map|travel|explor|geolog|stone", "exploring"),
              (r"cook|bak|bread|barbecue|recipe|food|tea|coffee|preserve|pastry|chili", "cafe"),
              (r"read|poetry|book|detective|folklore|serial|film|movie|crossword|puzzle|radio play", "quiet spots"),
              (r"build|metal|wood|repair|model|fabricat|mechan|electron|solder|craft", "building"),
              (r"box|skate|surf|swim|beach|sun|sail|boat|harbo", "beach"), (r"fish|angl", "fishing"),
              (r"fursuit|\bcon\b|badge|party|parties|club|festival", "parties"),
              (r"roleplay|\bRP\b|MUCK|tabletop|dungeon|story", "roleplay")]
_OUTGOING = re.compile(r"outgoing|warm|social|gregarious|friendly|cheer|bubbly|loud|life of|chatty|talkative|welcoming", re.I)
_RESERVED = re.compile(r"\bshy|quiet|reserved|independent|private|solitary|introvert|soft-spoken|keeps to", re.I)


def load_all():
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_all(data):
    FILE.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def surname(name):
    try:
        from claudexp.programs.secondlife.residents import surname as sn
        return sn(name)
    except Exception:
        return "Resident"


def _times(text):
    """The clock times in a sentence like 'Usually sleeps from 2 a.m. to 10 a.m.' as hours (0-24)."""
    out = []
    for m in re.finditer(r"(\d{1,2})(?::(\d\d))?\s*([ap])\.?m\.?|\b(midnight|noon)\b", text or "", re.I):
        if m.group(4):
            out.append(0 if m.group(4).lower() == "midnight" else 12)
        else:
            h = int(m.group(1)) % 12 + (12 if m.group(3).lower() == "p" else 0)
            out.append(h + int(m.group(2) or 0) / 60)
    return out


def _schedule(resident):
    sleep = _times(resident.era.get("sleep_schedule", "")) if resident else []
    bed = sleep[0] if sleep else 0
    start = (bed - 3.5) % 24                       # the evening (their evening) before bed
    hours = [[round(start, 1), round(bed % 24, 1)]]
    if resident and re.search(r"retired|not currently working", resident.era.get("occupation", "") +
                              resident.era.get("work_schedule", ""), re.I):
        hours.append([14, 17])                      # and an afternoon
    return {"days_per_week": 5, "hours": hours, "session_hours": 2.5,
            "timezone": (resident.era.get("timezone") if resident else None) or "America/New_York"}


def defaults(name, resident=None, wardrobe=None):
    """A fresh persona for a resident, from their record."""
    core = resident.core if resident else {}
    era = resident.era if resident else {}
    text = " ".join([core.get("interests", ""), core.get("personality", ""), era.get("occupation", ""),
                     core.get("summary", "")])
    usually = []
    for pattern, act in _INTERESTS:
        if re.search(pattern, text, re.I) and act not in usually:
            usually.append(act)
    usually = usually[:4] or ["local chat", "exploring"]
    sometimes = [a for a in ("local chat", "exploring", "shopping", "cuddling", "parties") if a not in usually][:3]
    if _OUTGOING.search(text) and not _RESERVED.search(text):
        crowds, chat = 0.5, 0.75
    elif _RESERVED.search(text):
        crowds, chat = -0.4, 0.45
    else:
        crowds, chat = 0.0, 0.6
    rnd = random.Random(name)
    scores = {r: sum(3 for a in usually if a in REGION_ROLES[r] and a != "local chat") +
              sum(1 for a in sometimes if a in REGION_ROLES[r] and a != "local chat")
              for r in REGION_ROLES if r not in ADULT_REGIONS and r not in HOME_REGIONS}
    hangouts = sorted(scores, key=lambda r: (-scores[r], rnd.random()))[:3]
    # their home: a cottage in Heartland for the quiet and homely, a house on Maple Row for the rest
    homely = any(a in usually for a in ("gardening", "quiet spots", "cuddling", "cafe"))
    home = HOME_REGIONS[1] if HOME_REGIONS[1:] and rnd.random() < (0.65 if homely else 0.3) else HOME_REGIONS[0]
    home_parcel = _assign_parcel(name, home)
    partner = (core.get("relationship") or {}).get("partner", "")
    codes = core.get("codes") or {}
    adult_ok = bool(codes.get("show_yiff")) and bool(codes.get("yiffcode"))
    gender = (core.get("identity") or {}).get("gender", "")
    look = {"body": "", "clothes": []}
    if wardrobe:
        look = {"body": wardrobe.get("picks", {}).get(name, ""), "clothes": wardrobe.get("clothes", {}).get(name, [])}
    return {
        "sl_name": f"{''.join(ch for ch in name if ch.isalnum())[:31]} {surname(name)}",
        "display_name": core.get("fur_name") or name,
        "about": core.get("summary", "") or f"{name}, a furry.",
        "partner": partner, "groups": ["Furry Hollow Residents"],
        "maturity": "Adult" if adult_ok else "Moderate",
        "gender": gender,
        "home": {"region": home, "parcel": home_parcel[0] if home_parcel else None,
                 "spot": home_parcel[1] if home_parcel else None},
        "schedule": _schedule(resident),
        "usually": usually, "sometimes": sometimes,
        "favourite_regions": hangouts,
        "avoids_regions": [] if adult_ok else sorted(ADULT_REGIONS),
        "social": {"crowds": crowds, "chattiness": chat, "im_over_local": 0.6 if crowds < 0 else 0.3,
                   "roleplay": True, "rp_receptive": 0.7, "invites_receptive": 0.7 if crowds >= 0 else 0.5,
                   "initiates": 0.5 + crowds / 3, "rp_style": "light, in-character, follows the other person's lead"},
        "adult": {"visits": "sometimes" if adult_ok else "never",
                  "engages": ["flirting", "cuddling", "adult poseballs"] if adult_ok else [],
                  "with": "partner" if partner else "friends", "with_user": adult_ok and not partner},
        "look": look, "notes": ""}


def get(name, resident=None, wardrobe=None):
    """The persona on file, with any missing fields filled from the defaults."""
    base = defaults(name, resident, wardrobe)
    data = load_all().get(name, {})
    for k, v in base.items():
        if k not in data:
            data[k] = v
        elif isinstance(v, dict) and isinstance(data[k], dict):
            for kk, vv in v.items():
                data[k].setdefault(kk, vv)
    return data


# ---- parcels: the homes regions are cut into lots, one per resident -----------------------------------------------
def parcels(region_name):
    """[(parcel name, (x, y), area)] in a region, from the world's land table (the server's database; fine to read
    while it runs). The spot is the middle of the parcel's land."""
    import sqlite3
    from . import opensim_bin
    rid = next((r[1] for r in REGIONS if r[0] == region_name), None)
    db = opensim_bin() / "OpenSim.db" if opensim_bin() else None
    if not rid or db is None or not db.exists():
        return []
    out = []
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5)
        try:
            for name, bitmap, area, local_id in con.execute(
                    "SELECT Name, Bitmap, Area, LocalLandID FROM land WHERE RegionUUID = ? ORDER BY LocalLandID", (rid,)):
                xs, ys = [], []
                bitmap = bitmap or b""
                for i in range(min(len(bitmap), 512) * 8):          # 64x64 cells of 4 m
                    if bitmap[i // 8] >> (i % 8) & 1:
                        xs.append((i % 64) * 4 + 2)
                        ys.append((i // 64) * 4 + 2)
                if xs:
                    out.append((name or f"Parcel {local_id}", (sum(xs) / len(xs), sum(ys) / len(ys)), area))
        finally:
            con.close()
    except Exception:
        return []
    return out


def _assign_parcel(name, region):
    """A resident's own lot in their home region: the main residents take the region's parcels in turn (a stable
    order), skipping the region-sized one that means it hasn't been cut up."""
    lots = [p for p in parcels(region) if p[2] < 60000]
    if not lots:
        return None
    try:
        import residents
        order = list(residents.names(2025, tier="main"))
    except Exception:
        order = [name]
    saved = load_all()
    same_home = [n for n in order if n == name or
                 (saved.get(n, {}).get("home", {}).get("region") or region) == region]
    i = same_home.index(name) if name in same_home else 0
    lot = lots[i % len(lots)]
    return lot[0], [round(lot[1][0], 1), round(lot[1][1], 1)]


# ---- what the persona means for the world --------------------------------------------------------------------
def _daily(name, day):
    """A stable number 0-1 for a resident and a date."""
    h = hashlib.md5(f"{name}/{day.isoformat()}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def online(persona, name, when=None):
    """Are they logged on right now (by their schedule, in their own time zone)?"""
    sched = persona.get("schedule", {})
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(sched.get("timezone") or "America/New_York")
    except Exception:
        tz = None
    now = (when or dt.datetime.now(dt.timezone.utc)).astimezone(tz)
    hour = now.hour + now.minute / 60
    for i, (start, end) in enumerate(sched.get("hours") or [[19, 23]]):
        inside = start <= hour < end if start <= end else (hour >= start or hour < end)
        if not inside:
            continue
        day = now.date() if hour >= start or start <= end else now.date() - dt.timedelta(days=1)
        if _daily(name + f"/{i}", day) <= sched.get("days_per_week", 5) / 7:
            # a session shorter than the window: a stable stretch of it
            length = (end - start) % 24 or 24
            session = min(sched.get("session_hours", 2.5), length)
            offset = _daily(name + f"/o{i}", day) * (length - session)
            into = (hour - start) % 24
            if offset <= into < offset + session:
                return True
    return False


def allowed_regions(persona):
    """The regions they'll go to at all."""
    out = []
    for region, *_r in REGIONS:
        if region in persona.get("avoids_regions", []):
            continue
        if region in ADULT_REGIONS and persona.get("adult", {}).get("visits", "never") == "never":
            continue
        out.append(region)
    return out or [REGIONS[0][0]]


def region_weights(persona):
    """How much each region draws them: home and favourites most, then where their activities happen."""
    weights = {}
    adult = persona.get("adult", {}).get("visits", "never")
    for region in allowed_regions(persona):
        w = 1.0
        if region == persona.get("home", {}).get("region"):
            w += 4
        if region in persona.get("favourite_regions", []):
            w += 3
        roles = REGION_ROLES.get(region, [])
        w += 2 * sum(1 for a in persona.get("usually", []) if a in roles)
        w += 0.7 * sum(1 for a in persona.get("sometimes", []) if a in roles)
        if region in ADULT_REGIONS:
            w *= {"sometimes": 0.6, "often": 1.6}.get(adult, 0)
        weights[region] = w
    return weights


def pick_region(persona, rnd=random):
    weights = region_weights(persona)
    total = sum(weights.values()) or 1
    r = rnd.random() * total
    for region, w in weights.items():
        r -= w
        if r <= 0:
            return region
    return next(iter(weights))


def accepts(persona, kind, from_user=True, seat_name="", rnd=random):
    """Would they say yes to an invitation? kind: sit / dance / adult."""
    social = persona.get("social", {})
    adult = persona.get("adult", {})
    if kind == "adult":
        if adult.get("visits", "never") == "never" or not adult.get("engages"):
            return False
        if from_user and not adult.get("with_user", False):
            return False
        return rnd.random() < 0.4 + 0.6 * social.get("invites_receptive", 0.5)
    base = social.get("invites_receptive", 0.6)
    if kind == "dance":
        base += 0.2 if "dancing" in persona.get("usually", []) + persona.get("sometimes", []) else 0
    return rnd.random() < min(0.98, 0.25 + 0.75 * base)


def is_adult_seat(seat_name):
    """Does the seat's name belong to one of the adult poseball sets?"""
    n = (seat_name or "").lower()
    return any(w in n for w in ("fuck", "bj", "missionary", "behind", "handjob", "pleasure", "lick", "bound", "caged",
                                "gag", "hook", "sandwhich", "sandwich", "yummy", "bottle", "stool", "enjoy", "hang on",
                                "tube", "cage", "sex"))


def flavour(persona, region):
    """Lines for the resident's system prompt: how this persona behaves in the world."""
    social = persona.get("social", {})
    adult = persona.get("adult", {})
    lines = []
    doing = [a for a in persona.get("usually", []) if a in REGION_ROLES.get(region, [])] or persona.get("usually", [])[:2]
    if doing:
        lines.append(f"What you're usually here for: {', '.join(doing)}.")
    if region == persona.get("home", {}).get("region"):
        lines.append("This region is your home in Second Life; you know it well.")
    c = social.get("crowds", 0)
    lines.append("You love a crowd and drift towards groups." if c > 0.3 else
                 "You'd rather a quiet corner than a crowd, and keep chat short in groups." if c < -0.3 else
                 "You're fine in company or alone.")
    if social.get("im_over_local", 0) > 0.6:
        lines.append("You prefer IMs to local chat and say so if local gets busy.")
    if social.get("roleplay", True):
        lines.append(f"You're up for light roleplay ({social.get('rp_style', 'in character')}); "
                     f"{'you go along readily' if social.get('rp_receptive', 0.7) > 0.6 else 'you take some coaxing'}.")
    else:
        lines.append("You don't roleplay; you steer back to ordinary chat.")
    if region in ADULT_REGIONS:
        lines.append(f"This is an adults' region. You're here {adult.get('visits', 'sometimes')}; what you're open to: "
                     f"{', '.join(adult.get('engages') or ['nothing much, just looking'])}; with "
                     f"{adult.get('with', 'friends')}." + ("" if adult.get("with_user") else
                                                           " Not with your buddy, though: keep that line friendly."))
    if persona.get("partner"):
        lines.append(f"You're partnered (with {persona['partner']}) and faithful.")
    if persona.get("notes"):
        lines.append(persona["notes"])
    return "\n".join(lines)
