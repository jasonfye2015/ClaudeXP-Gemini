"""Claude Aquarium: a living fish tank - in a window, full screen, or as a little desktop pet above the taskbar.

Eight kinds of fish grow from fry to adults to elders; they get hungry (feed them: pellets sink and they chase
them), their water gets dirty (clean it), and now and then one falls sick (Ich, Fin Rot or Swim Bladder trouble,
each with its own medicine). Two healthy adults of a kind sometimes breed, and the fry can carry a mutation (Albino,
Golden, Neon, Giant, Dwarf, Calico, Melanistic) that changes their colour or size. Fish can be put into stasis -
held, frozen, out of the tank - and brought back. Pausing stops all of it: the fish just swim, as a display.

Time only passes while the tank is open (nobody starves while you're away). The tank saves itself, and there are
three save slots to keep tanks in (save over them as often as you like, load them, delete them)."""
import json
import math
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QColor, QFont, QIcon, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
                           QPolygonF, QRadialGradient)
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QMenu, QProgressBar, QPushButton, QToolButton, QVBoxLayout, QWidget)
from shiboken6 import isValid

from claudecore import host

TITLE = "Claude Aquarium"
FPS = 30
CAPACITY = 16
FRY_TIME, ADULT_TIME, ELDER_TIME = 10 * 60, 25 * 60, 4 * 3600           # seconds of tank time
HUNGER_TIME = 3 * 3600                                                  # full to starving
NAMES = ("Bubbles", "Finn", "Nemo", "Goldie", "Splash", "Coral", "Pebble", "Ziggy", "Marlin", "Dory", "Gill",
         "Sunny", "Shadow", "Pip", "Wiggles", "Captain", "Mango", "Kiwi", "Blue", "Jewel", "Sprite", "Tango",
         "Pickles", "Biscuit", "Comet", "Luna", "Nova", "Ripple", "Squirt", "Fizz", "Peaches", "Domino", "Ember",
         "Opal", "Puddles", "Rocket", "Sushi", "Taffy", "Zephyr", "Echo")
# kind -> colours, shape and adult length (as a share of the tank's width)
SPECIES = {
    "Goldfish": {"body": "#F28C28", "fin": "#F9B46B", "shape": "round", "size": 0.085, "tail": "fan", "speed": 0.8},
    "Neon Tetra": {"body": "#203E8F", "fin": "#9DB4E8", "shape": "slim", "size": 0.045, "tail": "fork", "speed": 1.2,
                   "stripe": "#2EE6F2", "rear": "#E3264E"},
    "Angelfish": {"body": "#DCDCDC", "fin": "#EDEDED", "shape": "tall", "size": 0.09, "tail": "fork", "speed": 0.6,
                  "bands": "#2B2B2B"},
    "Clownfish": {"body": "#FF7A00", "fin": "#FF9A3C", "shape": "round", "size": 0.065, "tail": "fan", "speed": 0.9,
                  "bands": "#FFFFFF", "edge": "#1A1A1A"},
    "Betta": {"body": "#6D28D9", "fin": "#A855F7", "shape": "slim", "size": 0.075, "tail": "veil", "speed": 0.7},
    "Guppy": {"body": "#A7AFBA", "fin": "#F43F5E", "shape": "slim", "size": 0.05, "tail": "veil", "speed": 1.1,
              "spots": "#FDE047"},
    "Pufferfish": {"body": "#D6B36A", "fin": "#E9D19A", "shape": "ball", "size": 0.075, "tail": "fan", "speed": 0.5,
                   "spots": "#5C4A1E"},
    "Discus": {"body": "#E85D04", "fin": "#F48C3C", "shape": "disc", "size": 0.09, "tail": "fan", "speed": 0.6,
               "lines": "#2563EB"},
}
MUTATIONS = {"Albino": "pale, pink-eyed", "Golden": "gold all over", "Neon": "glowing colours",
             "Giant": "much bigger", "Dwarf": "much smaller", "Calico": "patched colours",
             "Melanistic": "almost black"}
ILLNESSES = {"Ich": "white spots", "Fin Rot": "ragged fins", "Swim Bladder": "swims lopsided"}
MEDICINES = {"Ich Treatment": "Ich", "Antibiotics": "Fin Rot", "Cooked Pea": "Swim Bladder"}
BACKGROUNDS = {"Ocean Blue": ("#1F6FB2", "#0B2E59"), "Freshwater": ("#3E8E7E", "#103B33"),
               "Coral Reef": ("#2BA3C9", "#0E4E7A"), "Night Glow": ("#141A3A", "#03040F"),
               "Sunset Lagoon": ("#F29E6D", "#5A2E6E"), "Deep Sea": ("#0A2342", "#000308")}
SANDS = {"Golden sand": "#D9B779", "White sand": "#ECE6D6", "Black gravel": "#3A3A3A", "Rainbow gravel": "rainbow",
         "Pink coral sand": "#E7A6A1"}
DECOR = ("Castle", "Treasure chest", "Rocks", "Sunken ship")


def _mix(a, b, t):
    a, b = QColor(a), QColor(b)
    return QColor(int(a.red() + (b.red() - a.red()) * t), int(a.green() + (b.green() - a.green()) * t),
                  int(a.blue() + (b.blue() - a.blue()) * t))


# ---- a fish -------------------------------------------------------------------------------------------------------
def new_fish(kind, rng=random, generation=1, parents=None, genes=None):
    genes = genes or {"hue": rng.uniform(-8, 8), "size": rng.uniform(0.92, 1.08), "mutation": None}
    return {"id": f"{int(time.time() * 1000) % 10 ** 9}{rng.randint(100, 999)}", "kind": kind,
            "name": rng.choice(NAMES), "age": 0.0, "hunger": 20.0, "health": 100.0, "happiness": 80.0,
            "sick": None, "sick_for": 0.0, "genes": genes, "generation": generation, "parents": parents or [],
            "x": rng.uniform(0.15, 0.85), "y": rng.uniform(0.2, 0.7), "vx": 0.0, "vy": 0.0,
            "tx": rng.uniform(0.1, 0.9), "ty": rng.uniform(0.15, 0.75), "facing": 1, "dead": False, "dead_for": 0.0,
            "born": time.time()}


def stage(f):
    if f["age"] < FRY_TIME:
        return "Fry"
    if f["age"] < ADULT_TIME:
        return "Juvenile"
    if f["age"] < ELDER_TIME:
        return "Adult"
    return "Elder"


def growth(f):
    """How grown a fish is (0.35 a new fry, 1.0 an adult, a little more as an elder)."""
    a = f["age"]
    if a < ADULT_TIME:
        return 0.35 + 0.65 * a / ADULT_TIME
    return min(1.12, 1.0 + 0.12 * (a - ADULT_TIME) / ELDER_TIME)


def length(f):
    """Length as a share of the tank's width."""
    g = f["genes"]
    m = {"Giant": 1.4, "Dwarf": 0.68}.get(g.get("mutation"), 1.0)
    return SPECIES[f["kind"]]["size"] * growth(f) * g["size"] * m


