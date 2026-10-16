"""Taipei: mahjong solitaire on the classic 144-tile 'turtle', as in the Entertainment Pack.

Click two free tiles that match to take them away. A tile is free when nothing lies on top of it and its left or
right side is open. Flowers match any flower and seasons any season. Every deal is built by playing the layout
backwards, so it can always be solved. H gives a hint, Ctrl+Z takes back a move."""
import random

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from .. import sound
from .common import GameWindow, message, open_game, save_stats, stats

TW, TH = 34, 46               # tile face size
DEPTH = 5                     # how far each layer is lifted
W, H = 15 * TW + 60, 8 * TH + 70


def turtle():
    """(x, y, z) in tile units for the 144-tile turtle layout."""
    spots = []
    rows = {0: range(1, 13), 1: range(3, 11), 2: range(2, 12), 3: range(1, 13),
            4: range(1, 13), 5: range(2, 12), 6: range(3, 11), 7: range(1, 13)}
    for y, xs in rows.items():
        spots += [(x, y, 0) for x in xs]
    spots += [(0, 3.5, 0), (13, 3.5, 0), (14, 3.5, 0)]
    spots += [(x, y, 1) for y in range(1, 7) for x in range(4, 10)]
    spots += [(x, y, 2) for y in range(2, 6) for x in range(5, 9)]
    spots += [(x, y, 3) for y in range(3, 5) for x in range(6, 8)]
    spots += [(6.5, 3.5, 4)]
    return spots


# 34 kinds x 4, plus 4 flowers and 4 seasons (which match within their group)
KINDS = [("dot", n) for n in range(1, 10)] + [("bam", n) for n in range(1, 10)] + [("chr", n) for n in range(1, 10)] \
    + [("wind", w) for w in "ESWN"] + [("drg", d) for d in "RGW"]
GROUPS = [(k, i) for k in KINDS for i in range(4)] + [(("flw", n), 0) for n in range(1, 5)] + \
    [(("ssn", n), 0) for n in range(1, 5)]
CHARS = "一二三四五六七八九"
WINDS = {"E": "東", "S": "南", "W": "西", "N": "北"}


def match(a, b):
    if a[0] in ("flw", "ssn"):
        return a[0] == b[0]
    return a == b


