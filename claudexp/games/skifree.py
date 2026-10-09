"""SkiFree: ski down an endless mountain, dodge trees, rocks and stumps, jump the ramps for style, and keep ahead of
what lives at the 2000 m mark. An original recreation of the 1991 Entertainment Pack classic, drawn in code.

The skier steers toward the mouse (or use the arrow keys); F skis fast; F2 starts again; P or Pause pauses."""
import math
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QWidget

from .common import GameWindow, message, open_game, save_stats, stats

W, H = 640, 480
SKIER_Y = 150                         # the skier stays put; the mountain scrolls up past him
PX_PER_M = 8                          # world pixels per metre
YETI_AT = 2000                        # metres
CHUNK = 400                           # obstacles are made per 400 px band of mountain
# headings: angle from straight down (0) in degrees; |angle| 90 = across the slope (stopped)
HEADINGS = [-90, -60, -35, -15, 0, 15, 35, 60, 90]


def _snow_tree(p, x, y, s=1.0, dead=False):
    if dead:
        p.setPen(QPen(QColor("#6A4A2A"), 2 * s))
        p.drawLine(QPointF(x, y), QPointF(x, y - 22 * s))
        for dy, dx in ((-8, -6), (-12, 5), (-17, -4)):
            p.drawLine(QPointF(x, y + dy * s), QPointF(x + dx * s, y + (dy - 4) * s))
        return
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#7A4A1E"))
    p.drawRect(QRectF(x - 2 * s, y - 5 * s, 4 * s, 6 * s))
    for i, (w, top) in enumerate(((13, -14), (10, -21), (7, -27))):
        poly = QPolygonF([QPointF(x - w * s, y + (top + 9) * s), QPointF(x + w * s, y + (top + 9) * s),
                          QPointF(x, y + (top - 2) * s)])
        p.setBrush(QColor("#1E7A2E") if i % 2 == 0 else QColor("#28903A"))
        p.drawPolygon(poly)
    p.setBrush(QColor("#FFFFFF"))
    p.drawPolygon(QPolygonF([QPointF(x - 4 * s, y - 24 * s), QPointF(x + 4 * s, y - 24 * s), QPointF(x, y - 29 * s)]))


def _rock(p, x, y):
    p.setPen(QPen(QColor("#505050"), 1))
    p.setBrush(QColor("#9A9A9A"))
    p.drawPolygon(QPolygonF([QPointF(x - 9, y), QPointF(x - 7, y - 6), QPointF(x - 1, y - 9), QPointF(x + 7, y - 6),
                             QPointF(x + 9, y)]))
    p.setPen(QPen(QColor("#D0D0D0"), 1))
    p.drawLine(QPointF(x - 4, y - 6), QPointF(x, y - 8))


def _stump(p, x, y):
    p.setPen(QPen(QColor("#4A2E12"), 1))
    p.setBrush(QColor("#8A5A2A"))
    p.drawRect(QRectF(x - 6, y - 7, 12, 7))
    p.setBrush(QColor("#C8A060"))
    p.drawEllipse(QRectF(x - 6, y - 10, 12, 5))


def _mogul(p, x, y):
    p.setPen(QPen(QColor("#B8C8E0"), 1.5))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(x - 11, y - 5, 22, 10), 20 * 16, 140 * 16)


def _ramp(p, x, y):
    p.setPen(QPen(QColor("#7A5A20"), 1))
    p.setBrush(QColor("#E8C870"))
    p.drawPolygon(QPolygonF([QPointF(x - 14, y + 4), QPointF(x + 14, y + 4), QPointF(x + 10, y - 6),
                             QPointF(x - 10, y - 6)]))
    p.setPen(QPen(QColor("#B89040"), 1))
    for k in (-6, 0, 6):
        p.drawLine(QPointF(x + k, y + 3), QPointF(x + k * 0.8, y - 5))


