"""Furry Code 2.0 (vilaa.neocities.org/art/furcode2): read one into parts, write one from parts, and say it in words.

A code is space-separated components, in this order:
  F...        the fursona(s): species code (FCG = generic dog), fursona modifier letters (d i g h m p r s t u w),
              the human-to-animal scale (1-6) and relationship letters (a c d r s w); more fursonas after '/'
  A C D H M P R T V W     the furry side: a letter and a level (+++ ... ---, ^, ? ! #), then sub-option letters
  RL...       real-life job (RLCT = Computers/IT), '^' trained but no job, [custom]
  a c e f g h i j m p     the offline side (a = age bracket, or a37 for an exact age)
  S..  s..    fursona's and your own gender (f i m n #) and sexuality (a b d g h l o), [custom]
Modifiers anywhere: ~ approximately, / several, > going from one to another, & a hybrid, $ makes money, [text].

parts(code) -> {"fursonas": [...], "levels": {letter: (level, subs)}, "job": ..., "age": ..., "S": ..., "s": ...}
encode(parts) -> the code; describe(code) -> [(side, name, words)] for a decoder."""
import re

from .furcode_tables import CATEGORY_NAMES, SPECIES_BY_CATEGORY, TABLES

FURRY = [("A", "Art", "art"), ("C", "Conventions", "conventions"), ("D", "Dressing/Fursuiting", "dressing"),
         ("H", "Hugs", "hugs"), ("M", "Roleplay", "roleplay"), ("P", "Plushies", "plushies"),
         ("R", "Realism", "realism"), ("T", "Transformation", "transformation"), ("V", "Virtual Reality", "vr"),
         ("W", "Writing", "writing")]
OFFLINE = [("c", "Computers", "computers"), ("e", "Education", "education"), ("f", "Real-life furriness", "furriness"),
           ("g", "Videogames", "gaming"), ("h", "Housing", "housing"), ("i", "Internet", "internet"),
           ("j", "Anime", "anime"), ("m", "Mobile devices", "mobile"), ("p", "Pets", "pets")]
SUBS = {"D": {"m": "made their own"}, "M": {"t": "TTRPGs", "l": "LARPing", "s": "NSFW okay"},
        "V": {"m": "has a 3D model / VTubes"}, "c": dict(TABLES["computerOS"]), "i": {"w": "has a webpage",
        "f": "mentions furries"}, "j": {"s": "subtitles", "d": "dubbing"}, "m": dict(TABLES["mobileOS"])}
LEVEL_CHARS = "+-^~?!#$"
FURSONA_MODS = "dighmprstuw"
RELATIONSHIPS = "acdrsw"
GENDERS = {"f": "female", "i": "intersex", "m": "male", "n": "non-binary", "#": "private"}
SEXUALITIES = {"a": "asexual", "b": "bisexual", "d": "demisexual", "g": "gay", "h": "heterosexual",
               "l": "lesbian", "o": "other", "?": "unsure"}
ORDER = [c for c, _n, _t in FURRY] + ["RL", "a"] + [c for c, _n, _t in OFFLINE]


def split(code):
    """Components, keeping [custom text] (which may have spaces) inside its component."""
    out, buf, depth = [], "", 0
    for ch in (code or "").strip():
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth = max(0, depth - 1)
        if ch.isspace() and depth == 0:
            if buf:
                out.append(buf)
            buf = ""
        else:
            buf += ch
    if buf:
        out.append(buf)
    return out


def _species_code(rest):
    """The longest species code at the start of rest (without its 'F')."""
    for code in sorted(TABLES["species"], key=len, reverse=True):
        if rest.startswith(code[1:]) and len(code) > 1:
            return code
    return None


def parse_fursona(comp):
    """'FCG3rs' -> {"species": "FCG", "mods": "", "scale": "3", "rel": "rs"}."""
    if comp in ("F?", "F!", "F#"):
        return {"species": comp, "mods": "", "scale": "", "rel": ""}
    m = re.match(r"^F\[([^\]]*)\](.*)$", comp)
    if m:
        species, rest = f"F[{m.group(1)}]", m.group(2)
    else:
        species = _species_code(comp[1:]) or "FG"
        rest = comp[len(species):] if comp.startswith(species) else comp[1:]
    mods = ""
    while rest and rest[0] in FURSONA_MODS:
        mods += rest[0]
        rest = rest[1:]
    scale = ""
    if rest and rest[0].isdigit():
        scale, rest = rest[0], rest[1:]
    rel = "".join(ch for ch in rest if ch in RELATIONSHIPS)
    return {"species": species, "mods": mods, "scale": scale, "rel": rel}


