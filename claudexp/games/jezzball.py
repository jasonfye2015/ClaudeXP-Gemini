"""JezzBall: trap the bouncing atoms by building walls, and clear 75% of the field to reach the next level.
An original recreation of the Entertainment Pack 4 classic, drawn in code.

Click to start a wall from that spot; it grows both ways at once. Right-click switches between up/down and
left/right walls. If an atom touches a wall while it is still growing, that half is lost - and so is a life.
Areas with no atoms in them fill in. Level n has n+1 atoms and n+1 lives."""
import math
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF, QRadialGradient
from PySide6.QtWidgets import QWidget

from .. import sound
from .common import GameWindow, message, open_game, save_stats, stats

COLS, ROWS, CELL = 38, 24, 16
W, H = COLS * CELL, ROWS * CELL
RADIUS = 6.5
ATOM_SPEED = 150.0          # px/s
WALL_SPEED = 9.0            # cells/s each way
GOAL = 0.75
OPEN, FILLED, RED, BLUE = 0, 1, 2, 3          # cells; RED/BLUE are the two halves of a growing wall


def draw_atom(p, x, y, r=RADIUS, spin=0.0):
    g = QRadialGradient(QPointF(x - r * 0.35, y - r * 0.35), r * 1.4)
    g.setColorAt(0, QColor("#FFFFFF"))
    g.setColorAt(1, QColor("#E8E8E8"))
    p.setPen(QPen(QColor("#701010"), 0.8))
    p.setBrush(g)
    p.drawEllipse(QPointF(x, y), r, r)
    p.save()
    p.setClipRect(QRectF(x - r, y - r, 2 * r, 2 * r))
    p.translate(x, y)
    p.rotate(spin)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#D01818"))
    for k in (-1, 1):
        p.drawEllipse(QRectF(-r * 0.35 + k * r * 0.95 - r * 0.4, -r, r * 0.8, 2 * r))
    p.restore()
    p.setBrush(QColor(255, 255, 255, 170))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(x - r * 0.4, y - r * 0.4), r * 0.28, r * 0.28)


class Atom:
    __slots__ = ("x", "y", "vx", "vy", "spin")

    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy, self.spin = x, y, vx, vy, random.uniform(0, 360)


