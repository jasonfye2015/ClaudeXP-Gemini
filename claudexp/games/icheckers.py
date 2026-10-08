"""Internet Checkers: English draughts on the Zone. Jumps are compulsory, multi-jumps continue, men reaching
the far row are crowned (and their turn ends). 80 moves with no capture is a draw. You play red (bottom)."""
import random

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QRadialGradient

from .zone import ZoneBoard, open_zone_game

DIRS = {"r": [(-1, -1), (-1, 1)], "b": [(1, -1), (1, 1)]}
KING_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
DEPTH = [1, 4, 8]


def owner(piece):
    return piece.lower() if piece else None


def initial():
    b = [[None] * 8 for _ in range(8)]
    for r in range(8):
        for c in range(8):
            if (r + c) % 2 == 1:
                if r < 3:
                    b[r][c] = "b"
                elif r > 4:
                    b[r][c] = "r"
    return b


def piece_dirs(piece):
    return KING_DIRS if piece.isupper() else DIRS[piece]


def jumps_from(b, r, c, piece, captured=()):
    """All jump sequences for the piece at (r, c): [(path, captured squares)]."""
    out = []
    for dr, dc in piece_dirs(piece):
        mr, mc, tr, tc = r + dr, c + dc, r + 2 * dr, c + 2 * dc
        if not (0 <= tr < 8 and 0 <= tc < 8):
            continue
        mid = b[mr][mc]
        if mid and owner(mid) != owner(piece) and (mr, mc) not in captured and b[tr][tc] is None:
            crowned = piece.islower() and (tr == 0 if piece == "r" else tr == 7)
            if crowned:
                out.append(([(r, c), (tr, tc)], captured + ((mr, mc),)))
                continue
            # move the piece temporarily to look for more jumps
            b[r][c], b[tr][tc] = None, piece
            more = jumps_from(b, tr, tc, piece, captured + ((mr, mc),))
            b[r][c], b[tr][tc] = piece, None
            if more:
                out += [([(r, c)] + path, caps) for path, caps in more]
            else:
                out.append(([(r, c), (tr, tc)], captured + ((mr, mc),)))
    return out


def legal_moves(b, side):
    jumps, steps = [], []
    for r in range(8):
        for c in range(8):
            p = b[r][c]
            if owner(p) != side:
                continue
            jumps += jumps_from(b, r, c, p)
            for dr, dc in piece_dirs(p):
                tr, tc = r + dr, c + dc
                if 0 <= tr < 8 and 0 <= tc < 8 and b[tr][tc] is None:
                    steps.append(([(r, c), (tr, tc)], ()))
    return jumps if jumps else steps


def apply(b, move):
    path, caps = move
    b = [row[:] for row in b]
    (r0, c0), (r1, c1) = path[0], path[-1]
    piece = b[r0][c0]
    b[r0][c0] = None
    for r, c in caps:
        b[r][c] = None
    if piece == "r" and r1 == 0 or piece == "b" and r1 == 7:
        piece = piece.upper()
    b[r1][c1] = piece
    return b


def evaluate(b, side):
    score = 0
    mine, theirs = [], []
    for r in range(8):
        for c in range(8):
            p = b[r][c]
            if not p:
                continue
            v = 160 if p.isupper() else 100 + (7 - r if p == "r" else r) * 3
            if 2 <= c <= 5 and 2 <= r <= 5:
                v += 4
            score += v if owner(p) == side else -v
            (mine if owner(p) == side else theirs).append((r, c, p))
    if score > 120 and theirs:
        # Ahead: hunt the remaining pieces down instead of shuffling kings around (avoids silly draws)
        for r, c, p in mine:
            if p.isupper():
                score -= 3 * min(max(abs(r - tr), abs(c - tc)) for tr, tc, _ in theirs)
    return score


def search(b, side, depth, alpha, beta):
    other = "r" if side == "b" else "b"
    moves = legal_moves(b, side)
    if not moves:
        return -10000 - depth, None
    if depth == 0:
        return evaluate(b, side), None
    best = None
    moves.sort(key=lambda m: -len(m[1]))
    for m in moves:
        val = -search(apply(b, m), other, depth - 1, -beta, -alpha)[0]
        if best is None or val > alpha:
            alpha, best = max(alpha, val), m
        if alpha >= beta:
            break
    return alpha, best


