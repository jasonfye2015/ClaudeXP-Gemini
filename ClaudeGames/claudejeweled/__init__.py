"""Claudejeweled - swap gems, line up three, watch them cascade. In the spirit of Bejeweled.

Classic: play until there are no moves left. Action: the bar drains - keep matching to fill it. Zen: no
ending, no hurry; the board reshuffles itself when it runs out of moves.

Mouse: click a gem then a neighbour (or drag it onto one). Keys: arrows move the cursor, Space picks up /
swaps, H for a hint, P or Esc to pause.
"""
import json
import math
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QFont, QIcon, QLinearGradient, QPainter, QPainterPath,
                           QPen, QPixmap, QPolygonF, QRadialGradient)
from PySide6.QtWidgets import QWidget
from shiboken6 import isValid

from claudecore import host
from . import board as B

SCORES = host.saves("claudejeweled") / "scores.json"    # shared by every era
MODES = ["Classic", "Action", "Zen"]
BLURBS = {"Classic": "Play until you run out of moves.", "Action": "Race the draining bar!",
          "Zen": "No timer, no game over. Just gems."}
GEM_RGB = ["#E8202A", "#F07818", "#F8D020", "#20B840", "#2070F0", "#B030D8", "#E8ECF4"]
# each gem's outline in unit coordinates (-1..1): ruby square, amber hexagon, topaz diamond, emerald octagon,
# sapphire round, amethyst triangle, diamond pentagon
SHAPES = [
    [(-0.78, -0.78), (0.78, -0.78), (0.78, 0.78), (-0.78, 0.78)],
    [(math.cos(math.radians(a)) * 0.88, math.sin(math.radians(a)) * 0.88) for a in range(-90, 270, 60)],
    [(0, -0.95), (0.8, 0), (0, 0.95), (-0.8, 0)],
    [(-0.42, -0.85), (0.42, -0.85), (0.82, -0.42), (0.82, 0.42), (0.42, 0.85), (-0.42, 0.85), (-0.82, 0.42),
     (-0.82, -0.42)],
    [(math.cos(math.radians(a)) * 0.86, math.sin(math.radians(a)) * 0.86) for a in range(-90, 270, 30)],
    [(0, -0.92), (0.9, 0.72), (-0.9, 0.72)],
    [(math.cos(math.radians(a)) * 0.9, math.sin(math.radians(a)) * 0.9 + 0.05) for a in range(-90, 270, 72)],
]
CHEERS = {2: "Good!", 3: "Excellent!", 4: "Awesome!", 5: "Spectacular!", 6: "Extraordinary!", 7: "Unbelievable!"}
_cache = {}


def gem_pixmap(colour, size):
    key = (colour, size)
    if key in _cache:
        return _cache[key]
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.translate(size / 2, size / 2)
    p.scale(size / 2 * 0.9, size / 2 * 0.9)
    draw_gem(p, colour)
    p.end()
    _cache[key] = pm
    return pm


