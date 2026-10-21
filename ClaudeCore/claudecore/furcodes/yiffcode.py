"""YIFF Code 3.0 (vilaa.neocities.org/art/yiff/help): read one into parts, write one from parts, and say it in words.

  YIFF 3.0 <gender> [orientation] <category>... [WIXXX:<flags>]
  gender       M F H N G O
  orientation  het (left out when het) kinsey-1 kinsey-2 bi kinsey-4 kinsey-5 hom trans pan ace demi
  category     <letter>[-mod-mod...] [orientation exception] [*species*] <qualifier>
               P plush, T toons/anthros, S fursuits, V virtual (online), H human (real life)
  species      *wolf_fox* (equal), *fox-wolf* (in order), *dog-* / *-* (then everything else)
  WIXXX        WIXXX:2,10,31 - numbered interests (58 of them), *custom* ones too
Version 2.5 codes read the same way (their WIXXX two-letter list is kept as written).

parts(code) -> {"version", "gender", "orientation", "categories": {letter: {...}}, "wixxx": [..], "custom": [..]}
encode(parts) -> the code; describe(code) -> [(section, name, words)] for a decoder."""
import re

GENDERS = {"M": "Male", "F": "Female", "H": "Hermaphrodite", "N": "Non-binary", "G": "Genderfluid", "O": "Other"}
ORIENTATIONS = {"het": "Heterosexual", "kinsey-1": "Mostly heterosexual (Kinsey 1)",
                "kinsey-2": "Heterosexual, more than incidentally homosexual (Kinsey 2)", "bi": "Bisexual",
                "kinsey-4": "Homosexual, more than incidentally heterosexual (Kinsey 4)",
                "kinsey-5": "Mostly homosexual (Kinsey 5)", "hom": "Homosexual", "trans": "Into trans partners",
                "pan": "Pansexual", "ace": "Asexual", "demi": "Demisexual"}
CATEGORIES = {"P": "Plushophilia (plush animals)", "T": "Toonophilia (toons and anthros)", "S": "Fursuitophilia (fursuits)",
              "V": "Virtual sex (online / TinySex)", "H": "Human (real-life sex)"}
ORDER = list(CATEGORIES)
QUALIFIERS = {"Pr": "Practicing", "Th": "Thinking about it", "Cu": "Curious", "Tr": "Tried it, not for me",
              "Ne": "Never tried, no intention", "Ce": "Celibate for personal reasons", "No": "No comment",
              "Ns": "Not sure"}
SPECIAL_QUALIFIERS = {"P": {"Co": "Collector only", "En": "Enthusiast"}, "T": {"Rp": "Roleplay only",
                      "Ar": "Art only"},
                      "S": {"Ma": "Maker", "Pe": "Performer"}, "V": {"Ca": "Casual", "Lo": "Long-term only"},
                      "H": {"Mo": "Monogamous only", "Po": "Polyamorous"}}
MODIFIERS = {"P": {"ma": "macro", "mi": "micro", "ve": "vintage / antique", "po": "Pokemon", "di": "Disney"},
             "T": {"ma": "macro", "mi": "micro", "fe": "feral", "an": "anthro", "di": "Disney", "po": "Pokemon"},
             "S": {"fu": "full suits only", "pa": "partials only", "ke": "kemono style", "re": "realistic style",
                   "ct": "cartoon style"},
             "V": {"te": "text", "vo": "voice", "vi": "video", "vr": "VR", "ga": "games / MMOs"},
             "H": {"fu": "furries only", "nf": "non-furries only", "ro": "romantic", "ca": "casual",
                   "lo": "long-term only"}}
EXCEPTIONS = {"het": "heterosexual here", "bi": "bisexual here", "hom": "homosexual here", "pan": "pansexual here",
              "ace": "asexual here"}
WIXXX = {1: "Ageplaying", 2: "Bondable", 3: "Clued-in", 4: "Dominant", 5: "Humiliating", 6: "Lactophile",
         7: "Machinist", 8: "Messy", 9: "Painless", 10: "Role playing", 11: "Small-body", 12: "Switch",
         13: "Trainable", 14: "Voyeur", 15: "Anal", 16: "Bottom", 17: "Crossdresser", 18: "Electrical",
         19: "Incestuous", 20: "Large-body", 21: "Magical", 22: "Mind-control", 23: "Piercing", 24: "Romantic",
         25: "Snuff", 26: "Tattooing", 27: "Transforming", 28: "Watersports", 29: "Available", 30: "Branding",
         31: "Cuddling", 32: "Exhibitionist", 33: "Inexperienced", 34: "Latex", 35: "Masochist", 36: "Open-minded",
         37: "Predator", 38: "Sadist", 39: "Spanking", 40: "Teasing", 41: "Uninterested", 42: "Blood",
         43: "Chemical", 44: "Curious", 45: "Food-using", 46: "Infantilist", 47: "Leather", 48: "Mastering",
         49: "Oral", 50: "Prey", 51: "Scat", 52: "Submissive", 53: "Top", 54: "Vorarephile", 55: "Tentacles",
         56: "Degradation", 57: "Petplay", 58: "Hypnosis"}