def draw_skier(p, x, y, heading, state, frame=0):
    """state: ski | crash | air | eaten-free. heading in degrees (0 = straight down)."""
    p.save()
    p.translate(x, y)
    if state == "crash":
        p.setPen(QPen(QColor("#1A1A1A"), 2))
        p.drawLine(QPointF(-10, 4), QPointF(8, -2))                  # skis every which way
        p.drawLine(QPointF(-8, -3), QPointF(10, 5))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2050C8"))
        p.drawEllipse(QRectF(-8, -4, 16, 7))                         # flat on his back
        p.setBrush(QColor("#F0C8A0"))
        p.drawEllipse(QRectF(6, -5, 6, 6))
        p.setBrush(QColor("#D02020"))
        p.drawRect(QRectF(6, -7, 6, 3))
        p.restore()
        return
    lean = max(-1.0, min(1.0, heading / 60))
    sideways = abs(heading) >= 90
    # skis
    p.setPen(QPen(QColor("#1A1A1A"), 2.2, Qt.SolidLine, Qt.RoundCap))
    if sideways:
        p.drawLine(QPointF(-9, 9), QPointF(9, 9))
        p.drawLine(QPointF(-9, 11), QPointF(9, 11))
    else:
        dx, dy = math.sin(math.radians(heading)) * 10, math.cos(math.radians(heading)) * 10
        for off in (-2.5, 2.5):
            p.drawLine(QPointF(off - dx * 0.6, 8 - dy * 0.6), QPointF(off + dx, 8 + dy * 0.6))
    # body
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#2050C8"))                                      # trousers
    p.drawRect(QRectF(-3.5 + lean * 1.5, 0, 7, 8))
    p.setBrush(QColor("#D02020"))                                      # jacket
    p.drawRoundedRect(QRectF(-4.5 + lean * 2, -9, 9, 10), 2, 2)
    p.setBrush(QColor("#F0C8A0"))                                      # face
    p.drawEllipse(QRectF(-3 + lean * 2.5, -15, 6, 6))
    p.setBrush(QColor("#FFD040"))                                      # hat
    p.drawRect(QRectF(-3.5 + lean * 2.5, -17, 7, 3))
    # poles
    p.setPen(QPen(QColor("#505050"), 1.2))
    p.drawLine(QPointF(-4 + lean * 2, -4), QPointF(-9 + lean * 3, 7))
    p.drawLine(QPointF(4 + lean * 2, -4), QPointF(9 + lean * 3, 7))
    if state == "air":
        p.setPen(QPen(QColor(0, 0, 0, 40), 1))
        p.setBrush(QColor(0, 0, 0, 30))
        p.drawEllipse(QRectF(-8, 20, 16, 4))                         # his shadow far below
    p.restore()


def draw_yeti(p, x, y, frame, eating=False):
    p.save()
    p.translate(x, y)
    p.setPen(QPen(QColor("#9AA8B8"), 1))
    p.setBrush(QColor("#F4F6FA"))
    p.drawEllipse(QRectF(-11, -18, 22, 26))                          # big white body
    p.drawEllipse(QRectF(-8, -30, 16, 15))                           # head
    arm = 6 if frame % 2 else -4
    p.drawEllipse(QRectF(-18, -14 + (arm if not eating else -10), 9, 14))
    p.drawEllipse(QRectF(9, -14 - (arm if not eating else 10), 9, 14))
    leg = 3 if frame % 2 else -3
    p.drawEllipse(QRectF(-9, 4 + leg, 8, 10))
    p.drawEllipse(QRectF(1, 4 - leg, 8, 10))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#1A1A1A"))
    p.drawEllipse(QRectF(-4, -26, 3, 3))
    p.drawEllipse(QRectF(1, -26, 3, 3))
    p.setBrush(QColor("#C83040") if eating else QColor("#5A6A7A"))
    p.drawEllipse(QRectF(-3, -21, 6, 3 if not eating else 6))
    p.restore()


