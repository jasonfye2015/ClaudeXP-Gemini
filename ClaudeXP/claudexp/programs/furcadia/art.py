"""Claudecadia's art, painted in code: isometric floor tiles, objects, and furres recoloured from a look.

Every picture can be replaced by a file in assets/furcadia/ (see 'Features to add.txt' and the README there):
  tiles/<floor>.png               a 64 x 32 diamond floor tile
  objects/<object>.png            any size; its bottom centre sits 16 px below the middle of its tile
  furres/<kind>/<pose>_<facing>.png   48 x 64, feet at (24, 58); pure key colours are recoloured per furre:
                                  #FF00FF fur, #00FFFF markings, #FFFF00 eyes, #00FF00 clothes (darker shades of
                                  each key colour are kept darker)
  splash.png / splash.jpg         the title screen, with an Enter... button under it
"""
import random
from dataclasses import dataclass

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QIcon, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
                           QPolygonF, QRadialGradient)

from ...paths import ROOT

ART = ROOT / "assets" / "furcadia"
TW, TH = 64, 32                       # a floor tile's diamond
FW, FH, FOOT = 48, 64, 58             # a furre's canvas and where its feet are

# Facings: which way a furre looks on screen.  SE and SW show the face, NE and NW the back.
SE, SW, NE, NW = 0, 1, 2, 3
STEP = {NE: (0, -1), SE: (1, 0), SW: (0, 1), NW: (-1, 0)}

# ---- the colour palette (Claudecadia gave every furre a few remappable colours) --------------------------------
PALETTE = {
    "fur": ["#C8642E", "#E8A050", "#8A5A32", "#5A3A22", "#2E2420", "#F2F0EA", "#B8B8B8", "#6E6E74", "#E8D6A8",
            "#D9B23A", "#4A70B8", "#7AA8D8", "#5E8A3A", "#3E7A6E", "#9A4AA0", "#C04A5A", "#F0A8C0", "#2A3C66"],
    "markings": ["#F2F0EA", "#E8D6A8", "#2E2420", "#C8642E", "#B8B8B8", "#F0A8C0", "#7AA8D8", "#D9B23A",
                 "#5A3A22", "#6E6E74", "#5E8A3A", "#9A4AA0"],
    "eyes": ["#3A7AD8", "#5EA040", "#C88A20", "#7A4A22", "#9A4AA0", "#C03030", "#3AB0B0", "#202020"],
    "clothes": ["", "#C03030", "#3050B0", "#3A8A40", "#E0C030", "#7A3AA0", "#202028", "#F0F0F0", "#E07A20",
                "#40A0C0", "#8A5A32", "#E070A0"],
}

# words in a description -> a colour
COLOUR_WORDS = [
    ("arctic", "#F2F0EA"), ("snow", "#F2F0EA"), ("white", "#F2F0EA"), ("cream", "#E8D6A8"), ("ivory", "#F2F0EA"),
    ("silver", "#C8C8CC"), ("grey", "#9A9AA0"), ("gray", "#9A9AA0"), ("slate", "#6E6E74"), ("charcoal", "#3A3A3E"),
    ("black", "#2A2426"), ("ebony", "#2A2426"), ("brown", "#7A4E2E"), ("chocolate", "#5A3A22"),
    ("mocha", "#7A5238"), ("tan", "#C8A070"), ("sandy", "#D8B880"), ("sand", "#D8B880"), ("fawn", "#C89A68"),
    ("golden", "#D9A830"), ("gold", "#D9A830"), ("honey", "#D9A040"), ("blond", "#E8D090"),
    ("yellow", "#E8C83A"), ("orange", "#E07A20"), ("ginger", "#D0702A"), ("rust", "#A8502A"),
    ("red", "#C8442E"), ("crimson", "#A82030"), ("pink", "#F0A8C0"), ("rose", "#E07A98"),
    ("purple", "#8A4AA8"), ("violet", "#9A5AC8"), ("lavender", "#B8A0E0"), ("blue", "#4A70C8"),
    ("navy", "#2A3C66"), ("azure", "#5A9AE0"), ("aqua", "#40B8C0"), ("teal", "#2E8A88"),
    ("turquoise", "#40C0B0"), ("green", "#4E9A3A"), ("emerald", "#2E9A5A"), ("olive", "#7A7A3A"),
    ("moss", "#5E7A3A"), ("copper", "#B8683A"), ("brass", "#C8A040"), ("bronze", "#A0703A"),
    ("iron", "#6E6E74"), ("steel", "#8A9098"),
]

# species words -> a body kind
KINDS = {
    "canine": ("Canine", ["fox", "vixen", "wolf", "husky", "dog", "coyote", "jackal", "shepherd", "renamon", "pup",
                          "fennec", "dingo", "fawks", "malamute", "collie", "hound", "canine", "lupine"]),
    "feline": ("Feline", ["cat", "kitty", "lion", "tiger", "lynx", "leopard", "cheetah", "panther", "cougar",
                          "puma", "ocelot", "feline", "kat", "jaguar", "serval"]),
    "lapine": ("Lapine", ["rabbit", "bunny", "hare", "kangaroo", "wallaby", "lapine"]),
    "rodent": ("Rodent", ["mouse", "rat", "squirrel", "hamster", "porcupine", "opossum", "possum", "chipmunk",
                          "rodent", "gerbil", "hedgehog"]),
    "mustelid": ("Musteline", ["otter", "ferret", "weasel", "badger", "skunk", "mink", "raccoon", "stoat",
                               "wolverine"]),
    "ursine": ("Ursine", ["bear", "panda", "koala"]),
    "avian": ("Avian", ["bird", "owl", "cockatoo", "swan", "kingfisher", "waxwing", "parrot", "raven", "crow",
                        "eagle", "hawk", "gryphon", "griffin", "phoenix", "falcon", "jay", "sparrow", "avian"]),
    "dragon": ("Dragon", ["dragon", "drake", "wyvern", "wyrm"]),
    "equine": ("Equine", ["horse", "pony", "zebra", "unicorn", "alpaca", "llama", "donkey", "mare", "stallion"]),
    "bovine": ("Bovine", ["buffalo", "musk ox", " ox", "bull", "cow", "goat", "sheep", "ram", "bison", "yak",
                          "bovine"]),
    "cervine": ("Cervine", ["deer", "caribou", "reindeer", "elk", "moose", "stag", "doe", "antelope"]),
    "reptile": ("Reptilian", ["lizard", "frog", "chameleon", "gecko", "snake", "turtle", "croc", "iguana",
                              "kobold", "toad", "newt", "salamander", "reptile"]),
    "aquatic": ("Aquatic", ["fish", "anglerfish", "shark", "dolphin", "orca", "seal", "whale"]),
    "insect": ("Insectoid", ["cicada", "moth", "butterfly", "bee", "beetle", "mantis", "dragonfly"]),
    "other": ("Other", ["golem", "spirit", "robot", "construct"]),
}
KIND_ORDER = list(KINDS)


@dataclass
class Look:
    kind: str = "canine"
    fur: str = "#C8642E"
    markings: str = "#F2F0EA"
    eyes: str = "#3A7AD8"
    clothes: str = ""           # "" = no clothes
    wings: bool = False

    def key(self):
        return (self.kind, self.fur, self.markings, self.eyes, self.clothes, self.wings)

    def to_json(self):
        return {"kind": self.kind, "fur": self.fur, "markings": self.markings, "eyes": self.eyes,
                "clothes": self.clothes, "wings": self.wings}

    @classmethod
    def from_json(cls, d):
        d = d or {}
        look = cls()
        for k in ("kind", "fur", "markings", "eyes", "clothes"):
            if isinstance(d.get(k), str):
                setattr(look, k, d[k])
        look.wings = bool(d.get("wings", look.wings))
        if look.kind not in KINDS:
            look.kind = "other"
        return look


def _kind_hits(text):
    """(position, kind, word) for every species word in text, as whole words ('kat' isn't in 'cockatoo')."""
    import re
    low = (text or "").lower()
    hits = []
    for kind, (_label, words) in KINDS.items():
        for w in words:
            m = re.search(r"(?<![a-z])" + re.escape(w.strip()) + r"(?:s|es|xo)?(?![a-z])", low)
            if m:
                hits.append((m.start(), kind, w.strip()))
    return sorted(hits)


def kind_for(species):
    hits = _kind_hits(species)
    return hits[0][1] if hits else "other"


def species_word(text):
    """The first species named in a description ('a furry whose fursona is an arctic fox' -> 'fox')."""
    hits = _kind_hits(text)
    return hits[0][2] if hits else ""


def _colours_in(text):
    """Colours in the order a description names them (leaving out eye colours)."""
    import re
    low = re.sub(r"[a-z-]+(?:[ -][a-z]+)? eyes|[a-z]+-eyed|eyes are [a-z]+", " ", (text or "").lower())
    found = []
    for word, hexc in COLOUR_WORDS:
        i = low.find(word)
        if i >= 0:
            found.append((i, hexc))
    found.sort()
    out = []
    for _i, c in found:
        if c not in out:
            out.append(c)
    return out


def _eye_colour(text):
    low = (text or "").lower()
    for word, hexc in (("blue", "#3A7AD8"), ("green", "#5EA040"), ("amber", "#C88A20"), ("gold", "#C8A020"),
                       ("brown", "#7A4A22"), ("hazel", "#8A7A3A"), ("violet", "#9A4AA0"), ("purple", "#9A4AA0"),
                       ("red", "#C03030"), ("grey", "#7A8A98"), ("gray", "#7A8A98"), ("silver", "#A8B0B8"),
                       ("yellow", "#D8C030"), ("orange", "#E07A20"), ("black", "#202020")):
        for phrase in (f"{word} eyes", f"{word}-eyed", f"{word} eyed", f"eyes are {word}"):
            if phrase in low:
                return hexc
    return None


# a species' usual colours, for descriptions that don't name any: (fur, markings)
USUAL_COLOURS = {"husky": ("#8A9098", "#F2F0EA"), "wolf": ("#8A8A90", "#E8E4DC"), "renamon": ("#E8C050", "#F2F0EA"),
                 "shepherd": ("#8A5A32", "#2E2420"), "calico": ("#E8A050", "#F2F0EA"), "dragon": ("#3E7A6E", "#E8D6A8"),
                 "arctic": ("#F2F0EA", "#B8B8B8"), "red fox": ("#C8642E", "#F2F0EA")}


