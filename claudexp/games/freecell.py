"""FreeCell, like Windows XP's: the Microsoft deal numbers (1 to 32000), four free cells, four home cells,
multi-card moves limited by free space, safe auto-play to home, Select Game, Restart and statistics."""
import random

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from .cards import CARD_H, CARD_W, CardTable, Pile, ms_deal
from .common import GameWindow, card_icon, message, open_game, save_stats, stats

GAP = 8
TOP = 10


class FreeCellTable(CardTable):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.game_number = None
        self.moves = 0
        self.won = False
        self.cells = [Pile("cell", GAP + i * (CARD_W + 2), TOP, index=i) for i in range(4)]
        home_x = GAP + 4 * (CARD_W + 2) + 2 * GAP + 40
        self.homes = [Pile("home", home_x + i * (CARD_W + 2), TOP, index=i, label="") for i in range(4)]
        col_w = CARD_W + GAP
        self.columns = [Pile("column", GAP + 6 + i * col_w, TOP + CARD_H + 26, fan_up=18, index=i) for i in range(8)]
        self.piles = [*self.cells, *self.homes, *self.columns]
        self.setMinimumSize(home_x + 4 * (CARD_W + 2) + GAP, 460)

    def deal(self, number):
        self.game_number = number
        for pile in self.piles:
            pile.cards = []
        for i, card in enumerate(ms_deal(number)):
            self.columns[i % 8].cards.append(card)
        self.moves, self.won = 0, False
        self._status()
        self.update()

    def _status(self):
        self.win.status.setText(f"Game #{self.game_number}" + ("" if not self.moves else f"      Moves: {self.moves}"))

    # ---- rules -------------------------------------------------------------------------------------------
    @staticmethod
    def _sequence(cards):
        return all(a.red != b.red and a.rank == b.rank + 1 for a, b in zip(cards, cards[1:]))

    def _max_move(self, to_empty_column=False):
        free = sum(1 for c in self.cells if not c.cards)
        empty = sum(1 for c in self.columns if not c.cards) - (1 if to_empty_column else 0)
        return (free + 1) * (2 ** max(0, empty))

    def can_pick(self, pile, index):
        if self.won or pile.kind == "home":
            return False
        if pile.kind == "cell":
            return True
        return self._sequence(pile.cards[index:]) and len(pile.cards) - index <= self._max_move()

    def can_drop(self, cards, src, dst):
        first = cards[0]
        if dst.kind == "cell":
            return len(cards) == 1 and not dst.cards
        if dst.kind == "home":
            top = dst.top
            return len(cards) == 1 and ((top is None and first.rank == 1) or
                                        (top is not None and top.suit == first.suit and top.rank + 1 == first.rank))
        top = dst.top
        if top is None:
            return len(cards) <= self._max_move(to_empty_column=True)
        return top.red != first.red and top.rank == first.rank + 1

    def dropped(self, cards, src, dst):
        dst.cards.extend(cards)
        self.moves += 1
        self._auto_play()
        self._status()
        self._check_win()

    def double_clicked(self, pile, index):
        """Double-click a column's bottom card: send it to a free cell (or home)."""
        if pile.kind not in ("column", "cell") or not pile.cards or index != len(pile.cards) - 1:
            return
        card = pile.top
        for home in self.homes:
            if self.can_drop([card], pile, home):
                pile.cards.pop()
                self.dropped([card], pile, home)
                return
        if pile.kind == "column":
            for cell in self.cells:
                if not cell.cards:
                    pile.cards.pop()
                    self.dropped([card], pile, cell)
                    return

    def _safe_home(self, card):
        """XP auto-plays a card home only when nothing could still need to sit on it."""
        if card.rank <= 2:
            return True
        opposite = [h for h in self.homes if h.top is not None and h.top.red != card.red]
        lowest = min([h.top.rank for h in opposite] + [0] * (2 - len(opposite)))
        return lowest >= card.rank - 1

    def _auto_play(self):
        moved = True
        while moved:
            moved = False
            for pile in [*self.cells, *self.columns]:
                card = pile.top
                if card is None or not self._safe_home(card):
                    continue
                for home in self.homes:
                    if self.can_drop([card], pile, home):
                        home.cards.append(pile.cards.pop())
                        moved = True
                        break

    def _check_win(self):
        if all(len(h.cards) == 13 for h in self.homes) and not self.won:
            self.won = True
            s = stats("freecell")
            s["wins"] = s.get("wins", 0) + 1
            s["streak"] = s.get("streak", 0) + 1
            save_stats("freecell", s)
            self.update()
            message(self.win.desktop, "Game Over", "Congratulations, you win!\n\nDo you want to play again?",
                    ("Yes", "No"), lambda b: b == "Yes" and self.win.new_game())

    def record_loss(self):
        if self.game_number is not None and self.moves and not self.won:
            s = stats("freecell")
            s["losses"] = s.get("losses", 0) + 1
            s["streak"] = 0
            save_stats("freecell", s)

    # ---- painting ------------------------------------------------------------------------------------------
    def paint_overlay(self, p):
        # The king between the free cells and home cells looks toward your last move.
        cx = self.cells[-1].x + CARD_W + GAP + 20
        font = QFont("Segoe UI Symbol")
        font.setPixelSize(34)
        p.setFont(font)
        p.setPen(QColor("#FFD700"))
        p.drawText(QRect(int(cx) - 20, TOP + 20, 40, 50), Qt.AlignCenter, "♔")


