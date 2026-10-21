"""Claudeita: descend through a living world of falling sand, flowing liquids and fire, with wands you build yourself.

Five biomes stacked deep - the Mines, the Frozen Depths, the Fungal Caverns, the Magma Vault and the Hollow Heart -
each guarded at its bottom by a boss (Gravelmaw, Rimecaller, Mother Spore, the Cinder Colossus) whose fall opens the
way to a Sanctuary with a healing fountain and a shop. The Unmaker waits at the very bottom. Everything can be
blown apart, dug through, flooded or burned. Wands are found deeper and better; their spells (projectiles, modifiers
and multicasts) are arranged in the wand editor (Tab). Death is final: the world is made anew.

A/D move, W or Space jump (hold to levitate), mouse to aim, left button to cast, 1-4 wands, E pick up / buy,
Tab wands and spells, Esc pause, R a new world after death."""
import json
import math
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import QWidget
from shiboken6 import isValid

from claudecore import host

from . import world as wd
from .magic import SPELLS, random_spell, random_wand, starter_wands

TITLE = "Claudeita"
TICK = 1 / 30
VIEW_W = 300                     # cells across the screen
GRAV = 0.18
ENEMIES = {   # hp, speed, damage, gold, how it moves, colour, (w, h), ranged spell or None, shot cooldown (ticks)
    "slime": (18, 0.6, 8, 6, "hop", "#5BC85B", (8, 6), None, 0),
    "bat": (10, 1.5, 6, 4, "fly", "#4A3B5C", (7, 5), None, 0),
    "hiisi": (30, 0.7, 10, 12, "walk", "#B0533C", (6, 11), "Spark Bolt", 70),
    "frost": (26, 1.0, 8, 12, "fly", "#9FD8F5", (7, 7), "Ice Shard", 80),
    "spore": (22, 0.5, 8, 10, "walk", "#B56FD6", (8, 8), "Acid Ball", 90),
    "worm": (60, 0.9, 14, 18, "dig", "#C07A6A", (6, 6), None, 0),
    "imp": (34, 1.2, 10, 16, "fly", "#E2481F", (7, 8), "Fireball", 100),
    "turret": (50, 0.0, 10, 20, "still", "#6E6E7A", (9, 8), "Magic Missile", 75),
    "ghost": (40, 0.9, 14, 20, "ghost", "#D9D6F5", (8, 10), None, 0),
}
BOSSES = ["Gravelmaw", "Rimecaller", "Mother Spore", "Cinder Colossus", "The Unmaker"]
BOSS_HP = [700, 900, 1200, 1600, 3500]


def _clamp(v, a, b):
    return max(a, min(b, v))


