"""Personalization (data/display.json): the desktop background (a Windows 7 wallpaper, or your own picture, with
Fill/Fit/Stretch/Tile/Center), the window colour Aero tints the glass with, and the screen saver."""
import json
from pathlib import Path

from PySide6.QtCore import QObject, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap

from .paths import BACKGROUNDS, DATA

DISPLAY_FILE = DATA / "display.json"
POSITIONS = ("Fill", "Fit", "Stretch", "Tile", "Center")
# Windows 7's window colours (Personalization > Window Color)
AERO_COLORS = [("Sky", "#6BA4D9"), ("Twilight", "#4A6FA5"), ("Sea", "#3D8FA6"), ("Leaf", "#7FAE4B"),
               ("Lime", "#A8C33A"), ("Sun", "#E0B64C"), ("Pumpkin", "#E08A3C"), ("Ruby", "#C1443F"),
               ("Fuchsia", "#C94F8C"), ("Blush", "#D08AA8"), ("Violet", "#8B6FBE"), ("Lavender", "#9A8DC3"),
               ("Taupe", "#8C8277"), ("Chocolate", "#6E4F3A"), ("Slate", "#4E5A66"), ("Frost", "#A8BBCC")]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
DEFAULTS = {"wallpaper": str(BACKGROUNDS / "Harmony.jpg"), "position": "Fill", "color": "#000000",
            "aero": "#6BA4D9", "aero_intensity": 0.75, "saver": "Claude Entertainment System", "wait": 10, "resume_welcome": False}


def _captured():
    """The captured desktop's background (assets/desktop_layout.json), over the defaults: a format brings it back."""
    from .paths import ROOT, default_layout
    shown = {k: v for k, v in (default_layout().get("display") or {}).items() if k in DEFAULTS}
    if shown.get("wallpaper") and not Path(shown["wallpaper"]).is_absolute():
        shown["wallpaper"] = str(ROOT / shown["wallpaper"])
    return shown


DEFAULTS.update(_captured())


def wallpapers():
    """[(label, path or None)]: solid colour, then the Windows 7 wallpapers."""
    out = [("(Solid color)", None)]
    for path in sorted(BACKGROUNDS.glob("*")):
        if path.suffix.lower() in IMAGE_EXTS:
            out.append((path.stem, path))
    return out


class Display(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.data = dict(DEFAULTS)
        try:
            with open(DISPLAY_FILE, encoding="utf-8") as f:
                self.data.update(json.load(f))
        except (OSError, ValueError):
            pass
        self._cache = {}

    def apply(self, wallpaper, position, color):
        self.data.update({"wallpaper": str(wallpaper) if wallpaper else "", "position": position, "color": color})
        self._save()

    def set_aero(self, color, intensity=None):
        self.data["aero"] = QColor(color).name()
        if intensity is not None:
            self.data["aero_intensity"] = max(0.2, min(1.0, float(intensity)))
        self._save()

    def set_screensaver(self, **values):
        self.data.update(values)
        self._save()

    def _save(self):
        DISPLAY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DISPLAY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
        self._cache.clear()
        self.changed.emit()

    def set_wallpaper(self, path):
        """Explorer's 'Set as desktop background' (filled, like Windows 7)."""
        self.apply(path, "Fill", self.data["color"])

    def aero_color(self):
        return QColor(self.data.get("aero") or DEFAULTS["aero"])

    def aero_intensity(self):
        return float(self.data.get("aero_intensity", DEFAULTS["aero_intensity"]))

    def render(self, width, height, settings=None):
        """The desktop background at this size (cached)."""
        s = settings or self.data
        key = (width, height, s["wallpaper"], s["position"], s["color"])
        if key in self._cache:
            return self._cache[key]
        pm = QPixmap(max(1, width), max(1, height))
        pm.fill(QColor(s["color"] or "#000000"))
        img = QPixmap(s["wallpaper"]) if s["wallpaper"] and Path(s["wallpaper"]).exists() else QPixmap()
        if not img.isNull():
            p = QPainter(pm)
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            pos = s["position"]
            if pos == "Stretch":
                p.drawPixmap(QRectF(0, 0, width, height), img, QRectF(img.rect()))
            elif pos == "Tile":
                p.drawTiledPixmap(0, 0, width, height, img)
            elif pos == "Center":
                p.drawPixmap((width - img.width()) // 2, (height - img.height()) // 2, img)
            else:
                sx, sy = width / img.width(), height / img.height()
                scale = max(sx, sy) if pos == "Fill" else min(sx, sy)
                w, h = img.width() * scale, img.height() * scale
                p.drawPixmap(QRectF((width - w) / 2, (height - h) / 2, w, h), img, QRectF(img.rect()))
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