def open_freecell(desktop):
    def make():
        win = GameWindow(desktop, FreeCellTable)
        table = win.play

        def new_game():
            table.record_loss()
            table.deal(random.randint(1, 32000))

        def restart():
            if table.game_number:
                table.deal(table.game_number)

        win.new_game = new_game
        game_menu = win.menu.addMenu("&Game")
        game_menu.addAction("&New Game", new_game, "F2")
        game_menu.addAction("&Select Game...", lambda: _select_game(desktop, table), "F3")
        game_menu.addAction("&Restart Game", restart)
        game_menu.addSeparator()
        game_menu.addAction("S&tatistics...", lambda: message(desktop, "FreeCell Statistics", _stats_text()), "F4")
        game_menu.addSeparator()
        game_menu.addAction("E&xit", lambda: win.frame.request_close())
        help_menu = win.menu.addMenu("&Help")
        help_menu.addAction("&How to Play", lambda: message(desktop, "FreeCell", HOW_TO))
        new_game()
        return win

    return open_game(desktop, "freecell", "FreeCell", make, card_icon("H", "#D00000"), (690, 560))


def _select_game(desktop, table):
    from ..network import DialogBody, _fixed_window
    body = DialogBody()
    v = QVBoxLayout(body)
    v.addWidget(QLabel("Select a game number from 1 to 32000:"))
    edit = QLineEdit(str(random.randint(1, 32000)))
    v.addWidget(edit)
    row = QHBoxLayout()
    row.addStretch()
    ok, cancel = QPushButton("OK"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(75, 23)
        row.addWidget(b)
    v.addLayout(row)
    body.setFixedWidth(280)
    holder = {}

    def close():
        if holder.get("win") is not None:
            desktop.close_window(holder.pop("win"))

    def accept():
        try:
            number = int(edit.text())
        except ValueError:
            return
        if 1 <= number <= 32000:
            close()
            table.record_loss()
            table.deal(number)

    ok.clicked.connect(accept)
    edit.returnPressed.connect(accept)
    cancel.clicked.connect(close)
    holder["win"] = _fixed_window(desktop, "Game Number", body, close)
    desktop.open_window(holder["win"])
    edit.selectAll()
    edit.setFocus()


def _stats_text():
    s = stats("freecell")
    wins, losses = s.get("wins", 0), s.get("losses", 0)
    pct = int(100 * wins / (wins + losses)) if wins + losses else 0
    return f"Total: {pct}%\n\nWins: {wins}\nLosses: {losses}\nCurrent streak: {s.get('streak', 0)} wins"


HOW_TO = ("Move all the cards to the four home cells at the upper right, building each suit up from Ace to King.\n\n"
          "In the columns, stack cards in descending order, alternating red and black. The four free cells at the "
          "upper left hold one card each. You can move several cards at once if there are enough free cells and "
          "empty columns.\n\nDouble-click a card to send it to a free cell.")