def colours(f):
    """(body, fin) for this fish, with its hue drift and mutation."""
    sp = SPECIES[f["kind"]]
    g = f["genes"]
    out = []
    for key in ("body", "fin"):
        c = QColor(sp[key])
        h, s, v, _a = c.getHsv()
        h = int((max(h, 0) + g["hue"]) % 360)
        mut = g.get("mutation")
        if mut == "Albino":
            s, v = int(s * 0.18), min(255, int(v * 1.15) + 30)
        elif mut == "Golden":
            h, s, v = 45, max(s, 200), max(v, 220)
        elif mut == "Neon":
            s, v = 255, 255
        elif mut == "Melanistic":
            v = int(v * 0.32)
        out.append(QColor.fromHsv(h, max(0, min(255, s)), max(0, min(255, v))))
    if f["sick"]:                                       # (a sick fish looks washed out)
        out = [_mix(c, "#9AA3A8", 0.35) for c in out]
    return out


def draw_fish(p, f, cx, cy, size, t):
    """A fish of `size` pixels long at (cx, cy), facing its way; tail and fins wave with time t."""
    sp = SPECIES[f["kind"]]
    body, fin = colours(f)
    shape = sp["shape"]
    L = size
    H = {"round": 0.55, "slim": 0.32, "tall": 0.5, "ball": 0.8, "disc": 0.85}[shape] * L
    p.save()
    p.translate(cx, cy)
    if f["facing"] < 0:
        p.scale(-1, 1)
    if f["dead"]:
        p.rotate(180)
    elif f["sick"] == "Swim Bladder":
        p.rotate(-25)
    wave = math.sin(t * (6 + sp["speed"] * 4) + hash(f["id"]) % 7) * 0.15
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(body.darker(160), max(0.6, L / 60)))
    # tail
    tail = QPainterPath()
    tx = -L * 0.45
    ragged = f["sick"] == "Fin Rot"
    if sp["tail"] == "veil":
        tail.moveTo(tx + L * 0.05, 0)
        tail.cubicTo(tx - L * 0.3, -H * (1.1 + wave), tx - L * 0.55, -H * 0.2, tx - L * 0.5, H * (0.2 + wave))
        tail.cubicTo(tx - L * 0.55, H * 0.9, tx - L * 0.2, H * (1.0 - wave), tx + L * 0.05, 0)
    elif sp["tail"] == "fork":
        tail.moveTo(tx + L * 0.05, 0)
        tail.lineTo(tx - L * 0.25, -H * (0.55 + wave))
        tail.lineTo(tx - L * 0.12, 0)
        tail.lineTo(tx - L * 0.25, H * (0.55 - wave))
        tail.closeSubpath()
    else:
        tail.moveTo(tx + L * 0.05, 0)
        tail.cubicTo(tx - L * 0.2, -H * (0.7 + wave), tx - L * 0.32, -H * 0.4, tx - L * 0.28, 0)
        tail.cubicTo(tx - L * 0.32, H * 0.4, tx - L * 0.2, H * (0.7 - wave), tx + L * 0.05, 0)
    fin_col = QColor(fin)
    fin_col.setAlpha(150 if ragged else 220)
    p.setBrush(fin_col)
    p.drawPath(tail)
    # dorsal and belly fins
    fins = QPainterPath()
    up = 1.25 if shape in ("tall", "disc") else 0.75
    fins.moveTo(-L * 0.15, -H * 0.42)
    fins.quadTo(L * 0.0, -H * (up + wave * 0.5), L * 0.18, -H * 0.4)
    fins.moveTo(-L * 0.12, H * 0.42)
    fins.quadTo(L * 0.02, H * (up * (0.95 if shape == "tall" else 0.6)), L * 0.12, H * 0.4)
    p.drawPath(fins)
    # body
    grad = QLinearGradient(0, -H / 2, 0, H / 2)
    grad.setColorAt(0, body.lighter(125))
    grad.setColorAt(0.6, body)
    grad.setColorAt(1, body.darker(125))
    p.setBrush(grad)
    p.drawEllipse(QRectF(-L * 0.45, -H / 2, L * 0.9, H))
    p.setPen(Qt.NoPen)
    clip = QPainterPath()
    clip.addEllipse(QRectF(-L * 0.45, -H / 2, L * 0.9, H))
    p.setClipPath(clip)
    mut = f["genes"].get("mutation")
    if "stripe" in sp and mut != "Albino":                # neon tetra: the glowing line and red rear
        p.setBrush(QColor(sp["rear"]))
        p.drawRect(QRectF(-L * 0.45, 0, L * 0.45, H / 2))
        p.setBrush(QColor(sp["stripe"]))
        p.drawRect(QRectF(-L * 0.45, -H * 0.14, L * 0.9, H * 0.16))
    if "bands" in sp:                                   # clownfish / angelfish bands
        for bx in ((-0.2, 0.15) if shape == "round" else (-0.25, -0.02, 0.2)):
            if "edge" in sp:
                p.setBrush(QColor(sp["edge"]))
                p.drawRect(QRectF(L * bx - L * 0.055, -H, L * 0.11, H * 2))
            p.setBrush(QColor(sp["bands"]))
            p.drawRect(QRectF(L * bx - L * 0.04, -H, L * 0.08, H * 2))
    if "lines" in sp:                                   # discus waves
        p.setPen(QPen(QColor(sp["lines"]), max(0.6, L / 45)))
        p.setBrush(Qt.NoBrush)
        for k in range(-3, 4):
            path = QPainterPath()
            path.moveTo(-L * 0.45, H * k / 8)
            for i in range(1, 9):
                path.lineTo(-L * 0.45 + L * 0.9 * i / 8, H * k / 8 + math.sin(i + k) * H * 0.04)
            p.drawPath(path)
        p.setPen(Qt.NoPen)
    if "spots" in sp or mut == "Calico":                # guppy / puffer spots, calico patches
        rng = random.Random(f["id"])
        col = QColor(sp.get("spots", "#FFFFFF"))
        for _ in range(9 if mut != "Calico" else 6):
            if mut == "Calico":
                col = QColor(rng.choice(["#FFFFFF", "#1A1A1A", "#F28C28"]))
            p.setBrush(col)
            r = L * (0.03 if mut != "Calico" else 0.09)
            p.drawEllipse(QPointF(rng.uniform(-0.35, 0.3) * L, rng.uniform(-0.35, 0.35) * H), r, r)
    if f["sick"] == "Ich":                              # white spots
        rng = random.Random(f["id"] + "ich")
        p.setBrush(QColor(255, 255, 255, 230))
        for _ in range(12):
            p.drawEllipse(QPointF(rng.uniform(-0.4, 0.4) * L, rng.uniform(-0.4, 0.4) * H), L * 0.018, L * 0.018)
    p.setClipping(False)
    # eye
    ex, ey = L * 0.27, -H * 0.12
    p.setBrush(QColor("#FFFFFF"))
    p.drawEllipse(QPointF(ex, ey), L * 0.065, L * 0.065)
    p.setBrush(QColor("#C8323C") if mut == "Albino" else QColor("#111111"))
    if f["dead"]:
        p.setPen(QPen(QColor("#111111"), max(0.8, L / 40)))
        d = L * 0.04
        p.drawLine(QPointF(ex - d, ey - d), QPointF(ex + d, ey + d))
        p.drawLine(QPointF(ex - d, ey + d), QPointF(ex + d, ey - d))
    else:
        p.drawEllipse(QPointF(ex + L * 0.01, ey), L * 0.035, L * 0.035)
    if mut == "Neon":                                   # a glow
        p.setPen(Qt.NoPen)
        glow = QRadialGradient(0, 0, L * 0.7)
        c = QColor(body)
        c.setAlpha(70)
        glow.setColorAt(0, c)
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(glow)
        p.drawEllipse(QPointF(0, 0), L * 0.7, L * 0.7)
    p.restore()


