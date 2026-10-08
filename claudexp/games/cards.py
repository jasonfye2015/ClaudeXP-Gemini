"""Playing cards drawn with QPainter (classic 71x96 size), plus a card table with drag and drop.

Each card game subclasses CardTable and supplies its piles and rules:
  can_pick(pile, index) -> bool          may the cards from index up be picked up?
  can_drop(cards, src, dst) -> bool      may they be dropped on dst?
  dropped(cards, src, dst)               do the move (cards are already off src)
  clicked(pile, index)                   a single click (e.g. on the stock)
  double_clicked(pile, index)            a double click (e.g. send to foundation)
"""
import math
import random
from functools import lru_cache

from PySide6.QtCore import QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget

CARD_W, CARD_H = 71, 96
SUITS = "CDHS"
SUIT_SYMBOLS = {"C": "♣", "D": "♦", "H": "♥", "S": "♠"}
RANK_TEXT = {1: "A", 11: "J", 12: "Q", 13: "K"}
FELT = QColor("#008000")


class Card:
    __slots__ = ("rank", "suit", "face_up")

    def __init__(self, rank, suit, face_up=False):
        self.rank, self.suit, self.face_up = rank, suit, face_up

    @property
    def red(self):
        return self.suit in "DH"

    @property
    def name(self):
        return f"{RANK_TEXT.get(self.rank, str(self.rank))}{self.suit}"

    def __repr__(self):
        return self.name


def deck(decks=1, suits=SUITS):
    """A fresh deck (or several), face down. suits limits which suits appear (Spider's 1- and 2-suit games)."""
    cards = []
    per_suit = 4 * decks // len(suits)
    for suit in suits:
        for _ in range(per_suit):
            for rank in range(1, 14):
                cards.append(Card(rank, suit))
    return cards


# ---- drawing ---------------------------------------------------------------------------------------

L, C, R = 0.27, 0.5, 0.73
PIPS = {
    1: [(C, 0.5)],
    2: [(C, 0.17), (C, 0.83)],
    3: [(C, 0.17), (C, 0.5), (C, 0.83)],
    4: [(L, 0.17), (R, 0.17), (L, 0.83), (R, 0.83)],
    5: [(L, 0.17), (R, 0.17), (C, 0.5), (L, 0.83), (R, 0.83)],
    6: [(L, 0.17), (R, 0.17), (L, 0.5), (R, 0.5), (L, 0.83), (R, 0.83)],
    7: [(L, 0.17), (R, 0.17), (C, 0.335), (L, 0.5), (R, 0.5), (L, 0.83), (R, 0.83)],
    8: [(L, 0.17), (R, 0.17), (C, 0.335), (L, 0.5), (R, 0.5), (C, 0.665), (L, 0.83), (R, 0.83)],
    9: [(L, 0.17), (R, 0.17), (L, 0.39), (R, 0.39), (C, 0.5), (L, 0.61), (R, 0.61), (L, 0.83), (R, 0.83)],
    10: [(L, 0.17), (R, 0.17), (C, 0.28), (L, 0.39), (R, 0.39), (L, 0.61), (R, 0.61), (C, 0.72), (L, 0.83), (R, 0.83)],
}


def _symbol_font(px):
    font = QFont("Segoe UI Symbol")
    font.setPixelSize(max(4, int(px)))
    return font


def _draw_pip(p, suit, cx, cy, size, flip=False):
    p.save()
    p.translate(cx, cy)
    if flip:
        p.rotate(180)
    p.setFont(_symbol_font(size))
    p.drawText(QRectF(-size, -size * 0.75, size * 2, size * 1.5), Qt.AlignCenter, SUIT_SYMBOLS[suit])
    p.restore()