def claudeita_icon():
    pm = QPixmap(32, 32)
    pm.fill(QColor("#0B0712"))
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#7A5230"), 3, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(6, 27, 20, 12)
    g = QRadialGradient(22, 10, 9)
    g.setColorAt(0, QColor("#FFF3B0"))
    g.setColorAt(0.4, QColor("#FF8A1A"))
    g.setColorAt(1, QColor(255, 80, 0, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawEllipse(QPointF(22, 10), 9, 9)
    p.setBrush(QColor("#C9A65A"))
    for x, y in ((4, 30), (9, 31), (14, 30), (26, 29), (28, 31), (20, 31)):
        p.drawRect(x, y, 2, 2)
    p.end()
    return QIcon(pm)


# ---- things in the world ------------------------------------------------------------------------------------------
class Body:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = float(x), float(y), w, h      # x: centre, y: feet
        self.vx = self.vy = 0.0
        self.on_ground = False

    def box(self):
        return self.x - self.w / 2, self.y - self.h, self.x + self.w / 2, self.y

    def hits(self, other, pad=0):
        a, b = self.box(), other.box()
        return a[0] - pad < b[2] and a[2] + pad > b[0] and a[1] - pad < b[3] and a[3] + pad > b[1]


def blocked(world, x0, y0, x1, y1):
    for yy in range(int(y0), int(math.ceil(y1))):
        for xx in range(int(x0), int(math.ceil(x1))):
            if world.solid(xx, yy):
                return True
    return False


def move_body(b, world, step_up=2, through=False):
    """Move with the terrain in the way: step up small ledges, stop at walls, land on floors."""
    if through:
        b.x += b.vx
        b.y += b.vy
        return
    dx = b.vx
    n = int(math.ceil(abs(dx)))
    for i in range(n):
        s = math.copysign(min(1.0, abs(dx) - i), dx)
        x0, y0, x1, y1 = b.x - b.w / 2 + s, b.y - b.h, b.x + b.w / 2 + s, b.y
        if not blocked(world, x0, y0, x1, y1):
            b.x += s
            continue
        for up in range(1, step_up + 1):
            if not blocked(world, x0, y0 - up, x1, y1 - up):
                b.x += s
                b.y -= up
                break
        else:
            b.vx = 0
            break
    dy = b.vy
    b.on_ground = False
    n = int(math.ceil(abs(dy)))
    for i in range(n):
        s = math.copysign(min(1.0, abs(dy) - i), dy)
        x0, y0, x1, y1 = b.x - b.w / 2, b.y - b.h + s, b.x + b.w / 2, b.y + s
        if blocked(world, x0, y0, x1, y1):
            if s > 0:
                b.on_ground = True
            b.vy = 0
            break
        b.y += s
    if not b.on_ground and b.vy >= 0 and blocked(world, b.x - b.w / 2, b.y, b.x + b.w / 2, b.y + 1):
        b.on_ground = True


def in_material(world, b):
    """What the body is standing in (liquids, fire) - the worst of it."""
    found = set()
    for yy in range(int(b.y - b.h), int(b.y), 3):
        for xx in range(int(b.x - b.w / 2), int(b.x + b.w / 2) + 1, 2):
            found.add(world.get(xx, yy))
    for m in (wd.LAVA, wd.ACID, wd.FIRE, wd.WATER):
        if m in found:
            return m
    return wd.AIR


class Player(Body):
    def __init__(self, x, y):
        super().__init__(x, y, 5, 11)
        self.hp = self.hp_max = 100.0
        self.lev = 100.0
        self.wands = starter_wands()
        self.current = 0
        self.spells = ["Digging Bolt", "Spark Bolt"]
        self.gold = 0
        self.facing = 1
        self.hurt = 0
        self.kills = 0

    @property
    def wand(self):
        return self.wands[self.current] if self.wands else None


class Enemy(Body):
    def __init__(self, kind, x, y, biome):
        hp, speed, dmg, gold, move, colour, (w, h), spell, cd = ENEMIES[kind]
        super().__init__(x, y, w, h)
        k = 1 + biome * 0.6
        self.kind, self.hp, self.hp_max = kind, hp * k, hp * k
        self.speed, self.dmg, self.gold, self.move = speed, dmg * k, int(gold * (1 + biome)), move
        self.colour, self.spell, self.cd = colour, spell, cd
        self.timer = random.randint(0, max(1, cd))
        self.t = random.random() * 10
        self.awake = False
        self.facing = -1
        self.boss = False
        self.biome = biome


class Boss(Enemy):
    def __init__(self, index, x, y):
        Enemy.__init__(self, "ghost", x, y, index)
        self.kind = BOSSES[index]
        self.index = index
        self.boss = True
        self.hp = self.hp_max = float(BOSS_HP[index])
        self.dmg = 18 + index * 6
        self.gold = 200 * (index + 1)
        self.w, self.h = [(12, 12), (16, 16), (26, 22), (20, 28), (22, 22)][index]
        self.colour = ["#C07A6A", "#BDEBFF", "#B56FD6", "#E2481F", "#F2EEFF"][index]
        self.segments = [(x, y)] * 14 if index == 0 else []
        self.phase = 1
        self.awake = True


class Shot:
    """A spell in flight (or an enemy's)."""

    def __init__(self, name, mods, x, y, angle, owner, dmg_scale=1.0):
        s = dict(SPELLS[name])
        self.name, self.owner = name, owner
        speed = s["speed"]
        dmg = s["dmg"] * dmg_scale
        self.bounce = s.get("bounce", 0)
        self.boom = s.get("boom", 0)
        self.pierce = s.get("pierce", False)
        self.homing = False
        self.trail = False
        for m in mods or []:
            ms = SPELLS[m]
            dmg = dmg * ms.get("dmg_x", 1.0) + ms.get("add_dmg", 0)
            speed *= ms.get("speed_x", 1.0)
            self.bounce += ms.get("add_bounce", 0)
            self.boom = max(self.boom, ms.get("add_boom", 0)) + (2 if self.boom and ms.get("add_boom") else 0)
            self.pierce = self.pierce or ms.get("pierce", False)
            self.homing = self.homing or ms.get("homing", False)
            self.trail = self.trail or ms.get("trail", False)
        self.dmg = dmg
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.life = s["life"]
        self.gravity = s.get("gravity", 0.0)
        self.colour = QColor(s.get("colour", "#FFFFFF"))
        self.size = s.get("size", 1.5)
        self.dig, self.drill = s.get("dig", 0), s.get("drill", False)
        self.fire, self.splash, self.freeze, self.fuse = s.get("fire"), s.get("splash"), s.get("freeze"), s.get("fuse")
        self.lightning = s.get("lightning", False)
        self.hit = set()
        self.dead = False


class Pickup(Body):
    def __init__(self, kind, x, y, value=None, price=0):
        super().__init__(x, y, 6 if kind in ("wand", "spell", "heart") else 3, 6 if kind != "gold" else 3)
        self.kind, self.value, self.price = kind, value, price
        self.t = random.random() * 6


# ---- the game -----------------------------------------------------------------------------------------------------
class Game:
    def __init__(self, seed=None):
        self.world = wd.World(seed)
        self.world.make_rows(wd.SURFACE + 420)
        self.player = Player(wd.W // 2 - 40, wd.SURFACE - 6)
        self.enemies, self.shots, self.pickups, self.particles, self.texts, self.bolts = [], [], [], [], [], []
        self._spawned = 0
        self._itemised = 0
        self.boss = None
        self.bosses_down = set()
        self.boss_started = set()
        self.biome_seen = -1
        self.banner = ("", 0)
        self.shake = 0.0
        self.tick_n = 0
        self.started = time.time()
        self.over = None                           # None, "dead" or "won"
        self.message = ""
        self.cam = [self.player.x, self.player.y]
        self._populate()

    # ---- the world filling in ----
    def _populate(self):
        w = self.world
        for kind, x, y, b in w.spawns[self._spawned:]:
            self.enemies.append(Enemy(kind, x, y, b))
        self._spawned = len(w.spawns)
        for item in w.items[self._itemised:]:
            kind, x, y = item[0], item[1], item[2]
            b = item[3] if len(item) > 3 else wd.biome_at(y)
            if kind == "wand":
                self.pickups.append(Pickup("wand", x, y, random_wand(b)))
            elif kind == "spell":
                self.pickups.append(Pickup("spell", x, y, random_spell(b)))
            elif kind == "heart":
                self.pickups.append(Pickup("heart", x, y))
            elif kind == "fountain":
                self.pickups.append(Pickup("fountain", x, y))
            elif kind == "shop_wand":
                self.pickups.append(Pickup("wand", x, y, random_wand(b + 1), price=120 + b * 160))
            elif kind == "shop_spell":
                self.pickups.append(Pickup("spell", x, y, random_spell(b + 1), price=50 + b * 70))
        self._itemised = len(w.items)

    # ---- stepping ----
    def step(self, keys, aim, firing):
        if self.over:
            return
        self.tick_n += 1
        p, w = self.player, self.world
        need = int(self.cam[1]) + 320
        if w.made < need:                          # (a few rows a frame: falling is never faster than this)
            w.make_rows(min(need, w.made + (8 if w.made > need - 200 else 4)))
            self._populate()
        self._player(keys, aim, firing)
        for e in list(self.enemies):
            self._enemy(e)
        for s in list(self.shots):
            self._shot(s)
        for k in list(self.pickups):
            self._pickup(k)
        w.step(1800)
        for prt in list(self.particles):
            prt[0] += prt[2]
            prt[1] += prt[3]
            prt[3] += 0.12 if prt[6] else 0
            prt[4] -= 1
            if prt[4] <= 0:
                self.particles.remove(prt)
        for t in list(self.texts):
            t[1] -= 0.4
            t[3] -= 1
            if t[3] <= 0:
                self.texts.remove(t)
        self.bolts = [(a, b, life - 1) for a, b, life in self.bolts if life > 1]
        self.shake *= 0.85
        b = wd.biome_at(int(p.y))
        if b != self.biome_seen and p.y > wd.SURFACE:
            self.biome_seen = b
            self.banner = (wd.BIOMES[b]["name"], 120)
        if self.banner[1]:
            self.banner = (self.banner[0], self.banner[1] - 1)
        self._boss_check()
        self.cam[0] += (p.x - self.cam[0]) * 0.15
        self.cam[1] += (p.y - 20 - self.cam[1]) * 0.15

    def _player(self, keys, aim, firing):
        p, w = self.player, self.world
        accel = 0.35 if p.on_ground else 0.22
        want = (1 if "right" in keys else 0) - (1 if "left" in keys else 0)
        p.vx += (want * 1.4 - p.vx) * accel
        medium = in_material(w, p)
        if "jump" in keys:
            if p.on_ground:
                p.vy = -3.0
            elif p.lev > 0:
                p.vy = max(-2.2, p.vy - 0.34)
                p.lev -= 1.2
        if p.on_ground:
            p.lev = min(100.0, p.lev + 3)
        p.vy = min(4.0, p.vy + GRAV * (0.4 if medium == wd.WATER else 1.0))
        if medium == wd.WATER:
            p.vx *= 0.9
            p.vy *= 0.9
        move_body(p, w)
        if aim is not None:
            p.facing = 1 if aim[0] >= p.x else -1
        if medium == wd.LAVA:
            self.hurt_player(1.6, quiet=True)
        elif medium == wd.ACID:
            self.hurt_player(0.8, quiet=True)
        elif medium == wd.FIRE:
            self.hurt_player(0.5, quiet=True)
        if p.hurt:
            p.hurt -= 1
        for wand in p.wands:
            wand.tick(TICK)
        if firing and p.wand is not None and aim is not None:
            hx, hy = p.x, p.y - p.h * 0.6
            ang = math.atan2(aim[1] - hy, aim[0] - hx)
            for name, mods, spread in p.wand.cast():
                a = ang + math.radians(random.uniform(-spread, spread))
                self._launch(name, mods, hx + math.cos(ang) * 4, hy + math.sin(ang) * 4, a, "player")

    def hurt_player(self, dmg, quiet=False):
        p = self.player
        if p.hurt and not quiet:
            return
        p.hp -= dmg
        if not quiet:
            p.hurt = 18
            self.shake = max(self.shake, 3)
            self.texts.append([p.x, p.y - p.h - 2, f"-{dmg:.0f}", 30, "#FF5A5A"])
        if p.hp <= 0:
            p.hp = 0
            self.over = "dead"
            self._record()

    def _launch(self, name, mods, x, y, angle, owner, scale=1.0):
        s = Shot(name, mods, x, y, angle, owner, scale)
        if s.lightning:
            self._lightning(s)
            return
        self.shots.append(s)

    def _targets(self, owner):
        return [e for e in self.enemies if e.awake] if owner == "player" else [self.player]

    def _shot(self, s):
        w = self.world
        s.life -= 1
        if s.life <= 0:
            if s.fuse or s.boom:
                self._explode(s.x, s.y, s.boom or 8, s.dmg, s.fire, s.owner)
            self.shots.remove(s)
            return
        if s.homing:
            near = min(self._targets(s.owner), key=lambda e: (e.x - s.x) ** 2 + (e.y - e.h / 2 - s.y) ** 2,
                       default=None)
            if near is not None and abs(near.x - s.x) < 120 and abs(near.y - s.y) < 120:
                sp = math.hypot(s.vx, s.vy) or 1
                ang = math.atan2(near.y - near.h / 2 - s.y, near.x - s.x)
                s.vx += (math.cos(ang) * sp - s.vx) * 0.15
                s.vy += (math.sin(ang) * sp - s.vy) * 0.15
        s.vy += s.gravity
        steps = max(1, int(math.ceil(max(abs(s.vx), abs(s.vy)))))
        sx, sy = s.vx / steps, s.vy / steps
        for i in range(steps):
            nx, ny = s.x + sx, s.y + sy
            if w.solid(nx, ny):
                if s.dig:
                    gold = w.carve(nx, ny, s.dig, soft_only=not s.drill, hard=s.name == "Black Hole")
                    self._gold_from(gold, nx, ny)
                    if w.solid(nx, ny):
                        s.life -= 4
                        if s.life <= 0 or not s.drill:
                            self._impact(s)
                            return
                elif s.bounce > 0:
                    s.bounce -= 1
                    if w.solid(nx, s.y):
                        s.vx, sx = -s.vx, -sx
                    if w.solid(s.x, ny):
                        s.vy, sy = -s.vy, -sy
                    continue
                else:
                    self._impact(s)
                    return
            s.x, s.y = nx, ny
            if s.trail and i % 2 == 0 and w.get(int(s.x), int(s.y)) == wd.AIR:
                w.set(int(s.x), int(s.y), wd.FIRE)
            for t in self._targets(s.owner):
                if t in s.hit:
                    continue
                x0, y0, x1, y1 = t.box()
                if x0 - s.size < s.x < x1 + s.size and y0 - s.size < s.y < y1 + s.size:
                    if s.owner == "player":
                        self.damage(t, s.dmg)
                    else:
                        self.hurt_player(s.dmg)
                    s.hit.add(t)
                    if not s.pierce:
                        self._impact(s)
                        return
        if not (0 <= s.y < wd.H):
            self.shots.remove(s)

    def _impact(self, s):
        if s in self.shots:
            self.shots.remove(s)
        w = self.world
        if s.boom:
            self._explode(s.x, s.y, s.boom, s.dmg, s.fire, s.owner)
        if s.splash:
            w.splash(s.x - s.vx, s.y - s.vy, wd.ACID if s.splash == "acid" else wd.WATER, 3)
        if s.freeze:
            w.freeze(s.x, s.y, 6)
        if s.fire and not s.boom:
            w.splash(s.x - s.vx, s.y - s.vy, wd.FIRE, 2)
        for _ in range(5):
            self.particles.append([s.x, s.y, random.uniform(-1, 1), random.uniform(-1.5, 0.5), 10,
                                   s.colour.name(), True])

    def _explode(self, x, y, r, dmg, fire, owner):
        w = self.world
        gold = w.carve(x, y, int(r), fire=bool(fire))
        self._gold_from(gold, x, y)
        self.shake = max(self.shake, min(8, r / 2))
        for _ in range(int(r * 3)):
            a = random.uniform(0, math.tau)
            sp = random.uniform(0.5, 2.5)
            self.particles.append([x, y, math.cos(a) * sp, math.sin(a) * sp - 1, random.randint(10, 25),
                                   random.choice(("#FFE36E", "#FF8A1A", "#FF4A1A", "#9A8A7A")), True])
        reach = r * 1.4
        for t in ([e for e in self.enemies if e.awake] + [self.player]):
            d = math.hypot(t.x - x, t.y - t.h / 2 - y)
            if d < reach:
                hurt = dmg * (1 - d / reach * 0.6)
                if t is self.player:
                    if owner != "player" or d < r * 0.8:      # (your own blasts hurt you too, up close)
                        self.hurt_player(hurt * (0.5 if owner == "player" else 1.0))
                elif owner == "player":
                    self.damage(t, hurt)

    def _lightning(self, s):
        here = (s.x, s.y)
        done = set()
        for _ in range(4):
            near = min((e for e in self.enemies if e.awake and e not in done),
                       key=lambda e: (e.x - here[0]) ** 2 + (e.y - e.h / 2 - here[1]) ** 2, default=None)
            if near is None or math.hypot(near.x - here[0], near.y - near.h / 2 - here[1]) > 110:
                break
            self.bolts.append((here, (near.x, near.y - near.h / 2), 6))
            self.damage(near, s.dmg)
            done.add(near)
            here = (near.x, near.y - near.h / 2)
        if not done:                               # nothing to strike: a crackle in the air
            self.bolts.append((here, (here[0] + math.cos(math.atan2(s.vy, s.vx)) * 40,
                                      here[1] + math.sin(math.atan2(s.vy, s.vx)) * 40), 4))

    def _gold_from(self, cells, x, y):
        b = wd.biome_at(int(y))
        for _ in range(cells // 4 + (1 if cells % 4 and random.random() < 0.5 else 0)):
            g = Pickup("gold", x + random.uniform(-4, 4), y, 5 * (b + 1))
            g.vy = -1.5
            self.pickups.append(g)

    def damage(self, e, dmg):
        e.hp -= dmg
        e.awake = True
        self.texts.append([e.x, e.y - e.h - 2, f"{dmg:.0f}", 24, "#FFE36E"])
        if e.hp <= 0 and e in self.enemies:
            self.enemies.remove(e)
            self.player.kills += 1
            for _ in range(max(1, e.gold // 10)):
                g = Pickup("gold", e.x + random.uniform(-3, 3), e.y - 3, max(1, e.gold // max(1, e.gold // 10)))
                g.vy = -2
                self.pickups.append(g)
            for _ in range(14):
                self.particles.append([e.x, e.y - e.h / 2, random.uniform(-1.5, 1.5), random.uniform(-2, 0.5),
                                       random.randint(12, 24), e.colour, True])
            if e.boss:
                self._boss_down(e)

    # ---- enemies ----
    def _enemy(self, e):
        p, w = self.player, self.world
        dx, dy = p.x - e.x, (p.y - p.h / 2) - (e.y - e.h / 2)
        dist = math.hypot(dx, dy)
        if not e.awake:
            if dist < 170:
                e.awake = True
            else:
                return
        if dist > 360 and not e.boss:
            e.awake = False
            return
        e.t += TICK
        if e.boss:
            self._boss_ai(e, dx, dy, dist)
        elif e.move == "hop":
            if e.on_ground:
                e.vx *= 0.7
                if random.random() < 0.04:
                    e.vy = -2.6
                    e.vx = math.copysign(e.speed * 2, dx) if dist < 150 else random.uniform(-1, 1)
            e.vy = min(4, e.vy + GRAV)
            move_body(e, w)
        elif e.move == "walk":
            if dist < 160:
                e.vx = math.copysign(e.speed, dx) if abs(dx) > 30 or not e.spell else e.vx * 0.8
            else:
                e.vx = e.speed * (1 if math.sin(e.t * 0.7) > 0 else -1)
            if e.on_ground and abs(e.vx) > 0.1 and blocked(w, e.x + math.copysign(e.w, e.vx), e.y - e.h, e.x +
                                                              math.copysign(e.w, e.vx) + 1, e.y - 3):
                e.vy = -2.8
            e.vy = min(4, e.vy + GRAV)
            move_body(e, w)
        elif e.move in ("fly", "ghost"):
            tx, ty = (dx, dy - 10) if dist < 200 else (math.sin(e.t) * 20, math.cos(e.t * 0.7) * 10)
            n = math.hypot(tx, ty) or 1
            keep = 40 if e.spell else 0                 # (shooters keep their distance)
            sign = -1 if dist < keep else 1
            e.vx += (sign * tx / n * e.speed - e.vx) * 0.08
            e.vy += (sign * ty / n * e.speed + math.sin(e.t * 4) * 0.3 - e.vy) * 0.08
            move_body(e, w, step_up=0, through=e.move == "ghost")
        elif e.move == "dig":
            n = dist or 1
            e.vx += (dx / n * e.speed - e.vx) * 0.05
            e.vy += (dy / n * e.speed - e.vy) * 0.05
            e.x += e.vx
            e.y += e.vy
            if random.random() < 0.5:
                w.carve(e.x, e.y - e.h / 2, 4, hard=False)
        if e.vx:
            e.facing = 1 if e.vx > 0 else -1
        if e.spell and dist < 170:
            e.timer -= 1
            if e.timer <= 0 and self._sees(e.x, e.y - e.h / 2, p.x, p.y - p.h / 2):
                e.timer = e.cd + random.randint(0, 30)
                ang = math.atan2(dy, dx)
                self._launch(e.spell, [], e.x, e.y - e.h / 2, ang, "enemy", 0.6 + e.biome * 0.25)
        if e.hits(p, 1):
            self.hurt_player(e.dmg)
        if e.y > wd.H or e.y < 0:
            self.enemies.remove(e)

    def _sees(self, x0, y0, x1, y1):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) / 3) + 1
        for i in range(1, n):
            if self.world.solid(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n):
                return False
        return True

    # ---- bosses ----
    def _boss_check(self):
        p = self.player
        for b in range(len(wd.BIOMES)):
            if b in self.boss_started:
                continue
            x0, y0, x1, y1 = wd.arena_rect(b)
            if x0 < p.x < x1 and y0 + 10 < p.y < y1 and self.world.made > y1:
                self.boss_started.add(b)
                boss = Boss(b, (x0 + x1) / 2, y0 + 40 if b != 2 else y1 - 2)
                self.enemies.append(boss)
                self.boss = boss
                self.banner = (f"{BOSSES[b]} awakens" if b < 4 else "THE UNMAKER", 150)

    def _boss_down(self, e):
        b = e.index
        self.bosses_down.add(b)
        self.boss = None
        self.shake = 12
        if b == len(BOSSES) - 1:
            self.over = "won"
            self._record()
            return
        self.world.open_gate(b)
        self.banner = (f"{BOSSES[b]} has fallen", 150)
        self.pickups.append(Pickup("wand", e.x, e.y - 4, random_wand(b + 1)))
        self.pickups.append(Pickup("heart", e.x + 10, e.y - 4))

    def _boss_ai(self, e, dx, dy, dist):
        w, p = self.world, self.player
        i = e.index
        frac = e.hp / e.hp_max
        e.phase = 1 if frac > 0.66 else 2 if frac > 0.33 else 3
        k = self.tick_n
        x0, y0, x1, y1 = wd.arena_rect(i)
        if i == 0:                                  # Gravelmaw: a great worm through the rock
            sp = 1.6 + (3 - e.phase) * -0.3 + 0.4 * e.phase
            tx, ty = p.x + math.sin(e.t * 1.3) * 40, p.y - 6 + math.cos(e.t * 0.9) * 30
            ang = math.atan2(ty - e.y, tx - e.x)
            e.vx += (math.cos(ang) * sp - e.vx) * 0.04
            e.vy += (math.sin(ang) * sp - e.vy) * 0.04
            e.x = _clamp(e.x + e.vx, x0 + 8, x1 - 8)
            e.y = _clamp(e.y + e.vy, y0 + 8, y1)
            e.segments = [(e.x, e.y)] + e.segments[:-1]
            if k % 3 == 0:
                w.carve(e.x, e.y - 6, 7, hard=False)
            for sx, sy in e.segments[3::3]:
                if abs(sx - p.x) < 7 and abs(sy - 6 - (p.y - p.h / 2)) < 9:
                    self.hurt_player(e.dmg * 0.6)
        elif i == 1:                                # Rimecaller: rings of ice, and bats
            e.x += ((p.x + math.sin(e.t * 0.6) * 60) - e.x) * 0.02
            e.y += ((y0 + 30 + math.sin(e.t) * 12) - e.y) * 0.03
            if k % max(30, 75 - e.phase * 15) == 0:
                for a in range(0, 360, 30 if e.phase < 3 else 20):
                    self._launch("Ice Shard", [], e.x, e.y - 8, math.radians(a + k), "enemy", 1.0)
            if k % 240 == 0:
                for _ in range(e.phase):
                    self.enemies.append(Enemy("bat", e.x, e.y, 1))
        elif i == 2:                                # Mother Spore: acid arcs and spores, rooted to the floor
            if k % max(25, 70 - e.phase * 15) == 0:
                for _ in range(1 + e.phase):
                    ang = math.atan2(dy, dx) + random.uniform(-0.4, 0.4) - 0.5
                    self._launch("Acid Ball", [], e.x, e.y - e.h, ang, "enemy", 1.0)
            if k % 200 == 0:
                for _ in range(e.phase):
                    self.enemies.append(Enemy(random.choice(("spore", "slime")), e.x + random.uniform(-20, 20),
                                              e.y - 4, 2))
        elif i == 3:                                # Cinder Colossus: stomps, leaps and fire
            e.vy = min(4, e.vy + GRAV)
            if e.on_ground:
                e.vx = math.copysign(0.6 + e.phase * 0.2, dx)
                if k % max(50, 120 - e.phase * 20) == 0:
                    e.vy = -4.2
                    e.vx = math.copysign(2.2, dx)
                    e.slam = True
            move_body(e, w, step_up=4)
            if e.on_ground and getattr(e, "slam", False):
                e.slam = False
                self._explode(e.x, e.y, 8, 0, False, "enemy")
                if abs(p.x - e.x) < 60 and p.on_ground:
                    self.hurt_player(e.dmg)
                for a in (-30, -60, -120, -150):
                    self._launch("Fireball", [], e.x, e.y - e.h, math.radians(a), "enemy", 0.8)
        else:                                       # The Unmaker: spirals, a sweeping beam, and the void
            cx, cy = (x0 + x1) / 2, y0 + 45
            if k % 180 == 0 and e.phase >= 2:       # it blinks to a new place
                e.x = random.uniform(x0 + 40, x1 - 40)
                e.y = random.uniform(y0 + 25, y0 + 70)
                for _ in range(30):
                    self.particles.append([e.x, e.y - 11, random.uniform(-2, 2), random.uniform(-2, 2), 20,
                                           "#F2EEFF", False])
            else:
                e.x += ((cx + math.sin(e.t * 0.5) * 120) - e.x) * 0.01
                e.y += ((cy + math.sin(e.t * 0.8) * 20) - e.y) * 0.01
            if k % (6 if e.phase < 3 else 4) == 0:
                a = e.t * (2.0 + e.phase) * 1.3
                arms = 2 + e.phase
                for j in range(arms):
                    self._launch("Spark Bolt", [], e.x, e.y - 11, a + j * math.tau / arms, "enemy", 2.0)
            if e.phase >= 2 and k % 150 < 40:      # the beam
                ang = math.atan2(dy, dx) + math.sin(k * 0.08) * 0.6
                end = (e.x + math.cos(ang) * 260, e.y - 11 + math.sin(ang) * 260)
                self.bolts.append(((e.x, e.y - 11), end, 2))
                px, py = p.x - e.x, p.y - p.h / 2 - (e.y - 11)
                along = px * math.cos(ang) + py * math.sin(ang)
                off = abs(-px * math.sin(ang) + py * math.cos(ang))
                if 0 < along < 260 and off < 5:
                    self.hurt_player(1.2, quiet=True)
            if e.phase == 3:                        # the void pulls at you
                p.vx += _clamp(-dx / 400, -0.15, 0.15)
                if k % 120 == 0:
                    self.enemies.append(Enemy("ghost", e.x, e.y, 4))
        if e.hits(p, 2):
            self.hurt_player(e.dmg)

    # ---- pickups ----
    def _pickup(self, k):
        w, p = self.world, self.player
        k.t += TICK
        if k.kind not in ("fountain",) and not k.price:
            k.vy = min(3, k.vy + GRAV)
            move_body(k, w, step_up=0)
        if k.kind == "gold" and k.hits(p, 3):
            p.gold += k.value
            self.texts.append([p.x, p.y - p.h - 4, f"+{k.value}", 20, "#F2C230"])
            self.pickups.remove(k)
        elif k.kind == "heart" and k.hits(p, 2):
            p.hp_max += 25
            p.hp = p.hp_max
            self.banner = ("Max health +25", 80)
            self.pickups.remove(k)
        elif k.kind == "fountain" and abs(k.x - p.x) < 10 and abs(k.y - p.y) < 14 and p.hp < p.hp_max:
            p.hp = p.hp_max
            for wand in p.wands:
                wand.mana = wand.mana_max
            self.banner = ("The fountain restores you", 70)
        if k.y > wd.H:
            self.pickups.remove(k)

    def nearest_item(self):
        p = self.player
        near = [k for k in self.pickups if k.kind in ("wand", "spell") and abs(k.x - p.x) < 9 and abs(k.y - p.y) < 12]
        return min(near, key=lambda k: abs(k.x - p.x), default=None)

    def interact(self):
        k = self.nearest_item()
        p = self.player
        if k is None:
            return
        if k.price and p.gold < k.price:
            self.banner = (f"Not enough gold ({k.price} needed)", 70)
            return
        if k.kind == "wand":
            if len(p.wands) < 4:
                p.wands.append(k.value)
                self.pickups.remove(k)
            else:                                   # swap with the wand in hand
                old = p.wands[p.current]
                p.wands[p.current] = k.value
                k.value, k.price = old, 0
            self.banner = (f"Picked up {p.wands[-1].name if len(p.wands) < 4 else p.wand.name}", 70)
        else:
            if len(p.spells) >= 16:
                self.banner = ("Your spell bag is full (Tab to sort it)", 70)
                return
            p.spells.append(k.value)
            self.pickups.remove(k)
            self.banner = (f"Picked up {k.value}", 70)
        if k.price:
            p.gold -= k.price
            k.price = 0

    # ---- a record of the run ----
    def depth(self):
        return max(0, int((self.player.y - wd.SURFACE) / 2))

    def _record(self):
        try:
            path = host.saves(TITLE) / "records.json"
            rec = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (OSError, ValueError):
            rec = {}
        rec["runs"] = rec.get("runs", 0) + 1
        rec["wins"] = rec.get("wins", 0) + (1 if self.over == "won" else 0)
        rec["deepest"] = max(rec.get("deepest", 0), self.depth())
        rec["kills"] = rec.get("kills", 0) + self.player.kills
        try:
            path.write_text(json.dumps(rec), encoding="utf-8")
        except OSError:
            pass
        self.records = rec


# ---- drawing --------------------------------------------------------------------------------------------------------
def spell_icon(name, size=22):
    s = SPELLS[name]
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    border = {"proj": "#4A90E2", "mod": "#4FC36A", "multi": "#F0A030"}[s["kind"]]
    p.setPen(QPen(QColor(border), 1.5))
    p.setBrush(QColor("#1A1420"))
    p.drawRoundedRect(QRectF(1, 1, size - 2, size - 2), 3, 3)
    col = QColor(s.get("colour", border))
    if s["kind"] == "proj":
        g = QRadialGradient(size / 2, size / 2, size * 0.35)
        g.setColorAt(0, col.lighter(150))
        g.setColorAt(1, col)
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(QPointF(size / 2, size / 2), size * 0.28, size * 0.28)
    p.setPen(QColor("#FFFFFF"))
    f = QFont("Tahoma")
    f.setPixelSize(int(size * 0.36))
    f.setBold(True)
    p.setFont(f)
    abbrev = "".join(w[0] for w in name.split())[:2].upper() if s["kind"] != "proj" else ""
    p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, abbrev)
    p.end()
    return pm


class Claudeita(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(640, 420)
        self.keys = set()
        self.mouse = None
        self.firing = False
        self.paused = False
        self.inventory = False
        self.pick = None                            # what's picked up in the wand editor
        self.hover = None
        self.icons = {}
        self.game = Game()
        self.setAttribute(Qt.WA_OpaquePaintEvent)    # (it paints every pixel: nothing behind it needs redrawing)
        self.acc = 0.0
        self.last = time.perf_counter()
        self.perf = {"fps": 0, "sps": 0, "frames": 0, "steps": 0, "since": self.last, "step": 0.0, "paint": 0.0}
        self.show_perf = False
        self.light_cache = {}
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)     # (Windows' default timers are coarse: 33 ms becomes 47)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def _icon(self, name, size=22):
        k = (name, size)
        if k not in self.icons:
            self.icons[k] = spell_icon(name, size)
        return self.icons[k]

    # ---- input ----
    KEYMAP = {Qt.Key_A: "left", Qt.Key_Left: "left", Qt.Key_D: "right", Qt.Key_Right: "right", Qt.Key_W: "jump",
              Qt.Key_Space: "jump", Qt.Key_Up: "jump"}

    def keyPressEvent(self, e):
        k = e.key()
        g = self.game
        if k in self.KEYMAP:
            self.keys.add(self.KEYMAP[k])
        elif Qt.Key_1 <= k <= Qt.Key_4 and k - Qt.Key_1 < len(g.player.wands):
            g.player.current = k - Qt.Key_1
        elif k == Qt.Key_E:
            g.interact()
        elif k == Qt.Key_Tab:
            self.inventory = not self.inventory
            self.pick = None
        elif k == Qt.Key_Escape:
            if self.inventory:
                self.inventory = False
            else:
                self.paused = not self.paused
        elif k == Qt.Key_F3:
            self.show_perf = not self.show_perf
        elif k == Qt.Key_R and g.over:
            self.game = Game()
            self.keys.clear()
        else:
            super().keyPressEvent(e)

    def keyReleaseEvent(self, e):
        if e.key() in self.KEYMAP:
            self.keys.discard(self.KEYMAP[e.key()])

    def focusNextPrevChild(self, nxt):
        return False                                # (Tab belongs to the game)

    def mousePressEvent(self, e):
        self.setFocus()
        if self.inventory:
            self._inventory_click(e.position(), e.button())
            return
        if self.game.over and e.button() == Qt.LeftButton:
            self.game = Game()
            return
        if e.button() == Qt.LeftButton:
            self.firing = True

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.firing = False

    def mouseMoveEvent(self, e):
        self.mouse = e.position()

    def wheelEvent(self, e):
        p = self.game.player
        if p.wands:
            p.current = (p.current + (-1 if e.angleDelta().y() > 0 else 1)) % len(p.wands)

    # ---- running ----
    def _scale(self):
        return self.width() / VIEW_W

    def _view_origin(self):
        g = self.game
        s = self._scale()
        vw, vh = VIEW_W, self.height() / s
        cx = _clamp(g.cam[0], vw / 2, wd.W - vw / 2)
        cy = _clamp(g.cam[1], vh / 2, wd.H - vh / 2)
        jx = random.uniform(-g.shake, g.shake) if g.shake > 0.3 else 0
        jy = random.uniform(-g.shake, g.shake) if g.shake > 0.3 else 0
        return cx - vw / 2 + jx * 0.3, cy - vh / 2 + jy * 0.3

    def _aim(self):
        if self.mouse is None:
            return None
        ox, oy = self._view_origin()
        s = self._scale()
        return ox + self.mouse.x() / s, oy + self.mouse.y() / s

    def _tick(self):
        """Real time decides how many steps the game takes (30 a second), however often the timer actually fires:
        a late frame never slows the game down, it just takes two steps."""
        now = time.perf_counter()
        dt = min(0.25, now - self.last)
        self.last = now
        steps = 0
        if not self.paused and not self.inventory and self.isVisible():
            self.acc += dt
            t = time.perf_counter()
            while self.acc >= TICK and steps < 4:
                self.game.step(self.keys, self._aim(), self.firing)
                self.acc -= TICK
                steps += 1
            if steps == 4:
                self.acc = 0.0                      # (too far behind: let it go rather than spiral)
            if steps:
                self.perf["step"] = (time.perf_counter() - t) / steps * 1000
        else:
            self.acc = 0.0
        self.perf["steps"] += steps
        if steps or self.paused or self.inventory or self.game.over:
            self.update()
        if now - self.perf["since"] >= 1.0:
            self.perf.update(fps=self.perf["frames"], sps=self.perf["steps"], frames=0, steps=0, since=now)

    # ---- drawing ----
    def paintEvent(self, event):
        t0 = time.perf_counter()
        self._paint()
        self.perf["frames"] += 1
        self.perf["paint"] = (time.perf_counter() - t0) * 1000

    def _paint(self):
        g = self.game
        p = QPainter(self)
        s = self._scale()
        ox, oy = self._view_origin()
        self._origin = (ox, oy)                     # (this frame's camera, shake and all)
        vh = self.height() / s
        p.fillRect(self.rect(), QColor("#000000"))
        p.drawImage(QRectF(0, 0, self.width(), self.height()), g.world.image, QRectF(ox, oy, VIEW_W, vh))
        p.save()
        p.scale(s, s)
        p.translate(-ox, -oy)
        p.setRenderHint(QPainter.Antialiasing)
        for k in g.pickups:
            self._draw_pickup(p, k)
        for e in g.enemies:
            if ox - 30 < e.x < ox + VIEW_W + 30 and oy - 40 < e.y < oy + vh + 40:
                self._draw_enemy(p, e)
        self._draw_player(p)
        for sh in g.shots:
            glow = QRadialGradient(sh.x, sh.y, sh.size * 2.2)
            c = QColor(sh.colour)
            glow.setColorAt(0, c.lighter(160))
            c2 = QColor(c)
            c2.setAlpha(0)
            glow.setColorAt(1, c2)
            p.setPen(Qt.NoPen)
            p.setBrush(glow)
            p.drawEllipse(QPointF(sh.x, sh.y), sh.size * 2.2, sh.size * 2.2)
            p.setBrush(c)
            p.drawEllipse(QPointF(sh.x, sh.y), sh.size * 0.7, sh.size * 0.7)
        for (x0, y0), (x1, y1), life in g.bolts:
            p.setPen(QPen(QColor(230, 240, 255, 220), 1.2))
            pts = [QPointF(x0, y0)]
            for i in range(1, 6):
                t = i / 6
                pts.append(QPointF(x0 + (x1 - x0) * t + random.uniform(-3, 3), y0 + (y1 - y0) * t +
                                   random.uniform(-3, 3)))
            pts.append(QPointF(x1, y1))
            for a, b in zip(pts, pts[1:]):
                p.drawLine(a, b)
        p.setPen(Qt.NoPen)
        for x, y, _vx, _vy, life, col, _g in g.particles:
            c = QColor(col)
            c.setAlpha(min(255, life * 14))
            p.fillRect(QRectF(x, y, 1, 1), c)
        f = QFont("Tahoma")
        f.setPixelSize(5)
        f.setBold(True)
        p.setFont(f)
        for x, y, text, life, col in g.texts:
            p.setPen(QColor(col))
            p.drawText(QPointF(x - 4, y), text)
        p.restore()
        self._draw_light(p)
        self._draw_hud(p)
        if self.inventory:
            self._draw_inventory(p)
        elif g.over:
            self._draw_over(p)
        elif self.paused:
            self._center_text(p, "PAUSED", "Esc to carry on")
        if self.show_perf:
            f = QFont("Consolas")
            f.setPixelSize(12)
            p.setFont(f)
            pf = self.perf
            text = (f"{pf['fps']} frames/s   {pf['sps']} steps/s (30 is full speed)   step {pf['step']:.1f} ms   "
                    f"paint {pf['paint']:.1f} ms   moving cells {len(g.world.active)}   "
                    f"awake {sum(1 for e in g.enemies if e.awake)}   shots {len(g.shots)}")
            p.fillRect(QRectF(0, self.height() - 74, self.width(), 18), QColor(0, 0, 0, 180))
            p.setPen(QColor("#9EF0A0"))
            p.drawText(QRectF(8, self.height() - 74, self.width() - 16, 18), Qt.AlignVCenter, text)

    def _draw_light(self, p):
        """The dark of the deep, lit around you: a picture made once per size and depth, moved with you."""
        g = self.game
        s = self._scale()
        ox, oy = getattr(self, "_origin", self._view_origin())
        px, py = (g.player.x - ox) * s, (g.player.y - g.player.h / 2 - oy) * s
        depth = round(_clamp((g.player.y - wd.SURFACE) / 600, 0, 1) * 10) / 10
        key = (self.width(), self.height(), depth)
        light = self.light_cache.get(key)
        if light is None:
            w, h = self.width(), self.height()
            light = QPixmap(w * 2, h * 2)
            light.fill(Qt.transparent)
            r = w * (0.55 - depth * 0.18)
            grad = QRadialGradient(w, h, r)
            grad.setColorAt(0, QColor(0, 0, 0, 0))
            grad.setColorAt(0.55, QColor(0, 0, 0, int(40 * depth)))
            grad.setColorAt(1, QColor(0, 0, 0, int(120 + 70 * depth)))
            q = QPainter(light)
            q.fillRect(light.rect(), grad)
            q.end()
            if len(self.light_cache) > 24:
                self.light_cache.clear()
            self.light_cache[key] = light
        p.drawPixmap(QPointF(px - self.width(), py - self.height()), light)

    def _draw_player(self, p):
        g = self.game
        pl = g.player
        if pl.hurt and (pl.hurt // 3) % 2:
            return
        x, y = pl.x, pl.y
        p.setPen(Qt.NoPen)
        robe = QPainterPath()
        robe.moveTo(x - 3, y)
        robe.lineTo(x + 3, y)
        robe.lineTo(x + 2, y - 7)
        robe.lineTo(x - 2, y - 7)
        robe.closeSubpath()
        p.setBrush(QColor("#D97757"))
        p.drawPath(robe)
        p.setBrush(QColor("#F2C9A0"))
        p.drawEllipse(QPointF(x, y - 8.5), 1.8, 1.8)
        hat = QPainterPath()
        hat.moveTo(x - 3, y - 9.5)
        hat.lineTo(x + 3, y - 9.5)
        hat.lineTo(x - pl.facing * 1.5, y - 14)
        hat.closeSubpath()
        p.setBrush(QColor("#4B2E83"))
        p.drawPath(hat)
        aim = self._aim()
        if aim and pl.wand:
            ang = math.atan2(aim[1] - (y - 6.6), aim[0] - x)
            ex, ey = x + math.cos(ang) * 6, y - 6.6 + math.sin(ang) * 6
            p.setPen(QPen(QColor(pl.wand.colour), 1.0))
            p.drawLine(QPointF(x, y - 6.6), QPointF(ex, ey))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#9EE6FF") if not pl.wand.recharging else QColor("#55606A"))
            p.drawEllipse(QPointF(ex, ey), 0.9, 0.9)

    def _draw_enemy(self, p, e):
        x, y = e.x, e.y
        col = QColor(e.colour)
        p.setPen(Qt.NoPen)
        if e.boss:
            self._draw_boss(p, e)
            return
        if e.move == "ghost":
            col.setAlpha(150)
        p.setBrush(col)
        if e.kind == "bat":
            flap = math.sin(e.t * 18) * 2
            p.drawEllipse(QPointF(x, y - 3), 2, 2)
            p.drawPolygon([QPointF(x - 1, y - 3), QPointF(x - 5, y - 4 - flap), QPointF(x - 2, y - 2)])
            p.drawPolygon([QPointF(x + 1, y - 3), QPointF(x + 5, y - 4 - flap), QPointF(x + 2, y - 2)])
        elif e.kind == "worm":
            for i in range(4):
                p.drawEllipse(QPointF(x - e.vx * i * 3, y - 3 - e.vy * i * 3), 3 - i * 0.4, 3 - i * 0.4)
        else:
            p.drawRoundedRect(QRectF(x - e.w / 2, y - e.h, e.w, e.h), 2, 2)
        p.setBrush(QColor("#FFFFFF") if e.kind != "ghost" else QColor("#3A2A5A"))
        ex = x + e.facing * e.w * 0.2
        p.drawEllipse(QPointF(ex, y - e.h * 0.7), 0.8, 0.8)
        if e.hp < e.hp_max:
            p.fillRect(QRectF(x - 4, y - e.h - 3, 8, 1), QColor(40, 0, 0, 200))
            p.fillRect(QRectF(x - 4, y - e.h - 3, 8 * max(0, e.hp) / e.hp_max, 1), QColor("#E53935"))

    def _draw_boss(self, p, e):
        x, y = e.x, e.y
        col = QColor(e.colour)
        i = e.index
        if i == 0:
            for j, (sx, sy) in enumerate(reversed(e.segments)):
                r = 4 + (j / len(e.segments)) * 4
                p.setBrush(col.darker(100 + (len(e.segments) - j) * 4))
                p.drawEllipse(QPointF(sx, sy - 6), r, r)
            p.setBrush(QColor("#FFE36E"))
            p.drawEllipse(QPointF(x + e.vx, y - 7), 1.5, 1.5)
        elif i == 1:
            g = QRadialGradient(x, y - 8, 14)
            g.setColorAt(0, QColor("#FFFFFF"))
            g.setColorAt(0.5, col)
            g.setColorAt(1, QColor(150, 200, 255, 0))
            p.setBrush(g)
            p.drawEllipse(QPointF(x, y - 8), 14, 14)
            p.setBrush(QColor("#2A4A6A"))
            p.drawEllipse(QPointF(x - 2, y - 9), 1.2, 1.6)
            p.drawEllipse(QPointF(x + 2, y - 9), 1.2, 1.6)
        elif i == 2:
            p.setBrush(QColor("#E9D7B8"))
            p.drawRect(QRectF(x - 4, y - 10, 8, 10))
            cap = QPainterPath()
            cap.moveTo(x - 14, y - 9)
            cap.quadTo(x, y - 30 - math.sin(e.t * 2) * 2, x + 14, y - 9)
            cap.closeSubpath()
            p.setBrush(col)
            p.drawPath(cap)
            p.setBrush(QColor("#F5E6FF"))
            for dx, dy in ((-7, -14), (2, -20), (8, -13), (-2, -12)):
                p.drawEllipse(QPointF(x + dx, y + dy), 1.6, 1.6)
        elif i == 3:
            p.setBrush(QColor("#2A1A16"))
            p.drawRoundedRect(QRectF(x - 10, y - 28, 20, 28), 3, 3)
            p.setBrush(col)
            for k in range(5):
                p.drawRect(QRectF(x - 8 + (k * 7) % 14, y - 26 + k * 5, 4, 2))
            p.setBrush(QColor("#FFE36E"))
            p.drawEllipse(QPointF(x - 3, y - 22), 1.5, 1.5)
            p.drawEllipse(QPointF(x + 3, y - 22), 1.5, 1.5)
        else:
            g = QRadialGradient(x, y - 11, 22)
            g.setColorAt(0, QColor("#FFFFFF"))
            g.setColorAt(0.3, QColor("#C9B8FF"))
            g.setColorAt(0.7, QColor(60, 20, 90, 200))
            g.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(g)
            p.drawEllipse(QPointF(x, y - 11), 22, 22)
            for j in range(3):                      # three eyes, watching
                a = e.t * 0.8 + j * math.tau / 3
                ex, ey = x + math.cos(a) * 6, y - 11 + math.sin(a) * 6
                p.setBrush(QColor("#FFFFFF"))
                p.drawEllipse(QPointF(ex, ey), 2.4, 2.4)
                p.setBrush(QColor("#1A0A2A"))
                pdx = _clamp(self.game.player.x - ex, -1, 1)
                p.drawEllipse(QPointF(ex + pdx, ey), 1.1, 1.1)

    def _draw_pickup(self, p, k):
        x, y = k.x, k.y
        bob = math.sin(k.t * 3) * 0.8
        p.setPen(Qt.NoPen)
        if k.kind == "gold":
            p.setBrush(QColor("#F2C230"))
            p.drawEllipse(QPointF(x, y - 1.5), 1.4, 1.4)
        elif k.kind == "heart":
            p.setBrush(QColor("#E53935"))
            p.drawEllipse(QPointF(x - 1.2, y - 4 + bob), 1.6, 1.6)
            p.drawEllipse(QPointF(x + 1.2, y - 4 + bob), 1.6, 1.6)
            p.drawPolygon([QPointF(x - 2.8, y - 3.6 + bob), QPointF(x + 2.8, y - 3.6 + bob), QPointF(x, y - 0.5 + bob)])
        elif k.kind == "fountain":
            p.setBrush(QColor("#6A6A7A"))
            p.drawRect(QRectF(x - 5, y - 4, 10, 4))
            p.setBrush(QColor(110, 190, 255, 200))
            p.drawEllipse(QPointF(x, y - 6 + bob), 2.5, 3)
        elif k.kind == "wand":
            p.setPen(QPen(QColor(k.value.colour), 1.2))
            p.drawLine(QPointF(x - 3, y - 1 + bob), QPointF(x + 3, y - 5 + bob))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#9EE6FF"))
            p.drawEllipse(QPointF(x + 3, y - 5 + bob), 1.0, 1.0)
        elif k.kind == "spell":
            s = SPELLS[k.value]
            p.setBrush(QColor({"proj": "#4A90E2", "mod": "#4FC36A", "multi": "#F0A030"}[s["kind"]]))
            p.drawRoundedRect(QRectF(x - 2.5, y - 6 + bob, 5, 5), 1, 1)
        if k.price:
            f = QFont("Tahoma")
            f.setPixelSize(4)
            p.setFont(f)
            p.setPen(QColor("#F2C230"))
            p.drawText(QRectF(x - 10, y + 1, 20, 6), Qt.AlignCenter, f"{k.price}g")

    def _draw_hud(self, p):
        g = self.game
        pl = g.player
        f = QFont("Tahoma")
        f.setPixelSize(12)
        f.setBold(True)
        p.setFont(f)

        def bar(y, frac, col, label):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 150))
            p.drawRect(QRectF(12, y, 180, 12))
            p.setBrush(QColor(col))
            p.drawRect(QRectF(13, y + 1, 178 * _clamp(frac, 0, 1), 10))
            p.setPen(QColor("#FFFFFF"))
            p.drawText(QRectF(198, y - 2, 140, 16), Qt.AlignVCenter, label)

        bar(12, pl.hp / pl.hp_max, "#D9363E", f"{pl.hp:.0f} / {pl.hp_max:.0f}")
        bar(28, pl.lev / 100, "#E8C547", "Levitation")
        if pl.wand:
            w = pl.wand
            bar(44, w.mana / w.mana_max, "#3F8DF0", f"{w.mana:.0f} mana" + ("  recharging" if w.recharging else ""))
        p.setPen(QColor("#F2C230"))
        p.drawText(QRectF(self.width() - 260, 10, 248, 18), Qt.AlignRight, f"Gold {pl.gold}")
        p.setPen(QColor("#E0E0E0"))
        b = wd.biome_at(int(pl.y)) if pl.y > wd.SURFACE else -1
        p.drawText(QRectF(self.width() - 360, 28, 348, 18), Qt.AlignRight,
                   f"{wd.BIOMES[b]['name'] if b >= 0 else 'The Surface'}   {g.depth()} m")
        for i, wand in enumerate(pl.wands):          # the wands, bottom left
            x = 12 + i * 40
            y = self.height() - 46
            p.setPen(QPen(QColor("#F2C230") if i == pl.current else QColor("#555060"), 2))
            p.setBrush(QColor(0, 0, 0, 160))
            p.drawRoundedRect(QRectF(x, y, 34, 34), 4, 4)
            p.setPen(QPen(QColor(wand.colour), 3))
            p.drawLine(QPointF(x + 8, y + 26), QPointF(x + 24, y + 10))
            p.setPen(QColor("#FFFFFF"))
            p.drawText(QRectF(x + 2, y + 1, 10, 12), Qt.AlignLeft, str(i + 1))
        if pl.wand:
            x0 = 12 + 4 * 40 + 10
            for j, name in enumerate(pl.wand.slots):
                rect = QRectF(x0 + j * 24, self.height() - 40, 22, 22)
                p.setPen(QPen(QColor("#F2C230") if j == pl.wand.cursor else QColor("#3A3440"), 1))
                p.setBrush(QColor(0, 0, 0, 150))
                p.drawRect(rect)
                if name:
                    p.drawPixmap(rect.topLeft().toPoint(), self._icon(name, 22))
        item = g.nearest_item()
        if item is not None:
            what = item.value.name if item.kind == "wand" else item.value
            p.setPen(QColor("#FFFFFF"))
            p.drawText(QRectF(0, self.height() * 0.62, self.width(), 20), Qt.AlignCenter,
                       f"E - {'buy' if item.price else 'take'} {what}" + (f" ({item.price} gold)" if item.price else ""))
        if g.boss is not None and g.boss in g.enemies:
            w = self.width() * 0.6
            x = (self.width() - w) / 2
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 170))
            p.drawRect(QRectF(x, 14, w, 14))
            p.setBrush(QColor("#9C2BD6"))
            p.drawRect(QRectF(x + 1, 15, (w - 2) * max(0, g.boss.hp) / g.boss.hp_max, 12))
            p.setPen(QColor("#FFFFFF"))
            p.drawText(QRectF(x, 30, w, 16), Qt.AlignCenter, g.boss.kind)
        if g.banner[1]:
            big = QFont("Georgia")
            big.setPixelSize(30)
            big.setItalic(True)
            p.setFont(big)
            c = QColor("#F2E6C8")
            c.setAlpha(min(255, g.banner[1] * 6))
            p.setPen(c)
            p.drawText(QRectF(0, self.height() * 0.22, self.width(), 40), Qt.AlignCenter, g.banner[0])

    def _center_text(self, p, big, small):
        p.fillRect(self.rect(), QColor(0, 0, 0, 150))
        f = QFont("Georgia")
        f.setPixelSize(40)
        p.setFont(f)
        p.setPen(QColor("#F2E6C8"))
        p.drawText(QRectF(0, self.height() * 0.32, self.width(), 60), Qt.AlignCenter, big)
        f.setPixelSize(15)
        p.setFont(f)
        p.drawText(QRectF(0, self.height() * 0.32 + 64, self.width(), 120), Qt.AlignHCenter | Qt.AlignTop, small)

    def _draw_over(self, p):
        g = self.game
        mins = int(time.time() - g.started) // 60
        rec = getattr(g, "records", {})
        stats = (f"Depth {g.depth()} m   Kills {g.player.kills}   Gold {g.player.gold}   {mins} minutes\n"
                 f"Runs {rec.get('runs', 1)}   Wins {rec.get('wins', 0)}   Deepest ever {rec.get('deepest', 0)} m\n\n"
                 "Click or press R for a new world")
        if g.over == "won":
            self._center_text(p, "The Unmaker is undone", "The deep is quiet. The world remains.\n\n" + stats)
        else:
            self._center_text(p, "You have died", "The world forgets you, and makes itself anew.\n\n" + stats)

    # ---- the wand editor ----
    def _inv_layout(self):
        """{("wand", i, j) | ("bag", k): QRectF} for the editor's slots."""
        out = {}
        pl = self.game.player
        x0, y0 = 40, 70
        for i, wand in enumerate(pl.wands):
            for j in range(len(wand.slots)):
                out[("wand", i, j)] = QRectF(x0 + 190 + j * 34, y0 + i * 70 + 18, 30, 30)
        for k in range(16):
            out[("bag", k)] = QRectF(x0 + (k % 8) * 38, y0 + 4 * 70 + 30 + (k // 8) * 38, 34, 34)
        return out

    def _slot_get(self, key):
        pl = self.game.player
        if key[0] == "wand":
            return pl.wands[key[1]].slots[key[2]]
        return pl.spells[key[1]] if key[1] < len(pl.spells) else None

    def _slot_set(self, key, name):
        pl = self.game.player
        if key[0] == "wand":
            pl.wands[key[1]].slots[key[2]] = name
            pl.wands[key[1]].cursor = 0
        else:
            k = key[1]
            if name is None:
                if k < len(pl.spells):
                    pl.spells.pop(k)
            elif k < len(pl.spells):
                pl.spells[k] = name
            else:
                pl.spells.append(name)

    def _inventory_click(self, pos, button):
        for key, rect in self._inv_layout().items():
            if not rect.contains(pos):
                continue
            here = self._slot_get(key)
            if button == Qt.RightButton and key[0] == "wand" and here:   # back into the bag
                if len(self.game.player.spells) < 16:
                    self._slot_set(key, None)
                    self.game.player.spells.append(here)
                self.pick = None
                return
            if self.pick is None:
                if here:
                    self.pick = key
                return
            if self.pick == key:
                self.pick = None
                return
            moving = self._slot_get(self.pick)
            src = self.pick
            self.pick = None
            if src[0] == "bag" and key[0] == "bag":
                return
            if src[0] == "bag":                     # bag -> wand: swap what's there back into the bag
                self._slot_set(key, moving)
                self._slot_set(src, here)
            elif key[0] == "bag":                   # wand -> bag
                self._slot_set(src, here)
                if here is None:
                    self.game.player.spells.append(moving)
                else:
                    self._slot_set(key, moving)
            else:                                   # wand <-> wand
                self._slot_set(key, moving)
                self._slot_set(src, here)
            return
        self.pick = None

    def _draw_inventory(self, p):
        pl = self.game.player
        p.fillRect(self.rect(), QColor(8, 6, 14, 220))
        f = QFont("Georgia")
        f.setPixelSize(22)
        p.setFont(f)
        p.setPen(QColor("#F2E6C8"))
        p.drawText(QRectF(40, 20, 600, 36), Qt.AlignLeft | Qt.AlignVCenter, "Wands and Spells")
        small = QFont("Tahoma")
        small.setPixelSize(11)
        p.setFont(small)
        p.setPen(QColor("#B8B0C8"))
        p.drawText(QRectF(300, 24, self.width() - 340, 30), Qt.AlignRight | Qt.AlignVCenter,
                   "Click a spell, then click where it goes. Right-click a wand's spell to put it in the bag. "
                   "Tab to close.")
        layout = self._inv_layout()
        mouse = self.mouse or QPointF(-1, -1)
        hover_name = None
        for i, wand in enumerate(pl.wands):
            y = 70 + i * 70
            p.setPen(QColor("#F2C230") if i == pl.current else QColor("#E0D8F0"))
            p.drawText(QRectF(40, y, 180, 16), Qt.AlignLeft, f"{i + 1}. {wand.name}")
            p.setPen(QColor("#9A92AE"))
            p.drawText(QRectF(40, y + 16, 150, 60), Qt.AlignLeft | Qt.TextWordWrap,
                       f"Mana {wand.mana_max} (+{wand.charge}/s)\nDelay {wand.delay}s  Recharge {wand.recharge}s\n"
                       f"Spread {wand.spread}°")
        for key, rect in layout.items():
            here = self._slot_get(key)
            sel = key == self.pick
            p.setPen(QPen(QColor("#F2C230") if sel else QColor("#3A3440"), 2 if sel else 1))
            p.setBrush(QColor(20, 16, 28))
            p.drawRect(rect)
            if here:
                p.drawPixmap(QPointF(rect.x() + (rect.width() - 26) / 2, rect.y() + (rect.height() - 26) / 2),
                             self._icon(here, 26))
                if rect.contains(mouse):
                    hover_name = here
        p.setPen(QColor("#E0D8F0"))
        p.drawText(QRectF(40, 70 + 4 * 70 + 8, 300, 18), Qt.AlignLeft, f"Spell bag ({len(pl.spells)}/16)")
        if hover_name:
            s = SPELLS[hover_name]
            kind = {"proj": "Projectile", "mod": "Modifier", "multi": "Multicast"}[s["kind"]]
            extra = (f"   Damage {s['dmg']}" if s.get("dmg") else "") + f"   Mana {s['mana']}"
            f2 = QFont("Tahoma")
            f2.setPixelSize(13)
            f2.setBold(True)
            p.setFont(f2)
            p.setPen(QColor("#FFFFFF"))
            p.drawText(QRectF(40, self.height() - 70, self.width() - 80, 20), Qt.AlignLeft,
                       f"{hover_name}  ({kind}){extra}")
            p.setFont(small)
            p.setPen(QColor("#C8C0D8"))
            p.drawText(QRectF(40, self.height() - 48, self.width() - 80, 20), Qt.AlignLeft, s["desc"])

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = Claudeita(desktop)
        win = host.window(desktop, TITLE, body, claudeita_icon(), (960, 640))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    win.content.setFocus()
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.timer.stop()