def fish_pixmap(f, size=40):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    copy = dict(f, facing=1, dead=False)
    draw_fish(p, copy, size / 2, size / 2, size * 0.8, 0.0)
    p.end()
    return pm


def aquarium_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 4, 0, 30)
    g.setColorAt(0, QColor("#5BB6F0"))
    g.setColorAt(1, QColor("#0E4E8A"))
    p.setPen(QPen(QColor("#2B2B2B"), 1.2))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(1.5, 5.5, 29, 23), 3, 3)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#D9B779"))
    p.drawRect(QRectF(2.2, 25, 27.6, 3))
    draw_fish(p, dict(new_fish("Goldfish", random.Random(1)), age=ADULT_TIME, facing=1), 16, 16, 18, 0.3)
    p.end()
    return QIcon(pm)


# ---- the tank -------------------------------------------------------------------------------------------------------
def new_tank():
    rng = random.Random()
    fish = [new_fish(k, rng) for k in ("Goldfish", "Goldfish", "Neon Tetra", "Neon Tetra", "Clownfish")]
    for f in fish:
        f["age"] = ADULT_TIME + rng.uniform(0, 600)        # (a starter tank of grown fish)
    return {"fish": fish, "stasis": [], "pellets": [], "water": 100.0, "paused": False, "tank_time": 0.0,
            "background": "Ocean Blue", "sand": "Golden sand", "plants": True, "bubbles": True,
            "decor": ["Castle"], "picture": "", "log": ["Your tank is ready. Say hello to your fish!"],
            "next_breed": 120.0}