def look_from_text(species, text, seed=""):
    """A sensible look from a species and a description ('a red fox with a white-tipped tail')."""
    kind = kind_for(species)
    rnd = random.Random(seed or species)
    cols = _colours_in(text)
    defaults = {"canine": "#C8642E", "feline": "#D9A830", "lapine": "#C8A070", "rodent": "#8A7A70",
                "mustelid": "#6E4A2E", "ursine": "#6E4A2E", "avian": "#F2F0EA", "dragon": "#3E7A6E",
                "equine": "#8A5A32", "bovine": "#5A3A22", "cervine": "#A8784A", "reptile": "#5E9A3A",
                "aquatic": "#4A70B8", "insect": "#5E8A3A", "other": "#8A9098"}
    low_sp = (species or "").lower()
    usual = next((cm for word, cm in USUAL_COLOURS.items() if word in low_sp), None)
    fur = cols[0] if cols else usual[0] if usual else defaults[kind]
    rest = [c for c in cols[1:] if c != fur]
    markings = rest[0] if rest else usual[1] if usual and not cols else         ("#F2F0EA" if fur not in ("#F2F0EA",) else "#B8B8B8")
    eyes = _eye_colour(text) or rnd.choice(PALETTE["eyes"])
    low = (text or "").lower()
    clothes = ""
    if any(w in low for w in ("hoodie", "shirt", "jacket", "vest", "sweater", "coat", "scarf", "overalls",
                              "t-shirt", "tee", "dress", "uniform", "tank top", "flannel")):
        clothes = rnd.choice([c for c in PALETTE["clothes"] if c])
    if "doesn't wear clothes" in low or "no clothes" in low:
        clothes = ""
    wings = kind in ("avian", "dragon", "insect") or "wing" in low
    return Look(kind, fur, markings, eyes, clothes, wings)


# ---- helpers --------------------------------------------------------------------------------------------------

def _shade(hexc, f):
    c = QColor(hexc)
    if f < 1:
        return c.darker(int(100 / max(0.05, f)))
    return c.lighter(int(100 * f))


def _override(path):
    if path.exists():
        pm = QPixmap(str(path))
        if not pm.isNull():
            return pm
    return None


def _diamond(w=TW, h=TH, ox=0.0, oy=0.0):
    return QPolygonF([QPointF(ox + w / 2, oy), QPointF(ox + w, oy + h / 2), QPointF(ox + w / 2, oy + h),
                      QPointF(ox, oy + h / 2)])


# ---- floor tiles ----------------------------------------------------------------------------------------------

FLOORS = {
    # name: (base colour, speckle colours, walkable)
    "grass": ("#5E9A3A", ["#6EAA44", "#4E8A30", "#7AB64E"], True),
    "flowers": ("#5E9A3A", ["#6EAA44", "#4E8A30"], True),
    "darkgrass": ("#3E6A2E", ["#4A7A36", "#345C26", "#527E3A"], True),
    "dirt": ("#9A7448", ["#8A6440", "#AA8456", "#7E5A38"], True),
    "cobble": ("#9A948A", ["#8A847A", "#AAA49A", "#7A746C"], True),
    "flagstone": ("#8C8478", ["#7C7468", "#9C9488"], True),
    "wood": ("#9A6A3C", ["#8A5C32", "#AA7A48"], True),
    "boardwalk": ("#B08A5A", ["#A07A4C", "#C09A68"], True),
    "sand": ("#E2CC96", ["#D6BE86", "#EED8A4", "#CCB27A"], True),
    "rug": ("#9A2E2E", ["#B83A3A", "#7A2424"], True),
    "water": ("#3A78C0", ["#4A88D0", "#2E6AB0", "#5A98DC"], False),
    "deepwater": ("#2A5A9C", ["#3468AA", "#224E8C"], False),
    "void": ("#000000", [], False),
    "snow": ("#EEF2F8", ["#FFFFFF", "#DCE4F0", "#D0DAEA"], True),
    "ice": ("#B8DCF0", ["#D0ECFA", "#A0CCE8"], True),
    "cave": ("#5A5048", ["#4A4038", "#6A6058", "#504640"], True),
    "marble": ("#E8E4DC", ["#D8D2C8", "#F4F0EA"], True),
    "cloud": ("#F4F6FF", ["#FFFFFF", "#E0E6F8"], True),
    "sky": ("#9CC8F0", ["#B0D4F4", "#8ABCE8"], False),
    "wheat": ("#D8B850", ["#C8A840", "#E8C860", "#B89838"], True),
    "seafloor": ("#C8B88A", ["#B8A87A", "#D8C89A", "#E0D0A8"], True),
    "rainbow": ("#E04040", [], True),
    "mud": ("#6A5A3A", ["#5A4A2E", "#7A6A48"], True),
}


class Tiles:
    """Floor tile pixmaps (three variants each), cached."""

    def __init__(self):
        self.cache = {}

    def get(self, name, variant=0):
        key = (name, variant % 3)
        if key not in self.cache:
            pm = _override(ART / "tiles" / f"{name}.png")
            self.cache[key] = pm if pm is not None else self._paint(name, variant % 3)
        return self.cache[key]

    def _paint(self, name, variant):
        base, specks, _walk = FLOORS.get(name, FLOORS["grass"])
        pm = QPixmap(TW, TH)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        shape = QPainterPath()
        shape.addPolygon(_diamond())
        shape.closeSubpath()
        p.setClipPath(shape)
        p.fillRect(0, 0, TW, TH, QColor(base))
        rnd = random.Random(f"{name}{variant}")
        if name in ("wood", "boardwalk"):
            p.setPen(QPen(_shade(base, 0.7), 1))
            for i in range(-4, 8):
                y = i * 6 + 2
                p.drawLine(QPointF(0, y + TW / 4), QPointF(TW, y - TW / 4 + 16))
            for c in specks:
                p.setPen(QColor(c))
                for _ in range(20):
                    p.drawPoint(rnd.randrange(TW), rnd.randrange(TH))
        elif name in ("cobble", "flagstone"):
            for _ in range(14 if name == "cobble" else 6):
                x, y = rnd.uniform(0, TW), rnd.uniform(0, TH)
                w = rnd.uniform(9, 14) if name == "cobble" else rnd.uniform(16, 24)
                p.setPen(QPen(_shade(base, 0.72), 1))
                p.setBrush(QColor(rnd.choice(specks)))
                p.drawEllipse(QRectF(x - w / 2, y - w / 4, w, w / 2))
        elif name == "rug":
            p.setPen(QPen(QColor("#D8B04A"), 2))
            p.setBrush(Qt.NoBrush)
            p.drawPolygon(_diamond(TW - 16, TH - 8, 8, 4))
            for c in specks:
                p.setPen(QColor(c))
                for _ in range(30):
                    p.drawPoint(rnd.randrange(TW), rnd.randrange(TH))
        elif name == "ice":
            p.setPen(QPen(QColor(255, 255, 255, 150), 1))
            for _ in range(5):
                x, y = rnd.uniform(0, TW), rnd.uniform(0, TH)
                p.drawLine(QPointF(x, y), QPointF(x + rnd.uniform(6, 14), y - rnd.uniform(2, 6)))
            p.setPen(QColor(specks[1]))
            for _ in range(30):
                p.drawPoint(rnd.randrange(TW), rnd.randrange(TH))
        elif name == "marble":
            p.setPen(QPen(QColor(150, 140, 130, 110), 1))
            for _ in range(3):
                path = QPainterPath(QPointF(rnd.uniform(0, TW), rnd.uniform(0, TH)))
                path.cubicTo(QPointF(rnd.uniform(0, TW), rnd.uniform(0, TH)),
                             QPointF(rnd.uniform(0, TW), rnd.uniform(0, TH)),
                             QPointF(rnd.uniform(0, TW), rnd.uniform(0, TH)))
                p.drawPath(path)
            p.setPen(QPen(QColor(120, 110, 100, 90), 1))
            p.setBrush(Qt.NoBrush)
            p.drawPolygon(_diamond(TW - 2, TH - 1, 1, 0.5))
        elif name == "cloud":
            p.setPen(Qt.NoPen)
            for _ in range(10):
                p.setBrush(QColor(rnd.choice(["#FFFFFF", "#E8ECFA", "#F8FAFF"])))
                p.drawEllipse(QPointF(rnd.uniform(0, TW), rnd.uniform(0, TH)), rnd.uniform(5, 11), rnd.uniform(3, 6))
        elif name == "sky":
            p.setPen(Qt.NoPen)
            for _ in range(2):
                p.setBrush(QColor(255, 255, 255, 90))
                p.drawEllipse(QPointF(rnd.uniform(8, TW - 8), rnd.uniform(6, TH - 6)), rnd.uniform(8, 14), 3)
        elif name == "wheat":
            for _ in range(70):
                x, y = rnd.randrange(TW), rnd.randrange(2, TH)
                p.setPen(QColor(rnd.choice(specks)))
                p.drawLine(x, y, x + rnd.choice((-1, 0, 1)), y - 4)
        elif name == "rainbow":
            bands = ["#E04040", "#F08A30", "#F0D040", "#50B850", "#4A80D8", "#8A50C8"]
            for i, c in enumerate(bands):
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(c))
                off = i * TW / len(bands) / 2
                p.drawPolygon(QPolygonF([QPointF(off, TH / 2 + off / 2), QPointF(TW / 2 + off, off / 2),
                                         QPointF(TW / 2 + off + TW / 12, off / 2 + TW / 24),
                                         QPointF(off + TW / 12, TH / 2 + off / 2 + TW / 24)]))
        else:
            for _ in range(140):
                p.setPen(QColor(rnd.choice(specks)) if specks else Qt.NoPen)
                x, y = rnd.randrange(TW), rnd.randrange(TH)
                if name in ("water", "deepwater"):
                    p.drawLine(x, y, x + rnd.randint(2, 5), y)
                else:
                    p.drawPoint(x, y)
            if name in ("grass", "darkgrass"):
                p.setPen(QColor(specks[0]))
                for _ in range(12):
                    x, y = rnd.randrange(4, TW - 4), rnd.randrange(4, TH - 2)
                    p.drawLine(x, y, x + rnd.choice((-1, 1)), y - 3)
            if name == "flowers":
                for _ in range(9):
                    x, y = rnd.randrange(10, TW - 10), rnd.randrange(6, TH - 6)
                    p.setPen(Qt.NoPen)
                    p.setBrush(QColor(rnd.choice(["#F0E040", "#F070A0", "#FFFFFF", "#A070F0", "#F08040"])))
                    p.drawEllipse(QRectF(x - 2, y - 1.5, 4, 3))
                    p.setBrush(QColor("#F8F0A0"))
                    p.drawEllipse(QRectF(x - 0.8, y - 0.6, 1.6, 1.2))
        p.end()
        return pm


def walkable_floor(name):
    return FLOORS.get(name, FLOORS["grass"])[2]


