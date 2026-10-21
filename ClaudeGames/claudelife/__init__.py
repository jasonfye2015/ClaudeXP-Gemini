"""Claude Life: John Conway's Game of Life, with everything you'd want to play with it.

Draw with the left button and erase with the right (or pick a tool); drag with the middle button or Shift to pan,
and the wheel zooms. Run, pause, step forward or back a generation, or go back to where you pressed Run. A gallery
of famous patterns (still lifes, oscillators, spaceships, guns, methuselahs) to stamp anywhere, turned and flipped
as you like. Other rules besides B3/S23 (HighLife, Day & Night, Seeds...) or your own. The plane can be endless,
wrap around, or have walls. Colour themes, cells coloured by age, fading trails.

Patterns are saved as standard .rle files in E:\\Created Files\\Claude Life (Open... reads any .rle or .cells file),
and your saved patterns can be stamped like the gallery's. The last world comes back the next time you open it."""
import json
import random
import re
from collections import deque
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QPushButton, QRadioButton, QSizePolicy, QSlider, QSpinBox,
                               QTabWidget, QVBoxLayout, QWidget)
from shiboken6 import isValid

from claudecore import host

TITLE = "Claude Life"
NEIGHBOURS = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
RULES = {"Conway's Life (B3/S23)": "B3/S23", "HighLife (B36/S23)": "B36/S23", "Day & Night (B3678/S34678)":
         "B3678/S34678", "Seeds (B2/S)": "B2/S", "Life without Death (B3/S012345678)": "B3/S012345678",
         "Maze (B3/S12345)": "B3/S12345", "Replicator (B1357/S1357)": "B1357/S1357", "2x2 (B36/S125)": "B36/S125",
         "Diamoeba (B35678/S5678)": "B35678/S5678", "Morley (B368/S245)": "B368/S245",
         "Anneal (B4678/S35678)": "B4678/S35678"}
EDGES = ["Endless plane", "Wrap around", "Walls"]
WORLDS = {"Small (80 x 60)": (80, 60), "Medium (160 x 120)": (160, 120), "Large (320 x 240)": (320, 240),
          "Huge (640 x 480)": (640, 480)}
THEMES = {   # background, grid, live, trail, age ramp
    "Classic Green": ("#000000", "#14301A", "#39FF5A", "#0E5C22", ["#9DFFB0", "#39FF5A", "#14B83A", "#0A7A2A"]),
    "Paper": ("#FFFFFF", "#E3E3E3", "#111111", "#C9D6F0", ["#D33A2C", "#E8902A", "#2C6ED3", "#111111"]),
    "Amber Monitor": ("#120A00", "#2A1A00", "#FFB000", "#5A3A00", ["#FFE08A", "#FFB000", "#C77800", "#7A4800"]),
    "Neon": ("#07001A", "#1A1040", "#FF3DF5", "#3A1066", ["#FFFFFF", "#3DF5FF", "#FF3DF5", "#8A3DFF"]),
    "Ocean": ("#03142B", "#0C2A4E", "#7FD8FF", "#0F4A7A", ["#E6FBFF", "#7FD8FF", "#2C8FD8", "#1A4FA0"]),
    "Windows XP": ("#3A6EA5", "#4A7EB5", "#FFFFFF", "#5C8CC0", ["#FFFFFF", "#FFE57A", "#F5A623", "#E05A1E"]),
}


def _pic(text):
    """A pattern drawn with '.' and 'O', rows split by '/'."""
    return [(x, y) for y, row in enumerate(text.split("/")) for x, ch in enumerate(row) if ch in "O*"]


def parse_rle(text):
    """-> (cells, rule or None, name or None, (x, y) offset or None). Reads RLE and plain-text .cells."""
    name = rule = offset = None
    lines = text.replace("\r", "").split("\n")
    if not any(re.match(r"\s*x\s*=", ln) for ln in lines):           # plain text (.cells)
        rows = []
        for ln in lines:
            if ln.startswith("!"):
                if ln.startswith("!Name:"):
                    name = ln[6:].strip()
                continue
            rows.append(ln)
        return [(x, y) for y, row in enumerate(rows) for x, ch in enumerate(row) if ch in "O*o"], None, name, None
    body = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("#"):
            if s[:2] in ("#N",):
                name = s[2:].strip()
            elif s[:2] in ("#R", "#P"):
                nums = s[2:].split()
                if len(nums) >= 2:
                    offset = (int(nums[0]), int(nums[1]))
            continue
        if re.match(r"x\s*=", s):
            m = re.search(r"rule\s*=\s*([^\s,]+)", s, re.I)
            if m:
                rule = m.group(1)
            continue
        body.append(s)
    cells, x, y, run = [], 0, 0, ""
    for ch in "".join(body):
        if ch.isdigit():
            run += ch
            continue
        n = int(run) if run else 1
        run = ""
        if ch == "!":
            break
        if ch == "$":
            y += n
            x = 0
        elif ch in "b.":
            x += n
        elif ch.isalpha():
            cells += [(x + i, y) for i in range(n)]
            x += n
    return cells, rule, name, offset


def to_rle(cells, rule, name="", comment=""):
    """Cells -> RLE text (with #R so a saved world comes back where it was)."""
    cells = sorted(cells, key=lambda c: (c[1], c[0]))
    if not cells:
        return f"#N {name}\nx = 0, y = 0, rule = {rule}\n!\n"
    x0 = min(c[0] for c in cells)
    y0 = min(c[1] for c in cells)
    w = max(c[0] for c in cells) - x0 + 1
    h = max(c[1] for c in cells) - y0 + 1
    live = set(cells)
    out, line = [], ""

    def put(count, tag):
        nonlocal line
        if not count:
            return
        tok = (str(count) if count > 1 else "") + tag
        if len(line) + len(tok) > 68:
            out.append(line)
            line = ""
        line += tok

    blank_rows = 0
    for y in range(y0, y0 + h):
        row = [(x, y) in live for x in range(x0, x0 + w)]
        while row and not row[-1]:
            row.pop()
        if not row:
            blank_rows += 1
            continue
        if y > y0:
            put(1 + blank_rows, "$")
        blank_rows = 0
        i = 0
        while i < len(row):
            j = i
            while j < len(row) and row[j] == row[i]:
                j += 1
            put(j - i, "o" if row[i] else "b")
            i = j
    put(1, "!")
    out.append(line)
    head = f"#N {name}\n" + (f"#C {comment}\n" if comment else "") + f"#R {x0} {y0}\n"
    return head + f"x = {w}, y = {h}, rule = {rule}\n" + "\n".join(out) + "\n"