class Tank:
    """The simulation: fish swimming (always), and hunger, health, growth, sickness, water and breeding (when not
    paused). Views draw it at any size: positions are shares of the tank (0..1)."""

    def __init__(self, data=None):
        self.d = new_tank()
        if data:
            self.d.update(data)
        self.t = 0.0
        self.listeners = []
        self.bubbles = [[random.random(), random.random(), random.uniform(0.5, 1.5)] for _ in range(14)]

    # ---- talking to views ----
    def note(self, text):
        self.d["log"].append(text)
        del self.d["log"][:-40]
        for cb in list(self.listeners):
            try:
                cb(text)
            except RuntimeError:
                self.listeners.remove(cb)

    def fish(self, fid):
        return next((f for f in self.d["fish"] if f["id"] == fid), None)

    # ---- care ----
    def feed(self, count=None):
        """Some pellets: enough for everyone (a pellet and a half each) unless a count is given."""
        if count is None:
            count = max(4, int(len(self.alive()) * 1.5))
        for _ in range(count):
            self.d["pellets"].append({"x": random.uniform(0.15, 0.85), "y": 0.02, "age": 0.0})

    def clean(self):
        self.d["water"] = 100.0
        self.d["pellets"] = [pl for pl in self.d["pellets"] if pl["y"] < 0.8]
        self.note("You cleaned the tank. The water sparkles.")

    def medicate(self, fid, medicine):
        f = self.fish(fid)
        if f is None or f["dead"]:
            return
        cures = MEDICINES.get(medicine)
        if not f["sick"]:
            self.note(f"{f['name']} isn't sick - the {medicine.lower()} does nothing.")
        elif f["sick"] == cures:
            f["sick"], f["sick_for"] = None, 0.0
            f["health"] = min(100.0, f["health"] + 15)
            self.note(f"{f['name']} is cured of {cures}!")
        else:
            self.note(f"The {medicine.lower()} doesn't help {f['name']}'s {f['sick']}.")

    def add(self, kind):
        if len(self.alive()) >= CAPACITY:
            return None
        f = new_fish(kind)
        self.d["fish"].append(f)
        self.note(f"A new {kind.lower()}, {f['name']}, joins the tank.")
        return f

    def alive(self):
        return [f for f in self.d["fish"] if not f["dead"]]

    def to_stasis(self, fid):
        f = self.fish(fid)
        if f is not None and not f["dead"]:
            self.d["fish"].remove(f)
            self.d["stasis"].append(f)
            self.note(f"{f['name']} goes into stasis, held safe until you need them.")

    def from_stasis(self, fid):
        f = next((x for x in self.d["stasis"] if x["id"] == fid), None)
        if f is None or len(self.alive()) >= CAPACITY:
            return False
        self.d["stasis"].remove(f)
        f["x"], f["y"] = random.uniform(0.2, 0.8), random.uniform(0.2, 0.6)
        self.d["fish"].append(f)
        self.note(f"{f['name']} is back in the tank.")
        return True

    def release(self, fid, from_stasis=False):
        pool = self.d["stasis"] if from_stasis else self.d["fish"]
        f = next((x for x in pool if x["id"] == fid), None)
        if f is not None:
            pool.remove(f)
            self.note(f"{f['name']} was given to a good home.")

    # ---- time ----
    def step(self, dt):
        self.t += dt
        d = self.d
        live = not d["paused"]
        if live:
            d["tank_time"] += dt
        for b in self.bubbles:
            b[1] -= dt * 0.08 * b[2]
            if b[1] < 0:
                b[0], b[1] = random.random(), 1.0
        for pl in list(d["pellets"]):                   # pellets sink, and rot if nobody eats them
            pl["age"] += dt
            pl["y"] = min(0.86, pl["y"] + dt * 0.06)
            if live and pl["age"] > 60:
                d["pellets"].remove(pl)
                d["water"] = max(0.0, d["water"] - 2.5)
        for f in list(d["fish"]):
            self._swim(f, dt)
            if live:
                self._live(f, dt)
        if live:
            d["water"] = max(0.0, d["water"] - dt * 0.0005 * len(self.alive()))
            d["next_breed"] -= dt
            if d["next_breed"] <= 0:
                d["next_breed"] = random.uniform(600, 1200)
                self._breed()

    def _swim(self, f, dt):
        sp = SPECIES[f["kind"]]
        if f["dead"]:                                   # float up, then gone
            f["dead_for"] += dt
            f["y"] = max(0.04, f["y"] - dt * 0.03)
            if f["dead_for"] > 12:
                self.d["fish"].remove(f)
            return
        speed = 0.06 * sp["speed"] * (0.5 if f["sick"] else 1.0) * (1.3 if stage(f) == "Fry" else 1.0)
        target = None
        if f["hunger"] > 25 and self.d["pellets"]:      # chase the nearest pellet
            pl = min(self.d["pellets"], key=lambda q: (q["x"] - f["x"]) ** 2 + (q["y"] - f["y"]) ** 2)
            target = (pl["x"], pl["y"])
            speed *= 1.6
            if abs(pl["x"] - f["x"]) < 0.03 and abs(pl["y"] - f["y"]) < 0.04:
                self.d["pellets"].remove(pl)
                f["hunger"] = max(0.0, f["hunger"] - 30)
                target = None
        if target is None:
            if abs(f["tx"] - f["x"]) < 0.03 and abs(f["ty"] - f["y"]) < 0.03 or random.random() < dt * 0.05:
                f["tx"], f["ty"] = random.uniform(0.06, 0.94), random.uniform(0.1, 0.8)
            target = (f["tx"], f["ty"])
        dx, dy = target[0] - f["x"], target[1] - f["y"]
        dist = math.hypot(dx, dy) or 1.0
        ax, ay = dx / dist * speed, dy / dist * speed * 0.6
        f["vx"] += (ax - f["vx"]) * min(1.0, dt * 2)
        f["vy"] += (ay - f["vy"]) * min(1.0, dt * 2)
        f["x"] = min(0.96, max(0.04, f["x"] + f["vx"] * dt))
        f["y"] = min(0.82, max(0.08, f["y"] + f["vy"] * dt))
        if abs(f["vx"]) > 0.004:
            f["facing"] = 1 if f["vx"] > 0 else -1

    def _live(self, f, dt):
        if f["dead"]:
            return
        d = self.d
        f["age"] += dt
        f["hunger"] = min(100.0, f["hunger"] + dt * 100 / HUNGER_TIME * (1.4 if stage(f) == "Fry" else 1.0))
        heal = 0.03
        if f["hunger"] > 90:
            heal -= 0.08
        if f["sick"]:                                   # (untreated, about two hours to the end)
            f["sick_for"] += dt
            heal -= 0.045
        if d["water"] < 40:
            heal -= 0.015
        if stage(f) == "Elder":
            heal -= 0.004
        f["health"] = max(0.0, min(100.0, f["health"] + heal * dt))
        crowd = max(0, len(self.alive()) - 12) * 5
        f["happiness"] = max(0.0, min(100.0, 100 - f["hunger"] * 0.5 - (100 - f["health"]) * 0.4 -
                                      (100 - d["water"]) * 0.3 - crowd))
        if not f["sick"]:
            chance = dt / (8 * 3600) * (3 if d["water"] < 50 else 1) * (2 if f["hunger"] > 70 else 1)
            if random.random() < chance:
                f["sick"] = random.choice(list(ILLNESSES))
                self.note(f"{f['name']} looks unwell: {ILLNESSES[f['sick']]}. It's {f['sick']}.")
        lifespan = 7 * 3600 * f["genes"]["size"]
        if f["health"] <= 0 or f["age"] > lifespan:
            f["dead"] = True
            why = "of old age, peacefully" if f["age"] > lifespan else \
                ("of " + f["sick"]) if f["sick"] else "- they weren't looked after"
            self.note(f"{f['name']} the {f['kind'].lower()} has died {why}.")

    def _breed(self):
        if len(self.alive()) >= CAPACITY:
            return
        ready = {}
        for f in self.alive():
            if stage(f) in ("Adult", "Elder") and f["health"] > 60 and f["hunger"] < 60 and not f["sick"]:
                ready.setdefault(f["kind"], []).append(f)
        pairs = [k for k, v in ready.items() if len(v) >= 2]
        if not pairs or random.random() > 0.55:
            return
        kind = random.choice(pairs)
        a, b = random.sample(ready[kind], 2)
        ga, gb = a["genes"], b["genes"]
        genes = {"hue": (ga["hue"] + gb["hue"]) / 2 + random.gauss(0, 8),
                 "size": (ga["size"] + gb["size"]) / 2 * random.gauss(1.0, 0.05), "mutation": None}
        inherited = [m for m in (ga.get("mutation"), gb.get("mutation")) if m]
        if inherited and random.random() < 0.45:
            genes["mutation"] = random.choice(inherited)
        elif random.random() < 0.15:
            genes["mutation"] = random.choice(list(MUTATIONS))
        child = new_fish(kind, generation=max(a["generation"], b["generation"]) + 1,
                         parents=[a["name"], b["name"]], genes=genes)
        child["x"], child["y"] = (a["x"] + b["x"]) / 2, (a["y"] + b["y"]) / 2
        self.d["fish"].append(child)
        extra = f" It's a {genes['mutation'].lower()} mutation: {MUTATIONS[genes['mutation']]}!" \
            if genes["mutation"] else ""
        self.note(f"{a['name']} and {b['name']} had a baby {kind.lower()}: {child['name']}.{extra}")


# ---- drawing the tank ---------------------------------------------------------------------------------------------
_picture_cache = {}