# ---- objects --------------------------------------------------------------------------------------------------
# name: (walkable, seat)
OBJECTS = {
    "tree": (False, False), "pine": (False, False), "palm": (False, False), "bush": (False, False),
    "rock": (False, False), "bench": (True, True), "lamp": (False, False), "fountain": (False, False),
    "fence": (False, False), "sign": (False, False), "portal": (True, False), "campfire": (False, False),
    "log": (True, True), "mushroom": (True, False), "table": (False, False), "chair": (True, True),
    "umbrella": (False, False), "bookshelf": (False, False), "fireplace": (False, False),
    "wall": (False, False), "woodwall": (False, False), "barrel": (False, False), "crate": (False, False),
    "stool": (True, True), "lantern": (False, False), "counter": (False, False), "plant": (False, False),
    "cushion": (True, True), "shell": (True, False), "bigtree": (False, False),
    "snowpine": (False, False), "snowman": (False, False), "crystal": (False, False),
    "stalagmite": (False, False), "column": (False, False), "ruin": (False, False), "statue": (False, False),
    "telescope": (False, False), "cactus": (False, False), "tent": (False, False), "hay": (True, True),
    "scarecrow": (False, False), "sunflower": (False, False), "lilypad": (True, False), "reeds": (False, False),
    "coral": (False, False), "kelp": (False, False), "stall": (False, False), "torch": (False, False),
    "chest": (False, False),
}
# things that glow in the dark dreams: name -> (radius, colour)
LIGHTS = {"campfire": (90, (120, 70, 20)), "lantern": (40, (120, 80, 30)), "lamp": (44, (110, 90, 40)),
          "torch": (60, (130, 70, 20)), "crystal": (52, (60, 80, 140)), "stall": (56, (120, 80, 30)),
          "fireplace": (80, (120, 60, 20))}


def obj_walkable(name):
    return OBJECTS.get(name, (False, False))[0]


def obj_seat(name):
    return OBJECTS.get(name, (False, False))[1]