# never part of anyone's play here, whatever a code says (and never given to a resident)
OFF_LIMITS_FLAGS = {1, 19, 25, 46}


def species_words(spec):
    """'dog-' -> 'dogs, then everything else'; 'wolf_fox' -> 'wolves and foxes' (roughly)."""
    if not spec:
        return ""
    s = spec.strip("*")
    rest = s.endswith("-") or s == "-"
    s = s.rstrip("-").rstrip("*")
    groups = [g.replace("_", " and ") for g in s.split("-") if g]
    words = ", then ".join(groups)
    if rest:
        words = (words + ", then everything else") if words else "any species"
    return words


def parts(code):
    tokens = (code or "").split()
    out = {"version": "3.0", "gender": "", "orientation": "het", "categories": {}, "wixxx": [], "custom": [],
           "other": []}
    i = 0
    if tokens[:1] and tokens[0].upper() == "YIFF":
        i = 1
        if i < len(tokens) and re.match(r"^\d", tokens[i]):
            out["version"] = tokens[i]
            i += 1
    if i < len(tokens) and tokens[i] in GENDERS:
        out["gender"] = tokens[i]
        i += 1
    if i < len(tokens) and tokens[i] in ORIENTATIONS:
        out["orientation"] = tokens[i]
        i += 1
    cur = None
    while i < len(tokens):
        t = tokens[i]
        i += 1
        if t.startswith("WIXXX"):
            body = t.split(":", 1)[1] if ":" in t else ""
            if not body:                                  # 2.5: WIXXX Ag Bn ... (two-letter codes) to the end
                out["other"] += tokens[i - 1:]
                break
            for f in body.split(","):
                f = f.strip()
                if f.isdigit():
                    out["wixxx"].append(int(f))
                elif f:
                    out["custom"].append(f.strip("*"))
            continue
        m = re.match(r"^([PZTSVH])((?:-[a-z]{2})*)$", t)
        if m and (cur is None or cur.get("q")):
            cur = {"mods": [x for x in m.group(2).split("-") if x], "oe": "", "species": "", "q": ""}
            if m.group(1) != "Z":                     # (not a category here: an old code's Z section is dropped)
                out["categories"][m.group(1)] = cur
            continue
        if cur is not None and not cur["q"]:
            if t in EXCEPTIONS and not cur["species"]:
                cur["oe"] = t
                continue
            if t.startswith("*"):
                spec = t
                while not spec.endswith("*") or spec == "*":
                    if i >= len(tokens):
                        break
                    spec += " " + tokens[i]
                    i += 1
                cur["species"] = spec.strip("*")
                continue
            cur["q"] = t
            continue
        out["other"].append(t)
    return out


def encode(p):
    code = f"YIFF {p.get('version') or '3.0'} {p.get('gender') or 'M'}"
    if p.get("orientation") and p["orientation"] != "het":
        code += " " + p["orientation"]
    for letter in ORDER:
        c = (p.get("categories") or {}).get(letter)
        if not c or not c.get("q") or c["q"] == "Ns":
            continue
        code += " " + letter + "".join("-" + m for m in c.get("mods", []))
        if c.get("oe"):
            code += " " + c["oe"]
        if c.get("species"):
            code += " *" + c["species"].strip("*") + "*"
        code += " " + c["q"]
    flags = [str(n) for n in sorted(set(p.get("wixxx") or []))] + ["*" + c + "*" for c in p.get("custom") or []]
    if flags:
        code += " WIXXX:" + ",".join(flags)
    return code


def qualifier_words(letter, q):
    return SPECIAL_QUALIFIERS.get(letter, {}).get(q) or QUALIFIERS.get(q, q)


def describe(code):
    p = parts(code)
    rows = [("Header", "Version", f"YIFF {p['version']}"),
            ("Header", "Gender", GENDERS.get(p["gender"], p["gender"] or "?")),
            ("Header", "Orientation", ORIENTATIONS.get(p["orientation"], p["orientation"]))]
    for letter in ORDER:
        c = p["categories"].get(letter)
        if not c:
            continue
        words = qualifier_words(letter, c["q"])
        mods = [MODIFIERS.get(letter, {}).get(m, m) for m in c["mods"]]
        if mods:
            words += f" ({', '.join(mods)})"
        if c["oe"]:
            words += f"; {EXCEPTIONS.get(c['oe'], c['oe'])}"
        if c["species"]:
            words += f"; species: {species_words(c['species'])}"
        rows.append(("Categories", CATEGORIES[letter], words))
    if p["wixxx"] or p["custom"]:
        names = [f"{WIXXX.get(n, '?')} ({n})" for n in p["wixxx"]] + p["custom"]
        rows.append(("WIXXX", "Interests", ", ".join(names)))
    for t in p["other"]:
        rows.append(("?", "Not understood", t))
    return rows
