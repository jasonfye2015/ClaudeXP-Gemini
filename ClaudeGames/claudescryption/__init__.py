"""Claudescryption: a card game in a cabin in the woods, after the first act of Inscryption.

Leshy deals. You walk a map through the Woodlands, the Wetlands and the Snow Line - battles, new cards, a campfire,
the sacrifice stones, the mycologists - to each region's boss (the Prospector, the Angler, the Trapper), and then to
Leshy himself, and the Moon. You carry two candles: lose a battle and one goes out; lose both and the run is over,
and you leave a Deathcard behind for the runs to come. (The rules are in game.py.)

The run saves itself whenever you're on the map; deathcards are kept for good."""
import json
import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import QWidget
from shiboken6 import isValid

from claudecore import host

from .game import CARDS, RARES, REGIONS, REWARDS, SIGILS, Battle, Creature, info, spec

TITLE = "Claudescryption"
EMOJI = "Segoe UI Emoji"
INK = QColor("#2A2118")
PAPER = QColor("#E6D9BC")
STARTER = ["Stoat", "Bullfrog", "Wolf", "Sparrow"]
INTROS = ["A creature emerges from the trees.", "Something stirs in the undergrowth.", "You are not alone here.",
          "The wind carries the scent of something hungry.", "Leshy lays down his cards.",
          "\"Let us see what you have learned.\"", "A shape moves at the edge of the firelight."]
BOSS_LINES = {"The Prospector": "\"GOLD! There's gold in these hills, and I'll have yours!\"",
              "The Angler": "\"Go fish.\"",
              "The Trapper": "\"Nothing escapes my traps. Nothing.\"",
              "Leshy": "Leshy sets down the masks. \"Now. You face me.\""}
NODE_ICONS = {"battle": "⚔️", "choice": "🃏", "cost": "🎴", "campfire": "🔥", "stones": "🪨", "fungi": "🍄",
              "boss": "💀", "start": "🕯️"}
NODE_NAMES = {"battle": "A battle", "choice": "Choose a creature", "cost": "A card by its cost",
              "campfire": "The campfire", "stones": "The sacrifice stones", "fungi": "The mycologists",
              "boss": "The boss", "start": "Where you begin"}
SYLLABLES = ("gra", "mor", "thu", "vel", "sko", "rin", "ash", "bel", "dur", "kai", "lo", "fen", "orr", "ul", "zen")


def scry_icon():
    pm = QPixmap(32, 32)
    pm.fill(QColor("#1A120C"))
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(INK, 1))
    p.setBrush(PAPER)
    p.drawRoundedRect(QRectF(8, 4, 16, 24), 2, 2)
    f = QFont(EMOJI)
    f.setPixelSize(11)
    p.setFont(f)
    p.drawText(QRectF(8, 6, 16, 16), Qt.AlignCenter, "🐺")
    g = QRadialGradient(26, 6, 6)
    g.setColorAt(0, QColor("#FFE9A0"))
    g.setColorAt(1, QColor(255, 140, 0, 0))
    p.setBrush(g)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(26, 6), 6, 6)
    p.end()
    return QIcon(pm)


# ---- the run -----------------------------------------------------------------------------------------------------
def make_map(region, rng):
    """Rows of nodes, each linked to one or two in the next row; a boss at the end."""
    rows = [[{"type": "start", "x": 0.5, "links": [], "done": True}]]
    for r in range(1, 7):
        n = rng.choice((2, 3, 3))
        row = []
        for i in range(n):
            kind = rng.choices(["battle", "choice", "cost", "campfire", "stones", "fungi"], [46, 20, 8, 9, 9, 8])[0]
            row.append({"type": kind, "x": (i + 1) / (n + 1), "links": [], "done": False})
        rows.append(row)
    for r in (2, 4, 6):                              # (a few battles you can't avoid)
        for node in rows[r]:
            node["type"] = "battle"
    rows.append([{"type": "boss", "x": 0.5, "links": [], "done": False}])
    for r in range(len(rows) - 1):
        a, b = rows[r], rows[r + 1]
        for i, node in enumerate(a):
            near = sorted(range(len(b)), key=lambda j: abs(b[j]["x"] - node["x"]))
            node["links"] = sorted(set(near[:1 + (1 if rng.random() < 0.5 and len(b) > 1 else 0)]))
        for j in range(len(b)):                      # everything can be reached
            if not any(j in node["links"] for node in a):
                closest = min(range(len(a)), key=lambda i: abs(a[i]["x"] - b[j]["x"]))
                a[closest]["links"].append(j)
    return rows


def new_run(rng):
    return {"deck": [spec(n) for n in STARTER], "candles": 2, "region": 0, "map": make_map(0, rng),
            "pos": [0, 0], "battles": 0}


def card_for_cost(kind, rng, deathcards):
    pool = [n for n in REWARDS if (CARDS[n][1] > 0 if kind == "blood" else CARDS[n][2] > 0 if kind == "bones"
                                   else CARDS[n][1] == 0 and CARDS[n][2] == 0)]
    return spec(rng.choice(pool or REWARDS))


def reward_cards(rng, deathcards, rare=False):
    out = []
    names = RARES if rare else REWARDS
    for _ in range(3):
        if deathcards and rng.random() < 0.12:
            out.append(rng.choice(deathcards))
        else:
            out.append(spec(rng.choice(names)))
    return out


