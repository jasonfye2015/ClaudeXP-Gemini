"""Propose a Furry Code 2.0 and a YIFF Code 3.0 for every resident (and every user fursona preset), for review.

  python propose_codes.py            write Residents/codes_proposal.json and 'Residents/Proposed Codes.md'
  python propose_codes.py --bake     put the reviewed proposal into each resident.json / preset profile.json
                                     ("codes": {"furcode", "yiffcode"}); a code already there is kept unless --force

The codes come from what's written about them (an artist draws, a fursuiter suits, a con-goer goes to cons, a stated
partner or orientation is kept) and, where nothing is said, seeded chances: most male furs gay or male-leaning, most
female furs straight, everyone else varied, and nearly everyone up for roleplay. Every resident is an adult. Nobody is
given zoophilia, ageplay, infantilism, incest or snuff. Bots get no codes. The same name always gets the same codes,
so running this again gives the same proposal (edit codes_proposal.json by hand before baking if you like)."""
import argparse
import json
import random
import re
import sys
from datetime import date
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TIMELINE / "ClaudeCore"))
from claudecore.furcodes import furcode, yiffcode  # noqa: E402
from claudecore.furcodes.furcode_tables import TABLES  # noqa: E402

RESIDENTS = TIMELINE / "Residents"
PRESETS = TIMELINE / "ClaudeXP" / "Program Files" / "The Fur Directory" / "user fursonas"
PROPOSAL = RESIDENTS / "codes_proposal.json"
REVIEW = RESIDENTS / "Proposed Codes.md"
ERA = 2001
USER_DEFAULTS = {   # the codes the user gave for their own account
    "Kithylin": {"furcode": "FCG3rs A- C+++ Dm H+++ M++ls P+ R+ T+++ V+ W RLCT a++ c++lmw e+ f+++ g++ h^ i++wf j-- "
                             "m++ai p Smb smb",
                 "yiffcode": "YIFF 3.0 M kinsey-5 P *dog* Cu T bi *dog* Cu S Pr V-te-vr-ga *dog-* Pr H-fu bi Pr "
                             "WIXXX:2,10,12,15,16,18,28,31,36,40,49,52,57"},
}

SYNONYMS = [   # words in a species -> a Furry Code species (checked after the code tables' own names)
    (r"red panda", None), (r"protogen", "FXP"),
    (r"husk(y|ie)|malamute|shepherd|collie|retriever|labrador|dalmatian|corgi|beagle|terrier|poodle|rottweiler|"
     r"doberman|mastiff|shiba|akita|samoyed|\bpup(py)?\b|\bdog\b|\bk-?9\b|canine|hound", "FCG"),
    (r"vixen|\bfox\b", "FCF"), (r"\bwolf\b|wolves", "FCW"),
    (r"mountain lion|cougar|puma", "FFM"), (r"snow leopard", "FFS"), (r"leopard|panther", "FFP"),
    (r"kitt(y|en)|feline|\bcat\b", "FFD"), (r"drake|wyvern|dragon|wyrm", "FDD"),
    (r"turtle|tortoise", "FDT"), (r"gecko|chameleon|iguana|lizard|salamander|monitor", "FDL"),
    (r"snake|python|cobra|viper|serpent", "FDS"), (r"crocodile|alligator|\bcroc\b|\bgator\b", "FDA"),
    (r"bunny|rabbit|cottontail", "FLR"), (r"\bhare\b|jackrabbit", "FLH"), (r"otter", "FMO"),
    (r"dormouse|\bmouse\b|\bmice\b", "FRM"), (r"\brat\b", "FRR"), (r"squirrel", "FRG"), (r"opossum|possum", "FMaP"),
    (r"\bstag\b|\bdoe\b|\bdeer\b|fawn", "FArD"), (r"\bboar\b|\bhog\b|\bpig\b|swine", "FArP"),
    (r"bison|buffalo", "FArB"), (r"ibex|\bgoat\b", "FArG"), (r"\bram\b|\bsheep\b|\blamb\b", "FArS"),
    (r"horse|pony|stallion|\bmare\b|mustang|equine", "FEH"), (r"gr[iy]ff?[io]n|gryphon", "FXG"),
    (r"polar bear", "FUA"), (r"black bear", "FUB"), (r"grizzly|brown bear", "FUG"), (r"\bbear\b", "FU"),
    (r"hyena", "FHyH"), (r"\bseal\b", "FPiS"), (r"skunk", "FMS"), (r"ferret", "FMF"), (r"badger", "FMB"),
    (r"weasel", "FMW"), (r"raccoon", "FPR"), (r"\bbat\b", "FCh"), (r"\bowl\b", "FAO"), (r"raven|crow", "FAR"),
    (r"hawk", "FAH"), (r"falcon", "FAE"), (r"tiger", "FFT"), (r"\blion\b", "FFL"), (r"lynx", "FFX"),
    (r"cheetah", "FFH"), (r"jaguar", "FFJ"), (r"serval", "FFV"), (r"ocelot", "FFO"), (r"bobcat", "FFB"),
    (r"coyote", "FCC"), (r"jackal", "FCJ"), (r"dingo", "FCD"), (r"tanuki", "FCT"),
]
FURSONA_MODS = [("t", r"\btaur\b|centaur|-taur"), ("w", r"\bwing(s|ed)?\b"), ("d", r"\bdemon"),
                ("r", r"robot|protogen|android|cyborg|mechanical"), ("s", r"\bplush(ie)?\b"),
                ("g", r"\bgoo\b|slime"), ("h", r"\bwere(wolf|-)"), ("u", r"unicorn"),
                ("m", r"\bmagic|\bmage\b|wizard|psychic|sorcer")]
