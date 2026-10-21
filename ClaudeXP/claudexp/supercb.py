"""Super Claude Bros: a Super Mario Bros. clock screen saver, after Game & Watch: Super Mario Bros.

Mario runs through the world (hills, trees or clouds over the ground, in the theme's colours), jumping pipes, pits,
hard-block walls and staircases and bumping '?' blocks for coins, while Goombas, Koopas
and Buzzy Beetles walk in from the right: he stomps them, jumps them, and now and then gets caught and dies (and a new
life runs in). The time is spelled out in brick blocks, with a '?' block colon; when the minute changes he runs under
the digit and bumps it: the old bricks break, the new ones appear and a coin pops out.

The pictures come from the sprite sheets in Local Storage/SMB Clock (the Spriters Resource's NES sheets). The scene is
drawn at the NES's own size (240 lines, as wide as the screen's shape needs) and scaled up without smoothing.
Sound effects come from Local Storage/SMB Clock/sounds (jumps, stomps, kicks, coins, bumps, breaking bricks, deaths,
a 1-Up on the hour, 'hurry up' at :59 and the warp pipe when the world changes), on the real screen saver only.
Settings (Display Properties > Screen Saver > Settings): character, world (and how often it changes: every 5, 30 or
60 minutes), scenery, 24-hour clock, sound effects on or off."""
import math
import random
import time
from array import array

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter

FOLDER = "SMB Clock"
SHEETS = {"chars": "NES - Super Mario Bros. - Playable Characters - Mario & Luigi.png",
          "enemies": "NES - Super Mario Bros. - Enemies & Bosses - Enemies & Bosses.png",
          "blocks": "NES - Super Mario Bros. - Miscellaneous - Item and Brick Blocks.png",
          "items": "NES - Super Mario Bros. - Miscellaneous - Items, Objects and NPCs.png",
          "tiles": "NES - Super Mario Bros. - Miscellaneous - Tileset.png",
          "hills": "NES - Super Mario Bros. - Backgrounds - Background 1 (Mountains).png",
          "trees": "NES - Super Mario Bros. - Backgrounds - Background 2 (Trees).png",
          "clouds": "NES - Super Mario Bros. - Backgrounds - Background 3 (Clouds).png"}
CLEAR = {0xFF00298C, 0xFF9290FF, 0xFF8886FF, 0xFF6C6AFF}    # the sheets' backdrop and box colours: see-through

# character -> (x of the frame boxes, y, height): stand, run 1-3, skid, jump, (small only) dead
CHARACTERS = {"Mario": (0, 8, 16), "Luigi": (288, 8, 16), "Super Mario": (0, 32, 32), "Super Luigi": (288, 32, 32),
              "Fire Mario": (0, 140, 32)}
FRAME_X = [0, 20, 38, 56, 76, 96, 116]
# theme -> scenery band, sky, block group/row, ground tile, goomba and koopa offsets, enemy kinds
THEMES = {
    "Overworld": {"band": 0, "sky": "#5C94FC", "group": 0, "row": 0, "ground": (0, 16), "goomba": 0, "koopa": 0,
                  "enemies": ["goomba", "goomba", "koopa"]},
    "Underground": {"band": 1, "sky": "#000000", "group": 1, "row": 1, "ground": (147, 16), "goomba": 74,
                    "koopa": 146, "enemies": ["goomba", "goomba", "buzzy", "koopa"]},
    "Castle": {"band": 2, "sky": "#000000", "group": 1, "row": 2, "ground": (0, 100), "goomba": 148, "koopa": 146,
               "enemies": ["goomba", "buzzy", "koopa"]},
    "Underwater": {"band": 3, "sky": "#2038EC", "group": 0, "row": 3, "ground": (147, 100), "goomba": 222,
                   "koopa": 292, "enemies": ["goomba", "koopa"]},
    "Mushroom Kingdom": {"band": 4, "sky": "#5C94FC", "group": 0, "row": 0, "ground": (0, 16), "goomba": 0,
                         "koopa": 0, "enemies": ["goomba", "goomba", "koopa"]},
    "Snowy Night": {"band": 5, "sky": "#000000", "group": 0, "row": 2, "ground": (0, 100), "goomba": 148,
                    "koopa": 0, "enemies": ["goomba", "koopa"]},
}
CHANGING = "Changes now and then"
THEME_CHOICES = [CHANGING] + list(THEMES)
EVERY = {"Every 5 minutes": 5, "Every 30 minutes": 30, "Every hour": 60}
SCENERY = {"Hills": "hills", "Trees": "trees", "Clouds": "clouds"}
SCENERY_CHOICES = ["Mixed"] + list(SCENERY)
DEFAULTS = {"character": "Mario", "theme": CHANGING, "scenery": "Mixed", "clock24": False, "sound": True,
            "every": 30}
SOUNDS = "sounds"             # in the SMB Clock folder: the game's sound effects (.wav)
DIGITS = {"0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111",
          "4": "101101111001001", "5": "111100111001111", "6": "111100111101111", "7": "111001001001001",
          "8": "111101111101111", "9": "111101111001111"}
