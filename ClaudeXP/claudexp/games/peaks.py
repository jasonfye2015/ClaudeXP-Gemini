"""TriPeaks and Golf: two quick solitaires from the Entertainment Packs, on Solitaire's felt with its cards.

TriPeaks: clear the three peaks. Click an uncovered card one higher or lower than the waste card (Kings and Aces
wrap); the longer the run, the more each card scores. Click the deck for a new waste card.

Golf: seven columns of five. Clear the bottom cards one higher or lower than the waste card (no wrapping, and
nothing goes on a King). Fewer cards left is a better score; clear them all for a hole in one."""
import random

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from .. import sound
from .cards import CARD_H, CARD_W, FELT, back_pixmap, deck, draw_slot, face_pixmap
from .common import GameWindow, message, open_game, save_stats, stats


def _adjacent(a, b, wrap):
    d = abs(a - b)
    return d == 1 or (wrap and d == 12)


class Table(QWidget):
    """Shared bits: felt, the stock and waste piles, card drawing and hit-testing."""
    W, H = 640, 440

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setFixedSize(self.W, self.H)
        self.faces = {}
        self.back = back_pixmap()
        self.new_game()

    def face(self, card):
        key = (card.rank, card.suit)
        if key not in self.faces:
            self.faces[key] = face_pixmap(card.rank, card.suit)
        return self.faces[key]

    def stock_rect(self):
        return QRectF(40, self.H - CARD_H - 24, CARD_W, CARD_H)

    def waste_rect(self):
        return QRectF(40 + CARD_W + 30, self.H - CARD_H - 24, CARD_W, CARD_H)

    def draw_piles(self, p):
        if self.stock:
            for i in range(min(3, len(self.stock))):
                p.drawPixmap(self.stock_rect().topLeft() + QPointF(-i * 2, -i * 2), self.back)
        else:
            draw_slot(p, self.stock_rect().toRect(), "")
        if self.waste:
            p.drawPixmap(self.waste_rect().topLeft(), self.face(self.waste[-1]))
        p.setPen(QColor("#E8F8E8"))
        p.setFont(QFont("Tahoma", 8))
        p.drawText(QRectF(self.stock_rect().x(), self.stock_rect().bottom() + 2, CARD_W, 16), Qt.AlignCenter,
                   f"{len(self.stock)} left")

    def deal_one(self):
        if self.stock:
            self.waste.append(self.stock.pop())
            self.waste[-1].face_up = True
            self.run = 0
            sound.play("menu")
            self.after_move()
            self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or self.over:
            return
        pos = event.position()
        if self.stock_rect().contains(pos):
            self.deal_one()
            return
        self.click(pos)

    def mouseDoubleClickEvent(self, event):
        self.mousePressEvent(event)


