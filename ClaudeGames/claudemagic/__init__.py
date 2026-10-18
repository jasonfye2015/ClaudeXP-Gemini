"""Claude and Magic: a grid-based dungeon crawler ("blobber") in the line of Wizardry, Might and Magic, The Bard's Tale
and Eye of the Beholder. A party of four - Knight, Rogue, Cleric and Mage - moves as one through twenty floors of
stone mazes, a square and a quarter-turn at a time, with an automap filling in as they go. Chests and fallen monsters
give weapons, armor, potions and gold; a ladder on every floor leads deeper. After floors 5, 10 and 15 there's a
merchant's camp (buy, sell, rest, raise the fallen). The Lich King waits on floor 20. It's a roguelike: when the whole
party falls, the run is over and the next one starts afresh. The deepest runs go in the Hall of Fame (shared saves).

Keys: Up/W forward, Down/S back, Left/A and Right/D turn, Q/E sidestep, Space use (chest, ladder), I inventory.
In a fight: F fight, C cast, P potion, R run."""
import json
import math
import random
import struct
import wave

from PySide6.QtCore import QPointF, QRectF, Qt, QUrl
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QStackedWidget,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from claudecore import host

SAVES = host.saves("claudemagic")
RUN_FILE = SAVES / "run.json"
FAME_FILE = SAVES / "hall_of_fame.json"
VIEW_W, VIEW_H = 480, 300
DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]               # north, east, south, west
DIR_NAMES = "NESW"
PLANES = [1.0, 0.56, 0.32, 0.19, 0.11, 0.065]           # how big each step away looks
LAST_FLOOR = 20
CAMP_AFTER = (5, 10, 15)

CLASSES = {"Knight": dict(hp=34, mp=0, atk=6, df=3), "Rogue": dict(hp=24, mp=0, atk=5, df=2),
           "Cleric": dict(hp=26, mp=12, atk=4, df=2), "Mage": dict(hp=18, mp=14, atk=3, df=1)}
WEAPONS = ["Dagger", "Short Sword", "Mace", "Long Sword", "Battle Axe", "War Hammer", "Bastard Sword", "Rune Blade",
           "Flamberge", "Mithril Sword", "Dragonslayer", "Claudebrand"]
ARMORS = ["Padded Vest", "Leather Armor", "Studded Leather", "Ring Mail", "Scale Mail", "Chain Mail", "Banded Mail",
          "Plate Mail", "Elven Mail", "Mithril Plate", "Dragon Scale", "Aegis of Claude"]
MONSTERS = [("Giant Rat", "#8A7058"), ("Kobold", "#B07040"), ("Skeleton", "#E0E0D0"), ("Goblin", "#5A9A40"),
            ("Zombie", "#7A9A70"), ("Orc", "#4A7A3A"), ("Ghoul", "#9AA0A0"), ("Dark Elf", "#5A4A8A"),
            ("Troll", "#3A6A50"), ("Wraith", "#6A7AA0"), ("Ogre", "#A08050"), ("Minotaur", "#7A4A30"),
            ("Gargoyle", "#707078"), ("Vampire", "#8A2030"), ("Demon", "#C03020"), ("Wyvern", "#407A70")]
BOSS = ("The Lich King", "#A0E0FF")


def magic_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(QRectF(1, 1, 30, 30), QColor("#1A1410"))
    p.setBrush(QColor("#6A5A48"))
    p.setPen(Qt.NoPen)
    p.drawPolygon(QPolygonF([QPointF(1, 1), QPointF(10, 8), QPointF(10, 24), QPointF(1, 31)]))
    p.drawPolygon(QPolygonF([QPointF(31, 1), QPointF(22, 8), QPointF(22, 24), QPointF(31, 31)]))
    p.setBrush(QColor("#4A3E32"))
    p.drawRect(QRectF(10, 8, 12, 16))
    p.setPen(QPen(QColor("#E8E8F0"), 2))
    p.drawLine(QPointF(9, 26), QPointF(23, 6))                    # a sword
    p.setPen(QPen(QColor("#F0C040"), 2))
    p.drawLine(QPointF(10, 20), QPointF(16, 24))
    p.end()
    return QIcon(pm)


# ---- sounds -------------------------------------------------------------------------------------------------------
def _write(path, samples, rate=22050):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", max(-32000, min(32000, int(s)))) for s in samples))


def _tones(notes, wave_kind="square", rate=22050, vol=5000):
    out = []
    for freq, length in notes:
        n = int(rate * length)
        for i in range(n):
            t = i / rate
            fade = (1 - i / n) ** 1.5
            if wave_kind == "sine":
                v = math.sin(2 * math.pi * freq * t)
            else:
                v = 1 if (t * freq) % 1 < 0.5 else -1
            out.append(v * vol * fade)
    return out


def _noise(length, vol, smooth, rate=22050, seed=1):
    rnd = random.Random(seed)
    out, last = [], 0.0
    n = int(rate * length)
    for i in range(n):
        last += (rnd.uniform(-1, 1) - last) * smooth
        out.append(last * vol * (1 - i / n))
    return out


def _make_sounds():
    folder = host.data("claudemagic") / "sounds"
    folder.mkdir(parents=True, exist_ok=True)
    recipes = {
        "step": lambda: _noise(0.09, 9000, 0.08, seed=3),
        "bump": lambda: _tones([(70, 0.12)], vol=7000),
        "chest": lambda: _tones([(392, 0.07), (523, 0.07), (659, 0.12)]),
        "hit": lambda: _noise(0.12, 14000, 0.5, seed=5),
        "hurt": lambda: _tones([(180, 0.06), (120, 0.1)], vol=6000),
        "spell": lambda: _tones([(f, 0.025) for f in range(400, 1600, 80)], "sine", vol=7000),
        "heal": lambda: _tones([(523, 0.07), (659, 0.07), (784, 0.07), (1047, 0.14)], "sine", vol=6000),
        "coin": lambda: _tones([(1319, 0.05), (1760, 0.12)]),
        "stairs": lambda: _tones([(392, 0.1), (330, 0.1), (262, 0.1), (196, 0.2)], "sine", vol=6000),
        "level": lambda: _tones([(523, 0.09), (659, 0.09), (784, 0.09), (1047, 0.09), (784, 0.09), (1047, 0.25)]),
        "death": lambda: _tones([(330, 0.2), (262, 0.2), (196, 0.25), (131, 0.5)], "sine", vol=7000),
        "victory": lambda: _tones([(523, 0.12), (523, 0.12), (523, 0.12), (659, 0.3), (587, 0.15), (784, 0.5)]),
        "monster": lambda: _tones([(110, 0.15), (98, 0.25)], vol=6000),
    }
    paths = {}
    for name, make in recipes.items():
        path = folder / f"{name}.wav"
        if not path.exists():
            _write(path, make())
        paths[name] = path
    ambient = folder / "ambient.wav"
    if not ambient.exists():                       # a dungeon: low drone, distant rumble, water dripping
        rate, secs = 22050, 8
        rnd = random.Random(11)
        rumble = _noise(secs, 2500, 0.01, seed=7)
        samples = []
        drips = sorted(rnd.uniform(0.3, secs - 0.4) for _ in range(5))
        for i in range(rate * secs):
            t = i / rate
            v = 900 * math.sin(2 * math.pi * 55 * t) * (0.7 + 0.3 * math.sin(2 * math.pi * 0.25 * t))
            v += 500 * math.sin(2 * math.pi * 82.5 * t)
            v += rumble[i] * (1 / max(0.05, (1 - i / (rate * secs))))
            for d in drips:
                if 0 <= t - d < 0.25:
                    k = t - d
                    v += 5000 * math.sin(2 * math.pi * (1800 - k * 2000) * k) * math.exp(-k * 25)
            samples.append(v)
        _write(ambient, samples)
    paths["ambient"] = ambient
    return paths


