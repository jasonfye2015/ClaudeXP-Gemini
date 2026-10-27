"""Screen savers: Super Claude Bros (the Super Mario Bros. clock, the default; supercb.py), Super Claude Bros. 3 (the same game
in Super Mario Bros. 3's clothes; smb3cb.py), The Legend of Claude (the Legend of Zelda clock; zeldacb.py), Zelda II: The Adventure of Claude (its sequel's side-on
clock; zelda2cb.py), Windows XP, Starfield, Mystify, Beziers, 3D Pipes, Marquee, My Pictures Slideshow, Blank,
Copilot Matrix Rain (falling green code), and After Dark's Flying Toasters (a looped video clip).

Each saver is a QWidget that animates at any size (full screen, or the little monitor in Display
Properties). The manager watches for idle time and covers the whole PC screen with the chosen saver;
moving the mouse or pressing a key wakes it (optionally to the Welcome screen).
"""
import math
import random
import time

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetrics, QImage, QLinearGradient, QPainter, QPainterPath, QPen,
                           QPixmap, QPolygonF, QRadialGradient)
from PySide6.QtWidgets import QWidget

from . import display
from .paths import ROOT, pixmap

DEFAULTS = {"saver": "Super Claude Bros", "wait": 10, "resume_welcome": False, "marquee": "Windows XP"}


def settings():
    data = display.get().data
    return {k: data.get(k, v) for k, v in DEFAULTS.items()}


class Saver(QWidget):
    FPS = 30

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(int(1000 / self.FPS))
        self.t = 0.0

    def _tick(self):
        self.t += 1 / self.FPS
        self.step()
        self.update()

    def step(self):
        pass

    def s(self):
        """Scale relative to a 1024-wide screen (so the preview looks the same, smaller)."""
        return max(0.15, self.width() / 1024)


class Blank(Saver):
    FPS = 2

    def paintEvent(self, event):
        QPainter(self).fillRect(self.rect(), QColor("black"))


class WindowsXP(Saver):
    """The XP logo fading in and out at a new spot each time, drifting slowly."""
    CYCLE = 9.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logo = pixmap("xp_logo.png")
        self.pos = None
        self.vel = QPointF(0, 0)
        self.phase = 0.0

    def step(self):
        self.phase += 1 / self.FPS
        if self.pos is None or self.phase >= self.CYCLE:
            self.phase = 0.0
            w = self.logo.width() * self.s() * 0.6
            h = self.logo.height() * self.s() * 0.6
            self.pos = QPointF(random.uniform(0, max(1, self.width() - w)), random.uniform(0, max(1, self.height() - h)))
            angle = random.uniform(0, 2 * math.pi)
            self.vel = QPointF(math.cos(angle), math.sin(angle)) * 6 * self.s()
        self.pos += self.vel / self.FPS

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        if self.logo.isNull() or self.pos is None:
            return
        f = self.phase / self.CYCLE
        p.setOpacity(min(1.0, f * 4, (1 - f) * 4))
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        w = self.logo.width() * self.s() * 0.6
        h = self.logo.height() * self.s() * 0.6
        p.drawPixmap(QRectF(self.pos.x(), self.pos.y(), w, h), self.logo, QRectF(self.logo.rect()))


class Starfield(Saver):
    STARS = 420

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stars = [self._star(random.uniform(0.05, 1.0)) for _ in range(self.STARS)]

    @staticmethod
    def _star(z=1.0):
        return [random.uniform(-1, 1), random.uniform(-1, 1), z]

    def step(self):
        for st in self.stars:
            st[2] -= 0.012
            if st[2] <= 0.02:
                st[:] = self._star()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        cx, cy = self.width() / 2, self.height() / 2
        for x, y, z in self.stars:
            sx, sy = cx + x / z * cx, cy + y / z * cy
            if 0 <= sx < self.width() and 0 <= sy < self.height():
                b = int(min(255, 60 + (1 - z) * 220))
                size = max(1.2, (1 - z) * 3.6 * self.s())
                p.fillRect(QRectF(sx, sy, size, size), QColor(b, b, b))


