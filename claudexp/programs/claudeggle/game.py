"""Claudeggle's rules: the pegs, the ball's bounces, the bucket, powers, scoring and Extreme Fever.

The field is W x H pixels. Blue pegs are worth 10, orange 100 (clear them all to win), green 10 and they set off
the level's power, and one purple peg (500) moves to a new blue peg every shot. Points are multiplied by how few
oranges are left. Pegs the ball lights stay until the shot is over, then pop.
"""
import math
import random

W, H = 760, 600
BALL_R = 7
PEG_R = 9
GRAVITY = 520.0
SPEED = 560.0
LAUNCH = (W / 2, 46)
BUCKET_Y = H - 22
BUCKET_HALF = 48
ORANGES = 25
POINTS = {"blue": 10, "orange": 100, "green": 10, "purple": 500}
POWERS = {"guide": ("Super Guide", "Green pegs show the ball's path for the next three shots."),
          "multi": ("Multiball", "A green peg splits off a second ball."),
          "fire": ("Fireball", "A green peg sets the ball ablaze: it burns straight through pegs."),
          "spooky": ("Spooky Ball", "A green peg makes the ball come back from the top once it falls out."),
          "zap": ("Zap", "A green peg lights every peg near it.")}
FEVER_SLOTS = [10000, 50000, 100000, 50000, 10000]


class Peg:
    __slots__ = ("x", "y", "x2", "y2", "brick", "colour", "lit", "gone", "orbit", "pop")

    def __init__(self, x, y, x2=None, y2=None, orbit=None):
        self.x, self.y = x, y
        self.brick = x2 is not None
        self.x2, self.y2 = (x2, y2) if self.brick else (x, y)
        self.colour = "blue"
        self.lit = False
        self.gone = False
        self.orbit = orbit                    # (cx, cy, radius, angle, speed) for pegs on a turning wheel
        self.pop = 0.0

    def centre(self):
        return (self.x + self.x2) / 2, (self.y + self.y2) / 2

    def closest(self, px, py):
        if not self.brick:
            return self.x, self.y
        dx, dy = self.x2 - self.x, self.y2 - self.y
        ln = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((px - self.x) * dx + (py - self.y) * dy) / ln)) if ln else 0.0
        return self.x + dx * t, self.y + dy * t


# ---- the levels -------------------------------------------------------------------------------------------------
def _ring(cx, cy, r, n, start=0.0):
    return [Peg(cx + math.cos(start + i / n * math.tau) * r, cy + math.sin(start + i / n * math.tau) * r)
            for i in range(n)]


def _arc_bricks(cx, cy, r, a0, a1, n):
    out = []
    for i in range(n):
        t0 = math.radians(a0 + (a1 - a0) * (i + 0.12) / n)
        t1 = math.radians(a0 + (a1 - a0) * (i + 0.88) / n)
        out.append(Peg(cx + math.cos(t0) * r, cy + math.sin(t0) * r, cx + math.cos(t1) * r, cy + math.sin(t1) * r))
    return out


def _line_bricks(x0, y0, x1, y1, n):
    out = []
    for i in range(n):
        a, b = (i + 0.1) / n, (i + 0.9) / n
        out.append(Peg(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a, x0 + (x1 - x0) * b, y0 + (y1 - y0) * b))
    return out


def lv_first_light():
    pegs = []
    for row in range(7):
        y = 170 + row * 50
        off = 25 if row % 2 else 0
        for i in range(12):
            x = 105 + off + i * 50
            if x < W - 80:
                pegs.append(Peg(x, y))
    return pegs


def lv_rings():
    return (_ring(W / 2, 330, 190, 34) + _ring(W / 2, 330, 125, 24, 0.13) + _ring(W / 2, 330, 60, 12)
            + [Peg(W / 2, 330)])


def lv_spiral():
    pegs = []
    for i in range(95):
        a = i * 0.36
        r = 40 + i * 2.1
        x, y = W / 2 + math.cos(a) * r, 340 + math.sin(a) * r * 0.85
        if 40 < x < W - 40 and 120 < y < 540:
            pegs.append(Peg(x, y))
    return pegs


def lv_waves():
    pegs = []
    for row in range(5):
        for i in range(20):
            x = 70 + i * 33
            y = 180 + row * 70 + math.sin(i * 0.55 + row) * 26
            pegs.append(Peg(x, y))
    return pegs