class TriPeaks(Table):
    def new_game(self):
        cards = deck()
        random.shuffle(cards)
        # 3 peaks: rows of 3, 6, 9 and a base of 10
        self.slots = []                      # [card or None, x, y, row, index]
        rows = [3, 6, 9, 10]
        spacing = CARD_W * 0.74
        top = 18
        for row, n in enumerate(rows):
            for i in range(n):
                if row == 0:
                    x = 80 + i * 3 * spacing + spacing * 1.5
                elif row == 1:
                    x = 80 + (i // 2) * 3 * spacing + spacing * (1 + (i % 2))
                elif row == 2:
                    x = 80 + i * spacing + spacing * 0.5
                else:
                    x = 80 + i * spacing
                self.slots.append([cards.pop(), x, top + row * CARD_H * 0.42, row, i])
        self.stock = cards
        self.waste = [self.stock.pop()]
        self.waste[0].face_up = True
        self.score = stats("tripeaks").get("bank", 0) - 52   # Vegas-style: each game costs $52
        self.run = 0
        self.over = False
        self._flip()
        self._status()
        self.update()

    def _covers(self, k):
        """Indices of the two cards that cover slot k (in the row below)."""
        _c, _x, _y, row, i = self.slots[k]
        start = [0, 3, 9, 18, 28][row + 1] if row < 3 else None
        if start is None:
            return []
        if row == 0:
            below = [2 * i, 2 * i + 1]
        elif row == 1:
            below = [i + i // 2, i + i // 2 + 1]
        else:
            below = [i, i + 1]
        return [start + b for b in below]

    def _free(self, k):
        return self.slots[k][0] is not None and all(self.slots[j][0] is None for j in self._covers(k))

    def _flip(self):
        for k, slot in enumerate(self.slots):
            if slot[0] is not None:
                slot[0].face_up = self._free(k)

    def click(self, pos):
        for k in range(len(self.slots) - 1, -1, -1):
            card, x, y, _r, _i = self.slots[k]
            if card is None or not QRectF(x, y, CARD_W, CARD_H).contains(pos):
                continue
            if self._free(k) and _adjacent(card.rank, self.waste[-1].rank, wrap=True):
                self.slots[k][0] = None
                self.waste.append(card)
                self.run += 1
                self.score += self.run
                for peak_top in (0, 1, 2):                       # clearing a peak is worth a bonus
                    if k == peak_top:
                        self.score += 15 if any(s[0] for s in self.slots[:3]) else 30
                sound.play("menu")
                self._flip()
                self.after_move()
                self.update()
            return

    def after_move(self):
        self._status()
        if all(s[0] is None for s in self.slots):
            self._end(True)
        elif not self.stock and not any(self._free(k) and _adjacent(s[0].rank, self.waste[-1].rank, True)
                                        for k, s in enumerate(self.slots) if s[0] is not None):
            self._end(False)

    def _end(self, won):
        self.over = True
        s = stats("tripeaks")
        s["bank"] = self.score
        s["games"] = s.get("games", 0) + 1
        s["wins"] = s.get("wins", 0) + (1 if won else 0)
        save_stats("tripeaks", s)
        message(self.window.desktop, "TriPeaks", ("You cleared all three peaks!" if won else "No more moves.")
                + f"\n\nBank: ${self.score:,}\n\nPress F2 to deal again.")

    def _status(self):
        left = sum(1 for s in self.slots if s[0] is not None)
        self.window.status.setText(f"  Bank: ${self.score:,}     Run: {self.run}     Cards in the peaks: {left}")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.fillRect(self.rect(), FELT)
        for card, x, y, _r, _i in self.slots:
            if card is not None:
                p.drawPixmap(QPointF(x, y), self.face(card) if card.face_up else self.back)
        self.draw_piles(p)


class Golf(Table):
    COLS = 7

    def new_game(self):
        cards = deck()
        random.shuffle(cards)
        self.columns = [[cards.pop() for _ in range(5)] for _ in range(self.COLS)]
        for col in self.columns:
            for c in col:
                c.face_up = True
        self.stock = cards
        self.waste = [self.stock.pop()]
        self.waste[0].face_up = True
        self.run = 0
        self.over = False
        self._status()
        self.update()

    def col_x(self, i):
        gap = (self.W - 40 - self.COLS * CARD_W) / (self.COLS - 1)
        return 20 + i * (CARD_W + gap)

    def click(self, pos):
        for i, col in enumerate(self.columns):
            if not col:
                continue
            y = 16 + (len(col) - 1) * 22
            if QRectF(self.col_x(i), y, CARD_W, CARD_H).contains(pos):
                card, top = col[-1], self.waste[-1]
                if top.rank != 13 and _adjacent(card.rank, top.rank, wrap=False):
                    self.waste.append(col.pop())
                    self.run += 1
                    sound.play("menu")
                    self.after_move()
                    self.update()
                return

    def left(self):
        return sum(len(c) for c in self.columns)

    def after_move(self):
        self._status()
        if self.left() == 0:
            self._end()
        elif not self.stock and not any(c and self.waste[-1].rank != 13 and _adjacent(c[-1].rank, self.waste[-1].rank,
                                                                                      False) for c in self.columns):
            self._end()

    def _end(self):
        self.over = True
        n = self.left()
        s = stats("golf")
        best = s.get("best")
        if best is None or n < best:
            s["best"] = n
        s["games"] = s.get("games", 0) + 1
        save_stats("golf", s)
        self._status()
        message(self.window.desktop, "Golf", ("Hole in one! Every card cleared." if n == 0 else
                                              f"Round over: {n} card{'s' if n != 1 else ''} left.")
                + f"\n\nBest round: {s['best']}\n\nPress F2 to play again.")

    def _status(self):
        self.window.status.setText(f"  Cards left: {self.left()}     Run: {self.run}     "
                                   f"Best round: {stats('golf').get('best', '-')}")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.fillRect(self.rect(), FELT)
        for i, col in enumerate(self.columns):
            if not col:
                draw_slot(p, QRectF(self.col_x(i), 16, CARD_W, CARD_H).toRect())
            for j, card in enumerate(col):
                p.drawPixmap(QPointF(self.col_x(i), 16 + j * 22), self.face(card))
        self.draw_piles(p)


def _icon(kind):
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    card = face_pixmap(13 if kind == "tripeaks" else 7, "H" if kind == "tripeaks" else "S", 18, 24)
    if kind == "tripeaks":
        for x, y in ((1, 8), (13, 8), (7, 2)):
            p.drawPixmap(x, y, card)
    else:
        for i in range(3):
            p.drawPixmap(3 + i * 9, 2 + i * 3, card)
        p.setPen(QPen(QColor("#2A7A2A"), 2))
        p.drawLine(QPointF(24, 30), QPointF(24, 18))
        p.setBrush(QColor("#E02020"))
        p.setPen(Qt.NoPen)
        p.drawPolygon([QPointF(24, 18), QPointF(31, 21), QPointF(24, 24)])
    p.end()
    return QIcon(pm)


def tripeaks_icon():
    return _icon("tripeaks")


def golf_icon():
    return _icon("golf")


TRIPEAKS_HOW = ("Clear the three peaks.\n\nClick an uncovered card that is one higher or one lower than the face-up "
                "card at the bottom (Kings and Aces wrap round). A card turns over once both cards on top of it "
                "are gone.\n\nThe longer your run without turning a card from the deck, the more each card "
                "scores. Clearing a peak earns a bonus. Each new deal costs $52, Vegas-style.")
GOLF_HOW = ("Clear the seven columns.\n\nClick the bottom card of a column if it is one higher or one lower than "
            "the face-up card at the bottom. Aces are low and don't wrap, and nothing can be played on a King.\n\n"
            "When you're stuck, click the deck. Like golf, a lower score is better: clear every card for a hole "
            "in one.")


def _open(desktop, key, title, cls, icon, how):
    def make():
        win = GameWindow(desktop, cls)
        table = win.play
        game = win.menu.addMenu("&Game")
        game.addAction("&Deal", table.new_game, "F2")
        game.addSeparator()
        game.addAction("E&xit", lambda: win.frame.request_close())
        help_menu = win.menu.addMenu("&Help")
        help_menu.addAction("&How to Play", lambda: message(desktop, title, how))
        return win
    return open_game(desktop, key, title, make, icon, None)


def open_tripeaks(desktop):
    return _open(desktop, "tripeaks", "TriPeaks", TriPeaks, tripeaks_icon(), TRIPEAKS_HOW)


def open_golf(desktop):
    return _open(desktop, "golf", "Golf", Golf, golf_icon(), GOLF_HOW)
