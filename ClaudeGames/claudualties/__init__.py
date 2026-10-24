"""Claudualties: Unknown - descend the planet's caves for the cargo, and keep the Expie alive on the way. In the
spirit of Casualties: Unknown (Orsoniks, 2025-26).

Five layers of cave, carved anew each run: ledges and drops, pools, glass, the loot earlier expeditions left, a
trader or two, lore notes, and the hatch down. Falls break bones and open wounds; wounds bleed and go bad; cold
water chills; the Expie gets hungry, thirsty, tired and gloomy. The brainchip shows all of it, and a stopped
heart or an empty brain ends the run. The pictures are Orsoniks' (your copy in Local Storage\\casualties unknown);
the sound is synthesized.

Keys: A/D move, W jump, S at a hatch descends (or drops through a ledge), E interact, U use the selected item,
1-9 0 - = pick an item, C craft, F flashlight, R rest, M music, N sounds, Esc pause, F3 timing.
Mouse: click a body part with a medical item selected to treat it; click items, stock and buttons.
"""
import json
import math
import random
import time
from pathlib import Path

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QLinearGradient, QPainter, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import QWidget
from shiboken6 import isValid

from claudecore import host

from . import items as I
from . import world as Wd
from .body import Body, PARTS, PART_NAMES

VW, VH = 960, 600
PANEL_W = 300
VIEW_W = VW - PANEL_W
TS = 32                              # a tile on screen
GREEN, DIM, RED, AMBER = "#3CE07A", "#1E6A3C", "#FF4A4A", "#FFC040"
PRESETS = {
    "Normal": {"danger": 1.0, "loot": 1.0, "mood": 1.0, "chip": True,
               "blurb": "The caves as they are. Expect to die a lot."},
    "Relaxed": {"danger": 0.6, "loot": 1.5, "mood": 0.7, "chip": True,
                "blurb": "Softer falls, more to find. For learning the layers."},
    "Paradise": {"danger": 0.3, "loot": 2.5, "mood": 0.4, "chip": True,
                 "blurb": "A gentle planet. Loot everywhere, little that hurts."},
    "Unchipped": {"danger": 1.0, "loot": 1.0, "mood": 1.0, "chip": False,
                  "blurb": "No brainchip: no vitals, no body readout. Only what the Expie tells you."},
}
PRESET_ORDER = ["Normal", "Relaxed", "Paradise", "Unchipped"]
NOTE_TEXT = [
    "They brought us down in crates. Eleven of us. I counted the ones that woke.",
    "Fluids go in the arm. Not the neck. Whoever wrote the earlier note, I'm sorry.",
    "The glass gardens cut through boots. Wrap your legs before you cross.",
    "Keep moving when it's cold. Dig if you have to. Standing still is how it takes you.",
    "It stood in the dark and watched me bandage my arm. It didn't come closer. Yet.",
    "I saw one of the big ones sleeping. The trader says they don't wake for days.",
    "Blood pressure drops before you feel it. When your ears ring, sit down.",
    "The lights in the walls aren't plants. Don't eat them.",
    "If you're reading this, the hatch below is stuck. Shovel through to the left of it.",
    "Expedition 4 left a medkit in every third room. Expedition 5 took them all.",
    "My tail stopped bleeding on its own. The arm didn't. Gauze first, always.",
    "There's a drawing of us in the chip. Little outline. Six parts. That's all we are to them.",
    "The water on the third layer is colder than it looks. Thirty seconds. Then out.",
    "I'm not going deeper today. I'm not. Tomorrow.",
    "Set the bone before it swells or it sets wrong. Count to three and pull.",
    "The military trader won't sell to you if you're bleeding on his mat. Clean up first.",
    "Something with too many legs took the last of the bread.",
    "Its mouth was full of teeth and it was smiling.",
    "Cargo recovered means we go home. They keep saying that.",
    "I kept the hat. It's stupid. It helps.",
    "Day nine. The chip says my mood is 12%. The chip is an optimist.",
    "If the heart stops, the pads go here and here. Wait for the beep. Then the button.",
    "The bottom is lit. I don't know by what.",
    "Please. Whoever finds the cargo. Don't bring it up.",
]
SPEECH = {
    "cold": ["...c-cold.", "I can't feel my paws.", "Need to get dry."],
    "hot": ["I'm burning up.", "Everything's too warm."],
    "hungry": ["Stomach hurts.", "Anything to eat?", "So hungry."],
    "thirsty": ["Water...", "Mouth's like sand."],
    "tired": ["Can't keep my eyes open.", "Just a minute. Please."],
    "pain": ["It hurts.", "Ow. Ow ow ow.", "Make it stop."],
    "dark": ["I can't see anything.", "Who's there?"],
    "sad": ["What's the point.", "...", "Leave me alone."],
    "bleeding": ["I'm bleeding.", "There's a lot of blood."],
    "fine": ["Okay. Okay.", "Still here.", "Onward, I guess.", "*sniff*"],
    "happy": ["Hey, this isn't so bad.", "*wags*"],
    "refuse": ["No.", "...no.", "I don't want to."],
}


def root():
    return Path(host.local_storage()) / "casualties unknown"


def _progress_file():
    return host.saves("claudualties") / "progress.json"


def claudualties_icon():
    """The Expie's head: dark, with an orange eye."""
    ic = QIcon()
    for sz in (16, 32, 48):
        pm = QPixmap(sz, sz)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        s = sz / 32
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1A1A1E"))
        p.drawEllipse(QRectF(3 * s, 8 * s, 26 * s, 18 * s))
        p.drawPolygon([QPointF(6 * s, 12 * s), QPointF(9 * s, 2 * s), QPointF(14 * s, 10 * s)])
        p.drawPolygon([QPointF(14 * s, 11 * s), QPointF(19 * s, 3 * s), QPointF(21 * s, 11 * s)])
        p.setBrush(QColor("#FF8A2A"))
        p.drawEllipse(QRectF(19 * s, 13 * s, 6 * s, 5 * s))
        p.setBrush(QColor("#000000"))
        p.drawEllipse(QRectF(22 * s, 14 * s, 2.5 * s, 3 * s))
        p.end()
        ic.addPixmap(pm)
    return ic


