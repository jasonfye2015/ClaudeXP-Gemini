"""Neko's sprites: the classic 32x32 frames (assets/images/Neko/neko_sheet.png).

The sheet is the one from desktopPet's Neko (github.com/Adrianotiger/desktopPet, MIT licence, by Adriano Petrucci),
whose sprites come from webneko.net - the same 1-bit cat as the original Neko for the NEC PC-9801 and Mac.
4 columns x 9 rows of 32x32 cells:
  0 sit   1 lick   2-3 scratch   4 yawn   5-6 sleep   7 awake
  8-9 run up   10-11 down   12-13 left   14-15 right   16-17 up-left   18-19 up-right   20-21 down-left   22-23 down-right
  24-25 scratch the top wall   26-27 scratch the bottom wall (also: dangling when picked up)
  28-29 scratch the left wall   30-31 scratch the right wall   33-35 the mouse
"""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPen, QPixmap

from ..paths import IMAGES

SHEET = IMAGES / "Neko" / "neko_sheet.png"
CELL = 32
COLS = 4

SIT, LICK, SCRATCH, YAWN, SLEEP, AWAKE = 0, 1, (2, 3), 4, (5, 6), 7
RUN = {"up": (8, 9), "down": (10, 11), "left": (12, 13), "right": (14, 15),
       "ul": (16, 17), "ur": (18, 19), "dl": (20, 21), "dr": (22, 23)}
WALL = {"up": (24, 25), "down": (26, 27), "left": (28, 29), "right": (30, 31)}
DANGLE = (26, 27)

# fur colours: the sheet's white fill becomes this (the black outline stays)
PALETTES = {
    "white": {"name": "Classic White", "fur": "#FFFFFF"},
    "cream": {"name": "Cream", "fur": "#F8E6C0"},
    "ginger": {"name": "Ginger", "fur": "#F6B060"},
    "grey": {"name": "Grey", "fur": "#B8BCC4"},
    "siamese": {"name": "Siamese", "fur": "#E8D8C0"},
    "pink": {"name": "Bubblegum", "fur": "#FFC4DA"},
}

_sheet = None
_cache = {}


def _load_sheet():
    global _sheet
    if _sheet is None:
        img = QImage(str(SHEET)).convertToFormat(QImage.Format_ARGB32)
        for y in range(img.height()):                 # magenta is the sheet's 'transparent' colour
            for x in range(img.width()):
                c = img.pixelColor(x, y)
                if c.red() > 240 and c.green() < 16 and c.blue() > 240:
                    img.setPixelColor(x, y, QColor(0, 0, 0, 0))
        _sheet = img
    return _sheet


def frame(index, palette="white", scale=1):
    """One 32x32 cell as a QPixmap (scaled by an integer, kept pixel-sharp)."""
    key = (index, palette, scale)
    if key not in _cache:
        sheet = _load_sheet()
        cell = sheet.copy((index % COLS) * CELL, (index // COLS) * CELL, CELL, CELL)
        fur = QColor(PALETTES.get(palette, PALETTES["white"])["fur"])
        if fur != QColor("#FFFFFF"):
            for y in range(CELL):
                for x in range(CELL):
                    c = cell.pixelColor(x, y)
                    if c.alpha() > 0 and c.red() > 200 and c.green() > 200 and c.blue() > 200:
                        cell.setPixelColor(x, y, fur)
        if scale != 1:
            cell = cell.scaled(CELL * scale, CELL * scale, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        _cache[key] = QPixmap.fromImage(cell)
    return _cache[key]


def neko_icon(size=32):
    """Program / Start menu icon: Neko sitting."""
    pm = frame(SIT)
    return QIcon(pm.scaled(size, size, Qt.KeepAspectRatio, Qt.FastTransformation) if size != CELL else pm)


def paw_icon(size=32):
    """A small paw print for Neko's notification-area icon."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32.0
    p.setPen(QPen(QColor("#5A3545"), 1.2 * s))
    p.setBrush(QColor("#F59AB5"))
    p.drawEllipse(QRectF(7 * s, 16 * s, 18 * s, 13 * s))
    for x, y, w, h in ((4, 8, 7, 9), (11, 3, 7, 10), (20, 3, 7, 10), (25, 8, 6, 9)):
        p.drawEllipse(QRectF(x * s, y * s, w * s, h * s))
    p.end()
    return QIcon(pm)