JOBS = [(r"tech support|computer|programm|software|\bit\b|network|web ?design|sysadmin|help ?desk", "RLCT"),
        (r"artist|illustrat|painter|sign painter|graphic", "RLA"), (r"teacher|tutor|professor|instructor", "RLET"),
        (r"nurse|doctor|paramedic|medic\b|hospital|pharmac", "RLMH"), (r"\bvet\b|veterinar|animal[- ]care", "RLMV"),
        (r"army|navy|marine|air force|military|soldier", "RLMA"), (r"writer|author|journalist|editor|copywrit", "RLLW"),
        (r"radio|reporter|tv\b|television|newspaper|media|broadcast", "RLMC"), (r"musician|\bdj\b|band\b", "RLM"),
        (r"construction|carpenter|roofer|builder|mason", "RLCI"), (r"engineer|technician|mechanic|repair", "RLE"),
        (r"bank|account|finance|teller|insurance", "RLFB"), (r"farm|ranch|garden|tree|forest|ranger|park", "RLF"),
        (r"driver|courier|truck|dispatch|pilot|ferry|tram|bus\b|freight|rail", "RLTI"),
        (r"clerk|registrar|records|government|city|post office|postal|security|guard|watch", "RLGP"),
        (r"lawyer|paralegal|legal|court", "RLL"), (r"manager|business|owner|sales", "RLBM"),
        (r"scien|lab\b|research|museum|aquarium|archiv", "RLS"), (r"theat|actor|stage", "RLTH"),
        (r"shop|store|retail|cashier|clerk|barista|waiter|waitress|cook|chef|confection|bakery", "RLR"),
        (r"craft|clock|jewel|tailor|woodwork|smith", "RLC"), (r"student|college|school", "RLU"),
        (r"none|no current|not working|unemployed|between jobs", "RL-"), (r"retired", "RL-")]
# WIXXX interests a resident may have, and how common each is (never 1, 19, 25 or 46)
FLAG_WEIGHTS = {31: 70, 24: 45, 40: 40, 10: 45, 36: 35, 44: 20, 49: 30, 15: 22, 2: 18, 39: 14, 37: 10, 50: 10,
                27: 14, 21: 12, 47: 8, 34: 8, 57: 10, 58: 7, 32: 8, 14: 8, 33: 10, 29: 10, 13: 7, 48: 6, 35: 5,
                38: 4, 23: 5, 26: 5, 17: 5, 20: 6, 11: 6, 54: 4, 55: 4, 28: 3, 6: 2, 7: 2, 8: 3, 9: 2, 18: 2, 45: 3,
                3: 6, 5: 2, 56: 2, 22: 3, 42: 1, 43: 1, 30: 1, 51: 1}
ROLE_FLAGS = {"dom": 4, "sub": 52, "switch": 12, "top": 53, "bottom": 16}