class _Bouncer:
    """Points bouncing around the screen, with a trail of earlier positions."""

    def __init__(self, n, w, h, speed):
        self.pts = [[random.uniform(0, w), random.uniform(0, h)] for _ in range(n)]
        self.vel = [[random.choice((-1, 1)) * random.uniform(0.5, 1) * speed,
                     random.choice((-1, 1)) * random.uniform(0.5, 1) * speed] for _ in range(n)]
        self.trail = []
        self.hue = random.randint(0, 359)

    def step(self, w, h, keep):
        for pt, v in zip(self.pts, self.vel):
            for i, limit in ((0, w), (1, h)):
                pt[i] += v[i]
                if pt[i] < 0 or pt[i] > limit:
                    v[i] = -v[i]
                    pt[i] = max(0, min(limit, pt[i]))
        self.trail.append([list(pt) for pt in self.pts])
        del self.trail[:-keep]
        self.hue = (self.hue + 0.6) % 360


class Mystify(Saver):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shapes = None

    def step(self):
        if self.shapes is None:
            self.shapes = [_Bouncer(4, self.width(), self.height(), 4 * self.s()) for _ in range(2)]
        for sh in self.shapes:
            sh.step(self.width(), self.height(), 8)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        if not self.shapes:
            return
        p.setRenderHint(QPainter.Antialiasing)
        for sh in self.shapes:
            for i, pts in enumerate(sh.trail):
                c = QColor.fromHsv(int(sh.hue), 220, 255)
                c.setAlpha(int(255 * (i + 1) / len(sh.trail)))
                p.setPen(QPen(c, 1.2))
                p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))


class Beziers(Saver):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.curves = None

    def step(self):
        if self.curves is None:
            self.curves = [_Bouncer(4, self.width(), self.height(), 5 * self.s()) for _ in range(2)]
        for c in self.curves:
            c.step(self.width(), self.height(), 14)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        if not self.curves:
            return
        p.setRenderHint(QPainter.Antialiasing)
        for cv in self.curves:
            for i, pts in enumerate(cv.trail):
                c = QColor.fromHsv(int(cv.hue + i * 4) % 360, 200, 255)
                c.setAlpha(int(255 * (i + 1) / len(cv.trail)))
                p.setPen(QPen(c, 1.3))
                path = QPainterPath(QPointF(*pts[0]))
                path.cubicTo(QPointF(*pts[1]), QPointF(*pts[2]), QPointF(*pts[3]))
                p.drawPath(path)


class Marquee(Saver):
    def __init__(self, parent=None, text=None):
        super().__init__(parent)
        self.text = text or settings()["marquee"] or "Windows XP"
        self.x = None
        self.y = 0
        self.color = QColor.fromHsv(random.randint(0, 359), 200, 255)

    def step(self):
        font = self._font()
        width = QFontMetrics(font).horizontalAdvance(self.text)
        if self.x is None or self.x < -width:
            self.x = self.width()
            self.y = random.uniform(self.height() * 0.2, self.height() * 0.85)
            self.color = QColor.fromHsv(random.randint(0, 359), 200, 255)
        self.x -= 4 * self.s()

    def _font(self):
        font = QFont("Times New Roman")
        font.setPixelSize(max(8, int(64 * self.s())))
        return font

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        if self.x is None:
            return
        p.setFont(self._font())
        p.setPen(self.color)
        p.drawText(QPointF(self.x, self.y), self.text)


