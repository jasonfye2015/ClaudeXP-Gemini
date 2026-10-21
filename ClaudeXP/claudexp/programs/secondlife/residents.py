"""The 34 residents as they appear in Second Life: an avatar for each (after their fursona), what they wear, the
group title over their name, where they like to hang out, who owns a house in Pawprint Estates, and their profile
(from their Fur Directory card - with their Furry Code and, if they make it public, their YIFF Code)."""
import datetime
import hashlib
import json

from ...paths import ROOT
from .avatar import PRESETS, spec

FURDIR = ROOT / "Program Files" / "The Fur Directory" / "residents"
AIM_DIR = ROOT / "Program Files" / "ClaudeAIM"
SURNAMES = ["Furlong", "Pawsome", "Moonfur", "Snowpaw", "Tailwind", "Fluffington", "Whiskerton", "Starlight",
            "Brightwater", "Thistle", "Ember", "Quicksilver", "Mistral", "Hollowell", "Ashford", "Sparkle"]


def base(name, **kw):
    s = dict(PRESETS[name])
    s.update(kw)
    return spec(**s)


# screen name -> (avatar, worn item keys, title, haunts {sim: weight})
LOOKS = {
    "ArcticFox": (base("Arctic Fox", eyes="#8AC8F0", build=0.92),
                  ["cloth:hoodie-blue", "cloth:jeans-blue"], "Yarf! Fluffy Hugger", {"club": 4, "bazaar": 2}),
    "Brass": (spec(species="Cockatoo", head="bird", snout=0.9, ears="none", tail="feathers", legs="plant",
                   wings="feather", fur="#F4F4F2", belly="#FFFFFF", accent="#F2D23A", nose="#3A3A3A", eyes="#7A8A9A",
                   surface="feathers", markings=["belly"], extras=["crest"], height=1.05, build=1.1),
              ["cloth:vest", "acc:bowtie"], "Bazaar Regular", {"bazaar": 4, "club": 1}),
    "Cairngorm": (spec(species="Mountain Lion", head="feline", ears="round", tail="thin", fur="#C8A070",
                       belly="#EEE0C8", accent="#3A2A20", eyes="#8A7A3A", markings=["belly", "muzzle", "tailtip"],
                       extras=["whiskers"], height=0.96, build=1.08),
                  ["cloth:flannel", "cloth:jeans-black", "cloth:boots"], "Mountain Dweller", {"club": 2, "sandbox": 2}),
    "Cameo": (spec(species="Chameleon", head="reptile", snout=0.5, ears="none", tail="thick", fur="#6AB86A",
                   belly="#C8E8A8", accent="#4A8AE8", eyes="#7A8A9A", surface="scales", markings=["belly", "cheeks"],
                   extras=["crest"], crest="#4A9A4A", frame="f", height=1.04),
              ["cloth:dress-sun", "acc:flowers"], "Colour Collector", {"bazaar": 4, "club": 1}),
    "Cicada": (spec(species="Cicada", head="insect", ears="none", tail=None, legs="plant", wings="insect",
                    fur="#7A7A3A", belly="#9A9A5A", accent="#3A3A1A", eyes="#D8A030", surface="scales",
                    extras=["antennae"], frame="f", build=0.9),
               ["acc:scarf"], "Summer Singer", {"sandbox": 2, "club": 2}),
    "Crispin": (spec(species="Porcupine", head="rodent", snout=0.6, ears="round", ear_size=0.7, tail="stub",
                     legs="plant", fur="#6A4A30", belly="#A88A6A", accent="#E8DCC0", eyes="#3A2A1A",
                     markings=["belly", "muzzle"], extras=["quills"], build=1.15),
                ["cloth:jacket-denim", "cloth:jeans-blue"], "Estate Resident", {"estates": 3, "sandbox": 2}),
    "CyberianHusky": (base("Husky", fur="#6A7078", accent="#26282C", eyes="#9AD8F8", build=1.15),
                      ["cloth:tee-black", "cloth:shorts-cargo", "acc:headphones"], "Neon Paws Regular",
                      {"club": 5, "bazaar": 1}),
    "Dewdrop": (base("Frog", fur="#3AA878", belly="#E8D890", accent="#2A7A50", eyes="#8A7A3A", frame="f"),
                ["cloth:tee-sky", "cloth:skirt-pink", "acc:bow"], "Estate Resident", {"estates": 3, "bazaar": 2}),
    "Flicker": (spec(species="Phoenix", head="bird", snout=0.8, ears="none", tail="feathers", tail_size=1.4,
                     legs="plant", wings="feather", fur="#C84A2A", belly="#E8A050", accent="#F2C230", nose="#E8B030",
                     eyes="#D89020", surface="feathers", markings=["belly"], extras=["crest"], build=0.92),
                ["cloth:jacket-leather", "acc:shades"], "Rising From the Ashes", {"club": 4, "sandbox": 1}),
    "Hush": (spec(species="Snowy Owl", head="bird", snout=0.45, ears="tufted", ear_size=0.6, tail="feathers",
                  legs="plant", wings="feather", fur="#F4F4F2", belly="#FFFFFF", accent="#3A3A3E", nose="#2A2A2A",
                  eyes="#E8C840", surface="feathers", markings=["speckles"], height=1.04, build=1.1),
             ["cloth:sweater", "acc:glasses"], "Night Owl", {"estates": 3, "club": 1}),
    "Juniper": (base("Lynx", fur="#C89A60", accent="#5A4030", eyes="#A8D8A0", frame="f", height=0.92),
                ["cloth:tank-pink", "cloth:shorts-cargo"], "Estate Resident", {"estates": 2, "bazaar": 2, "club": 1}),
    "KittyKat": (base("Calico Cat", eyes="#58B848", build=0.92),
                 ["cloth:tee-red", "cloth:jeans-blue", "acc:collar-red"], "Mew Crew", {"club": 4, "bazaar": 2}),
    "Latchkey": (spec(species="Opossum", head="rodent", snout=1.1, ears="round", tail="thin", legs="plant",
                      fur="#A8A8AE", belly="#E8E8E8", accent="#E8A0B0", nose="#E89AA8", eyes="#C89030",
                      markings=["belly", "eartips", "tailtip", "muzzle"]),
                 ["cloth:hoodie-grey", "cloth:pants-track"], "Estate Resident", {"estates": 3, "sandbox": 1}),
    "LazyFox": (base("Red Fox", eyes="#8A7A3A", height=1.06, build=0.92),
                ["cloth:tee-white", "cloth:jeans-blue", "acc:cap-red"], "Neon Paws Regular", {"club": 4, "sandbox": 1}),
    "Mallowroot": (base("Bunny", fur="#8A5A3A", belly="#F4F0E8", eyes="#A8D8A0", frame="f", height=0.9),
                   ["cloth:sweater", "cloth:skirt-plaid"], "Estate Resident", {"estates": 3, "bazaar": 2}),
    "Meringue": (spec(species="Swan", head="bird", snout=1.0, ears="none", tail="feathers", legs="plant",
                      wings="feather", fur="#F8F8F6", belly="#FFFFFF", accent="#E8E8E4", nose="#2A2A2A",
                      eyes="#A8D8A0", surface="feathers", extras=["longneck"], frame="f", height=0.92),
                 ["cloth:dress-red", "acc:pearls"], "Bazaar Regular", {"bazaar": 4, "club": 2}),
    "Moor": (spec(species="Water Buffalo", head="bovine", ears="small", horns="curved", horn="#4A4A48", tail="thin",
                  legs="hoof", fur="#3A3A3E", belly="#5A5A5E", accent="#1E1E22", eyes="#8A7A3A",
                  markings=["muzzle", "tailtip"], build=1.25),
             ["cloth:flannel", "cloth:jeans-blue", "cloth:boots"], "Estate Resident", {"estates": 3, "sandbox": 1}),
    "Mote": (spec(species="Anglerfish", head="fish", ears="none", tail="fin", legs="plant", fur="#1E5A6A",
                  belly="#2E7A8A", accent="#0E3A4A", eyes="#3A2A1A", surface="skin", markings=["belly"],
                  extras=["lure", "fins"], build=1.2),
             ["cloth:tee-black"], "Deep Sea Builder", {"sandbox": 4, "club": 1}),
    "MushTheHusky": (base("Husky", fur="#2A2A2E", accent="#F4F4F2", eyes="#7AC8F0", build=1.3, height=1.06),
                     ["cloth:hoodie-purple", "cloth:pants-track", "acc:collar-blue"], "Big Cuddly Husky",
                     {"club": 4, "bazaar": 1}),
    "Oxbow": (spec(species="River Dragon", head="reptile", snout=1.2, ears="fin", tail="thick", tail_size=1.4,
                   horns="dragon", horn="#C8D8C8", fur="#3A8A8A", belly="#A8D8C8", accent="#2A5A6A", eyes="#7A8A9A",
                   surface="scales", markings=["belly"], extras=["whiskers"], height=1.06, build=1.1),
              ["acc:scarf", "cloth:jeans-black"], "River Wanderer", {"sandbox": 3, "estates": 1}),
    "Ravel": (spec(species="Badger", head="ursine", snout=0.7, ears="small", tail="stub", legs="plant",
                   fur="#3A3A3E", belly="#5A5A5E", accent="#D8D8D8", eyes="#8A7A3A", markings=["blaze"],
                   build=1.2, height=0.94),
              ["cloth:vest", "acc:nerd"], "Estate Resident", {"estates": 3, "sandbox": 2}),
    "RedFawks": (base("Red Fox", eyes="#D89020", height=0.92, build=0.9),
                 ["cloth:tee-black", "cloth:jeans-black", "acc:bandana"], "Neon Paws Regular", {"club": 4, "bazaar": 1}),
    "Renamon": (spec(species="Renamon", head="canine", snout=1.1, ears="pointed", ear_size=1.4, tail="fluffy",
                     tail_size=1.3, fur="#F2C84A", belly="#F8F4EC", accent="#7A4FA8", eyes="#5A8AE8",
                     markings=["belly", "muzzle", "tailtip"], height=1.1, build=0.9),
                [], "Digital Fox", {"club": 3, "bazaar": 2}),
    "Rill": (spec(species="Kingfisher", head="bird", snout=1.3, ears="none", tail="stub", legs="plant",
                  wings="feather", fur="#2A9AC8", belly="#E8783A", accent="#1A5A8A", nose="#2A2A2A",
                  eyes="#8A7A3A", surface="feathers", markings=["belly"], height=0.92, build=1.08),
             ["cloth:tee-sky", "cloth:shorts-cargo"], "Sandbox Builder", {"sandbox": 3, "bazaar": 1}),
    "Serein": (spec(species="Rain Spirit", head="canine", snout=0.8, ears="long", ear_size=0.8, tail="fluffy",
                    fur="#9AB8D8", belly="#D8E8F8", accent="#F0F6FF", eyes="#D8A030", surface="spirit",
                    markings=["belly", "eartips", "tailtip"], extras=["glowcore"], frame="f", build=0.9),
               ["acc:flowers"], "Drizzle", {"bazaar": 2, "club": 2, "sandbox": 1}),
    "Skein": (spec(species="Alpaca", head="alpaca", ears="pointed", tail="puff", legs="hoof", fur="#F0E6D0",
                   belly="#F8F0E0", accent="#3A3A3A", eyes="#C89030", markings=["eartips"], extras=["longneck"],
                   frame="f", build=0.9),
              ["cloth:sweater", "acc:scarf"], "Estate Resident", {"estates": 3, "bazaar": 2}),
    "Slag": (spec(species="Iron Golem", head="golem", ears="none", tail=None, legs="plant", fur="#6A6058",
                  belly="#6A6058", accent="#C8783A", eyes="#FF9A30", surface="metal", markings=[],
                  extras=["plates", "glowcore"], build=1.35, height=1.1),
             [], "Sandbox Builder", {"sandbox": 5}),
    "Sundog": (spec(species="Coyote", head="canine", snout=1.15, ears="pointed", ear_size=1.2, tail="fluffy",
                    fur="#A8886A", belly="#E8DCC8", accent="#5A4A3A", eyes="#A8D8A0",
                    markings=["belly", "muzzle", "tailtip"], height=0.95, build=0.9),
               ["cloth:tee-red", "cloth:shorts-cargo", "acc:cowboy"], "Desert Drifter", {"club": 3, "sandbox": 2}),
    "Tallow": (spec(species="Musk Ox", head="bovine", ears="small", horns="curved", horn="#C8B898", tail="stub",
                    legs="hoof", fur="#5A3E2A", belly="#7A5A40", accent="#3A2A1A", eyes="#7A8A9A",
                    extras=["ruff", "hair"], build=1.3, height=1.08),
               ["cloth:flannel", "cloth:jeans-blue", "cloth:boots"], "Estate Resident", {"estates": 3, "bazaar": 1}),
    "Tamarack": (spec(species="Caribou", head="deer", ears="pointed", tail="puff", legs="hoof", horns="antlers",
                      horn="#C8B080", fur="#5A3E28", belly="#E8E0D0", accent="#3A2818", eyes="#3A2A1A",
                      markings=["muzzle"], extras=["ruff", "palmate"], build=1.2, height=1.08),
                 ["cloth:jacket-denim", "cloth:jeans-blue", "cloth:boots"], "Estate Resident",
                 {"estates": 3, "sandbox": 1}),
    "Tumbleweed": (base("Kangaroo", fur="#B8603A", accent="#3A2A20", build=1.2),
                   ["cloth:tank-white", "cloth:shorts-cargo", "acc:cap-blue"], "Outback Builder",
                   {"sandbox": 3, "club": 2}),
    "Waxwing": (spec(species="Cedar Waxwing", head="bird", snout=0.6, ears="none", tail="feathers", legs="plant",
                     wings="feather", fur="#A8865A", belly="#E8D8A0", accent="#1E1E1E", wingtip="#C83030",
                     crest="#A8865A", nose="#2A2A2A", eyes="#A8D8A0", surface="feathers", markings=["belly", "mask"],
                     extras=["crest"], frame="f", height=0.9),
                ["cloth:tee-white", "cloth:skirt-pink"], "Bazaar Regular", {"bazaar": 4, "club": 1}),
    "WinterDragon": (base("Dragon", fur="#1E1E22", belly="#F4F4F4", accent="#F4F4F4", eyes="#E8B030", horn="#E8E8E8",
                          surface="fur", build=1.25, height=1.12),
                     ["cloth:jacket-leather", "cloth:jeans-black", "acc:chain"], "Estate Resident",
                     {"estates": 2, "club": 2}),
    "XavierPup": (base("German Shepherd", eyes="#6A4A2A"),
                  ["cloth:tee-sky", "cloth:jeans-blue", "acc:collar-black"], "Good Boy", {"club": 3, "bazaar": 2}),
}
# who owns which lot in Pawprint Estates (lots 4, 6, 11 and 15 start free)
HOMES = {"Tamarack": 0, "Moor": 1, "Tallow": 2, "Juniper": 3, "Hush": 5, "Mallowroot": 7, "WinterDragon": 8,
         "Crispin": 9, "Latchkey": 10, "Skein": 12, "Dewdrop": 13, "Ravel": 14}