class Board(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setFixedSize(W, H)
        self.new_game()

    # ---- dealing -------------------------------------------------------------------------------------
    def new_game(self):
        spots = turtle()
        for _ in range(50):                               # play the layout backwards with random pairs
            tiles = self._deal(spots)
            if tiles:
                break
        self.tiles = tiles                                # [(x, y, z), kind]; kind None once removed
        self.picked = None
        self.history = []
        self.hint = []
        self.over = False
        self._status()
        self.update()

    def _deal(self, spots):
        faces = [k for k, _i in GROUPS]
        pairs = []
        bag = list(faces)
        random.shuffle(bag)
        # pair up: ordinary kinds pair with themselves, flowers with flowers, seasons with seasons
        by = {}
        for f in bag:
            key = f[0] if f[0] in ("flw", "ssn") else f
            by.setdefault(key, []).append(f)
        for group in by.values():
            for i in range(0, len(group), 2):
                pairs.append((group[i], group[i + 1]))
        random.shuffle(pairs)
        placed = {s: None for s in spots}
        remaining = set(spots)
        for a, b in pairs:
            free = [s for s in remaining if self._free_in(s, remaining)]
            if len(free) < 2:
                return None
            s1, s2 = random.sample(free, 2)
            placed[s1], placed[s2] = a, b
            remaining -= {s1, s2}
        return [[s, placed[s]] for s in sorted(spots, key=lambda s: (s[2], s[0], s[1]))]

    @staticmethod
    def _free_in(s, present):
        x, y, z = s
        for (ox, oy, oz) in present:
            if oz == z + 1 and abs(ox - x) < 1 and abs(oy - y) < 1:
                return False                              # something on top
        left = any(oz == z and ox == x - 1 and abs(oy - y) < 1 for (ox, oy, oz) in present)
        right = any(oz == z and ox == x + 1 and abs(oy - y) < 1 for (ox, oy, oz) in present)
        return not (left and right)

    def present(self):
        return {s for s, k in self.tiles if k is not None}

    def free(self, s):
        return self._free_in(s, self.present())

    def moves(self):
        present = self.present()
        free = [(s, k) for s, k in self.tiles if k is not None and self._free_in(s, present)]
        out = []
        for i in range(len(free)):
            for j in range(i + 1, len(free)):
                if match(free[i][1], free[j][1]):
                    out.append((free[i][0], free[j][0]))
        return out

    # ---- play -----------------------------------------------------------------------------------------
    def rect_of(self, s):
        x, y, z = s
        return QRectF(30 + x * TW - z * DEPTH, 20 + y * TH - z * DEPTH, TW, TH)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or self.over:
            return
        pos = event.position()
        hit = None
        for s, k in sorted(self.tiles, key=lambda t: -t[0][2]):     # topmost first
            if k is not None and self.rect_of(s).contains(pos):
                hit = s
                break
        self.hint = []
        if hit is None or not self.free(hit):
            self.picked = None
            self.update()
            return
        if self.picked is None or self.picked == hit:
            self.picked = None if self.picked == hit else hit
        else:
            a = self._kind(self.picked)
            b = self._kind(hit)
            if match(a, b):
                self.history.append([(self.picked, a), (hit, b)])
                self._set(self.picked, None)
                self._set(hit, None)
                self.picked = None
                sound.play("menu")
                self._after()
            else:
                self.picked = hit
        self.update()

    def _kind(self, s):
        return next(k for t, k in self.tiles if t == s)

    def _set(self, s, kind):
        for t in self.tiles:
            if t[0] == s:
                t[1] = kind

    def undo(self):
        if self.history and not self.over:
            for s, k in self.history.pop():
                self._set(s, k)
            self.picked = None
            self._status()
            self.update()

    def show_hint(self):
        moves = self.moves()
        self.hint = list(moves[0]) if moves else []
        if not moves:
            message(self.window.desktop, "Taipei", "There are no more matching pairs.")
        self.update()

    def _after(self):
        self._status()
        left = len(self.present())
        if left == 0:
            self.over = True
            s = stats("taipei")
            s["wins"] = s.get("wins", 0) + 1
            save_stats("taipei", s)
            message(self.window.desktop, "Taipei", "Congratulations! You cleared every tile.\n\nPress F2 for a new game.")
        elif not self.moves():
            message(self.window.desktop, "Taipei", f"No more moves, with {left} tiles left.\n\n"
                                                   "Take moves back with Undo, or press F2 for a new game.")

    def _status(self):
        self.window.status.setText(f"  Tiles left: {len(self.present())}     Matching pairs free: {len(self.moves())}")

    # ---- drawing ------------------------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 0, H)
        g.setColorAt(0, QColor("#1E5A3A"))
        g.setColorAt(1, QColor("#0E3A22"))
        p.fillRect(self.rect(), g)
        for s, k in self.tiles:
            if k is not None:
                draw_tile(p, self.rect_of(s), k, picked=s == self.picked, hint=s in self.hint)


def draw_tile(p, r, kind, picked=False, hint=False):
    side = QRectF(r.x() + DEPTH, r.y() + DEPTH, r.width(), r.height())
    p.setPen(QPen(QColor("#6A5A3A"), 1))
    p.setBrush(QColor("#C8B48A"))
    p.drawRoundedRect(side, 4, 4)                               # the tile's body
    face = QLinearGradient(r.topLeft(), r.bottomRight())
    face.setColorAt(0, QColor("#FFFDF4"))
    face.setColorAt(1, QColor("#E8E0C8"))
    p.setBrush(QColor("#9CC8FF") if picked else QColor("#FFF2A0") if hint else face)
    p.drawRoundedRect(r, 4, 4)
    draw_face(p, r.adjusted(3, 3, -3, -3), kind)


def draw_face(p, r, kind):
    suit, n = kind
    cx, cy = r.center().x(), r.center().y()
    if suit == "dot":
        cols = 1 if n == 1 else 2 if n in (2, 4) else 3 if n in (3, 9) else 2
        pos = {1: [(0.5, 0.5)], 2: [(0.5, 0.25), (0.5, 0.75)], 3: [(0.2, 0.2), (0.5, 0.5), (0.8, 0.8)],
               4: [(0.3, 0.27), (0.7, 0.27), (0.3, 0.73), (0.7, 0.73)],
               5: [(0.28, 0.24), (0.72, 0.24), (0.5, 0.5), (0.28, 0.76), (0.72, 0.76)],
               6: [(0.3, 0.2), (0.7, 0.2), (0.3, 0.5), (0.7, 0.5), (0.3, 0.8), (0.7, 0.8)],
               7: [(0.2, 0.15), (0.5, 0.25), (0.8, 0.35), (0.3, 0.6), (0.7, 0.6), (0.3, 0.85), (0.7, 0.85)],
               8: [(0.3, 0.13), (0.7, 0.13), (0.3, 0.38), (0.7, 0.38), (0.3, 0.62), (0.7, 0.62), (0.3, 0.87),
                   (0.7, 0.87)],
               9: [(x, y) for y in (0.18, 0.5, 0.82) for x in (0.2, 0.5, 0.8)]}[n]
        rad = r.width() * (0.3 if n == 1 else 0.13)
        for i, (fx, fy) in enumerate(pos):
            c = QColor("#C82020") if (n in (1, 5) and i == len(pos) // 2) or (n == 7 and i < 3) else \
                QColor("#1E5AA8") if i % 2 == 0 else QColor("#2A8A3A")
            p.setPen(QPen(c, 1.4))
            p.setBrush(QColor("#FFFDF4"))
            p.drawEllipse(QPointF(r.x() + fx * r.width(), r.y() + fy * r.height()), rad, rad)
            p.setBrush(c)
            p.drawEllipse(QPointF(r.x() + fx * r.width(), r.y() + fy * r.height()), rad * 0.45, rad * 0.45)
    elif suit == "bam":
        if n == 1:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#2A8A3A"))
            p.drawEllipse(QPointF(cx, cy + 2), r.width() * 0.28, r.height() * 0.22)     # the bird
            p.setBrush(QColor("#C82020"))
            p.drawEllipse(QPointF(cx + 4, cy - 7), 3.5, 3.5)
            return
        cols = 3 if n >= 5 else 2
        rows_ = -(-n // cols)
        k = 0
        for row in range(rows_):
            for col in range(cols):
                if k >= n:
                    break
                x = r.x() + (col + 0.5) * r.width() / cols
                y = r.y() + (row + 0.5) * r.height() / rows_
                p.setPen(QPen(QColor("#1E6A2E") if k % 2 == 0 else QColor("#C82020"), 2.2, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(x, y - r.height() / rows_ * 0.38), QPointF(x, y + r.height() / rows_ * 0.38))
                k += 1
    elif suit == "chr":
        p.setPen(QColor("#1A1A1A"))
        p.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        p.drawText(QRectF(r.x(), r.y(), r.width(), r.height() * 0.5), Qt.AlignCenter, CHARS[n - 1])
        p.setPen(QColor("#C82020"))
        p.drawText(QRectF(r.x(), r.y() + r.height() * 0.45, r.width(), r.height() * 0.55), Qt.AlignCenter, "萬")
    elif suit == "wind":
        p.setPen(QColor("#1A1A1A"))
        p.setFont(QFont("Microsoft YaHei", 15, QFont.Bold))
        p.drawText(r, Qt.AlignCenter, WINDS[n])
    elif suit == "drg":
        if n == "W":
            p.setPen(QPen(QColor("#1E5AA8"), 2))
            p.setBrush(Qt.NoBrush)
            p.drawRect(r.adjusted(3, 4, -3, -4))
        else:
            p.setPen(QColor("#C82020") if n == "R" else QColor("#1E7A2E"))
            p.setFont(QFont("Microsoft YaHei", 15, QFont.Bold))
            p.drawText(r, Qt.AlignCenter, "中" if n == "R" else "發")
    else:                                                          # flowers and seasons
        p.setPen(Qt.NoPen)
        petal = QColor("#E05090") if suit == "flw" else QColor("#E09020")
        for k in range(5):
            p.save()
            p.translate(cx, cy - 3)
            p.rotate(k * 72)
            p.setBrush(petal)
            p.drawEllipse(QRectF(-3, -10, 6, 9))
            p.restore()
        p.setBrush(QColor("#FFD040"))
        p.drawEllipse(QPointF(cx, cy - 3), 3, 3)
        p.setPen(QColor("#5A4A2A"))
        p.setFont(QFont("Tahoma", 7, QFont.Bold))
        p.drawText(QRectF(r.x(), r.bottom() - 11, r.width(), 11), Qt.AlignCenter, str(n))


def taipei_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    global DEPTH
    keep, DEPTH = DEPTH, 2
    draw_tile(p, QRectF(2, 4, 16, 22), ("drg", "R"))
    draw_tile(p, QRectF(13, 2, 16, 22), ("dot", 5))
    DEPTH = keep
    p.end()
    return QIcon(pm)


HOW_TO = ("Clear the board by matching pairs of tiles.\n\nClick two free tiles that are the same. A tile is free "
          "when no tile lies on top of it and it can slide out to the left or the right. Any flower matches any "
          "flower, and any season matches any season.\n\nEvery deal can be solved, but the order matters. Press H "
          "for a hint and Ctrl+Z to take a move back. F2 deals a new game.")


def open_taipei(desktop):
    def make():
        win = GameWindow(desktop, Board)
        board = win.play
        game = win.menu.addMenu("&Game")
        game.addAction("&New Game", board.new_game, "F2")
        game.addAction("&Undo", board.undo, "Ctrl+Z")
        game.addAction("&Hint", board.show_hint, "H")
        game.addSeparator()
        game.addAction("E&xit", lambda: win.frame.request_close())
        help_menu = win.menu.addMenu("&Help")
        help_menu.addAction("&How to Play", lambda: message(desktop, "Taipei", HOW_TO))
        return win
    return open_game(desktop, "taipei", "Taipei", make, taipei_icon(), None)