class Pipes(Saver):
    """3D Pipes: pipes grow through a 3D grid, drawn shaded onto a canvas that's kept between frames."""
    FPS = 40
    DIRS = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    GRID = 14
    MAX_SEGMENTS = 520

    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = None
        self._reset()

    def _reset(self):
        self.used = set()
        self.pipes = []
        self.segments = 0
        self.canvas = None
        self._new_pipe()

    def _new_pipe(self):
        for _ in range(50):
            pos = tuple(random.randrange(self.GRID) for _ in range(3))
            if pos not in self.used:
                break
        self.used.add(pos)
        self.pipes.append({"pos": pos, "dir": random.choice(self.DIRS),
                           "color": QColor.fromHsv(random.choice([0, 30, 55, 120, 200, 240, 280, 320]), 210, 235)})
        if len(self.pipes) > 5:
            self.pipes.pop(0)

    def _project(self, pos):
        x, y, z = pos
        w, h = self.width(), self.height()
        cell = min(w, h) / (self.GRID + 4)
        sx = w / 2 + (x - z) * cell * 0.87
        sy = h / 2 + (y - self.GRID / 2) * cell + (x + z - self.GRID) * cell * 0.5
        return QPointF(sx, sy), cell

    def step(self):
        if self.canvas is None or self.canvas.size() != self.size():
            self.canvas = QPixmap(self.size())
            self.canvas.fill(QColor("black"))
        pipe = self.pipes[-1]
        options = [d for d in self.DIRS if self._free(pipe["pos"], d)]
        if not options:
            self._new_pipe()
            return
        d = pipe["dir"] if pipe["dir"] in options and random.random() < 0.75 else random.choice(options)
        turned = d != pipe["dir"]
        start = pipe["pos"]
        end = tuple(a + b for a, b in zip(start, d))
        self.used.add(end)
        self._draw(start, end, pipe["color"], joint=turned)
        pipe["pos"], pipe["dir"] = end, d
        self.segments += 1
        if self.segments % 60 == 0:
            self._new_pipe()
        if self.segments >= self.MAX_SEGMENTS:
            self._reset()

    def _free(self, pos, d):
        nxt = tuple(a + b for a, b in zip(pos, d))
        return all(0 <= c < self.GRID for c in nxt) and nxt not in self.used

    def _draw(self, a, b, color, joint):
        p = QPainter(self.canvas)
        p.setRenderHint(QPainter.Antialiasing)
        pa, cell = self._project(a)
        pb, _ = self._project(b)
        r = cell * 0.22
        dx, dy = pb.x() - pa.x(), pb.y() - pa.y()
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy / length * r, dx / length * r
        g = QLinearGradient(pa.x() - nx, pa.y() - ny, pa.x() + nx, pa.y() + ny)
        g.setColorAt(0, color.darker(260))
        g.setColorAt(0.45, color.lighter(150))
        g.setColorAt(1, color.darker(260))
        p.setPen(QPen(g, r * 2, Qt.SolidLine, Qt.FlatCap))
        p.drawLine(pa, pb)
        if joint:
            rg = QRadialGradient(pa.x() - r * 0.4, pa.y() - r * 0.4, r * 1.4)
            rg.setColorAt(0, color.lighter(170))
            rg.setColorAt(1, color.darker(250))
            p.setPen(Qt.NoPen)
            p.setBrush(rg)
            p.drawEllipse(pa, r * 1.25, r * 1.25)
        p.end()

    def paintEvent(self, event):
        p = QPainter(self)
        if self.canvas is not None:
            p.drawPixmap(0, 0, self.canvas)
        else:
            p.fillRect(self.rect(), QColor("black"))


class Slideshow(Saver):
    FPS = 20
    SHOW = 7.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = self._pictures()
        random.shuffle(self.files)
        self.index = -1
        self.current = None
        self.previous = None
        self.since = self.SHOW

    @staticmethod
    def _pictures():
        from .controlpanel import _found_pictures
        files = _found_pictures()
        return files or [p for _l, p in display.wallpapers() if p]

    def step(self):
        self.since += 1 / self.FPS
        if self.since >= self.SHOW and self.files:
            self.since = 0.0
            self.index = (self.index + 1) % len(self.files)
            self.previous = self.current
            self.current = QPixmap(str(self.files[self.index]))

    def _draw(self, p, pm, opacity):
        if pm is None or pm.isNull():
            return
        scale = min(self.width() / pm.width(), self.height() / pm.height(), 1.0 if self.width() > 400 else 99)
        w, h = pm.width() * scale, pm.height() * scale
        p.setOpacity(opacity)
        p.drawPixmap(QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h), pm, QRectF(pm.rect()))

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        fade = min(1.0, self.since / 1.0)
        self._draw(p, self.previous, 1 - fade)
        self._draw(p, self.current, fade)


