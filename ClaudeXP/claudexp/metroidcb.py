"""Metroid: Claude's Mission - a side-scrolling Metroid clock screen saver, after Zelda II: The Adventure of Claude.

Samus runs through the real corridors of planet Zebes - Brinstar, Norfair, Kraid's Lair, Ridley's Lair and Tourian,
cut from the area maps a screen-high strip at a time - finding her own way over the platforms, up the ledges and
through the bubble doors, which she shoots open. Each area has its own crawlers and fliers: she shoots what gets in
front of her (up, when it's above), they burst, and now and then they leave an energy ball or a missile behind. The
time is built out of the area's own breakable blocks; when the minute changes the changed blocks crumble the way
they do when she shoots them, and the new ones grow back. On the hour she does a spinning jump. The HUD is the
game's: energy, tanks and missiles.

The pictures come from the sprite sheets in Local Storage/Metroid - Sprites (the Spriters Resource's NES sheets,
ripped by Mister Mike, the maps and tileset by Mica). Drawn at the NES's own size (240 lines, as wide as the
screen's shape needs) and scaled up without smoothing."""
import heapq
import math
import random
from array import array
from datetime import datetime

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter

FOLDERS = ("Metroid - Sprites", "Mertoid - Sprites")
_P = "NES - Metroid - "
SHEETS = {"samus": _P + "Playable Characters - Samus Aran (Power Suit).png",
          "enemies": _P + "Enemies & Bosses - Enemies & Bosses.png",
          "items": _P + "Miscellaneous - Items & Objects.png",
          "tiles": _P + "Miscellaneous - Tileset.png"}
AREAS = {"brinstar": "Brinstar", "norfair": "Norfair", "kraid": "Kraid's Lair", "ridley": "Ridley's Lair",
         "tourian": "Tourian"}
MAP = _P + "Maps - {}.png"
CLEAR = {0xFF008000, 0xFF747474}                   # the sheets' green backdrop and grey frame boxes: clear
MARGIN = 0xFF0B0E1C                                # the maps' backdrop between the rooms
BLACK = 0xFF000000
H, TILE, ROWS = 240, 16, 15
ROOM_W, MAP_X, MAP_Y = 256, 64, 64                 # the maps are a grid of 256 x 240 screens, 64 pixels in

# physics, in pixels and frames
GRAVITY, FALL, RUN = 0.2, 5.0, 1.5
JUMPS = (-3.6, -4.8, -5.8)                         # a hop, a jump and a full jump (2, 3½ and 5 tiles up)
DRIFTS = (1.5, 0.75, -0.75, -1.5)
JUMP_COST = 30                                     # frames: what a jump 'costs' over running
TURN_COST = 40                                     # and turning back: only when there's no way on without it
BODY_W, BODY_H = 12, 30                            # her box: 6 either side of x, 30 up from her feet

# Samus (faces right on the sheet)
SAMUS = {"stand": (1, 11, 20, 32), "run": [(29, 11, 16, 32), (46, 11, 24, 32), (71, 11, 24, 32)],
         "jump": (100, 11, 24, 32), "spin": [(255, 11, 16, 24), (272, 15, 24, 16), (297, 11, 16, 24), (314, 15, 24, 16)],
         "up": (142, 11, 16, 40), "uprun": [(176, 11, 24, 40), (201, 11, 24, 40), (226, 11, 24, 40)],
         "shoot": (1, 68, 18, 32), "shootrun": [(29, 68, 24, 32), (54, 68, 32, 32), (87, 68, 32, 32)],
         "shootjump": (124, 68, 32, 32), "front": (128, 121, 16, 32)}
BEAM, MISSILE = [(1, 168, 8, 8), (10, 168, 8, 8)], (277, 172, 16, 8)
MISSILE_UP = (294, 168, 8, 16)
BURST = [(19, 199, 16, 16), (36, 199, 16, 16)]
# enemies: frames on the enemy sheet, how they move, health
FOE = {"zoomer": ([(1, 21, 16, 16), (18, 21, 16, 16)], "crawl", 2),
       "skree": ([(73, 21, 16, 24), (90, 21, 8, 24), (99, 21, 8, 24)], "dive", 2),
       "reo": ([(121, 21, 24, 20), (146, 25, 24, 16)], "swoop", 2),
       "ripper": ([(175, 21, 16, 8)], "fly", 1),
       "waver": ([(235, 21, 16, 16), (252, 21, 16, 16)], "wave", 1),
       "zeb": ([(273, 21, 16, 16), (290, 21, 16, 16)], "pipe", 1),
       "mellow": ([(311, 21, 16, 8), (328, 21, 16, 8)], "swarm", 1),
       "mella": ([(1, 98, 16, 8), (18, 98, 16, 8)], "swarm", 1),
       "sova": ([(140, 98, 16, 16), (157, 98, 16, 16)], "crawl", 2),
       "gamet": ([(212, 98, 16, 16), (229, 98, 16, 16)], "pipe", 1),
       "ripper2": ([(253, 98, 16, 8), (270, 98, 16, 8)], "fly", 2),
       "multiviola": ([(387, 98, 16, 16), (404, 98, 16, 16), (421, 98, 16, 16), (438, 98, 16, 16)], "bounce", 2),
       "zebbo": ([(1, 178, 16, 16), (18, 178, 16, 16)], "pipe", 1),
       "holtz": ([(41, 178, 24, 16), (66, 178, 24, 16)], "swoop", 3),
       "viola": ([(145, 178, 16, 16), (162, 178, 16, 16)], "crawl", 2),
       "multiviola2": ([(183, 178, 16, 16), (200, 178, 16, 16), (217, 178, 16, 16), (234, 178, 16, 16)], "bounce", 2),
       "memu": ([(1, 246, 16, 8), (18, 246, 16, 8)], "swarm", 1),
       "geega": ([(72, 246, 16, 16), (89, 246, 16, 16)], "pipe", 1),
       "skree2": ([(113, 246, 16, 24), (130, 246, 8, 24), (139, 246, 8, 24)], "dive", 2),
       "zeela": ([(161, 246, 16, 16), (178, 246, 16, 16)], "crawl", 2),
       "ripper3": ([(233, 246, 16, 8)], "fly", 1),
       "rinka": ([(85, 314, 16, 16), (102, 314, 16, 16), (119, 314, 16, 16)], "ring", 1),
       "metroid": ([(140, 314, 24, 24), (165, 314, 24, 24), (190, 314, 24, 24), (215, 314, 24, 24)], "latch", 4)}
