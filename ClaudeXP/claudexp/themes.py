"""Desktop themes: a visual style plus a wallpaper, a sound scheme, mouse pointers and a screen saver.

Built in: Windows XP, Windows Classic, and the four Microsoft Plus! for Windows XP themes (Aquarium, Da Vinci, Nature,
Space). Plus!'s wallpapers are painted here the first time they're needed (into C:\\WINDOWS\\Web\\Wallpaper), its
sound schemes are synthesised into data/theme_sounds, and its pointers are drawn in code.

Themes are also real .theme files (INI text) in C:\\WINDOWS\\Resources\\Themes; Display Properties' 'Save As...'
writes your own, and double-clicking one in Explorer opens it in Display Properties."""
import configparser
import math
import random
import struct
import wave
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QCursor, QFont, QImage, QLinearGradient, QPainter, QPainterPath, QPen,
                           QPixmap, QPolygonF, QRadialGradient)

from . import display, theme
from .paths import DATA

SOUND_DIR = DATA / "theme_sounds"
RATE = 22050

# name -> settings. wallpaper: None = keep, "" = none, "bliss", or a generated Plus! picture's name.
THEMES = {
    "Windows XP": dict(style="luna", scheme="blue", wallpaper="bliss", position="Stretch", color="#004E98",
                       sounds="Windows Default", cursors="Windows Default", saver="Windows XP"),
    "Windows Classic": dict(style="classic", scheme="Windows Classic", wallpaper="", position="Center",
                            color="#3A6EA5", sounds="Windows Default", cursors="Windows Default", saver=None),
    "Plus! Aquarium": dict(style="luna", scheme="blue", wallpaper="Aquarium", position="Stretch", color="#0A3A5A",
                           sounds="Aquarium", cursors="Aquarium", saver="Aquarium"),
    "Plus! Da Vinci": dict(style="luna", scheme="olive", wallpaper="Da Vinci", position="Stretch", color="#6A5030",
                           sounds="Da Vinci", cursors="Da Vinci", saver="Da Vinci"),
    "Plus! Nature": dict(style="luna", scheme="olive", wallpaper="Nature", position="Stretch", color="#3A6A2A",
                         sounds="Nature", cursors="Nature", saver="Nature"),
    "Plus! Space": dict(style="luna", scheme="silver", wallpaper="Space", position="Stretch", color="#000000",
                        sounds="Space", cursors="Space", saver="Space"),
}
FILE_NAMES = {"Windows XP": "Luna.theme", "Windows Classic": "Windows Classic.theme",
              "Plus! Aquarium": "Plus! Aquarium.theme", "Plus! Da Vinci": "Plus! Da Vinci.theme",
              "Plus! Nature": "Plus! Nature.theme", "Plus! Space": "Plus! Space.theme"}
SOUND_SCHEMES = ["Windows Default", "No Sounds", "Aquarium", "Da Vinci", "Nature", "Space"]
CURSOR_SCHEMES = ["Windows Default", "Aquarium", "Da Vinci", "Nature", "Space"]
WALLPAPERS = ("Aquarium", "Da Vinci", "Nature", "Space")


# ---- applying ---------------------------------------------------------------------------------------------------

def themes_dir():
    from .explorer import vfs
    return vfs.DRIVE_C / "WINDOWS" / "Resources" / "Themes"


def wallpaper_dir():
    from .explorer import vfs
    return vfs.DRIVE_C / "WINDOWS" / "Web" / "Wallpaper"


def resolve_wallpaper(value):
    """A theme's wallpaper setting -> a real file path ('' for none)."""
    if value in (None, ""):
        return value
    if value == "bliss":
        return str(display.BLISS_HD)
    if value in WALLPAPERS:
        return str(wallpaper(value))
    return value


def apply(desktop, cfg, name):
    """Switch to a theme: visual style, background, screen saver, sounds and pointers."""
    disp = display.get()
    wall = resolve_wallpaper(cfg.get("wallpaper"))
    if wall is not None:
        disp.apply(wall, cfg.get("position", "Stretch"), cfg.get("color", disp.data["color"]))
    elif cfg.get("color"):
        disp.apply(disp.data["wallpaper"], disp.data["position"], cfg["color"])
    if cfg.get("saver"):
        disp.set_screensaver(saver=cfg["saver"])
    theme.set_state(style=cfg.get("style", "luna"), scheme=cfg.get("scheme") or theme.default_scheme(cfg["style"]),
                    name=name, sounds=cfg.get("sounds", "Windows Default"),
                    cursors=cfg.get("cursors", "Windows Default"))
    restore(desktop)