def _load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _text(*parts):
    out = []
    for p in parts:
        if isinstance(p, dict):
            out += [_text(v) for v in p.values()]
        elif isinstance(p, list):
            out += [_text(v) for v in p]
        elif p:
            out.append(str(p))
    return " ".join(out)


def _pick(rng, weighted):
    """weighted: [(value, weight)]."""
    total = sum(w for _v, w in weighted)
    r = rng.uniform(0, total)
    for v, w in weighted:
        r -= w
        if r <= 0:
            return v
    return weighted[-1][0]


def species_code(species):
    clean = re.sub(r"\(.*?\)|anthro(pomorphic)?", "", species or "", flags=re.I).strip(" -,")
    low = clean.lower()
    if not low:
        return "FG"
    names = sorted(((v.lower(), k) for k, v in TABLES["species"].items() if "unspecified" not in v
                    and "/" not in v), key=lambda p: -len(p[0]))
    if any(re.search(rx, low) for rx, code in SYNONYMS if code is None):
        return f"F[{clean}]"
    for name, code in names:
        if low == name:
            return code
    for rx, code in SYNONYMS:
        if code and re.search(rx, low):
            return code
    for name, code in names:
        if re.search(rf"\b{re.escape(name)}\b", low):
            return code
    return f"F[{clean[:1].upper() + clean[1:]}]"


def _gender(ident_gender, pronouns="", sex=""):
    g = f"{ident_gender} {sex}".lower()
    if re.search(r"\b(woman|female|girl|f)\b", g) or "she/" in (pronouns or ""):
        return "F"
    if re.search(r"\b(man|male|boy|m)\b", g) or "he/" in (pronouns or ""):
        return "M"
    return "N"


def orientation(rng, gender, text):
    t = text.lower()
    if re.search(r"\bgay\b|\bhomosexual\b", t):
        return "hom" if gender != "F" else "het"
    if re.search(r"\blesbian\b", t):
        return "hom"
    if re.search(r"\bbisexual\b", t):
        return "bi"
    if re.search(r"\bpansexual\b", t):
        return "pan"
    if re.search(r"\basexual\b", t):
        return "ace"
    likes_men = bool(re.search(r"\b(boyfriend|husband)\b", t))
    likes_women = bool(re.search(r"\b(girlfriend|wife)\b", t))
    if gender == "M":
        if likes_women and likes_men:
            return "bi"
        if likes_men:
            return _pick(rng, [("hom", 6), ("kinsey-5", 2), ("kinsey-4", 1), ("bi", 1)])
        if likes_women:
            return _pick(rng, [("het", 5), ("kinsey-1", 2), ("bi", 2)])
        return _pick(rng, [("hom", 42), ("kinsey-5", 16), ("kinsey-4", 12), ("bi", 15), ("pan", 5), ("kinsey-2", 3),
                           ("kinsey-1", 2), ("het", 3), ("demi", 1), ("ace", 1)])
    if gender == "F":
        if likes_women:
            return _pick(rng, [("hom", 5), ("bi", 3), ("kinsey-4", 1)])
        if likes_men:
            return _pick(rng, [("het", 6), ("kinsey-1", 2), ("bi", 2)])
        return _pick(rng, [("het", 52), ("kinsey-1", 12), ("kinsey-2", 6), ("bi", 16), ("pan", 7), ("kinsey-4", 2),
                           ("hom", 3), ("demi", 1), ("ace", 1)])
    return _pick(rng, [("pan", 35), ("bi", 35), ("kinsey-4", 6), ("kinsey-2", 6), ("demi", 8), ("ace", 5),
                       ("trans", 5)])


def sexuality_letter(gender, orient):
    if orient in ("hom", "kinsey-5"):
        return "l" if gender == "F" else "g"
    return {"het": "h", "kinsey-1": "h", "kinsey-2": "b", "bi": "b", "kinsey-4": "b", "pan": "o", "trans": "o",
            "ace": "a", "demi": "d"}.get(orient, "o")


def _has(t, rx):
    return bool(re.search(rx, t, re.I))


