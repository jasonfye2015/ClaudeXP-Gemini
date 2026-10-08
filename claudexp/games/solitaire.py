"""Solitaire (Klondike), like Windows XP's: Draw One or Draw Three, Standard scoring with a timer,
double-click to send a card home, right-click to auto-finish, and the bouncing-cards win cascade."""
import random

from PySide6.QtCore import QPointF, QRect, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QPainter, QPixmap

from .cards import CARD_H, CARD_W, FELT, CardTable, Pile, card_pixmap, deck, shuffled
from .common import GameWindow, card_icon, message, open_game, save_stats, stats

GAP = 11
TOP = 10


class Klondike(CardTable):
    def __init__(self, win):
        super().__init__()
        self.win = win
        s = stats("solitaire")
        self.draw_three = bool(s.get("draw_three", False))
        self.score = 0
        self.seconds = 0
        self.passes = 0
        self.won = False
        self.cascade = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.cascade_timer = QTimer(self)
        self.cascade_timer.timeout.connect(self._cascade_step)
        x = lambda col: GAP + col * (CARD_W + GAP)
        self.stock = Pile("stock", x(0), TOP)
        self.waste = Pile("waste", x(1), TOP)
        self.waste.fan_x, self.waste.show_last = 14, 3
        self.foundations = [Pile("foundation", x(3 + i), TOP, index=i) for i in range(4)]
        self.tableau = [Pile("tableau", x(i), TOP + CARD_H + 18, fan_up=16, fan_down=4, index=i) for i in range(7)]
        self.piles = [self.stock, self.waste, *self.foundations, *self.tableau]
        self.setMinimumSize(x(7), 440)
        self.new_game()

    # ---- setup ------------------------------------------------------------------------------------
    def new_game(self):
        self.stop_cascade()
        cards = shuffled(deck())
        for pile in self.piles:
            pile.cards = []
        for col in range(7):
            for row in range(col + 1):
                card = cards.pop()
                card.face_up = row == col
                self.tableau[col].cards.append(card)
        self.stock.cards = cards
        self.score, self.seconds, self.passes, self.won = 0, 0, 0, False
        self.timer.stop()
        self._status()
        self.update()

    def stop(self):
        self.timer.stop()
        self.stop_cascade()

    def _start_clock(self):
        if not self.timer.isActive() and not self.won:
            self.timer.start(1000)

    def _tick(self):
        self.seconds += 1
        if self.seconds % 10 == 0:
            self.score = max(0, self.score - 2)
        self._status()

    def _status(self):
        self.win.status.setText(f"Score: {self.score}      Time: {self.seconds}")

    def _add(self, points):
        self.score = max(0, self.score + points)
        self._status()

    # ---- rules ----------------------------------------------------------------------------------------------
    def can_pick(self, pile, index):
        if pile.kind == "stock":
            return False
        if pile.kind in ("waste", "foundation"):
            return index == len(pile.cards) - 1
        return pile.cards[index].face_up

    def can_drop(self, cards, src, dst):
        first = cards[0]
        if dst.kind == "foundation":
            if len(cards) != 1:
                return False
            top = dst.top
            return (top is None and first.rank == 1) or (top is not None and top.suit == first.suit and top.rank + 1 == first.rank)
        if dst.kind == "tableau":
            top = dst.top
            if top is None:
                return first.rank == 13
            return top.face_up and top.red != first.red and top.rank == first.rank + 1
        return False

    def dropped(self, cards, src, dst):
        dst.cards.extend(cards)
        if dst.kind == "foundation":
            self._add(10)
        elif src.kind == "waste":
            self._add(5)
        elif src.kind == "foundation":
            self._add(-15)
        self._after_move(src)

    def _after_move(self, src):
        self._start_clock()
        if src.kind == "tableau" and src.cards and not src.top.face_up:
            src.top.face_up = True
            self._add(5)
        if all(len(f.cards) == 13 for f in self.foundations):
            self._win()

    def clicked(self, pile, index):
        if self.won:
            return
        if pile.kind == "tableau" and pile.cards and not pile.top.face_up and index == len(pile.cards) - 1:
            pile.top.face_up = True
            self._add(5)
            self._start_clock()
        elif pile.kind == "stock":
            self._start_clock()
            if self.stock.cards:
                for _ in range(3 if self.draw_three else 1):
                    if self.stock.cards:
                        card = self.stock.cards.pop()
                        card.face_up = True
                        self.waste.cards.append(card)
            elif self.waste.cards:
                self.passes += 1
                if self.passes > (3 if self.draw_three else 1) or not self.draw_three:
                    self._add(-20 if self.draw_three else -100)
                while self.waste.cards:
                    card = self.waste.cards.pop()
                    card.face_up = False
                    self.stock.cards.append(card)

    def double_clicked(self, pile, index):
        if pile.kind in ("waste", "tableau") and pile.cards and index == len(pile.cards) - 1 and pile.top.face_up:
            self._send_home(pile)

    def _send_home(self, pile):
        card = pile.top
        for f in self.foundations:
            if self.can_drop([card], pile, f):
                pile.cards.pop()
                self.dropped([card], pile, f)
                return True
        return False

    def right_clicked(self):
        """Right-click: move everything that can go home, home."""
        moved = True
        while moved and not self.won:
            moved = False
            for pile in [self.waste, *self.tableau]:
                if pile.cards and pile.top.face_up and self._send_home(pile):
                    moved = True
        self.update()

    # ---- winning: the bouncing cascade -------------------------------------------------------------------------
    def _win(self):
        self.won = True
        self.timer.stop()
        if self.seconds > 30:
            self._add(int(700000 / self.seconds))
        s = stats("solitaire")
        s["wins"] = s.get("wins", 0) + 1
        s["best"] = max(s.get("best", 0), self.score)
        s["draw_three"] = self.draw_three
        save_stats("solitaire", s)
        self.cascade = {"canvas": None, "cards": [], "next": 0, "card": None}
        QTimer.singleShot(300, lambda: self.cascade_timer.start(16))

    def stop_cascade(self):
        self.cascade_timer.stop()
        self.cascade = None

    def _cascade_step(self):
        c = self.cascade
        if c is None:
            return
        if c["canvas"] is None:
            canvas = QPixmap(self.size())
            canvas.fill(FELT)
            p = QPainter(canvas)
            for f in self.foundations:
                if f.cards:
                    p.drawPixmap(f.base_rect().topLeft(), card_pixmap(f.top))
            p.end()
            c["canvas"] = canvas
        if c["card"] is None:
            piles = [f for f in self.foundations if f.cards]
            if not piles:
                self.cascade_timer.stop()
                QTimer.singleShot(500, self._ask_again)
                return
            f = piles[c["next"] % len(piles)]
            c["next"] += 1
            card = f.cards.pop()
            c["card"] = {"card": card, "x": float(f.x), "y": float(f.y),
                         "vx": random.choice((-1, 1)) * random.uniform(2.5, 6), "vy": random.uniform(-6, 0)}
        b = c["card"]
        p = QPainter(c["canvas"])
        for _ in range(2):
            b["vy"] += 0.6
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            floor = self.height() - CARD_H
            if b["y"] > floor:
                b["y"] = floor
                b["vy"] = -b["vy"] * 0.75
            p.drawPixmap(int(b["x"]), int(b["y"]), card_pixmap(b["card"]))
        p.end()
        if b["x"] < -CARD_W or b["x"] > self.width():
            c["card"] = None
        self.update()

    def _ask_again(self):
        message(self.win.desktop, "Game Over", "Congratulations, you won!\n\nDeal again?", ("Yes", "No"),
                lambda b: b == "Yes" and self.new_game())

    def paintEvent(self, event):
        if self.cascade is not None and self.cascade.get("canvas") is not None:
            QPainter(self).drawPixmap(0, 0, self.cascade["canvas"])
            return
        super().paintEvent(event)


