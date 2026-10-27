"""Zelda II: The Adventure of Claude - a side-scrolling Zelda II clock screen saver, after The Legend of Claude.

Link walks right through Hyrule's wild-encounter fields - the real grass, swamp, forest, desert and graveyard strips
from the stage sheet, one after another, fading between them as the game does when you meet a monster. Bots hop at
him, Lowders crawl, Octoroks bounce, Moblins and Dairas march up: he stabs high at the tall ones and ducks to stab
the low ones, they burst, the experience they're worth floats up and now and then a P-bag drops for him to pick up.
A touch knocks him back a life segment. Raised ground he jumps up onto. The time is built in the sky out of palace
stone; when the minute changes the changed blocks crack and crumble and new ones set, and on the hour he holds up a
heart container. The HUD has his magic, his life and his experience, in the game's own lettering.

The pictures come from the sprite sheets in Local Storage/Zelda2 - Sprites (the Spriters Resource's NES sheets,
ripped by Mister Mike and Jackster). Drawn at the NES's own size (240 lines, as wide as the screen's shape needs)
and scaled up without smoothing."""
import random
from array import array
from datetime import datetime

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter

FOLDER = "Zelda2 - Sprites"
_P = "NES - Zelda 2_ The Adventure of Link - "
SHEETS = {"wild": _P + "Stages - Wild Encounters_ Multiple Screens.png",
          "link": _P + "Playable Characters - Link.png",
          "enemies": _P + "Enemies & Bosses - Overworld Enemies.png",
          "items": _P + "Miscellaneous - Items & Objects.png",
          "palace": _P + "Miscellaneous - Palace Tilesets.png",
          "font": _P + "Miscellaneous - Font.png"}
CLEAR = {0xFF008000, 0xFF800080, 0xFF5F97FF}       # the sheets' green backdrop, purple boxes, the font's blue: clear
H, HUD, FIELD = 240, 32, 208

# the encounter strips: (name, x, y, width) on the stage sheet, all 208 high; who you meet there
PANELS = [("grass", 1, 21, 768), ("swamp", 774, 21, 768), ("forest", 1, 244, 768), ("forest", 774, 244, 768),
          ("desert", 1, 467, 768), ("desert", 774, 467, 768), ("graveyard", 1, 690, 1024),
          ("grass", 1, 923, 768), ("swamp", 774, 923, 768), ("forest", 1, 1146, 768),
          ("graveyard", 774, 1146, 768), ("desert", 1, 1369, 768)]
FOES = {"grass": ["bot", "lowder", "octorok", "moblin"], "swamp": ["bot", "octorok", "bot"],
        "forest": ["moblin", "daira", "bot"], "desert": ["lowder", "octorok", "moblin"],
        "graveyard": ["moblin", "bot", "daira"]}

# Link (faces right on the sheet): idle, walk 1-3, duck, jump, hurt, holding up
LINK = {"idle": (1, 11, 16, 32), "walk": [(29, 11, 16, 32), (46, 11, 16, 32), (63, 11, 16, 32)],
        "duck": (84, 11, 16, 32), "jump": (117, 11, 16, 32), "hurt": (155, 11, 16, 32), "hold": (188, 11, 16, 32),
        "wind": (1, 73, 24, 32), "stab": (26, 73, 32, 32), "duckstab": (67, 73, 32, 32)}
# enemies (face left on the sheet): frames, health, experience, tall (stabbed high) or low (stabbed ducking)
ENEMIES = {"bot": {"frames": [(298, 11, 16, 16), (315, 11, 16, 16)], "hp": 1, "exp": 2, "tall": False},
           "lowder": {"frames": [(188, 100, 16, 16), (205, 100, 16, 16)], "hp": 1, "exp": 5, "tall": False},
           "octorok": {"frames": [(291, 182, 16, 16), (308, 182, 16, 16)], "hp": 1, "exp": 10, "tall": False},
           "moblin": {"frames": [(449, 11, 16, 33), (466, 11, 16, 33)], "hp": 2, "exp": 20, "tall": True},
           "daira": {"frames": [(1, 64, 16, 32), (18, 64, 16, 32)], "hp": 3, "exp": 50, "tall": True}}
