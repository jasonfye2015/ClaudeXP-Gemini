"""Internet Backgammon on the Zone. You play white, moving from point 24 down to your home board (points 1-6) and
bearing off; your opponent plays red the other way. Click the dice to roll, then click a checker and where it
should go. Hit a lone checker to send it to the bar; it must come back in before anything else moves. Doubles
move four times. You must use both dice if you can (otherwise the larger one)."""
import random
from functools import lru_cache

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient

from .zone import ZoneBoard, open_zone_game

# A position: (points, bar_white, bar_red, off_white, off_red); points[1..24] > 0 white, < 0 red (index 0 unused).
START = [0] * 25
for p, n in ((24, 2), (13, 5), (8, 3), (6, 5)):
    START[p] = n
    START[25 - p] = -n
START = (tuple(START), 0, 0, 0, 0)


def mirror(state):
    pts, bw, br, ow, orr = state
    return tuple([0] + [-pts[25 - i] for i in range(1, 25)]), br, bw, orr, ow


def single_moves(state, d):
    """White's single-die moves: [(src, dst)] where src 'bar' or 1..24, dst 1..24 or 'off'."""
    pts, bw, _br, _ow, _or = state
    if bw:
        t = 25 - d
        return [("bar", t)] if pts[t] >= -1 else []
    out = []
    home = all(pts[p] <= 0 for p in range(7, 25))
    highest = max((p for p in range(1, 7) if pts[p] > 0), default=0)
    for p in range(1, 25):
        if pts[p] <= 0:
            continue
        t = p - d
        if t >= 1:
            if pts[t] >= -1:
                out.append((p, t))
        elif home and (t == 0 or p == highest):
            out.append((p, "off"))
    return out


def apply_single(state, move):
    pts, bw, br, ow, orr = state
    pts = list(pts)
    src, dst = move
    if src == "bar":
        bw -= 1
    else:
        pts[src] -= 1
    if dst == "off":
        ow += 1
    else:
        if pts[dst] == -1:
            pts[dst] = 0
            br += 1
        pts[dst] += 1
    return tuple(pts), bw, br, ow, orr


def sequences(state, dice):
    return _sequences(state, tuple(sorted(dice)))


@lru_cache(maxsize=256)
def _sequences(state, dice):
    """Every legal full turn for white: [(moves, final state, dice used)], using as many dice as possible."""
    results = []

    def walk(st, remaining, done):
        extended = False
        for i, d in enumerate(remaining):
            if d in remaining[:i]:
                continue
            for m in single_moves(st, d):
                extended = True
                walk(apply_single(st, m), remaining[:i] + remaining[i + 1:], done + [(m, d)])
        if not extended:
            results.append((done, st))

    walk(state, list(dice), [])
    most = max(len(r[0]) for r in results)
    results = [r for r in results if len(r[0]) == most]
    if most == 1 and len(set(dice)) == 2:
        big = [r for r in results if r[0][0][1] == max(dice)]
        results = big or results
    seen, out = set(), []
    for moves, st in results:
        if st not in seen:
            seen.add(st)
            out.append(([m for m, _d in moves], st, [d for _m, d in moves]))
    return out


def pips(state):
    pts, bw, br, _ow, _or = state
    white = sum(p * n for p, n in enumerate(pts) if n > 0) + bw * 25
    red = sum((25 - p) * -n for p, n in enumerate(pts) if n < 0) + br * 25
    return white, red


def evaluate(state):
    """How good a position is for white."""
    pts, bw, br, ow, orr = state
    w, r = pips(state)
    score = (r - w) * 1.0 + br * 14 - bw * 14 + ow * 4
    reds = [p for p in range(1, 25) if pts[p] < 0] + ([0] if br else [])     # a checker on the bar enters low
    for p in range(1, 25):
        n = pts[p]
        if n >= 2:
            score += 3 + (4 if p <= 6 else 0) + (2 if 18 <= p <= 21 else 0)
        elif n == 1:
            # a blot: how many red checkers are close enough behind it to hit (red moves upward)
            shooters = sum(1 for q in reds if 0 < p - q <= 12)
            near = sum(1 for q in reds if 0 < p - q <= 6)
            score -= 2 + near * 3 + shooters
    return score


HOW_TO_TEXT = " ".join(__doc__.split())


