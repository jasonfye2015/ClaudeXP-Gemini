"""Screen savers: Windows 11's Bubbles (over your desktop), Ribbons, Mystify and Blank, Photos, plus the ones
ClaudeXP brought along (3D Pipes, Starfield, Flying Toasters, Matrix Rain, Super Claude Bros). The manager watches
for idle time and covers the screen; moving the mouse or a key wakes it (optionally to the logon screen)."""
import math
import random
import time

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import QWidget

from . import display

DEFAULTS = {"saver": "Bubbles", "wait": 10, "resume_welcome": False}


def settings():
    data = display.get().data
    return {k: data.get(k, v) for k, v in DEFAULTS.items()}


class Saver(QWidget):
    INTERVAL = 33

    def __init__(self, parent=None):
        super().__init__(parent)
        self.t0 = time.monotonic()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(self.INTERVAL)

    def _tick(self):
        self.step()
        self.update()

    def step(self):
        pass

    def s(self):
        return time.monotonic() - self.t0


class Bubbles(Saver):
    """Translucent soap bubbles drifting over a shot of the desktop."""

    def __init__(self, parent=None, backdrop=None):
        super().__init__(parent)
        self.backdrop = backdrop
        self.bubbles = []

    def _spawn(self):
        w, h = max(1, self.width()), max(1, self.height())
        for _ in range(18):
            r = random.uniform(28, 70)
            self.bubbles.append([random.uniform(r, w - r), random.uniform(r, h - r), random.uniform(-1.6, 1.6),
                                 random.uniform(-1.6, 1.6), r, random.uniform(0, 360)])

    def step(self):
        if not self.bubbles:
            self._spawn()
        w, h = self.width(), self.height()
        for b in self.bubbles:
            b[0] += b[2]
            b[1] += b[3]
            if b[0] - b[4] < 0 or b[0] + b[4] > w:
                b[2] = -b[2]
                b[0] = min(max(b[0], b[4]), w - b[4])
            if b[1] - b[4] < 0 or b[1] + b[4] > h:
                b[3] = -b[3]
                b[1] = min(max(b[1], b[4]), h - b[4])
            b[5] = (b[5] + 0.7) % 360

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self.backdrop is not None and not self.backdrop.isNull():
            p.drawPixmap(self.rect(), self.backdrop)
        else:
            p.fillRect(self.rect(), QColor("black"))
        for x, y, _vx, _vy, r, hue in self.bubbles:
            g = QRadialGradient(QPointF(x, y), r)
            c = QColor.fromHsv(int(hue), 120, 255, 40)
            g.setColorAt(0.0, QColor(255, 255, 255, 10))
            g.setColorAt(0.82, c)
            g.setColorAt(0.95, QColor.fromHsv(int((hue + 120) % 360), 160, 255, 150))
            g.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(g)
            p.drawEllipse(QPointF(x, y), r, r)
            p.setBrush(QColor(255, 255, 255, 120))
            p.drawEllipse(QPointF(x - r * 0.4, y - r * 0.45), r * 0.18, r * 0.12)