def restore(desktop):
    """Put the saved sound scheme and pointers back (at log on, and after a theme change)."""
    theme.current()
    if theme.reverted and desktop is not None:          # StyleXP's trial lapsed: save the fallback, and nag
        from PySide6.QtCore import QTimer
        theme.reverted = False
        theme.set_state(style="luna", scheme="blue", name="Modified Theme")

        def nag():
            from .programs import stylexp
            stylexp.nag(desktop)
        QTimer.singleShot(6000, nag)
    s = theme.state()
    apply_sounds(s.get("sounds", "Windows Default"))
    apply_cursors(desktop, s.get("cursors", "Windows Default"))


def with_please_wait(desktop, fn):
    """XP greys the screen and says 'Please wait...' while it switches visual styles."""
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QWidget

    class Wait(QWidget):
        def paintEvent(self, event):
            p = QPainter(self)
            p.fillRect(self.rect(), QColor(60, 60, 60, 120))
            box = QRectF(self.width() / 2 - 110, self.height() / 2 - 32, 220, 64)
            p.fillRect(box.translated(3, 3), QColor(0, 0, 0, 90))
            p.fillRect(box, QColor("#ECE9D8"))
            p.setPen(QPen(QColor("#0054E3"), 2))
            p.drawRect(box)
            p.setPen(QColor("black"))
            f = QFont("Tahoma", 10)
            p.setFont(f)
            p.drawText(box, Qt.AlignCenter, "Please wait...")

    cover = Wait(desktop)
    cover.setGeometry(desktop.rect())
    cover.show()
    cover.raise_()
    QApplication.processEvents()

    def go():
        try:
            fn()
        finally:
            QTimer.singleShot(350, cover.deleteLater)
    QTimer.singleShot(700, go)


# ---- .theme files -------------------------------------------------------------------------------------------------

def _virtual(path):
    from .explorer import vfs
    if not path:
        return ""
    if path == str(display.BLISS_HD):
        return r"%WinDir%\Web\Wallpaper\Bliss.bmp"
    v = vfs.to_virtual(Path(path))
    if v and v.upper().startswith("C:\\WINDOWS"):
        return "%WinDir%" + v[10:]
    return v or path


def _real(value):
    from .explorer import vfs
    if not value:
        return ""
    if value.lower().endswith("bliss.bmp"):
        return "bliss"
    stem = Path(value.replace("\\", "/")).stem
    if stem in WALLPAPERS:
        return stem
    v = value.replace("%WinDir%", "C:\\WINDOWS")
    real = vfs.to_real(v)
    return str(real) if real else value


def write_file(path, name, cfg):
    styles = {"luna": r"%ResourceDir%\Themes\Luna\Luna.msstyles", "classic": "",
              "watercolor": r"%ResourceDir%\Themes\Watercolor\Watercolor.msstyles",
              "aquax": r"%ResourceDir%\Themes\Aqua X\AquaX.msstyles",
              "chromehex": r"%ResourceDir%\Themes\Chrome Hex\ChromeHex.msstyles"}
    color = {"blue": "NormalColor", "olive": "HomeStead", "silver": "Metallic"}.get(cfg.get("scheme"),
                                                                                   cfg.get("scheme", ""))
    wall = cfg.get("wallpaper")
    wall = (r"%WinDir%\Web\Wallpaper\Bliss.bmp" if wall == "bliss" else
            rf"%WinDir%\Web\Wallpaper\{wall}.jpg" if wall in WALLPAPERS else _virtual(wall or ""))
    lines = ["; Windows XP Theme File (ClaudeXP)", "", "[Theme]", f"DisplayName={name}", "",
             "[Control Panel\\Desktop]", f"Wallpaper={wall}",
             f"TileWallpaper={1 if cfg.get('position') == 'Tile' else 0}",
             f"WallpaperStyle={2 if cfg.get('position') == 'Stretch' else 0}", "",
             "[Control Panel\\Colors]", f"Background={cfg.get('color', '#004E98')}", "",
             "[VisualStyles]", f"Path={styles.get(cfg.get('style'), '')}", f"ColorStyle={color}",
             f"Size={'NormalSize' if cfg.get('font', 'normal') == 'normal' else 'LargeFonts'}", "",
             "[Sounds]", f"SchemeName={cfg.get('sounds', 'Windows Default')}", "",
             "[Control Panel\\Cursors]", f"DefaultValue={cfg.get('cursors', 'Windows Default')}", "",
             "[boot]", f"SCRNSAVE.EXE={cfg.get('saver') or ''}", ""]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\r\n".join(lines), encoding="utf-8")