# ---- drawing cards --------------------------------------------------------------------------------------------------
def draw_card(p, r, card, *, faded=False, selected=False, marked=False, hover=False, back=None):
    """A card: name, cost, the creature, sigils, power and health. card: a deck spec or a Creature."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    if faded:
        p.setOpacity(0.55)
    if back:                                         # a face-down card (the cost choice)
        p.setPen(QPen(INK, 2))
        p.setBrush(QColor("#5A3E2A"))
        p.drawRoundedRect(r, 6, 6)
        f = QFont(EMOJI)
        f.setPixelSize(int(r.width() * 0.36))
        p.setFont(f)
        p.drawText(r, Qt.AlignCenter, back)
        p.restore()
        return
    live = isinstance(card, Creature)
    if live:
        emoji, blood, bones, power, health, sigils = card.emoji, card.blood, card.bones, card.base_power, \
            card.health, card.sigils
        name = card.name
        max_health = card.max_health
    else:
        emoji, blood, bones, power, health, sigils = info(card)
        name = card["custom"]["name"] if card.get("custom") else card["name"]
        max_health = health
    custom = (card.spec if live else card).get("custom")
    terrain = not custom and CARDS.get(name, ("", 0, 0, 0, 0, [], "c"))[6] == "t"
    border = QColor("#C9A227") if selected else QColor("#B23A2A") if marked else INK
    p.setPen(QPen(border, 3 if (selected or marked) else 1.5))
    grad = QLinearGradient(r.topLeft(), r.bottomLeft())
    base = QColor("#CFC6B4") if terrain else PAPER
    if not live and card.get("custom"):
        base = QColor("#D8C9E8")                     # deathcards are paler, stranger
    grad.setColorAt(0, base.lighter(108))
    grad.setColorAt(1, base.darker(112))
    p.setBrush(grad)
    p.drawRoundedRect(r, 6, 6)
    if hover:
        p.fillRect(r, QColor(255, 255, 255, 25))
    w, h = r.width(), r.height()
    f = QFont("Georgia")
    f.setPixelSize(max(8, int(w * 0.11)))
    f.setBold(True)
    p.setFont(f)
    p.setPen(INK)
    p.drawText(QRectF(r.x() + 4, r.y() + 3, w - 8, h * 0.13), Qt.AlignCenter,
               p.fontMetrics().elidedText(name, Qt.ElideRight, int(w - 8)))
    # cost: blood drops or bones, top right
    if blood or bones:
        p.setPen(Qt.NoPen)
        n = blood or bones
        col = QColor("#A3201A") if blood else QColor("#EFEBDF")
        size = w * 0.085
        for i in range(min(n, 4)):
            cx = r.right() - 8 - i * (size * 1.25)
            cy = r.y() + h * 0.2
            p.setBrush(col)
            if blood:
                drop = QPainterPath()
                drop.moveTo(cx, cy - size * 0.7)
                drop.quadTo(cx + size * 0.6, cy, cx, cy + size * 0.45)
                drop.quadTo(cx - size * 0.6, cy, cx, cy - size * 0.7)
                p.drawPath(drop)
            else:
                p.setPen(QPen(INK, 0.8))
                p.drawRoundedRect(QRectF(cx - size * 0.55, cy - size * 0.2, size * 1.1, size * 0.4), 2, 2)
                p.setPen(Qt.NoPen)
        if n > 4:
            fn = QFont("Georgia")
            fn.setPixelSize(int(w * 0.09))
            p.setFont(fn)
            p.setPen(INK)
            p.drawText(QRectF(r.right() - 8 - 5 * size * 1.25 - 10, r.y() + h * 0.15, 20, size * 1.5),
                       Qt.AlignCenter, f"{n}x")
    # the creature
    f = QFont(EMOJI)
    f.setPixelSize(int(w * 0.42))
    p.setFont(f)
    p.setPen(INK)
    p.drawText(QRectF(r.x(), r.y() + h * 0.22, w, h * 0.42), Qt.AlignCenter, emoji)
    # sigils
    if sigils:
        f = QFont(EMOJI)
        f.setPixelSize(int(w * 0.15))
        p.setFont(f)
        icons = " ".join(SIGILS.get(s, ("?", ""))[0] for s in sigils[:3])
        p.drawText(QRectF(r.x(), r.y() + h * 0.64, w, h * 0.16), Qt.AlignCenter, icons)
    # power and health
    f = QFont("Georgia")
    f.setPixelSize(int(w * 0.17))
    f.setBold(True)
    p.setFont(f)
    if not terrain or power:
        p.setPen(INK)
        p.drawText(QRectF(r.x() + 6, r.bottom() - h * 0.2, w * 0.4, h * 0.18), Qt.AlignLeft | Qt.AlignVCenter,
                   str(power))
    p.setPen(QColor("#A3201A") if live and health < max_health else INK)
    p.drawText(QRectF(r.right() - w * 0.4 - 6, r.bottom() - h * 0.2, w * 0.4, h * 0.18),
               Qt.AlignRight | Qt.AlignVCenter, str(health))
    p.restore()


# ---- the cabin ---------------------------------------------------------------------------------------------------
class Cabin(QWidget):
    """Everything on screen: title, map, battles, and the places on the map."""

    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setMouseTracking(True)
        self.setMinimumSize(980, 680)
        self.rng = random.Random()
        self.deathcards = self._load("deathcards.json", [])
        self.run = self._load("run.json", None)
        self.screen = "title"
        self.hits = []
        self.mouse = QPointF(-1, -1)
        self.battle = None
        self.anim = None                            # the combat generator, stepped by the timer
        self.flash = None                           # (what, side, lane, frames)
        self.sel = None
        self.sacs = []
        self.prompt = ""
        self.offer = []
        self.pick = []
        self.camp = None
        self.t = 0.0
        self.timer = QTimer(self, interval=40, timeout=self._tick)
        self.timer.start()
        self.combat_timer = QTimer(self, interval=420, timeout=self._combat_step)

    # ---- saving ----
    def _load(self, name, default):
        try:
            return json.loads((host.saves(TITLE) / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return default

    def _save(self, name, data):
        try:
            path = host.saves(TITLE) / name
            if data is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(json.dumps(data), encoding="utf-8")
        except OSError:
            pass

    # ---- the run ----
    def new_run(self):
        self.run = new_run(self.rng)
        self.screen = "map"
        self.prompt = "Leshy deals you four cards. \"Choose your path.\""
        self._save("run.json", self.run)

    def node(self, r, i):
        return self.run["map"][r][i]

    def reachable(self):
        r, i = self.run["pos"]
        if r + 1 >= len(self.run["map"]):
            return []
        return [(r + 1, j) for j in self.node(r, i)["links"]]

    def go(self, r, i):
        self.run["pos"] = [r, i]
        node = self.node(r, i)
        kind = node["type"]
        if kind == "battle":
            reg = self.run["region"]
            diff = min(3, r // 3 + (1 if reg >= 1 else 0))
            self._start_battle(Battle(self.run["deck"], reg, diff, seed=self.rng.random()))
            self.prompt = self.rng.choice(INTROS)
        elif kind == "boss":
            reg = self.run["region"]
            boss = "Leshy" if reg >= 3 else REGIONS[reg]["boss"]
            self._start_battle(Battle(self.run["deck"], min(2, reg), min(reg, 3) * 0.5, boss=boss,
                                      deathcards=self.deathcards, seed=self.rng.random()))
            self.prompt = BOSS_LINES[boss]
        elif kind == "choice":
            self.offer = reward_cards(self.rng, self.deathcards)
            self.screen = "choice"
            self.prompt = "\"Choose one. The others return to the woods.\""
        elif kind == "cost":
            self.offer = [("blood", "🩸"), ("bones", "🦴"), ("free", "🐿️")]
            self.screen = "cost"
            self.prompt = "\"Three cards, face down. You may know only what they cost.\""
        elif kind == "campfire":
            self.camp = {"card": None, "times": 0}
            self.screen = "campfire"
            self.prompt = "Survivors huddle by a fire. \"Warm a creature by it - if you dare.\""
        elif kind == "stones":
            self.pick = []
            self.screen = "stones"
            self.prompt = "The sacrifice stones. Choose a creature to give up its sigil."
        elif kind == "fungi":
            self.pick = []
            self.screen = "fungi"
            self.prompt = "Two mycologists. \"Bring us two of a kind, and we will make them one.\""
        node["done"] = True

    def finish_node(self):
        r, i = self.run["pos"]
        if self.node(r, i)["type"] == "boss":
            self._next_region()
            return
        self.screen = "map"
        self._save("run.json", self.run)

    def _next_region(self):
        run = self.run
        run["region"] += 1
        run["candles"] = 2
        if run["region"] > 3:
            self.screen = "victory"
            self._save("run.json", None)
            return
        run["map"] = make_map(min(2, run["region"]), self.rng)
        if run["region"] == 3:                       # the end: only Leshy
            run["map"] = [[{"type": "start", "x": 0.5, "links": [0], "done": True}],
                          [{"type": "boss", "x": 0.5, "links": [], "done": False}]]
        run["pos"] = [0, 0]
        self.offer = reward_cards(self.rng, self.deathcards, rare=True)
        self.screen = "choice"
        self.prompt = "A rare creature, for your trouble. Your candles are relit."
        self._save("run.json", run)

    # ---- battles ----
    def _start_battle(self, b):
        self.battle = b
        self.screen = "battle"
        self.sel = None
        self.sacs = []

    def _combat_step(self):
        if self.anim is None:
            self.combat_timer.stop()
            return
        try:
            ev = next(self.anim)
            if ev[0] in ("face", "hit"):
                self.flash = ev
            elif ev[0] == "trick":
                self.prompt = self.battle.log[-1] if self.battle.log else ""
        except StopIteration:
            self.anim = None
            self.combat_timer.stop()
            self.flash = None
            self._after_combat()
        self.update()

    def _after_combat(self):
        b = self.battle
        if b.over == "phase":
            b.next_phase()
            self.prompt = b.log[-1] if b.log else "The second phase begins."
        elif b.over == "won":
            if b.boss:
                self.prompt = f"{'Leshy' if b.boss == 'Leshy' else b.boss} is beaten."
            else:
                self.prompt = "You win the battle."
            self.run["battles"] += 1
            self.battle = None
            self.finish_node()
        elif b.over == "lost":
            self.run["candles"] -= 1
            self.battle = None
            if self.run["candles"] <= 0:
                self.screen = "death"
                self.pick = []
                self.prompt = "Your last candle goes out. \"Before you go... leave something of yourself behind.\""
                self._save("run.json", None)
            else:
                self.prompt = "A candle is snuffed out. You carry on, in a little more darkness."
                self.finish_node()
        elif not b.drawn and not b.can_draw():
            b.drawn = True

    def ring_bell(self):
        b = self.battle
        if b is None or self.anim is not None:
            return
        if b.can_draw():
            self.prompt = "Draw a card first: your deck or a squirrel."
            return
        self.sel, self.sacs = None, []
        self.anim = b.ring_bell()
        self.combat_timer.start()

    def click_hand(self, i):
        b = self.battle
        if b.can_draw():
            self.prompt = "Draw a card first: your deck or a squirrel."
            return
        card = b.hand[i]
        if self.sel == i:
            self.sel, self.sacs = None, []
            return
        if not b.can_afford(card):
            _e, blood, bones, *_ = info(card)
            self.prompt = (f"You need {bones} bones." if bones else
                           f"You haven't enough creatures to sacrifice ({blood} blood).")
            return
        self.sel, self.sacs = i, []
        blood = info(card)[1]
        self.prompt = (f"Choose creatures to sacrifice ({blood} blood), then where to play it." if blood
                       else "Choose where to play it.")

    def click_lane(self, lane):
        b = self.battle
        if self.sel is None:
            c = b.you[lane]
            if c is not None:
                self.prompt = f"{c.name}: " + "; ".join(SIGILS[s][1] for s in c.sigils if s in SIGILS) or c.name
            return
        card = b.hand[self.sel]
        blood = info(card)[1]
        need = blood - b.blood_of(self.sacs)
        if b.you[lane] is not None and lane not in self.sacs and need > 0:
            self.sacs.append(lane)                  # mark a sacrifice
            need = blood - b.blood_of(self.sacs)
            self.prompt = "Enough blood. Now choose where to play it." if need <= 0 else \
                f"{need} more blood."
            return
        if lane in self.sacs and need > 0:
            self.sacs.remove(lane)
            return
        if need > 0:
            self.prompt = f"{need} more blood: choose another creature to sacrifice."
            return
        if b.you[lane] is not None and lane not in self.sacs:
            self.prompt = "That space is taken."
            return
        if b.play(self.sel, lane, list(self.sacs)):
            if self.sacs:
                self.prompt = "Blood is spilled."
            self.sel, self.sacs = None, []
        else:
            self.prompt = "That can't be played there."

    # ---- input ----
    def mouseMoveEvent(self, e):
        self.mouse = e.position()
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            self.sel, self.sacs = None, []
            if self.screen == "deck":
                self.screen = self.back_to
            self.update()
            return
        pos = e.position()
        for rect, action in reversed(self.hits):
            if rect.contains(pos):
                action()
                self.update()
                return

    def _tick(self):
        self.t += 0.04
        self.update()

    # ---- drawing ----
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self.hits = []
        self._table(p)
        draw = {"title": self._draw_title, "map": self._draw_map, "battle": self._draw_battle,
                "choice": self._draw_choice, "cost": self._draw_cost, "campfire": self._draw_campfire,
                "stones": self._draw_stones, "fungi": self._draw_fungi, "deck": self._draw_deck,
                "death": self._draw_death, "made": self._draw_made, "victory": self._draw_victory}[self.screen]
        draw(p)
        if self.prompt and self.screen not in ("title",):
            f = QFont("Georgia")
            f.setPixelSize(16)
            f.setItalic(True)
            p.setFont(f)
            p.setPen(QColor("#E8D9B0"))
            p.drawText(QRectF(200, self.height() - 34, self.width() - 400, 28), Qt.AlignCenter, self.prompt)

    def _table(self, p):
        g = QRadialGradient(self.width() / 2, self.height() * 0.45, self.width() * 0.75)
        g.setColorAt(0, QColor("#4A3423"))
        g.setColorAt(1, QColor("#120B07"))
        p.fillRect(self.rect(), g)
        p.setPen(QPen(QColor(0, 0, 0, 40), 1))
        for y in range(0, self.height(), 46):        # the planks of the table
            p.drawLine(0, y, self.width(), y)

    def _button(self, p, rect, text, action, big=False):
        hover = rect.contains(self.mouse)
        p.setPen(QPen(QColor("#C9A227") if hover else QColor("#8A6A3A"), 1.5))
        p.setBrush(QColor(60, 40, 25, 230) if hover else QColor(35, 24, 16, 230))
        p.drawRoundedRect(rect, 6, 6)
        f = QFont("Georgia")
        f.setPixelSize(18 if big else 14)
        p.setFont(f)
        p.setPen(QColor("#F0E2C0"))
        p.drawText(rect, Qt.AlignCenter, text)
        self.hits.append((rect, action))

    def _candles(self, p, x, y):
        for i in range(2):
            cx = x + i * 34
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#E9DFC9"))
            p.drawRect(QRectF(cx - 6, y, 12, 38))
            if self.run and i < self.run["candles"]:
                flick = math.sin(self.t * 9 + i * 2) * 1.5
                g = QRadialGradient(cx, y - 8, 16)
                g.setColorAt(0, QColor(255, 230, 150, 240))
                g.setColorAt(0.4, QColor(255, 150, 40, 160))
                g.setColorAt(1, QColor(255, 120, 0, 0))
                p.setBrush(g)
                p.drawEllipse(QPointF(cx, y - 8 + flick * 0.3), 16, 16)
                p.setBrush(QColor("#FFF4C8"))
                p.drawEllipse(QPointF(cx, y - 7 + flick * 0.3), 3, 6 + flick)
            else:
                p.setPen(QPen(QColor("#2A2118"), 2))
                p.drawLine(QPointF(cx, y), QPointF(cx, y - 5))

    def _title_text(self, p, text, y, size=44):
        f = QFont("Georgia")
        f.setPixelSize(size)
        p.setFont(f)
        p.setPen(QColor("#E8D9B0"))
        p.drawText(QRectF(0, y, self.width(), size + 16), Qt.AlignCenter, text)

    def _draw_title(self, p):
        self._title_text(p, "CLAUDESCRYPTION", self.height() * 0.2, 54)
        f = QFont("Georgia")
        f.setPixelSize(17)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(QColor("#B8A27A"))
        p.drawText(QRectF(0, self.height() * 0.2 + 74, self.width(), 30), Qt.AlignCenter,
                   "A cabin. A table. A game of cards with something that is not quite a man.")
        w = 240
        x = (self.width() - w) / 2
        y = self.height() * 0.48
        if self.run:
            self._button(p, QRectF(x, y, w, 46), "Continue the run", lambda: self._continue(), big=True)
            y += 58
        self._button(p, QRectF(x, y, w, 46), "A new run", self.new_run, big=True)
        p.setPen(QColor("#8A7A5A"))
        f.setPixelSize(13)
        p.setFont(f)
        p.drawText(QRectF(0, self.height() - 60, self.width(), 20), Qt.AlignCenter,
                   f"Deathcards left behind: {len(self.deathcards)}")

    def _continue(self):
        self.screen = "map"
        self.prompt = "\"Ah. You've returned.\""

    def _side_panel(self, p):
        """Candles and the deck button, on the map and the other places."""
        self._candles(p, 40, 70)
        reg = self.run["region"]
        name = "Leshy's Cabin" if reg >= 3 else REGIONS[reg]["name"]
        f = QFont("Georgia")
        f.setPixelSize(20)
        p.setFont(f)
        p.setPen(QColor("#E8D9B0"))
        p.drawText(QRectF(20, 130, 200, 30), Qt.AlignLeft, name)
        self._button(p, QRectF(20, 170, 150, 34), f"Your deck ({len(self.run['deck'])})", self._show_deck)
        self._button(p, QRectF(20, self.height() - 90, 150, 30), "Leave the table", self._to_title)

    def _to_title(self):
        self.screen = "title"
        if self.run and self.battle is None:
            self._save("run.json", self.run)

    def _show_deck(self):
        self.back_to = self.screen
        self.screen = "deck"

    def _draw_map(self, p):
        self._side_panel(p)
        rows = self.run["map"]
        top, bottom = 60, self.height() - 80
        left, right = 260, self.width() - 60
        pos = lambda r, i: QPointF(left + rows[r][i]["x"] * (right - left), bottom - r * (bottom - top) / max(1, len(rows) - 1))  # noqa: E731,E501
        p.setPen(QPen(QColor("#7A5A3A"), 2, Qt.DashLine))
        for r, row in enumerate(rows):
            for i, node in enumerate(row):
                for j in node["links"]:
                    p.drawLine(pos(r, i), pos(r + 1, j))
        reach = set(map(tuple, self.reachable()))
        here = tuple(self.run["pos"])
        f = QFont(EMOJI)
        f.setPixelSize(26)
        for r, row in enumerate(rows):
            for i, node in enumerate(row):
                c = pos(r, i)
                rect = QRectF(c.x() - 24, c.y() - 24, 48, 48)
                hot = (r, i) in reach
                p.setPen(QPen(QColor("#C9A227") if hot else QColor("#5A4430"), 3 if hot else 1.5))
                p.setBrush(QColor(70, 50, 32) if not node["done"] or (r, i) == here else QColor(40, 30, 22))
                p.drawEllipse(rect)
                p.setFont(f)
                p.setPen(INK)
                p.setOpacity(1.0 if not node["done"] or (r, i) == here else 0.4)
                icon = NODE_ICONS["boss"] if node["type"] == "boss" else NODE_ICONS[node["type"]]
                p.drawText(rect, Qt.AlignCenter, icon)
                p.setOpacity(1.0)
                if hot:
                    self.hits.append((rect, lambda r=r, i=i: self.go(r, i)))
                if rect.contains(self.mouse):
                    self.prompt = NODE_NAMES[node["type"]] if node["type"] != "boss" else \
                        ("Leshy" if self.run["region"] >= 3 else REGIONS[self.run["region"]]["boss"])
        c = pos(*here)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#C9A227"))
        p.drawEllipse(QPointF(c.x(), c.y() + 30), 6, 6)

    # the battle
    def _lane_x(self, lane):
        return 250 + lane * 128

    def _draw_battle(self, p):
        b = self.battle
        cw, ch = 112, 152
        # Leshy's side
        f = QFont("Georgia")
        f.setPixelSize(14)
        for lane in range(4):
            x = self._lane_x(lane)
            for row, y, cards, faded in (("queue", 14, b.queue, True), ("leshy", 182, b.leshy, False),
                                         ("you", 350, b.you, False)):
                rect = QRectF(x, y, cw, ch)
                p.setPen(QPen(QColor(0, 0, 0, 90), 1.5, Qt.DashLine))
                p.setBrush(QColor(0, 0, 0, 40))
                p.drawRoundedRect(rect, 6, 6)
                c = cards[lane]
                if c is not None and not (c.name == "The Moon" and lane > 0 and cards[0] is c):
                    if c.name == "The Moon":
                        rect = QRectF(self._lane_x(0), y, self._lane_x(3) + cw - self._lane_x(0), ch)
                    marked = row == "you" and lane in self.sacs
                    draw_card(p, rect, c, faded=faded, marked=marked, hover=rect.contains(self.mouse))
                if row == "you":
                    self.hits.append((QRectF(x, y, cw, ch), lambda lane=lane: self.click_lane(lane)))
                if self.flash and self.flash[0] in ("hit", "face"):
                    _k, side, src, tgt, power = self.flash
                    if (row == ("you" if side == "you" else "leshy") and lane == src):
                        p.setPen(QPen(QColor("#FFE36E"), 3))
                        p.setBrush(Qt.NoBrush)
                        p.drawRoundedRect(QRectF(x - 3, y - 3, cw + 6, ch + 6), 8, 8)
        if self.flash and self.flash[0] in ("hit", "face"):
            _k, side, src, tgt, power = self.flash
            f2 = QFont("Georgia")
            f2.setPixelSize(30)
            f2.setBold(True)
            p.setFont(f2)
            p.setPen(QColor("#E0402A"))
            ty = (182 if side == "you" else 350) + 60
            if _k == "face":
                ty = 10 if side == "you" else 520
            p.drawText(QRectF(self._lane_x(tgt), ty, cw, 40), Qt.AlignCenter, f"-{power}")
        # the scale, candles, bones
        self._draw_scale(p, b, 30, 80)
        self._candles(p, 50, 330)
        f.setPixelSize(17)
        p.setFont(f)
        p.setPen(QColor("#EFE6D2"))
        p.drawText(QRectF(20, 390, 200, 24), Qt.AlignLeft, f"🦴 Bones: {b.bones}")
        if b.boss:
            p.drawText(QRectF(20, 416, 220, 24), Qt.AlignLeft, f"{b.boss} - phase {b.phase}")
        # piles and the bell
        rx = self._lane_x(3) + cw + 40
        deck_r, sq_r = QRectF(rx, 182, 90, 122), QRectF(rx + 104, 182, 90, 122)
        glow = b.can_draw() and self.anim is None
        for rect, label, count, action in ((deck_r, "Deck", len(b.deck), lambda: b.draw("deck")),
                                           (sq_r, "Squirrels", b.squirrels, lambda: b.draw("squirrel"))):
            p.setPen(QPen(QColor("#C9A227") if glow else INK, 2))
            p.setBrush(QColor("#5A3E2A") if label == "Deck" else QColor("#6A5A3A"))
            p.drawRoundedRect(rect, 6, 6)
            f.setPixelSize(13)
            p.setFont(f)
            p.setPen(QColor("#EFE6D2"))
            p.drawText(rect.adjusted(0, 6, 0, 0), Qt.AlignHCenter | Qt.AlignTop, label)
            ef = QFont(EMOJI)
            ef.setPixelSize(34)
            p.setFont(ef)
            p.drawText(rect, Qt.AlignCenter, "🂠" if label == "Deck" else "🐿️")
            p.setFont(f)
            p.drawText(rect.adjusted(0, 0, 0, -6), Qt.AlignHCenter | Qt.AlignBottom, str(count))
            if glow and count:
                self.hits.append((rect, action))
        bell = QRectF(rx + 20, 340, 154, 60)
        if self.anim is None and not b.over:
            self._button(p, bell, "🔔 Ring the bell", self.ring_bell, big=True)
        # the hand
        n = len(b.hand)
        hw, hh = 96, 130
        span = min(self.width() - 260, n * (hw + 6))
        step = (span - hw) / max(1, n - 1) if n > 1 else 0
        x0 = 240 + (self.width() - 260 - span) / 2
        for i, card in enumerate(b.hand):
            rect = QRectF(x0 + i * step, self.height() - hh - 44 - (14 if i == self.sel else 0), hw, hh)
            draw_card(p, rect, card, selected=i == self.sel, hover=rect.contains(self.mouse))
            self.hits.append((rect, lambda i=i: self.click_hand(i)))
        if b.log and self.prompt == "":
            self.prompt = b.log[-1]

    def _draw_scale(self, p, b, x, y):
        w = 170
        tilt = max(-5, min(5, b.scale)) / 5 * 18                     # + : toward Leshy's side (right pan down)
        cx, cy = x + w / 2, y + 40
        p.setPen(QPen(QColor("#B89A5A"), 3))
        p.drawLine(QPointF(cx, cy), QPointF(cx, cy + 120))
        ang = math.radians(tilt)
        lx, ly = cx - math.cos(ang) * 70, cy - math.sin(ang) * 70
        rx, ry = cx + math.cos(ang) * 70, cy + math.sin(ang) * 70
        p.drawLine(QPointF(lx, ly), QPointF(rx, ry))
        f = QFont("Georgia")
        f.setPixelSize(12)
        p.setFont(f)
        for px, py, label, teeth in ((lx, ly, "You", max(0, -b.scale)), (rx, ry, "Leshy", max(0, b.scale))):
            p.setPen(QPen(QColor("#B89A5A"), 1.5))
            p.drawLine(QPointF(px, py), QPointF(px - 18, py + 34))
            p.drawLine(QPointF(px, py), QPointF(px + 18, py + 34))
            p.setBrush(QColor("#5A4430"))
            p.drawChord(QRectF(px - 24, py + 22, 48, 26), 180 * 16, 180 * 16)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#F2EEE2"))
            for k in range(min(teeth, 8)):
                p.drawRect(QRectF(px - 16 + (k % 4) * 8, py + 26 + (k // 4) * 6, 5, 5))
            p.setPen(QColor("#EFE6D2"))
            p.drawText(QRectF(px - 30, py + 50, 60, 16), Qt.AlignCenter, label)
        p.setPen(QColor("#EFE6D2"))
        p.drawText(QRectF(x, y, w, 20), Qt.AlignCenter,
                   f"The scale: {abs(b.scale)} {'his way' if b.scale > 0 else 'your way' if b.scale < 0 else ''}")

    # the places on the map
    def _cards_row(self, p, cards, y, action, w=128, h=176, gap=34, marked=()):
        n = len(cards)
        x0 = (self.width() - (n * w + (n - 1) * gap)) / 2 + 100
        for i, c in enumerate(cards):
            rect = QRectF(x0 + i * (w + gap), y, w, h)
            draw_card(p, rect, c, hover=rect.contains(self.mouse), selected=i in marked)
            self.hits.append((rect, lambda i=i: action(i)))
        return x0

    def _draw_choice(self, p):
        self._side_panel(p)
        self._title_text(p, "Choose a creature", 60, 30)

        def take(i):
            self.run["deck"].append(dict(self.offer[i]))
            self.prompt = "It joins your deck."
            self.finish_node()
        self._cards_row(p, self.offer, 200, take)

    def _draw_cost(self, p):
        self._side_panel(p)
        self._title_text(p, "Choose by cost", 60, 30)
        n = len(self.offer)
        w, h, gap = 128, 176, 34
        x0 = (self.width() - (n * w + (n - 1) * gap)) / 2 + 100
        for i, (kind, icon) in enumerate(self.offer):
            rect = QRectF(x0 + i * (w + gap), 200, w, h)
            draw_card(p, rect, None, back=icon, hover=rect.contains(self.mouse))

            def take(kind=kind):
                card = card_for_cost(kind, self.rng, self.deathcards)
                self.run["deck"].append(card)
                self.prompt = f"It was {card['name']}. It joins your deck."
                self.finish_node()
            self.hits.append((rect, take))

    def _deck_grid(self, p, action, y0=110, marked=(), only=None):
        deck = self.run["deck"]
        w, h, gap = 96, 130, 12
        cols = max(1, int((self.width() - 260) // (w + gap)))
        for k, c in enumerate(deck):
            if only is not None and not only(c):
                continue
            rect = QRectF(240 + (k % cols) * (w + gap), y0 + (k // cols) * (h + gap), w, h)
            draw_card(p, rect, c, selected=k in marked, hover=rect.contains(self.mouse))
            if action is not None:
                self.hits.append((rect, lambda k=k: action(k)))

    def _draw_deck(self, p):
        self._title_text(p, "Your deck", 40, 28)
        self._deck_grid(p, None)
        self._button(p, QRectF(20, 60, 150, 34), "Back", lambda: setattr(self, "screen", self.back_to))

    def _draw_campfire(self, p):
        self._side_panel(p)
        camp = self.camp
        g = QRadialGradient(self.width() / 2 + 100, 90, 90)
        flick = math.sin(self.t * 8) * 6
        g.setColorAt(0, QColor(255, 210, 120, 220))
        g.setColorAt(1, QColor(255, 90, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(QPointF(self.width() / 2 + 100, 90), 80 + flick, 70 + flick)
        if camp["card"] is None:
            self._title_text(p, "Choose a creature to warm by the fire", 160, 22)

            def choose(k):
                camp["card"] = k
                self.prompt = "\"Will it be its strength, or its hide?\""
            self._deck_grid(p, choose, y0=220)
            return
        k = camp["card"]
        card = self.run["deck"][k]
        draw_card(p, QRectF(self.width() / 2 + 36, 180, 128, 176), card)

        def warm(what):
            if camp["times"] >= 1 and self.rng.random() < 0.34:
                self.run["deck"].pop(k)
                self.prompt = "The survivors could not help themselves. They ate it."
                self.finish_node()
                return
            card[what] = card.get(what, 0) + (1 if what == "power" else 2)
            camp["times"] += 1
            self.prompt = "It grows stronger by the fire." if what == "power" else "It grows hardier by the fire."
        x = self.width() / 2 - 60
        label = "Warm it again (risky)" if camp["times"] else "Warm it"
        self._button(p, QRectF(x, 380, 170, 40), f"{label}: +1 power", lambda: warm("power"))
        self._button(p, QRectF(x + 180, 380, 170, 40), f"{label}: +2 health", lambda: warm("health"))
        if camp["times"]:
            self._button(p, QRectF(x + 90, 432, 170, 40), "Leave the fire", self.finish_node)

    def _draw_stones(self, p):
        self._side_panel(p)
        if not self.pick:
            self._title_text(p, "Choose a creature to sacrifice for its sigil", 50, 22)

            def victim(k):
                if not info(self.run["deck"][k])[5]:
                    self.prompt = "That creature has no sigil to give."
                    return
                self.pick = [k]
                self.prompt = "Now choose who receives it."
            self._deck_grid(p, victim, only=None)
            self._button(p, QRectF(20, 220, 150, 34), "Walk past", self.finish_node)
            return
        self._title_text(p, "Choose who receives the sigil", 50, 22)
        v = self.pick[0]

        def receive(k):
            if k == v:
                return
            deck = self.run["deck"]
            sig = info(deck[v])[5][0]
            target = deck[k]
            if sig in info(target)[5]:
                self.prompt = "It already bears that sigil."
                return
            target["sigils"] = target.get("sigils", []) + [sig]
            deck.pop(v)
            self.prompt = f"The {sig} passes on. The stones are satisfied."
            self.finish_node()
        self._deck_grid(p, receive, marked=(v,))

    def _draw_fungi(self, p):
        self._side_panel(p)
        deck = self.run["deck"]
        names = [c["name"] for c in deck if not c.get("custom")]
        twins = sorted({n for n in names if names.count(n) >= 2 and n != "Squirrel"})
        if not twins:
            self._title_text(p, "You have no two of a kind.", 120, 24)
            self.prompt = "\"Come back when you have twins.\""
            self._button(p, QRectF(self.width() / 2 + 20, 200, 160, 40), "Leave", self.finish_node)
            return
        self._title_text(p, "Choose a pair to fuse", 50, 24)

        def fuse(i):
            name = twins[i]
            ks = [k for k, c in enumerate(deck) if c["name"] == name and not c.get("custom")][:2]
            a, b = deck[ks[0]], deck[ks[1]]
            _e, _bl, _bo, pa, ha, sa = info(a)
            _e, _bl, _bo, pb, hb, sb = info(b)
            base = CARDS[name]
            merged = spec(name, power=pa + pb - base[3], health=ha + hb - base[4],
                          sigils=[s for s in dict.fromkeys(sa + sb) if s not in base[5]])
            deck.pop(ks[1])
            deck[ks[0]] = merged
            self.prompt = f"The two {name}s become one."
            self.finish_node()
        self._cards_row(p, [spec(n) for n in twins], 200, fuse)

    def _draw_death(self, p):
        """Leave a Deathcard: one card's cost, another's power and health, a third's sigils."""
        steps = ["Take this creature's cost", "Take this creature's power and health", "Take this creature's sigils"]
        self._title_text(p, steps[min(2, len(self.pick))], 40, 24)

        def take(k):
            if k not in self.pick:
                self.pick.append(k)
            if len(self.pick) == 3:
                self._make_deathcard()
        self._deck_grid(p, take, marked=self.pick)

    def _make_deathcard(self):
        deck = self.run["deck"]
        a, b2, c = (info(deck[k]) for k in self.pick)
        name = "".join(self.rng.choice(SYLLABLES) for _ in range(2)).title()
        card = spec(name, custom={"name": name, "emoji": b2[0], "blood": a[1], "bones": a[2], "power": b2[3],
                                  "health": b2[4], "sigils": c[5][:2]})
        self.deathcards = (self.deathcards + [card])[-12:]
        self._save("deathcards.json", self.deathcards)
        self.made = card
        self.pick = []
        self.run = None
        self.screen = "made"
        self.prompt = f"{name} will remember you."

    def _draw_made(self, p):
        self._title_text(p, "Your Deathcard", 60, 30)
        draw_card(p, QRectF(self.width() / 2 - 64, 140, 128, 176), self.made)
        f = QFont("Georgia")
        f.setPixelSize(15)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(QColor("#B8A27A"))
        p.drawText(QRectF(0, 330, self.width(), 50), Qt.AlignCenter,
                   "It will wait in the woods for whoever comes next. Leshy may play it against you.")
        self._button(p, QRectF(self.width() / 2 - 110, 400, 220, 46), "Begin again", self.new_run, big=True)

    def _draw_victory(self, p):
        self._title_text(p, "You have beaten Leshy", self.height() * 0.25, 40)
        f = QFont("Georgia")
        f.setPixelSize(16)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(QColor("#B8A27A"))
        p.drawText(QRectF(0, self.height() * 0.25 + 70, self.width(), 60), Qt.AlignCenter,
                   "The Moon is broken. Leshy lowers his eyes, and the candlelight steadies.\n"
                   "\"...Well played.\"")
        self._button(p, QRectF(self.width() / 2 - 110, self.height() * 0.55, 220, 46), "Play again", self.new_run,
                     big=True)

    def closeEvent(self, event):
        if self.run and self.battle is None and self.screen not in ("death",):
            self._save("run.json", self.run)
        self.timer.stop()
        self.combat_timer.stop()
        event.accept()


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = Cabin(desktop)
        win = host.window(desktop, TITLE, body, scry_icon(), (1000, 700))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.close()
