"""Claudemmings' rules: the terrain (a solid/air mask over the level's map, carved and built on) and the lemmings.

Everything is in map pixels; one step is one game frame (17 a second, like the original). A lemming's (x, y) is its
foot: when standing, the map pixel at (x, y) is solid ground and the body is the 10 pixels above it.

    level = Level(spec, map_image)          # spec from levels.LEVELS, map_image a QImage of the map
    level.step()                            # one frame; level.events lists what happened (for sounds)
    level.assign(lemming, "digger")         # give a lemming a skill
"""
import math
import random

from PySide6.QtGui import QColor, QImage, QPainter

FPS = 17
FALL_SPLAT = 60          # fall further than this and a lemming splats (unless floating)
STEP_UP = 6              # walk up a step at most this high; higher is a wall
BRICKS = 12
BRICK = QColor("#E8C8A8").rgba()
AIR_LEVEL = 40           # r+g+b at or below this is the map's black background (the maps are lossy WebP)
TRAP_W, TRAP_H = 45, 25

BUSY = ("walk", "build", "bash", "mine", "dig", "shrug")       # what a lemming can be switched from to a job


class Lemming:
    __slots__ = ("x", "y", "dir", "state", "frame", "fall", "climber", "floater", "bomb", "bricks", "gone",
                 "saved", "work")

    def __init__(self, x, y):
        self.x, self.y, self.dir = x, y, 1
        self.state, self.frame, self.fall = "fall", 0, 0
        self.climber = self.floater = False
        self.bomb = None            # frames until it goes off
        self.bricks = 0
        self.gone = self.saved = False
        self.work = 0               # frames into the current job's cycle

    def set(self, state):
        self.state, self.frame, self.work = state, 0, 0

    @property
    def alive(self):
        return not self.gone

    def label(self):
        if self.state in ("walk", "fall") and (self.climber or self.floater):
            return "Athlete" if self.climber and self.floater else ("Climber" if self.climber else "Floater")
        return {"walk": "Walker", "fall": "Faller", "float": "Floater", "climb": "Climber", "hoist": "Climber",
                "block": "Blocker", "build": "Builder", "shrug": "Builder", "bash": "Basher", "mine": "Miner",
                "dig": "Digger", "splat": "Splat", "exit": "Walker", "ohno": "Bomber"}.get(self.state, "Lemming")