def propose_furcode(rng, *, gender, orient, species, text, job, age, relationship, sona=""):
    t = text.lower()
    sp = species_code(species)
    mods = "".join(m for m, rx in FURSONA_MODS if _has(f"{species} {sona}", rx))     # (the fursona itself only)
    if sp == "FXP":
        mods = mods.replace("r", "")
    scale = _pick(rng, [("3", 70), ("2", 14), ("4", 12), ("5", 2), ("1", 2)])
    rel = "r"
    if rng.random() < 0.55:
        rel = "a" + rel
    if _has(t, r"fursuit"):
        rel += "c"
    if _has(t, r"\bartist|draws?\b|drawing|sketch"):
        rel += "d"
    if _has(t, r"\bwrit(es|er|ing)\b|stories"):
        rel += "w"
    if rng.random() < 0.15:
        rel += "s"
    rel = "".join(ch for ch in "acdrsw" if ch in rel)
    levels = {}
    art = _has(t, r"\bartist|draws?\b|drawing|sketch|paint|commission|illustrat")
    levels["A"] = {"level": _pick(rng, [("++", 3), ("+", 5), ("+++", 1)]) if art else
                   _pick(rng, [("", 3), ("-", 4), ("--", 3), ("---", 1)])}
    cons = _has(t, r"\bcons?\b|convention|anthrocon|furfest|confusion|eurofurence|con badge|con vacation")
    levels["C"] = {"level": _pick(rng, [("++", 4), ("+", 4), ("+++", 1)]) if cons else
                   _pick(rng, [("", 3), ("-", 4), ("+", 2), ("--", 1)])}
    suit = _has(t, r"fursuit")
    levels["D"] = {"level": _pick(rng, [("++", 4), ("+++", 2), ("+", 1)]) if suit else
                   _pick(rng, [("", 4), ("-", 3), ("--", 1)]),
                   "subs": "m" if suit and _has(t, r"made|build|maker|sew") else ""}
    huggy = _has(t, r"\bhugs?\b|cuddl|snuggl|glomp|affection|pounce|tackle|nuzzl")
    levels["H"] = {"level": _pick(rng, [("+++", 3), ("++", 4)]) if huggy else
                   _pick(rng, [("+", 4), ("++", 3), ("", 2), ("-", 1)])}
    rp = _pick(rng, [("++", 45), ("+", 38), ("", 10), ("-", 4), ("--", 3)])
    subs = ""
    if rp in ("++", "+"):
        subs += "t" if rng.random() < 0.3 else ""
        subs += "l" if rng.random() < 0.08 else ""
        subs += "s" if rng.random() < 0.8 else ""
    levels["M"] = {"level": rp, "subs": subs}
    levels["P"] = {"level": _pick(rng, [("++", 2), ("+", 4), ("", 3), ("-", 1)]) if not _has(t, r"plush") else "++"}
    levels["R"] = {"level": _pick(rng, [("", 4), ("+", 2), ("-", 2), ("++", 1), ("--", 1)])}
    levels["T"] = {"level": _pick(rng, [("+++", 2), ("++", 3), ("+", 2), ("", 3), ("-", 1), ("--", 1)])}
    levels["V"] = {"level": _pick(rng, [("", 5), ("-", 2), ("--", 2), ("+", 1)])}
    writes = _has(t, r"\bwrit(es|er|ing)\b|stories|poet|author")
    levels["W"] = {"level": _pick(rng, [("+", 3), ("", 2), ("++", 1)]) if writes else
                   _pick(rng, [("", 3), ("-", 3), ("--", 3)])}
    techy = _has(f"{t} {job}", r"computer|tech|program|linux|hacker|network|software|\bit\b")
    levels["c"] = {"level": _pick(rng, [("++", 3), ("+++", 2)]) if techy else
                   _pick(rng, [("+", 5), ("", 3), ("++", 1), ("-", 1)]),
                   "subs": _pick(rng, [("w", 8), ("lw", 2), ("m", 1)])}
    levels["e"] = {"level": _pick(rng, [("+", 4), ("", 4), ("++", 3), ("+++", 1), ("-", 1)])}
    levels["f"] = {"level": _pick(rng, [("++", 4), ("+", 3), ("+++", 3), ("", 2), ("-", 2), ("--", 1)])}
    gamer = _has(t, r"\bgam(e|es|er|ing)\b|video ?game|nintendo|playstation|quake|everquest|ultima|doom")
    levels["g"] = {"level": _pick(rng, [("++", 4), ("+++", 2)]) if gamer else
                   _pick(rng, [("+", 4), ("++", 2), ("", 2), ("-", 1)])}
    partnered = bool(relationship) and not _has(relationship, r"single")
    levels["h"] = {"level": _pick(rng, [("+++", 5), ("++", 2)]) if partnered else
                   _pick(rng, [("+", 4), ("", 3), ("^", 3), ("++", 2), ("-", 1)])}
    levels["i"] = {"level": _pick(rng, [("++", 6), ("+", 3), ("+++", 1)]),
                   "subs": ("w" if rng.random() < 0.35 else "") + ("f" if rng.random() < 0.3 else "")}
    levels["j"] = {"level": "++" if _has(t, r"anime|manga") else _pick(rng, [("+", 3), ("", 3), ("-", 2), ("++", 1),
                                                                             ("--", 1)])}
    levels["m"] = {"level": _pick(rng, [("", 6), ("+", 2), ("-", 2)])}
    levels["p"] = {"level": _pick(rng, [("", 3), ("+", 2), ("-", 3), ("++", 1), ("^", 1), ("^^", 1)])}
    job_code = next((code for rx, code in JOBS if re.search(rx, job or "", re.I)), None) or \
        _pick(rng, [("RLAT", 2), ("RLR", 2), ("RLU", 1)])
    sex = sexuality_letter(gender, orient)
    g = {"M": "m", "F": "f"}.get(gender, "n")
    p = {"fursonas": [{"species": sp, "mods": mods, "scale": scale, "rel": rel}], "levels": levels,
         "job": {"code": job_code, "trained": False, "custom": ""}, "age": {"level": furcode.age_level(age)},
         "S": {"gender": g, "sexuality": sex}, "s": {"gender": g, "sexuality": sex}, "other": []}
    return furcode.encode(p)