class FlyingToasters(Saver):
    """After Dark's Flying Toasters: a short clip (assets/video/flying_toasters.mp4) looped silently."""
    FPS = 2                                    # the video drives the repaints
    CLIP = ROOT / "assets" / "video" / "flying_toasters.mp4"

    def __init__(self, parent=None):
        super().__init__(parent)
        from PySide6.QtCore import QUrl
        from PySide6.QtMultimedia import QMediaPlayer, QVideoSink
        self.frame = QImage()
        self.backdrop = QColor()
        self.player = QMediaPlayer(self)
        self.sink = QVideoSink(self)
        self.player.setVideoSink(self.sink)
        self.sink.videoFrameChanged.connect(self._frame)
        self.player.setLoops(QMediaPlayer.Infinite)
        if self.CLIP.exists():
            self.player.setSource(QUrl.fromLocalFile(str(self.CLIP)))
            self.player.play()

    def _frame(self, frame):
        if frame.isValid():
            self.frame = frame.toImage()
            if not self.backdrop.isValid():               # the clip's sky colour, for the bars around it
                self.backdrop = self.frame.pixelColor(2, 2)
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), self.backdrop if self.backdrop.isValid() else QColor("black"))
        if self.frame.isNull():
            return
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        scale = min(self.width() / self.frame.width(), self.height() / self.frame.height())
        w, h = self.frame.width() * scale, self.frame.height() * scale
        p.drawImage(QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h), self.frame)

    def hideEvent(self, event):
        self.player.pause()
        super().hideEvent(event)

    def showEvent(self, event):
        if self.CLIP.exists():
            self.player.play()
        super().showEvent(event)


class _PlusSaver(Saver):
    """The Microsoft Plus! for Windows XP savers: their theme's wallpaper, with things moving over it."""
    WALL = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        from . import themes
        self.bg = QPixmap(str(themes.wallpaper(self.WALL)))
        self.rnd = random.Random()
        self.things = []

    def paint_bg(self, p):
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawPixmap(QRectF(self.rect()), self.bg, QRectF(self.bg.rect()))


class Aquarium(_PlusSaver):
    """Plus! Aquarium: fish swim across the tank, bubbles rise."""
    WALL = "Aquarium"

    def step(self):
        w, h, s = self.width(), self.height(), self.s()
        if len([t for t in self.things if t[0] == "fish"]) < 7:
            d = self.rnd.choice([1, -1])
            self.things.append(["fish", -60 * s if d > 0 else w + 60 * s, self.rnd.uniform(0.12, 0.75) * h, d,
                                self.rnd.uniform(40, 110) * s, self.rnd.uniform(14, 30) * s,
                                self.rnd.choice(["#FF7A1A", "#FFD21A", "#3AA0FF", "#FF4A8A", "#9A5AFF"])])
        if self.rnd.random() < 0.3:
            self.things.append(["bubble", self.rnd.uniform(0, w), h * 0.9, 0, self.rnd.uniform(30, 70) * s,
                                self.rnd.uniform(2, 7) * s, None])
        for t in self.things:
            if t[0] == "fish":
                t[1] += t[3] * t[4] / self.FPS
                t[2] += math.sin(self.t * 2 + t[4]) * 0.3 * s
            else:
                t[2] -= t[4] / self.FPS
                t[1] += math.sin(self.t * 4 + t[2] / 20) * 0.6 * s
        self.things = [t for t in self.things if -100 * s < t[1] < w + 100 * s and t[2] > -20]

    def paintEvent(self, event):
        from .themes import _fish
        p = QPainter(self)
        self.paint_bg(p)
        p.setRenderHint(QPainter.Antialiasing)
        for t in self.things:
            if t[0] == "fish":
                _fish(p, t[1], t[2], t[5], t[6], "#FFFFFF", t[3])
            else:
                p.setPen(QPen(QColor(255, 255, 255, 170), 1.2))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QPointF(t[1], t[2]), t[5], t[5])