FOES = {"brinstar": ["zoomer", "zoomer", "skree", "reo", "ripper", "waver", "zeb", "mellow"],
        "norfair": ["sova", "sova", "gamet", "ripper2", "multiviola", "mella"],
        "kraid": ["zeela", "zeela", "skree2", "geega", "memu", "ripper3"],
        "ridley": ["viola", "viola", "zebbo", "holtz", "multiviola2"],
        "tourian": ["metroid", "rinka", "rinka", "metroid"]}
# the items sheet: pickups and the HUD
ENERGY_BALL, MISSILE_DROP = [(1, 15, 8, 8), (10, 15, 8, 8)], (19, 11, 8, 16)
EN, TANK_EMPTY, TANK_FULL, MISSILE_ICON = (1, 100, 16, 8), (1, 109, 8, 8), (10, 109, 8, 8), (1, 118, 16, 8)
DOTS = (18, 100, 8, 8)
DIGIT_X, DIGIT_Y = 31, 110                          # 0-9 across, 9 apart
# each area's breakable block on the tileset sheet, with its two crumbling frames 18 and 36 pixels on (one that
# stands out from the area's walls; Tourian has none of its own, so it borrows Ridley's red one)
BLOCKS = {"brinstar": (12, 247), "norfair": (294, 231), "kraid": (726, 229), "ridley": (618, 195),
          "tourian": (558, 195)}
DIGITS = {"0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111",
          "4": "101101111001001", "5": "111100111001111", "6": "111100111101111", "7": "111001001001001",
          "8": "111101111101111", "9": "111101111001111"}


# ---- pictures ------------------------------------------------------------------------------------------------------
_sheets, _cache = {}, {}


def _folder():
    from .explorer.vfs import local_storage
    base = local_storage()
    for name in FOLDERS:
        if (base / name).is_dir():
            return base / name
    return base / FOLDERS[0]


def available():
    f = _folder()
    return all((f / s).exists() for s in SHEETS.values()) and all((f / MAP.format(a)).exists() for a in AREAS.values())


def _sheet(key):
    if key not in _sheets:
        img = QImage(str(_folder() / SHEETS[key]))
        _sheets[key] = img.convertToFormat(QImage.Format_ARGB32) if not img.isNull() else QImage()
    return _sheets[key]


def _pixels(img):
    img = img.convertToFormat(QImage.Format_ARGB32)
    px = array("I")
    px.frombytes(bytes(img.constBits())[:img.width() * img.height() * 4])
    return px


def _clear(img):
    w, h = img.width(), img.height()
    out = array("I", [0 if v in CLEAR else v for v in _pixels(img)])
    return QImage(out.tobytes(), w, h, w * 4, QImage.Format_ARGB32).copy()


def cut(key, x, y, w=16, h=16, flip=False, clear=True):
    k = (key, x, y, w, h, flip)
    if k not in _cache:
        img = _sheet(key).copy(x, y, w, h)
        img = _clear(img) if clear else img.convertToFormat(QImage.Format_ARGB32)
        if flip:
            img = img.mirrored(True, False)
        _cache[k] = img
    return _cache[k]


_anchors = {}


def anchor(frame, flip=False):
    """Where her helmet's middle is across a frame of Samus: the frames are cut to different widths (a leg out
    behind, the cannon out in front), so they're lined up on the helmet or she'd judder as she runs."""
    k = (frame, flip)
    if k not in _anchors:
        img = cut("samus", *frame, flip=flip)
        h = img.height()
        cols = [x for x in range(img.width()) for y in range(max(0, h - 32), h - 25) if img.pixel(x, y) >> 24]
        _anchors[k] = (min(cols) + max(cols)) / 2 if cols else img.width() / 2
    return _anchors[k]


