"""Scorched Claude's rules: the landscape (a height for every column - dirt falls into craters, as it does in the
original), tanks, weapons and their flight through gravity and wind, explosions, napalm, rollers, MIRVs, damage,
falling, money, the shop, and the computer players' aim.

Units are pixels and seconds. The battle is W x H pixels; height[x] is how high the ground reaches at column x
(the ground's surface is at y = H - height[x]).
"""
import math
import random

W, H = 900, 520
GRAVITY = 300.0
MAX_SPEED = 900.0                      # at power 1000
WIND_FORCE = 9.0                       # px/s^2 per wind point
TANK_R = 9

WEAPONS = {
    # name: (price, quantity per purchase, blast radius, kind, description)
    "Baby Missile": (400, 10, 15, "missile", "A small explosion."),
    "Missile": (1500, 5, 22, "missile", "A medium explosion."),
    "Baby Nuke": (8000, 3, 42, "missile", "A big explosion."),
    "Nuke": (12000, 1, 75, "missile", "A very big explosion."),
    "LeapFrog": (9000, 2, 22, "leapfrog", "Bounces twice, exploding each time."),
    "Funky Bomb": (7000, 2, 26, "funky", "Bursts into a shower of bomblets."),
    "MIRV": (10000, 3, 22, "mirv", "Splits into five warheads at the top of its arc."),
    "Death's Head": (20000, 1, 42, "mirv", "Splits into nine nukes. Ouch."),
    "Napalm": (9000, 10, 0, "napalm", "Burning jelly flows downhill."),
    "Hot Napalm": (16000, 2, 0, "napalm", "Hotter, wider, nastier."),
    "Roller": (5000, 10, 22, "roller", "Rolls downhill, then blows up."),
    "Heavy Roller": (6500, 2, 42, "roller", "A big one that rolls."),
    "Dirt Clod": (4000, 10, 22, "dirt", "Drops a ball of dirt."),
    "Ton of Dirt": (6500, 2, 55, "dirt", "Drops a LOT of dirt."),
    "Riot Bomb": (4500, 5, 35, "riot", "Blows dirt away without hurting anyone."),
    "Tracer": (10, 20, 0, "tracer", "Shows the path - no damage."),
}
ITEMS = {
    "Parachute": (8000, 8, "Saves you from falling damage."),
    "Shield": (12000, 3, "Absorbs 100 damage."),
    "Heavy Shield": (20000, 2, "Absorbs 200 damage."),
    "Battery": (4000, 10, "Restores 15 health."),
    "Fuel": (3000, 25, "Lets you drive left and right (A / D)."),
}
AI_TYPES = {"Moron": 0.0, "Shooter": 0.35, "Poolshark": 0.6, "Tosser": 0.75, "Chooser": 0.8, "Spoiler": 0.88,
            "Cyborg": 0.95}
COLOURS = ["#E03030", "#3060F0", "#30C040", "#F0D020", "#C040E0", "#30D0D0", "#F08020", "#F0F0F0", "#E070A0",
           "#90E030"]
TAUNTS_FIRE = ["Eat this!", "Say hello to my little friend!", "Duck!", "Fire in the hole!", "Incoming!",
               "This one's for you!", "Catch!", "Special delivery!", "Bombs away!", "Ka-BOOM time!",
               "Hope you like dirt!", "Physics, don't fail me now."]
TAUNTS_DIE = ["I'll be back...", "Tell my mother I...", "Not again!", "Ouch.", "That was uncalled for.",
              "I regret nothing!", "Medic!", "Blasted!", "Was it something I said?", "Game over, man!"]


class Tank:
    def __init__(self, name, colour, ai=None):
        self.name, self.colour, self.ai = name, colour, ai
        self.cash = 10000
        self.inventory = {"Baby Missile": 99}
        self.score = 0
        self.kills = 0
        self.reset()

    def reset(self):
        self.x, self.y = 0.0, 0.0
        self.health = 100.0
        self.angle, self.power = 90.0, 500.0
        self.weapon = "Baby Missile"
        self.shield = 0.0
        self.alive = True
        self.falling = False
        self.fall_from = 0.0
        self.fuel_left = 0.0
        self.say = None
        self.round_damage = 0.0
        self.ai_target, self.ai_streak = None, 0

    @property
    def max_power(self):
        return max(50.0, self.health * 10)

    def owned(self):
        return [w for w in list(WEAPONS) if self.inventory.get(w, 0) > 0]

    def muzzle(self):
        a = math.radians(self.angle)
        return self.x + math.cos(a) * 14, self.y - 8 - math.sin(a) * 14