def parts(code):
    """A code -> its parts (unknown components are kept in "other")."""
    out = {"fursonas": [], "levels": {}, "job": None, "age": None, "S": None, "s": None, "other": []}
    for comp in split(code):
        if comp.startswith("F"):
            out["fursonas"] += [parse_fursona(f) for f in comp.split("/") if f]
            continue
        if comp.startswith("RL"):
            m = re.match(r"^RL([^\[^]*)(\^?)(?:\[([^\]]*)\])?", comp)
            out["job"] = {"code": "RL" + (m.group(1) if m else comp[2:]), "trained": bool(m and m.group(2)),
                          "custom": (m.group(3) or "") if m else ""}
            continue
        m = re.match(r"^([Ss])([fimn#])([a-z?]?)(?:\[([^\]]*)\])?(?:\[([^\]]*)\])?$", comp)
        if m:
            out[m.group(1)] = {"gender": m.group(2), "sexuality": m.group(3), "custom": m.group(4) or "",
                               "custom2": m.group(5) or ""}
            continue
        m = re.match(r"^a(\d+)$", comp)
        if m:
            out["age"] = {"exact": int(m.group(1))}
            continue
        letter = comp[0]
        if letter in ORDER:
            body = comp[1:]
            m = re.match(r"^([" + re.escape(LEVEL_CHARS) + r"/>&]*)([a-z]*)(\[[^\]]*\])?$", body)
            level, subs, custom = (m.group(1), m.group(2), m.group(3) or "") if m else (body, "", "")
            if letter == "a":
                out["age"] = {"level": level}
            else:
                out["levels"][letter] = {"level": level, "subs": subs, "custom": custom.strip("[]")}
            continue
        out["other"].append(comp)
    return out


def encode(p):
    """Parts -> a code, in the encoder's order (age once)."""
    comps = []
    fs = []
    for i, f in enumerate(p.get("fursonas") or []):
        s = f.get("species") or "F?"
        if s not in ("F?", "F!", "F#"):
            s += f.get("mods", "")
            if i == 0 and f.get("scale"):
                s += str(f["scale"]) + f.get("rel", "")
        fs.append(s)
    if fs:
        comps.append("/".join(fs))
    levels = p.get("levels") or {}
    for letter in ORDER:
        if letter == "RL":
            job = p.get("job")
            if job:
                comps.append(job["code"] + ("^" if job.get("trained") else "") +
                             (f"[{job['custom']}]" if job.get("custom") else ""))
            continue
        if letter == "a":
            age = p.get("age")
            if age:
                comps.append(f"a{age['exact']}" if age.get("exact") else "a" + age.get("level", ""))
            continue
        if letter in levels:
            lv = levels[letter]
            comps.append(letter + lv.get("level", "") + lv.get("subs", "") +
                         (f"[{lv['custom']}]" if lv.get("custom") else ""))
    for key in ("S", "s"):
        g = p.get(key)
        if g:
            comps.append(key + g.get("gender", "?") + g.get("sexuality", "") +
                         (f"[{g['custom']}]" if g.get("custom") else ""))
    return " ".join(comps + list(p.get("other") or []))


# ---- in words --------------------------------------------------------------------------------------------------
def species_name(code):
    if code.startswith("F[") and code.endswith("]"):
        return code[2:-1]
    return {"F?": "unsure", "F!": "no fursona", "F#": "private"}.get(code) or TABLES["species"].get(code) \
        or CATEGORY_NAMES.get(code, "unknown species")


def describe_fursona(f):
    words = species_name(f["species"])
    mods = [TABLES["modifiers"][m] for m in f.get("mods", "") if m in TABLES["modifiers"]]
    if mods:
        words += f" ({', '.join(mods)})"
    if f.get("scale"):
        words += ", " + TABLES["scale"].get(str(f["scale"]), "").lower()
    rel = [TABLES["relationship"][r] for r in f.get("rel", "") if r in TABLES["relationship"]]
    if rel:
        words += f" ({', '.join(rel).lower()})"
    return words


