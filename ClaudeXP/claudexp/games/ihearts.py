"""Internet Hearts on the Zone: the same Hearts as the offline game, but the other three seats are your buddies
(or strangers). Beginners play a little carelessly; the game ends at 100 and the lowest score wins."""
import random

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter

from .common import card_icon
from .hearts import HeartsTable, _you, choose_card, legal_cards, points
from .zone import open_zone_game


class InternetHearts(HeartsTable):
    moved = Signal(str, dict)
    finished = Signal(str)
    SEATS = 3
    SELF_DRIVEN = True
    AI_DELAY = 900
    HOW_TO = ("Hearts with three other people on the Zone. Try to take as few points as you can: each heart is one "
              "point and the queen of spades is 13. Pass three cards before each hand (left, right, across, then "
              "none). Take every heart and the queen to 'shoot the moon'. The game ends when someone reaches 100; "
              "the lowest score wins.")

    def __init__(self, win):
        super().__init__(win, start=False)
        self.locked = True
        self.banner = ""
        self.skills = [1, 1, 1]

    # ---- the Zone's side ----------------------------------------------------------------------------------------
    def set_players(self, names, skills):
        self.names = ["You", *names]
        self.skills = list(skills)

    def start(self, user_first):
        self.locked = False
        self.new_game()

    def result(self):
        return None

    def colors(self):
        return (None, None)

    def score_text(self):
        return "Scores:  " + "   ".join(f"{n} {s}" for n, s in zip([_you(), *self.names[1:]], self.scores))

    def stop(self):
        self.timer.stop()

    def ranking(self):
        names = [_you(), *self.names[1:]]
        return sorted(zip(self.scores, range(4), names))

    def result_text(self):
        low = min(self.scores)
        winners = [n for s, _i, n in self.ranking() if s == low]
        if winners == [_you()]:
            return f"You won with {low} points!"
        return f"{' and '.join(winners)} won with {low} points."

    def outcome_for(self, opponent):
        order = ", ".join(f"{n} {s}" for s, _i, n in self.ranking())
        seat = self.names.index(opponent.name)
        place = [i for _s, i, _n in self.ranking()].index(seat) + 1
        word = {1: "I won", 2: "I came second", 3: "I came third", 4: "I came last"}[place]
        return f"{word} (final scores: {order})"

    # ---- hooks from the table ----------------------------------------------------------------------------------
    def choose(self, player):
        if self.skills[player - 1] == 0 and random.random() < 0.3:
            return random.choice(legal_cards(self, player))
        return choose_card(self, player)

    def trick_taken(self, winner, cards):
        pts = sum(points(c) for c in cards)
        queen = any(c.suit == "S" and c.rank == 12 for c in cards)
        who = "user" if winner == 0 else str(winner)
        self.moved.emit(who, {"captured": 2 if queen else 0, "oops": queen and winner != 0, "big": pts >= 5})

    def game_over(self):
        low = min(self.scores)
        res = "user" if self.scores[0] == low and self.scores.count(low) == 1 else \
            "draw" if self.scores[0] == low else "ai"
        self.locked = True
        self.finished.emit(res)

    # ---- input and drawing -------------------------------------------------------------------------------------
    def mousePressEvent(self, event):
        if self.locked:
            return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.banner:
            p = QPainter(self)
            p.fillRect(self.rect(), QColor(0, 0, 0, 110))
            f = QFont("Tahoma")
            f.setPixelSize(16)
            f.setBold(True)
            p.setFont(f)
            p.setPen(QColor("white"))
            p.drawText(self.rect(), Qt.AlignCenter | Qt.TextWordWrap, self.banner)


def open_internet_hearts(desktop):
    return open_zone_game(desktop, "Hearts", InternetHearts, (None, None), card_icon("H", "#D00000"), (900, 620))
