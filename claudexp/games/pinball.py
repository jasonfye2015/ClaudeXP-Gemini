"""3D Pinball for Windows - Space Cadet (well, a 2D tribute to it). Real-time ball physics (gravity on a tilted
table, walls, pop bumpers, slingshots, flippers that swing and push), a plunger, drop targets, top rollover lanes
for the bonus multiplier, a Hyperspace kick-out hole, missions that raise your rank from Cadet to Fleet Admiral,
3 balls, nudging (and TILT), and high scores.

Keys, like XP's: Z = left flipper, / = right flipper, Space = plunger (hold, then let go), X or . = nudge,
F2 = new game, F3 = pause."""
import math
import random
import time

from PySide6.QtCore import QElapsedTimer, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QAction, QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
                           QPolygonF, QRadialGradient)
from PySide6.QtWidgets import QWidget

from .. import sound
from .common import GameWindow, message, open_game, save_stats, stats

W, H = 360, 600                 # table coordinates
R = 8                           # ball radius
GRAVITY = 820.0
SUBSTEPS = 8
RANKS = ["Cadet", "Ensign", "Lieutenant", "Captain", "Lt. Commander", "Commander", "Commodore", "Admiral",
         "Fleet Admiral"]
LANE_X0, LANE_X1 = 322, 350     # the plunger lane
TOP_Y = 178                     # centre of the top arc (radius 170, so its top is at y=8)
LANE_TOP = 208                  # where the plunger lane opens onto the playfield
STUCK_SECONDS = 5
PLUNGER_Y = 568
FLIPPER_LEN, FLIPPER_R = 56, 6
FLIP_SPEED = 24.0               # rad/s
HOW_TO = __doc__.split("\n\n", 1)[1]


def closest_on_segment(px, py, ax, ay, bx, by):
    abx, aby = bx - ax, by - ay
    l2 = abx * abx + aby * aby or 1e-9
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / l2))
    return ax + abx * t, ay + aby * t


class Flipper:
    def __init__(self, x, y, rest, up):
        self.x, self.y = x, y
        self.rest, self.up = rest, up
        self.angle = rest
        self.omega = 0.0
        self.pressed = False

    def tip(self):
        return self.x + math.cos(self.angle) * FLIPPER_LEN, self.y + math.sin(self.angle) * FLIPPER_LEN

    def step(self, dt):
        target = self.up if self.pressed else self.rest
        diff = target - self.angle
        move = max(-FLIP_SPEED * dt, min(FLIP_SPEED * dt, diff))
        self.angle += move
        self.omega = move / dt if dt else 0.0