class Objects:
    """Object sprites. Each is (pixmap, anchor) where anchor is the canvas point that sits on the tile centre."""

    def __init__(self):
        self.cache = {}

    def get(self, name, frame=0, variant=0):
        animated = name in ("portal", "campfire", "fountain", "lantern", "fireplace", "crystal", "torch", "kelp")
        key = (name, frame % 4 if animated else 0, variant % 3)
        if key not in self.cache:
            pm = _override(ART / "objects" / f"{name}.png")
            if pm is not None:
                self.cache[key] = (pm, QPointF(pm.width() / 2, pm.height() - 16))
            else:
                self.cache[key] = self._paint(name, key[1], key[2])
        return self.cache[key]

    def _paint(self, name, frame, variant):
        w, h = 96, 144
        pm = QPixmap(w, h)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = w / 2, h - 16          # the tile centre
        getattr(self, "_" + name, self._crate)(p, cx, cy, frame, random.Random(f"{name}{variant}"))
        p.end()
        return pm, QPointF(cx, cy)

    # each painter draws around (cx, cy), the middle of its tile
    @staticmethod
    def _shadow(p, cx, cy, rw=20, rh=8):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 60))
        p.drawEllipse(QPointF(cx, cy + 2), rw, rh)

    @staticmethod
    def _box(p, cx, cy, hw, hh, height, top, left, right, outline=None):
        """An isometric box sitting on the tile: half-width hw, half-depth hh, height."""
        pen = QPen(outline or QColor(0, 0, 0, 90), 1)
        p.setPen(pen)
        p.setBrush(QColor(left))
        p.drawPolygon(QPolygonF([QPointF(cx - hw, cy), QPointF(cx, cy + hh), QPointF(cx, cy + hh - height),
                                 QPointF(cx - hw, cy - height)]))
        p.setBrush(QColor(right))
        p.drawPolygon(QPolygonF([QPointF(cx, cy + hh), QPointF(cx + hw, cy), QPointF(cx + hw, cy - height),
                                 QPointF(cx, cy + hh - height)]))
        p.setBrush(QColor(top))
        p.drawPolygon(QPolygonF([QPointF(cx - hw, cy - height), QPointF(cx, cy + hh - height),
                                 QPointF(cx + hw, cy - height), QPointF(cx, cy - hh - height)]))

    def _tree(self, p, cx, cy, frame, rnd, scale=1.0):
        self._shadow(p, cx, cy, 24 * scale, 9 * scale)
        p.setPen(QPen(QColor("#3E2A18"), 1))
        p.setBrush(QColor("#6A4A2A"))
        p.drawRect(QRectF(cx - 4 * scale, cy - 34 * scale, 8 * scale, 34 * scale))
        greens = ["#2E6A2A", "#3A7E32", "#4A9040", "#5AA048"]
        for i, (dx, dy, r) in enumerate(((-12, -48, 18), (12, -50, 18), (0, -64, 20), (-6, -56, 16),
                                         (8, -60, 15))):
            p.setPen(QPen(QColor("#1E4A1A"), 1))
            p.setBrush(QColor(greens[min(3, i % 4)]))
            p.drawEllipse(QPointF(cx + dx * scale, cy + dy * scale), r * scale, r * 0.85 * scale)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 40))
        p.drawEllipse(QPointF(cx - 4 * scale, cy - 70 * scale), 8 * scale, 5 * scale)

    def _bigtree(self, p, cx, cy, frame, rnd):
        self._tree(p, cx, cy, frame, rnd, 1.35)

    def _pine(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 18, 7)
        p.setPen(QPen(QColor("#3E2A18"), 1))
        p.setBrush(QColor("#5A3A22"))
        p.drawRect(QRectF(cx - 3, cy - 14, 6, 14))
        for i, (y, hw) in enumerate(((-14, 22), (-34, 18), (-52, 14), (-68, 9))):
            p.setPen(QPen(QColor("#163A22"), 1))
            p.setBrush(QColor(["#1E5A32", "#24683A", "#2C7442", "#34804A"][i]))
            p.drawPolygon(QPolygonF([QPointF(cx - hw, cy + y), QPointF(cx + hw, cy + y),
                                     QPointF(cx, cy + y - 30)]))

    def _palm(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 16, 6)
        path = QPainterPath(QPointF(cx - 3, cy))
        path.cubicTo(QPointF(cx - 4, cy - 30), QPointF(cx + 8, cy - 50), QPointF(cx + 6, cy - 78))
        p.setPen(QPen(QColor("#8A6A3A"), 6, Qt.SolidLine, Qt.RoundCap))
        p.drawPath(path)
        p.setPen(QPen(QColor("#6A4A2A"), 1))
        for i in range(8):
            y = cy - 8 - i * 9
            p.drawLine(QPointF(cx - 6 + i * 0.9, y), QPointF(cx + 2 + i * 0.9, y + 1))
        top = QPointF(cx + 6, cy - 78)
        for ang, ln in ((-160, 34), (-120, 30), (-60, 30), (-20, 34), (170, 26), (10, 26), (-90, 22)):
            from math import cos, radians, sin
            end = QPointF(top.x() + cos(radians(ang)) * ln, top.y() + sin(radians(ang)) * ln * 0.6 + 10)
            leaf = QPainterPath(top)
            mid = QPointF((top.x() + end.x()) / 2, (top.y() + end.y()) / 2 - 8)
            leaf.quadTo(mid, end)
            p.setPen(QPen(QColor("#2E7A32"), 5, Qt.SolidLine, Qt.RoundCap))
            p.drawPath(leaf)
            p.setPen(QPen(QColor("#4AA048"), 2, Qt.SolidLine, Qt.RoundCap))
            p.drawPath(leaf)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#6A4A22"))
        for dx in (-3, 3, 0):
            p.drawEllipse(QPointF(top.x() + dx, top.y() + 4), 3, 3)

    def _bush(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 18, 7)
        for dx, dy, r, c in ((-8, -8, 11, "#3A7E32"), (8, -9, 11, "#3A7E32"), (0, -15, 12, "#4A9040")):
            p.setPen(QPen(QColor("#1E4A1A"), 1))
            p.setBrush(QColor(c))
            p.drawEllipse(QPointF(cx + dx, cy + dy), r, r * 0.8)
        p.setPen(Qt.NoPen)
        for _ in range(5):
            p.setBrush(QColor(rnd.choice(["#E04040", "#F0F0F0", "#F0C040"])))
            p.drawEllipse(QPointF(cx + rnd.uniform(-14, 14), cy - rnd.uniform(6, 22)), 1.6, 1.6)

    def _rock(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 16, 6)
        p.setPen(QPen(QColor("#4A4A4E"), 1))
        p.setBrush(QColor("#8A8A90"))
        p.drawPolygon(QPolygonF([QPointF(cx - 15, cy), QPointF(cx - 11, cy - 12), QPointF(cx - 2, cy - 18),
                                 QPointF(cx + 10, cy - 14), QPointF(cx + 15, cy - 2), QPointF(cx + 4, cy + 4)]))
        p.setBrush(QColor("#A8A8AE"))
        p.drawPolygon(QPolygonF([QPointF(cx - 11, cy - 12), QPointF(cx - 2, cy - 18), QPointF(cx + 10, cy - 14),
                                 QPointF(cx, cy - 9)]))

    def _bench(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 20, 6)
        wood, dark = QColor("#9A6A3C"), QColor("#6A4626")
        p.setPen(QPen(dark, 2))
        for dx in (-14, 12):
            p.drawLine(QPointF(cx + dx, cy + 2 - dx * 0.25), QPointF(cx + dx, cy - 8 - dx * 0.25))
        p.setPen(QPen(dark, 1))
        p.setBrush(wood)
        p.drawPolygon(QPolygonF([QPointF(cx - 20, cy - 6), QPointF(cx + 4, cy + 6), QPointF(cx + 20, cy - 2),
                                 QPointF(cx - 4, cy - 14)]))
        p.drawPolygon(QPolygonF([QPointF(cx - 20, cy - 6), QPointF(cx - 4, cy - 14), QPointF(cx - 4, cy - 26),
                                 QPointF(cx - 20, cy - 18)]))

    def _lamp(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 8, 4)
        p.setPen(QPen(QColor("#1E1E24"), 3))
        p.drawLine(QPointF(cx, cy), QPointF(cx, cy - 58))
        p.setPen(QPen(QColor("#1E1E24"), 1))
        p.setBrush(QColor("#2A2A30"))
        p.drawRect(QRectF(cx - 5, cy - 4, 10, 4))
        glow = QRadialGradient(QPointF(cx, cy - 64), 22)
        glow.setColorAt(0, QColor(255, 230, 150, 140))
        glow.setColorAt(1, QColor(255, 230, 150, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx, cy - 64), 22, 22)
        p.setPen(QPen(QColor("#1E1E24"), 1))
        p.setBrush(QColor("#FFE9A0"))
        p.drawPolygon(QPolygonF([QPointF(cx - 6, cy - 58), QPointF(cx + 6, cy - 58), QPointF(cx + 8, cy - 70),
                                 QPointF(cx - 8, cy - 70)]))
        p.setBrush(QColor("#2A2A30"))
        p.drawPolygon(QPolygonF([QPointF(cx - 10, cy - 70), QPointF(cx + 10, cy - 70), QPointF(cx, cy - 78)]))

    def _fountain(self, p, cx, cy, frame, rnd):
        p.setPen(QPen(QColor("#5A5A60"), 1))
        p.setBrush(QColor("#A8A49C"))
        p.drawEllipse(QPointF(cx, cy - 4), 30, 15)
        p.setBrush(QColor("#4A88D0"))
        p.drawEllipse(QPointF(cx, cy - 7), 25, 11)
        p.setBrush(QColor("#A8A49C"))
        p.drawRect(QRectF(cx - 4, cy - 30, 8, 24))
        p.drawEllipse(QPointF(cx, cy - 30), 12, 5)
        p.setPen(QPen(QColor(200, 230, 255, 220), 2))
        for i in range(5):
            off = (frame * 3 + i * 7) % 14
            p.drawArc(QRectF(cx - 14 + off * 0.2, cy - 40 + off * 0.4, 28, 26), 30 * 16, 120 * 16)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 120))
        for i in range(6):
            a = (frame + i) % 4
            p.drawEllipse(QPointF(cx - 18 + i * 7, cy - 8 + (a % 2)), 2, 1)

    def _fence(self, p, cx, cy, frame, rnd):
        wood, dark = QColor("#B08A5A"), QColor("#6A4626")
        p.setPen(QPen(dark, 1))
        p.setBrush(wood)
        for dx in (-16, 0, 16):
            y = cy - dx * 0.5 * 0 + (-dx * 0.0)
            p.drawRect(QRectF(cx + dx - 2, y - 22 + dx * 0.5, 4, 22))
        p.drawPolygon(QPolygonF([QPointF(cx - 18, cy - 24), QPointF(cx + 18, cy - 6), QPointF(cx + 18, cy - 10),
                                 QPointF(cx - 18, cy - 28)]))
        p.drawPolygon(QPolygonF([QPointF(cx - 18, cy - 12), QPointF(cx + 18, cy + 6), QPointF(cx + 18, cy + 2),
                                 QPointF(cx - 18, cy - 16)]))

    def _sign(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 8, 3)
        p.setPen(QPen(QColor("#4A3018"), 3))
        p.drawLine(QPointF(cx, cy), QPointF(cx, cy - 30))
        p.setPen(QPen(QColor("#4A3018"), 1))
        p.setBrush(QColor("#C89A5A"))
        p.drawRect(QRectF(cx - 15, cy - 42, 30, 16))
        p.setPen(QPen(QColor("#4A3018"), 1))
        for i in range(3):
            p.drawLine(QPointF(cx - 10, cy - 38 + i * 4), QPointF(cx + 10 - i * 4, cy - 38 + i * 4))

    def _portal(self, p, cx, cy, frame, rnd):
        p.setPen(Qt.NoPen)
        glow = QRadialGradient(QPointF(cx, cy - 2), 30)
        glow.setColorAt(0, QColor(190, 120, 255, 180))
        glow.setColorAt(1, QColor(190, 120, 255, 0))
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx, cy), 30, 15)
        p.setPen(QPen(QColor("#5A2A8A"), 2))
        p.setBrush(QColor(150, 90, 230, 120))
        p.drawEllipse(QPointF(cx, cy), 22, 11)
        p.setPen(QPen(QColor(230, 200, 255, 230), 1.5))
        for i in range(3):
            r = 4 + ((frame * 4 + i * 6) % 18)
            p.drawEllipse(QPointF(cx, cy), r, r / 2)
        for i in range(6):
            a = (frame * 3 + i * 11) % 30
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(240, 220, 255, 220 - a * 6))
            p.drawEllipse(QPointF(cx - 14 + i * 5.5, cy - a * 1.4), 1.6, 1.6)

    def _campfire(self, p, cx, cy, frame, rnd):
        glow = QRadialGradient(QPointF(cx, cy - 8), 50)
        glow.setColorAt(0, QColor(255, 170, 60, 110))
        glow.setColorAt(1, QColor(255, 170, 60, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx, cy - 8), 48, 30)
        p.setBrush(QColor("#6A6A70"))
        for i in range(8):
            from math import cos, radians, sin
            a = radians(i * 45)
            p.drawEllipse(QPointF(cx + cos(a) * 14, cy + sin(a) * 7), 4, 3)
        p.setPen(QPen(QColor("#3A2414"), 4, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(cx - 10, cy + 2), QPointF(cx + 10, cy - 4))
        p.drawLine(QPointF(cx - 10, cy - 4), QPointF(cx + 10, cy + 2))
        flick = [0, 3, 1, 4][frame % 4]
        for col, sc in (("#E0401A", 1.0), ("#F8A020", 0.7), ("#FFE070", 0.4)):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(col))
            hgt = (26 + flick) * sc
            p.drawPolygon(QPolygonF([QPointF(cx - 9 * sc, cy - 2), QPointF(cx - 4 * sc, cy - hgt * 0.7),
                                     QPointF(cx + (flick - 2) * sc, cy - hgt), QPointF(cx + 5 * sc, cy - hgt * 0.65),
                                     QPointF(cx + 9 * sc, cy - 2)]))

    def _log(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 20, 6)
        p.setPen(QPen(QColor("#3A2414"), 1))
        p.setBrush(QColor("#7A5230"))
        path = QPainterPath()
        path.moveTo(cx - 20, cy - 10)
        path.lineTo(cx + 14, cy + 6)
        path.lineTo(cx + 14, cy - 4)
        path.lineTo(cx - 20, cy - 20)
        path.closeSubpath()
        p.drawPath(path)
        p.setBrush(QColor("#C8A070"))
        p.drawEllipse(QPointF(cx + 14, cy + 1), 4, 5.5)
        p.setPen(QPen(QColor("#8A6A40"), 1))
        p.drawEllipse(QPointF(cx + 14, cy + 1), 2, 2.5)

    def _mushroom(self, p, cx, cy, frame, rnd):
        for dx, dy, s in ((-6, 2, 1.0), (7, -2, 0.7), (0, 6, 0.55)):
            x, y = cx + dx, cy + dy
            p.setPen(QPen(QColor("#8A7A60"), 1))
            p.setBrush(QColor("#F0E8D0"))
            p.drawRect(QRectF(x - 2 * s, y - 8 * s, 4 * s, 8 * s))
            p.setBrush(QColor("#D03A2A"))
            p.drawChord(QRectF(x - 8 * s, y - 14 * s, 16 * s, 12 * s), 0, 180 * 16)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#FFFFFF"))
            p.drawEllipse(QPointF(x - 3 * s, y - 11 * s), 1.4 * s, 1.2 * s)
            p.drawEllipse(QPointF(x + 3 * s, y - 10 * s), 1.2 * s, 1 * s)

    def _table(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 20, 8)
        p.setPen(QPen(QColor("#4A3018"), 2))
        for dx, dy in ((-12, -2), (12, -2), (0, 5), (0, -9)):
            p.drawLine(QPointF(cx + dx, cy + dy), QPointF(cx + dx, cy + dy - 14))
        self._box(p, cx, cy - 14, 20, 10, 3, "#A87A48", "#7A5230", "#6A4626")
        if rnd.random() < 0.7:
            p.setPen(QPen(QColor("#606060"), 1))
            p.setBrush(QColor("#F8F8F8"))
            p.drawEllipse(QPointF(cx - 4, cy - 19), 4, 2)
            p.setBrush(QColor("#7A4A2A"))
            p.drawRect(QRectF(cx + 4, cy - 24, 4, 5))

    def _chair(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 12, 5)
        p.setPen(QPen(QColor("#4A3018"), 2))
        for dx, dy in ((-7, 0), (7, 0), (0, 4)):
            p.drawLine(QPointF(cx + dx, cy + dy), QPointF(cx + dx, cy + dy - 9))
        self._box(p, cx, cy - 9, 10, 5, 2, "#A87A48", "#7A5230", "#6A4626")
        self._box(p, cx - 6, cy - 14, 3, 4, 14, "#A87A48", "#7A5230", "#6A4626")

    def _stool(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 9, 4)
        p.setPen(QPen(QColor("#4A3018"), 2))
        for dx in (-5, 5, 0):
            p.drawLine(QPointF(cx + dx, cy + (2 if dx == 0 else 0)), QPointF(cx + dx * 0.6, cy - 12))
        p.setPen(QPen(QColor("#4A3018"), 1))
        p.setBrush(QColor("#A02A2A"))
        p.drawEllipse(QPointF(cx, cy - 13), 8, 4)

    def _cushion(self, p, cx, cy, frame, rnd):
        p.setPen(QPen(QColor("#5A2050"), 1))
        p.setBrush(QColor(rnd.choice(["#A040A0", "#4060C0", "#C04040", "#40A080"])))
        p.drawEllipse(QPointF(cx, cy - 2), 14, 7)
        p.setBrush(QColor(255, 255, 255, 50))
        p.drawEllipse(QPointF(cx - 3, cy - 4), 6, 3)

    def _umbrella(self, p, cx, cy, frame, rnd):
        self._table(p, cx, cy, frame, rnd)
        p.setPen(QPen(QColor("#E0E0E0"), 2))
        p.drawLine(QPointF(cx, cy - 18), QPointF(cx, cy - 60))
        cols = rnd.choice([("#D03A2A", "#F8F0E0"), ("#2A6AC0", "#F8F0E0"), ("#2A9A5A", "#F8E040")])
        for i in range(8):
            from math import cos, radians, sin
            a1, a2 = radians(i * 45), radians(i * 45 + 45)
            p.setPen(QPen(QColor(0, 0, 0, 80), 1))
            p.setBrush(QColor(cols[i % 2]))
            p.drawPolygon(QPolygonF([QPointF(cx, cy - 66), QPointF(cx + cos(a1) * 30, cy - 52 + sin(a1) * 13),
                                     QPointF(cx + cos(a2) * 30, cy - 52 + sin(a2) * 13)]))

    def _bookshelf(self, p, cx, cy, frame, rnd):
        self._box(p, cx, cy, 24, 12, 56, "#6A4626", "#7A5230", "#5A3A1E")
        for row in range(4):
            y = cy - 10 - row * 12
            x = cx - 22
            while x < cx - 2:
                bw = rnd.uniform(2.5, 4.5)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(rnd.choice(["#A02A2A", "#2A4AA0", "#2A7A3A", "#C8A040", "#6A2A7A", "#E0D0B0"])))
                t = (x - (cx - 24)) / 24
                p.drawRect(QRectF(x, y - 9 + t * 12 - 2, bw, 9))
                x += bw + 0.5

    def _fireplace(self, p, cx, cy, frame, rnd):
        self._box(p, cx, cy, 26, 13, 60, "#7A746C", "#9A948A", "#8A847A")
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1A1410"))
        p.drawPolygon(QPolygonF([QPointF(cx - 18, cy - 4), QPointF(cx - 2, cy + 4), QPointF(cx - 2, cy - 22),
                                 QPointF(cx - 18, cy - 30)]))
        flick = [0, 2, 1, 3][frame % 4]
        for col, sc in (("#E0401A", 1.0), ("#F8A020", 0.65), ("#FFE070", 0.35)):
            p.setBrush(QColor(col))
            p.drawEllipse(QPointF(cx - 10, cy - 8 - flick * 0.5), 6 * sc, (11 + flick) * sc)
        glow = QRadialGradient(QPointF(cx - 10, cy), 40)
        glow.setColorAt(0, QColor(255, 160, 60, 90))
        glow.setColorAt(1, QColor(255, 160, 60, 0))
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx - 10, cy + 8), 40, 22)

    def _wall(self, p, cx, cy, frame, rnd):
        self._box(p, cx, cy, 32, 16, 64, "#A8A49C", "#8A847A", "#9A948A")
        p.setPen(QPen(QColor(0, 0, 0, 50), 1))
        for row in range(1, 8):
            y = cy - row * 8
            p.drawLine(QPointF(cx - 32, y), QPointF(cx, y + 16))
            p.drawLine(QPointF(cx, y + 16), QPointF(cx + 32, y))

    def _woodwall(self, p, cx, cy, frame, rnd):
        self._box(p, cx, cy, 32, 16, 64, "#8A5C32", "#9A6A3C", "#7A5230")
        p.setPen(QPen(QColor(0, 0, 0, 45), 1))
        for i in range(1, 6):
            x = cx - 32 + i * 6
            p.drawLine(QPointF(x, cy - 64 + i * 3), QPointF(x, cy + i * 3))
            x2 = cx + i * 6
            p.drawLine(QPointF(x2, cy + 16 - i * 3 - 64), QPointF(x2, cy + 16 - i * 3))

    def _barrel(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 12, 5)
        p.setPen(QPen(QColor("#3A2414"), 1))
        p.setBrush(QColor("#8A5C32"))
        p.drawRoundedRect(QRectF(cx - 10, cy - 26, 20, 28), 6, 4)
        p.setBrush(QColor("#A87A48"))
        p.drawEllipse(QPointF(cx, cy - 25), 10, 4)
        p.setPen(QPen(QColor("#404048"), 2))
        p.drawLine(QPointF(cx - 10, cy - 18), QPointF(cx + 10, cy - 18))
        p.drawLine(QPointF(cx - 10, cy - 6), QPointF(cx + 10, cy - 6))

    def _crate(self, p, cx, cy, frame, rnd):
        self._box(p, cx, cy, 14, 7, 18, "#C89A5A", "#A87A48", "#8A6238")

    def _counter(self, p, cx, cy, frame, rnd):
        self._box(p, cx, cy, 32, 16, 22, "#A87A48", "#7A5230", "#6A4626")

    def _lantern(self, p, cx, cy, frame, rnd):
        p.setPen(QPen(QColor("#2A2A30"), 2))
        p.drawLine(QPointF(cx, cy), QPointF(cx, cy - 40))
        a = 110 + (frame % 2) * 30
        glow = QRadialGradient(QPointF(cx, cy - 44), 18)
        glow.setColorAt(0, QColor(255, 200, 100, a))
        glow.setColorAt(1, QColor(255, 200, 100, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx, cy - 44), 18, 18)
        p.setPen(QPen(QColor("#2A2A30"), 1))
        p.setBrush(QColor("#FFD070"))
        p.drawRect(QRectF(cx - 4, cy - 50, 8, 10))

    def _plant(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 10, 4)
        p.setPen(QPen(QColor("#6A3A1E"), 1))
        p.setBrush(QColor("#B8603A"))
        p.drawPolygon(QPolygonF([QPointF(cx - 8, cy - 14), QPointF(cx + 8, cy - 14), QPointF(cx + 6, cy),
                                 QPointF(cx - 6, cy)]))
        for dx, dy in ((-6, -26), (6, -27), (0, -32), (-2, -22), (4, -21)):
            p.setPen(QPen(QColor("#1E5A2A"), 1))
            p.setBrush(QColor("#3A8A3A"))
            p.drawEllipse(QPointF(cx + dx, cy + dy), 6, 4)

    def _snowpine(self, p, cx, cy, frame, rnd):
        self._pine(p, cx, cy, frame, rnd)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 230))
        for y, hw in ((-14, 22), (-34, 18), (-52, 14), (-68, 9)):
            p.drawPolygon(QPolygonF([QPointF(cx - hw * 0.55, cy + y - 12), QPointF(cx + hw * 0.55, cy + y - 12),
                                     QPointF(cx, cy + y - 30)]))
            p.drawEllipse(QPointF(cx - hw * 0.6, cy + y - 2), 4, 2)
            p.drawEllipse(QPointF(cx + hw * 0.5, cy + y - 3), 4, 2)

    def _snowman(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 14, 5)
        p.setPen(QPen(QColor("#A0B0C8"), 1))
        p.setBrush(QColor("#FAFCFF"))
        for y, r in ((-10, 12), (-30, 9), (-45, 7)):
            p.drawEllipse(QPointF(cx, cy + y), r, r)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#202020"))
        p.drawEllipse(QPointF(cx - 2.5, cy - 47), 1.2, 1.2)
        p.drawEllipse(QPointF(cx + 2.5, cy - 47), 1.2, 1.2)
        for y in (-34, -29, -24):
            p.drawEllipse(QPointF(cx, cy + y), 1.2, 1.2)
        p.setBrush(QColor("#F08020"))
        p.drawPolygon(QPolygonF([QPointF(cx, cy - 45), QPointF(cx + 8, cy - 44), QPointF(cx, cy - 43)]))
        p.setBrush(QColor("#C03030"))
        p.drawRect(QRectF(cx - 8, cy - 40, 16, 3))
        p.drawRect(QRectF(cx + 3, cy - 40, 3, 9))
        p.setBrush(QColor("#202024"))
        p.drawRect(QRectF(cx - 6, cy - 60, 12, 9))
        p.drawRect(QRectF(cx - 9, cy - 52, 18, 2))
        p.setPen(QPen(QColor("#5A3A22"), 1.5))
        p.drawLine(QPointF(cx - 9, cy - 30), QPointF(cx - 18, cy - 38))
        p.drawLine(QPointF(cx + 9, cy - 30), QPointF(cx + 18, cy - 36))

    def _crystal(self, p, cx, cy, frame, rnd):
        glow = QRadialGradient(QPointF(cx, cy - 18), 30)
        a = 90 + [0, 30, 50, 30][frame % 4]
        hue = rnd.choice(["#80C8FF", "#C890FF", "#80FFD0"])
        g = QColor(hue)
        glow.setColorAt(0, QColor(g.red(), g.green(), g.blue(), a))
        glow.setColorAt(1, QColor(g.red(), g.green(), g.blue(), 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx, cy - 18), 30, 24)
        for dx, hgt, w in ((-8, 26, 6), (6, 34, 7), (0, 44, 8), (12, 20, 5), (-14, 16, 5)):
            p.setPen(QPen(_shade(hue, 0.5), 1))
            p.setBrush(_shade(hue, 0.85))
            p.drawPolygon(QPolygonF([QPointF(cx + dx - w, cy), QPointF(cx + dx - w * 0.7, cy - hgt * 0.8),
                                     QPointF(cx + dx, cy - hgt), QPointF(cx + dx + w * 0.7, cy - hgt * 0.8),
                                     QPointF(cx + dx + w, cy)]))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 120))
            p.drawPolygon(QPolygonF([QPointF(cx + dx - w * 0.5, cy - 2), QPointF(cx + dx - w * 0.4, cy - hgt * 0.75),
                                     QPointF(cx + dx, cy - hgt * 0.95), QPointF(cx + dx - w * 0.1, cy - 2)]))

    def _stalagmite(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 14, 5)
        for dx, hgt, w in ((-6, 30, 9), (7, 20, 7), (0, 42, 8)):
            p.setPen(QPen(QColor("#3A3028"), 1))
            p.setBrush(QColor("#7A6A5A"))
            p.drawPolygon(QPolygonF([QPointF(cx + dx - w, cy), QPointF(cx + dx, cy - hgt), QPointF(cx + dx + w, cy)]))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 35))
            p.drawPolygon(QPolygonF([QPointF(cx + dx - w * 0.6, cy - 2), QPointF(cx + dx, cy - hgt),
                                     QPointF(cx + dx - w * 0.1, cy - 2)]))

    def _column(self, p, cx, cy, frame, rnd, broken=False):
        self._shadow(p, cx, cy, 16, 6)
        height = rnd.choice((30, 40, 24)) if broken else 70
        self._box(p, cx, cy, 14, 7, 6, "#E8E4DC", "#C8C2B8", "#B8B2A8")
        g = QLinearGradient(cx - 9, 0, cx + 9, 0)
        g.setColorAt(0, QColor("#C8C2B8"))
        g.setColorAt(0.4, QColor("#F4F0EA"))
        g.setColorAt(1, QColor("#A8A298"))
        p.setPen(QPen(QColor("#8A847A"), 1))
        p.setBrush(QBrush(g))
        p.drawRect(QRectF(cx - 9, cy - 6 - height, 18, height))
        p.setPen(QPen(QColor(0, 0, 0, 40), 1))
        for dx in (-5, 0, 5):
            p.drawLine(QPointF(cx + dx, cy - 6), QPointF(cx + dx, cy - 6 - height))
        if broken:
            p.setPen(QPen(QColor("#8A847A"), 1))
            p.setBrush(QColor("#D8D2C8"))
            top = cy - 6 - height
            p.drawPolygon(QPolygonF([QPointF(cx - 9, top), QPointF(cx - 3, top - 6), QPointF(cx + 2, top - 1),
                                     QPointF(cx + 9, top - 5), QPointF(cx + 9, top + 2), QPointF(cx - 9, top + 2)]))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#4A8A3A"))
            for _ in range(5):
                p.drawEllipse(QPointF(cx + rnd.uniform(-9, 9), cy - rnd.uniform(6, height)), 2.5, 2)
        else:
            self._box(p, cx, cy - 6 - height, 14, 7, 6, "#F0ECE4", "#D0CAC0", "#C0BAB0")

    def _ruin(self, p, cx, cy, frame, rnd):
        self._column(p, cx, cy, frame, rnd, broken=True)

    def _statue(self, p, cx, cy, frame, rnd):
        self._box(p, cx, cy, 16, 8, 14, "#C8C2B8", "#A8A298", "#989288")
        stone = Look(rnd.choice(["canine", "feline", "dragon", "avian"]), "#B8B4AC", "#D0CCC4", "#8A867E")
        pm = QPixmap(FW * 2, FH * 2)
        pm.fill(Qt.transparent)
        q = QPainter(pm)
        q.setRenderHint(QPainter.Antialiasing)
        q.scale(2, 2)
        draw_furre(q, stone, "sit")
        q.end()
        pm.setDevicePixelRatio(2)
        p.drawPixmap(QPointF(cx - FW / 2 * 1.2, cy - 14 - FOOT * 1.2), pm.scaled(int(FW * 2.4), int(FH * 2.4)))

    def _telescope(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 14, 5)
        p.setPen(QPen(QColor("#3A2A18"), 2))
        for dx, dy in ((-10, 4), (10, 4), (0, -6)):
            p.drawLine(QPointF(cx, cy - 26), QPointF(cx + dx, cy + dy))
        p.setPen(QPen(QColor("#5A4210"), 1))
        g = QLinearGradient(0, cy - 50, 0, cy - 30)
        g.setColorAt(0, QColor("#E8C860"))
        g.setColorAt(1, QColor("#A07820"))
        p.setBrush(QBrush(g))
        tube = QPolygonF([QPointF(cx - 14, cy - 22), QPointF(cx + 16, cy - 46), QPointF(cx + 20, cy - 40),
                          QPointF(cx - 10, cy - 16)])
        p.drawPolygon(tube)
        p.setBrush(QColor("#2A2A40"))
        p.drawEllipse(QPointF(cx + 18, cy - 43), 3, 4)

    def _cactus(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 10, 4)
        p.setPen(QPen(QColor("#2A5A2A"), 1))
        p.setBrush(QColor("#4A8A3A"))
        p.drawRoundedRect(QRectF(cx - 6, cy - 48, 12, 48), 6, 6)
        p.drawRoundedRect(QRectF(cx - 18, cy - 34, 8, 18), 4, 4)
        p.drawRect(QRectF(cx - 14, cy - 20, 10, 6))
        p.drawRoundedRect(QRectF(cx + 9, cy - 40, 8, 20), 4, 4)
        p.drawRect(QRectF(cx + 4, cy - 26, 9, 6))
        p.setPen(QPen(QColor(255, 255, 255, 90), 1))
        for y in range(-44, -4, 7):
            p.drawPoint(QPointF(cx - 3, cy + y))
            p.drawPoint(QPointF(cx + 3, cy + y + 3))
        if rnd.random() < 0.5:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#F070A0"))
            p.drawEllipse(QPointF(cx, cy - 49), 3, 2.5)

    def _tent(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 30, 12)
        col = rnd.choice(["#C8A060", "#B05040", "#E0D0B0"])
        p.setPen(QPen(_shade(col, 0.5), 1))
        p.setBrush(_shade(col, 0.8))
        p.drawPolygon(QPolygonF([QPointF(cx - 30, cy), QPointF(cx, cy + 14), QPointF(cx, cy - 40)]))
        p.setBrush(QColor(col))
        p.drawPolygon(QPolygonF([QPointF(cx, cy + 14), QPointF(cx + 30, cy), QPointF(cx, cy - 40)]))
        p.setBrush(QColor("#2A1A10"))
        p.drawPolygon(QPolygonF([QPointF(cx + 4, cy + 12), QPointF(cx + 16, cy + 6), QPointF(cx + 6, cy - 16)]))
        p.setPen(QPen(QColor("#5A3A22"), 2))
        p.drawLine(QPointF(cx, cy - 40), QPointF(cx, cy - 48))

    def _hay(self, p, cx, cy, frame, rnd):
        self._box(p, cx, cy, 16, 8, 14, "#E8C860", "#C8A040", "#B89030")
        p.setPen(QPen(QColor("#8A6A20"), 1))
        for i in range(1, 4):
            p.drawLine(QPointF(cx - 16, cy - i * 3.5), QPointF(cx, cy + 8 - i * 3.5))

    def _scarecrow(self, p, cx, cy, frame, rnd):
        self._shadow(p, cx, cy, 10, 4)
        p.setPen(QPen(QColor("#5A3A22"), 3))
        p.drawLine(QPointF(cx, cy), QPointF(cx, cy - 56))
        p.drawLine(QPointF(cx - 18, cy - 40), QPointF(cx + 18, cy - 40))
        p.setPen(QPen(QColor("#4A3018"), 1))
        p.setBrush(QColor("#4A70B8"))
        p.drawRect(QRectF(cx - 10, cy - 44, 20, 22))
        p.setBrush(QColor("#E8D090"))
        p.drawEllipse(QPointF(cx, cy - 52), 7, 7)
        p.setBrush(QColor("#8A5A22"))
        p.drawPolygon(QPolygonF([QPointF(cx - 12, cy - 56), QPointF(cx + 12, cy - 56), QPointF(cx, cy - 68)]))
        p.setPen(QPen(QColor("#E8C860"), 1))
        for dx in (-18, -15, 15, 18):
            p.drawLine(QPointF(cx + dx, cy - 40), QPointF(cx + dx * 1.1, cy - 34))

    def _sunflower(self, p, cx, cy, frame, rnd):
        for dx, h in ((-8, 40), (6, 48), (0, 34)):
            p.setPen(QPen(QColor("#3A7A2A"), 2))
            p.drawLine(QPointF(cx + dx, cy), QPointF(cx + dx, cy - h))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#4A9A3A"))
            p.drawEllipse(QPointF(cx + dx + 4, cy - h * 0.5), 4, 2)
            p.setBrush(QColor("#F0C020"))
            for i in range(10):
                from math import cos, radians, sin
                a = radians(i * 36)
                p.drawEllipse(QPointF(cx + dx + cos(a) * 5, cy - h + sin(a) * 5), 3, 2)
            p.setBrush(QColor("#5A3A12"))
            p.drawEllipse(QPointF(cx + dx, cy - h), 3.5, 3.5)

    def _lilypad(self, p, cx, cy, frame, rnd):
        p.setPen(QPen(QColor("#1E5A22"), 1))
        p.setBrush(QColor("#3A9A3A"))
        p.drawPie(QRectF(cx - 18, cy - 9, 36, 18), 20 * 16, 320 * 16)
        p.drawPie(QRectF(cx - 10, cy - 1, 18, 9), 200 * 16, 300 * 16)
        if rnd.random() < 0.5:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#F8C0D8"))
            for i in range(6):
                from math import cos, radians, sin
                a = radians(i * 60)
                p.drawEllipse(QPointF(cx + 4 + cos(a) * 3, cy - 4 + sin(a) * 1.6), 2.5, 1.5)
            p.setBrush(QColor("#F8E040"))
            p.drawEllipse(QPointF(cx + 4, cy - 4), 1.4, 1)

    def _reeds(self, p, cx, cy, frame, rnd):
        for i in range(9):
            x = cx + rnd.uniform(-14, 14)
            h = rnd.uniform(18, 36)
            p.setPen(QPen(QColor("#5A8A3A"), 1.5))
            p.drawLine(QPointF(x, cy + rnd.uniform(-4, 4)), QPointF(x + rnd.uniform(-3, 3), cy - h))
            if i % 3 == 0:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#6A4626"))
                p.drawRoundedRect(QRectF(x - 2, cy - h - 2, 4, 10), 2, 2)

    def _coral(self, p, cx, cy, frame, rnd):
        col = rnd.choice(["#F07890", "#F0A040", "#C060E0", "#F05050"])
        p.setPen(QPen(_shade(col, 0.6), 4, Qt.SolidLine, Qt.RoundCap))
        for dx, dy, tx, ty in ((0, 0, -4, -24), (-4, -14, -14, -28), (-2, -18, 4, -34), (2, -8, 14, -22),
                               (12, -18, 16, -30)):
            p.drawLine(QPointF(cx + dx, cy + dy), QPointF(cx + tx, cy + ty))
        p.setPen(QPen(QColor(col), 2.5, Qt.SolidLine, Qt.RoundCap))
        for dx, dy, tx, ty in ((0, 0, -4, -24), (-4, -14, -14, -28), (-2, -18, 4, -34), (2, -8, 14, -22),
                               (12, -18, 16, -30)):
            p.drawLine(QPointF(cx + dx, cy + dy), QPointF(cx + tx, cy + ty))

    def _kelp(self, p, cx, cy, frame, rnd):
        sway = [0, 2, 3, 2][frame % 4]
        for dx in (-6, 3, 9):
            path = QPainterPath(QPointF(cx + dx, cy))
            path.cubicTo(QPointF(cx + dx - 6 + sway, cy - 20), QPointF(cx + dx + 6 + sway, cy - 40),
                         QPointF(cx + dx + sway * 2, cy - 60))
            p.setPen(QPen(QColor("#2E6A3A"), 4, Qt.SolidLine, Qt.RoundCap))
            p.drawPath(path)
            p.setPen(QPen(QColor("#4A9A4A"), 2, Qt.SolidLine, Qt.RoundCap))
            p.drawPath(path)

    def _stall(self, p, cx, cy, frame, rnd):
        self._box(p, cx, cy, 26, 13, 20, "#A87A48", "#7A5230", "#6A4626")
        p.setPen(QPen(QColor("#4A3018"), 2))
        for dx, dy in ((-24, -1), (24, -1), (0, 12), (0, -12)):
            p.drawLine(QPointF(cx + dx, cy + dy - 20), QPointF(cx + dx, cy + dy - 46))
        cols = rnd.choice([("#C03030", "#F8F0E0"), ("#3050B0", "#F8F0E0"), ("#2A8A4A", "#F8E040")])
        for i in range(6):
            t0, t1 = i / 6, (i + 1) / 6
            a = QPointF(cx - 28 + 28 * t0, cy - 46 + 14 * t0)
            b = QPointF(cx - 28 + 28 * t1, cy - 46 + 14 * t1)
            c = QPointF(b.x() + 28, b.y() - 14 - 0)
            d = QPointF(a.x() + 28, a.y() - 14)
            p.setPen(QPen(QColor(0, 0, 0, 70), 1))
            p.setBrush(QColor(cols[i % 2]))
            p.drawPolygon(QPolygonF([a, b, c, d]))
        for i in range(4):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(rnd.choice(["#F04040", "#F0A030", "#F0E060", "#80C040", "#A060E0"])))
            p.drawEllipse(QPointF(cx - 14 + i * 9, cy - 22 + i * 2), 3.5, 3)
        p.setBrush(QColor("#FFD070"))
        p.drawEllipse(QPointF(cx - 26, cy - 44), 3, 3)

    def _torch(self, p, cx, cy, frame, rnd):
        p.setPen(QPen(QColor("#4A3018"), 3))
        p.drawLine(QPointF(cx, cy), QPointF(cx, cy - 36))
        p.setPen(QPen(QColor("#2A2A30"), 1))
        p.setBrush(QColor("#3A3A40"))
        p.drawRect(QRectF(cx - 4, cy - 42, 8, 6))
        flick = [0, 3, 1, 4][frame % 4]
        for col, sc in (("#E0401A", 1.0), ("#F8A020", 0.65), ("#FFE070", 0.35)):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(col))
            p.drawEllipse(QPointF(cx + (flick - 2) * 0.3, cy - 48 - flick * 0.5), 5 * sc, (10 + flick) * sc)

    def _chest(self, p, cx, cy, frame, rnd):
        self._box(p, cx, cy, 14, 7, 14, "#A8702E", "#8A5A22", "#7A4A1A")
        p.setPen(QPen(QColor("#E8C040"), 1.5))
        p.drawLine(QPointF(cx - 14, cy - 8), QPointF(cx, cy - 1))
        p.drawLine(QPointF(cx, cy - 1), QPointF(cx + 14, cy - 8))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#F8D040"))
        p.drawRect(QRectF(cx - 2, cy - 5, 4, 4))

    def _shell(self, p, cx, cy, frame, rnd):
        p.setPen(QPen(QColor("#B08070"), 1))
        p.setBrush(QColor("#F8D8C8"))
        p.drawChord(QRectF(cx - 6, cy - 6, 12, 10), 0, 180 * 16)
        p.drawLine(QPointF(cx, cy - 6), QPointF(cx, cy - 1))