BURST = [(86, 42, 16, 16), (103, 42, 16, 16), (120, 42, 16, 16), (137, 42, 16, 16)]
PBAG = (1, 11, 8, 16)
HEART = (203, 11, 16, 16)
BLOCK, CRACKED = (35, 21, 16, 16), (18, 113, 16, 16)     # Parapa Palace's stone, and its crumbling block
FONT = "/.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-"
DIGITS = {"0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111",
          "4": "101101111001001", "5": "111100111001111", "6": "111100111101111", "7": "111001001001001",
          "8": "111101111101111", "9": "111101111001111"}
GRAVITY = 0.25


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


def cut(key, x, y, w=16, h=16, flip=False):
    k = (key, x, y, w, h, flip)
    if k not in _cache:
        img = _clear(_sheet(key).copy(x, y, w, h))
        if flip:
            img = img.mirrored(True, False)
        _cache[k] = img
    return _cache[k]


def glyph(ch):
    i = FONT.find(ch)
    if i < 0:
        return None
    return cut("font", 24 + 16 * (i % 16), 24 + 16 * (i // 16), 8, 8)


class Panel:
    """An encounter strip: its picture, and the ground's height at each column (from the ground's own colours, so
    stumps, cacti and gravestones stand on it rather than being steps)."""

    def __init__(self, index):
        self.kind, x, y, self.w = PANELS[index]
        self.img = _sheet("wild").copy(x, y, self.w, FIELD)
        img = self.img
        w = self.w
        px = array("I")
        px.frombytes(bytes(img.constBits())[:w * FIELD * 4])
        # what's above the ground: the sky (unless the ground shares its colour - the forest's canopy), and darkness
        bottom = {px[(FIELD - 1 - r) * w + c] for r in range(8) for c in range(0, w, 2)}
        top = max(set(px[:w * 6]), key=px[:w * 6].count)
        floor = [px[(FIELD - 1 - r) * w + c] for r in range(8) for c in range(w)]
        above = ({top} if top not in bottom else set()) | \
            ({0xFF000000} if floor.count(0xFF000000) < len(floor) // 4 else set())   # (a graveyard's soil is half black)
        # each row as a running count of its solid pixels, so a 32-pixel stretch of it can be weighed at once
        rows = []
        for y in range(FIELD):
            run, acc = [0], 0
            for c in range(w):
                acc += px[y * w + c] not in above
                run.append(acc)
            rows.append(run)
        self.ground = []                       # (in 8-pixel columns: up from the bottom while 32 pixels round about
        for c0 in range(0, w, 8):              # are mostly solid - a stump, a cactus, a gravestone or a tuft of tall
            a, b = max(0, c0 - 12), min(w, c0 + 20)   # grass is too thin to stand on, with sky either side of it)
            y, thin = FIELD - 1, 0
            while y > 24:
                thin = thin + 1 if rows[y][b] - rows[y][a] < 0.7 * (b - a) else 0
                if thin >= 4:
                    break
                y -= 1
            self.ground.append((y + thin) // 8 * 8)

    def at(self, x):
        c = int(x) // 8
        return self.ground[max(0, min(len(self.ground) - 1, c))]


class Thing:
    def __init__(self, kind, x, y):
        self.kind, self.x, self.y = kind, float(x), float(y)        # y: feet
        self.vx = self.vy = 0.0
        self.t = 0
        self.state = "walk"
        self.facing = -1


# ---- the game -------------------------------------------------------------------------------------------------------
class AdventureOfClaude:
    def __init__(self, width=320, now=None):
        self.W = width
        self.now = now or datetime.now
        self.order = list(range(len(PANELS)))
        random.shuffle(self.order)
        self.which = 0
        self.panel = Panel(self.order[0])
        self.link = Thing("link", 24, self.panel.at(32))
        self.link.facing = 1
        self.enemies, self.bits = [], []
        self.life, self.magic, self.exp = 8, 8, 0
        self.next_foe = 90
        self.fade = 0
        self.hold = 0
        self.sounds = []
        self.text = self._time_text()
        self.cracking = []                     # [x, y, t] blocks crumbling (screen pixels)
        self.coming = None                     # the next time, set once the old blocks have crumbled
        self.last_minute = self.now().minute
        self.cam = 0.0

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
        return [(x0 + cx * 16, HUD + 12 + cy * 16, i) for cx, cy, i in cells]

    # ---- the clock ticks ----
    def step(self):
        t = self.now()
        if t.minute != self.last_minute:
            self.last_minute = t.minute
            new = self._time_text()
            keep = {(x, y) for x, y, _ in self.clock_cells(new)}
            for x, y, i in self.clock_cells():
                if (x, y) not in keep or i >= len(new) or new[i] != self.text[i]:
                    self.cracking.append([x, y, 0])
            self.coming = new
            if t.minute == 0:
                self.hold = 150
        for c in list(self.cracking):
            c[2] += 1
            if c[2] > 40:
                self.cracking.remove(c)
        if self.coming and not any(c[2] < 30 for c in self.cracking):
            self.text, self.coming = self.coming, None       # crumbled: the new time sets
        if self.fade:
            self.fade -= 1
            if self.fade == 20:
                self._next_panel()
            return
        self._link()
        self._enemies()
        self._bits()
        self.cam = max(0.0, min(self.panel.w - self.W, self.link.x - self.W * 0.35))
        if self.link.x > self.panel.w - 24 and not self.fade:
            self.fade = 40                            # the edge of the field: on to the next encounter

    def _next_panel(self):
        self.which = (self.which + 1) % len(self.order)
        if self.which == 0:
            random.shuffle(self.order)
        self.panel = Panel(self.order[self.which])
        L = self.link
        L.x, L.y, L.vy, L.state = 16, self.panel.at(24), 0.0, "walk"
        self.enemies, self.bits = [], []
        self.next_foe = 120
        self.cam = 0.0
        self.life = min(8, self.life + 3)                # (a fairy on the road between encounters)

    # ---- Link ----
    def _link(self):
        L = self.link
        L.t += 1
        ground = self.panel.at(L.x + 8)
        if self.hold:
            self.hold -= 1
            L.state = "hold"
            return
        if L.state == "hold":
            L.state = "walk"
        if L.state == "hurt":
            L.x = max(0, L.x + L.vx)
            self._fall(L)
            if L.t > 24:
                L.state = "walk"
            return
        if L.state in ("stab", "duckstab"):
            if 4 <= L.t <= 12:
                hit = self._sword()
                for e in self.enemies:
                    if e.state == "walk" and hit.intersects(self._rect(e)):
                        self._hit(e)
            if L.t >= 16:
                L.state = "walk"
            return
        foe = self._foe_near(L)
        if foe is not None and L.vy == 0:
            L.facing = 1 if foe.x > L.x else -1
            L.state, L.t = ("stab" if ENEMIES[foe.kind]["tall"] or foe.y < L.y - 12 else "duckstab"), 0
            return
        for b in list(self.bits):                  # P-bags: walk over to get them
            if b["kind"] == "pbag" and abs(b["x"] - L.x) < 12 and abs(b["y"] - L.y) < 16:
                self.bits.remove(b)
                self.exp += 50
                self._float(b["x"], b["y"] - 16, "50")
        L.facing = 1                                     # on he goes (a foe in reach gets the sword first)
        L.x += 0.9
        ahead = self.panel.at(L.x + 20)
        if L.vy == 0 and ahead < ground - 3:              # a rise ahead: up onto it
            L.vy = -4.6
        self._fall(L)

    def _fall(self, t, ground=None):
        ground = self.panel.at(t.x + 8) if ground is None else ground
        t.vy += GRAVITY
        t.y += t.vy
        if t.y >= ground:
            t.y, t.vy = ground, 0.0

    def _sword(self):
        L = self.link
        y = L.y - (24 if L.state == "stab" else 12)
        x = L.x + 16 if L.facing > 0 else L.x - 16
        return QRect(int(x), int(y), 16, 6)

    def _rect(self, e):
        h = ENEMIES[e.kind]["frames"][0][3]
        return QRect(int(e.x) + 2, int(e.y) - h + 2, 12, h - 2)

    def _foe_near(self, L):
        best = None
        for e in self.enemies:
            if e.state != "walk":
                continue
            d = e.x - L.x
            if (0 < d <= 26 or -14 <= d < 0) and abs(e.y - L.y) < 28 and (best is None or abs(d) < abs(best.x - L.x)):
                best = e
        return best

    def hurt(self, from_x):
        L = self.link
        if L.state in ("hurt", "hold"):
            return
        self.life = max(1, self.life - 1)
        L.state, L.t = "hurt", 0
        L.vx = -1.5 if from_x > L.x else 1.5
        L.vy = -2.0

    # ---- enemies ----
    def _enemies(self):
        self.next_foe -= 1
        if self.next_foe <= 0 and len(self.enemies) < 3:
            self.next_foe = random.randint(150, 330)
            kind = random.choice(FOES[self.panel.kind])
            behind = random.random() < 0.15 and self.cam > 0
            x = self.cam - 20 if behind else self.cam + self.W + 8
            if 0 < x < self.panel.w - 16:
                e = Thing(kind, x, self.panel.at(x + 8))
                e.hp = ENEMIES[kind]["hp"]
                e.facing = 1 if behind else -1
                self.enemies.append(e)
        L = self.link
        for e in list(self.enemies):
            e.t += 1
            if e.state == "dying":
                if e.t > 16:
                    self.enemies.remove(e)
                    self.exp += ENEMIES[e.kind]["exp"]
                    self._float(e.x, e.y - 20, str(ENEMIES[e.kind]["exp"]))
                    if random.random() < 0.25:
                        self.bits.append({"kind": "pbag", "x": e.x + 4, "y": e.y, "t": 0})
                continue
            if e.state == "flash":
                if e.t > 12:
                    e.state, e.t = "walk", 0
                continue
            e.facing = 1 if L.x > e.x else -1
            if e.kind in ("bot", "octorok"):          # hoppers
                if e.vy == 0 and e.t % (50 if e.kind == "bot" else 70) == 0:
                    e.vy = -3.2 if e.kind == "bot" else -2.6
                    e.vx = 0.9 * e.facing if e.kind == "bot" else 0.0
                if e.vy != 0 or e.y < self.panel.at(e.x + 8):
                    e.x += e.vx
                self._fall(e)
                if e.vy == 0:
                    e.vx = 0.0
            else:
                e.x += {"lowder": 0.45, "moblin": 0.5, "daira": 0.6}[e.kind] * e.facing
                self._fall(e)
            if not (-40 < e.x - self.cam < self.W + 40):
                self.enemies.remove(e)
                continue
            if L.state not in ("hurt", "hold") and self._rect(e).intersects(QRect(int(L.x) + 3, int(L.y) - 28, 10, 26)):
                if L.state in ("stab", "duckstab") and 4 <= L.t <= 12:
                    continue
                self.hurt(e.x)

    def _hit(self, e):
        e.hp -= 1
        e.state, e.t = ("dying" if e.hp <= 0 else "flash"), 0
        e.x += 6 * (1 if e.x > self.link.x else -1)

    def _float(self, x, y, text):
        self.bits.append({"kind": "exp", "x": x, "y": y, "t": 0, "text": text})

    def _bits(self):
        for b in list(self.bits):
            b["t"] += 1
            if b["kind"] == "exp":
                b["y"] -= 0.4
                if b["t"] > 50:
                    self.bits.remove(b)
            elif b["t"] > 600:
                self.bits.remove(b)

    # ---- drawing ----
    def draw(self, p):
        p.fillRect(QRect(0, 0, self.W, H), QColor("black"))
        cam = int(self.cam)
        p.drawImage(QRect(0, HUD, self.W, FIELD), self.panel.img, QRect(cam, 0, self.W, FIELD))
        if self.panel.w < self.W:
            p.fillRect(QRect(self.panel.w, HUD, self.W - self.panel.w, FIELD), QColor("black"))
        self._draw_clock(p)
        for b in self.bits:
            if b["kind"] == "pbag":
                if b["t"] < 480 or (b["t"] // 4) % 2:
                    p.drawImage(int(b["x"]) - cam, HUD + int(b["y"]) - 16, cut("items", *PBAG))
        for e in self.enemies:
            self._draw_enemy(p, e, cam)
        self._draw_link(p, cam)
        for b in self.bits:
            if b["kind"] == "exp":
                self._text(p, int(b["x"]) - cam, HUD + int(b["y"]), b["text"])
        self._draw_hud(p)
        if self.fade:
            a = int(255 * (1 - abs(self.fade - 20) / 20))
            p.fillRect(QRect(0, HUD, self.W, FIELD), QColor(0, 0, 0, a))

    def _draw_clock(self, p):
        block = cut("palace", *BLOCK)
        crumbling = {(x, y) for x, y, _t in self.cracking}
        for x, y, _i in self.clock_cells():
            if (x, y) not in crumbling or not self.coming:
                p.drawImage(x, y, block)
        cracked = cut("palace", *CRACKED)
        for x, y, t in self.cracking:                   # cracking, then the pieces falling away
            if t < 14:
                p.drawImage(x, y, cracked)
            else:
                f = t - 14
                for i, (dx, dy) in enumerate(((0, 0), (8, 0), (0, 8), (8, 8))):
                    px = x + dx + (i % 2 * 2 - 1) * f * 0.6
                    py = y + dy + f * f * 0.05 * (1 + i // 2)
                    p.drawImage(int(px), int(py), block, dx, dy, 8, 8)

    def _draw_link(self, p, cam):
        L = self.link
        if L.state == "hurt" and (L.t // 2) % 2:
            return
        flip = L.facing < 0
        if L.state == "hold":
            frame = LINK["hold"]
        elif L.state in ("stab", "duckstab"):
            frame = LINK["wind"] if L.t < 4 else LINK["stab" if L.state == "stab" else "duckstab"]
        elif L.vy != 0:
            frame = LINK["jump"]
        elif L.state == "hurt":
            frame = LINK["hurt"]
        else:
            frame = LINK["walk"][(L.t // 8) % 3]
        img = cut("link", *frame, flip=flip)
        x = int(L.x) - cam - (img.width() - 16 if flip else 0)
        p.drawImage(x, HUD + int(L.y) - 32, img)
        if L.state == "hold":
            p.drawImage(int(L.x) - cam, HUD + int(L.y) - 46, cut("items", *HEART))

    def _draw_enemy(self, p, e, cam):
        spec = ENEMIES[e.kind]
        x = int(e.x) - cam
        if e.state == "dying":
            p.drawImage(x, HUD + int(e.y) - 16, cut("items", *BURST[min(3, e.t // 4)]))
            return
        if e.state == "flash" and (e.t // 2) % 2:
            return
        frame = spec["frames"][(e.t // 12) % 2] if e.vy == 0 else spec["frames"][1]
        img = cut("enemies", *frame, flip=e.facing > 0)
        p.drawImage(x, HUD + int(e.y) - img.height(), img)

    def _text(self, p, x, y, text):
        for ch in text.upper():
            g = glyph(ch)
            if g is not None:
                p.drawImage(x, y, g)
            x += 8

    def _draw_hud(self, p):
        left = max(0, (self.W - 256) // 2)
        self._text(p, left + 8, 8, "MAGIC")
        self._text(p, left + 104, 8, "LIFE")
        for i in range(8):                               # the bars: magic white, life red
            p.fillRect(QRect(left + 8 + i * 9, 18, 8, 6), QColor(252, 252, 252) if i < self.magic else QColor(60, 60, 60))
            p.fillRect(QRect(left + 104 + i * 9, 18, 8, 6), QColor(216, 40, 0) if i < self.life else QColor(60, 60, 60))
        self._text(p, left + 192, 8, "EXP")
        self._text(p, left + 192, 18, f"{self.exp % 10000:04d}")


# ---- the screen saver -----------------------------------------------------------------------------------------------
def make_saver_class(Saver):
    class AdventureOfClaudeSaver(Saver):
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
                self.game = AdventureOfClaude(w)
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
                p.drawText(self.rect(), Qt.AlignCenter, "Zelda II: The Adventure of Claude needs its sprite sheets "
                           f"in\nE:\\{FOLDER}")
                return
            frame = QImage(g.W, H, QImage.Format_ARGB32)
            q = QPainter(frame)
            g.draw(q)
            q.end()
            scale = min(self.width() / g.W, self.height() / H)
            w, h = g.W * scale, H * scale
            p.drawImage(QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h), frame)

    return AdventureOfClaudeSaver