@lru_cache(maxsize=None)
def face_pixmap(rank, suit, w=CARD_W, h=CARD_H):
    pm = QPixmap(w, h)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    p.setPen(QPen(QColor("#202020"), 1))
    p.setBrush(QColor("white"))
    p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 4, 4)
    color = QColor("#D00000") if suit in "DH" else QColor("#000000")
    p.setPen(color)
    rank_text = RANK_TEXT.get(rank, str(rank))
    # corner indices, top-left and (upside down) bottom-right
    for flip in (False, True):
        p.save()
        if flip:
            p.translate(w, h)
            p.rotate(180)
        font = QFont("Arial")
        font.setPixelSize(int(h * 0.15))
        font.setBold(True)
        p.setFont(font)
        p.drawText(QRectF(1, 2, 14, h * 0.15), Qt.AlignCenter, rank_text if rank != 10 else "10")
        _draw_pip(p, suit, 8, 2 + h * 0.15 + h * 0.06, h * 0.11)
        p.restore()
    inner = QRectF(w * 0.2, h * 0.08, w * 0.6, h * 0.84)
    if rank <= 10:
        size = h * (0.42 if rank == 1 and suit == "S" else 0.3 if rank == 1 else 0.17)
        for px, py in PIPS[rank]:
            _draw_pip(p, suit, inner.left() + px * inner.width() if rank > 3 or px != C else w / 2,
                      inner.top() + py * inner.height(), size, flip=py > 0.55)
    else:
        # Court cards: a framed panel with a big letter and the suit, mirrored top and bottom.
        frame = QRectF(w * 0.2, h * 0.11, w * 0.6, h * 0.78)
        g = QLinearGradient(frame.topLeft(), frame.bottomRight())
        tone = QColor("#F7E7B4") if rank == 13 else QColor("#E8F0FF") if rank == 12 else QColor("#FFE8E0")
        g.setColorAt(0, tone)
        g.setColorAt(1, tone.darker(112))
        p.setPen(QPen(color, 1))
        p.setBrush(g)
        p.drawRect(frame)
        p.setPen(QPen(QColor("#C9A227"), 1))
        p.drawRect(frame.adjusted(2, 2, -2, -2))
        p.drawLine(QPointF(frame.left() + 2, frame.center().y()), QPointF(frame.right() - 2, frame.center().y()))
        for flip in (False, True):
            p.save()
            p.translate(frame.center())
            if flip:
                p.rotate(180)
            p.setPen(color)
            font = QFont("Times New Roman")
            font.setPixelSize(int(h * 0.27))
            font.setBold(True)
            p.setFont(font)
            p.drawText(QRectF(-frame.width() / 2, -frame.height() / 2, frame.width() * 0.62, frame.height() / 2),
                       Qt.AlignCenter, rank_text)
            _draw_pip(p, suit, frame.width() * 0.22, -frame.height() * 0.25, h * 0.16)
            p.restore()
    p.end()
    return pm


@lru_cache(maxsize=None)
def back_pixmap(w=CARD_W, h=CARD_H):
    pm = QPixmap(w, h)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#202020"), 1))
    p.setBrush(QColor("white"))
    p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 4, 4)
    inner = QRectF(4, 4, w - 8, h - 8)
    g = QLinearGradient(inner.topLeft(), inner.bottomRight())
    g.setColorAt(0, QColor("#2A5DD6"))
    g.setColorAt(1, QColor("#13368F"))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawRoundedRect(inner, 3, 3)
    p.setClipRect(inner)
    p.setPen(QPen(QColor(255, 255, 255, 70), 1))
    for k in range(-h, w + h, 6):
        p.drawLine(k, 0, k + h, h)
        p.drawLine(k + h, 0, k, h)
    p.setClipping(False)
    p.setPen(QPen(QColor(255, 255, 255, 160), 1))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(inner.adjusted(3, 3, -3, -3), 3, 3)
    p.end()
    return pm


def card_pixmap(card):
    return face_pixmap(card.rank, card.suit) if card.face_up else back_pixmap()


def draw_slot(p, rect, label=""):
    """An empty pile spot on the felt."""
    p.setPen(QPen(QColor(0, 60, 0), 1.5))
    p.setBrush(QColor(0, 100, 0, 90))
    p.drawRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), 4, 4)
    if label:
        p.setPen(QColor(0, 70, 0))
        p.setFont(_symbol_font(rect.height() * 0.4))
        p.drawText(rect, Qt.AlignCenter, label)


# ---- the card table ------------------------------------------------------------------------------

class Pile:
    def __init__(self, kind, x, y, fan_up=0, fan_down=0, label="", index=0):
        self.kind, self.x, self.y = kind, x, y
        self.fan_up, self.fan_down = fan_up, fan_down      # vertical offset per face-up / face-down card
        self.label, self.index = label, index
        self.cards = []
        self.fan_x = 0                                     # horizontal fan (Draw Three waste)
        self.show_last = None                              # only fan the last N cards horizontally

    def card_rect(self, i):
        x, y = self.x, self.y
        for k in range(i):
            y += self.fan_up if self.cards[k].face_up else self.fan_down
        if self.fan_x and self.show_last:
            start = max(0, len(self.cards) - self.show_last)
            if i >= start:
                x += (i - start) * self.fan_x
        return QRect(int(x), int(y), CARD_W, CARD_H)

    def base_rect(self):
        return QRect(int(self.x), int(self.y), CARD_W, CARD_H)

    def top_rect(self):
        return self.card_rect(len(self.cards) - 1) if self.cards else self.base_rect()

    @property
    def top(self):
        return self.cards[-1] if self.cards else None