# ---- furres ---------------------------------------------------------------------------------------------------

KEYS = {"fur": (255, 0, 255), "markings": (0, 255, 255), "eyes": (255, 255, 0), "clothes": (0, 255, 0)}


def _recolour(img, look):
    """Swap the key colours in a supplied sprite for this furre's colours (keeping shading)."""
    img = img.convertToFormat(QImage.Format_ARGB32)
    targets = {k: QColor(getattr(look, k) or look.fur) for k in KEYS}
    for y in range(img.height()):
        for x in range(img.width()):
            c = img.pixelColor(x, y)
            if c.alpha() == 0:
                continue
            rgb = (c.red(), c.green(), c.blue())
            m = max(rgb)
            if m < 40:
                continue
            for k, key in KEYS.items():
                # a key colour (or a darker shade of it): the key's channels equal, the others near zero
                if all(abs(v - m) < 24 if on else v < 24 for v, on in zip(rgb, key)):
                    t = QColor(targets[k])
                    f = m / 255
                    img.setPixelColor(x, y, QColor(int(t.red() * f), int(t.green() * f), int(t.blue() * f), c.alpha()))
                    break
    return img


class Furres:
    """Furre sprites: (kind, colours, pose, facing) -> a 48 x 64 pixmap with the feet at (24, 58)."""

    def __init__(self):
        self.cache = {}

    def get(self, look, pose="stand", facing=SE):
        key = (look.key(), pose, facing)
        if key not in self.cache:
            self.cache[key] = self._make(look, pose, facing)
            if len(self.cache) > 600:
                self.cache.pop(next(iter(self.cache)))
        return self.cache[key]

    def _make(self, look, pose, facing):
        f = ART / "furres" / look.kind / f"{pose}_{facing}.png"
        if f.exists():
            img = QImage(str(f))
            if not img.isNull():
                return QPixmap.fromImage(_recolour(img, look))
        pm = QPixmap(FW * 2, FH * 2)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.scale(2, 2)
        if facing in (SW, NW):                 # the left-facing views are mirror images
            p.translate(FW, 0)
            p.scale(-1, 1)
        draw_furre(p, look, pose, back=facing in (NE, NW))
        p.end()
        pm.setDevicePixelRatio(2)
        return pm


