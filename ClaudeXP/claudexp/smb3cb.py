"""Super Claude Bros. 3: the Super Mario Bros. clock screen saver (supercb.py) in Super Mario Bros. 3's clothes.

The game is Super Claude Bros' own - the ground made ahead of the camera with its pipes, pits, walls and staircases,
the floating bricks and '?' blocks, the Goombas and Koopa Troopas walking in, Mario jumping and stomping, the time
spelled out in bricks that he bumps when the minute changes - drawn from Super Mario Bros. 3's sheets in Local
Storage/SMB3 - Sprites: Raccoon Mario (or small, Super or Fire Mario, or Luigi), SMB3's Goombas, Koopas and their
shells, its striped ground, wooden blocks, bricks and '?' blocks, its pipes, spinning coins and points, and World 1's
own scenery behind - clouds, the big round bushes and the bolted pastel blocks - drifting at half speed.
Sound effects, when switched on, are Super Claude Bros' (Local Storage/SMB Clock/sounds)."""
import math
from array import array

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter

from . import supercb as base

FOLDER = "SMB3 - Sprites"
SHEETS = {"stage": "NES - Super Mario Bros. 3 - Grass Land - Stage 1-1.png",
          "chars": "NES - Super Mario Bros. 3 - Playable Characters - Mario & Luigi.png",
          "enemies": "NES - Super Mario Bros. 3 - Enemies & Bosses - Enemies.png",
          "items": "NES - Super Mario Bros. 3 - Miscellaneous - Items and Objects.png",
          "text": "NES - Super Mario Bros. 3 - Miscellaneous - On-Screen Text.png"}
SKY = QColor(156, 252, 240)
# the sheets' backdrops, frame boxes and pink * marks, and the stage's sky: see-through
CLEAR = {0xFF29587C, 0xFF4491BE, 0xFF9653A5, 0xFF23323E, 0xFFFD72CB, 0xFFAFF9F0, 0xFF9CFCF0}
H, GROUND = base.H, base.GROUND

# character -> its frames (x, y, w, h) on the sheet, as Super Claude Bros counts them: stand, run 1-3, skid, jump, dead
CHARACTERS = {
    "Mario": [(1, 16, 16, 16), (19, 16, 16, 16), (1, 16, 16, 16), (19, 16, 16, 16), (109, 16, 16, 16),
              (91, 16, 16, 16), (307, 16, 16, 16)],
    "Luigi": [(1, 52, 16, 16), (19, 52, 16, 16), (1, 52, 16, 16), (19, 52, 16, 16), (109, 52, 16, 16),
              (91, 52, 16, 16), (307, 52, 16, 16)],
    "Super Mario": [(1, 88, 16, 32), (19, 88, 16, 32), (1, 88, 16, 32), (37, 88, 16, 32), (195, 88, 16, 32),
                    (73, 88, 16, 32), (1, 88, 16, 32)],
    "Super Luigi": [(1, 174, 16, 32), (19, 174, 16, 32), (1, 174, 16, 32), (37, 174, 16, 32), (195, 174, 16, 32),
                    (73, 174, 16, 32), (1, 174, 16, 32)],
    "Fire Mario": [(1, 260, 16, 32), (19, 260, 16, 32), (1, 260, 16, 32), (37, 260, 16, 32), (195, 260, 16, 32),
                   (73, 260, 16, 32), (1, 260, 16, 32)],
    "Raccoon Mario": [(1, 346, 24, 32), (27, 346, 24, 32), (1, 346, 24, 32), (53, 346, 24, 32), (339, 346, 16, 32),
                      (105, 346, 24, 32), (1, 346, 24, 32)],
}
DEFAULT_CHARACTER = "Raccoon Mario"
# the stage's own pieces, from Stage 1-1
GROUND_TOP, GROUND_BODY = (656, 400), (656, 416)
WOOD, BRICK, QUESTION = (1568, 400), (1952, 400), (176, 352)
PIPE_LIP, PIPE_BODY = (352, 368, 32, 16), (352, 384, 32, 16)
USED = (435, 152)                                    # (items sheet)
COINS = [(435, 310), (445, 310)]
POINTS = {"100": (1, 29), "200": (18, 29), "400": (35, 29)}
# World 1's scenery, from Stage 1-1 (bottoms on the ground): (x, y, w, h) on the stage, where in the 768 band
SCENERY = [((240, 336, 88, 80), 150), ((16, 352, 128, 64), 0), ((160, 400, 48, 16), 290),
           ((400, 304, 216, 112), 420), ((160, 400, 48, 16), 700)]