def propose_yiffcode(rng, *, gender, orient, species, text, partnered=False):
    t = text.lower()
    own = re.sub(r"\(.*?\)|anthro(pomorphic)?", "", species or "", flags=re.I).strip().lower()
    own = re.sub(r"[^a-z]+", "_", own.split()[-1] if own.split() else "").strip("_") or "fur"
    favs = [own] + rng.sample(["fox", "wolf", "dog", "cat", "dragon", "otter", "husky", "lion", "tiger", "rabbit",
                               "horse", "bear", "hyena", "skunk", "raccoon", "deer"], 2)
    private = rng.random() < 0.12                       # some keep it to themselves
    ace = orient == "ace"
    cats = {}
    q = _pick(rng, [("Ne", 5), ("Cu", 2), ("No", 3), ("Th", 1), ("En", 1), ("Co", 1)])
    cats["P"] = {"mods": [], "oe": "", "species": "", "q": q}
    tq = "No" if private else "Ce" if ace else _pick(rng, [("Pr", 6), ("Cu", 3), ("Th", 1), ("Rp", 2), ("Ar", 1)])
    tmods = [m for m, chance in (("an", 0.45), ("fe", 0.08), ("ma", 0.06), ("mi", 0.05)) if rng.random() < chance]
    cats["T"] = {"mods": tmods, "oe": "", "species": _species_pref(rng, favs), "q": tq}
    suit = _has(t, r"fursuit")
    sq = "No" if private else _pick(rng, [("Pr", 3), ("Cu", 2), ("Th", 1)]) if suit else \
        _pick(rng, [("Cu", 3), ("Ne", 3), ("No", 2), ("Th", 1)])
    cats["S"] = {"mods": [m for m, chance in (("fu", 0.25), ("ct", 0.2), ("ke", 0.1)) if rng.random() < chance],
                 "oe": "", "species": "", "q": sq}
    vq = "No" if private else "Ce" if ace else _pick(rng, [("Pr", 66), ("Cu", 14), ("Th", 6), ("Ca", 5), ("Lo", 4),
                                                           ("Ne", 5)])
    vmods = ["te"] + [m for m, chance in (("vo", 0.12), ("ga", 0.15)) if rng.random() < chance]
    cats["V"] = {"mods": vmods, "oe": "", "species": _species_pref(rng, favs, rest=True), "q": vq}
    if partnered:                                       # (someone with a partner isn't celibate)
        hq = "No" if private else _pick(rng, [("Pr", 4), ("Mo", 3), ("Cu", 1), ("No", 1)])
    else:
        hq = "No" if private else "Ce" if ace else _pick(rng, [("Pr", 4), ("Cu", 2), ("Mo", 2), ("Po", 1), ("No", 2),
                                                               ("Ce", 1)])
    hmods = [m for m, chance in (("fu", 0.4), ("ro", 0.35), ("ca", 0.12), ("lo", 0.15)) if rng.random() < chance]
    if "ca" in hmods and "lo" in hmods:
        hmods.remove("ca")
    cats["H"] = {"mods": hmods, "oe": "", "species": "", "q": hq}
    flags = []
    if ace:
        flags = [31, 24, 41] + ([40] if rng.random() < 0.4 else [])
    elif private:
        flags = [31] + ([24] if rng.random() < 0.5 else [])
    else:
        role = _pick(rng, [("switch", 30), ("sub", 25), ("dom", 20), ("none", 25)])
        if role != "none":
            flags.append(ROLE_FLAGS[role])
        if role in ("sub", "switch") and rng.random() < 0.5:
            flags.append(ROLE_FLAGS["bottom"])
        if role in ("dom", "switch") and rng.random() < 0.5:
            flags.append(ROLE_FLAGS["top"])
        pool = dict(FLAG_WEIGHTS)
        for _ in range(rng.randint(3, 9)):
            pick = _pick(rng, list(pool.items()))
            flags.append(pick)
            pool.pop(pick, None)
    flags = sorted(set(f for f in flags if f not in yiffcode.OFF_LIMITS_FLAGS))
    p = {"version": "3.0", "gender": gender, "orientation": orient, "categories": cats, "wixxx": flags, "custom": []}
    return yiffcode.encode(p)