class Level:
    def __init__(self, spec, image):
        self.spec = spec
        self.W, self.H = image.width(), image.height()
        img = image.convertToFormat(QImage.Format_ARGB32)
        self.solid = bytearray(self.W * self.H)
        tx, ty = spec["trapdoor"]
        self.trap = (tx, ty)
        dl, dt, dr, db = spec["door"]
        cx = (dl + dr) // 2
        # the exit's floor: the first solid row under the doorway (on the map as drawn)
        floor = db + 1
        while floor < self.H and _air(img.pixelColor(cx, floor)):
            floor += 1
        self.exit = (dl, dt, dr, floor)
        # the exit's arch and the trapdoor aren't terrain: they become decoration
        ex = (cx - 22, dt - 22, cx + 22, floor - 1)
        self.decor = QImage(self.W, self.H, QImage.Format_ARGB32)
        self.decor.fill(0)
        for y in range(self.H):
            for x in range(self.W):
                c = img.pixelColor(x, y)
                in_trap = tx - 1 <= x <= tx + TRAP_W and ty - 1 <= y <= ty + TRAP_H
                in_exit = ex[0] <= x <= ex[2] and ex[1] <= y <= ex[3]
                if _air(c):
                    img.setPixel(x, y, 0)
                elif in_trap:
                    img.setPixel(x, y, 0)
                elif in_exit:
                    self.decor.setPixel(x, y, c.rgba())
                    img.setPixel(x, y, 0)
                else:
                    self.solid[y * self.W + x] = 1
        self.terrain = img
        self.changed = True                      # the terrain image needs redrawing
        self.lemmings = []
        self.events = []
        self.skills = dict(spec["skills"])
        self.total = spec["lemmings"]
        self.out = 0                             # let out of the trapdoor so far
        self.min_rate = spec["rate"]
        self.rate = spec["rate"]
        self.time_left = spec["minutes"] * 60 * FPS
        self.tick = 0
        self.trap_frame = 0                      # 0 closed ... 9 open
        self.release_wait = 0
        self.nuking = False
        self.done = False
        self.particles = []                      # [x, y, vx, vy, life, rgb]
        self.spawn_at = (tx + TRAP_W // 2, ty + 14)

    # ---- the terrain ----------------------------------------------------------------------------------------
    def is_solid(self, x, y):
        if x < 0 or x >= self.W:
            return True                          # the sides of the level are walls
        if y < 0 or y >= self.H:
            return False
        return self.solid[y * self.W + x] == 1

    def clear(self, x, y):
        if 0 <= x < self.W and 0 <= y < self.H and self.solid[y * self.W + x]:
            self.solid[y * self.W + x] = 0
            self.terrain.setPixel(x, y, 0)
            self.changed = True
            return True
        return False

    def fill(self, x, y):
        if 0 <= x < self.W and 0 <= y < self.H and not self.solid[y * self.W + x]:
            self.solid[y * self.W + x] = 1
            self.terrain.setPixel(x, y, BRICK)
            self.changed = True

    def any_solid(self, x0, x1, y0, y1):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                if 0 <= x < self.W and self.is_solid(x, y):
                    return True
        return False

    # ---- the frame --------------------------------------------------------------------------------------------
    def step(self):
        self.events = []
        if self.done:
            return
        self.tick += 1
        if self.trap_frame < 9:
            if self.tick == FPS:
                self.events.append("door")
            if self.tick >= FPS and self.tick % 2 == 0:
                self.trap_frame += 1
        elif not self.nuking and self.out < self.total:
            self.release_wait -= 1
            if self.release_wait <= 0:
                lem = Lemming(*self.spawn_at)
                self.lemmings.append(lem)
                self.out += 1
                self.release_wait = max(4, 53 - self.rate // 2)
        if self.trap_frame >= 9 and self.time_left > 0:
            self.time_left -= 1
        for lem in self.lemmings:
            if not lem.gone:
                self._lemming(lem)
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.25
            p[4] -= 1
        self.particles = [p for p in self.particles if p[4] > 0]
        alive = [lem for lem in self.lemmings if not lem.gone]
        all_out = self.out >= self.total or self.nuking
        if (all_out and not alive and self.trap_frame >= 9) or self.time_left <= 0:
            self.done = True

    @property
    def saved(self):
        return sum(1 for lem in self.lemmings if lem.saved)

    @property
    def alive_count(self):
        return sum(1 for lem in self.lemmings if not lem.gone)

    def percent(self, n=None):
        return int(100 * (self.saved if n is None else n) / max(1, self.total))

    @property
    def won(self):
        return self.percent() >= self.spec["save"]

    # ---- one lemming ------------------------------------------------------------------------------------------
    def _lemming(self, lem):
        lem.frame += 1
        if lem.bomb is not None and lem.state not in ("ohno", "splat", "exit"):
            lem.bomb -= 1
            if lem.bomb <= 0:
                lem.bomb = None
                if lem.state in ("walk", "block", "build", "bash", "mine", "dig", "shrug"):
                    lem.set("ohno")
                    self.events.append("ohno")
                else:
                    self._explode(lem)
                    return
        getattr(self, "_" + lem.state)(lem)

    def _walk(self, lem):
        if self._at_exit(lem):
            return
        for b in self.lemmings:                       # a blocker turns walkers round
            if b is not lem and b.state == "block" and not b.gone and abs(b.y - lem.y) <= 8 \
                    and 0 < (b.x - lem.x) * lem.dir <= 6:
                lem.dir = -lem.dir
                return
        x2 = lem.x + lem.dir
        if self.is_solid(x2, lem.y - 1):
            up = 1
            while up <= STEP_UP + 1 and self.is_solid(x2, lem.y - 1 - up):
                up += 1
            if up > STEP_UP or x2 < 0 or x2 >= self.W:
                if lem.climber and 0 <= x2 < self.W:
                    lem.set("climb")
                else:
                    lem.dir = -lem.dir
                return
            lem.x, lem.y = x2, lem.y - up
            return
        lem.x = x2
        if self.is_solid(lem.x, lem.y):
            return
        for d in (1, 2, 3):
            if self.is_solid(lem.x, lem.y + d):
                lem.y += d
                return
        lem.y += 1
        lem.set("fall")
        lem.fall = 1

    def _at_exit(self, lem):
        dl, dt, dr, floor = self.exit
        cx = (dl + dr) // 2
        if abs(lem.x - cx) <= max(2, (dr - dl) // 3) and dt - 4 <= lem.y <= floor + 2:
            lem.set("exit")
            self.events.append("yippee")
            return True
        return False

    def _fall(self, lem):
        if lem.y >= self.H:
            self._out_of_level(lem)
            return
        speed = 3
        if lem.floater and lem.fall >= 16:
            lem.set("float")
            return
        for _ in range(speed):
            if self.is_solid(lem.x, lem.y):
                if lem.fall > FALL_SPLAT:
                    lem.set("splat")
                    self.events.append("splat")
                else:
                    lem.set("walk")
                return
            lem.y += 1
            lem.fall += 1
            if lem.y >= self.H:
                self._out_of_level(lem)
                return

    def _float(self, lem):
        if lem.y >= self.H:
            self._out_of_level(lem)
            return
        if lem.frame % 2 == 0 or lem.frame < 4:
            return
        if self.is_solid(lem.x, lem.y):
            lem.set("walk")
            lem.fall = 0
            return
        lem.y += 1

    def _out_of_level(self, lem):
        lem.gone = True
        self.events.append("die")

    def _climb(self, lem):
        if lem.frame % 2:
            return
        if self.is_solid(lem.x, lem.y - 11):             # a ceiling over its head: let go
            lem.dir = -lem.dir
            lem.x += lem.dir
            lem.set("fall")
            lem.fall = 0
            return
        lem.y -= 1
        if not self.is_solid(lem.x + lem.dir, lem.y - 1):  # over the top
            lem.set("hoist")

    def _hoist(self, lem):
        if lem.frame >= 6:
            lem.x += lem.dir
            while lem.y < self.H and not self.is_solid(lem.x, lem.y):
                lem.y += 1
            if lem.y >= self.H:
                self._out_of_level(lem)
                return
            lem.set("walk")

    def _block(self, lem):
        if not self.is_solid(lem.x, lem.y):
            lem.set("fall")
            lem.fall = 0

    def _build(self, lem):
        lem.work += 1
        if lem.work == 9:                                  # lay a brick: 6 wide, at foot level - 1
            for i in range(6):
                self.fill(lem.x + lem.dir * i, lem.y - 1)
            lem.bricks -= 1
            if lem.bricks < 3:
                self.events.append("chink")
        elif lem.work >= 16:
            lem.work = 0
            if self.is_solid(lem.x + lem.dir * 2, lem.y - 2) or self.is_solid(lem.x + lem.dir, lem.y - 9):
                lem.dir = -lem.dir                          # bumped its head or a wall
                lem.set("walk")
                return
            lem.x += 2 * lem.dir
            lem.y -= 1
            if lem.bricks <= 0:
                lem.set("shrug")

    def _shrug(self, lem):
        if lem.frame >= 8:
            lem.set("walk")

    def _bash(self, lem):
        if not self.is_solid(lem.x, lem.y) and not self.is_solid(lem.x, lem.y + 1):
            lem.set("fall")
            lem.fall = 0
            return
        lem.work += 1
        if lem.work % 2:
            return
        if not self.any_solid(lem.x + lem.dir, lem.x + lem.dir * 9, lem.y - 9, lem.y - 2):
            lem.set("walk")                                 # nothing left to bash
            return
        for dx in range(1, 4):
            for dy in range(1, 10):
                self.clear(lem.x + lem.dir * dx, lem.y - dy)
        lem.x += lem.dir
        if not self.is_solid(lem.x, lem.y):
            for d in (1, 2):
                if self.is_solid(lem.x, lem.y + d):
                    lem.y += d
                    break

    def _mine(self, lem):
        lem.work += 1
        if lem.work % 3:
            return
        for dx in range(0, 4):
            for dy in range(-1, 10):
                self.clear(lem.x + lem.dir * dx, lem.y - dy)
        lem.x += lem.dir
        lem.y += 1
        if lem.y >= self.H:
            self._out_of_level(lem)
            return
        if not self.is_solid(lem.x, lem.y):
            lem.set("fall")
            lem.fall = 0

    def _dig(self, lem):
        lem.work += 1
        if lem.work % 2:
            return
        if not self.any_solid(lem.x - 4, lem.x + 4, lem.y, lem.y):
            lem.set("fall")
            lem.fall = 0
            return
        for dx in range(-4, 5):
            self.clear(lem.x + dx, lem.y)
        lem.y += 1
        if lem.y >= self.H:
            self._out_of_level(lem)

    def _splat(self, lem):
        if lem.frame >= 16:
            lem.gone = True

    def _exit(self, lem):
        if lem.frame >= 8:
            lem.gone = lem.saved = True

    def _ohno(self, lem):
        if lem.frame >= 16:
            self._explode(lem)
        elif not self.is_solid(lem.x, lem.y):
            lem.y += 1

    def _explode(self, lem):
        cx, cy = lem.x, lem.y - 5
        for dy in range(-9, 10):
            for dx in range(-9, 10):
                if dx * dx + dy * dy <= 80:
                    self.clear(cx + dx, cy + dy)
        for _ in range(24):
            a = random.uniform(0, 2 * math.pi)
            v = random.uniform(1.0, 3.5)
            self.particles.append([float(cx), float(cy), math.cos(a) * v, math.sin(a) * v - 2,
                                   random.randint(12, 26), random.choice((0x00B000, 0x4040E0, 0xF0D0D0, 0xFFFFFF))])
        lem.gone = True
        self.events.append("explode")

    # ---- what the player does -------------------------------------------------------------------------------------
    def assign(self, lem, skill):
        """Give lem the skill if it can take it; True (and one fewer of that skill) if it did."""
        if lem is None or lem.gone or self.skills.get(skill, 0) <= 0 or self.done:
            return False
        s = lem.state
        if s in ("splat", "exit", "ohno"):
            return False
        ok = False
        if skill == "climber" and not lem.climber:
            lem.climber = ok = True
        elif skill == "floater" and not lem.floater:
            lem.floater = ok = True
        elif skill == "bomber" and lem.bomb is None:
            lem.bomb, ok = 5 * FPS, True
        elif skill == "blocker" and s in BUSY and self.is_solid(lem.x, lem.y):
            lem.set("block")
            ok = True
        elif skill in ("builder", "basher", "miner", "digger") and s in BUSY:
            state = {"builder": "build", "basher": "bash", "miner": "mine", "digger": "dig"}[skill]
            if state == "dig" or s != state:
                lem.set(state)
                if state == "build":
                    lem.bricks = BRICKS
                ok = True
        if ok:
            self.skills[skill] -= 1
            self.events.append("assign")
        return ok

    def lemming_at(self, x, y, prefer=None):
        """The lemming under map point (x, y), if any (one that can take `prefer` first)."""
        best, best_d = None, 1e9
        for lem in self.lemmings:
            if lem.gone or lem.state in ("splat", "exit"):
                continue
            if lem.x - 5 <= x <= lem.x + 5 and lem.y - 12 <= y <= lem.y + 2:
                d = abs(lem.x - x) + abs(lem.y - 5 - y) * 0.5
                if prefer == "blocker" and lem.state == "block":
                    d += 50
                if d < best_d:
                    best, best_d = lem, d
        return best

    def lemmings_under(self, x, y):
        return [lem for lem in self.lemmings if not lem.gone and lem.state not in ("splat", "exit")
                and lem.x - 5 <= x <= lem.x + 5 and lem.y - 12 <= y <= lem.y + 2]

    def nuke(self):
        if self.nuking or self.done:
            return
        self.nuking = True
        k = 0
        for lem in self.lemmings:
            if not lem.gone and lem.bomb is None and lem.state not in ("splat", "exit"):
                lem.bomb = 5 * FPS + k
                k += 1
        self.events.append("ohno")

    def change_rate(self, d):
        r = max(self.min_rate, min(99, self.rate + d))
        if r != self.rate:
            self.rate = r
            return True
        return False


def _air(c):
    return c.alpha() < 128 or c.red() + c.green() + c.blue() <= AIR_LEVEL