class CardTable(QWidget):
    """A green felt table with piles of cards you can drag between."""
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.piles = []
        self.drag = None            # (src pile, index, cards, grab offset, current pos)
        self.press = None
        self.animations = []
        self.setMouseTracking(False)
        self.setMinimumSize(560, 400)

    # rules (overridden by each game)
    def can_pick(self, pile, index):
        return False

    def can_drop(self, cards, src, dst):
        return False

    def dropped(self, cards, src, dst):
        dst.cards.extend(cards)

    def clicked(self, pile, index):
        pass

    def double_clicked(self, pile, index):
        pass

    def right_clicked(self):
        pass

    # ---- hit testing --------------------------------------------------------------------------------
    def hit(self, pos):
        """(pile, card index or -1 for an empty pile) at a point, top-most first."""
        for pile in reversed(self.piles):
            for i in range(len(pile.cards) - 1, -1, -1):
                if pile.card_rect(i).contains(pos):
                    return pile, i
            if pile.base_rect().contains(pos):
                return pile, -1
        return None, None

    def drop_target(self, rect, src):
        best, overlap = None, 0
        for pile in self.piles:
            if pile is src:
                continue
            r = pile.top_rect().intersected(rect)
            area = r.width() * r.height() if r.isValid() else 0
            if area > overlap:
                best, overlap = pile, area
        return best

    # ---- mouse ----------------------------------------------------------------------------------------
    def mousePressEvent(self, event):
        if self.animations:
            return
        pos = event.position().toPoint()
        if event.button() == Qt.RightButton:
            self.right_clicked()
            return
        pile, index = self.hit(pos)
        if pile is None:
            return
        self.press = (pile, index, pos)
        if index >= 0 and self.can_pick(pile, index):
            cards = pile.cards[index:]
            offset = pos - pile.card_rect(index).topLeft()
            self.drag = {"src": pile, "index": index, "cards": cards, "offset": offset, "pos": pos, "moved": False}

    def mouseMoveEvent(self, event):
        if self.drag is None:
            return
        pos = event.position().toPoint()
        if not self.drag["moved"] and (pos - self.press[2]).manhattanLength() < 4:
            return
        if not self.drag["moved"]:
            self.drag["moved"] = True
            del self.drag["src"].cards[self.drag["index"]:]
        self.drag["pos"] = pos
        self.update()

    def mouseReleaseEvent(self, event):
        drag, self.drag = self.drag, None
        press, self.press = self.press, None
        if drag is not None and drag["moved"]:
            rect = QRect(drag["pos"] - drag["offset"], QSize(CARD_W, CARD_H))
            dst = self.drop_target(rect, drag["src"])
            if dst is not None and self.can_drop(drag["cards"], drag["src"], dst):
                self.dropped(drag["cards"], drag["src"], dst)
            else:
                drag["src"].cards.extend(drag["cards"])   # snap back
            self.update()
            self.changed.emit()
            return
        if press is not None:
            self.clicked(press[0], press[1])
            self.update()
            self.changed.emit()

    def mouseDoubleClickEvent(self, event):
        if self.animations:
            return
        pile, index = self.hit(event.position().toPoint())
        if pile is not None:
            self.double_clicked(pile, index)
            self.update()
            self.changed.emit()

    # ---- painting -----------------------------------------------------------------------------------------
    def paint_background(self, p):
        p.fillRect(self.rect(), FELT)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self.paint_background(p)
        for pile in self.piles:
            if not pile.cards:
                draw_slot(p, pile.base_rect(), pile.label)
            for i, card in enumerate(pile.cards):
                p.drawPixmap(pile.card_rect(i).topLeft(), card_pixmap(card))
        if self.drag is not None and self.drag["moved"]:
            top_left = self.drag["pos"] - self.drag["offset"]
            dy = 0
            for card in self.drag["cards"]:
                p.drawPixmap(top_left + QPointF(0, dy).toPoint(), card_pixmap(card))
                dy += self.drag["src"].fan_up or 16
        self.paint_overlay(p)

    def paint_overlay(self, p):
        pass


# ---- Microsoft FreeCell / Solitaire style deals ----------------------------------------------------------

def ms_deal(seed):
    """The Microsoft FreeCell deal for game number `seed` (the same deals as Windows 2000/XP)."""
    state = seed
    cards = list(range(51, -1, -1))   # 0 = A of clubs, 1 = A of diamonds, ... (rank * 4 + suit, suits C D H S)
    for i in range(52):
        state = (214013 * state + 2531011) & 0x7FFFFFFF
        r = state >> 16
        j = 51 - r % (52 - i)
        cards[i], cards[j] = cards[j], cards[i]
    return [Card(c // 4 + 1, "CDHS"[c % 4], True) for c in cards]


def shuffled(cards, rng=None):
    rng = rng or random
    rng.shuffle(cards)
    return cards
