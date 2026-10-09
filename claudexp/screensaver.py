"""Screen savers: Windows XP, Starfield, Mystify, Beziers, 3D Pipes, Marquee, My Pictures Slideshow, Blank,
and After Dark's Flying Toasters (a looped video clip).

Each saver is a QWidget that animates at any size (full screen, or the little monitor in Display
Properties). The manager watches for idle time and covers the whole PC screen with the chosen saver;
moving the mouse or pressing a key wakes it (optionally to the Welcome screen).
"""
import math
import random
import time

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
                           QPolygonF, QRadialGradient)
from PySide6.QtWidgets import QWidget

from . import display
from .paths import ROOT, pixmap

DEFAULTS = {"saver": "Windows XP", "wait": 10, "resume_welcome": False, "marquee": "Windows XP"}


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


SAVERS = {"(None)": None, "Windows XP": WindowsXP, "3D Pipes": Pipes, "Beziers": Beziers, "Blank": Blank,
          "Flying Toasters": FlyingToasters, "Marquee": Marquee, "My Pictures Slideshow": Slideshow,
          "Mystify": Mystify, "Starfield": Starfield}


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