def draw_tank(p, tank, w, h, selected=None, small=False):
    d = tank.d
    top, bottom = BACKGROUNDS.get(d["background"], BACKGROUNDS["Ocean Blue"])
    pic = None
    if d.get("picture"):
        if d["picture"] not in _picture_cache:
            _picture_cache[d["picture"]] = QImage(d["picture"])
        pic = _picture_cache[d["picture"]]
    if pic is not None and not pic.isNull():
        p.drawImage(QRectF(0, 0, w, h), pic, QRectF(pic.rect()))
        p.fillRect(QRectF(0, 0, w, h), QColor(20, 70, 140, 70))       # (seen through water)
    else:
        g = QLinearGradient(0, 0, 0, h)
        g.setColorAt(0, QColor(top))
        g.setColorAt(1, QColor(bottom))
        p.fillRect(QRectF(0, 0, w, h), g)
        if not small:                                   # light from above
            p.setPen(Qt.NoPen)
            for i in range(5):
                x = (i * 0.23 + 0.07 + math.sin(tank.t * 0.2 + i) * 0.02) * w
                ray = QPolygonF([QPointF(x, 0), QPointF(x + w * 0.05, 0), QPointF(x + w * 0.14, h),
                                 QPointF(x + w * 0.06, h)])
                p.setBrush(QColor(255, 255, 255, 14))
                p.drawPolygon(ray)
    # water quality: murky when dirty
    murk = (100 - d["water"]) / 100
    if murk > 0.2:
        p.fillRect(QRectF(0, 0, w, h), QColor(90, 110, 40, int(110 * (murk - 0.2))))
    p.setRenderHint(QPainter.Antialiasing)
    sand_top = h * 0.88
    sand = SANDS.get(d["sand"], "#D9B779")
    if sand == "rainbow":
        rng = random.Random(3)
        p.fillRect(QRectF(0, sand_top, w, h - sand_top), QColor("#C9B48A"))
        p.setPen(Qt.NoPen)
        for _ in range(int(w / 2)):
            p.setBrush(QColor.fromHsv(rng.randint(0, 359), 200, 230))
            p.drawEllipse(QPointF(rng.uniform(0, w), rng.uniform(sand_top + 2, h)), max(1, w / 260), max(1, w / 260))
    else:
        g = QLinearGradient(0, sand_top, 0, h)
        g.setColorAt(0, QColor(sand).lighter(110))
        g.setColorAt(1, QColor(sand).darker(130))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        path = QPainterPath(QPointF(0, h))
        for i in range(0, 41):
            path.lineTo(w * i / 40, sand_top + math.sin(i * 0.9) * h * 0.012)
        path.lineTo(w, h)
        p.drawPath(path)
    for name in d.get("decor", []):
        _draw_decor(p, name, w, h, sand_top)
    if d["plants"]:
        rng = random.Random(7)
        for i in range(7):
            x = rng.uniform(0.03, 0.97) * w
            hh = rng.uniform(0.18, 0.42) * h
            col = QColor.fromHsv(rng.randint(95, 140), 170, rng.randint(120, 190))
            p.setPen(QPen(col, max(1.5, w / 160), Qt.SolidLine, Qt.RoundCap))
            for k in range(3):
                path = QPainterPath(QPointF(x + k * w * 0.008, sand_top + 4))
                for j in range(1, 9):
                    yy = sand_top - hh * j / 8
                    sway = math.sin(tank.t * 0.8 + j * 0.6 + i + k) * w * 0.006 * j / 4
                    path.lineTo(x + k * w * 0.008 + sway, yy)
                p.drawPath(path)
    if d["bubbles"]:
        p.setPen(QPen(QColor(255, 255, 255, 150), 1))
        p.setBrush(QColor(255, 255, 255, 40))
        for bx, by, s in tank.bubbles:
            r = max(1.0, w * 0.004 * s)
            p.drawEllipse(QPointF((0.08 + bx * 0.84) * w + math.sin(tank.t * 2 + bx * 9) * 3, by * h * 0.9), r, r)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#7A4A1E"))
    for pl in d["pellets"]:
        p.drawEllipse(QPointF(pl["x"] * w, pl["y"] * h), max(1.2, w * 0.005), max(1.2, w * 0.005))
    for f in sorted(d["fish"], key=lambda f: length(f)):
        L = max(6.0, length(f) * w)
        draw_fish(p, f, f["x"] * w, f["y"] * h, L, tank.t)
        if f["id"] == selected:
            p.setPen(QPen(QColor(255, 255, 255, 200), 1.2, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(f["x"] * w, f["y"] * h), L * 0.65, L * 0.5)
            p.setPen(Qt.NoPen)
        if f["sick"] and not small:                     # a little red cross over a sick fish
            p.setBrush(QColor("#E53935"))
            cx, cy = f["x"] * w, f["y"] * h - L * 0.55
            s = max(2.0, L * 0.08)
            p.drawRect(QRectF(cx - s / 2, cy - s * 1.5, s, s * 3))
            p.drawRect(QRectF(cx - s * 1.5, cy - s / 2, s * 3, s))
    if d["paused"] and not small:
        p.setPen(QColor(255, 255, 255, 170))
        f = QFont("Tahoma")
        f.setPixelSize(max(10, int(h / 26)))
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(0, 6, w - 10, h * 0.06), Qt.AlignRight | Qt.AlignTop, "❚❚ PAUSED - display mode")
    # the glass
    p.setPen(Qt.NoPen)
    shine = QLinearGradient(0, 0, w, 0)
    shine.setColorAt(0, QColor(255, 255, 255, 30))
    shine.setColorAt(0.15, QColor(255, 255, 255, 0))
    p.setBrush(shine)
    p.drawRect(QRectF(0, 0, w, h))


def _draw_decor(p, name, w, h, sand_top):
    p.save()
    if name == "Castle":
        x, cw, ch = w * 0.68, w * 0.14, h * 0.24
        p.setPen(QPen(QColor("#5E5A55"), 1))
        p.setBrush(QColor("#9C968C"))
        p.drawRect(QRectF(x, sand_top - ch, cw, ch + 4))
        for i in range(4):
            p.drawRect(QRectF(x + i * cw / 3.5, sand_top - ch - h * 0.03, cw / 7, h * 0.03))
        p.drawRect(QRectF(x + cw * 0.35, sand_top - ch * 1.45, cw * 0.3, ch * 0.5))
        p.setBrush(QColor("#2A2724"))
        door = QPainterPath()
        door.addRoundedRect(QRectF(x + cw * 0.38, sand_top - ch * 0.45, cw * 0.24, ch * 0.45 + 4), cw * 0.1, cw * 0.1)
        p.drawPath(door)
    elif name == "Treasure chest":
        x, cw, ch = w * 0.2, w * 0.1, h * 0.08
        p.setPen(QPen(QColor("#3B2412"), 1))
        p.setBrush(QColor("#7B4A22"))
        p.drawRect(QRectF(x, sand_top - ch, cw, ch + 3))
        p.setBrush(QColor("#E3B23C"))
        p.drawRect(QRectF(x + cw * 0.44, sand_top - ch * 0.7, cw * 0.12, ch * 0.3))
        lid = QPainterPath()
        lid.moveTo(x, sand_top - ch)
        lid.quadTo(x + cw / 2, sand_top - ch * 1.8, x + cw, sand_top - ch)
        p.setBrush(QColor("#8C5628"))
        p.drawPath(lid)
    elif name == "Rocks":
        rng = random.Random(11)
        p.setPen(Qt.NoPen)
        for _ in range(5):
            r = rng.uniform(0.025, 0.05) * w
            p.setBrush(QColor.fromHsv(30, 15, rng.randint(90, 150)))
            p.drawEllipse(QPointF(rng.uniform(0.35, 0.6) * w, sand_top + 2), r, r * 0.7)
    elif name == "Sunken ship":
        x, sw, sh = w * 0.4, w * 0.22, h * 0.1
        p.setPen(QPen(QColor("#2B1B0E"), 1))
        p.setBrush(QColor("#5B3A1E"))
        hull = QPolygonF([QPointF(x, sand_top - sh), QPointF(x + sw, sand_top - sh * 1.3), QPointF(x + sw * 0.9,
                          sand_top + 3), QPointF(x + sw * 0.1, sand_top + 3)])
        p.drawPolygon(hull)
        p.drawLine(QPointF(x + sw * 0.5, sand_top - sh * 1.1), QPointF(x + sw * 0.62, sand_top - sh * 3.2))
    p.restore()