H = 240                       # the NES's lines
GROUND = 208                  # top of the ground (two block rows below it)
CLOCK_TOP = 40
GRAVITY = 0.25


def settings():
    from . import display
    data = display.get().data.get("supercb") or {}
    return {k: data.get(k, v) for k, v in DEFAULTS.items()}


def save_settings(values):
    from . import display
    d = display.get()
    d.data["supercb"] = {k: values.get(k, v) for k, v in DEFAULTS.items()}
    d._save()


# ---- pictures ------------------------------------------------------------------------------------------------------
_sheets = {}
_cache = {}


def _folder():
    from .explorer.vfs import local_storage
    return local_storage() / FOLDER


def available():
    return all((_folder() / f).exists() for f in SHEETS.values())


def _sheet(key):
    if key not in _sheets:
        img = QImage(str(_folder() / SHEETS[key]))
        _sheets[key] = img.convertToFormat(QImage.Format_ARGB32) if not img.isNull() else QImage()
    return _sheets[key]


def _clear(img):
    """The sheet's backdrop colours made see-through."""
    img = img.convertToFormat(QImage.Format_ARGB32)
    w, h = img.width(), img.height()
    px = array("I")
    px.frombytes(bytes(img.constBits())[:w * h * 4])
    out = array("I", [0 if v in CLEAR else v for v in px])
    return QImage(out.tobytes(), w, h, w * 4, QImage.Format_ARGB32).copy()


def cut(key, x, y, w, h, flip=False):
    k = (key, x, y, w, h, flip)
    if k not in _cache:
        img = _clear(_sheet(key).copy(x, y, w, h))
        if flip:
            img = img.mirrored(True, False)
        _cache[k] = img
    return _cache[k]


def band(scenery, index):
    """A theme's scenery (three screens wide, 240 lines), sky see-through."""
    k = ("band", scenery, index)
    if k not in _cache:
        sheet = _sheet(scenery)
        bands = (sheet.height() - 8) // 248
        index = index if index < bands else 0
        _cache[k] = _clear(sheet.copy(0, 8 + 248 * index, 768, 240))
    return _cache[k]


# ---- the world --------------------------------------------------------------------------------------------------------
TILE = 16
FLOAT_Y = GROUND - 80          # floating brick and '?' rows: five blocks up, clear of an ordinary jump
PIT = -1


class Thing:
    def __init__(self, kind, x, y, w, h):
        self.kind, self.x, self.y, self.w, self.h = kind, x, y, w, h      # x: world position
        self.vx = self.vy = 0.0
        self.state = "walk"
        self.t = 0
        self.decided = None