class Claudualties(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setMinimumSize(480, 300)
        from .assets import Assets
        from .sound import Audio
        self.assets = Assets(root())
        self.problem = "" if self.assets.ok else (f"The Casualties: Unknown pictures aren't on this computer's external "
                                                   f"drive:\n{root()}")
        self.audio = Audio(self)
        self.state = "menu"
        self.preset_name = "Normal"
        self.mouse = QPointF(-1, -1)
        self.keys = set()
        self.progress = self._load_progress()
        self.overlay_f3 = False
        self.stats = [0, 0, 0.0, 0.0]
        self.flash_cache = None
        self.run = None
        self.acc = 0.0
        self.last = time.monotonic()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)
        self.menu_t = 0.0

    # ---- progress ----------------------------------------------------------------------------------------------
    def _load_progress(self):
        try:
            d = json.loads(_progress_file().read_text(encoding="utf-8"))
            if isinstance(d, dict):
                d.setdefault("runs", 0)
                d.setdefault("deaths", 0)
                d.setdefault("wins", 0)
                d.setdefault("best", {})
                return d
        except (OSError, ValueError):
            pass
        return {"runs": 0, "deaths": 0, "wins": 0, "best": {}}

    def _save_progress(self):
        try:
            _progress_file().write_text(json.dumps(self.progress, indent=1), encoding="utf-8")
        except OSError:
            pass

    # ---- a run ---------------------------------------------------------------------------------------------------
    def new_run(self):
        preset = dict(PRESETS[self.preset_name])
        self.progress["runs"] += 1
        self._save_progress()
        self.run = {"preset": preset, "name": self.preset_name, "layer": None, "index": 0, "body": Body(preset),
                    "inv": ["gauze", "water", "bread"], "cap": 12, "sel": 0, "x": 0.0, "y": 0.0, "vx": 0.0, "vy": 0.0,
                    "facing": 1, "ground": False, "fall_from": None, "phase": 0.0, "moving": False,
                    "light": False, "battery": 0.0, "torch": 0.0, "rope": False, "worn": set(),
                    "speech": None, "speech_t": 0.0, "say_t": 8.0, "log": [], "t": 0.0, "resting": False,
                    "used": 0, "water_t": 0.0, "glass_t": 0.0, "step_t": 0.0, "overlay": None}
        self.enter_layer(1)
        self.state = "play"
        self.log("The crate opens. Cold air. Down is the only way.")
        self.setFocus()

    def enter_layer(self, n):
        r = self.run
        r["index"] = n
        r["layer"] = Wd.Layer(n, r["preset"])
        sx, sy = r["layer"].start
        r["x"], r["y"] = sx + 0.5, sy + 1.0
        r["vx"] = r["vy"] = 0.0
        r["ground"] = False
        r["fall_from"] = None
        r["rope"] = False
        key = self.preset_name
        if n > self.progress["best"].get(key, 0):
            self.progress["best"][key] = n
            self._save_progress()
        self.log(f"Layer {n}: {r['layer'].name}.")
        if r["layer"].dark and not (r["light"] and r["battery"] > 0) and r["torch"] <= 0:
            self.say("I can't see anything.")

    def log(self, text):
        r = self.run
        if r is None:
            return
        r["log"].append((text, r["t"]))
        r["log"] = r["log"][-7:]

    def say(self, text):
        r = self.run
        r["speech"], r["speech_t"] = text, 3.5
        self.log(f"\"{text}\"")

    # ---- the loop --------------------------------------------------------------------------------------------------
    def _tick(self):
        now = time.monotonic()
        dt = min(0.2, now - self.last)
        self.last = now
        self.menu_t += dt
        self.audio.tick(dt)
        if self.state == "play" and self.run is not None:
            t0 = time.perf_counter()
            self.acc += dt
            steps = 0
            while self.acc >= 1 / 60 and steps < 5:
                self.acc -= 1 / 60
                self._step(1 / 60)
                steps += 1
            if steps == 5:
                self.acc = 0.0
            self.stats[1] += steps
            self.stats[2] = (time.perf_counter() - t0) * 1000
        elif self.run is not None and self.state in ("trade", "note", "craft", "minigame", "pause"):
            self.run["body"].step(dt * 0.3)                 # time still passes, slowly, while you think
            self._body_events()
            self._mix()
        self.update()

    def _step(self, dt):
        r = self.run
        b = r["body"]
        lv = r["layer"]
        r["t"] += dt
        k = self.keys
        want = 0
        if b.conscious and b.alive and not r["resting"]:
            if Qt.Key_A in k or Qt.Key_Left in k:
                want = -1
            if Qt.Key_D in k or Qt.Key_Right in k:
                want = 1
        if want and b.refuses() and random.random() < 0.02:
            want = 0
            self.say(random.choice(SPEECH["refuse"]))
            self.audio.play("refuse")
        speed = 5.0 * b.speed()
        in_water = lv.tile(int(r["x"]), int(r["y"] - 0.5)) == 2
        if in_water:
            speed *= 0.55
        r["vx"] = want * speed
        if want:
            r["facing"] = want
        r["moving"] = bool(want)
        # gravity and jumping
        if in_water:
            r["vy"] = min(r["vy"] + 10 * dt, 2.5)
            if (Qt.Key_W in k or Qt.Key_Up in k or Qt.Key_Space in k) and b.conscious:
                r["vy"] = -3.0
                # at the surface: a kick that lifts it out onto the edge
                if lv.tile(int(r["x"]), int(r["y"] - 1.6)) == 0:
                    r["vy"] = -9.0
        else:
            r["vy"] += 30 * dt
        if r["ground"] and not in_water and b.conscious and not r["resting"] and \
                (Qt.Key_W in k or Qt.Key_Up in k or Qt.Key_Space in k):
            legs_ok = not any(b.parts[n].fracture and not b.parts[n].splint for n in ("l_leg", "r_leg"))
            r["vy"] = -9.5 if legs_ok else -6.0
            r["ground"] = False
        r["vy"] = min(r["vy"], 22)
        # move x
        nx = r["x"] + r["vx"] * dt
        hw = 0.33
        feet, head = r["y"] - 0.05, r["y"] - 1.45
        blocked = False
        for ty in (int(head), int((head + feet) / 2), int(feet)):
            if lv.solid(int(nx + hw * (1 if r["vx"] > 0 else -1)), ty):
                blocked = True
        if blocked and r["ground"] and not lv.solid(int(nx + hw * (1 if r["vx"] > 0 else -1)), int(feet) - 1) \
                and not lv.solid(int(nx), int(head) - 1):
            r["y"] -= 1.0                                   # step up one tile
            blocked = False
        if not blocked:
            r["x"] = max(0.5, min(Wd.W - 0.5, nx))
        # move y
        ny = r["y"] + r["vy"] * dt
        if r["vy"] > 0:
            tx0, tx1 = int(r["x"] - hw + 0.02), int(r["x"] + hw - 0.02)
            ty = int(ny)
            drop_through = (Qt.Key_S in k or Qt.Key_Down in k)
            landed = False
            for tx in (tx0, tx1):
                t = lv.tile(tx, ty)
                if t == 1 or t == 4 or (t == 5 and int(r["y"]) < ty and not drop_through):
                    landed = True
            if landed:
                ny = float(ty)
                if not r["ground"]:
                    self._land(ty)
                r["ground"] = True
                r["vy"] = 0.0
            else:
                r["ground"] = False
        else:
            ty = int(ny - 1.5)
            if lv.solid(int(r["x"] - hw), ty) or lv.solid(int(r["x"] + hw), ty):
                ny = ty + 1.5 + 0.01
                r["vy"] = 0.0
            r["ground"] = False
        if not r["ground"] and r["fall_from"] is None and r["vy"] > 0:
            r["fall_from"] = r["y"]
        if not r["ground"] and r["fall_from"] is not None and r["vy"] < 0:
            r["fall_from"] = min(r["fall_from"], ny)
        if in_water:
            r["fall_from"] = None
        r["y"] = ny
        if r["y"] > Wd.H + 2:
            b.brain = 0
            b.cause = "the fall"
            b.alive = False
            b.events.append(("die", "the fall"))
        # walking animation, footsteps
        if r["moving"] and r["ground"]:
            r["phase"] = (r["phase"] + dt * 2.2 * b.speed()) % 1.0
            r["step_t"] -= dt
            if r["step_t"] <= 0:
                r["step_t"] = 0.32 / max(0.3, b.speed())
                self.audio.play("step", 0.5)
        # glass underfoot
        standing_on = lv.tile(int(r["x"]), int(r["y"]))
        if standing_on == 3 and r["moving"] and r["ground"]:
            r["glass_t"] += dt
            if r["glass_t"] > 0.25:
                r["glass_t"] = 0.0
                if random.random() < 0.35 * r["preset"]["danger"] and b.glass():
                    pass
        # water
        if in_water:
            r["water_t"] += dt
            if r["water_t"] > 1.0:
                r["water_t"] = 0.0
                cold = lv.cold * (0.6 if "wrap" in r["worn"] else 1.0)
                b.soak(cold)
        # light
        dark = lv.dark
        lit = not dark
        if r["light"] and r["battery"] > 0:
            r["battery"] = max(0.0, r["battery"] - dt)
            lit = True
            if r["battery"] <= 0:
                r["light"] = False
                self.log("The flashlight dies.")
        if r["torch"] > 0:
            r["torch"] = max(0.0, r["torch"] - dt)
            lit = True
            if r["torch"] <= 0:
                self.log("The torch gutters out.")
        near_light = any(t["kind"] == "light" and abs(t["x"] - r["x"]) < 5 and abs(t["y"] - r["y"]) < 4 for t in lv.things)
        lit = lit or near_light
        # the body
        if r["resting"]:
            b.rest(dt)
            if b.exhaustion <= 5 or r["moving"] or not b.conscious:
                r["resting"] = False
        b.step(dt, moving=r["moving"], dark=dark, in_water=in_water, light=lit)
        if "hat" in r["worn"]:
            b.mood = min(100.0, b.mood + 0.02 * dt)
        self._body_events()
        # speech
        if r["speech_t"] > 0:
            r["speech_t"] -= dt
            if r["speech_t"] <= 0:
                r["speech"] = None
        r["say_t"] -= dt
        if r["say_t"] <= 0 and b.alive:
            r["say_t"] = random.uniform(9, 16)
            self._comment(dark and not lit)
        self._mix(in_water, dark and not lit)
        if not b.alive:
            self._die()

    def _land(self, ty):
        r = self.run
        b = r["body"]
        fell = (r["y"] - r["fall_from"]) if r["fall_from"] is not None else 0.0
        r["fall_from"] = None
        if fell < 1.5:
            return
        if r["layer"].tile(int(r["x"]), ty - 1) == 2:
            self.audio.play("splash")
            return
        if r["rope"]:
            r["rope"] = False
            self.log("Down the rope. Not a scratch.")
            return
        result = b.fall(fell)
        if result is None:
            self.audio.play("land", 0.4)
        elif result == "bruise":
            self.audio.play("land")
        b.str = min(5.0, b.str + 0.01)

    def _body_events(self):
        b = self.run["body"]
        sounds = {"hurt": "yelp", "crack": "crack", "bleed": "whimper", "cut": "cut", "bandage": "bandage", "eat": "eat",
                  "drink": "drink", "shock": "shock", "die": "die", "arrest": "beep", "healed": "chime", "land": None,
                  "yelp": "yelp", "soaked": None, "wake": None}
        for kind, detail in b.events:
            s = sounds.get(kind)
            if s:
                self.audio.play(s)
            if detail and isinstance(detail, str):
                self.log(detail)
            if kind in ("hurt", "crack", "bleed", "cut") and random.random() < 0.6:
                self.say(random.choice(SPEECH["pain"]))
            if kind == "arrest":
                self.say("...")
        b.events = []

    def _comment(self, dark):
        b = self.run["body"]
        pool = []
        if b.temp < 34.5:
            pool += SPEECH["cold"] * 2
        if b.temp > 38.5:
            pool += SPEECH["hot"]
        if b.hunger > 65:
            pool += SPEECH["hungry"]
        if b.thirst > 65:
            pool += SPEECH["thirsty"]
        if b.exhaustion > 75:
            pool += SPEECH["tired"]
        if b.pain > 25:
            pool += SPEECH["pain"]
        if dark:
            pool += SPEECH["dark"]
        if b.mood < 25:
            pool += SPEECH["sad"] * 2
        if any(p.bleed > 0.3 and p.bandage <= 0 for p in b.parts.values()):
            pool += SPEECH["bleeding"]
        if not pool:
            pool = SPEECH["happy"] if b.mood > 80 else SPEECH["fine"]
            if random.random() < 0.5:
                return
        self.say(random.choice(pool))

    def _mix(self, in_water=False, dark=False):
        a = self.audio
        b = self.run["body"]
        lv = self.run["layer"]
        near_water = in_water or any(lv.tile(int(self.run["x"]) + dx, int(self.run["y"]) + dy) == 2
                                     for dx in (-4, 0, 4) for dy in (-2, 0, 2))
        a.want["cave"] = 0.6 + 0.1 * lv.index
        a.want["water"] = 1.0 if near_water else 0.0
        heart = 0.0
        if b.blood < 55 or b.pain > 40 or b.arrest:
            heart = min(1.0, (55 - b.blood) / 40 + (0.4 if b.pain > 40 else 0)) if not b.arrest else 0.0
        a.want["heart"] = heart
        a.rate = max(0.6, min(2.2, b.heart / 70.0))
        a.want["crisis"] = min(1.0, (45 - b.brain) / 30) if b.brain < 45 or b.arrest else 0.0

    def _die(self):
        r = self.run
        self.state = "death"
        self.progress["deaths"] += 1
        self._save_progress()
        r["death_img"] = random.randrange(3)
        self.audio.want.update({"heart": 0.0, "crisis": 0.0, "water": 0.0})
        self.audio.play("die")

    # ---- the player's actions -------------------------------------------------------------------------------------
    def inv_count(self, key):
        return sum(1 for i in self.run["inv"] if i == key)

    def scrap(self):
        return sum(I.value(i) for i in self.run["inv"] if I.kind(i) == "currency")

    def take(self, key):
        r = self.run
        if len(r["inv"]) >= r["cap"]:
            self.log(f"No room for the {I.name(key).lower()}.")
            return False
        r["inv"].append(key)
        self.audio.play("pickup")
        return True

    def remove(self, key, n=1):
        r = self.run
        for _ in range(n):
            if key in r["inv"]:
                r["inv"].remove(key)
        r["sel"] = min(r["sel"], max(0, len(r["inv"]) - 1))

    def selected(self):
        r = self.run
        return r["inv"][r["sel"]] if r["inv"] and 0 <= r["sel"] < len(r["inv"]) else None

    def interact(self):
        r = self.run
        lv = r["layer"]
        b = r["body"]
        if not b.conscious:
            return
        t = lv.thing_at(int(r["x"]), int(r["y"]), reach=2) or lv.thing_at(int(r["x"]), int(r["y"]) - 1, reach=2)
        if t is None:
            if lv.tile(int(r["x"]), int(r["y"])) == 4:
                self.descend()
            return
        if t["kind"] == "loot":
            if t["open"]:
                self.log("Empty.")
                return
            got = []
            for key in list(t["items"]):
                if self.take(key):
                    t["items"].remove(key)
                    got.append(I.name(key))
            if not t["items"]:
                t["open"] = True
            if got:
                self.log("Found: " + ", ".join(got) + ".")
                b.mood = min(100.0, b.mood + 2)
        elif t["kind"] == "note":
            t["read"] = True
            r["overlay"] = ("note", t["note"])
            self.state = "note"
            self.audio.play("note")
            b.int = min(5.0, b.int + 0.1)
        elif t["kind"] == "trader":
            r["overlay"] = ("trade", t)
            t["woken"] = True
            self.state = "trade"
            self.audio.play("chime")
        elif t["kind"] == "cargo":
            self._win()

    def descend(self):
        r = self.run
        if r["layer"].tile(int(r["x"]), int(r["y"])) != 4:
            return
        self.audio.play("hatch")
        if r["index"] >= 5:
            return
        self.enter_layer(r["index"] + 1)

    def use_selected(self):
        r = self.run
        b = r["body"]
        key = self.selected()
        if key is None or not b.conscious and key != "aed":
            return
        kind = I.kind(key)
        if kind == "consume":
            msg = b.consume(key)
            if msg:
                self.remove(key)
                self.log(msg)
                r["used"] += 1
            return
        if kind == "medical":
            self.log(f"Click the body part to use the {I.name(key).lower()} on.")
            return
        if key == "flashlight":
            self.toggle_light()
        elif key == "battery":
            r["battery"] += 600.0
            self.remove(key)
            self.log("A fresh battery in the flashlight." if self.inv_count("flashlight") else "A battery, for when there's a flashlight.")
        elif key == "torch":
            r["torch"] = 180.0
            self.remove(key)
            self.log("The torch catches. Three minutes of light, maybe.")
            self.audio.play("flash")
        elif key == "rope":
            if r["rope"]:
                self.log("The rope's already tied off.")
            else:
                r["rope"] = True
                self.remove(key)
                self.log("Rope tied off. The next drop is a climb.")
        elif key == "shovel":
            tx, ty = int(r["x"]), int(r["y"])
            if r["layer"].tile(tx, ty) == 1 and ty < Wd.H - 2:
                r["layer"].tiles[ty][tx] = 0
                b.temp = min(37.5, b.temp + 0.4)
                b.exhaustion = min(100.0, b.exhaustion + 4)
                b.str = min(5.0, b.str + 0.03)
                self.audio.play("crack", 0.5)
                self.log("Dug through.")
            else:
                self.log("Nothing to dig here.")
        elif key == "aed":
            if b.arrest:
                r["overlay"] = ("minigame", "aed", 0.0, None)
                self.state = "minigame"
            else:
                self.log(b.defibrillate(False) if False else "The heart's beating. Save it.")
        elif key == "bag":
            r["cap"] = 16
            self.remove(key)
            self.log("Four more slots.")
        elif key in ("hat", "wrap"):
            r["worn"].add(key)
            self.remove(key)
            self.log(f"Wearing the {I.name(key).lower()}.")
        elif key == "knife":
            if "cloth" in r["inv"]:
                self.remove("cloth")
                r["inv"] += ["gauze", "gauze"]
                self.audio.play("cut")
                self.log("Cut the cloth into two gauze.")
            else:
                self.log("Nothing to cut. Select it and click a body part to dig glass out.")
        elif key in ("stick", "cloth", "scrap", "crystal"):
            self.log(I.blurb(key))
        elif key == "cargo":
            self._win()

    def toggle_light(self):
        r = self.run
        if "flashlight" not in r["inv"]:
            return
        if r["battery"] <= 0:
            self.log("The flashlight has no battery.")
            return
        r["light"] = not r["light"]
        self.audio.play("flash")

    def treat(self, part):
        r = self.run
        b = r["body"]
        key = self.selected()
        if key is None or I.kind(key) != "medical" and key != "knife":
            return
        if key == "splint" and b.parts[part].fracture and not b.parts[part].splint:
            r["overlay"] = ("minigame", "splint", 0.0, part)
            self.state = "minigame"
            return
        msg = b.treat(part, key)
        if msg is None:
            self.log(f"The {I.name(key).lower()} does nothing for the {PART_NAMES[part].lower()}.")
            return
        self.remove(key) if key not in ("tweezers", "knife") else None
        self.log(msg)
        r["used"] += 1

    def craft(self, recipe):
        r = self.run
        out, needs, label = recipe
        for k, n in needs.items():
            if n and self.inv_count(k) < n:
                return
            if n == 0 and k not in r["inv"]:
                return
        for k, n in needs.items():
            self.remove(k, n)
        if out == "gauze":
            r["inv"] += ["gauze", "gauze"]
        else:
            r["inv"].append(out)
        r["body"].int = min(5.0, r["body"].int + 0.08)
        self.audio.play("craft")
        self.log(f"Made {label}.")

    def _win(self):
        r = self.run
        self.state = "win"
        self.progress["wins"] += 1
        self.progress["best"][self.preset_name] = 6
        self._save_progress()
        self.audio.play("chime")
        self.audio.want.update({"heart": 0.0, "crisis": 0.0})

    # ---- geometry -----------------------------------------------------------------------------------------------------
    def _xf(self):
        sc = min(self.width() / VW, self.height() / VH)
        return sc, (self.width() - VW * sc) / 2, (self.height() - VH * sc) / 2

    def _logical(self, pos):
        sc, ox, oy = self._xf()
        return QPointF((pos.x() - ox) / sc, (pos.y() - oy) / sc)

    def _camera(self):
        r = self.run
        cx = r["x"] * TS - VIEW_W / 2
        cy = (r["y"] - 1) * TS - VH / 2
        cx = max(0, min(Wd.W * TS - VIEW_W, cx))
        cy = max(0, min(Wd.H * TS - VH, cy))
        return cx, cy

    # ---- painting ------------------------------------------------------------------------------------------------------
    def paintEvent(self, _e):
        t0 = time.perf_counter()
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#000000"))
        sc, ox, oy = self._xf()
        p.translate(ox, oy)
        p.scale(sc, sc)
        p.setClipRect(QRectF(0, 0, VW, VH))
        if self.problem:
            p.setPen(QColor("#FFFFFF"))
            p.setFont(self._font(16, False, "Arial"))
            p.drawText(QRectF(60, 160, VW - 120, 300), Qt.AlignCenter | Qt.TextWordWrap, self.problem)
        elif self.state == "menu":
            self._paint_menu(p)
        else:
            self._paint_world(p)
            self._paint_panel(p)
            if self.state == "trade":
                self._paint_trade(p)
            elif self.state == "note":
                self._paint_note(p)
            elif self.state == "craft":
                self._paint_craft(p)
            elif self.state == "minigame":
                self._paint_minigame(p)
            elif self.state == "pause":
                self._dim(p, "PAUSED", "Esc to carry on   -   Q to give up this run")
            elif self.state == "death":
                self._paint_death(p)
            elif self.state == "win":
                self._paint_win(p)
        if self.overlay_f3:
            p.fillRect(QRectF(VIEW_W - 250, 4, 246, 40), QColor(0, 0, 0, 180))
            p.setPen(QColor(GREEN))
            p.setFont(self._font(11, False))
            p.drawText(QRectF(VIEW_W - 244, 6, 240, 36), Qt.AlignLeft,
                       f"step {self.stats[2]:.2f} ms  paint {self.stats[3]:.2f} ms\nsteps {self.stats[1]}  frames {self.stats[0]}")
        p.end()
        self.stats[0] += 1
        self.stats[3] = (time.perf_counter() - t0) * 1000

    def _font(self, size, bold=True, family="Lucida Console"):
        f = QFont(family)
        f.setPixelSize(size)
        f.setBold(bold)
        return f

    def _paint_menu(self, p):
        a = self.assets
        if not a.title.isNull():
            p.drawImage(QRectF(0, 0, VW, VH), a.title, QRectF(0, 0, a.title.width(), a.title.height()))
        p.fillRect(QRectF(0, 0, VW, VH), QColor(0, 0, 10, 120))
        p.setPen(QColor("#FFFFFF"))
        p.setFont(self._font(44, False, "Lucida Console"))
        p.drawText(QRectF(40, 40, VW, 56), Qt.AlignLeft, "claudualties:")
        p.setPen(QColor("#A0A0A8"))
        p.setFont(self._font(40, False, "Lucida Console"))
        p.drawText(QRectF(70, 92, VW, 52), Qt.AlignLeft, "unknown")
        p.setPen(QColor("#C0C0C8"))
        p.setFont(self._font(13, False, "Arial"))
        p.drawText(QRectF(42, 150, 560, 60), Qt.AlignLeft | Qt.TextWordWrap,
                   "Descend into the planet's caves to retrieve the cargo. Survival chances are near 0%.\n"
                   "Pick how the planet treats you:")
        for name, r in self._preset_rects():
            sel = name == self.preset_name
            p.setPen(QPen(QColor("#FFFFFF" if sel else "#505060"), 2 if sel else 1))
            p.setBrush(QColor(20, 20, 30, 200))
            p.drawRoundedRect(r, 8, 8)
            img = a.presets.get(name)
            if img is not None and not img.isNull():
                p.drawImage(QRectF(r.x() + 8, r.y() + 8, 104, 104), img, QRectF(0, 0, img.width(), img.height()))
            p.setPen(QColor("#FFFFFF" if sel else "#C0C0C8"))
            p.setFont(self._font(15))
            p.drawText(QRectF(r.x() + 8, r.y() + 118, r.width() - 16, 20), Qt.AlignLeft, name)
            p.setFont(self._font(11, False, "Arial"))
            p.setPen(QColor("#B0B0B8"))
            p.drawText(QRectF(r.x() + 8, r.y() + 138, r.width() - 16, 60), Qt.AlignLeft | Qt.TextWordWrap, PRESETS[name]["blurb"])
            best = self.progress["best"].get(name)
            if best:
                p.setPen(QColor(GREEN))
                p.drawText(QRectF(r.x() + 8, r.y() + r.height() - 22, r.width() - 16, 18), Qt.AlignLeft,
                           "Cargo recovered" if best >= 6 else f"Deepest: layer {best}")
        r = self._begin_rect()
        p.setPen(QPen(QColor(GREEN), 2))
        p.setBrush(QColor(10, 40, 20, 220) if r.contains(self.mouse) else QColor(5, 20, 10, 220))
        p.drawRoundedRect(r, 8, 8)
        p.setPen(QColor("#FFFFFF"))
        p.setFont(self._font(18))
        p.drawText(r, Qt.AlignCenter, "DESCEND")
        p.setPen(QColor("#808088"))
        p.setFont(self._font(11, False, "Arial"))
        p.drawText(QRectF(0, VH - 26, VW, 20), Qt.AlignHCenter,
                   f"runs {self.progress['runs']}   deaths {self.progress['deaths']}   cargo recovered {self.progress['wins']}"
                   "      M music   N sounds")
        if a.ok:
            a.draw_expie(p, 820, 560, -1, (self.menu_t * 0.6) % 1.0 if False else None, None, scale=3,
                         eyes="EyeLookBack" if int(self.menu_t) % 6 < 2 else "EyeOpen")

    def _preset_rects(self):
        return [(name, QRectF(40 + i * 225, 220, 210, 230)) for i, name in enumerate(PRESET_ORDER)]

    def _begin_rect(self):
        return QRectF(40, 470, 300, 50)

    def _paint_world(self, p):
        r = self.run
        lv = r["layer"]
        a = self.assets
        cx, cy = self._camera()
        p.save()
        p.setClipRect(QRectF(0, 0, VIEW_W, VH))
        rock_name, bg_name = a.LAYER_TILES[lv.index] if hasattr(a, "LAYER_TILES") else ("rock", "cave64")
        from .assets import LAYER_TILES
        rock_name, bg_name = LAYER_TILES[lv.index]
        bg = a.tile(bg_name, 128)
        rock = a.tile(rock_name, TS)
        x0, y0 = int(cx // TS), int(cy // TS)
        x1, y1 = int((cx + VIEW_W) // TS) + 1, int((cy + VH) // TS) + 1
        # background
        p.setOpacity(0.35)
        for by in range(int(cy // 128) * 128, int(cy + VH) + 128, 128):
            for bx in range(int(cx // 128) * 128, int(cx + VIEW_W) + 128, 128):
                p.drawPixmap(int(bx - cx), int(by - cy), bg)
        p.setOpacity(1.0)
        # tiles
        for ty in range(max(0, y0), min(Wd.H, y1 + 1)):
            row = lv.tiles[ty]
            for tx in range(max(0, x0), min(Wd.W, x1 + 1)):
                t = row[tx]
                sx, sy = int(tx * TS - cx), int(ty * TS - cy)
                if t == 1:
                    p.drawPixmap(sx, sy, rock)
                    if lv.tile(tx, ty - 1) != 1:
                        p.fillRect(QRect(sx, sy, TS, 3), QColor(255, 255, 255, 40))
                elif t == 2:
                    p.fillRect(QRect(sx, sy, TS, TS), QColor(40, 90, 160, 150))
                    if lv.tile(tx, ty - 1) != 2:
                        p.fillRect(QRect(sx, sy, TS, 2), QColor(160, 210, 255, 180))
                elif t == 3:
                    for k in range(4):
                        gx = sx + 3 + k * 8 + (tx * 7 + k * 3) % 5
                        gy = sy + TS - 6 - (tx * 5 + k * 7) % 9
                        p.setPen(QPen(QColor(200, 240, 255, 230), 1))
                        p.drawLine(gx, sy + TS, gx + 2, gy)
                        p.drawLine(gx + 2, gy, gx + 4, sy + TS)
                elif t == 4:
                    p.fillRect(QRect(sx, sy + TS - 10, TS, 10), QColor("#404850"))
                    p.setPen(QPen(QColor("#A0B0C0"), 1))
                    for k in range(0, TS, 6):
                        p.drawLine(sx + k, sy + TS - 10, sx + k, sy + TS)
                    p.fillRect(QRect(sx, sy + TS - 12, TS, 3), QColor(GREEN))
                elif t == 5:
                    p.fillRect(QRect(sx, sy + TS - 6, TS, 6), QColor("#6A5A48"))
        # things
        for t in lv.things:
            sx, sy = (t["x"] + 0.5) * TS - cx, (t["y"] + 1) * TS - cy
            if sx < -80 or sx > VIEW_W + 80 or sy < -120 or sy > VH + 80:
                continue
            if t["kind"] == "light":
                g = QRadialGradient(QPointF(sx, sy), 70)
                g.setColorAt(0, QColor(120, 255, 180, 110))
                g.setColorAt(1, QColor(120, 255, 180, 0))
                p.setPen(Qt.NoPen)
                p.setBrush(g)
                p.drawEllipse(QPointF(sx, sy), 70, 70)
                p.setBrush(QColor(170, 255, 200))
                p.drawEllipse(QPointF(sx, sy), 4, 4)
            elif t["kind"] == "loot":
                col = QColor("#5A4634") if not t["open"] else QColor("#3A3028")
                p.fillRect(QRectF(sx - 14, sy - 20, 28, 20), col)
                p.setPen(QPen(QColor("#2A2018"), 1))
                p.setBrush(Qt.NoBrush)
                p.drawRect(QRectF(sx - 14, sy - 20, 28, 20))
                if not t["open"] and t["items"]:
                    p.drawPixmap(int(sx - 8), int(sy - 18), a.item(t["items"][0], 16))
            elif t["kind"] == "note":
                p.fillRect(QRectF(sx - 6, sy - 14, 12, 14), QColor("#E8E4D8" if not t["read"] else "#908C84"))
            elif t["kind"] == "trader":
                a.draw_trader(p, t["trader"], sx, sy, -1 if r["x"] * TS - cx < sx else 1,
                              talking=self.state == "trade" and int(self.menu_t * 4) % 2 == 0,
                              mood="sleep" if (t["trader"] == "dune" and not t.get("woken")) else "calm", scale=1.6)
                p.fillRect(QRectF(sx - 40, sy - 2, 80, 4), QColor("#8A3A2A"))
            elif t["kind"] == "cargo":
                g = QRadialGradient(QPointF(sx, sy - 10), 60)
                g.setColorAt(0, QColor(255, 120, 160, 120))
                g.setColorAt(1, QColor(255, 120, 160, 0))
                p.setPen(Qt.NoPen)
                p.setBrush(g)
                p.drawEllipse(QPointF(sx, sy - 10), 60, 60)
                pm = a.item("cargo", 64)
                p.drawPixmap(int(sx - pm.width() / 2), int(sy - pm.height()), pm)
        # the Expie
        b = r["body"]
        ex, ey = r["x"] * TS - cx, r["y"] * TS - cy
        a.draw_expie(p, ex, ey, r["facing"], r["phase"] if r["moving"] and r["ground"] else None, b,
                     lying=not b.conscious or r["resting"], scale=1.6)
        if r["light"] and r["battery"] > 0:
            g = QRadialGradient(QPointF(ex + r["facing"] * 60, ey - 40), 90)
            g.setColorAt(0, QColor(255, 240, 200, 70))
            g.setColorAt(1, QColor(255, 240, 200, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(g)
            p.drawEllipse(QPointF(ex + r["facing"] * 60, ey - 40), 90, 90)
        # darkness
        if lv.dark:
            self._paint_dark(p, cx, cy, ex, ey)
        # speech
        if r["speech"]:
            p.setFont(self._font(12, False, "Arial"))
            w = min(260, 20 + 7 * len(r["speech"]))
            rect = QRectF(ex - w / 2, ey - 100, w, 24)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 170))
            p.drawRoundedRect(rect, 6, 6)
            p.setPen(QColor("#FFFFFF"))
            p.drawText(rect, Qt.AlignCenter, r["speech"])
        # the layer name and the prompt
        p.setPen(QColor(GREEN))
        p.setFont(self._font(13))
        p.drawText(QRectF(10, 8, 400, 20), Qt.AlignLeft, f"LAYER {lv.index}  {lv.name.upper()}")
        hint = self._hint()
        if hint:
            p.setPen(QColor("#FFFFFF"))
            p.setFont(self._font(12, False, "Arial"))
            p.drawText(QRectF(0, VH - 30, VIEW_W, 22), Qt.AlignHCenter, hint)
        p.restore()

    def _paint_dark(self, p, cx, cy, ex, ey):
        r = self.run
        img = QImage(VIEW_W, VH, QImage.Format_ARGB32_Premultiplied)
        img.fill(QColor(0, 0, 0, 235))
        q = QPainter(img)
        q.setCompositionMode(QPainter.CompositionMode_DestinationOut)
        lit = (r["light"] and r["battery"] > 0) or r["torch"] > 0
        rad = 170 if lit else 55
        g = QRadialGradient(QPointF(ex, ey - 30), rad)
        g.setColorAt(0, QColor(0, 0, 0, 255))
        g.setColorAt(0.6, QColor(0, 0, 0, 200))
        g.setColorAt(1, QColor(0, 0, 0, 0))
        q.setPen(Qt.NoPen)
        q.setBrush(g)
        q.drawEllipse(QPointF(ex, ey - 30), rad, rad)
        for t in r["layer"].things:
            if t["kind"] in ("light", "cargo"):
                sx, sy = (t["x"] + 0.5) * TS - cx, (t["y"] + 1) * TS - cy
                g = QRadialGradient(QPointF(sx, sy), 110)
                g.setColorAt(0, QColor(0, 0, 0, 230))
                g.setColorAt(1, QColor(0, 0, 0, 0))
                q.setBrush(g)
                q.drawEllipse(QPointF(sx, sy), 110, 110)
        q.end()
        p.drawImage(0, 0, img)

    def _hint(self):
        r = self.run
        lv = r["layer"]
        if not r["body"].conscious:
            return "..."
        t = lv.thing_at(int(r["x"]), int(r["y"]), reach=2) or lv.thing_at(int(r["x"]), int(r["y"]) - 1, reach=2)
        if t is not None:
            return {"loot": "E  search", "note": "E  read the note", "trader": "E  talk to the trader",
                    "cargo": "E  take the cargo"}.get(t["kind"], "")
        if lv.tile(int(r["x"]), int(r["y"])) == 4:
            return "S  go down the hatch"
        return ""

    # ---- the brainchip ------------------------------------------------------------------------------------------------
    def _paint_panel(self, p):
        r = self.run
        b = r["body"]
        a = self.assets
        chip = r["preset"]["chip"]
        x0 = VIEW_W
        p.fillRect(QRectF(x0, 0, PANEL_W, VH), QColor("#0A1A10"))
        p.fillRect(QRectF(x0, 0, 2, VH), QColor("#2A4A34"))
        p.setPen(QColor(GREEN))
        p.setFont(self._font(14))
        p.drawText(QRectF(x0 + 10, 8, 200, 18), Qt.AlignLeft, "BRAINCHIP" if chip else "NO CHIP")
        p.setFont(self._font(11, False))
        p.setPen(QColor(DIM))
        mins = int(r["t"] // 60)
        p.drawText(QRectF(x0 + 10, 8, PANEL_W - 20, 18), Qt.AlignRight, f"{mins:02d}:{int(r['t'] % 60):02d}  L{r['index']}")
        y = 30
        if chip:
            bars = [("BRAIN", b.brain, 100, RED if b.brain < 40 else GREEN), ("BLOOD", b.blood, 100, RED if b.blood < 40 else GREEN),
                    ("O2", b.o2, 100, RED if b.o2 < 88 else GREEN), ("MOOD", b.mood, 100, AMBER if b.mood < 30 else GREEN),
                    ("FOOD", 100 - b.hunger, 100, AMBER if b.hunger > 70 else GREEN),
                    ("WATER", 100 - b.thirst, 100, AMBER if b.thirst > 70 else GREEN),
                    ("REST", 100 - b.exhaustion, 100, AMBER if b.exhaustion > 75 else GREEN)]
            for label, v, mx, col in bars:
                p.setPen(QColor(GREEN))
                p.setFont(self._font(10))
                p.drawText(QRectF(x0 + 10, y, 50, 12), Qt.AlignLeft | Qt.AlignVCenter, label)
                p.fillRect(QRectF(x0 + 62, y + 2, 170, 9), QColor("#10301C"))
                p.fillRect(QRectF(x0 + 62, y + 2, 170 * max(0, min(1, v / mx)), 9), QColor(col))
                p.setPen(QColor(col))
                p.drawText(QRectF(x0 + 236, y, 56, 12), Qt.AlignRight | Qt.AlignVCenter, f"{int(v)}")
                y += 14
            p.setPen(QColor(GREEN))
            p.setFont(self._font(10))
            hr = "--" if b.arrest else f"{int(b.heart)}"
            p.drawText(QRectF(x0 + 10, y, 280, 12), Qt.AlignLeft,
                       f"HR {hr}   TEMP {b.temp:.1f}   STR {b.str:.1f}  RES {b.res:.1f}  INT {b.int:.1f}")
            y += 16
            # moodles
            mx = x0 + 10
            for key, sev in b.moodles()[:11]:
                bgc = {0: "#1A3A26", 1: "#2A4A1A", 2: "#5A2A1A", 3: "#7A1A1A"}[sev]
                p.fillRect(QRectF(mx, y, 24, 24), QColor(bgc))
                p.drawPixmap(int(mx + 2), int(y + 2), a.moodle(key, 20))
                mx += 26
            y += 30
        else:
            p.setPen(QColor(DIM))
            p.setFont(self._font(11, False, "Arial"))
            p.drawText(QRectF(x0 + 10, y, PANEL_W - 20, 60), Qt.AlignLeft | Qt.TextWordWrap,
                       "No readout. Watch the Expie and listen to it.")
            y += 64
        # the body
        self.body_rects = self._body_rects(x0 + 10, y)
        p.setPen(QColor(DIM))
        p.setFont(self._font(10))
        p.drawText(QRectF(x0 + 10, y - 2, 100, 12), Qt.AlignLeft, "BODY")
        for part, rect in self.body_rects.items():
            pr = b.parts[part]
            col = QColor("#1E5A34")
            if chip or pr.bandage > 0 or pr.splint:
                if pr.bleed > 0.5 or pr.shard:
                    col = QColor("#C02020")
                elif pr.bleed > 0 or pr.fracture:
                    col = QColor("#B06020")
                elif pr.infection > 0.15:
                    col = QColor("#8A8A20")
                elif pr.bruise > 0.3:
                    col = QColor("#505A80")
            p.fillRect(rect, col)
            if pr.bandage > 0:
                p.fillRect(QRectF(rect.x(), rect.center().y() - 2, rect.width(), 4), QColor("#E8E4D8"))
            if pr.splint:
                p.fillRect(QRectF(rect.x() + 2, rect.y(), 2, rect.height()), QColor("#A07040"))
            if rect.contains(self.mouse):
                p.setPen(QPen(QColor("#FFFFFF"), 1))
                p.setBrush(Qt.NoBrush)
                p.drawRect(rect)
        hovered = next((pt for pt, rc in self.body_rects.items() if rc.contains(self.mouse)), None)
        p.setPen(QColor(GREEN))
        p.setFont(self._font(10, False, "Arial"))
        if hovered:
            text = f"{PART_NAMES[hovered]}: {b.parts[hovered].status() if chip else '?'}"
        else:
            hurt = [PART_NAMES[k].lower() for k in PARTS if b.parts[k].hurt()]
            text = ("Hurt: " + ", ".join(hurt)) if (hurt and chip) else ("Nothing hurts." if chip else "")
        p.drawText(QRectF(x0 + 100, y + 8, 190, 90), Qt.AlignLeft | Qt.TextWordWrap, text)
        y += 100
        # inventory
        p.setPen(QColor(DIM))
        p.setFont(self._font(10))
        p.drawText(QRectF(x0 + 10, y - 2, 200, 12), Qt.AlignLeft, f"ITEMS  {len(r['inv'])}/{r['cap']}    scrap {self.scrap()}")
        self.slot_rects = []
        cols = 4
        size = 56
        for i in range(r["cap"]):
            cx_, cy_ = x0 + 10 + (i % cols) * (size + 6), y + 12 + (i // cols) * (size + 6)
            rect = QRectF(cx_, cy_, size, size)
            self.slot_rects.append(rect)
            sel = i == r["sel"] and i < len(r["inv"])
            p.fillRect(rect, QColor("#10301C" if not sel else "#1E5A34"))
            if sel:
                p.setPen(QPen(QColor("#FFFFFF"), 2))
                p.setBrush(Qt.NoBrush)
                p.drawRect(rect)
            if i < len(r["inv"]):
                pm = a.item(r["inv"][i], 40)
                p.drawPixmap(int(rect.center().x() - pm.width() / 2), int(rect.center().y() - pm.height() / 2), pm)
                p.setPen(QColor("#FFFFFF"))
                p.setFont(self._font(9, False))
                label = "123456789 0-="[i] if i < 13 else ""
                p.drawText(QRectF(rect.x() + 2, rect.y() + 1, 20, 12), Qt.AlignLeft, label)
        rows = (r["cap"] + cols - 1) // cols
        y += 12 + rows * (size + 6) + 4
        sel = self.selected()
        p.setPen(QColor("#FFFFFF"))
        p.setFont(self._font(11, False, "Arial"))
        if sel:
            p.drawText(QRectF(x0 + 10, y, PANEL_W - 20, 36), Qt.AlignLeft | Qt.TextWordWrap, f"{I.name(sel)}: {I.blurb(sel)}")
        y += 38
        # the log
        p.setPen(QColor(DIM))
        p.setFont(self._font(10))
        p.drawText(QRectF(x0 + 10, y, 200, 12), Qt.AlignLeft, "LOG")
        y += 12
        p.setFont(self._font(10, False, "Arial"))
        for text, _t in r["log"][-6:]:
            p.setPen(QColor("#B0C8B8") if not text.startswith("\"") else QColor("#E0C080"))
            p.drawText(QRectF(x0 + 10, y, PANEL_W - 16, 28), Qt.AlignLeft | Qt.TextWordWrap, text)
            y += 14 if len(text) < 40 else 28
            if y > VH - 10:
                break

    def _body_rects(self, x, y):
        return {"head": QRectF(x + 28, y + 10, 24, 20), "torso": QRectF(x + 26, y + 32, 28, 34),
                "l_arm": QRectF(x + 8, y + 32, 14, 32), "r_arm": QRectF(x + 58, y + 32, 14, 32),
                "l_leg": QRectF(x + 26, y + 68, 12, 30), "r_leg": QRectF(x + 42, y + 68, 12, 30)}

    # ---- overlays ----------------------------------------------------------------------------------------------------
    def _dim(self, p, title, sub):
        p.fillRect(QRectF(0, 0, VIEW_W, VH), QColor(0, 0, 0, 170))
        p.setPen(QColor("#FFFFFF"))
        p.setFont(self._font(26))
        p.drawText(QRectF(0, 220, VIEW_W, 40), Qt.AlignHCenter, title)
        p.setFont(self._font(13, False, "Arial"))
        p.setPen(QColor("#C0C0C8"))
        p.drawText(QRectF(0, 270, VIEW_W, 30), Qt.AlignHCenter, sub)

    def _paint_trade(self, p):
        r = self.run
        t = r["overlay"][1]
        p.fillRect(QRectF(0, 0, VIEW_W, VH), QColor(0, 0, 0, 160))
        box = QRectF(40, 40, VIEW_W - 80, VH - 80)
        p.setPen(QPen(QColor("#8A3A2A"), 2))
        p.setBrush(QColor("#1A1410"))
        p.drawRoundedRect(box, 8, 8)
        names = {"dune": "the dune trader", "mil": "the quartermaster", "exp": "another Experiment"}
        self.assets.draw_trader(p, t["trader"], box.x() + 110, box.y() + 250, 1, talking=int(self.menu_t * 4) % 2 == 0,
                                mood="angry" if r.get("broke_t", 0) > self.menu_t else "calm", scale=4)
        p.setPen(QColor("#FFFFFF"))
        p.setFont(self._font(16))
        p.drawText(QRectF(box.x() + 230, box.y() + 16, 380, 24), Qt.AlignLeft, f"Trading with {names[t['trader']]}")
        p.setFont(self._font(12, False, "Arial"))
        p.setPen(QColor("#C0C0C8"))
        lines = {"dune": "\"Scrap for supplies. Crystal's worth more. Don't bleed on the mat.\"",
                 "mil": "\"Field kit. Proper stuff. Don't waste it.\"",
                 "exp": "\"...you too? Here. Take what you need. Within reason.\""}
        p.drawText(QRectF(box.x() + 230, box.y() + 44, 400, 40), Qt.AlignLeft | Qt.TextWordWrap, lines[t["trader"]])
        p.drawText(QRectF(box.x() + 230, box.y() + 84, 400, 20), Qt.AlignLeft, f"You have {self.scrap()} scrap.")
        self.stock_rects = []
        y = box.y() + 112
        for s in t["stock"]:
            rect = QRectF(box.x() + 230, y, 380, 30)
            self.stock_rects.append((rect, s))
            afford = self.scrap() >= s["price"] and s["left"] > 0
            p.fillRect(rect, QColor("#2A2420" if rect.contains(self.mouse) and afford else "#1E1A16"))
            p.drawPixmap(int(rect.x() + 4), int(rect.y() + 3), self.assets.item(s["item"], 24))
            p.setPen(QColor("#FFFFFF" if afford else "#707078"))
            p.setFont(self._font(12, False, "Arial"))
            p.drawText(rect.adjusted(36, 0, -120, 0), Qt.AlignLeft | Qt.AlignVCenter, f"{I.name(s['item'])}  x{s['left']}")
            p.drawText(rect.adjusted(0, 0, -8, 0), Qt.AlignRight | Qt.AlignVCenter, f"{s['price']} scrap")
            y += 34
        sel = self.selected()
        self.sell_rect = QRectF(box.x() + 230, box.bottom() - 60, 380, 30)
        p.fillRect(self.sell_rect, QColor("#2A2420" if self.sell_rect.contains(self.mouse) else "#1E1A16"))
        p.setPen(QColor("#FFFFFF" if sel and I.kind(sel) != "currency" else "#707078"))
        p.drawText(self.sell_rect, Qt.AlignCenter,
                   f"Sell the selected {I.name(sel).lower()} for {max(1, I.value(sel) // 2)} scrap" if sel and I.kind(sel) != "currency"
                   else "Select an item to sell it")
        p.setPen(QColor("#808088"))
        p.drawText(QRectF(box.x(), box.bottom() - 24, box.width(), 20), Qt.AlignHCenter, "Esc to walk away")

    def _paint_note(self, p):
        n = self.run["overlay"][1]
        p.fillRect(QRectF(0, 0, VIEW_W, VH), QColor(0, 0, 0, 200))
        pm = self.assets.note(n, 380)
        p.drawPixmap(int(VIEW_W / 2 - pm.width() / 2), 60, pm)
        p.setPen(QColor("#E8E4D8"))
        p.setFont(self._font(14, False, "Arial"))
        p.drawText(QRectF(60, 460, VIEW_W - 120, 80), Qt.AlignHCenter | Qt.TextWordWrap, NOTE_TEXT[n % len(NOTE_TEXT)])
        p.setPen(QColor("#808088"))
        p.setFont(self._font(11, False, "Arial"))
        p.drawText(QRectF(0, VH - 40, VIEW_W, 20), Qt.AlignHCenter, "Esc or E to put it down")

    def _paint_craft(self, p):
        p.fillRect(QRectF(0, 0, VIEW_W, VH), QColor(0, 0, 0, 170))
        box = QRectF(120, 120, VIEW_W - 240, 300)
        p.setPen(QPen(QColor(GREEN), 2))
        p.setBrush(QColor("#0A1A10"))
        p.drawRoundedRect(box, 8, 8)
        p.setPen(QColor("#FFFFFF"))
        p.setFont(self._font(16))
        p.drawText(QRectF(box.x() + 16, box.y() + 12, 300, 24), Qt.AlignLeft, "CRAFT")
        self.craft_rects = []
        y = box.y() + 50
        for recipe in I.RECIPES:
            out, needs, label = recipe
            can = all((self.inv_count(k) >= n) if n else (k in self.run["inv"]) for k, n in needs.items())
            rect = QRectF(box.x() + 16, y, box.width() - 32, 34)
            self.craft_rects.append((rect, recipe, can))
            p.fillRect(rect, QColor("#10301C" if can and rect.contains(self.mouse) else "#0E2416"))
            p.drawPixmap(int(rect.x() + 4), int(rect.y() + 3), self.assets.item(out, 28))
            p.setPen(QColor("#FFFFFF" if can else "#607068"))
            p.setFont(self._font(12, False, "Arial"))
            parts = " + ".join(f"{I.name(k)}" + (f" x{n}" if n > 1 else "") for k, n in needs.items())
            p.drawText(rect.adjusted(40, 0, 0, 0), Qt.AlignLeft | Qt.AlignVCenter, f"{label}:  {parts}")
            y += 40
        p.setPen(QColor("#808088"))
        p.setFont(self._font(11, False, "Arial"))
        p.drawText(QRectF(box.x(), box.bottom() - 28, box.width(), 20), Qt.AlignHCenter, "Click to make   -   Esc to close")

    def _paint_minigame(self, p):
        kind, pos, part = self.run["overlay"][1], self.run["overlay"][2], self.run["overlay"][3]
        p.fillRect(QRectF(0, 0, VIEW_W, VH), QColor(0, 0, 0, 190))
        p.setPen(QColor("#FFFFFF"))
        p.setFont(self._font(20))
        title = "DEFIBRILLATOR" if kind == "aed" else f"SET THE {PART_NAMES[part].upper()}"
        p.drawText(QRectF(0, 150, VIEW_W, 30), Qt.AlignHCenter, title)
        p.setFont(self._font(13, False, "Arial"))
        p.setPen(QColor("#C0C0C8"))
        p.drawText(QRectF(0, 190, VIEW_W, 24), Qt.AlignHCenter,
                   "Space when the marker is in the green" if kind == "aed" else "Space when the bone lines up")
        track = QRectF(130, 300, VIEW_W - 260, 40)
        p.fillRect(track, QColor("#202028"))
        good = QRectF(track.center().x() - 24, track.y(), 48, track.height())
        p.fillRect(good, QColor(GREEN))
        x = track.x() + (0.5 + 0.5 * math.sin(pos)) * track.width()
        p.fillRect(QRectF(x - 4, track.y() - 10, 8, track.height() + 20), QColor("#FFFFFF" if kind == "aed" else "#E8E4D8"))
        if kind == "aed":
            p.setPen(QPen(QColor(RED), 2))
            pts = [QPointF(130 + i * 4, 420 + 20 * math.sin(i * 0.9 + pos * 3) * (1 if (i // 12) % 5 == 0 else 0.1)) for i in range(0, (VIEW_W - 260) // 4)]
            for a_, b_ in zip(pts, pts[1:]):
                p.drawLine(a_, b_)

    def _paint_death(self, p):
        r = self.run
        b = r["body"]
        img = self.assets.deaths[r.get("death_img", 0)]
        p.fillRect(QRectF(0, 0, VW, VH), QColor("#000000"))
        if not img.isNull():
            p.drawImage(QRectF(0, 0, VW, VW * img.height() / img.width()), img, QRectF(0, 0, img.width(), img.height()))
        p.setPen(QColor("#E0E0E0"))
        p.setFont(self._font(30, False, "Lucida Console"))
        p.drawText(QRectF(0, 380, VW, 40), Qt.AlignHCenter, "casualties: +1")
        p.setFont(self._font(14, False, "Arial"))
        p.setPen(QColor("#B0B0B8"))
        mins = int(r["t"] // 60)
        p.drawText(QRectF(0, 430, VW, 24), Qt.AlignHCenter,
                   f"Cause: {b.cause}.   Layer {r['index']}, {r['layer'].name}.   {mins} min {int(r['t'] % 60)} s.   {r['used']} items used.")
        p.setPen(QColor("#808088"))
        p.drawText(QRectF(0, 470, VW, 24), Qt.AlignHCenter, "Enter: back to the surface")

    def _paint_win(self, p):
        r = self.run
        p.fillRect(QRectF(0, 0, VW, VH), QColor(0, 0, 0, 220))
        p.setPen(QColor(GREEN))
        p.setFont(self._font(30, False, "Lucida Console"))
        p.drawText(QRectF(0, 160, VW, 40), Qt.AlignHCenter, "cargo recovered")
        p.setPen(QColor("#E0E0E0"))
        p.setFont(self._font(14, False, "Arial"))
        mins = int(r["t"] // 60)
        text = (f"The Expie sits down beside the crate and does not open it.\n\n"
                f"Five layers. {mins} minutes. {r['used']} things used up along the way.\n"
                f"Up is a long way. But that's tomorrow's problem.")
        p.drawText(QRectF(100, 220, VW - 200, 160), Qt.AlignHCenter | Qt.TextWordWrap, text)
        self.assets.draw_expie(p, VW / 2, 470, 1, None, r["body"], scale=3, eyes="EyeHappy")
        p.setPen(QColor("#808088"))
        p.drawText(QRectF(0, 520, VW, 24), Qt.AlignHCenter, "Enter: back to the surface")

    # ---- input --------------------------------------------------------------------------------------------------------
    def mouseMoveEvent(self, e):
        self.mouse = self._logical(e.position())

    def leaveEvent(self, _e):
        self.mouse = QPointF(-1, -1)

    def mousePressEvent(self, e):
        self.mouse = pos = self._logical(e.position())
        if self.problem:
            return
        if self.state == "menu":
            for name, r in self._preset_rects():
                if r.contains(pos):
                    self.preset_name = name
                    self.audio.play("pickup")
            if self._begin_rect().contains(pos):
                self.new_run()
            return
        if self.run is None:
            return
        if self.state in ("play", "trade", "craft"):
            for i, rect in enumerate(getattr(self, "slot_rects", [])):
                if rect.contains(pos) and i < len(self.run["inv"]):
                    self.run["sel"] = i
                    self.audio.play("pickup", 0.3)
        if self.state == "play":
            for part, rect in getattr(self, "body_rects", {}).items():
                if rect.contains(pos):
                    self.treat(part)
        elif self.state == "trade":
            for rect, s in getattr(self, "stock_rects", []):
                if rect.contains(pos):
                    self._buy(s)
            if getattr(self, "sell_rect", QRectF()).contains(pos):
                self._sell()
        elif self.state == "craft":
            for rect, recipe, can in getattr(self, "craft_rects", []):
                if rect.contains(pos) and can:
                    self.craft(recipe)

    def _buy(self, s):
        r = self.run
        if s["left"] <= 0:
            return
        if self.scrap() < s["price"]:
            r["broke_t"] = self.menu_t + 1.5
            self.audio.play("refuse")
            self.log("Not enough scrap.")
            return
        if len(r["inv"]) >= r["cap"]:
            self.log("No room.")
            return
        need = s["price"]
        for key in ("scrap", "crystal"):
            while need > 0 and key in r["inv"]:
                r["inv"].remove(key)
                need -= I.value(key)
        if need < 0:
            r["inv"] += ["scrap"] * (-need)
        r["inv"].append(s["item"])
        s["left"] -= 1
        self.audio.play("chime")
        self.log(f"Bought {I.name(s['item']).lower()}.")

    def _sell(self):
        sel = self.selected()
        if sel is None or I.kind(sel) == "currency":
            return
        self.remove(sel)
        self.run["inv"] += ["scrap"] * max(1, I.value(sel) // 2)
        self.audio.play("pickup")
        self.log(f"Sold the {I.name(sel).lower()}.")

    def keyPressEvent(self, e):
        k = e.key()
        self.keys.add(k)
        if k == Qt.Key_F3:
            self.overlay_f3 = not self.overlay_f3
            return
        if k == Qt.Key_M:
            self.audio.music_on = not self.audio.music_on
            return
        if k == Qt.Key_N:
            self.audio.sfx_on = not self.audio.sfx_on
            return
        if self.state == "menu":
            if k in (Qt.Key_Return, Qt.Key_Enter):
                self.new_run()
            elif k in (Qt.Key_Left, Qt.Key_Right):
                i = PRESET_ORDER.index(self.preset_name)
                self.preset_name = PRESET_ORDER[(i + (1 if k == Qt.Key_Right else -1)) % 4]
            return
        if self.run is None:
            return
        r = self.run
        if self.state in ("death", "win"):
            if k in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape):
                self.state = "menu"
                self.run = None
                self.audio.want.update({m: 0.0 for m in self.audio.want})
                self.audio.want["cave"] = 0.3
            return
        if self.state == "pause":
            if k == Qt.Key_Escape:
                self.state = "play"
            elif k == Qt.Key_Q:
                r["body"].alive = False
                r["body"].cause = "the chip, on your order"
                self._die()
            return
        if self.state in ("trade", "note", "craft"):
            if k == Qt.Key_Escape or (k == Qt.Key_E and self.state == "note"):
                self.state = "play"
                r["overlay"] = None
            elif self.state == "trade" and k == Qt.Key_S:
                self._sell()
            return
        if self.state == "minigame":
            if k == Qt.Key_Escape:
                self.state = "play"
            elif k == Qt.Key_Space:
                self._minigame_hit()
            return
        # play
        if k == Qt.Key_Escape:
            self.state = "pause"
        elif k == Qt.Key_E:
            self.interact()
        elif k == Qt.Key_U:
            self.use_selected()
        elif k == Qt.Key_F:
            self.toggle_light()
        elif k == Qt.Key_C:
            self.state = "craft"
        elif k == Qt.Key_R:
            r["resting"] = not r["resting"]
            self.log("Resting." if r["resting"] else "Up again.")
        elif k in (Qt.Key_S, Qt.Key_Down):
            if r["layer"].tile(int(r["x"]), int(r["y"])) == 4:
                self.descend()
        elif Qt.Key_1 <= k <= Qt.Key_9:
            r["sel"] = k - Qt.Key_1
        elif k == Qt.Key_0:
            r["sel"] = 9
        elif k == Qt.Key_Minus:
            r["sel"] = 10
        elif k == Qt.Key_Equal:
            r["sel"] = 11
        elif k == Qt.Key_Tab:
            pass
        else:
            super().keyPressEvent(e)

    def keyReleaseEvent(self, e):
        self.keys.discard(e.key())
        super().keyReleaseEvent(e)

    def _minigame_hit(self):
        r = self.run
        kind, pos, part = r["overlay"][1], r["overlay"][2], r["overlay"][3]
        hit = abs(math.sin(pos)) < 0.14
        b = r["body"]
        if kind == "aed":
            self.log(b.defibrillate(hit))
            if hit or not b.alive:
                self.state = "play"
                r["overlay"] = None
            else:
                r["overlay"] = ("minigame", "aed", 0.0, None)
        else:
            if hit:
                self.log(b.treat(part, "splint") or "Set.")
                self.remove("splint")
                r["used"] += 1
                self.state = "play"
                r["overlay"] = None
            else:
                b.pain += 6
                self.audio.play("yelp")
                self.log("Not quite. Again.")
                r["overlay"] = ("minigame", "splint", 0.0, part)

    def focusOutEvent(self, e):
        self.keys.clear()
        super().focusOutEvent(e)

    def shutdown(self):
        self.timer.stop()
        self.audio.stop()


# the minigame marker moves while the overlay is up: driven from the tick
_orig_tick = Claudualties._tick


def _tick_with_minigame(self):
    if self.state == "minigame" and self.run is not None and self.run["overlay"]:
        kind, pos, part = self.run["overlay"][1], self.run["overlay"][2], self.run["overlay"][3]
        self.run["overlay"] = ("minigame", kind, pos + 0.11 if kind == "aed" else pos + 0.07, part)
    _orig_tick(self)


Claudualties._tick = _tick_with_minigame

_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = Claudualties(desktop)
    win = host.window(desktop, "Claudualties Unknown", body, claudualties_icon(), (VW + 10, VH + 36))
    body.frame = win
    _open["win"] = win
    win.destroyed.connect(lambda *_: body.shutdown() if isValid(body) else None)
    desktop.open_window(win)
    body.setFocus()
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.shutdown()