def lv_diamonds():
    pegs = []
    for cx, cy in ((190, 250), (380, 250), (570, 250), (285, 420), (475, 420)):
        for r in range(1, 4):
            for k in range(4 * r):
                side, t = divmod(k, r)
                corners = [(0, -1), (1, 0), (0, 1), (-1, 0)]
                (ax, ay), (bx, by) = corners[side], corners[(side + 1) % 4]
                f = t / r
                pegs.append(Peg(cx + (ax + (bx - ax) * f) * r * 24, cy + (ay + (by - ay) * f) * r * 24))
        pegs.append(Peg(cx, cy))
    return pegs


def lv_heart():
    pegs = []
    for i in range(46):
        t = i / 46 * math.tau
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pegs.append(Peg(W / 2 + x * 13, 320 - y * 13))
    for i in range(26):
        t = i / 26 * math.tau
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pegs.append(Peg(W / 2 + x * 7, 312 - y * 7))
    for x in (80, 140, 620, 680):
        for y in (200, 280, 360, 440):
            pegs.append(Peg(x, y))
    return pegs


def lv_arches():
    pegs = []
    for cx in (190, 380, 570):
        pegs += _arc_bricks(cx, 330, 85, 190, 350, 7)
        pegs += _ring(cx, 330, 40, 8)
    for i in range(14):
        pegs.append(Peg(80 + i * 46, 470))
        pegs.append(Peg(103 + i * 46, 520))
    return pegs


def lv_pinwheel():
    pegs = []
    for k in range(4):                                   # four turning arms
        for j in range(1, 8):
            pegs.append(Peg(0, 0, orbit=[W / 2, 340, j * 26, k * math.pi / 2, 0.55]))
    for side in (-1, 1):
        for i in range(6):
            pegs.append(Peg(W / 2 + side * (300 - i * 6), 170 + i * 64))
            pegs.append(Peg(W / 2 + side * (250 - i * 6), 200 + i * 64))
    return pegs


def lv_hourglass():
    pegs = []
    for row in range(9):
        y = 150 + row * 45
        half = abs(row - 4) * 50 + 40
        n = max(2, int(half * 2 / 40))
        for i in range(n + 1):
            pegs.append(Peg(W / 2 - half + i * (half * 2 / n), y))
    pegs += _line_bricks(110, 140, 330, 330, 6) + _line_bricks(650, 140, 430, 330, 6)
    return pegs


def lv_starfield():
    rnd = random.Random(42)
    pegs = []
    tries = 0
    while len(pegs) < 100 and tries < 4000:
        tries += 1
        x, y = rnd.uniform(50, W - 50), rnd.uniform(140, 530)
        if all((x - p.x) ** 2 + (y - p.y) ** 2 > 34 ** 2 for p in pegs):
            pegs.append(Peg(x, y))
    return pegs


def lv_smile():
    pegs = _ring(W / 2, 330, 200, 40)
    pegs += _ring(W / 2 - 75, 270, 30, 9) + _ring(W / 2 + 75, 270, 30, 9)
    pegs += _arc_bricks(W / 2, 330, 120, 20, 160, 7)
    pegs += [Peg(W / 2 - 90 + i * 30, 470) for i in range(7)]
    return pegs


def lv_finale():
    pegs = _ring(W / 2, 330, 90, 14) + _ring(W / 2, 330, 45, 8)
    for k in range(2):
        for j in range(1, 6):
            pegs.append(Peg(0, 0, orbit=[W / 2, 330, 112 + j * 18, k * math.pi, -0.4]))
    pegs += _arc_bricks(W / 2, 330, 260, 200, 340, 10)
    for side in (-1, 1):
        for i in range(7):
            pegs.append(Peg(W / 2 + side * (300 - i * 14), 300 + i * 34))
    for i in range(12):
        pegs.append(Peg(110 + i * 49, 545))
    return pegs


LEVELS = [("First Light", lv_first_light, "guide"), ("Rings", lv_rings, "multi"), ("Spiral", lv_spiral, "fire"),
          ("Waves", lv_waves, "spooky"), ("Diamond Mine", lv_diamonds, "zap"), ("Heart", lv_heart, "multi"),
          ("Arches", lv_arches, "guide"), ("Pinwheel", lv_pinwheel, "spooky"), ("Hourglass", lv_hourglass, "fire"),
          ("Starfield", lv_starfield, "zap"), ("Smile", lv_smile, "multi"), ("Grand Finale", lv_finale, "fire")]


