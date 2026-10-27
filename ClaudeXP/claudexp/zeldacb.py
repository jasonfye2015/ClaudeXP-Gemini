"""The Legend of Claude: a Legend of Zelda clock screen saver, after Super Claude Bros (supercb.py).

Link walks Hyrule - the real first-quest overworld, stitched from the map sheet - a screen at a time. On each screen
Octoroks, Moblins and Tektites appear in a puff of smoke; he lines up with one, swings his sword and it bursts, now
and then leaving a rupee or a heart he goes and picks up. Octoroks spit rocks and Moblins shoot arrows, and a hit
knocks him back a half-heart. When a screen is clear he walks out of it and the view scrolls to the next, as the
game does. The time is built in the middle of each screen out of that screen's own blocks - boulders in the
mountains, trees in the forest, tombstones in the graveyard - and he walks around it; when the minute changes the
old blocks go up in smoke and the new ones appear, and on the hour he holds up a piece of the Triforce. The HUD has
the overworld mini-map with where he is, his rupees and his hearts.

The pictures come from the sprite sheets in Local Storage/LOZ Sprites (the Spriters Resource's NES sheets, ripped by
Mister Mike). The scene is drawn at the NES's own size (240 lines, as wide as the screen's shape needs) and scaled up
without smoothing."""
import random
from array import array
from collections import deque
from datetime import datetime

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter

FOLDER = "LOZ Sprites"
SHEETS = {"map": "NES - The Legend of Zelda - Overworld - Overworld (First Quest).png",
          "link": "NES - The Legend of Zelda - Playable Characters - Link.png",
          "enemies": "NES - The Legend of Zelda - Enemies & Bosses - Overworld Enemies.png",
          "items": "NES - The Legend of Zelda - Miscellaneous - Items & Weapons.png",
          "death": "NES - The Legend of Zelda - Miscellaneous - Enemy Death.png",
          "hud": "NES - The Legend of Zelda - Miscellaneous - HUD & Pause Screen.png"}
CLEAR = {0xFF008000, 0xFF747474}             # the sheets' green backdrop and grey frame boxes: see-through
H, HUD, FIELD = 240, 64, 176                 # the NES's lines: the HUD, then the playfield
COLS, ROWS = 16, 8                           # overworld screens
SW, SH = 256, 176                            # a screen
GROUND = {(252, 216, 168), (116, 116, 116)}  # sand, and the graveyard's grey
WATER = (32, 56, 236)
CELL = 8                                     # the grid things walk on (half a tile, as the game does)
GW, GH = SW // CELL, SH // CELL
START = (7, 7)                               # the screen the game starts on
DIGITS = {"0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111",
          "4": "101101111001001", "5": "111100111001111", "6": "111100111101111", "7": "111001001001001",
          "8": "111101111101111", "9": "111101111001111"}
DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}

# Link: walking (two frames per way; left is right mirrored), and the sword (base, out, half, short)
LINK_WALK = {"down": [(1, 11), (18, 11)], "right": [(35, 11), (52, 11)], "up": [(69, 11), (86, 11)]}
LINK_SWORD = {"down": [(1, 47, 16, 16), (18, 47, 16, 27), (35, 47, 16, 23), (52, 47, 16, 19)],
              "right": [(1, 77, 16, 16), (18, 77, 27, 17), (46, 77, 23, 17), (70, 77, 19, 17)],
              "up": [(1, 109, 16, 16), (18, 97, 16, 28), (35, 98, 16, 27), (52, 106, 16, 19)]}
LINK_HOLD = (213, 11)
CLOUD = [(138, 185), (155, 185), (172, 185)]          # the smoke enemies appear in (and blocks go up in)
# enemies: walking frames for down and side (side faces left), and what they throw
ENEMIES = {"octorok": {"down": [(1, 11), (18, 11)], "side": [(35, 11), (52, 11)], "shot": (69, 11, 8, 16),
                       "hp": 1, "speed": 0.5},
           "blue octorok": {"down": [(1, 28), (18, 28)], "side": [(35, 28), (52, 28)], "shot": (69, 11, 8, 16),
                            "hp": 2, "speed": 0.75},
           "moblin": {"down": [(82, 11)], "up": [(99, 11)], "side": [(116, 11), (133, 11)], "shot": (150, 11, 8, 16),
                      "hp": 2, "speed": 0.5},
           "tektite": {"hop": [(162, 90), (179, 90)], "hp": 1}}


# ---- pictures ------------------------------------------------------------------------------------------------------
_sheets, _cache = {}, {}


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
    img = img.convertToFormat(QImage.Format_ARGB32)
    w, h = img.width(), img.height()
    px = array("I")
    px.frombytes(bytes(img.constBits())[:w * h * 4])
    out = array("I", [0 if v in CLEAR else v for v in px])
    return QImage(out.tobytes(), w, h, w * 4, QImage.Format_ARGB32).copy()