class Field(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setFixedSize(W, H)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.timer = QTimer(self, interval=16, timeout=self.tick)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.vertical = True
        self.mouse = None
        self.new_game()

    # ---- levels -------------------------------------------------------------------------------------
    def new_game(self):
        self.level = 0
        self.score = 0
        self.next_level()

    def next_level(self):
        self.level += 1
        self.lives = self.level + 1
        self.grid = [[OPEN] * COLS for _ in range(ROWS)]
        for c in range(COLS):
            self.grid[0][c] = self.grid[ROWS - 1][c] = FILLED
        for r in range(ROWS):
            self.grid[r][0] = self.grid[r][COLS - 1] = FILLED
        self.atoms = []
        for _ in range(self.level + 1):
            ang = random.choice((45, 135, 225, 315)) + random.uniform(-8, 8)
            self.atoms.append(Atom(random.uniform(3 * CELL, W - 3 * CELL), random.uniform(3 * CELL, H - 3 * CELL),
                                   math.cos(math.radians(ang)) * ATOM_SPEED, math.sin(math.radians(ang)) * ATOM_SPEED))
        self.halves = []                # growing walls: dict(kind=RED/BLUE, cells=[(r,c)], dir=(dr,dc), head=(r,c), acc)
        self.time_left = 20.0 + 15.0 * self.level
        self.over = False
        self.between = False
        self.last = time.monotonic()
        self.timer.start()
        self._status()
        self.update()

    def cleared(self):
        inner = (ROWS - 2) * (COLS - 2)
        filled = sum(1 for r in range(1, ROWS - 1) for c in range(1, COLS - 1) if self.grid[r][c] == FILLED)
        return filled / inner

    def _status(self):
        self.window.status.setText(f"  Level: {self.level}     Lives: {self.lives}     Area cleared: "
                                   f"{int(self.cleared() * 100)}%     Score: {self.score:,}     "
                                   f"Time: {max(0, int(self.time_left))}")

    # ---- input --------------------------------------------------------------------------------------
    def mouseMoveEvent(self, event):
        self.mouse = event.position()
        self.update()

    def leaveEvent(self, event):
        self.mouse = None
        self.update()

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.RightButton:
            self.vertical = not self.vertical
            self.update()
            return
        if event.button() != Qt.LeftButton or self.over or self.between or self.halves:
            return
        c, r = int(event.position().x() // CELL), int(event.position().y() // CELL)
        if not (0 <= r < ROWS and 0 <= c < COLS) or self.grid[r][c] != OPEN:
            return
        dirs = ((-1, 0), (1, 0)) if self.vertical else ((0, -1), (0, 1))
        self.grid[r][c] = RED
        self.halves = [{"kind": RED, "cells": [(r, c)], "dir": dirs[0], "head": (r, c), "acc": 0.0, "done": False},
                       {"kind": BLUE, "cells": [], "dir": dirs[1], "head": (r, c), "acc": 0.0, "done": False}]

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.vertical = not self.vertical
            self.update()
        else:
            super().keyPressEvent(event)

    # ---- the loop -----------------------------------------------------------------------------------
    def tick(self):
        now = time.monotonic()
        dt = min(0.04, now - self.last)
        self.last = now
        frame = self.window.frame
        if self.over or self.between or frame is None or not self.window.desktop.is_active(frame):
            return
        self.time_left -= dt
        self._grow(dt)
        self._move(dt)
        if self.time_left <= 0:
            self._lose_life(reason="time")
            self.time_left = 20.0 + 15.0 * self.level
        self._status()
        self.update()

    def _grow(self, dt):
        for half in self.halves:
            if half["done"]:
                continue
            half["acc"] += WALL_SPEED * dt
            while half["acc"] >= 1 and not half["done"]:
                half["acc"] -= 1
                r, c = half["head"]
                nr, nc = r + half["dir"][0], c + half["dir"][1]
                if self.grid[nr][nc] == FILLED or self.grid[nr][nc] in (RED, BLUE):
                    half["done"] = True
                else:
                    self.grid[nr][nc] = half["kind"]
                    half["cells"].append((nr, nc))
                    half["head"] = (nr, nc)
        if self.halves and all(h["done"] for h in self.halves):
            for h in self.halves:
                for r, c in h["cells"]:
                    self.grid[r][c] = FILLED
            self.halves = []
            self._fill()

    def _move(self, dt):
        for a in self.atoms:
            a.spin = (a.spin + 300 * dt) % 360
            for axis in ("x", "y"):
                v = a.vx if axis == "x" else a.vy
                pos = getattr(a, axis) + v * dt
                setattr(a, axis, pos)
                hit = self._touching(a)
                if hit is not None:
                    cell_kind, cell = hit
                    if cell_kind in (RED, BLUE):
                        self._break(cell_kind)
                    setattr(a, axis, pos - v * dt)
                    if axis == "x":
                        a.vx = -a.vx
                    else:
                        a.vy = -a.vy
        # atoms bounce off each other too, like the original
        for i in range(len(self.atoms)):
            for j in range(i + 1, len(self.atoms)):
                a, b = self.atoms[i], self.atoms[j]
                dx, dy = b.x - a.x, b.y - a.y
                if dx * dx + dy * dy < (2 * RADIUS) ** 2:
                    if abs(dx) > abs(dy):                   # equal masses: they trade speeds along the hit
                        a.vx, b.vx = b.vx, a.vx
                    else:
                        a.vy, b.vy = b.vy, a.vy
                    a.x -= dx * 0.1
                    a.y -= dy * 0.1
                    b.x += dx * 0.1
                    b.y += dy * 0.1

    def _touching(self, a):
        """The first non-open cell the atom overlaps: (kind, (r, c)), or None."""
        for r in range(int((a.y - RADIUS) // CELL), int((a.y + RADIUS) // CELL) + 1):
            for c in range(int((a.x - RADIUS) // CELL), int((a.x + RADIUS) // CELL) + 1):
                if not (0 <= r < ROWS and 0 <= c < COLS):
                    return FILLED, (r, c)
                kind = self.grid[r][c]
                if kind != OPEN:
                    nx = max(c * CELL, min(a.x, (c + 1) * CELL))
                    ny = max(r * CELL, min(a.y, (r + 1) * CELL))
                    if (a.x - nx) ** 2 + (a.y - ny) ** 2 <= RADIUS * RADIUS:
                        return kind, (r, c)
        return None

    def _break(self, kind):
        """An atom hit a growing wall: that half vanishes, and a life goes with it."""
        for half in self.halves:
            if half["kind"] == kind and not half["done"]:
                for r, c in half["cells"]:
                    self.grid[r][c] = OPEN
                half["cells"] = []
                half["done"] = True
                self._lose_life()
                break

    def _lose_life(self, reason="hit"):
        self.lives -= 1
        sound.play("critical") if reason == "hit" else None
        if self.lives <= 0:
            self.over = True
            self.halves = []
            self._status()
            s = stats("jezzball")
            best = s.get("best", 0)
            if self.score > best:
                s["best"], s["best_level"] = self.score, self.level
                save_stats("jezzball", s)
            QTimer.singleShot(400, lambda: message(
                self.window.desktop, "JezzBall", f"Game over.\n\nYou reached level {self.level} with a score of "
                                                 f"{self.score:,}.\nBest score: {max(best, self.score):,}\n\n"
                                                 "Press F2 to play again."))

    def _fill(self):
        """Seal off every open region that has no atom in it."""
        seen = [[False] * COLS for _ in range(ROWS)]
        atom_cells = {(int(a.y // CELL), int(a.x // CELL)) for a in self.atoms}
        gained = 0
        for r0 in range(ROWS):
            for c0 in range(COLS):
                if self.grid[r0][c0] != OPEN or seen[r0][c0]:
                    continue
                region, stack, has_atom = [], [(r0, c0)], False
                seen[r0][c0] = True
                while stack:
                    r, c = stack.pop()
                    region.append((r, c))
                    if (r, c) in atom_cells:
                        has_atom = True
                    for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                        if 0 <= nr < ROWS and 0 <= nc < COLS and not seen[nr][nc] and self.grid[nr][nc] == OPEN:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                if not has_atom:
                    for r, c in region:
                        self.grid[r][c] = FILLED
                    gained += len(region)
        self.score += gained * 2 * self.level
        if self.cleared() >= GOAL:
            self.between = True
            bonus = int(self.time_left) * 10 * self.level + int((self.cleared() - GOAL) * 4000) * self.level
            self.score += bonus
            self._status()
            sound.play("notify")
            QTimer.singleShot(300, lambda: message(
                self.window.desktop, "JezzBall", f"Level {self.level} cleared!\n\nBonus: {bonus:,}\n"
                                                 f"Score: {self.score:,}\n\nOn to level {self.level + 1}.",
                on_button=lambda _b: self.next_level()))

    # ---- drawing ------------------------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#0E1830"))
        for r in range(ROWS):
            for c in range(COLS):
                kind = self.grid[r][c]
                cell = QRectF(c * CELL, r * CELL, CELL, CELL)
                if kind == OPEN:
                    p.fillRect(cell, QColor("#F4F4F0"))
                    p.setPen(QPen(QColor("#DCDCD4"), 1))
                    p.drawRect(cell.adjusted(0, 0, -0.5, -0.5))
                elif kind == FILLED:
                    g = QLinearGradient(cell.topLeft(), cell.bottomRight())
                    g.setColorAt(0, QColor("#3A5A98"))
                    g.setColorAt(1, QColor("#22386A"))
                    p.fillRect(cell, g)
                else:
                    p.fillRect(cell, QColor("#D82020") if kind == RED else QColor("#2050E0"))
        for a in self.atoms:
            draw_atom(p, a.x, a.y, spin=a.spin)
        if self.mouse is not None and not self.over:
            self._cursor(p, self.mouse)

    def _cursor(self, p, pos):
        """The wall-direction cursor: a double arrow, up/down or left/right."""
        p.save()
        p.translate(pos)
        if not self.vertical:
            p.rotate(90)
        p.setPen(QPen(QColor("#000000"), 1))
        p.setBrush(QColor("#FFFFFF"))
        arrow = [QPointF(0, -11), QPointF(5, -5), QPointF(2, -5), QPointF(2, 5), QPointF(5, 5), QPointF(0, 11),
                 QPointF(-5, 5), QPointF(-2, 5), QPointF(-2, -5), QPointF(-5, -5)]
        p.drawPolygon(QPolygonF(arrow))
        p.restore()

    def stop(self):
        self.timer.stop()


def jezzball_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(QRectF(2, 2, 28, 28), QColor("#F4F4F0"))
    p.fillRect(QRectF(2, 2, 9, 28), QColor("#2C4A88"))
    p.fillRect(QRectF(11, 14, 19, 3), QColor("#D82020"))
    p.setPen(QPen(QColor("#404040"), 1))
    p.setBrush(Qt.NoBrush)
    p.drawRect(QRectF(2.5, 2.5, 27, 27))
    draw_atom(p, 21, 8, 5)
    draw_atom(p, 20, 24, 5, 40)
    p.end()
    return QIcon(pm)


HOW_TO = ("Build walls to trap the bouncing atoms, and clear 75% of the field to finish the level.\n\n"
          "Click in the field to start a wall there: it grows in both directions at once. Right-click (or "
          "Space) switches between up/down and left/right walls.\n\n"
          "If an atom touches a wall while it is still growing, that half of the wall breaks and you lose a "
          "life. Once a wall is finished, any area with no atoms in it is filled in.\n\n"
          "Each level has one more atom than the last. Finish quickly for a time bonus. F2 starts a new game.")


def open_jezzball(desktop):
    def make():
        win = GameWindow(desktop, Field)
        field = win.play
        game = win.menu.addMenu("&Game")
        game.addAction("&New Game", field.new_game, "F2")
        game.addSeparator()
        game.addAction("High &Score...", lambda: message(
            desktop, "JezzBall", f"High score: {stats('jezzball').get('best', 0):,}\n"
                                 f"Level reached: {stats('jezzball').get('best_level', 0)}"))
        game.addSeparator()
        game.addAction("E&xit", lambda: win.frame.request_close())
        help_menu = win.menu.addMenu("&Help")
        help_menu.addAction("&How to Play", lambda: message(desktop, "JezzBall", HOW_TO))
        return win

    win = open_game(desktop, "jezzball", "JezzBall", make, jezzball_icon(), None)
    win.content.play.setFocus()
    return win
