"""Doggo's frames: cut from the sprite sheet in Local Storage\\Rover (drive E:), never copied into the program.

The sheet is a 27 x 27 grid of 38-pixel cells (1024 / 27), read row by row as one long reel: frame k is row k // 27,
column k % 27. Each action is a run of frames (ACTIONS below; worked out frame by frame from the sheet). A few cells
catch a sliver of the frame above them - a falling sheet of paper - so small specks touching a cell's top edge are
cleared as each frame is cut. Frames are cut once, scaled and cached as they're first needed; the walk is drawn
facing left, so going right is the same frames mirrored."""
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap, QTransform

GRID = 27
CELL = 38                                       # each frame's size on the sheet (1024 / 27, rounded)
FRAMES = 703                                    # the reel's length (the last row holds one frame)
SIT = 54                                        # sitting, looking at you: where every action starts and ends


def _run(a, b, hold=None, times=0):
    """Frames a..b (b < a runs backwards); hold=(i, j) repeats frames i..j `times` more times in the middle."""
    step = 1 if b >= a else -1
    out = list(range(a, b + step, step))
    if hold and times:
        i, j = hold
        loop = list(range(i, j + 1))
        at = out.index(j) + 1
        out[at:at] = loop * times
    return out


# ---- what the sheet holds ------------------------------------------------------------------------------------
# name: (menu label, frames, what he might say)
ACTIONS = {
    "greet": ("Say hello", _run(0, 23), ["Woof! Hi there!", "Hello, friend!", "Arf! You're here!"]),
    "bark": ("Bark", _run(513, 523), ["Woof!", "Arf arf!", "Bark!"]),
    "happy": ("Wag his tail", _run(621, 635), ["*wag wag wag*", "Happy doggo!"]),
    "pant": ("Pant happily", _run(688, 702, (697, 701), 2), ["*pant pant*", "Hehehe!"]),
    "look": ("Look around", _run(270, 306), ["Hmm?", "What's that?"]),
    "scratch": ("Scratch an itch", _run(307, 323), ["*scritch scritch*", "Itchy ear..."]),
    "dig": ("Dig a hole", _run(77, 101, (85, 92), 1), ["*dig dig dig*", "There's something down here!"]),
    "bone": ("Dig up a bone", _run(591, 620) + _run(586, 590), ["A bone! A bone!", "Found it!"]),
    "fetch": ("Fetch", _run(102, 139, (112, 118), 1), ["Look what I brought you!", "Fetched it!"]),
    "party": ("Party", _run(140, 162, (148, 155), 1), ["Party time!", "Yippee!", "Woohoo!"]),
    "news": ("Read the paper", _run(187, 211, (194, 199), 3), ["Let's see the news...", "*rustle*"]),
    "picture": ("Show a picture", _run(212, 242, (220, 228), 2), ["Look, it's me!", "My best side."]),
    "movie": ("Movie time", _run(243, 269, (248, 257), 2), ["Action!", "Lights, camera, woof!"]),
    "book": ("Read a book", _run(422, 475, (436, 448), 3), ["Once upon a time...", "*turns a page*"]),
    "notes": ("Take notes", _run(671, 687, (674, 683), 2), ["Noting that down.", "*scribble scribble*"]),
    "letter": ("Fetch the mail", _run(524, 548), ["You've got mail!", "A letter for you!"]),
    "chew": ("Chew a bone", _run(324, 345) + _run(346, 377, (352, 366), 2) + _run(378, 386) + _run(345, 324),
             ["*nom nom nom*", "Best bone ever."]),
    "sad": ("Mope", _run(648, 670), ["*whimper*", "Nobody's playing with me..."]),
}
TRICKS = [k for k in ACTIONS if k not in ("sad",)]
# little things he does while sitting about (no bubbles)
FIDGETS = [_run(44, 53), _run(54, 76), _run(162, 186), _run(410, 421), _run(476, 493)]
WALK_START = _run(549, 552)                     # from sitting, round to his side (facing left)
WALK = _run(553, 584)                           # nose down, trotting along (facing left)
WALK_END = _run(585, 590)                       # back round to face you
LIE_DOWN = _run(324, 345)
FALL_ASLEEP = _run(387, 399)
SLEEP = _run(400, 409) + _run(408, 401)         # breathing, curled up
WAKE = _run(399, 387) + _run(345, 324)
ARRIVE = _run(504, 512)                         # trotting in from far away
LEAVE = _run(24, 42)                            # off into the distance
HELD = 25                                       # dangling, when you pick him up


def sheet_path():
    """The sprite sheet: the first picture in Local Storage\\Rover (None if there's none)."""
    try:
        from claudecore import host
        folder = Path(host.local_storage()) / "Rover"
    except Exception:
        return None
    if not folder.is_dir():
        return None
    pics = sorted(folder.glob("*.png"))
    return pics[0] if pics else None


@lru_cache(maxsize=1)
def _sheet():
    path = sheet_path()
    if path is None:
        return None
    img = QImage(str(path)).convertToFormat(QImage.Format_ARGB32)
    return None if img.isNull() else img


def available():
    return _sheet() is not None


def _clean(img):
    """Clear specks along the top edge that belong to the frame above (a few pixels tall, apart from the dog)."""
    w, h = img.width(), img.height()
    seen = [[False] * w for _ in range(h)]
    for sx in range(w):
        for sy in range(2):
            if seen[sy][sx] or img.pixelColor(sx, sy).alpha() <= 16:
                continue
            todo, blob, low = [(sx, sy)], [], 0
            seen[sy][sx] = True
            while todo:
                x, y = todo.pop()
                blob.append((x, y))
                low = max(low, y)
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and img.pixelColor(nx, ny).alpha() > 16:
                        seen[ny][nx] = True
                        todo.append((nx, ny))
            if low <= 5 and len(blob) < 60:
                for x, y in blob:
                    img.setPixelColor(x, y, QColor(0, 0, 0, 0))
    return img


@lru_cache(maxsize=None)
def _cut(k):
    sheet = _sheet()
    if sheet is None or not 0 <= k < FRAMES:
        return None
    size = sheet.width() / GRID
    r, c = divmod(k, GRID)
    x, y = round(c * size), round(r * size)
    return _clean(sheet.copy(QRect(x, y, CELL, CELL)))


@lru_cache(maxsize=2048)
def frame(k, scale=2, mirrored=False):
    """Frame k as a pixmap, scale times its size, facing right when mirrored. An empty pixmap if there's no sheet."""
    img = _cut(k)
    side = int(CELL * scale)
    if img is None:
        pm = QPixmap(side, side)
        pm.fill(Qt.transparent)
        return pm
    pm = QPixmap.fromImage(img).scaled(side, side, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return pm.transformed(QTransform().scale(-1, 1)) if mirrored else pm


def doggo_icon(size=32):
    """His face for the Start menu and the tray (a paw print if the sheet isn't there)."""
    img = _cut(SIT)
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    if img is not None:
        p.drawImage(QRect(0, 0, size, size), img)
    else:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#E0A21E"))
        s = size / 32
        p.drawEllipse(int(9 * s), int(14 * s), int(14 * s), int(12 * s))
        for x, y in ((5, 8), (11, 4), (18, 4), (24, 8)):
            p.drawEllipse(int(x * s), int(y * s), int(6 * s), int(7 * s))
    p.end()
    return QIcon(pm)