class TankView(QWidget):
    """The tank, drawn at this widget's size. Click a fish to pick it; (in feeding mode) click to drop food."""

    def __init__(self, app, small=False):
        super().__init__()
        self.app = app
        self.small = small
        self.setMouseTracking(not small)

    def paintEvent(self, event):
        p = QPainter(self)
        draw_tank(p, self.app.tank, self.width(), self.height(), None if self.small else self.app.selected,
                  self.small)

    def mousePressEvent(self, event):
        if self.small:
            return
        pos = event.position()
        x, y = pos.x() / max(1, self.width()), pos.y() / max(1, self.height())
        hit = min((f for f in self.app.tank.d["fish"] if not f["dead"]),
                  key=lambda f: (f["x"] - x) ** 2 + ((f["y"] - y) * 0.6) ** 2, default=None)
        if hit is not None and abs(hit["x"] - x) < length(hit) * 0.8 and abs(hit["y"] - y) < length(hit) * 0.9:
            self.app.select(hit["id"])
        elif event.button() == Qt.RightButton:
            self.app.tank.feed(3)


# ---- the program --------------------------------------------------------------------------------------------------
STYLE = """
QWidget#aquarium { background: #0E2238; }
QWidget#side { background: #102A44; }
QLabel { color: #E3F1FF; font-family: Tahoma; font-size: 11px; }
QLabel#title { font-size: 14px; font-weight: bold; color: #FFFFFF; }
QToolButton, QPushButton { background: #1D4E7A; color: #FFFFFF; border: 1px solid #3F7DB3; border-radius: 3px;
                           padding: 4px 8px; font-family: Tahoma; font-size: 11px; }
QToolButton:hover, QPushButton:hover { background: #2A6AA3; }
QToolButton:checked { background: #C2701E; border-color: #F0A050; }
QPushButton:disabled { color: #7F98AE; background: #17334E; }
QListWidget { background: #0B1D30; color: #E3F1FF; border: 1px solid #2D5F8C; font-family: Tahoma; font-size: 11px; }
QListWidget::item:selected { background: #2A6AA3; }
QProgressBar { border: 1px solid #2D5F8C; background: #0B1D30; height: 10px; text-align: center; color: white;
               font-size: 9px; }
QProgressBar::chunk { background: #3FB37F; }
QComboBox, QCheckBox { color: #E3F1FF; font-family: Tahoma; font-size: 11px; }
QComboBox { background: #0B1D30; border: 1px solid #2D5F8C; padding: 2px 4px; }
"""