GOSPER = ("24bo$22bobo$12b2o6b2o12b2o$11bo3bo4b2o12b2o$2o8bo5bo3b2o$2o8bo3bob2o4bobo$10bo5bo7bo$11bo3bo$12b2o!")
SIMKIN = ("2o5b2o$2o5b2o2$4b2o$4b2o5$22b2ob2o$21bo5bo$21bo6bo2b2o$21b3o3bo3b2o$26bo4$20b2o$20bo$21b3o$23bo!")


def _pulsar():
    quarter = [(2, 0), (3, 0), (4, 0), (0, 2), (0, 3), (0, 4), (5, 2), (5, 3), (5, 4), (2, 5), (3, 5), (4, 5)]
    cells = set()
    for x, y in quarter:
        for mx, my in ((0, 0), (1, 0), (0, 1), (1, 1)):
            cells.add((12 - x if mx else x, 12 - y if my else y))
    return sorted(cells)


# category -> [(name, cells, about)]
GALLERY = {
    "Still lifes": [
        ("Block", _pic("OO/OO"), "The simplest still life."),
        ("Beehive", _pic(".OO./O..O/.OO."), "The most common still life."),
        ("Loaf", _pic(".OO./O..O/.O.O/..O."), "A common still life."),
        ("Boat", _pic("OO./O.O/.O."), "Five cells that never change."),
        ("Ship", _pic("OO./O.O/.OO"), "A boat's longer cousin."),
        ("Tub", _pic(".O./O.O/.O."), "Four cells around a hole."),
        ("Pond", _pic(".OO./O..O/O..O/.OO."), "A larger ring."),
        ("Eater 1", _pic("OO../O.O./..O./..OO"), "The fishhook: eats gliders that hit it the right way."),
    ],
    "Oscillators": [
        ("Blinker", _pic("OOO"), "Period 2 - the smallest oscillator."),
        ("Toad", _pic(".OOO/OOO."), "Period 2."),
        ("Beacon", _pic("OO../OO../..OO/..OO"), "Period 2: the corners blink."),
        ("Clock", _pic("..O./O.O./.O.O/.O.."), "Period 2."),
        ("Pulsar", _pulsar(), "Period 3 - the best-known big oscillator."),
        ("Pentadecathlon", _pic("..O....O../OO.OOOO.OO/..O....O.."), "Period 15."),
        ("Kok's Galaxy", _pic("OOOOOO.OO/OOOOOO.OO/.......OO/OO.....OO/OO.....OO/OO.....OO/OO......./"
                              "OO.OOOOOO/OO.OOOOOO"), "Period 8: it spins."),
    ],
    "Spaceships": [
        ("Glider", _pic(".O./..O/OOO"), "Travels diagonally, one cell every 4 generations."),
        ("Lightweight spaceship", _pic(".O..O/O..../O...O/OOOO."), "LWSS: flies sideways at c/2."),
        ("Middleweight spaceship", _pic("...O../.O...O/O...../O....O/OOOOO."), "MWSS: c/2."),
        ("Heavyweight spaceship", _pic("...OO../.O....O/O....../O.....O/OOOOOO."), "HWSS: c/2."),
    ],
    "Guns": [
        ("Gosper glider gun", parse_rle("x = 36, y = 9\n" + GOSPER)[0], "The first gun ever found (1970): "
                                                                         "a new glider every 30 generations."),
        ("Simkin glider gun", parse_rle("x = 33, y = 21\n" + SIMKIN)[0], "A glider every 120 generations."),
    ],
    "Methuselahs": [
        ("R-pentomino", _pic(".OO/OO./.O."), "Five cells that take 1,103 generations to settle."),
        ("Diehard", _pic("......O./OO....../.O...OOO"), "Vanishes completely after 130 generations."),
        ("Acorn", _pic(".O...../...O.../OO..OOO"), "Seven cells, 5,206 generations of chaos."),
        ("Pi-heptomino", _pic("OOO/O.O/O.O"), "Settles after 173 generations."),
        ("B-heptomino", _pic("O.OO/OOO./.O.."), "Settles after 148 generations."),
        ("Thunderbird", _pic("OOO/.../.O./.O./.O."), "Settles after 243 generations."),
        ("Rabbits", _pic("O...OOO/OOO..O./.O....."), "Nine cells, 17,331 generations."),
    ],
    "Infinite growth": [
        ("Switch engine", _pic(".O.O../O...../.O..O./...OOO"), "Eight cells that grow forever (on an endless plane)."),
        ("One-line grower", _pic("OOOOOOOO.OOOOO...OOO......OOOOOOO.OOOOO"), "A single row of 39 cells that "
                                                                              "grows forever."),
    ],
}


def normalise(cells):
    if not cells:
        return []
    x0 = min(c[0] for c in cells)
    y0 = min(c[1] for c in cells)
    return [(x - x0, y - y0) for x, y in cells]


def transform(cells, turns=0, flip=False):
    out = list(cells)
    if flip:
        out = [(-x, y) for x, y in out]
    for _ in range(turns % 4):
        out = [(-y, x) for x, y in out]
    return normalise(out)


def parse_rule(text):
    """'B3/S23' -> (birth set, survive set), or None."""
    m = re.fullmatch(r"\s*[Bb]?([0-8]*)\s*/\s*[Ss]?([0-8]*)\s*", text or "")
    if not m:
        m2 = re.fullmatch(r"\s*([0-8]*)\s*/\s*([0-8]*)\s*", text or "")        # S/B notation: 23/3
        if not m2:
            return None
        return {int(c) for c in m2.group(2)}, {int(c) for c in m2.group(1)}
    return {int(c) for c in m.group(1)}, {int(c) for c in m.group(2)}


def thumbnail(cells, size=44, fg="#1E1E1E", bg="#FFFFFF"):
    pm = QPixmap(size, size)
    pm.fill(QColor(bg))
    if not cells:
        return pm
    w = max(c[0] for c in cells) + 1
    h = max(c[1] for c in cells) + 1
    s = max(1.0, min((size - 4) / w, (size - 4) / h))
    ox, oy = (size - w * s) / 2, (size - h * s) / 2
    p = QPainter(pm)
    for x, y in cells:
        p.fillRect(QRectF(ox + x * s, oy + y * s, max(1.0, s - (1 if s >= 4 else 0)),
                          max(1.0, s - (1 if s >= 4 else 0))), QColor(fg))
    p.end()
    return pm


