"""The lemmings' animations, cut from the PC sprite sheet in Local Storage\\Lemmings\\sprites\\LEM 1.png: a grid of
17-pixel cells (one every 18 pixels from x = 9) in bands, on a dark blue background that becomes transparent.

Each animation is facing right; facing left is the same frames mirrored. Frames are scaled up once (nearest
neighbour, so the pixels stay crisp) and anchored at the lemming's feet.

    sheet = Sprites(path, scale=3)
    pm, (ax, ay) = sheet.frame("walk", n, facing=1)   # draw pm at (foot_x*scale - ax, foot_y*scale - ay)
    sheet.trapdoor(i)                                 # 0 closed ... 9 open
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QTransform

BANDS = {"top": (0, 11), "dig": (13, 23), "climb": (29, 40), "bash": (42, 52), "mine": (66, 79), "build": (95, 108),
         "fx": (110, 120), "float": (122, 138)}
ANIMS = {
    "walk": ("top", range(0, 8)),
    "fall": ("top", range(18, 22)),
    "dig": ("dig", range(0, 16)),
    "block": ("dig", range(16, 24)),
    "climb": ("climb", range(0, 8)),
    "hoist": ("climb", range(8, 14)),
    "bash": ("bash", range(0, 32)),
    "mine": ("mine", range(0, 24)),
    "build": ("build", range(0, 16)),
    "shrug": ("top", range(16, 18)),
    "splat": ("fx", range(0, 16)),
    "exit": ("fx", range(16, 24)),
    "ohno": ("fx", range(24, 32)),
    "float": ("float", range(1, 6)),
    "open": ("float", range(0, 1)),
}
CELL_X0, CELL_STEP, CELL_W = 9, 18, 17
TRAP_TOP, TRAP_BOTTOM, TRAP_X0, TRAP_STEP, TRAP_W = 184, 209, 27, 50, 49


class Sprites:
    def __init__(self, path, scale=3):
        self.scale = scale
        sheet = QImage(str(path)).convertToFormat(QImage.Format_ARGB32)
        if sheet.isNull():
            raise FileNotFoundError(path)
        self.bg = sheet.pixel(sheet.width() - 1, sheet.height() - 1)
        self.frames = {}            # name -> [(pixmap right, pixmap left, anchor)]
        for name, (band, cells) in ANIMS.items():
            top, bottom = BANDS[band]
            imgs = [self._clean(sheet.copy(CELL_X0 + CELL_STEP * k, top, CELL_W, bottom - top + 1)) for k in cells]
            # one anchor for the whole animation, so it doesn't jitter: the centre column, the lowest drawn row + 1
            low = 0
            for im in imgs:
                for y in range(im.height() - 1, -1, -1):
                    if any((im.pixel(x, y) >> 24) for x in range(im.width())):
                        low = max(low, y)
                        break
            ax, ay = CELL_W // 2, low + 1
            out = []
            for im in imgs:
                right = self._scaled(im)
                left = self._scaled(im.mirrored(True, False))
                out.append((right, left, (ax * scale, ay * scale)))
            self.frames[name] = out
        self.trap = [self._scaled(self._clean(sheet.copy(TRAP_X0 + TRAP_STEP * k, TRAP_TOP, TRAP_W,
                                                         TRAP_BOTTOM - TRAP_TOP + 1))) for k in range(10)]
        self.trap_offset = self._trap_offset(sheet)

    def _clean(self, im):
        im = im.convertToFormat(QImage.Format_ARGB32)
        w, h = im.width(), im.height()
        for y in range(h):
            for x in range(w):
                p = im.pixel(x, y)
                r, g, b = (p >> 16) & 255, (p >> 8) & 255, p & 255
                grid = r > 140 and abs(r - g) < 16 and abs(g - b) < 16 and (y in (0, h - 1) or x in (0, w - 1))
                if p == self.bg or grid:            # the background, or the sheet's grey grid lines at the edges
                    im.setPixel(x, y, 0)
        return im

    def _scaled(self, im):
        return QPixmap.fromImage(im.scaled(im.width() * self.scale, im.height() * self.scale,
                                           Qt.IgnoreAspectRatio, Qt.FastTransformation))

    def _trap_offset(self, sheet):
        """Where the trapdoor graphic starts inside its cell (the level data gives the graphic's own top-left)."""
        last = self._clean(sheet.copy(TRAP_X0 + TRAP_STEP * 9, TRAP_TOP, TRAP_W, TRAP_BOTTOM - TRAP_TOP + 1))
        xs, ys = [], []
        for y in range(last.height()):
            for x in range(last.width()):
                p = last.pixel(x, y)
                if (p >> 24) and ((p >> 16) & 255) + ((p >> 8) & 255) + (p & 255) > 90:
                    xs.append(x)
                    ys.append(y)
        return (min(xs), min(ys)) if xs else (0, 0)

    def frame(self, name, n, facing=1):
        seq = self.frames.get(name) or self.frames["walk"]
        right, left, anchor = seq[n % len(seq)]
        return (right if facing >= 0 else left), anchor

    def icon(self, name):
        """A frame for a skill button."""
        return self.frame(name, 3 if name not in ("block", "open") else 0, 1)[0]