class Aquarium(QWidget):
    """The windowed tank: toolbar, tank, and the fish panel. It also owns the full-screen and pet views."""

    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.selected = None
        self.full = None
        self.pet = None
        self.setObjectName("aquarium")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        self.tank = Tank(self._load(self._current()))
        self.tank.listeners.append(self._noted)
        col = QVBoxLayout(self)
        col.setContentsMargins(6, 6, 6, 6)
        col.setSpacing(6)
        col.addLayout(self._toolbar())
        row = QHBoxLayout()
        self.view = TankView(self)
        self.view.setMinimumSize(360, 240)
        row.addWidget(self.view, 1)
        row.addWidget(self._side())
        col.addLayout(row, 1)
        self.status = QLabel()
        col.addWidget(self.status)
        self.timer = QTimer(self, interval=int(1000 / FPS), timeout=self._tick)
        self.timer.start()
        self.autosave = QTimer(self, interval=20000, timeout=self.save_current)
        self.autosave.start()
        self.last = time.monotonic()
        self._refresh_list()

    # ---- building ----
    def _toolbar(self):
        bar = QHBoxLayout()
        bar.setSpacing(4)

        def tool(text, slot, tip=""):
            b = QToolButton()
            b.setText(text)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            bar.addWidget(b)
            return b

        tool("Feed", lambda: self.tank.feed(), "Drop some food in (or right-click the water)")
        med = tool("Medicine", lambda: None, "Treat the chosen fish")
        med.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(med)
        for name, illness in MEDICINES.items():
            menu.addAction(f"{name}  (for {illness})", lambda n=name: self._medicate(n))
        med.setMenu(menu)
        tool("Clean", lambda: self.tank.clean(), "Change the water and clear up old food")
        add = tool("Add Fish", lambda: None, "A new fish for the tank")
        add.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(add)
        for kind in SPECIES:
            menu.addAction(QIcon(fish_pixmap(new_fish(kind, random.Random(kind)), 24)), kind,
                           lambda k=kind: self._add(k))
        add.setMenu(menu)
        tool("Stasis...", self.open_stasis, "Fish held out of the tank")
        tool("Decorate...", self.open_decorate, "Background, sand, plants, decorations")
        self.pause_btn = tool("Pause", self.toggle_pause, "Pause: the fish just swim; nothing grows or changes")
        self.pause_btn.setCheckable(True)
        tool("Save Slots...", self.open_slots, "Keep tanks in three save slots")
        bar.addStretch(1)
        tool("Full Screen", self.show_full, "The tank fills the screen (Esc to come back)")
        tool("Desktop Pet", self.show_pet, "A little tank above the taskbar")
        return bar

    def _side(self):
        side = QWidget()
        side.setObjectName("side")
        side.setAttribute(Qt.WA_StyledBackground, True)
        side.setFixedWidth(230)
        col = QVBoxLayout(side)
        col.setContentsMargins(6, 6, 6, 6)
        self.list = QListWidget()
        self.list.setIconSize(QPixmap(28, 28).size())
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setTextElideMode(Qt.ElideRight)
        self.list.currentItemChanged.connect(lambda item, _o: item and self.select(item.data(Qt.UserRole), False))
        col.addWidget(self.list, 1)
        self.info_title = QLabel("Pick a fish")
        self.info_title.setObjectName("title")
        col.addWidget(self.info_title)
        self.info = QLabel()
        self.info.setWordWrap(True)
        col.addWidget(self.info)
        grid = QGridLayout()
        self.bars = {}
        for r, key in enumerate(("hunger", "health", "happiness")):
            grid.addWidget(QLabel(key.title()), r, 0)
            bar = QProgressBar()
            bar.setRange(0, 100)
            grid.addWidget(bar, r, 1)
            self.bars[key] = bar
        col.addLayout(grid)
        row = QHBoxLayout()
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self._rename)
        self.stasis_btn = QPushButton("To Stasis")
        self.stasis_btn.clicked.connect(lambda: self.selected and (self.tank.to_stasis(self.selected),
                                                                   self._refresh_list()))
        row.addWidget(self.rename_btn)
        row.addWidget(self.stasis_btn)
        col.addLayout(row)
        return side

    # ---- saving ----
    def _current(self):
        return host.saves(TITLE) / "current.json"

    def _slot(self, n):
        return host.saves(TITLE) / f"slot{n}.json"

    @staticmethod
    def _load(path):
        try:
            return json.loads(path.read_text(encoding="utf-8")).get("tank")
        except (OSError, ValueError):
            return None

    def _write(self, path):
        data = {"saved": time.time(), "tank": self.tank.d}
        try:
            path.write_text(json.dumps(data), encoding="utf-8")
            return True
        except OSError:
            return False

    def save_current(self):
        self._write(self._current())

    # ---- running ----
    def _tick(self):
        now = time.monotonic()
        dt = min(0.25, now - self.last)
        self.last = now
        self.tank.step(dt)
        for v in (self.view, self.full, self.pet):
            if v is not None and isValid(v) and v.isVisible():
                v.update()
        self.frames = getattr(self, "frames", 0) + 1
        if self.frames % FPS == 0:                      # (once a second)
            self._refresh_info()
            if len(self.tank.d["fish"]) != self.list.count():
                self._refresh_list()
        if self.pet is not None and isValid(self.pet):
            self.pet.keep_on_top()

    def _noted(self, text):
        self._refresh_list()
        self.status.setText(text)

    def select(self, fid, sync=True):
        self.selected = fid
        if sync:
            for i in range(self.list.count()):
                if self.list.item(i).data(Qt.UserRole) == fid:
                    self.list.blockSignals(True)
                    self.list.setCurrentRow(i)
                    self.list.blockSignals(False)
        self._refresh_info()

    def _refresh_list(self):
        self.list.blockSignals(True)
        self.list.clear()
        for f in self.tank.d["fish"]:
            label = f"{f['name']} - {f['kind']}" + (" (sick)" if f["sick"] else "") + (" (died)" if f["dead"] else "")
            item = QListWidgetItem(QIcon(fish_pixmap(f, 28)), label)
            item.setData(Qt.UserRole, f["id"])
            self.list.addItem(item)
            if f["id"] == self.selected:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        self._refresh_info()

    def _refresh_info(self):
        d = self.tank.d
        tt = int(d["tank_time"])
        self.status.setText(f"Fish {len(self.tank.alive())}/{CAPACITY}   In stasis {len(d['stasis'])}   "
                            f"Water {d['water']:.0f}%   Tank time {tt // 3600}h {tt % 3600 // 60:02d}m"
                            + ("   - PAUSED (display only)" if d["paused"] else "")
                            + (f"   |   {d['log'][-1]}" if d["log"] else ""))
        self.pause_btn.setChecked(d["paused"])
        self.pause_btn.setText("Resume" if d["paused"] else "Pause")
        f = self.tank.fish(self.selected) if self.selected else None
        for w in (self.rename_btn, self.stasis_btn):
            w.setEnabled(f is not None and not f["dead"])
        if f is None:
            self.info_title.setText("Pick a fish")
            self.info.setText("Click a fish in the tank or the list to see how it's doing.")
            for b in self.bars.values():
                b.setValue(0)
            return
        mins = int(f["age"] // 60)
        mut = f["genes"].get("mutation")
        self.info_title.setText(f"{f['name']} the {f['kind']}")
        lines = [f"{stage(f)}, {mins // 60}h {mins % 60:02d}m old" + (" (died)" if f["dead"] else ""),
                 f"Length {length(f) * 100:.1f} (grown {growth(f) * 100:.0f}%)",
                 f"Generation {f['generation']}" + (f", child of {' and '.join(f['parents'])}" if f["parents"] else ""),
                 f"Mutation: {mut} ({MUTATIONS[mut]})" if mut else "No mutation",
                 f"<b style='color:#FF8A80'>Sick: {f['sick']} ({ILLNESSES[f['sick']]})</b>" if f["sick"] else "Healthy"]
        self.info.setText("<br>".join(lines))
        for key, bar in self.bars.items():
            bar.setValue(int(f[key]))

    # ---- care ----
    def _medicate(self, name):
        if not self.selected:
            host.message(self.desktop, TITLE, "Pick the fish to treat first (click it in the tank or the list).",
                         "info")
            return
        self.tank.medicate(self.selected, name)
        self._refresh_list()

    def _add(self, kind):
        if self.tank.add(kind) is None:
            host.message(self.desktop, TITLE, f"The tank is full ({CAPACITY} fish). Put some in stasis first.",
                         "info")
        self._refresh_list()

    def _rename(self):
        f = self.tank.fish(self.selected) if self.selected else None
        if f is None:
            return
        try:
            from claudeai.app import ask_text           # (XP's little text prompt, if it's there)
        except ImportError:
            f["name"] = random.choice(NAMES)
            self._refresh_list()
            return

        def done(text):
            if text.strip():
                f["name"] = text.strip()[:20]
                self._refresh_list()
        ask_text(self.desktop, "Rename", f"A new name for {f['name']}:", f["name"], done)

    def toggle_pause(self):
        d = self.tank.d
        d["paused"] = not d["paused"]
        self.tank.note("The tank is paused: the fish just swim, and nothing changes." if d["paused"]
                       else "The tank is running again.")
        self._refresh_info()

    # ---- other windows ----
    def _small_window(self, title, body, size):
        win = host.window(self.desktop, title, body, aquarium_icon(), size)
        body.frame = win
        self.desktop.open_window(win)
        return win

    def open_stasis(self):
        body = QWidget()
        body.setObjectName("aquarium")
        body.setAttribute(Qt.WA_StyledBackground, True)
        body.setStyleSheet(STYLE)
        col = QVBoxLayout(body)
        note = QLabel("Fish in stasis are held frozen: they don't age, get hungry or fall sick until they come back.")
        note.setWordWrap(True)
        col.addWidget(note)
        lst = QListWidget()
        lst.setIconSize(QPixmap(28, 28).size())
        col.addWidget(lst, 1)

        def fill():
            lst.clear()
            for f in self.tank.d["stasis"]:
                it = QListWidgetItem(QIcon(fish_pixmap(f, 28)), f"{f['name']} - {f['kind']}, {stage(f)}"
                                     + (f" ({f['genes']['mutation']})" if f["genes"].get("mutation") else ""))
                it.setData(Qt.UserRole, f["id"])
                lst.addItem(it)

        def back():
            it = lst.currentItem()
            if it is not None and not self.tank.from_stasis(it.data(Qt.UserRole)):
                host.message(self.desktop, TITLE, "The tank is full.", "info")
            fill()
            self._refresh_list()

        def release():
            it = lst.currentItem()
            if it is not None:
                self.tank.release(it.data(Qt.UserRole), from_stasis=True)
                fill()

        row = QHBoxLayout()
        for text, slot in (("Back to the Tank", back), ("Give Away", release)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            row.addWidget(b)
        col.addLayout(row)
        fill()
        self._small_window("Stasis", body, (380, 360))

    def open_decorate(self):
        d = self.tank.d
        body = QWidget()
        body.setObjectName("aquarium")
        body.setAttribute(Qt.WA_StyledBackground, True)
        body.setStyleSheet(STYLE)
        form = QFormLayout(body)
        bg = QComboBox()
        bg.addItems(list(BACKGROUNDS))
        bg.setCurrentText(d["background"])
        bg.currentTextChanged.connect(lambda v: d.update(background=v))
        form.addRow("Water:", bg)
        sand = QComboBox()
        sand.addItems(list(SANDS))
        sand.setCurrentText(d["sand"])
        sand.currentTextChanged.connect(lambda v: d.update(sand=v))
        form.addRow("Floor:", sand)
        for key, label in (("plants", "Plants"), ("bubbles", "Bubbles")):
            cb = QCheckBox(label)
            cb.setChecked(bool(d[key]))
            cb.toggled.connect(lambda on, k=key: d.update({k: on}))
            form.addRow(cb)
        for name in DECOR:
            cb = QCheckBox(name)
            cb.setChecked(name in d["decor"])

            def toggled(on, n=name):
                if on and n not in d["decor"]:
                    d["decor"].append(n)
                elif not on and n in d["decor"]:
                    d["decor"].remove(n)
            cb.toggled.connect(toggled)
            form.addRow(cb)
        pic_row = QHBoxLayout()
        pick = QPushButton("Your Picture...")
        clear = QPushButton("No Picture")

        def chosen(path):
            d["picture"] = str(path)
            _picture_cache.pop(str(path), None)

        pick.clicked.connect(lambda: host.open_dialog(self.desktop, "Background Picture",
                                                      [".jpg", ".jpeg", ".png", ".bmp", ".gif"], chosen,
                                                      aquarium_icon(), start=host.my_pictures()))
        clear.clicked.connect(lambda: d.update(picture=""))
        pic_row.addWidget(pick)
        pic_row.addWidget(clear)
        form.addRow("Backdrop:", pic_row)
        self._small_window("Decorate the Tank", body, (330, 330))

    def open_slots(self):
        body = QWidget()
        body.setObjectName("aquarium")
        body.setAttribute(Qt.WA_StyledBackground, True)
        body.setStyleSheet(STYLE)
        grid = QGridLayout(body)
        labels = {}

        def describe(n):
            path = self._slot(n)
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return f"Slot {n}: empty"
            t = data.get("tank") or {}
            alive = [f for f in t.get("fish", []) if not f.get("dead")]
            when = time.strftime("%b %d, %I:%M %p", time.localtime(data.get("saved", 0)))
            return f"Slot {n}: {len(alive)} fish, {len(t.get('stasis', []))} in stasis - saved {when}"

        def refresh():
            for n, lab in labels.items():
                lab.setText(describe(n))

        def save(n):
            self._write(self._slot(n))
            self.tank.note(f"Saved the tank to slot {n}.")
            refresh()

        def load(n):
            data = self._load(self._slot(n))
            if not data:
                return

            def answer(button):
                if button == "Yes":
                    self.tank.d = Tank(data).d
                    self.selected = None
                    self.tank.note(f"Loaded slot {n}.")
                    self._refresh_list()
            host.message(self.desktop, TITLE, f"Load slot {n}? The tank you have now will be replaced (save it "
                         "first if you want to keep it).", "question", ("Yes", "No"), answer)

        def delete(n):
            def answer(button):
                if button == "Yes":
                    try:
                        self._slot(n).unlink()
                    except OSError:
                        pass
                    refresh()
            host.message(self.desktop, TITLE, f"Delete save slot {n}?", "question", ("Yes", "No"), answer)

        for r, n in enumerate((1, 2, 3)):
            lab = QLabel()
            lab.setWordWrap(True)
            labels[n] = lab
            grid.addWidget(lab, r * 2, 0, 1, 3)
            for c, (text, slot) in enumerate((("Save Here", save), ("Load", load), ("Delete", delete))):
                b = QPushButton(text)
                b.clicked.connect(lambda _c=False, f=slot, n=n: f(n))
                grid.addWidget(b, r * 2 + 1, c)
        refresh()
        self._small_window("Save Slots", body, (420, 260))

    # ---- full screen and the pet ----
    def show_full(self):
        if self.full is None or not isValid(self.full):
            self.full = FullScreenTank(self)
        self.full.open()

    def show_pet(self):
        if self.pet is None or not isValid(self.pet):
            self.pet = PetTank(self)
        self.pet.place()
        self.pet.show()
        if self.frame is not None and hasattr(self.desktop, "minimize"):
            self.desktop.minimize(self.frame)           # (the tank keeps running; the pet shows it)

    def bring_back(self):
        if self.frame is not None and isValid(self.frame):
            self.desktop.open_window(self.frame)

    def closeEvent(self, event):
        self.save_current()
        if self.pet is not None and isValid(self.pet):
            self.pet.deleteLater()
            self.pet = None
        if self.full is not None and isValid(self.full):
            self.full.deleteLater()
            self.full = None
        self.timer.stop()
        event.accept()


class FullScreenTank(TankView):
    """The tank over the whole screen. Esc (or the button) comes back to the window; right-click feeds."""

    def __init__(self, app):
        super().__init__(app)
        self.setParent(app.desktop)
        self.setFocusPolicy(Qt.StrongFocus)
        self.back = QPushButton("Back to Window (Esc)", self)
        self.back.setStyleSheet("QPushButton { background: rgba(0,0,0,110); color: white; border: 1px solid "
                                "rgba(255,255,255,90); border-radius: 3px; padding: 4px 10px; }")
        self.back.clicked.connect(self.leave)
        self.feed_btn = QPushButton("Feed", self)
        self.feed_btn.setStyleSheet(self.back.styleSheet())
        self.feed_btn.clicked.connect(lambda: app.tank.feed())

    def open(self):
        self.setGeometry(self.app.desktop.rect())
        self.back.adjustSize()
        self.feed_btn.adjustSize()
        self.back.move(self.width() - self.back.width() - 12, 12)
        self.feed_btn.move(self.back.x() - self.feed_btn.width() - 8, 12)
        self.show()
        self.raise_()
        self.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.leave()

    def leave(self):
        self.hide()
        self.app.bring_back()


class PetTank(TankView):
    """A little tank (100 x 50) sitting in the middle of the screen, just above the taskbar."""
    W, H = 100, 50

    def __init__(self, app):
        super().__init__(app, small=True)
        self.setParent(app.desktop)
        self.setFixedSize(self.W, self.H)
        self.setToolTip("Claude Aquarium - click to open, right-click for more")
        self.setCursor(Qt.PointingHandCursor)

    def place(self):
        desk = self.app.desktop
        area = desk.work_area() if hasattr(desk, "work_area") else desk.rect()
        self.move(area.center().x() - self.W // 2, area.bottom() - self.H - 2)
        self.raise_()

    def keep_on_top(self):
        if self.isVisible() and self.parentWidget() is not None:
            kids = self.parentWidget().children()
            if kids and kids[-1] is not self:
                self.raise_()

    def paintEvent(self, event):
        p = QPainter(self)
        draw_tank(p, self.app.tank, self.width(), self.height(), small=True)
        p.setPen(QPen(QColor("#1F2A33"), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRect(self.rect().adjusted(1, 1, -1, -1))

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            menu = QMenu(self)
            menu.addAction("Feed", lambda: self.app.tank.feed())
            menu.addAction("Open the Tank", self.app.bring_back)
            menu.addAction("Full Screen", self.app.show_full)
            menu.addSeparator()
            menu.addAction("Put the Pet Away", self.hide)
            menu.exec(event.globalPosition().toPoint())
        else:
            self.app.bring_back()


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = Aquarium(desktop)
        win = host.window(desktop, TITLE, body, aquarium_icon(), (900, 560))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.save_current()
