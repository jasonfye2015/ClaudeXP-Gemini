"""Spider Solitaire, like Windows XP's: 1, 2 or 4 suits, ten columns, deal a new row from the stock,
complete King-to-Ace runs of one suit to clear them, score from 500, Undo."""
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QAction, QActionGroup

from .cards import CARD_H, CARD_W, Card, CardTable, Pile, back_pixmap, card_pixmap, deck, shuffled
from .common import GameWindow, card_icon, message, open_game, save_stats, stats

GAP = 6
TOP = 8
SUIT_SETS = {1: "SSSS", 2: "SSHH", 4: "SHDC"}


class Spider(CardTable):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.suits = int(stats("spider").get("suits", 1))
        self.columns = [Pile("column", GAP + i * (CARD_W + GAP), TOP, fan_up=17, fan_down=6, index=i) for i in range(10)]
        self.piles = list(self.columns)
        self.stock = []
        self.done = []          # suits of completed runs
        self.history = []
        self._before = None
        self.score = 500
        self.moves = 0
        self.setMinimumSize(10 * (CARD_W + GAP) + GAP, 480)

    def new_game(self):
        cards = shuffled(deck(decks=2, suits=SUIT_SETS[self.suits]))
        for pile in self.columns:
            pile.cards = []
        for i in range(54):
            card = cards.pop()
            self.columns[i % 10].cards.append(card)
        for pile in self.columns:
            pile.top.face_up = True
        self.stock = cards
        self.done, self.history, self.score, self.moves = [], [], 500, 0
        self._status()
        self.update()

    def _status(self):
        self.win.status.setText(f"Score: {self.score}      Moves: {self.moves}")

    def _snapshot(self):
        return ([[(c.rank, c.suit, c.face_up) for c in p.cards] for p in self.columns],
                [(c.rank, c.suit) for c in self.stock], list(self.done), self.score, self.moves)

    def undo(self):
        if not self.history:
            return
        cols, stock, done, score, moves = self.history.pop()
        for pile, cards in zip(self.columns, cols):
            pile.cards = [Card(r, s, f) for r, s, f in cards]
        self.stock = [Card(r, s) for r, s in stock]
        self.done, self.score, self.moves = done, score - 1, moves + 1   # an undo still costs a move
        self._status()
        self.update()

    # ---- rules ---------------------------------------------------------------------------------------------
    @staticmethod
    def _run(cards):
        return all(c.face_up for c in cards) and all(
            a.suit == b.suit and a.rank == b.rank + 1 for a, b in zip(cards, cards[1:]))

    def can_pick(self, pile, index):
        return self._run(pile.cards[index:])

    def can_drop(self, cards, src, dst):
        top = dst.top
        return top is None or top.rank == cards[0].rank + 1

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.stock and self.stock_rect().contains(event.position().toPoint()):
                self.deal_row()
                return
            self._before = self._snapshot()          # kept for Undo if this turns into a move
        super().mousePressEvent(event)

    def dropped(self, cards, src, dst):
        self.history.append(self._before)
        dst.cards.extend(cards)
        self.score -= 1
        self.moves += 1
        if src.cards and not src.top.face_up:
            src.top.face_up = True
        self._clear_runs(dst)
        self._status()

    def _clear_runs(self, pile):
        if len(pile.cards) >= 13 and self._run(pile.cards[-13:]) and pile.cards[-13].rank == 13:
            self.done.append(pile.cards[-1].suit)
            del pile.cards[-13:]
            if pile.cards and not pile.top.face_up:
                pile.top.face_up = True
            self.score += 100
            if len(self.done) == 8:
                s = stats("spider")
                s["wins"] = s.get("wins", 0) + 1
                s["best"] = max(s.get("best", 0), self.score)
                save_stats("spider", s)
                message(self.win.desktop, "Game Over",
                        f"Congratulations, you won!\n\nScore: {self.score}\n\nDo you want to start another game?",
                        ("Yes", "No"), lambda b: b == "Yes" and self.new_game())

    def stock_rect(self):
        n = len(self.stock) // 10
        return QRect(self.width() - GAP - CARD_W - (n - 1) * 12, self.height() - CARD_H - GAP, CARD_W + (n - 1) * 12, CARD_H)

    def deal_row(self):
        if not self.stock:
            return
        if any(not p.cards for p in self.columns):
            message(self.win.desktop, "Spider", "You are not allowed to deal a new row while any columns are empty.")
            return
        self.history.append(self._snapshot())
        for pile in self.columns:
            card = self.stock.pop()
            card.face_up = True
            pile.cards.append(card)
        self.moves += 1
        for pile in self.columns:
            self._clear_runs(pile)
        self._status()
        self.update()

    def clicked(self, pile, index):
        pass

    def mouseDoubleClickEvent(self, event):
        pass

    # ---- painting --------------------------------------------------------------------------------------------
    def paint_overlay(self, p):
        n = len(self.stock) // 10
        r = self.stock_rect()
        for i in range(n):
            p.drawPixmap(r.x() + i * 12, r.y(), back_pixmap())
        for i, suit in enumerate(self.done):
                p.drawPixmap(GAP + i * 14, self.height() - CARD_H - GAP, card_pixmap(Card(13, suit, True)))


def open_spider(desktop):
    def make():
        win = GameWindow(desktop, Spider)
        game = win.play
        game_menu = win.menu.addMenu("&Game")
        game_menu.addAction("&New Game", game.new_game, "F2")
        game_menu.addAction("&Undo", game.undo, "Ctrl+Z")
        game_menu.addAction("&Deal Next Row", game.deal_row, "D")
        game_menu.addSeparator()
        group = QActionGroup(win)
        for n, label in ((1, "Easy: &One Suit"), (2, "Medium: &Two Suits"), (4, "Difficult: &Four Suits")):
            act = QAction(label, win, checkable=True, checked=game.suits == n)
            act.triggered.connect(lambda _c=False, n=n: _set_suits(game, n))
            group.addAction(act)
            game_menu.addAction(act)
        game_menu.addSeparator()
        game_menu.addAction("S&tatistics", lambda: message(desktop, "Spider Solitaire", _stats_text()))
        game_menu.addAction("E&xit", lambda: win.frame.request_close())
        help_menu = win.menu.addMenu("&Help")
        help_menu.addAction("&How to Play", lambda: message(desktop, "Spider Solitaire", HOW_TO))
        game.new_game()
        return win

    return open_game(desktop, "spider", "Spider Solitaire", make, card_icon("S"), (10 * (CARD_W + GAP) + 20, 600))


def _set_suits(game, n):
    game.suits = n
    s = stats("spider")
    s["suits"] = n
    save_stats("spider", s)
    game.new_game()


def _stats_text():
    s = stats("spider")
    return f"Games won: {s.get('wins', 0)}\nHigh score: {s.get('best', 0)}"


HOW_TO = ("Remove all the cards by building runs from King down to Ace in one suit; a finished run leaves the table.\n\n"
          "You can put any card on a card one higher, but you can only move a group of cards together if they are "
          "all the same suit and in order. Click the stock at the bottom right to deal a new row (no empty columns).")