def _h(name):
    return int(hashlib.md5(name.encode()).hexdigest(), 16)


def surname(name):
    return SURNAMES[_h(name) % len(SURNAMES)]


def born(name):
    """When their account was made (Second Life opened in June 2003)."""
    return (datetime.date(2003, 6, 23) + datetime.timedelta(days=_h(name) % 520)).strftime("%m/%d/%Y")


def look_for(name, species="", fur_colour=""):
    """Their avatar (a guess for anyone not in the table)."""
    if name in LOOKS:
        return LOOKS[name]
    text = (species + " " + name).lower()
    pick = "Red Fox"
    for word, preset in (("wolf", "Grey Wolf"), ("husky", "Husky"), ("shepherd", "German Shepherd"), ("dog", "Husky"),
                         ("fox", "Red Fox"), ("lion", "Lion"), ("tiger", "Tiger"), ("lynx", "Lynx"), ("cat", "Housecat"),
                         ("rabbit", "Bunny"), ("bunny", "Bunny"), ("dragon", "Dragon"), ("gryphon", "Gryphon"),
                         ("bird", "Songbird"), ("deer", "Deer"), ("bear", "Bear"), ("otter", "Otter"),
                         ("raccoon", "Raccoon"), ("skunk", "Skunk"), ("kangaroo", "Kangaroo"), ("frog", "Frog"),
                         ("shark", "Shark")):
        if word in text:
            pick = preset
            break
    return (base(pick), ["cloth:tee-white", "cloth:jeans-blue"], "Resident", {"club": 2, "bazaar": 2, "sandbox": 1})


