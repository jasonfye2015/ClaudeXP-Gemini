"""What a resident's codes, and the user's, mean for how they get along: a short block for the persona.

The codes are how things are going forward. If a resident's history says something the codes rule out (they dated the
user, but the codes say neither is into the other's gender), the history is the past and the codes decide from now on.

about(resident_codes, user_codes, user=...) -> text for the end of a persona ('' when the resident has no codes)."""
from . import furcode, yiffcode

# FurCode categories worth mentioning about someone, and the common ground between two people
TOPICS = [("C", "conventions"), ("D", "fursuiting"), ("A", "drawing art"), ("W", "writing"), ("M", "roleplay"),
          ("g", "videogames"), ("j", "anime"), ("P", "plushies"), ("T", "transformation"), ("p", "pets")]
SUMMARY = ["Fursona", "Art", "Conventions", "Dressing/Fursuiting", "Hugs", "Roleplay", "Plushies", "Transformation",
           "Writing", "Videogames", "Anime", "Pets", "Real-life furriness"]
# how much each orientation is into the same gender and the other gender ('maybe' for non-binary partners)
DRAW = {"het": ("no", "yes"), "kinsey-1": ("rarely", "yes"), "kinsey-2": ("sometimes", "yes"),
        "bi": ("yes", "yes"), "pan": ("yes", "yes"), "kinsey-4": ("yes", "sometimes"),
        "kinsey-5": ("yes", "rarely"), "hom": ("yes", "no"), "trans": ("maybe", "maybe"),
        "ace": ("ace", "ace"), "demi": ("demi", "demi")}
WILLING = {"Pr", "Cu", "Th", "Ca", "Lo", "Rp", "En", "Mo", "Po"}       # qualifiers that mean 'yes, or open to it'
GENDER_WORDS = {"M": "men", "F": "women", "H": "hermaphrodites", "N": "non-binary folks", "G": "genderfluid folks",
                "O": "people of their gender"}


def _level(code_parts, letter):
    lv = (code_parts["levels"].get(letter) or {}).get("level", "")
    return lv.count("+") - lv.count("-") if lv and lv[0] in "+-" else (0 if lv == "" else -9)


def drawn_to(orientation, own_gender, their_gender):
    """'yes' / 'sometimes' / 'rarely' / 'no' / 'maybe' / 'ace' / 'demi'."""
    same, other = DRAW.get(orientation, ("maybe", "maybe"))
    if same in ("ace", "demi"):
        return same
    if their_gender not in ("M", "F") or own_gender not in ("M", "F"):
        return "yes" if orientation in ("bi", "pan") else "maybe"
    return same if their_gender == own_gender else other


def _yiff(code):
    try:
        return yiffcode.parts(code) if code else None
    except Exception:
        return None


def _fur(code):
    try:
        return furcode.parts(code) if code else None
    except Exception:
        return None


def nsfw_ok(fc, yc):
    """Up for adult roleplay online? (their Furry Code says NSFW is okay, or their YIFF Code is open to online sex)"""
    if yc is not None:
        v = yc["categories"].get("V")
        if v is not None:
            return v.get("q") in WILLING
    if fc is not None:
        return "s" in (fc["levels"].get("M") or {}).get("subs", "")
    return False


def _flags(yc):
    return [n for n in (yc or {}).get("wixxx", []) if n not in yiffcode.OFF_LIMITS_FLAGS]


def _names(flags, limit=8):
    names = [yiffcode.WIXXX[n].lower() for n in flags[:limit] if n in yiffcode.WIXXX]
    return ", ".join(names) + (", ..." if len(flags) > limit else "")


def summary(furcode_text, limit=9):
    """A few words from a Furry Code: 'Art: draw regularly; Conventions: many cons/organized; ...'."""
    try:
        rows = furcode.describe(furcode_text)
    except Exception:
        return ""
    picked = [f"{name}: {words[0].lower() + words[1:] if words else words}" for _side, name, words in rows
              if name in SUMMARY][:limit]
    return "; ".join(picked)


