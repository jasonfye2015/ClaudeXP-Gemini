"""Claudeanoid: a block breaker in the Breakout / Arkanoid line. Steer the paddle with the mouse (or the arrow keys),
keep the ball up, and clear every breakable block to finish the round - 40 rounds in all.

Coloured blocks break in one hit, silver ones take more (more each eight rounds), gold ones never break. Broken blocks
sometimes drop a capsule: E expands the paddle, L arms lasers, C catches the ball, S slows it, D splits it into three,
P gives an extra paddle and B opens the warp to the next round. Click or Space launches (and fires lasers), P or Esc
pauses. The top ten scores are kept with the shared saves (ClaudeGames/Saves/claudeanoid), so every era sees them.
Sound effects are little chiptune blips made on first run (this computer's data folder), and stay quiet when the
computer is muted."""
import json
import math
import random
import struct
import time
import wave

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import QWidget
from shiboken6 import isValid

from claudecore import host

FIELD_W, FIELD_H = 624, 580                       # the playfield; a panel sits to its right
PANEL_W = 196
COLS, BW, BH = 13, 48, 20
TOP = 60                                          # first block row
PADDLE_Y = FIELD_H - 40
BALL_R = 6
ROUNDS = 40
SCORES = host.saves("claudeanoid") / "scores.json"
COLOURS = {"w": ("#F4F4F4", 50), "o": ("#FF9A2E", 60), "c": ("#38D8F0", 70), "g": ("#4ED84E", 80),
           "r": ("#F0383C", 90), "b": ("#3C6CF0", 100), "p": ("#E040E0", 110), "y": ("#F4E030", 120)}
CAPSULES = {"E": "#3C6CF0", "L": "#F0383C", "C": "#4ED84E", "S": "#FF9A2E", "D": "#38D8F0", "P": "#A0A0A8",
            "B": "#E040E0"}
CAPSULE_ODDS = "EEELLLCCSSSDDDPB"


def claudeanoid_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(QRectF(1, 1, 30, 30), QColor("#101830"))
    for i, c in enumerate(("#F0383C", "#F4E030", "#4ED84E", "#3C6CF0")):
        for j in range(3):
            p.fillRect(QRectF(3 + j * 9, 3 + i * 4, 8, 3), QColor(c))
    p.setBrush(QColor("white"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QRectF(17, 19, 4, 4))
    g = QLinearGradient(0, 26, 0, 30)
    g.setColorAt(0, QColor("#D8D8E0"))
    g.setColorAt(1, QColor("#707080"))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(8, 26, 16, 4), 2, 2)
    p.end()
    return QIcon(pm)


# ---- the 40 rounds ----------------------------------------------------------------------------------------------
def _mirror(rows):
    """Rows written for the left half (7 columns) mirrored into the full 13."""
    return [r[:7] + r[:6][::-1] for r in rows]