class Nature(_PlusSaver):
    """Plus! Nature: leaves drifting down over the hills."""
    WALL = "Nature"

    def step(self):
        w, h, s = self.width(), self.height(), self.s()
        if len(self.things) < 40 and self.rnd.random() < 0.4:
            self.things.append([self.rnd.uniform(0, w), -20, self.rnd.uniform(0, 360), self.rnd.uniform(30, 70) * s,
                                self.rnd.uniform(8, 16) * s, self.rnd.randint(15, 60)])
        for t in self.things:
            t[1] += t[3] / self.FPS
            t[0] += math.sin(self.t * 1.5 + t[3]) * 1.2 * s
            t[2] += 3
        self.things = [t for t in self.things if t[1] < h + 30]

    def paintEvent(self, event):
        p = QPainter(self)
        self.paint_bg(p)
        p.setRenderHint(QPainter.Antialiasing)
        for x, y, a, _v, size, hue in self.things:
            p.save()
            p.translate(x, y)
            p.rotate(a)
            leaf = QPainterPath()
            leaf.moveTo(-size, 0)
            leaf.quadTo(0, -size * 0.7, size, 0)
            leaf.quadTo(0, size * 0.7, -size, 0)
            p.fillPath(leaf, QColor.fromHsv(hue, 210, 220))
            p.restore()


class Space(_PlusSaver):
    """Plus! Space: comets streak past the ringed planet, stars twinkle."""
    WALL = "Space"

    def step(self):
        w, h, s = self.width(), self.height(), self.s()
        if self.rnd.random() < 0.03 and len(self.things) < 4:
            self.things.append([self.rnd.uniform(0, w), -10, self.rnd.uniform(-4, -1) * 60 * s,
                                self.rnd.uniform(2, 5) * 60 * s])
        for t in self.things:
            t[0] += t[2] / self.FPS
            t[1] += t[3] / self.FPS
        self.things = [t for t in self.things if t[1] < h + 50 and t[0] > -50]

    def paintEvent(self, event):
        p = QPainter(self)
        self.paint_bg(p)
        p.setRenderHint(QPainter.Antialiasing)
        rnd = random.Random(int(self.t * 3))
        for _ in range(25):
            b = rnd.randint(180, 255)
            p.fillRect(QRectF(rnd.uniform(0, self.width()), rnd.uniform(0, self.height()), 2, 2), QColor(b, b, 255))
        for x, y, vx, vy in self.things:
            g = QLinearGradient(x, y, x - vx * 0.4, y - vy * 0.4)
            g.setColorAt(0, QColor(255, 255, 255, 230))
            g.setColorAt(1, QColor(120, 180, 255, 0))
            p.setPen(QPen(QBrush(g), 3 * self.s() + 1))
            p.drawLine(QPointF(x, y), QPointF(x - vx * 0.4, y - vy * 0.4))