class SuperClaudeBros:
    """The game: the terrain, Mario, the enemies, the clock and what's flying about. Steps 60 times a second.

    Everything has a world position; the camera follows Mario (and stops while he deals with the clock). The terrain
    is made ahead of the camera, column by column: flat ground, pipes, pits, hard-block walls and staircases, with
    floating rows of bricks and '?' blocks."""

    def __init__(self, width=320, now=None):
        self.cfg = settings()
        self.W = width
        self.now = now or time.localtime
        self.frame = 0
        self.cam = 0.0
        self.speed = 1.5
        self.theme_name = ""
        self.hour = None
        self.sounds = []
        self._pick_theme()
        self.char = self.cfg["character"] if self.cfg["character"] in CHARACTERS else "Mario"
        self.big = CHARACTERS[self.char][2] == 32
        self.home = self.W * 0.3
        self.cols = {}            # column -> top of the solid there (GROUND if not listed), or PIT
        self.cells = set()        # (column, y) hard blocks
        self.pipes = {}           # first column -> height in blocks
        self.floats = {}          # (column, y) -> "brick" / "question" / "used"
        self.float_bumps = {}     # (column, y) -> frames left of its bump
        self.plans = {}           # obstacle column -> what Mario does there ("jump" / "miss" / "bump")
        self.gen_col = int(self.W // TILE) + 4          # the first screen is flat
        self.enemies = []
        self.bits = []            # debris, coins, scores
        self.bumps = {}           # clock brick -> frames left of its bump
        self.shown = self._time_text()
        self.pending = None
        self.next_enemy = 90
        self.mario = Thing("mario", -20, 0, 16, CHARACTERS[self.char][2])
        self.mario.y = GROUND - self.mario.h
        self.mario.state = "enter"
        self.sounds = []          # sound effects to play (the screen saver takes them each frame)
        self._generate()

    def sfx(self, name):
        self.sounds.append(name)

    # ---- theme ----
    def _pick_theme(self):
        """The world (and, when mixed, the scenery) for this stretch of the day: a new one every 5, 30 or 60
        minutes (Settings), the same all through the stretch."""
        t = self.now()
        every = int(self.cfg.get("every") or 30)
        stretch = (t.tm_hour * 60 + t.tm_min) // max(1, every)
        if self.hour == stretch and self.theme_name:
            return
        first = not self.theme_name
        self.hour = stretch
        choice = self.cfg["theme"]
        old = (self.theme_name, getattr(self, "scenery", ""))
        if choice in THEMES:
            self.theme_name = choice
        else:
            rng = random.Random(f"{time.strftime('%Y%m%d')}:{every}:{stretch}")
            self.theme_name = rng.choice([n for n in THEMES if n != self.theme_name] or list(THEMES))
        sc = self.cfg["scenery"]
        self.scenery = SCENERY.get(sc) or random.Random(f"{stretch}:{self.theme_name}").choice(list(SCENERY.values()))
        self.theme = THEMES[self.theme_name]
        if not first and (self.theme_name, self.scenery) != old:
            self.sfx("pipepowerdown")                   # (down the warp pipe, into somewhere new)

    # ---- the clock ----
    def _time_text(self):
        t = self.now()
        if self.cfg["clock24"]:
            return f"{t.tm_hour:02d}:{t.tm_min:02d}"
        h = t.tm_hour % 12 or 12
        return f"{h:>2d}:{t.tm_min:02d}"

    def clock_cells(self, text=None):
        """{(digit index, col, row): (x, y)} of every brick in the clock (screen positions), and the colon's two
        '?' blocks."""
        text = text if text is not None else self.shown
        widths = [16 if ch == ":" else 48 for ch in text]
        total = sum(widths) + 8 * (len(text) - 1)
        x = (self.W - total) // 2
        cells, colon = {}, []
        for i, ch in enumerate(text):
            if ch == ":":
                colon += [(x, CLOCK_TOP + 16), (x, CLOCK_TOP + 48)]
            elif ch in DIGITS:
                for n, bit in enumerate(DIGITS[ch]):
                    if bit == "1":
                        cells[(i, n % 3, n // 3)] = (x + 16 * (n % 3), CLOCK_TOP + 16 * (n // 3))
            x += widths[i] + 8
        return cells, colon

    def digit_x(self, index, text):
        widths = [16 if ch == ":" else 48 for ch in text]
        total = sum(widths) + 8 * (len(text) - 1)
        return (self.W - total) // 2 + sum(widths[:index]) + 8 * index + 24

    # ---- the terrain ----
    def top(self, col):
        """The top of the solid in a column (GROUND for plain ground), or None over a pit."""
        t = self.cols.get(col, GROUND)
        return None if t == PIT else t

    def _span(self, x, w=16):
        return range(int(math.floor((x + 3) / TILE)), int(math.floor((x + w - 4) / TILE)) + 1)

    def floor(self, x, feet, w=16):
        """The highest surface at or below these feet, under a body at world x; None if there's nothing (a pit)."""
        best = None
        for col in self._span(x, w):
            for t in [self.top(col)] + [y for (c, y) in self.floats if c == col]:
                if t is not None and t >= feet - 2 and (best is None or t < best):
                    best = t
        return best

    def wall(self, x, feet, w=16):
        """Is there a solid side in the way of a body at world x whose feet are here?"""
        for col in self._span(x, w):
            t = self.top(col)
            if t is not None and t < feet - 1:
                return True
        return False

    def _flat(self, col0, col1):
        return all(self.cols.get(c, GROUND) == GROUND for c in range(col0, col1)) and \
            not any(col0 <= c < col1 for (c, _y) in self.floats)

    def _generate(self):
        """Make terrain until there's some beyond the right of the screen."""
        while self.gen_col * TILE < self.cam + self.W + 96:
            c = self.gen_col
            if self.pending or self.mario.state in ("dead", "gone", "enter"):
                self.gen_col += 4                       # (flat ground while the clock is due)
                continue
            run = random.randint(5, 12)
            if random.random() < 0.4 and run >= 10:     # a floating row over the flat stretch, clear of the
                length = random.randint(3, min(5, run - 7))         # obstacles at each end (they'd spoil his jumps)
                start = c + random.randint(3, run - 4 - length)
                for i in range(length):
                    self.floats[(start + i, FLOAT_Y)] = random.choice(["brick", "brick", "question"])
            c += run
            kind = random.choices(["pipe", "pit", "wall", "stairs"], [32, 24, 20, 24])[0]
            if kind == "pipe":
                h = random.randint(2, 4)
                self.pipes[c] = h
                for i in (0, 1):
                    self.cols[c + i] = GROUND - TILE * h
                c += 2
            elif kind == "pit":
                w = random.randint(2, 3)
                for i in range(w):
                    self.cols[c + i] = PIT
                self.plans[c] = "miss" if random.random() < 0.06 else "jump"
                c += w
            elif kind == "wall":
                h, w = random.randint(1, 3), random.randint(1, 2)
                for i in range(w):
                    self.cols[c + i] = GROUND - TILE * h
                    for k in range(h):
                        self.cells.add((c + i, GROUND - TILE * (k + 1)))
                c += w
            else:                                       # a staircase up, a flat top, and back down
                n = random.randint(2, 4)
                heights = list(range(1, n + 1)) + [n] * random.randint(0, 1) + list(range(n, 0, -1))
                for i, h in enumerate(heights):
                    self.cols[c + i] = GROUND - TILE * h
                    for k in range(h):
                        self.cells.add((c + i, GROUND - TILE * (k + 1)))
                c += len(heights)
            self.gen_col = c
        gone = int(self.cam // TILE) - 4                # forget what's behind the camera
        for d in (self.cols, self.pipes, self.plans):
            for key in [k for k in d if (k if isinstance(k, int) else k[1][0]) < gone]:   # (('q', block) plans)
                del d[key]
        self.cells = {cell for cell in self.cells if cell[0] >= gone}
        for key in [k for k in self.floats if k[0] < gone]:
            del self.floats[key]

    def _flatten(self, col0, col1):
        """Plain ground here (a new life starts on it)."""
        for col in range(col0, col1):
            self.cols.pop(col, None)
            self.pipes.pop(col, None)
        self.cells = {cell for cell in self.cells if not col0 <= cell[0] < col1}
        for key in [k for k in self.floats if col0 <= k[0] < col1]:
            del self.floats[key]
        for col in range(col0 - 1, col1):               # (a pipe half in the cleared part)
            if col in self.pipes and col + 1 >= col0:
                self.pipes.pop(col)
                self.cols.pop(col, None)
                self.cols.pop(col + 1, None)
        self.gen_col = max(self.gen_col, col1)

    # ---- stepping ----
    def step(self):
        self.frame += 1
        if self.frame % 60 == 0:
            self._pick_theme()
            new = self._time_text()
            if new != self.shown and self.pending is None:
                self.pending = new
        m = self.mario
        grounded = m.state in ("run", "to_clock") and (m.state == "to_clock" or self.on_ground(m))
        self._mario(m)
        if grounded and m.vy < -2 and m.state in ("run", "clock_jump"):
            self.sfx("jump" if self.big else "jumpsmall")
        if m.state == "run":
            self.cam = max(self.cam, m.x - self.home)   # the camera follows him, never backwards
        self._generate()
        self._enemies(m)
        for b in list(self.bits):
            b.t += 1
            b.x += b.vx
            b.y += b.vy
            b.vy += GRAVITY if b.kind in ("debris", "coin") else 0
            if b.kind == "coin" and b.vy > 2:
                self.bits.remove(b)
                self._score(b.x, b.y, "200")
            elif b.y > H or b.t > (40 if b.kind == "score" else 200):
                self.bits.remove(b)
        for d in (self.bumps, self.float_bumps):
            for cell in list(d):
                d[cell] -= 1
                if d[cell] <= 0:
                    del d[cell]

    def on_ground(self, m):
        f = self.floor(m.x, m.y + m.h)
        return f is not None and m.vy >= 0 and abs((m.y + m.h) - f) < 0.5

    def _move_x(self, m, dx):
        """Walk, unless a wall is in the way."""
        if dx and not self.wall(m.x + dx, m.y + m.h):
            m.x += dx
            return True
        return False

    def _move_y(self, m):
        """Gravity, landing, and bumping blocks from below."""
        m.vy = min(m.vy + GRAVITY, 6.0)
        feet = m.y + m.h
        f = self.floor(m.x, feet)
        m.y += m.vy
        if m.vy < 0:                                    # rising: a floating block overhead stops him
            for col in self._span(m.x):
                key = (col, FLOAT_Y)
                if key in self.floats and m.y < FLOAT_Y + TILE <= m.y - m.vy + 0.01:
                    m.y, m.vy = FLOAT_Y + TILE, 1.0
                    self._bump_float(key)
                    break
        elif f is not None and m.y + m.h >= f:
            m.y, m.vy = f - m.h, 0.0

    def _bump_float(self, key):
        self.float_bumps[key] = 10
        self.sfx("coin" if self.floats[key] == "question" else "bump")
        if self.floats[key] == "question":
            self.floats[key] = "used"
            coin = Thing("coin", key[0] * TILE + 4, FLOAT_Y - 16, 8, 16)
            coin.vy = -5
            self.bits.append(coin)

    def _look_ahead(self, m):
        """Jump for what's coming: a rise (pipe, wall, step), a pit, or a '?' block worth bumping."""
        feet = m.y + m.h
        for d in range(0, 72, 2):
            col = int((m.x + 13 + d) // TILE)
            t = self.top(col)
            if t is None:                               # a pit: leap from its edge (or, now and then, don't)
                first = col
                while self.top(first - 1) is None:
                    first -= 1
                if d <= 4:
                    if self.plans.get(first) == "miss":
                        return
                    m.vy = -5.6
                return
            if t < feet - 1:                            # something to get up onto or over
                h = feet - min(self.top(col + i) or GROUND for i in range(2)) if self.pipes.get(col) else \
                    feet - t                            # (a pipe all at once; steps one at a time)
                v = min(7.2, max(4.2, math.sqrt(2 * GRAVITY * (h + 10))))
                rise = h + 4                            # be this far up by the time he gets there
                if v * v <= 2 * GRAVITY * rise:
                    t_up = v / GRAVITY
                else:
                    t_up = (v - math.sqrt(v * v - 2 * GRAVITY * rise)) / GRAVITY
                if d <= self.speed * t_up + 2:
                    m.vy = -v
                return
        for col in self._span(m.x):                     # a '?' overhead: sometimes he bumps it
            key = (col, FLOAT_Y)
            if self.floats.get(key) == "question" and self.plans.get(("q", key)) is None:
                self.plans[("q", key)] = random.random() < 0.6
                if self.plans[("q", key)]:
                    m.vy = -6.8
                return

    def _air_speed(self, m):
        """In the air, heading for a pit he's not meant to fall in: push on (like a running jump) to clear it."""
        if self.on_ground(m):
            return self.speed
        feet, v = m.y + m.h, m.vy
        drop = GROUND - feet
        frames = (v + math.sqrt(max(0.0, v * v + 2 * GRAVITY * drop))) / GRAVITY
        land = m.x + self.speed * frames
        cols = list(self._span(land))
        if all(self.top(c) is not None for c in cols):
            return self.speed
        first = cols[0] if self.top(cols[0]) is None else cols[-1]
        while self.top(first - 1) is None:
            first -= 1
        if self.plans.get(first) == "miss":
            return self.speed
        return 2.8

    def _mario(self, m):
        m.t += 1
        if m.state == "enter":                          # a new life runs in from the left
            m.facing = 1
            m.x += self.speed
            if m.x >= self.cam + self.home:
                m.state = "run"
            return
        if m.state == "dead":
            if m.t == 30:
                m.vy = -5.0
            if m.t > 30:
                m.vy += GRAVITY
                m.y += m.vy
            if m.y > H + 20:
                m.state, m.t = "gone", 0
            return
        if m.state == "gone":
            if m.t > 90:                                # a new life, on cleared ground
                self.enemies = []
                c0 = int(self.cam // TILE) - 2
                self._flatten(c0, c0 + int(self.W // TILE) + 8)
                m.x, m.y, m.vy = self.cam - 20, GROUND - m.h, 0.0
                m.state, m.t = "enter", 0
            return
        if m.y > H:                                     # fell down a pit
            m.state, m.t = "gone", 0
            self.sfx("death")
            return
        if self.pending and m.state == "run" and self.on_ground(m) and abs(m.y + m.h - GROUND) < 1 and \
                self._flat(int(self.cam // TILE), int((self.cam + self.W) // TILE) + 1):
            m.state = "to_clock"
            changed = [i for i, (a, b) in enumerate(zip(self.shown.ljust(len(self.pending)), self.pending)) if a != b]
            self.target = self.cam + self.digit_x(changed[0] if changed else 0, self.pending) - 8
        if m.state == "to_clock":
            d = self.target - m.x
            m.facing = 1 if d > 0 else -1
            if abs(d) <= 1.5:
                m.x = self.target
                m.state, m.vy = "clock_jump", -6.4
            else:
                m.x += 1.5 * (1 if d > 0 else -1)
            return
        if m.state == "clock_jump":
            m.vy += GRAVITY
            m.y += m.vy
            if m.vy < 0 and m.y <= CLOCK_TOP + 80:      # his head hits the bottom of the clock
                m.y = CLOCK_TOP + 80
                m.vy = 1.0
                self._change_clock()
            if m.y >= GROUND - m.h:
                m.y, m.vy = GROUND - m.h, 0
                m.state = "back"
            return
        if m.state == "back":
            d = self.cam + self.home - m.x
            m.facing = 1 if d > 0 else -1
            if abs(d) <= 1.5:
                m.x, m.state, m.facing = self.cam + self.home, "run", 1
            else:
                m.x += 1.5 * (1 if d > 0 else -1)
            return
        m.facing = 1                                    # running
        if self.on_ground(m):
            self._look_ahead(m)
        if self._move_x(m, self._air_speed(m)):
            m.blocked = 0
        else:
            m.blocked = getattr(m, "blocked", 0) + 1
            if m.blocked > 90:                          # (stuck under something: break it and carry on)
                m.blocked = 0
                m.vy = -7.2                             # (and a big jump, whatever's in front)
                for col in range(int(m.x // TILE) - 1, int(m.x // TILE) + 4):
                    if (col, FLOAT_Y) in self.floats:
                        del self.floats[(col, FLOAT_Y)]
                        for dx, dy, vx, vy in ((0, 0, -1, -4), (8, 0, 1, -4), (0, 8, -1, -2.5), (8, 8, 1, -2.5)):
                            b = Thing("debris", col * TILE + dx, FLOAT_Y + dy, 8, 8)
                            b.vx, b.vy = vx, vy
                            self.bits.append(b)
        self._move_y(m)

    def _change_clock(self):
        old_cells, _c = self.clock_cells(self.shown)
        new_cells, _c = self.clock_cells(self.pending)
        old_pos = set(old_cells.values())
        new_pos = set(new_cells.values())
        for x, y in old_pos - new_pos:                  # bricks that go: broken
            for dx, dy, vx, vy in ((0, 0, -1, -4), (8, 0, 1, -4), (0, 8, -1, -2.5), (8, 8, 1, -2.5)):
                b = Thing("debris", self.cam + x + dx, y + dy, 8, 8)
                b.vx, b.vy = vx, vy
                self.bits.append(b)
        for pos in new_pos:
            self.bumps[pos] = 10
        coin = Thing("coin", self.mario.x + 4, CLOCK_TOP + 64, 8, 16)
        coin.vy = -5
        self.bits.append(coin)
        self.sfx("brick" if old_pos - new_pos else "bump")
        self.sfx("coin")
        minute = self.pending[-2:]
        if minute == "00":
            self.sfx("1up")                             # (the top of the hour)
        elif minute == "59":
            self.sfx("hurryup")
        self.shown, self.pending = self.pending, None

    def _score(self, x, y, text):
        s = Thing("score", x, y, 16, 8)
        s.vy = -0.8
        s.text = text
        self.bits.append(s)

    def _spawn(self):
        kind = random.choice(self.theme["enemies"])
        h = 24 if kind == "koopa" else 16
        x = self.cam + self.W + 8
        col = int((x + 8) // TILE)
        if self.top(col) != GROUND or self.top(col + 1) != GROUND:
            return                                      # (only onto plain ground)
        e = Thing(kind, x, GROUND - h, 16, h)
        e.vx = -0.5
        e.decided = random.choices(["stomp", "over", "die"], [62, 28, 10])[0]
        self.enemies.append(e)

    def _enemies(self, m):
        if m.state == "run" and not self.pending:
            self.next_enemy -= 1
            if self.next_enemy <= 0 and len(self.enemies) < 3:
                self._spawn()
                self.next_enemy = random.randint(150, 420)
        for e in list(self.enemies):
            e.t += 1
            if e.state == "squished":
                if e.t > 30:
                    self.enemies.remove(e)
                continue
            if e.state in ("flipped", "falling"):
                e.vy += GRAVITY
                e.y += e.vy
                if e.y > H:
                    self.enemies.remove(e)
                continue
            if e.vx:                                    # walking (or a sliding shell): turn at walls, fall in pits
                if self.wall(e.x + e.vx, e.y + e.h):
                    if e.state == "shell":              # (a shell breaks on a wall rather than ping-ponging)
                        e.state, e.vy = "flipped", -3.0
                        if self.cam - 16 < e.x < self.cam + self.W:
                            self.sfx("kickkill")
                        continue
                    e.vx = -e.vx
                else:
                    e.x += e.vx
                if self.floor(e.x, e.y + e.h) is None:
                    e.state, e.vy = "falling", 0.0
                    continue
            if e.x < self.cam - 60 or e.x > self.cam + self.W + 80:
                self.enemies.remove(e)
                continue
            if m.state != "run":
                continue
            gap = e.x - m.x
            closing = self.speed - e.vx
            if e.state in ("walk", "shell") and e.vx and self.on_ground(m) and closing > 0.3 and \
                    e.decided in ("stomp", "over"):
                want = (80 if e.decided == "stomp" else 44) * closing / 2.0
                if want - closing - 1 < gap <= want + 1:
                    m.vy = -5.0                         # (a 40-frame jump: lands on it, or clears it)
            if e.state == "shell" and e.vx == 0 and abs(gap) < 12 and self.on_ground(m):
                e.vx, e.kicked = 4.0, e.t               # kick the shell away
                self.sfx("kickkill")
                e.decided = random.choice(["over", "over", "stomp"])
                self._score(e.x, e.y - 8, "400")
                continue
            if e.state == "shell" and e.t - getattr(e, "kicked", -99) < 30:
                continue                                # (just kicked: it's leaving, not hitting him)
            if e.t - getattr(e, "dodged", -99) < 45:
                continue
            if abs(gap) < 13 and m.y + m.h > e.y + 2 and m.y < e.y + e.h:
                if m.vy > 0 and m.y + m.h <= e.y + 10:  # landed on it
                    self._stomp(e)
                    m.vy = -3.0
                elif e.state == "walk" or (e.state == "shell" and e.vx != 0):
                    if self.big:                        # a big Mario knocks it away
                        e.state, e.vy = "flipped", -3.0
                        self.sfx("kickkill")
                        self._score(e.x, e.y - 8, "100")
                    elif e.decided == "die":            # the encounter that was meant to go wrong
                        m.state, m.t, m.vy = "dead", 0, 0.0
                        self.sfx("death")
                    else:                               # (one that turned round, or met him mid-jump: he hops it)
                        e.dodged = e.t
                        if self.on_ground(m):
                            m.vy = -5.0

    def _stomp(self, e):
        self.sfx("stompswim")
        if e.kind == "goomba":
            e.state, e.t, e.y, e.h, e.vx = "squished", 0, e.y + e.h - 8, 8, 0.0
            self._score(e.x, e.y - 12, "100")
        elif e.state == "walk":                         # koopas and buzzies go into their shells
            e.state, e.vx, e.y, e.h = "shell", 0.0, e.y + e.h - 16, 16
            self._score(e.x, e.y - 12, "100")
        elif e.vx == 0:                                 # jumping on a still shell kicks it
            e.vx, e.kicked = (4.0 if e.x >= self.mario.x else -4.0), e.t
            self.sfx("kickkill")
            self._score(e.x, e.y - 8, "400")
        else:
            e.vx = 0.0

    # ---- drawing ----
    def draw(self, p):
        th = self.theme
        cam = int(self.cam)
        p.fillRect(QRectF(0, 0, self.W, H), QColor(th["sky"]))
        bg = band(self.scenery, th["band"])
        off = -int(self.cam * 0.5) % 768                # (the scenery drifts at half speed)
        x = off - 768
        while x < self.W:
            p.drawImage(x, 0, bg)
            x += 768
        gx, gy = th["ground"]
        ground = cut("tiles", gx, gy, 16, 16)
        hard = cut("tiles", gx, gy + 17, 16, 16)
        c0, c1 = cam // TILE - 1, (cam + self.W) // TILE + 2
        for col in range(c0, c1):
            if self.top(col) is not None:
                for row in (GROUND, GROUND + 16):
                    p.drawImage(col * TILE - cam, row, ground)
        for col, y in self.cells:
            if c0 <= col < c1:
                p.drawImage(col * TILE - cam, y, hard)
        lip, body = cut("tiles", 112, 624, 32, 16), cut("tiles", 112, 640, 32, 16)
        for col, h in self.pipes.items():
            if c0 - 2 <= col < c1:
                top = GROUND - TILE * h
                p.drawImage(col * TILE - cam, top, lip)
                for y in range(top + 16, GROUND, 16):
                    p.drawImage(col * TILE - cam, y, body)
        for (col, y), kind in self.floats.items():
            if c0 <= col < c1:
                lift = math.sin(math.pi * self.float_bumps[(col, y)] / 10) * 5 if (col, y) in self.float_bumps else 0
                frame = [0, 0, 0, 1, 2, 1][(self.frame // 8) % 6]
                p.drawImage(col * TILE - cam, int(y - lift), self._block(kind, frame))
        self._draw_clock(p)
        for e in self.enemies:
            self._draw_enemy(p, e, cam)
        self._draw_mario(p, cam)
        for b in self.bits:
            self._draw_bit(p, b, cam)

    def _block(self, kind, frame=0):
        group, row = self.theme["group"], self.theme["row"]
        if kind == "brick":
            return cut("blocks", 272 + 96 * group, 112 + 16 * row, 16, 16)
        if kind == "question":
            return cut("blocks", 80 + 96 * group + 16 * frame, 112 + 16 * row, 16, 16)
        return cut("blocks", 80 + 96 * group + 64, 112 + 16 * row, 16, 16)    # used

    def _draw_clock(self, p):
        cells, colon = self.clock_cells()
        brick = self._block("brick")
        for pos in cells.values():
            lift = math.sin(math.pi * self.bumps[pos] / 10) * 5 if pos in self.bumps else 0
            p.drawImage(int(pos[0]), int(pos[1] - lift), brick)
        shimmer = [0, 0, 0, 1, 2, 1][(self.frame // 8) % 6]
        q = self._block("question", shimmer)
        for x, y in colon:
            p.drawImage(int(x), int(y), q)

    def _draw_enemy(self, p, e, cam):
        walk = (e.t // 10) % 2
        if e.kind == "goomba":
            ox = self.theme["goomba"]
            img = cut("enemies", ox + 36, 24, 16, 8) if e.state == "squished" else cut("enemies", ox + 18 * walk, 16,
                                                                                         16, 16)
        elif e.kind == "buzzy":
            ox = self.theme["goomba"]
            img = cut("enemies", ox + 36, 34, 16, 16) if e.state in ("shell", "flipped") else \
                cut("enemies", ox + 18 * walk, 34, 16, 16, flip=e.vx > 0)
        else:
            ox = self.theme["koopa"]
            img = cut("enemies", ox + 72, 120, 16, 16) if e.state in ("shell", "flipped") or e.h == 16 else \
                cut("enemies", ox + 18 * walk, 112, 16, 24, flip=e.vx > 0)
        if e.state == "flipped":
            img = img.mirrored(False, True)
        p.drawImage(int(e.x) - cam, int(e.y + e.h - img.height()), img)

    def _draw_mario(self, p, cam):
        m = self.mario
        if m.state == "gone":
            return
        x0, y0, h = CHARACTERS[self.char]
        if m.state == "dead":
            img = cut("chars", x0 + FRAME_X[6], 8, 16, 16) if not self.big else cut("chars", x0 + FRAME_X[0], y0, 16, h)
        else:
            grounded = m.state in ("enter", "to_clock", "back") or self.on_ground(m)
            if not grounded and m.state != "enter":
                f = 5
            elif m.state in ("run", "enter", "to_clock", "back"):
                f = 1 + (m.t // 5) % 3
            else:
                f = 0
            img = cut("chars", x0 + FRAME_X[f], y0, 16, h, flip=getattr(m, "facing", 1) < 0)
        p.drawImage(int(m.x) - cam, int(m.y + m.h - img.height()), img)

    def _draw_bit(self, p, b, cam):
        if b.kind == "debris":
            group, row = self.theme["group"], self.theme["row"]
            piece = cut("blocks", 272 + 96 * group + 32, 112 + 16 * row, 8, 8)
            p.drawImage(int(b.x) - cam, int(b.y), piece)
        elif b.kind == "coin":
            p.drawImage(int(b.x) - cam, int(b.y), cut("items", 180 + 10 * ((b.t // 4) % 4), 36, 8, 16))
        elif b.kind == "score":
            row = {"100": 26, "200": 36, "400": 46}[b.text]
            p.drawImage(int(b.x) - cam, int(b.y), cut("items", 234, row, 16, 8))


# ---- the screen saver -----------------------------------------------------------------------------------------------
def make_saver_class(Saver):
    class SuperClaudeBrosSaver(Saver):
        """The game, scaled up to the screen without smoothing."""
        FPS = 60

        def __init__(self, parent=None):
            super().__init__(parent)
            self.game = None
            self.missing = not available()
            self.effects = {}
            # sound only on the real thing (not the little monitor in Display Properties), when it's switched on
            self.audible = type(parent).__name__ == "ScreenSaverManager" and bool(settings()["sound"])
            if self.audible:
                for f in (_folder() / SOUNDS).glob("*.wav"):        # (loaded up front: they play at once)
                    self._effect(f.stem)

        def _effect(self, name):
            if name not in self.effects:
                from PySide6.QtCore import QUrl
                from PySide6.QtMultimedia import QSoundEffect
                e = QSoundEffect(self)
                e.setSource(QUrl.fromLocalFile(str(_folder() / SOUNDS / f"{name}.wav")))
                self.effects[name] = e
            return self.effects[name]

        def _play(self, names):
            from . import sound
            if not self.audible or sound.is_muted():
                return
            for name in dict.fromkeys(names):           # (each once per frame)
                if (_folder() / SOUNDS / f"{name}.wav").exists():
                    e = self._effect(name)
                    e.setVolume(0.7 * sound.wave_volume())
                    e.play()

        def _ensure(self):
            if self.missing or self.width() < 4:
                return None
            w = max(256, int(round(H * self.width() / max(1, self.height()))))
            if self.game is None or self.game.W != w:
                self.game = SuperClaudeBros(w)
            return self.game

        def step(self):
            g = self._ensure()
            if g is not None:
                g.step()
                if g.sounds:
                    self._play(g.sounds)
                    g.sounds.clear()

        def hideEvent(self, event):
            for e in self.effects.values():
                e.stop()
            super().hideEvent(event)

        def paintEvent(self, event):
            p = QPainter(self)
            p.fillRect(self.rect(), QColor("black"))
            g = self._ensure()
            if g is None:
                p.setPen(QColor("white"))
                f = QFont("Tahoma")
                f.setPixelSize(max(9, self.height() // 30))
                p.setFont(f)
                p.drawText(self.rect(), Qt.AlignCenter, "Super Claude Bros needs its sprite sheets in\n"
                           f"E:\\{FOLDER}")
                return
            frame = QImage(g.W, H, QImage.Format_ARGB32)
            q = QPainter(frame)
            g.draw(q)
            q.end()
            scale = min(self.width() / g.W, self.height() / H)
            w, h = g.W * scale, H * scale
            p.drawImage(QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h), frame)

    return SuperClaudeBrosSaver


def settings_dialog(desktop, on_done=None):
    """Display Properties > Screen Saver > Settings for Super Claude Bros."""
    from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QPushButton, QVBoxLayout
    from .network import DialogBody, _fixed_window
    s = settings()
    body = DialogBody()
    col = QVBoxLayout(body)
    form = QFormLayout()
    boxes = {}
    for key, label, items in (("character", "&Character:", list(CHARACTERS)), ("theme", "&World:", THEME_CHOICES),
                              ("scenery", "&Scenery:", SCENERY_CHOICES)):
        box = QComboBox()
        box.addItems(items)
        box.setCurrentText(s[key])
        form.addRow(label, box)
        boxes[key] = box
    every = QComboBox()
    every.addItems(list(EVERY))
    every.setCurrentText(next((k for k, v in EVERY.items() if v == int(s["every"] or 30)), "Every 30 minutes"))
    form.addRow("&Change world:", every)
    clock24 = QCheckBox("&24-hour clock")
    clock24.setChecked(bool(s["clock24"]))
    form.addRow(clock24)
    sound_on = QCheckBox("&Sound effects")
    sound_on.setChecked(bool(s["sound"]))
    form.addRow(sound_on)
    col.addLayout(form)
    row = QHBoxLayout()
    row.addStretch(1)
    ok, cancel = QPushButton("OK"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(75, 23)
        row.addWidget(b)
    col.addLayout(row)
    body.setFixedWidth(300)
    holder = {}

    def close():
        win = holder.get("win")
        if win is not None:
            desktop.close_window(win)

    def accept():
        save_settings({"character": boxes["character"].currentText(), "theme": boxes["theme"].currentText(),
                       "scenery": boxes["scenery"].currentText(), "clock24": clock24.isChecked(),
                       "sound": sound_on.isChecked(), "every": EVERY[every.currentText()]})
        close()
        if on_done:
            on_done()

    ok.clicked.connect(accept)
    cancel.clicked.connect(close)
    win = _fixed_window(desktop, "Super Claude Bros Setup", body, close)
    holder["win"] = win
    desktop.open_window(win)
    return win
