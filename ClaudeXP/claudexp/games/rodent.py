"""Rodent's Revenge: push blocks to trap the cats, then eat the cheese they turn into. An original recreation of the
Entertainment Pack classic, drawn in code.

Move with the arrow keys (or the number pad, diagonals included). Walking into a block pushes the whole row of blocks
ahead of you, as long as there's room at the end. A cat that can't move anywhere turns into cheese. Cats come in
waves; you have three lives. Level 2 onward adds immovable stones."""
import random

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QWidget

from .. import sound
from .common import GameWindow, message, open_game, save_stats, stats

N = 23                      # grid size
CELL = 22
W = H = N * CELL
EMPTY, WALL, BLOCK, STONE, CHEESE = 0, 1, 2, 3, 4
KEYS = {Qt.Key_Left: (0, -1), Qt.Key_Right: (0, 1), Qt.Key_Up: (-1, 0), Qt.Key_Down: (1, 0),
        Qt.Key_4: (0, -1), Qt.Key_6: (0, 1), Qt.Key_8: (-1, 0), Qt.Key_2: (1, 0),
        Qt.Key_7: (-1, -1), Qt.Key_9: (-1, 1), Qt.Key_1: (1, -1), Qt.Key_3: (1, 1),
        Qt.Key_Home: (-1, -1), Qt.Key_PageUp: (-1, 1), Qt.Key_End: (1, -1), Qt.Key_PageDown: (1, 1)}
DIRS8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


