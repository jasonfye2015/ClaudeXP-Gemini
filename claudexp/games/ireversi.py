"""Internet Reversi on the Zone: place a disc so it brackets a line of your opponent's discs and they flip to your
colour. No move? You pass. When neither player can move, the most discs wins. Black moves first."""
import random

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QRadialGradient

from .zone import ZoneBoard, open_zone_game

DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
WEIGHTS = [[120, -20, 20, 5, 5, 20, -20, 120],
           [-20, -40, -5, -5, -5, -5, -40, -20],
           [20, -5, 15, 3, 3, 15, -5, 20],
           [5, -5, 3, 3, 3, 3, -5, 5],
           [5, -5, 3, 3, 3, 3, -5, 5],
           [20, -5, 15, 3, 3, 15, -5, 20],
           [-20, -40, -5, -5, -5, -5, -40, -20],
           [120, -20, 20, 5, 5, 20, -20, 120]]
DEPTH = [1, 3, 4]


def initial():
    b = [[None] * 8 for _ in range(8)]
    b[3][3] = b[4][4] = "W"
    b[3][4] = b[4][3] = "B"
    return b


def flips(b, r, c, side):
    if b[r][c] is not None:
        return []
    other = "W" if side == "B" else "B"
    out = []
    for dr, dc in DIRS:
        line = []
        rr, cc = r + dr, c + dc
        while 0 <= rr < 8 and 0 <= cc < 8 and b[rr][cc] == other:
            line.append((rr, cc))
            rr, cc = rr + dr, cc + dc
        if line and 0 <= rr < 8 and 0 <= cc < 8 and b[rr][cc] == side:
            out += line
    return out


def legal(b, side):
    return {(r, c): f for r in range(8) for c in range(8) if (f := flips(b, r, c, side))}


def apply(b, r, c, side, flipped):
    b = [row[:] for row in b]
    b[r][c] = side
    for rr, cc in flipped:
        b[rr][cc] = side
    return b


def evaluate(b, side):
    other = "W" if side == "B" else "B"
    score = 0
    for r in range(8):
        for c in range(8):
            if b[r][c] == side:
                score += WEIGHTS[r][c]
            elif b[r][c] == other:
                score -= WEIGHTS[r][c]
    mobility = len(legal(b, side)) - len(legal(b, other))
    return score + mobility * 5


def search(b, side, depth, alpha, beta):
    other = "W" if side == "B" else "B"
    moves = legal(b, side)
    if depth == 0 or (not moves and not legal(b, other)):
        if not moves and not legal(b, other):
            mine = sum(row.count(side) for row in b)
            theirs = sum(row.count(other) for row in b)
            return (mine - theirs) * 1000, None
        return evaluate(b, side), None
    if not moves:
        return -search(b, other, depth - 1, -beta, -alpha)[0], None
    best = None
    for (r, c), f in sorted(moves.items(), key=lambda kv: -WEIGHTS[kv[0][0]][kv[0][1]]):
        val = -search(apply(b, r, c, side, f), other, depth - 1, -beta, -alpha)[0]
        if best is None or val > alpha:
            alpha, best = max(alpha, val), (r, c)
        if alpha >= beta:
            break
    return alpha, best


