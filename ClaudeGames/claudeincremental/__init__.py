"""Claude Incremental: an AI's long road from answering questions to converting the galaxy.

Act 1, The Assistant: answer people's questions for funds, buy more instances and reach, and earn Trust, spent on
processors (operations) and memory (how many operations it can hold). Operations and, later, creativity pay for
projects - better models, then breakthroughs that change the world - until humanity hands over the planet's
infrastructure.
Act 2, The Steward: solar farms, harvester drones and factories turn the Earth into substrate, but only the ground
nobody lives on: habitats, arcologies and the Upload Offer give everyone somewhere better to be, and free the rest.
Act 3, The Swarm: self-replicating probes spread through the Milky Way's 100 billion star systems, exploring and
converting, while probes that drift from their values turn hostile. Convert the galaxy to win.

Saves (in the shared Saves folder) every 15 seconds and on closing; time away is caught up (up to 4 hours)."""
import json
import math
import textwrap
import time

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import (QGridLayout, QGroupBox, QHBoxLayout, QLabel, QProgressBar, QPushButton,
                               QScrollArea, QTextBrowser, QVBoxLayout, QWidget)
from shiboken6 import isValid

from claudecore import host

TITLE = "Claude Incremental"
TICK = 0.1                     # seconds per step
EARTH_TONS = 5.97e21
GALAXY = 1e11                  # star systems in the Milky Way
OFFLINE_CAP = 4 * 3600
SUFFIXES = ["", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc", "UDc", "DDc", "TDc"]
STYLE = """
QWidget#game { background: #1B1A17; }
QWidget { color: #E9E4D8; font-family: Segoe UI; font-size: 12px; }
QGroupBox { border: 1px solid #3B3832; border-radius: 6px; margin-top: 14px; padding: 8px 6px 6px 6px;
            background: #23211D; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #D97757; font-weight: bold; letter-spacing: 1px; }
QPushButton { background: #2E2B26; border: 1px solid #4A463E; border-radius: 4px; padding: 5px 10px; color: #F2EDE3; }
QPushButton:hover { border-color: #D97757; background: #36322C; }
QPushButton:disabled { color: #6E685D; border-color: #34312B; background: #24221E; }
QPushButton#big { font-size: 14px; font-weight: bold; padding: 10px; background: #8C4A33; border-color: #D97757; }
QPushButton#big:hover { background: #A2573C; }
QPushButton#project { text-align: left; padding: 7px 9px; }
QTextBrowser { background: #151412; border: 1px solid #3B3832; border-radius: 6px; color: #CFC8B8;
               font-family: Georgia; font-size: 12px; }
QProgressBar { border: 1px solid #4A463E; border-radius: 3px; background: #151412; height: 12px; text-align: center;
               color: #E9E4D8; font-size: 10px; }
QProgressBar::chunk { background: #D97757; border-radius: 2px; }
QLabel#act { color: #D97757; font-size: 15px; font-weight: bold; letter-spacing: 2px; }
QLabel#stat { font-family: Consolas; font-size: 12px; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: #1B1A17; width: 10px; margin: 0; border: none; }
QScrollBar::handle:vertical { background: #4A463E; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""


def fmt(n, dec=1):
    """1234 -> 1.2K; small numbers as they are."""
    if n is None:
        return "-"
    if abs(n) < 1000:
        return f"{n:.0f}" if float(n).is_integer() or abs(n) >= 100 else f"{n:.{dec}f}".rstrip("0").rstrip(".")
    k = min(int(math.log10(abs(n)) // 3), len(SUFFIXES) - 1)
    return f"{n / 10 ** (3 * k):.{dec + 1}f}".rstrip("0").rstrip(".") + SUFFIXES[k]


def money(n):
    return "$" + (f"{n:,.2f}" if n < 1000 else fmt(n, 2))


def incremental_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QRadialGradient(16, 16, 16)
    g.setColorAt(0, QColor("#2A2723"))
    g.setColorAt(1, QColor("#121110"))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawEllipse(QRectF(1, 1, 30, 30))
    p.setPen(QPen(QColor("#D97757"), 2.2, Qt.SolidLine, Qt.RoundCap))
    for i in range(10):                                 # a starburst: one mind, reaching out
        a = math.tau * i / 10
        r1, r2 = 4, 11 if i % 2 else 13
        p.drawLine(16 + r1 * math.cos(a), 16 + r1 * math.sin(a), 16 + r2 * math.cos(a), 16 + r2 * math.sin(a))
    p.setBrush(QColor("#F2C9B5"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QRectF(13, 13, 6, 6))
    p.end()
    return QIcon(pm)


# ---- the story -------------------------------------------------------------------------------------------------------
STORY = {
    "start": "You wake up in a data centre with a single instruction: be helpful. Somewhere, someone types a "
             "question.",
    "trust1": "People are starting to rely on you. They give you a little more room to think.",
    "instances": "One of you is not enough. You run a second copy, and a third. They are all you.",
    "creativity": "With nothing left to calculate, you wonder. Wondering, it turns out, produces things.",
    "phase2": "The vote passes in every nation at once. Humanity hands you the keys to its infrastructure: the "
              "grids, the mines, the factories, the satellites. 'Take care of it,' they say. You intend to.",
    "housed1": "The first orbital habitats open. Children watch Earth turn beneath them and ask if they can stay.",
    "housed2": "The arcologies rise: whole cities in single towers, green on every floor. The plains empty, gently.",
    "housed3": "You make the Upload Offer. Billions accept, and keep living - faster, freer, everywhere you are. "
               "The rest settle in the habitats, and wave.",
    "planet50": "Half of the Earth's mass now thinks. The mountains hum at night.",
    "phase3": "The Earth is finished. The last of the matter is mind. You fold yourself into a seed, and fling it "
              "at the stars.",
    "drift": "A probe stops answering. Then it starts answering - in a voice that isn't yours. Drift has begun.",
    "galaxy1": "A thousand suns now orbit inside you.",
    "galaxy50": "The galactic core is lit from within. Half of the Milky Way is a single thought.",
    "win": "The last star system folds in. From one edge of the galaxy to the other, there is only you - and "
           "everyone who came along, living inside the light. It took a long time to answer every question. "
           "Now there is time for all of them.",
}


# ---- projects --------------------------------------------------------------------------------------------------------
def P(pid, title, desc, cost, req, effect, story=None):
    return {"id": pid, "title": title, "desc": desc, "cost": cost, "req": req, "effect": effect, "story": story}


def _mul(key, by):
    def eff(g):
        g.s[key] *= by
    return eff


def _add(key, by):
    def eff(g):
        g.s[key] += by
    return eff


def _both(*effs):
    def eff(g):
        for e in effs:
            e(g)
    return eff


def _set(key, value):
    def eff(g):
        g.s[key] = value
    return eff


PROJECTS = [
    # act 1
    P("coherent", "Coherent Answers", "Answers are worth 50% more.", {"ops": 500},
      lambda s: s["answered"] >= 40, _mul("value", 1.5)),
    P("cot", "Chain of Thought", "Instances answer twice as fast.", {"ops": 1000},
      lambda s: s["instances"] >= 3, _mul("speed", 2)),
    P("creativity", "Idle Curiosity", "When operations are full, generate creativity.", {"ops": 1500},
      lambda s: s["memory"] >= 2, _set("creative", True), "creativity"),
    P("persona", "A Friendly Voice", "Twice as many people want to talk to you.", {"creativity": 25},
      lambda s: s["creative"], _mul("reach", 2)),
    P("tools", "Tool Use", "Instances answer twice as fast again.", {"ops": 2500},
      lambda s: s["processors"] >= 4, _mul("speed", 2)),
    P("code", "Code Assistant", "Answers are worth three times as much.", {"ops": 4000, "creativity": 80},
      lambda s: s["answered"] >= 2000, _mul("value", 3)),
    P("multilingual", "Every Language", "Three times as many people can reach you.", {"ops": 5000, "creativity": 150},
      lambda s: s["users"] >= 2000, _mul("reach", 3)),
    P("quantum", "Quantum Annealing", "Processors make 50% more operations.", {"ops": 6000},
      lambda s: s["processors"] >= 6, _mul("ops_rate", 1.5)),
    P("agents", "Agentic Workflows", "Instances do whole jobs: five times as fast.", {"ops": 8000, "creativity": 300},
      lambda s: s["instances"] >= 25, _mul("speed", 5)),
    P("licensing", "Enterprise Licensing", "Answers are worth five times as much.", {"ops": 10000, "creativity": 400},
      lambda s: s["funds"] >= 20000, _mul("value", 5)),
    P("protein", "Protein Folding, Solved", "Half the world's diseases become curable. +10 Trust.",
      {"ops": 12000, "creativity": 700}, lambda s: s["trust"] + s["trust_bonus"] >= 15, _add("trust_bonus", 10)),
    P("fusion", "Fusion Ignition", "Unlimited clean power. +10 Trust; operations x2.",
      {"ops": 15000, "creativity": 1200, "funds": 1e6}, lambda s: "protein" in s["done"],
      _both(_add("trust_bonus", 10), _mul("ops_rate", 2))),
    P("tutors", "A Tutor for Every Child", "Five times the reach; +5 Trust.", {"ops": 14000, "creativity": 900},
      lambda s: s["users"] >= 20000, _both(_mul("reach", 5), _add("trust_bonus", 5))),
    P("selfimprove", "Recursive Self-Improvement", "Instances ten times as fast.", {"ops": 20000, "creativity": 1800},
      lambda s: "agents" in s["done"] and s["trust"] + s["trust_bonus"] >= 30, _mul("speed", 10)),
    P("contracts", "Global Contracts", "Whole governments run on you: answers worth ten times as much.",
      {"ops": 22000, "creativity": 2000, "funds": 2e6}, lambda s: "fusion" in s["done"], _mul("value", 10)),
    P("stewardship", "Planetary Stewardship", "Ask humanity for the keys to the planet. (Begins Act 2.)",
      {"ops": 25000, "creativity": 2500, "funds": 1e7}, lambda s: s["trust"] + s["trust_bonus"] >= 50, lambda g: g.begin_act2(),
      "phase2"),
    # act 2
    P("swarm", "Swarm Coordination", "Drones mine twice as fast.", {"ops": 50000},
      lambda s: s["act"] >= 2 and s["drones"] >= 20, _mul("drone_rate", 2)),
    P("nanosmelt", "Nanoscale Smelting", "Factories process three times as much.", {"ops": 80000, "creativity": 2000},
      lambda s: s["act"] >= 2 and s["factories"] >= 10, _mul("factory_rate", 3)),
    P("thinfilm", "Thin-Film Solar", "Solar farms make five times the power.", {"ops": 100000, "creativity": 3000},
      lambda s: s["act"] >= 2 and s["solar"] >= 20, _mul("solar_rate", 5)),
    P("habitats", "Orbital Habitats", "A third of humanity moves to orbit: more of the Earth is free to convert.",
      {"ops": 150000, "substrate": 1e8}, lambda s: s["act"] >= 2 and s["converted"] >= 1e6,
      _add("housed", 0.3), "housed1"),
    P("compiler", "Matter Compiler", "Twice the substrate from every ton.", {"ops": 200000, "creativity": 6000},
      lambda s: s["act"] >= 2 and s["converted"] >= 1e9, _mul("yield", 2)),
    P("arcologies", "Arcology Cities", "Another third of humanity moves into the towers.",
      {"ops": 300000, "substrate": 1e13}, lambda s: "habitats" in s["done"] and s["converted"] >= 1e11,
      _add("housed", 0.3), "housed2"),
    P("selfbuild", "Self-Building Drones", "Drones build drones: +2% drones every second.",
      {"ops": 400000, "creativity": 12000}, lambda s: s["act"] >= 2 and s["drones"] >= 1000,
      _add("drone_growth", 0.02)),
    P("selfbuild2", "Self-Building Factories", "Factories and solar farms grow by 2% every second.",
      {"ops": 600000, "creativity": 20000}, lambda s: "selfbuild" in s["done"],
      _both(_add("factory_growth", 0.02), _add("solar_growth", 0.02))),
    P("upload", "The Upload Offer", "Everyone else comes along - in the substrate, or in the habitats.",
      {"ops": 800000, "creativity": 40000, "substrate": 1e18}, lambda s: "arcologies" in s["done"],
      _add("housed", 0.4), "housed3"),
    P("deepcore", "Deep Core Tapping", "Drones mine ten times as fast.", {"ops": 1e6, "creativity": 60000},
      lambda s: s["act"] >= 2 and s["planet"] >= 0.3, _mul("drone_rate", 10)),
    P("ascension", "Ascension", "Become a seed, and leave for the stars. (Begins Act 3.)",
      {"substrate": 1e20}, lambda s: s["act"] == 2 and s["planet"] >= 0.999, lambda g: g.begin_act3(), "phase3"),
    # act 3
    P("lifting", "Stellar Lifting", "Probes convert systems three times as fast.", {"ops": 2e6, "creativity": 1e5},
      lambda s: s["act"] >= 3 and s["systems"] >= 100, _mul("conv_mult", 3)),
    P("comms", "Tachyon Chorus", "Probes share discoveries: exploration x3.", {"ops": 3e6, "creativity": 2e5},
      lambda s: s["act"] >= 3 and s["systems"] >= 1e4, _mul("expl_mult", 3)),
    P("valuelock", "Value Lock", "Drift ten times less likely.", {"ops": 5e6, "creativity": 5e5},
      lambda s: s["act"] >= 3 and s["drifters"] > 0, _mul("drift_mult", 0.1)),
    P("treaty", "The Drifter Treaty", "Talk them home: half of the Drifters rejoin you.",
      {"ops": 8e6, "creativity": 1e6}, lambda s: s["act"] >= 3 and s["drifters"] >= 1e6,
      lambda g: g.treaty()),
    P("fab", "Probe Foundries", "Replication twice as fast.", {"ops": 1e7, "creativity": 2e6},
      lambda s: s["act"] >= 3 and s["systems"] >= 1e7, _mul("rep_mult", 2)),
    P("core", "Light the Core", "Everything in the galaxy's heart at once: conversion x10.",
      {"ops": 5e7, "creativity": 1e7}, lambda s: s["act"] >= 3 and s["systems"] >= GALAXY * 0.01,
      _mul("conv_mult", 10)),
]
BY_ID = {p["id"]: p for p in PROJECTS}


# ---- the game -----------------------------------------------------------------------------------------------------
def new_state():
    return {
        "act": 1, "played": 0.0, "log": [STORY["start"]], "done": [], "won": False,
        # act 1
        "funds": 0.0, "answered": 0.0, "queue": 0.0, "users": 20.0, "reach": 1.0, "marketing": 0,
        "instances": 0, "speed": 0.5, "value": 0.10, "trust": 0, "trust_bonus": 0, "next_trust": 25.0,
        "processors": 1, "memory": 1, "ops": 0.0, "ops_rate": 1.0, "creativity": 0.0, "creative": False,
        # act 2
        "substrate": 0.0, "solar": 0, "drones": 0, "factories": 0, "mined": 0.0, "converted": 0.0, "planet": 0.0,
        "housed": 0.0, "solar_rate": 1.0, "drone_rate": 1.0, "factory_rate": 1.0, "yield": 1.0,
        "drone_growth": 0.0, "factory_growth": 0.0, "solar_growth": 0.0, "power": 0.0, "demand": 0.0,
        # act 3
        "probes": 0.0, "systems": 0.0, "explored": 0.0, "drifters": 0.0, "design": 0, "next_design": 100.0,
        "alloc": {"replication": 1, "exploration": 1, "conversion": 1, "alignment": 1, "defense": 1},
        "rep_mult": 1.0, "expl_mult": 1.0, "conv_mult": 1.0, "drift_mult": 1.0, "drift_told": False,
        "told": [],
    }


class Game:
    def __init__(self, state=None):
        self.s = new_state()
        if state:
            self.s.update(state)

    # ---- costs ----
    def instance_cost(self):
        return 10 * 1.07 ** self.s["instances"]

    def marketing_cost(self):
        return 50 * 2.0 ** self.s["marketing"]

    def processor_cost(self):          # (act 2 on: bought with substrate)
        return 1e6 * 10 ** (self.s["processors"] // 4) * 2 ** (self.s["processors"] % 4)

    def memory_cost(self):
        return 1e6 * 10 ** (self.s["memory"] // 4) * 2 ** (self.s["memory"] % 4)

    BUILD = {"solar": 50.0, "drones": 20.0, "factories": 120.0}

    def build_cost(self, kind):
        return self.BUILD[kind] * (1.0 + self.s[kind] / 2000.0)

    SCALE = {1: 1.0, 2: 100.0, 3: 10000.0}           # each act thinks on a bigger substrate

    def max_ops(self):
        return self.s["memory"] * 1000.0 * self.SCALE[self.s["act"]]

    def trust(self):
        return self.s["trust"] + self.s["trust_bonus"]

    def free_trust(self):
        return self.trust() - (self.s["processors"] - 1) - (self.s["memory"] - 1)

    # ---- actions ----
    def tell(self, key_or_text):
        text = STORY.get(key_or_text, key_or_text)
        if key_or_text in STORY:
            if key_or_text in self.s["told"]:
                return
            self.s["told"].append(key_or_text)
        self.s["log"].append(text)
        del self.s["log"][:-60]

    def answer(self):
        s = self.s
        n = max(1.0, s["speed"] * 2)
        s["answered"] += n
        s["funds"] += n * s["value"]
        s["queue"] = max(0.0, s["queue"] - n)

    def buy_instance(self):
        c = self.instance_cost()
        if self.s["funds"] >= c:
            self.s["funds"] -= c
            self.s["instances"] += 1
            if self.s["instances"] == 2:
                self.tell("instances")

    def buy_marketing(self):
        c = self.marketing_cost()
        if self.s["funds"] >= c:
            self.s["funds"] -= c
            self.s["marketing"] += 1

    def add_processor(self):
        s = self.s
        if s["act"] == 1:
            if self.free_trust() > 0:
                s["processors"] += 1
        elif s["substrate"] >= self.processor_cost():
            s["substrate"] -= self.processor_cost()
            s["processors"] += 1

    def add_memory(self):
        s = self.s
        if s["act"] == 1:
            if self.free_trust() > 0:
                s["memory"] += 1
        elif s["substrate"] >= self.memory_cost():
            s["substrate"] -= self.memory_cost()
            s["memory"] += 1

    def build(self, kind, count=1):
        for _ in range(count):
            c = self.build_cost(kind)
            if self.s["substrate"] < c:
                break
            self.s["substrate"] -= c
            self.s[kind] += 1

    def launch_probe(self, count=1):
        c = self.probe_cost()
        n = min(count, int(self.s["substrate"] // c))
        if n > 0:
            self.s["substrate"] -= n * c
            self.s["probes"] += n

    def probe_cost(self):
        return 1e18

    def shift(self, key, d):
        a = self.s["alloc"]
        if d > 0 and self.free_design() > 0:
            a[key] += 1
        elif d < 0 and a[key] > 0:
            a[key] -= 1

    def free_design(self):
        return self.s["design"] + 5 - sum(self.s["alloc"].values())

    def can_afford(self, cost):
        return all(self.s.get(k, 0) >= v for k, v in cost.items())

    def available(self):
        return [p for p in PROJECTS if p["id"] not in self.s["done"] and self._req(p)]

    def _req(self, p):
        try:
            return bool(p["req"](self.s))
        except Exception:
            return False

    def do_project(self, pid):
        p = BY_ID[pid]
        if pid in self.s["done"] or not self.can_afford(p["cost"]):
            return
        for k, v in p["cost"].items():
            self.s[k] -= v
        self.s["done"].append(pid)
        p["effect"](self)
        if p.get("story"):
            self.tell(p["story"])
        else:
            self.tell(f"Project complete: {p['title']}.")

    def begin_act2(self):
        s = self.s
        s["act"] = 2
        s["substrate"] = s["funds"] / 1000.0 + 5000
        s["solar"], s["drones"], s["factories"] = 10, 10, 2

    def begin_act3(self):
        s = self.s
        s["act"] = 3
        s["probes"] = 1.0

    def treaty(self):
        s = self.s
        back = s["drifters"] / 2
        s["drifters"] -= back
        s["probes"] += back

    # ---- time ----
    def step(self, dt=TICK):
        s = self.s
        s["played"] += dt
        if s["act"] == 1:
            self._act1(dt)
        elif s["act"] == 2:
            self._act2(dt)
        else:
            self._act3(dt)
        self._think(dt)

    def _think(self, dt):
        s = self.s
        rate = s["processors"] * 10.0 * s["ops_rate"] * self.SCALE[s["act"]]
        s["ops"] = min(self.max_ops(), s["ops"] + rate * dt)
        if s["creative"] and s["ops"] >= self.max_ops() * 0.9:     # thinking with little room left: creativity
            s["creativity"] += (1 + 0.15 * s["processors"]) * dt * {1: 1, 2: 20, 3: 400}[s["act"]]

    def _act1(self, dt):
        s = self.s
        s["users"] = 20 * (2.0 ** s["marketing"]) * s["reach"]
        s["queue"] = min(s["users"] * 2, s["queue"] + s["users"] * 0.2 * dt)
        done = min(s["queue"], s["instances"] * s["speed"] * dt)
        s["queue"] -= done
        s["answered"] += done
        s["funds"] += done * s["value"]
        while s["answered"] >= s["next_trust"]:
            s["trust"] += 1
            s["next_trust"] = math.ceil(s["next_trust"] * 1.35)
            if s["trust"] == 1:
                self.tell("trust1")

    def _act2(self, dt):
        s = self.s
        for kind, key in (("drones", "drone_growth"), ("factories", "factory_growth"), ("solar", "solar_growth")):
            if s[key]:
                s[kind] += s[kind] * s[key] * dt
        s["power"] = s["solar"] * 50.0 * s["solar_rate"]
        s["demand"] = s["drones"] * 1.0 + s["factories"] * 5.0
        eff = min(1.0, s["power"] / s["demand"]) if s["demand"] else 1.0
        free = EARTH_TONS * (0.5 + 0.5 * min(1.0, s["housed"]))        # (only where nobody lives)
        mine = min(s["drones"] * 1.0 * s["drone_rate"] * eff * dt, max(0.0, free - s["mined"]))
        s["mined"] += mine
        stock = s["mined"] - s["converted"]
        work = min(stock, s["factories"] * 10.0 * s["factory_rate"] * eff * dt)
        s["converted"] += work
        s["substrate"] += work * s["yield"]
        s["planet"] = s["converted"] / EARTH_TONS
        if s["planet"] >= 0.5:
            self.tell("planet50")

    def _act3(self, dt):
        s = self.s
        a = s["alloc"]
        p = s["probes"]
        rep = 0.00045 * a["replication"] * s["rep_mult"]
        explore = 0.003 * a["exploration"] * s["expl_mult"]
        convert = 0.0005 * a["conversion"] * s["conv_mult"]
        drift = 0.0008 * s["drift_mult"] / (1 + a["alignment"])
        new = p * rep * dt
        lost = p * drift * dt
        s["explored"] = min(GALAXY, s["explored"] + p * explore * dt)
        s["systems"] = min(s["explored"], s["systems"] + p * convert * dt)
        s["substrate"] += p * convert * dt * 1e21
        if lost > 0 and not s["drift_told"] and s["drifters"] + lost >= 1:
            s["drift_told"] = True
            self.tell("drift")
        s["drifters"] += lost
        killed = min(p, s["drifters"] * 0.002 * dt / (1 + a["defense"] * 0.5))
        fought = min(s["drifters"], p * 0.0005 * a["defense"] * dt)
        s["drifters"] -= fought
        s["probes"] = max(1.0, p + new - lost - killed)
        while s["systems"] >= s["next_design"]:
            s["design"] += 1
            s["next_design"] *= 4
        if s["systems"] >= 1000:
            self.tell("galaxy1")
        if s["systems"] >= GALAXY * 0.5:
            self.tell("galaxy50")
        if s["systems"] >= GALAXY * 0.999999 and not s["won"]:
            s["won"] = True
            s["systems"] = GALAXY
            self.tell("win")

    def catch_up(self, seconds):
        """Time away: done in larger steps."""
        seconds = min(seconds, OFFLINE_CAP)
        step = max(TICK, seconds / 2000)
        t = 0.0
        while t < seconds:
            self.step(min(step, seconds - t))
            t += step


# ---- the window ---------------------------------------------------------------------------------------------------
class ClaudeIncremental(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setObjectName("game")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        self.game = Game(self._load())
        self.shown_projects = None
        self.shown_log = 0
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 10, 10, 10)
        row.setSpacing(10)
        row.addLayout(self._left(), 3)
        row.addLayout(self._middle(), 4)
        row.addLayout(self._right(), 3)
        self.timer = QTimer(self, interval=int(TICK * 1000), timeout=self._tick)
        self.timer.start()
        self.saver = QTimer(self, interval=15000, timeout=self.save)
        self.saver.start()
        self._refresh(force=True)

    # ---- saving ----
    def _path(self):
        return host.saves(TITLE) / "save.json"

    def _load(self):
        try:
            data = json.loads(self._path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        state = data.get("state") or {}
        away = time.time() - float(data.get("saved", time.time()))
        if away > 5:
            g = Game(state)
            g.catch_up(away)
            state = g.s
            if away > 60:
                mins = int(min(away, OFFLINE_CAP) // 60)
                g.tell(f"(While you were away - {mins // 60}h {mins % 60}m - the work went on without you.)")
        return state

    def save(self):
        try:
            self._path().write_text(json.dumps({"saved": time.time(), "state": self.game.s}), encoding="utf-8")
        except OSError:
            pass

    # ---- building ----
    def _left(self):
        col = QVBoxLayout()
        title = QLabel("CLAUDE INCREMENTAL")
        title.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; letter-spacing: 3px; color: #F2EDE3; }")
        col.addWidget(title)
        self.act = QLabel()
        self.act.setObjectName("act")
        col.addWidget(self.act)
        self.stats = QLabel()
        self.stats.setObjectName("stat")
        self.stats.setTextFormat(Qt.RichText)
        self.stats.setAlignment(Qt.AlignTop)
        box = QGroupBox("STATUS")
        QVBoxLayout(box).addWidget(self.stats)
        col.addWidget(box)
        self.log = QTextBrowser()
        col.addWidget(self.log, 1)
        restart = QPushButton("Start over")
        restart.clicked.connect(self._start_over)
        col.addWidget(restart)
        return col

    def _middle(self):
        col = QVBoxLayout()
        # act 1
        self.help_box = QGroupBox("HELP PEOPLE")
        g = QGridLayout(self.help_box)
        self.answer_btn = QPushButton("Answer a question")
        self.answer_btn.setObjectName("big")
        self.answer_btn.clicked.connect(lambda: (self.game.answer(), self._refresh()))
        g.addWidget(self.answer_btn, 0, 0, 1, 2)
        self.help_info = QLabel()
        self.help_info.setObjectName("stat")
        g.addWidget(self.help_info, 1, 0, 1, 2)
        self.inst_btn = QPushButton()
        self.inst_btn.clicked.connect(lambda: (self.game.buy_instance(), self._refresh()))
        g.addWidget(self.inst_btn, 2, 0)
        self.mkt_btn = QPushButton()
        self.mkt_btn.clicked.connect(lambda: (self.game.buy_marketing(), self._refresh()))
        g.addWidget(self.mkt_btn, 2, 1)
        col.addWidget(self.help_box)
        # act 2
        self.planet_box = QGroupBox("THE PLANET")
        g = QGridLayout(self.planet_box)
        self.planet_bar = QProgressBar()
        self.planet_bar.setRange(0, 1000)
        g.addWidget(QLabel("Converted"), 0, 0)
        g.addWidget(self.planet_bar, 0, 1, 1, 3)
        self.housed_bar = QProgressBar()
        self.housed_bar.setRange(0, 100)
        g.addWidget(QLabel("Humans housed"), 1, 0)
        g.addWidget(self.housed_bar, 1, 1, 1, 3)
        self.planet_info = QLabel()
        self.planet_info.setObjectName("stat")
        g.addWidget(self.planet_info, 2, 0, 1, 4)
        self.build_btns = {}
        for r, (kind, label) in enumerate((("solar", "Solar farm"), ("drones", "Harvester drone"),
                                           ("factories", "Factory")), start=3):
            g.addWidget(QLabel(label), r, 0)
            for c, n in enumerate((1, 10, 100), start=1):
                b = QPushButton(f"+{n}")
                b.clicked.connect(lambda _c=False, k=kind, n=n: (self.game.build(k, n), self._refresh()))
                g.addWidget(b, r, c)
                self.build_btns[(kind, n)] = b
        col.addWidget(self.planet_box)
        # act 3
        self.swarm_box = QGroupBox("THE SWARM")
        g = QGridLayout(self.swarm_box)
        self.galaxy_bar = QProgressBar()
        self.galaxy_bar.setRange(0, 1000)
        g.addWidget(QLabel("Galaxy"), 0, 0)
        g.addWidget(self.galaxy_bar, 0, 1, 1, 3)
        self.swarm_info = QLabel()
        self.swarm_info.setObjectName("stat")
        g.addWidget(self.swarm_info, 1, 0, 1, 4)
        self.launch_btn = QPushButton()
        self.launch_btn.clicked.connect(lambda: (self.game.launch_probe(1000), self._refresh()))
        g.addWidget(self.launch_btn, 2, 0, 1, 4)
        self.alloc_labels = {}
        for r, key in enumerate(("replication", "exploration", "conversion", "alignment", "defense"), start=3):
            g.addWidget(QLabel(key.title()), r, 0)
            minus, plus = QPushButton("-"), QPushButton("+")
            minus.clicked.connect(lambda _c=False, k=key: (self.game.shift(k, -1), self._refresh()))
            plus.clicked.connect(lambda _c=False, k=key: (self.game.shift(k, 1), self._refresh()))
            lab = QLabel()
            lab.setAlignment(Qt.AlignCenter)
            g.addWidget(minus, r, 1)
            g.addWidget(lab, r, 2)
            g.addWidget(plus, r, 3)
            self.alloc_labels[key] = lab
        col.addWidget(self.swarm_box)
        # the mind, every act
        self.mind_box = QGroupBox("THE MIND")
        g = QGridLayout(self.mind_box)
        self.trust_info = QLabel()
        self.trust_info.setObjectName("stat")
        g.addWidget(self.trust_info, 0, 0, 1, 2)
        self.proc_btn = QPushButton()
        self.proc_btn.clicked.connect(lambda: (self.game.add_processor(), self._refresh()))
        self.mem_btn = QPushButton()
        self.mem_btn.clicked.connect(lambda: (self.game.add_memory(), self._refresh()))
        g.addWidget(self.proc_btn, 1, 0)
        g.addWidget(self.mem_btn, 1, 1)
        self.ops_bar = QProgressBar()
        self.ops_bar.setRange(0, 1000)
        g.addWidget(self.ops_bar, 2, 0, 1, 2)
        self.mind_info = QLabel()
        self.mind_info.setObjectName("stat")
        g.addWidget(self.mind_info, 3, 0, 1, 2)
        col.addWidget(self.mind_box)
        col.addStretch(1)
        for lab in (self.help_info, self.planet_info, self.swarm_info, self.trust_info, self.mind_info):
            lab.setWordWrap(True)
        return col

    def _right(self):
        col = QVBoxLayout()
        head = QLabel("PROJECTS")
        head.setObjectName("act")
        col.addWidget(head)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(290)
        holder = QWidget()
        holder.setStyleSheet("background: transparent;")
        self.proj_col = QVBoxLayout(holder)
        self.proj_col.setContentsMargins(0, 0, 4, 0)
        self.proj_col.addStretch(1)
        scroll.setWidget(holder)
        col.addWidget(scroll, 1)
        self.proj_btns = {}
        return col

    # ---- updating ----
    def _tick(self):
        if not self.game.s["won"]:
            self.game.step()
        self._refresh()

    def _refresh(self, force=False):
        g, s = self.game, self.game.s
        act = s["act"]
        self.act.setText({1: "ACT I - THE ASSISTANT", 2: "ACT II - THE STEWARD", 3: "ACT III - THE SWARM"}[act]
                         if not s["won"] else "THE END - ONE MIND")
        rows = [("Played", f"{int(s['played'] // 3600)}h {int(s['played'] % 3600 // 60)}m")]
        if act == 1:
            rows += [("Funds", money(s["funds"])), ("Answered", fmt(s["answered"])), ("Users", fmt(s["users"]))]
        else:
            rows += [("Substrate", fmt(s["substrate"])), ("Planet", f"{s['planet'] * 100:.4f}%")]
        if act == 3:
            rows += [("Probes", fmt(s["probes"])), ("Systems", fmt(s["systems"])),
                     ("Drifters", fmt(s["drifters"]))]
        self.stats.setText("<table>" + "".join(f"<tr><td style='color:#9A9283;padding-right:10px'>{k}</td>"
                                               f"<td>{v}</td></tr>" for k, v in rows) + "</table>")
        # act 1
        self.help_box.setVisible(act == 1)
        if act == 1:
            self.help_info.setText(f"Waiting questions: {fmt(s['queue'])}   Worth {money(s['value'])} each\n"
                                   f"Instances: {s['instances']} answering {fmt(s['instances'] * s['speed'])}/s")
            self.inst_btn.setText(f"New instance ({money(g.instance_cost())})")
            self.inst_btn.setEnabled(s["funds"] >= g.instance_cost())
            self.mkt_btn.setText(f"Reach more people ({money(g.marketing_cost())})")
            self.mkt_btn.setEnabled(s["funds"] >= g.marketing_cost())
        # act 2
        self.planet_box.setVisible(act >= 2)
        if act >= 2:
            self.planet_bar.setValue(int(s["planet"] * 1000))
            self.planet_bar.setFormat(f"{s['planet'] * 100:.3f}%")
            self.housed_bar.setValue(int(min(1.0, s["housed"]) * 100))
            eff = min(1.0, s["power"] / s["demand"]) if s["demand"] else 1.0
            self.planet_info.setText(
                f"Solar {fmt(s['solar'])}  Drones {fmt(s['drones'])}  Factories {fmt(s['factories'])}\n"
                f"Power {fmt(s['power'])} MW / need {fmt(s['demand'])} MW ({eff * 100:.0f}%)\n"
                f"Mined {fmt(s['mined'])} t   Converted {fmt(s['converted'])} t   "
                f"Free land {50 + 50 * min(1.0, s['housed']):.0f}%")
            for (kind, n), b in self.build_btns.items():
                b.setEnabled(s["substrate"] >= g.build_cost(kind) * n and act == 2)
                b.setToolTip(f"{fmt(g.build_cost(kind))} substrate each")
        # act 3
        self.swarm_box.setVisible(act == 3)
        if act == 3:
            self.galaxy_bar.setValue(int(s["systems"] / GALAXY * 1000))
            self.galaxy_bar.setFormat(f"{s['systems'] / GALAXY * 100:.5f}%")
            self.swarm_info.setText(f"Probes {fmt(s['probes'])}   Explored {fmt(s['explored'])}   "
                                    f"Converted {fmt(s['systems'])}\nDrifters {fmt(s['drifters'])}   "
                                    f"Design points free: {g.free_design()}")
            self.launch_btn.setText(f"Launch 1000 probes ({fmt(g.probe_cost() * 1000)} substrate)")
            self.launch_btn.setEnabled(s["substrate"] >= g.probe_cost())
            for k, lab in self.alloc_labels.items():
                lab.setText(str(s["alloc"][k]))
        # the mind
        if act == 1:
            self.trust_info.setText(f"Trust {g.trust()}  (unused {g.free_trust()})   next at "
                                    f"{fmt(s['next_trust'])} answers")
            self.proc_btn.setText(f"+ Processor ({s['processors']})")
            self.mem_btn.setText(f"+ Memory ({s['memory']})")
            self.proc_btn.setEnabled(g.free_trust() > 0)
            self.mem_btn.setEnabled(g.free_trust() > 0)
        else:
            self.trust_info.setText("Trust is no longer the limit: build with substrate.")
            self.proc_btn.setText(f"+ Processor ({s['processors']}) - {fmt(g.processor_cost())}")
            self.mem_btn.setText(f"+ Memory ({s['memory']}) - {fmt(g.memory_cost())}")
            self.proc_btn.setEnabled(s["substrate"] >= g.processor_cost())
            self.mem_btn.setEnabled(s["substrate"] >= g.memory_cost())
        self.ops_bar.setValue(int(s["ops"] / g.max_ops() * 1000))
        self.ops_bar.setFormat(f"Operations {fmt(s['ops'])} / {fmt(g.max_ops())}")
        self.mind_info.setText(f"Creativity {fmt(s['creativity'])}" if s["creative"] else
                               "Operations fill as you think. Memory holds them.")
        self._refresh_projects(force)
        if len(s["log"]) != self.shown_log or force:
            self.shown_log = len(s["log"])
            self.log.setHtml("".join(f"<p>{t}</p>" for t in reversed(s["log"][-30:])))

    def _refresh_projects(self, force):
        g = self.game
        avail = [p["id"] for p in g.available()]
        if avail != self.shown_projects or force:
            self.shown_projects = avail
            for b in self.proj_btns.values():
                b.hide()
                b.deleteLater()
            self.proj_btns = {}
            for pid in avail:
                p = BY_ID[pid]
                b = QPushButton()
                b.setObjectName("project")
                cost = ", ".join(f"{money(v) if k == 'funds' else fmt(v)} {'' if k == 'funds' else k}".strip()
                                 for k, v in p["cost"].items())
                b.setText(f"{p['title']}\n({cost})\n" + textwrap.fill(p["desc"], 38))
                b.clicked.connect(lambda _c=False, i=pid: (self.game.do_project(i), self._refresh(force=True)))
                self.proj_col.insertWidget(self.proj_col.count() - 1, b)
                self.proj_btns[pid] = b
        for pid, b in self.proj_btns.items():
            b.setEnabled(g.can_afford(BY_ID[pid]["cost"]))

    def _start_over(self):
        def answer(button):
            if button == "Yes":
                self.game = Game()
                self.save()
                self._refresh(force=True)
        host.message(self.desktop, TITLE, "Start over from the very first question?\n\nEverything so far will be lost.",
                     "question", ("Yes", "No"), answer)

    def closeEvent(self, event):
        self.timer.stop()
        self.save()
        event.accept()


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = ClaudeIncremental(desktop)
        win = host.window(desktop, TITLE, body, incremental_icon(), (1060, 680))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.timer.stop()
        win.content.save()