class Garden(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setFixedSize(W, H)
        self.setFocusPolicy(Qt.StrongFocus)
        self.timer = QTimer(self, interval=520, timeout=self.cats_move)
        self.new_game()

    def new_game(self):
        self.level = 0
        self.score = 0
        self.lives = 3
        self.next_level()

    def next_level(self):
        self.level += 1
        g = [[EMPTY] * N for _ in range(N)]
        for i in range(N):
            g[0][i] = g[N - 1][i] = g[i][0] = g[i][N - 1] = WALL
        for r in range(4, N - 4):                         # the garden of movable blocks
            for c in range(4, N - 4):
                g[r][c] = BLOCK
        rng = random.Random()
        for _ in range(4 * (self.level - 1)):            # later levels scatter stones you can't push
            r, c = rng.randrange(2, N - 2), rng.randrange(2, N - 2)
            if g[r][c] == EMPTY or (g[r][c] == BLOCK and rng.random() < 0.3):
                g[r][c] = STONE
        self.grid = g
        self.mouse = (N // 2, N // 2)
        self.grid[N // 2][N // 2] = EMPTY
        self.wave = 0
        self.cats = []
        self.dead_until = 0
        self.over = False
        self.spawn_wave()
        self.timer.start()
        self._status()
        self.update()

    def spawn_wave(self):
        self.wave += 1
        n = min(1 + self.wave // 2 + (self.level - 1), 6)
        edge = [(r, c) for r in range(1, N - 1) for c in range(1, N - 1)
                if (r in (1, N - 2) or c in (1, N - 2)) and self.grid[r][c] == EMPTY]
        random.shuffle(edge)
        far = sorted(edge, key=lambda p: -(abs(p[0] - self.mouse[0]) + abs(p[1] - self.mouse[1])))
        self.cats = far[:n]

    # ---- the mouse ------------------------------------------------------------------------------------
    def keyPressEvent(self, event):
        d = KEYS.get(event.key())
        if d is None or self.over:
            if event.key() in (Qt.Key_P, Qt.Key_Pause):
                self.toggle_pause()
            else:
                super().keyPressEvent(event)
            return
        self.step(d)

    def toggle_pause(self):
        if self.timer.isActive():
            self.timer.stop()
        elif not self.over:
            self.timer.start()
        self._status()

    def step(self, d):
        if not self.timer.isActive():
            return
        r, c = self.mouse
        nr, nc = r + d[0], c + d[1]
        cell = self.grid[nr][nc]
        if (nr, nc) in self.cats or cell in (WALL, STONE):
            return
        if cell == BLOCK:
            er, ec = nr, nc                                    # find the end of the row of blocks
            while self.grid[er][ec] == BLOCK:
                er, ec = er + d[0], ec + d[1]
            if self.grid[er][ec] not in (EMPTY, CHEESE) or (er, ec) in self.cats:
                return
            self.grid[er][ec] = BLOCK
            self.grid[nr][nc] = EMPTY
        elif cell == CHEESE:
            self.grid[nr][nc] = EMPTY
            self.score += 100
            sound.play("notify")
        self.mouse = (nr, nc)
        self._trap_check()
        self._status()
        self.update()

    # ---- the cats -------------------------------------------------------------------------------------
    def _open(self, r, c, others):
        return self.grid[r][c] == EMPTY and (r, c) not in others

    def cats_move(self):
        if self.over or self.window.frame is None or not self.window.desktop.is_active(self.window.frame):
            return
        moved = []
        for i, (r, c) in enumerate(self.cats):
            others = set(self.cats[:i] + moved) | set(self.cats[i + 1:])
            options = [(r + dr, c + dc) for dr, dc in DIRS8 if self._open(r + dr, c + dc, others)]
            if (self.mouse[0], self.mouse[1]) in [(r + dr, c + dc) for dr, dc in DIRS8]:
                self._caught()
                return
            if options:
                mr, mc = self.mouse
                best = min(options, key=lambda p: (max(abs(p[0] - mr), abs(p[1] - mc)), random.random()))
                if random.random() < 0.15:                    # cats aren't perfect hunters
                    best = random.choice(options)
                moved.append(best)
            else:
                moved.append((r, c))
        self.cats = moved
        self._trap_check()
        self.update()

    def _trap_check(self):
        """Cats boxed in (no free cell around them) become cheese; a cleared wave brings the next one."""
        keep = []
        for (r, c) in self.cats:
            others = set(self.cats) - {(r, c)}
            free = [(r + dr, c + dc) for dr, dc in DIRS8
                    if self._open(r + dr, c + dc, others) or (r + dr, c + dc) == self.mouse]
            if free:
                keep.append((r, c))
            else:
                self.grid[r][c] = CHEESE
                self.score += 25
        if len(keep) < len(self.cats):
            sound.play("ding")
        self.cats = keep
        if not self.cats:
            if self.wave >= 3 + self.level:
                self.timer.stop()
                self.score += 500 * self.level
                self._status()
                QTimer.singleShot(200, lambda: message(
                    self.window.desktop, "Rodent's Revenge", f"Level {self.level} complete!\n\nScore: {self.score:,}"
                                                             f"\n\nOn to level {self.level + 1}.",
                    on_button=lambda _b: self.next_level()))
            else:
                self.spawn_wave()

    def _caught(self):
        self.lives -= 1
        sound.play("critical")
        if self.lives <= 0:
            self.over = True
            self.timer.stop()
            s = stats("rodent")
            best = s.get("best", 0)
            if self.score > best:
                s["best"], s["best_level"] = self.score, self.level
                save_stats("rodent", s)
            self._status()
            message(self.window.desktop, "Rodent's Revenge", f"The cats got you.\n\nScore: {self.score:,}\n"
                                                             f"Best: {max(best, self.score):,}\n\nPress F2 to play again.")
        else:
            # the mouse scurries to the safest empty spot
            spots = [(r, c) for r in range(1, N - 1) for c in range(1, N - 1) if self.grid[r][c] == EMPTY
                     and (r, c) not in self.cats]
            self.mouse = max(spots, key=lambda p: min((max(abs(p[0] - a), abs(p[1] - b)) for a, b in self.cats),
                                                      default=99))
            self._status()
        self.update()

    def _status(self):
        state = "" if self.timer.isActive() or self.over else "     (Paused - press P)"
        self.window.status.setText(f"  Level: {self.level}     Lives: {self.lives}     Score: {self.score:,}     "
                                   f"Wave: {self.wave}/{3 + self.level}{state}")

    # ---- drawing ------------------------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#B8D890"))
        for r in range(N):
            for c in range(N):
                cell = QRectF(c * CELL, r * CELL, CELL, CELL)
                kind = self.grid[r][c]
                if kind == WALL:
                    p.fillRect(cell, QColor("#5A4030"))
                elif kind == BLOCK:
                    g = QLinearGradient(cell.topLeft(), cell.bottomRight())
                    g.setColorAt(0, QColor("#E0B060"))
                    g.setColorAt(1, QColor("#A87830"))
                    p.setPen(QPen(QColor("#7A5420"), 1))
                    p.setBrush(g)
                    p.drawRect(cell.adjusted(1, 1, -1, -1))
                elif kind == STONE:
                    p.setPen(QPen(QColor("#404040"), 1))
                    p.setBrush(QColor("#8A8A8A"))
                    p.drawRoundedRect(cell.adjusted(1, 1, -1, -1), 5, 5)
                elif kind == CHEESE:
                    p.setPen(QPen(QColor("#B08A10"), 1))
                    p.setBrush(QColor("#FFD84A"))
                    p.drawPolygon(QPolygonF([cell.bottomLeft() + QPointF(3, -3), cell.bottomRight() + QPointF(-3, -3),
                                             cell.topRight() + QPointF(-3, 5)]))
                    p.setBrush(QColor("#E8B820"))
                    p.drawEllipse(QPointF(cell.center().x() + 2, cell.center().y() + 3), 2, 2)
        for r, c in self.cats:
            draw_cat(p, QRectF(c * CELL, r * CELL, CELL, CELL))
        draw_mouse(p, QRectF(self.mouse[1] * CELL, self.mouse[0] * CELL, CELL, CELL))

    def stop(self):
        self.timer.stop()


def draw_mouse(p, cell):
    cx, cy = cell.center().x(), cell.center().y()
    p.setPen(QPen(QColor("#5A5A5A"), 1))
    p.setBrush(QColor("#A8A8B0"))
    p.drawEllipse(QPointF(cx, cy + 2), 7, 6)
    p.drawEllipse(QPointF(cx - 5, cy - 5), 3.5, 3.5)                  # ears
    p.drawEllipse(QPointF(cx + 5, cy - 5), 3.5, 3.5)
    p.setBrush(QColor("#F0A0B0"))
    p.drawEllipse(QPointF(cx, cy + 4), 1.6, 1.6)
    p.setBrush(QColor("#000000"))
    p.drawEllipse(QPointF(cx - 2.5, cy), 1.1, 1.1)
    p.drawEllipse(QPointF(cx + 2.5, cy), 1.1, 1.1)


def draw_cat(p, cell):
    cx, cy = cell.center().x(), cell.center().y()
    p.setPen(QPen(QColor("#7A3A00"), 1))
    p.setBrush(QColor("#F09A30"))
    p.drawEllipse(QPointF(cx, cy + 1), 8, 7.5)
    p.drawPolygon(QPolygonF([QPointF(cx - 7, cy - 2), QPointF(cx - 6, cy - 10), QPointF(cx - 2, cy - 5)]))
    p.drawPolygon(QPolygonF([QPointF(cx + 7, cy - 2), QPointF(cx + 6, cy - 10), QPointF(cx + 2, cy - 5)]))
    p.setBrush(QColor("#2A6A1A"))
    p.drawEllipse(QPointF(cx - 3, cy), 1.6, 2)
    p.drawEllipse(QPointF(cx + 3, cy), 1.6, 2)
    p.setPen(QPen(QColor("#5A2A00"), 0.8))
    for dy in (-0.5, 1.5):
        p.drawLine(QPointF(cx - 2, cy + 3), QPointF(cx - 9, cy + 2 + dy))
        p.drawLine(QPointF(cx + 2, cy + 3), QPointF(cx + 9, cy + 2 + dy))


def rodent_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(QRectF(1, 1, 30, 30), QColor("#B8D890"))
    p.setPen(QPen(QColor("#7A5420"), 1))
    p.setBrush(QColor("#D8A850"))
    p.drawRect(QRectF(16, 2, 13, 13))
    draw_cat(p, QRectF(15, 15, 16, 16))
    draw_mouse(p, QRectF(1, 4, 16, 16))
    p.end()
    return QIcon(pm)


HOW_TO = ("You are the mouse. Trap the cats by pushing blocks around them.\n\nMove with the arrow keys, or the number "
          "pad for diagonals. Walking into a block pushes the whole row of blocks in front of you, as long as there "
          "is an empty space at the end.\n\nA cat that has nowhere to move turns into cheese: eat it for 100 points. "
          "Cats come in waves; clear every wave to finish the level. If a cat reaches you, you lose a life.\n\n"
          "P pauses. F2 starts a new game.")


def open_rodent(desktop):
    def make():
        win = GameWindow(desktop, Garden)
        garden = win.play
        game = win.menu.addMenu("&Game")
        game.addAction("&New Game", garden.new_game, "F2")
        game.addAction("&Pause", garden.toggle_pause, "P")
        game.addSeparator()
        game.addAction("High &Score...", lambda: message(
            desktop, "Rodent's Revenge", f"High score: {stats('rodent').get('best', 0):,}\n"
                                         f"Level reached: {stats('rodent').get('best_level', 0)}"))
        game.addSeparator()
        game.addAction("E&xit", lambda: win.frame.request_close())
        help_menu = win.menu.addMenu("&Help")
        help_menu.addAction("&How to Play", lambda: message(desktop, "Rodent's Revenge", HOW_TO))
        return win
    win = open_game(desktop, "rodent", "Rodent's Revenge", make, rodent_icon(), None)
    win.content.play.setFocus()
    return win
