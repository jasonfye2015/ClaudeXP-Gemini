"""Minesweeper, like Windows XP's: Beginner / Intermediate / Expert / Custom, red LED counters, the smiley,
flags and question marks, chording (both buttons or middle click), a safe first click, and Best Times."""
import random

from PySide6.QtCore import QPoint, QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QFont, QPainter, QPen, QPolygon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QGridLayout, QVBoxLayout, QWidget

from .. import sound
from .common import GameWindow, message, mine_icon, open_game, save_stats, stats

CELL = 16
BORDER = 12
HEADER = 37
LEVELS = {"beginner": (9, 9, 10), "intermediate": (16, 16, 40), "expert": (30, 16, 99)}
NUMBER_COLORS = {1: "#0000FF", 2: "#008000", 3: "#FF0000", 4: "#000080",
                 5: "#800000", 6: "#008080", 7: "#000000", 8: "#808080"}
GRAY = QColor("#C0C0C0")
LIGHT = QColor("white")
DARK = QColor("#808080")


def bevel(p, rect, width, raised=True):
    a, b = (LIGHT, DARK) if raised else (DARK, LIGHT)
    for i in range(width):
        r = rect.adjusted(i, i, -i - 1, -i - 1)
        p.setPen(a)
        p.drawLine(r.topLeft(), r.topRight())
        p.drawLine(r.topLeft(), r.bottomLeft())
        p.setPen(b)
        p.drawLine(r.bottomLeft(), r.bottomRight())
        p.drawLine(r.topRight(), r.bottomRight())


# Seven-segment digits: segments a b c d e f g
SEGMENTS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
            "7": "abc", "8": "abcdefg", "9": "abcdfg", "-": "g"}


def draw_led(p, x, y, value):
    """Three red seven-segment digits on black, like the mine counter and the clock."""
    p.fillRect(x, y, 41, 25, QColor("black"))
    p.setPen(DARK)
    p.drawLine(x, y, x + 40, y)
    p.drawLine(x, y, x, y + 24)
    p.setPen(LIGHT)
    p.drawLine(x, y + 24, x + 40, y + 24)
    p.drawLine(x + 40, y, x + 40, y + 24)
    value = max(-99, min(999, value))
    text = f"{value:03d}" if value >= 0 else f"-{-value:02d}"
    on, off = QColor("#FF0000"), QColor("#400000")
    for k, ch in enumerate(text):
        dx = x + 2 + k * 13
        lit = SEGMENTS.get(ch, "")
        segs = {"a": QRect(dx + 2, y + 2, 7, 2), "g": QRect(dx + 2, y + 11, 7, 2), "d": QRect(dx + 2, y + 20, 7, 2),
                "f": QRect(dx, y + 3, 2, 8), "b": QRect(dx + 9, y + 3, 2, 8),
                "e": QRect(dx, y + 13, 2, 8), "c": QRect(dx + 9, y + 13, 2, 8)}
        for name, r in segs.items():
            p.fillRect(r, on if name in lit else off)