def life_icon():
    pm = QPixmap(32, 32)
    pm.fill(QColor("#000000"))
    p = QPainter(pm)
    p.setPen(QColor("#14301A"))
    for i in range(0, 33, 6):
        p.drawLine(i + 1, 0, i + 1, 32)
        p.drawLine(0, i + 1, 32, i + 1)
    for x, y in _pic(".O./..O/OOO"):
        p.fillRect(2 + (x + 1) * 6, 2 + (y + 1) * 6, 5, 5, QColor("#39FF5A"))
    p.end()
    icon = QIcon(pm)
    return icon


# ---- the world ---------------------------------------------------------------------------------------------------------
class World:
    """The live cells (a set), stepped by the rule; endless, wrapped or walled."""

    def __init__(self):
        self.live = set()
        self.age = {}
        self.trail = {}               # recently dead cell -> how bright its ghost still is (1..8)
        self.generation = 0
        self.birth, self.survive = {3}, {2, 3}
        self.edges = EDGES[0]
        self.size = WORLDS["Large (320 x 240)"]
        self.births = self.deaths = 0

    def inside(self, c):
        if self.edges == EDGES[0]:
            return True
        w, h = self.size
        return 0 <= c[0] < w and 0 <= c[1] < h

    def fix(self, c):
        """Where a cell really is: wrapped onto the torus, or None if it's outside the walls."""
        if self.edges == EDGES[1]:
            w, h = self.size
            return c[0] % w, c[1] % h
        if self.edges == EDGES[2] and not self.inside(c):
            return None
        return c

    def set(self, c, alive):
        c = self.fix(c)
        if c is None:
            return False
        if alive and c not in self.live:
            self.live.add(c)
            self.age[c] = 1
            return True
        if not alive and c in self.live:
            self.live.discard(c)
            self.age.pop(c, None)
            return True
        return False

    def step(self):
        counts = {}
        get = counts.get
        wrap = self.edges == EDGES[1]
        w, h = self.size
        for x, y in self.live:
            for dx, dy in NEIGHBOURS:
                k = ((x + dx) % w, (y + dy) % h) if wrap else (x + dx, y + dy)
                counts[k] = get(k, 0) + 1
        walls = self.edges == EDGES[2]
        birth, survive, live = self.birth, self.survive, self.live
        new = set()
        for c, n in counts.items():
            if (n in survive) if c in live else (n in birth):
                if walls and not (0 <= c[0] < w and 0 <= c[1] < h):
                    continue
                new.add(c)
        if 0 in survive:
            new |= {c for c in live if c not in counts}
        died = live - new
        self.births = len(new - live)
        self.deaths = len(died)
        trail = {c: t - 1 for c, t in self.trail.items() if t > 1 and c not in new}
        for c in died:
            trail[c] = 8
        self.trail = trail
        age = self.age
        self.age = {c: age.get(c, 0) + 1 for c in new}
        self.live = new
        self.generation += 1

    def snapshot(self):
        return frozenset(self.live), dict(self.age), self.generation

    def restore(self, snap):
        live, age, gen = snap
        self.live = set(live)
        self.age = dict(age)
        self.generation = gen
        self.trail = {}