# ---- a corridor -----------------------------------------------------------------------------------------------------
class Strip:
    """A row of screens from an area map: its picture, which 16-pixel tiles are solid (anything drawn on the black)
    and which are lava or acid, its bubble doors, and the way through it."""

    def __init__(self, img, area="brinstar"):
        self.area = area
        self.img = img.convertToFormat(QImage.Format_ARGB32)
        self.w = self.img.width()
        self.cols = self.w // TILE
        px = _pixels(self.img)
        w = self.w
        self.solid = bytearray(self.cols * ROWS)
        self.liquid = bytearray(self.cols * ROWS)
        for ty in range(ROWS):
            for tx in range(self.cols):
                counts = {}
                for yy in range(ty * TILE, ty * TILE + TILE, 2):
                    row = yy * w + tx * TILE
                    for xx in range(0, TILE, 2):
                        v = px[row + xx]
                        counts[v] = counts.get(v, 0) + 1
                lit = 64 - counts.get(BLACK, 0)
                top = max(counts, key=counts.get)
                i = ty * self.cols + tx
                if counts.get(MARGIN, 0) > 16:
                    self.solid[i] = 1
                elif top != BLACK and counts[top] >= 54 and ty >= 10:   # one flat colour, low down: lava or acid
                    self.liquid[i] = 1
                elif lit >= 6:
                    self.solid[i] = 1
        # bubble doors on the screen edges: a tube three tiles high between solid frame tiles
        self.doors = []
        for b in range(0, self.w + 1, ROOM_W):
            tube = [c for c in (b // TILE - 1, b // TILE) if 0 <= c < self.cols]
            if tube and all(self.solid[r * self.cols + c] for c in tube for r in (5, 6, 7)) \
                    and all(self.solid[r * self.cols + c] for c in tube for r in (4, 8)):
                self.doors.append({"x": b, "open": False})
                for c in range(b // TILE - 2, b // TILE + 2):
                    if 0 <= c < self.cols:
                        for r in (5, 6, 7):
                            self.solid[r * self.cols + c] = 0
                            self.liquid[r * self.cols + c] = 0

    # ---- the tiles ----
    def hard(self, tx, ty):
        if tx < 0 or tx >= self.cols or ty < 0:
            return True
        if ty >= ROWS:
            return False
        return self.solid[ty * self.cols + tx] == 1

    def blocked(self, x, y, h=BODY_H):
        x0, x1 = int(x - BODY_W // 2) // TILE, int(x + BODY_W // 2 - 1) // TILE
        for ty in range(int(y - h) // TILE, int(y - 1) // TILE + 1):
            if self.hard(x0, ty) or self.hard(x1, ty):
                return True
        return False

    def grounded(self, x, y):
        return y % TILE == 0 and self.blocked(x, y + 1, 1)

    def wet(self, x, y):
        tx, ty = int(x) // TILE, int(y - 4) // TILE
        return 0 <= tx < self.cols and 0 <= ty < ROWS and self.liquid[ty * self.cols + tx] == 1

    # ---- moving: the same physics the game runs, so a route found here is a route she can run ----
    def sim(self, x, y, vx, vy, target=None, limit=240):
        """Run (or jump, or fall) from (x, y): to the tile centre `target` along the ground, or until she lands.
        The positions she passes through, or None if she drops out of the strip, into lava or into a wall."""
        pts, air = [], vy != 0 or not self.grounded(x, y)
        for _ in range(limit):
            if vx:
                if self.blocked(x + vx, y):
                    if not air:
                        return None
                    vx = 0.0
                else:
                    x += vx
            if not air and not self.grounded(x, y):
                air, vy = True, 0.0
            if air:
                vy = min(vy + GRAVITY, FALL)
                ny = y + vy
                if self.blocked(x, ny):
                    if vy > 0:
                        ny = (int(ny) // TILE) * TILE
                        while ny > y and self.blocked(x, ny):
                            ny -= TILE
                        if self.blocked(x, ny):
                            return None
                        y, vy, air = float(ny), 0.0, False
                        pts.append((x, y, False))
                        if target is None:
                            return pts
                        continue
                    vy = 0.0
                else:
                    y = ny
                if y > H + BODY_H or self.wet(x, y):
                    return None
                pts.append((x, y, True))
                continue
            if target is not None and (x - target) * (vx or 1) >= 0:
                if (x - vx - target) * (vx or 1) < 0:     # (reached it this frame: to the middle of the tile
                    x = float(target)                   # exactly, so the next step doesn't start behind her)
                pts.append((x, y, False))
                return pts
            pts.append((x, y, False))
        return None

    def standing(self, tx, y):
        x = tx * TILE + TILE // 2
        return 0 <= tx < self.cols and self.grounded(x, y) and not self.blocked(x, y) and not self.wet(x, y + 1)

    def moves(self, node):
        """Each move from a standing place, with its code: r or l a step along (or off the edge, falling), a-l the
        jumps (three heights by four drifts)."""
        tx, y = node
        x = tx * TILE + TILE // 2
        for code, d in (("r", 1), ("l", -1)):
            pts = self.sim(float(x), float(y), RUN * d, 0.0, target=x + TILE * d)
            if pts:
                yield code, pts
        for i, vy in enumerate(JUMPS):
            for j, vx in enumerate(DRIFTS):
                pts = self.sim(float(x), float(y), vx, vy)
                if pts:
                    yield chr(97 + i * 4 + j), pts

    def move(self, node, code):
        tx, y = node
        x = tx * TILE + TILE // 2
        if code in "rl":
            d = 1 if code == "r" else -1
            pts = self.sim(float(x), float(y), RUN * d, 0.0, target=x + TILE * d)
        else:
            i = ord(code) - 97
            pts = self.sim(float(x), float(y), DRIFTS[i % 4], JUMPS[i // 4])
        return self.settle(pts) if pts else (None, None)

    def settle(self, pts):
        """Where a move ends up as a standing node: the middle of a tile she landed on - the one ahead of her if
        there's floor there, so she runs on into it rather than stepping back."""
        x, y, _air = pts[-1]
        tx = int(x) // TILE
        d = 1 if x >= pts[0][0] else -1
        here = tx * TILE + TILE // 2
        ahead = tx if (here - x) * d >= 0 else tx + d
        for c in dict.fromkeys((ahead, ahead - d, ahead + d)):
            if self.standing(c, y):
                cx = c * TILE + TILE // 2
                if abs(cx - x) < 0.5:
                    return (c, int(y)), pts
                walk = self.sim(x, y, RUN if cx > x else -RUN, 0.0, target=cx)
                if walk and walk[-1][1] == y and not walk[-1][2]:
                    return (c, int(y)), pts + walk
        return None, None

    def route(self, start):
        """The quickest way to the furthest place right she can reach, counting each jump as half a second more than
        it takes, so she runs where she can and jumps where she has to. (start, end, moves)"""
        best = {start: 0}
        prev = {start: None}
        todo = [(0, 0, start)]
        n = 0
        while todo:
            cost, _n, node = heapq.heappop(todo)
            if cost > best[node]:
                continue
            for code, pts in self.moves(node):
                to, path = self.settle(pts)
                if to is None:
                    continue
                c = cost + len(path) + (0 if code in "rl" else JUMP_COST) + (TURN_COST if self._back(code) else 0)
                if c < best.get(to, 1 << 30):
                    best[to], prev[to] = c, (node, code)
                    n += 1
                    heapq.heappush(todo, (c, n, to))
        end = max(prev, key=lambda nd: (nd[0], -best[nd]))
        codes, nd = "", end
        while prev[nd] is not None:
            nd, code = prev[nd]
            codes = code + codes
        return start, end, codes

    @staticmethod
    def _back(code):
        """Whether a move heads left (back the way she came)."""
        return code == "l" or (code not in "r" and DRIFTS[(ord(code) - 97) % 4] < 0)

    def replay(self, start, codes):
        """The positions along a route, frame by frame, as (x, y, how): 0 on the ground, 1 in the air, 2 in a
        spinning jump (a running jump high enough) - or None if the route no longer fits the picture."""
        path, node = [], start
        for code in codes:
            node, pts = self.move(node, code)
            if node is None:
                return None
            i = ord(code) - 97
            spin = code not in "rl" and i // 4 >= 1 and i % 4 in (0, 3)
            path += [(x, y, (2 if spin else 1) if air else 0) for x, y, air in pts]
        return path

    def starts(self, screen=0):
        """Where she can come in on the left of a screen: the door's sill if there is one, else the floor there."""
        out = []
        for tx in range(screen * ROOM_W // TILE, screen * ROOM_W // TILE + 4):
            for ty in range(1, ROWS + 1):
                if self.standing(tx, ty * TILE):
                    out.append((tx, ty * TILE))
        return out


# the corridors, solved: (area, map row, first screen, last screen, where she starts, her moves)
CORRIDORS = [
    ('brinstar', 1, 4, 10, (0, 128), 'rrrrrrrrrirrirriirrrrrriirrrrrrrrrrrrrrrrrrrrrirrrrrrrrrrirrrr'),
    ('brinstar', 1, 15, 19, (0, 128), 'rrrrrrrrrriirriirrriirrrrrrrrr'),
    ('brinstar', 2, 17, 24, (0, 208), 'rrrrrrrrrjrrrrbairrrrrrrjrrjrrrrrrrrrrrrrreajaarrrrrajaaairirrrjrr'),
    ('brinstar', 2, 26, 29, (0, 160), 'aierajaarrrbairrrrrrrrirrrr'),
    ('brinstar', 4, 7, 10, (0, 128), 'rrrrrrrrrriirrriirrrrrrrrrrrrirrrr'),
    ('brinstar', 4, 25, 29, (0, 128), 'rrrrrrrrrriirriirrriirrrrrrrrrrrrirrrr'),
    ('brinstar', 6, 10, 29, (0, 128), (
        'rrrrirrrrrrrrrrrrrrrrrrrrrrrrerrrrrrrrrrrririrrrrrrrrrirririirrrrrrrrrrrrrrrrrrrrrrrrriirirrrriirrrr'
        'rrrrrrrrrrrrrrrrrrrrriririiieiirrrrirriiirrrriirrrrrrrirrrr'
    )),
    ('brinstar', 8, 19, 21, (0, 128), 'rrrrrrrrrrriirrrrrrrrrrrrirrrr'),
    ('brinstar', 10, 12, 21, (0, 128), (
        'rrrrirrrrrrrrrrrrrrrrrrrrrrrrrrrrrrirrirrrrrrrrrrrrrriirirrriiiirrrrrrrrrirrrrrrrrrrrrrrrrrrrrr'
    )),
    ('brinstar', 13, 2, 8, (0, 208), (
        'rrrrjrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrirrrrrrrrerrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr'
    )),
    ('norfair', 1, 14, 17, (0, 128), 'rirriririrrriirrrrrrrrrrrrrrrrr'),
    ('norfair', 2, 13, 17, (0, 128), 'rirririrriririrrriirrrrrrrr'),
    ('norfair', 5, 4, 17, (0, 144), (
        'rrreerairirrrirriirrriierrrrrrrrrrrrrrrrrrrrrrerrrrrerrarrrrrerrrerrerrrerreirrrfrarrrerrieirrrrrrrr'
    )),
    ('norfair', 6, 11, 17, (0, 160), 'rirrriirrrirrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrriirrrrrrrrrrrrrrrrr'),
    ('norfair', 7, 3, 5, (0, 128), 'rrrirrrrrrrrrrrrirrrrrrrrrrrrrrrrrrr'),
    ('norfair', 8, 0, 12, (2, 48), (
        'rrrrerrrrrrriirrrrirrrrrrrrrrirrrrrrrriirrrrrrrrrrrrrrrrrrrrrriirrrrirrrrrrjiirrrrrrrrrrrrrrrrrrrrrr'
        'rrrrrrrrrarfjrrifjrre'
    )),
    ('norfair', 8, 15, 17, (0, 128), 'rrrirrrrrrrrrrrrirrrrrrrrrr'),
    ('norfair', 9, 0, 11, (0, 128), (
        'rrrrrrrrrrrrrrrrrrrriirrrrrrrrrrrrrrrrrrrrrrrrrrrrrariirrrrrrrrrrrrrrrrrrrrrrierirarrrrrrirarrrrrrir'
        'airrrrrrrrjrrrrrrrrrrrrrr'
    )),
    ('norfair', 9, 13, 16, (0, 80), 'aarrrrrrrrrrrrrrrrrrrrrrariirrrrrrrrrrrrr'),
    ('norfair', 10, 14, 17, (0, 144), 'rrrrirrrrrrrriirrrrrrrrrrrrrrrrrrrrrrrrir'),
    ('norfair', 11, 3, 10, (0, 176), 'eiarrrrrrrrrrrrrrrrrrrrrreijrrijaeiarrrrrrrrrrrrrrrrrrrrrreerrrrrr'),
    ('norfair', 12, 6, 8, (0, 128), 'rrrirrrrrrrrrrrrirrrrrrrrrrrrrrrrrrr'),
    ('norfair', 12, 11, 17, (2, 48), 'rrrrerrrrrrreirrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrriiriarrrrrrrr'),
    ('norfair', 13, 4, 7, (2, 48), 'rrrrerrrrrrreaiirririrrrr'),
    ('kraid', 1, 7, 10, (2, 96), 'rrrrirrrrrrrrrrrrirrrrrrirrrrrajir'),
    ('kraid', 5, 5, 10, (0, 208), 'rrrrrrrrirrrrrrrjrrrrrrrrrrrrrrrreieerrrrrrrirrrrrajir'),
    ('kraid', 6, 0, 7, (0, 128), (
        'rjjiirrrrrrrrrrrrirrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrirrrrrrrjrrrrrrrrrrrrrrrre'
    )),
    ('kraid', 8, 7, 11, (0, 128), 'rrrrrrrrirrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrirrrrrajir'),
    ('kraid', 9, 9, 11, (1, 176), 'ieerrrrrrrirrrrae'),
    ('kraid', 10, 4, 6, (0, 128), 'rrrrrrrrrrirrrrrrirrrrrrrrrr'),
    ('kraid', 11, 1, 8, (0, 128), (
        'rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrreieerrrrrrrrrrrrirrrrrrrrrrrrrrrrrrrrirrrrrrrrrr'
    )),
    ('kraid', 12, 2, 11, (0, 128), (
        'rrjrjrrrrrrrrrrrrrrrrrrrrirrrrrrrrrirrrrrrrrrirrrrrrrrrairrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr'
        'rrrrrrrra'
    )),
    ('kraid', 13, 7, 11, (0, 128), 'rrrrrrrirrrrrrrrrrrrrrrrrrrrrrrrrrrirrrrrrirrrrrajir'),
    ('ridley', 1, 4, 9, (0, 176), 'rrrrrrrrrirrrrrrrrrrrrrrirrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrijrrrrrrr'),
    ('ridley', 2, 5, 16, (0, 192), (
        'rrrirrrrrrrrrirrrrrrrrrirrrrrrreaerrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrirrrrrrrrriiiirriririererrrr'
        'rrrraer'
    )),
    ('ridley', 4, 1, 8, (0, 128), (
        'rrrrrlirrreaerrrrrrirrrrrrrrrrrrrrrrrirrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrirrrrrrrr'
    )),
    ('ridley', 4, 11, 16, (1, 192), 'riirririirriirrirrrrrrrijrrrrrrrrraer'),
    ('ridley', 6, 10, 16, (0, 160), 'rirrrjrrirrrjrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrreaerrrrrrrraer'),
    ('ridley', 7, 0, 16, (0, 128), (
        'rrrrrrrrrrrrrrrrrrrrirrrrrrrrrrrrrrrrrirrrrrrrrrrrrrrrrrrrrrrrrrrrrirrrrrrrrrrrrrrrrrrrrrrirrrrrrrrr'
        'rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrirrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr'
        'rrrrrrrrrrrrrrrrijrrrrrrrrrrrrrrrrrrr'
    )),
    ('tourian', 4, 2, 9, (0, 128), (
        'rrrrrrirrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrririrrirrirrrrrrrrrrrrrrrrrrrrirrrrrrrrrrr'
    )),
    ('tourian', 8, 4, 9, (0, 128), 'arrrrrrarrrrrrjarrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrierrrrrrrirrrr'),
]


def strip_for(area_img, area, row, s0, s1):
    return Strip(area_img.copy(MAP_X + s0 * ROOM_W, MAP_Y + row * H, (s1 - s0 + 1) * ROOM_W, H), area)


class Thing:
    def __init__(self, kind, x, y):
        self.kind, self.x, self.y = kind, float(x), float(y)       # y: the bottom (feet, for Samus)
        self.vx = self.vy = 0.0
        self.t = 0
        self.state = "go"
        self.hp = 1
        self.flash = 0
        self.base = 0.0


# ---- the game -------------------------------------------------------------------------------------------------------
class ClaudesMission:
    def __init__(self, width=320, now=None):
        self.W = width
        self.now = now or datetime.now
        self.area, self.area_img = None, None
        self.queue = []
        self.strip = None
        self.path, self.i = [], 0
        self.samus = Thing("samus", 0, 0)
        self.facing = 1
        self.energy, self.tanks, self.full_tanks, self.missiles = 30, 3, 3, 15
        self.enemies, self.shots, self.bits = [], [], []
        self.cool = 0
        self.aim, self.aim_t = None, 0                  # "ahead" or "up" while she's shooting
        self.blink = 0
        self.hold = 0                                   # on the hour: she turns to face us
        self.next_foe = 120
        self.fade = 0
        self.sounds = []
        self.text = self._time_text()
        self.blocks = {}                                # (x, y): [t, "out" | "in"] - crumbling, or growing back
        self.coming = None                              # the next time, once the changed blocks have crumbled
        self.crumbled = set()
        self.last_minute = self.now().minute
        self.cam = 0
        self.passed = 0
        self._next_corridor()

    # ---- the corridors ----
    def _load_area(self, area):
        if area != self.area:
            self.area_img = None                          # (the old map goes before the new one comes in)
            self.area = area
            self.area_img = QImage(str(_folder() / MAP.format(AREAS[area])))

    def _next_corridor(self):
        """Two or three corridors of an area, then on to another (a whole map is big: one in memory at a time)."""
        strip = path = start = None
        for _attempt in range(len(CORRIDORS) + 1):
            if not self.queue:
                areas = sorted({c[0] for c in CORRIDORS} - {self.area}) or [CORRIDORS[0][0]]
                mine = [c for c in CORRIDORS if c[0] == random.choice(areas)]
                random.shuffle(mine)
                self.queue = mine[:random.randint(2, 3)]
            area, row, s0, s1, start, codes = self.queue.pop(0)
            self._load_area(area)
            strip = strip_for(self.area_img, area, row, s0, s1)
            path = strip.replay(start, codes)
            if path is None:                              # (not the picture it was solved on: solve it again)
                start, _end, codes = strip.route(start)
                path = strip.replay(start, codes)
            if path and len(path) > 120:
                break
        self.strip, self.path, self.i = strip, path or [], 0
        self.passed += 1
        S = self.samus
        S.x, S.y = float(start[0] * TILE + TILE // 2), float(start[1])
        S.t, S.state = 0, "stand"
        for d in strip.doors:                             # the door she comes in by is open
            if abs(d["x"] - S.x) < 48:
                self._open(d)
        self.enemies, self.shots, self.bits = [], [], []
        self.next_foe = 100
        self.cam = self._cam_for(S.x)
        self.energy = min(99, self.energy + 20)

    def _cam_for(self, x):
        """Whole pixels, from her whole-pixel x: she and the corridor then move together, never a pixel apart."""
        return max(0, min(self.strip.w - self.W, int(x) - int(self.W * 0.4)))

    def _open(self, door):
        """Shoot a bubble door: its caps (the 8-pixel crescents either side of the tube) go."""
        if door["open"]:
            return
        door["open"] = True
        img, b = self.strip.img, door["x"]
        for x0 in (b - 24, b + 16):
            for x in range(max(0, x0), min(img.width(), x0 + 8)):
                for y in range(78, 130):
                    if img.pixel(x, y) != BLACK:
                        img.setPixel(x, y, BLACK)

    # ---- the clock ----
    def _time_text(self):
        t = self.now()
        return f"{(t.hour % 12) or 12}:{t.minute:02d}"

    def clock_cells(self, text=None):
        text = text or self.text
        cells, x = [], 0
        for i, ch in enumerate(text):
            if ch == ":":
                cells += [(x, 1, i), (x, 3, i)]
                x += 2
                continue
            for r in range(5):
                for c in range(3):
                    if DIGITS[ch][r * 3 + c] == "1":
                        cells.append((x + c, r, i))
            x += 4 if i + 1 < len(text) and text[i + 1] != ":" else 3
            if i + 1 < len(text) and text[i + 1] == ":":
                x += 1
        x0 = (self.W - x * 16) // 2
        return [(x0 + cx * 16, 56 + cy * 16, i) for cx, cy, i in cells]

    def _tick_clock(self):
        t = self.now()
        if t.minute != self.last_minute:
            self.last_minute = t.minute
            new = self._time_text()
            keep = {(x, y) for x, y, _ in self.clock_cells(new)}
            for x, y, i in self.clock_cells():           # the changed digits' blocks crumble, as when she shoots them
                if (x, y) not in keep or i >= len(new) or new[i] != self.text[i]:
                    self.blocks[(x, y)] = [0, "out"]
            self.crumbled = {pos for pos, b in self.blocks.items() if b[1] == "out"}
            self.coming = new
            if t.minute == 0:
                self.hold = 150
        for pos, b in list(self.blocks.items()):
            b[0] += 1
            if b[0] > 24:
                del self.blocks[pos]
        if self.coming and not any(b[1] == "out" for b in self.blocks.values()):
            steady = {(x, y) for x, y, _ in self.clock_cells()} - self.crumbled
            self.text, self.coming = self.coming, None    # gone: the new time's blocks grow back in
            for x, y, _i in self.clock_cells():
                if (x, y) not in steady:
                    self.blocks[(x, y)] = [0, "in"]

    # ---- a frame ----
    def step(self):
        self._tick_clock()
        if self.fade:
            self.fade -= 1
            if self.fade == 20:
                self._next_corridor()
            return
        self._samus()
        self._enemies()
        self._shots()
        self._bits()
        d = self._cam_for(self.samus.x) - self.cam        # (catching up, a few pixels a frame, after a door)
        self.cam += max(-4, min(4, d))
        if self.i >= len(self.path) and not self.hold:
            self.fade = 40                                # the end of the corridor: through the door

    # ---- Samus ----
    def _samus(self):
        S = self.samus
        S.t += 1
        self.blink = max(0, self.blink - 1)
        self.cool = max(0, self.cool - 1)
        if self.aim_t:
            self.aim_t -= 1
            if not self.aim_t:
                self.aim = None
        here = self.path[min(self.i, len(self.path) - 1)] if self.path else (S.x, S.y, 0)
        if self.hold and here[2] == 0:                  # the hour: she stops and turns to us
            self.hold -= 1
            S.state = "front"
            return
        if self.i < len(self.path):
            x, y, how = self.path[self.i]
            self.i += 1
            ahead = self.path[min(self.i + 8, len(self.path) - 1)][0] - x
            if x != S.x and ahead and (ahead > 0) == (x > S.x):
                self.facing = 1 if x > S.x else -1      # (she turns only when she's going that way for a while:
            S.vx, S.vy = x - S.x, y - S.y               # a few pixels' settling back after a landing is a skid)
            S.x, S.y = x, y
            back = S.vx and (S.vx > 0) != (self.facing > 0)
            S.state = ("spin" if how == 2 and self.aim is None else "air") if how else \
                ("stand" if back or not S.vx else "run")
        else:
            S.vx = S.vy = 0.0
            S.state = "stand"
        for d in self.strip.doors:                      # a door ahead: a shot opens it
            if not d["open"] and 0 < (d["x"] - S.x) * self.facing < 56 and abs(S.y - 128) < 40:
                self._fire("ahead")
                self._open(d)
        foe = self._target()
        if foe:
            self._fire(*foe)
        for b in list(self.bits):                       # pickups she runs through
            if abs(b["x"] - S.x) < 12 and S.y - 34 < b["y"] < S.y + 4:
                self.bits.remove(b)
                if b["kind"] == "energy":
                    self.energy = min(99, self.energy + 5)
                else:
                    self.missiles = min(255, self.missiles + 2)

    def _target(self):
        """Something to shoot: in front of her at gun height, or right above her."""
        S = self.samus
        gun = S.y - 23
        for e in self.enemies:
            if e.state not in ("go", "fall", "rise", "hang"):
                continue
            r = self._rect(e)
            d = (r.center().x() - S.x) * self.facing
            if 0 < d < 120 and r.top() - 4 < gun < r.bottom() + 4:
                return "ahead", e
        for e in self.enemies:
            if e.state not in ("go", "fall", "rise", "hang"):
                continue
            r = self._rect(e)
            if abs(r.center().x() - S.x) < 20 and r.bottom() < S.y - 30 and S.y - r.bottom() < 110:
                return "up", e
        return None

    def _fire(self, aim, foe=None):
        if self.cool:
            return
        S = self.samus
        missile = foe is not None and foe.kind == "metroid" and self.missiles > 0
        if missile:
            self.missiles -= 1
        if aim == "up":
            shot = {"x": S.x + 2 * self.facing, "y": S.y - 44, "vx": 0.0, "vy": -5.0}
        else:
            shot = {"x": S.x + 12 * self.facing, "y": S.y - 23, "vx": 5.0 * self.facing, "vy": 0.0}
        shot.update(t=0, missile=missile)
        self.shots.append(shot)
        self.cool = 14 if missile else 9
        self.aim, self.aim_t = aim, 14
        self.sounds.append("missile" if missile else "beam")

    def hurt(self, dmg=8):
        if self.blink or self.hold:
            return
        self.blink = 60
        self.energy -= dmg
        if self.energy < 0:                             # a tank empties into her
            if self.full_tanks:
                self.full_tanks -= 1
                self.energy += 100
            else:
                self.energy = 1

    # ---- enemies ----
    def _rect(self, e):
        fw, fh = FOE[e.kind][0][0][2], FOE[e.kind][0][0][3]
        return QRect(int(e.x - fw / 2) + 2, int(e.y - fh) + 2, fw - 4, fh - 4)

    def _floor_near(self, x, y):
        """The top of a floor in the column at x - the one nearest y."""
        tx, s = int(x) // TILE, self.strip
        if not 0 <= tx < s.cols:
            return None
        best = None
        for ty in range(2, ROWS):
            if s.hard(tx, ty) and not s.hard(tx, ty - 1) and not s.hard(tx, ty - 2) \
                    and not s.liquid[(ty - 1) * s.cols + tx]:
                fy = ty * TILE
                if best is None or abs(fy - y) < abs(best - y):
                    best = fy
        return best

    def _ceiling_above(self, x, y):
        tx = int(x) // TILE
        for ty in range(int(y - 40) // TILE, -1, -1):
            if self.strip.hard(tx, ty):
                return (ty + 1) * TILE
        return None

    def _spawn(self):
        S = self.samus
        kind = random.choice(FOES[self.area])
        how = FOE[kind][1]
        ahead = random.random() > 0.15
        x = self.cam + (self.W + 12 if ahead else -12)
        if how == "dive":                                # a Skree waits on the ceiling a little way ahead
            x = S.x + random.randint(90, 160)
        if not 8 < x < self.strip.w - 8:
            return
        e = Thing(kind, x, 0)
        e.hp = FOE[kind][2]
        e.vx = -1.0 if ahead else 1.0
        if how in ("crawl", "pipe"):
            fy = self._floor_near(x, S.y)
            if fy is None:
                return
            e.y = e.base = float(fy)
            if how == "pipe":
                e.state = "rise"
        elif how == "dive":
            cy = self._ceiling_above(x, S.y)
            if cy is None or cy > S.y - 56:
                return
            e.y, e.state = float(cy + FOE[kind][0][0][3]), "hang"
        elif how in ("fly", "wave"):
            e.y = e.base = S.y - 14
        elif how == "ring":
            e.y = S.y - 40 - random.randint(0, 40)
            dx, dy = S.x - x, (S.y - 16) - e.y
            n = max(1.0, (dx * dx + dy * dy) ** 0.5)
            e.vx, e.vy = dx / n * 1.2, dy / n * 1.2
        else:                                            # swoopers, swarms, bouncers, Metroids: from up high
            e.y = float(random.randint(48, max(49, int(S.y) - 40)))
            if how == "bounce":
                e.vx, e.vy = (-0.9 if ahead else 0.9), 0.8
            else:
                e.vx = 0.0
        self.enemies.append(e)

    def _enemies(self):
        self.next_foe -= 1
        if self.next_foe <= 0 and len(self.enemies) < 3 and self.i < len(self.path) - 90:
            self.next_foe = random.randint(110, 240)
            self._spawn()
        S, s = self.samus, self.strip
        for e in list(self.enemies):
            e.t += 1
            if e.state == "burst":
                if e.t > 12:
                    self.enemies.remove(e)
                continue
            how = FOE[e.kind][1]
            if how == "crawl":
                d = 1 if e.vx > 0 else -1
                nx = e.x + 0.5 * d
                tx, ty = int(nx + 8 * d) // TILE, int(e.y) // TILE
                if s.hard(tx, ty - 1) or not s.hard(tx, ty):
                    e.vx = -e.vx                         # a wall or an edge: back the other way
                else:
                    e.x = nx
            elif how == "fly":
                if s.hard(int(e.x + 10 * (1 if e.vx > 0 else -1)) // TILE, int(e.y - 4) // TILE):
                    e.vx = -e.vx
                e.x += e.vx * 0.8
            elif how == "wave":
                e.x += e.vx * 0.9
                e.y = e.base + 14 * math.sin(e.t / 14)
            elif how == "pipe":
                if e.state == "rise":
                    e.y -= 1.2
                    if e.y <= S.y - 10:
                        e.state = "go"
                        e.vx = 1.6 if S.x > e.x else -1.6
                else:
                    e.x += e.vx
            elif how == "dive":
                if e.state == "hang":
                    if abs(S.x - e.x) < 48:
                        e.state = "fall"
                else:
                    e.vy = min(4.0, e.vy + 0.3)
                    e.y += e.vy
                    e.x += 0.6 * (1 if S.x > e.x else -1)
                    if s.hard(int(e.x) // TILE, int(e.y) // TILE) or e.y > H:
                        e.state, e.t = "burst", 0        # it hits the floor and bursts
                        continue
            elif how in ("swoop", "swarm", "latch"):
                tx, ty = S.x, S.y - (36 if how == "latch" else 16)
                pull = {"swoop": 0.05, "swarm": 0.08, "latch": 0.035}[how]
                cap = {"swoop": 1.3, "swarm": 1.6, "latch": 0.9}[how]
                e.vx = max(-cap, min(cap, e.vx + max(-pull, min(pull, (tx - e.x) * 0.01))))
                e.vy = max(-cap, min(cap, e.vy + max(-pull, min(pull, (ty - e.y) * 0.01))))
                e.x += e.vx + (0.6 * math.sin(e.t / 5) if how == "swarm" else 0)
                e.y += e.vy
            elif how == "bounce":
                e.x += e.vx
                e.y += e.vy
                if s.hard(int(e.x + 8 * (1 if e.vx > 0 else -1)) // TILE, int(e.y - 8) // TILE):
                    e.vx = -e.vx
                if s.hard(int(e.x) // TILE, int(e.y + (1 if e.vy > 0 else -16)) // TILE) or e.y < 24:
                    e.vy = -e.vy
            elif how == "ring":
                e.x += e.vx
                e.y += e.vy
            if not (-60 < e.x - self.cam < self.W + 60) or not -40 < e.y < H + 40:
                self.enemies.remove(e)
                continue
            if e.state in ("go", "fall") and self._rect(e).intersects(QRect(int(S.x) - 6, int(S.y) - 30, 12, 30)):
                self.hurt()

    def _shots(self):
        for sh in list(self.shots):
            sh["t"] += 1
            sh["x"] += sh["vx"]
            sh["y"] += sh["vy"]
            if sh["t"] > (36 if sh["missile"] else 24) or self.strip.hard(int(sh["x"]) // TILE, int(sh["y"]) // TILE):
                self.shots.remove(sh)
                continue
            for e in self.enemies:
                if e.state in ("go", "hang", "fall", "rise") and \
                        self._rect(e).adjusted(-3, -3, 3, 3).contains(int(sh["x"]), int(sh["y"])):
                    e.hp -= 2 if sh["missile"] else 1
                    if e.hp <= 0:
                        e.state, e.t = "burst", 0
                        r = random.random()
                        if r < 0.3:
                            self.bits.append({"kind": "energy", "x": e.x, "y": e.y - 6, "t": 0})
                        elif r < 0.42:
                            self.bits.append({"kind": "missile", "x": e.x, "y": e.y - 4, "t": 0})
                    else:
                        e.flash = 8
                    self.shots.remove(sh)
                    break

    def _bits(self):
        for b in list(self.bits):
            b["t"] += 1
            if b["t"] > 360:
                self.bits.remove(b)

    # ---- drawing ----
    def draw(self, p):
        p.fillRect(QRect(0, 0, self.W, H), QColor("black"))
        cam = int(self.cam)
        p.drawImage(QRect(0, 0, self.W, H), self.strip.img, QRect(cam, 0, self.W, H))
        if self.strip.w - cam < self.W:
            p.fillRect(QRect(self.strip.w - cam, 0, self.W, H), QColor("black"))
        self._draw_clock(p)
        for b in self.bits:
            if b["t"] < 280 or (b["t"] // 4) % 2:
                if b["kind"] == "energy":
                    p.drawImage(int(b["x"]) - 4 - cam, int(b["y"]) - 4, cut("items", *ENERGY_BALL[(b["t"] // 4) % 2]))
                else:
                    p.drawImage(int(b["x"]) - 4 - cam, int(b["y"]) - 8, cut("items", *MISSILE_DROP))
        for e in self.enemies:
            self._draw_enemy(p, e, cam)
        for sh in self.shots:
            if sh["missile"]:
                img = cut("samus", *MISSILE_UP) if sh["vy"] else cut("samus", *MISSILE, flip=sh["vx"] < 0)
            else:
                img = cut("samus", *BEAM[(sh["t"] // 3) % 2])
            p.drawImage(int(sh["x"] - img.width() / 2) - cam, int(sh["y"] - img.height() / 2), img)
        self._draw_samus(p, cam)
        self._draw_hud(p)
        if self.fade:
            a = int(255 * (1 - abs(self.fade - 20) / 20))
            p.fillRect(QRect(0, 0, self.W, H), QColor(0, 0, 0, a))

    def _block(self, n=0):
        bx, by = BLOCKS[self.area]
        return cut("tiles", bx + 18 * n, by, 16, 16, clear=False)

    def _draw_clock(self, p):
        for x, y, _i in self.clock_cells():
            b = self.blocks.get((x, y))
            if b is None:
                p.drawImage(x, y, self._block())
            elif b[1] == "out":                          # block, crumbling, dust, gone
                if b[0] < 18:
                    p.drawImage(x, y, self._block(min(2, b[0] // 6)))
            elif b[0] >= 6:                             # growing back: dust, crumbled, whole
                p.drawImage(x, y, self._block(max(0, 2 - (b[0] - 6) // 6)))

    def _draw_samus(self, p, cam):
        S = self.samus
        if self.blink and (self.blink // 2) % 2:
            return
        flip = self.facing < 0
        st, k = S.state, (S.t // 6) % 3
        if st == "front":
            frame = SAMUS["front"]
            flip = False
        elif st == "spin":
            frame = SAMUS["spin"][(S.t // 3) % 4]
        elif st == "air":
            frame = SAMUS["shootjump"] if self.aim == "ahead" else SAMUS["up"] if self.aim == "up" else SAMUS["jump"]
        elif st == "run":
            frame = (SAMUS["shootrun"][k] if self.aim == "ahead" else SAMUS["uprun"][k] if self.aim == "up"
                     else SAMUS["run"][k])
        else:
            frame = SAMUS["shoot"] if self.aim == "ahead" else SAMUS["up"] if self.aim == "up" else SAMUS["stand"]
        img = cut("samus", *frame, flip=flip)
        sx = int(S.x) - cam
        if st == "spin":
            x, y = sx - img.width() // 2, int(S.y) - 20 - img.height() // 2
        else:
            x, y = sx - int(anchor(frame, flip) + 0.5), int(S.y) - img.height()
        p.drawImage(x, y, img)

    def _draw_enemy(self, p, e, cam):
        if e.state == "burst":
            p.drawImage(int(e.x) - 8 - cam, int(e.y) - 14, cut("samus", *BURST[min(1, e.t // 6)]))
            return
        if e.flash:
            e.flash -= 1
            if e.flash % 2:
                return
        frames = FOE[e.kind][0]
        how = FOE[e.kind][1]
        frame = frames[0] if how == "dive" and e.state == "hang" else frames[(e.t // 8) % len(frames)]
        img = cut("enemies", *frame, flip=e.vx > 0 and how in ("fly", "swoop", "pipe", "wave"))
        p.drawImage(int(e.x - img.width() / 2) - cam, int(e.y) - img.height(), img)

    def _digits(self, p, x, y, text):
        for ch in text:
            p.drawImage(x, y, cut("items", DIGIT_X + 9 * int(ch), DIGIT_Y, 8, 8))
            x += 8

    def _draw_hud(self, p):
        left = max(0, (self.W - 256) // 2) + 24
        for i in range(self.tanks):                      # energy tanks over the EN
            p.drawImage(left + 24 + i * 9, 18, cut("items", *(TANK_FULL if i < self.full_tanks else TANK_EMPTY)))
        p.drawImage(left, 28, cut("items", *EN))
        p.drawImage(left + 16, 28, cut("items", *DOTS))
        self._digits(p, left + 24, 28, f"{max(0, self.energy) % 100:02d}")
        p.drawImage(left, 40, cut("items", *MISSILE_ICON))
        self._digits(p, left + 24, 40, f"{self.missiles:03d}")


# ---- the screen saver -----------------------------------------------------------------------------------------------
def make_saver_class(Saver):
    class ClaudesMissionSaver(Saver):
        """The game, scaled up to the screen without smoothing."""
        FPS = 60

        def __init__(self, parent=None):
            super().__init__(parent)
            self.game = None
            self.missing = not available()

        def _ensure(self):
            if self.missing or self.width() < 4:
                return None
            w = max(288, int(round(H * self.width() / max(1, self.height()))))
            if self.game is None or self.game.W != w:
                self.game = ClaudesMission(w)
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
                p.drawText(self.rect(), Qt.AlignCenter, "Metroid: Claude's Mission needs its sprite sheets and maps "
                           f"in\nE:\\{FOLDERS[0]}")
                return
            frame = QImage(g.W, H, QImage.Format_ARGB32)
            q = QPainter(frame)
            g.draw(q)
            q.end()
            scale = min(self.width() / g.W, self.height() / H)
            w, h = g.W * scale, H * scale
            p.drawImage(QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h), frame)

    return ClaudesMissionSaver