class DaVinci(_PlusSaver):
    """Plus! Da Vinci: sketches drawing themselves in ink on the parchment."""
    WALL = "Da Vinci"

    def step(self):
        w, h, s = self.width(), self.height(), self.s()
        if not self.things or self.things[-1][3] >= 1:
            if len(self.things) > 6:
                self.things.pop(0)
            kind = self.rnd.choice(["circle", "gear", "spiral", "wing"])
            self.things.append([kind, QPointF(self.rnd.uniform(0.1, 0.9) * w, self.rnd.uniform(0.1, 0.9) * h),
                                self.rnd.uniform(30, 90) * s, 0.0])
        self.things[-1][3] = min(1.0, self.things[-1][3] + 0.012)

    def paintEvent(self, event):
        p = QPainter(self)
        self.paint_bg(p)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(80, 45, 20, 210), 2))
        p.setBrush(Qt.NoBrush)
        for kind, c, r, done in self.things:
            span = int(360 * 16 * done)
            box = QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r)
            if kind == "circle":
                p.drawArc(box, 0, span)
                p.drawArc(box.adjusted(r * 0.4, r * 0.4, -r * 0.4, -r * 0.4), 0, span)
            elif kind == "gear":
                p.drawArc(box, 0, span)
                for k in range(int(16 * done)):
                    a = k * math.pi / 8
                    p.drawLine(c + QPointF(math.cos(a) * r, math.sin(a) * r),
                               c + QPointF(math.cos(a) * r * 1.2, math.sin(a) * r * 1.2))
            elif kind == "spiral":
                path = QPainterPath(c)
                for k in range(int(200 * done)):
                    a = k * 0.12
                    path.lineTo(c + QPointF(math.cos(a) * r * k / 200, math.sin(a) * r * k / 200))
                p.drawPath(path)
            else:
                path = QPainterPath(c)
                for k in range(int(5 * done) + 1):
                    path.quadTo(c + QPointF(r * (0.3 + k * 0.3), -r * 0.8), c + QPointF(r * (0.3 + k * 0.3), r * 0.2))
                p.drawPath(path)