class Board(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        s = stats("minesweeper")
        self.level = s.get("level", "beginner")
        self.custom = tuple(s.get("custom", (9, 9, 10)))
        self.marks = bool(s.get("marks", True))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.pressed = set()         # cells shown sunken while a button is held
        self.buttons = Qt.NoButton
        self.face_down = False
        self.new_game()

    # ---- setup ---------------------------------------------------------------------------------------
    def dims(self):
        return self.custom if self.level == "custom" else LEVELS[self.level]

    def new_game(self):
        self.cols, self.rows, self.mines = self.dims()
        self.mine = [[False] * self.cols for _ in range(self.rows)]
        self.state = [["hidden"] * self.cols for _ in range(self.rows)]   # hidden, open, flag, mark
        self.placed = False
        self.over = None             # None, "won", "lost"
        self.blast = None
        self.seconds = 0
        self.timer.stop()
        size = QSize(self.cols * CELL + 2 * BORDER, self.rows * CELL + HEADER + BORDER + 2 * 3 + 6)
        self.setFixedSize(size)
        if self.win.frame is not None:
            self.win.fit()
        self.update()

    def stop(self):
        self.timer.stop()

    def _place(self, safe_r, safe_c):
        """Mines go anywhere but the first cell clicked (XP moves a mine away from the first click)."""
        spots = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) != (safe_r, safe_c)]
        for r, c in random.sample(spots, min(self.mines, len(spots))):
            self.mine[r][c] = True
        self.placed = True

    def _tick(self):
        if self.seconds < 999:
            self.seconds += 1
        self.update()

    # ---- geometry -----------------------------------------------------------------------------------------
    def field_rect(self):
        return QRect(BORDER, HEADER + BORDER // 2 + 6, self.cols * CELL, self.rows * CELL)

    def face_rect(self):
        return QRect(self.width() // 2 - 13, BORDER // 2 + 6 + 6, 26, 26)

    def cell_at(self, pos):
        f = self.field_rect()
        if not f.contains(pos):
            return None
        return (pos.y() - f.y()) // CELL, (pos.x() - f.x()) // CELL

    def neighbours(self, r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (dr or dc) and 0 <= rr < self.rows and 0 <= cc < self.cols:
                    yield rr, cc

    def count(self, r, c):
        return sum(self.mine[rr][cc] for rr, cc in self.neighbours(r, c))

    def flags_left(self):
        return self.mines - sum(row.count("flag") for row in self.state)

    # ---- moves -------------------------------------------------------------------------------------------------
    def reveal(self, r, c):
        if self.state[r][c] not in ("hidden", "mark"):
            return
        if not self.placed:
            self._place(r, c)
            self.timer.start(1000)
            self.seconds = 1
        if self.mine[r][c]:
            self._lose(r, c)
            return
        stack = [(r, c)]
        while stack:
            r, c = stack.pop()
            if self.state[r][c] not in ("hidden", "mark"):
                continue
            self.state[r][c] = "open"
            if self.count(r, c) == 0:
                stack.extend(n for n in self.neighbours(r, c) if self.state[n[0]][n[1]] in ("hidden", "mark"))
        self._check_win()

    def chord(self, r, c):
        if self.state[r][c] != "open":
            return
        around = list(self.neighbours(r, c))
        if sum(self.state[rr][cc] == "flag" for rr, cc in around) != self.count(r, c):
            return
        for rr, cc in around:
            if self.state[rr][cc] in ("hidden", "mark") and not self.over:
                self.reveal(rr, cc)

    def toggle_flag(self, r, c):
        st = self.state[r][c]
        if st == "hidden":
            self.state[r][c] = "flag"
        elif st == "flag":
            self.state[r][c] = "mark" if self.marks else "hidden"
        elif st == "mark":
            self.state[r][c] = "hidden"

    def _lose(self, r, c):
        self.over, self.blast = "lost", (r, c)
        self.timer.stop()

    def _check_win(self):
        hidden = sum(st != "open" for row in self.state for st in row)
        if hidden == self.mines and not self.over:
            self.over = "won"
            self.timer.stop()
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.mine[r][c]:
                        self.state[r][c] = "flag"
            if self.level != "custom":
                best = stats("minesweeper").get("best", {})
                if self.seconds < best.get(self.level, {}).get("time", 999):
                    QTimer.singleShot(50, lambda: _ask_name(self.win.desktop, self.level, self.seconds))

    # ---- mouse -----------------------------------------------------------------------------------------------------
    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        self.buttons = event.buttons()
        if self.face_rect().contains(pos) and event.button() == Qt.LeftButton:
            self.face_down = True
            self.update()
            return
        if self.over:
            return
        cell = self.cell_at(pos)
        if event.button() == Qt.RightButton and not (self.buttons & Qt.LeftButton):
            if cell:
                self.toggle_flag(*cell)
                self.update()
            return
        self._press_at(pos)

    def mouseMoveEvent(self, event):
        if not self.over and self.buttons & (Qt.LeftButton | Qt.MiddleButton) and not self.face_down:
            self._press_at(event.position().toPoint())

    def _chording(self):
        return (self.buttons & Qt.LeftButton and self.buttons & Qt.RightButton) or self.buttons & Qt.MiddleButton

    def _press_at(self, pos):
        cell = self.cell_at(pos)
        self.pressed = set()
        if cell and (self.buttons & (Qt.LeftButton | Qt.MiddleButton)):
            group = [cell, *self.neighbours(*cell)] if self._chording() else [cell]
            self.pressed = {rc for rc in group if self.state[rc[0]][rc[1]] in ("hidden", "mark")}
        self.update()

    def mouseReleaseEvent(self, event):
        pos = event.position().toPoint()
        buttons, self.buttons = self.buttons, event.buttons()
        self.pressed = set()
        if self.face_down:
            self.face_down = False
            if self.face_rect().contains(pos):
                self.new_game()
            self.update()
            return
        if self.over:
            return
        cell = self.cell_at(pos)
        if cell:
            both = (buttons & Qt.LeftButton and buttons & Qt.RightButton) or buttons & Qt.MiddleButton
            if both:
                self.chord(*cell)
                self.buttons = Qt.NoButton      # don't also reveal when the second button comes up
            elif event.button() == Qt.LeftButton and buttons & Qt.LeftButton:
                if self.state[cell[0]][cell[1]] == "open":
                    pass
                else:
                    self.reveal(*cell)
        self.update()

    # ---- painting ------------------------------------------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), GRAY)
        bevel(p, self.rect(), 3, raised=True)
        header = QRect(BORDER - 3, BORDER // 2 + 3, self.cols * CELL + 6, HEADER)
        bevel(p, header, 2, raised=False)
        draw_led(p, header.x() + 7, header.y() + 6, self.flags_left())
        draw_led(p, header.right() - 7 - 40, header.y() + 6, self.seconds)
        self._paint_face(p)
        f = self.field_rect()
        bevel(p, f.adjusted(-3, -3, 3, 3), 3, raised=False)
        font = QFont("Tahoma")
        font.setPixelSize(12)
        font.setBold(True)
        p.setFont(font)
        for r in range(self.rows):
            for c in range(self.cols):
                self._paint_cell(p, QRect(f.x() + c * CELL, f.y() + r * CELL, CELL, CELL), r, c)

    def _paint_cell(self, p, rect, r, c):
        st = self.state[r][c]
        lost = self.over == "lost"
        if st == "open" or (r, c) in self.pressed or (lost and self.mine[r][c] and st != "flag"):
            p.fillRect(rect, GRAY)
            p.setPen(DARK)
            p.drawLine(rect.topLeft(), rect.topRight())
            p.drawLine(rect.topLeft(), rect.bottomLeft())
            if lost and self.mine[r][c] and st != "open":
                if (r, c) == self.blast:
                    p.fillRect(rect.adjusted(1, 1, 0, 0), QColor("red"))
                self._paint_mine(p, rect)
            elif st == "open":
                n = self.count(r, c)
                if self.mine[r][c]:
                    p.fillRect(rect.adjusted(1, 1, 0, 0), QColor("red"))
                    self._paint_mine(p, rect)
                elif n:
                    p.setPen(QColor(NUMBER_COLORS[n]))
                    p.drawText(rect, Qt.AlignCenter, str(n))
            return
        p.fillRect(rect, GRAY)
        bevel(p, rect, 2, raised=True)
        if st == "flag":
            if lost and not self.mine[r][c]:
                self._paint_mine(p, rect)
                p.setPen(QPen(QColor("red"), 2))
                p.drawLine(rect.topLeft() + QPoint(3, 3), rect.bottomRight() - QPoint(3, 3))
                p.drawLine(rect.topRight() + QPoint(-3, 3), rect.bottomLeft() + QPoint(3, -3))
            else:
                self._paint_flag(p, rect)
        elif st == "mark":
            p.setPen(QColor("black"))
            p.drawText(rect, Qt.AlignCenter, "?")

    @staticmethod
    def _paint_mine(p, rect):
        cx, cy = rect.center().x() + 1, rect.center().y() + 1
        p.setPen(QPen(QColor("black"), 1))
        p.drawLine(cx - 6, cy, cx + 6, cy)
        p.drawLine(cx, cy - 6, cx, cy + 6)
        p.drawLine(cx - 4, cy - 4, cx + 4, cy + 4)
        p.drawLine(cx - 4, cy + 4, cx + 4, cy - 4)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("black"))
        p.drawEllipse(QPoint(cx, cy), 4, 4)
        p.setBrush(QColor("white"))
        p.drawRect(cx - 2, cy - 2, 2, 2)
        p.setBrush(Qt.NoBrush)

    @staticmethod
    def _paint_flag(p, rect):
        x, y = rect.x(), rect.y()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("red"))
        p.drawPolygon(QPolygon([QPoint(x + 9, y + 3), QPoint(x + 9, y + 9), QPoint(x + 4, y + 6)]))
        p.setBrush(QColor("black"))
        p.drawRect(x + 9, y + 3, 1, 8)
        p.drawRect(x + 6, y + 11, 6, 1)
        p.drawRect(x + 4, y + 12, 9, 2)
        p.setBrush(Qt.NoBrush)

    def _paint_face(self, p):
        r = self.face_rect()
        p.fillRect(r, GRAY)
        p.setPen(DARK)
        p.drawRect(r.adjusted(0, 0, -1, -1))
        bevel(p, r.adjusted(1, 1, -1, -1), 2, raised=not self.face_down)
        off = 1 if self.face_down else 0
        p.setRenderHint(QPainter.Antialiasing)
        c = QRectF(r.x() + 4 + off, r.y() + 4 + off, 17, 17)
        p.setPen(QPen(QColor("black"), 1))
        p.setBrush(QColor("#FFFF00"))
        p.drawEllipse(c)
        cx, cy = c.center().x(), c.center().y()
        worried = bool(self.pressed) and not self.over
        if self.over == "won":
            p.setBrush(QColor("black"))          # sunglasses
            p.drawRect(QRectF(cx - 6, cy - 3, 5, 3))
            p.drawRect(QRectF(cx + 1, cy - 3, 5, 3))
            p.drawLine(QPoint(int(cx - 8), int(cy - 3)), QPoint(int(cx + 8), int(cy - 3)))
        elif self.over == "lost":
            for ex in (cx - 3.5, cx + 3.5):     # x eyes
                p.drawLine(QPoint(int(ex - 1.5), int(cy - 4.5)), QPoint(int(ex + 1.5), int(cy - 1.5)))
                p.drawLine(QPoint(int(ex - 1.5), int(cy - 1.5)), QPoint(int(ex + 1.5), int(cy - 4.5)))
        else:
            p.setBrush(QColor("black"))
            p.drawEllipse(QRectF(cx - 4.5, cy - 4, 2, 2.5 if not worried else 3))
            p.drawEllipse(QRectF(cx + 2.5, cy - 4, 2, 2.5 if not worried else 3))
        p.setBrush(Qt.NoBrush)
        if worried:
            p.drawEllipse(QRectF(cx - 2, cy + 2, 4, 4))
        elif self.over == "lost":
            p.drawArc(QRectF(cx - 4, cy + 3, 8, 6), 0, 180 * 16)
        else:
            p.drawArc(QRectF(cx - 4.5, cy - 1, 9, 6), 200 * 16, 140 * 16)
        p.setRenderHint(QPainter.Antialiasing, False)


# ---- dialogs -------------------------------------------------------------------------------------------------------------

def _best(level):
    return stats("minesweeper").get("best", {}).get(level, {"time": 999, "name": "Anonymous"})


def _save_setting(**values):
    s = stats("minesweeper")
    s.update(values)
    save_stats("minesweeper", s)


def _ask_name(desktop, level, seconds):
    from ..network import DialogBody, _fixed_window
    from .. import user
    body = DialogBody()
    v = QVBoxLayout(body)
    v.addWidget(QLabel(f"You have the fastest time\nfor {level} level.\nPlease type your name.", alignment=Qt.AlignCenter))
    edit = QLineEdit(user.user_name() if hasattr(user, "user_name") else "Anonymous")
    v.addWidget(edit)
    ok = QPushButton("OK")
    ok.setFixedSize(75, 23)
    v.addWidget(ok, alignment=Qt.AlignCenter)
    body.setFixedWidth(200)
    holder = {}

    def done():
        s = stats("minesweeper")
        s.setdefault("best", {})[level] = {"time": seconds, "name": edit.text().strip() or "Anonymous"}
        save_stats("minesweeper", s)
        desktop.close_window(holder.pop("win"))
        _best_times(desktop)

    ok.clicked.connect(done)
    edit.returnPressed.connect(done)
    holder["win"] = _fixed_window(desktop, "Congratulations", body, done)
    desktop.open_window(holder["win"])
    edit.selectAll()
    edit.setFocus()


def _best_times(desktop):
    lines = []
    for level in ("beginner", "intermediate", "expert"):
        b = _best(level)
        lines.append(f"{level.title() + ':':<15}{b['time']} second{'' if b['time'] == 1 else 's'}    {b['name']}")
    message(desktop, "Fastest Mine Sweepers", "\n".join(lines))


def _custom(desktop, board):
    from ..network import DialogBody, _fixed_window
    body = DialogBody()
    grid = QGridLayout(body)
    spins = []
    for i, (label, value, lo, hi) in enumerate((("&Height:", board.custom[1], 9, 24), ("&Width:", board.custom[0], 9, 30),
                                                 ("&Mines:", board.custom[2], 10, 667))):
        lab = QLabel(label)
        spin = QSpinBox()
        spin.setRange(lo, hi)
        spin.setValue(value)
        lab.setBuddy(spin)
        grid.addWidget(lab, i, 0)
        grid.addWidget(spin, i, 1)
        spins.append(spin)
    ok, cancel = QPushButton("OK"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(75, 23)
    grid.addWidget(ok, 0, 2)
    grid.addWidget(cancel, 1, 2)
    holder = {}

    def close():
        if holder.get("win") is not None:
            desktop.close_window(holder.pop("win"))

    def accept():
        h, w, m = (s.value() for s in spins)
        m = max(10, min(m, (w - 1) * (h - 1)))
        board.custom, board.level = (w, h, m), "custom"
        _save_setting(custom=[w, h, m], level="custom")
        close()
        board.win.sync_level()
        board.new_game()

    ok.clicked.connect(accept)
    cancel.clicked.connect(close)
    holder["win"] = _fixed_window(desktop, "Custom Field", body, close)
    desktop.open_window(holder["win"])


def open_minesweeper(desktop):
    def make():
        win = GameWindow(desktop, Board, status=False)
        board = win.play
        game_menu = win.menu.addMenu("&Game")
        game_menu.addAction("&New", board.new_game, "F2")
        game_menu.addSeparator()
        group = QActionGroup(win)
        acts = {}

        def set_level(level):
            board.level = level
            _save_setting(level=level)
            board.new_game()

        for level, label in (("beginner", "&Beginner"), ("intermediate", "&Intermediate"), ("expert", "&Expert")):
            act = QAction(label, win, checkable=True)
            act.triggered.connect(lambda _c=False, lv=level: set_level(lv))
            group.addAction(act)
            game_menu.addAction(act)
            acts[level] = act
        custom = QAction("&Custom...", win, checkable=True)
        custom.triggered.connect(lambda: (win.sync_level(), _custom(desktop, board)))
        group.addAction(custom)
        game_menu.addAction(custom)
        acts["custom"] = custom

        def sync_level():
            acts[board.level].setChecked(True)

        win.sync_level = sync_level
        sync_level()
        game_menu.addSeparator()
        marks = QAction("&Marks (?)", win, checkable=True, checked=board.marks)
        marks.triggered.connect(lambda on: (setattr(board, "marks", on), _save_setting(marks=on)))
        game_menu.addAction(marks)
        game_menu.addSeparator()
        game_menu.addAction("Best &Times...", lambda: _best_times(desktop))
        game_menu.addSeparator()
        game_menu.addAction("E&xit", lambda: win.frame.request_close())
        help_menu = win.menu.addMenu("&Help")
        help_menu.addAction("&How to Play", lambda: message(desktop, "Minesweeper", HOW_TO))
        return win

    return open_game(desktop, "minesweeper", "Minesweeper", make, mine_icon(), None)


HOW_TO = ("Find the mines without stepping on one.\n\n"
          "Click a square to uncover it. A number tells you how many mines touch that square. Right-click to "
          "plant a flag where you think a mine is (right-click again for a question mark).\n\n"
          "If a number already has that many flags around it, click it with both mouse buttons (or the middle "
          "button) to uncover all the squares around it.\n\nClick the smiley to start over.")