class Sounds:
    def __init__(self, parent):
        self.effects = {}
        try:
            from PySide6.QtMultimedia import QSoundEffect
            for name, path in _make_sounds().items():
                fx = QSoundEffect(parent)
                fx.setSource(QUrl.fromLocalFile(str(path)))
                fx.setVolume(0.22 if name == "ambient" else 0.5)
                if name == "ambient":
                    fx.setLoopCount(QSoundEffect.Infinite)
                self.effects[name] = fx
        except Exception:
            self.effects = {}

    def play(self, name):
        fx = self.effects.get(name)
        if fx is not None and not host.muted():
            fx.play()

    def ambience(self, on):
        fx = self.effects.get("ambient")
        if fx is None:
            return
        if on and not host.muted() and not fx.isPlaying():
            fx.play()
        elif not on:
            fx.stop()


# ---- the world ------------------------------------------------------------------------------------------------------
def make_item(floor, rnd, kind=None):
    kind = kind or rnd.choice(["weapon", "weapon", "armor", "armor", "potion", "potion", "potion"])
    if kind == "potion":
        roll = rnd.random()
        if roll < 0.12:
            return {"name": "Phoenix Feather", "kind": "revive", "power": 0, "value": 120}
        if roll < 0.4:
            return {"name": "Mana Potion", "kind": "mana", "power": 12 + floor, "value": 25}
        return {"name": "Healing Potion", "kind": "heal", "power": 20 + floor * 3, "value": 20}
    tier = max(0, min(11, (floor + rnd.randint(-2, 2)) * 12 // 21))
    names = WEAPONS if kind == "weapon" else ARMORS
    power = (tier + 1) * (2 if kind == "weapon" else 1) + rnd.randint(0, 2)
    bonus = rnd.random() < 0.15
    return {"name": names[tier] + (" +1" if bonus else ""), "kind": kind, "power": power + (2 if bonus else 0),
            "value": 15 * (tier + 1) ** 2 + (40 if bonus else 0)}


def make_floor(number):
    """A maze (recursive backtracker, with some extra openings), a start, a ladder, chests and monsters."""
    rnd = random.Random()
    size = min(17 + (number // 4) * 2, 27)
    grid = [[1] * size for _ in range(size)]
    stack = [(1, 1)]
    grid[1][1] = 0
    while stack:
        x, y = stack[-1]
        options = [(dx, dy) for dx, dy in DIRS if 0 < x + dx * 2 < size - 1 and 0 < y + dy * 2 < size - 1
                   and grid[y + dy * 2][x + dx * 2] == 1]
        if not options:
            stack.pop()
            continue
        dx, dy = rnd.choice(options)
        grid[y + dy][x + dx] = 0
        grid[y + dy * 2][x + dx * 2] = 0
        stack.append((x + dx * 2, y + dy * 2))
    for _ in range(size * size // 14):                            # loops, so it isn't a perfect maze
        x, y = rnd.randrange(1, size - 1), rnd.randrange(1, size - 1)
        if grid[y][x] == 1 and ((grid[y][x - 1] == 0 and grid[y][x + 1] == 0) or
                                (grid[y - 1][x] == 0 and grid[y + 1][x] == 0)):
            grid[y][x] = 0
    open_cells = [(x, y) for y in range(size) for x in range(size) if grid[y][x] == 0]
    start = (1, 1)
    # the ladder (or the boss) goes on the open square furthest from the start
    dist = {start: 0}
    queue = [start]
    for cell in queue:
        for dx, dy in DIRS:
            nxt = (cell[0] + dx, cell[1] + dy)
            if grid[nxt[1]][nxt[0]] == 0 and nxt not in dist:
                dist[nxt] = dist[cell] + 1
                queue.append(nxt)
    far = max(dist, key=dist.get)
    things = {}
    spare = [c for c in open_cells if c not in (start, far) and dist.get(c, 0) > 3]
    rnd.shuffle(spare)
    for _ in range(3 + number // 4):
        if spare:
            things[spare.pop()] = {"type": "chest", "gold": rnd.randint(10, 30) * number,
                                   "items": [make_item(number, rnd) for _ in range(rnd.randint(1, 2))]}
    for _ in range(5 + number // 2):
        if spare:
            things[spare.pop()] = {"type": "monsters", "group": monster_group(number, rnd)}
    if number == LAST_FLOOR:
        things[far] = {"type": "boss", "group": [boss_monster()]}
    else:
        things[far] = {"type": "ladder"}
    return {"number": number, "grid": grid, "pos": list(start), "facing": 2 if grid[2][1] == 0 else 1,
            "things": {f"{x},{y}": t for (x, y), t in things.items()}, "seen": []}


def monster_group(floor, rnd):
    top = min(len(MONSTERS) - 1, floor * len(MONSTERS) // LAST_FLOOR)
    name, colour = MONSTERS[rnd.randint(max(0, top - 2), top)]
    count = rnd.randint(1, 2 + floor // 6)
    level = floor
    return [{"name": name, "colour": colour, "hp": 8 + level * 6, "max": 8 + level * 6, "atk": 3 + level * 2,
             "df": level, "xp": 10 + level * 8, "gold": rnd.randint(2, 8) * level} for _ in range(count)]


def boss_monster():
    return {"name": BOSS[0], "colour": BOSS[1], "hp": 650, "max": 650, "atk": 46, "df": 18, "xp": 5000, "gold": 5000,
            "boss": True}


def new_party():
    party = []
    for cls, s in CLASSES.items():
        party.append({"name": cls, "cls": cls, "level": 1, "xp": 0, "hp": s["hp"], "max": s["hp"], "mp": s["mp"],
                      "maxmp": s["mp"], "atk": s["atk"], "df": s["df"],
                      "weapon": {"name": "Staff" if cls in ("Mage", "Cleric") else "Club", "kind": "weapon",
                                 "power": 1, "value": 5},
                      "armor": {"name": "Robes" if cls == "Mage" else "Tunic", "kind": "armor", "power": 0,
                                "value": 5}})
    return party


# ---- the game -----------------------------------------------------------------------------------------------------
class Dungeon(QWidget):
    """The painted part: the first-person view, the automap, the party and the message log."""

    def __init__(self, game):
        super().__init__()
        self.game = game
        self.setMinimumSize(820, 470)
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        if not self.game.key(event.key()):
            super().keyPressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#18120C"))
        g = self.game
        if g.mode == "title":
            self._title(p)
        else:
            self._view(p, QRectF(10, 10, VIEW_W, VIEW_H))
            self._automap(p, QRectF(VIEW_W + 22, 10, 288, 288))
            self._party(p, QRectF(10, VIEW_H + 18, 800, 72))
            self._log(p, QRectF(10, VIEW_H + 96, 800, self.height() - VIEW_H - 104))
        p.end()

    # ---- the first-person view --------------------------------------------------------------------------------
    def _view(self, p, area):
        g = self.game
        fl = g.floor
        p.save()
        p.setClipRect(area)
        p.translate(area.topLeft())
        cx, cy = VIEW_W / 2, VIEW_H / 2
        sky = QLinearGradient(0, 0, 0, cy)
        sky.setColorAt(0, QColor("#0C0A08"))
        sky.setColorAt(1, QColor("#2A2218"))
        p.fillRect(QRectF(0, 0, VIEW_W, cy), sky)
        ground = QLinearGradient(0, cy, 0, VIEW_H)
        ground.setColorAt(0, QColor("#2A241C"))
        ground.setColorAt(1, QColor("#5A4C3A"))
        p.fillRect(QRectF(0, cy, VIEW_W, VIEW_H - cy), ground)
        x0, y0 = fl["pos"]
        fdx, fdy = DIRS[fl["facing"]]
        rdx, rdy = DIRS[(fl["facing"] + 1) % 4]

        def tile(d, l):
            x, y = x0 + fdx * d + rdx * l, y0 + fdy * d + rdy * l
            if 0 <= y < len(fl["grid"]) and 0 <= x < len(fl["grid"]):
                return fl["grid"][y][x], (x, y)
            return 1, (x, y)

        def hw(k):
            return cx * PLANES[k]

        def hh(k):
            return cy * PLANES[k]

        for d in range(4, -1, -1):
            for l in (-2, 2, -1, 1, 0):
                wall, cell = tile(d, l)
                if wall:
                    shade = 1.0 - d * 0.17
                    if l != 0:                              # the side facing the middle
                        xa = cx + (2 * l + (1 if l < 0 else -1)) * hw(d)
                        xb = cx + (2 * l + (1 if l < 0 else -1)) * hw(d + 1)
                        poly = QPolygonF([QPointF(xa, cy - hh(d)), QPointF(xb, cy - hh(d + 1)),
                                          QPointF(xb, cy + hh(d + 1)), QPointF(xa, cy + hh(d))])
                        self._stone(p, poly, shade * 0.75, d, side=(xa, xb, d))
                    if d > 0:                               # the face toward us
                        rect = QRectF(cx + (2 * l - 1) * hw(d), cy - hh(d), 2 * hw(d), 2 * hh(d))
                        self._stone(p, QPolygonF(rect), shade, d, rect=rect)
                elif l == 0 and d > 0:
                    thing = fl["things"].get(f"{cell[0]},{cell[1]}")
                    if thing is not None and (d == 1 or not tile(d - 1, 0)[0]):
                        self._thing(p, thing, cx, cy, (PLANES[d] + PLANES[d + 1]) / 2, d)
        # a compass
        p.setPen(QColor("#E8D8A0"))
        p.setFont(QFont("Georgia", 11, QFont.Bold))
        p.drawText(QRectF(0, 4, VIEW_W, 20), Qt.AlignHCenter, f"{DIR_NAMES[fl['facing']]}   -   Floor {fl['number']}")
        p.restore()
        p.setPen(QPen(QColor("#8A6A3A"), 3))
        p.setBrush(Qt.NoBrush)
        p.drawRect(area.adjusted(-1, -1, 1, 1))
        if g.mode == "combat":
            self._enemies(p, area)

    def _stone(self, p, poly, shade, d, rect=None, side=None):
        base = QColor(int(118 * shade), int(104 * shade), int(88 * shade))
        p.setPen(QPen(QColor(int(40 * shade), int(34 * shade), int(28 * shade)), 1))
        p.setBrush(base)
        p.drawPolygon(poly)
        p.setPen(QPen(QColor(int(70 * shade), int(60 * shade), int(50 * shade)), 1))
        if rect is not None:                                  # mortar lines and staggered joints
            rows = 5
            for i in range(1, rows):
                y = rect.top() + rect.height() * i / rows
                p.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            for i in range(rows):
                y1, y2 = rect.top() + rect.height() * i / rows, rect.top() + rect.height() * (i + 1) / rows
                for j in range(4):
                    x = rect.left() + rect.width() * (j + (0.5 if i % 2 else 0)) / 4
                    if rect.left() < x < rect.right():
                        p.drawLine(QPointF(x, y1), QPointF(x, y2))
        elif side is not None:
            xa, xb, k = side
            cy = VIEW_H / 2
            for i in range(1, 5):
                f = i / 5
                ya = cy - cy * PLANES[k] + 2 * cy * PLANES[k] * f
                yb = cy - cy * PLANES[k + 1] + 2 * cy * PLANES[k + 1] * f
                p.drawLine(QPointF(xa, ya), QPointF(xb, yb))

    def _thing(self, p, thing, cx, cy, scale, d):
        s = scale * 200
        floor_y = cy + cy * scale
        fade = 1.0 - d * 0.15
        if thing["type"] == "chest":
            box = QRectF(cx - s * 0.35, floor_y - s * 0.4, s * 0.7, s * 0.4)
            p.setPen(QPen(QColor("#2A1A08"), 1))
            p.setBrush(QColor(int(140 * fade), int(90 * fade), int(40 * fade)))
            p.drawRect(box)
            p.setBrush(QColor(int(160 * fade), int(110 * fade), int(50 * fade)))
            p.drawRect(QRectF(box.left(), box.top() - s * 0.12, box.width(), s * 0.12))
            p.setBrush(QColor("#D8B040"))
            p.drawRect(QRectF(cx - s * 0.05, box.top() - s * 0.04, s * 0.1, s * 0.1))
        elif thing["type"] == "ladder":
            hole = QRectF(cx - s * 0.4, floor_y - s * 0.1, s * 0.8, s * 0.14)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#050403"))
            p.drawEllipse(hole)
            p.setPen(QPen(QColor(int(150 * fade), int(110 * fade), int(60 * fade)), max(1, s / 40)))
            p.drawLine(QPointF(cx - s * 0.15, floor_y - s * 0.9), QPointF(cx - s * 0.15, floor_y))
            p.drawLine(QPointF(cx + s * 0.15, floor_y - s * 0.9), QPointF(cx + s * 0.15, floor_y))
            for i in range(5):
                y = floor_y - s * 0.85 + i * s * 0.18
                p.drawLine(QPointF(cx - s * 0.15, y), QPointF(cx + s * 0.15, y))
        elif thing["type"] in ("monsters", "boss"):
            self._monster(p, thing["group"][0], cx, floor_y, s * (1.4 if thing["type"] == "boss" else 1.0), fade)

    def _monster(self, p, m, cx, floor_y, s, fade=1.0):
        c = QColor(m["colour"])
        c = QColor(int(c.red() * fade), int(c.green() * fade), int(c.blue() * fade))
        body = QRectF(cx - s * 0.3, floor_y - s * 0.95, s * 0.6, s * 0.8)
        p.setPen(QPen(c.darker(180), 1))
        p.setBrush(c)
        p.drawRoundedRect(body, s * 0.2, s * 0.2)
        p.drawEllipse(QRectF(cx - s * 0.2, floor_y - s * 1.2, s * 0.4, s * 0.38))   # head
        p.setBrush(QColor("#FFE040") if not m.get("boss") else QColor("#40F0FF"))
        p.setPen(Qt.NoPen)
        for ex in (-0.08, 0.08):
            p.drawEllipse(QRectF(cx + s * ex - s * 0.035, floor_y - s * 1.06, s * 0.07, s * 0.06))
        p.setBrush(c.darker(130))
        p.drawRect(QRectF(cx - s * 0.42, floor_y - s * 0.8, s * 0.12, s * 0.45))           # arms
        p.drawRect(QRectF(cx + s * 0.3, floor_y - s * 0.8, s * 0.12, s * 0.45))
        if m.get("boss"):                                                                # a crown
            p.setBrush(QColor("#F0C030"))
            p.drawPolygon(QPolygonF([QPointF(cx - s * 0.2, floor_y - s * 1.18), QPointF(cx - s * 0.15, floor_y - s * 1.34),
                                     QPointF(cx - s * 0.05, floor_y - s * 1.22), QPointF(cx, floor_y - s * 1.36),
                                     QPointF(cx + s * 0.05, floor_y - s * 1.22), QPointF(cx + s * 0.15, floor_y - s * 1.34),
                                     QPointF(cx + s * 0.2, floor_y - s * 1.18)]))

    def _enemies(self, p, area):
        foes = [m for m in self.game.foes if m["hp"] > 0]
        p.fillRect(area, QColor(0, 0, 0, 90))
        n = max(1, len(foes))
        for i, m in enumerate(foes):
            x = area.left() + area.width() * (i + 0.5) / n
            s = 150 if not m.get("boss") else 210
            self._monster(p, m, x, area.bottom() - 30, s)
            bar = QRectF(x - 40, area.bottom() - 22, 80, 7)
            p.fillRect(bar, QColor("#401010"))
            p.fillRect(QRectF(bar.left(), bar.top(), bar.width() * m["hp"] / m["max"], bar.height()), QColor("#E03030"))
            p.setPen(QColor("white"))
            p.setFont(QFont("Georgia", 9, QFont.Bold))
            p.drawText(QRectF(x - 70, area.bottom() - 14, 140, 14), Qt.AlignCenter, m["name"])

    # ---- the automap ------------------------------------------------------------------------------------------
    def _automap(self, p, area):
        fl = self.game.floor
        size = len(fl["grid"])
        cell = area.width() / size
        p.fillRect(area, QColor("#E8DCC0"))                       # graph paper
        p.setPen(QPen(QColor("#C8B898"), 1))
        for i in range(size + 1):
            p.drawLine(QPointF(area.left() + i * cell, area.top()), QPointF(area.left() + i * cell, area.bottom()))
            p.drawLine(QPointF(area.left(), area.top() + i * cell), QPointF(area.right(), area.top() + i * cell))
        seen = set(map(tuple, fl["seen"]))
        p.setPen(Qt.NoPen)
        for (x, y) in seen:
            r = QRectF(area.left() + x * cell, area.top() + y * cell, cell, cell)
            p.setBrush(QColor("#3A3028") if fl["grid"][y][x] else QColor("#F8F0DC"))
            p.drawRect(r)
            thing = fl["things"].get(f"{x},{y}")
            if thing is not None and not fl["grid"][y][x]:
                colour = {"chest": "#C08030", "ladder": "#3060C0", "monsters": "#C03030", "boss": "#8030C0"}
                p.setBrush(QColor(colour[thing["type"]]))
                p.drawEllipse(r.adjusted(cell * 0.2, cell * 0.2, -cell * 0.2, -cell * 0.2))
        x, y = fl["pos"]
        c = QPointF(area.left() + (x + 0.5) * cell, area.top() + (y + 0.5) * cell)
        dx, dy = DIRS[fl["facing"]]
        p.setBrush(QColor("#20A040"))
        p.drawPolygon(QPolygonF([QPointF(c.x() + dx * cell * 0.45, c.y() + dy * cell * 0.45),
                                 QPointF(c.x() - dy * cell * 0.35 - dx * cell * 0.3, c.y() + dx * cell * 0.35 - dy * cell * 0.3),
                                 QPointF(c.x() + dy * cell * 0.35 - dx * cell * 0.3, c.y() - dx * cell * 0.35 - dy * cell * 0.3)]))
        p.setPen(QPen(QColor("#8A6A3A"), 3))
        p.setBrush(Qt.NoBrush)
        p.drawRect(area.adjusted(-1, -1, 1, 1))

    # ---- the party and the log -------------------------------------------------------------------------------
    def _party(self, p, area):
        w = area.width() / 4
        for i, m in enumerate(self.game.party):
            r = QRectF(area.left() + i * w + 2, area.top(), w - 4, area.height())
            dead = m["hp"] <= 0
            p.setPen(QPen(QColor("#8A6A3A"), 2))
            p.setBrush(QColor("#2A2018") if not dead else QColor("#2A1010"))
            p.drawRect(r)
            p.setPen(QColor("#F0E0B0") if not dead else QColor("#A06060"))
            p.setFont(QFont("Georgia", 10, QFont.Bold))
            p.drawText(r.adjusted(6, 3, -6, 0), Qt.AlignLeft | Qt.AlignTop,
                       f"{m['cls']}  Lv {m['level']}" + ("  (fallen)" if dead else ""))
            p.setFont(QFont("Tahoma", 7))
            p.setPen(QColor("#B0A080"))
            p.drawText(r.adjusted(6, 19, -6, 0), Qt.AlignLeft | Qt.AlignTop,
                       f"{m['weapon']['name']} / {m['armor']['name']}")
            self._bar(p, QRectF(r.left() + 6, r.top() + 36, r.width() - 12, 9), m["hp"], m["max"], "#C02828", "HP")
            if m["maxmp"]:
                self._bar(p, QRectF(r.left() + 6, r.top() + 52, r.width() - 12, 9), m["mp"], m["maxmp"], "#2848C0", "MP")

    @staticmethod
    def _bar(p, r, v, top, colour, label):
        p.fillRect(r, QColor("#100C08"))
        p.fillRect(QRectF(r.left(), r.top(), r.width() * max(0, v) / max(1, top), r.height()), QColor(colour))
        p.setPen(QColor("white"))
        p.setFont(QFont("Tahoma", 7, QFont.Bold))
        p.drawText(r, Qt.AlignCenter, f"{label} {max(0, v)}/{top}")

    def _log(self, p, area):
        p.fillRect(area, QColor("#0E0A06"))
        p.setPen(QPen(QColor("#8A6A3A"), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRect(area)
        p.setFont(QFont("Courier New", 9))
        lines = self.game.messages[-max(1, int(area.height() // 15)):]
        for i, line in enumerate(lines):
            p.setPen(QColor("#F0E0B0") if i == len(lines) - 1 else QColor("#A09070"))
            p.drawText(QRectF(area.left() + 8, area.top() + 4 + i * 15, area.width() - 16, 15), Qt.AlignLeft, line)
        p.setPen(QColor("#E8C870"))
        p.setFont(QFont("Georgia", 10, QFont.Bold))
        g = self.game
        p.drawText(area.adjusted(0, 4, -10, 0), Qt.AlignRight | Qt.AlignTop,
                   f"Gold: {g.gold:,}   Potions: {sum(1 for i in g.bag if i['kind'] in ('heal', 'mana', 'revive'))}")

    def _title(self, p):
        r = self.rect()
        p.setPen(QColor("#E8C870"))
        p.setFont(QFont("Georgia", 40, QFont.Bold))
        p.drawText(QRectF(0, 40, r.width(), 70), Qt.AlignCenter, "Claude and Magic")
        p.setFont(QFont("Georgia", 13, -1, True))
        p.setPen(QColor("#B0A080"))
        p.drawText(QRectF(0, 110, r.width(), 24), Qt.AlignCenter,
                   "Twenty floors down, the Lich King waits. Four go in together.")
        p.setFont(QFont("Georgia", 12, QFont.Bold))
        p.setPen(QColor("#E03030"))
        p.drawText(QRectF(0, 160, r.width(), 22), Qt.AlignCenter, "- Hall of Fame -")
        p.setFont(QFont("Courier New", 10, QFont.Bold))
        fame = self.game.fame
        if not fame:
            p.setPen(QColor("#807060"))
            p.drawText(QRectF(0, 186, r.width(), 20), Qt.AlignCenter, "No party has gone down yet.")
        for i, e in enumerate(fame[:10]):
            p.setPen(QColor("#F0E0B0"))
            line = f"{i + 1:>2}. {e['name'][:14]:<14} {'SLEW THE LICH KING' if e.get('won') else 'floor ' + str(e['floor']):<18}" \
                   f" {e['gold']:>7,} gold  {e['date']}"
            p.drawText(QRectF(0, 186 + i * 20, r.width(), 20), Qt.AlignCenter, line)
        p.setPen(QColor("#F0E0B0"))
        p.setFont(QFont("Georgia", 14, QFont.Bold))
        p.drawText(QRectF(0, r.height() - 60, r.width(), 24), Qt.AlignCenter,
                   self.game.title_note or "Press Enter (or New Expedition) to begin")


class ClaudeAndMagic(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.sounds = Sounds(self)
        self.fame = self._load(FAME_FILE, [])
        self.mode = "title"                 # title, explore, combat, camp, over
        self.title_note = ""
        self.messages = []
        self.party, self.bag, self.gold, self.floor, self.foes = [], [], 0, None, []
        self.foe_key = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.pages = QStackedWidget()
        lay.addWidget(self.pages)
        self.view = Dungeon(self)
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(0, 0, 0, 6)
        col.addWidget(self.view, 1)
        self.buttons = QHBoxLayout()
        self.buttons.setContentsMargins(10, 0, 10, 0)
        col.addLayout(self.buttons)
        self.pages.addWidget(page)
        self.bag_page = self._bag_page()
        self.pages.addWidget(self.bag_page)
        self.setStyleSheet("QPushButton { background: #3A2C1C; color: #F0E0B0; border: 1px solid #8A6A3A; padding: 5px 9px;"
                           " font: bold 11px Georgia; } QPushButton:hover { background: #5A442A; }"
                           " QPushButton:disabled { color: #6A5A40; } QListWidget { background: #1A140E;"
                           " color: #F0E0B0; font: 11px Georgia; border: 1px solid #8A6A3A; }"
                           " QListWidget::item:selected { background: #5A442A; } QLabel { color: #F0E0B0; font: 12px Georgia; }")
        saved = self._load(RUN_FILE, None)
        if saved:
            self._restore(saved)
        self._set_buttons()

    # ---- saving ----------------------------------------------------------------------------------------------
    @staticmethod
    def _load(path, default):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return default

    def save_run(self):
        data = {"party": self.party, "bag": self.bag, "gold": self.gold, "floor": self.floor, "mode": self.mode}
        try:
            RUN_FILE.write_text(json.dumps(data), encoding="utf-8")
        except OSError:
            pass

    def _restore(self, data):
        self.party, self.bag, self.gold, self.floor = data["party"], data["bag"], data["gold"], data["floor"]
        self.mode = "camp" if data.get("mode") == "camp" else "explore"
        self.say("You take up the expedition where you left it.")
        self.sounds.ambience(self.mode == "explore")

    def end_run(self, won):
        entry = {"name": host.user_name() or "Adventurer", "floor": self.floor["number"], "gold": self.gold, "won": won,
                 "date": host.now().strftime("%m/%d/%Y")}
        self.fame.append(entry)
        self.fame.sort(key=lambda e: (-int(e.get("won", False)), -e["floor"], -e["gold"]))
        self.fame = self.fame[:10]
        try:
            FAME_FILE.write_text(json.dumps(self.fame, indent=1), encoding="utf-8")
            RUN_FILE.unlink(missing_ok=True)
        except OSError:
            pass
        self.sounds.ambience(False)
        self.sounds.play("victory" if won else "death")
        self.title_note = ("The Lich King is no more. The party returns as legends!  (Enter for a new expedition)" if won
                           else f"The party fell on floor {self.floor['number']}. Their story ends here.  (Enter to try again)")
        self.mode = "title"
        self._set_buttons()

    # ---- buttons ---------------------------------------------------------------------------------------------
    def _set_buttons(self):
        while self.buttons.count():
            w = self.buttons.takeAt(0).widget()
            if w is not None:
                w.hide()                                  # (gone now, not when Qt gets round to deleting it)
                w.deleteLater()
        sets = {"title": [("New Expedition", self.new_game)],
                "explore": [("◄ Turn", lambda: self.turn(-1)), ("▲ Forward", lambda: self.move(0)),
                            ("▼ Back", lambda: self.move(2)), ("Turn ►", lambda: self.turn(1)),
                            ("Use (Space)", self.use), ("Inventory (I)", self.open_bag)],
                "combat": [("Fight (F)", lambda: self.combat_round("fight")), ("Cast (C)", lambda: self.combat_round("cast")),
                           ("Potion (P)", lambda: self.combat_round("potion")), ("Run (R)", lambda: self.combat_round("run"))],
                "camp": [("Merchant", self.open_merchant), ("Rest (20 gold)", self.rest),
                         ("Raise the fallen", self.raise_dead), ("Inventory", self.open_bag),
                         ("Go deeper", self.leave_camp)]}
        for text, slot in sets.get(self.mode, []):
            b = QPushButton(text)
            b.setFocusPolicy(Qt.NoFocus)
            b.clicked.connect(slot)
            self.buttons.addWidget(b)
        self.view.update()
        self.view.setFocus()

    def say(self, text):
        self.messages.append(text)
        self.messages = self.messages[-60:]
        self.view.update()

    # ---- starting --------------------------------------------------------------------------------------------
    def new_game(self):
        self.party, self.bag, self.gold = new_party(), [make_item(1, random.Random(), "potion") for _ in range(2)], 30
        self.messages = []
        self.enter_floor(1)
        self.say("Four adventurers climb down into the dark. Somewhere below, the Lich King stirs.")

    def enter_floor(self, number):
        self.floor = make_floor(number)
        self.mode = "explore"
        self._look()
        self.save_run()
        self.sounds.ambience(True)
        self._set_buttons()
        self.say(f"Floor {number}." + ("  A terrible cold rises from somewhere ahead..." if number == LAST_FLOOR else ""))

    # ---- moving ----------------------------------------------------------------------------------------------
    def key(self, k):
        if self.mode == "title" and k in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.new_game()
        elif self.mode == "explore":
            actions = {Qt.Key_Up: lambda: self.move(0), Qt.Key_W: lambda: self.move(0), Qt.Key_Down: lambda: self.move(2),
                       Qt.Key_S: lambda: self.move(2), Qt.Key_Left: lambda: self.turn(-1), Qt.Key_A: lambda: self.turn(-1),
                       Qt.Key_Right: lambda: self.turn(1), Qt.Key_D: lambda: self.turn(1), Qt.Key_Q: lambda: self.move(3),
                       Qt.Key_E: lambda: self.move(1), Qt.Key_Space: self.use, Qt.Key_I: self.open_bag}
            if k not in actions:
                return False
            actions[k]()
        elif self.mode == "combat":
            actions = {Qt.Key_F: "fight", Qt.Key_C: "cast", Qt.Key_P: "potion", Qt.Key_R: "run"}
            if k not in actions:
                return False
            self.combat_round(actions[k])
        else:
            return False
        return True

    def turn(self, way):
        self.floor["facing"] = (self.floor["facing"] + way) % 4
        self._look()
        self.view.update()

    def move(self, rel):
        fl = self.floor
        dx, dy = DIRS[(fl["facing"] + rel) % 4]
        x, y = fl["pos"][0] + dx, fl["pos"][1] + dy
        if fl["grid"][y][x]:
            self.sounds.play("bump")
            self.say("Ouch! A solid wall.")
            return
        thing = fl["things"].get(f"{x},{y}")
        if thing is not None and thing["type"] in ("monsters", "boss"):
            self.start_combat(f"{x},{y}", thing)
            return
        fl["pos"] = [x, y]
        self.sounds.play("step")
        self._look()
        if thing is not None:
            self.say({"chest": "A chest sits here. (Space to open it)",
                      "ladder": "A ladder leads down into the dark. (Space to climb down)"}[thing["type"]])
        self.view.update()

    def _look(self):
        """Marks what the party can see on the automap: around them, and along the corridor they face."""
        fl = self.floor
        seen = set(map(tuple, fl["seen"]))
        x, y = fl["pos"]
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                seen.add((x + dx, y + dy))
        dx, dy = DIRS[fl["facing"]]
        for d in range(1, 5):
            cx, cy = x + dx * d, y + dy * d
            seen.add((cx, cy))
            seen.add((cx + dy, cy + dx))
            seen.add((cx - dy, cy - dx))
            if fl["grid"][cy][cx]:
                break
        size = len(fl["grid"])
        fl["seen"] = [list(c) for c in seen if 0 <= c[0] < size and 0 <= c[1] < size]

    def use(self):
        fl = self.floor
        key = f"{fl['pos'][0]},{fl['pos'][1]}"
        thing = fl["things"].get(key)
        if thing is None:
            self.say("There's nothing here to use.")
            return
        if thing["type"] == "chest":
            del fl["things"][key]
            self.gold += thing["gold"]
            self.bag += thing["items"]
            self.sounds.play("chest")
            found = ", ".join(i["name"] for i in thing["items"])
            self.say(f"The chest creaks open: {thing['gold']} gold" + (f", {found}." if found else "."))
        elif thing["type"] == "ladder":
            self.sounds.play("stairs")
            if fl["number"] in CAMP_AFTER:
                self.mode = "camp"
                self.sounds.ambience(False)
                self.save_run()
                self._set_buttons()
                self.say(f"Halfway down a long shaft, a lantern glows: a merchant's camp beneath floor {fl['number']}."
                         " Rest, trade, and see to the fallen.")
            else:
                self.enter_floor(fl["number"] + 1)

    # ---- fighting --------------------------------------------------------------------------------------------
    def start_combat(self, key, thing):
        self.foes, self.foe_key = thing["group"], key
        self.mode = "combat"
        self.sounds.play("monster")
        names = {}
        for m in self.foes:
            names[m["name"]] = names.get(m["name"], 0) + 1
        self.say("Monsters! " + ", ".join(f"{n} {k}{'s' if n > 1 else ''}" for k, n in names.items()) + " attack!")
        self._set_buttons()

    def _alive(self):
        return [m for m in self.party if m["hp"] > 0]

    def _damage(self, atk, power, df, rnd):
        return max(1, atk + power + rnd.randint(0, max(1, (atk + power) // 2)) - df // 2)

    def combat_round(self, action):
        rnd = random.Random()
        foes = [m for m in self.foes if m["hp"] > 0]
        if action == "run":
            if rnd.random() < (0.55 if not any(m.get("boss") for m in foes) else 0.0):
                self.say("The party flees back the way it came!")
                self.mode = "explore"
                self._set_buttons()
                return
            self.say("You can't get away!")
        elif action == "potion":
            self._potion_in_battle()
        for hero in self._alive():
            foes = [m for m in self.foes if m["hp"] > 0]
            if not foes or action in ("run", "potion"):
                break
            if action == "cast" and hero["cls"] == "Mage" and hero["mp"] >= 4:
                hero["mp"] -= 4
                self.sounds.play("spell")
                dmg = 8 + hero["level"] * 4
                for m in foes:
                    m["hp"] -= dmg
                self.say(f"The Mage hurls a fireball! {dmg} damage to every foe.")
            elif action == "cast" and hero["cls"] == "Cleric" and hero["mp"] >= 3:
                hero["mp"] -= 3
                target = min(self._alive(), key=lambda m: m["hp"] / m["max"])
                heal = 12 + hero["level"] * 4
                target["hp"] = min(target["max"], target["hp"] + heal)
                self.sounds.play("heal")
                self.say(f"The Cleric prays: the {target['cls']} is healed by {heal}.")
            else:
                target = rnd.choice(foes)
                if rnd.random() < 0.88:
                    dmg = self._damage(hero["atk"], hero["weapon"]["power"], target["df"], rnd)
                    if hero["cls"] == "Rogue" and rnd.random() < 0.25:
                        dmg *= 2
                        self.say(f"The Rogue strikes a weak spot! {target['name']} takes {dmg}.")
                    else:
                        self.say(f"The {hero['cls']} hits the {target['name']} for {dmg}.")
                    target["hp"] -= dmg
                    self.sounds.play("hit")
                else:
                    self.say(f"The {hero['cls']} misses.")
        foes = [m for m in self.foes if m["hp"] > 0]
        if not foes:
            self._won_fight()
            return
        for m in foes:                                                   # the monsters' turn
            heroes = self._alive()
            if not heroes:
                break
            target = rnd.choice(heroes)
            if rnd.random() < 0.8:
                dmg = self._damage(m["atk"] // 2, 0, target["df"] + target["armor"]["power"] * 2, rnd)
                target["hp"] -= dmg
                self.sounds.play("hurt")
                self.say(f"The {m['name']} hits the {target['cls']} for {dmg}." +
                         ("  The " + target["cls"] + " falls!" if target["hp"] <= 0 else ""))
            else:
                self.say(f"The {m['name']} misses the {target['cls']}.")
        for hero in self.party:
            hero["hp"] = max(0, hero["hp"])
        if not self._alive():
            self.say("The last of the party falls...")
            self.end_run(False)
        self.view.update()

    def _potion_in_battle(self):
        potion = next((i for i in self.bag if i["kind"] == "heal"), None)
        if potion is None:
            self.say("No healing potions left!")
            return
        target = min(self._alive(), key=lambda m: m["hp"] / m["max"])
        self.bag.remove(potion)
        target["hp"] = min(target["max"], target["hp"] + potion["power"])
        self.sounds.play("heal")
        self.say(f"The {target['cls']} drinks a Healing Potion (+{potion['power']}).")

    def _won_fight(self):
        rnd = random.Random()
        xp = sum(m["xp"] for m in self.foes)
        gold = sum(m["gold"] for m in self.foes)
        self.gold += gold
        loot = [make_item(self.floor["number"], rnd) for _ in range(1 if rnd.random() < 0.45 else 0)]
        self.bag += loot
        boss = any(m.get("boss") for m in self.foes)
        del self.floor["things"][self.foe_key]
        self.sounds.play("coin")
        self.say(f"Victory! {xp} experience and {gold} gold" + (f", and a {loot[0]['name']}." if loot else "."))
        for hero in self._alive():
            hero["xp"] += xp // 2                                  # (everyone standing learns from the fight)
            while hero["xp"] >= 60 * hero["level"] ** 1.6:
                hero["level"] += 1
                base = CLASSES[hero["cls"]]
                hero["max"] += max(3, base["hp"] // 5)
                hero["hp"] = hero["max"]
                hero["atk"] += 1 + (hero["cls"] in ("Knight", "Rogue"))
                hero["df"] += 1 if hero["level"] % 2 == 0 else 0
                if hero["maxmp"]:
                    hero["maxmp"] += 3
                    hero["mp"] = hero["maxmp"]
                self.sounds.play("level")
                self.say(f"The {hero['cls']} reaches level {hero['level']}!")
        if boss:
            self.end_run(True)
            return
        self.mode = "explore"
        self._set_buttons()

    # ---- the bag, the merchant and the camp ------------------------------------------------------------------
    def _bag_page(self):
        page = QWidget()
        page.setStyleSheet("background: #18120C;")
        col = QVBoxLayout(page)
        self.bag_title = QLabel()
        col.addWidget(self.bag_title)
        row = QHBoxLayout()
        self.bag_list = QListWidget()
        self.shop_list = QListWidget()
        row.addWidget(self.bag_list, 1)
        row.addWidget(self.shop_list, 1)
        col.addLayout(row, 1)
        self.bag_note = QLabel()
        self.bag_note.setWordWrap(True)
        col.addWidget(self.bag_note)
        give = QHBoxLayout()
        self.give_buttons = []
        for i in range(4):
            b = QPushButton()
            b.clicked.connect(lambda _c=False, n=i: self.give(n))
            give.addWidget(b)
            self.give_buttons.append(b)
        col.addLayout(give)
        actions = QHBoxLayout()
        self.buy_btn = QPushButton("Buy")
        self.buy_btn.clicked.connect(self.buy)
        self.sell_btn = QPushButton("Sell")
        self.sell_btn.clicked.connect(self.sell)
        done = QPushButton("Done")
        done.clicked.connect(self.close_bag)
        for b in (self.buy_btn, self.sell_btn, done):
            actions.addWidget(b)
        col.addLayout(actions)
        return page

    def open_bag(self, shop=False):
        self.shopping = shop
        self.shop_list.setVisible(shop)
        self.buy_btn.setVisible(shop)
        self.sell_btn.setVisible(shop)
        if shop and not getattr(self, "stock", None):
            rnd = random.Random()
            depth = self.floor["number"] + 3
            self.stock = [make_item(depth, rnd, k) for k in ("weapon", "weapon", "weapon", "armor", "armor", "armor")]
            self.stock += [{"name": "Healing Potion", "kind": "heal", "power": 20 + depth * 3, "value": 20},
                           {"name": "Mana Potion", "kind": "mana", "power": 12 + depth, "value": 25},
                           {"name": "Phoenix Feather", "kind": "revive", "power": 0, "value": 120}]
        self._fill_bag()
        self.pages.setCurrentWidget(self.bag_page)

    def open_merchant(self):
        self.open_bag(shop=True)

    def _fill_bag(self):
        self.bag_title.setText(f"{'The Merchant' if self.shopping else 'Inventory'}   -   Gold: {self.gold:,}")
        self.bag_list.clear()
        for item in self.bag:
            what = {"weapon": f"weapon +{item['power']}", "armor": f"armor +{item['power']}", "heal": "heals",
                    "mana": "restores magic", "revive": "raises the fallen"}[item["kind"]]
            self.bag_list.addItem(QListWidgetItem(f"{item['name']}  ({what}, worth {item['value'] // 2} gold)"))
        self.shop_list.clear()
        for item in getattr(self, "stock", []):
            self.shop_list.addItem(QListWidgetItem(f"{item['name']}  (+{item['power']})  -  {item['value']} gold"
                                                   if item["kind"] in ("weapon", "armor") else
                                                   f"{item['name']}  -  {item['value']} gold"))
        for b, m in zip(self.give_buttons, self.party):
            b.setText(f"Give to {m['cls']}" + (" (fallen)" if m["hp"] <= 0 else ""))
        self.bag_note.setText("Pick something from your pack, then who should equip or use it."
                              + ("  Pick from the merchant's wares (right) to Buy." if self.shopping else ""))

    def give(self, n):
        row = self.bag_list.currentRow()
        if not (0 <= row < len(self.bag)):
            return
        item, hero = self.bag[row], self.party[n]
        if item["kind"] == "revive":
            if hero["hp"] > 0:
                self.bag_note.setText("The Phoenix Feather is for the fallen.")
                return
            hero["hp"] = hero["max"] // 2
            self.bag.pop(row)
            self.sounds.play("heal")
        elif hero["hp"] <= 0:
            self.bag_note.setText(f"The {hero['cls']} has fallen. Raise them first.")
            return
        elif item["kind"] == "heal":
            hero["hp"] = min(hero["max"], hero["hp"] + item["power"])
            self.bag.pop(row)
            self.sounds.play("heal")
        elif item["kind"] == "mana":
            if not hero["maxmp"]:
                self.bag_note.setText(f"The {hero['cls']} has no magic to restore.")
                return
            hero["mp"] = min(hero["maxmp"], hero["mp"] + item["power"])
            self.bag.pop(row)
            self.sounds.play("heal")
        else:
            old = hero[item["kind"]]
            hero[item["kind"]] = item
            self.bag[row] = old
            self.sounds.play("chest")
        self._fill_bag()

    def buy(self):
        row = self.shop_list.currentRow()
        if not (0 <= row < len(self.stock)):
            return
        item = self.stock[row]
        if self.gold < item["value"]:
            self.bag_note.setText("You can't afford that.")
            return
        self.gold -= item["value"]
        self.bag.append(dict(item))
        if item["kind"] in ("weapon", "armor"):
            self.stock.pop(row)
        self.sounds.play("coin")
        self._fill_bag()

    def sell(self):
        row = self.bag_list.currentRow()
        if not (0 <= row < len(self.bag)):
            return
        item = self.bag.pop(row)
        self.gold += item["value"] // 2
        self.sounds.play("coin")
        self._fill_bag()

    def close_bag(self):
        self.pages.setCurrentIndex(0)
        if self.mode in ("explore", "camp"):
            self.save_run()
        self.view.update()
        self.view.setFocus()

    def rest(self):
        if self.gold < 20:
            self.say("The merchant wants 20 gold for a bedroll by the fire.")
            return
        self.gold -= 20
        for m in self._alive():
            m["hp"], m["mp"] = m["max"], m["maxmp"]
        self.sounds.play("heal")
        self.say("The party rests by the fire. Wounds close and magic returns.")

    def raise_dead(self):
        fallen = [m for m in self.party if m["hp"] <= 0]
        if not fallen:
            self.say("No one needs raising.")
            return
        hero = fallen[0]
        cost = 100 * hero["level"]
        if self.gold < cost:
            self.say(f"The old priest asks {cost} gold to raise the {hero['cls']}.")
            return
        self.gold -= cost
        hero["hp"] = hero["max"]
        self.sounds.play("heal")
        self.say(f"For {cost} gold, the priest raises the {hero['cls']}!")

    def leave_camp(self):
        self.stock = None
        self.enter_floor(self.floor["number"] + 1)

    def shutdown(self):
        self.sounds.ambience(False)
        if self.mode in ("explore", "camp"):
            self.save_run()


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = ClaudeAndMagic(desktop)
    win = host.window(desktop, "Claude and Magic", body, magic_icon(), size=(820, 560))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    body.view.setFocus()
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.shutdown()