def _species_pref(rng, favs, rest=False):
    kind = rng.random()
    if kind < 0.25:
        s = favs[0]
    elif kind < 0.55:
        s = f"{favs[0]}_{favs[1]}"
    elif kind < 0.8:
        s = f"{favs[0]}-{favs[1]}-{favs[2]}"
    else:
        return "-" if rest else ""
    return s + ("-" if rest and rng.random() < 0.6 else "")


# ---- the cast ----------------------------------------------------------------------------------------------------
def _age(born):
    try:
        b = date.fromisoformat(born)
    except (TypeError, ValueError):
        return None
    snap = date(ERA, 10, 1)
    return snap.year - b.year - ((snap.month, snap.day) < (b.month, b.day))


def residents():
    for folder in sorted(RESIDENTS.iterdir(), key=lambda p: p.name.lower()):
        core = _load(folder / "resident.json")
        if not core:
            continue
        era = _load(folder / "eras" / f"{ERA}.json") or {}
        yield folder, core, era


def is_bot(core):
    return bool(re.search(r"\bbot\b", f"{(core.get('fursona') or {}).get('species', '')} {core.get('summary', '')}",
                          re.I)) and core.get("tier") == "background"


def propose_one(name, gender, species, text, job, age, relationship, sona=""):
    rng = random.Random(f"codes:{name}")
    orient = orientation(rng, gender, f"{text} {relationship}")
    partnered = bool(relationship.strip()) and not re.search(r"single", relationship, re.I)
    return {"furcode": propose_furcode(rng, gender=gender, orient=orient, species=species, text=text, job=job,
                                       age=age, relationship=relationship, sona=sona),
            "yiffcode": propose_yiffcode(rng, gender=gender, orient=orient, species=species, text=text,
                                         partnered=partnered)}


