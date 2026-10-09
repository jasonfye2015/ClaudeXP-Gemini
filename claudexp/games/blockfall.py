"""Blockfall: the falling-blocks game every 2001 PC had a copy of. Fit the falling pieces together into full rows.

Left/Right move, Up (or X) rotates, Z rotates the other way, Down drops faster, Space drops all the way. Every ten
rows speeds things up. P pauses, F2 starts again."""
import random

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from .. import sound
from .common import GameWindow, message, open_game, save_stats, stats

COLS, ROWS, CELL = 10, 20, 22
PANEL = 150
W, H = COLS * CELL + PANEL + 24, ROWS * CELL + 16
SHAPES = {
    "I": [(0, 1), (1, 1), (2, 1), (3, 1)], "O": [(1, 0), (2, 0), (1, 1), (2, 1)],
    "T": [(1, 0), (0, 1), (1, 1), (2, 1)], "S": [(1, 0), (2, 0), (0, 1), (1, 1)],
    "Z": [(0, 0), (1, 0), (1, 1), (2, 1)], "J": [(0, 0), (0, 1), (1, 1), (2, 1)],
    "L": [(2, 0), (0, 1), (1, 1), (2, 1)],
}
COLORS = {"I": "#30C8E8", "O": "#F0D020", "T": "#A040D0", "S": "#40C040", "Z": "#E03030", "J": "#3060E0",
          "L": "#F08A20"}
LINE_SCORES = [0, 40, 100, 300, 1200]


def rotate(cells, kind, turns):
    """Rotate within the piece's box (4x4 for I, 3x3 for the rest; O doesn't turn)."""
    if kind == "O":
        return cells
    size = 4 if kind == "I" else 3
    for _ in range(turns % 4):
        cells = [(size - 1 - y, x) for x, y in cells]
    return cells


