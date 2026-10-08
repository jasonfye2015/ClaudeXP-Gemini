"""Desktop background settings (data/display.json): wallpaper, position and color."""
import json
from pathlib import Path

from PySide6.QtCore import QObject, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap

from .paths import DATA, IMAGES, ROOT

DISPLAY_FILE = DATA / "display.json"
WALLPAPER_DIR = ROOT / "assets" / "backgrounds"
BLISS_HD = IMAGES / "windows-xp-bliss-4k-lu-1024x768.jpg"   # a sharper Bliss than the 800x600 one
POSITIONS = ("Center", "Tile", "Stretch")
COLORS = [("Blue (default)", "#004E98"), ("Black", "#000000"), ("Dark teal", "#3A6EA5"), ("Teal", "#008080"),
          ("Olive", "#808000"), ("Maroon", "#800000"), ("Purple", "#5A2D82"), ("Gray", "#808080"),
          ("Silver", "#C0C0C0"), ("Forest green", "#2E6B2E"), ("Navy", "#000080"), ("White", "#FFFFFF")]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}


def wallpapers():
    """[(label, path or None)]: (None), then the Windows XP wallpapers."""
    out = [("(None)", None)]
    for path in sorted(WALLPAPER_DIR.glob("*")):
        if path.suffix.lower() not in IMAGE_EXTS:
            continue
        label = path.stem.replace("_", " ")
        if path.stem.lower() == "bliss" and BLISS_HD.exists():
            path = BLISS_HD
        out.append((label, path))
    return out


class Display(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.data = {"wallpaper": str(BLISS_HD), "position": "Stretch", "color": "#004E98"}
        try:
            with open(DISPLAY_FILE, encoding="utf-8") as f:
                self.data.update(json.load(f))
        except (OSError, ValueError):
            pass
        self._cache = {}

    def apply(self, wallpaper, position, color):
        self.data.update({"wallpaper": str(wallpaper) if wallpaper else "", "position": position, "color": color})
        self._save()

    def set_screensaver(self, **values):
        """saver, wait (minutes), resume_welcome, marquee."""
        self.data.update(values)
        self._save()

    def _save(self):
        DISPLAY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DISPLAY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
        self._cache.clear()
        self.changed.emit()

    def set_wallpaper(self, path):
        """Explorer's 'Set as Desktop Background' (stretched, like XP)."""
        self.apply(path, "Stretch", self.data["color"])

    def render(self, width, height, settings=None):
        """The desktop background at this size (cached), optionally for preview settings."""
        s = settings or self.data
        key = (width, height, s["wallpaper"], s["position"], s["color"])
        if key in self._cache:
            return self._cache[key]
        pm = QPixmap(max(1, width), max(1, height))
        pm.fill(QColor(s["color"]))
        img = QPixmap(s["wallpaper"]) if s["wallpaper"] and Path(s["wallpaper"]).exists() else QPixmap()
        if not img.isNull():
            p = QPainter(pm)
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            if s["position"] == "Stretch":
                p.drawPixmap(QRectF(0, 0, width, height), img, QRectF(img.rect()))
            elif s["position"] == "Tile":
                p.drawTiledPixmap(0, 0, width, height, img)
            else:
                p.drawPixmap((width - img.width()) // 2, (height - img.height()) // 2, img)
            p.end()
        if settings is None:
            if len(self._cache) > 8:
                self._cache.clear()
            self._cache[key] = pm
        return pm


_display = None


def get():
    global _display
    if _display is None:
        _display = Display()
    return _display