class Ribbons(Saver):
    """Flowing coloured ribbons on black."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ribbons = [{"hue": random.uniform(0, 360), "pts": [], "x": 0.0, "y": 0.0, "a": random.uniform(0, 6.28),
                         "w": random.uniform(18, 42)} for _ in range(4)]
        self.trail = None

    def step(self):
        w, h = max(1, self.width()), max(1, self.height())
        if self.trail is None or self.trail.size() != self.size():
            self.trail = QPixmap(self.size())
            self.trail.fill(QColor("black"))
            for rb in self.ribbons:
                rb["x"], rb["y"] = random.uniform(0, w), random.uniform(0, h)
        p = QPainter(self.trail)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.trail.rect(), QColor(0, 0, 0, 6))
        for rb in self.ribbons:
            rb["a"] += random.uniform(-0.25, 0.25)
            nx = rb["x"] + math.cos(rb["a"]) * 9
            ny = rb["y"] + math.sin(rb["a"]) * 9
            if nx < 0 or nx > w:
                rb["a"] = math.pi - rb["a"]
                nx = min(max(nx, 0), w)
            if ny < 0 or ny > h:
                rb["a"] = -rb["a"]
                ny = min(max(ny, 0), h)
            rb["hue"] = (rb["hue"] + 0.6) % 360
            pen = QPen(QColor.fromHsv(int(rb["hue"]), 200, 255, 200), rb["w"], Qt.SolidLine, Qt.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(rb["x"], rb["y"]), QPointF(nx, ny))
            p.setPen(QPen(QColor(255, 255, 255, 90), rb["w"] * 0.3, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(rb["x"], rb["y"]), QPointF(nx, ny))
            rb["x"], rb["y"] = nx, ny
        p.end()

    def paintEvent(self, event):
        p = QPainter(self)
        if self.trail is None:
            p.fillRect(self.rect(), QColor("black"))
        else:
            p.drawPixmap(0, 0, self.trail)


class Blank(Saver):
    def paintEvent(self, event):
        QPainter(self).fillRect(self.rect(), QColor("black"))


class WindowsLogo(Saver):
    """The Windows 11 flag floating around, like 'Windows Logo' did."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.x, self.y = 100.0, 100.0
        self.vx, self.vy = 2.2, 1.6

    def step(self):
        w, h = self.width(), self.height()
        self.x += self.vx
        self.y += self.vy
        if self.x < 0 or self.x > w - 120:
            self.vx = -self.vx
        if self.y < 0 or self.y > h - 120:
            self.vy = -self.vy

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("black"))
        from .logon import LogonScreen
        LogonScreen._flag(p, self.x, self.y, 110)


def _xp_savers():
    try:
        from claudexp import screensaver as xp
        return {"Mystify": xp.Mystify, "3D Pipes": xp.Pipes, "Starfield": xp.Starfield, "Photos": xp.Slideshow,
                "Flying Toasters": xp.FlyingToasters, "Matrix Rain": xp.MatrixRain, "Beziers": xp.Beziers,
                "Super Claude Bros": xp.SAVERS.get("Super Claude Bros"),
                "Super Claude Bros. 3": xp.SAVERS.get("Super Claude Bros. 3"),
                "The Legend of Claude": xp.SAVERS.get("The Legend of Claude"),
                "Zelda II: The Adventure of Claude": xp.SAVERS.get("Zelda II: The Adventure of Claude")}
    except Exception:
        return {}


SAVERS = {"(None)": None, "Bubbles": Bubbles, "Ribbons": Ribbons, "Windows Logo": WindowsLogo, "Blank": Blank}
SAVERS.update({k: v for k, v in _xp_savers().items() if v is not None})


def make(name, parent=None, backdrop=None):
    cls = SAVERS.get(name)
    if cls is None:
        return None
    if cls is Bubbles:
        return Bubbles(parent, backdrop=backdrop)
    return cls(parent)


class ScreenSaverManager(QWidget):
    """Watches for idle time and covers the PC screen with the chosen screen saver."""
    WAKE_GRACE = 0.8

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
        if app.stack.currentWidget() not in (app.desktop, app.logon):
            return
        if time.monotonic() - app.desktop.last_input >= float(s["wait"]) * 60:
            self.start(s["saver"])

    def start(self, name=None):
        name = name or settings()["saver"]
        backdrop = self.app.stack.currentWidget().grab() if name == "Bubbles" else None
        saver = make(name, self, backdrop=backdrop)
        if saver is None:
            return
        self.saver = saver
        self.setGeometry(self.app.rect())
        saver.setGeometry(self.rect())
        saver.setMouseTracking(True)
        saver.setAttribute(Qt.WA_TransparentForMouseEvents)
        saver.show()
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