# ---- the board ---------------------------------------------------------------------------------------------------------
class Board(QWidget):
    """The view of the world: zoom, pan, drawing, erasing, and a stamp that follows the mouse."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(320, 240)
        self.cell = 6.0                         # pixels per cell
        self.ox, self.oy = -10.0, -10.0         # the world coordinate at the top-left of the view
        self.drag = None
        self.paint_value = None
        self.hover = None
        self.last_cell = None

    def cell_at(self, pos):
        import math
        return math.floor(pos.x() / self.cell + self.ox), math.floor(pos.y() / self.cell + self.oy)

    def zoom(self, factor, around=None):
        around = around or QPointF(self.width() / 2, self.height() / 2)
        wx, wy = around.x() / self.cell + self.ox, around.y() / self.cell + self.oy
        self.cell = max(1.0, min(40.0, self.cell * factor))
        self.ox, self.oy = wx - around.x() / self.cell, wy - around.y() / self.cell
        self.update()
        self.app.update_status()

    def fit(self):
        """Show all the live cells (or the whole world, if it has edges)."""
        world = self.app.world
        if world.edges != EDGES[0]:
            x0, y0 = 0, 0
            x1, y1 = world.size
        elif world.live:
            xs = [c[0] for c in world.live]
            ys = [c[1] for c in world.live]
            x0, y0, x1, y1 = min(xs) - 4, min(ys) - 4, max(xs) + 5, max(ys) + 5
        else:
            x0, y0, x1, y1 = -40, -30, 40, 30
        self.cell = max(1.0, min(24.0, self.width() / max(1, x1 - x0), self.height() / max(1, y1 - y0)))
        self.ox = (x0 + x1) / 2 - self.width() / self.cell / 2
        self.oy = (y0 + y1) / 2 - self.height() / self.cell / 2
        self.update()
        self.app.update_status()

    def centre_on(self, x, y):
        self.ox = x - self.width() / self.cell / 2
        self.oy = y - self.height() / self.cell / 2
        self.update()

    # ---- mouse ----
    def mousePressEvent(self, e):
        self.setFocus()
        pos = e.position()
        app = self.app
        if e.button() == Qt.MiddleButton or (e.button() == Qt.LeftButton and e.modifiers() & Qt.ShiftModifier) \
                or (e.button() == Qt.LeftButton and app.tool == "pan"):
            self.drag = (pos, self.ox, self.oy)
            self.setCursor(Qt.ClosedHandCursor)
            return
        c = self.cell_at(pos)
        if app.tool == "stamp" and app.stamp:
            if e.button() == Qt.RightButton:
                app.set_tool("draw")
                return
            app.stamp_at(c)
            return
        app.begin_edit()
        if e.button() == Qt.RightButton or app.tool == "erase":
            self.paint_value = False
        else:
            self.paint_value = c not in app.world.live if app.tool == "draw" else True
        self.last_cell = c
        if app.world.set(c, self.paint_value):
            app.changed()

    def mouseMoveEvent(self, e):
        pos = e.position()
        if self.drag is not None:
            start, ox, oy = self.drag
            self.ox = ox - (pos.x() - start.x()) / self.cell
            self.oy = oy - (pos.y() - start.y()) / self.cell
            self.update()
            return
        c = self.cell_at(pos)
        self.hover = c
        if self.paint_value is not None and self.last_cell is not None:
            changed = False
            for cc in _line(self.last_cell, c):           # (no gaps when the mouse moves fast)
                changed |= self.app.world.set(cc, self.paint_value)
            self.last_cell = c
            if changed:
                self.app.changed()
        if self.app.tool == "stamp":
            self.update()
        self.app.update_status()

    def mouseReleaseEvent(self, e):
        if self.drag is not None:
            self.drag = None
            self.setCursor(Qt.CrossCursor)
        self.paint_value = None
        self.last_cell = None

    def leaveEvent(self, e):
        self.hover = None
        self.update()

    def wheelEvent(self, e):
        self.zoom(1.25 if e.angleDelta().y() > 0 else 0.8, e.position())

    def keyPressEvent(self, e):
        if not self.app.key(e):
            super().keyPressEvent(e)

    # ---- painting ----
    def paintEvent(self, event):
        app = self.app
        bg, grid, live_c, trail_c, ramp = THEMES[app.theme]
        world = app.world
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(bg))
        s = self.cell
        cols = int(self.width() / s) + 2
        rows = int(self.height() / s) + 2
        import math
        cx0, cy0 = math.floor(self.ox), math.floor(self.oy)
        # outside a walled or wrapped world: dimmed
        if world.edges != EDGES[0]:
            w, h = world.size
            inside = QRectF((0 - self.ox) * s, (0 - self.oy) * s, w * s, h * s)
            shade = QColor(grid)
            shade.setAlpha(110)
            p.save()
            p.setClipRect(self.rect())
            outside = QRectF(self.rect())
            for r in (QRectF(outside.left(), outside.top(), outside.width(), inside.top() - outside.top()),
                      QRectF(outside.left(), inside.bottom(), outside.width(), outside.bottom() - inside.bottom()),
                      QRectF(outside.left(), inside.top(), inside.left() - outside.left(), inside.height()),
                      QRectF(inside.right(), inside.top(), outside.right() - inside.right(), inside.height())):
                if r.width() > 0 and r.height() > 0:
                    p.fillRect(r, shade)
            p.setPen(QPen(QColor(live_c), 1))
            p.drawRect(inside)
            p.restore()
        # the cells, drawn into a small picture one pixel per cell, then scaled up
        img = QImage(cols, rows, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        x1, y1 = cx0 + cols, cy0 + rows
        if app.trails:
            tc = QColor(trail_c)
            for (x, y), t in world.trail.items():
                if cx0 <= x < x1 and cy0 <= y < y1:
                    c = QColor(tc)
                    c.setAlpha(30 + t * 26)
                    img.setPixelColor(x - cx0, y - cy0, c)
        if app.age_colours:
            ramp_c = [QColor(c).rgba() for c in ramp]
            age = world.age
            for (x, y) in world.live:
                if cx0 <= x < x1 and cy0 <= y < y1:
                    a = age.get((x, y), 1)
                    img.setPixel(x - cx0, y - cy0, ramp_c[0 if a <= 1 else 1 if a <= 5 else 2 if a <= 30 else 3])
        else:
            live_rgba = QColor(live_c).rgba()
            for (x, y) in world.live:
                if cx0 <= x < x1 and cy0 <= y < y1:
                    img.setPixel(x - cx0, y - cy0, live_rgba)
        left = (cx0 - self.ox) * s
        top = (cy0 - self.oy) * s
        p.drawImage(QRectF(left, top, cols * s, rows * s), img)
        # grid lines
        if app.show_grid and s >= 5:
            p.setPen(QPen(QColor(grid), 1))
            for i in range(cols + 1):
                x = left + i * s
                p.drawLine(QPointF(x, 0), QPointF(x, self.height()))
            for j in range(rows + 1):
                y = top + j * s
                p.drawLine(QPointF(0, y), QPointF(self.width(), y))
        # the stamp's ghost, or the cell under the mouse
        if self.hover is not None:
            hx, hy = self.hover
            if app.tool == "stamp" and app.stamp:
                ghost = QColor(live_c)
                ghost.setAlpha(120)
                cells = app.stamp_cells()
                w = max(c[0] for c in cells) + 1
                h = max(c[1] for c in cells) + 1
                bx, by = hx - w // 2, hy - h // 2
                p.setPen(QPen(QColor(live_c), 1, Qt.DashLine))
                p.setBrush(Qt.NoBrush)
                p.drawRect(QRectF((bx - self.ox) * s, (by - self.oy) * s, w * s, h * s))
                for x, y in cells:
                    p.fillRect(QRectF((bx + x - self.ox) * s, (by + y - self.oy) * s, max(1.0, s), max(1.0, s)),
                               ghost)
            elif s >= 4:
                p.setPen(QPen(QColor(live_c), 1))
                p.setBrush(Qt.NoBrush)
                p.drawRect(QRectF((hx - self.ox) * s, (hy - self.oy) * s, s, s))


def _line(a, b):
    """The cells on a line between two cells (Bresenham)."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    out = []
    while True:
        out.append((x0, y0))
        if (x0, y0) == (x1, y1) or len(out) > 4000:
            return out
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