def draw_furre(p, look, pose="stand", back=False):
    """Paint a furre facing screen-right (down-right, or up-right when back=True) on a 48 x 64 canvas."""
    fur, mark = QColor(look.fur), QColor(look.markings or look.fur)
    line = QPen(_shade(look.fur, 0.45), 1.0)
    dark = _shade(look.fur, 0.78)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 70))
    if pose == "lie":
        p.drawEllipse(QPointF(24, FOOT), 20, 5)
    else:
        p.drawEllipse(QPointF(24, FOOT), 12, 4.5)

    if pose == "lie":
        _tail(p, look, QPointF(10, 52), line, lying=True)
        p.setPen(line)
        p.setBrush(fur)
        p.drawEllipse(QPointF(22, 51), 13, 7)
        if not back:
            p.setBrush(mark)
            p.drawEllipse(QPointF(24, 54), 8, 3.5)
        if look.clothes:
            p.setBrush(QColor(look.clothes))
            p.drawChord(QRectF(12, 44, 20, 14), 0, 180 * 16)
        p.setBrush(dark)
        p.drawEllipse(QPointF(31, 56), 4, 2.5)
        p.drawEllipse(QPointF(13, 56), 4, 2.5)
        _head(p, look, QPointF(36, 44), 0.85, line, back)
        return

    sit = pose == "sit"
    by = 8 if sit else 0                     # sitting lowers the body
    head_c = QPointF(25, 21 + by)
    if back:
        if look.wings:
            _wings(p, look, QPointF(24, 36 + by), line, front=True)
    else:
        _tail(p, look, QPointF(14, 46 + by * 0.6), line)
        if look.wings:
            _wings(p, look, QPointF(22, 36 + by), line, front=False)

    p.setPen(line)
    if sit:
        p.setBrush(dark)
        p.drawEllipse(QPointF(20, 53), 7, 4.5)
        p.setBrush(fur)
        p.drawEllipse(QPointF(28, 52), 8, 5)
        p.setBrush(dark)
        p.drawEllipse(QPointF(34, 56), 3.5, 2)
    else:
        p.setBrush(dark)
        p.drawRoundedRect(QRectF(17, 46, 6, 12), 3, 3)
        p.setBrush(fur)
        p.drawRoundedRect(QRectF(25, 46, 6, 12), 3, 3)
        p.setBrush(dark)
        p.drawEllipse(QPointF(20.5, 57.5), 4, 2)
        p.drawEllipse(QPointF(28.5, 57.5), 4, 2)
    # body
    p.setBrush(fur)
    p.drawEllipse(QPointF(24, 39 + by), 9, 10.5)
    if not back:
        p.setBrush(mark)
        p.drawEllipse(QPointF(26, 41 + by), 5, 7)
    if look.clothes:
        p.setBrush(QColor(look.clothes))
        p.setPen(QPen(_shade(look.clothes, 0.5), 1))
        shirt = QPainterPath()
        shirt.moveTo(15.5, 36 + by)
        shirt.cubicTo(16, 29 + by, 32, 29 + by, 32.5, 36 + by)
        shirt.lineTo(32, 44 + by)
        shirt.cubicTo(28, 46 + by, 20, 46 + by, 16, 44 + by)
        shirt.closeSubpath()
        p.drawPath(shirt)
        p.setPen(line)
    # arms
    p.setBrush(dark if back else fur)
    p.drawEllipse(QPointF(16, 39 + by), 3, 6)
    p.setBrush(fur)
    p.drawEllipse(QPointF(32, 39 + by), 3, 6)
    if look.clothes:
        p.setBrush(QColor(look.clothes))
        p.drawEllipse(QPointF(16, 36 + by), 3, 3)
        p.drawEllipse(QPointF(32, 36 + by), 3, 3)
    _head(p, look, head_c, 1.0, line, back)
    if back:
        _tail(p, look, QPointF(18, 46 + by * 0.6), line, front=True)