def _level_words(letter, table, lv):
    level = lv.get("level", "")
    extras = []
    if "$" in level:
        extras.append("makes money from it")
        level = level.replace("$", "")
    approx = "~" in level
    level = level.replace("~", "")
    pieces = re.split(r"([/>&])", level) if re.search(r"[/>&]", level) else [level]
    words = []
    joiner = {"/": " or ", ">": " going to ", "&": " and "}
    for piece in pieces:
        if piece in joiner:
            words.append(joiner[piece])
        else:
            words.append(TABLES[table].get(letter + piece, piece or "-"))
    text = ("about: " if approx else "") + "".join(words)
    subs = [SUBS.get(letter, {}).get(ch, ch) for ch in lv.get("subs", "")]
    extras = subs + extras + ([lv["custom"]] if lv.get("custom") else [])
    return text + (f" ({', '.join(extras)})" if extras else "")


def _gender_words(g):
    if not g:
        return ""
    words = GENDERS.get(g.get("gender"), "unsure")
    if g.get("custom") and g.get("gender") == "n":
        words += f" ({g['custom']})"
    if g.get("sexuality"):
        words += ", " + SEXUALITIES.get(g["sexuality"], g["sexuality"])
    return words


def describe(code):
    """[(side, name, words)] - what a decoder shows, in order."""
    p = parts(code)
    rows = []
    for i, f in enumerate(p["fursonas"]):
        rows.append(("Furry", "Fursona" if i == 0 else f"Fursona {i + 1}", describe_fursona(f)))
    names = {c: (n, t) for c, n, t in FURRY + OFFLINE}
    for letter, (name, table) in names.items():
        if letter in p["levels"] and letter in [c for c, _n, _t in FURRY]:
            rows.append(("Furry", name, _level_words(letter, table, p["levels"][letter])))
    if p["S"]:
        rows.append(("Furry", "Fursona gender", _gender_words(p["S"])))
    if p["job"]:
        job = p["job"]
        words = TABLES["realLife"].get(job["code"], job["code"])
        if job.get("trained"):
            words += " (trained, but no job)"
        if job.get("custom"):
            words += f" [{job['custom']}]"
        rows.append(("Real life", "Job", words))
    if p["age"]:
        a = p["age"]
        rows.append(("Real life", "Age", f"{a['exact']} years old" if a.get("exact")
                     else TABLES["age"].get("a" + a.get("level", ""), a.get("level", ""))))
    for letter, (name, table) in names.items():
        if letter in p["levels"] and letter in [c for c, _n, _t in OFFLINE]:
            rows.append(("Real life", name, _level_words(letter, table, p["levels"][letter])))
    if p["s"]:
        rows.append(("Real life", "Gender", _gender_words(p["s"])))
    for comp in p["other"]:
        rows.append(("?", "Not understood", comp))
    return rows


def age_level(age):
    """The age bracket's level for an age in years."""
    if age is None:
        return "?"
    for level, low in (("++++", 60), ("+++", 50), ("++", 40), ("+", 30), ("", 20), ("-", 13)):
        if age >= low:
            return level
    return "?"


def with_age(code, age):
    """The code with its age bracket for an age (each era works out its own; an exact age stays as written)."""
    if not code or age is None:
        return code
    p = parts(code)
    if p["age"] and p["age"].get("exact"):
        return code
    p["age"] = {"level": age_level(age)}
    return encode(p)


def levels_for(letter):
    """[(code level, words)] a category can take, for an encoder's menus."""
    table = dict((c, t) for c, _n, t in FURRY + OFFLINE).get(letter) or {"a": "age"}.get(letter)
    if table is None:
        return []
    return [(k[len(letter):], v) for k, v in TABLES[table].items()]


def species_menu():
    """[(category code, category name, [(species code, name)])] for an encoder."""
    out = []
    for cat, name in CATEGORY_NAMES.items():
        species = SPECIES_BY_CATEGORY.get(cat, {})
        out.append((cat, name, list(species.items())))
    return out