def read_file(path):
    """(name, settings) from a .theme file (None if it can't be read)."""
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.optionxform = str
    try:
        cp.read_string(Path(path).read_text(encoding="utf-8", errors="replace"))
    except (OSError, configparser.Error):
        return None
    get = lambda sec, key, default="": cp.get(sec, key, fallback=default).strip()
    vs = get("VisualStyles", "Path").lower()
    style = ("luna" if "luna" in vs else "watercolor" if "watercolor" in vs else "aquax" if "aqua" in vs
             else "chromehex" if "chrome" in vs else "classic")
    color = get("VisualStyles", "ColorStyle")
    scheme = {"NormalColor": "blue", "HomeStead": "olive", "Metallic": "silver"}.get(color, color)
    if scheme not in dict(theme.schemes(style)):
        scheme = theme.default_scheme(style)
    tile, stretch = get("Control Panel\\Desktop", "TileWallpaper", "0"), get("Control Panel\\Desktop",
                                                                             "WallpaperStyle", "2")
    cfg = dict(style=style, scheme=scheme, wallpaper=_real(get("Control Panel\\Desktop", "Wallpaper")),
               position="Tile" if tile == "1" else "Stretch" if stretch == "2" else "Center",
               color=get("Control Panel\\Colors", "Background", "#004E98") or "#004E98",
               font="normal" if get("VisualStyles", "Size", "NormalSize") == "NormalSize" else "large",
               sounds=get("Sounds", "SchemeName", "Windows Default") or "Windows Default",
               cursors=get("Control Panel\\Cursors", "DefaultValue", "Windows Default") or "Windows Default",
               saver=get("boot", "SCRNSAVE.EXE") or None)
    name = get("Theme", "DisplayName") or Path(path).stem
    return name, cfg


def install_files():
    """The built-in themes as files in C:\\WINDOWS\\Resources\\Themes (written once)."""
    folder = themes_dir()
    for name, cfg in THEMES.items():
        f = folder / FILE_NAMES[name]
        if not f.exists():
            try:
                write_file(f, name, cfg)
            except OSError:
                pass


def current_settings():
    """The settings in effect now, as a theme (for 'Save As...')."""
    s, d = theme.state(), display.get().data
    return dict(style=s["style"], scheme=s["scheme"], font=s.get("font", "normal"), wallpaper=d.get("wallpaper", ""),
                position=d.get("position", "Stretch"), color=d.get("color", "#004E98"),
                sounds=s.get("sounds", "Windows Default"), cursors=s.get("cursors", "Windows Default"),
                saver=d.get("saver"))


# ---- Plus! wallpapers ---------------------------------------------------------------------------------------------

def wallpaper(name):
    """C:\\WINDOWS\\Web\\Wallpaper\\<name>.jpg, painted the first time it's wanted."""
    path = wallpaper_dir() / f"{name}.jpg"
    if not path.exists():
        img = QImage(1024, 768, QImage.Format_RGB32)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        {"Aquarium": _paint_aquarium, "Da Vinci": _paint_davinci, "Nature": _paint_nature,
         "Space": _paint_space}[name](p, 1024, 768, random.Random(name))
        p.end()
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(path), "JPG", 92)
    return path