class Table:
    """The physics and the rules; the widget only draws it and feeds it keys."""

    def __init__(self):
        self.walls = []                   # (ax, ay, bx, by, restitution)
        self._build_walls()
        self.bumpers = [{"x": 112, "y": 205, "r": 18, "lit": 0.0}, {"x": 206, "y": 205, "r": 18, "lit": 0.0},
                        {"x": 159, "y": 265, "r": 18, "lit": 0.0}]
        # slingshots: free-standing triangles (room to pass on both sides); their inner edge kicks
        self.slings = [((40, 330), (78, 405), (40, 385)), ((292, 330), (254, 405), (292, 385))]
        self.targets = [{"y": y, "down": False} for y in (232, 258, 284)]
        self.lanes = [{"x": x, "lit": False} for x in (128, 160, 192)]
        self.lane_posts = [(112, 70), (144, 64), (176, 64), (208, 70)]
        self.sink = (60, 150)
        self.flippers = [Flipper(92, 535, 0.52, -0.42), Flipper(230, 535, math.pi - 0.52, math.pi + 0.42)]
        self.new_game()

    def _build_walls(self):
        add = lambda ax, ay, bx, by, e=0.45: self.walls.append((ax, ay, bx, by, e))
        cx, cy, rad = 180, TOP_Y, 170
        pts = [(cx + rad * math.cos(math.pi + i * math.pi / 24), cy + rad * math.sin(math.pi + i * math.pi / 24))
               for i in range(25)]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            add(ax, ay, bx, by, 0.4)
        add(10, TOP_Y, 10, 455)                   # left wall
        add(10, 451, 96, 531)                     # left guide: meets the flipper's top surface (no notch)
        add(LANE_X1, TOP_Y, LANE_X1, H)           # right outer wall
        add(LANE_X0, H, LANE_X0, LANE_TOP)        # plunger lane inner wall (also the playfield's right wall)
        add(LANE_X0, 451, 226, 530)               # right guide
        add(LANE_X0, PLUNGER_Y, LANE_X1, PLUNGER_Y, 0.2)   # the plunger tip
        for a, c, b in ((40, 330), (78, 405), (40, 385)), ((292, 330), (254, 405), (292, 385)):
            add(*a, *b)                           # the slingshots' other two sides are plain walls
            add(*b, *c)

    # ---- game state ------------------------------------------------------------------------------------------
    def new_game(self):
        self.score = 0
        self.ball_no = 1
        self.balls_left = 3
        self.missions = 0
        self.hyperspace_lit = False
        self.multiplier = 1
        self.over = False
        self.messages = []
        self.say("Welcome, Cadet! Press Space to launch.", 4)
        self.serve()

    def serve(self):
        self.bx, self.by = (LANE_X0 + LANE_X1) / 2, PLUNGER_Y - R - 1
        self.vx = self.vy = 0.0
        self.gate = False
        self.in_play = True
        self.held = None                     # hyperspace hold timer
        self.plunger = 0.0
        self.pulling = False
        self.tilted = False
        self.bumps = []
        self.ball_hits = 0
        self.still = 0.0
        if not getattr(self, "hyperspace_lit", False):
            for t in self.targets:
                t["down"] = False

    @property
    def rank(self):
        return RANKS[min(self.missions, len(RANKS) - 1)]

    def say(self, text, seconds=2.5):
        self.messages.append([text, seconds])
        del self.messages[:-3]

    def add(self, points):
        if not self.tilted:
            self.score += points

    # ---- input -------------------------------------------------------------------------------------------------
    def flipper(self, side, down):
        if self.tilted and down:
            return
        self.flippers[side].pressed = down

    def plunge(self, down):
        if down:
            self.pulling = True
        elif self.pulling:
            self.pulling = False
            if LANE_X0 < self.bx < LANE_X1 and self.by > PLUNGER_Y - 40 and abs(self.vy) < 60:
                self.vy = -(520 + 1150 * self.plunger)
            self.plunger = 0.0

    def nudge(self):
        if not self.in_play or self.tilted:
            return
        now = time.monotonic()
        self.bumps = [t for t in self.bumps if now - t < 3.0] + [now]
        self.vx += random.uniform(-110, 110)
        self.vy -= random.uniform(40, 140)
        if len(self.bumps) > 3:
            self.tilted = True
            for f in self.flippers:
                f.pressed = False
            self.say("TILT!", 4)
        elif len(self.bumps) == 3:
            self.say("Careful...", 1.5)

    # ---- physics ---------------------------------------------------------------------------------------------------
    def step(self, dt):
        for m in self.messages:
            m[1] -= dt
        self.messages = [m for m in self.messages if m[1] > 0]
        for b in self.bumpers:
            b["lit"] = max(0.0, b["lit"] - dt)
        if self.pulling:
            self.plunger = min(1.0, self.plunger + dt * 1.1)
        if not self.in_play or self.over:
            return
        if self.held is not None:
            self.held -= dt
            if self.held <= 0:
                self.held = None
                self.bx, self.by = self.sink[0] + 12, self.sink[1] + 14
                self.vx, self.vy = 260, 120
            return
        h = dt / SUBSTEPS
        for _ in range(SUBSTEPS):
            for f in self.flippers:
                f.step(h)
            self.vy += GRAVITY * h
            speed = math.hypot(self.vx, self.vy)
            if speed > 1900:
                self.vx, self.vy = self.vx / speed * 1900, self.vy / speed * 1900
            self.bx += self.vx * h
            self.by += self.vy * h
            self._collide()
            if self.held is not None:
                return
        # 'ball search': a ball sitting still out on the table gets kicked free
        in_lane = LANE_X0 < self.bx < LANE_X1
        cradled = any(f.pressed for f in self.flippers)      # holding the ball on a raised flipper is allowed
        self.still = self.still + dt if math.hypot(self.vx, self.vy) < 15 and not in_lane and not cradled else 0.0
        if self.still > STUCK_SECONDS:
            self.still = 0.0
            self.vx, self.vy = random.uniform(-250, 250), -random.uniform(250, 450)
            self.say("Ball search", 1.5)
        if not self.gate and self.bx < LANE_X0 - R and self.by < 420:
            self.gate = True                     # the one-way gate at the top of the plunger lane closes
        if self.by > H + 30:
            self._drain()

    def _bounce(self, nx, ny, e, extra_x=0.0, extra_y=0.0):
        rvx, rvy = self.vx - extra_x, self.vy - extra_y
        vn = rvx * nx + rvy * ny
        if vn < 0:
            rvx -= (1 + e) * vn * nx
            rvy -= (1 + e) * vn * ny
            # a little friction along the surface
            tx, ty = -ny, nx
            vt = rvx * tx + rvy * ty
            rvx -= vt * 0.02 * tx
            rvy -= vt * 0.02 * ty
        self.vx, self.vy = rvx + extra_x, rvy + extra_y
        return -vn

    def _segment(self, ax, ay, bx, by, e, radius=0.0):
        cx, cy = closest_on_segment(self.bx, self.by, ax, ay, bx, by)
        dx, dy = self.bx - cx, self.by - cy
        dist = math.hypot(dx, dy)
        reach = R + radius
        if dist >= reach:
            return None
        if dist < 1e-6:
            dx, dy, dist = -(by - ay), bx - ax, math.hypot(bx - ax, by - ay) or 1
        nx, ny = dx / dist, dy / dist
        self.bx, self.by = cx + nx * reach, cy + ny * reach
        return nx, ny, cx, cy

    def _collide(self):
        walls = list(self.walls)
        if self.gate:
            walls.append((LANE_X0, LANE_TOP, LANE_X1, LANE_TOP - 10, 0.3))
        for ax, ay, bx, by, e in walls:
            hit = self._segment(ax, ay, bx, by, e)
            if hit:
                self._bounce(hit[0], hit[1], e)
        # slingshots: the inner edges kick the ball away
        for (a, c, _b) in self.slings:
            hit = self._segment(a[0], a[1], c[0], c[1], 0.5)
            if hit:
                nx, ny = hit[0], hit[1]
                hard = self._bounce(nx, ny, 0.5)
                if hard > 120:
                    self.vx += nx * 380
                    self.vy += ny * 380
                    self.add(100)
        # pop bumpers
        for b in self.bumpers:
            dx, dy = self.bx - b["x"], self.by - b["y"]
            dist = math.hypot(dx, dy)
            reach = b["r"] + R
            if dist < reach:
                nx, ny = dx / (dist or 1), dy / (dist or 1)
                self.bx, self.by = b["x"] + nx * reach, b["y"] + ny * reach
                self._bounce(nx, ny, 0.6)
                vn = self.vx * nx + self.vy * ny
                if vn < 460:
                    self.vx += nx * (460 - vn)
                    self.vy += ny * (460 - vn)
                b["lit"] = 0.25
                self.add(500)
                self.ball_hits += 1
        # lane posts
        for px, py in self.lane_posts:
            dx, dy = self.bx - px, self.by - py
            dist = math.hypot(dx, dy)
            if dist < R + 4:
                nx, ny = dx / (dist or 1), dy / (dist or 1)
                self.bx, self.by = px + nx * (R + 4), py + ny * (R + 4)
                self._bounce(nx, ny, 0.5)
        # drop targets along the left wall
        for t in self.targets:
            if not t["down"] and self.bx - R < 22 and abs(self.by - t["y"]) < 12:
                t["down"] = True
                self.bx = 22 + R
                self.vx = abs(self.vx) * 0.6 + 60
                self.add(1000)
                self.ball_hits += 1
                if all(x["down"] for x in self.targets) and not self.hyperspace_lit:
                    self.hyperspace_lit = True
                    self.say("Targets cleared! Hyperspace is lit - shoot for the hole.", 3.5)
        # top rollover lanes (sensors)
        for lane in self.lanes:
            if abs(self.bx - lane["x"]) < 9 and 60 < self.by < 82 and self.vy > 0 and not lane["lit"]:
                lane["lit"] = True
                self.add(250)
                if all(l["lit"] for l in self.lanes):
                    self.multiplier = min(5, self.multiplier + 1)
                    self.say(f"Bonus multiplier {self.multiplier}x!")
                    for l in self.lanes:
                        l["lit"] = False
        # hyperspace hole
        sx, sy = self.sink
        if math.hypot(self.bx - sx, self.by - sy) < 9 and math.hypot(self.vx, self.vy) < 1100:
            self.bx, self.by, self.vx, self.vy = sx, sy, 0.0, 0.0
            self.held = 1.2
            self.add(5000)
            if self.hyperspace_lit:
                self._mission("Hyperspace jump complete!")
            else:
                self.say("Hyperspace bonus! 5,000")
        # flippers
        for f in self.flippers:
            tx, ty = f.tip()
            hit = self._segment(f.x, f.y, tx, ty, 0.35, FLIPPER_R)
            if hit:
                nx, ny, cx, cy = hit
                sx_, sy_ = -f.omega * (cy - f.y), f.omega * (cx - f.x)      # the flipper surface's velocity
                self._bounce(nx, ny, 0.35, sx_, sy_)

    def _mission(self, why):
        sound.play("ding")
        self.hyperspace_lit = False
        self.missions += 1
        bonus = 10000 * self.missions
        self.add(bonus)
        self.say(why, 2.5)
        self.say(f"Mission complete: +{bonus:,}. Rank: {self.rank}", 3.5)
        for t in self.targets:
            t["down"] = False

    def _drain(self):
        bonus = self.ball_hits * 100 * self.multiplier if not self.tilted else 0
        self.add(bonus)
        self.in_play = False
        self.balls_left -= 1
        if self.balls_left <= 0:
            self.over = True
            self.say("GAME OVER", 30)
            return
        self.say(f"End of ball bonus: {bonus:,}" if bonus else "Ball lost", 2.5)
        self.ball_no += 1
        self.multiplier = 1
        self.serve()
        self.say(f"Ball {self.ball_no}. Press Space to launch.", 3)


