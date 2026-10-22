"""Personalization (data/display.json): the desktop background (Windows 11's wallpapers from the real PC, your own
pictures, or a colour, with Fill/Fit/Stretch/Tile/Center/Span), the accent colour, the lock screen picture and the
screen saver."""
import json
from pathlib import Path

from PySide6.QtCore import QObject, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QImageReader, QLinearGradient, QPainter, QPixmap, QRadialGradient

from .paths import BACKGROUNDS, DATA, IMAGE_EXTS, host_wallpapers, lock_images, media_wallpapers

MAX_SIDE = 2560                                # wallpapers come in 8K; this is plenty for the screen


def load_image(path, max_side=MAX_SIDE):
    """A picture file as a QPixmap, scaled down on the way in when it is bigger than the screen needs."""
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid() and max(size.width(), size.height()) > max_side:
        scale = max_side / max(size.width(), size.height())
        reader.setScaledSize(QSize(max(1, int(size.width() * scale)), max(1, int(size.height() * scale))))
    image = reader.read()
    return QPixmap.fromImage(image) if not image.isNull() else QPixmap()

DISPLAY_FILE = DATA / "display.json"
POSITIONS = ("Fill", "Fit", "Stretch", "Tile", "Center", "Span")
# Windows 11's accent colours (Settings > Personalization > Colors)
ACCENT_COLORS = [("Default blue", "#0078D4"), ("Yellow gold", "#FFB900"), ("Gold", "#FF8C00"),
                 ("Orange bright", "#F7630C"), ("Orange dark", "#CA5010"), ("Rust", "#DA3B01"),
                 ("Pale rust", "#EF6950"), ("Brick red", "#D13438"), ("Mod red", "#FF4343"), ("Pale red", "#E74856"),
                 ("Red", "#E81123"), ("Rose bright", "#EA005E"), ("Rose", "#C30052"), ("Plum light", "#E3008C"),
                 ("Plum", "#BF0077"), ("Orchid light", "#C239B3"), ("Orchid", "#9A0089"), ("Navy blue", "#0063B1"),
                 ("Purple shadow", "#8E8CD8"), ("Purple shadow dark", "#6B69D6"), ("Iris pastel", "#8764B8"),
                 ("Iris spring", "#744DA9"), ("Violet red light", "#B146C2"), ("Violet red", "#881798"),
                 ("Cool blue bright", "#0099BC"), ("Cool blue", "#2D7D9A"), ("Seafoam", "#00B7C3"),
                 ("Seafoam teal", "#038387"), ("Mint light", "#00B294"), ("Mint dark", "#018574"),
                 ("Turf green", "#00CC6A"), ("Sport green", "#10893E"), ("Gray", "#7A7574"), ("Gray brown", "#5D5A58"),
                 ("Steel blue", "#68768A"), ("Metal blue", "#515C6B"), ("Pale moss", "#567C73"), ("Moss", "#486860"),
                 ("Meadow green", "#498205"), ("Green", "#107C10"), ("Overcast", "#767676"), ("Storm", "#4C4A48"),
                 ("Blue gray", "#69797E"), ("Gray dark", "#4A5459"), ("Liddy green", "#647C64"), ("Sage", "#525E54"),
                 ("Camouflage desert", "#847545"), ("Camouflage", "#7E735F")]
AERO_COLORS = ACCENT_COLORS                   # (the period code's name for the list)


def _default_wallpaper():
    for _label, path in wallpapers():
        if path is not None:
            return str(path)
    return ""


def _dark_wallpaper():
    """The dark Bloom: the collection's official dark-mode Bloom, else Windows 11's own img19, else the light one."""
    walls = [(label, p) for label, p in wallpapers() if p is not None]
    for key in ("dark-mode-blue-stock-official", "dark-mode-stock-official-dark", "img19", "windows-11-dark-3840"):
        for _label, p in walls:
            if key in p.stem.lower():
                return str(p)
    for _label, p in walls:
        if "dark" in p.stem.lower():
            return str(p)
    return _default_wallpaper()


def wallpapers():
    """[(label, path or None)]: solid colour, your own pictures in assets/backgrounds, the Windows 11 Media
    collection on Local Storage, then the ones the real PC ships with."""
    out = [("(Solid color)", None)]
    if BACKGROUNDS.is_dir():
        for path in sorted(BACKGROUNDS.glob("*")):
            if path.suffix.lower() in IMAGE_EXTS:
                out.append((path.stem, path))
    out += media_wallpapers()
    out += host_wallpapers()
    return out


DEFAULTS = {"wallpaper": None, "position": "Fill", "color": "#0067C0", "accent": "#0067C0", "aero_intensity": 1.0,
            "theme": "light", "lock": "", "saver": "(None)", "wait": 10, "resume_welcome": False}