def _fish(p, x, y, size, body, stripe, facing=1):
    p.save()
    p.translate(x, y)
    p.scale(facing, 1)
    p.setPen(QPen(QColor(body).darker(150), 1.2))
    tail = QPolygonF([QPointF(-size * 0.9, 0), QPointF(-size * 1.5, -size * 0.45), QPointF(-size * 1.4, size * 0.45)])
    p.setBrush(QColor(body).darker(115))
    p.drawPolygon(tail)
    g = QLinearGradient(0, -size * 0.5, 0, size * 0.5)
    g.setColorAt(0, QColor(body).lighter(130))
    g.setColorAt(1, QColor(body).darker(120))
    p.setBrush(g)
    p.drawEllipse(QRectF(-size, -size * 0.5, size * 2, size))
    p.setPen(QPen(QColor(stripe), size * 0.16))
    for sx in (-0.3, 0.25):
        p.drawLine(QPointF(size * sx, -size * 0.42), QPointF(size * sx, size * 0.42))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("white"))
    p.drawEllipse(QPointF(size * 0.6, -size * 0.1), size * 0.16, size * 0.16)
    p.setBrush(QColor("black"))
    p.drawEllipse(QPointF(size * 0.64, -size * 0.1), size * 0.08, size * 0.08)
    p.restore()