class Shot:
    def __init__(self, x, y, vx, vy, weapon, owner, generation=0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.weapon, self.owner, self.gen = weapon, owner, generation
        self.trail = [(x, y)]
        self.done = False
        self.bounces = 0
        self.rolling = False
        self.split = False


class Battle:
    """One round on one landscape."""

    def __init__(self, tanks, rnd=None, wind_max=10):
        self.rnd = rnd or random.Random()
        self.tanks = tanks
        self.height = self._landscape()
        self.wind = self.rnd.randint(-wind_max, wind_max)
        self.wind_max = wind_max
        self.shots = []
        self.blasts = []              # (x, y, radius, age, colour) for the screen
        self.flames = []              # napalm: [x, y, life, owner]
        self.texts = []               # (x, y, text, age)
        self.sky = self.rnd.choice(["night", "dusk", "day", "storm", "sunset"])
        self.palette = self.rnd.choice(["classic", "desert", "snow", "lava", "grass"])
        self.turn = 0
        self.busy = False
        self.dirty = True             # the landscape changed (the screen re-renders it)
        self._place_tanks()
        self.order = [t for t in tanks if t.alive]
        self.rnd.shuffle(self.order)
        self.current = self.order[0]

    # ---- the land -------------------------------------------------------------------------------------------
    def _landscape(self):
        rnd = self.rnd
        n = W + 1
        h = [0.0] * n
        # midpoint displacement for a mountainous skyline
        step = 512
        size = 1024
        pts = [0.0] * (size + 1)
        pts[0] = rnd.uniform(80, 300)
        pts[size] = rnd.uniform(80, 300)
        rough = rnd.uniform(0.45, 0.6)
        disp = rnd.uniform(120, 220)
        while step >= 1:
            for i in range(step, size, step * 2):
                pts[i] = (pts[i - step] + pts[i + step]) / 2 + rnd.uniform(-disp, disp)
            disp *= rough
            step //= 2
        for x in range(n):
            v = pts[int(x / W * size)]
            h[x] = max(25.0, min(H - 120.0, v))
        return h

    def ground(self, x):
        xi = int(min(W, max(0, x)))
        return H - self.height[xi]

    def _place_tanks(self):
        alive = [t for t in self.tanks]
        n = len(alive)
        xs = [int((i + 0.5) * W / n + self.rnd.uniform(-W / n * 0.3, W / n * 0.3)) for i in range(n)]
        self.rnd.shuffle(xs)
        for t, x in zip(alive, xs):
            t.x = float(max(20, min(W - 20, x)))
            # flatten a little pad
            base = self.height[int(t.x)]
            for dx in range(-12, 13):
                xi = int(t.x) + dx
                if 0 <= xi <= W:
                    self.height[xi] = base
            t.y = self.ground(t.x)
            t.angle = 45.0 if t.x < W / 2 else 135.0

    def remove_dirt(self, cx, cy, r):
        """A crater: the dirt inside the circle vanishes and what was above it falls in."""
        for x in range(int(cx - r), int(cx + r) + 1):
            if not 0 <= x <= W:
                continue
            dx = x - cx
            half = math.sqrt(max(0.0, r * r - dx * dx))
            top_y, bot_y = cy - half, cy + half          # the circle's chord in screen y
            surface = H - self.height[x]
            # overlap of [top_y, bot_y] with the solid part [surface, H]
            overlap = max(0.0, min(bot_y, H) - max(top_y, surface))
            if overlap > 0:
                self.height[x] = max(0.0, self.height[x] - overlap)
        self.dirty = True

    def add_dirt(self, cx, cy, r):
        for x in range(int(cx - r), int(cx + r) + 1):
            if not 0 <= x <= W:
                continue
            dx = x - cx
            half = math.sqrt(max(0.0, r * r - dx * dx))
            self.height[x] = min(H - 30.0, self.height[x] + half * 2)
        self.dirty = True

    # ---- firing ---------------------------------------------------------------------------------------------
    def fire(self, tank):
        w = tank.weapon
        if tank.inventory.get(w, 0) <= 0:
            w = tank.weapon = "Baby Missile"
        if w != "Baby Missile":
            tank.inventory[w] -= 1
        mx, my = tank.muzzle()
        speed = min(tank.power, tank.max_power) / 1000 * MAX_SPEED
        a = math.radians(tank.angle)
        self.shots.append(Shot(mx, my, math.cos(a) * speed, -math.sin(a) * speed, w, tank))
        self.busy = True
        if self.rnd.random() < 0.35:
            tank.say = (self.rnd.choice(TAUNTS_FIRE), 2.5)

    def step(self, dt):
        """Advance shots, napalm, falling tanks and effects. Returns True while anything is still happening."""
        for s in list(self.shots):
            self._fly(s, dt)
        self.shots = [s for s in self.shots if not s.done]
        for f in self.flames:
            f[2] -= dt
        for t in self.tanks:                              # burning: once per tank, however many flames touch it
            f = next((f for f in self.flames if t.alive and abs(t.x - f[0]) < 10 and abs(t.y - f[1]) < 14), None)
            if f is not None:
                self._damage(t, 28 * dt, f[3])
        self.flames = [f for f in self.flames if f[2] > 0]
        self.blasts = [(x, y, r, age + dt, c) for x, y, r, age, c in self.blasts if age < 0.6]
        self.texts = [(x, y, txt, age + dt) for x, y, txt, age in self.texts if age < 1.4]
        for t in self.tanks:
            if t.say:
                t.say = (t.say[0], t.say[1] - dt) if t.say[1] > dt else None
        moving = self._settle(dt)
        active = bool(self.shots or self.flames or self.blasts or moving)
        if self.busy and not active:
            self.busy = False
            self._next_turn()
        return active

    def _fly(self, s, dt):
        if s.rolling:
            self._roll(s, dt)
            return
        sub = 4
        for _ in range(sub):
            h = dt / sub
            s.vx += self.wind * WIND_FORCE * h
            s.vy += GRAVITY * h
            prev_vy = s.vy
            s.x += s.vx * h
            s.y += s.vy * h
            kind = WEAPONS[s.weapon][3]
            if kind == "mirv" and not s.split and s.gen == 0 and prev_vy > 0 and s.vy - GRAVITY * h <= 0:
                self._split(s)
                return
            if kind == "mirv" and not s.split and s.gen == 0 and s.vy > 0:
                self._split(s)
                return
            if s.x < -50 or s.x > W + 50 or s.y > H + 50:
                s.done = True
                return
            if s.y < -2000:
                continue
            hit_tank = next((t for t in self.tanks if t.alive and (t is not s.owner or len(s.trail) > 8)
                             and math.hypot(t.x - s.x, t.y - 5 - s.y) < TANK_R + 2), None)
            if hit_tank is not None or (0 <= s.x <= W and s.y >= self.ground(s.x)):
                self._impact(s, hit_tank)
                return
        if len(s.trail) < 400:
            s.trail.append((s.x, s.y))

    def _split(self, s):
        s.split = True
        s.done = True
        n = 9 if s.weapon == "Death's Head" else 5
        sub_weapon = "Baby Nuke" if s.weapon == "Death's Head" else "Missile"
        for i in range(n):
            spread = (i - (n - 1) / 2) * (38 if n == 5 else 30)
            c = Shot(s.x, s.y, s.vx + spread, s.vy, sub_weapon, s.owner, 1)
            c.trail = list(s.trail[-3:])
            self.shots.append(c)

    def _impact(self, s, tank):
        kind = WEAPONS[s.weapon][3]
        r = WEAPONS[s.weapon][2]
        x, y = s.x, min(s.y, self.ground(s.x)) if tank is None else s.y
        if kind == "tracer":
            s.done = True
            return
        if kind == "leapfrog" and s.bounces < 2:
            self.explode(x, y, r - s.bounces * 4, s.owner)
            s.bounces += 1
            s.vy = -abs(s.vy) * 0.6
            s.vx *= 0.8
            s.y = self.ground(s.x) - 2
            return
        if kind == "roller" and tank is None:
            s.rolling = True
            s.y = self.ground(s.x)
            s.roll_t = 0.0
            s.vx = (1 if s.vx >= 0 else -1) * max(40.0, abs(s.vx) * 0.4)
            return
        s.done = True
        if kind == "napalm":
            self._napalm(x, s.weapon == "Hot Napalm", s.owner)
        elif kind == "dirt":
            self.add_dirt(x, y, r)
            self.blasts.append((x, y, r, 0.0, "#8A6A3A"))
        elif kind == "riot":
            self.remove_dirt(x, y, r)
            self.blasts.append((x, y, r, 0.0, "#C8C8FF"))
        elif kind == "funky":
            self.explode(x, y, r, s.owner)
            for _ in range(7):
                ang = self.rnd.uniform(math.pi * 0.15, math.pi * 0.85)
                sp = self.rnd.uniform(150, 330)
                b = Shot(x, y - 4, math.cos(ang) * sp, -math.sin(ang) * sp, "Baby Missile", s.owner, 1)
                b.funky_colour = self.rnd.choice(COLOURS)
                self.shots.append(b)
        else:
            self.explode(x, y, r, s.owner)

    def _roll(self, s, dt):
        s.roll_t += dt
        left, right = self.ground(s.x - 3), self.ground(s.x + 3)
        slope = right - left                              # positive: the ground falls away to the right
        s.vx += slope * 20 * dt
        s.vx = max(-160.0, min(160.0, s.vx))
        s.x += s.vx * dt
        s.y = self.ground(s.x)
        hit = next((t for t in self.tanks if t.alive and t is not s.owner and abs(t.x - s.x) < TANK_R + 2), None)
        if hit or s.roll_t > 4 or abs(s.vx) < 8 or not 0 <= s.x <= W:
            s.done = True
            self.explode(s.x, s.y - 2, WEAPONS[s.weapon][2], s.owner)
        elif len(s.trail) < 400:
            s.trail.append((s.x, s.y))

    def _napalm(self, x, hot, owner):
        """Burning jelly that runs downhill from where it lands."""
        n = 26 if hot else 16
        life = 3.2 if hot else 2.4
        for direction in (-1, 1):
            px = x
            for i in range(n // 2):
                nx = px + direction * 4
                if not 0 <= nx <= W:
                    break
                if self.ground(nx) < self.ground(px) - 3 and i > 2:     # uphill: it stops
                    break
                px = nx
                self.flames.append([px, self.ground(px), life + self.rnd.uniform(-0.3, 0.3), owner])
        self.flames.append([x, self.ground(x), life, owner])

    def explode(self, x, y, r, owner, colour=None):
        self.remove_dirt(x, y, r)
        self.blasts.append((x, y, r, 0.0, colour or "#FFB030"))
        for t in self.tanks:
            if not t.alive:
                continue
            d = math.hypot(t.x - x, t.y - 5 - y)
            if d < r + TANK_R:
                dmg = (r * 2.0 + 18) * (1 - d / (r + TANK_R))
                self._damage(t, dmg, owner)

    def _damage(self, t, dmg, owner):
        if not t.alive or dmg <= 0:
            return
        if t.shield > 0:
            absorbed = min(t.shield, dmg)
            t.shield -= absorbed
            dmg -= absorbed
        if dmg <= 0:
            return
        t.health -= dmg
        if owner is not None and owner is not t:
            owner.cash += int(dmg * 6)
            owner.round_damage += dmg
        if dmg >= 1:
            self.texts.append((t.x, t.y - 30, str(int(dmg)), 0.0))
        if t.health <= 0:
            self._kill(t, owner)

    def _kill(self, t, owner):
        t.alive = False
        t.health = 0
        t.say = (self.rnd.choice(TAUNTS_DIE), 2.5)
        if owner is not None and owner is not t:
            owner.kills += 1
            owner.cash += 750
            owner.score += 1
        self.explode(t.x, t.y - 4, 22, None, "#FF6020")

    def _settle(self, dt):
        """Tanks fall when the ground under them is blown away."""
        moving = False
        for t in self.tanks:
            if not t.alive:
                continue
            g = self.ground(t.x)
            if t.y < g - 0.5:
                if not t.falling:
                    t.falling = True
                    t.fall_from = t.y
                    t.parachute = t.inventory.get("Parachute", 0) > 0 and g - t.y > 12
                    if t.parachute:
                        t.inventory["Parachute"] -= 1
                t.y = min(g, t.y + (60 if getattr(t, "parachute", False) else 220) * dt)
                moving = True
            elif t.falling:
                t.falling = False
                t.y = g
                drop = g - t.fall_from
                if drop > 10 and not getattr(t, "parachute", False):
                    self._damage(t, drop * 0.35, None)
                t.parachute = False
            else:
                t.y = g
        return moving

    # ---- turns ---------------------------------------------------------------------------------------------
    def alive(self):
        return [t for t in self.tanks if t.alive]

    def over(self):
        return len(self.alive()) <= 1

    def _next_turn(self):
        if self.over():
            return
        order = [t for t in self.order if t.alive]
        if not order:
            return
        if self.current in order:
            i = (order.index(self.current) + 1) % len(order)
        else:
            i = 0
        self.current = order[i]
        if self.rnd.random() < 0.3:                       # the wind shifts now and then
            self.wind = max(-self.wind_max, min(self.wind_max, self.wind + self.rnd.randint(-3, 3)))

    def use_item(self, t, item):
        if t.inventory.get(item, 0) <= 0:
            return False
        if item == "Shield":
            t.shield = max(t.shield, 100)
        elif item == "Heavy Shield":
            t.shield = max(t.shield, 200)
        elif item == "Battery":
            if t.health >= 100:
                return False
            t.health = min(100, t.health + 15)
        else:
            return False
        t.inventory[item] -= 1
        return True

    def drive(self, t, direction, dt):
        """Spend fuel to roll the tank along the ground (it won't climb cliffs)."""
        if t.inventory.get("Fuel", 0) <= 0 and t.fuel_left <= 0:
            return
        nx = t.x + direction * 40 * dt
        if not 12 <= nx <= W - 12 or self.ground(nx) < self.ground(t.x) - 6:
            return
        if t.fuel_left <= 0:
            t.inventory["Fuel"] -= 1
            t.fuel_left = 10.0
        t.fuel_left -= 40 * dt
        t.x = nx
        t.y = self.ground(nx)

    # ---- the computer players --------------------------------------------------------------------------------
    def simulate(self, x, y, angle, power, wind):
        a = math.radians(angle)
        sp = power / 1000 * MAX_SPEED
        vx, vy = math.cos(a) * sp, -math.sin(a) * sp
        dt = 1 / 30
        for _ in range(400):
            vx += wind * WIND_FORCE * dt
            vy += GRAVITY * dt
            x += vx * dt
            y += vy * dt
            if x < -50 or x > W + 50:
                return None
            if 0 <= x <= W and y >= self.ground(x):
                return x, y
        return None

    def ai_aim(self, t):
        """Pick a target and work out an angle and power, with mistakes depending on the AI's skill."""
        skill = AI_TYPES.get(t.ai, 0.5)
        enemies = [e for e in self.alive() if e is not t]
        if not enemies:
            return
        if t.ai_target in enemies and self.rnd.random() < 0.85:
            target = t.ai_target                          # keep walking shots in on the same tank
        else:
            target = min(enemies, key=lambda e: abs(e.x - t.x)) if self.rnd.random() < 0.6 else self.rnd.choice(enemies)
        t.ai_streak = t.ai_streak + 1 if target is t.ai_target else 0
        t.ai_target = target
        best, best_d = None, 1e9
        mx, my = t.muzzle()
        wind_guess = self.wind if skill > 0.5 else self.wind * self.rnd.uniform(0, 1)
        maxp = t.max_power
        for angle in range(10, 171, 4):
            for power in range(120, int(maxp) + 1, 45):
                land = self.simulate(mx, my, angle, power, wind_guess)
                if land is None:
                    continue
                d = abs(land[0] - target.x) + abs(land[1] - target.y) * 0.3
                if d < best_d:
                    best, best_d = (angle, power), d
        if best is None:
            best = (self.rnd.uniform(30, 150), self.rnd.uniform(200, maxp))
        err = (1 - skill) * 0.6 ** t.ai_streak             # each shot at the same tank gets closer
        angle = best[0] + self.rnd.gauss(0, 7 * err)
        power = best[1] + self.rnd.gauss(0, 90 * err)
        if t.ai == "Moron":
            angle, power = self.rnd.uniform(20, 160), self.rnd.uniform(150, maxp)
        t.angle = max(0.0, min(180.0, angle))
        t.power = max(50.0, min(maxp, power))
        # the best weapon it owns for the job
        owned = [w for w in t.owned() if WEAPONS[w][3] not in ("tracer", "dirt", "riot")]
        near_self = abs(target.x - t.x) < 80
        choices = [w for w in owned if not (near_self and WEAPONS[w][2] > 40)]
        if choices:
            t.weapon = max(choices, key=lambda w: (WEAPONS[w][0] * (0.6 + self.rnd.random())))
        for item in ("Heavy Shield", "Shield"):
            if t.shield <= 0 and t.inventory.get(item, 0) > 0 and self.rnd.random() < 0.7:
                self.use_item(t, item)
                break
        if t.health < 60 and t.inventory.get("Battery", 0):
            self.use_item(t, "Battery")


def ai_shop(t, rnd):
    """Computer players spend their money sensibly-ish."""
    wish = ["Shield", "Missile", "Parachute", "Baby Nuke", "MIRV", "Funky Bomb", "Napalm", "Heavy Shield", "Nuke",
            "LeapFrog", "Battery", "Death's Head", "Roller", "Hot Napalm"]
    rnd.shuffle(wish)
    for name in wish:
        price, qty = (WEAPONS[name][0], WEAPONS[name][1]) if name in WEAPONS else ITEMS[name][:2]
        if t.cash >= price and rnd.random() < 0.7:
            t.cash -= price
            t.inventory[name] = t.inventory.get(name, 0) + qty