class Well(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setFixedSize(W, H)
        self.setFocusPolicy(Qt.StrongFocus)
        self.timer = QTimer(self, timeout=self.fall)
        self.new_game()

    def new_game(self):
        self.grid = [[None] * COLS for _ in range(ROWS)]
        self.bag = []
        self.score = 0
        self.lines = 0
        self.level = 1
        self.over = False
        self.paused = False
        self.next_kind = self._draw()
        self.spawn()
        self._speed()
        self.update()

    def _draw(self):
        if not self.bag:
            self.bag = list(SHAPES)
            random.shuffle(self.bag)                      # every shape once per 'bag', like modern rules
        return self.bag.pop()

    def spawn(self):
        self.kind = self.next_kind
        self.next_kind = self._draw()
        self.turn = 0
        self.px, self.py = 3, 0
        if not self.fits(self.px, self.py, self.turn):
            self.over = True
            self.timer.stop()
            self._game_over()

    def cells(self, px=None, py=None, turn=None):
        px = self.px if px is None else px
        py = self.py if py is None else py
        turn = self.turn if turn is None else turn
        return [(px + x, py + y) for x, y in rotate(SHAPES[self.kind], self.kind, turn)]

    def fits(self, px, py, turn):
        for x, y in self.cells(px, py, turn):
            if not (0 <= x < COLS and y < ROWS) or (y >= 0 and self.grid[y][x] is not None):
                return False
        return True

    def _speed(self):
        self.timer.start(max(70, 800 - (self.level - 1) * 70))

    def _active(self):
        return self.window.frame is not None and self.window.desktop.is_active(self.window.frame)

    # ---- controls -----------------------------------------------------------------------------------
    def keyPressEvent(self, event):
        k = event.key()
        if k in (Qt.Key_P, Qt.Key_Pause):
            self.toggle_pause()
            return
        if self.over or self.paused:
            return super().keyPressEvent(event)
        if k == Qt.Key_Left:
            self.shift(-1)
        elif k == Qt.Key_Right:
            self.shift(1)
        elif k in (Qt.Key_Up, Qt.Key_X):
            self.spin(1)
        elif k == Qt.Key_Z:
            self.spin(-1)
        elif k == Qt.Key_Down:
            if self.fall(soft=True):
                self.score += 1
        elif k == Qt.Key_Space:
            while self.fits(self.px, self.py + 1, self.turn):
                self.py += 1
                self.score += 2
            self.lock()
        else:
            return super().keyPressEvent(event)
        self._status()
        self.update()

    def shift(self, dx):
        if self.fits(self.px + dx, self.py, self.turn):
            self.px += dx

    def spin(self, d):
        t = self.turn + d
        for kick in (0, -1, 1, -2, 2):                      # nudge away from walls if the turn doesn't fit
            if self.fits(self.px + kick, self.py, t):
                self.px += kick
                self.turn = t
                return

    def toggle_pause(self):
        if self.over:
            return
        self.paused = not self.paused
        self._status()
        self.update()

    # ---- gravity ------------------------------------------------------------------------------------
    def fall(self, soft=False):
        if self.over or self.paused or (not soft and not self._active()):
            return False
        if self.fits(self.px, self.py + 1, self.turn):
            self.py += 1
            self.update()
            return True
        self.lock()
        return False

    def lock(self):
        for x, y in self.cells():
            if y < 0:
                self.over = True
                self.timer.stop()
                self._game_over()
                return
            self.grid[y][x] = self.kind
        full = [r for r in range(ROWS) if all(self.grid[r][c] is not None for c in range(COLS))]
        for r in full:
            del self.grid[r]
            self.grid.insert(0, [None] * COLS)
        if full:
            self.lines += len(full)
            self.score += LINE_SCORES[len(full)] * self.level
            sound.play("ding" if len(full) < 4 else "notify")
            new_level = 1 + self.lines // 10
            if new_level != self.level:
                self.level = new_level
                self._speed()
        self.spawn()
        self._status()
        self.update()

    def _game_over(self):
        s = stats("blockfall")
        best = s.get("best", 0)
        if self.score > best:
            s["best"], s["best_lines"] = self.score, self.lines
            save_stats("blockfall", s)
        self._status()
        self.update()
        QTimer.singleShot(200, lambda: message(
            self.window.desktop, "Blockfall", f"Game over.\n\nScore: {self.score:,}\nLines: {self.lines}\n"
                                              f"High score: {max(best, self.score):,}\n\nPress F2 to play again."))

    def _status(self):
        self.window.status.setText(f"  Score: {self.score:,}     Lines: {self.lines}     Level: {self.level}"
                                   + ("     (Paused)" if self.paused else ""))

    # ---- drawing ------------------------------------------------------------------------------------
    def _block(self, p, x, y, kind, ghost=False):
        r = QRectF(8 + x * CELL, 8 + y * CELL, CELL, CELL)
        if ghost:
            p.setPen(QPen(QColor(COLORS[kind]), 1.5, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawRect(r.adjusted(2, 2, -2, -2))
            return
        base = QColor(COLORS[kind])
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, base.lighter(140))
        g.setColorAt(1, base.darker(130))
        p.setPen(QPen(base.darker(170), 1))
        p.setBrush(g)
        p.drawRect(r.adjusted(0.5, 0.5, -0.5, -0.5))
        p.setPen(QPen(QColor(255, 255, 255, 120), 1))
        p.drawLine(r.topLeft() + QPointF(3, 3), r.topRight() + QPointF(-3, 3))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#1A1E2A"))
        well = QRectF(8, 8, COLS * CELL, ROWS * CELL)
        p.fillRect(well, QColor("#0A0C14"))
        p.setPen(QPen(QColor("#1C2030"), 1))
        for c in range(1, COLS):
            p.drawLine(int(well.x() + c * CELL), int(well.top()), int(well.x() + c * CELL), int(well.bottom()))
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c]:
                    self._block(p, c, r, self.grid[r][c])
        if not self.over:
            gy = self.py
            while self.fits(self.px, gy + 1, self.turn):
                gy += 1
            for x, y in self.cells(self.px, gy, self.turn):
                if y >= 0:
                    self._block(p, x, y, self.kind, ghost=True)
            for x, y in self.cells():
                if y >= 0:
                    self._block(p, x, y, self.kind)
        p.setPen(QPen(QColor("#5A6A9A"), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRect(well)
        # the side panel: next piece and the numbers
        px = well.right() + 16
        p.setPen(QColor("#C8D0F0"))
        p.setFont(QFont("Tahoma", 9, QFont.Bold))
        p.drawText(QRectF(px, 12, PANEL - 10, 18), Qt.AlignLeft, "NEXT")
        box = QRectF(px, 32, 110, 70)
        p.setPen(QPen(QColor("#3A4468"), 1))
        p.setBrush(QColor("#0A0C14"))
        p.drawRect(box)
        nk = self.next_kind
        cells = SHAPES[nk]
        minx = min(x for x, _ in cells)
        maxx = max(x for x, _ in cells)
        miny = min(y for _, y in cells)
        maxy = max(y for _, y in cells)
        ox = box.center().x() - (maxx - minx + 1) * 9
        oy = box.center().y() - (maxy - miny + 1) * 9
        for x, y in cells:
            base = QColor(COLORS[nk])
            p.setPen(QPen(base.darker(170), 1))
            p.setBrush(base)
            p.drawRect(QRectF(ox + (x - minx) * 18, oy + (y - miny) * 18, 18, 18))
        p.setPen(QColor("#C8D0F0"))
        p.setFont(QFont("Tahoma", 9))
        for i, (label, value) in enumerate((("Score", f"{self.score:,}"), ("Lines", self.lines),
                                            ("Level", self.level), ("Best", f"{stats('blockfall').get('best', 0):,}"))):
            y = 120 + i * 44
            p.setFont(QFont("Tahoma", 8, QFont.Bold))
            p.drawText(QRectF(px, y, PANEL, 16), Qt.AlignLeft, label.upper())
            p.setFont(QFont("Tahoma", 13, QFont.Bold))
            p.drawText(QRectF(px, y + 14, PANEL, 22), Qt.AlignLeft, str(value))
        if self.paused or self.over or not self._active():
            text = "GAME OVER" if self.over else "PAUSED" if self.paused else "Click to play"
            p.fillRect(well, QColor(0, 0, 0, 140))
            p.setPen(QColor("#FFFFFF"))
            p.setFont(QFont("Tahoma", 14, QFont.Bold))
            p.drawText(well, Qt.AlignCenter, text)

    def mousePressEvent(self, event):
        self.setFocus()

    def stop(self):
        self.timer.stop()


def blockfall_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.fillRect(QRectF(2, 2, 28, 28), QColor("#0A0C14"))
    for (x, y, k) in ((1, 0, "T"), (0, 1, "T"), (1, 1, "T"), (2, 1, "T"), (0, 4, "I"), (1, 4, "I"), (2, 4, "I"),
                      (3, 4, "I"), (3, 3, "L"), (4, 3, "L"), (4, 4, "L"), (4, 2, "L"), (0, 3, "S"), (1, 3, "S")):
        p.setPen(QPen(QColor(COLORS[k]).darker(170), 1))
        p.setBrush(QColor(COLORS[k]))
        p.drawRect(QRectF(4 + x * 5, 4 + y * 5 + 2, 5, 5))
    p.end()
    return QIcon(pm)


HOW_TO = ("Fit the falling pieces together to make complete rows across the well. A full row disappears; clear "
          "four at once for the big score.\n\nLeft and Right move the piece, Up (or X) turns it, Z turns it the "
          "other way. Down drops it faster and Space drops it all the way.\n\nEvery ten rows the pieces fall "
          "faster. The game ends when the pile reaches the top. P pauses, F2 starts again.")


def open_blockfall(desktop):
    def make():
        win = GameWindow(desktop, Well)
        well = win.play
        game = win.menu.addMenu("&Game")
        game.addAction("&New Game", well.new_game, "F2")
        game.addAction("&Pause", well.toggle_pause, "P")
        game.addSeparator()
        game.addAction("E&xit", lambda: win.frame.request_close())
        help_menu = win.menu.addMenu("&Help")
        help_menu.addAction("&How to Play", lambda: message(desktop, "Blockfall", HOW_TO))
        return win
    win = open_game(desktop, "blockfall", "Blockfall", make, blockfall_icon(), None)
    win.content.play.setFocus()
    return win