def _wings(p, look, at, line, front):
    k = look.kind
    if k == "insect":
        p.setPen(QPen(QColor(80, 80, 100, 160), 1))
        p.setBrush(QColor(200, 230, 255, 110))
        for dx, dy, rx, ry in ((-10, -6, 9, 13), (-8, 6, 7, 9)):
            p.drawEllipse(QPointF(at.x() + dx, at.y() + dy), rx, ry)
        return
    col = QColor(look.fur if k == "avian" else look.markings or look.fur)
    p.setPen(QPen(_shade(col.name(), 0.5), 1))
    p.setBrush(col if k != "dragon" else _shade(look.markings or look.fur, 0.9))
    x, y = at.x(), at.y()
    if k == "dragon":
        path = QPainterPath(QPointF(x, y - 4))
        path.lineTo(x - 18, y - 20)
        path.lineTo(x - 14, y - 6)
        path.lineTo(x - 20, y - 2)
        path.lineTo(x - 12, y + 2)
        path.lineTo(x - 16, y + 8)
        path.closeSubpath()
    else:
        path = QPainterPath(QPointF(x, y - 6))
        path.cubicTo(QPointF(x - 20, y - 18), QPointF(x - 24, y + 4), QPointF(x - 10, y + 12))
        path.cubicTo(QPointF(x - 12, y + 4), QPointF(x - 6, y), QPointF(x, y + 2))
        path.closeSubpath()
    p.drawPath(path)


