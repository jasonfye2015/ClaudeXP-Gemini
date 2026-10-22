"""Chess Titans: chess against the computer on a wooden board, as Windows 7 shipped it. Three strengths of
opponent, full rules (castling, en passant, promotion, check, checkmate, stalemate, the fifty-move rule), undo, play
as White or Black, and your record in the Statistics. The computer thinks on its own thread."""
import random
import threading

from PySide6.QtCore import QObject, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import QWidget

from .. import sound

GLYPHS = {"K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
          "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"}
VALUES = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20000}
START = "rnbqkbnr" "pppppppp" "........" "........" "........" "........" "PPPPPPPP" "RNBQKBNR"
KNIGHT = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
KING = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
BISHOP = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK = [(-1, 0), (1, 0), (0, -1), (0, 1)]
LEVELS = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
# piece-square bonuses (from White's side; mirrored for Black), one row per rank from the top
PST = {
    "P": [0, 0, 0, 0, 0, 0, 0, 0, 50, 50, 50, 50, 50, 50, 50, 50, 10, 10, 20, 30, 30, 20, 10, 10, 5, 5, 10, 25, 25, 10, 5, 5,
          0, 0, 0, 20, 20, 0, 0, 0, 5, -5, -10, 0, 0, -10, -5, 5, 5, 10, 10, -20, -20, 10, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0],
    "N": [-50, -40, -30, -30, -30, -30, -40, -50, -40, -20, 0, 0, 0, 0, -20, -40, -30, 0, 10, 15, 15, 10, 0, -30,
          -30, 5, 15, 20, 20, 15, 5, -30, -30, 0, 15, 20, 20, 15, 0, -30, -30, 5, 10, 15, 15, 10, 5, -30,
          -40, -20, 0, 5, 5, 0, -20, -40, -50, -40, -30, -30, -30, -30, -40, -50],
    "B": [-20, -10, -10, -10, -10, -10, -10, -20, -10, 0, 0, 0, 0, 0, 0, -10, -10, 0, 5, 10, 10, 5, 0, -10,
          -10, 5, 5, 10, 10, 5, 5, -10, -10, 0, 10, 10, 10, 10, 0, -10, -10, 10, 10, 10, 10, 10, 10, -10,
          -10, 5, 0, 0, 0, 0, 5, -10, -20, -10, -10, -10, -10, -10, -10, -20],
    "R": [0, 0, 0, 0, 0, 0, 0, 0, 5, 10, 10, 10, 10, 10, 10, 5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5,
          -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, 0, 0, 0, 5, 5, 0, 0, 0],
    "Q": [-20, -10, -10, -5, -5, -10, -10, -20, -10, 0, 0, 0, 0, 0, 0, -10, -10, 0, 5, 5, 5, 5, 0, -10,
          -5, 0, 5, 5, 5, 5, 0, -5, 0, 0, 5, 5, 5, 5, 0, -5, -10, 5, 5, 5, 5, 5, 0, -10, -10, 0, 5, 0, 0, 0, 0, -10,
          -20, -10, -10, -5, -5, -10, -10, -20],
    "K": [-30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30,
          -30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30,
          -20, -30, -30, -40, -40, -30, -30, -20, -10, -20, -20, -20, -20, -20, -20, -10,
          20, 20, 0, 0, 0, 0, 20, 20, 20, 30, 10, 0, 0, 10, 30, 20],
}


def _white(p):
    return p.isupper()