class MatrixRain(Saver):
    """Falling green code: each column has a bright head and a fading trail of glyphs that keep changing."""
    FPS = 30
    KATAKANA = [chr(c) for c in range(0xFF66, 0xFF9E)]
    SYMBOLS = list("0123456789:.=*+-<>|Z")
    FAMILIES = ("MS Gothic", "Yu Gothic", "Meiryo", "MS Mincho", "SimSun")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.size_key = None
        self.columns = []
        self.font = QFont(self.FAMILIES[0])
        self.font.setStyleStrategy(QFont.PreferAntialias)
        self.glyphs = self.SYMBOLS + self.SYMBOLS                 # no Japanese font installed: digits and symbols only
        for family in self.FAMILIES:
            font = QFont(family)
            font.setPixelSize(16)
            if QFontMetrics(font).inFontUcs4(0xFF76):
                self.font.setFamily(family)
                self.glyphs = self.KATAKANA * 2 + self.SYMBOLS
                break

    def _build(self):
        self.size_key = (self.width(), self.height())
        self.cell = max(7, int(16 * self.s()))
        self.font.setPixelSize(self.cell)
        self.rows = self.height() // self.cell + 2
        self.columns = []
        for i in range(self.width() // self.cell + 1):
            col = {"x": i * self.cell, "chars": [random.choice(self.glyphs) for _ in range(self.rows)]}
            self._restart(col, scattered=True)
            self.columns.append(col)

    def _restart(self, col, scattered=False):
        col["length"] = random.randint(8, max(10, self.rows * 2 // 3))
        col["speed"] = random.uniform(0.25, 0.9)
        col["head"] = random.uniform(-self.rows, self.rows) if scattered else -random.uniform(0, self.rows * 0.6)

    def step(self):
        if self.size_key != (self.width(), self.height()):
            self._build()
        for col in self.columns:
            col["head"] += col["speed"]
            if col["head"] - col["length"] > self.rows:
                self._restart(col)
            chars = col["chars"]
            for _ in range(2):
                chars[random.randrange(self.rows)] = random.choice(self.glyphs)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 6, 0))
        if not self.columns:
            return
        p.setFont(self.font)
        cell = self.cell
        for col in self.columns:
            head, length, chars = int(col["head"]), col["length"], col["chars"]
            for i in range(length):
                row = head - i
                if not 0 <= row < self.rows:
                    continue
                if i == 0:
                    p.setPen(QColor(215, 255, 215))
                else:
                    fade = 1 - i / length
                    p.setPen(QColor(0, int(40 + 215 * fade * fade), int(25 * fade)))
                p.drawText(col["x"], (row + 1) * cell - cell // 5, chars[row])


from .supercb import make_saver_class  # noqa: E402

SuperClaudeBros = make_saver_class(Saver)     # the Super Mario Bros. clock (supercb.py)
from . import zeldacb  # noqa: E402

LegendOfClaude = zeldacb.make_saver_class(Saver)     # the Legend of Zelda clock (zeldacb.py)
from . import smb3cb  # noqa: E402

SuperClaudeBros3 = smb3cb.make_saver_class(Saver)    # the Super Mario Bros. 3 clock (smb3cb.py)
from . import zelda2cb  # noqa: E402

AdventureOfClaude = zelda2cb.make_saver_class(Saver)  # the Zelda II clock (zelda2cb.py)

SAVERS = {"(None)": None, "Super Claude Bros": SuperClaudeBros, "Super Claude Bros. 3": SuperClaudeBros3,
          "The Legend of Claude": LegendOfClaude, "Zelda II: The Adventure of Claude": AdventureOfClaude,
          "Windows XP": WindowsXP, "3D Pipes": Pipes,
          "Beziers": Beziers, "Blank": Blank,
          "Copilot Matrix Rain": MatrixRain,
          "Flying Toasters": FlyingToasters, "Marquee": Marquee, "My Pictures Slideshow": Slideshow,
          "Mystify": Mystify, "Starfield": Starfield, "Aquarium": Aquarium, "Da Vinci": DaVinci, "Nature": Nature,
          "Space": Space}


def make(name, parent=None):
    cls = SAVERS.get(name)
    return cls(parent) if cls else None


# ---- running it ------------------------------------------------------------------------------------

class ScreenSaverManager(QWidget):
    """Watches for idle time and covers the PC screen with the chosen screen saver."""
    WAKE_GRACE = 0.8      # seconds after starting during which mouse jitter is ignored

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.saver = None
        self.started = 0.0
        self.last_pos = None
        self.hide()
        self.setMouseTracking(True)
        self.setCursor(Qt.BlankCursor)
        self.checker = QTimer(self)
        self.checker.timeout.connect(self._check)
        self.checker.start(5000)
        app.installEventFilter(self)

    def active(self):
        return self.isVisible()

    def _check(self):
        s = settings()
        if self.active() or SAVERS.get(s["saver"]) is None:
            return
        app = self.app
        if app.stack.currentWidget() not in (app.desktop, app.welcome):
            return
        if time.monotonic() - app.desktop.last_input >= float(s["wait"]) * 60:
            self.start(s["saver"])

    def start(self, name=None):
        name = name or settings()["saver"]
        saver = make(name, self)
        if saver is None:
            return
        self.saver = saver
        self.setGeometry(self.app.rect())
        saver.setGeometry(self.rect())
        saver.setMouseTracking(True)
        saver.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.started = time.monotonic()
        self.last_pos = None
        self.show()
        self.raise_()
        self.setFocus()
        self.grabKeyboard()

    def stop(self):
        if not self.active():
            return
        self.releaseKeyboard()
        self.hide()
        if self.saver is not None:
            self.saver.deleteLater()
            self.saver = None
        self.app.desktop.last_input = time.monotonic()
        if settings()["resume_welcome"] and self.app.stack.currentWidget() is self.app.desktop:
            self.app.lock()

    def eventFilter(self, obj, event):
        if obj is self.app and event.type() == QEvent.Resize and self.active():
            self.setGeometry(self.app.rect())
            if self.saver is not None:
                self.saver.setGeometry(self.rect())
        return False

    def _wake(self):
        if time.monotonic() - self.started > self.WAKE_GRACE:
            self.stop()

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self.last_pos is not None and (abs(pos.x() - self.last_pos.x()) + abs(pos.y() - self.last_pos.y())) > 6:
            self._wake()
        self.last_pos = pos

    def mousePressEvent(self, event):
        self._wake()

    def keyPressEvent(self, event):
        self._wake()

    def wheelEvent(self, event):
        self._wake()