class ReversiBoard(ZoneBoard):
    HOW_TO = ("Place a disc next to your opponent's discs so that a straight line of theirs (across, down or "
              "diagonal) is trapped between your new disc and another of yours. The trapped discs flip to your "
              "colour. If you can't move, you pass. When neither player can move, whoever has more discs wins.\n\n"
              "Small dots show where you can play.")

    def __init__(self):
        super().__init__()
        self.board = initial()
        self.user_color = "B"
        self.side = "B"
        self.last = None
        self.passed = ""
        self.setMinimumSize(400, 400)

    def start(self, user_first):
        self.board = initial()
        self.user_color = "B" if user_first else "W"     # black always moves first
        self.side = "B"
        self.last, self.passed = None, ""
        self._skip_if_stuck()
        self.update()

    def colors(self):
        return ("Black", "White") if self.user_color == "B" else ("White", "Black")

    def ai_color(self):
        return "W" if self.user_color == "B" else "B"

    def turn(self):
        return "user" if self.side == self.user_color else "ai"

    def result(self):
        if legal(self.board, "B") or legal(self.board, "W"):
            return None
        mine = sum(row.count(self.user_color) for row in self.board)
        theirs = sum(row.count(self.ai_color()) for row in self.board)
        return "user" if mine > theirs else "ai" if theirs > mine else "draw"

    def score_text(self):
        b = sum(row.count("B") for row in self.board)
        w = sum(row.count("W") for row in self.board)
        text = f"Black: {b}    White: {w}"
        return text + (f"\n{self.passed}" if self.passed else "")

    def ai_play(self, level):
        moves = legal(self.board, self.side)
        if not moves:
            return
        if level == 0 and random.random() < 0.4:
            r, c = random.choice(list(moves))
        else:
            _v, best = search(self.board, self.side, DEPTH[level], -10 ** 9, 10 ** 9)
            r, c = best or random.choice(list(moves))
        self._play(r, c, moves[(r, c)], "ai")

    def _play(self, r, c, flipped, who):
        self.board = apply(self.board, r, c, self.side, flipped)
        self.last = (r, c)
        corner = (r, c) in ((0, 0), (0, 7), (7, 0), (7, 7))
        self.side = "W" if self.side == "B" else "B"
        self.passed = ""
        self._skip_if_stuck()
        self.update()
        self.moved.emit(who, {"captured": len(flipped) // 3, "big": corner})

    def _skip_if_stuck(self):
        """A player with no legal move passes (unless the game is over)."""
        if not legal(self.board, self.side) and legal(self.board, "W" if self.side == "B" else "B"):
            who = "You have" if self.side == self.user_color else "Your opponent has"
            self.passed = f"{who} no moves and must pass."
            self.side = "W" if self.side == "B" else "B"

    def mousePressEvent(self, event):
        if self.locked or self.side != self.user_color:
            return
        size = self.cell()
        x0, y0 = self.origin()
        c, r = int((event.position().x() - x0) // size), int((event.position().y() - y0) // size)
        if not (0 <= r < 8 and 0 <= c < 8):
            return
        f = flips(self.board, r, c, self.side)
        if f:
            self._play(r, c, f, "user")

    def cell(self):
        return min(self.width(), self.height()) // 8

    def origin(self):
        s = self.cell() * 8
        return (self.width() - s) // 2, (self.height() - s) // 2

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#3B6EA5"))
        size = self.cell()
        x0, y0 = self.origin()
        p.fillRect(QRectF(x0, y0, size * 8, size * 8), QColor("#1E8C3A"))
        p.setPen(QPen(QColor("#0D4D1E"), 1.5))
        for i in range(9):
            p.drawLine(QPointF(x0 + i * size, y0), QPointF(x0 + i * size, y0 + 8 * size))
            p.drawLine(QPointF(x0, y0 + i * size), QPointF(x0 + 8 * size, y0 + i * size))
        hints = legal(self.board, self.side) if not self.locked and self.side == self.user_color else {}
        for r in range(8):
            for c in range(8):
                rect = QRectF(x0 + c * size, y0 + r * size, size, size)
                disc = self.board[r][c]
                if disc:
                    d = rect.adjusted(size * 0.1, size * 0.1, -size * 0.1, -size * 0.1)
                    base = QColor("#101010") if disc == "B" else QColor("#F4F4F4")
                    g = QRadialGradient(d.center() - QPointF(d.width() * 0.2, d.height() * 0.25), d.width() * 0.75)
                    g.setColorAt(0, base.lighter(250) if disc == "B" else QColor("white"))
                    g.setColorAt(1, base if disc == "B" else QColor("#C8C8C8"))
                    p.setPen(QPen(QColor("#000000") if disc == "B" else QColor("#A0A0A0"), 1))
                    p.setBrush(g)
                    p.drawEllipse(d)
                    if (r, c) == self.last:
                        p.setPen(Qt.NoPen)
                        p.setBrush(QColor("#E03030"))
                        p.drawEllipse(d.center(), size * 0.06, size * 0.06)
                elif (r, c) in hints:
                    p.setPen(Qt.NoPen)
                    p.setBrush(QColor(0, 0, 0, 70) if self.user_color == "B" else QColor(255, 255, 255, 110))
                    p.drawEllipse(rect.center(), size * 0.09, size * 0.09)
        self.paint_banner(p)


def reversi_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(QRectF(2, 2, 28, 28), QColor("#1E8C3A"))
    p.setPen(QPen(QColor("#0D4D1E"), 1))
    for i in range(3):
        p.drawLine(2 + i * 14, 2, 2 + i * 14, 30)
        p.drawLine(2, 2 + i * 14, 30, 2 + i * 14)
    for (x, y), col in (((4, 4), "#101010"), ((18, 4), "#F4F4F4"), ((4, 18), "#F4F4F4"), ((18, 18), "#101010")):
        p.setBrush(QColor(col))
        p.setPen(QPen(QColor("#505050"), 1))
        p.drawEllipse(QRectF(x, y, 10, 10))
    p.end()
    return QIcon(pm)


def open_internet_reversi(desktop):
    return open_zone_game(desktop, "Reversi", lambda _w: ReversiBoard(), ("Black", "White"), reversi_icon())