def build():
    out = {"residents": {}, "presets": {}, "skipped": []}
    for folder, core, era in residents():
        if is_bot(core):
            out["skipped"].append(core.get("name", folder.name))
            continue
        ident = core.get("identity") or {}
        gender = _gender(ident.get("gender", ""), ident.get("pronouns", ""))
        rel = _text(core.get("relationship"), core.get("relationships"))
        text = _text(core.get("summary"), core.get("personality"), core.get("mannerisms"), core.get("interests"),
                     core.get("notes"), core.get("fursona"), era.get("persona"))
        codes = propose_one(folder.name, gender, (core.get("fursona") or {}).get("species", ""), text,
                            era.get("occupation", ""), _age(core.get("born")), rel, _text(core.get("fursona")))
        codes.update(tier=core.get("tier", ""), gender=gender, species=(core.get("fursona") or {}).get("species", ""))
        out["residents"][folder.name] = codes
    for folder in sorted(PRESETS.iterdir()) if PRESETS.is_dir() else []:
        prof = _load(folder / "profile.json")
        if not prof:
            continue
        personal = prof.get("personal") or {}
        gender = _gender(personal.get("sex", ""), personal.get("pronouns", ""))
        if folder.name in USER_DEFAULTS:
            codes = dict(USER_DEFAULTS[folder.name], given=True)
        else:
            dob = personal.get("dob", "")
            m = re.match(r"(\d+)/(\d+)/(\d{4})", dob)
            age = _age(f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}") if m else None
            text = _text(prof.get("summary"), prof.get("personality"), prof.get("interests"), prof.get("fursuit"),
                         prof.get("fursona"), prof.get("roleplay_notes"))
            codes = propose_one(folder.name, gender, (prof.get("fursona") or {}).get("species", ""), text,
                                personal.get("job", ""), age, _text(prof.get("relationship")),
                                _text(prof.get("fursona")))
        codes.update(gender=gender, species=(prof.get("fursona") or {}).get("species", ""))
        out["presets"][folder.name] = codes
    return out


def _summary(yc):
    p = yiffcode.parts(yc)
    v = p["categories"].get("V", {})
    flags = ", ".join(yiffcode.WIXXX[n] for n in p["wixxx"][:6]) + ("..." if len(p["wixxx"]) > 6 else "")
    return (f"{yiffcode.ORIENTATIONS.get(p['orientation'], p['orientation'])}; online: "
            f"{yiffcode.qualifier_words('V', v.get('q', '')) if v else '-'}; {flags}")


def write_review(data):
    lines = ["# Proposed Furry Codes and YIFF Codes", "",
             "Made by `ClaudeCore/tools/propose_codes.py`. Nothing is baked into the residents yet: review this, edit "
             "`codes_proposal.json` by hand if you like, then run `propose_codes.py --bake`.", "",
             "Age in the Furry Code is the 2001 bracket; each era works out its own from the birth date.", ""]
    lines += ["## Your fursona presets", "", "| Preset | Gender | Furry Code | YIFF Code |", "|---|---|---|---|"]
    for name, c in data["presets"].items():
        lines.append(f"| **{name}**{' (your codes)' if c.get('given') else ''} | {c['gender']} | `{c['furcode']}` | "
                     f"`{c['yiffcode']}` |")
    for tier in ("main", "support", "background"):
        rows = {n: c for n, c in data["residents"].items() if c["tier"] == tier}
        lines += ["", f"## {tier.title()} furs ({len(rows)})", "",
                  "| Resident | Species | Furry Code | YIFF Code | In short |", "|---|---|---|---|---|"]
        for name, c in rows.items():
            lines.append(f"| **{name}** ({c['gender']}) | {c['species']} | `{c['furcode']}` | `{c['yiffcode']}` | "
                         f"{_summary(c['yiffcode'])} |")
    if data["skipped"]:
        lines += ["", f"No codes (bots): {', '.join(data['skipped'])}"]
    REVIEW.write_text("\n".join(lines) + "\n", encoding="utf-8")


def bake(force=False):
    data = _load(PROPOSAL)
    if not data:
        sys.exit("No codes_proposal.json yet: run without --bake first.")
    done = 0
    for name, c in data["residents"].items():
        path = RESIDENTS / name / "resident.json"
        core = _load(path)
        if core is None or (core.get("codes") and not force):
            continue
        core["codes"] = {"furcode": c["furcode"], "yiffcode": c["yiffcode"]}
        path.write_text(json.dumps(core, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        done += 1
    for name, c in data["presets"].items():
        path = PRESETS / name / "profile.json"
        prof = _load(path)
        if prof is None or (prof.get("codes") and not force):
            continue
        prof["codes"] = {"furcode": c["furcode"], "yiffcode": c["yiffcode"]}
        path.write_text(json.dumps(prof, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        done += 1
    print(f"Baked codes into {done} files.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bake", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.bake:
        bake(args.force)
        return
    data = build()
    PROPOSAL.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    write_review(data)
    print(f"Proposed codes for {len(data['residents'])} residents and {len(data['presets'])} presets "
          f"({len(data['skipped'])} bots skipped). Review: {REVIEW}")


if __name__ == "__main__":
    main()