class BackgammonBoard(ZoneBoard):
    HOW_TO = HOW_TO_TEXT

    def __init__(self):
        super().__init__()
        self.state = START
        self.side = "white"
        self.dice, self.remaining = [], []
        self.rolled = False
        self.selected = None
        self.ai_queue = []
        self.anim = QTimer(self)
        self.anim.timeout.connect(self._ai_step)
        self.setMinimumSize(520, 400)

    # ---- the ZoneBoard interface ---------------------------------------------------------------------------------
    def start(self, user_first):
        self.state = START
        self.side = "white" if user_first else "red"
        self.dice, self.remaining, self.rolled, self.selected = [], [], False, None
        self.update()

    def colors(self):
        return ("White", "Red")

    def turn(self):
        return "user" if self.side == "white" else "ai"

    def result(self):
        if self.state[3] == 15:
            return "user"
        if self.state[4] == 15:
            return "ai"
        return None

    def score_text(self):
        w, r = pips(self.state)
        return f"Pip count — White: {w}   Red: {r}\nBorne off — White: {self.state[3]}   Red: {self.state[4]}"

    def result_text(self):
        res = self.result()
        loser_off = self.state[4] if res == "user" else self.state[3]
        kind = " — a gammon!" if loser_off == 0 else ""
        return ("You won" if res == "user" else "Your opponent won") + kind

    def outcome_for(self, opponent):
        from .hearts import _you
        res = self.result()
        loser_off = self.state[4] if res == "user" else self.state[3]
        gammon = " — a gammon" if loser_off == 0 else ""
        return (f"{_you()} beat me{gammon}" if res == "user" else f"I beat {_you()}{gammon}") + \
            f" (they'd borne off {self.state[3]}, I'd borne off {self.state[4]})"

    def stop(self):
        self.anim.stop()

    # ---- the computer ----------------------------------------------------------------------------------------------
    def ai_play(self, level):
        self.dice = [random.randint(1, 6), random.randint(1, 6)]
        rolls = self.dice * 2 if self.dice[0] == self.dice[1] else list(self.dice)
        seqs = sequences(mirror(self.state), rolls)
        if level == 0:
            choice = random.choice(seqs)
        else:
            noise = 6 if level == 1 else 0
            choice = max(seqs, key=lambda s: evaluate(s[1]) + random.uniform(-noise, noise))
        self.ai_queue = list(choice[0])          # moves in red's own (mirrored) view, replayed one at a time
        self.remaining = list(rolls)
        self.ai_hits = 0
        self.update()
        self.anim.start(450)

    def _ai_step(self):
        if not self.ai_queue:
            self.anim.stop()
            self._end_turn("ai", {"captured": 2 if self.ai_hits else 0})
            return
        move = self.ai_queue.pop(0)
        before = self.state[1]
        self.state = mirror(apply_single(mirror(self.state), move))
        self.ai_hits += self.state[1] - before
        if self.remaining:
            self.remaining.pop(0)
        self.update()

    def _end_turn(self, who, info):
        self.side = "red" if self.side == "white" else "white"
        self.rolled, self.selected, self.remaining = False, None, []
        self.update()
        self.moved.emit(who, info)

    # ---- you --------------------------------------------------------------------------------------------------------
    def roll(self):
        if self.locked or self.side != "white" or self.rolled:
            return
        self.dice = [random.randint(1, 6), random.randint(1, 6)]
        self.remaining = self.dice * 2 if self.dice[0] == self.dice[1] else list(self.dice)
        self.rolled = True
        self.user_hits = 0
        if not sequences(self.state, self.remaining)[0][0]:
            self.banner = "No legal moves."
            self.update()
            QTimer.singleShot(1600, self._no_moves)
        self.update()

    def _no_moves(self):
        self.banner = ""
        self._end_turn("user", {})

    def _options(self):
        """Single steps that start some legal full turn from here: {(src, dst): die}."""
        out = {}
        for moves, _st, dice in sequences(self.state, self.remaining):
            if moves:
                out.setdefault(moves[0], dice[0])
        return out

    def _step(self, move, die):
        before = self.state[2]
        self.state = apply_single(self.state, move)
        self.user_hits += self.state[2] - before
        self.remaining.remove(die)
        self.selected = None
        if not self.remaining or not self._options():
            self._end_turn("user", {"captured": 2 if self.user_hits else 0,
                                    "big": move[1] == "off" and self.state[3] == 15})
        self.update()

    def mousePressEvent(self, event):
        if self.locked or self.side != "white":
            return
        pos = event.position()
        if not self.rolled:
            if self.dice_rect().contains(pos):
                self.roll()
            return
        target = self.hit(pos)
        if target is None:
            self.selected = None
            self.update()
            return
        opts = self._options()
        if self.selected is not None:
            for (src, dst), die in opts.items():
                if src == self.selected and dst == target:
                    return self._step((src, dst), die)
        if any(src == target for (src, _dst) in opts):
            self.selected = target
        else:
            self.selected = None
        self.update()

    # ---- geometry ------------------------------------------------------------------------------------------------------
    def geo(self):
        w, h = self.width(), self.height()
        tray = 46
        board = QRectF(8, 8, w - 16 - tray, h - 16)
        bar = 34
        pw = (board.width() - bar) / 12
        return board, bar, pw, QRectF(board.right() + 6, board.top(), tray - 6, board.height())

    def point_x(self, p):
        board, bar, pw, _tray = self.geo()
        col = (12 - p) if p <= 12 else (p - 13)
        return board.left() + col * pw + (bar if col >= 6 else 0)

    def hit(self, pos):
        board, bar, pw, tray = self.geo()
        if tray.contains(pos):
            return "off"
        bar_x = board.left() + 6 * pw
        if bar_x <= pos.x() <= bar_x + bar:
            return "bar"
        if not board.contains(pos):
            return None
        x = pos.x() - board.left()
        col = int(x // pw) if x < 6 * pw else int((x - bar) // pw)
        col = max(0, min(11, col))
        top = pos.y() < board.center().y()
        return 13 + col if top else 12 - col

    def dice_rect(self):
        board, bar, pw, _tray = self.geo()
        cx = board.left() + 6 * pw + bar + 3 * pw
        return QRectF(cx - 50, board.center().y() - 20, 100, 40)

    # ---- drawing ---------------------------------------------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#3B6EA5"))
        board, bar, pw, tray = self.geo()
        p.fillRect(board, QColor("#C9A46A"))
        p.fillRect(QRectF(board.left() + 6 * pw, board.top(), bar, board.height()), QColor("#6B4423"))
        p.fillRect(tray, QColor("#6B4423"))
        opts = self._options() if (self.rolled and self.side == "white" and not self.locked) else {}
        sources = {s for s, _d in opts}
        dests = {d for s, d in opts if s == self.selected}
        tri_h = board.height() * 0.4
        for pt in range(1, 25):
            x = self.point_x(pt)
            top = pt >= 13
            path = QPainterPath()
            if top:
                path.moveTo(x, board.top())
                path.lineTo(x + pw, board.top())
                path.lineTo(x + pw / 2, board.top() + tri_h)
            else:
                path.moveTo(x, board.bottom())
                path.lineTo(x + pw, board.bottom())
                path.lineTo(x + pw / 2, board.bottom() - tri_h)
            path.closeSubpath()
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#7A1E1E") if pt % 2 else QColor("#F4E9D0"))
            p.drawPath(path)
            if pt in dests:
                p.setBrush(QColor(255, 230, 80, 150))
                p.drawPath(path)
            n = self.state[0][pt]
            if n:
                self._stack(p, x + pw / 2, top, abs(n), "white" if n > 0 else "red", pw,
                            board, highlight=(pt in sources and self.selected is None) or pt == self.selected)
        # bar
        cx = board.left() + 6 * pw + bar / 2
        if self.state[1]:
            self._stack(p, cx, False, self.state[1], "white", min(pw, bar), board, from_mid=True,
                        highlight=("bar" in sources))
        if self.state[2]:
            self._stack(p, cx, True, self.state[2], "red", min(pw, bar), board, from_mid=True)
        # borne off
        for i in range(self.state[3]):
            p.fillRect(QRectF(tray.left() + 4, tray.bottom() - 6 - i * 7, tray.width() - 8, 5), QColor("#F4F4F0"))
        for i in range(self.state[4]):
            p.fillRect(QRectF(tray.left() + 4, tray.top() + 2 + i * 7, tray.width() - 8, 5), QColor("#C02020"))
        if "off" in dests:
            p.setPen(QPen(QColor("#FFE050"), 3))
            p.setBrush(Qt.NoBrush)
            p.drawRect(tray.adjusted(1, 1, -1, -1))
        self._draw_dice(p)
        self.paint_banner(p)

    def _stack(self, p, cx, top, n, color, pw, board, highlight=False, from_mid=False):
        d = min(pw * 0.9, board.height() * 0.08)
        shown = min(n, 5)
        for i in range(shown):
            if from_mid:
                cy = board.center().y() + (-(i + 1) * d if top else (i + 1) * d) + (d / 2 if top else -d / 2)
            else:
                cy = board.top() + d / 2 + i * d if top else board.bottom() - d / 2 - i * d
            r = QRectF(cx - d / 2, cy - d / 2, d, d)
            base = QColor("#F7F3E8") if color == "white" else QColor("#C42222")
            g = QRadialGradient(r.center() - QPointF(d * 0.2, d * 0.2), d * 0.7)
            g.setColorAt(0, base.lighter(115))
            g.setColorAt(1, base.darker(115))
            p.setPen(QPen(QColor("#FFE050") if highlight and i == shown - 1 else base.darker(170),
                          3 if highlight and i == shown - 1 else 1))
            p.setBrush(g)
            p.drawEllipse(r)
            if i == shown - 1 and n > 5:
                f = QFont("Tahoma")
                f.setPixelSize(int(d * 0.45))
                f.setBold(True)
                p.setFont(f)
                p.setPen(QColor("black") if color == "white" else QColor("white"))
                p.drawText(r, Qt.AlignCenter, str(n))

    def _draw_dice(self, p):
        r = self.dice_rect()
        if self.side == "white" and not self.rolled and not self.locked:
            p.setPen(QPen(QColor("#402000"), 1))
            p.setBrush(QColor("#FFF8E0"))
            p.drawRoundedRect(r, 8, 8)
            f = QFont("Tahoma")
            f.setPixelSize(13)
            f.setBold(True)
            p.setFont(f)
            p.setPen(QColor("#402000"))
            p.drawText(r, Qt.AlignCenter, "Click to roll")
            return
        if not self.dice:
            return
        used = len(self.dice * (2 if self.dice[0] == self.dice[1] else 1)) - len(self.remaining)
        for i, v in enumerate(self.dice):
            die = QRectF(r.center().x() - 42 + i * 46, r.top(), 38, 38)
            faded = (self.dice[0] != self.dice[1] and v not in self.remaining) or \
                    (self.dice[0] == self.dice[1] and used >= (4 if i == 1 else 2))
            p.setPen(QPen(QColor("#202020"), 1))
            p.setBrush(QColor("#E8E8E8") if faded else QColor("white"))
            p.drawRoundedRect(die, 6, 6)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#A0A0A0") if faded else (QColor("#C42222") if self.side == "red" else QColor("black")))
            spots = {1: [(1, 1)], 2: [(0, 0), (2, 2)], 3: [(0, 0), (1, 1), (2, 2)], 4: [(0, 0), (0, 2), (2, 0), (2, 2)],
                     5: [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)], 6: [(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)]}[v]
            for sx, sy in spots:
                p.drawEllipse(QPointF(die.left() + 9 + sx * 10, die.top() + 9 + sy * 10), 3.4, 3.4)


def backgammon_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(QRectF(2, 4, 28, 24), QColor("#C9A46A"))
    for i in range(4):
        path = QPainterPath()
        x = 3 + i * 7
        path.moveTo(x, 4)
        path.lineTo(x + 6, 4)
        path.lineTo(x + 3, 15)
        path.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#7A1E1E") if i % 2 else QColor("#F4E9D0"))
        p.drawPath(path)
    p.setBrush(QColor("#F7F3E8"))
    p.setPen(QPen(QColor("#606060"), 1))
    p.drawEllipse(QRectF(5, 19, 8, 8))
    p.setBrush(QColor("#C42222"))
    p.drawEllipse(QRectF(17, 19, 8, 8))
    p.end()
    return QIcon(pm)


def open_internet_backgammon(desktop):
    return open_zone_game(desktop, "Backgammon", lambda _w: BackgammonBoard(), ("White", "Red"), backgammon_icon())