def draw_gem(p, colour):
    """A faceted gem in unit coordinates: a bevel of facets lit from the top left around a flat table."""
    base = QColor(GEM_RGB[colour])
    outer = SHAPES[colour]
    inner = [(x * 0.55, y * 0.55 - 0.06) for x, y in outer]
    n = len(outer)
    p.setPen(Qt.NoPen)
    shadow = QPolygonF([QPointF(x + 0.06, y + 0.08) for x, y in outer])
    p.setBrush(QColor(0, 0, 0, 90))
    p.drawPolygon(shadow)
    for i in range(n):
        (x1, y1), (x2, y2) = outer[i], outer[(i + 1) % n]
        nx, ny = (y2 - y1), -(x2 - x1)                     # the edge's outward normal
        ln = math.hypot(nx, ny) or 1
        light = (-nx * 0.6 - ny * 0.8) / ln               # light from the top left
        c = base.lighter(int(100 + 60 * light)) if light > 0 else base.darker(int(100 - 90 * light))
        p.setBrush(c)
        p.drawPolygon(QPolygonF([QPointF(x1, y1), QPointF(x2, y2), QPointF(*inner[(i + 1) % n]),
                                 QPointF(*inner[i])]))
    g = QLinearGradient(-0.5, -0.6, 0.5, 0.6)
    g.setColorAt(0, base.lighter(165))
    g.setColorAt(0.5, base.lighter(110))
    g.setColorAt(1, base.darker(115))
    p.setBrush(QBrush(g))
    p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in inner]))
    p.setPen(QPen(base.darker(190), 0.05))
    p.setBrush(Qt.NoBrush)
    p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in outer]))
    hl = QRadialGradient(QPointF(-0.28, -0.38), 0.45)
    hl.setColorAt(0, QColor(255, 255, 255, 200))
    hl.setColorAt(1, QColor(255, 255, 255, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(hl))
    p.drawEllipse(QPointF(-0.28, -0.38), 0.45, 0.32)


def draw_hyper(p, t):
    """The hypercube: a little cube with rainbow light swirling over it (unit coordinates)."""
    g = QConicalGradient(QPointF(0, 0), (t * 160) % 360)
    for i, c in enumerate(GEM_RGB[:6] + [GEM_RGB[0]]):
        g.setColorAt(i / 6, QColor(c))
    p.setPen(QPen(QColor(30, 30, 40), 0.06))
    p.setBrush(QBrush(g))
    p.drawRoundedRect(QRectF(-0.72, -0.72, 1.44, 1.44), 0.18, 0.18)
    p.setPen(QPen(QColor(255, 255, 255, 140), 0.05))
    for k in (-0.24, 0.24):
        p.drawLine(QPointF(k, -0.7), QPointF(k, 0.7))
        p.drawLine(QPointF(-0.7, k), QPointF(0.7, k))
    hl = QRadialGradient(QPointF(-0.3, -0.35), 0.5)
    hl.setColorAt(0, QColor(255, 255, 255, 210))
    hl.setColorAt(1, QColor(255, 255, 255, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(hl))
    p.drawEllipse(QPointF(-0.3, -0.35), 0.5, 0.4)


def jeweled_icon():
    ic = QIcon()
    for sz in (16, 32, 48):
        pm = QPixmap(sz, sz)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        h = sz / 2
        for colour, (cx, cy) in ((0, (0.3, 0.32)), (4, (0.7, 0.32)), (3, (0.3, 0.72)), (2, (0.7, 0.72))):
            p.save()
            p.translate(cx * sz, cy * sz)
            p.scale(h * 0.42, h * 0.42)
            draw_gem(p, colour)
            p.restore()
        p.end()
        ic.addPixmap(pm)
    return ic


def load_scores():
    try:
        data = json.loads(SCORES.read_text(encoding="utf-8"))
        return {m: list(data.get(m, [])) for m in MODES}
    except (OSError, ValueError):
        return {m: [] for m in MODES}


class Jeweled(QWidget):
    PANEL = 230

    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(720, 500)
        self.state = "title"                 # title, play, paused, over
        self.mode = "Classic"
        self.scores = load_scores()
        self.board = None
        self.phase = "idle"                  # idle, swap, unswap, pop, fall, levelup
        self.mouse = QPointF(-1, -1)
        self.buttons = []
        self.sel = None
        self.cursor = (3, 3)
        self.drag_from = None
        self.pending = None                  # the swap being animated
        self.popping = []                    # (cell, gem, age) shrinking away
        self.pop_t = 0.0
        self.particles = []
        self.texts = []                      # [x, y, text, age, colour, size]
        self.rays = []                       # star / zap beams: [kind, cells or (cell, cells), age]
        self.banner = None                   # [text, age]
        self.hint = None
        self.idle_t = 0.0
        self.t = 0.0
        self.bg = None
        self.stars = [(random.random(), random.random(), random.random()) for _ in range(90)]
        self.last = time.monotonic()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    # ---- geometry ---------------------------------------------------------------------------------------------
    def _cell_size(self):
        return max(24, int(min((self.height() - 30) / B.N, (self.width() - self.PANEL - 40) / B.N)))

    def _origin(self):
        cs = self._cell_size()
        x = self.PANEL + (self.width() - self.PANEL - cs * B.N) / 2
        return x, (self.height() - cs * B.N) / 2

    def _centre(self, cell):
        cs = self._cell_size()
        ox, oy = self._origin()
        return QPointF(ox + (cell[1] + 0.5) * cs, oy + (cell[0] + 0.5) * cs)

    def _cell_at(self, pos):
        cs = self._cell_size()
        ox, oy = self._origin()
        c, r = int((pos.x() - ox) // cs), int((pos.y() - oy) // cs)
        return (r, c) if 0 <= r < B.N and 0 <= c < B.N and pos.x() >= ox and pos.y() >= oy else None

    # ---- a game ---------------------------------------------------------------------------------------------
    def new_game(self, mode):
        self.mode = mode
        self.board = B.Board()
        self.score = 0
        self.level = 1
        self.progress = 0.0                  # 0..1 toward the next level
        self.bar = 0.5                       # Action mode's draining bar
        self.state = "play"
        self.phase = "fall"
        self.sel = None
        self.hint = None
        self.particles, self.texts, self.rays, self.popping = [], [], [], []
        self.banner = ["Level 1", 0.0]
        self.idle_t = 0.0
        self.saved = False
        self.levelup_pending = False
        self._drop_in()
        self.setFocus()

    def _drop_in(self):
        for r in range(B.N):
            for c in range(B.N):
                g = self.board.grid[r][c]
                g.dy = -(B.N + 1) - (B.N - r) * 0.35 - c * 0.08
                g.vy = 0.0

    def _level_goal(self):
        return 1000 + 600 * (self.level - 1)

    def _gain(self, info):
        pts = info["score"]
        self.score += pts
        n = len(info["cleared"])
        if self.mode == "Action":
            self.bar = min(1.0, self.bar + n * 0.012 + (0.02 if info["cascade"] > 1 else 0))
            if self.bar >= 1.0:
                self._level_up()
        else:
            self.progress += pts / self._level_goal()
            if self.progress >= 1.0:
                self._level_up()

    def _level_up(self):
        self.level += 1
        self.progress = 0.0
        self.bar = 0.55
        self.banner = [f"Level {self.level}!", 0.0]
        self.score += 500 * self.level
        host.sound("notify")
        self.levelup_pending = True

    def _game_over(self, why):
        self.state = "over"
        self.over_why = why
        self.sel = None
        host.sound("critical" if self.mode == "Action" else "exclamation")
        if not self.saved and self.score > 0:
            self.saved = True
            s = sorted(self.scores[self.mode] + [{"score": self.score, "level": self.level,
                                                    "when": time.strftime("%Y-%m-%d")}],
                       key=lambda e: -e["score"])[:5]
            self.scores[self.mode] = s
            try:
                SCORES.parent.mkdir(parents=True, exist_ok=True)
                SCORES.write_text(json.dumps(self.scores, indent=1), encoding="utf-8")
            except OSError:
                pass

    # ---- the loop -------------------------------------------------------------------------------------------
    def _tick(self):
        now = time.monotonic()
        dt = min(0.05, now - self.last)
        self.last = now
        self.t += dt
        self._effects(dt)
        if self.state == "play":
            self._animate(dt)
        self.update()

    def _effects(self, dt):
        for pt in self.particles:
            pt[0] += pt[2] * dt
            pt[1] += pt[3] * dt
            pt[3] += 900 * dt
            pt[4] -= dt
        self.particles = [pt for pt in self.particles if pt[4] > 0]
        for tx in self.texts:
            tx[3] += dt
        self.texts = [tx for tx in self.texts if tx[3] < 1.3]
        for ry in self.rays:
            ry[2] += dt
        self.rays = [ry for ry in self.rays if ry[2] < 0.45]
        if self.banner:
            self.banner[1] += dt
            if self.banner[1] > 1.6:
                self.banner = None

    def _animate(self, dt):
        b = self.board
        moving = False
        for row in b.grid:
            for g in row:
                if g is None:
                    continue
                if g.dx or (g.dy and self.phase in ("swap", "unswap")):
                    for attr in ("dx", "dy"):
                        v = getattr(g, attr)
                        step = 7.0 * dt
                        setattr(g, attr, 0.0 if abs(v) <= step else v - math.copysign(step, v))
                    moving = moving or g.dx or g.dy
                elif g.dy < 0:
                    g.vy += 38 * dt
                    g.dy = min(0.0, g.dy + g.vy * dt)
                    if g.dy == 0:
                        g.vy = 0.0
                    moving = True
                elif g.dy > 0:
                    g.dy = 0.0
        if self.mode == "Action" and self.phase != "levelup":
            self.bar -= dt * (0.010 + 0.003 * self.level)
            if self.bar <= 0:
                self.bar = 0
                self._game_over("Time's up!")
                return
        if self.phase == "swap" and not moving:
            a, b2 = self.pending
            if self.board.productive(a, b2):
                self.phase = "clear"
            else:
                host.sound("default")
                self._slide(a, b2)
                self.phase = "unswap"
        elif self.phase == "unswap" and not moving:
            self.phase = "idle"
        elif self.phase == "pop":
            self.pop_t += dt
            if self.pop_t >= 0.22:
                self.popping = []
                b.collapse()
                self.phase = "fall"
        elif self.phase == "fall" and not moving:
            self.phase = "clear"
        if self.phase == "clear":
            self._clear()
        if self.phase == "idle":
            self.idle_t += dt
            if self.idle_t > 12 and self.hint is None:
                self.hint = b.find_move()

    def _slide(self, a, c):
        """Swap two gems on the board, drawn sliding from where they were."""
        self.board.swap(a, c)
        ga, gc = self.board.get(a), self.board.get(c)
        gc.dx, gc.dy = a[1] - c[1], a[0] - c[0]
        ga.dx, ga.dy = c[1] - a[1], c[0] - a[0]

    def _clear(self):
        info = self.board.clear_step()
        if info is None:
            if self.levelup_pending:
                self.levelup_pending = False
                self.board.fill_fresh()
                self._drop_in()
                self.phase = "fall"
                return
            self.phase = "idle"
            self.idle_t = 0.0
            self.hint = None
            if self.board.find_move() is None:
                if self.mode == "Classic":
                    self._game_over("No more moves!")
                else:
                    self.texts.append([self.width() / 2, self.height() / 2, "No more moves - shuffling!", 0.0,
                                       "#FFFFFF", 18])
                    self.board.shuffle()
                    self._drop_in()
                    self.phase = "fall"
            return
        cs = self._cell_size()
        for cell, gem in info["cleared"]:
            p = self._centre(cell)
            col = QColor(GEM_RGB[gem.colour] if gem.special != "hyper" else "#FFFFFF")
            for _ in range(5):
                a = random.uniform(0, math.tau)
                sp = random.uniform(60, 260)
                self.particles.append([p.x(), p.y(), math.cos(a) * sp, math.sin(a) * sp - 180,
                                       random.uniform(0.5, 0.9), col, random.uniform(2, 4.5)])
        self.popping = list(info["cleared"])
        for kind, cell in info["blasts"]:
            self.rays.append([kind, cell, 0.0])
        for src, cells in info["zaps"]:
            self.rays.append(["zap", (src, cells), 0.0])
        if info["blasts"] or info["zaps"]:
            host.sound("ding")
        xs = [self._centre(c) for c, _g in info["cleared"]]
        cx = sum(p.x() for p in xs) / len(xs)
        cy = sum(p.y() for p in xs) / len(xs)
        self.texts.append([cx, cy, str(info["score"]), 0.0, "#FFFFFF", max(12, int(cs * 0.3))])
        if info["cascade"] >= 2:
            self.banner = [CHEERS[min(7, info["cascade"])], 0.0]
        elif info["biggest"] >= 5:
            self.banner = ["Excellent!", 0.0]
        self._gain(info)
        self.pop_t = 0.0
        self.phase = "pop"

    # ---- input ----------------------------------------------------------------------------------------------
    def _try_swap(self, a, c):
        if abs(a[0] - c[0]) + abs(a[1] - c[1]) != 1:
            return False
        self.pending = (a, c)
        self.sel = None
        self.hint = None
        self.idle_t = 0.0
        self._slide(a, c)
        self.phase = "swap"
        return True

    def _pick(self, cell):
        if self.state != "play" or self.phase != "idle" or cell is None:
            return
        if self.sel is None:
            self.sel = cell
        elif self.sel == cell:
            self.sel = None
        elif not self._try_swap(self.sel, cell):
            self.sel = cell

    def mousePressEvent(self, e):
        self.setFocus()
        pos = e.position()
        for rect, action in reversed(self.buttons):
            if rect.contains(pos):
                host.sound("menu")
                action()
                return
        if self.state == "play" and e.button() == Qt.LeftButton:
            cell = self._cell_at(pos)
            if cell:
                self.cursor = cell
                self.drag_from = cell
                self._pick(cell)

    def mouseMoveEvent(self, e):
        self.mouse = e.position()
        if self.drag_from and e.buttons() & Qt.LeftButton and self.phase == "idle" and self.state == "play":
            c0 = self._centre(self.drag_from)
            dx, dy = self.mouse.x() - c0.x(), self.mouse.y() - c0.y()
            if max(abs(dx), abs(dy)) > self._cell_size() * 0.45:
                r, c = self.drag_from
                to = (r, c + (1 if dx > 0 else -1)) if abs(dx) > abs(dy) else (r + (1 if dy > 0 else -1), c)
                if 0 <= to[0] < B.N and 0 <= to[1] < B.N:
                    self._try_swap(self.drag_from, to)
                self.drag_from = None

    def mouseReleaseEvent(self, e):
        self.drag_from = None

    def keyPressEvent(self, e):
        k = e.key()
        if self.state == "title":
            if k in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
                self.new_game("Classic")
            return
        if k in (Qt.Key_Escape, Qt.Key_P):
            if self.state == "play":
                self.state = "paused"
            elif self.state == "paused":
                self.state = "play"
                self.last = time.monotonic()
            return
        if self.state != "play":
            return
        moves = {Qt.Key_Left: (0, -1), Qt.Key_Right: (0, 1), Qt.Key_Up: (-1, 0), Qt.Key_Down: (1, 0)}
        if k in moves:
            dr, dc = moves[k]
            to = (max(0, min(B.N - 1, self.cursor[0] + dr)), max(0, min(B.N - 1, self.cursor[1] + dc)))
            if self.sel is not None and self.phase == "idle":
                self._try_swap(self.sel, to)
            self.cursor = to
        elif k in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self._pick(self.cursor)
        elif k == Qt.Key_H:
            self._show_hint()

    def _show_hint(self):
        if self.state == "play" and self.phase == "idle":
            self.hint = self.board.find_move()
            if self.mode == "Classic" and self.hint:
                self.score = max(0, self.score - 100)
                self.texts.append([self.PANEL / 2, 200, "-100", 0.0, "#FF8080", 14])

    # ---- painting ----------------------------------------------------------------------------------------------
    def _backdrop(self, p):
        if self.bg is None or self.bg.size() != self.size():
            pm = QPixmap(self.size())
            q = QPainter(pm)
            q.setRenderHint(QPainter.Antialiasing)
            w, h = self.width(), self.height()
            g = QLinearGradient(0, 0, w, h)
            g.setColorAt(0, QColor("#0A0420"))
            g.setColorAt(0.5, QColor("#1A0838"))
            g.setColorAt(1, QColor("#04142A"))
            q.fillRect(pm.rect(), QBrush(g))
            rnd = random.Random(7)
            for colour in ("#6020A0", "#2050C0", "#A02070", "#2090A0"):
                x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(150, 320)
                rg = QRadialGradient(QPointF(x, y), r)
                c = QColor(colour)
                c.setAlpha(70)
                rg.setColorAt(0, c)
                c.setAlpha(0)
                rg.setColorAt(1, c)
                q.setPen(Qt.NoPen)
                q.setBrush(QBrush(rg))
                q.drawEllipse(QPointF(x, y), r, r)
            q.end()
            self.bg = pm
        p.drawPixmap(0, 0, self.bg)
        p.setPen(Qt.NoPen)
        for x, y, s in self.stars:
            a = int(110 + 110 * math.sin(self.t * (0.8 + s * 2) + s * 20))
            p.setBrush(QColor(255, 255, 255, max(20, a)))
            p.drawEllipse(QPointF(x * self.width(), y * self.height()), 0.6 + s, 0.6 + s)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self.buttons = []
        self._backdrop(p)
        if self.state == "title":
            self._draw_title(p)
        else:
            self._draw_panel(p)
            self._draw_board(p)
            if self.state == "paused":
                self._draw_paused(p)
            elif self.state == "over":
                self._draw_over(p)
        self._draw_effects(p)
        p.end()

    def _button(self, p, r, text, action, colour="#5030A0", size=12):
        hot = r.contains(self.mouse)
        c = QColor(colour)
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, c.lighter(165 if hot else 135))
        g.setColorAt(0.5, c)
        g.setColorAt(1, c.darker(140))
        p.setPen(QPen(QColor("#F0D890") if hot else QColor("#B0A0D0"), 1.5))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(r, r.height() / 2.6, r.height() / 2.6)
        p.setFont(QFont("Georgia", size, QFont.Bold))
        p.setPen(QColor("white"))
        p.drawText(r, Qt.AlignCenter, text)
        self.buttons.append((r, action))

    def _logo(self, p, rect, size):
        f = QFont("Georgia", size, QFont.Bold)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(QColor(40, 10, 60, 200))
        p.drawText(rect.translated(3, 3), Qt.AlignCenter, "Claudejeweled")
        g = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        g.setColorAt(0.2, QColor("#FFF6C0"))
        g.setColorAt(0.55, QColor("#F0B030"))
        g.setColorAt(0.9, QColor("#A05010"))
        p.setPen(QPen(QBrush(g), 1))
        p.drawText(rect, Qt.AlignCenter, "Claudejeweled")

    def _draw_title(self, p):
        w, h = self.width(), self.height()
        # a ring of gems turning around the logo
        rad = min(w, h) * 0.36
        for i in range(14):
            a = self.t * 0.35 + i / 14 * math.tau
            x, y = w / 2 + math.cos(a) * rad * 1.35, h * 0.42 + math.sin(a) * rad * 0.75
            sz = int(26 + 14 * (1 + math.sin(a)) / 2)
            p.setOpacity(0.55 + 0.45 * (1 + math.sin(a)) / 2)
            p.drawPixmap(QPointF(x - sz / 2, y - sz / 2), gem_pixmap(i % 7, sz))
        p.setOpacity(1.0)
        self._logo(p, QRectF(0, h * 0.1, w, 80), 46)
        p.setFont(QFont("Georgia", 11))
        p.setPen(QColor("#D8C8F0"))
        p.drawText(QRectF(0, h * 0.1 + 74, w, 22), Qt.AlignHCenter, "Line up three. Watch them fall.")
        y = h * 0.38
        for m in MODES:
            r = QRectF(w / 2 - 120, y, 240, 44)
            self._button(p, r, m, lambda m=m: self.new_game(m),
                         {"Classic": "#5030A0", "Action": "#A03020", "Zen": "#207060"}[m], 15)
            best = self.scores[m][0]["score"] if self.scores[m] else 0
            p.setFont(QFont("Arial", 9))
            p.setPen(QColor("#C8B8E8"))
            p.drawText(QRectF(w / 2 - 200, y + 46, 400, 16), Qt.AlignHCenter,
                       BLURBS[m] + (f"   Best: {best:,}" if best else ""))
            y += 76
        self._button(p, QRectF(w / 2 - 70, y + 4, 140, 32), "Quit",
                     lambda: self.frame.request_close() if self.frame else None, "#404050", 11)

    def _draw_panel(self, p):
        h = self.height()
        r = QRectF(12, 12, self.PANEL - 24, h - 24)
        p.setPen(QPen(QColor(200, 170, 90, 160), 2))
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, QColor(40, 20, 70, 220))
        g.setColorAt(1, QColor(15, 10, 35, 220))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(r, 12, 12)
        self._logo(p, QRectF(r.x(), r.y() + 8, r.width(), 40), 19)
        p.setFont(QFont("Georgia", 10))
        p.setPen(QColor("#C8B8E8"))
        p.drawText(QRectF(r.x(), r.y() + 46, r.width(), 18), Qt.AlignHCenter, f"{self.mode} mode")
        p.setFont(QFont("Georgia", 26, QFont.Bold))
        p.setPen(QColor("#FFF0B0"))
        p.drawText(QRectF(r.x(), r.y() + 74, r.width(), 40), Qt.AlignHCenter, f"{self.score:,}")
        p.setFont(QFont("Georgia", 13, QFont.Bold))
        p.setPen(QColor("white"))
        p.drawText(QRectF(r.x(), r.y() + 122, r.width(), 22), Qt.AlignHCenter, f"Level {self.level}")
        # the level / time bar
        br = QRectF(r.x() + 18, r.y() + 152, r.width() - 36, 18)
        frac = self.bar if self.mode == "Action" else min(1.0, self.progress)
        p.setPen(QPen(QColor("#806040"), 1.5))
        p.setBrush(QColor(0, 0, 0, 160))
        p.drawRoundedRect(br, 9, 9)
        if frac > 0:
            fill = QRectF(br.x() + 2, br.y() + 2, (br.width() - 4) * frac, br.height() - 4)
            bg = QLinearGradient(fill.topLeft(), fill.bottomLeft())
            hot = self.mode == "Action" and frac < 0.25 and int(self.t * 4) % 2
            top = QColor("#FF6040") if hot else QColor("#FFE070") if self.mode != "Action" else QColor("#70E0FF")
            bg.setColorAt(0, top.lighter(130))
            bg.setColorAt(1, top.darker(150))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(bg))
            p.drawRoundedRect(fill, 7, 7)
        p.setFont(QFont("Arial", 8))
        p.setPen(QColor("#B0A0D0"))
        p.drawText(QRectF(br.x(), br.bottom() + 2, br.width(), 14), Qt.AlignHCenter,
                   "Keep it full!" if self.mode == "Action" else "Progress to the next level")
        y = r.y() + 200
        if self.state == "play":
            self._button(p, QRectF(r.x() + 30, y, r.width() - 60, 34), "Hint" + (" (-100)" if self.mode == "Classic" else ""),
                         self._show_hint, "#306090", 11)
            self._button(p, QRectF(r.x() + 30, y + 44, r.width() - 60, 34), "Pause",
                         lambda: setattr(self, "state", "paused"), "#504070", 11)
        best = self.scores[self.mode][0]["score"] if self.scores[self.mode] else 0
        p.setFont(QFont("Georgia", 10))
        p.setPen(QColor("#C8B8E8"))
        p.drawText(QRectF(r.x(), r.bottom() - 70, r.width(), 18), Qt.AlignHCenter, f"Best: {best:,}")
        p.setFont(QFont("Arial", 8))
        p.setPen(QColor("#9080B0"))
        p.drawText(QRectF(r.x() + 12, r.bottom() - 50, r.width() - 24, 44), Qt.AlignHCenter | Qt.TextWordWrap,
                   "4 in a row: Flame Gem. L or T: Star Gem. 5 in a row: Hypercube!")

    def _draw_board(self, p):
        cs = self._cell_size()
        ox, oy = self._origin()
        frame = QRectF(ox - 6, oy - 6, cs * B.N + 12, cs * B.N + 12)
        p.setPen(QPen(QColor(200, 170, 90, 180), 2))
        p.setBrush(QColor(0, 0, 0, 120))
        p.drawRoundedRect(frame, 8, 8)
        p.setPen(Qt.NoPen)
        for r in range(B.N):
            for c in range(B.N):
                p.setBrush(QColor(255, 255, 255, 22) if (r + c) % 2 else QColor(255, 255, 255, 8))
                p.drawRect(QRectF(ox + c * cs, oy + r * cs, cs, cs))
        if self.state == "paused":
            return
        p.save()
        p.setClipRect(QRectF(ox, oy, cs * B.N, cs * B.N))
        gs = int(cs * 0.92)
        # the hint
        if self.hint and self.state == "play":
            for cell in self.hint:
                c = self._centre(cell)
                a = int(120 + 100 * math.sin(self.t * 6))
                p.setPen(QPen(QColor(255, 255, 160, a), 3))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(c, cs * 0.48, cs * 0.48)
        for r in range(B.N):
            for c in range(B.N):
                g = self.board.grid[r][c]
                if g is None:
                    continue
                cx = ox + (c + 0.5 + g.dx) * cs
                cy = oy + (r + 0.5 + g.dy) * cs
                if cy < oy - cs:
                    continue
                self._draw_one(p, g, cx, cy, gs, selected=(r, c) == self.sel)
        for cell, g in self.popping:
            c = self._centre(cell)
            k = max(0.0, 1 - self.pop_t / 0.22)
            p.setOpacity(k)
            self._draw_one(p, g, c.x(), c.y(), max(2, int(gs * (0.4 + 0.6 * k) * (1 + 0.3 * (1 - k)))))
            p.setOpacity(1.0)
        p.restore()
        # selection and keyboard cursor
        if self.sel and self.state == "play":
            c = self._centre(self.sel)
            p.setPen(QPen(QColor("#FFF0A0"), 2.5))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(c.x() - cs / 2 + 2, c.y() - cs / 2 + 2, cs - 4, cs - 4), 6, 6)
        if self.hasFocus() and self.state == "play":
            c = self._centre(self.cursor)
            p.setPen(QPen(QColor(255, 255, 255, 90), 1.5, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawRect(QRectF(c.x() - cs / 2 + 1, c.y() - cs / 2 + 1, cs - 2, cs - 2))

    def _draw_one(self, p, g, cx, cy, size, selected=False):
        if g.special == "flame":
            fl = 0.5 + 0.5 * math.sin(self.t * 9 + cx)
            rg = QRadialGradient(QPointF(cx, cy), size * 0.75)
            rg.setColorAt(0, QColor(255, 220, 80, 220))
            rg.setColorAt(0.6, QColor(255, 90, 0, int(110 + 80 * fl)))
            rg.setColorAt(1, QColor(255, 40, 0, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(rg))
            p.drawEllipse(QPointF(cx, cy), size * 0.75, size * 0.75)
        elif g.special == "star":
            p.save()
            p.translate(cx, cy)
            p.rotate(self.t * 60)
            p.setPen(QPen(QColor(255, 255, 255, 170), max(1.0, size * 0.04)))
            for i in range(8):
                ln = size * (0.62 if i % 2 else 0.78)
                a = i * math.pi / 4
                p.drawLine(QPointF(0, 0), QPointF(math.cos(a) * ln, math.sin(a) * ln))
            p.restore()
        p.save()
        p.translate(cx, cy)
        if selected:
            p.rotate(math.sin(self.t * 5) * 14)
            p.scale(1.08, 1.08)
        if g.special == "hyper":
            p.scale(size / 2 * 0.9, size / 2 * 0.9)
            draw_hyper(p, self.t)
        else:
            p.drawPixmap(QPointF(-size / 2, -size / 2), gem_pixmap(g.colour, size))
        p.restore()
        if g.special == "star":
            a = int(140 + 110 * math.sin(self.t * 7 + cy))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, a))
            p.drawEllipse(QPointF(cx - size * 0.18, cy - size * 0.2), size * 0.07, size * 0.07)

    def _draw_effects(self, p):
        cs = self._cell_size()
        ox, oy = self._origin()
        for kind, data, age in self.rays:
            fade = max(0.0, 1 - age / 0.45)
            if kind == "star":
                c = self._centre(data)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 255, 255, int(200 * fade)))
                th = cs * 0.5 * fade + 2
                p.drawRect(QRectF(ox, c.y() - th / 2, cs * B.N, th))
                p.drawRect(QRectF(c.x() - th / 2, oy, th, cs * B.N))
            elif kind == "flame":
                c = self._centre(data)
                rg = QRadialGradient(c, cs * 1.8)
                rg.setColorAt(0, QColor(255, 255, 200, int(240 * fade)))
                rg.setColorAt(0.5, QColor(255, 140, 20, int(200 * fade)))
                rg.setColorAt(1, QColor(255, 40, 0, 0))
                p.setPen(Qt.NoPen)
                p.setBrush(QBrush(rg))
                p.drawEllipse(c, cs * 1.8, cs * 1.8)
            elif kind == "zap":
                src, cells = data
                s = self._centre(src)
                for i, cell in enumerate(cells):
                    e = self._centre(cell)
                    col = QColor.fromHsv(int(self.t * 400 + i * 40) % 360, 120, 255, int(230 * fade))
                    path = QPainterPath(s)
                    mx, my = (s.x() + e.x()) / 2, (s.y() + e.y()) / 2
                    path.lineTo(mx + random.uniform(-8, 8), my + random.uniform(-8, 8))
                    path.lineTo(e)
                    p.setPen(QPen(col, 2.5))
                    p.setBrush(Qt.NoBrush)
                    p.drawPath(path)
        p.setPen(Qt.NoPen)
        for x, y, _vx, _vy, life, col, sz in self.particles:
            c = QColor(col)
            c.setAlpha(int(255 * min(1.0, life * 2)))
            p.setBrush(c)
            p.drawPolygon(QPolygonF([QPointF(x, y - sz), QPointF(x + sz * 0.7, y), QPointF(x, y + sz),
                                     QPointF(x - sz * 0.7, y)]))
        for x, y, text, age, col, size in self.texts:
            f = QFont("Georgia", size, QFont.Bold)
            p.setFont(f)
            a = int(255 * max(0.0, 1 - age / 1.3))
            r = QRectF(x - 200, y - 30 - age * 40, 400, 40)
            p.setPen(QColor(0, 0, 0, a // 2))
            p.drawText(r.translated(2, 2), Qt.AlignCenter, text)
            c = QColor(col)
            c.setAlpha(a)
            p.setPen(c)
            p.drawText(r, Qt.AlignCenter, text)
        if self.banner and self.state in ("play", "over"):
            text, age = self.banner
            k = min(1.0, age / 0.2)
            a = int(255 * max(0.0, min(1.0, (1.6 - age) / 0.4)))
            ox, oy = self._origin()
            bw = cs * B.N
            f = QFont("Georgia", int(cs * 0.55 * (0.6 + 0.4 * k)), QFont.Bold)
            f.setItalic(True)
            p.setFont(f)
            r = QRectF(ox, oy + bw / 2 - cs, bw, cs * 2)
            p.setPen(QColor(60, 0, 80, a))
            p.drawText(r.translated(3, 3), Qt.AlignCenter, text)
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            g.setColorAt(0.3, QColor(255, 250, 200, a))
            g.setColorAt(0.7, QColor(240, 160, 40, a))
            p.setPen(QPen(QBrush(g), 1))
            p.drawText(r, Qt.AlignCenter, text)

    def _overlay(self, p, title, lines, buttons):
        cs = self._cell_size()
        ox, oy = self._origin()
        bw = cs * B.N
        r = QRectF(ox + bw / 2 - 170, oy + bw / 2 - 130, 340, 260)
        p.setPen(QPen(QColor(220, 190, 100), 2))
        p.setBrush(QColor(20, 10, 45, 235))
        p.drawRoundedRect(r, 14, 14)
        p.setFont(QFont("Georgia", 22, QFont.Bold))
        p.setPen(QColor("#FFE8A0"))
        p.drawText(QRectF(r.x(), r.y() + 14, r.width(), 36), Qt.AlignHCenter, title)
        p.setFont(QFont("Georgia", 11))
        p.setPen(QColor("white"))
        for i, line in enumerate(lines):
            p.drawText(QRectF(r.x(), r.y() + 60 + i * 22, r.width(), 20), Qt.AlignHCenter, line)
        y = r.bottom() - 16 - 40 * len(buttons)
        for text, action, colour in buttons:
            self._button(p, QRectF(r.x() + 70, y, r.width() - 140, 32), text, action, colour, 11)
            y += 40

    def _resume(self):
        self.state = "play"
        self.last = time.monotonic()

    def _draw_paused(self, p):
        self._overlay(p, "Paused", ["The board is hidden while you rest.", f"Score {self.score:,} - level {self.level}"],
                      [("Resume", self._resume, "#307040"), ("Restart", lambda: self.new_game(self.mode), "#504070"),
                       ("Main Menu", lambda: setattr(self, "state", "title"), "#404050")])

    def _draw_over(self, p):
        top = self.scores[self.mode]
        rank = next((i for i, e in enumerate(top) if e["score"] == self.score), None)
        lines = [getattr(self, "over_why", ""), f"Final score: {self.score:,}", f"Reached level {self.level}"]
        if rank == 0:
            lines.append("A new best score!")
        elif rank is not None:
            lines.append(f"#{rank + 1} on your {self.mode} scores")
        self._overlay(p, "Game Over", lines, [("Play Again", lambda: self.new_game(self.mode), "#A03020"),
                                              ("Main Menu", lambda: setattr(self, "state", "title"), "#404050")])

    def shutdown(self):
        self.timer.stop()


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = Jeweled(desktop)
    win = host.window(desktop, "Claudejeweled", body, jeweled_icon(), size=(820, 600))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    body.setFocus()
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.shutdown()