CLOUDS = [((120, 272, 48, 24), 70, 40), ((328, 256, 32, 24), 330, 22), ((648, 280, 32, 24), 600, 55)]


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


def band():
    """World 1's scenery, 768 pixels wide, the sky see-through: bushes and bolted blocks on the ground, clouds."""
    if "band" not in _cache:
        img = QImage(768, GROUND, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        p = QPainter(img)
        for (x, y, w, h), at in SCENERY:
            p.drawImage(at, GROUND - h, cut("stage", x, y, w, h))
        for (x, y, w, h), at, top in CLOUDS:
            p.drawImage(at, top, cut("stage", x, y, w, h))
        p.end()
        _cache["band"] = img
    return _cache["band"]


def settings():
    """Display Properties' settings for it (the character; sound and the clock as Super Claude Bros has them)."""
    from . import display
    data = display.get().data.get("supercb3") or {}
    return {"character": data.get("character", DEFAULT_CHARACTER)}


# ---- the game -------------------------------------------------------------------------------------------------------
class SuperClaudeBros3(base.SuperClaudeBros):
    """Super Claude Bros, played the same way, drawn the SMB3 way."""

    def __init__(self, width=320, now=None):
        super().__init__(width, now)
        try:
            char = settings()["character"]
        except Exception:
            char = DEFAULT_CHARACTER
        self.char = char if char in CHARACTERS else DEFAULT_CHARACTER
        h = CHARACTERS[self.char][0][3]
        self.big = h == 32
        bottom = self.mario.y + self.mario.h
        self.mario.h = h
        self.mario.y = bottom - h

    def _pick_theme(self):
        """Always Grass Land (the overworld's Goombas and Koopas)."""
        if not self.theme_name:
            self.theme_name = "Overworld"
            self.theme = base.THEMES["Overworld"]
            self.scenery = "smb3"
            self.hour = 0

    def draw(self, p):
        cam = int(self.cam)
        p.fillRect(QRectF(0, 0, self.W, H), SKY)
        bg = band()
        x = -int(self.cam * 0.5) % 768 - 768                # (the scenery drifts at half speed)
        while x < self.W:
            p.drawImage(x, 0, bg)
            x += 768
        top, body = cut("stage", *GROUND_TOP), cut("stage", *GROUND_BODY)
        wood = cut("stage", *WOOD)
        c0, c1 = cam // base.TILE - 1, (cam + self.W) // base.TILE + 2
        for col in range(c0, c1):
            if self.top(col) is not None:
                p.drawImage(col * base.TILE - cam, GROUND, top)
                p.drawImage(col * base.TILE - cam, GROUND + 16, body)
        for col, y in self.cells:
            if c0 <= col < c1:
                p.drawImage(col * base.TILE - cam, y, wood)
        lip, pipe = cut("stage", *PIPE_LIP), cut("stage", *PIPE_BODY)
        for col, h in self.pipes.items():
            if c0 - 2 <= col < c1:
                y0 = GROUND - base.TILE * h
                p.drawImage(col * base.TILE - cam, y0, lip)
                for y in range(y0 + 16, GROUND, 16):
                    p.drawImage(col * base.TILE - cam, y, pipe)
        for (col, y), kind in self.floats.items():
            if c0 <= col < c1:
                lift = math.sin(math.pi * self.float_bumps[(col, y)] / 10) * 5 if (col, y) in self.float_bumps else 0
                p.drawImage(col * base.TILE - cam, int(y - lift), self._block(kind))
        self._draw_clock(p)
        for e in self.enemies:
            self._draw_enemy(p, e, cam)
        self._draw_mario(p, cam)
        for b in self.bits:
            self._draw_bit(p, b, cam)

    def _block(self, kind, frame=0):
        if kind == "brick":
            return cut("stage", *BRICK)
        if kind == "question":
            return cut("stage", *QUESTION)
        return cut("items", *USED)

    def _draw_enemy(self, p, e, cam):
        walk = (e.t // 10) % 2
        if e.kind == "goomba":
            img = cut("enemies", 35, 8, 16, 9) if e.state == "squished" else cut("enemies", 1 + 17 * walk, 1, 16, 16)
        elif e.state in ("shell", "flipped") or e.h == 16:
            spin = (e.t // 4) % 4 if e.vx else 0
            img = cut("enemies", 35 + 17 * spin, 56, 16, 16)
        else:
            img = cut("enemies", 1 + 17 * walk, 63, 16, 27, flip=e.vx > 0)   # (below the sheet's own * mark)
        if e.state == "flipped":
            img = img.mirrored(False, True)
        p.drawImage(int(e.x) - cam, int(e.y + e.h - img.height()), img)

    def _draw_mario(self, p, cam):
        m = self.mario
        if m.state == "gone":
            return
        frames = CHARACTERS[self.char]
        if m.state == "dead":
            f = 6
        else:
            grounded = m.state in ("enter", "to_clock", "back") or self.on_ground(m)
            if not grounded and m.state != "enter":
                f = 5
            elif m.state in ("run", "enter", "to_clock", "back"):
                f = 1 + (m.t // 5) % 3
            else:
                f = 0
        x, y, w, h = frames[f]
        right = getattr(m, "facing", 1) >= 0
        img = cut("chars", x, y, w, h, flip=right and m.state != "dead")     # (the sheet's frames face left)
        dx = -(w - 16) if right and w > 16 else 0                           # (the raccoon's tail trails behind)
        p.drawImage(int(m.x) - cam + dx, int(m.y + m.h - img.height()), img)

    def _draw_bit(self, p, b, cam):
        if b.kind == "debris":
            p.drawImage(int(b.x) - cam, int(b.y), cut("stage", BRICK[0] + 4, BRICK[1] + 4, 8, 8))
        elif b.kind == "coin":
            p.drawImage(int(b.x) - cam, int(b.y), cut("items", *COINS[(b.t // 4) % 2], 8, 16))
        elif b.kind == "score":
            p.drawImage(int(b.x) - cam, int(b.y), cut("text", *POINTS.get(b.text, POINTS["100"]), 12, 7))


# ---- the screen saver -----------------------------------------------------------------------------------------------
def make_saver_class(Saver):
    SMB1 = base.make_saver_class(Saver)

    class SuperClaudeBros3Saver(SMB1):
        """Super Claude Bros' screen saver (its sounds and scaling), with this game."""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.missing = not available()

        def _ensure(self):
            if self.missing or self.width() < 4:
                return None
            w = max(256, int(round(H * self.width() / max(1, self.height()))))
            if self.game is None or self.game.W != w:
                self.game = SuperClaudeBros3(w)
            return self.game

        def paintEvent(self, event):
            if self.missing:
                p = QPainter(self)
                p.fillRect(self.rect(), QColor("black"))
                p.setPen(QColor("white"))
                f = QFont("Tahoma")
                f.setPixelSize(max(9, self.height() // 30))
                p.setFont(f)
                p.drawText(self.rect(), Qt.AlignCenter, f"Super Claude Bros. 3 needs its sprite sheets in\nE:\\{FOLDER}")
                return
            super().paintEvent(event)

    return SuperClaudeBros3Saver