def _paint_aquarium(p, w, h, rnd):
    g = QLinearGradient(0, 0, 0, h)
    for at, c in ((0, "#3FB4D8"), (0.35, "#167AA8"), (0.8, "#0A4A72"), (1, "#06324E")):
        g.setColorAt(at, QColor(c))
    p.fillRect(0, 0, w, h, g)
    for i in range(7):                                                  # light shafts
        x = rnd.uniform(-100, w)
        shaft = QPolygonF([QPointF(x, 0), QPointF(x + 60, 0), QPointF(x + 260, h * 0.8), QPointF(x + 120, h * 0.8)])
        sg = QLinearGradient(0, 0, 0, h * 0.8)
        sg.setColorAt(0, QColor(255, 255, 255, 50))
        sg.setColorAt(1, QColor(255, 255, 255, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(sg)
        p.drawPolygon(shaft)
    sand = QPainterPath()
    sand.moveTo(0, h)
    sand.lineTo(0, h * 0.86)
    for x in range(0, w + 64, 64):
        sand.quadTo(x + 32, h * (0.84 + rnd.uniform(-0.02, 0.02)), x + 64, h * 0.86)
    sand.lineTo(w, h)
    sg = QLinearGradient(0, h * 0.82, 0, h)
    sg.setColorAt(0, QColor("#E8D29A"))
    sg.setColorAt(1, QColor("#A88A50"))
    p.fillPath(sand, sg)
    for i in range(16):                                                 # sea grass
        x = rnd.uniform(0, w)
        top = h * rnd.uniform(0.45, 0.72)
        path = QPainterPath()
        path.moveTo(x, h * 0.9)
        path.cubicTo(x - 40, h * 0.8, x + 40, (h * 0.9 + top) / 2, x + rnd.uniform(-30, 30), top)
        p.setPen(QPen(QColor.fromHsv(rnd.randint(90, 140), 200, rnd.randint(110, 190)), rnd.uniform(5, 10),
                      Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
    for i in range(5):                                                  # coral
        x, base = rnd.uniform(40, w - 40), h * 0.9
        p.setPen(QPen(QColor.fromHsv(rnd.choice([0, 15, 330, 300]), 170, 230), 9, Qt.SolidLine, Qt.RoundCap))
        for b in range(5):
            a = math.radians(-90 + rnd.uniform(-45, 45))
            ln = rnd.uniform(40, 90)
            p.drawLine(QPointF(x, base), QPointF(x + math.cos(a) * ln, base + math.sin(a) * ln))
    for i in range(9):
        _fish(p, rnd.uniform(60, w - 60), rnd.uniform(h * 0.15, h * 0.75), rnd.uniform(18, 34),
              rnd.choice(["#FF7A1A", "#FFD21A", "#3AA0FF", "#FF4A8A", "#9A5AFF"]), "#FFFFFF", rnd.choice([1, -1]))
    p.setBrush(Qt.NoBrush)
    for i in range(60):                                                 # bubbles
        r = rnd.uniform(2, 9)
        p.setPen(QPen(QColor(255, 255, 255, 150), 1.4))
        p.drawEllipse(QPointF(rnd.uniform(0, w), rnd.uniform(0, h * 0.85)), r, r)


def _paint_space(p, w, h, rnd):
    g = QLinearGradient(0, 0, w, h)
    g.setColorAt(0, QColor("#02020A"))
    g.setColorAt(1, QColor("#0A0A24"))
    p.fillRect(0, 0, w, h, g)
    for cx, cy, r, col in ((w * 0.3, h * 0.35, 420, QColor(140, 40, 160, 70)),
                           (w * 0.55, h * 0.5, 360, QColor(30, 120, 170, 60)),
                           (w * 0.2, h * 0.7, 260, QColor(200, 70, 60, 45))):
        rg = QRadialGradient(cx, cy, r)
        rg.setColorAt(0, col)
        rg.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(0, 0, w, h, rg)
    for i in range(900):
        b = rnd.randint(110, 255)
        s = rnd.choice([0.8, 1, 1, 1.4, 2])
        p.fillRect(QRectF(rnd.uniform(0, w), rnd.uniform(0, h), s, s), QColor(b, b, min(255, b + 20)))
    planet = QRectF(w * 0.62, h * 0.42, 300, 300)
    pg = QRadialGradient(planet.center() - QPointF(70, 70), 260)
    pg.setColorAt(0, QColor("#F2C88A"))
    pg.setColorAt(0.6, QColor("#B0603A"))
    pg.setColorAt(1, QColor("#2A1008"))
    p.setPen(Qt.NoPen)
    p.setBrush(pg)
    p.drawEllipse(planet)
    p.setPen(QPen(QColor(230, 200, 160, 160), 7))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(planet.center(), 250, 46)
    p.setPen(QPen(QColor(230, 200, 160, 70), 16))
    p.drawEllipse(planet.center(), 220, 38)
    moon = QRectF(w * 0.18, h * 0.16, 70, 70)
    mg = QRadialGradient(moon.center() - QPointF(15, 15), 60)
    mg.setColorAt(0, QColor("#E8E8F0"))
    mg.setColorAt(1, QColor("#3A3A48"))
    p.setPen(Qt.NoPen)
    p.setBrush(mg)
    p.drawEllipse(moon)


def _paint_nature(p, w, h, rnd):
    g = QLinearGradient(0, 0, 0, h * 0.6)
    g.setColorAt(0, QColor("#6AA8E8"))
    g.setColorAt(1, QColor("#D8ECF8"))
    p.fillRect(0, 0, w, h, g)
    sun = QRadialGradient(w * 0.78, h * 0.18, 220)
    sun.setColorAt(0, QColor(255, 250, 210, 255))
    sun.setColorAt(0.15, QColor(255, 240, 170, 220))
    sun.setColorAt(1, QColor(255, 240, 170, 0))
    p.fillRect(0, 0, w, h, sun)
    for i, (base, col) in enumerate(((0.55, "#7FAE5A"), (0.65, "#5E9440"), (0.76, "#457A2C"), (0.88, "#2E5E1C"))):
        hill = QPainterPath()
        hill.moveTo(0, h)
        y0 = h * base
        hill.lineTo(0, y0)
        for x in range(0, w + 200, 200):
            hill.quadTo(x + 100, y0 - rnd.uniform(20, 70), x + 200, y0 + rnd.uniform(-15, 15))
        hill.lineTo(w, h)
        p.fillPath(hill, QColor(col))
    for i in range(7):                                                  # trees
        x, y = rnd.uniform(0, w), h * rnd.uniform(0.6, 0.72)
        s = rnd.uniform(0.6, 1.2)
        p.fillRect(QRectF(x - 4 * s, y, 8 * s, 40 * s), QColor("#5A3A1A"))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2E6A22"))
        for dx, dy, r in ((0, -10, 28), (-18, 4, 20), (18, 4, 20), (0, -32, 20)):
            p.drawEllipse(QPointF(x + dx * s, y + dy * s), r * s, r * s)
    for i in range(160):                                                # flowers
        x, y = rnd.uniform(0, w), rnd.uniform(h * 0.86, h)
        p.setBrush(QColor.fromHsv(rnd.choice([0, 50, 300, 40, 60]), 170, 255))
        p.drawEllipse(QPointF(x, y), 3.5, 3.5)
    for i in range(14):                                                 # falling leaves
        x, y, a = rnd.uniform(0, w), rnd.uniform(0, h * 0.6), rnd.uniform(0, 360)
        p.save()
        p.translate(x, y)
        p.rotate(a)
        leaf = QPainterPath()
        leaf.moveTo(-12, 0)
        leaf.quadTo(0, -8, 12, 0)
        leaf.quadTo(0, 8, -12, 0)
        p.fillPath(leaf, QColor.fromHsv(rnd.randint(20, 60), 200, 220))
        p.restore()


def _paint_davinci(p, w, h, rnd):
    g = QRadialGradient(w / 2, h / 2, w * 0.7)
    g.setColorAt(0, QColor("#F2E2BC"))
    g.setColorAt(1, QColor("#C8A870"))
    p.fillRect(0, 0, w, h, g)
    for i in range(40):                                                 # stains
        rg = QRadialGradient(rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(30, 120))
        rg.setColorAt(0, QColor(140, 100, 50, 30))
        rg.setColorAt(1, QColor(140, 100, 50, 0))
        p.fillRect(0, 0, w, h, rg)
    ink = QColor(90, 55, 25, 200)
    p.setPen(QPen(ink, 2))
    p.setBrush(Qt.NoBrush)
    cx, cy, r = w * 0.38, h * 0.48, 230
    p.drawEllipse(QPointF(cx, cy), r, r)                                # the Vitruvian circle and square
    side = r * 1.62
    p.drawRect(QRectF(cx - side / 2, cy + r - side, side, side))
    p.setPen(QPen(ink, 3))
    head = QPointF(cx, cy - 150)
    p.drawEllipse(head, 26, 32)
    body = [(QPointF(cx, cy - 118), QPointF(cx, cy + 40)),
            (QPointF(cx, cy - 90), QPointF(cx - 170, cy - 95)), (QPointF(cx, cy - 90), QPointF(cx + 170, cy - 95)),
            (QPointF(cx, cy - 95), QPointF(cx - 150, cy - 170)), (QPointF(cx, cy - 95), QPointF(cx + 150, cy - 170)),
            (QPointF(cx, cy + 40), QPointF(cx - 40, cy + 228)), (QPointF(cx, cy + 40), QPointF(cx + 40, cy + 228)),
            (QPointF(cx, cy + 40), QPointF(cx - 110, cy + 200)), (QPointF(cx, cy + 40), QPointF(cx + 110, cy + 200))]
    for a, b in body:
        p.drawLine(a, b)
    p.setPen(QPen(QColor(90, 55, 25, 150), 1.4))                        # mirror writing
    for row in range(14):
        x, y = w * 0.68, h * 0.12 + row * 22
        path = QPainterPath()
        path.moveTo(x + 260, y)
        for k in range(36):
            path.lineTo(x + 260 - k * 7, y + rnd.uniform(-5, 5))
        p.drawPath(path)
    gear = QPointF(w * 0.8, h * 0.78)                                   # a gear sketch
    p.setPen(QPen(ink, 2))
    p.drawEllipse(gear, 60, 60)
    p.drawEllipse(gear, 18, 18)
    for k in range(16):
        a = k * math.pi / 8
        p.drawLine(gear + QPointF(math.cos(a) * 60, math.sin(a) * 60), gear + QPointF(math.cos(a) * 76,
                                                                                     math.sin(a) * 76))
    wing = QPainterPath()                                               # an ornithopter wing
    wing.moveTo(w * 0.62, h * 0.62)
    for k in range(5):
        wing.quadTo(w * (0.66 + k * 0.05), h * (0.5 - k * 0.02), w * (0.66 + k * 0.05), h * 0.64)
    p.drawPath(wing)


# ---- Plus! sound schemes ------------------------------------------------------------------------------------------

THEMED_EVENTS = ("default", "error", "exclamation", "info", "ding", "menu", "minimize", "restore", "logon",
                 "logoff", "notify", "balloon", "critical", "recycle")


def _env(n, attack=0.005, release=0.6):
    a, r = max(1, int(attack * RATE)), max(1, int(release * n))
    return [min(1.0, i / a) * (1.0 if i < n - r else max(0.0, (n - i) / r)) for i in range(n)]


def _chirp(f0, f1, dur, amp=0.5, shape="sine", decay=6.0):
    n = int(dur * RATE)
    out, ph = [], 0.0
    for i in range(n):
        t = i / n
        f = f0 + (f1 - f0) * t
        ph += 2 * math.pi * f / RATE
        v = math.sin(ph) if shape == "sine" else (0.6 * math.sin(ph) + 0.3 * math.sin(2 * ph) + 0.2 * math.sin(3 * ph))
        out.append(v * amp * math.exp(-decay * t) * min(1.0, i / 60))
    return out


def _pluck(freq, dur, amp=0.6, rnd=None):
    """Karplus-Strong: a plucked string (Da Vinci's lute)."""
    rnd = rnd or random.Random(int(freq))
    period = max(2, int(RATE / freq))
    buf = [rnd.uniform(-1, 1) for _ in range(period)]
    out = []
    for i in range(int(dur * RATE)):
        v = buf[i % period]
        buf[i % period] = 0.5 * (v + buf[(i + 1) % period]) * 0.996
        out.append(v * amp)
    return out


def _mix(parts, total=None):
    """parts: [(start seconds, samples)] -> one track."""
    end = max(int(s * RATE) + len(x) for s, x in parts)
    track = [0.0] * (total or end)
    for s, x in parts:
        o = int(s * RATE)
        for i, v in enumerate(x):
            if o + i < len(track):
                track[o + i] += v
    peak = max(1e-6, max(abs(v) for v in track))
    return [v / max(1.0, peak / 0.9) for v in track]


def _scheme_sound(scheme, event):
    rnd = random.Random(f"{scheme}:{event}")
    up = event in ("restore", "logon", "info", "notify", "balloon")
    down = event in ("minimize", "logoff", "recycle")
    bad = event in ("error", "critical", "exclamation")
    count = 6 if event in ("logon", "logoff") else 1 if event == "menu" else 3
    if scheme == "Aquarium":
        parts = []
        for k in range(count + (3 if bad else 0)):
            f0 = rnd.uniform(350, 700) * (0.6 if bad else 1)
            if up:
                f0 *= 1 + k * 0.15
            if down:
                f0 *= 1.6 - k * 0.15
            parts.append((k * rnd.uniform(0.05, 0.09), _chirp(f0, f0 * 2.2, rnd.uniform(0.05, 0.09), 0.5, decay=4)))
        if bad:
            parts.append((0, _chirp(220, 140, 0.35, 0.4, "rich", decay=3)))
        return _mix(parts)
    if scheme == "Space":
        if bad:
            return _mix([(0, _chirp(900, 120, 0.45, 0.5, "rich", 2)), (0.1, _chirp(600, 100, 0.4, 0.3, "rich", 2))])
        if event == "menu":
            return _chirp(1600, 1900, 0.06, 0.35, decay=3)
        if up or down:
            seq = [523, 659, 784, 1047] if up else [1047, 784, 659, 523]
            seq = seq * (2 if event in ("logon", "logoff") else 1)
            return _mix([(k * 0.09, _chirp(f, f * 1.01, 0.18, 0.4, "rich", 4)) for k, f in enumerate(seq)])
        return _mix([(0, _chirp(1800, 300, 0.28, 0.45, "rich", 3)), (0.12, _chirp(1200, 250, 0.2, 0.25, "rich", 4))])
    if scheme == "Nature":
        if bad:                                                         # a woodpecker
            return _mix([(k * 0.07, [rnd.uniform(-0.7, 0.7) * math.exp(-i / 180) for i in range(900)])
                         for k in range(5)])
        if event == "menu":                                             # a drop of water
            return _chirp(1400, 700, 0.07, 0.5, decay=5)
        parts = []
        for k in range(count + 1):
            f0 = rnd.uniform(2200, 3200) * (1.15 if up else 0.9 if down else 1)
            parts.append((k * 0.11, _chirp(f0, f0 * rnd.uniform(1.2, 1.5), 0.07, 0.35, decay=3)))
        return _mix(parts)
    # Da Vinci: a lute
    scale = [293.7, 329.6, 349.2, 392.0, 440.0, 523.3, 587.3]
    if bad:
        notes = [220.0, 261.6]
    elif event == "menu":
        notes = [587.3]
    elif up:
        notes = scale[:count + 1]
    elif down:
        notes = list(reversed(scale[:count + 1]))
    else:
        notes = [440.0, 587.3]
    return _mix([(k * 0.12, _pluck(f, 0.9, 0.55, rnd)) for k, f in enumerate(notes)])


def sound_file(scheme, event):
    path = SOUND_DIR / scheme / f"{event}.wav"
    if not path.exists():
        samples = _scheme_sound(scheme, event)
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32000)) for v in samples))
    return path


