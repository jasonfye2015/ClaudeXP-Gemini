"""Hearts, like Windows XP's (offline): you against Pauline, Michele and Ben. Pass three cards left, right,
across, then hold; the 2 of clubs leads; no hearts until they're broken; the queen of spades is 13 points;
take them all to shoot the moon. The game ends when someone reaches 100, and the lowest score wins."""
from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QWidget

from .cards import CARD_H, CARD_W, FELT, back_pixmap, card_pixmap, deck, shuffled
from .common import GameWindow, card_icon, message, open_game

NAMES = ["You", "Pauline", "Michele", "Ben"]           # south, west, north, east (play goes clockwise)
PASSES = [("left", 1), ("right", 3), ("across", 2), (None, 0)]
SUIT_ORDER = "CDSH"
SPACING = 20


def value(card):
    return 14 if card.rank == 1 else card.rank


def points(card):
    return 13 if (card.suit, card.rank) == ("S", 12) else 1 if card.suit == "H" else 0


def sort_hand(cards):
    cards.sort(key=lambda c: (SUIT_ORDER.index(c.suit), value(c)))


class HeartsTable(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.setMinimumSize(620, 500)
        self.button = QPushButton("", self)
        self.button.setFixedSize(110, 25)
        self.button.clicked.connect(self._button)
        self.button.hide()
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._step)
        self.new_game()

    # ---- game flow ---------------------------------------------------------------------------------------
    def new_game(self):
        self.timer.stop()
        self.scores = [0, 0, 0, 0]
        self.history = []             # per-hand points
        self.hand_number = 0
        self.deal()

    def stop(self):
        self.timer.stop()

    def deal(self):
        cards = shuffled(deck())
        for c in cards:
            c.face_up = True
        self.hands = [sorted_hand(cards[i::4]) for i in range(4)]
        self.taken = [[], [], [], []]
        self.trick = []               # [(player, card)]
        self.selected = set()
        self.hearts_broken = False
        self.first_trick = True
        direction, self.pass_shift = PASSES[self.hand_number % 4]
        self.leader = None
        if direction:
            self.phase = "pass"
            self._say(f"Select three cards to pass to {NAMES[self.pass_shift]}.")
            self._show_button(f"Pass {direction.title()}", enabled=False)
        else:
            self._say("There is no passing this hand.")
            self._start_play()
        self.update()

    def _start_play(self):
        self.phase = "play"
        self.button.hide()
        self.leader = next(i for i, h in enumerate(self.hands) if any(c.suit == "C" and c.rank == 2 for c in h))
        self.turn = self.leader
        self._next_turn()

    def _next_turn(self):
        if len(self.trick) == 4:
            self.phase = "collect"
            self.timer.start(1000)
            return
        if self.turn == 0:
            self._say("Your turn. Click a card to play it." if self.trick or not self.first_trick
                      else "You have the two of clubs; click it to lead.")
        else:
            self._say(f"Waiting for {NAMES[self.turn]} to play.")
            self.timer.start(450)
        self.update()

    def _step(self):
        if self.phase == "collect":
            self._collect()
        elif self.phase == "play" and self.turn != 0:
            self._play(self.turn, choose_card(self, self.turn))

    def _play(self, player, card):
        self.hands[player].remove(card)
        self.trick.append((player, card))
        if card.suit == "H":
            self.hearts_broken = True
        self.turn = (player + 1) % 4
        self._next_turn()

    def _collect(self):
        lead = self.trick[0][1].suit
        winner = max((pc for pc in self.trick if pc[1].suit == lead), key=lambda pc: value(pc[1]))[0]
        self.taken[winner].extend(c for _, c in self.trick)
        self.trick = []
        self.first_trick = False
        if not self.hands[0]:
            self._end_hand()
            return
        self.phase = "play"
        self.leader = self.turn = winner
        self._next_turn()

    def _end_hand(self):
        got = [sum(points(c) for c in t) for t in self.taken]
        note = ""
        if 26 in got:
            shooter = got.index(26)
            got = [0 if i == shooter else 26 for i in range(4)]
            note = f"{NAMES[shooter]} shot the moon!" if shooter else "You shot the moon!"
        self.scores = [a + b for a, b in zip(self.scores, got)]
        self.history.append(got)
        self.hand_number += 1
        self.phase = "scores"
        self._say(note or "The hand is over.")
        self.update()
        over = max(self.scores) >= 100
        _score_sheet(self, note, over)

    def after_scores(self, over):
        if over:
            self.new_game()
        else:
            self.deal()

    # ---- you ------------------------------------------------------------------------------------------------
    def legal(self, player, card):
        return card in legal_cards(self, player)

    def _card_rects(self):
        hand = self.hands[0]
        x0 = (self.width() - (CARD_W + SPACING * (len(hand) - 1))) // 2
        y = self.height() - CARD_H - 12
        return [QRect(x0 + i * SPACING, y - (22 if c in self.selected else 0), CARD_W, CARD_H) for i, c in enumerate(hand)]

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        pos = event.position().toPoint()
        rects = self._card_rects()
        hit = None
        for i in range(len(rects) - 1, -1, -1):
            if rects[i].contains(pos):
                hit = self.hands[0][i]
                break
        if hit is None:
            return
        if self.phase == "pass":
            if hit in self.selected:
                self.selected.discard(hit)
            elif len(self.selected) < 3:
                self.selected.add(hit)
            self.button.setEnabled(len(self.selected) == 3)
            self.update()
        elif self.phase == "play" and self.turn == 0:
            if self.legal(0, hit):
                self._play(0, hit)
            else:
                self._say(why_illegal(self, hit))

    def _button(self):
        if self.phase == "pass" and len(self.selected) == 3:
            self._do_pass()

    def _do_pass(self):
        outgoing = [list(self.selected)] + [choose_pass(self.hands[i]) for i in (1, 2, 3)]
        for i, cards in enumerate(outgoing):
            for c in cards:
                self.hands[i].remove(c)
        received = None
        for i, cards in enumerate(outgoing):
            to = (i + self.pass_shift) % 4
            self.hands[to].extend(cards)
            sort_hand(self.hands[to])
            if to == 0:
                received = cards
        self.selected = set(received)          # show what you got, raised, for a moment
        self.phase = "received"
        self._show_button("OK")
        self.button.clicked.disconnect()
        self.button.clicked.connect(self._received_ok)
        self._say(f"You received these cards from {NAMES[(0 - self.pass_shift) % 4]}.")
        self.update()

    def _received_ok(self):
        self.button.clicked.disconnect()
        self.button.clicked.connect(self._button)
        self.selected = set()
        self._start_play()

    # ---- display ----------------------------------------------------------------------------------------------
    def _say(self, text):
        self.win.status.setText(text)

    def _show_button(self, text, enabled=True):
        self.button.setText(text)
        self.button.setEnabled(enabled)
        self.button.move(self.width() // 2 - 55, self.height() // 2 - 12)
        self.button.show()

    def resizeEvent(self, event):
        self.button.move(self.width() // 2 - 55, self.height() // 2 - 12)

    def _trick_pos(self, player):
        cx, cy = self.width() // 2, self.height() // 2 - 20
        return {0: QPoint(cx - CARD_W // 2, cy + 6), 1: QPoint(cx - CARD_W - 30, cy - CARD_H // 2),
                2: QPoint(cx - CARD_W // 2, cy - CARD_H - 6), 3: QPoint(cx + 30, cy - CARD_H // 2)}[player]

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), FELT)
        w, h = self.width(), self.height()
        font = QFont("Tahoma")
        font.setPixelSize(11)
        font.setBold(True)
        p.setFont(font)
        # opponents' hands (backs)
        n = len(self.hands[2])
        x0 = (w - (CARD_W + 12 * max(0, n - 1))) // 2
        for i in range(n):
            p.drawPixmap(x0 + i * 12, 14, back_pixmap())
        for player, x in ((1, 14), (3, w - 14 - CARD_W)):
            n = len(self.hands[player])
            y0 = (h - (CARD_H + 12 * max(0, n - 1))) // 2 - 20
            for i in range(n):
                p.drawPixmap(x, y0 + i * 12, back_pixmap())
        # names
        p.setPen(QColor("white"))
        p.drawText(QRect(0, 14 + CARD_H + 2, w, 16), Qt.AlignHCenter, NAMES[2])
        p.drawText(QRect(14, h // 2 + 130, CARD_W + 40, 16), Qt.AlignLeft, NAMES[1])
        p.drawText(QRect(w - 14 - CARD_W - 40, h // 2 + 130, CARD_W + 40, 16), Qt.AlignRight, NAMES[3])
        p.drawText(QRect(0, h - CARD_H - 12 - 40, w, 16), Qt.AlignHCenter, NAMES[0] if NAMES[0] != "You" else _you())
        # the trick
        for player, card in self.trick:
            p.drawPixmap(self._trick_pos(player), card_pixmap(card))
        # your hand (cards you can't play right now are shaded)
        my_turn = self.phase == "play" and self.turn == 0
        hand = self.hands[0]
        for i, (rect, card) in enumerate(zip(self._card_rects(), hand)):
            p.drawPixmap(rect.topLeft(), card_pixmap(card))
            if my_turn and not self.legal(0, card):
                width = SPACING if i < len(hand) - 1 else CARD_W
                p.fillRect(QRect(rect.x() + 1, rect.y() + 1, width - 1, CARD_H - 2), QColor(0, 0, 0, 45))


def sorted_hand(cards):
    sort_hand(cards)
    return cards


def _you():
    try:
        from .. import user
        return user.user_name()
    except Exception:
        return "You"


# ---- rules and the computer players ------------------------------------------------------------------------------

def legal_cards(t, player):
    hand = t.hands[player]
    if not t.trick:
        if t.first_trick:
            return [c for c in hand if c.suit == "C" and c.rank == 2]
        if t.hearts_broken or all(c.suit == "H" for c in hand):
            return list(hand)
        return [c for c in hand if c.suit != "H"]
    lead = t.trick[0][1].suit
    follow = [c for c in hand if c.suit == lead]
    if follow:
        return follow
    if t.first_trick:
        clean = [c for c in hand if not points(c)]
        if clean:
            return clean
    return list(hand)


def why_illegal(t, card):
    if not t.trick and t.first_trick:
        return "You must lead the two of clubs."
    if not t.trick:
        return "Hearts have not been broken yet."
    if any(c.suit == t.trick[0][1].suit for c in t.hands[0]):
        return "You must follow suit."
    return "You can't play points on the first trick."


def choose_pass(hand):
    """Get rid of the dangerous cards: the queen, ace and king of spades (unless well guarded), then high cards."""
    spades = sum(c.suit == "S" for c in hand)

    def danger(c):
        v = value(c)
        if c.suit == "S" and v >= 12:
            return 100 + v if spades < 5 else v
        if c.suit == "H":
            return v + 3
        return v
    return sorted(hand, key=danger, reverse=True)[:3]


def choose_card(t, player):
    options = legal_cards(t, player)
    hand = t.hands[player]
    if len(options) == 1:
        return options[0]
    if not t.trick:
        # Lead low, from a suit other than hearts; don't lead high spades while the queen is out.
        safe = [c for c in options if not (c.suit == "S" and value(c) >= 12)] or options
        return min(safe, key=lambda c: (c.suit == "H", value(c)))
    lead = t.trick[0][1].suit
    winning = max((c for _, c in t.trick if c.suit == lead), key=value)
    trick_points = sum(points(c) for _, c in t.trick)
    if options[0].suit == lead:
        under = [c for c in options if value(c) < value(winning)]
        if under:
            return max(under, key=value)              # duck as high as possible
        if len(t.trick) == 3 and trick_points == 0:
            no_queen = [c for c in options if not (c.suit == "S" and c.rank == 12)] or options
            return max(no_queen, key=value)           # we take it anyway, so take it high
        no_queen = [c for c in options if not (c.suit == "S" and c.rank == 12)] or options
        return min(no_queen, key=value)
    # Void in the led suit: dump the queen, then hearts, then the highest card.
    for c in options:
        if c.suit == "S" and c.rank == 12:
            return c
    hearts = [c for c in options if c.suit == "H"]
    if hearts:
        return max(hearts, key=value)
    return max(options, key=lambda c: (c.suit == "S" and value(c) > 12, value(c)))


# ---- the score sheet ---------------------------------------------------------------------------------------------

def _score_sheet(table, note, over):
    from ..network import DialogBody, _fixed_window
    desktop = table.win.desktop
    body = DialogBody()
    grid = QGridLayout(body)
    grid.setHorizontalSpacing(18)
    names = [_you(), *NAMES[1:]]
    for col, name in enumerate(names):
        lab = QLabel(f"<b>{name}</b>")
        lab.setAlignment(Qt.AlignRight)
        grid.addWidget(lab, 0, col + 1)
    row = 1
    for i, got in enumerate(table.history[-8:]):
        grid.addWidget(QLabel(f"Hand {len(table.history) - min(8, len(table.history)) + i + 1}"), row, 0)
        for col, v in enumerate(got):
            lab = QLabel(str(v))
            lab.setAlignment(Qt.AlignRight)
            grid.addWidget(lab, row, col + 1)
        row += 1
    grid.addWidget(QLabel("<b>Total</b>"), row, 0)
    for col, v in enumerate(table.scores):
        lab = QLabel(f"<b>{v}</b>")
        lab.setAlignment(Qt.AlignRight)
        grid.addWidget(lab, row, col + 1)
    row += 1
    if over:
        low = min(table.scores)
        winners = [names[i] for i, s in enumerate(table.scores) if s == low]
        note = (note + "\n\n" if note else "") + (
            "You won the game!" if winners == [names[0]] else f"{' and '.join(winners)} won the game.")
    if note:
        grid.addWidget(QLabel(note), row, 0, 1, 5)
        row += 1
    ok = QPushButton("OK")
    ok.setFixedSize(75, 23)
    grid.addWidget(ok, row, 0, 1, 5, alignment=Qt.AlignCenter)
    holder = {}

    def close():
        if holder.get("win") is not None:
            desktop.close_window(holder.pop("win"))
            table.after_scores(over)

    ok.clicked.connect(close)
    holder["win"] = _fixed_window(desktop, "Game Over" if over else "Score", body, close)
    desktop.open_window(holder["win"])


def open_hearts(desktop):
    def make():
        win = GameWindow(desktop, HeartsTable)
        table = win.play
        game_menu = win.menu.addMenu("&Game")
        game_menu.addAction("&New Game", table.new_game, "F2")
        game_menu.addSeparator()
        game_menu.addAction("&Score...", lambda: message(desktop, "Hearts Score", _score_text(table)), "F4")
        game_menu.addSeparator()
        game_menu.addAction("E&xit", lambda: win.frame.request_close())
        help_menu = win.menu.addMenu("&Help")
        help_menu.addAction("&How to Play", lambda: message(desktop, "Hearts", HOW_TO))
        return win

    return open_game(desktop, "hearts", "Hearts", make, card_icon("H", "#D00000"), (660, 590))


def _score_text(table):
    names = [_you(), *NAMES[1:]]
    return "\n".join(f"{n}: {s}" for n, s in zip(names, table.scores)) + f"\n\nHands played: {len(table.history)}"


HOW_TO = ("Try to take as few points as you can. Every heart you win in a trick is one point, and the queen of "
          "spades is 13. When someone reaches 100 points, the player with the lowest score wins.\n\n"
          "Before each hand, pass three cards (left, then right, then across, then no pass). The two of clubs "
          "leads the first trick. Follow suit if you can. You can't lead hearts until a heart has been played.\n\n"
          "Take every heart and the queen of spades to \"shoot the moon\": everyone else gets 26 instead.")