def layout(n):
    """Round n (1-40): a list of row strings, 13 characters each ('.' empty, colour letters, 's' silver, 'G' gold)."""
    rnd = random.Random(n * 7919)
    pals = ["wocgrbpy", "rygbcpow", "pbcgyorw", "yorpbgcw", "gcbpryow"]
    pal = pals[n % len(pals)]
    kind = (n - 1) % 10
    silver = min(0.06 + n * 0.006, 0.3) if n > 4 else 0.0
    gold = 0.0 if n < 9 else min(0.02 + (n - 9) * 0.003, 0.1)
    rows = []
    if kind == 0:                                                  # stripes
        rows = [pal[i % 8] * COLS for i in range(6 + n // 10)]
    elif kind == 1:                                                # pyramid
        rows = ["." * (6 - i) + pal[i % 8] * (1 + 2 * i) + "." * (6 - i) for i in range(7)]
    elif kind == 2:                                                # checkerboard
        rows = ["".join(pal[(r + c) % 8] if (r + c) % 2 == 0 else "." for c in range(COLS)) for r in range(9)]
    elif kind == 3:                                                # invader
        art = ["..x.....", "...x....", "..xxxx..", ".xx.xxx.", "xxxxxxxx", "x.xxxxxx", "x.x.....", "...xx..."]
        rows = _mirror(["".join(pal[(r + 2) % 8] if ch == "x" else "." for ch in line[:7]) for r, line in enumerate(art)])
    elif kind == 4:                                                # diamond
        rows = ["." * abs(4 - i) * 1 + pal[i % 8] * (COLS - 2 * abs(4 - i)) + "." * abs(4 - i) for i in range(9)]
        rows = [r[:COLS].ljust(COLS, ".") for r in rows]
    elif kind == 5:                                                # heart
        art = [".xx..xx", "xxxxxxx", "xxxxxxx", ".xxxxxx", "..xxxxx", "...xxxx", "....xxx", ".....xx", "......x"]
        rows = _mirror(["".join(pal[1] if ch == "x" else "." for ch in line) for line in art])
    elif kind == 6:                                                # fortress: gold walls with a way in
        rows = ["G" * 5 + "..." + "G" * 5] + [pal[i % 8] * COLS for i in range(5)] + ["G...." + "sss" + "....G"]
        rows += [pal[(i + 3) % 8] * COLS for i in range(3)]
    elif kind == 7:                                                # columns
        rows = ["".join(pal[c % 8] if c % 2 == 0 else "." for c in range(COLS)) for _ in range(10)]
    elif kind == 8:                                                # rings
        rows = []
        for r in range(11):
            line = ""
            for c in range(COLS):
                d = max(abs(c - 6), abs(r - 5) * 1.2)
                line += pal[int(d) % 8] if int(d) % 2 == 0 else "."
            rows.append(line)
    else:                                                          # a random symmetric pattern
        rows = _mirror(["".join(pal[rnd.randrange(8)] if rnd.random() < 0.7 else "." for _ in range(7))
                        for _ in range(8 + n // 8)])
    out = []
    for line in rows:
        chars = []
        for ch in line[:COLS].ljust(COLS, "."):
            if ch in COLOURS:
                roll = rnd.random()
                ch = "G" if roll < gold else "s" if roll < gold + silver else ch
            chars.append(ch)
        out.append("".join(chars))
    if not any(ch not in ".G" for line in out for ch in line):     # (never a round with nothing to break)
        out.append(pal[0] * COLS)
    return out


class Brick:
    __slots__ = ("rect", "kind", "hits", "flash")

    def __init__(self, rect, kind, hits):
        self.rect, self.kind, self.hits, self.flash = rect, kind, hits, 0


# ---- sounds -----------------------------------------------------------------------------------------------------
def _make_sounds():
    """Little square-wave blips, written once to this computer's data folder."""
    folder = host.data("claudeanoid") / "sounds"
    rate = 22050
    recipes = {"paddle": [(440, 0.045)], "brick": [(880, 0.04)], "silver": [(1320, 0.05)], "gold": [(196, 0.06)],
               "capsule": [(523, 0.05), (659, 0.05), (784, 0.07)], "laser": [(1760, 0.03)],
               "lose": [(392, 0.12), (330, 0.12), (262, 0.12), (196, 0.25)],
               "clear": [(523, 0.08), (659, 0.08), (784, 0.08), (1047, 0.2)], "life": [(784, 0.07), (1047, 0.07)] * 3,
               "wall": [(330, 0.025)]}
    paths = {}
    for name, notes in recipes.items():
        path = folder / f"{name}.wav"
        paths[name] = path
        if path.exists():
            continue
        folder.mkdir(parents=True, exist_ok=True)
        frames = bytearray()
        for freq, length in notes:
            count = int(rate * length)
            for i in range(count):
                fade = 1 - i / count
                square = 1 if (i * freq / rate) % 1 < 0.5 else -1
                frames += struct.pack("<h", int(square * 6000 * fade))
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(bytes(frames))
    return paths


class Sounds:
    def __init__(self, parent):
        self.effects = {}
        try:
            from PySide6.QtMultimedia import QSoundEffect
            for name, path in _make_sounds().items():
                fx = QSoundEffect(parent)
                fx.setSource(QUrl.fromLocalFile(str(path)))
                fx.setVolume(0.45)
                self.effects[name] = fx
        except Exception:
            self.effects = {}

    def play(self, name):
        fx = self.effects.get(name)
        if fx is not None and not host.muted():
            fx.play()


# ---- high scores ------------------------------------------------------------------------------------------------
def load_scores():
    try:
        data = json.loads(SCORES.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def add_score(score, round_):
    scores = load_scores()
    entry = {"name": host.user_name() or "Player", "score": score, "round": round_,
             "date": host.now().strftime("%m/%d/%Y")}
    scores.append(entry)
    scores.sort(key=lambda s: -s["score"])
    scores = scores[:10]
    try:
        SCORES.write_text(json.dumps(scores, indent=1), encoding="utf-8")
    except OSError:
        pass
    return entry in scores, scores


# ---- the game ---------------------------------------------------------------------------------------------------
class Claudeanoid(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setFixedSize(FIELD_W + PANEL_W, FIELD_H)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.BlankCursor)
        self.sounds = Sounds(self)
        self.scores = load_scores()
        self.state = "title"                       # title, banner, play, paused, over, won
        self.keys = set()
        self.score, self.lives, self.round = 0, 3, 1
        self.last_entry = None
        self.stars = [(random.randrange(FIELD_W), random.randrange(FIELD_H), random.random()) for _ in range(70)]
        self._new_round_objects()
        self.timer = QTimer(self, interval=16, timeout=self.tick)
        self.timer.start()
        self.last = time.time()

    # ---- set-up -----------------------------------------------------------------------------------------------
    def new_game(self):
        self.score, self.lives, self.round = 0, 3, 1
        self.start_round()

    def start_round(self):
        self._new_round_objects()
        rows = layout(self.round)
        silver_hits = 2 + (self.round - 1) // 8
        left = (FIELD_W - COLS * BW) / 2
        for r, line in enumerate(rows):
            for c, ch in enumerate(line):
                if ch == ".":
                    continue
                rect = QRectF(left + c * BW, TOP + r * BH, BW, BH)
                self.bricks.append(Brick(rect, ch, silver_hits if ch == "s" else 1))
        self.state = "banner"
        self.banner_until = time.time() + 1.6

    def _new_round_objects(self):
        self.bricks, self.capsules, self.shots, self.particles = [], [], [], []
        self.paddle_w, self.paddle_x = 80.0, FIELD_W / 2
        self.power = None                          # E, L, C or S while it lasts
        self.speed = 5.2 + min(self.round, 40) * 0.07 if hasattr(self, "round") else 5.2
        self.balls = [self._ball_on_paddle()]
        self.warp = False

    def _ball_on_paddle(self):
        return {"x": self.paddle_x, "y": PADDLE_Y - BALL_R - 1, "dx": 0.0, "dy": 0.0, "stuck": True, "offset": 12.0}

    # ---- input -----------------------------------------------------------------------------------------------
    def mouseMoveEvent(self, event):
        if self.state in ("play", "banner"):
            self.paddle_x = max(self.paddle_w / 2, min(FIELD_W - self.paddle_w / 2, event.position().x()))

    def mousePressEvent(self, event):
        self.setFocus()
        self._action()

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Left, Qt.Key_Right):
            self.keys.add(key)
        elif key in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self._action()
        elif key in (Qt.Key_P, Qt.Key_Escape):
            if self.state == "play":
                self.state = "paused"
            elif self.state == "paused":
                self.state = "play"
                self.last = time.time()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self.keys.discard(event.key())

    def _action(self):
        if self.state in ("title", "over", "won"):
            self.new_game()
            return
        if self.state == "paused":
            self.state = "play"
            self.last = time.time()
            return
        if self.state != "play":
            return
        launched = False
        for b in self.balls:
            if b["stuck"]:
                b["stuck"] = False
                angle = math.radians(-60 + 120 * (b["offset"] + self.paddle_w / 2) / self.paddle_w)
                b["dx"], b["dy"] = math.sin(angle) * self.speed, -math.cos(angle) * self.speed
                launched = True
        if not launched and self.power == "L" and len(self.shots) < 6:
            for side in (-1, 1):
                self.shots.append([self.paddle_x + side * (self.paddle_w / 2 - 8), PADDLE_Y - 6])
            self.sounds.play("laser")

    # ---- the game loop ---------------------------------------------------------------------------------------
    def tick(self):
        now = time.time()
        frame_dt = min(0.05, now - self.last)
        self.last = now
        if self.state == "play" and self.frame is not None and not host.in_front(self.desktop, self.frame):
            self.state = "paused"                                  # someone switched away
        if self.state == "banner" and now >= self.banner_until:
            self.state = "play"
        if self.state in ("play", "banner"):
            step = 220 * frame_dt * (1 if Qt.Key_Right in self.keys else -1 if Qt.Key_Left in self.keys else 0) * 2.2
            self.paddle_x = max(self.paddle_w / 2, min(FIELD_W - self.paddle_w / 2, self.paddle_x + step))
            for b in self.balls:
                if b["stuck"]:
                    b["x"], b["y"] = self.paddle_x + b["offset"], PADDLE_Y - BALL_R - 1
        if self.state == "play":
            self._update(frame_dt * 60)
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.25
            p[5] -= 1
        self.particles = [p for p in self.particles if p[5] > 0]
        for brick in self.bricks:
            brick.flash = max(0, brick.flash - 1)
        self.update()

    def _update(self, k):
        slow = 0.7 if self.power == "S" else 1.0
        target_w = 120.0 if self.power == "E" else 80.0
        self.paddle_w += (target_w - self.paddle_w) * 0.2
        for b in list(self.balls):
            if b["stuck"]:
                continue
            dist = math.hypot(b["dx"], b["dy"]) * k * slow
            steps = max(1, int(dist / 3) + 1)
            for _ in range(steps):
                b["x"] += b["dx"] * k * slow / steps
                b["y"] += b["dy"] * k * slow / steps
                if self._collide(b):
                    break
            if b["y"] > FIELD_H + 20:
                self.balls.remove(b)
        if not self.balls:
            self._lose_life()
            return
        # lasers
        for s in list(self.shots):
            s[1] -= 12 * k
            hit = next((br for br in self.bricks if br.rect.contains(QPointF(s[0], s[1]))), None)
            if hit is not None:
                self._hit_brick(hit)
                self.shots.remove(s)
            elif s[1] < 0:
                self.shots.remove(s)
        # capsules
        paddle = QRectF(self.paddle_x - self.paddle_w / 2, PADDLE_Y, self.paddle_w, 12)
        for cap in list(self.capsules):
            cap[1] += 2.2 * k
            if paddle.intersects(QRectF(cap[0] - 16, cap[1] - 7, 32, 14)):
                self.capsules.remove(cap)
                self._catch(cap[2])
            elif cap[1] > FIELD_H:
                self.capsules.remove(cap)
        if self.warp and self.paddle_x + self.paddle_w / 2 >= FIELD_W - 2:
            self.score += 10000
            self._round_cleared()
        elif not any(br.kind != "G" for br in self.bricks):
            self._round_cleared()

    def _collide(self, b):
        """Walls, paddle and blocks for one small step; True once it has bounced."""
        x, y = b["x"], b["y"]
        if x < BALL_R:
            b["x"], b["dx"] = BALL_R, abs(b["dx"])
            self.sounds.play("wall")
        elif x > FIELD_W - BALL_R:
            b["x"], b["dx"] = FIELD_W - BALL_R, -abs(b["dx"])
            self.sounds.play("wall")
        if y < BALL_R + 24:
            b["y"], b["dy"] = BALL_R + 24, abs(b["dy"])
            self.sounds.play("wall")
        half = self.paddle_w / 2
        if b["dy"] > 0 and PADDLE_Y - BALL_R <= y <= PADDLE_Y + 8 and abs(x - self.paddle_x) <= half + BALL_R:
            offset = max(-half, min(half, x - self.paddle_x))
            angle = math.radians(-62 + 124 * (offset + half) / (2 * half))
            speed = min(self.speed + 0.3 * (len(self.bricks) < 10), 11.0)
            b["dx"], b["dy"] = math.sin(angle) * speed, -abs(math.cos(angle) * speed)
            b["y"] = PADDLE_Y - BALL_R - 1
            if self.power == "C":
                b["stuck"], b["offset"] = True, offset
            self.sounds.play("paddle")
            return True
        for brick in self.bricks:
            r = brick.rect
            if r.left() - BALL_R < x < r.right() + BALL_R and r.top() - BALL_R < y < r.bottom() + BALL_R:
                over_x = min(x - (r.left() - BALL_R), (r.right() + BALL_R) - x)
                over_y = min(y - (r.top() - BALL_R), (r.bottom() + BALL_R) - y)
                if over_x < over_y:
                    b["dx"] = -b["dx"]
                    b["x"] += -over_x if x < r.center().x() else over_x
                else:
                    b["dy"] = -b["dy"]
                    b["y"] += -over_y if y < r.center().y() else over_y
                self._hit_brick(brick)
                self.speed = min(self.speed + 0.012, 10.5)
                return True
        return False

    def _hit_brick(self, brick):
        if brick.kind == "G":
            brick.flash = 6
            self.sounds.play("gold")
            return
        brick.hits -= 1
        if brick.hits > 0:
            brick.flash = 6
            self.sounds.play("silver")
            return
        self.bricks.remove(brick)
        colour = COLOURS.get(brick.kind, ("#C8C8D0", 0))
        self.score += 50 * self.round if brick.kind == "s" else colour[1]
        self.sounds.play("brick")
        c = brick.rect.center()
        for _ in range(8):
            self.particles.append([c.x(), c.y(), random.uniform(-2.5, 2.5), random.uniform(-3, 0.5),
                                   colour[0], random.randint(14, 26)])
        if random.random() < 0.13 and not self.capsules and len(self.balls) == 1:
            self.capsules.append([c.x(), c.y(), random.choice(CAPSULE_ODDS)])

    def _catch(self, kind):
        self.score += 1000
        self.sounds.play("capsule")
        if kind == "P":
            self.lives += 1
            self.sounds.play("life")
            return
        if kind == "B":
            self.warp = True
            return
        if kind == "D":
            base = next((b for b in self.balls if not b["stuck"]), None)
            if base is not None:
                for turn in (-0.45, 0.45):
                    a = math.atan2(base["dx"], -base["dy"]) + turn
                    s = math.hypot(base["dx"], base["dy"])
                    self.balls.append({"x": base["x"], "y": base["y"], "dx": math.sin(a) * s, "dy": -math.cos(a) * s,
                                       "stuck": False, "offset": 0.0})
            self.power = None
            return
        if self.power == "C" and kind != "C":
            for b in self.balls:
                if b["stuck"]:
                    self._action()
        self.power = kind
        if kind == "S":
            for b in self.balls:
                b["dx"] *= 0.8
                b["dy"] *= 0.8

    def _lose_life(self):
        self.lives -= 1
        self.sounds.play("lose")
        if self.lives <= 0:
            self._game_over("over")
            return
        self.capsules, self.shots = [], []
        self.power, self.warp = None, False
        self.balls = [self._ball_on_paddle()]
        self.state = "banner"
        self.banner_until = time.time() + 1.2

    def _round_cleared(self):
        self.sounds.play("clear")
        if self.round >= ROUNDS:
            self._game_over("won")
            return
        self.round += 1
        self.start_round()

    def _game_over(self, how):
        self.state = how
        made_it, self.scores = add_score(self.score, self.round)
        self.last_entry = self.score if made_it else None

    # ---- drawing ----------------------------------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 0, FIELD_H)
        g.setColorAt(0, QColor("#0A1030"))
        g.setColorAt(1, QColor("#1A0A30"))
        p.fillRect(QRectF(0, 0, FIELD_W, FIELD_H), g)
        for x, y, b in self.stars:
            p.fillRect(QRectF(x, y, 2, 2), QColor(255, 255, 255, int(60 + 120 * b)))
        p.fillRect(QRectF(0, 0, FIELD_W, 24), QColor("#3A3A4A"))           # the top wall
        p.fillRect(QRectF(0, 22, FIELD_W, 2), QColor("#8A8AA0"))
        if self.state != "title":
            self._draw_field(p)
        self._draw_panel(p)
        if self.state == "title":
            self._draw_title(p)
        elif self.state == "banner":
            self._text(p, f"ROUND {self.round}", 34, FIELD_H / 2 + 30, "#FFFFFF")
            self._text(p, "READY", 18, FIELD_H / 2 + 64, "#F4E030")
        elif self.state == "paused":
            self._text(p, "PAUSED", 34, FIELD_H / 2, "#FFFFFF")
            self._text(p, "Click or press P to carry on", 12, FIELD_H / 2 + 30, "#C0C8E0")
        elif self.state in ("over", "won"):
            p.fillRect(QRectF(0, 0, FIELD_W, FIELD_H), QColor(0, 0, 0, 150))
            self._text(p, "YOU BEAT ALL 40 ROUNDS!" if self.state == "won" else "GAME OVER", 32, 150,
                       "#F4E030" if self.state == "won" else "#F0383C")
            self._text(p, f"Score {self.score:,}", 18, 190, "#FFFFFF")
            if self.last_entry is not None:
                self._text(p, "A new high score!", 14, 218, "#4ED84E")
            self._draw_scores(p, 250)
            self._text(p, "Click to play again", 14, FIELD_H - 40, "#C0C8E0")
        p.end()

    def _draw_field(self, p):
        for brick in self.bricks:
            r = brick.rect.adjusted(1, 1, -1, -1)
            if brick.kind == "G":
                base = QColor("#D8B030")
            elif brick.kind == "s":
                base = QColor("#B8BCC8")
            else:
                base = QColor(COLOURS[brick.kind][0])
            if brick.flash:
                base = base.lighter(170)
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            g.setColorAt(0, base.lighter(140))
            g.setColorAt(1, base.darker(120))
            p.fillRect(r, g)
            p.fillRect(QRectF(r.left(), r.bottom() - 3, r.width(), 3), base.darker(160))
            p.fillRect(QRectF(r.right() - 3, r.top(), 3, r.height()), base.darker(140))
        for x, y, dx, dy, colour, life in self.particles:
            c = QColor(colour)
            c.setAlpha(min(255, life * 12))
            p.fillRect(QRectF(x, y, 3, 3), c)
        for x, y, kind in self.capsules:
            rect = QRectF(x - 16, y - 7, 32, 14)
            g = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            g.setColorAt(0, QColor(CAPSULES[kind]).lighter(150))
            g.setColorAt(1, QColor(CAPSULES[kind]).darker(130))
            p.setPen(QPen(QColor(20, 20, 20), 1))
            p.setBrush(g)
            p.drawRoundedRect(rect, 7, 7)
            p.setPen(QColor("white"))
            p.setFont(QFont("Arial", 9, QFont.Bold))
            p.drawText(rect, Qt.AlignCenter, kind)
        p.setPen(Qt.NoPen)
        for s in self.shots:
            p.fillRect(QRectF(s[0] - 1.5, s[1] - 8, 3, 10), QColor("#FF6060"))
        # the paddle (the Vaus): capsule ends, a metal middle; red cannons when lasers are armed
        x0 = self.paddle_x - self.paddle_w / 2
        body = QRectF(x0, PADDLE_Y, self.paddle_w, 12)
        g = QLinearGradient(body.topLeft(), body.bottomLeft())
        g.setColorAt(0, QColor("#E8E8F0"))
        g.setColorAt(0.5, QColor("#9898A8"))
        g.setColorAt(1, QColor("#585868"))
        p.setBrush(g)
        p.drawRoundedRect(body, 6, 6)
        end = QColor("#F0383C") if self.power == "L" else QColor("#3C6CF0")
        p.setBrush(end)
        p.drawRoundedRect(QRectF(x0, PADDLE_Y, 14, 12), 6, 6)
        p.drawRoundedRect(QRectF(x0 + self.paddle_w - 14, PADDLE_Y, 14, 12), 6, 6)
        if self.warp:
            p.setBrush(QColor(224, 64, 224, 160 + int(60 * math.sin(time.time() * 8))))
            p.drawRect(QRectF(FIELD_W - 6, PADDLE_Y - 30, 6, 60))
        for b in self.balls:
            g = QRadialGradient(QPointF(b["x"] - 2, b["y"] - 2), BALL_R * 1.4)
            g.setColorAt(0, QColor("white"))
            g.setColorAt(1, QColor("#A0B0D0"))
            p.setBrush(g)
            p.drawEllipse(QPointF(b["x"], b["y"]), BALL_R, BALL_R)

    def _draw_panel(self, p):
        x = FIELD_W
        g = QLinearGradient(x, 0, x + PANEL_W, 0)
        g.setColorAt(0, QColor("#202838"))
        g.setColorAt(1, QColor("#101420"))
        p.fillRect(QRectF(x, 0, PANEL_W, FIELD_H), g)
        p.fillRect(QRectF(x, 0, 3, FIELD_H), QColor("#8A8AA0"))
        p.setPen(QColor("#F4E030"))
        p.setFont(QFont("Arial Black", 16))
        p.drawText(QRectF(x, 14, PANEL_W, 30), Qt.AlignCenter, "CLAUDEANOID")
        best = self.scores[0]["score"] if self.scores else 0
        lines = [("HIGH SCORE", f"{max(best, self.score):,}"), ("SCORE", f"{self.score:,}"),
                 ("ROUND", f"{self.round} / {ROUNDS}"), ("PADDLES", str(max(self.lives, 0)))]
        y = 64
        for label, value in lines:
            p.setPen(QColor("#F0383C"))
            p.setFont(QFont("Arial", 9, QFont.Bold))
            p.drawText(QRectF(x + 14, y, PANEL_W - 28, 16), Qt.AlignLeft, label)
            p.setPen(QColor("white"))
            p.setFont(QFont("Arial", 15, QFont.Bold))
            p.drawText(QRectF(x + 14, y + 16, PANEL_W - 28, 24), Qt.AlignLeft, value)
            y += 50
        if self.power:
            names = {"E": "EXPAND", "L": "LASER", "C": "CATCH", "S": "SLOW"}
            p.setPen(QColor(CAPSULES[self.power]).lighter(130))
            p.setFont(QFont("Arial", 11, QFont.Bold))
            p.drawText(QRectF(x + 14, y, PANEL_W - 28, 20), Qt.AlignLeft, f"POWER: {names[self.power]}")
        p.setPen(QColor("#8890A8"))
        p.setFont(QFont("Tahoma", 8))
        p.drawText(QRectF(x + 14, FIELD_H - 128, PANEL_W - 28, 120), Qt.AlignLeft | Qt.TextWordWrap,
                   "Mouse or arrow keys: move\nClick or Space: launch / fire\nP or Esc: pause\n\n"
                   "E expand  L laser  C catch\nS slow  D disruption\nP extra paddle  B break out")

    def _draw_title(self, p):
        self._text(p, "CLAUDEANOID", 46, 140, "#F4E030")
        self._text(p, "40 rounds of block breaking", 14, 176, "#C0C8E0")
        self._draw_scores(p, 230)
        self._text(p, "Click to start", 16, FIELD_H - 50, "#FFFFFF")

    def _draw_scores(self, p, y):
        self._text(p, "- HIGH SCORES -", 13, y, "#F0383C")
        p.setFont(QFont("Courier New", 11, QFont.Bold))
        if not self.scores:
            self._text(p, "No scores yet", 11, y + 26, "#8890A8")
        for i, s in enumerate(self.scores[:10]):
            p.setPen(QColor("#4ED84E") if s["score"] == self.last_entry else QColor("white"))
            line = f"{i + 1:>2}. {s['name'][:14]:<14} {s['score']:>8,}  R{s['round']:<2} {s['date']}"
            p.drawText(QRectF(0, y + 10 + i * 20, FIELD_W, 20), Qt.AlignCenter, line)

    @staticmethod
    def _text(p, text, size, y, colour):
        p.setFont(QFont("Arial Black", size))
        p.setPen(QColor(0, 0, 0, 180))
        p.drawText(QRectF(2, y - size * 1.6 + 2, FIELD_W, size * 2), Qt.AlignCenter, text)
        p.setPen(QColor(colour))
        p.drawText(QRectF(0, y - size * 1.6, FIELD_W, size * 2), Qt.AlignCenter, text)

    def shutdown(self):
        self.timer.stop()


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = Claudeanoid(desktop)
    win = host.window(desktop, "Claudeanoid", body, claudeanoid_icon(), size=(FIELD_W + PANEL_W, FIELD_H))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    body.setFocus()
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.shutdown()