def cut(key, x, y, w=16, h=16, flip=False, upside=False):
    k = (key, x, y, w, h, flip, upside)
    if k not in _cache:
        img = _clear(_sheet(key).copy(x, y, w, h))
        if flip or upside:
            img = img.mirrored(flip, upside)
        _cache[k] = img
    return _cache[k]


def world():
    """Hyrule in one piece: the map sheet's 16 x 8 screens without the lines between them."""
    if "world" not in _cache:
        sheet = _sheet("map")
        img = QImage(COLS * SW, ROWS * SH, QImage.Format_ARGB32)
        img.fill(QColor("black"))
        p = QPainter(img)
        for r in range(ROWS):
            for c in range(COLS):
                p.drawImage(c * SW, r * SH, sheet, 1 + 257 * c, 1 + 177 * r, SW, SH)
        p.end()
        _cache["world"] = img
    return _cache["world"]


class Screen:
    """One overworld screen: where things can walk (8-pixel cells), and the block its clock is built of."""

    def __init__(self, col, row):
        self.col, self.row = col, row
        img = world().copy(col * SW, row * SH, SW, SH)
        w = SW
        px = array("I")
        px.frombytes(bytes(img.constBits())[:w * SH * 4])
        ground = {0xFF000000 | (r << 16) | (g << 8) | b for r, g, b in GROUND}
        self.walk = [[False] * GW for _ in range(GH)]
        for cy in range(GH):
            for cx in range(GW):
                hits = sum(1 for y in range(cy * CELL, cy * CELL + CELL) for x in range(cx * CELL, cx * CELL + CELL)
                           if px[y * w + x] in ground)
                self.walk[cy][cx] = hits >= 56
        self.open = sum(map(sum, self.walk)) / (GW * GH)
        sand = 0xFF000000 | (252 << 16) | (216 << 8) | 168
        grey = 0xFF747474
        self.ground = QColor(116, 116, 116) if px.count(grey) > px.count(sand) else QColor(252, 216, 168)
        green = px.count(0xFF00A800)
        brown = px.count(0xFF000000 | (200 << 16) | (76 << 8) | 12)
        if self.ground.red() == 116:
            kind = "tomb"
        else:
            kind = "boulder" if green >= brown else "bush"
        self.block = block(kind)


# the clock's blocks: Hyrule's own, the kind that stands out on a screen - a boulder among the trees, a bush in the
# mountains, a tombstone in the graveyard (where each is found on the stitched map, its most common one)
BLOCKS = {"bush": (2224, 400), "boulder": (0, 0), "tomb": (0, 352)}


def block(kind):
    k = ("block", kind)
    if k not in _cache:
        x, y = BLOCKS[kind]
        _cache[k] = world().copy(x, y, 16, 16)
    return _cache[k]


# ---- things that move ----------------------------------------------------------------------------------------------
class Thing:
    def __init__(self, kind, x, y):
        self.kind, self.x, self.y = kind, float(x), float(y)
        self.dir = "down"
        self.t = 0
        self.path = []
        self.state = "walk"
        self.vx = self.vy = 0.0

    def rect(self, shrink=2):
        return QRect(int(self.x) + shrink, int(self.y) + shrink, 16 - 2 * shrink, 16 - 2 * shrink)

    def cell(self):
        return int(round(self.x / CELL)), int(round(self.y / CELL))