def _load(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def profile(name, aim_icon=None):
    """What their Second Life profile shows."""
    rec = _load(FURDIR / f"{name}.json")
    fs = rec.get("fursona") or {}
    personal = rec.get("personal") or {}
    rel = rec.get("relationship") or {}
    codes = rec.get("codes") or {}
    picture = None
    if aim_icon and (AIM_DIR / "assets" / "icons" / aim_icon).exists():
        picture = AIM_DIR / "assets" / "icons" / aim_icon
    elif rec.get("icon") and (FURDIR.parent / rec["icon"]).exists():
        picture = FURDIR.parent / rec["icon"]
    about = (rec.get("summary") or "").strip()
    species = fs.get("species", "")
    look = ", ".join(x for x in (fs.get("colors"), f"{fs['eyes']} eyes" if fs.get("eyes") else "", fs.get("build"))
                     if x)
    partner = ""
    if rel.get("status"):
        partner = rel["status"] + (f" ({rel['partner']})" if rel.get("partner") else "")
    return {"name": name, "full": f"{name} {surname(name)}", "born": born(name), "about": about, "species": species,
            "look": look, "interests": (rec.get("interests") or "").strip(), "pronouns": personal.get("pronouns", ""),
            "partner": partner, "furcode": codes.get("furcode", ""),
            "yiffcode": codes.get("yiffcode", "") if codes.get("yiff_public") else "", "picture": picture}