def open_solitaire(desktop):
    def make():
        win = GameWindow(desktop, Klondike)
        game = win.play
        game_menu = win.menu.addMenu("&Game")
        game_menu.addAction("&Deal", game.new_game, "F2")
        game_menu.addSeparator()
        group = QActionGroup(win)
        for label, three in (("Draw &One", False), ("Draw &Three", True)):
            act = QAction(label, win, checkable=True, checked=game.draw_three == three)
            act.triggered.connect(lambda _c=False, t=three: (setattr(game, "draw_three", t), _save_draw(t), game.new_game()))
            group.addAction(act)
            game_menu.addAction(act)
        game_menu.addSeparator()
        game_menu.addAction("E&xit", lambda: win.frame.request_close())
        help_menu = win.menu.addMenu("&Help")
        help_menu.addAction("&How to Play", lambda: message(desktop, "Solitaire", HOW_TO))
        help_menu.addAction("Statistics", lambda: message(desktop, "Solitaire", _stats_text()))
        return win

    return open_game(desktop, "solitaire", "Solitaire", make, card_icon("S"), (8 * (CARD_W + GAP) + 30, 520))


def _save_draw(three):
    s = stats("solitaire")
    s["draw_three"] = three
    save_stats("solitaire", s)


def _stats_text():
    s = stats("solitaire")
    return f"Games won: {s.get('wins', 0)}\nBest score: {s.get('best', 0)}"


HOW_TO = ("Build up the four piles at the top from Ace to King, one suit each.\n\n"
          "Down below, stack cards in descending order, alternating red and black. Only a King can go in "
          "an empty column. Click the deck to turn cards over.\n\n"
          "Double-click a card to send it up to its pile; right-click the table to send every card that can go.")
