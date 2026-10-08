"""Internet Spades on the Zone: you and your partner (across the table, one of your buddies) against two others.
Everyone bids how many tricks they'll take (or Nil: none at all); spades are trumps and can't be led until they've
been broken. Make your bid: 10 points a trick, extra tricks are 'bags' (10 bags cost 100). Fail: lose 10 a trick.
Nil is worth 100 either way. First team to 500 wins (a team at -200 loses)."""
import random

from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QWidget

from .cards import CARD_H, CARD_W, FELT, back_pixmap, card_pixmap, deck, shuffled
from .common import card_icon
from .hearts import _you
from .zone import open_zone_game

SUIT_ORDER = "DCHS"
SPACING = 20
TARGET, FLOOR = 500, -200


def value(card):
    return 14 if card.rank == 1 else card.rank


def sort_hand(cards):
    cards.sort(key=lambda c: (SUIT_ORDER.index(c.suit), value(c)))
    return cards


def team(seat):
    return seat % 2          # 0: you (0) and your partner (2); 1: west (1) and east (3)


HOW_TO_TEXT = " ".join(__doc__.split()[5:])        # without 'Internet Spades on the Zone:'


class SpadesTable(QWidget):
    moved = Signal(str, dict)
    finished = Signal(str)
    SEATS = 3
    SELF_DRIVEN = True
    HOW_TO = HOW_TO_TEXT

    def __init__(self, win):
        super().__init__()
        self.win = win
        self.names = ["You", "West", "North", "East"]
        self.skills = [1, 1, 1]
        self.locked = True
        self.banner = ""
        self.hands = [[], [], [], []]
        self.trick, self.bids, self.tricks = [], [None] * 4, [0] * 4
        self.scores, self.bags, self.history = [0, 0], [0, 0], []
        self.phase, self.turn, self.dealer = "idle", 0, random.randrange(4)
        self.spades_broken = False
        self.setMinimumSize(660, 520)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._step)
        self.bid_panel = QWidget(self)
        grid = QGridLayout(self.bid_panel)
        grid.setSpacing(3)
        title = QLabel("How many tricks will you take?")
        title.setStyleSheet("color: white; font-family: Tahoma; font-size: 12px; font-weight: bold;")
        grid.addWidget(title, 0, 0, 1, 7, Qt.AlignCenter)
        for i, label in enumerate(["Nil"] + [str(n) for n in range(1, 14)]):
            b = QPushButton(label)
            b.setFixedSize(38, 24)
            b.clicked.connect(lambda _c=False, n=i: self._user_bid(n))
            grid.addWidget(b, 1 + i // 7, i % 7)
        self.bid_panel.adjustSize()
        self.bid_panel.hide()

    # ---- the Zone's side ----------------------------------------------------------------------------------------
    def set_players(self, names, skills):
        self.names = ["You", *names]
        self.skills = list(skills)

    def colors(self):
        return (None, ["Opponent", "Your partner", "Opponent"])

    def start(self, user_first):
        self.scores, self.bags, self.history = [0, 0], [0, 0], []
        self.dealer = 3 if user_first else random.randrange(4)
        self.locked = False
        self.deal()

    def result(self):
        return None

    def stop(self):
        self.timer.stop()

    def score_text(self):
        partner = self.names[2]
        return (f"You & {partner}: {self.scores[0]} (bags {self.bags[0]})\n"
                f"{self.names[1]} & {self.names[3]}: {self.scores[1]} (bags {self.bags[1]})")

    def result_text(self):
        if self.scores[0] > self.scores[1]:
            return f"You and {self.names[2]} won, {self.scores[0]} to {self.scores[1]}!"
        return f"{self.names[1]} and {self.names[3]} won, {self.scores[1]} to {self.scores[0]}."

    def outcome_for(self, opponent):
        seat = self.names.index(opponent.name)
        mine = team(seat)
        won = self.scores[mine] > self.scores[1 - mine]
        if seat == 2:
            return f"we were partners and {'we won' if won else 'we lost'}, {self.scores[0]} to {self.scores[1]}"
        return f"my partner {self.names[4 - seat]} and I {'won' if won else 'lost'}, " \
               f"{self.scores[1]} to {self.scores[0]}"

    # ---- dealing and bidding ---------------------------------------------------------------------------------------
    def deal(self):
        cards = shuffled(deck())
        for c in cards:
            c.face_up = True
        self.hands = [sort_hand(cards[i::4]) for i in range(4)]
        self.trick, self.bids, self.tricks = [], [None] * 4, [0] * 4
        self.spades_broken = False
        self.dealer = (self.dealer + 1) % 4
        self.phase = "bid"
        self.turn = (self.dealer + 1) % 4
        self._next()

    def _next(self):
        self.update()
        if self.phase == "bid":
            if all(b is not None for b in self.bids):
                self.phase = "play"
                self.turn = (self.dealer + 1) % 4
                return self._next()
            if self.turn == 0:
                self._say("Your bid: how many tricks will you take?")
                self._place_bid_panel()
                self.bid_panel.show()
                self.bid_panel.raise_()
            else:
                self._say(f"Waiting for {self.names[self.turn]} to bid.")
                self.timer.start(random.randint(700, 1600))
        elif self.phase == "play":
            if len(self.trick) == 4:
                self.phase = "collect"
                self.timer.start(1100)
            elif self.turn == 0:
                self._say("Your turn. Click a card to play it.")
            else:
                self._say(f"Waiting for {self.names[self.turn]} to play.")
                self.timer.start(random.randint(600, 1200))

    def _user_bid(self, n):
        if self.phase != "bid" or self.turn != 0:
            return
        self.bid_panel.hide()
        self.bids[0] = n
        self.turn = 1
        self._next()

    def ai_bid(self, seat):
        hand = self.hands[seat]
        by_suit = {s: [c for c in hand if c.suit == s] for s in "SHDC"}
        est = 0.0
        for s, cards in by_suit.items():
            vals = sorted((value(c) for c in cards), reverse=True)
            if s == "S":
                est += sum(1 for v in vals if v >= 12)
                est += max(0, len(vals) - 3) * 0.8
            else:
                if 14 in vals:
                    est += 1
                if 13 in vals and len(vals) >= 2:
                    est += 0.8
                if 12 in vals and len(vals) >= 3:
                    est += 0.4
                if len(by_suit["S"]) >= 3:
                    est += {0: 1.0, 1: 0.6}.get(len(vals), 0)
        partner_bid = self.bids[(seat + 2) % 4]
        if est < 0.8 and not any(value(c) > 10 for c in by_suit["S"]) and partner_bid not in (0,) \
                and not any(value(c) == 14 for c in hand):
            return 0                                           # Nil
        bid = max(1, round(est))
        if self.skills[seat - 1] == 0:
            bid = max(1, bid + random.choice((-1, 0, 1)))
        return min(13, bid)

    # ---- playing ----------------------------------------------------------------------------------------------
    def legal(self, seat):
        hand = self.hands[seat]
        if not self.trick:
            if self.spades_broken or all(c.suit == "S" for c in hand):
                return list(hand)
            return [c for c in hand if c.suit != "S"]
        lead = self.trick[0][1].suit
        follow = [c for c in hand if c.suit == lead]
        return follow or list(hand)

    def winning(self):
        """(seat, card) currently winning the trick."""
        lead = self.trick[0][1].suit
        spades = [pc for pc in self.trick if pc[1].suit == "S"]
        pool = spades or [pc for pc in self.trick if pc[1].suit == lead]
        return max(pool, key=lambda pc: value(pc[1]))

    def beats(self, card, current):
        if card.suit == current.suit:
            return value(card) > value(current)
        return card.suit == "S"

    def team_needs(self, seat):
        t = team(seat)
        bid = sum(self.bids[s] for s in (t, t + 2) if self.bids[s])
        took = sum(self.tricks[s] for s in (t, t + 2) if self.bids[s])
        return took < bid

    def ai_card(self, seat):
        options = self.legal(seat)
        if self.skills[seat - 1] == 0 and random.random() < 0.3:
            return random.choice(options)
        low = lambda cs: min(cs, key=lambda c: (c.suit == "S", value(c)))
        high = lambda cs: max(cs, key=lambda c: (c.suit == "S", value(c)))
        nil = self.bids[seat] == 0
        if not self.trick:
            if nil:
                return low(options)
            if self.team_needs(seat):
                aces = [c for c in options if value(c) == 14 and c.suit != "S"]
                if aces:
                    return aces[0]
            return low(options)
        win_seat, win_card = self.winning()
        partner_winning = team(win_seat) == team(seat) and self.bids[win_seat] != 0
        winners = [c for c in options if self.beats(c, win_card)]
        losers = [c for c in options if c not in winners]
        if nil:
            return high(losers) if losers else low(options)
        partner_nil = self.bids[(seat + 2) % 4] == 0
        if partner_nil and win_seat == (seat + 2) % 4 and winners:
            return low(winners)                         # rescue a partner who bid nil
        if partner_winning:
            return low(losers) if losers else low(options)
        if winners and (self.team_needs(seat) or len(self.trick) == 3):
            return low(winners)
        return low(losers) if losers else low(options)

    def _step(self):
        if self.phase == "bid" and self.turn != 0:
            self.bids[self.turn] = self.ai_bid(self.turn)
            self.turn = (self.turn + 1) % 4
            self._next()
        elif self.phase == "play" and self.turn != 0:
            self._play(self.turn, self.ai_card(self.turn))
        elif self.phase == "collect":
            self._collect()

    def _play(self, seat, card):
        self.hands[seat].remove(card)
        if card.suit == "S":
            self.spades_broken = True
        self.trick.append((seat, card))
        self.turn = (seat + 1) % 4
        self._next()

    def _collect(self):
        win_seat, win_card = self.winning()
        trumped = win_card.suit == "S" and self.trick[0][1].suit != "S"
        self.tricks[win_seat] += 1
        who = "user" if win_seat == 0 else str(win_seat)
        self.moved.emit(who, {"big": trumped, "oops": self.bids[win_seat] == 0, "captured": 0})
        self.trick = []
        if not self.hands[0]:
            return self._end_hand()
        self.phase = "play"
        self.turn = win_seat
        self._next()

    def _end_hand(self):
        lines = []
        for t in (0, 1):
            seats = (t, t + 2)
            contract = sum(self.bids[s] for s in seats if self.bids[s])
            made = sum(self.tricks[s] for s in seats if self.bids[s])
            pts, bags = 0, 0
            if made >= contract:
                pts += 10 * contract + (made - contract)
                bags += made - contract
            else:
                pts -= 10 * contract
            for s in seats:
                if self.bids[s] == 0:
                    if self.tricks[s] == 0:
                        pts += 100
                    else:
                        pts -= 100
                        bags += self.tricks[s]
            self.bags[t] += bags
            while self.bags[t] >= 10:
                self.bags[t] -= 10
                pts -= 100
            self.scores[t] += pts
            lines.append(pts)
        self.history.append(lines)
        self.phase = "scores"
        self.update()
        over = max(self.scores) >= TARGET or min(self.scores) <= FLOOR
        if over and self.scores[0] == self.scores[1]:
            over = False                               # play on until someone's ahead
        self._score_sheet(over)

    def _score_sheet(self, over):
        from ..explorer.dialogs import msgbox
        partner = self.names[2]
        rows = [f"{self.names[s]}: bid {'Nil' if self.bids[s] == 0 else self.bids[s]}, took {self.tricks[s]}"
                for s in range(4)]
        rows[0] = rows[0].replace("You:", f"{_you()}:")
        text = "\n".join(rows) + (f"\n\nThis hand:  You & {partner} {self.history[-1][0]:+d},  "
                                  f"{self.names[1]} & {self.names[3]} {self.history[-1][1]:+d}\n\n") + self.score_text()

        def done(_button):
            if over:
                self.locked = True
                self.finished.emit("user" if self.scores[0] > self.scores[1] else "ai")
            else:
                self.deal()
        msgbox(self.win.desktop, "Game Over" if over else "Score", text, "info", ("OK",), done)

    # ---- you ----------------------------------------------------------------------------------------------------
    def _say(self, text):
        self.win.status.setText(text)

    def _card_rects(self):
        hand = self.hands[0]
        x0 = (self.width() - (CARD_W + SPACING * (len(hand) - 1))) // 2
        y = self.height() - CARD_H - 12
        return [QRect(x0 + i * SPACING, y, CARD_W, CARD_H) for i in range(len(hand))]

    def mousePressEvent(self, event):
        if self.locked or self.phase != "play" or self.turn != 0 or event.button() != Qt.LeftButton:
            return
        pos = event.position().toPoint()
        rects = self._card_rects()
        for i in range(len(rects) - 1, -1, -1):
            if rects[i].contains(pos):
                card = self.hands[0][i]
                if card in self.legal(0):
                    self._play(0, card)
                elif not self.trick:
                    self._say("Spades have not been broken yet.")
                else:
                    self._say("You must follow suit.")
                return

    def _place_bid_panel(self):
        self.bid_panel.move((self.width() - self.bid_panel.width()) // 2, self.height() // 2 - 40)

    def resizeEvent(self, event):
        self._place_bid_panel()

    def _trick_pos(self, seat):
        cx, cy = self.width() // 2, self.height() // 2 - 20
        return {0: QPoint(cx - CARD_W // 2, cy + 6), 1: QPoint(cx - CARD_W - 30, cy - CARD_H // 2),
                2: QPoint(cx - CARD_W // 2, cy - CARD_H - 6), 3: QPoint(cx + 30, cy - CARD_H // 2)}[seat]

    def _bid_text(self, seat):
        b = self.bids[seat]
        if b is None:
            return ""
        return f"Bid {'Nil' if b == 0 else b}  ·  Took {self.tricks[seat]}"

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), FELT)
        w, h = self.width(), self.height()
        n = len(self.hands[2])
        x0 = (w - (CARD_W + 12 * max(0, n - 1))) // 2
        for i in range(n):
            p.drawPixmap(x0 + i * 12, 14, back_pixmap())
        for seat, x in ((1, 14), (3, w - 14 - CARD_W)):
            n = len(self.hands[seat])
            y0 = (h - (CARD_H + 12 * max(0, n - 1))) // 2 - 20
            for i in range(n):
                p.drawPixmap(x, y0 + i * 12, back_pixmap())
        f = QFont("Tahoma")
        f.setPixelSize(11)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("#FFFF99"))
        p.drawText(QRect(0, 14 + CARD_H + 2, w, 16), Qt.AlignHCenter, f"{self.names[2]} (partner)")
        p.setPen(QColor("white"))
        p.drawText(QRect(14, h // 2 + 130, 160, 16), Qt.AlignLeft, self.names[1])
        p.drawText(QRect(w - 174, h // 2 + 130, 160, 16), Qt.AlignRight, self.names[3])
        p.drawText(QRect(0, h - CARD_H - 12 - 40, w, 16), Qt.AlignHCenter, _you())
        small = QFont("Tahoma")
        small.setPixelSize(11)
        p.setFont(small)
        p.setPen(QColor("#E0FFE0"))
        p.drawText(QRect(0, 14 + CARD_H + 18, w, 16), Qt.AlignHCenter, self._bid_text(2))
        p.drawText(QRect(14, h // 2 + 146, 200, 16), Qt.AlignLeft, self._bid_text(1))
        p.drawText(QRect(w - 214, h // 2 + 146, 200, 16), Qt.AlignRight, self._bid_text(3))
        p.drawText(QRect(0, h - CARD_H - 12 - 24, w, 16), Qt.AlignHCenter, self._bid_text(0))
        for seat, card in self.trick:
            p.drawPixmap(self._trick_pos(seat), card_pixmap(card))
        my_turn = self.phase == "play" and self.turn == 0 and not self.locked
        legal = self.legal(0) if my_turn else []
        hand = self.hands[0]
        for i, (rect, card) in enumerate(zip(self._card_rects(), hand)):
            p.drawPixmap(rect.topLeft(), card_pixmap(card))
            if my_turn and card not in legal:
                width = SPACING if i < len(hand) - 1 else CARD_W
                p.fillRect(QRect(rect.x() + 1, rect.y() + 1, width - 1, CARD_H - 2), QColor(0, 0, 0, 45))
        if self.banner:
            p.fillRect(self.rect(), QColor(0, 0, 0, 110))
            bf = QFont("Tahoma")
            bf.setPixelSize(16)
            bf.setBold(True)
            p.setFont(bf)
            p.setPen(QColor("white"))
            p.drawText(self.rect(), Qt.AlignCenter | Qt.TextWordWrap, self.banner)


def open_internet_spades(desktop):
    return open_zone_game(desktop, "Spades", SpadesTable, (None, None), card_icon("S"), (900, 620))
