"""Filesystem locations and cached image loading."""
from functools import lru_cache
from pathlib import Path

from PySide6.QtGui import QPixmap

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "assets" / "images"
SOUNDS = ROOT / "assets" / "sounds"
DATA = ROOT / "data"


@lru_cache(maxsize=None)
def pixmap(name):
    """Load an image from assets/images (cached). Returns a null pixmap if missing."""
    return QPixmap(str(IMAGES / name))


def find_image(stem):
    """Return the first assets/images/<stem>.* file, or None."""
    for path in sorted(IMAGES.glob(stem + ".*")):
        return path
    return None