def _tail(p, look, at, line, front=False, lying=False):
    k = look.kind
    fur, mark = QColor(look.fur), QColor(look.markings or look.fur)
    x, y = at.x(), at.y()
    p.setPen(line)
    if k in ("canine",):
        path = QPainterPath(QPointF(x + 4, y))
        path.cubicTo(QPointF(x - 10, y - 2), QPointF(x - 12, y - 16), QPointF(x - 4, y - 20))
        path.cubicTo(QPointF(x - 2, y - 12), QPointF(x + 2, y - 6), QPointF(x + 6, y - 4))
        path.closeSubpath()
        p.setBrush(fur)
        p.drawPath(path)
        p.setBrush(mark)
        p.drawEllipse(QPointF(x - 5, y - 18), 3, 3)
    elif k in ("feline", "rodent", "other"):
        path = QPainterPath(QPointF(x + 4, y))
        path.cubicTo(QPointF(x - 12, y + 2), QPointF(x - 10, y - 18), QPointF(x - 4, y - 22))
        pen = QPen(_shade(look.fur, 0.45), 4.5, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
        p.setPen(QPen(fur if k != "rodent" else QColor("#E8B0A8"), 3, Qt.SolidLine, Qt.RoundCap))
        p.drawPath(path)
    elif k in ("lapine", "ursine"):
        p.setBrush(mark if k == "lapine" else fur)
        p.drawEllipse(QPointF(x + 2, y - 4), 4, 4)
    elif k == "mustelid":
        path = QPainterPath(QPointF(x + 4, y))
        path.cubicTo(QPointF(x - 12, y), QPointF(x - 14, y - 10), QPointF(x - 10, y - 14))
        path.cubicTo(QPointF(x - 6, y - 8), QPointF(x, y - 4), QPointF(x + 5, y - 4))
        path.closeSubpath()
        p.setBrush(_shade(look.fur, 0.85))
        p.drawPath(path)
    elif k in ("dragon", "reptile"):
        path = QPainterPath(QPointF(x + 6, y - 4))
        path.cubicTo(QPointF(x - 6, y - 2), QPointF(x - 14, y + 6), QPointF(x - 20, y + 2))
        path.cubicTo(QPointF(x - 12, y + 2), QPointF(x - 4, y - 4), QPointF(x + 6, y + 2))
        path.closeSubpath()
        p.setBrush(fur)
        p.drawPath(path)
    elif k == "avian":
        p.setBrush(_shade(look.fur, 0.85))
        p.drawPolygon(QPolygonF([QPointF(x + 4, y - 2), QPointF(x - 10, y + 2), QPointF(x - 12, y - 4),
                                 QPointF(x - 10, y - 9), QPointF(x + 4, y - 6)]))
    elif k in ("equine", "bovine", "cervine"):
        if k == "equine":
            path = QPainterPath(QPointF(x + 4, y - 4))
            path.cubicTo(QPointF(x - 8, y - 4), QPointF(x - 10, y + 6), QPointF(x - 6, y + 10))
            p.setPen(QPen(QColor(look.markings or look.fur).darker(130), 4, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)
        else:
            p.setBrush(mark if k == "cervine" else fur)
            p.drawEllipse(QPointF(x + 2, y - 5), 3, 4)
    elif k == "aquatic":
        p.setBrush(_shade(look.fur, 0.85))
        p.drawPolygon(QPolygonF([QPointF(x + 4, y - 4), QPointF(x - 8, y - 12), QPointF(x - 6, y - 4),
                                 QPointF(x - 9, y + 4)]))


def _head(p, look, c, s, line, back):
    k = look.kind
    fur, mark = QColor(look.fur), QColor(look.markings or look.fur)
    x, y = c.x(), c.y()

    def P(dx, dy):
        return QPointF(x + dx * s, y + dy * s)

    def ear_pointed(bx, tip_dx, tip_dy, w=5.0):
        p.setPen(line)
        p.setBrush(fur)
        p.drawPolygon(QPolygonF([P(bx - w, -6), P(bx + tip_dx, tip_dy), P(bx + w, -8)]))
        if not back:
            p.setPen(Qt.NoPen)
            p.setBrush(mark if k != "feline" else QColor("#F0B0B8"))
            p.drawPolygon(QPolygonF([P(bx - w * 0.5, -7), P(bx + tip_dx * 0.8, tip_dy * 0.8), P(bx + w * 0.5, -8)]))

    # ears and horns (behind the head)
    if k in ("canine", "feline", "mustelid") or k == "other" and False:
        tall = 13 if k == "canine" else 10 if k == "feline" else 6
        ear_pointed(-6, -2, -6 - tall)
        ear_pointed(5, 2, -6 - tall)
    elif k == "lapine":
        for bx, lean in ((-4, -3), (4, 2)):
            p.setPen(line)
            p.setBrush(fur)
            p.drawEllipse(P(bx + lean * 0.5, -18), 3.2 * s, 10 * s)
            if not back:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#F0B0B8"))
                p.drawEllipse(P(bx + lean * 0.5, -18), 1.6 * s, 7 * s)
    elif k in ("rodent", "ursine"):
        for bx in (-7, 7):
            p.setPen(line)
            p.setBrush(fur)
            p.drawEllipse(P(bx, -8), 4.5 * s, 4.5 * s)
            if not back:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#F0B0B8") if k == "rodent" else mark)
                p.drawEllipse(P(bx, -8), 2.5 * s, 2.5 * s)
    elif k == "bovine":
        p.setPen(QPen(QColor("#8A7A60"), 1))
        p.setBrush(QColor("#E8DCC0"))
        for side in (-1, 1):
            horn = QPainterPath(P(side * 5, -7))
            horn.cubicTo(P(side * 14, -8), P(side * 16, -14), P(side * 12, -18))
            horn.cubicTo(P(side * 12, -13), P(side * 9, -10), P(side * 6, -10))
            horn.closeSubpath()
            p.drawPath(horn)
        ear_pointed(-9, -4, -8, 3)
        ear_pointed(8, 4, -8, 3)
    elif k == "cervine":
        p.setPen(QPen(QColor("#7A5A3A"), 1.6 * s, Qt.SolidLine, Qt.RoundCap))
        for side in (-1, 1):
            p.drawLine(P(side * 4, -8), P(side * 8, -22))
            p.drawLine(P(side * 6, -15), P(side * 12, -18))
            p.drawLine(P(side * 7, -19), P(side * 4, -25))
        ear_pointed(-8, -5, -10, 3)
        ear_pointed(7, 5, -10, 3)
    elif k == "equine":
        ear_pointed(-5, -1, -16, 3)
        ear_pointed(5, 1, -16, 3)
    elif k == "dragon":
        p.setPen(QPen(QColor("#5A4A30"), 1))
        p.setBrush(QColor("#E0D4B0"))
        for side in (-1, 1):
            p.drawPolygon(QPolygonF([P(side * 3, -8), P(side * 9 - 4, -20), P(side * 7, -7)]))
    elif k == "insect":
        p.setPen(QPen(_shade(look.fur, 0.4), 1))
        for side in (-1, 1):
            p.drawLine(P(side * 3, -9), P(side * 8, -20))
            p.setBrush(_shade(look.fur, 0.6))
            p.drawEllipse(P(side * 8, -20), 1.5 * s, 1.5 * s)
    elif k == "aquatic":
        p.setPen(line)
        p.setBrush(_shade(look.fur, 0.85))
        p.drawPolygon(QPolygonF([P(-6, -8), P(-2, -18), P(6, -9)]))

    # the head
    p.setPen(line)
    p.setBrush(fur)
    p.drawEllipse(c, 10 * s, 9.5 * s)
    if k == "avian":
        p.setBrush(mark)
        p.drawPolygon(QPolygonF([P(-3, -9), P(-6, -17), P(0, -10), P(2, -18), P(4, -9)]))
    if k == "equine":
        p.setPen(QPen(QColor(look.markings or look.fur).darker(130), 3, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(P(-2, -9), P(-8, 4))
        p.setPen(line)
    if back:
        return
    # face: muzzle, nose, eyes, cheeks
    if k == "canine":
        p.setBrush(mark)
        p.drawEllipse(P(7, 3), 6 * s, 4.2 * s)
        p.setBrush(QColor("#202020"))
        p.drawEllipse(P(12, 1.5), 1.8 * s, 1.4 * s)
    elif k in ("feline", "lapine", "rodent", "mustelid", "ursine", "other"):
        p.setBrush(mark)
        p.drawEllipse(P(4, 4), 4.5 * s, 3.2 * s)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#E08090") if k != "ursine" else QColor("#202020"))
        p.drawEllipse(P(5.5, 2.5), 1.6 * s, 1.1 * s)
        if k in ("feline", "rodent"):
            p.setPen(QPen(QColor(40, 40, 40, 120), 0.6))
            for dy in (-0.5, 1.5):
                p.drawLine(P(8, 3 + dy), P(13, 2 + dy * 1.6))
    elif k == "avian":
        p.setPen(QPen(QColor("#8A5A10"), 1))
        p.setBrush(QColor("#F0B030"))
        p.drawPolygon(QPolygonF([P(6, 0), P(15, 4), P(6, 6)]))
    elif k in ("dragon", "reptile"):
        p.setBrush(fur)
        p.drawEllipse(P(7, 3), 7 * s, 4.5 * s)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        p.drawEllipse(P(12, 1.5), 0.9 * s, 0.7 * s)
        p.setPen(QPen(_shade(look.fur, 0.45), 0.8))
        p.drawLine(P(4, 6), P(12, 5))
    elif k in ("equine", "bovine", "cervine"):
        p.setBrush(mark)
        p.drawEllipse(P(6, 5), 5.5 * s, 4.8 * s)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 160))
        p.drawEllipse(P(8, 5), 0.9 * s, 1.2 * s)
        p.drawEllipse(P(10.5, 4.5), 0.9 * s, 1.2 * s)
    elif k == "insect":
        p.setPen(QPen(_shade(look.fur, 0.4), 0.8))
        p.drawLine(P(5, 5), P(8, 7))
    elif k == "aquatic":
        p.setPen(QPen(_shade(look.fur, 0.4), 0.8))
        p.drawArc(QRectF(x + 2 * s, y + 2 * s, 8 * s, 4 * s), 200 * 16, 140 * 16)
    # eyes
    for ex, er in ((0, 2.4), (6.5, 2.0)) if k not in ("insect", "aquatic") else ((0, 3.0), (6.5, 2.6)):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(P(ex, -1.5), er * s, (er + 0.6) * s)
        p.setBrush(QColor(look.eyes))
        p.drawEllipse(P(ex + 0.6, -1.2), (er - 0.7) * s, er * s)
        p.setBrush(QColor("#101010"))
        p.drawEllipse(P(ex + 0.8, -1.0), 0.8 * s, 1.1 * s)
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(P(ex + 0.1, -2.2), 0.55 * s, 0.55 * s)


# ---- the program icon and the splash -------------------------------------------------------------------------

def icon_pixmap(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    grad = QLinearGradient(0, 0, 0, size)
    grad.setColorAt(0, QColor("#8A5AD8"))
    grad.setColorAt(1, QColor("#3A1A78"))
    p.setPen(QPen(QColor("#20104A"), max(1.0, s)))
    p.setBrush(QBrush(grad))
    p.drawEllipse(QRectF(1 * s, 1 * s, 30 * s, 30 * s))
    p.scale(s * 0.62, s * 0.62)
    p.translate(2, -14)
    _head(p, Look("canine", "#E07A30", "#F8F0E0", "#3AA040"), QPointF(24, 38), 1.25,
          QPen(QColor("#5A2A10"), 1.0), False)
    p.end()
    return pm


def icon():
    ic = QIcon()
    for sz in (16, 32, 48):
        ic.addPixmap(icon_pixmap(sz))
    return ic


_splash = {}


def sidebar_pixmap():
    """assets/furcadia/sidebar.jpg (or .png), the side panel picture; None if there isn't one."""
    return _override(ART / "sidebar.png") or _override(ART / "sidebar.jpg")


def splash_pixmap(w, h):
    """assets/furcadia/splash.png (or .jpg), fitted into w x h; None if there isn't one."""
    if "src" not in _splash:
        _splash["src"] = _override(ART / "splash.png") or _override(ART / "splash.jpg")
    src = _splash["src"]
    if src is None or w < 2 or h < 2:
        return None
    if _splash.get("size") != (w, h):
        _splash["size"] = (w, h)
        _splash["scaled"] = src.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return _splash["scaled"]