# ---- the widget -------------------------------------------------------------------------------------------------------

class Pinball(QWidget):
    PANEL = 210

    def __init__(self, win):
        super().__init__()
        self.win = win
        self.table = Table()
        self.paused = False
        self.recorded = False
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(W * 0.85 + self.PANEL, H * 0.85)
        self.clock = QElapsedTimer()
        self.clock.start()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)
        self.stars = [(random.uniform(0, W), random.uniform(0, H), random.uniform(0.5, 1.6)) for _ in range(90)]

    def new_game(self):
        self.table.new_game()
        self.recorded = False
        self.paused = False
        self.setFocus()

    def toggle_pause(self):
        self.paused = not self.paused
        self.table.say("Paused" if self.paused else "Resumed", 1.5)

    def stop(self):
        self.timer.stop()

    def tick(self):
        dt = min(0.033, self.clock.restart() / 1000)
        if not self.paused:
            self.table.step(dt)
        t = self.table
        if t.over and not self.recorded:
            self.recorded = True
            self._record(t.score)
        self.update()

    def _record(self, score):
        from .hearts import _you
        s = stats("pinball")
        best = s.get("scores", [])
        best.append({"name": _you(), "score": score, "rank": self.table.rank})
        best = sorted(best, key=lambda x: -x["score"])[:5]
        s["scores"] = best
        save_stats("pinball", s)
        if any(b["score"] == score for b in best) and score > 0:
            self.table.say("New high score!", 30)

    # ---- keys --------------------------------------------------------------------------------------------------------
    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        k, text = event.key(), event.text().lower()
        if k == Qt.Key_Z:
            self.table.flipper(0, True)
        elif k in (Qt.Key_Slash, Qt.Key_Question) or text == "/":
            self.table.flipper(1, True)
        elif k == Qt.Key_Space:
            if self.table.over:
                self.new_game()
            else:
                self.table.plunge(True)
        elif k in (Qt.Key_X, Qt.Key_Period, Qt.Key_Up):
            self.table.nudge()
        elif k == Qt.Key_F2:
            self.new_game()
        elif k == Qt.Key_F3:
            self.toggle_pause()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        k, text = event.key(), event.text().lower()
        if k == Qt.Key_Z:
            self.table.flipper(0, False)
        elif k in (Qt.Key_Slash, Qt.Key_Question) or text == "/":
            self.table.flipper(1, False)
        elif k == Qt.Key_Space:
            self.table.plunge(False)

    def focusOutEvent(self, event):
        for f in self.table.flippers:
            f.pressed = False
        super().focusOutEvent(event)

    # ---- drawing -------------------------------------------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#000010"))
        table_w = self.width() - self.PANEL
        scale = min(table_w / W, self.height() / H)
        ox = (table_w - W * scale) / 2
        oy = (self.height() - H * scale) / 2
        p.save()
        p.translate(ox, oy)
        p.scale(scale, scale)
        self._draw_table(p)
        p.restore()
        self._draw_panel(p, QRectF(table_w, 0, self.PANEL, self.height()))

    def _glow_line(self, p, ax, ay, bx, by, color, width=3):
        c = QColor(color)
        c.setAlpha(70)
        p.setPen(QPen(c, width + 5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(ax, ay), QPointF(bx, by))
        p.setPen(QPen(QColor(color), width, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(ax, ay), QPointF(bx, by))

    def _draw_table(self, p):
        t = self.table
        g = QLinearGradient(0, 0, 0, H)
        g.setColorAt(0, QColor("#140A3C"))
        g.setColorAt(0.6, QColor("#0B1A52"))
        g.setColorAt(1, QColor("#05102A"))
        path = QPainterPath()
        path.moveTo(10, H)
        path.lineTo(10, TOP_Y)
        path.arcTo(QRectF(10, TOP_Y - 170, 340, 340), 180, -180)
        path.lineTo(LANE_X1, H)
        path.closeSubpath()
        p.fillPath(path, g)
        p.save()
        p.setClipPath(path)
        for x, y, s in self.stars:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, int(90 + 60 * s)))
            p.drawEllipse(QPointF(x, y), s, s)
        # a faint planet and the title
        planet = QRadialGradient(QPointF(150, 380), 90)
        planet.setColorAt(0, QColor(80, 140, 255, 90))
        planet.setColorAt(1, QColor(20, 40, 120, 0))
        p.setBrush(planet)
        p.drawEllipse(QPointF(160, 380), 90, 90)
        f = QFont("Arial Black")
        f.setPixelSize(22)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(QColor(255, 210, 60, 150))
        p.drawText(QRectF(40, 395, 250, 30), Qt.AlignCenter, "SPACE CADET")
        p.restore()
        for ax, ay, bx, by, _e in t.walls:
            self._glow_line(p, ax, ay, bx, by, "#40E0FF")
        if t.gate:
            self._glow_line(p, LANE_X0, LANE_TOP, LANE_X1, LANE_TOP - 10, "#FF60C0", 2)
        # slingshots
        for (a, c, b) in t.slings:
            tri = QPolygonF([QPointF(*a), QPointF(*c), QPointF(*b)])
            p.setPen(QPen(QColor("#FF8030"), 2))
            p.setBrush(QColor(255, 120, 40, 90))
            p.drawPolygon(tri)
        # bumpers
        for b in t.bumpers:
            lit = b["lit"] > 0
            rg = QRadialGradient(QPointF(b["x"] - 5, b["y"] - 5), b["r"] * 1.4)
            rg.setColorAt(0, QColor("#FFFFFF") if lit else QColor("#FFB0D0"))
            rg.setColorAt(1, QColor("#FF2080") if lit else QColor("#901050"))
            p.setPen(QPen(QColor("#FFE0F0") if lit else QColor("#FF60A0"), 2))
            p.setBrush(rg)
            p.drawEllipse(QPointF(b["x"], b["y"]), b["r"], b["r"])
        # drop targets
        for tg in t.targets:
            if tg["down"]:
                p.fillRect(QRectF(12, tg["y"] - 9, 4, 18), QColor("#405060"))
            else:
                p.fillRect(QRectF(12, tg["y"] - 10, 10, 20), QColor("#FFD040"))
                p.setPen(QPen(QColor("#806000"), 1))
                p.drawRect(QRectF(12, tg["y"] - 10, 10, 20))
        # rollover lanes and posts
        for lane in t.lanes:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#60FF60") if lane["lit"] else QColor("#204020"))
            p.drawEllipse(QPointF(lane["x"], 76), 4, 4)
        for px, py in t.lane_posts:
            p.setBrush(QColor("#C0C0FF"))
            p.drawEllipse(QPointF(px, py), 4, 4)
        # hyperspace hole
        sx, sy = t.sink
        hg = QRadialGradient(QPointF(sx, sy), 14)
        hg.setColorAt(0, QColor("#000000"))
        hg.setColorAt(0.7, QColor("#FF40C0") if t.hyperspace_lit else QColor("#4020A0"))
        hg.setColorAt(1, QColor(120, 80, 255, 0))
        p.setBrush(hg)
        p.drawEllipse(QPointF(sx, sy), 14, 14)
        # flippers
        for f in t.flippers:
            tx, ty = f.tip()
            p.setPen(QPen(QColor("#FFFFFF"), FLIPPER_R * 2, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(f.x, f.y), QPointF(tx, ty))
            p.setPen(QPen(QColor("#E03030"), FLIPPER_R * 2 - 4, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(f.x, f.y), QPointF(tx, ty))
        # plunger
        py = PLUNGER_Y + t.plunger * 26
        p.setPen(QPen(QColor("#A0A0A0"), 2))
        for i in range(6):
            yy = py + 4 + i * (H - py - 6) / 6
            p.drawLine(QPointF(LANE_X0 + 6, yy), QPointF(LANE_X1 - 6, yy + 3))
        p.fillRect(QRectF(LANE_X0 + 3, py, LANE_X1 - LANE_X0 - 6, 6), QColor("#E0E0E0"))
        # the ball
        if t.in_play and not t.over:
            bg = QRadialGradient(QPointF(t.bx - 3, t.by - 3), R * 1.6)
            bg.setColorAt(0, QColor("#FFFFFF"))
            bg.setColorAt(0.4, QColor("#C8C8D0"))
            bg.setColorAt(1, QColor("#404050"))
            p.setPen(Qt.NoPen)
            p.setBrush(bg)
            p.drawEllipse(QPointF(t.bx, t.by), R, R)
        if t.tilted:
            f = QFont("Arial Black")
            f.setPixelSize(48)
            p.setFont(f)
            p.setPen(QColor(255, 40, 40, 200))
            p.drawText(QRectF(10, 240, 310, 80), Qt.AlignCenter, "TILT")

    def _draw_panel(self, p, r):
        t = self.table
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, QColor("#202848"))
        g.setColorAt(1, QColor("#080A18"))
        p.fillRect(r, g)
        x = r.left() + 14
        w = r.width() - 28
        f = QFont("Arial Black")
        f.setPixelSize(17)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(QColor("#FFD040"))
        p.drawText(QRectF(x, 14, w, 24), Qt.AlignCenter, "3D Pinball")
        f.setPixelSize(15)
        p.setFont(f)
        p.setPen(QColor("#60C0FF"))
        p.drawText(QRectF(x, 38, w, 22), Qt.AlignCenter, "Space Cadet")
        y = 80
        lab = QFont("Tahoma")
        lab.setPixelSize(12)
        lab.setBold(True)
        for title, value in (("BALL", str(t.ball_no) if not t.over else "-"), ("PLAYER", "1"),
                             ("RANK", t.rank), ("BONUS", f"{t.multiplier}x")):
            p.setFont(lab)
            p.setPen(QColor("#A0B0D0"))
            p.drawText(QRectF(x, y, w, 16), Qt.AlignLeft, title)
            p.setPen(QColor("#FFFFFF"))
            p.drawText(QRectF(x, y, w, 16), Qt.AlignRight, value)
            y += 22
        # score in red LED digits
        box = QRectF(x, y + 8, w, 40)
        p.fillRect(box, QColor("#100000"))
        p.setPen(QPen(QColor("#502020"), 1))
        p.drawRect(box)
        digits = QFont("Lucida Console")
        digits.setPixelSize(24)
        digits.setBold(True)
        p.setFont(digits)
        p.setPen(QColor("#FF3020"))
        p.drawText(box.adjusted(4, 0, -6, 0), Qt.AlignRight | Qt.AlignVCenter, f"{t.score:,}")
        y = box.bottom() + 16
        msg = QFont("Tahoma")
        msg.setPixelSize(12)
        p.setFont(msg)
        for text, _left in t.messages[-3:]:
            p.setPen(QColor("#FFE080"))
            rect = QRectF(x, y, w, 46)
            p.drawText(rect, Qt.AlignLeft | Qt.TextWordWrap, text)
            y += 44
        p.setPen(QColor("#7080A0"))
        small = QFont("Tahoma")
        small.setPixelSize(10)
        p.setFont(small)
        p.drawText(QRectF(x, r.bottom() - 74, w, 70), Qt.AlignLeft | Qt.TextWordWrap,
                   "Z  left flipper\n/  right flipper\nSpace  plunger\nX or .  nudge     F3  pause")
        if self.paused:
            p.setPen(QColor("#FFFFFF"))
            p.setFont(lab)
            p.drawText(QRectF(x, r.bottom() - 100, w, 20), Qt.AlignCenter, "PAUSED")


def pinball_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, 0, 32)
    g.setColorAt(0, QColor("#2A1A70"))
    g.setColorAt(1, QColor("#0A2060"))
    p.setPen(QPen(QColor("#40E0FF"), 1.5))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(5, 2, 22, 28), 9, 9)
    p.setPen(QPen(QColor("#E03030"), 3, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(9, 24, 14, 26)
    p.drawLine(23, 24, 18, 26)
    rg = QRadialGradient(QPointF(15, 12), 5)
    rg.setColorAt(0, QColor("white"))
    rg.setColorAt(1, QColor("#606070"))
    p.setPen(Qt.NoPen)
    p.setBrush(rg)
    p.drawEllipse(QPointF(16, 13), 4, 4)
    p.end()
    return QIcon(pm)


def _high_scores_text():
    best = stats("pinball").get("scores", [])
    if not best:
        return "No high scores yet."
    return "\n".join(f"{i + 1}.  {b['name']:<14} {b['score']:>12,}   ({b.get('rank', '')})" for i, b in enumerate(best))


def open_pinball(desktop):
    def make():
        win = GameWindow(desktop, Pinball, status=False)
        game = win.play
        gm = win.menu.addMenu("&Game")
        gm.addAction("&New Game", game.new_game, "F2")
        gm.addAction("&Launch Ball", lambda: (game.table.plunge(True), QTimer.singleShot(400, lambda: game.table.plunge(False))))
        gm.addAction("&Pause/Resume Game", game.toggle_pause, "F3")
        gm.addSeparator()
        gm.addAction("&High Scores...", lambda: message(desktop, "High Scores", _high_scores_text()))
        gm.addSeparator()
        gm.addAction("E&xit", lambda: win.frame.request_close())
        win.menu.addMenu("&Help").addAction("&How to Play", lambda: message(desktop, "3D Pinball", HOW_TO))
        QTimer.singleShot(200, game.setFocus)
        return win

    return open_game(desktop, "pinball", "3D Pinball for Windows - Space Cadet", make, pinball_icon(), (620, 640))