class Position:
    """The board (index 0 is a8, 63 is h1), whose turn, castling rights, the en passant square, move counters."""

    def __init__(self, board=None, turn="w", castling="KQkq", ep=None, halfmove=0, fullmove=1):
        self.board = list(board) if board is not None else list(START)
        self.turn, self.castling, self.ep, self.halfmove, self.fullmove = turn, castling, ep, halfmove, fullmove

    def copy(self):
        return Position(self.board, self.turn, self.castling, self.ep, self.halfmove, self.fullmove)

    def king(self, white):
        return self.board.index("K" if white else "k")

    def attacked(self, sq, by_white):
        """Is sq attacked by the given side?"""
        b = self.board
        r, c = divmod(sq, 8)
        pr = r + 1 if by_white else r - 1
        for dc in (-1, 1):
            if 0 <= pr < 8 and 0 <= c + dc < 8 and b[pr * 8 + c + dc] == ("P" if by_white else "p"):
                return True
        for dr, dc in KNIGHT:
            rr, cc = r + dr, c + dc
            if 0 <= rr < 8 and 0 <= cc < 8 and b[rr * 8 + cc] == ("N" if by_white else "n"):
                return True
        for dr, dc in KING:
            rr, cc = r + dr, c + dc
            if 0 <= rr < 8 and 0 <= cc < 8 and b[rr * 8 + cc] == ("K" if by_white else "k"):
                return True
        for dirs, kinds in ((BISHOP, "BQ"), (ROOK, "RQ")):
            kinds = kinds if by_white else kinds.lower()
            for dr, dc in dirs:
                rr, cc = r + dr, c + dc
                while 0 <= rr < 8 and 0 <= cc < 8:
                    p = b[rr * 8 + cc]
                    if p != ".":
                        if p in kinds:
                            return True
                        break
                    rr, cc = rr + dr, cc + dc
        return False

    def in_check(self):
        white = self.turn == "w"
        return self.attacked(self.king(white), not white)

    def pseudo_moves(self):
        b = self.board
        white = self.turn == "w"
        out = []
        for sq, p in enumerate(b):
            if p == "." or _white(p) != white:
                continue
            r, c = divmod(sq, 8)
            kind = p.upper()
            if kind == "P":
                step = -1 if white else 1
                start = 6 if white else 1
                last = 0 if white else 7
                rr = r + step
                if 0 <= rr < 8 and b[rr * 8 + c] == ".":
                    promos = "QRBN" if rr == last else (None,)
                    for pm in promos:
                        out.append((sq, rr * 8 + c, pm))
                    if r == start and b[(r + 2 * step) * 8 + c] == ".":
                        out.append((sq, (r + 2 * step) * 8 + c, None))
                for dc in (-1, 1):
                    cc = c + dc
                    if 0 <= rr < 8 and 0 <= cc < 8:
                        t = rr * 8 + cc
                        if (b[t] != "." and _white(b[t]) != white) or t == self.ep:
                            promos = "QRBN" if rr == last else (None,)
                            for pm in promos:
                                out.append((sq, t, pm))
            elif kind == "N" or kind == "K":
                for dr, dc in (KNIGHT if kind == "N" else KING):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < 8 and 0 <= cc < 8:
                        t = rr * 8 + cc
                        if b[t] == "." or _white(b[t]) != white:
                            out.append((sq, t, None))
                if kind == "K":
                    out += self._castles(sq, white)
            else:
                dirs = BISHOP if kind == "B" else ROOK if kind == "R" else BISHOP + ROOK
                for dr, dc in dirs:
                    rr, cc = r + dr, c + dc
                    while 0 <= rr < 8 and 0 <= cc < 8:
                        t = rr * 8 + cc
                        if b[t] == ".":
                            out.append((sq, t, None))
                        else:
                            if _white(b[t]) != white:
                                out.append((sq, t, None))
                            break
                        rr, cc = rr + dr, cc + dc
        return out

    def _castles(self, sq, white):
        b = self.board
        out = []
        home = 60 if white else 4
        if sq != home or self.attacked(sq, not white):
            return out
        rights = self.castling
        if ("K" if white else "k") in rights and b[home + 1] == "." and b[home + 2] == "." and \
                b[home + 3] == ("R" if white else "r") and not self.attacked(home + 1, not white) and \
                not self.attacked(home + 2, not white):
            out.append((sq, home + 2, None))
        if ("Q" if white else "q") in rights and b[home - 1] == "." and b[home - 2] == "." and b[home - 3] == "." \
                and b[home - 4] == ("R" if white else "r") and not self.attacked(home - 1, not white) and \
                not self.attacked(home - 2, not white):
            out.append((sq, home - 2, None))
        return out

    def apply(self, move):
        """-> the position after the move (a new Position)."""
        frm, to, promo = move
        p = self.board[frm]
        white = _white(p)
        n = self.copy()
        b = n.board
        capture = b[to] != "." or (p.upper() == "P" and to == self.ep)
        b[to], b[frm] = p, "."
        if p.upper() == "P" and to == self.ep:
            b[to + (8 if white else -8)] = "."
        if promo:
            b[to] = promo if white else promo.lower()
        if p.upper() == "K":
            if to - frm == 2:
                b[frm + 1], b[frm + 3] = b[frm + 3], "."
            elif frm - to == 2:
                b[frm - 1], b[frm - 4] = b[frm - 4], "."
            n.castling = n.castling.replace("K" if white else "k", "").replace("Q" if white else "q", "")
        for corner, flag in ((63, "K"), (56, "Q"), (7, "k"), (0, "q")):
            if frm == corner or to == corner:
                n.castling = n.castling.replace(flag, "")
        n.ep = (frm + to) // 2 if p.upper() == "P" and abs(to - frm) == 16 else None
        n.halfmove = 0 if (capture or p.upper() == "P") else self.halfmove + 1
        n.turn = "b" if white else "w"
        if not white:
            n.fullmove += 1
        return n

    def legal_moves(self):
        white = self.turn == "w"
        out = []
        for m in self.pseudo_moves():
            n = self.apply(m)
            if not n.attacked(n.king(white), not white):
                out.append(m)
        return out

    def evaluate(self):
        """From White's side, in centipawns."""
        score = 0
        for sq, p in enumerate(self.board):
            if p == ".":
                continue
            kind = p.upper()
            v = VALUES[kind] + PST[kind][sq if _white(p) else (7 - sq // 8) * 8 + sq % 8]
            score += v if _white(p) else -v
        return score

    def insufficient(self):
        pieces = [p for p in self.board if p not in ".Kk"]
        return not pieces or (len(pieces) == 1 and pieces[0] in "BbNn")


def search(pos, depth, alpha=-10 ** 9, beta=10 ** 9):
    """Negamax with alpha-beta; -> (score for the side to move, best move)."""
    moves = pos.legal_moves()
    white = pos.turn == "w"
    if not moves:
        if pos.in_check():
            return -100000 - depth, None
        return 0, None
    if depth == 0:
        return (pos.evaluate() if white else -pos.evaluate()), None
    moves.sort(key=lambda m: (pos.board[m[1]] == ".", -VALUES.get(pos.board[m[1]].upper(), 0)))
    best, best_move = -10 ** 9, moves[0]
    for m in moves:
        score, _ = search(pos.apply(m), depth - 1, -beta, -alpha)
        score = -score
        if score > best:
            best, best_move = score, m
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    return best, best_move


class Thinker(QObject):
    done = Signal(object)

    def __init__(self, pos, depth, level):
        super().__init__()
        self.pos, self.depth, self.level = pos, depth, level

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        moves = self.pos.legal_moves()
        if not moves:
            self.done.emit(None)
            return
        if self.level == "Beginner" and random.random() < 0.35:
            self.done.emit(random.choice(moves))
            return
        _score, move = search(self.pos, self.depth)
        self.done.emit(move or random.choice(moves))


def square_name(sq):
    return "abcdefgh"[sq % 8] + str(8 - sq // 8)


class Board(QWidget):
    """The wooden board: click a piece, then where it goes."""
    MARGIN = 26

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.desktop = window.desktop
        self.level = "Intermediate"
        self.human_white = True
        self.pos = Position()
        self.history = []
        self.selected = None
        self.targets = []
        self.last = None
        self.thinking = False
        self.over = False
        self.thinker = None
        self.setMinimumSize(420, 420)
        self.setMouseTracking(True)
        self._status()

    # ---- game flow ----
    def new_game(self, human_white=None):
        if human_white is not None:
            self.human_white = human_white
        self.pos, self.history, self.selected, self.targets, self.last = Position(), [], None, [], None
        self.over, self.thinking = False, False
        self._status()
        self.update()
        if not self.human_white:
            QTimer.singleShot(300, self.computer_move)

    def undo(self):
        if self.thinking or len(self.history) < 2:
            return
        self.history.pop()
        self.pos = self.history.pop()[0] if self.history else Position()
        if self.history:
            self.pos = self.history[-1][1]
        self.last = self.history[-1][2] if self.history else None
        self.over = False
        self.selected, self.targets = None, []
        self._status()
        self.update()

    def _push(self, before, after, move):
        self.history.append((before, after, move))

    def play(self, move):
        before = self.pos
        self.pos = self.pos.apply(move)
        self.last = move
        self._push(before, self.pos, move)
        self.selected, self.targets = None, []
        sound.play("navigate" if before.board[move[1]] == "." else "default")
        self._check_end()
        self._status()
        self.update()

    def _check_end(self):
        pos = self.pos
        moves = pos.legal_moves()
        result = None
        if not moves:
            result = "mate" if pos.in_check() else "stalemate"
        elif pos.halfmove >= 100 or pos.insufficient():
            result = "draw"
        if result:
            self.over = True
            human_to_move = (pos.turn == "w") == self.human_white
            if result == "mate":
                outcome = "loss" if human_to_move else "win"
                text = "Checkmate. You lose." if human_to_move else "Checkmate! You win."
            else:
                outcome = "draw"
                text = "Stalemate: a draw." if result == "stalemate" else "A draw."
            self._record(outcome)
            from claudexp.games.common import message
            QTimer.singleShot(200, lambda: message(self.desktop, "Chess Titans", text + "\n\nPlay again?",
                                                   ("Yes", "No"), lambda a: self.new_game() if a == "Yes" else None))

    def _record(self, outcome):
        from claudexp.games.common import save_stats, stats
        s = stats("chess")
        key = {"win": "wins", "loss": "losses", "draw": "draws"}[outcome]
        s[key] = s.get(key, 0) + 1
        s[f"{key}_{self.level}"] = s.get(f"{key}_{self.level}", 0) + 1
        save_stats("chess", s)

    def computer_move(self):
        if self.over or self.thinking:
            return
        self.thinking = True
        self.window.status.setText(" Thinking...")
        self.thinker = Thinker(self.pos, LEVELS[self.level], self.level)
        self.thinker.done.connect(self._computer_done)
        self.thinker.start()

    def _computer_done(self, move):
        self.thinking = False
        if move is None or self.over:
            return
        self.play(move)
        self._status()

    def _status(self):
        if self.over:
            return
        side = "White" if self.pos.turn == "w" else "Black"
        you = (self.pos.turn == "w") == self.human_white
        text = f" {side} to move" + (" (you)" if you else " (computer)")
        if self.pos.in_check():
            text += "  -  Check!"
        self.window.status.setText(text)

    # ---- the mouse ----
    def _geometry(self):
        size = min(self.width(), self.height()) - 2 * self.MARGIN
        cell = size // 8
        x0 = (self.width() - cell * 8) // 2
        y0 = (self.height() - cell * 8) // 2
        return x0, y0, cell

    def _square_at(self, pos):
        x0, y0, cell = self._geometry()
        c, r = (pos.x() - x0) // cell, (pos.y() - y0) // cell
        if not (0 <= c < 8 and 0 <= r < 8):
            return None
        if not self.human_white:
            r, c = 7 - r, 7 - c
        return r * 8 + c

    def mousePressEvent(self, event):
        if self.over or self.thinking or event.button() != Qt.LeftButton:
            return
        if (self.pos.turn == "w") != self.human_white:
            return
        sq = self._square_at(event.position().toPoint())
        if sq is None:
            return
        if self.selected is not None:
            for m in self.targets:
                if m[1] == sq:
                    move = m if m[2] in (None, "Q") else (m[0], m[1], "Q")
                    self.play(move)
                    if not self.over:
                        QTimer.singleShot(250, self.computer_move)
                    return
        p = self.pos.board[sq]
        if p != "." and _white(p) == (self.pos.turn == "w"):
            self.selected = sq
            self.targets = [m for m in self.pos.legal_moves() if m[0] == sq]
            sound.play("menu")
        else:
            self.selected, self.targets = None, []
        self.update()

    # ---- painting ----
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QColor("#4A3524"))
        bg.setColorAt(1, QColor("#2B1D12"))
        p.fillRect(self.rect(), bg)
        x0, y0, cell = self._geometry()
        frame = QRect(x0 - 18, y0 - 18, cell * 8 + 36, cell * 8 + 36)
        wood = QLinearGradient(frame.topLeft(), frame.bottomRight())
        wood.setColorAt(0, QColor("#8B5A2B"))
        wood.setColorAt(0.5, QColor("#A0693A"))
        wood.setColorAt(1, QColor("#6E4320"))
        p.setPen(QPen(QColor("#3A2412"), 2))
        p.setBrush(wood)
        p.drawRoundedRect(frame, 6, 6)
        f = QFont("Segoe UI")
        f.setPixelSize(max(9, cell // 5))
        p.setFont(f)
        for i in range(8):
            file_ = "abcdefgh"[i if self.human_white else 7 - i]
            rank = str(8 - i) if self.human_white else str(i + 1)
            p.setPen(QColor("#F3E3CC"))
            p.drawText(QRect(x0 + i * cell, y0 + cell * 8 + 2, cell, 14), Qt.AlignCenter, file_)
            p.drawText(QRect(x0 - 16, y0 + i * cell, 14, cell), Qt.AlignCenter, rank)
        check_sq = self.pos.king(self.pos.turn == "w") if self.pos.in_check() else None
        for r in range(8):
            for c in range(8):
                sq = r * 8 + c
                dr, dc = (r, c) if self.human_white else (7 - r, 7 - c)
                rect = QRect(x0 + dc * cell, y0 + dr * cell, cell, cell)
                light = (r + c) % 2 == 0
                g = QLinearGradient(rect.topLeft(), rect.bottomRight())
                if light:
                    g.setColorAt(0, QColor("#F2DEBD"))
                    g.setColorAt(1, QColor("#E2C79A"))
                else:
                    g.setColorAt(0, QColor("#B3783F"))
                    g.setColorAt(1, QColor("#8F5A2A"))
                p.fillRect(rect, g)
                if self.last and sq in self.last[:2]:
                    p.fillRect(rect, QColor(255, 230, 90, 90))
                if sq == self.selected:
                    p.fillRect(rect, QColor(120, 190, 255, 120))
                if sq == check_sq:
                    rg = QRadialGradient(rect.center(), cell * 0.7)
                    rg.setColorAt(0, QColor(255, 60, 40, 170))
                    rg.setColorAt(1, QColor(255, 60, 40, 0))
                    p.fillRect(rect, rg)
                piece = self.pos.board[sq]
                if piece != ".":
                    self._piece(p, rect, piece, cell)
                if any(m[1] == sq for m in self.targets):
                    p.setPen(Qt.NoPen)
                    if self.pos.board[sq] != ".":
                        p.setBrush(QColor(60, 160, 60, 0))
                        p.setPen(QPen(QColor(60, 160, 60, 200), 3))
                        p.drawEllipse(QRectF(rect).adjusted(4, 4, -4, -4))
                    else:
                        p.setBrush(QColor(60, 160, 60, 170))
                        p.drawEllipse(rect.center(), cell * 0.14, cell * 0.14)
        p.setPen(QPen(QColor("#3A2412"), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRect(x0, y0, cell * 8, cell * 8)

    def _piece(self, p, rect, piece, cell):
        f = QFont("Segoe UI Symbol")
        f.setPixelSize(int(cell * 0.82))
        p.setFont(f)
        glyph = GLYPHS[piece]
        r = QRectF(rect).adjusted(0, -cell * 0.04, 0, -cell * 0.04)
        p.setPen(QColor(0, 0, 0, 110))
        p.drawText(r.translated(2, 3), Qt.AlignCenter, glyph)
        if _white(piece):
            p.setPen(QColor("#2A2A2A"))
            p.drawText(r.translated(1, 1), Qt.AlignCenter, GLYPHS[piece.lower()])
            p.setPen(QColor("#FFF9EC"))
            p.drawText(r, Qt.AlignCenter, GLYPHS[piece.lower()])
            p.setPen(QColor("#2A2A2A"))
            p.drawText(r, Qt.AlignCenter, glyph)
        else:
            p.setPen(QColor("#111111"))
            p.drawText(r, Qt.AlignCenter, glyph)


def chess_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    g = QLinearGradient(0, 0, size, size)
    g.setColorAt(0, QColor("#F2DEBD"))
    g.setColorAt(1, QColor("#B3783F"))
    p.setPen(QPen(QColor("#5A3A1C"), 1))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(2 * s, 2 * s, 28 * s, 28 * s), 3 * s, 3 * s)
    f = QFont("Segoe UI Symbol")
    f.setPixelSize(int(24 * s))
    p.setFont(f)
    p.setPen(QColor("#111111"))
    p.drawText(QRectF(2 * s, 1 * s, 28 * s, 28 * s), Qt.AlignCenter, "♞")
    p.end()
    return QIcon(pm)


def open_chess(desktop):
    from PySide6.QtGui import QActionGroup
    from claudexp.games.common import GameWindow, message, open_game, stats

    def make():
        win = GameWindow(desktop, Board)
        win.setStyleSheet("QMenuBar { background: #F0F0F0; font-family: 'Segoe UI'; font-size: 12px; }"
                          "QMenuBar::item:selected { background: #CCE8FF; }"
                          "QMenu { background: #F0F0F0; border: 1px solid #979797; font-family: 'Segoe UI'; font-size: 12px; }"
                          "QMenu::item { padding: 4px 24px 4px 28px; } QMenu::item:selected { background: #CCE8FF; }"
                          "QLabel#gamestatus { background: #F0F0F0; border-top: 1px solid #D5D5D5; padding: 2px 8px;"
                          " font-family: 'Segoe UI'; font-size: 12px; }")
        board = win.play
        game = win.menu.addMenu("&Game")
        game.addAction("&New Game", lambda: board.new_game(), "F2")
        game.addAction("&Undo", board.undo, "Ctrl+Z")
        game.addSeparator()
        side = game.addMenu("&Play as")
        for label, white in (("White", True), ("Black", False)):
            side.addAction(label, lambda w=white: board.new_game(w))
        level = game.addMenu("&Difficulty")
        grp = QActionGroup(level)
        for name in LEVELS:
            a = level.addAction(name)
            a.setCheckable(True)
            a.setChecked(name == board.level)
            a.triggered.connect(lambda _c=False, n=name: setattr(board, "level", n))
            grp.addAction(a)

        def show_stats():
            s = stats("chess")
            lines = [f"Wins: {s.get('wins', 0)}", f"Losses: {s.get('losses', 0)}", f"Draws: {s.get('draws', 0)}", ""]
            for name in LEVELS:
                lines.append(f"{name}: {s.get(f'wins_{name}', 0)} won, {s.get(f'losses_{name}', 0)} lost, "
                             f"{s.get(f'draws_{name}', 0)} drawn")
            message(desktop, "Chess Titans - Statistics", "\n".join(lines))
        game.addAction("&Statistics", show_stats, "F4")
        game.addSeparator()
        game.addAction("E&xit", lambda: win.frame.request_close() if win.frame else None)
        help_menu = win.menu.addMenu("&Help")
        help_menu.addAction("&How to play", lambda: message(
            desktop, "Chess Titans", "Click one of your pieces, then the square to move it to. Green dots are the "
            "legal moves; a ring marks a capture. Pawns promote to queens.\n\nGame > Difficulty sets how far the "
            "computer thinks ahead; Game > Play as lets you take Black."))
        help_menu.addAction("&About Chess Titans", lambda: message(
            desktop, "About Chess Titans", "Chess Titans\nWindows 7 Home Premium\n\n© 2009 Microsoft Corporation "
            "(and Claude7's own engine)."))
        return win
    open_game(desktop, "chess", "Chess Titans", make, chess_icon(), (560, 600))