class Ball:
    __slots__ = ("x", "y", "vx", "vy", "fire", "spooky", "trail", "hist", "hist_t", "last_orange")

    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.fire = False
        self.spooky = False
        self.trail = []
        self.hist = (x, y)
        self.hist_t = 0.0
        self.last_orange = None


class Game:
    def __init__(self, index, rnd=None):
        self.rnd = rnd or random.Random()
        self.index = index
        self.name, maker, self.power = LEVELS[index]
        self._place_orbits_of(pegs := maker())
        self.pegs = []
        for p in pegs:                        # no two pegs on top of each other
            cx, cy = p.centre()
            if p.orbit or all(q.orbit or math.hypot(cx - q.centre()[0], cy - q.centre()[1]) > 21 for q in self.pegs):
                self.pegs.append(p)
        self._colour()
        self.balls_left = 10
        self.score = 0
        self.shot_score = 0
        self.shots = 0
        self.balls = []
        self.state = "aim"                    # aim, flying, clearing, won, lost
        self.t = 0.0
        self.guide_shots = 0
        self.fever = False
        self.fever_slot = None
        self.slowmo = 0.0
        self.events = []                      # ("hit", peg, points) ("free", reason) ("fever",) ... for the screen
        self.clear_queue = []
        self.clear_t = 0.0
        self.free_this_shot = 0
        self.bucket_x = W / 2

    # ---- set-up ------------------------------------------------------------------------------------------------
    def _colour(self):
        pegs = self.pegs
        n_orange = min(ORANGES, 15 + self.index, max(5, int(len(pegs) * 0.3)))     # easing in: 15 on level 1
        order = self.rnd.sample(pegs, len(pegs))
        for p in order[:n_orange]:
            p.colour = "orange"
        for p in order[n_orange:n_orange + 2]:
            p.colour = "green"
        self.total_oranges = n_orange
        self._new_purple()

    def _new_purple(self):
        for p in self.pegs:
            if p.colour == "purple":
                p.colour = "blue"
        blues = [p for p in self.pegs if p.colour == "blue" and not p.gone and not p.lit]
        if blues:
            self.rnd.choice(blues).colour = "purple"

    def _place_orbits(self, dt):
        self._place_orbits_of(self.pegs, dt)

    @staticmethod
    def _place_orbits_of(pegs, dt=0.0):
        for p in pegs:
            if p.orbit:
                o = p.orbit
                o[3] += o[4] * dt
                p.x = p.x2 = o[0] + math.cos(o[3]) * o[2]
                p.y = p.y2 = o[1] + math.sin(o[3]) * o[2]

    # ---- the numbers ------------------------------------------------------------------------------------------
    def oranges_left(self):
        return sum(1 for p in self.pegs if p.colour == "orange" and not p.lit and not p.gone)

    def multiplier(self):
        hit = self.total_oranges - self.oranges_left()
        frac = hit / self.total_oranges
        return 1 if frac < 0.4 else 2 if frac < 0.6 else 3 if frac < 0.76 else 5 if frac < 0.88 else 10

    # ---- shooting ----------------------------------------------------------------------------------------------
    def aim_angle(self, mx, my):
        """The launcher's angle (radians, 0 = right, pi/2 = straight down) toward a point."""
        a = math.atan2(my - LAUNCH[1], mx - LAUNCH[0])
        if a < 0:                                         # pointing upward: lie flat on that side
            a = 0.0 if mx >= LAUNCH[0] else math.pi
        return max(math.radians(4), min(math.radians(176), a))

    def shoot(self, angle):
        if self.state != "aim" or self.balls_left <= 0:
            return False
        self.balls_left -= 1
        self.shots += 1
        self.shot_score = 0
        self.shot_t = 0.0
        self.free_this_shot = 0
        x, y = LAUNCH[0] + math.cos(angle) * 30, LAUNCH[1] + math.sin(angle) * 30
        self.balls = [Ball(x, y, math.cos(angle) * SPEED, math.sin(angle) * SPEED)]
        self.state = "flying"
        if self.guide_shots:
            self.guide_shots -= 1
        return True

    def guide(self, angle, bounces=1, steps=120):
        """Where the ball will go: points until it has touched `bounces` pegs."""
        x, y = LAUNCH[0] + math.cos(angle) * 30, LAUNCH[1] + math.sin(angle) * 30
        vx, vy = math.cos(angle) * SPEED, math.sin(angle) * SPEED
        pts = [(x, y)]
        touched = 0
        self.guide_hit = None
        dt = 1 / 60
        for _ in range(steps):
            for _s in range(3):
                h = dt / 3
                vy += GRAVITY * h
                x += vx * h
                y += vy * h
                if x < BALL_R or x > W - BALL_R:
                    vx = -vx
                    x = max(BALL_R, min(W - BALL_R, x))
                for p in self.pegs:
                    if p.gone:
                        continue
                    cx, cy = p.closest(x, y)
                    dx, dy = x - cx, y - cy
                    d = math.hypot(dx, dy)
                    rr = BALL_R + (6 if p.brick else PEG_R)
                    if d < rr and d > 0:
                        nx, ny = dx / d, dy / d
                        x, y = cx + nx * rr, cy + ny * rr
                        vn = vx * nx + vy * ny
                        if vn < 0:
                            vx -= 1.75 * vn * nx
                            vy -= 1.75 * vn * ny
                        touched += 1
                        if self.guide_hit is None:
                            self.guide_hit = p
                        break
            pts.append((x, y))
            if touched >= bounces or y > H:
                break
        return pts

    # ---- the simulation ---------------------------------------------------------------------------------------
    def step(self, dt):
        self.t += dt
        self.events = []
        self.bucket_x = W / 2 + math.sin(self.t * 0.8) * (W / 2 - 70)
        if self.slowmo > 0:
            self.slowmo -= dt
            dt *= 0.3
        self._place_orbits(dt)
        if self.state == "flying":
            self.shot_t += dt
            for b in list(self.balls):
                for _ in range(4):
                    if self._move(b, dt / 4):
                        break
                self._unstick(b, dt)
            if not self.balls:
                self._end_shot()
        elif self.state == "clearing":
            self.clear_t -= dt
            while self.clear_queue and self.clear_t <= 0:
                p = self.clear_queue.pop(0)
                p.gone = True
                self.events.append(("pop", p))
                self.clear_t += 0.045
            for p in self.pegs:
                if p.pop:
                    p.pop += dt
            if not self.clear_queue and self.clear_t <= -0.35:
                self._after_clear()

    def _move(self, b, h):
        """Move one ball a little. Returns True if it left play."""
        b.vy += GRAVITY * h
        b.x += b.vx * h
        b.y += b.vy * h
        if b.x < BALL_R:
            b.x, b.vx = BALL_R, abs(b.vx) * 0.9
        elif b.x > W - BALL_R:
            b.x, b.vx = W - BALL_R, -abs(b.vx) * 0.9
        if b.y < BALL_R and b.vy < 0:
            b.y, b.vy = BALL_R, -b.vy * 0.9
        for p in self.pegs:
            if p.gone:
                continue
            cx, cy = p.closest(b.x, b.y)
            dx, dy = b.x - cx, b.y - cy
            rr = BALL_R + (6 if p.brick else PEG_R)
            if dx * dx + dy * dy >= rr * rr:
                continue
            d = math.hypot(dx, dy) or 0.01
            if not b.fire:
                nx, ny = dx / d, dy / d
                b.x, b.y = cx + nx * rr, cy + ny * rr
                vn = b.vx * nx + b.vy * ny
                if vn < 0:
                    b.vx -= 1.72 * vn * nx
                    b.vy -= 1.72 * vn * ny
                    # a touch of spin keeps balls from balancing on a peg forever
                    b.vx += self.rnd.uniform(-6, 6)
            if not p.lit:
                self._light(p, b)
        # the bucket (or Extreme Fever's slots)
        if self.fever:
            if b.y > H - 34:
                slot = max(0, min(4, int(b.x / (W / 5))))
                self.fever_slot = slot
                self._add(FEVER_SLOTS[slot], b.x, H - 40, plain=True)
                self.events.append(("fever_slot", slot))
                self.balls.remove(b)
                return True
        else:
            for ex in (-BUCKET_HALF, BUCKET_HALF):
                rx, ry = self.bucket_x + ex, BUCKET_Y
                dx, dy = b.x - rx, b.y - ry
                d = math.hypot(dx, dy)
                if 0 < d < BALL_R + 5:
                    nx, ny = dx / d, dy / d
                    b.x, b.y = rx + nx * (BALL_R + 5), ry + ny * (BALL_R + 5)
                    vn = b.vx * nx + b.vy * ny
                    if vn < 0:
                        b.vx -= 1.6 * vn * nx
                        b.vy -= 1.6 * vn * ny
            if b.vy > 0 and BUCKET_Y - 4 < b.y < BUCKET_Y + 10 and abs(b.x - self.bucket_x) < BUCKET_HALF - 6:
                self.balls_left += 1
                self.events.append(("free", "Free Ball!", b.x))
                self.balls.remove(b)
                return True
        if b.y > H + BALL_R:
            if b.spooky:
                b.spooky = False
                b.y = BALL_R + 1
                b.vy = min(b.vy, 260.0)
                self.events.append(("spooky", b.x))
                return False
            self.balls.remove(b)
            return True
        if len(b.trail) > 18:
            b.trail.pop(0)
        b.trail.append((b.x, b.y))
        return False

    def _light(self, p, b):
        p.lit = True
        pts = self._add(POINTS[p.colour], *p.centre())
        self.events.append(("hit", p, pts))
        if p.colour == "orange":
            if b.last_orange is not None:
                ox, oy = b.last_orange
                if math.hypot(p.x - ox, p.y - oy) > 300:
                    self._add(25000, *p.centre(), plain=True)
                    self.events.append(("style", "Long Shot! +25,000", p.x, p.y))
            b.last_orange = (p.x, p.y)
            if self.oranges_left() == 0 and not self.fever:
                self.fever = True
                self.slowmo = 1.6
                self.events.append(("fever",))
        elif p.colour == "green":
            self._power(p, b)

    def _power(self, p, b):
        self.events.append(("power", self.power, p.x, p.y))
        if self.power == "guide":
            self.guide_shots += 3
        elif self.power == "multi":
            nb = Ball(b.x, b.y, -b.vx, b.vy - 60)
            self.balls.append(nb)
        elif self.power == "fire":
            b.fire = True
        elif self.power == "spooky":
            b.spooky = True
        elif self.power == "zap":
            for q in self.pegs:
                if not q.gone and not q.lit and math.hypot(q.x - p.x, q.y - p.y) < 130:
                    self._light(q, b)

    def _add(self, base, x, y, plain=False):
        pts = base if plain else base * self.multiplier()
        self.score += pts
        before = self.shot_score
        self.shot_score += pts
        if not self.fever:
            for limit in (25000, 75000, 125000):
                if before < limit <= self.shot_score:
                    self.balls_left += 1
                    self.free_this_shot += 1
                    self.events.append(("free", f"Free Ball! ({limit // 1000}k shot)", x))
        return pts

    def _unstick(self, b, dt):
        """A ball wedged between pegs: clear the lit pegs around it early, like the real thing."""
        b.hist_t += dt
        if b.hist_t < 1.4:
            return
        moved = math.hypot(b.x - b.hist[0], b.y - b.hist[1])
        b.hist, b.hist_t = (b.x, b.y), 0.0
        if b not in self.balls or (moved > 30 and self.shot_t < 12):
            return
        near = [p for p in self.pegs if p.lit and not p.gone and math.hypot(p.centre()[0] - b.x, p.centre()[1] - b.y) < (45 if moved <= 30 else 70)]
        for p in near:
            p.gone = True
            self.events.append(("pop", p))
        if not near and moved <= 30:
            b.vx += self.rnd.choice((-1, 1)) * 120
            b.vy -= 80

    def _end_shot(self):
        self.clear_queue = [p for p in self.pegs if p.lit and not p.gone]
        self.clear_queue.sort(key=lambda p: (p.colour != "orange", p.y))
        self.clear_t = 0.15
        self.state = "clearing"

    def _after_clear(self):
        if self.fever:
            self.score += self.balls_left * 10000
            self.state = "won"
            return
        if self.balls_left <= 0:
            self.state = "lost"
            return
        self._new_purple()
        self.state = "aim"