def apply_sounds(scheme):
    from . import sound
    if scheme in ("Aquarium", "Da Vinci", "Nature", "Space"):
        sound.set_scheme({ev: sound_file(scheme, ev) for ev in THEMED_EVENTS})
    elif scheme == "No Sounds":
        sound.set_scheme({ev: None for ev in sound.EVENTS if ev not in ("startup", "shutdown")})
    else:
        sound.set_scheme(None)


# ---- Plus! pointers ----------------------------------------------------------------------------------------------

def cursor_pixmap(scheme):
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    if scheme == "Aquarium":                                            # a fish nosing at the hot spot
        p.translate(14, 14)
        p.rotate(225)
        _fish(p, 0, 0, 9, "#FF7A1A", "#FFFFFF", -1)
    elif scheme == "Space":                                             # a rocket
        p.translate(1, 1)
        body = QPainterPath()
        body.moveTo(0, 0)
        body.cubicTo(10, 2, 18, 10, 20, 20)
        body.lineTo(14, 20)
        body.lineTo(0, 6)
        body.closeSubpath()
        p.setPen(QPen(QColor("#303040"), 1))
        p.setBrush(QColor("#E8E8F0"))
        p.drawPath(body)
        p.setBrush(QColor("#D02020"))
        p.drawPolygon(QPolygonF([QPointF(14, 20), QPointF(20, 20), QPointF(24, 27), QPointF(17, 25)]))
        p.setBrush(QColor("#FFB020"))
        p.setPen(Qt.NoPen)
        p.drawPolygon(QPolygonF([QPointF(16, 21), QPointF(21, 21), QPointF(29, 30)]))
        p.setBrush(QColor("#3A8AE0"))
        p.drawEllipse(QPointF(9, 8), 2.5, 2.5)
    elif scheme == "Nature":                                            # a leaf
        leaf = QPainterPath()
        leaf.moveTo(0, 0)
        leaf.cubicTo(20, 2, 26, 14, 22, 24)
        leaf.cubicTo(12, 24, 2, 18, 0, 0)
        p.setPen(QPen(QColor("#2A5A10"), 1))
        g = QLinearGradient(0, 0, 22, 24)
        g.setColorAt(0, QColor("#B8E070"))
        g.setColorAt(1, QColor("#4A9A20"))
        p.setBrush(g)
        p.drawPath(leaf)
        p.drawLine(QPointF(0, 0), QPointF(26, 28))
    elif scheme == "Da Vinci":                                          # a quill
        feather = QPainterPath()
        feather.moveTo(0, 0)
        feather.cubicTo(6, 4, 22, 14, 30, 30)
        feather.cubicTo(18, 26, 6, 12, 0, 0)
        p.setPen(QPen(QColor("#6A4A20"), 1))
        p.setBrush(QColor("#F2E6C8"))
        p.drawPath(feather)
        p.setPen(QPen(QColor("#3A2410"), 1.5))
        p.drawLine(QPointF(0, 0), QPointF(26, 27))
    p.end()
    return pm


def apply_cursors(desktop, scheme):
    if desktop is None:
        return
    if scheme in ("Aquarium", "Space", "Nature", "Da Vinci"):
        desktop.setCursor(QCursor(cursor_pixmap(scheme), 0, 0))
    else:
        desktop.unsetCursor()