def bloom(width, height):
    """A stand-in for Windows 11's Bloom when there is no wallpaper file: deep blue with a soft light ribbon."""
    pm = QPixmap(max(1, width), max(1, height))
    g = QLinearGradient(0, 0, width, height)
    g.setColorAt(0, QColor("#0A2E73"))
    g.setColorAt(0.5, QColor("#0D47A1"))
    g.setColorAt(1, QColor("#0B3D91"))
    p = QPainter(pm)
    p.fillRect(pm.rect(), g)
    p.setRenderHint(QPainter.Antialiasing)
    for cx, cy, rad, colour, alpha in ((0.5, 0.52, 0.55, "#4FC3F7", 150), (0.42, 0.6, 0.35, "#E1F5FE", 110),
                                       (0.6, 0.45, 0.3, "#81D4FA", 120), (0.5, 0.5, 0.18, "#FFFFFF", 90)):
        rg = QRadialGradient(cx * width, cy * height, rad * max(width, height))
        c = QColor(colour)
        c.setAlpha(alpha)
        rg.setColorAt(0, c)
        c2 = QColor(colour)
        c2.setAlpha(0)
        rg.setColorAt(1, c2)
        p.fillRect(pm.rect(), rg)
    p.end()
    return pm


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
        if self.data.get("wallpaper") is None:
            self.data["wallpaper"] = _default_wallpaper()
        self._cache = {}

    def apply(self, wallpaper, position, color):
        self.data.update({"wallpaper": str(wallpaper) if wallpaper else "", "position": position, "color": color})
        self._save()

    def set_accent(self, color, intensity=None):
        self.data["accent"] = QColor(color).name()
        self._save()

    set_aero = set_accent

    def set_theme(self, mode):
        """Light or dark; the default Bloom follows the mode (the dark Bloom for dark) when it is the wallpaper."""
        old = self.data.get("theme", "light")
        self.data["theme"] = mode
        current = self.data.get("wallpaper") or ""
        defaults = {"light": _default_wallpaper(), "dark": _dark_wallpaper()}
        if current and current == defaults.get(old) and defaults.get(mode):
            self.data["wallpaper"] = defaults[mode]
        self._save()

    def set_lock_image(self, path):
        self.data["lock"] = str(path) if path else ""
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
        """Explorer's 'Set as desktop background' (filled, like Windows 11)."""
        self.apply(path, "Fill", self.data["color"])

    def accent(self):
        return QColor(self.data.get("accent") or DEFAULTS["accent"])

    aero_color = accent

    def aero_intensity(self):
        return 1.0

    def lock_image(self):
        """The lock screen picture's path (your choice, else a scenic one from the collection, else Windows 11's),
        or None."""
        chosen = self.data.get("lock")
        if chosen and Path(chosen).exists():
            return Path(chosen)
        images = lock_images()
        wall = self.data.get("wallpaper") or ""
        others = [p for p in images if str(p) != wall]
        return (others or images)[0] if images else None

    def mica_tint(self):
        """The wallpaper's average colour, which Mica lets through the window frames a little."""
        key = ("tint", self.data["wallpaper"])
        if key not in self._cache:
            img = load_image(self.data["wallpaper"], 64) if self.data["wallpaper"] and \
                Path(self.data["wallpaper"]).exists() else QPixmap()
            if img.isNull():
                tint = QColor(self.data["color"] or "#0067C0")
            else:
                small = img.scaled(8, 8, Qt.IgnoreAspectRatio, Qt.SmoothTransformation).toImage()
                r = g = b = 0
                for y in range(small.height()):
                    for x in range(small.width()):
                        c = small.pixelColor(x, y)
                        r, g, b = r + c.red(), g + c.green(), b + c.blue()
                n = max(1, small.width() * small.height())
                tint = QColor(r // n, g // n, b // n)
            self._cache[key] = tint
        return self._cache[key]

    def render(self, width, height, settings=None):
        """The desktop background at this size (cached)."""
        s = settings or self.data
        key = (width, height, s["wallpaper"], s["position"], s["color"])
        if key in self._cache:
            return self._cache[key]
        img = load_image(s["wallpaper"]) if s["wallpaper"] and Path(s["wallpaper"]).exists() else QPixmap()
        if img.isNull() and not s["wallpaper"] and settings is None and not (BACKGROUNDS.is_dir() and
                                                                               any(BACKGROUNDS.iterdir())):
            pm = bloom(width, height) if s["color"] == DEFAULTS["color"] else QPixmap(max(1, width), max(1, height))
            if s["color"] != DEFAULTS["color"]:
                pm.fill(QColor(s["color"]))
        else:
            pm = QPixmap(max(1, width), max(1, height))
            pm.fill(QColor(s["color"] or "#000000"))
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
                scale = max(sx, sy) if pos in ("Fill", "Span") else min(sx, sy)
                w, h = img.width() * scale, img.height() * scale
                p.drawPixmap(QRectF((width - w) / 2, (height - h) / 2, w, h), img, QRectF(img.rect()))
            p.end()
        if settings is None:
            if len(self._cache) > 8:
                tint = self._cache.get(("tint", self.data["wallpaper"]))
                self._cache.clear()
                if tint is not None:
                    self._cache[("tint", self.data["wallpaper"])] = tint
            self._cache[key] = pm
        return pm


_display = None


def get():
    global _display
    if _display is None:
        _display = Display()
    return _display