class CheckersBoard(ZoneBoard):
    HOW_TO = ("Move your red pieces diagonally forward onto empty dark squares. Jump over an opponent's piece to "
              "capture it; if you can jump, you must, and a piece keeps jumping while it can. A piece that reaches the "
              "far side is crowned king and can move backward too. Capture all your opponent's pieces, or leave them "
              "with no moves, to win.\n\nClick a piece, then click where it should go.")

    def __init__(self):
        super().__init__()
        self.board = initial()
        self.side = "r"
        self.selected = []          # the path built so far by the user's clicks
        self.quiet = 0              # moves since the last capture or crowning
        self.last = None
        self.setMinimumSize(400, 400)

    # ---- the ZoneBoard interface ----------------------------------------------------------------------------
    def start(self, user_first):
        self.board = initial()
        # red always moves first in this version of the Zone; whoever 'goes first' plays red at the bottom
        self.user_side = "r"
        self.side = "r" if user_first else "b"
        self.selected, self.quiet, self.last = [], 0, None
        self.update()

    def turn(self):
        return "user" if self.side == "r" else "ai"

    def result(self):
        if not legal_moves(self.board, self.side):
            return "ai" if self.side == "r" else "user"
        if self.quiet >= 80:
            return "draw"
        return None

    def score_text(self):
        reds = sum(1 for row in self.board for p in row if owner(p) == "r")
        blacks = sum(1 for row in self.board for p in row if owner(p) == "b")
        return f"Red pieces: {reds}    Black pieces: {blacks}"

    def ai_play(self, level):
        moves = legal_moves(self.board, "b")
        if not moves:
            return
        if level == 0 and random.random() < 0.35:
            move = random.choice(moves)
        else:
            _val, move = search(self.board, "b", DEPTH[level], -10 ** 9, 10 ** 9)
            move = move or random.choice(moves)
        self._play(move, "ai")

    # ---- moves ------------------------------------------------------------------------------------------------
    def _play(self, move, who):
        before = self.board[move[0][0][0]][move[0][0][1]]
        self.board = apply(self.board, move)
        after = self.board[move[0][-1][0]][move[0][-1][1]]
        crowned = before != after
        self.quiet = 0 if move[1] or crowned else self.quiet + 1
        self.last = move
        self.side = "b" if self.side == "r" else "r"
        self.selected = []
        self.update()
        self.moved.emit(who, {"captured": len(move[1]), "big": crowned})

    def square_at(self, pos):
        size = self.cell()
        x0, y0 = self.origin()
        c, r = int((pos.x() - x0) // size), int((pos.y() - y0) // size)
        return (r, c) if 0 <= r < 8 and 0 <= c < 8 else None

    def mousePressEvent(self, event):
        if self.locked or self.side != "r":
            return
        sq = self.square_at(event.position())
        if sq is None:
            return
        moves = legal_moves(self.board, "r")
        r, c = sq
        if owner(self.board[r][c]) == "r" and (not self.selected or len(self.selected) == 1):
            if any(m[0][0] == sq for m in moves):
                self.selected = [sq]
            self.update()
            return
        if not self.selected:
            return
        prefix = self.selected + [sq]
        matching = [m for m in moves if m[0][:len(prefix)] == prefix]
        if not matching:
            return
        complete = [m for m in matching if len(m[0]) == len(prefix)]
        if complete:
            self._play(complete[0], "user")
        else:
            self.selected = prefix      # a multi-jump continues from here
            self.update()

    # ---- drawing ------------------------------------------------------------------------------------------------
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
        hints = set()
        if not self.locked and self.side == "r":
            moves = legal_moves(self.board, "r")
            if self.selected:
                n = len(self.selected)
                hints = {m[0][n] for m in moves if m[0][:n] == self.selected and len(m[0]) > n}
            else:
                hints = {m[0][0] for m in moves}
        for r in range(8):
            for c in range(8):
                rect = QRectF(x0 + c * size, y0 + r * size, size, size)
                dark = (r + c) % 2 == 1
                p.fillRect(rect, QColor("#2E6B34") if dark else QColor("#F2E6C2"))
                if self.last and (r, c) in (self.last[0][0], self.last[0][-1]):
                    p.fillRect(rect, QColor(255, 255, 160, 70))
                if (r, c) in hints:
                    p.setPen(QPen(QColor("#FFE070"), 3))
                    p.setBrush(Qt.NoBrush)
                    p.drawRect(rect.adjusted(2, 2, -2, -2))
                if self.selected and (r, c) == self.selected[-1]:
                    p.setPen(QPen(QColor("#FFFFFF"), 3))
                    p.setBrush(Qt.NoBrush)
                    p.drawRect(rect.adjusted(2, 2, -2, -2))
                piece = self.board[r][c]
                if piece:
                    self._draw_piece(p, rect, piece)
        p.setPen(QPen(QColor("#1A3A1A"), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(x0, y0, size * 8, size * 8))
        self.paint_banner(p)

    @staticmethod
    def _draw_piece(p, rect, piece):
        r = rect.adjusted(rect.width() * 0.12, rect.height() * 0.12, -rect.width() * 0.12, -rect.height() * 0.12)
        base = QColor("#C81E1E") if owner(piece) == "r" else QColor("#202020")
        g = QRadialGradient(r.center() - QPointF(r.width() * 0.2, r.height() * 0.2), r.width() * 0.7)
        g.setColorAt(0, base.lighter(170))
        g.setColorAt(1, base)
        p.setPen(QPen(base.darker(160), 1.5))
        p.setBrush(g)
        p.drawEllipse(r)
        p.setPen(QPen(base.lighter(140), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(r.adjusted(r.width() * 0.16, r.height() * 0.16, -r.width() * 0.16, -r.height() * 0.16))
        if piece.isupper():
            crown = QColor("#FFD700")
            p.setPen(Qt.NoPen)
            p.setBrush(crown)
            cx, cy, s = r.center().x(), r.center().y(), r.width() * 0.22
            from PySide6.QtGui import QPolygonF
            p.drawPolygon(QPolygonF([QPointF(cx - s, cy + s * 0.6), QPointF(cx - s, cy - s * 0.5),
                                     QPointF(cx - s * 0.5, cy), QPointF(cx, cy - s * 0.8), QPointF(cx + s * 0.5, cy),
                                     QPointF(cx + s, cy - s * 0.5), QPointF(cx + s, cy + s * 0.6)]))


def checkers_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    for r in range(4):
        for c in range(4):
            p.fillRect(QRectF(2 + c * 7, 2 + r * 7, 7, 7), QColor("#2E6B34") if (r + c) % 2 else QColor("#F2E6C2"))
    p.setPen(QPen(QColor("#701010"), 1))
    p.setBrush(QColor("#D02020"))
    p.drawEllipse(QRectF(9, 16, 10, 10))
    p.setPen(QPen(QColor("black"), 1))
    p.setBrush(QColor("#303030"))
    p.drawEllipse(QRectF(16, 9, 10, 10))
    p.end()
    return QIcon(pm)


def open_internet_checkers(desktop):
    return open_zone_game(desktop, "Checkers", CheckersBoard, ("Red", "Black"), checkers_icon())