class Slope(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setFixedSize(W, H)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.CrossCursor)
        self.timer = QTimer(self, interval=16, timeout=self.tick)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.best = stats("skifree").get("best", 0)
        self.new_game()

    # ---- game state -----------------------------------------------------------------------------------
    def new_game(self):
        self.seed = random.randrange(1 << 30)
        self.chunks = {}
        self.x = 0.0                         # skier's world position (x across, y down the mountain)
        self.y = 0.0
        self.heading_i = HEADINGS.index(90)  # start standing across the slope
        self.speed = 0.0
        self.fast = False
        self.state = "ski"                   # ski | crash | air | eaten
        self.crash_until = 0.0
        self.air_until = 0.0
        self.style = 0
        self.started = time.monotonic()
        self.elapsed = 0.0
        self.paused = False
        self.yeti = None                     # [x, y] in world coords once he turns up
        self.eaten_at = 0.0
        self.mouse = None
        self.last = time.monotonic()
        self.frame_n = 0
        self.timer.start()
        self.update()

    def _chunk(self, cy):
        if cy not in self.chunks:
            rng = random.Random(self.seed * 1000003 + cy)
            items = []
            n = 14 + min(18, cy // 3)              # the mountain gets busier the further you go
            for _ in range(n):
                kind = rng.choices(["tree", "tree", "dead", "rock", "stump", "mogul", "mogul", "ramp"],
                                   [5, 3, 1, 2, 2, 3, 2, 1])[0]
                x = rng.uniform(-900, 900)
                y = cy * CHUNK + rng.uniform(0, CHUNK)
                if cy == 0 and abs(x) < 120 and y < SKIER_Y + 120:
                    continue                       # a clear run at the top
                items.append([kind, x, y])
            self.chunks[cy] = items
            for old in [k for k in self.chunks if k < cy - 3]:
                del self.chunks[old]
        return self.chunks[cy]

    def obstacles(self):
        top = int((self.y - SKIER_Y) // CHUNK) - 1
        out = []
        for cy in range(max(0, top), top + 4):
            out += self._chunk(cy)
        return out

    @property
    def heading(self):
        return HEADINGS[self.heading_i]

    def metres(self):
        return int(self.y / PX_PER_M)

    # ---- controls -----------------------------------------------------------------------------------
    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key_Left:
            self.mouse = None
            self.heading_i = max(0, self.heading_i - 1)
        elif k == Qt.Key_Right:
            self.mouse = None
            self.heading_i = min(len(HEADINGS) - 1, self.heading_i + 1)
        elif k == Qt.Key_Down:
            self.mouse = None
            self.heading_i = HEADINGS.index(0)
        elif k == Qt.Key_Up:
            self.mouse = None
            self.heading_i = HEADINGS.index(90 if self.heading >= 0 else -90)
        elif k == Qt.Key_F:
            self.fast = not self.fast
        elif k in (Qt.Key_P, Qt.Key_Pause):
            self.toggle_pause()
        else:
            super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        self.mouse = event.position()

    def mousePressEvent(self, event):
        self.mouse = event.position()
        self.setFocus()

    def toggle_pause(self):
        self.paused = not self.paused
        self.last = time.monotonic()
        self.update()

    def _steer_to_mouse(self):
        if self.mouse is None:
            return
        dx = self.mouse.x() - (W / 2)
        dy = self.mouse.y() - SKIER_Y
        if dy <= 4:
            angle = 90 if dx >= 0 else -90           # pointer level with or above him: stop across the slope
        else:
            angle = math.degrees(math.atan2(dx, dy))
        self.heading_i = min(range(len(HEADINGS)), key=lambda i: abs(HEADINGS[i] - angle))

    # ---- the loop -------------------------------------------------------------------------------------
    def tick(self):
        now = time.monotonic()
        dt = min(0.05, now - self.last)
        self.last = now
        desktop = self.window.desktop
        active = self.window.frame is not None and desktop.is_active(self.window.frame)
        if self.paused or not active or self.state == "eaten":
            if self.state == "eaten":
                self.frame_n += 1
                self.update()
            return
        self.frame_n += 1
        self.elapsed += dt
        if self.state == "crash":
            if now >= self.crash_until:
                self.state = "ski"
                self.heading_i = HEADINGS.index(90 if self.heading >= 0 else -90)
        elif self.state == "air" and now >= self.air_until:
            self.state = "ski"
        if self.state == "ski":
            self._steer_to_mouse()
        # speed builds up pointing downhill and bleeds off across the slope
        if self.state != "crash":
            downhill = math.cos(math.radians(self.heading))
            top = (330 if self.fast else 210) * max(0.0, downhill)
            accel = 260 if downhill > 0.2 else 520
            self.speed += max(-accel * dt, min(accel * dt, top - self.speed))
            rad = math.radians(self.heading)
            self.x += math.sin(rad) * self.speed * dt * (0.9 if abs(self.heading) < 90 else 0)
            self.y += math.cos(rad) * self.speed * dt
            if abs(self.heading) >= 90 and self.speed < 5:
                self.speed = 0
        self._collide(now)
        self._yeti(dt, now)
        self.update()

    def _collide(self, now):
        if self.state != "ski":
            return
        for item in self.obstacles():
            kind, ox, oy = item
            if abs(ox - self.x) < 10 and -4 < (oy - (self.y)) < 6:
                if kind in ("tree", "dead", "rock", "stump"):
                    self.state = "crash"
                    self.crash_until = now + 1.1
                    self.speed = 0
                    self.style = max(0, self.style - 2)
                    return
                if kind == "ramp":
                    self.state = "air"
                    self.air_until = now + 0.9 + self.speed / 400
                    self.style += 10 + int(self.speed / 25)
                    return
                if kind == "mogul" and self.speed > 120:
                    self.state = "air"
                    self.air_until = now + 0.25
                    self.style += 1
                    return

    def _yeti(self, dt, now):
        if self.metres() < YETI_AT and self.yeti is None:
            return
        if self.yeti is None:
            self.yeti = [self.x - 260, self.y - SKIER_Y - 40]
        yx, yy = self.yeti
        dx, dy = self.x - yx, self.y - yy
        dist = math.hypot(dx, dy)
        run = 240 + min(120, (self.metres() - YETI_AT) / 10)       # just a little quicker than a normal skier
        if dist > 1:
            self.yeti[0] += dx / dist * run * dt
            self.yeti[1] += dy / dist * run * dt
        if dist < 14:
            self.state = "eaten"
            self.eaten_at = now
            self._game_over()

    def _game_over(self):
        m = self.metres()
        s = stats("skifree")
        best = s.get("best", 0)
        if m > best:
            s["best"] = m
            s["best_style"] = self.style
            save_stats("skifree", s)
            self.best = m
        QTimer.singleShot(1500, lambda: message(
            self.window.desktop, "SkiFree",
            f"The Abominable Snow Monster got you at {m:,} m.\n\nStyle points: {self.style}\n"
            f"Best distance: {max(m, best):,} m\n\nPress F2 to ski again."))

    # ---- drawing ----------------------------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#FFFFFF"))
        ox = W / 2 - self.x
        oy = SKIER_Y - self.y
        items = sorted(self.obstacles(), key=lambda it: it[2])
        behind = [it for it in items if it[2] <= self.y]
        ahead = [it for it in items if it[2] > self.y]
        for it in behind + ahead:
            self._draw_item(p, it, ox, oy)
        sx, sy = W / 2, SKIER_Y - (14 if self.state == "air" else 0)
        if self.state != "eaten":
            draw_skier(p, sx, sy, self.heading, self.state, self.frame_n)
        if self.yeti is not None:
            draw_yeti(p, self.yeti[0] + ox, self.yeti[1] + oy, self.frame_n // 6, eating=self.state == "eaten")
        self._panel(p)
        if self.paused:
            self._banner(p, "Paused  -  press P to continue")
        elif self.window.frame is not None and not self.window.desktop.is_active(self.window.frame) \
                and self.state != "eaten":
            self._banner(p, "Click here to ski")

    def _draw_item(self, p, it, ox, oy):
        kind, x, y = it
        X, Y = x + ox, y + oy
        if -40 < X < W + 40 and -40 < Y < H + 40:
            {"tree": lambda: _snow_tree(p, X, Y), "dead": lambda: _snow_tree(p, X, Y, dead=True),
             "rock": lambda: _rock(p, X, Y), "stump": lambda: _stump(p, X, Y), "mogul": lambda: _mogul(p, X, Y),
             "ramp": lambda: _ramp(p, X, Y)}[kind]()

    def _panel(self, p):
        r = QRectF(W - 150, 6, 144, 70)
        p.setPen(QPen(QColor("#000000"), 1))
        p.setBrush(QColor("#FFFFFF"))
        p.drawRect(r)
        p.setFont(QFont("Courier New", 9, QFont.Bold))
        t = int(self.elapsed)
        lines = [f"Time:  {t // 3600}:{t // 60 % 60:02d}:{t % 60:02d}", f"Dist:  {self.metres():>6,}m",
                 f"Speed: {int(self.speed / PX_PER_M * 3.6):>5}k/h", f"Style: {self.style:>6}"]
        for i, line in enumerate(lines):
            p.drawText(QPointF(r.x() + 8, r.y() + 16 + i * 15), line)

    def _banner(self, p, text):
        p.setFont(QFont("Tahoma", 10, QFont.Bold))
        fm = p.fontMetrics()
        w = fm.horizontalAdvance(text) + 24
        r = QRectF((W - w) / 2, H / 2 - 16, w, 32)
        p.setPen(QPen(QColor("#304070"), 1))
        p.setBrush(QColor(255, 255, 230, 230))
        p.drawRoundedRect(r, 4, 4)
        p.setPen(QColor("#202040"))
        p.drawText(r, Qt.AlignCenter, text)

    def stop(self):
        self.timer.stop()


def skifree_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#FFFFFF"))
    p.setPen(QPen(QColor("#9AB0CC"), 1))
    p.drawRoundedRect(QRectF(1.5, 1.5, 29, 29), 4, 4)
    _snow_tree(p, 25, 27, 0.55)
    draw_skier(p, 12, 16, 15, "ski")
    p.end()
    return QIcon(pm)


HOW_TO = ("Ski as far down the mountain as you can.\n\n"
          "The skier heads toward the mouse pointer (or steer with the arrow keys: Left/Right turn, Down points "
          "straight down the hill, Up stops you across the slope). Press F to ski fast.\n\n"
          "Trees, rocks and stumps knock you over. Ramps and big moguls send you flying - that's where style "
          "points come from.\n\nWatch out after 2000 metres. Press F2 for a new run, P to pause.")


def open_skifree(desktop):
    def make():
        win = GameWindow(desktop, Slope, status=False)
        slope = win.play
        game = win.menu.addMenu("&Game")
        game.addAction("&New Game", slope.new_game, "F2")
        game.addAction("&Pause", slope.toggle_pause, "P")
        game.addSeparator()
        game.addAction("Best &Distance...", lambda: message(
            desktop, "SkiFree", f"Best distance: {stats('skifree').get('best', 0):,} m\n"
                                f"Style points on that run: {stats('skifree').get('best_style', 0)}"))
        game.addSeparator()
        game.addAction("E&xit", lambda: win.frame.request_close())
        help_menu = win.menu.addMenu("&Help")
        help_menu.addAction("&How to Play", lambda: message(desktop, "SkiFree", HOW_TO))
        return win

    win = open_game(desktop, "skifree", "SkiFree", make, skifree_icon(), None)
    win.content.play.setFocus()
    return win