# ---- the program -------------------------------------------------------------------------------------------------------
class ClaudeLife(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.world = World()
        self.tool = "draw"
        self.stamp = None                       # (name, cells)
        self.turns = 0
        self.flipped = False
        self.start_snap = None                  # where Run was last pressed
        self.history = deque(maxlen=200)        # for Step Back
        self.edit_snap = None
        self.seen = {}                          # state hash -> generation (to notice still lifes and oscillators)
        self.cycle = ""
        s = self._settings()
        self.theme = s.get("theme", "Classic Green") if s.get("theme") in THEMES else "Classic Green"
        self.show_grid = s.get("grid", True)
        self.age_colours = s.get("age", False)
        self.trails = s.get("trails", False)
        self.speed = int(s.get("speed", 12))
        self.world.edges = s.get("edges", EDGES[0]) if s.get("edges") in EDGES else EDGES[0]
        size_name = s.get("world", "Large (320 x 240)")
        self.world.size = WORLDS.get(size_name, WORLDS["Large (320 x 240)"])
        rule = parse_rule(s.get("rule", "B3/S23")) or ({3}, {2, 3})
        self.world.birth, self.world.survive = rule
        self.timer = QTimer(self, timeout=self.tick)
        self._build(size_name)
        self._restore_world()
        self.update_status()

    # ---- settings and the last world ----
    def _settings(self):
        try:
            data = json.loads((host.data("claudelife") / "settings.json").read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _save_settings(self):
        data = {"theme": self.theme, "grid": self.show_grid, "age": self.age_colours, "trails": self.trails,
                "speed": self.speed, "edges": self.world.edges, "world": self.world_box.currentText(),
                "rule": self.rule_text()}
        try:
            (host.data("claudelife") / "settings.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
        except OSError:
            pass

    def _restore_world(self):
        path = host.data("claudelife") / "last.rle"
        cells = []
        if path.exists():
            try:
                cells, _rule, _name, offset = parse_rle(path.read_text(encoding="utf-8"))
                if offset:
                    cells = [(x + offset[0], y + offset[1]) for x, y in cells]
            except (OSError, ValueError):
                cells = []
        if not cells:                            # a first look: a Gosper gun firing
            cells = [(x + 2, y + 2) for x, y in dict((n, c) for n, c, _a in GALLERY["Guns"])["Gosper glider gun"]]
            if self.world.edges != EDGES[0]:
                cells = [(x + 10, y + 10) for x, y in cells]
        for c in cells:
            self.world.set(c, True)
        QTimer.singleShot(0, self.board.fit)

    def _save_world(self):
        try:
            (host.data("claudelife") / "last.rle").write_text(
                to_rle(self.world.live, self.rule_text(), "Last world"), encoding="utf-8")
        except OSError:
            pass

    # ---- building ----
    def _build(self, size_name):
        root = QHBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(6)
        left = QVBoxLayout()
        left.setSpacing(4)
        bar = QHBoxLayout()
        bar.setSpacing(3)

        def button(text, slot, tip, width=None):
            b = QPushButton(text)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            if width:
                b.setFixedWidth(width)
            bar.addWidget(b)
            return b

        self.run_btn = button("▶ Run", self.toggle_run, "Run or pause (Space)", 74)
        button("Step ▸", self.step_once, "One generation (N or Right arrow)")
        button("◂ Back", self.step_back, "Undo the last generation or edit (B or Left arrow / Ctrl+Z)")
        button("⟲ Reset", self.reset, "Back to where you last pressed Run (Home)")
        bar.addSpacing(6)
        button("Clear", self.clear, "Clear the world (Delete)")
        button("Random", self.randomise, "Fill the view with random cells")
        bar.addSpacing(6)
        bar.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 60)
        self.speed_slider.setValue(self.speed)
        self.speed_slider.setFixedWidth(110)
        self.speed_slider.setToolTip("Generations per second")
        self.speed_slider.valueChanged.connect(self.set_speed)
        bar.addWidget(self.speed_slider)
        self.speed_label = QLabel()
        self.speed_label.setFixedWidth(52)
        bar.addWidget(self.speed_label)
        bar.addStretch(1)
        button("−", lambda: self.board.zoom(0.8), "Zoom out (-)", 26)
        button("+", lambda: self.board.zoom(1.25), "Zoom in (+)", 26)
        button("Fit", lambda: self.board.fit(), "Show everything (F)")
        left.addLayout(bar)
        self.board = Board(self)
        self.board.setCursor(Qt.CrossCursor)
        left.addWidget(self.board, 1)
        self.status = QLabel()
        self.status.setStyleSheet("QLabel { font-family: Tahoma; font-size: 11px; padding: 2px; }")
        self.status.setMinimumWidth(1)                      # (a long line is cut off, never widening the window)
        self.status.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        left.addWidget(self.status)
        root.addLayout(left, 1)

        side = QTabWidget()
        side.setFixedWidth(270)
        side.addTab(self._tools_tab(), "Patterns")
        side.addTab(self._rules_tab(size_name), "Rules")
        side.addTab(self._view_tab(), "View")
        side.addTab(self._saves_tab(), "Saved")
        root.addWidget(side)
        self.set_speed(self.speed)

    def _tools_tab(self):
        tab = QWidget()
        col = QVBoxLayout(tab)
        col.setSpacing(5)
        tools = QGroupBox("Tool")
        tl = QHBoxLayout(tools)
        self.tool_buttons = {}
        for key, label in (("draw", "Draw"), ("erase", "Erase"), ("pan", "Move"), ("stamp", "Stamp")):
            r = QRadioButton(label)
            r.toggled.connect(lambda on, k=key: on and self.set_tool(k))
            tl.addWidget(r)
            self.tool_buttons[key] = r
        self.tool_buttons["draw"].setChecked(True)
        col.addWidget(tools)
        self.category = QComboBox()
        self.category.addItems(list(GALLERY) + ["My saved patterns"])
        self.category.currentTextChanged.connect(self._fill_gallery)
        col.addWidget(self.category)
        self.gallery = QListWidget()
        self.gallery.setIconSize(QSize(44, 44))
        self.gallery.setWordWrap(True)
        self.gallery.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.gallery.currentItemChanged.connect(lambda item, _o: self._pick(item))
        col.addWidget(self.gallery, 1)
        self.about = QLabel()
        self.about.setWordWrap(True)
        self.about.setMinimumHeight(44)
        col.addWidget(self.about)
        row = QHBoxLayout()
        for text, slot, tip in (("⟳ Turn", self.turn, "Turn the stamp a quarter (R)"),
                                ("⇋ Flip", self.flip, "Mirror the stamp (M)"),
                                ("Centre", self.stamp_centre, "Stamp it in the middle of the view")):
            b = QPushButton(text)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            row.addWidget(b)
        col.addLayout(row)
        hint = QLabel("Left: draw / stamp. Right: erase / cancel stamp.\nMiddle or Shift+drag: move. Wheel: zoom.")
        hint.setStyleSheet("QLabel { color: #555555; }")
        col.addWidget(hint)
        self._fill_gallery(self.category.currentText())
        return tab

    def _rules_tab(self, size_name):
        tab = QWidget()
        form = QFormLayout(tab)
        self.rule_box = QComboBox()
        self.rule_box.addItems(list(RULES) + ["Custom"])
        form.addRow("Rule:", self.rule_box)
        self.rule_edit = QLineEdit(self.rule_text())
        self.rule_edit.setToolTip("Born / Survives, e.g. B3/S23")
        self.rule_edit.editingFinished.connect(self._custom_rule)
        form.addRow("B/S:", self.rule_edit)
        current = next((k for k, v in RULES.items() if v == self.rule_text()), "Custom")
        self.rule_box.setCurrentText(current)
        self.rule_box.currentTextChanged.connect(self._preset_rule)
        explain = QLabel("B = how many neighbours bring an empty cell to life; S = how many keep a live cell alive. "
                         "Conway's Life is B3/S23.")
        explain.setWordWrap(True)
        form.addRow(explain)
        self.edge_box = QComboBox()
        self.edge_box.addItems(EDGES)
        self.edge_box.setCurrentText(self.world.edges)
        self.edge_box.currentTextChanged.connect(self._edges)
        form.addRow("Edges:", self.edge_box)
        self.world_box = QComboBox()
        self.world_box.addItems(list(WORLDS))
        self.world_box.setCurrentText(size_name if size_name in WORLDS else "Large (320 x 240)")
        self.world_box.currentTextChanged.connect(self._world_size)
        form.addRow("World:", self.world_box)
        note = QLabel("World size applies when the edges wrap around or are walls.")
        note.setWordWrap(True)
        note.setStyleSheet("QLabel { color: #555555; }")
        form.addRow(note)
        self.density = QSpinBox()
        self.density.setRange(5, 80)
        self.density.setValue(30)
        self.density.setSuffix(" %")
        form.addRow("Random fill:", self.density)
        self.stop_on_cycle = QCheckBox("Pause when it settles down")
        self.stop_on_cycle.setChecked(False)
        form.addRow(self.stop_on_cycle)
        return tab

    def _view_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        self.theme_box = QComboBox()
        self.theme_box.addItems(list(THEMES))
        self.theme_box.setCurrentText(self.theme)
        self.theme_box.currentTextChanged.connect(self._theme)
        form.addRow("Colours:", self.theme_box)
        for attr, label in (("show_grid", "Show grid lines (G)"), ("age_colours", "Colour cells by age (A)"),
                            ("trails", "Fading trails (T)")):
            box = QCheckBox(label)
            box.setChecked(getattr(self, attr))
            box.toggled.connect(lambda on, a=attr: self._view_option(a, on))
            form.addRow(box)
            setattr(self, attr + "_box", box)
        keys = QLabel("<b>Keys</b><br>Space run/pause &nbsp; N step &nbsp; B back<br>Home reset &nbsp; Delete clear<br>"
                      "+ / - zoom &nbsp; F fit &nbsp; arrows (with Ctrl) move<br>R turn &nbsp; M flip &nbsp; "
                      "Esc stop stamping<br>D draw &nbsp; E erase &nbsp; S stamp")
        keys.setTextFormat(Qt.RichText)
        form.addRow(keys)
        return tab

    def _saves_tab(self):
        tab = QWidget()
        col = QVBoxLayout(tab)
        self.saved = QListWidget()
        self.saved.setIconSize(QSize(36, 36))
        self.saved.itemDoubleClicked.connect(lambda _i: self.load_selected())
        col.addWidget(self.saved, 1)
        row = QHBoxLayout()
        self.save_name = QLineEdit()
        self.save_name.setPlaceholderText("Name for this world")
        self.save_name.returnPressed.connect(self.save_world)
        row.addWidget(self.save_name, 1)
        save = QPushButton("Save")
        save.clicked.connect(self.save_world)
        row.addWidget(save)
        col.addLayout(row)
        row2 = QHBoxLayout()
        for text, slot in (("Load", self.load_selected), ("Stamp", self.stamp_selected), ("Delete", self.delete_selected)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            row2.addWidget(b)
        col.addLayout(row2)
        row3 = QHBoxLayout()
        for text, slot in (("Open...", self.open_file), ("Save Image", self.save_image), ("Folder", self.open_folder)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            row3.addWidget(b)
        col.addLayout(row3)
        note = QLabel("Saved as .rle files in E:\\Created Files\\Claude Life. Open... reads any .rle or .cells "
                      "pattern file.")
        note.setWordWrap(True)
        note.setStyleSheet("QLabel { color: #555555; }")
        col.addWidget(note)
        self._fill_saved()
        return tab

    # ---- running ----
    def toggle_run(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.start_snap = self.world.snapshot()
            self.seen = {}
            self.cycle = ""
            self.timer.start(max(16, int(1000 / self.speed)))
        self.run_btn.setText("❚❚ Pause" if self.timer.isActive() else "▶ Run")
        self.update_status()

    def pause(self):
        if self.timer.isActive():
            self.toggle_run()

    def set_speed(self, v):
        self.speed = v
        self.speed_label.setText(f"{v} gen/s")
        if self.timer.isActive():
            self.timer.setInterval(max(16, int(1000 / v)))

    def tick(self):
        self.history.append(self.world.snapshot())
        self.world.step()
        self._watch_cycle()
        self.board.update()
        self.update_status()

    def _watch_cycle(self):
        """Notice when the world settles: dead, still, or repeating."""
        w = self.world
        if not w.live:
            self.cycle = "Everything died"
        else:
            key = hash(frozenset(w.live))
            if key in self.seen:
                period = w.generation - self.seen[key]
                self.cycle = "Still life (stable)" if period == 1 else f"Repeating, period {period}"
            else:
                self.cycle = ""
                if len(self.seen) > 400:
                    self.seen.clear()
                self.seen[key] = w.generation
        if self.cycle and self.stop_on_cycle.isChecked() and self.timer.isActive():
            self.toggle_run()

    def step_once(self):
        self.pause()
        self.tick()

    def step_back(self):
        if not self.history:
            host.sound("default")
            return
        self.pause()
        self.world.restore(self.history.pop())
        self.cycle = ""
        self.board.update()
        self.update_status()

    def reset(self):
        if self.start_snap is None:
            host.sound("default")
            return
        self.pause()
        self.history.append(self.world.snapshot())
        self.world.restore(self.start_snap)
        self.cycle = ""
        self.board.update()
        self.update_status()

    def clear(self):
        self.pause()
        self.begin_edit()
        self.world.live.clear()
        self.world.age.clear()
        self.world.trail.clear()
        self.world.generation = 0
        self.changed()

    def randomise(self):
        self.pause()
        self.begin_edit()
        b = self.board
        w = self.world
        if w.edges != EDGES[0]:
            x0, y0 = 0, 0
            x1, y1 = w.size
        else:
            x0, y0 = int(b.ox), int(b.oy)
            x1, y1 = x0 + int(b.width() / b.cell), y0 + int(b.height() / b.cell)
            if (x1 - x0) * (y1 - y0) > 400 * 300:      # (an enormous view: just the middle of it)
                mx, my = (x0 + x1) // 2, (y0 + y1) // 2
                x0, x1, y0, y1 = mx - 200, mx + 200, my - 150, my + 150
        chance = self.density.value() / 100
        for y in range(y0, y1):
            for x in range(x0, x1):
                if random.random() < chance:
                    w.set((x, y), True)
        self.changed()

    # ---- editing ----
    def begin_edit(self):
        self.history.append(self.world.snapshot())

    def changed(self):
        self.cycle = ""
        self.board.update()
        self.update_status()

    def set_tool(self, key):
        self.tool = key
        if key == "stamp" and self.stamp is None:
            item = self.gallery.currentItem() or self.gallery.item(0)
            if item is not None:
                self.gallery.setCurrentItem(item)
                self._pick(item)
        b = self.tool_buttons.get(key)
        if b is not None and not b.isChecked():
            b.setChecked(True)
        self.board.setCursor(Qt.OpenHandCursor if key == "pan" else Qt.CrossCursor)
        self.board.update()
        self.update_status()

    def _fill_gallery(self, category):
        self.gallery.clear()
        if category == "My saved patterns":
            entries = []
            for path in self._saved_files():
                try:
                    cells, _r, name, _o = parse_rle(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                entries.append((name or path.stem, normalise(cells), f"Saved: {path.name}"))
        else:
            entries = GALLERY.get(category, [])
        for name, cells, about in entries:
            if not cells:
                continue
            item = QListWidgetItem(QIcon(thumbnail(cells)), name)
            item.setData(Qt.UserRole, (name, normalise(cells), about))
            self.gallery.addItem(item)

    def _pick(self, item):
        if item is None:
            return
        name, cells, about = item.data(Qt.UserRole)
        self.stamp = (name, cells)
        self.turns = 0
        self.flipped = False
        w = max(c[0] for c in cells) + 1
        h = max(c[1] for c in cells) + 1
        self.about.setText(f"<b>{name}</b> ({w} x {h}, {len(cells)} cells)<br>{about}")
        if self.tool != "stamp":
            self.set_tool("stamp")
        self.board.setFocus()

    def stamp_cells(self):
        return transform(self.stamp[1], self.turns, self.flipped) if self.stamp else []

    def stamp_at(self, c):
        cells = self.stamp_cells()
        if not cells:
            return
        w = max(x for x, _y in cells) + 1
        h = max(y for _x, y in cells) + 1
        self.begin_edit()
        for x, y in cells:
            self.world.set((c[0] - w // 2 + x, c[1] - h // 2 + y), True)
        self.changed()

    def stamp_centre(self):
        if not self.stamp:
            return
        b = self.board
        self.stamp_at((int(b.ox + b.width() / b.cell / 2), int(b.oy + b.height() / b.cell / 2)))

    def turn(self):
        self.turns = (self.turns + 1) % 4
        self.board.update()

    def flip(self):
        self.flipped = not self.flipped
        self.board.update()

    # ---- rules, edges and view ----
    def rule_text(self):
        w = self.world
        return "B" + "".join(map(str, sorted(w.birth))) + "/S" + "".join(map(str, sorted(w.survive)))

    def _preset_rule(self, name):
        if name in RULES:
            self.world.birth, self.world.survive = parse_rule(RULES[name])
            self.rule_edit.setText(self.rule_text())
            self.seen = {}
            self._save_settings()
            self.update_status()

    def _custom_rule(self):
        rule = parse_rule(self.rule_edit.text())
        if rule is None or 0 in rule[0]:
            host.message(self.desktop, TITLE, "Type a rule like B3/S23: the neighbour counts (0-8) that bring a "
                         "cell to life, then the ones that keep it alive. (B0 rules aren't supported.)", "warning")
            self.rule_edit.setText(self.rule_text())
            return
        self.world.birth, self.world.survive = rule
        self.rule_edit.setText(self.rule_text())
        self.rule_box.blockSignals(True)
        self.rule_box.setCurrentText(next((k for k, v in RULES.items() if v == self.rule_text()), "Custom"))
        self.rule_box.blockSignals(False)
        self.seen = {}
        self._save_settings()
        self.update_status()

    def _edges(self, name):
        self.world.edges = name
        if name != EDGES[0]:                    # bring everything into the world
            fixed = set()
            for c in self.world.live:
                f = self.world.fix(c)
                if f is not None:
                    fixed.add(f)
            self.world.live = fixed
            self.world.age = {c: self.world.age.get(c, 1) for c in fixed}
        self._save_settings()
        self.board.fit()

    def _world_size(self, name):
        self.world.size = WORLDS[name]
        self._edges(self.world.edges)

    def _theme(self, name):
        self.theme = name
        self._save_settings()
        self.board.update()

    def _view_option(self, attr, on):
        setattr(self, attr, on)
        self._save_settings()
        self.board.update()

    # ---- saving and loading ----
    def _folder(self):
        folder = host.local_storage() / "Created Files" / TITLE
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _saved_files(self):
        try:
            return sorted(self._folder().glob("*.rle"), key=lambda p: p.stat().st_mtime, reverse=True)
        except OSError:
            return []

    def _fill_saved(self):
        self.saved.clear()
        for path in self._saved_files():
            try:
                cells, rule, name, _o = parse_rle(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            item = QListWidgetItem(QIcon(thumbnail(normalise(cells), 36)), f"{name or path.stem}\n"
                                   f"{len(cells)} cells, {rule or 'B3/S23'}")
            item.setData(Qt.UserRole, str(path))
            self.saved.addItem(item)
        if self.category.currentText() == "My saved patterns":
            self._fill_gallery("My saved patterns")

    def save_world(self):
        name = self.save_name.text().strip() or f"World {self.world.generation}"
        safe = re.sub(r'[\\/:*?"<>|]+', "_", name)
        path = self._folder() / f"{safe}.rle"
        try:
            path.write_text(to_rle(self.world.live, self.rule_text(), name,
                                   f"Saved from Claude Life at generation {self.world.generation}"), encoding="utf-8")
        except OSError:
            host.message(self.desktop, TITLE, "The world couldn't be saved.", "error")
            return
        self.save_name.clear()
        self._fill_saved()
        host.message(self.desktop, TITLE, f"Saved as E:\\Created Files\\{TITLE}\\{path.name}", "info")

    def _selected_path(self):
        item = self.saved.currentItem()
        return Path(item.data(Qt.UserRole)) if item is not None else None

    def load_file(self, path):
        try:
            cells, rule, _name, offset = parse_rle(Path(path).read_text(encoding="utf-8", errors="replace"))
        except OSError:
            host.message(self.desktop, TITLE, "That file couldn't be read.", "error")
            return
        if not cells:
            host.message(self.desktop, TITLE, "There's no pattern in that file.", "warning")
            return
        self.pause()
        self.begin_edit()
        if offset is None:                      # (no position saved: in the middle of the view)
            cells = normalise(cells)
            w = max(c[0] for c in cells) + 1
            h = max(c[1] for c in cells) + 1
            b = self.board
            cx, cy = int(b.ox + b.width() / b.cell / 2), int(b.oy + b.height() / b.cell / 2)
            if self.world.edges != EDGES[0]:
                cx, cy = self.world.size[0] // 2, self.world.size[1] // 2
            cells = [(x + cx - w // 2, y + cy - h // 2) for x, y in cells]
        else:
            cells = [(x + offset[0], y + offset[1]) for x, y in cells]
        self.world.live.clear()
        self.world.age.clear()
        self.world.trail.clear()
        self.world.generation = 0
        for c in cells:
            self.world.set(c, True)
        if rule:
            parsed = parse_rule(rule)
            if parsed is not None and 0 not in parsed[0]:
                self.world.birth, self.world.survive = parsed
                self.rule_edit.setText(self.rule_text())
                self.rule_box.blockSignals(True)
                self.rule_box.setCurrentText(next((k for k, v in RULES.items() if v == self.rule_text()), "Custom"))
                self.rule_box.blockSignals(False)
        self.start_snap = None
        self.changed()
        self.board.fit()

    def load_selected(self):
        path = self._selected_path()
        if path is not None:
            self.load_file(path)

    def stamp_selected(self):
        path = self._selected_path()
        if path is None:
            return
        try:
            cells, _r, name, _o = parse_rle(path.read_text(encoding="utf-8"))
        except OSError:
            return
        if cells:
            self.stamp = (name or path.stem, normalise(cells))
            self.turns, self.flipped = 0, False
            self.about.setText(f"<b>{name or path.stem}</b> ({len(cells)} cells)<br>One of your saved patterns.")
            self.set_tool("stamp")
            self.board.setFocus()

    def delete_selected(self):
        path = self._selected_path()
        if path is None:
            return

        def answer(button):
            if button == "Yes":
                try:
                    path.unlink()
                except OSError:
                    pass
                self._fill_saved()
        host.message(self.desktop, TITLE, f"Delete '{path.stem}'?", "question", ("Yes", "No"), answer)

    def open_file(self):
        host.open_dialog(self.desktop, "Open Pattern", [".rle", ".cells", ".lif", ".txt"], self.load_file,
                         life_icon(), start=self._folder())

    def open_folder(self):
        host.open_folder(self.desktop, self._folder())

    def save_image(self):
        folder = self._folder()
        n = 1
        while (folder / f"Life {n:03d}.png").exists():
            n += 1
        path = folder / f"Life {n:03d}.png"
        if self.board.grab().save(str(path)):
            host.message(self.desktop, TITLE, f"Saved as E:\\Created Files\\{TITLE}\\{path.name}", "info")

    # ---- keys and status ----
    def key(self, e):
        k = e.key()
        ctrl = e.modifiers() & Qt.ControlModifier
        b = self.board
        if ctrl and k in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
            step = 40 / b.cell
            b.ox += {Qt.Key_Left: -step, Qt.Key_Right: step}.get(k, 0)
            b.oy += {Qt.Key_Up: -step, Qt.Key_Down: step}.get(k, 0)
            b.update()
            return True
        if ctrl and k == Qt.Key_Z:
            self.step_back()
            return True
        actions = {Qt.Key_Space: self.toggle_run, Qt.Key_N: self.step_once, Qt.Key_Right: self.step_once,
                   Qt.Key_B: self.step_back, Qt.Key_Left: self.step_back, Qt.Key_Home: self.reset,
                   Qt.Key_Delete: self.clear, Qt.Key_Plus: lambda: b.zoom(1.25), Qt.Key_Equal: lambda: b.zoom(1.25),
                   Qt.Key_Minus: lambda: b.zoom(0.8), Qt.Key_F: b.fit, Qt.Key_R: self.turn, Qt.Key_M: self.flip,
                   Qt.Key_Escape: lambda: self.set_tool("draw"), Qt.Key_D: lambda: self.set_tool("draw"),
                   Qt.Key_E: lambda: self.set_tool("erase"), Qt.Key_S: lambda: self.set_tool("stamp"),
                   Qt.Key_G: lambda: self.show_grid_box.toggle(), Qt.Key_A: lambda: self.age_colours_box.toggle(),
                   Qt.Key_T: lambda: self.trails_box.toggle()}
        act = actions.get(k)
        if act is None:
            return False
        act()
        return True

    def update_status(self):
        w = self.world
        b = self.board
        where = f"   Cell: {b.hover[0]}, {b.hover[1]}" if b.hover else ""
        tool = {"draw": "Draw", "erase": "Erase", "pan": "Move", "stamp": f"Stamp: {self.stamp[0]}"
                if self.stamp else "Stamp"}[self.tool]
        state = "Running" if self.timer.isActive() else "Paused"
        cycle = f"   <b>{self.cycle}</b>" if self.cycle else ""
        self.status.setText(f"Generation: <b>{w.generation:,}</b>   Population: <b>{len(w.live):,}</b>   "
                            f"(+{w.births} / -{w.deaths})   {self.rule_text()}   {state}   Zoom: {b.cell:g}px   "
                            f"{tool}{where}{cycle}")

    def closeEvent(self, event):
        self.timer.stop()
        self._save_settings()
        self._save_world()
        event.accept()


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = ClaudeLife(desktop)
        win = host.window(desktop, TITLE, body, life_icon(), (1020, 660))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.timer.stop()
        win.content._save_settings()
        win.content._save_world()