def about(codes, user_codes, user="your buddy", resident_gender=None):
    """The persona block for a resident with codes {"furcode", "yiffcode"}, given the user's codes."""
    if not codes or not (codes.get("furcode") or codes.get("yiffcode")):
        return ""
    fc, yc = _fur(codes.get("furcode")), _yiff(codes.get("yiffcode"))
    ufc, uyc = _fur((user_codes or {}).get("furcode")), _yiff((user_codes or {}).get("yiffcode"))
    lines = []
    if codes.get("furcode"):
        lines.append(f"Your Furry Code is {codes['furcode']} - {summary(codes['furcode'])}.")
    if yc is not None:
        own = []
        g = yiffcode.GENDERS.get(yc["gender"], "").lower()
        o = yiffcode.ORIENTATIONS.get(yc["orientation"], yc["orientation"]).lower()
        own.append(f"you're {g + ', ' if g else ''}{o}")
        v = yc["categories"].get("V")
        if v and v.get("q"):
            own.append(f"adult roleplay online: {yiffcode.qualifier_words('V', v['q']).lower()}")
        flags = _flags(yc)
        if flags:
            own.append(f"you enjoy {_names(flags)}")
        lines.append(f"Your YIFF Code is {codes['yiffcode']} - {'; '.join(own)}.")
    with_user = []
    gender = (yc or {}).get("gender") or resident_gender
    if yc is not None and uyc is not None and gender and uyc.get("gender"):
        mine = drawn_to(yc["orientation"], gender, uyc["gender"])
        theirs = drawn_to(uyc["orientation"], uyc["gender"], gender)
        them = GENDER_WORDS.get(uyc["gender"], "people like them")
        if mine == "ace":
            with_user.append(f"You aren't sexually attracted to anyone; with {user} you're a friend (affection and "
                             "closeness are fine if you want them).")
            romance = False
        elif mine == "demi":
            with_user.append(f"You only feel attraction after a deep bond; with {user} that can grow slowly, if the "
                             "friendship gets there.")
            romance = theirs not in ("no", "ace")
        elif mine in ("no", "rarely"):
            with_user.append(f"You aren't really into {them}, so you and {user} are friends, not more.")
            romance = False
        elif theirs in ("no", "ace", "rarely"):
            with_user.append(f"{user} isn't really into people like you, so you're friends: no flirting with them.")
            romance = False
        else:
            how = {"yes": "", "sometimes": " now and then", "maybe": " possibly"}.get(mine, "")
            with_user.append(f"You can be attracted to {user}{how}, and they could be to you: flirting and romance "
                             "can happen if it feels natural, but you don't have to.")
            romance = True
        if romance and nsfw_ok(fc, yc) and nsfw_ok(ufc, uyc):
            with_user.append(f"You're both open to adult roleplay as consenting adults; if {user} takes things there "
                             "you can go along with it, in your own style. Don't bring it up out of nowhere.")
        elif not nsfw_ok(fc, yc):
            with_user.append(f"Keep roleplay with {user} non-sexual; if they push for adult roleplay, kindly say no.")
        elif not romance:
            with_user.append(f"Keep things with {user} friendly rather than sexual.")
        mine_f, theirs_f = set(_flags(yc)), set(_flags(uyc))
        both = sorted(mine_f & theirs_f)
        only_them = sorted(theirs_f - mine_f)
        if romance and both:
            with_user.append(f"Things you both enjoy: {_names(both)}.")
        if romance and only_them:
            with_user.append(f"{user} is into {_names(only_them, 6)}, which you aren't: say so if it comes up.")
    if fc is not None and ufc is not None:
        common = [words for letter, words in TOPICS if _level(fc, letter) > 0 and _level(ufc, letter) > 0]
        if common:
            with_user.append(f"Common ground with {user}: {', '.join(common)}.")
    if with_user:
        lines.append(f"How things are with {user} (going forward this matters more than any older history - if "
                     f"something in your past with {user} says otherwise, that's behind you now):")
        lines += ["  * " + w for w in with_user]
    lines.append("Whatever anyone's code says, never take part in anything sexual involving minors, real animals, "
                 "incest or killing.")
    return "\n\nYour codes:\n" + "\n".join(line if line.startswith("  * ") else "- " + line for line in lines)