class LegendOfClaude:
    def __init__(self, width=320, now=None):
        self.W = width
        self.now = now or datetime.now
        self.sounds = []
        self.screens = {}
        self.good = [(c, r) for r in range(ROWS) for c in range(COLS)]
        self.col, self.row = START
        self.scr = self.screen(*START)
        self.link = Thing("link", 120, 128)
        self.hearts, self.max_hearts, self.rupees = 6, 6, 0
        self.enemies, self.shots, self.bits = [], [], []
        self.came_from = None
        self.scroll = None                         # (from col, row, to col, row, frames done, frames)
        self.fade = 0
        self.screen_t = 0
        self.hold = 0                              # frames left holding the Triforce up
        self.text = self._time_text()
        self.blocks = self._blocks(self.text)
        self.smoke = []                            # (x, y, t) clouds where blocks went
        self.last_minute = self.now().minute
        self._spawn_enemies()

    # ---- the world ----
    def screen(self, col, row):
        if (col, row) not in self.screens:
            self.screens[(col, row)] = Screen(col, row)
        return self.screens[(col, row)]

    def _time_text(self):
        t = self.now()
        return f"{(t.hour % 12) or 12}:{t.minute:02d}"

    def clock_cells(self, text, y0=None):
        """[(x, y, char index)] in a screen's pixels: the time in 16-pixel blocks, across the middle, its top at y0
        (the current screen's own height for it when not given)."""
        if y0 is None:
            y0 = self.clock_y(self.scr, text)
        cells, x = [], 0
        for i, ch in enumerate(text):
            if ch == ":":
                cells += [(x, 1, i), (x, 3, i)]
                x += 2
                continue
            pattern = DIGITS[ch]
            for r in range(5):
                for c in range(3):
                    if pattern[r * 3 + c] == "1":
                        cells.append((x + c, r, i))
            x += 4 if i + 1 < len(text) and text[i + 1] != ":" else 3
            if i + 1 < len(text) and text[i + 1] == ":":
                x += 1
        width = x * 16
        x0 = ((SW - width) // 2 // CELL) * CELL
        return [(x0 + cx * 16, y0 + cy * 16, i) for cx, cy, i in cells]

    def _blocks(self, text):
        cells = self.clock_cells(text)
        self._grids(cells)
        return cells

    @staticmethod
    def plaza_of(cells):
        """The cleared ground a clock stands on: its blocks, and a cell all round."""
        x0, y0 = min(c[0] for c in cells) - CELL, min(c[1] for c in cells) - CELL
        x1, y1 = max(c[0] for c in cells) + 16 + CELL, max(c[1] for c in cells) + 16 + CELL
        return QRect(x0, y0, x1 - x0, y1 - y0)

    def plaza(self):
        return self.plaza_of(self.blocks)

    @staticmethod
    def _grid(scr, cells):
        """(free, free but for the blocks): where something 16 x 16 can stand with its corner at each cell, on
        this screen with this clock (its plaza is walkable ground, its blocks aren't)."""
        plaza = LegendOfClaude.plaza_of(cells)
        px0, py0 = plaza.left() // CELL, plaza.top() // CELL
        px1, py1 = (plaza.right() + 1) // CELL, (plaza.bottom() + 1) // CELL
        ground = [[scr.walk[y][x] or (px0 <= x < px1 and py0 <= y < py1) for x in range(GW)] for y in range(GH)]
        blocked = [[False] * GW for _ in range(GH)]
        for bx, by, _i in cells:
            for y in range(by // CELL, by // CELL + 2):
                for x in range(bx // CELL, bx // CELL + 2):
                    if 0 <= x < GW and 0 <= y < GH:
                        blocked[y][x] = True
        loose = [[False] * GW for _ in range(GH)]
        free = [[False] * GW for _ in range(GH)]
        for y in range(GH - 1):
            for x in range(GW - 1):
                if ground[y][x] and ground[y][x + 1] and ground[y + 1][x] and ground[y + 1][x + 1]:
                    loose[y][x] = True
                    free[y][x] = not (blocked[y][x] or blocked[y][x + 1] or blocked[y + 1][x] or blocked[y + 1][x + 1])
        return free, loose

    def _grids(self, cells):
        self.grid, self.loose = self._grid(self.scr, cells)

    def clock_y(self, scr, text):
        """Where the clock stands on a screen: the height that keeps the screen's ways in and out joined up (a clock
        across the only path would wall Link in), standing over scenery rather than paths where it can."""
        key = ("clock_y", len(text))
        if key in scr.__dict__:
            return scr.__dict__[key]
        best, best_score = 48, None
        for y0 in range(16, SH - 80 - 8 + 1, 8):
            cells = self.clock_cells(text, y0)
            free, _loose = self._grid(scr, cells)
            score = (self._joined_edges(free), -sum(scr.walk[by // CELL][bx // CELL] for bx, by, _i in cells))
            if best_score is None or score > best_score:
                best, best_score = y0, score
        scr.__dict__[key] = best
        return best

    @staticmethod
    def _joined_edges(free):
        """The most edges of the screen one walkable area reaches (left, right, top, bottom)."""
        seen = [[False] * GW for _ in range(GH)]
        best = 0
        for sy in range(GH - 1):
            for sx in range(GW - 1):
                if not free[sy][sx] or seen[sy][sx]:
                    continue
                edges, q = set(), deque([(sx, sy)])
                seen[sy][sx] = True
                while q:
                    x, y = q.popleft()
                    if x == 0:
                        edges.add("left")
                    if x == GW - 2:
                        edges.add("right")
                    if y == 0:
                        edges.add("up")
                    if y == GH - 2:
                        edges.add("down")
                    for dx, dy in DIRS.values():
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GW - 1 and 0 <= ny < GH - 1 and free[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            q.append((nx, ny))
                best = max(best, len(edges))
        return best

    def free(self, cx, cy, ignore_blocks=False):
        """Can something 16 x 16 stand with its corner at cell (cx, cy)?"""
        if cx < 0 or cy < 0 or cx + 1 >= GW or cy + 1 >= GH:
            return False
        return (self.loose if ignore_blocks else self.grid)[cy][cx]

    def bfs(self, start, goal):
        """Cells from start to the nearest goal(cell) cell, or None."""
        q = deque([start])
        prev = {start: None}
        while q:
            c = q.popleft()
            if goal(c) and c != start:
                out = []
                while c != start:
                    out.append(c)
                    c = prev[c]
                return out[::-1]
            for dx, dy in DIRS.values():
                n = (c[0] + dx, c[1] + dy)
                if n not in prev and self.free(*n):
                    prev[n] = c
                    q.append(n)
        return None

    # ---- the clock ----
    def step(self):
        self.screen_t += 1
        for s in list(self.smoke):
            s[2] += 1
            if s[2] > 24:
                self.smoke.remove(s)
        t = self.now()
        if t.minute != self.last_minute:
            self.last_minute = t.minute
            new = self._time_text()
            old_cells = set(self.blocks)
            new_cells = self.clock_cells(new)
            keep = {(x, y) for x, y, _ in new_cells}
            for x, y, i in old_cells:
                if (x, y) not in keep or i >= len(new) or new[i] != self.text[i]:
                    self.smoke.append([x, y, 0])
            self.text = new
            self.blocks = self._blocks(new)
            self.sounds.append("bomb")
            if t.minute == 0:
                self.hold = 180
        if self.fade:
            self.fade -= 1
            if self.fade == 30:
                self._warp()
            return
        if self.scroll is not None:
            self._scroll_step()
            return
        self._link()
        self._enemies()
        self._shots()
        self._bits()

    # ---- Link ----
    def _link(self):
        L = self.link
        L.t += 1
        if self.hold:
            self.hold -= 1
            L.state = "hold"
            return
        if L.state == "hold":
            L.state = "walk"
        if L.state == "hurt":
            if L.t < 12:
                nx, ny = L.x + L.vx, L.y + L.vy
                if self.free(int(nx // CELL), int(ny // CELL), True):
                    L.x, L.y = nx, ny
                return
            L.state, L.path = "walk", []
            self._snap(L)
        if L.state == "attack":
            if L.t >= 14:
                L.state = "walk"
            elif 3 <= L.t <= 10:
                hit = self._sword_rect()
                for e in list(self.enemies):
                    if e.state not in ("dying", "appear") and hit.intersects(e.rect()):
                        self._hit(e)
            return
        out = getattr(L, "exit", None)
        if out and not L.path and self._at_edge(L, out):
            self._start_scroll(out)
            return
        if not L.path or (L.t % 30 == 0 and not out):
            self._plan()
        self._follow(L, 1.0)
        target = self._facing_enemy()
        if target is not None:
            L.state, L.t = "attack", 0
            self.sounds.append("sword")
        for b in list(self.bits):
            if L.rect(0).intersects(QRect(int(b["x"]), int(b["y"]), 8, 16)):
                self.bits.remove(b)
                if b["kind"] == "heart":
                    self.hearts = min(self.max_hearts, self.hearts + 2)
                else:
                    self.rupees = min(255, self.rupees + (5 if b["kind"] == "blue" else 1))
                self.sounds.append("rupee" if b["kind"] != "heart" else "heart")

    def _snap(self, t):
        cx, cy = t.cell()
        if not self.free(cx, cy):
            for r in range(1, 6):
                found = next(((cx + dx, cy + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)
                              if self.free(cx + dx, cy + dy)), None)
                if found:
                    cx, cy = found
                    break
        t.x, t.y = cx * CELL, cy * CELL

    def _plan(self):
        L = self.link
        start = L.cell()
        if not self.free(*start):
            self._snap(L)
            start = L.cell()
        if self.bits:                                  # a drop: go and get it
            goals = {(int(b["x"]) // CELL - 1 + dx, int(b["y"]) // CELL + dy) for b in self.bits
                     for dx in (0, 1) for dy in (-1, 0, 1)}
            path = self.bfs(start, lambda c: c in goals)
            if path:
                L.path = path
                return
        alive = [e for e in self.enemies if e.state not in ("dying", "appear")]
        if alive:
            spots = set()
            for e in alive:
                ex, ey = e.cell()
                spots |= {(ex - 2, ey), (ex + 2, ey), (ex, ey - 2), (ex, ey + 2)}
            path = self.bfs(start, lambda c: c in spots)
            if path:
                L.path = path
                return
            if self.screen_t < 600:                    # (out of reach - across water: give it a while)
                return
        if (not alive and self.screen_t > 90 and not self.enemies) or (alive and self.screen_t >= 600):
            self._head_out()

    def _head_out(self):
        """The screen is clear: out by an edge to a screen he can walk into."""
        L = self.link
        exits = []
        for name, (dx, dy) in DIRS.items():
            nc, nr = self.col + dx, self.row + dy
            if not (0 <= nc < COLS and 0 <= nr < ROWS) or self.screen(nc, nr).open < 0.2:
                continue
            exits.append((name, nc, nr))
        random.shuffle(exits)
        exits.sort(key=lambda e: e[0] == self.came_from)        # (not back the way he came, if he can help it)
        for name, nc, nr in exits:
            other = self.screen(nc, nr)
            if name == "left":
                goal = lambda c, o=other: c[0] == 0 and o.walk[c[1]][GW - 1] and o.walk[c[1] + 1][GW - 1]
            elif name == "right":
                goal = lambda c, o=other: c[0] == GW - 2 and o.walk[c[1]][0] and o.walk[c[1] + 1][0]
            elif name == "up":
                goal = lambda c, o=other: c[1] == 0 and o.walk[GH - 1][c[0]] and o.walk[GH - 1][c[0] + 1]
            else:
                goal = lambda c, o=other: c[1] == GH - 2 and o.walk[0][c[0]] and o.walk[0][c[0] + 1]
            path = self.bfs(L.cell(), goal)
            if path is not None or goal(L.cell()):
                L.path = path or []
                L.exit = name
                return
        L.exit = None
        if self.screen_t > 900:                      # nowhere to walk to: the recorder's whirlwind (a fade)
            self.fade = 60

    @staticmethod
    def _at_edge(t, name):
        cx, cy = t.cell()
        return {"left": cx == 0, "right": cx == GW - 2, "up": cy == 0, "down": cy == GH - 2}[name]

    def _follow(self, t, speed):
        if not t.path:
            return
        tx, ty = t.path[0][0] * CELL, t.path[0][1] * CELL
        dx, dy = tx - t.x, ty - t.y
        if abs(dx) > 0.01:
            t.dir = "right" if dx > 0 else "left"
            t.x += max(-speed, min(speed, dx))
        elif abs(dy) > 0.01:
            t.dir = "down" if dy > 0 else "up"
            t.y += max(-speed, min(speed, dy))
        if abs(t.x - tx) < 0.01 and abs(t.y - ty) < 0.01:
            t.x, t.y = tx, ty
            t.path.pop(0)

    def _sword_rect(self):
        L = self.link
        x, y = int(L.x), int(L.y)
        return {"down": QRect(x + 4, y + 12, 8, 14), "up": QRect(x + 4, y - 10, 8, 14),
                "right": QRect(x + 12, y + 4, 14, 8), "left": QRect(x - 10, y + 4, 14, 8)}[L.dir]

    def _facing_enemy(self):
        L = self.link
        if L.path and len(L.path) > 0 and not self._near_enemy(26):
            return None
        for e in self.enemies:
            if e.state in ("dying", "appear"):
                continue
            dx, dy = e.x - L.x, e.y - L.y
            if abs(dy) < 6 and 0 < abs(dx) <= 24:
                L.dir = "right" if dx > 0 else "left"
                return e
            if abs(dx) < 6 and 0 < abs(dy) <= 24:
                L.dir = "down" if dy > 0 else "up"
                return e
        return None

    def _near_enemy(self, d):
        L = self.link
        return any(abs(e.x - L.x) + abs(e.y - L.y) <= d for e in self.enemies if e.state not in ("dying", "appear"))

    def hurt(self, from_x, from_y):
        L = self.link
        if L.state in ("hurt", "hold"):
            return
        self.hearts = max(1, self.hearts - 1)
        dx, dy = L.x - from_x, L.y - from_y
        if abs(dx) > abs(dy):
            L.vx, L.vy = (2.0 if dx > 0 else -2.0), 0.0
        else:
            L.vx, L.vy = 0.0, (2.0 if dy > 0 else -2.0)
        L.state, L.t, L.path = "hurt", 0, []
        self.sounds.append("hurt")

    # ---- enemies ----
    def _spawn_enemies(self):
        self.enemies = []
        self.screen_t = 0
        if self.scr.open < 0.25:
            return
        kinds = ["octorok", "octorok", "blue octorok", "moblin", "tektite"]
        kind = random.choice(kinds)
        L = self.link
        cells = [(cx, cy) for cy in range(GH - 1) for cx in range(GW - 1) if self.free(cx, cy)
                 and abs(cx * CELL - L.x) + abs(cy * CELL - L.y) > 64]
        random.shuffle(cells)
        for cx, cy in cells[:random.randint(2, 5)]:
            e = Thing(kind, cx * CELL, cy * CELL)
            e.state, e.t = "appear", -random.randint(0, 40)
            e.hp = ENEMIES[kind]["hp"]
            e.reload = random.randint(90, 240)
            self.enemies.append(e)

    def _enemies(self):
        for e in list(self.enemies):
            e.t += 1
            if e.state == "appear":
                if e.t >= 24:
                    e.state, e.t = "walk", 0
                continue
            if e.state == "dying":
                if e.t > 16:
                    self.enemies.remove(e)
                    roll = random.random()
                    if roll < 0.35:
                        self.bits.append({"kind": "orange" if roll < 0.28 else "blue", "x": e.x + 4, "y": e.y, "t": 0})
                    elif roll < 0.5:
                        self.bits.append({"kind": "heart", "x": e.x + 4, "y": e.y + 4, "t": 0})
                continue
            if e.state == "flash":
                if e.t > 10:
                    e.state, e.t = "walk", 0
                continue
            if e.kind == "tektite":
                self._hop(e)
            else:
                if not e.path:
                    e.path = self._wander(e)
                self._follow(e, ENEMIES[e.kind]["speed"])
                e.reload -= 1
                if e.reload <= 0 and ENEMIES[e.kind].get("shot"):
                    e.reload = random.randint(120, 300)
                    dx, dy = DIRS[e.dir]
                    self.shots.append({"x": e.x + 4, "y": e.y + 4, "dx": dx * 2.0, "dy": dy * 2.0,
                                       "kind": "rock" if "octorok" in e.kind else "arrow", "dir": e.dir})
            if self.link.state not in ("hurt", "hold") and e.rect(3).intersects(self.link.rect(3)):
                self.hurt(e.x, e.y)

    def _wander(self, e):
        cx, cy = e.cell()
        name = random.choice(list(DIRS))
        dx, dy = DIRS[name]
        out = []
        for _ in range(random.randint(2, 8)):
            n = (cx + dx * 2, cy + dy * 2)
            if not self.free(*n) or not self.free(cx + dx, cy + dy):
                break
            out += [(cx + dx, cy + dy), n]
            cx, cy = n
        return out

    def _hop(self, e):
        if e.state == "walk":
            e.state, e.t = "rest", 0
        if e.state == "rest":
            if e.t > random.randint(20, 60):
                cx, cy = e.cell()
                options = [(cx + dx, cy + dy) for dx in range(-5, 6) for dy in range(-4, 5)
                           if self.free(cx + dx, cy + dy) and abs(dx) + abs(dy) >= 3]
                if options:
                    e.goal = random.choice(options)
                    e.start = (e.x, e.y)
                    e.state, e.t = "jump", 0
            return
        if e.state == "jump":
            f = min(1.0, e.t / 32)
            gx, gy = e.goal[0] * CELL, e.goal[1] * CELL
            e.x = e.start[0] + (gx - e.start[0]) * f
            e.y = e.start[1] + (gy - e.start[1]) * f - 24 * (1 - (2 * f - 1) ** 2)
            if f >= 1:
                e.x, e.y = gx, gy
                e.state, e.t = "rest", 0

    def _hit(self, e):
        e.hp -= 1
        if e.hp <= 0:
            e.state, e.t = "dying", 0
            self.sounds.append("kill")
        else:
            e.state, e.t = "flash", 0
            self.sounds.append("hit")

    def _shots(self):
        for s in list(self.shots):
            s["x"] += s["dx"]
            s["y"] += s["dy"]
            if not (-8 < s["x"] < SW and -8 < s["y"] < SH):
                self.shots.remove(s)
                continue
            if QRect(int(s["x"]), int(s["y"]), 8, 8).intersects(self.link.rect(2)):
                self.shots.remove(s)
                if self.link.state == "attack" or self.link.state == "walk" and random.random() < 0.5:
                    self.sounds.append("shield")                     # (his shield takes it)
                else:
                    self.hurt(s["x"], s["y"])

    def _bits(self):
        for b in list(self.bits):
            b["t"] += 1
            if b["t"] > 60 * 12:
                self.bits.remove(b)

    # ---- between screens ----
    def _start_scroll(self, name):
        dx, dy = DIRS[name]
        nc, nr = self.col + dx, self.row + dy
        self.scroll = [self.col, self.row, nc, nr, 0, 64 if dx else 44, name]
        self.enemies, self.shots, self.bits = [], [], []
        L = self.link
        nx = {"left": SW - 16, "right": 0}.get(name, L.x)
        ny = {"up": SH - 16, "down": 0}.get(name, L.y)
        self.walk_across = ((self.col * SW + L.x, self.row * SH + L.y), (nc * SW + nx, nr * SH + ny))

    def _scroll_step(self):
        s = self.scroll
        s[4] += 1
        L = self.link
        dx, dy = DIRS[s[6]]
        L.dir = s[6]
        L.t += 1
        if s[4] >= s[5]:
            self.col, self.row = s[2], s[3]
            self.scr = self.screen(self.col, self.row)
            L.x = {"left": SW - 16, "right": 0}.get(s[6], L.x)
            L.y = {"up": SH - 16, "down": 0}.get(s[6], L.y)
            self.came_from = {"left": "right", "right": "left", "up": "down", "down": "up"}[s[6]]
            self.scroll = None
            L.path, L.exit = [], None
            self.blocks = self._blocks(self.text)
            self._snap(L)
            self._spawn_enemies()

    def _warp(self):
        """The whirlwind: off to another screen with room to walk."""
        good = [(c, r) for c in range(COLS) for r in range(ROWS) if self.screen(c, r).open > 0.4]
        self.col, self.row = random.choice(good)
        self.scr = self.screen(self.col, self.row)
        self.blocks = self._blocks(self.text)
        L = self.link
        L.x, L.y, L.path, L.exit = 120, 128, [], None
        self._snap(L)
        self.came_from = None
        self._spawn_enemies()

    # ---- drawing ----
    def camera(self):
        """The playfield's left edge and top in world pixels."""
        side = (self.W - SW) // 2
        if self.scroll is None:
            return self.col * SW - side, self.row * SH
        c0, r0, c1, r1, done, total, _n = self.scroll
        f = done / total
        x = (c0 + (c1 - c0) * f) * SW - side
        y = (r0 + (r1 - r0) * f) * SH
        return int(x), int(y)

    def draw(self, p):
        p.fillRect(QRect(0, 0, self.W, H), QColor("black"))
        cx, cy = self.camera()
        p.drawImage(QRect(0, HUD, self.W, FIELD), world(), QRect(cx, cy, self.W, FIELD))
        if cx < 0:
            p.fillRect(QRect(0, HUD, -cx, FIELD), QColor("black"))
        if cx + self.W > COLS * SW:
            p.fillRect(QRect(COLS * SW - cx, HUD, cx + self.W - COLS * SW, FIELD), QColor("black"))
        screens = [(self.col, self.row)]
        if self.scroll is not None:
            screens = [(self.scroll[0], self.scroll[1]), (self.scroll[2], self.scroll[3])]
        for sc, sr in screens:                        # each screen's clock, of its own blocks, on cleared ground
            ox, oy = sc * SW - cx, sr * SH - cy + HUD
            scr = self.screen(sc, sr)
            block = scr.block
            cells = self.clock_cells(self.text, self.clock_y(scr, self.text))
            p.fillRect(self.plaza_of(cells).translated(ox, oy), scr.ground)
            for bx, by, _i in cells:
                p.drawImage(ox + bx, oy + by, block)
        ox, oy = self.col * SW - cx, self.row * SH - cy + HUD
        for x, y, t in self.smoke:
            p.drawImage(ox + x, oy + y, cut("link", *CLOUD[min(2, t // 8)]))
        if self.scroll is None:
            for b in self.bits:
                if b["t"] > 60 * 10 and (b["t"] // 4) % 2:
                    continue
                img = {"orange": cut("items", 72, 0, 8, 16), "blue": cut("items", 72, 16, 8, 16),
                       "heart": cut("items", 0, 0, 8, 8)}[b["kind"]]
                p.drawImage(ox + int(b["x"]), oy + int(b["y"]), img)
            for e in self.enemies:
                self._draw_enemy(p, e, ox, oy)
            for s in self.shots:
                if s["kind"] == "rock":
                    img = cut("enemies", 69, 11, 8, 16)
                else:
                    img = cut("enemies", 159, 11, 16, 16, flip=s["dir"] == "left") if s["dir"] in ("left", "right") \
                        else cut("enemies", 150, 11, 8, 16, upside=s["dir"] == "down")
                p.drawImage(ox + int(s["x"]), oy + int(s["y"]), img)
        self._draw_link(p, cx, cy)
        self._draw_hud(p)
        if self.fade:
            a = int(255 * (1 - abs(self.fade - 30) / 30))
            p.fillRect(QRect(0, HUD, self.W, FIELD), QColor(0, 0, 0, a))

    def _draw_link(self, p, cx, cy):
        L = self.link
        if L.state == "hurt" and (L.t // 2) % 2:
            return
        if self.scroll is not None:
            # he walks with the screen: from the edge he leaves by to the edge he comes in by
            f = self.scroll[4] / self.scroll[5]
            (x0, y0), (x1, y1) = self.walk_across
            x, y = int(x0 + (x1 - x0) * f - cx), int(y0 + (y1 - y0) * f - cy) + HUD
        else:
            x, y = self.col * SW + int(L.x) - cx, self.row * SH + int(L.y) - cy + HUD
        if L.state == "hold":
            p.drawImage(x, y, cut("link", *LINK_HOLD))
            p.drawImage(x + 3, y - 12, cut("items", 275, 3, 10, 10))
            return
        if L.state == "attack":
            way = "right" if L.dir == "left" else L.dir
            i = 0 if L.t < 3 else 1 if L.t < 10 else 2 if L.t < 12 else 3
            bx, by, w, h = LINK_SWORD[way][i]
            img = cut("link", bx, by, w, h, flip=L.dir == "left")
            dx = -(w - 16) if L.dir == "left" else 0
            dy = -(h - 16) if L.dir == "up" else 0
            p.drawImage(x + dx, y + dy, img)
            return
        way = "right" if L.dir == "left" else L.dir
        frames = LINK_WALK[way]
        moving = bool(L.path) or self.scroll is not None or L.state == "hurt"
        f = frames[(L.t // 8) % 2] if moving else frames[0]
        p.drawImage(x, y, cut("link", *f, flip=L.dir == "left"))

    def _draw_enemy(self, p, e, ox, oy):
        x, y = ox + int(e.x), oy + int(e.y)
        if e.state == "appear":
            if e.t >= 0:
                p.drawImage(x, y, cut("link", *CLOUD[min(2, e.t // 8)]))
            return
        if e.state == "dying":
            i = min(3, e.t // 4)
            p.drawImage(x, y, cut("death", i * 16, 0, 15, 16))
            return
        if e.state == "flash" and (e.t // 2) % 2:
            return
        spec = ENEMIES[e.kind]
        if e.kind == "tektite":
            f = spec["hop"][1 if e.state == "jump" else (e.t // 16) % 2]
            p.drawImage(x, y, cut("enemies", *f))
            return
        step = (e.t // 10) % 2
        if e.dir in ("left", "right"):
            frames = spec["side"]
            img = cut("enemies", *frames[step % len(frames)], flip=e.dir == "right")
        elif e.dir == "up" and "up" in spec:
            img = cut("enemies", *spec["up"][0], flip=bool(step))
        else:
            frames = spec["down"]
            img = cut("enemies", *frames[step % len(frames)], upside=e.dir == "up",
                      flip=len(frames) == 1 and bool(step))
        p.drawImage(x, y, img)

    def _glyph(self, ch):
        """The HUD's own digits: 'X', then 0-9 (8 x 8, from the HUD sheet)."""
        i = "X0123456789".index(ch) if ch in "X0123456789" else 0
        return cut("hud", 519 + 9 * i, 117, 8, 8)

    def _draw_hud(self, p):
        left = (self.W - SW) // 2
        # the mini-map: the overworld in grey, where he is in green
        p.fillRect(QRect(left + 16, 16, 64, 32), QColor(116, 116, 116))
        p.fillRect(QRect(left + 16 + self.col * 4 + 1, 16 + self.row * 4 + 1, 3, 3), QColor(128, 208, 16))
        # rupees
        p.drawImage(left + 88, 16, cut("items", 72, 0, 8, 16))
        for i, ch in enumerate(f"X{self.rupees}"):
            p.drawImage(left + 96 + i * 8, 20, self._glyph(ch))
        # the B and A boxes, the sword in A
        for bx, label in ((left + 120, "B"), (left + 144, "A")):
            p.setPen(QColor(32, 56, 236))
            p.drawRect(QRect(bx, 24, 15, 23))
            p.setPen(QColor("white"))
            f = QFont("Courier New")
            f.setPixelSize(8)
            f.setBold(True)
            p.setFont(f)
            p.drawText(QRect(bx, 15, 16, 9), Qt.AlignCenter, label)
        p.drawImage(left + 148, 28, cut("link", 1, 154, 8, 16))
        # -LIFE- and the hearts
        f = QFont("Courier New")
        f.setPixelSize(9)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(216, 40, 0))
        p.drawText(QRect(left + 176, 14, 64, 10), Qt.AlignCenter, "-LIFE-")
        for i in range(self.max_hearts // 2):
            full = self.hearts - i * 2
            img = cut("items", 0, 0, 8, 8) if full >= 2 else cut("items", 8, 0, 8, 8) if full == 1 \
                else cut("items", 16, 0, 8, 8)
            p.drawImage(left + 176 + i * 8, 32, img)


# ---- the screen saver -----------------------------------------------------------------------------------------------
def make_saver_class(Saver):
    class LegendOfClaudeSaver(Saver):
        """The game, scaled up to the screen without smoothing."""
        FPS = 60

        def __init__(self, parent=None):
            super().__init__(parent)
            self.game = None
            self.missing = not available()

        def _ensure(self):
            if self.missing or self.width() < 4:
                return None
            w = max(SW + 32, int(round(H * self.width() / max(1, self.height()))))
            if self.game is None or self.game.W != w:
                self.game = LegendOfClaude(w)
            return self.game

        def step(self):
            g = self._ensure()
            if g is not None:
                g.step()
                g.sounds.clear()

        def paintEvent(self, event):
            p = QPainter(self)
            p.fillRect(self.rect(), QColor("black"))
            g = self._ensure()
            if g is None:
                p.setPen(QColor("white"))
                f = QFont("Tahoma")
                f.setPixelSize(max(9, self.height() // 30))
                p.setFont(f)
                p.drawText(self.rect(), Qt.AlignCenter, "The Legend of Claude needs its sprite sheets in\n"
                           f"E:\\{FOLDER}")
                return
            frame = QImage(g.W, H, QImage.Format_ARGB32)
            q = QPainter(frame)
            g.draw(q)
            q.end()
            scale = min(self.width() / g.W, self.height() / H)
            w, h = g.W * scale, H * scale
            p.drawImage(QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h), frame)

    return LegendOfClaudeSaver
